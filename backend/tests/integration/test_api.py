"""The local HTTP API: health, context, tools, ask with conversation continuity, validation."""

import dataclasses
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crew_ops_advisor.config import Settings
from crew_ops_advisor.interface.api import create_app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="module")
def client(db_path, tmp_path_factory):
    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path_factory.mktemp("chats") / "chats.db",
        llm_provider="offline",
        offline_fallback=False,
    )
    return TestClient(create_app(settings))


def test_health_and_context(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["provider"] == "offline"
    ctx = client.get("/api/context").json()
    assert ctx["today"] == "2026-09-14" and len(ctx["samples"]) == 38
    assert ctx["week"] == {"start": "2026-09-14", "end": "2026-09-20"}


def test_tools_catalogue(client):
    tools = client.get("/api/tools").json()
    assert {t["tier"] for t in tools} == {1, 2, 3} and len(tools) == 33
    assert any(t["name"] == "recommend_cover" and "crew_id" in t["parameters"] for t in tools)


def test_ask_keeps_conversation_and_returns_trace(client):
    r = client.post("/api/ask", json={"question": "Who's on reserve at BLR tomorrow?"}).json()
    a = r["answer"]
    assert a["mode"] == "offline" and "C-3310" in a["answer"]
    assert [s["name"] for s in a["trace"] if s["kind"] == "tool"] == ["list_reserves"]
    assert a["grounding"]["ok"]
    r2 = client.post(
        "/api/ask",
        json={"question": "What is C-2210's base?", "conversation_id": r["conversation_id"]},
    ).json()
    assert r2["conversation_id"] == r["conversation_id"] and "DEL" in r2["answer"]["answer"]


def test_validation(client):
    assert client.post("/api/ask", json={"question": ""}).status_code == 422
    assert client.post("/api/ask", json={}).status_code == 422


def test_chat_lifecycle(client):
    r = client.post("/api/ask", json={"question": "Who's on reserve at BLR tomorrow?"}).json()
    cid = r["conversation_id"]
    assert (
        r["chat"]["title"] == "Who's on reserve at BLR tomorrow?"
        and r["chat"]["message_count"] == 2
    )

    r2 = client.post(f"/api/chats/{cid}/ask", json={"question": "What is C-2210's base?"}).json()
    assert r2["conversation_id"] == cid and r2["chat"]["message_count"] == 4

    chats = client.get("/api/chats").json()
    assert chats[0]["id"] == cid and chats[0]["message_count"] == 4

    detail = client.get(f"/api/chats/{cid}").json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]
    assert detail["messages"][1]["answer"]["trace"]  # stored answers keep their trace

    assert (
        client.patch(f"/api/chats/{cid}", json={"title": "Reserves"}).json()["title"] == "Reserves"
    )
    assert client.post("/api/chats", json={}).status_code == 201
    assert client.delete(f"/api/chats/{cid}").status_code == 204
    assert client.get(f"/api/chats/{cid}").status_code == 404
    assert client.post(f"/api/chats/{cid}/ask", json={"question": "x"}).status_code == 404


def test_voice_endpoints_with_a_fake_server_side_provider(db_path, tmp_path):
    from crew_ops_advisor.voice import AudioClip, Transcript

    class FakeSTT:
        name, server_side = "fake", True

        def transcribe(self, audio, *, mime, language=None):
            return Transcript(
                text=f"heard {len(audio)} bytes of {mime}", language=language, provider="fake"
            )

    class FakeTTS:
        name, server_side = "fake", True

        def synthesize(self, text, *, language=None):
            return AudioClip(data=b"RIFFfake", mime="audio/wav", provider="fake")

    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
    )
    c = TestClient(create_app(settings, stt=FakeSTT(), tts=FakeTTS()))
    assert c.get("/api/voice").json()["stt"] == {
        "provider": "fake",
        "server_side": True,
        "language": "en-IN",
    }
    # A browser-style WebM/Opus upload reaches the provider as 16 kHz mono WAV.
    webm = (FIXTURES / "reserve_question.webm").read_bytes()
    r = c.post(
        "/api/transcribe",
        files={"audio": ("speech.webm", webm, "audio/webm;codecs=opus")},
        data={"language": "en-IN"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["text"].endswith("bytes of audio/wav") and r.json()["language"] == "en-IN"
    # Unreadable uploads are the client's problem, not a provider failure.
    bad = c.post("/api/transcribe", files={"audio": ("q.webm", b"abc" * 50, "audio/webm")})
    assert bad.status_code == 400 and "could not read the recording" in bad.json()["detail"]
    s = c.post("/api/speak", json={"text": "hello"})
    assert (
        s.status_code == 200
        and s.content == b"RIFFfake"
        and s.headers["content-type"].startswith("audio/wav")
    )


def test_voice_endpoints_report_browser_side_providers(db_path, tmp_path):
    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
        stt_provider="browser",
        tts_provider="browser",
    )
    c = TestClient(create_app(settings))
    assert c.get("/api/voice").json()["stt"]["server_side"] is False
    assert (
        c.post("/api/transcribe", files={"audio": ("q.wav", b"abc", "audio/wav")}).status_code
        == 501
    )
    assert c.post("/api/speak", json={"text": "hi"}).status_code == 501

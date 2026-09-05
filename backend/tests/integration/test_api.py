"""The local HTTP API: health, context, tools, ask with conversation continuity, validation."""

import dataclasses
import json
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
    assert {t["tier"] for t in tools} == {1, 2, 3} and len(tools) == 35
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


def test_directory_and_pii_mode_are_exposed_for_client_side_name_joins(db_path, tmp_path):
    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
        pii_mode="minimal",
    )
    c = TestClient(create_app(settings))
    assert c.get("/api/health").json()["pii_mode"] == "minimal"
    assert c.get("/api/context").json()["pii_mode"] == "minimal"
    directory = c.get("/api/directory").json()
    assert len(directory) == 150 and directory["C-1042"]


def test_ask_stream_sends_progress_events_then_the_verified_answer(db_path, tmp_path):
    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
    )
    c = TestClient(create_app(settings))
    with c.stream("POST", "/api/ask/stream", json={"question": "What is C-2210 base?"}) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        frames = [line for line in r.iter_lines() if line.startswith("data: ")]
    events = [json.loads(f[6:]) for f in frames]
    kinds = [e["type"] for e in events]
    assert kinds[0] == "tool_call" and "tool_done" in kinds and kinds[-1] == "done"
    assert events[0]["label"].startswith("reading the crew roster")
    done = events[-1]
    assert done["conversation_id"] and "DEL" in done["answer"]["answer"]
    # the chat was persisted exactly as /api/ask would have
    assert (
        c.get(f"/api/chats/{done['conversation_id']}").json()["messages"][-1]["role"] == "assistant"
    )


def test_watchlist_endpoint(db_path, tmp_path):
    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
    )
    c = TestClient(create_app(settings))
    w = c.get("/api/watchlist").json()
    assert w["date"] == "2026-09-15" and w["count"] >= 1
    assert c.get("/api/watchlist?date=2026-09-18").json()["date"] == "2026-09-18"
    assert c.get("/api/watchlist?date=nonsense").status_code == 400


def test_concurrent_requests_do_not_corrupt_reads(db_path, tmp_path):
    """A page load fires several requests at once; each worker thread must read the
    database through its own connection (a shared one interleaved cursors → NULL rows)."""
    from concurrent.futures import ThreadPoolExecutor

    settings = dataclasses.replace(
        Settings.from_env(),
        db_path=db_path,
        chats_db_path=tmp_path / "c.db",
        llm_provider="offline",
    )
    c = TestClient(create_app(settings))
    paths = ["/api/watchlist", "/api/context", "/api/chats", "/api/directory", "/api/tools"] * 8

    def hit(path):
        r = c.get(path)
        return path, r.status_code

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(hit, paths))
    assert all(code == 200 for _, code in results), [r for r in results if r[1] != 200]

"""Local HTTP API for the React frontend (ADR-0006, ADR-0015).

    GET    /api/health                liveness + provider + snapshot
    GET    /api/context               snapshot, stations, fleet, sample questions by tier
    GET    /api/tools                 the tool catalogue (name, description, tier)
    GET    /api/chats                 conversation list, most recent first
    POST   /api/chats                 create an empty chat  {title?}
    GET    /api/chats/{id}            chat + its messages (with stored answers/traces)
    PATCH  /api/chats/{id}            rename  {title}
    DELETE /api/chats/{id}            delete chat and messages
    POST   /api/chats/{id}/ask        ask within a chat  {question}
    POST   /api/ask                   ask; creates a chat when no conversation_id is given
    GET    /api/voice                 configured speech providers (server- or browser-side)
    POST   /api/transcribe            multipart audio -> transcript (server-side STT providers)
    POST   /api/speak                 {text} -> audio/wav (server-side TTS providers)
    /                                 the built React app (frontend/dist), when present

Endpoints are synchronous on purpose: the Advisor is sync and the Agent SDK provider runs
its own event loop, so FastAPI's threadpool is the right place for it. Conversations are
persisted (ChatStore); model sessions are rebuilt from the store when a chat is reopened.
"""

from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from crew_ops_advisor import __version__
from crew_ops_advisor.agent import Advisor, Conversation, make_advisor
from crew_ops_advisor.chats import ChatStore
from crew_ops_advisor.config import Settings
from crew_ops_advisor.data import Datastore, load_json
from crew_ops_advisor.domain.timeutil import fmt_utc
from crew_ops_advisor.simulation.scenario import Scenario
from crew_ops_advisor.voice import (
    SpeechToText,
    TextToSpeech,
    VoiceError,
    make_stt,
    make_tts,
    to_wav,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
# The frontend is a separate project; its build is served here for the single-process demo.
WEB_DIST = Path(os.environ.get("CREW_OPS_WEB_DIST", _BACKEND_ROOT.parent / "frontend" / "dist"))


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ChatRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class AskResponse(BaseModel):
    conversation_id: str
    chat: dict[str, Any]
    answer: dict[str, Any]


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str | None = None


MAX_AUDIO_BYTES = 15 * 1024 * 1024
_AUDIO_FILE = File(...)
_LANGUAGE_FORM = Form(default=None)


def _sse(chats: ChatService, chat_id: str | None, question: str):
    """Run the question on a worker thread and yield its progress events as SSE frames."""
    events: queue.Queue = queue.Queue()

    def work() -> None:
        try:
            response = chats.ask(chat_id, question, on_event=events.put)
            events.put({"type": "done", **response.model_dump()})
        except Exception as exc:  # noqa: BLE001 - the stream carries the error to the client
            events.put({"type": "error", "detail": str(exc)})

    threading.Thread(target=work, name="ask-stream", daemon=True).start()
    while True:
        try:
            event = events.get(timeout=15)
        except queue.Empty:
            yield ": keep-alive\n\n"  # comment frame: keeps proxies from closing a slow answer
            continue
        yield f"data: {json.dumps(event, default=str)}\n\n"
        if event["type"] in ("done", "error"):
            return


class ChatService:
    """Chats in the store plus the live model sessions for chats used in this process."""

    def __init__(self, advisor: Advisor, store: ChatStore):
        self.advisor = advisor
        self.store = store
        self._live: dict[str, Conversation] = {}
        self._lock = threading.Lock()

    def conversation(self, chat_id: str) -> Conversation:
        with self._lock:
            conv = self._live.get(chat_id)
            if conv is None:
                chat = self.store.get(chat_id)
                if chat is None:
                    raise KeyError(chat_id)
                conv = self.advisor.new_conversation(
                    session_id=chat.session_id,
                    prior=self.store.exchanges(chat_id),
                    scenario=Scenario.from_dict(chat.scenario),
                )
                if len(self._live) >= 200:  # bounded memory; reopened chats rehydrate
                    self._live.pop(next(iter(self._live)))
                self._live[chat_id] = conv
            return conv

    def ask(self, chat_id: str | None, question: str, on_event=None) -> AskResponse:
        question = question.strip()
        if chat_id is None or self.store.get(chat_id) is None:
            chat = self.store.create(provider=self.advisor.provider.name)
            chat_id = chat.id
        conv = self.conversation(chat_id)
        self.store.append(chat_id, "user", question)
        answer = self.advisor.ask(question, conv, on_event=on_event)
        self.store.append(chat_id, "assistant", answer.text, answer=answer.to_dict())
        self.store.set_session(chat_id, conv.session_id)
        self.store.set_scenario(chat_id, conv.scenario.to_dict())
        chat = self.store.get(chat_id)
        assert chat is not None
        return AskResponse(conversation_id=chat_id, chat=chat.to_dict(), answer=answer.to_dict())

    def forget(self, chat_id: str) -> None:
        with self._lock:
            self._live.pop(chat_id, None)


def create_app(
    settings: Settings | None = None,
    *,
    advisor: Advisor | None = None,
    chat_store: ChatStore | None = None,
    stt: SpeechToText | None = None,
    tts: TextToSpeech | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Datastore.open(settings)
    advisor = advisor or make_advisor(settings, store)
    chats = ChatService(advisor, chat_store or ChatStore(settings.chats_db_path))
    stt = stt or make_stt(settings)
    tts = tts or make_tts(settings)

    app = FastAPI(title="Crew Ops Advisor", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- context ---------------------------------------------------------

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": __version__,
            "provider": advisor.provider.name,
            "fallback": advisor.fallback.name if advisor.fallback else None,
            "pii_mode": advisor.pii.mode,
            "snapshot_utc": fmt_utc(store.snapshot_utc),
        }

    @app.get("/api/context")
    def context() -> dict[str, Any]:
        questions = load_json(store.data_dir, "questions.json")
        samples = [
            {"id": q["question_id"], "tier": q["tier"], "prompt": q["prompt"]} for q in questions
        ]
        dates = sorted({f.date for f in store.flights.list()})
        return {
            "snapshot_utc": fmt_utc(store.snapshot_utc),
            "pii_mode": advisor.pii.mode,
            "today": store.snapshot_utc.date().isoformat(),
            "week": {"start": dates[0].isoformat(), "end": dates[-1].isoformat()},
            "stations": store.flights.stations(),
            "fleet": [{"aircraft": r, "aircraft_type": t} for r, t in store.flights.aircraft()],
            "provider": advisor.provider.name,
            "samples": samples,
        }

    @app.get("/api/tools")
    def tools() -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "tier": spec.tier,
                "description": spec.description,
                "parameters": list(spec.input_schema.get("properties", {})),
            }
            for spec in (advisor.registry.get(n) for n in advisor.registry.names())
        ]

    # ---- chats -------------------------------------------------------------

    @app.get("/api/chats")
    def list_chats() -> list[dict[str, Any]]:
        return [c.to_dict() for c in chats.store.list()]

    @app.post("/api/chats", status_code=201)
    def create_chat(req: ChatCreateRequest) -> dict[str, Any]:
        return chats.store.create(provider=advisor.provider.name, title=req.title).to_dict()

    @app.get("/api/chats/{chat_id}")
    def get_chat(chat_id: str) -> dict[str, Any]:
        chat = chats.store.get(chat_id)
        if chat is None:
            raise HTTPException(status_code=404, detail="chat not found")
        return {
            "chat": chat.to_dict(),
            "messages": [m.to_dict() for m in chats.store.messages(chat_id)],
        }

    @app.patch("/api/chats/{chat_id}")
    def rename_chat(chat_id: str, req: ChatRenameRequest) -> dict[str, Any]:
        chat = chats.store.rename(chat_id, req.title)
        if chat is None:
            raise HTTPException(status_code=404, detail="chat not found")
        return chat.to_dict()

    @app.delete("/api/chats/{chat_id}", status_code=204)
    def delete_chat(chat_id: str) -> None:
        if not chats.store.delete(chat_id):
            raise HTTPException(status_code=404, detail="chat not found")
        chats.forget(chat_id)

    @app.post("/api/chats/{chat_id}/scenario/reset")
    def reset_scenario(chat_id: str) -> dict[str, Any]:
        """Discard the chat's working scenario (everyone available again, covers undone)."""
        if chats.store.get(chat_id) is None:
            raise HTTPException(status_code=404, detail="chat not found")
        conv = chats.conversation(chat_id)
        discarded = conv.scenario.summary()
        conv.scenario.reset()
        chats.store.set_scenario(chat_id, None)
        return {"discarded": discarded, "scenario": conv.scenario.to_dict()}

    @app.post("/api/chats/{chat_id}/ask", response_model=AskResponse)
    def ask_in_chat(chat_id: str, req: ChatAskRequest) -> AskResponse:
        if chats.store.get(chat_id) is None:
            raise HTTPException(status_code=404, detail="chat not found")
        return _ask(chat_id, req.question)

    @app.post("/api/ask", response_model=AskResponse)
    def ask(req: AskRequest) -> AskResponse:
        return _ask(req.conversation_id, req.question)

    def _ask(chat_id: str | None, question: str) -> AskResponse:
        try:
            return chats.ask(chat_id, question)
        except Exception as exc:  # noqa: BLE001 - surface as a clean 500, never a hang
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/ask/stream")
    def ask_stream(req: AskRequest) -> StreamingResponse:
        """Same as /api/ask, delivered as server-sent events: progress while the answer is
        produced (tool steps in the controller's words, the answer text as it is written),
        then one `done` event with the verified answer — the same payload /api/ask returns."""
        if req.conversation_id and chats.store.get(req.conversation_id) is None:
            raise HTTPException(status_code=404, detail="chat not found")
        return StreamingResponse(
            _sse(chats, req.conversation_id, req.question),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ---- voice ---------------------------------------------------------------

    @app.get("/api/watchlist")
    def watchlist(date: str | None = None, chat_id: str | None = None) -> dict[str, Any]:
        """Proactive alerts for a date (default tomorrow) — deterministic, no model call.
        With a chat_id the chat's scenario counts: applied covers and vacant pairing days."""
        registry = advisor.registry
        if chat_id and chats.store.get(chat_id) is not None:
            registry = chats.conversation(chat_id).registry
        outcome = registry.call("watchlist", {"date": date} if date else {})
        if not outcome.ok:
            raise HTTPException(status_code=400, detail=outcome.error)
        return outcome.result

    @app.get("/api/directory")
    def directory() -> dict[str, str]:
        """Crew id → name, joined client-side so names never travel with the model traffic
        (ADR-0017). In production this sits behind the controller's own authorisation."""
        return dict(advisor.pii.directory)

    @app.get("/api/voice")
    def voice() -> dict[str, Any]:
        return {
            "stt": {
                "provider": stt.name,
                "server_side": stt.server_side,
                "language": settings.sarvam_language,
            },
            "tts": {
                "provider": tts.name,
                "server_side": tts.server_side,
                "language": settings.sarvam_language,
            },
        }

    @app.post("/api/transcribe")
    def transcribe(
        audio: UploadFile = _AUDIO_FILE, language: str | None = _LANGUAGE_FORM
    ) -> dict[str, Any]:
        if not stt.server_side:
            raise HTTPException(
                status_code=501, detail=f"speech-to-text provider '{stt.name}' runs in the browser"
            )
        data = audio.file.read(MAX_AUDIO_BYTES + 1)
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="audio too large (15 MB max)")
        # The browser uploads its native recording (WebM/Opus, MP4/AAC, ...); normalise it to
        # 16 kHz mono WAV here so every provider sees the same thing.
        try:
            data, mime = to_wav(data, audio.content_type or "application/octet-stream")
        except VoiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            result = stt.transcribe(data, mime=mime, language=language)
        except VoiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return result.to_dict()

    @app.post("/api/speak")
    def speak(req: SpeakRequest) -> Response:
        if not tts.server_side:
            raise HTTPException(
                status_code=501, detail=f"text-to-speech provider '{tts.name}' runs in the browser"
            )
        try:
            clip = tts.synthesize(req.text, language=req.language)
        except VoiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return Response(content=clip.data, media_type=clip.mime)

    # ---- frontend ----------------------------------------------------------

    if WEB_DIST.exists():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            candidate = WEB_DIST / path
            if path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(WEB_DIST / "index.html")

    return app


def serve(host: str = "127.0.0.1", port: int = 8000, *, settings: Settings | None = None) -> None:
    import uvicorn

    uvicorn.run(create_app(settings), host=host, port=port, log_level="info")

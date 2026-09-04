"""Local speech-to-text with faster-whisper (no keys, no network after the first model download).

The model loads lazily on the first request and is shared across requests; the Whisper
`base` model transcribes a short desk question in well under a second on a laptop CPU.
"""

from __future__ import annotations

import io
import threading
import time

from crew_ops_advisor.voice.base import Transcript, VoiceError


class WhisperSTT:
    name = "whisper"
    server_side = True

    def __init__(
        self, model_size: str = "base", *, device: str = "cpu", compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = threading.Lock()

    @staticmethod
    def available() -> bool:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False
        return True

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from faster_whisper import WhisperModel
                    except ImportError as exc:
                        raise VoiceError(
                            "faster-whisper is not installed (pip install -e '.[voice]')"
                        ) from exc
                    self._model = WhisperModel(
                        self.model_size, device=self.device, compute_type=self.compute_type
                    )
        return self._model

    def transcribe(self, audio: bytes, *, mime: str, language: str | None = None) -> Transcript:
        if not audio:
            raise VoiceError("empty audio")
        model = self._load()
        started = time.perf_counter()
        try:
            segments, info = model.transcribe(
                io.BytesIO(audio),
                beam_size=5,
                language=_whisper_language(language),
                vad_filter=True,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        except Exception as exc:  # noqa: BLE001 - decoder/model errors become one user-facing error
            raise VoiceError(f"could not transcribe audio ({mime}): {exc}") from exc
        return Transcript(
            text=text,
            language=getattr(info, "language", None),
            provider=self.name,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )


def _whisper_language(language: str | None) -> str | None:
    """'en-IN' -> 'en'; None/'auto'/'unknown' -> let the model detect."""
    if not language or language.lower() in ("auto", "unknown"):
        return None
    return language.split("-")[0].lower()

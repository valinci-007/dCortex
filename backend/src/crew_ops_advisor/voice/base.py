"""Voice provider contracts: speech-to-text feeds the Advisor, text-to-speech reads answers.

Providers are swappable by configuration (ADR-0016). A provider is either server-side
(audio is posted to the backend, which calls the provider) or browser-side (the page uses
the Web Speech API and the backend is not involved). The UI asks `/api/voice` which it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class VoiceError(RuntimeError):
    """The provider could not transcribe / synthesise (config, network, unsupported audio)."""


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    language: str | None
    provider: str
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "provider": self.provider,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True, slots=True)
class AudioClip:
    data: bytes
    mime: str
    provider: str


class SpeechToText(Protocol):
    name: str
    server_side: bool

    def transcribe(self, audio: bytes, *, mime: str, language: str | None = None) -> Transcript: ...


class TextToSpeech(Protocol):
    name: str
    server_side: bool

    def synthesize(self, text: str, *, language: str | None = None) -> AudioClip: ...

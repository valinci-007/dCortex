"""Browser-side providers: the page uses the Web Speech API; the backend only advertises it."""

from __future__ import annotations

from crew_ops_advisor.voice.base import AudioClip, Transcript, VoiceError


class BrowserSTT:
    name = "browser"
    server_side = False

    def transcribe(self, audio: bytes, *, mime: str, language: str | None = None) -> Transcript:
        raise VoiceError(
            "speech-to-text runs in the browser for this configuration; nothing to transcribe here"
        )


class BrowserTTS:
    name = "browser"
    server_side = False

    def synthesize(self, text: str, *, language: str | None = None) -> AudioClip:
        raise VoiceError("text-to-speech runs in the browser for this configuration")

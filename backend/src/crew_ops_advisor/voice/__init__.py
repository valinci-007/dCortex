"""Voice layer: configurable speech-to-text and text-to-speech providers (ADR-0016).

CREW_OPS_STT_PROVIDER   whisper (local, default when installed) | sarvam | browser
CREW_OPS_TTS_PROVIDER   browser (default) | sarvam
"""

from __future__ import annotations

from crew_ops_advisor.config import Settings
from crew_ops_advisor.voice.audio import to_wav
from crew_ops_advisor.voice.base import (
    AudioClip,
    SpeechToText,
    TextToSpeech,
    Transcript,
    VoiceError,
)
from crew_ops_advisor.voice.browser import BrowserSTT, BrowserTTS
from crew_ops_advisor.voice.sarvam import SarvamSTT, SarvamTTS
from crew_ops_advisor.voice.whisper import WhisperSTT

STT_PROVIDERS = ("whisper", "sarvam", "browser")
TTS_PROVIDERS = ("browser", "sarvam")


def make_stt(settings: Settings) -> SpeechToText:
    """Speech-to-text per settings; falls back to the browser when a local model is missing."""
    name = settings.stt_provider
    if name == "whisper":
        if WhisperSTT.available():
            return WhisperSTT(settings.whisper_model)
        return BrowserSTT()
    if name == "sarvam":
        return SarvamSTT(
            settings.sarvam_api_key,
            model=settings.sarvam_stt_model,
            language=settings.sarvam_language,
            url=settings.sarvam_stt_url,
        )
    if name == "browser":
        return BrowserSTT()
    raise ValueError(
        f"unknown CREW_OPS_STT_PROVIDER {name!r} (use one of {', '.join(STT_PROVIDERS)})"
    )


def make_tts(settings: Settings) -> TextToSpeech:
    name = settings.tts_provider
    if name == "sarvam":
        return SarvamTTS(
            settings.sarvam_api_key,
            model=settings.sarvam_tts_model,
            speaker=settings.sarvam_tts_speaker,
            language=settings.sarvam_language,
            url=settings.sarvam_tts_url,
        )
    if name == "browser":
        return BrowserTTS()
    raise ValueError(
        f"unknown CREW_OPS_TTS_PROVIDER {name!r} (use one of {', '.join(TTS_PROVIDERS)})"
    )


__all__ = [
    "STT_PROVIDERS",
    "TTS_PROVIDERS",
    "AudioClip",
    "BrowserSTT",
    "BrowserTTS",
    "SarvamSTT",
    "SarvamTTS",
    "SpeechToText",
    "TextToSpeech",
    "Transcript",
    "VoiceError",
    "WhisperSTT",
    "make_stt",
    "make_tts",
    "to_wav",
]

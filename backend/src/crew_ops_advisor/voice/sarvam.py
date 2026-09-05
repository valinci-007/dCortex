"""Sarvam AI speech providers (Saarika speech-to-text, Bulbul text-to-speech).

Configured entirely from the environment so the hackathon credentials drop in without a
code change: SARVAM_API_KEY, SARVAM_STT_MODEL, SARVAM_TTS_MODEL, SARVAM_TTS_SPEAKER,
SARVAM_LANGUAGE, and — should the endpoints or field names differ from the defaults below —
SARVAM_STT_URL / SARVAM_TTS_URL. Standard library HTTP only: no extra dependency.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
import uuid

from crew_ops_advisor.voice.base import AudioClip, Transcript, VoiceError

DEFAULT_STT_URL = "https://api.sarvam.ai/speech-to-text"
DEFAULT_TTS_URL = "https://api.sarvam.ai/text-to-speech"
DEFAULT_STT_MODEL = "saarika:v2.5"
DEFAULT_TTS_MODEL = "bulbul:v2"
DEFAULT_SPEAKER = "anushka"
DEFAULT_LANGUAGE = "en-IN"
TIMEOUT_S = 60


def _open(request: urllib.request.Request, *, opener=None):
    fn = opener or urllib.request.urlopen
    return fn(request, timeout=TIMEOUT_S)


class SarvamSTT:
    name = "sarvam"
    server_side = True

    def __init__(
        self,
        api_key: str | None,
        *,
        model: str = DEFAULT_STT_MODEL,
        language: str = DEFAULT_LANGUAGE,
        url: str = DEFAULT_STT_URL,
        opener=None,
    ):
        self.api_key = api_key
        self.model = model
        self.language = language
        self.url = url
        self._opener = opener  # injectable for tests

    def transcribe(self, audio: bytes, *, mime: str, language: str | None = None) -> Transcript:
        if not self.api_key:
            raise VoiceError("SARVAM_API_KEY is not set")
        if not audio:
            raise VoiceError("empty audio")
        boundary = f"----crewops{uuid.uuid4().hex}"
        ext = {
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/webm": "webm",
            "audio/ogg": "ogg",
            "audio/mpeg": "mp3",
            "audio/mp4": "m4a",
        }.get(mime.split(";")[0].strip(), "wav")
        fields = {"model": self.model, "language_code": language or self.language}
        body = _multipart(boundary, fields, ("file", f"speech.{ext}", mime, audio))
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={
                "api-subscription-key": self.api_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        )
        started = time.perf_counter()
        payload = _call(request, opener=self._opener)
        text = (payload.get("transcript") or payload.get("text") or "").strip()
        return Transcript(
            text=text,
            language=payload.get("language_code"),
            provider=self.name,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )


class SarvamTTS:
    name = "sarvam"
    server_side = True

    def __init__(
        self,
        api_key: str | None,
        *,
        model: str = DEFAULT_TTS_MODEL,
        speaker: str = DEFAULT_SPEAKER,
        language: str = DEFAULT_LANGUAGE,
        url: str = DEFAULT_TTS_URL,
        opener=None,
    ):
        self.api_key = api_key
        self.model = model
        self.speaker = speaker
        self.language = language
        self.url = url
        self._opener = opener

    def synthesize(self, text: str, *, language: str | None = None) -> AudioClip:
        if not self.api_key:
            raise VoiceError("SARVAM_API_KEY is not set")
        text = text.strip()
        if not text:
            raise VoiceError("nothing to say")
        body = json.dumps(
            {
                "text": text[:1500],
                "target_language_code": language or self.language,
                "speaker": self.speaker,
                "model": self.model,
                "output_audio_codec": "wav",
            }
        ).encode()
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        payload = _call(request, opener=self._opener)
        audios = payload.get("audios") or []
        if not audios:
            raise VoiceError("Sarvam returned no audio")
        return AudioClip(data=base64.b64decode(audios[0]), mime="audio/wav", provider=self.name)


# ---------------------------------------------------------------- helpers


def _call(request: urllib.request.Request, *, opener=None) -> dict:
    try:
        with _open(request, opener=opener) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise VoiceError(f"Sarvam API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VoiceError(f"could not reach the Sarvam API: {exc.reason}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VoiceError("Sarvam API returned a non-JSON response") from exc


def _multipart(boundary: str, fields: dict[str, str], file: tuple[str, str, str, bytes]) -> bytes:
    name, filename, mime, data = file
    out = bytearray()
    for key, value in fields.items():
        out += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
        ).encode()
    out += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
        f'filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'
    ).encode()
    out += data
    out += f"\r\n--{boundary}--\r\n".encode()
    return bytes(out)

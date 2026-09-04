"""Voice providers: Sarvam request shape (no network), factory, browser markers, Whisper helper."""

import dataclasses
import io
import json
import wave
from pathlib import Path

import pytest

from crew_ops_advisor.config import Settings
from crew_ops_advisor.voice import (
    BrowserSTT,
    BrowserTTS,
    SarvamSTT,
    SarvamTTS,
    VoiceError,
    WhisperSTT,
    make_stt,
    make_tts,
)
from crew_ops_advisor.voice import audio as audio_norm
from crew_ops_advisor.voice.whisper import _whisper_language

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def fake_opener(payload, recorder):
    def opener(request, timeout):
        recorder.append(request)
        return FakeResponse(json.dumps(payload).encode())

    return opener


def test_sarvam_stt_builds_a_multipart_request_and_reads_the_transcript():
    seen = []
    stt = SarvamSTT(
        "key-123",
        model="saarika:v2.5",
        language="en-IN",
        opener=fake_opener({"transcript": " Who is on reserve? ", "language_code": "en-IN"}, seen),
    )
    t = stt.transcribe(b"RIFF....", mime="audio/wav")
    assert t.text == "Who is on reserve?" and t.language == "en-IN" and t.provider == "sarvam"
    req = seen[0]
    assert req.full_url == "https://api.sarvam.ai/speech-to-text" and req.get_method() == "POST"
    assert req.get_header("Api-subscription-key") == "key-123"
    assert req.get_header("Content-type").startswith("multipart/form-data; boundary=")
    body = req.data.decode(errors="ignore")
    assert 'name="model"\r\n\r\nsaarika:v2.5' in body
    assert 'name="language_code"\r\n\r\nen-IN' in body
    assert 'name="file"; filename="speech.wav"' in body and "Content-Type: audio/wav" in body


def test_sarvam_tts_posts_json_and_decodes_base64_audio():
    seen = []
    tts = SarvamTTS(
        "key-123", speaker="anushka", opener=fake_opener({"audios": ["UklGRg=="]}, seen)
    )
    clip = tts.synthesize("Twelve reserves at BLR.", language="en-IN")
    assert clip.data == b"RIFF" and clip.mime == "audio/wav"
    sent = json.loads(seen[0].data)
    assert sent["text"] == "Twelve reserves at BLR." and sent["speaker"] == "anushka"
    assert sent["target_language_code"] == "en-IN" and sent["model"] == "bulbul:v2"


def test_sarvam_requires_a_key_and_reports_http_errors():
    with pytest.raises(VoiceError, match="SARVAM_API_KEY"):
        SarvamSTT(None).transcribe(b"x", mime="audio/wav")
    import urllib.error

    def failing(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 401, "unauthorised", {}, io.BytesIO(b"bad key")
        )

    with pytest.raises(VoiceError, match="401"):
        SarvamSTT("k", opener=failing).transcribe(b"x", mime="audio/wav")


def test_factory_honours_settings():
    base = Settings.from_env()
    assert isinstance(make_stt(dataclasses.replace(base, stt_provider="browser")), BrowserSTT)
    assert isinstance(make_stt(dataclasses.replace(base, stt_provider="sarvam")), SarvamSTT)
    assert isinstance(make_tts(dataclasses.replace(base, tts_provider="browser")), BrowserTTS)
    assert isinstance(make_tts(dataclasses.replace(base, tts_provider="sarvam")), SarvamTTS)
    with pytest.raises(ValueError):
        make_stt(dataclasses.replace(base, stt_provider="nope"))


def test_browser_providers_are_client_side_markers():
    assert not BrowserSTT().server_side and not BrowserTTS().server_side
    with pytest.raises(VoiceError):
        BrowserSTT().transcribe(b"x", mime="audio/wav")


def test_whisper_language_normalisation():
    assert _whisper_language("en-IN") == "en" and _whisper_language(None) is None
    assert _whisper_language("unknown") is None and _whisper_language("hi") == "hi"


@pytest.mark.skipif(not WhisperSTT.available(), reason="faster-whisper not installed")
def test_whisper_transcribes_the_fixture_clip():
    wav = (FIXTURES / "reserve_question.wav").read_bytes()
    t = WhisperSTT("base").transcribe(wav, mime="audio/wav", language="en")
    assert t.text.lower().replace("?", "") == "who is on reserve at blr tomorrow"
    assert t.provider == "whisper" and t.language == "en"


# ---- recording normalisation (the browser uploads WebM/MP4/OGG; the server makes WAV) ----


def _wav_params(data: bytes):
    with wave.open(io.BytesIO(data)) as w:
        return w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()


@pytest.mark.skipif(not audio_norm.available(), reason="PyAV not installed")
def test_browser_style_webm_recording_becomes_16k_mono_wav():
    # reserve_question.webm is a live-style WebM/Opus clip (no duration header, no cues),
    # the same shape Chrome's MediaRecorder produces and Chrome's own decoder rejects.
    webm = (FIXTURES / "reserve_question.webm").read_bytes()
    data, mime = audio_norm.to_wav(webm, "audio/webm;codecs=opus")
    channels, width, rate, frames = _wav_params(data)
    assert mime == "audio/wav" and (channels, width, rate) == (1, 2, 16000)
    assert 1.5 < frames / rate < 2.5  # ~2 s question


@pytest.mark.skipif(not audio_norm.available(), reason="PyAV not installed")
def test_wav_input_is_normalised_too_and_garbage_is_rejected():
    wav = (FIXTURES / "reserve_question.wav").read_bytes()
    data, mime = audio_norm.to_wav(wav, "audio/wav")
    assert mime == "audio/wav" and _wav_params(data)[:3] == (1, 2, 16000)
    with pytest.raises(VoiceError, match="could not read the recording"):
        audio_norm.to_wav(b"not audio at all" * 100, "audio/webm")
    with pytest.raises(VoiceError, match="empty"):
        audio_norm.to_wav(b"", "audio/webm")


@pytest.mark.skipif(not audio_norm.available(), reason="PyAV not installed")
def test_a_mis_click_recording_is_reported_as_too_short():
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)  # 0.1 s of silence
    with pytest.raises(VoiceError, match="too short"):
        audio_norm.to_wav(buf.getvalue(), "audio/wav")


@pytest.mark.skipif(not WhisperSTT.available(), reason="faster-whisper not installed")
def test_whisper_transcribes_a_normalised_browser_recording():
    webm = (FIXTURES / "reserve_question.webm").read_bytes()
    data, mime = audio_norm.to_wav(webm, "audio/webm")
    t = WhisperSTT("base").transcribe(data, mime=mime, language="en")
    assert t.text.lower().replace("?", "") == "who is on reserve at blr tomorrow"

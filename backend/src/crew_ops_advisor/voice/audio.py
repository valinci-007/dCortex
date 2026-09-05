"""Normalise whatever the browser recorded into 16 kHz mono PCM16 WAV.

Browsers record with MediaRecorder in whichever container they like — WebM/Opus in Chrome
and Firefox, MP4/AAC in Safari — and none of them writes a duration header, because the
recording is live. Decoding that in the page with the Web Audio API is unreliable (Chrome
regularly rejects its own MediaRecorder output with "Unable to decode audio data"), so the
page uploads the recording untouched and the server converts it here with FFmpeg through
PyAV, which faster-whisper already depends on. Every speech-to-text provider then sees the
same canonical WAV, which is also the format Sarvam's API is happiest with.
"""

from __future__ import annotations

import io
import wave

from crew_ops_advisor.voice.base import VoiceError

TARGET_RATE = 16000
MIN_SECONDS = 0.25  # anything shorter is a mis-click, not a question
WAV_MIME = "audio/wav"


def available() -> bool:
    try:
        import av  # noqa: F401
    except ImportError:
        return False
    return True


def to_wav(data: bytes, mime: str) -> tuple[bytes, str]:
    """Return `(wav_bytes, "audio/wav")` for any container FFmpeg can read.

    Without PyAV the input is passed through unchanged, so a provider that accepts the
    browser's native format still works.
    """
    if not data:
        raise VoiceError("the recording is empty")
    try:
        import av
    except ImportError:
        return data, mime
    resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_RATE)
    pcm = bytearray()
    try:
        with av.open(io.BytesIO(data), mode="r", metadata_errors="ignore") as container:
            for frame in _frames(container, av):
                for out in resampler.resample(frame):
                    pcm += _samples(out)
            for out in resampler.resample(None):  # flush the resampler
                pcm += _samples(out)
    except Exception as exc:  # noqa: BLE001 - every demux/decode failure is one user-facing error
        raise VoiceError(
            f"could not read the recording ({mime or 'unknown type'}, {len(data)} bytes): {exc}"
        ) from exc
    seconds = len(pcm) / (2 * TARGET_RATE)
    if seconds < MIN_SECONDS:
        raise VoiceError(
            f"the recording is too short ({seconds:.2f}s) — hold the microphone a moment longer"
        )
    return _wav(bytes(pcm)), WAV_MIME


def _frames(container, av):
    """Decode audio frames, skipping the odd corrupt packet a live recording can end with."""
    frames = container.decode(audio=0)
    while True:
        try:
            yield next(frames)
        except StopIteration:
            return
        except av.error.InvalidDataError:
            continue


def _samples(frame) -> bytes:
    # Packed s16 mono: plane 0 holds every sample; its buffer may carry alignment padding.
    return bytes(frame.planes[0])[: frame.samples * 2]


def _wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(TARGET_RATE)
        out.writeframes(pcm)
    return buf.getvalue()

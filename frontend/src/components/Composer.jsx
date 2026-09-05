import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { browserRecognitionAvailable, canRecord, recognizeInBrowser, startRecording } from "../audio.js";
import { MicIcon, SendIcon, StopIcon } from "./icons.jsx";
import Waveform from "./Waveform.jsx";

const AUTO_SEND_KEY = "crew-ops-advisor:voice-auto-send";

function readAutoSend() {
  try {
    const v = localStorage.getItem(AUTO_SEND_KEY);
    return v === null ? true : v === "1";
  } catch {
    return true;
  }
}

function clock(ms) {
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function Composer({ value, onChange, onSubmit, disabled, voice, dev = false }) {
  const ref = useRef(null);
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [voiceError, setVoiceError] = useState(null);
  const [autoSend, setAutoSend] = useState(readAutoSend);
  const controller = useRef(null);

  useEffect(() => {
    if (!disabled && !listening && !transcribing) ref.current?.focus();
  }, [disabled, listening, transcribing]);

  useEffect(() => {
    try {
      localStorage.setItem(AUTO_SEND_KEY, autoSend ? "1" : "0");
    } catch {
      // ignore
    }
  }, [autoSend]);

  // Recording timer, and Esc to stop.
  useEffect(() => {
    if (!listening) return undefined;
    const started = controller.current?.startedAt || Date.now();
    setElapsed(0);
    const tick = setInterval(() => setElapsed(Date.now() - started), 250);
    const onKey = (e) => {
      if (e.key === "Escape") stopVoice();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      clearInterval(tick);
      window.removeEventListener("keydown", onKey);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listening]);

  const serverSide = !!voice?.stt?.server_side;
  const micSupported = serverSide ? canRecord() : browserRecognitionAvailable();
  const micTitle = !micSupported
    ? "Voice input is not available in this browser"
    : listening
      ? "Stop and transcribe (Esc)"
      : serverSide
        ? `Speak your question (transcribed by the ${voice.stt.provider} provider)`
        : "Speak your question (browser speech recognition)";

  const finish = (text) => {
    const t = (text || "").trim();
    if (!t) {
      setVoiceError("Nothing was recognised — try again a little closer to the microphone.");
      return;
    }
    onChange(t);
    if (autoSend) onSubmit(t);
  };

  const startVoice = async () => {
    setVoiceError(null);
    try {
      if (serverSide) {
        controller.current = await startRecording();
        setListening(true);
      } else {
        const rec = recognizeInBrowser({ language: voice?.stt?.language || "en-IN", onInterim: onChange });
        controller.current = rec;
        setListening(true);
        const text = await rec.done;
        setListening(false);
        controller.current = null;
        finish(text);
      }
    } catch (e) {
      setListening(false);
      controller.current = null;
      setVoiceError(
        e.name === "NotAllowedError" || e.message === "not-allowed"
          ? "Microphone access was denied — allow it in the address bar and try again."
          : e.message,
      );
    }
  };

  const stopVoice = async () => {
    const c = controller.current;
    if (!c) return;
    if (serverSide) {
      setListening(false);
      setTranscribing(true);
      try {
        const recording = await c.stop();
        if (!recording.size) {
          setVoiceError("Nothing was recorded — hold the microphone a moment longer before stopping.");
          return;
        }
        const res = await api.transcribe(recording, voice?.stt?.language);
        finish(res.text);
      } catch (e) {
        setVoiceError(`Transcription failed: ${e.message}`);
      } finally {
        setTranscribing(false);
        controller.current = null;
      }
    } else {
      c.stop(); // onend resolves the promise in startVoice
    }
  };

  const submit = (e) => {
    e.preventDefault();
    onSubmit(value);
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(value);
    }
  };

  const micState = transcribing ? "busy" : listening ? "on" : "";
  const levelFn = controller.current?.level;

  return (
    <form className="composer" onSubmit={submit}>
      <div className={`composer-row ${listening ? "is-listening" : ""}`}>
        {listening ? (
          <div className="listening" role="status" aria-live="polite">
            <span className="rec-dot" aria-hidden="true" />
            <span className="rec-time">{clock(elapsed)}</span>
            <Waveform level={levelFn} active={listening} />
            <span className="rec-hint">Listening — press ■ or Esc when you're done</span>
          </div>
        ) : (
          <textarea
            ref={ref}
            rows={2}
            value={value}
            disabled={disabled || transcribing}
            placeholder={
              transcribing
                ? "Transcribing…"
                : "e.g. Captain C-1042 called in sick for tomorrow — which flights are now uncrewed?"
            }
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={onKeyDown}
          />
        )}
        <button
          type="button"
          className={`mic ${micState}`}
          onClick={listening ? stopVoice : startVoice}
          disabled={disabled || transcribing || !micSupported}
          title={micTitle}
          aria-label={listening ? "Stop recording" : "Speak your question"}
          aria-pressed={listening}
        >
          {transcribing ? <span className="spinner" aria-hidden="true" /> : listening ? <StopIcon /> : <MicIcon />}
        </button>
        <button
          type="submit"
          className="ask"
          disabled={disabled || listening || transcribing || !value.trim()}
          title="Ask (Enter)"
        >
          {disabled ? <span className="spinner" aria-hidden="true" /> : <SendIcon />}
          <span>{disabled ? "Working…" : "Ask"}</span>
        </button>
      </div>
      <div className="composer-foot">
        <label className="auto-send">
          <input type="checkbox" checked={autoSend} onChange={(e) => setAutoSend(e.target.checked)} />
          send voice questions automatically
        </label>
        {voice && dev && (
          <span className="muted small">
            voice: {voice.stt.provider}
            {voice.stt.server_side ? "" : " (in browser)"}
          </span>
        )}
        {transcribing && <span className="muted small">transcribing…</span>}
        {voiceError && <span className="voice-error">{voiceError}</span>}
      </div>
    </form>
  );
}

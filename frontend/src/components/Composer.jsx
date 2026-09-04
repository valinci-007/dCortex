import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { browserRecognitionAvailable, canRecord, recognizeInBrowser, startRecording } from "../audio.js";

const AUTO_SEND_KEY = "crew-ops-advisor:voice-auto-send";

function readAutoSend() {
  try {
    const v = localStorage.getItem(AUTO_SEND_KEY);
    return v === null ? true : v === "1";
  } catch {
    return true;
  }
}

export default function Composer({ value, onChange, onSubmit, disabled, voice }) {
  const ref = useRef(null);
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const [autoSend, setAutoSend] = useState(readAutoSend);
  const controller = useRef(null);

  useEffect(() => {
    if (!disabled && !listening) ref.current?.focus();
  }, [disabled, listening]);

  useEffect(() => {
    try {
      localStorage.setItem(AUTO_SEND_KEY, autoSend ? "1" : "0");
    } catch {
      // ignore
    }
  }, [autoSend]);

  const serverSide = !!voice?.stt?.server_side;
  const micSupported = serverSide ? canRecord() : browserRecognitionAvailable();
  const micTitle = !micSupported
    ? "Voice input is not available in this browser"
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
      setVoiceError(e.message === "not-allowed" ? "Microphone access was denied." : e.message);
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

  return (
    <form className="composer" onSubmit={submit}>
      <div className="composer-row">
        <textarea
          ref={ref}
          rows={2}
          value={value}
          disabled={disabled || transcribing}
          placeholder={
            listening
              ? "Listening… click the microphone again to stop."
              : "e.g. Captain C-1042 called in sick for tomorrow — which flights are now uncrewed?"
          }
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button
          type="button"
          className={`mic ${listening ? "on" : ""}`}
          onClick={listening ? stopVoice : startVoice}
          disabled={disabled || transcribing || !micSupported}
          title={micTitle}
          aria-pressed={listening}
        >
          {transcribing ? "…" : listening ? "■" : "🎤"}
        </button>
        <button type="submit" disabled={disabled || transcribing || !value.trim()}>
          {disabled ? "Working…" : "Ask"}
        </button>
      </div>
      <div className="composer-foot">
        <label className="auto-send">
          <input type="checkbox" checked={autoSend} onChange={(e) => setAutoSend(e.target.checked)} />
          send voice questions automatically
        </label>
        {voice && (
          <span className="muted small">
            voice: {voice.stt.provider}
            {voice.stt.server_side ? "" : " (in browser)"}
            {transcribing ? " · transcribing…" : listening ? " · recording" : ""}
          </span>
        )}
        {voiceError && <span className="voice-error">{voiceError}</span>}
      </div>
    </form>
  );
}

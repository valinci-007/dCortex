import { useEffect, useRef, useState } from "react";
import { marked } from "marked";
import { api } from "../api.js";
import { canSpeak, speakInBrowser, speakableText } from "../audio.js";
import Trace from "./Trace.jsx";

marked.setOptions({ breaks: true, gfm: true });

function splitReasoning(text) {
  // The advisor writes the direct answer, then a "Reasoning:" section, then optional
  // offline / unverified notes. Keep them visually distinct.
  const idx = text.indexOf("\nReasoning:");
  if (idx === -1) return { answer: text, reasoning: null };
  return { answer: text.slice(0, idx), reasoning: text.slice(idx + 1) };
}

function ReadAloud({ text, voice }) {
  const [speaking, setSpeaking] = useState(false);
  const stopRef = useRef(null);
  const language = voice?.tts?.language || "en-IN";
  const serverSide = !!voice?.tts?.server_side;
  const supported = serverSide || canSpeak();

  useEffect(() => () => stopRef.current?.(), []);

  const toggle = async () => {
    if (speaking) {
      stopRef.current?.();
      stopRef.current = null;
      setSpeaking(false);
      return;
    }
    const body = speakableText(text);
    if (!body) return;
    setSpeaking(true);
    try {
      if (serverSide) {
        const blob = await api.speak(body, language);
        const audio = new Audio(URL.createObjectURL(blob));
        audio.onended = () => setSpeaking(false);
        stopRef.current = () => audio.pause();
        await audio.play();
      } else {
        const stop = speakInBrowser(body, { language });
        stopRef.current = stop;
        const check = setInterval(() => {
          if (!window.speechSynthesis.speaking) {
            clearInterval(check);
            setSpeaking(false);
          }
        }, 300);
      }
    } catch {
      setSpeaking(false);
    }
  };

  if (!supported) return null;
  return (
    <button className="link small" onClick={toggle} title={`Read aloud (${voice?.tts?.provider || "browser"} voice)`}>
      {speaking ? "stop reading" : "read aloud"}
    </button>
  );
}

/** "C-1042" → "C-1042 (A. Nair)" using the local directory — the name never went to the model. */
function joinNames(text, directory) {
  if (!directory) return text;
  return text.replace(/\bC-\d{4}\b(?!\s*\()/g, (id) => (directory[id] ? `${id} (${directory[id]})` : id));
}

export default function Message({ message, voice, directory }) {
  const [showTrace, setShowTrace] = useState(false);
  if (message.role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">{message.text}</div>
      </div>
    );
  }
  if (!message.answer) {
    return (
      <div className="msg assistant">
        <div className="card error">Request failed: {message.error}</div>
      </div>
    );
  }
  const a = message.answer;
  const { answer: rawAnswer, reasoning: rawReasoning } = splitReasoning(a.answer || "");
  const answer = joinNames(rawAnswer, directory);
  const reasoning = joinNames(rawReasoning, directory);
  const grounding = a.grounding;
  const fallback = Boolean(a.fallback_reason);
  const offline = a.mode.includes("offline");
  return (
    <div className="msg assistant">
      <div className={`card ${a.refused ? "refused" : ""}`}>
        <div className="meta">
          <span className={`badge provider-${offline ? "offline" : a.mode}`}>
            {fallback ? "offline fallback" : offline ? "offline mode" : "AI-assisted"}
          </span>
          {a.refused && <span className="badge warn">declined to answer</span>}
          {directory && !offline && (
            <span className="badge good" title="Crew names were removed before the question and data reached the model; they are joined back here from the local directory.">
              names never sent to model
            </span>
          )}
          {a.error && <span className="badge bad">error</span>}
          {a.redactions && a.redactions.length > 0 && (
            <span className="badge warn" title={`removed: ${a.redactions.join(", ")}`}>
              implementation terms withheld
            </span>
          )}
          {grounding && (
            <span
              className={`badge ${grounding.ok ? "good" : "bad"}`}
              title={
                grounding.ok
                  ? `${grounding.checked} facts checked against tool evidence`
                  : `not in tool evidence: ${grounding.unsupported.join(", ")}`
              }
            >
              {grounding.ok ? `grounded · ${grounding.checked} facts` : "unverified figures"}
            </span>
          )}
          <span className="badge muted">{Math.round(a.elapsed_ms / 100) / 10} s</span>
          {a.cost_usd != null && <span className="badge muted">${a.cost_usd.toFixed(3)}</span>}
          <span className="badge muted">
            {a.trace.filter((s) => s.kind === "tool").length} tool call
            {a.trace.filter((s) => s.kind === "tool").length === 1 ? "" : "s"}
          </span>
        </div>
        {fallback && (
          <div className="note warn">
            Model provider failed ({a.fallback_reason}); answered by the offline router instead.
          </div>
        )}
        <div className="answer" dangerouslySetInnerHTML={{ __html: marked.parse(answer) }} />
        {reasoning && (
          <div className="reasoning" dangerouslySetInnerHTML={{ __html: marked.parse(reasoning) }} />
        )}
        <div className="card-actions">
          <button className="link small" onClick={() => setShowTrace((v) => !v)}>
            {showTrace ? "hide" : "show"} reasoning trail
          </button>
          <ReadAloud text={a.answer || ""} voice={voice} />
        </div>
        {showTrace && <Trace trace={a.trace} usage={a.usage} />}
      </div>
    </div>
  );
}

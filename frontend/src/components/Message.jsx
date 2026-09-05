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

// How far the controller can lean on an answer (ADR-0018 §4).
const CONFIDENCE = {
  verified: { cls: "good", hint: "Every fact traced to a data result; no correction was needed" },
  "verified after correction": { cls: "good", hint: "The first draft was corrected and the result verified against the data" },
  unverified: { cls: "bad", hint: "Figures remain that no data result supports — flagged in the answer" },
  declined: { cls: "warn", hint: "The Advisor refused rather than guess" },
};

/** "C-1042" → "C-1042 (A. Nair)" using the local directory — the name never went to the model. */
function joinNames(text, directory) {
  if (!directory || !text) return text; // no directory (PII mode full) or no Reasoning section
  return text.replace(/\bC-\d{4}\b(?!\s*\()/g, (id) => (directory[id] ? `${id} (${directory[id]})` : id));
}

export default function Message({ message, voice, directory, dev = false }) {
  const [showTrace, setShowTrace] = useState(false);
  if (message.role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">{message.text}</div>
      </div>
    );
  }
  if (message.pending) {
    return (
      <div className="msg assistant">
        <div className="card pending">
          <ul className="progress">
            {message.steps.map((s, i) => (
              <li key={i} className={s.done ? (s.ok ? "done" : "failed") : "running"}>
                <span className="tick" aria-hidden="true">{s.done ? (s.ok ? "✓" : "✗") : ""}</span>
                <span className="step-label">{s.label}</span>
                {dev && s.done && s.summary && <span className="step-summary">{s.summary}</span>}
              </li>
            ))}
            {(message.phase || message.steps.length === 0) && !message.text && (
              <li className="running">
                <span className="tick" aria-hidden="true" />
                <span className="step-label">{message.phase || "reading the question"}</span>
              </li>
            )}
          </ul>
          {message.text && (
            <div className="answer streaming" dangerouslySetInnerHTML={{ __html: marked.parse(message.text) }} />
          )}
          {message.phase && message.text && <div className="phase">{message.phase}…</div>}
        </div>
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
          {/* Controller view: only what changes how far the answer can be trusted. */}
          {(offline || fallback) && (
            <span className="badge provider-offline" title="Answered by the desk's rule-based router, not the model">
              {fallback ? "offline fallback" : "offline mode"}
            </span>
          )}
          {dev && !offline && !fallback && <span className={`badge provider-${a.mode}`}>AI-assisted</span>}
          {a.refused && <span className="badge warn">declined to answer</span>}
          {dev && directory && !offline && (
            <span className="badge good" title="Crew names were removed before the question and data reached the model; they are joined back here from the local directory.">
              names never sent to model
            </span>
          )}
          {a.error && <span className="badge bad">error</span>}
          {dev && a.redactions && a.redactions.length > 0 && (
            <span className="badge warn" title={`removed: ${a.redactions.join(", ")}`}>
              implementation terms withheld
            </span>
          )}
          {a.confidence && a.confidence !== "error" && !a.refused && (
            <span
              className={`badge ${CONFIDENCE[a.confidence]?.cls || "muted"}`}
              title={
                (CONFIDENCE[a.confidence]?.hint || "") +
                (grounding
                  ? grounding.ok
                    ? ` · ${grounding.checked} facts checked against the data results`
                    : ` · not in any data result: ${grounding.unsupported.join(", ")}`
                  : "")
              }
            >
              {a.confidence === "unverified" ? "unverified figures" : a.confidence}
              {dev && grounding?.ok && a.confidence.startsWith("verified") ? ` · ${grounding.checked} facts` : ""}
            </span>
          )}
          {dev && <span className="badge muted">{Math.round(a.elapsed_ms / 100) / 10} s</span>}
          {dev && a.cost_usd != null && <span className="badge muted">${a.cost_usd.toFixed(3)}</span>}
          {dev && (
            <span className="badge muted">
              {a.trace.filter((s) => s.kind === "tool").length} tool call
              {a.trace.filter((s) => s.kind === "tool").length === 1 ? "" : "s"}
            </span>
          )}
        </div>
        {fallback && (
          <div className="note warn">
            {dev
              ? `Model provider failed (${a.fallback_reason}); answered by the offline router instead.`
              : "The assistant is temporarily in offline mode — this answer comes from the desk's rule-based router and covers lookups and standard checks only."}
          </div>
        )}
        <div className="answer" dangerouslySetInnerHTML={{ __html: marked.parse(answer) }} />
        {reasoning && (
          <div className="reasoning" dangerouslySetInnerHTML={{ __html: marked.parse(reasoning) }} />
        )}
        <div className="card-actions">
          {dev && (
            <button className="link small" onClick={() => setShowTrace((v) => !v)}>
              {showTrace ? "hide" : "show"} reasoning trail
            </button>
          )}
          <ReadAloud text={a.answer || ""} voice={voice} />
        </div>
        {dev && showTrace && <Trace trace={a.trace} usage={a.usage} />}
      </div>
    </div>
  );
}

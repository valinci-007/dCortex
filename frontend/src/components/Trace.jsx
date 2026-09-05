import { useState } from "react";

function Args({ args }) {
  const entries = Object.entries(args || {});
  if (entries.length === 0) return <span className="mono muted">()</span>;
  return (
    <span className="mono">
      ({entries.map(([k, v], i) => (
        <span key={k}>
          {i > 0 && ", "}
          {k}=<b>{typeof v === "string" ? v : JSON.stringify(v)}</b>
        </span>
      ))})
    </span>
  );
}

function ToolStep({ step }) {
  const [open, setOpen] = useState(false);
  return (
    <li className={`step tool ${step.ok ? "ok" : "failed"}`}>
      <div className="step-head">
        <span className="mark">{step.ok ? "✓" : "✗"}</span>
        <span className="mono name">{step.name}</span>
        <Args args={step.arguments} />
        <span className="muted"> → {step.summary}</span>
        <span className="ms">{step.elapsed_ms.toFixed(1)} ms</span>
        {step.result && (
          <button className="link small" onClick={() => setOpen((v) => !v)}>
            {open ? "hide" : "show"} result
          </button>
        )}
      </div>
      {open && <pre className="result">{JSON.stringify(step.result, null, 2)}</pre>}
    </li>
  );
}

export default function Trace({ trace, usage }) {
  return (
    <div className="trace">
      <ul>
        {trace.map((s, i) =>
          s.kind === "tool" ? (
            <ToolStep key={i} step={s} />
          ) : (
            <li key={i} className="step llm">
              <span className="mark">·</span>
              <span className="name">model / {s.name}</span>
              <span className="muted"> {s.summary}</span>
              <span className="ms">{Math.round(s.elapsed_ms)} ms</span>
            </li>
          ),
        )}
      </ul>
      {usage && Object.keys(usage).length > 0 && (
        <div className="usage mono muted">
          tokens: {Object.entries(usage).map(([k, v]) => `${k.replace("_tokens", "")} ${v}`).join(" · ")}
        </div>
      )}
    </div>
  );
}

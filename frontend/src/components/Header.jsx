export default function Header({ health, context, chat, samplesOpen, onToggleSamples }) {
  const provider = health?.provider || "…";
  return (
    <header className="header">
      <div className="brand">
        <div className="eyebrow">dCortex Air · Crew Control</div>
        <h1>Crew Ops Advisor</h1>
        {chat && <div className="chat-heading">{chat.title}</div>}
      </div>
      <div className="status">
        <span className={`badge provider-${provider}`} title="How answers are produced">
          {provider === "offline" ? "offline mode" : "AI-assisted"}
        </span>
        {context && (
          <span className="badge muted" title="Dataset snapshot (UTC)">
            snapshot {context.snapshot_utc}
          </span>
        )}
        <button className="link" onClick={onToggleSamples} title="Sample questions by tier">
          {samplesOpen ? "hide samples" : "sample questions"}
        </button>
      </div>
    </header>
  );
}

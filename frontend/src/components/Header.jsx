import { MenuIcon, PlusIcon } from "./icons.jsx";

export default function Header({
  health,
  context,
  chat,
  busy,
  samplesOpen,
  onToggleSamples,
  onNewChat,
  onToggleSidebar,
  sidebarOpen,
  watchCount,
  watchOpen,
  onToggleWatch,
  dev,
  onToggleDev,
}) {
  const provider = health?.provider || "…";
  const asOf = context?.snapshot_utc ? context.snapshot_utc.replace("T", " ").replace(":00Z", "Z") : null;
  return (
    <header className="header">
      <div className="brand-row">
        <button
          type="button"
          className="icon-btn sidebar-toggle"
          onClick={onToggleSidebar}
          title={sidebarOpen ? "Hide conversations" : "Show conversations"}
          aria-label="Toggle conversations"
          aria-expanded={sidebarOpen}
        >
          <MenuIcon />
        </button>
        <div className="brand">
          <div className="eyebrow">dCortex Air · Crew Control</div>
          <h1>Crew Ops Advisor</h1>
          {chat && <div className="chat-heading">{chat.title}</div>}
        </div>
      </div>
      <div className="status">
        {(dev || provider === "offline") && (
          <span className={`badge provider-${provider}`} title="How answers are produced">
            {provider === "offline" ? "offline mode" : "AI-assisted"}
          </span>
        )}
        {asOf && (
          <span className="badge muted" title="Operational data time (UTC)">
            {dev ? `snapshot ${context.snapshot_utc}` : `data as of ${asOf}`}
          </span>
        )}
        {dev && context?.pii_mode === "minimal" && (
          <span className="badge good" title="PII minimal: crew names never leave this machine — the model sees ids; names are joined in the browser">
            PII: minimal
          </span>
        )}
        {watchCount != null && (
          <button className="link" onClick={onToggleWatch} title="What needs attention tomorrow — from the rules and the roster">
            {watchOpen ? "hide watchlist" : `watchlist${watchCount ? ` (${watchCount})` : ""}`}
          </button>
        )}
        {dev && (
          <button className="link" onClick={onToggleSamples} title="Sample questions by tier">
            {samplesOpen ? "hide samples" : "sample questions"}
          </button>
        )}
        <button
          type="button"
          className="new-chat-btn"
          onClick={onNewChat}
          disabled={busy}
          title="Start a new conversation"
        >
          <PlusIcon width={16} height={16} />
          <span>New chat</span>
        </button>
        <button
          type="button"
          className={`dev-toggle ${dev ? "on" : ""}`}
          onClick={onToggleDev}
          title={dev ? "Developer view on — traces, timings, cost, sample questions" : "Developer view: traces, timings, cost, sample questions"}
          aria-pressed={dev}
        >
          dev
        </button>
      </div>
    </header>
  );
}

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
}) {
  const provider = health?.provider || "…";
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
      </div>
    </header>
  );
}

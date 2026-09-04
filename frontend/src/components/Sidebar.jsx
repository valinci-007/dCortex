function relative(iso) {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  const d = Math.floor(s / 86400);
  return d === 1 ? "yesterday" : `${d} days ago`;
}

export default function Sidebar({ chats, activeId, onNew, onSelect, onRename, onDelete, busy }) {
  return (
    <aside className="sidebar">
      <button className="new-chat" onClick={onNew} disabled={busy}>
        + New chat
      </button>
      <div className="rail-title">Conversations</div>
      {chats.length === 0 && <div className="sidebar-empty">No conversations yet.</div>}
      <ul className="chat-list">
        {chats.map((c) => (
          <li key={c.id} className={c.id === activeId ? "active" : ""}>
            <button className="chat-item" onClick={() => onSelect(c.id)} disabled={busy} title={c.title}>
              <span className="chat-title">{c.title}</span>
              <span className="chat-meta">
                {c.message_count / 2 | 0} Q · {relative(c.updated_at)}
              </span>
            </button>
            <div className="chat-actions">
              <button className="icon" title="Rename" onClick={() => onRename(c)} disabled={busy}>
                ✎
              </button>
              <button className="icon danger" title="Delete" onClick={() => onDelete(c)} disabled={busy}>
                ×
              </button>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}

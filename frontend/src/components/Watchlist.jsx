// Proactive watchlist (ADR-0018 §2): what needs attention before anyone asks. Deterministic —
// the backend computes it from the rules and the roster; no model call is involved.

const SEVERITY_LABEL = { breach: "breach", tight: "tight", watch: "watch" };

function Item({ item, directory, onPick, question }) {
  const name = item.name || directory?.[item.crew_id];
  return (
    <li className={`watch-item ${item.severity}`}>
      <span className={`sev ${item.severity}`}>{SEVERITY_LABEL[item.severity] || item.severity}</span>
      <div className="watch-body">
        <div className="watch-who">
          <span className="mono">{item.crew_id}</span>
          {name && <span> {name}</span>}
          {item.rank && <span className="muted"> · {item.rank}</span>}
        </div>
        <div className="watch-note">{item.note}</div>
      </div>
      {onPick && (
        <button type="button" className="link small" onClick={() => onPick(question(item))} title="Ask about this">
          ask
        </button>
      )}
    </li>
  );
}

export default function Watchlist({ watchlist, directory, onPick, compact = false, dev = false }) {
  if (!watchlist) return null;
  const groups = [
    {
      title: "Near a duty limit",
      items: watchlist.near_limits,
      question: (i) => `Check ${i.crew_id}'s duty headroom for ${watchlist.date} — what can they still legally fly?`,
    },
    {
      title: "Certifications lapsing",
      items: watchlist.expiring_certifications,
      question: (i) =>
        i.rostered_after_expiry?.length
          ? `${i.crew_id}'s ${i.cert_type.replace(/_/g, " ")} expires ${i.expires} but they are rostered on ${i.rostered_after_expiry[0]} — resolve that assignment.`
          : `${i.crew_id}'s ${i.cert_type.replace(/_/g, " ")} expires ${i.expires} — is anything rostered after that?`,
    },
    {
      title: "Highest disruption risk",
      items: watchlist.high_risk,
      question: (i) => `${i.crew_id} has a high disruption-risk score — if they call in sick on ${watchlist.date}, which flights are exposed?`,
    },
    {
      title: "Uncovered in the active scenario",
      items: watchlist.uncovered_flights,
      question: (i) => `Who can cover ${i.flight_id || i.pairing_id} on ${i.date || watchlist.date}?`,
    },
  ].filter((g) => g.items && g.items.length);

  return (
    <section className={`watchlist ${compact ? "compact" : ""}`} aria-label="Watchlist">
      <div className="watch-head">
        <span className="rail-title">Watchlist · {watchlist.date}</span>
        <span className="muted small">
          {watchlist.count} item{watchlist.count === 1 ? "" : "s"}
          {dev ? " · from the rules and the roster, no model involved" : ""}
        </span>
      </div>
      {groups.length === 0 && <p className="muted small">Nothing needs attention for {watchlist.date}.</p>}
      {groups.map((g) => (
        <div className="watch-group" key={g.title}>
          <div className="tier-label">{g.title}</div>
          <ul className="watch-list">
            {g.items.map((item, i) => (
              <Item key={i} item={item} directory={directory} onPick={onPick} question={g.question} />
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

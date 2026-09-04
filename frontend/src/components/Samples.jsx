const TIER_LABELS = {
  1: "Tier 1 · lookup",
  2: "Tier 2 · consequence",
  3: "Tier 3 · recommendation",
};

export default function Samples({ samples, onPick, disabled }) {
  const byTier = { 1: [], 2: [], 3: [] };
  for (const s of samples) byTier[s.tier]?.push(s);
  return (
    <div className="samples">
      <div className="rail-title">Sample questions</div>
      {[1, 2, 3].map((tier) => (
        <div key={tier} className="sample-group">
          <div className={`tier-label tier-${tier}`}>{TIER_LABELS[tier]}</div>
          {byTier[tier].map((s) => (
            <button
              key={s.id}
              className="sample"
              disabled={disabled}
              onClick={() => onPick(s.prompt)}
              title={`${s.id} — click to load into the composer`}
            >
              <span className="sample-id">{s.id}</span>
              {s.prompt}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

function label(it) {
  if (it.override?.kind === "dish") return it.override.display_name;
  if (it.override?.kind === "none") return "Not a dish";
  return it.result.in_scope ? it.result.top[0].display_name : "Out of scope";
}

export default function History({ items, currentId, onSelect }) {
  if (items.length === 0) return null;
  return (
    <section className="hist">
      <p className="eyebrow">Earlier this session</p>
      <div className="hist-list">
        {items.map((it) => (
          <button key={it.id} className="hist-item" aria-current={it.id === currentId} onClick={() => onSelect(it)}>
            <img src={it.url} alt="" />
            <span>{label(it)}</span>
            <em>{it.override ? "corrected" : `${Math.round(it.result.top[0].confidence * 100)}%`}</em>
          </button>
        ))}
      </div>
    </section>
  );
}

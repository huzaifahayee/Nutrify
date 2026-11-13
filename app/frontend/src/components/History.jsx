export default function History({ items, currentId, onSelect }) {
  if (items.length === 0) return null;
  return (
    <section className="hist">
      <p className="eyebrow">Earlier this session</p>
      <div className="hist-list">
        {items.map((it) => (
          <button key={it.id} className="hist-item" aria-current={it.id === currentId} onClick={() => onSelect(it)}>
            <img src={it.url} alt="" />
            <span>{it.result.confident ? it.result.top[0].display_name : "Not sure"}</span>
            <em>{Math.round(it.result.top[0].confidence * 100)}%</em>
          </button>
        ))}
      </div>
    </section>
  );
}

export default function Guesses({ top }) {
  return (
    <ol className="guesses" aria-label="Top guesses">
      {top.map((g, i) => {
        const pct = Math.round(g.confidence * 100);
        return (
          <li key={g.dish}>
            <div className={`g-row${i === 0 ? " first" : ""}`}>
              <span className="g-name">{g.display_name}</span>
              <span className="g-lead" aria-hidden="true" />
              <span className="g-pct">{pct}%</span>
            </div>
            <div className="g-bar" aria-hidden="true"><i style={{ width: `${Math.max(pct, 1)}%` }} /></div>
          </li>
        );
      })}
    </ol>
  );
}

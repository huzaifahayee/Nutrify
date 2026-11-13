import Guesses from "./Guesses.jsx";
import PortionPicker from "./PortionPicker.jsx";

function Calories({ calories, portion, onPortion }) {
  const hasNumbers = calories && calories.kcal_typical > 0;
  return (
    <>
      <hr className="rule" />
      <p className="eyebrow">Estimated energy</p>
      {hasNumbers ? (
        <>
          <div className="kcal"><b>{calories.kcal_typical}</b><span>kcal</span></div>
          <p className="range">Likely between {calories.kcal_low} and {calories.kcal_high} kcal</p>
          <p className="serving">{calories.serving}</p>
        </>
      ) : (
        <p className="pending-cal">Calorie data for this dish isn't available yet.</p>
      )}
      <PortionPicker value={portion} onChange={onPortion} />
      {hasNumbers && calories.sources?.length > 0 && (
        <details className="src">
          <summary>Where these numbers come from</summary>
          <ul>
            {calories.sources.map((s, i) => (
              <li key={i}>
                {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : s.name}
                {s.note ? ` (${s.note})` : ""}
              </li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}

export default function ResultCard({ result, loading, portion, onPortion }) {
  if (!result) {
    return (
      <section className="result empty" aria-live="polite">
        {loading ? (
          <h2>Reading your photo…</h2>
        ) : (
          <>
            <h2>Your result appears here</h2>
            <p>We name the dish, say how sure we are, and estimate the calories for a serving.</p>
          </>
        )}
      </section>
    );
  }
  const best = result.top[0];
  const pct = Math.round(best.confidence * 100);
  return (
    <section className={`result${loading ? " busy" : ""}${result.confident ? "" : " unsure"}`} aria-live="polite">
      {result.confident ? (
        <>
          <p className="eyebrow">This looks like</p>
          <h2 className="dish">{best.display_name}</h2>
          <div className="sure"><span>{pct}% sure</span><span className="meter"><i style={{ width: `${pct}%` }} /></span></div>
        </>
      ) : (
        <>
          <span className="tag-unsure">Not sure</span>
          <h2 className="dish">Couldn't tell</h2>
          <p className="tip">Our best guess is {best.display_name} at {pct}%, below the {Math.round(result.threshold * 100)}% we need to answer. Try a closer, well-lit photo of one dish.</p>
        </>
      )}
      {result.confident && <Calories calories={result.calories} portion={portion} onPortion={onPortion} />}
      <hr className="rule" />
      <p className="eyebrow">Top guesses</p>
      <Guesses top={result.top} />
      <p className="fine">Estimates only, not medical or dietary advice. Calories depend on the recipe and portion.</p>
    </section>
  );
}

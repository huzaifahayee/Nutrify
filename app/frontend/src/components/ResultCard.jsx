import Guesses from "./Guesses.jsx";
import PortionPicker from "./PortionPicker.jsx";
import { DISHES } from "../dishes.js";

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

function OutOfScope({ result, loading, onReset }) {
  const best = result.top[0];
  const near = result.reason === "low_confidence";
  return (
    <section className={`result unsure${loading ? " busy" : ""}`} aria-live="polite">
      <span className="tag-unsure">Out of scope</span>
      <h2 className="dish">Not one of our dishes</h2>
      <p className="tip">
        This doesn't look like one of the dishes we support.
        {near && ` The closest match was ${best.display_name} at ${Math.round(best.confidence * 100)}%, which isn't sure enough to answer.`}
      </p>
      <hr className="rule" />
      <p className="eyebrow">Dishes we support</p>
      <ul className="dish-chips">
        {DISHES.map((d) => <li key={d}>{d}</li>)}
      </ul>
      <div className="actions left">
        <button className="btn primary" onClick={onReset}>Try another</button>
      </div>
      <p className="fine">Estimates only, not medical or dietary advice.</p>
    </section>
  );
}

export default function ResultCard({ result, loading, portion, onPortion, onReset }) {
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
  if (!result.in_scope) return <OutOfScope result={result} loading={loading} onReset={onReset} />;
  const best = result.top[0];
  const pct = Math.round(best.confidence * 100);
  return (
    <section className={`result${loading ? " busy" : ""}`} aria-live="polite">
      <p className="eyebrow">This looks like</p>
      <h2 className="dish">{best.display_name}</h2>
      <div className="sure"><span>{pct}% sure</span><span className="meter"><i style={{ width: `${pct}%` }} /></span></div>
      <Calories calories={result.calories} portion={portion} onPortion={onPortion} />
      <hr className="rule" />
      <p className="eyebrow">Top guesses</p>
      <Guesses top={result.top} />
      <p className="fine">Estimates only, not medical or dietary advice. Calories depend on the recipe and portion.</p>
    </section>
  );
}

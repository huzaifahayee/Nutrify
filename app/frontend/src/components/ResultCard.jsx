import Guesses from "./Guesses.jsx";
import PortionPicker from "./PortionPicker.jsx";
import DishPicker from "./DishPicker.jsx";
import Feedback from "./Feedback.jsx";
import { useCountUp } from "../hooks.js";

// A number that eases to its new value (used for calories).
function CountNum({ value }) {
  return <>{useCountUp(value, { duration: 700 })}</>;
}

// "Chicken Biryani" -> Chicken <em>Biryani</em> (last word in italic accent)
function DishName({ name }) {
  const words = name.split(" ");
  const last = words.pop();
  return <>{words.join(" ")}{words.length ? " " : ""}<em>{last}</em></>;
}

function Calories({ calories, portion, onPortion }) {
  const hasNumbers = calories && calories.kcal_typical > 0;
  return (
    <>
      <hr className="rule" />
      <p className="eyebrow">Estimated energy</p>
      {hasNumbers ? (
        <>
          <div className="tiles">
            <div className="tile"><b><CountNum value={calories.kcal_typical} /></b><span>kcal, typical</span></div>
            <div className="tile"><b><CountNum value={calories.kcal_low} /> to <CountNum value={calories.kcal_high} /></b><span>kcal, likely range</span></div>
          </div>
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

function Saved({ onUndo, label }) {
  return (
    <p className="fb-note" role="status">
      {label} <button className="link-btn" onClick={onUndo}>Change answer</button>
    </p>
  );
}

function OutOfScope({ result, override, loading, onReset, fb }) {
  const best = result.top[0];
  const near = result.reason === "low_confidence";
  const none = override?.kind === "none";
  return (
    <section key="oos" className={`result unsure${loading ? " busy" : ""}`} aria-live="polite">
      <span className="tag-unsure">Out of scope</span>
      <h2 className="dish">Not one of our dishes</h2>
      <p className="tip">
        This doesn't look like one of the dishes we support.
        {near && ` The closest match was ${best.display_name} at ${Math.round(best.confidence * 100)}%, which isn't sure enough to answer.`}
      </p>
      <hr className="rule" />
      {none ? (
        <Saved label="Thanks, noted that this isn't one of our dishes." onUndo={fb.onUndo} />
      ) : (
        <>
          <p className="eyebrow">Dishes we support. Is yours one of them? Pick it.</p>
          <DishPicker top={result.top} busy={fb.status === "saving"} onPick={fb.onSubmit} />
          {fb.status === "saving" && <p className="fb-note" role="status">Saving…</p>}
          {fb.status === "error" && <p className="fb-error" role="alert">Couldn't save your answer. Try again.</p>}
        </>
      )}
      <div className="actions left">
        <button className="btn primary" onClick={onReset}>Try another</button>
      </div>
      <p className="fine">Estimates only, not medical or dietary advice.</p>
    </section>
  );
}

function Corrected({ result, override, loading, portion, onPortion, fb }) {
  const best = result.top[0];
  const was = result.in_scope
    ? `The model guessed ${best.display_name} at ${Math.round(best.confidence * 100)}%.`
    : "The model wasn't sure about this photo.";
  return (
    <section key="corrected" className={`result${loading ? " busy" : ""}`} aria-live="polite">
      <p className="eyebrow">You told us it's</p>
      <h2 className="dish"><DishName name={override.display_name} /></h2>
      <p className="tip">{was}</p>
      <Calories calories={override.calories} portion={portion} onPortion={onPortion} />
      <hr className="rule" />
      <Saved label="Thanks, saved your answer." onUndo={fb.onUndo} />
      <p className="fine">Estimates only, not medical or dietary advice. Calories depend on the recipe and portion.</p>
    </section>
  );
}

export default function ResultCard({ result, override, loading, portion, onPortion, onReset, fb }) {
  if (!result) {
    return (
      <section key="empty" className="result empty" aria-live="polite">
        {loading ? (
          <div className="skeleton" aria-label="Reading your photo">
            <i className="sk sk-tag" /><i className="sk sk-title" /><i className="sk sk-line" />
            <i className="sk sk-tiles" /><i className="sk sk-line short" /><i className="sk sk-line" />
          </div>
        ) : (
          <>
            <h2>Your result appears here</h2>
            <p>We name the dish, say how sure we are, and estimate the calories for a serving.</p>
          </>
        )}
      </section>
    );
  }
  if (override?.kind === "dish") {
    return <Corrected result={result} override={override} loading={loading} portion={portion} onPortion={onPortion} fb={fb} />;
  }
  if (!result.in_scope || override?.kind === "none") {
    return <OutOfScope result={result} override={override} loading={loading} onReset={onReset} fb={fb} />;
  }
  const best = result.top[0];
  const pct = Math.round(best.confidence * 100);
  return (
    <section key="ok" className={`result${loading ? " busy" : ""}`} aria-live="polite">
      <p className="eyebrow">This looks like</p>
      <h2 className="dish"><DishName name={best.display_name} /></h2>
      <div className="sure"><span>{pct}% sure</span><span className="meter"><i style={{ "--w": `${pct}%` }} /></span></div>
      <Calories calories={result.calories} portion={portion} onPortion={onPortion} />
      <hr className="rule" />
      <p className="eyebrow">Top guesses</p>
      <Guesses top={result.top} />
      <hr className="rule" />
      <Feedback result={result} status={fb.status} onSubmit={fb.onSubmit} />
      <p className="fine">Estimates only, not medical or dietary advice. Calories depend on the recipe and portion.</p>
    </section>
  );
}

import { DISH_LIST } from "../dishes.js";

// Lets the user choose the right dish: the model's other guesses first, then all 14.
export default function DishPicker({ top = [], exclude, onPick, onNone, busy }) {
  const guesses = top.filter((g) => g.dish !== exclude);
  const rest = DISH_LIST.filter((d) => d.key !== exclude && !guesses.some((g) => g.dish === d.key));
  return (
    <div className="picker">
      {guesses.length > 0 && (
        <>
          <p className="pick-label">{exclude ? "Our other guesses" : "Our best guesses"}</p>
          <div className="pick-row">
            {guesses.map((g) => (
              <button key={g.dish} className="pick-btn guess" disabled={busy} onClick={() => onPick(g.dish)}>
                {g.display_name} <small>{Math.round(g.confidence * 100)}%</small>
              </button>
            ))}
          </div>
        </>
      )}
      <p className="pick-label">{guesses.length > 0 ? "Or choose from all dishes" : "Choose the dish"}</p>
      <div className="pick-row">
        {rest.map((d) => (
          <button key={d.key} className="pick-btn" disabled={busy} onClick={() => onPick(d.key)}>{d.name}</button>
        ))}
      </div>
      {onNone && (
        <button className="pick-btn none" disabled={busy} onClick={onNone}>None of these, it isn't one of the 14</button>
      )}
    </div>
  );
}

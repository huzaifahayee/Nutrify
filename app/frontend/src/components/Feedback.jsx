import { useState } from "react";
import DishPicker from "./DishPicker.jsx";

// "Is this correct?" under an in-scope result. Yes confirms; No opens the dish picker.
export default function Feedback({ result, status, onSubmit }) {
  const [picking, setPicking] = useState(false);
  const best = result.top[0];
  const busy = status === "saving";

  if (status === "confirmed") {
    return <p className="fb-note" role="status">Thanks, noted. That helps us check the model.</p>;
  }
  return (
    <div className="fb">
      {!picking ? (
        <>
          <p className="fb-q">Is this correct?</p>
          <div className="fb-actions">
            <button className="btn quiet" disabled={busy} onClick={() => onSubmit(best.dish)}>Yes</button>
            <button className="btn quiet" disabled={busy} onClick={() => setPicking(true)}>No</button>
          </div>
        </>
      ) : (
        <>
          <p className="fb-q">What is it?</p>
          <DishPicker
            top={result.top}
            exclude={best.dish}
            busy={busy}
            onPick={onSubmit}
            onNone={() => onSubmit("none")}
          />
          <button className="link-btn" onClick={() => setPicking(false)}>Cancel</button>
        </>
      )}
      {status === "saving" && <p className="fb-note" role="status">Saving…</p>}
      {status === "error" && <p className="fb-error" role="alert">Couldn't save your answer. Try again.</p>}
    </div>
  );
}

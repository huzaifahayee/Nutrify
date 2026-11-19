import { DISHES, STATS } from "../dishes.js";
import Reveal from "./Reveal.jsx";

export function HowItWorks() {
  const steps = [
    ["01", "Snap", "Take a photo or upload one. A single dish in good light works best."],
    ["02", "Match", "An EfficientNet-B0 network trained on desi food photos scores all 14 dishes."],
    ["03", "Estimate", "If it is sure enough, you get a calorie range for your portion. If not, it says so."],
  ];
  return (
    <section className="band" id="how">
      <div className="wrap">
        <Reveal><p className="eyebrow">How it works</p>
        <h2 className="h2">From photo to <em>estimate</em> in three steps.</h2></Reveal>
        <ol className="steps">
          {steps.map(([n, t, d], i) => (
            <Reveal as="li" key={n} delay={i * 140}><span className="step-n">{n}</span><h3>{t}</h3><p>{d}</p></Reveal>
          ))}
        </ol>
        <Reveal as="p" className="note" delay={200}>
          Nutrify knows {STATS.dishes} dishes. A photo of anything else will get a low-confidence
          answer, and the app will say it is not sure instead of forcing a guess.
        </Reveal>
      </div>
    </section>
  );
}

export function DishMenu() {
  return (
    <section className="wrap" id="dishes">
      <Reveal><p className="eyebrow">The menu</p>
      <h2 className="h2">The 14 dishes <em>we know.</em></h2></Reveal>
      <ol className="menu">
        {DISHES.map((d, i) => (
          <Reveal as="li" key={d} delay={(i % 7) * 60}>
            <span className="m-n">{String(i + 1).padStart(2, "0")}</span>
            <span className="m-name">{d}</span>
            <span className="g-lead" aria-hidden="true" />
          </Reveal>
        ))}
      </ol>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="foot">
      <div className="wrap foot-in">
        <p className="foot-brand">Nutrify</p>
        <div>
          <p>An AI course project at FAST-NUCES Lahore, by Muhammad Huzaifa and Muhammad Abdullah Rasheed.</p>
          <p>Hero photo by Shreyak Singh on Unsplash.</p>
          <p>Calorie values are estimates, not medical or dietary advice.</p>
        </div>
      </div>
    </footer>
  );
}

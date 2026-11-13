import Jali from "./Jali.jsx";
import PlateArt from "./PlateArt.jsx";
import { STATS } from "../dishes.js";

export default function Hero() {
  return (
    <section className="hero" id="top">
      <Jali className="hero-pattern" />
      <div className="hero-in">
        <div className="hero-copy">
          <p className="eyebrow">Photo-based desi dish recognition</p>
          <h1 className="hero-title">Know what is on your plate.</h1>
          <p className="hero-sub">
            Snap a photo of nihari, biryani, samosa or eleven other dishes. Nutrify names the
            dish, tells you how sure it is, and estimates the calories for your portion.
          </p>
          <div className="actions left">
            <a className="btn primary" href="#try">Try a photo</a>
            <a className="btn" href="#dishes">See the 14 dishes</a>
          </div>
          <dl className="stats">
            <div><dt>Dishes</dt><dd>{STATS.dishes}</dd></div>
            <div><dt>Test accuracy</dt><dd>{STATS.testAccuracy}</dd></div>
            <div><dt>Model</dt><dd>EfficientNet-B0</dd></div>
          </dl>
        </div>
        <div className="hero-art"><PlateArt /></div>
      </div>
    </section>
  );
}

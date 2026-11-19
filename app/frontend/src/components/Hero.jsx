import { useState } from "react";
import { useCountUp, useParallax } from "../hooks.js";
import PlateArt from "./PlateArt.jsx";
import { STATS, SAMPLE } from "../dishes.js";

// Large food photo. Put a photo at app/frontend/public/photos/hero.jpg to replace the illustration.
function HeroPhoto() {
  const [missing, setMissing] = useState(false);
  return (
    <div className="hero-photo">
      {missing ? (
        <PlateArt />
      ) : (
        <img src="/photos/hero.jpg" alt="A plate of freshly cooked curry" onError={() => setMissing(true)} />
      )}
    </div>
  );
}

export default function Hero() {
  const art = useParallax(0.07);
  const kcal = useCountUp(SAMPLE.kcal, { duration: 1400, delay: 900 });
  return (
    <section className="hero" id="top">
      <div className="hero-in">
        <div className="hero-copy">
          <span className="pill">Desi dish recognition</span>
          <h1 className="hero-title">
            <span>Know what is</span>
            <em>on your plate.</em>
          </h1>
          <p className="hero-sub">
            Snap a photo of nihari, biryani, samosa or eleven other dishes. Nutrify names the
            dish, tells you how sure it is, and estimates the calories for your portion.
          </p>
          <div className="actions left">
            <a className="btn primary" href="#try">Try a photo</a>
            <a className="link-arrow" href="#dishes">Explore the menu</a>
          </div>
          <dl className="stats">
            <div><dt>Dishes</dt><dd>{STATS.dishes}</dd></div>
            <div><dt>Test accuracy</dt><dd>{STATS.testAccuracy}</dd></div>
            <div><dt>Model</dt><dd>EfficientNet-B0</dd></div>
          </dl>
        </div>
        <div className="hero-art" ref={art}>
          <HeroPhoto />
          <div className="kcal-tag" aria-label={`Example: ${SAMPLE.dish}, ${SAMPLE.kcal} kilocalories`}>
            <span className="kt-k">Example · {SAMPLE.dish}</span>
            <span className="kt-n">{kcal} kcal</span>
            <span className="kt-s">{SAMPLE.serving}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

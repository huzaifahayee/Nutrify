import { DISHES } from "../dishes.js";

// Slow, endless ribbon of the 14 dish names. Pauses on hover; static for reduced motion.
export default function Marquee() {
  const items = [...DISHES, ...DISHES];
  return (
    <div className="marquee" aria-hidden="true">
      <div className="marquee-track">
        {items.map((d, i) => (
          <span key={i} className="marquee-item">{d}<i /></span>
        ))}
      </div>
    </div>
  );
}

export const PORTIONS = [
  { value: 0.75, label: "Small" },
  { value: 1, label: "Regular" },
  { value: 1.5, label: "Large" },
  { value: 2, label: "Double" },
];

export default function PortionPicker({ value, onChange }) {
  return (
    <div className="portion" role="group" aria-label="Portion size">
      {PORTIONS.map((p) => (
        <button key={p.value} aria-pressed={value === p.value} onClick={() => onChange(p.value)}>
          {p.label}
          <small>{p.value}x</small>
        </button>
      ))}
    </div>
  );
}

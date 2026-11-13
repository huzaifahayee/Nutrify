export default function ThemeToggle({ theme, onToggle }) {
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button className="toggle" onClick={onToggle} aria-label={`Switch to ${next} theme`}>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        {theme === "dark" ? (
          <g fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
            <circle cx="7" cy="7" r="2.6" />
            <path d="M7 1v1.6M7 11.4V13M1 7h1.6M11.4 7H13M2.8 2.8l1.1 1.1M10.1 10.1l1.1 1.1M2.8 11.2l1.1-1.1M10.1 3.9l1.1-1.1" />
          </g>
        ) : (
          <path d="M11.5 8.6A5 5 0 0 1 5.4 2.5a5 5 0 1 0 6.1 6.1z" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
        )}
      </svg>
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}

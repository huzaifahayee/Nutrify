import ThemeToggle from "./ThemeToggle.jsx";
import { useActiveSection, useScrolled } from "../hooks.js";

const SECTIONS = ["try", "how", "dishes"];

export default function NavBar({ theme, onToggle }) {
  const active = useActiveSection(SECTIONS);
  const scrolled = useScrolled();
  const link = (id, label) => (
    <a href={`#${id}`} aria-current={active === id ? "true" : undefined}>{label}</a>
  );
  return (
    <header className={`nav${scrolled ? " scrolled" : ""}`}>
      <div className="nav-in">
        <a className="brand" href="#top">Nutrify</a>
        <nav className="nav-links" aria-label="Sections">
          {link("try", "Try it")}
          {link("how", "How it works")}
          {link("dishes", "The menu")}
        </nav>
        <ThemeToggle theme={theme} onToggle={onToggle} />
      </div>
    </header>
  );
}

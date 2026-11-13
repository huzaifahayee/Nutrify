import ThemeToggle from "./ThemeToggle.jsx";

export default function NavBar({ theme, onToggle }) {
  return (
    <header className="nav">
      <div className="nav-in">
        <a className="brand" href="#top">Nutrify</a>
        <nav className="nav-links" aria-label="Sections">
          <a href="#try">Try it</a>
          <a href="#how">How it works</a>
          <a href="#dishes">Dishes</a>
        </nav>
        <ThemeToggle theme={theme} onToggle={onToggle} />
      </div>
    </header>
  );
}

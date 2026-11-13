import { useCallback, useEffect, useRef, useState } from "react";
import { predict, ApiError } from "./api.js";
import UploadZone from "./components/UploadZone.jsx";
import CameraCapture from "./components/CameraCapture.jsx";
import ResultCard from "./components/ResultCard.jsx";
import History from "./components/History.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";

const MAX_HISTORY = 6;

function initialTheme() {
  try {
    const saved = localStorage.getItem("nutrify-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch { /* storage can be blocked */ }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState(initialTheme);
  const [current, setCurrent] = useState(null); // { id, file, url }
  const [result, setResult] = useState(null);
  const [portion, setPortion] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [camera, setCamera] = useState(false);
  const [history, setHistory] = useState([]);
  const abort = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("nutrify-theme", theme); } catch { /* ignore */ }
  }, [theme]);

  const run = useCallback(async (item, p) => {
    abort.current?.abort();
    const ctl = new AbortController();
    abort.current = ctl;
    setLoading(true);
    setError(null);
    try {
      const res = await predict(item.file, p, ctl.signal);
      setResult(res);
      setHistory((h) => {
        const entry = { id: item.id, url: item.url, file: item.file, result: res, portion: p };
        return [entry, ...h.filter((x) => x.id !== item.id)].slice(0, MAX_HISTORY);
      });
    } catch (err) {
      if (err.name === "AbortError") return;
      setResult(null);
      setError(err instanceof ApiError ? err : new ApiError("server", "Something went wrong."));
    } finally {
      if (abort.current === ctl) setLoading(false);
    }
  }, []);

  const onFile = (file) => {
    const item = { id: crypto.randomUUID(), file, url: URL.createObjectURL(file) };
    setCamera(false);
    setCurrent(item);
    setResult(null);
    setPortion(1);
    run(item, 1);
  };

  const onPortion = (p) => {
    setPortion(p);
    if (current) run(current, p);
  };

  const onSelectHistory = (it) => {
    abort.current?.abort();
    setLoading(false);
    setError(null);
    setCurrent({ id: it.id, file: it.file, url: it.url });
    setResult(it.result);
    setPortion(it.portion);
  };

  const reset = () => {
    abort.current?.abort();
    setCurrent(null);
    setResult(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="shell">
      <header className="top">
        <h1 className="brand">Nutrify<small>Know your plate</small></h1>
        <ThemeToggle theme={theme} onToggle={() => setTheme(theme === "dark" ? "light" : "dark")} />
      </header>

      <main className="board">
        <div>
          <p className="eyebrow">Your photo</p>
          {camera ? (
            <CameraCapture onCapture={onFile} onClose={() => setCamera(false)} />
          ) : current ? (
            <div className="photo">
              <img src={current.url} alt="The photo you uploaded" />
              <div className="photo-bar">
                <button className="btn quiet" onClick={reset}>Try another</button>
                <button className="btn quiet" onClick={() => setCamera(true)}>Use camera</button>
              </div>
            </div>
          ) : (
            <UploadZone onFile={onFile} onCamera={() => setCamera(true)} />
          )}
        </div>

        <div>
          <p className="eyebrow">What we found</p>
          {error && (
            <div className="alert" role="alert">
              <span>
                {error.kind === "network"
                  ? "Can't reach the Nutrify server. Make sure the backend is running, then try again."
                  : error.message}
              </span>
              {current && error.kind !== "bad-image" && (
                <button className="btn quiet" onClick={() => run(current, portion)}>Retry</button>
              )}
            </div>
          )}
          <ResultCard result={result} loading={loading} portion={portion} onPortion={onPortion} />
        </div>
      </main>

      <History items={history} currentId={current?.id} onSelect={onSelectHistory} />
    </div>
  );
}

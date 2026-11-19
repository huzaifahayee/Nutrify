import { useCallback, useEffect, useRef, useState } from "react";
import { predict, getCalories, sendFeedback, ApiError } from "./api.js";
import { DISH_LIST } from "./dishes.js";
import UploadZone from "./components/UploadZone.jsx";
import CameraCapture from "./components/CameraCapture.jsx";
import ResultCard from "./components/ResultCard.jsx";
import History from "./components/History.jsx";
import NavBar from "./components/NavBar.jsx";
import Hero from "./components/Hero.jsx";
import { HowItWorks, DishMenu, Footer } from "./components/Sections.jsx";

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
  const [override, setOverride] = useState(null); // user's correction: { kind: "dish" | "none", ... }
  const [fbStatus, setFbStatus] = useState("idle"); // idle | saving | saved | confirmed | error
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

  // Keep the user's answer with the photo in session history.
  useEffect(() => {
    if (!current) return;
    setHistory((h) => h.map((x) => (x.id === current.id ? { ...x, override, fbStatus } : x)));
  }, [override, fbStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const onFile = (file) => {
    const item = { id: crypto.randomUUID(), file, url: URL.createObjectURL(file) };
    setCamera(false);
    setCurrent(item);
    setResult(null);
    setOverride(null);
    setFbStatus("idle");
    setPortion(1);
    run(item, 1);
  };

  const onPortion = (p) => {
    setPortion(p);
    if (override?.kind === "dish") {
      // The user chose the dish, so only the calories change; no need to run the model again.
      getCalories(override.dish, p)
        .then((cal) => setOverride((o) => (o ? { ...o, calories: cal } : o)))
        .catch(() => {});
    } else if (current && !override) {
      run(current, p);
    }
  };

  // label is one of the 14 dish keys, or "none". Saves it, then shows the corrected answer.
  const submitFeedback = async (label) => {
    if (!current || !result) return;
    setFbStatus("saving");
    const confirms = result.in_scope && label === result.top[0].dish;
    try {
      const [, cal] = await Promise.all([
        sendFeedback(current.file, label),
        confirms || label === "none" ? Promise.resolve(null) : getCalories(label, portion).catch(() => null),
      ]);
      if (confirms) {
        setFbStatus("confirmed");
      } else if (label === "none") {
        setOverride({ kind: "none" });
        setFbStatus("saved");
      } else {
        const name = DISH_LIST.find((d) => d.key === label)?.name ?? label;
        setOverride({ kind: "dish", dish: label, display_name: name, calories: cal });
        setFbStatus("saved");
      }
    } catch {
      setFbStatus("error");
    }
  };

  const undoFeedback = () => {
    setOverride(null);
    setFbStatus("idle");
  };

  const onSelectHistory = (it) => {
    abort.current?.abort();
    setLoading(false);
    setError(null);
    setCurrent({ id: it.id, file: it.file, url: it.url });
    setResult(it.result);
    setPortion(it.portion);
    setOverride(it.override ?? null);
    setFbStatus(it.fbStatus && it.fbStatus !== "saving" ? it.fbStatus : "idle");
  };

  const reset = () => {
    abort.current?.abort();
    setCurrent(null);
    setResult(null);
    setOverride(null);
    setFbStatus("idle");
    setError(null);
    setLoading(false);
  };

  return (
    <>
      <NavBar theme={theme} onToggle={() => setTheme(theme === "dark" ? "light" : "dark")} />
      <Hero />

      <section className="wrap try" id="try">
        <p className="eyebrow">Try it</p>
        <h2 className="h2">Show us a plate.</h2>
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
            <ResultCard
              result={result}
              override={override}
              loading={loading}
              portion={portion}
              onPortion={onPortion}
              onReset={reset}
              fb={{ status: fbStatus, onSubmit: submitFeedback, onUndo: undoFeedback }}
            />
          </div>
        </main>
        <History items={history} currentId={current?.id} onSelect={onSelectHistory} />
      </section>

      <HowItWorks />
      <DishMenu />
      <Footer />
    </>
  );
}

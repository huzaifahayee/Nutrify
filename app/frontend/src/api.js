// Talks to the FastAPI backend. In dev, /api is proxied to port 8000 (vite.config.js).
const BASE = import.meta.env.VITE_API_URL ?? "/api";

export class ApiError extends Error {
  constructor(kind, message) {
    super(message);
    this.kind = kind; // "network" | "bad-image" | "too-large" | "server"
  }
}

export async function predict(file, portion = 1, signal) {
  const body = new FormData();
  body.append("file", file);
  body.append("portion", String(portion));
  let res;
  try {
    res = await fetch(`${BASE}/predict`, { method: "POST", body, signal });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError("network", "Can't reach the Nutrify server.");
  }
  if (res.status === 400) throw new ApiError("bad-image", "That file doesn't look like an image.");
  if (res.status === 413) throw new ApiError("too-large", "That photo is over 10 MB.");
  if (!res.ok) throw new ApiError("server", "Something went wrong on the server.");
  return res.json();
}

export async function getCalories(dish, portion = 1) {
  let res;
  try {
    res = await fetch(`${BASE}/calories?dish=${encodeURIComponent(dish)}&portion=${portion}`);
  } catch {
    throw new ApiError("network", "Can't reach the Nutrify server.");
  }
  if (!res.ok) throw new ApiError("server", "Calorie data is not available.");
  return res.json();
}

// Tell the server what the dish really is (a dish key from the 14, or "none").
export async function sendFeedback(file, correctedLabel) {
  const body = new FormData();
  body.append("file", file);
  body.append("corrected_label", correctedLabel);
  let res;
  try {
    res = await fetch(`${BASE}/feedback`, { method: "POST", body });
  } catch {
    throw new ApiError("network", "Can't reach the Nutrify server.");
  }
  if (!res.ok) throw new ApiError("server", "Couldn't save your answer.");
  return res.json();
}

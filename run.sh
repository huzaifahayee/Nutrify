#!/usr/bin/env bash
# Start the Nutrify app: backend (port 8000) and frontend (port 5173) with one command.
# Usage:  ./run.sh        Stop both with Ctrl+C.
cd "$(dirname "$0")" || exit 1

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

if [ ! -f checkpoints/efficientnet_best.pt ]; then
  echo "Missing checkpoints/efficientnet_best.pt. Download it from the Drive link in README.md." >&2
  exit 1
fi
if [ ! -d app/frontend/node_modules ]; then
  echo "Installing frontend packages (first run only)..."
  (cd app/frontend && npm install) || exit 1
fi

# Stop both servers when this script ends or Ctrl+C is pressed.
trap 'echo; echo "Stopping Nutrify..."; kill 0' INT TERM

"$PY" -m uvicorn app.backend.main:app --port 8000 &
(cd app/frontend && npm run dev -- --host 127.0.0.1) &

# Wait for the model to load (about 20 seconds), then open the browser.
echo "Starting Nutrify, loading the model..."
for _ in $(seq 1 120); do
  if curl -s -m 1 http://127.0.0.1:8000/health 2>/dev/null | grep -q '"status":"ok"'; then
    echo "Ready: http://localhost:5173"
    (xdg-open http://localhost:5173 || open http://localhost:5173) >/dev/null 2>&1 &
    break
  fi
  sleep 1
done
wait

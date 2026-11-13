"""Paths and constants for the Nutrify backend."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = REPO_ROOT / "checkpoints" / "efficientnet_best.pt"
THRESHOLD_PATH = REPO_ROOT / "results" / "confidence_threshold.json"

DEFAULT_THRESHOLD = 0.5  # used until results/confidence_threshold.json exists
TOP_K = 3
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
PORTION_MIN, PORTION_MAX = 0.25, 4.0

# The React dev server (Vite) runs here by default.
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def load_threshold():
    """Confidence threshold chosen on the validation set (Abdullah's script)."""
    try:
        with open(THRESHOLD_PATH) as f:
            return float(json.load(f)["threshold"])
    except (OSError, KeyError, ValueError, TypeError):
        return DEFAULT_THRESHOLD

"""Choose the confidence threshold below which the app says "not sure".

The threshold is chosen on the VALIDATION set and only reported on the TEST set.
Run from the repo root: python src/confidence_analysis.py
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
# make the sibling modules importable whether we run from the repo root or from src/
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))

try:
    from efficientnet_model import build_efficientnet
    from dataset import get_loaders
except ImportError:
    from src.efficientnet_model import build_efficientnet
    from src.dataset import get_loaders

CKPT = ROOT / "checkpoints" / "efficientnet_best.pt"
DATA_DIR = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
THRESHOLDS = [float(round(t, 2)) for t in np.arange(0.30, 0.9001, 0.05)]
MIN_ACCURACY = 0.90   # accuracy wanted on the images the app answers
MIN_COVERAGE = 0.50   # share of images the app must still answer


def val_confidences():
    """Run the model on the validation set; return max probability and correctness."""
    ckpt = torch.load(CKPT, map_location="cpu", weights_only=False)
    model = build_efficientnet(num_classes=14, pretrained=False)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    _, val_loader, _ = get_loaders(data_dir=str(DATA_DIR), batch_size=32, num_workers=0)
    conf, correct = [], []
    with torch.inference_mode():
        for batch in val_loader:
            images, labels = batch[0], batch[1]   # ignore any extra items
            probs = torch.softmax(model(images), dim=1)
            top_prob, top_idx = probs.max(dim=1)
            conf.extend(top_prob.tolist())
            correct.extend((top_idx == labels).tolist())
    return np.array(conf), np.array(correct, dtype=bool)


def table(conf, correct):
    """Coverage and accuracy on the answered images, for every threshold."""
    rows = []
    for t in THRESHOLDS:
        answered = conf >= t
        coverage = answered.mean()
        accuracy = correct[answered].mean() if answered.any() else float("nan")
        rows.append((t, float(coverage), float(accuracy)))
    return rows


def choose(rows):
    """Smallest threshold with accuracy >= 0.90 and coverage >= 0.50.

    If none qualifies: among thresholds that keep coverage >= 0.50, take the one with
    the highest accuracy; if even the lowest threshold has coverage < 0.50, take the
    lowest threshold (answer as many images as possible).
    """
    for t, cov, acc in rows:
        if acc >= MIN_ACCURACY and cov >= MIN_COVERAGE:
            return t, "meets accuracy >= 0.90 with coverage >= 0.50"
    kept = [r for r in rows if r[1] >= MIN_COVERAGE and not np.isnan(r[2])]
    if kept:
        best = max(kept, key=lambda r: r[2])
        return best[0], "no threshold reaches 0.90 accuracy; best accuracy with coverage >= 0.50"
    return rows[0][0], "no threshold keeps coverage >= 0.50; lowest threshold used"


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "coverage", "accuracy"])
        for t, cov, acc in rows:
            w.writerow([t, round(cov, 4), round(acc, 4)])


def test_row(threshold):
    """Apply the chosen threshold to the saved test predictions."""
    with open(RESULTS / "preds_efficientnet_test.csv", newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    prob_cols = [c for c in data[0] if c.startswith("prob_")]
    conf = np.array([max(float(r[c]) for c in prob_cols) for r in data])
    correct = np.array([r["true_label"] == r["pred_label"] for r in data])
    answered = conf >= threshold
    acc = correct[answered].mean() if answered.any() else float("nan")
    return [(threshold, float(answered.mean()), float(acc))]


def main():
    RESULTS.mkdir(exist_ok=True)
    conf, correct = val_confidences()
    rows = table(conf, correct)
    write_csv(RESULTS / "confidence_val.csv", rows)

    threshold, reason = choose(rows)
    with open(RESULTS / "confidence_threshold.json", "w", encoding="utf-8") as f:
        json.dump({"threshold": threshold}, f)

    test = test_row(threshold)
    write_csv(RESULTS / "confidence_test.csv", test)

    print(f"validation images: {len(conf)}, overall accuracy {correct.mean():.4f}")
    for t, cov, acc in rows:
        print(f"  threshold {t:.2f}: coverage {cov:.3f}, accuracy {acc:.3f}")
    print(f"chosen threshold: {threshold} ({reason})")
    t, cov, acc = test[0]
    print(f"test at {t}: coverage {cov:.3f}, accuracy {acc:.3f}")


if __name__ == "__main__":
    main()

# Summary: Runs the EfficientNet-B0 checkpoint on the validation set and records the top probability.
# Summary: Picks the confidence threshold on validation (accuracy >= 0.90, coverage >= 0.50) and saves it.
# Summary: Reports coverage and accuracy at that threshold on the test predictions only.

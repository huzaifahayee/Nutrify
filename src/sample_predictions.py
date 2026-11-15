"""Draw a 3 x 4 grid of test images with true dish, predicted dish and confidence.

8 correct and 4 wrong predictions, picked with random.seed(42).
Run from the repo root: python src/sample_predictions.py
"""
import csv
import random
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window needed
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
PREDS = ROOT / "results" / "preds_efficientnet_test.csv"
OUT = ROOT / "results" / "sample_predictions.png"
REPORT_COPY = ROOT / "report" / "figures" / "sample_predictions.png"
N_CORRECT, N_WRONG = 8, 4


def nice(name):
    """chicken_biryani -> Chicken Biryani"""
    return name.replace("_", " ").title()


def load_rows():
    with open(PREDS, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    prob_cols = [c for c in rows[0] if c.startswith("prob_")]
    for r in rows:
        r["conf"] = max(float(r[c]) for c in prob_cols)
        r["ok"] = r["true_label"] == r["pred_label"]
    return rows


def image_path(rel):
    """The path column is relative to data/processed/."""
    p = DATA_DIR / rel
    return p if p.exists() else ROOT / rel


def main():
    rows = sorted(load_rows(), key=lambda r: r["path"])  # sorted so the seed is repeatable
    right = [r for r in rows if r["ok"]]
    wrong = [r for r in rows if not r["ok"]]

    random.seed(42)
    picked = random.sample(right, N_CORRECT) + random.sample(wrong, N_WRONG)
    random.shuffle(picked)  # mix correct and wrong in the grid

    fig, axes = plt.subplots(3, 4, figsize=(12, 9.5))
    for ax, r in zip(axes.flat, picked):
        ax.imshow(Image.open(image_path(r["path"])).convert("RGB"))
        ax.axis("off")
        colour = "green" if r["ok"] else "red"
        ax.set_title(
            f"True: {nice(r['true_label'])}\nPred: {nice(r['pred_label'])} ({r['conf']:.2f})",
            fontsize=10, color=colour,
        )
    fig.suptitle("EfficientNet-B0 sample test predictions (green = correct, red = wrong)", fontsize=13)
    fig.tight_layout()
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=150)
    plt.close(fig)

    REPORT_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT, REPORT_COPY)
    print(f"saved {OUT} and {REPORT_COPY}")


if __name__ == "__main__":
    main()

# Summary: Reads the EfficientNet-B0 test predictions and picks 8 correct and 4 wrong images (seed 42).
# Summary: Draws them in a 3 x 4 grid titled with true dish, predicted dish and confidence.
# Summary: Saves results/sample_predictions.png and copies it to report/figures/.

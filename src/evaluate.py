"""Evaluate Nutrify models from their saved test predictions.

Reads  results/preds_<model>_test.csv  (written by train.py).
Writes results/metrics_<model>.csv and results/confusion_<model>.png.
Run:  python src\\evaluate.py            (both models)
      python src\\evaluate.py --model baseline
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)
from sklearn.preprocessing import label_binarize

RESULTS = Path(__file__).resolve().parent.parent / "results"
MODELS = ["baseline", "efficientnet"]


def save_confusion(y_true, y_pred, classes, out_path, title):
    """Row-normalised confusion matrix; colour = fraction, number = count."""
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)  # each row sums to 1
    n = len(classes)
    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Predicted dish")
    ax.set_ylabel("True dish")
    ax.set_title(title)
    for i in range(n):
        for j in range(n):
            colour = "white" if norm[i, j] > 0.5 else "black"
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color=colour, fontsize=8)
    fig.colorbar(im, ax=ax, label="Fraction of true class")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def evaluate_model(name):
    pred_file = RESULTS / f"preds_{name}_test.csv"
    if not pred_file.exists():
        print(f"[skip] {name}: {pred_file.name} not found")
        return

    df = pd.read_csv(pred_file)
    # Class order = order of the prob_ columns (same as classes.json)
    prob_cols = [c for c in df.columns if c.startswith("prob_")]
    classes = [c[len("prob_"):] for c in prob_cols]
    y_true = df["true_label"].values
    y_pred = df["pred_label"].values
    probs = df[prob_cols].values
    probs = probs / probs.sum(axis=1, keepdims=True)  # rows sum to exactly 1

    # Accuracy and per-class precision / recall / F1 / support
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, sup = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, zero_division=0)
    mp, mr, mf, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average="macro", zero_division=0)
    wp, wr, wf, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, average="weighted", zero_division=0)

    # One-vs-rest AUC-ROC: each dish against all the others
    y_bin = label_binarize(y_true, classes=classes)
    aucs = [roc_auc_score(y_bin[:, i], probs[:, i]) for i in range(len(classes))]
    macro_auc = roc_auc_score(y_true, probs, multi_class="ovr",
                              average="macro", labels=classes)
    weighted_auc = float(np.average(aucs, weights=sup))

    # Metrics table: one row per class, then the summary rows
    rows = [{"name": c, "precision": prec[i], "recall": rec[i], "f1": f1[i],
             "support": int(sup[i]), "auc_roc": aucs[i]}
            for i, c in enumerate(classes)]
    rows.append({"name": "macro avg", "precision": mp, "recall": mr, "f1": mf,
                 "support": int(sup.sum()), "auc_roc": macro_auc})
    rows.append({"name": "weighted avg", "precision": wp, "recall": wr,
                 "support": int(sup.sum()), "f1": wf, "auc_roc": weighted_auc})
    # accuracy row: the value is stored in the f1 column
    rows.append({"name": "accuracy", "precision": np.nan, "recall": np.nan,
                 "f1": acc, "support": int(sup.sum()), "auc_roc": np.nan})
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / f"metrics_{name}.csv", index=False)

    save_confusion(y_true, y_pred, classes,
                   RESULTS / f"confusion_{name}.png", f"{name}: confusion matrix")

    # Short summary on screen
    print(f"\n=== {name} ({len(df)} test images) ===")
    print(f"accuracy        : {acc:.4f}")
    print(f"macro precision : {mp:.4f}")
    print(f"macro recall    : {mr:.4f}")
    print(f"macro F1        : {mf:.4f}")
    print(f"macro AUC-ROC   : {macro_auc:.4f}")
    worst = sorted(zip(classes, f1), key=lambda t: t[1])[:3]
    print("3 lowest-F1 dishes:", ", ".join(f"{c} ({v:.2f})" for c, v in worst))
    print(f"wrote metrics_{name}.csv and confusion_{name}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS, default=None,
                        help="evaluate one model (default: both)")
    args = parser.parse_args()
    for m in ([args.model] if args.model else MODELS):
        evaluate_model(m)

# Summary:
# 1) Reads each model's saved test predictions and computes accuracy, precision, recall, F1.
# 2) Adds one-vs-rest AUC-ROC from the probabilities and draws a row-normalised confusion matrix.
# 3) Saves metrics_<model>.csv and confusion_<model>.png, and skips a model if its file is missing.
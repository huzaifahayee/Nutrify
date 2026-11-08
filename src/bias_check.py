"""Error analysis and bias check for Nutrify models.

Reads  results/preds_<model>_test.csv  and  data/processed/split.csv.
Writes results/bias_<model>_class.csv, _confusions.csv, _subgroups.csv
and results/failures_<model>.png.
Run:  python src\\bias_check.py
"""
import argparse
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.metrics import f1_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MODELS = ["baseline", "efficientnet"]


def load_joined(name, meta):
    """Predictions + metadata (source, setting, brightness), joined on dish+filename."""
    df = pd.read_csv(RESULTS / f"preds_{name}_test.csv")
    parts = df["path"].str.replace("\\", "/", regex=False).str.split("/")
    df["dish"] = parts.str[-2]       # test/samosa/bing_00012.jpg -> samosa
    df["filename"] = parts.str[-1]   # -> bing_00012.jpg
    df = df.merge(meta, on=["dish", "filename"], how="left")
    unmatched = df["source"].isna().sum()
    print(f"[{name}] rows: {len(df)}, not matched to split.csv: {unmatched}")
    return df


def group_rows(df, group_type, col):
    """Accuracy and macro-F1 for each value of one metadata column."""
    rows = []
    for value, g in df.groupby(col, dropna=False):
        labels = sorted(set(g["true_label"]))
        rows.append({
            "group_type": group_type, "group": str(value), "n_images": len(g),
            "accuracy": (g["true_label"] == g["pred_label"]).mean(),
            "macro_f1": f1_score(g["true_label"], g["pred_label"], labels=labels,
                                 average="macro", zero_division=0)})
    return rows


def failure_grid(df, data_dir, out_path, title):
    """Grid of 8 wrong predictions (random, seed 42)."""
    wrong = df[df["true_label"] != df["pred_label"]]
    pick = wrong.sample(n=min(8, len(wrong)), random_state=42)
    fig, axes = plt.subplots(2, 4, figsize=(14, 8))
    for ax in axes.ravel():
        ax.axis("off")
    for ax, (_, r) in zip(axes.ravel(), pick.iterrows()):
        img = Image.open(data_dir / r["path"]).convert("RGB")
        ax.imshow(img)
        ax.set_title(f"true: {r['true_label']}\npred: {r['pred_label']}", fontsize=9)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def bias_for_model(name, meta, data_dir):
    if not (RESULTS / f"preds_{name}_test.csv").exists():
        print(f"[skip] {name}: predictions file not found")
        return
    df = load_joined(name, meta)

    # 1) Per-dish accuracy (= recall) and F1, worst first
    classes = sorted(df["true_label"].unique())
    _, rec, f1, sup = precision_recall_fscore_support(
        df["true_label"], df["pred_label"], labels=classes, zero_division=0)
    cls = pd.DataFrame({"dish": classes, "n_images": sup, "accuracy": rec, "f1": f1})
    cls = cls.sort_values("accuracy").reset_index(drop=True)
    cls.to_csv(RESULTS / f"bias_{name}_class.csv", index=False)
    print(f"\n=== {name}: 3 worst dishes ===")
    print(cls.head(3).to_string(index=False))

    # 2) Top 10 confused pairs (true -> predicted)
    wrong = df[df["true_label"] != df["pred_label"]]
    pairs = (wrong.groupby(["true_label", "pred_label"]).size()
             .sort_values(ascending=False).head(10).reset_index(name="count"))
    pairs.to_csv(RESULTS / f"bias_{name}_confusions.csv", index=False)
    print(f"--- {name}: top confused pairs ---")
    print(pairs.to_string(index=False))

    # 3) Subgroups: source, setting, (optional) brightness thirds
    df["source_group"] = df["source"].apply(
        lambda s: "bing" if str(s).startswith("bing")
        else ("kaggle" if str(s).startswith("kaggle") else "unmatched"))
    rows = group_rows(df, "source", "source_group")
    rows += group_rows(df, "setting", "setting")
    if "brightness" in df.columns and df["brightness"].notna().any():
        df["brightness_group"] = pd.qcut(df["brightness"], 3,
                                         labels=["dark", "medium", "bright"],
                                         duplicates="drop")
        rows += group_rows(df, "brightness", "brightness_group")
    sub = pd.DataFrame(rows)
    sub.to_csv(RESULTS / f"bias_{name}_subgroups.csv", index=False)
    print(f"--- {name}: subgroups ---")
    print(sub.to_string(index=False))

    # 4) Failure examples
    failure_grid(df, data_dir, RESULTS / f"failures_{name}.png",
                 f"{name}: misclassified test images")
    print(f"wrote bias_{name}_*.csv and failures_{name}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    meta = pd.read_csv(data_dir / "split.csv")
    if "split" in meta.columns:
        meta = meta[meta["split"] == "test"]  # only test images
    keep = [c for c in ["dish", "filename", "source", "setting", "brightness"]
            if c in meta.columns]
    meta = meta[keep].drop_duplicates(subset=["dish", "filename"])

    for m in MODELS:
        bias_for_model(m, meta, data_dir)

# Summary:
# 1) Joins each model's test predictions to split.csv to learn each image's source and setting.
# 2) Finds the weakest dishes, the most confused dish pairs, and accuracy by source/setting/brightness.
# 3) Saves the CSVs and a grid of misclassified images so errors can be explained in the report.
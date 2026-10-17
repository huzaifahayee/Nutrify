"""Phase 2 - Feature strategy: label encoding, resizing, split, normalisation.

Reads  data/clean_metadata.csv
Writes data/processed/{train,val,test}/<dish>/*.jpg (224x224),
       data/processed/split.csv, data/processed/classes.json,
       data/processed/norm_stats.json
"""
import json
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split

from config import CLEAN, CLEAN_META, IMG_SIZE, PROCESSED, SEED, SPLIT


def main():
    df = pd.read_csv(CLEAN_META)

    # Label encoding: dish name -> integer id
    classes = sorted(df["dish"].unique())
    class_to_idx = {c: i for i, c in enumerate(classes)}
    df["label"] = df["dish"].map(class_to_idx)

    # Stratified split so each dish appears in train/val/test proportionally
    train_df, tmp = train_test_split(
        df, test_size=1 - SPLIT[0], stratify=df["label"], random_state=SEED)
    val_df, test_df = train_test_split(
        tmp, test_size=SPLIT[2] / (SPLIT[1] + SPLIT[2]),
        stratify=tmp["label"], random_state=SEED)
    parts = {"train": train_df, "val": val_df, "test": test_df}

    # Resize to 224x224 and write out
    for name, part in parts.items():
        for r in part.itertuples():
            out = PROCESSED / name / r.dish
            out.mkdir(parents=True, exist_ok=True)
            img = Image.open(CLEAN / r.dish / r.filename).convert("RGB")
            img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR).save(
                out / r.filename, "JPEG", quality=95)

    # Pixel scaling to [0,1] + per-channel mean/std from TRAIN set only
    pix_sum = np.zeros(3); pix_sq = np.zeros(3); n = 0
    for r in train_df.itertuples():
        arr = np.asarray(Image.open(PROCESSED / "train" / r.dish / r.filename),
                         dtype=np.float64) / 255.0
        pix_sum += arr.sum(axis=(0, 1))
        pix_sq += (arr ** 2).sum(axis=(0, 1))
        n += arr.shape[0] * arr.shape[1]
    mean = pix_sum / n
    std = np.sqrt(pix_sq / n - mean ** 2)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    json.dump(class_to_idx, open(PROCESSED / "classes.json", "w"), indent=2)
    json.dump({"mean": mean.tolist(), "std": std.tolist(), "scale": "x/255"},
              open(PROCESSED / "norm_stats.json", "w"), indent=2)
    pd.concat([p.assign(split=k) for k, p in parts.items()]).to_csv(
        PROCESSED / "split.csv", index=False)

    print("Classes:", class_to_idx)
    print({k: len(v) for k, v in parts.items()})
    print("mean:", mean.round(4), "std:", std.round(4))


if __name__ == "__main__":
    main()

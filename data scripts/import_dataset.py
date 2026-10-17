"""Phase 2 - Collection: import classes from a downloaded Kaggle/other dataset.

Example:
  python import_dataset.py --src "C:/downloads/indian-food/train" \
      --source-name "kaggle:l33tc0d3r/indian-food-classification" \
      --license "see Kaggle page" \
      --map "biryani=chicken_biryani" --map "samosa=samosa"

--map takes  <folder name in dataset>=<our dish slug>  (repeat it per class).
Images are copied into data/raw/<dish>/ and logged in raw_metadata.csv.
"""
import argparse
import csv
import shutil
from pathlib import Path

from config import DISHES, RAW, RAW_META, META_COLUMNS

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--source-name", required=True)
    ap.add_argument("--license", default="see dataset page")
    ap.add_argument("--map", action="append", required=True)
    args = ap.parse_args()

    mapping = dict(m.split("=", 1) for m in args.map)
    for dish in mapping.values():
        assert dish in DISHES, f"Unknown dish slug: {dish}"

    RAW.mkdir(parents=True, exist_ok=True)
    new_file = not RAW_META.exists()
    tag = args.source_name.split(":")[-1].replace("/", "_")[:20]
    with open(RAW_META, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=META_COLUMNS)
        if new_file:
            w.writeheader()
        for folder, dish in mapping.items():
            src_dir = Path(args.src) / folder
            dst_dir = RAW / dish
            dst_dir.mkdir(parents=True, exist_ok=True)
            n = 0
            for p in src_dir.rglob("*"):
                if p.suffix.lower() in EXTS:
                    new_name = f"{tag}_{n:05d}{p.suffix.lower()}"
                    shutil.copy2(p, dst_dir / new_name)
                    w.writerow({"filename": new_name, "dish": dish,
                                "source": args.source_name, "url": "",
                                "license": args.license, "setting": "unknown"})
                    n += 1
            print(f"{folder} -> {dish}: {n} images")


if __name__ == "__main__":
    main()

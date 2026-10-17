"""Phase 2 - Cleaning: missing values, duplicates, outliers.

Reads  data/raw + data/raw_metadata.csv
Writes data/clean/<dish>/*.jpg, data/clean_metadata.csv, data/cleaning_report.csv
Nothing in raw/ is deleted; clean images are copied.
"""
from collections import Counter
import cv2
import imagehash
import numpy as np
import pandas as pd
from PIL import Image

from config import CLEAN, CLEAN_META, DATA, DISHES, RAW, RAW_META

MIN_SIDE = 150            # px, smaller = outlier
MAX_ASPECT = 3.0          # width/height beyond this = outlier
BLUR_THRESHOLD = 40.0     # Laplacian variance below this = too blurry
PHASH_DIST = 4            # perceptual-hash distance counted as near-duplicate


def main():
    meta = pd.read_csv(RAW_META)
    report = Counter()
    report["rows_in_metadata"] = len(meta)

    # 1. Missing values ------------------------------------------------
    before = len(meta)
    meta = meta.dropna(subset=["filename", "dish"])
    meta["dish"] = meta["dish"].str.strip()
    meta = meta[meta["dish"].isin(DISHES)]
    meta[["source", "url", "license", "setting"]] = (
        meta[["source", "url", "license", "setting"]].fillna("unknown"))
    report["dropped_missing_label"] = before - len(meta)

    # exact duplicate rows (same file logged twice)
    before = len(meta)
    meta = meta.drop_duplicates(subset=["dish", "filename"])
    report["dropped_duplicate_rows"] = before - len(meta)

    kept, seen_md5, seen_hash = [], set(), {}
    for row in meta.itertuples():
        path = RAW / row.dish / row.filename
        # missing file
        if not path.exists():
            report["dropped_file_missing"] += 1
            continue
        # 2. Corrupt / unreadable ------------------------------------
        try:
            with Image.open(path) as im:
                im.verify()
            img = Image.open(path).convert("RGB")
        except Exception:
            report["dropped_corrupt"] += 1
            continue
        w, h = img.size
        # 3. Outliers: size, aspect ratio, blur ----------------------
        if min(w, h) < MIN_SIDE:
            report["dropped_too_small"] += 1
            continue
        if max(w, h) / min(w, h) > MAX_ASPECT:
            report["dropped_bad_aspect"] += 1
            continue
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur < BLUR_THRESHOLD:
            report["dropped_blurry"] += 1
            continue
        # 4. Duplicates: exact (md5) + near (perceptual hash) -------
        import hashlib
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        if md5 in seen_md5:
            report["dropped_exact_duplicate"] += 1
            continue
        seen_md5.add(md5)
        ph = imagehash.phash(img)
        bucket = seen_hash.setdefault(row.dish, [])
        if any(ph - other <= PHASH_DIST for other in bucket):
            report["dropped_near_duplicate"] += 1
            continue
        bucket.append(ph)

        # save cleaned copy (RGB jpg)
        out_dir = CLEAN / row.dish
        out_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{path.stem}.jpg"
        img.save(out_dir / out_name, "JPEG", quality=92)
        kept.append({"filename": out_name, "dish": row.dish,
                     "source": row.source, "url": row.url,
                     "license": row.license, "setting": row.setting,
                     "width": w, "height": h,
                     "brightness": float(gray.mean()),
                     "blur_score": float(blur)})

    clean = pd.DataFrame(kept)
    clean.to_csv(CLEAN_META, index=False)
    report["images_kept"] = len(clean)
    pd.Series(report, name="count").to_csv(DATA / "cleaning_report.csv")

    print(pd.Series(report))
    print("\nImages per dish after cleaning:")
    print(clean["dish"].value_counts())


if __name__ == "__main__":
    main()

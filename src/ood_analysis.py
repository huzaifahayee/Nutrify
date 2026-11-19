"""Build the out-of-scope check used by the app.

The app answers only when the photo looks like one of the 14 dishes. Two gates:
  1. confidence: top softmax probability >= the threshold in results/confidence_threshold.json
  2. similarity: cosine similarity between the photo's feature vector and the nearest
     dish centroid >= a threshold chosen here on the VALIDATION set.

Writes:
  results/ood_reference.npz     the 14 dish centroids (from the training images)
  results/ood_thresholds.json   min_confidence and min_similarity used by the backend
  results/ood_val.csv           how each similarity threshold treats validation images
  results/ood_test.csv          both gates applied once to the test images
  results/ood_probe.csv         only if data/ood_probe/ exists: per-photo result for
                                non-dish photos (selfies, objects, other foods)

Run from the repo root: python src/ood_analysis.py
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.dataset import eval_transforms, load_class_map, make_imagefolder  # noqa: E402
from src.efficientnet_model import build_efficientnet  # noqa: E402

CKPT = ROOT / "checkpoints" / "efficientnet_best.pt"
DATA_DIR = ROOT / "data" / "processed"
PROBE_DIR = ROOT / "data" / "ood_probe"
RESULTS = ROOT / "results"
# Keep this share of correctly classified validation photos. It was 0.95 at first; the
# first probe run (data/ood_probe/) let two non-dish photos through, so it was tightened
# to 0.88. Note: this was tuned on a small probe set (26 photos), so treat it as a choice.
KEEP_CORRECT = 0.88


def load_model():
    ckpt = torch.load(CKPT, map_location="cpu", weights_only=False)
    model = build_efficientnet(num_classes=14, pretrained=False)
    model.load_state_dict(ckpt["state_dict"])
    return model.eval()


def features_and_probs(model, x):
    """Feature vector before the classifier head, and softmax probabilities."""
    f = model.avgpool(model.features(x)).flatten(1)
    return f, torch.softmax(model.classifier(f), dim=1)


def run_split(model, split):
    ds = make_imagefolder(DATA_DIR / split, eval_transforms(), load_class_map())
    feats, probs, labels = [], [], []
    with torch.inference_mode():
        for x, y in DataLoader(ds, batch_size=64, num_workers=0):
            f, p = features_and_probs(model, x)
            feats.append(f)
            probs.append(p)
            labels.append(y)
    return torch.cat(feats).numpy(), torch.cat(probs).numpy(), torch.cat(labels).numpy()


def unit(x):
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def similarity(feats, centroids):
    """Highest cosine similarity between each photo and the 14 dish centroids."""
    return (unit(feats) @ unit(centroids).T).max(axis=1)


def probe_photos(model, centroids, min_conf, min_sim):
    """Score non-dish photos from data/ood_probe/ (optional folder, not in Git)."""
    files = sorted(p for p in PROBE_DIR.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if not files:
        return None
    tf = eval_transforms()
    rows = []
    with torch.inference_mode():
        for p in files:
            img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            f, pr = features_and_probs(model, tf(img).unsqueeze(0))
            conf = float(pr.max())
            sim = float(similarity(f.numpy(), centroids)[0])
            low_conf, far = conf < min_conf, sim < min_sim
            rows.append([p.name, round(conf, 3), round(sim, 3), int(low_conf), int(far), int(low_conf or far)])
    with open(RESULTS / "ood_probe.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["photo", "confidence", "similarity", "rejected_by_confidence", "rejected_by_similarity", "rejected"])
        w.writerows(rows)
    return rows


def main():
    RESULTS.mkdir(exist_ok=True)
    model = load_model()
    min_conf = json.load(open(RESULTS / "confidence_threshold.json"))["threshold"]

    train_f, _, train_y = run_split(model, "train")
    centroids = np.stack([train_f[train_y == k].mean(axis=0) for k in range(14)]).astype(np.float32)
    np.savez(RESULTS / "ood_reference.npz", centroids=centroids)

    val_f, val_p, val_y = run_split(model, "val")
    sim = similarity(val_f, centroids)
    correct = val_p.argmax(axis=1) == val_y
    # Largest threshold that still keeps KEEP_CORRECT of the correct validation photos.
    min_sim = float(np.percentile(sim[correct], 100 * (1 - KEEP_CORRECT)))

    rows = []
    for t in np.round(np.arange(0.30, 0.801, 0.05), 2):
        kept = sim >= t
        rows.append([t, round(float(kept[correct].mean()), 4), round(float(kept[~correct].mean()), 4)])
    with open(RESULTS / "ood_val.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["min_similarity", "correct_kept", "wrong_kept"])
        w.writerows(rows)

    both = (val_p.max(axis=1) >= min_conf) & (sim >= min_sim)
    with open(RESULTS / "ood_thresholds.json", "w", encoding="utf-8") as f:
        json.dump({"min_confidence": min_conf, "min_similarity": round(min_sim, 4)}, f)

    print(f"min_confidence {min_conf}, min_similarity {min_sim:.4f} (keeps {KEEP_CORRECT:.0%} of correct val photos)")
    print(f"validation: both gates answer {both.mean():.3f} of photos, accuracy {correct[both].mean():.3f}")

    test_f, test_p, test_y = run_split(model, "test")
    test_ok = test_p.argmax(axis=1) == test_y
    test_both = (test_p.max(axis=1) >= min_conf) & (similarity(test_f, centroids) >= min_sim)
    with open(RESULTS / "ood_test.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["min_confidence", "min_similarity", "coverage", "accuracy"])
        w.writerow([min_conf, round(min_sim, 4), round(float(test_both.mean()), 4), round(float(test_ok[test_both].mean()), 4)])
    print(f"test: both gates answer {test_both.mean():.3f} of photos, accuracy {test_ok[test_both].mean():.3f}")

    probe = probe_photos(model, centroids, min_conf, min_sim)
    if probe is None:
        print(f"no probe photos found in {PROBE_DIR}; add non-dish photos there and rerun")
    else:
        rejected = sum(r[5] for r in probe)
        print(f"probe photos: {rejected} of {len(probe)} rejected -> results/ood_probe.csv")


if __name__ == "__main__":
    main()

# Summary: Builds the 14 dish centroids from the training images and picks a similarity threshold on validation.
# Summary: Saves the thresholds the app uses to say "out of scope" (confidence gate plus similarity gate).
# Summary: Optionally scores non-dish photos in data/ood_probe/ to show how many the gates reject.

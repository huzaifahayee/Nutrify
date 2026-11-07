"""ImageFolder data loaders for Nutrify train / val / test splits."""
import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# ImageNet stats used when EfficientNet-B0 was pretrained.
# We use these instead of data/processed/norm_stats.json so the
# pretrained weights see the same input scale they were trained on.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Expected sizes from Phase 2. Warn (do not crash) if they differ.
EXPECTED_SIZES = {"train": 2986, "val": 640, "test": 641}

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "processed"
CLASSES_JSON = Path(__file__).resolve().parent / "classes.json"


def load_class_map():
    """Alphabetical dish name -> integer id from src/classes.json."""
    with open(CLASSES_JSON) as f:
        return json.load(f)


def train_transforms():
    """Light augmentation for training. Images are already 224x224 JPEGs."""
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def eval_transforms():
    """No random aug on val/test. Resize is a no-op if images are already 224."""
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def make_imagefolder(split_dir, transform, class_map):
    """Build ImageFolder and check folder order matches classes.json."""
    dataset = datasets.ImageFolder(str(split_dir), transform=transform)
    # ImageFolder sorts class folders alphabetically, which should match our ids.
    assert dataset.class_to_idx == class_map, (
        f"ImageFolder class_to_idx {dataset.class_to_idx} "
        f"does not match classes.json {class_map}"
    )
    return dataset


def get_loaders(data_dir=None, batch_size=32, num_workers=2):
    """Return (train_loader, val_loader, test_loader). Test is not shuffled."""
    data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    class_map = load_class_map()

    train_ds = make_imagefolder(data_dir / "train", train_transforms(), class_map)
    val_ds = make_imagefolder(data_dir / "val", eval_transforms(), class_map)
    test_ds = make_imagefolder(data_dir / "test", eval_transforms(), class_map)

    # pin_memory speeds host->GPU copies; skip it on CPU-only machines.
    pin_memory = torch.cuda.is_available()
    common = dict(batch_size=batch_size, num_workers=num_workers, pin_memory=pin_memory)

    train_loader = DataLoader(train_ds, shuffle=True, **common)
    val_loader = DataLoader(val_ds, shuffle=False, **common)
    test_loader = DataLoader(test_ds, shuffle=False, **common)
    return train_loader, val_loader, test_loader


def main():
    parser = argparse.ArgumentParser(description="Smoke-check Nutrify data loaders")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(DEFAULT_DATA_DIR),
        help="Folder with train/, val/, test/ class subfolders",
    )
    args = parser.parse_args()

    train_loader, val_loader, test_loader = get_loaders(args.data_dir)
    sizes = {
        "train": len(train_loader.dataset),
        "val": len(val_loader.dataset),
        "test": len(test_loader.dataset),
    }
    for name, n in sizes.items():
        print(f"{name}: {n}")
        expected = EXPECTED_SIZES[name]
        if n != expected:
            print(
                f"WARNING: {name} has {n} images, expected {expected}. "
                "Check data/processed/ if this is the real split.",
                file=sys.stderr,
            )

    images, labels = next(iter(train_loader))
    print(f"batch images shape: {tuple(images.shape)}")
    print(f"batch labels shape: {tuple(labels.shape)}")


if __name__ == "__main__":
    main()

# This file loads the train/val/test image folders and applies ImageNet
# normalisation plus light training augmentation. get_loaders() is what
# train.py will call; running this file prints sizes and one batch shape.

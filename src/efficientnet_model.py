"""EfficientNet-B0 transfer-learning helpers for 14 dish classes."""
import argparse

import torch.nn as nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


def build_efficientnet(num_classes=14, dropout=0.3, pretrained=True):
    """Return EfficientNet-B0 with a new Dropout -> Linear classifier head."""
    # IMAGENET1K_V1 matches the ImageNet mean/std used in dataset.py.
    weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
    model = efficientnet_b0(weights=weights)
    in_features = model.classifier[-1].in_features  # 1280 after global pool
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_features, num_classes),
    )
    return model


def freeze_backbone(model):
    """Train only the classifier; freeze every EfficientNet feature block."""
    for param in model.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True


def unfreeze_last_blocks(model, n_blocks):
    """Unfreeze the last n_blocks entries of model.features (keep the head on)."""
    blocks = list(model.features.children())
    for block in blocks[-n_blocks:]:
        for param in block.parameters():
            param.requires_grad = True


def count_params(model):
    """Return (total_params, trainable_params)."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def main():
    parser = argparse.ArgumentParser(description="Print EfficientNet param counts")
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Download ImageNet weights (needs network). Default is random init.",
    )
    args = parser.parse_args()

    model = build_efficientnet(pretrained=args.pretrained)
    freeze_backbone(model)
    total, trainable = count_params(model)
    print(f"after freeze: total={total:,} trainable={trainable:,}")

    unfreeze_last_blocks(model, 3)
    total, trainable = count_params(model)
    print(f"after unfreeze last 3 blocks: total={total:,} trainable={trainable:,}")


if __name__ == "__main__":
    main()

# This file builds EfficientNet-B0 and swaps in a 14-class head.
# freeze_backbone / unfreeze_last_blocks are the two training stages.
# Running the file prints how many weights are trainable in each stage.

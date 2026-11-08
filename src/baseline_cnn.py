"""Baseline CNN for Nutrify: a small network trained from scratch.

Used to compare against the pretrained EfficientNet.
Input : batch of 3 x 224 x 224 images
Output: batch of 14 logits (no softmax; the loss applies it)
"""
import torch
import torch.nn as nn


def conv_block(in_ch, out_ch):
    """Conv(3x3) -> BatchNorm -> ReLU -> MaxPool(2). Halves height and width."""
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


class BaselineCNN(nn.Module):
    # Layer sizes (input 3 x 224 x 224):
    #   block1: Conv 3->32    -> 32 x 224 x 224, MaxPool -> 32 x 112 x 112
    #   block2: Conv 32->64   -> 64 x 112 x 112, MaxPool -> 64 x 56 x 56
    #   block3: Conv 64->128  -> 128 x 56 x 56,  MaxPool -> 128 x 28 x 28
    #   block4: Conv 128->256 -> 256 x 28 x 28,  MaxPool -> 256 x 14 x 14
    #   Global average pool   -> 256 x 1 x 1 -> flatten -> 256
    #   Dropout(0.3)          -> 256
    #   Linear 256 -> 14      -> 14 logits
    def __init__(self, num_classes=14, dropout=0.3):
        super().__init__()
        self.features = nn.Sequential(
            conv_block(3, 32),
            conv_block(32, 64),
            conv_block(64, 128),
            conv_block(128, 256),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)  # global average pooling
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)  # (batch, 256)
        x = self.dropout(x)
        return self.fc(x)  # raw logits, no softmax


if __name__ == "__main__":
    # Quick check: random batch of 2 images
    model = BaselineCNN(num_classes=14)
    x = torch.randn(2, 3, 224, 224)
    out = model(x)
    n_params = sum(p.numel() for p in model.parameters())
    print("Output shape:", list(out.shape))
    print("Trainable parameters:", n_params)

# Summary:
# 1) Four conv blocks (32, 64, 128, 256 channels) learn image features from scratch.
# 2) Global average pooling, dropout and one linear layer turn them into 14 dish scores.
# 3) It returns raw logits, so the training loss applies softmax itself.
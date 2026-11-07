"""Train baseline or EfficientNet, then write history, curves and test preds."""
import argparse
import csv
import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dataset import DEFAULT_DATA_DIR, get_loaders, load_class_map  # noqa: E402
from efficientnet_model import (  # noqa: E402
    build_efficientnet,
    count_params,
    freeze_backbone,
    unfreeze_last_blocks,
)

HISTORY_COLUMNS = [
    "epoch",
    "phase",
    "train_loss",
    "train_acc",
    "val_loss",
    "val_acc",
    "lr",
]


def set_seed(seed):
    """Make a run as repeatable as we reasonably can on CPU/GPU."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Train Nutrify dish classifiers")
    p.add_argument("--model", choices=["efficientnet", "baseline"], required=True)
    p.add_argument("--data-dir", type=str, default=str(DEFAULT_DATA_DIR))
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--dropout", type=float, default=0.3)
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--patience", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", type=str, default=str(REPO_ROOT))
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--head-epochs", type=int, default=5)
    p.add_argument("--finetune-lr", type=float, default=1e-4)
    p.add_argument("--unfreeze-blocks", type=int, default=3)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument(
        "--max-epochs",
        type=int,
        default=None,
        help="Cap total epochs (tune.py uses this so searches stay short)",
    )
    p.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip test-set prediction (tune.py does not need a preds CSV)",
    )
    p.add_argument(
        "--pretrained",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="ImageNet weights for EfficientNet (use --no-pretrained offline)",
    )
    return p.parse_args(argv)


def build_model(args, num_classes):
    if args.model == "efficientnet":
        model = build_efficientnet(
            num_classes=num_classes,
            dropout=args.dropout,
            pretrained=args.pretrained,
        )
        return model
    try:
        from baseline_cnn import BaselineCNN
    except ImportError:
        sys.exit(
            "src/baseline_cnn.py is missing. That file is Abdullah's — "
            "add it before training --model baseline."
        )
    return BaselineCNN(num_classes=num_classes)


def trainable_params(model):
    return [p for p in model.parameters() if p.requires_grad]


def make_optimizer(model, lr, weight_decay):
    return AdamW(trainable_params(model), lr=lr, weight_decay=weight_decay)


def make_scheduler(optimizer, n_epochs):
    # Cosine annealing drops lr smoothly over the phase. It needs no extra
    # val-set rule (unlike ReduceLROnPlateau) and is a common default for
    # transfer learning. T_max is the number of epochs in this phase.
    return CosineAnnealingLR(optimizer, T_max=max(int(n_epochs), 1))


def run_one_epoch(model, loader, criterion, optimizer, device, max_batches, train):
    """One pass over a loader. Returns (avg_loss, accuracy)."""
    if train:
        model.train()
        context = torch.enable_grad()
    else:
        model.eval()
        context = torch.no_grad()

    total_loss = 0.0
    total_correct = 0
    total_n = 0
    with context:
        for b, (images, labels) in enumerate(tqdm(loader, leave=False)):
            if max_batches is not None and b >= max_batches:
                break
            images = images.to(device)
            labels = labels.to(device)
            if train:
                optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            if train:
                loss.backward()
                optimizer.step()
            n = labels.size(0)
            total_loss += loss.item() * n
            total_correct += (logits.argmax(dim=1) == labels).sum().item()
            total_n += n
    if total_n == 0:
        return 0.0, 0.0
    return total_loss / total_n, total_correct / total_n


def save_checkpoint(path, model, args, class_names):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state_dict": model.state_dict(),
        "args": vars(args),
        "classes": class_names,
    }
    torch.save(payload, path)


def init_history_csv(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        csv.DictWriter(f, fieldnames=HISTORY_COLUMNS).writeheader()


def append_history(path, row):
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_COLUMNS)
        writer.writerow(row)


def save_curves(history, out_path, finetune_start_epoch=None):
    """Two plots: loss and accuracy. Dashed line = start of fine-tuning."""
    epochs = [r["epoch"] for r in history]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].plot(epochs, [r["train_loss"] for r in history], label="train")
    axes[0].plot(epochs, [r["val_loss"] for r in history], label="val")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("epoch")
    axes[0].legend()

    axes[1].plot(epochs, [r["train_acc"] for r in history], label="train")
    axes[1].plot(epochs, [r["val_acc"] for r in history], label="val")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("epoch")
    axes[1].legend()

    if finetune_start_epoch is not None:
        for ax in axes:
            ax.axvline(
                finetune_start_epoch,
                linestyle="--",
                color="gray",
                label="fine-tune starts",
            )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def write_test_preds(model, test_loader, device, class_names, data_dir, out_csv):
    """Write path, true_label, pred_label, then prob_<class> columns."""
    model.eval()
    data_dir = Path(data_dir).resolve()
    samples = test_loader.dataset.samples
    rows = []
    idx = 0
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="test", leave=False):
            images = images.to(device)
            probs = torch.softmax(model(images), dim=1).cpu()
            pred_ids = probs.argmax(dim=1)
            for i in range(labels.size(0)):
                abs_path, true_id = samples[idx]
                idx += 1
                rel = Path(abs_path).resolve().relative_to(data_dir).as_posix()
                row = {
                    "path": rel,
                    "true_label": class_names[true_id],
                    "pred_label": class_names[int(pred_ids[i])],
                }
                for c, name in enumerate(class_names):
                    row[f"prob_{name}"] = float(probs[i, c])
                rows.append(row)

    fieldnames = ["path", "true_label", "pred_label"] + [
        f"prob_{name}" for name in class_names
    ]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def fit_phase(
    model,
    train_loader,
    val_loader,
    criterion,
    optimizer,
    scheduler,
    device,
    args,
    phase_name,
    n_epochs,
    epoch_offset,
    history,
    history_csv,
    ckpt_path,
    class_names,
    best_state,
):
    """Train n_epochs. best_state is a dict mutated in place. Returns stop flag."""
    bad_epochs = 0
    for local_epoch in range(1, n_epochs + 1):
        epoch = epoch_offset + local_epoch
        lr_now = optimizer.param_groups[0]["lr"]
        train_loss, train_acc = run_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            args.max_batches,
            train=True,
        )
        val_loss, val_acc = run_one_epoch(
            model,
            val_loader,
            criterion,
            None,
            device,
            args.max_batches,
            train=False,
        )
        scheduler.step()
        row = {
            "epoch": epoch,
            "phase": phase_name,
            "train_loss": f"{train_loss:.6f}",
            "train_acc": f"{train_acc:.6f}",
            "val_loss": f"{val_loss:.6f}",
            "val_acc": f"{val_acc:.6f}",
            "lr": f"{lr_now:.8f}",
        }
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "train_acc": train_acc,
                "val_acc": val_acc,
            }
        )
        append_history(history_csv, row)
        print(
            f"epoch {epoch} [{phase_name}] "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} lr={lr_now:.6f}"
        )

        if val_loss < best_state["val_loss"]:
            best_state["val_loss"] = val_loss
            best_state["val_acc"] = val_acc
            best_state["epoch"] = epoch
            save_checkpoint(ckpt_path, model, args, class_names)
            bad_epochs = 0
            print(f"  saved best checkpoint to {ckpt_path}")
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                print(f"  early stopping at epoch {epoch} (patience={args.patience})")
                return True
    return False


def run(args):
    set_seed(args.seed)
    if args.max_epochs is not None:
        args.epochs = min(args.epochs, args.max_epochs)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    out_dir = Path(args.out_dir)
    results_dir = out_dir / "results"
    ckpt_dir = out_dir / "checkpoints"
    history_csv = results_dir / f"history_{args.model}.csv"
    curves_png = results_dir / f"curves_{args.model}.png"
    preds_csv = results_dir / f"preds_{args.model}_test.csv"
    ckpt_path = ckpt_dir / f"{args.model}_best.pt"

    class_map = load_class_map()
    class_names = [name for name, _ in sorted(class_map.items(), key=lambda kv: kv[1])]
    num_classes = len(class_names)

    train_loader, val_loader, test_loader = get_loaders(
        args.data_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    model = build_model(args, num_classes).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)

    init_history_csv(history_csv)
    history = []
    best_state = {"val_loss": float("inf"), "val_acc": 0.0, "epoch": 0}
    finetune_start = None

    if args.model == "efficientnet":
        freeze_backbone(model)
        total, trainable = count_params(model)
        print(f"head phase params: total={total:,} trainable={trainable:,}")
        n_head = min(args.head_epochs, args.epochs)
        n_ft = args.epochs - n_head
        stopped = False
        if n_head > 0:
            opt = make_optimizer(model, args.lr, args.weight_decay)
            sch = make_scheduler(opt, n_head)
            stopped = fit_phase(
                model,
                train_loader,
                val_loader,
                criterion,
                opt,
                sch,
                device,
                args,
                "head",
                n_head,
                0,
                history,
                history_csv,
                ckpt_path,
                class_names,
                best_state,
            )
        if n_ft > 0 and not stopped:
            if ckpt_path.exists():
                ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
                model.load_state_dict(ckpt["state_dict"])
            unfreeze_last_blocks(model, args.unfreeze_blocks)
            total, trainable = count_params(model)
            print(
                f"finetune phase params: total={total:,} trainable={trainable:,}"
            )
            finetune_start = n_head + 1
            opt = make_optimizer(model, args.finetune_lr, args.weight_decay)
            sch = make_scheduler(opt, n_ft)
            fit_phase(
                model,
                train_loader,
                val_loader,
                criterion,
                opt,
                sch,
                device,
                args,
                "finetune",
                n_ft,
                n_head,
                history,
                history_csv,
                ckpt_path,
                class_names,
                best_state,
            )
    else:
        opt = make_optimizer(model, args.lr, args.weight_decay)
        sch = make_scheduler(opt, args.epochs)
        fit_phase(
            model,
            train_loader,
            val_loader,
            criterion,
            opt,
            sch,
            device,
            args,
            "baseline",
            args.epochs,
            0,
            history,
            history_csv,
            ckpt_path,
            class_names,
            best_state,
        )

    if not ckpt_path.exists():
        save_checkpoint(ckpt_path, model, args, class_names)

    save_curves(history, curves_png, finetune_start_epoch=finetune_start)
    print(f"wrote {history_csv}")
    print(f"wrote {curves_png}")

    if args.skip_test:
        print("skipping test prediction")
    else:
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["state_dict"])
        n_preds = write_test_preds(
            model, test_loader, device, class_names, args.data_dir, preds_csv
        )
        print(f"wrote {preds_csv} ({n_preds} rows)")

    print(f"best val_loss={best_state['val_loss']:.4f} at epoch {best_state['epoch']}")
    return {
        "best_val_loss": best_state["val_loss"],
        "best_val_acc": best_state["val_acc"],
        "epochs_run": len(history),
        "preds_csv": str(preds_csv),
        "history_csv": str(history_csv),
    }


def main():
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()

# This script trains EfficientNet in two phases (frozen head, then last blocks)
# or the baseline CNN in one phase. It stores the best weights, a history CSV,
# loss/accuracy curves, and a test-prediction CSV for Abdullah's evaluate.py.

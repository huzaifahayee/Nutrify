"""One-factor-at-a-time hyperparameter search around a default EfficientNet config."""
import argparse
import csv
import sys
import time
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dataset import DEFAULT_DATA_DIR  # noqa: E402
from train import parse_args as parse_train_args  # noqa: E402
from train import run  # noqa: E402

HPARAM_COLUMNS = [
    "run_id",
    "model",
    "lr",
    "finetune_lr",
    "batch_size",
    "dropout",
    "weight_decay",
    "label_smoothing",
    "best_val_loss",
    "best_val_acc",
    "epochs_run",
    "minutes",
]

# Default matches the Chunk 3 / Colab training defaults.
DEFAULT = {
    "lr": 1e-3,
    "finetune_lr": 1e-4,
    "batch_size": 32,
    "dropout": 0.3,
    "weight_decay": 1e-4,
    "label_smoothing": 0.1,
}

# One changed knob per row. First row is the default itself.
TRIALS = [
    ("default", {}),
    ("lr_3e-4", {"lr": 3e-4}),
    ("lr_1e-4", {"lr": 1e-4}),
    ("batch_16", {"batch_size": 16}),
    ("batch_64", {"batch_size": 64}),
    ("dropout_0.2", {"dropout": 0.2}),
    ("dropout_0.5", {"dropout": 0.5}),
    ("wd_1e-2", {"weight_decay": 1e-2}),
]


def merge_cfg(overrides):
    cfg = dict(DEFAULT)
    cfg.update(overrides)
    return cfg


def cfg_to_train_argv(cfg, args, run_dir):
    """Build the argv list that train.parse_args expects."""
    argv = [
        "--model",
        "efficientnet",
        "--data-dir",
        args.data_dir,
        "--out-dir",
        str(run_dir),
        "--epochs",
        str(args.epochs),
        "--head-epochs",
        str(args.head_epochs),
        "--unfreeze-blocks",
        str(args.unfreeze_blocks),
        "--patience",
        str(args.patience),
        "--seed",
        str(args.seed),
        "--num-workers",
        str(args.num_workers),
        "--lr",
        str(cfg["lr"]),
        "--finetune-lr",
        str(cfg["finetune_lr"]),
        "--batch-size",
        str(cfg["batch_size"]),
        "--dropout",
        str(cfg["dropout"]),
        "--weight-decay",
        str(cfg["weight_decay"]),
        "--label-smoothing",
        str(cfg["label_smoothing"]),
        "--skip-test",
    ]
    if args.max_epochs is not None:
        argv += ["--max-epochs", str(args.max_epochs)]
    if args.max_batches is not None:
        argv += ["--max-batches", str(args.max_batches)]
    if not args.pretrained:
        argv += ["--no-pretrained"]
    return argv


def append_row(csv_path, row):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HPARAM_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def final_train_command(cfg, data_dir):
    """Exact command to train the winner on the full schedule (with test preds)."""
    return (
        "python src/train.py --model efficientnet"
        f" --data-dir '{data_dir}'"
        f" --lr {cfg['lr']}"
        f" --finetune-lr {cfg['finetune_lr']}"
        f" --batch-size {cfg['batch_size']}"
        f" --dropout {cfg['dropout']}"
        f" --weight-decay {cfg['weight_decay']}"
        f" --label-smoothing {cfg['label_smoothing']}"
    )


def parse_tune_args(argv=None):
    p = argparse.ArgumentParser(description="One-factor EfficientNet search")
    p.add_argument("--data-dir", type=str, default=str(DEFAULT_DATA_DIR))
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--max-epochs", type=int, default=8)
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--max-runs", type=int, default=None, help="Smoke-test cap, e.g. 2")
    p.add_argument("--head-epochs", type=int, default=5)
    p.add_argument("--unfreeze-blocks", type=int, default=3)
    p.add_argument("--patience", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--out-dir", type=str, default=str(REPO_ROOT))
    p.add_argument(
        "--pretrained",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return p.parse_args(argv)


def main():
    args = parse_tune_args()
    out_dir = Path(args.out_dir)
    runs_root = out_dir / "runs"
    table_path = out_dir / "results" / "hparam_results.csv"
    trials = TRIALS[: args.max_runs] if args.max_runs is not None else TRIALS
    rows = []

    for run_id, overrides in trials:
        cfg = merge_cfg(overrides)
        run_dir = runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {run_id} cfg={cfg} ===")
        train_args = parse_train_args(cfg_to_train_argv(cfg, args, run_dir))
        t0 = time.time()
        summary = run(train_args)
        minutes = (time.time() - t0) / 60.0
        row = {
            "run_id": run_id,
            "model": "efficientnet",
            "lr": cfg["lr"],
            "finetune_lr": cfg["finetune_lr"],
            "batch_size": cfg["batch_size"],
            "dropout": cfg["dropout"],
            "weight_decay": cfg["weight_decay"],
            "label_smoothing": cfg["label_smoothing"],
            "best_val_loss": f"{summary['best_val_loss']:.6f}",
            "best_val_acc": f"{summary['best_val_acc']:.6f}",
            "epochs_run": summary["epochs_run"],
            "minutes": f"{minutes:.2f}",
        }
        append_row(table_path, row)
        rows.append({**row, "cfg": cfg, "best_val_loss": summary["best_val_loss"]})
        print(f"finished {run_id} in {minutes:.2f} min")

    best = min(rows, key=lambda r: r["best_val_loss"])
    print("\n=== best (lowest val loss) ===")
    print(
        f"{best['run_id']}: val_loss={best['best_val_loss']:.4f} "
        f"val_acc={float(best['best_val_acc']):.4f}"
    )
    print("train this config:")
    print(final_train_command(best["cfg"], args.data_dir))
    print(f"wrote {table_path}")


if __name__ == "__main__":
    main()

# This file tries one hyperparameter at a time around a default EfficientNet setup.
# Each trial writes to its own runs/<run_id>/ folder so checkpoints do not clash.
# At the end it prints the best row and the train.py command for a full retrain.

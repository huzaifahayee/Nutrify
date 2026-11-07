# Nutrify

AI-powered desi dish recognition and calorie estimation from a single photo.

## Team
- Muhammad Huzaifa (24L-3019)
- Muhammad Abdullah Rasheed (24L-3002)

## Problem
Popular nutrition apps are built around Western foods and rarely recognise
South Asian dishes like biryani, nihari, haleem or karahi. Nutrify identifies
the dish from a photo and returns a calorie estimate.

## Planned System
- Image classifier: transfer learning on EfficientNet-B0, compared against a baseline CNN
- Calorie module: dish mapped to a per-serving value from a food composition database, adjustable portion size
- Web app: image upload and camera capture, returns dish name, confidence score and calorie range

## Dishes (14)
chicken biryani, pulao, nihari, haleem, chicken karahi, daal, palak paneer,
aloo gosht, seekh kebab, chicken tikka, samosa, pakora, paratha roll, halwa puri

## Data Sources
- Bing image scraping (`collect_images.py`), with every URL logged in `raw_metadata.csv`
- Kaggle "Indian Food Classification": samosa, pakode (pakora), dal_makhani (daal),
  kaathi_rolls (paratha roll), imported with `import_dataset.py`

## Repository Structure
```
Nutrify/
├── README.md
├── .gitignore
├── requirements.txt          # model training (Phase 3)
├── data scripts/             # Phase 2 code, with its own requirements.txt
├── src/
│   ├── dataset.py
│   ├── efficientnet_model.py
│   ├── train.py
│   ├── tune.py
│   ├── classes.json
│   ├── baseline_cnn.py       (Abdullah, in progress)
│   ├── evaluate.py           (Abdullah, in progress)
│   └── bias_check.py         (Abdullah, in progress)
├── results/                  # CSV logs, curves, test predictions
├── docs/
│   └── COLAB.md              # running on a Colab T4
└── report/
    ├── main.tex
    ├── phase1.tex
    ├── phase2.tex
    ├── phase3.tex
    ├── phase4.tex            (Abdullah, in progress)
    ├── contribution.tex
    └── figures/
```
`checkpoints/`, `runs/` and `data/` are not in Git.

## Data Pipeline
`collect_images.py` / `import_dataset.py` -> `clean_data.py` -> `preprocess.py` -> `eda.py`

Run from inside `data scripts/`:
```bash
python collect_images.py --per-query 80
python import_dataset.py --src <path> --source-name <name> --map "folder=dish"
python clean_data.py
python preprocess.py
python eda.py
```

## Setup
Two requirements files:
- `requirements.txt` (repo root): model training and tuning.
- `data scripts/requirements.txt`: Phase 2 data scripts.

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
# only if you also run the Phase 2 scripts:
pip install -r "data scripts/requirements.txt"
```

## Data
The training code expects `data/processed/` in this layout (written by
`preprocess.py`):
```
data/processed/
├── train/<dish>/*.jpg
├── val/<dish>/*.jpg
├── test/<dish>/*.jpg
├── split.csv
├── classes.json
└── norm_stats.json
```
Images are not in Git. The team shares the processed split as a zip on Drive:
TODO: paste Drive link for processed.zip. Unzip it so that `data/processed/`
exists in the repo root.

## Training and tuning
Run from the repo root. Defaults are in `src/train.py`; `python src/train.py --help` lists all flags.

EfficientNet-B0 final run (winning config from `results/hparam_results.csv`, run `batch_16`):
```bash
python src/train.py --model efficientnet --data-dir data/processed --epochs 20 --head-epochs 5 --lr 1e-3 --finetune-lr 1e-4 --batch-size 16 --dropout 0.3 --weight-decay 1e-4 --label-smoothing 0.1 --num-workers 2
```

Baseline CNN (needs `src/baseline_cnn.py`, Abdullah, in progress):
```bash
python src/train.py --model baseline --data-dir data/processed --epochs 20 --batch-size 32 --lr 1e-3 --weight-decay 1e-4 --label-smoothing 0.1 --num-workers 2
```

Hyperparameter search (8 one-factor-at-a-time runs, appends to `results/hparam_results.csv`):
```bash
python src/tune.py --data-dir data/processed --max-epochs 8 --num-workers 2
```

Evaluation and bias check: added by Abdullah, commands will be listed here once
`src/evaluate.py` and `src/bias_check.py` are merged.

To run on a Colab T4 GPU, follow `docs/COLAB.md`.

## Outputs
| File | Content |
|---|---|
| `results/history_<model>.csv` | per-epoch train/val loss and accuracy, learning rate |
| `results/curves_<model>.png` | loss and accuracy curves |
| `results/preds_<model>_test.csv` | test-set predictions |
| `results/hparam_results.csv` | one row per tuning run |
| `checkpoints/<model>_best.pt` | best weights (not in Git) |

The predictions CSV has the columns `path`, `true_label`, `pred_label`, then one
`prob_<class>` column per dish (14 columns, in the order of `src/classes.json`).

## Model Weights
Weights are not committed.
- EfficientNet-B0: https://drive.google.com/file/d/1x7J9duZSv4HPczMAYuKbfNOB3Q2ELMZE/view?usp=drive_link
- Baseline CNN: TODO: paste Drive link (from Abdullah)

Download the file and place it at `checkpoints/<model>_best.pt`
(for example `checkpoints/efficientnet_best.pt`).

## Results summary
| Model | Best val accuracy | Best val loss | Test accuracy | Test macro-F1 | Test AUC-ROC |
|---|---|---|---|---|---|
| EfficientNet-B0 | 0.8313 | 1.0688 | 0.7988 | TODO | TODO |
| Baseline CNN | TODO | TODO | TODO | TODO | TODO |

Sources: EfficientNet validation numbers from `results/history_efficientnet.csv`
(best accuracy and best loss are the maximum and minimum over the 20 epochs);
test accuracy is 512 of 641 rows with `pred_label` equal to `true_label` in
`results/preds_efficientnet_test.csv`; macro-F1 and AUC-ROC will come from
`src/evaluate.py` (Abdullah, in progress); baseline numbers are TODO until the
baseline run exists.

Tuning winner: `batch_16` (batch size 16, other settings at the default), validation
loss 1.167360 and validation accuracy 0.792188 in the 8-epoch search
(`results/hparam_results.csv`).

## Notes
- Raw images are not stored in this repo (see `.gitignore`).
- Known limitation: scraped images can include watermarks and text overlays.

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
├── run.sh                    # one-command launcher for the app
├── requirements.txt          # model training, evaluation and the app backend
├── data scripts/             # Phase 2 code, with its own requirements.txt
├── app/
│   ├── backend/              # FastAPI: model loading and /predict
│   └── frontend/             # React (Vite) web app
├── feedback/                 # user corrections (created at runtime, not in Git)
├── tests/
│   ├── test_api.py           # backend tests (need the weights file)
│   ├── test_calories.py      # calorie module tests
│   ├── test_ood.py           # out-of-scope gate tests
│   └── test_feedback.py      # feedback and calories endpoint tests
├── src/
│   ├── dataset.py
│   ├── efficientnet_model.py
│   ├── train.py
│   ├── tune.py
│   ├── classes.json
│   ├── baseline_cnn.py
│   ├── evaluate.py
│   ├── bias_check.py
│   ├── confidence_analysis.py
│   ├── ood_analysis.py
│   ├── sample_predictions.py
│   ├── calories.py
│   └── calories.json
├── results/                  # CSV logs, curves, test predictions, metrics, bias check
├── docs/
│   └── COLAB.md              # running on a Colab T4
└── report/
    ├── main.tex
    ├── abstract.tex
    ├── phase1.tex
    ├── phase2.tex
    ├── phase3.tex
    ├── phase4.tex
    ├── phase5_app.tex
    ├── phase5_calories.tex
    ├── contribution.tex
    ├── references.bib
    ├── main.pdf              # final compiled report
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
- `requirements.txt` (repo root): model training and tuning, the app backend and the tests.
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
https://drive.google.com/file/d/1Gyzhh16OMr_QpBggNqiQkYdxqsdeUutr/view?usp=drive_link

Unzip it inside `data/` so that `data/processed/` exists in the repo root.

## Training and tuning
Run from the repo root. Defaults are in `src/train.py`; `python src/train.py --help` lists all flags.

EfficientNet-B0 final run (winning config from `results/hparam_results.csv`, run `batch_16`):
```bash
python src/train.py --model efficientnet --data-dir data/processed --epochs 20 --head-epochs 5 --lr 1e-3 --finetune-lr 1e-4 --batch-size 16 --dropout 0.3 --weight-decay 1e-4 --label-smoothing 0.1 --num-workers 2
```

Baseline CNN:
```bash
python src/train.py --model baseline --data-dir data/processed --epochs 20 --batch-size 32 --lr 1e-3 --weight-decay 1e-4 --label-smoothing 0.1 --num-workers 2
```

Hyperparameter search (8 one-factor-at-a-time runs, appends to `results/hparam_results.csv`):
```bash
python src/tune.py --data-dir data/processed --max-epochs 8 --num-workers 2
```

Evaluation (reads `results/preds_<model>_test.csv`, writes `results/metrics_<model>.csv`
and `results/confusion_<model>.png`; default is both models):
```bash
python src/evaluate.py
python src/evaluate.py --model baseline
```

Error analysis and bias check (reads the predictions and `data/processed/split.csv`,
writes `results/bias_<model>_*.csv` and `results/failures_<model>.png`):
```bash
python src/bias_check.py --data-dir data/processed
```

To run on a Colab T4 GPU, follow `docs/COLAB.md`.

## Outputs
| File | Content |
|---|---|
| `results/history_<model>.csv` | per-epoch train/val loss and accuracy, learning rate |
| `results/curves_<model>.png` | loss and accuracy curves |
| `results/preds_<model>_test.csv` | test-set predictions |
| `results/metrics_<model>.csv` | per-class precision, recall, F1, AUC-ROC and averages |
| `results/confusion_<model>.png` | confusion matrix |
| `results/bias_<model>_class.csv`, `_confusions.csv`, `_subgroups.csv` | error analysis and subgroup accuracy |
| `results/failures_<model>.png` | misclassified test images |
| `results/hparam_results.csv` | one row per tuning run |
| `results/confidence_val.csv` | coverage and accuracy for each confidence threshold, on the validation set |
| `results/confidence_threshold.json` | the chosen threshold (0.45) |
| `results/confidence_test.csv` | coverage and accuracy at that threshold on the test set |
| `results/ood_reference.npz` | the 14 dish centroids used by the out-of-scope check |
| `results/ood_thresholds.json` | confidence and similarity thresholds used by the app |
| `results/ood_test.csv` | coverage and accuracy of both checks together on the test set |
| `results/ood_val.csv` | how each similarity threshold treats validation photos |
| `results/ood_probe.csv` | optional: results for non-dish photos placed in `data/ood_probe/` |
| `results/non_dish_check.csv` | informal check with six non-dish photos |
| `results/sample_predictions.png` | grid of correct and wrong test predictions |
| `checkpoints/<model>_best.pt` | best weights (not in Git) |

The predictions CSV has the columns `path`, `true_label`, `pred_label`, then one
`prob_<class>` column per dish (14 columns, in the order of `src/classes.json`).

## Model Weights
Weights are not committed.
- EfficientNet-B0: https://drive.google.com/file/d/1x7J9duZSv4HPczMAYuKbfNOB3Q2ELMZE/view?usp=drive_link
- Baseline CNN: https://drive.google.com/file/d/1B23ZUqqSsF5Y-Lpx8tz0Y4CvPFsNLnqp/view?usp=drive_link

Download the file and place it at `checkpoints/<model>_best.pt`
(for example `checkpoints/efficientnet_best.pt`).

## Run the app
The web app has a FastAPI backend and a React frontend. You need the weights at
`checkpoints/efficientnet_best.pt` (see Model Weights), the Python packages from
`requirements.txt`, and Node.js 20 or newer with npm.

The quickest way, from the repo root (starts both and opens the browser; stop with Ctrl+C):
```bash
./run.sh
```

Or start them by hand in two terminals. Terminal 1, from the repo root (backend on port 8000):
```bash
uvicorn app.backend.main:app --port 8000
```

Terminal 2 (frontend on port 5173):
```bash
cd app/frontend
npm install
npm run dev
```
Open http://localhost:5173, drop in a photo or use the camera. In dev mode the
frontend forwards `/api/...` to the backend.

Backend endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | status, number of classes, confidence threshold |
| `GET /dishes` | the 14 dish names |
| `GET /calories` | calorie range for a chosen `dish` and `portion`, without running the model |
| `POST /feedback` | form fields `file` and `corrected_label` (one of the 14 dishes or `none`); stores the correction |
| `POST /predict` | form fields `file` (image, up to 10 MB) and optional `portion` (0.25 to 4, default 1); returns the top 3 dishes, `in_scope` (with a `reason` when it is false), and a calorie range |

Corrections: under every result the app asks "Is this correct?". Yes confirms the answer. No
lets the user pick the right dish (the model's other guesses first, then all 14, or "None
of these"), and the calories update to the chosen dish. Photos the app rejected as out of
scope can also be corrected by picking the dish. Each answer is saved by the backend in
`feedback/corrections.jsonl` (one JSON line per answer: id, UTC timestamp, image file,
image hash, predicted label, confidence, top 3, in-scope flag and reason, corrected label,
whether the model was right) with the photo in `feedback/images/`. Photos are re-saved as
JPEG, which drops EXIF data such as location. The folder is not in Git because it holds user
photos. If the same photo appears twice (same `image_sha256`), the latest line is the
final answer. These records can be used to evaluate or retrain the model later.

Example:
```bash
curl -F "file=@photo.jpg" -F "portion=1" http://localhost:8000/predict
```

The app only answers when a photo looks like one of the 14 dishes. Otherwise it shows
"out of scope", lists the supported dishes and hides the calories. Two checks run:
the top probability must be at least 0.45 (`results/confidence_threshold.json`, chosen on
the validation set: accuracy 0.9173 at coverage 0.8313; test accuracy 0.8727 at coverage
0.8456), and the photo's feature vector must be close enough to the nearest dish centroid
(`results/ood_thresholds.json`, chosen on the validation set so that 88% of correctly
classified photos still pass; with both checks the model answers 75.7% of test photos at
88.2% accuracy, see `results/ood_test.csv`). Calorie ranges (low, typical, high per serving) come from
`src/calories.py` and `src/calories.json`.

To redo the threshold analysis and the sample-predictions figure (they need the weights
file and `data/processed/`):
```bash
python src/confidence_analysis.py
python src/ood_analysis.py
python src/sample_predictions.py
```

Tests (the API tests load the weights file):
```bash
pytest tests/ -q
```

## Results summary
| Model | Val accuracy (best-loss epoch) | Best val loss | Test accuracy | Test macro-F1 | Test AUC-ROC |
|---|---|---|---|---|---|
| EfficientNet-B0 | 0.8297 | 1.0688 | 0.7988 | 0.7785 | 0.9706 |
| Baseline CNN | 0.5422 | 1.7605 | 0.5086 | 0.4700 | 0.8915 |

Sources: validation numbers from `results/history_<model>.csv`, taken at the epoch
with the lowest validation loss (epoch 19 for EfficientNet-B0, epoch 20 for the
baseline); test accuracy, macro-F1
and AUC-ROC from the accuracy row and the macro avg row of `results/metrics_<model>.csv`
(AUC-ROC is one-vs-rest).

Tuning winner: `batch_16` (batch size 16, other settings at the default), validation
loss 1.167360 and validation accuracy 0.792188 in the 8-epoch search
(`results/hparam_results.csv`).

## Known limitations
- The classifier knows only 14 dishes. Photos of anything else are rejected as out of scope by two checks (confidence and feature similarity). The checks work on most non-dish photos we tried (29 of 30 in an informal test) but are not guaranteed to catch every one.
- Calorie values are estimates for a standard serving, built from recipes and food composition tables. They are not laboratory measurements, and the portion size is chosen by the user, not detected from the photo.
- Scraped training images can include watermarks and text overlays, and four dishes come from a different source than the other ten, which can bias results.
- Raw images, model weights and user feedback photos are not stored in this repo (see `.gitignore`).

## Credits
- Hero photo on the landing page: Shreyak Singh on Unsplash.
- Calorie sources (details in `src/calories.json`): Indian Food Composition Tables 2017 (ICMR-NIN), McCance and Widdowson's CoFID as used in the Indian Nutrient Databank, and Vijayakumar et al., Current Developments in Nutrition, 2024.
- Datasets: Bing image search results and the Kaggle "Indian Food Classification" dataset; the full list of references is in `report/references.bib`.

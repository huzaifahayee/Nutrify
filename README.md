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
├── data scripts/      # all Phase 2 code
└── report/            # LaTeX report (main.tex, phase1.tex, phase2.tex, figures/)
```

## Data Pipeline
`collect_images.py` / `import_dataset.py` -> `clean_data.py` -> `preprocess.py` -> `eda.py`

## Setup
```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1      Linux/Mac: source venv/bin/activate
pip install -r "data scripts/requirements.txt"
```

## Run (from inside `data scripts/`)
```bash
python collect_images.py --per-query 80
python import_dataset.py --src <path> --source-name <name> --map "folder=dish"
python clean_data.py
python preprocess.py
python eda.py
```

## Notes
- Raw images are not stored in this repo (see `.gitignore`).
- Known limitation: scraped images can include watermarks and text overlays.

"""Shared settings for all Nutrify data scripts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"                 # git-ignored
RAW = DATA / "raw"
CLEAN = DATA / "clean"
PROCESSED = DATA / "processed"
FIGURES = ROOT / "report" / "figures"
RAW_META = DATA / "raw_metadata.csv"
CLEAN_META = DATA / "clean_metadata.csv"

IMG_SIZE = 224                       # EfficientNet-B0 input
SEED = 42
SPLIT = (0.70, 0.15, 0.15)           # train / val / test

# slug -> human readable search name. Edit this to match your final dish list.
DISHES = {
    "chicken_biryani": "chicken biryani",
    "pulao": "pulao rice",
    "nihari": "nihari",
    "haleem": "haleem",
    "chicken_karahi": "chicken karahi",
    "daal": "daal lentil curry",
    "palak_paneer": "palak paneer",
    "aloo_gosht": "aloo gosht",
    "seekh_kebab": "seekh kebab",
    "chicken_tikka": "chicken tikka",
    "samosa": "samosa",
    "pakora": "pakora",
    "paratha_roll": "paratha roll",
    "halwa_puri": "halwa puri",
}

# Query templates: the variety helps the bias analysis (home vs restaurant etc.)
QUERY_TEMPLATES = [
    "{n}",
    "{n} Pakistani",
    "homemade {n}",
    "{n} restaurant plate",
    "{n} close up",
]

META_COLUMNS = ["filename", "dish", "source", "url", "license", "setting"]

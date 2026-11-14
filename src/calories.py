"""Calorie lookup for the 14 Nutrify dishes.

Reads src/calories.json (path is relative to this file, not the working directory)
and returns a calorie range for one standard serving, scaled by a portion factor.
"""
import json
from pathlib import Path

# calories.json sits next to this file
DATA_PATH = Path(__file__).resolve().parent / "calories.json"


def _load():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_calories(dish: str, portion: float = 1.0) -> dict:
    """Return calories for one dish.

    dish: a class name from src/classes.json (for example "nihari").
    portion: multiplier for the standard serving (1.0 = standard serving).
    Raises KeyError for an unknown dish and ValueError if portion <= 0.
    """
    if portion <= 0:
        raise ValueError("portion must be greater than 0")

    data = _load()
    if dish not in data:
        raise KeyError(f"unknown dish: {dish}")

    entry = data[dish]
    return {
        "display_name": entry["display_name"],
        "serving": entry["serving"],
        # portion multiplies the three kcal values, rounded to integers
        "kcal_low": round(entry["kcal_low"] * portion),
        "kcal_typical": round(entry["kcal_typical"] * portion),
        "kcal_high": round(entry["kcal_high"] * portion),
        "sources": entry["sources"],
    }


# Summary: get_calories(dish, portion) reads src/calories.json and returns the
# Summary: serving text, a low/typical/high kcal range scaled by portion, and sources.
# Summary: Unknown dish raises KeyError; portion <= 0 raises ValueError.
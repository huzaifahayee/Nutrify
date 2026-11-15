"""Tests for the calorie module (src/calories.py and src/calories.json)."""
import json
from pathlib import Path

import pytest

from src.calories import get_calories

SRC = Path(__file__).resolve().parent.parent / "src"
CAL = json.load(open(SRC / "calories.json", encoding="utf-8"))
CLASSES = json.load(open(SRC / "classes.json", encoding="utf-8"))
DISHES = sorted(CLASSES)


def test_keys_match_classes():
    assert set(CAL) == set(CLASSES)


@pytest.mark.parametrize("dish", DISHES)
def test_kcal_values_are_ordered_numbers(dish):
    e = CAL[dish]
    low, typ, high = e["kcal_low"], e["kcal_typical"], e["kcal_high"]
    for v in (low, typ, high):
        assert isinstance(v, (int, float)) and v > 0
    assert low <= typ <= high


@pytest.mark.parametrize("dish", DISHES)
def test_has_a_named_source(dish):
    sources = CAL[dish]["sources"]
    assert len(sources) >= 1
    assert all(s["name"].strip() for s in sources)


@pytest.mark.parametrize("dish", DISHES)
def test_portion_scales_typical(dish):
    one = get_calories(dish, 1.0)["kcal_typical"]
    two = get_calories(dish, 2.0)["kcal_typical"]
    assert abs(two - 2 * one) <= 1


def test_unknown_dish_raises_keyerror():
    with pytest.raises(KeyError):
        get_calories("not_a_dish")


def test_zero_portion_raises_valueerror():
    with pytest.raises(ValueError):
        get_calories("nihari", 0)

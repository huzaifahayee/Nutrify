"""Out-of-scope check: decide whether a photo looks like one of the 14 dishes."""
import json
from dataclasses import dataclass

from . import config


@dataclass
class Gates:
    min_confidence: float
    min_similarity: float | None  # None when the similarity gate is not available


def load_gates():
    """Thresholds from results/ood_thresholds.json, falling back to the confidence file."""
    try:
        with open(config.OOD_THRESHOLDS_PATH) as f:
            data = json.load(f)
        return Gates(float(data["min_confidence"]), float(data["min_similarity"]))
    except (OSError, KeyError, ValueError, TypeError):
        return Gates(config.load_threshold(), None)


def check(confidence, similarity, gates):
    """Return None if the photo is in scope, else the reason it was rejected.

    "far_from_dishes": the photo's features are far from every known dish.
    "low_confidence": the model is not sure which of the 14 dishes it is.
    """
    if gates.min_similarity is not None and similarity is not None and similarity < gates.min_similarity:
        return "far_from_dishes"
    if confidence < gates.min_confidence:
        return "low_confidence"
    return None

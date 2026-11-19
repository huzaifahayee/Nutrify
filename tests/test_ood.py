"""Unit tests for the out-of-scope gates (no model or data needed)."""
from app.backend.ood import Gates, check

GATES = Gates(min_confidence=0.45, min_similarity=0.40)


def test_in_scope():
    assert check(0.80, 0.70, GATES) is None


def test_low_confidence():
    assert check(0.30, 0.70, GATES) == "low_confidence"


def test_far_from_dishes_even_when_confident():
    assert check(0.95, 0.20, GATES) == "far_from_dishes"


def test_far_reason_wins_when_both_fail():
    assert check(0.10, 0.10, GATES) == "far_from_dishes"


def test_no_similarity_gate_uses_confidence_only():
    gates = Gates(min_confidence=0.45, min_similarity=None)
    assert check(0.30, None, gates) == "low_confidence"
    assert check(0.60, None, gates) is None


def test_thresholds_are_inclusive():
    assert check(0.45, 0.40, GATES) is None

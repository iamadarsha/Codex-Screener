from __future__ import annotations

from decimal import Decimal

from app.breakouts.scoring import compute_basic_score


def test_zero_volume_ratio_and_zero_distance_scores_zero():
    assert compute_basic_score(0.0, Decimal(100), Decimal(100)) == 0.0


def test_none_volume_ratio_treated_as_zero():
    assert compute_basic_score(None, Decimal(100), Decimal(100)) == 0.0


def test_volume_ratio_clamped_at_three():
    high = compute_basic_score(3.0, Decimal(100), Decimal(100))
    higher = compute_basic_score(10.0, Decimal(100), Decimal(100))
    assert high == higher == 60.0


def test_reference_level_zero_guard_no_division_error():
    score = compute_basic_score(1.0, Decimal(0), Decimal(100))
    assert score == 20.0  # volume component only: 1/3 * 60


def test_distance_component_clamps_at_forty():
    # >=3% distance clamps to the max distance component
    score = compute_basic_score(0.0, Decimal(100), Decimal(110))
    assert score == 40.0


def test_combined_score_within_bounds():
    score = compute_basic_score(1.5, Decimal(100), Decimal(101))
    assert 0.0 <= score <= 100.0

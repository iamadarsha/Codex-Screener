"""Basic breakout scoring.

Explicitly BASIC (volume-ratio + level-distance only) — the full
multi-factor "Breakout DNA" transparent scoring engine and false-breakout
ML/heuristics are Phase 3.4 scope, not this round.
"""

from __future__ import annotations

from decimal import Decimal


def compute_basic_score(
    volume_ratio: float | None,
    reference_level: Decimal,
    trigger_price: Decimal,
) -> float:
    """Return a 0-100 score: 60% volume-ratio component, 40% level-distance."""
    volume_component = min(volume_ratio or 0.0, 3.0) / 3.0 * 60.0

    if reference_level:
        distance_pct = abs(float(trigger_price - reference_level) / float(reference_level)) * 100
    else:
        distance_pct = 0.0
    distance_component = min(distance_pct / 3.0, 1.0) * 40.0

    return round(volume_component + distance_component, 1)

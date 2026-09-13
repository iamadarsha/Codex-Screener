"""Market regime classification.

Pure logic layered on top of already-flowing data: `nse_poller.py` already
polls `MAJOR_INDICES` (NIFTY 50/BANK/IT/PHARMA/AUTO/FMCG, INDIA VIX, NIFTY
MIDCAP 50) into Redis key `market:indices` and separately derives
advance/decline breadth into `market:breadth` every poll cycle. This module
adds zero new data ingestion — it only classifies what's already there.

Explicitly v1/simplified, in the same spirit as
`app.breakouts.scoring.compute_basic_score`: threshold bands on
already-available data, not a historical trend regression — a legitimate,
honestly-scoped starting point rather than a fuller regime model.

Styled after `app.market.failover.FailoverController` (plain dataclass
result, a pure classification function, no hidden state) and
`app.breakouts.types.BreakoutSignal` (expose the raw inputs that drove the
classification, not just the label, for a transparent "why").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MarketRegime(str, Enum):
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    CHOPPY = "choppy"
    HIGH_VOLATILITY = "high_volatility"


# ---------------------------------------------------------------------------
# Thresholds (v1 — deliberately simple named-constant bands, not comments,
# per the plan's request; documented here rather than tuned from history)
# ---------------------------------------------------------------------------

# India VIX is conventionally read as: below ~14 = calm, above ~20 = elevated
# / fearful. We take "elevated" as the regime-defining line. A VIX above this
# threshold overrides trend and breadth entirely — a volatility spike is
# treated as its own regime, not blended into a trend read.
VIX_HIGH_VOLATILITY_THRESHOLD: float = 20.0

# NIFTY 50 `change_pct` magnitude (in percentage points) below which the
# day's move is considered too flat to call a trend, regardless of breadth.
TREND_CHANGE_PCT_THRESHOLD: float = 0.5

# Advance/decline ratio bands. Above this many advancers per decliner, market
# breadth is considered "advance-heavy"; at or below its reciprocal, breadth
# is "decline-heavy". Between the two bands, breadth is roughly balanced.
BREADTH_ADVANCE_HEAVY_RATIO: float = 1.5
BREADTH_DECLINE_HEAVY_RATIO: float = 1.0 / BREADTH_ADVANCE_HEAVY_RATIO  # ~0.667


@dataclass(frozen=True, slots=True)
class RegimeResult:
    """The classification plus the raw component readings that drove it.

    Mirrors the project's established "transparent scoring" convention (see
    `BreakoutSignal`/`compute_basic_score`) — the label alone is never the
    whole story, the inputs behind it are always inspectable alongside it.
    """

    regime: MarketRegime
    vix_level: float | None
    nifty_change_pct: float
    advance_decline_ratio: float
    advances: int
    declines: int
    unchanged: int
    extra: dict[str, Any] = field(default_factory=dict)


def _find_index(indices: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for idx in indices:
        if isinstance(idx, dict) and idx.get("name") == name:
            return idx
    return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_market_regime(
    indices: list[dict[str, Any]] | dict[str, Any],
    breadth: dict[str, Any],
) -> RegimeResult:
    """Classify the current market regime from already-fetched
    `market:indices` (a list of dicts shaped like `IndexData`/`nse_poller.py`'s
    `index_data`) and `market:breadth` (a dict shaped like `MarketBreadth`).

    Pure function — no I/O — so it's fully unit-testable with synthetic
    dicts. Classification precedence:

    1. INDIA VIX above `VIX_HIGH_VOLATILITY_THRESHOLD` -> `HIGH_VOLATILITY`,
       regardless of trend/breadth.
    2. Otherwise, NIFTY 50's `change_pct` sign/magnitude plus the
       advance/decline ratio: strongly positive + advance-heavy breadth ->
       `TRENDING_BULLISH`; strongly negative + decline-heavy ->
       `TRENDING_BEARISH`.
    3. Anything else (flat change_pct, and/or roughly balanced breadth, or
       a trend/breadth mismatch) -> `CHOPPY`.

    Missing or malformed input degrades gracefully rather than raising —
    matching the "return an empty/degraded result, don't crash" convention
    already used throughout `app.breakouts.levels`. Anything defaulted is
    flagged in `RegimeResult.extra` so callers can tell a genuine `CHOPPY`
    read apart from one produced by incomplete data.
    """
    extra: dict[str, Any] = {}

    if isinstance(indices, dict):
        indices_list: list[dict[str, Any]] = [indices]
    elif isinstance(indices, list):
        indices_list = [idx for idx in indices if isinstance(idx, dict)]
    else:
        indices_list = []
        extra["indices_malformed"] = True

    breadth = breadth if isinstance(breadth, dict) else {}
    if not breadth:
        extra["breadth_missing"] = True

    vix_row = _find_index(indices_list, "INDIA VIX")
    vix_level = _safe_float(vix_row.get("last")) if vix_row is not None else None
    if vix_row is None:
        extra["vix_missing"] = True

    nifty_row = _find_index(indices_list, "NIFTY 50")
    nifty_change_pct = _safe_float(nifty_row.get("change_pct")) if nifty_row is not None else None
    if nifty_row is None or nifty_change_pct is None:
        extra["nifty_missing"] = True
        nifty_change_pct = 0.0

    advances = int(breadth.get("advances", 0) or 0)
    declines = int(breadth.get("declines", 0) or 0)
    unchanged = int(breadth.get("unchanged", 0) or 0)

    raw_ratio = breadth.get("advance_decline_ratio")
    advance_decline_ratio = _safe_float(raw_ratio)
    if advance_decline_ratio is None:
        advance_decline_ratio = round(advances / declines, 2) if declines > 0 else float(advances)

    if vix_level is not None and vix_level > VIX_HIGH_VOLATILITY_THRESHOLD:
        regime = MarketRegime.HIGH_VOLATILITY
    elif (
        nifty_change_pct >= TREND_CHANGE_PCT_THRESHOLD
        and advance_decline_ratio >= BREADTH_ADVANCE_HEAVY_RATIO
    ):
        regime = MarketRegime.TRENDING_BULLISH
    elif (
        nifty_change_pct <= -TREND_CHANGE_PCT_THRESHOLD
        and advance_decline_ratio <= BREADTH_DECLINE_HEAVY_RATIO
    ):
        regime = MarketRegime.TRENDING_BEARISH
    else:
        regime = MarketRegime.CHOPPY

    return RegimeResult(
        regime=regime,
        vix_level=vix_level,
        nifty_change_pct=nifty_change_pct,
        advance_decline_ratio=advance_decline_ratio,
        advances=advances,
        declines=declines,
        unchanged=unchanged,
        extra=extra,
    )

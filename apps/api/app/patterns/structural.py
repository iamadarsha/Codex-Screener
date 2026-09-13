"""Structural (multi-bar geometry) pattern detection, built on the pivot
primitive in `pivots.py`.

Every detector here is a pure function over an already-fetched chronological
candle list — no I/O — following the same synthetic-data-testable
convention as `app.breakouts.levels`. Thresholds (slope tolerance,
symmetry/tightness tolerances) are deliberately simple, explicit constants;
they're sane defaults for real geometry checks, not placeholders, but are
not claimed to be tuned/optimal.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.patterns.pivots import DEFAULT_PIVOT_WINDOW, find_pivots, pivot_highs, pivot_lows
from app.patterns.types import Candle, PatternDirection, PatternMatch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot convert {value!r} to Decimal") from exc


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


# Slope magnitude below this fraction of price-per-bar counts as "flat".
_TRIANGLE_FLAT_SLOPE_TOL = Decimal("0.001")
# Height/depth comparability tolerance for double top/bottom and H&S shoulders.
_SYMMETRY_TOL = Decimal("0.03")
# Darvas box: box range as a fraction of its midpoint must stay under this to
# count as a "tight" consolidation.
_DARVAS_MAX_WIDTH_RATIO = Decimal("0.08")


# ---------------------------------------------------------------------------
# Triangles
# ---------------------------------------------------------------------------

def detect_triangle(
    candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW
) -> PatternMatch | None:
    """Fit a converging/flat trendline over the two most recent pivot highs
    and the two most recent pivot lows; classify ascending / descending /
    symmetrical triangle from the resulting slopes."""
    pivots = find_pivots(candles, window)
    highs = pivot_highs(pivots)
    lows = pivot_lows(pivots)
    if len(highs) < 2 or len(lows) < 2:
        return None

    h1, h2 = highs[-2], highs[-1]
    l1, l2 = lows[-2], lows[-1]
    if h2.index == h1.index or l2.index == l1.index:
        return None

    high_slope = (h2.price - h1.price) / Decimal(h2.index - h1.index)
    low_slope = (l2.price - l1.price) / Decimal(l2.index - l1.index)

    avg_price = (h2.price + l2.price) / 2
    if avg_price <= 0:
        return None
    flat_tol = avg_price * _TRIANGLE_FLAT_SLOPE_TOL

    high_flat = abs(high_slope) <= flat_tol
    low_flat = abs(low_slope) <= flat_tol
    lows_rising = low_slope > flat_tol
    highs_falling = high_slope < -flat_tol

    if high_flat and lows_rising:
        name, direction = "ascending_triangle", PatternDirection.BULLISH
    elif low_flat and highs_falling:
        name, direction = "descending_triangle", PatternDirection.BEARISH
    elif highs_falling and lows_rising:
        name, direction = "symmetrical_triangle", PatternDirection.NEUTRAL
    else:
        return None

    older_gap = h1.price - l1.price
    newer_gap = h2.price - l2.price
    if older_gap > 0:
        convergence = _clamp01(float(1 - newer_gap / older_gap))
    else:
        convergence = 0.5

    return PatternMatch(
        name=name,
        confidence=convergence,
        direction=direction,
        support=l2.price,
        resistance=h2.price,
        extra={"high_slope": str(high_slope), "low_slope": str(low_slope)},
    )


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

def detect_flag(
    candles: list[Candle], pole_len: int = 5, flag_len: int = 5
) -> PatternMatch | None:
    """A sharp directional "pole" move followed by a short, tight
    consolidation ("flag") that retraces only a fraction of the pole."""
    if len(candles) < pole_len + flag_len:
        return None

    pole = candles[-(pole_len + flag_len) : -flag_len]
    flag = candles[-flag_len:]

    pole_start_close = _d(pole[0]["close"])
    pole_end_close = _d(pole[-1]["close"])
    pole_move = pole_end_close - pole_start_close
    pole_range = max(_d(c["high"]) for c in pole) - min(_d(c["low"]) for c in pole)
    if pole_range <= 0 or pole_move == 0:
        return None

    # The pole must be a decisive, mostly-one-directional run: its net move
    # should account for most of its own high-low range.
    move_conviction = abs(pole_move) / pole_range
    if move_conviction < Decimal("0.6"):
        return None

    flag_high = max(_d(c["high"]) for c in flag)
    flag_low = min(_d(c["low"]) for c in flag)
    flag_range = flag_high - flag_low

    # Tight consolidation: the flag must retrace only a small fraction of
    # the pole's move.
    if flag_range > abs(pole_move) * Decimal("0.5"):
        return None

    direction = PatternDirection.BULLISH if pole_move > 0 else PatternDirection.BEARISH
    tightness = _clamp01(float(1 - flag_range / (abs(pole_move) * Decimal("0.5"))))

    return PatternMatch(
        name="flag",
        confidence=tightness,
        direction=direction,
        support=flag_low,
        resistance=flag_high,
        extra={"pole_move": str(pole_move)},
    )


# ---------------------------------------------------------------------------
# Double top / double bottom
# ---------------------------------------------------------------------------

def detect_double_top(
    candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW
) -> PatternMatch | None:
    """Two comparable-height pivot highs with a confirmed trough between
    them."""
    pivots = find_pivots(candles, window)
    highs = pivot_highs(pivots)
    if len(highs) < 2:
        return None

    h1, h2 = highs[-2], highs[-1]
    avg = (h1.price + h2.price) / 2
    if avg <= 0:
        return None
    diff_ratio = abs(h1.price - h2.price) / avg
    if diff_ratio > _SYMMETRY_TOL:
        return None

    lows = pivot_lows(pivots)
    between = [p for p in lows if h1.index < p.index < h2.index]
    if not between:
        return None
    trough = min(between, key=lambda p: p.price)
    if trough.price >= avg * Decimal("0.99"):
        return None  # not a meaningful dip between the two tops

    confidence = _clamp01(float(1 - diff_ratio / _SYMMETRY_TOL))
    return PatternMatch(
        name="double_top",
        confidence=confidence,
        direction=PatternDirection.BEARISH,
        support=trough.price,
        resistance=avg,
    )


def detect_double_bottom(
    candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW
) -> PatternMatch | None:
    """Two comparable-depth pivot lows with a confirmed peak between them."""
    pivots = find_pivots(candles, window)
    lows = pivot_lows(pivots)
    if len(lows) < 2:
        return None

    l1, l2 = lows[-2], lows[-1]
    avg = (l1.price + l2.price) / 2
    if avg <= 0:
        return None
    diff_ratio = abs(l1.price - l2.price) / avg
    if diff_ratio > _SYMMETRY_TOL:
        return None

    highs = pivot_highs(pivots)
    between = [p for p in highs if l1.index < p.index < l2.index]
    if not between:
        return None
    peak = max(between, key=lambda p: p.price)
    if peak.price <= avg * Decimal("1.01"):
        return None

    confidence = _clamp01(float(1 - diff_ratio / _SYMMETRY_TOL))
    return PatternMatch(
        name="double_bottom",
        confidence=confidence,
        direction=PatternDirection.BULLISH,
        support=avg,
        resistance=peak.price,
    )


# ---------------------------------------------------------------------------
# Head & shoulders
# ---------------------------------------------------------------------------

def detect_head_and_shoulders(
    candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW
) -> PatternMatch | None:
    """Three-pivot-high shape: left shoulder, head (strictly higher), right
    shoulder — a topping, bearish reversal formation."""
    pivots = find_pivots(candles, window)
    highs = pivot_highs(pivots)
    if len(highs) < 3:
        return None

    left, head, right = highs[-3], highs[-2], highs[-1]
    if not (head.price > left.price and head.price > right.price):
        return None

    avg_shoulder = (left.price + right.price) / 2
    if avg_shoulder <= 0:
        return None
    symmetry_diff = abs(left.price - right.price) / avg_shoulder
    if symmetry_diff > _SYMMETRY_TOL:
        return None

    lows = pivot_lows(pivots)
    neckline_points = [p for p in lows if left.index < p.index < right.index]
    neckline = (
        sum((p.price for p in neckline_points), start=Decimal(0)) / len(neckline_points)
        if neckline_points
        else avg_shoulder
    )

    confidence = _clamp01(float(1 - symmetry_diff / _SYMMETRY_TOL))
    return PatternMatch(
        name="head_and_shoulders",
        confidence=confidence,
        direction=PatternDirection.BEARISH,
        support=neckline,
        resistance=head.price,
    )


def detect_inverse_head_and_shoulders(
    candles: list[Candle], window: int = DEFAULT_PIVOT_WINDOW
) -> PatternMatch | None:
    """Three-pivot-low shape: left shoulder, head (strictly lower), right
    shoulder — a bottoming, bullish reversal formation."""
    pivots = find_pivots(candles, window)
    lows = pivot_lows(pivots)
    if len(lows) < 3:
        return None

    left, head, right = lows[-3], lows[-2], lows[-1]
    if not (head.price < left.price and head.price < right.price):
        return None

    avg_shoulder = (left.price + right.price) / 2
    if avg_shoulder <= 0:
        return None
    symmetry_diff = abs(left.price - right.price) / avg_shoulder
    if symmetry_diff > _SYMMETRY_TOL:
        return None

    highs = pivot_highs(pivots)
    neckline_points = [p for p in highs if left.index < p.index < right.index]
    neckline = (
        sum((p.price for p in neckline_points), start=Decimal(0)) / len(neckline_points)
        if neckline_points
        else avg_shoulder
    )

    confidence = _clamp01(float(1 - symmetry_diff / _SYMMETRY_TOL))
    return PatternMatch(
        name="inverse_head_and_shoulders",
        confidence=confidence,
        direction=PatternDirection.BULLISH,
        support=head.price,
        resistance=neckline,
    )


# ---------------------------------------------------------------------------
# Cup & handle
# ---------------------------------------------------------------------------

def detect_cup_and_handle(
    candles: list[Candle], cup_len: int = 15, handle_len: int = 5
) -> PatternMatch | None:
    """A rounded U-shaped trough (the "cup") with comparable rim heights,
    followed by a short, shallow pullback (the "handle")."""
    if len(candles) < cup_len + handle_len:
        return None

    cup = candles[-(cup_len + handle_len) : -handle_len]
    handle = candles[-handle_len:]

    lows = [_d(c["low"]) for c in cup]
    bottom_price = min(lows)
    bottom_idx = lows.index(bottom_price)

    # The bottom should sit roughly in the middle of the cup (a rounded U),
    # not right at either edge (which would just be a straight-line move).
    relative_pos = bottom_idx / (len(cup) - 1) if len(cup) > 1 else 0.5
    if not (0.25 <= relative_pos <= 0.75):
        return None

    left_rim = _d(cup[0]["high"])
    right_rim = _d(cup[-1]["high"])
    rim_avg = (left_rim + right_rim) / 2
    if rim_avg <= 0:
        return None
    rim_diff_ratio = abs(left_rim - right_rim) / rim_avg
    if rim_diff_ratio > _SYMMETRY_TOL:
        return None

    cup_depth = rim_avg - bottom_price
    if cup_depth <= 0:
        return None

    handle_high = max(_d(c["high"]) for c in handle)
    handle_low = min(_d(c["low"]) for c in handle)
    handle_depth = handle_high - handle_low

    # The handle must be a shallow pullback relative to the cup's depth, and
    # must not break meaningfully above the right rim.
    if handle_depth > cup_depth * Decimal("0.5"):
        return None
    if handle_high > right_rim * Decimal("1.02"):
        return None

    rim_conf = _clamp01(float(1 - rim_diff_ratio / _SYMMETRY_TOL))
    handle_conf = _clamp01(float(1 - handle_depth / (cup_depth * Decimal("0.5"))))
    confidence = _clamp01((rim_conf + handle_conf) / 2)

    return PatternMatch(
        name="cup_and_handle",
        confidence=confidence,
        direction=PatternDirection.BULLISH,
        support=bottom_price,
        resistance=right_rim,
    )


# ---------------------------------------------------------------------------
# Darvas box
# ---------------------------------------------------------------------------

def detect_darvas_box(candles: list[Candle], box_len: int = 10) -> PatternMatch | None:
    """A tight consolidation range (the "box") followed by a confirmed
    breakout close through one of its edges."""
    if len(candles) < box_len + 1:
        return None

    box = candles[-(box_len + 1) : -1]
    breakout_candle = candles[-1]

    box_high = max(_d(c["high"]) for c in box)
    box_low = min(_d(c["low"]) for c in box)
    box_mid = (box_high + box_low) / 2
    if box_mid <= 0:
        return None
    box_width_ratio = (box_high - box_low) / box_mid
    if box_width_ratio > _DARVAS_MAX_WIDTH_RATIO:
        return None  # not a tight enough consolidation to call it a box

    breakout_close = _d(breakout_candle["close"])
    box_range = box_high - box_low
    if breakout_close > box_high:
        direction = PatternDirection.BULLISH
        edge = box_high
    elif breakout_close < box_low:
        direction = PatternDirection.BEARISH
        edge = box_low
    else:
        return None  # still inside the box: no confirmed breakout yet

    breakout_strength = (
        abs(breakout_close - edge) / box_range if box_range > 0 else Decimal("1")
    )
    tightness_conf = _clamp01(float(1 - box_width_ratio / _DARVAS_MAX_WIDTH_RATIO))
    strength_conf = _clamp01(float(breakout_strength))
    confidence = _clamp01((tightness_conf + strength_conf) / 2)

    return PatternMatch(
        name="darvas_box",
        confidence=confidence,
        direction=direction,
        support=box_low,
        resistance=box_high,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_structural_patterns(candles: list[Candle]) -> list[PatternMatch]:
    """Run every structural detector and collect the non-None matches."""
    detectors = (
        detect_triangle,
        detect_flag,
        detect_double_top,
        detect_double_bottom,
        detect_head_and_shoulders,
        detect_inverse_head_and_shoulders,
        detect_cup_and_handle,
        detect_darvas_box,
    )
    matches: list[PatternMatch] = []
    for detector in detectors:
        try:
            result = detector(candles)
        except (KeyError, ValueError):
            continue
        if result is not None:
            matches.append(result)
    return matches

"""Incremental technical indicator computation.

Unlike `app.services.indicator_engine.compute_indicators` (which rebuilds a
full pandas DataFrame and recomputes every indicator from scratch on every
call), this module updates each indicator's running state in O(1) per new
candle, using the same standard recurrences the underlying library
(pandas-ta) uses — EMA/Wilder's-smoothing are SMA-seeded over their first
`length` samples, then updated recursively. Results converge to match
pandas-ta's batch output once past the warm-up window (verified in
apps/api/app/tests/test_incremental_indicators.py); early bars during
warm-up are seed-convention-dependent for *any* incremental implementation
and aren't expected to match exactly.

Field names match the canonical schema already used by
`app.services.yahoo_finance` / `app.services.indicator_engine` /
`app.services.condition_evaluator.INDICATOR_NAMES`, reconciling the minor
drift between those two writers found during the Phase 1 audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _ema_alpha(length: int) -> float:
    return 2.0 / (length + 1)


@dataclass
class EmaState:
    """Exponential moving average, SMA-seeded over the first `length` samples."""

    length: int
    value: float | None = None
    _seed_window: list[float] = field(default_factory=list)

    def update(self, price: float) -> float | None:
        if self.value is None:
            self._seed_window.append(price)
            if len(self._seed_window) < self.length:
                return None
            self.value = sum(self._seed_window) / self.length
            return self.value
        alpha = _ema_alpha(self.length)
        self.value = alpha * price + (1 - alpha) * self.value
        return self.value


@dataclass
class WilderState:
    """Wilder's smoothing (a specific EMA variant, alpha = 1/length) — used
    by RSI's average gain/loss and by ATR's true-range average, both
    SMA-seeded the same way as `EmaState`."""

    length: int
    value: float | None = None
    _seed_window: list[float] = field(default_factory=list)

    def update(self, sample: float) -> float | None:
        if self.value is None:
            self._seed_window.append(sample)
            if len(self._seed_window) < self.length:
                return None
            self.value = sum(self._seed_window) / self.length
            return self.value
        self.value = (self.value * (self.length - 1) + sample) / self.length
        return self.value


@dataclass
class RsiState:
    length: int = 14
    value: float | None = None
    _avg_gain: WilderState = field(init=False)
    _avg_loss: WilderState = field(init=False)
    _prev_close: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._avg_gain = WilderState(self.length)
        self._avg_loss = WilderState(self.length)

    def update(self, close: float) -> float | None:
        if self._prev_close is None:
            self._prev_close = close
            return None
        change = close - self._prev_close
        self._prev_close = close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = self._avg_gain.update(gain)
        avg_loss = self._avg_loss.update(loss)
        if avg_gain is None or avg_loss is None:
            return None
        if avg_loss == 0:
            self.value = 100.0
        else:
            rs = avg_gain / avg_loss
            self.value = 100.0 - (100.0 / (1.0 + rs))
        return self.value


@dataclass
class AtrState:
    length: int = 14
    value: float | None = None
    _wilder: WilderState = field(init=False)
    _prev_close: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._wilder = WilderState(self.length)

    def update(self, high: float, low: float, close: float) -> float | None:
        if self._prev_close is None:
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - self._prev_close),
                abs(low - self._prev_close),
            )
        self._prev_close = close
        self.value = self._wilder.update(tr)
        return self.value


@dataclass
class MacdState:
    fast: int = 12
    slow: int = 26
    signal: int = 9
    macd: float | None = None
    signal_line: float | None = None
    histogram: float | None = None
    _fast_ema: EmaState = field(init=False)
    _slow_ema: EmaState = field(init=False)
    _signal_ema: EmaState = field(init=False)

    def __post_init__(self) -> None:
        self._fast_ema = EmaState(self.fast)
        self._slow_ema = EmaState(self.slow)
        self._signal_ema = EmaState(self.signal)

    def update(self, close: float) -> tuple[float | None, float | None, float | None]:
        fast_val = self._fast_ema.update(close)
        slow_val = self._slow_ema.update(close)
        if fast_val is None or slow_val is None:
            return None, None, None
        self.macd = fast_val - slow_val
        self.signal_line = self._signal_ema.update(self.macd)
        self.histogram = (
            self.macd - self.signal_line if self.signal_line is not None else None
        )
        return self.macd, self.signal_line, self.histogram


@dataclass
class SmaState:
    """Simple moving average over a fixed-size trailing window — an exact
    computation (no seed-dependent warm-up error, unlike EMA/Wilder)."""

    length: int
    value: float | None = None
    _window: list[float] = field(default_factory=list)

    def update(self, sample: float) -> float | None:
        self._window.append(sample)
        if len(self._window) > self.length:
            self._window.pop(0)
        if len(self._window) < self.length:
            self.value = None
            return None
        self.value = sum(self._window) / self.length
        return self.value


@dataclass
class BollingerState:
    """Bollinger Bands — mid = SMA(length), bands = mid +/- std_mult * sample
    std-dev (ddof=1, matching pandas' `.rolling().std()` default)."""

    length: int = 20
    std_mult: float = 2.0
    upper: float | None = None
    mid: float | None = None
    lower: float | None = None
    _window: list[float] = field(default_factory=list)

    def update(self, close: float) -> tuple[float, float, float] | None:
        self._window.append(close)
        if len(self._window) > self.length:
            self._window.pop(0)
        if len(self._window) < self.length:
            return None
        mean = sum(self._window) / self.length
        variance = sum((x - mean) ** 2 for x in self._window) / (self.length - 1)
        std = variance**0.5
        self.mid = mean
        self.upper = mean + self.std_mult * std
        self.lower = mean - self.std_mult * std
        return self.upper, self.mid, self.lower


@dataclass
class VwapState:
    """Session VWAP — call `reset()` at session start (master prompt §23:
    never reuse a one-size-fits-all dataframe VWAP; this resets per session
    rather than accumulating across days)."""

    value: float | None = None
    _cum_tp_vol: float = 0.0
    _cum_vol: float = 0.0

    def reset(self) -> None:
        self._cum_tp_vol = 0.0
        self._cum_vol = 0.0
        self.value = None

    def update(self, high: float, low: float, close: float, volume: float) -> float | None:
        typical = (high + low + close) / 3.0
        self._cum_tp_vol += typical * volume
        self._cum_vol += volume
        if self._cum_vol > 0:
            self.value = self._cum_tp_vol / self._cum_vol
        return self.value


class RvolTracker:
    """Relative volume vs. a time-of-day historical baseline (master prompt
    §8.8/§24 — do not compare current volume against a generic full-day
    average; compare against the historical pace *at the same session time*).

    `baseline_by_bucket` maps a time-of-day bucket key (e.g. "09:45") to the
    historical average cumulative volume observed by that point in past
    sessions. Without a baseline (no history yet for a symbol), RVOL_TOD
    returns `None` rather than a misleading ratio against zero/missing data.
    """

    def __init__(self, baseline_by_bucket: dict[str, float] | None = None) -> None:
        self._baseline = baseline_by_bucket or {}

    def rvol(self, cumulative_volume: float, session_avg_volume: float | None) -> float | None:
        """Today's cumulative volume vs. the session's own historical daily average."""
        if not session_avg_volume:
            return None
        return cumulative_volume / session_avg_volume

    def rvol_tod(self, cumulative_volume: float, bucket_key: str) -> float | None:
        """Today's cumulative volume vs. the historical average by this time of day."""
        baseline = self._baseline.get(bucket_key)
        if not baseline:
            return None
        return cumulative_volume / baseline


@dataclass
class SymbolIndicatorState:
    """Bundles the full incremental indicator state for one symbol+timeframe."""

    ema_9: EmaState = field(default_factory=lambda: EmaState(9))
    ema_21: EmaState = field(default_factory=lambda: EmaState(21))
    sma_20: SmaState = field(default_factory=lambda: SmaState(20))
    sma_50: SmaState = field(default_factory=lambda: SmaState(50))
    sma_200: SmaState = field(default_factory=lambda: SmaState(200))
    sma_20_volume: SmaState = field(default_factory=lambda: SmaState(20))
    rsi_14: RsiState = field(default_factory=lambda: RsiState(14))
    atr_14: AtrState = field(default_factory=lambda: AtrState(14))
    macd: MacdState = field(default_factory=MacdState)
    bollinger: BollingerState = field(default_factory=lambda: BollingerState(20, 2.0))
    session_vwap: VwapState = field(default_factory=VwapState)
    prev_bar: dict[str, float | None] | None = None
    high_52w: float | None = None

    def update(self, candle: dict) -> dict[str, float | None]:
        """Feed one completed candle in; return the canonical indicator field dict."""
        o, h, l, c, v = (
            float(candle["open"]),
            float(candle["high"]),
            float(candle["low"]),
            float(candle["close"]),
            float(candle["volume"]),
        )

        prev = self.prev_bar

        ema9 = self.ema_9.update(c)
        ema21 = self.ema_21.update(c)
        sma20 = self.sma_20.update(c)
        sma50 = self.sma_50.update(c)
        sma200 = self.sma_200.update(c)
        vol_sma20 = self.sma_20_volume.update(v)
        rsi14 = self.rsi_14.update(c)
        atr14 = self.atr_14.update(h, l, c)
        macd, macd_signal, macd_hist = self.macd.update(c)
        bb = self.bollinger.update(c)
        vwap = self.session_vwap.update(h, l, c, v)

        self.high_52w = h if self.high_52w is None else max(self.high_52w, h)

        result: dict[str, float | None] = {
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "ema_9": ema9,
            "ema_21": ema21,
            "sma_20": sma20,
            "sma_50": sma50,
            "sma_200": sma200,
            "sma_20_volume": vol_sma20,
            "rsi_14": rsi14,
            "atr_14": atr14,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_histogram": macd_hist,
            "bollinger_upper": bb[0] if bb else None,
            "bollinger_mid": bb[1] if bb else None,
            "bollinger_lower": bb[2] if bb else None,
            "vwap": vwap,
            "high_52w": self.high_52w,
        }

        if prev is not None:
            result["prev_open"] = prev["open"]
            result["prev_high"] = prev["high"]
            result["prev_low"] = prev["low"]
            result["prev_close"] = prev["close"]
            result["prev_volume"] = prev["volume"]
            result["prev_ema_9"] = prev.get("ema_9")
            result["prev_ema_21"] = prev.get("ema_21")
            result["prev_rsi_14"] = prev.get("rsi_14")
            result["prev_macd"] = prev.get("macd")
            result["prev_macd_signal"] = prev.get("macd_signal")

        self.prev_bar = result
        return result

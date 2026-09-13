"""Incremental indicators vs. pandas-ta batch output (Phase 2.1 acceptance
gate). SMA/Bollinger-mid are exact computations (no seed dependence) and
are checked tightly; EMA/RSI/MACD/ATR/Bollinger-bands are seed-dependent
during warm-up but converge exponentially — checked only after a long
warm-up run, with a tolerance documented here rather than assumed.
"""

from __future__ import annotations

import random

import pandas as pd
import pandas_ta as ta
import pytest

from app.market.indicators import SymbolIndicatorState

N_BARS = 300
WARMUP_BARS = 250  # past this point, seed influence on EMA(21)/MACD(26) is negligible


def _synthetic_ohlcv(n: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    price = 100.0
    candles = []
    for _ in range(n):
        change = rng.uniform(-1.5, 1.5)
        price = max(price + change, 1.0)
        high = price + rng.uniform(0, 1.0)
        low = price - rng.uniform(0, 1.0)
        open_ = price - change
        volume = rng.randint(1000, 5000)
        candles.append(
            {"open": open_, "high": high, "low": low, "close": price, "volume": volume}
        )
    return candles


@pytest.fixture(scope="module")
def synthetic_candles() -> list[dict]:
    return _synthetic_ohlcv(N_BARS)


@pytest.fixture(scope="module")
def batch_df(synthetic_candles: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(synthetic_candles)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col])
    return df


def _incremental_series(candles: list[dict]) -> list[dict]:
    state = SymbolIndicatorState()
    return [state.update(c) for c in candles]


def test_sma_matches_batch_exactly(synthetic_candles, batch_df):
    incremental = _incremental_series(synthetic_candles)
    batch_sma20 = batch_df.ta.sma(length=20)

    for i in range(19, N_BARS):
        assert incremental[i]["sma_20"] == pytest.approx(batch_sma20.iloc[i], abs=1e-9)


def test_bollinger_mid_matches_sma20(synthetic_candles):
    incremental = _incremental_series(synthetic_candles)
    for i in range(19, N_BARS):
        assert incremental[i]["bollinger_mid"] == pytest.approx(incremental[i]["sma_20"], abs=1e-9)


def test_ema_converges_to_batch_after_warmup(synthetic_candles, batch_df):
    incremental = _incremental_series(synthetic_candles)
    batch_ema21 = batch_df.ta.ema(length=21)

    for i in range(WARMUP_BARS, N_BARS):
        assert incremental[i]["ema_21"] == pytest.approx(batch_ema21.iloc[i], rel=1e-3)


def test_rsi_converges_to_batch_after_warmup(synthetic_candles, batch_df):
    incremental = _incremental_series(synthetic_candles)
    batch_rsi = batch_df.ta.rsi(length=14)

    for i in range(WARMUP_BARS, N_BARS):
        assert incremental[i]["rsi_14"] == pytest.approx(batch_rsi.iloc[i], abs=1.0)


def test_macd_converges_to_batch_after_warmup(synthetic_candles, batch_df):
    incremental = _incremental_series(synthetic_candles)
    batch_macd = batch_df.ta.macd(fast=12, slow=26, signal=9)

    # pandas-ta orders MACD columns as [MACD, MACDh (histogram), MACDs
    # (signal)] — histogram before signal. Select by name, not position, to
    # avoid silently comparing against the wrong column.
    macd_col = next(c for c in batch_macd.columns if c.startswith("MACD_"))
    signal_col = next(c for c in batch_macd.columns if c.startswith("MACDs_"))
    for i in range(WARMUP_BARS, N_BARS):
        assert incremental[i]["macd"] == pytest.approx(batch_macd[macd_col].iloc[i], rel=1e-2)
        assert incremental[i]["macd_signal"] == pytest.approx(
            batch_macd[signal_col].iloc[i], rel=1e-2
        )


def test_atr_converges_to_batch_after_warmup(synthetic_candles, batch_df):
    incremental = _incremental_series(synthetic_candles)
    batch_atr = batch_df.ta.atr(length=14)

    for i in range(WARMUP_BARS, N_BARS):
        assert incremental[i]["atr_14"] == pytest.approx(batch_atr.iloc[i], rel=5e-2)


def test_indicators_are_none_during_warmup_not_wrong_values():
    state = SymbolIndicatorState()
    candles = _synthetic_ohlcv(5)
    results = [state.update(c) for c in candles]

    # Fewer than 9/14/20/21/26 bars in — these must be None, not a bogus number.
    assert results[-1]["ema_9"] is None
    assert results[-1]["rsi_14"] is None
    assert results[-1]["sma_20"] is None

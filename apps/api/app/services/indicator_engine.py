"""Technical indicator computation using pandas / pandas-ta."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pandas_ta as ta  # noqa: F401 – registers accessor
import structlog

from app.db.models.ohlcv import Ohlcv1Min, OhlcvDaily
from app.db.session import SessionLocal
from app.services.redis_cache import hset_dict
from app.utils.redis_keys import TTL_INDICATOR, indicator_key
from app.utils.time import IST, now_ist

log = structlog.get_logger(__name__)

# Minimum number of candles required to compute the slowest indicator (SMA-200)
_MIN_CANDLES = 210


def compute_indicators(
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute a full set of technical indicators from OHLCV candle dicts.

    Each candle dict must contain keys: ``open``, ``high``, ``low``,
    ``close``, ``volume``.

    Returns a flat dict of indicator values (latest bar).
    """
    if len(candles) < 2:
        log.warning("not_enough_candles", symbol=symbol, tf=timeframe, n=len(candles))
        return {}

    df = pd.DataFrame(candles)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    result: dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "close": _last(df["close"]),
        "volume": _last(df["volume"]),
    }

    # -- EMAs ---------------------------------------------------------------
    result["ema_9"] = _last(df.ta.ema(length=9))
    result["ema_21"] = _last(df.ta.ema(length=21))

    # -- SMAs ---------------------------------------------------------------
    result["sma_20"] = _last(df.ta.sma(length=20))
    result["sma_50"] = _last(df.ta.sma(length=50))
    result["sma_200"] = _last(df.ta.sma(length=200))

    # -- RSI ----------------------------------------------------------------
    result["rsi_14"] = _last(df.ta.rsi(length=14))

    # -- MACD ---------------------------------------------------------------
    macd_df = df.ta.macd(fast=12, slow=26, signal=9)
    if macd_df is not None and not macd_df.empty:
        result["macd"] = _last(macd_df.iloc[:, 0])
        result["macd_signal"] = _last(macd_df.iloc[:, 1])
        result["macd_histogram"] = _last(macd_df.iloc[:, 2])
    else:
        result["macd"] = None
        result["macd_signal"] = None
        result["macd_histogram"] = None

    # -- Bollinger Bands ----------------------------------------------------
    bbands = df.ta.bbands(length=20, std=2)
    if bbands is not None and not bbands.empty:
        result["bollinger_lower"] = _last(bbands.iloc[:, 0])
        result["bollinger_mid"] = _last(bbands.iloc[:, 1])
        result["bollinger_upper"] = _last(bbands.iloc[:, 2])
    else:
        result["bollinger_lower"] = None
        result["bollinger_mid"] = None
        result["bollinger_upper"] = None

    # -- ATR ----------------------------------------------------------------
    result["atr_14"] = _last(df.ta.atr(length=14))

    # -- VWAP ---------------------------------------------------------------
    result["vwap"] = _compute_vwap(df)

    # -- Volume SMA(20) -- needed by volume_spike scan ----------------------
    vol_sma_20 = _last(df["volume"].rolling(window=20).mean())
    result["sma_20_volume"] = vol_sma_20

    # -- 52-week high -- needed by near_52_week_high scan -------------------
    if len(df) >= 2:
        result["high_52w"] = round(float(df["high"].max()), 4)
        result["open"] = _last(df["open"])
        result["high"] = _last(df["high"])
        result["low"] = _last(df["low"])

    # -- Previous bar values -- needed for crossover scans ------------------
    if len(df) >= 2:
        prev_idx = len(df) - 2
        result["prev_close"] = round(float(df["close"].iloc[prev_idx]), 4)
        result["prev_open"] = round(float(df["open"].iloc[prev_idx]), 4)
        result["prev_high"] = round(float(df["high"].iloc[prev_idx]), 4)
        result["prev_low"] = round(float(df["low"].iloc[prev_idx]), 4)
        result["prev_volume"] = int(df["volume"].iloc[prev_idx])
        # Previous EMA/indicator values for cross detection
        ema9_series = df.ta.ema(length=9)
        ema21_series = df.ta.ema(length=21)
        if ema9_series is not None and len(ema9_series) >= 2:
            prev_ema9 = ema9_series.iloc[-2]
            result["prev_ema_9"] = round(float(prev_ema9), 4) if not pd.isna(prev_ema9) else None
        if ema21_series is not None and len(ema21_series) >= 2:
            prev_ema21 = ema21_series.iloc[-2]
            result["prev_ema_21"] = round(float(prev_ema21), 4) if not pd.isna(prev_ema21) else None
        if macd_df is not None and len(macd_df) >= 2:
            prev_macd = macd_df.iloc[-2, 0]
            prev_signal = macd_df.iloc[-2, 1]
            result["prev_macd"] = round(float(prev_macd), 4) if not pd.isna(prev_macd) else None
            result["prev_macd_signal"] = round(float(prev_signal), 4) if not pd.isna(prev_signal) else None

    result["updated_at"] = now_ist().isoformat()
    return result


async def store_indicators(symbol: str, timeframe: str, indicators: dict[str, Any]) -> None:
    """Write computed indicators to the Redis hash with a TTL."""
    key = indicator_key(symbol, timeframe)
    await hset_dict(key, indicators, ttl=TTL_INDICATOR)
    log.debug("indicators_stored", symbol=symbol, tf=timeframe)


async def refresh_indicators(symbol: str, timeframe: str) -> dict[str, Any]:
    """Fetch recent candles from the database, compute, store, and return indicators."""
    candles = await _fetch_candles(symbol, timeframe)
    if not candles:
        log.warning("no_candles_for_indicators", symbol=symbol, tf=timeframe)
        return {}

    indicators = compute_indicators(symbol, timeframe, candles)
    if indicators:
        await store_indicators(symbol, timeframe, indicators)
    return indicators


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _last(series: pd.Series | None) -> float | None:
    """Return the last non-NaN value of a pandas Series, or None."""
    if series is None or series.empty:
        return None
    val = series.iloc[-1]
    if pd.isna(val):
        return None
    return round(float(val), 4)


def _compute_vwap(df: pd.DataFrame) -> float | None:
    """Compute a simple cumulative VWAP over the provided dataframe."""
    if "volume" not in df.columns or df["volume"].sum() == 0:
        return None
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_tp_vol = (typical * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum()
    vwap_series = cum_tp_vol / cum_vol
    return _last(vwap_series)


async def _fetch_candles(symbol: str, timeframe: str) -> list[dict[str, Any]]:
    """Load recent candles from the database for indicator computation."""
    from sqlalchemy import select

    async with SessionLocal() as session:
        if timeframe in ("1min", "5min", "15min"):
            stmt = (
                select(Ohlcv1Min)
                .where(Ohlcv1Min.symbol == symbol)
                .order_by(Ohlcv1Min.ts.desc())
                .limit(_MIN_CANDLES)
            )
            rows = (await session.execute(stmt)).scalars().all()
        else:
            stmt = (
                select(OhlcvDaily)
                .where(OhlcvDaily.symbol == symbol)
                .order_by(OhlcvDaily.date.desc())
                .limit(_MIN_CANDLES)
            )
            rows = (await session.execute(stmt)).scalars().all()

    # Reverse to chronological order
    rows = list(reversed(rows))
    candles: list[dict[str, Any]] = []
    for r in rows:
        candles.append(
            {
                "open": float(r.open),
                "high": float(r.high),
                "low": float(r.low),
                "close": float(r.close),
                "volume": int(r.volume),
            }
        )
    return candles

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP
from typing import cast
from zoneinfo import ZoneInfo

import pandas as pd
import pandas_ta as ta
import redis.asyncio as redis
from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from app.db.models.ohlcv import OhlcvDaily
from app.db.session import SessionLocal
from data.candle_builder import Candle

settings = get_settings()
logger = logging.getLogger(__name__)

_redis_client: redis.Redis[str] | None = None


class IndicatorEngineError(BreakoutScanError):
    """Raised when indicator calculation or Redis caching fails."""


@dataclass(slots=True)
class IndicatorSnapshot:
    symbol: str
    timeframe: str
    values: dict[str, str]


def get_redis_client() -> redis.Redis[str]:
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def decimal_string(value: float | int | Decimal | None, scale: str = "0.000001") -> str | None:
    if value is None:
        return None

    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value))

    return str(decimal_value.quantize(Decimal(scale), rounding=ROUND_HALF_UP))


def build_frame(candles: list[Candle]) -> pd.DataFrame:
    rows = [
        {
            "timestamp": candle.start_ts,
            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close),
            "volume": candle.volume,
        }
        for candle in candles
    ]

    if not rows:
        raise IndicatorEngineError("Cannot compute indicators without candles.")

    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.set_index("timestamp")
    return frame


def latest_value(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    cleaned = series.dropna()
    if cleaned.empty:
        return None
    return float(cleaned.iloc[-1])


def extract_previous_daily_values(daily_frame: pd.DataFrame) -> dict[str, str]:
    if len(daily_frame.index) < 2:
        return {}

    previous_day = daily_frame.iloc[-2]
    return {
        "prev_high": decimal_string(previous_day["high"]) or "",
        "prev_low": decimal_string(previous_day["low"]) or "",
        "prev_close": decimal_string(previous_day["close"]) or "",
    }


def extract_orb_values(frame: pd.DataFrame) -> dict[str, str]:
    market_tz = ZoneInfo(settings.market_timezone)
    local_index = frame.index.tz_convert(market_tz)
    session_open = time(9, 15)
    orb_end = time(9, 30)

    mask = [
        current.time() >= session_open and current.time() < orb_end
        for current in local_index
    ]

    orb_frame = frame.loc[mask]
    if orb_frame.empty:
        return {}

    return {
        "orb_high": decimal_string(float(orb_frame["high"].max())) or "",
        "orb_low": decimal_string(float(orb_frame["low"].min())) or "",
    }


def compute_core_indicators(
    frame: pd.DataFrame,
    daily_frame: pd.DataFrame | None,
) -> dict[str, str]:
    close = frame["close"]
    high = frame["high"]
    low = frame["low"]
    volume = frame["volume"]
    values: dict[str, str] = {}

    for length in (9, 14, 21):
        indicator_value = latest_value(ta.rsi(close, length=length))
        decimal_value = decimal_string(indicator_value)
        if decimal_value is not None:
            values[f"rsi_{length}"] = decimal_value

    for length in (9, 20, 50, 200):
        indicator_value = latest_value(ta.ema(close, length=length))
        decimal_value = decimal_string(indicator_value)
        if decimal_value is not None:
            values[f"ema_{length}"] = decimal_value

    for length in (20, 50, 200):
        indicator_value = latest_value(ta.sma(close, length=length))
        decimal_value = decimal_string(indicator_value)
        if decimal_value is not None:
            values[f"sma_{length}"] = decimal_value

    macd_frame = ta.macd(close)
    if macd_frame is not None and not macd_frame.empty:
        macd_line = decimal_string(latest_value(macd_frame.iloc[:, 0]))
        macd_histogram = decimal_string(latest_value(macd_frame.iloc[:, 1]))
        macd_signal = decimal_string(latest_value(macd_frame.iloc[:, 2]))
        if macd_line is not None:
            values["macd_line"] = macd_line
        if macd_signal is not None:
            values["macd_signal"] = macd_signal
        if macd_histogram is not None:
            values["macd_histogram"] = macd_histogram

    bbands_frame = ta.bbands(close, length=20, std=2.0)
    if bbands_frame is not None and not bbands_frame.empty:
        upper = decimal_string(latest_value(bbands_frame.iloc[:, 2]))
        lower = decimal_string(latest_value(bbands_frame.iloc[:, 0]))
        bandwidth = decimal_string(latest_value(bbands_frame.iloc[:, 3]))
        if upper is not None:
            values["bb_upper"] = upper
        if lower is not None:
            values["bb_lower"] = lower
        if bandwidth is not None:
            values["bb_bandwidth"] = bandwidth

    atr = decimal_string(latest_value(ta.atr(high, low, close, length=14)))
    if atr is not None:
        values["atr_14"] = atr

    vwap = decimal_string(latest_value(ta.vwap(high, low, close, volume)))
    if vwap is not None:
        values["vwap"] = vwap

    supertrend_frame = ta.supertrend(high, low, close, length=10, multiplier=3.0)
    if supertrend_frame is not None and not supertrend_frame.empty:
        supertrend_value = decimal_string(latest_value(supertrend_frame.iloc[:, 0]))
        direction = latest_value(supertrend_frame.iloc[:, 1])
        if supertrend_value is not None:
            values["supertrend_10_3"] = supertrend_value
        if direction is not None:
            values["supertrend_direction"] = str(int(direction))

    volume_sma = decimal_string(latest_value(ta.sma(volume, length=20)))
    if volume_sma is not None:
        values["vol_sma_20"] = volume_sma

    if daily_frame is not None and not daily_frame.empty:
        daily_high = float(daily_frame["high"].tail(252).max())
        daily_low = float(daily_frame["low"].tail(252).min())
        values["high_52w"] = decimal_string(daily_high) or ""
        values["low_52w"] = decimal_string(daily_low) or ""
        values.update(extract_previous_daily_values(daily_frame))

    values.update(extract_orb_values(frame))
    return values


async def fetch_daily_reference_frame(symbol: str) -> pd.DataFrame | None:
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(OhlcvDaily)
                .where(OhlcvDaily.symbol == symbol)
                .order_by(OhlcvDaily.date.asc())
            )
        except Exception as error:
            logger.warning("daily reference lookup unavailable for %s: %s", symbol, error)
            return None

    rows = list(result.scalars())
    if not rows:
        return None

    frame = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp(row.date),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": row.volume,
            }
            for row in rows
        ]
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=False)
    frame = frame.set_index("timestamp")
    return frame


class IndicatorEngine:
    async def compute_snapshot(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Candle],
        daily_frame: pd.DataFrame | None = None,
    ) -> IndicatorSnapshot:
        try:
            frame = build_frame(candles)
            if daily_frame is None:
                daily_frame = await fetch_daily_reference_frame(symbol)
            values = compute_core_indicators(frame, daily_frame)
            values["updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            values["close"] = str(candles[-1].close)
            values["volume"] = str(candles[-1].volume)
            return IndicatorSnapshot(symbol=symbol, timeframe=timeframe, values=values)
        except IndicatorEngineError:
            raise
        except Exception as error:
            raise IndicatorEngineError(f"Unable to compute indicators for {symbol} {timeframe}.") from error

    async def store_snapshot(self, snapshot: IndicatorSnapshot) -> IndicatorSnapshot:
        redis_client = get_redis_client()
        key = f"ind:{snapshot.symbol}:{snapshot.timeframe}"

        try:
            await redis_client.hset(key, mapping=snapshot.values)
            await redis_client.expire(key, settings.redis_indicator_ttl_seconds)
        except redis.RedisError as error:
            raise IndicatorEngineError(
                f"Unable to store indicator cache for {snapshot.symbol} {snapshot.timeframe}."
            ) from error

        return snapshot

    async def compute_and_store(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Candle],
    ) -> IndicatorSnapshot:
        snapshot = await self.compute_snapshot(symbol=symbol, timeframe=timeframe, candles=candles)
        return await self.store_snapshot(snapshot)

    async def read_snapshot(self, symbol: str, timeframe: str) -> dict[str, str]:
        redis_client = get_redis_client()
        key = f"ind:{symbol}:{timeframe}"

        try:
            return await redis_client.hgetall(key)
        except redis.RedisError as error:
            raise IndicatorEngineError(
                f"Unable to read indicator cache for {symbol} {timeframe}."
            ) from error


_engine: IndicatorEngine | None = None


def get_indicator_engine() -> IndicatorEngine:
    global _engine

    if _engine is None:
        _engine = IndicatorEngine()

    return _engine


def manual_ema(values: list[Decimal], length: int) -> Decimal:
    if len(values) < length:
        raise IndicatorEngineError("Not enough values to compute manual EMA.")

    multiplier = Decimal("2") / (Decimal(length) + Decimal("1"))
    ema = sum(values[:length]) / Decimal(length)
    for value in values[length:]:
        ema = ((value - ema) * multiplier) + ema
    return ema


def manual_rsi(values: list[Decimal], length: int) -> Decimal:
    if len(values) <= length:
        raise IndicatorEngineError("Not enough values to compute manual RSI.")

    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(values, values[1:]):
        delta = current - previous
        gains.append(max(delta, Decimal("0")))
        losses.append(abs(min(delta, Decimal("0"))))

    average_gain = sum(gains[:length]) / Decimal(length)
    average_loss = sum(losses[:length]) / Decimal(length)

    for gain, loss in zip(gains[length:], losses[length:]):
        average_gain = ((average_gain * (Decimal(length) - Decimal("1"))) + gain) / Decimal(length)
        average_loss = ((average_loss * (Decimal(length) - Decimal("1"))) + loss) / Decimal(length)

    if average_loss == 0:
        return Decimal("100")

    rs = average_gain / average_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def build_indicator_validation_candles(symbol: str = "RELIANCE") -> list[Candle]:
    start = pd.Timestamp("2026-03-12 09:15:00", tz=settings.market_timezone).tz_convert("UTC").to_pydatetime()
    candles: list[Candle] = []

    for index in range(40):
        open_price = Decimal("100") + (Decimal(index) / Decimal("2"))
        close_price = open_price + Decimal("0.30")
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="15min",
                start_ts=start + pd.Timedelta(minutes=index * 15).to_pytimedelta(),
                end_ts=start + pd.Timedelta(minutes=(index + 1) * 15).to_pytimedelta(),
                open=open_price,
                high=close_price + Decimal("0.40"),
                low=open_price - Decimal("0.20"),
                close=close_price,
                volume=1000 + index * 25,
            )
        )

    return candles


async def validate_indicator_engine() -> dict[str, str]:
    engine = IndicatorEngine()
    candles = build_indicator_validation_candles()
    snapshot = await engine.compute_snapshot(
        symbol="RELIANCE",
        timeframe="15min",
        candles=candles,
        daily_frame=pd.DataFrame(),
    )
    closes = [candle.close for candle in candles]

    expected_ema_9 = manual_ema(closes, 9)
    expected_rsi_14 = manual_rsi(closes, 14)
    actual_ema_9 = Decimal(snapshot.values["ema_9"])
    actual_rsi_14 = Decimal(snapshot.values["rsi_14"])

    ema_delta = abs(actual_ema_9 - expected_ema_9)
    rsi_delta = abs(actual_rsi_14 - expected_rsi_14)

    if ema_delta > Decimal("0.05"):
        raise IndicatorEngineError("EMA 9 validation drifted beyond tolerance.")
    if rsi_delta > Decimal("0.05"):
        raise IndicatorEngineError("RSI 14 validation drifted beyond tolerance.")

    return {
        "ema_9": snapshot.values["ema_9"],
        "rsi_14": snapshot.values["rsi_14"],
        "ema_delta": str(ema_delta.quantize(Decimal("0.000001"))),
        "rsi_delta": str(rsi_delta.quantize(Decimal("0.000001"))),
    }

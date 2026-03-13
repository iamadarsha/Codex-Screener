"""Yahoo Finance data provider for historical OHLCV and technical indicators."""

from __future__ import annotations

import asyncio
import math
from typing import Any

import pandas as pd
import structlog
import yfinance as yf

from app.services.redis_cache import hset_dict
from app.utils.redis_keys import indicator_key

log = structlog.get_logger(__name__)

# Rate-limit: short pause between successive yfinance downloads to avoid
# getting throttled by Yahoo.
_RATE_LIMIT_DELAY = 0.5  # seconds


def _safe_str(value: Any) -> str:
    """Convert a value to string, replacing NaN / None with empty string."""
    if value is None:
        return ""
    try:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _nse_ticker(symbol: str) -> str:
    """Append ``.NS`` suffix for NSE stocks if not already present."""
    symbol = symbol.strip().upper()
    if not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    return symbol


class YFinanceProvider:
    """Fetches historical data via *yfinance* and computes technical indicators
    using *pandas-ta*, storing the results in Redis.
    """

    # ------------------------------------------------------------------
    # Historical data
    # ------------------------------------------------------------------

    @staticmethod
    def get_historical(
        symbol: str,
        period: str = "6mo",
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        """Download OHLCV history for *symbol* and return as a list of dicts.

        This is a **synchronous** call because ``yfinance`` uses ``requests``
        under the hood.  Callers should run it inside
        ``asyncio.to_thread()`` when used from async code.
        """
        ticker = _nse_ticker(symbol)
        try:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )
            if df.empty:
                log.warning("yfinance_empty_data", symbol=ticker)
                return []

            # Flatten MultiIndex columns if present (yfinance >= 0.2.31)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            records: list[dict[str, Any]] = []
            for idx, row in df.iterrows():
                records.append(
                    {
                        "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                        "open": float(row.get("Open", 0)),
                        "high": float(row.get("High", 0)),
                        "low": float(row.get("Low", 0)),
                        "close": float(row.get("Close", 0)),
                        "volume": int(row.get("Volume", 0)),
                    }
                )
            return records
        except Exception as exc:
            log.warning("yfinance_download_error", symbol=ticker, error=str(exc))
            return []

    # ------------------------------------------------------------------
    # Indicator computation + Redis storage
    # ------------------------------------------------------------------

    @staticmethod
    async def compute_and_store_indicators(symbol: str) -> bool:
        """Fetch 1-year history, compute indicators, and store in Redis.

        Returns ``True`` on success, ``False`` on failure.
        """
        try:
            import pandas_ta as ta  # noqa: F811 – local import to isolate dep

            ticker = _nse_ticker(symbol)
            df = await asyncio.to_thread(
                yf.download,
                ticker,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )

            if df.empty:
                log.warning("yfinance_no_data_for_indicators", symbol=symbol)
                return False

            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Ensure columns are simple strings
            df.columns = [str(c) for c in df.columns]

            # --- Compute indicators ----------------------------------------
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            # RSI
            rsi_series = ta.rsi(close, length=14)
            rsi = rsi_series.iloc[-1] if rsi_series is not None and len(rsi_series) else None

            # EMAs
            ema9_series = ta.ema(close, length=9)
            ema9 = ema9_series.iloc[-1] if ema9_series is not None and len(ema9_series) else None

            ema21_series = ta.ema(close, length=21)
            ema21 = ema21_series.iloc[-1] if ema21_series is not None and len(ema21_series) else None

            # SMAs
            sma20_series = ta.sma(close, length=20)
            sma20 = sma20_series.iloc[-1] if sma20_series is not None and len(sma20_series) else None

            sma50_series = ta.sma(close, length=50)
            sma50 = sma50_series.iloc[-1] if sma50_series is not None and len(sma50_series) else None

            sma200_series = ta.sma(close, length=200)
            sma200 = sma200_series.iloc[-1] if sma200_series is not None and len(sma200_series) else None

            # MACD
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            macd_val = None
            macd_signal = None
            if macd_df is not None and not macd_df.empty:
                macd_cols = macd_df.columns.tolist()
                # pandas-ta returns columns like MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
                for col in macd_cols:
                    if col.startswith("MACD_"):
                        macd_val = macd_df[col].iloc[-1]
                    elif col.startswith("MACDs_"):
                        macd_signal = macd_df[col].iloc[-1]

            # Bollinger Bands
            bb_df = ta.bbands(close, length=20, std=2)
            bb_upper = None
            bb_lower = None
            if bb_df is not None and not bb_df.empty:
                bb_cols = bb_df.columns.tolist()
                for col in bb_cols:
                    if col.startswith("BBU_"):
                        bb_upper = bb_df[col].iloc[-1]
                    elif col.startswith("BBL_"):
                        bb_lower = bb_df[col].iloc[-1]

            # ATR
            atr_series = ta.atr(high, low, close, length=14)
            atr = atr_series.iloc[-1] if atr_series is not None and len(atr_series) else None

            # ADX
            adx_df = ta.adx(high, low, close, length=14)
            adx_val = None
            if adx_df is not None and not adx_df.empty:
                adx_cols = adx_df.columns.tolist()
                for col in adx_cols:
                    if col.startswith("ADX_"):
                        adx_val = adx_df[col].iloc[-1]

            # VWAP (only meaningful for intraday but we compute a rolling proxy)
            vwap_series = ta.vwap(high, low, close, volume)
            vwap = vwap_series.iloc[-1] if vwap_series is not None and len(vwap_series) else None

            # Volume SMA(20)
            vol_sma20_series = ta.sma(volume.astype(float), length=20)
            vol_sma20 = (
                vol_sma20_series.iloc[-1]
                if vol_sma20_series is not None and len(vol_sma20_series)
                else None
            )

            # --- Latest and previous OHLCV -----------------------------------
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else latest

            latest_close = float(latest["Close"])
            prev_close_val = float(prev["Close"])
            change_pct = (
                round(((latest_close - prev_close_val) / prev_close_val) * 100, 2)
                if prev_close_val
                else 0.0
            )

            # 52-week high
            high_52w = float(high.tail(252).max()) if len(high) >= 252 else float(high.max())

            # --- Build mapping and store in Redis -----------------------------
            mapping = {
                "open": _safe_str(latest.get("Open")),
                "high": _safe_str(latest.get("High")),
                "low": _safe_str(latest.get("Low")),
                "close": _safe_str(latest.get("Close")),
                "volume": _safe_str(latest.get("Volume")),
                "prev_open": _safe_str(prev.get("Open")),
                "prev_high": _safe_str(prev.get("High")),
                "prev_low": _safe_str(prev.get("Low")),
                "prev_close": _safe_str(prev.get("Close")),
                "prev_volume": _safe_str(prev.get("Volume")),
                "rsi_14": _safe_str(rsi),
                "ema_9": _safe_str(ema9),
                "ema_21": _safe_str(ema21),
                "sma_20": _safe_str(sma20),
                "sma_50": _safe_str(sma50),
                "sma_200": _safe_str(sma200),
                "macd": _safe_str(macd_val),
                "macd_signal": _safe_str(macd_signal),
                "atr_14": _safe_str(atr),
                "adx_14": _safe_str(adx_val),
                "vwap": _safe_str(vwap),
                "bollinger_upper": _safe_str(bb_upper),
                "bollinger_lower": _safe_str(bb_lower),
                "sma_20_volume": _safe_str(vol_sma20),
                "change_pct": _safe_str(change_pct),
                "high_52w": _safe_str(high_52w),
            }

            await hset_dict(indicator_key(symbol, "1d"), mapping, ttl=14400)

            # Store OHLCV bars in Redis for chart rendering (avoids DB dependency)
            try:
                from app.services.redis_cache import set_json as _set_json

                ohlcv_records = []
                for ts_idx, row in df.iterrows():
                    epoch = int(ts_idx.timestamp()) if hasattr(ts_idx, "timestamp") else 0
                    ohlcv_records.append({
                        "time": epoch,
                        "open": round(float(row.get("Open", 0)), 2),
                        "high": round(float(row.get("High", 0)), 2),
                        "low": round(float(row.get("Low", 0)), 2),
                        "close": round(float(row.get("Close", 0)), 2),
                        "volume": int(row.get("Volume", 0)),
                    })
                if ohlcv_records:
                    await _set_json(f"ohlcv:{symbol}:daily", ohlcv_records, ttl=14400)
            except Exception as ohlcv_exc:
                log.warning("ohlcv_store_error", symbol=symbol, error=str(ohlcv_exc))

            log.info("indicators_stored", symbol=symbol)
            return True

        except Exception as exc:
            log.warning("indicator_compute_error", symbol=symbol, error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Bulk compute
    # ------------------------------------------------------------------

    @staticmethod
    async def bulk_compute(symbols: list[str]) -> dict[str, bool]:
        """Compute and store indicators for all *symbols* with rate limiting.

        Returns a dict mapping symbol to success boolean.
        """
        results: dict[str, bool] = {}
        total = len(symbols)

        for idx, symbol in enumerate(symbols, 1):
            log.info("bulk_compute_progress", symbol=symbol, current=idx, total=total)
            ok = await YFinanceProvider.compute_and_store_indicators(symbol)
            results[symbol] = ok
            # Rate limit to avoid Yahoo throttling
            if idx < total:
                await asyncio.sleep(_RATE_LIMIT_DELAY)

        succeeded = sum(1 for v in results.values() if v)
        log.info("bulk_compute_done", total=total, succeeded=succeeded, failed=total - succeeded)
        return results

"""Redis key constants and helper formatters for BreakoutScan."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# TTL constants (seconds)
# ---------------------------------------------------------------------------
TTL_TOKEN: int = 8 * 60 * 60  # 8 h  (Upstox market session)
TTL_INSTRUMENT_MAP: int = 24 * 60 * 60  # 24 h
TTL_LTP: int = 60  # 60 s
TTL_INDICATOR: int = 5 * 60  # 5 min
TTL_CANDLE_CURRENT: int = 20 * 60  # 20 min (safety buffer for 15-min candles)
TTL_UNIVERSE: int = 24 * 60 * 60  # 24 h
TTL_WS_TICK: int = 5 * 60  # 5 min

# ---------------------------------------------------------------------------
# Key prefixes / static keys
# ---------------------------------------------------------------------------
KEY_UPSTOX_TOKEN: str = "upstox:token"
KEY_SYMBOL_TO_KEY: str = "instrument:symbol_to_key"
KEY_KEY_TO_SYMBOL: str = "instrument:key_to_symbol"
KEY_UNIVERSE_NIFTY50: str = "universe:nifty50"
KEY_UNIVERSE_NIFTY500: str = "universe:nifty500"
KEY_WS_LAST_TICK: str = "ws:last_tick_at"

# ---------------------------------------------------------------------------
# Key builder helpers
# ---------------------------------------------------------------------------


def ltp_key(instrument_key: str) -> str:
    """Return the Redis key for a last-traded-price entry by instrument key."""
    return f"ltp:{instrument_key}"


def ltp_symbol_key(symbol: str) -> str:
    """Return the Redis key for a last-traded-price entry by symbol."""
    return f"ltp:symbol:{symbol}"


def indicator_key(symbol: str, timeframe: str) -> str:
    """Return the Redis hash key for computed indicators.

    *timeframe* is one of ``1min``, ``5min``, ``15min``, ``1d``, etc.
    """
    return f"ind:{symbol}:{timeframe}"


def candle_current_key(symbol: str, timeframe: str) -> str:
    """Return the Redis key for the current (in-progress) candle."""
    return f"candle:{symbol}:{timeframe}:current"


def universe_key(name: str) -> str:
    """Return the Redis set key for a stock universe."""
    return f"universe:{name}"


def orb_range_key(symbol: str) -> str:
    """Return the Redis hash key for an ORB range."""
    return f"orb:{symbol}:range"


def scan_result_key(scan_hash: str) -> str:
    """Return the Redis key for cached scan results (30 s TTL)."""
    return f"scan:last_run:{scan_hash}"


def indicator_history_key(symbol: str, timeframe: str, field: str) -> str:
    """Return the Redis list key for historical indicator values."""
    return f"ind_hist:{symbol}:{timeframe}:{field}"

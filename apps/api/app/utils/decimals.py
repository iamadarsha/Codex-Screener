"""Decimal conversion helpers for safe numeric handling."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def safe_decimal(val: Any, default: Decimal | None = None) -> Decimal | None:
    """Convert *val* to :class:`Decimal` without raising.

    Returns *default* (``None`` by default) when conversion fails.
    """
    if val is None:
        return default
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return default


def decimal_to_str(val: Decimal | None, places: int = 4) -> str | None:
    """Format a :class:`Decimal` to a fixed-point string suitable for JSON.

    Returns ``None`` when the input is ``None``.
    """
    if val is None:
        return None
    return f"{val:.{places}f}"

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.models.ohlcv import Ohlcv1Min
from app.db.models.stock import Stock
from app.db.session import SessionLocal


class OhlcvVerificationError(Exception):
    """Raised when the OHLCV verification script fails."""


async def fetch_symbols(limit: int = 25) -> list[str]:
    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(Stock.symbol).where(Stock.is_nifty500.is_(True)).order_by(Stock.symbol).limit(limit)
            )
        except Exception as error:
            raise OhlcvVerificationError("Unable to fetch seeded stock symbols.") from error

    return list(result.scalars())


def build_rows(symbols: list[str]) -> list[dict[str, object]]:
    start = datetime(2026, 1, 1, 9, 15, tzinfo=UTC)
    rows: list[dict[str, object]] = []

    for symbol_index, symbol in enumerate(symbols):
        price_base = Decimal("100") + Decimal(symbol_index)
        for offset in range(400):
            ts = start + timedelta(minutes=offset)
            open_price = price_base + Decimal(offset) / Decimal("100")
            high_price = open_price + Decimal("0.80")
            low_price = open_price - Decimal("0.65")
            close_price = open_price + Decimal("0.25")
            volume = 1000 + symbol_index * 10 + offset
            rows.append(
                {
                    "symbol": symbol,
                    "ts": ts,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
            )

    return rows


async def insert_rows(rows: list[dict[str, object]]) -> None:
    async with SessionLocal() as session:
        try:
            for batch_start in range(0, len(rows), 1000):
                batch = rows[batch_start : batch_start + 1000]
                statement = insert(Ohlcv1Min).values(batch).on_conflict_do_nothing()
                await session.execute(statement)
            await session.commit()
        except Exception as error:
            await session.rollback()
            raise OhlcvVerificationError("Unable to insert OHLCV verification rows.") from error


async def verify_hypertable() -> tuple[int, str]:
    async with SessionLocal() as session:
        try:
            hypertable_result = await session.execute(
                text(
                    """
                    SELECT hypertable_name
                    FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'ohlcv_1min'
                    """
                )
            )
            hypertable_name = hypertable_result.scalar_one_or_none()
            if hypertable_name != "ohlcv_1min":
                raise OhlcvVerificationError("ohlcv_1min is not registered as a hypertable.")

            count_result = await session.execute(select(func.count()).select_from(Ohlcv1Min))
            row_count = int(count_result.scalar_one())
        except Exception as error:
            if isinstance(error, OhlcvVerificationError):
                raise
            raise OhlcvVerificationError("Unable to verify the OHLCV hypertable.") from error

    return row_count, hypertable_name


async def async_main() -> None:
    symbols = await fetch_symbols()
    if len(symbols) < 25:
        raise OhlcvVerificationError("Expected at least 25 seeded NIFTY500 stocks before backfill.")

    rows = build_rows(symbols)
    if len(rows) != 10000:
        raise OhlcvVerificationError("The verification data set must contain exactly 10,000 rows.")

    await insert_rows(rows)
    row_count, hypertable_name = await verify_hypertable()
    print(f"hypertable={hypertable_name} row_count={row_count}")


def main() -> int:
    try:
        asyncio.run(async_main())
    except OhlcvVerificationError as error:
        print(f"backfill_ohlcv error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

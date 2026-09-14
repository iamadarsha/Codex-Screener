"""Insert any symbol missing from the `stocks` table that the live feed
subscribes to.

Discovered live (2026-09-15): `seed_stocks.py`'s default local cache
(`data/nifty500_seed.json`) is a static snapshot that can drift from the
*live* NIFTY 500 constituent list `nse_poller.py` actually subscribes to
(via `app.services.nse_live.fetch_bulk_quotes`, added when the live feed
was rebuilt on jugaad-data). A symbol present in the live list but absent
from `stocks` fails `ohlcv_1min`'s and `breakout_events`'s foreign key
constraint — and because candles are persisted in one batched multi-row
INSERT, a single missing symbol in a batch rolls back the *entire* batch,
blocking persistence for every other symbol in it too.

This is a defensive reconciliation, not a replacement for `seed_stocks.py`
— it only ever inserts a minimal placeholder row (symbol as company_name)
for symbols not already present; it never updates or removes existing
rows' real metadata.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.models.stock import Stock
from app.db.session import SessionLocal
from app.services.nse_live import fetch_bulk_quotes


async def main() -> int:
    live_rows = await fetch_bulk_quotes("NIFTY 500")
    # jugaad-data's live_index response includes an aggregate row for the
    # index itself alongside real constituents — exclude it the same way
    # nse_poller.py's _populate_universe() already does.
    live_symbols = {
        row["symbol"]
        for row in live_rows
        if row.get("symbol") and row["symbol"] not in ("NIFTY 50", "NIFTY 500")
    }
    if not live_symbols:
        print("No symbols returned from the live feed — nothing to reconcile.")
        return 1

    async with SessionLocal() as session:
        existing = set((await session.execute(select(Stock.symbol))).scalars().all())
        missing = sorted(live_symbols - existing)

        if not missing:
            print(f"stocks table already covers all {len(live_symbols)} live symbols.")
            return 0

        stmt = insert(Stock).values(
            [
                {
                    "symbol": symbol,
                    "company_name": symbol,
                    "exchange": "NSE",
                    "is_nifty500": True,
                }
                for symbol in missing
            ]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["symbol"])
        await session.execute(stmt)
        await session.commit()

    print(f"Inserted {len(missing)} missing symbol(s): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

import httpx
from sqlalchemy.dialects.postgresql import insert

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.models.stock import Stock
from app.db.session import SessionLocal

NSE_HOME_URL = "https://www.nseindia.com"
NSE_INDEX_URL = "https://www.nseindia.com/api/equity-stockIndices"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "nifty500_seed.json"


class SeedError(Exception):
    """Raised when stock seeding cannot continue."""


@dataclass(slots=True)
class SeedStockRecord:
    symbol: str
    isin: str | None
    instrument_key: str | None
    company_name: str
    exchange: str
    sector: str | None
    market_cap: str | None
    pe: str | None
    pb: str | None
    roe: str | None
    debt_equity: str | None
    div_yield: str | None
    is_nifty50: bool
    is_nifty500: bool
    is_fno: bool
    is_active: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the stocks table with NSE data.")
    parser.add_argument(
        "--cache-file",
        type=Path,
        default=DEFAULT_CACHE_PATH,
        help="Path to the local JSON cache file.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Fetch the latest NIFTY data from NSE before seeding.",
    )
    parser.add_argument(
        "--write-cache-only",
        action="store_true",
        help="Refresh the cache file and exit without touching the database.",
    )
    return parser


def decimal_to_string(value: object) -> str | None:
    if value in (None, ""):
        return None

    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError):
        return None


async def bootstrap_nse_client(client: httpx.AsyncClient) -> None:
    try:
        response = await client.get(NSE_HOME_URL, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise SeedError("Unable to bootstrap NSE cookie session.") from error


async def fetch_index_members(
    client: httpx.AsyncClient,
    index_name: str,
) -> list[dict[str, object]]:
    try:
        response = await client.get(
            NSE_INDEX_URL,
            params={"index": index_name},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = cast(dict[str, object], response.json())
    except (httpx.HTTPError, ValueError) as error:
        raise SeedError(f"Unable to fetch index data for {index_name}.") from error

    raw_rows = cast(list[dict[str, object]], payload.get("data", []))

    return [
        row
        for row in raw_rows
        if row.get("symbol") not in {index_name, None} and isinstance(row.get("meta"), dict)
    ]


async def fetch_seed_records() -> list[SeedStockRecord]:
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
        ),
        "accept": "application/json,text/plain,*/*",
        "referer": NSE_HOME_URL,
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        await bootstrap_nse_client(client)
        nifty500_rows, nifty50_rows = await asyncio.gather(
            fetch_index_members(client, "NIFTY 500"),
            fetch_index_members(client, "NIFTY 50"),
        )

    nifty50_symbols = {str(row["symbol"]) for row in nifty50_rows if row.get("symbol")}

    records: list[SeedStockRecord] = []

    for row in nifty500_rows:
        meta = cast(dict[str, object], row["meta"])
        symbol = str(row["symbol"])
        is_active = not bool(meta.get("isSuspended", False))
        records.append(
            SeedStockRecord(
                symbol=symbol,
                isin=cast(str | None, meta.get("isin")),
                instrument_key=None,
                company_name=str(meta.get("companyName", symbol)),
                exchange="NSE",
                sector=cast(str | None, meta.get("industry")),
                market_cap=decimal_to_string(row.get("ffmc")),
                pe=None,
                pb=None,
                roe=None,
                debt_equity=None,
                div_yield=None,
                is_nifty50=symbol in nifty50_symbols,
                is_nifty500=True,
                is_fno=bool(meta.get("isFNOSec", False)),
                is_active=is_active,
            )
        )

    return sorted(records, key=lambda record: record.symbol)


def load_cache(cache_file: Path) -> list[SeedStockRecord]:
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SeedError(f"Cache file not found: {cache_file}") from error
    except json.JSONDecodeError as error:
        raise SeedError(f"Cache file is invalid JSON: {cache_file}") from error

    if not isinstance(payload, list):
        raise SeedError("Cache file payload must be a JSON array.")

    return [SeedStockRecord(**cast(dict[str, object], item)) for item in payload]


def write_cache(cache_file: Path, records: list[SeedStockRecord]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps([asdict(record) for record in records], indent=2),
        encoding="utf-8",
    )


async def seed_database(records: list[SeedStockRecord]) -> None:
    rows: list[dict[str, object]] = []
    for record in records:
        row = asdict(record)
        row["market_cap"] = (
            Decimal(record.market_cap) if record.market_cap is not None else None
        )
        rows.append(row)

    async with SessionLocal() as session:
        try:
            statement = insert(Stock).values(rows)
            update_columns = {
                "isin": statement.excluded.isin,
                "company_name": statement.excluded.company_name,
                "exchange": statement.excluded.exchange,
                "sector": statement.excluded.sector,
                "market_cap": statement.excluded.market_cap,
                "is_nifty50": statement.excluded.is_nifty50,
                "is_nifty500": statement.excluded.is_nifty500,
                "is_fno": statement.excluded.is_fno,
                "is_active": statement.excluded.is_active,
            }
            await session.execute(
                statement.on_conflict_do_update(
                    index_elements=[Stock.symbol],
                    set_=update_columns,
                )
            )
            await session.commit()
        except Exception as error:
            await session.rollback()
            raise SeedError("Failed to upsert stock records into PostgreSQL.") from error


async def async_main(args: argparse.Namespace) -> None:
    if args.refresh_cache:
        records = await fetch_seed_records()
        write_cache(args.cache_file, records)
    else:
        records = load_cache(args.cache_file)

    if args.write_cache_only:
        print(f"Wrote {len(records)} stock records to {args.cache_file}")
        return

    await seed_database(records)
    print(f"Seeded {len(records)} stocks into PostgreSQL")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        asyncio.run(async_main(args))
    except SeedError as error:
        print(f"seed_stocks error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

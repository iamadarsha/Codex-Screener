"""Background poller that fetches NSE data and populates Redis for live data."""
import asyncio
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

POLL_INTERVAL = 30  # seconds
MAJOR_INDICES = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO", "NIFTY FMCG", "INDIA VIX", "NIFTY MIDCAP 50"]


async def _populate_universe_and_compute(stock_data: list[dict]) -> None:
    """Extract symbols from stock data, populate universe sets, and kick off
    indicator computation in the background.

    Called once on the first successful poll iteration.
    """
    from app.services.redis_cache import get_redis

    redis = await get_redis()

    nifty50_symbols: list[str] = []
    for stock in stock_data:
        symbol = stock.get("symbol", "")
        if symbol and symbol != "NIFTY 50":
            nifty50_symbols.append(symbol)

    if nifty50_symbols:
        # Populate Nifty 50 universe
        await redis.delete("universe:nifty50")
        await redis.sadd("universe:nifty50", *nifty50_symbols)
        log.info("Populated universe:nifty50 with %d symbols", len(nifty50_symbols))

        # Also populate nifty500 with the same data for now (will be expanded
        # when more data sources provide the full Nifty 500 list).
        await redis.delete("universe:nifty500")
        await redis.sadd("universe:nifty500", *nifty50_symbols)
        log.info("Populated universe:nifty500 with %d symbols", len(nifty50_symbols))

        # Kick off bulk indicator computation in the background so it does not
        # block the polling loop.
        asyncio.create_task(
            _run_bulk_compute(nifty50_symbols),
            name="bulk_compute_nifty50",
        )


async def _run_bulk_compute(symbols: list[str]) -> None:
    """Wrapper that runs YFinanceProvider.bulk_compute and logs completion."""
    from app.services.yahoo_finance import YFinanceProvider

    try:
        log.info("Starting bulk indicator compute for %d symbols", len(symbols))
        results = await YFinanceProvider.bulk_compute(symbols)
        succeeded = sum(1 for v in results.values() if v)
        log.info(
            "Bulk indicator compute finished: %d/%d succeeded",
            succeeded,
            len(symbols),
        )
    except Exception as e:
        log.error("Bulk indicator compute failed: %s", e)


async def _fetch_and_store_trending() -> None:
    """Fetch trending stocks from IndianAPI and store in Redis."""
    from app.services.indian_api import IndianAPIClient
    from app.services.redis_cache import set_json

    client = IndianAPIClient()
    try:
        trending = await client.get_trending()
        if trending:
            await set_json("market:trending", trending, ttl=300)
            log.debug("Stored trending stocks data")
    except Exception as e:
        log.warning("Failed to fetch trending stocks: %s", e)
    finally:
        await client.close()


async def nse_poller_loop():
    """Continuously poll NSE for market data and store in Redis."""
    from app.services.nse_fallback import NSEClient
    from app.services.redis_cache import get_redis, set_json

    client = NSEClient()
    log.info("NSE poller started")

    first_iteration = True

    while True:
        try:
            redis = await get_redis()

            # Fetch all indices
            try:
                raw = await client.get_indices()
                data = raw.get("data", []) if isinstance(raw, dict) else []

                indices_list = []
                breadth = {"advances": 0, "declines": 0, "unchanged": 0}

                for idx in data:
                    name = idx.get("index", "")
                    if name in MAJOR_INDICES:
                        index_data = {
                            "name": name,
                            "symbol": name.replace(" ", ""),
                            "last": idx.get("last", 0),
                            "change": idx.get("change", 0),
                            "change_pct": idx.get("percentChange", 0),
                            "open": idx.get("open"),
                            "high": idx.get("high"),
                            "low": idx.get("low"),
                            "prev_close": idx.get("previousClose"),
                        }
                        indices_list.append(index_data)

                    # Use NIFTY 50 data for breadth
                    if name == "NIFTY 50":
                        breadth["advances"] = idx.get("advances", 0) or 0
                        breadth["declines"] = idx.get("declines", 0) or 0
                        breadth["unchanged"] = idx.get("unchanged", 0) or 0

                if indices_list:
                    await set_json("market:indices", indices_list, ttl=60)
                    log.debug("Stored %d indices", len(indices_list))

                breadth["total"] = breadth["advances"] + breadth["declines"] + breadth["unchanged"]
                breadth["advance_decline_ratio"] = round(breadth["advances"] / max(breadth["declines"], 1), 2)
                await set_json("market:breadth", breadth, ttl=60)

            except Exception as e:
                log.warning("Failed to fetch indices: %s", e)

            # Fetch Nifty 50 stock quotes for live prices
            try:
                http = await client._ensure_client()
                resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 50"})
                if resp.status_code == 403:
                    await client._refresh_cookies()
                    resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 50"})
                if resp.status_code == 200:
                    stock_data = resp.json().get("data", [])
                    for stock in stock_data:
                        symbol = stock.get("symbol", "")
                        if not symbol or symbol == "NIFTY 50":
                            continue
                        price_data = {
                            "symbol": symbol,
                            "ltp": stock.get("lastPrice", 0),
                            "open": stock.get("open", 0),
                            "high": stock.get("dayHigh", 0),
                            "low": stock.get("dayLow", 0),
                            "close": stock.get("lastPrice", 0),
                            "prev_close": stock.get("previousClose", 0),
                            "change": stock.get("change", 0),
                            "change_pct": stock.get("pChange", 0),
                            "volume": stock.get("totalTradedVolume", 0),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        await set_json(f"price:{symbol}", price_data, ttl=60)
                    log.debug("Stored prices for %d stocks", len(stock_data))

                    # On startup: populate universe sets and start bulk compute
                    if first_iteration and stock_data:
                        first_iteration = False
                        await _populate_universe_and_compute(stock_data)

            except Exception as e:
                log.warning("Failed to fetch stock prices: %s", e)

            # Fetch trending stocks from Indian API (non-blocking, every cycle)
            asyncio.create_task(
                _fetch_and_store_trending(),
                name="fetch_trending",
            )

        except Exception as e:
            log.error("NSE poller error: %s", e)

        await asyncio.sleep(POLL_INTERVAL)

"""Background poller that fetches NSE data and populates Redis for live data."""
import asyncio
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

POLL_INTERVAL = 30  # seconds
MAJOR_INDICES = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO", "NIFTY FMCG", "INDIA VIX", "NIFTY MIDCAP 50"]

async def nse_poller_loop():
    """Continuously poll NSE for market data and store in Redis."""
    from app.services.nse_fallback import NSEClient
    from app.services.redis_cache import get_redis, set_json

    client = NSEClient()
    log.info("NSE poller started")

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
            except Exception as e:
                log.warning("Failed to fetch stock prices: %s", e)

        except Exception as e:
            log.error("NSE poller error: %s", e)

        await asyncio.sleep(POLL_INTERVAL)

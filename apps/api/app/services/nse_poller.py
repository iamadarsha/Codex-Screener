"""Background poller that fetches NSE data and populates Redis for live data."""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone

log = logging.getLogger(__name__)

POLL_INTERVAL = 30  # seconds
COMPUTE_INTERVAL = 300  # 5 minutes — indicator refresh cycle
MAJOR_INDICES = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO", "NIFTY FMCG", "INDIA VIX", "NIFTY MIDCAP 50"]

# ── NIFTY 50 constituents (large-cap anchor universe) ────────────────────────
NIFTY_50_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY",
    "EICHERMOT", "ETERNAL", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK",
    "LT", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
    "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
]

# ── NIFTY 500 static fallback (used when live NSE fetch is unavailable) ───────
# Covers large-cap, mid-cap and small-cap across all major sectors.
# Updated periodically; NSE live fetch supersedes this at runtime.
NIFTY_500_SYMBOLS = [
    # ── NIFTY 50 ──────────────────────────────────────────────────────────────
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DRREDDY",
    "EICHERMOT", "ETERNAL", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK",
    "LT", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
    "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
    # ── NIFTY NEXT 50 ─────────────────────────────────────────────────────────
    "ABB", "AMBUJACEM", "ATGL", "DELHIVERY", "DIVISLAB",
    "DLF", "HAVELLS", "HAL", "INDIAMART", "IOC",
    "IRCTC", "JUBLFOOD", "LODHA", "MARICO", "MUTHOOTFIN",
    "NAUKRI", "NBCC", "NHPC", "NMDC", "OFSS",
    "PAYTM", "PFC", "PIDILITIND", "RECLTD", "SRF",
    "SAIL", "SIEMENS", "TORNTPHARM", "TATAPOWER", "TVSMOTOR",
    "UNITDSPR", "VBL", "VEDL", "ZOMATO", "ZYDUSLIFE",
    "GODREJCP", "INDUSTOWER", "IRFC", "JSWINFRA", "LUPIN",
    "MAXHEALTH", "MOTHERSON", "RVNL", "SHREECEM", "SHRIRAMFIN",
    "TATAELXSI", "TORNTPOWER", "OBEROIRLTY", "CGPOWER", "DIXON",
    # ── Banking & Finance ──────────────────────────────────────────────────────
    "BANKBARODA", "CANBK", "IDFCFIRSTB", "FEDERALBNK", "PNB",
    "UNIONBANK", "YESBANK", "BANDHANBNK", "AUBANK", "RBLBANK",
    "KARURVYSYA", "CITYUNIONBK", "DCBBANK", "SOUTHBANK", "EQUITASBNK",
    "UJJIVANSFB", "ESAFSFB", "IDBI", "MAHABANK", "J&KBANK",
    "CHOLAFIN", "MANAPPURAM", "LICHSGFIN", "IIFL", "MOTILALOFS",
    "ANGELONE", "SBICARD", "ICICIPRULI", "ICICIGI", "HDFCAMC",
    "NIPPONLIFE", "ABSLAMC", "UTIAMC", "360ONE", "NUVAMA",
    "BAJAJHFL", "LICI", "POONAWALLA", "CREDITACC", "APTUS",
    # ── IT & Technology ───────────────────────────────────────────────────────
    "MPHASIS", "LTI", "LTIM", "COFORGE", "PERSISTENT",
    "KPITTECH", "CYIENT", "MASTEK", "SONATSOFTW", "BIRLASOFT",
    "RATEGAIN", "TATATECH", "TANLA", "NEWGEN", "INTELLECT",
    "NUCLEUS", "RAMCO", "ROUTE", "HAPPSTMNDS", "ZENSAR",
    "HEXAWARE", "NIIT", "DATAMATICS", "SUBEXLTD", "SAKSOFT",
    # ── Pharma & Healthcare ───────────────────────────────────────────────────
    "BIOCON", "AUROPHARMA", "ALKEM", "GLENMARK", "IPCA",
    "LAURUSLABS", "GRANULES", "NATCOPHARMA", "SYNGENE", "PFIZER",
    "ABBOTINDIA", "GLAXO", "WOCKPHARMA", "ERIS", "JBCHEPHARM",
    "ASTRAZEN", "SUVEN", "LALPATHLAB", "METROPOLIS", "DRREDDYLAB",
    "IPCALAB", "FORTIS", "NARAYANA", "RAINBOW", "VIJAYABANK",
    "MEDANTA", "KRSNAA", "PRISTINE", "POLYMED", "ESTEEMEDCARE",
    # ── Auto & Auto Ancillaries ───────────────────────────────────────────────
    "ASHOKLEY", "BALKRISIND", "BHARATFORG", "ENDURANCE", "SUNDRMFAST",
    "MINDA", "BOSCH", "TIINDIA", "SOMICONVEY", "EXIDEIND",
    "AMARAJABAT", "CEATLTD", "APOLLOTYRE", "MFSL", "SUPRAJIT",
    "GABRIEL", "SUBROS", "LUMAX", "MINDAIND", "SAMVARDHANA",
    "SCHAEFFLER", "TIMKEN", "SKFINDIA", "FAGBEARINGS", "WABCO",
    # ── Energy & Power ────────────────────────────────────────────────────────
    "GAIL", "ADANIGREEN", "SJVN", "CESC", "JSPL",
    "HINDPETRO", "MRPL", "PETRONET", "GUJTGAS", "IGL",
    "MGL", "ADANIENSOL", "IRCON", "KNRCON", "PNBHOUSING",
    "JSWENERGY", "GREENKO", "SUZLON", "INOXWIND", "WIPRO",
    "KALPATPOWR", "RPOWER", "GVK", "LNTECC", "BHEL",
    # ── FMCG & Consumer ───────────────────────────────────────────────────────
    "DABUR", "EMAMILTD", "BAJAJCON", "JYOTHYLAB", "RADICO",
    "MCDOWELL-N", "COLPAL", "GILLETTE", "PGHH", "HATSUN",
    "HERITGFOOD", "DODLA", "DEVYANI", "WESTLIFE", "BARBEQUE",
    "SAPIENT", "TASTYBITE", "BIKAJI", "GOPAL", "AVANTIFEED",
    # ── Infrastructure & Real Estate ──────────────────────────────────────────
    "GMRINFRA", "IRB", "GRSE", "MDL", "NLC",
    "AHLUCONT", "HG INFRA", "PNC INFRATECH", "KEC", "KALINDEE",
    "JKCEMENT", "RAMCOCEM", "HEIDELBERG", "DALMIA", "NUVOCO",
    "ACC", "STARCEMENT", "BIRLACORPN", "PRISM", "WONDER",
    "SOBHA", "PRESTIGE", "BRIGADE", "GODREJPROP", "SUNTECK",
    "KOLTEPATIL", "MAHINDLIFE", "IBREALEST", "PHOENIXLTD", "NESCO",
    # ── Metals & Mining ───────────────────────────────────────────────────────
    "NATIONALUM", "WELCORP", "APL", "RATNAMANI", "APLAPOLLO",
    "JINDALSTEL", "MOIL", "GMDC", "EDELWEISS", "TINPLATE",
    "HINDUSTAN ZINC", "HINDCOPPER", "HINDZINC", "BALCO", "NALCO",
    # ── Telecom & Media ───────────────────────────────────────────────────────
    "IDEA", "TTML", "STLTELECOM", "HFCL", "TEJAS",
    "SUNTV", "ZEEL", "PVR", "INOX", "SAREGAMA",
    "NAZARA", "NXTDIGITAL", "DBCORP", "JUBLPHARMA", "NETWORK18",
    # ── Capital Goods & Engineering ───────────────────────────────────────────
    "CUMMINSIND", "THERMAX", "BHARAT FORGE", "GRINDWELL", "CARBORUNIV",
    "ELGIEQUIP", "KIRLOSKER", "KIRLOSBROS", "KIRILINDS", "PRAJ",
    "JYOTISTRUC", "AIAENG", "GREAVES", "TRIVENI", "BLUESTAR",
    "WHIRLPOOL", "VOLTAS", "SYMPHONY", "ORIENTELEC", "AMBER",
    "DIXON", "VGUARD", "POLYCAB", "KEI", "FINOLEX",
    # ── Chemicals & Specialty ─────────────────────────────────────────────────
    "AARTI", "AARTIDRUGS", "DEEPAKNI", "DEEPAKNTR", "FINEORG",
    "GALAXYSURF", "NAVINFLUOR", "FLUOROCHEM", "ALKYLAMINE", "CLEAN",
    "BALAJI AMINES", "NEOGEN", "TATACHEM", "GSFC", "GNFC",
    "COROMANDEL", "CHAMBAL", "BASF", "ATUL", "VINATI",
    # ── Retail & E-commerce ───────────────────────────────────────────────────
    "DMART", "TRENT", "ABFRL", "MANYAVAR", "VEDANT",
    "SHOPERSTOP", "V2RETAIL", "VMART", "THANGAMAYL", "SENCO",
    "METRO", "BATA", "RELAXO", "KHADIM", "LIBERTY",
    # ── Logistics & Shipping ─────────────────────────────────────────────────
    "BLUEDART", "MAHLOG", "ALLCARGO", "GATI", "CONCOR",
    "AEGISLOG", "TCI", "VRLLOG", "MAHSEAMLESS", "GATEWAY",
    # ── Hospitality & Tourism ─────────────────────────────────────────────────
    "INDHOTEL", "EIHOTEL", "CHALET", "LEMONTREE", "MAHINDHOLIDAY",
    "THOMASCOOK", "SOTL", "MHRIL", "EIHASSOC", "TAJGVK",
    # ── Agri & Food Processing ────────────────────────────────────────────────
    "UBL", "KRBL", "LTFOODS", "RUCHI", "GODREJAGRO",
    "BALRAMCHIN", "DWARIKESH", "TRIVENI ENG", "EID PARRY", "SHREERAMA",
]

# TTL values (seconds)
PRICE_TTL = 300       # 5 min — survives between poll cycles
INDICES_TTL = 180     # 3 min
BREADTH_TTL = 180     # 3 min

# Module-level state persisted across poll cycles
_cached_symbols: list[str] = []
_last_compute_time: float = 0.0
_poll_count: int = 0
_startup_done: bool = False
_consecutive_failures: int = 0


async def populate_universe_fallback() -> list[str]:
    """Populate both universe sets from the static fallback lists.

    nifty50  → 50 large-cap symbols
    nifty500 → full ~500-symbol static list (superseded by live NSE data once
               the poller fetches successfully)
    """
    from app.services.redis_cache import get_redis

    redis = await get_redis()
    await redis.delete("universe:nifty50")
    await redis.sadd("universe:nifty50", *NIFTY_50_SYMBOLS)
    await redis.delete("universe:nifty500")
    await redis.sadd("universe:nifty500", *NIFTY_500_SYMBOLS)
    log.info(
        "Universe fallback loaded — nifty50=%d nifty500=%d",
        len(NIFTY_50_SYMBOLS),
        len(NIFTY_500_SYMBOLS),
    )
    return list(NIFTY_500_SYMBOLS)


async def _populate_universe(stock_data: list[dict]) -> list[str]:
    """Extract symbols from stock data and populate universe sets."""
    from app.services.redis_cache import get_redis

    redis = await get_redis()

    symbols: list[str] = []
    for stock in stock_data:
        symbol = stock.get("symbol", "")
        if symbol and symbol not in ("NIFTY 50", "NIFTY 500"):
            symbols.append(symbol)

    if symbols:
        await redis.delete("universe:nifty50")
        await redis.sadd("universe:nifty50", *symbols[:50])
        await redis.delete("universe:nifty500")
        await redis.sadd("universe:nifty500", *symbols)
        log.info("Populated universe sets with %d symbols from live data", len(symbols))

    return symbols


async def _populate_universe_from_symbols(symbols: list[str]) -> list[str]:
    """Populate universe sets directly from a list of symbols."""
    from app.services.redis_cache import get_redis

    redis = await get_redis()

    if symbols:
        await redis.delete("universe:nifty500")
        await redis.sadd("universe:nifty500", *symbols)
        # Keep nifty50 as the first 50 or from hardcoded list
        nifty50 = [s for s in symbols if s in set(NIFTY_50_SYMBOLS)]
        if nifty50:
            await redis.delete("universe:nifty50")
            await redis.sadd("universe:nifty50", *nifty50)
        log.info("Universe sets updated: nifty500=%d, nifty50=%d", len(symbols), len(nifty50))

    return symbols


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
    global _cached_symbols, _last_compute_time, _poll_count, _startup_done, _consecutive_failures

    from app.services.nse_fallback import NSEClient
    from app.services.redis_cache import get_redis, set_json

    client = NSEClient()
    log.info("NSE poller started")

    # Immediately populate universe with fallback symbols so screener works from the start
    if not _cached_symbols:
        try:
            _cached_symbols = await populate_universe_fallback()
        except Exception as e:
            log.error("Failed to populate fallback universe: %s", e)

    while True:
        _poll_count += 1
        try:
            redis = await get_redis()

            # ----------------------------------------------------------
            # 1. Fetch all indices
            # ----------------------------------------------------------
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

                    if name == "NIFTY 50":
                        breadth["advances"] = idx.get("advances", 0) or 0
                        breadth["declines"] = idx.get("declines", 0) or 0
                        breadth["unchanged"] = idx.get("unchanged", 0) or 0

                if indices_list:
                    await set_json("market:indices", indices_list, ttl=INDICES_TTL)
                    log.debug("Stored %d indices", len(indices_list))

                breadth["total"] = breadth["advances"] + breadth["declines"] + breadth["unchanged"]
                breadth["advance_decline_ratio"] = round(breadth["advances"] / max(breadth["declines"], 1), 2)
                await set_json("market:breadth", breadth, ttl=BREADTH_TTL)

            except Exception as e:
                log.warning("Failed to fetch indices: %s", e)

            # ----------------------------------------------------------
            # 2. Fetch Nifty 500 stock quotes for live prices
            #    NSE limits each index query to its constituents, so we
            #    fetch NIFTY 500 which returns all ~500 stocks in one call.
            #    We also fetch NIFTY 50 separately to tag nifty50 members.
            # ----------------------------------------------------------
            fetch_ok = False
            try:
                http = await client._ensure_client()

                # Fetch NIFTY 500 (covers all 500 stocks)
                resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 500"})
                if resp.status_code == 403:
                    await client._refresh_cookies()
                    resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 500"})

                if resp.status_code == 200:
                    stock_data = resp.json().get("data", [])
                    all_symbols: list[str] = []
                    ts = datetime.now(timezone.utc).isoformat()

                    for stock in stock_data:
                        symbol = stock.get("symbol", "")
                        if not symbol or symbol in ("NIFTY 500", "NIFTY 50"):
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
                            "timestamp": ts,
                        }
                        await set_json(f"price:{symbol}", price_data, ttl=PRICE_TTL)
                        await redis.publish("price_updates", json.dumps(price_data))
                        all_symbols.append(symbol)

                    log.info("Stored + published prices for %d Nifty 500 stocks", len(all_symbols))
                    fetch_ok = True
                    _consecutive_failures = 0

                    # Update universe with live data
                    if all_symbols:
                        _cached_symbols = await _populate_universe_from_symbols(all_symbols)
                else:
                    log.warning("NSE NIFTY 500 returned status %d, falling back to NIFTY 50", resp.status_code)
                    # Fallback: try NIFTY 50 if 500 fails
                    resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 50"})
                    if resp.status_code == 403:
                        await client._refresh_cookies()
                        resp = await http.get("/api/equity-stockIndices", params={"index": "NIFTY 50"})
                    if resp.status_code == 200:
                        stock_data = resp.json().get("data", [])
                        ts = datetime.now(timezone.utc).isoformat()
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
                                "timestamp": ts,
                            }
                            await set_json(f"price:{symbol}", price_data, ttl=PRICE_TTL)
                            await redis.publish("price_updates", json.dumps(price_data))
                        log.info("Fallback: stored prices for %d Nifty 50 stocks", len(stock_data))
                        fetch_ok = True
                        _consecutive_failures = 0

            except Exception as e:
                log.warning("Failed to fetch stock prices: %s", e)

            if not fetch_ok:
                _consecutive_failures += 1
                if _consecutive_failures >= 3:
                    log.error(
                        "NSE fetch failed %d consecutive times — data may be stale",
                        _consecutive_failures,
                    )

            # ----------------------------------------------------------
            # 3. Trigger indicator compute
            # ----------------------------------------------------------
            # On first successful cycle OR every COMPUTE_INTERVAL
            now = time.monotonic()
            if _cached_symbols and (
                not _startup_done
                or (now - _last_compute_time) >= COMPUTE_INTERVAL
            ):
                _startup_done = True
                _last_compute_time = now
                asyncio.create_task(
                    _run_bulk_compute(_cached_symbols),
                    name="bulk_compute_periodic",
                )

            # ----------------------------------------------------------
            # 4. Fetch trending stocks from Indian API (every other cycle = ~60s)
            # ----------------------------------------------------------
            if _poll_count % 2 == 0:
                asyncio.create_task(
                    _fetch_and_store_trending(),
                    name="fetch_trending",
                )

        except Exception as e:
            log.error("NSE poller error: %s", e)
            _consecutive_failures += 1

        # Adaptive backoff: double the sleep time for each consecutive failure
        # (capped at 5 minutes) so a broken NSE session doesn't hammer the server.
        if _consecutive_failures == 0:
            sleep_time = POLL_INTERVAL
        else:
            sleep_time = min(POLL_INTERVAL * (2 ** min(_consecutive_failures - 1, 4)), 300)
            log.info("NSE poller backing off: sleeping %ds (failures=%d)", sleep_time, _consecutive_failures)

        await asyncio.sleep(sleep_time)

"""Market-open orchestrator -- runs daily at ~08:00 IST before the bell."""

from __future__ import annotations

import structlog

from app.services.upstox_auth import is_token_valid
from app.services.upstox_instruments import (
    download_instruments,
    parse_instruments,
    refresh_universe_sets,
    sync_to_redis,
)

log = structlog.get_logger(__name__)


async def run_daily_setup() -> None:
    """Execute the full pre-market setup sequence.

    Steps
    -----
    1. Download and sync the Upstox instrument CSV.
    2. Refresh ``universe:nifty50`` / ``universe:nifty500`` Redis sets.
    3. Verify the Upstox access token is present and valid.
    4. Pre-warm Redis caches (LTP maps, universe sets already done above).

    This function is designed to be called by APScheduler or a similar
    scheduler at 08:00 IST each trading day.
    """
    log.info("daily_setup_started")

    # 1. Instruments ---------------------------------------------------------
    try:
        csv_data = await download_instruments()
        symbol_to_key, key_to_symbol = parse_instruments(csv_data)
        await sync_to_redis(symbol_to_key, key_to_symbol)
        log.info("daily_setup_instruments_done", count=len(symbol_to_key))
    except Exception:
        log.exception("daily_setup_instruments_failed")

    # 2. Universe sets -------------------------------------------------------
    try:
        await refresh_universe_sets()
        log.info("daily_setup_universe_done")
    except Exception:
        log.exception("daily_setup_universe_failed")

    # 3. Token check ---------------------------------------------------------
    try:
        valid = await is_token_valid()
        if valid:
            log.info("daily_setup_token_valid")
        else:
            log.warning(
                "daily_setup_token_missing",
                hint="User must re-authenticate via /auth/upstox/login before market open",
            )
    except Exception:
        log.exception("daily_setup_token_check_failed")

    # 4. Pre-warm (universe + instrument maps already cached above) ----------
    log.info("daily_setup_complete")

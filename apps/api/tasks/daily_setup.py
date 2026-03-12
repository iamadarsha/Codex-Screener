from __future__ import annotations

import logging
from typing import cast

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.errors import BreakoutScanError
from data.nse_fallback import is_fallback_active
from data.upstox_auth import (
    UpstoxAuthError,
    UpstoxTokenMissingError,
    prepare_login,
    refresh_cached_token,
)
from data.upstox_instruments import InstrumentSyncError, sync_instruments_to_redis
from data.upstox_streamer import UpstoxStreamerError, get_streamer_manager

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/tasks/daily-setup", tags=["daily-setup"])


class DailySetupError(BreakoutScanError):
    """Raised when scheduled market-setup tasks cannot complete."""


class DailySetupService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone=settings.market_timezone)
        self.started = False

    async def start(self) -> None:
        if self.started:
            return

        try:
            self.scheduler.add_job(
                self.run_instrument_sync,
                CronTrigger(hour=8, minute=0, timezone=settings.market_timezone),
                id="instrument-sync",
                replace_existing=True,
            )
            self.scheduler.add_job(
                self.refresh_token_or_request_login,
                CronTrigger(hour=8, minute=45, timezone=settings.market_timezone),
                id="token-refresh",
                replace_existing=True,
            )
            self.scheduler.add_job(
                self.start_market_stream,
                CronTrigger(hour=9, minute=0, timezone=settings.market_timezone),
                id="market-open-stream",
                replace_existing=True,
            )
            self.scheduler.start()
            self.started = True
        except Exception as error:
            raise DailySetupError("Unable to start the daily setup scheduler.") from error

    async def stop(self) -> None:
        if not self.started:
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.started = False
        except Exception as error:
            raise DailySetupError("Unable to stop the daily setup scheduler.") from error

    async def run_instrument_sync(self) -> dict[str, object]:
        try:
            summary = await sync_instruments_to_redis()
            return cast(dict[str, object], summary.to_redis_mapping())
        except InstrumentSyncError:
            raise
        except Exception as error:
            raise DailySetupError("Unexpected error while syncing instruments.") from error

    async def refresh_token_or_request_login(self) -> dict[str, object]:
        try:
            result = await refresh_cached_token()
            return {
                "status": "validated",
                "authorized_feed_uri": result["authorized_feed_uri"],
            }
        except UpstoxTokenMissingError:
            login_payload = await prepare_login()
            return {
                "status": "manual_login_required",
                "authorize_url": login_payload["authorize_url"],
                "redirect_uri": login_payload["redirect_uri"],
            }
        except UpstoxAuthError as error:
            login_payload = await prepare_login()
            return {
                "status": "manual_login_required",
                "reason": str(error),
                "authorize_url": login_payload["authorize_url"],
                "redirect_uri": login_payload["redirect_uri"],
            }
        except Exception as error:
            raise DailySetupError("Unexpected error while validating the Upstox token.") from error

    async def start_market_stream(self) -> dict[str, object]:
        streamer = get_streamer_manager()
        try:
            return await streamer.start()
        except (UpstoxAuthError, InstrumentSyncError, UpstoxStreamerError):
            raise
        except Exception as error:
            raise DailySetupError("Unexpected error while starting the market stream.") from error

    async def run_all(self) -> dict[str, object]:
        instrument_result = await self.run_instrument_sync()
        token_result = await self.refresh_token_or_request_login()

        if token_result.get("status") == "validated":
            stream_result = await self.start_market_stream()
        else:
            stream_result = {"status": "skipped_until_manual_login"}

        return {
            "instruments": instrument_result,
            "token": token_result,
            "streamer": stream_result,
            "fallback_active": await is_fallback_active(),
        }

    async def status(self) -> dict[str, object]:
        streamer = get_streamer_manager()
        jobs = sorted(self.scheduler.get_jobs(), key=lambda job: job.id)
        return {
            "scheduler_started": self.started,
            "jobs": [
                {
                    "id": cast(str, getattr(job, "id")),
                    "next_run_time": str(getattr(job, "next_run_time")),
                }
                for job in jobs
            ],
            "streamer_running": streamer.running,
            "fallback_active": await is_fallback_active(),
        }


_service: DailySetupService | None = None


def get_daily_setup_service() -> DailySetupService:
    global _service

    if _service is None:
        _service = DailySetupService()

    return _service


@router.post("/run")
async def run_daily_setup() -> dict[str, object]:
    service = get_daily_setup_service()
    try:
        return await service.run_all()
    except (DailySetupError, InstrumentSyncError, UpstoxAuthError, UpstoxStreamerError) as error:
        logger.exception("daily setup run failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/sync-instruments")
async def run_daily_instrument_sync() -> dict[str, object]:
    service = get_daily_setup_service()
    try:
        return await service.run_instrument_sync()
    except (DailySetupError, InstrumentSyncError) as error:
        logger.exception("daily instrument sync failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/refresh-token")
async def run_daily_token_refresh() -> dict[str, object]:
    service = get_daily_setup_service()
    try:
        return await service.refresh_token_or_request_login()
    except (DailySetupError, UpstoxAuthError) as error:
        logger.exception("daily token refresh failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/start-stream")
async def run_daily_market_stream() -> dict[str, object]:
    service = get_daily_setup_service()
    try:
        return await service.start_market_stream()
    except (DailySetupError, InstrumentSyncError, UpstoxAuthError, UpstoxStreamerError) as error:
        logger.exception("daily market stream start failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/status")
async def daily_setup_status() -> dict[str, object]:
    service = get_daily_setup_service()
    try:
        return await service.status()
    except DailySetupError as error:
        logger.exception("daily setup status failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

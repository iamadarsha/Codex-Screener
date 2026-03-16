from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: UUID
    user_id: UUID
    symbol: str
    scan_id: UUID | None = None
    notify_email: bool = False
    notify_push: bool = False
    notify_telegram: bool = False
    frequency: str
    is_active: bool = True

    model_config = {"from_attributes": True}


class AlertCreateRequest(BaseModel):
    symbol: str
    scan_id: str | None = None
    notify_email: bool = False
    notify_push: bool = False
    notify_telegram: bool = False
    frequency: str = "once"  # "once", "every_time", "daily_digest"


class AlertUpdateRequest(BaseModel):
    notify_email: bool | None = None
    notify_push: bool | None = None
    notify_telegram: bool | None = None
    frequency: str | None = None
    is_active: bool | None = None


class AlertHistoryOut(BaseModel):
    id: UUID
    alert_id: UUID
    symbol: str
    trigger_price: float
    conditions_met: list[dict[str, object]]
    triggered_at: datetime

    model_config = {"from_attributes": True}

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.alert import Alert
from app.db.models.alert_history import AlertHistory
from app.schemas.alert import (
    AlertCreateRequest,
    AlertHistoryOut,
    AlertOut,
    AlertUpdateRequest,
)
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    user_id: str = Query(..., description="User ID"),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List the user's alerts."""
    uid = uuid.UUID(user_id)
    query = select(Alert).where(Alert.user_id == uid)
    if active_only:
        query = query.where(Alert.is_active.is_(True))
    query = query.order_by(Alert.symbol)
    rows = (await db.execute(query)).scalars().all()
    return [AlertOut.model_validate(r) for r in rows]


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(
    req: AlertCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert."""
    alert = Alert(
        user_id=uuid.UUID(req.user_id),
        symbol=req.symbol.upper(),
        scan_id=uuid.UUID(req.scan_id) if req.scan_id else None,
        notify_email=req.notify_email,
        notify_push=req.notify_push,
        notify_telegram=req.notify_telegram,
        frequency=req.frequency,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertOut)
async def update_alert(
    alert_id: str,
    req: AlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing alert."""
    aid = uuid.UUID(alert_id)
    alert = (
        await db.execute(select(Alert).where(Alert.id == aid))
    ).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = req.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Alert).where(Alert.id == aid).values(**update_data)
        )
        await db.commit()
        await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.delete("/{alert_id}", response_model=SuccessResponse)
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    aid = uuid.UUID(alert_id)
    result = await db.execute(delete(Alert).where(Alert.id == aid))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return SuccessResponse(message="Alert deleted")


@router.get("/history", response_model=list[AlertHistoryOut])
async def alert_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get alert trigger history for a user."""
    uid = uuid.UUID(user_id)
    query = (
        select(AlertHistory)
        .join(Alert, AlertHistory.alert_id == Alert.id)
        .where(Alert.user_id == uid)
        .order_by(AlertHistory.triggered_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(query)).scalars().all()
    return [AlertHistoryOut.model_validate(r) for r in rows]

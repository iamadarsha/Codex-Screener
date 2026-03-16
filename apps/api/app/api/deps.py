from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Optional

import jwt
from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session

logger = logging.getLogger(__name__)


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_session():
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract and verify user_id from Supabase JWT.

    Returns the user UUID string from the token's ``sub`` claim.
    """
    settings = get_settings()

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization[7:]

    if not settings.supabase_jwt_secret:
        logger.warning("SUPABASE_JWT_SECRET not configured — rejecting request")
        raise HTTPException(status_code=500, detail="Auth not configured")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Like get_current_user but returns None for unauthenticated requests."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.schemas.auth import AuthStatus, LoginURLResponse, TokenResponse
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_model=LoginURLResponse)
async def login(
    redirect: bool = Query(False, description="If true, redirect to Upstox login page"),
):
    """Return the Upstox OAuth login URL (or redirect to it)."""
    try:
        from app.services.upstox_auth import get_login_url

        url, state = await get_login_url()
    except Exception as exc:
        logger.exception("Failed to generate login URL")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if redirect:
        return RedirectResponse(url=url)
    return LoginURLResponse(url=url, state=state)


@router.get("/upstox/callback", response_model=TokenResponse)
async def upstox_callback(
    code: str = Query(..., description="Authorization code from Upstox"),
    state: str = Query("", description="OAuth state parameter"),
):
    """Exchange the Upstox authorization code for an access token."""
    try:
        from app.services.upstox_auth import exchange_code, store_token

        token_data = await exchange_code(code)
        await store_token(token_data)
        return TokenResponse(
            ok=True,
            message="authenticated",
            access_token=token_data.get("access_token"),
            expires_in=token_data.get("expires_in"),
        )
    except Exception as exc:
        logger.exception("Token exchange failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status", response_model=AuthStatus)
async def auth_status():
    """Check whether a valid Upstox token exists."""
    try:
        from app.services.upstox_auth import get_token

        token = await get_token()
        if token:
            return AuthStatus(
                authenticated=True,
                broker="upstox",
                expires_at=token.get("expires_at"),
            )
        return AuthStatus(authenticated=False)
    except Exception:
        return AuthStatus(authenticated=False)


@router.post("/logout", response_model=SuccessResponse)
async def logout():
    """Clear the stored Upstox token."""
    try:
        from app.services.upstox_auth import store_token

        await store_token({})
    except Exception as exc:
        logger.exception("Logout failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SuccessResponse(message="logged out")

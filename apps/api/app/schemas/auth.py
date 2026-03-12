from __future__ import annotations

from pydantic import BaseModel


class LoginURLResponse(BaseModel):
    url: str
    state: str | None = None


class TokenResponse(BaseModel):
    ok: bool = True
    message: str = "authenticated"
    access_token: str | None = None
    expires_in: int | None = None


class AuthStatus(BaseModel):
    authenticated: bool
    broker: str = "upstox"
    expires_at: str | None = None

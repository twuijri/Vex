"""
Vex - Dashboard Authentication
Cookie-based auth using itsdangerous signed tokens.
Password read from DASHBOARD_PASSWORD env var (default: "admin").
"""
import os
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeSerializer, BadSignature

_SECRET_KEY = os.getenv("SECRET_KEY", "vex-dashboard-secret-key-change-me")
_serializer = URLSafeSerializer(_SECRET_KEY, salt="vex-auth")
_COOKIE_NAME = "vex_auth"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_dashboard_password() -> str:
    return os.getenv("DASHBOARD_PASSWORD", "admin")


def create_auth_token() -> str:
    """Create a signed auth token."""
    return _serializer.dumps({"v": 1})


def verify_auth_token(token: str) -> bool:
    """Verify a signed auth token."""
    try:
        data = _serializer.loads(token)
        return data.get("v") == 1
    except BadSignature:
        return False


def set_auth_cookie(response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=_COOKIE_MAX_AGE,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/")


class RequireAuth:
    """FastAPI dependency — redirects to login if not authenticated."""
    async def __call__(self, vex_auth: Optional[str] = Cookie(default=None)):
        if not vex_auth or not verify_auth_token(vex_auth):
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/dashboard/login"},
            )
        return True


require_auth = RequireAuth()

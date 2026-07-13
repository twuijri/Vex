"""
Vex - Dashboard Authentication
Starlette middleware-based auth using itsdangerous signed cookies.
Password read from DASHBOARD_PASSWORD env var (default: "admin").
"""
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from itsdangerous import URLSafeSerializer, BadSignature

_SECRET_KEY = os.getenv("SECRET_KEY", "vex-dashboard-secret-key-change-me")
_serializer = URLSafeSerializer(_SECRET_KEY, salt="vex-auth")
_COOKIE_NAME = "vex_auth"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Routes that don't require auth
_PUBLIC_PATHS = {"/dashboard/login", "/api/login", "/api/logout"}


def get_dashboard_password() -> str:
    return os.getenv("DASHBOARD_PASSWORD", "admin")


def create_auth_token() -> str:
    return _serializer.dumps({"v": 1})


def verify_auth_token(token: str) -> bool:
    try:
        data = _serializer.loads(token)
        return data.get("v") == 1
    except Exception:
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


class DashboardAuthMiddleware(BaseHTTPMiddleware):
    """Protect /api/* (401 JSON) — the SPA itself is public and shows its
    own login screen when /api/me returns 401."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only guard the JSON API — the SPA shell + static assets are public
        if not path.startswith("/api"):
            return await call_next(request)

        if path in _PUBLIC_PATHS:
            return await call_next(request)

        token = request.cookies.get(_COOKIE_NAME, "")
        if not verify_auth_token(token):
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

        return await call_next(request)

"""Bearer token auth.

Compares the `Authorization: Bearer <token>` header against the set of
tokens in API_KEYS. If API_KEYS is empty, auth is disabled (dev only —
do not deploy publicly without setting it).

When you later move to OAuth 2.1, replace this with a middleware that
validates JWTs against your authorization server's JWKS.
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import get_settings

log = logging.getLogger(__name__)


def bearer_auth_middleware(app: ASGIApp) -> ASGIApp:
    settings = get_settings()
    tokens = settings.allowed_tokens()

    if not tokens:
        log.warning("API_KEYS is empty — bearer auth DISABLED (dev mode)")
        return app

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        # Allow unauthenticated discovery endpoints
        path = scope.get("path", "")
        if path in {"/healthz", "/.well-known/oauth-protected-resource"}:
            await app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode("latin-1")
        if not auth.lower().startswith("bearer "):
            await _unauthorized(send, "Missing bearer token")
            return
        token = auth.split(" ", 1)[1].strip()
        if token not in tokens:
            await _unauthorized(send, "Invalid bearer token")
            return

        await app(scope, receive, send)

    return middleware


async def _unauthorized(send: Send, detail: str) -> None:
    response = JSONResponse(
        {"error": "unauthorized", "detail": detail},
        status_code=401,
        headers={"WWW-Authenticate": 'Bearer realm="appstore-intel"'},
    )
    await response({"type": "http"}, _empty_receive, send)  # type: ignore[arg-type]


async def _empty_receive() -> dict:
    return {"type": "http.request", "body": b"", "more_body": False}


# Re-export for type checkers
AsgiMiddleware = Callable[[ASGIApp], ASGIApp]
_ = Awaitable  # silence "imported but unused" linters if any

"""FastMCP server entrypoint.

Exposes app store intelligence tools over Streamable HTTP.
Run: python -m appstore_intel_mcp
"""
from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .auth.bearer import bearer_auth_middleware
from .tools import metadata, reviews, search

log = logging.getLogger(__name__)

mcp = FastMCP(
    name="appstore-intel",
    instructions=(
        "Query Google Play and the Apple App Store for app metadata, "
        "reviews, and competitive intelligence. Use search_apps to find "
        "an app's identifier, then call get_app_metadata or get_reviews."
    ),
)

# Register tools.
search.register(mcp)
metadata.register(mcp)
reviews.register(mcp)


def _build_http_app():
    """Build the Streamable HTTP ASGI app with DNS rebinding protection
    disabled. HF proxies through a public hostname which FastMCP's default
    Host check rejects with 421. Bearer auth remains the real security
    boundary, so disabling the host check is safe here.
    """
    try:
        from mcp.server.transport_security import TransportSecuritySettings
        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
        return mcp.streamable_http_app(transport_security=security)
    except (ImportError, TypeError):
        log.warning("transport_security not supported in this SDK; using default")
        return mcp.streamable_http_app()


def healthz_middleware(app: ASGIApp) -> ASGIApp:
    """Answer GET /healthz with 200 OK before delegating to FastMCP.

    FastMCP doesn't mount a health endpoint, but the Dockerfile HEALTHCHECK
    (and HF Spaces' liveness probe) call /healthz. Without this, containers
    are marked unhealthy and restarted.
    """
    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path") == "/healthz":
            response = PlainTextResponse("ok")
            await response(scope, receive, send)
            return
        await app(scope, receive, send)

    return middleware


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    app = _build_http_app()
    app = bearer_auth_middleware(app)
    app = healthz_middleware(app)

    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "7860")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
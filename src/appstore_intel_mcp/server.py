"""FastMCP server entrypoint.

Exposes app store intelligence tools over Streamable HTTP.
Run: python -m appstore_intel_mcp
"""
from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

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

# Register tools. Each module exposes a `register(mcp)` function so the
# server module stays a thin composition root.
search.register(mcp)
metadata.register(mcp)
reviews.register(mcp)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    app = mcp.streamable_http_app()

    # HF Spaces proxies requests; the Host header is the public hostname.
    # Wrap with TrustedHostMiddleware to allow it through FastMCP's checks.
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    
    allowed = os.getenv(
        "ALLOWED_HOSTS",
        "gautam84-appstore-intel-mcp.hf.space,localhost,127.0.0.1,0.0.0.0",
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[h.strip() for h in allowed.split(",") if h.strip()],
    )

    app = bearer_auth_middleware(app)

    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
if __name__ == "__main__":
    main()

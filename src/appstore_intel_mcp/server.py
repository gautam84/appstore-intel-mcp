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

# FastMCP enables DNS rebinding protection by default, which restricts
# the Host header to localhost. HF Spaces proxies requests through their
# public hostname, so the protection must be disabled here. Bearer auth
# remains the real security boundary.
try:
    mcp.settings.streamable_http_dns_rebinding_protection = False
except AttributeError:
    # Older/newer SDK versions: setting may live elsewhere. Fall back to
    # the env var that FastMCP also reads on init.
    os.environ.setdefault(
        "FASTMCP_STREAMABLE_HTTP_DNS_REBINDING_PROTECTION", "false"
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
    app = bearer_auth_middleware(app)

    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "7860")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
---
title: Appstore Intel MCP
emoji: 📱
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# appstore-intel-mcp

A remote MCP server that gives AI agents structured access to **Google Play** and the **Apple App Store** — search apps, fetch metadata, pull reviews. OAuth-protected, Streamable HTTP, deployable in minutes.

> Status: early. v0.1 ships three tools. v0.2 adds review analysis, competitor discovery, and release-tracking webhooks.

## Tools

| Tool | Purpose |
|---|---|
| `search_apps` | Free-text search across a storefront, returns identifiers |
| `get_app_metadata` | Full listing for one app (title, version, rating, screenshots, …) |
| `get_reviews` | Paginated reviews, sortable by recency / rating / helpfulness |

## Quickstart (local)

```bash
git clone https://github.com/<you>/appstore-intel-mcp
cd appstore-intel-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env             # leave API_KEYS empty for dev
python -m appstore_intel_mcp     # serves on http://localhost:8000/mcp
```

Connect from Claude Code:

```bash
claude mcp add --transport http appstore-intel http://localhost:8000/mcp
```

## Deploy to Koyeb

```bash
koyeb secret create api_keys --value "$(openssl rand -hex 32)"
koyeb app create -f koyeb.yaml
```

Then in Claude.ai → Settings → Connectors → Add custom connector, paste `https://<your-app>.koyeb.app/mcp` and the bearer token.

## Architecture

```
mcp client ──► Streamable HTTP ──► FastMCP
                                     │
                  ┌──────────────────┼──────────────────┐
                  ▼                  ▼                  ▼
            tools/search     tools/metadata      tools/reviews
                  │                  │                  │
                  └──────► registry ─┴──────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
       providers/google_play        providers/app_store
       (google-play-scraper)        (iTunes Search + RSS)
```

All tool calls go through an in-memory TTL cache (`cache.py`) so the same app metadata isn't re-scraped every request.

## Roadmap

- [ ] `analyze_reviews` — theme extraction + sentiment using a local embedding model
- [ ] `compare_apps` — side-by-side matrix
- [ ] `find_competitors` — category + embedding-based similarity
- [ ] Release/rating-drop webhooks
- [ ] Full OAuth 2.1 + PKCE flow for multi-tenant hosting
- [ ] Redis cache for horizontal scale

## License

MIT.

#!/usr/bin/env bash
# Quick local check: boot the server, hit healthz, kill it.
set -euo pipefail

export API_KEYS="${API_KEYS:-dev-token}"
export LOG_LEVEL=DEBUG

python -m appstore_intel_mcp &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

sleep 2
echo "--- healthz ---"
curl -fsS http://localhost:8000/healthz || true
echo
echo "--- unauthorized call (expected 401) ---"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/mcp
echo "--- authorized call ---"
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer dev-token" http://localhost:8000/mcp

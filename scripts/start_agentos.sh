#!/usr/bin/env bash
# Start AI Dropshipping Agency AgentOS (REST + MCP /mcp for Hermes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
PORT="${AGENCY_PORT:-7777}"
echo "Starting AgentOS on :$PORT (MCP at http://127.0.0.1:${PORT}/mcp)"
exec python -m app.main

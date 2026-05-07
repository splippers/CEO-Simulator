#!/usr/bin/env bash
# Run the opencode worker alongside central (host-side, no Docker).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
set -a
[[ -f .env ]] && source .env
set +a
export CENTRAL_URL="${CENTRAL_URL:-http://127.0.0.1:${CEO_CENTRAL_PORT:-8080}}"
export WORKER_ID="${WORKER_ID:-opencode-worker}"
export OPENCODE_MODEL="${OPENCODE_MODEL:-opencode/big-pickle}"
export POLL_INTERVAL="${POLL_INTERVAL:-3}"
export OPENCODE_TIMEOUT="${OPENCODE_TIMEOUT:-120}"
exec python3 -u "$ROOT/harness/worker.py"

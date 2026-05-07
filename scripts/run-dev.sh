#!/usr/bin/env bash
# Local central without Docker: serves on CEO_CENTRAL_PORT (default 8080).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -f .env ]] && [[ -f .env.example ]]; then
  echo "Tip: cp .env.example .env and set NERVECENTRE_PUBLIC_ORIGIN for Marvin." >&2
fi
set -a
[[ -f .env ]] && source .env
set +a
export PORT="${CEO_CENTRAL_PORT:-8080}"
export PYTHONPATH="$ROOT"
exec python3 -u "$ROOT/harness/central.py"

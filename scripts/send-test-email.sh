#!/usr/bin/env bash
# Send a test email to a staff role in the CEO-Simulator mailserver.
# Usage: ./scripts/send-test-email.sh [role] [subject]
#   Pipe a custom body: echo "your message" | ./scripts/send-test-email.sh cto
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set -a
[[ -f .env ]] && source .env
set +a

exec python3 -u "$ROOT/harness/test_mail.py" "$@"

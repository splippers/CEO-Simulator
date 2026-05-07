#!/usr/bin/env bash
# Create staff mail accounts in docker-mailserver.
# Run after `docker compose up -d` when the mailserver is running.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set -a
[[ -f .env ]] && source .env
set +a

DOMAIN="${DOMAIN:-biab.local}"
CONTAINER="ceo-mailserver"
PASS="${CEO_MAIL_PASS:-ceo123}"

# Map of local-part → display name
declare -A ACCOUNTS=(
  [ceo]="Aragorn CEO"
  [cto]="Gandalf CTO"
  [dev]="Frodo Dev"
  [ops]="Samwise Ops"
  [support]="Pippin Support"
)

echo "==> Setting up mail accounts for ${DOMAIN}"
echo "    password: ${PASS}"

for localpart in "${!ACCOUNTS[@]}"; do
  email="${localpart}@${DOMAIN}"
  display="${ACCOUNTS[$localpart]}"
  echo -n "    ${email} (${display}) ... "
  if docker exec "${CONTAINER}" setup email add "${email}" "${PASS}" 2>&1; then
    echo "OK"
  else
    echo "SKIP (may already exist)"
  fi
done

echo "==> Done. Accounts:"
for localpart in "${!ACCOUNTS[@]}"; do
  echo "    ${localpart}@${DOMAIN} / ${PASS}"
done

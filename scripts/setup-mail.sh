#!/usr/bin/env bash
# Create staff accounts in Samba AD for mail auth.
# Run after `docker compose up -d` when samba-ad is running.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set -a
[[ -f .env ]] && source .env
set +a

SAMBA_ADMIN_PASS="${SAMBA_ADMIN_PASS}"
AD_CONTAINER="ceo-samba-ad"
UPN_SUFFIX="${DOMAIN:-project6x7.com}"

# Staff roles: local-part:display:password
declare -A ACCOUNTS=(
  [ceo]="Aragorn CEO:ceo123"
  [cto]="Gandalf CTO:cto123"
  [dev]="Frodo Dev:dev123"
  [ops]="Samwise Ops:ops123"
  [support]="Pippin Support:support123"
)

echo "==> Creating staff accounts in Samba AD (${UPN_SUFFIX})"

for localpart in "${!ACCOUNTS[@]}"; do
  IFS=':' read -r display pass <<< "${ACCOUNTS[$localpart]}"
  email="${localpart}@${UPN_SUFFIX}"
  given="${display%% *}"
  surname="${display#* }"

  echo -n "    ${email} (${display}) ... "

  if docker exec "${AD_CONTAINER}" samba-tool user show "${localpart}" &>/dev/null; then
    echo "ALREADY EXISTS"
  else
    docker exec "${AD_CONTAINER}" samba-tool user create \
      "${localpart}" "${pass}" \
      --display-name="${display}" \
      --mail-address="${email}" \
      --given-name="${given}" \
      --surname="${surname}" \
      --use-username-as-mail 2>&1 | head -1
    docker exec "${AD_CONTAINER}" samba-tool user setexpiry "${localpart}" --noexpiry
    echo "    OK"
  fi
done

echo "==> Done. Accounts:"
for localpart in "${!ACCOUNTS[@]}"; do
  echo "    IMAP/SMTP: ${localpart}@${UPN_SUFFIX}"
done

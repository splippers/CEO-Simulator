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
  [ceo]="Aragorn CEO:Ceo2026!"
  [cto]="Gandalf CTO:Cto2026!"
  [dev]="Frodo Dev:Dev2026!"
  [ops]="Samwise Ops:Ops2026!"
  [support]="Pippin Support:Support2026!"
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
      --mail-address="${email}" \
      --given-name="${given}" \
      --surname="${surname}" \
      --use-username-as-cn 2>&1 | head -1
    docker exec "${AD_CONTAINER}" samba-tool user setexpiry "${localpart}" --noexpiry
    echo "    OK"
  fi
done

echo "==> Done. Accounts:"
for localpart in "${!ACCOUNTS[@]}"; do
  echo "    IMAP/SMTP: ${localpart}@${UPN_SUFFIX}"
done

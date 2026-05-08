#!/usr/bin/env bash
# Stop and disable host services that conflict with CEO-Simulator Docker containers.
set -euo pipefail

SERVICES=(dovecot postfix nmbd smbd)

echo "==> Stopping and disabling host services:"
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo -n "    $svc ... "
        sudo systemctl stop "$svc"
        sudo systemctl disable "$svc"
        echo "STOPPED + DISABLED"
    else
        echo "    $svc ... not running"
    fi
done

echo ""
echo "==> Verifying ports 25, 143, 389, 445 are free:"
for port in 25 143 389 445 53 88; do
    if ss -tlnp "sport = :$port" 2>/dev/null | grep -q LISTEN; then
        echo "    WARNING: port $port still in use"
        ss -tlnp "sport = :$port" 2>/dev/null | head -3
    else
        echo "    port $port: FREE"
    fi
done

echo ""
echo "==> Done. Run 'docker compose up -d' to start the containerized stack."

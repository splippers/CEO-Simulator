#!/bin/bash
set -e

SAMBA_DOMAIN=${SAMBA_DOMAIN:-corp}
SAMBA_REALM=${SAMBA_REALM:-CORP.PROJECT6X7.COM}
SAMBA_ADMIN_PASS=${SAMBA_ADMIN_PASS:-$(tr -dc A-Za-z0-9 < /dev/urandom | head -c 20)}
SAMBA_DNS_FORWARDER=${SAMBA_DNS_FORWARDER:-1.1.1.1}

# Check for AD database (sam.ldb) to determine if already provisioned.
# The samba package installs a default smb.conf, so checking that alone is unreliable.
if [ ! -f /var/lib/samba/private/sam.ldb ]; then
    echo "=== Provisioning Samba AD domain ==="
    echo "Domain: $SAMBA_DOMAIN"
    echo "Realm:  $SAMBA_REALM"

    # Remove default smb.conf so provision creates a fresh one
    rm -f /etc/samba/smb.conf

    samba-tool domain provision \
        --domain="${SAMBA_DOMAIN}" \
        --realm="${SAMBA_REALM}" \
        --adminpass="${SAMBA_ADMIN_PASS}" \
        --dns-backend=SAMBA_INTERNAL \
        --server-role=dc \
        --use-rfc2307 \
        --function-level=2008_R2

    echo "=== Setting DNS forwarder ==="
    sed -i "s/^[[:space:]]*dns forwarder = .*/dns forwarder = ${SAMBA_DNS_FORWARDER}/" /etc/samba/smb.conf

    echo "=== AD Provisioning complete ==="
    echo "Admin password: $SAMBA_ADMIN_PASS"
else
    echo "=== Samba already provisioned, starting ==="
fi

mkdir -p /var/run/samba

echo "=== Starting Samba AD DC ==="
exec samba --foreground --no-process-group

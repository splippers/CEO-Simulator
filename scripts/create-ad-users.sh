#!/bin/bash
# Creates CEO Simulator staff accounts in Samba AD + assigns mail attributes.
# Run inside the samba-ad container: docker exec ceo-samba-ad /create-ad-users.sh
set -e

SAMBA_REALM=${SAMBA_REALM:-CORP.PROJECT6X7.COM}
SAMBA_ADMIN_PASS=${SAMBA_ADMIN_PASS:-$(< /etc/samba/smbpasswd 2>/dev/null || echo "")}
DOMAIN=${DOMAIN:-corp.project6x7.com}
UPN_SUFFIX=${UPN_SUFFIX:-project6x7.com}

# Staff roles: username, display name, mail local part, password
staff=(
    "ceo:Aragorn CEO:ceo:ceo123"
    "cto:Gandalf CTO:cto:cto123"
    "dev:Frodo Dev:dev:dev123"
    "ops:Samwise Ops:ops:ops123"
    "support:Pippin Support:support:support123"
)

for entry in "${staff[@]}"; do
    IFS=':' read -r uname display localpart pass <<< "$entry"
    mail="${localpart}@${UPN_SUFFIX}"
    upn="${localpart}@${UPN_SUFFIX}"

    if samba-tool user show "$uname" &>/dev/null; then
        echo "User $uname already exists, skipping"
    else
        echo "Creating user: $uname ($display) <$mail>"
        samba-tool user create "$uname" "$pass" \
            --display-name="$display" \
            --mail-address="$mail" \
            --given-name="$(echo $display | cut -d' ' -f1)" \
            --surname="$(echo $display | cut -d' ' -f2-)" \
            --userou="OU=Staff,OU=Users" \
            --use-username-as-mail

        samba-tool user setexpiry "$uname" --noexpiry
        echo "  OK: $mail"
    fi
done

echo ""
echo "=== Verifying LDAP users ==="
ldapsearch -H ldap://localhost -x \
    -b "cn=Users,dc=$(echo $SAMBA_REALM | tr '[:upper:]' '[:lower:]' | tr '.' ',dc=')" \
    -D "cn=Administrator,cn=Users,dc=$(echo $SAMBA_REALM | tr '[:upper:]' '[:lower:]' | tr '.' ',dc=')" \
    -w "$SAMBA_ADMIN_PASS" \
    -LLL "(&(objectClass=person)(mail=*))" dn mail 2>/dev/null

echo ""
echo "=== Staff accounts created ==="
echo "Connect Roundcube as any staff user:"
for entry in "${staff[@]}"; do
    IFS=':' read -r uname display localpart pass <<< "$entry"
    echo "  IMAP/SMTP: $localpart@${UPN_SUFFIX} / $pass"
done

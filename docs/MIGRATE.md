# Migration Guide: CEO-Simulator → Real Company

Every component in CEO-Simulator is chosen for a clean migration path.
You never build lock-in. You build operational muscle memory, then graduate to
Google Workspace and Cloud Compute with zero rewrite.

---

## 1. Email → Google Workspace

The core principle: **Maildir is Law**. All company mail lives in standard Maildir
format on a Docker volume. Migration is a single `imapsync` command per mailbox.

### Prerequisites

1. Google Workspace account with your domain (e.g. `yourcompany.com`)
2. IMAP enabled in Google Workspace Admin → Apps → Gmail → User settings
3. App Password created for each mailbox (Google Account → Security → App Passwords)
4. docker-mailserver is running and mail is accessible

### Migrate a single mailbox

```bash
# Install imapsync
sudo apt install imapsync

# Sync CEO mailbox
imapsync \
  --host1 localhost --user1 "ceo@biab.local"  --password1 "ceo123"  --port1 143 \
  --host2 imap.gmail.com --user2 "ceo@yourcompany.com" --password2 "gmail-app-password" --port2 993 --ssl2 \
  --automap --justlogin --nofoldersizes
```

### Migrate all staff mailboxes at once

```bash
#!/usr/bin/env bash
# migrate-to-gws.sh — sync all staff Maildirs to Google Workspace
DOMAIN_SRC="${DOMAIN:-biab.local}"
DOMAIN_DST="yourcompany.com"
PASS_SRC="${CEO_MAIL_PASS:-ceo123}"
HOST2="imap.gmail.com"

for USER in ceo cto dev ops support; do
  echo "==> Migrating ${USER}@${DOMAIN_SRC} → ${USER}@${DOMAIN_DST}"
  read -rsp "App password for ${USER}@${DOMAIN_DST}: " PASS_DST
  echo
  imapsync \
    --host1 localhost --user1 "${USER}@${DOMAIN_SRC}" --password1 "${PASS_SRC}" --port1 143 \
    --host2 "${HOST2}" --user2 "${USER}@${DOMAIN_DST}" --password2 "${PASS_DST}" --port2 993 --ssl2 \
    --automap --nofoldersizes --skipcrossfolders
done
```

### What migrates

| Data | Migrates? | Notes |
|---|---|---|
| Emails (all folders) | ✅ Full via imapsync | All Maildir folders map to Gmail labels |
| Sent mail | ✅ | Mapped to `[Gmail]/Sent Mail` |
| Drafts | ✅ | Mapped to `[Gmail]/Drafts` |
| Spam/Ham | ✅ | Mapped to `[Gmail]/Spam` |
| Trash | ✅ | Mapped to `[Gmail]/Trash` |
| Server-side filters (Sieve) | ❌ Manual | Rewrite as Gmail filters |
| Mail server config | ❌ Manual | Set up Google Workspace MX, SPF, DKIM, DMARC |

### Post-migration DNS changes

```bash
# 1. Add Google MX records to your DNS
# 2. Add Google's SPF include
# 3. Generate DKIM key in Google Workspace → Apps → Gmail → Authenticate Email
# 4. Set up DMARC policy
```

---

## 2. Contacts → Google Contacts

### Export from Roundcube

1. Log into Roundcube (http://your-server:8081)
2. Go to Address Book
3. Click Export → select LDIF or CSV format
4. Save the file

### Import to Google Workspace

1. Go to [Google Contacts](https://contacts.google.com)
2. Click Import → select your LDIF/CSV file
3. Verify contacts appear under "Other contacts" or a custom label

### Programmatic export (all address books)

```bash
# Roundcube stores contacts in the MySQL database
# Export all contacts per user:
docker exec ceo-roundcubedb mysql -u roundcube -p roundcube \
  -e "SELECT email, name, firstname, surname, birthday, phone, address, organization
      FROM contacts WHERE user_id = (SELECT user_id FROM users WHERE username = 'ceo@biab.local');"
```

---

## 3. Infrastructure → Google Cloud Compute

The entire stack is designed to run on a single Compute Engine VM or a cluster.

### Deploy on GCP Compute Engine

```bash
# 1. Create a VM
gcloud compute instances create ceo-simulator \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --tags=ceo-simulator \
  --network-interface=network-tier=PREMIUM

# 2. Open ports
gcloud compute firewall-rules create ceo-simulator-central \
  --allow tcp:8080,tcp:8081 \
  --target-tags=ceo-simulator

# 3. SSH and install Docker
gcloud compute ssh ceo-simulator -- "
  sudo apt update && sudo apt install -y docker.io docker-compose-v2
  sudo systemctl enable --now docker
  sudo usermod -aG docker \$USER
"

# 4. Clone and run
gcloud compute ssh ceo-simulator -- "
  git clone https://github.com/splippers/CEO-Simulator.git
  cd CEO-Simulator
  cp .env.example .env
  # Edit .env: set DOMAIN, NERVECENTRE_PUBLIC_ORIGIN, ROUNDCUBE_DES_KEY
  docker compose -f docker-compose.biab.yml up -d
"
```

### TLS with Cloud Load Balancer (production)

For production, put the stack behind a Google Cloud HTTPS Load Balancer:

```
GCP LB :443  ──→  central :8080  (CEO-Simulator API)
             ──→  roundcube :8081 (Roundcube webmail)
```

1. Reserve a static IP: `gcloud compute addresses create ceo-simulator-lb --global`
2. Create an SSL certificate: `gcloud compute ssl-certificates create ceo-simulator-cert --domains=mail.yourcompany.com`
3. Create a backend service pointing to your instance group
4. Create URL maps to route `/` → central, `/roundcube` → webmail (or use separate subdomains)

### Persistent data on GCP

The named Docker volumes (`mail-data`, `mail-state`, `biab-state`, `roundcubedb-data`)
are stored at `/var/lib/docker/volumes/` on the VM. For production:

1. **Option A: Persistent disk** — Create a larger persistent disk and bind-mount it
2. **Option B: Filestore** — NFS-backed storage for multi-VM setups
3. **Option C: Periodic backup** — `gcloud compute disks snapshot` the boot disk

```bash
# Backup mail data
docker run --rm -v mail-data:/source -v $(pwd)/backup:/dest \
  alpine tar czf /dest/mail-data-$(date +%Y%m%d).tar.gz -C /source .
```

---

## 4. DNS & Domain Transition

### During CEO-Simulator (sandbox)

```bash
# /etc/hosts on the host machine
127.0.0.1 biab.local mail.biab.local

# Test with:
swaks --to ceo@biab.local --server 127.0.0.1:25
```

### After migration to Google Workspace

| Record | Type | Value |
|---|---|---|
| `@` | MX | `aspmx.l.google.com.` (priority 1) |
| `@` | MX | `alt1.aspmx.l.google.com.` (priority 5) |
| `@` | MX | `alt2.aspmx.l.google.com.` (priority 5) |
| `@` | TXT | `"v=spf1 include:_spf.google.com ~all"` |
| `google._domainkey` | TXT | Google-provided DKIM key |
| `_dmarc` | TXT | `"v=DMARC1; p=quarantine; rua=mailto:postmaster@yourcompany.com"` |

---

## 5. Cloudflare Email Routing (Dynamic IP / No Port 25)

If you have a dynamic home IP and can't run port 25, Cloudflare Email Routing
(free) + a Cloudflare Worker (free) replaces the docker-mailserver inbound path
entirely. Mail lands at Cloudflare, your Worker forwards it via HTTP to your
home game server. No open SMTP port needed.

### Architecture

```
someone@yourdomain.com
         ↓
  Cloudflare MX (handles deliverability, spam filtering)
         ↓
  Cloudflare Email Routing → sends to Worker
         ↓
  Worker extracts (to, from, subject, body) + adds shared secret
         ↓
  POST /api/ingest/email (HTTP, port 8080)
         ↓
  Your home server (DynDNS / Cloudflare Tunnel)
         ↓
  central.py → enqueues job → opencode worker → result
```

### 5.1 Deploy the Worker

```bash
# 1. Install Wrangler
npm install -g wrangler

# 2. Go to the worker directory
cd cloudflare/

# 3. Set the home server address and shared secret
npx wrangler secret put HOME_HOST -- "your-dyndns.duckdns.org:8080"
npx wrangler secret put INGEST_SECRET -- "changeme"

# 4. Deploy
npx wrangler deploy
```

### 5.2 Configure Email Routing

1. Go to [Cloudflare Dashboard → Email → Email Routing](https://dash.cloudflare.com/?to=/:account/email/routing/overview)
2. Enable Email Routing for your domain
3. Under **Email Workers**, select the `ceo-simulator-ingest` worker
4. Set **Catch-all** action → **Send to Worker** (`ceo-simulator-ingest`)
5. Verify DNS: Cloudflare auto-adds MX records. No MX setup required.

### 5.3 Home server config

Add to `.env` on your home server:

```env
INGEST_SECRET=changeme
```

The worker sends role, raw email, and secret to `/api/ingest/email`. The endpoint
parses the raw email and enqueues a job. No docker-mailserver or port 25 needed
for inbound.

### 5.4 What this replaces

| Component | Replaced by |
|---|---|
| docker-mailserver (inbound) | Cloudflare Email Routing |
| Postfix (port 25) | Cloudflare MX |
| ingest.py (Maildir watcher) | Cloudflare Worker → HTTP |
| Port forwarding / ISP blocks | Nothing to forward |
| PTR / IP reputation | Cloudflare handles it |

The docker-mailserver is still useful for:
- Outbound SMTP (if you add a relay like SendGrid / Mailgun)
- IMAP access (Roundcube → mailserver)
- Local mail storage in Maildir format

But if you're purely in Mock Mode and don't need outbound, you can drop
docker-mailserver entirely and rely on Cloudflare + HTTP ingest.

### 5.5 No outbound email (AI Firewall)

Per the BIAB design, LLM agents never send email externally. The AI Firewall
means all outbound mail goes through a human. So you don't need outbound SMTP
at all during the simulation phase. Only when you graduate to Google Workspace
do you configure outbound — and by then you're on their infrastructure.

---

## 6. Architecture Migration Map

```
CEO-Simulator                        Google Workspace / Cloud
─────────────                        ─────────────────────────
Maildirs (Docker volume)     ──→     Gmail / Google Workspace
Roundcube (Docker)           ──→     Gmail web UI
Roundcube contacts (MySQL)   ──→     Google Contacts
Postfix (docker-mailserver)  ──→     Google Workspace SMTP
Dovecot (docker-mailserver)  ──→     Google Workspace IMAP
Sieve filters                ──→     Gmail filters (manual)
Self-signed TLS              ──→     Google-managed SSL certs
.env configuration           ──→     GCP Secret Manager / env vars
Docker volumes               ──→     GCP Persistent Disk / Filestore
Single Docker host           ──→     GCP Compute Engine + LB
```

Every component has a one-way door out. No data is trapped. The cost of migration
is `imapsync` and DNS propagation — measured in hours, not rewrites.

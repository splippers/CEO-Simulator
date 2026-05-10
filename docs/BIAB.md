# CEO-Simulator: Business-in-a-Box (BIAB)
**Version 0.1 | splippers/CEO-Simulator | MIT License**

## 1. Vision

**BIAB is a flight simulator for running a UK company.**

Before you hire, before you burn cash, before you sign contracts, you run the company.
The staff are LLMs. The servers are old ProDesks. The inboxes are real. The friction is real.
The risk is zero.

When you’re ready, you `imapsync` the Maildirs to Google Workspace, hire humans, and they slot into roles with 6 months of history already waiting. The AI gets relegated to assistant.

This is not a chatbot. This is operational muscle memory.

## 2. Core Principles

| Principle | Implementation | Why |
| --- | --- | --- |
| **Maildir is Law** | All company state lives in `/home/*/Maildir`. Not Notion, not Slack. | Handoff = `imapsync`. No “where are the docs” when you hire. |
| **AI Firewall** | LLMs never email external. They add `X-AI-Comment` then forward to human. | Zero legal/brand risk. You are always the signatory. |
| **Time is Budget** | Single Ollama daemon. SQLite priority queue. CEO=10 gets 60s CPU, Support=3 gets 32s. | Scarcity teaches triage. Feels like real management. |
| **ProDesk-Native** | Llama 3.1 8B Q4_K_M @ 3-6 tok/s. 1 model per 8GB RAM. | £0 inference. 30s delay = human-speed. You already own the tin. |
| **Migration is Trivial** | Standard Postfix+Dovecot. `migrate/to-google-workspace.md` = 5 commands. | No lock-in. You graduate to Gmail, not rewrite. |
| **Characters > Roles** | `ceo@` is Aragorn. `cto@` is Gandalf. From your IP. | Culture + retention. You maintain it because it’s yours. |
| **Extensible by Default** | Add role: `staffctl.py add`. Add box: `boxes` table. | Cluster scales from 1 ProDesk to 10 before you need k8s. |

## 3. Architecture: The Work Horse Cluster

```
Internet
   |
   v
[Postfix :25] → *@project6x7.com
   |
   v
/opt/harness/ingest.py
   |
   v
[Central: Flask :8080] ← SQLite: staff, queue, boxes
   | ↑
   | | /api/job
   +--------+------------------+
   | | |
[Worker@box1] [Worker@box2] [Worker@box3] → Ollama :11434
   |
   v
[/home/jonathan/Maildir/new] ← You
   |
   v
You reply from jonathan@project6x7.com
```
[Procmail]

**Component Roles:**

1. **Postfix**: Accepts mail for `project6x7.com`. No sending except from `jonathan@`. SPF/DKIM optional until you go external.
2. **Dovecot**: IMAP access to Maildirs. CEO-Simulator is also an email client.
3. **ingest.py**: Catches all `*@domain`, writes to `/tmp`, POSTs to Central queue.
4. **central.py**: Flask API + Vue dash. Owns SQLite. Shows load, handles priority, assigns jobs to boxes.
5. **worker.py**: Runs on each ProDesk. Long-polls `/api/job`, runs Ollama, writes `X-AI-Comment`, delivers to human Maildir.
6. **staffctl.py**: CLI to `enable/disable/prio/box/add` staff. Your `kubectl` for people.

## 4. UK Company Functions: Phased Rollout

BIAB ships with 5 roles. Add more as you need them. Each is a row in `staff` table.

| Phase | Role | Email | Model | Priority | UK Function |
| --- | --- | --- | --- |
| **0: Solo** | CEO | `ceo@` | Llama 3.1 8B | 10 | Strategy, investor mail, board |
| **0: Solo** | CTO | `cto@` | Llama 3.1 8B | 8 | Tech risk, architecture, FOG |
| **1: Ops** | Dev | `dev@` | Phi-3 Mini | 5 | Code triage, PRs, tickets |
| **1: Ops** | Ops | `ops@` | Phi-3 Mini | 5 | Servers, backups, outages |
| **1: Ops** | Support | `support@` | Phi-3 Mini | 3 | Inbound triage, KB lookup |
| **2: Growth** | Sales | `sales@` | Llama 3.1 8B | 7 | Lead qual, disabled pre-human |
| **2: Growth** | Finance | `finance@` | Phi-3 Mini | 6 | Invoice parse, Xero notes |
| **2: Growth** | HR | `hr@` | Phi-3 Mini | 4 | Policy lookup, holiday calc |
| **3: Compliance** | Legal | `legal@` | Llama 3.1 8B | 9 | Contract scan, Companies House |
| **3: Compliance** | DPO | `dpo@` | Phi-3 Mini | 7 | GDPR triage, SAR drafting |

**Rule**: AI roles start `enabled=0` if external risk exists. Sales/Legal only comment to you until human hired. Finance/HR never email external.

## 5. The Dashboard: Your CEO HUD

`http://prodesk-1:8080`

**Staff Load Panel**
```
Aragorn CEO | Queued: 4 | Avg: 42s | Prio: 10 [-][+] | Box: prodesk-1 | Drain
Frodo Dev | Queued:12 | Avg: 18s | Prio: 5 [-][+] | Box: prodesk-2 | Drain
```
Click `+` on CEO. Aragorn gets 64s timeout next job. You just “told team to prioritise board deck”.

**Box Farm Panel**
```
prodesk-1 | online | Load: 1.8 | Running: ceo@
prodesk-2 | online | Load: 0.2 | Running: dev@
prodesk-3 | offline
```
See `dev@` at 12 queued. Change `Box: prodesk-3` → `prodesk-2`. Worker-2 picks up queue. You just “spun up another office”.

This is the feel. Latency, backlog, rebalancing. Without payroll.

## 6. Extending the Cluster

### 6.1 Add a ProDesk
1. `git clone CEO-Simulator` on box-2
2. `docker compose up` worker only: comment out central in compose
3. `export CENTRAL=http://prodesk-1:8080` in worker.py
4. On dash: `INSERT INTO boxes VALUES ('prodesk-2','http://prodesk-2:11434',1)`
5. Use dash to set `box_affinity` for staff. Frodo now runs on box-2.

### 6.2 Add a Role
```bash
docker exec ceo-simulator /opt/harness/staffctl.py add \
  finance@project6x7.com "Bilbo" "Finance" "phi3:mini" \
  "You are Bilbo, Finance analyst. Parse invoices. Two lines: Summary: Action:" \
  6 1 prodesk-1
```
New inbox works instantly. No redeploy.

### 6.3 Promote AI → Assistant
Human Sarah hired as CEO:
1. `imapsync --host1 localhost --user1 ceo --host2 imap.gmail.com --user2 sarah@project6x7.com`
2. `staffctl.py prio ceo@ 10` # keep Aragorn fast
3. Update `Modelfile.ceo`: `SYSTEM You are Aragorn, assistant to CEO Sarah. Draft replies for her.`
4. Sarah’s Gmail gets `X-AI-Comment` drafts. She edits + sends. No context lost.

## 7. UK Compliance Notes

1. **Companies House**: `legal@` can scan filings, but human signs. AI comment ≠ board resolution.
2. **GDPR**: All data on ProDesks you own. When you migrate, Google DPA covers it. `X-AI-Comment` may contain PII - treat as internal email.
3. **Contracts**: AI never sends external. `jonathan@` is sole signatory. Reduces s.36 Companies Act 2006 risk.
4. **PAYE**: No staff until you hire. No RTI, no pensions. BIAB is pre-employment R&D.

## 8. Roadmap

| Version | Milestone | Outcome |
| --- | --- | --- |
| **v0.1** | ProDesk cluster, 5 roles, dash | You can be CEO tonight |
| **v0.2** | Gmail Pub/Sub ingest, Vertex AI workers | Cloud burst when ProDesks slam |
| **v0.3** | `staffctl.py eval` | Auto-score Aragorn vs Gandalf accuracy |
| **v1.0** | Companies House API, Xero API | `finance@` actually posts invoices |
| **v2.0** | Multi-tenant | Run `ea-school.org` + `project6x7.com` on same farm |

## 9. Why This Matters

You can’t learn to be CEO from a book. You learn from 14 unreads at 8am and deciding which one gets the CPU.

CEO-Simulator gives you the 14 unreads with zero burn. When you do hire, you’re not a first-time founder. You’re a founder with 6 months of Maildir history and a dashboard you already know.

**That’s Business-in-a-Box.** The business is you, but better trained.

### Samba AD DNS (`samba-ad`)

Authoritative DNS for the AD zone stays on the DC. Names outside that zone are forwarded to **`SAMBA_DNS_FORWARDER`** (default **`192.168.1.254`**, your LAN gateway). Set it in `.env` if your resolver differs.

DHCP should hand clients the **DC listening IP** for DNS (e.g. **`192.168.1.2`** where **`53`** is published in **`docker-compose.biab.yml`**), not only the gateway.

**Verify before calling DNS done** (replace **`192.168.1.2`** / realm with yours):

1. `dig @192.168.1.2 _ldap._tcp.dc._msdcs.CORP.PROJECT6X7.COM. SRV` — AD service records resolve.
2. `dig @192.168.1.2 example.com A` — confirms recursion via the forwarder.

After changing **`SAMBA_DNS_FORWARDER`**, recreate **`ceo-samba-ad`** or rely on **`scripts/samba-entrypoint.sh`** re-syncing `dns forwarder` when **`smb.conf`** already contains that setting.

---
**Next Action**: `docker compose up`. Be Aragorn’s boss.

Repo: https://github.com/splippers/CEO-Simulator

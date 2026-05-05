FILE: CEO-SIMULATOR-FRAMEWORK.md
# CEO-Simulator: Business-in-a-Box Framework
**Version 0.3 | Splippers/CEO-Simulator | MIT License**  
**Purpose**: Let anyone become their own CEO. Play the game. Build a real UK company. All FOSS.

## 1. Executive Summary

**CEO-Simulator is a 2D office you walk around in. The staff are LLMs. The servers are ProDesks. The emails, invoices, and Companies House filings are real.**

You start in Mock Mode for fun. When ready, flip to New Startup and incorporate a real Ltd at Companies House from inside the game. Already trading? Use Enrol Mode to ingest your existing company and play it forward.

This repo is the framework + report + playable build. Clone it, run it, become CEO.

**Core Thesis**: Friction teaches. Maildir > Notion. CPU time > SaaS credits. If you can run the game, you can run the company.

## 2. The Three Modes

| Mode | Data | Email | Companies House | Risk | Use Case |
| --- | --- | --- | --- |
| **Mock Mode** | Faker-generated | docker-mailserver local only | Sandbox API, no filings | Zero | Learn, schools, EA IT testbeds |
| **New Startup** | Real founder data | Real domain + SMTP | Live API: IN01 incorporation | You form a real Ltd | Pre-revenue founders |
| **Enrol Existing** | Import via CH API + imapsync | Your domain or Gmail | Live API: Read officers, PSC, accounts | You operate real Ltd | Existing directors |

Switch modes in-game at “Reception Desk”. All progress persists. You can graduate Mock → Startup → Enrol without reset.

## 3. System Architecture: Game IS the OS

```
Browser: WorkAdventure Map :80
   | WSS + HTTP
   v
WA-Back + Redis + Postgres
   | Webhooks
   v
CEO-Simulator Central :8080 ← SQLite + WebSockets → All Players
   | docker.sock
   +--> Mail: docker-mailserver
   +--> AI: Ollama + workers per ProDesk
   +--> CRM: EspoCRM / Twenty
   +--> Accounts: Akaunting / Apache OFBiz
   +--> Files: Nextcloud + LibreOffice
   +--> Projects: Plane / Focalboard
   +--> Legal: Docassemble + CH API
   +--> Imaging: Blender/PyTorch on GPU

Each room = docker container. Each NPC = LLM + Maildir. Each "investment" = docker compose up.
```

**Principle**: No game state separate from business state. `/home/ceo/Maildir` is both Aragorn’s memory and your company record.

## 4. UK Company Functions: FOSS Tech Stack Map

All unlocked progressively. Cost = real CapEx or “in-game” difficulty.

| Phase | UK Function | Room | FOSS Container | Real World Action |
| --- | --- | --- | --- | --- |
| **0: Day 1** | Registered Office | Reception | WA spawn only | Set in .env |
| **0: Day 1** | Email + Comms | Mail Room | docker-mailserver | Send/receive real mail |
| **0: Day 1** | Documents | Board Room | Nextcloud + Collabora | LibreOffice .odt/.ods |
| **1: Ops** | Dev Tickets | Dev Pit | Plane / Focalboard | Git issues, real sprints |
| **1: Ops** | Support | Helpdesk | Zammad / UVdesk | Ticketing on your domain |
| **2: Growth** | CRM/Leads | Sales Office | EspoCRM / Twenty | Real pipeline, GDPR compliant |
| **2: Growth** | Bookkeeping | Finance Office | Akaunting + Paperless-ngx | OCR invoices, MTD VAT |
| **2: Growth** | HR | HR Office | OrangeHRM / ERPNext HR | Contracts, holidays |
| **3: Compliance** | Legal Entity | Legal Office | Docassemble + CH API | IN01, CS01, AA01 filings |
| **3: Compliance** | Data Protection | DPO Cupboard | Nextcloud GDPR app | SAR templates, RoPA |
| **3: Compliance** | Payroll | Payroll Cage | PayrollMate / ERPNext | RTI FPS/EPS to HMRC |
| **3: Scale** | Imaging/Render | Render Farm | Blender + ffmpeg + PyTorch | GPU jobs for clients |
| **3: Scale** | E-commerce | Shop Floor | Medusa / Saleor | Real Stripe test/live |

## 5. Companies House Integration: The Three Modes in Code

### 5.1 Mock Mode
Uses `https://developer-sandbox.company-information.service.gov.uk`.  
API Key: public test key. All filings return 200 but don’t persist.  
NPC “Companies House Clerk” gives fake certs. Fun + safe.

### 5.2 New Startup Mode
1. Walk to Legal Office. Talk to “Legal@ Gandalf”.
2. Game form: Company Name, SIC, Address, Directors, PSC, Shares.
3. Docassemble renders IN01.odt for review.
4. Click “Submit”. `legal-worker.py` POSTs to live CH API with your real API key.
5. CH returns company number. Broadcast: “Legal Office: Company 12345678 incorporated!”.
6. New room unlocked: “Board Room”. New NPC: “Chairman”.

You just incorporated. Certificate PDF lands in Nextcloud `/CompaniesHouse`.

### 5.3 Enrol Existing Mode
1. Reception: “Enrol Company” → Enter existing company number.
2. `ch-worker.py` pulls officers, PSC, filing history via CH API.
3. Creates NPCs for each real director. Creates Maildirs: `ceo@`, `cfo@`.
4. `imapsync` wizard: Point at your Gmail/Workspace. History ingested.
5. You spawn as Chairman. Your real staff slot into NPC roles.

## 6. Repo Structure: Cursor Build Target

```
CEO-Simulator/
├── docker-compose.biab.yml      # All services. Mode set by .env
├── .env.example                 # MODE=mock | MODE=startup | MODE=enrol
├── .env                         # You create. DOMAIN, CH_API_KEY, SIC
├── maps/
│   ├── startup-office.json      # Tiled map: rooms = tech stacks
│   └── office.js                # WA scripting: WebSockets to central
├── harness/
│   ├── central.py               # Flask + WebSocket + CH API router
│   ├── worker.py                # Generic Ollama worker
│   ├── ch-worker.py             # Companies House API agent
│   ├── mail-worker.py           # IMAP/SMTP agent
│   ├── crm-worker.py            # EspoCRM agent
│   ├── acc-worker.py            # Akaunting + Paperless agent
│   ├── staffctl.py              # CLI: add/prio/invest/hire
│   └── supervisord.conf
├── legal/
│   ├── docassemble/             # IN01, CS01, AA01 interviews
│   └── templates/               # LibreOffice .odt templates
├── mocks/                       # CRM, CH sandbox responses
├── docs/
│   ├── BIAB.md                  # This framework
│   ├── PLAYBOOK.md              # Day 1 → Ltd → VAT
│   ├── MIGRATE.md               # ProDesk → AWS/GCP
│   └── REPORT.md                # The report others use to replicate
└── README.md                    # 10-min quickstart
```

## 7. Quickstart: Become CEO in 10 Minutes

```bash
git clone https://github.com/splippers/CEO-Simulator
cd CEO-Simulator
cp .env.example .env
# Edit .env: MODE=mock, DOMAIN=startup.co.uk, HUMAN=founder
docker compose -f docker-compose.biab.yml up -d
docker exec -it $(docker ps -qf name=ollama) ollama pull llama3.1:8b
echo "127.0.0.1 biab.local" | sudo tee -a /etc/hosts
open http://biab.local
```
Walk to CEO Desk. Talk to Aragorn. You’re CEO.

## 8. Gameplay → Real World: Investment Loop

1. **In-Game**: HUD shows “Imaging Farm: Locked. Invest £500”.
2. **Real World**: You buy GPU ProDesk off eBay. Plug in.
3. **In-Game**: Click “Invest”. `central.py` runs `docker compose up imaging`.
4. **WorkAdventure**: Render Farm room door unlocks. NPC “Blender Bot” appears.
5. **Real World**: Drag client .blend to Nextcloud `/Render`. Bot queues job on GPU.
6. **In-Game**: Bot emotes “Rendering”. You see progress bar.
7. **Real World**: Job done. MP4 in Nextcloud. Invoice draft in Akaunting.
8. **In-Game**: Walk to Finance Office. Bilbo: “Invoice ready. Send?”
9. **Real World**: Click Send. Real email via your SMTP. Client pays.

You played. HMRC is happy. You made money.

## 9. The Report: How Others Replicate

`docs/REPORT.md` in repo is the artifact you hand to schools, EA, funders. It contains:

1. **Why**: UK productivity, NEETs, CEO skills gap. Game = safe practice.
2. **What**: Architecture diagrams, FOSS list, GDPR statement.
3. **How**: 10-min quickstart, ProDesk shopping list, mode guides.
4. **Proof**: Case study: `project6x7.co.uk` incorporated via game on 2026-05-12.
5. **Scale**: Multi-tenant mode: Run 30 schools on 1 ProDesk farm.
6. **Exit**: `imapsync` + `pg_dump` = graduate to AWS. No vendor lock.

This report is the deliverable. The game is the appendix.

## 10. Compliance & Safety

1. **Companies House**: Live API key in `.env`. All filings logged. Human confirms before POST.
2. **GDPR**: All data on your tin. Nextcloud + Postgres = UK-hosted. SAR button in DPO Cupboard.
3. **AI Firewall**: LLMs never hit external SMTP. `X-AI-Comment` only. You sign all.
4. **PAYE/RTI**: Disabled until you “Hire” in-game, which creates real HMRC PAYE scheme.
5. **MTD VAT**: Akaunting + VAT module. Bilbo drafts, you submit.

## 11. Roadmap to v1.0

| Version | Milestone | Enables |
| --- | --- | --- |
| **v0.3** | Mock Mode complete | Schools can play safe |
| **v0.4** | CH Sandbox IN01 flow | Test incorporation |
| **v0.5** | New Startup Mode live | Real Ltd in 20 mins |
| **v0.6** | Enrol Mode + imapsync | Existing SMEs onboard |
| **v0.7** | Akaunting MTD + RTI | Real tax submissions |
| **v1.0** | Multi-tenant + LDAP | EA runs 50 companies on 5 ProDesks |

## 12. Call to Action

This isn’t a game you play. It’s a company you run, with a game as the shell.

**Next steps for Cursor:**
1. Create repo structure above.
2. Commit `docker-compose.biab.yml` with `MODE` env switch.
3. Implement `ch-worker.py` with CH sandbox + live endpoints.
4. Ship `maps/startup-office.json` with 3 rooms: Reception, CEO, Mail.
5. Write `docs/REPORT.md` from this framework.

**Next step for you, Jonathan:**
Run it in Mock Mode. Spam `ceo@`. Feel the backlog. Then flip `.env` to `MODE=startup`. Walk to Legal Office. Incorporate `project6x7.co.uk` for £12.

You’ll be CEO before lunch.

---
Repo: https://github.com/splippers/CEO-Simulator  
License: MIT. Steal this. Run your town.  

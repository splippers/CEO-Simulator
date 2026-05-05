# CEO-Simulator — Initial game plan

This plan turns [Framework.md](./Framework.md) and [BIAB.md](./BIAB.md) into an executable build sequence. Order matters: each phase unlocks real UK-company mechanics without pretending unfinished pieces are production-safe.

## North star

Ship **Mock Mode first** (zero external risk), then **Companies House sandbox**, then **live New Startup** and **Enrol**, with **one shared rule**: game state and business state stay unified (Maildir + services the game shells).

## Phase 0 — Repository and run skeleton

- Land the target tree from Framework §6: `docker-compose.biab.yml`, `.env.example` (`MODE=mock|startup|enrol`), `harness/`, `maps/`, `legal/`, `mocks/`, remaining `docs/` stubs as referenced in Framework.
- One command brings up the minimal stack for Mock: WA entry, central, Redis/Postgres as needed, local mail, Ollama placeholder or documented pull.
- Document hostnames (`biab.local`) and health checks in README so “10 minutes to CEO desk” is verifiable.

## Phase 1 — BIAB core in the harness

- Implement `central.py` (queue, staff, boxes) and `worker.py` (Ollama job drain) per BIAB §3–5: priority, box affinity, Maildir handoff, **AI firewall** (no external SMTP from LLM paths; `X-AI-Comment` only).
- Add `staffctl.py` for roles and priorities (BIAB §6).
- Prove **Maildir is law**: inbound path → queue → worker → human Maildir; dashboard shows backlog and box load.

## Phase 2 — WorkAdventure shell

- `maps/startup-office.json` with **Reception, CEO desk, Mail** first (Framework Cursor checklist §12).
- `office.js` (or equivalent): WebSocket client to central; room enter/leave tied to “desks” and NPC presence.
- NPCs = staff rows + LLM config; walking to a desk triggers the same job/conversation surface the harness already understands.

## Phase 3 — Companies House (sandbox before live)

- `ch-worker.py`: sandbox API for Mock (Framework §5.1); fake certs and NPC “Clerk” behaviour backed by `mocks/` fixtures.
- Legal path: Docassemble interviews + LibreOffice templates under `legal/`; **human confirmation** before any live POST (Framework §10).
- Only after sandbox is boring: wire **New Startup** live filing (Framework §5.2) and broadcast company number into the world state.

## Phase 4 — Enrol and real comms

- Enrol flow: company number → CH read APIs → director/PSC NPCs → Maildir layout (Framework §5.3).
- `mail-worker.py` / `imapsync` wizard for ingesting existing inboxes; mode switch at Reception without reset.

## Phase 5 — Progressive “rooms = compose profiles”

Unlock containers by phase (Framework §4): documents (Nextcloud), tickets (Plane/Focalboard), CRM, accounting (Akaunting + Paperless), compliance (Docassemble + CH), etc. Each unlock should map to **real** `docker compose` profiles or explicit `invest`/hire actions in-game.

## Phase 6 — Artefacts for outsiders

- Flesh `docs/REPORT.md`, `docs/PLAYBOOK.md`, `docs/MIGRATE.md` per Framework §6 and §9 so schools/EA can replicate without reading source.

## Success criteria (exit each phase)

| Phase | Done when |
| --- | --- |
| 0 | `docker compose … up` + README quickstart works end-to-end in Mock |
| 1 | Mail-driven loop + dashboard + AI firewall enforced in code paths |
| 2 | Three-room map; CEO desk talks to same backend as harness |
| 3 | Sandbox IN01 (or equivalent) round-trip with logged dry-run |
| 4 | Enrol pulls real CH metadata into game state; optional IMAP ingest documented |
| 5 | At least one “growth” room (e.g. docs or tickets) behind an in-game gate |
| 6 | REPORT gives a non-developer a credible replication story |

## Version alignment

Track releases against Framework §11 (v0.3 Mock complete → v1.0 multi-tenant). Tag `v0.3.0` when Phase 0–2 meet Mock success criteria; later tags follow roadmap milestones.

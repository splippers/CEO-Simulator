# CEO-Simulator

**Business-in-a-box as a 2D office**: WorkAdventure map, LLM “staff”, real Maildir and (when enabled) real UK company workflows—see the framework for the full architecture and modes.

## Documentation

- [Business-in-a-Box framework (v0.3)](docs/Framework.md) — modes, stack map, Companies House, repo target layout, roadmap.
- [BIAB cluster vision (v0.1)](docs/BIAB.md) — Maildir, AI firewall, ProDesk workers, dashboard.
- [Initial game plan (build order)](docs/GAME_PLAN.md) — phased implementation from mock-safe skeleton to live enrol.

## Quickstart (target per framework)

When `docker-compose.biab.yml` and `.env.example` land:

```bash
git clone https://github.com/splippers/CEO-Simulator
cd CEO-Simulator
cp .env.example .env
# Set MODE=mock and edit DOMAIN / secrets as documented
docker compose -f docker-compose.biab.yml up -d
```

Further steps (hosts file, Ollama pull, `biab.local`) are in [Framework §7](docs/Framework.md).

## License

MIT — see [LICENSE](LICENSE).

Repository: https://github.com/splippers/CEO-Simulator

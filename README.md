# CEO-Simulator

**Business-in-a-box as a 2D office**: WorkAdventure map, LLM “staff”, real Maildir and (when enabled) real UK company workflows—see the framework for the full architecture and modes.

## Documentation

- [Business-in-a-Box framework (v0.3)](docs/Framework.md) — modes, stack map, Companies House, repo target layout, roadmap.
- [BIAB cluster vision (v0.1)](docs/BIAB.md) — Maildir, AI firewall, ProDesk workers, dashboard.
- [Initial game plan (build order)](docs/GAME_PLAN.md) — phased implementation from mock-safe skeleton to live enrol.

## Quickstart (prototype central)

```bash
git clone https://github.com/splippers/CEO-Simulator
cd CEO-Simulator
cp .env.example .env
# Set MODE=mock, DOMAIN, and NERVECENTRE_PUBLIC_ORIGIN (e.g. http://marvin.lan)
docker compose -f docker-compose.biab.yml up --build -d
curl -s "http://127.0.0.1:${CEO_CENTRAL_PORT:-8080}/health"
```

Run without Docker:

```bash
./scripts/run-dev.sh
```

Health and NerveCentre reachability:

- `GET /health` — process up.
- `GET /api/nervecentre/probe` — HTTP GET to `NERVECENTRE_PUBLIC_ORIGIN` + `NERVECENTRE_PING_PATH` (defaults to `/`).

## NerveCentre on Marvin (or any nginx portal host)

[Splippers NerveCentre](https://github.com/splippers/NerveCentre) proxies **`/ceo-simulator/`** to this central (default backend **`127.0.0.1:8080`**), same pattern as **`/jonotron/`**.

1. On **Marvin**, run central on **8080** (compose or `./scripts/run-dev.sh`).
2. Pull NerveCentre **`deploy/portal`** that includes the `CEO_SIMULATOR_*` upstream and landing card.
3. Reinstall the portal so nginx picks up the new site:

   ```bash
   cd Projects/NerveCentre
   sudo CEO_SIMULATOR_PORT=8080 ./deploy/portal/install-portal.sh
   ```

   For a central on another host/port: `sudo CEO_SIMULATOR_BACKENDS="10.0.0.9:8080" ./deploy/portal/install-portal.sh`

4. Open **`http://<nervecentre-host>/ceo-simulator/health`** — should match **`http://127.0.0.1:8080/health`** on the box running central.

Further steps (WorkAdventure, Ollama, `biab.local`) are in [Framework §7](docs/Framework.md).

## License

MIT — see [LICENSE](LICENSE).

Repository: https://github.com/splippers/CEO-Simulator

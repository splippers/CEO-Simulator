"""
CEO-Simulator central (prototype): BIAB harness entrypoint behind NerveCentre /ceo-simulator/.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from flask import Flask, Response, jsonify, request

app = Flask(__name__)

_START = time.monotonic()


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


@app.get("/health")
def health() -> Response:
    return jsonify(ok=True, service="ceo-simulator-central", uptime_s=round(time.monotonic() - _START, 3))


@app.get("/api/info")
def api_info() -> Response:
    return jsonify(
        mode=_env("MODE", "mock"),
        domain=_env("DOMAIN"),
        human=_env("HUMAN"),
        nervecentre_public_origin=_env("NERVECENTRE_PUBLIC_ORIGIN"),
    )


@app.get("/api/nervecentre/probe")
def nervecentre_probe() -> tuple[Response, int]:
    origin = _env("NERVECENTRE_PUBLIC_ORIGIN")
    if not origin:
        return jsonify(ok=False, error="NERVECENTRE_PUBLIC_ORIGIN not set"), 503

    url = origin.rstrip("/") + _env("NERVECENTRE_PING_PATH", "/")
    started = time.monotonic()

    def _fetch() -> tuple[int | None, str | None]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CEO-Simulator-Central/0.1"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status, None
        except urllib.error.HTTPError as e:
            return e.code, str(e)
        except Exception as e:  # noqa: BLE001 — boundary: log shape for operators
            return None, str(e)

    status, err = _fetch()
    ms = round((time.monotonic() - started) * 1000, 2)
    body: dict[str, Any] = {
        "ok": status is not None and 200 <= status < 400,
        "url": url,
        "status": status,
        "latency_ms": ms,
    }
    if err:
        body["error"] = err
    code = 200 if body["ok"] else 502
    return jsonify(body), code


@app.post("/api/hooks/nervecentre")
def hook_nervecentre() -> tuple[Response, int]:
    """Optional ingress for future NerveCentre → central automations (signature TBD)."""
    secret = _env("NERVECENTRE_WEBHOOK_SECRET")
    if secret and request.headers.get("X-Nervecentre-Secret") != secret:
        return jsonify(ok=False, error="unauthorized"), 401
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception:  # noqa: BLE001
        return jsonify(ok=False, error="invalid json"), 400
    app.logger.info("nervecentre hook: %s", json.dumps(payload, default=str)[:2000])
    return jsonify(ok=True, received=True), 200


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    port = int(_env("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=_env("FLASK_DEBUG") == "1", use_reloader=False, threaded=True)

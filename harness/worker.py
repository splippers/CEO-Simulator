"""
Opencode worker: long-polls the central job queue, runs opencode with Big-Pickle
for each job, and posts the result back.

Usage:
  python3 harness/worker.py                          # default: http://127.0.0.1:8080
  CENTRAL_URL=http://192.168.1.10:8080 python3 harness/worker.py
  OPENCODE_MODEL=opencode/big-pickle python3 harness/worker.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid

import urllib.error
import urllib.request

CENTRAL_URL = os.environ.get("CENTRAL_URL", "http://127.0.0.1:8080").rstrip("/")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "3"))
WORKER_ID = os.environ.get("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
OPENCODE_MODEL = os.environ.get("OPENCODE_MODEL", "opencode/big-pickle")
OPENCODE_TIMEOUT = int(os.environ.get("OPENCODE_TIMEOUT", "120"))


def log(msg: str) -> None:
    print(f"[{WORKER_ID}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _request(method: str, path: str, body: bytes | None = None) -> tuple[int, dict | None]:
    url = f"{CENTRAL_URL}{path}"
    headers = {"User-Agent": "CEO-Simulator-Worker/0.1"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        data = e.read()
        return e.code, json.loads(data) if data else None
    except Exception as e:
        return 0, {"ok": False, "error": str(e)}


def fetch_job() -> dict | None:
    code, data = _request("GET", f"/api/job/next?worker={WORKER_ID}")
    if code == 204 or (data and not data.get("ok")):
        return None
    if data and data.get("ok"):
        return data
    return None


def submit_result(job_id: str, result: str | None = None, error: str | None = None) -> bool:
    body = json.dumps({
        "result": result,
        "error": error,
        "worker": WORKER_ID,
    }).encode()
    code, _ = _request("POST", f"/api/job/{job_id}/result", body=body)
    return code == 200


# ---------------------------------------------------------------------------
# Opencode runner
# ---------------------------------------------------------------------------


def run_opencode(system_prompt: str, context: str) -> tuple[str | None, str | None]:
    """Run opencode with the given prompt. Returns (result_text, error)."""
    message = f"{system_prompt}\n\n---\n\n{context}\n\n---\n\nWrite your response:"

    with tempfile.TemporaryDirectory(prefix="ceo-worker-") as tmpdir:
        cmd = [
            "opencode", "run", message,
            "--format", "json",
            "--model", OPENCODE_MODEL,
            "--dir", tmpdir,
        ]
        log(f"running: {' '.join(cmd[:4])} ...")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=OPENCODE_TIMEOUT,
            )
        except FileNotFoundError:
            return None, "opencode binary not found on PATH"
        except subprocess.TimeoutExpired:
            return None, f"opencode timed out after {OPENCODE_TIMEOUT}s"
        except Exception as e:
            return None, f"subprocess error: {e}"

    # Parse JSON events for the text response
    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            text = event.get("part", {}).get("text", "")
            if text:
                return text.strip(), None

    # If no text event found, check stderr
    stderr = proc.stderr.strip() if proc.stderr else ""
    if stderr:
        # stderr has opencode log lines but sometimes has errors
        pass

    return None, f"no text response from opencode (exit code {proc.returncode})"


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    log(f"worker starting")
    log(f"  central:   {CENTRAL_URL}")
    log(f"  model:     {OPENCODE_MODEL}")
    log(f"  poll:      {POLL_INTERVAL}s")
    log(f"  timeout:   {OPENCODE_TIMEOUT}s")
    log(f"  worker_id: {WORKER_ID}")

    while True:
        try:
            job = fetch_job()
        except Exception as e:
            log(f"error fetching job: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        if job:
            log(f"got job {job['id']} for role '{job.get('role', '?')}'")
            result, error = run_opencode(
                job.get("system_prompt", ""),
                job.get("context", ""),
            )

            if result:
                submit_result(job["id"], result=result)
                log(f"completed job {job['id']} ({len(result)} chars)")
            else:
                submit_result(job["id"], error=error or "unknown error")
                log(f"FAILED job {job['id']}: {error}")
        else:
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

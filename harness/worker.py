"""
Opencode worker: long-polls the central job queue, runs opencode with Big-Pickle
for each job, posts the result back, and optionally sends an email reply.

Usage:
  python3 harness/worker.py                          # default: http://127.0.0.1:8080
  CENTRAL_URL=http://192.168.1.10:8080 python3 harness/worker.py
  OPENCODE_MODEL=opencode/big-pickle python3 harness/worker.py
  ENABLE_AUTOREPLY=1 python3 harness/worker.py       # also send email replies
"""

from __future__ import annotations

import json
import os
import re
import smtplib
import subprocess
import sys
import tempfile
import time
import uuid
from email.mime.text import MIMEText

import urllib.error
import urllib.request

CENTRAL_URL = os.environ.get("CENTRAL_URL", "http://127.0.0.1:8080").rstrip("/")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "3"))
WORKER_ID = os.environ.get("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
OPENCODE_MODEL = os.environ.get("OPENCODE_MODEL", "opencode/big-pickle")
OPENCODE_TIMEOUT = int(os.environ.get("OPENCODE_TIMEOUT", "120"))

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
ENABLE_AUTOREPLY = os.environ.get("ENABLE_AUTOREPLY", "0") == "1"


def log(msg: str) -> None:
    print(f"[{WORKER_ID}] {msg}", flush=True)


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


def parse_sender(context: str) -> str | None:
    m = re.search(r"^From:\s*(.*)", context, re.MULTILINE)
    if m:
        addr = m.group(1).strip()
        m2 = re.search(r"<([^>]+)>", addr)
        if m2:
            return m2.group(1)
        if "@" in addr:
            return addr
    return None


def parse_subject(context: str) -> str:
    m = re.search(r"^Subject:\s*(.*)", context, re.MULTILINE)
    return m.group(1).strip() if m else ""


def send_email_reply(to_addr: str, original_subject: str, reply_body: str) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        log("SMTP not configured, skipping email reply")
        return False
    prefix = "Re: " if not original_subject.lower().startswith("re:") else ""
    msg = MIMEText(reply_body, _charset="utf-8")
    msg["From"] = "Aragorn <ceo@project6x7.com>"
    msg["To"] = to_addr
    msg["Subject"] = f"{prefix}{original_subject}"
    msg["In-Reply-To"] = original_subject
    try:
        s = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
        s.quit()
        log(f"sent email reply to {to_addr}")
        return True
    except Exception as e:
        log(f"failed to send email reply: {e}")
        return False


def run_opencode(system_prompt: str, context: str) -> tuple[str | None, str | None]:
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

    stderr = proc.stderr.strip() if proc.stderr else ""
    if stderr:
        pass

    return None, f"no text response from opencode (exit code {proc.returncode})"


def main() -> None:
    log(f"worker starting")
    log(f"  central:    {CENTRAL_URL}")
    log(f"  model:      {OPENCODE_MODEL}")
    log(f"  poll:       {POLL_INTERVAL}s")
    log(f"  timeout:    {OPENCODE_TIMEOUT}s")
    log(f"  worker_id:  {WORKER_ID}")
    log(f"  autoreply:  {'ON' if ENABLE_AUTOREPLY else 'OFF'}")

    while True:
        try:
            job = fetch_job()
        except Exception as e:
            log(f"error fetching job: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        if job:
            log(f"got job {job['id']} for role '{job.get('role', '?')}'")
            context = job.get("context", "")

            result, error = run_opencode(
                job.get("system_prompt", ""),
                context,
            )

            if result:
                submit_result(job["id"], result=result)
                log(f"completed job {job['id']} ({len(result)} chars)")

                if ENABLE_AUTOREPLY:
                    sender = parse_sender(context)
                    if sender:
                        subj = parse_subject(context)
                        send_email_reply(sender, subj, result)
                    else:
                        log(f"could not parse sender from context, skipping reply")
            else:
                submit_result(job["id"], error=error or "unknown error")
                log(f"FAILED job {job['id']}: {error}")
        else:
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

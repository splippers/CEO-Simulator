"""
Ingest: watches docker-mailserver Maildir volumes for new messages,
parses them, and POSTs to central /api/job based on recipient role.
"""

from __future__ import annotations

import email.message
import email.policy
import json
import os
import time

import urllib.error
import urllib.request

CENTRAL_URL = os.environ.get("CENTRAL_URL", "http://central:8080").rstrip("/")
MAIL_DIR = os.environ.get("MAIL_DIR", "/var/mail")
DOMAIN = os.environ.get("DOMAIN", "biab.local")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "2"))

LOCALPART_TO_ROLE: dict[str, str | None] = {
    "ceo": "ceo",
    "cto": "cto",
    "dev": "dev",
    "ops": "ops",
    "support": "support",
    "postmaster": None,  # system, skip
}


def log(msg: str) -> None:
    print(f"[ingest] {msg}", flush=True)


def find_new_mail() -> list[tuple[str, str]]:
    """Scan mail directories for new (unread) messages under DOMAIN."""
    domain_dir = os.path.join(MAIL_DIR, DOMAIN)
    if not os.path.isdir(domain_dir):
        return []
    found: list[tuple[str, str]] = []
    for user in os.listdir(domain_dir):
        new_dir = os.path.join(domain_dir, user, "Maildir", "new")
        if not os.path.isdir(new_dir):
            continue
        for fname in sorted(os.listdir(new_dir)):
            fpath = os.path.join(new_dir, fname)
            if os.path.isfile(fpath):
                found.append((user, fpath))
    return found


def parse_email(fpath: str) -> tuple[str, str] | None:
    """Parse an email file, return (role, context_str) or None."""
    try:
        with open(fpath, "rb") as f:
            msg = email.message_from_binary_file(f, policy=email.policy.default)
    except Exception as e:
        log(f"error reading {fpath}: {e}")
        return None

    to_addr = msg.get("To", "") or ""
    from_addr = msg.get("From", "") or ""
    subject = msg.get("Subject", "") or "(no subject)"

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content() or ""

    if body:
        body = body.strip()

    localpart = to_addr.split("@")[0].strip().lower() if "@" in to_addr else ""
    role = LOCALPART_TO_ROLE.get(localpart)

    if role is None:
        log(f"no role mapping for '{to_addr}' (localpart={localpart!r}), skipping")
        return None

    context = f"From: {from_addr}\nSubject: {subject}\n\n{body}"
    return role, context


def submit_job(role: str, context: str) -> bool:
    url = f"{CENTRAL_URL}/api/job"
    payload = json.dumps({"role": role, "context": context}).encode()
    try:
        req = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("ok"):
                log(f"submitted {role} job: {data.get('job_id')}")
                return True
            log(f"central rejected: {data}")
            return False
    except Exception as e:
        log(f"error submitting job: {e}")
        return False


def mark_processed(fpath: str) -> None:
    """Move file from Maildir/new/ to Maildir/cur/."""
    cur_path = fpath.replace("/new/", "/cur/")
    if cur_path == fpath:
        return
    try:
        os.renames(fpath, cur_path)
    except OSError:
        pass  # will be picked up again next poll


def main() -> None:
    log(f"ingest starting")
    log(f"  mail_dir: {MAIL_DIR}")
    log(f"  domain:   {DOMAIN}")
    log(f"  central:  {CENTRAL_URL}")
    log(f"  poll:     {POLL_INTERVAL}s")

    while True:
        try:
            for user, fpath in find_new_mail():
                result = parse_email(fpath)
                if result:
                    role, context = result
                    if submit_job(role, context):
                        mark_processed(fpath)
        except Exception as e:
            log(f"loop error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

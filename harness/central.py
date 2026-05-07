"""
CEO-Simulator central (prototype): BIAB harness entrypoint behind NerveCentre /ceo-simulator/.
Extended with job queue for opencode workers.
"""

from __future__ import annotations

import email
import email.policy
import json
import os
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

import urllib.error
import urllib.request
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

_START = time.monotonic()

# ---------------------------------------------------------------------------
# Job queue
# ---------------------------------------------------------------------------

_JOB_LEASE_S = int(os.environ.get("JOB_LEASE_SECONDS", "300"))


@dataclass
class Job:
    id: str
    role: str
    priority: int
    system_prompt: str
    context: str
    status: str = "pending"  # pending | running | completed | failed
    result: str | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.monotonic)
    started_at: float | None = None
    completed_at: float | None = None
    worker: str | None = None
    lease_expires: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "priority": self.priority,
            "system_prompt": self.system_prompt,
            "context": self.context,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": round(self.created_at, 3),
            "started_at": round(self.started_at, 3) if self.started_at else None,
            "completed_at": round(self.completed_at, 3) if self.completed_at else None,
            "worker": self.worker,
        }

    def is_lease_expired(self) -> bool:
        return self.lease_expires is not None and time.monotonic() > self.lease_expires


class JobQueue:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}
        self._pending: list[str] = []  # job IDs ordered by priority then creation

    def enqueue(self, role: str, priority: int, system_prompt: str, context: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        job = Job(id=job_id, role=role, priority=priority,
                  system_prompt=system_prompt, context=context)
        with self._lock:
            self._jobs[job_id] = job
            self._pending.append(job_id)
            self._pending.sort(key=lambda jid: (
                -self._jobs[jid].priority, self._jobs[jid].created_at
            ))
        return job_id

    def dequeue(self, worker_id: str) -> Job | None:
        now = time.monotonic()
        with self._lock:
            # expire stale leases
            for jid in list(self._pending):
                job = self._jobs.get(jid)
                if job and job.status == "running" and job.is_lease_expired():
                    job.status = "pending"
                    job.worker = None
                    job.lease_expires = None

            # find next pending job
            for i, jid in enumerate(self._pending):
                job = self._jobs.get(jid)
                if job and job.status == "pending":
                    job.status = "running"
                    job.started_at = now
                    job.worker = worker_id
                    job.lease_expires = now + _JOB_LEASE_S
                    self._pending.pop(i)
                    return job
        return None

    def complete(self, job_id: str, result: str | None = None,
                 error: str | None = None, worker: str | None = None) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if worker and job.worker and job.worker != worker:
                return False
            job.status = "failed" if error else "completed"
            job.result = result
            job.error = error
            job.completed_at = time.monotonic()
            job.lease_expires = None
        return True

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = [j.to_dict() for j in self._jobs.values()]
            jobs.sort(key=lambda j: (-j["priority"], j["created_at"]))
            return jobs

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "pending": sum(1 for j in self._jobs.values() if j.status == "pending"),
                "running": sum(1 for j in self._jobs.values() if j.status == "running"),
                "completed": sum(1 for j in self._jobs.values() if j.status == "completed"),
                "failed": sum(1 for j in self._jobs.values() if j.status == "failed"),
                "total": len(self._jobs),
            }


_queue = JobQueue()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()

# ---------------------------------------------------------------------------
# Existing routes
# ---------------------------------------------------------------------------


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
        except Exception as e:
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
    secret = _env("NERVECENTRE_WEBHOOK_SECRET")
    if secret and request.headers.get("X-Nervecentre-Secret") != secret:
        return jsonify(ok=False, error="unauthorized"), 401
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(ok=False, error="invalid json"), 400
    app.logger.info("nervecentre hook: %s", json.dumps(payload, default=str)[:2000])
    return jsonify(ok=True, received=True), 200

# ---------------------------------------------------------------------------
# Job queue routes
# ---------------------------------------------------------------------------


@app.post("/api/job")
def api_enqueue() -> tuple[Response, int]:
    """Enqueue a new AI job for a staff role."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(ok=False, error="invalid json"), 400

    role = (data.get("role") or "").strip()
    context = (data.get("context") or "").strip()
    if not role or not context:
        return jsonify(ok=False, error="role and context required"), 400

    priority = int(data.get("priority", 5))
    system_prompt = (data.get("system_prompt") or "").strip()

    job_id = _queue.enqueue(role, priority, system_prompt, context)
    app.logger.info("enqueued job %s for role '%s' (prio %d)", job_id, role, priority)
    return jsonify(ok=True, job_id=job_id), 201


@app.get("/api/job/next")
def api_job_next() -> tuple[Response, int]:
    """Claim the next available job (polled by workers). Returns 204 if empty."""
    worker = (request.args.get("worker") or "").strip()
    if not worker:
        return jsonify(ok=False, error="worker param required"), 400

    job = _queue.dequeue(worker)
    if not job:
        return jsonify(ok=False), 204

    return jsonify(
        ok=True,
        id=job.id,
        role=job.role,
        priority=job.priority,
        system_prompt=job.system_prompt,
        context=job.context,
    ), 200


@app.post("/api/job/<job_id>/result")
def api_job_result(job_id: str) -> tuple[Response, int]:
    """Submit the result of a completed (or failed) job."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(ok=False, error="invalid json"), 400

    worker = (data.get("worker") or "").strip() or None
    result = (data.get("result") or "").strip() or None
    error = (data.get("error") or "").strip() or None

    ok = _queue.complete(job_id, result=result, error=error, worker=worker)
    if not ok:
        return jsonify(ok=False, error="job not found or worker mismatch"), 404

    return jsonify(ok=True), 200


@app.get("/api/job/<job_id>")
def api_job_get(job_id: str) -> tuple[Response, int]:
    job = _queue.get(job_id)
    if not job:
        return jsonify(ok=False, error="not found"), 404
    return jsonify(ok=True, job=job.to_dict()), 200


@app.get("/api/jobs")
def api_jobs_list() -> Response:
    return jsonify(ok=True, jobs=_queue.list(), stats=_queue.stats())


# ---------------------------------------------------------------------------
# Cloudflare Email ingest
# ---------------------------------------------------------------------------


@app.post("/api/ingest/email")
def api_ingest_email() -> tuple[Response, int]:
    """Receive forwarded email from the Cloudflare Worker and enqueue a job."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(ok=False, error="invalid json"), 400

    secret = _env("INGEST_SECRET")
    if secret and data.get("secret") != secret:
        return jsonify(ok=False, error="unauthorized"), 401

    role = (data.get("role") or "").strip()
    context = (data.get("context") or "").strip()
    if not role or not context:
        return jsonify(ok=False, error="role and context required"), 400

    # If raw email content is sent, parse it into a clean context string
    if context.startswith("From ") or context.startswith("Return-Path:"):
        try:
            msg = email.message_from_string(context, policy=email.policy.default)
            from_addr = msg.get("From", "(unknown)")
            subject = msg.get("Subject", "(no subject)")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_content()
                        break
            else:
                body = msg.get_content() or ""
            context = f"From: {from_addr}\nSubject: {subject}\n\n{body.strip()}"
        except Exception:
            pass  # fall through with raw context

    job_id = _queue.enqueue(role, int(data.get("priority", 5)), "", context)
    app.logger.info("ingest email: enqueued job %s for role '%s'", job_id, role)
    return jsonify(ok=True, job_id=job_id), 201


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    port = int(_env("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=_env("FLASK_DEBUG") == "1", use_reloader=False, threaded=True)

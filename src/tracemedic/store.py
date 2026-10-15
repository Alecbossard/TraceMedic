"""Durable audit journal and idempotency ledger, separate from graph checkpoints."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(UTC).isoformat()


def stable_id(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:20]


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, incident_id TEXT NOT NULL, mode TEXT NOT NULL,
                  provider TEXT NOT NULL, model TEXT NOT NULL, status TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT '{}', cancel_requested INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS events (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
                  event_key TEXT NOT NULL, timestamp TEXT NOT NULL, role TEXT NOT NULL,
                  kind TEXT NOT NULL, message TEXT NOT NULL, data TEXT NOT NULL,
                  UNIQUE(run_id,event_key)
                );
                CREATE TABLE IF NOT EXISTS evidence (
                  run_id TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL,
                  PRIMARY KEY(run_id,id)
                );
                CREATE TABLE IF NOT EXISTS operations (
                  run_id TEXT NOT NULL, key TEXT NOT NULL, status TEXT NOT NULL,
                  result TEXT, PRIMARY KEY(run_id,key)
                );
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def create(self, run_id, incident_id, mode, provider, model):
        with self.connect() as db:
            db.execute(
                "INSERT INTO runs(id,incident_id,mode,provider,model,status,created_at,updated_at) VALUES(?,?,?,?,?,'queued',?,?)",
                (run_id, incident_id, mode, provider, model, now(), now()),
            )

    def run(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        result = dict(row)
        result["state"] = json.loads(result["state"])
        return result

    def runs(self):
        with self.connect() as db:
            ids = [
                r[0] for r in db.execute("SELECT id FROM runs ORDER BY created_at DESC LIMIT 100")
            ]
        return [self.run(key) for key in ids]

    def update(self, run_id, status=None, state=None, cancel=None):
        fields, values = ["updated_at=?"], [now()]
        for column, value in (
            ("status", status),
            ("state", json.dumps(state) if state is not None else None),
            ("cancel_requested", int(cancel) if cancel is not None else None),
        ):
            if value is not None:
                fields.append(f"{column}=?")
                values.append(value)
        with self.connect() as db:
            db.execute(f"UPDATE runs SET {','.join(fields)} WHERE id=?", (*values, run_id))

    def event(self, run_id, key, role, kind, message, data=None):
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO events(run_id,event_key,timestamp,role,kind,message,data) VALUES(?,?,?,?,?,?,?)",
                (run_id, key, now(), role, kind, message, json.dumps(data or {})),
            )

    def events(self, run_id):
        with self.connect() as db:
            return [
                {**dict(r), "data": json.loads(r["data"])}
                for r in db.execute("SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,))
            ]

    def add_evidence(self, run_id, evidence):
        with self.connect() as db:
            for item in evidence:
                db.execute(
                    "INSERT OR IGNORE INTO evidence VALUES(?,?,?)",
                    (run_id, item["id"], json.dumps(item)),
                )

    def evidence(self, run_id):
        with self.connect() as db:
            return [
                json.loads(r[0])
                for r in db.execute(
                    "SELECT body FROM evidence WHERE run_id=? ORDER BY id", (run_id,)
                )
            ]

    def cached(self, run_id, key):
        with self.connect() as db:
            row = db.execute(
                "SELECT status,result FROM operations WHERE run_id=? AND key=?", (run_id, key)
            ).fetchone()
        return dict(row) if row else None

    def claim(self, run_id, key):
        with self.connect() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO operations VALUES(?,?,'started',NULL)", (run_id, key)
            )
            return cursor.rowcount == 1

    def complete(self, run_id, key, result):
        with self.connect() as db:
            db.execute(
                "INSERT INTO operations VALUES(?,?,'completed',?) ON CONFLICT(run_id,key) DO UPDATE SET status='completed',result=excluded.result",
                (run_id, key, json.dumps(result)),
            )

    def metrics(self, run_id):
        events = self.events(run_id)
        attempts = [e for e in events if e["kind"] == "model_attempt"]
        responses = [e["data"] for e in events if e["kind"] == "model_response"]
        tools = [e["data"] for e in events if e["kind"] == "tool_result"]
        return {
            "model_calls": len(attempts),
            "tool_calls": len(tools),
            "tool_successes": sum(t.get("ok", False) for t in tools),
            "input_tokens": sum(r.get("input_tokens") or 0 for r in responses)
            if responses
            else None,
            "output_tokens": sum(r.get("output_tokens") or 0 for r in responses)
            if responses
            else None,
            "usage_complete": len(responses) == len(attempts)
            and all(
                r.get("input_tokens") is not None and r.get("output_tokens") is not None
                for r in responses
            ),
            "model_latency_ms": round(sum(r.get("latency_ms", 0) for r in responses), 1),
            "cost_usd": None,
        }

#!/usr/bin/env python3
"""Minimal durable queue demonstration for OpenCode peer tasks.

This is not a network daemon and not production-ready. It demonstrates a transactional
SQLite claim/lease state machine that a real coordinator can build upon.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
import uuid
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  target TEXT NOT NULL,
  envelope_json TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('queued','leased','succeeded','failed','cancelled','dead')),
  attempt INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_until INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  result_json TEXT
);
CREATE INDEX IF NOT EXISTS tasks_dispatch ON tasks(state, target, created_at);
"""


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def submit(db: sqlite3.Connection, envelope: dict) -> str:
    now = int(time.time())
    task_id = envelope.get("task_id") or f"tsk_{uuid.uuid4().hex}"
    db.execute(
        "INSERT OR IGNORE INTO tasks(id,idempotency_key,target,envelope_json,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (
            task_id,
            envelope["idempotency_key"],
            envelope["target"]["principal_id"],
            json.dumps(envelope, separators=(",", ":")),
            "queued",
            now,
            now,
        ),
    )
    row = db.execute(
        "SELECT id FROM tasks WHERE idempotency_key=?", (envelope["idempotency_key"],)
    ).fetchone()
    return str(row["id"])


def claim(
    db: sqlite3.Connection, target: str, owner: str, lease_seconds: int = 60
) -> dict | None:
    now = int(time.time())
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT * FROM tasks WHERE target=? AND (state='queued' OR (state='leased' AND lease_until<?)) ORDER BY created_at LIMIT 1",
            (target, now),
        ).fetchone()
        if not row:
            db.execute("COMMIT")
            return None
        lease_until = now + lease_seconds
        db.execute(
            "UPDATE tasks SET state='leased',attempt=attempt+1,lease_owner=?,lease_until=?,updated_at=? WHERE id=?",
            (owner, lease_until, now, row["id"]),
        )
        db.execute("COMMIT")
        return json.loads(row["envelope_json"])
    except Exception:
        db.execute("ROLLBACK")
        raise


def complete(
    db: sqlite3.Connection, task_id: str, owner: str, result: dict, success: bool
) -> None:
    now = int(time.time())
    cur = db.execute(
        "UPDATE tasks SET state=?,result_json=?,lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=? AND state='leased' AND lease_owner=?",
        ("succeeded" if success else "failed", json.dumps(result), now, task_id, owner),
    )
    if cur.rowcount != 1:
        raise RuntimeError("lease is not owned by this worker")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, default=Path("peer-broker.sqlite3"))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit")
    s.add_argument("envelope", type=Path)
    c = sub.add_parser("claim")
    c.add_argument("target")
    c.add_argument("owner")
    d = sub.add_parser("complete")
    d.add_argument("task_id")
    d.add_argument("owner")
    d.add_argument("result", type=Path)
    d.add_argument("--fail", action="store_true")
    args = p.parse_args()
    db = connect(args.db)
    if args.cmd == "submit":
        print(submit(db, json.loads(args.envelope.read_text())))
    elif args.cmd == "claim":
        print(json.dumps(claim(db, args.target, args.owner), indent=2))
    else:
        complete(
            db,
            args.task_id,
            args.owner,
            json.loads(args.result.read_text()),
            not args.fail,
        )


if __name__ == "__main__":
    main()

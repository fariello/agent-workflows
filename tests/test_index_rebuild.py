"""Behavioral tests for `aw index rebuild` and the typed `aw index <type>` cache refresh (IPD `1ajqaa`).

Each case builds a temp git repository, drives `cli.main`, and asserts on exit codes, parsed
`aw.agent/v1` JSON and filesystem state. No test reads production source (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta, cli, meta_cli

pytestmark = pytest.mark.core


def _run(repo: Path, argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        rc = cli.main(["index"] + argv + ["--dir", str(repo)])
    return rc, out.getvalue(), err.getvalue()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def _plan(repo: Path, id6: str, order: int, status: str = "approved") -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261106-rbset-{order:02d}-{id6}-plan-{id6}.ipd.md"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# IPD: Plan {id6}\n\n- Id: {id6}\n- Status: {status}\n- Set: rbset\n- Order: {order}\n\n"
        "## Workflow history\n- 2026-11-06 approved (aw set): ok\n\n## Goal\n\nBody.\n",
        encoding="utf-8",
    )
    return p


def _repo(tmp_path: Path) -> Path:
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    _plan(repo, "rb0001", 1)
    _plan(repo, "rb0002", 2)
    walk = repo / ".aw" / "records" / "walkthroughs"
    walk.mkdir(parents=True)
    (walk / "20261106-rbset-01-rb0001-x.walkthrough.md").write_text(
        "# Walkthrough\n\n- Id: rbw001\n\nText.\n", encoding="utf-8"
    )
    rev = repo / ".aw" / "records" / "reviews"
    rev.mkdir(parents=True)
    (rev / "20261106-rbset-01-rb0001-plan-rb0001.review.md").write_text(
        "# Review\n\n- Subject-Id: rb0001\n- Verdict: APPROVE\n\n## Round 1\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "-m",
        "init",
    )
    return repo


def _invalid_log(repo: Path) -> None:
    meta = repo / ".aw" / "records" / "meta"
    meta.mkdir(parents=True, exist_ok=True)
    ev = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "t"},
        "op": "note",
        "message": "starts at seq 2",
    }
    (meta / "bd0001.jsonl").write_text(artifact_meta.encode_event(ev), encoding="utf-8")


def _record(out: str) -> dict:
    return json.loads(out.strip().splitlines()[-1])


def test_a_rebuild_reports_counts_and_creates_cache(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    rc, out, _ = _run(repo, ["rebuild", "--agent"])
    rec = _record(out)
    assert rc == 0 and rec["exit"] == 0 and rec["outcome"] == "ok"
    ev = set(rec["evidence"])
    assert {
        "artifacts:2",
        "walkthroughs:1",
        "review_files:1",
        "events:0",
        "valid:3",
        "invalid:0",
    } <= ev
    assert (repo / ".aw" / "state" / "index.db").is_file()
    rc_j, out_j, _ = _run(repo, ["rebuild", "--json"])
    data = json.loads(out_j)["data"]
    assert (
        rc_j == 0 and data["cache"] == ".aw/state/index.db" and data["artifacts"] == 2
    )


def test_b_rebuild_writes_no_tracked_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = _git(repo, "status", "--porcelain")
    rc, _, _ = _run(repo, ["rebuild", "--agent"])
    after = _git(repo, "status", "--porcelain")
    assert rc == 0
    assert before == after == ""


def test_c_garbage_cache_is_replaced(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    db = repo / ".aw" / "state" / "index.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_bytes(b"this is not a sqlite database")
    rc, out, _ = _run(repo, ["rebuild", "--agent"])
    assert rc == 0 and _record(out)["outcome"] == "ok"
    assert db.read_bytes()[:15] == b"SQLite format 3"


def test_d_typed_index_refreshes_cache(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert _run(repo, ["rebuild", "--agent"])[0] == 0
    _plan(repo, "rb0003", 3)
    rc, _, _ = _run(repo, ["plans", "--agent"])
    assert rc == 0
    ctx = meta_cli.meta_context(repo)
    # Read the cache file directly (no freshness pass): the typed spelling already loaded rb0003.
    db = ctx.state_root / "index.db"
    import sqlite3

    conn = sqlite3.connect(str(db))
    try:
        ids = {r[0] for r in conn.execute("SELECT id6 FROM artifacts").fetchall()}
    finally:
        conn.close()
    assert "rb0003" in ids
    assert "rb0003" in {s.id6 for s in artifact_meta.query(project_context=ctx)}


def test_f_invalid_log_does_not_change_typed_index_output_or_exit(
    tmp_path: Path,
) -> None:
    clean = _repo(tmp_path / "clean")
    dirty = _repo(tmp_path / "dirty")
    _invalid_log(dirty)
    rc_c, out_c, _ = _run(clean, ["plans", "--agent"])
    rc_d, out_d, _ = _run(dirty, ["plans", "--agent"])
    assert rc_c == rc_d == 0
    assert _record(out_c) == _record(out_d)


def test_e_rebuild_reports_invalid_record_as_finding(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _invalid_log(repo)
    rc, out, _ = _run(repo, ["rebuild", "--agent"])
    rec = _record(out)
    assert rc == 1 and rec["exit"] == 1 and rec["outcome"] == "findings"
    assert "invalid:1" in rec["evidence"]
    assert rec["diagnostics"] == [
        {"location": "meta/bd0001.jsonl", "rule": "invalid-record"}
    ]
    rc_h, out_h, _ = _run(repo, ["rebuild"])
    assert rc_h == 1 and "invalid: 1" in out_h and "bd0001" in out_h


def test_rebuild_outside_a_project_refuses_and_writes_nothing(tmp_path: Path) -> None:
    bare = (tmp_path / "bare").resolve()
    bare.mkdir()
    _git(bare, "init", "-q")
    rc, out, _ = _run(bare, ["rebuild", "--agent"])
    rec = _record(out)
    assert rc == 2 and rec["exit"] == 2 and rec["outcome"] == "cannot-run"
    assert [p.name for p in bare.iterdir()] == [".git"]

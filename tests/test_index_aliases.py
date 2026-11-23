"""Behavioral tests for the typed `aw index` spellings as aliases of `aw index rebuild` (IPD `tqknnc`).

Spec `4sd62s` 4.5 keeps `aw index plans|research|prompts` (and `aw index all`, and the legacy
`aw research index`) only as informational aliases of `aw index rebuild`. Each case builds a temp
git repository with `tests/record_builder.py`, drives `cli.main`, and asserts on exit codes, parsed
`aw.agent/v1` records, stderr, and filesystem state. No test reads production source
(GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import agent_schema, cli
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

NOTICE_TAIL = "is an alias of `aw index rebuild`; INDEX files are no longer generated"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def _repo(tmp_path: Path) -> Path:
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    plans = repo / ".aw" / "records" / "plans" / "pending"
    plans.mkdir(parents=True)
    (plans / "20261106-alset-01-al0001-plan-al0001.ipd.md").write_text(
        RecordBuilder().plan(
            title="Plan al0001",
            id6="al0001",
            status="approved",
            set="alset",
            order=1,
            history=["- 2026-11-06 approved (aw set): ok"],
            body="## Goal\n\nBody.",
            text_only=True,
        ),
        encoding="utf-8",
    )
    prompts = repo / ".aw" / "records" / "prompts" / "pending"
    prompts.mkdir(parents=True)
    (prompts / "20260701-alset-01-al0002-prompt.prompt.md").write_text(
        RecordBuilder().prompt(
            id6="al0002",
            prompt_kind="research",
            set="alset",
            order=1,
            status="pending",
            when="2026-07-01",
            body="Prompt body.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )
    research = repo / ".aw" / "records" / "research"
    research.mkdir(parents=True)
    (research / "20260701-alset-01-al0003-notes.research-report.md").write_text(
        RecordBuilder().research(
            id6="al0003",
            when="2026-07-01",
            set="alset",
            order=1,
            status="active",
            topic=["test"],
            body="# Research notes\n\nResearch body.\n",
            text_only=True,
        ),
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


def _run(repo: Path, argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        rc = cli.main(argv + ["--dir", str(repo)])
    return rc, out.getvalue(), err.getvalue()


def _record(out: str) -> dict:
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1, f"expected exactly one agent record, got {out!r}"
    rec = json.loads(lines[0])
    assert agent_schema.validate_agent_record(rec) == []
    return rec


def _index_files(repo: Path) -> List[str]:
    return sorted(
        p.relative_to(repo).as_posix() for p in repo.rglob("INDEX.*") if p.is_file()
    )


def _assert_alias(repo: Path, argv: List[str], spelling: str) -> None:
    before = _git(repo, "status", "--porcelain", "--ignored")
    assert _index_files(repo) == []

    rc, out, _ = _run(repo, argv + ["--agent"])
    rec = _record(out)
    assert rc == 0 and rec["exit"] == 0 and rec["outcome"] == "ok"
    assert rec["cmd"] == "index rebuild"
    assert {"location": spelling, "rule": "index-alias"} in rec["diagnostics"]
    assert rec["findings_by_severity"]["info"] >= 1
    assert rec["findings_by_severity"]["error"] == 0

    rc_j, out_j, _ = _run(repo, argv + ["--json"])
    doc = json.loads(out_j)
    notices = [d for d in doc["diagnostics"] if d["rule"] == "index-alias"]
    assert rc_j == 0 and len(notices) == 1
    assert notices[0]["severity"] == "info"
    assert notices[0]["detail"] == f"`{spelling}` {NOTICE_TAIL}"

    rc_h, out_h, err_h = _run(repo, argv)
    assert rc_h == 0
    assert err_h.count(NOTICE_TAIL) == 1
    assert f"`{spelling}` {NOTICE_TAIL}" in err_h
    assert NOTICE_TAIL not in out_h

    assert _index_files(repo) == []
    after = _git(repo, "status", "--porcelain", "--ignored")
    # The only ignored entry is the gitignored cache root, before and after.
    assert after.replace("!! .aw/state/\n", "") == before.replace("!! .aw/state/\n", "")
    assert _git(repo, "status", "--porcelain") == ""
    assert (repo / ".aw" / "state" / "index.db").is_file()


def test_index_plans_is_an_alias(tmp_path: Path) -> None:
    _assert_alias(_repo(tmp_path), ["index", "plans"], "aw index plans")


def test_index_research_is_an_alias(tmp_path: Path) -> None:
    _assert_alias(_repo(tmp_path), ["index", "research"], "aw index research")


def test_index_prompts_is_an_alias(tmp_path: Path) -> None:
    _assert_alias(_repo(tmp_path), ["index", "prompts"], "aw index prompts")


def test_index_all_is_one_alias_with_one_notice(tmp_path: Path) -> None:
    _assert_alias(_repo(tmp_path), ["index", "all"], "aw index all")


def test_research_index_is_an_alias(tmp_path: Path) -> None:
    _assert_alias(_repo(tmp_path), ["research", "index"], "aw research index")


def test_limit_is_accepted_and_ignored(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _assert_alias(repo, ["index", "plans", "--limit", "3"], "aw index plans")
    _assert_alias(repo, ["research", "index", "--limit", "3"], "aw research index")


def test_check_runs_content_drift_and_fails_on_dangling_citation(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    clean_rc, clean_out, clean_err = _run(
        repo, ["index", "plans", "--check", "--agent"]
    )
    clean = _record(clean_out)
    assert clean_rc == 0 and clean["exit"] == 0 and clean["outcome"] == "conforms"
    assert clean["findings_by_severity"]["error"] == 0
    assert clean["findings_by_severity"]["warning"] == 0
    assert {"location": "aw index plans", "rule": "index-alias"} in clean["diagnostics"]
    assert not any(
        d["rule"].startswith("check.stale-index-") for d in clean["diagnostics"]
    )
    clean_h_rc, clean_h_out, clean_h_err = _run(repo, ["index", "plans", "--check"])
    assert clean_h_rc == 0 and clean_h_out == "plans index --check: clean\n"
    assert clean_h_err.count(NOTICE_TAIL) == 1

    (repo / "DECISIONS.md").write_text("See PLAN-zzzzzz here.\n", encoding="utf-8")
    # `dangling-citation` is registered `info`, so plant one `error`-severity companion, a
    # clustered plan whose name id disagrees with its metadata Id, to make the gate fail.
    bad = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261106-alset-02-al9999-plan-mismatch.ipd.md"
    )
    bad.write_text(
        RecordBuilder().plan(
            title="Plan al0004",
            id6="al0004",
            status="approved",
            set="alset",
            order=2,
            history=["- 2026-11-06 approved (aw set): ok"],
            body="## Goal\n\nBody.",
            text_only=True,
        ),
        encoding="utf-8",
    )
    rc, out, _ = _run(repo, ["index", "plans", "--check", "--agent"])
    rec = _record(out)
    rules = [d["rule"] for d in rec["diagnostics"]]
    assert rc == 1 and rec["exit"] == 1 and rec["outcome"] == "findings"
    assert "dangling-citation" in rules
    assert "name-metadata-mismatch" in rules
    assert "index-alias" in rules
    assert not any(r.startswith("check.stale-index-") for r in rules)
    assert {"location": "DECISIONS.md:1", "rule": "dangling-citation"} in rec[
        "diagnostics"
    ]

    rc_h, out_h, _ = _run(repo, ["index", "plans", "--check"])
    assert rc_h == 1
    assert "dangling-citation: PLAN-zzzzzz" in out_h
    assert _index_files(repo) == []

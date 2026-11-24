"""Behavioral pinning tests for `aw attention` across all six tracked trees (IPD dqutt8 E-01).

Pins observable behavior of `agent_workflows.attention` on `tmp_path` fixture repositories
before moving `attention` metadata and history reads onto `artifact_meta`: per-tree status
mapping (`attention.missing-status`, `attention.unknown-status`, `attention.disposition-mismatch`),
`id`, `priority`, `blocks_release`, `readiness`, `last_history_at` (newest record by
`artifact_meta._newest_history_record`), gate fields, open-question counts,
`detail_kind`/`detail_text`, `item_dependencies`, and `aw attention --check --agent` exit code
with one violation. Calls real `attention` and `cli` functions and never reads production source.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import attention as att
from agent_workflows import attention_contract as A
from agent_workflows import cli
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    return repo


def _item_by_path(items: list[att.Item], rel: str) -> att.Item:
    matches = [it for it in items if it.path == rel]
    assert len(matches) == 1, f"expected 1 item for {rel}, got {matches}"
    return matches[0]


def test_plans_tree_attention_pin(tmp_path: Path) -> None:
    """Plans tree: status mapping, fields, newest history, OQs, detail, and drift rules."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    executed_dir = repo / ".aw" / "records" / "plans" / "executed"
    pending_dir.mkdir(parents=True)
    executed_dir.mkdir(parents=True)

    valid_rel = ".aw/records/plans/pending/20261010-pinset-01-pln001-valid-plan.ipd.md"
    (repo / valid_rel).write_text(
        RecordBuilder().plan(
            title="Valid Plan Heading",
            when="2026-10-10",
            plan_role="child",
            status="reviewed",
            readiness="go-pending-approval",
            priority="high",
            blocks_release="next",
            item_dependencies="executed:dep001",
            set="pinset",
            order=1,
            id6="pln001",
            history=[
                "- 2026-10-12 reviewed (tester): reviewed plan",
                "- 2026-10-10 draft (tester): created plan",
            ],
            body=(
                "## Detailed Implementation Checklist (TODO)\n"
                "- [x] E-01 done step\n"
                "- [ ] E-02 todo step\n\n"
                "## Open questions\n"
                "### OQ-01: Open question one\n"
                "- Status: open\n\n"
                "### RQ-01: Resolved question one\n"
                "- Status: resolved\n\n"
                "## Validation and cross-check\n"
                "- [x] V-01 validates E-01"
            ),
            raw_fields={
                "Concern": "Pin attention plan fields.",
                "Scope": "Plans tree coverage.",
            },
            text_only=True,
        ),
        encoding="utf-8",
    )

    multi_rel = ".aw/records/plans/executed/20261001-pinset-02-pln002-multi-exec.ipd.md"
    (repo / multi_rel).write_text(
        RecordBuilder().plan(
            title="Legacy Executed Plan",
            when="2026-10-01",
            set="pinset",
            order=2,
            id6="pln002",
            history=["- 2026-10-02 executed (tester): done"],
            raw_fields={"Status": "EXECUTED 2026-10-02 completed"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    mismatch_rel = (
        ".aw/records/plans/executed/20261002-pinset-03-pln003-mismatch.ipd.md"
    )
    (repo / mismatch_rel).write_text(
        RecordBuilder().plan(
            title="Disposition Mismatch Plan",
            when="2026-10-02",
            status="superseded",
            set="pinset",
            order=3,
            id6="pln003",
            history=["- 2026-10-02 superseded (tester): replaced"],
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = ".aw/records/plans/pending/20261003-pinset-04-pln004-no-status.ipd.md"
    (repo / missing_rel).write_text(
        RecordBuilder().plan(
            title="Missing Status Plan",
            set="pinset",
            id6="pln004",
            raw_fields={"Status": None},
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/plans/pending/20261004-pinset-05-pln005-bad-status.ipd.md"
    )
    (repo / unknown_rel).write_text(
        RecordBuilder().plan(
            title="Unknown Status Plan",
            set="pinset",
            id6="pln005",
            raw_fields={"Status": "bogus-state"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "plans"
    assert valid.id == "pln001"
    assert valid.native_status == "reviewed"
    assert valid.attention_class == A.READY
    assert valid.priority == "high"
    assert valid.blocks_release == "next"
    assert valid.readiness == "go-pending-approval"
    assert valid.last_history_at == "2026-10-12"
    assert valid.gate is None
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "scope"
    assert valid.detail_text == "Plans tree coverage."
    assert valid.item_dependencies == ("executed:dep001",)
    assert valid.exec_progress == (1, 2)
    assert valid.valid_progress == (1, 1)

    multi = _item_by_path(items, multi_rel)
    assert multi.id == "pln002"
    assert multi.native_status == "executed"
    assert multi.attention_class == A.DONE
    assert multi.last_history_at == "2026-10-02"

    mismatch = _item_by_path(items, mismatch_rel)
    assert mismatch.native_status == "superseded"
    assert mismatch.attention_class == A.PARKED

    missing_deg = _item_by_path(items, missing_rel)
    assert missing_deg.id == "pln004"
    assert missing_deg.native_status == "-"
    assert missing_deg.attention_class == A.BLOCKED

    unknown_deg = _item_by_path(items, unknown_rel)
    assert unknown_deg.id == "pln005"
    assert unknown_deg.native_status == "-"
    assert unknown_deg.attention_class == A.BLOCKED

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (mismatch_rel, "attention.disposition-mismatch") in drift_pairs
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_specs_tree_attention_pin(tmp_path: Path) -> None:
    """Specs tree: status mapping, gate fields, priority, blocks_release, history, OQs, detail."""
    repo = _init_repo(tmp_path)
    specs_dir = repo / ".aw" / "records" / "specs"
    specs_dir.mkdir(parents=True)

    valid_rel = ".aw/records/specs/20261010-pinset-01-spc001-deferred-spec.spec.md"
    (repo / valid_rel).write_text(
        RecordBuilder().spec(
            title="Deferred Spec",
            id6="spc001",
            status="deferred",
            priority="high",
            blocks_release="next",
            gate_kind="decision",
            gate_ref="D42",
            gate_summary="Waiting for architecture signoff",
            history=[
                "- 2026-10-14 deferred (tester): deferred pending D42",
                "- 2026-10-10 draft (tester): created spec",
            ],
            body=(
                "## Open questions\n"
                "### OQ-01: Unresolved spec question\n"
                "- Status: open\n\n"
                "### OQ-02: Resolved spec question\n"
                "- Status: resolved"
            ),
            raw_fields={
                "Readiness": "go",
                "Summary": "Pin spec attention reader fields.",
            },
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = ".aw/records/specs/20261011-pinset-02-spc002-no-status.spec.md"
    (repo / missing_rel).write_text(
        RecordBuilder().spec(
            title="Missing Status Spec",
            id6="spc002",
            history=["- 2026-10-11 draft (tester): created"],
            raw_fields={"Status": None},
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = ".aw/records/specs/20261012-pinset-03-spc003-bad-status.spec.md"
    (repo / unknown_rel).write_text(
        RecordBuilder().spec(
            title="Unknown Status Spec",
            id6="spc003",
            history=["- 2026-10-12 draft (tester): created"],
            raw_fields={"Status": "mythical"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "specs"
    assert valid.id == "spc001"
    assert valid.native_status == "deferred"
    assert valid.attention_class == A.BLOCKED
    assert valid.priority == "high"
    assert valid.blocks_release == "next"
    assert valid.readiness == "go"
    assert valid.last_history_at == "2026-10-14"
    assert valid.gate == {
        "kind": "decision",
        "ref": "D42",
        "summary": "Waiting for architecture signoff",
    }
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "summary"
    assert valid.detail_text == "Pin spec attention reader fields."

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_backlog_tree_attention_pin(tmp_path: Path) -> None:
    """Backlog tree: status mapping, gate fields, priority, blocks_release, history, OQs, detail."""
    repo = _init_repo(tmp_path)
    blocked_dir = repo / ".aw" / "records" / "backlog" / "blocked"
    open_dir = repo / ".aw" / "records" / "backlog" / "open"
    blocked_dir.mkdir(parents=True)
    open_dir.mkdir(parents=True)

    valid_rel = ".aw/records/backlog/blocked/20261010-pinset-01-bkl001-gated.backlog.md"
    (repo / valid_rel).write_text(
        RecordBuilder().backlog(
            id6="bkl001",
            status="blocked",
            priority="medium",
            blocks_release="next",
            work_kind="feature",
            gate_kind="date",
            gate_ref="2026-12-01",
            summary="Pin backlog attention reader fields.",
            history=[
                "- 2026-10-15 blocked (tester): gated on date",
                "- 2026-10-10 open (tester): created",
            ],
            body=(
                "## Open questions\n"
                "### OQ-01: Open backlog question\n"
                "- Status: open\n\n"
                "### RQ-01: Answered backlog question\n"
                "- Status: answered"
            ),
            raw_fields={"Readiness": "go-pending-approval"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = (
        ".aw/records/backlog/open/20261011-pinset-02-bkl002-no-status.backlog.md"
    )
    (repo / missing_rel).write_text(
        RecordBuilder().backlog(
            id6="bkl002",
            priority="low",
            raw_fields={"Status": None},
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/backlog/open/20261012-pinset-03-bkl003-bad-status.backlog.md"
    )
    (repo / unknown_rel).write_text(
        RecordBuilder().backlog(
            id6="bkl003", raw_fields={"Status": "sideways"}, text_only=True
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "backlog"
    assert valid.id == "bkl001"
    assert valid.native_status == "blocked"
    assert valid.attention_class == A.BLOCKED
    assert valid.priority == "medium"
    assert valid.blocks_release == "next"
    assert valid.readiness == "go-pending-approval"
    assert valid.last_history_at == "2026-10-15"
    assert valid.gate == {"kind": "date", "ref": "2026-12-01"}
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "summary"
    assert valid.detail_text == "Pin backlog attention reader fields."

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_research_tree_attention_pin(tmp_path: Path) -> None:
    """Research tree: YAML frontmatter status, priority, blocks_release, history, OQs, detail."""
    repo = _init_repo(tmp_path)
    res_dir = repo / ".aw" / "records" / "research"
    res_dir.mkdir(parents=True)

    valid_rel = (
        ".aw/records/research/20261010-pinset-01-res001-active-study.findings.md"
    )
    (repo / valid_rel).write_text(
        RecordBuilder().research(
            id6="res001",
            research_kind="findings",
            status="active",
            priority="high",
            summary="Pin research attention reader fields.",
            raw_fields={"blocks-release": "next"},
            body=(
                "\n# Research: Active Study\n\n"
                "## Workflow history\n"
                "- 2026-10-16 active (tester): resumed study\n"
                "- 2026-10-10 todo (tester): opened study\n\n"
                "## Open questions\n"
                "### OQ-01: Unresolved research question\n"
                "- Status: open\n\n"
                "### RQ-01: Resolved research question\n"
                "- Status: resolved\n"
            ),
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = ".aw/records/research/20261011-pinset-02-res002-no-status.findings.md"
    (repo / missing_rel).write_text(
        RecordBuilder().research(
            id6="res002",
            research_kind="findings",
            raw_fields={"status": None},
            body="\n# Research: Missing Status\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/research/20261012-pinset-03-res003-bad-status.findings.md"
    )
    (repo / unknown_rel).write_text(
        RecordBuilder().research(
            id6="res003",
            research_kind="findings",
            body="\n# Research: Bad Status\n",
            raw_fields={"status": "limbo"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "research"
    assert valid.id == "res001"
    assert valid.native_status == "active"
    assert valid.attention_class == A.ACTIVE
    assert valid.priority == "high"
    assert valid.blocks_release == "next"
    assert valid.readiness is None
    assert valid.last_history_at == "2026-10-16"
    assert valid.gate is None
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "summary"
    assert valid.detail_text == "Pin research attention reader fields."

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_releases_tree_attention_pin(tmp_path: Path) -> None:
    """Releases tree: status mapping, id, newest history, OQs, detail, missing/unknown drift."""
    repo = _init_repo(tmp_path)
    rel_dir = repo / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True)

    valid_rel = ".aw/records/releases/20261010-pinset-01-rel001-v1-0-0.release.md"
    (repo / valid_rel).write_text(
        RecordBuilder().release(
            id6="rel001",
            version="v1.0.0",
            status="planned",
            summary="Pin release attention reader fields.",
            history=[
                "- 2026-10-17 planned (tester): scheduled release",
                "- 2026-10-10 planned (tester): drafted release",
            ],
            body=(
                "# Release: v1.0.0\n\n"
                "## Open questions\n"
                "### OQ-01: Open release question\n"
                "- Status: open\n\n"
                "### RQ-01: Closed release question\n"
                "- Status: closed\n"
            ),
            raw_fields={"Summary": "Pin release attention reader fields."},
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = ".aw/records/releases/20261011-pinset-02-rel002-no-status.release.md"
    (repo / missing_rel).write_text(
        RecordBuilder().release(
            id6="rel002",
            version="Missing Status",
            raw_fields={"Status": None},
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = ".aw/records/releases/20261012-pinset-03-rel003-bad-status.release.md"
    (repo / unknown_rel).write_text(
        RecordBuilder().release(
            version="Unknown Status",
            id6="rel003",
            raw_fields={"Status": "aborted"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "releases"
    assert valid.id == "rel001"
    assert valid.native_status == "planned"
    assert valid.attention_class == A.READY
    assert valid.priority is None
    assert valid.blocks_release is None
    assert valid.readiness is None
    assert valid.last_history_at == "2026-10-17"
    assert valid.gate is None
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "summary"
    assert valid.detail_text == "Pin release attention reader fields."

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_prompts_tree_attention_pin(tmp_path: Path) -> None:
    """Prompts tree: disposition mapping, comment id, newest history, OQs, detail, drift."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "prompts" / "pending"
    bogus_dir = repo / ".aw" / "records" / "prompts" / "weird"
    pending_dir.mkdir(parents=True)
    bogus_dir.mkdir(parents=True)

    valid_rel = ".aw/records/prompts/pending/20261010-pinset-01-prm001-sample.prompt.md"
    (repo / valid_rel).write_text(
        RecordBuilder().prompt(
            prompt_kind="research",
            id6="prm001",
            set="pinset",
            status="pending",
            raw_fields={"Short-Description": None},
            body=(
                "# Prompt: Pin prompt attention reader fields.\n\n"
                "## Workflow history\n"
                "- 2026-10-18 pending (tester): staged prompt\n"
                "- 2026-10-10 pending (tester): created prompt\n\n"
                "## Open questions\n"
                "### OQ-01: Open prompt question\n"
                "- Status: open\n\n"
                "### RQ-01: Resolved prompt question\n"
                "- Status: resolved\n"
            ),
            text_only=True,
        ),
        encoding="utf-8",
    )

    missing_rel = ".aw/records/prompts/20261011-pinset-02-prm002-unbucketed.prompt.md"
    (repo / missing_rel).write_text(
        RecordBuilder().prompt(
            prompt_kind="research",
            id6="prm002",
            set="pinset",
            status="pending",
            body="# Prompt: Unbucketed\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/prompts/weird/20261012-pinset-03-prm003-bad-bucket.prompt.md"
    )
    (repo / unknown_rel).write_text(
        RecordBuilder().prompt(
            prompt_kind="research",
            id6="prm003",
            set="pinset",
            status="pending",
            raw_fields={"Status": "weird"},
            body="# Prompt: Unknown Bucket\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)

    valid = _item_by_path(items, valid_rel)
    assert valid.tree == "prompts"
    assert valid.id == "prm001"
    assert valid.native_status == "pending"
    assert valid.attention_class == A.READY
    assert valid.priority is None
    assert valid.blocks_release is None
    assert valid.readiness is None
    assert valid.last_history_at == "2026-10-18"
    assert valid.gate is None
    assert valid.oqs == 1
    assert valid.rqs == 1
    assert valid.detail_kind == "title"
    assert valid.detail_text == "Pin prompt attention reader fields."

    drift_pairs = {(d.location, d.rule) for d in drift}
    assert (missing_rel, "attention.missing-status") in drift_pairs
    assert (unknown_rel, "attention.unknown-status") in drift_pairs


def test_check_agent_exit_code_with_one_violation(tmp_path: Path) -> None:
    """`aw attention --check --agent` exits 1 and emits a findings record with one violation."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True)

    (pending_dir / "20261010-pinset-01-chk001-ok.ipd.md").write_text(
        RecordBuilder().plan(
            title="Clean Plan",
            when="2026-10-10",
            status="draft",
            set="pinset",
            order=1,
            id6="chk001",
            history=["- 2026-10-10 draft (tester): created"],
            text_only=True,
        ),
        encoding="utf-8",
    )
    bad_rel = ".aw/records/plans/pending/20261011-pinset-02-chk002-bad.ipd.md"
    (repo / bad_rel).write_text(
        RecordBuilder().plan(
            title="Broken Plan",
            set="pinset",
            id6="chk002",
            raw_fields={"Status": None},
            text_only=True,
        ),
        encoding="utf-8",
    )

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli.main(["attention", "--dir", str(repo), "--check", "--agent"])

    assert rc == 1
    lines = [ln for ln in stdout_buf.getvalue().splitlines() if ln.strip()]
    assert lines, f"expected agent JSONL output, stderr={stderr_buf.getvalue()!r}"
    records = [json.loads(ln) for ln in lines]
    result_rec = next(r for r in records if r.get("kind") == "result")
    assert result_rec["exit"] == 1
    assert result_rec["outcome"] == "findings"
    assert result_rec["findings"] == 1
    diagnostics = result_rec.get("diagnostics") or []
    assert any(
        d.get("rule") == "attention.missing-status" and d.get("location") == bad_rel
        for d in diagnostics
    )


def test_incomplete_query_record_becomes_missing_status_violation(
    tmp_path: Path,
) -> None:
    """An `incomplete` record from `artifact_meta.query` becomes `attention.missing-status` (dqutt8 E-02)."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    meta_dir = repo / ".aw" / "records" / "meta"
    pending_dir.mkdir(parents=True)
    meta_dir.mkdir(parents=True)

    # 1. Valid plan for control
    ok_rel = ".aw/records/plans/pending/20261010-pinset-01-inc001-ok.ipd.md"
    (repo / ok_rel).write_text(
        RecordBuilder().plan(
            title="Control Plan",
            when="2026-10-10",
            status="draft",
            set="pinset",
            id6="inc001",
            text_only=True,
        ),
        encoding="utf-8",
    )

    # 2. Plan with a corrupt authoritative log (has both .md mirror and invalid meta/<id6>.jsonl)
    bad_rel = ".aw/records/plans/pending/20261011-pinset-02-inc002-corrupt.ipd.md"
    (repo / bad_rel).write_text(
        RecordBuilder().plan(
            title="Corrupt Log Plan",
            when="2026-10-11",
            status="approved",
            set="pinset",
            id6="inc002",
            text_only=True,
        ),
        encoding="utf-8",
    )
    (meta_dir / "inc002.jsonl").write_text("{not valid json\n", encoding="utf-8")

    # 3. Log-only corrupt record (no .md file on disk)
    (meta_dir / "inc003.jsonl").write_text("{also broken\n", encoding="utf-8")

    items, drift = att.scan(repo)

    # Control item is valid; inc002 must NOT be served as approved from its .md mirror
    ok_item = _item_by_path(items, ok_rel)
    assert ok_item.native_status == "draft"
    bad_item = _item_by_path(items, bad_rel)
    assert bad_item.native_status == "-"
    assert bad_item.attention_class == A.BLOCKED

    missing_drifts = [d for d in drift if d.rule == "attention.missing-status"]
    assert any(d.location == bad_rel and "inc002" in d.detail for d in missing_drifts)
    assert any("inc003" in d.detail for d in missing_drifts)


def test_short_description_wins_over_extract_detail_fallback(tmp_path: Path) -> None:
    """D-3: cached `short_description` wins when present; `_extract_detail` stays as fallback."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True)

    with_sd_rel = ".aw/records/plans/pending/20261010-pinset-01-sd0001-with-sd.ipd.md"
    (repo / with_sd_rel).write_text(
        RecordBuilder().plan(
            title="With Short Description",
            when="2026-10-10",
            status="draft",
            short_description="Crisp one-line description.",
            set="pinset",
            id6="sd0001",
            text_only=True,
        ),
        encoding="utf-8",
    )

    no_sd_rel = ".aw/records/plans/pending/20261011-pinset-02-sd0002-no-sd.ipd.md"
    (repo / no_sd_rel).write_text(
        RecordBuilder().plan(
            title="Without Short Description",
            when="2026-10-11",
            status="draft",
            set="pinset",
            id6="sd0002",
            raw_fields={"Scope": "Fallback scope paragraph."},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)
    assert drift == []
    with_sd = _item_by_path(items, with_sd_rel)
    assert with_sd.detail_kind == "summary"
    assert with_sd.detail_text == "Crisp one-line description."

    no_sd = _item_by_path(items, no_sd_rel)
    assert no_sd.detail_kind == "scope"
    assert no_sd.detail_text == "Fallback scope paragraph."


def test_log_format_record_history_via_artifact_meta(tmp_path: Path) -> None:
    """Log-format record reads `last_history_at` via `artifact_meta.history` and `artifact_meta._last_history_at`."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    meta_dir = repo / ".aw" / "records" / "meta"
    pending_dir.mkdir(parents=True)
    meta_dir.mkdir(parents=True)

    rel = ".aw/records/plans/pending/20261010-pinset-01-log001-log-plan.ipd.md"
    (repo / rel).write_text(
        RecordBuilder().research(
            id6="log001",
            body="\n# IPD: Log Plan\n",
            raw_fields={"status": "reviewed"},
            text_only=True,
        ),
        encoding="utf-8",
    )
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-10-10T10:00:00Z",
            "actor": {"tool": "aw"},
            "op": "create",
            "path": "plans/pending/20261010-pinset-01-log001-log-plan.ipd.md",
            "fields": {
                "type": "ipd",
                "status": "draft",
                "set": "pinset",
                "priority": "high",
                "short_description": "Log-backed plan summary.",
            },
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-10-19T15:30:00Z",
            "actor": {"tool": "aw"},
            "op": "transition",
            "from": "draft",
            "to": "reviewed",
        },
    ]
    (meta_dir / "log001.jsonl").write_text(
        "".join(
            json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n"
            for ev in events
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)
    assert drift == []
    it = _item_by_path(items, rel)
    assert it.id == "log001"
    assert it.native_status == "reviewed"
    assert it.priority == "high"
    assert it.last_history_at == "2026-10-19"
    assert it.detail_text == "Log-backed plan summary."


def test_item_dependencies_preserved_for_backlog_and_spec(tmp_path: Path) -> None:
    """`attention.scan` preserves Item-Dependencies on backlog and spec records via artifact_meta."""
    repo = _init_repo(tmp_path)
    bkl_dir = repo / ".aw" / "records" / "backlog" / "open"
    spec_dir = repo / ".aw" / "records" / "specs"
    bkl_dir.mkdir(parents=True)
    spec_dir.mkdir(parents=True)

    bkl1_rel = ".aw/records/backlog/open/20261010-bkl001-01-bkl001-root.backlog.md"
    (repo / bkl1_rel).write_text(
        RecordBuilder().backlog(
            id6="bkl001",
            status="open",
            priority="high",
            item_dependencies="none",
            history=["- 2026-10-10 created (tester): root."],
            text_only=True,
        ),
        encoding="utf-8",
    )

    bkl2_rel = ".aw/records/backlog/open/20261011-bkl002-01-bkl002-child.backlog.md"
    (repo / bkl2_rel).write_text(
        RecordBuilder().backlog(
            id6="bkl002",
            status="open",
            priority="medium",
            item_dependencies="exists:backlog:bkl001",
            history=["- 2026-10-11 created (tester): child."],
            text_only=True,
        ),
        encoding="utf-8",
    )

    spec_rel = ".aw/records/specs/20261012-spc001-01-spc001-dependent.spec.md"
    (repo / spec_rel).write_text(
        RecordBuilder().spec(
            id6="spc001",
            status="draft",
            item_dependencies="exists:backlog:bkl002",
            history=["- 2026-10-12 created (tester): spec."],
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)
    assert drift == []
    bkl1 = _item_by_path(items, bkl1_rel)
    bkl2 = _item_by_path(items, bkl2_rel)
    spc1 = _item_by_path(items, spec_rel)
    assert bkl1.item_dependencies == ()
    assert bkl2.item_dependencies == ("exists:backlog:bkl001",)
    assert spc1.item_dependencies == ("exists:backlog:bkl002",)


def _write_log(meta_dir: Path, id6: str, events: list[dict[str, object]]) -> None:
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"{id6}.jsonl").write_text(
        "".join(
            json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n"
            for ev in events
        ),
        encoding="utf-8",
    )


def _run_attention_json(repo: Path) -> tuple[int, dict[str, object]]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli.main(["attention", "--dir", str(repo), "--all", "--format", "json"])
    raw = stdout_buf.getvalue()
    assert raw.strip(), f"expected JSON stdout, stderr={stderr_buf.getvalue()!r}"
    return rc, json.loads(raw)


def test_v2_log_backed_specs_valid_migrated_and_fresh(tmp_path: Path) -> None:
    """Migrated approved, freshly created, and valid deferred v2 specs validate cleanly."""
    repo = _init_repo(tmp_path)
    specs_dir = repo / ".aw" / "records" / "specs"
    meta_dir = repo / ".aw" / "records" / "meta"
    specs_dir.mkdir(parents=True)

    # 1. Migrated approved spec: stripped Markdown mirror + seq 0 checkpoint + op: legacy history
    approved_rel = (
        ".aw/records/specs/20261010-v2sp01-01-v2sp01-migrated-approved.spec.md"
    )
    (repo / approved_rel).write_text(
        "---\nid: v2sp01\ntype: spec\n---\n\n"
        "# Spec: Migrated Approved Spec\n\n"
        "## Summary\n\nMigrated v2 specification.\n",
        encoding="utf-8",
    )
    _write_log(
        meta_dir,
        "v2sp01",
        [
            {
                "v": 1,
                "seq": 0,
                "append": 0,
                "at": "2026-11-20T00:00:00Z",
                "actor": {"tool": "aw migrate metadata"},
                "op": "checkpoint",
                "path": "specs/20261010-v2sp01-01-v2sp01-migrated-approved.spec.md",
                "fields": {
                    "type": "spec",
                    "status": "approved",
                    "priority": "high",
                    "work_kind": "feature",
                    "last_history_day": "2026-10-14",
                },
            },
            {
                "v": 1,
                "seq": 1,
                "append": 0,
                "at": "2026-11-20T00:00:00Z",
                "actor": {"tool": "aw migrate metadata"},
                "op": "legacy",
                "source": "history",
                "position": 0,
                "ordering_confidence": "unknown",
                "observed_day": "2026-10-14",
                "line": "- 2026-10-14 approved (human): approved spec",
            },
        ],
    )

    # 2. Freshly created v2 spec: seq 1 op: create with no last_history_day field
    fresh_rel = ".aw/records/specs/20261018-v2sp02-01-v2sp02-fresh-create.spec.md"
    (repo / fresh_rel).write_text(
        "---\nid: v2sp02\ntype: spec\n---\n\n# Spec: Fresh Created Spec\n",
        encoding="utf-8",
    )
    _write_log(
        meta_dir,
        "v2sp02",
        [
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-10-18T12:34:56Z",
                "actor": {"tool": "aw"},
                "op": "create",
                "path": "specs/20261018-v2sp02-01-v2sp02-fresh-create.spec.md",
                "fields": {
                    "type": "spec",
                    "status": "draft",
                    "priority": "medium",
                    "work_kind": "chore",
                },
            }
        ],
    )

    # 3. Migrated deferred spec with valid gate_kind, gate_ref, and safe gate_summary
    deferred_rel = ".aw/records/specs/20261015-v2sp03-01-v2sp03-deferred-valid.spec.md"
    (repo / deferred_rel).write_text(
        "---\nid: v2sp03\ntype: spec\n---\n\n# Spec: Deferred Valid Spec\n",
        encoding="utf-8",
    )
    _write_log(
        meta_dir,
        "v2sp03",
        [
            {
                "v": 1,
                "seq": 0,
                "append": 0,
                "at": "2026-11-20T00:00:00Z",
                "actor": {"tool": "aw migrate metadata"},
                "op": "checkpoint",
                "path": "specs/20261015-v2sp03-01-v2sp03-deferred-valid.spec.md",
                "fields": {
                    "type": "spec",
                    "status": "deferred",
                    "gate_kind": "decision",
                    "gate_ref": "D42",
                    "gate_summary": "Waiting on D42 decision",
                    "last_history_day": "2026-10-15",
                },
            }
        ],
    )

    items, drift = att.scan(repo)
    assert drift == []

    approved_item = _item_by_path(items, approved_rel)
    assert approved_item.id == "v2sp01"
    assert approved_item.native_status == "approved"
    assert approved_item.last_history_at == "2026-10-14"
    assert approved_item.priority == "high"

    fresh_item = _item_by_path(items, fresh_rel)
    assert fresh_item.id == "v2sp02"
    assert fresh_item.native_status == "draft"
    assert fresh_item.last_history_at == "2026-10-18"
    assert fresh_item.priority == "medium"

    deferred_item = _item_by_path(items, deferred_rel)
    assert deferred_item.id == "v2sp03"
    assert deferred_item.native_status == "deferred"
    assert deferred_item.last_history_at == "2026-10-15"
    assert deferred_item.gate == {
        "kind": "decision",
        "ref": "D42",
        "summary": "Waiting on D42 decision",
    }

    rc, payload = _run_attention_json(repo)
    assert rc == 0
    assert payload["valid"] is True
    assert payload["violations"] == []
    by_id = {it["id"]: it for it in payload["items"]}  # type: ignore[index]
    assert by_id["v2sp01"]["native_status"] == "approved"
    assert by_id["v2sp01"]["last_history_at"] == "2026-10-14"
    assert by_id["v2sp02"]["native_status"] == "draft"
    assert by_id["v2sp02"]["last_history_at"] == "2026-10-18"
    assert by_id["v2sp03"]["native_status"] == "deferred"
    assert by_id["v2sp03"]["gate"] == {
        "kind": "decision",
        "ref": "D42",
        "summary": "Waiting on D42 decision",
    }


def test_v2_log_backed_specs_gate_history_status_and_vocab_violations(
    tmp_path: Path,
) -> None:
    """Log-backed specs enforce gate rules, history presence, status enum, and vocabularies."""
    repo = _init_repo(tmp_path)
    specs_dir = repo / ".aw" / "records" / "specs"
    meta_dir = repo / ".aw" / "records" / "meta"
    specs_dir.mkdir(parents=True)

    cases: list[tuple[str, str, dict[str, object]]] = [
        (
            "v2g001",
            "deferred-missing-gate",
            {
                "type": "spec",
                "status": "deferred",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g002",
            "deferred-bad-kind",
            {
                "type": "spec",
                "status": "deferred",
                "gate_kind": "bogus",
                "gate_ref": "D1",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g003",
            "deferred-bad-ref",
            {
                "type": "spec",
                "status": "deferred",
                "gate_kind": "date",
                "gate_ref": "not-a-date",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g004",
            "deferred-unsafe-ctrl",
            {
                "type": "spec",
                "status": "deferred",
                "gate_kind": "decision",
                "gate_ref": "D10",
                "gate_summary": "unsafe\x07summary",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g005",
            "deferred-unsafe-len",
            {
                "type": "spec",
                "status": "deferred",
                "gate_kind": "decision",
                "gate_ref": "D11",
                "gate_summary": "x" * (A.MAX_DESCRIPTIVE_LEN + 1),
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g006",
            "non-deferred-with-gate",
            {
                "type": "spec",
                "status": "approved",
                "gate_kind": "decision",
                "gate_ref": "D12",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g007",
            "checkpoint-only-no-history",
            {
                "type": "spec",
                "status": "approved",
            },
        ),
        (
            "v2g008",
            "unknown-status",
            {
                "type": "spec",
                "status": "mythical",
                "last_history_day": "2026-10-10",
            },
        ),
        (
            "v2g009",
            "invalid-priority-work-kind",
            {
                "type": "spec",
                "status": "draft",
                "priority": "urgent",
                "work_kind": "epic",
                "last_history_day": "2026-10-10",
            },
        ),
    ]

    rels: dict[str, str] = {}
    for idx, (id6, slug, fields) in enumerate(cases, start=1):
        rel = f".aw/records/specs/20261010-v2gate-{idx:02d}-{id6}-{slug}.spec.md"
        rels[id6] = rel
        (repo / rel).write_text(
            f"---\nid: {id6}\ntype: spec\n---\n\n# Spec: {slug}\n",
            encoding="utf-8",
        )
        _write_log(
            meta_dir,
            id6,
            [
                {
                    "v": 1,
                    "seq": 0,
                    "append": 0,
                    "at": "2026-11-20T00:00:00Z",
                    "actor": {"tool": "aw migrate metadata"},
                    "op": "checkpoint",
                    "path": rel.removeprefix(".aw/records/"),
                    "fields": fields,
                }
            ],
        )

    items, drift = att.scan(repo)
    by_loc: dict[str, set[str]] = {}
    for d in drift:
        by_loc.setdefault(d.location, set()).add(d.rule)

    assert by_loc[rels["v2g001"]] == {"attention.gate-missing"}
    assert by_loc[rels["v2g002"]] == {"attention.gate-malformed"}
    assert by_loc[rels["v2g003"]] == {"attention.gate-malformed"}
    assert by_loc[rels["v2g004"]] == {"attention.unsafe-field"}
    assert by_loc[rels["v2g005"]] == {"attention.unsafe-field"}
    assert by_loc[rels["v2g006"]] == {"attention.gate-forbidden"}
    # Checkpoint-only with no history: recognized as log-backed (no missing-status), flags history-missing
    assert by_loc[rels["v2g007"]] == {"attention.history-missing"}
    assert _item_by_path(items, rels["v2g007"]).native_status == "approved"
    # Unknown status: emits unknown-status and degrades item
    assert by_loc[rels["v2g008"]] == {"attention.unknown-status"}
    assert _item_by_path(items, rels["v2g008"]).native_status == "-"
    # Invalid priority and work_kind
    assert by_loc[rels["v2g009"]] == {"spec.priority-invalid", "spec.work-kind-invalid"}

    rc, payload = _run_attention_json(repo)
    assert rc == 1
    assert payload["valid"] is False
    v_pairs = {(v["location"], v["rule"]) for v in payload["violations"]}  # type: ignore[index]
    assert (rels["v2g001"], "attention.gate-missing") in v_pairs
    assert (rels["v2g002"], "attention.gate-malformed") in v_pairs
    assert (rels["v2g003"], "attention.gate-malformed") in v_pairs
    assert (rels["v2g004"], "attention.unsafe-field") in v_pairs
    assert (rels["v2g005"], "attention.unsafe-field") in v_pairs
    assert (rels["v2g006"], "attention.gate-forbidden") in v_pairs
    assert (rels["v2g007"], "attention.history-missing") in v_pairs
    assert (rels["v2g007"], "attention.missing-status") not in v_pairs
    assert (rels["v2g008"], "attention.unknown-status") in v_pairs
    assert (rels["v2g009"], "spec.priority-invalid") in v_pairs
    assert (rels["v2g009"], "spec.work-kind-invalid") in v_pairs


def test_legacy_spec_with_history_still_uses_validate_spec(tmp_path: Path) -> None:
    """Legacy Markdown specs with workflow history (`last_seq > 0`) stay on `specs.validate_spec`."""
    repo = _init_repo(tmp_path)
    specs_dir = repo / ".aw" / "records" / "specs"
    specs_dir.mkdir(parents=True)

    dup_rel = ".aw/records/specs/20261012-leg001-01-leg001-dup-bullet.spec.md"
    (repo / dup_rel).write_text(
        RecordBuilder().spec(
            title="Legacy Duplicate Bullet",
            id6="leg001",
            status="approved",
            history=[
                "- 2026-10-12 approved (human): approved",
                "- 2026-10-10 draft (tester): created",
            ],
            raw_fields={"Priority": "high\n- Priority: low"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    items, drift = att.scan(repo)
    leg_item = _item_by_path(items, dup_rel)
    assert leg_item.native_status == "approved"
    assert leg_item.last_history_at == "2026-10-12"
    assert {(d.location, d.rule) for d in drift} == {
        (dup_rel, "spec.metadata-bullet-repeated")
    }


def test_validate_spec_state_defensive_fields_and_no_context_fallback() -> None:
    """Direct checks for defensive scope/summary checks, missing status, and no-context fallback."""
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import specs as specs_mod

    rel = ".aw/records/specs/20261010-def001-01-def001-direct.spec.md"
    st = _meta.State(
        id6="def001",
        type="spec",
        status=None,
        created_at="2026-10-10T00:00:00Z",
        fields={
            "gate_summary": "\n",
            "scope": "bad\x00scope",
            "summary": "bad\nsummary",
        },
    )
    drift = specs_mod.validate_spec_state(Path(rel), st, has_history=False)
    rules = [d.rule for d in drift]
    assert "attention.missing-status" in rules
    assert "attention.gate-forbidden" in rules
    assert rules.count("attention.unsafe-field") == 2
    assert "attention.history-missing" in rules

    # Direct _spec_record call without project_context uses created_at/updated_at fallback
    ok_state = _meta.State(
        id6="def002",
        type="spec",
        status="approved",
        created_at="2026-10-10T00:00:00Z",
        last_history_day="2026-10-10",
        fields={"priority": "high"},
    )
    item, rec_drift = att._spec_record(
        rel,
        Path(rel),
        "---\nid: def002\ntype: spec\n---\n\n# Spec: Direct\n",
        state=ok_state,
        project_context=None,
    )
    assert rec_drift == []
    assert item is not None
    assert item.native_status == "approved"
    assert item.last_history_at == "2026-10-10"

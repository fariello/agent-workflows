"""Behavioral pinning tests for `aw attention` across all six tracked trees (IPD dqutt8 E-01).

Pins observable behavior of `agent_workflows.attention` on `tmp_path` fixture repositories
before moving `attention` metadata and history reads onto `artifact_meta`: per-tree status
mapping (`attention.missing-status`, `attention.unknown-status`, `attention.disposition-mismatch`),
`id`, `priority`, `blocks_release`, `readiness`, `last_history_at` (newest record by
`attention_contract.newest_history_record`), gate fields, open-question counts,
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
        "# IPD: Valid Plan Heading\n\n"
        "- Date: 2026-10-10\n"
        "- Kind: child\n"
        "- Concern: Pin attention plan fields.\n"
        "- Scope: Plans tree coverage.\n"
        "- Status: reviewed\n"
        "- Readiness: go-pending-approval\n"
        "- Priority: high\n"
        "- Blocks-Release: next\n"
        "- Item-Dependencies: executed:dep001\n"
        "- Set: pinset\n"
        "- Order: 1\n"
        "- Id: pln001\n\n"
        "## Workflow history\n"
        "- 2026-10-12 reviewed (tester): reviewed plan\n"
        "- 2026-10-10 draft (tester): created plan\n\n"
        "## Detailed Implementation Checklist (TODO)\n"
        "- [x] E-01 done step\n"
        "- [ ] E-02 todo step\n\n"
        "## Open questions\n"
        "### OQ-01: Open question one\n"
        "- Status: open\n\n"
        "### RQ-01: Resolved question one\n"
        "- Status: resolved\n\n"
        "## Validation and cross-check\n"
        "- [x] V-01 validates E-01\n",
        encoding="utf-8",
    )

    multi_rel = ".aw/records/plans/executed/20261001-pinset-02-pln002-multi-exec.ipd.md"
    (repo / multi_rel).write_text(
        "# IPD: Legacy Executed Plan\n\n"
        "- Date: 2026-10-01\n"
        "- Status: EXECUTED 2026-10-02 completed\n"
        "- Set: pinset\n"
        "- Order: 2\n"
        "- Id: pln002\n\n"
        "## Workflow history\n"
        "- 2026-10-02 executed (tester): done\n",
        encoding="utf-8",
    )

    mismatch_rel = (
        ".aw/records/plans/executed/20261002-pinset-03-pln003-mismatch.ipd.md"
    )
    (repo / mismatch_rel).write_text(
        "# IPD: Disposition Mismatch Plan\n\n"
        "- Date: 2026-10-02\n"
        "- Status: superseded\n"
        "- Set: pinset\n"
        "- Order: 3\n"
        "- Id: pln003\n\n"
        "## Workflow history\n"
        "- 2026-10-02 superseded (tester): replaced\n",
        encoding="utf-8",
    )

    missing_rel = ".aw/records/plans/pending/20261003-pinset-04-pln004-no-status.ipd.md"
    (repo / missing_rel).write_text(
        "# IPD: Missing Status Plan\n\n- Set: pinset\n- Id: pln004\n",
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/plans/pending/20261004-pinset-05-pln005-bad-status.ipd.md"
    )
    (repo / unknown_rel).write_text(
        "# IPD: Unknown Status Plan\n\n"
        "- Status: bogus-state\n"
        "- Set: pinset\n"
        "- Id: pln005\n",
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
        "# Spec: Deferred Spec\n\n"
        "- Id: spc001\n"
        "- Status: deferred\n"
        "- Priority: high\n"
        "- Blocks-Release: next\n"
        "- Readiness: go\n"
        "- Gate-Kind: decision\n"
        "- Gate-Ref: D42\n"
        "- Gate-Summary: Waiting for architecture signoff\n"
        "- Summary: Pin spec attention reader fields.\n\n"
        "## Workflow history\n"
        "- 2026-10-14 deferred (tester): deferred pending D42\n"
        "- 2026-10-10 draft (tester): created spec\n\n"
        "## Open questions\n"
        "### OQ-01: Unresolved spec question\n"
        "- Status: open\n\n"
        "### OQ-02: Resolved spec question\n"
        "- Status: resolved\n",
        encoding="utf-8",
    )

    missing_rel = ".aw/records/specs/20261011-pinset-02-spc002-no-status.spec.md"
    (repo / missing_rel).write_text(
        "# Spec: Missing Status Spec\n\n"
        "- Id: spc002\n\n"
        "## Workflow history\n"
        "- 2026-10-11 draft (tester): created\n",
        encoding="utf-8",
    )

    unknown_rel = ".aw/records/specs/20261012-pinset-03-spc003-bad-status.spec.md"
    (repo / unknown_rel).write_text(
        "# Spec: Unknown Status Spec\n\n"
        "- Id: spc003\n"
        "- Status: mythical\n\n"
        "## Workflow history\n"
        "- 2026-10-12 draft (tester): created\n",
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
        "# Backlog: Gated Item\n\n"
        "- Id: bkl001\n"
        "- Status: blocked\n"
        "- Priority: medium\n"
        "- Blocks-Release: next\n"
        "- Readiness: go-pending-approval\n"
        "- Work-Kind: feature\n"
        "- Gate-Kind: date\n"
        "- Gate-Ref: 2026-12-01\n"
        "- Summary: Pin backlog attention reader fields.\n\n"
        "## Workflow history\n"
        "- 2026-10-15 blocked (tester): gated on date\n"
        "- 2026-10-10 open (tester): created\n\n"
        "## Open questions\n"
        "### OQ-01: Open backlog question\n"
        "- Status: open\n\n"
        "### RQ-01: Answered backlog question\n"
        "- Status: answered\n",
        encoding="utf-8",
    )

    missing_rel = (
        ".aw/records/backlog/open/20261011-pinset-02-bkl002-no-status.backlog.md"
    )
    (repo / missing_rel).write_text(
        "# Backlog: No Status\n\n- Id: bkl002\n- Priority: low\n",
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/backlog/open/20261012-pinset-03-bkl003-bad-status.backlog.md"
    )
    (repo / unknown_rel).write_text(
        "# Backlog: Bad Status\n\n- Id: bkl003\n- Status: sideways\n",
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
        "---\n"
        "id: res001\n"
        "kind: findings\n"
        "status: active\n"
        "priority: high\n"
        "blocks-release: next\n"
        "summary: Pin research attention reader fields.\n"
        "---\n\n"
        "# Research: Active Study\n\n"
        "## Workflow history\n"
        "- 2026-10-16 active (tester): resumed study\n"
        "- 2026-10-10 todo (tester): opened study\n\n"
        "## Open questions\n"
        "### OQ-01: Unresolved research question\n"
        "- Status: open\n\n"
        "### RQ-01: Resolved research question\n"
        "- Status: resolved\n",
        encoding="utf-8",
    )

    missing_rel = ".aw/records/research/20261011-pinset-02-res002-no-status.findings.md"
    (repo / missing_rel).write_text(
        "---\nid: res002\nkind: findings\n---\n\n# Research: Missing Status\n",
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/research/20261012-pinset-03-res003-bad-status.findings.md"
    )
    (repo / unknown_rel).write_text(
        "---\nid: res003\nkind: findings\nstatus: limbo\n---\n\n# Research: Bad Status\n",
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
        "# Release: v1.0.0\n\n"
        "- Id: rel001\n"
        "- Status: planned\n"
        "- Summary: Pin release attention reader fields.\n\n"
        "## Workflow history\n"
        "- 2026-10-17 planned (tester): scheduled release\n"
        "- 2026-10-10 planned (tester): drafted release\n\n"
        "## Open questions\n"
        "### OQ-01: Open release question\n"
        "- Status: open\n\n"
        "### RQ-01: Closed release question\n"
        "- Status: closed\n",
        encoding="utf-8",
    )

    missing_rel = ".aw/records/releases/20261011-pinset-02-rel002-no-status.release.md"
    (repo / missing_rel).write_text(
        "# Release: Missing Status\n\n- Id: rel002\n",
        encoding="utf-8",
    )

    unknown_rel = ".aw/records/releases/20261012-pinset-03-rel003-bad-status.release.md"
    (repo / unknown_rel).write_text(
        "# Release: Unknown Status\n\n- Id: rel003\n- Status: aborted\n",
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
        "<!-- aw-prompt: Kind: research | Id: prm001 | Set: pinset | Order: 01 | Status: pending | Slug: sample -->\n\n"
        "# Prompt: Pin prompt attention reader fields.\n\n"
        "## Workflow history\n"
        "- 2026-10-18 pending (tester): staged prompt\n"
        "- 2026-10-10 pending (tester): created prompt\n\n"
        "## Open questions\n"
        "### OQ-01: Open prompt question\n"
        "- Status: open\n\n"
        "### RQ-01: Resolved prompt question\n"
        "- Status: resolved\n",
        encoding="utf-8",
    )

    missing_rel = ".aw/records/prompts/20261011-pinset-02-prm002-unbucketed.prompt.md"
    (repo / missing_rel).write_text(
        "<!-- aw-prompt: Kind: research | Id: prm002 | Set: pinset | Order: 02 | Status: pending | Slug: unbucketed -->\n\n"
        "# Prompt: Unbucketed\n",
        encoding="utf-8",
    )

    unknown_rel = (
        ".aw/records/prompts/weird/20261012-pinset-03-prm003-bad-bucket.prompt.md"
    )
    (repo / unknown_rel).write_text(
        "<!-- aw-prompt: Kind: research | Id: prm003 | Set: pinset | Order: 03 | Status: weird | Slug: bad-bucket -->\n\n"
        "# Prompt: Unknown Bucket\n",
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
        "# IPD: Clean Plan\n\n"
        "- Date: 2026-10-10\n"
        "- Status: draft\n"
        "- Set: pinset\n"
        "- Order: 1\n"
        "- Id: chk001\n\n"
        "## Workflow history\n"
        "- 2026-10-10 draft (tester): created\n",
        encoding="utf-8",
    )
    bad_rel = ".aw/records/plans/pending/20261011-pinset-02-chk002-bad.ipd.md"
    (repo / bad_rel).write_text(
        "# IPD: Broken Plan\n\n- Set: pinset\n- Id: chk002\n",
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
        "# IPD: Control Plan\n\n- Date: 2026-10-10\n- Status: draft\n- Set: pinset\n- Id: inc001\n",
        encoding="utf-8",
    )

    # 2. Plan with a corrupt authoritative log (has both .md mirror and invalid meta/<id6>.jsonl)
    bad_rel = ".aw/records/plans/pending/20261011-pinset-02-inc002-corrupt.ipd.md"
    (repo / bad_rel).write_text(
        "# IPD: Corrupt Log Plan\n\n- Date: 2026-10-11\n- Status: approved\n- Set: pinset\n- Id: inc002\n",
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
        "# IPD: With Short Description\n\n"
        "- Date: 2026-10-10\n"
        "- Status: draft\n"
        "- Scope: Long fallback scope paragraph.\n"
        "- Short-Description: Crisp one-line description.\n"
        "- Set: pinset\n"
        "- Id: sd0001\n",
        encoding="utf-8",
    )

    no_sd_rel = ".aw/records/plans/pending/20261011-pinset-02-sd0002-no-sd.ipd.md"
    (repo / no_sd_rel).write_text(
        "# IPD: Without Short Description\n\n"
        "- Date: 2026-10-11\n"
        "- Status: draft\n"
        "- Scope: Fallback scope paragraph.\n"
        "- Set: pinset\n"
        "- Id: sd0002\n",
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
    """Log-format record reads `last_history_at` via `artifact_meta.history` and `A.last_history_at`."""
    repo = _init_repo(tmp_path)
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    meta_dir = repo / ".aw" / "records" / "meta"
    pending_dir.mkdir(parents=True)
    meta_dir.mkdir(parents=True)

    rel = ".aw/records/plans/pending/20261010-pinset-01-log001-log-plan.ipd.md"
    (repo / rel).write_text(
        "---\nid: log001\nstatus: reviewed\n---\n\n# IPD: Log Plan\n",
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

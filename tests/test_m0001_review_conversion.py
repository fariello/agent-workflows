"""Outcome tests for m0001 review events and research/walkthrough/roadmap/review conversion (IPD hpedmn).

Covers E-01..E-03 / V-01..V-03: AC-32 case 1 with review events, AC-29 case 1,
AC-14 migration form (K4 bindings for own-id6 and multi-file subjects), AC-14a
case 5 (four off-vocabulary verdict strings recovered byte for byte), AC-19
research clock separation, OQ-02 roadmap disposition, and byte-identical
preservation of review Round/Findings/Decisions and excluded trees/templates.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from agent_workflows import artifact_meta, cli, review_findings
from agent_workflows.migrations import chain, m0001_convert, m0001_verify

pytestmark = pytest.mark.core

_DEFAULT_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/runs/\n"
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "repo",
) -> Path:
    """Create a fresh isolated git repo with AW_HOME pointed into tmp_path."""
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "records").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")
    return repo


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        artifact_meta.decode_line(line)
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.strip()
    ]


def _run_cli(argv: List[str]) -> Tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = int(exc.code) if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _parse_agent_jsonl(raw: str) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _find_research_statuses(repo: Path) -> Dict[str, str]:
    rc, out, err = _run_cli(["find", "research", "--agent", "--dir", str(repo)])
    assert rc == 0, f"aw find research failed: {err}\n{out}"
    statuses: Dict[str, str] = {}
    for rec in _parse_agent_jsonl(out):
        if rec.get("kind") == "item" and rec.get("id6"):
            statuses[str(rec["id6"])] = str(rec.get("status") or "")
    return statuses


# --------------------------------------------------------------------------------------
# V-01: AC-32 with review events, AC-19 research clock, K4/K5/K6, and field destinations
# --------------------------------------------------------------------------------------


def test_layout_ac32_with_review_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-32 case 1: checkpoint, 2 history, 1 sidecar, 2 review events in append 0."""
    repo = _init_repo(tmp_path, monkeypatch, name="ac32_rev")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)

    plan_path = rec / "plans" / "executed" / "20261101-demo-01-pl3201-ac32-plan.ipd.md"
    plan_path.write_text(
        "# AC-32 Plan\n\n"
        "- Id: pl3201\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Date: 2026-11-01\n"
        "- Kind: child\n"
        "- Item-Dependencies: none\n\n"
        "## Goal\n\nTest AC-32 layout with reviews.\n\n"
        "## Workflow history\n\n"
        "- 2026-11-02 executed (codex): finished work\n"
        "- 2026-11-01 approved (human): approved\n",
        encoding="utf-8",
    )

    rev_path = rec / "reviews" / "20261101-demo-01-pl3201-ac32-plan.review.md"
    rev_path.write_text(
        "# Review: AC-32 Plan\n\n"
        "- Subject-Id: pl3201\n"
        "- Subject-Type: ipd\n"
        "- Reviewed-At: 2026-11-01\n"
        "- Reviewer: opencode/opus\n"
        "- Verdict: APPROVE WITH REVISIONS APPLIED\n"
        "- Findings: 1 medium FIXED\n\n"
        "## Round 1\n\nInitial findings.\n\n"
        "## Round 2\n\nVerified fixed.\n",
        encoding="utf-8",
    )

    sidecar_records = [
        {
            "op": "legacy",
            "source": "sidecar",
            "observed_day": "2026-11-01",
            "position": 0,
            "ordering_confidence": "unknown",
            "line": "- 2026-11-01 note (sidecar): sidecar record",
        }
    ]
    fixed_at = "2026-11-17T07:00:00Z"

    summary = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        sidecar_events={"pl3201": sidecar_records},
        migration_at=fixed_at,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )
    assert summary["by_type"]["ipd"] == 1
    assert summary["by_type"]["review"] == 1
    assert not (rec / "meta" / "pl3201.review.jsonl").exists()

    events = _read_jsonl(rec / "meta" / "pl3201.jsonl")
    assert [e["op"] for e in events] == [
        "checkpoint",
        "legacy",
        "legacy",
        "legacy",
        "review",
        "review",
    ]
    assert [e["seq"] for e in events] == [0, 1, 2, 3, 4, 5]
    assert all(e["append"] == 0 for e in events)
    assert all(e["at"] == fixed_at for e in events)
    assert all(e["actor"] == {"tool": "aw migrate metadata"} for e in events)
    assert [e["source"] for e in events[1:4]] == ["history", "history", "sidecar"]

    # K5a: earlier round carries legacy_verdict=None and omits last-round fields.
    assert events[4]["round"] == 1
    assert events[4]["review_kind"] == "gate"
    assert events[4]["legacy_verdict"] is None
    assert "reviewer" not in events[4]
    assert "observed_day" not in events[4]
    assert "findings_summary" not in events[4]
    assert "review_ref" not in events[4]

    # K5a: last round carries verdict/reviewer/observed_day/findings_summary.
    assert events[5]["round"] == 2
    assert events[5]["review_kind"] == "gate"
    assert events[5]["legacy_verdict"] == "APPROVE WITH REVISIONS APPLIED"
    assert events[5]["reviewer"] == "opencode/opus"
    assert events[5]["observed_day"] == "2026-11-01"
    assert events[5]["findings_summary"] == "1 medium FIXED"
    assert "review_ref" not in events[5]

    state_cp, _, _, _ = artifact_meta.replay(
        "pl3201", "ipd", events[:1], records_root=rec, migration_import=True
    )
    state, _, _, proj = artifact_meta.replay(
        "pl3201", "ipd", events, records_root=rec, migration_import=True
    )
    assert state.fields == state_cp.fields
    assert len(proj["reviews"]) == 2
    assert proj["reviews"][0]["legacy_verdict"] is None
    assert proj["reviews"][1]["legacy_verdict"] == "APPROVE WITH REVISIONS APPLIED"
    assert proj["reviews"][1]["findings_summary"] == "1 medium FIXED"


def test_clock_ac19_research_filename_date_vs_created_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-19: research filename_date vs created_day stay distinct without drift."""
    repo = _init_repo(tmp_path, monkeypatch, name="clock_res")
    rec = repo / ".aw" / "records"
    (rec / "research" / "reference" / "202609").mkdir(parents=True)
    (rec / "walkthroughs").mkdir(parents=True)

    # Set date 2026-09-03 differs from report creation day 2026-09-23 (4.2b cxe3dw case).
    r_path = (
        rec
        / "research"
        / "reference"
        / "202609"
        / "20260903-demo-01-rs1901-clock-study.research-report.md"
    )
    r_path.write_text(
        "---\n"
        "id: rs1901\n"
        "created: 20260923\n"
        "set: demo\n"
        "order: 01\n"
        "topic: [clocks]\n"
        "model: opus55\n"
        "kind: research-report\n"
        "status: reference\n"
        "outcome: adopted\n"
        "summary: Distinct filename and creation days.\n"
        "consumed-by: [pl0001]\n"
        "---\n\n"
        "# Clock Study\n\nBody.\n",
        encoding="utf-8",
    )

    # Walkthrough without - Date:: filename_date populated, created_day remains None.
    w_path = rec / "walkthroughs" / "20260905-demo-01-wt1902-no-date.walkthrough.md"
    w_path.write_text("# No Date Walkthrough\n\n- Id: wt1902\n", encoding="utf-8")

    _, _, ev_r, _ = m0001_convert.build_record_log(r_path, rec, repo_root=repo)
    st_r, _, _, _ = artifact_meta.replay(
        "rs1901", "research", ev_r, records_root=rec, migration_import=True
    )
    assert st_r.filename_date == "2026-09-03"
    assert st_r.created_day == "2026-09-23"
    assert st_r.fields["filename_date"] == "2026-09-03"
    assert st_r.fields["created_day"] == "2026-09-23"

    _, _, ev_w, _ = m0001_convert.build_record_log(w_path, rec, repo_root=repo)
    st_w, _, _, _ = artifact_meta.replay(
        "wt1902", "walkthrough", ev_w, records_root=rec, migration_import=True
    )
    assert st_w.filename_date == "2026-09-05"
    assert st_w.created_day is None
    assert st_w.fields.get("created_day") is None


def test_fields_research_yaml_and_nonleading_prompt_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify research YAML field destinations, D177 facets, and OQ-04 body prose."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_res")
    rec = repo / ".aw" / "records"
    (rec / "research" / "reference" / "202610").mkdir(parents=True)

    r_report = (
        rec
        / "research"
        / "20261017-revsteps-05-rs5001-synthesis.reconciliation.reconciliation-report.md"
    )
    r_report.write_text(
        "---\n"
        "id: rs5001\n"
        "created: 20261017\n"
        "set: revsteps\n"
        "order: 05\n"
        "topic: [plan-review, runner]\n"
        "model: reconciliation\n"
        "kind: reconciliation-report\n"
        "status: active\n"
        "outcome: informational\n"
        "priority: high\n"
        "summary: Synthesis summary moved to body.\n"
        "consumed-by: [sp0001]\n"
        "---\n\n"
        "# Reconciliation Report\n\n"
        "- Prompt: y6vfto\n"
        "- Reports: r7rfdi, xd85vw\n"
        "- Reconciler: opencode\n"
        "- Repository: agent-workflows\n"
        "- Component: runner\n"
        "- Severity: high\n"
        "- Source: audit\n"
        "- Researched: 2026-10-17\n"
        "- Researcher: opus\n\n"
        "## Findings\n\nDetails.\n\n"
        "## Workflow history\n\n"
        "- 2026-10-17 active (tester): synthesized\n",
        encoding="utf-8",
    )

    # Research-prompt without YAML status + non-leading aw-prompt comment (OQ-04) + D177 facets.
    r_prompt = (
        rec
        / "research"
        / "reference"
        / "202610"
        / "20261018-actorenv-00-rs5002-actor-prompt.agy.opus55.research-prompt.md"
    )
    r_prompt.write_text(
        "---\n"
        "id: rs5002\n"
        "created: 20261018\n"
        "set: actorenv\n"
        "order: 00\n"
        "topic: [actor]\n"
        "model:\n"
        "kind: research-prompt\n"
        "outcome: none-yet\n"
        "summary: Research prompt summary.\n"
        "consumed-by: []\n"
        "---\n\n"
        "<!-- aw-prompt: Kind: research | Status: pending . Pipeline metadata only. -->\n"
        "You are a principal investigator.\n\n"
        "# Prompt Body\n\n"
        "## Deliverables\n\nOne markdown report.\n",
        encoding="utf-8",
    )

    pre_rec = tmp_path / "pre_fields_res_records"
    shutil.copytree(rec, pre_rec)
    pre_find_statuses = _find_research_statuses(repo)
    assert pre_find_statuses["rs5001"] == "active"

    summary = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("research",),
        include_reviews=False,
    )
    assert summary["by_type"]["research"] == 2

    ev1 = _read_jsonl(rec / "meta" / "rs5001.jsonl")
    st1, _, _, _ = artifact_meta.replay(
        "rs5001", "research", ev1, records_root=rec, migration_import=True
    )
    f1 = st1.fields
    assert st1.status == "active"
    assert f1["created_day"] == "2026-10-17"
    assert f1["research_kind"] == "reconciliation-report"
    assert f1["set"] == "revsteps"
    assert f1["order"] == 5
    assert f1["topic"] == ["plan-review", "runner"]
    assert f1["model"] == "reconciliation"
    assert f1["outcome"] == "informational"
    assert f1["priority"] == "high"
    assert f1["consumed_by"] == ["sp0001"]
    assert "summary" not in f1

    body1 = r_report.read_text(encoding="utf-8")
    assert "## Summary\n\nSynthesis summary moved to body.\n" in body1
    for kept_bullet in (
        "- Prompt: y6vfto",
        "- Reports: r7rfdi, xd85vw",
        "- Reconciler: opencode",
        "- Repository: agent-workflows",
        "- Component: runner",
        "- Severity: high",
        "- Source: audit",
        "- Researched: 2026-10-17",
        "- Researcher: opus",
    ):
        assert kept_bullet in body1
    assert "## Workflow history" not in body1

    ev2 = _read_jsonl(rec / "meta" / "rs5002.jsonl")
    st2, _, _, _ = artifact_meta.replay(
        "rs5002", "research", ev2, records_root=rec, migration_import=True
    )
    assert st2.status is None
    assert "status" not in st2.fields
    assert st2.fields["ace"] == "agy"
    assert st2.fields["model"] == "opus55"
    assert st2.fields["research_kind"] == "research-prompt"
    assert st2.fields["consumed_by"] == []
    body2 = r_prompt.read_text(encoding="utf-8")
    assert body2.splitlines()[:3] == ["---", "id: rs5002", "---"]
    assert body2.splitlines()[3].startswith("<!-- aw-managed:")
    assert "status:" not in "\n".join(body2.splitlines()[:4])
    assert artifact_meta.parse_artifact_mirror(body2, allow_statusless=True) == {
        "id": "rs5002",
        "status": None,
    }
    assert "<!-- aw-prompt: Kind: research | Status: pending" in body2
    assert "## Summary\n\nResearch prompt summary.\n" in body2

    rt = m0001_verify.verify_round_trip(
        repo,
        pre_conversion_records_root=pre_rec,
        converted_records_root=rec,
    )
    assert rt["passed"] is True, rt["errors"]
    assert rt["errors"] == []

    assert chain.repo_has_legacy_records(repo, records_root=rec) is False

    _rc_meta, out_meta, _err_meta = _run_cli(
        ["check", "meta", "--agent", "--dir", str(repo)]
    )
    meta_items = [r for r in _parse_agent_jsonl(out_meta) if r.get("kind") == "item"]
    mirror_drift_rules = {
        it.get("rule")
        for it in meta_items
        if it.get("rule") in ("meta.status-mirror-drift", "meta.id-mirror-drift")
    }
    assert mirror_drift_rules == set(), meta_items

    rc_att, out_att, err_att = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_att == 0, f"aw attention failed: {err_att}\n{out_att}"
    att_doc = json.loads(out_att)
    unknown_status_violations = [
        v
        for v in att_doc.get("violations", [])
        if v.get("code") == "attention.unknown-status"
    ]
    assert unknown_status_violations == []
    assert att_doc.get("valid") is True

    post_find_statuses = _find_research_statuses(repo)
    assert post_find_statuses == pre_find_statuses


def test_fields_walkthrough_and_free_prose_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify walkthrough field destinations and free-prose - Status: preserved in body."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_wt")
    rec = repo / ".aw" / "records"
    (rec / "walkthroughs").mkdir(parents=True)

    wt_path = rec / "walkthroughs" / "20260917-demo-02-wt5001-verify.walkthrough.md"
    wt_path.write_text(
        "# Walkthrough Verification\n\n"
        "- Id: wt5001\n"
        "- Date: 2026-09-17\n"
        "- Set: demo\n"
        "- Order: 2\n"
        "- Target-Id: pl1001\n"
        "- Kind: whole-Set verification record\n"
        "- Status: IN PROGRESS - Stage 1 done;\n"
        "  rehearsal NOT yet performed.\n"
        "- Origin: Split from parent\n"
        "- Plan: pl1001\n"
        "- Purpose: Verify whole set\n"
        "- Spec: sp1001\n"
        "- Reviewer: opencode\n"
        "- Verdict: APPROVED\n"
        "- Scope: All children\n"
        "- Summary: Verification summary.\n\n"
        "## Details\n\nVerified.\n\n"
        "## Workflow history\n\n"
        "- 2026-09-17 note (tester): recorded\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("walkthrough",),
        include_reviews=False,
    )
    ev = _read_jsonl(rec / "meta" / "wt5001.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "wt5001", "walkthrough", ev, records_root=rec, migration_import=True
    )
    assert st.status is None
    assert st.fields["created_day"] == "2026-09-17"
    assert st.fields["set"] == "demo"
    assert st.fields["order"] == 2
    assert st.fields["target_id"] == "pl1001"
    assert "plan_role" not in st.fields
    assert "status" not in st.fields

    rewritten = wt_path.read_text(encoding="utf-8")
    assert artifact_meta.parse_walkthrough_mirror(rewritten) == {
        "id": "wt5001",
        "status": None,
    }
    assert (
        "- Status: IN PROGRESS - Stage 1 done;\n  rehearsal NOT yet performed."
        in rewritten
    )
    for sec in (
        "## Kind",
        "## Origin",
        "## Plan",
        "## Purpose",
        "## Spec",
        "## Reviewer",
        "## Verdict",
        "## Scope",
        "## Summary",
    ):
        assert sec in rewritten
    assert "## Workflow history" not in rewritten


def test_fields_review_events_and_k6_destinations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify review K6 event fields and non-K6 bullets moved to body before ## Round."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_rev")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)

    (rec / "plans" / "executed" / "20260916-lanectn-07-4fodkt-plan.ipd.md").write_text(
        "# Plan 4fodkt\n\n"
        "- Id: 4fodkt\n"
        "- Status: executed\n"
        "- Set: lanectn\n"
        "- Order: 7\n"
        "- Readiness: go-pending-approval\n",
        encoding="utf-8",
    )
    rev_path = rec / "reviews" / "20260916-lanectn-07-4fodkt-plan.review.md"
    rev_path.write_text(
        "# Review findings: plan 4fodkt\n\n"
        "- Subject-Id: 4fodkt\n"
        "- Subject-Type: ipd\n"
        "- Reviewed-At: 2026-09-16\n"
        "- Reviewer: opencode/opus\n"
        "- Verdict: APPROVE WITH REVISIONS APPLIED\n"
        "- Readiness: no-go\n"
        "- Set: lanectn\n"
        "- Order: 7\n"
        "- Rounds: 1\n"
        "- Audited-Scope: [FR-01..FR-10]\n"
        "- Findings: 2 medium FIXED\n\n"
        "## Round 1\n\nBody.\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("ipd",),
        include_reviews=True,
    )
    ev = _read_jsonl(rec / "meta" / "4fodkt.jsonl")
    st, _, _, proj = artifact_meta.replay(
        "4fodkt", "ipd", ev, records_root=rec, migration_import=True
    )
    # Migrated review event does not overwrite the plan's checkpoint readiness.
    assert st.fields["readiness"] == "go-pending-approval"
    assert len(proj["reviews"]) == 1
    rrow = proj["reviews"][0]
    assert rrow["reviewer"] == "opencode/opus"
    assert rrow["observed_day"] == "2026-09-16"
    assert rrow["findings_summary"] == "2 medium FIXED"
    assert rrow["legacy_verdict"] == "APPROVE WITH REVISIONS APPLIED"

    rev_text = rev_path.read_text(encoding="utf-8")
    assert artifact_meta.parse_review_mirror(rev_text) == {
        "subject": "4fodkt",
        "subject_type": "ipd",
    }
    for sec in (
        "## Readiness",
        "## Set",
        "## Order",
        "## Rounds",
        "## Audited-Scope",
    ):
        assert sec in rev_text


def test_review_event_k4_bindings_own_id6_and_multi_file_subject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-14 migration form: K4 bindings for own-id6 files and multi-file pairs."""
    repo = _init_repo(tmp_path, monkeypatch, name="k4_bindings")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "draft").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)

    # Subject 1: spec 18hh1u with 2 own-id6 specflow refinement review files.
    (
        rec / "specs" / "draft" / "20261024-specflow-01-18hh1u-synthesis.spec.md"
    ).write_text(
        "# Specflow\n\n- Id: 18hh1u\n- Status: draft\n- Set: specflow\n",
        encoding="utf-8",
    )
    sf1 = (
        rec
        / "reviews"
        / "20261024-specflow-04-vprs7o-spec-refinement.agy.gemini38flashhigh.review.md"
    )
    sf1.write_text(
        "# Refinement 1\n\n"
        "- Subject-Id: 18hh1u\n"
        "- Subject-Type: spec\n"
        "- Reviewed-At: 2026-10-24\n"
        "- Reviewer: agy/gemini38flashhigh\n"
        "- Verdict: REVIEWED - MATERIAL CHANGES APPLIED\n\n"
        "## Round 1\n\nRefined.\n",
        encoding="utf-8",
    )
    sf2 = (
        rec
        / "reviews"
        / "20261024-specflow-07-v5fjwb-spec-refinement.agy.gemini38flashhigh.review.md"
    )
    sf2.write_text(
        "# Refinement 2\n\n"
        "- Subject-Id: 18hh1u\n"
        "- Subject-Type: spec\n"
        "- Reviewed-At: 2026-10-24\n"
        "- Reviewer: agy/gemini38flashhigh\n"
        "- Verdict: REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION\n\n"
        "## Round 2\n\nConverged.\n",
        encoding="utf-8",
    )

    # Subject 2: plan rtvdak with 2 gate review files sharing the subject's id6.
    (rec / "plans" / "executed" / "20260930-reqids-02-rtvdak-parser.ipd.md").write_text(
        "# Parser\n\n- Id: rtvdak\n- Status: executed\n- Set: reqids\n",
        encoding="utf-8",
    )
    pair1 = rec / "reviews" / "20260930-reqids-02-rtvdak-parser-old.review.md"
    pair1.write_text(
        "# Pair 1\n\n"
        "- Subject-Id: rtvdak\n"
        "- Subject-Type: ipd\n"
        "- Reviewed-At: 2026-10-01\n"
        "- Reviewer: opencode\n"
        "- Verdict: APPROVE WITH REVISIONS APPLIED\n\n"
        "## Round 1\n\nFirst.\n",
        encoding="utf-8",
    )
    pair2 = rec / "reviews" / "20261007-reqids-02-rtvdak-parser.review.md"
    pair2.write_text(
        "# Pair 2\n\n"
        "- Subject-Id: rtvdak\n"
        "- Subject-Type: ipd\n"
        "- Reviewed-At: 2026-10-07\n"
        "- Reviewer: opencode\n"
        "- Verdict: APPROVE WITH REVISIONS APPLIED\n\n"
        "## Round 1\n\nRe-review.\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )

    # No separate logs for review files.
    assert not (rec / "meta" / "vprs7o.jsonl").exists()
    assert not (rec / "meta" / "v5fjwb.jsonl").exists()

    ev_spec = _read_jsonl(rec / "meta" / "18hh1u.jsonl")
    _, _, _, proj_spec = artifact_meta.replay(
        "18hh1u", "spec", ev_spec, records_root=rec, migration_import=True
    )
    assert [
        (r["round"], r["review_kind"], r["review_ref"]) for r in proj_spec["reviews"]
    ] == [
        (1, "refinement", "vprs7o"),
        (2, "refinement", "v5fjwb"),
    ]
    assert artifact_meta.parse_review_mirror(sf1.read_text(encoding="utf-8")) == {
        "subject": "18hh1u",
        "subject_type": "spec",
        "ref": "vprs7o",
    }
    assert artifact_meta.parse_review_mirror(sf2.read_text(encoding="utf-8")) == {
        "subject": "18hh1u",
        "subject_type": "spec",
        "ref": "v5fjwb",
    }

    ev_plan = _read_jsonl(rec / "meta" / "rtvdak.jsonl")
    _, _, _, proj_plan = artifact_meta.replay(
        "rtvdak", "ipd", ev_plan, records_root=rec, migration_import=True
    )
    assert [
        (r["round"], r["review_kind"], r["review_ref"]) for r in proj_plan["reviews"]
    ] == [
        (1, "gate", "20260930-reqids-02"),
        (1, "gate", "20261007-reqids-02"),
    ]
    assert artifact_meta.parse_review_mirror(pair1.read_text(encoding="utf-8")) == {
        "subject": "rtvdak",
        "subject_type": "ipd",
        "ref": "20260930-reqids-02",
    }
    assert artifact_meta.parse_review_mirror(pair2.read_text(encoding="utf-8")) == {
        "subject": "rtvdak",
        "subject_type": "ipd",
        "ref": "20261007-reqids-02",
    }


def test_review_event_ac14a_case5_off_vocabulary_verdicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-14a case 5: all four off-vocabulary verdicts recovered byte for byte."""
    repo = _init_repo(tmp_path, monkeypatch, name="ac14a_case5")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "draft").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)

    (rec / "specs" / "draft" / "20261024-specflow-01-18hh1u-spec.spec.md").write_text(
        "# Spec\n\n- Id: 18hh1u\n- Status: draft\n- Set: specflow\n", encoding="utf-8"
    )

    verdicts = [
        ("rv0001", "REVIEWED - MATERIAL CHANGES APPLIED"),
        ("rv0002", "REVIEWED"),
        ("rv0003", "REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION"),
        ("rv0004", "REVIEWED - CONVERGED WITH REVISIONS"),
    ]
    for idx, (own_id, vstr) in enumerate(verdicts, start=1):
        (
            rec
            / "reviews"
            / f"20261024-specflow-{idx:02d}-{own_id}-spec-refinement.review.md"
        ).write_text(
            f"# Refinement {idx}\n\n"
            "- Subject-Id: 18hh1u\n"
            "- Subject-Type: spec\n"
            "- Reviewed-At: 2026-10-24\n"
            "- Reviewer: agy\n"
            f"- Verdict: {vstr}\n\n"
            f"## Round {idx}\n\nNotes.\n",
            encoding="utf-8",
        )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )
    events = _read_jsonl(rec / "meta" / "18hh1u.jsonl")
    _, _, _, proj = artifact_meta.replay(
        "18hh1u", "spec", events, records_root=rec, migration_import=True
    )
    recovered = {r["review_ref"]: r["legacy_verdict"] for r in proj["reviews"]}
    assert recovered == dict(verdicts)


# --------------------------------------------------------------------------------------
# V-02: AC-29(1) walkthrough, roadmap disposition, review/research rewrites, exclusions
# --------------------------------------------------------------------------------------


def test_walkthrough_ac29_case1_one_key_frontmatter_and_no_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-29 case 1: walkthrough one-key mirror, no transition, comms/data untouched, setter refused."""
    repo = _init_repo(tmp_path, monkeypatch, name="ac29_case1")
    rec = repo / ".aw" / "records"
    (rec / "walkthroughs").mkdir(parents=True)
    (rec / "comms" / "shared" / "inbox").mkdir(parents=True)
    (rec / "research" / "20261101-demo-01-rs0001-study.data").mkdir(parents=True)

    wt_path = rec / "walkthroughs" / "20261105-demo-01-wt2901-audit.walkthrough.md"
    wt_path.write_text(
        "# Audit Walkthrough\n\n"
        "- Id: wt2901\n"
        "- Date: 2026-11-05\n\n"
        "## Workflow history\n\n"
        "- 2026-11-05 note (author): recorded\n",
        encoding="utf-8",
    )
    comms_path = rec / "comms" / "shared" / "inbox" / "20261105-msg.md"
    comms_bytes = b"# Comms Message\nKeep untouched.\n"
    comms_path.write_bytes(comms_bytes)

    data_path = rec / "research" / "20261101-demo-01-rs0001-study.data" / "notes.md"
    data_bytes = b"# Companion Data\nRaw notes.\n"
    data_path.write_bytes(data_bytes)

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )

    wt_text = wt_path.read_text(encoding="utf-8")
    assert wt_text.splitlines()[:3] == ["---", "id: wt2901", "---"]
    assert wt_text.splitlines()[3].startswith("<!-- aw-managed:")
    assert artifact_meta.parse_walkthrough_mirror(wt_text) == {
        "id": "wt2901",
        "status": None,
    }
    assert "## Workflow history" not in wt_text

    events = _read_jsonl(rec / "meta" / "wt2901.jsonl")
    assert all(e["op"] != "transition" for e in events)
    assert [e["op"] for e in events] == ["checkpoint", "legacy"]

    # Comms and .data/ files are byte-identical and receive no log.
    assert comms_path.read_bytes() == comms_bytes
    assert data_path.read_bytes() == data_bytes
    assert len(list((rec / "meta").glob("*.jsonl"))) == 1

    # Walkthrough status transition is refused by the metadata store.
    ok, reason = artifact_meta.validate_transition_edge("walkthrough", None, "active")
    assert not ok
    assert "no status" in reason

    ctx = type(
        "Ctx", (), {"logical_roots": {"records": rec, "state": repo / ".aw" / "state"}}
    )
    with pytest.raises(ValueError, match="no status"):
        artifact_meta.append(
            "wt2901",
            [{"op": "transition", "to": "active"}],
            project_context=ctx,
            actor={"tool": "test"},
        )


def test_roadmap_disposition_one_key_frontmatter_and_sidecar_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify OQ-02 roadmap disposition: one-key mirror, bold prose kept, no transition, sidecar imported."""
    repo = _init_repo(tmp_path, monkeypatch, name="roadmap_disp")
    rec = repo / ".aw" / "records"
    (rec / "roadmaps").mkdir(parents=True)

    rm_path = (
        rec / "roadmaps" / "20260712-7ny1bg-01-7ny1bg-bounded-iteration.roadmap.md"
    )
    rm_path.write_text(
        "# Roadmap for Consideration\n\n"
        "- **Created:** 2026-07-12 14:26 America/New_York\n"
        "- **Status:** DRAFT FOR CONSIDERATION\n\n"
        "---\n\n"
        "## 1. Executive recommendation\n\n"
        "Recommendation text.\n",
        encoding="utf-8",
    )

    sidecar_records = [
        {
            "op": "legacy",
            "source": "sidecar",
            "observed_day": "2026-07-12",
            "position": 0,
            "ordering_confidence": "unknown",
            "line": {"id6": "7ny1bg", "date": "2026-07-12", "action": "created"},
        }
    ]
    summary = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        sidecar_events={"7ny1bg": sidecar_records},
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )
    assert summary["by_type"]["roadmap"] == 1

    events = _read_jsonl(rec / "meta" / "7ny1bg.jsonl")
    assert [e["op"] for e in events] == ["checkpoint", "legacy"]
    assert all(e["op"] != "transition" for e in events)
    assert events[1]["source"] == "sidecar"

    st, _, _, _ = artifact_meta.replay(
        "7ny1bg", "roadmap", events, records_root=rec, migration_import=True
    )
    assert st.type == "roadmap"
    assert st.status is None
    assert st.filename_date == "2026-07-12"

    rm_text = rm_path.read_text(encoding="utf-8")
    assert rm_text.splitlines()[:3] == ["---", "id: 7ny1bg", "---"]
    assert rm_text.splitlines()[3].startswith("<!-- aw-managed:")
    assert artifact_meta.parse_walkthrough_mirror(rm_text) == {
        "id": "7ny1bg",
        "status": None,
    }
    assert "- **Created:** 2026-07-12 14:26 America/New_York" in rm_text
    assert "- **Status:** DRAFT FOR CONSIDERATION" in rm_text

    ok, reason = artifact_meta.validate_transition_edge("roadmap", None, "active")
    assert not ok
    assert "no status" in reason


def test_review_file_rewrite_preserves_rounds_findings_and_decisions_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify review file rewrite keeps ## Round, ### Findings, and ### Decisions byte-identical."""
    repo = _init_repo(tmp_path, monkeypatch, name="rev_rewrite")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)

    (rec / "plans" / "executed" / "20261101-demo-01-pl7701-target.ipd.md").write_text(
        "# Target\n\n- Id: pl7701\n- Status: executed\n- Set: demo\n",
        encoding="utf-8",
    )

    rounds_and_tables = (
        "## Round 1\n\n"
        "```markdown\n"
        "## Workflow history\n\n"
        "- 2026-10-01 note (example): fenced history sample must stay\n"
        "```\n\n"
        "### Findings\n\n"
        "| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| PR-001 | MEDIUM | IN-SCOPE | Testing | `tests/a.py` | Missing check. | Low | FIXED | Added test. |\n\n"
        "### Decisions\n\n"
        "| ID | Question | Chosen | Alternatives considered | Basis | Reversible |\n"
        "|---|---|---|---|---|---|\n"
        "| D-1 | Which path? | Option A | Option B | Measured | yes |\n"
    )
    rev_path = rec / "reviews" / "20261101-demo-01-pl7701-target.review.md"
    rev_path.write_text(
        "# Review: Target\n\n"
        "- Subject-Id: pl7701\n"
        "- Subject-Type: ipd\n"
        "- Reviewed-At: 2026-11-01\n"
        "- Reviewer: opencode\n"
        "- Verdict: APPROVE WITH REVISIONS APPLIED\n"
        "- Findings: 1 medium FIXED\n\n" + rounds_and_tables,
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )

    migrated = rev_path.read_text(encoding="utf-8")
    assert migrated.splitlines()[:4] == [
        "---",
        "subject: pl7701",
        "subject_type: ipd",
        "---",
    ]
    assert migrated.splitlines()[4].startswith(
        "<!-- aw-managed: review metadata lives in"
    )
    assert "- Subject-Id:" not in migrated
    assert "- Verdict:" not in migrated

    idx = migrated.index("## Round 1\n")
    assert migrated[idx:] == rounds_and_tables

    doc = review_findings.parse_review_text(migrated)
    # Phase-A review_findings still looks for legacy metadata bullets (REV-M*), while
    # round/table parsing produces zero structural diagnostics (REV-P*/REV-R*).
    assert all(d.code.startswith("REV-M") for d in doc.diagnostics)
    assert len(doc.rounds) == 1
    assert len(doc.rounds[0].findings) == 1
    assert len(doc.rounds[0].decisions) == 1


def test_research_file_rewrite_mirror_banner_and_summary_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify research file rewrite adds two-key front matter + banner and strips history."""
    repo = _init_repo(tmp_path, monkeypatch, name="res_rewrite")
    rec = repo / ".aw" / "records"
    (rec / "research").mkdir(parents=True)

    r_path = rec / "research" / "20261102-demo-01-rs8801-study.findings.md"
    r_path.write_text(
        "---\n"
        "id: rs8801\n"
        "created: 20261102\n"
        "set: demo\n"
        "order: 01\n"
        "topic: [migration]\n"
        "model: opus\n"
        "kind: findings\n"
        "status: active\n"
        "outcome: adopted\n"
        "summary: Research summary moved into body.\n"
        "consumed-by: [pl0001]\n"
        "---\n\n"
        "# Study Findings\n\n"
        "## Evidence\n\n"
        "```markdown\n"
        "## Workflow history\n\n"
        "- 2026-10-01 note (example): fenced sample\n"
        "```\n\n"
        "## Workflow history\n\n"
        "- 2026-11-02 active (tester): created\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("research",),
        include_reviews=False,
    )
    migrated = r_path.read_text(encoding="utf-8")
    assert migrated.splitlines()[:4] == [
        "---",
        "id: rs8801",
        "status: active",
        "---",
    ]
    assert migrated.splitlines()[4].startswith("<!-- aw-managed:")
    assert artifact_meta.parse_artifact_mirror(migrated) == {
        "id": "rs8801",
        "status": "active",
    }
    assert "## Summary\n\nResearch summary moved into body.\n" in migrated
    assert "- 2026-10-01 note (example): fenced sample" in migrated
    assert "- 2026-11-02 active (tester): created" not in migrated


def test_excluded_comms_data_readmes_and_templates_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify full conversion leaves comms, .data/, READMEs, and the six templates untouched."""
    repo = _init_repo(tmp_path, monkeypatch, name="excluded_all")
    rec = repo / ".aw" / "records"
    (rec / "research" / "reference" / "202611").mkdir(parents=True)

    # One real research record under research/reference/ (OQ-02: migrates as research).
    ref_doc = (
        rec
        / "research"
        / "reference"
        / "202611"
        / "20261101-demo-01-rs9901-ref-study.research-report.md"
    )
    ref_doc.write_text(
        "---\n"
        "id: rs9901\n"
        "created: 20261101\n"
        "set: demo\n"
        "order: 01\n"
        "topic: [ref]\n"
        "model: opus\n"
        "kind: research-report\n"
        "status: reference\n"
        "outcome: adopted\n"
        "summary: Reference report.\n"
        "consumed-by: []\n"
        "---\n\n# Reference Report\n\nBody.\n",
        encoding="utf-8",
    )

    protected: Dict[Path, bytes] = {
        rec / "README.md": b"# Records README\n",
        rec / "research" / "README.md": b"# Research README\n",
        rec / "research" / "pkg" / "README.md": b"# Nested Research README\n",
        rec / "walkthroughs" / "README.md": b"# Walkthroughs README\n",
        rec / "roadmaps" / "README.md": b"# Roadmaps README\n",
        rec / "reviews" / "README.md": b"# Reviews README\n",
        rec
        / "comms"
        / "shared"
        / "inbox"
        / "20261106-msg.md": b"# Comms\nUntouched.\n",
        rec / "research" / "pkg.data" / "s1.md": b"# Data 1\nRaw bytes.\n",
        rec / "prompts" / "prompt-library" / "t1.md": b"Template 1\n",
        rec / "prompts" / "prompt-library" / "t2.md": b"Template 2\n",
        rec / "prompts" / "prompt-library" / "t3.md": b"Template 3\n",
        rec / "prompts" / "prompt-library" / "t4.md": b"Template 4\n",
        rec / "prompts" / "conformance-results-template.md": b"# Conformance\n",
        rec
        / "research"
        / "20260712-0156-14-chatgpt-modular-report-template.md": b"# ChatGPT Report Template\n",
    }
    for p, raw in protected.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)

    before = {
        p.relative_to(repo).as_posix(): hashlib.sha256(raw).hexdigest()
        for p, raw in protected.items()
    }

    res = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=m0001_convert.ALL_RECORD_TYPES,
    )
    assert res["by_type"]["research"] == 1
    assert (rec / "meta" / "rs9901.jsonl").is_file()

    for p, orig_bytes in protected.items():
        rel = p.relative_to(repo).as_posix()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == before[rel], rel
        assert p.read_bytes() == orig_bytes, rel


# --------------------------------------------------------------------------------------
# IPD s4utmv: status-less research records, id-only mirrors, bidirectional drift & strictness
# --------------------------------------------------------------------------------------


def test_research_prompt_roundtrip_check_meta_attention_and_find_parity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify two-axis research-prompt keeps id-only mirror, clean check meta/attention, and find '-' parity."""
    repo = _init_repo(tmp_path, monkeypatch, name="prompt_parity")
    rec = repo / ".aw" / "records"
    (rec / "research").mkdir(parents=True)

    r_prompt = (
        rec / "research" / "20261018-actorenv-00-rs5004-actor-prompt.research-prompt.md"
    )
    r_prompt.write_text(
        "---\n"
        "id: rs5004\n"
        "created: 20261018\n"
        "set: actorenv\n"
        "order: 00\n"
        "topic: [actor]\n"
        "kind: research-prompt\n"
        "outcome: none-yet\n"
        "summary: Standard two-axis research prompt.\n"
        "consumed-by: []\n"
        "---\n\n# Research Prompt\n\nPrompt body.\n",
        encoding="utf-8",
    )
    r_active = rec / "research" / "20261018-actorenv-01-rs5005-findings.findings.md"
    r_active.write_text(
        "---\n"
        "id: rs5005\n"
        "created: 20261018\n"
        "set: actorenv\n"
        "order: 01\n"
        "topic: [actor]\n"
        "kind: findings\n"
        "status: active\n"
        "outcome: informational\n"
        "summary: Companion active findings.\n"
        "consumed-by: []\n"
        "---\n\n# Findings\n\nBody.\n",
        encoding="utf-8",
    )

    pre_rec = tmp_path / "pre_prompt_parity_records"
    shutil.copytree(rec, pre_rec)
    pre_find = _find_research_statuses(repo)
    assert pre_find == {"rs5004": "-", "rs5005": "active"}

    summary = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("research",),
        include_reviews=False,
    )
    assert summary["by_type"]["research"] == 2

    ev_p = _read_jsonl(rec / "meta" / "rs5004.jsonl")
    st_p, _, _, _ = artifact_meta.replay(
        "rs5004", "research", ev_p, records_root=rec, migration_import=True
    )
    assert st_p.status is None
    assert "status" not in st_p.fields
    migrated_p = r_prompt.read_text(encoding="utf-8")
    assert migrated_p.splitlines()[:3] == ["---", "id: rs5004", "---"]
    assert migrated_p.splitlines()[3].startswith("<!-- aw-managed:")
    assert "status:" not in "\n".join(migrated_p.splitlines()[:4])

    rt = m0001_verify.verify_round_trip(
        repo,
        pre_conversion_records_root=pre_rec,
        converted_records_root=rec,
    )
    assert rt["passed"] is True, rt["errors"]
    assert rt["errors"] == []

    assert chain.repo_has_legacy_records(repo, records_root=rec) is False

    rc_meta, out_meta, err_meta = _run_cli(
        ["check", "meta", "--agent", "--dir", str(repo)]
    )
    assert rc_meta == 0, f"aw check meta failed: {err_meta}\n{out_meta}"
    meta_records = _parse_agent_jsonl(out_meta)
    assert meta_records[-1]["outcome"] == "clean"
    assert meta_records[-1]["total"] == 0

    rc_att, out_att, err_att = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_att == 0, f"aw attention failed: {err_att}\n{out_att}"
    att_doc = json.loads(out_att)
    assert att_doc.get("valid") is True
    assert [
        v
        for v in att_doc.get("violations", [])
        if v.get("code") == "attention.unknown-status"
    ] == []

    post_find = _find_research_statuses(repo)
    assert post_find == pre_find
    assert post_find["rs5004"] == "-"
    assert post_find["rs5005"] == "active"


def test_statusless_legacy_research_note_id_only_mirror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify legacy status-less research note migrates with id-only mirror and status=None."""
    repo = _init_repo(tmp_path, monkeypatch, name="statusless_note")
    rec = repo / ".aw" / "records"
    (rec / "research").mkdir(parents=True)

    note_path = rec / "research" / "20260708-demo-01-rs5003-survey-notes.notes.md"
    note_path.write_text(
        "# Survey Notes\n\nUnstructured legacy research note with no front matter.\n",
        encoding="utf-8",
    )

    pre_rec = tmp_path / "pre_statusless_note_records"
    shutil.copytree(rec, pre_rec)

    summary = m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("research",),
        include_reviews=False,
    )
    assert summary["by_type"]["research"] == 1

    ev = _read_jsonl(rec / "meta" / "rs5003.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "rs5003", "research", ev, records_root=rec, migration_import=True
    )
    assert st.status is None
    assert st.legacy_raw_status is None
    assert "status" not in st.fields

    migrated = note_path.read_text(encoding="utf-8")
    assert migrated.splitlines()[:3] == ["---", "id: rs5003", "---"]
    assert migrated.splitlines()[3].startswith("<!-- aw-managed:")
    assert artifact_meta.parse_artifact_mirror(migrated, allow_statusless=True) == {
        "id": "rs5003",
        "status": None,
    }
    assert "# Survey Notes" in migrated

    rt = m0001_verify.verify_round_trip(
        repo,
        pre_conversion_records_root=pre_rec,
        converted_records_root=rec,
    )
    assert rt["passed"] is True, rt["errors"]
    assert rt["errors"] == []

    assert chain.repo_has_legacy_records(repo, records_root=rec) is False

    rc_meta, out_meta, err_meta = _run_cli(
        ["check", "meta", "--agent", "--dir", str(repo)]
    )
    assert rc_meta == 0, f"aw check meta failed: {err_meta}\n{out_meta}"
    assert _parse_agent_jsonl(out_meta)[-1]["total"] == 0

    _rc_att, out_att, err_att = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert out_att.strip(), f"aw attention emitted no JSON: {err_att}"
    att_doc = json.loads(out_att)
    codes = [v.get("code") for v in att_doc.get("violations", [])]
    assert "attention.unknown-status" not in codes


def test_research_status_mirror_drift_bidirectional_and_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify bidirectional meta.status-mirror-drift on research and canonical repair."""
    repo = _init_repo(tmp_path, monkeypatch, name="research_drift_repair")
    rec = repo / ".aw" / "records"
    (rec / "research").mkdir(parents=True)

    r_active = rec / "research" / "20261120-demo-01-rs6001-findings.findings.md"
    r_active.write_text(
        "---\n"
        "id: rs6001\n"
        "created: 20261120\n"
        "set: demo\n"
        "order: 01\n"
        "topic: [drift]\n"
        "kind: findings\n"
        "status: active\n"
        "outcome: informational\n"
        "summary: Active research findings.\n"
        "consumed-by: []\n"
        "---\n\n# Active Findings\n\nBody.\n",
        encoding="utf-8",
    )

    r_prompt = rec / "research" / "20261120-demo-02-rs6002-prompt.research-prompt.md"
    r_prompt.write_text(
        "---\n"
        "id: rs6002\n"
        "created: 20261120\n"
        "set: demo\n"
        "order: 02\n"
        "topic: [drift]\n"
        "kind: research-prompt\n"
        "outcome: none-yet\n"
        "summary: Status-less research prompt.\n"
        "consumed-by: []\n"
        "---\n\n# Research Prompt\n\nBody.\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(
        repo,
        records_root=rec,
        repo_root=repo,
        record_types=("research",),
        include_reviews=False,
    )

    # Clean baseline after migration.
    rc0, out0, err0 = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
    assert rc0 == 0, f"Baseline check meta failed: {err0}\n{out0}"

    # Direction 1: status-bearing research record drops its `status:` mirror line.
    active_txt = r_active.read_text(encoding="utf-8")
    assert "status: active\n" in active_txt
    r_active.write_text(active_txt.replace("status: active\n", "", 1), encoding="utf-8")

    rc1, out1, _err1 = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
    assert rc1 == 1
    items1 = [r for r in _parse_agent_jsonl(out1) if r.get("kind") == "item"]
    assert any(
        it.get("rule") == "meta.status-mirror-drift"
        and "rs6001" in str(it.get("location"))
        for it in items1
    ), items1

    rc_rep1, out_rep1, err_rep1 = _run_cli(
        ["meta", "repair", "rs6001", "--apply", "--dir", str(repo)]
    )
    assert rc_rep1 == 0, f"meta repair rs6001 failed: {err_rep1}\n{out_rep1}"
    repaired_active = r_active.read_text(encoding="utf-8")
    assert repaired_active.splitlines()[:4] == [
        "---",
        "id: rs6001",
        "status: active",
        "---",
    ]

    # Direction 2: status-less research record gains a spurious `status: draft` mirror line.
    prompt_txt = r_prompt.read_text(encoding="utf-8")
    assert prompt_txt.splitlines()[:3] == ["---", "id: rs6002", "---"]
    r_prompt.write_text(
        prompt_txt.replace("id: rs6002\n---", "id: rs6002\nstatus: draft\n---", 1),
        encoding="utf-8",
    )

    rc2, out2, _err2 = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
    assert rc2 == 1
    items2 = [r for r in _parse_agent_jsonl(out2) if r.get("kind") == "item"]
    assert any(
        it.get("rule") == "meta.status-mirror-drift"
        and "rs6002" in str(it.get("location"))
        for it in items2
    ), items2

    rc_rep2, out_rep2, err_rep2 = _run_cli(
        ["meta", "repair", "rs6002", "--apply", "--dir", str(repo)]
    )
    assert rc_rep2 == 0, f"meta repair rs6002 failed: {err_rep2}\n{out_rep2}"
    repaired_prompt = r_prompt.read_text(encoding="utf-8")
    assert repaired_prompt.splitlines()[:3] == ["---", "id: rs6002", "---"]
    assert repaired_prompt.splitlines()[3].startswith("<!-- aw-managed:")
    assert "status:" not in "\n".join(repaired_prompt.splitlines()[:4])

    rc_final, out_final, err_final = _run_cli(
        ["check", "meta", "--agent", "--dir", str(repo)]
    )
    assert rc_final == 0, f"Post-repair check meta failed: {err_final}\n{out_final}"


def test_non_research_id_only_mirror_still_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify non-research 1-key mirrors remain rejected by parse_artifact_mirror and chain."""
    one_key_text = (
        "---\n"
        "id: pl9001\n"
        "---\n"
        "<!-- aw-managed: metadata lives in .aw/records/meta/pl9001.jsonl -->\n"
        "# Plan\n"
    )
    with pytest.raises(ValueError, match="expected exactly 2 front-matter keys"):
        artifact_meta.parse_artifact_mirror(one_key_text)

    assert artifact_meta.parse_artifact_mirror(one_key_text, allow_statusless=True) == {
        "id": "pl9001",
        "status": None,
    }
    with pytest.raises(ValueError, match="expected 1 or 2 front-matter keys"):
        artifact_meta.parse_artifact_mirror("---\n---\n", allow_statusless=True)
    with pytest.raises(ValueError, match="expected 1 or 2 front-matter keys"):
        artifact_meta.parse_artifact_mirror(
            "---\nid: pl9001\nstatus: draft\nextra: bad\n---\n",
            allow_statusless=True,
        )
    with pytest.raises(ValueError, match="line 1 must be 'id: <id6>'"):
        artifact_meta.parse_artifact_mirror(
            "---\nstatus: draft\n---\n",
            allow_statusless=True,
        )

    # Plan with 1-key id-only mirror must still be detected as legacy by repo_has_legacy_records.
    repo_plan = _init_repo(tmp_path, monkeypatch, name="strict_plan")
    rec_plan = repo_plan / ".aw" / "records"
    (rec_plan / "plans" / "pending").mkdir(parents=True)
    (
        rec_plan / "plans" / "pending" / "20261121-demo-01-pl9001-strict-plan.ipd.md"
    ).write_text(one_key_text, encoding="utf-8")
    assert chain.repo_has_legacy_records(repo_plan, records_root=rec_plan) is True

    # Spec with 1-key id-only mirror must still be detected as legacy by repo_has_legacy_records.
    repo_spec = _init_repo(tmp_path, monkeypatch, name="strict_spec")
    rec_spec = repo_spec / ".aw" / "records"
    (rec_spec / "specs" / "draft").mkdir(parents=True)
    (
        rec_spec / "specs" / "draft" / "20261121-demo-01-sp9002-strict-spec.spec.md"
    ).write_text(
        "---\n"
        "id: sp9002\n"
        "---\n"
        "<!-- aw-managed: metadata lives in .aw/records/meta/sp9002.jsonl -->\n"
        "# Spec\n",
        encoding="utf-8",
    )
    assert chain.repo_has_legacy_records(repo_spec, records_root=rec_spec) is True

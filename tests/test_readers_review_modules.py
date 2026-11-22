"""Behavioral pinning tests for review and orchestration module readers (IPDs y4spqy, 0i0zsg).

Pins the observable behavior of:
- ``agent_workflows.review_findings``: ``parse_review_text``, ``parse_review_file``,
  ``subject_review_records``, ``subject_gating_blocks``, ``review_attestation_missing``.
- ``agent_workflows.artifact_audit``: ``read_declared_status`` (including D-1 plan vs non-plan
  handling), ``audit_artifact``, ``audit_tracked_artifact``.
- ``agent_workflows.reviews``: ``_resolve_selector_paths``, ``collect_decisions``,
  ``run_decisions``.
- ``agent_workflows.review_sequence``: ``structural_diff``, ``check_S5``, ``verdict_outputs``,
  ``restore_pre_s7_plan``, ``check_S7``.
- ``agent_workflows.review_tier``: ``tier_facts``.
- ``agent_workflows.review_rereview``: ``rereview_triggers``, ``check_limit_s7``.
- ``agent_workflows.orchestrator_readiness``: ``resolve_all_set_memberships``,
  ``review_readiness``, ``run_coverage``.

All fixtures live in isolated ``tmp_path`` repositories; no test reads production source or the
live repository's ``.aw/records/`` tree.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_workflows import (
    artifact_audit,
    coverage_record,
    orchestrator_readiness,
    review_rereview,
    review_sequence,
    review_tier,
    reviews,
)
from agent_workflows import review_findings as rf
from tests.record_builder import RecordBuilder
from tests.test_ipd_lint import _CONFORMING_CHILD_BODY

pytestmark = pytest.mark.core


def _finding(
    fid: str = "F-01",
    severity: str = "high",
    decision: str = "open",
) -> rf.Finding:
    return rf.Finding(
        id=fid,
        severity=severity,
        scope="in-scope",
        area="rubric",
        evidence="mod.py:1",
        finding="sample finding",
        remediation_risk="low",
        decision=decision,
        resolution="pending",
    )


def _decision(
    did: str = "D-01",
    reversible: str = "yes",
    question: str = "which source should be read?",
) -> rf.Decision:
    return rf.Decision(
        id=did,
        question=question,
        chosen="cached metadata",
        alternatives="raw regex scan",
        basis="spec 4sd62s",
        reversible=reversible,
    )


class TestReviewFindingsReaders:
    """Pins front-matter parsing, subject lookup, gating blocks, and review attestation."""

    def test_review_findings_parse_text_reads_front_matter_and_body_rounds(
        self,
    ) -> None:
        text = rf.render_review(
            subject_id="rf1001",
            subject_type="ipd",
            reviewed_at="2026-11-09",
            reviewer="opencode/test",
            verdict="APPROVE WITH REVISIONS APPLIED",
            rounds=[
                rf.Round(
                    1,
                    (_finding("PR-001", "high", "open"),),
                    (_decision("D-01", "yes"),),
                ),
                rf.Round(
                    2,
                    (_finding("PR-001", "high", "fixed"),),
                    (_decision("D-02", "no"),),
                ),
            ],
        )
        doc = rf.parse_review_text(text)
        assert doc.diagnostics == ()
        assert doc.subject_id == "rf1001"
        assert doc.subject_type == "ipd"
        assert doc.reviewed_at == "2026-11-09"
        assert doc.reviewer == "opencode/test"
        assert doc.verdict == "APPROVE WITH REVISIONS APPLIED"
        assert len(doc.rounds) == 2
        assert doc.current_round().number == 2
        assert doc.current_findings()[0].decision == "fixed"
        assert doc.current_decisions()[0].id == "D-02"
        assert doc.unresolved_findings() == ()

    def test_review_findings_parse_text_reports_missing_and_invalid_front_matter(
        self,
    ) -> None:
        bad_type = rf.render_review(
            subject_id="rf1002",
            subject_type="backlog",
            reviewed_at="2026-11-09",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding("F-1", "low", "fixed"),), ())],
        )
        doc_bad_type = rf.parse_review_text(bad_type)
        codes_bad = {d.code for d in doc_bad_type.diagnostics}
        assert rf.D_UNKNOWN_SUBJECT_TYPE in codes_bad
        assert doc_bad_type.subject_type == "backlog"

        retired_field = bad_type.replace(
            "- Subject-Id: rf1002", "- Plan-Id: rf1002"
        ).replace("- Subject-Type: backlog", "- Subject-Type: ipd")
        doc_retired = rf.parse_review_text(retired_field)
        codes_retired = {d.code for d in doc_retired.diagnostics}
        assert rf.D_MISSING_META in codes_retired
        assert doc_retired.subject_id == ""

        no_rounds = (
            "# Review findings: ipd rf1003\n\n"
            "- Subject-Id: rf1003\n"
            "- Subject-Type: ipd\n"
            "- Reviewed-At: 2026-11-09\n"
            "- Reviewer: tester\n"
            "- Verdict: APPROVE\n"
        )
        doc_no_rounds = rf.parse_review_text(no_rounds)
        assert {d.code for d in doc_no_rounds.diagnostics} == {rf.D_NO_ROUNDS}
        assert doc_no_rounds.subject_id == "rf1003"

    def test_review_findings_subject_records_and_gating_blocks(
        self, tmp_path: Path
    ) -> None:
        builder = RecordBuilder(tmp_path)
        builder.plan(
            id6="pl2001",
            title="Plan with gating finding",
            when="2026-11-09",
            status="approved",
            set="demo",
            order=1,
            slug="plan-gating",
        )
        rev_path = builder.review(
            "pl2001",
            when="2026-11-09",
            set="demo",
            order=1,
            slug="plan-gating",
            reviewer="tester",
            verdict="REVIEWED - OPEN QUESTIONS",
            rounds=[
                rf.Round(
                    1,
                    (
                        _finding("F-01", "high", "open"),
                        _finding("F-02", "low", "open"),
                    ),
                    (),
                )
            ],
        )

        # Listing records finds the review for pl2001 and nothing for an unrelated id6.
        assert rf.subject_review_records(tmp_path, "pl2001") == (rev_path,)
        assert rf.subject_review_records(tmp_path, "pl9999") == ()

        # High threshold blocks on F-01 only; off disables gating.
        blocks = rf.subject_gating_blocks(tmp_path, "pl2001", threshold="high")
        assert len(blocks) == 1
        assert blocks[0].kind == "finding"
        assert blocks[0].finding_id == "F-01"
        assert rf.subject_gating_blocks(tmp_path, "pl2001", threshold="off") == ()

        # Fixing F-01 in round 2 clears gating blocks.
        rf.write_review(
            rev_path,
            subject_id="pl2001",
            subject_type="ipd",
            reviewed_at="2026-11-09",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(1, (_finding("F-01", "high", "open"),), ()),
                rf.Round(2, (_finding("F-01", "high", "fixed"),), ()),
            ],
        )
        assert rf.subject_gating_blocks(tmp_path, "pl2001", threshold="high") == ()

    def test_review_findings_gating_blocks_malformed_record(
        self, tmp_path: Path
    ) -> None:
        rev_dir = tmp_path / ".aw" / "records" / "reviews"
        rev_dir.mkdir(parents=True)
        bad_rev = rev_dir / "20261109-demo-01-pl2002-bad.review.md"
        bad_rev.write_text(
            "# Review findings: ipd pl2002\n\n"
            "- Subject-Id: pl2002\n"
            "- Subject-Type: ipd\n"
            "- Reviewed-At: 2026-11-09\n"
            "- Reviewer: tester\n"
            "- Verdict: APPROVE\n\n"
            "no rounds section here\n",
            encoding="utf-8",
        )
        assert rf.subject_review_records(tmp_path, "pl2002") == (bad_rev,)
        blocks = rf.subject_gating_blocks(tmp_path, "pl2002", threshold="high")
        assert len(blocks) == 1
        assert blocks[0].kind == "malformed"
        assert rf.D_NO_ROUNDS in blocks[0].detail

    def test_review_findings_attestation_missing_covers_gate_refinement_malformed_and_wrong_type(
        self, tmp_path: Path
    ) -> None:
        builder = RecordBuilder(tmp_path)
        builder.spec(
            id6="sp3001",
            status="to-review",
            title="Attested spec",
            when="2026-11-09",
            slug="attested-spec",
        )
        builder.spec(
            id6="sp3002",
            status="to-review",
            title="Refinement only spec",
            when="2026-11-09",
            slug="refinement-only",
        )
        builder.spec(
            id6="sp3003",
            status="to-review",
            title="Wrong type spec",
            when="2026-11-09",
            slug="wrong-type",
        )
        builder.spec(
            id6="sp3004",
            status="to-review",
            title="Malformed review spec",
            when="2026-11-09",
            slug="malformed-review",
        )

        # Unattested before any review exists
        missing_before = rf.review_attestation_missing(tmp_path, "sp3001", "spec")
        assert missing_before is not None
        assert "sp3001" in missing_before

        # Gate review attests sp3001
        builder.review(
            "sp3001",
            subject_type="spec",
            when="2026-11-09",
            set="demo",
            order=1,
            slug="attested-spec",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding("SR-01", "low", "fixed"),), ())],
        )
        assert rf.review_attestation_missing(tmp_path, "sp3001", "spec") is None

        # Refinement review never attests sp3002
        builder.review(
            "sp3002",
            subject_type="spec",
            when="2026-11-09",
            set="demo",
            order=2,
            slug="spec-refinement-sp3002",
            reviewer="tester",
            verdict="REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION",
            rounds=[rf.Round(1, (_finding("SR-01", "low", "fixed"),), ())],
        )
        refinement_reason = rf.review_attestation_missing(tmp_path, "sp3002", "spec")
        assert refinement_reason is not None
        assert "REFINEMENT" in refinement_reason

        # Wrong Subject-Type (ipd instead of spec) refuses sp3003
        builder.review(
            "sp3003",
            subject_type="ipd",
            when="2026-11-09",
            set="demo",
            order=3,
            slug="wrong-type",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding("PR-01", "low", "fixed"),), ())],
        )
        wrong_type_reason = rf.review_attestation_missing(tmp_path, "sp3003", "spec")
        assert wrong_type_reason is not None
        assert "different subject type" in wrong_type_reason

        # Malformed review refuses sp3004
        bad_spec_rev = (
            tmp_path
            / ".aw"
            / "records"
            / "reviews"
            / "20261109-demo-04-sp3004-malformed.review.md"
        )
        bad_spec_rev.write_text(
            "# Review findings: spec sp3004\n\n"
            "- Subject-Id: sp3004\n"
            "- Subject-Type: spec\n"
            "- Reviewed-At: 2026-11-09\n"
            "- Reviewer: tester\n"
            "- Verdict: APPROVE\n",
            encoding="utf-8",
        )
        malformed_reason = rf.review_attestation_missing(tmp_path, "sp3004", "spec")
        assert malformed_reason is not None
        assert "does NOT parse" in malformed_reason

        # Empty id6 and missing repo fail closed
        assert rf.review_attestation_missing(tmp_path, "", "spec") is not None
        assert (
            rf.review_attestation_missing(tmp_path / "does-not-exist", "sp3001", "spec")
            is not None
        )


class TestArtifactAuditReaders:
    """Pins read_declared_status (multi-type + D-1), audit_artifact, and audit_tracked_artifact."""

    def test_read_declared_status_across_plan_spec_backlog_and_non_plan(
        self, tmp_path: Path
    ) -> None:
        builder = RecordBuilder(tmp_path)
        plan_p = builder.plan(
            id6="aa1001",
            status="approved",
            when="2026-11-09",
            set="aud",
            order=1,
            slug="plan-one",
        )
        spec_p = builder.spec(
            id6="aa1002",
            status="implemented",
            when="2026-11-09",
            slug="spec-one",
            disposition="implemented",
        )
        bk_p = builder.backlog(
            id6="aa1003",
            status="graduated",
            when="2026-11-09",
            set="aud",
            order=1,
            slug="bk-one",
            disposition="graduated",
        )

        assert artifact_audit.read_declared_status(plan_p) == "approved"
        assert artifact_audit.read_declared_status(spec_p) == "implemented"
        assert artifact_audit.read_declared_status(bk_p) == "graduated"

        # Non-plan standalone file with multi-word status stays None.
        standalone = tmp_path / "standalone.md"
        standalone.write_text(
            RecordBuilder().plan(
                id6="aa1004",
                body="",
                raw_fields={"Status": "EXECUTED (approved by maintainer)"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        assert artifact_audit.read_declared_status(standalone) is None

        # Missing file returns None without raising.
        assert artifact_audit.read_declared_status(tmp_path / "missing.md") is None

    def test_read_declared_status_plan_multi_word_d1(self, tmp_path: Path) -> None:
        # Decision D-1: PLAN records return canonical normalized `executed` for multi-word
        # executed status (previously `_STATUS_LINE_RE` returned None).
        ex_dir = tmp_path / ".aw" / "records" / "plans" / "executed"
        ex_dir.mkdir(parents=True)
        multi_plan = ex_dir / "20261109-aud-02-aa1005-multi.ipd.md"
        multi_plan.write_text(
            RecordBuilder().plan(
                id6="aa1005",
                body="",
                raw_fields={"Status": "EXECUTED (approved by maintainer)"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        assert artifact_audit.read_declared_status(multi_plan) == "executed"

        # Warm the SQLite cache and verify the cached artifact_meta.query path agrees under D-1.
        from agent_workflows import artifact_meta as _am

        ctx = _am.legacy_context(tmp_path)
        _am.query(type="ipd", project_context=ctx)
        assert (Path(ctx.logical_roots["state"]) / "index.db").exists()
        assert (
            artifact_audit.read_declared_status(multi_plan, repo_root=tmp_path)
            == "executed"
        )

    def test_audit_artifact_and_tracked_artifact_verdicts(self, tmp_path: Path) -> None:
        builder = RecordBuilder(tmp_path)
        ex_plan = builder.plan(
            id6="aa2001",
            status="executed",
            when="2026-11-09",
            set="aud",
            order=1,
            slug="clean-exec",
            disposition="executed",
        )
        clean = artifact_audit.audit_artifact(tmp_path, "aa2001", status="executed")
        assert not clean.has_discrepancy
        assert clean.file_status == "executed"
        assert clean.difference_class == artifact_audit.CLASS_UNCHANGED

        # Tracked-only sweep: terminal file declaring a different terminal status flags location_mismatch.
        mismatch_plan = builder.plan(
            id6="aa2002",
            status="superseded",
            when="2026-11-09",
            set="aud",
            order=2,
            slug="wrong-terminal",
            disposition="executed",
        )
        tracked_clean = artifact_audit.audit_tracked_artifact(tmp_path, ex_plan)
        assert tracked_clean is None
        tracked_drift = artifact_audit.audit_tracked_artifact(tmp_path, mismatch_plan)
        assert tracked_drift is not None
        assert tracked_drift.location_mismatch is True
        assert tracked_drift.actual_dir == "executed"
        assert tracked_drift.expected_dir == "superseded"


class TestReviewsModuleAuditReaders:
    """Pins reviews._resolve_selector_paths, collect_decisions, and run_decisions."""

    def test_resolve_selector_paths_and_collect_decisions(self, tmp_path: Path) -> None:
        builder = RecordBuilder(tmp_path)
        builder.plan(
            id6="rv1001",
            status="to-review",
            when="2026-11-09",
            set="revset",
            order=1,
            slug="first-plan",
        )
        rev1 = builder.review(
            "rv1001",
            when="2026-11-09",
            set="revset",
            order=1,
            slug="first-plan",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(
                    1, (_finding("F-1", "low", "fixed"),), (_decision("D-1", "yes"),)
                ),
                rf.Round(
                    2, (_finding("F-1", "low", "fixed"),), (_decision("D-2", "no"),)
                ),
            ],
        )
        builder.plan(
            id6="rv1002",
            status="to-review",
            when="2026-11-09",
            set="revset",
            order=2,
            slug="second-plan",
        )
        builder.review(
            "rv1002",
            when="2026-11-09",
            set="revset",
            order=2,
            slug="second-plan",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(
                    1, (_finding("F-2", "low", "fixed"),), (_decision("D-9", "yes"),)
                ),
            ],
        )

        # Direct path and subject id6 selector resolve to rev1.
        direct_paths, note = reviews._resolve_selector_paths(tmp_path, str(rev1))
        assert direct_paths == [rev1]
        assert note == ""

        sel_paths, sel_note = reviews._resolve_selector_paths(tmp_path, "rv1001")
        assert sel_paths == [rev1]
        assert sel_note == ""

        # Unknown selector returns empty with an explanatory note.
        miss_paths, miss_note = reviews._resolve_selector_paths(tmp_path, "zzzzzz")
        assert miss_paths == []
        assert "zzzzzz" in miss_note

        # collect_decisions gathers all rounds by default, or current round only.
        all_rows, diags = reviews.collect_decisions(tmp_path)
        assert diags == []
        assert [(r.subject_id, r.id, r.round_number) for r in all_rows] == [
            ("rv1001", "D-1", 1),
            ("rv1001", "D-2", 2),
            ("rv1002", "D-9", 1),
        ]

        cur_rows, _ = reviews.collect_decisions(tmp_path, current_round_only=True)
        assert [(r.subject_id, r.id) for r in cur_rows] == [
            ("rv1001", "D-2"),
            ("rv1002", "D-9"),
        ]

        # run_decisions JSON output filters by selector and --irreversible.
        buf = io.StringIO()
        args = SimpleNamespace(
            dir=str(tmp_path),
            selector="rv1001",
            irreversible=True,
            agent=False,
            json=True,
            no_color=True,
        )
        with redirect_stdout(buf):
            rc = reviews.run_decisions(args)
        assert rc == 0
        payload = json.loads(buf.getvalue())
        data = payload.get("data", payload)
        assert data["total"] == 1
        assert data["decisions"][0]["id"] == "D-2"
        assert data["decisions"][0]["subject_id"] == "rv1001"

    def test_resolve_selector_paths_matches_cached_subject_id_with_distinct_filename_ref(
        self, tmp_path: Path
    ) -> None:
        builder = RecordBuilder(tmp_path)
        builder.plan(
            id6="rv2001",
            status="to-review",
            when="2026-11-09",
            set="revset",
            order=3,
            slug="plan-with-ref-review",
        )
        rev_dir = tmp_path / ".aw" / "records" / "reviews"
        rev_dir.mkdir(parents=True, exist_ok=True)
        # Filename carries ref id6 `ref999`, while front matter declares `- Subject-Id: rv2001`.
        ref_rev = rev_dir / "20261109-revset-03-ref999-distinct-filename.review.md"
        rf.write_review(
            ref_rev,
            subject_id="rv2001",
            subject_type="ipd",
            reviewed_at="2026-11-09",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(
                    1, (_finding("F-3", "low", "fixed"),), (_decision("D-3", "yes"),)
                )
            ],
        )

        matched, note = reviews._resolve_selector_paths(tmp_path, "rv2001")
        assert matched == [ref_rev]
        assert note == ""

    def test_resolve_selector_paths_legacy_agents_dir_does_not_leak_other_subjects(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".aw" / "records").mkdir(parents=True)
        retention_manifest = (
            tmp_path
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        retention_manifest.parent.mkdir(parents=True)
        retention_manifest.write_text("{}\n", encoding="utf-8")
        legacy_dir = tmp_path / ".agents" / "reviews"
        legacy_dir.mkdir(parents=True)
        assert legacy_dir in rf.review_dirs(tmp_path)
        rev_a = legacy_dir / "20261109-leg-01-leg101-first.review.md"
        rev_b = legacy_dir / "20261109-leg-02-leg202-second.review.md"
        rf.write_review(
            rev_a,
            subject_id="leg101",
            subject_type="ipd",
            reviewed_at="2026-11-09",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(
                    1, (_finding("F-1", "low", "fixed"),), (_decision("D-1", "yes"),)
                )
            ],
        )
        rf.write_review(
            rev_b,
            subject_id="leg202",
            subject_type="ipd",
            reviewed_at="2026-11-09",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[
                rf.Round(
                    1, (_finding("F-2", "low", "fixed"),), (_decision("D-2", "yes"),)
                )
            ],
        )

        # Unrelated id6 must not match legacy reviews belonging to other subjects.
        miss_paths, miss_note = reviews._resolve_selector_paths(tmp_path, "zzzzzz")
        assert miss_paths == []
        assert "zzzzzz" in miss_note

        # Matching id6 returns only its own legacy review, not siblings in .agents/reviews.
        hit_paths, hit_note = reviews._resolve_selector_paths(tmp_path, "leg101")
        assert hit_paths == [rev_a]
        assert hit_note == ""

    def test_review_findings_attestation_matches_cached_query(
        self, tmp_path: Path
    ) -> None:
        from agent_workflows import artifact_meta as _am

        builder = RecordBuilder(tmp_path)
        builder.spec(
            id6="sp4001",
            status="to-review",
            title="Cached query spec",
            when="2026-11-09",
            slug="cached-query-spec",
        )
        builder.review(
            "sp4001",
            subject_type="spec",
            when="2026-11-09",
            set="demo",
            order=1,
            slug="cached-query-spec",
            reviewer="tester",
            verdict="APPROVE",
            rounds=[rf.Round(1, (_finding("SR-01", "low", "fixed"),), ())],
        )
        ctx = _am.legacy_context(tmp_path)
        q_rows = _am.query(latest_gate_review_of="sp4001", project_context=ctx)
        assert [s.id6 for s in q_rows] == ["sp4001"]
        assert rf.review_attestation_missing(tmp_path, "sp4001", "spec") is None
        assert rf.review_attestation_missing(tmp_path, "sp4001", "ipd") is not None

        # Refinement-only spec has no gate row in query(latest_gate_review_of=...) and is refused.
        builder.spec(
            id6="sp4002",
            status="to-review",
            title="Refinement query spec",
            when="2026-11-09",
            slug="refinement-query-spec",
        )
        builder.review(
            "sp4002",
            subject_type="spec",
            when="2026-11-09",
            set="demo",
            order=2,
            slug="spec-refinement-sp4002",
            reviewer="tester",
            verdict="REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION",
            rounds=[rf.Round(1, (_finding("SR-01", "low", "fixed"),), ())],
        )
        assert _am.query(latest_gate_review_of="sp4002", project_context=ctx) == []
        ref_reason = rf.review_attestation_missing(tmp_path, "sp4002", "spec")
        assert ref_reason is not None
        assert "REFINEMENT" in ref_reason


_SNAPSHOT_PLAN = """# IPD: Pinning snapshot plan

- Date: 2026-11-09
- Kind: child
- Concern: Pin reader behavior before and after moving onto artifact_meta.
- Scope: Snapshot reader tests only.
- Scope-Paths: agent_workflows/demo.py, docs/demo.spec.md
- Item-Dependencies: executed:ffceq0
- Status: to-review
- Priority: medium
- Work-Kind: feature
- Set: demo (demo set description)
- Order: 2
- Highest E allocated: 01
- Author: tester
- Id: sq1001

## Workflow history

- 2026-11-09 to-review (tester): authored.
- 2026-11-09 draft (tester): created.

## Goal

Pin observable behavior of the snapshot metadata readers.

## Detailed Implementation Checklist (TODO)

### Task group 1: main

- [ ] E-01 Perform sample step.
  - Depends on: none
  - Expected outcome: sample step works
  - Execution state: pending

## Project conventions discovered (Step 0)

- none

## Findings

- none

## Proposed changes (ordered, validatable)

1. Sample step (E-01).

## Deferred / out of scope (with reason)

- none
  - Carrier: none

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- sample test

## Spec / documentation sync

None needed.

## Open questions

### OQ-01: Sample open question

- Blocking: no
- Status: resolved
- Owner: tester
- Resolution or deferral rationale: resolved.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: paste output
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: none
"""


class TestReviewSequenceReaders:
    """Pins review_sequence metadata reads (structural_diff, check_S5, verdict_outputs, restore_pre_s7_plan, check_S7)."""

    def test_sequence_structural_diff_front_matter_and_body_invariants(self) -> None:
        assert review_sequence.structural_diff(_SNAPSHOT_PLAN, _SNAPSHOT_PLAN) == (
            [],
            [],
        )
        assert review_sequence.structural_diff("", "") == ([], [])
        headerless = "# IPD: No metadata\n\n## Goal\nBody only.\n"
        assert review_sequence.structural_diff(headerless, headerless) == ([], [])

        # Canonical front-matter field edits report canonical bullet names.
        for old, new, expected_name in (
            ("- Priority: medium", "- Priority: high", "Priority"),
            ("- Kind: child", "- Kind: orchestrator", "Kind"),
            (
                "- Scope-Paths: agent_workflows/demo.py, docs/demo.spec.md",
                "- Scope-Paths: agent_workflows/other.py",
                "Scope-Paths",
            ),
            (
                "- Item-Dependencies: executed:ffceq0",
                "- Item-Dependencies: none",
                "Item-Dependencies",
            ),
            ("- Status: to-review", "- Status: reviewed", "Status"),
            (
                "- Set: demo (demo set description)",
                "- Set: other (renamed)",
                "Set",
            ),
            ("- Order: 2", "- Order: 3", "Order"),
            ("- Id: sq1001", "- Id: sq9999", "Id"),
        ):
            changed = _SNAPSHOT_PLAN.replace(old, new)
            refused, confirm = review_sequence.structural_diff(_SNAPSHOT_PLAN, changed)
            assert len(refused) == 1
            assert f"Front-matter field {expected_name!r} changed" in refused[0]
            assert confirm == []

        # Adding Readiness, Review-Depth, or an unmapped legacy bullet is refused with its field name.
        with_extra = _SNAPSHOT_PLAN.replace(
            "- Id: sq1001",
            "- Id: sq1001\n- Readiness: go\n- Review-Depth: standard\n- Custom-Note: legacy value",
        )
        refused_extra, confirm_extra = review_sequence.structural_diff(
            _SNAPSHOT_PLAN, with_extra
        )
        assert confirm_extra == []
        assert any("'Readiness'" in msg for msg in refused_extra)
        assert any("'Review-Depth'" in msg for msg in refused_extra)
        assert any("'Custom-Note'" in msg for msg in refused_extra)

        # Body confirm-only edit produces confirm without refused.
        confirm_edit = _SNAPSHOT_PLAN.replace(
            "- Expected outcome: sample step works",
            "- Expected outcome: sample step works cleanly",
        )
        ref_c, conf_c = review_sequence.structural_diff(_SNAPSHOT_PLAN, confirm_edit)
        assert ref_c == []
        assert len(conf_c) == 1
        assert "Expected outcome changed" in conf_c[0]

    def test_sequence_check_s5_declared_id_and_idless_fallback(self) -> None:
        review_with_high = (
            "## Round 1\n\n"
            "### Findings\n"
            "| Id | Severity | Scope | Area | Evidence | Finding | Remediation risk | Decision | Resolution |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            "| F-01 | high | in-scope | rubric | a.py:1 | unescalated | low | open | pending |\n"
        )
        # Declared - Id: catches unescalated high finding.
        err = review_sequence.check_S5(
            _SNAPSHOT_PLAN, _SNAPSHOT_PLAN, review_with_high, ""
        )
        assert err is not None
        assert "check.review-finding-unescalated" in err

        # Escalating F-01 clears check_S5.
        escalated = _SNAPSHOT_PLAN.replace(
            "## Validation and cross-check",
            "### OQ-02: Escalated F-01\n\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Finding: F-01\n"
            "- Resolution or deferral rationale: pending.\n\n"
            "## Validation and cross-check",
        )
        assert (
            review_sequence.check_S5(_SNAPSHOT_PLAN, escalated, review_with_high, "")
            is None
        )

        # Id-less snippet (no - Id:, no plan_path) does not synthesize a derived id6.
        idless_plan = _SNAPSHOT_PLAN.replace("- Id: sq1001\n", "")
        assert (
            review_sequence.check_S5(idless_plan, idless_plan, review_with_high, "")
            is None
        )

        # Missing Status in open question still fails on an id-less snippet.
        bad_oq = idless_plan.replace("- Status: resolved\n", "")
        err_bad_oq = review_sequence.check_S5(idless_plan, bad_oq, "", "")
        assert err_bad_oq is not None
        assert "Blocking:" in err_bad_oq and "Status:" in err_bad_oq

    def test_sequence_verdict_outputs_and_restore_pre_s7_plan(self) -> None:
        assert review_sequence.verdict_outputs("") == (None, None, "")
        assert review_sequence.verdict_outputs(_SNAPSHOT_PLAN) == (
            None,
            "to-review",
            "",
        )

        reviewed_plan = _SNAPSHOT_PLAN.replace(
            "- Status: to-review",
            "- Status: reviewed\n- Readiness: GO",
        ).replace(
            "## Workflow history\n",
            "## Workflow history\n\n- 2026-11-09 reviewed (tester): /plan-review (tester): APPROVE; ok\n",
        )
        rd, st, newest = review_sequence.verdict_outputs(reviewed_plan)
        assert rd == "go"
        assert st == "reviewed"
        assert "APPROVE" in newest

        bad_readiness = _SNAPSHOT_PLAN.replace(
            "- Status: to-review",
            "- Status: reviewed\n- Readiness: invalid-val",
        )
        rd_bad, st_bad, _ = review_sequence.verdict_outputs(bad_readiness)
        assert rd_bad is None
        assert st_bad == "reviewed"

        # restore_pre_s7_plan reverts Status, removes added Readiness, and strips added review history.
        mutated = reviewed_plan.replace(
            "Pin observable behavior of the snapshot metadata readers.",
            "Pin observable behavior (body edit kept).",
        )
        restored = review_sequence.restore_pre_s7_plan(_SNAPSHOT_PLAN, mutated)
        rd_res, st_res, newest_res = review_sequence.verdict_outputs(restored)
        assert rd_res is None
        assert st_res == "to-review"
        assert newest_res == ""
        assert "body edit kept" in restored

    def test_sequence_check_s7_readiness_status_and_exhausted_repair(self) -> None:
        # Condition (a): valid readiness + reviewed + 1 verdict history entry passes.
        good_a = _SNAPSHOT_PLAN.replace(
            "- Status: to-review",
            "- Status: reviewed\n- Readiness: go-pending-approval",
        ).replace(
            "## Workflow history\n",
            "## Workflow history\n\n- 2026-11-09 reviewed (tester): /plan-review (tester): APPROVE\n",
        )
        assert (
            review_sequence.check_S7(_SNAPSHOT_PLAN, good_a, "## Round 1\n", "") is None
        )

        # Condition (b): no readiness + to-review + exhausted repair in review + 1 verdict entry passes.
        good_b = _SNAPSHOT_PLAN.replace(
            "## Workflow history\n",
            "## Workflow history\n\n- 2026-11-09 reviewed (tester): /plan-review (tester): REJECT - NEEDS REPLAN\n",
        )
        assert (
            review_sequence.check_S7(
                _SNAPSHOT_PLAN,
                good_b,
                "## Round 1\nExhausted orchestrator repair.\n",
                "",
            )
            is None
        )

        # Invalid readiness value fails closed.
        bad_rd = good_a.replace(
            "- Readiness: go-pending-approval", "- Readiness: maybe"
        )
        err_bad_rd = review_sequence.check_S7(
            _SNAPSHOT_PLAN, bad_rd, "## Round 1\n", ""
        )
        assert err_bad_rd is not None
        assert "One of: (a)" in err_bad_rd


class TestReviewTierReaders:
    """Pins review_tier.tier_facts metadata reads and TODO exclusion."""

    def test_tier_facts_reads_kind_set_scope_paths_and_todo_exclusion(self) -> None:
        facts = review_tier.tier_facts(_SNAPSHOT_PLAN)
        assert facts["kind"] == "child"
        assert facts["in_set"] is True
        assert facts["scope_paths"] == ["agent_workflows/demo.py", "docs/demo.spec.md"]
        assert facts["names_spec"] is True
        assert facts["e_items"] == 1
        assert facts["task_groups"] == 1
        assert facts["exceeds_size"] is False

        # Orchestrator without Set and with TODO-prefixed Scope-Paths.
        for todo_val in ("TODO", "TODO fill in", "TODO(later)", "TODO: pending"):
            todo_plan = (
                _SNAPSHOT_PLAN.replace("- Kind: child", "- Kind: orchestrator")
                .replace("- Set: demo (demo set description)\n", "")
                .replace(
                    "- Scope-Paths: agent_workflows/demo.py, docs/demo.spec.md",
                    f"- Scope-Paths: {todo_val}",
                )
            )
            f_todo = review_tier.tier_facts(todo_plan)
            assert f_todo["kind"] == "orchestrator"
            assert f_todo["in_set"] is False
            assert f_todo["scope_paths"] is None
            assert f_todo["names_spec"] is False

        # Empty and headerless plans return safe defaults without raising.
        f_empty = review_tier.tier_facts("")
        assert f_empty == {
            "kind": None,
            "scope_paths": None,
            "names_spec": False,
            "e_items": 0,
            "task_groups": 0,
            "exceeds_size": False,
            "in_set": False,
        }
        f_headerless = review_tier.tier_facts("# IPD: Headerless\n\n## Goal\nText.\n")
        assert f_headerless["kind"] is None
        assert f_headerless["in_set"] is False
        assert f_headerless["scope_paths"] is None


class TestReviewRereviewReaders:
    """Pins review_rereview.rereview_triggers and check_limit_s7 metadata reads."""

    def test_rereview_triggers_scope_paths_item_deps_and_empty_inputs(self) -> None:
        assert (
            review_rereview.rereview_triggers(
                _SNAPSHOT_PLAN, _SNAPSHOT_PLAN, after_r_text=None
            )
            == []
        )
        assert review_rereview.rereview_triggers("", "", after_r_text=None) == []

        sp_changed = _SNAPSHOT_PLAN.replace(
            "- Scope-Paths: agent_workflows/demo.py, docs/demo.spec.md",
            "- Scope-Paths: agent_workflows/demo.py",
        )
        sp_reasons = review_rereview.rereview_triggers(
            _SNAPSHOT_PLAN, sp_changed, after_r_text=None
        )
        assert len(sp_reasons) == 1
        assert "Scope-Paths changed" in sp_reasons[0]

        dep_changed = _SNAPSHOT_PLAN.replace(
            "- Item-Dependencies: executed:ffceq0",
            "- Item-Dependencies: executed:ffceq0, executed:tve77h",
        )
        dep_reasons = review_rereview.rereview_triggers(
            _SNAPSHOT_PLAN, dep_changed, after_r_text=None
        )
        assert len(dep_reasons) == 1
        assert "Item-Dependencies changed" in dep_reasons[0]

        both_changed = dep_changed.replace(
            "- Scope-Paths: agent_workflows/demo.py, docs/demo.spec.md",
            "- Scope-Paths: none",
        )
        both_reasons = review_rereview.rereview_triggers(
            _SNAPSHOT_PLAN, both_changed, after_r_text=None
        )
        assert len(both_reasons) == 2

    def test_rereview_check_limit_s7_readiness_case_and_blocking_oq(self) -> None:
        # Lowercase and uppercase NO-GO with a new Blocking: yes open question pass.
        for rd_val in ("no-go", "NO-GO"):
            after_ok = _SNAPSHOT_PLAN.replace(
                "- Status: to-review", f"- Status: to-review\n- Readiness: {rd_val}"
            ).replace(
                "## Validation and cross-check",
                "### OQ-02: Limit reached\n\n"
                "- Blocking: yes\n"
                "- Status: open\n"
                "- Resolution or deferral rationale: active changes.\n\n"
                "## Validation and cross-check",
            )
            assert review_rereview.check_limit_s7(_SNAPSHOT_PLAN, after_ok) is None

        # Wrong or absent Readiness fails.
        after_go = _SNAPSHOT_PLAN.replace(
            "- Status: to-review", "- Status: to-review\n- Readiness: go"
        ).replace(
            "## Validation and cross-check",
            "### OQ-02: Limit reached\n\n- Blocking: yes\n- Status: open\n\n"
            "## Validation and cross-check",
        )
        err_go = review_rereview.check_limit_s7(_SNAPSHOT_PLAN, after_go)
        assert err_go is not None
        assert "- Readiness: no-go" in err_go

        err_absent = review_rereview.check_limit_s7(_SNAPSHOT_PLAN, _SNAPSHOT_PLAN)
        assert err_absent is not None
        assert "- Readiness: no-go" in err_absent

        # Readiness no-go without a new blocking open question fails.
        after_no_oq = _SNAPSHOT_PLAN.replace(
            "- Status: to-review", "- Status: to-review\n- Readiness: no-go"
        )
        err_no_oq = review_rereview.check_limit_s7(_SNAPSHOT_PLAN, after_no_oq)
        assert err_no_oq is not None
        assert "Blocking: yes" in err_no_oq


def _make_orch_body(setid: str, child_rows: list[tuple[str, str, str]]) -> str:
    table_rows = "\n".join(
        f"| {ord_tok} | {cid} | pending | {cpath} | none |"
        for ord_tok, cid, cpath in child_rows
    )
    first_cid = child_rows[0][1] if child_rows else "chd001"
    return (
        "## Goal\n\n"
        f"Orchestrate set {setid}.\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        f"- [ ] E-01 CONFIRM {first_cid} REACHED executed\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n\n"
        "## Child IPDs, sequence, and dependencies\n\n"
        "| Order | Id | Status | Plan | Depends on |\n"
        "|---|---|---|---|---|\n"
        f"{table_rows}\n\n"
        "## Completion criteria (the whole Set is done only when)\n\n- None.\n\n"
        "## Cross-IPD validation\n\n- None.\n\n"
        "## Deferred / out of scope (with reason)\n\n- None.\n\n"
        "## Scope check\n\n- None.\n\n"
        "## Required tests / validation\n\n- None.\n\n"
        "## Open questions\n\n- None.\n\n"
        "## Validation and cross-check (verify before reporting the Set complete)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: check.\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n\n"
        "## Approval and execution gate\n\n- None.\n"
    )


class TestOrchestratorReadinessReaders:
    """Pins orchestrator_readiness.resolve_all_set_memberships, review_readiness, and run_coverage."""

    def test_orchestrator_resolve_all_set_memberships_and_skips_idless(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".git").mkdir()
        builder = RecordBuilder(tmp_path)
        orch_a = Path(
            builder.plan(
                id6="or1001",
                plan_role="orchestrator",
                status="to-review",
                when="2026-11-09",
                set="alpha",
                order=0,
                slug="alpha-orch",
                body=_make_orch_body(
                    "alpha",
                    [
                        (
                            "01",
                            "ch1001",
                            ".aw/records/plans/pending/20261109-alpha-01-ch1001-first.ipd.md",
                        )
                    ],
                ),
            )
        )
        ch1 = Path(
            builder.plan(
                id6="ch1001",
                plan_role="child",
                status="to-review",
                when="2026-11-09",
                set="alpha",
                order=1,
                slug="first",
                body=_CONFORMING_CHILD_BODY,
            )
        )
        ch2 = Path(
            builder.plan(
                id6="ch1002",
                plan_role="child",
                status="executed",
                disposition="executed",
                when="2026-11-09",
                set="alpha",
                order=2,
                slug="second",
                body=_CONFORMING_CHILD_BODY,
            )
        )

        # Id-less legacy plan (no - Id: bullet, timestamp filename) must be skipped (D-3).
        idless = (
            tmp_path
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260101-1200-03-legacy-no-id.ipd.md"
        )
        idless.write_text(
            "# IPD: Legacy without id\n\n"
            "- Date: 2026-01-01\n"
            "- Kind: child\n"
            "- Set: alpha\n"
            "- Order: 3\n"
            "- Status: draft\n",
            encoding="utf-8",
        )

        # Also enable a legacy .agents/plans tree alongside .aw/records/plans.
        retention_manifest = (
            tmp_path
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        retention_manifest.parent.mkdir(parents=True)
        retention_manifest.write_text("{}\n", encoding="utf-8")
        legacy_dir = tmp_path / ".agents" / "plans" / "pending"
        legacy_dir.mkdir(parents=True)
        legacy_orch = legacy_dir / "20261109-beta-00-or2001-beta-orch.ipd.md"
        legacy_orch.write_text(
            RecordBuilder().plan(
                title="Beta orchestrator",
                when="2026-11-09",
                plan_role="orchestrator",
                set="beta (legacy set)",
                order=0,
                status="to-review",
                id6="or2001",
                text_only=True,
            ),
            encoding="utf-8",
        )
        legacy_child = legacy_dir / "20261109-beta-01-ch2001-beta-child.ipd.md"
        legacy_child.write_text(
            RecordBuilder().plan(
                title="Beta child",
                when="2026-11-09",
                plan_role="child",
                set="beta",
                order=1,
                status="approved",
                id6="ch2001",
                text_only=True,
            ),
            encoding="utf-8",
        )

        memberships = orchestrator_readiness.resolve_all_set_memberships(tmp_path)
        assert "alpha" in memberships
        alpha = memberships["alpha"]
        assert alpha.orchestrator is not None
        assert alpha.orchestrator.id6 == "or1001"
        assert alpha.orchestrator.path.resolve() == orch_a.resolve()
        assert [c.id6 for c in alpha.children] == ["ch1001", "ch1002"]
        assert [c.status for c in alpha.children] == ["to-review", "executed"]
        assert [c.path.resolve() for c in alpha.children] == [
            ch1.resolve(),
            ch2.resolve(),
        ]

        assert "beta" in memberships
        beta = memberships["beta"]
        assert beta.orchestrator is not None
        assert beta.orchestrator.id6 == "or2001"
        assert beta.orchestrator.path.resolve() == legacy_orch.resolve()
        assert [c.id6 for c in beta.children] == ["ch2001"]
        assert beta.children[0].status == "approved"
        assert beta.children[0].path.resolve() == legacy_child.resolve()

    def test_orchestrator_review_readiness_tracked_and_untracked_plans(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        (repo / ".git").mkdir(parents=True)
        builder = RecordBuilder(repo)
        child_rel = ".aw/records/plans/pending/20261109-gamma-01-ch3001-work.ipd.md"
        orch_p = Path(
            builder.plan(
                id6="or3001",
                plan_role="orchestrator",
                status="to-review",
                when="2026-11-09",
                set="gamma",
                order=0,
                slug="gamma-orch",
                priority="medium",
                work_kind="chore",
                author="tester",
                highest_e_allocated="01",
                scope_paths="none",
                item_dependencies="none",
                body=_make_orch_body("gamma", [("01", "ch3001", child_rel)]),
                raw_fields={"Concern": "gamma concern.", "Scope": "gamma scope."},
            )
        )
        child_p = Path(
            builder.plan(
                id6="ch3001",
                plan_role="child",
                status="to-review",
                when="2026-11-09",
                set="gamma",
                order=1,
                slug="work",
                priority="medium",
                work_kind="chore",
                author="tester",
                body=_CONFORMING_CHILD_BODY,
                raw_fields={
                    "Concern": "sample.",
                    "Scope": "sample.",
                    "Item-Dependencies": None,
                    "Scope-Paths": None,
                    "Highest E allocated": "01",
                },
            )
        )
        coverage_record.write(orch_p, "pass", model="fixture", tool="test")

        # Non-orchestrator child returns applies=False, ready=True with metadata populated.
        child_res = orchestrator_readiness.review_readiness(repo, child_p, ask=False)
        assert child_res.applies is False
        assert child_res.ready is True
        assert child_res.id6 == "ch3001"
        assert child_res.setid == "gamma"

        # Tracked ready orchestrator passes (both uncached and with warmed SQLite cache).
        orch_res = orchestrator_readiness.review_readiness(repo, orch_p, ask=False)
        assert orch_res.applies is True
        assert orch_res.ready is True, [f.detail for f in orch_res.findings]
        assert orch_res.id6 == "or3001"
        assert orch_res.setid == "gamma"

        from agent_workflows import artifact_meta as _am

        ctx = _am.legacy_context(repo)
        _am.query(type="ipd", project_context=ctx)
        assert (Path(ctx.logical_roots["state"]) / "index.db").exists()
        orch_cached = orchestrator_readiness.review_readiness(repo, orch_p, ask=False)
        assert orch_cached.applies is True
        assert orch_cached.ready is True
        assert orch_cached.id6 == "or3001"
        assert orch_cached.setid == "gamma"

        # Untracked plan file outside the repo/cache roots uses the read_text fallback (D-3).
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        ext_child = external_dir / "untracked-child.ipd.md"
        ext_child.write_text(child_p.read_text(encoding="utf-8"), encoding="utf-8")
        ext_child_res = orchestrator_readiness.review_readiness(
            repo, ext_child, ask=False
        )
        assert ext_child_res.applies is False
        assert ext_child_res.ready is True
        assert ext_child_res.id6 == "ch3001"
        assert ext_child_res.setid == "gamma"

        ext_orch = external_dir / "untracked-orch.ipd.md"
        ext_orch.write_text(orch_p.read_text(encoding="utf-8"), encoding="utf-8")
        ext_orch_res = orchestrator_readiness.review_readiness(
            repo, ext_orch, ask=False
        )
        assert ext_orch_res.applies is True
        assert ext_orch_res.ready is True, [f.detail for f in ext_orch_res.findings]
        assert ext_orch_res.id6 == "or3001"
        assert ext_orch_res.setid == "gamma"

    def test_orchestrator_run_coverage_filters_orchestrators_and_reports_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)
        builder = RecordBuilder(tmp_path)
        child_rel = ".aw/records/plans/pending/20261109-delta-01-ch4001-work.ipd.md"
        orch_p = Path(
            builder.plan(
                id6="or4001",
                plan_role="orchestrator",
                status="to-review",
                when="2026-11-09",
                set="delta",
                order=0,
                slug="delta-orch",
                priority="medium",
                work_kind="chore",
                author="tester",
                highest_e_allocated="01",
                scope_paths="none",
                item_dependencies="none",
                body=_make_orch_body("delta", [("01", "ch4001", child_rel)]),
                raw_fields={"Concern": "delta concern.", "Scope": "delta scope."},
            )
        )
        child_p = Path(
            builder.plan(
                id6="ch4001",
                plan_role="child",
                status="to-review",
                when="2026-11-09",
                set="delta",
                order=1,
                slug="work",
                priority="medium",
                work_kind="chore",
                author="tester",
                body=_CONFORMING_CHILD_BODY,
                raw_fields={
                    "Concern": "sample.",
                    "Scope": "sample.",
                    "Item-Dependencies": None,
                    "Scope-Paths": None,
                    "Highest E allocated": "01",
                },
            )
        )
        coverage_record.write(orch_p, "pass", model="fixture", tool="test")

        buf = io.StringIO()
        args = SimpleNamespace(
            targets=[str(orch_p), str(child_p)],
            host=None,
            model=None,
            no_commit=True,
            agent=False,
            json=True,
            fields=None,
            no_color=True,
        )
        with redirect_stdout(buf):
            rc = orchestrator_readiness.run_coverage(args)
        assert rc == 0
        payload = json.loads(buf.getvalue())
        assert payload["outcome"] == "clean"
        assert payload["data"]["id6"] == "or4001"
        assert payload["data"]["ready"] is True
        assert str(child_p) in payload["data"]["not_applicable"]

        # Selecting only a non-orchestrator returns exit 2 (cannot-run).
        buf_non = io.StringIO()
        args_non = SimpleNamespace(
            targets=[str(child_p)],
            host=None,
            model=None,
            no_commit=True,
            agent=False,
            json=True,
            fields=None,
            no_color=True,
        )
        with redirect_stdout(buf_non):
            rc_non = orchestrator_readiness.run_coverage(args_non)
        assert rc_non == 2
        payload_non = json.loads(buf_non.getvalue())
        assert payload_non["outcome"] == "cannot-run"

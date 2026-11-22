"""Behavioral pinning tests for review_findings, artifact_audit, and reviews readers (IPD y4spqy).

Pins the observable behavior of:
- ``agent_workflows.review_findings``: ``parse_review_text``, ``parse_review_file``,
  ``subject_review_records``, ``subject_gating_blocks``, ``review_attestation_missing``.
- ``agent_workflows.artifact_audit``: ``read_declared_status`` (including D-1 plan vs non-plan
  handling), ``audit_artifact``, ``audit_tracked_artifact``.
- ``agent_workflows.reviews``: ``_resolve_selector_paths``, ``collect_decisions``,
  ``run_decisions``.

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

from agent_workflows import artifact_audit, reviews
from agent_workflows import review_findings as rf
from tests.record_builder import RecordBuilder

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

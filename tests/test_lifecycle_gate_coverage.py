"""Outcome tests for lifecycle gate coverage reporting across history date collapse (IPD 5xq2ng).

Pins the reported-not-silent property: when unified UTC history dates collapse date variation,
a plan with two or more distinct forward statuses whose transitions cannot be ordered yields
an advisory `check.lifecycle-transition-unvalidated` (info) finding rather than silently
validating nothing.

Assertions drive the checker and evaluate findings; no source inspection or regex is used.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from tests.record_builder import RecordBuilder


def _fixture_plan_text(id6: str, history_text: str, status: str = "approved") -> str:
    history_lines = [line for line in history_text.splitlines() if line.strip()]
    return str(
        RecordBuilder().plan(
            title=f"Fixture {id6}",
            when="2026-09-01",
            plan_role="child",
            scope_paths="agent_workflows/check_engine.py",
            item_dependencies="none",
            status=status,
            set="demo",
            order=1,
            priority="medium",
            work_kind="chore",
            author="fixture",
            id6=id6,
            approval=(
                "2026-09-03, recorded via aw ipd set" if status == "approved" else None
            ),
            history=history_lines,
            text_only=True,
        )
    )


class LifecycleGateCoverageTests(unittest.TestCase):
    """Pin the reported-not-silent property across history date collapse."""

    RULE_ID = "check.lifecycle-transition-unvalidated"

    def _setup_fixture_repo(
        self, tmpdir: str, filename: str, content: str, bucket: str = "pending"
    ) -> Path:
        tmproot = Path(tmpdir)
        target_dir = tmproot / ".aw" / "records" / "plans" / bucket
        target_dir.mkdir(parents=True, exist_ok=True)
        plan_file = target_dir / filename
        plan_file.write_text(content, encoding="utf-8")
        return tmproot

    def test_two_date_legal_lifecycle_has_no_coverage_finding(self):
        """A two-date legal lifecycle validates transitions; coverage check emits 0 findings."""
        history = (
            "- 2026-09-02 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-02 to-review (agent): ok\n"
            "- 2026-09-01 draft (agent): ok"
        )
        content = _fixture_plan_text("twod01", history, status="approved")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir, "20260901-twod01-01-twod01-two-date.ipd.md", content
            )
            # Sibling coverage checker emits no findings because transitions are validated.
            coverage_drifts = ce.check_lifecycle_transition_coverage(
                tmproot, include_untracked=True
            )
            self.assertEqual(coverage_drifts, [])

            # Existing transition checker also emits no violation findings.
            invalid_drifts = ce.check_lifecycle_transitions(
                tmproot, include_untracked=True
            )
            self.assertEqual(invalid_drifts, [])

    def test_one_date_collapsed_lifecycle_reports_coverage_finding(self):
        """The same lifecycle on one date validates 0 transitions; companion emits one info finding."""
        history = (
            "- 2026-09-02 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-02 to-review (agent): ok\n"
            "- 2026-09-02 draft (agent): ok"
        )
        content = _fixture_plan_text("oned01", history, status="approved")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir, "20260902-oned01-01-oned01-one-date.ipd.md", content
            )
            # Sibling coverage checker reports the coverage loss with exactly one finding.
            coverage_drifts = ce.check_lifecycle_transition_coverage(
                tmproot, include_untracked=True
            )
            self.assertEqual(len(coverage_drifts), 1)
            d = coverage_drifts[0]
            self.assertEqual(d.rule, self.RULE_ID)
            self.assertEqual(d.severity, "info")

            # Detail must name distinct statuses and unorderable group dates.
            for st in ("draft", "to-review", "reviewed", "approved"):
                self.assertIn(st, d.detail)
            self.assertIn("2026-09-02", d.detail)

            # Non-regression of existing rule: check_lifecycle_transitions still returns []
            # (the new finding is NOT appended to check_lifecycle_transitions).
            invalid_drifts = ce.check_lifecycle_transitions(
                tmproot, include_untracked=True
            )
            self.assertEqual(invalid_drifts, [])

    def test_single_status_negative_produces_no_coverage_finding(self):
        """A plan with only one distinct status in history emits no coverage finding (noise guard)."""
        history = "- 2026-09-01 draft (agent): created"
        content = _fixture_plan_text("sngl01", history, status="draft")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir, "20260901-sngl01-01-sngl01-single-status.ipd.md", content
            )
            coverage_drifts = ce.check_lifecycle_transition_coverage(
                tmproot, include_untracked=True
            )
            self.assertEqual(coverage_drifts, [])

    def test_terminal_plan_scoping_produces_no_coverage_finding(self):
        """A terminal plan with collapsed history produces no coverage finding (grandfathered)."""
        history = "- 2026-09-02 approved (agent): ok\n" "- 2026-09-02 draft (agent): ok"
        content = _fixture_plan_text("term01", history, status="approved")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir,
                "20260902-term01-01-term01-executed.ipd.md",
                content,
                bucket="executed",
            )
            coverage_drifts = ce.check_lifecycle_transition_coverage(
                tmproot, include_untracked=True
            )
            self.assertEqual(coverage_drifts, [])

    def test_two_limb_exit_code_proof(self):
        """Canonical two-limb severity and exit code proof: info exits 0; swapped to error exits 1."""
        # Limb 1: Registry severity is info
        spec = ce.rule_spec(self.RULE_ID)
        self.assertEqual(spec.severity, "info")

        # Limb 2: drift_exit_code over enriched findings is 0, and 1 when severity is error
        history = "- 2026-09-02 approved (agent): ok\n" "- 2026-09-02 draft (agent): ok"
        content = _fixture_plan_text("exit01", history, status="approved")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir, "20260902-exit01-01-exit01-plan.ipd.md", content
            )
            coverage_drifts = ce.check_lifecycle_transition_coverage(
                tmproot, include_untracked=True
            )
            self.assertEqual(len(coverage_drifts), 1)

            # Exit code over info findings is 0
            self.assertEqual(core.drift_exit_code(coverage_drifts), 0)

            # Swapping severity to error changes exit code to 1
            as_error = [d._replace(severity="error") for d in coverage_drifts]
            self.assertEqual(core.drift_exit_code(as_error), 1)

    def test_check_type_plans_integration(self):
        """check_type(repo, 'plans') composes the coverage rule in its check_content pass."""
        history = "- 2026-09-02 approved (agent): ok\n" "- 2026-09-02 draft (agent): ok"
        content = _fixture_plan_text("integ1", history, status="approved")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = self._setup_fixture_repo(
                tmpdir, "20260902-integ1-01-integ1-plan.ipd.md", content
            )
            all_drifts = ce.check_type(tmproot, "plans", include_untracked=True)
            coverage_matches = [d for d in all_drifts if d.rule == self.RULE_ID]
            self.assertEqual(len(coverage_matches), 1)
            self.assertEqual(coverage_matches[0].severity, "info")


if __name__ == "__main__":
    unittest.main()

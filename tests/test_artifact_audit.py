"""Focused unit tests for agent_workflows.artifact_audit engine (mlhryi E-02, E-03)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit


class TestAllowedLifecyclePairs(unittest.TestCase):
    """Test paired status and directory expectations across artifact types and actions (V-02)."""

    def test_backlog_plan_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("backlog", "plan", "executed")
        self.assertEqual(pairs, [("graduated", "graduated"), ("done", "done")])

    def test_backlog_execute_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("backlog", "execute", "executed")
        self.assertEqual(pairs, [("done", "done")])

    def test_spec_plan_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("specs", "plan", "executed")
        self.assertEqual(
            pairs, [("implementing", "implementing"), ("implemented", "implemented")]
        )

    def test_spec_review_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("specs", "review", "executed")
        self.assertEqual(pairs, [("reviewed", "reviewed"), ("approved", "approved")])

    def test_ipd_execute_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("plans", "execute", "executed")
        self.assertEqual(
            pairs,
            [
                ("executed", "executed"),
                ("complete", "executed"),
                ("superseded", "superseded"),
                ("not-executed", "not-executed"),
                ("reusable", "reusable"),
            ],
        )

    def test_ipd_review_success_pairs(self) -> None:
        pairs = _audit.allowed_lifecycle_pairs("plans", "review", "executed")
        self.assertEqual(pairs, [("reviewed", "pending"), ("approved", "pending")])

    def test_unstarted_typed_steps_with_initial_status(self) -> None:
        # Backlog queued with initial status open
        bk_pairs = _audit.allowed_lifecycle_pairs(
            "backlog", "plan", "queued", initial_status="open"
        )
        self.assertEqual(bk_pairs, [("open", "open")])

        # Spec queued with initial status approved (for plan)
        sp_plan_pairs = _audit.allowed_lifecycle_pairs(
            "specs", "plan", "queued", initial_status="approved"
        )
        self.assertEqual(sp_plan_pairs, [("approved", "approved")])

        # Spec queued with initial status to-review (for review)
        sp_rev_pairs = _audit.allowed_lifecycle_pairs(
            "specs", "review", "queued", initial_status="to-review"
        )
        self.assertEqual(sp_rev_pairs, [("to-review", "to-review")])

    def test_typed_steps_fallback_when_initial_status_absent(self) -> None:
        bk_pairs = _audit.allowed_lifecycle_pairs(
            "backlog", "plan", "queued", initial_status=None, is_explicit_type=True
        )
        self.assertEqual(bk_pairs, [("open", "open")])

        sp_pairs = _audit.allowed_lifecycle_pairs(
            "specs", "plan", "queued", initial_status=None, is_explicit_type=True
        )
        self.assertEqual(sp_pairs, [("approved", "approved")])


class TestArtifactAuditEngine(unittest.TestCase):
    """Engine tests for audit_artifact, paired placement, type conflicts, and monthly shards (V-02, V-03)."""

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _write_file(self, rel_path: str, content: str) -> Path:
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_backlog_plan_success_unchanged(self) -> None:
        self._write_file(
            ".aw/records/backlog/graduated/20260928-testset-01-bk0001-sample.backlog.md",
            "- Id: bk0001\n- Status: graduated\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0001",
            "20260928-testset-01-bk0001-sample",
            status="executed",
            artifact_type="backlog",
            action="plan",
        )
        self.assertFalse(audit.missing_entirely)
        self.assertFalse(audit.location_mismatch)
        self.assertFalse(audit.status_mismatch)
        self.assertFalse(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_backlog_done_success_unchanged(self) -> None:
        self._write_file(
            ".aw/records/backlog/done/20260928-testset-01-bk0002-sample.backlog.md",
            "- Id: bk0002\n- Status: done\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0002",
            "20260928-testset-01-bk0002-sample",
            status="executed",
            artifact_type="backlog",
            action="plan",
        )
        self.assertFalse(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_spec_plan_success_unchanged(self) -> None:
        self._write_file(
            ".aw/records/specs/implementing/20260928-testset-01-sp0001-sample.spec.md",
            "- Id: sp0001\n- Status: implementing\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "sp0001",
            "20260928-testset-01-sp0001-sample",
            status="executed",
            artifact_type="specs",
            action="plan",
        )
        self.assertFalse(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_matching_unstarted_typed_steps(self) -> None:
        self._write_file(
            ".aw/records/backlog/open/20260928-testset-01-bk0003-sample.backlog.md",
            "- Id: bk0003\n- Status: open\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0003",
            "20260928-testset-01-bk0003-sample",
            status="queued",
            artifact_type="backlog",
            action="plan",
            initial_status="open",
        )
        self.assertFalse(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_backlog_cross_pair_rejected(self) -> None:
        # A file in graduated/ declaring done is cross-paired and rejected
        self._write_file(
            ".aw/records/backlog/graduated/20260928-testset-01-bk0004-sample.backlog.md",
            "- Id: bk0004\n- Status: done\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0004",
            "20260928-testset-01-bk0004-sample",
            status="executed",
            artifact_type="backlog",
            action="plan",
        )
        self.assertTrue(audit.location_mismatch)
        self.assertTrue(audit.status_mismatch)
        self.assertTrue(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_REGRESSED)

    def test_type_conflict_detected_and_reported_as_unknown(self) -> None:
        # Queue declares artifact_type="ipd", but disk file is a backlog file
        self._write_file(
            ".aw/records/backlog/open/20260928-testset-01-bk0005-sample.backlog.md",
            "- Id: bk0005\n- Status: open\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0005",
            "20260928-testset-01-bk0005-sample",
            status="executed",
            artifact_type="ipd",
            action="execute",
        )
        self.assertTrue(audit.type_conflict)
        self.assertTrue(audit.location_mismatch)
        self.assertTrue(audit.status_mismatch)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNKNOWN)
        self.assertEqual(audit.class_reason, _audit.UNKNOWN_TYPE_CONFLICT)

    def test_ipd_monthly_shard_not_location_mismatch(self) -> None:
        # IPD plan archived under monthly shard executed/202608/
        self._write_file(
            ".aw/records/plans/executed/202608/20260820-testset-01-pl0001-sample.ipd.md",
            "# IPD: sample\n\n- Id: pl0001\n- Status: executed\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "pl0001",
            "20260820-testset-01-pl0001-sample",
            status="executed",
            artifact_type="ipd",
            action="execute",
        )
        self.assertFalse(audit.missing_entirely)
        self.assertFalse(audit.location_mismatch)
        self.assertFalse(audit.status_mismatch)
        self.assertFalse(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_backlog_executed_without_transition_is_regressed(self) -> None:
        # Backlog item was dispatched under plan, executed, but is still in open/ reading open
        self._write_file(
            ".aw/records/backlog/open/20260928-testset-01-bk0006-sample.backlog.md",
            "- Id: bk0006\n- Status: open\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0006",
            "20260928-testset-01-bk0006-sample",
            status="executed",
            artifact_type="backlog",
            action="plan",
        )
        self.assertTrue(audit.location_mismatch)
        self.assertTrue(audit.status_mismatch)
        self.assertTrue(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_REGRESSED)
        self.assertIn(
            "the run recorded executed (plan) but the artifact is in open/",
            audit.class_reason,
        )

    def test_spec_executed_without_transition_is_regressed(self) -> None:
        # Spec dispatched under plan, executed, but is still in approved/ reading approved
        self._write_file(
            ".aw/records/specs/approved/20260928-testset-01-sp0002-sample.spec.md",
            "- Id: sp0002\n- Status: approved\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "sp0002",
            "20260928-testset-01-sp0002-sample",
            status="executed",
            artifact_type="specs",
            action="plan",
        )
        self.assertTrue(audit.location_mismatch)
        self.assertTrue(audit.status_mismatch)
        self.assertTrue(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_REGRESSED)

    def test_backlog_later_progress_evidenced_is_resolved(self) -> None:
        # Backlog item was queued in run, but later graduated with transition commit
        self._write_file(
            ".aw/records/backlog/graduated/20260928-testset-01-bk0007-sample.backlog.md",
            "- Id: bk0007\n- Status: graduated\n",
        )
        fake_idx = _audit.FinalizeEvidenceIndex(
            available=True,
            head_reachable={"head123", "commit456", "base000"},
            parents={"head123": ["commit456"], "commit456": ["base000"]},
            transition_commits={"bk0007": [("commit456", "graduated")]},
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0007",
            "20260928-testset-01-bk0007-sample",
            status="queued",
            artifact_type="backlog",
            action="plan",
            initial_status="open",
            evidence=fake_idx,
            ending_head="base000",
        )
        self.assertTrue(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_RESOLVED)
        self.assertEqual(audit.evidence_commit, "commit456")
        self.assertIn("transitioned after the run ended", audit.class_reason)

    def test_backlog_later_progress_without_evidence_is_unknown(self) -> None:
        # Backlog item was queued, now graduated, but no evidence commit found
        self._write_file(
            ".aw/records/backlog/graduated/20260928-testset-01-bk0008-sample.backlog.md",
            "- Id: bk0008\n- Status: graduated\n",
        )
        fake_idx = _audit.FinalizeEvidenceIndex(
            available=True,
            head_reachable={"head123", "base000"},
            parents={"head123": ["base000"]},
            transition_commits={},
        )
        audit = _audit.audit_artifact(
            self.root,
            "bk0008",
            "20260928-testset-01-bk0008-sample",
            status="queued",
            artifact_type="backlog",
            action="plan",
            initial_status="open",
            evidence=fake_idx,
            ending_head="base000",
        )
        self.assertTrue(audit.has_discrepancy)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNKNOWN)
        self.assertIn(
            "no lifecycle transition commit in the after-the-run range",
            audit.class_reason,
        )

    def test_ipd_retired_with_banner_is_retired(self) -> None:
        self._write_file(
            ".aw/records/plans/superseded/20260928-testset-01-pl0002-sample.ipd.md",
            "# IPD: sample\n\n> **RETIRED**\n\n- Id: pl0002\n- Status: superseded\n",
        )
        audit = _audit.audit_artifact(
            self.root,
            "pl0002",
            "20260928-testset-01-pl0002-sample",
            status="retired",
            artifact_type="ipd",
            action="execute",
        )
        self.assertFalse(audit.missing_entirely)
        self.assertFalse(audit.location_mismatch)
        self.assertFalse(audit.status_mismatch)
        self.assertEqual(audit.difference_class, _audit.CLASS_UNCHANGED)

    def test_audit_tracked_artifact_preserves_doctor_behavior(self) -> None:
        # Tracked only doctor audit returns None for valid terminal plan
        valid_p = self._write_file(
            ".aw/records/plans/executed/20260928-testset-01-pl0003-sample.ipd.md",
            "- Id: pl0003\n- Status: executed\n",
        )
        self.assertIsNone(_audit.audit_tracked_artifact(self.root, valid_p))

        # Returns None for pending plan
        pending_p = self._write_file(
            ".aw/records/plans/pending/20260928-testset-01-pl0004-sample.ipd.md",
            "- Id: pl0004\n- Status: approved\n",
        )
        self.assertIsNone(_audit.audit_tracked_artifact(self.root, pending_p))

        # Returns finding for terminal plan in executed/ declaring superseded
        drift_p = self._write_file(
            ".aw/records/plans/executed/20260928-testset-01-pl0005-sample.ipd.md",
            "- Id: pl0005\n- Status: superseded\n",
        )
        finding = _audit.audit_tracked_artifact(self.root, drift_p)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertTrue(finding.location_mismatch)
        self.assertEqual(finding.difference_class, _audit.CLASS_UNKNOWN)
        self.assertEqual(finding.class_reason, _audit.UNKNOWN_TRACKED_ONLY)

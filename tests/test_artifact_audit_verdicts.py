"""Outcome tests for artifact_audit verdict behaviors (IPD auqoig).

Re-expresses the verdict shapes against allowed_lifecycle_pairs semantics, restores
the is_live passthrough and no-drift property, covers expected_dir_for_status across
the three previously unpinned terminal/standing dispositions and pre-terminal sweep,
and pins read_declared_status multi-word refusal parity.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit


class ArtifactAuditVerdictTests(unittest.TestCase):
    """Outcome-asserting tests for artifact_audit verdict behaviors."""

    def test_four_verdict_shapes(self) -> None:
        """The four verdict shapes of audit_artifact under allowed_lifecycle_pairs."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            ex = root / ".aw" / "records" / "plans" / "executed"
            pend.mkdir(parents=True)
            ex.mkdir(parents=True)

            # CLEAN: executed plan in executed/ under run status executed
            (ex / "20260908-v-01-vcl001-x.ipd.md").write_text(
                "- Id: vcl001\n- Status: executed\n",
                encoding="utf-8",
            )
            clean = artifact_audit.audit_artifact(root, "vcl001", status="executed")
            self.assertFalse(clean.location_mismatch)
            self.assertFalse(clean.status_mismatch)
            self.assertFalse(clean.has_discrepancy)
            self.assertEqual(clean.difference_class, artifact_audit.CLASS_UNCHANGED)

            # LOCATION-ONLY: executed plan in pending/ under run status executed
            (pend / "20260908-v-02-vlc002-x.ipd.md").write_text(
                "- Id: vlc002\n- Status: executed\n",
                encoding="utf-8",
            )
            loc = artifact_audit.audit_artifact(root, "vlc002", status="executed")
            self.assertTrue(loc.location_mismatch)
            self.assertFalse(loc.status_mismatch)
            self.assertTrue(loc.has_discrepancy)
            self.assertEqual(loc.difference_class, artifact_audit.CLASS_REGRESSED)

            # STATUS-ONLY: approved plan in executed/ under run status executed
            (ex / "20260908-v-03-vst003-x.ipd.md").write_text(
                "- Id: vst003\n- Status: approved\n",
                encoding="utf-8",
            )
            st = artifact_audit.audit_artifact(root, "vst003", status="executed")
            self.assertFalse(st.location_mismatch)
            self.assertTrue(st.status_mismatch)
            self.assertTrue(st.has_discrepancy)
            self.assertEqual(st.difference_class, artifact_audit.CLASS_UNKNOWN)

            # MISSING: an id6 written nowhere
            missing = artifact_audit.audit_artifact(root, "vms004", status="executed")
            self.assertTrue(missing.missing_entirely)
            self.assertTrue(missing.has_discrepancy)
            self.assertEqual(missing.difference_class, artifact_audit.CLASS_MISSING)

    def test_liveness_is_carried_through_and_never_derived(self) -> None:
        """`is_live` is an INPUT (from a run dir's PID/lock holder) that this module only records."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            pend.mkdir(parents=True)
            (pend / "20260908-lv-01-lvv001-x.ipd.md").write_text(
                "- Id: lvv001\n- Status: approved\n",
                encoding="utf-8",
            )
            live = artifact_audit.audit_artifact(
                root, "lvv001", status="running", is_live=True
            )
            not_live = artifact_audit.audit_artifact(
                root, "lvv001", status="running", is_live=False
            )
            self.assertIs(live.is_live, True)
            self.assertIs(not_live.is_live, False)
            # A running step's plan in pending/ is NOT drift either way.
            self.assertFalse(live.has_discrepancy)
            self.assertFalse(not_live.has_discrepancy)

    def test_expected_dir_for_status_uncovered_dispositions_and_preterminal_sweep(
        self,
    ) -> None:
        """The three uncovered terminal/standing dispositions, executed, and pre-terminal sweep."""
        self.assertEqual(artifact_audit.expected_dir_for_status("executed"), "executed")
        self.assertEqual(
            artifact_audit.expected_dir_for_status("superseded"), "superseded"
        )
        self.assertEqual(
            artifact_audit.expected_dir_for_status("not-executed"), "not-executed"
        )
        self.assertEqual(artifact_audit.expected_dir_for_status("reusable"), "reusable")
        for pre in ("draft", "to-review", "reviewed", "approved", "queued", "running"):
            self.assertEqual(artifact_audit.expected_dir_for_status(pre), "pending")

    def test_multi_word_status_is_unreadable_by_design(self) -> None:
        """Parity with `selectors._STATUS_RE`: a multi-word status yields None, not a partial read."""
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "x.md"
            f.write_text(
                "- Id: mww001\n- Status: EXECUTED (approved by maintainer)\n",
                encoding="utf-8",
            )
            self.assertIsNone(artifact_audit.read_declared_status(f))

            # Positive control: single-token status returns the declared value
            f_ok = Path(td) / "ok.md"
            f_ok.write_text("- Id: mww002\n- Status: executed\n", encoding="utf-8")
            self.assertEqual(artifact_audit.read_declared_status(f_ok), "executed")

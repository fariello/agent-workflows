"""agentadhere Phase 3 (IPD wqj1ne): event-derived lifecycle state + declared file scope.

Covers:
  E-01/V-01 - validate_transition rejects each invalid transition (missing predecessor, stale tree,
              invalid actor, malformed evidence, unauthorized terminal); a valid ordered event
              sequence derives the expected status; events come from the existing inline history
              (no parallel log); existing `- Status:` reads still work (backward-compat).
  E-02/V-02 - check.scope-drift flags an out-of-scope changed path for a plan with an active begin
              receipt, is clean for in-scope, reuses the finalize scope helpers (no fork), and
              honors the `grandfathered` sentinel.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as life


# --------------------------------------------------------------------------------------
# E-01 / V-01: transition validity + derivation + no-parallel-log + backward compat
# --------------------------------------------------------------------------------------


class TestTransitionValidity(unittest.TestCase):
    def test_missing_predecessor_start_mid_sequence(self):
        chk = life.validate_transition(None, "reviewed", actor="aw set")
        self.assertFalse(chk.ok)
        self.assertIn("missing predecessor", chk.reason)

    def test_missing_predecessor_backwards(self):
        chk = life.validate_transition("approved", "draft", actor="aw set")
        self.assertFalse(chk.ok)
        self.assertIn("missing predecessor", chk.reason)

    def test_missing_predecessor_terminal_from_draft(self):
        chk = life.validate_transition("draft", "executed", actor="aw ipd finalize")
        self.assertFalse(chk.ok)
        self.assertIn("missing predecessor", chk.reason)

    def test_stale_tree_id(self):
        chk = life.validate_transition(
            "reviewed",
            "approved",
            actor="aw set",
            tree_id_current="aaa",
            tree_id_evidence="bbb",
        )
        self.assertFalse(chk.ok)
        self.assertIn("stale tree id", chk.reason)

    def test_invalid_actor(self):
        chk = life.validate_transition("draft", "to-review", actor="   ")
        self.assertFalse(chk.ok)
        self.assertIn("invalid actor", chk.reason)

    def test_malformed_evidence(self):
        chk = life.validate_transition(
            "reviewed", "approved", actor="aw set", require_evidence=True, evidence={}
        )
        self.assertFalse(chk.ok)
        self.assertIn("malformed evidence", chk.reason)

    def test_unauthorized_terminal(self):
        chk = life.validate_transition("approved", "executed", actor="aw set")
        self.assertFalse(chk.ok)
        self.assertIn("unauthorized terminal", chk.reason)

    def test_valid_forward_transitions(self):
        self.assertTrue(
            life.validate_transition("draft", "reviewed", actor="aw set").ok
        )
        self.assertTrue(
            life.validate_transition("reviewed", "approved", actor="aw set").ok
        )
        self.assertTrue(
            life.validate_transition("approved", "executed", actor="aw ipd finalize").ok
        )
        self.assertTrue(
            life.validate_transition(
                "auto-approved", "executed", actor="aw ipd finalize"
            ).ok
        )


class TestDerivation(unittest.TestCase):
    def test_derive_status_from_valid_sequence(self):
        events = [
            ("2026-08-25", "draft", "author"),
            ("2026-08-26", "reviewed", "author"),
            ("2026-08-27", "approved", "aw set"),
        ]
        self.assertEqual(life.derive_status_from_events(events), "approved")

    def test_derive_ignores_off_sequence_notes(self):
        # an off-sequence disposition token does not advance the forward-derived status
        events = [
            ("2026-08-25", "draft", "a"),
            ("2026-08-26", "reviewed", "a"),
            ("2026-08-27", "parked", "a"),
        ]
        self.assertEqual(life.derive_status_from_events(events), "reviewed")

    def test_events_from_inline_history_no_parallel_log(self):
        # events are parsed from the plan's INLINE `## Workflow history` via record_history's parser
        # (no new event-log file). A workflow NOTE token (not a status) is skipped.
        import inspect

        src = inspect.getsource(life._plan_status_events)
        self.assertIn("record_history", src)
        self.assertIn("_inline_history_records", src)
        text = (
            "# IPD: x\n\n- Id: aaa111\n- Status: approved\n\n## Workflow history\n"
            "- 2026-08-27 approved (aw set): status set to approved\n"
            "- 2026-08-26 reviewed (author): /plan-review done\n"
            "- 2026-08-26 /plan-review (author): a note, not a status\n"
            "- 2026-08-25 draft (author): created.\n"
        )
        events = life._plan_status_events(text)
        statuses = [s for _d, s, _a in events]
        self.assertEqual(
            statuses, ["draft", "reviewed", "approved"]
        )  # oldest-first, note skipped
        self.assertEqual(life.derive_status_from_events(events), "approved")

    def test_backward_compat_status_read_unchanged(self):
        # The authoritative `- Status:` read (used by aw set/finalize/hooks) is unchanged by adding
        # derivation-alongside; the derived value cross-checks but does not replace it.
        text = (
            "# IPD: x\n\n- Id: aaa111\n- Status: approved\n\n## Workflow history\n"
            "- 2026-08-27 approved (aw set): status set to approved\n"
            "- 2026-08-25 draft (author): created.\n"
        )
        # the existing status-read primitive still returns the field value
        self.assertEqual(ce._status_meta(text), "approved")
        # and derivation agrees with it
        self.assertEqual(life.derive_plan_status(text), "approved")


class TestLifecycleEngineRule(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.pending = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending.mkdir(parents=True)

    def _plan(self, name, history_lines):
        body = (
            "# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n\n"
            "## Workflow history\n"
            + "".join(f"- {line}\n" for line in history_lines)
            + "\n## Goal\n\ng\n"
        )
        (self.pending / name).write_text(body, encoding="utf-8")

    def test_flags_backwards_transition_in_history(self):
        # newest-first inline order; a backwards approved->draft transition is invalid
        self._plan(
            "20260828-t-01-aaa111-x.ipd.md",
            [
                "2026-08-27 draft (aw set): back",
                "2026-08-26 approved (aw set): fwd",
                "2026-08-25 draft (author): created.",
            ],
        )
        drift = ce.check_lifecycle_transitions(self.root)
        rules = {d.rule for d in drift}
        self.assertIn("check.lifecycle-transition-invalid", rules)

    def test_clean_valid_history(self):
        self._plan(
            "20260828-t-01-aaa111-x.ipd.md",
            [
                "2026-08-27 approved (aw set): ok",
                "2026-08-26 reviewed (author): ok",
                "2026-08-25 draft (author): created.",
            ],
        )
        drift = ce.check_lifecycle_transitions(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.lifecycle-transition-invalid"], []
        )


# --------------------------------------------------------------------------------------
# E-02 / V-02: declared-file-scope drift
# --------------------------------------------------------------------------------------


class TestScopeDrift(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.pending = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending.mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "other").mkdir()
        (self.root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
        )

    def _plan(self, scope_paths="src/"):
        body = (
            f"# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n"
            f"- Scope-Paths: {scope_paths}\n\n## Workflow history\n"
            "- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n"
        )
        p = self.pending / "20260828-t-01-aaa111-x.ipd.md"
        p.write_text(body, encoding="utf-8")
        return p

    def _write_receipt(self, base_head):
        rpath = life.receipt_path_for(self.root, "aaa111")
        rpath.parent.mkdir(parents=True, exist_ok=True)
        rpath.write_text(
            json.dumps(
                {"plan_id": "aaa111", "base_head": base_head, "scope_paths": ["src/"]}
            ),
            encoding="utf-8",
        )

    def _commit_all(self, msg):
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

    def _head(self):
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()

    def test_flags_out_of_scope_change(self):
        self._plan("src/")
        self._commit_all("init")
        base = self._head()
        self._write_receipt(base)
        # change a path OUTSIDE src/
        (self.root / "other" / "x.py").write_text("y\n", encoding="utf-8")
        drift = ce.check_scope_drift(self.root)
        hits = [d for d in drift if d.rule == "check.scope-drift"]
        self.assertTrue(hits, [d.detail for d in drift])
        # git status collapses an untracked dir, so the reported out-of-scope path is `other/`.
        self.assertTrue(any("other" in d.detail for d in hits))

    def test_in_scope_change_clean(self):
        self._plan("src/")
        self._commit_all("init")
        base = self._head()
        self._write_receipt(base)
        (self.root / "src" / "feat.py").write_text("x\n", encoding="utf-8")
        drift = ce.check_scope_drift(self.root)
        self.assertEqual([d for d in drift if d.rule == "check.scope-drift"], [])

    def test_grandfathered_sentinel_not_flagged(self):
        self._plan("grandfathered")
        self._commit_all("init")
        base = self._head()
        self._write_receipt(base)
        (self.root / "other" / "x.py").write_text("y\n", encoding="utf-8")
        drift = ce.check_scope_drift(self.root)
        # grandfathered: no allowlist -> advisory-satisfied, never hard-flagged
        self.assertEqual([d for d in drift if d.rule == "check.scope-drift"], [])

    def test_no_receipt_no_drift(self):
        self._plan("src/")
        self._commit_all("init")
        (self.root / "other" / "x.py").write_text("y\n", encoding="utf-8")
        drift = ce.check_scope_drift(self.root)  # no receipt written
        self.assertEqual([d for d in drift if d.rule == "check.scope-drift"], [])

    def test_reuses_finalize_scope_helpers_no_fork(self):
        import inspect

        src = inspect.getsource(ce.check_scope_drift)
        self.assertIn("_paths_changed_by_this_execution", src)
        self.assertIn("_scope_match", src)
        self.assertIn("_frozen_scope_paths", src)


if __name__ == "__main__":
    unittest.main()

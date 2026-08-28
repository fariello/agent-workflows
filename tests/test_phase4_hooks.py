"""agentadhere Phase 4 (IPD diundn): local pre-commit/pre-push hooks + contract matrix.

Covers:
  E-01/V-01 - pre-commit scope/invariant gate: refuses an out-of-scope staged tree with a teaching
              message (invariant + recovery), passes clean, delegates to the shared aggregator (no
              fork), idempotent no-clobber install.
  E-02/V-02 - pre-push authorization gate: prevents an unacknowledged push with an HONEST local-only
              message, passes with the ack, delegates to the shared engine.
  E-03/V-03 - contract matrix (coverage, malformed input, disablement, fail-open/closed) + a
              NO-DIVERGENCE proof (hook and aw check produce the same rule for the same tree).
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import engine
from agent_workflows.hooks import precommit_scope_gate as pcgate
from agent_workflows.hooks import prepush_authorization_gate as ppgate


def _mk_repo(tmp: Path):
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp, check=True)
    (tmp / ".gitignore").write_text(".aw/state/\n.aw/worktrees/\n", encoding="utf-8")
    plans = tmp / ".aw" / "records" / "plans" / "pending"
    plans.mkdir(parents=True)
    (tmp / "src").mkdir()
    (tmp / "other").mkdir()
    (plans / "20260828-t-01-aaa111-x.ipd.md").write_text(
        "# IPD: x\n\n- Id: aaa111\n- Kind: child\n- Status: approved\n- Set: t\n- Order: 1\n"
        "- Scope-Paths: src/\n\n## Workflow history\n- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp, check=True)
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp, capture_output=True, text=True
    ).stdout.strip()
    rp = tmp / ".aw" / "state" / "ipd-lifecycle"
    rp.mkdir(parents=True, exist_ok=True)
    (rp / "aaa111.receipt.json").write_text(
        json.dumps({"plan_id": "aaa111", "base_head": base, "scope_paths": ["src/"]}),
        encoding="utf-8",
    )
    return tmp


class TestPreCommitGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _mk_repo(Path(self._tmp.name))

    def test_clean_in_scope_passes(self):
        (self.root / "src" / "f.py").write_text("x\n", encoding="utf-8")
        rc, msgs = pcgate.check(self.root)
        self.assertEqual(rc, 0, msgs)
        self.assertEqual(msgs, [])

    def test_out_of_scope_refused_with_teaching_message(self):
        (self.root / "other" / "g.py").write_text("y\n", encoding="utf-8")
        rc, msgs = pcgate.check(self.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(msgs)
        self.assertIn("check.scope-drift", joined)  # names the violated invariant/rule
        self.assertIn("fix:", joined)  # teaches the recovery command
        self.assertIn("Scope-Paths", joined)

    def test_delegates_to_shared_aggregator_no_fork(self):
        import inspect

        src = inspect.getsource(pcgate.check)
        self.assertIn("check_commit_invariants", src)
        # the aggregator only re-invokes existing shared rules (no forked policy)
        agg = inspect.getsource(ce.check_commit_invariants)
        self.assertIn("check_status_untooled", agg)
        self.assertIn("check_release_gate_consistency", agg)
        self.assertIn("check_scope_drift", agg)

    def test_no_divergence_hook_matches_aw_check(self):
        # the hook and the engine's scope-drift rule produce the SAME rule for the same tree
        (self.root / "other" / "g.py").write_text("y\n", encoding="utf-8")
        _rc, msgs = pcgate.check(self.root)
        engine_rules = {d.rule for d in ce.check_scope_drift(self.root)}
        self.assertIn("check.scope-drift", engine_rules)
        self.assertTrue(any("check.scope-drift" in m for m in msgs))

    def test_install_idempotent_no_clobber(self):
        r1 = engine.create_precommit_scope_gate_hook(self.root, False, install=True)
        self.assertEqual(r1["created"], [".pre-commit-config.yaml"])
        r2 = engine.create_precommit_scope_gate_hook(self.root, False, install=True)
        self.assertTrue(r2["skipped"])  # second run does not duplicate
        self.assertEqual(r2["created"], [])
        # install=False is a no-op
        r3 = engine.create_precommit_scope_gate_hook(self.root, False, install=False)
        self.assertEqual(r3, {"created": [], "skipped": [], "notes": []})

    def test_malformed_input_fails_isolated(self):
        # a corrupt receipt must not crash the gate (aggregator isolates a rule error)
        rp = self.root / ".aw" / "state" / "ipd-lifecycle" / "aaa111.receipt.json"
        rp.write_text("{not json", encoding="utf-8")
        rc, _msgs = pcgate.check(self.root)
        self.assertIn(rc, (0, 1))  # did not raise


class TestPrePushGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _mk_repo(Path(self._tmp.name))

    def test_prevents_unacknowledged_push(self):
        old = os.environ.pop(ce.PUSH_ACK_ENV, None)
        try:
            rc, msgs = ppgate.check(self.root)
        finally:
            if old is not None:
                os.environ[ce.PUSH_ACK_ENV] = old
        self.assertEqual(rc, 1)
        joined = "\n".join(msgs)
        self.assertIn("check.push-unauthorized", joined)

    def test_honest_local_only_message(self):
        out = io.StringIO()
        old = os.environ.pop(ce.PUSH_ACK_ENV, None)
        try:
            with redirect_stderr(out), redirect_stdout(io.StringIO()):
                rc = ppgate.main([])
        finally:
            if old is not None:
                os.environ[ce.PUSH_ACK_ENV] = old
        self.assertEqual(rc, 1)
        text = out.getvalue()
        # honestly states local-only, bypassable, NOT an authority boundary
        self.assertIn("NOT an authority boundary", text)
        self.assertIn("--no-verify", text)

    def test_ack_allows_push(self):
        os.environ[ce.PUSH_ACK_ENV] = "1"
        try:
            rc, msgs = ppgate.check(self.root)
        finally:
            os.environ.pop(ce.PUSH_ACK_ENV, None)
        self.assertEqual(rc, 0)
        self.assertEqual(msgs, [])

    def test_delegates_to_shared_engine_no_fork(self):
        import inspect

        src = inspect.getsource(ppgate.check)
        self.assertIn("check_push_authorization", src)

    def test_push_rule_is_authority_class(self):
        # honest labeling: the push invariant is Authority-class (a local hook can only give feedback)
        spec = ce.rule_spec("check.push-unauthorized")
        self.assertEqual(spec.assurance, ce.ASSURANCE_AUTHORITY)
        self.assertEqual(spec.invariant, "I-02")

    def test_install_idempotent_no_clobber(self):
        r1 = engine.create_prepush_authorization_gate_hook(
            self.root, False, install=True
        )
        self.assertEqual(r1["created"], [".pre-commit-config.yaml"])
        r2 = engine.create_prepush_authorization_gate_hook(
            self.root, False, install=True
        )
        self.assertTrue(r2["skipped"])


if __name__ == "__main__":
    unittest.main()

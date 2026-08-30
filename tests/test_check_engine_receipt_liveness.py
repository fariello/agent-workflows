"""IPD rygds7 (E-01/E-02, V-01..V-03): only a LIVE begin receipt may drive `check.scope-drift`.

A begin receipt is execution AUTHORITY for one in-flight plan. `check_scope_drift` used to accept ANY
receipt on disk, so a plan already sitting in a TERMINAL lifecycle directory kept driving a scope
advisory that compared the whole working tree against a frozen base no live execution owned. Because
the opt-in `precommit-scope-gate` hook and CI's `aw check plans` both reach that rule through the ONE
shared aggregator `check_commit_invariants`, a stale receipt could refuse every commit in a busy
shared checkout.

Covers, each in its OWN temp git repo (no test here reads the live checkout):
  (a) a receipt whose plan is in `executed/` produces NO finding even with an out-of-scope dirty path;
  (b) a receipt whose plan is in `pending/` STILL produces the finding for the same dirty path, so the
      rule was NARROWED and not disabled;
  (c) a receipt whose `base_head` is not an ancestor of HEAD is skipped;
  (d) each terminal dir (executed/superseded/not-executed) is rejected; pending/reusable are not;
  (e) an undeterminable liveness check results in a SKIP, not a finding and not a traceback (E-02);
  (f) a plan in a `<terminal>/YYYYMM/` SHARD is also skipped (pinning the first-path-component
      derivation against a `parent.name` regression, since `aw archive plans` creates such shards);
  (g) the assertions also run through `check_commit_invariants`, the aggregator the hook actually
      calls, so the fix is proven on the surface that gates commits.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as life
from agent_workflows import plans as plans_mod

PLAN_ID = "aaa111"
PLAN_NAME = "20260828-t-01-aaa111-x.ipd.md"


class ReceiptLivenessTests(unittest.TestCase):
    """Each test builds its own temp repo; mirrors tests/test_event_derived_lifecycle.py's fixture."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans"
        (self.root / "src").mkdir()
        (self.root / "other").mkdir()
        # `.aw/state/` holds the (gitignored) receipts; `.aw/worktrees/` holds per-lane worktrees.
        (self.root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n", encoding="utf-8"
        )

    # -- fixture helpers ---------------------------------------------------------------

    def _plan_at(self, rel_dir: str, scope_paths: str = "src/") -> Path:
        """Write the plan into `<plans>/<rel_dir>/` (e.g. 'pending', 'executed/202608')."""
        body = (
            f"# IPD: x\n\n- Id: {PLAN_ID}\n- Kind: child\n- Status: approved\n- Set: t\n"
            f"- Order: 1\n- Scope-Paths: {scope_paths}\n\n## Workflow history\n"
            "- 2026-08-25 approved (aw set): x\n\n## Goal\n\ng\n"
        )
        d = self.plans / rel_dir
        d.mkdir(parents=True, exist_ok=True)
        p = d / PLAN_NAME
        p.write_text(body, encoding="utf-8")
        return p

    def _write_receipt(self, base_head: str) -> Path:
        rpath = life.receipt_path_for(self.root, PLAN_ID)
        rpath.parent.mkdir(parents=True, exist_ok=True)
        rpath.write_text(
            json.dumps(
                {"plan_id": PLAN_ID, "base_head": base_head, "scope_paths": ["src/"]}
            ),
            encoding="utf-8",
        )
        return rpath

    def _commit_all(self, msg: str) -> None:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()

    def _dirty_out_of_scope(self) -> None:
        """Create a working-tree change OUTSIDE the plan's declared Scope-Paths (`src/`)."""
        (self.root / "other" / "x.py").write_text("y\n", encoding="utf-8")

    def _scope_hits(self, include_untracked: bool = False):
        return [
            d
            for d in ce.check_scope_drift(
                self.root, include_untracked=include_untracked
            )
            if d.rule == "check.scope-drift"
        ]

    def _aggregator_scope_hits(self):
        """Findings via `check_commit_invariants` - the surface the pre-commit hook calls (case g)."""
        return [
            d
            for d in ce.check_commit_invariants(self.root)
            if d.rule == "check.scope-drift"
        ]

    def _arrange(self, rel_dir: str, scope_paths: str = "src/") -> str:
        """Plan at `rel_dir`, committed, receipt frozen at HEAD, one out-of-scope dirty path."""
        self._plan_at(rel_dir, scope_paths)
        self._commit_all("init")
        base = self._head()
        self._write_receipt(base)
        self._dirty_out_of_scope()
        return base

    # -- (a) terminal plan: receipt ignored --------------------------------------------

    def test_a_executed_plan_receipt_is_ignored(self):
        """(a) A plan in `executed/` yields NO scope-drift finding despite an out-of-scope change.

        This is the defect: pre-fix the receipt was believed and the finding was emitted.
        """
        self._arrange("executed")
        self.assertEqual([d.detail for d in self._scope_hits()], [])

    # -- (b) narrowed, not disabled ----------------------------------------------------

    def test_b_pending_plan_still_flags_the_same_dirty_path(self):
        """(b) The SAME dirty path against a `pending/` plan is still flagged (rule not disabled)."""
        self._arrange("pending")
        hits = self._scope_hits()
        self.assertTrue(hits, "a pending plan's live receipt must still be enforced")
        self.assertTrue(
            any("other" in d.detail for d in hits), [d.detail for d in hits]
        )

    def test_b_narrowing_is_the_only_difference(self):
        """(b, sharpened) Identical repo/receipt/dirty path; ONLY the plan's directory differs."""
        self._arrange("pending")
        self.assertTrue(self._scope_hits(), "pending must flag")
        # Move the very same plan into a terminal dir; nothing else changes.
        src = self.plans / "pending" / PLAN_NAME
        dst_dir = self.plans / "executed"
        dst_dir.mkdir(parents=True, exist_ok=True)
        src.rename(dst_dir / PLAN_NAME)
        self.assertEqual(self._scope_hits(), [], "terminal must not flag")

    # -- (c) unreachable frozen base ---------------------------------------------------

    def test_c_base_head_not_ancestor_of_head_is_skipped(self):
        """(c) A `base_head` that is not an ancestor of HEAD cannot describe this history."""
        self._plan_at("pending")
        self._commit_all("init")
        # A well-formed but unreachable sha (not in this repo's history at all).
        self._write_receipt("0" * 40)
        self._dirty_out_of_scope()
        self.assertEqual([d.detail for d in self._scope_hits()], [])

    def test_c_orphan_branch_commit_is_not_an_ancestor(self):
        """(c, real history) A commit on an orphan branch is a genuine unreachable base."""
        self._plan_at("pending")
        self._commit_all("init")
        # Capture the initial branch by NAME: the default ('master'/'main') is environment-dependent
        # and `git checkout -` has no previous ref to return to from a fresh orphan branch.
        main_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "checkout", "-q", "--orphan", "sidelane"], cwd=self.root, check=True
        )
        (self.root / "sidefile").write_text("s\n", encoding="utf-8")
        self._commit_all("orphan")
        orphan_head = self._head()
        subprocess.run(
            ["git", "checkout", "-q", main_branch], cwd=self.root, check=True
        )
        self.assertNotEqual(orphan_head, self._head())
        self._write_receipt(orphan_head)
        self._dirty_out_of_scope()
        self.assertEqual([d.detail for d in self._scope_hits()], [])

    def test_c_empty_base_head_is_skipped(self):
        """(c) An empty `base_head` is not live (also pre-existing behavior; kept true here)."""
        self._plan_at("pending")
        self._commit_all("init")
        self._write_receipt("")
        self._dirty_out_of_scope()
        self.assertEqual([d.detail for d in self._scope_hits()], [])

    # -- (d) the exact terminal vocabulary --------------------------------------------

    def test_d_every_terminal_dir_rejected_and_non_terminal_kept(self):
        """(d) executed/superseded/not-executed are terminal; pending/reusable are not."""
        for rel_dir in plans_mod.TERMINAL:
            with self.subTest(directory=rel_dir, expect="skipped"):
                self.setUp()  # a fresh repo per case, so no state leaks between them
                self._arrange(rel_dir)
                self.assertEqual(
                    [d.detail for d in self._scope_hits()],
                    [],
                    f"{rel_dir} is terminal and must be skipped",
                )
        for rel_dir in ("pending", "reusable"):
            with self.subTest(directory=rel_dir, expect="flagged"):
                self.setUp()
                self._arrange(rel_dir)
                self.assertTrue(
                    self._scope_hits(),
                    f"{rel_dir} is NOT terminal and must be enforced",
                )

    def test_d_terminal_vocabulary_is_the_shared_one(self):
        """(d) The predicate reuses `plans.TERMINAL`, not a fourth hardcoded copy of the names."""
        import inspect

        src = inspect.getsource(ce._receipt_is_live)
        self.assertIn("TERMINAL", src)
        self.assertNotIn('"executed"', src)
        self.assertNotIn("'executed'", src)
        self.assertEqual(plans_mod.TERMINAL, ("executed", "superseded", "not-executed"))

    # -- (e) fail safe, not fail open --------------------------------------------------

    def test_e_liveness_error_results_in_a_skip(self):
        """(e) When the liveness check itself raises, the receipt is skipped (E-02 fail-safe)."""
        self._arrange("pending")
        self.assertTrue(
            self._scope_hits(), "sanity: this arrangement flags when healthy"
        )

        boom_calls = []
        real = ce._git_capture

        def boom(repo_root, args):
            if args[:1] == ["merge-base"]:
                boom_calls.append(args)
                raise OSError("git unavailable")
            return real(repo_root, args)

        ce._git_capture = boom
        try:
            hits = self._scope_hits()  # must not raise
        finally:
            ce._git_capture = real
        self.assertTrue(boom_calls, "the induced error path must actually be exercised")
        self.assertEqual([d.detail for d in hits], [])

    def test_e_failsafe_is_inside_the_predicate_not_the_aggregator(self):
        """(e) The skip comes from the predicate itself, so the aggregator's blanket `except` (which
        would also swallow a genuine bug in the comparison) is NOT what makes this safe."""
        self._arrange("pending")
        real = ce._git_capture

        def boom(repo_root, args):
            if args[:1] == ["merge-base"]:
                raise OSError("git unavailable")
            return real(repo_root, args)

        ce._git_capture = boom
        try:
            # Called DIRECTLY, bypassing check_commit_invariants' try/except entirely.
            direct = ce.check_scope_drift(self.root)
            live = ce._receipt_is_live(
                self.root, self.plans / "pending" / PLAN_NAME, {"base_head": "deadbeef"}
            )
        finally:
            ce._git_capture = real
        self.assertEqual([d for d in direct if d.rule == "check.scope-drift"], [])
        self.assertFalse(live, "an undeterminable liveness must be treated as NOT live")

    def test_e_missing_plan_location_is_not_live(self):
        """(e) A plan that cannot be located under any plans dir is treated as not live."""
        self._plan_at("pending")
        self._commit_all("init")
        outside = self.root / "not-a-plan-dir" / PLAN_NAME
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text("# IPD: x\n\n- Id: aaa111\n", encoding="utf-8")
        self.assertIsNone(ce._plan_disposition(self.root, outside))

    # -- (f) sharded terminal plan (the parent.name regression) ------------------------

    def test_f_sharded_terminal_plan_is_skipped(self):
        """(f) `executed/YYYYMM/` (what `aw archive plans` creates) is still terminal.

        A `parent.name`-based implementation would read '202608' here, not 'executed', and would
        wrongly flag. This is the regression that would otherwise appear the first time anything is
        archived.
        """
        self._arrange("executed/202608")
        self.assertEqual([d.detail for d in self._scope_hits()], [])

    def test_f_sharded_pending_plan_is_not_skipped(self):
        """(f) The mirror: a shard under a NON-terminal disposition must still be enforced, so the
        skip is attributable to the disposition and not merely to path depth."""
        self._arrange("pending/202608")
        self.assertTrue(self._scope_hits())

    def test_f_disposition_is_the_first_path_component(self):
        """(f) Pin the derivation directly: first component under the plans dir, not the parent."""
        for rel, expected in (
            ("executed/x.ipd.md", "executed"),
            ("executed/202608/x.ipd.md", "executed"),
            ("superseded/202601/x.ipd.md", "superseded"),
            ("not-executed/202608/x.ipd.md", "not-executed"),
            ("pending/202608/x.ipd.md", "pending"),
        ):
            p = self.plans / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x\n", encoding="utf-8")
            with self.subTest(rel=rel):
                self.assertEqual(ce._plan_disposition(self.root, p), expected)
                if "/" in rel.split("/", 1)[1]:
                    # Demonstrate the naive alternative really would differ on a shard.
                    self.assertNotEqual(p.parent.name, expected)

    # -- (g) the aggregator surface the hook calls ------------------------------------

    def test_g_aggregator_terminal_plan_is_clean(self):
        """(g) Through `check_commit_invariants`: a terminal plan's receipt gates nothing."""
        self._arrange("executed")
        self.assertEqual([d.detail for d in self._aggregator_scope_hits()], [])

    def test_g_aggregator_pending_plan_still_refuses(self):
        """(g) Through the same aggregator: a live receipt still produces the refusal."""
        self._arrange("pending")
        self.assertTrue(self._aggregator_scope_hits())

    def test_g_hook_exit_code_flips_with_liveness(self):
        """(g) End-to-end on the real gate: the hook refuses for a live plan and passes for a
        terminal one, which is the whole point (installing it must not refuse every commit)."""
        from agent_workflows.hooks import precommit_scope_gate as gate

        self._arrange("pending")
        rc_live, msgs_live = gate.check(self.root)
        self.assertEqual(rc_live, 1, msgs_live)

        src = self.plans / "pending" / PLAN_NAME
        dst = self.plans / "executed"
        dst.mkdir(parents=True, exist_ok=True)
        src.rename(dst / PLAN_NAME)
        rc_terminal, msgs_terminal = gate.check(self.root)
        self.assertEqual(rc_terminal, 0, msgs_terminal)

    # -- the receipt is ignored, NEVER deleted ----------------------------------------

    def test_ignoring_a_terminal_receipt_does_not_delete_it(self):
        """A terminal plan's receipt may still be required by an unfinished finalize transaction
        (`committed-incomplete` re-runs finalize on a plan already in `executed/`), so this rule must
        ignore it WITHOUT removing it. Guards against a later 'terminal implies cleanup' change."""
        self._arrange("executed")
        rpath = life.receipt_path_for(self.root, PLAN_ID)
        self.assertTrue(rpath.exists())
        self.assertEqual(self._scope_hits(), [])
        self.assertTrue(
            rpath.exists(), "the rule is read-only; it must not consume the receipt"
        )
        self.assertEqual(json.loads(rpath.read_text())["plan_id"], PLAN_ID)


if __name__ == "__main__":
    unittest.main()

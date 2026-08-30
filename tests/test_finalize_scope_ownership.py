"""Finalize attributes by OWNERSHIP, not by mere dirtiness (scopeattrib Order 01, lbgzxg).

The defect: ``_paths_changed_by_this_execution`` unioned the committed diff since the frozen base
with the ENTIRE ``git status --porcelain`` and applied no ownership filter, so in a SHARED checkout
every concurrent agent's uncommitted file was attributed to whichever plan finalized first. That
plan's only options were to write a false ``--scope-reason`` into its permanent record or to block
until every other agent happened to be clean.

The fix RESCOPES the gate; it does not remove it. These tests prove BOTH directions:

* the working-tree half is ownership-filtered, so an unowned disjoint dirty path is disregarded
  (and RECORDED as disregarded rather than silently dropped);
* the committed half is untouched, so a path the plan ITSELF committed out of scope still demands a
  reason, and the intervening-commit collision computation still reports in-scope collisions.

Two cases here are CHARACTERIZATION tests that pin accepted costs rather than desired features:
``test_own_UNCOMMITTED_out_of_scope_edit_is_now_disregarded_ACCEPTED_REGRESSION`` (F3/OQ-01) and
``test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation`` (F9, backlog
`a8eufb`). Both say so in their names and docstrings.

Stdlib unittest on throwaway git repos, reusing the proven fixture helpers from
``tests.test_ipd_lifecycle_cli`` (that module is deliberately NOT edited by this plan).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC

from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _write_plan,
)

ACTOR = "opencode/test"
SCOPE = "agent_workflows/demo.py, tests/test_demo.py"


def _commit_paths(root: Path, message: str, paths: list[str]) -> None:
    """Path-scoped commit, mirroring the execution contract (never ``git add -A``)."""
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message, "--", *paths], cwd=root, check=True
    )


def _git_out(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


class _ScopeOwnershipBase(unittest.TestCase):
    """A throwaway repo holding one approved, execution-ready plan with a real frozen scope."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _plan(self, scope_paths: str = SCOPE, plan_id: str = "abc123") -> Path:
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths=scope_paths),
            f"20260830-demo-01-{plan_id}-demo.ipd.md",
        )
        _commit_all(self.root, f"add plan {plan_id}")
        return plan

    def _begin(self, plan: Path):
        res = LC.begin(self.root, plan, ACTOR, timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        return res

    def _do_in_scope_work_and_commit(self) -> None:
        """The plan's OWN work, committed path-scoped exactly as the execution contract requires."""
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "tests/test_demo.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(
            self.root,
            "the plan's own in-scope work",
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )

    def _audit(self, plan: Path) -> dict:
        code, msg, evidence, _findings = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_OK, msg)
        return evidence["scope_audit"]

    def _executed_path(self, plan: Path) -> Path:
        return self.root / ".aw" / "records" / "plans" / "executed" / plan.name


class WorkingTreeOwnershipFilterTests(_ScopeOwnershipBase):
    """E-04 (a)(e)(f): the working-tree half is filtered by ownership, visibly."""

    def test_unowned_dirty_path_no_longer_blocks_finalize(self):
        """E-04 case (a): the exact F1 failure. A plan that committed its own in-scope work
        finalizes with NO --scope-reason while an unrelated agent's file is dirty.

        FAILS against pre-fix code, where this exited 1 demanding a reason for coworker.py.
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        # A concurrent agent's in-flight file: untracked, disjoint from Scope-Paths, not ours.
        (self.root / "agent_workflows/coworker.py").write_text(
            "not mine\n", encoding="utf-8"
        )

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)

        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertEqual(result.findings, ())
        self.assertTrue(
            self._executed_path(plan).is_file(), "plan should have moved to executed/"
        )
        self.assertFalse(plan.is_file())
        # The co-worker's file is untouched: still untracked, still theirs.
        self.assertIn(
            "?? agent_workflows/coworker.py",
            _git_out(self.root, ["status", "--porcelain"]),
        )

    def test_disregarded_unowned_path_is_recorded_in_the_evidence_not_dropped(self):
        """E-04 case (e): the excluded path is VISIBLE under its own scope-audit key and in the
        human message, alongside the existing out_of_scope_paths key.

        FAILS against pre-fix code, which had no such key (and refused instead).
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        (self.root / "agent_workflows/coworker.py").write_text(
            "not mine\n", encoding="utf-8"
        )

        code, msg, evidence, _f = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_OK, msg)
        audit = evidence["scope_audit"]

        self.assertEqual(
            audit["disregarded_unowned_paths"], ["agent_workflows/coworker.py"]
        )
        self.assertEqual(
            audit["out_of_scope_paths"], []
        )  # the pre-existing key still there
        self.assertIn("out_of_scope_paths", audit)
        self.assertIn("in_scope_unmodified", audit)
        self.assertIn("intervening_in_scope_commits", audit)
        # The two halves are separately recorded, so an auditor can see WHY it was disregarded.
        self.assertEqual(audit["working_tree_paths"], ["agent_workflows/coworker.py"])
        self.assertNotIn("agent_workflows/coworker.py", audit["committed_paths"])
        # Surfaced to the human, not hidden.
        self.assertIn("agent_workflows/coworker.py", msg)
        self.assertIn("not owned by this execution", msg)
        # User-facing message text carries no em or en dash (execution contract).
        self.assertNotIn("\u2014", msg)
        self.assertNotIn("\u2013", msg)

        # The same note reaches the terminal success message.
        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
        self.assertIn("agent_workflows/coworker.py", result.message)
        self.assertIn("Disregarded", result.message)
        self.assertNotIn("\u2014", result.message)
        self.assertNotIn("\u2013", result.message)

    def test_own_UNCOMMITTED_out_of_scope_edit_is_now_disregarded_ACCEPTED_REGRESSION(
        self,
    ):
        """E-04 case (f): CHARACTERIZATION of the ONE accepted cost (F3 / OQ-01), not a feature.

        A `git status --porcelain` entry carries no author, so the executor's OWN uncommitted
        out-of-scope edit is byte-identical to a co-worker's; no filter at this site can separate
        them. The fix therefore stops demanding a reason for the executor's own uncommitted
        out-of-scope work too. This is DELIBERATE and mitigated, not overlooked:

        * the execution contract requires path-scoped commits, so an executor's real out-of-scope
          work is COMMITTED by finalize time and lands in the committed half, where
          ``test_own_committed_out_of_scope_path_still_demands_a_reason`` still refuses it; and
        * the path is recorded as disregarded (asserted below), so it never becomes invisible.

        If a future change makes uncommitted ownership provable, this test SHOULD start failing and
        should then be inverted rather than deleted.
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        # The executor's OWN out-of-scope edit, left UNCOMMITTED (contrary to the contract).
        (self.root / "agent_workflows/mine_oos.py").write_text(
            "mine, uncommitted\n", encoding="utf-8"
        )

        audit = self._audit(plan)
        self.assertEqual(
            audit["out_of_scope_paths"], [], "accepted regression: no longer refused"
        )
        self.assertEqual(
            audit["disregarded_unowned_paths"],
            ["agent_workflows/mine_oos.py"],
            "the accepted cost must stay VISIBLE in the audit trail",
        )
        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)


class NoWeakeningTests(_ScopeOwnershipBase):
    """E-04 (b)(c)(d): every refusal the gate legitimately owns must survive the rescoping.

    These are the assertions that FAIL if the working-tree half is DELETED outright instead of
    ownership-filtered, or if the filter leaks into the committed half.
    """

    def test_own_committed_out_of_scope_path_still_demands_a_reason(self):
        """E-04 case (b), the NO-WEAKENING assertion (F2 scenario A).

        A commit EXISTS for this path, so it is attributable and the audit trail must keep
        demanding a justification. Fails if E-02 filtered the committed half by mistake.

        It ALSO fails if the working-tree half is DELETED outright rather than ownership-filtered:
        the dirty in-scope path below must still be collected, which is the difference between
        rescoping the gate and removing half its input.
        """
        plan = self._plan()
        self._begin(plan)
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "tests/test_demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/mine_oos.py").write_text(
            "mine, out of scope\n", encoding="utf-8"
        )
        _commit_paths(
            self.root,
            "own work including an out-of-scope path",
            [
                "agent_workflows/demo.py",
                "tests/test_demo.py",
                "agent_workflows/mine_oos.py",
            ],
        )
        # A further in-scope edit left dirty: the working-tree half must still see it.
        (self.root / "agent_workflows/demo.py").write_text(
            "mine\nmore\n", encoding="utf-8"
        )

        audit = self._audit(plan)
        self.assertEqual(audit["out_of_scope_paths"], ["agent_workflows/mine_oos.py"])
        self.assertEqual(audit["disregarded_unowned_paths"], [])
        self.assertEqual(
            audit["working_tree_paths"],
            ["agent_workflows/demo.py"],
            "the working-tree half must still be COLLECTED (rescoped, not deleted)",
        )

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("--scope-reason", result.message)
        self.assertTrue(
            any("agent_workflows/mine_oos.py" in f for f in result.findings)
        )
        self.assertTrue(plan.is_file(), "plan must be left unmoved")

        # And a supplied reason still legitimizes it, recorded verbatim in the terminal history.
        ok = LC.finalize(
            self.root,
            plan,
            ACTOR,
            "did the work",
            apply=True,
            scope_reasons={"agent_workflows/mine_oos.py": "needed mid-stream"},
        )
        self.assertEqual(ok.exit_code, LC.EXIT_OK, f"{ok.message} / {ok.findings}")
        moved = self._executed_path(plan).read_text(encoding="utf-8")
        self.assertIn("out-of-scope agent_workflows/mine_oos.py", moved)
        self.assertIn("needed mid-stream", moved)

    def test_dirty_path_inside_scope_paths_behaves_exactly_as_before(self):
        """E-04 case (c): pins F8. An in-scope dirty path was never out-of-scope and still is not,
        so the ownership filter must not turn it into a disregarded path either.

        In-scope dirtiness is BEGIN's gate, not finalize's; this test exists so nobody 'fixes' a
        non-defect. Fails if the working-tree half is deleted outright (working_tree_paths would
        no longer report the dirty in-scope path).
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        # Dirty an IN-SCOPE path after committing it.
        (self.root / "agent_workflows/demo.py").write_text(
            "mine\nmore\n", encoding="utf-8"
        )

        audit = self._audit(plan)
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertEqual(
            audit["disregarded_unowned_paths"], [], "in-scope, so never disregarded"
        )
        self.assertIn("agent_workflows/demo.py", audit["working_tree_paths"])
        self.assertTrue(audit["in_scope"])

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(self._executed_path(plan).is_file())

    def test_intervening_commit_collision_computation_is_unchanged(self):
        """E-04 case (d): the in-scope intervening-commit computation still reports collisions.

        Per OQ-02 this must NOT be ownership-filtered: its purpose is the opposite, namely to
        surface commits touching this plan's declared territory. It reads only the committed diff.

        Also fails under a naive deletion of the working-tree half, which would stop reporting the
        dirty declared path in ``working_tree_paths`` and would wrongly report that declared path as
        in-scope-unmodified.
        """
        plan = self._plan(
            "agent_workflows/demo.py, tests/test_demo.py, tests/declared.py"
        )
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        (self.root / "agent_workflows/coworker.py").write_text(
            "not mine\n", encoding="utf-8"
        )
        # A DECLARED path touched only in the working tree: the missing-work direction must see it.
        (self.root / "tests/declared.py").write_text("dirty only\n", encoding="utf-8")

        audit = self._audit(plan)
        self.assertEqual(
            audit["intervening_in_scope_commits"],
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )
        # The disregarded path is NOT laundered into the collision set.
        self.assertNotIn(
            "agent_workflows/coworker.py", audit["intervening_in_scope_commits"]
        )
        # The working-tree half still feeds the in-scope-unmodified computation, so a declared path
        # touched ONLY in the working tree is correctly NOT reported as unmodified.
        self.assertIn("tests/declared.py", audit["working_tree_paths"])
        self.assertNotIn("tests/declared.py", audit["in_scope_unmodified"])

    def test_isolated_lane_finalize_is_unaffected_by_the_ownership_filter(self):
        """E-04 case (g): pins F9's blast-radius measurement. An isolated lane was ALREADY immune
        (it cannot see main's uncommitted files), and it must stay immune and unchanged.

        Exists so a later reader does not 'fix' the lane path, which was never broken. The lane is
        modeled as a real ``git worktree`` finalizing its own tree while main is dirty.
        """
        plan = self._plan()
        lane = self.root.parent / (self.root.name + "-lane")
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "aw/lane/abc123", str(lane), "HEAD"],
            cwd=self.root,
            check=True,
        )
        try:
            lane_plan = lane / plan.relative_to(self.root)
            self.assertTrue(lane_plan.is_file())
            res = LC.begin(lane, lane_plan, ACTOR, timestamp="t")
            self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
            # The lane does its own in-scope work path-scoped.
            (lane / "agent_workflows").mkdir(exist_ok=True)
            (lane / "tests").mkdir(exist_ok=True)
            (lane / "agent_workflows/demo.py").write_text("lane\n", encoding="utf-8")
            (lane / "tests/test_demo.py").write_text("lane\n", encoding="utf-8")
            _commit_paths(
                lane,
                "lane in-scope work",
                ["agent_workflows/demo.py", "tests/test_demo.py"],
            )
            # MAIN is dirty with an unrelated file the lane cannot see.
            (self.root / "agent_workflows/coworker.py").write_text(
                "main dirty\n", encoding="utf-8"
            )

            code, msg, evidence, _f = LC.finalize_precheck(lane, lane_plan)
            self.assertEqual(code, LC.EXIT_OK, msg)
            audit = evidence["scope_audit"]
            self.assertEqual(audit["out_of_scope_paths"], [])
            # Nothing to disregard: the lane's porcelain never contained main's file.
            self.assertEqual(audit["disregarded_unowned_paths"], [])
            self.assertEqual(audit["working_tree_paths"], [])
            self.assertEqual(_git_out(lane, ["status", "--porcelain"]), "")
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(lane)],
                cwd=self.root,
                check=False,
            )


class BeginFinalizeConsistencyTests(_ScopeOwnershipBase):
    """E-05: begin and finalize must reach the SAME verdict on a disjoint unowned dirty path."""

    def test_begin_and_finalize_agree_about_a_disjoint_unowned_dirty_path(self):
        """The invariant the underlying bug violated, asserted on ONE repo state.

        ``begin`` already ignores disjoint uncommitted work so a concurrent multi-agent workflow is
        not thrashed; before this fix ``finalize`` demanded a reason for that same path, which is
        the divergence. Asserting the AGREEMENT (not two separate per-gate behaviors) is what a
        future edit to either gate would break.

        FAILS against pre-fix code at the finalize half.
        """
        plan = self._plan()
        # ONE repo state: a disjoint, unowned, uncommitted path present for BOTH gates.
        (self.root / "agent_workflows/coworker.py").write_text(
            "not mine\n", encoding="utf-8"
        )

        # begin GRANTS authority: the dirty path is outside this plan's Scope-Paths.
        begin_res = LC.begin(self.root, plan, ACTOR, timestamp="t")
        begin_grants = begin_res.exit_code == LC.EXIT_OK

        self._do_in_scope_work_and_commit()  # the plan does its own work, contract-style
        self.assertIn(
            "?? agent_workflows/coworker.py",
            _git_out(self.root, ["status", "--porcelain"]),
            "the same unowned dirty path must still be present for the finalize half",
        )

        audit = self._audit(plan)
        finalize_demands_reason = (
            "agent_workflows/coworker.py" in audit["out_of_scope_paths"]
        )

        self.assertTrue(begin_grants, f"begin should grant: {begin_res.message}")
        self.assertFalse(
            finalize_demands_reason,
            "finalize must NOT demand a reason for a path begin deliberately ignored",
        )
        # Stated as the agreement itself, so either gate drifting breaks this assertion.
        self.assertEqual(
            begin_grants,
            not finalize_demands_reason,
            "begin and finalize must agree about a disjoint unowned dirty path",
        )
        self.assertIn("agent_workflows/coworker.py", audit["disregarded_unowned_paths"])


class CommittedHalfResidualGapTests(_ScopeOwnershipBase):
    """E-06: the KNOWN RESIDUAL GAP (F9), pinned so it cannot be mistaken for fixed."""

    def test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation(self):
        """DOCUMENTED LIMITATION, not a feature: pins post-fix behavior that MUST be INVERTED.

        Follow-up that must invert this test: backlog item `a8eufb`
        (scopeattrib, 'finalize still demands a scope reason for a CONCURRENT agent's COMMITTED
        out-of-scope path'). Do NOT delete this test to make that fix pass; invert it.

        scopeattrib Order 01 fixed the WORKING-TREE half of the attribution union only. When a
        concurrent agent COMMITS its unrelated out-of-scope file instead of leaving it dirty, the
        path enters the COMMITTED half, which this plan deliberately does not filter, so finalize
        STILL demands a --scope-reason for work the finalizing plan never touched. In a repo where
        concurrent agents commit to one branch continuously this is common, not exotic.

        The test also demonstrates WHY git authorship cannot rescue the committed half: the
        co-worker commit here is authored under the SAME user.name/user.email as the executor's, so
        an ``%an``-based filter would look like a fix and do nothing. A future implementer needs a
        real per-path or per-commit ownership record (see `a8eufb`).
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        # A concurrent agent COMMITS an unrelated out-of-scope file, under the SAME git identity.
        (self.root / "agent_workflows/other_agents_file.py").write_text(
            "another agent's work\n", encoding="utf-8"
        )
        _commit_paths(
            self.root,
            "another agent's unrelated commit",
            ["agent_workflows/other_agents_file.py"],
        )

        # SAME-IDENTITY condition: authorship cannot discriminate the two commits.
        identities = set(
            _git_out(self.root, ["log", "--format=%an|%ae", "-2"]).splitlines()
        )
        self.assertEqual(
            len(identities),
            1,
            f"the limitation requires ONE shared identity; got {identities}",
        )

        audit = self._audit(plan)
        # STILL refused: this is the declared bound, and a SUCCESS here would mean E-02 leaked
        # into the committed half and the no-weakening proof is invalid.
        self.assertEqual(
            audit["out_of_scope_paths"],
            ["agent_workflows/other_agents_file.py"],
            "residual gap: the committed half is intentionally NOT ownership-filtered",
        )
        self.assertEqual(audit["disregarded_unowned_paths"], [])
        self.assertIn("agent_workflows/other_agents_file.py", audit["committed_paths"])

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any("agent_workflows/other_agents_file.py" in f for f in result.findings)
        )
        self.assertTrue(plan.is_file(), "plan left unmoved by the residual gap")


class ChangedPathSourcesSplitTests(_ScopeOwnershipBase):
    """E-01: the split is behavior-neutral for the union-returning surface."""

    def test_union_of_the_split_equals_the_pre_split_union(self):
        """``_paths_changed_by_this_execution`` must still return the exact same sorted union.

        The name is asserted as a source substring by tests/test_event_derived_lifecycle.py and the
        union surface is consumed by check_engine.check_scope_drift, so neither may change.
        """
        plan = self._plan()
        self._begin(plan)
        receipt = LC.read_receipt(self.root, "abc123")
        self.assertIsNotNone(receipt)
        assert receipt is not None  # narrow for the type checker
        base = receipt["base_head"]
        # Every case at once: committed in-scope, committed out-of-scope, untracked, dirty, staged.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/mine_oos.py").write_text(
            "mine\n", encoding="utf-8"
        )
        _commit_paths(
            self.root,
            "committed work",
            ["agent_workflows/demo.py", "agent_workflows/mine_oos.py"],
        )
        (self.root / "agent_workflows/coworker.py").write_text(
            "theirs\n", encoding="utf-8"
        )
        (self.root / "agent_workflows/demo.py").write_text(
            "mine\ndirty\n", encoding="utf-8"
        )
        (self.root / "tests/staged.py").write_text("staged\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "--", "tests/staged.py"], cwd=self.root, check=True
        )

        sources = LC._changed_path_sources(self.root, base)
        union = LC._paths_changed_by_this_execution(self.root, base)

        # The union-returning surface is exactly the union of the two halves.
        self.assertEqual(union, sources.union())
        self.assertEqual(
            union, sorted(set(sources.committed) | set(sources.working_tree))
        )
        # And the two halves really are DIFFERENT sets carrying different evidence.
        self.assertIn("agent_workflows/mine_oos.py", sources.committed)
        self.assertNotIn("agent_workflows/mine_oos.py", sources.working_tree)
        self.assertIn("agent_workflows/coworker.py", sources.working_tree)
        self.assertNotIn("agent_workflows/coworker.py", sources.committed)
        # A path can legitimately be in BOTH (committed then edited again).
        self.assertIn("agent_workflows/demo.py", sources.committed)
        self.assertIn("agent_workflows/demo.py", sources.working_tree)

    def test_ownership_predicate_only_ever_removes_paths_never_adds(self):
        """The predicate is a pure narrowing of the out-of-scope set: owned by scope, by a commit,
        or by an implicit lifecycle allowance."""
        scope = ["agent_workflows/demo.py", "tests/"]
        committed = ("agent_workflows/mine_oos.py",)
        plan_rel = ".aw/records/plans/pending/20260830-demo-01-abc123-demo.ipd.md"

        def owned(p: str) -> bool:
            return LC._working_tree_path_is_owned(
                p, scope_paths=scope, committed=committed, plan_rel=plan_rel
            )

        self.assertTrue(owned("agent_workflows/demo.py"), "in Scope-Paths")
        self.assertTrue(
            owned("tests/anything.py"), "under a dir-bounded Scope-Paths entry"
        )
        self.assertTrue(owned("agent_workflows/mine_oos.py"), "already committed by us")
        self.assertTrue(owned(plan_rel), "the plan's own file")
        self.assertTrue(
            owned(".aw/records/plans/INDEX.json"), "implicit lifecycle allowance"
        )
        self.assertFalse(
            owned("agent_workflows/coworker.py"), "unowned: nothing attributes it"
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

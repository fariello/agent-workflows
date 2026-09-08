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
    """The residual gap `a8eufb` named is now CLOSED (scopeattr `h9cn0y` E-02).

    THIS CLASS WAS DELIBERATELY INVERTED, NOT DELETED. Its previous single test,
    ``test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation``, pinned the
    post-scopeattrib-Order-01 behavior and its own docstring instructed the follow-up: "pins post-fix
    behavior that MUST be INVERTED ... Do NOT delete this test to make that fix pass; invert it."
    Backlog `a8eufb` records the same assignment by name ("`h9cn0y` also owns inverting the
    characterization test"). The inversion below keeps the original's SAME-IDENTITY measurement,
    because that measurement is now the positive evidence that COHESION rather than authorship did
    the work.
    """

    def test_committed_half_of_a_coworker_is_now_disregarded_gap_CLOSED(self):
        """The INVERSION of the former documented limitation. Closes `a8eufb`'s step (3).

        A concurrent agent COMMITS an unrelated out-of-scope file instead of leaving it dirty. Before
        `h9cn0y` the path entered the unfiltered COMMITTED half and finalize demanded a
        ``--scope-reason`` for work the finalizing plan never touched, which in a repo where agents
        commit to one branch continuously is common rather than exotic, and which wrote a FALSE claim
        into the plan's permanent record.

        It is now DISREGARDED, because the co-worker's commit touched NO path this plan declared, so
        it is not cohesive with this execution's commits.

        THE SAME-IDENTITY ASSERTION IS RETAINED FROM THE ORIGINAL and is the point of the test: the
        co-worker's commit shares the executor's ``user.name``/``user.email``, so an ``%an``-based
        filter would look like a fix and do nothing. This test therefore also proves the fix does not
        secretly depend on authorship.
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

        # SAME-IDENTITY condition, retained: authorship cannot discriminate the two commits, so
        # whatever excludes the co-worker's path below, it is provably not an authorship lookup.
        identities = set(
            _git_out(self.root, ["log", "--format=%an|%ae", "-2"]).splitlines()
        )
        self.assertEqual(
            len(identities),
            1,
            f"the test requires ONE shared identity; got {identities}",
        )

        audit = self._audit(plan)
        # NO LONGER REFUSED: the co-worker's commit is not cohesive with this plan's territory.
        self.assertEqual(
            audit["out_of_scope_paths"],
            [],
            "a concurrent agent's committed out-of-scope path must not demand a reason",
        )
        # Excluded VISIBLY, in the one existing evidence channel.
        self.assertEqual(
            audit["disregarded_unowned_paths"],
            ["agent_workflows/other_agents_file.py"],
        )
        self.assertIn("agent_workflows/other_agents_file.py", audit["committed_paths"])

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(
            self._executed_path(plan).is_file(),
            "the plan should now finalize without justifying another agent's commit",
        )


class CommittedHalfAttributionTests(_ScopeOwnershipBase):
    """scopeattr `h9cn0y` E-04: the COMMITTED half is attributed by COMMIT COHESION.

    The mechanism, stated once so each test below can be read against it: a commit is one atomic act
    by one actor, so a commit that touched a path this plan DECLARED is this execution's commit and
    every path in it is attributable to this execution; a commit that touched NO declared path is not.
    Authorship is useless here (all actors share one git identity) and the run record is unreachable
    from finalize, so the commit boundary is the only evidence available.

    All of these arrange the foreign commits in THE SAME TREE the finalize then runs in, which is the
    in-place / hand-finalize shape that actually misfires. The isolated-lane shape is already correct
    and is pinned separately in ``tests/test_finalize_isolated_commit.py``.
    """

    def test_committed_path_inside_scope_paths_behaves_exactly_as_today(self):
        """CASE 1 of 3. A declared path is in scope whether committed or not; nothing changed here."""
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()

        audit = self._audit(plan)
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertEqual(audit["disregarded_unowned_paths"], [])
        self.assertTrue(audit["in_scope"])
        self.assertEqual(
            sorted(audit["committed_paths"])[:2],
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )
        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )

    def test_committed_out_of_scope_path_in_a_foreign_commit_is_excluded_and_recorded(
        self,
    ):
        """CASE 2 of 3. Another actor's commit, in THIS tree, touching no declared path.

        This is the defect: before the fix the path landed in the unfiltered committed half and
        demanded a reason this plan could not honestly give.
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        # Another actor commits two unrelated files together, in the SAME tree.
        for name in ("agent_workflows/theirs_a.py", "agent_workflows/theirs_b.py"):
            (self.root / name).write_text("theirs\n", encoding="utf-8")
        _commit_paths(
            self.root,
            "another actor's unrelated commit",
            ["agent_workflows/theirs_a.py", "agent_workflows/theirs_b.py"],
        )

        code, msg, evidence, _f = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_OK, msg)
        audit = evidence["scope_audit"]

        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertEqual(
            audit["disregarded_unowned_paths"],
            ["agent_workflows/theirs_a.py", "agent_workflows/theirs_b.py"],
        )
        # Recorded in the ONE existing channel, and surfaced to the human.
        self.assertIn("agent_workflows/theirs_a.py", msg)
        self.assertIn("not owned by this execution", msg)
        # The message substantiates nothing it cannot: no sha, no actor named.
        self.assertNotIn("committed by", msg)
        self.assertNotIn("\u2014", msg)
        self.assertNotIn("\u2013", msg)
        # They ARE in the committed half, so the exclusion was a filter decision, not a collection gap.
        for name in ("agent_workflows/theirs_a.py", "agent_workflows/theirs_b.py"):
            self.assertIn(name, audit["committed_paths"])

    def test_intervening_signal_still_fires_for_an_in_scope_path_another_actor_touched(
        self,
    ):
        """CASE 3 of 3. The collision signal is a DIFFERENT fact and must survive untouched.

        Another actor editing a path this plan DECLARED is worth surfacing, so it must not be
        laundered away by the ownership filter.
        """
        plan = self._plan()
        self._begin(plan)
        # Another actor commits INTO this plan's declared territory, before the plan's own work.
        (self.root / "tests/test_demo.py").write_text("theirs\n", encoding="utf-8")
        _commit_paths(
            self.root,
            "another actor touches declared territory",
            ["tests/test_demo.py"],
        )
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(self.root, "the plan's own work", ["agent_workflows/demo.py"])

        audit = self._audit(plan)
        self.assertIn("tests/test_demo.py", audit["intervening_in_scope_commits"])
        self.assertIn("agent_workflows/demo.py", audit["intervening_in_scope_commits"])
        # A declared path is in scope, so it is neither out-of-scope nor disregarded.
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertEqual(audit["disregarded_unowned_paths"], [])

    def test_FAIL_CLOSED_an_unattributable_committed_path_still_demands_a_reason(self):
        """THE FAIL-CLOSED DIRECTION, which is the assertion that matters most.

        This change makes a demanding gate demand LESS, which is the direction in which a mistake
        becomes invisible, so the class of committed path that STILL refuses must be demonstrated
        rather than assumed. That class is a path COHESIVE with this execution's work: it rides in a
        commit that also touched a declared path, so the same atomic act produced both, and it is
        therefore this execution's to justify.

        The implementation does admit such a case, so this is a real refusal and not a constructed
        one; had it not, E-04 required reporting a whole-class exclusion as a finding instead.
        """
        plan = self._plan()
        self._begin(plan)
        # ONE commit containing a declared path AND an out-of-scope path: the executor's own
        # out-of-scope edit, committed alongside its real work.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "tests/test_demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(
            "mine, out of scope\n", encoding="utf-8"
        )
        _commit_paths(
            self.root,
            "own work plus an out-of-scope path in ONE commit",
            ["agent_workflows/demo.py", "tests/test_demo.py", "CHANGELOG.md"],
        )

        audit = self._audit(plan)
        self.assertEqual(
            audit["out_of_scope_paths"],
            ["CHANGELOG.md"],
            "a cohesive out-of-scope commit must STILL demand a reason",
        )
        self.assertEqual(audit["disregarded_unowned_paths"], [])

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("--scope-reason", result.message)
        self.assertTrue(any("CHANGELOG.md" in f for f in result.findings))
        self.assertTrue(plan.is_file(), "plan must be left unmoved")

        # A supplied reason still legitimizes it, recorded verbatim: the gate is RESCOPED, not removed.
        ok = LC.finalize(
            self.root,
            plan,
            ACTOR,
            "did the work",
            apply=True,
            scope_reasons={"CHANGELOG.md": "release note for this change"},
        )
        self.assertEqual(ok.exit_code, LC.EXIT_OK, f"{ok.message} / {ok.findings}")
        moved = self._executed_path(plan).read_text(encoding="utf-8")
        self.assertIn("out-of-scope CHANGELOG.md", moved)
        self.assertIn("release note for this change", moved)


class MeasuredIncidentRegressionTests(_ScopeOwnershipBase):
    """The 2026-09-07 `mm6wuz` incident, reproduced in its REAL shape (scopeattr `h9cn0y` E-04).

    Finalizing `mm6wuz` demanded TEN ``--scope-reason`` entries of which only TWO were that plan's
    (``CHANGELOG.md`` and ``tests/test_runner_stop_level3.py``, both committed ALONGSIDE its declared
    files). The other eight came from four unrelated commits by other agents.

    The shape matters and is reproduced faithfully: the incident was a HAND finalize from the MAIN
    checkout (the run never earned integration, so the runner's own finalize never ran), which is why
    the foreign commits were in the very tree the finalize computed its diff in. The fixture therefore
    commits the foreign work in the SAME tree, not in a peer worktree.
    """

    SCOPE_8 = (
        "agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, "
        "tests/test_render_stream.py, tests/test_oc_runipd_cli.py"
    )

    def _incident_repo(self):
        """Build the incident: the plan's own commit, then four foreign commits, one tree."""
        plan = self._plan(scope_paths=self.SCOPE_8, plan_id="mmw001")
        self._begin(plan)
        # (1) THE PLAN'S OWN COMMIT: four declared files plus its two genuine out-of-scope paths.
        own = [
            "agent_workflows/render_stream.py",
            "agent_workflows/oc_runipd.py",
            "tests/test_render_stream.py",
            "tests/test_oc_runipd_cli.py",
            "CHANGELOG.md",
            "tests/test_runner_stop_level3.py",
        ]
        for name in own:
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text("mine\n", encoding="utf-8")
        _commit_paths(self.root, "the plan's own work", own)
        # (2) FOUR FOREIGN COMMITS, none touching a declared path, in the SAME tree.
        foreign = {
            "attention": [
                "agent_workflows/attention.py",
                "tests/test_next_ordering.py",
            ],
            "isolated-commit": [
                "agent_workflows/commit_lock.py",
                "agent_workflows/git_commit_helper.py",
                "tests/test_commit_lock.py",
                "tests/test_isolated_commit.py",
            ],
            "lifecycle": [
                "agent_workflows/ipd_lifecycle.py",
                "tests/test_finalize_isolated_commit.py",
            ],
        }
        for subject, names in foreign.items():
            for name in names:
                (self.root / name).parent.mkdir(parents=True, exist_ok=True)
                (self.root / name).write_text("another agent\n", encoding="utf-8")
            _commit_paths(self.root, f"another agent: {subject}", names)
        return plan

    def test_the_incident_now_demands_TWO_reasons_not_TEN(self):
        """THE REGRESSION ASSERTION: exactly the two paths that were genuinely this plan's."""
        plan = self._incident_repo()

        audit = self._audit(plan)

        self.assertEqual(
            sorted(audit["out_of_scope_paths"]),
            ["CHANGELOG.md", "tests/test_runner_stop_level3.py"],
            "only the plan's OWN out-of-scope paths may demand a reason",
        )
        self.assertEqual(len(audit["out_of_scope_paths"]), 2)
        # The eight foreign paths are excluded, and visibly so.
        self.assertEqual(len(audit["disregarded_unowned_paths"]), 8)
        for name in (
            "agent_workflows/attention.py",
            "agent_workflows/commit_lock.py",
            "agent_workflows/ipd_lifecycle.py",
            "agent_workflows/git_commit_helper.py",
        ):
            self.assertIn(name, audit["disregarded_unowned_paths"])

    def test_the_same_fixture_demanded_TEN_reasons_under_the_PRE_FIX_rule(self):
        """THE CONTRAST, computed against the PRE-FIX rule on the SAME repository state.

        Without this, the fixture above would pass even if the filter were inverted, because a
        one-sided assertion cannot show that anything improved. The pre-fix rule is re-applied here
        exactly as it stood: EVERY committed path outside Scope-Paths demanded a reason, with only the
        working-tree half ownership-filtered.
        """
        plan = self._incident_repo()
        receipt = LC.read_receipt(self.root, "mmw001")
        assert receipt is not None
        base = str(receipt["base_head"])
        scope_paths = list(receipt["scope_paths"])
        plan_rel = str(plan.relative_to(self.root))

        sources = LC._changed_path_sources(self.root, base)
        committed_set = set(sources.committed)
        pre_fix_out_of_scope = []
        for p in sources.union():
            if LC._is_implicitly_allowed(p, plan_rel):
                continue
            if any(LC._scope_match(p, pat) for pat in scope_paths):
                continue
            if p not in committed_set and not LC._working_tree_path_is_owned(
                p,
                scope_paths=scope_paths,
                committed=sources.committed,
                plan_rel=plan_rel,
            ):
                continue
            pre_fix_out_of_scope.append(p)

        self.assertEqual(
            len(pre_fix_out_of_scope),
            10,
            f"the pre-fix rule should demand TEN reasons here; got {sorted(pre_fix_out_of_scope)}",
        )
        # And the post-fix audit on the SAME state demands two: 10 -> 2, demonstrated not asserted.
        self.assertEqual(len(self._audit(plan)["out_of_scope_paths"]), 2)

    def test_the_incident_plan_now_finalizes_with_its_own_two_reasons_alone(self):
        """END TO END: the plan reaches executed/ giving reasons ONLY for its own two paths.

        And its permanent record therefore contains no claim about a file it never touched, which is
        the record-corruption this plan exists to stop.
        """
        plan = self._incident_repo()

        result = LC.finalize(
            self.root,
            plan,
            ACTOR,
            "structured live event stream",
            apply=True,
            scope_reasons={
                "CHANGELOG.md": "release note for this change",
                "tests/test_runner_stop_level3.py": "stop-trigger coverage moved with the stream",
            },
        )

        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        moved = self._executed_path(plan).read_text(encoding="utf-8")
        self.assertIn("out-of-scope CHANGELOG.md", moved)
        # THE RECORD IS CLEAN: no reason was written for another agent's file.
        for foreign in (
            "out-of-scope agent_workflows/attention.py",
            "out-of-scope agent_workflows/commit_lock.py",
            "out-of-scope agent_workflows/ipd_lifecycle.py",
        ):
            self.assertNotIn(foreign, moved)


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


class NothingElseMovedTests(_ScopeOwnershipBase):
    """scopeattr `h9cn0y` E-05: the surfaces this gate shares must be provably unaffected.

    The committed-half filter is applied at the SPLIT, never to the union-returning surface, precisely
    so the readers of that union do not change behavior as a side effect. These tests assert that
    rather than trusting the code comment.
    """

    def test_check_scope_drift_still_sees_the_broad_time_window(self):
        """``check_engine.check_scope_drift`` must be UNAFFECTED: it wants the time window.

        It consumes ``_paths_changed_by_this_execution`` (the union), which is deliberately NOT
        ownership-filtered. So a foreign committed path that finalize now DISREGARDS must still be
        reported as drift here. This is the compatibility constraint the union surface exists for; if
        a future change ownership-filters the union, this test is what catches it.
        """
        from agent_workflows import check_engine as CE

        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        (self.root / "agent_workflows/theirs.py").write_text(
            "theirs\n", encoding="utf-8"
        )
        _commit_paths(self.root, "another actor", ["agent_workflows/theirs.py"])

        # finalize DISREGARDS it (the new behavior)...
        audit = self._audit(plan)
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertIn("agent_workflows/theirs.py", audit["disregarded_unowned_paths"])

        # ...while the union surface still CONTAINS it, unchanged in shape and value.
        receipt = LC.read_receipt(self.root, "abc123")
        assert receipt is not None
        union = LC._paths_changed_by_this_execution(
            self.root, str(receipt["base_head"])
        )
        self.assertIn("agent_workflows/theirs.py", union)
        sources = LC._changed_path_sources(self.root, str(receipt["base_head"]))
        self.assertEqual(union, sources.union())

        # And the drift rule that reads it still flags the path.
        drift = CE.check_scope_drift(self.root)
        self.assertTrue(
            any("agent_workflows/theirs.py" in str(d.detail) for d in drift),
            f"check_scope_drift must still flag the broad window; got {[d.detail for d in drift]}",
        )

    def test_the_in_scope_unmodified_scope_ack_direction_is_untouched(self):
        """The MISSING-work direction still fires and still needs an ack. Not relaxed."""
        plan = self._plan("agent_workflows/demo.py, tests/test_demo.py, tests/never.py")
        self._begin(plan)
        self._do_in_scope_work_and_commit()

        audit = self._audit(plan)
        self.assertEqual(audit["in_scope_unmodified"], ["tests/never.py"])

        refused = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(refused.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("--scope-ack", refused.message)
        self.assertTrue(plan.is_file())

        ok = LC.finalize(
            self.root,
            plan,
            ACTOR,
            "did the work",
            apply=True,
            scope_acks={"tests/never.py": "not-needed"},
        )
        self.assertEqual(ok.exit_code, LC.EXIT_OK, f"{ok.message} / {ok.findings}")

    def test_a_clean_finalize_still_completes_without_prompting(self):
        """Zero out-of-scope, zero unmodified, nothing disregarded: silent success, no message noise."""
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()

        code, msg, evidence, _f = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_OK, msg)
        audit = evidence["scope_audit"]
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertEqual(audit["disregarded_unowned_paths"], [])
        self.assertNotIn("Disregarded", msg)

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(self._executed_path(plan).is_file())

    def test_cohesion_uses_no_run_record_and_no_authorship_lookup(self):
        """The two retired approaches must be ABSENT from the code, not merely unused.

        F-13 forbids a run-record dependency in the lifecycle gate (gitignored, absent from a lane,
        and finalize gets no run id) and F-14 forbids an authorship lookup (it cannot partition actors
        here). Asserted by reading the source, because absence of a mechanism is not observable
        behaviorally.

        DOCSTRINGS AND COMMENTS ARE STRIPPED FIRST, deliberately: those functions DISCUSS the retired
        approaches at length (that prose is required by the plan's spec-sync section, so a future
        reader does not re-derive them), and a naive substring search would match the explanation
        rather than a use. Only executable code is searched.
        """
        import ast
        import inspect

        def _executable_source(fn) -> str:
            """The function's code with comments and docstrings removed."""
            tree = ast.parse(inspect.cleandoc(inspect.getsource(fn)))
            for node in ast.walk(tree):
                # Drop every docstring (module, class, function) by deleting the leading Expr-of-Str.
                body = getattr(node, "body", None)
                if (
                    isinstance(body, list)
                    and body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    body.pop(0)
            # ast.unparse never emits comments, so the result is code only.
            return ast.unparse(tree)

        for fn in (
            LC._execution_cohesive_committed_paths,
            LC._working_tree_path_is_owned,
            LC.finalize_precheck,
        ):
            src = _executable_source(fn)
            for forbidden in (
                ".aw/records/runs",
                "last_outcome",
                "%an",
                "%ae",
                "--author",
                "isolated_baseline",
            ):
                self.assertNotIn(
                    forbidden,
                    src,
                    f"{fn.__name__} must not use {forbidden!r} as attribution evidence",
                )

    def test_cohesion_reports_UNANCHORED_rather_than_an_empty_set(self):
        """THE FAIL-CLOSED SWITCH, and the reason the helper returns a pair rather than a set.

        "No cohesive paths" and "cohesion knows nothing" are different states that a bare set cannot
        tell apart, and conflating them INVERTS the gate: an empty set reads as "nothing is owned",
        which would excuse every committed path on no evidence at all.

        MEASURED during execution: with the switch absent, the pre-existing
        ``FinalizeTests::test_p7dqwz_counterexample_refuses_out_of_scope_path`` began to FAIL, because
        a plan whose ONLY commit was out-of-scope had no anchored commit and so was excused. That is
        precisely the case the gate exists for, which is why this test guards the distinction.
        """
        plan = self._plan()
        self._begin(plan)
        self._do_in_scope_work_and_commit()
        receipt = LC.read_receipt(self.root, "abc123")
        assert receipt is not None
        base = str(receipt["base_head"])

        # No fence at all (grandfathered): unanchored, so the caller must not filter.
        no_fence = LC._execution_cohesive_committed_paths(self.root, base, [])
        self.assertFalse(no_fence.anchored)
        self.assertEqual(no_fence.paths, frozenset())

        # A git failure must not read as "nothing is owned" either.
        bad_base = LC._execution_cohesive_committed_paths(
            self.root, "0000000000000000000000000000000000000000", ["agent_workflows/"]
        )
        self.assertFalse(bad_base.anchored)
        self.assertEqual(bad_base.paths, frozenset())

        # A real footprint IS anchored, so the two states are genuinely distinguished.
        real = LC._execution_cohesive_committed_paths(
            self.root, base, list(receipt["scope_paths"])
        )
        self.assertTrue(real.anchored)
        self.assertIn("agent_workflows/demo.py", real.paths)

    def test_an_unanchored_execution_still_demands_a_reason(self):
        """The behavioral half of the switch: no footprint means the gate behaves as before.

        A plan that committed ONLY out-of-scope work (the `p7dqwz` counterexample's shape) has no
        anchored commit, so cohesion cannot disclaim anything and the reason requirement still fires.
        """
        plan = self._plan("agent_workflows/demo.py")
        self._begin(plan)
        (self.root / "tests/test_empty_state_ux.py").write_text("x\n", encoding="utf-8")
        _commit_paths(self.root, "out-of-scope only", ["tests/test_empty_state_ux.py"])

        audit = self._audit(plan)
        self.assertEqual(audit["out_of_scope_paths"], ["tests/test_empty_state_ux.py"])
        self.assertEqual(audit["disregarded_unowned_paths"], [])

        result = LC.finalize(self.root, plan, ACTOR, "did the work", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any("tests/test_empty_state_ux.py" in f for f in result.findings),
            result.findings,
        )

    def test_cohesion_groups_paths_by_commit_not_by_position(self):
        """The helper's grouping is per COMMIT, so anchoring does not leak across commits."""
        plan = self._plan()
        self._begin(plan)
        # Commit A: anchored (declared path) plus a rider.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "rider.md").write_text("rider\n", encoding="utf-8")
        _commit_paths(
            self.root, "anchored commit", ["agent_workflows/demo.py", "rider.md"]
        )
        # Commit B: unanchored, entirely foreign.
        (self.root / "agent_workflows/theirs.py").write_text(
            "theirs\n", encoding="utf-8"
        )
        _commit_paths(self.root, "foreign commit", ["agent_workflows/theirs.py"])

        receipt = LC.read_receipt(self.root, "abc123")
        assert receipt is not None
        cohesive = LC._execution_cohesive_committed_paths(
            self.root, str(receipt["base_head"]), list(receipt["scope_paths"])
        )

        self.assertTrue(cohesive.anchored)
        self.assertIn(
            "rider.md", cohesive.paths, "a rider in an anchored commit is cohesive"
        )
        self.assertIn("agent_workflows/demo.py", cohesive.paths)
        self.assertNotIn(
            "agent_workflows/theirs.py",
            cohesive.paths,
            "anchoring must not leak into a separate, unanchored commit",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

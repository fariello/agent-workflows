"""Restored behavioral tests for agent_workflows/ipd_lifecycle.py begin, _baseline_ambiguity,
_execution_cohesive_committed_paths, and finalize_precheck.

Restores core-tier behavioral coverage for four production keys recorded in backlog item gcpj15
and IPD 2qlg0w, whose control files were deleted at 19313eed^:
- tests/test_begin_dirty_gate_scope.py
- tests/test_finalize_exact_attribution.py
- tests/test_finalize_scope_ownership.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import ipd_lifecycle as LC
from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _completed_plan_text,
    _init_git,
    _ready_plan_text,
    _write_plan,
)

pytestmark = pytest.mark.core

IN_SCOPE = "agent_workflows/demo.py"
ACTOR = "opencode/test"
SCOPE = "agent_workflows/demo.py, tests/test_demo.py"


def _git(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def _git_out(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def _so_commit_paths(root: Path, message: str, paths: list[str]) -> None:
    """Path-scoped commit, mirroring the execution contract (never ``git add -A``)."""
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message, "--", *paths], cwd=root, check=True
    )


def _ea_commit_paths(root: Path, message: str, paths: list[str]) -> str:
    """Path-scoped commit, mirroring the execution contract (never ``git add -A``). Returns the sha."""
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message, "--", *paths], cwd=root, check=True
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class _Fixture(unittest.TestCase):
    """A conforming, committed, APPROVED plan in a throwaway git repo (clean baseline)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        _init_git(self.root)
        self.plan = _write_plan(
            self.root,
            _ready_plan_text(
                plan_id="abc123", scope_paths=f"{IN_SCOPE}, tests/test_demo.py"
            ),
            "20260829-demo-01-abc123-demo.ipd.md",
        )
        (self.root / "agent_workflows").mkdir(parents=True, exist_ok=True)
        (self.root / IN_SCOPE).write_text("committed = True\n", encoding="utf-8")
        _commit_all(self.root, "base")
        self.addCleanup(self._tmp.cleanup)

    def _dirty_in_scope(self) -> None:
        """Simulate a CO-WORKER's uncommitted edit to a commonly-scoped file in the main tree."""
        (self.root / IN_SCOPE).write_text(
            "someone_elses_wip = True\n", encoding="utf-8"
        )

    def _begin(self, *, isolated: bool) -> LC.BeginResult:
        return LC.begin(
            self.root,
            self.plan,
            "opencode/test",
            timestamp="2026-08-30T00:00:00Z",
            isolated_baseline=isolated,
        )


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
        _so_commit_paths(
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


class _ExactAttributionBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        LC.clear_checkout_control_root_cache()

    def tearDown(self) -> None:
        LC.clear_checkout_control_root_cache()
        self._tmp.cleanup()

    def _plan(self, scope_paths: str = SCOPE, plan_id: str = "abc123") -> Path:
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths=scope_paths),
            f"20260914-demo-01-{plan_id}-demo.ipd.md",
        )
        _commit_all(self.root, f"add plan {plan_id}")
        return plan

    def _begin(self, plan: Path):
        res = LC.begin(self.root, plan, ACTOR, timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        return res

    def _write_run_record(
        self,
        plan_id: str,
        shas: list[str],
        *,
        position: int = 2,
        run: str = "run-20260914T000000Z-1",
    ) -> Path:
        """Write a minimal run outcome record of the shape both drivers actually emit."""
        outcomes = self.root / ".aw" / "records" / "runs" / run / "outcomes"
        outcomes.mkdir(parents=True, exist_ok=True)
        path = outcomes / f"{position:02d}-{plan_id}.json"
        path.write_text(
            json.dumps({"id6": plan_id, "commits": [{"sha": s} for s in shas]}),
            encoding="utf-8",
        )
        return path

    def _audit_out_of_scope(self, plan: Path) -> list[str]:
        code, msg, evidence, _f = LC.finalize_precheck(self.root, plan)
        self.assertEqual(code, LC.EXIT_OK, msg)
        return sorted(evidence["scope_audit"]["out_of_scope_paths"])

    def _attribution_source(self, plan: Path) -> str:
        _code, _msg, evidence, _f = LC.finalize_precheck(self.root, plan)
        return str(evidence.get("attribution_source") or "")


# ======================================================================================
# begin behavioral tests (from tests/test_begin_dirty_gate_scope.py)
# ======================================================================================


class IsolatedBaselineGrantsAuthorityTests(_Fixture):
    def test_the_same_dirt_still_refuses_a_non_isolated_turn(self) -> None:
        # The SAME repository state, differing only in where the turn will run. This pairing is what
        # makes (a) a rescope rather than a removal.
        self._dirty_in_scope()
        self.assertEqual(self._begin(isolated=False).exit_code, LC.EXIT_CANNOT_RUN)
        self.assertEqual(self._begin(isolated=True).exit_code, LC.EXIT_OK)


class NonIsolatedRefusalIsUnchangedTests(_Fixture):
    def test_refusal_names_the_measured_baseline(self) -> None:
        self._dirty_in_scope()
        msg = self._begin(isolated=False).message
        # (d): the operator must be able to tell WHICH baseline produced the refusal.
        self.assertIn("Measured baseline:", msg)
        self.assertIn(str(self.root), msg)


# ======================================================================================
# _baseline_ambiguity behavioral tests (from tests/test_begin_dirty_gate_scope.py)
# ======================================================================================


class IsolatedBaselineStillFailsClosedTests(_Fixture):
    def test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo(self) -> None:
        # Directly pin the fail-closed vocabulary of the predicate both baselines share, in BOTH
        # modes, so neither can silently start reporting "clean" for a tree git cannot speak for.
        with tempfile.TemporaryDirectory() as td:
            not_a_repo = Path(td).resolve()
            for isolated in (False, True):
                self.assertEqual(
                    LC._baseline_ambiguity(
                        not_a_repo, [IN_SCOPE], isolated_baseline=isolated
                    ),
                    "unversioned",
                    f"isolated_baseline={isolated} must fail closed outside a git repo",
                )

    def test_unreadable_base_commit_is_still_refused_when_isolated(self) -> None:
        # A repo with no commit has no frozen base to cut a lane from, so the baseline IS ambiguous
        # and must still fail closed. If the isolated branch simply returned "clean", this passes
        # vacuously and the fail-closed posture would be gone.
        with tempfile.TemporaryDirectory() as td:
            fresh = Path(td).resolve()
            _init_git(fresh)
            plan = _write_plan(
                fresh,
                _ready_plan_text(plan_id="abc123", scope_paths=IN_SCOPE),
                "20260829-demo-01-abc123-demo.ipd.md",
            )
            result = LC.begin(
                fresh, plan, "opencode/test", timestamp="t", isolated_baseline=True
            )
            self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
            self.assertFalse(LC.receipt_path_for(fresh, "abc123").is_file())


# ======================================================================================
# _execution_cohesive_committed_paths behavioral tests (from tests/test_finalize_scope_ownership.py)
# ======================================================================================


class NothingElseMovedTests(_ScopeOwnershipBase):
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

    def test_cohesion_groups_paths_by_commit_not_by_position(self):
        """The helper's grouping is per COMMIT, so anchoring does not leak across commits."""
        plan = self._plan()
        self._begin(plan)
        # Commit A: anchored (declared path) plus a rider.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "rider.md").write_text("rider\n", encoding="utf-8")
        _so_commit_paths(
            self.root, "anchored commit", ["agent_workflows/demo.py", "rider.md"]
        )
        # Commit B: unanchored, entirely foreign.
        (self.root / "agent_workflows/theirs.py").write_text(
            "theirs\n", encoding="utf-8"
        )
        _so_commit_paths(self.root, "foreign commit", ["agent_workflows/theirs.py"])

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


# ======================================================================================
# finalize_precheck behavioral tests (from tests/test_finalize_exact_attribution.py)
# ======================================================================================


class FallBackWhenAbsentTests(_ExactAttributionBase):
    """Required test 2: with no run corpus, behavior is IDENTICAL to the cohesion-only result."""

    def test_no_corpus_reproduces_the_cohesion_result_exactly(self):
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        _ea_commit_paths(
            self.root, "work", ["agent_workflows/demo.py", "agent_workflows/extra.py"]
        )

        self.assertFalse((self.root / ".aw" / "records" / "runs").exists())
        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(exact.anchored)
        self.assertEqual(set(exact.paths), set())

        cohesion = LC._execution_cohesive_committed_paths(
            self.root, base, ["agent_workflows/demo.py", "tests/test_demo.py"]
        )
        self.assertTrue(cohesion.anchored)
        # The audit's demand set is the cohesion-derived one, byte for byte.
        self.assertIn("agent_workflows/extra.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "commit-cohesion")


class ExactSourceWinsTests(_ExactAttributionBase):
    """Required test 1: the exact source excludes a CO-WORKER's commit that cohesion would attribute."""

    def test_the_plans_own_out_of_scope_path_is_still_demanded(self):
        """NON-VACUITY of the fix itself: it must not become a blanket excuse.

        The exact source names this plan's commit, and that commit contains an out-of-scope path, so a
        reason IS still required. A fix that merely stopped demanding things would pass the test above
        and fail this one.
        """
        plan = self._plan()
        self._begin(plan)
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text(
            "mine too\n", encoding="utf-8"
        )
        mine = _ea_commit_paths(
            self.root,
            "my work, including an undeclared path",
            ["agent_workflows/demo.py", "agent_workflows/extra.py"],
        )
        self._write_run_record("abc123", [mine])

        self.assertIn("agent_workflows/extra.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "run-record-exact")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

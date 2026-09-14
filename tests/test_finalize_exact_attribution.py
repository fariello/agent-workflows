"""Finalize attributes its COMMITTED half by the run record's exact SHAs (`gys47u` E-04/E-05).

WHY THIS SUITE EXISTS, measured 2026-09-14. Ten lanes stranded overnight by an unrelated red test
were recovered into `main` in one pass. Finalizing `8tgg6g` then demanded ~19 `--scope-reason`
answers, because five non-merge commits in range touched the shared hot file
`agent_workflows/runner_shared.py` and FOUR of them belonged to other plans. Answering would have
written into `8tgg6g`'s permanent finalize record a claim that it edited `cli.py` and `run_viewer.py`,
which it never touched. `_run_record_committed_paths` reduces that case to the three paths genuinely
its own.

THE PROPERTY UNDER TEST is a two-tier ownership source: EXACT (the run record's own SHAs) when
available, COHESION (the pre-existing commit-boundary heuristic) otherwise, with every fail-closed arm
of the old behavior preserved. The fail-closed cases below are the highest-value ones, because a
weakened gate here does not fail loudly; it silently stops demanding a reason it should demand.

Stdlib unittest on throwaway git repos, reusing the proven fixture helpers from
``tests.test_ipd_lifecycle_cli`` and the path-scoped commit helper shape from
``tests.test_finalize_scope_ownership`` (neither module is edited by this plan).
"""

from __future__ import annotations

import json
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


def _commit_paths(root: Path, message: str, paths: list[str]) -> str:
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


class ExactSourceWinsTests(_ExactAttributionBase):
    """Required test 1: the exact source excludes a CO-WORKER's commit that cohesion would attribute."""

    def test_a_coworkers_commit_touching_a_declared_path_is_not_demanded(self):
        """THE MEASURED INCIDENT, reduced to a fixture.

        A concurrent agent commits its own file TOGETHER WITH one of this plan's declared paths, which
        is exactly what a shared hot file like `runner_shared.py` produces. Cohesion attributes the
        whole commit to this plan; the run record knows better.
        """
        plan = self._plan()
        self._begin(plan)
        # This plan's OWN work, committed path-scoped.
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        mine = _commit_paths(
            self.root, "my own in-scope work", ["agent_workflows/demo.py"]
        )
        # A co-worker's commit that ALSO touches a declared path (the hot-file case).
        (self.root / "agent_workflows/demo.py").write_text("theirs\n", encoding="utf-8")
        (self.root / "agent_workflows/coworker.py").write_text(
            "theirs\n", encoding="utf-8"
        )
        _commit_paths(
            self.root,
            "a co-worker's commit that also touches my declared path",
            ["agent_workflows/demo.py", "agent_workflows/coworker.py"],
        )

        # WITHOUT a run record, cohesion demands the co-worker's file: the false DEMAND.
        self.assertIn("agent_workflows/coworker.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "commit-cohesion")

        # WITH the run record naming only this plan's own sha, it is not demanded.
        self._write_run_record("abc123", [mine])
        self.assertNotIn("agent_workflows/coworker.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "run-record-exact")

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
        mine = _commit_paths(
            self.root,
            "my work, including an undeclared path",
            ["agent_workflows/demo.py", "agent_workflows/extra.py"],
        )
        self._write_run_record("abc123", [mine])

        self.assertIn("agent_workflows/extra.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "run-record-exact")


class FallBackWhenAbsentTests(_ExactAttributionBase):
    """Required test 2: with no run corpus, behavior is IDENTICAL to the cohesion-only result."""

    def test_no_corpus_reproduces_the_cohesion_result_exactly(self):
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(
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


class FailClosedTests(_ExactAttributionBase):
    """Required tests 3, 4, 5: every arm that must NOT excuse a path on absent evidence."""

    def test_a_plan_whose_only_commit_is_out_of_scope_is_still_refused(self):
        """Required test 3, the `p7dqwz` counterexample the `anchored` switch protects.

        No commit touches a declared path, so cohesion is unanchored and there is no run record. The
        committed out-of-scope path must still be demanded rather than excused.
        """
        plan = self._plan()
        self._begin(plan)
        (self.root / "agent_workflows/only_extra.py").write_text(
            "x\n", encoding="utf-8"
        )
        _commit_paths(self.root, "out-of-scope only", ["agent_workflows/only_extra.py"])

        self.assertIn("agent_workflows/only_extra.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "none-fail-closed")

    def test_a_run_record_naming_zero_commits_falls_through_to_cohesion(self):
        """Required test 4. An empty `commits[]` must not read as 'this plan owns nothing'."""
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(
            self.root, "work", ["agent_workflows/demo.py", "agent_workflows/extra.py"]
        )
        self._write_run_record("abc123", [])

        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(exact.anchored, "an empty commits[] must not anchor")
        self.assertIn("agent_workflows/extra.py", self._audit_out_of_scope(plan))
        self.assertEqual(self._attribution_source(plan), "commit-cohesion")

    def test_a_malformed_run_record_falls_through_instead_of_raising(self):
        """A corrupt record is a MISSING source, never a crash inside a lifecycle gate."""
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(self.root, "work", ["agent_workflows/demo.py"])
        outcomes = self.root / ".aw" / "records" / "runs" / "run-x" / "outcomes"
        outcomes.mkdir(parents=True)
        (outcomes / "02-abc123.json").write_text("{not json", encoding="utf-8")

        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(exact.anchored)
        self.assertEqual(self._attribution_source(plan), "commit-cohesion")

    def test_a_sha_that_is_not_an_ancestor_of_head_contributes_nothing(self):
        """Required test 5 (finding F-7). An abandoned lane attempt must not launder a path.

        MEASURED: `mm5p3v` recorded SEVEN shas across two attempts, and `r2i1b1`/`fn2l1u` recorded
        shas from an attempt whose branch was never merged. Without this filter a record could name a
        commit that never landed and its paths would be treated as owned.
        """
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(self.root, "landed work", ["agent_workflows/demo.py"])
        # An abandoned attempt on a side branch, never merged.
        subprocess.run(
            ["git", "checkout", "-q", "-b", "abandoned"], cwd=self.root, check=True
        )
        (self.root / "agent_workflows/never_landed.py").write_text(
            "x\n", encoding="utf-8"
        )
        orphan = _commit_paths(
            self.root, "abandoned attempt", ["agent_workflows/never_landed.py"]
        )
        subprocess.run(["git", "checkout", "-q", "-"], cwd=self.root, check=True)

        self._write_run_record("abc123", [orphan])
        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(
            exact.anchored, "a non-ancestor sha must not anchor attribution"
        )
        self.assertNotIn("agent_workflows/never_landed.py", set(exact.paths))

    def test_a_sha_predating_the_frozen_base_contributes_nothing(self):
        """The window filter. Attribution answers a question about THIS execution's range only."""
        plan = self._plan()
        # A commit BEFORE begin freezes the base.
        (self.root / "agent_workflows/older.py").write_text("old\n", encoding="utf-8")
        older = _commit_paths(self.root, "pre-base work", ["agent_workflows/older.py"])
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(self.root, "in-window work", ["agent_workflows/demo.py"])

        self._write_run_record("abc123", [older])
        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(
            exact.anchored, "a pre-base sha is not in this execution's window"
        )
        self.assertNotIn("agent_workflows/older.py", set(exact.paths))

    def test_a_record_for_a_different_id6_is_ignored(self):
        """Attribution must key on THIS plan, not on any record that happens to exist."""
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        other = _commit_paths(self.root, "work", ["agent_workflows/demo.py"])
        self._write_run_record("zzz999", [other], position=3)

        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertFalse(exact.anchored)


class RecordShapeToleranceTests(_ExactAttributionBase):
    """Both `commits[]` element shapes in the shipped corpus must be read (measured 2026-09-14)."""

    def test_a_bare_string_sha_is_read_like_a_mapping(self):
        plan = self._plan()
        res = self._begin(plan)
        base = res.receipt["base_head"]
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        sha = _commit_paths(
            self.root, "work", ["agent_workflows/demo.py", "agent_workflows/extra.py"]
        )
        outcomes = self.root / ".aw" / "records" / "runs" / "run-s" / "outcomes"
        outcomes.mkdir(parents=True)
        # The "<sha> <subject>" spelling the corpus also contains.
        (outcomes / "02-abc123.json").write_text(
            json.dumps({"id6": "abc123", "commits": [f"{sha} did the work"]}),
            encoding="utf-8",
        )

        exact = LC._run_record_committed_paths(self.root, "abc123", base)
        self.assertTrue(exact.anchored, "a bare-string sha must anchor")
        self.assertIn("agent_workflows/extra.py", set(exact.paths))


class AttributionSourceIsReportedTests(_ExactAttributionBase):
    """`gys47u` E-03: the deciding source is reported, and the cohesion case carries its warning."""

    def test_the_refusal_names_cohesion_and_warns_it_is_heuristic(self):
        plan = self._plan()
        self._begin(plan)
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        _commit_paths(
            self.root, "work", ["agent_workflows/demo.py", "agent_workflows/extra.py"]
        )

        result = LC.finalize(self.root, plan, ACTOR, "msg", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("attribution: commit-cohesion", result.message)
        self.assertIn("MAY belong to a concurrent agent", result.message)
        self.assertEqual(result.evidence.get("attribution_source"), "commit-cohesion")

    def test_the_exact_case_reports_the_exact_source(self):
        plan = self._plan()
        self._begin(plan)
        (self.root / "agent_workflows/demo.py").write_text("mine\n", encoding="utf-8")
        (self.root / "agent_workflows/extra.py").write_text("mine\n", encoding="utf-8")
        sha = _commit_paths(
            self.root, "work", ["agent_workflows/demo.py", "agent_workflows/extra.py"]
        )
        self._write_run_record("abc123", [sha])

        result = LC.finalize(self.root, plan, ACTOR, "msg", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("attribution: run-record-exact", result.message)
        self.assertEqual(result.evidence.get("attribution_source"), "run-record-exact")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

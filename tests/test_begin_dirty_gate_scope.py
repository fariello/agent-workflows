"""`aw ipd begin` measures the baseline the turn will ACTUALLY execute against (lanetruth-02, z2isfg).

The in-scope-dirty gate exists so a plan's frozen base is unambiguous. For a NON-isolated turn the
main working tree genuinely IS the execution tree, so its in-scope uncommitted state is real ambiguity
and must keep being refused. For an ISOLATED turn the work happens in a fresh worktree cut at the
frozen base commit (clean by construction), so uncommitted work in the main tree can never reach it;
refusing there withheld execution authority over state the turn would never see, and the refusal's own
advice (commit or stash it) is forbidden by the shared-checkout contract when the dirt is a co-worker's.

Both directions are asserted deliberately: a change that merely stopped refusing would have REMOVED a
safety property rather than rescoped it. So this module pins, in one place, that

  (a) an isolated turn IS granted authority while an in-scope path is dirty in the main tree;
  (b) a genuinely ambiguous baseline is STILL refused (an unreadable/absent base commit), so the
      isolated path is a different measurement rather than a skipped one;
  (c) the non-isolated refusal is unchanged, still naming `Scope-Paths` and the offending path;
  (d) the refusal names the baseline that was actually measured;
  (e) the receipt's `base_head` still comes from the MAIN tree even for an isolated turn, because
      finalize consumes it as a GIT REVISION (`diff base..HEAD`); a lane HEAD there would silently
      corrupt the finalize delta. The guard uses a second tree whose HEAD genuinely differs.

Fixtures are built here (stdlib unittest, git-backed throwaway repos) rather than pointed at any live
lane: the live lane set churns hourly, so a test naming one would rot.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from agent_workflows import oc_runipd as OC

from tests.test_ipd_lifecycle_cli import (
    _commit_all,
    _init_git,
    _ready_plan_text,
    _write_plan,
)

IN_SCOPE = "agent_workflows/demo.py"
OUT_OF_SCOPE = "unrelated_note.txt"


def _git(root: Path, args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
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


class IsolatedBaselineGrantsAuthorityTests(_Fixture):
    """(a) The defect itself: main-tree dirt must not withhold authority from an isolated lane."""

    def test_isolated_turn_granted_despite_in_scope_dirt_in_main_tree(self) -> None:
        self._dirty_in_scope()
        # Pre-fix, begin measured the MAIN tree unconditionally, so this was EXIT_CANNOT_RUN. That is
        # the bug: the lane is cut from the base COMMIT and never sees this edit.
        result = self._begin(isolated=True)
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").is_file())

    def test_the_same_dirt_still_refuses_a_non_isolated_turn(self) -> None:
        # The SAME repository state, differing only in where the turn will run. This pairing is what
        # makes (a) a rescope rather than a removal.
        self._dirty_in_scope()
        self.assertEqual(self._begin(isolated=False).exit_code, LC.EXIT_CANNOT_RUN)
        self.assertEqual(self._begin(isolated=True).exit_code, LC.EXIT_OK)

    def test_isolated_turn_records_the_committed_base_it_will_be_cut_from(self) -> None:
        self._dirty_in_scope()
        result = self._begin(isolated=True)
        assert result.receipt is not None
        self.assertEqual(
            result.receipt["base_head"], _git(self.root, ["rev-parse", "HEAD"])
        )
        self.assertNotEqual(result.receipt["base_head"], "unversioned")


class IsolatedBaselineStillFailsClosedTests(_Fixture):
    """(b) The isolated path is a DIFFERENT measurement, not a skipped check."""

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

    def test_isolated_baseline_does_not_exempt_out_of_scope_or_empty_scope(
        self,
    ) -> None:
        # An empty Scope-Paths is "clean" in both modes (unchanged contract), and out-of-scope dirt is
        # ignored in both modes (the path-overlap rule this plan must not disturb).
        (self.root / OUT_OF_SCOPE).write_text("someone else\n", encoding="utf-8")
        for isolated in (False, True):
            self.assertEqual(
                LC._baseline_ambiguity(self.root, [], isolated_baseline=isolated),
                "clean",
            )
            self.assertEqual(
                LC._baseline_ambiguity(
                    self.root, [IN_SCOPE], isolated_baseline=isolated
                ),
                "clean",
            )


class NonIsolatedRefusalIsUnchangedTests(_Fixture):
    """(c) + (d) The default path is byte-identical in behavior and names what it measured."""

    def test_default_argument_preserves_todays_refusal(self) -> None:
        self._dirty_in_scope()
        # No keyword at all: the single pre-existing caller shape.
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("Scope-Paths", result.message)
        self.assertIn(IN_SCOPE, result.message)
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").is_file())

    def test_default_argument_and_explicit_false_agree(self) -> None:
        self._dirty_in_scope()
        implicit = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        explicit = self._begin(isolated=False)
        self.assertEqual(implicit.exit_code, explicit.exit_code)
        self.assertEqual(implicit.message, explicit.message)

    def test_default_argument_receipt_is_unchanged_on_a_clean_tree(self) -> None:
        implicit = LC.begin(
            self.root, self.plan, "opencode/test", timestamp="2026-08-30T00:00:00Z"
        )
        explicit = self._begin(isolated=False)
        assert implicit.receipt is not None and explicit.receipt is not None
        self.assertEqual(implicit.receipt, explicit.receipt)
        self.assertEqual(
            implicit.receipt["base_head"], _git(self.root, ["rev-parse", "HEAD"])
        )

    def test_refusal_names_the_measured_baseline(self) -> None:
        self._dirty_in_scope()
        msg = self._begin(isolated=False).message
        # (d): the operator must be able to tell WHICH baseline produced the refusal.
        self.assertIn("Measured baseline:", msg)
        self.assertIn(str(self.root), msg)


class RefusalMessageIsActionableTests(_Fixture):
    """E-04: the advice must be one the shared-checkout contract permits."""

    def _refusal(self) -> str:
        self._dirty_in_scope()
        return self._begin(isolated=False).message

    def test_does_not_tell_the_operator_to_touch_another_partys_work(self) -> None:
        msg = self._refusal().lower()
        # Pre-fix text: "Commit or stash these in-scope changes first". AGENTS.md forbids committing or
        # stashing a co-worker's uncommitted work, so that was unactionable exactly when it fired.
        self.assertNotIn("commit or stash", msg)
        self.assertNotIn("stash these", msg)

    def test_offers_a_remedy_the_operator_may_actually_apply(self) -> None:
        msg = self._refusal()
        self.assertIn("worktree isolation", msg)
        self.assertIn("do NOT touch their work", msg)

    def test_preserves_the_two_properties_existing_tests_assert(self) -> None:
        # tests/test_ipd_lifecycle_cli.py (NOT in this plan's Scope-Paths) asserts the substring
        # `Scope-Paths` and the verbatim offending path. Pinned here so a future reword cannot break
        # a module this plan is forbidden to edit.
        msg = self._refusal()
        self.assertIn("Scope-Paths", msg)
        self.assertIn(IN_SCOPE, msg)

    def test_refusal_text_has_no_em_or_en_dash(self) -> None:
        # User-facing prose: the execution contract forbids em/en dashes.
        msg = self._refusal()
        self.assertNotIn("\u2014", msg)
        self.assertNotIn("\u2013", msg)


class BaseHeadAlwaysComesFromTheMainTreeTests(_Fixture):
    """(e) The F7 guard: `base_head` must never be sourced from the execution tree."""

    def test_base_head_is_this_repos_head_even_when_isolated(self) -> None:
        # Build a SECOND tree whose HEAD genuinely differs, mirroring a real lane (a live lane's HEAD
        # is not main's and is not even its ancestor). Built here rather than naming a live lane.
        other = self.root / "other-tree"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "other/lane", str(other), "HEAD"],
            cwd=self.root,
            check=True,
        )
        self.addCleanup(
            lambda: subprocess.run(
                ["git", "worktree", "remove", "--force", str(other)],
                cwd=self.root,
                check=False,
            )
        )
        (other / "divergent.txt").write_text(
            "only in the other tree\n", encoding="utf-8"
        )
        _commit_all(other, "advance the other tree")

        main_head = _git(self.root, ["rev-parse", "HEAD"])
        other_head = _git(other, ["rev-parse", "HEAD"])
        # The guard is only meaningful if the two HEADs really differ and neither is the other's base.
        self.assertNotEqual(main_head, other_head)
        self.assertNotEqual(
            0,
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", other_head, main_head],
                cwd=self.root,
                capture_output=True,
            ).returncode,
            "fixture is vacuous: the other tree must not be an ancestor of this one",
        )

        self._dirty_in_scope()
        result = self._begin(isolated=True)
        assert result.receipt is not None
        # Fails if base_head is ever sourced from an execution tree instead of repo_root.
        self.assertEqual(result.receipt["base_head"], main_head)
        self.assertNotEqual(result.receipt["base_head"], other_head)

    def test_isolated_and_non_isolated_receipts_bind_the_same_base(self) -> None:
        non_isolated = self._begin(isolated=False)
        LC.receipt_path_for(self.root, "abc123").unlink()
        isolated = self._begin(isolated=True)
        assert non_isolated.receipt is not None and isolated.receipt is not None
        self.assertEqual(
            non_isolated.receipt["base_head"], isolated.receipt["base_head"]
        )


class RunnerDeclaresTheExecutionBaselineTests(unittest.TestCase):
    """E-02: the driver, which alone knows whether the turn is isolated, declares it."""

    def test_isolated_turn_sends_the_declaration(self) -> None:
        self.assertEqual(OC.begin_baseline_env(True), {"AW_ISOLATED_BASELINE": "1"})

    def test_non_isolated_turn_sends_nothing(self) -> None:
        # Sending nothing (rather than "0") keeps the non-isolated path byte-identical to pre-fix.
        self.assertEqual(OC.begin_baseline_env(False), {})

    def test_driver_begin_accepts_the_isolated_declaration(self) -> None:
        import inspect

        sig = inspect.signature(OC.driver_begin)
        self.assertIn("isolated", sig.parameters)
        param = sig.parameters["isolated"]
        # Keyword-only with a behavior-preserving default: existing call shapes are unaffected.
        self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(param.default, False)

    def test_cli_reads_the_declaration_from_the_environment(self) -> None:
        # The runner reaches begin through a SUBPROCESS (`python -m agent_workflows ipd begin`), so a
        # function parameter alone would be unreachable; env is the transport. Absent or any value
        # other than "1" must mean today's behavior.
        import os
        from unittest import mock

        src = Path(LC.__file__).read_text(encoding="utf-8")
        self.assertIn("AW_ISOLATED_BASELINE", src)
        for value, expected in (
            ("1", True),
            ("0", False),
            ("true", False),
            ("", False),
        ):
            with mock.patch.dict(os.environ, {"AW_ISOLATED_BASELINE": value}):
                self.assertEqual(
                    os.environ.get("AW_ISOLATED_BASELINE") == "1", expected
                )

    def test_begin_is_called_before_the_lane_is_allocated(self) -> None:
        # The fail-closed ordering (authority BEFORE side effects) is deliberate and this plan must
        # not invert it: that is why the isolated baseline is the frozen base COMMIT rather than a
        # path to a lane that does not exist yet.
        src = Path(OC.__file__).read_text(encoding="utf-8")
        self.assertLess(
            src.index("begin_rc, begin_msg = driver_begin("),
            src.index("wt_handle = allocate_isolation_worktree("),
            "begin must still run before the lane is allocated",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

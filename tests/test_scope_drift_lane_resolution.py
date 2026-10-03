"""Behavioral regression tests for scope drift lane resolution (fkmjoy `iqtt8d` E-06).

Tests observable outcomes against real git repositories constructed in temporary directories:
(a) attempt-scoped lane execution: out-of-scope change is reported, with proven pre-fix failure
(b) canonical lane reconciliation: normal in-scope / out-of-scope detection unchanged
(c) no-lane silence: ruled maintainer contract preserved (no finding)
(d) irreconcilable lane advisory: check.scope-not-audited emitted at info severity (exit 0)
(e) foreign lane branch: review-sweep branches are never selected as candidates
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine as _ce
from agent_workflows import worktree_lease as _lease


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(path), check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"], cwd=str(path), check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=str(path), check=True
    )
    (path / "README.md").write_text("# Test Repository\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(path), check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial commit"], cwd=str(path), check=True
    )
    return path


def _create_plan_and_receipt(
    repo: Path,
    plan_id: str,
    base_head: str,
    scope_paths: list[str],
) -> tuple[Path, Path]:
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plans_dir / f"20261001-fkmjoy-01-{plan_id}-test-plan.ipd.md"
    scope_decl = ", ".join(scope_paths) if scope_paths else "allowed.txt"
    plan_file.write_text(
        f"""# Plan: Test Plan

- Id: {plan_id}
- Set: fkmjoy
- Scope-Paths: {scope_decl}
- Status: approved
""",
        encoding="utf-8",
    )

    state_dir = repo / ".aw" / "state" / "ipd-lifecycle"
    state_dir.mkdir(parents=True, exist_ok=True)
    receipt_file = state_dir / f"{plan_id}.receipt.json"
    receipt_file.write_text(
        json.dumps(
            {
                "plan_id": plan_id,
                "base_head": base_head,
                "scope_paths": scope_paths,
            }
        ),
        encoding="utf-8",
    )
    return plan_file, receipt_file


class TestScopeDriftLaneResolution(unittest.TestCase):
    """Behavioral tests for lane resolution and scope drift detection."""

    def test_case_a_attempt_scoped_lane_reports_drift_and_proves_pre_fix_failure(
        self,
    ) -> None:
        """Case (a): an execution in an attempt-scoped lane is audited, with proven pre-fix failure."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            # Canonical lane cut from base0, abandoned
            canonical_dir = root / "canonical_lane"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/plana1",
                    str(canonical_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )

            # Main advances to base1
            (repo / "main_work.txt").write_text("main update\n", encoding="utf-8")
            subprocess.run(["git", "add", "main_work.txt"], cwd=str(repo), check=True)
            subprocess.run(
                ["git", "commit", "-qm", "advance main"], cwd=str(repo), check=True
            )
            base1 = _git(repo, "rev-parse", "HEAD")

            # Attempt-scoped lane cut from base1
            attempt_dir = root / "attempt_lane"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/plana1_attempt2",
                    str(attempt_dir),
                    base1,
                ],
                cwd=str(repo),
                check=True,
            )

            # In attempt lane, make an out-of-scope commit
            (attempt_dir / "unapproved_change.txt").write_text(
                "drift\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", "unapproved_change.txt"],
                cwd=str(attempt_dir),
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-qm", "attempt work"],
                cwd=str(attempt_dir),
                check=True,
            )

            _create_plan_and_receipt(
                repo,
                "plana1",
                base1,
                ["in_scope.txt"],
            )

            # 1. With current implementation: out-of-scope path is detected
            drift = _ce.check_scope_drift(repo)
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0].rule, "check.scope-drift")
            self.assertEqual(drift[0].severity, "error")
            self.assertIn("unapproved_change.txt", drift[0].detail)

            # 2. PROVEN PRE-FIX FAILURE: simulate pre-E-03 logic (calling inspect_lane directly)
            def _old_plan_execution_tree(repo_root: Path, plan_id: str, base_head: str):
                st = _lease.inspect_lane(Path(repo_root), plan_id)
                lane = st.worktree_path
                if lane is None or not lane.is_dir():
                    return None
                rc, _, _ = _ce._git_capture(
                    lane, ["merge-base", "--is-ancestor", base_head, "HEAD"]
                )
                return lane if rc == 0 else None

            with mock.patch(
                "agent_workflows.check_engine._plan_execution_tree",
                side_effect=_old_plan_execution_tree,
            ):
                pre_fix_drift = _ce.check_scope_drift(repo)
                # Before E-03, inspect_lane checked canonical lane whose base was base0, which
                # failed ancestry check against base1, silently reporting NO drift finding.
                self.assertEqual(len(pre_fix_drift), 0)

    def test_case_b_canonical_lane_reconciles_normally(self) -> None:
        """Case (b): a plan whose canonical lane reconciles normally has behavior unchanged."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            canonical_dir = root / "canonical_lane"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/planb1",
                    str(canonical_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )

            (canonical_dir / "out_of_scope.txt").write_text("drift\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "out_of_scope.txt"], cwd=str(canonical_dir), check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "canonical work"],
                cwd=str(canonical_dir),
                check=True,
            )

            _create_plan_and_receipt(
                repo,
                "planb1",
                base0,
                ["in_scope.txt"],
            )

            drift = _ce.check_scope_drift(repo)
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0].rule, "check.scope-drift")
            self.assertIn("out_of_scope.txt", drift[0].detail)

    def test_case_c_no_lane_is_silent(self) -> None:
        """Case (c): a plan with no lane produces total silence (ruled maintainer contract)."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            _create_plan_and_receipt(
                repo,
                "planc1",
                base0,
                ["in_scope.txt"],
            )

            drift = _ce.check_scope_drift(repo)
            self.assertEqual(len(drift), 0)

    def test_case_d_irreconcilable_lane_emits_info_advisory(self) -> None:
        """Case (d): an irreconcilable work-holding lane emits check.scope-not-audited at info."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            # Divergent lane cut from base0
            lane_dir = root / "divergent_lane"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/pland1",
                    str(lane_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )
            (lane_dir / "drift.txt").write_text("divergent\n", encoding="utf-8")
            subprocess.run(["git", "add", "drift.txt"], cwd=str(lane_dir), check=True)
            subprocess.run(
                ["git", "commit", "-qm", "divergent work"],
                cwd=str(lane_dir),
                check=True,
            )

            # Main advances to base1, and receipt is frozen at base1
            (repo / "adv.txt").write_text("main adv\n", encoding="utf-8")
            subprocess.run(["git", "add", "adv.txt"], cwd=str(repo), check=True)
            subprocess.run(
                ["git", "commit", "-qm", "advance main"], cwd=str(repo), check=True
            )
            base1 = _git(repo, "rev-parse", "HEAD")

            _create_plan_and_receipt(
                repo,
                "pland1",
                base1,
                ["allowed.txt"],
            )

            drift = _ce.check_scope_drift(repo)
            self.assertEqual(len(drift), 1)
            d = drift[0]
            self.assertEqual(d.rule, "check.scope-not-audited")
            self.assertEqual(d.severity, "info")
            self.assertIn("pland1", d.detail)
            self.assertIn("aw/lane/pland1", d.detail)
            self.assertIn("finalize remains the enforcement point", d.detail)
            self.assertIn("scope was not audited", d.detail)

            # Verify non-gating: drift_exit_code returns 0 for info findings
            exit_code = _core.drift_exit_code([d])
            self.assertEqual(exit_code, 0)

    def test_case_e_foreign_review_sweep_lane_never_selected(self) -> None:
        """Case (e): foreign review-sweep branches are never selected as lane candidates."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            foreign_dir = root / "foreign_lane"
            foreign_branch = "aw/lane/review-sweep-run-20261001T051707Z-999999"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    foreign_branch,
                    str(foreign_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )

            # Query candidates for various plan IDs
            for pid in ["review-sweep", "review", "run", "999999", "plan01"]:
                cands = _lease.enumerate_lane_candidates(repo, pid, base0)
                matched_branches = [c.branch for c in cands]
                self.assertNotIn(foreign_branch, matched_branches)

    def test_f10_candidate_tie_break_prefers_work_holding_then_highest_attempt(
        self,
    ) -> None:
        """F-10 tie-break: when multiple candidates descend from receipt base, select work-holding then highest attempt."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            repo.mkdir()
            _init_repo(repo)
            base0 = _git(repo, "rev-parse", "HEAD")

            # Canonical lane cut from base0 (empty, no commits)
            canonical_dir = root / "canonical"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/tiebrk",
                    str(canonical_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )

            # Attempt 2 lane cut from base0 (holds work)
            attempt2_dir = root / "attempt2"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/tiebrk_attempt2",
                    str(attempt2_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )
            (attempt2_dir / "work.txt").write_text("work\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "work.txt"], cwd=str(attempt2_dir), check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "attempt2 work"],
                cwd=str(attempt2_dir),
                check=True,
            )

            # Attempt 3 lane cut from base0 (also holds work)
            attempt3_dir = root / "attempt3"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/tiebrk_attempt3",
                    str(attempt3_dir),
                    base0,
                ],
                cwd=str(repo),
                check=True,
            )
            (attempt3_dir / "work3.txt").write_text("work3\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "work3.txt"], cwd=str(attempt3_dir), check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "attempt3 work"],
                cwd=str(attempt3_dir),
                check=True,
            )

            cands = _lease.enumerate_lane_candidates(repo, "tiebrk", base0)
            self.assertEqual(len(cands), 3)
            self.assertEqual([c.attempt for c in cands], [0, 2, 3])
            self.assertTrue(all(c.receipt_consistent for c in cands))

            # _plan_execution_tree must select attempt3 (holds work + highest attempt)
            exec_tree = _ce._plan_execution_tree(repo, "tiebrk", base0)
            self.assertEqual(exec_tree, attempt3_dir)

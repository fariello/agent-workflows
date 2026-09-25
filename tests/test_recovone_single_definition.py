"""Tests verifying single-definition recovery routing and reconciliation.

recovone (`cdxcbh`): single working definitions in runner_shared for
classify_recovery_disposition, build_verify_and_continue_notice,
route_recovery_turn, and reconcile_disposition.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, runner_shared, worktree_lease


class _TempGitRepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="test-recovone-"))
        self.repo = self._tmp / "repo"
        self.repo.mkdir()
        self.run_dir = self._tmp / "run"
        self.run_dir.mkdir()

        self._git(self.repo, ["init", "-b", "main"])
        self._git(self.repo, ["config", "user.name", "Test Runner"])
        self._git(self.repo, ["config", "user.email", "runner@example.com"])

        init_file = self.repo / "README.md"
        init_file.write_text("# Test Repo\n", encoding="utf-8")
        self._git(self.repo, ["add", "README.md"])
        self._git(self.repo, ["commit", "-m", "initial commit"])

        rc, out, _ = self._git(self.repo, ["rev-parse", "HEAD"])
        self.assertEqual(rc, 0)
        self.base_sha = out.strip()

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _git(self, cwd: Path, args: list[str]) -> tuple[int, str, str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr


class TestClassifyRecoveryDispositionBehavior(_TempGitRepoTestCase):
    """Behavioral parity across oc_runipd, agy_runipd, and runner_shared."""

    def _assert_modules_agree(
        self,
        item: dict[str, Any],
        expected_disposition: str,
        expected_snapshot_only: bool,
        expected_dirty: bool,
        expected_commits_ahead: int,
        expected_real_count: int | None = None,
    ) -> None:
        # Obtain LaneState via worktree_lease.inspect_lane to guarantee realistic inputs
        lane_id = item.get("preserved_lane_id") or item.get("id6")
        st = worktree_lease.inspect_lane(self.repo, lane_id, base_commit=self.base_sha)
        self.assertIsInstance(st, worktree_lease.LaneState)

        modules = (oc_runipd, agy_runipd, runner_shared)
        results = []
        for mod in modules:
            res = mod.classify_recovery_disposition(
                self.repo, item, {"repo": str(self.repo)}
            )
            self.assertEqual(
                res.disposition,
                expected_disposition,
                f"{mod.__name__} returned unexpected disposition {res.disposition}",
            )
            self.assertEqual(
                res.snapshot_only,
                expected_snapshot_only,
                f"{mod.__name__} returned unexpected snapshot_only {res.snapshot_only}",
            )
            self.assertEqual(
                res.dirty,
                expected_dirty,
                f"{mod.__name__} returned unexpected dirty {res.dirty}",
            )
            self.assertEqual(
                res.commits_ahead,
                expected_commits_ahead,
                f"{mod.__name__} returned unexpected commits_ahead {res.commits_ahead}",
            )
            if expected_real_count is not None:
                self.assertEqual(
                    len(res.real_commits),
                    expected_real_count,
                    f"{mod.__name__} returned unexpected real_commits count",
                )
            results.append(
                (
                    res.disposition,
                    res.snapshot_only,
                    res.inspected_branch,
                    res.inspected_worktree,
                    res.dirty,
                    res.commits_ahead,
                )
            )

        # All three must agree on the full tuple
        first = results[0]
        for idx, other in enumerate(results[1:], start=1):
            self.assertEqual(
                first,
                other,
                f"{modules[0].__name__} and {modules[idx].__name__} disagreed",
            )

    def test_ordinary_commit(self) -> None:
        lane_id = "recov01"
        branch_name = worktree_lease.lane_branch_name(lane_id)
        self._git(self.repo, ["checkout", "-b", branch_name, self.base_sha])
        (self.repo / "feature.py").write_text("print('feat')\n", encoding="utf-8")
        self._git(self.repo, ["add", "feature.py"])
        self._git(self.repo, ["commit", "-m", "feat: add feature"])
        self._git(self.repo, ["checkout", "main"])

        item = {
            "id6": lane_id,
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
        }
        self._assert_modules_agree(
            item=item,
            expected_disposition=runner_shared.DISPOSITION_VERIFY_AND_CONTINUE,
            expected_snapshot_only=False,
            expected_dirty=False,
            expected_commits_ahead=1,
            expected_real_count=1,
        )

    def test_snapshot_only_commit(self) -> None:
        lane_id = "recov02"
        branch_name = worktree_lease.lane_branch_name(lane_id)
        self._git(self.repo, ["checkout", "-b", branch_name, self.base_sha])
        (self.repo / "wip.py").write_text("print('wip')\n", encoding="utf-8")
        self._git(self.repo, ["add", "wip.py"])
        snap_msg = f"{worktree_lease.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX} mid-edit work"
        self._git(self.repo, ["commit", "-m", snap_msg])
        self._git(self.repo, ["checkout", "main"])

        item = {
            "id6": lane_id,
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
        }
        self._assert_modules_agree(
            item=item,
            expected_disposition=runner_shared.DISPOSITION_FRESH_EXECUTION,
            expected_snapshot_only=True,
            expected_dirty=False,
            expected_commits_ahead=1,
            expected_real_count=0,
        )

    def test_missing_lane_branch(self) -> None:
        lane_id = "recov03"
        item = {
            "id6": lane_id,
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
        }
        self._assert_modules_agree(
            item=item,
            expected_disposition=runner_shared.DISPOSITION_FRESH_EXECUTION,
            expected_snapshot_only=False,
            expected_dirty=False,
            expected_commits_ahead=0,
            expected_real_count=0,
        )

    def test_no_commits_ahead(self) -> None:
        lane_id = "recov04"
        branch_name = worktree_lease.lane_branch_name(lane_id)
        self._git(self.repo, ["checkout", "-b", branch_name, self.base_sha])
        self._git(self.repo, ["checkout", "main"])

        item = {
            "id6": lane_id,
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
        }
        self._assert_modules_agree(
            item=item,
            expected_disposition=runner_shared.DISPOSITION_FRESH_EXECUTION,
            expected_snapshot_only=False,
            expected_dirty=False,
            expected_commits_ahead=0,
            expected_real_count=0,
        )

    def test_dirty_lane_with_real_commit(self) -> None:
        lane_id = "recov05"
        branch_name = worktree_lease.lane_branch_name(lane_id)
        self._git(self.repo, ["checkout", "-b", branch_name, self.base_sha])
        (self.repo / "committed.py").write_text("committed = True\n", encoding="utf-8")
        self._git(self.repo, ["add", "committed.py"])
        self._git(self.repo, ["commit", "-m", "feat: committed work"])
        self._git(self.repo, ["checkout", "main"])

        wt_path = self._tmp / "lanes" / lane_id
        wt_path.parent.mkdir(parents=True, exist_ok=True)
        self._git(self.repo, ["worktree", "add", str(wt_path), branch_name])
        (wt_path / "uncommitted.txt").write_text("dirty edits\n", encoding="utf-8")

        item = {
            "id6": lane_id,
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
        }
        self._assert_modules_agree(
            item=item,
            expected_disposition=runner_shared.DISPOSITION_VERIFY_AND_CONTINUE,
            expected_snapshot_only=False,
            expected_dirty=True,
            expected_commits_ahead=1,
            expected_real_count=1,
        )


class TestRouteRecoveryTurnBehavior(_TempGitRepoTestCase):
    """Proves route_recovery_turn handles save_state injection on both hosts."""

    def test_route_recovery_turn_saves_state(self) -> None:
        lane_id = "rtr001"
        branch_name = worktree_lease.lane_branch_name(lane_id)
        self._git(self.repo, ["checkout", "-b", branch_name, self.base_sha])
        (self.repo / "code.py").write_text("x = 1\n", encoding="utf-8")
        self._git(self.repo, ["add", "code.py"])
        self._git(self.repo, ["commit", "-m", "feat: code"])
        self._git(self.repo, ["checkout", "main"])

        item = {
            "id6": lane_id,
            "setid": "testset",
            "preserved_lane_id": lane_id,
            "preserved_base": self.base_sha,
            "position": 1,
            "action": "execute",
            "status": "queued",
        }
        state = {
            "run_id": "test-run-001",
            "repo": str(self.repo),
            "started_at": runner_shared.utc_now(),
            "options": {},
            "queue": [item],
        }

        for host in (oc_runipd, agy_runipd):
            host_run_dir = self.run_dir / host.__name__
            host_run_dir.mkdir(parents=True, exist_ok=True)
            decision = host.route_recovery_turn(host_run_dir, state, item, True)
            self.assertIsNotNone(decision)
            self.assertIn("recovery_routing", item)
            self.assertEqual(
                item["recovery_routing"]["disposition"],
                runner_shared.DISPOSITION_VERIFY_AND_CONTINUE,
            )
            state_file = host_run_dir / "state.json"
            self.assertTrue(
                state_file.exists(),
                f"state.json was not created in {host_run_dir} for {host.__name__}",
            )


class TestReconcileDispositionTolerant(_TempGitRepoTestCase):
    """Proves reconcile_disposition tolerates items without configured_file."""

    def test_reconcile_without_configured_file(self) -> None:
        item = {"id6": "rec001", "position": 1, "action": "execute"}
        for host in (oc_runipd, agy_runipd):
            disp0, out0 = host.reconcile_disposition(self.repo, item, self.run_dir, 0)
            self.assertIn(disp0, ("fail-verify", "partial"))
            self.assertIsNone(out0)

            disp1, out1 = host.reconcile_disposition(self.repo, item, self.run_dir, 1)
            self.assertIn(disp1, ("fail-gate", "failed-safely"))
            self.assertIsNone(out1)


class TestSingleDefinitionIdentity(unittest.TestCase):
    """Proves single-definition identity across host modules and runner_shared."""

    def test_identity_pins(self) -> None:
        names = (
            "classify_recovery_disposition",
            "build_verify_and_continue_notice",
            "reconcile_disposition",
        )
        for name in names:
            for host in (oc_runipd, agy_runipd):
                self.assertIs(
                    getattr(host, name),
                    getattr(runner_shared, name),
                    f"{host.__name__}.{name} is not runner_shared.{name}",
                )


if __name__ == "__main__":
    unittest.main()

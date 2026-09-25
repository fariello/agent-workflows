"""Dispatch-time already-landed gate tests for OpenCode and Antigravity runners.

mergeskip (8k0z40) E-07.

NOTE ON SPAWN SEAM: Patching `execute_item` proves the gate skipped DISPATCH, which is this
plan's claim, and is the right level: it is cheap, host-neutral, and needs no agent launcher.
It therefore does NOT prove the launcher was never reached (a stronger claim this plan does
not make).
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared


class AlreadyLandedPredicateUnitTests(unittest.TestCase):
    """Direct unit tests of runner_shared.lane_work_already_landed on hand-built records."""

    def test_empty_records(self):
        self.assertFalse(runner_shared.lane_work_already_landed([]))

    def test_single_landed_clean_with_commits(self):
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 1,
                "dirty": False,
            }
        ]
        self.assertTrue(runner_shared.lane_work_already_landed(records))

    def test_single_landed_zero_commits_dirty(self):
        # F-3 false-positive guard
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 0,
                "dirty": True,
            }
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_single_landed_commits_ahead_dirty(self):
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 2,
                "dirty": True,
            }
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_single_landed_zero_commits_clean(self):
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 0,
                "dirty": False,
            }
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_fail_closed_with_stranded_attempt(self):
        # rule (ii): any STRANDED lane keeps dispatch
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 1,
                "dirty": False,
            },
            {
                "lane_state": runner_shared.LANE_STRANDED,
                "commits_ahead": 1,
                "dirty": False,
            },
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_fail_closed_with_unknown_attempt(self):
        # rule (ii): any UNKNOWN lane keeps dispatch
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 1,
                "dirty": False,
            },
            {
                "lane_state": runner_shared.LANE_UNKNOWN,
                "commits_ahead": 0,
                "dirty": False,
            },
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_fail_closed_with_live_attempt(self):
        # rule (ii): any LIVE lane keeps dispatch
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 1,
                "dirty": False,
            },
            {
                "lane_state": runner_shared.LANE_LIVE,
                "commits_ahead": 1,
                "dirty": False,
            },
        ]
        self.assertFalse(runner_shared.lane_work_already_landed(records))

    def test_landed_with_empty_or_superseded_sister_lane(self):
        records = [
            {
                "lane_state": runner_shared.LANE_LANDED,
                "commits_ahead": 1,
                "dirty": False,
            },
            {
                "lane_state": runner_shared.LANE_EMPTY_OF_WORK,
                "commits_ahead": 0,
                "dirty": False,
            },
            {
                "lane_state": runner_shared.LANE_SUPERSEDED,
                "commits_ahead": 0,
                "dirty": False,
            },
        ]
        self.assertTrue(runner_shared.lane_work_already_landed(records))


class AlreadyLandedDispatchTests(unittest.TestCase):
    """End-to-end dispatch tests verifying oc_runipd and agy_runipd gate already-landed plans."""

    @staticmethod
    def _create_fixture_repo(
        root: pathlib.Path, id6: str = "abc123"
    ) -> tuple[pathlib.Path, str]:
        repo = root / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        for cmd in (
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / "init.txt").write_text("initial\n", encoding="utf-8")
        plans_dir = repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        plan_file = plans_dir / f"20260101-s-01-{id6}-test-plan.ipd.md"
        plan_file.write_text(
            f"# IPD: Test plan\n\n- Date: 2026-01-01\n- Kind: child\n- Status: approved\n"
            f"- Set: s\n- Id: {id6}\n- Highest E allocated: 01\n\n## Workflow history\n"
            f"- 2026-01-01 approved: approved\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit with plan"], cwd=repo, check=True
        )
        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return repo, base_sha

    @staticmethod
    def _create_run_dir(
        root: pathlib.Path,
        repo: pathlib.Path,
        id6: str = "abc123",
        initial_status: str = "approved",
    ) -> pathlib.Path:
        run_dir = root / "run-dispatch"
        run_dir.mkdir(parents=True, exist_ok=True)
        plan_rel = f".aw/records/plans/pending/20260101-s-01-{id6}-test-plan.ipd.md"
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": "run-dispatch",
                    "repo": str(repo),
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "selectors": ["s"],
                    "options": {},
                    "set_sessions": {},
                    "queue": [
                        {
                            "position": 1,
                            "id6": id6,
                            "setid": "s",
                            "action": "execute",
                            "kind": "child",
                            "status": "queued",
                            "initial_status": initial_status,
                            "dependencies": [],
                            "attempts": [],
                            "configured_file": plan_rel,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return run_dir

    def test_case_a_positive_already_landed(self):
        """Case A: Merged committed clean lane -> execute_item skipped, status already-landed, rc != 0."""
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    repo, base_sha = self._create_fixture_repo(root, "abc123")
                    # Cut lane from resolved sha
                    wt_path = root / "wt_abc123"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123",
                            str(wt_path),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path / "code.txt").write_text("feature\n", encoding="utf-8")
                    subprocess.run(["git", "add", "code.txt"], cwd=wt_path, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "lane commit"], cwd=wt_path, check=True
                    )
                    # Merge into main
                    subprocess.run(
                        [
                            "git",
                            "merge",
                            "--no-ff",
                            "aw/lane/abc123",
                            "-m",
                            "merge lane abc123",
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )

                    run_dir = self._create_run_dir(
                        root, repo, "abc123", initial_status="approved"
                    )
                    calls: list = []

                    def _fake_execute(rd, st, item, *args, **kwargs):
                        calls.append(item.get("id6"))
                        item["status"] = "executed"
                        module.save_state(rd, st)

                    with (
                        mock.patch.object(module, "execute_item", _fake_execute),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        rc = module.run_queue(run_dir, retry_incomplete=False)

                    # 1. execute_item never called
                    self.assertEqual(
                        len(calls),
                        0,
                        f"{module.__name__} called execute_item on landed lane",
                    )
                    # 2. queue status is already-landed
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(
                        item["status"], runner_shared.ALREADY_LANDED_STATUS
                    )
                    # 3. already_landed_recovery mentions aw ipd finalize
                    self.assertIn("already_landed_recovery", item)
                    self.assertIn("aw ipd finalize", item["already_landed_recovery"])
                    # 4. events.jsonl carries already-landed event
                    events_file = run_dir / "events.jsonl"
                    self.assertTrue(events_file.exists())
                    events = [
                        json.loads(line)
                        for line in events_file.read_text(encoding="utf-8").splitlines()
                        if line
                    ]
                    self.assertTrue(
                        any(e.get("event") == "already-landed" for e in events)
                    )
                    # 5. run_queue returns nonzero
                    self.assertNotEqual(
                        rc,
                        0,
                        f"{module.__name__} returned exit 0 for already-landed item",
                    )

    def test_case_b_negative_unmerged_lane(self):
        """Case B: Unmerged committed lane -> execute_item called once."""
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    repo, base_sha = self._create_fixture_repo(root, "abc123")
                    wt_path = root / "wt_abc123"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123",
                            str(wt_path),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path / "code.txt").write_text("feature\n", encoding="utf-8")
                    subprocess.run(["git", "add", "code.txt"], cwd=wt_path, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "lane commit"], cwd=wt_path, check=True
                    )

                    run_dir = self._create_run_dir(
                        root, repo, "abc123", initial_status="approved"
                    )
                    calls: list = []

                    def _fake_execute(rd, st, item, *args, **kwargs):
                        calls.append(item.get("id6"))
                        item["status"] = "executed"
                        module.save_state(rd, st)

                    with (
                        mock.patch.object(module, "execute_item", _fake_execute),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(
                        len(calls),
                        1,
                        f"{module.__name__} did not call execute_item for unmerged lane",
                    )

    def test_case_c_false_positive_guard_zero_commits_dirty(self):
        """Case C: Zero commits beyond base with uncommitted dirty changes -> execute_item called once."""
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    repo, base_sha = self._create_fixture_repo(root, "abc123")
                    wt_path = root / "wt_abc123"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123",
                            str(wt_path),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path / "dirty.txt").write_text(
                        "uncommitted\n", encoding="utf-8"
                    )

                    run_dir = self._create_run_dir(
                        root, repo, "abc123", initial_status="approved"
                    )
                    calls: list = []

                    def _fake_execute(rd, st, item, *args, **kwargs):
                        calls.append(item.get("id6"))
                        item["status"] = "executed"
                        module.save_state(rd, st)

                    with (
                        mock.patch.object(module, "execute_item", _fake_execute),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(
                        len(calls),
                        1,
                        f"{module.__name__} falsely parked zero-commit dirty lane",
                    )

    def test_case_d_fail_closed_unmerged_attempt(self):
        """Case D: Merged aw/lane/abc123 PLUS unmerged aw/lane/abc123_attempt2 -> execute_item called once."""
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    repo, base_sha = self._create_fixture_repo(root, "abc123")
                    # Lane 1: merged
                    wt_path1 = root / "wt_abc123"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123",
                            str(wt_path1),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path1 / "c1.txt").write_text("c1\n", encoding="utf-8")
                    subprocess.run(["git", "add", "c1.txt"], cwd=wt_path1, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "lane 1 commit"],
                        cwd=wt_path1,
                        check=True,
                    )
                    subprocess.run(
                        [
                            "git",
                            "merge",
                            "--no-ff",
                            "aw/lane/abc123",
                            "-m",
                            "merge lane 1",
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )

                    # Lane 2: attempt 2 unmerged
                    wt_path2 = root / "wt_abc123_attempt2"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123_attempt2",
                            str(wt_path2),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path2 / "c2.txt").write_text("c2\n", encoding="utf-8")
                    subprocess.run(["git", "add", "c2.txt"], cwd=wt_path2, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "lane 2 commit"],
                        cwd=wt_path2,
                        check=True,
                    )

                    run_dir = self._create_run_dir(
                        root, repo, "abc123", initial_status="approved"
                    )
                    calls: list = []

                    def _fake_execute(rd, st, item, *args, **kwargs):
                        calls.append(item.get("id6"))
                        item["status"] = "executed"
                        module.save_state(rd, st)

                    with (
                        mock.patch.object(module, "execute_item", _fake_execute),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(
                        len(calls),
                        1,
                        f"{module.__name__} failed to fail closed on unmerged attempt",
                    )

    def test_case_e_reusable_plan_dispatches(self):
        """Case E: Merged lane with initial_status=reusable -> execute_item called once."""
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    repo, base_sha = self._create_fixture_repo(root, "abc123")
                    wt_path = root / "wt_abc123"
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "add",
                            "-b",
                            "aw/lane/abc123",
                            str(wt_path),
                            base_sha,
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    (wt_path / "code.txt").write_text("feature\n", encoding="utf-8")
                    subprocess.run(["git", "add", "code.txt"], cwd=wt_path, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "lane commit"], cwd=wt_path, check=True
                    )
                    subprocess.run(
                        [
                            "git",
                            "merge",
                            "--no-ff",
                            "aw/lane/abc123",
                            "-m",
                            "merge lane abc123",
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )

                    run_dir = self._create_run_dir(
                        root, repo, "abc123", initial_status="reusable"
                    )
                    calls: list = []

                    def _fake_execute(rd, st, item, *args, **kwargs):
                        calls.append(item.get("id6"))
                        item["status"] = "executed"
                        module.save_state(rd, st)

                    with (
                        mock.patch.object(module, "execute_item", _fake_execute),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(
                        len(calls),
                        1,
                        f"{module.__name__} did not dispatch reusable plan",
                    )


if __name__ == "__main__":
    unittest.main()

"""Tests for merge-back conflict resolution sent back to the agent in its lane.

mergeagent-01 (`ounhsn`) E-05 (unit) and E-08 (driver).
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, commit_lock, oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}


class UnitConflictSendbackTests(unittest.TestCase):
    """Unit tests for prepare_lane_for_conflict_resolution and merge_conflict_question (E-05)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _repo(self, root: pathlib.Path, branch: str = "main") -> pathlib.Path:
        repo = root / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", branch], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "base.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
        return repo

    def _lane(self, repo: pathlib.Path, id6: str, *, path: str, body: str):
        from agent_workflows import worktree_lease

        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        branch = f"aw/lane/{id6}"
        subprocess.run(["git", "branch", branch], cwd=repo, check=True)
        wt = repo.parent / f"wt-{id6}"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(wt), branch], cwd=repo, check=True
        )
        target = wt / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        subprocess.run(["git", "add", path], cwd=wt, check=True)
        subprocess.run(
            ["git", "commit", "-qm", f"lane {id6}: write {path}"], cwd=wt, check=True
        )
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )

    def test_case_1_conflicting_lane_leaves_main_clean_and_returns_conflicts(self):
        """Case 1: prepare_lane_for_conflict_resolution returns ok=True, conflicted_paths=('clash.txt',),
        leaves markers in the lane file, and leaves repo's HEAD and git status --short byte-identical."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._repo(root)
                handle = self._lane(repo, "ccc111", path="clash.txt", body="lane\n")

                (repo / "clash.txt").write_text("main\n", encoding="utf-8")
                subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main writes clash.txt"],
                    cwd=repo,
                    check=True,
                )

                head_before = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                status_before = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                run_checked = _MODULES[runner].run_checked
                prep = runner_shared.prepare_lane_for_conflict_resolution(
                    repo, handle, run_checked=run_checked
                )

                self.assertTrue(prep.ok)
                self.assertEqual(prep.conflicted_paths, ("clash.txt",))
                self.assertEqual(prep.merge_head, head_before)

                lane_content = (handle.path / "clash.txt").read_text(encoding="utf-8")
                self.assertIn("<<<<<<<", lane_content)
                self.assertIn(">>>>>>>", lane_content)

                head_after = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                status_after = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                self.assertEqual(head_after, head_before)
                self.assertEqual(status_after, status_before)

    def test_case_2_unrelated_main_advance_merges_cleanly(self):
        """Case 2: main moved on an UNRELATED file -> returns ok=True, conflicted_paths=() and
        a lane whose HEAD now has main as an ancestor."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._repo(root)
                handle = self._lane(repo, "ccc222", path="lane.txt", body="lane work\n")

                (repo / "other.txt").write_text("main unrelated\n", encoding="utf-8")
                subprocess.run(["git", "add", "other.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main unrelated"], cwd=repo, check=True
                )
                main_tip = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                run_checked = _MODULES[runner].run_checked
                prep = runner_shared.prepare_lane_for_conflict_resolution(
                    repo, handle, run_checked=run_checked, main_tip=main_tip
                )

                self.assertTrue(prep.ok)
                self.assertEqual(prep.conflicted_paths, ())
                self.assertEqual(prep.merge_head, "")

                rc, _, _ = runner_shared._run_git(
                    handle.path, ["merge-base", "--is-ancestor", main_tip, "HEAD"]
                )
                self.assertEqual(rc, 0, "main tip must be an ancestor of lane HEAD")

    def test_case_3_called_with_merge_in_progress_refuses_without_second_merge(self):
        """Case 3: called with a merge already in progress returns ok=False naming the unconcluded merge
        and does NOT run a second git merge."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._repo(root)
                handle = self._lane(repo, "ccc333", path="clash.txt", body="lane\n")

                (repo / "clash.txt").write_text("main\n", encoding="utf-8")
                subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
                )

                run_checked = _MODULES[runner].run_checked
                prep1 = runner_shared.prepare_lane_for_conflict_resolution(
                    repo, handle, run_checked=run_checked
                )
                self.assertTrue(prep1.ok)
                self.assertTrue(runner_shared.merge_in_progress(handle.path))

                prep2 = runner_shared.prepare_lane_for_conflict_resolution(
                    repo, handle, run_checked=run_checked
                )
                self.assertFalse(prep2.ok)
                self.assertIn("unconcluded merge in progress", prep2.detail)

    def test_case_4_non_main_branch_name_succeeds_without_error(self):
        """Case 4: repository whose default branch is master succeeds without 128 error on rev-parse."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                root = pathlib.Path(td)
                repo = self._repo(root, branch="master")
                handle = self._lane(repo, "ccc444", path="clash.txt", body="lane\n")

                (repo / "clash.txt").write_text("master clash\n", encoding="utf-8")
                subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "master clash"], cwd=repo, check=True
                )

                run_checked = _MODULES[runner].run_checked
                prep = runner_shared.prepare_lane_for_conflict_resolution(
                    repo, handle, run_checked=run_checked
                )
                self.assertTrue(prep.ok)
                self.assertEqual(prep.conflicted_paths, ("clash.txt",))

    def test_case_5_merge_conflict_question_shape_and_commit_instructions(self):
        """Case 5: merge_conflict_question names adjacency-only and keep-both, or semantic and resolve-on-merits,
        and carries the bare git commit --no-edit instruction with no pathspec commit and no aw commit."""
        adj_detail = {
            "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
            "files": [
                {
                    "path": "clash.txt",
                    "shape": runner_shared.CONFLICT_SHAPE_ADJACENCY_ONLY,
                    "ours_hunks": 1,
                    "theirs_hunks": 1,
                }
            ],
        }
        sem_detail = {
            "shape": runner_shared.CONFLICT_SHAPE_SEMANTIC,
            "files": [
                {
                    "path": "clash.txt",
                    "shape": runner_shared.CONFLICT_SHAPE_SEMANTIC,
                    "ours_hunks": 1,
                    "theirs_hunks": 1,
                }
            ],
        }

        q_adj = runner_shared.merge_conflict_question(
            adj_detail, main_tip="1111111111111111111111111111111111111111"
        )
        q_sem = runner_shared.merge_conflict_question(
            sem_detail, main_tip="2222222222222222222222222222222222222222"
        )

        # Adjacency-only check
        self.assertIn("Conflict shape is adjacency-only", q_adj)
        self.assertIn("Keeping both sides in a sensible order is correct", q_adj)
        self.assertNotIn("unknown", q_adj.lower().split("## conflict details")[0])
        self.assertIn("git commit --no-edit", q_adj)
        self.assertNotIn("git commit -- <", q_adj)
        self.assertNotIn("git commit -- ", q_adj)
        self.assertNotIn("aw commit", q_adj)

        # Semantic check
        self.assertIn("Conflict shape is semantic", q_sem)
        self.assertIn("Read both sides and resolve on their merits", q_sem)
        self.assertIn("git commit --no-edit", q_sem)
        self.assertNotIn("git commit -- <", q_sem)
        self.assertNotIn("git commit -- ", q_sem)
        self.assertNotIn("aw commit", q_sem)


class DriverConflictSendbackTests(unittest.TestCase):
    """Driver-level outcome tests for merge conflict send-back across both hosts (E-08)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_driver_fixture(
        self, td: str, id6: str = "wir001", retry_budget: int = 2
    ) -> tuple[pathlib.Path, pathlib.Path, dict, dict]:
        repo = pathlib.Path(td) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
        )
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")

        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        plan_text = _CONFORMING_PLAN.format(id6=id6)
        plan_text = plan_text.replace(
            "Scope-Paths: src/demo.txt", "Scope-Paths: clash.txt"
        )
        plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
        plan.write_text(plan_text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)

        item = {
            "position": 1,
            "id6": id6,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "agy": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": True,
                "retry_budget": retry_budget,
            },
        }
        return repo, run_dir, state, item

    def _passing_suite(self, repo: pathlib.Path) -> runner_shared.SuiteCheckResult:
        return runner_shared.SuiteCheckResult(
            passing=True,
            reason="ok",
            exit_code=0,
            summary="ok",
            cwd=str(repo),
            timeout_seconds=60.0,
            elapsed_seconds=0.1,
        )

    def test_case_a_fake_resolves_properly_integrates_both_lines(self):
        """Case (a): fake resolves properly -> integrates both lines, merge-conflict-resolved emitted,
        exactly 1 ask, finalize called once."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(td)
                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        (pathlib.Path(work_dir) / "clash.txt").write_text(
                            "main line\nlane line\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "--", "clash.txt"], cwd=work_dir, check=True
                        )
                        subprocess.run(
                            ["git", "commit", "--no-edit"], cwd=work_dir, check=True
                        )
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    # Execution turn: lane writes clash.txt
                    target_dir = pathlib.Path(work_dir)
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    # Main also commits a conflicting clash.txt
                    (repo / "clash.txt").write_text("main line\n", encoding="utf-8")
                    subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                finalize_calls = 0
                driver_mod = _MODULES[runner]
                orig_finalize = driver_mod.driver_finalize

                def spy_finalize(*a, **k):
                    nonlocal finalize_calls
                    finalize_calls += 1
                    return orig_finalize(*a, **k)

                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod, "driver_finalize", spy_finalize
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "executed")
                self.assertEqual(ask_count, 1)
                self.assertEqual(
                    finalize_calls, 1, "finalize must not be called a second time"
                )
                self.assertEqual(
                    (repo / "clash.txt").read_text(encoding="utf-8"),
                    "main line\nlane line\n",
                )

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                event_names = [e.get("event") for e in events]
                self.assertIn("merge-conflict-sent-back", event_names)
                self.assertIn("merge-conflict-resolved", event_names)

                att = item["attempts"][0]
                sendback = att.get("merge_conflict_sendback")
                self.assertTrue(sendback)
                self.assertTrue(sendback[0].get("consummated"))
                self.assertTrue(sendback[0].get("resolved"))

    def test_case_b_fake_does_nothing_fails_merge_and_cleans_lane(self):
        """Case (b): fake does nothing -> after retry budget asks, ends fail-merge, main unchanged,
        lane preserved with NO merge in progress (aborted), merge-conflict-unresolved emitted."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=2
                )
                ask_count = 0
                lane_path_captured = None

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count, lane_path_captured
                    work_dir = kwargs.get("work_dir")
                    lane_path_captured = pathlib.Path(work_dir)
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        # fake does nothing
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    target_dir = pathlib.Path(work_dir)
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    (repo / "clash.txt").write_text("main line\n", encoding="utf-8")
                    subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "fail-merge")
                self.assertEqual(ask_count, 1)
                self.assertEqual(
                    (repo / "clash.txt").read_text(encoding="utf-8"), "main line\n"
                )

                # Lane worktree must have NO merge in progress (clean abort)
                self.assertIsNotNone(lane_path_captured)
                self.assertFalse(
                    runner_shared.merge_in_progress(lane_path_captured),
                    "Lane must have no MERGE_HEAD so human integration path remains usable",
                )

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                event_names = [e.get("event") for e in events]
                self.assertIn("merge-conflict-unresolved", event_names)
                self.assertIn("lane-merge-aborted", event_names)

    def test_case_c_retry_budget_zero_no_ask_fails_merge_immediately(self):
        """Case (c): --retry-budget 0 -> 0 asks, ends fail-merge immediately."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=0
                )
                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    target_dir = pathlib.Path(work_dir)
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    (repo / "clash.txt").write_text("main line\n", encoding="utf-8")
                    subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "fail-merge")
                self.assertEqual(
                    ask_count, 0, "Budget 0 must make 0 conflict resolution asks"
                )

    def test_case_d_unrelated_main_advance_integrates_without_agent_ask(self):
        """Case (d): main moved on an UNRELATED file so E-01's merge is clean -> item integrates with 0 asks."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(td)
                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    target_dir = pathlib.Path(work_dir)
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    # Main moves on UNRELATED file
                    (repo / "unrelated.txt").write_text(
                        "main unrelated\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "unrelated.txt"], cwd=repo, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "main unrelated"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )

                # Simulate a transient conflict refusal on first publish that E-01 cleanly merges
                publish_calls = 0
                orig_integrate_lane = driver_mod.integrate_lane_branch

                def wrapped_integrate_lane(r, handle, id6, val_r, **kwargs):
                    nonlocal publish_calls
                    publish_calls += 1
                    if publish_calls == 1:
                        # First publish refuses with properly tagged merge conflict
                        return (
                            False,
                            runner_shared.tag_integration_cause(
                                runner_shared.INTEGRATION_CAUSE_GIT_CONFLICT, "conflict"
                            ),
                            runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                        )
                    return orig_integrate_lane(r, handle, id6, val_r, **kwargs)

                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod, "integrate_lane_branch", wrapped_integrate_lane
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "executed")
                self.assertEqual(
                    ask_count, 0, "Clean lane merge must not ask the agent"
                )
                self.assertEqual(
                    (repo / "clash.txt").read_text(encoding="utf-8"), "lane line\n"
                )
                self.assertEqual(
                    (repo / "unrelated.txt").read_text(encoding="utf-8"),
                    "main unrelated\n",
                )

    def test_case_e_consummation_regression_commit_isolated_unresolved(self):
        """Case (e): THE CONSUMMATION REGRESSION: fake removes markers and commits via commit_isolated
        without concluding merge -> attempt counted UNRESOLVED, item does NOT integrate."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_driver_fixture(
                    td, retry_budget=1
                )
                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    log_suffix = kwargs.get("log_suffix", "")
                    if log_suffix == "merge-conflict":
                        ask_count += 1
                        # Remove markers, but commit via commit_isolated (F-7)
                        (pathlib.Path(work_dir) / "clash.txt").write_text(
                            "main line\nlane line\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "clash.txt"], cwd=work_dir, check=True
                        )
                        commit_lock.commit_isolated(
                            pathlib.Path(work_dir),
                            ["clash.txt"],
                            message="isolated resolution",
                        )
                        return 0, "ses1", str(rd / "conflict-log"), [runner]

                    target_dir = pathlib.Path(work_dir)
                    (target_dir / "clash.txt").write_text(
                        "lane line\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["git", "add", "clash.txt"], cwd=target_dir, check=True
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "lane clash"],
                        cwd=target_dir,
                        check=True,
                    )

                    (repo / "clash.txt").write_text("main line\n", encoding="utf-8")
                    subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "main clash"], cwd=repo, check=True
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    driver_mod,
                    "make_integration_validation_runner",
                    lambda *a, **k: (lambda _d, _f: True),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "fail-merge")
                self.assertEqual(ask_count, 1)

                att = item["attempts"][0]
                sendback = att.get("merge_conflict_sendback")
                self.assertTrue(sendback)
                # Conditions (i) and (ii) resolved, but condition (iii) consummated is False
                self.assertTrue(sendback[0].get("resolved"))
                self.assertFalse(sendback[0].get("consummated"))

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                    if line.strip()
                ]
                unresolved = [
                    e for e in events if e.get("event") == "merge-conflict-unresolved"
                ]
                self.assertTrue(unresolved)
                self.assertFalse(unresolved[0].get("consummated"))

    def test_case_e_consummation_check_non_vacuous(self):
        """Regression proof for V-08: a two-condition checker (omitting condition iii) wrongly passes
        case (e)'s unconcluded commit_isolated resolution, while the full three-condition check catches it."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            repo = root / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@e.i"], cwd=repo, check=True
            )
            subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
            )
            (repo / "clash.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            lane = root / "lane"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "aw/lane/demo",
                    str(lane),
                    "HEAD",
                ],
                cwd=repo,
                check=True,
            )
            (lane / "clash.txt").write_text("lane\n", encoding="utf-8")
            subprocess.run(["git", "add", "clash.txt"], cwd=lane, check=True)
            subprocess.run(["git", "commit", "-qm", "lane edit"], cwd=lane, check=True)

            (repo / "clash.txt").write_text("main\n", encoding="utf-8")
            subprocess.run(["git", "add", "clash.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "main edit"], cwd=repo, check=True)
            main_tip = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            handle = type("H", (), {"path": lane, "base_commit": ""})()
            prep = runner_shared.prepare_lane_for_conflict_resolution(
                repo, handle, main_tip=main_tip
            )
            self.assertTrue(prep.ok)

            # Agent removes markers, stages file, and runs commit_isolated (F-7)
            (lane / "clash.txt").write_text("resolved\n", encoding="utf-8")
            subprocess.run(["git", "add", "clash.txt"], cwd=lane, check=True)
            commit_lock.commit_isolated(
                lane, ["clash.txt"], message="isolated resolution"
            )

            # 1. Two-condition checker (conditions i and ii only)
            rc_u, out_u, _ = runner_shared._run_git(
                lane, ["diff", "--name-only", "--diff-filter=U"]
            )
            rc_g, out_g, _ = runner_shared._run_git(
                lane, ["grep", "-nE", "^(<<<<<<<|>>>>>>>)", "--", "clash.txt"]
            )
            two_condition_pass = (rc_u == 0 and not out_u.strip()) and (
                rc_g == 1 or (rc_g == 0 and not out_g.strip())
            )
            self.assertTrue(
                two_condition_pass,
                "Two-condition check wrongly passes without condition (iii)",
            )

            # 2. Three-condition checker (check_conflict_resolution_consummated)
            resolved, consummated = runner_shared.check_conflict_resolution_consummated(
                lane, prep.conflicted_paths, prep.merge_head
            )
            self.assertTrue(resolved, "Conditions (i) and (ii) pass")
            self.assertFalse(
                consummated,
                "Condition (iii) fails: merge is still in progress / main not ancestor",
            )


if __name__ == "__main__":
    unittest.main()

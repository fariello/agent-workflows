"""Tests for isolated attempt lane facts recording (IPD s6ne9d).

Behavioral tests verifying:
(1) OC host integrated isolated turn records lane facts (lane_starting_head == base,
    lane_ending_head != lane_starting_head, diff includes src/demo.txt, ending_head == lane_ending_head post-merge).
(2) OC host refused isolated turn records lane facts (fail-merge, starting_head == ending_head,
    ending_status == '', lane_ending_head != lane_starting_head containing src/demo.txt and finalize commit).
(3) AGY host integrated isolated turn records lane facts.
(4) Non-isolated turn (isolate_worktree: False) carries none of the three lane keys.
(5) collect_earned_paths prefers lane_starting_head..lane_ending_head over starting_head..ending_head.
(6) prior_attempt_summary allowlist keeps the three lane keys, drops worktree/log/prompt,
    and absolute_paths_outside_lane finds no out-of-lane path in a recovery prompt with lane_ending_status.
(7) Removed-lane guard leaves previously recorded lane values in place without raising.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared
from tests import support
from tests.test_agy_runipd_cli import _init_repo_with_conforming_plan as _init_agy_plan
from tests.test_oc_runipd import _init_repo_with_conforming_plan as _init_oc_plan


class AttemptLaneFactsTests(unittest.TestCase):
    """Behavioral tests verifying lane facts recorded on isolated attempt records."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        return run_dir

    def _oc_state_and_item(
        self, repo: Path, plan: Path, *, isolate: bool = True
    ) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "wir001",
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
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": isolate,
                "no_audit": False,
            },
        }
        return state, item

    def _fake_oc_agent_commits_in_worktree(self, run_dir: Path):
        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]

            target_dir = Path(work_dir) if work_dir else Path(state["repo"])
            (target_dir / "src").mkdir(parents=True, exist_ok=True)
            (target_dir / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=target_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=target_dir,
                check=True,
            )
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def _agy_state_and_item(
        self, repo: Path, plan: Path, *, isolate: bool = True
    ) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "agy001",
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
                "agy": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": isolate,
                "no_audit": False,
            },
        }
        return state, item

    def _fake_agy_agent_commits_in_worktree(self, run_dir: Path):
        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
                (run_dir / "outcomes" / "01-agy001-verification.json").write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["agy"]

            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=wt,
                check=True,
            )
            (run_dir / "outcomes" / "01-agy001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def test_case_1_oc_host_integrated_isolated_turn(self):
        """Case 1: OC host integrated isolated turn records lane facts."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_oc_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan)
            fake_agent = self._fake_oc_agent_commits_in_worktree(run_dir)
            main_head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            with mock.patch.object(oc_runipd, "run_opencode", fake_agent):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed")
            att = item["attempts"][0]
            self.assertEqual(att.get("starting_head"), main_head_before)
            self.assertEqual(att.get("lane_starting_head"), att.get("worktree_base"))
            self.assertNotEqual(
                att.get("lane_ending_head"), att.get("lane_starting_head")
            )
            # ending_head == lane_ending_head here only because integration succeeded and
            # re-recorded ending_head post-merge (PR-003):
            self.assertEqual(att.get("ending_head"), att.get("lane_ending_head"))

            sh = att["lane_starting_head"]
            eh = att["lane_ending_head"]
            diff = subprocess.run(
                ["git", "diff", "--name-only", f"{sh}..{eh}"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.splitlines()
            self.assertIn("src/demo.txt", diff)

    def test_case_2_oc_host_refused_isolated_turn(self):
        """Case 2: OC host refused isolated turn records lane facts even when main did not move."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_oc_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan)
            fake_agent = self._fake_oc_agent_commits_in_worktree(run_dir)
            main_head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            with mock.patch.object(
                oc_runipd, "run_opencode", fake_agent
            ), mock.patch.object(
                oc_runipd,
                "make_integration_validation_runner",
                lambda *a, **k: (lambda _d, _f: False),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            att = item["attempts"][0]
            self.assertEqual(att.get("starting_head"), main_head_before)
            self.assertEqual(att.get("ending_head"), main_head_before)
            self.assertEqual(att.get("starting_head"), att.get("ending_head"))
            self.assertEqual(att.get("ending_status"), "")

            self.assertIn("lane_starting_head", att)
            self.assertIn("lane_ending_head", att)
            self.assertIn("lane_ending_status", att)
            self.assertEqual(att.get("lane_starting_head"), att.get("worktree_base"))
            self.assertNotEqual(
                att.get("lane_ending_head"), att.get("lane_starting_head")
            )

            sh = att["lane_starting_head"]
            eh = att["lane_ending_head"]
            log = subprocess.run(
                ["git", "log", "--format=%s", f"{sh}..{eh}"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.splitlines()
            self.assertTrue(any("finalize wir001 -> executed" in msg for msg in log))
            self.assertTrue(
                any("create src/demo.txt" in msg or "demo" in msg for msg in log)
            )

    def test_case_3_agy_host_integrated_isolated_turn(self):
        """Case 3: AGY host integrated isolated turn records lane facts."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_agy_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._agy_state_and_item(repo, plan)
            fake_agent = self._fake_agy_agent_commits_in_worktree(run_dir)
            main_head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            with mock.patch.object(agy_runipd, "run_agy_turn", fake_agent):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "executed")
            att = item["attempts"][0]
            self.assertEqual(att.get("starting_head"), main_head_before)
            self.assertEqual(att.get("lane_starting_head"), att.get("worktree_base"))
            self.assertNotEqual(
                att.get("lane_ending_head"), att.get("lane_starting_head")
            )
            self.assertEqual(att.get("ending_head"), att.get("lane_ending_head"))

            sh = att["lane_starting_head"]
            eh = att["lane_ending_head"]
            diff = subprocess.run(
                ["git", "diff", "--name-only", f"{sh}..{eh}"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.splitlines()
            self.assertIn("src/demo.txt", diff)

    def test_case_4_non_isolated_turn_carries_none_of_the_three_keys(self):
        """Case 4: Non-isolated turn (isolate_worktree: False) carries none of the three lane keys."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_oc_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan, isolate=False)
            fake_agent = self._fake_oc_agent_commits_in_worktree(run_dir)

            with mock.patch.object(oc_runipd, "run_opencode", fake_agent):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            att = item["attempts"][0]
            self.assertNotIn("lane_starting_head", att)
            self.assertNotIn("lane_ending_head", att)
            self.assertNotIn("lane_ending_status", att)

    def test_case_5_collect_earned_paths_prefers_lane_range(self):
        """Case 5: collect_earned_paths prefers lane range over main range when present and differing."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            base_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            # Create a branch with a commit
            subprocess.run(
                ["git", "checkout", "-qb", "test-lane"], cwd=repo, check=True
            )
            (repo / "lane_file.txt").write_text("lane\n", encoding="utf-8")
            subprocess.run(["git", "add", "lane_file.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "lane commit"], cwd=repo, check=True
            )
            lane_tip = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            subprocess.run(["git", "checkout", "-q", "-"], cwd=repo, check=True)

            def _rc(cmd, **kw):
                return subprocess.run(
                    cmd, text=True, capture_output=True, check=True, **kw
                ).stdout

            # Item with starting_head == ending_head but lane_starting_head != lane_ending_head
            item_with_lane = {
                "attempts": [
                    {
                        "starting_head": base_head,
                        "ending_head": base_head,
                        "lane_starting_head": base_head,
                        "lane_ending_head": lane_tip,
                    }
                ]
            }
            earned = runner_shared.collect_earned_paths(
                repo, item_with_lane, run_checked=_rc
            )
            self.assertEqual(earned, ["lane_file.txt"])

            # Item without lane keys: starting_head == ending_head returns []
            item_without_lane = {
                "attempts": [
                    {
                        "starting_head": base_head,
                        "ending_head": base_head,
                    }
                ]
            }
            earned_no_lane = runner_shared.collect_earned_paths(
                repo, item_without_lane, run_checked=_rc
            )
            self.assertEqual(earned_no_lane, [])

    def test_case_6_prior_attempt_summary_and_path_hygiene(self):
        """Case 6: prior_attempt_summary keeps lane keys, drops out-of-lane paths, prompt has no out-of-lane paths."""
        prior = {
            "number": 1,
            "starting_head": "111111",
            "ending_head": "222222",
            "lane_starting_head": "333333",
            "lane_ending_head": "444444",
            "lane_ending_status": " M src/demo.txt\n?? src/untracked.txt\n",
            "worktree": "/driver/absolute/worktree",
            "log": "/driver/absolute/log.txt",
            "prompt": "/driver/absolute/prompt.txt",
        }
        lane_root = Path("/tmp/fake-lane")
        summary = lane_containment.prior_attempt_summary(prior, lane_root=lane_root)
        self.assertIsNotNone(summary)
        assert summary is not None

        # Lane keys kept
        self.assertEqual(summary.get("lane_starting_head"), "333333")
        self.assertEqual(summary.get("lane_ending_head"), "444444")
        self.assertEqual(
            summary.get("lane_ending_status"),
            " M src/demo.txt\n?? src/untracked.txt\n",
        )
        # Driver-side absolute path keys dropped
        self.assertNotIn("worktree", summary)
        self.assertNotIn("log", summary)
        self.assertNotIn("prompt", summary)

        # Prompt rendering with realistic lane_ending_status contains no out-of-lane absolute paths
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_oc_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan)
            lane_root = repo
            summary = lane_containment.prior_attempt_summary(prior, lane_root=lane_root)
            item["attempts"] = [summary]
            rendered_prompt = runner_shared.build_prompt(
                item,
                state,
                run_dir,
                plan,
                recovery=True,
                lane_root=lane_root,
                labels=runner_shared.OC_HOST_LABELS,
            )
            offenders = lane_containment.absolute_paths_outside_lane(
                rendered_prompt, lane_root
            )
            self.assertEqual(
                offenders,
                [],
                f"Recovery prompt should not contain out-of-lane paths: {offenders}",
            )

    def test_case_7_removed_lane_leaves_post_turn_value_in_place(self):
        """Case 7: removed or missing lane worktree leaves previously recorded lane values in place."""
        attempt = {
            "lane_ending_head": "preserved_head_123456",
            "lane_ending_status": "preserved_status_ok",
        }
        # Call with nonexistent directory; git_head / git_status raise or path missing
        runner_shared._record_lane_ending_facts(
            attempt,
            Path("/nonexistent/path/that/does/not/exist"),
            git_head_fn=oc_runipd.git_head,
            git_status_fn=oc_runipd.git_status,
        )
        self.assertEqual(attempt["lane_ending_head"], "preserved_head_123456")
        self.assertEqual(attempt["lane_ending_status"], "preserved_status_ok")

        # Also verify with mock git functions that raise DriverError or OSError
        def _failing_head(_path):
            raise runner_shared.DriverError("git failed")

        def _failing_status(_path):
            raise OSError("os error")

        runner_shared._record_lane_ending_facts(
            attempt,
            "/some/path",
            git_head_fn=_failing_head,
            git_status_fn=_failing_status,
        )
        self.assertEqual(attempt["lane_ending_head"], "preserved_head_123456")
        self.assertEqual(attempt["lane_ending_status"], "preserved_status_ok")


if __name__ == "__main__":
    unittest.main()

"""Behavioral tests for resolve_plan_path type-checking, exact id6 matching, and narrowed glob fallback.

WHAT THIS FILE PROVES (IPD mxzogk):
`runner_shared.resolve_plan_path` must return only a real IPD plan (exact `- Id:` match,
or a configured path that is a plan by discover_plans' membership rule and detect_artifact_type == "plans",
or a plans-tree file claiming the id6) and otherwise raise DriverError.

FAIL AGAINST PRE-CHANGE FUNCTION (PROOFS):
  (1)  configured = plans README -> raises DriverError naming a plans index file
  (2)  configured = .spec.md path -> raises DriverError naming a specs
  (3)  configured = root AGENTS.md with child kind -> raises DriverError naming outside the plans trees
  (4)  id6 in slug but foreign - Id: -> raises DriverError (Cannot locate IPD)
  (5b) worktree and baseline copies without real plan in plans tree -> raises DriverError (Cannot locate IPD)
  (6)  two plans mentioning id6 mid-slug with foreign - Id: -> raises DriverError (Cannot locate IPD)
  (10) dispatch: queue item with spec path refused before spawn for review & execute, run_queue continues

PASS BOTH BEFORE AND AFTER (GUARDS):
  (5a) worktree and baseline copies with real plan in plans tree -> resolves real plan
  (7)  pending plan resolves, and after move to executed/ still resolves
  (8)  lane copy returned when lane passed as repo
  (9)  legacy slot-only plan found by glob fallback
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import oc_runipd, runner_shared
from tests import support


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True
    )


class ResolvePlanPathTypedTests(unittest.TestCase):
    """Behavioral tests for resolve_plan_path: type checks, exact declaration, and glob scope."""

    def test_01_configured_plans_readme_raises_plans_index_file(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            plans_dir = repo / ".aw" / "records" / "plans"
            plans_dir.mkdir(parents=True)
            readme = plans_dir / "README.md"
            readme.write_text("# Plans\n", encoding="utf-8")
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(
                    repo, ".aw/records/plans/README.md", "zzzzzz"
                )
            msg = str(cm.exception)
            self.assertIn("a plans index file", msg)
            self.assertIn("not an IPD plan", msg)

    def test_02_configured_spec_path_raises_spec_type(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            specs_dir = repo / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_file = (
                specs_dir
                / "20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md"
            )
            spec_file.write_text(
                "# Spec\n\n- Id: 4sd62s\n- Status: approved\n", encoding="utf-8"
            )
            rel_path = str(spec_file.relative_to(repo))
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(repo, rel_path, "4sd62s")
            msg = str(cm.exception)
            self.assertIn("a specs", msg)
            self.assertIn("not an IPD plan", msg)

    def test_03_configured_agents_md_raises_outside_plans_trees(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            agents_md = repo / "AGENTS.md"
            agents_md.write_text("# AGENTS\n\n- Kind: child\n", encoding="utf-8")
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(repo, "AGENTS.md", "ag0001")
            msg = str(cm.exception)
            self.assertIn("outside the plans trees", msg)
            self.assertIn("not an IPD plan", msg)

    def test_04_id6_only_in_another_plan_slug_raises_cannot_locate(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            plan = pending_dir / "20260101-demo-01-zzz999-adopt-spec-abc123.ipd.md"
            plan.write_text(
                "- Id: zzz999\n- Set: demo\n- Status: pending\n# IPD: demo\n",
                encoding="utf-8",
            )
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(repo, "", "abc123")
            msg = str(cm.exception)
            self.assertIn("Cannot locate IPD abc123", msg)

    def test_05a_guard_worktree_and_baseline_copies_do_not_ambiguate_real_plan(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            real_plan = pending_dir / "20260101-set-01-abc123-real-plan.ipd.md"
            content = "- Id: abc123\n- Set: set\n- Status: approved\n# Real Plan\n"
            real_plan.write_text(content, encoding="utf-8")

            # Copy under worktree
            wt_dir = (
                repo
                / ".aw"
                / "worktrees"
                / "lane1"
                / ".aw"
                / "records"
                / "plans"
                / "pending"
            )
            wt_dir.mkdir(parents=True)
            (wt_dir / real_plan.name).write_text(content, encoding="utf-8")

            # Copy under suite-baselines
            sb_dir = repo / ".aw" / "state" / "suite-baselines" / "base1"
            sb_dir.mkdir(parents=True)
            (sb_dir / real_plan.name).write_text(content, encoding="utf-8")

            resolved = runner_shared.resolve_plan_path(repo, "", "abc123")
            self.assertEqual(resolved, real_plan.resolve())

    def test_05b_worktree_and_baseline_copies_without_real_plan_raises_cannot_locate(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            content = "- Id: abc123\n- Set: set\n- Status: approved\n# Plan\n"

            # Copies ONLY under worktree and baseline, NO file in repo's plans tree
            wt_dir = (
                repo
                / ".aw"
                / "worktrees"
                / "lane1"
                / ".aw"
                / "records"
                / "plans"
                / "pending"
            )
            wt_dir.mkdir(parents=True)
            (wt_dir / "20260101-set-01-abc123-foo.ipd.md").write_text(
                content, encoding="utf-8"
            )

            sb_dir = repo / ".aw" / "state" / "suite-baselines" / "base1"
            sb_dir.mkdir(parents=True)
            (sb_dir / "20260101-set-01-abc123-foo.ipd.md").write_text(
                content, encoding="utf-8"
            )

            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(repo, "", "abc123")
            msg = str(cm.exception)
            self.assertIn("Cannot locate IPD abc123", msg)

    def test_06_two_plans_mentioning_id6_mid_slug_do_not_produce_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            p1 = pending_dir / "20260101-set-01-zzz999-adopt-abc123-spec.ipd.md"
            p1.write_text(
                "- Id: zzz999\n- Set: set\n- Status: approved\n# P1\n", encoding="utf-8"
            )
            p2 = pending_dir / "20260101-set-01-yyy888-revisit-abc123-again.ipd.md"
            p2.write_text(
                "- Id: yyy888\n- Set: set\n- Status: approved\n# P2\n", encoding="utf-8"
            )

            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.resolve_plan_path(repo, "", "abc123")
            msg = str(cm.exception)
            self.assertIn("Cannot locate IPD abc123", msg)

    def test_07_guard_pending_plan_resolves_and_after_move_to_executed_still_resolves(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            executed_dir = repo / ".aw" / "records" / "plans" / "executed"
            pending_dir.mkdir(parents=True)
            executed_dir.mkdir(parents=True)

            plan_p = pending_dir / "20260827-testset-01-xyz999-test-plan.ipd.md"
            plan_p.write_text(
                "- Id: xyz999\n- Set: testset\n- Status: approved\n# Test Plan\n",
                encoding="utf-8",
            )
            configured = (
                ".aw/records/plans/pending/20260827-testset-01-xyz999-test-plan.ipd.md"
            )
            found_pending = runner_shared.resolve_plan_path(repo, configured, "xyz999")
            self.assertEqual(found_pending, plan_p.resolve())

            plan_e = executed_dir / "20260827-testset-01-xyz999-test-plan.ipd.md"
            plan_p.rename(plan_e)
            found_executed = runner_shared.resolve_plan_path(repo, configured, "xyz999")
            self.assertEqual(found_executed, plan_e.resolve())

    def test_08_guard_lane_copy_returned_when_lane_passed_as_repo(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            lane = repo / ".aw" / "worktrees" / "aaaaaa"
            rel = ".aw/records/plans/pending/20260101-s-01-aaaaaa-x.ipd.md"
            for root in (repo, lane):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("# IPD: x\n\n- Id: aaaaaa\n", encoding="utf-8")
            lane_plan = runner_shared.resolve_plan_path(lane, rel, "aaaaaa")
            self.assertTrue(str(lane_plan).startswith(str(lane)))
            self.assertEqual(lane_plan, (lane / rel).resolve())

    def test_09_guard_legacy_slot_only_plan_found_by_glob(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            # Legacy slot-only: no "- Id:", id6 in filename slot
            plan = pending_dir / "20260101-legset-01-leg123-legacy-plan.ipd.md"
            plan.write_text(
                "# Legacy Plan\n\n- Set: legset\n- Status: approved\n", encoding="utf-8"
            )
            found = runner_shared.resolve_plan_path(repo, "", "leg123")
            self.assertEqual(found, plan.resolve())


class DispatchRefusalTests(unittest.TestCase):
    """Dispatch refusal tests for non-plan configured_file items."""

    def setUp(self):
        support.declare_execution_role(self)

    def test_10a_dispatch_refusal_execute_item_review_action(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            specs_dir = repo / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_file = specs_dir / "20260926-0001-01-tst001-test-spec.spec.md"
            spec_file.write_text(
                "- Id: tst001\n- Status: to-review\n# Spec\n", encoding="utf-8"
            )
            _init_git_repo(repo)
            rel_spec = str(spec_file.relative_to(repo))

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            item = {
                "position": 1,
                "id6": "tst001",
                "setid": "standalone",
                "status": "queued",
                "configured_file": rel_spec,
                "action": "review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {"action": "review", "isolate_worktree": False},
            }

            mock_spawn = mock.Mock(
                side_effect=AssertionError("spawn must not be called")
            )
            with (
                mock.patch.object(oc_runipd, "run_opencode", mock_spawn),
                self.assertRaises(runner_shared.DriverError) as cm,
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)
            self.assertIn("a specs", str(cm.exception))
            mock_spawn.assert_not_called()

    def test_10b_dispatch_refusal_execute_item_execute_action(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            specs_dir = repo / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_file = specs_dir / "20260926-0001-01-tst001-test-spec.spec.md"
            spec_file.write_text(
                "- Id: tst001\n- Status: approved\n# Spec\n", encoding="utf-8"
            )
            _init_git_repo(repo)
            rel_spec = str(spec_file.relative_to(repo))

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            item = {
                "position": 1,
                "id6": "tst001",
                "setid": "standalone",
                "status": "queued",
                "configured_file": rel_spec,
                "action": "execute",
                "attempts": [],
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {"action": "execute", "isolate_worktree": False},
            }

            mock_spawn = mock.Mock(
                side_effect=AssertionError("spawn must not be called")
            )
            with (
                mock.patch.object(oc_runipd, "run_opencode", mock_spawn),
                self.assertRaises(runner_shared.DriverError) as cm,
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)
            self.assertIn("a specs", str(cm.exception))
            mock_spawn.assert_not_called()

    def test_10c_dispatch_refusal_run_queue_multi_item(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td).resolve()
            specs_dir = repo / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            spec_file = specs_dir / "20260926-0001-01-tst001-test-spec.spec.md"
            spec_file.write_text(
                "- Id: tst001\n- Status: approved\n# Spec\n", encoding="utf-8"
            )

            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            plan_file = plans_dir / "20260926-demo-01-pl0002-real-plan.ipd.md"
            plan_file.write_text(
                "- Id: pl0002\n- Set: demo\n- Status: approved\n# IPD: Demo\n",
                encoding="utf-8",
            )
            _init_git_repo(repo)

            rel_spec = str(spec_file.relative_to(repo))
            rel_plan = str(plan_file.relative_to(repo))

            item1 = {
                "position": 1,
                "id6": "tst001",
                "setid": "standalone",
                "status": "queued",
                "configured_file": rel_spec,
                "action": "review",
                "attempts": [],
                "dependencies": [],
            }
            item2 = {
                "position": 2,
                "id6": "pl0002",
                "setid": "demo",
                "status": "queued",
                "configured_file": rel_plan,
                "action": "execute",
                "attempts": [],
                "dependencies": [],
            }
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
            state = {
                "schema_version": 1,
                "run_id": "run-test",
                "created_at": "2026-08-24T00:00:00+00:00",
                "updated_at": "2026-08-24T00:00:00+00:00",
                "repo": str(repo),
                "selectors": ["demo"],
                "queue": [item1, item2],
                "set_sessions": {},
                "options": {
                    "opencode": "/bin/false",
                    "model": None,
                    "agent": None,
                    "auto": True,
                    "isolate_worktree": False,
                },
            }
            oc_runipd.save_state(run_dir, state)

            opencode_calls = []

            def fake_opencode(
                st, rdir, itm, plan_path, prompt_path, attempt_no, **kwargs
            ):
                opencode_calls.append(itm["id6"])
                outcome_file = (
                    rdir / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                )
                outcome_file.write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                v_outcome_file = (
                    rdir
                    / "outcomes"
                    / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                )
                v_outcome_file.write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": ["python3 -m unittest tests/test_foo.py"],
                        }
                    ),
                    encoding="utf-8",
                )
                if kwargs.get("fresh_session") or kwargs.get("log_suffix") == "verify":
                    return 0, "ses_verify", str(rdir / "log"), ["oc"]
                return 0, "ses", str(rdir / "log"), ["oc"]

            with (
                mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
                mock.patch.object(
                    oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")
                ),
                mock.patch.object(oc_runipd, "run_opencode", fake_opencode),
                mock.patch.object(oc_runipd, "run_suite_check", lambda *a, **k: True),
            ):
                oc_runipd.run_queue(run_dir, retry_incomplete=False)

            saved_state = oc_runipd.load_state(run_dir)
            q1 = saved_state["queue"][0]
            q2 = saved_state["queue"][1]

            # Item 1 was refused at dispatch without spawning
            self.assertEqual(q1["status"], "failed-safely")
            self.assertIn("a specs", q1.get("driver_error", ""))

            # Item 2 completed
            self.assertEqual(q2["status"], "executed")

            # Spawn was called for item 2 only (0 calls for item 1)
            self.assertEqual(opencode_calls.count("tst001"), 0)
            self.assertGreaterEqual(opencode_calls.count("pl0002"), 1)


if __name__ == "__main__":
    unittest.main()

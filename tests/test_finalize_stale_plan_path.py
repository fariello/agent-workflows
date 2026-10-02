"""Behavioral tests for refusing stale plan path at finalize and downstream gates (1fzist).

Tests outcomes, not code structure (no inspect/ast/regex on production source,
and no reading from gitignored .aw/records/runs/).
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import ipd_lifecycle, oc_runipd, render_stream, runner_shared


class TestFinalizeStalePlanPath(unittest.TestCase):
    """Behavioral tests covering all five deliverables of IPD 1fzist."""

    # -------------------------------------------------------------------------
    # (a) E-02: execute_item_core refuses when finalize re-resolution fails
    # -------------------------------------------------------------------------

    def _setup_repo_and_plan(
        self, tpath: Path, id6: str = "1fz001"
    ) -> tuple[Path, Path]:
        """Create a minimal git repo with an IPD file and initial commit."""
        repo = tpath / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", str(repo)], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.name", "Tester"], check=True
        )
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
            check=True,
        )

        plan_dir = repo / ".aw/records/plans/pending"
        plan_dir.mkdir(parents=True)
        plan_path = plan_dir / f"20260930-rfhiu2-01-{id6}-test-plan.ipd.md"
        plan_path.write_text(
            f"# IPD: Test Plan\n\n- Id: {id6}\n- Set: rfhiu2\n- Status: approved\n\n## Goal\nTest.\n",
            encoding="utf-8",
        )

        dummy = repo / "README.md"
        dummy.write_text("hello", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)
        return repo, plan_path

    def test_a1_lane_arm_refuses_when_finalize_re_resolution_fails(self) -> None:
        """(a) Lane arm: when resolve_plan_path fails for finalize, record refusal, skip finalize, disposition fail-gate."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo, plan_path = self._setup_repo_and_plan(tpath, id6="1fz001")
            run_dir = tpath / "run"
            run_dir.mkdir()
            (run_dir / "outcomes").mkdir()
            (run_dir / "logs").mkdir()
            (run_dir / "prompts").mkdir()

            item = {
                "id6": "1fz001",
                "setid": "rfhiu2",
                "action": "execute",
                "position": 1,
                "configured_file": str(plan_path),
                "status": "queued",
                "attempts": [],
            }
            state = {
                "options": {
                    "isolate_worktree": True,
                    "validate": True,
                    "self_finalize": True,
                },
                "repo": str(repo),
                "run_id": "run-test-lane",
                "queue": [item],
            }

            in_finalize = [False]

            def mock_executor(
                *args: object, **kwargs: object
            ) -> tuple[int, str, Path, list[str]]:
                work_dir = kwargs.get("work_dir") or (
                    args[1] if len(args) > 1 else None
                )
                wt = Path(work_dir) if work_dir else repo
                (wt / "change.txt").write_text("work done\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(wt), "add", "."], check=True)
                subprocess.run(
                    ["git", "-C", str(wt), "commit", "-m", "lane work"], check=True
                )

                outcome = run_dir / "outcomes/01-1fz001.json"
                outcome.write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "defect_report": {"state": "none-found", "findings": []},
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                (run_dir / "outcomes/01-1fz001-verification.json").write_text(
                    json.dumps(
                        {"verdict": "verified", "tests_run": ["python3 -m pytest"]}
                    ),
                    encoding="utf-8",
                )
                log_p = run_dir / "logs/test.log"
                log_p.write_text("test log", encoding="utf-8")
                return 0, "session-1", log_p, ["agent"]

            def mock_verifier(
                *args: object, **kwargs: object
            ) -> tuple[int, str, Path | None, list[str]]:
                in_finalize[0] = True
                (run_dir / "outcomes/01-1fz001-verification.json").write_text(
                    json.dumps(
                        {"verdict": "verified", "tests_run": ["python3 -m pytest"]}
                    ),
                    encoding="utf-8",
                )
                return 0, "vsession", None, []

            real_resolve = runner_shared.resolve_plan_path

            def fake_resolve(r: Path, c: str, i: str) -> Path:
                if in_finalize[0]:
                    raise runner_shared.DriverError(
                        f"cannot resolve plan {i} for finalize"
                    )
                return real_resolve(r, c, i)

            driver_finalize_spy = mock.Mock(return_value=(0, "ok"))

            with mock.patch(
                "agent_workflows.runner_shared.driver_begin", return_value=(0, "ok")
            ):
                with mock.patch(
                    "agent_workflows.runner_shared.resolve_plan_path",
                    side_effect=fake_resolve,
                ):
                    with mock.patch.object(
                        oc_runipd, "driver_finalize", driver_finalize_spy
                    ):
                        with mock.patch(
                            "agent_workflows.runner_shared.driver_finalize",
                            driver_finalize_spy,
                        ):
                            runner_shared.execute_item_core(
                                run_dir,
                                state,
                                item,
                                recovery=False,
                                host_labels=runner_shared.OC_HOST_LABELS,
                                spawn_executor=mock_executor,
                                spawn_verifier=mock_verifier,
                                raw_launcher=lambda *a, **k: None,
                                run_suite_check=lambda p, s: None,
                                process_backlog_close=lambda *a, **k: None,
                                driver_module=oc_runipd,
                            )

            # Assertions after execute_item_core returns (end of turn)
            driver_finalize_spy.assert_not_called()
            self.assertEqual(item.get("status"), "fail-gate")
            self.assertEqual(
                item.get("attempts", [{}])[-1].get("disposition"), "fail-gate"
            )
            refusal = render_stream.refusal_of_item(item)
            expected_code = getattr(
                runner_shared,
                "FINALIZE_PLAN_UNRESOLVABLE_CODE",
                "finalize-plan-unresolvable",
            )
            self.assertIsNotNone(
                refusal, "item must carry a recorded refusal at end of turn"
            )
            self.assertEqual(refusal.code, expected_code)
            self.assertTrue(plan_path.exists(), "plan file must not have been moved")

    def test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails(self) -> None:
        """(a) Non-lane arm: when resolve_plan_path fails for finalize, record refusal, skip finalize, disposition fail-gate."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo, plan_path = self._setup_repo_and_plan(tpath, id6="1fz002")
            run_dir = tpath / "run"
            run_dir.mkdir()
            (run_dir / "outcomes").mkdir()
            (run_dir / "logs").mkdir()
            (run_dir / "prompts").mkdir()

            item = {
                "id6": "1fz002",
                "setid": "rfhiu2",
                "action": "execute",
                "position": 1,
                "configured_file": str(plan_path),
                "status": "queued",
                "attempts": [],
            }
            state = {
                "options": {
                    "isolate_worktree": False,
                    "validate": True,
                    "self_finalize": True,
                },
                "repo": str(repo),
                "run_id": "run-test-nonlane",
                "queue": [item],
            }

            in_finalize = [False]

            def mock_executor(
                *args: object, **kwargs: object
            ) -> tuple[int, str, Path, list[str]]:
                (repo / "change.txt").write_text("work done\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "commit", "-m", "repo work"], check=True
                )

                outcome = run_dir / "outcomes/01-1fz002.json"
                outcome.write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "defect_report": {"state": "none-found", "findings": []},
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                (run_dir / "outcomes/01-1fz002-verification.json").write_text(
                    json.dumps(
                        {"verdict": "verified", "tests_run": ["python3 -m pytest"]}
                    ),
                    encoding="utf-8",
                )
                log_p = run_dir / "logs/test.log"
                log_p.write_text("test log", encoding="utf-8")
                return 0, "session-1", log_p, ["agent"]

            def mock_verifier(
                *args: object, **kwargs: object
            ) -> tuple[int, str, Path | None, list[str]]:
                in_finalize[0] = True
                (run_dir / "outcomes/01-1fz002-verification.json").write_text(
                    json.dumps(
                        {"verdict": "verified", "tests_run": ["python3 -m pytest"]}
                    ),
                    encoding="utf-8",
                )
                return 0, "vsession", None, []

            real_resolve = runner_shared.resolve_plan_path

            def fake_resolve(r: Path, c: str, i: str) -> Path:
                if in_finalize[0]:
                    raise runner_shared.DriverError(
                        f"cannot resolve plan {i} for finalize"
                    )
                return real_resolve(r, c, i)

            driver_finalize_spy = mock.Mock(return_value=(0, "ok"))

            with mock.patch(
                "agent_workflows.runner_shared.driver_begin", return_value=(0, "ok")
            ):
                with mock.patch(
                    "agent_workflows.runner_shared.resolve_plan_path",
                    side_effect=fake_resolve,
                ):
                    with mock.patch.object(
                        oc_runipd, "driver_finalize", driver_finalize_spy
                    ):
                        with mock.patch(
                            "agent_workflows.runner_shared.driver_finalize",
                            driver_finalize_spy,
                        ):
                            runner_shared.execute_item_core(
                                run_dir,
                                state,
                                item,
                                recovery=False,
                                host_labels=runner_shared.OC_HOST_LABELS,
                                spawn_executor=mock_executor,
                                spawn_verifier=mock_verifier,
                                raw_launcher=lambda *a, **k: None,
                                run_suite_check=lambda p, s: None,
                                process_backlog_close=lambda *a, **k: None,
                                driver_module=oc_runipd,
                            )

            # Assertions after execute_item_core returns (end of turn)
            driver_finalize_spy.assert_not_called()
            self.assertEqual(item.get("status"), "fail-gate")
            self.assertEqual(
                item.get("attempts", [{}])[-1].get("disposition"), "fail-gate"
            )
            refusal = render_stream.refusal_of_item(item)
            expected_code = getattr(
                runner_shared,
                "FINALIZE_PLAN_UNRESOLVABLE_CODE",
                "finalize-plan-unresolvable",
            )
            self.assertIsNotNone(
                refusal, "item must carry a recorded refusal at end of turn"
            )
            self.assertEqual(refusal.code, expected_code)
            self.assertTrue(plan_path.exists(), "plan file must not have been moved")

    # -------------------------------------------------------------------------
    # (b) E-04: finalize_already_done existence and containment guards
    # -------------------------------------------------------------------------

    def test_b1_ghost_path_refuses_false_success(self) -> None:
        """(b1) Ghost path: nonexistent executed/-shaped path returns False and original nonzero exit code."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            subprocess.run(["git", "init", str(tpath)], check=True, capture_output=True)
            ghost = (
                tpath
                / ".aw/records/plans/executed/20260930-rfhiu2-01-ghost1-some-plan.ipd.md"
            )

            self.assertFalse(ghost.exists())
            already = runner_shared.finalize_already_done(tpath, ghost, "ghost1")
            self.assertFalse(
                already, "nonexistent plan must not be reported as already finalized"
            )

            rc, msg = runner_shared.finalize_outcome(
                tpath, ghost, "ghost1", 1, "refusal: no begin receipt"
            )
            self.assertEqual(
                rc, 1, "original nonzero returncode must survive for ghost path"
            )
            self.assertEqual(msg, "refusal: no begin receipt")

    def test_b2_wrong_tree_lane_worktree_refuses_false_success(self) -> None:
        """(b2) Wrong tree on real git worktree: plan exists in main but outside lane repo."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            main_repo = tpath / "main"
            main_repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main", str(main_repo)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(main_repo), "config", "user.name", "Tester"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(main_repo),
                    "config",
                    "user.email",
                    "test@example.com",
                ],
                check=True,
            )

            dummy = main_repo / "README.md"
            dummy.write_text("hello", encoding="utf-8")
            subprocess.run(["git", "-C", str(main_repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(main_repo), "commit", "-m", "init"], check=True
            )

            # branch lane before plan exists
            subprocess.run(
                ["git", "-C", str(main_repo), "branch", "lane-branch"], check=True
            )

            # create executed plan in main
            main_exec_dir = main_repo / ".aw/records/plans/executed"
            main_exec_dir.mkdir(parents=True)
            main_plan = main_exec_dir / "20260930-rfhiu2-01-tst001-some-plan.ipd.md"
            main_plan.write_text("# IPD\n- Id: tst001\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(main_repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(main_repo), "commit", "-m", "add executed plan"],
                check=True,
            )

            # add worktree for lane
            lane_repo = tpath / "lane"
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(main_repo),
                    "worktree",
                    "add",
                    str(lane_repo),
                    "lane-branch",
                ],
                check=True,
                capture_output=True,
            )

            self.assertTrue(main_plan.exists(), "substituted path exists in main")
            # Judged against lane repo: must answer False because main_plan is not contained in lane_repo
            already = runner_shared.finalize_already_done(
                lane_repo, main_plan, "tst001"
            )
            self.assertFalse(
                already,
                "plan outside the finalized repo must not be reported already-done",
            )

            rc, msg = runner_shared.finalize_outcome(
                lane_repo, main_plan, "tst001", 1, "refused: no begin receipt"
            )
            self.assertEqual(
                rc, 1, "nonzero exit code must survive when plan is in other tree"
            )
            self.assertEqual(msg, "refused: no begin receipt")

    def test_b_controls_same_tree_and_pending_cases(self) -> None:
        """(b controls) Executed plan inside repo yields 0, non-normalized yields 0, pending yields nonzero."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            subprocess.run(["git", "init", str(tpath)], check=True, capture_output=True)

            exec_dir = tpath / ".aw/records/plans/executed"
            exec_dir.mkdir(parents=True)
            exec_plan = exec_dir / "20260930-rfhiu2-01-tst002-lane-plan.ipd.md"
            exec_plan.write_text("# IPD\n- Id: tst002\n", encoding="utf-8")

            # Control 1: contained executed plan -> True and rc 0 (idempotent no-op)
            self.assertTrue(
                runner_shared.finalize_already_done(tpath, exec_plan, "tst002")
            )
            rc1, msg1 = runner_shared.finalize_outcome(
                tpath, exec_plan, "tst002", 1, "refused: no begin receipt"
            )
            self.assertEqual(rc1, 0)
            self.assertIn("finalize is a NO-OP", msg1)

            # Control 2: non-normalized spelling contained in repo -> True and rc 0
            non_norm_plan = (
                tpath
                / "sub/../.aw/records/plans/executed/20260930-rfhiu2-01-tst002-lane-plan.ipd.md"
            )
            (tpath / "sub").mkdir(exist_ok=True)
            self.assertTrue(
                runner_shared.finalize_already_done(tpath, non_norm_plan, "tst002")
            )
            rc2, msg2 = runner_shared.finalize_outcome(
                tpath, non_norm_plan, "tst002", 1, "refused: no begin receipt"
            )
            self.assertEqual(rc2, 0)
            self.assertIn("finalize is a NO-OP", msg2)

            # Control 3: pending plan -> False and rc unchanged
            pending_dir = tpath / ".aw/records/plans/pending"
            pending_dir.mkdir(parents=True)
            pending_plan = pending_dir / "20260930-rfhiu2-01-tst003-pending-plan.ipd.md"
            pending_plan.write_text("# IPD\n- Id: tst003\n", encoding="utf-8")
            self.assertFalse(
                runner_shared.finalize_already_done(tpath, pending_plan, "tst003")
            )
            rc3, msg3 = runner_shared.finalize_outcome(
                tpath, pending_plan, "tst003", 1, "refused: not executed"
            )
            self.assertEqual(rc3, 1)
            self.assertEqual(msg3, "refused: not executed")

    # -------------------------------------------------------------------------
    # (c) E-05: finalize_precheck refuses unreadable/missing plan with exit 2
    # -------------------------------------------------------------------------

    def test_c_finalize_precheck_refuses_missing_plan_file(self) -> None:
        """(c) finalize_precheck returns exit code 2 and does not raise OSError on missing or unreadable plan."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            subprocess.run(["git", "init", str(tpath)], check=True, capture_output=True)
            nonexistent = (
                tpath
                / ".aw/records/plans/pending/20260930-rfhiu2-01-ghost1-nonexistent.ipd.md"
            )

            rc, msg, evidence, findings = ipd_lifecycle.finalize_precheck(
                tpath, nonexistent
            )
            self.assertEqual(rc, ipd_lifecycle.EXIT_CANNOT_RUN)
            self.assertIn(f"plan file not found: {nonexistent}", msg)
            self.assertEqual(evidence, {})
            self.assertEqual(findings, ())

            reasons, acks = runner_shared.compute_scope_reconciliation(
                tpath, nonexistent, labels=runner_shared.OC_HOST_LABELS
            )
            self.assertEqual(reasons, {})
            self.assertEqual(acks, {})

            item = {"id6": "ghost1", "setid": "rfhiu2"}
            rec = runner_shared.record_item_spec_edits(
                tpath,
                nonexistent,
                item,
                reconcile=lambda r, p: runner_shared.compute_scope_reconciliation(
                    r, p, labels=runner_shared.OC_HOST_LABELS
                ),
            )
            self.assertEqual(rec["state"], "refused")

    # -------------------------------------------------------------------------
    # (d) Vocabulary separation control
    # -------------------------------------------------------------------------

    def test_d_verify_absence_vocabulary_remains_disjoint(self) -> None:
        """(d) VERIFY_ABSENCE_CODES remains the 4-element closed set, and verify_absence_text raises for finalize code."""
        self.assertEqual(len(runner_shared.VERIFY_ABSENCE_CODES), 4)
        new_code = getattr(
            runner_shared,
            "FINALIZE_PLAN_UNRESOLVABLE_CODE",
            "finalize-plan-unresolvable",
        )
        self.assertNotIn(new_code, runner_shared.VERIFY_ABSENCE_CODES)
        with self.assertRaises(ValueError):
            runner_shared.verify_absence_text(new_code)


if __name__ == "__main__":
    unittest.main()

"""Behavioral end-to-end tests for IPD lifecycle verbs on companion-records repos.

Covers:
  1. `aw ipd begin` from a public target repo for a plan living in its companion repo
     (and still refusing an unrelated external plan outside both target and companion).
  2. Direct `aw ipd finalize --apply` from a public target repo: audits target code diff,
     lands the lifecycle move + commit in the companion repo, leaves target git free of
     `.aw/records/**`, consumes the target receipt, and reports already-finalized on retry.
  3. Isolated companion execute lane end-to-end: `driver_begin(isolated=True)` -> stage
     plan into lane -> agent edits target code + staged lane plan -> `driver_finalize`
     moves staged plan on disk inside `.aw/records/` with zero target-branch record commits
     -> `integrate_lane_branch` merges code into target `main` and atomically commits the
     executed plan into the companion repo.
  4. `ipd_lifecycle.retire_orchestrator` on a companion-records repo: retires an Order-0
     orchestrator cleanly into the companion repo without touching target git history.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    ipd_lifecycle,
    lane_containment,
    oc_runipd,
    runner_shared,
)
from tests import support
from tests.record_builder import RecordBuilder
from tests.test_companion_runner_integration import (
    _add_lane_worktree,
    _git_head,
    _passing_validation_runner,
    _patched_env,
    _provision_companion_repos,
)


def _conforming_plan_text(
    *,
    id6: str,
    setid: str = "cmpset",
    status: str = "approved",
    performed: bool = False,
    evidence_line: str = "",
) -> str:
    text = support.ready_plan_text(
        plan_id=id6,
        scope_paths="app.py",
        status=status,
    )
    text = text.replace("- Set: demo\n", f"- Set: {setid} (Companion test set)\n", 1)
    if performed:
        ev = evidence_line or "done, verified."
        text = text.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
            "  - Execution state: pending", "  - Execution state: performed", 1
        )
        text = (
            text.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
            .replace("  - Observed evidence:\n", f"  - Observed evidence: {ev}\n", 1)
            .replace("  - Result: pending", "  - Result: pass", 1)
        )
    return text


def _orchestrator_plan_text(*, id6: str, child_id6: str, setid: str = "cmporch") -> str:
    text = str(
        RecordBuilder().plan(
            plan_role="orchestrator",
            title=f"Companion orchestrator {id6}",
            author="tester",
            when="2026-11-24",
            set=setid,
            order=0,
            id6=id6,
            status="approved",
            scope_paths="grandfathered",
            item_dependencies="none",
            priority="medium",
            work_kind="chore",
            approval="2026-11-24, human: approved",
            readiness="go-pending-approval",
            text_only=True,
        )
    )
    text = text.replace("c0ch01", child_id6).replace(
        "TODO child plan filename",
        f"20261124-{setid}-01-{child_id6}-child.ipd.md",
    )
    return text


def _commit_in_repo(
    repo: Path, rel_paths: list[str], message: str, env: dict[str, str]
) -> str:
    subprocess.run(
        ["git", "-C", str(repo), "add", "--", *rel_paths],
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", message],
        env=env,
        check=True,
        capture_output=True,
    )
    return _git_head(repo, env)


def _target_has_aw_records(repo: Path, env: dict[str, str]) -> bool:
    tree = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "HEAD"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return any(p == ".aw/records" or p.startswith(".aw/records/") for p in tree)


class TestCompanionIpdLifecycle(unittest.TestCase):
    def test_begin_succeeds_for_companion_plan_and_refuses_unrelated_external_plan(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            plan_name = "20261124-cmpset-01-cmp101-sample.ipd.md"
            plan_path = records_root / "plans" / "pending" / plan_name
            plan_path.write_text(
                _conforming_plan_text(id6="cmp101", status="approved"),
                encoding="utf-8",
            )
            _commit_in_repo(
                companion,
                [f"records/plans/pending/{plan_name}"],
                "seed approved companion plan",
                env,
            )

            # Create an unrelated external repository with its own plan.
            unrelated = td_path / "unrelated_repo"
            support.init_repo(unrelated)
            ext_plan = (
                unrelated
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261124-extset-01-ext999-foreign.ipd.md"
            )
            ext_plan.parent.mkdir(parents=True, exist_ok=True)
            ext_plan.write_text(
                _conforming_plan_text(id6="ext999", setid="extset", status="approved"),
                encoding="utf-8",
            )

            with _patched_env(env):
                rc, msg = oc_runipd.driver_begin(
                    target, "cmp101", "aw agy run model=test", isolated=True
                )
                self.assertEqual(rc, 0, msg)
                rcpt = ipd_lifecycle.read_receipt(target, "cmp101")
                self.assertIsNotNone(rcpt)
                assert rcpt is not None
                self.assertEqual(rcpt["plan_id"], "cmp101")
                self.assertEqual(rcpt["base_head"], _git_head(target, env))
                self.assertFalse(_target_has_aw_records(target, env))

                # Unrelated external plan must still be refused by the containment guard.
                rc_ext, msg_ext = oc_runipd.driver_begin(
                    target, str(ext_plan), "aw agy run model=test", isolated=False
                )
                self.assertEqual(rc_ext, ipd_lifecycle.EXIT_CANNOT_RUN, msg_ext)
                self.assertIn("not inside repo root", msg_ext)
                self.assertIsNone(ipd_lifecycle.read_receipt(target, "ext999"))

    def test_direct_finalize_commits_lifecycle_to_companion_and_keeps_target_clean(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            plan_name = "20261124-cmpset-01-cmp201-direct.ipd.md"
            pending_path = records_root / "plans" / "pending" / plan_name
            pending_path.write_text(
                _conforming_plan_text(id6="cmp201", status="approved"),
                encoding="utf-8",
            )
            comp_head_before = _commit_in_repo(
                companion,
                [f"records/plans/pending/{plan_name}"],
                "seed cmp201",
                env,
            )

            with _patched_env(env):
                rc_begin, msg_begin = oc_runipd.driver_begin(
                    target, "cmp201", "test-agent", isolated=False
                )
                self.assertEqual(rc_begin, 0, msg_begin)

                # Commit target code change and update companion plan evidence (left uncommitted
                # in companion to also verify uncommitted evidence rides the coordinator worktree).
                (target / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
                target_code_head = _commit_in_repo(
                    target, ["app.py"], "work(cmp201): set VALUE = 2", env
                )
                pending_path.write_text(
                    _conforming_plan_text(
                        id6="cmp201",
                        status="approved",
                        performed=True,
                        evidence_line="python3 verified VALUE == 2 (exit 0)",
                    ),
                    encoding="utf-8",
                )

                cmd = runner_shared.pinned_module_argv(
                    [
                        "ipd",
                        "finalize",
                        "cmp201",
                        "--actor",
                        "test-agent",
                        "--message",
                        "Completed cmp201",
                        "--apply",
                        "--dir",
                        str(target),
                    ]
                )
                proc = subprocess.run(
                    cmd,
                    cwd=str(target),
                    env=env,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(
                    proc.returncode,
                    0,
                    f"stdout={proc.stdout}\nstderr={proc.stderr}",
                )

                executed_path = records_root / "plans" / "executed" / plan_name
                self.assertTrue(executed_path.is_file())
                self.assertFalse(pending_path.exists())
                exec_text = executed_path.read_text(encoding="utf-8")
                self.assertIn("- Status: executed", exec_text)
                self.assertIn("python3 verified VALUE == 2", exec_text)

                # Companion advanced with a lifecycle commit; target did not gain any records commit.
                comp_head_after = _git_head(companion, env)
                self.assertNotEqual(comp_head_after, comp_head_before)
                comp_subject = subprocess.run(
                    ["git", "-C", str(companion), "log", "-1", "--format=%s"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertTrue(
                    comp_subject.startswith("lifecycle(cmp201): finalize"),
                    comp_subject,
                )
                self.assertEqual(_git_head(target, env), target_code_head)
                self.assertFalse(_target_has_aw_records(target, env))
                self.assertIsNone(ipd_lifecycle.read_receipt(target, "cmp201"))

                # Already-finalized predicate finds the companion lifecycle commit.
                verdict = ipd_lifecycle.plan_already_finalized(
                    target, executed_path, "cmp201"
                )
                self.assertTrue(verdict.already)
                self.assertEqual(verdict.lifecycle_commit, comp_head_after)

    def test_isolated_companion_lane_begin_self_finalize_and_integrate_end_to_end(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            plan_name = "20261124-cmpset-01-cmp301-isolated.ipd.md"
            pending_src = records_root / "plans" / "pending" / plan_name
            pending_src.write_text(
                _conforming_plan_text(id6="cmp301", status="approved"),
                encoding="utf-8",
            )
            comp_head_before = _commit_in_repo(
                companion,
                [f"records/plans/pending/{plan_name}"],
                "seed cmp301",
                env,
            )

            with _patched_env(env):
                # 1. Begin on target main under isolated baseline.
                rc_begin, msg_begin = oc_runipd.driver_begin(
                    target, "cmp301", "aw agy run model=test", isolated=True
                )
                self.assertEqual(rc_begin, 0, msg_begin)

                # 2. Allocate isolated lane worktree and stage the companion plan inside it.
                wt, handle = _add_lane_worktree(target, "cmp301", env)
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, pending_src, records_root
                )
                self.assertTrue(staged.is_file())

                # 3. Simulate agent committing code in lane + writing E/V evidence to staged plan.
                (wt / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
                lane_code_head = _commit_in_repo(
                    wt, ["app.py"], "work(cmp301): update VALUE = 2", env
                )
                staged.write_text(
                    _conforming_plan_text(
                        id6="cmp301",
                        status="approved",
                        performed=True,
                        evidence_line="lane verification passed (VALUE == 2)",
                    ),
                    encoding="utf-8",
                )

                # 4. Driver self-finalize inside the lane worktree.
                runner_shared.sync_receipt_into_worktree(target, wt, "cmp301")
                resolved_for_fin = ipd_lifecycle._resolve_staged_companion_lane_plan(
                    wt, pending_src
                )
                self.assertEqual(resolved_for_fin.resolve(), staged.resolve())

                fin_rc, fin_msg = oc_runipd.driver_finalize(
                    wt,
                    resolved_for_fin,
                    "cmp301",
                    "aw agy run model=test",
                    "verified in isolated companion lane",
                )
                self.assertEqual(fin_rc, 0, fin_msg)

                # Staged plan moved inside gitignored wt/.aw/records/, zero commits added to wt,
                # and companion repo untouched until integration succeeds.
                lane_exec = wt / ".aw" / "records" / "plans" / "executed" / plan_name
                self.assertTrue(lane_exec.is_file())
                self.assertFalse(staged.exists())
                self.assertIn(
                    "- Status: executed", lane_exec.read_text(encoding="utf-8")
                )
                self.assertEqual(_git_head(wt, env), lane_code_head)
                self.assertFalse(_target_has_aw_records(wt, env))
                self.assertTrue(pending_src.is_file())
                self.assertEqual(_git_head(companion, env), comp_head_before)

                # Re-running driver_finalize on the already-finalized lane is idempotent (exit 0).
                resolved_again = ipd_lifecycle._resolve_staged_companion_lane_plan(
                    wt, pending_src
                )
                self.assertEqual(resolved_again.resolve(), lane_exec.resolve())
                fin_rc_2, fin_msg_2 = oc_runipd.driver_finalize(
                    wt,
                    resolved_again,
                    "cmp301",
                    "aw agy run model=test",
                    "verified in isolated companion lane",
                )
                self.assertEqual(fin_rc_2, 0, fin_msg_2)

                # 5. Integrate lane: merges code to target main and routes executed plan to companion.
                ok, reason, kind = oc_runipd.integrate_lane_branch(
                    target, handle, "cmp301", _passing_validation_runner
                )
                self.assertTrue(ok, reason)
                self.assertEqual(kind, "integrated")

                self.assertEqual(
                    (target / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n"
                )
                self.assertFalse(_target_has_aw_records(target, env))

                comp_exec = records_root / "plans" / "executed" / plan_name
                self.assertTrue(comp_exec.is_file())
                self.assertFalse(pending_src.exists())
                comp_exec_text = comp_exec.read_text(encoding="utf-8")
                self.assertIn("- Status: executed", comp_exec_text)
                self.assertIn("lane verification passed (VALUE == 2)", comp_exec_text)
                self.assertNotEqual(_git_head(companion, env), comp_head_before)

    def test_retire_orchestrator_commits_to_companion_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            child_name = "20261124-cmporch-01-cmp401-child.ipd.md"
            orch_name = "20261124-cmporch-00-cmp400-orch.ipd.md"

            child_exec = records_root / "plans" / "executed" / child_name
            child_exec.write_text(
                _conforming_plan_text(
                    id6="cmp401",
                    setid="cmporch",
                    status="executed",
                    performed=True,
                    evidence_line="child verified",
                ),
                encoding="utf-8",
            )
            orch_pending = records_root / "plans" / "pending" / orch_name
            orch_pending.write_text(
                _orchestrator_plan_text(
                    id6="cmp400", child_id6="cmp401", setid="cmporch"
                ),
                encoding="utf-8",
            )
            comp_head_before = _commit_in_repo(
                companion,
                [
                    f"records/plans/executed/{child_name}",
                    f"records/plans/pending/{orch_name}",
                ],
                "seed orchestrator and executed child",
                env,
            )
            target_head_before = _git_head(target, env)

            with _patched_env(env):
                res = ipd_lifecycle.retire_orchestrator(
                    target,
                    orch_pending,
                    "aw agy run model=test",
                    setid="cmporch",
                    run_id="run-companion-test",
                    apply=True,
                )
                self.assertEqual(res.exit_code, 0, res.message)
                self.assertIsNotNone(res.commit)

                orch_exec = records_root / "plans" / "executed" / orch_name
                self.assertTrue(orch_exec.is_file())
                self.assertFalse(orch_pending.exists())
                orch_text = orch_exec.read_text(encoding="utf-8")
                self.assertIn("- Status: executed", orch_text)
                self.assertIn(ipd_lifecycle.ROLLUP_SUPERSEDED_STATEMENT, orch_text)

                self.assertNotEqual(_git_head(companion, env), comp_head_before)
                self.assertEqual(_git_head(target, env), target_head_before)
                self.assertFalse(_target_has_aw_records(target, env))

    def test_companion_backlog_and_spec_pass_structure_preflight_and_initialize_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"

            b1_name = "20261124-bkl101-01-bkl101-sample-one.backlog.md"
            b2_name = "20261124-bkl102-01-bkl102-sample-two.backlog.md"
            (records_root / "backlog" / "open" / b1_name).write_text(
                str(
                    RecordBuilder().backlog(
                        title="Sample companion backlog one",
                        when="2026-11-24",
                        id6="bkl101",
                        set="bkl101",
                        status="open",
                        priority="medium",
                        text_only=True,
                    )
                ),
                encoding="utf-8",
            )
            (records_root / "backlog" / "open" / b2_name).write_text(
                str(
                    RecordBuilder().backlog(
                        title="Sample companion backlog two",
                        when="2026-11-24",
                        id6="bkl102",
                        set="bkl102",
                        status="open",
                        priority="low",
                        text_only=True,
                    )
                ),
                encoding="utf-8",
            )
            spec_dir = records_root / "specs" / "to-review"
            spec_dir.mkdir(parents=True, exist_ok=True)
            s1_name = "20261124-spc101-01-spc101-sample-spec.spec.md"
            (spec_dir / s1_name).write_text(
                str(
                    RecordBuilder().spec(
                        title="Sample companion spec",
                        when="2026-11-24",
                        id6="spc101",
                        set="spc101",
                        status="to-review",
                        text_only=True,
                    )
                ),
                encoding="utf-8",
            )
            _commit_in_repo(
                companion,
                [
                    f"records/backlog/open/{b1_name}",
                    f"records/backlog/open/{b2_name}",
                    f"records/specs/to-review/{s1_name}",
                ],
                "seed companion backlog and spec items",
                env,
            )

            with _patched_env(env):
                manifest = runner_shared.build_dynamic_manifest(
                    target, runner_shared.discover_plans(target)
                )
                b_map = runner_shared.populate_manifest_backlog(manifest, target)
                self.assertEqual(
                    b_map["bkl101"]["file"], f".aw/records/backlog/open/{b1_name}"
                )
                s_map = runner_shared.populate_manifest_specs(manifest, target)
                self.assertEqual(
                    s_map["spc101"]["file"], f".aw/records/specs/to-review/{s1_name}"
                )

                # Full `aw oc run --action plan bkl101 bkl102 --prepare-only` initializes cleanly
                # without RUN-NOT-FOUND in RUN-STRUCTURE-PREFLIGHT.
                parser = oc_runipd.build_parser()
                args = parser.parse_args(
                    [
                        "start",
                        "--repo",
                        str(target),
                        "--action",
                        "plan",
                        "--prepare-only",
                        "bkl101",
                        "bkl102",
                    ]
                )
                run_dir = oc_runipd.initialize_run(args)
                self.assertTrue(run_dir.is_dir())
                state = oc_runipd.load_state(run_dir)
                self.assertEqual(
                    [it["id6"] for it in state["queue"]], ["bkl101", "bkl102"]
                )
                self.assertEqual(
                    [it["action"] for it in state["queue"]], ["plan", "plan"]
                )

                # Companion spec also passes freeze-time structure preflight.
                runner_shared.enforce_freeze_time_refusal(
                    [
                        {
                            "id6": "spc101",
                            "artifact_type": "spec",
                            "initial_status": "to-review",
                            "status": "queued",
                            "action": "review",
                            "configured_file": s_map["spc101"]["file"],
                            "dependencies": [],
                        }
                    ],
                    repo=target,
                    host="oc",
                )

                # A genuinely missing backlog file still refuses with RUN-NOT-FOUND.
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    runner_shared.enforce_freeze_time_refusal(
                        [
                            {
                                "id6": "ghost9",
                                "artifact_type": "backlog",
                                "initial_status": "open",
                                "status": "queued",
                                "action": "plan",
                                "configured_file": ".aw/records/backlog/open/nonexistent.backlog.md",
                                "dependencies": [],
                            }
                        ],
                        repo=target,
                        host="oc",
                    )
                self.assertIn("RUN-NOT-FOUND", str(ctx.exception))


class CompanionPlanProductionTests(unittest.TestCase):
    """End-to-end companion-records tests for `--action plan` (backlog and spec production)."""

    def test_backlog_production_in_isolated_companion_lane_discovers_graduates_and_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"

            bkl_name = "20261124-mux2cz-01-mux2cz-fix-pytest-import-order.backlog.md"
            bkl_rel = f"records/backlog/open/{bkl_name}"
            bkl_path = companion / bkl_rel
            bkl_path.parent.mkdir(parents=True, exist_ok=True)
            bkl_path.write_text(
                str(
                    RecordBuilder().backlog(
                        title="Fix pytest import order",
                        id6="mux2cz",
                        set="mux2cz",
                        status="open",
                        priority="medium",
                        work_kind="chore",
                        text_only=True,
                    )
                ),
                encoding="utf-8",
            )
            comp_head_before = _commit_in_repo(
                companion, [bkl_rel], "seed companion backlog mux2cz", env
            )
            main_head_before = _git_head(target, env)

            run_dir = td_path / "run-20261124T151000Z-5555"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, object] = {
                "position": 1,
                "id6": "mux2cz",
                "setid": "mux2cz",
                "action": "plan",
                "artifact_type": "backlog",
                "initial_status": "open",
                "configured_file": f".aw/records/backlog/open/{bkl_name}",
                "status": "queued",
                "attempts": [],
            }
            state: dict[str, object] = {
                "run_id": run_dir.name,
                "repo": str(target),
                "queue": [item],
                "options": {
                    "isolate_worktree": True,
                    "self_finalize": True,
                },
            }
            observed: dict[str, object] = {}

            def _fake_spawn_backlog_producer(
                prompt_path: Path,
                work_dir: Path | None,
                _tracker: object,
                _plan_path: Path,
                _attempt_no: int,
                _session_id: str | None,
                _use_continue: bool,
            ) -> tuple[int, str | None, Path, list[str]]:
                assert work_dir is not None
                wt = Path(work_dir)
                prompt_text = Path(prompt_path).read_text(encoding="utf-8")
                observed["outside"] = lane_containment.absolute_paths_outside_lane(
                    prompt_text, wt
                )
                observed["staged_bkl_exists"] = (
                    wt / ".aw" / "records" / "backlog" / "open" / bkl_name
                ).is_file()

                # Verify `aw ipd scaffold` writes into the lane's `.aw/records/plans/pending/`,
                # NOT outside the lane into the live companion repo.
                scaffold_proc = subprocess.run(
                    [
                        "python3",
                        "-m",
                        "agent_workflows",
                        "ipd",
                        "scaffold",
                        "--title",
                        "Make pytest import checkout source",
                        "--author",
                        "tester",
                        "--set",
                        "mux2cz",
                        "--order",
                        "1",
                        "--from-backlog",
                        "mux2cz",
                        "--kind",
                        "child",
                        "--priority",
                        "medium",
                        "--work-kind",
                        "chore",
                        "--apply",
                    ],
                    cwd=str(wt),
                    env=env,
                    capture_output=True,
                    text=True,
                )
                observed["scaffold_rc"] = scaffold_proc.returncode
                observed["scaffold_stderr"] = scaffold_proc.stderr
                lane_pending = wt / ".aw" / "records" / "plans" / "pending"
                scaffolded = sorted(lane_pending.glob("*.ipd.md"))
                observed["scaffolded_count"] = len(scaffolded)
                observed["companion_plans_during_turn"] = list(
                    (records_root / "plans" / "pending").glob("*.ipd.md")
                )
                assert len(scaffolded) == 1, scaffold_proc.stdout + scaffold_proc.stderr
                plan_file = scaffolded[0]
                plan_id = plan_file.stem.split("-")[3]
                observed["produced_id6"] = plan_id

                # Fill the scaffolded plan with conforming to-review content linked to mux2cz.
                plan_text = _conforming_plan_text(
                    id6=plan_id, setid="mux2cz", status="to-review"
                )
                plan_text = plan_text.replace(
                    "- Status: to-review\n",
                    "- Status: to-review\n- From-Backlog: mux2cz\n",
                    1,
                )
                plan_file.write_text(plan_text, encoding="utf-8")

                log_p = run_dir / "mux2cz.log"
                log_p.write_text("produced plan\n", encoding="utf-8")
                return 0, "sess-mux2cz", log_p, ["fake-host"]

            with _patched_env(env):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fake_spawn_backlog_producer,
                    spawn_verifier=_fake_spawn_backlog_producer,
                    raw_launcher=lambda *_a, **_kw: (0, None, run_dir / "raw.log", []),
                    run_suite_check=lambda _p, _l: None,
                    process_backlog_close=lambda *_a, **_kw: None,
                    driver_module=oc_runipd,
                )

            self.assertEqual(observed.get("outside"), [])
            self.assertTrue(observed.get("staged_bkl_exists"))
            self.assertEqual(
                observed.get("scaffold_rc"), 0, observed.get("scaffold_stderr")
            )
            self.assertEqual(observed.get("scaffolded_count"), 1)
            self.assertEqual(observed.get("companion_plans_during_turn"), [])
            self.assertEqual(item.get("status"), "executed", item)
            self.assertTrue(item.get("prod_integrated"), item)

            # Public target repo stays completely untouched and free of `.aw/records/**`.
            self.assertEqual(_git_head(target, env), main_head_before)
            self.assertFalse(_target_has_aw_records(target, env))

            # Companion repo received ONE clean commit with the new plan AND graduated backlog move.
            self.assertNotEqual(_git_head(companion, env), comp_head_before)
            self.assertFalse(bkl_path.exists())
            grad_bkl = records_root / "backlog" / "graduated" / bkl_name
            self.assertTrue(grad_bkl.is_file())
            grad_text = grad_bkl.read_text(encoding="utf-8")
            self.assertIn("- Status: graduated", grad_text)
            self.assertIn("- Graduated-To: mux2cz", grad_text)
            produced_id6 = str(observed["produced_id6"])
            self.assertIn(produced_id6, grad_text)
            comp_plans = list(
                (records_root / "plans" / "pending").glob(f"*{produced_id6}*.ipd.md")
            )
            self.assertEqual(len(comp_plans), 1)
            self.assertIn(
                "- From-Backlog: mux2cz", comp_plans[0].read_text(encoding="utf-8")
            )

            # Companion working tree must have zero pending record or state/lock mutations
            # (ignoring runtime `records/runs/` created by the lock/runner).
            comp_status_lines = [
                line
                for line in subprocess.run(
                    ["git", "-C", str(companion), "status", "--porcelain"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.splitlines()
                if line.strip() and not line.strip().endswith("records/runs/")
            ]
            self.assertEqual(comp_status_lines, [], comp_status_lines)

    def test_spec_production_in_isolated_companion_lane_discovers_transitions_and_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"

            spec_name = "20261124-spc777-01-spc777-companion-spec-prod.spec.md"
            spec_rel = f"records/specs/approved/{spec_name}"
            spec_path = companion / spec_rel
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_text = str(
                RecordBuilder().spec(
                    title="Companion spec production",
                    id6="spc777",
                    status="approved",
                    text_only=True,
                )
            )
            spec_path.write_text(spec_text, encoding="utf-8")
            comp_head_before = _commit_in_repo(
                companion, [spec_rel], "seed companion approved spec spc777", env
            )
            main_head_before = _git_head(target, env)

            run_dir = td_path / "run-20261124T152000Z-6666"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, object] = {
                "position": 1,
                "id6": "spc777",
                "setid": "spc777",
                "action": "plan",
                "artifact_type": "spec",
                "initial_status": "approved",
                "configured_file": f".aw/records/specs/approved/{spec_name}",
                "status": "queued",
                "attempts": [],
            }
            state: dict[str, object] = {
                "run_id": run_dir.name,
                "repo": str(target),
                "queue": [item],
                "options": {
                    "isolate_worktree": True,
                    "self_finalize": True,
                },
            }

            def _fake_spawn_spec_producer(
                _prompt_path: Path,
                work_dir: Path | None,
                _tracker: object,
                _plan_path: Path,
                _attempt_no: int,
                _session_id: str | None,
                _use_continue: bool,
            ) -> tuple[int, str | None, Path, list[str]]:
                assert work_dir is not None
                wt = Path(work_dir)
                plan_path = (
                    wt
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20261124-spc777-01-pln777-implement-companion-spec.ipd.md"
                )
                plan_path.parent.mkdir(parents=True, exist_ok=True)
                plan_text = _conforming_plan_text(
                    id6="pln777", setid="spc777", status="to-review"
                )
                plan_text = plan_text.replace(
                    "- Status: to-review\n",
                    "- Status: to-review\n- From-Spec: spc777\n",
                    1,
                )
                plan_path.write_text(plan_text, encoding="utf-8")
                log_p = run_dir / "spc777.log"
                log_p.write_text("produced spec plan\n", encoding="utf-8")
                return 0, "sess-spc777", log_p, ["fake-host"]

            with _patched_env(env):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fake_spawn_spec_producer,
                    spawn_verifier=_fake_spawn_spec_producer,
                    raw_launcher=lambda *_a, **_kw: (0, None, run_dir / "raw.log", []),
                    run_suite_check=lambda _p, _l: None,
                    process_backlog_close=lambda *_a, **_kw: None,
                    driver_module=oc_runipd,
                )

            self.assertEqual(item.get("status"), "executed", item)
            self.assertTrue(item.get("prod_integrated"), item)
            self.assertEqual(_git_head(target, env), main_head_before)
            self.assertFalse(_target_has_aw_records(target, env))
            self.assertNotEqual(_git_head(companion, env), comp_head_before)

            self.assertFalse(spec_path.exists())
            impl_spec = records_root / "specs" / "implementing" / spec_name
            self.assertTrue(impl_spec.is_file())
            self.assertIn(
                "- Status: implementing", impl_spec.read_text(encoding="utf-8")
            )
            self.assertTrue(
                (
                    records_root
                    / "plans"
                    / "pending"
                    / "20261124-spc777-01-pln777-implement-companion-spec.ipd.md"
                ).is_file()
            )
            comp_status_lines = [
                line
                for line in subprocess.run(
                    ["git", "-C", str(companion), "status", "--porcelain"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.splitlines()
                if line.strip() and not line.strip().endswith("records/runs/")
            ]
            self.assertEqual(comp_status_lines, [], comp_status_lines)

    def test_resolve_companion_lane_path_does_not_resurrect_moved_baseline_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, _handle = _add_lane_worktree(target, "mov001", env)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261124-cmpset-01-mov001-move-test.ipd.md"
            )
            plan_src.write_text(_conforming_plan_text(id6="mov001"), encoding="utf-8")

            with _patched_env(env):
                staged = lane_containment.resolve_companion_lane_path(
                    wt, plan_src, repo=target, overwrite=False
                )
                assert staged is not None and staged.is_file()
                moved = wt / ".aw" / "records" / "plans" / "executed" / plan_src.name
                moved.parent.mkdir(parents=True, exist_ok=True)
                staged.rename(moved)
                self.assertFalse(staged.exists())

                # Post-turn non-overwriting lookup (such as collect_lane_submissions) must NOT
                # copy the old pending/ file back from companion.
                again = lane_containment.resolve_companion_lane_path(
                    wt, plan_src, repo=target, overwrite=False
                )
                self.assertEqual(again, staged)
                self.assertFalse(staged.exists())
                self.assertTrue(moved.is_file())


if __name__ == "__main__":
    unittest.main()

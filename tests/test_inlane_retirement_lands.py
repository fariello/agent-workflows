"""An execute turn that RETIRES its plan in-lane is a success that LANDS on main (no finalize).

Measured incident (run `run-20260927T174659Z-293992`, plan `xts8ux`): the plan's E-01 stop condition
fired, the agent correctly moved the plan to `superseded/` in its lane, the verifier said VERIFIED,
and the runner still scored it `fail-gate`, tried to FINALIZE a superseded plan into `executed/`
(refused), and stranded the retirement on the lane. These tests pin the corrected behavior on both
hosts through the real `execute_item` path.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN, _init_repo_with_conforming_plan

_HOSTS = (("oc", oc_runipd, "run_opencode"), ("agy", agy_runipd, "run_agy_turn"))


def _state_and_item(repo: Path, plan: Path) -> tuple[dict, dict]:
    item = {
        "position": 1,
        "id6": "ret001",
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
            "no_audit": False,
        },
    }
    return state, item


def _fake_agent_retires_in_lane(run_dir: Path, *, verdict: str = "VERIFIED"):
    """Execute turn: `git mv` the plan to superseded/ (status bumped) and commit in the LANE, then
    self-report `blocked` exactly as the real agent did. Verify turn: record `verdict`."""

    def fake_run(state, rd, item, *_args, **kwargs):
        # oc: run_opencode(state, rd, item, plan_path, prompt_path, attempt_no, fresh_session=...)
        # agy: run_agy_turn(state, rd, item, prompt_path, attempt_no, ..., log_suffix="verify")
        if kwargs.get("fresh_session") or kwargs.get("log_suffix") == "verify":
            (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            ).write_text(
                json.dumps({"verdict": verdict, "tests_run": ["python3 -m pytest"]}),
                encoding="utf-8",
            )
            return 0, "vses", str(run_dir / "vlog"), ["x"]
        wt = Path(kwargs["work_dir"])
        pending = next((wt / ".aw" / "records" / "plans" / "pending").glob("*ret001*"))
        sup = wt / ".aw" / "records" / "plans" / "superseded"
        sup.mkdir(parents=True, exist_ok=True)
        text = pending.read_text(encoding="utf-8").replace(
            "- Status: approved", "- Status: superseded"
        )
        pending.write_text(
            "RETIRED 2026-09-27: premise spent.\n\n" + text, encoding="utf-8"
        )
        subprocess.run(
            ["git", "mv", str(pending), str(sup / pending.name)], cwd=wt, check=True
        )
        subprocess.run(["git", "commit", "-qam", "retire ret001"], cwd=wt, check=True)
        (
            run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
        ).write_text(
            json.dumps(
                {
                    "disposition": "blocked",
                    "pushed": False,
                    "defect_report": {"state": "none-found", "findings": []},
                }
            ),
            encoding="utf-8",
        )
        return 0, "ses1", str(run_dir / "log"), ["x"]

    return fake_run


class InLaneRetirementLandsTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _run(self, mod, spawn_name, *, verdict="VERIFIED"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name) / "repo"
        plan = _init_repo_with_conforming_plan(repo, "ret001")
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        state, item = _state_and_item(repo, plan)
        finalize_calls: list = []
        real_finalize = mod.driver_finalize

        def spy_finalize(*a, **k):
            finalize_calls.append(a)
            return real_finalize(*a, **k)

        with (
            mock.patch.object(
                mod, spawn_name, _fake_agent_retires_in_lane(run_dir, verdict=verdict)
            ),
            mock.patch.object(mod, "driver_finalize", spy_finalize),
        ):
            mod.execute_item(run_dir, state, item, recovery=False)
        return repo, plan, item, finalize_calls

    def test_verified_retirement_lands_on_main_without_finalize(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls = self._run(mod, spawn)
                self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
                self.assertEqual(
                    finalize_calls, [], "a retired plan must never be finalized"
                )
                sup = repo / ".aw" / "records" / "plans" / "superseded" / plan.name
                self.assertTrue(sup.is_file(), "the retirement must land on main")
                self.assertFalse(plan.is_file())
                self.assertFalse(
                    (repo / ".aw" / "records" / "plans" / "executed").exists()
                )
                self.assertTrue(runner_shared.item_reached_success(item))
                self.assertNotIn(item["status"], runner_shared.EXECUTION_SUCCESS_STATES)

    def test_unverified_retirement_does_not_land(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                repo, plan, item, finalize_calls = self._run(
                    mod, spawn, verdict="CORRECTION_REQUIRED"
                )
                self.assertNotEqual(item["status"], runner_shared.RETIRED_STATUS)
                self.assertFalse(runner_shared.item_reached_success(item))
                self.assertTrue(
                    plan.is_file(), "an unverified retirement must not reach main"
                )

    def test_retired_never_satisfies_an_executed_edge(self):
        self.assertNotIn("retired", runner_shared.EXECUTION_SUCCESS_STATES)
        self.assertEqual(
            runner_shared.outcome_precedence_disposition(
                "superseded", {"disposition": "blocked"}
            ),
            runner_shared.RETIRED_STATUS,
        )
        self.assertEqual(
            runner_shared.outcome_precedence_disposition("not-executed", None),
            runner_shared.RETIRED_STATUS,
        )


class RetiredLaneReintegrationTests(unittest.TestCase):
    """`aw <host> run integrate <id6>` lands a lane whose turn RETIRED its plan (measured: `xts8ux`
    was refused as 'not finalized'), and still refuses a lane whose plan is merely pending."""

    def _retired_lane(self, bucket: str):
        import pathlib
        import subprocess

        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _verified_lane,
            _write_run_state,
            _stranded_item,
        )

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        repo = _repo_with_pending_plan(root, "rr0001")
        lane = _verified_lane(repo, root, "rr0001", finalize=False)
        lane_dir = pathlib.Path(lane["worktree"])
        name = "20260906-demo-01-rr0001-demo.ipd.md"
        src = lane_dir / ".aw" / "records" / "plans" / "pending" / name
        dst = lane_dir / ".aw" / "records" / "plans" / bucket / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", str(src), str(dst)], cwd=lane_dir, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "retire rr0001"], cwd=lane_dir, check=True
        )
        _write_run_state(
            repo, {"repo": str(repo), "queue": [_stranded_item(lane, "fail-gate")]}
        )
        return repo, name

    def _integrate(self, repo, handle, id6, validation_runner):
        return oc_runipd.integrate_lane_branch(repo, handle, id6, validation_runner)

    def test_retired_lane_reintegrates_and_is_marked_retired(self):
        from tests.test_runner_shared import _passing_suite

        for bucket in ("superseded", "not-executed"):
            with self.subTest(bucket=bucket):
                repo, name = self._retired_lane(bucket)
                outcome = runner_shared.reintegrate_lane(
                    repo,
                    "rr0001",
                    integrate=self._integrate,
                    suite_check=_passing_suite,
                )
                self.assertTrue(outcome.integrated, outcome.reason)
                self.assertTrue(outcome.retired)
                self.assertTrue(
                    (repo / ".aw" / "records" / "plans" / bucket / name).is_file(),
                    "the retirement must land on main",
                )
                self.assertFalse(
                    (repo / ".aw" / "records" / "plans" / "executed" / name).exists()
                )

    def test_finish_records_retired_not_executed(self):
        item = {
            "id6": "rr0001",
            "status": "fail-gate",
            "attempts": [{"disposition": "fail-gate"}],
        }
        state = {"queue": [item]}
        outcome = runner_shared.ReintegrationOutcome(
            integrated=True,
            code=runner_shared.REINTEGRATE_OK,
            reason="ff",
            retired=True,
        )
        events: list = []
        with tempfile.TemporaryDirectory() as d:
            runner_shared.finish_reintegrated_item(
                repo=Path(d),
                run_dir=Path(d),
                state=state,
                item=item,
                outcome=outcome,
                save_state=lambda *a, **k: None,
                append_jsonl=lambda _p, e: events.append(e),
            )
        self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
        self.assertEqual(
            item["attempts"][-1]["disposition"], runner_shared.RETIRED_STATUS
        )
        self.assertEqual(events[0]["event"], "ipd-retired-integrated")


class InLaneRetirementBacklogCloseTests(unittest.TestCase):
    """reattclose-02 (`eg9jjm`) E-02: retired-lane backlog close lands safely in a coordinator worktree and is guarded."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_repo_and_carriers(
        self, repo: Path, *, bstatus: str = "graduated"
    ) -> tuple[Path, Path, Path]:
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )

        bdir = repo / ".aw" / "records" / "backlog" / bstatus
        bdir.mkdir(parents=True, exist_ok=True)
        bitem = bdir / "20260928-1200-01-bg0001-test.backlog.md"
        bitem.write_text(
            f"- Id: bg0001\n- Status: {bstatus}\n- Priority: medium\n- Work-Kind: chore\n",
            encoding="utf-8",
        )

        pdir = repo / ".aw" / "records" / "plans" / "pending"
        pdir.mkdir(parents=True, exist_ok=True)
        p1_text = _CONFORMING_PLAN.format(id6="ret001").replace(
            "- Item-Dependencies: none",
            "- Item-Dependencies: none\n- From-Backlog: bg0001",
        )
        plan1 = pdir / "20260828-demo-01-ret001-demo.ipd.md"
        plan1.write_text(p1_text, encoding="utf-8")

        edir = repo / ".aw" / "records" / "plans" / "executed"
        edir.mkdir(parents=True, exist_ok=True)
        p2_text = (
            _CONFORMING_PLAN.format(id6="ret002")
            .replace(
                "- Item-Dependencies: none",
                "- Item-Dependencies: none\n- From-Backlog: bg0001",
            )
            .replace("- Status: approved", "- Status: executed")
        )
        plan2 = edir / "20260828-demo-02-ret002-demo.ipd.md"
        plan2.write_text(p2_text, encoding="utf-8")

        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        return plan1, plan2, bitem

    def _agent(self, run_dir: Path, *, detach: bool = True):
        base = _fake_agent_retires_in_lane(run_dir)

        def run(state, rd, item, *args, **kwargs):
            if (
                not kwargs.get("fresh_session")
                and kwargs.get("log_suffix") != "verify"
                and detach
            ):
                wt = Path(kwargs["work_dir"])
                pending = next(
                    (wt / ".aw" / "records" / "plans" / "pending").glob("*ret001*")
                )
                text = pending.read_text(encoding="utf-8").replace(
                    "- From-Backlog: bg0001", "- From-Backlog: -"
                )
                pending.write_text(text, encoding="utf-8")
            return base(state, rd, item, *args, **kwargs)

        return run

    def test_case_1_success_arm(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as d:
                    repo = Path(d) / "repo"
                    p1, p2, bitem = self._setup_repo_and_carriers(repo)
                    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
                    (run_dir / "outcomes").mkdir(parents=True)
                    (run_dir / "prompts").mkdir(parents=True)
                    state, item = _state_and_item(repo, p1)
                    item["from_backlog"] = "bg0001"
                    state["queue"].append(
                        {
                            "position": 2,
                            "id6": "ret002",
                            "setid": "demo",
                            "status": "executed",
                            "earned_paths": [str(p2.relative_to(repo))],
                        }
                    )
                    with mock.patch.object(
                        mod, spawn, self._agent(run_dir, detach=True)
                    ):
                        mod.execute_item(run_dir, state, item, recovery=False)

                    self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
                    close_rec = item.get("backlog_close") or {}
                    self.assertTrue(
                        close_rec.get("closed"),
                        f"expected closed: True, got {close_rec}",
                    )
                    self.assertEqual(close_rec.get("wrote_in"), "coordinator_worktree")
                    porcelain = subprocess.run(
                        [
                            "git",
                            "status",
                            "--porcelain",
                            "-uall",
                            "--",
                            ".aw/records/backlog",
                        ],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    self.assertEqual(
                        porcelain, "", "working tree under backlog must be clean"
                    )
                    self.assertTrue(
                        (
                            repo / ".aw" / "records" / "backlog" / "done" / bitem.name
                        ).is_file()
                    )
                    self.assertFalse(
                        (
                            repo
                            / ".aw"
                            / "records"
                            / "backlog"
                            / "graduated"
                            / bitem.name
                        ).exists()
                    )

    def test_case_2_failure_arm(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as d:
                    repo = Path(d) / "repo"
                    p1, p2, bitem = self._setup_repo_and_carriers(repo)
                    hooks_dir = repo / ".git" / "hooks"
                    hooks_dir.mkdir(parents=True, exist_ok=True)
                    hook = hooks_dir / "pre-commit"
                    hook.write_text(
                        "#!/bin/sh\nif git diff --cached --name-only | grep -q 'backlog'; then exit 1; fi\nexit 0\n",
                        encoding="utf-8",
                    )
                    os.chmod(hook, 0o755)

                    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
                    (run_dir / "outcomes").mkdir(parents=True)
                    (run_dir / "prompts").mkdir(parents=True)
                    state, item = _state_and_item(repo, p1)
                    item["from_backlog"] = "bg0001"
                    state["queue"].append(
                        {
                            "position": 2,
                            "id6": "ret002",
                            "setid": "demo",
                            "status": "executed",
                            "earned_paths": [str(p2.relative_to(repo))],
                        }
                    )
                    with mock.patch.object(
                        mod, spawn, self._agent(run_dir, detach=True)
                    ):
                        mod.execute_item(run_dir, state, item, recovery=False)

                    self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
                    close_rec = item.get("backlog_close") or {}
                    self.assertFalse(close_rec.get("closed"))
                    porcelain = subprocess.run(
                        [
                            "git",
                            "status",
                            "--porcelain",
                            "-uall",
                            "--",
                            ".aw/records/backlog",
                        ],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    self.assertEqual(
                        porcelain,
                        "",
                        "main's backlog working tree must be left clean on failure",
                    )
                    self.assertEqual(close_rec.get("wrote_in"), "coordinator_worktree")

    def test_case_3_missing_guard(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as d:
                    repo = Path(d) / "repo"
                    p1, p2, bitem = self._setup_repo_and_carriers(repo, bstatus="done")
                    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
                    (run_dir / "outcomes").mkdir(parents=True)
                    (run_dir / "prompts").mkdir(parents=True)
                    state, item = _state_and_item(repo, p1)
                    item["from_backlog"] = "bg0001"
                    initial_close = {
                        "closed": True,
                        "commit": "abc123def456",
                        "wrote_in": "coordinator_worktree",
                        "landing": {"status": "reconciled", "detail": "ff"},
                    }
                    item["backlog_close"] = copy.deepcopy(initial_close)

                    close_calls: list = []
                    real_close = mod.process_backlog_close

                    def spy_close(*a, **k):
                        close_calls.append((a, k))
                        return real_close(*a, **k)

                    perf_calls: list = []
                    real_perf = runner_shared.perform_coordinator_backlog_close

                    def spy_perf(*a, **k):
                        perf_calls.append((a, k))
                        return real_perf(*a, **k)

                    with (
                        mock.patch.object(
                            mod, spawn, self._agent(run_dir, detach=True)
                        ),
                        mock.patch.object(mod, "process_backlog_close", spy_close),
                        mock.patch.object(
                            runner_shared, "perform_coordinator_backlog_close", spy_perf
                        ),
                    ):
                        mod.execute_item(run_dir, state, item, recovery=False)

                    self.assertEqual(
                        close_calls,
                        [],
                        "close performer must not be called when already closed",
                    )
                    self.assertEqual(
                        perf_calls,
                        [],
                        "coordinator performer must not be called when already closed",
                    )
                    self.assertEqual(
                        item["backlog_close"],
                        initial_close,
                        "backlog_close record must survive byte-for-byte",
                    )

    def test_case_4_refusing_shape_unchanged(self):
        for label, mod, spawn in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as d:
                    repo = Path(d) / "repo"
                    p1, p2, bitem = self._setup_repo_and_carriers(repo)
                    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
                    (run_dir / "outcomes").mkdir(parents=True)
                    (run_dir / "prompts").mkdir(parents=True)
                    state, item = _state_and_item(repo, p1)
                    item["from_backlog"] = "bg0001"
                    state["queue"].append(
                        {
                            "position": 2,
                            "id6": "ret002",
                            "setid": "demo",
                            "status": "executed",
                            "earned_paths": [str(p2.relative_to(repo))],
                        }
                    )
                    with mock.patch.object(
                        mod, spawn, self._agent(run_dir, detach=False)
                    ):
                        mod.execute_item(run_dir, state, item, recovery=False)

                    self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
                    close_rec = item.get("backlog_close") or {}
                    self.assertFalse(close_rec.get("closed"))
                    self.assertIn(
                        "IPD carrier(s) not executed", close_rec.get("reason", "")
                    )
                    porcelain = subprocess.run(
                        [
                            "git",
                            "status",
                            "--porcelain",
                            "-uall",
                            "--",
                            ".aw/records/backlog",
                        ],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    self.assertEqual(
                        porcelain, "", "main backlog working tree must be clean"
                    )
                    self.assertTrue(
                        (
                            repo
                            / ".aw"
                            / "records"
                            / "backlog"
                            / "graduated"
                            / bitem.name
                        ).is_file()
                    )


if __name__ == "__main__":
    unittest.main()

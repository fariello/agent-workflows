"""Tests for the `aw agy` / `aw antigravity` subcommand group.

The group forwards the raw argv tail verbatim to `agent_workflows.agy_runipd.main`, so `aw agy runipd`
(and its `antigravity` alias and `run`/`runagy` subcommands) has exact CLI parity with the standalone
runner - including the runner's own `--help` and its implicit-`start` shim.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, cli, runner_shared
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN


def _run_cli(argv):
    """Run `aw <argv...>` capturing (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:  # argparse may exit
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


class AgyRunipdCliTests(unittest.TestCase):
    def test_help_forwards_to_runner_both_aliases(self):
        for group in ("agy", "antigravity"):
            for subcmd in ("runipd", "run", "runagy"):
                rc, out, err = _run_cli([group, subcmd, "--help"])
                combined = out + err
                self.assertEqual(rc, 0, f"{group} {subcmd} --help rc={rc}: {combined}")
                self.assertIn("runagy", combined)
                self.assertIn("start", combined)
                self.assertIn("resume", combined)

    def test_forwarding_and_delegation_to_agy_runipd_main(self):
        for argv, expected in (
            (["agy", "runipd", "status", "run-xyz"], ["status", "run-xyz"]),
            (
                ["antigravity", "run", "resume", "run-xyz", "--retry-incomplete"],
                ["resume", "run-xyz", "--retry-incomplete"],
            ),
            (["agy", "runipd", "somesetid", "--dry-run"], ["somesetid", "--dry-run"]),
        ):
            with self.subTest(argv=argv):
                with mock.patch.object(agy_runipd, "main", return_value=0) as m:
                    rc = cli.main(argv)
                self.assertEqual(rc, 0)
                m.assert_called_once_with(expected)

        rc, out, err = _run_cli(["agy"])
        self.assertIn("runipd", out + err)


# --- driverfin-01 (p7peqf): agy driver self-finalize (aw ipd begin before + aw ipd finalize after) ---


def _init_repo_with_conforming_plan(repo: Path, id6: str = "agy001") -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
    plan.write_text(_CONFORMING_PLAN.format(id6=id6), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return plan


class AgySelfFinalizeTests(unittest.TestCase):
    """The agy driver self-finalizes exactly as the oc driver does: `aw ipd begin` before the
    execute turn (fail-closed) and `aw ipd finalize` after a verified turn (programmatic scope
    reconciliation), reusing the SAME gated lifecycle surface. Parity with test_oc_runipd."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_driver_actor_is_parenthesis_free(self):
        self.assertEqual(
            agy_runipd.driver_actor({"options": {"model": "opus-4.8"}}),
            "aw agy run model=opus-4.8",
        )
        self.assertNotIn("(", agy_runipd.driver_actor({"options": {"model": "x"}}))
        self.assertEqual(agy_runipd.driver_actor({"options": {}}), "aw agy run")

    def test_begin_writes_receipt_then_finalize_moves_to_executed(self):
        from agent_workflows import ipd_lifecycle

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            actor = agy_runipd.driver_actor({"options": {"model": "opus"}})

            rc, msg = agy_runipd.driver_begin(repo, "agy001", actor)
            self.assertEqual(rc, 0, msg)
            self.assertTrue(ipd_lifecycle.receipt_path_for(repo, "agy001").is_file())

            (repo / "src").mkdir()
            (repo / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=repo, check=True)

            reasons, acks = agy_runipd._compute_scope_reconciliation(repo, plan)
            self.assertEqual(reasons, {})
            self.assertEqual(acks, {})

            rc, msg = agy_runipd.driver_finalize(
                repo, plan, "agy001", actor, "self-finalize demo verified"
            )
            self.assertEqual(rc, 0, msg)
            executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
            self.assertTrue(executed.is_file())
            self.assertIn("- Status: executed", executed.read_text(encoding="utf-8"))

    def _state_and_item(self, repo, plan, self_finalize=True):
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
                "model": "opus",
                "self_finalize": self_finalize,
                "no_verify": True,
                # p7peqf wiring parity tests run in the MAIN tree; driverfin-02 isolation is covered
                # by AgyWorktreeIsolationTests below.
                "isolate_worktree": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo):
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def test_begin_refusal_blocks_child_no_agent_turn(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            calls = []

            with (
                mock.patch.object(
                    agy_runipd,
                    "driver_begin",
                    lambda r, i, a: calls.append("begin") or (1, "refused"),
                ),
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    lambda *a, **k: (
                        calls.append("turn") or (0, "s", str(run_dir / "l"), ["agy"])
                    ),
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                calls, ["begin"], "agent turn must NOT run after begin refusal"
            )
            self.assertEqual(item["status"], "fail-begin")
            self.assertIn("begin_refusal", item)

    def test_finalize_fires_on_verified_and_marks_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            state["options"]["no_verify"] = False

            (run_dir / "outcomes" / "01-agy001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-agy001-verification.json").write_text(
                json.dumps(
                    {
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m unittest tests.test_from_backlog -v"],
                    }
                ),
                encoding="utf-8",
            )

            fin = []

            def fake_finalize(r, p, i, a, m):
                fin.append((i, a, m))
                executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
                executed.parent.mkdir(parents=True, exist_ok=True)
                plan.rename(executed)
                return 0, "finalized"

            with (
                mock.patch.object(
                    agy_runipd, "driver_begin", lambda r, i, a: (0, "ok")
                ),
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    lambda *a, **k: (0, "s", str(run_dir / "l"), ["agy"]),
                ),
                mock.patch.object(agy_runipd, "driver_finalize", fake_finalize),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(fin), 1)
            self.assertTrue(fin[0][1].startswith("aw agy run"))
            self.assertTrue(fin[0][2])
            self.assertEqual(item["status"], "executed")

    def test_finalize_refusal_leaves_not_executed_and_not_forced(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            state["options"]["no_verify"] = False

            (run_dir / "outcomes" / "01-agy001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-agy001-verification.json").write_text(
                json.dumps(
                    {
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m unittest tests.test_from_backlog -v"],
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(
                    agy_runipd, "driver_begin", lambda r, i, a: (0, "ok")
                ),
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    lambda *a, **k: (0, "s", str(run_dir / "l"), ["agy"]),
                ),
                mock.patch.object(
                    agy_runipd,
                    "driver_finalize",
                    lambda *a, **k: (1, "refused: needs a --scope-reason"),
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-gate")
            self.assertIn("finalize_refusal", item)
            self.assertTrue(plan.is_file(), "plan must not move on finalize refusal")


class AgyWorktreeIsolationTests(unittest.TestCase):
    """driverfin-02 (emus4n) parity for the agy driver: each execute child runs in its own worktree;
    the main tree stays clean during the turn; a verified child integrates back to main via the
    REUSED gate; a non-passing gate defers rather than faking executed."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def _state_and_item(self, repo, plan):
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
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_verify": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo):
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def _fake_agent_commits_in_worktree(self, run_dir):
        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
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
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def test_main_tree_clean_during_turn_and_receipt_under_main(self):
        # V-01 (agy): main tree clean during the turn; worktree at repo/.aw/worktrees/agy001 on
        # aw/lane/agy001; begin receipt under MAIN repo's .aw/state/.
        from agent_workflows import ipd_lifecycle

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            observed = {}

            def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                if kwargs.get("log_suffix") == "verify":
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
                    return 0, "vses", str(run_dir / "vlog"), ["agy"]
                observed["main_status"] = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout
                observed["work_dir"] = work_dir
                observed["wt_expected"] = str(
                    (repo / ".aw" / "worktrees" / "agy001").resolve()
                )
                observed["wt_branch"] = subprocess.run(
                    ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
                    cwd=work_dir,
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                wt = Path(work_dir)
                (wt / "src").mkdir(parents=True, exist_ok=True)
                (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
                subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
                (
                    run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
                ).write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            # defreport (`b7xarm`): a CONFORMING agent now states its defect
                            # report affirmatively. Without it the driver correctly spends its
                            # one same-session re-ask, and this fake would then re-run its own
                            # `git commit` and fail on an already-clean tree.
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(run_dir / "log"), ["agy"]

            with mock.patch.object(agy_runipd, "run_agy_turn", fake_turn):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(observed["main_status"].strip(), "")
            self.assertEqual(observed["work_dir"], observed["wt_expected"])
            self.assertEqual(observed["wt_branch"], "aw/lane/agy001")
            # The receipt ANCHORS on the main checkout (dh0uno). See the oc twin for the full
            # rationale: the previous `assertTrue(...is_file())` passed for the wrong reason, because
            # finalize runs with the LANE as its repo and so consumed the lane's FORKED receipt,
            # orphaning this one. With one receipt, a clean finalize consumes it, so absence is the
            # correct post-condition. The lane-vs-main equality is proved against a LIVE worktree in
            # tests/test_statefork_dh0uno.py, not here: by this point the lane is integrated and torn
            # down, so its path has no git identity left to collapse onto the checkout.
            receipt = ipd_lifecycle.receipt_path_for(repo, "agy001")
            self.assertEqual(
                receipt,
                # git reports the canonical (symlink-resolved) checkout, so compare against
                # the resolved repo (macOS /var -> /private/var, Windows 8.3 short names).
                repo.resolve()
                / ".aw"
                / "state"
                / "ipd-lifecycle"
                / "agy001.receipt.json",
            )
            self.assertFalse(
                receipt.is_file(),
                "a completed finalize must consume the one begin receipt, leaving no orphan",
            )

    def test_verified_child_integrates_to_main_and_worktree_removed(self):
        # V-02 (agy, passed): routes through the reused gate, integrates to main, tears down worktree.
        from agent_workflows import orchestrate_isolation

        gate_calls = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            with (
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(gate_calls), 1, "must route through the reused gate")
            self.assertEqual(item["status"], "executed")
            executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
            self.assertTrue(executed.is_file())
            self.assertTrue((repo / "src" / "demo.txt").is_file())
            self.assertFalse((repo / ".aw" / "worktrees" / "agy001").exists())
            main_status = subprocess.run(
                ["git", "status", "--short"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(main_status, "")

    def test_non_passing_gate_defers_not_faked_executed(self):
        # V-02 (agy, non-passing): combined-red -> NOT integrated, recorded, worktree preserved.
        # driverfin-03 (7kbtkw) E-02 refines the recorded state to the dedicated `merge-conflict`.
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            def failing_runner_factory(*a, **k):
                return lambda _diff, _files: False

            with (
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    agy_runipd,
                    "make_integration_validation_runner",
                    failing_runner_factory,
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            self.assertIn("integration_deferral", item)
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertIn("preserved_branch", item)
            self.assertEqual(item["preserved_branch"], "aw/lane/agy001")


class AgyFailClosedIntegrationGuardTests(unittest.TestCase):
    """driverfin-03 (7kbtkw) parity for the agy driver: fail-closed dirty-tree guard (E-01) +
    merge-back conflict handling (E-02)."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def _state_and_item(self, repo, plan):
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
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_verify": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo):
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def _fake_agent_commits_in_worktree(self, run_dir):
        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
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
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def _fake_agent_also_dirties_main(self, run_dir, repo):
        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
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
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
            # Contaminate MAIN on the overlapping path AFTER begin (un-owned, uncommitted).
            (repo / "src").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "demo.txt").write_text("un-owned dirt\n", encoding="utf-8")
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def _fake_agent_renames_in_worktree(self, run_dir, repo, *, orig, dest, dirty):
        """An agent whose lane RENAMES a tracked file, then dirties the rename ORIGIN in main.

        dirtygates-02 (`metc8b`), agy twin. `changed_files` comes from `git diff --name-only`, which
        applies rename detection and reports only ``dest``, so dirt on ``orig`` PASSES the pre-merge
        `dirty_tree_overlap` guard while the merge must still delete ``orig`` and git refuses to start.
        """

        def fake_turn(state, rd, item, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("log_suffix") == "verify":
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
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            subprocess.run(["git", "mv", orig, dest], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", f"demo: rename {orig} -> {dest}"],
                cwd=wt,
                check=True,
            )
            (repo / orig).write_text(dirty, encoding="utf-8")
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
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

    def test_a_real_git_local_changes_refusal_is_DEFERRED_not_recorded_merge_conflict(
        self,
    ):
        """dirtygates-02 (`metc8b`) E-02, end-to-end on the agy host (the thinner suite).

        Both hosts branch on `kind`, so proving this on one only would leave the other free to drift.
        Here the PRE-MERGE guard PASSES and the refusal comes from git itself; the recorded kind must
        be the deferrable `integration-blocked`, not the terminal `merge-conflict` that stranded lanes
        `bzz5e6` and `f6idxs` on 2026-09-13.
        """
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            body = "".join(f"line {i}\n" for i in range(40))
            (repo / "moved.txt").write_text(body, encoding="utf-8")
            subprocess.run(["git", "add", "moved.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add moved.txt"], cwd=repo, check=True
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            dirty = body + "un-owned local edit\n"

            # mergedirty-01 (`fujm0y`), agy twin of the oc note: the write set is forced UNKNOWN (the
            # shipped older-git fallback) so this case still reaches GIT's OWN refusal and keeps
            # testing the structural discriminator. With the widened pre-merge guard active it would
            # refuse EARLIER, yielding the same kind without ever attempting a merge, so the "Your
            # local changes" assertion below would be testing nothing.

            with (
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    self._fake_agent_renames_in_worktree(
                        run_dir, repo, orig="moved.txt", dest="dest.txt", dirty=dirty
                    ),
                ),
                mock.patch.object(
                    runner_shared, "merge_write_set", lambda _repo, _branch: None
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                item["integration_ladder"]["kind"],
                "merge-retry",
                f"git refused to START the merge: {item.get('integration_deferral')}",
            )
            self.assertEqual(item["status"], "merge-retry")
            self.assertNotIn(item["status"], agy_runipd.TERMINAL_STATES)
            reason = item["integration_deferral"]
            self.assertIn("Your local changes", reason)
            self.assertIn("moved.txt", reason)
            self.assertNotIn("merge-back conflict", reason)
            # MAIN untouched: HEAD unmoved, the un-owned edit intact, no partial merge left behind.
            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout.strip(),
                head_before,
            )
            self.assertEqual((repo / "moved.txt").read_text(encoding="utf-8"), dirty)
            self.assertFalse((repo / ".git" / "MERGE_HEAD").exists())
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertEqual(item.get("preserved_branch"), "aw/lane/agy001")

    def test_dirty_overlapping_base_refuses_integration(self):
        # V-01 (agy): a dirty overlapping MAIN base refuses integration (integration-blocked); gate
        # not invoked; MAIN's un-owned edit intact; verified branch/worktree preserved.
        from agent_workflows import orchestrate_isolation

        gate_calls = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            with (
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    self._fake_agent_also_dirties_main(run_dir, repo),
                ),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            # integpath-03 (`51vw4y`): the REFUSAL is unchanged and every fail-closed assertion below
            # is kept; only the DISPOSITION after it moved, from terminal `integration-blocked` on the
            # first refusal to the NON-TERMINAL `integration-deferred`, so the transient condition no
            # longer permanently strands verified work. Kept symmetric with the oc twin (CID-3).
            self.assertEqual(len(gate_calls), 0)
            self.assertEqual(item["status"], "merge-retry")
            self.assertNotIn(
                item["status"],
                agy_runipd.TERMINAL_STATES,
                "the first refusal must be NON-terminal, or the item is never re-attempted",
            )
            self.assertIn("integration_deferral", item)
            self.assertIn("src/demo.txt", item["integration_deferral"])
            self.assertTrue(item["integration_ladder"]["deferred"])
            self.assertEqual(item["integration_ladder"]["attempts_used"], 1)
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertEqual(
                (repo / "src" / "demo.txt").read_text(encoding="utf-8"),
                "un-owned dirt\n",
            )
            self.assertEqual(item.get("preserved_branch"), "aw/lane/agy001")
            self.assertTrue((repo / ".aw" / "worktrees" / "agy001").exists())
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-deferred", events)

    def test_non_passing_gate_records_merge_conflict_main_pristine(self):
        # V-02 (agy): a non-passing gate leaves MAIN pristine (HEAD unchanged, no markers), records
        # merge-conflict + preserved branch, emits the event, and does not integrate.
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()

            def failing_runner_factory(*a, **k):
                return lambda _diff, _files: False

            with (
                mock.patch.object(
                    agy_runipd,
                    "run_agy_turn",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    agy_runipd,
                    "make_integration_validation_runner",
                    failing_runner_factory,
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-merge")
            self.assertIn("integration_deferral", item)
            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(head_before, head_after)
            main_status = subprocess.run(
                ["git", "status", "--short"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(main_status, "")
            self.assertFalse((repo / ".git" / "MERGE_HEAD").exists())
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertEqual(item.get("preserved_branch"), "aw/lane/agy001")
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-merge-conflict", events)

    def test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate(self):
        """integpath-03 (`51vw4y`) E-07: the incident's shape, survived on the AGY host.

        ASSERTED HERE INDEPENDENTLY RATHER THAN INFERRED FROM THE OC RESULT, which the plan requires
        explicitly: the two runner suites are asymmetric (the agy side has far fewer tests and several
        of the largest diverged symbols have zero agy coverage), so a green oc test can hide an agy-side
        regression. The ladder is shared, but the BINDINGS are per host, and a mis-bound host is exactly
        the class of defect this repository has already paid for (`--full-auto` defaulting oppositely on
        the two hosts).
        """
        from agent_workflows import orchestrate_isolation

        gate_calls: list = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        agent_turns: list = []

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            state["options"]["integration_retry_limit"] = 10
            state["options"]["on_integration_blocked"] = "defer"

            base_agent = self._fake_agent_also_dirties_main(run_dir, repo)

            def counting_agent(*a, **k):
                agent_turns.append(k.get("log_suffix"))
                return base_agent(*a, **k)

            with (
                mock.patch.object(agy_runipd, "run_agy_turn", counting_agent),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "merge-retry")
                self.assertNotIn(item["status"], agy_runipd.TERMINAL_STATES)
                self.assertEqual(len(gate_calls), 0)
                turns_after_first = len(agent_turns)

                # The co-worker's dirt clears, and the re-attempt runs with no new agent turn.
                (repo / "src" / "demo.txt").unlink()
                records = agy_runipd.retry_deferred_integrations(run_dir, state)

            self.assertEqual(
                [r["outcome"] for r in records], ["integrated"], f"{records}"
            )
            self.assertEqual(item["status"], "executed")
            self.assertEqual(
                len(agent_turns),
                turns_after_first,
                "a deferred re-attempt must spend NO agent turn",
            )
            self.assertEqual(
                len(gate_calls), 1, "the successful re-attempt must run the full gate"
            )
            self.assertEqual(
                (repo / "src" / "demo.txt").read_text(encoding="utf-8"), "demo\n"
            )
            self.assertTrue(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            # THIS HOST's label is on the merge, which is what proves the per-host binding survived
            # into the RE-ATTEMPT path and not only into the first attempt.
            subject = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=repo,
                text=True,
                capture_output=True,
            ).stdout.strip()
            self.assertNotIn("aw oc run", subject)
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-deferred", events)
            self.assertIn("ipd-integrated-after-deferral", events)

    def test_dirty_tree_overlap_helper_reports_only_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            (repo / "unrelated.txt").write_text("dirt\n", encoding="utf-8")
            self.assertEqual(agy_runipd.dirty_tree_overlap(repo, ["src/x.py"]), [])
            (repo / "src").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "x.py").write_text("dirt\n", encoding="utf-8")
            self.assertEqual(
                agy_runipd.dirty_tree_overlap(repo, ["src/x.py", "src/y.py"]),
                ["src/x.py"],
            )
            self.assertEqual(agy_runipd.dirty_tree_overlap(repo, []), [])

    def test_this_hosts_merge_subject_still_says_aw_agy_run(self):
        """The host label on THIS driver, from a REAL merge.

        Without this the extraction's riskiest wiring would be proven on one host only, and the agy
        suite is the thinner of the two, which is exactly where a silent regression would live.
        """
        from agent_workflows import worktree_lease

        def git(cwd, *args):
            return subprocess.run(
                ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
            ).stdout.strip()

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            base = git(repo, "rev-parse", "HEAD")
            git(repo, "branch", "aw/lane/agy001")
            wt = Path(temp) / "wt"
            git(repo, "worktree", "add", "-q", str(wt), "aw/lane/agy001")
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "x.py").write_text("lane\n", encoding="utf-8")
            git(wt, "add", "src/x.py")
            git(wt, "commit", "-qm", "lane writes src/x.py")
            # Advance main so `--ff-only` fails and the labelled `--no-ff` merge is taken.
            (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
            git(repo, "add", "other.txt")
            git(repo, "commit", "-qm", "main advances")

            handle = worktree_lease.WorktreeHandle(
                lane_id="agy001",
                path=wt,
                branch="aw/lane/agy001",
                base_commit=base,
            )
            integrated, reason, kind = agy_runipd.integrate_lane_branch(
                repo, handle, "agy001", lambda _d, _f: True
            )

            self.assertTrue(integrated, reason)
            self.assertEqual(kind, "integrated")
            subject = git(repo, "log", "-1", "--pretty=%s")
            self.assertEqual(
                subject, "integrate(aw agy run): merge verified lane agy001 to main"
            )
            self.assertNotIn("aw oc run", subject)

    def test_expand_selectors_reviews(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "p1": {
                    "set": "s1",
                    "file": ".aw/records/plans/pending/20260824-s1-01-p1.ipd.md",
                    "status": "to-review",
                    "order": 1,
                    "dependencies": [],
                },
                "p2": {
                    "set": "s1",
                    "file": ".aw/records/plans/pending/20260824-s1-02-p2.ipd.md",
                    "status": "approved",
                    "order": 2,
                    "dependencies": [],
                },
            },
            "sets": {
                "s1": {"order": ["p1", "p2"]},
            },
        }
        for alias in ("reviews", "review", "to-review"):
            expanded = agy_runipd.expand_selectors(manifest, [alias])
            self.assertEqual(expanded, ["p1"])


class AgyFullAutoApprovalTests(unittest.TestCase):
    """fullauto 97df1z E-03: the agy driver's `--full-auto` gate, which was broken in the SAME way.

    Parity with `test_oc_runipd`'s auto-approve tests. The bug existed in BOTH drivers (the agy copy
    of the predicate had even lost its docstrings), so a fix proven only on oc would have left
    `aw agy run --full-auto` dead. These assert the shared predicate is the one in use and that the
    driver clears to the HONEST `auto-approved` status rather than machine-asserting `--by-human`.
    """

    def test_predicate_is_the_shared_one_and_local_copies_are_gone(self):
        from agent_workflows import plan_readiness

        self.assertIs(
            agy_runipd.is_plan_review_approved, plan_readiness.is_plan_review_approved
        )
        self.assertFalse(hasattr(agy_runipd, "extract_last_history_entry"))

    def test_structured_readiness_decides_and_prose_does_not(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            clear = root / "clear.ipd.md"
            clear.write_text(
                "# P\n\n- Id: agy010\n- Status: reviewed\n"
                "- Readiness: go-pending-approval\n\n"
                "## Workflow history\n- 2026-08-29 /plan-review (agy): APPROVE; PR-001\n",
                encoding="utf-8",
            )
            self.assertTrue(agy_runipd.is_plan_review_approved(clear))

            refuse = root / "refuse.ipd.md"
            refuse.write_text(
                "# P\n\n- Id: agy011\n- Status: reviewed\n- Readiness: no-go\n\n"
                "## Workflow history\n"
                "- 2026-08-29 /plan-review (agy): APPROVE. Readiness: GO - PENDING HUMAN APPROVAL.\n",
                encoding="utf-8",
            )
            self.assertFalse(agy_runipd.is_plan_review_approved(refuse))

    def test_set_plan_approved_uses_auto_approved_and_never_by_human(self):
        """OQ-02: the machine must not assert the human-approval attestation."""
        captured: list = []

        def fake_run_checked(argv, cwd=None, env=None):
            captured.append(list(argv))
            return ""

        with mock.patch.object(agy_runipd, "run_checked", fake_run_checked):
            agy_runipd.set_plan_approved(Path("/tmp/repo"), "agy012")

        self.assertEqual(len(captured), 1)
        argv = captured[0]
        self.assertIn("auto-approved", argv)
        self.assertNotIn("approved", argv)  # the human tier is never requested
        self.assertNotIn("--by-human", argv)
        self.assertIn("--actor", argv)
        self.assertIn(agy_runipd.FULL_AUTO_ACTOR, argv)


# --------------------------------------------------------------------------------------------------
# revsweep 76gsmv: the agy half of the selector documentation, the `aw agy review` alias, `--action`
# legality, and the empty sweep's exit code. PARITY IS THE POINT: the plan's F-7 measured the two
# runners' sweep predicates as verbatim duplicates, so a change proven only on oc would leave this
# host behind, which is exactly how `aw agy run --full-auto` was once shipped broken (fullauto 97df1z).
# --------------------------------------------------------------------------------------------------


class AgyReviewsSelectorDocumentedTests(unittest.TestCase):
    def test_reviews_selector_documented_in_parser(self):
        desc = agy_runipd.build_parser().description or ""
        self.assertIn("SELECTOR TYPES:", desc)
        self.assertIn("reviews:", desc)
        self.assertIn("all:", desc)
        self.assertIn("IPDs only", desc)
        self.assertRegex(desc, r"runagy reviews\b")

        help_text = agy_runipd.build_parser().format_help()
        for spelling in ("reviews", "review", "to-review"):
            self.assertIn(spelling, help_text)


class AgyReviewAliasTests(unittest.TestCase):
    def test_review_alias_reaches_driver(self):
        for group in ("agy", "antigravity"):
            with self.subTest(group=group):
                captured = {}

                def fake_main(argv, _c=captured):
                    _c["argv"] = list(argv)
                    return 0

                with mock.patch.object(agy_runipd, "main", fake_main):
                    rc, out, err = _run_cli([group, "review"])
                self.assertEqual(rc, 0, out + err)
                self.assertNotIn("invalid choice", out + err)
                self.assertEqual(captured["argv"], ["reviews", "--action", "review"])

        captured_tail = {}

        def fake_main_tail(argv):
            captured_tail["argv"] = list(argv)
            return 0

        with mock.patch.object(agy_runipd, "main", fake_main_tail):
            rc, _out, _err = _run_cli(
                ["agy", "review", "5ahblp", "--repo", "/tmp/x", "--session", "s1"]
            )
        self.assertEqual(rc, 0)
        self.assertEqual(
            captured_tail["argv"],
            ["5ahblp", "--repo", "/tmp/x", "--session", "s1", "--action", "review"],
        )


class AgyIntegrateVerbTests(unittest.TestCase):
    """integpath-04 (`rl67b0`) E-02/E-05, agy half: the verb exists HERE too, at BOTH spellings.

    The DECISION cases live once, in `tests/test_runner_shared.py::ReintegrationVerbTests`, because
    `runner_shared.reintegrate_lane` is the single implementation. What must be proven per host is what
    only that host can get wrong: reachability at both spellings, and the merge subject's own label. The
    agy suite is the thinner of the two, which is exactly where a one-sided regression would hide.
    """

    def test_integrate_reaches_the_driver_instead_of_invalid_choice(self):
        for group in ("agy", "antigravity"):
            with self.subTest(group=group):
                captured = {}

                def fake_main(argv, _c=captured):
                    _c["argv"] = list(argv)
                    return 0

                with mock.patch.object(agy_runipd, "main", fake_main):
                    rc, out, err = _run_cli([group, "integrate", "mm6wuz"])
                self.assertEqual(rc, 0, out + err)
                self.assertNotIn("invalid choice", out + err)
                self.assertEqual(captured["argv"], ["integrate", "mm6wuz"])

    def test_the_verbatim_tail_reaches_the_driver(self):
        captured = {}

        def fake_main(argv, _c=captured):
            _c["argv"] = list(argv)
            return 0

        with mock.patch.object(agy_runipd, "main", fake_main):
            rc, _out, _err = _run_cli(
                ["agy", "integrate", "mm6wuz", "--repo", "/tmp/x", "--run-id", "r1"]
            )
        self.assertEqual(rc, 0)
        self.assertEqual(
            captured["argv"],
            ["integrate", "mm6wuz", "--repo", "/tmp/x", "--run-id", "r1"],
        )

    def test_the_driver_subcommand_help_states_the_no_turn_and_suite_costs(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            agy_runipd.main(["integrate", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = " ".join(out.getvalue().split())
        self.assertIn("COSTS NO AGENT TURN", text)
        self.assertIn("repository suite in the PRIMARY checkout", text)
        self.assertIn("merge-and-revalidate gate", text)
        # The examples must name THIS host's command, or an operator copies the wrong line.
        self.assertIn("aw agy run integrate", text)

    def test_both_spellings_reach_the_shared_implementation_once(self):
        for argv, route in (
            (["integrate", "zzzzzz"], "driver"),
            (["agy", "integrate", "zzzzzz"], "alias"),
        ):
            calls: list = []

            def spy(repo, id6, **kwargs):
                calls.append((id6, sorted(kwargs)))
                return runner_shared.ReintegrationOutcome(
                    integrated=False, code="no-lane-record", reason="fake"
                )

            with tempfile.TemporaryDirectory() as temp:
                repo = Path(temp) / "repo"
                repo.mkdir()
                subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
                with mock.patch.object(runner_shared, "reintegrate_lane", spy):
                    if route == "driver":
                        rc = agy_runipd.main([*argv, "--repo", str(repo)])
                    else:
                        rc, _o, _e = _run_cli([*argv, "--repo", str(repo)])
                self.assertEqual(rc, 1, f"{argv}: a refusal must exit 1")
                self.assertEqual(len(calls), 1, f"{argv}: exactly one shared call")
                self.assertEqual(calls[0][0], "zzzzzz")
                self.assertIn("suite_check", calls[0][1])

    def test_this_hosts_merge_subject_still_says_aw_agy_run(self):
        """From a REAL merge: the label lands on MAIN, so a mis-binding is invisible until an audit."""
        from tests.test_runner_shared import (
            _passing_suite,
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
            _write_run_state,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _repo_with_pending_plan(root, "agi001")
            lane = _verified_lane(repo, root, "agi001")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            # Advance main so `--ff-only` fails and the LABELLED `--no-ff` merge is taken.
            (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
            subprocess.run(["git", "add", "other.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "main advances"], cwd=repo, check=True
            )

            with mock.patch.object(agy_runipd, "run_suite_check", _passing_suite):
                rc = agy_runipd.main(["integrate", "agi001", "--repo", str(repo)])

            self.assertEqual(rc, 0)
            subject = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=repo,
                text=True,
                capture_output=True,
            ).stdout.strip()
            self.assertEqual(
                subject, "integrate(aw agy run): merge verified lane agi001 to main"
            )
            self.assertNotIn("aw oc run", subject)


class AgyResumeIntegratesInsteadOfDispatchingTests(unittest.TestCase):
    """integpath-04 (`rl67b0`) E-03/E-06, agy half: THE TWO ABSENCES on this host's real `run_queue`."""

    def _run(self, repo: Path, state: dict, *, retry_incomplete: bool):
        from tests.test_runner_shared import _passing_suite, _write_run_state

        run_dir = _write_run_state(repo, state, run_id="run-resume")

        def must_not_launch(*_a, **_k):
            raise AssertionError(
                "an agent turn was DISPATCHED: the resume paid for a turn where a merge would do"
            )

        with (
            mock.patch.object(agy_runipd, "run_agy_turn", must_not_launch),
            mock.patch.object(agy_runipd, "run_suite_check", _passing_suite),
        ):
            rc = agy_runipd.run_queue(run_dir, retry_incomplete=retry_incomplete)
        return rc, json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

    def test_a_bare_resume_merges_with_no_turn_and_no_second_lane(self):
        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _repo_with_pending_plan(root, "agr001")
            lane = _verified_lane(repo, root, "agr001")
            state = {"repo": str(repo), "queue": [_stranded_item(lane)]}

            _rc, final = self._run(repo, state, retry_incomplete=False)

            self.assertEqual(final["queue"][0]["status"], "executed")
            self.assertTrue((repo / "src" / "agr001.txt").is_file())
            self.assertNotIn(
                "_attempt2",
                subprocess.run(
                    ["git", "branch", "--list", "aw/lane/agr001*"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout,
            )

    def test_with_the_flag_passed_it_integrates_rather_than_requeuing(self):
        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = _repo_with_pending_plan(root, "agr002")
            lane = _verified_lane(repo, root, "agr002")
            state = {"repo": str(repo), "queue": [_stranded_item(lane)]}

            _rc, final = self._run(repo, state, retry_incomplete=True)

            item = final["queue"][0]
            self.assertEqual(item["status"], "executed")
            self.assertNotIn("recovery_next", item)


class AgyActionLegalityTests(unittest.TestCase):
    def test_action_vocabulary_and_parser(self):
        import argparse as _ap
        from agent_workflows import oc_runipd

        self.assertEqual(agy_runipd.ACTION_CHOICES, oc_runipd.ACTION_CHOICES)
        self.assertEqual(agy_runipd.ACTION_IMPLEMENTED, oc_runipd.ACTION_IMPLEMENTED)
        parser = agy_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        action_arg = next(
            a for a in sub.choices["start"]._actions if a.dest == "action"
        )
        self.assertEqual(tuple(action_arg.choices or ()), agy_runipd.ACTION_CHOICES)
        self.assertIsNone(action_arg.default)

    def test_action_enforcement_rules(self):
        agy_runipd.enforce_requested_action("review", [("a", "to-review", "review")])
        agy_runipd.enforce_requested_action(None, [("a", "approved", "execute")])

        for status in ("approved", "reviewed", "auto-approved"):
            with self.subTest(status=status):
                with self.assertRaises(agy_runipd.DriverError) as ctx:
                    agy_runipd.enforce_requested_action(
                        "review", [("a", status, "execute")]
                    )
                self.assertIn("illegal", str(ctx.exception))

        for action in ("plan", "execute"):
            with self.subTest(action=action):
                with self.assertRaises(agy_runipd.DriverError) as ctx:
                    agy_runipd.enforce_requested_action(
                        action, [("a", "to-review", "review")]
                    )
                self.assertIn("not implemented", str(ctx.exception))


class AgyEmptyReviewSweepTests(unittest.TestCase):
    _MANIFEST = {
        "schema_version": 1,
        "plans": {
            "appr01": {
                "set": "s1",
                "file": ".aw/records/plans/pending/20260828-s1-01-appr01-x.ipd.md",
                "status": "approved",
                "order": 1,
                "dependencies": [],
            }
        },
        "sets": {"s1": {"order": ["appr01"]}},
    }

    def test_empty_sweep_exception_hierarchy(self):
        self.assertTrue(
            issubclass(agy_runipd.EmptyStatusSelection, agy_runipd.DriverError)
        )
        for spelling in ("reviews", "review", "to-review"):
            with self.subTest(spelling=spelling):
                with self.assertRaises(agy_runipd.EmptyStatusSelection):
                    agy_runipd.expand_selectors(self._MANIFEST, [spelling])

        manifest_done = {
            "schema_version": 1,
            "plans": {
                "done01": {
                    "set": "s1",
                    "file": ".aw/records/plans/executed/20260828-s1-01-done01-x.ipd.md",
                    "status": "executed",
                    "order": 1,
                    "dependencies": [],
                }
            },
            "sets": {"s1": {"order": ["done01"]}},
        }
        with self.assertRaises(agy_runipd.DriverError) as ctx:
            agy_runipd.expand_selectors(manifest_done, ["all"])
        self.assertNotIsInstance(ctx.exception, agy_runipd.EmptyStatusSelection)

    def test_main_exit_codes_for_empty_sweep_and_missing_id6(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@e.invalid"], cwd=repo, check=True
            )
            subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            (pending / "20260828-demo-01-appr01-demo.ipd.md").write_text(
                _CONFORMING_PLAN.format(id6="appr01"), encoding="utf-8"
            )
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = agy_runipd.main(["reviews", "--repo", str(repo), "--prepare-only"])
            self.assertEqual(rc, 0, out.getvalue() + err.getvalue())
            self.assertIn("Nothing awaiting review", out.getvalue())
            self.assertFalse((repo / ".aw" / "records" / "runs").is_dir())

            out2, err2 = io.StringIO(), io.StringIO()
            with redirect_stdout(out2), redirect_stderr(err2):
                rc2 = agy_runipd.main(["zzzz99", "--repo", str(repo), "--prepare-only"])
            self.assertEqual(rc2, 2, out2.getvalue() + err2.getvalue())


class AgyVerbosityFlagTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-06/V-06: `-v` parses IDENTICALLY to the oc driver.

    The property under test is PARITY, so every case here mirrors
    `tests/test_oc_runipd_cli.py::VerbosityFlagTests`. A leading `-v` used to be swallowed by the
    implicit-start `subcommands` set in this driver too; both drivers' sets were changed together
    because `tests/test_runner_stop_triggers.py` regexes both source files.
    """

    def _parse(self, argv):
        return agy_runipd.build_parser().parse_args(argv)

    def test_verbosity_parsing_and_parity(self):
        from agent_workflows import oc_runipd

        for argv, expected in (
            (["start", "sel"], 0),
            (["start", "sel", "-v"], 1),
            (["start", "sel", "-vv"], 2),
            (["start", "sel", "--verbose"], 1),
            (["start", "-v", "sel"], 1),
        ):
            with self.subTest(start=argv):
                args = self._parse(argv)
                self.assertEqual(args.verbosity, expected)
                self.assertEqual(args.selectors, ["sel"])
                self.assertEqual(
                    agy_runipd.build_parser().parse_args(argv).verbosity,
                    oc_runipd.build_parser().parse_args(argv).verbosity,
                )

        self.assertIsNone(self._parse(["resume", "run-x"]).verbosity)
        for argv, expected in (
            (["resume", "run-x", "-v"], 1),
            (["resume", "run-x", "-vv"], 2),
            (["resume", "-v", "run-x"], 1),
        ):
            with self.subTest(resume=argv):
                self.assertEqual(self._parse(argv).verbosity, expected)

    def test_flags_forwarded_and_help(self):
        import argparse as _ap

        for argv in (["-v", "somesetid"], ["somesetid", "-vv"]):
            with self.subTest(argv=argv):
                with mock.patch.object(agy_runipd, "main", return_value=0) as m:
                    cli.main(["agy", "run", *argv])
                m.assert_called_once_with(argv)

        parser = agy_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        for cmd in ("start", "resume"):
            with self.subTest(cmd=cmd):
                self.assertIn("--verbose", sub.choices[cmd].format_help())

    def test_verbosity_is_frozen_and_honored_on_resume(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run-agy-verbosity"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-agy-verbosity",
                "repo": td,
                "created_at": "2026-09-06T00:00:00+00:00",
                "updated_at": "2026-09-06T00:00:00+00:00",
                "options": {"output_mode": "clean", "verbosity": 2},
                "queue": [],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            agy_runipd.run_queue(run_dir, retry_incomplete=False, verbosity=None)
            reloaded = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(reloaded["options"]["verbosity"], 2)

            agy_runipd.run_queue(run_dir, retry_incomplete=False, verbosity=1)
            reloaded = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(reloaded["options"]["verbosity"], 1)

    def test_render_agy_event_and_tracker(self):
        from agent_workflows.render_stream import StreamTracker

        pal = agy_runipd.Palette(False)
        tracker = StreamTracker()

        # Suppress system protocol placeholder
        placeholder = "[System: Empty message content sanitised to satisfy protocol]"
        self.assertIsNone(agy_runipd.render_agy_event(placeholder, pal))

        # Unparseable line rendered as-is
        unparseable = "unparseable raw line"
        res = agy_runipd.render_agy_event(unparseable, pal)
        self.assertIsNotNone(res)
        self.assertIn(unparseable, res)

        # Usage and cost update
        event_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "step_index": 1,
                    "state": "DONE",
                    "step_type": "agent_response",
                    "usage": {
                        "input_tokens": 1200,
                        "output_tokens": 340,
                        "cache_read_tokens": 4500,
                    },
                    "cost": 0.0125,
                },
            }
        )
        self.assertIsNone(agy_runipd.render_agy_event(event_line, pal, tracker=tracker))
        self.assertEqual(tracker.input_tokens, 1200)
        self.assertEqual(tracker.output_tokens, 340)
        self.assertEqual(tracker.cache_tokens, 4500)
        self.assertAlmostEqual(tracker.cost, 0.0125, places=4)

        # Modified files tracking
        repo_root = "/mock/repo"
        evt_write = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "write_to_file",
                        "parameters": {"TargetFile": "/mock/repo/src/new_mod.py"},
                    },
                },
            }
        )
        agy_runipd.render_agy_event(
            evt_write, pal, repo_root=repo_root, tracker=tracker
        )
        self.assertIn("src/new_mod.py", tracker.modified_files)

        # Active event suppression
        active_evt = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "ACTIVE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": "git status"},
                    },
                },
            }
        )
        self.assertIsNone(agy_runipd.render_agy_event(active_evt, pal))


class AgyDependencyPathsAreSharedTests(unittest.TestCase):
    """depreview 03ie04 E-03/E-06: THIS HOST's two dependency paths must be the shared ones.

    WHY THIS LIVES IN THE AGY SUITE and is not merely a line in the cross-driver test: agy is the host
    whose fix was missed. Its DISPATCH path calls the re-exported ``dependency_status`` (whose body
    resolves ``dependency_status_detailed`` in oc's globals) while its DRAIN path calls
    ``dependency_status_detailed`` directly. This module used to DEFINE its own copy of the latter, so
    a dependency fix reached one path and not the other, and the copy was additionally broken: it never
    called ``edge_satisfied``, never called ``parse_dependency_token`` (so a typed ``executed:<id6>``
    edge was treated as a bare id6 and reported as resolving to no plan), and had no ``orchestrate``
    clause. Measured before the deletion: ``agy.dependency_status_detailed is
    oc.dependency_status_detailed`` was ``False``.
    """

    def _repo(self, tmp: Path, *, bucket: str, status: str) -> Path:
        repo = tmp / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        d = repo / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260908-demo-01-depaaa-x.ipd.md").write_text(
            "# IPD: dep\n\n"
            "- Date: 2026-09-08\n- Kind: child\n- Scope-Paths: x.py\n"
            f"- Item-Dependencies: none\n- Status: {status}\n- Set: demo\n"
            "- Order: 1\n- Id: depaaa\n\n## Goal\ng\n",
            encoding="utf-8",
        )
        return repo

    def _item(self, action: str) -> dict:
        return {
            "id6": "itemaa",
            "status": "queued",
            "action": action,
            "dependencies": ["executed:depaaa"],
            "position": 1,
            "setid": "demo",
            "configured_file": "",
        }

    def test_both_dependency_entry_points_are_the_shared_objects(self):
        """The IDENTITY pin. After the deletion this is what fails if the copy ever returns.

        Stated honestly: because both paths now call the SAME object, the behavioral agreement
        asserted below is true BY CONSTRUCTION. The identity assertion is therefore the one that
        carries the guarantee, and the behavioral test is what catches a re-fork that kept the name.
        """
        from agent_workflows import oc_runipd

        self.assertIs(agy_runipd.dependency_status, oc_runipd.dependency_status)
        self.assertIs(
            agy_runipd.dependency_status_detailed,
            oc_runipd.dependency_status_detailed,
            "agy must BIND the shared implementation, never define its own",
        )
        self.assertIs(agy_runipd.edge_satisfied, oc_runipd.edge_satisfied)

    def test_drain_path_resolves_typed_edge_and_orchestrator(self):
        for action in ("review", "execute"):
            with self.subTest(action=action):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket="executed", status="executed")
                    item = self._item(action)
                    state = {"repo": str(repo), "queue": [item]}
                    ok, missing, reasons = agy_runipd.dependency_status_detailed(
                        item, state
                    )
                    self.assertTrue(ok, f"reasons={reasons!r}")
                    self.assertEqual(missing, [])

        with tempfile.TemporaryDirectory() as t:
            repo = Path(t) / "repo"
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            (pending / "20260908-demo-00-orch00-x.ipd.md").write_text(
                "# IPD: orch\n\n- Date: 2026-09-08\n- Kind: orchestrator\n"
                "- Scope-Paths: x.py\n- Item-Dependencies: none\n- Status: approved\n"
                "- Set: demo\n- Order: 0\n- Id: orch00\n\n"
                "## Children\n\n| Order | Id | Title |\n|---|---|---|\n| 01 | child1 | c |\n",
                encoding="utf-8",
            )
            (pending / "20260908-demo-01-child1-x.ipd.md").write_text(
                "# IPD: child\n\n- Date: 2026-09-08\n- Kind: child\n- Scope-Paths: x.py\n"
                "- Item-Dependencies: none\n- Status: approved\n- Set: demo\n"
                "- Order: 1\n- Id: child1\n\n## Goal\ng\n",
                encoding="utf-8",
            )
            orch = {
                "id6": "orch00",
                "status": "queued",
                "action": "orchestrate",
                "dependencies": [],
                "position": 1,
                "setid": "demo",
                "configured_file": "",
            }
            child = dict(
                self._item("execute"), id6="child1", position=2, dependencies=[]
            )
            state = {"repo": str(repo), "queue": [orch, child]}
            ok, missing, reasons = agy_runipd.dependency_status_detailed(orch, state)
            self.assertFalse(ok)
            self.assertEqual(missing, ["executed:child1"])
            self.assertIn(
                "orchestrator waits for child child1", reasons["executed:child1"]
            )

    def test_edge_satisfaction_rules(self):
        # Review edge
        for status, expected in (
            ("reviewed", True),
            ("approved", True),
            ("to-review", False),
        ):
            with self.subTest(review_status=status):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket="pending", status=status)
                    item = self._item("review")
                    state = {"repo": str(repo), "queue": [item]}
                    for entry in ("dependency_status", "dependency_status_detailed"):
                        got = getattr(agy_runipd, entry)(item, state)
                        self.assertEqual(got[0], expected)

        # Execute edge not relaxed
        for status in ("reviewed", "approved"):
            with self.subTest(execute_status=status):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket="pending", status=status)
                    item = self._item("execute")
                    state = {"repo": str(repo), "queue": [item]}
                    ok, missing, _reasons = agy_runipd.dependency_status_detailed(
                        item, state
                    )
                    self.assertFalse(ok)
                    self.assertEqual(missing, ["executed:depaaa"])

        # Terminal directory still decides
        for status in ("EXECUTED (approved by maintainer)", "to-review"):
            for action in ("review", "execute"):
                with self.subTest(terminal_status=status, action=action):
                    with tempfile.TemporaryDirectory() as t:
                        repo = self._repo(Path(t), bucket="executed", status=status)
                        item = self._item(action)
                        state = {"repo": str(repo), "queue": [item]}
                        ok, _m, reasons = agy_runipd.dependency_status_detailed(
                            item, state
                        )
                        self.assertTrue(ok, f"reasons={reasons!r}")


class AgyTelemetryWiringTests(unittest.TestCase):
    def test_a_turn_emits_a_start_and_an_end_event_keyed_on_the_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = root / "run-20260913T000000Z-1"
            (run_dir / "sessions").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)
            prompt_file = run_dir / "prompts" / "01-prompt.md"
            prompt_file.write_text("prompt", encoding="utf-8")
            state = {
                "run_id": "run-20260913T000000Z-1",
                "repo": str(repo),
                "options": {
                    "output_mode": "quiet",
                    "model": "provider/model",
                    "agy_executable": "agy",
                },
            }
            item = {
                "id6": "agy001",
                "setid": "agyset",
                "position": 5,
                "action": "execute",
            }

            class FakeProc:
                def __init__(self, cmd, *args, **kwargs):
                    self.pid = 5252
                    self.stdout = iter(())
                    self.returncode = 0

                def poll(self):
                    return 0

                def wait(self, timeout=None):
                    return 0

            with mock.patch("subprocess.Popen", side_effect=FakeProc):
                rc, _sess, _log, _argv = agy_runipd.run_agy_turn(
                    state,
                    run_dir,
                    item,
                    prompt_file,
                    1,
                    session_id=None,
                    use_continue=False,
                )

            self.assertEqual(rc, 0)
            streams = sorted(runner_shared.telemetry_dir(run_dir).glob("*.jsonl"))
            self.assertEqual(len(streams), 1, streams)
            events = [
                json.loads(line)
                for line in streams[0].read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])
            for event in events:
                self.assertEqual(event["host"], "agy")
                self.assertEqual(event["phase"], "execute")
                self.assertEqual(event["attempt"], 1)
                self.assertEqual(event["position"], 5)
                self.assertEqual(event["ipd_id6"], "agy001")
                self.assertEqual(event["set_id"], "agyset")


class ToolIdentityAbortsTests(unittest.TestCase):
    """Regression test for tool identity abort (hp9rot E-04 / BUG-02)."""

    def test_tool_identity_aborts(self):
        """E-04: Mismatched child tool identity raises ToolIdentityError and terminates run immediately."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            state = {
                "run_id": "run-test",
                "created_at": "2026-08-28T00:00:00+00:00",
                "updated_at": "2026-08-28T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [
                    {
                        "position": 1,
                        "id6": "agy001",
                        "setid": "demo",
                        "status": "queued",
                        "configured_file": str(plan.relative_to(repo)),
                        "action": "execute",
                    },
                    {
                        "position": 2,
                        "id6": "agy002",
                        "setid": "demo",
                        "status": "queued",
                        "configured_file": str(plan.relative_to(repo)),
                        "action": "execute",
                    },
                ],
                "options": {
                    "model": "opus",
                    "self_finalize": True,
                    "isolate_worktree": False,
                },
            }
            agy_runipd.save_state(run_dir, state)

            dispatched = []

            def fake_execute(rd, st, it, *a, **kw):
                dispatched.append(it["id6"])
                raise agy_runipd.ToolIdentityError("tool-identity mismatch (synthetic)")

            with mock.patch.object(
                agy_runipd, "execute_item", side_effect=fake_execute
            ):
                with self.assertRaises(agy_runipd.ToolIdentityError):
                    agy_runipd.run_queue(run_dir, retry_incomplete=False)

            self.assertEqual(
                dispatched,
                ["agy001"],
                "ToolIdentityError must abort immediately without dispatching subsequent items",
            )


class AgyPerArtifactDispositionLineTests(unittest.TestCase):
    """runnoop Order 02 (`m85gxh`) E-03, the AGY HALF: the same block, from the same object.

    A CHILD MUST LAND IN BOTH RUNNERS OR IN NEITHER (the orchestrator's hard constraint), and a
    one-sided guard is how `render_stream` was extracted and then re-forked in the other driver with
    nothing noticing. So this host's block is proven by driving THIS driver's real `run_queue`, not by
    reading its source.
    """

    def _run_and_capture(self, repo: Path, queue: list) -> str:
        def _must_not_launch(*_a, **_k):
            raise AssertionError(
                "an agent turn was dispatched for an item that must never be dispatched"
            )

        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        state = {
            "run_id": "run-test",
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["wtiso"],
            "repo": str(repo),
            "queue": queue,
            "set_sessions": {},
            "session_id": None,
            "options": {"model": "opus", "isolate_worktree": False},
        }
        (run_dir / "state.json").write_text(
            json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
        )
        buf = io.StringIO()
        with (
            mock.patch.object(agy_runipd, "run_agy_turn", _must_not_launch),
            redirect_stdout(buf),
        ):
            agy_runipd.run_queue(run_dir, retry_incomplete=False)
        return buf.getvalue()

    def test_this_host_prints_one_explained_line_per_matched_artifact(self):
        from agent_workflows import run_selection_policy as pol

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            out = self._run_and_capture(
                repo,
                [
                    {
                        "position": 1,
                        "id6": "agy001",
                        "setid": "wtiso",
                        "action": "execute",
                        "status": "reviewed",
                        "attempts": [],
                        "needs_input": True,
                    },
                    {
                        "position": 2,
                        "id6": "agy002",
                        "setid": "wtiso",
                        "action": "execute",
                        "status": "executed",
                        "attempts": [],
                    },
                ],
            )
            self.assertIn(pol.DISPOSITION_HEADER, out)
            lines = [line for line in out.splitlines() if line.startswith("- 0")]
            self.assertEqual(len(lines), 2)
            self.assertIn("needs_human_approval", lines[0])
            self.assertIn("approval", lines[0])
            self.assertIn("ipd_already_executed", lines[1])

    def test_both_hosts_render_the_line_from_the_same_object(self):
        from agent_workflows import oc_runipd, run_selection_policy as pol

        self.assertIs(
            agy_runipd.render_queue_dispositions, pol.render_queue_dispositions
        )
        self.assertIs(
            agy_runipd.render_queue_dispositions, oc_runipd.render_queue_dispositions
        )


class AgyEndOfRunDispositionSummaryTests(AgyPerArtifactDispositionLineTests):
    def test_a_run_that_acted_on_ZERO_artifacts_still_prints_the_summary(self):
        from agent_workflows import run_selection_policy as pol

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            out = self._run_and_capture(
                repo,
                [
                    {
                        "position": i,
                        "id6": "agy%03d" % i,
                        "setid": "wtiso",
                        "action": "execute",
                        "status": "reviewed",
                        "attempts": [],
                        "needs_input": True,
                    }
                    for i in range(1, 9)
                ],
            )
            self.assertIn(pol.SUMMARY_HEADER, out)
            self.assertIn("NO WORK WAS PERFORMED", out)
            self.assertIn("matched 8 artifact(s) and acted on NONE", out)
            self.assertIn("needs_human_approval (8)", out)
            self.assertIn("aw ipd set approved <id6> --by-human", out)
            self.assertIn("total: 8 matched, 0 acted on, 8 not acted on", out)

    def test_this_hosts_footer_names_ANTIGRAVITY_and_shared_object(self):
        from agent_workflows import oc_runipd, run_selection_policy as pol

        self.assertIs(
            agy_runipd.render_disposition_summary, pol.render_disposition_summary
        )
        self.assertIs(
            agy_runipd.render_disposition_summary, oc_runipd.render_disposition_summary
        )
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "agy001")
            out = self._run_and_capture(
                repo,
                [
                    {
                        "position": 1,
                        "id6": "agy001",
                        "setid": "wtiso",
                        "action": "execute",
                        "status": "reviewed",
                        "attempts": [],
                        "needs_input": True,
                    }
                ],
            )
            self.assertIn("No turn was attempted", out)
            self.assertIn("no Antigravity session exists for this run", out)
            self.assertNotIn("no OpenCode session exists", out)
            self.assertIn("--- Antigravity Session Continuity ---", out)


class AgyVerdictMappingTests(unittest.TestCase):
    def test_this_host_binds_the_shared_mapping_and_holds_no_copy(self):
        from agent_workflows import oc_runipd, runner_shared as rs

        for name in (
            "map_verdict",
            "normalize_verdict",
            "verdict_refusal_text",
            "VerdictMapping",
        ):
            with self.subTest(symbol=name):
                self.assertIs(
                    getattr(agy_runipd, name),
                    getattr(rs, name),
                )
                self.assertIs(getattr(agy_runipd, name), getattr(oc_runipd, name))

    def test_verdict_integration_decisions(self):
        from agent_workflows import runner_shared as rs

        for raw in ("CORRECTION_REQUIRED", "BLOCKED", "", "garbage", "NOT BLOCKED"):
            with self.subTest(verdict=raw):
                mapped = rs.map_verdict(raw)
                self.assertNotEqual(mapped.verify_disp, "verified")
                verdict = agy_runipd.integration_is_earned(
                    validate=True,
                    verify_disp=mapped.verify_disp,
                    suite_result=None,
                )
                self.assertFalse(verdict.earned)
                self.assertEqual(
                    verdict.signal, rs.INTEGRATION_REFUSED_VERIFIER_DECLINED
                )

        verified = agy_runipd.integration_is_earned(
            validate=True,
            verify_disp=rs.map_verdict("VERIFIED").verify_disp,
            suite_result=None,
        )
        self.assertTrue(verified.earned)
        self.assertEqual(verified.signal, rs.INTEGRATION_EARNED_BY_VERIFIER)


class AgyVerificationAbsenceTests(unittest.TestCase):
    def test_plan_path_resolution(self):
        from agent_workflows import runner_shared as rs

        self.assertIs(agy_runipd.resolve_plan_path, rs.resolve_plan_path)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            executed = repo / ".aw" / "records" / "plans" / "executed"
            pending.mkdir(parents=True)
            executed.mkdir(parents=True)

            configured = (
                ".aw/records/plans/pending/20260908-testset-01-agy999-test-plan.ipd.md"
            )
            plan = repo / configured
            plan.write_text(
                "- Id: agy999\n- Set: testset\n- Status: approved\n# Test Plan\n",
                encoding="utf-8",
            )
            self.assertEqual(
                agy_runipd.resolve_plan_path(repo, configured, "agy999"), plan.resolve()
            )

            moved = executed / "20260908-testset-01-agy999-test-plan.ipd.md"
            plan.rename(moved)
            self.assertEqual(
                agy_runipd.resolve_plan_path(repo, configured, "agy999"),
                moved.resolve(),
            )

        with tempfile.TemporaryDirectory() as temp:
            lane = Path(temp) / "lane"
            (lane / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            with self.assertRaises(agy_runipd.DriverError) as caught:
                agy_runipd.resolve_plan_path(
                    lane,
                    ".aw/records/plans/pending/20260908-s-01-agy404-x.ipd.md",
                    "agy404",
                )
            self.assertIn("Cannot locate IPD agy404", str(caught.exception))

    def test_verification_absence_codes_and_reasons(self):
        codes = (
            agy_runipd.VERIFY_ABSENCE_VERDICT_UNREADABLE,
            agy_runipd.VERIFY_ABSENCE_NO_OUTCOME_FILE,
            agy_runipd.VERIFY_ABSENCE_TURN_INTERRUPTED,
            agy_runipd.VERIFY_ABSENCE_PLAN_UNRESOLVABLE,
        )
        self.assertEqual(len(set(codes)), 4)
        self.assertEqual(tuple(agy_runipd.VERIFY_ABSENCE_CODES), codes)
        reasons = {agy_runipd.verify_absence_text(code)[0] for code in codes}
        self.assertEqual(len(reasons), 4)

        never, _ = agy_runipd.verify_absence_text(
            agy_runipd.VERIFY_ABSENCE_NO_OUTCOME_FILE
        )
        killed, _ = agy_runipd.verify_absence_text(
            agy_runipd.VERIFY_ABSENCE_TURN_INTERRUPTED
        )
        self.assertIn("FAILURE", never)
        self.assertIn("UNKNOWN", killed)
        self.assertNotIn("FAILURE", killed)


class AgyCostAttributionTests(unittest.TestCase):
    def test_an_agy_run_freezes_the_snapshot_with_its_real_model(self):
        record = runner_shared.cost_attribution_record(
            host="agy",
            model=agy_runipd.DEFAULT_MODEL,
            model_source="host-default-constant",
            resolve_card=False,
        )
        self.assertEqual(record["host"], "agy")
        self.assertEqual(record["model"], agy_runipd.DEFAULT_MODEL or "")
        self.assertEqual(record["kind"], "launch-time-snapshot")
        self.assertEqual(record["unit"], "$/Mtok")

    def test_the_card_is_a_NAMED_inability_and_carries_NO_guessed_rate(self):
        record = runner_shared.cost_attribution_record(
            host="agy",
            model=agy_runipd.DEFAULT_MODEL,
            model_source="host-default-constant",
            resolve_card=False,
        )
        self.assertEqual(record["card"], {})
        self.assertEqual(record["card_reason"], "host-card-not-in-any-readable-config")
        self.assertEqual(record["card_config"], "")
        self.assertEqual(record["card_config_digest"], "")
        for value in record.values():
            self.assertNotIsInstance(value, float)


if __name__ == "__main__":
    unittest.main()

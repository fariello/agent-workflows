"""Tests for the `aw agy` / `aw antigravity` subcommand group.

The group forwards the raw argv tail verbatim to `agent_workflows.agy_runipd.main`, so `aw agy runipd`
(and its `antigravity` alias and `run`/`runagy` subcommands) has exact CLI parity with the standalone
runner - including the runner's own `--help` and its implicit-`start` shim.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, cli
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
                self.assertIn("status", combined)
                self.assertIn("report", combined)

    def test_forwarding_delegates_to_agy_runipd_main(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            rc = cli.main(["agy", "runipd", "status", "run-xyz"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with(["status", "run-xyz"])

    def test_antigravity_alias_delegates_identically(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            cli.main(["antigravity", "run", "resume", "run-xyz", "--retry-incomplete"])
        m.assert_called_once_with(["resume", "run-xyz", "--retry-incomplete"])

    def test_implicit_start_shim_preserved_through_wrapper(self):
        with mock.patch.object(agy_runipd, "main", return_value=0) as m:
            cli.main(["agy", "runipd", "somesetid", "--dry-run"])
        m.assert_called_once_with(["somesetid", "--dry-run"])

    def test_bare_agy_group_shows_family_help(self):
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
            self.assertEqual(item["status"], "blocked")
            self.assertIn("begin_refusal", item)

    def test_finalize_fires_on_verified_and_marks_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            state["options"]["no_verify"] = False

            (run_dir / "outcomes" / "01-agy001.json").write_text(
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-agy001-verification.json").write_text(
                json.dumps({"verdict": "CONFORMING"}), encoding="utf-8"
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
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-agy001-verification.json").write_text(
                json.dumps({"verdict": "CONFORMING"}), encoding="utf-8"
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

            self.assertEqual(item["status"], "substantially-complete")
            self.assertIn("finalize_refusal", item)
            self.assertTrue(plan.is_file(), "plan must not move on finalize refusal")


class AgyWorktreeIsolationTests(unittest.TestCase):
    """driverfin-02 (emus4n) parity for the agy driver: each execute child runs in its own worktree;
    the main tree stays clean during the turn; a verified child integrates back to main via the
    REUSED gate; a non-passing gate defers rather than faking executed."""

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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps({"disposition": "executed", "pushed": False}),
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
                        json.dumps({"verdict": "CONFORMING"}), encoding="utf-8"
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
                    json.dumps({"disposition": "executed", "pushed": False}),
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
                repo / ".aw" / "state" / "ipd-lifecycle" / "agy001.receipt.json",
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

            self.assertEqual(item["status"], "merge-conflict")
            self.assertIn("integration_deferral", item)
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertIn("preserved_branch", item)
            self.assertEqual(item["preserved_branch"], "aw/lane/agy001")


class AgyFailClosedIntegrationGuardTests(unittest.TestCase):
    """driverfin-03 (7kbtkw) parity for the agy driver: fail-closed dirty-tree guard (E-01) +
    merge-back conflict handling (E-02)."""

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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
                return 0, "vses", str(run_dir / "vlog"), ["agy"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps({"disposition": "executed", "pushed": False}),
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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
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
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["agy"]

        return fake_turn

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

            self.assertEqual(len(gate_calls), 0)
            self.assertEqual(item["status"], "integration-blocked")
            self.assertIn("integration_deferral", item)
            self.assertIn("src/demo.txt", item["integration_deferral"])
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
            self.assertIn("ipd-integration-blocked", events)

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

            self.assertEqual(item["status"], "merge-conflict")
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

    def test_the_integration_helpers_are_the_SHARED_ones(self):
        """integpath-02 (`6sb3yu`): this module no longer carries its own copies.

        The agy twin of the oc assertion, and it exists BECAUSE the one-sided version is a recorded
        failure here: `render_stream` was extracted with an oc-only guard and this module then
        re-forked four of its symbols with nothing noticing.
        """
        from agent_workflows import runner_shared

        self.assertIs(agy_runipd.dirty_tree_overlap, runner_shared.dirty_tree_overlap)
        src = Path(str(agy_runipd.__file__)).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for name in ("build_lane_outcome", "integrate_lane_branch"):
            node = next(
                n
                for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == name
            )
            statements = [
                s
                for s in node.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
            ]
            self.assertEqual(len(statements), 1, f"{name} must be a one-line wrapper")
            self.assertIn(f"runner_shared.{name}", ast.unparse(statements[0]))

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
                "## Workflow history\n- 2026-08-29 reviewed (aw set): reviewed\n",
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
    """revsweep 76gsmv E-01/V-01, agy half. It documented `all` while omitting `reviews` (F-2)."""

    def test_selector_types_block_documents_reviews(self):
        desc = agy_runipd.build_parser().description or ""
        self.assertIn("SELECTOR TYPES:", desc)
        self.assertIn("reviews:", desc)
        self.assertIn("all:", desc)

    def test_all_three_spellings_appear_in_the_help(self):
        help_text = agy_runipd.build_parser().format_help()
        for spelling in ("reviews", "review", "to-review"):
            self.assertIn(spelling, help_text)

    def test_the_bare_sweep_example_lives_in_the_description(self):
        """F-11: agy has NO `epilog`, so its example goes here rather than in an invented block."""
        parser = agy_runipd.build_parser()
        self.assertIsNone(parser.epilog, "agy gained an epilog; re-derive this test")
        self.assertRegex(parser.description or "", r"runagy reviews\b")

    def test_selectors_positional_help_names_the_sweep(self):
        import argparse as _ap

        parser = agy_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        sel = next(a for a in sub.choices["start"]._actions if a.dest == "selectors")
        self.assertIn("reviews", sel.help or "")

    def test_help_states_the_current_type_scoping_and_not_the_buggy_predicate(self):
        desc = agy_runipd.build_parser().description or ""
        self.assertIn("IPDs only", desc)
        self.assertIn("next legal action is review", desc)
        self.assertNotIn("status == to-review", desc)


class AgyReviewAliasTests(unittest.TestCase):
    """revsweep 76gsmv E-02/V-02, agy half: the alias must REACH the driver at all."""

    def test_review_reaches_the_driver_instead_of_invalid_choice(self):
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

    def test_explicit_selector_and_verbatim_tail_reach_the_driver(self):
        captured = {}

        def fake_main(argv, _c=captured):
            _c["argv"] = list(argv)
            return 0

        with mock.patch.object(agy_runipd, "main", fake_main):
            rc, _out, _err = _run_cli(
                ["agy", "review", "5ahblp", "--repo", "/tmp/x", "--session", "s1"]
            )
        self.assertEqual(rc, 0)
        self.assertEqual(
            captured["argv"],
            ["5ahblp", "--repo", "/tmp/x", "--session", "s1", "--action", "review"],
        )

    def test_the_two_hosts_share_one_expansion_function(self):
        """Spec 25kzda 2.1: an operator-visible difference between the spellings is a DEFECT.

        Proven structurally rather than by comparing outputs: both hosts route through the SAME
        function, so there is no second implementation that could drift.
        """
        for tail in ([], ["5ahblp"], ["--repo", "/tmp/x"]):
            with self.subTest(tail=tail):
                self.assertEqual(
                    cli.expand_host_review_argv(tail),
                    cli.expand_host_review_argv(list(tail)),
                )


class AgyActionLegalityTests(unittest.TestCase):
    """revsweep 76gsmv E-03/V-03, agy half.

    MORE URGENT ON THIS HOST than on oc: `--full-auto` DEFAULTS TO TRUE here (`initialize_run` reads
    `getattr(args, "full_auto", True)`), so a merely-accepted `--action review` would let
    `aw agy review <reviewed-id6>` auto-clear that plan to `auto-approved` and execute it.
    """

    def test_action_vocabulary_matches_the_oc_host(self):
        from agent_workflows import oc_runipd

        self.assertEqual(agy_runipd.ACTION_CHOICES, oc_runipd.ACTION_CHOICES)
        self.assertEqual(agy_runipd.ACTION_IMPLEMENTED, oc_runipd.ACTION_IMPLEMENTED)

    def test_review_passes_a_to_review_item(self):
        agy_runipd.enforce_requested_action("review", [("a", "to-review", "review")])

    def test_review_refuses_approved_and_reviewed_items(self):
        for status in ("approved", "reviewed", "auto-approved"):
            with self.subTest(status=status):
                with self.assertRaises(agy_runipd.DriverError) as ctx:
                    agy_runipd.enforce_requested_action(
                        "review", [("a", status, "execute")]
                    )
                self.assertIn("illegal", str(ctx.exception))

    def test_plan_and_execute_refuse_honestly(self):
        for action in ("plan", "execute"):
            with self.subTest(action=action):
                with self.assertRaises(agy_runipd.DriverError) as ctx:
                    agy_runipd.enforce_requested_action(
                        action, [("a", "to-review", "review")]
                    )
                self.assertIn("not implemented", str(ctx.exception))

    def test_none_is_a_no_op(self):
        agy_runipd.enforce_requested_action(None, [("a", "approved", "execute")])

    def test_the_action_flag_is_registered_on_start(self):
        import argparse as _ap

        parser = agy_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        action_arg = next(
            a for a in sub.choices["start"]._actions if a.dest == "action"
        )
        self.assertEqual(tuple(action_arg.choices or ()), agy_runipd.ACTION_CHOICES)
        self.assertIsNone(action_arg.default)


class AgyEmptyReviewSweepTests(unittest.TestCase):
    """revsweep 76gsmv E-04/V-04, agy half: spec 25kzda 2.4a property 3."""

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

    def test_empty_sweep_raises_the_success_subclass(self):
        for spelling in ("reviews", "review", "to-review"):
            with self.subTest(spelling=spelling):
                with self.assertRaises(agy_runipd.EmptyStatusSelection):
                    agy_runipd.expand_selectors(self._MANIFEST, [spelling])

    def test_the_success_subclass_is_still_a_driver_error(self):
        self.assertTrue(
            issubclass(agy_runipd.EmptyStatusSelection, agy_runipd.DriverError)
        )

    def test_all_selector_zero_match_is_untouched(self):
        manifest = {
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
            agy_runipd.expand_selectors(manifest, ["all"])
        self.assertNotIsInstance(ctx.exception, agy_runipd.EmptyStatusSelection)

    def test_main_exits_zero_on_an_empty_sweep_and_creates_no_run_state(self):
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

    def test_main_still_exits_two_for_a_misspelled_id6(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = agy_runipd.main(["zzzz99", "--repo", str(repo), "--prepare-only"])
            self.assertEqual(rc, 2, out.getvalue() + err.getvalue())


class AgyVerbosityFlagTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-06/V-06: `-v` parses IDENTICALLY to the oc driver.

    The property under test is PARITY, so every case here mirrors
    `tests/test_oc_runipd_cli.py::VerbosityFlagTests`. A leading `-v` used to be swallowed by the
    implicit-start `subcommands` set in this driver too; both drivers' sets were changed together
    because `tests/test_runner_stop_triggers.py` regexes both source files.
    """

    def _parse(self, argv):
        return agy_runipd.build_parser().parse_args(argv)

    def test_start_parses_every_spelling_in_both_positions(self):
        for argv, expected in (
            (["start", "sel"], 0),
            (["start", "sel", "-v"], 1),
            (["start", "sel", "-vv"], 2),
            (["start", "sel", "--verbose"], 1),
            (["start", "sel", "--verbose", "--verbose"], 2),
            (["start", "-v", "sel"], 1),
            (["start", "-vv", "sel"], 2),
            (["start", "--verbose", "sel"], 1),
        ):
            with self.subTest(argv=argv):
                args = self._parse(argv)
                self.assertEqual(args.verbosity, expected)
                self.assertEqual(args.selectors, ["sel"])

    def test_resume_parses_every_spelling_and_defaults_to_none(self):
        self.assertIsNone(self._parse(["resume", "run-x"]).verbosity)
        for argv, expected in (
            (["resume", "run-x", "-v"], 1),
            (["resume", "run-x", "-vv"], 2),
            (["resume", "-v", "run-x"], 1),
            (["resume", "--verbose", "--verbose", "run-x"], 2),
        ):
            with self.subTest(argv=argv):
                self.assertEqual(self._parse(argv).verbosity, expected)

    def test_the_two_drivers_parse_the_flag_identically(self):
        from agent_workflows import oc_runipd

        for argv in (
            ["start", "sel", "-v"],
            ["start", "-vv", "sel"],
            ["start", "sel", "--verbose"],
        ):
            with self.subTest(argv=argv):
                self.assertEqual(
                    agy_runipd.build_parser().parse_args(argv).verbosity,
                    oc_runipd.build_parser().parse_args(argv).verbosity,
                )

    def test_the_flags_are_forwarded_verbatim_through_the_aw_wrapper(self):
        for argv in (["-v", "somesetid"], ["somesetid", "-vv"]):
            with self.subTest(argv=argv):
                with mock.patch.object(agy_runipd, "main", return_value=0) as m:
                    cli.main(["agy", "run", *argv])
                m.assert_called_once_with(argv)

    def test_the_flag_appears_in_help_for_start_and_resume(self):
        import argparse as _ap

        parser = agy_runipd.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        for cmd in ("start", "resume"):
            with self.subTest(cmd=cmd):
                text = sub.choices[cmd].format_help()
                self.assertIn("--verbose", text)

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

    def test_render_agy_event_suppresses_system_protocol_placeholder(self):
        pal = agy_runipd.Palette(False)
        placeholder = "[System: Empty message content sanitised to satisfy protocol]"
        self.assertIsNone(agy_runipd.render_agy_event(placeholder, pal))

        unparseable = "unparseable raw line"
        res = agy_runipd.render_agy_event(unparseable, pal)
        self.assertIsNotNone(res)
        self.assertIn(unparseable, res)


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

    def test_this_module_no_longer_defines_a_dependency_status_detailed(self):
        """Assertion by SOURCE, so a copy shadowed by a later import cannot hide behind identity."""
        import ast

        src = Path(str(agy_runipd.__file__)).read_text(encoding="utf-8")
        defined = [
            node.name
            for node in ast.parse(src).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.assertNotIn("dependency_status_detailed", defined)
        self.assertNotIn("dependency_status", defined)

    def test_the_drain_path_resolves_a_TYPED_edge(self):
        """The copy reported `no plan resolves to this id6 in the repo` for a valid typed edge."""
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

    def test_the_drain_path_routes_an_orchestrate_item_through_the_shared_decider(self):
        """The copy had NO `orchestrate` clause, so an orchestrator bypassed the shared decision."""
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
            self.assertFalse(ok, "an orchestrator with an unfinished child must WAIT")
            self.assertEqual(missing, ["executed:child1"])
            self.assertIn(
                "orchestrator waits for child child1",
                reasons["executed:child1"],
                "only the orchestrator clause can produce a child-named reason",
            )

    def test_a_review_edge_is_satisfied_by_a_reviewed_external_target_on_this_host(
        self,
    ):
        """The headline fix, asserted on THIS host: readiness is the FIELD, not the directory."""
        for status, expected in (
            ("reviewed", True),
            ("approved", True),
            ("to-review", False),
        ):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket="pending", status=status)
                    item = self._item("review")
                    state = {"repo": str(repo), "queue": [item]}
                    for entry in ("dependency_status", "dependency_status_detailed"):
                        got = getattr(agy_runipd, entry)(item, state)
                        self.assertEqual(got[0], expected, f"{entry} disagreed")

    def test_an_execute_edge_is_NOT_relaxed_on_this_host(self):
        """The asymmetry, on this host too: an execute turn consumes WORK, so it needs `executed/`."""
        for status in ("reviewed", "approved"):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket="pending", status=status)
                    item = self._item("execute")
                    state = {"repo": str(repo), "queue": [item]}
                    ok, missing, _reasons = agy_runipd.dependency_status_detailed(
                        item, state
                    )
                    self.assertFalse(ok)
                    self.assertEqual(missing, ["executed:depaaa"])

    def test_a_terminal_directory_still_decides_on_this_host(self):
        """The anti-regression half: an `executed/` plan with an unreadable field still satisfies."""
        for status in ("EXECUTED (approved by maintainer)", "to-review"):
            for action in ("review", "execute"):
                with self.subTest(status=status, action=action):
                    with tempfile.TemporaryDirectory() as t:
                        repo = self._repo(Path(t), bucket="executed", status=status)
                        item = self._item(action)
                        state = {"repo": str(repo), "queue": [item]}
                        ok, _m, reasons = agy_runipd.dependency_status_detailed(
                            item, state
                        )
                        self.assertTrue(ok, f"reasons={reasons!r}")

    def test_the_retained_findings_wrapper_is_uncalled_but_present(self):
        """`_findings_block_reason`'s two call sites were BOTH inside the deleted copy.

        It is kept because `tests/test_review_findings_cascade.py::SharedPredicateTests` requires this
        module to expose it and to name `subject_gating_blocks`; the live gate now runs in `oc_runipd`
        through the shared implementation. Pinned so a future reader does not mistake it for a second
        implementation, and so deleting it is a deliberate act rather than an accident.
        """
        import ast

        src = Path(str(agy_runipd.__file__)).read_text(encoding="utf-8")
        calls = [
            node
            for node in ast.walk(ast.parse(src))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_findings_block_reason"
        ]
        self.assertEqual(
            calls, [], "the wrapper must have no call sites in this module"
        )
        self.assertTrue(hasattr(agy_runipd, "_findings_block_reason"))
        self.assertIn("subject_gating_blocks", src)


if __name__ == "__main__":
    unittest.main()

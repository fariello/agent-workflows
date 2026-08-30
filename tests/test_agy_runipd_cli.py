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
            self.assertTrue(ipd_lifecycle.receipt_path_for(repo, "agy001").is_file())

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


if __name__ == "__main__":
    unittest.main()

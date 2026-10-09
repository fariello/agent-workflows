from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    ipd_lifecycle,
    oc_runipd,
    render_stream,
    runner_shared,
    runner_stop,
)
from tests import support
from tests.test_oc_runipd import _init_repo_with_conforming_plan


def _git_head(repo: Path) -> str:
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_clean_repo(repo: Path) -> Path:
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
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _mk_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run_dir"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "events.jsonl").touch()
    return run_dir


class InterruptReconcileNoWorktreeUnitTests(unittest.TestCase):
    """Direct unit tests for reconcile_item_on_interrupt with work_dir=None against real repos."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_no_worktree_dirty_repo_preserves_work(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo = _init_clean_repo(tmp / "repo")
            (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(repo), "queue": []}
            attempt = {"number": 1, "starting_head": _git_head(repo)}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "clean-up-and-terminate",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "interrupted")
            self.assertTrue(item.get("recovery_next"))
            self.assertEqual(attempt.get("interrupt_reason"), "clean-up-and-terminate")
            self.assertEqual(
                item.get("stopped", {}).get("certainty"), runner_stop.CERTAINTY_KNOWN
            )
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "work-preserved")
            self.assertGreaterEqual(len(calls), 1)

    def test_no_worktree_clean_repo_cleans_up(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo = _init_clean_repo(tmp / "repo")
            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(repo), "queue": []}
            head = _git_head(repo)
            attempt = {"number": 1, "starting_head": head}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}
            rcpt = ipd_lifecycle.receipt_path_for(repo, "rec001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("dummy receipt\n", encoding="utf-8")
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "clean-up-and-terminate",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "queued")
            self.assertIsNone(item.get("recovery_next"))
            self.assertEqual(item["attempts"], [])
            self.assertFalse(rcpt.exists())
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            cleaned_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(cleaned_events), 1)
            self.assertGreaterEqual(len(calls), 1)

    def test_no_worktree_just_terminate_no_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo = _init_clean_repo(tmp / "repo")
            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(repo), "queue": []}
            attempt = {"number": 1, "starting_head": _git_head(repo)}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "just-terminate-no-cleanup",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "interrupted")
            self.assertTrue(item.get("recovery_next"))
            self.assertEqual(
                attempt.get("interrupt_reason"), "just-terminate-no-cleanup"
            )
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "no-cleanup")
            self.assertGreaterEqual(len(calls), 1)

    def test_no_worktree_not_a_repo_preserves_work(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            not_a_repo = tmp / "not_a_repo"
            not_a_repo.mkdir(parents=True, exist_ok=True)
            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(not_a_repo), "queue": []}
            attempt = {"number": 1}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                not_a_repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "clean-up-and-terminate",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "interrupted")
            self.assertTrue(item.get("recovery_next"))
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "work-preserved")
            self.assertGreaterEqual(len(calls), 1)

    def test_no_worktree_committed_work_preserves_work(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo = _init_clean_repo(tmp / "repo")
            starting_head = _git_head(repo)
            attempt = {"number": 1, "starting_head": starting_head}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}

            (repo / "new_file.txt").write_text("committed work\n", encoding="utf-8")
            subprocess.run(["git", "add", "new_file.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "committed work"], cwd=repo, check=True
            )

            rcpt = ipd_lifecycle.receipt_path_for(repo, "rec001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("dummy receipt\n", encoding="utf-8")

            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(repo), "queue": []}
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "clean-up-and-terminate",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "interrupted")
            self.assertTrue(item.get("recovery_next"))
            self.assertTrue(rcpt.is_file())
            self.assertIn(attempt, item["attempts"])
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "work-preserved")
            self.assertGreaterEqual(len(calls), 1)

    def test_no_worktree_moved_head_without_starting_head_cleans_up(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            repo = _init_clean_repo(tmp / "repo")

            (repo / "new_file.txt").write_text("committed work\n", encoding="utf-8")
            subprocess.run(["git", "add", "new_file.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "committed work"], cwd=repo, check=True
            )

            attempt = {"number": 1}
            item = {"id6": "rec001", "status": "running", "attempts": [attempt]}

            rcpt = ipd_lifecycle.receipt_path_for(repo, "rec001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("dummy receipt\n", encoding="utf-8")

            run_dir = _mk_run_dir(tmp)
            state = {"repo": str(repo), "queue": []}
            calls: list[dict] = []

            runner_shared.reconcile_item_on_interrupt(
                repo,
                run_dir,
                state,
                item,
                attempt,
                1,
                None,
                "clean-up-and-terminate",
                save_state_fn=lambda rd, st: calls.append(st),
            )

            self.assertEqual(item["status"], "queued")
            self.assertEqual(item["attempts"], [])
            self.assertFalse(rcpt.exists())
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            cleaned_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "rec001"
            ]
            self.assertEqual(len(cleaned_events), 1)
            self.assertGreaterEqual(len(calls), 1)


class HostBehavioralInterruptTests(unittest.TestCase):
    """Behavioral tests driving real oc_runipd and agy_runipd execute_item with KeyboardInterrupt."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _state_and_item(
        self, repo: Path, plan: Path, driver_name: str
    ) -> tuple[dict, dict]:
        id6 = "wir001" if driver_name == "oc" else "agy001"
        item = {
            "position": 1,
            "id6": id6,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        options = {
            "model": "opus",
            "self_finalize": True,
            "isolate_worktree": False,
        }
        if driver_name == "oc":
            options["opencode"] = "/bin/true"
            options["no_audit"] = True
        else:
            options["no_verify"] = True

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "host_capabilities": {
                "host": "opencode" if driver_name == "oc" else "antigravity",
                "observed_at": "2026-08-28T00:00:00+00:00",
                "descriptor": {
                    "supports_fresh_verifier_session": True,
                },
            },
            "options": options,
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        return run_dir

    def test_oc_execute_item_keyboard_interrupt_clean_up_and_terminate(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "oc")

            def fake_run(*args, **kwargs):
                (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
                raise KeyboardInterrupt("clean-up-and-terminate")

            with (
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(oc_runipd, "run_opencode", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "interrupted")
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_state["queue"][0]["status"], "interrupted")
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "work-preserved")
            self.assertEqual(
                render_stream._interrupt_reason_of(item), "clean-up-and-terminate"
            )

    def test_oc_execute_item_keyboard_interrupt_just_terminate_no_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "oc")

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt("just-terminate-no-cleanup")

            with (
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(oc_runipd, "run_opencode", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "interrupted")
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_state["queue"][0]["status"], "interrupted")
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "no-cleanup")
            self.assertEqual(
                render_stream._interrupt_reason_of(item), "just-terminate-no-cleanup"
            )

    def test_agy_execute_item_keyboard_interrupt_clean_up_and_terminate(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "agy")

            def fake_run(*args, **kwargs):
                (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
                raise KeyboardInterrupt("clean-up-and-terminate")

            with (
                mock.patch.object(agy_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(agy_runipd, "run_agy_turn", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "interrupted")
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_state["queue"][0]["status"], "interrupted")
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "agy001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "work-preserved")
            self.assertEqual(
                render_stream._interrupt_reason_of(item), "clean-up-and-terminate"
            )

    def test_agy_execute_item_keyboard_interrupt_just_terminate_no_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "agy")

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt("just-terminate-no-cleanup")

            with (
                mock.patch.object(agy_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(agy_runipd, "run_agy_turn", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "interrupted")
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_state["queue"][0]["status"], "interrupted")
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "agy001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(interrupted_events[0].get("subevent"), "no-cleanup")
            self.assertEqual(
                render_stream._interrupt_reason_of(item), "just-terminate-no-cleanup"
            )


class TerminalRungInterruptBehavioralTests(unittest.TestCase):
    """Behavioral tests driving real oc_runipd and agy_runipd execute_item with the terminal rung."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _state_and_item(
        self, repo: Path, plan: Path, driver_name: str
    ) -> tuple[dict, dict]:
        id6 = "wir001" if driver_name == "oc" else "agy001"
        item = {
            "position": 1,
            "id6": id6,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        options = {
            "model": "opus",
            "self_finalize": True,
            "isolate_worktree": False,
        }
        if driver_name == "oc":
            options["opencode"] = "/bin/true"
            options["no_audit"] = True
        else:
            options["no_verify"] = True

        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "host_capabilities": {
                "host": "opencode" if driver_name == "oc" else "antigravity",
                "observed_at": "2026-08-28T00:00:00+00:00",
                "descriptor": {
                    "supports_fresh_verifier_session": True,
                },
            },
            "options": options,
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "events.jsonl").touch()
        return run_dir

    def _capture_terminal_message(
        self, run_dir: Path, requester: str = "signal pid=12345"
    ) -> str:
        """Capture the real KeyboardInterrupt message produced by install_stop_triggers._terminal."""
        captured_cb = None

        def fake_install(rd, *, command, requester, on_terminal):
            nonlocal captured_cb
            captured_cb = on_terminal
            return {}

        with mock.patch.object(
            runner_stop, "install_stop_signal_handlers", fake_install
        ):
            runner_shared.install_stop_triggers(
                run_dir,
                labels=runner_shared.OC_HOST_LABELS,
            )
        self.assertIsNotNone(
            captured_cb, "install_stop_triggers did not register on_terminal callback"
        )
        ladder = runner_stop.SIGINT_LADDER
        terminal_level = ladder[-1]
        try:
            captured_cb(terminal_level, requester)
        except KeyboardInterrupt as exc:
            return str(exc)
        self.fail("captured _terminal callback did not raise KeyboardInterrupt")

    def _capture_sigterm_fallback_message(self) -> str:
        """Capture the message produced by render_stream.install_exit_signal_handler default handler."""
        captured_handler = None

        def fake_signal(sig, handler):
            nonlocal captured_handler
            captured_handler = handler
            return None

        with mock.patch("signal.signal", fake_signal):
            render_stream.install_exit_signal_handler()
        self.assertIsNotNone(
            captured_handler,
            "install_exit_signal_handler did not register signal handler",
        )
        try:
            captured_handler(15, None)
        except KeyboardInterrupt as exc:
            return str(exc)
        self.fail("captured SIGTERM fallback handler did not raise KeyboardInterrupt")

    def test_terminal_rung_message_contains_sentinel_routing_pin(self):
        """Pin the routing contract: _terminal message must contain FORCED_INTERRUPT_SENTINEL (E-01/E-03)."""
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run_dir"
            run_dir.mkdir(parents=True, exist_ok=True)
            msg = self._capture_terminal_message(run_dir, requester="signal pid=42424")
            self.assertIn("stop level 4 (now-force)", msg)
            self.assertIn("requested by signal pid=42424", msg)
            self.assertIn(
                runner_shared.FORCED_INTERRUPT_SENTINEL,
                msg,
                "The message _terminal raises must carry FORCED_INTERRUPT_SENTINEL to route to preserve arm",
            )

    def test_oc_execute_item_terminal_rung_clean_tree_preserves_and_refuses_requeue(
        self,
    ):
        """End-to-end oc execute_item on clean tree with real _terminal message (E-03)."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            rcpt = ipd_lifecycle.receipt_path_for(repo, "wir001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("receipt data\n", encoding="utf-8")

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "oc")
            terminal_msg = self._capture_terminal_message(run_dir)

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt(terminal_msg)

            with (
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(oc_runipd, "run_opencode", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # Item must be recorded interrupted
            self.assertEqual(item["status"], "interrupted")
            self.assertNotIn(item["status"], runner_shared.SUCCESS_STATES)
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            saved_item = saved_state["queue"][0]
            self.assertEqual(saved_item["status"], "interrupted")

            # Begin receipt and attempt must NOT be removed
            self.assertTrue(
                rcpt.is_file(), "Begin receipt was unlinked on force interrupt"
            )
            self.assertEqual(
                len(item.get("attempts", [])),
                1,
                "Attempt was popped on force interrupt",
            )

            # Events verification
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(
                interrupted_events[0].get("subevent"),
                runner_shared.FORCED_INTERRUPT_SENTINEL,
            )
            cleanup_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "wir001"
            ]
            self.assertEqual(
                len(cleanup_events),
                0,
                "Clean tree force interrupt emitted ipd-cleaned-up-no-changes",
            )

            # Mandatory check: indeterminate stopped record
            self.assertTrue(
                runner_stop.is_indeterminate(saved_item),
                "item['stopped']['certainty'] must be CERTAINTY_INDETERMINATE",
            )

            # Mandatory check: requeue_interrupted REFUSES to re-queue
            requeued = runner_shared.requeue_interrupted(run_dir, saved_state)
            self.assertNotIn("wir001", requeued)
            self.assertEqual(saved_item["status"], "interrupted")
            self.assertTrue(saved_item.get("requires_reconciliation"))

            # Operator diagnostics line readability
            reason = render_stream._interrupt_reason_of(saved_item)
            self.assertEqual(reason, runner_shared.FORCED_INTERRUPT_SENTINEL)

    def test_agy_execute_item_terminal_rung_clean_tree_preserves_and_refuses_requeue(
        self,
    ):
        """End-to-end agy execute_item on clean tree with real _terminal message (E-03)."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            rcpt = ipd_lifecycle.receipt_path_for(repo, "agy001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("receipt data\n", encoding="utf-8")

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "agy")
            terminal_msg = self._capture_terminal_message(run_dir)

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt(terminal_msg)

            with (
                mock.patch.object(agy_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(agy_runipd, "run_agy_turn", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "interrupted")
            self.assertNotIn(item["status"], runner_shared.SUCCESS_STATES)
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            saved_item = saved_state["queue"][0]
            self.assertEqual(saved_item["status"], "interrupted")
            self.assertTrue(rcpt.is_file())
            self.assertEqual(len(item.get("attempts", [])), 1)

            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "agy001"
            ]
            self.assertEqual(len(interrupted_events), 1)
            self.assertEqual(
                interrupted_events[0].get("subevent"),
                runner_shared.FORCED_INTERRUPT_SENTINEL,
            )
            cleanup_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "agy001"
            ]
            self.assertEqual(len(cleanup_events), 0)

            self.assertTrue(runner_stop.is_indeterminate(saved_item))
            requeued = runner_shared.requeue_interrupted(run_dir, saved_state)
            self.assertNotIn("agy001", requeued)
            self.assertEqual(saved_item["status"], "interrupted")
            self.assertTrue(saved_item.get("requires_reconciliation"))

    def test_sigterm_fallback_raiser_pinned_behavior(self):
        """Cover the SIGTERM fallback raiser (F-10) with its measured behavior.

        As documented in E-01/V-01, render_stream.install_exit_signal_handler's fallback raiser
        is excluded from modification in this plan to preserve Scope-Paths boundaries
        (agent_workflows/runner_shared.py, tests/test_interrupt_reconcile.py) and prevent
        import cycles. In standard runs, install_stop_triggers replaces this fallback on the
        main thread by recording level 3 and returning cleanly (spec R13).
        This test pins the fallback's message and its clean-tree routing through oc_execute_item.
        """
        sigterm_msg = self._capture_sigterm_fallback_message()
        self.assertEqual(sigterm_msg, "Terminated by SIGTERM")
        self.assertNotIn(runner_shared.FORCED_INTERRUPT_SENTINEL, sigterm_msg)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            rcpt = ipd_lifecycle.receipt_path_for(repo, "wir001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("dummy receipt\n", encoding="utf-8")

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "oc")

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt(sigterm_msg)

            with (
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(oc_runipd, "run_opencode", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # Unsentinelled SIGTERM fallback routes to cleanup on clean tree
            self.assertEqual(item["status"], "queued")
            self.assertEqual(len(item.get("attempts", [])), 0)
            self.assertFalse(rcpt.exists())
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            cleaned_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(cleaned_events), 1)

    def test_interactive_menu_cleanup_action_unaffected(self):
        """E-04: Pin that the interactive menu's deliberate cleanup action remains destructive.

        runner_stop.INTERRUPT_ACTION_CLEANUP raises KeyboardInterrupt('clean-up-and-terminate')
        without FORCED_INTERRUPT_SENTINEL. On a clean tree, this must reach the no-changes cleanup
        arm (item queued, attempt popped, receipt unlinked, ipd-cleaned-up-no-changes emitted).
        The asymmetry with unrequested force stop is deliberate operator consent (F-7).
        """
        menu_msg = "clean-up-and-terminate"
        self.assertNotIn(
            runner_shared.FORCED_INTERRUPT_SENTINEL,
            menu_msg,
            "Interactive menu cleanup message must NOT carry the unrequested force stop sentinel",
        )

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            rcpt = ipd_lifecycle.receipt_path_for(repo, "wir001")
            rcpt.parent.mkdir(parents=True, exist_ok=True)
            rcpt.write_text("receipt data\n", encoding="utf-8")

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, "oc")

            def fake_run(*args, **kwargs):
                raise KeyboardInterrupt(menu_msg)

            with (
                mock.patch.object(oc_runipd, "driver_begin", return_value=(0, "ok")),
                mock.patch.object(oc_runipd, "run_opencode", fake_run),
            ):
                with pytest.raises(KeyboardInterrupt):
                    oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "queued")
            self.assertEqual(item.get("attempts", []), [])
            self.assertFalse(
                rcpt.exists(), "Deliberate cleanup must unlink begin receipt"
            )
            saved_state = json.loads(
                (run_dir / "state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_state["queue"][0]["status"], "queued")

            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            cleaned_events = [
                e
                for e in events
                if e.get("event") == "ipd-cleaned-up-no-changes"
                and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(cleaned_events), 1)
            interrupted_events = [
                e
                for e in events
                if e.get("event") == "ipd-interrupted" and e.get("id6") == "wir001"
            ]
            self.assertEqual(len(interrupted_events), 0)

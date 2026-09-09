#!/usr/bin/env python3
"""Tests for the interactive interrupt (Ctrl-C) menu in oc_runipd and agy_runipd.

Covers:
1. Clean up and terminate (with and without changed files).
2. Just terminate with no clean up.
3. Resume.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest import mock
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared, runner_stop


class InterruptMenuPromptTests(unittest.TestCase):
    def test_prompt_choice_1_resume(self):
        stdin = io.StringIO("1\n")
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_RESUME)
        output = stderr.getvalue()
        self.assertIn("1. Resume?", output)
        self.assertIn("2. Finish current item, clean up, and exit?", output)
        self.assertIn("3. Clean up and exit?", output)
        self.assertIn("4. Exit, leaving a mess?", output)

    def test_prompt_choice_2_finish_current(self):
        stdin = io.StringIO("2\n")
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_FINISH_CURRENT)

    def test_prompt_choice_3_cleanup(self):
        stdin = io.StringIO("3\n")
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_CLEANUP)

    def test_prompt_choice_4_terminate_no_cleanup(self):
        stdin = io.StringIO("4\n")
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_TERMINATE_NO_CLEANUP)

    def test_prompt_invalid_input_retries(self):
        stdin = io.StringIO("invalid\n3\n")
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_CLEANUP)
        self.assertIn("Please enter 1, 2, 3, or 4:", stderr.getvalue())

    def test_prompt_eof_defaults_to_cleanup(self):
        stdin = io.StringIO("")  # immediate EOF
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_CLEANUP)
        self.assertIn("EOF received", stderr.getvalue())

    def test_prompt_keyboard_interrupt_defaults_to_cleanup(self):
        stdin = mock.MagicMock()
        stdin.readline.side_effect = KeyboardInterrupt
        stderr = io.StringIO()
        choice = runner_stop.prompt_interrupt_action(stdin=stdin, stream=stderr)
        self.assertEqual(choice, runner_stop.INTERRUPT_ACTION_CLEANUP)
        self.assertIn("Repeated Ctrl-C", stderr.getvalue())


class HandleInteractiveInterruptTests(unittest.TestCase):
    @mock.patch("agent_workflows.runner_stop.prompt_interrupt_action")
    @mock.patch("agent_workflows.runner_stop.pause_live_children")
    @mock.patch("agent_workflows.runner_stop.resume_live_children")
    @mock.patch("agent_workflows.render_stream.pause_active_statusline")
    @mock.patch("agent_workflows.render_stream.resume_active_statusline")
    @mock.patch("agent_workflows.runner_shutdown.clean_shutdown")
    def test_resume_action_resumes_children_and_statusline(
        self,
        mock_shutdown,
        mock_res_sl,
        mock_pause_sl,
        mock_res_ch,
        mock_pause_ch,
        mock_prompt,
    ):
        mock_proc = mock.MagicMock()
        mock_pause_ch.return_value = [mock_proc]
        mock_prompt.return_value = runner_stop.INTERRUPT_ACTION_RESUME

        stderr = io.StringIO()
        action = runner_stop.handle_interactive_interrupt(
            run_dir=Path("/tmp/fake-run"),
            requester="test",
            stream=stderr,
        )
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_RESUME)
        mock_pause_ch.assert_called_once()
        mock_pause_sl.assert_called_once()
        mock_res_ch.assert_called_once_with([mock_proc])
        mock_res_sl.assert_called_once()
        mock_shutdown.assert_not_called()
        self.assertIn("Resuming...", stderr.getvalue())

    @mock.patch("agent_workflows.runner_stop.prompt_interrupt_action")
    @mock.patch("agent_workflows.runner_stop.pause_live_children")
    @mock.patch("agent_workflows.runner_stop.resume_live_children")
    @mock.patch("agent_workflows.render_stream.pause_active_statusline")
    @mock.patch("agent_workflows.render_stream.resume_active_statusline")
    @mock.patch("agent_workflows.runner_shutdown.clean_shutdown")
    def test_finish_current_action_resumes_children_and_statusline(
        self,
        mock_shutdown,
        mock_res_sl,
        mock_pause_sl,
        mock_res_ch,
        mock_pause_ch,
        mock_prompt,
    ):
        mock_proc = mock.MagicMock()
        mock_pause_ch.return_value = [mock_proc]
        mock_prompt.return_value = runner_stop.INTERRUPT_ACTION_FINISH_CURRENT

        stderr = io.StringIO()
        action = runner_stop.handle_interactive_interrupt(
            run_dir=Path("/tmp/fake-run"),
            requester="test",
            stream=stderr,
        )
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_FINISH_CURRENT)
        mock_pause_ch.assert_called_once()
        mock_pause_sl.assert_called_once()
        mock_res_ch.assert_called_once_with([mock_proc])
        mock_res_sl.assert_called_once()
        mock_shutdown.assert_not_called()
        self.assertIn("Finishing current item before stopping...", stderr.getvalue())

    @mock.patch("agent_workflows.runner_stop.prompt_interrupt_action")
    @mock.patch("agent_workflows.runner_stop.pause_live_children")
    @mock.patch("agent_workflows.runner_stop.resume_live_children")
    @mock.patch("agent_workflows.render_stream.pause_active_statusline")
    @mock.patch("agent_workflows.render_stream.resume_active_statusline")
    @mock.patch("agent_workflows.runner_shutdown.clean_shutdown")
    def test_cleanup_action_terminates_children(
        self,
        mock_shutdown,
        mock_res_sl,
        mock_pause_sl,
        mock_res_ch,
        mock_pause_ch,
        mock_prompt,
    ):
        mock_proc = mock.MagicMock()
        mock_pause_ch.return_value = [mock_proc]
        mock_prompt.return_value = runner_stop.INTERRUPT_ACTION_CLEANUP

        stderr = io.StringIO()
        action = runner_stop.handle_interactive_interrupt(
            run_dir=Path("/tmp/fake-run"),
            requester="test",
            stream=stderr,
        )
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_CLEANUP)
        mock_res_ch.assert_called_once_with([mock_proc])
        mock_shutdown.assert_called_once_with(mock_proc, run_dir=Path("/tmp/fake-run"))


class ReconcileItemOnInterruptTests(unittest.TestCase):
    def setUp(self):
        self.saved_states = []

    def save_state(self, run_dir, state):
        self.saved_states.append((run_dir, dict(state)))

    @mock.patch("agent_workflows.worktree_lease.teardown_worktree")
    @mock.patch("agent_workflows.runner_shared.describe_lane")
    def test_cleanup_when_no_files_changed_resets_to_queued(
        self, mock_desc, mock_teardown
    ):
        # Lane exists, but holds_work is False
        mock_desc.return_value = {
            "lane_id": "test01",
            "worktree": "/tmp/worktree/test01",
            "branch": "aw/lane/test01",
            "base_sha": "abc1234",
            "holds_work": False,
            "dirty": False,
        }

        item = {
            "id6": "test01",
            "status": "executing",
            "attempts": [
                {
                    "attempt": 1,
                    "worktree": "/tmp/worktree/test01",
                    "worktree_lane_id": "test01",
                }
            ],
        }
        state = {"queue": [item]}
        run_dir = Path("/tmp/run-dir")

        with mock.patch("agent_workflows.runner_shared.append_jsonl"):
            runner_shared.reconcile_item_on_interrupt(
                repo=Path("/tmp/repo"),
                run_dir=run_dir,
                state=state,
                item=item,
                attempt=item["attempts"][0],
                attempt_no=1,
                work_dir="/tmp/worktree/test01",
                msg="clean-up-and-terminate",
                save_state_fn=self.save_state,
            )

        # Worktree torn down
        mock_teardown.assert_called_once()
        # Item reset to queued, attempt popped
        self.assertEqual(item["status"], "queued")
        self.assertNotIn("recovery_next", item)
        self.assertEqual(len(item["attempts"]), 0)

    @mock.patch("agent_workflows.worktree_lease.snapshot_lane_dirty_work")
    @mock.patch("agent_workflows.worktree_lease.teardown_worktree")
    @mock.patch("agent_workflows.runner_shared.describe_lane")
    def test_cleanup_when_files_changed_snapshots_and_preserves(
        self, mock_desc, mock_teardown, mock_snapshot
    ):
        mock_desc.return_value = {
            "lane_id": "test01",
            "worktree": "/tmp/worktree/test01",
            "branch": "aw/lane/test01",
            "base_sha": "abc1234",
            "holds_work": True,
            "dirty": True,
        }
        mock_snapshot.return_value = "snap123456"

        item = {
            "id6": "test01",
            "status": "executing",
            "attempts": [
                {
                    "attempt": 1,
                    "worktree": "/tmp/worktree/test01",
                    "worktree_lane_id": "test01",
                }
            ],
        }
        state = {"queue": [item]}
        run_dir = Path("/tmp/run-dir")

        with mock.patch("agent_workflows.runner_shared.append_jsonl"):
            runner_shared.reconcile_item_on_interrupt(
                repo=Path("/tmp/repo"),
                run_dir=run_dir,
                state=state,
                item=item,
                attempt=item["attempts"][0],
                attempt_no=1,
                work_dir="/tmp/worktree/test01",
                msg="clean-up-and-terminate",
                save_state_fn=self.save_state,
            )

        # Worktree NOT torn down
        mock_teardown.assert_not_called()
        # Dirty work was snapshotted
        mock_snapshot.assert_called_once()
        # Item marked interrupted with certainty known (resumable)
        self.assertEqual(item["status"], "interrupted")
        self.assertTrue(item["recovery_next"])
        self.assertFalse(runner_stop.is_indeterminate(item))
        self.assertEqual(item["stopped"]["certainty"], runner_stop.CERTAINTY_KNOWN)

        # Verify requeue_interrupted accepts it
        with mock.patch("agent_workflows.oc_runipd.append_jsonl"):
            requeued = oc_runipd.requeue_interrupted(run_dir, state)
            self.assertIn("test01", requeued)
            self.assertEqual(item["status"], "queued")
            self.assertTrue(item["recovery_next"])

    @mock.patch("agent_workflows.worktree_lease.teardown_worktree")
    @mock.patch("agent_workflows.worktree_lease.snapshot_lane_dirty_work")
    def test_just_terminate_no_cleanup_leaves_worktree_intact(
        self, mock_snapshot, mock_teardown
    ):
        item = {
            "id6": "test01",
            "status": "executing",
            "attempts": [
                {
                    "attempt": 1,
                    "worktree": "/tmp/worktree/test01",
                    "worktree_lane_id": "test01",
                }
            ],
        }
        state = {"queue": [item]}
        run_dir = Path("/tmp/run-dir")

        with mock.patch("agent_workflows.runner_shared.append_jsonl"):
            runner_shared.reconcile_item_on_interrupt(
                repo=Path("/tmp/repo"),
                run_dir=run_dir,
                state=state,
                item=item,
                attempt=item["attempts"][0],
                attempt_no=1,
                work_dir="/tmp/worktree/test01",
                msg="just-terminate-no-cleanup",
                save_state_fn=self.save_state,
            )

        mock_teardown.assert_not_called()
        mock_snapshot.assert_not_called()
        self.assertEqual(item["status"], "interrupted")
        self.assertTrue(item["recovery_next"])
        self.assertEqual(
            item["attempts"][0]["interrupt_reason"], "just-terminate-no-cleanup"
        )


class RunnerMainOutputOnInterruptTests(unittest.TestCase):
    def test_main_messages_match(self):
        for module in (oc_runipd, agy_runipd):
            # Test option 2 output in main
            with mock.patch.object(
                module,
                "run_queue",
                side_effect=KeyboardInterrupt("just-terminate-no-cleanup"),
            ), mock.patch.object(module, "emit_shutdown_report"), mock.patch.object(
                module, "resolve_run_dir", return_value=Path("/tmp/fake-run")
            ), mock.patch.object(
                module, "load_state", return_value={"options": {}}
            ), mock.patch.object(
                module, "locked_run", mock.MagicMock()
            ), mock.patch.object(
                module, "install_stop_triggers", mock.MagicMock()
            ), mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                code = module.main(["resume", "run-fake"])
                self.assertEqual(code, 130)
                self.assertIn(
                    "Terminated without clean up; worktree and lanes left in place.",
                    err.getvalue(),
                )

            # Test option 1 output in main
            with mock.patch.object(
                module,
                "run_queue",
                side_effect=KeyboardInterrupt("clean-up-and-terminate"),
            ), mock.patch.object(module, "emit_shutdown_report"), mock.patch.object(
                module, "resolve_run_dir", return_value=Path("/tmp/fake-run")
            ), mock.patch.object(
                module, "load_state", return_value={"options": {}}
            ), mock.patch.object(
                module, "locked_run", mock.MagicMock()
            ), mock.patch.object(
                module, "install_stop_triggers", mock.MagicMock()
            ), mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                code = module.main(["resume", "run-fake"])
                self.assertEqual(code, 130)
                self.assertIn(
                    "Interrupted; durable run state was preserved.", err.getvalue()
                )


class InteractiveSigintSignalTests(unittest.TestCase):
    @mock.patch("agent_workflows.runner_stop.handle_interactive_interrupt")
    @mock.patch("agent_workflows.runner_stop.request_stop_nowait")
    def test_interactive_sigint_actions(self, mock_request, mock_handle):
        run_dir = Path("/tmp/run-test")
        runner_stop.install_stop_signal_handlers(run_dir)
        import signal

        sigint_fn = signal.getsignal(signal.SIGINT)

        with mock.patch.dict("os.environ", {"AW_FORCE_INTERACTIVE_INTERRUPT": "1"}):
            # Choice 1: Resume
            mock_handle.return_value = runner_stop.INTERRUPT_ACTION_RESUME
            sigint_fn(signal.SIGINT, None)  # Should return without raising

            # Choice 2: Finish current item
            mock_handle.return_value = runner_stop.INTERRUPT_ACTION_FINISH_CURRENT
            sigint_fn(signal.SIGINT, None)  # Should return without raising
            mock_request.assert_called_with(run_dir, runner_stop.LEVEL_AFTER_CALL, "")

            # Choice 3: Clean up and terminate
            mock_handle.return_value = runner_stop.INTERRUPT_ACTION_CLEANUP
            with self.assertRaises(KeyboardInterrupt) as ctx:
                sigint_fn(signal.SIGINT, None)
            self.assertEqual(str(ctx.exception), "clean-up-and-terminate")
            mock_request.assert_called_with(run_dir, runner_stop.LEVEL_NOW_FORCE, "")

            # Choice 4: Just terminate with no cleanup
            mock_handle.return_value = runner_stop.INTERRUPT_ACTION_TERMINATE_NO_CLEANUP
            with self.assertRaises(KeyboardInterrupt) as ctx:
                sigint_fn(signal.SIGINT, None)
            self.assertEqual(str(ctx.exception), "just-terminate-no-cleanup")


if __name__ == "__main__":
    unittest.main()

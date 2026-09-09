#!/usr/bin/env python3
"""The Ctrl-C menu may not block unless a human can BOTH see the question and answer it.

WHY THIS FILE EXISTS, and why the guard is not paranoia. `prompt_interrupt_action` renders the
four-choice interrupt menu and then blocks on an unbounded `readline()`. Before this fix the handler
decided whether to do that from `sys.stdin.isatty()` ALONE, while writing the prompt to `sys.stderr`,
which it never checked.

THAT EXACT PREDICATE ERROR HAS ALREADY COST THIS REPOSITORY 1h49m. `ipd_lifecycle.run_finalize`
carries the incident note: a parent spawns a child with stdout/stderr PIPED but stdin INHERITED, so
the child sees the operator's terminal, decides it may prompt, writes the question into a pipe nobody
reads, and waits forever for an answer nobody knows is wanted. It wedged a finalize while holding its
run lock, leaving the plan `approved` in `pending/` while the run reported `complete`.

THE INTERRUPT MENU IS A STRICTLY WORSE PLACE FOR IT: the wait happens inside a SIGNAL HANDLER, while
the run holds its lock, with no timeout. So a wedge there blocks the operator's own escape path, which
is the one path that must always work.

THE FIX IS FAIL-SAFE, NOT A REFUSAL: when the menu is unsafe the handler falls through to the
documented `SIGINT_LADDER`, which needs no answer from anybody. So the operator always gets a stop.

FOUR PROPERTIES, each independently falsifiable:
  1. The predicate requires BOTH streams to be a terminal (the measured wedge shape is stdin-TTY plus
     piped output, and that case must be refused).
  2. An explicit "nobody is watching" signal (`AW_NONINTERACTIVE` / `CI`) refuses regardless of the
     streams, and it BEATS the force override, because CI is where an unbounded wait is least
     recoverable.
  3. THE HANDLER ITSELF does not call the blocking prompt when the menu is unsafe. Property 1 is about
     a predicate; this is about the code path that would actually hang.
  4. The ladder still governs the unsafe case, so a stop is still requested.
"""

from __future__ import annotations

import io
import os
import signal
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import runner_stop


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class _FakePipe(io.StringIO):
    def isatty(self) -> bool:
        return False


class _Exploding(io.StringIO):
    """A stream whose `isatty` raises, as a closed/detached stream can."""

    def isatty(self) -> bool:
        raise ValueError("I/O operation on closed file")


_ENV_KEYS = ("AW_NONINTERACTIVE", "CI", "AW_FORCE_INTERACTIVE_INTERRUPT")


class _CleanEnv(unittest.TestCase):
    """Neutralize the three environment signals so a developer's own shell cannot flip a result."""

    def setUp(self) -> None:
        self._patcher = mock.patch.dict(
            os.environ, {k: "" for k in _ENV_KEYS}, clear=False
        )
        self._patcher.start()
        self.addCleanup(self._patcher.stop)


class PredicateTests(_CleanEnv):
    def test_both_streams_tty_is_safe(self):
        self.assertTrue(runner_stop.interrupt_menu_is_safe(_FakeTTY(), _FakeTTY()))

    def test_the_measured_wedge_shape_is_refused(self):
        """stdin inherited from the terminal, output piped: the 1h49m incident's exact shape."""
        self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakeTTY(), _FakePipe()))

    def test_unreadable_stdin_is_refused(self):
        self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakePipe(), _FakeTTY()))

    def test_neither_stream_tty_is_refused(self):
        self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakePipe(), _FakePipe()))

    def test_a_closed_stream_is_not_a_terminal(self):
        """`isatty()` on a detached stream raises; that must read as 'not a terminal', not crash."""
        self.assertFalse(runner_stop.interrupt_menu_is_safe(_Exploding(), _FakeTTY()))
        self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakeTTY(), _Exploding()))


class ForcedNoninteractiveTests(_CleanEnv):
    def test_ci_refuses_even_on_a_real_terminal(self):
        with mock.patch.dict(os.environ, {"CI": "1"}):
            self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakeTTY(), _FakeTTY()))

    def test_aw_noninteractive_refuses_even_on_a_real_terminal(self):
        with mock.patch.dict(os.environ, {"AW_NONINTERACTIVE": "1"}):
            self.assertFalse(runner_stop.interrupt_menu_is_safe(_FakeTTY(), _FakeTTY()))

    def test_falsey_spellings_do_not_force(self):
        """Empty/0/false/no must NOT be read as 'set', or exporting CI=0 would disable the menu."""
        for value in ("", "0", "false", "no", "FALSE", "No"):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {"CI": value}):
                    self.assertTrue(
                        runner_stop.interrupt_menu_is_safe(_FakeTTY(), _FakeTTY())
                    )

    def test_force_override_works_without_ttys(self):
        with mock.patch.dict(os.environ, {"AW_FORCE_INTERACTIVE_INTERRUPT": "1"}):
            self.assertTrue(
                runner_stop.interrupt_menu_is_safe(_FakePipe(), _FakePipe())
            )

    def test_ci_beats_the_force_override(self):
        """A deliberate CI setting must win over a stale force flag."""
        with mock.patch.dict(
            os.environ, {"AW_FORCE_INTERACTIVE_INTERRUPT": "1", "CI": "1"}
        ):
            self.assertFalse(
                runner_stop.interrupt_menu_is_safe(_FakePipe(), _FakePipe())
            )


class HandlerDoesNotBlockTests(_CleanEnv):
    """Property 3: the SIGINT handler must not reach the blocking prompt when the menu is unsafe.

    This is the property that actually prevents the hang. A predicate can be correct while the
    handler still calls the prompt, so these assert on the handler's own behavior.
    """

    def _sigint_handler(self, run_dir: Path):
        runner_stop.install_stop_signal_handlers(run_dir)
        return signal.getsignal(signal.SIGINT)

    @mock.patch("agent_workflows.runner_stop.request_stop_nowait")
    @mock.patch(
        "agent_workflows.runner_stop.prompt_interrupt_action",
        side_effect=AssertionError("the blocking prompt must NOT be reached"),
    )
    def test_piped_output_never_reaches_the_prompt(self, mock_prompt, mock_request):
        """The wedge shape. If the guard regresses, `prompt_interrupt_action` raises and this fails."""
        runner_stop.reset_signal_ladder()
        handler = self._sigint_handler(Path("/tmp/run-wedge-test"))
        with mock.patch("sys.stdin", _FakeTTY()), mock.patch("sys.stderr", _FakePipe()):
            # The ladder's FIRST rung records and returns; it does not raise. That is correct: a
            # first press asks for a graceful stop, it does not tear the run down.
            handler(signal.SIGINT, None)
        mock_prompt.assert_not_called()

    @mock.patch("agent_workflows.runner_stop.request_stop_nowait")
    @mock.patch(
        "agent_workflows.runner_stop.prompt_interrupt_action",
        side_effect=AssertionError("the blocking prompt must NOT be reached"),
    )
    def test_ci_never_reaches_the_prompt(self, mock_prompt, mock_request):
        runner_stop.reset_signal_ladder()
        handler = self._sigint_handler(Path("/tmp/run-ci-test"))
        with mock.patch.dict(os.environ, {"CI": "1"}), mock.patch(
            "sys.stdin", _FakeTTY()
        ), mock.patch("sys.stderr", _FakeTTY()):
            handler(signal.SIGINT, None)
        mock_prompt.assert_not_called()

    @mock.patch("agent_workflows.runner_stop.request_stop_nowait")
    def test_the_ladder_still_requests_a_stop_in_the_unsafe_case(self, mock_request):
        """Property 4: falling back is fail-SAFE, so the operator still gets a stop.

        The first ladder rung is level 1 (`after-call`), so an unattended Ctrl-C now requests the
        GENTLE level rather than hanging, which is what spec R12 specifies for a first press.
        """
        runner_stop.reset_signal_ladder()
        handler = self._sigint_handler(Path("/tmp/run-ladder-test"))
        with mock.patch("sys.stdin", _FakeTTY()), mock.patch("sys.stderr", _FakePipe()):
            handler(signal.SIGINT, None)
        self.assertTrue(mock_request.called, "no stop was requested at all")
        level = mock_request.call_args[0][1]
        self.assertEqual(
            level,
            runner_stop.SIGINT_LADDER[0],
            "the unsafe path must use the ladder's first rung",
        )
        self.assertEqual(level, runner_stop.LEVEL_AFTER_CALL)

    @mock.patch("agent_workflows.runner_stop.request_stop_nowait")
    @mock.patch("agent_workflows.runner_stop.handle_interactive_interrupt")
    def test_a_real_terminal_still_gets_the_menu(self, mock_handle, mock_request):
        """The guard only ADDS conditions: a genuine human terminal must still be prompted."""
        mock_handle.return_value = runner_stop.INTERRUPT_ACTION_RESUME
        handler = self._sigint_handler(Path("/tmp/run-tty-test"))
        with mock.patch("sys.stdin", _FakeTTY()), mock.patch("sys.stderr", _FakeTTY()):
            handler(signal.SIGINT, None)  # RESUME returns without raising
        mock_handle.assert_called_once()


if __name__ == "__main__":
    unittest.main()

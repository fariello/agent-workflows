"""Tests for CLI Output Mode Precedence and OutputContext resolution.

awcliux Order 01 (`hd3kln`) E-01 / V-01.

Truth-table tests for:
- stdout TTY / non-TTY (piped)
- stdin TTY vs stdout TTY
- explicit --json / --format
- --agent / --as_agent flags
- --no-color flag, NO_COLOR, FORCE_COLOR, TERM=dumb
- broken pipe handling
"""

from __future__ import annotations

import io
import os
import types
import unittest
from unittest.mock import MagicMock, patch

from agent_workflows.result_types import (
    CommandResult,
    OutputContext,
    OutputMode,
    select_output,
)
from agent_workflows.renderers import (
    AgentRenderer,
    HumanRenderer,
    JsonRenderer,
    get_renderer,
)


class FakeStream(io.StringIO):
    def __init__(self, is_a_tty: bool = False):
        super().__init__()
        self._is_a_tty = is_a_tty

    def isatty(self) -> bool:
        return self._is_a_tty


class OutputModePrecedenceTests(unittest.TestCase):
    """Truth-table tests for select_output precedence (E-01 / V-01)."""

    def test_explicit_json_flag_overrides_agent_and_tty(self):
        # Explicit --json wins over everything, selecting JSON mode with color=False
        args = types.SimpleNamespace(as_json=True, agent=True, no_color=False)
        stream = FakeStream(is_a_tty=True)
        ctx = select_output(args, stdout=stream)
        self.assertEqual(ctx.mode, OutputMode.JSON)
        self.assertTrue(ctx.is_json)
        self.assertFalse(ctx.is_agent)
        self.assertFalse(ctx.is_human)
        self.assertFalse(ctx.color)
        self.assertEqual(ctx.explicit_format, "json")

    def test_explicit_format_json_overrides_tty(self):
        # Explicit --format json selects JSON mode
        args = types.SimpleNamespace(format="json", agent=False, no_color=False)
        stream = FakeStream(is_a_tty=True)
        ctx = select_output(args, stdout=stream)
        self.assertEqual(ctx.mode, OutputMode.JSON)
        self.assertTrue(ctx.is_json)
        self.assertFalse(ctx.color)

    def test_agent_flag_on_tty_selects_agent_mode(self):
        # --agent on a real TTY stdout forces agent mode
        args = types.SimpleNamespace(agent=True, no_color=False)
        stream = FakeStream(is_a_tty=True)
        ctx = select_output(args, stdout=stream)
        self.assertEqual(ctx.mode, OutputMode.AGENT)
        self.assertTrue(ctx.is_agent)
        self.assertFalse(ctx.is_human)
        self.assertFalse(ctx.color)

    def test_non_tty_stdout_automatically_selects_agent_mode(self):
        # Non-TTY stdout (piped / redirected) automatically selects agent mode without any flag
        args = types.SimpleNamespace(agent=False, no_color=False)
        stream = FakeStream(is_a_tty=False)
        ctx = select_output(args, stdout=stream)
        self.assertEqual(ctx.mode, OutputMode.AGENT)
        self.assertTrue(ctx.is_agent)
        self.assertFalse(ctx.is_human)
        self.assertFalse(ctx.color)

    def test_tty_stdout_selects_human_mode(self):
        # TTY stdout without agent/json flags selects human mode
        args = types.SimpleNamespace(agent=False, no_color=False)
        stream = FakeStream(is_a_tty=True)
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            ctx = select_output(args, stdout=stream)
            self.assertEqual(ctx.mode, OutputMode.HUMAN)
            self.assertTrue(ctx.is_human)
            self.assertFalse(ctx.is_agent)
            self.assertTrue(ctx.color)

    def test_no_color_flag_preserves_human_mode_disables_color(self):
        # --no-color on a TTY stdout stays in human mode, with color=False
        args = types.SimpleNamespace(agent=False, no_color=True)
        stream = FakeStream(is_a_tty=True)
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            ctx = select_output(args, stdout=stream)
            self.assertEqual(ctx.mode, OutputMode.HUMAN)
            self.assertFalse(ctx.color)

    def test_no_color_env_preserves_human_mode_disables_color(self):
        # NO_COLOR=1 on TTY stays in human mode, with color=False
        args = types.SimpleNamespace(agent=False, no_color=False)
        stream = FakeStream(is_a_tty=True)
        with patch.dict(
            os.environ, {"NO_COLOR": "1", "TERM": "xterm-256color"}, clear=True
        ):
            ctx = select_output(args, stdout=stream)
            self.assertEqual(ctx.mode, OutputMode.HUMAN)
            self.assertFalse(ctx.color)

    def test_force_color_on_tty_enables_color(self):
        # FORCE_COLOR=1 enables color on TTY
        args = types.SimpleNamespace(agent=False, no_color=False)
        stream = FakeStream(is_a_tty=True)
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=True):
            ctx = select_output(args, stdout=stream)
            self.assertEqual(ctx.mode, OutputMode.HUMAN)
            self.assertTrue(ctx.color)

    def test_stdin_non_tty_does_not_change_output_mode(self):
        # stdin TTY controls prompting, not output audience; stdout TTY dictates human mode
        args = types.SimpleNamespace(agent=False, no_color=False)
        stdout_stream = FakeStream(is_a_tty=True)
        stdin_stream = FakeStream(is_a_tty=False)
        with patch("sys.stdin", stdin_stream):
            with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
                ctx = select_output(args, stdout=stdout_stream)
                self.assertEqual(ctx.mode, OutputMode.HUMAN)

    def test_get_renderer_mapping(self):
        # get_renderer returns the correct renderer class for each mode
        self.assertIsInstance(
            get_renderer(OutputContext(mode=OutputMode.HUMAN)), HumanRenderer
        )
        self.assertIsInstance(
            get_renderer(OutputContext(mode=OutputMode.AGENT)), AgentRenderer
        )
        self.assertIsInstance(
            get_renderer(OutputContext(mode=OutputMode.JSON)), JsonRenderer
        )


class BrokenPipeHandlingTests(unittest.TestCase):
    """Assert clean termination on BrokenPipeError (E-03 / V-03)."""

    def test_renderer_emit_handles_broken_pipe_cleanly(self):
        mock_stdout = MagicMock()
        mock_stdout.write.side_effect = BrokenPipeError("Broken pipe")
        ctx = OutputContext(mode=OutputMode.AGENT, stdout=mock_stdout)
        res = CommandResult(command="test", status="clean", exit_code=0)
        renderer = AgentRenderer()
        # Does not raise BrokenPipeError; exits cleanly returning exit_code
        ret = renderer.emit(res, ctx)
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()

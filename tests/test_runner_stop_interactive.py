"""Tests for interactive runner stop prompt, interrupt handling, and event stream formatting."""

from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from agent_workflows import agy_runipd, render_stream, runner_stop
from agent_workflows.render_stream import Palette
from agent_workflows.term import strip_ansi, visible_width


class InteractivePromptTests(unittest.TestCase):
    """Test prompt_interrupt_action box styling, compaction, and responses."""

    def test_prompt_box_layout_and_rectangular_width_unicode(self):
        """Verify prompt box is compact, bordered, and rectangular across all rows in Unicode."""
        in_buf = io.StringIO("1\n")
        out_buf = io.StringIO()

        action = runner_stop.prompt_interrupt_action(stdin=in_buf, stream=out_buf)
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_RESUME)

        output = out_buf.getvalue()
        plain_lines = [strip_ansi(line) for line in output.split("\n")]
        # Box rows: top, 4 options, bottom
        box_rows = [line for line in plain_lines if line.startswith(("╭─", "│", "╰"))]
        self.assertEqual(len(box_rows), 6)
        widths = [visible_width(r) for r in box_rows]
        self.assertTrue(len(set(widths)) == 1, f"Box rows not equal width: {widths}")
        self.assertEqual(widths[0], 62)

        # Check content inside box
        self.assertIn("Stopped on Ctrl-C. Choose an action:", box_rows[0])
        self.assertIn("1. Resume?", box_rows[1])
        self.assertIn("2. Finish current item, clean up, and exit?", box_rows[2])
        self.assertIn("3. Clean up and exit?", box_rows[3])
        self.assertIn("4. Exit, leaving a mess?", box_rows[4])
        self.assertIn("Choice [1-4]:", plain_lines[-1])

    def test_prompt_box_layout_and_rectangular_width_ascii(self):
        """Verify prompt box layout in ASCII mode."""
        in_buf = io.StringIO("2\n")
        out_buf = io.StringIO()

        with mock.patch("agent_workflows.term.should_unicode", return_value=False):
            action = runner_stop.prompt_interrupt_action(stdin=in_buf, stream=out_buf)
        self.assertEqual(action, runner_stop.INTERRUPT_ACTION_FINISH_CURRENT)

        output = out_buf.getvalue()
        plain_lines = [strip_ansi(line) for line in output.split("\n")]
        box_rows = [line for line in plain_lines if line.startswith(("+", "|"))]
        self.assertEqual(len(box_rows), 6)
        widths = [visible_width(r) for r in box_rows]
        self.assertTrue(
            len(set(widths)) == 1, f"ASCII box rows not equal width: {widths}"
        )
        self.assertEqual(widths[0], 62)

    def test_prompt_choices_and_retries(self):
        """Verify valid choices 3 and 4, invalid retry, and EOF."""
        # Choice 3
        in_3 = io.StringIO("3\n")
        self.assertEqual(
            runner_stop.prompt_interrupt_action(stdin=in_3, stream=io.StringIO()),
            runner_stop.INTERRUPT_ACTION_CLEANUP,
        )

        # Choice 4
        in_4 = io.StringIO("4\n")
        self.assertEqual(
            runner_stop.prompt_interrupt_action(stdin=in_4, stream=io.StringIO()),
            runner_stop.INTERRUPT_ACTION_TERMINATE_NO_CLEANUP,
        )

        # Invalid then valid
        in_retry = io.StringIO("invalid\n1\n")
        out_retry = io.StringIO()
        self.assertEqual(
            runner_stop.prompt_interrupt_action(stdin=in_retry, stream=out_retry),
            runner_stop.INTERRUPT_ACTION_RESUME,
        )
        self.assertIn("Please enter 1, 2, 3, or 4:", out_retry.getvalue())

        # EOF
        in_eof = io.StringIO("")
        self.assertEqual(
            runner_stop.prompt_interrupt_action(stdin=in_eof, stream=io.StringIO()),
            runner_stop.INTERRUPT_ACTION_CLEANUP,
        )


class HandleInteractiveInterruptOrderingTests(unittest.TestCase):
    """Test that handle_interactive_interrupt coordinates unpausing, messaging, and statusline."""

    def test_finish_current_orders_on_action_before_statusline_resume(self):
        call_order = []

        def mock_pause_statusline():
            call_order.append("pause_statusline")

        def mock_resume_statusline():
            call_order.append("resume_statusline")

        def mock_pause_children():
            call_order.append("pause_children")
            return ["fake_proc"]

        def mock_resume_children(procs):
            call_order.append("resume_children")

        def mock_on_action(action):
            call_order.append(f"on_action_{action}")

        out_buf = io.StringIO()
        with (
            mock.patch.object(
                render_stream,
                "pause_active_statusline",
                side_effect=mock_pause_statusline,
            ),
            mock.patch.object(
                render_stream,
                "resume_active_statusline",
                side_effect=mock_resume_statusline,
            ),
            mock.patch.object(
                runner_stop, "pause_live_children", side_effect=mock_pause_children
            ),
            mock.patch.object(
                runner_stop, "resume_live_children", side_effect=mock_resume_children
            ),
            mock.patch.object(
                runner_stop,
                "prompt_interrupt_action",
                return_value=runner_stop.INTERRUPT_ACTION_FINISH_CURRENT,
            ),
        ):
            act = runner_stop.handle_interactive_interrupt(
                stdin=io.StringIO("2\n"),
                stream=out_buf,
                on_action=mock_on_action,
            )

        self.assertEqual(act, runner_stop.INTERRUPT_ACTION_FINISH_CURRENT)
        self.assertIn("Finishing current item before stopping...", out_buf.getvalue())
        # on_action and resume_children MUST occur before resume_statusline
        self.assertEqual(call_order[0], "pause_children")
        self.assertEqual(call_order[1], "pause_statusline")
        self.assertIn("on_action_2", call_order)
        self.assertIn("resume_children", call_order)
        self.assertEqual(call_order[-1], "resume_statusline")


class StreamTruncationAndThinkingTests(unittest.TestCase):
    """Test 350-column truncation with […] and untruncated think output."""

    def test_agy_event_truncation_marker_and_limit(self):
        pal = Palette(False, use_unicode=True)
        # Command under 350 chars is not truncated
        cmd_200 = "pytest " + ("tests/test_foo.py " * 10)
        self.assertLess(len(cmd_200), 350)
        evt_short = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": cmd_200},
                    },
                },
            }
        )
        rendered_short = agy_runipd.render_agy_event(evt_short, pal)
        self.assertIsNotNone(rendered_short)
        self.assertIn(cmd_200.strip(), rendered_short)
        self.assertNotIn("[…]", rendered_short)

        # Command over 350 chars is truncated with […]
        cmd_500 = "python3 -c '" + ("abcde " * 90) + "'"
        self.assertGreater(len(cmd_500), 350)
        evt_long = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": cmd_500},
                    },
                },
            }
        )
        rendered_long = agy_runipd.render_agy_event(evt_long, pal)
        self.assertIsNotNone(rendered_long)
        self.assertIn("[…]", rendered_long)
        self.assertLessEqual(
            visible_width(strip_ansi(rendered_long.split(" (")[0])), 365
        )

    def test_think_output_is_not_truncated(self):
        pal = Palette(False, use_unicode=True)
        long_thought = "Thinking about the implementation details. " * 25  # ~1075 chars
        self.assertGreater(len(long_thought), 1000)

        cid = "conv-think-test"
        step_idx = 10
        step_rec = {
            "step_index": step_idx,
            "type": "PLANNER_RESPONSE",
            "thinking": long_thought,
        }

        evt = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "conversation_id": cid,
                    "step_index": step_idx,
                    "state": "DONE",
                    "step_type": "agent_response",
                },
            }
        )

        with mock.patch(
            "agent_workflows.agy_runipd._read_agy_step_transcript",
            return_value=step_rec,
        ):
            rendered = agy_runipd.render_agy_event(evt, pal)

        self.assertIsNotNone(rendered)
        self.assertIn("think:", rendered)
        # Complete thought must be preserved without truncation
        self.assertIn(long_thought.strip(), rendered)
        self.assertNotIn("…", rendered)
        self.assertNotIn("[…]", rendered)


if __name__ == "__main__":
    unittest.main()

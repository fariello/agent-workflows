#!/usr/bin/env python3
"""Tests for the shared interactive streaming renderer (runnernorm child dg28i9).

Covers:
1. Unit behavior of the extracted renderer: ``render_event`` event->line mapping,
   ``Palette`` applies/omits color per the flag, and ``Heartbeat`` enter/exit/interval
   lifecycle.
2. A GOLDEN byte-identical test: the rendered output for a fixed event stream matches a
   pinned expected transcript, proving the extraction preserved behavior.
3. SINGLE-DEFINITION assertions: the render layer is defined once in
   ``agent_workflows.render_stream``; ``agent_workflows.oc_runipd`` carries no inline copy
   (source inspection) and its names are the SAME objects re-exported from render_stream
   (identity check).
"""

from __future__ import annotations

import inspect
import io
import json
import time
import unittest

from agent_workflows import oc_runipd as driver
from agent_workflows import render_stream


class RenderEventUnitTests(unittest.TestCase):
    """render_event maps sample events to expected concise lines."""

    def setUp(self) -> None:
        self.plain = render_stream.Palette(False)

    def test_text_event_renders_narration(self):
        line = render_stream.render_event(
            '{"type":"text","part":{"type":"text","text":"Reading the plan."}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("Reading the plan.", line)
        self.assertNotIn("\033[", line)

    def test_tool_use_renders_tool_and_title(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"bash",'
            '"state":{"status":"completed","title":"git status --short"}}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("bash", line)
        self.assertIn("git status --short", line)

    def test_tool_use_derives_title_from_input_when_missing(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"read",'
            '"state":{"status":"running","input":{"path":"a.py"}}}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("read", line)
        self.assertIn("a.py", line)

    def test_step_start_and_blank_are_suppressed(self):
        self.assertIsNone(
            render_stream.render_event('{"type":"step_start"}', self.plain)
        )
        self.assertIsNone(render_stream.render_event("   ", self.plain))

    def test_step_finish_summarizes_tokens_and_cost(self):
        line = render_stream.render_event(
            '{"type":"step_finish","part":{"tokens":{"total":1234},"cost":0.0042}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("1234 tok", line)
        self.assertIn("$0.0042", line)

    def test_non_json_line_passed_through_dimmed(self):
        line = render_stream.render_event("a stray log line", self.plain)
        assert line is not None
        self.assertIn("a stray log line", line)

    def test_long_text_is_clipped_to_single_line(self):
        long = "word " * 200
        line = render_stream.render_event(
            json.dumps({"type": "text", "part": {"text": long}}), self.plain
        )
        assert line is not None
        self.assertNotIn("\n", line)
        self.assertLessEqual(len(line), 420)


class PaletteUnitTests(unittest.TestCase):
    """Palette applies/omits color per the enabled flag."""

    def test_palette_noop_when_disabled(self):
        pal = render_stream.Palette(False)
        self.assertEqual(pal("x", "green"), "x")

    def test_palette_active_when_enabled(self):
        colored = render_stream.Palette(True)("x", "green")
        self.assertTrue(colored.startswith("\033["))
        self.assertIn("x", colored)
        self.assertTrue(colored.endswith(render_stream._ANSI_RESET))

    def test_palette_status_maps_known_status_to_color(self):
        pal = render_stream.Palette(True)
        out = pal.status("executed")
        # "executed" -> green (code 32)
        self.assertIn("32", out)
        self.assertIn("executed", out)

    def test_palette_status_passthrough_for_unknown(self):
        pal = render_stream.Palette(True)
        self.assertEqual(pal.status("no-such-status"), "no-such-status")

    def test_strip_ansi_removes_sgr(self):
        colored = render_stream.Palette(True)("hello", "red", "bold")
        self.assertEqual(render_stream._strip_ansi(colored), "hello")


class HeartbeatLifecycleTests(unittest.TestCase):
    """Heartbeat enter/exit/interval lifecycle."""

    def test_disabled_heartbeat_writes_nothing(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        hb = render_stream.Heartbeat(pal, "test-ipd", buf, interval=0)
        with hb:
            time.sleep(0.05)
        self.assertEqual(buf.getvalue(), "")

    def test_enabled_heartbeat_emits_while_idle(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        hb = render_stream.Heartbeat(pal, "test-ipd", buf, interval=0.05)
        with hb:
            time.sleep(0.2)
        out = buf.getvalue()
        self.assertIn("still working on test-ipd", out)

    def test_touch_resets_idle_and_format_message(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        hb = render_stream.Heartbeat(pal, "lbl", buf, interval=1.0)
        hb.touch()
        self.assertIn("still working on lbl", hb.format_message())
        self.assertRegex(hb.format_idle(), r"^\d+m\d{2}s$")


# A fixed event stream and its pinned expected transcript. This is the GOLDEN input:
# if the renderer changes behavior, one of these lines will differ.
_GOLDEN_EVENTS = [
    "",
    '{"type":"step_start"}',
    '{"type":"text","part":{"type":"text","text":"Reading the plan."}}',
    '{"type":"tool_use","part":{"tool":"bash",'
    '"state":{"status":"running","title":"git status"}}}',
    '{"type":"tool_use","part":{"tool":"bash",'
    '"state":{"status":"completed","title":"git status"}}}',
    '{"type":"tool_use","part":{"tool":"edit",'
    '"state":{"status":"error","title":"patch failed"}}}',
    '{"type":"step_finish","part":{"tokens":{"total":1234},"cost":0.0042}}',
    "a stray non-json log line",
    '{"type":"unknown_event"}',
]


def _render_stream_transcript(events, pal):
    out = []
    for raw in events:
        rendered = pal_render(raw, pal)
        if rendered is not None:
            out.append(rendered)
    return "\n".join(out)


def pal_render(raw, pal):
    return render_stream.render_event(raw, pal)


class GoldenByteIdenticalTests(unittest.TestCase):
    """The rendered output for a fixed event stream is byte-identical to a pinned transcript.

    The pinned transcript is what runipd emitted for this stream before the extraction; this
    proves the shared renderer preserves byte-for-byte behavior.
    """

    def test_plain_transcript_is_byte_identical(self):
        pal = render_stream.Palette(False)
        transcript = _render_stream_transcript(_GOLDEN_EVENTS, pal)
        expected = "\n".join(
            [
                "  \u2022 Reading the plan.",
                "    \u2026 bash: git status",
                "    \u2713 bash: git status",
                "    \u2717 edit: patch failed",
                "    \u2014 step done (1234 tok, $0.0042)",
                "  a stray non-json log line",
            ]
        )
        self.assertEqual(transcript, expected)

    def test_driver_reexport_produces_identical_transcript(self):
        # Driving the SAME stream through the oc_runipd re-exported names yields the
        # identical transcript (the re-export is not a divergent copy).
        pal_via_driver = driver.Palette(False)
        via_driver = "\n".join(
            r
            for raw in _GOLDEN_EVENTS
            if (r := driver.render_event(raw, pal_via_driver)) is not None
        )
        pal_via_module = render_stream.Palette(False)
        via_module = _render_stream_transcript(_GOLDEN_EVENTS, pal_via_module)
        self.assertEqual(via_driver, via_module)

    def test_colored_transcript_strips_back_to_plain(self):
        # With color on, stripping ANSI recovers the plain transcript (color is additive).
        colored = render_stream.Palette(True)
        plain = render_stream.Palette(False)
        colored_txt = _render_stream_transcript(_GOLDEN_EVENTS, colored)
        plain_txt = _render_stream_transcript(_GOLDEN_EVENTS, plain)
        self.assertEqual(render_stream._strip_ansi(colored_txt), plain_txt)


class SingleDefinitionTests(unittest.TestCase):
    """The render layer has a SINGLE definition in render_stream; oc_runipd only re-exports."""

    def test_names_are_the_same_objects(self):
        # Identity: the driver's names ARE the render_stream objects (no inline copy).
        self.assertIs(driver.Palette, render_stream.Palette)
        self.assertIs(driver.render_event, render_stream.render_event)
        self.assertIs(driver.Heartbeat, render_stream.Heartbeat)
        self.assertIs(driver._STATUS_COLOR, render_stream._STATUS_COLOR)
        self.assertIs(driver._ANSI_CODES, render_stream._ANSI_CODES)
        self.assertIs(driver._ANSI_RESET, render_stream._ANSI_RESET)
        self.assertIs(driver._strip_ansi, render_stream._strip_ansi)
        self.assertIs(driver._one_line, render_stream._one_line)

    def test_definitions_live_in_render_stream_module(self):
        for obj in (
            render_stream.Palette,
            render_stream.render_event,
            render_stream.Heartbeat,
        ):
            module = inspect.getmodule(obj)
            assert module is not None
            self.assertEqual(module.__name__, "agent_workflows.render_stream")

    def test_oc_runipd_source_has_no_inline_definitions(self):
        # Source inspection: oc_runipd must not re-DEFINE the render layer inline.
        src = inspect.getsource(driver)
        self.assertNotIn("class Palette:", src)
        self.assertNotIn("class Heartbeat:", src)
        self.assertNotIn("def render_event(", src)
        self.assertNotIn("def _one_line(", src)
        self.assertNotIn("def _strip_ansi(", src)
        # It must import them from the shared module instead.
        self.assertIn("from agent_workflows.render_stream import", src)


if __name__ == "__main__":
    unittest.main()

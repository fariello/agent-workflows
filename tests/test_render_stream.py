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

from agent_workflows import agy_runipd as agy_driver
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
        self.assertEqual(line, "\u2022 Reading the plan.")
        self.assertNotIn("\033[", line)

    def test_tool_use_renders_tool_and_title(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"bash",'
            '"state":{"status":"completed","title":"git status --short"}}}',
            self.plain,
        )
        assert line is not None
        self.assertEqual(line, "\u2713 bash: git status --short")

    def test_tool_use_derives_title_from_input_when_missing(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"read",'
            '"state":{"status":"running","input":{"path":"a.py"}}}}',
            self.plain,
        )
        assert line is not None
        self.assertEqual(line, '\u2026 read: {"path": "a.py"}')

    def test_step_start_and_blank_are_suppressed(self):
        self.assertIsNone(
            render_stream.render_event('{"type":"step_start"}', self.plain)
        )
        self.assertIsNone(render_stream.render_event("   ", self.plain))

    def test_step_finish_updates_tracker_and_is_suppressed(self):
        tracker = render_stream.StreamTracker()
        evt1 = (
            '{"type":"step_finish","part":{"tokens":{"total":30476,"input":30371,'
            '"output":105,"cache":{"read":30000,"write":0}},"cost":0.15448}}'
        )
        line1 = render_stream.render_event(evt1, self.plain, tracker=tracker)
        self.assertIsNone(line1)
        self.assertEqual(tracker.input_tokens, 30371)
        self.assertEqual(tracker.output_tokens, 105)
        self.assertEqual(tracker.cache_tokens, 30000)
        self.assertAlmostEqual(tracker.cost, 0.15448)

        evt2 = (
            '{"type":"step_finish","part":{"tokens":{"total":37480,"input":7000,'
            '"output":480,"cache":{"read":30000,"write":0}},"cost":0.0088}}'
        )
        line2 = render_stream.render_event(evt2, self.plain, tracker=tracker)
        self.assertIsNone(line2)
        self.assertEqual(tracker.input_tokens, 37371)
        self.assertEqual(tracker.output_tokens, 585)
        self.assertEqual(tracker.cache_tokens, 60000)
        self.assertAlmostEqual(tracker.cost, 0.16328)

    def test_format_tokens_units(self):
        self.assertEqual(render_stream.format_tokens(0), "0")
        self.assertEqual(render_stream.format_tokens(500), "500")
        self.assertEqual(render_stream.format_tokens(1000), "1.00K")
        self.assertEqual(render_stream.format_tokens(37480), "37.48K")
        self.assertEqual(render_stream.format_tokens(1_500_000), "1.50M")
        self.assertEqual(render_stream.format_tokens(2_500_000_000), "2.50G")

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
        # stallfp kaga7s: the line names the IPD and reports LACK OF PROGRESS, rather than
        # the old bare "still working" that read as reassurance while a kill clock ran.
        self.assertIn("test-ipd", out)
        self.assertIn("no progress", out)

    def test_touch_resets_idle_and_format_message(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        hb = render_stream.Heartbeat(pal, "lbl", buf, interval=1.0)
        hb.touch()
        self.assertIn("lbl", hb.format_message())
        self.assertIn("no progress", hb.format_message())
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
                "\u2022 Reading the plan.",
                "\u2026 bash: git status",
                "\u2713 bash: git status",
                "\u2717 edit: patch failed",
                "a stray non-json log line",
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


class StatuslineUnitTests(unittest.TestCase):
    """Statusline formatters and component unit tests."""

    def test_format_compact_tokens(self):
        self.assertEqual(render_stream.format_compact_tokens(0), "0")
        self.assertEqual(render_stream.format_compact_tokens(500), "500")
        self.assertEqual(render_stream.format_compact_tokens(1000), "1k")
        self.assertEqual(render_stream.format_compact_tokens(4100), "4.1k")
        self.assertEqual(render_stream.format_compact_tokens(24500), "24.5k")
        self.assertEqual(render_stream.format_compact_tokens(88200), "88.2k")
        self.assertEqual(render_stream.format_compact_tokens(1_500_000), "1.5m")
        self.assertEqual(render_stream.format_compact_tokens(2_000_000_000), "2g")

    def test_format_progress_bar(self):
        self.assertEqual(
            render_stream.format_progress_bar(0, 0), "░░░░░░░░░░  0% [0/0]"
        )
        self.assertEqual(
            render_stream.format_progress_bar(0, 5), "░░░░░░░░░░  0% [0/5]"
        )
        self.assertEqual(
            render_stream.format_progress_bar(4, 5), "████████░░ 80% [4/5]"
        )
        self.assertEqual(
            render_stream.format_progress_bar(5, 5), "██████████ 100% [5/5]"
        )

    def test_format_compact_duration(self):
        self.assertEqual(render_stream.format_compact_duration(0), "0m00s")
        self.assertEqual(render_stream.format_compact_duration(45), "0m45s")
        self.assertEqual(render_stream.format_compact_duration(248), "4m08s")
        self.assertEqual(
            render_stream.format_compact_duration(64 * 60 + 21), "1h04m21s"
        )
        self.assertEqual(
            render_stream.format_compact_duration(187 * 60 + 56), "3h07m56s"
        )
        self.assertEqual(
            render_stream.format_compact_duration(86400 + 3 * 3600 + 7 * 60 + 56),
            "1d 3h07m56s",
        )

    def test_format_statusline_exact_layout(self):
        tracker = render_stream.StreamTracker()
        tracker.update(inp=214100, out=195700, cache=15800000, cost=15.27)

        now_ts = 1700000000.0  # fixed timestamp
        run_start_ts = now_ts - (64 * 60 + 21)  # 64m21s -> 1h04m21s
        item_start_ts = now_ts - (4 * 60 + 8)  # 4m08s
        last_act_ts = now_ts - 14  # idle 14s

        top, l1, l2, bot = render_stream.format_statusline_lines(
            now_ts=now_ts,
            run_start_ts=run_start_ts,
            item_start_ts=item_start_ts,
            last_act_ts=last_act_ts,
            current_idx=1,
            total_items=1,
            setid="revgate",
            id6="7nkcgp",
            tracker=tracker,
        )

        self.assertEqual(len(top), len(l1))
        self.assertEqual(len(l1), len(l2))
        self.assertEqual(len(l2), len(bot))
        self.assertTrue(top.startswith("╭") and top.endswith("╮"))
        self.assertTrue(bot.startswith("╰") and bot.endswith("╯"))
        self.assertTrue(l1.startswith("│") and l1.endswith("│"))
        self.assertTrue(l2.startswith("│") and l2.endswith("│"))

        seg1 = [s.strip() for s in l1.split("│")[1:-1]]
        seg2 = [s.strip() for s in l2.split("│")[1:-1]]
        self.assertEqual(len(seg1), 9)
        self.assertEqual(len(seg2), 9)

        # Header line segments
        self.assertEqual(seg1[0], "Time")
        self.assertEqual(seg1[1], "From start")
        self.assertEqual(seg1[2], "set: revgate id6: 7nkcgp")
        self.assertEqual(seg1[3], "Spend")
        self.assertEqual(seg1[4], "Tok")
        self.assertEqual(seg1[5], "Total")
        self.assertEqual(seg1[6], "in")
        self.assertEqual(seg1[7], "out")
        self.assertEqual(seg1[8], "cache")

        # Value line segments
        self.assertRegex(seg2[0], r"^\d{2}:\d{2}:\d{2}$")
        self.assertEqual(seg2[1], "1h04m21s idle: 14s")
        self.assertEqual(seg2[2], "4m08s ██████████ 100% [1/1]")
        self.assertEqual(seg2[3], "$15.27")
        self.assertEqual(seg2[4], "ens")
        self.assertEqual(seg2[5], "16.2m")
        self.assertEqual(seg2[6], "214.1k")
        self.assertEqual(seg2[7], "195.7k")
        self.assertEqual(seg2[8], "15.8m")

    def test_format_statusline_user_example_box_layout(self):
        class MockTracker:
            cost = 6.16
            input_tokens = 119000
            output_tokens = 110700
            cache_tokens = 4500000

        top, l1, l2, bot = render_stream.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0 - (27 * 60 + 48),
            item_start_ts=1700000000.0 - (27 * 60 + 48),
            last_act_ts=1700000000.0 - 8,
            current_idx=1,
            total_items=1,
            setid="wtisoland",
            id6="6knsrx",
            tracker=MockTracker(),
            stall_remaining=9 * 60 + 51,
            progress_source="stdout",
        )

        expected_top = "╭─────────┬────────────────────────────────┬───────────────────────────────┬─────────┬─────┬───────┬──────┬────────┬───────╮"
        expected_l1 = "│Time     │ From start       kill in 9m51s │ set: wtisoland id6: 6knsrx    │ Spend   │ Tok │ Total │   in │    out │ cache │"
        expected_bot = "╰─────────┴────────────────────────────────┴───────────────────────────────┴─────────┴─────┴───────┴──────┴────────┴───────╯"

        self.assertEqual(top, expected_top)
        self.assertEqual(l1, expected_l1)
        self.assertEqual(bot, expected_bot)
        self.assertIn("27m48s idle: 8s (last: stdout)", l2)
        self.assertIn("27m48s ██████████ 100% [1/1]", l2)
        self.assertIn("$6.16", l2)
        self.assertIn("4.7m", l2)
        self.assertIn("119k", l2)
        self.assertIn("110.7k", l2)
        self.assertIn("4.5m", l2)

    def test_format_statusline_colorized(self):
        tracker = render_stream.StreamTracker()
        tracker.update(inp=214100, out=195700, cache=15800000, cost=15.27)
        pal = render_stream.Palette(True)

        now_ts = 1700000000.0
        run_start_ts = now_ts - (64 * 60 + 21)
        item_start_ts = now_ts - (4 * 60 + 8)
        last_act_ts = now_ts - 14

        top, l1, l2, bot = render_stream.format_statusline_lines(
            now_ts=now_ts,
            run_start_ts=run_start_ts,
            item_start_ts=item_start_ts,
            last_act_ts=last_act_ts,
            current_idx=1,
            total_items=1,
            setid="revgate",
            id6="7nkcgp",
            tracker=tracker,
            pal=pal,
        )

        self.assertIn("\033[1;38;5;117m", l2)  # Bold sky light blue
        self.assertNotIn("\033[48;", l1)  # No background
        self.assertNotIn("\033[48;", l2)

        # Stripping ANSI recovers clean content
        s_top = render_stream._strip_ansi(top)
        s1 = render_stream._strip_ansi(l1)
        s2 = render_stream._strip_ansi(l2)
        s_bot = render_stream._strip_ansi(bot)
        self.assertEqual(len(s_top), len(s1))
        self.assertEqual(len(s1), len(s2))
        self.assertEqual(len(s2), len(s_bot))
        self.assertIn("Time", s1)
        self.assertIn("set: revgate id6: 7nkcgp", s1)
        self.assertIn("1h04m21s idle: 14s", s2)
        self.assertIn("4m08s ██████████ 100% [1/1]", s2)
        self.assertIn("$15.27", s2)

    def test_statusline_write_event_non_tty(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(pal, buf, interval=0)
        with st:
            st.write_event("  \u2022 Reading the plan.")
        self.assertEqual(buf.getvalue(), "  \u2022 Reading the plan.\n")

    def test_statusline_update_item_and_touch(self):
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(pal, buf, interval=0)
        st.touch()
        st.update_item(2, 10, setid="myset", id6="id6abc")
        line = st.render_line()
        self.assertIn("myset", line)
        self.assertIn("id6abc", line)
        self.assertIn("[2/10]", line)


class SingleDefinitionTests(unittest.TestCase):
    """The render layer has a SINGLE definition in render_stream; oc_runipd only re-exports."""

    def test_names_are_the_same_objects(self):
        # Identity: the driver's names ARE the render_stream objects (no inline copy).
        self.assertIs(driver.Palette, render_stream.Palette)
        self.assertIs(driver.StreamTracker, render_stream.StreamTracker)
        self.assertIs(driver.format_tokens, render_stream.format_tokens)
        self.assertIs(driver.format_compact_tokens, render_stream.format_compact_tokens)
        self.assertIs(driver.format_progress_bar, render_stream.format_progress_bar)
        self.assertIs(driver.format_statusline, render_stream.format_statusline)
        self.assertIs(
            driver.format_statusline_lines, render_stream.format_statusline_lines
        )
        self.assertIs(driver.Statusline, render_stream.Statusline)
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
            render_stream.StreamTracker,
            render_stream.format_tokens,
            render_stream.format_compact_tokens,
            render_stream.format_progress_bar,
            render_stream.format_statusline,
            render_stream.Statusline,
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
        self.assertNotIn("class StreamTracker:", src)
        self.assertNotIn("class Statusline:", src)
        self.assertNotIn("def format_tokens(", src)
        self.assertNotIn("def format_statusline(", src)
        self.assertNotIn("class Heartbeat:", src)
        self.assertNotIn("def render_event(", src)
        self.assertNotIn("def _one_line(", src)
        self.assertNotIn("def _strip_ansi(", src)
        # It must import them from the shared module instead.
        self.assertIn("from agent_workflows.render_stream import", src)

    def test_agy_runipd_has_no_inline_heartbeat_copy(self):
        # stallfp kaga7s: agy carried a byte-identical INLINE `class Heartbeat:`, so a
        # display fix in render_stream silently did NOT reach `aw agy run`. Guard both
        # drivers, not just oc, or the duplicate can come back unnoticed.
        src = inspect.getsource(agy_driver)
        self.assertNotIn("class Heartbeat:", src)
        self.assertIn("from agent_workflows.render_stream import", src)

    def test_heartbeat_is_the_same_object_in_both_drivers(self):
        self.assertIs(agy_driver.Heartbeat, render_stream.Heartbeat)
        self.assertIs(driver.Heartbeat, render_stream.Heartbeat)

    def test_exactly_one_heartbeat_definition_in_the_package(self):
        # Source-level: only render_stream may DEFINE it, anywhere in the package.
        import pathlib

        pkg = pathlib.Path(render_stream.__file__).parent
        definers = sorted(
            p.name
            for p in pkg.glob("*.py")
            if "class Heartbeat:" in p.read_text(encoding="utf-8")
        )
        self.assertEqual(definers, ["render_stream.py"])


if __name__ == "__main__":
    unittest.main()

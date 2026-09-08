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
from unittest import mock

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
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(line, "\u25c8 think:".ljust(pad) + "Reading the plan.")
        self.assertNotIn("\033[", line)

    def test_tool_use_renders_tool_and_title(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"bash",'
            '"state":{"status":"completed","title":"git status --short"}}}',
            self.plain,
        )
        assert line is not None
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(
            line,
            "\u276f bash:".ljust(pad) + "git status --short",
        )

    def test_tool_use_derives_title_from_input_when_missing(self):
        # `read` is suppressed at the default tier (E-04), so this asserts the title fallback at the
        # verbose tier where the event is visible at all.
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"read",'
            '"state":{"status":"running","input":{"path":"a.py"}}}}',
            self.plain,
            verbosity=1,
        )
        assert line is not None
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(
            line,
            "\u25c0 read:".ljust(pad) + '{"path": "a.py"}',
        )

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


_OBSERVED_SYSTEM_PROTOCOL_VARIANTS = [
    "[System: Empty message content sandbox to satisfy protocol]",
    "[System: Empty message content sanitised to assistant protocol]",
    "[System: Empty message content sanitised to justify protocol]",
    "[System: Empty message content sanitised to satisfy parameter]",
    "[System: Empty message content sanitised to satisfy parity]",
    "[System: Empty message content sanitised to satisfy partial protocol]",
    "[System: Empty message content sanitised to satisfy platform protocol]",
    "[System: Empty message content sanitised to satisfy polocol]",
    "[System: Empty message content sanitised to satisfy portico protocol]",
    "[System: Empty message content sanitised to satisfy portocol]",
    "[System: Empty message content sanitised to satisfy propecol]",
    "[System: Empty message content sanitised to satisfy propriety]",
    "[System: Empty message content sanitised to satisfy prot[System: Empty message content sanitised to satisfy protocol]",
    "[System: Empty message content sanitised to satisfy protocol]",
    "[System: Empty message description sanitised to satisfy protocol]",
    "[System: Empty method content sanitised]",
    "[System: Empty module content sanitised]",
    "[System: Empty money content sanitised to satisfy protocol]",
    "[System: Empty name sanitised to satisfy protocol]",
    "[System: Empty number content sanitised to satisfy protocol]",
]


class SystemProtocolSuppressionTests(unittest.TestCase):
    """Tests for synthetic platform protocol placeholder suppression (plan eqzd0h)."""

    def setUp(self) -> None:
        self.pal = render_stream.Palette(False)
        self.pad = render_stream.event_prefix_pad(True)
        self.think_prefix = render_stream.EVENT_PREFIXES["think"].ljust(self.pad)

    def test_all_20_observed_variants_reduce_to_empty(self):
        self.assertEqual(len(_OBSERVED_SYSTEM_PROTOCOL_VARIANTS), 20)
        for variant in _OBSERVED_SYSTEM_PROTOCOL_VARIANTS:
            with self.subTest(variant=variant):
                stripped = render_stream.strip_system_protocol_prefix(variant)
                self.assertEqual(stripped, "")

    def test_chained_placeholder_reduces_to_empty(self):
        chained = (
            "[System: Empty message content sanitised to satisfy protocol]"
            "[System: Empty message content sanitised to satisfy protocol]"
        )
        self.assertEqual(render_stream.strip_system_protocol_prefix(chained), "")

    def test_placeholder_only_text_events_render_none(self):
        for variant in _OBSERVED_SYSTEM_PROTOCOL_VARIANTS:
            with self.subTest(variant=variant):
                evt = json.dumps(
                    {"type": "text", "part": {"type": "text", "text": variant}}
                )
                self.assertIsNone(render_stream.render_event(evt, self.pal))

    def test_leading_placeholder_with_real_text_renders_text_behind_think_prefix(self):
        raw_text = (
            "[System: Empty message content sanitised to satisfy protocol]\n\n"
            "Now let me look at the key structural question."
        )
        evt = json.dumps({"type": "text", "part": {"type": "text", "text": raw_text}})
        rendered = render_stream.render_event(evt, self.pal)
        self.assertEqual(
            rendered,
            f"{self.think_prefix}Now let me look at the key structural question.",
        )

    def test_placeholder_quoted_mid_sentence_is_preserved_verbatim(self):
        raw_text = "We observed [System: Empty message content sanitised to satisfy protocol] in logs."
        evt = json.dumps({"type": "text", "part": {"type": "text", "text": raw_text}})
        rendered = render_stream.render_event(evt, self.pal)
        self.assertEqual(
            rendered,
            f"{self.think_prefix}{raw_text}",
        )

    def test_truncated_placeholder_without_closing_bracket_is_preserved(self):
        raw_text = "[System: Empty message content sanitised"
        evt = json.dumps({"type": "text", "part": {"type": "text", "text": raw_text}})
        rendered = render_stream.render_event(evt, self.pal)
        self.assertEqual(
            rendered,
            f"{self.think_prefix}{raw_text}",
        )

    def test_placeholder_only_non_json_line_returns_none(self):
        for variant in _OBSERVED_SYSTEM_PROTOCOL_VARIANTS:
            with self.subTest(variant=variant):
                self.assertIsNone(render_stream.render_event(variant, self.pal))

    def test_non_placeholder_non_json_line_renders_dimmed(self):
        line = "regular unparseable log line"
        rendered = render_stream.render_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn(line, rendered)


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
        # streamfmt (mm6wuz) E-07: RE-PINNED for the aligned format. The expected lines are built
        # from `event_prefix_pad()` rather than written with hand-counted spaces, so a pad change
        # cannot be "fixed" by silently re-counting the literal; a real format regression still
        # fails, because the prefix strings and the payloads are literals.
        pad = render_stream.event_prefix_pad(True)
        expected = "\n".join(
            [
                "\u25c8 think:".ljust(pad) + "Reading the plan.",
                "\u276f bash:".ljust(pad) + "git status",
                "\u276f bash:".ljust(pad) + "git status",
                "\u270e edit:".ljust(pad) + "patch failed",
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


def _code_text(obj) -> str:
    """The SOURCE of ``obj`` with comments and docstrings removed.

    A plain `inspect.getsource` substring check cannot tell code from a comment that EXPLAINS why
    the code avoids something, so the honest structural assertions below would fail on their own
    documentation. `ast.unparse` of the parsed tree drops comments outright, and the docstring is
    stripped explicitly, leaving only what executes.
    """
    import ast
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(obj)))
    node = tree.body[0]
    body = getattr(node, "body", None)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    ):
        if isinstance(body[0].value.value, str):
            body.pop(0)
    return ast.unparse(tree)


def _tool_event(tool: str, status: str = "completed", **state) -> str:
    """Build ONE `tool_use` event line INLINE, as a literal.

    HERMETICITY (the plan's `Required tests` rule): every fixture in this module is constructed
    here from literals. Nothing reads `.aw/records/runs/`, which is gitignored, absent in CI and in
    the runner's own isolated worktree, and full of absolute maintainer paths.
    """
    payload: dict[str, object] = {"status": status}
    payload.update(state)
    return json.dumps({"type": "tool_use", "part": {"tool": tool, "state": payload}})


class EventPrefixAlignmentTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-01/E-09/E-10: the derived pad and the alignment INVARIANT.

    The invariant, not the current value, is the point. A test asserting `PAD == 12` passes for the
    wrong reason the moment a longer prefix is added: the literal is edited to match the code and
    the misalignment ships. So the assertions below check the DERIVATION and check EVERY prefix,
    with color both on and off, in both width policies.
    """

    def test_the_pad_is_derived_from_the_table_not_hardcoded(self):
        for use_unicode in (True, False):
            with self.subTest(use_unicode=use_unicode):
                table = render_stream.event_prefix_table(use_unicode)
                self.assertEqual(
                    render_stream.event_prefix_pad(use_unicode),
                    max(len(p) for p in table.values()) + 1,
                )
        # And the module constant is the derived value for the default table, not a literal.
        self.assertEqual(
            render_stream.EVENT_PREFIX_PAD, render_stream.event_prefix_pad(True)
        )
        # The longest labels today are 8 codepoints, hence a pad of 9. Asserted as
        # a MEASUREMENT of the table, so adding a longer label moves both sides together.
        self.assertEqual(max(len(p) for p in render_stream.EVENT_PREFIXES.values()), 8)
        self.assertEqual(render_stream.EVENT_PREFIX_PAD, 9)

    def test_the_pad_follows_the_table_when_the_table_changes(self):
        """The derivation is LIVE: lengthen the table and the pad must follow."""
        longer = dict(render_stream.EVENT_PREFIXES)
        longer["orchestrate"] = "\u25c8 orchestrate-a-set:"
        with mock.patch.object(render_stream, "EVENT_PREFIXES", longer):
            self.assertEqual(
                render_stream.event_prefix_pad(True),
                len("\u25c8 orchestrate-a-set:") + 1,
            )

    def test_every_prefix_pads_to_the_derived_column_with_color_on_and_off(self):
        """E-10: the invariant, named per prefix, in both width policies.

        Padding is computed on the UNCOLORED text, so a colored prefix must strip back to exactly
        the pad width. Asserting only the plain case would let an ANSI-length bug through, which is
        the specific failure the plan's conventions section names.
        """
        for use_unicode in (True, False):
            table = render_stream.event_prefix_table(use_unicode)
            pad = render_stream.event_prefix_pad(use_unicode)
            for kind in table:
                for color in (False, True):
                    with self.subTest(kind=kind, unicode=use_unicode, color=color):
                        rendered = render_stream.format_event_prefix(
                            kind, render_stream.Palette(color), use_unicode
                        )
                        self.assertEqual(
                            len(render_stream._strip_ansi(rendered)),
                            pad,
                            f"prefix {kind!r} does not pad to the derived column {pad}",
                        )

    def test_an_unmapped_tool_still_pads_to_the_derived_column(self):
        rendered = render_stream.format_event_prefix(
            "newtool", render_stream.Palette(False)
        )
        self.assertEqual(
            len(render_stream._strip_ansi(rendered)),
            render_stream.event_prefix_pad(True),
        )
        self.assertEqual(rendered, "\u2022 tool:  ")

    def test_unmapped_tool_renders_with_tool_prefix_and_names_tool(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"ask_question",'
            '"state":{"status":"completed","title":"Pick branch"}}}',
            render_stream.Palette(False),
        )
        assert line is not None
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(
            line,
            "\u2022 tool:".ljust(pad) + "ask_question: Pick branch",
        )

    def test_task_renders_with_child_prefix(self):
        line = render_stream.render_event(
            '{"type":"tool_use","part":{"tool":"task",'
            '"state":{"status":"completed","title":"explore the codebase"}}}',
            render_stream.Palette(False),
        )
        assert line is not None
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(
            line,
            "\u21b3 child:".ljust(pad) + "explore the codebase",
        )

    def test_the_invariant_BITES_when_a_longer_prefix_is_added_without_the_pad(self):
        """Proof the guard is not vacuous.

        A test that only ever PASSES says nothing about a future regression, so this one injects the
        exact defect the invariant exists to catch (a prefix longer than the pad it is padded to)
        and shows the check FAILS and NAMES the offender. The stale pad is simulated rather than
        monkeypatched into `format_event_prefix`, because the padding is derived at call time; the
        assertion below is the same comparison `test_every_prefix_pads_to_the_derived_column...`
        makes.
        """
        longer = dict(render_stream.EVENT_PREFIXES)
        longer["verylong"] = "\u25c8 a-much-longer-label:"
        stale_pad = render_stream.EVENT_PREFIX_PAD
        offenders = [
            kind
            for kind, label in longer.items()
            if len(label.ljust(stale_pad)) != stale_pad
        ]
        self.assertEqual(
            offenders,
            ["verylong"],
            "a longer prefix padded to the stale width must be detectable, naming the offender",
        )
        # And with the pad DERIVED from the grown table, no prefix offends: the derivation is the fix.
        with mock.patch.object(render_stream, "EVENT_PREFIXES", longer):
            fresh_pad = render_stream.event_prefix_pad(True)
            self.assertGreater(fresh_pad, stale_pad)
            self.assertEqual(
                [
                    kind
                    for kind, label in longer.items()
                    if len(label.ljust(fresh_pad)) != fresh_pad
                ],
                [],
            )

    def test_the_five_ambiguous_glyphs_are_substituted_in_the_narrow_table(self):
        """E-09: only the five East-Asian-Ambiguous glyphs are swapped, and per-key length holds."""
        import unicodedata

        ambiguous = {
            kind
            for kind, label in render_stream.EVENT_PREFIXES.items()
            if unicodedata.east_asian_width(label[0]) == "A"
        }
        self.assertEqual(ambiguous, {"read", "write", "diag", "think", "tool"})
        for kind, label in render_stream.EVENT_PREFIXES_ASCII.items():
            with self.subTest(kind=kind):
                # `"N"` (Narrow) or `"Na"` (Narrow, the ASCII-range class) both render single-width;
                # what must NOT appear is `"A"`, `"W"` or `"F"`.
                self.assertIn(unicodedata.east_asian_width(label[0]), ("N", "Na"))
                # 1:1 codepoint swap, so both tables derive the SAME pad.
                self.assertEqual(len(label), len(render_stream.EVENT_PREFIXES[kind]))
        self.assertEqual(
            render_stream.event_prefix_pad(False), render_stream.event_prefix_pad(True)
        )

    def test_child_and_tool_prefixes_present_and_aligned(self):
        self.assertIn("child", render_stream.EVENT_PREFIXES)
        self.assertIn("child", render_stream.EVENT_PREFIXES_ASCII)
        self.assertEqual(render_stream.EVENT_PREFIXES["child"], "\u21b3 child:")
        self.assertEqual(render_stream.EVENT_PREFIXES_ASCII["child"], "\u21b3 child:")
        self.assertIn("tool", render_stream.EVENT_PREFIXES)
        self.assertIn("tool", render_stream.EVENT_PREFIXES_ASCII)
        self.assertEqual(render_stream.EVENT_PREFIXES["tool"], "\u2022 tool:")
        self.assertEqual(render_stream.EVENT_PREFIXES_ASCII["tool"], "- tool:")
        self.assertNotIn("reason", render_stream.EVENT_PREFIXES)
        self.assertNotIn("subagent", render_stream.EVENT_PREFIXES)
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(pad, 9)

    def test_think_prefix_present_and_aligned(self):
        self.assertIn("think", render_stream.EVENT_PREFIXES)
        self.assertIn("think", render_stream.EVENT_PREFIXES_ASCII)
        self.assertEqual(render_stream.EVENT_PREFIXES["think"], "\u25c8 think:")
        self.assertEqual(render_stream.EVENT_PREFIXES_ASCII["think"], "~ think:")
        pad = render_stream.event_prefix_pad(True)
        self.assertEqual(len("\u25c8 think:".ljust(pad)), pad)

    def test_the_width_policy_limitation_is_documented_in_code(self):
        """The plan's FIRST warning: the false 'all glyphs are single-width' claim must not return."""
        import pathlib

        src = pathlib.Path(render_stream.__file__).read_text(encoding="utf-8")
        self.assertIn("AMBIGUOUS", src)
        self.assertIn("east_asian_width", src)
        self.assertIn("EVENT_PREFIXES_ASCII", src)

    def test_the_narrow_table_is_selected_by_use_unicode_matching_the_statusline(self):
        """E-09: the SAME parameter spelling `format_statusline_lines` already uses."""
        self.assertIn(
            "use_unicode",
            inspect.signature(render_stream.format_statusline_lines).parameters,
        )
        for fn in (
            render_stream.event_prefix_table,
            render_stream.event_prefix_pad,
            render_stream.format_event_prefix,
            render_stream.render_event,
        ):
            with self.subTest(fn=fn.__name__):
                self.assertIn("use_unicode", inspect.signature(fn).parameters)


class TodoTransitionTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-02: `todowrite` transitions read from `metadata.todos`."""

    def setUp(self):
        self.plain = render_stream.Palette(False)
        self.pad = render_stream.event_prefix_pad(True)

    def _render(self, todos, tracker, source="metadata"):
        if source == "metadata":
            event = _tool_event("todowrite", metadata={"todos": todos})
        else:
            event = _tool_event("todowrite", input={"todos": todos})
        line = render_stream.render_event(event, self.plain, tracker=tracker)
        assert line is not None
        return line

    def _payload(self, line):
        head = "\u2611 todo:".ljust(self.pad)
        self.assertTrue(line.startswith(head), line)
        return line[len(head) :]

    def test_source_is_metadata_todos_not_the_title(self):
        tracker = render_stream.StreamTracker()
        line = render_stream.render_event(
            _tool_event(
                "todowrite",
                title="4 todos",
                metadata={
                    "todos": [
                        {"content": "A", "status": "in_progress", "priority": "high"}
                    ]
                },
            ),
            self.plain,
            tracker=tracker,
        )
        assert line is not None
        # The measured `title` value is only ever "<N> todos" and must NOT be what renders.
        self.assertNotIn("4 todos", line)
        self.assertIn("initialized 1 tasks", line)

    def test_input_todos_is_the_fallback_when_metadata_is_absent(self):
        tracker = render_stream.StreamTracker()
        line = self._render(
            [{"content": "A", "status": "pending", "priority": "high"}],
            tracker,
            source="input",
        )
        self.assertEqual(
            self._payload(line), "initialized 1 tasks (0 active, 1 pending)"
        )

    def test_initialization(self):
        tracker = render_stream.StreamTracker()
        line = self._render(
            [
                {"content": "A", "status": "in_progress", "priority": "high"},
                {"content": "B", "status": "pending", "priority": "low"},
                {"content": "C", "status": "pending", "priority": "low"},
            ],
            tracker,
        )
        self.assertEqual(
            self._payload(line), "initialized 3 tasks (1 active, 2 pending)"
        )

    def test_exactly_one_active(self):
        tracker = render_stream.StreamTracker()
        self._render(
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        line = self._render(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "in_progress"},
            ],
            tracker,
        )
        self.assertEqual(self._payload(line), '[1/2 done]: completed "A" -> active "B"')

    def test_zero_active_renders_no_active_task(self):
        """Measured: 169 of 984 events carry ZERO in_progress items."""
        tracker = render_stream.StreamTracker()
        self._render(
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        line = self._render(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        self.assertEqual(
            self._payload(line), '[1/2 done]: completed "A" -> no active task'
        )

    def test_multiple_active_are_all_named(self):
        """Measured: 16 of 984 events carry TWO OR MORE in_progress items."""
        tracker = render_stream.StreamTracker()
        self._render(
            [
                {"content": "A", "status": "pending"},
                {"content": "B", "status": "pending"},
                {"content": "C", "status": "pending"},
            ],
            tracker,
        )
        line = self._render(
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "in_progress"},
                {"content": "C", "status": "pending"},
            ],
            tracker,
        )
        self.assertEqual(self._payload(line), '[0/3 done]: active "A", "B"')

    def test_cancelled_is_not_counted_as_done(self):
        """Measured: `cancelled` occurs 4 times and is NOT an accomplishment."""
        tracker = render_stream.StreamTracker()
        self._render(
            [
                {"content": "A", "status": "pending"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        line = self._render(
            [
                {"content": "A", "status": "cancelled"},
                {"content": "B", "status": "in_progress"},
            ],
            tracker,
        )
        payload = self._payload(line)
        self.assertEqual(payload, '[0/2 done]: active "B"')
        self.assertNotIn("all 2 tasks completed", payload)

    def test_all_done(self):
        tracker = render_stream.StreamTracker()
        self._render(
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        line = self._render(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "completed"},
            ],
            tracker,
        )
        self.assertEqual(self._payload(line), "all 2 tasks completed")

    def test_a_cancelled_item_in_an_initial_list_is_reported(self):
        tracker = render_stream.StreamTracker()
        line = self._render(
            [
                {"content": "A", "status": "cancelled"},
                {"content": "B", "status": "pending"},
            ],
            tracker,
        )
        self.assertEqual(
            self._payload(line),
            "initialized 2 tasks (0 active, 1 pending, 1 cancelled)",
        )

    def test_todo_state_does_not_leak_across_queue_items(self):
        """F-15: one tracker serves the WHOLE run, so item 2 must not diff against item 1."""
        tracker = render_stream.StreamTracker()
        # Item 1 finishes with a full list.
        self._render(
            [
                {"content": "item1-A", "status": "in_progress"},
                {"content": "item1-B", "status": "pending"},
            ],
            tracker,
        )
        leaked = self._render(
            [{"content": "item2-A", "status": "in_progress"}], tracker
        )
        # Without a reset, item 2's first event renders a TRANSITION diffed against item 1.
        self.assertNotIn("initialized", self._payload(leaked))
        # With the reset the driver performs at turn start, it renders an initialization.
        tracker.begin_turn()
        fresh = self._render([{"content": "item2-A", "status": "in_progress"}], tracker)
        self.assertEqual(
            self._payload(fresh), "initialized 1 tasks (1 active, 0 pending)"
        )

    def test_begin_turn_resets_only_per_turn_state(self):
        tracker = render_stream.StreamTracker()
        tracker.update(inp=10, out=5, cache=2, cost=1.5)
        tracker.note_modified_file("a.py")
        tracker.todos = [{"content": "A", "status": "pending"}]
        tracker.begin_turn()
        self.assertEqual(tracker.todos, [])
        self.assertEqual(tracker.input_tokens, 10)
        self.assertEqual(tracker.modified_files, {"a.py"})

    def test_a_snapshot_is_rendered_when_no_tracker_is_supplied(self):
        line = render_stream.render_event(
            _tool_event(
                "todowrite",
                metadata={
                    "todos": [
                        {"content": "A", "status": "completed"},
                        {"content": "B", "status": "in_progress"},
                    ]
                },
            ),
            self.plain,
        )
        assert line is not None
        self.assertEqual(self._payload(line), "2 tasks (1 done, 1 active)")

    def test_the_driver_resets_the_tracker_at_turn_start(self):
        """The reset must be CALLED by the runner, not merely available on the tracker."""
        import pathlib

        src = pathlib.Path(driver.__file__).read_text(encoding="utf-8")
        self.assertIn("tracker.begin_turn()", src)


class EditWritePayloadTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-03: real `edit` diff stats and content-derived `write` line counts."""

    def setUp(self):
        self.plain = render_stream.Palette(False)
        self.pad = render_stream.event_prefix_pad(True)

    def _payload(self, line, kind):
        head = render_stream.EVENT_PREFIXES[kind].ljust(self.pad)
        self.assertTrue(line.startswith(head), line)
        return line[len(head) :]

    def test_edit_renders_int_additions_and_deletions(self):
        line = render_stream.render_event(
            _tool_event(
                "edit",
                metadata={
                    "filediff": {
                        "file": "/repo/agent_workflows/x.py",
                        "patch": "@@ -1 +1 @@\n-a\n+b",
                        "additions": 12,
                        "deletions": 3,
                    }
                },
            ),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        self.assertEqual(self._payload(line, "edit"), "agent_workflows/x.py (+12, -3)")

    def test_write_derives_the_line_count_from_input_content(self):
        line = render_stream.render_event(
            _tool_event(
                "write",
                metadata={"filepath": "/repo/new.py", "exists": False},
                input={"content": "a\nb\nc\n"},
            ),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        self.assertEqual(self._payload(line, "write"), "new.py (new file, 3 lines)")

    def test_write_with_exists_true_says_overwrote(self):
        line = render_stream.render_event(
            _tool_event(
                "write",
                metadata={"filepath": "/repo/old.py", "exists": True},
                input={"content": "x\ny\n"},
            ),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        self.assertEqual(self._payload(line, "write"), "old.py (overwrote, 2 lines)")

    def test_write_without_content_degrades_to_no_count(self):
        """Rather than raising or printing a confidently wrong number."""
        line = render_stream.render_event(
            _tool_event("write", metadata={"filepath": "/repo/x.py", "exists": False}),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        payload = self._payload(line, "write")
        self.assertEqual(payload, "x.py (new file)")
        self.assertNotIn("lines", payload)

    def test_a_write_whose_metadata_omits_filediff_entirely_still_renders(self):
        """F-8: `write` has NO `filediff` in 480 of 480 measured events."""
        state = {
            "status": "completed",
            "metadata": {
                "diagnostics": {},
                "filepath": "/repo/x.py",
                "exists": False,
                "truncated": False,
            },
            "input": {"content": "one\n"},
        }
        self.assertNotIn("filediff", state["metadata"])
        line = render_stream.render_event(
            json.dumps({"type": "tool_use", "part": {"tool": "write", "state": state}}),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        self.assertEqual(self._payload(line, "write"), "x.py (new file, 1 lines)")

    def test_no_code_path_reads_filediff_off_a_write(self):
        """Structural: no EXECUTABLE line in the write formatter may read `filediff` (F-8).

        Asserted against comment-stripped source, so the formatter's own docstring EXPLAINING that
        `write` has no `filediff` does not trip the guard.
        """
        self.assertNotIn("filediff", _code_text(render_stream.format_write_payload))

    def test_a_path_outside_the_repo_is_left_absolute_rather_than_truncated(self):
        line = render_stream.render_event(
            _tool_event(
                "edit",
                metadata={
                    "filediff": {
                        "file": "/elsewhere/z.py",
                        "patch": "",
                        "additions": 1,
                        "deletions": 0,
                    }
                },
            ),
            self.plain,
            repo_root="/repo",
        )
        assert line is not None
        self.assertIn("/elsewhere/z.py", line)

    def test_modified_files_accumulates_edits_and_writes(self):
        tracker = render_stream.StreamTracker()
        render_stream.render_event(
            _tool_event(
                "edit",
                metadata={
                    "filediff": {
                        "file": "/repo/a.py",
                        "patch": "",
                        "additions": 1,
                        "deletions": 1,
                    }
                },
            ),
            self.plain,
            tracker=tracker,
            repo_root="/repo",
        )
        render_stream.render_event(
            _tool_event(
                "write",
                metadata={"filepath": "/repo/b.py", "exists": False},
                input={"content": "x\n"},
            ),
            self.plain,
            tracker=tracker,
            repo_root="/repo",
        )
        self.assertEqual(tracker.modified_files, {"a.py", "b.py"})


class ModifiedFilesConsumerTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-08: `modified_files` has a NAMED READER, or it should not exist."""

    _STATE = {
        "run_id": "run-files-touched",
        "queue": [
            {
                "position": 1,
                "id6": "aaaaaa",
                "setid": "s",
                "action": "execute",
                "status": "executed",
                "attempts": [],
            }
        ],
    }

    def test_the_summary_table_reports_the_files_touched_count(self):
        tracker = render_stream.StreamTracker()
        tracker.note_modified_file("agent_workflows/render_stream.py")
        tracker.note_modified_file("tests/test_render_stream.py")
        out = render_stream.render_run_summary_table(
            self._STATE, tracker=tracker, pal=render_stream.Palette(False)
        )
        self.assertIn("Files touched: 2 files", out)

    def test_one_file_is_singular(self):
        tracker = render_stream.StreamTracker()
        tracker.note_modified_file("only.py")
        out = render_stream.render_run_summary_table(
            self._STATE, tracker=tracker, pal=render_stream.Palette(False)
        )
        self.assertIn("Files touched: 1 file", out)

    def test_no_touched_files_renders_nothing(self):
        """A run with no edits stays byte-identical to the pre-change table."""
        out = render_stream.render_run_summary_table(
            self._STATE,
            tracker=render_stream.StreamTracker(),
            pal=render_stream.Palette(False),
        )
        self.assertNotIn("Files touched", out)

    def test_the_accumulation_scope_is_documented_as_run_scoped(self):
        doc = render_stream.StreamTracker.__doc__ or ""
        self.assertIn("RUN-SCOPED", doc)
        self.assertIn("modified_files", doc)


class VerbosityTierTests(unittest.TestCase):
    """streamfmt (mm6wuz) E-04: what each tier renders, and what it suppresses."""

    def setUp(self):
        self.plain = render_stream.Palette(False)

    def _events(self):
        return {
            "bash": _tool_event("bash", title="git status"),
            "edit": _tool_event(
                "edit",
                metadata={
                    "filediff": {
                        "file": "/repo/a.py",
                        "patch": "@@ -1 +1 @@\n-a\n+b",
                        "additions": 1,
                        "deletions": 1,
                    }
                },
            ),
            "write": _tool_event(
                "write",
                metadata={"filepath": "/repo/b.py", "exists": False},
                input={"content": "x\n"},
            ),
            "todowrite": _tool_event(
                "todowrite",
                metadata={"todos": [{"content": "A", "status": "in_progress"}]},
            ),
            "read": _tool_event(
                "read",
                metadata={
                    "display": {
                        "path": "/repo/c.py",
                        "lineStart": 1,
                        "lineEnd": 40,
                        "totalLines": 400,
                    }
                },
            ),
            "grep": _tool_event(
                "grep", metadata={"matches": 7}, input={"pattern": "foo"}
            ),
            "glob": _tool_event(
                "glob", metadata={"count": 3}, input={"pattern": "*.py"}
            ),
            "task": _tool_event("task", title="explore the codebase"),
            "text": '{"type":"text","part":{"text":"Narrating."}}',
            "error": '{"type":"error","error":{"name":"UnknownError",'
            '"data":{"message":"The operation timed out."}}}',
        }

    def test_the_per_tier_matrix(self):
        expected = {
            0: {
                "bash": True,
                "edit": True,
                "write": True,
                "todowrite": True,
                "read": False,
                "grep": False,
                "glob": False,
                "task": True,
                "text": True,
                "error": True,
            },
            1: {k: True for k in self._events()},
            2: {k: True for k in self._events()},
        }
        for level, rows in expected.items():
            for name, should_render in rows.items():
                with self.subTest(level=level, event=name):
                    rendered = render_stream.render_event(
                        self._events()[name],
                        self.plain,
                        tracker=render_stream.StreamTracker(),
                        verbosity=level,
                        repo_root="/repo",
                    )
                    self.assertEqual(
                        rendered is not None,
                        should_render,
                        f"level {level}, {name}: rendered={rendered!r}",
                    )

    def test_error_renders_at_every_tier_including_zero(self):
        """F-13: this branch did not exist, so a real error event rendered as None."""
        for level in (0, 1, 2):
            with self.subTest(level=level):
                line = render_stream.render_event(
                    self._events()["error"], self.plain, verbosity=level
                )
                assert line is not None
                self.assertIn("UnknownError", line)
                self.assertIn("The operation timed out.", line)

    def test_verbose_read_carries_a_line_range_and_no_byte_size(self):
        """F-10: there is NO byte size in a read payload, so the tier shows lines."""
        line = render_stream.render_event(
            self._events()["read"], self.plain, verbosity=1, repo_root="/repo"
        )
        assert line is not None
        self.assertIn("c.py (lines 1-40 of 400)", line)
        for forbidden in ("bytes", "byteSize", "KB", " B)"):
            self.assertNotIn(forbidden, line)

    def test_verbose_read_falls_back_to_input_offset_and_limit(self):
        line = render_stream.render_event(
            _tool_event(
                "read", input={"filePath": "/repo/d.py", "offset": 10, "limit": 20}
            ),
            self.plain,
            verbosity=1,
            repo_root="/repo",
        )
        assert line is not None
        self.assertIn("d.py (lines 10-30)", line)

    def test_grep_reads_matches_and_glob_reads_count(self):
        """F-10: the two tools use DIFFERENT field names; one lookup would miss one."""
        grep = render_stream.render_event(
            self._events()["grep"], self.plain, verbosity=1
        )
        glob = render_stream.render_event(
            self._events()["glob"], self.plain, verbosity=1
        )
        assert grep is not None and glob is not None
        self.assertIn("grep foo (7 hits)", grep)
        self.assertIn("glob *.py (3 hits)", glob)

    def test_debug_tier_surfaces_diff_hunks(self):
        line = render_stream.render_event(
            self._events()["edit"], self.plain, verbosity=2, repo_root="/repo"
        )
        assert line is not None
        self.assertIn("@@ -1 +1 @@", line)
        self.assertIn("+b", line)
        # And NOT at the lower tiers.
        for level in (0, 1):
            lower = render_stream.render_event(
                self._events()["edit"], self.plain, verbosity=level, repo_root="/repo"
            )
            assert lower is not None
            self.assertNotIn("@@", lower)

    def test_debug_tier_surfaces_diagnostics(self):
        event = _tool_event(
            "edit",
            metadata={
                "filediff": {
                    "file": "/repo/a.py",
                    "patch": "",
                    "additions": 1,
                    "deletions": 0,
                },
                "diagnostics": {"/repo/a.py": [{"message": "unused import"}]},
            },
        )
        line = render_stream.render_event(
            event, self.plain, verbosity=2, repo_root="/repo"
        )
        assert line is not None
        self.assertIn("unused import", line)
        default_tier = render_stream.render_event(
            event, self.plain, verbosity=0, repo_root="/repo"
        )
        assert default_tier is not None
        self.assertNotIn("unused import", default_tier)

    def test_quiet_is_owned_by_the_call_site_not_by_a_renderer_level(self):
        """The renderer must not grow a second suppression path for `quiet`.

        `oc_runipd`'s stream loop branches `raw`/`clean` and simply DOES NOT CALL `render_event`
        for `quiet`, so `quiet` is a call-site decision. A `quiet` string inside `render_event`
        would mean the policy had two owners.
        """
        self.assertNotIn("quiet", _code_text(render_stream.render_event))
        # And the renderer's docstring STATES which layer owns it, so the next reader does not
        # "fix" the omission by adding the branch.
        self.assertIn("quiet", render_stream.render_event.__doc__ or "")
        driver_src = _code_text(driver.run_opencode)
        self.assertIn("'clean'", driver_src)
        self.assertNotIn("'quiet'", driver_src)

    def test_reason_is_retired_and_think_is_the_sole_thought_prefix(self):
        """streamfx (xs19dk) E-01: reason is retired into think; think is the canonical prefix."""
        self.assertNotIn("reason", render_stream.EVENT_PREFIXES)
        self.assertIn("think", render_stream.EVENT_PREFIXES)


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
            render_stream.format_progress_bar(0, 0), "0/0  [          ]   0%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(0, 5), "0/5  [          ]   0%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(4, 5), "4/5  [████████  ]  80%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(5, 5), "5/5  [██████████] 100%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(0, 80), " 0/80  [          ]   0%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(1, 80), " 1/80  [▏         ]   1%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(40, 80), "40/80  [█████     ]  50%"
        )
        self.assertEqual(
            render_stream.format_progress_bar(80, 80), "80/80  [██████████] 100%"
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

    def test_format_action_and_artifact_labels(self):
        for raw, exp in [
            ("Review", "Review"),
            ("review", "Review"),
            ("Execute", "Execute"),
            ("exec", "Execute"),
            ("execute", "Execute"),
            ("Graduate", "Graduat"),
            ("graduat", "Graduat"),
            ("Validate", "Validat"),
            ("validat", "Validat"),
            ("orchestrate", "Orchest"),
            ("Orchestrate", "Orchest"),
            ("orchest", "Orchest"),
            (None, "Review"),
        ]:
            self.assertEqual(render_stream.format_action_label(raw), exp)

        for raw, exp in [
            ("IPD", "IPD"),
            ("ipd", "IPD"),
            ("plan", "IPD"),
            ("Spec", "Spec"),
            ("spec", "Spec"),
            ("Prompt", "Prompt"),
            ("prompt", "Prompt"),
            ("Roadmap", "Roadmap"),
            ("roadmap", "Roadmap"),
            ("Walkthrough", "Walkthr"),
            ("walkthr", "Walkthr"),
            ("Backlog", "Backlog"),
            ("backlog", "Backlog"),
            (None, "IPD"),
        ]:
            self.assertEqual(render_stream.format_artifact_kind_label(raw), exp)

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
            action="Review",
            artifact_kind="IPD",
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
        self.assertEqual(len(seg1), 10)
        self.assertEqual(len(seg2), 10)

        # Header line segments
        self.assertEqual(seg1[0], "Time")
        self.assertEqual(seg1[1], "From start")
        self.assertIn("set: revgate", seg1[2])
        self.assertIn("id6: 7nkcgp", seg1[2])
        self.assertEqual(seg1[3], "Review")
        self.assertEqual(seg1[4], "Spend")
        self.assertEqual(seg1[5], "Tok")
        self.assertEqual(seg1[6], "Total")
        self.assertEqual(seg1[7], "In")
        self.assertEqual(seg1[8], "Out")
        self.assertEqual(seg1[9], "Cache")

        # Value line segments
        self.assertRegex(seg2[0], r"^\d{2}:\d{2}:\d{2}$")
        self.assertEqual(seg2[1], "1h04m21s last: 14s")
        self.assertEqual(seg2[2], "4m08s 1/1  [██████████] 100%")
        self.assertEqual(seg2[3], "IPD")
        self.assertEqual(seg2[4], "$15.27")
        self.assertEqual(seg2[5], "ens")
        self.assertEqual(seg2[6], "16.2m")
        self.assertEqual(seg2[7], "214.1k")
        self.assertEqual(seg2[8], "195.7k")
        self.assertEqual(seg2[9], "15.8m")

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
            action="Review",
            artifact_kind="IPD",
        )

        expected_top = "╭─────────┬───────────────────────────┬────────────────────────────────┬─────────┬───────┬─────┬───────┬──────┬────────┬───────╮"
        expected_l1_suffix = "│ From start  kill in 9m51s │ set: wtisoland     id6: 6knsrx │  Review │ Spend │ Tok │ Total │   In │    Out │ Cache │"
        expected_l2_suffix = "│ 27m48s last: 8s    stdout │ 27m48s 1/1  [██████████] 100%  │     IPD │ $6.16 │ ens │  4.7m │ 119k │ 110.7k │  4.5m │"
        expected_bot = "╰─────────┴───────────────────────────┴────────────────────────────────┴─────────┴───────┴─────┴───────┴──────┴────────┴───────╯"

        self.assertEqual(top, expected_top)
        self.assertEqual(l1[10:], expected_l1_suffix)
        self.assertEqual(l2[10:], expected_l2_suffix)
        self.assertEqual(bot, expected_bot)
        self.assertEqual(len(top), len(l1))
        self.assertEqual(len(l1), len(l2))
        self.assertEqual(len(l2), len(bot))

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
            action="Execute",
            artifact_kind="IPD",
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
        self.assertIn("set: revgate", s1)
        self.assertIn("Execute", s1)
        self.assertIn("IPD", s2)
        self.assertIn("1h04m21s last: 14s", s2)
        self.assertIn("4m08s 1/1  [██████████] 100%", s2)
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
        self.assertIn("2/10", line)


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
        self.assertIs(
            driver.statusline_action_for_item,
            render_stream.statusline_action_for_item,
        )
        self.assertIs(
            agy_driver.statusline_action_for_item,
            render_stream.statusline_action_for_item,
        )
        self.assertIs(
            driver.execution_index,
            render_stream.execution_index,
        )
        self.assertIs(
            agy_driver.execution_index,
            render_stream.execution_index,
        )

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
            render_stream.statusline_action_for_item,
            render_stream.execution_index,
        ):
            module = inspect.getmodule(obj)
            assert module is not None
            self.assertEqual(module.__name__, "agent_workflows.render_stream")

    # RETIRED by rununify 01 (`2r306y`): `test_oc_runipd_source_has_no_inline_definitions` and
    # `test_agy_runipd_has_no_inline_heartbeat_copy` lived here and were ONE-SIDED, which is the
    # root cause this Set addresses rather than the duplicates themselves: ten names were guarded
    # against `oc_runipd` and only two against `agy_runipd`, so agy quietly re-forked `Palette`,
    # `_strip_ansi`, `_one_line` and four ANSI constants with nothing failing. Both are now rows
    # in the SYMMETRIC, AST-based, table-driven guard in `tests/test_runner_refork_guard.py`,
    # which asserts over BOTH runners in both directions (no top-level definition, and the
    # attribute IS the owner's object). Every name they asserted is in that table (verified
    # mechanically, 0 dropped), so coverage strictly grew: 12 (runner, symbol) pairs became 28.
    # Do NOT re-add a one-sided source-substring guard here; add a row to that table instead.

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


class StatuslineActionDerivationTests(unittest.TestCase):
    """vaboqp: Statusline action column must derive from item['action'], not item['status']."""

    def test_statusline_action_for_item_resolves_explicit_actions(self):
        self.assertEqual(
            render_stream.statusline_action_for_item(
                {"action": "execute", "status": "running"}
            ),
            "execute",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item(
                {"action": "review", "status": "running"}
            ),
            "review",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item(
                {"action": "orchestrate", "status": "queued"}
            ),
            "orchestrate",
        )

    def test_statusline_action_for_item_fallbacks(self):
        self.assertEqual(
            render_stream.statusline_action_for_item({"initial_status": "to-review"}),
            "review",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item({"initial_status": "draft"}),
            "review",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item({"initial_status": "approved"}),
            "execute",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item({"status": "to-review"}),
            "review",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item({}),
            "execute",
        )
        self.assertEqual(
            render_stream.statusline_action_for_item(
                {"action": None, "initial_status": "approved"}
            ),
            "execute",
        )

    def test_queue_item_renders_execute_action_in_statusline(self):
        item = {
            "position": 1,
            "id6": "prpipy",
            "setid": "runorder",
            "configured_file": ".aw/records/plans/pending/test.ipd.md",
            "initial_status": "approved",
            "action": "execute",
            "status": "running",
        }
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(
            pal=pal,
            stream=io.StringIO(),
            interval=0,
            setid=item["setid"],
            id6=item["id6"],
            action=render_stream.statusline_action_for_item(item),
            artifact_kind="ipd",
        )
        line = st.render_line()
        self.assertIn("Execute", line)
        self.assertIn("IPD", line)
        self.assertNotIn("Review", line)


if __name__ == "__main__":
    unittest.main()

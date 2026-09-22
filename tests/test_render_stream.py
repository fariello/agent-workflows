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
    """Each event shape renders to ONE exact line, or to nothing, with color as a MODE column.

    Five tests became one table. Every one of them built a JSON event line, called `render_event`,
    and compared the result to one expected string (or to `None`). Only the event differed, which is
    a data row.

    Why the table beats the five, specifically for a TERMINAL RENDERER: the output of every row is
    assembled by the same two pieces, a prefix looked up in `EVENT_PREFIXES` and padded to the
    derived column, then a payload formatted per tool. So the realistic regression is in the shared
    assembly (a pad change, a prefix rename, a padding call that pads the COLORED string), and it
    shifts EVERY line by the same amount at once. Five tests report that as five red lines that
    each show one shifted string; the table reports one failure listing every row with expected
    versus actual, and seeing the same shift repeated is what identifies the cause as the pad rather
    than the payloads.

    COLOR IS A COLUMN, NOT A SECOND TABLE. Each row is rendered TWICE, once with `Palette(False)`
    and once with `Palette(True)`, and the colored render must satisfy two properties the plain one
    cannot express: it must actually CONTAIN an ANSI escape (otherwise the palette silently stopped
    working and every plain assertion still passes), and stripping ANSI must recover the plain line
    EXACTLY. That second property is the one that matters here, because padding is computed on
    UNCOLORED text: if a colored prefix were padded to the pad width including its escape bytes, the
    visible column would be wrong while every plain-mode test stayed green. The old
    `test_text_event_renders_narration` gestured at this with a single `assertNotIn("\\033[")` on the
    plain line; asserting the strip-to-plain identity on every row is strictly stronger.

    SUPPRESSED rows (expected `None`) live in the same table as rendered rows deliberately. A
    renderer that returned `None` for everything would satisfy every suppression row on its own, so
    keeping the positive rows beside them is what stops that from passing.
    """

    #: (case, raw event line, verbosity, expected plain line or None for suppressed, why)
    EVENTS = (
        (
            "a text part",
            '{"type":"text","part":{"type":"text","text":"Reading the plan."}}',
            0,
            "\u25c8 think: Reading the plan.",
            "narration renders behind the `think` prefix, padded to the derived column",
        ),
        (
            "a tool_use with an explicit title",
            '{"type":"tool_use","part":{"tool":"bash",'
            '"state":{"status":"completed","title":"git status --short"}}}',
            0,
            "\u276f bash:  git status --short",
            "the title is the payload when the event supplies one; `bash` is one codepoint shorter "
            "than `think`, so this row is also where an off-by-one in the padding shows up",
        ),
        (
            "a tool_use with NO title",
            '{"type":"tool_use","part":{"tool":"read",'
            '"state":{"status":"running","input":{"path":"a.py"}}}}',
            1,
            '\u25c0 read:  {"path": "a.py"}',
            "the title FALLS BACK to the serialized input. Asserted at the verbose tier because "
            "`read` is suppressed at the default tier (E-04), so at verbosity 0 there would be no "
            "line to check the fallback on",
        ),
        (
            "an unmapped tool",
            '{"type":"tool_use","part":{"tool":"ask_question",'
            '"state":{"status":"completed","title":"Pick branch"}}}',
            0,
            "\u2022 tool:  ask_question: Pick branch",
            "a tool with no prefix entry still renders: it takes the generic `tool` prefix and NAMES "
            "the tool in the payload, so an unknown tool is identifiable rather than anonymous",
        ),
        (
            "the task tool",
            '{"type":"tool_use","part":{"tool":"task",'
            '"state":{"status":"completed","title":"explore the codebase"}}}',
            0,
            "\u21b3 child: explore the codebase",
            "a subagent spawn gets the `child` prefix, which is how nested work is visually "
            "distinguishable from the parent's own tool calls",
        ),
        (
            "a non-JSON line",
            "a stray log line",
            0,
            "a stray log line",
            "an unparseable line passes through VERBATIM with no prefix and no padding (it is "
            "dimmed when color is on), because dropping it would hide real stderr from the user",
        ),
        (
            "a step_start event",
            '{"type":"step_start"}',
            0,
            None,
            "pure protocol noise: it carries nothing a human wants to read",
        ),
        (
            "a whitespace-only line",
            "   ",
            0,
            None,
            "blank input must not emit a blank line, which would shred the transcript's density",
        ),
        (
            "an unknown event type",
            '{"type":"unknown_event"}',
            0,
            None,
            "an unrecognized type is suppressed rather than dumped raw, so a protocol addition "
            "cannot spam the transcript",
        ),
    )

    def setUp(self) -> None:
        self.plain = render_stream.Palette(False)
        self.colored = render_stream.Palette(True)

    def test_every_event_shape_renders_its_exact_line_in_both_color_modes(self):
        wrong = []
        for case, raw, verbosity, expected, why in self.EVENTS:
            got = render_stream.render_event(raw, self.plain, verbosity=verbosity)
            colored = render_stream.render_event(raw, self.colored, verbosity=verbosity)
            problems = []
            if got != expected:
                problems.append(
                    f"plain render expected {expected!r}, got {got!r}"
                    + (
                        f" (a {len(got) - len(expected):+d} character shift)"
                        if isinstance(got, str) and isinstance(expected, str)
                        else ""
                    )
                )
            if expected is None:
                if colored is not None:
                    problems.append(
                        f"must be suppressed with color on too, got {colored!r}"
                    )
            elif colored is None:
                problems.append("rendered a line with color OFF but None with color ON")
            else:
                if "\033[" not in colored:
                    problems.append(
                        f"the colored render carries NO ANSI escape ({colored!r}), so the palette "
                        "is silently inert and no plain-mode assertion can detect it"
                    )
                stripped = render_stream._strip_ansi(colored)
                if stripped != got:
                    problems.append(
                        f"stripping ANSI gave {stripped!r} but the plain render is {got!r}; "
                        "padding must be computed on UNCOLORED text, so color is additive"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"render_stream.render_event rendered {len(wrong)} of {len(self.EVENTS)} event shapes "
            "wrongly. Every line is assembled from a prefix padded to the derived column plus a "
            "per-tool payload, so read the failures together. If several rows are shifted by the "
            "SAME number of characters, the pad or a prefix length changed and the payloads are "
            "fine (see EventPrefixAlignmentTests, whose table asserts the derivation). If the "
            "strip-to-plain check fails, padding is being computed on the COLORED string, which "
            "misaligns the real terminal while plain-mode tests stay green. If the SUPPRESSED rows "
            "are the ones rendering, noise is reaching the transcript; if only the rendered rows "
            "fail while suppression holds, note that a renderer returning None for everything "
            f"would satisfy the suppressed rows on its own.\n" + "\n".join(wrong),
        )

    def test_step_finish_updates_tracker_and_is_suppressed(self):
        """Kept separate: asserts ACCUMULATED tracker state across two events, not one line.

        The claim is that a second `step_finish` ADDS to the first (cache and cost accumulate while
        `input` is replaced by the running total), which needs two calls sharing one tracker and
        assertions over four numeric fields. A row holds one input and one expected line.
        """
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

    def test_long_text_is_clipped_to_single_line(self):
        """Kept separate: asserts a BOUND and an absence, not an exact line.

        The input is 1000 characters of filler, so there is no expected string to pin; the claims
        are that no newline survives (one event must never become two transcript lines) and that the
        result fits a length budget. Both are inequalities, which no exact-match row expresses.
        """
        long = "word " * 200
        line = render_stream.render_event(
            json.dumps({"type": "text", "part": {"text": long}}), self.plain
        )
        assert line is not None
        self.assertNotIn(
            "\n",
            line,
            "a long text event must be CLIPPED to one line; a newline here means one event "
            "becomes two transcript lines and the statusline redraw math breaks",
        )
        self.assertLessEqual(
            len(line),
            420,
            f"clipped line is {len(line)} characters, over the 420 budget",
        )


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


_CANONICAL_PLACEHOLDER = "[System: Empty message content sanitised to satisfy protocol]"


class SystemProtocolSuppressionTests(unittest.TestCase):
    """Synthetic platform placeholders are suppressed; real text that MENTIONS one is not (eqzd0h).

    Eight tests became two, and the split between them is the closed-set boundary. The three tests
    that each looped the SAME twenty observed variants are now one test that checks all three
    surfaces per variant; the five that each probed one distinctive TEXT SHAPE are one table.

    Why tables suit this subject: the twenty variants are a CLOSED SET of strings actually observed
    in run logs, all matched by one pattern in `strip_system_protocol_prefix`. The realistic failure
    is that pattern being tightened or loosened, which moves MANY variants at once, and in the
    loosened direction it starts eating real narration. Three `subTest` loops reported that as three
    red blocks listing overlapping variants; one accumulating test reports each variant once with
    every surface that mishandled it.

    THREE SURFACES ARE THREE COLUMNS, NOT THREE TABLES, and this is the important structural point.
    The same string reaches the renderer by two different routes, as the `text` field of a JSON
    event and as a bare unparseable line, and the two routes DO NOT agree, deliberately. A
    placeholder followed by real narration inside a JSON `text` part renders just the narration,
    while the identical bytes arriving as a bare line are passed through VERBATIM, placeholder
    included. That asymmetry is correct (an unparseable line is raw output we must not silently
    edit) and it is invisible unless both routes sit in one row, which is why `expected_event` and
    `expected_bare` are separate columns rather than separate tests.

    The PRESERVED rows (a placeholder quoted mid-sentence, a truncated one, ordinary log text) are in
    the same table as the suppressed ones because they are what stops the fix from being a
    catastrophe: a matcher that suppressed everything would satisfy every suppression row while
    deleting the narration a human is reading the transcript for.
    """

    def setUp(self) -> None:
        self.pal = render_stream.Palette(False)
        self.pad = render_stream.event_prefix_pad(True)
        self.think_prefix = render_stream.EVENT_PREFIXES["think"].ljust(self.pad)

    def test_every_observed_variant_is_suppressed_on_every_surface(self):
        """The twenty variants OBSERVED in real run logs, checked on all three surfaces at once."""
        self.assertEqual(
            len(_OBSERVED_SYSTEM_PROTOCOL_VARIANTS),
            20,
            "this test's name and the eqzd0h findings both claim TWENTY observed variants; "
            f"the list now holds {len(_OBSERVED_SYSTEM_PROTOCOL_VARIANTS)}",
        )
        variants = list(_OBSERVED_SYSTEM_PROTOCOL_VARIANTS) + [
            _CANONICAL_PLACEHOLDER
            * 2  # the CHAINED form, which the model emits back to back
        ]
        wrong = []
        for variant in variants:
            problems = []
            stripped = render_stream.strip_system_protocol_prefix(variant)
            if stripped != "":
                problems.append(
                    f"strip_system_protocol_prefix left {stripped!r} instead of an empty string"
                )
            evt = json.dumps(
                {"type": "text", "part": {"type": "text", "text": variant}}
            )
            as_event = render_stream.render_event(evt, self.pal)
            if as_event is not None:
                problems.append(
                    f"as a JSON text event it rendered {as_event!r} instead of being suppressed"
                )
            as_bare = render_stream.render_event(variant, self.pal)
            if as_bare is not None:
                problems.append(
                    f"as a bare non-JSON line it rendered {as_bare!r} instead of being suppressed"
                )
            if problems:
                wrong.append(
                    f"  {variant!r}\n"
                    + "".join(f"    - {p}\n" for p in problems).rstrip()
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(variants)} observed placeholder variants were not fully "
            "suppressed. All of them are matched by ONE pattern in "
            "`strip_system_protocol_prefix`, so many variants failing together means that pattern "
            "was TIGHTENED (it no longer covers the wording drift these twenty variants are a "
            "record of) rather than twenty separate bugs. FIX: note WHICH surface leaked. If "
            "`strip_system_protocol_prefix` is correct but the SURFACES still render, the renderer "
            "stopped calling it on that route; if the strip itself leaks, the pattern is the "
            "suspect. Every variant here was seen in a real run log, so a leak puts this noise back "
            f"in front of a human watching a run.\n" + "\n".join(wrong),
        )

    #: (case, raw text, expected `strip_system_protocol_prefix` result,
    #:  expected render as a JSON text event, expected render as a bare non-JSON line, why)
    #: `None` in a render column means the line must be SUPPRESSED. `"<THINK>"` is replaced with the
    #: padded think prefix, and `"<SELF>"` with the raw text itself.
    TEXT_SHAPES = (
        (
            "a placeholder alone",
            _CANONICAL_PLACEHOLDER,
            "",
            None,
            None,
            "the base case both other columns are measured against",
        ),
        (
            "two placeholders chained",
            _CANONICAL_PLACEHOLDER * 2,
            "",
            None,
            None,
            "the model emits them back to back, so stripping must be REPEATED rather than applied "
            "once; stripping once would leave a whole second placeholder on screen",
        ),
        (
            "a placeholder then real narration",
            _CANONICAL_PLACEHOLDER
            + "\n\nNow let me look at the key structural question.",
            "Now let me look at the key structural question.",
            "<THINK>Now let me look at the key structural question.",
            _CANONICAL_PLACEHOLDER + " Now let me look at the key structural question.",
            "THE CENTRAL CASE, and the one where the two surfaces diverge on purpose: as a JSON "
            "text part the placeholder is removed and the narration survives behind the think "
            "prefix, but the same bytes as a BARE line KEEP the placeholder, because an "
            "unparseable line is raw output we must not silently edit. Note the bare column is not "
            "byte-identical to the input either: the blank line collapses to a single space, "
            "because every rendered line is clipped to ONE line (see "
            "`test_long_text_is_clipped_to_single_line`). Preserving the placeholder and collapsing "
            "the newline are separate behaviors and this row pins both",
        ),
        (
            "a placeholder quoted mid-sentence",
            f"We observed {_CANONICAL_PLACEHOLDER} in logs.",
            "<SELF>",
            "<THINK><SELF>",
            "<SELF>",
            "the matcher is anchored at the START, so a human (or this very test file) DISCUSSING a "
            "placeholder keeps their sentence intact. A matcher that suppressed this would delete "
            "real narration, which is far worse than leaking noise",
        ),
        (
            "a truncated placeholder with no closing bracket",
            "[System: Empty message content sanitised",
            "<SELF>",
            "<THINK><SELF>",
            "<SELF>",
            "an incomplete placeholder is NOT one: matching it would mean matching any line that "
            "merely begins like one, so the closing bracket is required",
        ),
        (
            "ordinary unparseable log text",
            "regular unparseable log line",
            "<SELF>",
            "<THINK><SELF>",
            "<SELF>",
            "the control row: text with no placeholder at all must pass through untouched on both "
            "surfaces, which is what proves the suppression rows are not vacuous",
        ),
    )

    def test_every_text_shape_is_stripped_and_rendered_correctly_on_both_surfaces(self):
        wrong = []
        for case, raw, exp_strip, exp_event, exp_bare, why in self.TEXT_SHAPES:

            def resolve(value):
                if value is None:
                    return None
                return value.replace("<THINK>", self.think_prefix).replace(
                    "<SELF>", raw
                )

            expected_strip = resolve(exp_strip)
            expected_event = resolve(exp_event)
            expected_bare = resolve(exp_bare)
            problems = []
            got_strip = render_stream.strip_system_protocol_prefix(raw)
            if got_strip != expected_strip:
                problems.append(
                    f"strip_system_protocol_prefix expected {expected_strip!r}, got {got_strip!r}"
                )
            evt = json.dumps({"type": "text", "part": {"type": "text", "text": raw}})
            got_event = render_stream.render_event(evt, self.pal)
            if got_event != expected_event:
                problems.append(
                    f"as a JSON text event expected {expected_event!r}, got {got_event!r}"
                )
            got_bare = render_stream.render_event(raw, self.pal)
            if got_bare != expected_bare:
                problems.append(
                    f"as a bare non-JSON line expected {expected_bare!r}, got {got_bare!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (input {raw!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"placeholder handling is wrong for {len(wrong)} of {len(self.TEXT_SHAPES)} text "
            "shapes. One anchored matcher decides all of them, so the DIRECTION of the failures is "
            "the diagnosis and the two directions are not equally bad. If the PRESERVED rows "
            "(quoted mid-sentence, truncated, ordinary log text) are failing, the matcher has been "
            "LOOSENED and is now deleting real narration a human needs, which is the severe case. "
            "If only the suppression rows fail, noise is leaking through, which is merely untidy. "
            "FIX: remember the two surfaces are ALLOWED to differ. The bare-line column preserving "
            "a placeholder that the JSON-event column strips is the intended asymmetry, not a bug "
            f"to unify.\n" + "\n".join(wrong),
        )


class PaletteUnitTests(unittest.TestCase):
    """`Palette` wraps text in exactly the SGR sequence its arguments name, or in nothing.

    Five tests became one table with the ENABLED FLAG as a MODE COLUMN, which is the right shape
    because the flag is the whole subject: `Palette(False)` must be a perfect no-op and
    `Palette(True)` must emit the right codes, and those are two modes of one function rather than
    two functions. Splitting them into separate tables would lose the pairing that matters, namely
    that the same call with the flag flipped differs ONLY by escape bytes.

    Why the table beats the five: the expected strings are pinned as EXACT byte sequences, and they
    all come from one lookup table (`_ANSI_CODES`) joined by one wrapper. A renumbered or reordered
    code changes several rows at once, and the old tests could not see that because they asserted
    weakly and differently from each other: one checked only `startswith("\\033[")`, another only
    `assertIn("32", out)`, which would also pass on a stray `32` anywhere in the payload. Pinning
    the exact sequence per row is stronger AND makes the failure legible, since a wrong code is
    visible as a number rather than as a missing substring.

    The DISABLED rows are in the same table as the enabled ones for the usual reason: a `Palette`
    that returned its input unchanged in BOTH modes would satisfy every disabled row on its own,
    and that regression is exactly what "color silently stopped working" looks like.
    """

    #: (case, enabled, call as ("text", *styles) or ("status", value), expected exact output, why)
    PALETTE_CALLS = (
        (
            "plain text, color off",
            False,
            ("text", "x", ("green",)),
            "x",
            "with color off the wrapper is a perfect NO-OP: not an empty escape, not a reset, the "
            "input byte for byte, because this output is what lands in logs and CI",
        ),
        (
            "plain text, color on",
            True,
            ("text", "x", ("green",)),
            "\033[32mx\033[0m",
            "green is code 32, and the wrap is open-sequence, text, RESET; without the reset the "
            "color bleeds into every following line",
        ),
        (
            "two styles combined",
            True,
            ("text", "hello", ("red", "bold")),
            "\033[31;1mhello\033[0m",
            "multiple styles are SEMICOLON-JOINED inside ONE escape (31;1), not emitted as two "
            "nested escapes, and the order follows the arguments",
        ),
        # THE THREE `status` ROWS BELOW WERE RE-POINTED, NOT RELAXED (plan `qdd5jq` E-05, spec
        # `uonrjg` R10.3). They pinned the 16-color SGR codes of the LOCAL `_STATUS_COLOR` table this
        # module used to own; that table is gone and `Palette.status` now resolves through
        # `lifecycle_style`, so the expected bytes are the SPEC's xterm-256 indices. Each row keeps
        # the property it was written to protect, which is why re-pointing is correct and deleting
        # would have been a loss.
        (
            "a known status, color on",
            True,
            ("status", "executed"),
            "\033[1;38;5;46mexecuted\033[0m",
            "`executed` is the spec's `done` stage: 46 bold (spec Section 5). The terminal status "
            "word IS the text, unchanged",
        ),
        (
            "a READY status is NOT the same color as a COMPLETED one",
            True,
            ("status", "approved"),
            "\033[1;38;5;45mapproved\033[0m",
            "THE ROW THIS WHOLE CONVERSION EXISTS FOR (finding F-01). The retired table mapped "
            "`approved`, `reviewed`, `executed` AND `substantially-complete` all to ONE green, so a "
            "plan that had not started looked identical to one that was finished and verified. Spec "
            "Section 5 reserves green for completion and makes ready work cyan 45; this row fails if "
            "anything ever collapses them again",
        ),
        (
            "a failure status, color on",
            True,
            ("status", "failed-safely"),
            "\033[1;38;5;196mfailed-safely\033[0m",
            "a FAILURE maps to red 196, not to the same color a success gets. This row exists "
            "because a status-color table that collapsed to one color would still satisfy the "
            "`executed` row",
        ),
        (
            "an unknown status still returns its WORD",
            True,
            ("status", "no-such-status"),
            "\033[38;5;244mno-such-status\033[0m",
            "AN UNMAPPED STATUS DEGRADES RATHER THAN CRASHING, which is the property this row has "
            "always protected and which still holds: the word is returned intact. What changed is "
            "that it now carries the shared resolver's neutral `unknown` gray (244, not bold) "
            "instead of no escape at all, because spec criterion A20 requires an unresolvable "
            "status to render as `unknown` rather than to masquerade as unstyled ordinary text",
        ),
        (
            "a known status, color off",
            False,
            ("status", "executed"),
            "executed",
            "the status helper honors the flag too, rather than colorizing unconditionally",
        ),
    )

    def test_every_palette_call_emits_its_exact_escape_sequence(self):
        wrong = []
        for case, enabled, call, expected, why in self.PALETTE_CALLS:
            pal = render_stream.Palette(enabled)
            if call[0] == "text":
                _, text, styles = call
                got = pal(text, *styles)
                shown = f"Palette({enabled})({text!r}, {', '.join(map(repr, styles))})"
            else:
                got = pal.status(call[1])
                shown = f"Palette({enabled}).status({call[1]!r})"
            problems = []
            if got != expected:
                problems.append(f"expected {expected!r}, got {got!r}")
            # Whatever the codes, stripping must always recover the bare text.
            bare = call[1] if call[0] == "status" else call[1]
            if render_stream._strip_ansi(got) != bare:
                problems.append(
                    f"_strip_ansi gave {render_stream._strip_ansi(got)!r}, expected the bare text "
                    f"{bare!r}; every width calculation in this module strips first, so a "
                    "sequence _strip_ansi cannot remove corrupts the layout"
                )
            if problems:
                wrong.append(
                    f"  {case}: {shown}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"render_stream.Palette emitted the wrong sequence for {len(wrong)} of "
            f"{len(self.PALETTE_CALLS)} calls. Every row resolves through ONE lookup "
            "(`_ANSI_CODES`, or `_STATUS_COLOR` then `_ANSI_CODES`) and one wrapper, so several "
            "rows moving together usually means a code was renumbered or the wrapper's shape "
            "changed rather than several independent bugs. FIX: a DISABLED row emitting escapes is "
            "the serious direction, because that output goes into log files and CI transcripts; an "
            "ENABLED row emitting none means color silently died, which no plain-mode test in this "
            "module can detect. A failing _strip_ansi check means the emitted sequence is not one "
            f"the stripper recognizes, which breaks every padded column in the renderer.\n"
            + "\n".join(wrong),
        )


class HeartbeatLifecycleTests(unittest.TestCase):
    """Heartbeat enter/exit/interval lifecycle."""

    def test_disabled_heartbeat_writes_nothing(self):
        """Kept separate: needs a live thread and a real sleep; a timing lifecycle, not a mapping."""
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        hb = render_stream.Heartbeat(pal, "test-ipd", buf, interval=0)
        with hb:
            time.sleep(0.05)
        self.assertEqual(buf.getvalue(), "")

    def test_enabled_heartbeat_emits_while_idle(self):
        """Kept separate: needs a live thread and a real sleep to observe an emission."""
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
        """Kept separate: mutates a live Heartbeat then reads three derived strings back."""
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
        """Kept separate: a GOLDEN whole-transcript pin over a fixed event stream, deliberately
        redundant with the per-event table so a regression shows up as both a line and a stream."""
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
        """Kept separate: compares two transcripts to EACH OTHER, so it has no literal expectation."""
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
        """Kept separate: a whole-transcript strip identity, asserted across the stream not per line."""
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
        """Kept separate: asserts a padded WIDTH via `format_event_prefix`, not a rendered line."""
        rendered = render_stream.format_event_prefix(
            "newtool", render_stream.Palette(False)
        )
        self.assertEqual(
            len(render_stream._strip_ansi(rendered)),
            render_stream.event_prefix_pad(True),
        )
        self.assertEqual(rendered, "\u2022 tool:  ")

    def test_unmapped_tool_renders_with_tool_prefix_and_names_tool(self):
        """Kept separate: the RenderEventUnitTests table pins this exact line; here it asserts the
        alignment class's own concern, that an unmapped tool still reaches the derived column."""
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
        """Kept separate for the same reason as the unmapped-tool test above: this class owns the
        alignment claim, while the exact line is a row in the RenderEventUnitTests table."""
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

    #: (prefix key, its EVENT_PREFIXES label or None if the key must be ABSENT, its
    #: EVENT_PREFIXES_ASCII label, why this row exists)
    PREFIX_TABLE = (
        (
            "think",
            "\u25c8 think:",
            "~ think:",
            "the canonical thought prefix after streamfx (xs19dk) E-01 retired `reason` into it. "
            "Its glyph is East-Asian-AMBIGUOUS, so the narrow table substitutes a plain `~`",
        ),
        (
            "child",
            "\u21b3 child:",
            "\u21b3 child:",
            "a subagent spawn. Its arrow is NARROW already, so the two tables carry the SAME glyph; "
            "that identity is the point, and a test asserting only the unicode table would not see "
            "a substitution wrongly applied here",
        ),
        (
            "tool",
            "\u2022 tool:",
            "- tool:",
            "the fallback prefix for an unmapped tool; the bullet IS ambiguous-width, so unlike "
            "`child` it must be substituted in the narrow table",
        ),
        (
            "reason",
            None,
            None,
            "RETIRED into `think` (streamfx xs19dk E-01). It must be ABSENT from both tables: "
            "leaving it would give thoughts two different prefixes depending on which branch ran",
        ),
        (
            "subagent",
            None,
            None,
            "never existed under this name; `child` is the spelling. Asserted absent so the two "
            "never coexist",
        ),
    )

    def test_every_named_prefix_has_its_exact_label_in_both_width_tables(self):
        """One table over the prefix-table membership claims, replacing two tests.

        The two old tests were the same shape (assert a key is in both tables, assert its label in
        each, assert some keys are absent) applied to different keys, with sixteen sequential
        assertions between them that stopped at the first failure.

        Why the table beats the two: `EVENT_PREFIXES` and `EVENT_PREFIXES_ASCII` are a CLOSED SET
        that must stay in one-to-one correspondence, and the realistic failure is a rename or a
        retirement touching several keys at once. Each row asserts BOTH tables side by side, which is
        what makes the correspondence checkable per key; a per-table test cannot see that `child`
        legitimately carries the same glyph in both while `tool` legitimately does not.

        Each row also re-asserts the per-key LENGTH IDENTITY between the two tables, because equal
        lengths are what let both tables derive the same pad. A narrow substitution that changed a
        label's length would silently misalign the narrow terminal while every unicode-mode
        assertion stayed green.
        """
        wrong = []
        for key, unicode_label, ascii_label, why in self.PREFIX_TABLE:
            problems = []
            if unicode_label is None:
                if key in render_stream.EVENT_PREFIXES:
                    problems.append(
                        f"must be ABSENT from EVENT_PREFIXES but holds "
                        f"{render_stream.EVENT_PREFIXES[key]!r}"
                    )
                if key in render_stream.EVENT_PREFIXES_ASCII:
                    problems.append(
                        f"must be ABSENT from EVENT_PREFIXES_ASCII but holds "
                        f"{render_stream.EVENT_PREFIXES_ASCII[key]!r}"
                    )
            else:
                got_unicode = render_stream.EVENT_PREFIXES.get(key)
                got_ascii = render_stream.EVENT_PREFIXES_ASCII.get(key)
                if got_unicode != unicode_label:
                    problems.append(
                        f"EVENT_PREFIXES expected {unicode_label!r}, got {got_unicode!r}"
                    )
                if got_ascii != ascii_label:
                    problems.append(
                        f"EVENT_PREFIXES_ASCII expected {ascii_label!r}, got {got_ascii!r}"
                    )
                if (
                    got_unicode is not None
                    and got_ascii is not None
                    and len(got_unicode) != len(got_ascii)
                ):
                    problems.append(
                        f"the two labels differ in LENGTH ({len(got_unicode)} vs "
                        f"{len(got_ascii)}), so the two tables can no longer derive the same pad "
                        "and the narrow terminal will misalign"
                    )
            if problems:
                wrong.append(
                    f"  {key!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the prefix tables are wrong for {len(wrong)} of {len(self.PREFIX_TABLE)} keys. These "
            "two tables are a closed set in one-to-one correspondence, so several keys moving "
            "together usually means a rename or retirement swept through rather than several "
            "independent edits. FIX: a key expected ABSENT that is now present means a retired "
            "prefix came back, which gives one concept two spellings; a LENGTH mismatch between the "
            "two tables breaks the shared pad derivation and is the failure the narrow-width policy "
            f"exists to prevent.\n" + "\n".join(wrong),
        )

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

    #: (case, the PRIOR todo list already seen by the tracker (None for a first event), the todo
    #: list in this event, which field carries it, expected payload, why this row exists)
    TRANSITIONS = (
        (
            "a first event initializes",
            None,
            [
                {"content": "A", "status": "in_progress", "priority": "high"},
                {"content": "B", "status": "pending", "priority": "low"},
                {"content": "C", "status": "pending", "priority": "low"},
            ],
            "metadata",
            "initialized 3 tasks (1 active, 2 pending)",
            "with no prior list there is nothing to diff against, so the payload SUMMARIZES rather "
            "than reporting a transition",
        ),
        (
            "a first event carried in `input` instead",
            None,
            [{"content": "A", "status": "pending", "priority": "high"}],
            "input",
            "initialized 1 tasks (0 active, 1 pending)",
            "`input.todos` is the FALLBACK when `metadata` is absent; both routes must produce the "
            "identical payload, which is why the source is a column rather than a second table",
        ),
        (
            "one task completes and the next starts",
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "in_progress"},
            ],
            "metadata",
            '[1/2 done]: completed "A" -> active "B"',
            "the common case: a DIFF against the prior list names what finished and what started, "
            "which is the whole reason the tracker holds the previous todos at all",
        ),
        (
            "a task completes with nothing taking over",
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "pending"},
            ],
            "metadata",
            '[1/2 done]: completed "A" -> no active task',
            "measured: 169 of 984 real events carry ZERO in_progress items, so this is a normal "
            "state that must read as idle rather than rendering an empty quoted name",
        ),
        (
            "two tasks active at once",
            [
                {"content": "A", "status": "pending"},
                {"content": "B", "status": "pending"},
                {"content": "C", "status": "pending"},
            ],
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "in_progress"},
                {"content": "C", "status": "pending"},
            ],
            "metadata",
            '[0/3 done]: active "A", "B"',
            "measured: 16 of 984 events carry TWO OR MORE in_progress items, so ALL of them are "
            "named; showing only the first would misreport what the agent is doing",
        ),
        (
            "a task is cancelled, not completed",
            [
                {"content": "A", "status": "pending"},
                {"content": "B", "status": "pending"},
            ],
            [
                {"content": "A", "status": "cancelled"},
                {"content": "B", "status": "in_progress"},
            ],
            "metadata",
            '[0/2 done]: active "B"',
            "measured: `cancelled` occurs 4 times and is NOT an accomplishment, so the done count "
            "stays 0 of 2 and the payload must not claim all tasks completed",
        ),
        (
            "every task completes",
            [
                {"content": "A", "status": "in_progress"},
                {"content": "B", "status": "pending"},
            ],
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "completed"},
            ],
            "metadata",
            "all 2 tasks completed",
            "the terminal state gets its OWN wording rather than a [2/2 done] diff",
        ),
        (
            "a cancelled item in the very first list",
            None,
            [
                {"content": "A", "status": "cancelled"},
                {"content": "B", "status": "pending"},
            ],
            "metadata",
            "initialized 2 tasks (0 active, 1 pending, 1 cancelled)",
            "the initialization summary gains a `cancelled` clause only when there is one, so the "
            "common case stays short",
        ),
    )

    def test_every_todo_transition_renders_its_exact_payload(self):
        """One table over the todowrite payloads, replacing eight near-identical tests.

        Each of the eight fed a todo list (sometimes after a priming list), then compared the
        rendered payload to one string. The only differences were the lists, which is a data row.

        Why the table beats the eight: every payload is produced by ONE differ that compares this
        event's todos against the tracker's previous todos and then picks a wording (initialize,
        diff, or all-done). A change to the counting (does `cancelled` count as done?) or to the
        wording moves several rows at once, and the accumulated report shows which, where eight
        tests showed eight unrelated red lines.

        The PRIOR column is what makes this one table rather than two. An `initialized` payload and
        a `[N/M done]` payload are not two behaviors to test separately; they are the SAME differ
        answering with an empty prior versus a populated one, and keeping both here is what proves
        the initialize wording is chosen because there was nothing to diff rather than by accident.
        """
        wrong = []
        head = "\u2611 todo:".ljust(self.pad)
        for case, prior, todos, source, expected, why in self.TRANSITIONS:
            tracker = render_stream.StreamTracker()
            if prior is not None:
                self._render(prior, tracker, source=source)
            line = render_stream.render_event(
                _tool_event(
                    "todowrite",
                    **(
                        {"metadata": {"todos": todos}}
                        if source == "metadata"
                        else {"input": {"todos": todos}}
                    ),
                ),
                self.plain,
                tracker=tracker,
            )
            if line is None:
                wrong.append(
                    f"  {case}: rendered NOTHING; a todowrite event must always produce a line\n"
                    f"    this row exists because: {why}"
                )
                continue
            if not line.startswith(head):
                wrong.append(
                    f"  {case}: expected the `todo` prefix {head!r}, got line {line!r}\n"
                    f"    this row exists because: {why}"
                )
                continue
            got = line[len(head) :]
            if got != expected:
                wrong.append(
                    f"  {case} (via {source}):\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the todowrite payload is wrong for {len(wrong)} of {len(self.TRANSITIONS)} "
            "transitions. ONE differ produces all of them, so read the grouping. Every "
            "`initialized` row failing while the diff rows pass means the empty-prior branch "
            "changed; every `[N/M done]` row failing means the diff or the counting changed. FIX: "
            "if the cancelled row now reports a HIGHER done count, `cancelled` is being counted as "
            "an accomplishment, which overstates progress to a watching human; if the multi-active "
            "row names only one task, the renderer is hiding concurrent work that measurement says "
            "happens in 16 of 984 real events. A `metadata` row and its `input` twin disagreeing "
            "means the two carriers diverged and half of real events will render differently from "
            "the other half.\n" + "\n".join(wrong),
        )

    def test_the_title_field_is_never_the_payload(self):
        """Kept separate: a NEGATIVE claim about a field the table's rows do not even set.

        The measured `title` on a todowrite event is only ever the useless string "<N> todos", so
        this event sets BOTH `title` and `metadata.todos` and asserts the title does not appear. No
        transition row carries a title, and adding the column to all eight to serve this one case
        would be machinery every other row ignores.
        """
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
        self.assertNotIn(
            "4 todos",
            line,
            "the measured `title` value is only ever '<N> todos' and must NOT be what renders; "
            f"got {line!r}",
        )
        self.assertIn(
            "initialized 1 tasks",
            line,
            f"the payload must come from `metadata.todos`; got {line!r}",
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
        """Kept separate: asserts which tracker fields survive a reset, not a rendered payload."""
        tracker = render_stream.StreamTracker()
        tracker.update(inp=10, out=5, cache=2, cost=1.5)
        tracker.note_modified_file("a.py")
        tracker.todos = [{"content": "A", "status": "pending"}]
        tracker.begin_turn()
        self.assertEqual(tracker.todos, [])
        self.assertEqual(tracker.input_tokens, 10)
        self.assertEqual(tracker.modified_files, {"a.py"})

    def test_a_snapshot_is_rendered_when_no_tracker_is_supplied(self):
        """Kept separate: the distinguishing input is the ABSENCE of a tracker, and every transition
        row requires one; the payload is a snapshot rather than a transition."""
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

    #: (case, prefix kind, the tool_event kwargs, expected payload, why this row exists)
    PAYLOADS = (
        (
            "an edit with real diff stats",
            "edit",
            dict(
                tool="edit",
                metadata={
                    "filediff": {
                        "file": "/repo/agent_workflows/x.py",
                        "patch": "@@ -1 +1 @@\n-a\n+b",
                        "additions": 12,
                        "deletions": 3,
                    }
                },
            ),
            "agent_workflows/x.py (+12, -3)",
            "an edit reports its path RELATIVE to the repo root plus the integer add/delete counts "
            "the event already carries, rather than re-deriving them from the patch text",
        ),
        (
            "an edit to a path OUTSIDE the repo",
            "edit",
            dict(
                tool="edit",
                metadata={
                    "filediff": {
                        "file": "/elsewhere/z.py",
                        "patch": "",
                        "additions": 1,
                        "deletions": 0,
                    }
                },
            ),
            "/elsewhere/z.py (+1, -0)",
            "TRUNCATION BOUNDARY: a path that is not under the repo root is left ABSOLUTE rather "
            "than being relativized into a misleading `../..` or silently trimmed. This is the row "
            "that proves the shortening is a repo-relative rewrite and not blind prefix stripping",
        ),
        (
            "a write of a new file",
            "write",
            dict(
                tool="write",
                metadata={"filepath": "/repo/new.py", "exists": False},
                input={"content": "a\nb\nc\n"},
            ),
            "new.py (new file, 3 lines)",
            "a write has NO diff stats, so the line count is DERIVED from the content it wrote",
        ),
        (
            "a write over an existing file",
            "write",
            dict(
                tool="write",
                metadata={"filepath": "/repo/old.py", "exists": True},
                input={"content": "x\ny\n"},
            ),
            "old.py (overwrote, 2 lines)",
            "`exists: true` changes the wording to `overwrote`, which is the difference between "
            "creating a file and destroying one a human may care about",
        ),
        (
            "a write with no content at all",
            "write",
            dict(tool="write", metadata={"filepath": "/repo/x.py", "exists": False}),
            "x.py (new file)",
            "with nothing to count it DEGRADES to no count rather than raising or printing a "
            "confidently wrong number like `0 lines`",
        ),
    )

    def test_every_edit_and_write_event_renders_its_exact_payload(self):
        """One table over the edit/write payloads, replacing five near-identical tests.

        Each of the five built one `edit` or `write` event, rendered it with `repo_root="/repo"`, and
        compared the payload to one string. The tool is a column, not a reason for two tables: both
        answer the same question (which file, and what happened to it), and they are deliberately
        asymmetric in HOW they answer, which only a shared table makes visible. `edit` reads the
        integer `additions`/`deletions` the event supplies, while `write` has no `filediff` at all
        (measured: absent in 480 of 480 real write events) and must count lines from the content it
        wrote.

        Why the table beats the five: both payloads share the path-shortening step, so a regression
        there moves every row at once while the per-tool wording stays correct. Five tests report
        that as five red lines showing five different paths; the table reports one failure where the
        SAME wrong shortening is visible across rows, which is what names the cause.

        WIDTH AND TRUNCATION ARE THE SUBJECT of the outside-the-repo row, which is why it is here
        rather than in its own test: the shortening exists to keep this cell narrow, and the one case
        that must NOT be shortened is the only guard against the shortening being blind prefix
        removal.
        """
        wrong = []
        for case, kind, kwargs, expected, why in self.PAYLOADS:
            head = render_stream.EVENT_PREFIXES[kind].ljust(self.pad)
            line = render_stream.render_event(
                _tool_event(**kwargs), self.plain, repo_root="/repo"
            )
            if line is None:
                wrong.append(
                    f"  {case}: rendered NOTHING\n    this row exists because: {why}"
                )
                continue
            if not line.startswith(head):
                wrong.append(
                    f"  {case}: expected the {kind!r} prefix {head!r}, got line {line!r}\n"
                    f"    this row exists because: {why}"
                )
                continue
            got = line[len(head) :]
            if got != expected:
                wrong.append(
                    f"  {case}:\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the edit/write payload is wrong for {len(wrong)} of {len(self.PAYLOADS)} events. The "
            "two tools share the path-shortening step and differ in how they describe the change, "
            "so read the grouping. If the PATHS are wrong across both tools, the shortening broke; "
            "if only the parenthetical differs, the per-tool formatter did. FIX: the "
            "outside-the-repo row turning into a relative or trimmed path means the shortening is "
            "blind prefix removal and is now lying about where a file lives. A `write` row that "
            "grew diff stats means the formatter started reading `filediff`, which real write "
            f"events never carry.\n" + "\n".join(wrong),
        )

    def test_a_write_whose_metadata_omits_filediff_entirely_still_renders(self):
        """Kept separate: ASSERTS THE FIXTURE ITSELF lacks `filediff` before rendering it.

        F-8: `write` has NO `filediff` in 480 of 480 measured events. The point of this test is the
        `assertNotIn("filediff", ...)` precondition on a hand-built state dict, which pins the shape
        the measurement found. A table row cannot assert something about its own input, and the
        structural guard below covers the other half (no code path reads the field).
        """
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

    def test_modified_files_accumulates_edits_and_writes(self):
        """Kept separate: asserts TRACKER SIDE EFFECTS across two events, not either one's line.

        The claim is that an `edit` and a `write` both register their file in `tracker.modified_files`
        and that the set ACCUMULATES. That is a property of two calls sharing one tracker, and the
        rendered lines (which the payload table already pins) are irrelevant to it.
        """
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

    #: (case, the files to note on the tracker, the expected `Files touched` substring or None if
    #: the row must not appear at all, why this row exists)
    FILE_COUNTS = (
        (
            "two files touched",
            ("agent_workflows/render_stream.py", "tests/test_render_stream.py"),
            "Files touched: 2 files",
            "E-08: `modified_files` must have a NAMED READER or it should not exist, and the run "
            "summary table is that reader",
        ),
        (
            "exactly one file touched",
            ("only.py",),
            "Files touched: 1 file",
            "SINGULAR: `1 file`, not `1 files`. A count cell that reads wrong at n=1 is the most "
            "visible sloppiness in a summary a human reads at the end of every run",
        ),
        (
            "no files touched",
            (),
            None,
            "a run with no edits must omit the row ENTIRELY, staying byte-identical to the "
            "pre-change table rather than printing `0 files`",
        ),
    )

    def test_the_summary_table_reports_its_files_touched_count(self):
        """One table over the files-touched cell, replacing three tests.

        Each of the three noted some files on a tracker, rendered the run summary, and asserted one
        substring was present or absent. Only the file count differed.

        Why the table beats the three: one pluralization-and-omission decision produces all three
        answers, and its failure modes are adjacent (0 rendering as `0 files` instead of nothing, 1
        rendering as `1 files`). Seeing the whole ladder in one failure is what shows whether the
        boundary moved or the wording did. The ABSENT row is in the same table deliberately: a cell
        that never rendered would satisfy nothing else here, and a cell that always rendered would
        satisfy both count rows while breaking the no-edit run.
        """
        wrong = []
        for case, files, expected, why in self.FILE_COUNTS:
            tracker = render_stream.StreamTracker()
            for name in files:
                tracker.note_modified_file(name)
            out = render_stream.render_run_summary_table(
                self._STATE, tracker=tracker, pal=render_stream.Palette(False)
            )
            if expected is None:
                if "Files touched" in out:
                    line = next(
                        (row for row in out.splitlines() if "Files touched" in row), ""
                    )
                    wrong.append(
                        f"  {case}: the row must be OMITTED entirely, but the table contains "
                        f"{line.strip()!r}\n    this row exists because: {why}"
                    )
            elif expected not in out:
                line = next(
                    (row for row in out.splitlines() if "Files touched" in row), None
                )
                wrong.append(
                    f"  {case}: expected {expected!r}; the table's own line is "
                    f"{(line.strip() if line else 'ABSENT ENTIRELY')!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the run summary's files-touched cell is wrong for {len(wrong)} of "
            f"{len(self.FILE_COUNTS)} counts. One decision (omit at zero, else pluralize) produces "
            "all of them. FIX: if the ZERO row now renders, a run that changed nothing will report "
            "a `0 files` line the old table never had; if the ONE row reads `1 files`, the "
            "pluralization boundary is off by one. If ALL rows are missing the row entirely, "
            "`modified_files` has lost its only named reader and E-08's premise (that the field is "
            f"read by something) no longer holds.\n" + "\n".join(wrong),
        )

    def test_the_accumulation_scope_is_documented_as_run_scoped(self):
        """Kept separate: asserts over a DOCSTRING, not over rendered output."""
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

    #: (case, event key from `_events()` or a literal event, verbosity, expected payload
    #: substrings, substrings that must be ABSENT, why this row exists)
    TIER_PAYLOADS = (
        (
            "an error at the DEFAULT tier",
            "error",
            0,
            ("UnknownError", "The operation timed out."),
            (),
            "F-13: this branch did not exist, so a real error event rendered as None and a failing "
            "run looked silent. An error must surface at the QUIETEST tier, naming both the error "
            "class and its message",
        ),
        (
            "an error at the verbose tier",
            "error",
            1,
            ("UnknownError", "The operation timed out."),
            (),
            "raising the tier must not change an error's rendering; it is already the minimum",
        ),
        (
            "an error at the debug tier",
            "error",
            2,
            ("UnknownError", "The operation timed out."),
            (),
            "and the highest tier does not decorate it differently either",
        ),
        (
            "a verbose read with display metadata",
            "read",
            1,
            ("c.py (lines 1-40 of 400)",),
            ("bytes", "byteSize", "KB", " B)"),
            "F-10: there is NO byte size in a read payload, so the cell reports the LINE RANGE and "
            "the total. The forbidden substrings pin that: a formatter inventing a byte size would "
            "be printing a number the event never carried",
        ),
        (
            "a verbose read with only input offsets",
            None,
            1,
            ("d.py (lines 10-30)",),
            (),
            "with no `display` metadata the range is DERIVED from `offset` and `limit` (10 + 20 = "
            "30), so the fallback reports a real range rather than nothing",
        ),
        (
            "a verbose grep",
            "grep",
            1,
            ("grep foo (7 hits)",),
            (),
            "F-10: grep's count lives in `metadata.matches`",
        ),
        (
            "a verbose glob",
            "glob",
            1,
            ("glob *.py (3 hits)",),
            (),
            "F-10: glob's count lives in `metadata.count`, a DIFFERENT field name from grep's. One "
            "lookup would silently miss one of the two, which is why both rows are here",
        ),
        (
            "a debug-tier edit shows the diff hunks",
            "edit",
            2,
            ("@@ -1 +1 @@", "+b"),
            (),
            "the debug tier appends the patch text itself, which is the only tier where the actual "
            "change is visible rather than just its shape",
        ),
        (
            "the SAME edit at the default tier hides the hunks",
            "edit",
            0,
            ("a.py (+1, -1)",),
            ("@@",),
            "the negative half of the row above: hunks at the default tier would bury the "
            "transcript in diff noise",
        ),
        (
            "the SAME edit at the verbose tier also hides the hunks",
            "edit",
            1,
            ("a.py (+1, -1)",),
            ("@@",),
            "hunks are a DEBUG-only escalation, so the middle tier must not leak them either",
        ),
        (
            "a debug-tier edit shows linter diagnostics",
            None,
            2,
            ("unused import",),
            (),
            "`metadata.diagnostics` is a SECOND debug-only escalation, independent of the patch "
            "hunks: an edit can carry diagnostics with an empty patch, so it needs its own rows",
        ),
        (
            "the SAME edit at the default tier hides the diagnostics",
            None,
            0,
            ("a.py (+1, -0)",),
            ("unused import",),
            "the negative half: linter chatter at the default tier would drown the transcript, and "
            "without this row the debug row above would pass against a renderer that always shows "
            "diagnostics",
        ),
    )

    def test_every_tier_renders_its_payload_and_suppresses_what_it_should(self):
        """One table over the per-tier payloads, replacing six near-identical tests.

        Each of the six rendered one event at one verbosity and asserted substrings were present
        (and sometimes that others were absent). VERBOSITY IS A COLUMN, which is the whole reason
        this is one table: the same `edit` event appears at all three tiers, and the claim that
        matters is not any single rendering but that raising the tier ADDS detail and never changes
        what was already there. Three separate tests cannot express a relationship between tiers;
        adjacent rows over the same event can.

        Why the table beats the six: one tier gate plus one per-tool formatter produces all of
        these, so a gate regression moves several rows together while the payload text stays
        correct, and a formatter regression does the opposite. Six tests report either as scattered
        red lines. The accumulated report shows which, and it reports the FORBIDDEN-substring
        failures in the same place, which is where the tier discipline actually lives: `@@` leaking
        into tier 0, or an invented byte size appearing in a read, are both "the wrong tier's detail
        escaped" rather than a wrong value.
        """
        wrong = []
        diagnostics_edit = _tool_event(
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
        literal_events = {
            "a verbose read with only input offsets": _tool_event(
                "read", input={"filePath": "/repo/d.py", "offset": 10, "limit": 20}
            ),
            "a debug-tier edit shows linter diagnostics": diagnostics_edit,
            "the SAME edit at the default tier hides the diagnostics": diagnostics_edit,
        }
        for case, key, level, needles, forbidden, why in self.TIER_PAYLOADS:
            event = self._events()[key] if key is not None else literal_events[case]
            line = render_stream.render_event(
                event, self.plain, verbosity=level, repo_root="/repo"
            )
            problems = []
            if line is None:
                problems.append(
                    "rendered NOTHING, so none of its content can be checked"
                )
            else:
                missing = [n for n in needles if n not in line]
                if missing:
                    problems.append(f"missing {missing!r} from {line!r}")
                leaked = [f for f in forbidden if f in line]
                if leaked:
                    problems.append(
                        f"leaked {leaked!r}, which this tier must NOT show; got {line!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (verbosity={level}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the per-tier payload is wrong for {len(wrong)} of {len(self.TIER_PAYLOADS)} rows. One "
            "tier gate plus one per-tool formatter produces all of them, so read the grouping. "
            "Rows for the SAME event at different tiers failing together means the gate changed; a "
            "single tool's rows failing at every tier means that formatter did. FIX: a LEAKED "
            "substring is the more interesting failure. `@@` appearing at tier 0 or 1 means debug "
            "detail escaped into the default transcript, and a byte-size token appearing in a read "
            "means the formatter is printing a number the event never carried (F-10). An ERROR row "
            f"rendering None is F-13 returning: a failing run would look silent.\n"
            + "\n".join(wrong),
        )

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
    """The statusline's SCALAR formatters: pure functions from a value to a fixed-width cell.

    Five tests became ONE table, and the merge is the clearest-cut in this module: each of the five
    was already a LOOP or a run of `assertEqual`s over a single pure function, so each was a
    hand-inlined table that reported only its FIRST wrong value and then stopped. Forty-nine rows
    across five formatters now report together.

    Why one table rather than five, given these are five different functions: they are five columns
    of the SAME statusline row, and the property that makes the statusline work is not any single
    value but that all five produce a cell of the width the box drawing assumes. The merged failure
    message is therefore able to say something no single-formatter test can, namely that N of 49
    cells moved across M formatters, which distinguishes a shared width-policy change from one
    formatter's rounding bug. The `formatter` column carries the function name, and `args` is a
    tuple so `format_progress_bar`'s two arguments sit in the same table as the one-argument
    formatters.

    WIDTH AND TRUNCATION ARE THE SUBJECT, not incidental to it, which is why the expected values are
    pinned as exact strings including their padding:
      * `format_progress_bar` right-aligns the counter to the width of `total`, which is why `0/5`
        has no leading space but ` 0/80` does. That is what keeps the bar from jittering horizontally
        as the run advances from item 9 to item 10. The 5-total and 80-total rows are both present
        for exactly that reason, and a regression that dropped the alignment would pass a table
        containing only one of them.
      * The percentage is right-aligned in three columns (`  0%`, ` 80%`, `100%`) for the same
        reason.
      * `format_compact_duration` zero-pads the seconds and minutes (`4m08s`, not `4m8s`) so the
        cell width is stable as time passes.
      * `format_action_label` and `format_artifact_kind_label` TRUNCATE to seven characters, which is
        why `Graduate` becomes `Graduat` and `Walkthrough` becomes `Walkthr`. Those rows look like
        typos and are not; they are the truncation contract, and they are labelled as such below so
        nobody "fixes" them.
    """

    #: (formatter name, args tuple, expected cell, why this row exists)
    SCALAR_CELLS = (
        # format_tokens: the long-form units used in the run summary.
        ("format_tokens", (0,), "0", "zero is bare, not '0.00'"),
        ("format_tokens", (500,), "500", "under 1000 stays an exact integer"),
        ("format_tokens", (1000,), "1.00K", "the K threshold, with two decimals"),
        ("format_tokens", (37480,), "37.48K", "a measured real token count"),
        ("format_tokens", (1_500_000,), "1.50M", "the M unit"),
        ("format_tokens", (2_500_000_000,), "2.50G", "the G unit, the largest handled"),
        # format_compact_tokens: the SHORTER spelling the statusline cell uses.
        (
            "format_compact_tokens",
            (0,),
            "0",
            "the compact spelling is a DIFFERENT function from format_tokens (lowercase unit, at "
            "most one decimal) because the statusline cell is narrower than the summary column",
        ),
        ("format_compact_tokens", (500,), "500", "under 1k stays exact"),
        (
            "format_compact_tokens",
            (1000,),
            "1k",
            "a whole thousand drops the decimal entirely rather than showing '1.0k'",
        ),
        (
            "format_compact_tokens",
            (4100,),
            "4.1k",
            "one decimal when it is significant",
        ),
        (
            "format_compact_tokens",
            (24500,),
            "24.5k",
            "two integer digits plus a decimal",
        ),
        ("format_compact_tokens", (88200,), "88.2k", "the widest k-range cell"),
        ("format_compact_tokens", (1_500_000,), "1.5m", "lowercase m, one decimal"),
        (
            "format_compact_tokens",
            (2_000_000_000,),
            "2g",
            "a whole billion drops the decimal, keeping the cell at two characters",
        ),
        # format_progress_bar: counter, bar, percentage. Width alignment is the point.
        (
            "format_progress_bar",
            (0, 0),
            "0/0  [          ]   0%",
            "a ZERO total must not divide by zero; it renders an empty bar at 0%",
        ),
        ("format_progress_bar", (0, 5), "0/5  [          ]   0%", "nothing done yet"),
        (
            "format_progress_bar",
            (4, 5),
            "4/5  [████████  ]  80%",
            "a partial bar fills whole blocks and pads the rest with spaces",
        ),
        (
            "format_progress_bar",
            (5, 5),
            "5/5  [██████████] 100%",
            "complete fills all ten cells and reads 100%",
        ),
        (
            "format_progress_bar",
            (0, 80),
            " 0/80  [          ]   0%",
            "WIDTH: the counter is right-aligned to the width of `total`, hence the LEADING SPACE "
            "before `0/80`. Without it the bar shifts sideways as the count gains a digit",
        ),
        (
            "format_progress_bar",
            (1, 80),
            " 1/80  [▏         ]   1%",
            "a fraction of one cell renders a PARTIAL block glyph, so 1 of 80 is visibly not zero",
        ),
        (
            "format_progress_bar",
            (40, 80),
            "40/80  [█████     ]  50%",
            "a two-digit counter needs NO leading space, which is the other half of the alignment "
            "claim the 0/80 row makes",
        ),
        (
            "format_progress_bar",
            (80, 80),
            "80/80  [██████████] 100%",
            "complete at the wider total",
        ),
        # format_compact_duration: zero-padded so the cell width never changes.
        (
            "format_compact_duration",
            (0,),
            "0m00s",
            "zero seconds still shows both fields",
        ),
        ("format_compact_duration", (45,), "0m45s", "under a minute keeps the 0m"),
        (
            "format_compact_duration",
            (248,),
            "4m08s",
            "WIDTH: the seconds are ZERO-PADDED (4m08s, not 4m8s) so the cell does not change "
            "width as the clock ticks past nine seconds",
        ),
        (
            "format_compact_duration",
            (64 * 60 + 21,),
            "1h04m21s",
            "over an hour the minutes are zero-padded too, for the same reason",
        ),
        ("format_compact_duration", (187 * 60 + 56,), "3h07m56s", "multiple hours"),
        (
            "format_compact_duration",
            (86400 + 3 * 3600 + 7 * 60 + 56,),
            "1d 3h07m56s",
            "over a day gains a `Nd ` segment; the hours are NOT zero-padded there",
        ),
        # format_action_label: case-normalized and TRUNCATED to seven characters.
        (
            "format_action_label",
            ("Review",),
            "Review",
            "already correct, passes through",
        ),
        ("format_action_label", ("review",), "Review", "lowercase is title-cased"),
        (
            "format_action_label",
            ("Execute",),
            "Execute",
            "the seven-character maximum, intact",
        ),
        (
            "format_action_label",
            ("exec",),
            "Execute",
            "an ABBREVIATION expands to the full label, so the queue's short form and the "
            "statusline agree",
        ),
        ("format_action_label", ("execute",), "Execute", "the full lowercase form"),
        (
            "format_action_label",
            ("Graduate",),
            "Graduat",
            "TRUNCATION, not a typo: eight characters are cut to seven so the column is fixed. Do "
            "not 'fix' this row to 'Graduate'",
        ),
        (
            "format_action_label",
            ("graduat",),
            "Graduat",
            "the already-truncated form is stable",
        ),
        (
            "format_action_label",
            ("Validate",),
            "Validat",
            "truncated, same rule as Graduate",
        ),
        ("format_action_label", ("validat",), "Validat", "stable under re-application"),
        (
            "format_action_label",
            ("orchestrate",),
            "Orchest",
            "the longest action, cut to seven",
        ),
        (
            "format_action_label",
            ("Orchestrate",),
            "Orchest",
            "case does not change the truncation",
        ),
        ("format_action_label", ("orchest",), "Orchest", "stable under re-application"),
        (
            "format_action_label",
            (None,),
            "Review",
            "NO action defaults to Review, the SAFE reading; defaulting to Execute would tell a "
            "watching human that a plan is being mutated when it may only be reviewed",
        ),
        # format_artifact_kind_label: same case-normalize-and-truncate policy, different vocabulary.
        (
            "format_artifact_kind_label",
            ("IPD",),
            "IPD",
            "an acronym stays UPPERCASE, not 'Ipd'",
        ),
        (
            "format_artifact_kind_label",
            ("ipd",),
            "IPD",
            "lowercase becomes the acronym",
        ),
        (
            "format_artifact_kind_label",
            ("plan",),
            "IPD",
            "`plan` is an ALIAS of IPD, so both spellings render one label",
        ),
        ("format_artifact_kind_label", ("Spec",), "Spec", "already correct"),
        ("format_artifact_kind_label", ("spec",), "Spec", "title-cased"),
        ("format_artifact_kind_label", ("Prompt",), "Prompt", "already correct"),
        ("format_artifact_kind_label", ("prompt",), "Prompt", "title-cased"),
        (
            "format_artifact_kind_label",
            ("Roadmap",),
            "Roadmap",
            "exactly seven characters",
        ),
        (
            "format_artifact_kind_label",
            ("roadmap",),
            "Roadmap",
            "title-cased at full width",
        ),
        (
            "format_artifact_kind_label",
            ("Walkthrough",),
            "Walkthr",
            "TRUNCATION again: eleven characters cut to seven. Not a typo",
        ),
        (
            "format_artifact_kind_label",
            ("walkthr",),
            "Walkthr",
            "stable under re-application",
        ),
        (
            "format_artifact_kind_label",
            ("Backlog",),
            "Backlog",
            "exactly seven characters",
        ),
        ("format_artifact_kind_label", ("backlog",), "Backlog", "title-cased"),
        (
            "format_artifact_kind_label",
            (None,),
            "IPD",
            "NO kind defaults to IPD, the overwhelmingly common artifact a run operates on",
        ),
    )

    def test_every_scalar_formatter_produces_its_exact_cell(self):
        wrong = []
        by_formatter = {}
        for name, args, expected, why in self.SCALAR_CELLS:
            got = getattr(render_stream, name)(*args)
            if got != expected:
                by_formatter[name] = by_formatter.get(name, 0) + 1
                width_note = ""
                if isinstance(got, str) and len(got) != len(expected):
                    width_note = (
                        f" [WIDTH CHANGED: {len(expected)} -> {len(got)} characters, so the "
                        "statusline box will not line up]"
                    )
                wrong.append(
                    f"  {name}{args!r}\n    expected {expected!r}\n    got      {got!r}"
                    f"{width_note}\n    this row exists because: {why}"
                )
        summary = ", ".join(
            f"{name} ({count})" for name, count in sorted(by_formatter.items())
        )
        self.assertEqual(
            wrong,
            [],
            f"the statusline scalar formatters produced the wrong cell for {len(wrong)} of "
            f"{len(self.SCALAR_CELLS)} values, across {len(by_formatter)} formatter(s): {summary}. "
            "These five functions are five COLUMNS of one statusline row, so read the grouping. "
            "Failures confined to ONE formatter are that formatter's own rounding or threshold "
            "bug. Failures spread across several, especially any marked WIDTH CHANGED, mean a "
            "shared width or padding policy moved, and the box-drawing row lengths asserted in "
            "`test_format_statusline_user_example_box_layout` will be failing too. FIX: before "
            "editing an expectation, check whether the row is a documented TRUNCATION (Graduat, "
            "Validat, Orchest, Walkthr) or a documented ZERO-PAD (4m08s) or the counter's "
            "right-ALIGNMENT (' 0/80'). Those rows look wrong and are the contract; changing them "
            f"to match new output silently narrows or widens the real terminal cell.\n"
            + "\n".join(wrong),
        )

    def test_format_statusline_exact_layout(self):
        """Kept separate: asserts the SEGMENTED structure of a rendered box (ten cells per line,
        border glyphs, equal widths), which is a structural decomposition rather than a data row."""
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
        """Kept separate: pins four WHOLE box lines byte-for-byte against a real user example."""

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
        """Kept separate: asserts a specific SGR sequence is present and that stripping preserves the
        four lines' equal widths, a cross-line invariant no scalar row expresses."""
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
        """Kept separate: exercises the Statusline object's stream writing, not a formatter mapping."""
        buf = io.StringIO()
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(pal, buf, interval=0)
        with st:
            st.write_event("  \u2022 Reading the plan.")
        self.assertEqual(buf.getvalue(), "  \u2022 Reading the plan.\n")

    def test_statusline_update_item_and_touch(self):
        """Kept separate: mutates a live Statusline then reads it back, a stateful sequence."""
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
        """Kept separate: identity (`assertIs`) checks over re-exported names, not value rows."""
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
        # `_STATUS_COLOR` IS DELIBERATELY ABSENT FROM THIS LIST (plan `qdd5jq` E-02, criterion A17).
        # It was the local lifecycle palette this module re-exported into both drivers; the re-export
        # chain is dismantled and the table is gone, so there is no object left to assert identity
        # over. `test_no_module_re_exports_a_lifecycle_palette` below is what replaced it, and it
        # asserts the stronger property: that no driver carries such a table at all.
        # The LIFECYCLE SEAM that took its place is re-exported and IS asserted, so the two drivers
        # still cannot fork their lifecycle resolution.
        self.assertIs(driver.activity_for_item, render_stream.activity_for_item)
        self.assertIs(agy_driver.activity_for_item, render_stream.activity_for_item)
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
        """Kept separate: reflects over `inspect.getmodule`, a structural claim about ownership."""
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
        """Kept separate: identity checks across two driver modules."""
        self.assertIs(agy_driver.Heartbeat, render_stream.Heartbeat)
        self.assertIs(driver.Heartbeat, render_stream.Heartbeat)

    def test_exactly_one_heartbeat_definition_in_the_package(self):
        """Kept separate: globs the package source; a whole-tree structural scan."""
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

    #: (the queue item dict, expected action, why this row exists)
    ITEMS = (
        (
            {"action": "execute", "status": "running"},
            "execute",
            "an EXPLICIT `action` wins outright. vaboqp: the column must derive from `action`, not "
            "from `status`, and this item carries a `status` that would resolve differently",
        ),
        (
            {"action": "review", "status": "running"},
            "review",
            "the same precedence for the other common action, against the same misleading status",
        ),
        (
            {"action": "orchestrate", "status": "queued"},
            "orchestrate",
            "an orchestrator's action survives too, so a parent is not displayed as executing work "
            "it does not perform",
        ),
        (
            {"initial_status": "to-review"},
            "review",
            "with no explicit action, `initial_status` decides: a plan awaiting review is REVIEWED",
        ),
        (
            {"initial_status": "draft"},
            "review",
            "a draft is also reviewed, not executed; executing a draft is the mistake this row "
            "guards against being displayed as normal",
        ),
        (
            {"initial_status": "approved"},
            "execute",
            "approved is the ONE status that implies execution, which is what makes the two rows "
            "above meaningful rather than a blanket default",
        ),
        (
            {"status": "to-review"},
            "review",
            "`status` is consulted only when `initial_status` is absent too, so the fallback chain "
            "has three levels rather than two",
        ),
        (
            {},
            "execute",
            "an EMPTY item defaults to execute. Asserted so the default is a deliberate recorded "
            "choice rather than whatever the last branch happened to return",
        ),
        (
            {"action": None, "initial_status": "approved"},
            "execute",
            "an action explicitly set to None must FALL THROUGH to the status rather than being "
            "treated as a present-but-empty action, which would render a blank column",
        ),
    )

    def test_every_queue_item_shape_resolves_to_its_action(self):
        """One table over the action-derivation fallback chain, replacing two tests.

        The two old tests split these nine items into "explicit" and "fallback" groups, each a run
        of sequential `assertEqual`s that stopped at its first failure. The split was arbitrary:
        both were asking the same pure function the same question, and the explicit rows exist
        precisely to show they OUTRANK the fallback rows, a relationship neither test could state.

        Why the table beats the two: this is one precedence chain (`action`, else `initial_status`,
        else `status`, else the default), and the realistic failure is that chain being reordered or
        a level being skipped, which moves several rows at once in a legible pattern. The
        accumulated report shows that pattern; two tests showed two red lines whose relationship
        had to be guessed.
        """
        wrong = []
        for item, expected, why in self.ITEMS:
            got = render_stream.statusline_action_for_item(item)
            if got != expected:
                wrong.append(
                    f"  {item!r}\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"statusline_action_for_item resolved {len(wrong)} of {len(self.ITEMS)} queue items "
            "wrongly. One precedence chain (`action`, else `initial_status`, else `status`, else "
            "the default) decides all of them, so several rows moving together means that chain was "
            "reordered. FIX: if the EXPLICIT rows now follow their `status` instead of their "
            "`action`, this is vaboqp regressing and the statusline is describing the wrong "
            "activity to a watching human. If a review row now reads `execute`, the display claims "
            "a plan is being MUTATED when it is only being read, which is the more alarming "
            f"direction of error.\n" + "\n".join(wrong),
        )

    def test_queue_item_renders_execute_action_in_statusline(self):
        """Kept separate: renders a real Statusline end to end, not the pure derivation the table covers."""
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


class StatuslinePauseResumeTests(unittest.TestCase):
    def test_pause_and_resume_do_not_deadlock_when_drawn(self):
        """Kept separate: a stateful pause/resume sequence over a faked-tty stream."""
        stream = io.StringIO()
        stream.isatty = lambda: True  # type: ignore[attr-defined]
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(
            pal=pal,
            stream=stream,
            interval=0,
            setid="testset",
            id6="item01",
        )
        st.redraw()
        self.assertTrue(st._has_drawn)

        st.pause()
        self.assertTrue(st._paused)
        self.assertFalse(st._has_drawn)

        st.resume()
        self.assertFalse(st._paused)
        self.assertTrue(st._has_drawn)

    def test_global_pause_resume_active_statusline(self):
        """Kept separate: exercises the MODULE-level pause/resume registry, not a value mapping."""
        stream = io.StringIO()
        stream.isatty = lambda: True  # type: ignore[attr-defined]
        pal = render_stream.Palette(False)
        st = render_stream.Statusline(
            pal=pal,
            stream=stream,
            interval=0,
            setid="testset",
            id6="item01",
        )
        with st:
            st.redraw()
            self.assertTrue(st._has_drawn)
            render_stream.pause_active_statusline()
            self.assertTrue(st._paused)
            render_stream.resume_active_statusline()
            self.assertFalse(st._paused)


if __name__ == "__main__":
    unittest.main()

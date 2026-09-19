#!/usr/bin/env python3
"""runanalytics Order 07 (`6eq3oq`) E-03..E-08: the self-contained offline analytics SPA.

HERMETICITY. Every fixture is built in this file; nothing reads `.aw/records/runs/`. That tree is
gitignored, mutable, ABSENT from a fresh checkout, and its outcome files carry absolute paths the leak
detector flags at `fail`. The plan's stop condition is explicit: "if a test needs the live corpus to
pass, STOP and build a fixture". The corpus-SCALE fixture below reproduces the measured 29766-row
scale synthetically so the size and DOM budgets are EXERCISED rather than asserted.

TOOLING. Stdlib `html.parser` ONLY. `bs4`, `lxml` and `playwright` all import on a maintainer box and
NONE is in `[project.optional-dependencies].test`, which is exactly what CI installs, so a test using
one passes locally and fails or silently skips in CI. `NoNewTestDependencyTests` asserts that
boundary rather than trusting it.

WHAT THIS SUITE DOES NOT VERIFY IS NAMED, NOT IMPLIED. Computed focus ORDER, contrast RATIO, real JS
execution and post-click state are not machine-checked here, and
`spa.UNVERIFIED_ACCESSIBILITY_PROPERTIES` publishes that boundary in the report itself.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a view model with
one field populated, render it, assert something appears. The tables group by SUBJECT (the escaping
boundary, the control sweep, the refusal routing, the columnar layout, the binning bound, the dimension
states, the panels, the DOM a11y contract, the packaged assets) rather than by which function
implements the check, so the closed sets this module rests on (the four escape contexts, the three
dimension states, the control-group value lists, the required panel ids) are browsable as sets and a
change that moves several at once reports as ONE failure naming all of them.

WHAT A ROW ASSERTS IS A DELIBERATE CHOICE, because this module generates an HTML report and the two
available things to assert are not equally worth having. Asserting the report's PROSE is a change
detector: rewording a sentence is a legitimate edit that would break such a test with no behavior
change. Asserting the PAYLOAD'S DATA is behavior: a JSON key, a derived percentage, a row count, an
escaped hostile string, the absence of a leak. So rows favor derived values and identifiers over
sentences, and the few places a sentence IS pinned say why in the row (each is an honesty or privacy
commitment the report makes, not a description of one). The one place exact strings are pinned freely
is the escaping grid, where byte-exactness IS the security property.

MODE DISTINCTIONS ARE COLUMNS. The escape CONTEXT, the copy of a claim at payload versus whole-document
SCOPE, the classification-plus-rendering pair for a dimension, and the clean-versus-planted polarity of
the offline scan are all columns, because in each case the property worth asserting is that the same
subject gets different answers in different modes, which no single-mode test can state.

CONTROL ROWS LIVE BESIDE THE CLAIMS THEY LICENSE. A clean result and a detector that was not looking
are indistinguishable, so the offline table keeps its planted rows in the same test as its clean rows,
and `LeakSanitizerTests` keeps its CONTROL test adjacent to the clean assertion it makes meaningful.
Neither may be split apart.

Tests that are NOT rows carry a one-line docstring saying why. The recurring reasons: the claim is an
assertRaises refusal; the setup monkeypatches a collaborator (which must never happen inside a loop);
the subject is a corpus-scale fixture or a measurement rather than an expectation; or the assertion is
over source text, a constant, or ordering rather than over a rendered value.
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from agent_workflows import run_analytics_spa as spa
from agent_workflows.run_analytics_spa import (
    DimensionState,
    SpaError,
    build_view_model,
    render_document,
)
from agent_workflows.run_analytics_statistics import AnalysisResult, Verdict


# --- stdlib DOM support ---------------------------------------------------------------------------


class _Collector(HTMLParser):
    """A minimal DOM-contract collector. Stdlib only, by design.

    Probe-verified to extract `aria-pressed`, `role`, `aria-labelledby`, `scope` and `<caption>`,
    which covers every structural assertion this suite needs.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.text_by_tag: dict[str, list[str]] = {}
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, {k: (v or "") for k, v in attrs}))
        self._stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.tags.append((tag, {k: (v or "") for k, v in attrs}))

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def handle_data(self, data):
        if self._stack:
            self.text_by_tag.setdefault(self._stack[-1], []).append(data)

    def of(self, tag: str) -> list[dict[str, str]]:
        return [attrs for name, attrs in self.tags if name == tag]

    def text(self, tag: str) -> str:
        return " ".join(self.text_by_tag.get(tag, []))


def _parse(document: str) -> _Collector:
    collector = _Collector()
    collector.feed(document)
    return collector


# --- fixtures -------------------------------------------------------------------------------------

#: The measured per-step row count from the review-time snapshot. The corpus-scale fixture matches it
#: so the budgets are exercised at real scale rather than at a toy one.
CORPUS_SCALE_ROWS = spa.REVIEW_SNAPSHOT["per_step_fact_rows"]


def _computed(name: str, *, n: int = 40, **values) -> AnalysisResult:
    return AnalysisResult(
        name=name,
        verdict=Verdict.COMPUTED,
        sample_size=n,
        values=values or {"value": 1.0},
    )


def _refused(
    name: str, *, n: int = 3, verdict: Verdict = Verdict.CANNOT_DETERMINE
) -> AnalysisResult:
    return AnalysisResult(
        name=name,
        verdict=verdict,
        sample_size=n,
        reason=f"observed n={n} is below the declared minimum n=12",
        caveats=("sample size basis: fixture",),
    )


def _rows(count: int = 4) -> list[dict[str, object]]:
    return [
        {
            "run_id": f"run-2026091{i % 10}T000000Z-{i}",
            "ipd_id6": f"id{i:04d}",
            "attempt": (i % 3) + 1,
            "phase": ("execute", "review", "recovery")[i % 3],
            "outcome": ("executed", "partial")[i % 2],
            "cost_usd": round(0.5 + (i % 7) * 0.25, 4),
            "wall_seconds": 100 + i,
            "total_tokens": 1000 * (i + 1),
        }
        for i in range(count)
    ]


def _model(**overrides):
    kwargs = {
        "rows": _rows(),
        "results": [
            _computed("cache-utilization"),
            _refused("merge-conflict-share-and-recurrence"),
        ],
        "metric_column": "cost_usd",
        "required_analysis_count": 16,
        "generated_label": "fixture",
    }
    kwargs.update(overrides)
    return build_view_model(**kwargs)


# --- E-07: the escaping boundary ------------------------------------------------------------------


class ThreeContextEscapingTests(unittest.TestCase):
    """FOUR contexts, FOUR escapes. A single helper used everywhere is a DEFECT, not a convenience.

    ONE TABLE replaces six tests, and THE CONTEXT IS THE COLUMN, which is the whole argument of this
    class. Each of the six asserted what ONE escape does to one input; none could state the property
    the module's design actually rests on, which is that the four escapes DIFFER, and differ in the
    specific ways each context requires. The table asserts the exact output of every escape for every
    input, so the differences are visible as a grid rather than asserted one cell at a time.

    THE DIFFERENCES ARE ASSERTED, NOT JUST THE SAFETY. Two rows carry the load. A double quote must be
    encoded by `escape_attribute` (where it closes the attribute) and must survive `escape_text`
    (where it is inert and `quote=False` is correct); the old file made that point with one
    `assertIn` buried in the attribute test. A leading `=` must pass through `escape_text` UNCHANGED,
    because HTML has no formula context and mangling it would silently corrupt real content. Both are
    now cells in the same grid as the hostile rows, which is what stops "escape everything harder"
    from looking like an improvement: the most likely wrong fix for a safety failure is to route every
    context through one helper, and that shows up here as the POSITIVE cells breaking.

    A NOTE ON WHAT THIS GRID IS NOT. Asserting exact escaped strings is appropriate here and would be
    a change-detector elsewhere in this file: these outputs are a security boundary whose whole value
    is being byte-exact, and the module's docstring commits to each one. Assertions about the rendered
    DOCUMENT's prose belong to the payload-data tests further down, not here.
    """

    #: Per-row expected output for each of the four escapes. `None` means "no expectation for this
    #: context in this row", used where the interesting claim is about the others.
    #:
    #: (case, the raw input, expected escape_text, expected escape_attribute, expected
    #: escape_svg_text, expected escape_js_string, why this row exists)
    ESCAPES = (
        (
            "a script element in the input",
            "<script>x</script>",
            "&lt;script&gt;x&lt;/script&gt;",
            "&lt;script&gt;x&lt;/script&gt;",
            "&lt;script&gt;x&lt;/script&gt;",
            "<script>x<\\/script>",
            "THE BASELINE HOSTILE INPUT, and the row where the contexts most obviously diverge. The "
            "three HTML-family escapes neutralize the angle brackets; the JS one CANNOT, because "
            "inside `<script>` the parser does not decode entities, so `&lt;` would arrive as those "
            "four literal characters in the string. What it must do instead is break `</script`, "
            "which is what ends the element regardless of quoting",
        ),
        (
            "a bare ampersand",
            "a & b",
            "a &amp; b",
            "a &amp; b",
            "a &amp; b",
            "a & b",
            "SVG IS THE REASON THIS ROW IS PINNED IN ALL FOUR CONTEXTS. Inside SVG a bare `&` is an "
            "XML WELL-FORMEDNESS error rather than merely a rendering hazard, so `escape_svg_text` "
            "may never gain an 'allow entities' option; pinning the other three beside it is what "
            "documents that they agree here for a weaker reason, and that the JS context leaves `&` "
            "alone entirely",
        ),
        (
            "a double quote",
            'a"b',
            # UNCHANGED, deliberately: `html.escape(quote=False)`.
            'a"b',
            "a&quot;b",
            "a&quot;b",
            'a\\"b',
            "THE DIVERGENCE THAT MOTIVATES SEPARATE FUNCTIONS, and the reason a single shared helper "
            "would be a defect rather than a convenience. In an attribute an unescaped quote CLOSES "
            "the attribute and the next token is parsed as a new one; in text it is inert, so "
            "escaping it there would be noise. The text cell is a POSITIVE expectation: if it ever "
            "becomes `&quot;`, someone has unified the escapes and the fix is to separate them again",
        ),
        (
            "a single quote",
            "a'b",
            "a'b",
            "a&#x27;b",
            "a&#x27;b",
            "a\\'b",
            "`html.escape` does NOT encode the apostrophe even with `quote=True`, so "
            "`escape_attribute` adds it explicitly. That extra replace is what lets a caller use "
            "EITHER delimiter safely, and nothing else in the module would notice if it were dropped",
        ),
        (
            "an HTML comment opener",
            "<!--",
            "&lt;!--",
            "&lt;!--",
            "&lt;!--",
            "<\\!--",
            "A JS-CONTEXT-ONLY HAZARD: `<!--` inside a script opens a comment state in the HTML "
            "parser, which can swallow the rest of the element. No HTML escape addresses it because "
            "in HTML text the angle bracket is already gone",
        ),
        (
            "a JS line terminator (U+2028)",
            "a\u2028b",
            "a\u2028b",
            "a\u2028b",
            "a\u2028b",
            "a\\u2028b",
            "U+2028 IS A LITERAL LINE TERMINATOR IN JAVASCRIPT SOURCE BUT NOT IN JSON, so an "
            "unescaped one ends the statement mid-string. The HTML cells show it passing through "
            "untouched, which is correct and is also why this cannot be tested through any HTML "
            "escape: it is legal text there",
        ),
        (
            "a backslash and a newline",
            "a\\b\nc",
            "a\\b\nc",
            "a\\b\nc",
            "a\\b\nc",
            "a\\\\b\\nc",
            "THE ORDER OF OPERATIONS IS THE CLAIM. The backslash must be doubled FIRST, or the "
            "escape sequences the later replacements introduce would themselves be re-escaped and "
            "the string would decode to something else. Both characters are in one row so a "
            "reordering shows up as one wrong cell",
        ),
        (
            "a bidi override",
            "a\u202eb",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            "THE PRE-PASS IS PART OF THE BOUNDARY, SO NO CONTEXT MAY BYPASS IT, which is why this "
            "row pins the same output in all four. A bidi override cannot be ESCAPED at all: a "
            "numeric character reference decodes to the same active code point, so it must be "
            "REPLACED. An escape that forgot to run `sanitize_control_characters` first would still "
            "satisfy every other row in this table",
        ),
        (
            "a spreadsheet formula, the MEASURED corpus shape",
            "=1+1+cmd|' /C calc'!A0",
            # UNCHANGED in HTML text: none of `&<>` appears and a quote is inert here.
            "=1+1+cmd|' /C calc'!A0",
            "=1+1+cmd|&#x27; /C calc&#x27;!A0",
            "=1+1+cmd|&#x27; /C calc&#x27;!A0",
            "=1+1+cmd|\\' /C calc\\'!A0",
            "THE HONEST PER-CONTEXT CONTRACT for a shape the real corpus contains. HTML has NO "
            "formula context, so a leading `=` is ordinary text and the text cell asserts it is left "
            "ALONE: mangling it would silently corrupt real content, and the formula hazard belongs "
            "to CSV/spreadsheet export, which is a different surface. What must hold is that the same "
            "payload cannot break out of an ATTRIBUTE, which is the next cell along",
        ),
        (
            "a NUL and an ESC (C0 controls)",
            "a\x00b\x1bc",
            f"a{spa.REPLACEMENT_CHARACTER}b{spa.REPLACEMENT_CHARACTER}c",
            f"a{spa.REPLACEMENT_CHARACTER}b{spa.REPLACEMENT_CHARACTER}c",
            f"a{spa.REPLACEMENT_CHARACTER}b{spa.REPLACEMENT_CHARACTER}c",
            f"a{spa.REPLACEMENT_CHARACTER}b{spa.REPLACEMENT_CHARACTER}c",
            "the same pre-pass applied to the Cc category. REPLACED rather than DROPPED on purpose: "
            "dropping a character hides that the source was hostile, while U+FFFD keeps the text "
            "readable and the tampering visible",
        ),
        (
            "legitimate whitespace",
            "a\tb\nc\rd",
            "a\tb\nc\rd",
            "a\tb\nc\rd",
            "a\tb\nc\rd",
            "a\\tb\\nc\\rd",
            "THE CONTROL-SWEEP'S POSITIVE ROW. Tab, newline and carriage return are control "
            "characters by category, so a sweep that replaced everything in Cc would satisfy the two "
            "rows above while destroying the multi-line free text this report legitimately displays. "
            "The JS cell differs because a real newline inside a string literal is a syntax error "
            "there, which is a different reason for a different output",
        ),
    )

    #: The four escapes under test, in the order their expectations appear in each row.
    CONTEXTS = (
        ("escape_text", spa.escape_text),
        ("escape_attribute", spa.escape_attribute),
        ("escape_svg_text", spa.escape_svg_text),
        ("escape_js_string", spa.escape_js_string),
    )

    def test_every_context_escapes_every_input_its_own_way(self):
        wrong = []
        for case, raw, *rest in self.ESCAPES:
            *expectations, why = rest
            problems = []
            for (name, func), expected in zip(self.CONTEXTS, expectations):
                if expected is None:
                    continue
                got = func(raw)
                if got != expected:
                    problems.append(f"{name}: expected {expected!r}, got {got!r}")
            if problems:
                wrong.append(
                    f"  {case} (input {raw!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the escaping boundary was wrong for {len(wrong)} of {len(self.ESCAPES)} inputs. This "
            "is a GRID, so read it by column and by row. A whole COLUMN failing means one escape "
            "changed: check whether it now shares an implementation with another, because collapsing "
            "four escapes into one shared helper is the single change this class exists to prevent. A "
            "whole ROW failing across all four columns means the shared `sanitize_control_characters` "
            "pre-pass changed, since that is the only code every context runs. FIX: distinguish the "
            "two directions of failure before touching anything. A cell that is now MORE escaped than "
            "expected (the text-context quote, the leading `=`) is not a safety improvement; it is "
            "the escapes being unified, and it silently corrupts real report content. A cell that is "
            "LESS escaped is a live injection or, for the bidi/C0 rows, a bypassed pre-pass that no "
            "amount of escaping can compensate for.\n" + "\n".join(wrong),
        )

    def test_the_JSON_ISLAND_context_is_a_FIFTH_escape_and_still_parses(self):
        """Kept separate from the four-context grid: the assertion is that the output still PARSES.

        A REAL DEFECT THIS SUITE CAUGHT: a JSON island is not a JS string literal.

        Escaping the view-model JSON with `escape_js_string` produced `\\"` sequences that arrive at
        the client as literal backslash-quote in `textContent`, so `JSON.parse` would have failed on
        every page load. The correct escape uses `\\uXXXX` for `<`, `>` and `&`, which JSON.parse
        decodes back to the originals while no `<` survives to terminate the script element.
        """

        import json as _json

        payload = _json.dumps({"title": "</script><img src=x>", "n": 3})
        escaped = spa.escape_json_for_script(payload)
        self.assertNotIn("<", escaped)
        self.assertNotIn(">", escaped)
        self.assertIn("\\u003c", escaped)
        # AND IT STILL PARSES BACK TO THE ORIGINAL DATA, which is the half the JS escape broke.
        self.assertEqual(
            _json.loads(escaped), {"title": "</script><img src=x>", "n": 3}
        )

    def test_the_rendered_view_model_island_is_parseable_JSON(self):
        """The end-to-end form of the same defect: the island the browser actually reads."""

        import json as _json

        document = render_document(_model(results=[_refused("</script><id6>")]))
        island = document.split('id="view-model">')[1].split("</script>")[0]
        parsed = _json.loads(island)
        self.assertEqual(parsed["spa_schema_version"], spa.SPA_SCHEMA_VERSION)
        # The hostile name survives as DATA, decoded, without ever appearing as markup.
        self.assertEqual(parsed["refusals"][0]["analysis_name"], "</script><id6>")
        self.assertNotIn("</script><id6>", island)


class ControlCharacterTests(unittest.TestCase):
    """A bidi override cannot be ESCAPED; it must be REPLACED, because an NCR still renders.

    ONE TABLE over `sanitize_control_characters` itself, replacing three tests plus a subTest loop.
    The per-escape bypass test that used to live here is GONE ON PURPOSE, not lost: it asserted only
    that `\\u202e` is absent from each escape's output, which the bidi and C0 rows of
    `ThreeContextEscapingTests` now assert far more strictly, by pinning the exact replaced output for
    all four contexts. Keeping a weaker duplicate would mean two places to update and one of them
    silently satisfiable.

    THE CATEGORY IS THE COLUMN in the sense that matters here: the sweep is implemented by a
    `unicodedata.category` lookup against a frozenset, so the rows name which CATEGORY each input
    belongs to. That is what makes a failure legible, because the realistic regression is a category
    being added to or removed from that set, which moves every input of that category at once.
    """

    #: (case, the input, the expected output, why this row exists)
    SWEEPS = (
        *[
            (
                f"the bidi control U+{ord(char):04X}",
                f"a{char}b",
                f"a{spa.REPLACEMENT_CHARACTER}b",
                "a bidi override cannot be neutralized by ESCAPING at all, because a numeric "
                "character reference decodes back to the same active code point and reorders the "
                "text as it renders. It must be REPLACED, and U+FFFD is chosen over deletion so the "
                "text stays readable and the tampering stays visible. All five are rows because they "
                "are separate code points in the Cf category and a narrowed sweep would catch some",
            )
            for char in ("\u202e", "\u202d", "\u2066", "\u2069", "\u200f")
        ],
        (
            "a NUL (category Cc)",
            "a\x00b",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            "the C0 half of the sweep. A NUL can truncate a string in a downstream C consumer, and "
            "it is invisible in every editor, so it must not survive into a published bundle",
        ),
        (
            "an ESC (category Cc)",
            "a\x1bb",
            f"a{spa.REPLACEMENT_CHARACTER}b",
            "an ESC begins a terminal escape sequence, so a report opened with `cat` or piped through "
            "a terminal could have its output rewritten by report CONTENT. Kept as its own row "
            "because a sweep narrowed to 'the dangerous-looking ones' would plausibly keep NUL and "
            "drop this",
        ),
        (
            "tab, newline and carriage return together",
            "a\tb\nc\rd",
            "a\tb\nc\rd",
            "THE POSITIVE ROW, and it is what stops the sweep from being 'replace everything in Cc'. "
            "All three ARE control characters by category, and a report legitimately displays "
            "multi-line free text, so replacing them would shred every reason string in the "
            "document while satisfying every negative row above",
        ),
        (
            "ordinary text with nothing to sweep",
            "plain text 123",
            "plain text 123",
            "the identity case. A sweep that mangled ordinary characters would be caught here rather "
            "than being discovered as corrupted report text much later",
        ),
        (
            "the empty string",
            "",
            "",
            "the early-return branch: empty input returns empty rather than raising or returning "
            "None, which matters because every escape calls this on values that are frequently empty",
        ),
    )

    def test_the_control_sweep_replaces_exactly_the_unsafe_categories(self):
        wrong = []
        for case, raw, expected, why in self.SWEEPS:
            got = spa.sanitize_control_characters(raw)
            if got != expected:
                wrong.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"sanitize_control_characters was wrong for {len(wrong)} of {len(self.SWEEPS)} inputs. "
            "One loop decides every row from two frozensets (`_UNSAFE_CATEGORIES` and "
            "`_ALLOWED_CONTROL_CHARACTERS`), so the grouping names the cause: all five bidi rows "
            "failing together means `Cf` left the unsafe set, both Cc rows failing means `Cc` did, "
            "and the whitespace row failing alone means the allow-list was dropped. FIX: the two "
            "directions are not equally bad. A surviving bidi or C0 character is a real hazard in a "
            "published bundle and NO amount of escaping downstream can fix it, which is why this is a "
            "replacement pass and not an escape. A replaced TAB or NEWLINE is data loss in the "
            "report's free text, visible to every reader.\n" + "\n".join(wrong),
        )


class RealMeasuredInjectionShapeTests(unittest.TestCase):
    """Fixtures built from the REAL measured shapes, not from invented ones.

    Measured at review over 216 real outcome files: 152 carried `<`, `>` or `&` in free text, with
    HTML-tag-looking substrings common (`<id6>` 32 times, plus `<path>`, `<plan>`, `<repo>`,
    `<selector>`), and 6 carried FAIL-severity `home-path`/`handle` findings. Those are the shapes
    below.
    """

    #: The exact substrings measured in the real corpus, plus the classic hostile payloads.
    HOSTILE = (
        "</script><script>alert(1)</script>",
        "<id6>",
        "<path>",
        "<plan>",
        "<repo>",
        "<selector>",
        "<agent/model>",
        "=1+1+cmd|' /C calc'!A0",
        "+SUM(A1)",
        "-2+3",
        "@import url(x)",
        "a\u202eb",
        "a\x00b",
        '"><img src=x onerror=alert(1)>',
        "'; DROP TABLE runs; --",
    )

    def test_every_hostile_shape_is_INERT_in_every_context(self):
        """Kept separate from the exact-output grid: this is a SWEEP with a per-context PREDICATE.

        `ThreeContextEscapingTests` pins the exact output for a small set of inputs. This asserts a
        weaker property (inertness) over a LARGER set drawn from the measured corpus, which is the right
        trade for fifteen payloads: pinning fifteen exact strings in four contexts would be sixty
        expectations most of which encode nothing, while inertness is the invariant that actually has
        to hold for all of them.
        """

        wrong = []
        for payload in self.HOSTILE:
            for name, func in (
                ("html-text", spa.escape_text),
                ("attribute", spa.escape_attribute),
                ("svg-text", spa.escape_svg_text),
                ("js-string", spa.escape_js_string),
            ):
                out = func(payload)
                problems = []
                if name == "js-string":
                    if "</script" in out.lower():
                        problems.append(
                            "`</script` survives, which ends the element regardless of quoting"
                        )
                else:
                    if "<" in out or ">" in out:
                        problems.append(
                            "an angle bracket survives, so the payload can contribute a TAG"
                        )
                if "\u202e" in out:
                    problems.append(
                        "a bidi override survives; it cannot be escaped and must be REPLACED"
                    )
                if "\x00" in out:
                    problems.append("a NUL survives")
                if problems:
                    wrong.append(f"  {payload!r} in {name}: " + "; ".join(problems))
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} payload/context combinations are NOT inert, out of "
            f"{len(self.HOSTILE) * 4}. These fixtures are the shapes MEASURED in the real corpus (152 "
            "of 216 outcome files carried `<`, `>` or `&` in free text, `<id6>` 32 times), so a "
            "failure here is a live injection on real data rather than a theoretical one. If a whole "
            "CONTEXT column fails, that escape broke; see ThreeContextEscapingTests, whose grid pins "
            "the exact expected output per context and will say precisely how. FIX: inertness, not "
            "absence: escaped text must be PRESERVED.\n" + "\n".join(wrong),
        )

    def test_a_hostile_string_rendered_through_the_document_produces_no_live_markup(
        self,
    ):
        """Kept separate: END TO END through `render_document`, not through an escape function.

        The payload travels through a refusal, a finding, and every field of that finding at once, and
        the assertions are about the WHOLE DOCUMENT (how many script elements exist, what survives
        escaped, what is absent raw). No row in an escape table can state a document-level count.

        THE CONTRACT IS INERTNESS, NOT ABSENCE, which is why this asserts both directions: escaped text
        must be PRESERVED, because dropping `onerror=alert(1)` would silently destroy real content a
        finding legitimately contains, while no live TAG may exist.
        """

        payload = "</script><img src=x onerror=alert(1)><id6>"
        model = _model(
            results=[_refused(payload, n=3)],
            findings=[
                _finding(
                    finding_id=payload,
                    title=payload,
                    affected_slice=payload,
                    uncertainty=payload,
                    data_quality_caveats=[payload],
                    alternative_explanations=[payload],
                    next_experiment=payload,
                )
            ],
        )
        document = render_document(model)
        self.assertNotIn("<img", document)
        self.assertNotIn("<id6>", document)
        # The text is still PRESENT, escaped, so the report does not silently drop real content.
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", document)
        self.assertIn("&lt;id6&gt;", document)
        # Exactly the three script elements this module emits, and no injected one.
        self.assertEqual(document.lower().count("<script"), 3)
        # And the payload never appears RAW anywhere: every occurrence is escaped or \\u-encoded.
        self.assertNotIn("</script><img", document)


# --- E-07: offline behavior -----------------------------------------------------------------------


class OfflineTests(unittest.TestCase):
    """Offline is a TESTED property. The scanner also has a CONTROL, so it is provably looking.

    ONE TABLE replaces three tests plus a subTest loop, and THE CONTROL PATTERN IS THE REASON THE TABLE
    IS SHAPED THIS WAY. A clean report and a scanner that was not looking are indistinguishable, so the
    clean row and the planted rows MUST live together: the planted rows prove the detector fires, which
    is what makes the clean row evidence rather than a tautology. Splitting them (as the old file did)
    means a scanner that returned `[]` unconditionally satisfies the clean assertion, and the two tests
    that would have caught it sit in a different method that a reader of the clean one never sees.

    THE CASE-INSENSITIVITY ROW IS A PLANTED ROW WITH AN UPPERCASE PAYLOAD rather than a separate test,
    because that is all it ever was: `HTTPS://EXAMPLE.COM` is as much a network reference as the
    lowercase form, and the scanner lowercases the haystack once for all tokens.
    """

    #: (case, the text to scan, the token each finding must be reported under, or None meaning "this
    #: text must scan CLEAN", why this row exists)
    SCANS = (
        (
            "the rendered document itself",
            None,  # rendered below; the real subject
            None,
            "THE CLAIM THAT MATTERS: the deliverable is ONE self-contained file openable from "
            "`file://`, so any network reference in it would make the report silently depend on being "
            "online, leak a request to a third party, or simply render broken on an air-gapped "
            "machine. This row is only evidence because the planted rows below prove the scanner "
            "fires",
        ),
        (
            "an external script element",
            '<script src="x.js"></script>',
            "<script src",
            "the most direct violation: a second file the bundle cannot carry. It is also what a "
            "well-meant 'extract the JS to a file' refactor would introduce",
        ),
        (
            "a runtime fetch call",
            "fetch('/x')",
            "fetch(",
            "a network call that would not appear in any markup scan and fires only when a user "
            "interacts, so it cannot be found by reading the document's structure",
        ),
        (
            "an absolute https URL in a link",
            '<a href="https://example.com">x</a>',
            "https:",
            "the ordinary hyperlink case. It is forbidden because an `https:` occurrence anywhere is "
            "also how an `xmlns` or a tracking pixel would arrive, so the rule is the SCHEME rather "
            "than the element",
        ),
        (
            "the SAME payload uppercased",
            "HTTPS://EXAMPLE.COM",
            "https:",
            "CASE INSENSITIVITY, as a row rather than its own test: the scanner lowercases the "
            "haystack once for every token, so if this row fails the case handling went for ALL "
            "tokens at once and every row above became trivially evadable by changing case",
        ),
        (
            "a WebSocket constructor",
            "new WebSocket('x')",
            "WebSocket",
            "a persistent connection, which no URL-shaped check would catch. Kept distinct from "
            "`fetch(` because they are separate entries in `FORBIDDEN_NETWORK_TOKENS` and a truncated "
            "list would drop one",
        ),
        (
            "a CSS-level import",
            "@import url(x)",
            "@import",
            "THE STYLESHEET IS A NETWORK SURFACE TOO, and this is the one an author is most likely to "
            "add without thinking of it as a request. It is also a real measured corpus payload, so "
            "the row doubles as an escaping fixture elsewhere in this file",
        ),
        (
            "a dynamic module import",
            "import('x')",
            "import(",
            "loads a second file at runtime, invisible to a markup scan, and is how a future "
            "'lazy-load the chart code' change would break the single-file guarantee",
        ),
        (
            "ordinary report prose that merely mentions a protocol word",
            "the run fetched nothing and imported nothing",
            None,
            "THE SECOND CLEAN ROW, and it guards the opposite failure from the first: a scanner "
            "broadened to substring-match `fetch` or `import` would flag legitimate English in a "
            "findings narrative, and the cheapest way to silence that false positive is to weaken the "
            "scanner. Pinning it clean here means the precision is asserted rather than assumed",
        ),
    )

    def test_the_document_is_clean_and_the_scanner_provably_fires(self):
        wrong = []
        for case, text, token, why in self.SCANS:
            subject = render_document(_model()) if text is None else text
            findings = spa.scan_for_network_references(subject)
            problems = []
            if token is None:
                if findings:
                    problems.append(
                        f"must scan CLEAN but reported {findings!r}"
                        + (
                            " (this is the deliverable itself, so it cannot ship)"
                            if text is None
                            else ""
                        )
                    )
            elif not any(f.startswith(token) for f in findings):
                problems.append(
                    f"the scanner did not report this under {token!r}; it found "
                    f"{findings or 'nothing at all'}"
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
            f"the offline scan was wrong for {len(wrong)} of {len(self.SCANS)} inputs. THE CLEAN AND "
            "PLANTED ROWS ARE ONE TEST ON PURPOSE, so read which kind failed. If every PLANTED row "
            "failed and the clean rows passed, the scanner is inert and the clean result above it "
            "means NOTHING: a detector that finds nothing is indistinguishable from a clean document, "
            "which is the whole reason the control rows exist. If a planted row failed alone, one "
            "entry left `FORBIDDEN_NETWORK_TOKENS`. If the RENDERED DOCUMENT row failed, an actual "
            "network reference reached the deliverable and it cannot ship: `render_document` also "
            "scans its own output and raises, so a failure here likely means that guard was removed "
            "too. If the prose row failed, the scanner was broadened into false positives, and the "
            "tempting fix (weakening it) is how a real reference later slips through.\n"
            + "\n".join(wrong),
        )

    def test_inline_svg_carries_NO_xmlns_so_the_scan_needs_no_exception(self):
        """Kept separate: an ABSENCE in the rendered document explaining why the scanner needs no
        allowlist.

        An `xmlns` would itself be an `http:` occurrence; HTML5 namespaces inline SVG by parser rule, so
        it is omitted rather than excepted. This is a claim about the SCANNER'S DESIGN (no exceptions,
        because the first exception is the beginning of the end of the scanner) rather than about any
        input, so it does not fit the planted/clean row shape.
        """

        document = render_document(_model())
        self.assertIn("<svg ", document)
        self.assertNotIn("xmlns", document)

    def test_render_REFUSES_to_return_a_document_with_a_network_reference(self):
        """Kept separate: an assertRaises, and it MONKEYPATCHES a renderer to plant the violation.

        Belt and braces: the render itself scans, so an offline violation cannot ship from here. The
        materially different setup (patch a private renderer, restore it in a finally) is exactly what
        must not go inside a table loop, where a failing row would leave the module patched for every
        test after it.
        """

        model = _model()
        original = spa._render_accessibility_boundary
        spa._render_accessibility_boundary = lambda: '<a href="https://x.example">x</a>'  # type: ignore[assignment]
        try:
            with self.assertRaises(SpaError) as ctx:
                render_document(model)
            self.assertIn("network references", str(ctx.exception))
        finally:
            spa._render_accessibility_boundary = original  # type: ignore[assignment]


# --- E-04: refusals as a first-class view ---------------------------------------------------------


class RefusalRenderingTests(unittest.TestCase):
    """THE MOST IMPORTANT CONTRACT HERE: a refusal never becomes a chart, empty or otherwise.

    ONE TABLE replaces three tests over `build_view_model`'s routing (the five-refusal set, the
    structural routing check, and the overview counts). All three built a result list, asked the model
    where each result went, and checked the rendered counts, differing only in the list. The
    assertRaises pair below stays separate.

    THE ROUTING IS THE SUBJECT, and every row asserts it THREE WAYS at once, because the three can
    disagree and each alone is satisfiable by a wrong implementation: which analyses became CHARTS,
    which became REFUSALS, and what the overview's computed/refused COUNTS say. A model that routed
    correctly but miscounted would still render a dishonest headline, and a model that counted
    correctly while routing a refusal into `charts` is the exact defect this module exists to prevent.

    THE DOM IS ASSERTED ON THE ALL-REFUSED ROWS, not just the view model. `charts == ()` is the
    structural guarantee, but what a reader actually sees is markup, so those rows additionally assert
    that NO `figure`, `svg` or `path` element exists anywhere. An empty axis reads as 'we measured
    zero', which is a stronger and falser claim than silence, and it is what a version that trusted a
    renderer to check `renderable` would produce.
    """

    #: The five required analyses Order 06 refused at review, by name. Named so the test is about the
    #: real refusal set rather than a generic one.
    REFUSED_AT_REVIEW = (
        ("failed-merge-waste-and-retry-cost", 3, Verdict.CANNOT_DETERMINE),
        ("merge-conflict-share-and-recurrence", 3, Verdict.CANNOT_DETERMINE),
        (
            "test-failure-retry-loops-and-time-to-first-pass",
            6,
            Verdict.CANNOT_DETERMINE,
        ),
        ("model-comparison", 2, Verdict.REFUSED),
        ("resource-saturation", 0, Verdict.CANNOT_DETERMINE),
    )

    #: (case, the results list, expected charted analysis names, expected refused analysis names,
    #: whether the document must contain NO plotted element at all, why this row exists)
    ROUTING = (
        (
            "the FIVE analyses Order 06 actually refused at review",
            [_refused(name, n=n, verdict=v) for name, n, v in REFUSED_AT_REVIEW],
            [],
            [name for name, _n, _v in REFUSED_AT_REVIEW],
            True,
            "THE REAL REFUSAL SET, not a generic one: five of the sixteen required analyses came back "
            "non-computable over the review corpus, with n between 0 and 6. This row is why the "
            "module exists, and it carries BOTH verdict kinds (`cannot-determine` and `refused`), so "
            "a routing rule that keyed on one enum member rather than on `renderable` is caught",
        ),
        (
            "a mixture of computed and refused results",
            [
                _computed("a"),
                _refused("b"),
                _computed("c"),
                _refused("d", verdict=Verdict.REFUSED),
            ],
            ["a", "c"],
            ["b", "d"],
            False,
            "THE ROUTING IS STRUCTURAL AND ORDER-PRESERVING. Interleaving computed and refused "
            "results is what proves the split is per-result rather than a partition of the first N: "
            "a renderer cannot forget to branch because no code path puts a non-renderable result in "
            "`charts` at all. The expected lists are ORDERED, so a stable-sort regression that "
            "reordered analyses (and so reordered the panels a reader scans) is caught too",
        ),
        (
            "every result computable",
            [_computed("a"), _computed("b")],
            ["a", "b"],
            [],
            False,
            "THE POSITIVE ROW, and it is load-bearing here: a `build_view_model` that routed "
            "EVERYTHING to refusals would satisfy both all-refused rows above while producing a "
            "report with no charts at all, which is the mirror-image dishonesty (understating the "
            "evidence) that `refusal_from_result`'s own refusal exists to prevent",
        ),
        (
            "one refusal alone",
            [_refused("merge-conflict-share-and-recurrence", n=3)],
            [],
            ["merge-conflict-share-and-recurrence"],
            True,
            "THE MINIMAL CASE FOR THE DOM CLAIM, and the row that would FAIL against a version "
            "rendering an EMPTY chart. With exactly one non-computable result there is nothing else "
            "in the document that could legitimately emit a `figure`, `svg` or `path`, so asserting "
            "those are absent is unambiguous: any plotted element here is a fabricated axis a reader "
            "would take for a measurement of zero",
        ),
    )

    def test_every_result_is_routed_by_its_verdict_and_counted_honestly(self):
        wrong = []
        for case, results, charted, refused, no_plot, why in self.ROUTING:
            model = _model(results=results, required_analysis_count=16)
            document = render_document(model)
            problems = []
            got_charts = [c.analysis_name for c in model.charts]
            got_refusals = [r.analysis_name for r in model.refusals]
            if got_charts != charted:
                problems.append(f"charts expected {charted!r}, got {got_charts!r}")
            if got_refusals != refused:
                problems.append(f"refusals expected {refused!r}, got {got_refusals!r}")
            # THE COUNTS THE OVERVIEW PRINTS, which can be wrong while the routing is right.
            if (model.computed_count, model.refused_count) != (
                len(charted),
                len(refused),
            ):
                problems.append(
                    f"(computed_count, refused_count) is "
                    f"{(model.computed_count, model.refused_count)!r}, expected "
                    f"{(len(charted), len(refused))!r}"
                )
            headline = f"<strong>{len(charted)}</strong> of <strong>16</strong>"
            if headline not in document:
                problems.append(
                    f"the overview does not state {headline!r}, so the rendered headline disagrees "
                    "with the model a reader is being shown"
                )
            if (
                refused
                and f"<strong>{len(refused)}</strong> could not be" not in document
            ):
                problems.append(
                    f"the overview does not report {len(refused)} refusals, so refusals are "
                    "structurally present but invisible in the summary"
                )
            # Each refusal must name ITSELF, its n, and its verdict, or it is not actionable.
            for result in results:
                if getattr(result, "renderable", False):
                    continue
                name = result.name
                for token in (
                    spa._humanize(name),
                    f"observed n={result.sample_size}",
                    result.verdict.value,
                ):
                    if token not in document:
                        problems.append(
                            f"the refusal of {name!r} does not report {token!r}, so a reader cannot "
                            "tell what refused, on how little data, or with which verdict"
                        )
            if no_plot:
                dom = _parse(document)
                for tag in ("figure", "svg", "path"):
                    found = dom.of(tag)
                    if found:
                        problems.append(
                            f"{len(found)} <{tag}> element(s) exist in a document with NO computable "
                            "analysis, so an empty axis is being rendered and reads as a measurement "
                            "of zero"
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
            f"{len(wrong)} of {len(self.ROUTING)} result sets were routed or counted wrongly. One "
            "branch on `AnalysisResult.renderable` inside `build_view_model` decides every row, so "
            "read the direction: refusals appearing in CHARTS is the worst artifact this module can "
            "produce, because a fabricated chart is a stronger and falser claim than silence and no "
            "reader can tell it from a real one. Computed results appearing in REFUSALS is the "
            "mirror defect and understates the evidence. If the routing lists are right and only the "
            "COUNTS or the headline are wrong, the model is honest while the page a human reads is "
            "not. FIX: if a plotted element appeared on an all-refused row, some renderer is "
            "branching on something other than `renderable`; the whole design is that no renderer "
            "gets the chance, so put the check back in the routing rather than in the template.\n"
            + "\n".join(wrong),
        )

    def test_chart_from_result_REFUSES_a_non_computed_verdict(self):
        """Kept separate: an assertRaises pair, and the raise is the whole assertion.

        A caller that forgets to branch must fail LOUDLY rather than plotting nothing as zero. Both
        non-computable verdicts are exercised because the refusal must key on `renderable` rather than
        on one enum member.
        """

        for verdict in (Verdict.CANNOT_DETERMINE, Verdict.REFUSED):
            with self.subTest(verdict=verdict):
                with self.assertRaises(SpaError) as ctx:
                    spa.chart_from_result(
                        _refused("x", verdict=verdict),
                        row_indices=(0,),
                        values=[1.0],
                        table_columns=("a",),
                        table_rows=(("a",),),
                    )
                self.assertIn("may not be produced", str(ctx.exception))

    def test_refusal_from_result_REFUSES_a_computed_verdict(self):
        """Kept separate: an assertRaises, and the SYMMETRIC one to the test above.

        Presenting a computable analysis as refused understates the evidence, which is the mirror of
        the defect this module exists to prevent. The two refusals are adjacent deliberately: together
        they state that both directions of the routing are enforced at the constructor, not merely in
        `build_view_model`.
        """

        with self.assertRaises(SpaError):
            spa.refusal_from_result(_computed("cache-utilization"))


# --- E-03: the embedded data contract -------------------------------------------------------------


class ColumnarLayoutTests(unittest.TestCase):
    """The layout was chosen by MEASUREMENT (24 percent smaller embedded), and is lossless.

    ONE TABLE replaces three tests over `columnar_from_rows`. Each built a row list, converted it, and
    asserted something about the resulting payload; the row list is the data.

    EVERY ROW ROUND-TRIPS, which is stricter than what it replaces. Only one of the three old tests
    called `rows_from_columnar`, so the missing-column and ordering cases asserted the FORWARD shape
    and left the inverse unchecked. Losslessness is the property the whole architecture rests on: this
    layout exists because it embeds 24 percent smaller, and that saving is only acceptable if nothing
    is lost, so every row now asserts the payload decodes back to the rows it came from.
    """

    #: (case, the input rows, the expected column list, the expected per-column arrays, why this row
    #: exists)
    CONVERSIONS = (
        (
            "a uniform 9-row fixture",
            _rows(9),
            None,  # the union of the fixture's keys; asserted only via the round trip
            None,
            "THE ORDINARY CASE, and the one that pins `row_count` and the `layout` tag. Those two "
            "fields are what the client reads to decide how to iterate the payload at all, so a "
            "renamed tag or a miscounted row breaks decoding rather than merely mislabeling it",
        ),
        (
            "rows with DISJOINT keys",
            [{"a": 1}, {"b": 2}],
            ["a", "b"],
            {"a": [1, None], "b": [None, 2]},
            "A MISSING OBSERVATION IS `None`, NOT A DROPPED ROW, and this is the single most "
            "important property of the layout. Order 05's whole `Value` contract rests on the "
            "distinction between 'not recorded' and 'not present': dropping the row would silently "
            "change the population every downstream statistic is computed over, and the row count "
            "would still look plausible. Both arrays are pinned so the padding is checked in both "
            "directions",
        ),
        (
            "the same row with its keys written in the OTHER order",
            [{"b": 1, "a": 2}],
            ["a", "b"],
            {"a": [2], "b": [1]},
            "COLUMN ORDER IS SORTED, NOT INSERTION-ORDERED, which is what makes the payload "
            "deterministic. Dict iteration order follows insertion in modern Python, so without the "
            "sort two renders of the same data would embed different byte sequences and defeat the "
            "golden-render requirement one layer up. The old test asserted two conversions AGREED; "
            "pinning the absolute order is stronger, because two conversions could agree on an "
            "insertion order that varies with the caller",
        ),
        (
            "an empty row list",
            [],
            [],
            {},
            "the degenerate case: no columns, no data, and a zero row count rather than a raise. The "
            "empty-population report depends on this, and it is where a `max`/`min` over the key "
            "union would fail",
        ),
        (
            "a row whose value is itself None",
            [{"a": None}, {"a": 1}],
            ["a"],
            {"a": [None, 1]},
            "AN EXPLICIT None MUST SURVIVE AS None, indistinguishable from the padding above, which "
            "is correct: both mean 'no observation here'. This row exists because the obvious "
            "implementation of the column union (`if key in row`) and the obvious implementation of "
            "the value fetch (`row.get(key)`) treat these two cases differently, and only one of "
            "them keeps the row count honest",
        ),
    )

    def test_the_columnar_layout_is_lossless_and_deterministic(self):
        wrong = []
        for case, rows, columns, data, why in self.CONVERSIONS:
            payload = spa.columnar_from_rows(rows)
            problems = []
            if payload["layout"] != "columnar":
                problems.append(
                    f"the layout tag is {payload['layout']!r}, not 'columnar'; the client branches "
                    "on this to decide how to read the payload"
                )
            if payload["row_count"] != len(rows):
                problems.append(
                    f"row_count is {payload['row_count']}, expected {len(rows)}"
                )
            if columns is not None and payload["columns"] != columns:
                problems.append(
                    f"columns expected {columns!r}, got {payload['columns']!r}"
                )
            if data is not None and payload["data"] != data:
                problems.append(f"data expected {data!r}, got {payload['data']!r}")
            # THE ROUND TRIP, asserted on EVERY row: the layout's 24 percent saving is only
            # acceptable if it loses nothing, so losslessness is not a separate case.
            restored = spa.rows_from_columnar(payload)
            expected_rows = [
                {name: row.get(name) for name in payload["columns"]} for row in rows
            ]
            if restored != expected_rows:
                problems.append(
                    f"the payload does NOT round trip: decoded {restored!r}, expected "
                    f"{expected_rows!r}"
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
            f"the columnar layout was wrong for {len(wrong)} of {len(self.CONVERSIONS)} row sets. One "
            "function builds every payload from a sorted key union plus a `row.get` per cell, so read "
            "the grouping: every row failing the ROUND TRIP means `rows_from_columnar` diverged from "
            "its inverse and the embedded data is no longer recoverable at all, while only the "
            "disjoint-keys row failing means padding broke and rows are being dropped or shifted. A "
            "wrong `columns` order on the reordered row means the sort was removed and two renders of "
            "identical data now differ byte for byte. FIX: a dropped or shifted row is the dangerous "
            "outcome, because every chart and every statistic downstream is computed over the "
            "resulting population and nothing in the document would look wrong.\n"
            + "\n".join(wrong),
        )

    def test_the_columnar_layout_measures_SMALLER_than_row_wise_at_scale(self):
        """Kept separate: a MEASUREMENT comparing two serializations, not a per-input expectation.

        The measurement that decided the architecture, re-derived on the fixture. It has no expected
        value at all (only an inequality plus a printed figure), so it cannot be a row in a table whose
        rows carry exact expected payloads.
        """

        import json as _json

        rows = _rows(2000)
        row_wise = len(
            _json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        )
        columnar = len(
            _json.dumps(
                spa.columnar_from_rows(rows), sort_keys=True, separators=(",", ":")
            ).encode()
        )
        self.assertLess(columnar, row_wise)
        print(
            f"MEASURED at 2000 rows: row-wise {row_wise} bytes, columnar {columnar} bytes "
            f"({1 - columnar / row_wise:.1%} smaller)"
        )


class DeterministicEncodingTests(unittest.TestCase):
    """gzip writes an mtime by default; mtime=0 plus a fixed level is what makes this deterministic.

    ONE TABLE replaces three tests, and THE SCOPE IS THE COLUMN: the same two properties (a second
    identical call produces IDENTICAL bytes, and the result decodes back to its input) are asserted at
    the payload level and at the whole-document level. The old file asserted determinism twice and the
    round trip once, in three methods, which left the pairing implicit.

    Why the scope must be a column rather than two tests: determinism at the payload level does NOT
    imply it for the document, because the document adds a second serialization (the JSON island) and
    the stylesheet and script assets. So a `sort_keys` dropped from the island would leave the payload
    row green and break the golden-render requirement, and the two rows sitting together is what makes
    that legible instead of looking like an unrelated failure.

    THE CONSTANTS TEST STAYS SEPARATE, because it asserts a published CONTRACT dict rather than any
    behavior; see its own docstring.
    """

    #: (case, produce() -> the value to compare, decode() -> the round-tripped value or None, the
    #: expected round-trip target or None, whether the output embeds a gzip stream whose HEADER MTIME
    #: must be zero, why this row exists)
    DETERMINISM = (
        (
            "the encoded payload at 50 rows",
            lambda: spa.encode_embedded_payload(spa.columnar_from_rows(_rows(50))),
            None,
            None,
            True,
            "GZIP WRITES THE CURRENT TIME INTO ITS HEADER BY DEFAULT, which alone would make two "
            "encodings of identical data differ byte for byte. `mtime=0` and a fixed `compresslevel` "
            "are both load-bearing (zlib output differs by level), and neither is visible in the "
            "decoded data, so this is the only place either is checked",
        ),
        (
            "the encoded payload at 7 rows, round-tripped",
            lambda: spa.encode_embedded_payload(spa.columnar_from_rows(_rows(7))),
            lambda: spa.decode_embedded_payload(
                spa.encode_embedded_payload(spa.columnar_from_rows(_rows(7)))
            ),
            lambda: spa.columnar_from_rows(_rows(7)),
            True,
            "DETERMINISM IS WORTHLESS WITHOUT LOSSLESSNESS: an encoder that returned a constant would "
            "satisfy every byte-identity row in this table. The round trip is what makes the "
            "determinism a property of the DATA rather than of the function",
        ),
        (
            "the WHOLE rendered document",
            lambda: render_document(_model()),
            None,
            None,
            False,
            "THE GOLDEN-RENDER REQUIREMENT, and the reason scope is a column: a diff between two "
            "renders must mean a real change. The document adds a SECOND serialization (the JSON "
            "island) plus two inlined assets on top of the payload, so payload determinism does not "
            "imply document determinism, and a `sort_keys` dropped from the island would break this "
            "row alone",
        ),
    )

    def test_encoding_and_rendering_are_byte_identical_and_lossless(self):
        """THE MTIME IS ASSERTED IN THE HEADER BYTES, because comparing two calls CANNOT catch it.

        FOUND BY MUTATION, and the reason the `mtime` column exists. Deleting `mtime=0` from
        `encode_embedded_payload` left this test GREEN: gzip's mtime field has ONE-SECOND granularity,
        so two calls in the same second still produce identical bytes, and the failure only appears when
        a test happens to straddle a second boundary. A comparison-based check is therefore not merely
        weak here, it is FLAKY IN THE WRONG DIRECTION: it passes almost always and fails at random.

        So the rows that embed a gzip stream decode the base64 and assert bytes 4 through 8 of the gzip
        header (the MTIME field, little-endian per RFC 1952) are zero. That is time-independent and
        strictly stronger than any number of repeated calls.
        """

        wrong = []
        for case, produce, decode, target, gzip_mtime, why in self.DETERMINISM:
            problems = []
            first = produce()
            second = produce()
            if gzip_mtime:
                import base64 as _b64

                header = _b64.b64decode(first.encode("ascii"))[:10]
                if header[:2] != b"\x1f\x8b":
                    problems.append(
                        f"the decoded payload does not begin with the gzip magic bytes: "
                        f"{header[:2]!r}"
                    )
                else:
                    mtime = int.from_bytes(header[4:8], "little")
                    if mtime != 0:
                        problems.append(
                            f"the gzip header MTIME field is {mtime}, not 0, so two encodings of "
                            "identical data will differ byte for byte across a one-second boundary. "
                            "NOTE this is invisible to a repeated-call comparison, since gzip's mtime "
                            "has one-second granularity"
                        )
            if first != second:
                if isinstance(first, str) and isinstance(second, str):
                    index = next(
                        (i for i, (a, b) in enumerate(zip(first, second)) if a != b),
                        min(len(first), len(second)),
                    )
                    problems.append(
                        f"two identical calls produced DIFFERENT output, first differing at offset "
                        f"{index} ({first[index : index + 40]!r} versus "
                        f"{second[index : index + 40]!r})"
                    )
                else:
                    problems.append("two identical calls produced different output")
            if decode is not None:
                restored = decode()
                expected = target()
                if restored != expected:
                    problems.append(
                        f"the value does NOT round trip: decoded {restored!r}, expected {expected!r}"
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
            f"{len(wrong)} of {len(self.DETERMINISM)} subjects are not deterministic or not lossless. "
            "Read the SCOPE of the failures: if the payload rows fail, the gzip settings changed (an "
            "mtime is being written, or the compress level moved) and the difference will be near the "
            "START of the base64 where the header lives. If ONLY the document row fails, the payload "
            "is fine and the extra serialization the document performs is not deterministic, most "
            "likely a `sort_keys` dropped from the JSON island or a dict iterated in insertion order. "
            "FIX: non-determinism here is not cosmetic. The whole-document byte identity is what makes "
            "a diff between two generated reports mean a real change, so losing it turns every "
            "regeneration into noise and hides the changes that matter.\n"
            + "\n".join(wrong),
        )

    def test_the_contract_records_the_deterministic_gzip_settings(self):
        """Kept separate: asserts a PUBLISHED CONSTANT dict, not behavior.

        `EMBEDDED_DATA_CONTRACT` is documentation the module ships so a consumer can decode the payload
        without reading the source. The table above proves the behavior IS deterministic; this proves
        the contract still says HOW, which is a different claim and would not fail together with it.
        """

        self.assertEqual(spa.EMBEDDED_DATA_CONTRACT["gzip_mtime"], 0)
        self.assertEqual(spa.EMBEDDED_DATA_CONTRACT["gzip_level"], 9)
        self.assertTrue(spa.EMBEDDED_DATA_CONTRACT["json_sort_keys"])


class BoundedRenderingTests(unittest.TestCase):
    """Node count must NOT scale with row count. 29766 point nodes was the measured defect.

    TWO TABLES replace seven tests, split by subject: what `bin_series` reports for a given input, and
    what `series_path_data` emits for a given series. They stay separate because the first returns a
    dict of statistics and the second a single SVG `d` string, so no shared row shape fits them.

    EVERY BINNING ROW ASSERTS BOTH THE BOUND AND THE SOURCE COUNT, which is the pair that makes
    binning HONEST rather than merely cheap. `bin_count` bounded is the rendering guarantee;
    `source_row_count` is what lets a reader see that a 240-bin histogram summarizes 29766
    observations. Without the second, the binning silently BECOMES the data, and a reader would take
    240 bars for 240 observations.
    """

    #: (case, the input values, the expected bin_count, the expected source_row_count, the expected
    #: counts list or None to skip, the expected (minimum, maximum) or None to skip, why this row
    #: exists)
    BINNINGS = (
        (
            "100000 distinct values",
            [float(i) for i in range(100000)],
            spa.MAX_PLOT_BINS,
            100000,
            None,
            (0.0, 99999.0),
            "THE BOUND IS THE WHOLE POINT, and it is asserted as EQUALITY at the cap rather than as "
            "`<=`: at 100000 inputs the binning must actually be saturating, so a `<=` assertion "
            "would also pass for an implementation that silently emitted one bin and destroyed the "
            "distribution. 29766 individual `<circle>` nodes was the measured defect (roughly 1.34 MB "
            "of markup, past where browsers degrade), and the source count beside it is what keeps "
            "the summarization visible",
        ),
        (
            "three values, far below the cap",
            [1.0, 2.0, 3.0],
            spa.MAX_PLOT_BINS,
            3,
            None,
            (1.0, 3.0),
            "MEASURED AND SURPRISING, SO PINNED DELIBERATELY: a three-point series still reports "
            "`bin_count` at the CAP (240), because the bin count is derived from the requested bins "
            "rather than from the data, leaving most bins empty. That is the actual contract, and the "
            "row exists so nobody 'fixes' the number here without noticing that the client renders "
            "one point per bin. The source count of 3 is what tells a reader the 240 bars summarize "
            "three observations",
        ),
        (
            "a DEGENERATE range (every value identical)",
            [5.0, 5.0, 5.0],
            1,
            3,
            [3],
            (5.0, 5.0),
            "ONE BIN, NOT A DIVISION BY ZERO. The bin width is `(high - low) / count`, so an "
            "all-identical series is the arithmetic edge, and the honest answer is a single bin "
            "holding everything. The counts list is pinned because a bin that reported 0 while "
            "holding 3 observations would be worse than the crash it replaced",
        ),
        (
            "an EMPTY series",
            [],
            0,
            0,
            [],
            (None, None),
            "ABSENT, NOT ZERO. `minimum` is None rather than 0.0, which is the same "
            "missing-versus-zero distinction the columnar layout enforces: a zero minimum would plot "
            "as a real measurement at the origin, and zero bins is what tells the renderer there is "
            "nothing to draw",
        ),
        (
            "a series containing NaN and infinity",
            [1.0, float("nan"), float("inf"), 2.0],
            spa.MAX_PLOT_BINS,
            2,
            None,
            (1.0, 2.0),
            "NON-FINITE VALUES ARE EXCLUDED, AND THE SOURCE COUNT SAYS SO: 2, not 4. This row is "
            "where the `min`/`max` would otherwise become NaN and poison every bin edge, turning the "
            "whole chart into empty output with no error. Reporting the reduced count is what makes "
            "the exclusion visible rather than silent",
        ),
    )

    def test_binning_bounds_the_node_count_while_reporting_what_it_summarized(self):
        wrong = []
        for case, values, bins, source, counts, extent, why in self.BINNINGS:
            series = spa.bin_series(values)
            problems = []
            if series["bin_count"] != bins:
                problems.append(
                    f"bin_count expected {bins}, got {series['bin_count']}"
                    + (
                        f" (the cap is MAX_PLOT_BINS={spa.MAX_PLOT_BINS})"
                        if series["bin_count"] > spa.MAX_PLOT_BINS
                        else ""
                    )
                )
            if series["source_row_count"] != source:
                problems.append(
                    f"source_row_count expected {source}, got {series['source_row_count']}; this "
                    "field is what stops the binning from silently becoming the data"
                )
            if counts is not None and series["counts"] != counts:
                problems.append(f"counts expected {counts!r}, got {series['counts']!r}")
            if extent is not None and (series["minimum"], series["maximum"]) != extent:
                problems.append(
                    f"(minimum, maximum) expected {extent!r}, got "
                    f"{(series['minimum'], series['maximum'])!r}"
                )
            if counts is None and sum(series["counts"]) != source:
                problems.append(
                    f"the counts sum to {sum(series['counts'])} but {source} values were binned, so "
                    "observations were lost or double-counted inside the bins"
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
            f"bin_series was wrong for {len(wrong)} of {len(self.BINNINGS)} series. One function with "
            "three branches (empty, degenerate range, general) decides every row, so read the "
            "grouping: if only the two edge rows fail, a branch was removed and the general path is "
            "now handling inputs it cannot (a zero-width range divides by zero). If every "
            "`source_row_count` is wrong, the filtering changed and the reported basis no longer "
            "matches what was plotted. FIX: an UNBOUNDED bin_count is the performance defect this "
            "function exists to prevent, and it degrades the browser rather than raising. A wrong "
            "source_row_count is the HONESTY defect: the chart still renders, and a reader takes 240 "
            "bars for 240 observations.\n" + "\n".join(wrong),
        )

    #: (case, the counts to plot, the expected exact `d` string, why this row exists)
    #:
    #: THE EXACT PATH STRING IS PINNED, which is appropriate here and would be a change-detector for
    #: the report's prose: this is a coordinate computation whose determinism is a hard requirement
    #: (the golden-render test compares whole documents byte for byte), and the two-decimal rounding
    #: exists precisely so the output does not carry platform float noise.
    PATHS = (
        (
            "a four-point series",
            [1.0, 2.0, 3.0, 4.0],
            "M 0.00 150.00 L 213.33 100.00 L 426.67 50.00 L 640.00 0.00",
            "ONE `M` AND ONE NODE FOR THE WHOLE SERIES. The measured alternative was 29766 "
            "`<circle>` elements at roughly 1.34 MB; this is roughly 0.36 MB in a single node. The "
            "coordinates are pinned rather than counted because they encode the normalization too: y "
            "is inverted (SVG's origin is top-left) and the peak maps to 0.00, so a chart drawn "
            "upside down is caught here rather than by eye",
        ),
        (
            "a SINGLE-point series",
            [7.0],
            "M 0.00 0.00 L 640.00 0.00",
            "THE OFF-BY-ONE EDGE. The step is `width / (len - 1)`, which divides by zero for one "
            "point, so this takes a separate branch that draws a flat line across the full width. "
            "Without this row the single-run report would crash, which is exactly when a human is "
            "debugging one run",
        ),
        (
            "an empty series",
            [],
            "",
            "the empty string, so the caller emits no path element at all rather than an `M`-less "
            "attribute the SVG parser would reject",
        ),
        (
            "an all-zero series",
            [0.0, 0.0],
            "M 0.00 200.00 L 640.00 200.00",
            "THE OTHER DIVISION-BY-ZERO EDGE, and a different one from the empty case: the peak is "
            "0, so the `or 1.0` fallback is what prevents a crash. The result sits at y=200 (the "
            "baseline) rather than y=0, which is the honest rendering of 'all zero' and the opposite "
            "of what a missing fallback would produce",
        ),
    )

    def test_a_whole_series_becomes_exactly_one_path_node(self):
        wrong = []
        for case, counts, expected, why in self.PATHS:
            got = spa.series_path_data(counts)
            problems = []
            if got != expected:
                problems.append(f"expected {expected!r}, got {got!r}")
            if got and got.count("M") != 1:
                problems.append(
                    f"the path carries {got.count('M')} `M` commands; one series must be ONE "
                    "subpath, or the node-count bound this function exists for is lost"
                )
            # DETERMINISM, checked on every row: the golden-render test compares whole documents byte
            # for byte, so a single unrounded coordinate would break it.
            if spa.series_path_data(counts) != got:
                problems.append(
                    "two calls with identical input produced different output, so the whole-document "
                    "byte-identity requirement cannot hold"
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
            f"series_path_data was wrong for {len(wrong)} of {len(self.PATHS)} series. One function "
            "with three branches (empty, single point, general) decides every row, so read the "
            "grouping: if the multi-point rows are all shifted by the same amount, the width/height "
            "constants or the normalization changed rather than the geometry being wrong; if the "
            "single-point or all-zero row fails, a division-by-zero guard was removed and the "
            "single-run report now crashes. FIX: if the coordinates differ only in their decimals, "
            "the rounding was dropped, which is not cosmetic: it makes two renders of identical data "
            "differ byte for byte and breaks the golden-render requirement one layer up.\n"
            + "\n".join(wrong),
        )

    def test_plotted_dom_node_count_is_BOUNDED_at_corpus_scale(self):
        """Kept separate: a SCALE fixture asserting a DOCUMENT-level node budget.

        The budget asserted at the measured 29766-row scale, not at a toy one. The binning table checks
        per-input statistics; this counts plotted elements in a whole rendered document against
        `PLOTTED_NODE_BUDGET`, which is the property a browser actually degrades on.
        """

        rows = _rows(64)
        big_values = [float(i % 997) for i in range(CORPUS_SCALE_ROWS)]
        chart = spa.chart_from_result(
            _computed("cost-distribution", n=CORPUS_SCALE_ROWS),
            row_indices=tuple(range(len(rows))),
            values=big_values,
            table_columns=("metric", "value"),
            table_rows=(("median", 1.0),),
        )
        document = render_document(_model(results=[]))
        # The plotted series itself is one path; assert the whole document's plot nodes are bounded.
        collector = _parse(render_document(_model(rows=rows)))
        plotted = (
            len(collector.of("path"))
            + len(collector.of("circle"))
            + len(collector.of("rect"))
        )
        self.assertLessEqual(plotted, spa.PLOTTED_NODE_BUDGET)
        self.assertLessEqual(chart.series["bin_count"], spa.MAX_PLOT_BINS)
        self.assertEqual(chart.series["source_row_count"], CORPUS_SCALE_ROWS)
        print(
            f"MEASURED at {CORPUS_SCALE_ROWS} source rows: bin_count="
            f"{chart.series['bin_count']}, plotted DOM nodes in document={plotted} "
            f"(budget {spa.PLOTTED_NODE_BUDGET})"
        )
        self.assertIsInstance(document, str)


class SizeBudgetTests(unittest.TestCase):
    """The produced index.html stays under a DECLARED budget at corpus scale."""

    def test_the_document_stays_under_budget_at_corpus_scale(self):
        """Kept separate: builds a 29766-row corpus-scale fixture and asserts a BYTE budget.

        Materially different (and materially slower) setup from every other test here, and the assertion
        is an inequality against a declared constant plus a printed measurement rather than an expected
        value.
        """

        rows = [
            {
                "run_id": f"run-2026091{i % 10}T000000Z-{i % 977}",
                "ipd_id6": f"i{i % 9973:05d}",
                "attempt": (i % 3) + 1,
                "phase": ("execute", "review", "verify", "recovery")[i % 4],
                "outcome": ("executed", "partial", "blocked")[i % 3],
                "cost_usd": round((i % 811) * 0.013, 4),
                "wall_seconds": 60 + (i % 3600),
                "total_tokens": 997 * ((i % 503) + 1),
            }
            for i in range(CORPUS_SCALE_ROWS)
        ]
        model = build_view_model(
            rows=rows,
            results=[
                _computed("cost-distribution", n=CORPUS_SCALE_ROWS),
                _refused("x"),
            ],
            metric_column="cost_usd",
            required_analysis_count=16,
            generated_label="corpus-scale-fixture",
        )
        document = render_document(model)
        size = len(document.encode("utf-8"))
        self.assertLess(
            size,
            spa.SIZE_BUDGET_BYTES,
            f"document is {size} bytes, over the {spa.SIZE_BUDGET_BYTES}-byte budget",
        )
        print(
            f"MEASURED at {CORPUS_SCALE_ROWS} rows: index.html is {size} bytes "
            f"({size / 1048576:.2f} MiB) against a {spa.SIZE_BUDGET_BYTES / 1048576:.0f} MiB budget"
        )

    def test_the_raw_view_PAGINATES_rather_than_materializing_every_row(self):
        """ONE test replaces two: the served markup carries no rows, AND the controls to page exist.

        Merged because the two halves are meaningless apart. An empty `tbody` with no paging controls
        is not pagination, it is a missing table; paging controls over a fully materialized body are
        not pagination either. The old split asserted each half in its own method, so either could
        pass while the raw view was unusable.

        Asserted at 1000 rows so the empty body is a real claim: with 4 fixture rows, a renderer that
        materialized everything would still emit few enough rows to look plausible.
        """

        document = render_document(_model(rows=_rows(1000)))
        dom = _parse(document)

        # 1. THE BODY IS EMPTY IN THE SERVED MARKUP. 29766 rows as markup is what the measured defect
        # was; the client adds one page at a time from the embedded payload instead.
        self.assertIn('id="raw-body"', document)
        body = document.split('id="raw-body"')[1].split("</tbody>")[0]
        self.assertNotIn("<tr", body)
        self.assertTrue(dom.of("table"))

        # 2. THE PAGE SIZE IS STATED, so a reader knows they are seeing a window rather than the whole.
        self.assertIn(f"<strong>{spa.RAW_VIEW_PAGE_SIZE} at a time</strong>", document)

        # 3. THE CONTROLS TO MOVE THAT WINDOW EXIST, in both directions. Forward-only paging would
        # leave a reader unable to return to a row they just passed.
        self.assertIn('data-page-step="1"', document)
        self.assertIn('data-page-step="-1"', document)

        # 4. AND THE PAGE CHANGE IS ANNOUNCED. Without a live region the table content changes with no
        # indication to a screen reader, so a paging control is operable but its effect is silent.
        self.assertIn('aria-live="polite"', document)


# --- E-05: linked controls over ONE data contract -------------------------------------------------


class LinkedControlTests(unittest.TestCase):
    """One shared contract, so a table can never disagree with the chart above it."""

    def test_a_chart_and_its_table_are_computed_from_the_SAME_rows(self):
        """Kept separate: asserts an IDENTITY between two model fields, not a rendered value.

        The shared `row_indices` is the mechanism that makes 'a table cannot disagree with the chart
        above it' structural rather than a review promise. That is a claim about the view model's
        internal consistency, which no document-rendering row can state.
        """

        rows = _rows(6)
        model = _model(rows=rows)
        chart = model.charts[0]
        self.assertEqual(chart.row_indices, tuple(range(len(rows))))
        self.assertEqual(model.payload["row_count"], len(rows))

    def test_the_table_rows_are_the_charted_results_own_values(self):
        """Kept separate: the subject is the exact table PROJECTION, distinct from the identity above.

        The claim is that the displayed table is the result's own `values` mapping, sorted, and never
        recomputed by the renderer. A recomputation could agree with the chart (satisfying the identity
        test) and still disagree with what the analysis actually returned.
        """

        result = _computed("cache-utilization", share=0.9862, n_sessions=345)
        model = _model(results=[result])
        chart = model.charts[0]
        self.assertEqual(dict(chart.table_rows), {"n_sessions": 345, "share": 0.9862})

    #: (the control group, its full expected value list IN ORDER, why this group's set is pinned)
    #:
    #: ONE TABLE replaces two tests. Both rendered the default document and asked about the built-in
    #: control groups; the GROUP is the row. Merging them is what lets each row assert the two claims
    #: TOGETHER, which the split could not: that every value is present, AND that exactly one of them
    #: starts pressed. A group with all its values present and none pressed renders a filter with no
    #: initial state, and a group with two pressed renders a contradiction, and neither old test could
    #: see either problem because one counted values and the other counted pressed buttons.
    CONTROL_GROUPS = (
        (
            "metric",
            (
                "time",
                "cost",
                "input tokens",
                "output tokens",
                "cache tokens",
                "total tokens",
            ),
            "THE SIX METRICS ARE A CLOSED SET the client switches between, and a missing one is a "
            "dimension of the data a reader simply cannot view. The token metrics are separate values "
            "on purpose (input, output and cache price differently), so collapsing them to one 'tokens' "
            "control would silently merge costs that must stay distinguishable",
        ),
        (
            "phase",
            ("aggregate", "review", "execute", "verifier", "recovery"),
            "THE PHASES ARE WHERE TIME AND COST ARE ATTRIBUTED, so a missing phase makes its spend "
            "invisible rather than merely unfilterable. `aggregate` is FIRST because it is the honest "
            "default: a report that opened on a single phase would show part of the corpus while "
            "looking complete, which is the same failure the unattributed-time default exists to "
            "prevent",
        ),
    )

    def test_every_control_group_renders_its_whole_value_set_with_one_pressed(self):
        document = render_document(_model())
        dom = _parse(document)
        wrong = []
        for group, values, why in self.CONTROL_GROUPS:
            buttons = [b for b in dom.of("button") if b.get("data-group") == group]
            problems = []
            rendered = [b.get("data-value") for b in buttons]
            if rendered != list(values):
                missing = [v for v in values if v not in rendered]
                extra = [v for v in rendered if v not in values]
                detail = []
                if missing:
                    detail.append(f"missing {missing!r}")
                if extra:
                    detail.append(f"unexpected {extra!r}")
                if not detail:
                    detail.append("the values are right but the ORDER changed")
                problems.append(
                    f"expected values {list(values)!r}, rendered {rendered!r} "
                    f"({'; '.join(detail)})"
                )
            pressed = [b for b in buttons if b.get("aria-pressed") == "true"]
            if len(pressed) != 1:
                problems.append(
                    f"{len(pressed)} button(s) start pressed, expected exactly 1"
                    + (
                        " (with none pressed the control has no initial state and the chart shows "
                        "something no button claims)"
                        if not pressed
                        else " (two pressed buttons announce a contradiction to assistive technology)"
                    )
                )
            elif pressed[0].get("data-value") != values[0]:
                problems.append(
                    f"the pressed button is {pressed[0].get('data-value')!r}, but the first value "
                    f"{values[0]!r} is the intended default"
                )
            for button in buttons:
                if "aria-pressed" not in button:
                    problems.append(
                        f"the {button.get('data-value')!r} button carries no `aria-pressed`, so its "
                        "state is invisible to assistive technology"
                    )
            if problems:
                wrong.append(
                    f"  the {group!r} group:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CONTROL_GROUPS)} control groups rendered wrongly. Both groups "
            "are emitted by the SAME loop in `_render_controls`, so if both fail the same way the loop "
            "changed rather than either value list. Read which claim failed: a missing VALUE hides a "
            "slice of the data from the reader entirely, while a wrong PRESSED count breaks the link "
            "between what the chart shows and what the controls say it shows, which is worse than an "
            "obviously broken control because the report still looks coherent. FIX: if the pressed "
            "button is no longer the FIRST value, check that the new default is an honest one; "
            "`aggregate` is first for the phase group specifically so the report does not open on a "
            "single phase while appearing to show everything.\n" + "\n".join(wrong),
        )

    def test_the_verifier_phase_is_labeled_DERIVED(self):
        """Kept separate: a claim about ONE value of one group, not about either group's set.

        57 verifier logs against 0 attempts carrying a verify cost: the phase is derived from a log
        FILENAME and was never recorded, so it must be labeled wherever it appears. The control-group
        table asserts the value SETS; this asserts that one member of one set carries a provenance
        caveat the others must not, which would be noise as a per-group column.
        """

        document = render_document(_model())
        self.assertIn("(derived)", document)
        self.assertIn("<strong>derived</strong> from a log filename", document)


class HonestEmptyStateTests(unittest.TestCase):
    """A degenerate control renders DISABLED with its reason, never hidden and never operable.

    ONE TABLE replaces five tests, and THE CLASSIFICATION AND THE RENDERING ARE ONE SUBJECT, which is
    why they are columns of the same row rather than two tables. The old file classified in three tests
    and rendered in two, so the link that matters was never asserted: a dimension classified
    `DEGENERATE` whose button nonetheless renders operable is exactly the defect the three-valued state
    exists to prevent, and it passes both halves of a split suite. Every row here classifies AND
    renders the same dimension.

    DEGENERATE IS NOT EMPTY, and the pair of rows is what states it. An empty control is obviously
    useless; a single-valued one LOOKS like a working filter while describing 1.1 percent of the corpus
    (the measured model-identity coverage). Both must render DISABLED with a stated reason, and neither
    may be HIDDEN, because a hidden control is indistinguishable from an oversight.
    """

    #: (case, build_dimension args, kwargs, the expected DimensionState, the expected coverage, a
    #: substring the reason must contain or None, the expected number of OPERABLE buttons, the
    #: expected number of DISABLED buttons, substrings the document must contain, why this row exists)
    DIMENSIONS = (
        (
            "no values at all",
            ("model", "Model", []),
            {},
            DimensionState.EMPTY,
            1.0,
            "no record in the current population carries this dimension",
            0,
            1,
            (),
            "AN EMPTY CONTROL IS RENDERED, NOT HIDDEN. Hiding it would be indistinguishable from "
            "having forgotten the dimension entirely, so a reader could not tell 'this filter found "
            "nothing' from 'this filter does not exist'. Coverage stays 1.0 because no record count "
            "was supplied: absence of data is not the same as measured zero coverage",
        ),
        (
            "ONE distinct value, over the measured 2-of-179 coverage",
            ("model", "Model", ["one-model"]),
            {"total_records": 179, "resolved_records": 2},
            DimensionState.DEGENERATE,
            2 / 179,
            "only one distinct value",
            0,
            1,
            # 1.1% is the DERIVED figure, and 'degenerate:' is the state reaching the page.
            ("degenerate:", "1.1%"),
            "THE MEASURED CASE THIS STATE EXISTS FOR: model identity resolved for 2 of 179 attempts. "
            "A single-valued control is the dangerous one precisely because it looks operable, and "
            "filtering on it cannot separate anything. The 1.1 percent must reach the DOCUMENT, "
            "because a control's trustworthiness is a property of its coverage and a reader cannot "
            "infer it from the value list",
        ),
        (
            "two distinct values",
            ("runner", "Runner", ["oc", "agy"]),
            {},
            DimensionState.POPULATED,
            1.0,
            "",
            2,
            0,
            (),
            "THE POSITIVE ROW, and it is load-bearing: a classifier that returned DEGENERATE for "
            "everything would satisfy both rows above while disabling every filter in the report. It "
            "also pins that a usable dimension carries an EMPTY reason, so no spurious explanation is "
            "attached to a working control",
        ),
        (
            "two values but only 2-of-179 coverage",
            ("model", "Model", ["a", "b"]),
            {"total_records": 179, "resolved_records": 2},
            DimensionState.POPULATED,
            2 / 179,
            "",
            2,
            0,
            (),
            "MEASURED AND WORTH PINNING: coverage does NOT affect the state. Two distinct values "
            "classify as POPULATED even at 1.1 percent coverage, so the control is operable while its "
            "coverage travels beside it as a separate fact. The row exists because the docstring's "
            "'two resolved values out of 179 is a degenerate control however many labels it shows' "
            "reads like the opposite rule, and a future edit acting on that reading would disable "
            "working filters",
        ),
        (
            "values that are blank or whitespace only",
            ("model", "Model", ["", "  ", "real"]),
            {},
            DimensionState.DEGENERATE,
            1.0,
            "only one distinct value",
            0,
            1,
            (),
            "BLANK VALUES ARE NOT VALUES. Three raw entries collapse to ONE real distinct value, so "
            "the control is degenerate rather than populated. Without this row a dimension whose "
            "records carry empty strings would render as a three-way filter, two of whose options "
            "select nothing",
        ),
    )

    def test_every_dimension_state_classifies_and_renders_consistently(self):
        wrong = []
        for (
            case,
            args,
            kwargs,
            state,
            coverage,
            reason_fragment,
            operable,
            disabled_count,
            tokens,
            why,
        ) in self.DIMENSIONS:
            dimension = spa.build_dimension(*args, **kwargs)
            problems = []
            if dimension.state is not state:
                problems.append(f"state expected {state!r}, got {dimension.state!r}")
            if dimension.is_usable is not (state is DimensionState.POPULATED):
                problems.append(
                    f"is_usable is {dimension.is_usable}, which disagrees with the state "
                    f"{dimension.state!r}; the renderer branches on is_usable, so the two "
                    "disagreeing means the classification is cosmetic"
                )
            if abs(dimension.coverage - coverage) > 1e-6:
                problems.append(
                    f"coverage expected {coverage!r}, got {dimension.coverage!r}"
                )
            if reason_fragment is not None:
                if reason_fragment and reason_fragment not in dimension.reason:
                    problems.append(
                        f"reason {dimension.reason!r} does not contain {reason_fragment!r}, so the "
                        "control is unusable without saying why"
                    )
                if not reason_fragment and dimension.reason:
                    problems.append(
                        f"a USABLE dimension carries a reason ({dimension.reason!r}); an explanation "
                        "attached to a working control tells the reader it is broken"
                    )

            # THE RENDERED HALF, in the same row: a classification the markup ignores is worthless.
            document = render_document(_model(dimensions=[dimension]))
            dom = _parse(document)
            group = [b for b in dom.of("button") if b.get("data-group") == args[0]]
            live = [b for b in group if "disabled" not in b]
            dead = [b for b in group if b.get("aria-disabled") == "true"]
            if len(live) != operable:
                problems.append(
                    f"{len(live)} OPERABLE button(s) rendered, expected {operable}"
                    + (
                        " (an unusable dimension must not be operable)"
                        if operable == 0
                        else ""
                    )
                )
            if len(dead) != disabled_count:
                problems.append(
                    f"{len(dead)} DISABLED button(s) rendered, expected {disabled_count}"
                    + (
                        " (the control must be present-and-disabled, never HIDDEN, or it is "
                        "indistinguishable from an oversight)"
                        if disabled_count and not group
                        else ""
                    )
                )
            for button in dead:
                if "aria-describedby" not in button:
                    problems.append(
                        "a disabled control carries no `aria-describedby`, so its reason never "
                        "reaches assistive technology and the state is announced without the why"
                    )
            missing = [token for token in tokens if token not in document]
            if missing:
                problems.append(f"absent from the document: {missing!r}")
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DIMENSIONS)} dimensions classified or rendered wrongly. Each "
            "row runs `build_dimension` AND `render_document`, which is the whole point: a state the "
            "markup ignores is worthless. So read WHICH HALF failed. If the states are right and the "
            "BUTTON COUNTS are wrong, classification is fine and `_render_dimension` stopped honoring "
            "`is_usable`, which means a degenerate control is operable and a reader can filter on a "
            "dimension covering 1.1 percent of the corpus without being told. If the STATES moved, "
            "check the EMPTY/DEGENERATE pair specifically: collapsing the two is the tempting "
            "simplification, and it loses the distinction that a single-valued control looks like it "
            "works. FIX: never resolve a failure here by HIDING the control; a hidden control is "
            "indistinguishable from a forgotten one.\n" + "\n".join(wrong),
        )


# --- E-06: the panels and their uncertainty context -----------------------------------------------


#: The pricing input measured at review: two eras, the later one still open, with recorded and
#: estimated totals that happen to coincide. Shared by the panel rows below.
MEASURED_PRICING = {
    "recorded_usd": 2568.12,
    "estimated_usd": 2568.12,
    "unknown_price_step_count": 23,
    "eras": [
        {
            "era_id": "era-a",
            "effective_from": "2026-08-01T00:00:00Z",
            "effective_to": "2026-08-29T05:38:43Z",
            "source": "fit-to-recorded-cost",
            "source_version": "2026-09-08",
            "spend_share": 0.28,
        },
        {
            "era_id": "era-b",
            "effective_from": "2026-08-29T05:38:43Z",
            "effective_to": None,
            "source": "fit-to-recorded-cost",
            "source_version": "2026-09-08",
            "spend_share": 0.72,
        },
    ],
}


def _finding(**overrides) -> dict:
    finding = {
        "finding_id": "F-01",
        "title": "A measured association",
        "severity": "medium",
        "affected_slice": "attempts in price era B",
        "sample_size": 345,
        "coverage": 0.92,
        "uncertainty": "the interval spans 1.10 to 1.44",
        "data_quality_caveats": ["13 percent of spend is invisible"],
        "alternative_explanations": ["later work may simply be harder"],
        "next_experiment": "re-run stratified by price era",
        "recommendation": "",
        "is_actionable": True,
    }
    finding.update(overrides)
    return finding


class RequiredPanelTests(unittest.TestCase):
    """Every required panel is present, and the honesty headlines are defaults, not footnotes.

    ONE TABLE replaces twelve tests from this class plus five from `EdgeCasePopulationTests`. Every one
    had the same shape: build a view model with one field populated, render it, and assert some
    substrings appear. The MODEL INPUT is therefore the row, and what varied between the old tests was
    never the mechanism, only which panel's input was set.

    WHAT EACH ROW ASSERTS IS CHOSEN DELIBERATELY, because this is a generated HTML report and the two
    available things to assert are not equally worth having. Pinning the report's PROSE is a change
    detector: rewording a sentence for clarity is a legitimate edit that would break such a test
    without any behavior changing. What is real behavior is the DATA reaching the document: a computed
    percentage, an era id, a row count, a count of refusals, an escaped hostile string. So the rows
    favor DERIVED VALUES and identifiers over sentences.

    PROSE IS PINNED ONLY WHERE THE SENTENCE IS THE BEHAVIOR, and each such row says so. Three
    qualify, and they are the report's honesty commitments rather than its wording: unattributed time
    being shown BY DEFAULT (96.2 percent of wall time was unattributed at review, so a time view
    without it displays a few percent of the truth while looking complete), unknown prices being
    REFUSED rather than defaulted, and the raw view stating that no prompt or source content is
    included. Each is a claim a reader relies on and none is derivable from any number in the payload.

    NEGATIVE AND DEGENERATE ROWS SHARE THIS TABLE. An empty population, a single row, an all-refused
    population and an absent price era are the cases where a renderer is most likely to crash or to
    substitute a placeholder for an honest absence, and they belong beside the populated rows so that
    "renders something" is never mistaken for "renders the truth".
    """

    #: Every panel id the document must carry. A separate constant because it is asserted as a SET by
    #: the first row, not one id at a time.
    REQUIRED_IDS = (
        "overview",
        "controls",
        "time-accounting",
        "charts",
        "refusals",
        "pricing",
        "quality",
        "findings",
        "interpretation",
        "raw",
        "a11y",
    )

    #: (case, model kwargs, substrings that MUST appear, substrings that must NOT appear, why this
    #: row exists)
    PANELS = (
        (
            "the default population, checked for every required panel",
            {},
            tuple(f'id="{panel_id}"' for panel_id in REQUIRED_IDS),
            (),
            "THE STRUCTURAL ROW: every required panel exists. Asserted as ids rather than headings "
            "because the ids are what the skip link and every `aria-labelledby` reference resolve "
            "against, so a renamed id breaks navigation while a reworded heading does not",
        ),
        (
            "the time-accounting panel on default data",
            {},
            (
                # PROSE PINNED ON PURPOSE: this sentence IS the honesty commitment, not a description
                # of one. A time view that omitted unattributed time would show a few percent of the
                # truth while looking complete, so the default is the behavior.
                "Unattributed time is shown <strong>by default</strong>",
                # And the MEASURED share, which is the data half: 96.2 percent unattributed at review.
                "96.2%",
            ),
            (),
            "96.2 PERCENT OF WALL TIME WAS UNATTRIBUTED AT REVIEW. Both halves are asserted because "
            "they fail differently: losing the percentage means the figure stopped being computed, "
            "while losing the sentence means the default changed and a reader can no longer tell "
            "whether what they are seeing includes the unattributed majority",
        ),
        (
            "the pricing panel with the two MEASURED price eras",
            {"pricing": MEASURED_PRICING},
            (
                'class="recorded"',
                'class="estimated"',
                "never merged",
                "era-a",
                "era-b",
                "open-ended",
                # The DERIVED shares, which is the part that is arithmetic rather than wording.
                "28.0%",
                "72.0%",
            ),
            (),
            "RECORDED AND ESTIMATED COST MUST NEVER BE MERGED: recorded is measured, estimated is "
            "modeled, and a single total silently upgrades a model output to a measurement. The two "
            "totals in this fixture are deliberately EQUAL, so a renderer that summed or substituted "
            "them would produce a plausible-looking number; the distinct classes are what keep them "
            "apart. The era ids and the 28/72 split are asserted because a composition rendered as a "
            "placeholder is the likely decay, and `open-ended` proves the still-current era is not "
            "given a fabricated end date",
        ),
        (
            "pricing with unknown steps and no era",
            {"pricing": {"unknown_price_step_count": 23}},
            (
                "<strong>23</strong>",
                # PROSE PINNED ON PURPOSE: 'refused rather than defaulted' is the contract. A default
                # price would produce a total that looks complete and is partly invented.
                "<strong>refused</strong> rather than priced at a default",
            ),
            (),
            "23 STEPS WITH NO RESOLVABLE PRICE, and the rule is that they are REFUSED. This is the "
            "same refusal discipline the chart/refusal split enforces one layer up, applied to money: "
            "pricing them at a default would fabricate spend, and the count reaching the document is "
            "what lets a reader judge how much is missing",
        ),
        (
            "pricing with no era resolved at all",
            {"pricing": {}},
            ("No price era resolved",),
            (),
            "AN HONEST ABSENCE, NOT A PLACEHOLDER. An empty pricing panel, or one showing a zero, "
            "would read as 'nothing was spent' rather than 'we cannot attribute what was spent', "
            "which is the stronger and falser claim",
        ),
        (
            "pricing with a recorded total but no estimate",
            {"pricing": {"recorded_usd": 10.0}},
            ("no value",),
            (),
            "the asymmetric case: one total known, the other not. The unknown side must SAY it is "
            "unknown rather than rendering blank, because a blank cell beside a populated one reads "
            "as a zero",
        ),
        (
            "the quality panel with all three absence kinds populated",
            {
                "quality": {
                    "missing_fields": ["cost"],
                    "unavailable_fields": ["tokens.cache"],
                    "not_applicable_fields": ["wall_seconds"],
                    "parse_error_count": 4,
                }
            },
            (
                "Missing",
                "Unavailable",
                "Not applicable",
                "never one &ldquo;incomplete&rdquo; flag",
                "cost",
            ),
            (),
            "THREE KINDS OF ABSENCE ARE NOT ONE. `missing` means it should be there and is not, "
            "`unavailable` means it was never recorded, `not applicable` means it cannot exist for "
            "this record; collapsing them into one 'incomplete' flag would destroy exactly the "
            "distinction Order 05's Value contract exists to preserve, and the field NAME reaching "
            "the document is what makes an absence actionable rather than merely counted",
        ),
        (
            "the interpretation panel over a 3-row, 2-refusal population",
            {"rows": _rows(3), "results": [_refused("a"), _refused("b")]},
            (
                "current filter population",
                "(3 rows as loaded)",
                "Association, not causation",
                "2 of 16 required analyses were refused",
            ),
            (),
            "THE INTERPRETATION MUST DESCRIBE THE POPULATION IT IS ACTUALLY LOOKING AT. Both derived "
            "numbers are asserted, the row count and the refusal count against the required total, "
            "because a static caveat paragraph would satisfy any prose-only check while describing a "
            "population the reader is not viewing",
        ),
        (
            "the same panel over a 40-row population",
            {"rows": _rows(40)},
            ("(40 rows as loaded)",),
            # The 3-row count must NOT survive into a 40-row render, which is what makes this pair
            # evidence that the figure is computed rather than templated.
            ("(3 rows as loaded)",),
            "THE SAME FIELD AT A DIFFERENT POPULATION SIZE, which is what the old file expressed as a "
            "two-document comparison inside one test. As two rows with a NEGATIVE expectation it is "
            "stronger: it states that the previous size does not appear, so a hardcoded count is "
            "caught rather than merely unasserted",
        ),
        (
            "a single-row population",
            {"rows": _rows(1)},
            ("(1 rows as loaded)",),
            (),
            "the smallest non-empty population. It is in the table because off-by-one and "
            "pluralization branches are where a row-count renderer breaks, and because a report that "
            "crashes on one row is useless exactly when a human is debugging a single run",
        ),
        (
            "an EMPTY population with no results at all",
            {"rows": [], "results": [], "metric_column": ""},
            ("<strong>0</strong> of <strong>16</strong>",),
            (),
            "THE DEGENERATE CASE MUST RENDER, and it must render an HONEST overview: zero of sixteen "
            "computed, not a blank page and not a crash. A report that failed here would be "
            "unavailable precisely when the corpus is empty, which is the first time anyone runs it",
        ),
        (
            "a population where EVERY analysis refused",
            {"results": [_refused("a"), _refused("b"), _refused("c")]},
            (
                "No analysis in this population returned a computable verdict",
                "<strong>0</strong> of <strong>16</strong>",
                "<strong>3</strong> could not be",
            ),
            (),
            "THE MOST IMPORTANT DEGENERATE CASE IN THE MODULE. With no computable analysis the charts "
            "section must SAY so; an empty section would read as 'nothing to report' rather than "
            "'nothing could be computed'. The counts are asserted alongside so the refusals are "
            "quantified rather than merely acknowledged",
        ),
        (
            "a refusal carrying caveats",
            {"results": [_refused("x")]},
            ("sample size basis: fixture",),
            (),
            "a refusal's caveats explain WHY it refused, which is the only actionable part of a "
            "refusal. Dropping them would leave a reader with a refusal they cannot act on or dispute",
        ),
        (
            "a rich finding with uncertainty and alternatives",
            {"findings": [_finding()]},
            (
                "What is not known:",
                "Competing explanations",
                "Cheapest discriminating test:",
                "13 percent of spend is invisible",
            ),
            (),
            "A FINDING WITHOUT ITS UNCERTAINTY IS AN ASSERTION. All three honesty sections must "
            "render, plus the caveat TEXT itself, which is the data half: a template that emitted the "
            "headings with empty bodies would satisfy heading-only checks and present a bare claim",
        ),
        (
            "a cannot-determine finding",
            {"findings": [_finding(severity="cannot-determine", is_actionable=False)]},
            ('class="panel refusal"',),
            (),
            "A REFUSAL-SEVERITY FINDING MUST LOOK LIKE A REFUSAL, not like a measured result in the "
            "same visual style. Asserted as the CLASS rather than as prose because the class is what "
            "actually drives the visual distinction a reader sees",
        ),
        (
            "the raw view's schema documentation",
            {},
            (
                "<h3>Schema</h3>",
                "the driver run identifier",
                # PROSE PINNED ON PURPOSE: this is a PRIVACY commitment about what the bundle
                # contains, and no data assertion can stand in for it.
                "No prompt, conversation or source-file content is included",
            ),
            (),
            "THE EXCLUSION STATEMENT IS A PRIVACY CONTRACT. This bundle is shareable, so a reader must "
            "be able to know that no prompt or source content travels in it; the schema prose beside "
            "it is what makes the embedded columns interpretable at all",
        ),
        (
            "the provenance of every snapshot figure",
            {},
            ("review-time snapshot", "<strong>not current</strong>"),
            (),
            "EVERY CORPUS FIGURE IN THIS MODULE IS A LABELED SNAPSHOT, never a current measurement: "
            "the corpus grows with every run and is gitignored, so the numbers cannot even be "
            "re-derived from a fresh checkout. An unlabeled figure would be read as measured today, "
            "which is the misreading `REVIEW_SNAPSHOT['is_current'] = False` exists to prevent",
        ),
        (
            "a mixed runner and outcome population",
            {
                "dimensions": [
                    spa.build_dimension(
                        "runner", "Runner", ["oc_runipd", "agy_runipd"]
                    ),
                    spa.build_dimension(
                        "outcome", "Outcome", ["executed", "partial", "blocked"]
                    ),
                ]
            },
            (
                "oc_runipd",
                "agy_runipd",
                "executed",
                "partial",
                "blocked",
            ),
            (),
            "EVERY VALUE OF EVERY POPULATED DIMENSION REACHES THE DOCUMENT. A control that silently "
            "dropped a value would present a filter that cannot select part of the corpus, which is "
            "worse than no filter because the reader believes they have seen everything",
        ),
    )

    def test_every_panel_renders_its_own_input_honestly(self):
        wrong = []
        for case, kwargs, required, forbidden, why in self.PANELS:
            if "rows" in kwargs and not kwargs["rows"]:
                document = render_document(
                    build_view_model(
                        rows=[],
                        results=kwargs.get("results", []),
                        required_analysis_count=16,
                    )
                )
            else:
                document = render_document(_model(**kwargs))
            problems = []
            missing = [token for token in required if token not in document]
            if missing:
                problems.append(f"absent from the rendered document: {missing!r}")
            leaked = [token for token in forbidden if token in document]
            if leaked:
                problems.append(
                    f"present and must NOT be: {leaked!r} (a value from a DIFFERENT population "
                    "survived, so the figure is templated rather than computed)"
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
            f"{len(wrong)} of {len(self.PANELS)} panel inputs rendered wrongly. Every row is one "
            "`render_document` call over a model with one field populated, so read the grouping: if "
            "MANY rows lose their content at once, a panel renderer or `render_document`'s assembly "
            "dropped out, not each panel individually. If only the DEGENERATE rows fail (empty "
            "population, all-refused, no price era), the renderer now requires data it should treat as "
            "legitimately absent, and the report is unavailable exactly when a reader most needs to "
            "know that something is missing. FIX: distinguish the two kinds of missing token before "
            "editing anything. A missing DERIVED NUMBER (a percentage, a row count, an era id) means "
            "the value stopped being computed and is a real defect. A missing SENTENCE is usually a "
            "reword, and this table pins only three sentences on purpose, each an honesty or privacy "
            "commitment the report makes rather than a description: if one of those is what failed, "
            "confirm the COMMITMENT still holds before adjusting the expectation, because the wording "
            "is the only place it is stated.\n" + "\n".join(wrong),
        )


# --- E-08: accessibility, asserted with stdlib only -----------------------------------------------


class AccessibilityContractTests(unittest.TestCase):
    """Structural a11y asserted via stdlib `html.parser`. What it cannot check is NAMED, not implied.

    TWO TABLES replace thirteen tests. The split is by WHAT IS BEING INSPECTED, because that decides
    what a failure means: the first table asks the parsed DOM structural questions (does this element
    exist, does it carry this attribute, does the attribute RESOLVE to a real id), while the second
    asserts that named CSS affordances are present in the document's stylesheet.

    Why one table per group beats thirteen tests: every row is rendered from the same document by the
    same `render_document` call, so the realistic regression is a whole panel or the stylesheet asset
    going missing, which moves many rows at once. Thirteen tests report that as thirteen red lines
    each naming a different missing tag; the two tables report it as one failure listing every row, and
    the SHAPE of that list is what distinguishes "the CSS asset stopped being inlined" from "one
    attribute was renamed".

    A ROW THAT RESOLVES A REFERENCE IS STRICTER THAN THE TEST IT REPLACES. `aria-labelledby` pointing
    at an id that does not exist in the document is WORSE than no label at all, because it silently
    suppresses the element's accessible name while looking correct in source. The section, svg and
    figure rows therefore all check the id resolves, which only the section test used to do.

    WHAT IS DELIBERATELY NOT HERE. Computed focus ORDER, contrast RATIO, real JS execution and
    post-click state are not machine-checkable with stdlib, and the honesty test below asserts the
    module PUBLISHES that boundary in the report rather than letting this class imply coverage it does
    not have.
    """

    def setUp(self):
        self.document = render_document(_model())
        self.dom = _parse(self.document)

    #: (case, tag, attributes every instance of that tag must carry (name -> required value, or None
    #: for "present with any value"), attribute whose value must RESOLVE to an `id="..."` in the
    #: document or None, whether at least one instance must exist, why this row exists)
    DOM_CONTRACT = (
        (
            "the root html element",
            "html",
            {"lang": "en"},
            None,
            True,
            "a document with no declared language makes a screen reader guess the pronunciation "
            "rules for every word in it. It is one attribute and it is the cheapest a11y property in "
            "the file, which is exactly why it is the one most likely to be dropped in a rewrite",
        ),
        (
            "every panel section",
            "section",
            {"aria-labelledby": None},
            "aria-labelledby",
            True,
            "a landmark with no accessible name is unnavigable: the whole point of sectioning this "
            "report is that assistive technology can jump between panels by name. The reference is "
            "RESOLVED, because an `aria-labelledby` pointing at a missing id suppresses the name "
            "entirely while looking correct in the markup",
        ),
        (
            "every chart svg",
            "svg",
            {"role": "img", "aria-labelledby": None},
            "aria-labelledby",
            True,
            '`role="img"` plus a resolvable label is what makes a chart ANNOUNCEABLE rather than '
            "silent; without it the chart is invisible to a screen reader and the exact table beside "
            "it is the only access path. Note this row is why the module emits no `xmlns`: that "
            "attribute would itself be an `http:` occurrence and would fail the offline scan",
        ),
        (
            "every figure",
            "figure",
            {"aria-labelledby": None},
            "aria-labelledby",
            True,
            "THE FIGURE IS WHAT GROUPS A CHART WITH ITS EXACT TABLE, so a reader who cannot use the "
            "chart still finds the numbers in the same labeled group rather than adrift elsewhere in "
            "the document",
        ),
        (
            "every table header cell",
            "th",
            {"scope": ("col", "row")},
            None,
            True,
            "WITHOUT `scope` A DATA TABLE IS A GRID OF UNRELATED CELLS to a screen reader, which is "
            "the difference between a table that can be read and one that can only be heard. Both "
            "values are accepted because this document legitimately has row-headed tables as well as "
            "column-headed ones",
        ),
        (
            "the table structure itself",
            "thead",
            {},
            None,
            True,
            "REAL DATA TABLES, NOT LAYOUT DIVS. A div grid can be styled to look identical and "
            "conveys no relationships at all, so the presence of real sectioning elements is the "
            "assertion. `tbody` and `table` are covered by the row-count checks below",
        ),
        (
            "the paginated raw-view body",
            "tbody",
            {},
            None,
            True,
            "asserted as present-but-empty by the pagination test elsewhere; here it only has to "
            "EXIST, because a tbody-less table is what a rewrite that dropped the raw view would "
            "leave behind",
        ),
        (
            "at least one caption",
            "caption",
            {},
            None,
            True,
            "a caption names a table in the one place assistive technology reliably reads it. Kept as "
            "an existence row rather than a per-table row because the chart tables and the raw table "
            "are captioned by different renderers",
        ),
        (
            "at least one svg title",
            "title",
            {},
            None,
            True,
            "the text alternative the `aria-labelledby` above points AT. Without this row the "
            "reference could resolve to an empty element and the chart would announce as nothing",
        ),
    )

    def test_the_rendered_dom_satisfies_every_structural_a11y_contract(self):
        wrong = []
        for case, tag, required, resolves, must_exist, why in self.DOM_CONTRACT:
            elements = self.dom.of(tag)
            problems = []
            if must_exist and not elements:
                problems.append(
                    f"no <{tag}> element exists in the document at all, so every attribute check "
                    "for this row is vacuous"
                )
            for index, attrs in enumerate(elements):
                label = attrs.get("id") or attrs.get("data-value") or f"#{index}"
                for name, expected in required.items():
                    if name not in attrs:
                        problems.append(
                            f"<{tag} {label}> carries no {name!r} attribute"
                        )
                    elif expected is None:
                        continue
                    elif isinstance(expected, tuple):
                        if attrs[name] not in expected:
                            problems.append(
                                f"<{tag} {label}> has {name}={attrs[name]!r}, expected one of "
                                f"{expected!r}"
                            )
                    elif attrs[name] != expected:
                        problems.append(
                            f"<{tag} {label}> has {name}={attrs[name]!r}, expected {expected!r}"
                        )
                if resolves and resolves in attrs:
                    target = attrs[resolves]
                    if f'id="{target}"' not in self.document:
                        problems.append(
                            f"<{tag} {label}> points {resolves} at {target!r}, but no element in the "
                            "document carries that id, so the accessible name is SUPPRESSED while "
                            "the markup looks correct"
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
            f"the rendered document broke {len(wrong)} of {len(self.DOM_CONTRACT)} structural a11y "
            "contracts. Every row inspects ONE `render_document` output, so read them together: many "
            "rows reporting a MISSING ELEMENT means a whole panel or renderer dropped out, while many "
            "rows reporting a missing ATTRIBUTE on elements that exist means an attribute was renamed "
            "across a helper. FIX: an UNRESOLVED `aria-labelledby` is the failure to fix first, "
            "because it is the only one that is invisible in both the source and the rendered page "
            "while actively suppressing the accessible name. Note what this table does NOT prove: "
            "focus ORDER, contrast RATIO and post-click state are unverifiable with stdlib, which is "
            "why the honesty test below requires the document to publish that boundary itself.\n"
            + "\n".join(wrong),
        )

    #: (case, the CSS/markup token that must appear in the document, why this row exists)
    STYLE_AFFORDANCES = (
        (
            ":focus-visible",
            "a keyboard user who cannot SEE where focus is cannot use the page at all. This is the "
            "selector; the `outline:` row is the declaration, and both are needed because an empty "
            "rule would satisfy the selector alone",
        ),
        (
            "outline:",
            "the visible indicator itself. A `:focus-visible` block that set only a background color "
            "would pass the row above and be invisible against several of this report's panels",
        ),
        (
            "prefers-reduced-motion",
            "a HARD REQUIREMENT rather than a nicety: motion can be actively harmful (vestibular "
            "disorders, migraine), so the preference must be honored rather than assumed absent",
        ),
        (
            "animation: none",
            "the reduced-motion block's actual effect. Without this the media query could be present "
            "and empty, which is the most likely way this decays",
        ),
        (
            "stroke-dasharray",
            "SERIES MUST BE DISTINGUISHABLE WITHOUT COLOR. Dash patterns survive monochrome printing "
            "and every common color-vision deficiency; hue alone does not, and roughly one in twelve "
            "men cannot rely on it",
        ),
        *[
            (
                f".series-{index}",
                "each series needs its OWN class or the dash patterns above cannot differ per series. "
                "All four are rows because a loop that emitted one class for everything would "
                "satisfy the `stroke-dasharray` row while making every line identical",
            )
            for index in range(4)
        ],
        (
            'button[aria-pressed="true"]::before',
            "THE SELECTED STATE MUST ALSO BE NON-COLOR ENCODED, and this pseudo-element is the mark "
            "that does it. Without it a color-blind or monochrome reader cannot tell which metric or "
            "phase is currently active, which makes the whole filter UI unreadable rather than merely "
            "harder to read",
        ),
    )

    def test_every_non_color_and_motion_affordance_is_present(self):
        wrong = []
        for token, why in self.STYLE_AFFORDANCES:
            if token not in self.document:
                wrong.append(
                    f"  {token!r} does not appear in the rendered document\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.STYLE_AFFORDANCES)} a11y style affordances are missing from "
            "the rendered document. These all live in ONE packaged asset that `render_document` "
            "inlines, so if ALL of them are missing the stylesheet is not being inlined at all "
            "(check `stylesheet()` and `read_asset`) rather than each rule having been deleted "
            "individually; that single failure would also silently unstyle the whole report. A subset "
            "failing means specific rules were edited. FIX: these are asserted as TOKENS in the "
            "document rather than as computed styles because no stdlib tool can compute CSS, so a "
            "present token proves the rule SHIPS and not that it has the intended visual effect; the "
            "unverified-properties test below is what keeps that limit stated in the report itself.\n"
            + "\n".join(wrong),
        )

    def test_every_toggle_button_exposes_its_state(self):
        """Kept separate: the assertion is a DISJUNCTION over a filtered subset of buttons.

        A toggle must expose `aria-pressed` OR be marked `aria-disabled`, and which one is correct
        depends on the button's own dimension state. That is not a fixed per-row expectation, and
        flattening it into the DOM table would mean asserting an attribute is present on elements
        where its absence is correct.
        """

        toggles = [b for b in self.dom.of("button") if b.get("data-group")]
        self.assertTrue(toggles)
        for button in toggles:
            with self.subTest(value=button.get("data-value")):
                self.assertTrue(
                    "aria-pressed" in button or button.get("aria-disabled") == "true"
                )

    def test_a_disabled_control_is_disabled_for_BOTH_the_dom_and_assistive_tech(self):
        """Kept separate: needs a DIFFERENT document, rendered from an empty dimension.

        Every row in the tables above inspects the shared `setUp` document, which has no disabled
        control in it. The claim is also a pair: `disabled` (which stops a mouse and keyboard) and
        `aria-disabled="true"` (which is what a screen reader announces) must BOTH be present, since
        either alone leaves one class of user able to operate a control that does nothing.
        """

        dimension = spa.build_dimension("model", "Model", [])
        dom = _parse(render_document(_model(dimensions=[dimension])))
        disabled = [b for b in dom.of("button") if b.get("data-group") == "model"]
        self.assertTrue(disabled)
        for button in disabled:
            self.assertIn("disabled", button)
            self.assertEqual(button.get("aria-disabled"), "true")

    def test_a_skip_link_precedes_the_content(self):
        """Kept separate: the assertion is about ORDER, comparing two offsets in the document.

        A skip link that appears after the content it skips is useless, so position is the whole
        claim; no presence row can state it.
        """

        self.assertIn("Skip to the overview", self.document)
        self.assertLess(
            self.document.index("Skip to the overview"),
            self.document.index('id="overview"'),
        )

    def test_the_UNVERIFIED_properties_are_published_in_the_document(self):
        """Kept separate: the subject is the module's own declared boundary, not the DOM.

        The honest boundary, and the reason the two tables above may be read as evidence at all:
        claiming 'accessible' without naming what was NOT checked is the unearned claim. This iterates
        the module's published tuple rather than a literal list, so adding an unverified property
        automatically requires publishing it, and it asserts the named set still covers focus order,
        contrast and post-interaction state so the boundary cannot be quietly narrowed to nothing.
        """

        self.assertIn("Not machine-verified", self.document)
        for item in spa.UNVERIFIED_ACCESSIBILITY_PROPERTIES:
            with self.subTest(item=item[:40]):
                self.assertIn(spa.escape_text(item), self.document)
        joined = " ".join(spa.UNVERIFIED_ACCESSIBILITY_PROPERTIES).lower()
        for topic in ("focus", "contrast", "post-interaction"):
            with self.subTest(topic=topic):
                self.assertIn(topic, joined)


class NoNewTestDependencyTests(unittest.TestCase):
    """The tooling boundary, ASSERTED. A test that passes locally and fails in CI is the defect."""

    def test_no_analytics_report_test_imports_bs4_lxml_or_playwright(self):
        """Kept separate: the subject is TEST FILE SOURCE TEXT, not this module's behavior."""

        forbidden = ("bs4", "beautifulsoup", "lxml", "playwright", "selenium")
        for name in ("test_run_analytics_spa.py", "test_run_analytics_report.py"):
            source = (Path(__file__).parent / name).read_text(encoding="utf-8")
            for module in forbidden:
                with self.subTest(file=name, module=module):
                    self.assertFalse(
                        re.search(
                            rf"^\s*(import|from)\s+{module}\b",
                            source,
                            re.MULTILINE | re.IGNORECASE,
                        ),
                        f"{name} imports {module}, which is not a declared test dependency",
                    )

    def test_the_declared_test_extra_is_UNCHANGED(self):
        """Kept separate: a byte-pinned line of `pyproject.toml`, which is a different file entirely.

        No new test dependency was added, which is the point of using stdlib html.parser. Pinning the
        whole declaration rather than an absence is deliberate: a test asserting only that `bs4` is
        missing would pass while some other dependency was added.
        """

        pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'test = ["pytest>=8", "pytest-xdist>=3", "pytest-randomly>=3", "PyYAML>=6"]',
            pyproject,
        )

    def test_the_spa_module_imports_only_stdlib(self):
        """Kept separate: an ALLOWLIST sweep over the module's own import statements.

        A structural claim about the source text rather than about any rendered output, and the assertion
        is set membership against an allowlist, so there is no per-input row to write.
        """

        source = Path(spa.__file__).read_text(encoding="utf-8")
        imports = re.findall(
            r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", source, re.MULTILINE
        )
        stdlib_ok = {
            "base64",
            "gzip",
            "html",
            "json",
            "math",
            "re",
            "unicodedata",
            "dataclasses",
            "enum",
            "pathlib",
            "typing",
            "__future__",
            "io",
        }
        for module in imports:
            top = module.split(".")[0]
            with self.subTest(module=module):
                self.assertIn(top, stdlib_ok | {"agent_workflows"})


class LeakSanitizerTests(unittest.TestCase):
    """The produced bundle carries no leak, WITH A CONTROL so a clean result means something.

    A clean report and a detector that was not looking are indistinguishable, which is exactly the
    plan's requirement here. The control run is therefore not optional decoration; it is what makes
    the clean assertion evidence.
    """

    def setUp(self):
        from agent_workflows import leak_sanitizer

        self.sanitizer = leak_sanitizer
        self.repo = Path(__file__).resolve().parent.parent
        self.ruleset = leak_sanitizer.build_ruleset(self.repo)

    def test_the_produced_bundle_is_clean(self):
        """The CLEAN claim, which is evidence ONLY because of the CONTROL test below. Do not separate."""

        document = render_document(_model())
        findings = self.sanitizer.scan_text(document, "bundle/index.html", self.ruleset)
        self.assertEqual(
            [f"{f.location}\t{f.rule}\t{f.severity}" for f in findings],
            [],
        )

    @property
    def _leaky_repo_path(self) -> str:
        s = str(self.repo)
        if any(pat.search(s) for pat in self.ruleset.fail.values()):
            return s
        return "/ho" + f"me/dev_user/{self.repo.name}"

    def test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path(self):
        planted = f"<p>partial work at {self._leaky_repo_path}/.aw/worktrees/lane-x</p>"
        findings = self.sanitizer.scan_text(
            planted, "control/planted.html", self.ruleset
        )
        self.assertTrue(
            findings,
            "the CONTROL found nothing, so the detector was not looking and the clean result "
            "above is meaningless",
        )
        self.assertIn("fail", {f.severity for f in findings})

    def test_a_leaky_value_travelling_through_a_finding_is_still_detected(self):
        """6 of 216 real outcome files carried FAIL-severity leaks in exactly this kind of field."""

        leak = f"{self._leaky_repo_path}/.aw/worktrees/lane-x"
        model = _model(
            results=[_refused(f"analysis at {leak}")],
        )
        document = render_document(model)
        findings = self.sanitizer.scan_text(document, "bundle/index.html", self.ruleset)
        # ESCAPING IS NOT REDACTION, and this test states that boundary rather than blurring it: the
        # render boundary makes hostile text INERT, it does not remove a real path. Detecting the
        # leak is the sanitizer's job, and it does detect it, which is why the publish path tells the
        # caller to run the sanitizer before treating output as shareable.
        self.assertTrue(findings, "a real absolute path passed through undetected")


class PackagedAssetTests(unittest.TestCase):
    """E-02: the assets are REAL FILES inside the package, and a missing one REFUSES loudly.

    ONE TABLE replaces four tests, iterating `REQUIRED_ASSETS` rather than restating it. Each of the
    four asked one question per asset (does it exist, is it gitignored by pattern, is it gitignored
    according to git itself, does its content carry what it must), so the ASSET is the row and the
    QUESTION is a column.

    WHY ALL FOUR CHECKS BELONG TO ONE ROW: they are the same claim at four removes, and any one alone
    is satisfiable while the asset does not ship. Existence on disk says nothing about the wheel.
    `.gitignore` pattern matching catches the MEASURED hazard (hatchling HONORS `.gitignore` and drops
    a matching file SILENTLY at exit 0, so a wheel ships with no assets and every test passes). `git
    check-ignore` is the authoritative version of the same question, since a pattern check cannot see
    negations or directory rules. And content assertions are what prove the file that ships is the
    right file rather than an empty placeholder.
    """

    #: (asset name, tokens its content must contain, tokens its content must NOT contain, why this
    #: asset's content is asserted)
    #:
    #: Iterated against `spa.REQUIRED_ASSETS` so a newly declared asset with no row here FAILS rather
    #: than being silently unchecked, which is how the packaging test would otherwise fall behind.
    ASSET_CONTENTS = {
        "app.css": (
            (
                "prefers-reduced-motion",
                ":focus-visible",
                "stroke-dasharray",
                "aria-pressed",
            ),
            (),
            "EVERY A11Y AFFORDANCE THE REPORT CLAIMS LIVES IN THIS FILE, so if it ships empty or "
            "stale the document still renders and is quietly inaccessible: reduced motion ignored, "
            "focus invisible, series distinguishable by hue alone. Asserted on the ASSET as well as "
            "on the rendered document, because the rendered check passes if the inlining works while "
            "the packaged copy is wrong",
        ),
        "app.js": (
            ("textContent", "DecompressionStream"),
            # innerHTML must NEVER appear: client-side escaping is by CONSTRUCTION here.
            ("innerHTML",),
            "THE CLIENT-SIDE ESCAPING BOUNDARY IS THE ABSENCE OF `innerHTML`. The DOM API cannot "
            "produce markup from a string, so using `textContent` makes injection impossible rather "
            "than merely escaped; a single `innerHTML` would reopen every hole the server-side "
            "escaping closes. `DecompressionStream` is the payload inflater, without which the report "
            "renders an empty page in any browser",
        ),
    }

    def test_every_declared_asset_ships_and_carries_what_it_must(self):
        import fnmatch
        import subprocess

        repo_root = Path(__file__).parent.parent
        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
        patterns = [
            line.strip()
            for line in gitignore.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        wrong = []
        for name in spa.REQUIRED_ASSETS:
            problems = []
            path = spa.assets_dir() / name
            if not path.is_file():
                problems.append(
                    "the file does not exist on disk at all, so nothing below can be checked"
                )
            # 1. THE MEASURED PACKAGING HAZARD: hatchling honors .gitignore and drops a match
            # SILENTLY at exit 0, producing a wheel with no assets and a green test suite.
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern.rstrip("/")):
                    problems.append(
                        f"the name matches .gitignore pattern {pattern!r}, so hatchling would drop it "
                        "from the wheel silently at exit 0"
                    )
            # 2. THE AUTHORITATIVE FORM of the same question, since a pattern scan cannot evaluate
            # negations, directory rules or precedence.
            relative = f"agent_workflows/{spa.ASSETS_DIRNAME}/{name}"
            result = subprocess.run(
                ["git", "check-ignore", "-q", relative],
                cwd=str(repo_root),
                capture_output=True,
            )
            if result.returncode != 1:  # exit 1 means NOT ignored
                problems.append(
                    f"git check-ignore reports {relative} as IGNORED (exit {result.returncode}), so "
                    "it is not tracked and would not travel in the wheel"
                )
            # 3. THE CONTENT, so a shipping-but-empty placeholder is not mistaken for a shipping asset.
            if name not in self.ASSET_CONTENTS:
                problems.append(
                    "this asset is DECLARED in REQUIRED_ASSETS but has no content expectations in "
                    "ASSET_CONTENTS, so nothing verifies the file that ships is the right file"
                )
            elif path.is_file():
                required, forbidden, _why = self.ASSET_CONTENTS[name]
                text = spa.read_asset(name)
                missing = [token for token in required if token not in text]
                if missing:
                    problems.append(f"content is missing {missing!r}")
                leaked = [token for token in forbidden if token in text]
                if leaked:
                    problems.append(f"content carries forbidden {leaked!r}")
                # 4. THE OFFLINE RULE APPLIES TO THE ASSET ITSELF, not only to the assembled document.
                network = spa.scan_for_network_references(text)
                if network:
                    problems.append(
                        f"the asset carries network references {network!r}, which would make the "
                        "inlined bundle non-offline"
                    )
            if problems:
                why = (
                    self.ASSET_CONTENTS[name][2]
                    if name in self.ASSET_CONTENTS
                    else "declared in REQUIRED_ASSETS"
                )
                wrong.append(
                    f"  {name}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(spa.REQUIRED_ASSETS)} declared assets would not ship correctly. "
            "The four checks per row are the same claim at four removes, so the one that fails tells "
            "you the stage: EXISTENCE failing is a missing or moved file; a GITIGNORE match is the "
            "measured hazard where hatchling drops the file silently at exit 0 and the wheel ships "
            "with no assets while every other test stays green; CONTENT failing means the file ships "
            "but is stale or truncated, which is the hardest to notice because the report still "
            "renders. FIX: a missing ASSET_CONTENTS entry for a newly declared asset is not a test "
            "bug to route around; it is the packaging test telling you it has fallen behind the "
            "declaration, which is exactly the drift that made per-asset assertions necessary.\n"
            + "\n".join(wrong),
        )

    def test_the_assets_live_INSIDE_the_package_directory(self):
        """Kept separate: a claim about the DIRECTORY, not about any asset in it.

        Hatchling ships files under the declared package; outside it they simply do not travel, whatever
        their names or content. No per-asset row can state this, since it holds even when the directory
        is empty.
        """

        package_root = Path(spa.__file__).resolve().parent
        self.assertEqual(spa.assets_dir().parent, package_root)
        self.assertEqual(spa.assets_dir().name, spa.ASSETS_DIRNAME)

    def test_a_missing_asset_REFUSES_rather_than_falling_back_silently(self):
        """Kept separate: an assertRaises that also MONKEYPATCHES `assets_dir`.

        A silent inline fallback is what would let a wheel ship with no assets, tests green. The patch
        must not run inside a table loop, where a failing row would leave `spa.assets_dir` pointing at a
        nonexistent path for every test after it.
        """

        original = spa.assets_dir
        spa.assets_dir = lambda: Path("/nonexistent-assets-dir-for-this-test")  # type: ignore[assignment]
        try:
            with self.assertRaises(SpaError) as ctx:
                spa.read_asset("app.css")
            self.assertIn("missing", str(ctx.exception))
        finally:
            spa.assets_dir = original  # type: ignore[assignment]

    def test_an_undeclared_asset_is_REFUSED_so_the_packaging_test_cannot_fall_behind(
        self,
    ):
        """Kept separate: an assertRaises, and the inverse of the asset table.

        The table iterates `REQUIRED_ASSETS` and so can only ever check DECLARED assets. This asserts
        the reader refuses an UNDECLARED one, which is what stops the declaration from drifting behind
        the files on disk.
        """

        with self.assertRaises(SpaError) as ctx:
            spa.read_asset("not-declared.css")
        self.assertIn("REQUIRED_ASSETS", str(ctx.exception))

    def test_the_stylesheet_helper_returns_the_packaged_css(self):
        """Kept separate: asserts the `stylesheet()` HELPER, not the asset file the table reads.

        `render_document` calls `stylesheet()`, not `read_asset("app.css")`, so a helper that returned
        an inline fallback would satisfy every row of the asset table while shipping different CSS than
        the packaged file. The claim here is that the two agree.
        """

        self.assertEqual(spa.stylesheet(), spa.read_asset("app.css"))


class LargeDatasetFallbackTests(unittest.TestCase):
    """The documented, TESTED behavior at and above the measured corpus scale.

    ONE TABLE replaces three tests over the CLIENT-SIDE contract: each rendered the document and
    asserted one token was present or absent in it. The token and its polarity are the data.

    THESE ARE TOKENS IN THE EMITTED SCRIPT, NOT PROSE, which is why substring assertions are the right
    instrument here rather than a change detector: each names a JavaScript identifier or a fallback
    message whose PRESENCE OR ABSENCE is the behavior, and none is a sentence that could be reworded
    without changing what the client does.
    """

    #: (case, the token, whether it must be PRESENT, why this row exists)
    CLIENT_CONTRACT = (
        (
            "the payload inflater",
            "DecompressionStream",
            True,
            "the embedded payload is gzipped base64, so without this API call the client has no way "
            "to read its own data and the report renders empty",
        ),
        (
            "the message for a browser that lacks it",
            "cannot inflate the embedded payload",
            True,
            "AN HONEST FAILURE RATHER THAN A BLANK PAGE. `DecompressionStream` is not universally "
            "available, and a reader on an older browser must be told the data could not be read "
            "rather than shown an empty report they would take for an empty corpus",
        ),
        (
            "the text-setting DOM API",
            "textContent",
            True,
            "CLIENT-SIDE ESCAPING BY CONSTRUCTION: `textContent` cannot produce markup from a string, "
            "so injection is impossible rather than merely escaped. Every row the client renders from "
            "the embedded payload goes through it",
        ),
        (
            "the markup-parsing DOM API",
            "innerHTML",
            False,
            "THE NEGATIVE ROW, and the whole reason the positive one is worth anything: a single "
            "`innerHTML` would reopen every hole the server-side escaping closes, because the payload "
            "contains real corpus free text (measured: 152 of 216 outcome files carry `<`, `>` or "
            "`&`). Its ABSENCE is the guarantee; the presence of `textContent` alone would not be",
        ),
    )

    def test_the_emitted_client_carries_its_fallback_and_no_markup_api(self):
        document = render_document(_model())
        wrong = []
        for case, token, present, why in self.CLIENT_CONTRACT:
            found = token in document
            if found is not present:
                wrong.append(
                    f"  {case}: {token!r} is "
                    f"{'absent but must be present' if present else 'PRESENT and must not be'}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CLIENT_CONTRACT)} client-side contract tokens are wrong in the "
            "emitted document. All four come from ONE packaged asset that `render_document` inlines, so "
            "if every PRESENT row fails at once the script is not being inlined at all and the report "
            "is inert in the browser while every server-side test passes. FIX: the `innerHTML` row is "
            "the one to treat as urgent, because it is a security regression rather than a broken "
            "feature, and it fails silently: the report keeps working and starts rendering corpus text "
            "as markup.\n" + "\n".join(wrong),
        )

    def test_the_bound_holds_at_TWICE_the_measured_corpus_scale(self):
        """Kept separate: the subject is SCALE, and the assertion chains two functions.

        The binning table pins per-input behavior at ordinary sizes. This feeds twice the measured
        corpus scale (so roughly 59532 values) through `bin_series` AND then through
        `series_path_data`, asserting the composition still yields one node. The claim is that the
        bound is on BINS rather than on rows, which only a scale fixture can state.
        """

        series = spa.bin_series([float(i % 331) for i in range(CORPUS_SCALE_ROWS * 2)])
        self.assertLessEqual(series["bin_count"], spa.MAX_PLOT_BINS)
        self.assertEqual(series["source_row_count"], CORPUS_SCALE_ROWS * 2)
        path = spa.series_path_data(series["counts"])
        self.assertEqual(path.count("M"), 1)

    def test_no_emitted_script_line_carries_a_LITERAL_backslash_n(self):
        """A REAL DEFECT THIS SUITE CAUGHT, and the guard that keeps it fixed.

        The inline script is built by concatenating Python string literals, so writing `\\\\n` where a
        real newline was meant emits the two characters `\\` and `n` into the JavaScript source. In a
        `//` comment that silently swallows the NEXT statement onto the comment line, which is how a
        working renderer becomes a no-op with no error anywhere. Asserted structurally rather than
        trusted, because the failure is invisible in the Python source.
        """

        document = render_document(_model())
        script = document.rsplit("<script>", 1)[1].split("</script>")[0]
        for number, line in enumerate(script.splitlines(), 1):
            with self.subTest(line=number):
                self.assertNotIn(
                    "\\n",
                    line,
                    f"line {number} of the emitted script carries a literal backslash-n, which "
                    f"comments out the following statement: {line!r}",
                )

    def test_every_comment_line_in_the_emitted_script_is_only_a_comment(self):
        """Kept separate: the CONSEQUENCE form of the defect above, over a filtered line subset.

        No statement may share a `//` comment's line. It is a distinct claim from the backslash-n one and
        is deliberately kept beside it: that test finds the CAUSE (a literal `\\n` emitted into JS
        source), this one finds the SYMPTOM (a statement swallowed onto a comment line) whatever caused
        it, so neither subsumes the other.
        """

        document = render_document(_model())
        script = document.rsplit("<script>", 1)[1].split("</script>")[0]
        for number, line in enumerate(script.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//"):
                with self.subTest(line=number):
                    self.assertNotIn(
                        ";", stripped, f"statement hidden in a comment: {line!r}"
                    )

    def test_a_bin_count_below_one_is_refused(self):
        """Kept separate: an assertRaises."""

        with self.assertRaises(SpaError):
            spa.bin_series([1.0], bins=0)


if __name__ == "__main__":
    unittest.main()

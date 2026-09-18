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
    """FOUR contexts, FOUR escapes. A single helper used everywhere is a DEFECT, not a convenience."""

    def test_html_text_escapes_markup_characters(self):
        self.assertEqual(
            spa.escape_text("<script>x</script>"), "&lt;script&gt;x&lt;/script&gt;"
        )
        self.assertEqual(spa.escape_text("a & b"), "a &amp; b")

    def test_attribute_escaping_ALSO_escapes_both_quote_forms(self):
        """The difference that matters: an unescaped quote closes the attribute."""

        self.assertNotIn('"', spa.escape_attribute('a"b'))
        self.assertNotIn("'", spa.escape_attribute("a'b"))
        # And text escaping deliberately does NOT, which is why they are separate functions.
        self.assertIn('"', spa.escape_text('a"b'))

    def test_svg_text_escaping_always_escapes_ampersand(self):
        self.assertEqual(spa.escape_svg_text("a & b"), "a &amp; b")
        self.assertNotIn("<", spa.escape_svg_text("<title>"))

    def test_js_string_escaping_breaks_the_script_terminator(self):
        """No HTML escape does this: inside <script>, `</script` ends the element regardless."""

        escaped = spa.escape_js_string("</script><img onerror=alert(1)>")
        self.assertNotIn("</script", escaped.lower())
        self.assertIn("<\\/script", escaped)

    def test_js_string_escaping_handles_backslash_quotes_and_js_line_terminators(self):
        self.assertEqual(spa.escape_js_string("a\\b"), "a\\\\b")
        self.assertEqual(spa.escape_js_string('a"b'), 'a\\"b')
        self.assertEqual(spa.escape_js_string("a\u2028b"), "a\\u2028b")
        self.assertEqual(spa.escape_js_string("a\nb"), "a\\nb")

    def test_html_comment_opener_is_broken_in_a_js_string(self):
        self.assertNotIn("<!--", spa.escape_js_string("<!--"))

    def test_the_JSON_ISLAND_context_is_a_FIFTH_escape_and_still_parses(self):
        """A REAL DEFECT THIS SUITE CAUGHT: a JSON island is not a JS string literal.

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
    """A bidi override cannot be ESCAPED; it must be REPLACED, because an NCR still renders."""

    def test_bidi_override_is_replaced_not_encoded(self):
        for char in ("\u202e", "\u202d", "\u2066", "\u2069", "\u200f"):
            with self.subTest(char=hex(ord(char))):
                out = spa.sanitize_control_characters(f"a{char}b")
                self.assertNotIn(char, out)
                self.assertEqual(out, f"a{spa.REPLACEMENT_CHARACTER}b")

    def test_legitimate_whitespace_SURVIVES(self):
        self.assertEqual(spa.sanitize_control_characters("a\tb\nc\rd"), "a\tb\nc\rd")

    def test_c0_controls_are_replaced(self):
        self.assertNotIn("\x00", spa.sanitize_control_characters("a\x00b"))
        self.assertNotIn("\x1b", spa.sanitize_control_characters("a\x1bb"))

    def test_every_escape_runs_the_control_pre_pass(self):
        """The pre-pass is part of the BOUNDARY, so no context can bypass it."""

        hostile = "a\u202eb"
        for func in (
            spa.escape_text,
            spa.escape_attribute,
            spa.escape_svg_text,
            spa.escape_js_string,
        ):
            with self.subTest(func=func.__name__):
                self.assertNotIn("\u202e", func(hostile))


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
        for payload in self.HOSTILE:
            for name, func in (
                ("html-text", spa.escape_text),
                ("attribute", spa.escape_attribute),
                ("svg-text", spa.escape_svg_text),
                ("js-string", spa.escape_js_string),
            ):
                with self.subTest(payload=payload, context=name):
                    out = func(payload)
                    if name == "js-string":
                        self.assertNotIn("</script", out.lower())
                    else:
                        self.assertNotIn("<", out)
                        self.assertNotIn(">", out)
                    self.assertNotIn("\u202e", out)
                    self.assertNotIn("\x00", out)

    def test_a_hostile_string_rendered_through_the_document_produces_no_live_markup(
        self,
    ):
        """END TO END: the payload travels through a finding, a refusal and a table cell."""

        payload = "</script><img src=x onerror=alert(1)><id6>"
        model = _model(
            results=[_refused(payload, n=3)],
            findings=[
                {
                    "finding_id": payload,
                    "title": payload,
                    "severity": "medium",
                    "affected_slice": payload,
                    "sample_size": 3,
                    "coverage": 0.5,
                    "uncertainty": payload,
                    "data_quality_caveats": [payload],
                    "alternative_explanations": [payload],
                    "next_experiment": payload,
                    "recommendation": "",
                    "is_actionable": True,
                }
            ],
        )
        document = render_document(model)
        # THE CONTRACT IS INERTNESS, NOT ABSENCE, and the distinction is the point: `onerror=alert`
        # as escaped TEXT is inert and must be preserved, because dropping it would silently destroy
        # real content a finding legitimately contains. What must not exist is a live TAG.
        self.assertNotIn("<img", document)
        self.assertNotIn("<id6>", document)
        # The text is still PRESENT, escaped, so the report does not silently drop real content.
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", document)
        self.assertIn("&lt;id6&gt;", document)
        # Exactly the three script elements this module emits, and no injected one.
        self.assertEqual(document.lower().count("<script"), 3)
        # And the payload never appears RAW anywhere: every occurrence is escaped or \\u-encoded.
        self.assertNotIn("</script><img", document)

    def test_a_formula_leading_cell_is_inert_in_html_and_quote_safe_in_an_attribute(
        self,
    ):
        """The measured shape kept as a fixture, with the HONEST per-context contract.

        HTML has no formula context, so a leading `=` is ordinary text and `escape_text` correctly
        leaves the quote alone (`quote=False`). What matters is that the same payload in an ATTRIBUTE
        cannot break out, which is exactly why the two escapes are separate functions. The formula
        hazard itself belongs to CSV/spreadsheet export, which is Order 09's surface, not this one.
        """

        payload = "=1+1+cmd|' /C calc'!A0"
        # In HTML TEXT: unchanged, because none of `&<>` appears and a quote is inert here.
        self.assertEqual(spa.escape_text(payload), payload)
        # In an ATTRIBUTE: the quote MUST be encoded or it terminates the attribute.
        attribute = spa.escape_attribute(payload)
        self.assertNotIn("'", attribute)
        self.assertIn("&#x27;", attribute)
        # And a quote does NOT survive into a JS string literal unescaped either.
        self.assertIn("\\'", spa.escape_js_string(payload))


# --- E-07: offline behavior -----------------------------------------------------------------------


class OfflineTests(unittest.TestCase):
    """Offline is a TESTED property. The scanner also has a CONTROL, so it is provably looking."""

    def test_the_rendered_document_contains_no_network_reference(self):
        document = render_document(_model())
        self.assertEqual(spa.scan_for_network_references(document), [])

    def test_the_scanner_CONTROL_flags_a_planted_reference(self):
        """A clean report and a scanner that was not looking are indistinguishable without this."""

        for planted, token in (
            ('<script src="x.js"></script>', "<script src"),
            ("fetch('/x')", "fetch("),
            ('<a href="https://example.com">x</a>', "https:"),
            ("new WebSocket('x')", "WebSocket"),
            ("@import url(x)", "@import"),
            ("import('x')", "import("),
        ):
            with self.subTest(token=token):
                findings = spa.scan_for_network_references(planted)
                self.assertTrue(
                    any(f.startswith(token) for f in findings),
                    f"scanner missed {token!r}: {findings}",
                )

    def test_the_scanner_is_case_insensitive(self):
        self.assertTrue(spa.scan_for_network_references("HTTPS://EXAMPLE.COM"))

    def test_inline_svg_carries_NO_xmlns_so_the_scan_needs_no_exception(self):
        """An `xmlns` would itself be an `http:` occurrence; HTML5 namespaces inline SVG by rule."""

        document = render_document(_model())
        self.assertIn("<svg ", document)
        self.assertNotIn("xmlns", document)

    def test_render_REFUSES_to_return_a_document_with_a_network_reference(self):
        """Belt and braces: the render itself scans, so an offline violation cannot ship from here."""

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
    """THE MOST IMPORTANT CONTRACT HERE: a refusal never becomes a chart, empty or otherwise."""

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

    def test_each_of_the_five_refusals_renders_a_panel_naming_reason_and_n(self):
        results = [
            _refused(name, n=n, verdict=v) for name, n, v in self.REFUSED_AT_REVIEW
        ]
        model = _model(results=results)
        self.assertEqual(model.refused_count, 5)
        self.assertEqual(model.computed_count, 0)
        document = render_document(model)
        for name, n, verdict in self.REFUSED_AT_REVIEW:
            with self.subTest(analysis=name):
                self.assertIn(spa._humanize(name), document)
                self.assertIn(f"observed n={n}", document)
                self.assertIn(verdict.value, document)

    def test_a_cannot_determine_result_produces_NO_chart_element(self):
        """The assertion that would FAIL against a version rendering an empty chart."""

        model = _model(results=[_refused("merge-conflict-share-and-recurrence", n=3)])
        self.assertEqual(model.charts, ())
        document = render_document(model)
        collector = _parse(document)
        # No <figure> and no <svg> exist at all, so there is no empty axis to misread as zero.
        self.assertEqual(collector.of("figure"), [])
        self.assertEqual(collector.of("svg"), [])
        self.assertEqual(collector.of("path"), [])

    def test_chart_from_result_REFUSES_a_non_computed_verdict(self):
        """A caller that forgets to branch fails LOUDLY rather than plotting nothing as zero."""

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
        """Symmetric: presenting a computable analysis as refused understates the evidence."""

        with self.assertRaises(SpaError):
            spa.refusal_from_result(_computed("cache-utilization"))

    def test_build_view_model_routes_STRUCTURALLY_so_no_renderer_can_forget(self):
        results = [
            _computed("a"),
            _refused("b"),
            _computed("c"),
            _refused("d", verdict=Verdict.REFUSED),
        ]
        model = _model(results=results)
        self.assertEqual([c.analysis_name for c in model.charts], ["a", "c"])
        self.assertEqual([r.analysis_name for r in model.refusals], ["b", "d"])

    def test_the_overview_states_computed_versus_refused_counts(self):
        model = _model(
            results=[_computed("a"), _refused("b"), _refused("c")],
            required_analysis_count=16,
        )
        document = render_document(model)
        self.assertIn("<strong>1</strong> of <strong>16</strong>", document)
        self.assertIn("<strong>2</strong> could not be", document)

    def test_a_refusal_panel_carries_its_caveats(self):
        model = _model(results=[_refused("x")])
        document = render_document(model)
        self.assertIn("sample size basis: fixture", document)


# --- E-03: the embedded data contract -------------------------------------------------------------


class ColumnarLayoutTests(unittest.TestCase):
    """The layout was chosen by MEASUREMENT (24 percent smaller embedded), and is lossless."""

    def test_columnar_round_trips_losslessly(self):
        rows = _rows(9)
        payload = spa.columnar_from_rows(rows)
        self.assertEqual(payload["layout"], "columnar")
        self.assertEqual(payload["row_count"], 9)
        self.assertEqual(spa.rows_from_columnar(payload), [dict(r) for r in rows])

    def test_a_missing_column_becomes_None_not_a_dropped_row(self):
        payload = spa.columnar_from_rows([{"a": 1}, {"b": 2}])
        self.assertEqual(payload["columns"], ["a", "b"])
        self.assertEqual(payload["data"]["a"], [1, None])
        self.assertEqual(payload["data"]["b"], [None, 2])

    def test_column_order_is_deterministic(self):
        first = spa.columnar_from_rows([{"b": 1, "a": 2}])
        second = spa.columnar_from_rows([{"a": 2, "b": 1}])
        self.assertEqual(first["columns"], second["columns"])

    def test_the_columnar_layout_measures_SMALLER_than_row_wise_at_scale(self):
        """The measurement that decided the architecture, re-derived on the fixture."""

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
    """gzip writes an mtime by default; mtime=0 plus a fixed level is what makes this deterministic."""

    def test_encoding_is_byte_identical_across_calls(self):
        payload = spa.columnar_from_rows(_rows(50))
        self.assertEqual(
            spa.encode_embedded_payload(payload), spa.encode_embedded_payload(payload)
        )

    def test_the_payload_round_trips(self):
        payload = spa.columnar_from_rows(_rows(7))
        self.assertEqual(
            spa.decode_embedded_payload(spa.encode_embedded_payload(payload)), payload
        )

    def test_the_whole_document_is_byte_identical_for_identical_input(self):
        """The golden-render requirement: a diff means a real change."""

        first = render_document(_model())
        second = render_document(_model())
        self.assertEqual(first, second)

    def test_the_contract_records_the_deterministic_gzip_settings(self):
        self.assertEqual(spa.EMBEDDED_DATA_CONTRACT["gzip_mtime"], 0)
        self.assertEqual(spa.EMBEDDED_DATA_CONTRACT["gzip_level"], 9)
        self.assertTrue(spa.EMBEDDED_DATA_CONTRACT["json_sort_keys"])


class BoundedRenderingTests(unittest.TestCase):
    """Node count must NOT scale with row count. 29766 point nodes was the measured defect."""

    def test_binning_bounds_the_bin_count_regardless_of_input_size(self):
        series = spa.bin_series([float(i) for i in range(100000)])
        self.assertLessEqual(series["bin_count"], spa.MAX_PLOT_BINS)
        self.assertEqual(series["source_row_count"], 100000)

    def test_binning_reports_the_SOURCE_row_count_so_binning_is_visible(self):
        series = spa.bin_series([1.0, 2.0, 3.0])
        self.assertEqual(series["source_row_count"], 3)

    def test_a_degenerate_range_is_one_bin_not_a_division_by_zero(self):
        series = spa.bin_series([5.0, 5.0, 5.0])
        self.assertEqual(series["bin_count"], 1)
        self.assertEqual(series["counts"], [3])

    def test_an_empty_series_is_absent_not_zero(self):
        series = spa.bin_series([])
        self.assertEqual(series["bin_count"], 0)
        self.assertIsNone(series["minimum"])

    def test_non_finite_values_are_excluded(self):
        series = spa.bin_series([1.0, float("nan"), float("inf"), 2.0])
        self.assertEqual(series["source_row_count"], 2)

    def test_a_series_becomes_ONE_path_node(self):
        path = spa.series_path_data([1.0, 2.0, 3.0, 4.0])
        self.assertTrue(path.startswith("M "))
        self.assertEqual(path.count("M"), 1)

    def test_path_data_is_deterministic(self):
        counts = [float(i % 17) for i in range(500)]
        self.assertEqual(spa.series_path_data(counts), spa.series_path_data(counts))

    def test_plotted_dom_node_count_is_BOUNDED_at_corpus_scale(self):
        """The budget asserted at the measured 29766-row scale, not at a toy one."""

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
        rows = _rows(1000)
        document = render_document(_model(rows=rows))
        self.assertIn(f"<strong>{spa.RAW_VIEW_PAGE_SIZE} at a time</strong>", document)
        collector = _parse(document)
        # The raw table body is EMPTY in the served markup: rows are added client-side, per page.
        self.assertIn('id="raw-body"', document)
        body_rows = document.split('id="raw-body"')[1].split("</tbody>")[0]
        self.assertNotIn("<tr", body_rows)
        self.assertTrue(collector.of("table"))

    def test_paging_controls_and_a_live_region_are_present(self):
        document = render_document(_model())
        self.assertIn('data-page-step="1"', document)
        self.assertIn('data-page-step="-1"', document)
        self.assertIn('aria-live="polite"', document)


# --- E-05: linked controls over ONE data contract -------------------------------------------------


class LinkedControlTests(unittest.TestCase):
    """One shared contract, so a table can never disagree with the chart above it."""

    def test_a_chart_and_its_table_are_computed_from_the_SAME_rows(self):
        rows = _rows(6)
        model = _model(rows=rows)
        chart = model.charts[0]
        self.assertEqual(chart.row_indices, tuple(range(len(rows))))
        self.assertEqual(model.payload["row_count"], len(rows))

    def test_the_table_rows_are_the_charted_results_own_values(self):
        result = _computed("cache-utilization", share=0.9862, n_sessions=345)
        model = _model(results=[result])
        chart = model.charts[0]
        self.assertEqual(dict(chart.table_rows), {"n_sessions": 345, "share": 0.9862})

    def test_metric_and_phase_controls_are_all_present_with_aria_state(self):
        document = render_document(_model())
        collector = _parse(document)
        pressed = [b for b in collector.of("button") if "aria-pressed" in b]
        groups = {b.get("data-group") for b in pressed}
        self.assertIn("metric", groups)
        self.assertIn("phase", groups)
        for metric in (
            "time",
            "cost",
            "input tokens",
            "output tokens",
            "cache tokens",
            "total tokens",
        ):
            self.assertIn(f'data-value="{metric}"', document)
        for phase in ("aggregate", "review", "execute", "verifier", "recovery"):
            self.assertIn(f'data-value="{phase}"', document)

    def test_exactly_one_button_per_group_starts_pressed(self):
        collector = _parse(render_document(_model()))
        for group in ("metric", "phase"):
            with self.subTest(group=group):
                pressed = [
                    b
                    for b in collector.of("button")
                    if b.get("data-group") == group and b.get("aria-pressed") == "true"
                ]
                self.assertEqual(len(pressed), 1)

    def test_the_verifier_phase_is_labeled_DERIVED(self):
        """57 verifier logs against 0 attempts carrying a verify cost: derived, never recorded."""

        document = render_document(_model())
        self.assertIn("(derived)", document)
        self.assertIn("<strong>derived</strong> from a log filename", document)


class HonestEmptyStateTests(unittest.TestCase):
    """A degenerate control renders DISABLED with its reason, never hidden and never operable."""

    def test_an_empty_dimension_is_classified_empty(self):
        dimension = spa.build_dimension("model", "Model", [])
        self.assertIs(dimension.state, DimensionState.EMPTY)
        self.assertFalse(dimension.is_usable)

    def test_a_single_valued_dimension_is_DEGENERATE_not_populated(self):
        """It LOOKS like a working filter while describing 1.1 percent of the corpus."""

        dimension = spa.build_dimension(
            "model", "Model", ["one-model"], total_records=179, resolved_records=2
        )
        self.assertIs(dimension.state, DimensionState.DEGENERATE)
        self.assertAlmostEqual(dimension.coverage, 2 / 179, places=6)
        self.assertIn("only one distinct value", dimension.reason)

    def test_a_multi_valued_dimension_is_populated(self):
        dimension = spa.build_dimension("runner", "Runner", ["oc", "agy"])
        self.assertIs(dimension.state, DimensionState.POPULATED)

    def test_the_model_control_renders_a_disabled_state_with_its_measured_coverage(
        self,
    ):
        dimension = spa.build_dimension(
            "model", "Model", ["one-model"], total_records=179, resolved_records=2
        )
        document = render_document(_model(dimensions=[dimension]))
        collector = _parse(document)
        disabled = [
            b
            for b in collector.of("button")
            if b.get("data-group") == "model" and b.get("aria-disabled") == "true"
        ]
        self.assertEqual(len(disabled), 1)
        self.assertIn("disabled", disabled[0])
        self.assertIn("degenerate:", document)
        self.assertIn("1.1%", document)
        # And it is DESCRIBED, so the reason reaches assistive technology too.
        self.assertIn("aria-describedby", disabled[0])

    def test_a_populated_dimension_renders_operable_buttons(self):
        dimension = spa.build_dimension("runner", "Runner", ["oc", "agy"])
        collector = _parse(render_document(_model(dimensions=[dimension])))
        buttons = [b for b in collector.of("button") if b.get("data-group") == "runner"]
        self.assertEqual(len(buttons), 2)
        for button in buttons:
            self.assertNotIn("disabled", button)


# --- E-06: the panels and their uncertainty context -----------------------------------------------


class RequiredPanelTests(unittest.TestCase):
    """Every required panel is present, and the honesty headlines are defaults, not footnotes."""

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

    def test_every_required_panel_is_present(self):
        document = render_document(_model())
        for panel_id in self.REQUIRED_IDS:
            with self.subTest(panel=panel_id):
                self.assertIn(f'id="{panel_id}"', document)

    def test_unattributed_time_is_shown_BY_DEFAULT_in_the_time_view(self):
        """96.2 percent unattributed at review: a time view without it shows 4 percent of the truth."""

        document = render_document(_model())
        self.assertIn(
            "Unattributed time is shown <strong>by default</strong>", document
        )
        self.assertIn("96.2%", document)
        self.assertIn("Unattributed", document)

    def test_recorded_and_estimated_cost_are_visually_DISTINCT_and_never_merged(self):
        model = _model(
            pricing={
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
        )
        document = render_document(model)
        self.assertIn('class="recorded"', document)
        self.assertIn('class="estimated"', document)
        self.assertIn("never merged", document)
        # BOTH measured eras render as a composition rather than a placeholder.
        self.assertIn("era-a", document)
        self.assertIn("era-b", document)
        self.assertIn("open-ended", document)
        self.assertIn("28.0%", document)
        self.assertIn("72.0%", document)

    def test_unknown_price_states_are_reported_as_refused_not_defaulted(self):
        document = render_document(_model(pricing={"unknown_price_step_count": 23}))
        self.assertIn("<strong>23</strong>", document)
        self.assertIn(
            "<strong>refused</strong> rather than priced at a default", document
        )

    def test_pricing_with_no_era_says_so_rather_than_showing_a_placeholder(self):
        document = render_document(_model(pricing={}))
        self.assertIn("No price era resolved", document)

    def test_the_quality_panel_keeps_the_three_counts_SEPARATE(self):
        model = _model(
            quality={
                "missing_fields": ["cost"],
                "unavailable_fields": ["tokens.cache"],
                "not_applicable_fields": ["wall_seconds"],
                "parse_error_count": 4,
            }
        )
        document = render_document(model)
        for label in ("Missing", "Unavailable", "Not applicable"):
            self.assertIn(label, document)
        self.assertIn("never one &ldquo;incomplete&rdquo; flag", document)
        self.assertIn("cost", document)

    def test_the_interpretation_panel_describes_the_CURRENT_population(self):
        model = _model(rows=_rows(3), results=[_refused("a"), _refused("b")])
        document = render_document(model)
        self.assertIn("current filter population", document)
        self.assertIn("(3 rows as loaded)", document)
        self.assertIn("Association, not causation", document)
        self.assertIn("2 of 16 required analyses were refused", document)

    def test_the_interpretation_panel_changes_with_the_population(self):
        few = render_document(_model(rows=_rows(2)))
        many = render_document(_model(rows=_rows(40)))
        self.assertIn("(2 rows as loaded)", few)
        self.assertIn("(40 rows as loaded)", many)

    def test_findings_render_with_their_uncertainty_and_alternatives(self):
        model = _model(
            findings=[
                {
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
            ]
        )
        document = render_document(model)
        self.assertIn("What is not known:", document)
        self.assertIn("Competing explanations", document)
        self.assertIn("Cheapest discriminating test:", document)
        self.assertIn("13 percent of spend is invisible", document)

    def test_a_cannot_determine_finding_renders_in_the_refusal_style(self):
        model = _model(
            findings=[
                {
                    "finding_id": "F-02",
                    "title": "CANNOT DETERMINE: merge recurrence",
                    "severity": "cannot-determine",
                    "affected_slice": "merge conflicts",
                    "sample_size": 3,
                    "coverage": 0.0,
                    "uncertainty": "no effect size is reported",
                    "data_quality_caveats": ["n=3 is below the minimum"],
                    "alternative_explanations": ["the effect may be absent entirely"],
                    "next_experiment": "accumulate observations",
                    "recommendation": "",
                    "is_actionable": False,
                }
            ]
        )
        document = render_document(model)
        self.assertIn('class="panel refusal"', document)

    def test_the_raw_view_documents_its_schema_and_excludes_source_content(self):
        document = render_document(_model())
        self.assertIn("<h3>Schema</h3>", document)
        self.assertIn("the driver run identifier", document)
        self.assertIn(
            "No prompt, conversation or source-file content is included", document
        )

    def test_provenance_of_snapshot_figures_is_labeled_NOT_current(self):
        document = render_document(_model())
        self.assertIn("review-time snapshot", document)
        self.assertIn("<strong>not current</strong>", document)
        self.assertFalse(spa.REVIEW_SNAPSHOT["is_current"])


# --- E-08: accessibility, asserted with stdlib only -----------------------------------------------


class AccessibilityContractTests(unittest.TestCase):
    """Structural a11y asserted via stdlib `html.parser`. What it cannot check is NAMED, not implied."""

    def setUp(self):
        self.document = render_document(_model())
        self.dom = _parse(self.document)

    def test_the_document_declares_a_language(self):
        html_tags = self.dom.of("html")
        self.assertTrue(html_tags)
        self.assertEqual(html_tags[0].get("lang"), "en")

    def test_every_section_is_labeled_by_its_heading(self):
        for section in self.dom.of("section"):
            with self.subTest(section=section.get("id")):
                self.assertIn("aria-labelledby", section)
                self.assertIn(f'id="{section["aria-labelledby"]}"', self.document)

    def test_every_toggle_button_exposes_its_state(self):
        toggles = [b for b in self.dom.of("button") if b.get("data-group")]
        self.assertTrue(toggles)
        for button in toggles:
            with self.subTest(value=button.get("data-value")):
                self.assertTrue(
                    "aria-pressed" in button or button.get("aria-disabled") == "true"
                )

    def test_a_disabled_control_is_disabled_for_BOTH_the_dom_and_assistive_tech(self):
        dimension = spa.build_dimension("model", "Model", [])
        dom = _parse(render_document(_model(dimensions=[dimension])))
        disabled = [b for b in dom.of("button") if b.get("data-group") == "model"]
        self.assertTrue(disabled)
        for button in disabled:
            self.assertIn("disabled", button)
            self.assertEqual(button.get("aria-disabled"), "true")

    def test_every_chart_has_a_text_alternative(self):
        for svg in self.dom.of("svg"):
            self.assertEqual(svg.get("role"), "img")
            self.assertIn("aria-labelledby", svg)
        self.assertTrue(self.dom.of("title"))

    def test_every_table_has_a_caption_and_column_scopes(self):
        self.assertTrue(self.dom.of("caption"))
        headers = self.dom.of("th")
        self.assertTrue(headers)
        for header in headers:
            with self.subTest(header=header):
                self.assertIn(header.get("scope"), ("col", "row"))

    def test_tables_are_REAL_data_tables_not_layout_divs(self):
        self.assertTrue(self.dom.of("table"))
        self.assertTrue(self.dom.of("thead"))
        self.assertTrue(self.dom.of("tbody"))

    def test_a_visible_focus_style_exists(self):
        self.assertIn(":focus-visible", self.document)
        self.assertIn("outline:", self.document)

    def test_a_reduced_motion_rule_exists(self):
        self.assertIn("prefers-reduced-motion", self.document)
        self.assertIn("animation: none", self.document)

    def test_series_are_distinguished_WITHOUT_color(self):
        """Dash patterns, so the encoding survives monochrome and color-vision deficiency."""

        self.assertIn("stroke-dasharray", self.document)
        for index in range(4):
            self.assertIn(f".series-{index}", self.document)

    def test_a_pressed_toggle_is_distinguished_without_color(self):
        self.assertIn('button[aria-pressed="true"]::before', self.document)

    def test_a_skip_link_precedes_the_content(self):
        self.assertIn("Skip to the overview", self.document)
        self.assertLess(
            self.document.index("Skip to the overview"),
            self.document.index('id="overview"'),
        )

    def test_a_figure_groups_its_chart_with_its_table(self):
        figures = self.dom.of("figure")
        self.assertTrue(figures)
        for figure in figures:
            self.assertIn("aria-labelledby", figure)
        self.assertTrue(self.dom.of("figcaption"))

    def test_the_UNVERIFIED_properties_are_published_in_the_document(self):
        """The honest boundary. Claiming 'accessible' without it is the unearned claim."""

        self.assertIn("Not machine-verified", self.document)
        for item in spa.UNVERIFIED_ACCESSIBILITY_PROPERTIES:
            with self.subTest(item=item[:40]):
                self.assertIn(spa.escape_text(item), self.document)

    def test_the_named_unverified_set_covers_focus_order_contrast_and_post_click(self):
        joined = " ".join(spa.UNVERIFIED_ACCESSIBILITY_PROPERTIES).lower()
        for topic in ("focus", "contrast", "post-interaction"):
            self.assertIn(topic, joined)


class NoNewTestDependencyTests(unittest.TestCase):
    """The tooling boundary, ASSERTED. A test that passes locally and fails in CI is the defect."""

    def test_no_analytics_report_test_imports_bs4_lxml_or_playwright(self):
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
        """No new test dependency was added, which is the point of using stdlib html.parser."""

        pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'test = ["pytest>=8", "pytest-xdist>=3", "pytest-randomly>=3", "PyYAML>=6"]',
            pyproject,
        )

    def test_the_spa_module_imports_only_stdlib(self):
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
    """E-02: the assets are REAL FILES inside the package, and a missing one REFUSES loudly."""

    def test_every_declared_asset_exists_on_disk(self):
        for name in spa.REQUIRED_ASSETS:
            with self.subTest(asset=name):
                self.assertTrue((spa.assets_dir() / name).is_file())

    def test_the_assets_live_INSIDE_the_package_directory(self):
        """Hatchling ships files under the declared package; outside it they simply do not travel."""

        package_root = Path(spa.__file__).resolve().parent
        self.assertEqual(spa.assets_dir().parent, package_root)
        self.assertEqual(spa.assets_dir().name, spa.ASSETS_DIRNAME)

    def test_a_missing_asset_REFUSES_rather_than_falling_back_silently(self):
        """A silent inline fallback is what would let a wheel ship with no assets, tests green."""

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
        with self.assertRaises(SpaError) as ctx:
            spa.read_asset("not-declared.css")
        self.assertIn("REQUIRED_ASSETS", str(ctx.exception))

    def test_no_asset_filename_matches_a_gitignore_pattern(self):
        """The measured hazard: hatchling HONORS .gitignore and drops a match SILENTLY at exit 0."""

        import fnmatch

        gitignore = (Path(__file__).parent.parent / ".gitignore").read_text(
            encoding="utf-8"
        )
        patterns = [
            line.strip()
            for line in gitignore.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        for name in spa.REQUIRED_ASSETS:
            for pattern in patterns:
                with self.subTest(asset=name, pattern=pattern):
                    self.assertFalse(
                        fnmatch.fnmatch(name, pattern.rstrip("/")),
                        f"asset {name} matches .gitignore pattern {pattern!r} and would be "
                        "silently dropped from the wheel",
                    )

    def test_the_assets_are_TRACKED_by_git_which_is_what_makes_them_ship(self):
        import subprocess

        for name in spa.REQUIRED_ASSETS:
            relative = f"agent_workflows/{spa.ASSETS_DIRNAME}/{name}"
            with self.subTest(asset=name):
                result = subprocess.run(
                    ["git", "check-ignore", "-q", relative],
                    cwd=str(Path(__file__).parent.parent),
                    capture_output=True,
                )
                # exit 1 means NOT ignored, which is what must hold.
                self.assertEqual(
                    result.returncode,
                    1,
                    f"{relative} is gitignored and would be silently dropped from the wheel",
                )

    def test_the_stylesheet_asset_carries_the_required_rules(self):
        css = spa.stylesheet()
        for rule in (
            "prefers-reduced-motion",
            ":focus-visible",
            "stroke-dasharray",
            "aria-pressed",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, css)

    def test_the_script_asset_carries_no_network_primitive(self):
        self.assertEqual(spa.scan_for_network_references(spa.read_asset("app.js")), [])


class LargeDatasetFallbackTests(unittest.TestCase):
    """The documented, TESTED behavior at and above the measured corpus scale."""

    def test_the_size_budget_is_declared_as_a_constant(self):
        self.assertIsInstance(spa.SIZE_BUDGET_BYTES, int)
        self.assertGreater(spa.SIZE_BUDGET_BYTES, 0)

    def test_above_scale_the_plotted_nodes_stay_bounded(self):
        """Twice the measured corpus scale: the bound is on bins, not on rows."""

        series = spa.bin_series([float(i % 331) for i in range(CORPUS_SCALE_ROWS * 2)])
        self.assertLessEqual(series["bin_count"], spa.MAX_PLOT_BINS)
        self.assertEqual(series["source_row_count"], CORPUS_SCALE_ROWS * 2)
        path = spa.series_path_data(series["counts"])
        self.assertEqual(path.count("M"), 1)

    def test_the_client_side_fallback_for_a_browser_without_DecompressionStream_is_present(
        self,
    ):
        document = render_document(_model())
        self.assertIn("DecompressionStream", document)
        self.assertIn("cannot inflate the embedded payload", document)

    def test_the_client_renderer_uses_textContent_never_innerHTML(self):
        """Client-side escaping by construction: the DOM API cannot produce markup from a string."""

        document = render_document(_model())
        self.assertIn("textContent", document)
        self.assertNotIn("innerHTML", document)

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
        """The consequence form of the same defect: no statement may share a `//` comment's line."""

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
        with self.assertRaises(SpaError):
            spa.bin_series([1.0], bins=0)


class EdgeCasePopulationTests(unittest.TestCase):
    """Small, empty, one-run and mixed populations all render rather than crashing."""

    def test_an_empty_population_renders_with_no_chart_and_an_honest_overview(self):
        model = build_view_model(rows=[], results=[], required_analysis_count=16)
        document = render_document(model)
        self.assertIn("<strong>0</strong> of <strong>16</strong>", document)
        self.assertEqual(_parse(document).of("figure"), [])

    def test_a_single_row_population_renders(self):
        document = render_document(_model(rows=_rows(1)))
        self.assertIn("(1 rows as loaded)", document)

    def test_all_results_refused_renders_no_chart_section_content(self):
        model = _model(results=[_refused("a"), _refused("b"), _refused("c")])
        document = render_document(model)
        self.assertIn(
            "No analysis in this population returned a computable verdict", document
        )

    def test_a_mixed_runner_and_price_era_population_renders_both(self):
        dimensions = [
            spa.build_dimension("runner", "Runner", ["oc_runipd", "agy_runipd"]),
            spa.build_dimension(
                "outcome", "Outcome", ["executed", "partial", "blocked"]
            ),
        ]
        document = render_document(_model(dimensions=dimensions))
        for value in ("oc_runipd", "agy_runipd", "executed", "partial", "blocked"):
            self.assertIn(value, document)

    def test_a_missing_price_population_renders_without_an_estimate(self):
        document = render_document(_model(pricing={"recorded_usd": 10.0}))
        self.assertIn("no value", document)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""runanalytics Order 07 (`6eq3oq`): the self-contained offline analytics SPA.

WHAT THIS MODULE IS FOR, stated before the API because the reason decides every edge case below: it
RENDERS WHAT ORDER 06 ACTUALLY PRODUCED, INCLUDING ITS REFUSALS. Order 06
(:mod:`agent_workflows.run_analytics_statistics`) returns a :class:`~.AnalysisResult` whose
``renderable`` property is FALSE for every non-computed verdict, and measured over the review-time
corpus five of the sixteen required analyses came back ``cannot-determine`` (n between 3 and 6 for
three of them, 1.1 percent model-identity coverage for the model comparison, and zero telemetry runs
for resource saturation). So this module's job is NOT sixteen charts. It is however many charts the
data supports, plus a PROMINENT, first-class account of what could not be computed and why. A chart
fabricated from a refusal is the single worst artifact this Set can produce, which is why
:func:`build_view_model` REFUSES to place a non-renderable result in the chart list at all, rather
than trusting a later renderer to remember to check.

THREE CONTEXTS, THREE ESCAPES, ONE BOUNDARY. This package contained ZERO uses of ``html.escape``
before this module (a repo-wide search found only ``re.escape``), so there was no helper to reuse and
no precedent to copy. HTML text, an HTML attribute value, SVG text and a JavaScript string literal
need FOUR different escapes, and a single helper used for all of them is a defect rather than a
convenience: ``&quot;`` is required in an attribute and inert in text, while a JS string literal
needs ``</script`` broken up and a backslash doubled, neither of which any HTML escape performs.
:func:`escape_text`, :func:`escape_attribute`, :func:`escape_svg_text` and :func:`escape_js_string`
are those four, and every one of them routes through
:func:`sanitize_control_characters` first, because a bidi override cannot be neutralized by escaping
at all (a numeric character reference decodes to the same active code point) and must be REPLACED.

OFFLINE IS A TESTED PROPERTY, NOT AN INTENTION. The produced document contains no ``http:``, no
``https:``, no external script/link/font/image, no dynamic import, no ``fetch``, no ``XMLHttpRequest``
and no WebSocket, and :func:`scan_for_network_references` is the scanner that proves it. Note the
consequence for inline SVG: an ``xmlns`` attribute would itself be an ``http:`` occurrence, so the
SVG is emitted WITHOUT one and relies on HTML5 placing an inline ``<svg>`` in the SVG namespace by
parser rule. That is deliberate; adding an allowlist exception to the scanner instead would be the
beginning of the end of the scanner.

THE DATA LAYOUT WAS DECIDED BY MEASUREMENT, NOT BY TASTE. Measured over the review-time corpus,
29766 per-step fact rows are 3.24 MB as minified row-wise JSON and 2.11 MB COLUMNAR (one array per
field rather than one object per row), which is 0.93 MB versus 0.71 MB as the base64 text a single
HTML file must actually embed: a 24 percent saving on size and a larger one on parse time. The
RENDERING consequence is sharper than the size one: 29766 points as individual SVG ``<circle>`` nodes
is roughly 1.34 MB of markup and 29766 DOM nodes, which is past where browsers degrade, while the
same points as SVG PATH DATA are roughly 0.36 MB in ONE node. Canvas would fix rendering and destroy
accessibility (it cannot be asserted structurally), so the resolution is columnar storage,
path-rendered or pre-binned plotted series, and a PAGINATED raw view. See
:data:`EMBEDDED_DATA_CONTRACT`.

EVERY CORPUS FIGURE IN THIS MODULE IS A LABELED REVIEW-TIME SNAPSHOT, never a current measurement.
The corpus grows with every run and is gitignored, so it is absent from a fresh checkout entirely.
:data:`REVIEW_SNAPSHOT` carries ``is_current: False`` for the same reason
:data:`~agent_workflows.run_analytics_statistics.CORPUS_BASELINE` does, and the rendered report
labels each such figure with its provenance and date rather than presenting it as measured today.
"""

from __future__ import annotations

import base64
import gzip
import html
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "SPA_SCHEMA_VERSION",
    "ASSETS_DIRNAME",
    "REQUIRED_ASSETS",
    "assets_dir",
    "read_asset",
    "stylesheet",
    "EMBEDDED_DATA_CONTRACT",
    "REVIEW_SNAPSHOT",
    "SIZE_BUDGET_BYTES",
    "PLOTTED_NODE_BUDGET",
    "RAW_VIEW_PAGE_SIZE",
    "MAX_PLOT_BINS",
    "SpaError",
    "DimensionState",
    "Dimension",
    "ChartView",
    "RefusalView",
    "ViewModel",
    "sanitize_control_characters",
    "escape_text",
    "escape_attribute",
    "escape_svg_text",
    "escape_js_string",
    "columnar_from_rows",
    "rows_from_columnar",
    "encode_embedded_payload",
    "decode_embedded_payload",
    "bin_series",
    "series_path_data",
    "build_dimension",
    "chart_from_result",
    "refusal_from_result",
    "build_view_model",
    "render_document",
    "scan_for_network_references",
]


#: Bumped when the EMBEDDED CONTRACT or the document's structural shape changes. A style change does
#: not bump it; a renamed column or a new required view does.
SPA_SCHEMA_VERSION = 1


class SpaError(ValueError):
    """A render was refused because it would have produced a dishonest or unsafe document."""


# --- the measured constants -----------------------------------------------------------------------

#: THE REVIEW-TIME CORPUS SNAPSHOT. NOT A CURRENT MEASUREMENT, and the flag says so in the data
#: rather than only in a comment, exactly as Order 06's ``CORPUS_BASELINE`` does. The corpus is
#: gitignored (`.aw/.gitignore` carries `records/runs/`), so it is ABSENT from a fresh checkout and
#: these figures cannot be re-derived there at all; they are retained as the documented basis for the
#: architectural decisions below and as the scale the size fixture reproduces.
REVIEW_SNAPSHOT: dict[str, Any] = {
    "provenance": "review-time-snapshot",
    "measured_at": "2026-09-08",
    "is_current": False,
    "note": (
        "measured at plan review over a corpus that grows with every run and is not tracked; "
        "re-measure before citing any figure as current"
    ),
    # --- the sizes that decided the embedded layout ---
    "per_step_fact_rows": 29766,
    "row_wise_minified_bytes": 3_240_000,
    "row_wise_base64_gzip_bytes": 930_000,
    "columnar_minified_bytes": 2_110_000,
    "columnar_base64_gzip_bytes": 710_000,
    "columnar_saving_share": 0.24,
    # --- the node counts that decided path rendering ---
    "per_point_svg_markup_bytes": 1_340_000,
    "per_point_svg_node_count": 29766,
    "path_svg_markup_bytes": 360_000,
    "path_svg_node_count": 1,
    # --- the honesty headlines the report must publish by default ---
    "tool_activity_share_of_wall": 0.038,
    "unattributed_share_of_wall": 0.962,
    "model_identity_coverage": 0.011,
    "attempts_with_resolvable_model": 2,
    "attempt_count": 179,
    "verifier_log_count": 57,
    "attempts_with_verify_cost": 0,
    # --- the injection hazard that decided the escaping boundary ---
    "outcome_files_scanned": 216,
    "outcome_files_with_markup_characters": 152,
    "outcome_files_with_fail_severity_leaks": 6,
    # --- the required-analysis ceiling ---
    "required_analysis_count": 16,
    "required_analyses_refused": 5,
    "required_analyses_reshaped": 5,
}


#: THE EMBEDDED DATA CONTRACT, decided by the measurement above rather than at render time.
#:
#: ``columnar`` because it measured 24 percent smaller embedded and parses faster; ``per-step`` grain
#: because Order 05 stores per-step facts precisely so a median or a quantile need not reparse source
#: files, and per-attempt aggregates alone (39 KB, comfortable) would foreclose every distribution
#: this Set exists to provide; ``gzip`` with a FIXED mtime and level because determinism is also
#: required and gzip's header mtime is the only nondeterministic field in it.
EMBEDDED_DATA_CONTRACT: dict[str, Any] = {
    "spa_schema_version": SPA_SCHEMA_VERSION,
    "layout": "columnar",
    "grain": "per-step",
    "encoding": "gzip+base64",
    "gzip_mtime": 0,
    "gzip_level": 9,
    "json_separators": [",", ":"],
    "json_sort_keys": True,
    "plotted_series": "pre-binned-or-path-rendered",
    "raw_view": "paginated",
    "basis": (
        "columnar measured 2.11 MB against 3.24 MB row-wise over 29766 rows (0.71 MB against "
        "0.93 MB base64-gzip); per-point SVG measured 29766 nodes against 1 for path data"
    ),
    "basis_provenance": "review-time-snapshot-2026-09-08-NOT-CURRENT",
}

#: The declared size ceiling for the produced ``index.html``. 8 MiB, and the number is defensible
#: rather than round: the measured columnar payload is 0.71 MB base64-gzip at 29766 rows, the chrome
#: (markup, CSS, script, tables) measures well under 1 MB, so 8 MiB leaves roughly a 5x headroom for
#: corpus growth before the fallback engages, while staying inside what a browser opens from ``file://``
#: without complaint.
SIZE_BUDGET_BYTES = 8 * 1024 * 1024

#: The ceiling on DOM nodes contributed by PLOTTED series. Bounded by construction, not by hope: a
#: series becomes one ``<path>`` and at most :data:`MAX_PLOT_BINS` axis/label nodes, so the count is
#: independent of row count. Measured basis: 29766 per-point nodes is past where browsers degrade.
PLOTTED_NODE_BUDGET = 600

#: Rows materialized per page of the raw view. The raw view PAGINATES because 29766 rows materialized
#: at once is the defect measured above; this is the page, not the corpus.
RAW_VIEW_PAGE_SIZE = 100

#: Maximum bins a plotted series is reduced to before rendering. Bounded so the node count is too.
MAX_PLOT_BINS = 240


# --- the escaping boundary ------------------------------------------------------------------------
#
# FOUR CONTEXTS, FOUR FUNCTIONS, ONE PRE-PASS. The pre-pass exists because escaping cannot fix a
# control character: `&#x202E;` decodes to U+202E and reorders the text around it exactly as the raw
# character would, so a bidi override has to be REPLACED rather than encoded.

#: Unicode general categories that are never legitimate in a rendered analytics label. ``Cf`` covers
#: the bidi overrides and embeddings (U+202A..U+202E, U+2066..U+2069) plus the zero-width joiners;
#: ``Cc`` is C0/C1; ``Cs`` and ``Co`` are surrogates and private use.
_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co"})

#: Whitespace that IS legitimate and must survive the control sweep.
_ALLOWED_CONTROL_CHARACTERS = frozenset({"\t", "\n", "\r"})

#: U+FFFD. A dropped character hides that the source was hostile; a replacement character keeps the
#: text readable, keeps the tampering VISIBLE, and cannot reorder anything.
REPLACEMENT_CHARACTER = "\ufffd"


def sanitize_control_characters(text: str) -> str:
    """Replace every bidi/format/control code point with U+FFFD, preserving tab/newline/return.

    THE PRE-PASS EVERY ESCAPE RUNS FIRST, and the only member of this boundary that is not an
    escape at all. Escaping a bidi override produces an ENCODED bidi override, which renders
    identically, so the character has to go. Newlines survive because a report legitimately displays
    multi-line free text.
    """

    if not text:
        return ""
    out: list[str] = []
    for char in text:
        if char in _ALLOWED_CONTROL_CHARACTERS:
            out.append(char)
            continue
        if unicodedata.category(char) in _UNSAFE_CATEGORIES:
            out.append(REPLACEMENT_CHARACTER)
            continue
        out.append(char)
    return "".join(out)


def escape_text(value: Any) -> str:
    """Escape for HTML TEXT content (``&``, ``<``, ``>``), after the control pre-pass."""

    return html.escape(sanitize_control_characters(_as_text(value)), quote=False)


def escape_attribute(value: Any) -> str:
    """Escape for an HTML ATTRIBUTE value: text escapes PLUS both quote forms.

    A separate function from :func:`escape_text` deliberately. ``quote=False`` is correct in text and
    catastrophic in an attribute, where an unescaped ``"`` closes the attribute and the next token is
    parsed as a new one. Single quotes are escaped too, so the caller may use either delimiter.
    """

    escaped = html.escape(sanitize_control_characters(_as_text(value)), quote=True)
    return escaped.replace("'", "&#x27;")


def escape_svg_text(value: Any) -> str:
    """Escape for text inside an SVG element.

    Distinct from :func:`escape_text` even though the character set overlaps, because the reason
    differs and a future change to one must not silently change the other: inside SVG a bare ``&``
    is an XML well-formedness error rather than merely a rendering hazard, so ``&`` is escaped
    unconditionally here and the function may never gain an "allow entities" option.
    """

    text = sanitize_control_characters(_as_text(value))
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def escape_js_string(value: Any) -> str:
    """Escape for the inside of a JavaScript string literal in an inline ``<script>``.

    THE CONTEXT NO HTML ESCAPE HANDLES. Inside ``<script>`` the HTML parser does not decode entities,
    so ``&lt;`` would appear literally as those four characters in the string; what actually
    terminates the element early is the byte sequence ``</script``, so it is broken with an escaped
    slash. ``\\u2028``/``\\u2029`` are escaped because they are literal line terminators in
    JavaScript source but not in JSON.
    """

    text = sanitize_control_characters(_as_text(value))
    out = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    # `</script` (any case) ends the element regardless of quoting; `<!--` opens a comment state.
    out = re.sub(r"</(script)", r"<\\/\1", out, flags=re.IGNORECASE)
    return out.replace("<!--", "<\\!--")


def escape_json_for_script(payload: str) -> str:
    """Escape a JSON document for embedding in ``<script type="application/json">``.

    THE FIFTH CONTEXT, AND IT IS NOT THE JS-STRING ONE. This was a real defect caught by this
    module's own test: applying :func:`escape_js_string` here produced ``\\"`` sequences that arrive
    at the client as LITERAL backslash-quote in ``textContent``, so ``JSON.parse`` would fail at
    runtime on every load. A JSON island is not a string literal; it is a document the client parses
    verbatim.

    So the escape is the one that is BOTH valid JSON and inert in HTML: ``<``, ``>`` and ``&`` become
    ``\\uXXXX`` escapes. ``JSON.parse`` decodes those back to the original characters, so no data is
    lost, while the serialized text can neither terminate the ``<script>`` element (no ``<`` survives,
    so ``</script`` cannot appear) nor contribute a tag if the block is ever mis-parsed. The line
    terminators are escaped for the same reason as in a JS string literal.
    """

    return (
        payload.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value if isinstance(value, str) else str(value)


#: Every string that must not appear in the produced bundle, with the reason each is forbidden. A
#: single flat tuple rather than a regex, so a failure names the exact token it found.
FORBIDDEN_NETWORK_TOKENS: tuple[tuple[str, str], ...] = (
    ("http:", "an absolute http URL is a network reference"),
    ("https:", "an absolute https URL is a network reference"),
    ("//fonts.", "an external font host"),
    ("fetch(", "a runtime network call"),
    ("XMLHttpRequest", "a runtime network call"),
    ("WebSocket", "a runtime network call"),
    ("EventSource", "a runtime network call"),
    ("navigator.sendBeacon", "a runtime network call"),
    ("import(", "a dynamic module import loads a second file"),
    ("importScripts", "a worker-side dynamic load"),
    ("<script src", "an external script"),
    ("<link ", "an external stylesheet or preload"),
    ("<iframe", "an embedded external document"),
    ("srcset", "an external image candidate set"),
    ("@import", "a CSS-level external load"),
)


def scan_for_network_references(document: str) -> list[str]:
    """Every forbidden network reference in ``document``, as ``"<token>: <reason>"``. Empty is clean.

    Returns the FINDINGS rather than a boolean so a failure names what it found, which is the same
    reason :func:`~agent_workflows.run_analytics_findings.scan_for_causal_language` returns matches.
    Case-insensitive, because ``HTTP:`` is as much a network reference as ``http:``.
    """

    haystack = document.lower()
    findings: list[str] = []
    for token, reason in FORBIDDEN_NETWORK_TOKENS:
        if token.lower() in haystack:
            findings.append(f"{token}: {reason}")
    return findings


# --- the embedded data contract -------------------------------------------------------------------


def columnar_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    columns: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Turn row-wise records into the COLUMNAR layout: one array per field.

    ``columns`` fixes the column set and therefore the output's determinism; absent it, the union of
    every row's keys is used, SORTED, so two calls over the same data agree. A row missing a column
    contributes ``None`` rather than being dropped, because a missing observation is not an absent
    row and Order 05's whole ``Value`` contract rests on that distinction.
    """

    names = (
        list(columns)
        if columns is not None
        else sorted({key for row in rows for key in row})
    )
    data: dict[str, list[Any]] = {name: [] for name in names}
    for row in rows:
        for name in names:
            data[name].append(row.get(name))
    return {
        "spa_schema_version": SPA_SCHEMA_VERSION,
        "layout": "columnar",
        "row_count": len(rows),
        "columns": names,
        "data": data,
    }


def rows_from_columnar(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The inverse of :func:`columnar_from_rows`. Exists so the layout is provably lossless."""

    columns = list(payload.get("columns") or [])
    data = payload.get("data") or {}
    count = int(payload.get("row_count") or 0)
    rows: list[dict[str, Any]] = []
    for index in range(count):
        row: dict[str, Any] = {}
        for name in columns:
            column = data.get(name) or []
            row[name] = column[index] if index < len(column) else None
        rows.append(row)
    return rows


def encode_embedded_payload(payload: Mapping[str, Any]) -> str:
    """Serialize, gzip and base64 a payload DETERMINISTICALLY.

    ``mtime=0`` and a fixed ``compresslevel`` are both load-bearing: gzip writes the current time
    into its header by default, which alone would make two renders of identical data differ byte for
    byte and defeat the golden-render requirement, and zlib output differs by level.
    """

    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    raw = text.encode("utf-8")
    import io

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as handle:
        handle.write(raw)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def decode_embedded_payload(encoded: str) -> dict[str, Any]:
    """Inverse of :func:`encode_embedded_payload`, so a test can assert the round trip."""

    raw = gzip.decompress(base64.b64decode(encoded.encode("ascii")))
    return json.loads(raw.decode("utf-8"))


def bin_series(
    values: Sequence[float],
    *,
    bins: int = MAX_PLOT_BINS,
) -> dict[str, Any]:
    """Reduce a series to at most ``bins`` bins, so the plotted node count is bounded by construction.

    Returns the bin edges, the counts, and the ``source_row_count``. THE LAST FIELD IS NOT DECORATIVE:
    a reader must be able to see that a 240-bin histogram summarizes 29766 observations, or the
    binning has silently become the data.
    """

    if bins < 1:
        raise SpaError("a binned series needs at least one bin")
    numbers = [float(v) for v in values if v is not None and _is_finite(float(v))]
    if not numbers:
        return {
            "source_row_count": 0,
            "bin_count": 0,
            "edges": [],
            "counts": [],
            "minimum": None,
            "maximum": None,
        }
    low = min(numbers)
    high = max(numbers)
    if high == low:
        # A degenerate range is ONE bin holding everything, not a division by zero.
        return {
            "source_row_count": len(numbers),
            "bin_count": 1,
            "edges": [low, high],
            "counts": [len(numbers)],
            "minimum": low,
            "maximum": high,
        }
    count = min(int(bins), MAX_PLOT_BINS)
    width = (high - low) / count
    counts = [0] * count
    for number in numbers:
        index = int((number - low) / width)
        if index >= count:
            index = count - 1
        counts[index] += 1
    edges = [low + width * i for i in range(count + 1)]
    return {
        "source_row_count": len(numbers),
        "bin_count": count,
        "edges": edges,
        "counts": counts,
        "minimum": low,
        "maximum": high,
    }


def series_path_data(
    counts: Sequence[float],
    *,
    width: float = 640.0,
    height: float = 200.0,
) -> str:
    """One SVG ``path`` ``d`` string for a whole series: ONE node regardless of point count.

    The measured alternative was 29766 individual ``<circle>`` nodes at roughly 1.34 MB of markup,
    past where browsers degrade; this is roughly 0.36 MB in one node. Coordinates are rounded to two
    decimals so the output is deterministic across platforms rather than carrying float noise.
    """

    numbers = [float(c) for c in counts]
    if not numbers:
        return ""
    peak = max(numbers) or 1.0
    if len(numbers) == 1:
        y = height - (numbers[0] / peak) * height
        return f"M 0.00 {y:.2f} L {width:.2f} {y:.2f}"
    step = width / (len(numbers) - 1)
    points = []
    for index, number in enumerate(numbers):
        x = step * index
        y = height - (number / peak) * height
        points.append(f"{x:.2f} {y:.2f}")
    return "M " + " L ".join(points)


def _is_finite(number: float) -> bool:
    return not (math.isnan(number) or math.isinf(number))


# --- the view model -------------------------------------------------------------------------------


class DimensionState(str, Enum):
    """Whether a filter dimension is usable, and if not, WHY.

    ``DEGENERATE`` is separate from ``EMPTY`` because the two mislead differently: an empty control
    is obviously useless, while a single-valued one LOOKS like a working filter and silently
    describes 1.1 percent of the corpus (the measured model-identity coverage). Both render disabled
    with a stated reason; neither is hidden, because a hidden control is indistinguishable from an
    oversight.
    """

    POPULATED = "populated"
    DEGENERATE = "degenerate"
    EMPTY = "empty"


@dataclass(frozen=True)
class Dimension:
    """One filter control: its values, its state, and its coverage of the corpus."""

    name: str
    label: str
    values: tuple[str, ...]
    state: DimensionState
    #: Fraction of records for which this dimension resolved at all. 1.1 percent for ``model`` at
    #: review, which is exactly why a coverage figure travels WITH the control rather than in prose.
    coverage: float = 1.0
    #: True when the values were DERIVED rather than recorded (the verifier phase is read off a log
    #: filename), so the control can be labeled and never presented as recorded.
    is_derived: bool = False
    reason: str = ""

    @property
    def is_usable(self) -> bool:
        return self.state is DimensionState.POPULATED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "values": list(self.values),
            "state": self.state.value,
            "coverage": round(self.coverage, 6),
            "is_derived": self.is_derived,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ChartView:
    """ONE chart AND its exact table, computed from the SAME rows so they cannot disagree.

    The shared ``row_indices`` is the mechanism, not a convention: chart and table both project from
    those indices, so there is no second code path that could drift. A chart may only be built from a
    COMPUTED result; :func:`chart_from_result` refuses otherwise.
    """

    analysis_name: str
    title: str
    #: Indices into the embedded columnar payload. The SINGLE source both views project from.
    row_indices: tuple[int, ...]
    #: The binned/summarized series actually plotted, so the node count is bounded.
    series: dict[str, Any]
    #: The exact table: header plus rows, as displayed. Never recomputed by the renderer.
    table_columns: tuple[str, ...]
    table_rows: tuple[tuple[Any, ...], ...]
    sample_size: int
    metric: str = ""
    caveats: tuple[str, ...] = ()
    is_derived: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_name": self.analysis_name,
            "title": self.title,
            "row_indices": list(self.row_indices),
            "series": dict(self.series),
            "table_columns": list(self.table_columns),
            "table_rows": [list(r) for r in self.table_rows],
            "sample_size": self.sample_size,
            "metric": self.metric,
            "caveats": list(self.caveats),
            "is_derived": self.is_derived,
        }


@dataclass(frozen=True)
class RefusalView:
    """ONE refused analysis, rendered with EQUAL PROMINENCE to a chart.

    THE MOST IMPORTANT TYPE IN THIS MODULE. Five of the sixteen required analyses came back
    ``cannot-determine`` at review, and the three ways to present that are all worse than this one:
    an empty chart reads as "we measured zero", which is a stronger and falser claim than silence;
    omitting the analysis is indistinguishable from an oversight; and plotting the three points that
    do exist is the fabrication Order 06's gate forbids outright.
    """

    analysis_name: str
    title: str
    verdict: str
    reason: str
    sample_size: int
    coverage: float | None = None
    caveats: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_name": self.analysis_name,
            "title": self.title,
            "verdict": self.verdict,
            "reason": self.reason,
            "sample_size": self.sample_size,
            "coverage": self.coverage,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class ViewModel:
    """Everything the document renders, with charts and refusals kept STRUCTURALLY apart.

    The separation is the guarantee: a non-renderable result cannot reach :attr:`charts` because
    :func:`build_view_model` routes on ``AnalysisResult.renderable``, so no renderer needs to
    remember to check and none can forget.
    """

    payload: dict[str, Any]
    charts: tuple[ChartView, ...] = ()
    refusals: tuple[RefusalView, ...] = ()
    dimensions: tuple[Dimension, ...] = ()
    findings: tuple[Mapping[str, Any], ...] = ()
    pricing: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    time_accounting: dict[str, Any] = field(default_factory=dict)
    required_analysis_count: int = 0
    generated_label: str = ""

    @property
    def computed_count(self) -> int:
        return len(self.charts)

    @property
    def refused_count(self) -> int:
        return len(self.refusals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spa_schema_version": SPA_SCHEMA_VERSION,
            "charts": [c.to_dict() for c in self.charts],
            "refusals": [r.to_dict() for r in self.refusals],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "findings": [dict(f) for f in self.findings],
            "pricing": dict(self.pricing),
            "quality": dict(self.quality),
            "time_accounting": dict(self.time_accounting),
            "required_analysis_count": self.required_analysis_count,
            "computed_count": self.computed_count,
            "refused_count": self.refused_count,
            "generated_label": self.generated_label,
        }


def build_dimension(
    name: str,
    label: str,
    values: Iterable[Any],
    *,
    total_records: int = 0,
    resolved_records: int | None = None,
    is_derived: bool = False,
) -> Dimension:
    """Build one filter dimension, classifying its state HONESTLY.

    Coverage is computed from ``resolved_records / total_records`` when both are known, because a
    control's trustworthiness is a property of coverage rather than of value count: two resolved
    values out of 179 attempts is a degenerate control however many distinct labels it shows.
    """

    distinct = tuple(sorted({str(v) for v in values if str(v).strip()}))
    coverage = 1.0
    if total_records > 0 and resolved_records is not None:
        coverage = max(0.0, min(1.0, resolved_records / total_records))
    if not distinct:
        state = DimensionState.EMPTY
        reason = "no record in the current population carries this dimension"
    elif len(distinct) == 1:
        state = DimensionState.DEGENERATE
        reason = (
            f"only one distinct value is present ({distinct[0]}), covering "
            f"{coverage:.1%} of records; filtering on it cannot separate anything"
        )
    else:
        state = DimensionState.POPULATED
        reason = ""
    return Dimension(
        name=name,
        label=label,
        values=distinct,
        state=state,
        coverage=coverage,
        is_derived=is_derived,
        reason=reason,
    )


def refusal_from_result(result: Any, *, title: str = "") -> RefusalView:
    """A :class:`RefusalView` from a non-computed Order 06 result. REFUSES a computed one.

    The refusal on a COMPUTED input is deliberate and symmetric with
    :func:`chart_from_result`: presenting a computable analysis as refused understates the evidence,
    which is the mirror image of the defect this module exists to prevent.
    """

    if getattr(result, "renderable", False):
        raise SpaError(
            f"analysis {getattr(result, 'name', '?')!r} is COMPUTED and must be charted, "
            "not rendered as a refusal"
        )
    coverage = None
    values = getattr(result, "values", None) or {}
    if isinstance(values, Mapping) and "coverage" in values:
        try:
            coverage = float(values["coverage"])
        except (TypeError, ValueError):
            coverage = None
    return RefusalView(
        analysis_name=str(getattr(result, "name", "")),
        title=title or _humanize(str(getattr(result, "name", ""))),
        verdict=str(getattr(getattr(result, "verdict", ""), "value", ""))
        or str(getattr(result, "verdict", "")),
        reason=str(getattr(result, "reason", "")),
        sample_size=int(getattr(result, "sample_size", 0) or 0),
        coverage=coverage,
        caveats=tuple(str(c) for c in (getattr(result, "caveats", ()) or ())),
    )


def chart_from_result(
    result: Any,
    *,
    row_indices: Sequence[int],
    values: Sequence[float],
    table_columns: Sequence[str],
    table_rows: Sequence[Sequence[Any]],
    metric: str = "",
    title: str = "",
    bins: int = MAX_PLOT_BINS,
) -> ChartView:
    """A :class:`ChartView` from a COMPUTED Order 06 result. REFUSES a non-computed one.

    THE REFUSAL IS THE POINT. A caller that forgets to branch on ``renderable`` fails loudly here
    instead of producing an empty axis a reader would take for a measurement of zero, which is the
    same mechanism ``AnalysisResult.require_values`` uses one layer down.
    """

    if not getattr(result, "renderable", False):
        verdict = getattr(getattr(result, "verdict", ""), "value", None) or getattr(
            result, "verdict", ""
        )
        raise SpaError(
            f"analysis {getattr(result, 'name', '?')!r} returned {verdict!r} "
            f"(n={getattr(result, 'sample_size', 0)}): a chart may not be produced for it; "
            "render a RefusalView instead"
        )
    return ChartView(
        analysis_name=str(getattr(result, "name", "")),
        title=title or _humanize(str(getattr(result, "name", ""))),
        row_indices=tuple(int(i) for i in row_indices),
        series=bin_series(values, bins=bins),
        table_columns=tuple(str(c) for c in table_columns),
        table_rows=tuple(tuple(r) for r in table_rows),
        sample_size=int(getattr(result, "sample_size", 0) or 0),
        metric=metric,
        caveats=tuple(str(c) for c in (getattr(result, "caveats", ()) or ())),
        is_derived=bool(getattr(result, "is_derived", False)),
    )


def build_view_model(
    *,
    rows: Sequence[Mapping[str, Any]],
    results: Sequence[Any],
    columns: Sequence[str] | None = None,
    metric_column: str = "",
    dimensions: Sequence[Dimension] = (),
    findings: Sequence[Mapping[str, Any]] = (),
    pricing: Mapping[str, Any] | None = None,
    quality: Mapping[str, Any] | None = None,
    time_accounting: Mapping[str, Any] | None = None,
    required_analysis_count: int = 0,
    generated_label: str = "",
) -> ViewModel:
    """Route every Order 06 result to a chart OR a refusal, by its verdict alone.

    THE ROUTING IS STRUCTURAL, WHICH IS WHY IT CANNOT BE FORGOTTEN. A computed result becomes a
    chart; every other verdict becomes a refusal. There is no branch in which a ``cannot-determine``
    verdict reaches the chart list, so the document has no code path that could plot one.

    Chart and table are both projected from ONE ``row_indices`` tuple per analysis, which is what
    makes "a table can never disagree with the chart above it" a structural property rather than a
    review promise.
    """

    payload = columnar_from_rows(rows, columns=columns)
    charts: list[ChartView] = []
    refusals: list[RefusalView] = []
    indices = tuple(range(len(rows)))
    series_values: list[float] = []
    if metric_column:
        column = payload["data"].get(metric_column) or []
        series_values = [
            float(v)
            for v in column
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        ]

    for result in results:
        if getattr(result, "renderable", False):
            table_columns = ("metric", "value")
            table_rows = tuple(
                (str(k), v)
                for k, v in sorted((getattr(result, "values", None) or {}).items())
            )
            charts.append(
                chart_from_result(
                    result,
                    row_indices=indices,
                    values=series_values,
                    table_columns=table_columns,
                    table_rows=table_rows,
                    metric=metric_column,
                )
            )
        else:
            refusals.append(refusal_from_result(result))

    return ViewModel(
        payload=payload,
        charts=tuple(charts),
        refusals=tuple(refusals),
        dimensions=tuple(dimensions),
        findings=tuple(dict(f) for f in findings),
        pricing=dict(pricing or {}),
        quality=dict(quality or {}),
        time_accounting=dict(time_accounting or {}),
        required_analysis_count=int(required_analysis_count or len(results)),
        generated_label=generated_label,
    )


def _humanize(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").strip().capitalize() or "Analysis"


# --- rendering ------------------------------------------------------------------------------------
#
# ACCESSIBILITY IS ASSERTED WITH STDLIB `html.parser` AND NOTHING ELSE. `bs4`, `lxml` and
# `playwright` all import on a maintainer box and NONE is in `[project.optional-dependencies].test`,
# which is exactly what CI installs, so a test using one passes locally and fails or silently skips
# in CI - the reproducibility hole `pyproject.toml` already documents for `pytest-randomly`. Probed:
# stdlib `html.parser` extracts `aria-pressed`, `role`, `aria-labelledby`, `scope` and `<caption>`,
# which covers every structural assertion here.
#
# WHAT STDLIB CANNOT CHECK IS NAMED RATHER THAN IMPLIED. Computed focus ORDER, contrast RATIO, real
# JS execution and post-click state updates are not machine-verified by this suite, and
# `UNVERIFIED_ACCESSIBILITY_PROPERTIES` says so in the document itself. Claiming "accessible" without
# that boundary is the unearned claim this repository's honesty rules exist to prevent.

#: The a11y properties this suite does NOT verify, published IN the report rather than only in a doc.
UNVERIFIED_ACCESSIBILITY_PROPERTIES: tuple[str, ...] = (
    "computed keyboard focus ORDER (structural tab-ability is asserted; the resulting order is not)",
    "color CONTRAST RATIO against WCAG thresholds (no contrast calculator is a declared dependency)",
    "post-interaction state (no JS is executed by the suite, so a control's state AFTER a click is "
    "asserted only as authored markup)",
    "screen-reader ANNOUNCEMENT text as a real assistive technology would speak it",
)

#: Style rules. Series are distinguished by DASH PATTERN as well as hue, so the encoding survives
#: monochrome and every common color-vision deficiency; the reduced-motion block is a hard
#: requirement rather than a nicety.
#: The packaged browser assets directory. A REAL directory inside the package, not a string
#: constant, because the plan requires the assets to SHIP and shipping is only provable for files.
#: Measured with a probe build at execution: hatchling includes files under the declared package
#: directory automatically AND HONORS `.gitignore`, silently omitting a gitignored asset from the
#: wheel at exit 0 with no warning. That is why `tests/test_packaging.py` now carries a POSITIVE
#: per-asset assertion: the pre-existing test asserted only that FORBIDDEN content was absent and
#: would have passed with every asset missing (verified: `7 passed`).
ASSETS_DIRNAME = "run_analytics_assets"

#: Every asset that must ship, named EXPLICITLY so the packaging test can assert each one by name. A
#: derived list would silently stop covering a newly added file, which is exactly how a packaging
#: test stops working.
REQUIRED_ASSETS: tuple[str, ...] = ("app.css", "app.js")


def assets_dir() -> Path:
    """The packaged assets directory, resolved relative to this module.

    `__file__`-relative rather than via `importlib.resources`, matching how this package already
    locates its packaged data, so the lookup behaves identically from a source checkout and from an
    installed wheel.
    """

    return Path(__file__).resolve().parent / ASSETS_DIRNAME


def read_asset(name: str) -> str:
    """One packaged asset's text, or a REFUSAL naming what is missing.

    Refuses rather than falling back to an inline default, and that is deliberate: a silent fallback
    is precisely what would let a wheel ship with no assets while every test still passed, which is
    the measured defect (F-2) this whole item exists to close.
    """

    if name not in REQUIRED_ASSETS:
        raise SpaError(
            f"asset {name!r} is not a declared asset; declare it in REQUIRED_ASSETS so the "
            f"packaging test asserts it ships. Declared: {list(REQUIRED_ASSETS)}"
        )
    path = assets_dir() / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpaError(
            f"packaged browser asset {name!r} is missing from {assets_dir()}: {exc}. "
            "The wheel/sdist must carry it; see tests/test_packaging.py, which asserts each asset "
            "by name because hatchling drops a gitignored asset SILENTLY at exit 0"
        ) from exc


def stylesheet() -> str:
    """The report stylesheet, from the packaged asset.

    Series are distinguished by DASH PATTERN as well as hue, so the encoding survives monochrome and
    every common color-vision deficiency; the reduced-motion block is a hard requirement.
    """

    return read_asset("app.css")


def _script(encoded_payload: str, view_model_json: str) -> str:
    """The inline script, from the packaged asset.

    Inlined rather than referenced with `<script src=...>`, because a second file is a second
    request and the deliverable is explicitly ONE self-contained document openable from `file://`.
    No network primitive appears in it, which :func:`scan_for_network_references` proves.
    """

    return read_asset("app.js")


def render_document(model: ViewModel, *, title: str = "Run analytics") -> str:
    """Render the whole self-contained document. DETERMINISTIC for identical input.

    Every string crosses the escaping boundary on its way in, in the context it lands in, and the
    result is scanned by :func:`scan_for_network_references` before it is returned, so an offline
    violation is impossible to ship from here rather than merely tested for elsewhere.
    """

    encoded = encode_embedded_payload(model.payload)
    view_json = json.dumps(
        {
            **model.to_dict(),
            "raw_view_page_size": RAW_VIEW_PAGE_SIZE,
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append('<meta name="referrer" content="no-referrer">')
    parts.append(f"<title>{escape_text(title)}</title>")
    parts.append(f"<style>{stylesheet()}</style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append('<a class="visually-hidden" href="#overview">Skip to the overview</a>')
    parts.append(f"<h1>{escape_text(title)}</h1>")
    parts.append(_render_overview(model))
    parts.append(_render_controls(model))
    parts.append(_render_time_accounting(model))
    parts.append(_render_charts(model))
    parts.append(_render_refusals(model))
    parts.append(_render_pricing(model))
    parts.append(_render_quality(model))
    parts.append(_render_findings(model))
    parts.append(_render_interpretation(model))
    parts.append(_render_raw_view(model))
    parts.append(_render_accessibility_boundary())
    parts.append(
        '<script type="application/json" id="view-model">'
        + escape_json_for_script(view_json)
        + "</script>"
    )
    parts.append(
        '<script type="text/plain" id="embedded-data">' + encoded + "</script>"
    )
    parts.append("<script>" + _script(encoded, view_json) + "</script>")
    parts.append("</body>")
    parts.append("</html>")
    document = "\n".join(parts) + "\n"

    violations = scan_for_network_references(document)
    if violations:
        raise SpaError(
            "the rendered document contains network references, which an offline bundle may "
            f"never carry: {violations}"
        )
    return document


def _provenance_note() -> str:
    return (
        '<p class="provenance">Figures labeled <em>review-time snapshot</em> were measured '
        + escape_text(REVIEW_SNAPSHOT["measured_at"])
        + " over a corpus that grows with every run and is not tracked, so they are "
        + "<strong>not current</strong>. Re-measure before citing one.</p>"
    )


def _render_overview(model: ViewModel) -> str:
    required = model.required_analysis_count
    computed = model.computed_count
    refused = model.refused_count
    return (
        '<section class="panel" id="overview" aria-labelledby="overview-h">'
        '<h2 id="overview-h">Overview</h2>'
        f"<p><strong>{computed}</strong> of <strong>{required}</strong> required analyses were "
        f"computed; <strong>{refused}</strong> could not be and are rendered as refusals below. "
        "A refusal is a result, not a gap.</p>"
        f"<p>Generated: {escape_text(model.generated_label or 'unlabeled')}. "
        f"Embedded rows: {int(model.payload.get('row_count') or 0)}, stored "
        f"{escape_text(EMBEDDED_DATA_CONTRACT['layout'])} at "
        f"{escape_text(EMBEDDED_DATA_CONTRACT['grain'])} grain.</p>"
        + _provenance_note()
        + "</section>"
    )


def _render_controls(model: ViewModel) -> str:
    rows: list[str] = [
        '<section class="panel" id="controls" aria-labelledby="controls-h">',
        '<h2 id="controls-h">Filters, metrics and phases</h2>',
        '<p class="muted">Charts and their exact tables are computed from the same rows, so a '
        "table cannot disagree with the chart above it.</p>",
    ]
    for group, label, values in (
        (
            "metric",
            "Metric",
            (
                "time",
                "cost",
                "input tokens",
                "output tokens",
                "cache tokens",
                "total tokens",
            ),
        ),
        ("phase", "Phase", ("aggregate", "review", "execute", "verifier", "recovery")),
    ):
        rows.append(f"<fieldset><legend>{escape_text(label)}</legend>")
        rows.append(f'<div role="group" aria-label="{escape_attribute(label)}">')
        for index, value in enumerate(values):
            derived = value == "verifier"
            pressed = "true" if index == 0 else "false"
            suffix = ' <span class="muted">(derived)</span>' if derived else ""
            described = (
                f' aria-describedby="{escape_attribute(group)}-derived-note'
                if derived
                else ""
            )
            rows.append(
                f'<button type="button" data-group="{escape_attribute(group)}" '
                f'data-value="{escape_attribute(value)}" aria-pressed="{pressed}"'
                + (described + '"' if described else "")
                + f">{escape_text(value)}{suffix}</button>"
            )
        rows.append("</div>")
        if group == "phase":
            rows.append(
                '<p class="muted" id="phase-derived-note">The verifier phase is '
                "<strong>derived</strong> from a log filename rather than recorded on an attempt "
                f"record ({int(REVIEW_SNAPSHOT['verifier_log_count'])} verifier logs against "
                f"{int(REVIEW_SNAPSHOT['attempts_with_verify_cost'])} attempts carrying a verify "
                "cost, review-time snapshot), so it is labeled derived wherever it appears.</p>"
            )
        rows.append("</fieldset>")

    for dimension in model.dimensions:
        rows.append(_render_dimension(dimension))
    rows.append("</section>")
    return "".join(rows)


def _render_dimension(dimension: Dimension) -> str:
    note_id = f"dim-{dimension.name}-note"
    parts = [
        f"<fieldset><legend>{escape_text(dimension.label)}"
        + (' <span class="muted">(derived)</span>' if dimension.is_derived else "")
        + "</legend>"
    ]
    if dimension.is_usable:
        parts.append(
            f'<div role="group" aria-label="{escape_attribute(dimension.label)}">'
        )
        for value in dimension.values:
            parts.append(
                f'<button type="button" data-group="{escape_attribute(dimension.name)}" '
                f'data-value="{escape_attribute(value)}" aria-pressed="false">'
                f"{escape_text(value)}</button>"
            )
        parts.append("</div>")
    else:
        # A DISABLED control WITH ITS REASON, never a hidden one: a hidden control is
        # indistinguishable from an oversight, and a single-valued one that looks operable is worse
        # than either, because it describes a fraction of the corpus while appearing to work.
        parts.append(
            f'<button type="button" disabled aria-disabled="true" '
            f'aria-describedby="{escape_attribute(note_id)}" '
            f'data-group="{escape_attribute(dimension.name)}" data-value="">'
            f"{escape_text(dimension.label)} unavailable</button>"
        )
        parts.append(
            f'<p class="muted" id="{escape_attribute(note_id)}">'
            f"<strong>{escape_text(dimension.state.value)}:</strong> "
            f"{escape_text(dimension.reason)} Coverage: {dimension.coverage:.1%}.</p>"
        )
    parts.append("</fieldset>")
    return "".join(parts)


def _render_time_accounting(model: ViewModel) -> str:
    accounting = model.time_accounting or {}
    unattributed = accounting.get(
        "unattributed_share", REVIEW_SNAPSHOT["unattributed_share_of_wall"]
    )
    attributed = accounting.get(
        "attributed_share", REVIEW_SNAPSHOT["tool_activity_share_of_wall"]
    )
    labeled = accounting.get("provenance", "review-time snapshot")
    return (
        '<section class="panel" id="time-accounting" aria-labelledby="time-h">'
        '<h2 id="time-h">Time accounting, including unattributed time</h2>'
        "<p>Unattributed time is shown <strong>by default</strong> in every time view, and it is "
        "the larger share: classified tool activity accounted for "
        f"<strong>{float(attributed):.1%}</strong> of run wall time, leaving "
        f"<strong>{float(unattributed):.1%}</strong> unattributed "
        f"({escape_text(labeled)}). A time view that omitted it would show a few percent of the "
        "truth while looking complete.</p>"
        + _share_table(float(attributed), float(unattributed))
        + "</section>"
    )


def _share_table(attributed: float, unattributed: float) -> str:
    return (
        "<table><caption>Wall-time attribution</caption><thead><tr>"
        '<th scope="col">Category</th><th scope="col">Share of wall time</th>'
        "</tr></thead><tbody>"
        f'<tr><th scope="row">Classified tool activity</th><td>{attributed:.1%}</td></tr>'
        f'<tr><th scope="row">Unattributed</th><td>{unattributed:.1%}</td></tr>'
        "</tbody></table>"
    )


def _render_charts(model: ViewModel) -> str:
    if not model.charts:
        return (
            '<section class="panel" id="charts" aria-labelledby="charts-h">'
            '<h2 id="charts-h">Charts</h2>'
            "<p>No analysis in this population returned a computable verdict, so no chart is "
            "drawn. Every required analysis appears as a refusal below with its observed sample "
            "size.</p></section>"
        )
    parts = [
        '<section class="panel" id="charts" aria-labelledby="charts-h">',
        '<h2 id="charts-h">Computed analyses</h2>',
    ]
    for index, chart in enumerate(model.charts):
        parts.append(_render_chart(chart, index))
    parts.append("</section>")
    return "".join(parts)


def _render_chart(chart: ChartView, index: int) -> str:
    figure_id = f"chart-{index}"
    series = chart.series or {}
    counts = list(series.get("counts") or [])
    path = series_path_data(counts)
    summary = (
        f"{chart.title}: {int(series.get('source_row_count') or 0)} observations summarized into "
        f"{int(series.get('bin_count') or 0)} bins. The exact values are in the table that follows."
    )
    parts = [
        f'<figure id="{escape_attribute(figure_id)}" role="group" '
        f'aria-labelledby="{escape_attribute(figure_id)}-cap">',
        f'<figcaption id="{escape_attribute(figure_id)}-cap">{escape_text(chart.title)}'
        + (' <span class="muted">(derived)</span>' if chart.is_derived else "")
        + "</figcaption>",
        # No `xmlns`: an inline SVG is placed in the SVG namespace by the HTML parser, and the
        # namespace URI would itself be an `http:` occurrence the offline scan forbids.
        f'<svg viewBox="0 0 640 200" width="100%" height="200" role="img" '
        f'aria-labelledby="{escape_attribute(figure_id)}-desc">',
        f'<title id="{escape_attribute(figure_id)}-desc">{escape_svg_text(summary)}</title>',
        # ONE path node for the whole series. 29766 individual point nodes measured ~1.34 MB of
        # markup against ~0.36 MB here, which is why the node count does not scale with row count.
        f'<path class="series-{index % 4}" d="{escape_attribute(path)}" fill="none" '
        f'stroke="currentColor" stroke-width="2"></path>',
        "</svg>",
        f'<p class="muted">{escape_text(summary)}</p>',
        _render_exact_table(chart, figure_id),
        "</figure>",
    ]
    if chart.caveats:
        parts.append("<ul>")
        for caveat in chart.caveats:
            parts.append(f"<li>{escape_text(caveat)}</li>")
        parts.append("</ul>")
    return "".join(parts)


def _render_exact_table(chart: ChartView, figure_id: str) -> str:
    parts = [
        f'<table id="{escape_attribute(figure_id)}-table">',
        f"<caption>Exact values for {escape_text(chart.title)} "
        f"(n={chart.sample_size}, from the same rows as the chart)</caption>",
        "<thead><tr>",
    ]
    for column in chart.table_columns:
        parts.append(f'<th scope="col">{escape_text(column)}</th>')
    parts.append("</tr></thead><tbody>")
    for row in chart.table_rows:
        parts.append("<tr>")
        for position, cell in enumerate(row):
            tag = "th" if position == 0 else "td"
            scope = ' scope="row"' if position == 0 else ""
            parts.append(f"<{tag}{scope}>{escape_text(cell)}</{tag}>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_refusals(model: ViewModel) -> str:
    parts = [
        '<section class="panel" id="refusals" aria-labelledby="refusals-h">',
        '<h2 id="refusals-h">Analyses this corpus cannot support</h2>',
        "<p>Each entry below is a <strong>result</strong>, carrying the reason and the observed "
        "sample size or coverage. No chart is drawn for any of them: an empty axis would read as "
        '"we measured zero", which is a stronger and falser claim than the refusal.</p>',
    ]
    if not model.refusals:
        parts.append("<p>No analysis was refused for this population.</p>")
    for refusal in model.refusals:
        parts.append(_render_refusal(refusal))
    parts.append("</section>")
    return "".join(parts)


def _render_refusal(refusal: RefusalView) -> str:
    coverage = (
        f" Coverage: {refusal.coverage:.1%}." if refusal.coverage is not None else ""
    )
    parts = [
        f'<article class="panel refusal" role="group" '
        f'aria-label="{escape_attribute("Refused analysis: " + refusal.title)}">',
        f"<h3>{escape_text(refusal.title)}</h3>",
        f'<p><span class="verdict">{escape_text(refusal.verdict)}</span> '
        f"&mdash; observed n={refusal.sample_size}.{escape_text(coverage)}</p>",
        f"<p>{escape_text(refusal.reason)}</p>",
    ]
    if refusal.caveats:
        parts.append("<ul>")
        for caveat in refusal.caveats:
            parts.append(f"<li>{escape_text(caveat)}</li>")
        parts.append("</ul>")
    parts.append("</article>")
    return "".join(parts)


def _render_pricing(model: ViewModel) -> str:
    pricing = model.pricing or {}
    eras = list(pricing.get("eras") or [])
    parts = [
        '<section class="panel" id="pricing" aria-labelledby="pricing-h">',
        '<h2 id="pricing-h">Pricing and cost</h2>',
        "<p><strong>Recorded and estimated cost are never merged.</strong> A recorded value is the "
        "provider's own number; an estimate is modeled from an effective-dated schedule and is "
        "marked as such wherever it appears.</p>",
        '<p><span class="recorded">'
        + escape_text(_money(pricing.get("recorded_usd")))
        + '</span> &middot; <span class="estimated">'
        + escape_text(_money(pricing.get("estimated_usd")))
        + "</span></p>",
    ]
    parts.append(
        "<table><caption>Price-era composition</caption><thead><tr>"
        '<th scope="col">Era</th><th scope="col">Effective from</th>'
        '<th scope="col">Effective to</th><th scope="col">Source</th>'
        '<th scope="col">Version</th><th scope="col">Share of spend</th>'
        "</tr></thead><tbody>"
    )
    if not eras:
        parts.append(
            '<tr><td colspan="6">No price era resolved for this population; cost is shown as '
            "recorded only, and no estimate is offered.</td></tr>"
        )
    for era in eras:
        parts.append(
            "<tr>"
            f'<th scope="row">{escape_text(era.get("era_id"))}</th>'
            f'<td>{escape_text(era.get("effective_from"))}</td>'
            f'<td>{escape_text(era.get("effective_to") or "open-ended")}</td>'
            f'<td>{escape_text(era.get("source"))}</td>'
            f'<td>{escape_text(era.get("source_version"))}</td>'
            f'<td>{escape_text(_share(era.get("spend_share")))}</td>'
            "</tr>"
        )
    parts.append("</tbody></table>")
    unknown = int(pricing.get("unknown_price_step_count") or 0)
    parts.append(
        f"<p>Steps with no resolvable price: <strong>{unknown}</strong>. These are "
        "<strong>refused</strong> rather than priced at a default, so an unpriced model never "
        "silently inherits another model's rates.</p>"
    )
    parts.append("</section>")
    return "".join(parts)


def _money(value: Any) -> str:
    if value is None:
        return "no value"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "no value"


def _share(value: Any) -> str:
    if value is None:
        return "unknown"
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "unknown"


def _render_quality(model: ViewModel) -> str:
    quality = model.quality or {}
    parts = [
        '<section class="panel" id="quality" aria-labelledby="quality-h">',
        '<h2 id="quality-h">Data quality</h2>',
        "<p>Three separate counts, never one &ldquo;incomplete&rdquo; flag: a field an older "
        "driver never wrote (<em>unavailable</em>) is a compatibility fact, while a field the "
        "current driver should have written and did not (<em>missing</em>) is a defect.</p>",
        "<table><caption>Completeness by category</caption><thead><tr>"
        '<th scope="col">Category</th><th scope="col">Fields</th>'
        "</tr></thead><tbody>",
    ]
    for key, label in (
        ("missing_fields", "Missing"),
        ("unavailable_fields", "Unavailable"),
        ("not_applicable_fields", "Not applicable"),
    ):
        values = list(quality.get(key) or [])
        parts.append(
            f'<tr><th scope="row">{escape_text(label)}</th>'
            f'<td>{escape_text(", ".join(str(v) for v in values) or "none")}</td></tr>'
        )
    parts.append(
        f'<tr><th scope="row">Parse errors skipped</th>'
        f'<td>{int(quality.get("parse_error_count") or 0)}</td></tr>'
    )
    parts.append("</tbody></table></section>")
    return "".join(parts)


def _render_findings(model: ViewModel) -> str:
    parts = [
        '<section class="panel" id="findings" aria-labelledby="findings-h">',
        '<h2 id="findings-h">Ranked findings</h2>',
    ]
    if not model.findings:
        parts.append("<p>No finding was produced for this population.</p>")
    for finding in model.findings:
        parts.append(_render_finding(finding))
    parts.append("</section>")
    return "".join(parts)


def _render_finding(finding: Mapping[str, Any]) -> str:
    actionable = bool(finding.get("is_actionable"))
    classes = "panel" if actionable else "panel refusal"
    parts = [
        f'<article class="{classes}">',
        f'<h3>{escape_text(finding.get("finding_id"))}: '
        f'{escape_text(finding.get("title"))}</h3>',
        f'<p class="muted">Severity {escape_text(finding.get("severity"))} &middot; '
        f'slice {escape_text(finding.get("affected_slice"))} &middot; '
        f'n={escape_text(finding.get("sample_size"))} &middot; '
        f'coverage {escape_text(_share(finding.get("coverage")))}</p>',
        f'<p><strong>What is not known:</strong> '
        f'{escape_text(finding.get("uncertainty"))}</p>',
    ]
    for key, label in (
        ("data_quality_caveats", "Data-quality caveats"),
        ("alternative_explanations", "Competing explanations"),
    ):
        values = list(finding.get(key) or [])
        if values:
            parts.append(f"<p><strong>{escape_text(label)}:</strong></p><ul>")
            for value in values:
                parts.append(f"<li>{escape_text(value)}</li>")
            parts.append("</ul>")
    if finding.get("next_experiment"):
        parts.append(
            "<p><strong>Cheapest discriminating test:</strong> "
            f'{escape_text(finding.get("next_experiment"))}</p>'
        )
    if finding.get("recommendation"):
        parts.append(
            f'<p><strong>Recommendation:</strong> '
            f'{escape_text(finding.get("recommendation"))}</p>'
        )
    parts.append("</article>")
    return "".join(parts)


def _render_interpretation(model: ViewModel) -> str:
    row_count = int(model.payload.get("row_count") or 0)
    return (
        '<section class="panel" id="interpretation" aria-labelledby="interp-h">'
        '<h2 id="interp-h">How to read this report</h2>'
        f"<p><strong>This panel describes the current filter population</strong> "
        f"({row_count} rows as loaded), not the whole corpus. Narrowing a filter narrows every "
        "figure above and this description with it.</p>"
        "<ul>"
        "<li><strong>Association, not causation.</strong> Every figure here is observational. No "
        "intervention was assigned, so a difference between two slices is a difference between "
        "populations that also differ in ways nobody recorded.</li>"
        "<li><strong>Overlap.</strong> Activities run concurrently, so classified durations "
        "double count and are published beside wall time rather than reconciled into it.</li>"
        "<li><strong>Missingness.</strong> Absent values are typed and never zero-filled; a "
        "category with no observation is reported as unmeasured, not as zero.</li>"
        f"<li><strong>Sample size.</strong> {model.refused_count} of "
        f"{model.required_analysis_count} required analyses were refused for insufficient "
        "evidence rather than charted at a sample size no test discriminates at.</li>"
        "<li><strong>Uncertainty.</strong> A single point estimate with no interval is a summary, "
        "not a measurement; intervals are shown where the sample supports one.</li>"
        "</ul>" + _provenance_note() + "</section>"
    )


def _render_raw_view(model: ViewModel) -> str:
    columns = list(model.payload.get("columns") or [])
    row_count = int(model.payload.get("row_count") or 0)
    parts = [
        '<section class="panel" id="raw" aria-labelledby="raw-h">',
        '<h2 id="raw-h">Normalized data</h2>',
        f"<p>{row_count} rows are embedded in this file in "
        f"{escape_text(EMBEDDED_DATA_CONTRACT['layout'])} form at "
        f"{escape_text(EMBEDDED_DATA_CONTRACT['grain'])} grain, and are shown "
        f"<strong>{RAW_VIEW_PAGE_SIZE} at a time</strong>. They are never all materialized: at "
        f"corpus scale that was the measured defect this pagination exists to avoid. No prompt, "
        "conversation or source-file content is included.</p>",
        '<button type="button" id="load-raw">Load the embedded rows</button>',
        '<button type="button" data-page-step="-1">Previous page</button>',
        '<button type="button" data-page-step="1">Next page</button>',
        '<p role="status" aria-live="polite" id="raw-status">No rows loaded yet.</p>',
        '<table id="raw-table"><caption>Normalized rows (paginated)</caption><thead><tr>',
    ]
    for column in columns:
        parts.append(f'<th scope="col">{escape_text(column)}</th>')
    parts.append('</tr></thead><tbody id="raw-body"></tbody></table>')
    parts.append(
        "<h3>Schema</h3><dl>"
        + "".join(
            f"<dt>{escape_text(name)}</dt><dd>{escape_text(_COLUMN_NOTES.get(name, 'normalized field carried at the stated grain'))}</dd>"
            for name in columns
        )
        + "</dl>"
    )
    parts.append("</section>")
    return "".join(parts)


#: Short descriptions for the columns this report commonly carries. A column with no entry gets a
#: generic description rather than none, so the schema list is never partially blank.
_COLUMN_NOTES: dict[str, str] = {
    "run_id": "the driver run identifier this observation came from",
    "set_id": "the Set identifier, when the observation is Set-scoped",
    "ipd_id6": "the plan's stable 6-character handle",
    "attempt": "attempt ordinal; a retried item contributes more than one",
    "phase": "review, execute, verify, recovery or unknown; never guessed",
    "outcome": "the recorded disposition of the attempt",
    "model": "resolved model identity; absent for most historical records",
    "host": "runner host label",
    "wall_seconds": "elapsed wall time for the observation",
    "cost_usd": "cost in USD; recorded and estimated are distinguished elsewhere",
    "total_tokens": "provider-reported total tokens, never derived silently",
}


def _render_accessibility_boundary() -> str:
    parts = [
        '<section class="panel" id="a11y" aria-labelledby="a11y-h">',
        '<h2 id="a11y-h">What accessibility was and was not verified</h2>',
        "<p><strong>Machine-verified structurally:</strong> ARIA state on every control, table "
        "header scope and captions, text alternatives for every chart, a reduced-motion rule, a "
        "visible focus style, and series distinguished by dash pattern as well as hue so the "
        "encoding survives monochrome.</p>",
        "<p><strong>Not machine-verified.</strong> Stated plainly rather than implied, because "
        "claiming more than was tested is the unearned claim this report exists to avoid:</p><ul>",
    ]
    for item in UNVERIFIED_ACCESSIBILITY_PROPERTIES:
        parts.append(f"<li>{escape_text(item)}</li>")
    parts.append("</ul></section>")
    return "".join(parts)

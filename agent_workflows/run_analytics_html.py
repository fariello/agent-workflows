#!/usr/bin/env python3
"""HTML safety helpers for the run-analytics dashboard: escaping and the offline network scan.

These outlived the classic analytics report (`run_analytics_spa`, removed 2026-10-17), which first
defined them; the dashboard (`run_dashboard.render_dashboard`) is their only consumer now.

TEXT, AN ATTRIBUTE AND A JSON ISLAND NEED DIFFERENT ESCAPES. :func:`escape_text` is for HTML text,
:func:`escape_attribute` for an attribute value, and :func:`escape_json_for_script` for the
``<script type="application/json">`` data island the dashboard embeds. The HTML escapes route
through :func:`sanitize_control_characters` first, because escaping cannot neutralize a bidi
override: a numeric character reference decodes to the same active code point.

OFFLINE IS A TESTED PROPERTY. :func:`scan_for_network_references` lists every network reference in a
document; the dashboard refuses to return a document for which it finds any.
"""

from __future__ import annotations

import html
import unicodedata
from typing import Any

__all__ = [
    "HtmlSafetyError",
    "sanitize_control_characters",
    "escape_text",
    "escape_attribute",
    "escape_json_for_script",
    "scan_for_network_references",
    "FORBIDDEN_NETWORK_TOKENS",
]


class HtmlSafetyError(ValueError):
    """A render was refused because it would have produced an unsafe or non-offline document."""


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

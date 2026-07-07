"""Accessible terminal styling for the CLI (stdlib only).

Held to the terminal-accessibility rubric in
`.agents/workflows/assess/lenses/accessibility.md` (WCAG-inspired POUR for text UIs):

- Color/style is NEVER the sole carrier of meaning: every status prints a WORD
  (OK / SKIP / FAIL / WARN / ...) so the message is complete in monochrome (AC-15).
- Honor `NO_COLOR` (any value disables), `FORCE_COLOR` (enables even when not a TTY),
  `TERM=dumb`/unset (degrade), and `isatty()` false (plain when piped/redirected).
- Use only the 16 named colors and the terminal's default fg/bg (no assumed background,
  no truecolor). No blink; no load-bearing dim.
- Output stays linear `key: value` / `LABEL  text` so it survives screen readers and
  redirection.

When color is off, `colorize()` returns the text unchanged, so piping or `NO_COLOR=1`
yields clean plain text with the status words intact.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, TextIO

# SGR codes (16-color / attributes only; no truecolor, no blink, no load-bearing dim).
_RESET = "\033[0m"
_CODES = {
    "bold": "1",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "cyan": "36",
    "gray": "90",  # bright-black; used ONLY for decoration, never load-bearing text
}

# Status labels are words first; color is an optional redundant cue.
# label -> (word, color)
_STATUS_STYLE = {
    "ok": ("OK", "green"),
    "current": ("CURRENT", "green"),
    "installed": ("INSTALLED", "green"),
    "skip": ("SKIP", "yellow"),
    "ignored": ("IGNORED", "gray"),
    "warn": ("WARN", "yellow"),
    "stale": ("STALE", "yellow"),
    "ahead": ("AHEAD", "cyan"),
    "dev": ("DEV", "cyan"),
    "fail": ("FAIL", "red"),
    "failed": ("FAILED", "red"),
    "not-installed": ("NOT-INSTALLED", "gray"),
    "unknown": ("UNKNOWN", "gray"),
}


def should_color(stream: Optional[TextIO] = None) -> bool:
    """Decide whether to emit ANSI color for ``stream`` (default stdout).

    Precedence: NO_COLOR (off) is only overridden by FORCE_COLOR (on). Otherwise color is
    on only for a real TTY with a capable TERM.
    """

    stream = stream or sys.stdout

    # NO_COLOR: any value (even empty) disables, UNLESS FORCE_COLOR is set.
    if "NO_COLOR" in os.environ and "FORCE_COLOR" not in os.environ:
        return False
    # FORCE_COLOR: any value forces color on (overrides TTY detection).
    if os.environ.get("FORCE_COLOR"):
        return True

    term = os.environ.get("TERM", "")
    if term == "dumb" or term == "":
        return False

    isatty = getattr(stream, "isatty", None)
    try:
        return bool(isatty and isatty())
    except Exception:
        return False


class Term:
    """A small styling helper bound to a stream's color decision."""

    def __init__(self, stream: Optional[TextIO] = None, color: Optional[bool] = None):
        self.stream = stream or sys.stdout
        self.color = should_color(self.stream) if color is None else color

    def colorize(self, text: str, *styles: str) -> str:
        """Wrap ``text`` in the named styles when color is enabled, else return it plain."""

        if not self.color or not styles:
            return text
        codes = ";".join(_CODES[s] for s in styles if s in _CODES)
        if not codes:
            return text
        return f"\033[{codes}m{text}{_RESET}"

    def status_label(self, status: str) -> str:
        """Return the styled status LABEL (a word, optionally colored) for a status key.

        The word is always present so meaning survives monochrome / piped output.
        """

        word, colorname = _STATUS_STYLE.get(status, (status.upper(), None))
        if colorname:
            return self.colorize(word, colorname, "bold")
        return word

    def line(self, text: str = "") -> None:
        print(text, file=self.stream)

    def status(self, status: str, message: str) -> None:
        """Print a `LABEL  message` line (label word first; color is a redundant cue)."""

        self.line(f"{self.status_label(status)}  {message}")

    def heading(self, text: str) -> None:
        self.line(self.colorize(text, "bold"))

    def kv(self, key: str, value: str) -> None:
        """Print a screen-reader-friendly `key: value` line."""

        self.line(f"{self.colorize(key, 'bold')}: {value}")

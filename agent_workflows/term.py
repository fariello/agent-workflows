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

Output Conventions (GUIDING_PRINCIPLES P14 / UX-005):
- Human TTY: concise, fixed-width scannable output styled via `Term` (bold-colored words,
  bracketed fixed-width severity labels `[ERROR]`, `[WARN ]`, `[INFO ]`).
- Non-TTY / machine: all read verbs support universal machine flags (`--agent` / `--json`)
  for unstyled, parseable stream output.

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
    "error": ("ERROR", "red"),
    "info": ("INFO", "green"),
    "not-installed": ("NOT-INSTALLED", "gray"),
    "unknown": ("UNKNOWN", "gray"),
}
_STATUS_WIDTH = max(len(w) for w, _ in _STATUS_STYLE.values())


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


STATUS_COLOR_256 = {
    "active": 39,
    "intake": 44,  # teal
    "open": 40,
    "ready": 40,
    "pending": 40,
    "approved": 46,  # bright green
    "reviewed": 226,  # yellow
    "to-review": 214,  # orange
    "draft": 245,  # gray
    "implementing": 51,  # cyan
    "implemented": 46,
    "executed": 46,
    "reusable": 39,
    "blocked": 203,
    "deferred": 208,  # orange-red
    "done": 244,
    "parked": 244,
    "superseded": 240,
    "not-executed": 240,
}


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

    def color256(self, text: str, code: int, *, bold: bool = False) -> str:
        """Wrap ``text`` in an xterm-256 foreground color (SGR 38;5;N) when color is on.

        ``code`` is a 0-255 xterm-256 palette index. Returns plain text when color is
        disabled (NO_COLOR / non-TTY / TERM=dumb), so meaning must never depend on it.
        Every 256-color virtually all terminals of the last two decades support; the
        NO_COLOR/isatty/TERM gating in ``should_color`` still fully applies.
        """

        if not self.color:
            return text
        n = max(0, min(255, int(code)))
        prefix = "1;" if bold else ""
        return f"\033[{prefix}38;5;{n}m{text}{_RESET}"

    def status_256(self, status: str, *, width: int = 0) -> str:
        """Format a status word with its 256-color palette index, padded to width."""
        code = STATUS_COLOR_256.get(status.lower(), 244)
        styled = self.color256(status, code, bold=True)
        if width > len(status):
            return styled + (" " * (width - len(status)))
        return styled

    def severity_label(self, kind: str) -> str:
        """Return the P14 bracketed, fixed-width, bold-colored severity label for ``kind``.

        When color is enabled:
          - 'error' -> '[' + color256('ERROR', 196, bold=True) + ']'
          - 'warn' / 'warning' -> '[' + color256('WARN ', 226, bold=True) + ']'
          - 'info' -> '[' + color256('INFO ', 46, bold=True) + ']'
        When color is disabled (NO_COLOR / non-TTY / TERM=dumb):
          - 'error' -> '[ERROR]'
          - 'warn' / 'warning' -> '[WARN ]'
          - 'info' -> '[INFO ]'

        Brackets are uncolored and the words are padded to width 5 so the brackets align.
        """
        k = kind.lower()
        if k == "error":
            word, code = "ERROR", 196
        elif k in ("warn", "warning"):
            word, code = "WARN ", 226
        elif k == "info":
            word, code = "INFO ", 46
        else:
            word, code = f"{kind.upper()}", 244
            if len(word) < 5:
                word = word.ljust(5)

        styled = self.color256(word, code, bold=True) if self.color else word
        return f"[{styled}]"

    def status_label(self, status: str, *, width: int = _STATUS_WIDTH) -> str:
        """Return the styled status LABEL (a word, optionally colored) for a status key.

        Padded to a fixed width so message columns align on a TTY.
        The word is always present so meaning survives monochrome / piped output.
        """

        word, colorname = _STATUS_STYLE.get(status.lower(), (status.upper(), None))
        styled = self.colorize(word, colorname, "bold") if colorname else word
        if width > len(word):
            return styled + (" " * (width - len(word)))
        return styled

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


def severity_label(kind: str, term: Optional[Term] = None) -> str:
    """Convenience helper to format a P14 bracketed severity label using ``term`` or a default Term."""
    t = term or Term()
    return t.severity_label(kind)

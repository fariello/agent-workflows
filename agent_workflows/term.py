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
import re
import sys
from typing import Any, Optional, Sequence, TextIO, Tuple, Union

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from ``text``."""
    return _ANSI_RE.sub("", text)


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
    # Lifecycle & status states
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
    # Extended roles (awcliux Order 02 E-01)
    "success": 46,
    "conforms": 46,
    "ok": 46,
    "info": 39,
    "warning": 226,
    "warn": 226,
    "action": 214,
    "preview": 214,
    "failure": 196,
    "fail": 196,
    "failed": 196,
    "error": 196,
    "paths": 33,
    "path": 33,
    "secondary": 245,
}

# Unicode glyphs and their deterministic ASCII fallbacks (AC-15)
GLYPHS = {
    "ok": "✓",
    "success": "✓",
    "conforms": "✓",
    "clean": "✓",
    "check": "✓",
    "warn": "!",
    "warning": "!",
    "preview": "!",
    "fail": "✗",
    "failure": "✗",
    "failed": "✗",
    "error": "✗",
    "findings": "✗",
    "arrow": "→",
    "bullet": "•",
    "pointer": "›",
    "cross": "✗",
}

ASCII_GLYPHS = {
    "ok": "OK",
    "success": "OK",
    "conforms": "OK",
    "clean": "OK",
    "check": "OK",
    "warn": "!",
    "warning": "!",
    "preview": "!",
    "fail": "FAIL",
    "failure": "FAIL",
    "failed": "FAIL",
    "error": "FAIL",
    "findings": "FAIL",
    "arrow": "->",
    "bullet": "*",
    "pointer": ">",
    "cross": "X",
}


def should_unicode(stream: Optional[TextIO] = None) -> bool:
    """Decide whether to emit Unicode glyphs for ``stream`` (default stdout).

    Degrades to ASCII fallbacks when:
    - AW_ASCII_ONLY or FORCE_ASCII is set in os.environ
    - stream encoding is ascii, us-ascii, cp1252, or not utf-8/utf8
    """
    if os.environ.get("AW_ASCII_ONLY") == "1" or os.environ.get("FORCE_ASCII") == "1":
        return False
    stream = stream or sys.stdout
    enc = getattr(stream, "encoding", None)
    if enc:
        enc_lower = enc.lower()
        if "ascii" in enc_lower or "cp1252" in enc_lower or "ansi" in enc_lower:
            return False
        if "utf" in enc_lower:
            return True
    return True


class Term:
    """A small styling helper bound to a stream's color decision."""

    def __init__(
        self,
        stream: Optional[TextIO] = None,
        color: Optional[bool] = None,
        unicode: Optional[bool] = None,
    ):
        self.stream = stream or sys.stdout
        self.color = should_color(self.stream) if color is None else color
        self.unicode = should_unicode(self.stream) if unicode is None else unicode

    def glyph(self, name: str) -> str:
        """Return the Unicode glyph or its ASCII fallback depending on self.unicode."""
        k = name.lower()
        if self.unicode:
            return GLYPHS.get(k, k)
        return ASCII_GLYPHS.get(k, k)

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

    # ----------------------------------------------------------------------------------
    # Shared 11 TTY Components (awcliux Order 02 E-01)
    # ----------------------------------------------------------------------------------

    def format_title(
        self,
        command: str,
        target: str = "",
        *,
        elapsed_ms: Optional[int] = None,
        width: int = 80,
    ) -> str:
        """Format top title banner: AW <command>  <target>       <elapsed_ms> ms"""
        cmd_part = f"AW {command}"
        styled_cmd = self.colorize(cmd_part, "bold")
        target_part = f"  {target}" if target else ""
        left = f"{styled_cmd}{target_part}"
        left_plain = f"{cmd_part}{target_part}"
        right = f"{elapsed_ms} ms" if elapsed_ms is not None else ""
        if right and width > len(left_plain) + len(right) + 1:
            padding = " " * (width - len(left_plain) - len(right))
            return f"{left}{padding}{right}"
        if right:
            return f"{left}  {right}"
        return left

    def title(
        self,
        command: str,
        target: str = "",
        *,
        elapsed_ms: Optional[int] = None,
        width: int = 80,
    ) -> None:
        self.line(
            self.format_title(command, target, elapsed_ms=elapsed_ms, width=width)
        )

    def format_outcome(self, status: str, message: str = "") -> str:
        """Format top outcome banner: [glyph] [STATUS]  [message]"""
        s_norm = status.lower()
        glyph_str = self.glyph(s_norm)
        status_word = status.upper()
        code = STATUS_COLOR_256.get(s_norm, 244)
        badge_str = f"{glyph_str} {status_word}"
        styled_badge = self.color256(badge_str, code, bold=True)
        msg_part = f"  {message}" if message else ""
        return f"{styled_badge}{msg_part}"

    def outcome(self, status: str, message: str = "") -> None:
        self.line(self.format_outcome(status, message))

    def format_section(self, title: str) -> str:
        """Format section header line (e.g. 'Evidence', 'Findings', 'Would change')."""
        return self.colorize(title, "bold")

    def section(self, title: str) -> None:
        self.line(self.format_section(title))

    def format_table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        *,
        align: Optional[Sequence[str]] = None,
        width: Optional[int] = None,
    ) -> str:
        """Format tabular data with fixed-width scannable alignment."""
        if not headers and not rows:
            return ""
        str_rows = [[str(c) for c in r] for r in rows]
        num_cols = max(len(headers), max((len(r) for r in str_rows), default=0))
        padded_headers = list(headers) + [""] * (num_cols - len(headers))
        col_widths = [len(strip_ansi(h)) for h in padded_headers]
        for r in str_rows:
            for idx, c in enumerate(r):
                if idx < num_cols:
                    col_widths[idx] = max(col_widths[idx], len(strip_ansi(c)))
        lines = []
        if headers:
            hdr_cols = [
                self.colorize(h.ljust(col_widths[i]), "bold")
                for i, h in enumerate(padded_headers)
            ]
            lines.append("  ".join(hdr_cols))
        for r in str_rows:
            row_cols = []
            for i in range(num_cols):
                val = r[i] if i < len(r) else ""
                plain_len = len(strip_ansi(val))
                pad = max(0, col_widths[i] - plain_len)
                row_cols.append(val + (" " * pad))
            lines.append("  ".join(row_cols))
        return "\n".join(lines)

    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
        *,
        align: Optional[Sequence[str]] = None,
        width: Optional[int] = None,
    ) -> None:
        t = self.format_table(headers, rows, align=align, width=width)
        if t:
            self.line(t)

    def badge(
        self,
        label: str,
        role_or_code: Union[str, int] = "info",
        *,
        bold: bool = True,
    ) -> str:
        """Format a bracketed colored badge: [LABEL]."""
        if isinstance(role_or_code, int):
            code = role_or_code
        else:
            code = STATUS_COLOR_256.get(str(role_or_code).lower(), 244)
        if self.color:
            inner = self.color256(label, code, bold=bold)
            return f"[{inner}]"
        return f"[{label}]"

    def format_path(self, path_str: str) -> str:
        """Format a file or directory path using the 'paths' palette role (33)."""
        code = STATUS_COLOR_256.get("paths", 33)
        return self.color256(path_str, code)

    def path(self, path_str: str) -> str:
        return self.format_path(path_str)

    def format_diagnostic(
        self,
        location: str,
        rule: str,
        detail: str,
        severity: str = "error",
        fix: Optional[str] = None,
    ) -> str:
        """Format a diagnostic finding line: - <loc>: [<rule>] <detail> with optional Fix."""
        loc_txt = self.format_path(location)
        rule_badge = self.badge(rule, severity)
        line = f"  - {loc_txt}: {rule_badge} {detail}"
        if fix:
            fix_txt = self.format_fix(fix)
            line += f"\n      {fix_txt}"
        return line

    def diagnostic(
        self,
        location: str,
        rule: str,
        detail: str,
        severity: str = "error",
        fix: Optional[str] = None,
    ) -> None:
        self.line(
            self.format_diagnostic(location, rule, detail, severity=severity, fix=fix)
        )

    def format_preview(
        self,
        kind: str,
        source_path: str,
        target_path: Optional[str] = None,
        detail: str = "",
    ) -> str:
        """Format a preview line: file old.md -> new.md or refs 3 files."""
        arrow = self.glyph("arrow")
        src = self.format_path(source_path)
        if target_path:
            tgt = self.format_path(target_path)
            line = f"  {kind:<4}  {src} {arrow} {tgt}"
        else:
            line = f"  {kind:<4}  {src}"
        if detail:
            line += f" ({detail})"
        return line

    def preview(
        self,
        kind: str,
        source_path: str,
        target_path: Optional[str] = None,
        detail: str = "",
    ) -> None:
        self.line(self.format_preview(kind, source_path, target_path, detail))

    def format_evidence(
        self,
        key: str,
        value: Any,
        status: str = "verified",
        detail: str = "",
    ) -> str:
        """Format an evidence key-value summary line."""
        k_styled = self.colorize(f"{key}:", "bold")
        val_str = str(value)
        det_str = f" ({detail})" if detail else ""
        return f"  {k_styled} {val_str}{det_str}"

    def format_evidence_grid(self, items: Sequence[Tuple[str, Any]]) -> str:
        """Format an evidence grid on one or more lines: pending 17  reusable 2  terminal 41"""
        cols = []
        for k, v in items:
            k_styled = self.colorize(k, "bold") if self.color else k
            cols.append(f"{k_styled}  {v}")
        return "  " + "   ".join(cols)

    def evidence(
        self,
        key: str,
        value: Any,
        status: str = "verified",
        detail: str = "",
    ) -> None:
        self.line(self.format_evidence(key, value, status, detail))

    def format_fix(self, action: str) -> str:
        """Format a suggested fix line: Fix: <action>."""
        prefix = self.color256("Fix:", 46, bold=True) if self.color else "Fix:"
        return f"{prefix} {action}"

    def fix(self, action: str) -> None:
        self.line(self.format_fix(action))

    def format_next_action(self, command: str, description: str = "") -> str:
        """Format a next action recommendation: Next  <command>"""
        prefix = self.colorize("Next", "bold") if self.color else "Next"
        cmd_txt = self.color256(command, 39) if self.color else command
        desc_txt = f" ({description})" if description else ""
        return f"{prefix}  {cmd_txt}{desc_txt}"

    def next_action(self, command: str, description: str = "") -> None:
        self.line(self.format_next_action(command, description))


def severity_label(kind: str, term: Optional[Term] = None) -> str:
    """Convenience helper to format a P14 bracketed severity label using ``term`` or a default Term."""
    t = term or Term()
    return t.severity_label(kind)

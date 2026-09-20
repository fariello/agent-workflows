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
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, TextIO, Tuple, Union

from . import lifecycle_style

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from ``text``."""
    return _ANSI_RE.sub("", text)


# ======================================================================================
# Visible width and grapheme-safe truncation (spec `uonrjg` Section 9.4)
# ======================================================================================
#
# THE TWO PRIMITIVES SECTION 9.4 NEEDS, and the reason they live HERE rather than beside each
# consumer is that the section says so in as many words: an implementation "MAY add a shared
# display-width helper ... but MUST NOT create per-renderer width guesses". `term.py` is the one
# module every renderer already imports, so this is the conforming home.
#
# WHAT THEY ARE NOT. They are NOT a wcwidth-style 0/1/2 table and deliberately make no attempt to
# resolve East Asian AMBIGUOUS width. Section 9.4 states outright that "perfect alignment cannot be
# guaranteed across every terminal's ambiguous-width policy", and two of this spec's own lifecycle
# glyphs are Ambiguous (`▶` U+25B6 and `◇` U+25C7, measured), so no table here could make a
# terminal's policy agree with ours. What these primitives DO fix is the ZERO-width case, which is
# not a terminal-policy judgement at all but a deterministic Unicode property, and which Section
# 9.4's other three contract bullets cannot be met without.
#
# THE DEFECT THEY CLOSE, measured by execution 2026-09-19 rather than read:
#
#   Term(color=False).status_256('\u26a0\ufe0e', width=4) -> 4 codepoints, 3 rendered columns
#   Term(color=False).status_256('\u25d5',       width=4) -> 4 codepoints, 4 rendered columns
#
# i.e. a lifecycle column padded by `len()` comes out one column short for exactly the two glyphs
# that carry U+FE0E (`blocked` and `recovering`). `strip_ansi` is NOT the missing piece: it already
# preserves U+FE0E correctly. The defect is that a zero-width code point was then counted as one
# column.

#: Unicode general categories whose members occupy NO terminal column. ``Mn``/``Me`` are the
#: non-spacing and enclosing marks (this is where the text-presentation variation selectors U+FE0E
#: and U+FE0F live, and every combining accent); ``Cf`` is the format class (ZWJ, ZWSP, the
#: bidi controls). Held as a frozenset of category names rather than as a codepoint list because the
#: category is the PROPERTY that makes a code point zero-width, so this cannot rot as Unicode grows.
_ZERO_WIDTH_CATEGORIES = frozenset(("Mn", "Me", "Cf"))


def is_zero_width(ch: str) -> bool:
    """Does ``ch`` occupy no terminal column?

    Deterministic and data-driven: a combining or enclosing mark, or a format control. This is the
    half of display width that IS knowable, as distinct from the ambiguous-width half that
    Section 9.4 declines to guarantee.
    """

    return unicodedata.category(ch) in _ZERO_WIDTH_CATEGORIES


def visible_width(text: str) -> int:
    """Return the number of terminal columns ``text`` occupies, ignoring ANSI and zero-width marks.

    THE SINGLE VISIBLE-COLUMN MEASUREMENT for lifecycle rendering, and the one Section 9.4's fourth
    contract bullet demands in place of ``len(styled_text)``. Two properties callers rely on:

    1. It is ANSI-AWARE, built on :func:`strip_ansi` rather than on a second stripping path, so the
       styled and unstyled forms of the same text measure the SAME.
    2. It counts a zero-width code point as ZERO, so `⚠︎` (U+26A0 U+FE0E) measures 1 and not 2.

    It does NOT attempt double-width or ambiguous-width resolution; see the section note above.
    """

    return sum(0 if is_zero_width(ch) else 1 for ch in strip_ansi(text))


def _pad_visible(text: str, width: int) -> str:
    """Left-align ``text`` to ``width`` VISIBLE columns (the ``str.ljust`` a styled cell needs).

    ``str.ljust`` and ``len()`` both count escape bytes and zero-width marks as columns, so either
    one leaves a styled or VS-bearing cell short. This is the one padding path lifecycle rendering
    uses, which is what Section 9.4's fourth contract bullet asks for.
    """

    pad = width - visible_width(text)
    return text + (" " * pad) if pad > 0 else text


def _tokenize_ansi(text: str) -> List[Tuple[bool, str]]:
    """Split ``text`` into ``(is_escape, token)`` pairs, one CHARACTER per non-escape token.

    Shares the one ``_ANSI_RE`` with :func:`strip_ansi` rather than re-deriving escape syntax, so
    there is exactly one definition of "what an escape looks like" in this module.
    """

    tokens: List[Tuple[bool, str]] = []
    pos = 0
    for match in _ANSI_RE.finditer(text):
        for ch in text[pos : match.start()]:
            tokens.append((False, ch))
        tokens.append((True, match.group(0)))
        pos = match.end()
    for ch in text[pos:]:
        tokens.append((False, ch))
    return tokens


def truncate_visible(text: str, limit: int, *, ellipsis: str = "") -> str:
    """Truncate ``text`` to ``limit`` visible columns WITHOUT severing a grapheme.

    Section 9.4's first contract bullet ("no broken variation selector in every UTF-8 mode") is what
    this exists for, and the failure it prevents is real rather than theoretical: a naive codepoint
    clip that lands between U+26A0 and U+FE0E drops the selector and ships the EMOJI form of the
    glyph, which criterion A5 forbids. Measured 2026-09-19 against `render_stream._one_line`, which
    does exactly that at a boundary.

    THE RULE: a zero-width code point is never separated from the base character it follows. Because
    a zero-width code point costs no column, it is simply carried along with its base, so the
    boundary can only ever fall BEFORE a base character and never inside a grapheme cluster.

    ANSI escapes cost no columns and are preserved. When truncation actually occurs and the kept
    text opened a style it no longer closes, a reset is appended so the truncation cannot leak
    styling into the rest of the line; ``ellipsis`` is then appended UNSTYLED, because a marker that
    inherited the truncated cell's lifecycle color would be a color with no referent.
    """

    if limit <= 0:
        return ""
    budget = limit - visible_width(ellipsis)
    if budget < 0:
        return ""

    kept: List[str] = []
    pending: List[str] = []
    used = 0
    truncated = False
    style_open = False

    def _flush() -> None:
        nonlocal style_open
        for escape in pending:
            kept.append(escape)
            style_open = escape != _RESET
        pending.clear()

    for is_escape, token in _tokenize_ansi(text):
        if is_escape:
            # HELD BACK until a visible or zero-width code point actually follows it. An escape
            # flushed eagerly and then cut off by the budget would leave an empty `...m...m` pair
            # styling nothing, which is valid but is noise in a snapshot and in a `repr` diff.
            pending.append(token)
            continue
        if is_zero_width(token):
            # Costs no column. A zero-width mark rides along with the base already kept, which is
            # precisely what keeps a variation selector attached.
            _flush()
            kept.append(token)
            continue
        if used + 1 > budget:
            truncated = True
            break
        _flush()
        kept.append(token)
        used += 1

    if not truncated:
        return text

    out = "".join(kept)
    if style_open:
        out += _RESET
    return out + ellipsis


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
# Labels that `Term.status()` actually emits, which is what the padding exists to align.
# MEASURED 2026-09-12 across every `term.status("...")` call site: fail (55), info (44), ok (31),
# skip (21), warn (19), ignored (1). `NOT-INSTALLED` and the other currency words are NEVER passed
# to `status()`; they render through `_status_badge_256` in the `aw list`/`aw doctor` currency
# tables, which do their own layout. Padding every line to 13 therefore bought alignment with a
# label that never appears on these lines and cost 6 columns of terminal width on all 171 of them.
_STATUS_LINE_LABELS = (
    "ok",
    "info",
    "skip",
    "warn",
    "fail",
    "failed",
    "error",
    "ignored",
)
_STATUS_WIDTH = max(len(_STATUS_STYLE[k][0]) for k in _STATUS_LINE_LABELS)


#: Values of `FORCE_COLOR` that mean "do NOT force", i.e. the user wrote the variable but wrote a
#: falsey value in it. Compared case-insensitively against the stripped value.
#:
#: WHY THE VALUE IS INTERPRETED RATHER THAN MERELY TESTED FOR PRESENCE (maintainer ruling,
#: 2026-09-19; plan `z8ddk0`). `FORCE_COLOR=0` is common in CI configuration and plainly means "do
#: not force color". Reading it by TRUTHINESS in Python makes the string `"0"` true, so the value a
#: user writes to mean "off" FORCED COLOR ON, even into a pipe. That is the one behavior here that is
#: the exact opposite of what the user asked for, so it is the reading that changed.
#:
#: `NO_COLOR`, by contrast, stays PRESENCE-ONLY and interprets nothing: that is the published
#: no-color.org convention ("when present, regardless of its value"), and a repo-local
#: reinterpretation of an external accessibility convention would be worse than the inconsistency.
_FORCE_COLOR_FALSEY = frozenset({"", "0", "false", "no", "off"})


def _force_color_is_forcing() -> bool:
    """Is `FORCE_COLOR` set to a value that genuinely FORCES color on?

    THE SINGLE FORCING PREDICATE, and the reason it exists as a named helper rather than as an
    inline test is that `should_color` must consult `FORCE_COLOR` TWICE: once to decide whether it
    cancels `NO_COLOR`, and once to decide whether it forces color past TTY detection. Those two
    readings were INDEPENDENT before plan `z8ddk0` (presence at one site, truthiness at the other),
    which is what let a falsey `FORCE_COLOR` both fail to force AND still cancel `NO_COLOR`.

    MEASURED AT EXECUTION 2026-09-19 (that plan's F-05): correcting only the forcing site leaves the
    cancelling site a presence test, and SIX of the twelve `NO_COLOR`-set cells then colorize on a
    TTY - every cell where `NO_COLOR` is set AND `FORCE_COLOR` is present-but-falsey, including
    `NO_COLOR=1 FORCE_COLOR=0`. (The plan predicted twelve; the other six have `FORCE_COLOR` UNSET,
    where the naive presence test is still correct and the cell stays plain. The defect is real and
    the count is six, so it is recorded as six.) That silently voids the accessibility convention for
    any user who sets both, which is strictly worse than the defect being fixed. Routing BOTH
    readings through one predicate makes them move together by construction; a second independent
    falsey check at each site would re-create the very split this closes.
    """

    value = os.environ.get("FORCE_COLOR")
    if value is None:
        return False
    return value.strip().lower() not in _FORCE_COLOR_FALSEY


#: The PROCESS-WIDE color-flag override, set once per CLI invocation from the parsed
#: ``--color`` / ``--no-color`` pair and consulted by :func:`should_color` when no explicit
#: ``override=`` argument is supplied.
#:
#: WHY A PROCESS-WIDE VALUE RATHER THAN THREADING AN ARGUMENT THROUGH EVERY CALL SITE: the
#: package constructs ``Term`` and calls ``should_color`` from hundreds of places, most of
#: which never see the parsed namespace (measured: 40+ ``Term(color=False if
#: getattr(args, "no_color", False) else None)`` call sites alone). Threading a parameter to
#: all of them is the change that gets half-applied, leaving ``--color`` silently inert on
#: whichever renderer was missed - which is the exact per-command inconsistency this work
#: exists to remove.
#:
#: WHY NOT ``os.environ``, which would be the obvious alternative: this package spawns nested
#: ``aw`` invocations (both IPD runners, ``aw ipd finalize``, the commit helper), and an
#: environment variable is INHERITED. A presentation choice about this terminal would restyle
#: a child process's output too. A module-level value cannot leak across a process boundary.
#:
#: SET UNCONDITIONALLY, INCLUDING TO ``None``, once per ``cli._dispatch`` call, so an
#: invocation that passes no flag RESETS it rather than inheriting a previous invocation's
#: value. That is what keeps repeated in-process CLI calls (i.e. the test suite) independent.
_COLOR_OVERRIDE: Optional[bool] = None


def set_color_override(value: Optional[bool]) -> None:
    """Set the process-wide ``--color``/``--no-color`` override (``None`` clears it)."""

    global _COLOR_OVERRIDE
    _COLOR_OVERRIDE = None if value is None else bool(value)


def get_color_override() -> Optional[bool]:
    """Return the process-wide color-flag override set by :func:`set_color_override`."""

    return _COLOR_OVERRIDE


def should_color(
    stream: Optional[TextIO] = None, *, override: Optional[bool] = None
) -> bool:
    """Decide whether to emit ANSI color for ``stream`` (default stdout).

    THE SINGLE ORIGINATING DEFINITION of the color capability decision, package-wide (plan
    `z8ddk0`, for spec `uonrjg` R9.3a.2). `runner_shared.should_color` is a sanctioned one-line
    delegation to this function and `pwatch` calls it directly; both previously carried independent
    implementations that DISAGREED with this one, measured 2026-09-19, so a caller must reach this
    body rather than reimplement it. `tests/test_term.py::OneOriginatingDefinitionTests` fails if a
    second ORIGINATING definition appears anywhere in the package.

    Precedence: FLAG beats ENV beats DETECTION. Highest first:

    1. ``override`` (the ``--color`` / ``--no-color`` flag layer): ``True`` forces color on,
       ``False`` forces it off, and ``None`` falls back to the process-wide override set by
       :func:`set_color_override` (also ``None`` when no flag was passed).
    2. `NO_COLOR` PRESENT (any value, empty included) disables color, unless `FORCE_COLOR` is set
       to a genuinely FORCING value (see :func:`_force_color_is_forcing`).
    3. A forcing `FORCE_COLOR` enables color, overriding TTY detection (so a pipe gets color).
    4. `TERM` of `dumb` or empty/absent disables color.
    5. Otherwise color is on only for a real TTY.

    A falsey `FORCE_COLOR` (`0`/`false`/`no`/`off`/empty) is NOT an instruction to suppress: it
    means "do not force", so it falls through to ordinary detection. Suppressing is `NO_COLOR`'s
    job.

    ``override`` EXISTS SO A FLAG NEVER HAS TO MUTATE ``os.environ``. Setting ``FORCE_COLOR``
    or ``NO_COLOR`` from a flag handler would be inherited by every subprocess this package
    spawns (the two IPD runners launch nested ``aw`` invocations), so a presentation choice
    about THIS terminal would silently restyle a child's output too. The override is passed
    as an argument and therefore cannot leak.

    THE TWO LAYERS ARE COMPLEMENTARY, NOT RIVALS, and that is why this merge keeps both: the
    flag layer (plan `yaxr4i`) sits ABOVE the environment layer and answers "did the operator
    say so on this command line", while the environment layer (plan `z8ddk0`) decides what the
    environment means once no flag was given. Each was authored against a base lacking the
    other, so the composition was performed at salvage-integration time on 2026-09-19 rather
    than by either agent. The flag check must stay FIRST (an explicit instruction outranks
    inference) and both `FORCE_COLOR` readings must stay routed through the one forcing
    predicate (that shared routing is the property `z8ddk0` exists to establish).

    The full precedence table is published in ``docs/cli-output-contract.md`` section 1.1 and
    pinned by ``tests/test_term.py``.
    """

    stream = stream or sys.stdout

    # The FLAG layer, above everything: an explicit --color/--no-color is the operator's
    # direct instruction and beats both env detection and TTY detection. An explicit argument
    # wins over the process-wide value so a caller can always decide locally.
    effective = override if override is not None else _COLOR_OVERRIDE
    if effective is not None:
        return bool(effective)

    # NO_COLOR: any value (even empty) disables, UNLESS FORCE_COLOR is genuinely FORCING.
    # The forcing test is the shared predicate, NOT a bare presence check: a presence check here
    # is exactly the half-fix `_force_color_is_forcing` records as colorizing six NO_COLOR cells.
    if "NO_COLOR" in os.environ and not _force_color_is_forcing():
        return False
    # FORCE_COLOR: a forcing value beats TTY detection. A falsey value falls through.
    if _force_color_is_forcing():
        return True

    term = os.environ.get("TERM", "")
    if term == "dumb" or term == "":
        return False

    isatty = getattr(stream, "isatty", None)
    try:
        return bool(isatty and isatty())
    except Exception:
        return False


def color_override(args: Any = None) -> Optional[bool]:
    """Read the ``--color`` / ``--no-color`` pair off a parsed namespace.

    Returns ``True`` for ``--color``, ``False`` for ``--no-color``, and ``None`` when neither
    was passed (the "fall through to env and detection" case).

    THE ONE READER OF THAT FLAG PAIR, so the flag layer cannot be interpreted differently at
    different call sites. Passing both flags is refused STRUCTURALLY by argparse's mutually
    exclusive group in ``cli._build_parser``, so this function never has to arbitrate a
    conflict; if a caller hand-builds a namespace carrying both, ``--no-color`` wins here,
    which is the safe direction (never invent escapes the caller may not be able to render).
    """

    if args is None:
        return None
    if getattr(args, "no_color", False):
        return False
    if getattr(args, "color", False):
        return True
    return None


# ======================================================================================
# Color DEPTH: the 256 -> 16 -> none ladder (spec `uonrjg` R9.3a.1, R9.3a.2)
# ======================================================================================

#: The three rungs of the DECISIONS D42 ladder, as named constants so no caller spells a tier
#: as a bare literal. ``DEPTH_NONE`` is a tier like the others rather than a separate "color is
#: off" concept: R9.3a.1 makes "plain text with the glyph and word intact" the BOTTOM RUNG of one
#: ladder, so a renderer asks one question ("which tier?") instead of two.
DEPTH_NONE = "none"
DEPTH_16 = "16"
DEPTH_256 = "256"

#: The tiers a user may PIN, in ladder order, and the set an invalid value is refused against
#: (R9.3a.4, criterion A12c: the refusal MUST name the accepted set). Held as a tuple rather than
#: a set so the message lists them in a stable, meaningful order instead of a hash order.
COLOR_DEPTHS: Tuple[str, ...] = (DEPTH_NONE, DEPTH_16, DEPTH_256)

#: The DEFAULT tier when nothing is pinned and detection is inconclusive but color is on.
#:
#: 256 AND NOT THE MOST CONSERVATIVE RUNG, which is the entire point of D42 and is stated in
#: R9.3a.2 ("the default is 256 rather than the most conservative rung... the conservative default
#: is what produced a decade of monochrome tooling"). Virtually every terminal of the last two
#: decades renders SGR 38;5;N, so defaulting to 16 would degrade the common case to protect a rare
#: one that `COLORTERM`/`TERM` detection and the depth pin both already cover.
DEFAULT_COLOR_DEPTH = DEPTH_256

#: ``TERM`` substrings that prove only 16-color capability. Matched as substrings because the
#: terminfo namespace is open-ended (`xterm`, `screen`, `rxvt`, `tmux`, each with many suffixes),
#: so an exhaustive equality list would silently mis-tier the next terminal to appear.
_TERM_16_MARKERS: Tuple[str, ...] = (
    "16color",
    "-color",
    "ansi",
    "linux",
    "vt100",
    "vt220",
)

#: ``TERM`` substrings that prove 256-color (or better) capability.
_TERM_256_MARKERS: Tuple[str, ...] = (
    "256color",
    "direct",
    "truecolor",
    "kitty",
    "alacritty",
)


def _depth_from_environment() -> Optional[str]:
    """Detect the tier from ``COLORTERM``/``TERM``, or ``None`` when detection is inconclusive.

    THE DETECTION RUNG of R9.3a.2, and it deliberately returns ``None`` rather than guessing a
    tier when it cannot tell. That distinction is load-bearing: ``None`` means "fall through to
    the default of 256", while returning 16 on an unrecognized ``TERM`` would make every unknown
    terminal a 16-color terminal, which is the conservative-default failure D42 rejects.

    ``COLORTERM`` IS CONSULTED FIRST because it is the variable that exists specifically to
    ANSWER this question: a terminal setting `truecolor`/`24bit` is asserting capability beyond
    256, which this ladder tops out at, so it resolves 256 rather than a fourth rung (D42 names
    three rungs and this module adds none).
    """

    colorterm = os.environ.get("COLORTERM", "").strip().lower()
    if colorterm in ("truecolor", "24bit", "24bits"):
        return DEPTH_256
    if colorterm:
        # Any other non-empty COLORTERM asserts color capability without naming a depth. It is
        # evidence of color, not of 256, so it is NOT treated as conclusive here; TERM decides.
        pass

    term = os.environ.get("TERM", "").strip().lower()
    if not term:
        return None
    for marker in _TERM_256_MARKERS:
        if marker in term:
            return DEPTH_256
    for marker in _TERM_16_MARKERS:
        if marker in term:
            return DEPTH_16
    return None


def _configured_color_depth() -> Optional[str]:
    """Read the user's PINNED tier from the ``aw config`` store, or ``None`` when unset.

    IMPORTED LAZILY AND FAILING OPEN, both deliberately. ``config`` reads the user's config file,
    so importing it at module scope would put filesystem I/O on the import path of the single
    module every renderer in the package imports, and would risk an import cycle. And a
    presentation decision must never be the thing that crashes a command: an unreadable or
    malformed config file yields ``None`` here, which falls through to detection, rather than
    raising out of a styling call.

    An INVALID pinned value is likewise ignored here rather than raised, because the REFUSAL
    belongs at the setter where the user can still fix their typo (``config.set_config_value``,
    criterion A12c). A value that reached the file by hand-editing past that refusal must not
    make every subsequent command fail.
    """

    try:
        from . import config as _config

        value = _config.get_color_depth()
    except Exception:
        return None
    return value if value in COLOR_DEPTHS else None


def resolve_color_depth(
    stream: Optional[TextIO] = None, *, override: Optional[bool] = None
) -> str:
    """Resolve the ONE color tier in force for ``stream``: ``'256'``, ``'16'`` or ``'none'``.

    THE SINGLE DEFINITION of color DEPTH, package-wide (spec `uonrjg` R9.3a.2: "the depth is a
    resolved value, not a guess at each call site... it MUST have exactly one definition"). A
    renderer asks this once and selects a palette; it must never re-derive a tier from
    ``COLORTERM``, ``TERM`` or a config read of its own.

    Precedence, highest first, exactly as R9.3a.2 specifies it:

    1. COLOR IS OFF ENTIRELY -> ``'none'``. Delegated WHOLESALE to :func:`should_color`, which
       already owns the ``--color``/``--no-color`` flag layer, ``NO_COLOR``, ``FORCE_COLOR``,
       ``TERM=dumb`` and the TTY test. See the note below on why this rung delegates rather than
       re-implements.
    2. AN EXPLICIT USER DEPTH PIN -> that tier (``aw config`` key ``color_depth``).
    3. DETECTED CAPABILITY via ``COLORTERM``/``TERM`` -> that tier.
    4. The DEFAULT -> ``'256'``.

    ``NO_COLOR`` OUTRANKS A PINNED DEPTH, which R9.3a.2 singles out as the rung "a well-meaning
    implementation is most likely to get backwards" and criterion A12a requires be asserted on its
    own. It holds STRUCTURALLY here rather than by a written-out rule: rung 1 returns before rung 2
    is ever consulted, so a pin cannot be reached when color is off. The reason is that `NO_COLOR`
    is an accessibility convention while a pinned depth is a preference, and a preference may not
    defeat a convention.

    WHY RUNG 1 DELEGATES TO ``should_color`` INSTEAD OF RE-READING THE ENVIRONMENT (this is the
    one design decision in this function and it was ruled, not chosen). R9.3a.2 words its top rung
    as ``NO_COLOR``/``--no-color``/``TERM=dumb``/non-TTY, which reads like four env/stream tests to
    perform here. Performing them here would be WRONG twice over. FIRST, it would create a SECOND
    originating definition of the color decision, which is the exact defect plan `z8ddk0` closed
    when it unified three divergent ``should_color`` implementations, and which
    ``tests/test_term.py::OneOriginatingDefinitionTests`` now guards. SECOND, this function CANNOT
    see ``--no-color``: the flag never reaches ``os.environ`` (by design, because nested ``aw``
    processes inherit the environment and would be silently restyled), so it arrives only as the
    ``override=`` argument or through ``term.set_color_override``. Delegating gets all four inputs
    right for free, and keeps the ``FORCE_COLOR`` escape hatch that the maintainer's 2026-09-19
    ruling (plan `pow5sj` OQ-02, READING A) preserved: ``FORCE_COLOR`` still overrides
    ``NO_COLOR``, and R9.3a.2's "unconditional" is unconditional with respect to the DEPTH PIN
    only.

    ``override`` is forwarded to :func:`should_color` unchanged and carries the same meaning, so a
    caller that already holds a flag decision passes it here rather than mutating the environment.
    """

    if not should_color(stream, override=override):
        return DEPTH_NONE

    pinned = _configured_color_depth()
    if pinned is not None:
        return pinned

    detected = _depth_from_environment()
    if detected is not None:
        return detected

    return DEFAULT_COLOR_DEPTH


# ======================================================================================
# The AUTHORED 16-color tier (spec `uonrjg` R9.3a.3)
# ======================================================================================

#: The SGR foreground codes of the sixteen named colors this tier is allowed to use. Written as
#: the raw codes rather than reusing ``_CODES`` because that map is the small decoration palette
#: (it carries `bold` and omits magenta/white), while this tier needs the color axis alone.
_SGR_RED = 31
_SGR_GREEN = 32
_SGR_YELLOW = 33
_SGR_BLUE = 34
_SGR_MAGENTA = 35
_SGR_CYAN = 36
_SGR_WHITE = 37
_SGR_BRIGHT_BLACK = 90  # the one neutral; see the gray collapse below
_SGR_BRIGHT_GREEN = 92
_SGR_BRIGHT_YELLOW = 93
_SGR_BRIGHT_MAGENTA = 95
_SGR_BRIGHT_CYAN = 96

#: THE AUTHORED 16-COLOR PALETTE for the twenty semantic lifecycle stages (R9.3a.3).
#:
#: AUTHORED, NOT DERIVED, and that is a hard requirement rather than a stylistic preference.
#: Section 5's 256 table uses 11 distinct indices and this tier has far fewer usable colors, so a
#: mechanical nearest-neighbour mapping of those indices would merge stages that MUST stay
#: distinguishable. The risk is concrete and measured, not theoretical: `blocked` is 208 and
#: `waiting-input` is 214 (an adjacent orange pair), `blocked` is 208 and `failed` is 196 (both
#: warm reds), and `ready` is 45 while `done` is 46 (ADJACENT BY INDEX and completely opposite in
#: meaning - one says "start this", the other says "this is finished"). Every one of those pairs
#: is what a nearest-neighbour reduction would collapse first.
#:
#: THE THREE SEPARATIONS THIS TABLE MUST PRESERVE, which are the ones Section 5 exists to protect
#: and which criterion A12b asserts: `ready` is not `done`; `blocked` is not `failed`;
#: `waiting-input` is not `blocked`. They are held here by giving each member of each pair a
#: different named color, and `tests/test_term.py` asserts all three rather than trusting review.
#:
#: THE TWO COLLAPSES THAT ARE EXPECTED AND ACCEPTABLE, both named by R9.3a.3, and acceptable for
#: the SAME stated reason in each case: the glyph and the native word still separate the states, so
#: no information is lost, only redundancy (R9.3a.5).
#:   1. THE SIX ACTIVE STAGES -> ONE YELLOW. The five subtypes (`reviewing`, `executing`,
#:      `verifying`, `integrating`, `recovering`) plus generic `active` already share ONE index at
#:      256 (all six are 220), so this collapse is FREE: the tier loses nothing that 256 had.
#:      Their glyphs differ (`◎ ▶ ◆ ⇄ ↩︎ ●`), which is the design, not a compromise.
#:   2. THE SIX GRAY-FAMILY STAGES -> ONE NEUTRAL. `parked`, `superseded`, `abandoned`, `unknown`,
#:      `none` and `formative`. NOTE THE COUNT: R9.3a.3's prose says "the four grays" and then lists
#:      SIX names; the LIST is right and the WORD is wrong, confirmed by measuring the stage table
#:      (five stages sit at 244 and `formative` at 245, so six collapse). They differ by at most one
#:      index at 256, so this tier loses almost nothing.
#:
#: KEYED BY SEMANTIC STAGE, never by a native status word, so this table cannot become a second
#: lifecycle vocabulary. `lifecycle_style` owns the vocabulary and the native-status mappings; this
#: is purely the 16-color rendering of the stages that module defines, and
#: ``validate_16_color_palette`` refuses at import if the two ever disagree.
STAGE_COLOR_16: Dict[str, int] = {
    # --- The formative / queued / ready progression -----------------------------------
    "formative": _SGR_BRIGHT_BLACK,  # gray collapse member (245 at 256)
    "review-queued": _SGR_BLUE,  # 39 at 256, the cool "awaiting review" color
    # 135 at 256 is a purple, so bright magenta is its 16-color kin. NOT plain magenta, which
    # `blocked` takes below: these two stages are 135 and 208 at 256 (a purple and an orange, nowhere
    # near each other), so collapsing them into one color would be an UNNAMED merge, and R9.3a.3
    # names every collapse it considers acceptable. `test_the_palette_merges_no_unnamed_pair` refuses
    # any such merge, which is what caught this one.
    "authority-queued": _SGR_BRIGHT_MAGENTA,
    # SEPARATION 1 of 3: `ready` is CYAN and `done` is GREEN. At 256 these are 45 and 46, adjacent
    # by index, so this is the separation a derived table would lose first and the one whose loss
    # would hurt most (a board would stop distinguishing "start this" from "finished").
    "ready": _SGR_BRIGHT_CYAN,
    # --- The six active stages: ONE yellow, by design (collapse 1) ---------------------
    "reviewing": _SGR_YELLOW,
    "executing": _SGR_YELLOW,
    "verifying": _SGR_YELLOW,
    "integrating": _SGR_YELLOW,
    "recovering": _SGR_YELLOW,
    "active": _SGR_YELLOW,
    # --- The obstruction band, held apart in three colors ------------------------------
    # SEPARATION 3 of 3: `waiting-input` is BRIGHT YELLOW and `blocked` is MAGENTA. At 256 they are
    # 214 and 208, the adjacent orange pair R9.3a.4 names as the concrete accessibility hazard, so
    # they are pushed to different HUES here rather than two shades of one. Note `waiting-input`
    # differs from the active yellow above by BRIGHTNESS only; that is acceptable because waiting
    # for input IS a non-failure, non-terminal state adjacent to activity, and its `…` glyph and
    # its word both separate it.
    "waiting-input": _SGR_BRIGHT_YELLOW,
    # SEPARATION 2 of 3: `blocked` is MAGENTA and `failed` is RED. At 256 they are 208 and 196,
    # both warm, which is exactly the pair a nearest-neighbour reduction merges. Magenta is chosen
    # over "some other red" deliberately: only a different hue survives a 16-color terminal's
    # limited palette AND remains distinguishable under the most common color-vision deficiencies.
    "blocked": _SGR_MAGENTA,
    "failed": _SGR_RED,
    # --- Terminal success and the standing state ---------------------------------------
    "done": _SGR_BRIGHT_GREEN,
    "reusable": _SGR_CYAN,  # 81 at 256; a non-bright cyan keeps it apart from `ready`
    # --- The six gray-family stages: ONE neutral, by design (collapse 2) ---------------
    "parked": _SGR_BRIGHT_BLACK,
    "superseded": _SGR_BRIGHT_BLACK,
    "abandoned": _SGR_BRIGHT_BLACK,
    "unknown": _SGR_BRIGHT_BLACK,
    "none": _SGR_BRIGHT_BLACK,
}

#: The separations R9.3a.3 requires this tier to preserve, as DATA so the accessibility test asserts
#: the rule rather than re-listing it, and so a future edit to the palette above is checked against
#: the requirement instead of against a reviewer's memory.
REQUIRED_16_COLOR_SEPARATIONS: Tuple[Tuple[str, str], ...] = (
    ("ready", "done"),
    ("blocked", "failed"),
    ("waiting-input", "blocked"),
)

#: The two collapses R9.3a.3 declares EXPECTED, also as data. Pinning them is what stops a later
#: change quietly re-expanding these groups into colors a 16-color terminal cannot show.
EXPECTED_16_COLOR_COLLAPSES: Tuple[Tuple[str, ...], ...] = (
    ("reviewing", "executing", "verifying", "integrating", "recovering", "active"),
    ("parked", "superseded", "abandoned", "unknown", "none", "formative"),
)


def validate_16_color_palette() -> None:
    """Raise unless the authored 16-color table conforms to R9.3a.3. Called at import.

    FAILS CLOSED AT IMPORT, for the same reason ``lifecycle_style.validate`` does: a palette defect
    must be a loud failure at the first import rather than a wrong color discovered later in a view,
    and the two most likely defects here (a stage added upstream with no 16-color entry, and a
    well-meaning edit that merges a required separation) are both invisible to the eye.

    THE COVERAGE CHECK READS ``lifecycle_style`` RATHER THAN A LITERAL COUNT, deliberately. A
    hard-coded "there must be 20 entries" is itself a second table that rots the moment the stage
    vocabulary changes; asserting COVERAGE of the real vocabulary cannot rot. It also means a stage
    added to ``lifecycle_style`` without a color here fails immediately and by name.
    """

    from .lifecycle_style import ALL_STAGES

    missing = sorted(ALL_STAGES - set(STAGE_COLOR_16))
    if missing:
        raise ValueError(
            "the authored 16-color palette covers no color for semantic stage(s): {0}; "
            "R9.3a.3 requires an explicit entry for every stage".format(
                ", ".join(missing)
            )
        )
    unknown = sorted(set(STAGE_COLOR_16) - ALL_STAGES)
    if unknown:
        raise ValueError(
            "the authored 16-color palette colors non-stage key(s): {0}; this table is keyed by "
            "SEMANTIC STAGE and must never become a second lifecycle vocabulary".format(
                ", ".join(unknown)
            )
        )

    for left, right in REQUIRED_16_COLOR_SEPARATIONS:
        if STAGE_COLOR_16[left] == STAGE_COLOR_16[right]:
            raise ValueError(
                "16-color palette merges {0!r} and {1!r} (both SGR {2}); R9.3a.3 requires this "
                "separation survive the tier".format(left, right, STAGE_COLOR_16[left])
            )

    for group in EXPECTED_16_COLOR_COLLAPSES:
        codes = {STAGE_COLOR_16[stage] for stage in group}
        if len(codes) != 1:
            raise ValueError(
                "16-color palette splits the expected collapse {0} across SGR codes {1}; "
                "R9.3a.3 declares this group renders as ONE color".format(
                    ", ".join(group), sorted(codes)
                )
            )

    # EVERY MERGE MUST BE A NAMED ONE. R9.3a.3 lists the collapses it considers acceptable, which
    # means a merge it does NOT list is an unreviewed loss of a distinction, not a free one. This
    # check is what makes the requirement total rather than spot-checked, and it earned its place
    # immediately: it caught `authority-queued` (135, a purple) sharing plain magenta with `blocked`
    # (208, an orange) in this table's first draft, a pair no requirement permits merging and one
    # that the three REQUIRED_16_COLOR_SEPARATIONS do not cover.
    _collapse_members = {
        stage for group in EXPECTED_16_COLOR_COLLAPSES for stage in group
    }
    _by_code: Dict[int, List[str]] = {}
    for stage, code in STAGE_COLOR_16.items():
        _by_code.setdefault(code, []).append(stage)
    for code, stages in sorted(_by_code.items()):
        outside = sorted(stage for stage in stages if stage not in _collapse_members)
        if len(outside) > 1:
            raise ValueError(
                "16-color palette merges {0} onto SGR {1}, and R9.3a.3 names no collapse covering "
                "them; either give them distinct colors or declare the collapse "
                "explicitly".format(", ".join(outside), code)
            )


validate_16_color_palette()


def color_16_for_stage(stage: str) -> int:
    """Return the authored 16-color SGR foreground code for a semantic ``stage``.

    Raises ``KeyError`` on an undefined stage rather than returning a neutral, because
    ``validate_16_color_palette`` guarantees total coverage of the real vocabulary at import: a
    miss here therefore means the caller invented a stage name, which a silent gray would hide.
    """

    return STAGE_COLOR_16[stage]


STATUS_COLOR_256 = {
    # Lifecycle & status states
    "active": 39,
    "todo": 44,  # teal (research hot state; rstodo p3o9je, renamed from `intake`)
    "intake": 44,  # teal - legacy alias kept so a raw pre-migration `intake` label keeps its color
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
    "planned": 40,
    "shipped": 46,
    "reference": 244,
    "archived": 240,
    "blocked": 203,
    "deferred": 208,  # orange-red
    "done": 244,
    "parked": 244,
    "superseded": 240,
    "not-executed": 240,
    # Extended roles (awcliux Order 02 E-01)
    "success": 46,
    "conforms": 46,
    "conforming": 46,
    "quarantined": 214,
    "legacy": 244,
    "ok": 46,
    "up to date": 46,
    "wrote": 46,
    "updated": 46,
    "current": 46,
    "unchanged": 245,
    "info": 39,
    "warning": 226,
    "warn": 226,
    "advisory": 214,
    "action": 214,
    "preview": 214,
    "running": 51,
    "queued": 245,
    "substantially-complete": 46,
    "complete": 46,
    "partial": 214,
    "interrupted": 214,
    "dependency-blocked": 208,
    "failed-safely": 196,
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


# ======================================================================================
# The lifecycle rendering boundary (spec `uonrjg` R10.2, Sections 9.1, 9.2, 9.4)
# ======================================================================================
#
# RESOLUTION AND RENDERING ARE SEPARATE, which is the whole requirement R10.2 states and the one
# property the previous lifecycle path did not have: `Term.status_256` resolved a color from a table
# and emitted an escape on the NEXT LINE, so no test could check the resolution without also
# checking the ANSI. Here :func:`resolve_lifecycle` returns immutable DATA and emits nothing, and
# only the `Term` methods below produce a byte of styling.
#
# NO LIFECYCLE STAGE TABLE LIVES IN THIS MODULE. The vocabulary, the glyphs, the ASCII fallbacks,
# the 256 indices and the bold flags are all `lifecycle_style`'s (R10.1), and the 16-color tier
# above is keyed by the stages that module defines. A second table here is exactly the defect this
# spec exists to remove.


def resolve_lifecycle(
    artifact_type: str,
    native_status: Optional[str] = None,
    *,
    activity: Optional[str] = None,
    integrity: lifecycle_style.IntegrityInput = None,
    obstruction: Optional[str] = None,
    condition: Optional[str] = None,
) -> lifecycle_style.Resolved:
    """Resolve one lifecycle presentation, returning ANSI-FREE data (R10.2, spec Section 8).

    A THIN, DELIBERATE DELEGATION to :func:`lifecycle_style.resolve`, and the thinness is the point:
    this is the name a renderer reaches for, so it exists to give consumers ONE import
    (``term``) rather than two, while the semantics stay owned by the one canonical module. It adds
    no policy, consults no terminal, and reads no environment, so a test can assert resolution
    without a stream, a capability or an escape sequence anywhere in sight.

    ``artifact_type`` is the record FAMILY (``"plans"``, ``"specs"``, ``"backlog"``, ...), named as
    the spec names the parameter. An unknown family raises, because a silently-defaulted family
    would render a plausible glyph for a status it never looked up.
    """

    return lifecycle_style.resolve(
        artifact_type,
        native_status,
        activity=activity,
        integrity=integrity,
        obstruction=obstruction,
        condition=condition,
    )


def lifecycle_word(resolved: lifecycle_style.Resolved) -> str:
    """Return the WORD that must accompany the glyph (Section 11 item 1, R9.3a.5).

    Precedence: the caller's own native status spelling, then the live activity, then the semantic
    stage as a last resort. The native status comes FIRST because Section 0 makes it authoritative,
    and it is echoed in the caller's ORIGINAL case for the same reason.

    NEVER RETURNS EMPTY, because "glyph and color are redundant cues; either can be removed without
    losing the state" (Section 11 item 2) is only true if a word is always there to carry it.
    """

    if resolved.native_status:
        return str(resolved.native_status)
    if resolved.activity:
        return str(resolved.activity)
    return resolved.stage


class Term:
    """A small styling helper bound to a stream's color decision."""

    def __init__(
        self,
        stream: Optional[TextIO] = None,
        color: Optional[bool] = None,
        unicode: Optional[bool] = None,
        depth: Optional[str] = None,
    ):
        self.stream = stream or sys.stdout
        self.color = should_color(self.stream) if color is None else color
        self.unicode = should_unicode(self.stream) if unicode is None else unicode
        self._depth = depth if depth in COLOR_DEPTHS else None

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

    # ----------------------------------------------------------------------------------
    # Lifecycle RENDERING (spec `uonrjg` R10.2, Sections 9.1 / 9.2 / 9.4)
    # ----------------------------------------------------------------------------------

    def lifecycle_depth(self) -> str:
        """Return the color TIER this Term renders lifecycle elements at.

        Asked ONCE per render rather than re-derived per element, which is R9.3a.2's requirement
        ("the depth is a resolved value, not a guess at each call site"). An explicitly constructed
        ``Term(color=False)`` resolves ``none`` without consulting the environment at all, so a test
        that pins color off cannot be perturbed by the machine it runs on.
        """

        if self._depth is not None:
            return self._depth
        if not self.color:
            return DEPTH_NONE
        depth = resolve_color_depth(self.stream)
        return DEPTH_16 if depth == DEPTH_16 else DEPTH_256

    def style_lifecycle_text(
        self, text: str, resolved: lifecycle_style.Resolved
    ) -> str:
        """Apply ``resolved``'s color and bold flag to ``text`` (R10.2, the third helper).

        THE ONE PLACE A LIFECYCLE ESCAPE IS EMITTED, so every lifecycle element that must share a
        color (Section 9.1: glyph, id6 and status word) shares it by CONSTRUCTION rather than by
        three call sites agreeing. Returns ``text`` unchanged at the ``none`` tier, which is what
        keeps `NO_COLOR`, a pipe and `TERM=dumb` free of escapes (criterion A11).

        Both colored tiers are served here because the tier is a rendering decision and this is the
        rendering boundary: 256 uses ``lifecycle_style``'s index, 16 uses the authored
        :data:`STAGE_COLOR_16` palette. Neither table is defined in this method.
        """

        tier = self.lifecycle_depth()
        if tier == DEPTH_NONE or not text:
            return text
        style = resolved.style
        if tier == DEPTH_16:
            code = color_16_for_stage(resolved.stage)
            prefix = "1;" if style.bold else ""
            return f"\033[{prefix}{code}m{text}{_RESET}"
        n = max(0, min(255, int(style.color)))
        prefix = "1;" if style.bold else ""
        return f"\033[{prefix}38;5;{n}m{text}{_RESET}"

    def format_lifecycle_marker(
        self,
        resolved: lifecycle_style.Resolved,
        *,
        width: int = 0,
        style: bool = True,
    ) -> str:
        """Return the lifecycle GLYPH in this stream's tier, styled and optionally padded.

        The Unicode grapheme or the exact Section 5 ASCII fallback is chosen by ``self.unicode``,
        never by the semantic module: R10.2 assigns the capability decision to this boundary, which
        is why ``lifecycle_style.glyph_for`` takes the choice as an argument instead of sniffing.

        ``width`` PADS BY VISIBLE COLUMNS, not by code points (Section 9.4 bullets 2 and 4). That
        distinction is the whole reason :func:`visible_width` exists: the two glyphs carrying U+FE0E
        are 2 code points and 1 column, so a `len()`-based pad leaves their column one short of
        every other row's. Measured before this landed, `status_256('⚠︎', width=4)` produced 3
        rendered columns while `status_256('◕', width=4)` produced 4.
        """

        glyph = lifecycle_style.glyph_for(resolved.stage, unicode=self.unicode)
        painted = self.style_lifecycle_text(glyph, resolved) if style else glyph
        pad = width - visible_width(glyph)
        if pad > 0:
            return painted + (" " * pad)
        return painted

    def format_lifecycle_compact(
        self,
        id6: str,
        resolved: lifecycle_style.Resolved,
        *,
        word: bool = False,
    ) -> str:
        """Return Section 9.2's compact ``GLYPH id6`` form, glyph and id6 styled TOGETHER.

        STYLED AS ONE RUN rather than as two adjacent escape pairs, because Section 9.2 says "with
        the glyph and id6 styled together" and because one run is what a terminal that mishandles a
        reset mid-line renders correctly. Pass ``word=True`` to append the native word when it fits,
        which the section invites ("If a status word fits, include it").
        """

        glyph = lifecycle_style.glyph_for(resolved.stage, unicode=self.unicode)
        marker = self.style_lifecycle_text(f"{glyph} {id6}", resolved)
        if word:
            return f"{marker} {self.style_lifecycle_text(lifecycle_word(resolved), resolved)}"
        return marker

    def format_lifecycle_row(
        self,
        resolved: lifecycle_style.Resolved,
        *,
        id6: str = "",
        artifact_type: str = "",
        title: str = "",
        path: str = "",
        type_width: int = 0,
        id6_width: int = 0,
        status_width: int = 0,
        marker_width: int = 0,
    ) -> str:
        """Render Section 9.1's full row: ONLY glyph, id6 and status word carry lifecycle color.

        THE THREE LIFECYCLE CELLS TAKE ONE COLOR AND ONE WEIGHT and the rest take NONE (criterion
        A10). That is enforced STRUCTURALLY rather than by convention, which is E-02's actual
        requirement: the three styled cells all route through :meth:`style_lifecycle_text` with the
        SAME ``resolved``, so they cannot diverge, and ``artifact_type``, ``title`` and ``path`` are
        emitted as plain text with NO parameter existing by which a caller could ask for them to be
        lifecycle-colored. Whole-row coloring is therefore unreachable through this API, not merely
        discouraged (Section 9.1: "Whole-row coloring is forbidden because it destroys hierarchy").

        The glyph is placed IMMEDIATELY BEFORE the id6 (or before the status word when no id6 is
        given), which Section 9.1 requires so the glyph's referent is unambiguous.

        Every column pads by VISIBLE columns (Section 9.4 bullet 4). No cell is measured with
        ``len()``.
        """

        cells: List[str] = []

        if artifact_type:
            cells.append(_pad_visible(artifact_type, type_width))

        cells.append(self.format_lifecycle_marker(resolved, width=marker_width))

        if id6:
            cells.append(
                _pad_visible(self.style_lifecycle_text(id6, resolved), id6_width)
            )

        word = lifecycle_word(resolved)
        cells.append(
            _pad_visible(self.style_lifecycle_text(word, resolved), status_width)
        )

        if title:
            cells.append(title)
        if path:
            cells.append(path)

        return "  ".join(cell for cell in cells if cell != "")

    def format_lifecycle_legend(
        self,
        *,
        stages: Optional[Sequence[str]] = None,
        both_forms: bool = True,
    ) -> str:
        """Render the Section 9.2 legend, GENERATED from ``lifecycle_style``'s table.

        GENERATED, NEVER A LITERAL, which is the property that makes it impossible for the legend to
        drift from the table it documents: it iterates :data:`lifecycle_style.STAGE_ORDER`, so a
        stage added upstream appears here with no edit, and a stage removed cannot linger. A
        hand-written legend shipped in this module is precisely the artifact a later drift guard
        would have to retrofit.

        ORDERED IN LIFECYCLE WORD ORDER, never by color name (Section 11 item 6), because
        ``STAGE_ORDER`` is derived from the spec Section 5 rows in spec order.

        WHERE the legend APPEARS is NOT this method's business and deliberately so: command help
        placement and the "show once per view with three or more stages" rule belong to the
        consumers, and this module holds no call counter or once-per-process latch. A latch would
        make output depend on invocation order and would be untestable in a shared-process suite.
        """

        names = tuple(stages) if stages is not None else lifecycle_style.STAGE_ORDER
        rows: List[str] = []
        for stage in names:
            style = lifecycle_style.style_for(stage)
            resolved = lifecycle_style.Resolved(
                stage=stage, style=style, family=lifecycle_style.FAMILY_PLANS
            )
            shown = style.unicode if self.unicode else style.ascii
            marker = self.style_lifecycle_text(shown, resolved)
            pad = " " * max(0, 2 - visible_width(shown))
            if both_forms and self.unicode:
                rows.append(f"{marker}{pad} {style.ascii}  {stage}")
            else:
                rows.append(f"{marker}{pad} {stage}")
        return "\n".join(rows)

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

    def format_empty_result(
        self,
        summary: Union[str, Dict[str, Any], Any] = "no matching items",
        *,
        filters: Optional[
            Union[Dict[str, Any], Sequence[Tuple[str, Any]], Sequence[str], str]
        ] = None,
        next_action: Optional[Union[str, Tuple[str, str], Any]] = None,
        status: str = "clean",
    ) -> str:
        """Format a unified empty-state UX result (highpbacklog0822 Order 04 E-01).

        Echoes an outcome line (e.g. `✓ CLEAN  <summary>`), the active filters/selectors
        if any, and a recommended next action, composed from existing primitives
        (`format_outcome`, `format_section`, `colorize`, `format_next_action`).
        """
        # Handle dict or object context passed as first positional arg
        if isinstance(summary, dict):
            ctx_dict = summary
            filters = ctx_dict.get("filters", filters)
            next_action = (
                ctx_dict.get("next_action") or ctx_dict.get("next") or next_action
            )
            status = ctx_dict.get("status", status)
            summary = ctx_dict.get("summary") or ctx_dict.get(
                "message", "no matching items"
            )
        elif hasattr(summary, "summary") and not isinstance(summary, str):
            ctx_obj = summary
            data = getattr(ctx_obj, "data", {}) or {}
            filters = data.get("filters", filters)
            next_actions = getattr(ctx_obj, "next_actions", []) or []
            if next_actions and next_action is None:
                next_action = next_actions[0]
            status = getattr(ctx_obj, "status", status)
            summary = getattr(ctx_obj, "summary", "no matching items")

        lines: List[str] = [self.format_outcome(status, str(summary))]

        # Active filters / selectors
        if filters:
            lines.append("")
            lines.append(self.format_section("Active filters:"))
            if isinstance(filters, dict):
                for k, v in filters.items():
                    if v is not None and v != "":
                        v_str = (
                            ", ".join(str(x) for x in v)
                            if isinstance(v, (list, tuple))
                            else str(v)
                        )
                        k_styled = (
                            self.colorize(f"{k}:", "bold") if self.color else f"{k}:"
                        )
                        lines.append(f"  {k_styled} {v_str}")
            elif isinstance(filters, (list, tuple)):
                for item in filters:
                    if isinstance(item, tuple) and len(item) == 2:
                        k, v = item
                        if v is not None and v != "":
                            v_str = (
                                ", ".join(str(x) for x in v)
                                if isinstance(v, (list, tuple))
                                else str(v)
                            )
                            k_styled = (
                                self.colorize(f"{k}:", "bold")
                                if self.color
                                else f"{k}:"
                            )
                            lines.append(f"  {k_styled} {v_str}")
                    elif item:
                        lines.append(f"  {item}")
            elif isinstance(filters, str):
                lines.append(f"  {filters}")

        # Suggested next action
        if next_action:
            lines.append("")
            if isinstance(next_action, str):
                lines.append(self.format_next_action(next_action))
            elif isinstance(next_action, tuple):
                cmd = next_action[0]
                desc = next_action[1] if len(next_action) > 1 else ""
                lines.append(self.format_next_action(cmd, desc))
            elif hasattr(next_action, "command"):
                lines.append(
                    self.format_next_action(
                        next_action.command,
                        getattr(next_action, "description", ""),
                    )
                )

        return "\n".join(lines)

    def empty_result(
        self,
        summary: Union[str, Dict[str, Any], Any] = "no matching items",
        *,
        filters: Optional[
            Union[Dict[str, Any], Sequence[Tuple[str, Any]], Sequence[str], str]
        ] = None,
        next_action: Optional[Union[str, Tuple[str, str], Any]] = None,
        status: str = "clean",
    ) -> None:
        """Print an empty-state result with active filters and next action."""
        self.line(
            self.format_empty_result(
                summary=summary,
                filters=filters,
                next_action=next_action,
                status=status,
            )
        )

    def format_step_cue(self, message: str) -> str:
        """Format a transient progress step-cue for stderr using severity_label('info')."""
        return f"{self.severity_label('info')} {message}"

    def step_cue(self, message: str, stream: Optional[TextIO] = None) -> None:
        """Emit a transient step-cue line to stderr (or specified stream)."""
        dest = stream if stream is not None else sys.stderr
        print(self.format_step_cue(message), file=dest)


def severity_label(kind: str, term: Optional[Term] = None) -> str:
    """Convenience helper to format a P14 bracketed severity label using ``term`` or a default Term."""
    t = term or Term()
    return t.severity_label(kind)


def yes_no_suffix(default: bool, *, term: Optional[Term] = None) -> str:
    """Render a yes/no prompt suffix with the DEFAULT letter emphasized: ``[Y/n]`` or ``[y/N]``.

    ONE renderer for every interactive yes/no prompt, so the emphasis cannot drift between the
    setup flow and the runner-profile wizard (they previously built the suffix independently).

    THE CASE IS THE CONTRACT AND THE BOLD IS A REDUNDANT CUE, in the same relationship as a status
    LABEL and its color (see `_STATUS_STYLE`): the capital letter states which answer Enter takes,
    and bold merely makes it easier to see. So a monochrome terminal, a pipe, `NO_COLOR`, and a
    screen reader all keep the full meaning, and no caller has to special-case them.

    Note the ``default`` argument decides only which letter is capitalized; it does NOT decide what
    an empty answer does. That remains the caller's job, and the two must agree.
    """

    t = term or Term()
    if default:
        return "[" + t.colorize("Y", "bold") + "/n]"
    return "[y/" + t.colorize("N", "bold") + "]"

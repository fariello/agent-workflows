#!/usr/bin/env python3
"""Shared interactive streaming renderer for IPD-runner drivers.

This module holds the normalized progress/streaming render layer extracted from
``oc_runipd`` so any consumer (the OpenCode driver, the Antigravity driver, or a
future host adapter) can share a single definition instead of duplicating it:

- :data:`_ANSI_RESET`/:data:`_ANSI_CODES`/:data:`_ANSI_STRIP_RE`/:data:`_STATUS_COLOR`
  and the helpers :func:`_strip_ansi`/:func:`_one_line` are the coupled primitives.
- :class:`Palette` is a tiny colorizer that no-ops when color is disabled. The color
  decision (whether a TTY should be colored) is supplied BY THE CALLER, so this module
  does not own the duplicated ``should_color`` TTY logic (see runnernorm child dg28i9
  OQ-01; that consolidation is deferred).
- :func:`render_event` translates one raw JSONL event from ``opencode run --format json``
  into a concise, colored terminal line.
- :class:`Heartbeat` prints a periodic "still working" line when the child stream is quiet.

The behavior here is a byte-for-byte extraction; consumers keep identical rendered
output for the same event stream.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import signal
import threading
import time
from typing import Any, Callable, TextIO


# ANSI SGR codes. Kept local so a standalone driver has no heavier package dependency.
_ANSI_RESET = "\033[0m"
_ANSI_CODES = {
    "bold": "1",
    "dim": "2",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "gray": "90",
}
_ANSI_STRIP_RE = re.compile(r"\033\[[0-9;]*m")

# Terminal status word -> color, mirroring the toolkit's convention.
_STATUS_COLOR = {
    "executed": "green",
    "reviewed": "green",
    "approved": "green",
    "substantially-complete": "green",
    "partial": "yellow",
    "blocked": "yellow",
    "dependency-blocked": "yellow",
    "failed-safely": "red",
    "not-attempted": "gray",
    "interrupted": "yellow",
    "running": "cyan",
    "queued": "gray",
    # driverfin-03 (7kbtkw): fail-closed integration outcomes (dirty-base refusal / merge conflict);
    # rendered red because they leave the child NOT integrated and its set NOT finished.
    "integration-blocked": "red",
    "merge-conflict": "red",
}


class Palette:
    """Tiny colorizer: no-ops cleanly when color is disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        codes = ";".join(_ANSI_CODES[s] for s in styles if s in _ANSI_CODES)
        if not codes:
            return text
        return f"\033[{codes}m{text}{_ANSI_RESET}"

    def status(self, status: str) -> str:
        return (
            self(status, self_color)
            if (self_color := _STATUS_COLOR.get(status))
            else status
        )


def _strip_ansi(text: str) -> str:
    return _ANSI_STRIP_RE.sub("", text)


def _one_line(text: str, limit: int = 200) -> str:
    """Collapse whitespace/newlines to a single line and clip to ``limit`` chars."""
    collapsed = " ".join(text.split())
    if len(collapsed) > limit:
        return collapsed[: limit - 1] + "\u2026"
    return collapsed


def format_tokens(n: int | float) -> str:
    """Format token count into compact human-readable string with K/M/G suffix."""
    val = float(n)
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}G"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    if val >= 1_000:
        return f"{val / 1_000:.2f}K"
    return str(int(val))


class StreamTracker:
    """Tracks cumulative usage metrics across streamed events in a run."""

    def __init__(self) -> None:
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cache_tokens: int = 0
        self.cost: float = 0.0

    def update(
        self,
        inp: int = 0,
        out: int = 0,
        cache: int = 0,
        cost: float = 0.0,
    ) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.cache_tokens += cache
        self.cost += cost


def render_event(
    raw_line: str,
    pal: Palette,
    tracker: StreamTracker | None = None,
) -> str | None:
    """Translate one raw JSONL event from `opencode run --format json` into a
    concise, colored terminal line.
    """
    line = raw_line.rstrip("\n")
    if not line.strip():
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return pal(_one_line(line), "dim")
    etype = event.get("type")
    part = event.get("part") or {}
    if etype == "text":
        text = part.get("text") or ""
        text = _one_line(text, 400)
        if not text:
            return None
        return pal("\u2022 ", "cyan") + text
    if etype == "tool_use":
        state = part.get("state") or {}
        tool = part.get("tool") or "tool"
        status = state.get("status") or ""
        title = state.get("title") or ""
        if not title:
            inp = state.get("input")
            if isinstance(inp, dict):
                title = _one_line(json.dumps(inp, sort_keys=True), 120)
        title = _one_line(title, 160)
        if status == "completed":
            glyph = pal("\u2713", "green")
        elif status in ("error", "failed"):
            glyph = pal("\u2717", "red")
        elif status in ("running", "pending", "in_progress"):
            glyph = pal("\u2026", "yellow")
        else:
            glyph = pal("\u2022", "gray")
        label = pal(f"{tool}", "bold")
        body = f": {title}" if title else ""
        return f"{glyph} {label}{body}"
    if etype == "step_finish":
        tok_dict = part.get("tokens") or {}
        cost_raw = part.get("cost")
        if not tok_dict and cost_raw is None:
            return None

        inp = tok_dict.get("input") or 0
        out = tok_dict.get("output") or 0
        cache_raw = tok_dict.get("cache") or 0
        if isinstance(cache_raw, dict):
            cache_val = (cache_raw.get("read") or 0) + (cache_raw.get("write") or 0)
        elif isinstance(cache_raw, (int, float)):
            cache_val = int(cache_raw)
        else:
            cache_val = 0

        cost = cost_raw or 0.0

        if tracker is not None:
            tracker.update(inp=inp, out=out, cache=cache_val, cost=cost)

        return None


def format_compact_tokens(n: int | float) -> str:
    """Format token count into compact string with k/m/g suffix (e.g. 24.5k, 4.1k, 1.2M)."""
    val = float(n)
    if val >= 1_000_000_000:
        s = f"{val / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}g"
    if val >= 1_000_000:
        s = f"{val / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}m"
    if val >= 1_000:
        s = f"{val / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}k"
    return str(int(val))


_FRACTIONAL_BLOCKS = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]


def format_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Format a block progress bar with blank spaces and fraction eighths (e.g. ' 0/80  [          ]   0.00%')."""
    if total <= 0:
        frac = 0.0
        tot_str = "0"
        cur_str = "0"
    else:
        frac = max(0.0, min(1.0, float(current) / float(total)))
        tot_str = str(total)
        cur_str = f"{current:>{len(tot_str)}}"

    eighths = int(round(frac * width * 8))
    full = eighths // 8
    rem = eighths % 8
    if rem > 0 and full < width:
        bar = "█" * full + _FRACTIONAL_BLOCKS[rem] + " " * (width - full - 1)
    else:
        bar = "█" * full + " " * (width - full)

    pct = int(round(frac * 100))
    return f"{cur_str}/{tot_str}  [{bar}] {pct:>3}%"


def format_stall_countdown(
    remaining: float | None, progress_source: str | None = None
) -> str:
    """Render the stall-kill countdown for the live display.

    ``remaining`` MUST come from the watchdog that actually kills the turn (see
    ``StallWatchdog.remaining``), never from a second independent timestamp.

    Returns ``""`` when ``remaining`` is None, i.e. when no stall timeout is configured
    (``--stall-timeout 0``). Claiming a countdown in that case would be a lie: nothing is
    going to kill the turn.
    """
    if remaining is None:
        return ""
    secs = max(0, int(remaining))
    mins, rem = divmod(secs, 60)
    label = f"kill in {mins}m{rem:02d}s" if mins else f"kill in {rem}s"
    if progress_source:
        return f"{label} (last: {progress_source})"
    return label


ACTION_DISPLAY_MAP: dict[str, str] = {
    "review": "Review",
    "execute": "Execute",
    "exec": "Execute",
    "graduate": "Graduat",
    "graduat": "Graduat",
    "validate": "Validat",
    "validat": "Validat",
    "orchestrate": "Orchest",
    "orchest": "Orchest",
}

ARTIFACT_DISPLAY_MAP: dict[str, str] = {
    "ipd": "IPD",
    "plan": "IPD",
    "spec": "Spec",
    "prompt": "Prompt",
    "roadmap": "Roadmap",
    "walkthrough": "Walkthr",
    "walkthr": "Walkthr",
    "backlog": "Backlog",
}


def format_action_label(action: str | None) -> str:
    """Format the workflow action into a compact statusline column label (max 7 chars).

    Supported: Review, Execute, Graduat (Graduate), Validat (Validate), Orchest (Orchestrate).
    """
    if not action:
        return "Review"
    key = action.strip().lower()
    return ACTION_DISPLAY_MAP.get(key, action.strip()[:7].capitalize())


def format_artifact_kind_label(artifact_kind: str | None) -> str:
    """Format the workflow artifact kind into a compact statusline column label (max 7 chars).

    Supported: IPD, Spec, Prompt, Roadmap, Walkthr (Walkthrough), Backlog.
    """
    if not artifact_kind:
        return "IPD"
    key = artifact_kind.strip().lower()
    return ARTIFACT_DISPLAY_MAP.get(key, artifact_kind.strip()[:7].capitalize())


def statusline_action_for_item(item: dict[str, Any]) -> str:
    """Derive the statusline action label from a queue item (vaboqp).

    A queued item's 'status' tracks execution state ('queued' -> 'running' -> 'executed'),
    NOT plan readiness. The workflow action lives in 'action' ('execute', 'review',
    'orchestrate'), with fallback to 'initial_status' or 'execute'.
    """
    act = item.get("action")
    if act:
        return str(act)
    initial = item.get("initial_status")
    if initial and initial in ("to-review", "draft"):
        return "review"
    if initial:
        return "execute"
    status = item.get("status")
    if status in ("to-review", "draft"):
        return "review"
    return "execute"


def format_statusline_lines(
    now_ts: float,
    run_start_ts: float,
    item_start_ts: float,
    last_act_ts: float,
    current_idx: int,
    total_items: int,
    setid: str,
    id6: str,
    tracker: StreamTracker | None = None,
    pal: Palette | None = None,
    stall_remaining: float | None = None,
    progress_source: str | None = None,
    action: str | None = None,
    artifact_kind: str | None = None,
    use_unicode: bool = True,
) -> tuple[str, str, str, str]:
    """Format the 4-line boxed runner statusline (top border, header line, value line, bottom border):

    ╭─────────┬───────────────────────────┬───────────────────────────────┬─────────┬───────┬─────┬───────┬──────┬────────┬───────╮
    │Time     │ From start  kill in 9m51s │ set: wtisoland    id6: 6knsrx │  Review │ Spend │ Tok │ Total │   In │    Out │ Cache │
    │20:27:24 │ 27m48s last: 8s    stdout │ 27m48s ██████████ 100% [1/1]  │     IPD │ $6.16 │ ens │  4.7m │ 119k │ 110.7k │  4.5m │
    ╰─────────┴───────────────────────────┴───────────────────────────────┴─────────┴───────┴─────┴───────┴──────┴────────┴───────╯
    """
    t_str = time.strftime("%H:%M:%S", time.localtime(now_ts))

    # 1. Run Elapsed & Last Activity / Source (Col 2)
    run_elapsed = max(0, int(now_ts - run_start_ts))
    run_el_str = format_compact_duration(run_elapsed)

    idle = max(0, int(now_ts - last_act_ts))
    idle_str = f"{idle}s" if idle < 60 else format_compact_duration(idle)
    val2_left = f" {run_el_str} last: {idle_str}"

    countdown = format_stall_countdown(stall_remaining, None)
    hdr2_left = " From start"
    val2_right = f"{progress_source} " if progress_source else ""
    hdr2_right = f"{countdown} " if countdown else ""

    col2_w = max(
        27,
        len(hdr2_left) + len(hdr2_right) + 1,
        len(val2_left) + len(val2_right) + 1,
    )

    h2 = f"{hdr2_left}{hdr2_right:>{col2_w - len(hdr2_left)}s}"
    v2 = f"{val2_left}{val2_right:>{col2_w - len(val2_left)}s}"

    # 2. Item Elapsed & Progress Bar (Col 3)
    item_elapsed = max(0, int(now_ts - item_start_ts))
    item_el_str = format_compact_duration(item_elapsed)
    bar = format_progress_bar(current_idx, total_items)
    val3 = f" {item_el_str} {bar}"

    if setid and id6:
        hdr3_left = f" set: {setid}"
        hdr3_right = f"id6: {id6} "
        col3_w = max(31, len(hdr3_left) + len(hdr3_right) + 1, len(val3) + 2)
        h3 = f"{hdr3_left}{hdr3_right:>{col3_w - len(hdr3_left)}s}"
    elif setid:
        col3_w = max(31, len(setid) + 8, len(val3) + 2)
        h3 = f" set: {setid} ".ljust(col3_w)
    elif id6:
        col3_w = max(31, len(id6) + 8, len(val3) + 2)
        h3 = f" id6: {id6} ".ljust(col3_w)
    else:
        col3_w = max(31, len(val3) + 2)
        h3 = " -".ljust(col3_w)
    v3 = f"{val3:<{col3_w}s}"

    # 3. Action / Artifact Kind (Col 4)
    act_str = format_action_label(action)
    art_str = format_artifact_kind_label(artifact_kind)
    col4_w = max(9, len(act_str) + 2, len(art_str) + 2)
    h4 = f"{act_str:>{col4_w - 1}s} "
    v4 = f"{art_str:>{col4_w - 1}s} "

    # 4. Spend (Col 5)
    cost = tracker.cost if tracker is not None else 0.0
    cost_str = f"${cost:.2f}"
    col5_w = max(7, len(cost_str) + 2)
    h5 = " Spend ".rjust(col5_w)
    v5 = f"{cost_str:>{col5_w - 1}s} "

    # 5. Token Sub-columns (Cols 6-10)
    # Col 6: Tok / ens
    col6_w = 5
    h6 = " Tok "
    v6 = " ens "

    # Col 7: Total
    tot_tok = (
        (tracker.input_tokens + tracker.output_tokens + tracker.cache_tokens)
        if tracker is not None
        else 0
    )
    tot_str = format_compact_tokens(tot_tok)
    col7_w = max(7, len(tot_str) + 2)
    h7 = " Total ".rjust(col7_w)
    v7 = f"{tot_str:>{col7_w - 1}s} "

    # Col 8: In
    in_tok = tracker.input_tokens if tracker is not None else 0
    in_str = format_compact_tokens(in_tok)
    col8_w = max(6, len(in_str) + 2)
    h8 = "   In ".rjust(col8_w)
    v8 = f"{in_str:>{col8_w - 1}s} "

    # Col 9: Out
    out_tok = tracker.output_tokens if tracker is not None else 0
    out_str = format_compact_tokens(out_tok)
    col9_w = max(8, len(out_str) + 2)
    h9 = "    Out ".rjust(col9_w)
    v9 = f"{out_str:>{col9_w - 1}s} "

    # Col 10: Cache
    cache_tok = tracker.cache_tokens if tracker is not None else 0
    cache_str = format_compact_tokens(cache_tok)
    col10_w = max(7, len(cache_str) + 2)
    h10 = " Cache ".rjust(col10_w)
    v10 = f"{cache_str:>{col10_w - 1}s} "

    # Col 1: Time
    col1_w = 9
    h1 = f"{'Time':<{col1_w}s}"
    v1 = f"{t_str:<8s} "

    col_widths = [
        col1_w,
        col2_w,
        col3_w,
        col4_w,
        col5_w,
        col6_w,
        col7_w,
        col8_w,
        col9_w,
        col10_w,
    ]

    if use_unicode:
        c_tl, c_tm, c_tr = "╭", "┬", "╮"
        c_bl, c_bm, c_br = "╰", "┴", "╯"
        c_v, c_h = "│", "─"
    else:
        c_tl, c_tm, c_tr = "+", "+", "+"
        c_bl, c_bm, c_br = "+", "+", "+"
        c_v, c_h = "|", "-"

    top_border = c_tl + c_tm.join(c_h * w for w in col_widths) + c_tr
    bot_border = c_bl + c_bm.join(c_h * w for w in col_widths) + c_br

    hdrs = [h1, h2, h3, h4, h5, h6, h7, h8, h9, h10]
    vals = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10]

    l1_plain = c_v + c_v.join(hdrs) + c_v
    l2_plain = c_v + c_v.join(vals) + c_v

    if pal is None or not pal.enabled:
        return top_border, l1_plain, l2_plain, bot_border

    # Colorized 256-color palette styling:
    b_blue = "\033[1;38;5;117m"  # soft bold sky light blue
    b_clock = "\033[1;38;5;123m"  # pale bright cyan
    b_bar = "\033[1;38;5;78m"  # light emerald green
    b_target = "\033[1;38;5;229m"  # soft cream/yellow
    b_cost = "\033[1;38;5;114m"  # light green
    b_warn = "\033[1;38;5;208m"  # warm amber/orange for countdown
    dim_hdr = "\033[38;5;110m"  # soft muted slate blue for headers
    dim_src = "\033[38;5;110m"
    bdr_color = "\033[38;5;67m"
    reset = _ANSI_RESET

    top_color = f"{bdr_color}{top_border}{reset}"
    bot_color = f"{bdr_color}{bot_border}{reset}"

    c_h1 = f"{dim_hdr}{h1}"
    if countdown:
        pad_len = col2_w - len(hdr2_left) - len(hdr2_right)
        c_h2 = f"{dim_hdr}{hdr2_left}{' ' * pad_len}{b_warn}{hdr2_right}"
    else:
        c_h2 = f"{dim_hdr}{h2}"

    c_h3 = f"{b_target}{h3}"
    c_h4 = f"{dim_hdr}{h4}"
    c_h5 = f"{dim_hdr}{h5}"
    c_h6 = f"{dim_hdr}{h6}"
    c_h7 = f"{dim_hdr}{h7}"
    c_h8 = f"{dim_hdr}{h8}"
    c_h9 = f"{dim_hdr}{h9}"
    c_h10 = f"{dim_hdr}{h10}"

    c_v1 = f"{b_clock}{v1}"
    if progress_source:
        pad_len = col2_w - len(val2_left) - len(val2_right)
        c_v2 = f"{b_blue}{val2_left}{' ' * pad_len}{dim_src}{val2_right}"
    else:
        c_v2 = f"{b_blue}{v2}"

    c_v3 = f"{b_bar}{v3}"
    c_v4 = f"{b_target}{v4}"
    c_v5 = f"{b_cost}{v5}"
    c_v6 = f"{dim_hdr}{v6}"
    c_v7 = f"{b_blue}{v7}"
    c_v8 = f"{b_blue}{v8}"
    c_v9 = f"{b_blue}{v9}"
    c_v10 = f"{b_blue}{v10}"

    c_hdrs = [c_h1, c_h2, c_h3, c_h4, c_h5, c_h6, c_h7, c_h8, c_h9, c_h10]
    c_vals = [c_v1, c_v2, c_v3, c_v4, c_v5, c_v6, c_v7, c_v8, c_v9, c_v10]

    div = f"{bdr_color}{c_v}{reset}"
    l1_color = (
        f"{bdr_color}{c_v}{reset}" + div.join(c_hdrs) + f"{bdr_color}{c_v}{reset}"
    )
    l2_color = (
        f"{bdr_color}{c_v}{reset}" + div.join(c_vals) + f"{bdr_color}{c_v}{reset}"
    )

    return top_color, l1_color, l2_color, bot_color


def format_statusline(
    now_ts: float,
    start_ts: float,
    last_act_ts: float,
    current_idx: int,
    total_items: int,
    setid: str,
    id6: str,
    tracker: StreamTracker | None = None,
    pal: Palette | None = None,
    item_start_ts: float | None = None,
    stall_remaining: float | None = None,
    progress_source: str | None = None,
    action: str | None = None,
    artifact_kind: str | None = None,
    use_unicode: bool = True,
) -> str:
    """Format the 4-line unified runner statusline box as a newline-delimited string."""
    item_ts = start_ts if item_start_ts is None else item_start_ts
    lines = format_statusline_lines(
        now_ts=now_ts,
        run_start_ts=start_ts,
        item_start_ts=item_ts,
        last_act_ts=last_act_ts,
        current_idx=current_idx,
        total_items=total_items,
        setid=setid,
        id6=id6,
        tracker=tracker,
        pal=pal,
        stall_remaining=stall_remaining,
        progress_source=progress_source,
        action=action,
        artifact_kind=artifact_kind,
        use_unicode=use_unicode,
    )
    return "\n".join(lines)


class Statusline:
    """A live sticky 4-line boxed statusline pinned to the bottom of the terminal during execution."""

    def __init__(
        self,
        pal: Palette,
        stream: TextIO,
        tracker: StreamTracker | None = None,
        interval: float = 1.0,
        current_idx: int = 0,
        total_items: int = 0,
        setid: str = "",
        id6: str = "",
        run_start_mono: float | None = None,
        watchdog: object | None = None,
        action: str | None = None,
        artifact_kind: str | None = None,
    ) -> None:
        self.pal = pal
        self.stream = stream
        self.tracker = tracker
        self.interval = interval
        self.current_idx = current_idx
        self.total_items = total_items
        self.setid = setid
        self.id6 = id6
        self.action = action
        self.artifact_kind = artifact_kind
        # The stall watchdog is the SINGLE authority for the countdown. It is duck-typed
        # (anything exposing `remaining()`) so this display module keeps no dependency on a
        # driver module, and stays None-safe for callers that pass no watchdog.
        self.watchdog = watchdog
        # Which source last showed progress: "stdout" or "subagent". Names WHY the turn is
        # considered alive, so a quiet-stdout turn is not mistaken for a dead one.
        self.progress_source: str | None = None

        mono_now = time.monotonic()
        self._item_start_mono = mono_now
        self._run_start_mono = (
            run_start_mono if run_start_mono is not None else mono_now
        )
        self._last_activity = mono_now
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._is_tty = bool(getattr(stream, "isatty", None) and stream.isatty())
        self._has_drawn = False

    def touch(self, source: str | None = None) -> None:
        with self._lock:
            self._last_activity = time.monotonic()
            if source:
                self.progress_source = source

    def stall_remaining(self) -> float | None:
        """Remaining time before the stall kill, read from the watchdog itself.

        Returns None when there is no watchdog or it is disabled, so the display omits the
        countdown rather than inventing one.
        """
        watchdog = self.watchdog
        if watchdog is None:
            return None
        try:
            return watchdog.remaining()  # type: ignore[attr-defined]
        except Exception:
            return None

    def update_item(
        self,
        current_idx: int,
        total_items: int,
        setid: str = "",
        id6: str = "",
        action: str | None = None,
        artifact_kind: str | None = None,
    ) -> None:
        with self._lock:
            self.current_idx = current_idx
            self.total_items = total_items
            self._item_start_mono = time.monotonic()
            if setid:
                self.setid = setid
            if id6:
                self.id6 = id6
            if action is not None:
                self.action = action
            if artifact_kind is not None:
                self.artifact_kind = artifact_kind

    def _render_lines_unlocked(self) -> tuple[str, str, str, str]:
        now_wall = time.time()
        cur_mono = time.monotonic()
        run_wall = now_wall - (cur_mono - self._run_start_mono)
        item_wall = now_wall - (cur_mono - self._item_start_mono)
        last_wall = now_wall - (cur_mono - self._last_activity)
        return format_statusline_lines(
            now_ts=now_wall,
            run_start_ts=run_wall,
            item_start_ts=item_wall,
            last_act_ts=last_wall,
            current_idx=self.current_idx,
            total_items=self.total_items,
            setid=self.setid,
            id6=self.id6,
            tracker=self.tracker,
            pal=self.pal,
            stall_remaining=self.stall_remaining(),
            progress_source=self.progress_source,
            action=self.action,
            artifact_kind=self.artifact_kind,
        )

    def render_line(self) -> str:
        with self._lock:
            top, l1, l2, bot = self._render_lines_unlocked()
            return f"{top}\n{l1}\n{l2}\n{bot}"

    def redraw(self) -> None:
        if not self._is_tty:
            return
        with self._lock:
            top, l1, l2, bot = self._render_lines_unlocked()
            if self._has_drawn:
                self.stream.write(
                    f"\033[3A\r\033[K{top}\n\r\033[K{l1}\n\r\033[K{l2}\n\r\033[K{bot}"
                )
            else:
                self.stream.write(
                    f"\r\033[K{top}\n\r\033[K{l1}\n\r\033[K{l2}\n\r\033[K{bot}"
                )
            self.stream.flush()
            self._has_drawn = True

    def clear(self) -> None:
        if not self._is_tty or not self._has_drawn:
            return
        with self._lock:
            self.stream.write("\033[3A\r\033[K\n\r\033[K\n\r\033[K\n\r\033[K\033[3A\r")
            self.stream.flush()
            self._has_drawn = False

    def write_event(self, rendered_text: str) -> None:
        """Write a log event line above the live 4-line boxed statusline."""
        with self._lock:
            if self._is_tty and self._has_drawn:
                top, l1, l2, bot = self._render_lines_unlocked()
                self.stream.write(
                    f"\033[3A\r\033[K\n\r\033[K\n\r\033[K\n\r\033[K\033[3A\r{rendered_text}\n{top}\n{l1}\n{l2}\n{bot}"
                )
                self.stream.flush()
            else:
                self.stream.write(f"{rendered_text}\n")
                self.stream.flush()

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self.redraw()

    def __enter__(self) -> Statusline:
        if self._is_tty and self.interval > 0:
            self.redraw()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self.clear()


class Heartbeat:
    """Periodic quiet-stream line for a driver turn, stating the stall countdown.

    The line deliberately does NOT say a bare "still working": that wording read as
    reassurance while a kill countdown ran invisibly, making a doomed turn
    indistinguishable from a healthy one. Instead it reports time since the last OBSERVED
    PROGRESS, the remaining time before the stall kill, and WHICH source last showed
    progress (``stdout`` or ``subagent``).

    The countdown is sourced from the stall watchdog itself (duck-typed ``remaining()``),
    never from ``self._last_activity``, so the number displayed cannot disagree with the
    clock that actually terminates the child.
    """

    def __init__(
        self,
        pal: Palette,
        label: str,
        stream: TextIO,
        interval: float = 15.0,
        watchdog: object | None = None,
    ) -> None:
        self.pal = pal
        self.label = label
        self.stream = stream
        self.interval = interval
        self.watchdog = watchdog
        self.progress_source: str | None = None
        self._last_activity = time.monotonic()
        self._start = time.monotonic()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = interval > 0

    def touch(self, source: str | None = None) -> None:
        self._last_activity = time.monotonic()
        if source:
            self.progress_source = source

    def stall_remaining(self) -> float | None:
        """Remaining time before the stall kill, read from the watchdog (None if absent)."""
        watchdog = self.watchdog
        if watchdog is None:
            return None
        try:
            return watchdog.remaining()  # type: ignore[attr-defined]
        except Exception:
            return None

    def format_idle(self) -> str:
        idle = int(time.monotonic() - self._last_activity)
        return format_compact_duration(idle)

    def format_message(self) -> str:
        elapsed = int(time.monotonic() - self._start)
        el_str = format_compact_duration(elapsed)
        idle_str = self.format_idle()
        countdown = format_stall_countdown(self.stall_remaining(), self.progress_source)
        tail = f", stall {countdown}" if countdown else ""
        return (
            f"    \u2026 {self.label}: no progress {idle_str} "
            f"({el_str} elapsed{tail})"
        )

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            idle = time.monotonic() - self._last_activity
            if idle >= self.interval:
                msg = self.pal(self.format_message(), "dim")
                self.stream.write(msg + "\n")
                self.stream.flush()

    def __enter__(self) -> Heartbeat:
        if self._enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def format_compact_duration(seconds: float | None) -> str:
    """Format duration seconds into compact statusline format (e.g. '0m00s', '4m08s', '1h04m21s', '3h07m56s', '1d 3h07m56s')."""
    if seconds is None or seconds < 0:
        return "0m00s"
    secs = int(round(seconds))
    if secs < 3600:
        mins, rem_s = divmod(secs, 60)
        return f"{mins}m{rem_s:02d}s"
    hrs, rem = divmod(secs, 3600)
    mins, rem_s = divmod(rem, 60)
    if hrs < 24:
        return f"{hrs}h{mins:02d}m{rem_s:02d}s"
    days, rem_h = divmod(hrs, 24)
    return f"{days}d {rem_h}h{mins:02d}m{rem_s:02d}s"


def format_duration(seconds: float | None) -> str:
    """Format duration seconds into a human-readable string (e.g. '0s', '12s', '4m 12s', '1h 04m 12s', '1d 03h 07m 56s')."""
    if seconds is None or seconds < 0:
        return "0s"
    secs = int(round(seconds))
    if secs < 60:
        return f"{secs}s"
    mins, rem_s = divmod(secs, 60)
    if mins < 60:
        return f"{mins}m {rem_s:02d}s"
    hrs, rem_m = divmod(mins, 60)
    if hrs < 24:
        return f"{hrs}h {rem_m:02d}m {rem_s:02d}s"
    days, rem_h = divmod(hrs, 24)
    return f"{days}d {rem_h}h {rem_m:02d}m {rem_s:02d}s"


def _parse_iso_timestamp(ts_str: str | None) -> float | None:
    """Parse ISO8601 or similar UTC timestamp string into a float epoch timestamp."""
    if not ts_str:
        return None
    try:
        cleaned = ts_str.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(cleaned).timestamp()
    except Exception:
        return None


def render_run_summary_table(
    state: dict[str, Any],
    run_dir: Path | str | None = None,
    tracker: StreamTracker | None = None,
    pal: Palette | None = None,
    exit_reason: str | None = None,
    driver_label: str = "opencode",
    use_unicode: bool = True,
) -> str:
    """Render a visually compelling box-art summary table aggregating runner metrics at exit.

    Includes run duration, spend, token breakdown (total, input, output, cache), progress bar,
    per-item status, duration, cost, tokens, verify outcome, and diagnostic notes for failures.
    """
    if pal is None:
        pal = Palette(True)
    color = pal.enabled

    # Box-drawing primitives
    if use_unicode:
        tl, tm, tr = "╭", "┬", "╮"
        ml, mm, mr = "├", "┼", "┤"
        bl, bm, br = "╰", "┴", "╯"
        vl, hl = "│", "─"
    else:
        tl = tm = tr = ml = mm = mr = bl = bm = br = "+"
        vl, hl = "|", "-"

    queue = state.get("queue", [])
    run_id = state.get("run_id", "run-unknown")
    created_ts = _parse_iso_timestamp(state.get("created_at"))
    updated_ts = _parse_iso_timestamp(state.get("updated_at"))
    now_ts = time.time()

    # Calculate run duration
    if created_ts:
        end_anchor = updated_ts or now_ts
        run_duration_sec = max(0.0, end_anchor - created_ts)
    else:
        run_duration_sec = 0.0

    # Aggregate item data
    items_data = []
    tot_item_dur = 0.0
    tot_item_cost = 0.0
    tot_item_tok = 0
    tot_item_in = 0
    tot_item_out = 0
    tot_item_cache = 0

    status_counts: dict[str, int] = {}
    completed_count = 0

    for idx, item in enumerate(queue):
        pos = item.get("position", idx + 1)
        id6 = item.get("id6", "-")
        setid = item.get("setid", "-")
        action = item.get("action", "execute")
        status = item.get("status", "queued")
        verify = item.get("verification_status") or "-"
        status_counts[status] = status_counts.get(status, 0) + 1

        if status not in ("queued", "not-attempted"):
            completed_count += 1

        # Calculate item duration, cost, tokens
        item_dur = 0.0
        item_cost = 0.0
        item_tok = 0
        item_in = 0
        item_out = 0
        item_cache = 0
        has_run = False

        attempts = item.get("attempts", [])
        for att in attempts:
            has_run = True
            att_s = _parse_iso_timestamp(att.get("started_at"))
            att_e = _parse_iso_timestamp(
                att.get("ended_at") or att.get("interrupted_at")
            )
            if att_s:
                dur = max(0.0, (att_e or now_ts) - att_s)
                item_dur += dur

            c = att.get("cost")
            if c is not None:
                item_cost += float(c)
            vc = att.get("verification_cost")
            if vc is not None:
                item_cost += float(vc)

            toks = att.get("tokens") or {}
            if toks:
                item_tok += toks.get("total", 0)
                item_in += toks.get("input", 0)
                item_out += toks.get("output", 0)
                item_cache += toks.get("cache", 0)

            v_toks = att.get("verification_tokens") or {}
            if v_toks:
                item_tok += v_toks.get("total", 0)
                item_in += v_toks.get("input", 0)
                item_out += v_toks.get("output", 0)
                item_cache += v_toks.get("cache", 0)

        tot_item_dur += item_dur
        tot_item_cost += item_cost
        tot_item_tok += item_tok
        tot_item_in += item_in
        tot_item_out += item_out
        tot_item_cache += item_cache

        dur_str = format_duration(item_dur) if has_run else "-"
        cost_str = f"${item_cost:.2f}" if has_run else "-"
        tok_tot_str = (
            format_compact_tokens(item_tok) if (has_run and item_tok > 0) else "-"
        )
        tok_in_str = (
            format_compact_tokens(item_in) if (has_run and item_in > 0) else "-"
        )
        tok_out_str = (
            format_compact_tokens(item_out) if (has_run and item_out > 0) else "-"
        )
        tok_cache_str = (
            format_compact_tokens(item_cache) if (has_run and item_cache > 0) else "-"
        )

        items_data.append(
            {
                "pos": f"{pos:02d}",
                "id6": id6,
                "setid": setid,
                "action": action,
                "status": status,
                "verify": verify,
                "dur_str": dur_str,
                "cost_str": cost_str,
                "tok_tot_str": tok_tot_str,
                "tok_in_str": tok_in_str,
                "tok_out_str": tok_out_str,
                "tok_cache_str": tok_cache_str,
                "has_run": has_run,
            }
        )

    # Tracker overrides if tracker observed more
    if tracker:
        tot_cost = max(tot_item_cost, tracker.cost)
        tot_in = max(tot_item_in, tracker.input_tokens)
        tot_out = max(tot_item_out, tracker.output_tokens)
        tot_cache = max(tot_item_cache, tracker.cache_tokens)
        tot_tokens = max(
            tot_item_tok,
            tracker.input_tokens + tracker.output_tokens + tracker.cache_tokens,
        )
    else:
        tot_cost = tot_item_cost
        tot_in = tot_item_in
        tot_out = tot_item_out
        tot_cache = tot_item_cache
        tot_tokens = tot_item_tok

    total_items = len(queue)
    prog_bar = format_progress_bar(completed_count, total_items, width=10)

    # Status summary line
    status_parts = []
    for st, cnt in sorted(status_counts.items(), key=lambda x: (-x[1], x[0])):
        status_parts.append(f"{cnt} {st}")
    status_summary_str = ", ".join(status_parts) if status_parts else "0 items"

    # Outcome label
    if exit_reason:
        outcome_str = exit_reason
    elif any(it.get("status") == "interrupted" for it in queue):
        outcome_str = "INTERRUPTED"
    elif any(
        it.get("status") in ("failed-safely", "integration-blocked", "merge-conflict")
        for it in queue
    ):
        outcome_str = "FAILED"
    elif any(it.get("status") in ("blocked", "dependency-blocked") for it in queue):
        outcome_str = "BLOCKED"
    elif (
        all(
            it.get("status")
            in ("executed", "reviewed", "approved", "substantially-complete")
            for it in queue
        )
        and total_items > 0
    ):
        outcome_str = "COMPLETED"
    elif completed_count > 0:
        outcome_str = "PARTIAL"
    else:
        outcome_str = "QUEUED"

    # Colors
    c_bold = "\033[1m" if color else ""
    c_cyan = "\033[36m" if color else ""
    c_green = "\033[32m" if color else ""
    c_yellow = "\033[33m" if color else ""
    c_red = "\033[31m" if color else ""
    c_reset = "\033[0m" if color else ""

    outcome_color = (
        c_green
        if outcome_str == "COMPLETED"
        else (
            c_yellow
            if (
                "INTERRUPT" in outcome_str
                or "STOP" in outcome_str
                or outcome_str == "PARTIAL"
            )
            else (c_red if "FAIL" in outcome_str else c_cyan)
        )
    )

    headers = [
        "#",
        "ID6",
        "Set",
        "Action",
        "Status",
        "Verify",
        "Duration",
        "Spend",
        "Tok tot",
        "Tok in",
        "Tok out",
        "Tok cache",
    ]
    aligns = [
        "right",
        "left",
        "left",
        "left",
        "left",
        "left",
        "right",
        "right",
        "right",
        "right",
        "right",
        "right",
    ]

    raw_rows = []
    styled_rows = []
    for it in items_data:
        st_val = it["status"]
        st_styled = pal.status(st_val) if color else st_val
        v_val = it["verify"]
        if v_val == "pass":
            v_styled = f"{c_green}pass{c_reset}" if color else "pass"
        elif v_val == "fail":
            v_styled = f"{c_red}fail{c_reset}" if color else "fail"
        else:
            v_styled = v_val

        cost_val = it["cost_str"]
        cost_styled = (
            f"{c_green}{cost_val}{c_reset}" if (color and cost_val != "-") else cost_val
        )

        raw_row = [
            it["pos"],
            it["id6"],
            it["setid"],
            it["action"],
            st_val,
            v_val,
            it["dur_str"],
            cost_val,
            it["tok_tot_str"],
            it["tok_in_str"],
            it["tok_out_str"],
            it["tok_cache_str"],
        ]
        styled_row = [
            it["pos"],
            it["id6"],
            it["setid"],
            it["action"],
            st_styled,
            v_styled,
            it["dur_str"],
            cost_styled,
            it["tok_tot_str"],
            it["tok_in_str"],
            it["tok_out_str"],
            it["tok_cache_str"],
        ]
        raw_rows.append(raw_row)
        styled_rows.append(styled_row)

    col_widths = [len(h) for h in headers]
    for row in raw_rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(_strip_ansi(str(cell))))

    tot_dur_str = format_duration(run_duration_sec or tot_item_dur)
    tot_cost_str = f"${tot_cost:.2f}"
    tot_tok_str = format_compact_tokens(tot_tokens)
    tot_in_str = format_compact_tokens(tot_in)
    tot_out_str = format_compact_tokens(tot_out)
    tot_cache_str = format_compact_tokens(tot_cache)

    total_label = f"Total ({completed_count}/{total_items} items run)"
    col_widths[6] = max(col_widths[6], len(tot_dur_str))
    col_widths[7] = max(col_widths[7], len(tot_cost_str))
    col_widths[8] = max(col_widths[8], len(tot_tok_str))
    col_widths[9] = max(col_widths[9], len(tot_in_str))
    col_widths[10] = max(col_widths[10], len(tot_out_str))
    col_widths[11] = max(col_widths[11], len(tot_cache_str))

    b_title = f"AW RUN SUMMARY: {run_id} ({driver_label})"
    b_line1 = (
        f"Outcome: {outcome_color}{outcome_str}{c_reset}   "
        f"Duration: {c_cyan}{tot_dur_str}{c_reset}   "
        f"Spend: {c_green}{tot_cost_str}{c_reset}   "
        f"Tokens: {tot_tok_str} (In: {tot_in_str} │ Out: {tot_out_str} │ Cache: {tot_cache_str})"
    )
    b_line2 = f"Progress: {prog_bar} ({status_summary_str})"

    banner_plain = [
        _strip_ansi(b_title),
        _strip_ansi(b_line1),
        _strip_ansi(b_line2),
    ]
    base_table_width = sum(col_widths) + (len(col_widths) - 1) * 3 + 4
    max_banner_w = max((len(t) for t in banner_plain), default=0) + 4
    if max_banner_w > base_table_width:
        diff = max_banner_w - base_table_width
        col_widths[2] += diff
        base_table_width += diff

    total_table_width = base_table_width
    left_span_w = sum(col_widths[:6]) + (5 * 3)

    top_border = tl + hl * (total_table_width - 2) + tr
    sep_banner_table = ml + tm.join(hl * (w + 2) for w in col_widths) + mr
    sep_headers_rows = ml + mm.join(hl * (w + 2) for w in col_widths) + mr
    sep_totals_border = (
        ml
        + bm.join(hl * (w + 2) for w in col_widths[:6])
        + mm
        + mm.join(hl * (w + 2) for w in col_widths[6:])
        + mr
    )
    bot_border = (
        bl
        + hl * (left_span_w + 2)
        + bm
        + bm.join(hl * (w + 2) for w in col_widths[6:])
        + br
    )

    lines = []
    lines.append(top_border)

    # Banner Title
    pad_title = " " * max(0, total_table_width - 4 - len(_strip_ansi(b_title)))
    lines.append(f"{vl} {c_bold}{b_title}{c_reset}{pad_title} {vl}")

    # Banner Line 1
    pad_1 = " " * max(0, total_table_width - 4 - len(_strip_ansi(b_line1)))
    lines.append(f"{vl} {b_line1}{pad_1} {vl}")

    # Banner Line 2
    pad_2 = " " * max(0, total_table_width - 4 - len(_strip_ansi(b_line2)))
    lines.append(f"{vl} {b_line2}{pad_2} {vl}")
    lines.append(sep_banner_table)

    # Table Header
    hdr_cells = []
    for h, w, a in zip(headers, col_widths, aligns):
        pad = w - len(h)
        h_txt = f"{c_bold}{h}{c_reset}" if color else h
        spaces = " " * pad
        if a == "right":
            hdr_cells.append(f" {spaces}{h_txt} ")
        else:
            hdr_cells.append(f" {h_txt}{spaces} ")
    lines.append(vl + vl.join(hdr_cells) + vl)
    lines.append(sep_headers_rows)

    # Table Rows
    for s_row in styled_rows:
        row_cells = []
        for cell, w, a in zip(s_row, col_widths, aligns):
            raw_len = len(_strip_ansi(str(cell)))
            pad = w - raw_len
            spaces = " " * pad
            if a == "right":
                row_cells.append(f" {spaces}{cell} ")
            else:
                row_cells.append(f" {cell}{spaces} ")
        lines.append(vl + vl.join(row_cells) + vl)

    # Totals Row
    pad_tot_lbl = " " * max(0, left_span_w - len(_strip_ansi(total_label)))
    tot_lbl_txt = f"{c_bold}{total_label}{c_reset}" if color else total_label
    tot_lbl_cell = f" {tot_lbl_txt}{pad_tot_lbl} "

    dur_cell_str = (
        f" {' ' * (col_widths[6] - len(tot_dur_str))}{c_cyan}{tot_dur_str}{c_reset} "
        if color
        else f" {' ' * (col_widths[6] - len(tot_dur_str))}{tot_dur_str} "
    )
    cost_cell_str = (
        f" {' ' * (col_widths[7] - len(tot_cost_str))}{c_green}{tot_cost_str}{c_reset} "
        if color
        else f" {' ' * (col_widths[7] - len(tot_cost_str))}{tot_cost_str} "
    )

    tot_cells = [
        tot_lbl_cell,
        dur_cell_str,
        cost_cell_str,
        f" {' ' * (col_widths[8] - len(tot_tok_str))}{tot_tok_str} ",
        f" {' ' * (col_widths[9] - len(tot_in_str))}{tot_in_str} ",
        f" {' ' * (col_widths[10] - len(tot_out_str))}{tot_out_str} ",
        f" {' ' * (col_widths[11] - len(tot_cache_str))}{tot_cache_str} ",
    ]
    lines.append(sep_totals_border)
    lines.append(vl + vl.join(tot_cells) + vl)
    lines.append(bot_border)

    # Failure / Dependency block diagnostics
    diag_lines = []
    for it in queue:
        st = it.get("status")
        id6 = it.get("id6")
        if st == "dependency-blocked":
            reasons = it.get("unsatisfied_dependency_reasons") or {}
            deps = it.get("unsatisfied_dependencies") or []
            dep_msg = (
                ", ".join(f"{d} ({reasons.get(d, 'blocked')})" for d in deps)
                if deps
                else "unmet dependencies"
            )
            diag_lines.append(f"  • {id6}: dependency-blocked ({dep_msg})")
        elif st in (
            "failed-safely",
            "integration-blocked",
            "merge-conflict",
        ) and it.get("driver_error"):
            diag_lines.append(f"  • {id6}: {st} ({it['driver_error']})")
        elif st == "interrupted" and it.get("interrupt_reason"):
            diag_lines.append(f"  • {id6}: interrupted ({it['interrupt_reason']})")

    if diag_lines:
        lines.append("")
        lines.append(f"{c_bold}Diagnostics / Blocked Items:{c_reset}")
        lines.extend(diag_lines)

    return "\n".join(lines)


def install_exit_signal_handler(
    handler: Callable[[int, Any], None] | None = None,
) -> Any:
    """Install SIGTERM exit handler on the main thread if supported."""
    if handler is None:

        def _default_handler(signum: int, frame: Any) -> None:
            raise KeyboardInterrupt("Terminated by SIGTERM")

        handler = _default_handler
    try:
        if threading.current_thread() is threading.main_thread():
            return signal.signal(signal.SIGTERM, handler)
    except (ValueError, AttributeError):
        pass
    return None

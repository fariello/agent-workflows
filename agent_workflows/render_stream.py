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


def format_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Format a block progress bar with percentage and item count (e.g. '████████░░ 80% [4/5]')."""
    if total <= 0:
        return "░" * width + "  0% [0/0]"
    frac = max(0.0, min(1.0, float(current) / float(total)))
    filled = int(round(frac * width))
    bar = "█" * filled + "░" * (width - filled)
    pct = int(round(frac * 100))
    return f"{bar} {pct:>2}% [{current}/{total}]"


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
) -> tuple[str, str]:
    """Format the 2-line runner statusline (header line and value line):

    Time     │ From start        │ set: revgate id6: 7nkcgp         │ Spend   │  Tok tot │   Tok in │  Tok out │ Tok cache │
    23:11:21 │ 64m21s idle: 14s  │ 4m08s ██████████ 100% [1/1]      │ $15.27  │    16.2m │   214.1k │   195.7k │     15.8m │
    """
    t_str = time.strftime("%H:%M:%S", time.localtime(now_ts))

    # Run Elapsed & Idle
    run_elapsed = max(0, int(now_ts - run_start_ts))
    r_m, r_s = divmod(run_elapsed, 60)
    run_el_str = f"{r_m}m{r_s:02d}s"

    idle = max(0, int(now_ts - last_act_ts))
    if idle >= 60:
        im, is_ = divmod(idle, 60)
        idle_str = f"idle: {im}m{is_:02d}s"
    else:
        idle_str = f"idle: {idle}s"
    col2_val = f"{run_el_str} {idle_str}"
    # The stall countdown is ADDITIVE: with no configured timeout (`--stall-timeout 0`) the
    # column is byte-identical to before, so no false or infinite countdown is ever claimed.
    # `idle:` alone was the misleading part: it reported quiet time while a kill clock ran
    # invisibly. The countdown comes from the watchdog's own clock (see
    # StallWatchdog.remaining) so the displayed number cannot disagree with the killer.
    countdown = format_stall_countdown(stall_remaining, progress_source)
    if countdown:
        col2_val = f"{col2_val} {countdown}"

    # Item Elapsed & Progress bar
    item_elapsed = max(0, int(now_ts - item_start_ts))
    i_m, i_s = divmod(item_elapsed, 60)
    item_el_str = f"{i_m}m{i_s:02d}s"

    bar = format_progress_bar(current_idx, total_items)
    col3_val = f"{item_el_str} {bar}"
    target_hdr = f"set: {setid} id6: {id6}" if (setid or id6) else "-"

    # Spend
    cost = tracker.cost if tracker is not None else 0.0
    cost_str = f"${cost:.2f}"

    # Tokens
    tot_tok = (
        (tracker.input_tokens + tracker.output_tokens + tracker.cache_tokens)
        if tracker is not None
        else 0
    )
    tot_str = format_compact_tokens(tot_tok)
    in_str = format_compact_tokens(tracker.input_tokens if tracker is not None else 0)
    out_str = format_compact_tokens(tracker.output_tokens if tracker is not None else 0)
    cache_str = format_compact_tokens(
        tracker.cache_tokens if tracker is not None else 0
    )

    h1 = "Time    "
    # Column 2 grows to fit the countdown when one is shown, so the header and value lines
    # stay the SAME width (a pinned invariant: len(l1) == len(l2)) and the countdown is never
    # clipped. With no countdown the width is the original 17, keeping the layout unchanged.
    col2_w = max(17, len(col2_val))
    h2 = f"{'From start':<{col2_w}s}"
    col3_w = 32
    h3 = f"{target_hdr:<{col3_w}s}"
    h4 = "Spend  "
    h5 = " Tok tot"
    h6 = "  Tok in"
    h7 = " Tok out"
    h8 = "Tok cache"

    v1 = f"{t_str:<8s}"
    v2 = f"{col2_val:<{col2_w}s}"
    v3 = f"{col3_val:<{col3_w}s}"
    v4 = f"{cost_str:<7s}"
    v5 = f"{tot_str:>8s}"
    v6 = f"{in_str:>8s}"
    v7 = f"{out_str:>8s}"
    v8 = f"{cache_str:>9s}"

    div_plain = " │ "
    l1_plain = (
        f"{h1}{div_plain}{h2}{div_plain}{h3}{div_plain}{h4}"
        f"{div_plain}{h5}{div_plain}{h6}{div_plain}{h7}{div_plain}{h8} │"
    )
    l2_plain = (
        f"{v1}{div_plain}{v2}{div_plain}{v3}{div_plain}{v4}"
        f"{div_plain}{v5}{div_plain}{v6}{div_plain}{v7}{div_plain}{v8} │"
    )

    if pal is None or not pal.enabled:
        return l1_plain, l2_plain

    # Colorized 256-color palette styling:
    b_blue = "\033[1;38;5;117m"  # soft bold sky light blue
    b_clock = "\033[1;38;5;123m"  # pale bright cyan
    b_bar = "\033[1;38;5;78m"  # light emerald green
    b_target = "\033[1;38;5;229m"  # soft cream/yellow
    b_cost = "\033[1;38;5;114m"  # light green
    dim_hdr = "\033[38;5;110m"  # soft muted slate blue for headers
    div = "\033[38;5;67m │ \033[0m"
    reset = _ANSI_RESET

    hdrs = [
        f"{dim_hdr}{h1}",
        f"{dim_hdr}{h2}",
        f"{b_target}{h3}",
        f"{dim_hdr}{h4}",
        f"{dim_hdr}{h5}",
        f"{dim_hdr}{h6}",
        f"{dim_hdr}{h7}",
        f"{dim_hdr}{h8}",
    ]
    l1_color = div.join(hdrs) + f"\033[38;5;67m │{reset}"

    vals = [
        f"{b_clock}{v1}",
        f"{b_blue}{v2}",
        f"{b_bar}{v3}",
        f"{b_cost}{v4}",
        f"{b_blue}{v5}",
        f"{b_blue}{v6}",
        f"{b_blue}{v7}",
        f"{b_blue}{v8}",
    ]
    l2_color = div.join(vals) + f"\033[38;5;67m │{reset}"
    return l1_color, l2_color


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
) -> str:
    """Format the 2-line unified runner statusline as a newline-delimited string."""
    item_ts = start_ts if item_start_ts is None else item_start_ts
    l1, l2 = format_statusline_lines(
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
    )
    return f"{l1}\n{l2}"


class Statusline:
    """A live sticky 2-line statusline pinned to the bottom of the terminal during execution."""

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
    ) -> None:
        self.pal = pal
        self.stream = stream
        self.tracker = tracker
        self.interval = interval
        self.current_idx = current_idx
        self.total_items = total_items
        self.setid = setid
        self.id6 = id6
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
    ) -> None:
        with self._lock:
            self.current_idx = current_idx
            self.total_items = total_items
            self._item_start_mono = time.monotonic()
            if setid:
                self.setid = setid
            if id6:
                self.id6 = id6

    def _render_lines_unlocked(self) -> tuple[str, str]:
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
        )

    def render_line(self) -> str:
        with self._lock:
            l1, l2 = self._render_lines_unlocked()
            return f"{l1}\n{l2}"

    def redraw(self) -> None:
        if not self._is_tty:
            return
        with self._lock:
            l1, l2 = self._render_lines_unlocked()
            if self._has_drawn:
                self.stream.write(f"\033[1A\r\033[K{l1}\n\r\033[K{l2}")
            else:
                self.stream.write(f"\r\033[K{l1}\n\r\033[K{l2}")
            self.stream.flush()
            self._has_drawn = True

    def clear(self) -> None:
        if not self._is_tty or not self._has_drawn:
            return
        with self._lock:
            self.stream.write("\033[1A\r\033[K\n\r\033[K\033[1A\r")
            self.stream.flush()
            self._has_drawn = False

    def write_event(self, rendered_text: str) -> None:
        """Write a log event line above the live 2-line statusline."""
        with self._lock:
            if self._is_tty and self._has_drawn:
                l1, l2 = self._render_lines_unlocked()
                self.stream.write(
                    f"\033[1A\r\033[K\n\r\033[K\033[1A\r{rendered_text}\n{l1}\n{l2}"
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
        idle_m, idle_s = divmod(idle, 60)
        return f"{idle_m}m{idle_s:02d}s"

    def format_message(self) -> str:
        elapsed = int(time.monotonic() - self._start)
        mins, secs = divmod(elapsed, 60)
        idle_str = self.format_idle()
        countdown = format_stall_countdown(self.stall_remaining(), self.progress_source)
        tail = f", stall {countdown}" if countdown else ""
        return (
            f"    \u2026 {self.label}: no progress {idle_str} "
            f"({mins}m{secs:02d}s elapsed{tail})"
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


def format_duration(seconds: float | None) -> str:
    """Format duration seconds into a human-readable string (e.g. '0s', '12s', '4m 12s', '1h 04m 12s')."""
    if seconds is None or seconds < 0:
        return "0s"
    secs = int(round(seconds))
    if secs < 60:
        return f"{secs}s"
    mins, rem = divmod(secs, 60)
    if mins < 60:
        return f"{mins}m {rem:02d}s"
    hrs, rem_m = divmod(mins, 60)
    return f"{hrs}h {rem_m:02d}m {rem:02d}s"


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

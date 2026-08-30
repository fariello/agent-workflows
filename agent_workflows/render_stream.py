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

import json
import re
import threading
import time
from typing import TextIO


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
    h2 = "From start       "
    col3_w = 32
    h3 = f"{target_hdr:<{col3_w}s}"
    h4 = "Spend  "
    h5 = " Tok tot"
    h6 = "  Tok in"
    h7 = " Tok out"
    h8 = "Tok cache"

    v1 = f"{t_str:<8s}"
    v2 = f"{col2_val:<17s}"
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
    ) -> None:
        self.pal = pal
        self.stream = stream
        self.tracker = tracker
        self.interval = interval
        self.current_idx = current_idx
        self.total_items = total_items
        self.setid = setid
        self.id6 = id6

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

    def touch(self) -> None:
        with self._lock:
            self._last_activity = time.monotonic()

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
    """Prints a periodic 'still working' line to stderr when the child stream is quiet."""

    def __init__(
        self, pal: Palette, label: str, stream: TextIO, interval: float = 15.0
    ) -> None:
        self.pal = pal
        self.label = label
        self.stream = stream
        self.interval = interval
        self._last_activity = time.monotonic()
        self._start = time.monotonic()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = interval > 0

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    def format_idle(self) -> str:
        idle = int(time.monotonic() - self._last_activity)
        idle_m, idle_s = divmod(idle, 60)
        return f"{idle_m}m{idle_s:02d}s"

    def format_message(self) -> str:
        elapsed = int(time.monotonic() - self._start)
        mins, secs = divmod(elapsed, 60)
        idle_str = self.format_idle()
        return (
            f"    \u2026 still working on {self.label} "
            f"({mins}m{secs:02d}s elapsed, {idle_str} since last event)"
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

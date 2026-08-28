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
        return pal("  " + _one_line(line), "dim")
    etype = event.get("type")
    part = event.get("part") or {}
    if etype == "text":
        text = part.get("text") or ""
        text = _one_line(text, 400)
        if not text:
            return None
        return pal("  \u2022 ", "cyan") + text
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
        return f"    {glyph} {label}{body}"
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

        step_total = tok_dict.get("total")
        if step_total is None:
            step_total = inp + out + cache_val

        cost = cost_raw or 0.0

        if tracker is not None:
            tracker.update(inp=inp, out=out, cache=cache_val, cost=cost)
            cum_inp = tracker.input_tokens
            cum_out = tracker.output_tokens
            cum_cache = tracker.cache_tokens
            cum_cost = tracker.cost
        else:
            cum_inp = inp
            cum_out = out
            cum_cache = cache_val
            cum_cost = cost

        step_tok_str = format_tokens(step_total)
        step_cost_str = f"${cost:.4f}"
        cum_in_str = format_tokens(cum_inp)
        cum_out_str = format_tokens(cum_out)
        cum_cache_str = format_tokens(cum_cache)
        cum_cost_str = f"${cum_cost:.2f}"

        summary = (
            f"{step_tok_str} tok, {step_cost_str}; "
            f"tok: {cum_in_str} in, {cum_out_str} out, {cum_cache_str} cache, {cum_cost_str} tot"
        )
        return pal(f"    \u2014 step done ({summary})", "dim")
    return None


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

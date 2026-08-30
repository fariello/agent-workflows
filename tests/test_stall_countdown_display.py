#!/usr/bin/env python3
"""The live display must state the stall countdown, sourced from the watchdog's own clock.

Before this change the quiet-turn display said "still working", and reported only quiet
time, while a kill countdown ran invisibly; a doomed turn looked identical to a healthy one.
Worse, the display kept its OWN ``_last_activity``, independent of the watchdog's, so any
countdown it computed itself could disagree with the clock that actually kills.

These tests therefore assert three things: the countdown is PRESENT, it DECREASES, and it
FOLLOWS THE WATCHDOG rather than a second timestamp.
"""

from __future__ import annotations

import io
import unittest

from agent_workflows import render_stream


class _FakeWatchdog:
    """Stands in for StallWatchdog: the single authority for time-to-kill."""

    def __init__(self, remaining: float | None) -> None:
        self._remaining = remaining

    def remaining(self) -> float | None:
        return self._remaining

    def set(self, value: float | None) -> None:
        self._remaining = value


class _ExplodingWatchdog:
    def remaining(self):
        raise RuntimeError("watchdog unavailable")


class CountdownFormatterTests(unittest.TestCase):
    def test_formats_minutes_and_seconds(self):
        self.assertEqual(render_stream.format_stall_countdown(150.0), "kill in 2m30s")
        self.assertEqual(render_stream.format_stall_countdown(135.0), "kill in 2m15s")

    def test_formats_bare_seconds_under_a_minute(self):
        self.assertEqual(render_stream.format_stall_countdown(42.0), "kill in 42s")

    def test_names_the_progress_source(self):
        line = render_stream.format_stall_countdown(150.0, "subagent")
        self.assertIn("kill in 2m30s", line)
        self.assertIn("subagent", line)
        line = render_stream.format_stall_countdown(150.0, "stdout")
        self.assertIn("stdout", line)

    def test_disabled_watchdog_claims_no_countdown(self):
        # `--stall-timeout 0` disables the watchdog; claiming a countdown would be a lie.
        self.assertEqual(render_stream.format_stall_countdown(None), "")
        self.assertEqual(render_stream.format_stall_countdown(None, "stdout"), "")

    def test_never_renders_a_negative_countdown(self):
        self.assertEqual(render_stream.format_stall_countdown(-5.0), "kill in 0s")


class StatuslineCountdownTests(unittest.TestCase):
    """The LIVE display (Statusline) is what an operator actually sees during a turn."""

    def _line(self, watchdog, source=None):
        sl = render_stream.Statusline(
            pal=render_stream.Palette(False),
            stream=io.StringIO(),
            interval=0.0,
            setid="stallfp",
            id6="kaga7s",
            watchdog=watchdog,
        )
        if source:
            sl.touch(source)
        return sl.render_line()

    def test_countdown_appears_on_the_live_statusline(self):
        out = self._line(_FakeWatchdog(150.0))
        self.assertIn("kill in 2m30s", out)

    def test_countdown_follows_the_watchdogs_clock_not_its_own(self):
        # Drive the WATCHDOG's clock only. The statusline's own _last_activity is untouched,
        # so a display computing its own countdown would not move here.
        wd = _FakeWatchdog(150.0)
        sl = render_stream.Statusline(
            pal=render_stream.Palette(False),
            stream=io.StringIO(),
            interval=0.0,
            setid="s",
            id6="i",
            watchdog=wd,
        )
        first = sl.render_line()
        self.assertIn("kill in 2m30s", first)
        wd.set(135.0)
        second = sl.render_line()
        self.assertIn("kill in 2m15s", second)
        self.assertNotIn("kill in 2m30s", second)

    def test_countdown_decreases_across_successive_renders(self):
        wd = _FakeWatchdog(90.0)
        sl = render_stream.Statusline(
            pal=render_stream.Palette(False),
            stream=io.StringIO(),
            interval=0.0,
            setid="s",
            id6="i",
            watchdog=wd,
        )
        seen = []
        for remaining in (90.0, 75.0, 60.0, 45.0):
            wd.set(remaining)
            seen.append(sl.render_line())
        self.assertIn("kill in 1m30s", seen[0])
        self.assertIn("kill in 1m15s", seen[1])
        self.assertIn("kill in 1m00s", seen[2])
        # Under a minute the formatter renders bare seconds (see format_stall_countdown).
        self.assertIn("kill in 45s", seen[3])

    def test_progress_source_is_named_on_the_statusline(self):
        self.assertIn("subagent", self._line(_FakeWatchdog(120.0), "subagent"))
        self.assertIn("stdout", self._line(_FakeWatchdog(120.0), "stdout"))

    def test_no_countdown_when_watchdog_disabled(self):
        out = self._line(_FakeWatchdog(None))
        self.assertNotIn("kill in", out)

    def test_no_countdown_when_no_watchdog_supplied(self):
        out = self._line(None)
        self.assertNotIn("kill in", out)

    def test_a_broken_watchdog_degrades_silently(self):
        out = self._line(_ExplodingWatchdog())
        self.assertNotIn("kill in", out)
        self.assertIn("idle:", out)

    def test_layout_invariant_holds_with_the_countdown(self):
        # The pinned invariant: the two rendered lines stay the same width.
        l1, l2 = render_stream.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0 - 100,
            item_start_ts=1700000000.0 - 50,
            last_act_ts=1700000000.0 - 14,
            current_idx=1,
            total_items=1,
            setid="stallfp",
            id6="kaga7s",
            stall_remaining=150.0,
            progress_source="subagent",
        )
        self.assertEqual(len(l1), len(l2))
        self.assertIn("kill in 2m30s", l2)

    def test_layout_is_unchanged_when_no_countdown(self):
        # Additive: with no stall timeout the original pinned layout is preserved exactly.
        kw = dict(
            now_ts=1700000000.0,
            run_start_ts=1700000000.0 - (64 * 60 + 21),
            item_start_ts=1700000000.0 - (4 * 60 + 8),
            last_act_ts=1700000000.0 - 14,
            current_idx=1,
            total_items=1,
            setid="revgate",
            id6="7nkcgp",
        )
        l1, l2 = render_stream.format_statusline_lines(**kw)
        self.assertEqual(l2.split(" │ ")[1].strip(), "64m21s idle: 14s")
        self.assertEqual(len(l1), len(l2))


class HeartbeatCountdownTests(unittest.TestCase):
    """Heartbeat carries the same honest wording (and no bare 'still working')."""

    def _hb(self, watchdog, source=None):
        hb = render_stream.Heartbeat(
            render_stream.Palette(False),
            "kaga7s",
            io.StringIO(),
            interval=1.0,
            watchdog=watchdog,
        )
        if source:
            hb.touch(source)
        return hb

    def test_message_states_the_countdown(self):
        msg = self._hb(_FakeWatchdog(150.0)).format_message()
        self.assertIn("kill in 2m30s", msg)
        self.assertIn("no progress", msg)

    def test_message_names_the_progress_source(self):
        self.assertIn(
            "subagent", self._hb(_FakeWatchdog(60.0), "subagent").format_message()
        )

    def test_countdown_follows_the_watchdog(self):
        wd = _FakeWatchdog(150.0)
        hb = self._hb(wd)
        self.assertIn("kill in 2m30s", hb.format_message())
        wd.set(135.0)
        self.assertIn("kill in 2m15s", hb.format_message())

    def test_no_countdown_when_disabled(self):
        msg = self._hb(_FakeWatchdog(None)).format_message()
        self.assertNotIn("kill in", msg)

    def test_bare_still_working_wording_is_gone(self):
        # The exact misleading phrasing must not come back in either display.
        for msg in (
            self._hb(_FakeWatchdog(120.0)).format_message(),
            self._hb(_FakeWatchdog(None)).format_message(),
        ):
            self.assertNotIn("still working", msg)

    def test_no_driver_source_contains_the_misleading_phrase(self):
        import pathlib

        pkg = pathlib.Path(render_stream.__file__).parent
        offenders = [
            p.name
            for p in pkg.glob("*.py")
            if "still working on" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()

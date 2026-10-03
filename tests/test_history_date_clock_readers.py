"""Tests for history date clock reader timezone invariance (IPD 840y6i).

Asserts that staleness verdicts returned by attention._age_marker are invariant
under the reader's timezone by testing across UTC, east of UTC (XXX-20, UTC+20),
and west of UTC (XXX+12, UTC-12).

Subprocesses are used to isolate environment variables (TZ) so no in-worker
time.tzset() or os.environ mutation occurs under pytest-xdist.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_in_subprocess(code: str, args: list[str], tz: str) -> str:
    """Run a small python snippet in a subprocess with a specific TZ."""
    env = {
        **os.environ,
        "TZ": tz,
        "PYTHONPATH": str(REPO_ROOT),
        "AW_NO_REEXEC": "1",
    }
    proc = subprocess.run(
        [sys.executable, "-c", code, *args],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _get_observed_date(tz: str) -> date:
    """Query date.today() in a subprocess under the given timezone."""
    code = "from datetime import date; print(date.today().isoformat())"
    out = _run_in_subprocess(code, [], tz)
    return date.fromisoformat(out.strip())


def _call_age_marker_subprocess(
    last_history_at: Optional[str], tree: str, tz: str
) -> str:
    """Call attention._age_marker in a subprocess with the given TZ.

    Crucially, calls _age_marker WITHOUT a 'today' keyword argument so the test
    asserts on verdict invariance under reader timezone rather than signature errors.
    """
    code = (
        "import sys;"
        "from agent_workflows.attention import _age_marker;"
        "hist = None if sys.argv[1] == '__NONE__' else sys.argv[1];"
        "tree = sys.argv[2];"
        "sys.stdout.write(_age_marker(hist, tree))"
    )
    arg_hist = "__NONE__" if last_history_at is None else last_history_at
    return _run_in_subprocess(code, [arg_hist, tree], tz)


class TestHistoryDateClockReadersTimezoneInvariance(unittest.TestCase):
    """Verifies that attention._age_marker produces timezone-invariant staleness markers."""

    def test_timezone_invariance_east_and_west_boundaries(self):
        """Assert staleness verdicts are invariant under reader timezone across UTC, east, and west.

        East: XXX-20 (UTC+20)
        West: XXX+12 (UTC-12)
        """
        # 1. Measure observed dates under UTC, east (XXX-20), and west (XXX+12)
        utc_date = _get_observed_date("UTC")
        east_date = _get_observed_date("XXX-20")
        west_date = _get_observed_date("XXX+12")

        print(
            f"\n[Skew Window Observation] UTC: {utc_date.isoformat()}, "
            f"East (XXX-20, UTC+20): {east_date.isoformat()}, "
            f"West (XXX+12, UTC-12): {west_date.isoformat()}"
        )

        # Confirm that at least one timezone is in a skew window (dates differ)
        # to ensure the test never runs vacuously (F-09).
        self.assertTrue(
            east_date != utc_date or west_date != utc_date,
            f"Neither east ({east_date}) nor west ({west_date}) differed from UTC ({utc_date}); "
            "cannot verify timezone invariance without clock skew.",
        )

        # 2. Test boundary cohort:
        # Boundary 1: exactly 30 days before UTC date.
        # Under UTC clock, age_days == 30. Threshold is age_days > 30, so verdict is ''.
        # Under a reader ahead of UTC (e.g. XXX-20 tomorrow), age_days would be 31 -> '!'.
        d30 = (utc_date - timedelta(days=30)).isoformat()

        # Boundary 2: exactly 31 days before UTC date.
        # Under UTC clock, age_days == 31. Threshold is age_days > 30, so verdict is '!'.
        # Under a reader behind UTC (e.g. XXX+12 yesterday), age_days would be 30 -> ''.
        d31 = (utc_date - timedelta(days=31)).isoformat()

        # Midpoint / non-boundary dates:
        d10 = (utc_date - timedelta(days=10)).isoformat()  # Recent -> ''
        d400 = (utc_date - timedelta(days=400)).isoformat()  # Stale -> '!'

        test_cases = [
            ("boundary_30d_recent", d30, ""),
            ("boundary_31d_stale", d31, "!"),
            ("non_boundary_10d_recent", d10, ""),
            ("non_boundary_400d_stale", d400, "!"),
        ]

        for label, hist_date, expected_verdict in test_cases:
            utc_verdict = _call_age_marker_subprocess(hist_date, "plans", "UTC")
            east_verdict = _call_age_marker_subprocess(hist_date, "plans", "XXX-20")
            west_verdict = _call_age_marker_subprocess(hist_date, "plans", "XXX+12")

            self.assertEqual(
                utc_verdict,
                expected_verdict,
                f"[{label}] UTC verdict {utc_verdict!r} did not match expected {expected_verdict!r} for date {hist_date}",
            )
            self.assertEqual(
                east_verdict,
                expected_verdict,
                f"[{label}] East timezone XXX-20 (UTC+20) verdict {east_verdict!r} != expected {expected_verdict!r} for date {hist_date}",
            )
            self.assertEqual(
                west_verdict,
                expected_verdict,
                f"[{label}] West timezone XXX+12 (UTC-12) verdict {west_verdict!r} != expected {expected_verdict!r} for date {hist_date}",
            )

    def test_age_marker_injectable_today_seam(self):
        """Verify that _age_marker accepts an explicit injectable 'today' seam."""
        from agent_workflows.attention import _age_marker

        # Explicit reference date
        fixed_ref = date(2026, 6, 15)
        # 30 days before 2026-06-15 is 2026-05-16 -> age_days=30 -> ''
        self.assertEqual(_age_marker("2026-05-16", tree="plans", today=fixed_ref), "")
        # 31 days before 2026-06-15 is 2026-05-15 -> age_days=31 -> '!'
        self.assertEqual(_age_marker("2026-05-15", tree="plans", today=fixed_ref), "!")

        # Passing today=None defaults to the UTC clock
        utc_today = datetime.now(timezone.utc).date()
        d30 = (utc_today - timedelta(days=30)).isoformat()
        d31 = (utc_today - timedelta(days=31)).isoformat()
        self.assertEqual(_age_marker(d30, tree="plans", today=None), "")
        self.assertEqual(_age_marker(d31, tree="plans", today=None), "!")

    def test_age_marker_edge_cases_and_historyless_trees(self):
        """Verify None, malformed history dates, and history-less trees."""
        from agent_workflows.attention import _age_marker

        # History-less trees suppress '?'
        self.assertEqual(_age_marker(None, tree="actions"), "")
        self.assertEqual(_age_marker(None, tree="research"), "")

        # Normal trees return '?' on missing or malformed history
        self.assertEqual(_age_marker(None, tree="plans"), "?")
        self.assertEqual(_age_marker(None, tree="backlog"), "?")
        self.assertEqual(_age_marker("invalid-date", tree="plans"), "?")


if __name__ == "__main__":
    unittest.main()

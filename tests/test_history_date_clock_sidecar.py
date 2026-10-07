"""Tests verifying that the gitignored history sidecar is stamped with the UTC clock.

Spec 2vev8j Section 4.4 ("One timezone for every writer"):
"Every writer, tool and human-facing helper alike, records UTC; local time is a
RENDER-TIME concern only."

IPD dmrbqa: Put the gitignored history sidecar on the UTC clock so one event's
two copies cannot disagree by a day.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

from agent_workflows import record_history

SKEW_ZONES = [
    ("XXX-24", "east"),  # UTC+24: always +1 day ahead of UTC
    ("XXX+23:59", "west"),  # UTC-23:59: always -1 day behind UTC except 23:59-00:00 UTC
]


@contextlib.contextmanager
def temporary_timezone(tz: str):
    """Context manager setting process TZ with unconditional restoration in finally."""
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = tz
    time.tzset()
    try:
        yield
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        time.tzset()


class HistoryDateClockSidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        (self.root / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        (self.root / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        (self.root / ".aw" / "records" / "releases").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"], cwd=self.root, check=True
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _expected_utc_dates(self) -> tuple[set[str], set[str]]:
        """Return (iso_dates, compact_dates) tolerating execution crossing midnight UTC."""
        now_utc = dt.datetime.now(dt.timezone.utc)
        iso = {
            (now_utc - dt.timedelta(seconds=2)).strftime("%Y-%m-%d"),
            now_utc.strftime("%Y-%m-%d"),
            (now_utc + dt.timedelta(seconds=2)).strftime("%Y-%m-%d"),
        }
        compact = {d.replace("-", "") for d in iso}
        return iso, compact

    def _get_local_and_utc_dates(self, zone: str) -> tuple[str, str, str]:
        """Compute (local_iso, local_compact, utc_iso) for a timezone in a clean subprocess."""
        env = {**os.environ, "TZ": zone}
        cmd = [
            sys.executable,
            "-c",
            (
                "import datetime as dt; "
                "utc = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'); "
                "local = dt.date.today().strftime('%Y-%m-%d'); "
                "local_c = dt.date.today().strftime('%Y%m%d'); "
                "print(f'{local}|{local_c}|{utc}')"
            ),
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        local_iso, local_compact, utc_iso = res.stdout.strip().split("|")
        return local_iso, local_compact, utc_iso

    def test_backlog_set_inline_and_sidecar_agree_on_utc_under_skew_zones(self) -> None:
        """A real aw backlog set writes the same UTC date to both inline history and sidecar."""
        skew_window_entered_count = 0

        for zone, direction in SKEW_ZONES:
            with self.subTest(zone=zone, direction=direction):
                local_iso, local_compact, utc_iso = self._get_local_and_utc_dates(zone)
                print(
                    f"\n[test_backlog_set] zone={zone} ({direction}): local={local_iso} (compact={local_compact}), utc={utc_iso}"
                )

                # Prove skew window was entered
                if local_compact != utc_iso.replace("-", ""):
                    skew_window_entered_count += 1

                expected_iso, expected_compact = self._expected_utc_dates()

                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}

                # Create backlog item fixture
                slug = f"bk-{direction}-{zone.replace('/', '_').replace(':', '_').replace('+', 'p').replace('-', 'm')}"
                item_file = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-{slug}.backlog.md"
                )
                item_id6 = f"bk{direction[:4]}"
                item_file.write_text(
                    f"- Id: {item_id6}\n"
                    f"- Status: open\n"
                    f"- Set: testset\n"
                    f"- Priority: high\n"
                    f"- Work-Kind: bug\n"
                    f"- Summary: test item under {zone}\n\n"
                    f"## Workflow history\n"
                    f"- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )

                # Drive real aw backlog set via CLI in subprocess
                cmd = [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "backlog",
                    "set",
                    str(item_file),
                    "--status",
                    "open",
                    "--message",
                    f"probe-{direction}",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
                res = subprocess.run(cmd, env=env, capture_output=True, text=True)
                self.assertEqual(
                    res.returncode, 0, f"aw backlog set failed: stderr={res.stderr}"
                )

                # 1. Read inline history line
                item_text = item_file.read_text(encoding="utf-8")
                inline_lines = [
                    line
                    for line in item_text.splitlines()
                    if f"probe-{direction}" in line
                ]
                self.assertTrue(
                    inline_lines, f"Missing inline history line in:\n{item_text}"
                )
                inline_line = inline_lines[0]
                inline_date = inline_line.split()[1]

                # 2. Read sidecar history line
                sidecar_file = self.root / ".aw" / "records" / "history.jsonl"
                self.assertTrue(
                    sidecar_file.is_file(), "Sidecar file history.jsonl was not created"
                )
                sidecar_lines = [
                    json.loads(line)
                    for line in sidecar_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                matching_sidecar = [
                    rec
                    for rec in sidecar_lines
                    if rec.get("id6") == item_id6
                    and rec.get("message") == f"probe-{direction}"
                ]
                self.assertTrue(
                    matching_sidecar, f"Missing sidecar record for {item_id6}"
                )
                sidecar_rec = matching_sidecar[-1]
                sidecar_date = sidecar_rec["date"]

                print(
                    f"[test_backlog_set] zone={zone}: inline_date={inline_date}, sidecar_date={sidecar_date}"
                )

                # Assert both match expected UTC dates
                self.assertIn(
                    inline_date,
                    expected_iso,
                    f"Inline date {inline_date} not in expected UTC set {expected_iso}",
                )
                self.assertIn(
                    sidecar_date,
                    expected_compact,
                    f"Sidecar date {sidecar_date} not in expected UTC compact set {expected_compact}",
                )

                # Assert inline and sidecar agree on the same day
                self.assertEqual(
                    sidecar_date,
                    inline_date.replace("-", ""),
                    f"Disagreement between inline date ({inline_date}) and sidecar date ({sidecar_date}) under {zone}",
                )

        # Fail explicitly if neither zone entered skew
        self.assertGreater(
            skew_window_entered_count,
            0,
            "Neither east nor west zone entered a skew window; test proved nothing",
        )

    def test_explicit_date_precedence_in_append_and_record_rename(self) -> None:
        """Explicit date parameter takes precedence over the default in append and record_rename."""
        explicit_date = "20200101"

        # Direct call to append with explicit date
        record_history.append(
            self.root,
            id6="ex0001",
            tree="backlog",
            workflow="aw test",
            actor="test-actor",
            message="explicit date append test",
            date=explicit_date,
        )

        # Direct call to record_rename with explicit date
        record_history.record_rename(
            self.root,
            tree="specs",
            verb="rename",
            actor="test-actor",
            from_name="old-spec",
            to_name="20261001-ex0002-01-ex0002-new-spec.spec.md",
            message="explicit date rename test",
            date=explicit_date,
        )

        records = record_history.read_all(self.root)
        append_rec = [r for r in records if r.get("id6") == "ex0001"][0]
        rename_rec = [r for r in records if r.get("id6") == "ex0002"][0]

        self.assertEqual(append_rec["date"], explicit_date)
        self.assertEqual(rename_rec["date"], explicit_date)

    def test_sidecar_schema_and_key_order(self) -> None:
        """Sidecar records preserve schema and exact key order."""
        # Append status record
        record_history.append(
            self.root,
            id6="sc0001",
            tree="backlog",
            workflow="aw test",
            actor="test-actor",
            message="schema test",
        )
        # Append rename record
        record_history.record_rename(
            self.root,
            tree="specs",
            verb="rename",
            actor="test-actor",
            from_name="old-name",
            to_name="20261001-sc0002-01-sc0002-new-name.spec.md",
            message="rename test",
        )

        sidecar_file = self.root / ".aw" / "records" / "history.jsonl"
        lines = [
            line.strip()
            for line in sidecar_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 2)

        raw_rec1 = json.loads(lines[0])
        self.assertEqual(
            list(raw_rec1.keys()),
            ["id6", "date", "tree", "workflow", "actor", "message"],
        )

        raw_rec2 = json.loads(lines[1])
        self.assertEqual(
            list(raw_rec2.keys()),
            [
                "id6",
                "date",
                "tree",
                "workflow",
                "actor",
                "message",
                "verb",
                "from_name",
                "to_name",
            ],
        )

    def test_in_process_temporary_timezone_restoration(self) -> None:
        """temporary_timezone cleanly restores original ambient timezone without leaking."""
        original_tz = os.environ.get("TZ")
        with temporary_timezone("XXX-24"):
            self.assertEqual(os.environ.get("TZ"), "XXX-24")
        self.assertEqual(os.environ.get("TZ"), original_tz)

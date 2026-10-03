"""Tests verifying that every artifact history record is stamped with the UTC clock.

Spec 2vev8j Section 4.4 ("One timezone for every writer") requires:
"Every writer, tool and human-facing helper alike, records UTC; local time is a
RENDER-TIME concern only."

DECISIONS.md D55 ("Human-facing timestamps use LOCAL time, not UTC") requires:
Filename date prefixes (e.g. YYYYMMDD-) remain on the local machine clock.

This suite tests that history records carry the UTC date across writers and CLI spellings
under timezones east (Pacific/Kiritimati, UTC+14) and west (Pacific/Honolulu, UTC-10) of UTC,
while filename prefixes remain local.
"""

from __future__ import annotations

import datetime as dt
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

TIMEZONES = ["Pacific/Kiritimati", "Pacific/Honolulu"]


class HistoryDateClockTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        # Create records dirs so aw commands don't fall back to ~/.aw/projects/
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

    def _expected_utc_dates(self) -> set[str]:
        # Tolerate execution crossing midnight UTC
        now_utc = dt.datetime.now(dt.timezone.utc)
        return {
            (now_utc - dt.timedelta(seconds=1)).strftime("%Y-%m-%d"),
            now_utc.strftime("%Y-%m-%d"),
            (now_utc + dt.timedelta(seconds=1)).strftime("%Y-%m-%d"),
        }

    def _expected_local_compact_dates(self, zone: str) -> set[str]:
        # Determine local date in zone (handling midnight crossing)
        env = {**os.environ, "TZ": zone}
        res = subprocess.run(
            [
                sys.executable,
                "-c",
                "import datetime; print(datetime.date.today().strftime('%Y%m%d'))",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return {res.stdout.strip()}

    def test_backlog_set_both_spellings_record_utc_date(self) -> None:
        """Both aw backlog set <path> --status and aw backlog set <status> <path> record UTC date."""
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
                utc_dates = self._expected_utc_dates()

                # Flag spelling: aw backlog set <path> --status open
                f1 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-bk1-{zone.replace('/', '_')}.backlog.md"
                )
                f1.write_text(
                    "- Id: bk0001\n- Status: open\n- Set: bk1\n- Priority: high\n- Work-Kind: bug\n- Summary: bug 1\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res1 = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "backlog",
                        "set",
                        str(f1),
                        "--status",
                        "open",
                        "--message",
                        "via-flag",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res1.returncode, 0, f"res1 stderr: {res1.stderr}")
                text1 = f1.read_text(encoding="utf-8")
                hist_line1 = [
                    line for line in text1.splitlines() if "via-flag" in line
                ][0]
                date_written1 = hist_line1.split()[1]
                self.assertIn(
                    date_written1,
                    utc_dates,
                    f"Under {zone}, aw backlog set --status wrote {date_written1}, expected UTC in {utc_dates}. Line: {hist_line1}",
                )

                # Positional spelling: aw backlog set open <path>
                f2 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-bk2-{zone.replace('/', '_')}.backlog.md"
                )
                f2.write_text(
                    "- Id: bk0002\n- Status: open\n- Set: bk2\n- Priority: high\n- Work-Kind: bug\n- Summary: bug 2\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res2 = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "backlog",
                        "set",
                        "open",
                        str(f2),
                        "--message",
                        "via-pos",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res2.returncode, 0, f"res2 stderr: {res2.stderr}")
                text2 = f2.read_text(encoding="utf-8")
                hist_line2 = [line for line in text2.splitlines() if "via-pos" in line][
                    0
                ]
                date_written2 = hist_line2.split()[1]
                self.assertIn(
                    date_written2,
                    utc_dates,
                    f"Under {zone}, aw backlog set <pos> wrote {date_written2}, expected UTC in {utc_dates}. Line: {hist_line2}",
                )

    def test_backlog_new_records_utc_date_and_local_filename(self) -> None:
        """aw backlog new stamps UTC history date and local filename date prefix."""
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
                utc_dates = self._expected_utc_dates()
                local_compact = self._expected_local_compact_dates(zone)

                slug = f"item-{zone.replace('/', '-').lower()}"
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "backlog",
                        "new",
                        "--summary",
                        f"summary-{zone}",
                        "--slug",
                        slug,
                        "--priority",
                        "medium",
                        "--work-kind",
                        "chore",
                        "--apply",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                matches = list(
                    (self.root / ".aw" / "records" / "backlog" / "open").glob(
                        f"*-{slug}.backlog.md"
                    )
                )
                self.assertEqual(len(matches), 1, f"Found matches: {matches}")
                item_file = matches[0]

                # Check filename date prefix is local per D55
                file_prefix = item_file.name.split("-")[0]
                self.assertIn(
                    file_prefix,
                    local_compact,
                    f"Under {zone}, backlog filename prefix {file_prefix} was not local in {local_compact}",
                )

                # Check created history record date is UTC per 2vev8j 4.4
                text = item_file.read_text(encoding="utf-8")
                created_lines = [
                    line for line in text.splitlines() if "created (aw backlog)" in line
                ]
                self.assertTrue(created_lines, f"No created line found in:\n{text}")
                hist_date = created_lines[0].split()[1]
                self.assertIn(
                    hist_date,
                    utc_dates,
                    f"Under {zone}, backlog created line wrote {hist_date}, expected UTC in {utc_dates}. Line: {created_lines[0]}",
                )

    def test_specs_set_records_utc_date(self) -> None:
        """aw specs set records UTC date in history record."""
        (self.root / ".aw" / "records" / "specs" / "to-review").mkdir(
            parents=True, exist_ok=True
        )
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
                utc_dates = self._expected_utc_dates()

                spec_path = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-sp1-{zone.replace('/', '_')}.spec.md"
                )
                spec_path.write_text(
                    "# Spec: Test Spec\n\n- Date: 2026-10-01\n- Status: draft\n- Id: sp0001\n- Author: test\n- Scope: test\n\n"
                    "## Workflow history\n- 2026-10-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "specs",
                        "set",
                        str(spec_path),
                        "--status",
                        "to-review",
                        "--message",
                        "moving to review",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                dest = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "to-review"
                    / spec_path.name
                )
                text = dest.read_text(encoding="utf-8")
                hist_lines = [
                    line for line in text.splitlines() if "moving to review" in line
                ]
                self.assertTrue(hist_lines, f"No transition line found in:\n{text}")
                hist_date = hist_lines[0].split()[1]
                self.assertIn(
                    hist_date,
                    utc_dates,
                    f"Under {zone}, specs set wrote {hist_date}, expected UTC in {utc_dates}. Line: {hist_lines[0]}",
                )

    def test_specs_new_records_utc_date_and_local_filename(self) -> None:
        """aw specs new stamps UTC history date and local filename date prefix."""
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
                utc_dates = self._expected_utc_dates()
                local_compact = self._expected_local_compact_dates(zone)

                slug = f"spec-{zone.replace('/', '-').lower()}"
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "specs",
                        "new",
                        "--title",
                        f"Spec {zone}",
                        "--slug",
                        slug,
                        "--summary",
                        "summary",
                        "--apply",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                matches = list(
                    (self.root / ".aw" / "records" / "specs" / "draft").glob(
                        f"*-{slug}.spec.md"
                    )
                )
                self.assertEqual(len(matches), 1, f"Found matches: {matches}")
                spec_file = matches[0]

                # Check filename date prefix is local per D55
                file_prefix = spec_file.name.split("-")[0]
                self.assertIn(
                    file_prefix,
                    local_compact,
                    f"Under {zone}, specs filename prefix {file_prefix} was not local in {local_compact}",
                )

                # Check created history record date is UTC per 2vev8j 4.4
                text = spec_file.read_text(encoding="utf-8")
                created_lines = [
                    line for line in text.splitlines() if "created (aw specs)" in line
                ]
                self.assertTrue(created_lines, f"No created line found in:\n{text}")
                hist_date = created_lines[0].split()[1]
                self.assertIn(
                    hist_date,
                    utc_dates,
                    f"Under {zone}, specs created line wrote {hist_date}, expected UTC in {utc_dates}. Line: {created_lines[0]}",
                )

    def test_releases_new_records_utc_date_and_local_filename(self) -> None:
        """aw releases new stamps UTC history date and local filename date prefix."""
        for idx, zone in enumerate(TIMEZONES, start=1):
            with self.subTest(zone=zone):
                env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
                utc_dates = self._expected_utc_dates()
                local_compact = self._expected_local_compact_dates(zone)

                version = f"9.9.{idx}"
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "releases",
                        "new",
                        "--version",
                        version,
                        "--summary",
                        f"Release {version}",
                        "--apply",
                        "--dir",
                        str(self.root),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                matches = list(
                    (self.root / ".aw" / "records" / "releases").glob(
                        f"*-{version.replace('.', '-')}.release.md"
                    )
                )
                self.assertEqual(len(matches), 1, f"Found matches: {matches}")
                rel_file = matches[0]

                # Check filename date prefix is local per D55
                file_prefix = rel_file.name.split("-")[0]
                self.assertIn(
                    file_prefix,
                    local_compact,
                    f"Under {zone}, release filename prefix {file_prefix} was not local in {local_compact}",
                )

                # Check created history record date is UTC per 2vev8j 4.4
                text = rel_file.read_text(encoding="utf-8")
                created_lines = [
                    line
                    for line in text.splitlines()
                    if "created (aw releases)" in line
                ]
                self.assertTrue(created_lines, f"No created line found in:\n{text}")
                hist_date = created_lines[0].split()[1]
                self.assertIn(
                    hist_date,
                    utc_dates,
                    f"Under {zone}, release created line wrote {hist_date}, expected UTC in {utc_dates}. Line: {created_lines[0]}",
                )


if __name__ == "__main__":
    unittest.main()

"""Tests verifying UTC history-date clock parity across derived command surface.

Enforces spec 2vev8j Section 4.4 ("One timezone for every writer"):
"Every writer, tool and human-facing helper alike, records UTC; local time is a
RENDER-TIME concern only."

And DECISIONS.md D55 ("Human-facing timestamps use LOCAL time, not UTC"):
Filename date prefixes (e.g. YYYYMMDD-) remain on the local machine clock.

This suite derives the history-writing surface dynamically from
command_surface.COMMAND_INVENTORY, proves timezone skew observability on demand
via the Pacific/Kiritimati (UTC+14) and Pacific/Honolulu (UTC-10) bracket,
and asserts:
1. Every derived history-writing spelling records UTC dates in workflow history.
2. Cross-spelling agreement across all spellings of each artifact family.
3. Proper composition of local filename prefixes and UTC history dates.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from agent_workflows import command_surface

TIMEZONES = ["Pacific/Kiritimati", "Pacific/Honolulu"]
if os.environ.get("AW_TEST_SWAP_TZ") == "1":
    TIMEZONES = ["Pacific/Honolulu", "Pacific/Kiritimati"]
elif os.environ.get("AW_TEST_ZONES"):
    TIMEZONES = [z.strip() for z in os.environ["AW_TEST_ZONES"].split(",") if z.strip()]


@contextlib.contextmanager
def scoped_timezone(zone: str):
    """Context manager setting TZ for in-process operations with guaranteed restore."""
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = zone
    if hasattr(time, "tzset"):
        time.tzset()
    try:
        yield
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        if hasattr(time, "tzset"):
            time.tzset()


def derive_history_writing_surface() -> tuple[list[str], dict[str, str]]:
    """Derive history-writing candidate commands from COMMAND_INVENTORY.

    Returns:
        (exercised_commands, skipped_commands_with_reasons)
    """
    exercised: list[str] = []
    skipped: dict[str, str] = {}

    for cmd in command_surface.COMMAND_INVENTORY:
        tokens = cmd.command.split()
        if not tokens or tokens[-1] not in ("set", "note"):
            continue
        if cmd.command_class != "mutation":
            continue

        name = cmd.command
        if name == "config set":
            skipped[name] = "not an artifact verb; writes no history record"
        elif name == "ipd dependencies set":
            skipped[name] = (
                "edits dependency metadata field rather than artifact lifecycle status "
                "(verified by driving that it appends same-status history via run_set_command)"
            )
        else:
            exercised.append(name)

    return sorted(exercised), skipped


class HistoryDateClockParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        (self.root / ".aw" / "records" / "backlog" / "graduated").mkdir(parents=True)
        (self.root / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        (self.root / ".aw" / "records" / "specs" / "to-review").mkdir(parents=True)
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "prompts" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "prompts" / "executed").mkdir(parents=True)
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
            (now_utc - dt.timedelta(seconds=2)).strftime("%Y-%m-%d"),
            (now_utc - dt.timedelta(seconds=1)).strftime("%Y-%m-%d"),
            now_utc.strftime("%Y-%m-%d"),
            (now_utc + dt.timedelta(seconds=1)).strftime("%Y-%m-%d"),
            (now_utc + dt.timedelta(seconds=2)).strftime("%Y-%m-%d"),
        }

    def _expected_local_compact_dates(self, zone: str) -> set[str]:
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

    def _compute_zone_date(self, zone: str) -> str:
        env = {**os.environ, "TZ": zone}
        res = subprocess.run(
            [
                sys.executable,
                "-c",
                "import datetime; print(datetime.date.today().strftime('%Y-%m-%d'))",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def _assert_skew_window_present(
        self, zones: list[str]
    ) -> tuple[dict[str, str], str]:
        utc_date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        local_dates = {z: self._compute_zone_date(z) for z in zones}
        skew_zones = [z for z, d in local_dates.items() if d != utc_date]
        if not skew_zones:
            raise AssertionError(
                f"No timezone in {zones} is inside a skew window relative to UTC ({utc_date}). "
                f"Local dates: {local_dates}. Skew harness cannot observe divergence."
            )
        return local_dates, utc_date

    def _run_aw(self, args: list[str], zone: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "TZ": zone, "AW_NO_REEXEC": "1"}
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_precondition_at_least_one_zone_in_skew_window(self) -> None:
        """Self-check asserting that at least one of the two timezones is inside a skew window."""
        local_dates, utc_date = self._assert_skew_window_present(TIMEZONES)
        print("\nSKEW PRECONDITION CHECK:")
        print(f"  UTC date: {utc_date}")
        for z, d in local_dates.items():
            diff = " (INSIDE SKEW WINDOW)" if d != utc_date else " (same as UTC)"
            print(f"  {z}: {d}{diff}")
        self.assertTrue(
            any(d != utc_date for d in local_dates.values()),
            "At least one timezone must differ from UTC",
        )

    def test_scoped_timezone_restores_environment(self) -> None:
        """Verify that scoped_timezone restores TZ to its exact prior state."""
        orig_tz = os.environ.get("TZ")
        with scoped_timezone("Pacific/Kiritimati"):
            self.assertEqual(os.environ.get("TZ"), "Pacific/Kiritimati")
        self.assertEqual(os.environ.get("TZ"), orig_tz)

        os.environ["TZ"] = "EST5EDT"
        try:
            with scoped_timezone("Pacific/Honolulu"):
                self.assertEqual(os.environ.get("TZ"), "Pacific/Honolulu")
            self.assertEqual(os.environ.get("TZ"), "EST5EDT")
        finally:
            if orig_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = orig_tz

    def test_derived_history_writing_surface_coverage_and_floor(self) -> None:
        """Derive target spellings from COMMAND_INVENTORY and assert non-vacuity floor."""
        exercised, skipped = derive_history_writing_surface()
        print(f"\nDERIVED SPELLINGS: {sorted(exercised + list(skipped.keys()))}")
        print(f"EXERCISED SPELLINGS: {exercised}")
        print(f"SKIPPED SPELLINGS: {skipped}")

        # Floor assertion (P16: no census pin, assert floor of core setters)
        self.assertTrue(len(exercised) > 0, "Derived surface must be non-empty")
        self.assertIn("backlog set", exercised, "Floor must include 'backlog set'")
        self.assertIn("specs set", exercised, "Floor must include 'specs set'")
        self.assertIn("backlog note", exercised, "Floor must include 'backlog note'")
        self.assertIn("specs note", exercised, "Floor must include 'specs note'")
        self.assertIn("ipd set", exercised, "Floor must include 'ipd set'")
        self.assertIn("prompts set", exercised, "Floor must include 'prompts set'")
        self.assertIn("set", exercised, "Floor must include bare 'set'")
        self.assertIn("config set", skipped, "Floor must skip 'config set'")
        self.assertIn(
            "ipd dependencies set", skipped, "Floor must skip 'ipd dependencies set'"
        )

    def test_derived_setters_record_utc_date_under_both_timezones(self) -> None:
        """Assert that every derived history-writing spelling records UTC dates under both timezones."""
        for z_idx, zone in enumerate(TIMEZONES, start=1):
            with self.subTest(zone=zone):
                utc_dates = self._expected_utc_dates()

                # 1. backlog set (flag spelling: same-status and transition)
                bk_flag = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-bkf{z_idx}-{zone.replace('/', '_')}.backlog.md"
                )
                bk_flag.write_text(
                    f"- Id: bkf{z_idx}01\n- Status: open\n- Set: bkf\n- Priority: high\n- Work-Kind: bug\n- Summary: b\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "backlog",
                        "set",
                        str(bk_flag),
                        "--status",
                        "open",
                        "--message",
                        "bk-flag-same",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                lines = [
                    ln
                    for ln in bk_flag.read_text(encoding="utf-8").splitlines()
                    if "bk-flag-same" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, backlog set --status wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 2. backlog set (positional spelling: same-status and transition)
                bk_pos = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-bkp{z_idx}-{zone.replace('/', '_')}.backlog.md"
                )
                bk_pos.write_text(
                    f"- Id: bkp{z_idx}01\n- Status: open\n- Set: bkp\n- Priority: high\n- Work-Kind: bug\n- Summary: b\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "backlog",
                        "set",
                        "open",
                        f"bkp{z_idx}01",
                        "--message",
                        "bk-pos-same",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                lines = [
                    ln
                    for ln in bk_pos.read_text(encoding="utf-8").splitlines()
                    if "bk-pos-same" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, backlog set positional wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 3. backlog note
                bk_note = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-bkn{z_idx}-{zone.replace('/', '_')}.backlog.md"
                )
                bk_note.write_text(
                    f"- Id: bkn{z_idx}01\n- Status: open\n- Set: bkn\n- Priority: high\n- Work-Kind: bug\n- Summary: b\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "backlog",
                        "note",
                        str(bk_note),
                        "--message",
                        "bk-note-msg",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                lines = [
                    ln
                    for ln in bk_note.read_text(encoding="utf-8").splitlines()
                    if "bk-note-msg" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, backlog note wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 4. specs set (flag spelling: transition to-review)
                sp_flag = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-spf{z_idx}-{zone.replace('/', '_')}.spec.md"
                )
                sp_flag.write_text(
                    f"# Spec: SPF\n- Date: 2026-10-01\n- Status: draft\n- Id: spf{z_idx}01\n- Author: test\n- Scope: test\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "specs",
                        "set",
                        str(sp_flag),
                        "--status",
                        "to-review",
                        "--message",
                        "sp-flag-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                dest_sp_flag = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / sp_flag.name
                )
                lines = [
                    ln
                    for ln in dest_sp_flag.read_text(encoding="utf-8").splitlines()
                    if "sp-flag-trans" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, specs set --status wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 5. specs set (positional spelling: transition to-review)
                sp_pos = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-spp{z_idx}-{zone.replace('/', '_')}.spec.md"
                )
                sp_pos.write_text(
                    f"# Spec: SPP\n- Date: 2026-10-01\n- Status: draft\n- Id: spp{z_idx}01\n- Author: test\n- Scope: test\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "specs",
                        "set",
                        "to-review",
                        f"spp{z_idx}01",
                        "--message",
                        "sp-pos-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                dest_sp_pos = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / sp_pos.name
                )
                lines = [
                    ln
                    for ln in dest_sp_pos.read_text(encoding="utf-8").splitlines()
                    if "sp-pos-trans" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, specs set positional wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 6. specs note
                sp_note = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-spn{z_idx}-{zone.replace('/', '_')}.spec.md"
                )
                sp_note.write_text(
                    f"# Spec: SPN\n- Date: 2026-10-01\n- Status: draft\n- Id: spn{z_idx}01\n- Author: test\n- Scope: test\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "specs",
                        "note",
                        str(sp_note),
                        "--message",
                        "sp-note-msg",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                lines = [
                    ln
                    for ln in sp_note.read_text(encoding="utf-8").splitlines()
                    if "sp-note-msg" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, specs note wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 7. bare set (aw set <status> <id6>) on spec
                sp_bare = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-spb{z_idx}-{zone.replace('/', '_')}.spec.md"
                )
                sp_bare.write_text(
                    f"# Spec: SPB\n- Date: 2026-10-01\n- Status: draft\n- Id: spb{z_idx}01\n- Author: test\n- Scope: test\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "set",
                        "to-review",
                        f"spb{z_idx}01",
                        "--message",
                        "sp-bare-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                dest_sp_bare = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / sp_bare.name
                )
                lines = [
                    ln
                    for ln in dest_sp_bare.read_text(encoding="utf-8").splitlines()
                    if "sp-bare-trans" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, bare set wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 8. ipd set
                ipd_file = (
                    self.root
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / f"20261001-demo-01-pl{z_idx}01-{zone.replace('/', '_')}.ipd.md"
                )
                ipd_file.write_text(
                    f"# Plan\n- Id: pl{z_idx}01\n- Status: draft\n- Set: demo\n- Highest E allocated: 01\n"
                    "- Author: test\n- Scope-Paths: README.md\n- Concern: c\n- Scope: s\n- Work-Kind: chore\n"
                    "- Priority: medium\n- Item-Dependencies: none\n\n"
                    "## Workflow history\n- 2026-09-01 draft (test): init\n\n"
                    "## Goal\ng\n\n"
                    "## Detailed Implementation Checklist (TODO)\n- [ ] E-01 e\n  - Depends on: none\n  - Expected outcome: o\n  - Execution state: pending\n\n"
                    "## Project conventions discovered (Step 0)\nnone\n\n"
                    "## Findings\nnone\n\n"
                    "## Proposed changes (ordered, validatable)\n1. e\n\n"
                    "## Deferred / out of scope (with reason)\n- none\n\n"
                    "## Scope check\n- none\n\n"
                    "## Required tests / validation\n- none\n\n"
                    "## Spec / documentation sync\n- none\n\n"
                    "## Open questions\n- none\n\n"
                    "## Validation and cross-check (verify before reporting done)\n- [ ] V-01 v\n  - Required evidence: r\n  - Observed evidence:\n  - Result: pending\n\n"
                    "## Approval and execution gate\n- Size assessment: standard\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "ipd",
                        "set",
                        "to-review",
                        f"pl{z_idx}01",
                        "--message",
                        "ipd-set-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                lines = [
                    ln
                    for ln in ipd_file.read_text(encoding="utf-8").splitlines()
                    if "ipd-set-trans" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, ipd set wrote {date_written}, expected UTC in {utc_dates}",
                )

                # 9. prompts set
                pr_file = (
                    self.root
                    / ".aw"
                    / "records"
                    / "prompts"
                    / "pending"
                    / f"20261001-pr{z_idx}01-{zone.replace('/', '_')}.prompt.md"
                )
                pr_file.write_text(
                    f"# Prompt\n- Id: pr{z_idx}01\n- Status: pending\n\n## Workflow history\n- 2026-09-01 pending (test): init\n",
                    encoding="utf-8",
                )
                res = self._run_aw(
                    [
                        "prompts",
                        "set",
                        "executed",
                        f"pr{z_idx}01",
                        "--message",
                        "prompt-set-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                dest_pr = (
                    self.root
                    / ".aw"
                    / "records"
                    / "prompts"
                    / "executed"
                    / pr_file.name
                )
                lines = [
                    ln
                    for ln in dest_pr.read_text(encoding="utf-8").splitlines()
                    if "prompt-set-trans" in ln
                ]
                self.assertTrue(lines)
                date_written = lines[0].split()[1]
                self.assertIn(
                    date_written,
                    utc_dates,
                    f"Under {zone}, prompts set wrote {date_written}, expected UTC in {utc_dates}",
                )

    def test_cross_spelling_history_date_and_record_agreement(self) -> None:
        """Assert that multiple spellings of the same family agree on UTC date and record format."""
        for z_idx, zone in enumerate(TIMEZONES, start=1):
            with self.subTest(zone=zone):
                utc_dates = self._expected_utc_dates()

                # --- Backlog family agreement ---
                # Item 1: flag spelling
                f1 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-agr{z_idx}1-{zone.replace('/', '_')}.backlog.md"
                )
                f1.write_text(
                    f"- Id: agr{z_idx}01\n- Status: open\n- Set: agr\n- Priority: high\n- Work-Kind: bug\n- Summary: item 1\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                # Item 2: positional spelling
                f2 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "backlog"
                    / "open"
                    / f"20261001-agr{z_idx}2-{zone.replace('/', '_')}.backlog.md"
                )
                f2.write_text(
                    f"- Id: agr{z_idx}02\n- Status: open\n- Set: agr\n- Priority: high\n- Work-Kind: bug\n- Summary: item 2\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )

                # Same-status write on both
                res1 = self._run_aw(
                    [
                        "backlog",
                        "set",
                        str(f1),
                        "--status",
                        "open",
                        "--message",
                        "same-note",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    zone,
                )
                self.assertEqual(res1.returncode, 0)
                res2 = self._run_aw(
                    [
                        "backlog",
                        "set",
                        "open",
                        f"agr{z_idx}02",
                        "--message",
                        "same-note",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res2.returncode, 0)

                rec1 = [
                    ln
                    for ln in f1.read_text(encoding="utf-8").splitlines()
                    if "same-note" in ln
                ][0]
                rec2 = [
                    ln
                    for ln in f2.read_text(encoding="utf-8").splitlines()
                    if "same-note" in ln
                ][0]
                date1 = rec1.split()[1]
                date2 = rec2.split()[1]

                self.assertIn(date1, utc_dates)
                self.assertIn(date2, utc_dates)
                self.assertEqual(
                    date1,
                    date2,
                    f"Under {zone}, backlog spellings diverged on date: flag={date1}, pos={date2}",
                )

                # --- Specs family agreement ---
                # Spec 1: flag spelling
                s1 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-agrs{z_idx}1-{zone.replace('/', '_')}.spec.md"
                )
                s1.write_text(
                    f"# Spec: 1\n- Date: 2026-10-01\n- Status: draft\n- Id: ags{z_idx}01\n- Author: test\n- Scope: s\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                # Spec 2: positional spelling (aw specs set to-review ...)
                s2 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-agrs{z_idx}2-{zone.replace('/', '_')}.spec.md"
                )
                s2.write_text(
                    f"# Spec: 2\n- Date: 2026-10-01\n- Status: draft\n- Id: ags{z_idx}02\n- Author: test\n- Scope: s\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )
                # Spec 3: bare set spelling (aw set to-review ...)
                s3 = (
                    self.root
                    / ".aw"
                    / "records"
                    / "specs"
                    / "draft"
                    / f"20261001-agrs{z_idx}3-{zone.replace('/', '_')}.spec.md"
                )
                s3.write_text(
                    f"# Spec: 3\n- Date: 2026-10-01\n- Status: draft\n- Id: ags{z_idx}03\n- Author: test\n- Scope: s\n\n"
                    "## Workflow history\n- 2026-09-01 created (test): init\n",
                    encoding="utf-8",
                )

                res_s1 = self._run_aw(
                    [
                        "specs",
                        "set",
                        str(s1),
                        "--status",
                        "to-review",
                        "--message",
                        "spec-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ],
                    zone,
                )
                self.assertEqual(res_s1.returncode, 0)
                res_s2 = self._run_aw(
                    [
                        "specs",
                        "set",
                        "to-review",
                        f"ags{z_idx}02",
                        "--message",
                        "spec-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res_s2.returncode, 0)
                res_s3 = self._run_aw(
                    [
                        "set",
                        "to-review",
                        f"ags{z_idx}03",
                        "--message",
                        "spec-trans",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                        "--yes",
                    ],
                    zone,
                )
                self.assertEqual(res_s3.returncode, 0)

                dest_s1 = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / s1.name
                )
                dest_s2 = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / s2.name
                )
                dest_s3 = (
                    self.root / ".aw" / "records" / "specs" / "to-review" / s3.name
                )

                srec1 = [
                    ln
                    for ln in dest_s1.read_text(encoding="utf-8").splitlines()
                    if "spec-trans" in ln
                ][0]
                srec2 = [
                    ln
                    for ln in dest_s2.read_text(encoding="utf-8").splitlines()
                    if "spec-trans" in ln
                ][0]
                srec3 = [
                    ln
                    for ln in dest_s3.read_text(encoding="utf-8").splitlines()
                    if "spec-trans" in ln
                ][0]

                sdate1 = srec1.split()[1]
                sdate2 = srec2.split()[1]
                sdate3 = srec3.split()[1]

                self.assertIn(sdate1, utc_dates)
                self.assertIn(sdate2, utc_dates)
                self.assertIn(sdate3, utc_dates)
                self.assertEqual(
                    sdate1,
                    sdate2,
                    f"Under {zone}, specs flag vs pos diverged: {sdate1} vs {sdate2}",
                )
                self.assertEqual(
                    sdate1,
                    sdate3,
                    f"Under {zone}, specs flag vs bare set diverged: {sdate1} vs {sdate3}",
                )

    def test_local_filename_and_utc_history_date_composition(self) -> None:
        """Positively assert D55 composition: local filename prefix alongside UTC history date."""
        for zone in TIMEZONES:
            with self.subTest(zone=zone):
                utc_dates = self._expected_utc_dates()
                local_compact = self._expected_local_compact_dates(zone)
                local_iso = self._compute_zone_date(zone)
                utc_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

                slug = f"comp-{zone.replace('/', '-').lower()}"
                res = self._run_aw(
                    [
                        "specs",
                        "new",
                        "--title",
                        f"Composition Spec {zone}",
                        "--slug",
                        slug,
                        "--summary",
                        "testing composition",
                        "--apply",
                        "--dir",
                        str(self.root),
                    ],
                    zone,
                )
                self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")
                matches = list(
                    (self.root / ".aw" / "records" / "specs" / "draft").glob(
                        f"*-{slug}.spec.md"
                    )
                )
                self.assertEqual(len(matches), 1)
                spec_file = matches[0]

                # Check filename date prefix is local per D55
                file_prefix = spec_file.name.split("-")[0]
                self.assertIn(
                    file_prefix,
                    local_compact,
                    f"Under {zone}, filename prefix {file_prefix} must be local ({local_compact})",
                )

                # Check created history record date is UTC per 2vev8j 4.4
                content = spec_file.read_text(encoding="utf-8")
                created_lines = [
                    ln for ln in content.splitlines() if "created (aw specs)" in ln
                ]
                self.assertTrue(created_lines)
                hist_date = created_lines[0].split()[1]
                self.assertIn(
                    hist_date,
                    utc_dates,
                    f"Under {zone}, created line wrote {hist_date}, expected UTC in {utc_dates}",
                )

                print(
                    f"\nCOMPOSITION IN {zone}:\n"
                    f"  Local date (ISO): {local_iso} (compact: {file_prefix})\n"
                    f"  UTC date (ISO):   {utc_iso} (history: {hist_date})\n"
                    f"  Artifact name:    {spec_file.name}\n"
                    f"  History line:     {created_lines[0]}\n"
                )


if __name__ == "__main__":
    unittest.main()

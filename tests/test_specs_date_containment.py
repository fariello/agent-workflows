"""Tests for specs --date containment, validation, and non-regressions (IPD ribg85).

Covers:
- E-01 / V-01: --date format and calendar validation (refuses ../ traversal, 9999-99-99, notadate, 2026-9-9).
- E-02 / V-02: destination containment defense-in-depth (Path.relative_to / ValueError check before dry-run branch).
- E-03 / V-03: pinning escape behavior with nested fixture and bounded traversal depth.
- E-04 / V-04: fabricated date refusal, F-05 checker asymmetry, and non-regression matrix.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Tuple
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows import specs


class _ContainmentRepoTestCase(unittest.TestCase):
    """Base fixture for date containment tests with bounded nesting depth.

    SAFETY REQUIREMENT (IPD ribg85 E-03, F-03, F-12):
    The fixture is nested several directories deep inside self.tmp_base:
        <tmp_base>/nest1/nest2/nest3/repo
    whose records directory is:
        repo/.aw/records/specs/draft

    From draft/:
      - 4 `../` segments reach `repo/` (repo root)
      - 5 `../` reach `nest3/`
      - 6 `../` reach `nest2/`
      - 7 `../` reach `nest1/`
      - 8 `../` reach `tmp_base/`

    Any traversal probe MUST NOT exceed 7 segments so that the resolved target
    STRICTLY STAYS INSIDE self.tmp_base. In-test safety assertions verify that the
    resolved target is inside self.tmp_base before executing any probe.

    THE NESTING IS NOT INCIDENTAL:
    Against a shallow fixture directly under /tmp, an over-deep traversal can either
    land on / and fail with [Errno 13] Permission denied (a false green / pre-fix pass
    for the wrong reason, F-03), or succeed in creating directories and writing outside
    the scratch area (collateral damage, F-12). Nesting ensures that traversals land
    in writable locations inside the sandbox temp base.
    """

    def setUp(self):
        self.tmp_base = Path(tempfile.mkdtemp(prefix="aw_test_containment_")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp_base, ignore_errors=True))

        self.repo_dir = self.tmp_base / "nest1" / "nest2" / "nest3" / "repo"
        self.specs_dir = self.repo_dir / ".aw" / "records" / "specs"
        self.draft_dir = self.specs_dir / "draft"
        self.draft_dir.mkdir(parents=True, exist_ok=True)

        subprocess.run(["git", "init", "-q"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "T"], cwd=self.repo_dir, check=True
        )

    def _run(self, argv: list[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.repo_dir)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def _assert_target_bounded(self, date_arg: str) -> Path:
        """Assert that date_arg's computed destination remains inside self.tmp_base."""
        date_compact = date_arg.replace("-", "")
        # Arithmetically compute candidate destination
        candidate = (self.draft_dir / f"{date_compact}-test.spec.md").resolve()
        self.assertTrue(
            candidate.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: traversal target {candidate} escapes temp base {self.tmp_base}",
        )
        return candidate

    def _assert_no_escaped_files(self):
        """Assert no .spec.md exists outside the specs records tree under self.tmp_base."""
        all_specs = list(self.tmp_base.rglob("*.spec.md"))
        escaped = [
            p
            for p in all_specs
            if not p.resolve().is_relative_to(self.specs_dir.resolve())
        ]
        self.assertEqual(
            escaped,
            [],
            f"Escaped spec files found outside specs records tree: {escaped}",
        )


class TestSpecsDateContainment(_ContainmentRepoTestCase):
    """E-03 / V-03: Pin the escape as the primary property."""

    def test_escape_to_repo_root_refused(self):
        """A 4-level traversal (../../../../ESCAPED) targeting repo root must be refused at exit 2."""
        date_val = "../../../../ESCAPED"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                date_val,
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)

    def test_escape_leaving_repo_inside_tmp_refused(self):
        """A 6-level traversal leaving repo but inside tmp_base must be refused at exit 2."""
        date_val = "../../../../../../OUTSIDE/sub"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                date_val,
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)

    def test_absolute_path_date_refused(self):
        """An absolute path in --date must be refused at exit 2."""
        target_dir = self.tmp_base / "nest1" / "ABSOLUTE"
        date_val = str(target_dir)
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                date_val,
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)

    def test_traversing_dry_run_refused(self):
        """A traversing dry run (no --apply) must refuse at exit 2 and not preview an escape (F-11)."""
        date_val = "../../../../ESCAPED"
        self._assert_target_bounded(date_val)

        # 1. Plain dry run
        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                date_val,
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertNotIn("--- would write", out)
        self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)

        # 2. Agent envelope dry run
        rc_agent, out_agent, err_agent = self._run(
            [
                "specs",
                "new",
                "--date",
                date_val,
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
                "--agent",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc_agent,
            2,
            f"Expected exit 2, got {rc_agent}. stdout: {out_agent}, stderr: {err_agent}",
        )
        self.assertNotIn('"outcome":"clean"', out_agent)

    def test_conforming_date_succeeds(self):
        """A conforming --date 2026-09-29 succeeds at exit 0 and writes inside draft_dir."""
        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                "2026-09-29",
                "--title",
                "Conforming",
                "--slug",
                "conf",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"Expected exit 0, got {rc}. stderr: {err}")
        files = list(self.draft_dir.glob("20260929-*-01-*-conf.spec.md"))
        self.assertEqual(len(files), 1, f"Expected 1 written file, found {files}")
        self._assert_no_escaped_files()


class TestFabricatedDatesAndNonRegressions(_ContainmentRepoTestCase):
    """E-04 / V-04: Fabricated dates and non-regressions."""

    def test_fabricated_date_9999_refused_record_identity(self):
        """--date 9999-99-99 must be refused to protect record IDENTITY (F-04, OQ-01).

        This half of the defect is about record identity rather than path safety:
        a fabricated filename date silently stamps invalid dates into the filename,
        - Date: bullet, and history record, as previously occurred in repository history (tf4jz5).
        """
        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                "9999-99-99",
                "--title",
                "T",
                "--slug",
                "x",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)
        self._assert_no_escaped_files()
        self.assertEqual(list(self.draft_dir.glob("*.spec.md")), [])

    def test_fabricated_date_notadate_refused(self):
        """--date notadate and --date 2026-9-9 are refused by the format check."""
        for bad_date in ("notadate", "2026-9-9"):
            with self.subTest(bad_date=bad_date):
                rc, out, err = self._run(
                    [
                        "specs",
                        "new",
                        "--date",
                        bad_date,
                        "--title",
                        "T",
                        "--slug",
                        "x",
                        "--summary",
                        "s",
                        "--apply",
                    ]
                )
                self.assertEqual(rc, 2, f"Expected exit 2 for {bad_date}, got {rc}")
                self.assertIn("aw specs new: --date must be YYYY-MM-DD", err)
                self._assert_no_escaped_files()

    def test_f05_checker_asymmetry_pre_fix_artifact(self):
        """F-05 checker asymmetry on a malformed-date artifact placed in the specs tree.

        aw specs check reports 1 finding (attention.history-missing) while
        aw check specs reports 3 findings including check.name-nonconformant.
        """
        bad_file = self.draft_dir / "notadate-u6o1sr-01-u6o1sr-x.spec.md"
        bad_file.write_text(
            "# Spec: T\n\n- Date: notadate\n- Status: draft\n- Id: u6o1sr\n- Author: aw specs new\n- Scope: s\n\n"
            "## Workflow history\n\n- notadate created (aw specs): s\n",
            encoding="utf-8",
        )
        # 1. aw specs check --dir <repo> --agent
        rc_sc, out_sc, _ = self._run(["specs", "check", "--agent"])
        self.assertEqual(rc_sc, 1)
        self.assertIn('"rule":"attention.history-missing"', out_sc)

        # 2. aw check specs --dir <repo> --agent
        rc_cs, out_cs, _ = self._run(["check", "specs", "--agent"])
        self.assertEqual(rc_cs, 1)
        self.assertIn('"rule":"check.name-nonconformant"', out_cs)
        self.assertIn('"rule":"attention.history-missing"', out_cs)

    def test_non_regression_conforming_bytes(self):
        """(a) Conforming --date 2026-09-29 generates matching structure and bytes."""
        with patch("agent_workflows.specs.core.mint_id6", return_value="8rt43x"):
            rc, out, err = self._run(
                [
                    "specs",
                    "new",
                    "--date",
                    "2026-09-29",
                    "--title",
                    "Conforming Spec Title",
                    "--slug",
                    "conforming-spec",
                    "--summary",
                    "Conforming summary text.",
                    "--apply",
                ]
            )
        self.assertEqual(rc, 0, err)
        created = self.draft_dir / "20260929-8rt43x-01-8rt43x-conforming-spec.spec.md"
        self.assertTrue(created.exists())
        expected = (
            "# Spec: Conforming Spec Title\n\n"
            "- Date: 2026-09-29\n"
            "- Status: draft\n"
            "- Id: 8rt43x\n"
            "- Author: aw specs new\n"
            "- Scope: Conforming summary text.\n\n"
            "## Workflow history\n\n"
            "- 2026-09-29 created (aw specs): Conforming summary text.\n"
        )
        self.assertEqual(created.read_text(encoding="utf-8"), expected)

    def test_non_regression_omitted_date_defaults_today(self):
        """(b) Omitting --date defaults to today's date."""
        today_iso = dt.date.today().isoformat()
        today_compact = today_iso.replace("-", "")
        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--title",
                "Today Spec",
                "--slug",
                "today-spec",
                "--summary",
                "s",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, err)
        files = list(self.draft_dir.glob(f"{today_compact}-*-today-spec.spec.md"))
        self.assertEqual(len(files), 1)

    def test_non_regression_title_required_unchanged(self):
        """(c) Existing --title is required refusal keeps its exit code (2) and message."""
        rc, out, err = self._run(["specs", "new", "--slug", "x"])
        self.assertEqual(rc, 2)
        self.assertEqual(err, "aw specs new: --title is required\n")

    def test_non_regression_run_set_and_run_note_date_behavior(self):
        """(d) specs.run_set and specs.run_note date paths remain unchanged (F-15).

        Driven at the function: a malformed date writes to the history record without traversing,
        and creates no files.
        """
        spec_path = self.draft_dir / "20260929-fn0101-01-fn0101-test.spec.md"
        spec_path.write_text(
            "# Spec: Test\n\n"
            "- Date: 2026-09-29\n"
            "- Status: draft\n"
            "- Id: fn0101\n"
            "- Author: me\n"
            "- Scope: test\n\n"
            "## Workflow history\n\n"
            "- 2026-09-29 created (aw specs): initial\n",
            encoding="utf-8",
        )

        # 1. run_note
        args_note = argparse.Namespace(
            path=str(spec_path),
            message="note message",
            date="../../../ESCAPED",
            by_human=False,
            tool="aw specs",
            dir=str(self.repo_dir),
            no_commit=True,
        )
        rc_note = specs.run_note(args_note)
        self.assertEqual(rc_note, 0)
        self.assertIn(
            "- ../../../ESCAPED note (aw specs): note message",
            spec_path.read_text(encoding="utf-8"),
        )

        # 2. run_set
        args_set = argparse.Namespace(
            path=str(spec_path),
            status="to-review",
            message="status change",
            date="../../../ESCAPED_SET",
            by_human=False,
            gate_kind=None,
            gate_ref=None,
            tool="aw specs",
            dir=str(self.repo_dir),
            no_commit=True,
            dry_run=False,
        )
        rc_set = specs.run_set(args_set)
        self.assertEqual(rc_set, 0)
        to_review_path = (
            self.specs_dir / "to-review" / "20260929-fn0101-01-fn0101-test.spec.md"
        )
        self.assertTrue(to_review_path.exists())
        self.assertIn(
            "- ../../../ESCAPED_SET to-review (aw specs): status change",
            to_review_path.read_text(encoding="utf-8"),
        )

        # Confirm no ESCAPED files exist anywhere under tmp_base
        self._assert_no_escaped_files()

    def test_non_regression_conforming_dry_run_previews(self):
        """(e) Conforming dry run previews same path and exits 0."""
        rc, out, err = self._run(
            [
                "specs",
                "new",
                "--date",
                "2026-09-29",
                "--title",
                "Dry",
                "--slug",
                "dry",
                "--summary",
                "s",
            ]
        )
        self.assertEqual(rc, 0, err)
        self.assertIn("--- would write", out)
        self.assertIn("20260929-", out)
        self.assertEqual(list(self.draft_dir.glob("*.spec.md")), [])


class TestE02ContainmentBypassAndLegacyLayout(_ContainmentRepoTestCase):
    """E-02 / V-02: Containment defense in depth and legacy layout support."""

    def test_containment_refusal_when_format_guard_bypassed(self):
        """When format check is bypassed, E-02 containment guard refuses exit 2."""
        # Monkeypatch re.match in agent_workflows.specs to allow the traversal string through E-01
        orig_match = re.match

        def bypass_match(pattern, string, flags=0):
            if "../" in str(string):
                return orig_match(r".*", string, flags)
            return orig_match(pattern, string, flags)

        date_val = "../../../../ESCAPED"
        self._assert_target_bounded(date_val)

        class _FakeDate:
            @staticmethod
            def fromisoformat(s):
                return dt.date(2026, 9, 29)

            @staticmethod
            def today():
                return dt.date.today()

        class _FakeDateTime:
            date = _FakeDate

        with patch("re.match", side_effect=bypass_match), patch.object(
            specs, "_dt", _FakeDateTime
        ):
            # 1. With apply
            rc_apply, out_apply, err_apply = self._run(
                [
                    "specs",
                    "new",
                    "--date",
                    date_val,
                    "--title",
                    "T",
                    "--slug",
                    "x",
                    "--summary",
                    "s",
                    "--apply",
                ]
            )
            self._assert_no_escaped_files()
            self.assertEqual(
                rc_apply, 2, f"Expected containment exit 2, got {rc_apply}"
            )
            self.assertIn("escapes records tree", err_apply)

            # 2. Dry run without apply
            rc_dry, out_dry, err_dry = self._run(
                [
                    "specs",
                    "new",
                    "--date",
                    date_val,
                    "--title",
                    "T",
                    "--slug",
                    "x",
                    "--summary",
                    "s",
                ]
            )
            self._assert_no_escaped_files()
            self.assertEqual(rc_dry, 2, f"Expected dry run exit 2, got {rc_dry}")
            self.assertNotIn("--- would write", out_dry)
            self.assertIn("escapes records tree", err_dry)

            # 3. Dry run with --agent
            rc_ag, out_ag, err_ag = self._run(
                [
                    "specs",
                    "new",
                    "--date",
                    date_val,
                    "--title",
                    "T",
                    "--slug",
                    "x",
                    "--summary",
                    "s",
                    "--agent",
                ]
            )
            self._assert_no_escaped_files()
            self.assertEqual(rc_ag, 2, f"Expected agent dry run exit 2, got {rc_ag}")
            self.assertNotIn('"outcome":"clean"', out_ag)

    def test_conforming_new_in_legacy_layout(self):
        """Conforming specs new works in legacy .agents/specs layout fixture."""
        # Create legacy fixture (.agents/docs/specs/draft)
        legacy_repo = self.tmp_base / "legacy_repo"
        legacy_specs = legacy_repo / ".agents" / "docs" / "specs" / "draft"
        legacy_specs.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=legacy_repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=legacy_repo, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=legacy_repo, check=True)

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(
                [
                    "specs",
                    "new",
                    "--dir",
                    str(legacy_repo),
                    "--date",
                    "2026-09-29",
                    "--title",
                    "Legacy",
                    "--slug",
                    "legacy",
                    "--summary",
                    "s",
                    "--apply",
                ]
            )
        self.assertEqual(rc, 0, err.getvalue())
        files = list(legacy_specs.glob("20260929-*-legacy.spec.md"))
        self.assertEqual(
            len(files), 1, f"Expected file in legacy specs dir, found {files}"
        )

        # Dry run in legacy repo
        out_dry, err_dry = io.StringIO(), io.StringIO()
        with redirect_stdout(out_dry), redirect_stderr(err_dry):
            rc_dry = cli.main(
                [
                    "specs",
                    "new",
                    "--dir",
                    str(legacy_repo),
                    "--date",
                    "2026-09-29",
                    "--title",
                    "Legacy Dry",
                    "--slug",
                    "legacy-dry",
                    "--summary",
                    "s",
                ]
            )
        self.assertEqual(rc_dry, 0, err_dry.getvalue())
        self.assertIn("--- would write", out_dry.getvalue())
        self.assertIn(".agents/docs/specs/draft", out_dry.getvalue())

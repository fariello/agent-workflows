"""Tests for research --date containment, validation, and non-regressions (IPD iumgvk).

Covers:
- E-01 / V-01: --date format and calendar validation (_refuse_unsafe_date).
- E-02 / V-02: planner-level guard in plan_new, plan_new_comparison, and aw adopt.
- E-03 / V-03: destination containment defense-in-depth in _emit_and_write (relative_to / ValueError).
- E-04 / V-04: pinning escape behavior with nested fixture and bounded traversal depth.
- E-05 / V-05: frontmatter injection, fabricated dates, detection asymmetry, and non-regressions.
"""

from __future__ import annotations

import argparse
from datetime import date
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Tuple
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows import research_cmd
from agent_workflows import research_contract as R
from agent_workflows.project_context import resolve_verb_repo_root


class _ResearchContainmentTestCase(unittest.TestCase):
    """Base fixture for research date containment tests with bounded nesting depth.

    SAFETY REQUIREMENT (IPD iumgvk E-04, PR-001):
    The fixture is nested several directories deep inside self.tmp_base:
        <tmp_base>/a/b/c/repo
    whose records directory is:
        repo/.aw/records/research

    From research/:
      - 1 `../` reaches `.aw/records/`
      - 2 `../` reach `.aw/`
      - 3 `../` reach `repo/` (repo root)
      - 4 `../` reach `c/`
      - 5 `../` reach `b/`
      - 6 `../` reach `a/`
      - 7 `../` reach `tmp_base/`

    Any traversal probe MUST NOT exceed 6 segments so that the resolved target
    STRICTLY STAYS INSIDE self.tmp_base. In-test safety assertions verify that BOTH
    the resolved research root and the resolved target are inside self.tmp_base
    before executing any destructive probe.

    WHY THE FIXTURE IS NESTED:
    Against a shallow fixture directly under /tmp or scratch root, an over-deep traversal can either
    land on / and fail with [Errno 13] Permission denied (a false green / pre-fix pass
    for the wrong reason), or succeed in creating directories and writing outside
    the scratch area (collateral damage). Nesting ensures that traversals land
    in writable locations inside the sandbox temp base.
    The comment must not promise a permission error because whether / is writable
    depends on the filesystem and permissions.
    """

    def setUp(self):
        self.tmp_base = Path(
            tempfile.mkdtemp(prefix="aw_test_rsearch_containment_")
        ).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp_base, ignore_errors=True))

        self.repo_dir = self.tmp_base / "a" / "b" / "c" / "repo"
        self.research_root = self.repo_dir / ".aw" / "records" / "research"
        self.research_root.mkdir(parents=True, exist_ok=True)

        # PR-001: Isolate HOME and XDG_CONFIG_HOME to the temp base so project_context
        # and record_producers cannot resolve under the user home directory.
        self.env_patcher = patch.dict(
            os.environ,
            {
                "HOME": str(self.tmp_base),
                "XDG_CONFIG_HOME": str(self.tmp_base),
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        subprocess.run(["git", "init", "-q"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "T"], cwd=self.repo_dir, check=True
        )

    def _run(self, argv: list[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        if (
            len(argv) >= 2
            and argv[0] == "research"
            and argv[1] in ("new", "new-comparison")
        ):
            cmd = [argv[0], argv[1], str(self.repo_dir)] + argv[2:]
        else:
            cmd = argv + ["--dir", str(self.repo_dir)]
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(cmd)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def _assert_target_bounded(self, date_arg: str) -> Path:
        """Assert that date_arg's computed destination remains inside self.tmp_base."""
        # Derive research root from repository resolution under isolated environment
        repo_root = resolve_verb_repo_root(str(self.repo_dir))
        resolved_root = R.resolve_research_root(repo_root).resolve()
        self.assertTrue(
            resolved_root.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: resolved research root {resolved_root} escapes temp base {self.tmp_base}",
        )
        candidate = (resolved_root / date_arg).resolve()
        self.assertTrue(
            candidate.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: traversal target {candidate} escapes temp base {self.tmp_base}",
        )
        return candidate

    def _assert_no_escaped_files(self):
        """Assert no .md exists outside the research records tree under self.tmp_base."""
        all_md = list(self.tmp_base.rglob("*.md"))
        resolved_root = self.research_root.resolve()
        inbox_dir = (self.repo_dir / ".aw" / "inbox").resolve()
        escaped = [
            p
            for p in all_md
            if not p.resolve().is_relative_to(resolved_root)
            and not (inbox_dir.exists() and p.resolve().is_relative_to(inbox_dir))
        ]
        self.assertEqual(
            escaped,
            [],
            f"Escaped research files found outside research records tree: {escaped}",
        )


class TestResearchDateContainment(_ResearchContainmentTestCase):
    """E-04: Pin the escape as the primary property."""

    def test_escape_research_new_refused(self):
        """A 4-level traversal in research new must be refused at exit 2 and write nothing."""
        date_val = "../../../../ESCAPED1"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "esc-new-1",
                "--summary",
                "summary of esc1",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_escape_research_new_comparison_refused(self):
        """A traversal in research new-comparison must be refused at exit 2 without escaping 3 files."""
        date_val = "../../../../ESCAPED2"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "research",
                "new-comparison",
                "--set",
                "esc-cmp-set",
                "--slug",
                "esc-cmp-1",
                "--models",
                "gpt56",
                "--summary",
                "summary of cmp esc",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        combined = out + err
        self.assertIn("aw research new-comparison: --date must be YYYYMMDD", combined)

    def test_escape_adopt_refused(self):
        """aw adopt with a traversing date must be refused at exit 2 with the date refusal."""
        inbox = self.repo_dir / ".aw" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        drop = inbox / "drop.md"
        drop.write_text("# External drop content\n", encoding="utf-8")

        date_val = "../../../../ESCAPED3"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "adopt",
                str(drop),
                "--type",
                "research",
                "--kind",
                "findings",
                "--slug",
                "esc-adopt-1",
                "--summary",
                "summary of adopt esc",
                "--date",
                date_val,
                "--yes",
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_absolute_path_date_refused(self):
        """An absolute path in --date must be refused at exit 2."""
        abs_target = self.tmp_base / "a" / "ABSOUT"
        date_val = str(abs_target)
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "esc-abs-1",
                "--summary",
                "summary of abs esc",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_traversing_dry_run_refused(self):
        """A traversing dry run must refuse at exit 2 and not preview an out-of-tree write (F-05)."""
        date_val = "../../../../ESCAPED-DRY"
        self._assert_target_bounded(date_val)

        # 1. Plain dry run
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "esc-dry-1",
                "--summary",
                "summary of dry esc",
                "--date",
                date_val,
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertNotIn("--- would write", out)
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

        # 2. Agent envelope dry run
        rc_agent, out_agent, err_agent = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "esc-dry-2",
                "--summary",
                "summary of agent dry esc",
                "--date",
                date_val,
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
        self.assertIn('"outcome":"cannot-run"', out_agent)

    def test_set_date_masking_trap(self):
        """Pin the set-date masking trap (F-09) and prove fresh-slug requirement.

        On pre-fix code, if a set already existed on disk, _set_date_for_set substituted the
        existing set's date into the filename, masking the traversal from the filename while
        still injecting it into the created: frontmatter line.
        With the planner-level date guard in place, an invalid --date is refused upfront even
        when the set already exists.
        """
        # Seed an existing record in set 'maskseed'
        rc_seed, out_seed, err_seed = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "maskseed",
                "--summary",
                "initial seed record",
                "--date",
                "20260101",
                "--apply",
            ]
        )
        self.assertEqual(
            rc_seed, 0, f"Seed record creation failed: {out_seed}, {err_seed}"
        )

        # Now attempt to create another record in the same set with a traversing date
        date_val = "../../../../ESCAPED-MASKED"
        self._assert_target_bounded(date_val)
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--set",
                "maskseed",
                "--slug",
                "maskseed-child",
                "--summary",
                "masked child record",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)


class TestResearchFrontMatterInjection(_ResearchContainmentTestCase):
    """E-05: Pin frontmatter injection defect class."""

    def test_frontmatter_injection_release_gate_refused(self):
        """Pin F-08: newlines in --date injecting real release-gate frontmatter keys must be refused.

        Severe case: set-date masking kept the filename clean while injecting blocks-release: next,
        which aw releases show next honored as a release blocker while checkers reported clean.
        """
        # Seed the set so set date would mask filename if unvalidated
        rc_seed, out_seed, err_seed = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--set",
                "injseed",
                "--slug",
                "injseed",
                "--summary",
                "seed for injection test",
                "--date",
                "20260101",
                "--apply",
            ]
        )
        self.assertEqual(rc_seed, 0)

        injected_date = (
            "20260101\nstatus: reference\nblocks-release: next\npriority: high"
        )
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--set",
                "injseed",
                "--slug",
                "inj-child",
                "--summary",
                "injection child",
                "--date",
                injected_date,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_frontmatter_injection_first_record_literal_newline_refused(self):
        """Pin F-07: on a set's first record, newline in --date must be refused at exit 2."""
        injected_date = "20260929\nstatus: reference\nblocks-release: next"
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "inj-first",
                "--summary",
                "first record with newline",
                "--date",
                injected_date,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)


class TestResearchFabricationAndValidation(_ResearchContainmentTestCase):
    """E-05: Record identity / calendar validity and lexical format validation."""

    def test_fabricated_calendar_dates_refused(self):
        """Unreachable calendar dates matching 8 digits must be refused via calendar check."""
        for bad_date in ["99999999", "20261332", "20260230"]:
            with self.subTest(date=bad_date):
                rc, out, err = self._run(
                    [
                        "research",
                        "new",
                        "--kind",
                        "findings",
                        "--slug",
                        f"fab-{bad_date}",
                        "--summary",
                        "fabricated date",
                        "--date",
                        bad_date,
                        "--apply",
                    ]
                )
                self._assert_no_escaped_files()
                self.assertEqual(rc, 2)
                combined = out + err
                self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_fullwidth_unicode_digits_refused(self):
        """Fullwidth Unicode digits (PR-002) must be refused by ASCII regex check."""
        bad_date = "２０２６０９２９"
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "fullwidth",
                "--summary",
                "fullwidth digits",
                "--date",
                bad_date,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)

    def test_iso_date_refused(self):
        """ISO format YYYY-MM-DD must be refused because research grammar accepts only YYYYMMDD."""
        iso_date = "2026-09-29"
        rc, out, err = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "iso-date",
                "--summary",
                "iso date",
                "--date",
                iso_date,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research new: --date must be YYYYMMDD", combined)
        self.assertIn("got '2026-09-29'", combined)

    def test_various_invalid_date_strings_refused(self):
        """Empty, non-numeric, or malformed date strings must be refused."""
        for bad_date in ["", "notadate", "9999-99-99", "/abs/ESCAPED"]:
            with self.subTest(date=bad_date):
                rc, out, err = self._run(
                    [
                        "research",
                        "new",
                        "--kind",
                        "findings",
                        "--slug",
                        "bad-date",
                        "--summary",
                        "bad date",
                        "--date",
                        bad_date,
                        "--apply",
                    ]
                )
                self._assert_no_escaped_files()
                self.assertEqual(rc, 2)
                combined = out + err
                self.assertIn("aw research new: --date must be YYYYMMDD", combined)


class TestResearchDetectionAsymmetry(_ResearchContainmentTestCase):
    """E-05 / F-13: Detection asymmetry between index and check."""

    def test_malformed_in_tree_detection_asymmetry(self):
        """Pin F-13: malformed-but-in-tree record is caught by index --check but passes check research."""
        malformed = self.research_root / "9999-99-99-mal-00-bei2d5-mal.findings.md"
        content = research_cmd.build_frontmatter(
            id6="bei2d5",
            created="9999-99-99",
            set_id="mal",
            order="00",
            topic=[],
            model=None,
            kind="findings",
            status="todo",
            outcome="none-yet",
            summary="malformed in-tree doc",
        )
        malformed.write_text(content, encoding="utf-8")

        # 1. index --check flags name-invalid
        rc_idx, out_idx, err_idx = self._run(["research", "index", "--check"])
        self.assertEqual(rc_idx, 1)
        self.assertIn("name-invalid", out_idx + err_idx)

        # 2. check research reports conforms
        rc_chk, out_chk, err_chk = self._run(["check", "research", "--agent"])
        self.assertEqual(rc_chk, 0)
        self.assertIn('"outcome":"conforms"', out_chk)


class TestResearchNonRegressions(_ResearchContainmentTestCase):
    """E-05: Non-regression verification for conforming invocations and existing refusals."""

    def test_conforming_date_byte_identical(self):
        """A conforming --date 20260929 writes the expected path and content (pinned id6)."""
        with patch.object(research_cmd, "_mint_research_id6", return_value="fx1234"):
            rc, out, err = self._run(
                [
                    "research",
                    "new",
                    "--kind",
                    "findings",
                    "--slug",
                    "conf1",
                    "--summary",
                    "conforming record",
                    "--date",
                    "20260929",
                    "--apply",
                ]
            )
        self.assertEqual(rc, 0, f"Expected 0, got {rc}. out: {out}, err: {err}")
        expected_file = (
            self.research_root / "20260929-conf1-00-fx1234-conf1.findings.md"
        )
        self.assertTrue(expected_file.exists())
        text = expected_file.read_text(encoding="utf-8")
        self.assertIn("id: fx1234", text)
        self.assertIn("created: 20260929", text)
        self.assertIn("set: conf1", text)
        self.assertIn("kind: findings", text)

    def test_omitted_date_defaults_to_today(self):
        """Omitting --date defaults to today's date for new, new-comparison, and adopt."""
        today_str = date.today().strftime("%Y%m%d")

        # 1. research new
        rc_new, out_new, _ = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "omit-new",
                "--summary",
                "omit date new",
                "--apply",
            ]
        )
        self.assertEqual(rc_new, 0)
        new_files = list(self.research_root.glob(f"{today_str}-omit-new-*.findings.md"))
        self.assertEqual(len(new_files), 1)

        # 2. research new-comparison
        rc_cmp, out_cmp, _ = self._run(
            [
                "research",
                "new-comparison",
                "--set",
                "omit-cmp",
                "--slug",
                "omit-cmp",
                "--models",
                "gpt56",
                "--summary",
                "omit date cmp",
                "--apply",
            ]
        )
        self.assertEqual(rc_cmp, 0)
        cmp_files = list(self.research_root.glob(f"{today_str}-omit-cmp-*.md"))
        self.assertEqual(len(cmp_files), 3)

        # 3. aw adopt
        inbox = self.repo_dir / ".aw" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        drop = inbox / "drop_omit.md"
        drop.write_text("# Drop\n", encoding="utf-8")
        rc_adopt, out_adopt, _ = self._run(
            [
                "adopt",
                str(drop),
                "--type",
                "research",
                "--kind",
                "findings",
                "--slug",
                "omit-adopt",
                "--summary",
                "omit date adopt",
                "--yes",
                "--apply",
            ]
        )
        self.assertEqual(rc_adopt, 0)
        adopt_files = list(
            self.research_root.glob(f"{today_str}-omit-adopt-*.findings.md")
        )
        self.assertEqual(len(adopt_files), 1)

    def test_conforming_dry_run_previews_and_exits_zero(self):
        """Conforming dry run still previews and exits 0 on both arms."""
        # 1. Plain preview
        rc, out, _ = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "dry-conf",
                "--summary",
                "dry conf summary",
                "--date",
                "20260929",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("--- would write", out)
        self.assertIn("20260929-dry-conf-00-", out)

        # 2. Agent preview
        rc_agent, out_agent, _ = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "dry-agent-conf",
                "--summary",
                "agent dry conf summary",
                "--date",
                "20260929",
                "--agent",
            ]
        )
        self.assertEqual(rc_agent, 0)
        self.assertIn('"outcome":"clean"', out_agent)
        self.assertIn('"applied":false', out_agent)

    def test_existing_refusals_preserved(self):
        """Existing refusals for kind, slug/summary, priority, models are preserved."""
        # Invalid kind
        rc_kind, out_kind, err_kind = self._run(
            ["research", "new", "--kind", "badkind", "--slug", "k", "--summary", "s"]
        )
        self.assertEqual(rc_kind, 2)
        self.assertIn("unknown kind 'badkind'", out_kind + err_kind)

        # Missing slug and summary
        rc_noslug, out_noslug, err_noslug = self._run(
            ["research", "new", "--kind", "findings"]
        )
        self.assertEqual(rc_noslug, 2)
        self.assertIn("a --slug or --summary is required", out_noslug + err_noslug)

        # Invalid priority
        rc_prio, out_prio, err_prio = self._run(
            [
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "p",
                "--summary",
                "s",
                "--priority",
                "urgent",
            ]
        )
        self.assertEqual(rc_prio, 2)
        self.assertIn("invalid choice: 'urgent'", out_prio + err_prio)

        # Missing models for comparison
        rc_models, out_models, err_models = self._run(
            ["research", "new-comparison", "--set", "s", "--slug", "sl"]
        )
        self.assertEqual(rc_models, 2)
        self.assertIn(
            "the following arguments are required: --models", out_models + err_models
        )


class TestResearchContainmentDirectBypass(_ResearchContainmentTestCase):
    """E-03 / V-03: Destination containment assertion direct testing (defense-in-depth)."""

    def test_containment_refuses_traversal_when_date_guard_bypassed(self):
        """When date guard is bypassed, _emit_and_write containment assertion catches the traversal."""
        traversing_file = research_cmd.PlannedFile(
            path=self.research_root / "../../../../ESCAPED_BYPASS.md",
            content="# Escaped\n",
        )
        args = argparse.Namespace(dir=str(self.repo_dir))

        # 1. apply arm
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = research_cmd._emit_and_write(
                files=[traversing_file],
                apply=True,
                overwrite=False,
                args=args,
            )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        self.assertIn("escapes research tree", out.getvalue() + err.getvalue())

        # 2. dry run arm
        out_dry, err_dry = io.StringIO(), io.StringIO()
        with redirect_stdout(out_dry), redirect_stderr(err_dry):
            rc_dry = research_cmd._emit_and_write(
                files=[traversing_file],
                apply=False,
                overwrite=False,
                args=args,
            )
        self.assertEqual(rc_dry, 2)
        self.assertNotIn("--- would write", out_dry.getvalue())
        self.assertIn("escapes research tree", out_dry.getvalue() + err_dry.getvalue())

        # 3. dry run agent arm
        args_agent = argparse.Namespace(dir=str(self.repo_dir), agent=True)
        out_agent, err_agent = io.StringIO(), io.StringIO()
        with redirect_stdout(out_agent), redirect_stderr(err_agent):
            rc_agent = research_cmd._emit_and_write(
                files=[traversing_file],
                apply=False,
                overwrite=False,
                args=args_agent,
            )
        self.assertEqual(rc_agent, 2)
        self.assertIn('"outcome":"cannot-run"', out_agent.getvalue())
        self.assertNotIn('"outcome":"clean"', out_agent.getvalue())

    def test_containment_refuses_absolute_path_destination(self):
        """_emit_and_write containment assertion refuses an absolute path destination outside root."""
        abs_dest = self.tmp_base / "a" / "ABSOUT_DIRECT.md"
        planned = research_cmd.PlannedFile(path=abs_dest, content="# Abs\n")
        args = argparse.Namespace(dir=str(self.repo_dir))

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = research_cmd._emit_and_write(
                files=[planned],
                apply=True,
                overwrite=False,
                args=args,
            )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        self.assertIn("escapes research tree", out.getvalue() + err.getvalue())

    def test_containment_skipped_when_args_none(self):
        """When args is None, root cannot be derived, so assertion is skipped without error."""
        conforming_file = research_cmd.PlannedFile(
            path=self.research_root / "20260929-skip-00-fx1234-skip.findings.md",
            content="# Content\n",
        )
        out, _ = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            rc = research_cmd._emit_and_write(
                files=[conforming_file],
                apply=False,
                overwrite=False,
                args=None,
            )
        self.assertEqual(rc, 0)
        self.assertIn("--- would write", out.getvalue())

    def test_containment_accepts_nested_shard_descendant(self):
        """_emit_and_write containment assertion accepts nested shard descendants of root."""
        shard_file = research_cmd.PlannedFile(
            path=self.research_root
            / "202609-W39"
            / "20260929-shard-00-fx1234-shard.findings.md",
            content="# Shard content\n",
        )
        args = argparse.Namespace(dir=str(self.repo_dir))
        out, _ = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            rc = research_cmd._emit_and_write(
                files=[shard_file],
                apply=False,
                overwrite=False,
                args=args,
            )
        self.assertEqual(rc, 0)
        self.assertIn("--- would write", out.getvalue())

    def test_legacy_layout_boundary_derivation(self):
        """Boundary derivation resolves legacy layout .agents/docs/research correctly."""
        legacy_base = self.tmp_base / "legacy_repo"
        legacy_research = legacy_base / ".agents" / "docs" / "research"
        legacy_research.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=legacy_base, check=True)

        args = argparse.Namespace(dir=str(legacy_base))
        conforming_legacy = research_cmd.PlannedFile(
            path=legacy_research / "20260929-leg-00-fx1234-leg.findings.md",
            content="# Legacy\n",
        )
        out, _ = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            rc = research_cmd._emit_and_write(
                files=[conforming_legacy],
                apply=False,
                overwrite=False,
                args=args,
            )
        self.assertEqual(rc, 0)
        self.assertIn("--- would write", out.getvalue())


class TestRefuseUnsafeDateHelper(unittest.TestCase):
    """E-01 / V-01: Direct test of research_cmd._refuse_unsafe_date."""

    def test_refuse_unsafe_date_verdict_table(self):
        helper = getattr(research_cmd, "_refuse_unsafe_date", None)
        if helper is None:
            self.fail("research_cmd._refuse_unsafe_date not implemented yet")

        # Inputs that must return None
        self.assertIsNone(helper("aw research new", None))
        self.assertIsNone(helper("aw research new", "20260929"))

        # Inputs that must be refused
        refused_inputs = [
            "../../../../ESCAPED",
            "/abs/ESCAPED",
            "2026-09-29",
            "9999-99-99",
            "notadate",
            "",
            "99999999",
            "20261332",
            "20260230",
            "20260929\nstatus: reference",
            "２０２６０９２９",
        ]
        for val in refused_inputs:
            with self.subTest(value=val):
                msg = helper("aw research new", val)
                self.assertIsNotNone(msg, f"Expected refusal for {val!r}")
                self.assertIn("aw research new", msg)
                self.assertIn("YYYYMMDD", msg)
                self.assertIn(repr(val), msg)

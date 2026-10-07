"""Tests for research set-assign --date containment, validation, and non-regressions (IPD plb8jx).

Covers:
- E-01 / V-01: Date validation reuse from research_cmd._refuse_unsafe_date.
- E-02 / V-02: Planner-level date guard in research_refs.plan_set_assign.
- E-03 / V-03: Destination containment defense-in-depth in _apply_renames.
- E-04 / V-04: Pinning escape behavior with nested fixture and bounded traversal depth.
- E-05 / V-05: Mechanism (git mv refusal / shutil fallback), detection blindness, fabrication, and non-regressions.
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
from typing import Optional, Tuple
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows import research_contract as R
from agent_workflows import research_refs
from agent_workflows.project_context import resolve_verb_repo_root


class _ResearchSetAssignContainmentTestCase(unittest.TestCase):
    """Base fixture for research set-assign date containment tests with bounded nesting depth.

    SAFETY REQUIREMENT (IPD plb8jx E-04, PR-001):
    The fixture is nested several directories deep inside self.tmp_base:
        <tmp_base>/n1/n2/n3/repo
    whose records directory is:
        repo/.aw/records/research

    From research/:
      - 1 `../` reaches `.aw/records/`
      - 2 `../` reach `.aw/`
      - 3 `../` reach `repo/` (repo root)
      - 4 `../` reach `n3/`
      - 5 `../` reach `n2/`
      - 6 `../` reach `n1/`
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
            tempfile.mkdtemp(prefix="aw_test_set_assign_containment_")
        ).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp_base, ignore_errors=True))

        self.repo_dir = self.tmp_base / "n1" / "n2" / "n3" / "repo"
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

        # Seed standard committed research record
        self._seed_record(
            id6="w1qe6d",
            set_id="seed",
            order="00",
            slug="seed",
            created="20260101",
        )

    def _seed_record(
        self,
        id6: str = "w1qe6d",
        set_id: str = "seed",
        order: str = "00",
        slug: str = "seed",
        created: str = "20260101",
        subdir: Optional[str] = None,
    ) -> Path:
        target_dir = self.research_root
        if subdir:
            target_dir = target_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{created}-{set_id}-{order}-{id6}-{slug}.findings.md"
        filepath = target_dir / filename
        content = f"""---
id: {id6}
created: {created}
set: {set_id}
order: '{order}'
topic: [testing]
kind: findings
status: completed
outcome: confirmed
summary: seed record {id6}
---
# Seed {id6}
"""
        filepath.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"seed {id6}"], cwd=self.repo_dir, check=True
        )
        return filepath

    def _run(self, argv: list[str]) -> Tuple[int, str, str]:
        cmd = argv + ["--dir", str(self.repo_dir)]
        if (
            argv
            and argv[0] == "research"
            and len(argv) > 1
            and argv[1] in ("set-assign", "mv")
        ):
            cmd.append("--no-commit")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(cmd)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def _assert_target_bounded(
        self, date_arg: str, filename_suffix: str = "grp-00-w1qe6d-seed.findings.md"
    ) -> Path:
        """Assert that date_arg's computed destination remains inside self.tmp_base."""
        repo_root = resolve_verb_repo_root(str(self.repo_dir))
        resolved_root = R.resolve_research_root(repo_root).resolve()
        self.assertTrue(
            resolved_root.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: resolved research root {resolved_root} escapes temp base {self.tmp_base}",
        )
        candidate = (resolved_root / f"{date_arg}-{filename_suffix}").resolve()
        self.assertTrue(
            candidate.is_relative_to(self.tmp_base),
            f"SAFETY VIOLATION: traversal target {candidate} escapes temp base {self.tmp_base}",
        )
        return candidate

    def _assert_no_escaped_files(self):
        """Assert no .findings.md exists outside the research records tree under self.tmp_base."""
        all_findings = list(self.tmp_base.rglob("*.findings.md"))
        resolved_root = self.research_root.resolve()
        escaped = [
            p for p in all_findings if not p.resolve().is_relative_to(resolved_root)
        ]
        self.assertEqual(
            escaped,
            [],
            f"Escaped research files found outside research records tree: {escaped}",
        )


class TestEscapeSetAssignDateContainment(_ResearchSetAssignContainmentTestCase):
    """E-04 / V-04: Pin the escape as the primary property."""

    def test_escape_traversal_refused_cli_apply(self):
        """A 4-level traversal in research set-assign must be refused at exit 2 with no file moved."""
        date_val = "../../../../ESCAPED"
        self._assert_target_bounded(date_val)
        original_record = (
            self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md"
        )

        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertTrue(
            original_record.exists(), "Original record must remain in research tree"
        )
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        self.assertNotIn(
            " D ", status.stdout, "Git index must not report an unstaged deletion"
        )
        combined = out + err
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", combined)

    def test_escape_traversing_dry_run_refused(self):
        """A traversing dry run must refuse at exit 2 and not preview a clean basename (F-02)."""
        date_val = "../../../../ESCAPED-DRY"
        self._assert_target_bounded(date_val)

        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                date_val,
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(
            rc, 2, f"Expected exit 2, got {rc}. stdout: {out}, stderr: {err}"
        )
        self.assertNotIn(
            "--- would rename", out, "Dry run must refuse rather than previewing"
        )
        combined = out + err
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", combined)

    def test_newline_bearing_date_refused(self):
        """A newline in --date must be refused at exit 2 without creating a file with literal newline."""
        date_val = "20261002\nstatus: active"
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                date_val,
                "--apply",
            ]
        )
        self._assert_no_escaped_files()
        self.assertEqual(rc, 2)
        # Ensure no file with literal newline exists
        newline_files = [p for p in self.research_root.glob("*.md") if "\n" in p.name]
        self.assertEqual(newline_files, [])
        combined = out + err
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", combined)

    def test_absolute_path_date_pinned_at_planner(self):
        """Absolute-path date is pinned at planner: Path.__truediv__ discards left operand so it cannot be bounded."""
        abs_date = "/ABSOLUTE/ESCAPED"
        plans, err = research_refs.plan_set_assign(
            self.research_root, ["w1qe6d"], "grp", abs_date, repo_root=self.repo_dir
        )
        self.assertIsNone(plans)
        self.assertIsNotNone(err)
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", err)

    def test_conforming_rename_in_archive_shard_subdirectory(self):
        """Descendant allowance: conforming rename of a record in an archive shard subdirectory succeeds."""
        shard_rel = "reference/202608"
        self._seed_record(
            id6="rf0001",
            set_id="ref",
            order="00",
            slug="refdoc",
            created="20260801",
            subdir=shard_rel,
        )
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "rf0001",
                "--set",
                "newgrp",
                "--date",
                "20261007",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"Expected 0, got {rc}. out: {out}, err: {err}")
        old_file = (
            self.research_root / shard_rel / "20260801-ref-00-rf0001-refdoc.findings.md"
        )
        new_file = (
            self.research_root
            / shard_rel
            / "20261007-newgrp-00-rf0001-refdoc.findings.md"
        )
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())


class TestContainmentDirectBypass(_ResearchSetAssignContainmentTestCase):
    """E-03 / V-03: Destination containment assertion direct testing (defense-in-depth)."""

    def test_containment_refuses_traversal_when_date_guard_bypassed(self):
        """When date guard is bypassed, _apply_renames containment assertion catches the traversal."""
        traversing_plan = research_refs.RenamePlan(
            old_path=self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md",
            new_path=self.research_root
            / "../../../../ESCAPED_BYPASS-grp-00-w1qe6d-seed.findings.md",
        )
        self._assert_target_bounded("../../../../ESCAPED_BYPASS")

        # 1. apply arm
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            touched = research_refs._apply_renames(
                self.repo_dir,
                [traversing_plan],
                apply=True,
            )
        self.assertIsNone(touched, "Containment refusal must return sentinel None")
        self._assert_no_escaped_files()
        combined = out.getvalue() + err.getvalue()
        self.assertIn("error: destination", combined)
        self.assertIn("escapes research tree", combined)

        # 2. dry run arm
        out_dry, err_dry = io.StringIO(), io.StringIO()
        with redirect_stdout(out_dry), redirect_stderr(err_dry):
            touched_dry = research_refs._apply_renames(
                self.repo_dir,
                [traversing_plan],
                apply=False,
            )
        self.assertIsNone(
            touched_dry, "Dry run containment refusal must return sentinel None"
        )
        combined_dry = out_dry.getvalue() + err_dry.getvalue()
        self.assertNotIn(
            "--- would rename", combined_dry, "Dry run must refuse rather than preview"
        )
        self.assertIn("error: destination", combined_dry)
        self.assertIn("escapes research tree", combined_dry)

    def test_containment_refuses_absolute_path_destination_directly(self):
        """_apply_renames containment assertion catches an absolute path without ValueError traceback."""
        abs_dest = Path("/ABSOLUTE/ESCAPED-grp-00-w1qe6d-seed.findings.md")
        abs_plan = research_refs.RenamePlan(
            old_path=self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md",
            new_path=abs_dest,
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            touched = research_refs._apply_renames(
                self.repo_dir,
                [abs_plan],
                apply=False,
            )
        self.assertIsNone(touched)
        combined = out.getvalue() + err.getvalue()
        self.assertIn("error: destination", combined)
        self.assertIn("escapes research tree", combined)

    def test_containment_multi_id_one_bad_moves_none(self):
        """Multi-id call where one destination escapes moves NONE of the records."""
        self._seed_record(
            id6="w2qe6d", set_id="seed", order="01", slug="seed2", created="20260101"
        )
        plan_good = research_refs.RenamePlan(
            old_path=self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md",
            new_path=self.research_root / "20261007-grp-00-w1qe6d-seed.findings.md",
        )
        plan_bad = research_refs.RenamePlan(
            old_path=self.research_root / "20260101-seed-01-w2qe6d-seed2.findings.md",
            new_path=self.research_root / "../../../../ESCAPED_MULTI.findings.md",
        )
        self._assert_target_bounded(
            "../../../../ESCAPED_MULTI", filename_suffix="findings.md"
        )

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            touched = research_refs._apply_renames(
                self.repo_dir,
                [plan_good, plan_bad],
                apply=True,
            )
        self.assertIsNone(touched)
        self.assertTrue(
            (self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md").exists()
        )
        self.assertTrue(
            (self.research_root / "20260101-seed-01-w2qe6d-seed2.findings.md").exists()
        )
        self.assertFalse(
            (self.research_root / "20261007-grp-00-w1qe6d-seed.findings.md").exists()
        )
        self._assert_no_escaped_files()

    def test_containment_legacy_layout_supported(self):
        """Boundary derivation resolves legacy layout .agents/docs/research correctly."""
        legacy_base = self.tmp_base / "legacy_repo"
        legacy_research = legacy_base / ".agents" / "docs" / "research"
        legacy_research.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=legacy_base, check=True)

        seed_file = legacy_research / "20260101-seed-00-w1qe6d-seed.findings.md"
        seed_file.write_text(
            "---\nid: w1qe6d\nkind: findings\n---\n# Seed\n", encoding="utf-8"
        )
        conforming_plan = research_refs.RenamePlan(
            old_path=seed_file,
            new_path=legacy_research / "20261007-grp-00-w1qe6d-seed.findings.md",
        )

        out, _ = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            touched = research_refs._apply_renames(
                legacy_base,
                [conforming_plan],
                apply=False,
            )
        self.assertIsNotNone(touched)
        self.assertIn("--- would rename", out.getvalue())


class TestSetAssignFabricationAndValidation(_ResearchSetAssignContainmentTestCase):
    """E-05 / V-05: Record identity / calendar validity and lexical format validation."""

    def test_fabricated_calendar_dates_refused_record_identity(self):
        """Unreachable calendar dates matching 8 digits must be refused (record identity protection)."""
        for bad_date in ["99999999", "20261332", "20260230"]:
            with self.subTest(date=bad_date):
                rc, out, err = self._run(
                    [
                        "research",
                        "set-assign",
                        "w1qe6d",
                        "--set",
                        "grp",
                        "--date",
                        bad_date,
                    ]
                )
                self.assertEqual(rc, 2)
                combined = out + err
                self.assertIn(
                    "aw research set-assign: --date must be YYYYMMDD", combined
                )

    def test_fullwidth_unicode_digits_refused(self):
        """Fullwidth Unicode digits (PR-002) must be refused by ASCII regex check."""
        bad_date = "２０２６０９２９"
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                bad_date,
            ]
        )
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", combined)

    def test_iso_date_refused(self):
        """ISO format YYYY-MM-DD must be refused because research grammar accepts only YYYYMMDD."""
        iso_date = "2026-09-29"
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                iso_date,
            ]
        )
        self.assertEqual(rc, 2)
        combined = out + err
        self.assertIn("aw research set-assign: --date must be YYYYMMDD", combined)
        self.assertIn("got '2026-09-29'", combined)

    def test_various_invalid_date_strings_refused(self):
        """Empty, non-numeric, or malformed date strings must be refused."""
        for bad_date in ["", "notadate", "9999-99-99"]:
            with self.subTest(date=bad_date):
                rc, out, err = self._run(
                    [
                        "research",
                        "set-assign",
                        "w1qe6d",
                        "--set",
                        "grp",
                        "--date",
                        bad_date,
                    ]
                )
                self.assertEqual(rc, 2)
                combined = out + err
                self.assertIn(
                    "aw research set-assign: --date must be YYYYMMDD", combined
                )


class TestMechanismAndDetectionBlindness(_ResearchSetAssignContainmentTestCase):
    """E-05 / V-05: Mechanism (git mv refusal / shutil fallback) and detection blindness."""

    def test_mechanism_git_mv_refusal_and_shutil_fallback(self):
        """Pin F-04: git mv itself refuses out-of-tree destinations (exit 128); shutil.move swallows it.

        The artifact_core.git_mv fallback is a deliberately unfixed live defect
        whose scope is carried by backlog item ki1uqk.
        """
        # 1. Drive git mv directly to prove it refuses exit 128
        res = subprocess.run(
            [
                "git",
                "-C",
                str(self.repo_dir),
                "mv",
                "--",
                ".aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md",
                ".aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 128)
        self.assertIn("is outside repository", res.stderr)

    def test_git_index_inconsistency_after_shutil_move(self):
        """Pin F-05: when a record leaves through shutil.move, git index retains old path as unstaged deletion."""
        src = self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md"
        dst = (
            self.tmp_base
            / "n1"
            / "n2"
            / "n3"
            / "ESCAPED-grp-00-w1qe6d-seed.findings.md"
        )
        shutil.move(str(src), str(dst))

        # Check git status shows unstaged deletion
        st = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        self.assertIn(
            " D .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md",
            st.stdout,
        )

        # Check git ls-files still lists the file
        ls = subprocess.run(
            ["git", "ls-files"], cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertIn(
            ".aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md", ls.stdout
        )

    def test_detection_blindness_pinned(self):
        """Pin F-01/F-09: index --check, index, find, and check report clean on empty repo that lost its only record."""
        # Move the only record out of the tree manually
        src = self.research_root / "20260101-seed-00-w1qe6d-seed.findings.md"
        dst = (
            self.tmp_base
            / "n1"
            / "n2"
            / "n3"
            / "ESCAPED-grp-00-w1qe6d-seed.findings.md"
        )
        shutil.move(str(src), str(dst))

        # Regenerate index to simulate the post-escape index write
        from agent_workflows import research_index

        research_index.run_index(
            argparse.Namespace(
                dir=str(self.repo_dir),
                check=False,
                agent=False,
                limit=None,
            )
        )

        # 1. index --check reports clean
        rc_idx_chk, out_idx_chk, _ = self._run(["research", "index", "--check"])
        self.assertEqual(rc_idx_chk, 0)
        self.assertIn("index --check: clean", out_idx_chk)

        # 2. index reports 0 docs
        rc_idx, out_idx, _ = self._run(["research", "index"])
        self.assertEqual(rc_idx, 0)
        self.assertIn("(0 docs)", out_idx)

        # 3. find reports no matching docs
        rc_find, out_find, _ = self._run(["research", "find", "--agent"])
        self.assertEqual(rc_find, 0)
        self.assertIn("no matching research docs", out_find)

        # 4. check research reports conforms
        rc_check, out_check, _ = self._run(["check", "research", "--agent"])
        self.assertEqual(rc_check, 0)
        self.assertIn('"outcome":"conforms"', out_check)


class TestSetAssignNonRegressions(_ResearchSetAssignContainmentTestCase):
    """E-05 / V-05: Non-regression verification for conforming invocations and existing refusals."""

    def test_conforming_date_20260929(self):
        """A conforming --date 20260929 renames and updates frontmatter properly."""
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                "20260929",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"Expected 0, got {rc}. out: {out}, err: {err}")
        expected = self.research_root / "20260929-grp-00-w1qe6d-seed.findings.md"
        self.assertTrue(expected.exists())
        text = expected.read_text(encoding="utf-8")
        self.assertIn("set: grp", text)
        self.assertTrue("order: '00'" in text or "order: 00" in text)

    def test_omitted_date_defaults_to_today(self):
        """Omitting --date defaults to today's date."""
        today_str = date.today().strftime("%Y%m%d")
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0)
        expected = self.research_root / f"{today_str}-grp-00-w1qe6d-seed.findings.md"
        self.assertTrue(expected.exists())

    def test_conforming_dry_run_previews_and_exits_zero(self):
        """Conforming dry run previews and exits 0."""
        rc, out, err = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "grp",
                "--date",
                "20260929",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("--- would rename", out)
        self.assertIn("20260929-grp-00-w1qe6d-seed.findings.md", out)

    def test_existing_refusals_preserved(self):
        """Existing refusals for missing set, setid length, unknown id6, etc. are preserved."""
        # Missing set
        rc_set, out_set, err_set = self._run(
            ["research", "set-assign", "w1qe6d", "--set", ""]
        )
        self.assertEqual(rc_set, 2)
        self.assertIn("a --set id is required", out_set + err_set)

        # Setid length > 24
        rc_len, out_len, err_len = self._run(
            [
                "research",
                "set-assign",
                "w1qe6d",
                "--set",
                "this-is-a-very-long-set-id-over-limit",
            ]
        )
        self.assertEqual(rc_len, 2)
        self.assertIn("over the 24-character maximum for a setid", out_len + err_len)

        # Unknown id6
        rc_id, out_id, err_id = self._run(
            ["research", "set-assign", "zzzzzz", "--set", "grp"]
        )
        self.assertEqual(rc_id, 2)
        self.assertIn("no research artifact matched 'zzzzzz'", out_id + err_id)

    def test_research_mv_unchanged(self):
        """aw research mv remains unchanged and functional."""
        rc, out, err = self._run(
            [
                "research",
                "mv",
                "w1qe6d",
                "--slug",
                "newslug",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"Expected 0, got {rc}. out: {out}, err: {err}")
        expected = self.research_root / "20260101-seed-00-w1qe6d-newslug.findings.md"
        self.assertTrue(expected.exists())

"""Unit and functional tests for `aw search` command options:
-s/--status multi-filtering, -S short format, -t/--type multi-filtering,
and -F/--full entire artifact body search.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


class SearchOptionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

        # Create record directories
        self.plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        self.plans_exec_dir = self.repo / ".aw" / "records" / "plans" / "executed"
        self.specs_dir = self.repo / ".aw" / "records" / "specs"
        self.backlog_dir = self.repo / ".aw" / "records" / "backlog"
        self.research_dir = self.repo / ".aw" / "records" / "research"
        self.prompts_dir = self.repo / ".aw" / "records" / "prompts"

        for d in (
            self.plans_dir,
            self.plans_exec_dir,
            self.specs_dir,
            self.backlog_dir,
            self.research_dir,
            self.prompts_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        # 1. Plan approved with unique metadata keyword ALPHA_SECRET and body keyword BETA_BODY
        (self.plans_dir / "20260901-testplan-01-pln001-sample-plan.ipd.md").write_text(
            "# IPD: Sample Plan Title ALPHA_SECRET\n\n"
            "- Id: pln001\n"
            "- Status: approved\n"
            "- Set: testplan\n\n"
            "## Context\n\n"
            "This is body text containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 2. Plan executed
        (
            self.plans_exec_dir / "20260901-testplan-02-pln002-executed-plan.ipd.md"
        ).write_text(
            "# IPD: Executed Plan Title ALPHA_SECRET\n\n"
            "- Id: pln002\n"
            "- Status: executed\n"
            "- Set: testplan\n\n"
            "## Context\n\n"
            "Executed plan body text with BETA_BODY.\n",
            encoding="utf-8",
        )

        # 3. Spec to-review
        (self.specs_dir / "20260901-spc001-01-spc001-sample-spec.spec.md").write_text(
            "# Spec: Sample Spec Title ALPHA_SECRET\n\n"
            "- Id: spc001\n"
            "- Status: to-review\n\n"
            "## Requirements\n\n"
            "Requirements body containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 4. Spec draft
        (self.specs_dir / "20260901-spc002-01-spc002-draft-spec.spec.md").write_text(
            "# Spec: Draft Spec Title ALPHA_SECRET\n\n"
            "- Id: spc002\n"
            "- Status: draft\n\n"
            "## Requirements\n\n"
            "Draft requirements body containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 5. Backlog open
        (self.backlog_dir / "20260901-bkl001-01-bkl001-sample-backlog.md").write_text(
            "# Backlog: Sample Backlog Title ALPHA_SECRET\n\n"
            "- Id: bkl001\n"
            "- Status: open\n\n"
            "## Details\n\n"
            "Backlog body text containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 6. Backlog done
        (self.backlog_dir / "20260901-bkl002-01-bkl002-done-backlog.md").write_text(
            "# Backlog: Done Backlog Title ALPHA_SECRET\n\n"
            "- Id: bkl002\n"
            "- Status: done\n\n"
            "## Details\n\n"
            "Done body text containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 7. Research reference (YAML front matter)
        (
            self.research_dir / "20260901-res001-00-res001-sample-survey.survey.md"
        ).write_text(
            "---\n"
            "id: res001\n"
            "status: reference\n"
            "summary: Research summary with ALPHA_SECRET\n"
            "---\n"
            "# Research Survey\n\n"
            "## Findings\n\n"
            "Research body text containing BETA_BODY.\n",
            encoding="utf-8",
        )

        # 8. Prompt
        (self.prompts_dir / "20260901-prm001-01-prm001-sample-prompt.md").write_text(
            "# Prompt: Sample Prompt ALPHA_SECRET\n\n"
            "- Id: prm001\n"
            "- Status: reviewed\n\n"
            "## Prompt\n\n"
            "Prompt body containing BETA_BODY.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = cli.main(list(argv) + ["--dir", str(self.repo)])
        return rc, buf.getvalue()

    def test_status_filter_comma_separated(self):
        """1. --status / -s with comma-separated list returns ONLY matching statuses."""
        rc, out = self._run(
            "search", "-s", "open,to-review,reviewed,approved", "-p", "ALPHA_SECRET"
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 4)
        # Should include pln001 (approved), spc001 (to-review), bkl001 (open), prm001 (reviewed)
        self.assertTrue(any("pln001" in entry for entry in lines))
        self.assertTrue(any("spc001" in entry for entry in lines))
        self.assertTrue(any("bkl001" in entry for entry in lines))
        self.assertTrue(any("prm001" in entry for entry in lines))
        # Must NOT include pln002 (executed), spc002 (draft), bkl002 (done), res001 (reference)
        self.assertFalse(any("pln002" in entry for entry in lines))
        self.assertFalse(any("spc002" in entry for entry in lines))
        self.assertFalse(any("bkl002" in entry for entry in lines))
        self.assertFalse(any("res001" in entry for entry in lines))

    def test_status_filter_repeated_flags(self):
        """1. --status / -s with multiple flags."""
        rc, out = self._run(
            "search", "-s", "open", "-s", "approved", "-p", "ALPHA_SECRET"
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("pln001" in entry for entry in lines))
        self.assertTrue(any("bkl001" in entry for entry in lines))

    def test_status_normalization_hyphens_and_underscores(self):
        """Status filters handle to-review and to_review identically."""
        rc1, out1 = self._run("search", "-s", "to-review", "-p", "ALPHA_SECRET")
        rc2, out2 = self._run("search", "-s", "to_review", "-p", "ALPHA_SECRET")
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertEqual(out1, out2)
        self.assertIn("spc001", out1)

    def test_short_flag_uppercase_S(self):
        """2. --short should have -S as the one-letter arg."""
        rc, out = self._run("search", "-s", "approved", "-S", "ALPHA_SECRET")
        self.assertEqual(rc, 0)
        self.assertIn("approved", out)
        self.assertIn("pln001", out)
        # Verify attention-format row
        self.assertTrue(out.strip().startswith("-"))

    def test_type_filter_comma_separated(self):
        """3. --type / -t accepts comma-separated types."""
        rc, out = self._run("search", "-t", "plan,prompt", "-p", "ALPHA_SECRET")
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        # pln001, pln002, and prm001
        self.assertEqual(len(lines), 3)
        self.assertTrue(any("pln001" in entry for entry in lines))
        self.assertTrue(any("pln002" in entry for entry in lines))
        self.assertTrue(any("prm001" in entry for entry in lines))
        self.assertFalse(any("spc001" in entry for entry in lines))
        self.assertFalse(any("bkl001" in entry for entry in lines))
        self.assertFalse(any("res001" in entry for entry in lines))

    def test_type_filter_repeated_flags(self):
        """3. --type / -t accepts repeated flags."""
        rc, out = self._run(
            "search", "-t", "spec", "-t", "backlog", "-p", "ALPHA_SECRET"
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 4)
        self.assertTrue(any("spc001" in entry for entry in lines))
        self.assertTrue(any("spc002" in entry for entry in lines))
        self.assertTrue(any("bkl001" in entry for entry in lines))
        self.assertTrue(any("bkl002" in entry for entry in lines))
        self.assertFalse(any("pln001" in entry for entry in lines))

    def test_type_filter_with_aliases(self):
        """3. --type / -t supports aliases like ipd and bk."""
        rc, out = self._run("search", "-t", "ipd,bk", "-p", "ALPHA_SECRET")
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 4)
        self.assertTrue(any("pln001" in entry for entry in lines))
        self.assertTrue(any("bkl001" in entry for entry in lines))

    def test_type_flag_with_positional_pattern(self):
        """3. When -t is specified, positional arguments are the search pattern."""
        rc, out = self._run("search", "-t", "plans", "ALPHA_SECRET", "-p")
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("pln001" in entry for entry in lines))
        self.assertTrue(any("pln002" in entry for entry in lines))

    def test_default_search_only_filename_and_metadata(self):
        """4. Without --full / -F, search matches filename and metadata, not body."""
        # ALPHA_SECRET is in metadata/title -> matches without -F
        rc, out = self._run("search", "-p", "ALPHA_SECRET")
        self.assertEqual(rc, 0)
        self.assertIn("pln001", out)

        # BETA_BODY is only in the body sections (under ##) -> should NOT match without -F
        rc_body, out_body = self._run("search", "BETA_BODY")
        self.assertEqual(rc_body, 1)
        self.assertIn("no matching lines for 'BETA_BODY'", out_body)

    def test_full_search_with_F_flag(self):
        """4. With --full / -F, search searches entire artifact body."""
        rc, out = self._run("search", "-F", "-p", "BETA_BODY")
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        # All 8 documents contain BETA_BODY in their body
        self.assertEqual(len(lines), 8)

    def test_full_flag_long_form(self):
        """4. --full works identically to -F."""
        rc, out = self._run("search", "--full", "-p", "BETA_BODY")
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 8)

    def test_filename_match_without_F(self):
        """4. Filename matches are found even if token is not in file content."""
        # 'sample-plan' is in the filename of pln001
        rc, out = self._run("search", "-t", "plan", "-p", "sample-plan")
        self.assertEqual(rc, 0)
        self.assertIn("pln001", out)

    def test_combined_type_status_and_full(self):
        """Combined test with -t, -s, and -F."""
        rc, out = self._run(
            "search",
            "-t",
            "plan",
            "-s",
            "approved",
            "-F",
            "-p",
            "BETA_BODY",
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("pln001", lines[0])

    def test_json_output_filters_metadata(self):
        """JSON output contains status and full in filters data when supplied."""
        rc, out = self._run(
            "search",
            "-t",
            "plan",
            "-s",
            "approved,to-review",
            "-F",
            "--json",
            "BETA_BODY",
        )
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["command"], "search")
        self.assertEqual(data["status"], "clean")
        self.assertIn("status", data["data"]["filters"])
        self.assertEqual(data["data"]["filters"]["full"], True)
        self.assertEqual(data["data"]["filters"]["type"], "plans")
        self.assertEqual(data["data"]["filters"]["pattern"], "BETA_BODY")

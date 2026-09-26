"""Tests for aw find CLI commands and research status filtering (IPD 5e3nj2 E-10)."""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R


class CliFindResearchStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_cli_find_")
        self.repo_root = Path(self.temp_dir)
        rroot = self.repo_root / ".aw" / "records" / "research"
        rroot.mkdir(parents=True, exist_ok=True)

        # 1. Statusless research-prompt
        name_prompt = R.format_name(
            R.ResearchName(
                date="20260924",
                set_id="testset",
                order="00",
                id6="prm001",
                slug="test-prompt",
                model=None,
                kind="research-prompt",
            )
        )
        content_prompt = C.build_frontmatter(
            id6="prm001",
            created="20260924",
            set_id="testset",
            order="00",
            topic=["t"],
            model=None,
            kind="research-prompt",
            status=None,
            outcome="none-yet",
            summary="prompt summary",
        )
        (rroot / name_prompt).write_text(content_prompt, encoding="utf-8")

        # 2. Todo research-report
        name_report = R.format_name(
            R.ResearchName(
                date="20260924",
                set_id="testset",
                order="01",
                id6="rpt001",
                slug="test-report",
                model=None,
                kind="research-report",
            )
        )
        content_report = C.build_frontmatter(
            id6="rpt001",
            created="20260924",
            set_id="testset",
            order="01",
            topic=["t"],
            model=None,
            kind="research-report",
            status="todo",
            outcome="none-yet",
            summary="report summary",
        )
        (rroot / name_report).write_text(content_report, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_research_todo_returns_no_research_prompts(self):
        """E-10: aw find research todo returns only answer docs carrying status: todo, never prompts."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["find", "research", "todo", "-p", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 0)
        output = buf.getvalue()
        self.assertIn("rpt001", output)
        self.assertNotIn("prm001", output)
        self.assertNotIn(".research-prompt.md", output)

    def test_find_research_through_a_symlinked_repo_root(self):
        """The repo reached through a symlink (macOS `/var` -> `/private/var`) must find the same docs."""
        link = Path(self.temp_dir + "-link")
        try:
            os.symlink(self.temp_dir, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create a symlink here: {exc}")
        self.addCleanup(lambda: os.path.lexists(link) and os.unlink(link))
        rel = Path(self.repo_root).relative_to(self.temp_dir)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["find", "research", "todo", "-p", "--dir", str(link / rel)])
        self.assertEqual(rc, 0)
        self.assertIn("rpt001", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

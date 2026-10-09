"""Tests for aw find CLI commands and research status filtering (IPD 5e3nj2 E-10)."""

from __future__ import annotations

import io
import json
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

    def test_record_dirs_non_research_does_not_leak_legacy_research_nesting(self):
        """E-03/E-10: selectors.record_dirs for non-research types does not include .agents/docs/research."""
        from agent_workflows import selectors

        legacy_research = self.repo_root / ".agents" / "docs" / "research"
        legacy_research.mkdir(parents=True, exist_ok=True)
        # Clear cache to ensure fresh resolution
        selectors._record_dirs_cached.cache_clear()
        for rtype in ["plans", "specs", "prompts", "backlog"]:
            dirs = selectors.record_dirs(self.repo_root, rtype)
            self.assertNotIn(legacy_research.resolve(), [d.resolve() for d in dirs])


class CliFindExitMatrixTests(unittest.TestCase):
    """Unified exit matrix tests for aw find across all surfaces and token classes (zyj8io E-01..E-06)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_matrix_")
        self.repo_root = Path(self.temp_dir)
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        plan_file = plans_dir / "20260929-testplan-01-pln001-sample.ipd.md"
        plan_file.write_text(
            "# IPD: Sample\n\n- Id: pln001\n- Status: approved\n- Set: testplan\n",
            encoding="utf-8",
        )
        self.empty_repo = self.repo_root / "empty_repo"
        self.empty_repo.mkdir(parents=True, exist_ok=True)
        (self.empty_repo / ".aw" / "records" / "plans").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _invoke(self, args: list[str], repo: Path) -> tuple[int, str, str]:
        buf = io.StringIO()
        err = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", err):
            rc = cli.main(["find", *args, "--dir", str(repo)])
        return rc, buf.getvalue(), err.getvalue()

    def test_post_change_exit_matrix(self):
        """Unified matrix: (a) nonexistent exits 2 on all 4 surfaces; (b) empty vocab exits 0 on all 4;
        (c) matching exits 0 on all 4; (d) empty tree with no selector exits 0 on all 4.
        """
        # (a) nonexistent token exits 2 across all four surfaces
        rc_human, out_human, err_human = self._invoke(
            ["plans", "zzzzzz"], self.repo_root
        )
        self.assertEqual(rc_human, 2)
        self.assertEqual(out_human, "")
        self.assertIn("zzzzzz", err_human)

        rc_agent, out_agent, _ = self._invoke(
            ["plans", "zzzzzz", "--agent"], self.repo_root
        )
        self.assertEqual(rc_agent, 2)
        self.assertIn("zzzzzz", out_agent)

        rc_json, out_json, _ = self._invoke(
            ["plans", "zzzzzz", "--json"], self.repo_root
        )
        self.assertEqual(rc_json, 2)
        self.assertIn("zzzzzz", out_json)

        rc_paths, out_paths, err_paths = self._invoke(
            ["plans", "zzzzzz", "-p"], self.repo_root
        )
        self.assertEqual(rc_paths, 2)
        self.assertEqual(out_paths, "")
        self.assertIn("zzzzzz", err_paths)

        # (b) vocabulary token matching nothing in fixture exits 0 across all four surfaces
        rc_b_human, out_b_human, err_b_human = self._invoke(
            ["plans", "reusable"], self.repo_root
        )
        self.assertEqual(rc_b_human, 0)
        self.assertIn("no matching plans", out_b_human)
        self.assertEqual(err_b_human, "")

        rc_b_agent, out_b_agent, _ = self._invoke(
            ["plans", "reusable", "--agent"], self.repo_root
        )
        self.assertEqual(rc_b_agent, 0)

        rc_b_json, out_b_json, _ = self._invoke(
            ["plans", "reusable", "--json"], self.repo_root
        )
        self.assertEqual(rc_b_json, 0)

        rc_b_paths, out_b_paths, err_b_paths = self._invoke(
            ["plans", "reusable", "-p"], self.repo_root
        )
        self.assertEqual(rc_b_paths, 0)
        self.assertEqual(out_b_paths, "")
        self.assertEqual(err_b_paths, "")

        # (c) matching token exits 0 across all four surfaces
        self.assertEqual(self._invoke(["plans", "pln001"], self.repo_root)[0], 0)
        self.assertEqual(
            self._invoke(["plans", "pln001", "--agent"], self.repo_root)[0], 0
        )
        self.assertEqual(
            self._invoke(["plans", "pln001", "--json"], self.repo_root)[0], 0
        )
        rc_c_p, out_c_p, _ = self._invoke(["plans", "pln001", "-p"], self.repo_root)
        self.assertEqual(rc_c_p, 0)
        self.assertIn("pln001", out_c_p)

        # (d) empty tree with no selector exits 0 across all four surfaces
        self.assertEqual(self._invoke(["plans"], self.empty_repo)[0], 0)
        self.assertEqual(self._invoke(["plans", "--agent"], self.empty_repo)[0], 0)
        self.assertEqual(self._invoke(["plans", "--json"], self.empty_repo)[0], 0)
        self.assertEqual(self._invoke(["plans", "-p"], self.empty_repo)[0], 0)


class CliFindVocabularyAndMatchFactsTests(unittest.TestCase):
    """Tests for find_selector_vocabulary and find_selector_match_facts (zyj8io E-02, E-03)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_vocab_")
        self.repo_root = Path(self.temp_dir)
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / "20260929-testplan-01-pln001-sample.ipd.md").write_text(
            "# IPD: Sample\n\n- Id: pln001\n- Status: approved\n- Set: testplan\n",
            encoding="utf-8",
        )
        bkl_dir = self.repo_root / ".aw" / "records" / "backlog" / "open"
        bkl_dir.mkdir(parents=True, exist_ok=True)
        (bkl_dir / "20260929-setbkl-01-bkl001-item.backlog.md").write_text(
            "- Id: bkl001\n- Status: open\n- Set: setbkl\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vocabulary_membership_and_gap(self):
        """E-02: find_selector_vocabulary includes gap tokens reviews, other, intake, and excludes nonsense."""
        vocab = cli.find_selector_vocabulary()
        self.assertIn("reviews", vocab)
        self.assertIn("other", vocab)
        self.assertIn("intake", vocab)
        self.assertNotIn("zzzzzz", vocab)

    def test_match_facts_substring_query(self):
        """E-03 / V-03 (i): substring-only query counts as MATCHED and does not refuse."""
        facts = cli.find_selector_match_facts(self.repo_root, ["plans"], ["sample"])
        self.assertEqual(facts.matched, ("sample",))
        self.assertEqual(facts.unmatched, ())
        self.assertEqual(facts.refusable, ())

    def test_match_facts_narrowing_filter(self):
        """E-03 / V-03 (ii): token whose match is removed by narrowing filter is NOT reported unmatched."""
        buf = io.StringIO()
        err = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", err):
            rc = cli.main(
                [
                    "find",
                    "plans",
                    "pln001",
                    "--status",
                    "draft",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        self.assertIn("no matching plans", buf.getvalue())
        self.assertEqual(err.getvalue(), "")

    def test_match_facts_multi_type(self):
        """E-03 / V-03 (iii): in no---type multi-type search a token matching under any type counts as matched."""
        facts = cli.find_selector_match_facts(
            self.repo_root, ["plans", "specs", "backlog"], ["bkl001"]
        )
        self.assertEqual(facts.matched, ("bkl001",))
        self.assertEqual(facts.unmatched, ())
        self.assertEqual(facts.refusable, ())

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["find", "bkl001", "-p", "--dir", str(self.repo_root)])
        self.assertEqual(rc, 0)
        self.assertIn("bkl001", buf.getvalue())


class CliFindRefusalSurfacesTests(unittest.TestCase):
    """Tests for machine, human, and --paths refusal surfaces (zyj8io E-04, E-05, E-06)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_surfaces_")
        self.repo_root = Path(self.temp_dir)
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / "20260929-testplan-01-pln001-sample.ipd.md").write_text(
            "# IPD: Sample\n\n- Id: pln001\n- Status: approved\n- Set: testplan\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_surface_refusal_and_matching(self):
        """E-04: --agent emits cannot-run error record with tokens, passes schema validation."""
        from agent_workflows import agent_schema

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["find", "plans", "zzzzzz", "--agent", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 2)
        rec = json.loads(buf.getvalue())
        agent_schema.assert_valid_agent_record(rec)
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertFalse(rec["verified"])
        self.assertFalse(rec["complete"])
        self.assertIn("zzzzzz", rec["unresolved_targets"])
        self.assertIn("zzzzzz", rec["unresolved_selectors"])

        # Matching query emits stream records that pass schema
        buf_match = io.StringIO()
        with patch("sys.stdout", buf_match):
            rc_match = cli.main(
                ["find", "plans", "pln001", "--agent", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc_match, 0)
        lines = [
            line.strip() for line in buf_match.getvalue().splitlines() if line.strip()
        ]
        for line in lines:
            r = json.loads(line)
            agent_schema.assert_valid_agent_record(r)

    def test_json_surface_refusal(self):
        """E-04: --json emits CommandResult with cannot-run and data carrying unresolved tokens."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["find", "plans", "zzzzzz", "--json", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 2)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["status"], "cannot-run")
        self.assertEqual(data["exit_code"], 2)
        self.assertFalse(data["verified"])
        self.assertFalse(data["complete"])
        self.assertIn("zzzzzz", data["data"]["unresolved_targets"])

    def test_human_surface_refusal(self):
        """E-05: human surface writes refusal to stderr, names each token individually, stdout empty."""
        # (i) Single typo token
        buf1 = io.StringIO()
        err1 = io.StringIO()
        with patch("sys.stdout", buf1), patch("sys.stderr", err1):
            rc1 = cli.main(["find", "plans", "zzzzzz", "--dir", str(self.repo_root)])
        self.assertEqual(rc1, 2)
        self.assertEqual(buf1.getvalue(), "")
        self.assertIn("zzzzzz", err1.getvalue())
        self.assertIn("Active filters:", err1.getvalue())

        # (ii) Two tokens: one valid, one typo
        buf2 = io.StringIO()
        err2 = io.StringIO()
        with patch("sys.stdout", buf2), patch("sys.stderr", err2):
            rc2 = cli.main(
                ["find", "plans", "pln001", "zzzzzz", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc2, 2)
        self.assertEqual(buf2.getvalue(), "")
        self.assertIn("zzzzzz", err2.getvalue())
        self.assertIn("pln001", err2.getvalue())

    def test_paths_surface_exit_codes_and_stdout(self):
        """E-06: --paths exits 2 on typo with stdout empty, exits 0 on vocab empty with stdout empty."""
        # Typo -> 2, stdout empty, stderr has diagnostic
        buf_typo = io.StringIO()
        err_typo = io.StringIO()
        with patch("sys.stdout", buf_typo), patch("sys.stderr", err_typo):
            rc_typo = cli.main(
                ["find", "plans", "zzzzzz", "-p", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc_typo, 2)
        self.assertEqual(buf_typo.getvalue(), "")
        self.assertIn("zzzzzz", err_typo.getvalue())

        # Empty vocab -> 0, stdout empty, stderr empty
        buf_vocab = io.StringIO()
        err_vocab = io.StringIO()
        with patch("sys.stdout", buf_vocab), patch("sys.stderr", err_vocab):
            rc_vocab = cli.main(
                ["find", "plans", "reusable", "-p", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc_vocab, 0)
        self.assertEqual(buf_vocab.getvalue(), "")
        self.assertEqual(err_vocab.getvalue(), "")

        # Matching -> 0, stdout has path
        buf_match = io.StringIO()
        with patch("sys.stdout", buf_match):
            rc_match = cli.main(
                ["find", "plans", "pln001", "-p", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc_match, 0)
        self.assertIn("pln001", buf_match.getvalue())


if __name__ == "__main__":
    unittest.main()

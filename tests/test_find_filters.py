"""Tests for aw find filter flags (--status, --id, --set) and upfront status validation.

These tests define the behavioral contract that spec 4sd62s's SQLite-cache rewrite
of aw find must preserve.

Case classification at HEAD before E-03/E-04:
- Failing at HEAD:
  - test_01_find_specs_filter_status_to_review (1)
  - test_02_find_specs_filter_id (2)
  - test_03_find_backlog_filter_set (3)
  - test_04_find_specs_selector_plus_status_intersects (4)
  - test_05_find_specs_status_bogusvalue_refused_exit_2 (5)
  - test_06_find_plans_status_bogusvalue_refused_exit_2 (6)
  - test_08_find_backlog_status_open_filtered (8)
  - test_09_find_all_status_accepted_open_and_bogusvalue (9) (filtering half fails at HEAD until generic branch filters)
  - test_10_find_walkthroughs_status_anything_accepted_zero_rows (10)
- Passing at HEAD (guards):
  - test_07_find_research_status_intake_accepted (7)
  - test_11_find_specs_no_flags_prints_all (11)
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R


class TestFindFilters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_filters_")
        self.repo_root = Path(self.temp_dir)

        # 1. Specs in .aw/records/specs/<status>/
        specs_to_review = self.repo_root / ".aw" / "records" / "specs" / "to-review"
        specs_approved = self.repo_root / ".aw" / "records" / "specs" / "approved"
        specs_to_review.mkdir(parents=True, exist_ok=True)
        specs_approved.mkdir(parents=True, exist_ok=True)

        self.spec_1 = specs_to_review / "20260927-spc001-01-spc001-one.spec.md"
        self.spec_1.write_text(
            "# Spec: One\n\n- Id: spc001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.spec_2 = specs_to_review / "20260927-spc002-01-spc002-two.spec.md"
        self.spec_2.write_text(
            "# Spec: Two\n\n- Id: spc002\n- Status: to-review\n- Set: setbeta\n",
            encoding="utf-8",
        )
        self.spec_3 = specs_approved / "20260927-spc003-01-spc003-three.spec.md"
        self.spec_3.write_text(
            "# Spec: Three\n\n- Id: spc003\n- Status: approved\n- Set: setalpha\n",
            encoding="utf-8",
        )

        # 2. Backlog items in .aw/records/backlog/open/ and done/
        bkl_open = self.repo_root / ".aw" / "records" / "backlog" / "open"
        bkl_done = self.repo_root / ".aw" / "records" / "backlog" / "done"
        bkl_open.mkdir(parents=True, exist_ok=True)
        bkl_done.mkdir(parents=True, exist_ok=True)

        self.bkl_1 = bkl_open / "20260927-setgamma-01-bkl001-item-one.backlog.md"
        self.bkl_1.write_text(
            "- Id: bkl001\n- Status: open\n- Set: setgamma\n- Work-Kind: bug\n- Priority: high\n\n## Summary\nOpen item\n",
            encoding="utf-8",
        )
        self.bkl_2 = bkl_done / "20260927-setdelta-01-bkl002-item-two.backlog.md"
        self.bkl_2.write_text(
            "- Id: bkl002\n- Status: done\n- Set: setdelta\n- Work-Kind: bug\n- Priority: low\n\n## Summary\nDone item\n",
            encoding="utf-8",
        )

        # 3. Release record in .aw/records/releases/
        releases_dir = self.repo_root / ".aw" / "records" / "releases"
        releases_dir.mkdir(parents=True, exist_ok=True)
        self.release_1 = releases_dir / "20260927-rel001-01-rel001-release.release.md"
        self.release_1.write_text(
            "# Release: 1.0.0\n\n- Id: rel001\n- Status: planned\n- Set: setrel\n",
            encoding="utf-8",
        )

        # 4. Plans in .aw/records/plans/pending/
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_1 = plans_dir / "20260927-setplan-01-pln001-plan-one.ipd.md"
        self.plan_1.write_text(
            "# IPD: Plan One\n\n- Id: pln001\n- Status: approved\n- Set: setplan\n",
            encoding="utf-8",
        )
        self.plan_2 = plans_dir / "20260927-setplan-02-pln002-plan-two.ipd.md"
        self.plan_2.write_text(
            "# IPD: Plan Two\n\n- Id: pln002\n- Status: draft\n- Set: setplan\n",
            encoding="utf-8",
        )

        # 5. Research in .aw/records/research/ (status: intake)
        research_dir = self.repo_root / ".aw" / "records" / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        name_report = R.format_name(
            R.ResearchName(
                date="20260927",
                set_id="resset",
                order="01",
                id6="res001",
                slug="research-one",
                model=None,
                kind="research-report",
            )
        )
        content_report = C.build_frontmatter(
            id6="res001",
            created="20260927",
            set_id="resset",
            order="01",
            topic=["test"],
            model=None,
            kind="research-report",
            status="intake",
            outcome="none-yet",
            summary="research summary",
        )
        self.research_1 = research_dir / name_report
        self.research_1.write_text(content_report, encoding="utf-8")

        # 6. Walkthrough in .aw/records/walkthroughs/ (no readable - Status:)
        walkthrough_dir = self.repo_root / ".aw" / "records" / "walkthroughs"
        walkthrough_dir.mkdir(parents=True, exist_ok=True)
        self.walkthrough_1 = walkthrough_dir / "20260927-wlk001-sample-walkthrough.md"
        self.walkthrough_1.write_text(
            "# Walkthrough: Sample\n\nDate: 2026-09-27\nStatus: EXECUTED\n\nNo front-matter dash status.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_find(self, extra_args: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["find", *extra_args, "--dir", str(self.repo_root)])
        return rc, buf.getvalue()

    def test_01_find_specs_filter_status_to_review(self):
        """(1) find specs --status to-review prints exactly the two to-review paths."""
        rc, out = self.run_find(["specs", "--status", "to-review", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("spc001" in line for line in lines))
        self.assertTrue(any("spc002" in line for line in lines))
        self.assertFalse(any("spc003" in line for line in lines))

    def test_02_find_specs_filter_id(self):
        """(2) find specs --id <id6> prints exactly one."""
        rc, out = self.run_find(["specs", "--id", "spc001", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("spc001", lines[0])

    def test_03_find_backlog_filter_set(self):
        """(3) find backlog --set <setid> prints only that Set's items."""
        rc, out = self.run_find(["backlog", "--set", "setgamma", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("bkl001", lines[0])
        self.assertNotIn("bkl002", out)

    def test_04_find_specs_selector_plus_status_intersects(self):
        """(4) find specs <selector> --status approved (selector plus flag) intersects."""
        rc, out = self.run_find(["specs", "setalpha", "--status", "approved", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("spc003", lines[0])
        self.assertNotIn("spc001", out)

    def test_05_find_specs_status_bogusvalue_refused_exit_2(self):
        """(5) find specs --status bogusvalue exits 2 and its message lists the spec statuses."""
        rc, out = self.run_find(["specs", "--status", "bogusvalue", "--json"])
        self.assertEqual(rc, 2)
        data = json.loads(out)
        self.assertEqual(data.get("exit_code"), 2)
        self.assertEqual(data.get("status"), "cannot-run")
        summary = data.get("summary", "")
        self.assertIn("to-review", summary)
        self.assertIn("approved", summary)

    def test_06_find_plans_status_bogusvalue_refused_exit_2(self):
        """(6) find plans --status bogusvalue exits 2."""
        rc, out = self.run_find(["plans", "--status", "bogusvalue", "--json"])
        self.assertEqual(rc, 2)
        data = json.loads(out)
        self.assertEqual(data.get("exit_code"), 2)
        self.assertEqual(data.get("status"), "cannot-run")

    def test_07_find_research_status_intake_accepted(self):
        """(7) find research --status intake is ACCEPTED (legacy spelling, exits 0)."""
        rc, out = self.run_find(["research", "--status", "intake", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("res001", lines[0])

    def test_08_find_backlog_status_open_filtered(self):
        """(8) find backlog --status open exits 0 and prints only open items."""
        rc, out = self.run_find(["backlog", "--status", "open", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("bkl001", lines[0])
        self.assertNotIn("bkl002", out)

    def test_09_find_all_status_accepted_open_and_bogusvalue(self):
        """(9) find all --status open is accepted AND find all --status bogusvalue is ALSO accepted at exit 0 with an empty result."""
        # find all --status open is accepted (valid for backlog)
        rc_open, out_open = self.run_find(["all", "--status", "open", "-p"])
        self.assertEqual(rc_open, 0)
        self.assertIn("bkl001", out_open)

        # and find all --status bogusvalue is ALSO accepted at exit 0 with an empty result - NOT refused.
        # This reverses the authored expectation after review measured that refusing it contradicts OQ-01:
        # 'all' always spans the six enum-less types, so validating it would make the broad query stricter than
        # the narrow one (find walkthroughs --status bogusvalue accepts the same value).
        rc_bogus, out_bogus = self.run_find(["all", "--status", "bogusvalue", "-p"])
        self.assertEqual(rc_bogus, 0)
        lines_bogus = [line.strip() for line in out_bogus.splitlines() if line.strip()]
        self.assertEqual(len(lines_bogus), 0)

    def test_10_find_walkthroughs_status_anything_accepted_zero_rows(self):
        """(10) find walkthroughs --status anything is ACCEPTED (exit 0, no enum) and returns ZERO rows."""
        # All walkthrough records lack a readable `- Status:`, so filtering on status returns zero rows.
        rc, out = self.run_find(["walkthroughs", "--status", "anything", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 0)

    def test_11_find_specs_no_flags_prints_all(self):
        """(11) find specs with no flags prints every spec (the unchanged path)."""
        rc, out = self.run_find(["specs", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 3)

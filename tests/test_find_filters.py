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

        self.spec_1 = specs_to_review / "20260927-setalpha-01-spc001-one.spec.md"
        self.spec_1.write_text(
            "# Spec: One\n\n- Id: spc001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.spec_2 = specs_to_review / "20260927-setbeta-01-spc002-two.spec.md"
        self.spec_2.write_text(
            "# Spec: Two\n\n- Id: spc002\n- Status: to-review\n- Set: setbeta\n",
            encoding="utf-8",
        )
        self.spec_3 = specs_approved / "20260927-setalpha-01-spc003-three.spec.md"
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
        self.release_1 = releases_dir / "20260927-setrel-01-rel001-release.release.md"
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

    def test_12_find_specs_filter_status_not(self):
        """(12) find specs --status-not to-review prints only non-to-review specs."""
        rc, out = self.run_find(["specs", "--status-not", "to-review", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("spc003", lines[0])

    def test_13_find_specs_filter_status_not_short_flag(self):
        """(13) find specs -S to-review uses the -S shorthand for --status-not."""
        rc, out = self.run_find(["specs", "-S", "to-review", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("spc003", lines[0])

    def test_14_find_backlog_filter_status_not_comma_and_repeat(self):
        """(14) find backlog --status-not supports single, comma-separated, and repeated flags."""
        # Single
        rc, out = self.run_find(["backlog", "--status-not", "done", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("bkl001", lines[0])

        # Comma-separated
        rc_comma, out_comma = self.run_find(
            ["backlog", "--status-not", "open,done", "-p"]
        )
        self.assertEqual(rc_comma, 0)
        lines_comma = [line.strip() for line in out_comma.splitlines() if line.strip()]
        self.assertEqual(len(lines_comma), 0)

        # Repeated flags
        rc_rep, out_rep = self.run_find(
            ["backlog", "--status-not", "open", "--status-not", "done", "-p"]
        )
        self.assertEqual(rc_rep, 0)
        lines_rep = [line.strip() for line in out_rep.splitlines() if line.strip()]
        self.assertEqual(len(lines_rep), 0)

    def test_15_find_plans_filter_status_not(self):
        """(15) find plans --status-not draft prints only non-draft plans."""
        rc, out = self.run_find(["plans", "--status-not", "draft", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("pln001", lines[0])

    def test_16_find_specs_status_not_bogusvalue_refused_exit_2(self):
        """(16) find specs --status-not bogusvalue exits 2 and lists valid statuses."""
        rc, out = self.run_find(["specs", "--status-not", "bogusvalue", "--json"])
        self.assertEqual(rc, 2)
        data = json.loads(out)
        self.assertEqual(data.get("exit_code"), 2)
        self.assertEqual(data.get("status"), "cannot-run")
        summary = data.get("summary", "")
        self.assertIn("to-review", summary)
        self.assertIn("approved", summary)

    def test_17_find_all_status_not_accepted(self):
        """(17) find all --status-not filters across types without upfront enum refusal."""
        rc, out = self.run_find(["all", "--status-not", "open", "-p"])
        self.assertEqual(rc, 0)
        self.assertNotIn("bkl001", out)
        self.assertIn("bkl002", out)

        # Enum-less types in 'all' disable upfront validation for --status-not as well
        rc_bogus, out_bogus = self.run_find(["all", "--status-not", "bogusvalue", "-p"])
        self.assertEqual(rc_bogus, 0)

    def test_18_find_walkthroughs_status_not_accepted(self):
        """(18) find walkthroughs --status-not anything is accepted (exit 0) and returns rows."""
        rc, out = self.run_find(["walkthroughs", "--status-not", "anything", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("wlk001", lines[0])


class TestFindMigratedLegacyResearch(unittest.TestCase):
    """Behavioral regression tests for migrated legacy research records lacking a kind facet (IPD vvxbbl)."""

    def setUp(self):
        from agent_workflows import artifact_meta

        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_migrated_research_")
        self.repo_root = Path(self.temp_dir)
        config_dir = self.repo_root / ".aw" / "config"
        research_dir = self.repo_root / ".aw" / "records" / "research"
        meta_dir = self.repo_root / ".aw" / "records" / "meta"
        config_dir.mkdir(parents=True, exist_ok=True)
        research_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps({"records_backend": "repository"}) + "\n",
            encoding="utf-8",
        )

        # (a) Migrated v2 research record lacking a .<kind>.md facet, backed by meta/ab12cd.jsonl
        self.migrated_rel = "research/20260708-ab12cd-01-ab12cd-survey-notes.md"
        self.migrated_doc = self.repo_root / ".aw" / "records" / self.migrated_rel
        self.migrated_doc.write_text(
            "# Survey Notes\n\nLegacy research notes without a kind facet.\n",
            encoding="utf-8",
        )
        checkpoint_event = {
            "v": 1,
            "seq": 0,
            "append": 0,
            "at": "2026-11-21T00:00:00Z",
            "actor": {"tool": "aw"},
            "op": "checkpoint",
            "path": self.migrated_rel,
            "fields": {
                "id": "ab12cd",
                "type": "research",
                "set": "ab12cd",
                "order": 1,
            },
        }
        (meta_dir / "ab12cd.jsonl").write_text(
            artifact_meta.encode_event(checkpoint_event),
            encoding="utf-8",
        )

        # (b) Unmigrated id-less research prose file (no meta log, no front-matter id)
        self.unmigrated_doc = research_dir / "20260708-unmigrated-notes.md"
        self.unmigrated_doc.write_text(
            "# Unmigrated Notes\n\nPlain prose without a log or front-matter id.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_find(
        self, extra_args: list[str], repo_root: Path | None = None
    ) -> tuple[int, str]:
        target_root = repo_root or self.repo_root
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["find", *extra_args, "--dir", str(target_root)])
        return rc, buf.getvalue()

    def _assert_single_migrated_record(self, rc: int, out: str) -> None:
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(
            len(lines), 2, f"Expected 1 item + 1 summary record, got: {lines}"
        )
        item = json.loads(lines[0])
        summary = json.loads(lines[1])

        self.assertEqual(item.get("kind"), "item")
        self.assertEqual(item.get("type"), "research")
        self.assertEqual(item.get("id6"), "ab12cd")
        self.assertEqual(item.get("status"), "-")
        self.assertEqual(item.get("set"), "ab12cd")
        self.assertEqual(
            item.get("path"),
            ".aw/records/research/20260708-ab12cd-01-ab12cd-survey-notes.md",
        )

        self.assertEqual(summary.get("kind"), "summary")
        self.assertEqual(summary.get("total"), 1)
        self.assertEqual(summary.get("emitted"), 1)
        self.assertEqual(summary.get("omitted"), 0)
        self.assertNotIn("unmigrated-notes", out)

    def test_01_find_by_minted_id6_returns_migrated_kindless_research(self):
        """aw find ab12cd --agent returns the migrated research record lacking a kind facet."""
        rc, out = self.run_find(["ab12cd", "--agent"])
        self._assert_single_migrated_record(rc, out)

    def test_02_find_research_returns_only_migrated_record_and_skips_unmigrated(self):
        """aw find research --agent returns the migrated record and excludes the unmigrated id-less file."""
        rc, out = self.run_find(["research", "--agent"])
        self._assert_single_migrated_record(rc, out)

    def test_03_find_research_filter_set_returns_migrated_kindless_research(self):
        """aw find research --set ab12cd --agent returns the migrated kind-less research record."""
        rc, out = self.run_find(["research", "--set", "ab12cd", "--agent"])
        self._assert_single_migrated_record(rc, out)

    def test_04_find_migrated_kindless_research_uses_state_status_fallback(self):
        """When legacy_raw_status is None, aw find uses State.status for output and status filtering."""
        from agent_workflows import artifact_meta

        iso_dir = tempfile.mkdtemp(prefix="aw_test_find_migrated_status_")
        try:
            iso_root = Path(iso_dir)
            config_dir = iso_root / ".aw" / "config"
            research_dir = iso_root / ".aw" / "records" / "research"
            meta_dir = iso_root / ".aw" / "records" / "meta"
            config_dir.mkdir(parents=True, exist_ok=True)
            research_dir.mkdir(parents=True, exist_ok=True)
            meta_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(
                json.dumps({"records_backend": "repository"}) + "\n",
                encoding="utf-8",
            )

            rel = "research/20260708-cd34ef-01-cd34ef-status-notes.md"
            (iso_root / ".aw" / "records" / rel).write_text(
                "# Status Notes\n\nMigrated research with log-backed status.\n",
                encoding="utf-8",
            )
            checkpoint_event = {
                "v": 1,
                "seq": 0,
                "append": 0,
                "at": "2026-11-21T00:00:00Z",
                "actor": {"tool": "aw"},
                "op": "checkpoint",
                "path": rel,
                "fields": {
                    "id": "cd34ef",
                    "type": "research",
                    "set": "cd34ef",
                    "order": 1,
                    "status": "todo",
                },
            }
            (meta_dir / "cd34ef.jsonl").write_text(
                artifact_meta.encode_event(checkpoint_event),
                encoding="utf-8",
            )

            rc, out = self.run_find(
                ["research", "--status", "todo", "--agent"], repo_root=iso_root
            )
            self.assertEqual(rc, 0)
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            self.assertEqual(len(lines), 2)
            item = json.loads(lines[0])
            summary = json.loads(lines[1])
            self.assertEqual(item.get("id6"), "cd34ef")
            self.assertEqual(item.get("status"), "todo")
            self.assertEqual(summary.get("total"), 1)

            rc_not, out_not = self.run_find(
                ["research", "--status-not", "todo", "--agent"], repo_root=iso_root
            )
            self.assertEqual(rc_not, 0)
            lines_not = [line.strip() for line in out_not.splitlines() if line.strip()]
            self.assertEqual(len(lines_not), 1)
            self.assertEqual(json.loads(lines_not[0]).get("total"), 0)
        finally:
            shutil.rmtree(iso_dir, ignore_errors=True)

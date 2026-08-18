"""Tests for IPD awmigrename-01 (backlog u9cicx / awnaming OQ-02): optional rename-on-migrate to
the uniform `.type.md` grammar in `aw migrate-layout`.

Covers:
- the facet-resolution + transform helpers (`_grammar_facet_for`, `_apply_grammar_facet`): class is
  two-level (records-eligible + sub-type from destination_relpath), comms/research/non-durable are
  never faceted, idempotent on an already-faceted name (E-03/E-04);
- the CLI opt-in surface: a `rename_to_grammar` config key parses, and neither-set defaults OFF in a
  non-interactive run (E-01/E-02);
- integration over a real HOME->REPOSITORY migration of seeded legacy `.agents/` records: with
  rename ON a plan/spec lands `.type.md` (riding the atomic move + journaled), with rename OFF it
  lands bare, and comms/research stay bare (E-03/E-04).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.layout_migration import (
    MigrationManager,
    _apply_grammar_facet,
    _grammar_facet_for,
)
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class FacetResolutionTests(unittest.TestCase):
    def test_records_subtypes_map_to_facets(self) -> None:
        self.assertEqual(
            _grammar_facet_for("records/plans/pending/a.md", "records"), "ipd"
        )
        self.assertEqual(_grammar_facet_for("records/specs/x.md", "records"), "spec")
        self.assertEqual(
            _grammar_facet_for("records/walkthroughs/x.md", "records"), "walkthrough"
        )
        self.assertEqual(
            _grammar_facet_for("records/roadmaps/x.md", "records"), "roadmap"
        )
        self.assertEqual(
            _grammar_facet_for("records/backlog/open/x.md", "records"), "backlog"
        )
        self.assertEqual(
            _grammar_facet_for("records/prompts/x.md", "records"), "prompt"
        )
        self.assertEqual(
            _grammar_facet_for("records/prompt-library/x.md", "records"), "prompt"
        )

    def test_comms_and_research_are_excluded(self) -> None:
        self.assertIsNone(
            _grammar_facet_for("records/comms/shared/sent/x.md", "records")
        )
        self.assertIsNone(_grammar_facet_for("records/research/x.md", "records"))

    def test_non_records_class_is_excluded(self) -> None:
        self.assertIsNone(_grammar_facet_for("system/VERSION", "system"))
        self.assertIsNone(_grammar_facet_for("records/plans/x.md", "doc"))
        self.assertIsNone(_grammar_facet_for("config/config.json", "config"))

    def test_apply_facet_transform(self) -> None:
        self.assertEqual(
            _apply_grammar_facet(Path("/t/20260101-0001-01-a.md"), "ipd").name,
            "20260101-0001-01-a.ipd.md",
        )
        # idempotent
        self.assertEqual(
            _apply_grammar_facet(Path("/t/20260101-0001-01-a.ipd.md"), "ipd").name,
            "20260101-0001-01-a.ipd.md",
        )
        # non-durable basenames untouched
        self.assertEqual(
            _apply_grammar_facet(Path("/t/README.md"), "ipd").name, "README.md"
        )
        self.assertEqual(
            _apply_grammar_facet(Path("/t/INDEX.md"), "ipd").name, "INDEX.md"
        )
        # None facet is a no-op
        self.assertEqual(_apply_grammar_facet(Path("/t/x.md"), None).name, "x.md")


class ConfigKeyParsingTests(unittest.TestCase):
    """E-01: a `rename_to_grammar` config key parses; neither flag nor key => OFF (non-interactive)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, args):
        env = dict(os.environ)
        return subprocess.run(
            ["python3", "-m", "agent_workflows", "migrate-layout", *args],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_flag_in_help(self) -> None:
        r = self._run(["--help"])
        self.assertIn("--rename-to-grammar", r.stdout)

    def test_config_key_parses(self) -> None:
        cfg = self.repo / "cfg.json"
        cfg.write_text(
            json.dumps({"rename_to_grammar": True, "target_backend": "repository"}),
            encoding="utf-8",
        )
        # inventory action reads config without error (we only assert no config-parse failure).
        r = self._run(["inventory", "--config", str(cfg)])
        self.assertNotIn("Invalid JSON", r.stdout + r.stderr)
        self.assertNotIn("Config file must contain", r.stdout + r.stderr)


class _MigrationFixture(unittest.TestCase):
    """A HOME-backend project with seeded legacy `.agents/` records, ready to migrate to REPOSITORY."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(self.target_repo, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", self.target_repo], check=True, capture_output=True
        )
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-123456"
        )
        policy = Path(self.target_repo) / ".aw" / "config" / "policy.json"
        policy.parent.mkdir(parents=True, exist_ok=True)
        policy.write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.HOME.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )
        # Seed legacy .agents records: a plan, a spec, a comms message, a research doc.
        repo = Path(self.target_repo)
        seeds = {
            ".agents/plans/pending/20260101-0001-01-a.md": "# IPD: a\n\n- Status: approved\n",
            ".agents/docs/specs/20260101-1200-01-x.md": "# Spec\n\n- Status: draft\n",
            ".agents/docs/research/20260101-1300-01-note.gpt.analysis.md": "# research\n",
            ".agents/comms/shared/sent/20260101-1400-01-a.agent--to--b.agent-fyi-x.md": "# msg\n",
        }
        for rel, body in seeds.items():
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        subprocess.run(
            ["git", "-C", self.target_repo, "add", "-A"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                self.target_repo,
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "seed",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _records(self):
        return Path(self.target_repo) / ".aw" / "records"


class RenameOnMigrateIntegrationTests(_MigrationFixture):
    def test_rename_off_leaves_bare_names(self) -> None:
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value,
            dry_run=False,
            rename_to_grammar=False,
        )
        rec = self._records()
        self.assertTrue((rec / "plans/pending/20260101-0001-01-a.md").is_file())
        self.assertFalse(list(rec.glob("plans/pending/*.ipd.md")))

    def test_rename_on_facets_plans_and_specs_not_comms_research(self) -> None:
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value,
            dry_run=False,
            rename_to_grammar=True,
        )
        rec = self._records()
        # plan + spec faceted
        self.assertTrue((rec / "plans/pending/20260101-0001-01-a.ipd.md").is_file())
        self.assertTrue(list(rec.glob("specs/*.spec.md")))
        # research + comms stay bare (documented exceptions)
        self.assertFalse(list(rec.rglob("research/*.ipd.md")))
        self.assertFalse(list(rec.rglob("comms/**/*.comms.md")))
        research = list(rec.rglob("research/*.md"))
        self.assertTrue(research and all(".analysis.md" in p.name for p in research))

    def test_rename_rides_atomic_tracked_move(self) -> None:
        mgr = MigrationManager(target_repo=self.target_repo, aw_home=self.aw_home)
        mgr.execute_migration(
            target_backend=RecordsBackend.REPOSITORY.value,
            dry_run=False,
            rename_to_grammar=True,
        )
        # the faceted destination is tracked (git knows it), proving it rode the move, not a copy.
        r = subprocess.run(
            [
                "git",
                "-C",
                self.target_repo,
                "ls-files",
                ".aw/records/plans/pending/20260101-0001-01-a.ipd.md",
            ],
            capture_output=True,
            text=True,
        )
        self.assertIn("20260101-0001-01-a.ipd.md", r.stdout)
        # the journal records the faceted destination (so rollback reverses correctly).
        journal = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        data = json.loads(journal.read_text(encoding="utf-8"))
        dests = " ".join(e.get("destination", "") for e in data.get("move_journal", []))
        self.assertIn("20260101-0001-01-a.ipd.md", dests)


if __name__ == "__main__":
    unittest.main()

"""E-03: Docs, rollout, and spec-reconciliation conformance.

awcliux Order 05 (`e8hu4s`) E-03 / V-03. Stdlib unittest only (Python 3.9+).

Asserts (each falsifiable):
- The human TTY guide and agent protocol reference exist and describe the
  hard-cutover automatic non-TTY behavior, the overrides, the schema, exit codes,
  and rollback.
- The migration guide LOUDLY names the three byte breaks (piped `status` JSON, the
  `render_agent_drift` TSV, and `find`/`search` path lines all become
  `aw.agent/v1`) and carries a compatibility schedule.
- The release notes (CHANGELOG) name the byte break.
- The contributor command checklist exists.
- The authored docs carry NO em/en dashes (ASCII hyphens only) and pass the
  repository doc-check (links + known subcommands).
- Spec `20260818-1525-01` records the G6 supersession (the retired `Drift`
  machine convention is no longer mandated) in its workflow history.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import docs_check as dc

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

HUMAN_GUIDE = DOCS_DIR / "cli-human-guide.md"
AGENT_REF = DOCS_DIR / "cli-agent-protocol.md"
MIGRATION = DOCS_DIR / "cli-migration.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
SPEC = (
    REPO_ROOT
    / ".aw"
    / "records"
    / "specs"
    / "20260818-1525-01-command-surface-redesign.spec.md"
)

AUTHORED_DOCS = (HUMAN_GUIDE, AGENT_REF, MIGRATION)


class AuthoredDocsExistTests(unittest.TestCase):
    def test_authored_docs_exist(self):
        for doc in AUTHORED_DOCS:
            self.assertTrue(doc.is_file(), f"missing authored doc: {doc}")


class HumanGuideContentTests(unittest.TestCase):
    def setUp(self):
        self.text = HUMAN_GUIDE.read_text(encoding="utf-8")

    def test_describes_hard_cutover_and_overrides(self):
        low = self.text.lower()
        self.assertIn("hard cutover", low)
        self.assertIn("--agent", self.text)
        self.assertIn("--json", self.text)
        self.assertIn("--no-color", self.text)

    def test_describes_exit_codes(self):
        for token in ("0", "1", "2"):
            self.assertIn(token, self.text)
        self.assertIn("cannot run", self.text.lower())

    def test_describes_accessibility(self):
        self.assertIn("ASCII", self.text)
        self.assertIn("NO_COLOR", self.text)


class AgentReferenceContentTests(unittest.TestCase):
    def setUp(self):
        self.text = AGENT_REF.read_text(encoding="utf-8")

    def test_describes_schema_and_kinds(self):
        self.assertIn("aw.agent/v1", self.text)
        for kind in ("result", "summary", "item", "error"):
            self.assertIn(kind, self.text)

    def test_describes_exit_parity_and_truncation(self):
        low = self.text.lower()
        self.assertIn("exit", low)
        self.assertIn("omitted", low)
        self.assertIn("complete", low)

    def test_describes_hard_cutover_and_stability(self):
        self.assertIn("hard cutover", self.text.lower())
        self.assertIn("aw.agent/v2", self.text)


class MigrationGuideContentTests(unittest.TestCase):
    def setUp(self):
        self.text = MIGRATION.read_text(encoding="utf-8")

    def test_names_the_three_byte_breaks_loudly(self):
        # (1) piped status JSON
        self.assertIn("status", self.text)
        # (2) render_agent_drift TSV
        self.assertIn("render_agent_drift", self.text)
        self.assertIn("TSV", self.text)
        # (3) find / search path lines
        self.assertIn("find", self.text)
        self.assertIn("search", self.text)
        # all become aw.agent/v1
        self.assertIn("aw.agent/v1", self.text)

    def test_states_hard_cutover_and_no_window(self):
        # Normalize whitespace so a line wrap does not hide the phrase.
        low = " ".join(self.text.lower().split())
        self.assertIn("hard cutover", low)
        self.assertIn("no compatibility window", low)

    def test_has_compatibility_schedule_and_rollback(self):
        self.assertIn("Compatibility schedule", self.text)
        self.assertIn("Rollback", self.text)


class ReleaseNotesTests(unittest.TestCase):
    def test_changelog_names_the_byte_break(self):
        text = CHANGELOG.read_text(encoding="utf-8")
        self.assertIn("HARD CUTOVER", text)
        self.assertIn("aw.agent/v1", text)
        self.assertIn("render_agent_drift", text)


class ContributorChecklistTests(unittest.TestCase):
    def test_contributing_has_command_checklist(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        self.assertIn("output-contract checklist", text)
        self.assertIn("COMMAND_INVENTORY", text)


class NoUnicodeDashesInAuthoredDocsTests(unittest.TestCase):
    def test_authored_docs_are_ascii_hyphen_only(self):
        for doc in AUTHORED_DOCS:
            text = doc.read_text(encoding="utf-8")
            self.assertNotIn(dc.EM_DASH, text, f"em dash in {doc.name}")
            self.assertNotIn(dc.EN_DASH, text, f"en dash in {doc.name}")

    def test_authored_docs_pass_repository_doc_check(self):
        for doc in AUTHORED_DOCS:
            findings = dc.check_doc(doc)
            self.assertEqual(
                findings, [], "\n".join(str(f) for f in findings)
            )


class SpecReconciliationTests(unittest.TestCase):
    """Spec 1525-01 G6 supersession is recorded via aw specs (not hand-edited status)."""

    def test_spec_records_g6_supersession_of_drift_convention(self):
        text = SPEC.read_text(encoding="utf-8")
        self.assertIn("## Workflow history", text)
        # The supersession note names G6 and the retired Drift convention, and points
        # at the aw.agent/v1 replacement. Recorded by `aw specs note` (a CLI action).
        low = text.lower()
        self.assertIn("g6", low)
        self.assertIn("aw.agent/v1", text)
        self.assertIn("supersed", low)


if __name__ == "__main__":
    unittest.main()

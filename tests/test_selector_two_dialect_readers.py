"""Restored outcome coverage for the two-dialect selector readers.

This module guards the two-dialect selector readers in ``agent_workflows.selectors``:
  * ``_read_id``
  * ``_read_status``
  * ``_read_setid``

It restates and pins the contracts established by two executed plans:
  * IPD ``76w6mq``: region-bounding the identity, status, and set readers to
    ``metadata_region`` so quoted example front matter in record bodies is never
    mistaken for artifact declarations.
  * IPD ``xo3244``: teaching the internal selector readers both front-matter dialects
    (bullet first, falling back to YAML front matter in leading ``---`` fences for
    research and roadmaps), with case-sensitive key lookups and YAML scalar normalization.

Both ancestor test files that pinned these contracts:
  * ``tests/test_id_metadata_region.py``
  * ``tests/test_selector_zero_open.py``
were deleted by commit ``19313eed`` ("test: trim test suite from 9,136 to under 2,000 tests",
2026-09-24). Rather than restoring the deleted files verbatim (which contained code-structure
and internal-constant pins prohibited by GUIDING_PRINCIPLES.md P16), this module asserts
observable outcomes and behaviors on fixture records in temporary repositories.

Tests here avoid live-corpus dependency (no ``livecorpus`` marker) and execute in-memory or
in temporary directories without invoking external subprocesses (no ``slow`` marker), so they
run by default on bare ``python3 -m pytest``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import research_contract
from agent_workflows import selectors


class HarnessProvenanceTests(unittest.TestCase):
    """Prove the test harness imports agent_workflows from the local workspace checkout."""

    def test_harness_measures_workspace_package(self):
        """selectors module must be imported from the workspace root containing this test file."""
        workspace_root = Path(__file__).resolve().parent.parent
        selector_file = Path(selectors.__file__).resolve()
        self.assertTrue(
            selector_file.is_relative_to(workspace_root),
            f"Expected selectors.__file__ ({selector_file}) to be under workspace ({workspace_root})",
        )


class SelectorTwoDialectReadersBase(unittest.TestCase):
    """Base fixture providing isolated temporary repository trees."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory(prefix="aw_test_two_dialect_")
        self.repo_root = Path(self.tmpdir.name)
        for rtype in ("research", "plans", "prompts", "specs", "backlog"):
            (self.repo_root / ".aw" / "records" / rtype).mkdir(
                parents=True, exist_ok=True
            )

    def tearDown(self):
        self.tmpdir.cleanup()

    def make_research_record(
        self,
        rel_path: str,
        *,
        id: str | None = None,
        status: str | None = None,
        set: str | None = None,
        extra_frontmatter: str = "",
        body: str = "# Research Document\n\nResearch body prose.\n",
    ) -> Path:
        """Create a YAML-front-matter research record in the temporary repository."""
        target = self.repo_root / ".aw" / "records" / "research" / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = ["---"]
        if id is not None:
            lines.append(f"id: {id}")
        if status is not None:
            lines.append(f"status: {status}")
        if set is not None:
            lines.append(f"set: {set}")
        if extra_frontmatter:
            lines.append(extra_frontmatter.strip())
        lines.append("---")
        lines.append(body)
        target.write_text("\n".join(lines), encoding="utf-8")
        return target

    def make_bullet_plan(
        self,
        rel_path: str,
        *,
        id: str = "pln001",
        status: str = "draft",
        set: str = "testset",
        body: str = "## Workflow history\n- 2026-09-28 draft (tester): created\n",
    ) -> Path:
        """Create a bullet-front-matter plan record in the temporary repository."""
        target = self.repo_root / ".aw" / "records" / "plans" / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f"# Plan Title\n\n"
            f"- Id: {id}\n"
            f"- Status: {status}\n"
            f"- Set: {set}\n\n"
            f"{body}"
        )
        target.write_text(content, encoding="utf-8")
        return target


class BoundedReaderMetadataRegionTests(SelectorTwoDialectReadersBase):
    """Pin the metadata-region bound on _read_id, _read_status, and _read_setid (E-03)."""

    def test_metadata_region_bounds_all_three_readers_against_quoted_prose(self):
        """A record quoting an example metadata block returns its own declared values, never quoted ones."""
        # Record declares aaaaaa/reference/realset in YAML front matter, but quotes
        # - Id: ffffff, - Status: approved, - Set: quotedset in body prose.
        quoting_text = (
            "---\n"
            "id: aaaaaa\n"
            "status: reference\n"
            "set: realset\n"
            "---\n"
            "# Document About Metadata Format\n\n"
            "Here is an example bullet front-matter block quoted for documentation:\n\n"
            "```markdown\n"
            "- Id: ffffff\n"
            "- Status: approved\n"
            "- Set: quotedset\n"
            "```\n\n"
            "## Workflow history\n"
            "- 2026-09-28 reference (tester): created\n"
        )

        self.assertEqual(selectors._read_id(quoting_text), "aaaaaa")
        self.assertEqual(selectors._read_status(quoting_text), "reference")
        self.assertEqual(selectors._read_setid(quoting_text), "realset")

    def test_metadata_region_prevents_id6_collision_from_quoted_block(self):
        """Quoted id6 in a second record's body must not collide with the genuine artifact's id6."""
        # 1. Genuine research report declaring id6 aaaaaa
        genuine = self.make_research_record(
            "20260928-realset-01-aaaaaa-genuine.research-report.md",
            id="aaaaaa",
            status="reference",
            set="realset",
        )
        # 2. Quoting research report declaring bbbbbb, but quoting - Id: aaaaaa in its body before ##
        self.make_research_record(
            "20260928-realset-02-bbbbbb-quoting.research-report.md",
            id="bbbbbb",
            status="reference",
            set="realset",
            body=(
                "# Quoting Report\n\n"
                "Reviewing artifact aaaaaa metadata format:\n"
                "- Id: aaaaaa\n"
                "- Status: approved\n"
                "- Set: realset\n\n"
                "## Discussion\n"
            ),
        )

        res = selectors.resolve(self.repo_root, "research", "aaaaaa")
        self.assertEqual(res.kind, selectors.MATCH_ID6)
        self.assertEqual(len(res.paths), 1)
        self.assertEqual(res.paths[0], genuine.resolve())


class YamlKeyLookupCaseSensitivityTests(SelectorTwoDialectReadersBase):
    """Pin the case-sensitive YAML front-matter key lookup (E-04)."""

    def test_capitalized_yaml_keys_not_matched_by_readers_or_find(self):
        """Capitalized YAML keys (as in handoff prompts) must not match lowercase id/status/set."""
        handoff_text = (
            "---\n"
            "Kind: session-handoff\n"
            "Status: draft\n"
            "Date: 2026-09-28\n"
            "---\n"
            "# Session Handoff\n\n"
            "Prompt body notes.\n"
        )
        target = (
            self.repo_root
            / ".aw"
            / "records"
            / "prompts"
            / "20260928-prm001-01-prm001-handoff.prompt.md"
        )
        target.write_text(handoff_text, encoding="utf-8")

        self.assertIsNone(selectors._read_id(handoff_text))
        self.assertIsNone(selectors._read_status(handoff_text))
        self.assertIsNone(selectors._read_setid(handoff_text))

        # Querying status 'draft' against prompts must match nothing (not the capitalized Status)
        res = selectors.resolve(self.repo_root, "prompts", "draft")
        self.assertIsNone(res.kind)
        self.assertEqual(len(res.paths), 0)

    def test_case_sensitivity_is_lookup_not_parser_failure(self):
        """Confirm research_contract.parse_frontmatter exposes capitalized keys as-is."""
        handoff_text = (
            "---\n"
            "Kind: session-handoff\n"
            "Status: draft\n"
            "Date: 2026-09-28\n"
            "---\n"
            "# Session Handoff\n"
        )
        data = research_contract.parse_frontmatter(handoff_text)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("Kind"), "session-handoff")
        self.assertEqual(data.get("Status"), "draft")
        self.assertEqual(data.get("Date"), "2026-09-28")
        self.assertIsNone(data.get("kind"))
        self.assertIsNone(data.get("status"))


class YamlIdFallbackObservableResolutionTests(SelectorTwoDialectReadersBase):
    """Pin YAML id: fallback with observable match kind and mutating verb refusal (E-05)."""

    def test_yaml_id_fallback_resolves_unique_id6_and_succeeds_for_mutation(self):
        """Owner id6 query resolves with kind=id6 and resolve_for_mutation succeeds despite sibling substring."""
        owner = self.make_research_record(
            "20260928-tgtset-01-tgt001-primary-notes.research-report.md",
            id="tgt001",
            status="reference",
            set="tgtset",
        )
        # Sibling cites tgt001 in its filename slug, so a substring match would match BOTH
        self.make_research_record(
            "20260928-tgtset-02-sib001-reconciles-tgt001-findings.research-report.md",
            id="sib001",
            status="reference",
            set="tgtset",
        )

        # resolve_for_mutation returns a 2-tuple: (paths, error_message)
        paths, err = selectors.resolve_for_mutation(
            self.repo_root, "research", "tgt001"
        )
        self.assertIsNone(err)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0], owner.resolve())

        res = selectors.resolve(self.repo_root, "research", "tgt001")
        self.assertEqual(res.kind, selectors.MATCH_ID6)
        self.assertIn(res.kind, selectors.UNIQUE_KINDS)
        self.assertEqual(len(res.paths), 1)
        self.assertEqual(res.paths[0], owner.resolve())

    def test_same_filename_trap_demonstration(self):
        """Demonstrate why citing sibling is necessary: without it, substring query matches owner alone."""
        owner = self.make_research_record(
            "20260928-tgtset-01-tgt001-primary-notes.research-report.md",
            id="tgt001",
            status="reference",
            set="tgtset",
        )
        # When only the owner exists, substring matching also finds exactly 1 path (vacuous test)
        res = selectors.resolve(self.repo_root, "research", "tgt001")
        self.assertEqual(len(res.paths), 1)
        self.assertEqual(res.paths[0], owner.resolve())


class YamlScalarNormalizationAndBulletAsymmetryTests(SelectorTwoDialectReadersBase):
    """Pin YAML scalar normalization and the intentional bullet-dialect asymmetry (E-06)."""

    def test_yaml_scalars_strip_backticks_and_quotes_for_bare_resolution(self):
        """Backtick-wrapped and quoted YAML scalars resolve to bare selectors for set and status."""
        p_probe = self.make_research_record(
            "20260928-normset-01-nrm001-first-item.research-report.md",
            id="nrm001",
            status="reference",
            set="`probeset`",
        )
        p_quote = self.make_research_record(
            "20260928-normset-02-nrm002-second-item.research-report.md",
            id="nrm002",
            status="'reference'",
            set='"quotedset"',
        )

        # Selectors resolve by bare tokens
        res_probe = selectors.resolve(self.repo_root, "research", "probeset")
        self.assertEqual(res_probe.kind, selectors.MATCH_SETID)
        self.assertEqual(len(res_probe.paths), 1)
        self.assertEqual(res_probe.paths[0], p_probe.resolve())

        res_quote = selectors.resolve(self.repo_root, "research", "quotedset")
        self.assertEqual(res_quote.kind, selectors.MATCH_SETID)
        self.assertEqual(len(res_quote.paths), 1)
        self.assertEqual(res_quote.paths[0], p_quote.resolve())

        # Readers return stripped scalars
        text_probe = p_probe.read_text(encoding="utf-8")
        text_quote = p_quote.read_text(encoding="utf-8")
        self.assertEqual(selectors._read_setid(text_probe), "probeset")
        self.assertEqual(selectors._read_setid(text_quote), "quotedset")
        self.assertEqual(selectors._read_status(text_quote), "reference")

    def test_bullet_setid_preserves_backticks_verbatim_without_normalization(self):
        """Bullet front-matter reader deliberately preserves backticks verbatim on - Set:."""
        bullet_text = (
            "# Plan Record\n\n"
            "- Id: asy001\n"
            "- Status: draft\n"
            "- Set: `bulletset`\n\n"
            "## Workflow history\n"
            "- 2026-09-28 draft (tester): created\n"
        )
        self.assertEqual(selectors._read_setid(bullet_text), "`bulletset`")


class YamlStatusAndSetFallbacksDirectTests(SelectorTwoDialectReadersBase):
    """Direct behavioral tests for YAML status: and set: fallbacks (E-07)."""

    def test_yaml_status_fallback_resolves_status_directly(self):
        """YAML status: fallback resolves research records by status selector."""
        doc = self.make_research_record(
            "20260928-directset-01-drc001-notes.research-report.md",
            id="drc001",
            status="reference",
            set="directset",
        )
        text = doc.read_text(encoding="utf-8")
        self.assertEqual(selectors._read_status(text), "reference")

        res = selectors.resolve(self.repo_root, "research", "reference")
        self.assertEqual(res.kind, selectors.MATCH_STATUS)
        self.assertEqual(len(res.paths), 1)
        self.assertEqual(res.paths[0], doc.resolve())

    def test_yaml_setid_fallback_resolves_setid_directly(self):
        """YAML set: fallback resolves research records by setid selector."""
        doc = self.make_research_record(
            "20260928-directset-01-drc001-notes.research-report.md",
            id="drc001",
            status="reference",
            set="directset",
        )
        text = doc.read_text(encoding="utf-8")
        self.assertEqual(selectors._read_setid(text), "directset")

        res = selectors.resolve(self.repo_root, "research", "directset")
        self.assertEqual(res.kind, selectors.MATCH_SETID)
        self.assertEqual(len(res.paths), 1)
        self.assertEqual(res.paths[0], doc.resolve())

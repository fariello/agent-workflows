"""Restore behavioral coverage of SCAN_ROOTS classification completeness (IPD 2uw25m).

Guarantees that every artifact_core.SCAN_ROOTS entry either classifies to a
TreePolicy through attention._classify_tree or is a member of a closed, named,
separately justified exemption set, so any root scanned and silently dropped
(the TODO.md defect closed by diof9n) fails the test suite.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Iterable, List

from agent_workflows import artifact_core, attention

CITATION_ONLY_ROOT_DOCS = frozenset(
    {
        "DECISIONS.md",
        "README.md",
        "ARCHITECTURE.md",
    }
)
LEGACY_CONTAINER_ROOTS = frozenset({".agents/docs"})


def find_unclassified_roots(roots: Iterable[str] | None = None) -> List[str]:
    """Return sorted scan roots that classify to None and are not exempted."""
    if roots is None:
        roots = artifact_core.SCAN_ROOTS
    exempt = CITATION_ONLY_ROOT_DOCS | LEGACY_CONTAINER_ROOTS
    return sorted(
        root
        for root in roots
        if root not in exempt and attention._classify_tree(root) is None
    )


class ScanRootClassificationTests(unittest.TestCase):
    """Restore behavioral coverage of SCAN_ROOTS classification completeness (IPD 2uw25m)."""

    CITATION_ONLY_ROOT_DOCS = CITATION_ONLY_ROOT_DOCS
    LEGACY_CONTAINER_ROOTS = LEGACY_CONTAINER_ROOTS

    def test_no_scan_root_is_scanned_then_silently_dropped(self):
        """E-01: Every SCAN_ROOTS entry classifies or belongs to the closed exemption set."""
        offenders = find_unclassified_roots(artifact_core.SCAN_ROOTS)
        self.assertEqual(
            offenders,
            [],
            "These SCAN_ROOTS entries are scanned but classify to None, so anything written "
            "there is dropped with no drift violation and vanishes silently: "
            f"{offenders}. Either give the root a `TreePolicy` so a write is reported, or "
            "remove it from SCAN_ROOTS so it is honestly out of scope. If it is documentation "
            "scanned only for CITATIONS, add it to CITATION_ONLY_ROOT_DOCS with a reason.",
        )

    def test_the_exemptions_are_live_and_justified(self):
        """E-02: Every exempted root exists and is scanned, and .agents/docs typed children classify."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            for name in CITATION_ONLY_ROOT_DOCS:
                (repo / name).write_text(f"#{name}\n", encoding="utf-8")
            legacy_dir = repo / ".agents" / "docs"
            legacy_dir.mkdir(parents=True)
            (legacy_dir / "note.md").write_text("# Note\n", encoding="utf-8")

            scanned_files = artifact_core.iter_scan_files(repo)
            scanned_rel_paths = [f.relative_to(repo).as_posix() for f in scanned_files]

            exempt = CITATION_ONLY_ROOT_DOCS | LEGACY_CONTAINER_ROOTS
            for name in exempt:
                prefix = name if name.endswith("/") else f"{name}/"
                found = any(
                    rel == name or rel.startswith(prefix) for rel in scanned_rel_paths
                )
                self.assertTrue(
                    found,
                    f"Exempted root {name!r} is not observed in iter_scan_files output: {scanned_rel_paths}",
                )

        self.assertIsNotNone(attention._classify_tree(".agents/docs/specs/x.spec.md"))
        self.assertIsNotNone(attention._classify_tree(".agents/docs/research/y.md"))

    def test_todo_md_is_not_scanned(self):
        """E-03: TODO.md is not returned by iter_scan_files or attention.scan."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "TODO.md").write_text("# TODO\n- [ ] item\n", encoding="utf-8")
            (repo / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")

            scanned_files = artifact_core.iter_scan_files(repo)
            scanned_rel_paths = [f.relative_to(repo).as_posix() for f in scanned_files]

            self.assertNotIn("TODO.md", scanned_rel_paths)
            self.assertIn("DECISIONS.md", scanned_rel_paths)

            items, drift = attention.scan(repo)
            item_paths = [item.path for item in items]
            drift_locations = [d.location for d in drift]

            self.assertFalse(
                any("TODO.md" in p for p in item_paths),
                f"TODO.md unexpectedly appeared in attention.scan items: {item_paths}",
            )
            self.assertFalse(
                any("TODO.md" in loc for loc in drift_locations),
                f"TODO.md unexpectedly appeared in attention.scan drift: {drift_locations}",
            )

    def test_the_invariant_detects_an_unclassified_root(self):
        """E-05: Offender helper returns appended unclassified roots in sorted order."""
        roots = artifact_core.SCAN_ROOTS + ("TODO.md", ".aw/records/no-such-tree")
        offenders = find_unclassified_roots(roots)
        self.assertEqual(offenders, [".aw/records/no-such-tree", "TODO.md"])


if __name__ == "__main__":
    unittest.main()

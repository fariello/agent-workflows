"""Tests pinning the two attention records-tree blind spots (Hole 1 and Hole 2),
the exemption decision, and non-regressions (IPD 1qt1u3, Set attnblind).

Hole 1 (per-file): An unclassified file under .aw/records/ with no TreePolicy was silently
dropped because the unclassified branch checked `rel.startswith(".agents/")`.
Rekeyed onto `is_exempt_unclassified`.

Hole 2 (tree discovery): A tree under .aw/records/ with no scan root was never opened by
iter_scan_files, so no per-file branch could see it.
Closed by shallow records-root discovery pass emitting `attention.uninventoried-tree`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import attention as att
from agent_workflows import attention_contract as A

REPO_ROOT = Path(__file__).resolve().parent.parent


class AttentionBlindSpotHolesTests(unittest.TestCase):
    """Pin Hole 1 (per-file) and Hole 2 (tree discovery)."""

    def test_hole1_per_file_unclassified_drift(self):
        """Hole 1: .aw/records/newtype/x.md forced into scan roots yields attention.unclassified-tree."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # Modern path under .aw/records/
            modern_dir = repo / ".aw" / "records" / "newtype"
            modern_dir.mkdir(parents=True)
            modern_file = modern_dir / "x.md"
            modern_file.write_text("# Test doc\n", encoding="utf-8")

            # Legacy control under .agents/
            legacy_dir = repo / ".agents" / "newtype"
            legacy_dir.mkdir(parents=True)
            legacy_file = legacy_dir / "x.md"
            legacy_file.write_text("# Test doc\n", encoding="utf-8")

            # Force root set through core.iter_scan_files (F-06: patching core.SCAN_ROOTS passes vacuously)
            orig_iter = core.iter_scan_files

            def forced_iter(root, scan_roots=None):
                extra = [".aw/records/newtype", ".agents/newtype"]
                current_roots = list(scan_roots or core.SCAN_ROOTS) + extra
                return orig_iter(root, scan_roots=tuple(current_roots))

            with mock.patch.object(core, "iter_scan_files", side_effect=forced_iter):
                items, drift = att.scan(repo)

            modern_drift = [
                d
                for d in drift
                if d.rule == "attention.unclassified-tree"
                and d.location == ".aw/records/newtype/x.md"
            ]
            legacy_drift = [
                d
                for d in drift
                if d.rule == "attention.unclassified-tree"
                and d.location == ".agents/newtype/x.md"
            ]

            self.assertEqual(
                len(modern_drift),
                1,
                f"Expected exactly 1 attention.unclassified-tree drift for modern path, got: {modern_drift}",
            )
            self.assertEqual(
                len(legacy_drift),
                1,
                f"Expected exactly 1 attention.unclassified-tree drift for legacy control, got: {legacy_drift}",
            )

    def test_hole2_records_tree_discovery_drift(self):
        """Hole 2: .aw/records/newtype/ without scan roots yields attention.uninventoried-tree and valid: False."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            new_tree = repo / ".aw" / "records" / "newtype"
            new_tree.mkdir(parents=True)
            (new_tree / "x.md").write_text("# Test\n", encoding="utf-8")

            # Regular scan with default SCAN_ROOTS (NO root for newtype)
            items, drift = att.scan(repo)

            rendered = json.loads(att.render_json(items, drift))
            uninventoried_drift = [
                d
                for d in drift
                if d.rule == "attention.uninventoried-tree"
                and d.location == ".aw/records/newtype"
            ]

            self.assertEqual(
                len(uninventoried_drift),
                1,
                f"Expected 1 attention.uninventoried-tree drift for .aw/records/newtype; observed drift={drift}, valid={rendered.get('valid')}",
            )
            self.assertFalse(
                rendered.get("valid"),
                f"Expected render_json valid to be False for uninventoried tree, got: {rendered.get('valid')}",
            )


class AttentionExemptionsAndNonRegressionsTests(unittest.TestCase):
    """Pin the exemption decision and non-regressions (E-06)."""

    def test_exemptions_predicate_and_scan(self):
        """E-01 / E-06: Root docs and non-artifact names are exempt from per-file unclassified drift."""
        # 1. Direct predicate tests (V-01 contract)
        self.assertTrue(A.is_exempt_unclassified("DECISIONS.md"))
        self.assertTrue(A.is_exempt_unclassified("README.md"))
        self.assertTrue(A.is_exempt_unclassified("ARCHITECTURE.md"))
        self.assertTrue(A.is_exempt_unclassified(".aw/records/plans/README.md"))
        self.assertFalse(A.is_exempt_unclassified(".aw/records/newtype/x.md"))
        self.assertFalse(A.is_exempt_unclassified(".agents/newtype/x.md"))

        # 2. In scan fixture
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
            (repo / "README.md").write_text("# Readme\n", encoding="utf-8")
            (repo / "ARCHITECTURE.md").write_text("# Arch\n", encoding="utf-8")
            plans_dir = repo / ".aw" / "records" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "README.md").write_text("# Plans Readme\n", encoding="utf-8")

            items, drift = att.scan(repo)
            tree_drift = [d for d in drift if "tree" in d.rule]
            self.assertEqual(
                tree_drift,
                [],
                f"Exempt root docs and READMEs must not produce tree drift, got: {tree_drift}",
            )

    def test_excluded_trees_non_regression(self):
        """Non-regression (a): Excluded trees yield neither an attention item nor drift."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            for tree_name in (
                "walkthroughs",
                "roadmaps",
                "prompt-library",
                "comms",
                "reviews",
            ):
                d = repo / ".aw" / "records" / tree_name
                d.mkdir(parents=True)
                (d / "note.md").write_text("# Note\n", encoding="utf-8")

            items, drift = att.scan(repo)
            self.assertEqual(items, [])
            tree_drift = [d for d in drift if "tree" in d.rule]
            self.assertEqual(tree_drift, [])

    def test_runs_dir_ignored(self):
        """Non-regression (b): .aw/records/runs is ignored and not reported as uninventoried."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            runs_dir = repo / ".aw" / "records" / "runs"
            runs_dir.mkdir(parents=True)
            (runs_dir / "run_state.json").write_text("{}", encoding="utf-8")

            items, drift = att.scan(repo)
            uninventoried = [
                d for d in drift if d.rule == "attention.uninventoried-tree"
            ]
            self.assertEqual(uninventoried, [])

    def test_type_filters_skips_discovery(self):
        """Non-regression (c): type_filters-narrowed scan skips tree discovery."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            # An uninventoried tree alongside
            (repo / ".aw" / "records" / "uninventoried").mkdir(parents=True)

            items, drift = att.scan(repo, type_filters={"plans"})
            uninventoried = [
                d for d in drift if d.rule == "attention.uninventoried-tree"
            ]
            self.assertEqual(uninventoried, [])

    def test_scan_fresh_directory_write_on_read(self):
        """Non-regression (d): scan on a fresh empty directory creates no .aw/ and reports nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            items, drift = att.scan(repo)
            self.assertEqual(items, [])
            self.assertEqual(drift, [])
            self.assertFalse((repo / ".aw").exists())

    def test_legacy_agents_fallback_discovery(self):
        """Non-regression (d in V-04): fallback to .agents discovers uninventoried trees when .aw/records absent."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            new_leg = repo / ".agents" / "newtype"
            new_leg.mkdir(parents=True)
            (new_leg / "x.md").write_text("# Legacy test\n", encoding="utf-8")

            items, drift = att.scan(repo)
            uninventoried = [
                d
                for d in drift
                if d.rule == "attention.uninventoried-tree"
                and d.location == ".agents/newtype"
            ]
            self.assertEqual(len(uninventoried), 1)

    def test_live_repository_no_tree_drift(self):
        """Class-scoped property on live repository: zero findings whose rule contains 'tree'."""
        items, drift = att.scan(REPO_ROOT)
        tree_drift = [d for d in drift if "tree" in d.rule]
        self.assertEqual(
            tree_drift,
            [],
            f"Expected zero tree-class findings on repo root, got: {tree_drift}",
        )

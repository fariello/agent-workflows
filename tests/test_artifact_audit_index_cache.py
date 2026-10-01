"""Tests for artifact_audit index cache invalidation and memoization (IPD dea7dr).

Validates that _INDEX_CACHE invalidation sees changes across all routes:
- Route 1: same-tick addition with pinned directory mtime
- Route 2: addition in untyped record trees (e.g. .aw/records/prompt-library/)
- Route 3: addition four levels deep under .aw/records/
- Route 2 compound: untyped tree addition with pinned directory mtime
- Route 3 compound: deep directory addition with pinned directory mtime
- Memoization: unchanged trees reuse cached ArtifactIndex; real changes rebuild it.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit


class TestArtifactAuditIndexCache(unittest.TestCase):
    """Test index cache invalidation and memoization behavior."""

    def setUp(self) -> None:
        _audit._INDEX_CACHE.clear()

    def tearDown(self) -> None:
        _audit._INDEX_CACHE.clear()

    def test_route1_same_tick_addition_detected(self) -> None:
        """Route 1: same-tick additions in pending/ are seen even if directory mtime does not advance."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_a = pending_dir / "20260901-set1-01-aaaaaa-plan-a.ipd.md"
            art_a.write_text("# Plan A\n- Id: aaaaaa\n- Status: draft\n")

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = pending_dir.stat()
            art_b = pending_dir / "20260901-set1-02-bbbbbb-plan-b.ipd.md"
            art_b.write_text("# Plan B\n- Id: bbbbbb\n- Status: draft\n")
            os.utime(pending_dir, ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns))

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

    def test_route2_untyped_tree_addition_detected(self) -> None:
        """Route 2: additions in untyped record trees (like prompt-library) are seen without pinning."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prompts_dir = root / ".aw" / "records" / "prompt-library"
            prompts_dir.mkdir(parents=True)

            art_a = prompts_dir / "20260901-set2-01-aaaaaa-prompt-a.md"
            art_a.write_text("# Prompt A\n- Id: aaaaaa\n- Status: draft\n")

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            art_b = prompts_dir / "20260901-set2-02-bbbbbb-prompt-b.md"
            art_b.write_text("# Prompt B\n- Id: bbbbbb\n- Status: draft\n")

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

    def test_route3_deep_directory_addition_detected(self) -> None:
        """Route 3: additions nested four levels deep under .aw/records are seen without pinning."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            deep_dir = (
                root / ".aw" / "records" / "research" / "assign1" / "docdir1" / "sub"
            )
            deep_dir.mkdir(parents=True)

            art_a = deep_dir / "20260901-set3-01-aaaaaa-research-a.md"
            art_a.write_text("# Research A\n- Id: aaaaaa\n- Status: draft\n")

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            art_b = deep_dir / "20260901-set3-02-bbbbbb-research-b.md"
            art_b.write_text("# Research B\n- Id: bbbbbb\n- Status: draft\n")

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

    def test_memoization_cache_reuses_index_and_invalidates_on_change(self) -> None:
        """Memoization test: unchanged tree reuses cached index; adding an artifact rebuilds it."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_a = pending_dir / "20260901-set1-01-aaaaaa-plan-a.ipd.md"
            art_a.write_text("# Plan A\n- Id: aaaaaa\n- Status: draft\n")

            traversal_count = 0
            orig_iter = _audit._sel._iter_paths

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _audit._sel._iter_paths = counted_iter
            try:
                # First lookup: builds and caches index
                lookup_1 = _audit.find_artifact(root, "aaaaaa")
                self.assertIsNotNone(lookup_1.path)
                c1 = traversal_count
                self.assertGreater(c1, 0)
                key = (str(root.resolve()), tuple(_audit.TYPE_PRECEDENCE))
                idx_1 = _audit._INDEX_CACHE[key][1]

                # Second lookup: cache hit, no new traversals, same ArtifactIndex object
                lookup_2 = _audit.find_artifact(root, "aaaaaa")
                self.assertIsNotNone(lookup_2.path)
                c2 = traversal_count
                self.assertEqual(c1, c2)
                idx_2 = _audit._INDEX_CACHE[key][1]
                self.assertIs(idx_1, idx_2)

                # Add artifact B: tree changes
                art_b = pending_dir / "20260901-set1-02-bbbbbb-plan-b.ipd.md"
                art_b.write_text("# Plan B\n- Id: bbbbbb\n- Status: draft\n")

                # Third lookup: cache invalidated, traversal runs, returned index differs
                lookup_3 = _audit.find_artifact(root, "bbbbbb")
                self.assertIsNotNone(lookup_3.path)
                c3 = traversal_count
                self.assertGreater(c3, c2)
                idx_3 = _audit._INDEX_CACHE[key][1]
                self.assertIsNot(idx_1, idx_3)
                self.assertIn(art_b, idx_3.paths)
                self.assertNotIn(art_b, idx_1.paths)
            finally:
                _audit._sel._iter_paths = orig_iter

    def test_compound_route2_untyped_tree_with_pinned_mtime(self) -> None:
        """Compound Route 2: untyped tree addition with pinned directory mtime succeeds."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prompts_dir = root / ".aw" / "records" / "prompt-library"
            prompts_dir.mkdir(parents=True)

            art_a = prompts_dir / "20260901-set2-01-aaaaaa-prompt-a.md"
            art_a.write_text("# Prompt A\n- Id: aaaaaa\n- Status: draft\n")

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = prompts_dir.stat()
            art_b = prompts_dir / "20260901-set2-02-bbbbbb-prompt-b.md"
            art_b.write_text("# Prompt B\n- Id: bbbbbb\n- Status: draft\n")
            os.utime(prompts_dir, ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns))

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

    def test_compound_route3_deep_directory_with_pinned_mtime(self) -> None:
        """Compound Route 3: deep directory addition with pinned directory mtime succeeds."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            deep_dir = (
                root / ".aw" / "records" / "research" / "assign1" / "docdir1" / "sub"
            )
            deep_dir.mkdir(parents=True)

            art_a = deep_dir / "20260901-set3-01-aaaaaa-research-a.md"
            art_a.write_text("# Research A\n- Id: aaaaaa\n- Status: draft\n")

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = deep_dir.stat()
            art_b = deep_dir / "20260901-set3-02-bbbbbb-research-b.md"
            art_b.write_text("# Research B\n- Id: bbbbbb\n- Status: draft\n")
            os.utime(deep_dir, ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns))

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

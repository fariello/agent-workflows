"""Outcome tests for artifact_audit index cache eviction policy (IPD bvw2nd).

Validates:
- Bounded cache size: cache size equals _INDEX_CACHE_MAX after exceeding cap (no wholesale drop).
- Hot-root retention: hot root is retained across interleaved fresh roots by LRU promotion on hit.
- No rebuild on hit: memoization reuses existing ArtifactIndex without re-traversal.
- Invalidation on change: tree modifications invalidate cache and produce a fresh ArtifactIndex.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit


class TestArtifactAuditCacheEviction(unittest.TestCase):
    """Test outcome-based properties of the artifact index cache eviction policy."""

    def setUp(self) -> None:
        _audit._INDEX_CACHE.clear()

    def tearDown(self) -> None:
        _audit._INDEX_CACHE.clear()

    def test_cache_size_is_bounded_at_cap(self) -> None:
        """Cache size equals _INDEX_CACHE_MAX after indexing > cap distinct roots."""
        cap = _audit._INDEX_CACHE_MAX
        num_roots = cap + 2
        tds: list[tempfile.TemporaryDirectory] = []
        try:
            for i in range(num_roots):
                td = tempfile.TemporaryDirectory()
                tds.append(td)
                root = Path(td.name)
                pending = root / ".aw" / "records" / "plans" / "pending"
                pending.mkdir(parents=True)
                plan = pending / f"20261001-set{i}-01-id{i:04d}-plan-{i}.ipd.md"
                plan.write_text(f"# Plan {i}\n- Id: id{i:04d}\n- Status: draft\n")
                _audit.build_index(root)

            self.assertEqual(len(_audit._INDEX_CACHE), cap)
        finally:
            for td in tds:
                td.cleanup()

    def test_hot_root_retained_across_interleaved_queries(self) -> None:
        """Hot root is retained by object identity when interleaved with fresh roots."""
        cap = _audit._INDEX_CACHE_MAX
        num_fresh = cap + 2
        tds: list[tempfile.TemporaryDirectory] = []
        try:
            hot_td = tempfile.TemporaryDirectory()
            tds.append(hot_td)
            hot_root = Path(hot_td.name)
            pending = hot_root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            hot_plan = pending / "20261001-hot-01-hot001-hot-plan.ipd.md"
            hot_plan.write_text("# Hot Plan\n- Id: hot001\n- Status: draft\n")

            initial_hot_index = _audit.build_index(hot_root)

            for i in range(num_fresh):
                fresh_td = tempfile.TemporaryDirectory()
                tds.append(fresh_td)
                fresh_root = Path(fresh_td.name)
                f_pending = fresh_root / ".aw" / "records" / "plans" / "pending"
                f_pending.mkdir(parents=True)
                f_plan = f_pending / f"20261001-fresh{i}-01-fr{i:04d}-plan.ipd.md"
                f_plan.write_text(
                    f"# Fresh Plan {i}\n- Id: fr{i:04d}\n- Status: draft\n"
                )
                _audit.build_index(fresh_root)

                re_queried_hot = _audit.build_index(hot_root)

            self.assertIs(re_queried_hot, initial_hot_index)
        finally:
            for td in tds:
                td.cleanup()

    def test_no_rebuild_on_cache_hit(self) -> None:
        """Cache hit reuses the same ArtifactIndex object with zero additional filesystem traversals."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan = pending / "20261001-set1-01-aaaaaa-plan.ipd.md"
            plan.write_text("# Plan A\n- Id: aaaaaa\n- Status: draft\n")

            traversal_count = 0
            orig_iter = _audit._sel._iter_paths

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _audit._sel._iter_paths = counted_iter
            try:
                idx1 = _audit.build_index(root)
                c1 = traversal_count
                self.assertGreater(c1, 0)

                idx2 = _audit.build_index(root)
                c2 = traversal_count
                self.assertEqual(c1, c2)
                self.assertIs(idx1, idx2)
            finally:
                _audit._sel._iter_paths = orig_iter

    def test_cache_invalidated_on_real_change(self) -> None:
        """Real change to root invalidates cache, producing a new ArtifactIndex containing new file."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending = root / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan_a = pending / "20261001-set1-01-aaaaaa-plan.ipd.md"
            plan_a.write_text("# Plan A\n- Id: aaaaaa\n- Status: draft\n")

            idx1 = _audit.build_index(root)
            self.assertIn(plan_a, idx1.paths)

            plan_b = pending / "20261001-set1-02-bbbbbb-plan.ipd.md"
            plan_b.write_text("# Plan B\n- Id: bbbbbb\n- Status: draft\n")

            idx2 = _audit.build_index(root)
            self.assertIsNot(idx1, idx2)
            self.assertIn(plan_b, idx2.paths)
            self.assertNotIn(plan_b, idx1.paths)

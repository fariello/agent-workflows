"""Tests for artifact_audit identity staleness verification (IPD 0a7v0x).

Validates that find_artifact's tier-one verification closes the three wrong
answers reachable from an in-place - Id: rewrite without widening the signature,
and preserves the cache's memoization and cost invariants:
- Outcome 1: Stale positive returns fresh truth (None)
- Outcome 2: Wrong path returns fresh truth (new owner)
- Outcome 3: Phantom collision returns fresh truth (clean single hit)
- Cost shape 1: Unchanged tree reuses cached ArtifactIndex without re-traversal
- Cost shape 2: True tier-one answer does not re-derive or re-traverse
- Explicit index: Caller's ArtifactIndex is preserved; revalidation reuses cache
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit
from agent_workflows import selectors as _sel


class TestArtifactAuditIdentityStaleness(unittest.TestCase):
    """Pin the three wrong answers and the two cost-shape invariants."""

    def setUp(self) -> None:
        _audit._INDEX_CACHE.clear()

    def tearDown(self) -> None:
        _audit._INDEX_CACHE.clear()

    def test_stale_positive_returns_fresh_truth(self) -> None:
        """Scenario 1: Stale positive returns the fresh truth (None)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            # Filename id6 (xxxxxx) deliberately differs from declared id6 (aaaaaa)
            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            # Prime the cache
            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(prime.path)

            # In-place rewrite of X's declared id
            art_x.write_text(
                "# Plan X\n- Id: cccccc\n- Status: draft\n", encoding="utf-8"
            )

            cached_ans = _audit.find_artifact(root, "aaaaaa")

            _audit._INDEX_CACHE.clear()
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(cached_ans.path, fresh_truth.path)
            self.assertEqual(cached_ans.collisions, fresh_truth.collisions)
            self.assertIsNone(cached_ans.path)

    def test_wrong_path_returns_fresh_truth(self) -> None:
        """Scenario 2: Wrong path returns the fresh truth (new owner)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            art_y = pending_dir / "20261001-set1-02-yyyyyy-plan-y.ipd.md"
            art_y.write_text(
                "# Plan Y\n- Id: bbbbbb\n- Status: draft\n", encoding="utf-8"
            )

            # Prime the cache
            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(prime.path)

            # In-place rewrites: X -> cccccc, Y -> aaaaaa (no files added, removed or renamed)
            art_x.write_text(
                "# Plan X\n- Id: cccccc\n- Status: draft\n", encoding="utf-8"
            )
            art_y.write_text(
                "# Plan Y\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            cached_ans = _audit.find_artifact(root, "aaaaaa")

            _audit._INDEX_CACHE.clear()
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(cached_ans.path, fresh_truth.path)
            self.assertEqual(cached_ans.collisions, fresh_truth.collisions)
            self.assertEqual(cached_ans.path.name, art_y.name)

    def test_phantom_collision_returns_fresh_truth(self) -> None:
        """Scenario 3: Phantom collision resolves cleanly to single true hit."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            art_y = pending_dir / "20261001-set1-02-yyyyyy-plan-y.ipd.md"
            art_y.write_text(
                "# Plan Y\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            # Prime the cache: genuine collision
            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNone(prime.path)
            self.assertEqual(len(prime.collisions), 2)

            # Fix collision in place: rewrite Y to bbbbbb
            art_y.write_text(
                "# Plan Y\n- Id: bbbbbb\n- Status: draft\n", encoding="utf-8"
            )

            cached_ans = _audit.find_artifact(root, "aaaaaa")

            _audit._INDEX_CACHE.clear()
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(cached_ans.path, fresh_truth.path)
            self.assertEqual(cached_ans.collisions, fresh_truth.collisions)
            self.assertEqual(cached_ans.path.name, art_x.name)
            self.assertEqual(cached_ans.collisions, [])

    def test_cost_shape_cache_is_reused_on_unchanged_tree(self) -> None:
        """Cost shape 1: Traversal runs once for unchanged tree; cached index is reused."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            orig_iter = _sel._iter_paths
            traversal_count = 0

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _sel._iter_paths = counted_iter
            try:
                idx_1 = _audit.build_index(root)
                ans_1 = _audit.find_artifact(root, "aaaaaa")
                self.assertIsNotNone(ans_1.path)
                c1 = traversal_count
                self.assertGreater(c1, 0)

                ans_2 = _audit.find_artifact(root, "aaaaaa")
                self.assertEqual(ans_1.path, ans_2.path)
                c2 = traversal_count
                self.assertEqual(c1, c2)

                idx_2 = _audit.build_index(root)
                self.assertIs(idx_1, idx_2)
            finally:
                _sel._iter_paths = orig_iter

    def test_cost_shape_true_tier_one_answer_does_not_rederive(self) -> None:
        """Cost shape 2: Verification of a true tier-one answer does not re-derive."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            # Prime the cache
            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(prime.path)

            orig_iter = _sel._iter_paths
            traversal_count = 0

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _sel._iter_paths = counted_iter
            try:
                second_ans = _audit.find_artifact(root, "aaaaaa")
                self.assertEqual(traversal_count, 0)
                self.assertEqual(prime.path, second_ans.path)
            finally:
                _sel._iter_paths = orig_iter

    def test_explicit_artifact_index_preserves_caller_object_and_revalidates_without_extra_traversal(
        self,
    ) -> None:
        """Explicit index: caller object is untouched; repeat lookups reuse rebuilt cache."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                "# Plan X\n- Id: aaaaaa\n- Status: draft\n", encoding="utf-8"
            )

            caller_idx = _audit.build_index(root)
            id_before = id(caller_idx)
            orig_mapping = dict(caller_idx.by_declared_id)

            # Rewrite X in place
            art_x.write_text(
                "# Plan X\n- Id: cccccc\n- Status: draft\n", encoding="utf-8"
            )

            orig_iter = _sel._iter_paths
            traversal_count = 0

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _sel._iter_paths = counted_iter
            try:
                # First lookup against stale caller index
                ans1 = _audit.find_artifact(root, "aaaaaa", artifact_index=caller_idx)
                c1 = traversal_count

                # (b) Caller's object is unchanged
                self.assertEqual(id(caller_idx), id_before)
                self.assertEqual(caller_idx.by_declared_id, orig_mapping)
                self.assertIn("aaaaaa", caller_idx.by_declared_id)

                # (c) Second identical call against same stale caller index does not re-traverse
                ans2 = _audit.find_artifact(root, "aaaaaa", artifact_index=caller_idx)
                c2 = traversal_count
                self.assertEqual(c1, c2)

                # (a) Answer equals freshly built index's answer
                _audit._INDEX_CACHE.clear()
                truth = _audit.find_artifact(root, "aaaaaa")
                self.assertEqual(ans1.path, truth.path)
                self.assertEqual(ans1.collisions, truth.collisions)
                self.assertEqual(ans2.path, truth.path)
            finally:
                _sel._iter_paths = orig_iter


if __name__ == "__main__":
    unittest.main()

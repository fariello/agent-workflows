"""Tests for artifact_audit identity freshness (IPD 0a7v0x; retargeted by IPD h3jp4e).

`artifact_audit.build_index` holds no in-process cache (spec 4sd62s 4.5), so an in-place `- Id:`
rewrite between two lookups is reflected by the second. A caller-held `ArtifactIndex` can still be
stale, and `find_artifact`'s tier-one verification closes the wrong answers that reach it:
- Outcome 1: Stale positive returns fresh truth (None)
- Outcome 2: Wrong path returns fresh truth (new owner)
- Outcome 3: Phantom collision returns fresh truth (clean single hit)
- Unchanged tree: repeated build_index calls return equal indexes and answers
- True tier-one answer from a supplied index does not re-derive or re-traverse
- Explicit stale index: caller's ArtifactIndex is preserved; every lookup answers fresh truth
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit
from agent_workflows import selectors as _sel
from tests.record_builder import RecordBuilder


class TestArtifactAuditIdentityStaleness(unittest.TestCase):
    """Pin the three wrong answers and the freshness invariants."""

    def test_stale_positive_returns_fresh_truth(self) -> None:
        """Scenario 1: Stale positive returns the fresh truth (None)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            # Filename id6 (xxxxxx) deliberately differs from declared id6 (aaaaaa)
            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(prime.path)
            stale_idx = _audit.build_index(root)

            # In-place rewrite of X's declared id
            art_x.write_text(
                RecordBuilder().plan(id6="cccccc", status="draft", text_only=True),
                encoding="utf-8",
            )

            stale_ans = _audit.find_artifact(root, "aaaaaa", artifact_index=stale_idx)
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(stale_ans.path, fresh_truth.path)
            self.assertEqual(stale_ans.collisions, fresh_truth.collisions)
            self.assertIsNone(fresh_truth.path)
            self.assertEqual(_audit.find_artifact(root, "cccccc").path.name, art_x.name)

    def test_wrong_path_returns_fresh_truth(self) -> None:
        """Scenario 2: Wrong path returns the fresh truth (new owner)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            art_y = pending_dir / "20261001-set1-02-yyyyyy-plan-y.ipd.md"
            art_y.write_text(
                RecordBuilder().plan(id6="bbbbbb", status="draft", text_only=True),
                encoding="utf-8",
            )

            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(prime.path)
            stale_idx = _audit.build_index(root)

            # In-place rewrites: X -> cccccc, Y -> aaaaaa (no files added, removed or renamed)
            art_x.write_text(
                RecordBuilder().plan(id6="cccccc", status="draft", text_only=True),
                encoding="utf-8",
            )
            art_y.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            stale_ans = _audit.find_artifact(root, "aaaaaa", artifact_index=stale_idx)
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(stale_ans.path, fresh_truth.path)
            self.assertEqual(stale_ans.collisions, fresh_truth.collisions)
            self.assertEqual(fresh_truth.path.name, art_y.name)

    def test_phantom_collision_returns_fresh_truth(self) -> None:
        """Scenario 3: Phantom collision resolves cleanly to single true hit."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            art_y = pending_dir / "20261001-set1-02-yyyyyy-plan-y.ipd.md"
            art_y.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            # Genuine collision first
            prime = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNone(prime.path)
            self.assertEqual(len(prime.collisions), 2)
            stale_idx = _audit.build_index(root)

            # Fix collision in place: rewrite Y to bbbbbb
            art_y.write_text(
                RecordBuilder().plan(id6="bbbbbb", status="draft", text_only=True),
                encoding="utf-8",
            )

            stale_ans = _audit.find_artifact(root, "aaaaaa", artifact_index=stale_idx)
            fresh_truth = _audit.find_artifact(root, "aaaaaa")

            self.assertEqual(stale_ans.path, fresh_truth.path)
            self.assertEqual(stale_ans.collisions, fresh_truth.collisions)
            self.assertEqual(fresh_truth.path.name, art_x.name)
            self.assertEqual(fresh_truth.collisions, [])

    def test_unchanged_tree_repeated_build_index_is_equal(self) -> None:
        """Unchanged tree: every call enumerates afresh and returns an equal index and answer."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
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
                self.assertGreater(traversal_count, c1)

                idx_2 = _audit.build_index(root)
                self.assertEqual(idx_1.paths, idx_2.paths)
                self.assertEqual(idx_1.by_declared_id, idx_2.by_declared_id)
                self.assertEqual(idx_1.by_filename_id, idx_2.by_filename_id)
            finally:
                _sel._iter_paths = orig_iter

    def test_cost_shape_true_tier_one_answer_does_not_rederive(self) -> None:
        """Verification of a true tier-one answer from a supplied index does not re-derive."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            idx = _audit.build_index(root)
            prime = _audit.find_artifact(root, "aaaaaa", artifact_index=idx)
            self.assertIsNotNone(prime.path)

            orig_iter = _sel._iter_paths
            traversal_count = 0

            def counted_iter(*args, **kwargs):
                nonlocal traversal_count
                traversal_count += 1
                return orig_iter(*args, **kwargs)

            _sel._iter_paths = counted_iter
            try:
                second_ans = _audit.find_artifact(root, "aaaaaa", artifact_index=idx)
                self.assertEqual(traversal_count, 0)
                self.assertEqual(prime.path, second_ans.path)
            finally:
                _sel._iter_paths = orig_iter

    def test_explicit_stale_artifact_index_preserves_caller_object_and_answers_fresh_truth(
        self,
    ) -> None:
        """Explicit stale index: caller object is untouched; every lookup answers fresh truth."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_x = pending_dir / "20261001-set1-01-xxxxxx-plan-x.ipd.md"
            art_x.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True),
                encoding="utf-8",
            )

            caller_idx = _audit.build_index(root)
            id_before = id(caller_idx)
            orig_mapping = dict(caller_idx.by_declared_id)

            # Rewrite X in place
            art_x.write_text(
                RecordBuilder().plan(id6="cccccc", status="draft", text_only=True),
                encoding="utf-8",
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

                # (c) Each call against the stale caller index re-derives from disk
                self.assertGreater(c1, 0)
                ans2 = _audit.find_artifact(root, "aaaaaa", artifact_index=caller_idx)
                self.assertGreater(traversal_count, c1)
                self.assertEqual(caller_idx.by_declared_id, orig_mapping)

                # (a) Answer equals freshly built index's answer
                truth = _audit.find_artifact(root, "aaaaaa")
                self.assertEqual(ans1.path, truth.path)
                self.assertEqual(ans1.collisions, truth.collisions)
                self.assertEqual(ans2.path, truth.path)
            finally:
                _sel._iter_paths = orig_iter


if __name__ == "__main__":
    unittest.main()

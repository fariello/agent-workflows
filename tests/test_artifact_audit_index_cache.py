"""Tests for artifact_audit index freshness (IPD dea7dr; retargeted by IPD h3jp4e).

`artifact_audit.build_index` holds no in-process cache (spec 4sd62s 4.5), so a change made between
two calls must be reflected by the second, across every route that once defeated the old cache:
- Route 1: same-tick addition with pinned directory mtime
- Route 2: addition in untyped record trees (e.g. .aw/records/prompt-library/)
- Route 3: addition four levels deep under .aw/records/
- Route 2 compound: untyped tree addition with pinned directory mtime
- Route 3 compound: deep directory addition with pinned directory mtime
- Add, delete and move: a record added, deleted or moved between two build_index calls is
  reflected by the second.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_audit as _audit
from tests.record_builder import RecordBuilder


class TestArtifactAuditIndexCache(unittest.TestCase):
    """A change between two lookups is reflected by the second lookup."""

    def test_route1_same_tick_addition_detected(self) -> None:
        """Route 1: same-tick additions in pending/ are seen even if directory mtime does not advance."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            art_a = pending_dir / "20260901-set1-01-aaaaaa-plan-a.ipd.md"
            art_a.write_text(
                RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True)
            )

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = pending_dir.stat()
            art_b = pending_dir / "20260901-set1-02-bbbbbb-plan-b.ipd.md"
            art_b.write_text(
                RecordBuilder().plan(id6="bbbbbb", status="draft", text_only=True)
            )
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
            art_a.write_text(
                RecordBuilder().plan(
                    title="Prompt A",
                    id6="aaaaaa",
                    status="draft",
                    set="set2",
                    order=1,
                    when="2026-09-01",
                    text_only=True,
                )
            )

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            art_b = prompts_dir / "20260901-set2-02-bbbbbb-prompt-b.md"
            art_b.write_text(
                RecordBuilder().plan(
                    title="Prompt B",
                    id6="bbbbbb",
                    status="draft",
                    set="set2",
                    order=2,
                    when="2026-09-01",
                    text_only=True,
                )
            )

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
            art_a.write_text(
                RecordBuilder().research(
                    id6="aaaaaa", raw_fields={"Status": "draft"}, text_only=True
                )
            )

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            art_b = deep_dir / "20260901-set3-02-bbbbbb-research-b.md"
            art_b.write_text(
                RecordBuilder().research(
                    id6="bbbbbb", raw_fields={"Status": "draft"}, text_only=True
                )
            )

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

    def _pending_with_plan_a(self, root: Path) -> tuple[Path, Path]:
        pending_dir = root / ".aw" / "records" / "plans" / "pending"
        pending_dir.mkdir(parents=True)
        art_a = pending_dir / "20260901-set1-01-aaaaaa-plan-a.ipd.md"
        art_a.write_text(
            RecordBuilder().plan(id6="aaaaaa", status="draft", text_only=True)
        )
        return pending_dir, art_a

    def test_second_build_index_reflects_addition(self) -> None:
        """A record added between two build_index calls appears in the second index."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir, art_a = self._pending_with_plan_a(root)

            idx_1 = _audit.build_index(root)
            self.assertIn(art_a, idx_1.paths)

            # Unchanged tree: a repeat call answers the same, rebuilt rather than cached.
            idx_repeat = _audit.build_index(root)
            self.assertEqual(idx_repeat.paths, idx_1.paths)
            self.assertEqual(idx_repeat.by_declared_id, idx_1.by_declared_id)
            self.assertEqual(_audit.find_artifact(root, "aaaaaa").path, art_a)

            art_b = pending_dir / "20260901-set1-02-bbbbbb-plan-b.ipd.md"
            art_b.write_text(
                RecordBuilder().plan(id6="bbbbbb", status="draft", text_only=True)
            )

            idx_2 = _audit.build_index(root)
            self.assertIn(art_b, idx_2.paths)
            self.assertEqual(idx_2.by_declared_id.get("bbbbbb"), [art_b])
            self.assertNotIn(art_b, idx_1.paths)
            self.assertEqual(_audit.find_artifact(root, "bbbbbb").path, art_b)

    def test_second_build_index_reflects_deletion(self) -> None:
        """A record deleted between two build_index calls is absent from the second index."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir, art_a = self._pending_with_plan_a(root)
            art_b = pending_dir / "20260901-set1-02-bbbbbb-plan-b.ipd.md"
            art_b.write_text(
                RecordBuilder().plan(id6="bbbbbb", status="draft", text_only=True)
            )

            idx_1 = _audit.build_index(root)
            self.assertIn(art_b, idx_1.paths)
            self.assertEqual(_audit.find_artifact(root, "bbbbbb").path, art_b)

            art_b.unlink()

            idx_2 = _audit.build_index(root)
            self.assertNotIn(art_b, idx_2.paths)
            self.assertNotIn("bbbbbb", idx_2.by_declared_id)
            self.assertNotIn("bbbbbb", idx_2.by_filename_id)
            self.assertIn(art_a, idx_2.paths)
            lookup = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNone(lookup.path)
            self.assertEqual(lookup.collisions, [])

    def test_second_build_index_reflects_move(self) -> None:
        """A record moved between two build_index calls is found at its new path only."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _pending_dir, art_a = self._pending_with_plan_a(root)
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            executed_dir.mkdir(parents=True)

            idx_1 = _audit.build_index(root)
            self.assertEqual(idx_1.by_declared_id.get("aaaaaa"), [art_a])
            self.assertEqual(_audit.find_artifact(root, "aaaaaa").path, art_a)

            moved = executed_dir / art_a.name
            art_a.rename(moved)

            idx_2 = _audit.build_index(root)
            self.assertNotIn(art_a, idx_2.paths)
            self.assertIn(moved, idx_2.paths)
            self.assertEqual(idx_2.by_declared_id.get("aaaaaa"), [moved])
            self.assertEqual(idx_2.by_filename_id.get("aaaaaa"), [moved])
            self.assertEqual(_audit.find_artifact(root, "aaaaaa").path, moved)

    def test_compound_route2_untyped_tree_with_pinned_mtime(self) -> None:
        """Compound Route 2: untyped tree addition with pinned directory mtime succeeds."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prompts_dir = root / ".aw" / "records" / "prompt-library"
            prompts_dir.mkdir(parents=True)

            art_a = prompts_dir / "20260901-set2-01-aaaaaa-prompt-a.md"
            art_a.write_text(
                RecordBuilder().plan(
                    title="Prompt A",
                    id6="aaaaaa",
                    status="draft",
                    set="set2",
                    order=1,
                    when="2026-09-01",
                    text_only=True,
                )
            )

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = prompts_dir.stat()
            art_b = prompts_dir / "20260901-set2-02-bbbbbb-prompt-b.md"
            art_b.write_text(
                RecordBuilder().plan(
                    title="Prompt B",
                    id6="bbbbbb",
                    status="draft",
                    set="set2",
                    order=2,
                    when="2026-09-01",
                    text_only=True,
                )
            )
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
            art_a.write_text(
                RecordBuilder().research(
                    id6="aaaaaa", raw_fields={"Status": "draft"}, text_only=True
                )
            )

            lookup_a = _audit.find_artifact(root, "aaaaaa")
            self.assertIsNotNone(lookup_a.path)

            stat_before = deep_dir.stat()
            art_b = deep_dir / "20260901-set3-02-bbbbbb-research-b.md"
            art_b.write_text(
                RecordBuilder().research(
                    id6="bbbbbb", raw_fields={"Status": "draft"}, text_only=True
                )
            )
            os.utime(deep_dir, ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns))

            lookup_b = _audit.find_artifact(root, "bbbbbb")
            self.assertIsNotNone(lookup_b.path)
            self.assertEqual(lookup_b.path.name, art_b.name)

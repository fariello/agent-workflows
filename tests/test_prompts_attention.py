"""Tests for prompts as an attention adopter (Plan dx0u4s).

Stdlib unittest, zero external deps. Verifies:
- attention_contract mappings for prompts (pure, total over prompt dispositions)
- prompts in TRACKED_TREES and excluded trees (docs-prompts excluded)
- attention scanner behavior across prompt buckets, missing-status handling,
  empty-id handling (common case matching live corpus), untracked exclusion,
  and README exclusion.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention as att
from agent_workflows import attention_contract as A


class PromptsContractTests(unittest.TestCase):
    def test_tracked_trees_contains_prompts(self):
        self.assertIn("prompts", A.TRACKED_TREES)

    def test_docs_prompts_is_excluded(self):
        docs_prompts_policy = next(
            (p for p in A.TREE_POLICY if p.name == "docs-prompts"), None
        )
        self.assertIsNotNone(docs_prompts_policy)
        self.assertFalse(docs_prompts_policy.tracked)

    def test_class_of_total_over_dispositions(self):
        expected = {
            "pending": A.READY,
            "executed": A.DONE,
            "superseded": A.PARKED,
            "not-executed": A.PARKED,
            "reusable": A.PARKED,
        }
        for disp, expected_cls in expected.items():
            self.assertEqual(
                A.class_of("prompts", disp),
                expected_cls,
                f"disposition {disp!r} should map to {expected_cls!r}",
            )

    def test_class_of_unknown_disposition_raises(self):
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("prompts", "unknown-disposition")


class PromptsScanTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.prompts_dir = self.root / ".aw" / "records" / "prompts"

        # Create bucket directories
        for bucket in (
            "pending",
            "executed",
            "superseded",
            "not-executed",
            "reusable",
            "untracked",
        ):
            (self.prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

        # 1. Prompt WITH an Id: in aw-prompt comment
        (
            self.prompts_dir / "pending" / "20260920-set-01-abc123-with-id.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: research | Id: abc123 | Set: set | Order: 01 | Status: pending | Slug: with-id -->\n\nBody.\n",
            encoding="utf-8",
        )

        # 2. Prompt with aw-prompt comment but WITHOUT Id:
        (
            self.prompts_dir / "pending" / "20260810-1544-01-comment-no-id.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: run-once | Set: test | Order: 01 | Status: pending | Slug: comment-no-id -->\n\nBody.\n",
            encoding="utf-8",
        )

        # 3. Prompt with NO comment at all
        (
            self.prompts_dir / "executed" / "20260722-2317-01-no-comment.prompt.md"
        ).write_text(
            "# Legacy prompt without comment\n\nBody.\n",
            encoding="utf-8",
        )

        # 4. Other buckets
        (
            self.prompts_dir / "superseded" / "20260717-1950-01-superseded.prompt.md"
        ).write_text(
            "# Superseded\n\nBody.\n",
            encoding="utf-8",
        )
        (
            self.prompts_dir
            / "not-executed"
            / "20260717-1950-02-not-executed.prompt.md"
        ).write_text(
            "# Not executed\n\nBody.\n",
            encoding="utf-8",
        )
        (
            self.prompts_dir / "reusable" / "20260717-1950-03-reusable.prompt.md"
        ).write_text(
            "# Reusable\n\nBody.\n",
            encoding="utf-8",
        )

        # 5. Untracked file
        (self.prompts_dir / "untracked" / "20260920-untracked.prompt.md").write_text(
            "# Untracked\n\nBody.\n",
            encoding="utf-8",
        )

        # 6. README in bucket
        (self.prompts_dir / "pending" / "README.md").write_text(
            "# Pending Prompts\n",
            encoding="utf-8",
        )

        # 7. Unbucketed prompt (directly under .aw/records/prompts/)
        (self.prompts_dir / "20260920-no-bucket.prompt.md").write_text(
            "# No bucket\n\nBody.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_prompts(self):
        items, drift = att.scan(self.root)

        # Unbucketed prompt should yield attention.missing-status
        missing_status_drifts = [
            d for d in drift if d.rule == "attention.missing-status"
        ]
        self.assertTrue(
            any(
                "20260920-no-bucket.prompt.md" in d.location
                for d in missing_status_drifts
            ),
            f"Expected missing-status for unbucketed prompt, got: {drift}",
        )

        prompt_items = [it for it in items if it.tree == "prompts"]

        # 6 bucketed prompts (2 pending, 1 executed, 1 superseded, 1 not-executed, 1 reusable)
        self.assertEqual(len(prompt_items), 6)

        # Untracked prompt should be ABSENT
        self.assertFalse(
            any("untracked" in it.path for it in prompt_items),
            "untracked prompt should not be scanned as an item",
        )

        # README should produce NO item
        self.assertFalse(
            any("README.md" in it.path for it in prompt_items),
            "README.md should not produce an attention item",
        )

        # Check item classes
        by_name = {Path(it.path).name: it for it in prompt_items}
        self.assertEqual(
            by_name["20260920-set-01-abc123-with-id.prompt.md"].attention_class, A.READY
        )
        self.assertEqual(
            by_name["20260810-1544-01-comment-no-id.prompt.md"].attention_class, A.READY
        )
        self.assertEqual(
            by_name["20260722-2317-01-no-comment.prompt.md"].attention_class, A.DONE
        )
        self.assertEqual(
            by_name["20260717-1950-01-superseded.prompt.md"].attention_class, A.PARKED
        )
        self.assertEqual(
            by_name["20260717-1950-02-not-executed.prompt.md"].attention_class, A.PARKED
        )
        self.assertEqual(
            by_name["20260717-1950-03-reusable.prompt.md"].attention_class, A.PARKED
        )

        # Check ID distribution: exactly 1 has Id 'abc123', others have empty string ''
        self.assertEqual(
            by_name["20260920-set-01-abc123-with-id.prompt.md"].id, "abc123"
        )
        self.assertEqual(by_name["20260810-1544-01-comment-no-id.prompt.md"].id, "")
        self.assertEqual(by_name["20260722-2317-01-no-comment.prompt.md"].id, "")
        self.assertEqual(by_name["20260717-1950-01-superseded.prompt.md"].id, "")


if __name__ == "__main__":
    unittest.main()

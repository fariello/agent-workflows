"""Tests for prompts manifest index generation and drift checking (Plan dx0u4s).

Stdlib unittest, zero external deps. Verifies:
- scan_prompts lists every bucketed prompt with id6, set, order, disposition, kind
- check_drift reports no finding for an absent or out-of-date INDEX file (plan w819as)
- check_drift reports name-metadata-mismatch when filename id6 != comment Id
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import prompts_index


class _PromptsFixtureBase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.prompts_dir = self.root / ".aw" / "records" / "prompts"

        for bucket in ("pending", "executed", "superseded", "untracked"):
            (self.prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

        # 1. Clustered prompt with metadata comment
        (
            self.prompts_dir / "pending" / "20260920-seta-01-abc123-slug-one.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: research | Id: abc123 | Set: seta | Order: 01 | Status: pending | Slug: slug-one -->\n\nPrompt one.\n",
            encoding="utf-8",
        )

        # 2. Legacy prompt with metadata comment (no Id:)
        (
            self.prompts_dir / "executed" / "20260810-1544-01-legacy-prompt.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-10 -->\n\nPrompt two.\n",
            encoding="utf-8",
        )

        # 3. Legacy prompt with no comment
        (
            self.prompts_dir / "superseded" / "20260717-1950-01-no-comment.prompt.md"
        ).write_text(
            "# Legacy prompt\n\nBody.\n",
            encoding="utf-8",
        )

        # 4. Untracked file (should be ignored)
        (self.prompts_dir / "untracked" / "20260920-untracked.prompt.md").write_text(
            "# Untracked\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()


class PromptsIndexTests(_PromptsFixtureBase):
    def test_scan_and_build_index_json(self):
        entries, drift = prompts_index.scan_prompts(self.prompts_dir)
        self.assertEqual(drift, [])
        self.assertEqual(len(entries), 3)

        by_path = {e.path: e for e in entries}
        p1 = by_path["pending/20260920-seta-01-abc123-slug-one.prompt.md"]
        self.assertEqual(p1.id6, "abc123")
        self.assertEqual(p1.set_id, "seta")
        self.assertEqual(p1.order, 1)
        self.assertEqual(p1.disposition, "pending")
        self.assertEqual(p1.kind, "research")

        p2 = by_path["executed/20260810-1544-01-legacy-prompt.prompt.md"]
        self.assertEqual(p2.disposition, "executed")
        self.assertEqual(p2.kind, "run-once")

        p3 = by_path["superseded/20260717-1950-01-no-comment.prompt.md"]
        self.assertEqual(p3.disposition, "superseded")

    def test_check_drift_missing_index_is_not_drift(self):
        # Plan w819as (spec 4sd62s 4.5): absent INDEX files are not drift.
        drift = prompts_index.check_drift(self.root, self.prompts_dir)
        self.assertEqual(drift, [])
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_check_drift_stale_index_is_not_drift(self):
        # Plan w819as deleted the stale-INDEX rule: a leftover INDEX file, current or not, is no finding.
        (self.prompts_dir / "INDEX.json").write_text("[]\n", encoding="utf-8")
        (self.prompts_dir / "INDEX.md").write_text("# stale\n", encoding="utf-8")
        drift_stale = prompts_index.check_drift(self.root, self.prompts_dir)
        self.assertEqual(drift_stale, [])

    def test_check_drift_name_metadata_mismatch(self):
        # Create a prompt where filename id6 != comment Id
        (
            self.prompts_dir / "pending" / "20260920-setb-01-xyz789-mismatch.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: research | Id: dif123 | Set: setb | Order: 01 | Status: pending | Slug: mismatch -->\n\nPrompt.\n",
            encoding="utf-8",
        )
        drift = prompts_index.check_drift(self.root, self.prompts_dir)
        mismatch_drifts = [d for d in drift if d.rule == "name-metadata-mismatch"]
        self.assertTrue(len(mismatch_drifts) >= 1)
        self.assertTrue(any("xyz789" in d.detail for d in mismatch_drifts))


class PromptsContentValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.prompts_dir = self.root / ".aw" / "records" / "prompts"
        for bucket in ("pending", "executed", "superseded", "not-executed", "reusable"):
            (self.prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rule_prompt_metadata_missing_post_cutover(self):
        from agent_workflows import check_engine as ce

        # Post-cutover dated prompt without comment -> MUST report check.prompt-metadata-missing
        p_post = (
            self.prompts_dir
            / "pending"
            / "20260925-seta-01-abc123-new-prompt.prompt.md"
        )
        p_post.write_text("# Body only\n", encoding="utf-8")
        drift = ce.validate_prompt_content(p_post, repo_root=self.root)
        rules = [d.rule for d in drift]
        self.assertIn("check.prompt-metadata-missing", rules)

        # Pre-cutover dated prompt without comment -> Grandfathered, no error
        p_pre = self.prompts_dir / "pending" / "20260810-0100-01-old-prompt.prompt.md"
        p_pre.write_text("# Body only\n", encoding="utf-8")
        drift_pre = ce.validate_prompt_content(p_pre, repo_root=self.root)
        self.assertEqual(drift_pre, [])

    def test_rule_prompt_id_mismatch(self):
        from agent_workflows import check_engine as ce

        # Clustered prompt filename with abc123, comment with dif999
        p = (
            self.prompts_dir
            / "pending"
            / "20260920-seta-01-abc123-test-mismatch.prompt.md"
        )
        p.write_text(
            "<!-- aw-prompt: Kind: research | Id: dif999 | Set: seta | Order: 01 | Status: pending | Slug: test-mismatch -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift = ce.validate_prompt_content(p, repo_root=self.root)
        rules = [d.rule for d in drift]
        self.assertIn("check.prompt-id-mismatch", rules)

        # Matching id
        p_ok = (
            self.prompts_dir / "pending" / "20260920-seta-01-abc123-test-ok.prompt.md"
        )
        p_ok.write_text(
            "<!-- aw-prompt: Kind: research | Id: abc123 | Set: seta | Order: 01 | Status: pending | Slug: test-ok -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift_ok = ce.validate_prompt_content(p_ok, repo_root=self.root)
        self.assertEqual(drift_ok, [])

    def test_rule_prompt_status_mismatch(self):
        from agent_workflows import check_engine as ce

        # Prompt in executed/ with comment Status: pending
        p1 = self.prompts_dir / "executed" / "20260808-1948-01-spec-review.prompt.md"
        p1.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: pending | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift1 = ce.validate_prompt_content(p1, repo_root=self.root)
        rules1 = [d.rule for d in drift1]
        self.assertIn("check.prompt-status-mismatch", rules1)

        # Prompt in pending/ with comment Status: executed
        p2 = self.prompts_dir / "pending" / "20260808-1948-01-spec-review.prompt.md"
        p2.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift2 = ce.validate_prompt_content(p2, repo_root=self.root)
        rules2 = [d.rule for d in drift2]
        self.assertIn("check.prompt-status-mismatch", rules2)

        # Prompt in executed/ with comment Status: executed -> Clean
        p3 = self.prompts_dir / "executed" / "20260808-1948-01-spec-review.prompt.md"
        p3.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift3 = ce.validate_prompt_content(p3, repo_root=self.root)
        self.assertEqual(drift3, [])


if __name__ == "__main__":
    unittest.main()

"""Tests for the aw prompts set CLI surface, vocabulary bounding, and comment status writer.

Plan 7z3ovv (E-05, V-05).
Pins:
- Parser registration under `prompts` family so `aw prompts set` is reachable.
- Narrowed 5-bucket + done vocabulary with exact refusal message on non-bucket statuses.
- Comment status writer preserving body byte-identity without prepending a `- Status:` bullet.
- Commentless prompt relocation without minting a comment (refusal-to-mint posture).
- Dry-run byte-identity.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import check_engine, cli, prompts


class TestPromptsSetSurface(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_prompts_set_")
        self.repo_root = Path(self.temp_dir)
        # Create standard layout
        (self.repo_root / ".aw" / "records" / "prompts" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "prompts" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "prompts" / "superseded").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_conforming_prompt(
        self,
        id6: str,
        set_id: str = "testset",
        slug: str = "test-prompt",
        disposition: str = "pending",
        status: str = "pending",
        body: str = "",
    ) -> Path:
        """Create a conforming prompt artifact matching `aw prompts new` output."""
        filename = f"20261002-{set_id}-01-{id6}-{slug}.prompt.md"
        p = self.repo_root / ".aw" / "records" / "prompts" / disposition / filename
        comment = prompts.render_metadata_comment(
            kind="research",
            status=status,
            created="2026-10-02",
            id6=id6,
            set_id=set_id,
        )
        content = comment + ("\n\n" + body if body else "\n")
        p.write_text(content, encoding="utf-8")
        return p

    def create_commentless_prompt(
        self,
        id6: str,
        set_id: str = "testset",
        slug: str = "legacy-prompt",
        disposition: str = "pending",
        body: str = "# Legacy Prompt\n\nSome body content.\n",
    ) -> Path:
        """Create a prompt artifact without a metadata comment (legacy/grandfathered shape)."""
        filename = f"20261002-{set_id}-01-{id6}-{slug}.prompt.md"
        p = self.repo_root / ".aw" / "records" / "prompts" / disposition / filename
        p.write_text(body, encoding="utf-8")
        return p

    def test_registration_cli_help(self):
        """aw prompts set --help exits 0 and lists all declared flags."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            try:
                rc = cli.main(["prompts", "set", "--help"])
            except SystemExit as e:
                rc = e.code
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("--dir", out)
        self.assertIn("--yes", out)
        self.assertIn("--message", out)
        self.assertIn("--by-human", out)
        self.assertIn("--dry-run", out)
        self.assertIn("--commit", out)
        self.assertIn("--no-commit", out)

    def test_registration_unknown_flag_exits_2(self):
        """aw prompts set with unrecognized flag exits 2 (usage error)."""
        buf = io.StringIO()
        with patch("sys.stderr", buf):
            try:
                rc = cli.main(["prompts", "set", "--unknown-bogus-flag"])
            except SystemExit as e:
                rc = e.code
        self.assertEqual(rc, 2)

    def test_vocabulary_refusal_with_enumerated_message(self):
        """Narrowed vocabulary refuses 'draft' and enumerates the 5 buckets plus done."""
        self.create_conforming_prompt("vc0001", set_id="vocset")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "prompts",
                    "set",
                    "draft",
                    "vc0001",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertNotEqual(rc, 0)
        out = buf.getvalue()
        expected = "Status 'draft' is not valid for prompts (valid: ['done', 'executed', 'not-executed', 'pending', 'reusable', 'superseded'])"
        self.assertIn(expected, out)

    def test_comment_write_with_body_byte_identity(self):
        """Status is written into metadata comment; body is byte-identical; no - Status: bullet."""
        body = (
            "# Prompt: Token Compression Research\n\n"
            "This prompt evaluates multi-stage context compression.\n\n"
            "## Methodology\n\n"
            "1. Run stage A\n"
            "2. Compare with baseline\n"
        )
        prompt = self.create_conforming_prompt("bw0001", set_id="bodyset", body=body)
        body_stripped = body.strip()
        body_sha_before = hashlib.sha256(body_stripped.encode("utf-8")).hexdigest()

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "prompts",
                    "set",
                    "executed",
                    "bw0001",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)

        # Re-resolve path in executed/
        dest_path = (
            self.repo_root / ".aw" / "records" / "prompts" / "executed" / prompt.name
        )
        self.assertTrue(dest_path.exists(), f"Destination not found: {dest_path}")
        self.assertFalse(prompt.exists(), f"Source still exists: {prompt}")

        dest_text = dest_path.read_text(encoding="utf-8")
        lines = dest_text.splitlines()

        # Line 1 is still the metadata comment with updated status
        self.assertTrue(lines[0].startswith("<!-- aw-prompt:"))
        self.assertIn("Status: executed", lines[0])

        # No - Status: bullet anywhere in the file
        self.assertNotIn("- Status:", dest_text)

        # Extract body between line 1 and ## Workflow history
        hist_idx = dest_text.find("## Workflow history")
        self.assertNotEqual(hist_idx, -1)
        # Content between comment and workflow history
        body_region = dest_text[len(lines[0]) : hist_idx].strip()
        self.assertEqual(body_region, body_stripped)
        body_sha_after = hashlib.sha256(body_region.encode("utf-8")).hexdigest()
        self.assertEqual(body_sha_before, body_sha_after)

        # Verify checker reports zero errors and zero warnings
        findings = check_engine.validate_prompt_content(dest_path)
        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warn"]
        self.assertEqual(len(errors), 0, f"Checker errors: {errors}")
        self.assertEqual(len(warnings), 0, f"Checker warnings: {warnings}")

    def test_commentless_prompt_fallback_relocates_without_comment(self):
        """Commentless prompt relocates, gains no comment, leaves body untouched (OQ-02)."""
        prompt = self.create_commentless_prompt("cl0001", set_id="comset")
        original_text = prompt.read_text(encoding="utf-8")

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "prompts",
                    "set",
                    "executed",
                    "cl0001",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("has no metadata comment; status lives in directory only", out)

        # Re-resolve path in executed/
        dest_path = (
            self.repo_root / ".aw" / "records" / "prompts" / "executed" / prompt.name
        )
        self.assertTrue(dest_path.exists())
        self.assertFalse(prompt.exists())

        dest_text = dest_path.read_text(encoding="utf-8")
        self.assertFalse(prompts.has_metadata_comment(dest_text))
        self.assertNotIn("- Status:", dest_text)
        # Check original body is preserved in dest
        self.assertEqual(dest_text, original_text)

    def test_dry_run_byte_identity(self):
        """Dry-run previews and leaves file byte-identical without relocating."""
        prompt = self.create_conforming_prompt(
            "dr0001", set_id="dryset", body="Some prompt body.\n"
        )
        text_before = prompt.read_text(encoding="utf-8")
        sha_before = hashlib.sha256(text_before.encode("utf-8")).hexdigest()

        rc = cli.main(
            [
                "prompts",
                "set",
                "executed",
                "dr0001",
                "--dry-run",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(prompt.exists())

        text_after = prompt.read_text(encoding="utf-8")
        sha_after = hashlib.sha256(text_after.encode("utf-8")).hexdigest()
        self.assertEqual(sha_before, sha_after)


if __name__ == "__main__":
    unittest.main()

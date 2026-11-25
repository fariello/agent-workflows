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

import pytest

from agent_workflows import artifact_meta, artifact_rename, check_engine, cli


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
        set_id: str = "testset",
        slug: str = "test-prompt",
        body: str = "",
    ) -> tuple[Path, str]:
        """Create a conforming prompt through `aw prompts new`; return ``(path, id6)``.

        The metadata comment is written by the verb (and so by `artifact_meta`); only the body, which
        the verb deliberately leaves to the agent, is appended here.
        """
        buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", io.StringIO()):
            rc = cli.main(
                [
                    "prompts",
                    "new",
                    "--slug",
                    slug,
                    "--set",
                    set_id,
                    "--date",
                    "2026-10-02",
                    "--apply",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0, buf.getvalue())
        pending = self.repo_root / ".aw" / "records" / "prompts" / "pending"
        matches = sorted(pending.glob(f"20261002-{set_id}-01-*-{slug}.prompt.md"))
        self.assertEqual(len(matches), 1, matches)
        p = matches[0]
        text = p.read_text(encoding="utf-8")
        self.assertEqual(len(text.splitlines()), 1)
        id6 = artifact_meta.read_text(text, record_type="prompt").id6 or None
        self.assertIsNotNone(id6)
        assert id6 is not None
        self.assertEqual(p.name, f"20261002-{set_id}-01-{id6}-{slug}.prompt.md")
        state = artifact_meta.read_text(text, record_type="prompt")
        self.assertEqual(state.id6, id6)
        self.assertEqual(state.status, "pending")
        self.assertEqual(state.set_id, set_id)
        if body:
            p.write_text(text.rstrip("\n") + "\n\n" + body, encoding="utf-8")
        return p, id6

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
        _prompt, id6 = self.create_conforming_prompt(set_id="vocset")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "prompts",
                    "set",
                    "draft",
                    id6,
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
        prompt, id6 = self.create_conforming_prompt(set_id="bodyset", body=body)
        body_stripped = body.strip()
        body_sha_before = hashlib.sha256(body_stripped.encode("utf-8")).hexdigest()

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "prompts",
                    "set",
                    "executed",
                    id6,
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
        self.assertFalse(artifact_meta.has_prompt_metadata_comment(dest_text))
        self.assertNotIn("- Status:", dest_text)
        # Check original body is preserved in dest (before workflow history)
        hist_idx = dest_text.find("## Workflow history")
        self.assertNotEqual(hist_idx, -1)
        body_region = dest_text[:hist_idx].strip()
        self.assertEqual(body_region, original_text.strip())

    def test_dry_run_byte_identity(self):
        """Dry-run previews and leaves file byte-identical without relocating."""
        prompt, id6 = self.create_conforming_prompt(
            set_id="dryset", body="Some prompt body.\n"
        )
        text_before = prompt.read_text(encoding="utf-8")
        sha_before = hashlib.sha256(text_before.encode("utf-8")).hexdigest()

        rc = cli.main(
            [
                "prompts",
                "set",
                "executed",
                id6,
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


@pytest.mark.core
class TestPromptCommentMetaOwnership(unittest.TestCase):
    """Behavioral tests for prompt comment and mirror helpers owned by artifact_meta (t3t7za)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_prompt_meta_")
        self.repo_root = Path(self.temp_dir)
        for bucket in ("pending", "executed", "superseded", "not-executed", "reusable"):
            (self.repo_root / ".aw" / "records" / "prompts" / bucket).mkdir(
                parents=True, exist_ok=True
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_has_prompt_metadata_comment_cases(self):
        """Detect conforming and minimal aw-prompt comments; ignore commentless and body comments."""
        conforming = (
            f"<!-- aw-prompt: Kind: research | Id: ab12cd | Set: demo | Status: pending "
            f". {artifact_meta.PROMPT_METADATA_TRAILER} -->\n\nBody.\n"
        )
        minimal = "<!-- aw-prompt: Kind: research -->\n\nBody.\n"
        commentless = "# Prompt title\n\nBody.\n"
        non_leading = "# Prompt title\n\n<!-- aw-prompt: Kind: research -->\n"
        managed = "<!-- aw-managed-prompt: id: ab12cd | status: pending -->\n\nBody.\n"

        self.assertTrue(artifact_meta.has_prompt_metadata_comment(conforming))
        self.assertTrue(artifact_meta.has_prompt_metadata_comment(minimal))
        self.assertFalse(artifact_meta.has_prompt_metadata_comment(commentless))
        self.assertFalse(artifact_meta.has_prompt_metadata_comment(""))
        self.assertFalse(artifact_meta.has_prompt_metadata_comment(non_leading))
        self.assertFalse(artifact_meta.has_prompt_metadata_comment(managed))

    def test_inject_prompt_metadata_id6_and_purity(self):
        """Inject Id:/Set: idempotently while leaving commentless prompts unchanged."""
        src = (
            f"<!-- aw-prompt: Kind: research | Status: pending "
            f". {artifact_meta.PROMPT_METADATA_TRAILER} -->\n\nPrompt body.\n"
        )
        injected = artifact_meta.inject_prompt_metadata_id6(
            src, id6="ab12cd", set_id="demoset"
        )
        state = artifact_meta.read_text(injected, record_type="prompt")
        self.assertEqual(state.id6, "ab12cd")
        self.assertEqual(state.set_id, "demoset")
        self.assertTrue(injected.endswith("\n\nPrompt body.\n"))

        # Idempotent: an existing Id: is never overwritten.
        again = artifact_meta.inject_prompt_metadata_id6(
            injected, id6="zz9999", set_id="otherset"
        )
        self.assertEqual(again, injected)

        # Existing Set: is preserved without duplication.
        with_set = "<!-- aw-prompt: Kind: research | Set: keepset | Status: pending -->\nBody.\n"
        injected_set = artifact_meta.inject_prompt_metadata_id6(
            with_set, id6="cd34ef", set_id="ignoredset"
        )
        first_line = injected_set.splitlines()[0]
        self.assertEqual(first_line.count("Set:"), 1)
        self.assertIn("Set: keepset", first_line)
        self.assertIn("Id: cd34ef", first_line)

        # Refusal-to-mint purity on commentless and non-leading comment prompts.
        plain = "# Plain prompt\n\nNo comment here.\n"
        self.assertEqual(
            artifact_meta.inject_prompt_metadata_id6(plain, id6="ab12cd", set_id="s1"),
            plain,
        )
        body_comment = "# Plain prompt\n\n<!-- aw-prompt: Kind: research -->\n"
        self.assertEqual(
            artifact_meta.inject_prompt_metadata_id6(
                body_comment, id6="ab12cd", set_id="s1"
            ),
            body_comment,
        )

    def test_update_prompt_metadata_status_and_purity(self):
        """Update or insert Status: idempotently while leaving commentless prompts unchanged."""
        src = (
            "<!-- aw-prompt: Kind: research | Id: ab12cd | Set: demo | Status: pending -->\n"
            "\nPrompt body.\n"
        )
        updated = artifact_meta.update_prompt_metadata_status(src, "executed")
        self.assertEqual(
            artifact_meta.read_text(updated, record_type="prompt").status, "executed"
        )
        self.assertTrue(updated.endswith("\n\nPrompt body.\n"))

        # Idempotent when status already matches.
        self.assertEqual(
            artifact_meta.update_prompt_metadata_status(updated, "executed"), updated
        )

        # Insert Status: when missing from comment.
        no_status = (
            "<!-- aw-prompt: Kind: research | Id: ab12cd | Set: demo -->\nBody.\n"
        )
        inserted = artifact_meta.update_prompt_metadata_status(no_status, "reusable")
        self.assertEqual(
            artifact_meta.read_text(inserted, record_type="prompt").status, "reusable"
        )
        self.assertTrue(inserted.endswith("\nBody.\n"))

        # Refusal-to-mint purity on commentless and non-leading comment prompts.
        plain = "# Plain prompt\n\nBody.\n"
        self.assertEqual(
            artifact_meta.update_prompt_metadata_status(plain, "executed"), plain
        )
        body_comment = "# Plain prompt\n\n<!-- aw-prompt: Kind: research -->\n"
        self.assertEqual(
            artifact_meta.update_prompt_metadata_status(body_comment, "executed"),
            body_comment,
        )

    def test_validate_prompt_content_cases(self):
        """validate_prompt_content checks missing comments, minimal comments, and id/status drift."""
        prompts_dir = self.repo_root / ".aw" / "records" / "prompts"

        # 1. Missing comment on post-cutover prompt
        missing = prompts_dir / "pending" / "20261015-demo-01-ab12cd-missing.prompt.md"
        missing.write_text("# Body only\n", encoding="utf-8")
        missing_rules = [
            d.rule
            for d in check_engine.validate_prompt_content(
                missing, repo_root=self.repo_root
            )
        ]
        self.assertIn("check.prompt-metadata-missing", missing_rules)

        # 2. Minimal Kind-only comment (no Id:/Status:): recognized as having a comment
        minimal = prompts_dir / "pending" / "20261015-demo-02-ef34gh-minimal.prompt.md"
        minimal.write_text(
            "<!-- aw-prompt: Kind: research -->\n\nBody.\n", encoding="utf-8"
        )
        minimal_rules = [
            d.rule
            for d in check_engine.validate_prompt_content(
                minimal, repo_root=self.repo_root
            )
        ]
        self.assertEqual(minimal_rules, [])

        # 3. Mismatched Id: and Status:
        bad = prompts_dir / "executed" / "20261015-demo-03-ij56kl-mismatch.prompt.md"
        bad.write_text(
            "<!-- aw-prompt: Kind: research | Id: zz9999 | Set: demo | Status: pending -->\n\nBody.\n",
            encoding="utf-8",
        )
        bad_rules = [
            d.rule
            for d in check_engine.validate_prompt_content(bad, repo_root=self.repo_root)
        ]
        self.assertIn("check.prompt-id-mismatch", bad_rules)
        self.assertIn("check.prompt-status-mismatch", bad_rules)

        # 4. Conforming prompt
        good = prompts_dir / "pending" / "20261015-demo-04-mn78op-good.prompt.md"
        good.write_text(
            "<!-- aw-prompt: Kind: research | Id: mn78op | Set: demo | Status: pending -->\n\nBody.\n",
            encoding="utf-8",
        )
        self.assertEqual(
            check_engine.validate_prompt_content(good, repo_root=self.repo_root), []
        )

    def test_artifact_rename_prompt_set_and_to_id6_with_and_without_comment(self):
        """Prompt --to-id6 and --set renames preserve purity and update comment metadata."""
        pending = self.repo_root / ".aw" / "records" / "prompts" / "pending"

        # A. Legacy prompt WITH metadata comment
        with_comment = pending / "20260901-1200-01-legacy-comment.prompt.md"
        with_comment.write_text(
            "<!-- aw-prompt: Kind: research | Status: pending -->\n\nCommented body.\n",
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", io.StringIO()):
            rc = cli.main(
                [
                    "rename",
                    "prompts",
                    str(with_comment),
                    "--to-id6",
                    "--set",
                    "firstset",
                    "--apply",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn("into the aw-prompt metadata comment", buf.getvalue())
        self.assertFalse(with_comment.exists())
        matches = sorted(pending.glob("20260901-*-01-*-legacy-comment.prompt.md"))
        self.assertEqual(len(matches), 1, matches)
        renamed = matches[0]
        renamed_text = renamed.read_text(encoding="utf-8")
        state1 = artifact_meta.read_text(renamed_text, record_type="prompt")
        self.assertTrue(state1.id6)
        self.assertEqual(state1.fields.get("set"), "firstset")
        self.assertTrue(renamed_text.endswith("\n\nCommented body.\n"))

        # Follow-up Set: rename updates Set: in the metadata comment
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2), patch("sys.stderr", io.StringIO()):
            rc2 = cli.main(
                [
                    "rename",
                    "prompts",
                    state1.id6,
                    "--set",
                    "secondset",
                    "--apply",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc2, 0, buf2.getvalue())
        matches2 = sorted(
            pending.glob(f"20260901-secondset-01-{state1.id6}-legacy-comment.prompt.md")
        )
        self.assertEqual(len(matches2), 1, matches2)
        state2 = artifact_meta.read_text(
            matches2[0].read_text(encoding="utf-8"), record_type="prompt"
        )
        self.assertEqual(state2.fields.get("set"), "secondset")

        # B. Legacy prompt WITHOUT metadata comment (refusal-to-mint purity)
        without_comment = pending / "20260901-1201-01-legacy-plain.prompt.md"
        plain_bytes = b"# Plain legacy prompt\n\nKeep body pure.\n"
        without_comment.write_bytes(plain_bytes)
        buf3 = io.StringIO()
        with patch("sys.stdout", buf3), patch("sys.stderr", io.StringIO()):
            rc3 = cli.main(
                [
                    "rename",
                    "prompts",
                    str(without_comment),
                    "--to-id6",
                    "--set",
                    "plainset",
                    "--apply",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc3, 0, buf3.getvalue())
        self.assertIn("FILENAME ONLY", buf3.getvalue())
        self.assertFalse(without_comment.exists())
        plain_matches = sorted(pending.glob("20260901-*-01-*-legacy-plain.prompt.md"))
        self.assertEqual(len(plain_matches), 1, plain_matches)
        self.assertEqual(plain_matches[0].read_bytes(), plain_bytes)
        self.assertFalse(
            artifact_meta.has_prompt_metadata_comment(
                plain_matches[0].read_text(encoding="utf-8")
            )
        )

    def test_log_format_id6_mirror_extraction_with_and_without_bom(self):
        """log_format_id6 extracts mirror ids from YAML and aw-managed-prompt headers (with BOM)."""
        records_root = self.repo_root / ".aw" / "records"
        meta_dir = records_root / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        for id6 in ("ab12cd", "ef34gh", "ij56kl", "mn78op"):
            (meta_dir / f"{id6}.jsonl").write_text(
                f'{{"op":"create","id":"{id6}"}}\n', encoding="utf-8"
            )

        specs_dir = records_root / "specs" / "draft"
        specs_dir.mkdir(parents=True, exist_ok=True)
        yaml_no_bom = specs_dir / "yaml-no-bom.spec.md"
        yaml_no_bom.write_text(
            "---\nid: ab12cd\nstatus: draft\n---\n# Spec\n", encoding="utf-8"
        )
        yaml_with_bom = specs_dir / "yaml-with-bom.spec.md"
        yaml_with_bom.write_text(
            "\ufeff---\nid: ef34gh\nstatus: draft\n---\n# Spec\n", encoding="utf-8"
        )
        yaml_no_log = specs_dir / "yaml-no-log.spec.md"
        yaml_no_log.write_text(
            "---\nid: zz9999\nstatus: draft\n---\n# Spec\n", encoding="utf-8"
        )

        prompts_dir = records_root / "prompts" / "pending"
        prompt_no_bom = prompts_dir / "managed-no-bom.prompt.md"
        prompt_no_bom.write_text(
            "<!-- aw-managed-prompt: id: ij56kl | status: pending . Pipeline metadata only. -->\n"
            "\nPrompt body.\n",
            encoding="utf-8",
        )
        prompt_with_bom = prompts_dir / "managed-with-bom.prompt.md"
        prompt_with_bom.write_text(
            "\ufeff<!-- aw-managed-prompt: id: mn78op | status: pending . Pipeline metadata only. -->\n"
            "\nPrompt body.\n",
            encoding="utf-8",
        )

        self.assertEqual(
            artifact_rename.log_format_id6(yaml_no_bom, self.repo_root, "specs"),
            "ab12cd",
        )
        self.assertEqual(
            artifact_rename.log_format_id6(yaml_with_bom, self.repo_root, "specs"),
            "ef34gh",
        )
        self.assertIsNone(
            artifact_rename.log_format_id6(yaml_no_log, self.repo_root, "specs")
        )
        self.assertEqual(
            artifact_rename.log_format_id6(prompt_no_bom, self.repo_root, "prompts"),
            "ij56kl",
        )
        self.assertEqual(
            artifact_rename.log_format_id6(prompt_with_bom, self.repo_root, "prompts"),
            "mn78op",
        )
        self.assertEqual(
            artifact_meta.read_mirror_id6(
                "\ufeff---\nid: qr90st\n---\n# Walkthrough\n"
            ),
            "qr90st",
        )
        self.assertIsNone(artifact_meta.read_mirror_id6("# Plain markdown\n"))


if __name__ == "__main__":
    unittest.main()

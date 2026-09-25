"""Tests for installer managed section consent and drift decisions (IPD b4bvas).

Verifies the four-case consent rules in `engine._apply_section_consent` and `engine.merge_aw_block`:
1. disk == desired, stale record -> adopt and re-record hash, no warning.
2. disk == recorded, desired differs -> refresh to desired and update hash, no warning.
3. disk differs from both -> preserve disk, leave record untouched, warn naming key.
4. no record, disk differs from desired -> preserve disk, write no record, warn naming key.

Also verifies regression rows:
- declined tombstone omits section.
- absent section on disk writes desired and records hash.
- manifest=None writes desired (back-compat).
"""

from __future__ import annotations

import io
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import engine as INS
from agent_workflows import manifest as M
from tests.support import SOURCE_WORKFLOWS, init_repo


def make_section(slug: str, body: str) -> INS.AwSection:
    return INS.AwSection(slug=slug, lines=body.splitlines())


def _call_apply_section_consent(
    desired: list[INS.AwSection],
    on_disk: list[INS.AwSection],
    *,
    manifest: M.Manifest | None,
    file_key: str,
    warnings: list[str] | None = None,
) -> list[INS.AwSection]:
    try:
        return INS._apply_section_consent(
            desired, on_disk, manifest=manifest, file_key=file_key, warnings=warnings
        )
    except TypeError:
        return INS._apply_section_consent(
            desired, on_disk, manifest=manifest, file_key=file_key
        )


def _call_merge_aw_block(
    existing: str,
    sections: list[INS.AwSection],
    *,
    style: INS.AwCommentStyle = INS.AW_STYLE_MARKDOWN,
    default_header: str = "",
    manifest: M.Manifest | None = None,
    file_key: str = "",
    warnings: list[str] | None = None,
) -> tuple[str, str]:
    try:
        return INS.merge_aw_block(
            existing,
            sections,
            style=style,
            default_header=default_header,
            manifest=manifest,
            file_key=file_key,
            warnings=warnings,
        )
    except TypeError:
        return INS.merge_aw_block(
            existing,
            sections,
            style=style,
            default_header=default_header,
            manifest=manifest,
            file_key=file_key,
        )


class SectionConsentUnitTests(unittest.TestCase):
    """Direct unit tests for `_apply_section_consent` and `merge_aw_block`."""

    def test_case_1_disk_equals_desired_stale_record_adopts_and_updates_hash(
        self,
    ) -> None:
        """Case 1: disk == desired, record STALE (different hash).
        Result body is desired, recorded hash updated to desired, NO warning emitted.
        """
        key = "AGENTS.md#aw:pointer"
        desired_body = "## Desired Pointer Content\nSome lines here."
        disk_body = "## Desired Pointer Content\nSome lines here."
        stale_body = "## Old Stale Content"

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "managed-sections.json"
            manifest = M.Manifest()
            manifest.record(
                key, stale_body, kind="section", host="", logical_id="pointer"
            )
            M.save(manifest, manifest_path)

            loaded_manifest = M.load(manifest_path)
            self.assertNotEqual(
                loaded_manifest.recorded_hash(key), M.hash_content(desired_body)
            )

            warns: list[str] = []
            res = _call_apply_section_consent(
                desired,
                on_disk,
                manifest=loaded_manifest,
                file_key="AGENTS.md",
                warnings=warns,
            )

            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].body, desired_body)
            self.assertEqual(
                loaded_manifest.recorded_hash(key), M.hash_content(desired_body)
            )
            self.assertEqual(warns, [])

            M.save(loaded_manifest, manifest_path)
            reloaded = M.load(manifest_path)
            self.assertEqual(reloaded.recorded_hash(key), M.hash_content(desired_body))

    def test_case_2_disk_equals_recorded_desired_differs_refreshes_and_updates_hash(
        self,
    ) -> None:
        """Case 2: disk == recorded, desired differs (generator changed).
        Result body is desired, record updated to desired, no warning.
        """
        key = "AGENTS.md#aw:pointer"
        old_recorded_body = "## Old Generator Content"
        disk_body = "## Old Generator Content"
        desired_body = "## New Generator Content\nUpdated lines."

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        manifest = M.Manifest()
        manifest.record(
            key, old_recorded_body, kind="section", host="", logical_id="pointer"
        )

        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].body, desired_body)
        self.assertEqual(manifest.recorded_hash(key), M.hash_content(desired_body))
        self.assertEqual(warns, [])

    def test_case_3_disk_differs_from_both_preserves_body_and_leaves_record_untouched(
        self,
    ) -> None:
        """Case 3 (body and record): disk differs from BOTH desired and recorded.
        Result body is disk (preserved), record UNCHANGED.
        """
        key = "AGENTS.md#aw:pointer"
        recorded_body = "## Recorded Baseline"
        disk_body = "## User Modified Content"
        desired_body = "## New Generator Content"

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        manifest = M.Manifest()
        manifest.record(
            key, recorded_body, kind="section", host="", logical_id="pointer"
        )
        orig_hash = manifest.recorded_hash(key)

        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].body, disk_body)
        self.assertEqual(manifest.recorded_hash(key), orig_hash)

    def test_case_3_disk_differs_from_both_emits_warning(self) -> None:
        """Case 3 (warning): disk differs from BOTH desired and recorded.
        Exactly one warning naming AGENTS.md#aw:pointer.
        """
        key = "AGENTS.md#aw:pointer"
        recorded_body = "## Recorded Baseline"
        disk_body = "## User Modified Content"
        desired_body = "## New Generator Content"

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        manifest = M.Manifest()
        manifest.record(
            key, recorded_body, kind="section", host="", logical_id="pointer"
        )

        warns: list[str] = []
        _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(warns), 1)
        self.assertIn(
            "Warning: AGENTS.md#aw:pointer has manual modifications;", warns[0]
        )
        self.assertIn(
            "kept your version, the regenerated section was NOT applied.", warns[0]
        )
        self.assertIn(
            "delete that section (from its <!-- aw:pointer --> marker to the next marker) and re-run install.",
            warns[0],
        )

    def test_case_4_no_record_disk_differs_from_desired_preserves_and_writes_no_record(
        self,
    ) -> None:
        """Case 4 (body and record): NO record, disk differs from desired.
        Result body is disk, NO record written for the key.
        """
        key = "AGENTS.md#aw:pointer"
        disk_body = "## User Hand Written Content"
        desired_body = "## Generator Content"

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        manifest = M.Manifest()
        self.assertIsNone(manifest.recorded_hash(key))

        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].body, disk_body)
        self.assertIsNone(manifest.recorded_hash(key))

    def test_case_4_no_record_disk_differs_from_desired_emits_warning(self) -> None:
        """Case 4 (warning): NO record, disk differs from desired.
        Exactly one warning naming the key.
        """
        key = "AGENTS.md#aw:pointer"
        disk_body = "## User Hand Written Content"
        desired_body = "## Generator Content"

        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        manifest = M.Manifest()
        warns: list[str] = []
        _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(warns), 1)
        self.assertIn(f"Warning: {key} has manual modifications;", warns[0])
        self.assertIn(
            "kept your version, the regenerated section was NOT applied.", warns[0]
        )

    def test_regression_declined_tombstone_omits_section(self) -> None:
        """Regression: a declined tombstone omits the section."""
        key = "AGENTS.md#aw:pointer"
        desired = [make_section("pointer", "## Desired")]
        on_disk = [make_section("pointer", "## On Disk")]

        manifest = M.Manifest()
        manifest.mark_declined(key)

        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(res, [])
        self.assertEqual(warns, [])

    def test_regression_absent_on_disk_writes_desired_and_records_hash(self) -> None:
        """Regression: a section absent on disk (on_disk=[]) writes desired and records hash."""
        key = "AGENTS.md#aw:pointer"
        desired_body = "## Desired New Section"
        desired = [make_section("pointer", desired_body)]
        on_disk: list[INS.AwSection] = []

        manifest = M.Manifest()
        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=manifest, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].body, desired_body)
        self.assertEqual(manifest.recorded_hash(key), M.hash_content(desired_body))
        self.assertEqual(warns, [])

    def test_regression_manifest_none_writes_desired(self) -> None:
        """Regression: manifest=None writes desired (back-compat)."""
        desired_body = "## Desired Content"
        disk_body = "## Different Disk Content"
        desired = [make_section("pointer", desired_body)]
        on_disk = [make_section("pointer", disk_body)]

        warns: list[str] = []
        res = _call_apply_section_consent(
            desired, on_disk, manifest=None, file_key="AGENTS.md", warnings=warns
        )

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].body, desired_body)
        self.assertEqual(warns, [])

    def test_merge_aw_block_case_3_warning_forwarded(self) -> None:
        """End-to-end: merge_aw_block forwards warnings from case 3."""
        key = "AGENTS.md#aw:pointer"
        recorded_body = "## Baseline"
        disk_body = "## Drifted User Text"
        desired_body = "## New Desired Text"

        existing = f"# Header\n\n<!-- aw:block -->\n<!-- aw:pointer -->\n{disk_body}\n<!-- /aw:block -->\n"
        sections = [make_section("pointer", desired_body)]

        manifest = M.Manifest()
        manifest.record(
            key, recorded_body, kind="section", host="", logical_id="pointer"
        )

        warns: list[str] = []
        new_text, action = _call_merge_aw_block(
            existing,
            sections,
            default_header="# Header",
            manifest=manifest,
            file_key="AGENTS.md",
            warnings=warns,
        )

        self.assertEqual(action, "refreshed")
        self.assertIn(disk_body.strip(), new_text)
        self.assertEqual(len(warns), 1)
        self.assertIn(
            "Warning: AGENTS.md#aw:pointer has manual modifications;", warns[0]
        )

    def test_install_into_repo_user_edited_pointer_warns_and_preserves(self) -> None:
        """Install-level test: seed repo, install, hand-edit pointer, re-install, assert warning and preserved edit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            init_repo(repo_root)

            INS.install_into_repo(repo_root, SOURCE_WORKFLOWS, yes=True, no_color=True)

            agents_file = repo_root / "AGENTS.md"
            self.assertTrue(agents_file.exists())
            content = agents_file.read_text(encoding="utf-8")

            custom_pointer = (
                "## Custom User Hand Edited Pointer\nMy custom guidelines.\n\n"
            )
            modified_content = re.sub(
                r"<!-- aw:pointer -->.*?(?=<!-- /aw:block -->)",
                f"<!-- aw:pointer -->\n{custom_pointer}",
                content,
                flags=re.DOTALL,
            )
            self.assertIn("Custom User Hand Edited Pointer", modified_content)
            agents_file.write_text(modified_content, encoding="utf-8")

            out_buf = io.StringIO()
            with redirect_stdout(out_buf):
                INS.install_into_repo(
                    repo_root, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            captured = out_buf.getvalue()
            self.assertIn(
                "Warning: AGENTS.md#aw:pointer has manual modifications;", captured
            )
            self.assertIn(
                "kept your version, the regenerated section was NOT applied.", captured
            )

            content_after = agents_file.read_text(encoding="utf-8")
            self.assertIn("Custom User Hand Edited Pointer", content_after)

    def test_ensure_untracked_gitignore_warns_when_preserved_and_unchanged(
        self,
    ) -> None:
        """.gitignore caller warns before early return when section is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            gitignore_path = repo_root / ".gitignore"
            custom_body = "# Custom untracked section\n*.myuntracked\n"
            existing = f"# Top\n\n# <!-- aw:block -->\n# <!-- aw:untracked -->\n{custom_body}# <!-- /aw:block -->\n"
            gitignore_path.write_text(existing, encoding="utf-8")

            manifest = M.Manifest()
            # Record stale baseline hash so it differs from both desired and disk
            manifest.record(
                ".gitignore#aw:untracked",
                "# Old baseline\n",
                kind="section",
                host="",
                logical_id="untracked",
            )

            plan = INS.InstallPlan(
                source_root=SOURCE_WORKFLOWS,
                repo_root=repo_root,
                yes=True,
                no_color=True,
                dry_run=False,
                backup=False,
                prune=False,
                manifest=manifest,
            )

            out_buf = io.StringIO()
            with redirect_stdout(out_buf):
                status = INS.ensure_untracked_gitignore(plan, use_git=False)

            captured = out_buf.getvalue()
            self.assertEqual(status, "untracked-safety block already current")
            self.assertIn(
                "Warning: .gitignore#aw:untracked has manual modifications;", captured
            )
            self.assertEqual(gitignore_path.read_text(encoding="utf-8"), existing)

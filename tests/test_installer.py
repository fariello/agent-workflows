"""Self-tests for install-workflows.py.

End-to-end tests run the installer as a subprocess against throwaway git repos and assert
filesystem state (the real behavior, including git staging). Unit tests import the pure
functions. Stdlib unittest only.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.support import REPO_ROOT, init_repo, run_installer

# The install engine now lives in the agent_workflows package (IPD-2). Import it directly
# for the unit tests; the root install-workflows.py is a thin deprecated shim exercised by
# the subprocess-based end-to-end tests via run_installer().
from agent_workflows import engine as INS


class InstallerUnitTests(unittest.TestCase):
    """Pure-function tests (no filesystem side effects)."""

    def test_parse_manifest_has_core_and_catalog(self):
        source = REPO_ROOT / ".agents" / "workflows"
        workflows = INS.parse_manifest(source)
        commands = {w.command for w in workflows}
        # Core/standalone commands present.
        for expected in ("release-review", "plan-review", "assess", "advise", "verify"):
            self.assertIn(expected, commands)
        # Catalog rows present (assess concerns, advise personas).
        self.assertIn("assess-security", commands)
        self.assertIn("advise-skeptic", commands)

    def test_catalog_rows_are_recognized(self):
        def mk(c):
            return INS.Workflow(command=c, body="b", description="d")

        self.assertTrue(INS.is_concern_catalog_row(mk("assess-security")))
        self.assertTrue(INS.is_concern_catalog_row(mk("advise-skeptic")))
        self.assertFalse(INS.is_concern_catalog_row(mk("assess")))
        self.assertFalse(INS.is_concern_catalog_row(mk("advise")))
        self.assertFalse(INS.is_concern_catalog_row(mk("release-review")))
        # assess-all is a real command despite the assess- prefix (exception).
        self.assertFalse(INS.is_concern_catalog_row(mk("assess-all")))

    def test_shim_generation_collapses_catalog(self):
        source = REPO_ROOT / ".agents" / "workflows"
        workflows = INS.parse_manifest(source)
        shims = INS.generate_shim_members(workflows, source)
        # No per-concern / per-persona shims are generated.
        self.assertFalse(any("/assess-security.md" in k for k in shims))
        self.assertFalse(any("/advise-skeptic.md" in k for k in shims))
        # The single parameterized commands are generated.
        self.assertTrue(any(k.endswith("/assess.md") for k in shims))
        self.assertTrue(any(k.endswith("/advise.md") for k in shims))
        # assess-all gets its own shim (prefix exception).
        self.assertTrue(any(k.endswith("/assess-all.md") for k in shims))

    def test_read_version_in_git_tree_matches_resolver(self):
        # In this project's real git tree, read_version is git-aware and must agree with
        # the resolver (a semver/.dev string), not necessarily the raw VERSION file.
        source = REPO_ROOT / ".agents" / "workflows"
        from agent_workflows import versioning as VER

        expected = VER.resolve_version(source, version_file=source / "VERSION")
        self.assertEqual(INS.read_version(source), expected)

    def test_read_version_non_git_reads_file(self):
        # V-9 characterization: from a non-git tree (a copied/unpacked install),
        # read_version MUST fall back to the baked VERSION file value.
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "workflows"
            source.mkdir(parents=True)
            (source / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            self.assertEqual(INS.read_version(source), "1.2.3")

    def test_parse_args_no_color(self):
        args = INS.parse_args(["--no-color"])
        self.assertTrue(args.no_color)
        args_default = INS.parse_args([])
        self.assertFalse(args_default.no_color)

    def test_format_output_item(self):
        from agent_workflows.term import Term

        # Color enabled
        term_color = Term(color=True)
        res = INS.format_output_item("foo/bar.py [install]", term_color)
        # Should be green and bold for [added    ]
        self.assertIn("\033[32;1m[added    ]\033[0m", res)
        self.assertIn("foo/bar.py", res)
        self.assertNotIn("(dry-run)", res)

        res_dry = INS.format_output_item("foo/bar.py [overwrite, dry-run]", term_color)
        # Should be red and bold for [overwrite] and end with (dry-run)
        self.assertIn("\033[31;1m[overwrite]\033[0m", res_dry)
        self.assertIn("foo/bar.py", res_dry)
        self.assertTrue(res_dry.endswith("(dry-run)"))

        # Color disabled
        term_plain = Term(color=False)
        res_plain = INS.format_output_item("foo/bar.py [already current]", term_plain)
        self.assertEqual(res_plain, "[no change] foo/bar.py")

        res_prune = INS.format_output_item("foo/bar.py [git rm]", term_plain)
        self.assertEqual(res_prune, "[removed  ] foo/bar.py")


class InstallerEndToEndTests(unittest.TestCase):
    """Run the installer against throwaway repos and assert filesystem state."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")

    def tearDown(self):
        self._tmp.cleanup()

    def _shims(self, tool_dir: str) -> set[str]:
        d = self.repo / tool_dir
        return {p.name for p in d.glob("*.md")} if d.is_dir() else set()

    def test_fresh_install(self):
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Framework files landed.
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".agents/workflows/VERSION").is_file())
        # A single parameterized assess shim, and no per-concern shims.
        oc = self._shims(".opencode/commands")
        self.assertIn("assess.md", oc)
        self.assertIn("advise.md", oc)
        self.assertNotIn("assess-security.md", oc)
        self.assertNotIn("advise-skeptic.md", oc)
        # AGENTS pointer written.
        self.assertTrue((self.repo / "AGENTS.md").is_file())
        # The installer itself is NOT copied into the target.
        self.assertFalse((self.repo / "install-workflows.py").exists())

    def test_idempotent_rerun(self):
        run_installer(self.repo)
        before = sorted(
            p.relative_to(self.repo).as_posix()
            for p in self.repo.rglob("*")
            if p.is_file()
        )
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = sorted(
            p.relative_to(self.repo).as_posix()
            for p in self.repo.rglob("*")
            if p.is_file()
        )
        self.assertEqual(before, after, "re-run changed the set of files")

    def test_dry_run_makes_no_changes(self):
        proc = run_installer(self.repo, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(
            (self.repo / ".agents/workflows/index.md").exists(), "dry-run wrote files"
        )
        self.assertFalse((self.repo / ".opencode/commands/assess.md").exists())

    def test_prune_removes_legacy_assess_shims(self):
        run_installer(self.repo)
        # Simulate an older install that had per-concern shims.
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text(
            "Read and execute @.agents/workflows/assess-security\n", encoding="utf-8"
        )
        legacy2 = self.repo / ".claude/commands/assess-prose.md"
        legacy2.write_text(
            "Read and execute @.agents/workflows/assess-prose\n", encoding="utf-8"
        )
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(legacy.exists(), "stale assess-security shim not pruned")
        self.assertFalse(legacy2.exists(), "stale assess-prose shim not pruned")

    def test_no_prune_keeps_stale(self):
        run_installer(self.repo)
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text(
            "Read and execute @.agents/workflows/assess-security\n", encoding="utf-8"
        )
        run_installer(self.repo, "--no-prune")
        self.assertTrue(legacy.exists(), "--no-prune should not remove stale files")

    def test_legacy_layout_migration(self):
        # Pre-D17 layout: a root release-review/ dir (the old framework location).
        legacy_dir = self.repo / "release-review"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "README.md").write_text("legacy runbook\n", encoding="utf-8")
        from tests.support import git

        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "legacy layout")
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # New canonical layout exists after migration/install.
        self.assertTrue((self.repo / ".agents/workflows/index.md").is_file())

    def test_version_flag(self):
        # --version is git-aware (resolver). In this project's git tree it reports the
        # resolved semver/.dev string, which is what read_version(source) returns.
        proc = run_installer(self.repo, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        source = REPO_ROOT / ".agents" / "workflows"
        expected = INS.read_version(source)
        self.assertEqual(proc.stdout.strip(), expected)

    def test_tool_scripts_are_executable_and_staged(self):
        import os
        from tests.support import git

        run_installer(self.repo)
        tool = self.repo / ".agents/workflows/assess/tools/scan_secrets.py"
        # The re-run-leaves-nothing-unstaged idempotency guarantee holds on every OS.
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        leftover = git(self.repo, "status", "--porcelain").stdout.strip()
        self.assertEqual(leftover, "", f"re-run left files unstaged:\n{leftover}")

        # The POSIX executable-bit assertions are meaningful only on POSIX: Windows has no
        # mode exec bit and git there records 100644. Skip the mode checks on Windows.
        if os.name == "posix":
            self.assertTrue(
                tool.stat().st_mode & 0o111, "tool script is not executable"
            )
            indexed = git(
                self.repo,
                "ls-files",
                "-s",
                ".agents/workflows/assess/tools/scan_secrets.py",
            ).stdout
            self.assertTrue(
                indexed.startswith("100755"), f"exec bit not in index: {indexed!r}"
            )

    def test_gitignored_opencode_does_not_abort(self):
        from tests.support import git

        (self.repo / ".gitignore").write_text(".opencode/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-q", "-m", "ignore opencode")
        proc = run_installer(self.repo)
        # Install completes despite the gitignored shim dir.
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ignored by .gitignore", proc.stderr)
        # Shims are still written to disk (they work locally).
        self.assertTrue((self.repo / ".opencode/commands/assess.md").is_file())
        # But .opencode is not staged; .claude and .agents are.
        staged = git(self.repo, "diff", "--cached", "--name-only").stdout
        self.assertNotIn(".opencode/", staged)
        self.assertIn(".claude/commands/assess.md", staged)
        self.assertIn(".agents/workflows/index.md", staged)

    def test_readme_creation_and_preservation(self):
        # 1) Fresh install creates all README files
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        readmes = [
            self.repo / ".agents/workflows/README.md",
            self.repo / ".opencode/commands/README.md",
            self.repo / ".claude/commands/README.md",
            self.repo / "workflow-artifacts/README.md",
        ]
        for path in readmes:
            self.assertTrue(path.is_file(), f"README not created: {path}")

        # Verify they contain expected indicators
        self.assertIn(
            "auto-generated",
            (self.repo / ".opencode/commands/README.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Git Guidelines",
            (self.repo / "workflow-artifacts/README.md").read_text(encoding="utf-8"),
        )

        # 2) Re-run preserves customized workflow-artifacts/README.md
        custom_path = self.repo / "workflow-artifacts/README.md"
        custom_content = "Custom user guidelines for this repo's execution trails."
        custom_path.write_text(custom_content, encoding="utf-8")

        # Run installer again
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            custom_path.read_text(encoding="utf-8"),
            custom_content,
            "Custom README content was overwritten!",
        )

    def test_shim_readme_is_not_pruned(self):
        # Run installer to write shims
        run_installer(self.repo)
        shim_readme = self.repo / ".opencode/commands/README.md"
        self.assertTrue(shim_readme.is_file())

        # Run installer with prune=True
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(shim_readme.is_file(), "Shim README was pruned!")

    def test_rollback_undo(self):
        # 1) Install the framework
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        target_file = self.repo / ".agents/workflows/index.md"
        original_text = target_file.read_text(encoding="utf-8")

        # Modify the target file
        target_file.write_text("MODIFIED CONTENT", encoding="utf-8")

        # 2) Run installer again to trigger an overwrite and backup
        proc2 = run_installer(self.repo)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        # Verify it got overwritten back to original content
        self.assertEqual(target_file.read_text(encoding="utf-8"), original_text)

        # Now modify it again, so we can test rollback
        target_file.write_text("MODIFIED CONTENT SECOND TIME", encoding="utf-8")

        # Run rollback
        proc_undo = run_installer(self.repo, "--undo")
        self.assertEqual(proc_undo.returncode, 0, proc_undo.stderr)

        # Verify it got rolled back to the backup state ("MODIFIED CONTENT" from before the second install!)
        self.assertEqual(target_file.read_text(encoding="utf-8"), "MODIFIED CONTENT")

    def test_backup_auto_pruning(self):
        # 1) Install once so backups dir is created
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        backups_dir = self.repo / ".agent-workflows-installer-backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        # 2) Create 7 mock backup directories manually
        for i in range(7):
            (backups_dir / f"20260709-12000{i}").mkdir(parents=True, exist_ok=True)

        # 3) Run installer again with --yes to trigger pruning (since one more run occurs, it's 8 runs total)
        proc2 = run_installer(self.repo, "--yes")
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        # 4) Verify only 5 backup directories exist under .agent-workflows-installer-backups/
        self.assertTrue(backups_dir.is_dir())
        subdirs = sorted(
            [d for d in backups_dir.iterdir() if d.is_dir()], key=lambda d: d.name
        )
        self.assertEqual(len(subdirs), 5)

    def test_customization_protection(self):
        # Install shims first
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        shim_file = self.repo / ".opencode/commands/assess.md"
        self.assertTrue(shim_file.is_file())

        # Manually customize the shim
        custom_content = (
            "---\ndescription: My custom assessment\n---\nCustom instructions here."
        )
        shim_file.write_text(custom_content, encoding="utf-8")

        # Run installer without --yes (non-interactive mock skips customization overwrite by default)
        proc2 = run_installer(self.repo)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        # Content should remain customized
        self.assertEqual(shim_file.read_text(encoding="utf-8"), custom_content)

        # Run installer with --yes
        proc3 = run_installer(self.repo, "--yes")
        self.assertEqual(proc3.returncode, 0, proc3.stderr)
        # Content should be overwritten back to standard shim template
        self.assertNotEqual(shim_file.read_text(encoding="utf-8"), custom_content)

    def test_diff_mode(self):
        # Run with --diff
        proc = run_installer(self.repo, "--diff")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Diff output should show additions (+) since it's a fresh repo
        self.assertIn("+", proc.stdout)
        # Confirm no files were written to disk
        workflows_dir = self.repo / ".agents/workflows"
        self.assertFalse(workflows_dir.exists())

    def test_shim_expected_does_not_warn(self):
        # Every shim generated from the manifest must NOT be flagged as customized
        source = REPO_ROOT / ".agents" / "workflows"
        workflows = INS.parse_manifest(source)
        shims = INS.generate_shim_members(workflows, source)
        for rel, content in shims.items():
            if rel.endswith("README.md"):
                continue
            self.assertFalse(
                INS.is_shim_customized_vs_expected(content, content),
                f"Generated shim {rel} was flagged as customized vs expected",
            )
            self.assertFalse(
                INS.is_shim_customized(content),
                f"Generated shim {rel} was flagged as customized by fallback check",
            )

    def test_hand_edited_and_legacy_shims(self):
        # Genuinely hand-edited content is customized
        hand_edited = "---\ndescription: custom\n---\nSome user note here."
        self.assertTrue(INS.is_shim_customized(hand_edited))

        # A shim with an old/prior template format is differing (not current expected)
        old_template = (
            "---\ndescription: plan-review\nagent: build\n---\n"
            "Read and execute @.agents/workflows/plan-review\n"
            "Accept case-insensitive options..."
        )
        current_expected = (
            "---\ndescription: plan-review\nagent: build\n---\n"
            "Read and execute @.agents/workflows/plan-review-long\n"
            "Accept case-insensitive options..."
        )
        self.assertTrue(
            INS.is_shim_customized_vs_expected(old_template, current_expected)
        )

    # The overwrite prompt only runs when the installer thinks it is in an interactive
    # session (engine.is_interactive_session). Under a test harness sys.stdin is not a TTY,
    # so we must force interactivity on for these prompt tests; otherwise the prompt is
    # skipped, input() is never called, and the mocked interrupt/choice is never exercised.
    @mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)
    @mock.patch("builtins.input")
    def test_ctrl_c_aborts_install(self, mock_input, _mock_interactive):
        mock_input.side_effect = KeyboardInterrupt()
        target = Path(self._tmp.name) / "plain_ctrl_c"
        target.mkdir()

        # Install once to set up
        run_installer(target)

        # Modify a shim to a value that differs from its generated expected content,
        # so the overwrite prompt is reached.
        shim_file = target / ".opencode/commands/assess.md"
        shim_file.write_text(
            "Read and execute @.agents/workflows/assess.md\nCustomized lines here\n",
            encoding="utf-8",
        )

        # Ctrl-C at the prompt must propagate to main() and abort with 130 (not decline+continue).
        res = INS.main(["--repo", str(target)])
        self.assertEqual(res, 130)
        # The shim was NOT overwritten (the run aborted).
        self.assertIn("Customized lines here", shim_file.read_text(encoding="utf-8"))

    @mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)
    @mock.patch("builtins.input")
    def test_eof_declines_install(self, mock_input, _mock_interactive):
        mock_input.side_effect = EOFError()
        target = Path(self._tmp.name) / "plain_eof"
        target.mkdir()

        # Install once
        run_installer(target)

        # Modify a shim to trigger overwrite
        shim_file = target / ".opencode/commands/assess.md"
        shim_file.write_text(
            "Read and execute @.agents/workflows/assess.md\nCustomized lines here\n",
            encoding="utf-8",
        )

        # EOF at the prompt declines THIS file (safe default) and continues, exiting 0.
        res = INS.main(["--repo", str(target)])
        self.assertEqual(res, 0)
        # Content remains customized because EOF declined overwrite.
        self.assertIn("Customized lines here", shim_file.read_text(encoding="utf-8"))

    @mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)
    @mock.patch("builtins.input")
    def test_diff_option_re_prompts(self, mock_input, _mock_interactive):
        # First return 'd' (show diff), then 'n' (decline).
        mock_input.side_effect = ["d", "n"]
        target = Path(self._tmp.name) / "plain_diff"
        target.mkdir()

        run_installer(target)

        shim_file = target / ".opencode/commands/assess.md"
        shim_file.write_text(
            "Read and execute @.agents/workflows/assess.md\nCustomized lines here\n",
            encoding="utf-8",
        )

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            INS.main(["--repo", str(target)])

        output = buf.getvalue()
        # 'd' should have printed the diff, then re-prompted (and 'n' declined).
        self.assertIn("Diff:", output)
        self.assertIn("-Customized lines here", output)
        # Declined: the customized content remains.
        self.assertIn("Customized lines here", shim_file.read_text(encoding="utf-8"))

    def test_native_agent_files_mirroring(self):
        # 1. By default, absent CLAUDE.md/GEMINI.md are NOT created.
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        self.assertFalse((self.repo / "GEMINI.md").exists())

        # 2. Existing CLAUDE.md / GEMINI.md get the block.
        claude_file = self.repo / "CLAUDE.md"
        gemini_file = self.repo / "GEMINI.md"
        claude_file.write_text("User CLAUDE content\n", encoding="utf-8")
        gemini_file.write_text("User GEMINI content\n", encoding="utf-8")

        proc2 = run_installer(self.repo)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        claude_txt = claude_file.read_text(encoding="utf-8")
        gemini_txt = gemini_file.read_text(encoding="utf-8")

        self.assertIn("User CLAUDE content", claude_txt)
        self.assertIn("<!-- AGENT-WORKFLOWS:BEGIN -->", claude_txt)
        self.assertIn("<!-- AGENT-WORKFLOWS:END -->", claude_txt)

        self.assertIn("User GEMINI content", gemini_txt)
        self.assertIn("<!-- AGENT-WORKFLOWS:BEGIN -->", gemini_txt)
        self.assertIn("<!-- AGENT-WORKFLOWS:END -->", gemini_txt)

        # 3. Dry-run does not write to them.
        claude_file.write_text("User CLAUDE content\n", encoding="utf-8")
        proc3 = run_installer(self.repo, "--dry-run")
        self.assertEqual(proc3.returncode, 0, proc3.stderr)
        self.assertEqual(
            claude_file.read_text(encoding="utf-8"), "User CLAUDE content\n"
        )

        # 4. Re-running is idempotent.
        run_installer(self.repo)
        txt_after = claude_file.read_text(encoding="utf-8")
        self.assertEqual(txt_after.count("<!-- AGENT-WORKFLOWS:BEGIN -->"), 1)

        # 5. Uninstall removes only the block.
        INS.uninstall_repo(self.repo, use_git=True)

        # User content remains in the file
        self.assertTrue(claude_file.is_file())
        self.assertTrue(gemini_file.is_file())
        self.assertIn("User CLAUDE content", claude_file.read_text(encoding="utf-8"))
        self.assertNotIn(
            "<!-- AGENT-WORKFLOWS:BEGIN -->", claude_file.read_text(encoding="utf-8")
        )
        self.assertIn("User GEMINI content", gemini_file.read_text(encoding="utf-8"))
        self.assertNotIn(
            "<!-- AGENT-WORKFLOWS:BEGIN -->", gemini_file.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()

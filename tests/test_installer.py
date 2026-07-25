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


class ArgHintShimTests(unittest.TestCase):
    """Per-workflow argument hint in generated shims (IPD 20260721-1754-02)."""

    # The historical generic arguments line the unset path MUST reproduce byte-for-byte,
    # or is_shim_customized_vs_expected would flag every installed no-hint shim as customized.
    GENERIC_LINE = (
        "If the user provided arguments, treat them as the target path(s) and/or flags "
        "for this workflow: $ARGUMENTS"
    )

    def _wf(self, arg_hint=""):
        return INS.Workflow(
            command="demo",
            body=".agents/workflows/demo/demo.md",
            description="demo",
            arg_hint=arg_hint,
        )

    def test_parse_five_column_row_sets_arg_hint(self):
        # A 5-column row parses and populates arg_hint (real manifest is unaffected here).
        block = (
            f"{INS.MANIFEST_BEGIN}\n"
            "| command | body | lens | description | arg-hint |\n"
            "|---|---|---|---|---|\n"
            "| demo | .agents/workflows/demo/demo.md | - | d | narrow the scope, e.g. `x` |\n"
            f"{INS.MANIFEST_END}\n"
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = Path(tmp.name)
        (src / "index.md").write_text(block, encoding="utf-8")
        wfs = {w.command: w for w in INS.parse_manifest(src)}
        self.assertIn("demo", wfs)
        self.assertEqual(wfs["demo"].arg_hint, "narrow the scope, e.g. `x`")

    def test_three_and_four_column_rows_default_arg_hint_empty(self):
        block = (
            f"{INS.MANIFEST_BEGIN}\n"
            "| command | body | lens | description |\n"
            "|---|---|---|---|\n"
            "| four | .agents/workflows/four/four.md | - | d |\n"
            "| three | .agents/workflows/three/three.md | d |\n"
            f"{INS.MANIFEST_END}\n"
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = Path(tmp.name)
        (src / "index.md").write_text(block, encoding="utf-8")
        wfs = {w.command: w for w in INS.parse_manifest(src)}
        self.assertEqual(wfs["four"].arg_hint, "")
        self.assertEqual(wfs["three"].arg_hint, "")

    def test_unset_hint_renders_generic_line_byte_identical(self):
        for tool in ("opencode", "claude"):
            body = INS.shim_body("demo", self._wf(arg_hint=""), tool)
            self.assertIn(self.GENERIC_LINE, body, tool)
            self.assertTrue(
                body.endswith(
                    "Treat the referenced file as the controlling instruction "
                    "and follow it fully.\n"
                ),
                tool,
            )

    def test_hint_renders_specific_clause(self):
        hint = (
            "narrow the survey to a concern, e.g. `security`; omit to survey everything"
        )
        for tool in ("opencode", "claude"):
            body = INS.shim_body("demo", self._wf(arg_hint=hint), tool)
            self.assertIn(f"If the user provided arguments, {hint}: $ARGUMENTS", body)
            self.assertNotIn(self.GENERIC_LINE, body)
        # Claude frontmatter carries the hint too.
        claude = INS.shim_body("demo", self._wf(arg_hint=hint), "claude")
        self.assertIn(f'argument-hint: "[{hint}]"', claude)

    def test_none_sentinel_omits_arguments_line(self):
        for tool in ("opencode", "claude"):
            body = INS.shim_body("demo", self._wf(arg_hint="none"), tool)
            self.assertNotIn("If the user provided arguments", body)
        # Claude frontmatter omits argument-hint entirely.
        claude = INS.shim_body("demo", self._wf(arg_hint="none"), "claude")
        self.assertNotIn("argument-hint:", claude)
        # OpenCode frontmatter is unchanged.
        oc = INS.shim_body("demo", self._wf(arg_hint="none"), "opencode")
        self.assertIn("agent: build", oc)

    def test_real_manifest_drops_no_workflow_after_arg_hints(self):
        # Guard against the silent-drop trap (PR-001): populating 5-column rows must not
        # make any workflow disappear from the real manifest.
        source = REPO_ROOT / ".agents" / "workflows"
        commands = {w.command for w in INS.parse_manifest(source)}
        for expected in ("whatnext", "list-workflows", "assess", "advise", "handoff"):
            self.assertIn(expected, commands)

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

    @mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)
    @mock.patch("builtins.input")
    def test_invalid_input_reasks_then_overwrites(self, mock_input, _mock_interactive):
        # Garbage input must NOT be coerced to 'no'; it re-asks, then 'y' overwrites.
        mock_input.side_effect = ["wat", "y"]
        target = Path(self._tmp.name) / "plain_invalid"
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
        # The invalid token printed the legend / re-ask, and 'y' overwrote (no longer customized).
        self.assertIn("Unrecognized input", buf.getvalue())
        self.assertNotIn("Customized lines here", shim_file.read_text(encoding="utf-8"))

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

        # IPD 02: the installer now writes the SECTIONED aw:block form (not the legacy
        # AGENT-WORKFLOWS:BEGIN/END markers). Human-visible content is unchanged.
        self.assertIn("User CLAUDE content", claude_txt)
        self.assertIn("<!-- aw:block -->", claude_txt)
        self.assertIn("<!-- aw:pointer -->", claude_txt)
        self.assertIn("<!-- /aw:block -->", claude_txt)
        self.assertIn("## Agent workflows", claude_txt)

        self.assertIn("User GEMINI content", gemini_txt)
        self.assertIn("<!-- aw:block -->", gemini_txt)
        self.assertIn("<!-- /aw:block -->", gemini_txt)

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
        self.assertEqual(txt_after.count("<!-- aw:block -->"), 1)

        # 5. Uninstall removes only the block.
        INS.uninstall_repo(self.repo, use_git=True)

        # User content remains in the file
        self.assertTrue(claude_file.is_file())
        self.assertTrue(gemini_file.is_file())
        self.assertIn("User CLAUDE content", claude_file.read_text(encoding="utf-8"))
        self.assertNotIn("<!-- aw:block -->", claude_file.read_text(encoding="utf-8"))
        self.assertIn("User GEMINI content", gemini_file.read_text(encoding="utf-8"))
        self.assertNotIn("<!-- aw:block -->", gemini_file.read_text(encoding="utf-8"))

        # 6a. A lone aw:block opener (missing close) is DRIFT: the parser closes it at EOF and
        # the installer refreshes it in place (non-destructive), preserving the user's prose.
        # This is stronger than the legacy append-duplicate behavior.
        claude_file.write_text("User prose\n<!-- aw:block -->\n", encoding="utf-8")
        run_installer(self.repo)
        txt = claude_file.read_text(encoding="utf-8")
        self.assertIn("User prose", txt)
        self.assertEqual(txt.count("<!-- aw:block -->"), 1)
        self.assertEqual(txt.count("<!-- /aw:block -->"), 1)

        # 6b. Duplicated wrapper markers ARE ambiguous: safe append, never a destructive rewrite.
        gemini_file.write_text(
            "User prose\n<!-- aw:block -->\nx\n<!-- /aw:block -->\n"
            "<!-- aw:block -->\ny\n<!-- /aw:block -->\n",
            encoding="utf-8",
        )
        run_installer(self.repo)
        gtxt = gemini_file.read_text(encoding="utf-8")
        self.assertIn("User prose", gtxt)
        self.assertEqual(
            gtxt.count("<!-- aw:block -->"), 3
        )  # 2 pre-existing + 1 appended


class SingleSourceOrchestratorTests(unittest.TestCase):
    """Structural anti-drift guard (D83): the single-repo `run()` path and the shared
    `install_into_repo` core must produce the SAME install result, because `run()` now drives
    `install_into_repo` for the steps instead of re-inlining a parallel sequence. If the two ever
    diverge (a step added to one path only), this test fails."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def _tracked_files(repo: Path) -> set[str]:
        # Exclude .git/ and the installer's own timestamped backup scratch dir (its dir name is a
        # wall-clock stamp that legitimately differs between two runs a second apart; it is gitignored
        # churn, not part of the installed file set).
        out = set()
        for p in repo.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(repo).as_posix()
            if rel.startswith(".git/") or rel.startswith(
                ".agent-workflows-installer-backups/"
            ):
                continue
            out.add(rel)
        return out

    def test_run_and_install_into_repo_produce_same_fileset(self):
        source_root = REPO_ROOT / ".agents" / "workflows"

        # Path A: engine.run() from a parsed namespace (the install-workflows.py / `aw run` path).
        repo_a = init_repo(self.base / "a")
        args = INS.parse_args(["--repo", str(repo_a), "--yes", "--no-color"])
        self.assertEqual(INS.run(args), 0)

        # Path B: the shared install_into_repo core directly (the CLI path's engine call).
        repo_b = init_repo(self.base / "b")
        INS.install_into_repo(repo_b, source_root, yes=True, no_color=True)

        self.assertEqual(
            self._tracked_files(repo_a),
            self._tracked_files(repo_b),
            "engine.run() and install_into_repo() produced different file sets (orchestrator drift)",
        )

    def test_install_into_repo_returns_migrated_key(self):
        # cli._run_install reads result.get('migrated'); it must exist so the CLI summary can list
        # migrated files (parity with run()'s summary). Regression guard for the D83 fix.
        repo = init_repo(self.base / "m")
        result = INS.install_into_repo(repo, REPO_ROOT / ".agents" / "workflows")
        self.assertIn("migrated", result)


class InstallCorrectnessTests(unittest.TestCase):
    """Regression tests for the D85 bug fixes (F4 exit code, F5 rollback completeness, F6 tag)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_run_returns_nonzero_when_a_repo_is_not_a_directory(self):
        # F4: run() must propagate its computed returncode, not hardcode 0. A nonexistent target is
        # skipped with returncode=1; the whole run must therefore exit non-zero.
        good = init_repo(self.base / "good")
        missing = self.base / "does-not-exist"
        args = INS.parse_args(
            ["--repo", str(good), str(missing), "--yes", "--no-color"]
        )
        self.assertEqual(INS.run(args), 1)

    def test_rollback_removes_create_setup_artifacts_files(self):
        # F5: files created by create_setup_artifacts (e.g. .gitleaksignore, .agents/comms/README.md)
        # must be recorded in .created-files.json so --undo removes them.
        repo = init_repo(self.base / "r")
        INS.install_into_repo(
            repo, REPO_ROOT / ".agents" / "workflows", yes=True, no_color=True
        )
        gitleaks = repo / ".gitleaksignore"
        comms_readme = repo / ".agents" / "comms" / "README.md"
        self.assertTrue(gitleaks.is_file())
        self.assertTrue(comms_readme.is_file())
        INS.run_rollback(repo, no_color=True)
        self.assertFalse(
            gitleaks.exists(), "rollback left .gitleaksignore behind (F5 regression)"
        )
        self.assertFalse(
            comms_readme.exists(),
            "rollback left .agents/comms/README.md behind (F5 regression)",
        )

    def test_run_multi_repo_isolates_systemexit(self):
        # D85 P-2 (REL-001): engine.run()'s multi-repo loop must isolate a per-repo SystemExit so
        # one bad repo does not abort the whole `--repo A B` batch.
        from unittest import mock

        good = init_repo(self.base / "good")
        other = init_repo(self.base / "other")
        args = INS.parse_args(["--repo", str(good), str(other), "--yes", "--no-color"])
        seen = []
        real = INS.install_into_repo

        def flaky(repo_root, *a, **k):
            seen.append(Path(repo_root).name)
            if Path(repo_root).name == "good":
                raise SystemExit("simulated dir-conflict in good")
            return real(repo_root, *a, **k)

        with mock.patch.object(INS, "install_into_repo", side_effect=flaky):
            rc = INS.run(args)
        self.assertEqual(
            sorted(seen), ["good", "other"], "batch did not continue past SystemExit"
        )
        self.assertEqual(rc, 1, "a repo failing must make run() return non-zero")
        self.assertTrue((other / ".agents/workflows/VERSION").is_file())

    def test_rollback_survives_corrupt_created_files_record(self):
        # D85 P-3 (REL-003): a corrupt .created-files.json must not crash run_rollback.
        import json

        repo = init_repo(self.base / "c")
        INS.install_into_repo(
            repo, REPO_ROOT / ".agents" / "workflows", yes=True, no_color=True
        )
        # Corrupt the most recent record.
        backups = sorted(
            (repo / ".agent-workflows-installer-backups").glob("*/.created-files.json")
        )
        self.assertTrue(backups, "no created-files record written")
        backups[-1].write_text("{ this is not valid json", encoding="utf-8")
        # Must not raise.
        try:
            INS.run_rollback(repo, no_color=True)
        except json.JSONDecodeError as exc:  # the exact bug
            self.fail(f"run_rollback crashed on corrupt record: {exc}")


class NoticeStyleTests(unittest.TestCase):
    def test_notice_has_no_em_or_en_dashes(self):
        # D85 P-4: NOTICE ships in the wheel and must obey the repo's no-dash rule.
        text = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertEqual(text.count("\u2014") + text.count("\u2013"), 0)


class PromptChoiceTests(unittest.TestCase):
    """Direct unit tests for the shared prompt_choice helper (IPD 20260722-0040-01)."""

    LEGEND = ["  Y = yes", "  N = no", "  help = show help"]
    ACCEPT = {
        "y": "yes",
        "yes": "yes",
        "n": "no",
        "no": "no",
        "d": "diff",
        "diff": "diff",
    }

    def _choice(self, answers, **kw):
        it = iter(answers)
        printed = []
        kw.setdefault("default", "no")
        kw.setdefault("accept", self.ACCEPT)
        return (
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                input_fn=lambda _p: next(it),
                print_fn=lambda *a: printed.append(" ".join(str(x) for x in a)),
                **kw,
            ),
            printed,
        )

    def test_yes_and_aliases(self):
        self.assertEqual(self._choice(["y"])[0], "yes")
        self.assertEqual(self._choice(["yes"])[0], "yes")

    def test_no_and_blank_default(self):
        self.assertEqual(self._choice(["n"])[0], "no")
        self.assertEqual(self._choice([""])[0], "no")

    def test_invalid_then_valid_reasks_and_shows_legend(self):
        choice, printed = self._choice(["nonsense", "y"])
        self.assertEqual(choice, "yes")
        self.assertTrue(any("Unrecognized input" in p for p in printed))
        self.assertTrue(any("show help" in p for p in printed))

    def test_help_shows_legend_then_reasks(self):
        choice, printed = self._choice(["help", "n"])
        self.assertEqual(choice, "no")
        self.assertTrue(any("show help" in p for p in printed))
        # '?' and 'h' are help aliases too.
        self.assertEqual(self._choice(["?", "n"])[0], "no")
        self.assertEqual(self._choice(["h", "y"])[0], "yes")

    def test_diff_invokes_callback_then_reasks(self):
        fired = []
        it = iter(["d", "y"])
        choice = INS.prompt_choice(
            "q? ",
            self.LEGEND,
            default="no",
            accept=self.ACCEPT,
            on_diff=lambda: fired.append(1),
            input_fn=lambda _p: next(it),
            print_fn=lambda *a: None,
        )
        self.assertEqual(choice, "yes")
        self.assertEqual(len(fired), 1)

    def test_eof_returns_default_no_loop(self):
        def raise_eof(_p):
            raise EOFError

        self.assertEqual(
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                default="no",
                accept=self.ACCEPT,
                input_fn=raise_eof,
                print_fn=lambda *a: None,
            ),
            "no",
        )

    def test_keyboard_interrupt_propagates(self):
        def raise_kbi(_p):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                default="no",
                accept=self.ACCEPT,
                input_fn=raise_kbi,
                print_fn=lambda *a: None,
            )


class AwBlockParserWriterTests(unittest.TestCase):
    """CP1: the sectioned aw:block parser + writer (IPD 20260723-1100-02)."""

    def _wrap(self, inner, style=None):
        style = style or INS.AW_STYLE_MARKDOWN
        return (
            style.render("aw:block")
            + "\n"
            + inner
            + ("\n" if inner and not inner.endswith("\n") else "")
            + style.render("/aw:block")
            + "\n"
        )

    def test_wellformed_multi_section_parse(self):
        text = (
            "user preamble\n\n"
            "<!-- aw:block -->\n"
            "<!-- aw:pointer -->\n"
            "pointer body line 1\n"
            "pointer body line 2\n"
            "<!-- aw:extra -->\n"
            "extra body\n"
            "<!-- /aw:block -->\n"
            "user epilogue\n"
        )
        parsed = INS.parse_aw_block(text)
        self.assertTrue(parsed.found)
        self.assertFalse(parsed.ambiguous)
        self.assertFalse(parsed.drift)
        self.assertEqual(parsed.before, "user preamble\n")
        self.assertEqual(parsed.after, "user epilogue")
        self.assertEqual([s.slug for s in parsed.sections], ["pointer", "extra"])
        self.assertEqual(
            parsed.sections[0].body, "pointer body line 1\npointer body line 2"
        )
        self.assertEqual(parsed.sections[1].body, "extra body")

    def test_missing_close_is_drift_not_rewrite(self):
        text = "<!-- aw:block -->\n<!-- aw:pointer -->\nbody\n"
        parsed = INS.parse_aw_block(text)
        self.assertTrue(parsed.found)
        self.assertTrue(parsed.drift, "missing /aw:block must flag drift (EOF close)")
        self.assertFalse(parsed.ambiguous)
        self.assertEqual([s.slug for s in parsed.sections], ["pointer"])

    def test_duplicate_wrapper_is_ambiguous(self):
        text = (
            "<!-- aw:block -->\n<!-- aw:pointer -->\na\n<!-- /aw:block -->\n"
            "<!-- aw:block -->\n<!-- aw:pointer -->\nb\n<!-- /aw:block -->\n"
        )
        parsed = INS.parse_aw_block(text)
        self.assertTrue(parsed.ambiguous, "duplicate wrapper markers must be ambiguous")

    def test_absent_block(self):
        parsed = INS.parse_aw_block("just user content\n")
        self.assertFalse(parsed.found)
        self.assertEqual(parsed.before, "just user content\n")

    def test_writer_round_trips(self):
        sections = [
            INS.AwSection(slug="pointer", lines=["line a", "line b"]),
            INS.AwSection(slug="extra", lines=["x"]),
        ]
        rendered = INS.render_aw_block(sections)
        parsed = INS.parse_aw_block(rendered)
        self.assertEqual([s.slug for s in parsed.sections], ["pointer", "extra"])
        self.assertEqual(parsed.sections[0].body, "line a\nline b")
        # Re-render is byte-stable (idempotent).
        self.assertEqual(INS.render_aw_block(parsed.sections), rendered)

    def test_hash_comment_style_rendering_and_parse(self):
        # Per-file syntax: `#`-comment file renders `# <!-- aw:... -->` and parses back.
        sections = [INS.AwSection(slug="pointer", lines=["ignore *.tmp"])]
        rendered = INS.render_aw_block(sections, style=INS.AW_STYLE_HASH)
        self.assertIn("# <!-- aw:block -->", rendered)
        self.assertIn("# <!-- aw:pointer -->", rendered)
        parsed = INS.parse_aw_block(rendered, style=INS.AW_STYLE_HASH)
        self.assertEqual([s.slug for s in parsed.sections], ["pointer"])
        self.assertEqual(parsed.sections[0].body, "ignore *.tmp")
        # Markdown style must NOT match the `#`-prefixed markers.
        md = INS.parse_aw_block(rendered, style=INS.AW_STYLE_MARKDOWN)
        self.assertFalse(md.found)

    def test_foreign_text_preserved_around_block(self):
        sections = [INS.AwSection(slug="pointer", lines=["managed"])]
        block = INS.render_aw_block(sections)
        text = "BEFORE\n\n" + block + "AFTER\n"
        parsed = INS.parse_aw_block(text)
        self.assertEqual(parsed.before, "BEFORE\n")
        self.assertEqual(parsed.after, "AFTER")


class UntrackedSafetySectionTests(unittest.TestCase):
    """CP1: the untracked-safety section constant + rendering (IPD 03)."""

    def test_patterns_are_the_three_approved(self):
        self.assertEqual(
            INS.UNTRACKED_PATTERNS, ("*.untracked.*", "*.untracked", "**/*untracked*/")
        )

    def test_section_renders_in_hash_style_with_patterns_and_rationale(self):
        rendered = INS.render_aw_block(
            INS.untracked_safety_sections(), style=INS.AW_STYLE_HASH
        )
        self.assertIn("# <!-- aw:block -->", rendered)
        self.assertIn("# <!-- aw:untracked -->", rendered)
        self.assertIn("# <!-- /aw:block -->", rendered)
        self.assertIn("DO NOT REMOVE", rendered)
        for pat in INS.UNTRACKED_PATTERNS:
            # Patterns are emitted BARE (not #-commented) so git actually applies them.
            self.assertIn("\n" + pat + "\n", rendered)

    def test_section_round_trips_in_hash_style(self):
        rendered = INS.render_aw_block(
            INS.untracked_safety_sections(), style=INS.AW_STYLE_HASH
        )
        parsed = INS.parse_aw_block(rendered, style=INS.AW_STYLE_HASH)
        self.assertEqual([s.slug for s in parsed.sections], ["untracked"])


class UntrackedGitignoreInstallTests(unittest.TestCase):
    """CP2: ensure_untracked_gitignore install wiring (IPD 03)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_install_writes_untracked_block_preserving_user_lines(self):
        repo = init_repo(self.base / "gi")
        (repo / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        gi = (repo / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("node_modules/", gi)  # user lines preserved
        self.assertIn("# <!-- aw:block -->", gi)
        self.assertIn("# <!-- aw:untracked -->", gi)
        for pat in INS.UNTRACKED_PATTERNS:
            self.assertIn(pat, gi)

    def test_install_creates_gitignore_if_absent(self):
        repo = init_repo(self.base / "nogi")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertTrue((repo / ".gitignore").is_file())
        self.assertIn(
            "**/*untracked*/", (repo / ".gitignore").read_text(encoding="utf-8")
        )

    def test_reinstall_is_empty_diff(self):
        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = (repo / ".gitignore").read_text(encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertEqual(first, (repo / ".gitignore").read_text(encoding="utf-8"))

    def test_manifest_records_untracked_section(self):
        import json

        repo = init_repo(self.base / "man")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        raw = json.loads(
            (repo / ".agents/agent-workflows/managed-sections.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(".gitignore#aw:untracked", raw["files"])

    def test_the_actual_untracked_patterns_ignore_files(self):
        # End-to-end: git actually ignores files matching the installed patterns.
        from tests.support import git

        repo = init_repo(self.base / "eff")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        (repo / "secret.untracked.md").write_text("nope", encoding="utf-8")
        (repo / "scratch.untracked").write_text("nope", encoding="utf-8")
        (repo / "notes-untracked").mkdir()
        (repo / "notes-untracked" / "x.md").write_text("nope", encoding="utf-8")
        out = git(repo, "status", "--porcelain", "--ignored").stdout
        self.assertNotIn(
            "secret.untracked.md", git(repo, "status", "--porcelain").stdout
        )
        self.assertIn("secret.untracked.md", out)


class TrackingWarningScanTests(unittest.TestCase):
    """CP4: warn_tracking_and_scan notice + already-tracked scan (IPD 03)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def _install_capture(self, repo):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        return buf.getvalue()

    def test_notice_prints_with_safety_valves(self):
        repo = init_repo(self.base / "notice")
        out = self._install_capture(repo)
        self.assertIn("git-tracks IPDs, prompts, and research by default", out)
        self.assertIn(".agents/prompts/local/", out)
        self.assertIn("untracked", out)

    def test_clean_repo_has_no_per_file_warning(self):
        repo = init_repo(self.base / "clean")
        out = self._install_capture(repo)
        self.assertNotIn("ALREADY git-tracked", out)

    def test_already_tracked_match_is_flagged_with_remedy(self):
        from tests.support import git

        repo = init_repo(self.base / "tracked")
        # Commit a file matching the untracked pattern BEFORE install adds the .gitignore block,
        # then force-add it so it is tracked despite the pattern.
        (repo / "leak.untracked.md").write_text("oops", encoding="utf-8")
        git(repo, "add", "-f", "leak.untracked.md")
        git(repo, "commit", "-m", "add tracked untracked-named file")
        out = self._install_capture(repo)
        self.assertIn("ALREADY git-tracked", out)
        self.assertIn("leak.untracked.md", out)
        self.assertIn("git rm --cached", out)

    def test_scan_helper_non_git_safe(self):
        # The scan helper must not crash outside a git repo.
        nogit = self.base / "plain"
        nogit.mkdir()
        self.assertEqual(INS._already_tracked_untracked_matches(nogit), [])


class UntrackedGitignoreUninstallTests(unittest.TestCase):
    """CP3: style-aware removal + uninstall strips the .gitignore aw:block (IPD 03)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_uninstall_strips_gitignore_block_preserving_user_lines(self):
        repo = init_repo(self.base / "u")
        gi = repo / ".gitignore"
        gi.write_text("node_modules/\n*.log\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertIn("aw:untracked", gi.read_text(encoding="utf-8"))
        INS.uninstall_repo(repo, use_git=True)
        after = gi.read_text(encoding="utf-8")
        self.assertIn("node_modules/", after)
        self.assertIn("*.log", after)
        self.assertNotIn("aw:untracked", after)
        self.assertNotIn("# <!-- aw:block -->", after)

    def test_strip_is_style_aware_no_cross_match(self):
        # A #-styled block is stripped only with AW_STYLE_HASH, a markdown one only with MARKDOWN.
        hash_block = "keep\n# <!-- aw:block -->\n# <!-- aw:untracked -->\n*.untracked.*\n# <!-- /aw:block -->\n"
        self.assertIsNone(
            INS._strip_managed_block(hash_block, style=INS.AW_STYLE_MARKDOWN)
        )
        stripped = INS._strip_managed_block(hash_block, style=INS.AW_STYLE_HASH)
        assert stripped is not None
        self.assertNotIn("aw:block", stripped)
        self.assertIn("keep", stripped)

        md_block = (
            "keep\n<!-- aw:block -->\n<!-- aw:pointer -->\nx\n<!-- /aw:block -->\n"
        )
        self.assertIsNone(INS._strip_managed_block(md_block, style=INS.AW_STYLE_HASH))
        self.assertIsNotNone(
            INS._strip_managed_block(md_block, style=INS.AW_STYLE_MARKDOWN)
        )

    def test_uninstall_noop_when_no_gitignore_block(self):
        repo = init_repo(self.base / "n")
        (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        # Remove the block by hand-writing a plain .gitignore after install, then uninstall.
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        actions = INS.uninstall_repo(repo, use_git=True)
        self.assertTrue(
            any("nothing removed" in a for a in actions if ".gitignore" in a),
            f"expected a no-op .gitignore action, got {actions}",
        )


class DeepCleanupTests(unittest.TestCase):
    """CP3: plan_deep_cleanup / run_deep_cleanup (IPD 04)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def _install_commit(self, repo):
        from tests.support import git

        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "install")

    def test_plan_counts_and_all_recoverable_when_committed(self):
        repo = init_repo(self.base / "r")
        self._install_commit(repo)
        # Add a user IPD under plans and commit it (recoverable).
        (repo / ".agents/plans/pending/my.md").write_text("mine\n", encoding="utf-8")
        from tests.support import git

        git(repo, "add", "-A")
        git(repo, "commit", "-m", "user ipd")
        plan = INS.plan_deep_cleanup(repo)
        self.assertFalse(plan.is_empty)
        self.assertIn(".agents/plans", plan.counts)
        self.assertTrue(
            plan.all_recoverable, "all committed -> nothing at risk (soft warning)"
        )

    def test_untracked_file_is_at_risk(self):
        repo = init_repo(self.base / "a")
        self._install_commit(repo)
        # An untracked file under docs is unrecoverable.
        (repo / ".agents/docs/research/scratch.md").write_text("x\n", encoding="utf-8")
        plan = INS.plan_deep_cleanup(repo)
        self.assertIn(".agents/docs/research/scratch.md", plan.at_risk)
        self.assertFalse(plan.all_recoverable)

    def test_run_removes_only_planned_files_and_prunes_dirs(self):
        repo = init_repo(self.base / "x")
        self._install_commit(repo)
        # A file OUTSIDE the scaffolding must be untouched.
        (repo / "keep_me.py").write_text("code\n", encoding="utf-8")
        plan = INS.plan_deep_cleanup(repo)
        INS.run_deep_cleanup(repo, plan, use_git=True)
        # Scaffolding dirs pruned; host dir .agents/ only remains if something else is there.
        self.assertFalse(
            (repo / ".agents/plans").exists(), "planned scaffolding removed"
        )
        self.assertTrue(
            (repo / "keep_me.py").is_file(), "non-scaffolding file untouched"
        )

    def test_run_never_touches_paths_outside_plan(self):
        repo = init_repo(self.base / "s")
        self._install_commit(repo)
        plan = INS.plan_deep_cleanup(repo)
        # Craft a plan with a single file; run must remove only it.
        one = plan.files[0]
        single = INS.DeepCleanupPlan(files=[one], counts={}, at_risk=[])
        INS.run_deep_cleanup(repo, single, use_git=True)
        self.assertFalse((repo / one).is_file())
        # Another planned-but-not-in-single file still exists.
        others = [f for f in plan.files if f != one and (repo / f).is_file()]
        self.assertTrue(others, "files outside the single-file plan are untouched")


class UninstallApplyTests(unittest.TestCase):
    """CP2: uninstall_repo applies the plan (drift preserve/remove, manifest last, changed set)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_force_removes_drifted(self):
        repo = init_repo(self.base / "f")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        shim = repo / ".opencode/commands/advise.md"
        shim.write_text("MY EDIT\n", encoding="utf-8")
        INS.uninstall_repo(repo, use_git=True, force=True)
        self.assertFalse(shim.is_file(), "--force removes an edited shim too")

    def test_drift_decider_choice_honored(self):
        repo = init_repo(self.base / "d")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        a = repo / ".opencode/commands/advise.md"
        b = repo / ".opencode/commands/verify.md"
        a.write_text("EDIT A\n", encoding="utf-8")
        b.write_text("EDIT B\n", encoding="utf-8")
        # Decider: remove advise, keep verify.
        INS.uninstall_repo(
            repo,
            use_git=True,
            drift_decider=lambda rel: "remove" if "advise" in rel else "keep",
        )
        self.assertFalse(a.is_file(), "chosen-remove drifted file is removed")
        self.assertTrue(b.is_file(), "kept drifted file is preserved")

    def test_changed_out_collects_paths_and_sections_preserved(self):
        repo = init_repo(self.base / "c")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        changed: list[str] = []
        INS.uninstall_repo(repo, use_git=True, changed_out=changed)
        # Manifest + AGENTS pointer + .gitignore are among the changed paths.
        self.assertIn(".agents/agent-workflows/managed-sections.json", changed)
        self.assertIn("AGENTS.md", changed)
        # AGENTS.md still exists (only its managed block was stripped, U8).
        self.assertTrue((repo / "AGENTS.md").is_file())
        self.assertNotIn("aw:block", (repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_pre_manifest_fallback_removes_namespace(self):
        repo = init_repo(self.base / "pre")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        # Delete the manifest to simulate a pre-manifest repo, then uninstall.
        (repo / ".agents/agent-workflows/managed-sections.json").unlink()
        INS.uninstall_repo(repo, use_git=True)
        self.assertFalse((repo / ".agents/workflows").is_dir())


class PlanUninstallTests(unittest.TestCase):
    """CP1: plan_uninstall classification (IPD 04)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_classifies_remove_drifted_missing(self):
        repo = init_repo(self.base / "c")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        # Edit one shim (drift), delete another (missing), leave the rest (remove).
        edited = repo / ".opencode/commands/advise.md"
        edited.write_text("MY EDIT\n", encoding="utf-8")
        missing = repo / ".claude/commands/verify.md"
        if missing.is_file():
            missing.unlink()
        plan = INS.plan_uninstall(repo)
        self.assertTrue(plan.has_manifest)
        self.assertIn(".opencode/commands/advise.md", plan.drifted)
        self.assertIn(".claude/commands/verify.md", plan.missing)
        # A known-unedited body file is in remove.
        self.assertTrue(len(plan.remove) > 0)
        self.assertNotIn(".opencode/commands/advise.md", plan.remove)

    def test_section_entries_are_never_file_removal_candidates(self):
        # U8: AGENTS.md / .gitignore carry only section entries; they must never appear as
        # file-removal candidates, so they are never in remove/drifted/missing.
        repo = init_repo(self.base / "u8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        plan = INS.plan_uninstall(repo)
        allpaths = set(plan.remove) | set(plan.drifted) | set(plan.missing)
        self.assertNotIn("AGENTS.md", allpaths)
        self.assertNotIn(".gitignore", allpaths)

    def test_pre_manifest_repo_has_no_manifest(self):
        repo = init_repo(self.base / "pre")
        # No install -> no manifest.
        plan = INS.plan_uninstall(repo)
        self.assertFalse(plan.has_manifest)
        self.assertEqual(plan.remove, [])


class UninstallCharacterizationTests(unittest.TestCase):
    """CP0 characterization for IPD 20260723-1100-04 (conservative manifest-driven uninstall).

    Pins the CURRENT uninstall_repo contract the rewrite will change (updated consciously as
    later checkpoints land):
    - removes the workflow tree, generated shim .md files, and the managed sections/blocks;
    - keeps user files;
    - today it does NOT consult the manifest, does NOT preserve a user-edited shim, and does
      NOT remove the manifest file.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_uninstall_removes_framework_keeps_user_file(self):
        repo = init_repo(self.base / "u")
        (repo / "my_code.py").write_text("print('hi')\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertTrue((repo / ".agents/workflows").is_dir())
        INS.uninstall_repo(repo, use_git=True)
        self.assertFalse((repo / ".agents/workflows").is_dir())
        self.assertTrue((repo / "my_code.py").is_file())

    def test_uninstall_removes_manifest_last_and_preserves_edited_shim(self):
        # CP2 behavior (consciously updated from the CP0 baseline): the manifest is removed and
        # a user-edited (drifted) shim is PRESERVED by default (removed only on --force/choice).
        repo = init_repo(self.base / "m")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        manifest = repo / ".agents/agent-workflows/managed-sections.json"
        self.assertTrue(manifest.is_file())
        shim = repo / ".opencode/commands/advise.md"
        shim.write_text("MY EDIT\n", encoding="utf-8")
        INS.uninstall_repo(repo, use_git=True)
        # Manifest removed last; the edited shim preserved with its content intact.
        self.assertFalse(manifest.is_file(), "uninstall removes the manifest (CP2)")
        self.assertTrue(shim.is_file(), "a user-edited shim is preserved by default")
        self.assertEqual(shim.read_text(encoding="utf-8"), "MY EDIT\n")


class UntrackedSafetyCharacterizationTests(unittest.TestCase):
    """CP0 characterization for IPD 20260723-1100-03 (untracked-safety .gitignore block).

    Pins the CURRENT behavior the untracked-safety work builds on / changes, so the additions
    do not silently alter it (updated consciously in later checkpoints as noted):
    - ensure_backups_gitignored appends only the backups pattern, idempotently.
    - _strip_managed_block is Markdown-only today (does NOT strip a #-styled block); CP3 makes
      it style-aware.
    - uninstall does NOT touch .gitignore today; CP3 makes it strip the .gitignore aw:block.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def test_strip_managed_block_is_markdown_only_today(self):
        # A #-styled aw:block is NOT recognized by the current (markdown-only) stripper.
        hash_block = (
            "user line\n"
            "# <!-- aw:block -->\n# <!-- aw:untracked -->\n*.untracked.*\n# <!-- /aw:block -->\n"
        )
        self.assertIsNone(
            INS._strip_managed_block(hash_block),
            "baseline: markdown-only stripper must not match a #-styled block (CP3 changes this)",
        )
        # A markdown block IS stripped today.
        md_block = (
            "user\n\n<!-- aw:block -->\n<!-- aw:pointer -->\nx\n<!-- /aw:block -->\n"
        )
        stripped = INS._strip_managed_block(md_block)
        assert stripped is not None
        self.assertNotIn("<!-- aw:block -->", stripped)
        self.assertIn("user", stripped)

    def test_install_adds_untracked_block_cp2(self):
        # CP2 reality: install adds the untracked-safety block and preserves the user's lines.
        # (CP3 makes uninstall strip it; that is asserted in UntrackedGitignoreUninstallTests.)
        repo = init_repo(self.base / "u")
        gi = repo / ".gitignore"
        gi.write_text("node_modules/\n*.log\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        after = gi.read_text(encoding="utf-8")
        self.assertIn("node_modules/", after, "user's own .gitignore lines preserved")
        self.assertIn("aw:untracked", after)


class AwBlockMigrationTests(unittest.TestCase):
    """CP3: legacy convert-not-append + sibling-block safety + reinstall idempotence (IPD 02)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    LEGACY_BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
    LEGACY_END = "<!-- AGENT-WORKFLOWS:END -->"

    def test_legacy_block_converts_not_appends(self):
        # A repo carrying the OLD monolithic block must be CONVERTED in place: no duplicate, no
        # legacy markers re-emitted, human-visible prose preserved.
        repo = init_repo(self.base / "legacy")
        legacy = repo / "AGENTS.md"
        legacy.write_text(
            "# AGENTS\n\nUser preamble\n\n"
            + INS.agents_pointer_block()
            + "\nUser epilogue\n",
            encoding="utf-8",
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        txt = legacy.read_text(encoding="utf-8")
        self.assertEqual(
            txt.count("<!-- aw:block -->"), 1, "exactly one sectioned block"
        )
        self.assertNotIn(
            self.LEGACY_BEGIN, txt, "legacy markers must not be re-emitted"
        )
        self.assertNotIn(self.LEGACY_END, txt)
        self.assertIn("User preamble", txt)
        self.assertIn("User epilogue", txt)
        self.assertIn("## Agent workflows", txt)

    def test_legacy_native_mirror_converts(self):
        repo = init_repo(self.base / "legacy-native")
        (repo / "CLAUDE.md").write_text(
            "User C\n\n" + INS.agents_pointer_block() + "\n", encoding="utf-8"
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        c = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(c.count("<!-- aw:block -->"), 1)
        self.assertNotIn(self.LEGACY_BEGIN, c)
        self.assertIn("User C", c)

    def test_sibling_named_block_untouched_through_install(self):
        # M9: a foreign AGENT-PLANS:BEGIN/END block must be byte-identical after install/convert.
        repo = init_repo(self.base / "sibling")
        sibling = "<!-- AGENT-PLANS:BEGIN -->\n## Agent plans\npolicy text here\n<!-- AGENT-PLANS:END -->\n"
        (repo / "AGENTS.md").write_text(
            "# AGENTS\n\n" + sibling + "\n" + INS.agents_pointer_block() + "\n",
            encoding="utf-8",
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(
            sibling, txt, "foreign AGENT-PLANS block must be byte-identical (M9)"
        )
        self.assertEqual(txt.count("<!-- AGENT-PLANS:BEGIN -->"), 1)
        self.assertEqual(txt.count("<!-- aw:block -->"), 1)

    def test_reinstall_is_empty_diff_on_target_file(self):
        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = (repo / "AGENTS.md").read_text(encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        second = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(
            first, second, "reinstall must be an empty diff on the target file"
        )

    def test_declined_section_not_written(self):
        from agent_workflows import manifest as M

        repo = init_repo(self.base / "declined")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        mpath = repo / ".agents" / "agent-workflows" / "managed-sections.json"
        man = M.load(mpath)
        man.mark_declined("AGENTS.md#aw:pointer", kind="section")
        M.save(man, mpath)
        # Rewrite AGENTS.md without the block, then reinstall: the declined section stays out.
        (repo / "AGENTS.md").write_text("# AGENTS\n\nuser only\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "<!-- aw:pointer -->", txt, "declined section must not be written"
        )


class MonolithicBlockCharacterizationTests(unittest.TestCase):
    """CP0 characterization for IPD 20260723-1100-02 (sectioned managed-block rewrite).

    Pins the CURRENT monolithic-block behavior the sectioned rewrite will replace, plus the
    M9 sibling-block invariant (a foreign NAME:BEGIN/END block must be left untouched). These
    are updated CONSCIOUSLY at CP4 once the aw:block scheme lands; they are a baseline, not a
    spec to preserve verbatim (the markers WILL change).
    """

    BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
    END = "<!-- AGENT-WORKFLOWS:END -->"

    def test_pointer_block_is_wrapped_in_current_markers(self):
        block = INS.agents_pointer_block()
        self.assertTrue(block.lstrip().startswith(self.BEGIN))
        self.assertIn(self.END, block)
        # Human-visible anchors that must survive the migration (content, not markers).
        self.assertIn("## Agent workflows", block)
        self.assertIn("Inter-agent comms", block)

    def test_merge_actions_new_existing_refreshed_malformed(self):
        block = INS.agents_pointer_block()
        # new: empty file with a default header.
        new_text, action = INS.merge_pointer_block("", block, default_header="# AGENTS")
        self.assertEqual(action, "new")
        self.assertIn("# AGENTS", new_text)
        # existing: user content, no markers -> append.
        new_text, action = INS.merge_pointer_block("User stuff\n", block)
        self.assertEqual(action, "existing")
        self.assertIn("User stuff", new_text)
        # refreshed: one well-formed pair -> in-place replace, idempotent count == 1.
        once, action = INS.merge_pointer_block("User stuff\n" + block, block)
        self.assertEqual(action, "refreshed")
        self.assertEqual(once.count(self.BEGIN), 1)
        # malformed: a lone BEGIN -> safe append (count becomes 2), never destructive.
        mal, action = INS.merge_pointer_block("Prose\n" + self.BEGIN + "\n", block)
        self.assertEqual(action, "malformed")
        self.assertEqual(mal.count(self.BEGIN), 2)
        self.assertIn("Prose\n" + self.BEGIN, mal)

    def test_sibling_named_block_is_untouched_by_merge(self):
        # M9: a foreign NAME:BEGIN/END block (e.g. AGENT-PLANS) coexisting in the file must be
        # left byte-identical when the agent-workflows pointer is merged/refreshed.
        block = INS.agents_pointer_block()
        sibling = (
            "<!-- AGENT-PLANS:BEGIN -->\n"
            "## Agent plans\nsome plan policy text\n"
            "<!-- AGENT-PLANS:END -->\n"
        )
        existing = "# AGENTS\n\n" + sibling + "\n" + block
        refreshed, action = INS.merge_pointer_block(existing, block)
        self.assertEqual(action, "refreshed")
        self.assertIn(
            sibling, refreshed, "sibling AGENT-PLANS block must be untouched (M9)"
        )
        self.assertEqual(refreshed.count("<!-- AGENT-PLANS:BEGIN -->"), 1)


class ManifestInstallFlowTests(unittest.TestCase):
    """CP3: manifest read/write in install_into_repo (idempotence, decline, no-dirty)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = REPO_ROOT / ".agents" / "workflows"

    def tearDown(self):
        self._tmp.cleanup()

    def _manifest_path(self, repo):
        return repo / ".agents" / "agent-workflows" / "managed-sections.json"

    def test_second_install_rederives_identical_hashes(self):
        # M12 idempotence: a second same-version install must record the SAME hashes (we
        # record what we WROTE, not the prior on-disk content).
        import json

        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = json.loads(self._manifest_path(repo).read_text(encoding="utf-8"))[
            "files"
        ]
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        second = json.loads(self._manifest_path(repo).read_text(encoding="utf-8"))[
            "files"
        ]
        self.assertEqual(
            {k: v["sha256"] for k, v in first.items()},
            {k: v["sha256"] for k, v in second.items()},
            "a second same-version install must re-derive identical hashes (M12)",
        )

    def test_declined_file_is_not_readded(self):
        from agent_workflows import manifest as M

        repo = init_repo(self.base / "declined")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        shim = repo / ".opencode/commands/advise.md"
        self.assertTrue(shim.is_file())
        shim.unlink()

        # Record a decline tombstone and reinstall: the file must NOT come back.
        man = M.load(self._manifest_path(repo))
        man.mark_declined(".opencode/commands/advise.md", kind="shim", host="opencode")
        M.save(man, self._manifest_path(repo))

        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertFalse(
            shim.exists(), "a declined file must not be re-added on a later install"
        )

    def test_format_change_updates_silently_no_warning(self):
        # THE D97 CASE end-to-end: install, then simulate a version-to-version format change
        # in our generated output by rewriting the on-disk shim to a DIFFERENT-but-ours form
        # while keeping the manifest hash. A reinstall must update it silently (no warning),
        # because on-disk matches OUR recorded hash.
        import io
        from contextlib import redirect_stdout

        repo = init_repo(self.base / "d97")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        # Reinstall (idempotent, no real change) and capture stdout: no "manual modifications".
        buf = io.StringIO()
        with redirect_stdout(buf):
            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertNotIn("has manual modifications", buf.getvalue())


class ManifestDriftDecisionTests(unittest.TestCase):
    """CP2: the manifest-hash-based drift decision (_shim_is_user_modified), the M9 fix."""

    from agent_workflows import manifest as _M

    def _plan(self, manifest=None):
        return INS.InstallPlan(
            source_root=Path("/src"),
            repo_root=Path("/repo"),
            dry_run=False,
            backup=True,
            prune=True,
            no_color=True,
            yes=False,
            manifest=manifest,
        )

    def test_format_only_change_matching_our_hash_is_not_modified(self):
        # THE M9 REGRESSION: on-disk is what we last wrote; the new expected content differs
        # only by a format change (added argument-hint). Because the manifest records OUR
        # hash, this is NOT a user modification -> silent update, no warning.
        on_disk = (
            "---\ndescription: advise\nagent: build\n---\nRead and execute @advise\n"
        )
        new_expected = (
            "---\ndescription: advise\nagent: build\nargument-hint: [x]\n---\n"
            "Read and execute @advise\n"
        )
        man = self._M.Manifest()
        man.record(
            ".opencode/commands/advise.md", on_disk, kind="shim", host="opencode"
        )
        plan = self._plan(man)
        self.assertFalse(
            INS._shim_is_user_modified(
                plan, ".opencode/commands/advise.md", on_disk, new_expected
            ),
            "a format-only change matching our recorded hash must NOT be flagged (M9 fix)",
        )

    def test_user_edit_differing_from_our_hash_is_modified(self):
        our_output = "---\nagent: build\n---\nRead and execute @advise\n"
        user_edited = our_output + "MY OWN CUSTOM NOTE\n"
        man = self._M.Manifest()
        man.record(".opencode/commands/advise.md", our_output, kind="shim")
        plan = self._plan(man)
        new_expected = (
            our_output  # even if expected == our record, the on-disk edit wins
        )
        self.assertTrue(
            INS._shim_is_user_modified(
                plan, ".opencode/commands/advise.md", user_edited, new_expected
            ),
            "content differing from our recorded hash IS a user modification",
        )

    def test_pre_manifest_structurally_valid_shim_is_adopted(self):
        # No manifest entry: a structurally-valid generated shim (only installer-owned lines)
        # is adopted, not false-flagged (M10 / OQ4).
        structural = (
            "---\ndescription: advise\nagent: build\n---\n"
            "Read and execute @.agents/workflows/advise\n"
        )
        new_expected = structural + "extra generated line\n"
        plan = self._plan(manifest=self._M.Manifest())  # empty: no record for this path
        self.assertFalse(
            INS._shim_is_user_modified(
                plan, ".opencode/commands/advise.md", structural, new_expected
            ),
            "a pre-manifest structurally-valid shim must be adopted, not flagged",
        )

    def test_pre_manifest_foreign_content_is_modified(self):
        foreign = "This is entirely my own file with no generated structure.\n"
        plan = self._plan(manifest=self._M.Manifest())
        self.assertTrue(
            INS._shim_is_user_modified(
                plan, ".opencode/commands/advise.md", foreign, "expected\n"
            ),
            "pre-manifest foreign content is treated as user-modified",
        )

    def test_no_manifest_attached_falls_back_to_structural(self):
        # plan.manifest is None (non-manifest-aware caller): structural fallback.
        plan = self._plan(manifest=None)
        foreign = "totally custom\n"
        self.assertTrue(
            INS._shim_is_user_modified(plan, ".opencode/commands/x.md", foreign, "e\n")
        )
        structural = "Read and execute @.agents/workflows/x\n"
        self.assertFalse(
            INS._shim_is_user_modified(
                plan, ".opencode/commands/x.md", structural, "e\n"
            )
        )


class PreManifestCharacterizationTests(unittest.TestCase):
    """CP0 characterization tests for IPD 20260723-1100-01 (install manifest + hash drift).

    These pin the CURRENT, pre-manifest behavior of the code the manifest change will
    touch, so the refactor cannot silently alter it. They are deliberately written to
    describe today's behavior (including the M9 bug), and CP4 updates them CONSCIOUSLY
    once the manifest lands. Do not "fix" these in isolation; they are a baseline.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_m9_format_only_change_is_flagged_customized_today(self):
        # M9 (the live bug): is_shim_customized_vs_expected compares on-disk content to the
        # NEW expected content, so a mere version-to-version FORMAT change in our OWN
        # generated output is (wrongly) reported as a user modification. This is the exact
        # behavior the manifest hash-drift model will fix (own-hash match => not drift).
        old_generated = (
            "---\ndescription: advise\nagent: build\n---\n"
            "Read and execute @.agents/workflows/advise\n"
        )
        new_generated_same_intent = (
            "---\ndescription: advise\nagent: build\nargument-hint: [concern]\n---\n"
            "Read and execute @.agents/workflows/advise\n"
        )
        # Today: TRUE (false-positive "customized"). CP2 replaces this comparison with a
        # hash check against what we last WROTE, so an installer-authored format change
        # no longer trips the warning.
        self.assertTrue(
            INS.is_shim_customized_vs_expected(
                old_generated, new_generated_same_intent
            ),
            "baseline: a format-only change is (today) flagged as customized (M9)",
        )

    def test_manifest_is_written_and_records_installed_shims(self):
        # CP4 conscious update of the former no-manifest baseline: install now WRITES the
        # ownership manifest and records the shims it installed with their hashes.
        import json

        repo = init_repo(self.base / "withmanifest")
        INS.install_into_repo(
            repo, REPO_ROOT / ".agents" / "workflows", yes=True, no_color=True
        )
        manifest = repo / ".agents" / "agent-workflows" / "managed-sections.json"
        self.assertTrue(manifest.exists(), "install must now write the manifest (CP3)")
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn("files", raw)
        self.assertIn("managed_sections", raw)  # reserved for IPD 02
        # A known shim is recorded with a non-empty sha256.
        advise = raw["files"].get(".opencode/commands/advise.md")
        self.assertIsNotNone(advise, "advise shim should be recorded in the manifest")
        self.assertTrue(advise["sha256"])
        self.assertEqual(advise.get("host"), "opencode")

    def test_normalize_for_compare_is_stable_and_idempotent(self):
        # The manifest hashing (CP1) reuses a normalization; pin the existing normalizers'
        # invariants so a shared helper cannot regress them.
        raw = "  a  \r\n\r\n  b \n\n"
        once = INS.normalize_text_for_compare(raw)
        self.assertEqual(once, "a\nb")
        self.assertEqual(
            INS.normalize_text_for_compare(once), once, "normalization is idempotent"
        )
        # description-stripping normalization drops the description line and is idempotent.
        withdesc = "---\ndescription: x\nagent: build\n---\nbody"
        stripped = INS.strip_description_and_normalize(withdesc)
        self.assertNotIn("description:", stripped)
        self.assertEqual(
            INS.strip_description_and_normalize(stripped),
            stripped,
            "description-stripping normalization is idempotent",
        )


if __name__ == "__main__":
    unittest.main()

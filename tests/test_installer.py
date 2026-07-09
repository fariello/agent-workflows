"""Self-tests for install-workflows.py.

End-to-end tests run the installer as a subprocess against throwaway git repos and assert
filesystem state (the real behavior, including git staging). Unit tests import the pure
functions. Stdlib unittest only.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.support import REPO_ROOT, INSTALLER, init_repo, run_installer, load_module

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
        mk = lambda c: INS.Workflow(command=c, body="b", description="d")
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
        before = sorted(p.relative_to(self.repo).as_posix()
                        for p in self.repo.rglob("*") if p.is_file())
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = sorted(p.relative_to(self.repo).as_posix()
                       for p in self.repo.rglob("*") if p.is_file())
        self.assertEqual(before, after, "re-run changed the set of files")

    def test_dry_run_makes_no_changes(self):
        proc = run_installer(self.repo, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.repo / ".agents/workflows/index.md").exists(),
                         "dry-run wrote files")
        self.assertFalse((self.repo / ".opencode/commands/assess.md").exists())

    def test_prune_removes_legacy_assess_shims(self):
        run_installer(self.repo)
        # Simulate an older install that had per-concern shims.
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text("---\ndescription: old\n---\nold\n", encoding="utf-8")
        legacy2 = self.repo / ".claude/commands/assess-prose.md"
        legacy2.write_text("---\ndescription: old\n---\nold\n", encoding="utf-8")
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(legacy.exists(), "stale assess-security shim not pruned")
        self.assertFalse(legacy2.exists(), "stale assess-prose shim not pruned")

    def test_no_prune_keeps_stale(self):
        run_installer(self.repo)
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text("old\n", encoding="utf-8")
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
            self.assertTrue(tool.stat().st_mode & 0o111, "tool script is not executable")
            indexed = git(self.repo, "ls-files", "-s",
                          ".agents/workflows/assess/tools/scan_secrets.py").stdout
            self.assertTrue(indexed.startswith("100755"), f"exec bit not in index: {indexed!r}")

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
        self.assertIn("auto-generated", (self.repo / ".opencode/commands/README.md").read_text(encoding="utf-8"))
        self.assertIn("Git Guidelines", (self.repo / "workflow-artifacts/README.md").read_text(encoding="utf-8"))

        # 2) Re-run preserves customized workflow-artifacts/README.md
        custom_path = self.repo / "workflow-artifacts/README.md"
        custom_content = "Custom user guidelines for this repo's execution trails."
        custom_path.write_text(custom_content, encoding="utf-8")

        # Run installer again
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(custom_path.read_text(encoding="utf-8"), custom_content, "Custom README content was overwritten!")

    def test_shim_readme_is_not_pruned(self):
        # Run installer to write shims
        run_installer(self.repo)
        shim_readme = self.repo / ".opencode/commands/README.md"
        self.assertTrue(shim_readme.is_file())

        # Run installer with prune=True
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(shim_readme.is_file(), "Shim README was pruned!")


if __name__ == "__main__":
    unittest.main()

"""Tests for the agent_workflows CLI verbs (IPD-2 Batch D).

Covers AC-4 (install all report + isolation), AC-5 (list/status states), AC-10 (setup
non-interactive), AC-14 (uninstall), AC-15 (NO_COLOR / non-TTY plain output). Runs the CLI
in-process via cli.main(argv), capturing stdout, with XDG_CONFIG_HOME pointed at a temp dir
so no real config is touched. Stdlib unittest only.
"""

from __future__ import annotations

import io
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.support import init_repo
from agent_workflows import cli, config as CFG

_ANSI = re.compile(r"\033\[[0-9;]*m")


def _run(argv):
    """Run the CLI capturing stdout; return (exit_code, stdout)."""

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class CliTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        # Force plain output for deterministic assertions unless a test overrides.
        self._old_nocolor = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        if self._old_nocolor is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = self._old_nocolor
        self._tmp.cleanup()

    def _repo(self, name):
        return init_repo(self.base / name)


class InstallVerbTests(CliTestBase):
    def test_install_single_repo_yes(self):
        repo = self._repo("solo")
        code, out = _run(["install", str(repo), "--yes"])
        self.assertEqual(code, 0, out)
        self.assertTrue((repo / ".agents/workflows/VERSION").is_file())
        self.assertIn("OK", out)

    def test_install_all_reports_and_isolates(self):
        # Two good repos + one config entry that does not exist -> reported, not fatal.
        a = self._repo("a")
        b = self._repo("b")
        cfg = CFG.default_config()
        cfg["repos"] = [str(a), str(b), str(self.base / "ghost")]
        CFG.save(cfg)
        code, out = _run(["install", "all", "--yes"])
        # a and b install; ghost is skipped (not a directory) -> nothing silent.
        self.assertIn("Summary", out)
        self.assertTrue((a / ".agents/workflows/VERSION").is_file())
        self.assertTrue((b / ".agents/workflows/VERSION").is_file())
        self.assertIn("SKIP", out)  # ghost reported

    def test_install_all_empty_config_warns(self):
        code, out = _run(["install", "all", "--yes"])
        self.assertEqual(code, 1)
        self.assertIn("No repos", out)

    def test_install_multiple_repos_yes(self):
        repo1 = self._repo("multi1")
        repo2 = self._repo("multi2")
        code, out = _run(["install", str(repo1), str(repo2), "--yes"])
        self.assertEqual(code, 0, out)
        self.assertTrue((repo1 / ".agents/workflows/VERSION").is_file())
        self.assertTrue((repo2 / ".agents/workflows/VERSION").is_file())
        self.assertIn("Target Repo:", out)


class ListStatusTests(CliTestBase):
    def test_status_shows_environment_readout(self):
        code, out = _run(["status"])
        self.assertEqual(code, 0, out)
        self.assertIn("Packaged version", out)
        self.assertIn("Python", out)
        self.assertIn("Config", out)

    def test_list_shows_states(self):
        repo = self._repo("r")
        _run(["install", str(repo), "--yes"])
        cfg = CFG.default_config()
        cfg["repos"] = [str(repo)]
        CFG.save(cfg)
        code, out = _run(["list"])
        self.assertEqual(code, 0, out)
        # `list` prints the resolved path (canonicalized; on Windows this expands 8.3
        # short names), so match on the stable basename, not the raw temp path string.
        self.assertIn(repo.name, out)
        # The installed repo carries a VERSION; its state is one of the known labels.
        self.assertTrue(any(s in out for s in ("CURRENT", "STALE", "AHEAD", "DEV")))

    def test_list_reports_not_installed(self):
        repo = self._repo("empty")  # a repo with no framework installed
        cfg = CFG.default_config()
        cfg["repos"] = [str(repo)]
        CFG.save(cfg)
        code, out = _run(["list"])
        self.assertIn("NOT-INSTALLED", out)


class SetupTests(CliTestBase):
    def test_setup_noninteractive_root_yes(self):
        # AC-10: setup --root <tmp> --yes writes config + installs discovered repos.
        a = self._repo("proj_a")
        b = self._repo("proj_b")
        code, out = _run(["setup", "--root", str(self.base), "--yes"])
        self.assertEqual(code, 0, out)
        self.assertTrue(CFG.config_path().is_file())
        self.assertTrue((a / ".agents/workflows/VERSION").is_file())
        self.assertTrue((b / ".agents/workflows/VERSION").is_file())
        cfg = CFG.load()
        # Config stores paths with forward slashes for portability; compare by expanding
        # each stored root back to a Path (separator-independent) rather than string-eq.
        expanded = [CFG.expand_path(r) for r in cfg["search_roots"]]
        self.assertIn(self.base, expanded)

    def test_setup_skips_submodule(self):
        # A submodule under the root must not be installed into.
        _ = self._repo("app")
        lib = init_repo(self.base / "lib")
        (self.base / ".gitmodules").write_text(
            '[submodule "lib"]\n\tpath = lib\n\turl = https://example/lib.git\n',
            encoding="utf-8",
        )
        # Note: base itself is not a repo; discovery scans its children.
        code, out = _run(["setup", "--root", str(self.base), "--yes"])
        self.assertIn("submodule", out)
        self.assertFalse((lib / ".agents/workflows/VERSION").is_file())


class UninstallTests(CliTestBase):
    def test_uninstall_removes_framework_keeps_user_content(self):
        repo = self._repo("r")
        _run(["install", str(repo), "--yes"])
        (repo / "my_code.py").write_text("print('mine')\n", encoding="utf-8")
        code, out = _run(["uninstall", str(repo), "--yes"])
        self.assertEqual(code, 0, out)
        self.assertFalse((repo / ".agents/workflows").exists())
        self.assertFalse((repo / ".opencode/commands").exists())
        self.assertTrue((repo / "my_code.py").is_file())  # user content untouched

    def test_uninstall_removes_config_entry(self):
        repo = self._repo("r")
        _run(["install", str(repo), "--yes"])
        cfg = CFG.default_config()
        cfg["repos"] = [str(repo)]
        CFG.save(cfg)
        _run(["uninstall", str(repo), "--yes"])
        self.assertEqual(CFG.load()["repos"], [])

    def test_uninstall_not_installed_warns(self):
        repo = self._repo("bare")
        code, out = _run(["uninstall", str(repo), "--yes"])
        self.assertEqual(code, 1)
        self.assertIn("not installed", out)


class AccessibilityTests(CliTestBase):
    def test_no_color_output_has_no_ansi_and_keeps_status_words(self):
        # AC-15: NO_COLOR (set in setUp) => no escape sequences, status words present.
        repo = self._repo("r")
        code, out = _run(["install", str(repo), "--yes"])
        self.assertNotRegex(out, _ANSI)
        self.assertIn("OK", out)  # the status WORD survives monochrome

    def test_no_color_flag_forces_plain_even_if_env_absent(self):
        os.environ.pop("NO_COLOR", None)  # remove the setUp default
        repo = self._repo("r2")
        code, out = _run(["install", str(repo), "--no-color", "--yes"])
        self.assertNotRegex(out, _ANSI)
        self.assertIn("OK", out)


if __name__ == "__main__":
    unittest.main()

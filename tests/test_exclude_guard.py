"""Tests for the never-install exclude guard (clianx-01 E-03). Stdlib unittest only."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import cli as CLI
from agent_workflows import config as CFG
from agent_workflows.term import Term


class _Args:
    def __init__(self, yes=False):
        self.yes = yes


class ExcludeGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._prev_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        # A repo path we will exclude.
        self.repo = Path(self._tmp.name) / "legacy-repo"
        self.repo.mkdir()
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "exclude", [str(self.repo.resolve())])
        CFG.save(cfg)
        self.term = Term(color=False)

    def tearDown(self):
        if self._prev_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._prev_xdg
        self._tmp.cleanup()

    def test_non_excluded_repo_proceeds(self):
        other = Path(self._tmp.name) / "fine-repo"
        other.mkdir()
        self.assertEqual(
            CLI._exclude_guard(self.term, other, _Args(yes=False)), "proceed"
        )

    def test_yes_on_excluded_repo_skips_failsafe_no_config_change(self):
        # --yes MUST NOT silently install into an excluded repo; it skips, config intact.
        with mock.patch("builtins.input") as inp:
            result = CLI._exclude_guard(self.term, self.repo, _Args(yes=True))
        self.assertEqual(result, "skip")
        inp.assert_not_called()  # never prompted
        self.assertIn(str(self.repo.resolve()), CFG.load()["repos"]["exclude"])

    def test_non_interactive_excluded_repo_skips_failsafe(self):
        with mock.patch("sys.stdin.isatty", return_value=False):
            with mock.patch("builtins.input") as inp:
                result = CLI._exclude_guard(self.term, self.repo, _Args(yes=False))
        self.assertEqual(result, "skip")
        inp.assert_not_called()
        self.assertIn(str(self.repo.resolve()), CFG.load()["repos"]["exclude"])

    def test_interactive_decline_changes_nothing(self):
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", return_value="n"):
                result = CLI._exclude_guard(self.term, self.repo, _Args(yes=False))
        self.assertEqual(result, "skip")
        self.assertIn(str(self.repo.resolve()), CFG.load()["repos"]["exclude"])

    def test_interactive_continue_default_yes_keeps_exclude_when_unexclude_declined(
        self,
    ):
        # Continue prompt defaults YES on empty input; unexclude declined -> entry stays.
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", side_effect=["", "n"]):
                result = CLI._exclude_guard(self.term, self.repo, _Args(yes=False))
        self.assertEqual(result, "proceed")
        self.assertIn(str(self.repo.resolve()), CFG.load()["repos"]["exclude"])

    def test_interactive_continue_and_unexclude_removes_entry(self):
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("builtins.input", side_effect=["y", "y"]):
                result = CLI._exclude_guard(self.term, self.repo, _Args(yes=False))
        self.assertEqual(result, "proceed")
        self.assertNotIn(str(self.repo.resolve()), CFG.load()["repos"]["exclude"])

    def test_exclude_remove_matches_glob_entry(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "exclude", ["*/legacy-repo"])
        CFG.save(cfg)
        CLI._exclude_remove(CFG.load(), self.repo)
        self.assertEqual(CFG.load()["repos"]["exclude"], [])


class ConfigExcludeVerbTests(unittest.TestCase):
    """clianx-01 E-04: aw config exclude {add,list,rm} round-trip."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._prev_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        if self._prev_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._prev_xdg
        self._tmp.cleanup()

    def test_add_list_rm_roundtrip(self):
        term = Term(color=False)

        add_args = mock.Mock(exclude_command="add", path="~/src/legacy-repo")
        self.assertEqual(CLI._run_config_exclude(add_args, term), 0)
        self.assertIn("~/src/legacy-repo", CFG.load()["repos"]["exclude"])

        # list returns 0 and does not mutate.
        list_args = mock.Mock(exclude_command="list")
        self.assertEqual(CLI._run_config_exclude(list_args, term), 0)
        self.assertIn("~/src/legacy-repo", CFG.load()["repos"]["exclude"])

        rm_args = mock.Mock(exclude_command="rm", path="~/src/legacy-repo")
        self.assertEqual(CLI._run_config_exclude(rm_args, term), 0)
        self.assertNotIn("~/src/legacy-repo", CFG.load()["repos"]["exclude"])

    def test_rm_nonmatch_returns_nonzero(self):
        term = Term(color=False)
        rm_args = mock.Mock(exclude_command="rm", path="~/nope")
        self.assertEqual(CLI._run_config_exclude(rm_args, term), 1)

    def test_add_glob_entry(self):
        term = Term(color=False)
        add_args = mock.Mock(exclude_command="add", path="*/vendored-tool")
        self.assertEqual(CLI._run_config_exclude(add_args, term), 0)
        self.assertIn("*/vendored-tool", CFG.load()["repos"]["exclude"])


if __name__ == "__main__":
    unittest.main()

"""Tests for agent_workflows.config (IPD-2 Batch C; AC-3, R-5). Stdlib unittest only."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from agent_workflows import config as CFG


class ConfigPathTests(unittest.TestCase):
    def test_honors_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["XDG_CONFIG_HOME"] = d
            try:
                self.assertEqual(CFG.config_dir(), Path(d) / "agent-workflows")
                self.assertEqual(
                    CFG.config_path(), Path(d) / "agent-workflows" / "config.json"
                )
            finally:
                del os.environ["XDG_CONFIG_HOME"]

    def test_falls_back_to_home_config_when_xdg_unset(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        expected = Path.home() / ".config" / "agent-workflows"
        self.assertEqual(CFG.config_dir(), expected)

    def test_never_directly_under_home(self):
        # The config dir must be nested under .config/agent-workflows, never ~/ itself.
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.assertNotEqual(CFG.config_dir(), Path.home())
        self.assertEqual(CFG.config_dir().name, "agent-workflows")


class SaveLoadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self._tmp.cleanup()

    def test_save_writes_to_xdg_dir_and_roundtrips(self):
        cfg = CFG.default_config()
        cfg["search_roots"] = ["~/src"]
        cfg["repos"] = ["~/src/foo"]
        cfg["ignore"] = ["*/vendor/*"]
        path = CFG.save(cfg)
        self.assertTrue(path.is_file())
        self.assertTrue(str(path).startswith(self._tmp.name))
        loaded = CFG.load()
        self.assertEqual(loaded["search_roots"], ["~/src"])
        self.assertEqual(loaded["repos"], ["~/src/foo"])
        self.assertEqual(loaded["ignore"], ["*/vendor/*"])
        self.assertEqual(loaded["config_version"], CFG.CONFIG_VERSION)

    def test_load_missing_returns_default(self):
        self.assertEqual(CFG.load(), CFG.default_config())

    def test_load_corrupt_returns_default(self):
        p = CFG.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(CFG.load(), CFG.default_config())

    def test_no_pollution_directly_under_home(self):
        # With XDG pointed at a temp dir, saving must not write anything at ~/.
        before = set(os.listdir(Path.home())) if Path.home().is_dir() else set()
        CFG.save(CFG.default_config())
        after = set(os.listdir(Path.home())) if Path.home().is_dir() else set()
        self.assertEqual(before, after, "config save polluted the home directory")

    def test_drops_unknown_and_sensitive_keys(self):
        # R-5: only the allowlisted keys are persisted; a stray "token" is dropped.
        p = CFG.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {
                    "config_version": 1,
                    "search_roots": ["~/src"],
                    "token": "SECRET-should-not-persist",
                    "password": "nope",
                    "defaults": {"backup": True, "prune": False, "evil": "x"},
                }
            ),
            encoding="utf-8",
        )
        loaded = CFG.load()
        self.assertNotIn("token", loaded)
        self.assertNotIn("password", loaded)
        self.assertNotIn("evil", loaded["defaults"])
        self.assertEqual(loaded["defaults"], {"backup": True, "prune": False})

        # And a re-save persists only the allowlist.
        CFG.save(loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertEqual(set(on_disk.keys()), CFG.default_config().keys() | set())
        self.assertNotIn("token", on_disk)

    def test_is_configured(self):
        self.assertFalse(CFG.is_configured())
        cfg = CFG.default_config()
        cfg["search_roots"] = ["~/src"]
        CFG.save(cfg)
        self.assertTrue(CFG.is_configured())


class PathExpansionTests(unittest.TestCase):
    def test_expand_path_tilde(self):
        self.assertEqual(CFG.expand_path("~/x"), Path.home() / "x")

    def test_expand_path_env_var(self):
        os.environ["AW_TEST_VAR"] = "/somewhere"
        try:
            self.assertEqual(CFG.expand_path("$AW_TEST_VAR/x"), Path("/somewhere/x"))
        finally:
            del os.environ["AW_TEST_VAR"]

    def test_preserve_home_roundtrip(self):
        # A path under home stores as ~-relative; expansion restores it.
        p = Path.home() / "projects" / "demo"
        stored = CFG._preserve_home(str(p))
        self.assertTrue(stored.startswith("~"))
        self.assertEqual(CFG.expand_path(stored), p)


if __name__ == "__main__":
    unittest.main()

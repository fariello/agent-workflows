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

    def test_exclude_roundtrips_and_expands(self):
        # E-01: the exclude blocklist round-trips load/save (home-preserved), unknown keys
        # still stripped, and expanded_excludes returns expanded strings (paths AND globs).
        cfg = CFG.default_config()
        cfg["exclude"] = ["~/src/legacy-repo", "*/never-install/*"]
        cfg["token"] = "SECRET-should-not-persist"  # unknown -> must be dropped
        CFG.save(cfg)
        loaded = CFG.load()
        self.assertEqual(loaded["exclude"], ["~/src/legacy-repo", "*/never-install/*"])
        self.assertNotIn("token", loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertIn("exclude", on_disk)
        self.assertNotIn("token", on_disk)

        expanded = CFG.expanded_excludes(loaded)
        self.assertEqual(
            expanded,
            [str(Path.home() / "src" / "legacy-repo"), "*/never-install/*"],
        )
        # An absolute path entry expands to itself; a default config has no excludes.
        self.assertEqual(CFG.expanded_excludes(CFG.default_config()), [])

    def test_exclude_defaults_empty(self):
        self.assertEqual(CFG.default_config()["exclude"], [])
        self.assertEqual(CFG.load()["exclude"], [])


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


class ConfigSchemaAndGetSetTests(unittest.TestCase):
    def test_config_schema_contains_all_allowed_keys(self):
        for k in (
            "search_roots",
            "repos",
            "exclude",
            "ignore",
            "defaults.backup",
            "defaults.prune",
            "aw_home",
            "config_version",
        ):
            self.assertIn(k, CFG.CONFIG_SCHEMA)

    def test_get_config_value_top_level_and_dotted(self):
        cfg = CFG.default_config()
        cfg["search_roots"] = ["~/src"]
        cfg["defaults"] = {"backup": False, "prune": True}

        k, v = CFG.get_config_value("search_roots", cfg)
        self.assertEqual(k, "search_roots")
        self.assertEqual(v, ["~/src"])

        k, v = CFG.get_config_value("defaults.backup", cfg)
        self.assertEqual(k, "defaults.backup")
        self.assertFalse(v)

        k, v = CFG.get_config_value("backup", cfg)
        self.assertEqual(k, "defaults.backup")
        self.assertFalse(v)

        k, v = CFG.get_config_value("prune", cfg)
        self.assertEqual(k, "defaults.prune")
        self.assertTrue(v)

    def test_get_config_value_unknown_raises(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.get_config_value("nonexistent_key")

    def test_set_config_value_bool_coercion(self):
        cfg = CFG.default_config()
        for t_val in ("true", "1", "yes", "on", "t", "y", True):
            cfg, k, v = CFG.set_config_value(
                "defaults.backup", t_val, cfg=cfg, auto_save=False
            )
            self.assertEqual(k, "defaults.backup")
            self.assertTrue(v)
            self.assertTrue(cfg["defaults"]["backup"])

        for f_val in ("false", "0", "no", "off", "f", "n", False):
            cfg, k, v = CFG.set_config_value(
                "defaults.backup", f_val, cfg=cfg, auto_save=False
            )
            self.assertEqual(k, "defaults.backup")
            self.assertFalse(v)
            self.assertFalse(cfg["defaults"]["backup"])

    def test_set_config_value_invalid_bool_raises(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value("defaults.backup", "invalid_bool", auto_save=False)

    def test_set_config_value_list_and_paths(self):
        cfg = CFG.default_config()
        cfg, k, v = CFG.set_config_value(
            "search_roots", "~/src, ~/work", cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "search_roots")
        self.assertEqual(v, ["~/src", "~/work"])

        cfg, k, v = CFG.set_config_value(
            "search_roots", '["~/projects"]', cfg=cfg, auto_save=False
        )
        self.assertEqual(v, ["~/projects"])

    def test_set_config_value_read_only_raises(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value("config_version", 2, auto_save=False)

    def test_set_config_value_aw_home(self):
        cfg = CFG.default_config()
        cfg, k, v = CFG.set_config_value(
            "aw_home", "~/toolkit", cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "aw_home")
        self.assertEqual(v, "~/toolkit")

        cfg, k, v = CFG.set_config_value("aw_home", "", cfg=cfg, auto_save=False)
        self.assertIsNone(v)
        self.assertNotIn("aw_home", cfg)

    def test_parse_set_args_syntax_variants(self):
        var, val = CFG.parse_set_args(["defaults.backup", "false"])
        self.assertEqual((var, val), ("defaults.backup", "false"))

        var, val = CFG.parse_set_args(["defaults.backup", "=", "false"])
        self.assertEqual((var, val), ("defaults.backup", "false"))

        var, val = CFG.parse_set_args(["defaults.backup", "to", "false"])
        self.assertEqual((var, val), ("defaults.backup", "false"))

        var, val = CFG.parse_set_args(["defaults.backup=false"])
        self.assertEqual((var, val), ("defaults.backup", "false"))

        var, val = CFG.parse_set_args(["search_roots", "~/src,", "~/work"])
        self.assertEqual((var, val), ("search_roots", "~/src, ~/work"))

    def test_parse_set_args_error_cases(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args([])

        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args(["defaults.backup"])

        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args(["defaults.backup", "="])


class ConfigCliCommandTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self._tmp.cleanup()

    def test_cli_config_show_and_json(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "show"])
        self.assertEqual(rc, 0)
        self.assertIn("agent-workflows configuration", out.getvalue())
        self.assertIn("defaults.backup", out.getvalue())

        out_json = io.StringIO()
        with redirect_stdout(out_json):
            rc = cli.main(["config", "show", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out_json.getvalue())
        self.assertIn("config_file", data)
        self.assertIn("config", data)

    def test_cli_config_get_and_set_roundtrip(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        # Set value with 'to'
        out_set = io.StringIO()
        with redirect_stdout(out_set):
            rc = cli.main(["config", "set", "defaults.backup", "to", "false"])
        self.assertEqual(rc, 0)
        self.assertIn("defaults.backup = False", out_set.getvalue())

        # Get value
        out_get = io.StringIO()
        with redirect_stdout(out_get):
            rc = cli.main(["config", "get", "defaults.backup"])
        self.assertEqual(rc, 0)
        self.assertEqual(out_get.getvalue().strip(), "false")

        # Get value with --json
        out_get_json = io.StringIO()
        with redirect_stdout(out_get_json):
            rc = cli.main(["config", "get", "defaults.backup", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out_get_json.getvalue())
        self.assertEqual(data, {"defaults.backup": False})

    def test_cli_config_set_errors(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "set", "invalid_key", "foo"])
        self.assertEqual(rc, 2)
        self.assertIn("FAIL", out.getvalue())


if __name__ == "__main__":
    unittest.main()

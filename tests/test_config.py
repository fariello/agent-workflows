"""Tests for agent_workflows.config (IPD-2 Batch C; AC-3, R-5). Stdlib unittest only."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import config as CFG


class ConfigPathTests(unittest.TestCase):
    def test_config_path_resolution(self):
        # 1. Honors XDG_CONFIG_HOME
        with tempfile.TemporaryDirectory() as d:
            os.environ["XDG_CONFIG_HOME"] = d
            try:
                self.assertEqual(CFG.config_dir(), Path(d) / "agent-workflows")
                self.assertEqual(
                    CFG.config_path(), Path(d) / "agent-workflows" / "config.json"
                )
            finally:
                del os.environ["XDG_CONFIG_HOME"]

        # 2. Falls back to home config when XDG unset
        os.environ.pop("XDG_CONFIG_HOME", None)
        expected = Path.home() / ".config" / "agent-workflows"
        self.assertEqual(CFG.config_dir(), expected)

        # 3. Never directly under home
        self.assertNotEqual(CFG.config_dir(), Path.home())
        self.assertEqual(CFG.config_dir().name, "agent-workflows")


class SaveLoadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self._tmp.cleanup()

    def test_save_load_roundtrip_and_defaults(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        CFG.set_repo_setting(cfg, "installed", ["~/src/foo"])
        CFG.set_repo_setting(cfg, "ignore", ["*/vendor/*"])
        path = CFG.save(cfg)
        self.assertTrue(path.is_file())
        self.assertTrue(str(path).startswith(self._tmp.name))
        loaded = CFG.load()
        self.assertEqual(loaded["repos"]["search"], ["~/src"])
        self.assertEqual(loaded["repos"]["installed"], ["~/src/foo"])
        self.assertEqual(loaded["repos"]["ignore"], ["*/vendor/*"])
        self.assertEqual(loaded["config_version"], CFG.CONFIG_VERSION)

        # Load missing returns default
        with tempfile.TemporaryDirectory() as empty_d:
            os.environ["XDG_CONFIG_HOME"] = empty_d
            self.assertEqual(CFG.load(), CFG.default_config())
            os.environ["XDG_CONFIG_HOME"] = self._tmp.name

        # Load corrupt returns default
        p = CFG.config_path()
        p.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(CFG.load(), CFG.default_config())

        # Drops unknown and sensitive keys
        p.write_text(
            json.dumps(
                {
                    "config_version": 2,
                    "repos": {"search": ["~/src"]},
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
        CFG.save(loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertEqual(set(on_disk.keys()), CFG.default_config().keys() | set())
        self.assertNotIn("token", on_disk)

        # No pollution directly under home
        before = set(os.listdir(Path.home())) if Path.home().is_dir() else set()
        CFG.save(CFG.default_config())
        after = set(os.listdir(Path.home())) if Path.home().is_dir() else set()
        self.assertEqual(before, after, "config save polluted the home directory")

    def test_is_configured(self):
        self.assertFalse(CFG.is_configured())

        # False for default nested config
        CFG.save(CFG.default_config())
        self.assertTrue(CFG.config_path().is_file())
        self.assertFalse(CFG.is_configured())

        # True for search configured
        cfg = CFG.load()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        CFG.save(cfg)
        self.assertTrue(CFG.is_configured())

        # True for installed only
        cfg2 = CFG.default_config()
        CFG.set_repo_setting(cfg2, "installed", ["~/src/foo"])
        CFG.save(cfg2)
        self.assertTrue(CFG.is_configured())

    def test_exclude_config(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "exclude", ["~/src/legacy-repo", "*/never-install/*"])
        cfg["token"] = "SECRET-should-not-persist"
        CFG.save(cfg)
        loaded = CFG.load()
        self.assertEqual(
            loaded["repos"]["exclude"], ["~/src/legacy-repo", "*/never-install/*"]
        )
        self.assertNotIn("token", loaded)

        expanded = CFG.expanded_excludes(loaded)
        self.assertEqual(
            expanded, [str(Path.home() / "src" / "legacy-repo"), "*/never-install/*"]
        )
        self.assertEqual(CFG.expanded_excludes(CFG.default_config()), [])
        self.assertEqual(CFG.default_config()["repos"]["exclude"], [])
        self.assertEqual(
            CFG.load()["repos"]["exclude"], ["~/src/legacy-repo", "*/never-install/*"]
        )


class PathExpansionTests(unittest.TestCase):
    def test_path_expansion(self):
        self.assertEqual(CFG.expand_path("~/x"), Path.home() / "x")

        os.environ["AW_TEST_VAR"] = "/somewhere"
        try:
            self.assertEqual(CFG.expand_path("$AW_TEST_VAR/x"), Path("/somewhere/x"))
        finally:
            del os.environ["AW_TEST_VAR"]

        p = Path.home() / "projects" / "demo"
        stored = CFG._preserve_home(str(p))
        self.assertTrue(stored.startswith("~"))
        self.assertEqual(CFG.expand_path(stored), p)


class ConfigSchemaAndGetSetTests(unittest.TestCase):
    def test_config_schema_and_get(self):
        for k in (
            "repos",
            "repos.search",
            "repos.installed",
            "repos.exclude",
            "repos.ignore",
            "defaults",
            "defaults.backup",
            "defaults.prune",
            "aw_home",
            "config_version",
        ):
            self.assertIn(k, CFG.CONFIG_SCHEMA)

        for k in ("search_roots", "exclude", "ignore"):
            self.assertNotIn(k, CFG.CONFIG_SCHEMA)
        self.assertEqual(CFG.CONFIG_SCHEMA["repos"].type_name, "dict")

        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        cfg["defaults"] = {"backup": False, "prune": True}

        k, v = CFG.get_config_value("repos.search", cfg)
        self.assertEqual((k, v), ("repos.search", ["~/src"]))
        k, v = CFG.get_config_value("repos", cfg)
        self.assertEqual((k, v["search"]), ("repos", ["~/src"]))
        k, v = CFG.get_config_value("defaults.backup", cfg)
        self.assertEqual((k, v), ("defaults.backup", False))
        k, v = CFG.get_config_value("backup", cfg)
        self.assertEqual((k, v), ("defaults.backup", False))
        k, v = CFG.get_config_value("prune", cfg)
        self.assertEqual((k, v), ("defaults.prune", True))

        with self.assertRaises(CFG.ConfigError):
            CFG.get_config_value("nonexistent_key")

    def test_set_config_values(self):
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

        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value("defaults.backup", "invalid_bool", auto_save=False)

        cfg, k, v = CFG.set_config_value(
            "repos.search", "~/src, ~/work", cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "repos.search")
        self.assertEqual(v, ["~/src", "~/work"])

        cfg, k, v = CFG.set_config_value(
            "repos.search", '["~/projects"]', cfg=cfg, auto_save=False
        )
        self.assertEqual(v, ["~/projects"])

        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value("config_version", 2, auto_save=False)

        cfg, k, v = CFG.set_config_value(
            "aw_home", "~/toolkit", cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "aw_home")
        self.assertEqual(v, "~/toolkit")
        cfg, k, v = CFG.set_config_value("aw_home", "", cfg=cfg, auto_save=False)
        self.assertIsNone(v)
        self.assertNotIn("aw_home", cfg)

    def test_parse_args_and_add_remove(self):
        # parse_set_args variants
        for args in (
            ["defaults.backup", "false"],
            ["defaults.backup", "=", "false"],
            ["defaults.backup", "to", "false"],
            ["defaults.backup=false"],
        ):
            self.assertEqual(CFG.parse_set_args(args), ("defaults.backup", "false"))

        self.assertEqual(
            CFG.parse_set_args(["repos.search", "~/src,", "~/work"]),
            ("repos.search", "~/src, ~/work"),
        )
        for bad in ([], ["defaults.backup"], ["defaults.backup", "="]):
            with self.assertRaises(CFG.ConfigError):
                CFG.parse_set_args(bad)

        # parse_add_args variants
        for args in (
            ["~/src", "to", "repos.search"],
            ["~/src", "repos.search"],
            ["repos.search", "~/src"],
        ):
            self.assertEqual(CFG.parse_add_args(args), ("~/src", "repos.search"))

        # parse_remove_args variants
        for args in (
            ["~/src", "from", "repos.search"],
            ["~/src", "repos.search"],
            ["repos.search", "~/src"],
        ):
            self.assertEqual(CFG.parse_remove_args(args), ("~/src", "repos.search"))

        # parse_is_args variants
        for args in (["~/src", "in", "repos.search"], ["~/src", "repos.search"]):
            self.assertEqual(CFG.parse_is_args(args), ("~/src", "repos.search"))

        # add and remove item
        cfg = CFG.default_config()
        cfg, key, items, added, stored = CFG.add_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertEqual(key, "repos.search")
        self.assertTrue(added)
        self.assertIn("~/src", items)

        # idempotent add
        cfg, key, items, added, stored = CFG.add_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertFalse(added)
        self.assertEqual(len(items), 1)

        # check membership
        key, present, stored = CFG.is_config_item_present(
            "repos.search", "~/src", cfg=cfg
        )
        self.assertTrue(present)

        # remove item
        cfg, key, items, removed, stored = CFG.remove_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertTrue(removed)
        self.assertNotIn("~/src", items)

        # remove nonexistent
        cfg, key, items, removed, stored = CFG.remove_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertFalse(removed)

        # non-list raises
        with self.assertRaises(CFG.ConfigError):
            CFG.add_config_item("defaults.backup", "foo", cfg=cfg, auto_save=False)
        with self.assertRaises(CFG.ConfigError):
            CFG.remove_config_item("defaults.backup", "foo", cfg=cfg, auto_save=False)
        with self.assertRaises(CFG.ConfigError):
            CFG.is_config_item_present("defaults.backup", "foo", cfg=cfg)


class SchemaMigrationTests(unittest.TestCase):
    LEGACY = {
        "config_version": 1,
        "search_roots": ["~/src", "~/work"],
        "repos": ["~/src/foo", "~/src/bar"],
        "exclude": ["~/src/legacy", "*/never-install/*"],
        "ignore": ["*/vendor/*"],
        "defaults": {"backup": False, "prune": True},
    }

    def test_schema_migration_idempotent_and_shape_driven(self):
        out = CFG.normalize(self.LEGACY)
        self.assertEqual(out["config_version"], 2)
        self.assertEqual(out["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(out["repos"]["installed"], ["~/src/foo", "~/src/bar"])
        self.assertEqual(out["repos"]["exclude"], ["~/src/legacy", "*/never-install/*"])
        self.assertEqual(out["repos"]["ignore"], ["*/vendor/*"])
        self.assertEqual(out["defaults"], {"backup": False, "prune": True})
        for legacy_key in ("search_roots", "exclude", "ignore"):
            self.assertNotIn(legacy_key, out)

        # Idempotent
        twice = CFG.normalize(out)
        self.assertEqual(out, twice)
        self.assertEqual(
            json.dumps(out, sort_keys=True), json.dumps(twice, sort_keys=True)
        )

        # Partially migrated
        partial = {
            "config_version": 1,
            "search_roots": ["~/legacy-root"],
            "repos": {"search": ["~/new-root"]},
            "ignore": ["*/vendor/*"],
        }
        out_part = CFG.normalize(partial)
        self.assertEqual(out_part["repos"]["search"], ["~/new-root"])
        self.assertNotIn("~/legacy-root", out_part["repos"]["search"])
        self.assertEqual(out_part["repos"]["ignore"], ["*/vendor/*"])

        # Stale version flat file
        stale_version = dict(self.LEGACY)
        stale_version["config_version"] = 2
        out_stale = CFG.normalize(stale_version)
        self.assertEqual(out_stale["repos"]["search"], ["~/src", "~/work"])

        # Unversioned flat file
        unversioned = {k: v for k, v in self.LEGACY.items() if k != "config_version"}
        out_unv = CFG.normalize(unversioned)
        self.assertEqual(out_unv["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(out_unv["config_version"], 2)

    def test_normalize_config(self):
        # repos.ignore not home expanded
        out = CFG.normalize({"repos": {"ignore": ["~weird-glob", "*/vendor/*"]}})
        self.assertEqual(out["repos"]["ignore"], ["~weird-glob", "*/vendor/*"])

        # unknown repos subkeys rejected
        out_sub = CFG.normalize({"repos": {"search": ["~/src"], "bogus": ["x"]}})
        self.assertEqual(set(out_sub["repos"]), set(CFG._ALLOWED_REPOS_KEYS))
        self.assertNotIn("bogus", out_sub["repos"])

        # top key allowlist applied
        real_default = CFG.default_config

        def leaky_default():
            cfg = real_default()
            cfg["sneaky_key"] = "should-not-survive"
            return cfg

        with mock.patch.object(CFG, "default_config", leaky_default):
            out_leak = CFG.normalize({})
        self.assertNotIn("sneaky_key", out_leak)
        self.assertTrue(set(out_leak) <= CFG._ALLOWED_TOP_KEYS)

        # allowlist matches default config shape
        self.assertTrue(set(CFG.default_config()) <= CFG._ALLOWED_TOP_KEYS)
        self.assertNotIn("search_roots", CFG._ALLOWED_TOP_KEYS)
        self.assertIn("repos", CFG._ALLOWED_TOP_KEYS)

        # survives malformed repos values
        for bad in (None, "string", 7, []):
            out_bad = CFG.normalize({"repos": bad})
            self.assertEqual(out_bad["repos"], CFG.default_config()["repos"])


class MigrationOnDiskTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self._tmp.cleanup()

    def _plant(self, payload):
        p = CFG.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        p.write_text(text, encoding="utf-8")
        return p, text

    def test_planted_legacy_config_and_load_no_rewrite(self):
        _, planted_text = self._plant(SchemaMigrationTests.LEGACY)
        loaded = CFG.load()
        self.assertEqual(loaded["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(loaded["repos"]["installed"], ["~/src/foo", "~/src/bar"])
        self.assertEqual(
            loaded["repos"]["exclude"], ["~/src/legacy", "*/never-install/*"]
        )
        self.assertEqual(loaded["repos"]["ignore"], ["*/vendor/*"])

        # Load does not rewrite file (lazy)
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

        # Save updates to v2
        CFG.save(loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertEqual(on_disk["config_version"], 2)
        self.assertEqual(on_disk["repos"]["search"], ["~/src", "~/work"])
        self.assertNotIn("search_roots", on_disk)

    def test_future_version_handling(self):
        payload = {
            "config_version": 3,
            "repos": {
                "search": ["~/src"],
                "exclude": ["~/src/never"],
                "installed": ["~/src/foo"],
                "ignore": ["*/vendor/*"],
            },
            "some_future_key": {"kept": True},
        }
        _, planted_text = self._plant(payload)
        loaded = CFG.load()
        self.assertEqual(loaded["repos"]["search"], ["~/src"])
        self.assertEqual(loaded["config_version"], 3)
        self.assertIn("some_future_key", loaded)

        # Save refuses to overwrite future config
        with self.assertRaises(CFG.ConfigError):
            CFG.save(CFG.load())
        with self.assertRaises(CFG.ConfigError):
            CFG.save(CFG.default_config())
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

        # Mutating verb fails without data loss
        with self.assertRaises(CFG.ConfigError):
            CFG.add_config_item("repos.search", "~/other")
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

        # is_future_version check
        self.assertFalse(CFG.is_future_version({"config_version": 1}))
        self.assertFalse(CFG.is_future_version({"config_version": 2}))
        self.assertFalse(CFG.is_future_version({}))
        self.assertFalse(CFG.is_future_version({"config_version": "banana"}))
        self.assertFalse(CFG.is_future_version({"config_version": True}))
        self.assertTrue(CFG.is_future_version({"config_version": 3}))


class NestedRepoKeyVerbTests(unittest.TestCase):
    SUBKEYS = ("repos.search", "repos.installed", "repos.exclude", "repos.ignore")

    def test_nested_repo_key_roundtrip_and_subkeys(self):
        for key in self.SUBKEYS:
            with self.subTest(key=key):
                cfg = CFG.default_config()
                item = "*/glob-entry/*" if key == "repos.ignore" else "~/src/thing"

                cfg, k, items, added, _ = CFG.add_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertEqual(k, key)
                self.assertTrue(added)
                self.assertEqual(items, [item])

                _, val = CFG.get_config_value(key, cfg)
                self.assertEqual(val, [item])
                _, present, _ = CFG.is_config_item_present(key, item, cfg=cfg)
                self.assertTrue(present)

                cfg, _, items, removed, _ = CFG.remove_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertTrue(removed)
                self.assertEqual(items, [])

        # set_config_value on every subkey
        cfg = CFG.default_config()
        for key in self.SUBKEYS:
            cfg, k, val = CFG.set_config_value(key, "a,b", cfg=cfg, auto_save=False)
            self.assertEqual(k, key)
            self.assertEqual(val, ["a", "b"])
        for key in self.SUBKEYS:
            _, val = CFG.get_config_value(key, cfg)
            self.assertEqual(val, ["a", "b"])

        # set repos mapping rejects unknown subkey
        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value(
                "repos", {"search": ["~/src"], "bogus": []}, cfg=cfg, auto_save=False
            )
        cfg, k, val = CFG.set_config_value(
            "repos", {"search": ["~/src"]}, cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "repos")
        self.assertEqual(val["search"], ["~/src"])

    def test_nested_repo_key_verbs_and_readers(self):
        cfg = CFG.default_config()
        for call in (
            lambda: CFG.add_config_item("repos", "~/src", cfg=cfg, auto_save=False),
            lambda: CFG.remove_config_item("repos", "~/src", cfg=cfg, auto_save=False),
            lambda: CFG.is_config_item_present("repos", "~/src", cfg=cfg),
        ):
            with self.assertRaises(CFG.ConfigError) as ctx:
                call()
            msg = str(ctx.exception)
            for subkey in (
                "repos.installed",
                "repos.search",
                "repos.exclude",
                "repos.ignore",
            ):
                self.assertIn(subkey, msg)

        # reading bare repos
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        k, val = CFG.get_config_value("repos", cfg)
        self.assertEqual(k, "repos")
        self.assertEqual(val["search"], ["~/src"])

        # set_repo_setting rejects unknown subkey
        with self.assertRaises(CFG.ConfigError):
            CFG.set_repo_setting(CFG.default_config(), "bogus", [])

        # repo_setting reader degrades to empty
        self.assertEqual(CFG.repo_setting({}, "search"), [])
        self.assertEqual(CFG.repo_setting({"repos": "nonsense"}, "search"), [])
        self.assertEqual(CFG.repo_setting({"repos": {}}, "search"), [])

        # accessors read nested layout
        cfg_norm = CFG.normalize(SchemaMigrationTests.LEGACY)
        self.assertEqual(
            CFG.expanded_search_roots(cfg_norm),
            [Path.home() / "src", Path.home() / "work"],
        )
        self.assertEqual(
            CFG.expanded_repos(cfg_norm),
            [Path.home() / "src" / "foo", Path.home() / "src" / "bar"],
        )
        self.assertEqual(
            CFG.expanded_excludes(cfg_norm),
            [str(Path.home() / "src" / "legacy"), "*/never-install/*"],
        )
        self.assertEqual(CFG.ignore_patterns(cfg_norm), ["*/vendor/*"])


class ConfigCliCommandTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self._tmp.cleanup()

    def test_cli_config_show_get_set(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "show"]), 0)
        self.assertIn("agent-workflows configuration", out.getvalue())
        self.assertIn("defaults.backup", out.getvalue())

        out_json = io.StringIO()
        with redirect_stdout(out_json):
            self.assertEqual(cli.main(["config", "show", "--json"]), 0)
        data = json.loads(out_json.getvalue())
        self.assertIn("config_file", data)
        self.assertIn("config", data)

        # single var
        out_single = io.StringIO()
        with redirect_stdout(out_single):
            self.assertEqual(cli.main(["config", "show", "defaults.backup"]), 0)
        self.assertIn("defaults.backup", out_single.getvalue())

        out_sj = io.StringIO()
        with redirect_stdout(out_sj):
            self.assertEqual(
                cli.main(["config", "show", "defaults.backup", "--json"]), 0
            )
        self.assertTrue(json.loads(out_sj.getvalue())["value"])

        # set and get roundtrip
        out_set = io.StringIO()
        with redirect_stdout(out_set):
            self.assertEqual(
                cli.main(["config", "set", "defaults.backup", "to", "false"]), 0
            )
        self.assertIn("defaults.backup = False", out_set.getvalue())

        out_get = io.StringIO()
        with redirect_stdout(out_get):
            self.assertEqual(cli.main(["config", "get", "defaults.backup"]), 0)
        self.assertEqual(out_get.getvalue().strip(), "false")

        out_get_json = io.StringIO()
        with redirect_stdout(out_get_json):
            self.assertEqual(
                cli.main(["config", "get", "defaults.backup", "--json"]), 0
            )
        self.assertEqual(
            json.loads(out_get_json.getvalue()), {"defaults.backup": False}
        )

        # set errors
        out_err = io.StringIO()
        with redirect_stdout(out_err):
            self.assertEqual(cli.main(["config", "set", "invalid_key", "foo"]), 2)
        self.assertIn("FAIL", out_err.getvalue())

        # conf alias
        out_alias = io.StringIO()
        with redirect_stdout(out_alias):
            self.assertEqual(cli.main(["conf", "show", "defaults.backup"]), 0)
        self.assertIn("defaults.backup", out_alias.getvalue())

        # groups sections
        out_grp = io.StringIO()
        with redirect_stdout(out_grp):
            self.assertEqual(cli.main(["config", "show"]), 0)
        self.assertIn("Settings (defaults)", out_grp.getvalue())
        self.assertIn("Settings (repos)", out_grp.getvalue())

    def test_cli_config_add_remove_and_is(self):
        out_add = io.StringIO()
        with redirect_stdout(out_add):
            self.assertEqual(
                cli.main(["config", "add", "~/my-test-root", "to", "repos.search"]), 0
            )
        self.assertIn("Added", out_add.getvalue())

        out_is = io.StringIO()
        with redirect_stdout(out_is):
            self.assertEqual(
                cli.main(["config", "is", "~/my-test-root", "in", "repos.search"]), 0
            )
        self.assertIn("Yes", out_is.getvalue())

        out_rem = io.StringIO()
        with redirect_stdout(out_rem):
            self.assertEqual(
                cli.main(
                    ["config", "remove", "~/my-test-root", "from", "repos.search"]
                ),
                0,
            )
        self.assertIn("Removed", out_rem.getvalue())

        out_is2 = io.StringIO()
        with redirect_stdout(out_is2):
            self.assertEqual(
                cli.main(["config", "is", "~/my-test-root", "in", "repos.search"]), 1
            )
        self.assertIn("No", out_is2.getvalue())

        # add to bare repos is actionable error
        out_bare = io.StringIO()
        with redirect_stdout(out_bare):
            self.assertEqual(
                cli.main(["config", "add", "~/my-test-root", "to", "repos"]), 2
            )
        self.assertIn("repos.search", out_bare.getvalue())

    def test_cli_legacy_config_migration(self):
        p = CFG.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(SchemaMigrationTests.LEGACY), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                cli.main(["config", "add", "~/extra-root", "to", "repos.search"]), 0
            )

        on_disk = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["config_version"], 2)
        self.assertNotIn("search_roots", on_disk)
        self.assertEqual(
            on_disk["repos"]["search"], ["~/src", "~/work", "~/extra-root"]
        )
        self.assertEqual(on_disk["repos"]["installed"], ["~/src/foo", "~/src/bar"])


class ColorDepthKeyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._saved = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._tmp.name
        self.addCleanup(self._restore)

    def _restore(self):
        if self._saved is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._saved

    def test_color_depth_schema_registration_and_normalization(self):
        self.assertIn("color_depth", CFG.CONFIG_SCHEMA)
        spec = CFG.CONFIG_SCHEMA["color_depth"]
        self.assertFalse(spec.read_only)
        self.assertEqual(spec.allowed_values, CFG.COLOR_DEPTH_VALUES)

        # Survives normalization
        self.assertIn("color_depth", CFG._ALLOWED_TOP_KEYS)
        out = CFG.normalize({"color_depth": "16"})
        self.assertEqual(out["color_depth"], "16")

        # Accepted values roundtrip
        for value in CFG.COLOR_DEPTH_VALUES:
            with self.subTest(value=value):
                CFG.set_config_value("color_depth", value)
                self.assertEqual(CFG.load()["color_depth"], value)
                self.assertEqual(CFG.get_color_depth(), value)

        # Case insensitive and stored canonically
        CFG.set_config_value("color_depth", "NONE")
        self.assertEqual(CFG.get_color_depth(), "none")

        # Unset reads as none
        CFG.save(CFG.default_config())
        self.assertIsNone(CFG.get_color_depth())

    def test_color_depth_refusal_and_resilience(self):
        with self.assertRaises(CFG.ConfigError) as ctx:
            CFG.set_config_value("color_depth", "tru3color")
        message = str(ctx.exception)
        self.assertIn("tru3color", message)
        for value in CFG.COLOR_DEPTH_VALUES:
            self.assertIn(value, message)

        # Refused value not written to disk
        CFG.set_config_value("color_depth", "16")
        with self.assertRaises(CFG.ConfigError):
            CFG.set_config_value("color_depth", "nope")
        self.assertEqual(CFG.get_color_depth(), "16")

        # Plausible near misses refused
        for bad in ("8", "true", "yes", "full", "truecolor", "24bit", ""):
            with self.subTest(bad=bad), self.assertRaises(CFG.ConfigError):
                CFG.set_config_value("color_depth", bad)

        # Hand edited invalid value dropped
        cfg = CFG.load()
        cfg["color_depth"] = "tru3color"
        CFG.save(cfg)
        self.assertIsNone(CFG.get_color_depth())

        # Survives corrupt config file
        path = CFG.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json at all", encoding="utf-8")
        self.assertIsNone(CFG.get_color_depth())

    def test_color_depth_cli_interaction(self):
        self.assertEqual(cli.main(["config", "set", "color_depth", "16"]), 0)
        self.assertEqual(CFG.get_color_depth(), "16")

        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "show"]), 0)
        self.assertIn("color_depth", out.getvalue())

        out_err = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out_err), redirect_stderr(err):
            rc = cli.main(["config", "set", "color_depth", "tru3color"])
        self.assertNotEqual(rc, 0)
        combined = out_err.getvalue() + err.getvalue()
        self.assertIn("256", combined)
        self.assertIn("16", combined)


class DeclarativeAllowedValuesTests(unittest.TestCase):
    # This test calls set_config_value, which SAVES config.json. Without its own sandbox it
    # wrote the developer's real ~/.config/agent-workflows/config.json and left
    # "aw_home": "~/allowed" there (measured 2026-09-24).
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_declarative_allowed_values(self):
        self.assertTrue(str(CFG.config_path()).startswith(self._tmp.name))
        for key, spec in CFG.CONFIG_SCHEMA.items():
            if key in ("color_depth", "defaults.leftovers"):
                self.assertIsNotNone(spec.allowed_values)
                continue
            with self.subTest(key=key):
                self.assertIsNone(spec.allowed_values)

        CFG.set_config_value("aw_home", "~/somewhere")
        self.assertEqual(CFG.load()["aw_home"], "~/somewhere")

        fake = dict(CFG.CONFIG_SCHEMA)
        fake["aw_home"] = CFG.ConfigKeySpec(
            key="aw_home",
            type_name="path",
            description="temporarily constrained for this test",
            allowed_values=("~/allowed",),
        )
        with mock.patch.object(CFG, "CONFIG_SCHEMA", fake):
            CFG.set_config_value("aw_home", "~/allowed")
            with self.assertRaises(CFG.ConfigError) as ctx:
                CFG.set_config_value("aw_home", "~/forbidden")
        self.assertIn("~/allowed", str(ctx.exception))


class InstallPolicyDefaultsConfigTests(unittest.TestCase):
    """E-01 and E-02 tests for defaults.migrate_layout and defaults.leftovers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_schema_registration_and_absence_by_default(self):
        self.assertIn("defaults.migrate_layout", CFG.CONFIG_SCHEMA)
        self.assertIn("defaults.leftovers", CFG.CONFIG_SCHEMA)
        self.assertIn("migrate_layout", CFG._ALLOWED_DEFAULT_KEYS)
        self.assertIn("leftovers", CFG._ALLOWED_DEFAULT_KEYS)

        # ABSENT from default_config()
        def_cfg = CFG.default_config()
        self.assertNotIn("migrate_layout", def_cfg["defaults"])
        self.assertNotIn("leftovers", def_cfg["defaults"])

        # show initially displays '-'
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "show", "defaults.migrate_layout"]), 0)
        self.assertIn("defaults.migrate_layout = -", out.getvalue())

        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "show", "defaults.leftovers"]), 0)
        self.assertIn("defaults.leftovers   = -", out.getvalue())

    def test_set_and_persistence_roundtrip(self):
        # bool key
        CFG.set_config_value("defaults.migrate_layout", True)
        self.assertTrue(CFG.load()["defaults"]["migrate_layout"])
        _, val = CFG.get_config_value("defaults.migrate_layout")
        self.assertTrue(val)

        # str enum key persists correctly (F-9 / F-8 fix)
        CFG.set_config_value("defaults.leftovers", "remove")
        self.assertEqual(CFG.load()["defaults"]["leftovers"], "remove")
        _, val = CFG.get_config_value("defaults.leftovers")
        self.assertEqual(val, "remove")

        # Setter refusal of out-of-enum value
        with self.assertRaises(CFG.ConfigError) as ctx:
            CFG.set_config_value("defaults.leftovers", "rubbish")
        self.assertIn("keep, remove, defer", str(ctx.exception))

    def test_normalize_preserves_strings_and_drops_invalid(self):
        # Valid string survives normalization
        normalized = CFG.normalize(
            {"defaults": {"leftovers": "remove", "migrate_layout": True}}
        )
        self.assertEqual(normalized["defaults"]["leftovers"], "remove")
        self.assertTrue(normalized["defaults"]["migrate_layout"])

        # Out-of-enum string is DROPPED by normalize (fail-open)
        dropped = CFG.normalize({"defaults": {"leftovers": "rubbish"}})
        self.assertNotIn("leftovers", dropped["defaults"])

    def test_clearing_and_unset_removes_keys(self):
        CFG.set_config_value("defaults.migrate_layout", True)
        CFG.set_config_value("defaults.leftovers", "remove")
        self.assertIn("migrate_layout", CFG.load()["defaults"])
        self.assertIn("leftovers", CFG.load()["defaults"])

        # aw config unset removes subkey
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(
                cli.main(["config", "unset", "defaults.migrate_layout"]), 0
            )
        self.assertIn("defaults.migrate_layout unset", out.getvalue())

        loaded = CFG.load()
        self.assertNotIn("migrate_layout", loaded["defaults"])
        _, val = CFG.get_config_value("defaults.migrate_layout")
        self.assertIsNone(val)

        # Verify config get outputs empty (unset)
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "get", "defaults.migrate_layout"]), 0)
        self.assertEqual(out.getvalue().strip(), "")

        # aw config set <key> - also unsets
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["config", "set", "defaults.leftovers", "-"]), 0)
        loaded = CFG.load()
        self.assertNotIn("leftovers", loaded["defaults"])
        _, val = CFG.get_config_value("defaults.leftovers")
        self.assertIsNone(val)


class DynamicCutoverResolutionTests(unittest.TestCase):
    def test_cutover_resolution_precedence(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            project_json = cfg_dir / "project.json"
            project_json.write_text(
                json.dumps(
                    {
                        "cutovers": {
                            "spec_id6": "2026-08-29",
                            "carrier_obligations": "20260919",
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "spec_id6", compact=True), "20260829"
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "spec_id6", compact=False), "2026-08-29"
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "carrier_obligations", compact=False),
                "2026-09-19",
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "carrier_obligations", compact=True),
                "20260919",
            )

        # Legacy dependency schema fallback
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            project_json = cfg_dir / "project.json"
            project_json.write_text(
                json.dumps({"dependency_schema_cutover": {"date": "2026-09-01"}}),
                encoding="utf-8",
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "dependency_schema", compact=False),
                "2026-09-01",
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "dependency_schema", compact=True),
                "20260901",
            )

        # Install history fallback
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            history_dir = repo / ".aw" / "state" / "history"
            history_dir.mkdir(parents=True)
            installs = history_dir / "installs.jsonl"
            installs.write_text(
                json.dumps({"timestamp": "2026-08-18T15:00:00Z"})
                + "\n"
                + json.dumps({"timestamp": "2026-08-29T20:00:00Z"})
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                CFG.resolve_cutover_date(repo, "spec_id6", compact=False), "2026-08-29"
            )
            self.assertIsNone(
                CFG.resolve_cutover_date(repo, "carrier_obligations", compact=False)
            )

        # Fail open when no configuration or history
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self.assertIsNone(CFG.resolve_cutover_date(repo, "spec_id6"))
            self.assertIsNone(CFG.resolve_cutover_date(repo, "carrier_obligations"))
            self.assertIsNone(CFG.resolve_cutover_date(repo, "dependency_schema"))

    def test_sync_cutovers_on_install(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            project_json = cfg_dir / "project.json"
            project_json.write_text(
                json.dumps(
                    {"preset": "private-target", "cutovers": {"spec_id6": "2026-08-20"}}
                ),
                encoding="utf-8",
            )
            history_dir = repo / ".aw" / "state" / "history"
            history_dir.mkdir(parents=True)
            installs = history_dir / "installs.jsonl"
            installs.write_text(
                json.dumps({"timestamp": "2026-09-02T10:00:00Z"}) + "\n",
                encoding="utf-8",
            )

            stamped = CFG.sync_cutovers_on_install(repo, install_timestamp="2026-09-25")
            self.assertEqual(stamped["spec_id6"], "2026-08-20")
            self.assertEqual(stamped["dependency_schema"], "2026-09-02")
            self.assertEqual(stamped["carrier_obligations"], "2026-09-25")

            # Subsequent call preserves established cutovers
            stamped2 = CFG.sync_cutovers_on_install(
                repo, install_timestamp="2026-10-01"
            )
            self.assertEqual(stamped2["spec_id6"], "2026-08-20")
            self.assertEqual(stamped2["dependency_schema"], "2026-09-02")
            self.assertEqual(stamped2["carrier_obligations"], "2026-09-25")


class SetidPolicyTests(unittest.TestCase):
    def _repo(self, d, project=None):
        repo = Path(d)
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        if project is not None:
            (cfg / "project.json").write_text(json.dumps(project), encoding="utf-8")
        return repo

    def test_setid_policy_defaults_and_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, {"schema_version": 2})
            p = CFG.get_setid_policy(repo)
            self.assertEqual(p.warn_length, 14)
            self.assertEqual(p.max_length, 24)
            self.assertFalse(p.strict)
            self.assertIsNone(p.cutover_date)
            self.assertIsNone(CFG.resolve_cutover_date(repo, "setid_length"))

        # Custom thresholds and strict
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(
                d,
                {
                    "schema_version": 2,
                    "setids": {"warn_length": 8, "max_length": 12, "strict": True},
                },
            )
            p = CFG.get_setid_policy(repo)
            self.assertEqual((p.warn_length, p.max_length, p.strict), (8, 12, True))

        # Malformed thresholds fall back
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(
                d,
                {
                    "schema_version": 2,
                    "setids": {
                        "warn_length": "twelve",
                        "max_length": 0,
                        "strict": "yes",
                    },
                },
            )
            p = CFG.get_setid_policy(repo)
            self.assertEqual((p.warn_length, p.max_length, p.strict), (14, 24, False))

        # Inverted thresholds fall back
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(
                d,
                {"schema_version": 2, "setids": {"warn_length": 20, "max_length": 10}},
            )
            p = CFG.get_setid_policy(repo)
            self.assertEqual((p.warn_length, p.max_length), (14, 24))

        # Boundary at 24 and 25
        p_bound = CFG.SetidPolicy()
        self.assertIsNone(p_bound.tier_for("a" * 14))
        self.assertEqual(p_bound.tier_for("a" * 15), "warning")
        self.assertEqual(p_bound.tier_for("a" * 24), "warning")
        self.assertEqual(p_bound.tier_for("a" * 25), "error")
        self.assertEqual(len("research-prompt-pipeline"), 24)
        self.assertNotEqual(p_bound.tier_for("research-prompt-pipeline"), "error")

    def test_setid_and_prompt_cutover_registration(self):
        self.assertIn("setid_length", CFG.KNOWN_FEATURE_CUTOVERS)
        self.assertIn("prompt_id6", CFG.KNOWN_FEATURE_CUTOVERS)

        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(
                d, {"schema_version": 2, "cutovers": {"spec_id6": "2026-08-20"}}
            )
            stamped = CFG.sync_cutovers_on_install(repo, install_timestamp="2026-09-23")
            self.assertEqual(stamped["setid_length"], "2026-09-23")
            self.assertEqual(stamped["spec_id6"], "2026-08-20")
            self.assertEqual(CFG.resolve_cutover_date(repo, "setid_length"), "20260923")

            again = CFG.sync_cutovers_on_install(repo, install_timestamp="2026-10-01")
            self.assertEqual(again["setid_length"], "2026-09-23")

        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, {"schema_version": 2})
            stamped = CFG.sync_cutovers_on_install(repo, install_timestamp="2026-10-05")
            self.assertEqual(stamped["prompt_id6"], "2026-10-05")
            self.assertEqual(CFG.resolve_cutover_date(repo, "prompt_id6"), "20261005")
            again = CFG.sync_cutovers_on_install(repo, install_timestamp="2026-11-01")
            self.assertEqual(again["prompt_id6"], "2026-10-05")

    def test_setid_grandfathering(self):
        pre = CFG.SetidPolicy(cutover_date="20260923")
        self.assertFalse(pre.applies_to_artifact_date("20260901"))
        self.assertTrue(pre.applies_to_artifact_date("20260923"))
        self.assertTrue(pre.applies_to_artifact_date("20261001"))
        self.assertFalse(pre.applies_to_artifact_date(None))
        self.assertFalse(CFG.SetidPolicy().applies_to_artifact_date("20261001"))

        strict = CFG.SetidPolicy(strict=True)
        self.assertTrue(strict.applies_to_artifact_date("20200101"))
        self.assertTrue(strict.applies_to_artifact_date(None))


class SetidAuthoringGuardTests(unittest.TestCase):
    def _repo(self, d, extra_project=None):
        repo = Path(d)
        (repo / ".aw" / "config").mkdir(parents=True)
        payload = {"schema_version": 2}
        if extra_project:
            payload.update(extra_project)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        return repo

    def test_setid_authoring_guard(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d)
            # over max is error
            err, warn = CFG.validate_setid_length_for_authoring(
                repo, "a" * 25, verb="aw ipd scaffold"
            )
            self.assertIsNotNone(err)
            self.assertIn("25 characters", err)
            self.assertIn("24", err)
            self.assertIsNone(warn)

            # 15 to 24 is warning
            err, warn = CFG.validate_setid_length_for_authoring(
                repo, "a" * 16, verb="aw ipd scaffold"
            )
            self.assertIsNone(err)
            self.assertIsNotNone(warn)
            self.assertIn("16 characters", warn)

            # <= 14 conforms
            self.assertEqual(
                CFG.validate_setid_length_for_authoring(
                    repo, "a" * 14, verb="aw ipd scaffold"
                ),
                (None, None),
            )

            # boundary at 24 and 25
            err24, warn24 = CFG.validate_setid_length_for_authoring(
                repo, "a" * 24, verb="v"
            )
            err25, _ = CFG.validate_setid_length_for_authoring(repo, "a" * 25, verb="v")
            self.assertIsNone(err24)
            self.assertIsNotNone(warn24)
            self.assertIsNotNone(err25)

            # absent setid
            for value in (None, "", "   "):
                self.assertEqual(
                    CFG.validate_setid_length_for_authoring(repo, value, verb="v"),
                    (None, None),
                )

            # unstamped repo still refuses
            self.assertIsNone(CFG.get_setid_policy(repo).cutover_date)
            err_un, _ = CFG.validate_setid_length_for_authoring(
                repo, "a" * 25, verb="v"
            )
            self.assertIsNotNone(err_un)

        # repository raising max length honored
        with tempfile.TemporaryDirectory() as d:
            repo_raised = self._repo(d, {"setids": {"max_length": 30}})
            err_raised, _ = CFG.validate_setid_length_for_authoring(
                repo_raised, "a" * 25, verb="v"
            )
            self.assertIsNone(err_raised)


if __name__ == "__main__":
    unittest.main()

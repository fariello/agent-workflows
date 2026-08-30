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

        # And a re-save persists only the allowlist.
        CFG.save(loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertEqual(set(on_disk.keys()), CFG.default_config().keys() | set())
        self.assertNotIn("token", on_disk)

    def test_is_configured(self):
        self.assertFalse(CFG.is_configured())
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        CFG.save(cfg)
        self.assertTrue(CFG.is_configured())

    def test_is_configured_false_for_default_nested_config(self):
        # E-06 regression guard: the default `repos` MAPPING is a non-empty dict, so a
        # container truthiness check would report a brand-new user as configured and
        # suppress the setup path. is_configured() must test the nested LISTS.
        CFG.save(CFG.default_config())
        self.assertTrue(CFG.config_path().is_file())
        self.assertTrue(bool(CFG.load()["repos"]), "the container itself is truthy")
        self.assertFalse(CFG.is_configured())

        cfg = CFG.load()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        CFG.save(cfg)
        self.assertTrue(CFG.is_configured())

    def test_is_configured_true_for_installed_only(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "installed", ["~/src/foo"])
        CFG.save(cfg)
        self.assertTrue(CFG.is_configured())

    def test_exclude_roundtrips_and_expands(self):
        # E-01: the exclude blocklist round-trips load/save (home-preserved), unknown keys
        # still stripped, and expanded_excludes returns expanded strings (paths AND globs).
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "exclude", ["~/src/legacy-repo", "*/never-install/*"])
        cfg["token"] = "SECRET-should-not-persist"  # unknown -> must be dropped
        CFG.save(cfg)
        loaded = CFG.load()
        self.assertEqual(
            loaded["repos"]["exclude"], ["~/src/legacy-repo", "*/never-install/*"]
        )
        self.assertNotIn("token", loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertIn("exclude", on_disk["repos"])
        self.assertNotIn("token", on_disk)

        expanded = CFG.expanded_excludes(loaded)
        self.assertEqual(
            expanded,
            [str(Path.home() / "src" / "legacy-repo"), "*/never-install/*"],
        )
        # An absolute path entry expands to itself; a default config has no excludes.
        self.assertEqual(CFG.expanded_excludes(CFG.default_config()), [])

    def test_exclude_defaults_empty(self):
        self.assertEqual(CFG.default_config()["repos"]["exclude"], [])
        self.assertEqual(CFG.load()["repos"]["exclude"], [])


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

    def test_config_schema_has_no_legacy_flat_keys(self):
        for k in ("search_roots", "exclude", "ignore"):
            self.assertNotIn(k, CFG.CONFIG_SCHEMA)
        self.assertEqual(CFG.CONFIG_SCHEMA["repos"].type_name, "dict")

    def test_get_config_value_top_level_and_dotted(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        cfg["defaults"] = {"backup": False, "prune": True}

        k, v = CFG.get_config_value("repos.search", cfg)
        self.assertEqual(k, "repos.search")
        self.assertEqual(v, ["~/src"])

        k, v = CFG.get_config_value("repos", cfg)
        self.assertEqual(k, "repos")
        self.assertEqual(v["search"], ["~/src"])

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
            "repos.search", "~/src, ~/work", cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "repos.search")
        self.assertEqual(v, ["~/src", "~/work"])

        cfg, k, v = CFG.set_config_value(
            "repos.search", '["~/projects"]', cfg=cfg, auto_save=False
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

        var, val = CFG.parse_set_args(["repos.search", "~/src,", "~/work"])
        self.assertEqual((var, val), ("repos.search", "~/src, ~/work"))

    def test_parse_set_args_error_cases(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args([])

        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args(["defaults.backup"])

        with self.assertRaises(CFG.ConfigError):
            CFG.parse_set_args(["defaults.backup", "="])

    def test_parse_add_args_variants(self):
        item, var = CFG.parse_add_args(["~/src", "to", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

        item, var = CFG.parse_add_args(["~/src", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

        item, var = CFG.parse_add_args(["repos.search", "~/src"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

    def test_parse_remove_args_variants(self):
        item, var = CFG.parse_remove_args(["~/src", "from", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

        item, var = CFG.parse_remove_args(["~/src", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

        item, var = CFG.parse_remove_args(["repos.search", "~/src"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

    def test_parse_is_args_variants(self):
        item, var = CFG.parse_is_args(["~/src", "in", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

        item, var = CFG.parse_is_args(["~/src", "repos.search"])
        self.assertEqual((item, var), ("~/src", "repos.search"))

    def test_add_and_remove_config_item(self):
        cfg = CFG.default_config()
        # Add item
        cfg, key, items, added, stored = CFG.add_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertEqual(key, "repos.search")
        self.assertTrue(added)
        self.assertIn("~/src", items)

        # Idempotent add
        cfg, key, items, added, stored = CFG.add_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertFalse(added)
        self.assertEqual(len(items), 1)

        # Check membership
        key, present, stored = CFG.is_config_item_present(
            "repos.search", "~/src", cfg=cfg
        )
        self.assertTrue(present)

        # Remove item
        cfg, key, items, removed, stored = CFG.remove_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertTrue(removed)
        self.assertNotIn("~/src", items)

        # Remove nonexistent
        cfg, key, items, removed, stored = CFG.remove_config_item(
            "repos.search", "~/src", cfg=cfg, auto_save=False
        )
        self.assertFalse(removed)

    def test_add_remove_non_list_raises(self):
        cfg = CFG.default_config()
        with self.assertRaises(CFG.ConfigError):
            CFG.add_config_item("defaults.backup", "foo", cfg=cfg, auto_save=False)

        with self.assertRaises(CFG.ConfigError):
            CFG.remove_config_item("defaults.backup", "foo", cfg=cfg, auto_save=False)

        with self.assertRaises(CFG.ConfigError):
            CFG.is_config_item_present("defaults.backup", "foo", cfg=cfg)


class SchemaMigrationTests(unittest.TestCase):
    """Schema version 1 (flat keys) -> version 2 (nested `repos` mapping); plan 8h9lap E-02."""

    LEGACY = {
        "config_version": 1,
        "search_roots": ["~/src", "~/work"],
        "repos": ["~/src/foo", "~/src/bar"],
        "exclude": ["~/src/legacy", "*/never-install/*"],
        "ignore": ["*/vendor/*"],
        "defaults": {"backup": False, "prune": True},
    }

    def test_legacy_flat_config_migrates_with_no_value_loss(self):
        out = CFG.normalize(self.LEGACY)
        self.assertEqual(out["config_version"], 2)
        self.assertEqual(out["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(out["repos"]["installed"], ["~/src/foo", "~/src/bar"])
        self.assertEqual(out["repos"]["exclude"], ["~/src/legacy", "*/never-install/*"])
        self.assertEqual(out["repos"]["ignore"], ["*/vendor/*"])
        self.assertEqual(out["defaults"], {"backup": False, "prune": True})
        # No flat key survives the migration; there are deliberately no aliases.
        for legacy_key in ("search_roots", "exclude", "ignore"):
            self.assertNotIn(legacy_key, out)

    def test_migration_is_idempotent(self):
        once = CFG.normalize(self.LEGACY)
        twice = CFG.normalize(once)
        self.assertEqual(once, twice)
        self.assertEqual(
            json.dumps(once, sort_keys=True), json.dumps(twice, sort_keys=True)
        )

    def test_partially_migrated_config_does_not_double_apply(self):
        # A file carrying BOTH shapes: the nested value wins and the legacy value is not
        # appended onto it, so a half-migrated config cannot duplicate or clobber entries.
        partial = {
            "config_version": 1,
            "search_roots": ["~/legacy-root"],
            "repos": {"search": ["~/new-root"]},
            "ignore": ["*/vendor/*"],
        }
        out = CFG.normalize(partial)
        self.assertEqual(out["repos"]["search"], ["~/new-root"])
        self.assertNotIn("~/legacy-root", out["repos"]["search"])
        # A legacy key with NO nested counterpart still migrates in.
        self.assertEqual(out["repos"]["ignore"], ["*/vendor/*"])

    def test_migration_is_shape_driven_not_version_driven(self):
        # A hand-edited file whose version was bumped but whose keys are still flat must
        # still migrate; deciding on config_version alone would silently drop these.
        stale_version = dict(self.LEGACY)
        stale_version["config_version"] = 2
        out = CFG.normalize(stale_version)
        self.assertEqual(out["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(out["repos"]["installed"], ["~/src/foo", "~/src/bar"])

        # Likewise an UNVERSIONED flat file.
        unversioned = {k: v for k, v in self.LEGACY.items() if k != "config_version"}
        out = CFG.normalize(unversioned)
        self.assertEqual(out["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(out["config_version"], 2)

    def test_nested_repos_ignore_is_not_home_expanded(self):
        # `repos.ignore` holds fnmatch globs, not paths: a leading ~ must not be rewritten.
        out = CFG.normalize({"repos": {"ignore": ["~weird-glob", "*/vendor/*"]}})
        self.assertEqual(out["repos"]["ignore"], ["~weird-glob", "*/vendor/*"])

    def test_normalize_rejects_unknown_repos_subkeys(self):
        out = CFG.normalize({"repos": {"search": ["~/src"], "bogus": ["x"]}})
        self.assertEqual(set(out["repos"]), set(CFG._ALLOWED_REPOS_KEYS))
        self.assertNotIn("bogus", out["repos"])

    def test_normalize_applies_the_top_key_allowlist(self):
        # E-01: `_ALLOWED_TOP_KEYS` must be load-bearing, not dead code. Prove it actually
        # filters by having default_config() emit a key that is not on the allowlist.
        from unittest import mock

        real_default = CFG.default_config

        def leaky_default():
            cfg = real_default()
            cfg["sneaky_key"] = "should-not-survive"
            return cfg

        with mock.patch.object(CFG, "default_config", leaky_default):
            out = CFG.normalize({})
        self.assertNotIn("sneaky_key", out)
        self.assertTrue(set(out) <= CFG._ALLOWED_TOP_KEYS)

    def test_allowlist_matches_the_default_config_shape(self):
        self.assertTrue(set(CFG.default_config()) <= CFG._ALLOWED_TOP_KEYS)
        self.assertNotIn("search_roots", CFG._ALLOWED_TOP_KEYS)
        self.assertIn("repos", CFG._ALLOWED_TOP_KEYS)

    def test_normalize_survives_malformed_repos_value(self):
        for bad in (None, "string", 7, []):
            out = CFG.normalize({"repos": bad})
            self.assertEqual(out["repos"], CFG.default_config()["repos"])


class MigrationOnDiskTests(unittest.TestCase):
    """Lazy on-disk migration and the fail-closed downgrade guard (E-02, E-03)."""

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

    def test_planted_legacy_config_loads_nested_and_survives_a_save(self):
        self._plant(SchemaMigrationTests.LEGACY)
        loaded = CFG.load()
        self.assertEqual(loaded["repos"]["search"], ["~/src", "~/work"])
        self.assertEqual(loaded["repos"]["installed"], ["~/src/foo", "~/src/bar"])
        self.assertEqual(
            loaded["repos"]["exclude"], ["~/src/legacy", "*/never-install/*"]
        )
        self.assertEqual(loaded["repos"]["ignore"], ["*/vendor/*"])

        CFG.save(loaded)
        on_disk = json.loads(CFG.config_path().read_text(encoding="utf-8"))
        self.assertEqual(on_disk["config_version"], 2)
        self.assertEqual(on_disk["repos"]["search"], ["~/src", "~/work"])
        self.assertNotIn("search_roots", on_disk)

    def test_load_does_not_rewrite_the_file(self):
        # Migration is LAZY: a read-only session leaves a v1 file exactly as it was.
        _, planted_text = self._plant(SchemaMigrationTests.LEGACY)
        CFG.load()
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

    def test_future_version_config_is_not_emptied_on_load(self):
        payload = {
            "config_version": 3,
            "repos": {
                "search": ["~/src"],
                "installed": ["~/src/foo"],
                "exclude": ["~/src/never"],
                "ignore": ["*/vendor/*"],
            },
            "some_future_key": {"kept": True},
        }
        self._plant(payload)
        loaded = CFG.load()
        # Passthrough: nothing normalized away, so nothing is lost from view.
        self.assertEqual(loaded["repos"]["search"], ["~/src"])
        self.assertEqual(loaded["repos"]["exclude"], ["~/src/never"])
        self.assertEqual(loaded["config_version"], 3)
        self.assertIn("some_future_key", loaded)

    def test_save_refuses_to_overwrite_a_future_version_config(self):
        payload = {
            "config_version": 3,
            "repos": {"search": ["~/src"], "exclude": ["~/src/never"]},
        }
        _, planted_text = self._plant(payload)

        # Refuses the in-memory future config...
        with self.assertRaises(CFG.ConfigError) as ctx:
            CFG.save(CFG.load())
        self.assertIn(str(CFG.config_path()), str(ctx.exception))

        # ...and also refuses a normal write over a future file on disk.
        with self.assertRaises(CFG.ConfigError) as ctx2:
            CFG.save(CFG.default_config())
        self.assertIn(str(CFG.config_path()), str(ctx2.exception))

        # The file is byte-identical: nothing was destroyed.
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

    def test_future_version_mutating_verb_fails_without_data_loss(self):
        payload = {
            "config_version": 3,
            "repos": {"search": ["~/src"], "exclude": ["~/src/never"]},
        }
        _, planted_text = self._plant(payload)
        with self.assertRaises(CFG.ConfigError):
            CFG.add_config_item("repos.search", "~/other")
        self.assertEqual(CFG.config_path().read_text(encoding="utf-8"), planted_text)

    def test_current_and_older_versions_are_not_treated_as_future(self):
        self.assertFalse(CFG.is_future_version({"config_version": 1}))
        self.assertFalse(CFG.is_future_version({"config_version": 2}))
        self.assertFalse(CFG.is_future_version({}))
        # A non-integer version is treated as v1, not as a future version.
        self.assertFalse(CFG.is_future_version({"config_version": "banana"}))
        self.assertFalse(CFG.is_future_version({"config_version": True}))
        self.assertTrue(CFG.is_future_version({"config_version": 3}))


class NestedRepoKeyVerbTests(unittest.TestCase):
    """get/set/add/remove/is across all four `repos.*` keys, plus the bare-`repos` break (E-04, E-05)."""

    SUBKEYS = ("repos.search", "repos.installed", "repos.exclude", "repos.ignore")

    def test_roundtrip_on_every_repos_subkey(self):
        for key in self.SUBKEYS:
            with self.subTest(key=key):
                cfg = CFG.default_config()
                item = "*/glob-entry/*" if key == "repos.ignore" else "~/src/thing"

                cfg, k, items, added, stored = CFG.add_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertEqual(k, key)
                self.assertTrue(added)
                self.assertEqual(items, [item])

                _, val = CFG.get_config_value(key, cfg)
                self.assertEqual(val, [item])

                _, present, _ = CFG.is_config_item_present(key, item, cfg=cfg)
                self.assertTrue(present)

                cfg, _, items, added, _ = CFG.add_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertFalse(added, "add must be idempotent")
                self.assertEqual(items, [item])

                cfg, _, items, removed, _ = CFG.remove_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertTrue(removed)
                self.assertEqual(items, [])

                _, present, _ = CFG.is_config_item_present(key, item, cfg=cfg)
                self.assertFalse(present)

                cfg, _, _, removed, _ = CFG.remove_config_item(
                    key, item, cfg=cfg, auto_save=False
                )
                self.assertFalse(removed)

    def test_set_config_value_on_every_repos_subkey(self):
        cfg = CFG.default_config()
        for key in self.SUBKEYS:
            with self.subTest(key=key):
                cfg, k, val = CFG.set_config_value(key, "a,b", cfg=cfg, auto_save=False)
                self.assertEqual(k, key)
                self.assertEqual(val, ["a", "b"])
        # Every subkey kept its own value; the writes did not stomp each other.
        for key in self.SUBKEYS:
            _, val = CFG.get_config_value(key, cfg)
            self.assertEqual(val, ["a", "b"])

    def test_set_repos_mapping_rejects_unknown_subkey(self):
        cfg = CFG.default_config()
        with self.assertRaises(CFG.ConfigError) as ctx:
            CFG.set_config_value(
                "repos", {"search": ["~/src"], "bogus": []}, cfg=cfg, auto_save=False
            )
        self.assertIn("bogus", str(ctx.exception))

        cfg, k, val = CFG.set_config_value(
            "repos", {"search": ["~/src"]}, cfg=cfg, auto_save=False
        )
        self.assertEqual(k, "repos")
        self.assertEqual(val["search"], ["~/src"])

    def test_list_verbs_on_bare_repos_name_the_subkeys(self):
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
            self.assertNotIn("it is not a list (type is dict)", msg)

    def test_reading_bare_repos_still_works(self):
        cfg = CFG.default_config()
        CFG.set_repo_setting(cfg, "search", ["~/src"])
        k, val = CFG.get_config_value("repos", cfg)
        self.assertEqual(k, "repos")
        self.assertIsInstance(val, dict)
        self.assertEqual(val["search"], ["~/src"])

    def test_set_repo_setting_rejects_unknown_subkey(self):
        with self.assertRaises(CFG.ConfigError):
            CFG.set_repo_setting(CFG.default_config(), "bogus", [])

    def test_repo_setting_reader_degrades_to_empty(self):
        self.assertEqual(CFG.repo_setting({}, "search"), [])
        self.assertEqual(CFG.repo_setting({"repos": "nonsense"}, "search"), [])
        self.assertEqual(CFG.repo_setting({"repos": {}}, "search"), [])

    def test_accessors_read_the_nested_layout(self):
        cfg = CFG.normalize(SchemaMigrationTests.LEGACY)
        self.assertEqual(
            CFG.expanded_search_roots(cfg),
            [Path.home() / "src", Path.home() / "work"],
        )
        self.assertEqual(
            CFG.expanded_repos(cfg),
            [Path.home() / "src" / "foo", Path.home() / "src" / "bar"],
        )
        self.assertEqual(
            CFG.expanded_excludes(cfg),
            [str(Path.home() / "src" / "legacy"), "*/never-install/*"],
        )
        self.assertEqual(CFG.ignore_patterns(cfg), ["*/vendor/*"])


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

    def test_cli_config_show_single_var(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "show", "defaults.backup"])
        self.assertEqual(rc, 0)
        self.assertIn("defaults.backup", out.getvalue())

        out_json = io.StringIO()
        with redirect_stdout(out_json):
            rc = cli.main(["config", "show", "defaults.backup", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out_json.getvalue())
        self.assertEqual(data["key"], "defaults.backup")
        self.assertTrue(data["value"])

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

    def test_cli_config_add_remove_and_is(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        # Add
        out_add = io.StringIO()
        with redirect_stdout(out_add):
            rc = cli.main(["config", "add", "~/my-test-root", "to", "repos.search"])
        self.assertEqual(rc, 0)
        self.assertIn("Added", out_add.getvalue())

        # Is present
        out_is = io.StringIO()
        with redirect_stdout(out_is):
            rc = cli.main(["config", "is", "~/my-test-root", "in", "repos.search"])
        self.assertEqual(rc, 0)
        self.assertIn("Yes", out_is.getvalue())

        # Remove
        out_rm = io.StringIO()
        with redirect_stdout(out_rm):
            rc = cli.main(
                ["config", "remove", "~/my-test-root", "from", "repos.search"]
            )
        self.assertEqual(rc, 0)
        self.assertIn("Removed", out_rm.getvalue())

        # Is not present (exit 1)
        out_is2 = io.StringIO()
        with redirect_stdout(out_is2):
            rc = cli.main(["config", "is", "~/my-test-root", "in", "repos.search"])
        self.assertEqual(rc, 1)
        self.assertIn("No", out_is2.getvalue())

    def test_cli_conf_alias(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["conf", "show"])
        self.assertEqual(rc, 0)
        self.assertIn("agent-workflows configuration", out.getvalue())

    def test_cli_config_show_groups_sections(self):
        # E-10: nested settings are grouped, and the `repos` container is NOT also printed
        # as a raw mapping (that would show the same data twice).
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "show"])
        self.assertEqual(rc, 0)
        text = out.getvalue()
        self.assertIn("Settings (repos)", text)
        self.assertIn("Settings (defaults)", text)
        for key in (
            "repos.search",
            "repos.installed",
            "repos.exclude",
            "repos.ignore",
        ):
            self.assertIn(key, text)
        self.assertNotIn("'search':", text)
        self.assertEqual(text.count("repos.search"), 1)

    def test_cli_config_show_repos_group_and_subkey(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "show", "repos"])
        self.assertEqual(rc, 0)
        self.assertIn("repos.search", out.getvalue())
        self.assertIn("repos.installed", out.getvalue())

        out_one = io.StringIO()
        with redirect_stdout(out_one):
            rc = cli.main(["config", "show", "repos.search"])
        self.assertEqual(rc, 0)
        self.assertIn("repos.search", out_one.getvalue())
        self.assertNotIn("repos.installed", out_one.getvalue())

        out_json = io.StringIO()
        with redirect_stdout(out_json):
            rc = cli.main(["config", "show", "repos", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out_json.getvalue())
        self.assertEqual(data["key"], "repos")
        self.assertEqual(set(data["value"]), set(CFG._ALLOWED_REPOS_KEYS))

    def test_cli_config_add_remove_and_is_on_repos_subkeys(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        for key in ("repos.search", "repos.installed", "repos.exclude", "repos.ignore"):
            with self.subTest(key=key):
                item = "*/noise/*" if key == "repos.ignore" else "~/my-test-entry"
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = cli.main(["config", "add", item, "to", key])
                self.assertEqual(rc, 0)
                self.assertIn("Added", out.getvalue())
                self.assertIn(item, CFG.load()["repos"][key.split(".", 1)[1]])

                out_is = io.StringIO()
                with redirect_stdout(out_is):
                    rc = cli.main(["config", "is", item, "in", key])
                self.assertEqual(rc, 0)

                out_rm = io.StringIO()
                with redirect_stdout(out_rm):
                    rc = cli.main(["config", "remove", item, "from", key])
                self.assertEqual(rc, 0)
                self.assertIn("Removed", out_rm.getvalue())

                out_is2 = io.StringIO()
                with redirect_stdout(out_is2):
                    rc = cli.main(["config", "is", item, "in", key])
                self.assertEqual(rc, 1)

    def test_cli_config_add_to_bare_repos_is_actionable(self):
        # E-05: the one user-visible break. `aw config add <path> to repos` worked under the
        # flat v1 schema; it must now fail LOUDLY, naming the successor subkey.
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "add", "~/src/foo", "to", "repos"])
        self.assertEqual(rc, 2)
        text = out.getvalue()
        self.assertIn("repos.installed", text)
        self.assertNotIn("it is not a list (type is dict)", text)

    def test_cli_legacy_config_on_disk_is_migrated_by_a_mutating_verb(self):
        from agent_workflows import cli
        import io
        from contextlib import redirect_stdout

        p = CFG.config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(SchemaMigrationTests.LEGACY, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        out = io.StringIO()
        with redirect_stdout(out):
            rc = cli.main(["config", "add", "~/extra-root", "to", "repos.search"])
        self.assertEqual(rc, 0)

        on_disk = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["config_version"], 2)
        self.assertNotIn("search_roots", on_disk)
        self.assertEqual(
            on_disk["repos"]["search"], ["~/src", "~/work", "~/extra-root"]
        )
        self.assertEqual(on_disk["repos"]["installed"], ["~/src/foo", "~/src/bar"])
        self.assertEqual(
            on_disk["repos"]["exclude"], ["~/src/legacy", "*/never-install/*"]
        )
        self.assertEqual(on_disk["repos"]["ignore"], ["*/vendor/*"])


if __name__ == "__main__":
    unittest.main()

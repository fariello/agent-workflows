"""Tests for `agent_workflows.runner_profiles` (runprofile Order 01, `f2mrsw` E-04).

The matrix this suite is REQUIRED to fail on (plan "Required tests / validation"):

  * silent fallback     - a malformed/unsupported config must RAISE, never behave as empty,
                          because behaving as empty launches the host default model.
  * schema widening     - an unknown key, and every forbidden capability key by name, must fail.
  * dangling defaults   - a default reference to a missing/wrong-runner profile must fail, and
                          removing a referenced profile must force an EXPLICIT decision.
  * precedence inversion- an explicit flag must ALWAYS beat a stored `validate` default, and an
                          ABSENT tri-state level must fall THROUGH rather than read as `false`.
  * partial writes      - a fault injected mid-write must leave the previous bytes IDENTICAL.
  * namespace over-reservation - command-LIKE names (`status`, `report`, `run`) stay LEGAL;
                          only the grammar words `as`/`default` are reserved.
  * arbitrary argv      - the module must contain no `shell=True`, `eval`, `exec`, credential
                          field, or persisted command string.

MODEL IDENTIFIERS HERE ARE SYNTHETIC. The orchestrator (`3m0urk`) requires tests to use
synthetic equivalents of the three requested profiles, because one real identifier is
institution-specific and a tracked test is public. `_INHOUSE_MODEL` is shaped like the real
three-segment private identifier (so the grammar is genuinely exercised) without naming any
real gateway.

Stdlib `unittest` only, matching `tests/test_config.py`.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from agent_workflows import runner_profiles as RP

# The three requested profiles, as SYNTHETIC equivalents (see module docstring).
_FLASH_MODEL = "example-vendor/flash-3.7"
_INHOUSE_MODEL = "example-gw/inhouse/pt3-sonnet-5-1m-us"
_SOL_MODEL = "example-openai/gpt-sol-5.6"


def _profile(**kwargs) -> RP.LaunchProfile:
    kwargs.setdefault("runner", "oc")
    kwargs.setdefault("model", _FLASH_MODEL)
    return RP.LaunchProfile(**kwargs)


def _three_requested() -> RP.ProfileConfig:
    cfg = RP.empty_config()
    cfg = RP.add_profile(
        cfg, "gem", RP.LaunchProfile(runner="oc", model=_FLASH_MODEL, variant="high")
    )
    cfg = RP.add_profile(
        cfg,
        "sonnet",
        RP.LaunchProfile(runner="oc", model=_INHOUSE_MODEL, variant="medium"),
    )
    cfg = RP.add_profile(
        cfg, "sol", RP.LaunchProfile(runner="oc", model=_SOL_MODEL, variant="medium")
    )
    return cfg


# ==================================================================================================
# E-01 / V-01: schema, records, names, runner canonicalization
# ==================================================================================================


class RequestedProfilesParseTests(unittest.TestCase):
    """The three requested profiles must round-trip through the schema."""

    def test_three_requested_profiles_parse_and_round_trip(self):
        cfg = _three_requested()
        reparsed = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(sorted(reparsed.profiles), ["gem", "sol", "sonnet"])
        self.assertEqual(reparsed.get("gem").model, _FLASH_MODEL)
        self.assertEqual(reparsed.get("gem").variant, "high")
        self.assertEqual(reparsed.get("sonnet").model, _INHOUSE_MODEL)
        self.assertEqual(reparsed.get("sol").variant, "medium")
        self.assertEqual(reparsed.to_document(), cfg.to_document())
        print("three requested profiles round-trip:", sorted(reparsed.profiles))

    def test_records_are_immutable(self):
        cfg = _three_requested()
        with self.assertRaises(Exception):
            cfg.profiles["gem"].model = "other/model"  # type: ignore[misc]
        with self.assertRaises(Exception):
            cfg.profiles["nope"] = _profile()  # type: ignore[index]

    def test_optional_fields_are_omitted_not_nulled(self):
        doc = _profile().to_document()
        self.assertEqual(doc, {"runner": "oc", "model": _FLASH_MODEL})
        self.assertNotIn("variant", doc)
        self.assertNotIn("validate", doc)


class ProfileNameGrammarTests(unittest.TestCase):
    """Names: bounded kebab-ish grammar, `as`/`default` reserved, command-like names LEGAL."""

    def test_command_like_names_are_legal(self):
        # V-01 explicitly: over-reserving the namespace is a defect, because a name is only
        # resolved AFTER `as` and therefore cannot shadow a subcommand.
        for name in (
            "status",
            "report",
            "run",
            "show",
            "evidence",
            "start",
            "verify-ledger",
        ):
            with self.subTest(name=name):
                self.assertEqual(RP.validate_profile_name(name), name)
        print(
            "command-like names legal: status, report, run, show, evidence, start, verify-ledger"
        )

    def test_grammar_words_are_reserved(self):
        for name in ("as", "default"):
            with self.subTest(name=name):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.validate_profile_name(name)
                self.assertIn("reserved", str(ctx.exception))
        print("reserved by the grammar: as, default")

    def test_invalid_names_are_rejected(self):
        cases = {
            "empty": "",
            "leading-digit": "1gem",
            "leading-hyphen": "-gem",
            "uppercase": "Gem",
            "underscore": "my_gem",
            "space": "my gem",
            "dot": "gem.1",
            "slash": "a/b",
            "too-long": "g" * (RP.MAX_PROFILE_NAME_LEN + 1),
            "shell-metachar": "gem;rm",
            "not-a-string": 7,
        }
        for label, value in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.validate_profile_name(value)

    def test_max_length_boundary_is_inclusive(self):
        ok = "g" * RP.MAX_PROFILE_NAME_LEN
        self.assertEqual(RP.validate_profile_name(ok), ok)


class RunnerCanonicalizationTests(unittest.TestCase):
    def test_opencode_canonicalizes_to_oc(self):
        self.assertEqual(RP.canonical_runner("opencode"), "oc")
        self.assertEqual(RP.canonical_runner("OpenCode"), "oc")
        self.assertEqual(RP.canonical_runner("oc"), "oc")
        print("canonicalization: opencode/OpenCode/oc -> oc")

    def test_only_registered_runners_are_accepted(self):
        self.assertEqual(sorted(RP.RUNNER_REGISTRY), ["oc"])
        for name in ("agy", "antigravity", "codex", "claude", "", None, 3):
            with self.subTest(runner=name):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.canonical_runner(name)
        print(
            "version 1 registers exactly: ['oc']; agy/codex/claude refused (no parity claim)"
        )

    def test_profile_runner_is_stored_canonicalized(self):
        cfg = RP.add_profile(RP.empty_config(), "gem", _profile(runner="opencode"))
        self.assertEqual(cfg.get("gem").runner, "oc")


class ModelAndFieldValidationTests(unittest.TestCase):
    def test_exact_provider_model_is_required(self):
        for label, value in {
            "missing-provider": "flash-3.7",
            "empty": "",
            "trailing-slash": "vendor/",
            "leading-slash": "/model",
            "double-slash": "vendor//model",
            "whitespace": "vendor/mo del",
            "quote": 'vendor/mo"del',
            "backtick": "vendor/`id`",
            "dollar": "vendor/$MODEL",
            "semicolon": "vendor/model;whoami",
            "pipe": "vendor/model|tee",
            "backslash": "vendor\\model",
            "too-long": "vendor/" + "m" * RP.MAX_MODEL_LEN,
            "not-a-string": 5,
            "none": None,
        }.items():
            with self.subTest(case=label):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.validate_model(value)

    def test_multi_segment_private_shape_is_accepted(self):
        self.assertEqual(RP.validate_model(_INHOUSE_MODEL), _INHOUSE_MODEL)

    def test_missing_required_fields_fail(self):
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile("gem", {"model": _FLASH_MODEL})
        self.assertIn("runner", str(ctx.exception))
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile("gem", {"runner": "oc"})
        self.assertIn("model", str(ctx.exception))

    def test_variant_and_agent_are_bounded_tokens(self):
        good = RP.parse_profile(
            "gem",
            {
                "runner": "oc",
                "model": _FLASH_MODEL,
                "variant": "high",
                "agent": "build",
            },
        )
        self.assertEqual((good.variant, good.agent), ("high", "build"))
        for field_name, value in (
            ("variant", "high; rm -rf /"),
            ("variant", ""),
            ("variant", 1),
            ("agent", "a b"),
            ("agent", "x" * (RP.MAX_FIELD_LEN + 1)),
        ):
            with self.subTest(field=field_name, value=value):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.parse_profile(
                        "gem",
                        {"runner": "oc", "model": _FLASH_MODEL, field_name: value},
                    )


class ForbiddenAndUnknownFieldTests(unittest.TestCase):
    """Schema widening must fail: no argv, env, prompt, permission, token, or API-key fields."""

    def test_every_forbidden_capability_field_is_refused_by_name(self):
        refused = []
        for key in sorted(RP.FORBIDDEN_PROFILE_KEYS):
            with self.subTest(key=key):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.parse_profile(
                        "gem", {"runner": "oc", "model": _FLASH_MODEL, key: "anything"}
                    )
                self.assertIn("BY DESIGN", str(ctx.exception))
                refused.append(key)
        # The categories the plan names explicitly must all be present.
        for required in (
            "args",
            "argv",
            "env",
            "environment",
            "executable",
            "prompt",
            "permissions",
            "token",
            "api_key",
            "shell",
            "command",
            "secret",
        ):
            self.assertIn(required, refused)
        print(f"forbidden-by-name fields refused ({len(refused)}): {refused}")

    def test_unknown_field_is_refused(self):
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile(
                "gem", {"runner": "oc", "model": _FLASH_MODEL, "temperature": 0.2}
            )
        self.assertIn("unknown field", str(ctx.exception))

    def test_unknown_document_and_defaults_keys_are_refused(self):
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document({"schema_version": 1, "profiles": {}, "extra": 1})
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document(
                {"schema_version": 1, "profiles": {}, "defaults": {"token": "abc"}}
            )

    def test_a_credential_can_never_be_persisted(self):
        cfg = RP.add_profile(RP.empty_config(), "gem", _profile())
        text = RP.dumps(cfg)
        for word in (
            "token",
            "api_key",
            "secret",
            "password",
            "Authorization",
            "Bearer",
        ):
            self.assertNotIn(word, text)
        print("serialized document contains no credential-shaped field")


class DocumentValidationTests(unittest.TestCase):
    def test_schema_version_is_required_and_typed(self):
        for raw in (
            {},
            {"schema_version": "1"},
            {"schema_version": True},
            {"schema_version": 1.0},
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.from_document(raw)

    def test_unsupported_version_fails_closed_and_says_why(self):
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.from_document({"schema_version": 99, "profiles": {}})
        message = str(ctx.exception)
        self.assertIn("unsupported schema_version 99", message)
        self.assertIn("wrong model", message)
        print(f"unsupported version fails closed: {message.splitlines()[0]}")

    def test_non_object_document_and_sections_fail(self):
        for raw in ([], "x", 3, None):
            with self.subTest(raw=raw):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.from_document(raw)
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document({"schema_version": 1, "profiles": []})
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document({"schema_version": 1, "profiles": {}, "defaults": []})
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document(
                {"schema_version": 1, "profiles": {}, "defaults": {"profiles": []}}
            )


class TriStateValidateFieldTests(unittest.TestCase):
    """`validate` is present-true / present-false / ABSENT; absent is NOT false."""

    def test_absent_stays_none(self):
        self.assertIsNone(
            RP.parse_profile("gem", {"runner": "oc", "model": _FLASH_MODEL}).validate
        )

    def test_present_false_is_preserved_and_serialized(self):
        profile = RP.parse_profile(
            "gem", {"runner": "oc", "model": _FLASH_MODEL, "validate": False}
        )
        self.assertIs(profile.validate, False)
        self.assertIn("validate", profile.to_document())
        # Absent must NOT be serialized, so absent and present-false stay distinguishable.
        self.assertNotIn("validate", _profile().to_document())
        print("tri-state preserved: present-false serialized, absent omitted")

    def test_non_boolean_validate_is_refused(self):
        for value in ("true", 1, 0, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.parse_profile(
                        "gem",
                        {"runner": "oc", "model": _FLASH_MODEL, "validate": value},
                    )

    def test_defaults_validate_tri_state(self):
        cfg = RP.from_document(
            {"schema_version": 1, "profiles": {}, "defaults": {"validate": False}}
        )
        self.assertIs(cfg.validate, False)
        self.assertIsNone(
            RP.from_document({"schema_version": 1, "profiles": {}}).validate
        )


# ==================================================================================================
# E-02 / V-02: the XDG-backed atomic store
# ==================================================================================================


class StorePathTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("XDG_CONFIG_HOME")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old

    def test_honors_xdg_config_home(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["XDG_CONFIG_HOME"] = d
            self.assertEqual(RP.store_dir(), Path(d) / "agent-workflows")
            self.assertEqual(
                RP.store_path(), Path(d) / "agent-workflows" / "runner-profiles.json"
            )
            print(f"store path under XDG: .../agent-workflows/{RP.STORE_NAME}")

    def test_falls_back_to_home_config(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.assertEqual(RP.store_dir(), Path.home() / ".config" / "agent-workflows")
        self.assertNotEqual(RP.store_dir(), Path.home())

    def test_is_separate_from_the_main_config_and_not_in_the_repo(self):
        from agent_workflows import config as CFG

        with tempfile.TemporaryDirectory() as d:
            os.environ["XDG_CONFIG_HOME"] = d
            self.assertNotEqual(RP.store_path(), CFG.config_path())
            self.assertEqual(RP.store_path().parent, CFG.config_dir())
            repo_root = Path(RP.__file__).resolve().parent.parent
            self.assertFalse(str(RP.store_path()).startswith(str(repo_root)))
            print(
                "separate from config.json, inside the user config dir, never in the repo tree"
            )


class StoreReadWriteTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "runner-profiles.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_absent_is_distinct_from_malformed(self):
        absent = RP.load(self.path)
        self.assertFalse(absent.present)
        self.assertEqual(dict(absent.profiles), {})
        self.assertEqual(absent.source, self.path)

        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.load(self.path)
        self.assertIn("not treated as", str(ctx.exception).lower())
        print(
            "absent -> empty(present=False); malformed -> ProfileSchemaError, never empty"
        )

    def test_malformed_shapes_all_raise_rather_than_degrade(self):
        for label, text in {
            "unsupported-version": '{"schema_version": 42, "profiles": {}}',
            "unknown-key": '{"schema_version": 1, "profiles": {}, "argv": ["x"]}',
            "bad-profile": '{"schema_version": 1, "profiles": {"gem": {"runner": "oc"}}}',
            "dangling-default": (
                '{"schema_version": 1, "profiles": {}, '
                '"defaults": {"profiles": {"oc": "ghost"}}}'
            ),
            "json-array": "[]",
        }.items():
            with self.subTest(case=label):
                self.path.write_text(text, encoding="utf-8")
                with self.assertRaises(RP.RunnerProfileError):
                    RP.load(self.path)

    def test_save_then_load_round_trips_with_deterministic_bytes(self):
        cfg = RP.set_default_profile(_three_requested(), "gem")
        RP.save(cfg, self.path)
        first = self.path.read_bytes()
        RP.save(RP.load(self.path), self.path)
        self.assertEqual(first, self.path.read_bytes())
        loaded = RP.load(self.path)
        self.assertTrue(loaded.present)
        self.assertEqual(loaded.default_profile_for("oc"), "gem")
        self.assertEqual(loaded.digest, cfg.digest)
        print(f"deterministic bytes; digest {loaded.digest[:16]}...")

    def test_digest_changes_with_content_and_is_stable_otherwise(self):
        cfg = _three_requested()
        same = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(cfg.digest, same.digest)
        changed = RP.add_profile(cfg, "extra", _profile())
        self.assertNotEqual(cfg.digest, changed.digest)

    def test_save_creates_the_parent_directory(self):
        nested = Path(self._tmp.name) / "a" / "b" / "runner-profiles.json"
        RP.save(_three_requested(), nested)
        self.assertTrue(nested.is_file())

    def test_save_validates_the_whole_document_before_writing(self):
        RP.save(_three_requested(), self.path)
        before = self.path.read_bytes()
        # A hand-built record that bypassed the mutators is still validated at save time.
        smuggled = RP.ProfileConfig(
            profiles={
                "gem": RP.LaunchProfile(runner="oc", model="not-a-provider-model")
            }
        )
        with self.assertRaises(RP.ProfileSchemaError):
            RP.save(smuggled, self.path)
        self.assertEqual(before, self.path.read_bytes())
        print("invalid document refused at save; previous bytes unchanged")

    def test_refuses_to_overwrite_a_future_version(self):
        self.path.write_text(
            '{"schema_version": 99, "profiles": {}}\n', encoding="utf-8"
        )
        before = self.path.read_bytes()
        with self.assertRaises(RP.ProfileStoreError) as ctx:
            RP.save(_three_requested(), self.path)
        self.assertIn("Nothing was changed", str(ctx.exception))
        self.assertEqual(before, self.path.read_bytes())

    def test_no_leftover_temp_files_after_a_successful_write(self):
        RP.save(_three_requested(), self.path)
        leftovers = [
            p.name for p in self.path.parent.iterdir() if p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [])


class AtomicFaultInjectionTests(unittest.TestCase):
    """An interrupted replacement must leave the PREVIOUS bytes byte-identical."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "runner-profiles.json"
        RP.save(_three_requested(), self.path)
        self.before = self.path.read_bytes()

    def tearDown(self):
        self._tmp.cleanup()

    def test_fault_during_replace_preserves_prior_bytes_and_cleans_up(self):
        real_replace = os.replace

        def boom(src, dst):  # noqa: ANN001 - test double
            raise OSError(5, "injected I/O error")

        os.replace = boom
        try:
            with self.assertRaises(RP.ProfileStoreError):
                RP.save(
                    RP.add_profile(RP.load(self.path), "new", _profile()), self.path
                )
        finally:
            os.replace = real_replace

        self.assertEqual(self.before, self.path.read_bytes())
        leftovers = [
            p.name for p in self.path.parent.iterdir() if p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [], f"temp file leaked: {leftovers}")
        # And the file is still loadable, which is the property that actually matters.
        self.assertEqual(sorted(RP.load(self.path).profiles), ["gem", "sol", "sonnet"])
        print(
            "fault injected at os.replace: prior bytes identical, no temp leak, still loadable"
        )

    def test_fault_during_write_preserves_prior_bytes(self):
        real_fdopen = os.fdopen

        def boom(fd, *a, **kw):  # noqa: ANN001 - test double
            os.close(fd)
            raise OSError(28, "injected no space left on device")

        os.fdopen = boom
        try:
            with self.assertRaises(RP.ProfileStoreError):
                RP.save(
                    RP.add_profile(RP.load(self.path), "new", _profile()), self.path
                )
        finally:
            os.fdopen = real_fdopen

        self.assertEqual(self.before, self.path.read_bytes())
        leftovers = [
            p.name for p in self.path.parent.iterdir() if p.name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [])

    def test_a_keyboardinterrupt_mid_write_is_not_swallowed(self):
        real_fdopen = os.fdopen

        def boom(fd, *a, **kw):  # noqa: ANN001 - test double
            os.close(fd)
            raise KeyboardInterrupt

        os.fdopen = boom
        try:
            with self.assertRaises(KeyboardInterrupt):
                RP.save(RP.load(self.path), self.path)
        finally:
            os.fdopen = real_fdopen
        self.assertEqual(self.before, self.path.read_bytes())


# ==================================================================================================
# E-03 / V-03: mutations and resolution
# ==================================================================================================


class MutationTests(unittest.TestCase):
    def test_add_is_pure_and_refuses_a_silent_duplicate(self):
        base = RP.empty_config()
        one = RP.add_profile(base, "gem", _profile())
        self.assertEqual(dict(base.profiles), {}, "add must not mutate its input")
        with self.assertRaises(RP.ProfileExistsError):
            RP.add_profile(one, "gem", _profile(model=_SOL_MODEL))
        replaced = RP.add_profile(one, "gem", _profile(model=_SOL_MODEL), replace=True)
        self.assertEqual(replaced.get("gem").model, _SOL_MODEL)
        self.assertEqual(one.get("gem").model, _FLASH_MODEL)
        print("add: pure, duplicate refused, --replace honored")

    def test_add_validates_through_the_schema(self):
        with self.assertRaises(RP.ProfileSchemaError):
            RP.add_profile(RP.empty_config(), "As", _profile())
        with self.assertRaises(RP.ProfileSchemaError):
            RP.add_profile(
                RP.empty_config(),
                "gem",
                RP.LaunchProfile(runner="oc", model="bare-model"),
            )

    def test_remove_unknown_raises(self):
        with self.assertRaises(RP.ProfileNotFoundError):
            RP.remove_profile(_three_requested(), "ghost")

    def test_removing_a_referenced_default_requires_an_explicit_decision(self):
        cfg = RP.set_default_profile(_three_requested(), "gem")
        with self.assertRaises(RP.ProfileResolutionError) as ctx:
            RP.remove_profile(cfg, "gem")
        self.assertIn("Decide explicitly", str(ctx.exception))

        cleared = RP.remove_profile(cfg, "gem", clear_default=True)
        self.assertIsNone(cleared.default_profile_for("oc"))
        replaced = RP.remove_profile(cfg, "gem", replacement="sol")
        self.assertEqual(replaced.default_profile_for("oc"), "sol")
        with self.assertRaises(RP.ProfileNotFoundError):
            RP.remove_profile(cfg, "gem", replacement="ghost")
        with self.assertRaises(RP.ProfileResolutionError):
            RP.remove_profile(cfg, "gem", clear_default=True, replacement="sol")
        print("referenced default: refuse / clear / replace, each explicit")

    def test_removing_an_unreferenced_profile_is_straightforward(self):
        cfg = RP.set_default_profile(_three_requested(), "gem")
        after = RP.remove_profile(cfg, "sol")
        self.assertEqual(sorted(after.profiles), ["gem", "sonnet"])
        self.assertEqual(after.default_profile_for("oc"), "gem")

    def test_default_profile_setters(self):
        cfg = RP.set_default_profile(_three_requested(), "sonnet")
        self.assertEqual(cfg.default_profile_for("oc"), "sonnet")
        self.assertEqual(cfg.default_profile_for("opencode"), "sonnet")
        cleared = RP.clear_default_profile(cfg, "opencode")
        self.assertIsNone(cleared.default_profile_for("oc"))
        # Idempotent.
        self.assertIsNone(
            RP.clear_default_profile(cleared, "oc").default_profile_for("oc")
        )
        with self.assertRaises(RP.ProfileNotFoundError):
            RP.set_default_profile(_three_requested(), "ghost")

    def test_default_runner_setter_canonicalizes_and_clears(self):
        cfg = RP.set_default_runner(RP.empty_config(), "opencode")
        self.assertEqual(cfg.default_runner, "oc")
        self.assertIsNone(RP.set_default_runner(cfg, None).default_runner)
        with self.assertRaises(RP.ProfileSchemaError):
            RP.set_default_runner(cfg, "agy")

    def test_validate_default_setter_supports_unset(self):
        cfg = RP.set_validate_default(RP.empty_config(), True)
        self.assertIs(cfg.validate, True)
        self.assertIs(RP.set_validate_default(cfg, False).validate, False)
        self.assertIsNone(RP.set_validate_default(cfg, None).validate)
        with self.assertRaises(RP.ProfileSchemaError):
            RP.set_validate_default(cfg, "yes")  # type: ignore[arg-type] - negative test

    def test_a_dangling_default_cannot_be_constructed_through_the_mutators(self):
        cfg = RP.set_default_profile(_three_requested(), "gem")
        # Direct construction is validated too, so no path produces a dangling reference.
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document(
                {
                    "schema_version": 1,
                    "profiles": {"sol": {"runner": "oc", "model": _SOL_MODEL}},
                    "defaults": {"profiles": {"oc": "gem"}},
                }
            )
        self.assertEqual(cfg.default_profile_for("oc"), "gem")


class ResolutionPrecedenceTests(unittest.TestCase):
    """Launch precedence: explicit > named profile > per-runner default > host default."""

    def setUp(self):
        self.cfg = RP.set_default_profile(_three_requested(), "gem")

    def test_explicit_fields_beat_a_named_profile(self):
        got = RP.resolve(
            self.cfg,
            runner="oc",
            profile="sol",
            model=_FLASH_MODEL,
            variant="low",
            agent="plan",
        )
        self.assertEqual(
            (got.model, got.variant, got.agent), (_FLASH_MODEL, "low", "plan")
        )
        self.assertEqual(got.provenance["model"], RP.PROVENANCE_EXPLICIT)
        self.assertEqual(got.provenance["variant"], RP.PROVENANCE_EXPLICIT)
        print("tier 1 explicit:", dict(got.provenance))

    def test_a_named_profile_beats_the_per_runner_default(self):
        got = RP.resolve(self.cfg, runner="oc", profile="sol")
        self.assertEqual(got.model, _SOL_MODEL)
        self.assertEqual(got.applied_profile, "sol")
        self.assertEqual(got.provenance["model"], RP.PROVENANCE_PROFILE)
        print("tier 2 named profile:", got.applied_profile, dict(got.provenance))

    def test_the_per_runner_default_applies_when_no_profile_is_named(self):
        got = RP.resolve(self.cfg, runner="oc")
        self.assertIsNone(got.requested_profile)
        self.assertEqual(got.applied_profile, "gem")
        self.assertEqual(got.model, _FLASH_MODEL)
        self.assertEqual(got.provenance["model"], RP.PROVENANCE_DEFAULT_PROFILE)
        print("tier 3 per-runner default:", got.applied_profile, dict(got.provenance))

    def test_host_default_when_nothing_is_configured(self):
        got = RP.resolve(RP.empty_config(), runner="oc")
        self.assertIsNone(got.model)
        self.assertIsNone(got.variant)
        self.assertIsNone(got.agent)
        self.assertIsNone(got.applied_profile)
        self.assertEqual(got.provenance["model"], RP.PROVENANCE_HOST_DEFAULT)
        print(
            "tier 4 host default: no model/variant/agent argument, recorded as host-default"
        )

    def test_partial_explicit_override_keeps_the_other_profile_fields(self):
        cfg = RP.add_profile(
            self.cfg, "full", _profile(variant="high", agent="build"), replace=False
        )
        got = RP.resolve(cfg, runner="oc", profile="full", variant="low")
        self.assertEqual(got.variant, "low")
        self.assertEqual(got.agent, "build")
        self.assertEqual(got.provenance["variant"], RP.PROVENANCE_EXPLICIT)
        self.assertEqual(got.provenance["agent"], RP.PROVENANCE_PROFILE)

    def test_generic_dispatch_requires_default_runner(self):
        with self.assertRaises(RP.ProfileResolutionError) as ctx:
            RP.resolve(self.cfg, generic=True)
        self.assertIn("does not guess", str(ctx.exception))
        routed = RP.resolve(RP.set_default_runner(self.cfg, "oc"), generic=True)
        self.assertEqual(routed.runner, "oc")
        self.assertEqual(routed.provenance["runner"], RP.PROVENANCE_DEFAULT_RUNNER)
        print(
            "generic dispatch: no default_runner -> refuse; configured -> route to oc"
        )

    def test_generic_dispatch_with_a_named_profile_needs_no_default_runner(self):
        got = RP.resolve(self.cfg, generic=True, profile="sol")
        self.assertEqual(got.runner, "oc")
        self.assertEqual(got.provenance["runner"], RP.PROVENANCE_PROFILE)

    def test_resolve_without_a_runner_or_generic_is_a_typed_error(self):
        with self.assertRaises(RP.ProfileResolutionError):
            RP.resolve(self.cfg)

    def test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back(self):
        with self.assertRaises(RP.ProfileNotFoundError):
            RP.resolve(self.cfg, runner="oc", profile="ghost")
        with self.assertRaises(RP.ProfileSchemaError):
            RP.resolve(self.cfg, runner="agy", profile="gem")
        with self.assertRaises(RP.ProfileSchemaError):
            RP.resolve(self.cfg, runner="oc", profile="As")
        print("unknown profile / unregistered runner: raise, never silently fall back")

    def test_explicit_field_values_are_validated_at_resolution(self):
        for field_name, value in (
            ("model", "bare-model"),
            ("variant", "high; whoami"),
            ("agent", "a b"),
        ):
            with self.subTest(field=field_name, value=value):
                kwargs = {field_name: value}
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.resolve(self.cfg, runner="oc", **kwargs)  # type: ignore[arg-type]

    def test_a_command_like_profile_name_resolves_normally(self):
        cfg = RP.add_profile(self.cfg, "status", _profile(model=_SOL_MODEL))
        got = RP.resolve(cfg, runner="oc", profile="status")
        self.assertEqual(got.model, _SOL_MODEL)
        print("profile named 'status' resolves after `as`, shadowing nothing")


class ResolvedProvenanceRecordTests(unittest.TestCase):
    def test_resolved_record_carries_the_full_auditable_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runner-profiles.json"
            cfg = RP.set_default_profile(_three_requested(), "gem")
            cfg = RP.add_profile(
                cfg, "agentful", _profile(variant="high", agent="build")
            )
            RP.save(cfg, path)
            loaded = RP.load(path)
            got = RP.resolve(loaded, runner="oc", profile="agentful")

        self.assertEqual(got.requested_profile, "agentful")
        self.assertEqual(got.applied_profile, "agentful")
        self.assertIsNotNone(got.config_source)
        self.assertEqual(got.config_source, str(path))
        self.assertTrue(got.config_present)
        self.assertRegex(got.config_digest, r"^[0-9a-f]{64}$")
        self.assertEqual(
            sorted(got.provenance), ["agent", "model", "runner", "validate", "variant"]
        )
        for key, value in got.provenance.items():
            self.assertIn(value, RP.PROVENANCE_VALUES, f"{key} -> {value}")
        print(
            "resolved record: "
            + json.dumps(
                {
                    "requested_profile": got.requested_profile,
                    "applied_profile": got.applied_profile,
                    "config_source": Path(got.config_source or "").name,
                    "config_digest": got.config_digest[:16] + "...",
                    "runner": got.runner,
                    "model": got.model,
                    "variant": got.variant,
                    "agent": got.agent,
                    "validate": got.validate,
                    "provenance": dict(got.provenance),
                },
                sort_keys=True,
            )
        )

    def test_provenance_mapping_is_read_only(self):
        got = RP.resolve(_three_requested(), runner="oc", profile="gem")
        with self.assertRaises(TypeError):
            got.provenance["model"] = "explicit"  # type: ignore[index]


class ValidatePrecedenceMatrixTests(unittest.TestCase):
    """One named case per level, plus fall-through, plus the measured Opus/Gemini shape.

    An unstated precedence is how backlog `vju5ba` happened; a stored default beating an
    explicit flag would reproduce it inverted and make the flag a lie.
    """

    def _cfg(self, profile_validate=None, defaults_validate=None):
        cfg = RP.add_profile(
            RP.empty_config(), "p", _profile(validate=profile_validate)
        )
        if defaults_validate is not None:
            cfg = RP.set_validate_default(cfg, defaults_validate)
        return cfg

    def test_level_1_explicit_flag_wins_over_everything(self):
        cases = []
        for profile_validate in (True, False, None):
            for defaults_validate in (True, False, None):
                for flag in (True, False):
                    cfg = self._cfg(profile_validate, defaults_validate)
                    got = RP.resolve(cfg, runner="oc", profile="p", validate=flag)
                    self.assertIs(
                        got.validate,
                        flag,
                        f"explicit flag {flag} must win over profile={profile_validate} "
                        f"defaults={defaults_validate}",
                    )
                    self.assertEqual(got.provenance["validate"], RP.PROVENANCE_EXPLICIT)
                    cases.append(
                        (flag, profile_validate, defaults_validate, got.validate)
                    )
        print(f"level 1: explicit flag won all {len(cases)} combinations")

    def test_level_2_profile_beats_defaults(self):
        for profile_validate in (True, False):
            for defaults_validate in (True, False):
                with self.subTest(profile=profile_validate, defaults=defaults_validate):
                    got = RP.resolve(
                        self._cfg(profile_validate, defaults_validate),
                        runner="oc",
                        profile="p",
                    )
                    self.assertIs(got.validate, profile_validate)
                    self.assertEqual(got.provenance["validate"], RP.PROVENANCE_PROFILE)
        print(
            "level 2: profile `validate` beat `defaults.validate` in all 4 combinations"
        )

    def test_level_3_defaults_beats_the_shipped_default(self):
        for defaults_validate in (True, False):
            with self.subTest(defaults=defaults_validate):
                got = RP.resolve(
                    self._cfg(None, defaults_validate), runner="oc", profile="p"
                )
                self.assertIs(got.validate, defaults_validate)
                self.assertEqual(got.provenance["validate"], RP.PROVENANCE_DEFAULTS)
        print("level 3: `defaults.validate` beat the shipped default (both polarities)")

    def test_level_4_shipped_default_applies_when_no_level_specified(self):
        got = RP.resolve(self._cfg(None, None), runner="oc", profile="p")
        self.assertIs(got.validate, RP.SHIPPED_VALIDATE_DEFAULT)
        self.assertIs(RP.SHIPPED_VALIDATE_DEFAULT, False)
        self.assertEqual(got.provenance["validate"], RP.PROVENANCE_SHIPPED)
        print(
            f"level 4: shipped default {RP.SHIPPED_VALIDATE_DEFAULT} (matches --validate today)"
        )

    def test_absent_falls_through_and_is_never_read_as_false(self):
        # THE LOAD-BEARING CASE. Profile absent + defaults TRUE must resolve TRUE. If absent
        # were coerced to False at parse time, this would resolve False and the user's
        # `defaults.validate: true` would be silently dead.
        got = RP.resolve(self._cfg(None, True), runner="oc", profile="p")
        self.assertIs(got.validate, True)
        self.assertEqual(got.provenance["validate"], RP.PROVENANCE_DEFAULTS)
        # And present-false must NOT fall through: it is a decision, not an absence.
        got_false = RP.resolve(self._cfg(False, True), runner="oc", profile="p")
        self.assertIs(got_false.validate, False)
        self.assertEqual(got_false.provenance["validate"], RP.PROVENANCE_PROFILE)
        print(
            "absent falls through (None+defaults=True -> True); present-false does not"
        )

    def test_the_default_profile_also_supplies_validate(self):
        cfg = RP.add_profile(RP.empty_config(), "gem", _profile(validate=True))
        cfg = RP.set_default_profile(cfg, "gem")
        got = RP.resolve(cfg, runner="oc")
        self.assertIs(got.validate, True)
        self.assertEqual(got.provenance["validate"], RP.PROVENANCE_DEFAULT_PROFILE)

    def test_two_profiles_differing_only_in_validate_resolve_differently(self):
        # The measured Opus-off / Gemini-on shape, end to end from ONE command line.
        cfg = RP.empty_config()
        cfg = RP.add_profile(
            cfg, "strong", _profile(model=_INHOUSE_MODEL, validate=False)
        )
        cfg = RP.add_profile(cfg, "cheap", _profile(model=_FLASH_MODEL, validate=True))
        strong = RP.resolve(cfg, runner="oc", profile="strong")
        cheap = RP.resolve(cfg, runner="oc", profile="cheap")
        self.assertIs(strong.validate, False)
        self.assertIs(cheap.validate, True)
        self.assertEqual(strong.provenance["validate"], RP.PROVENANCE_PROFILE)
        self.assertEqual(cheap.provenance["validate"], RP.PROVENANCE_PROFILE)
        print(
            f"same command line, different verification decision: strong={strong.validate} "
            f"cheap={cheap.validate}"
        )


class NoSilentFallbackTests(unittest.TestCase):
    """The costly failure mode: a broken config must never quietly become the host default."""

    def test_a_broken_file_never_resolves_to_the_host_default(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runner-profiles.json"
            path.write_text(
                '{"schema_version": 1, "profiles": {"gem": 3}}', encoding="utf-8"
            )
            with self.assertRaises(RP.ProfileSchemaError):
                RP.load(path)
        print(
            "broken config raises at load; no code path resolves it to a host default"
        )

    def test_an_absent_file_is_a_legitimate_empty_config(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = RP.load(Path(d) / "runner-profiles.json")
            got = RP.resolve(cfg, runner="oc")
            self.assertIsNone(got.model)
            self.assertFalse(got.config_present)


# ==================================================================================================
# E-04 / V-04: source audit (no shell, no eval/exec, no arbitrary command execution)
# ==================================================================================================


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        import ast

        self.source = Path(RP.__file__).read_text(encoding="utf-8")
        # Audit EXECUTABLE code only. Comments and docstrings are excluded deliberately and
        # by structure (an AST walk over string-literal statements), not by a substring
        # heuristic: the module's own docstring says the words "subprocess" and "shell" while
        # explaining that it uses neither, and a prose mention must not read as a violation.
        prose_lines = set()
        for node in ast.walk(ast.parse(self.source)):
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                end = node.end_lineno or node.lineno
                prose_lines.update(range(node.lineno, end + 1))
        self.code_lines = [
            line
            for number, line in enumerate(self.source.splitlines(), start=1)
            if line.strip()
            and not line.strip().startswith("#")
            and number not in prose_lines
        ]
        self.assertGreater(len(self.code_lines), 200, "the audit must not be vacuous")

    def test_no_shell_true_no_eval_no_exec_no_subprocess(self):
        found = []
        for pattern in (
            r"shell\s*=\s*True",
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"\bsubprocess\b",
            r"\bos\.system\b",
            r"\bos\.popen\b",
            r"\bos\.exec",
            r"\b__import__\s*\(",
        ):
            for line in self.code_lines:
                if re.search(pattern, line):
                    found.append((pattern, line.strip()))
        self.assertEqual(
            found, [], f"prohibited construct in runner_profiles.py: {found}"
        )
        print(
            "source audit: no shell=True, eval(, exec(, subprocess, os.system/popen/exec*"
        )

    def test_module_imports_only_the_stdlib_and_one_first_party_helper(self):
        import ast

        tree = ast.parse(self.source)
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        self.assertEqual(
            modules,
            {
                "__future__",
                "hashlib",
                "json",
                "os",
                "re",
                "tempfile",
                "dataclasses",
                "pathlib",
                "types",
                "typing",
                "agent_workflows",
            },
            f"unexpected imports: {sorted(modules)}",
        )

    def test_no_arbitrary_argv_or_credential_field_is_persistable(self):
        # The ALLOWED sets are the whole storable surface; assert them literally so widening
        # them requires editing this test and stating why.
        self.assertEqual(
            sorted(RP.ALLOWED_PROFILE_KEYS),
            ["agent", "model", "runner", "validate", "variant"],
        )
        self.assertEqual(
            sorted(RP.ALLOWED_DOCUMENT_KEYS),
            ["default_runner", "defaults", "profiles", "schema_version"],
        )
        self.assertEqual(sorted(RP.ALLOWED_DEFAULTS_KEYS), ["profiles", "validate"])
        self.assertEqual(
            RP.ALLOWED_PROFILE_KEYS & RP.FORBIDDEN_PROFILE_KEYS, frozenset()
        )
        print(
            "storable surface is exactly: "
            f"{sorted(RP.ALLOWED_PROFILE_KEYS)} within {sorted(RP.ALLOWED_DOCUMENT_KEYS)}"
        )

    def test_the_module_does_not_read_credentials_from_the_environment(self):
        for pattern in (r"os\.environ", r"getenv"):
            hits = [
                line.strip() for line in self.code_lines if re.search(pattern, line)
            ]
            self.assertEqual(hits, [], f"unexpected environment access: {hits}")

    def test_every_error_class_derives_from_one_base(self):
        for cls in (
            RP.ProfileSchemaError,
            RP.ProfileStoreError,
            RP.ProfileNotFoundError,
            RP.ProfileExistsError,
            RP.ProfileResolutionError,
        ):
            self.assertTrue(issubclass(cls, RP.RunnerProfileError))
            self.assertTrue(issubclass(cls, Exception))


if __name__ == "__main__":
    unittest.main()

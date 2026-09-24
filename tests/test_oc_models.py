"""Tests for ocsync Order 01 (g7hljt): `agent_workflows.oc_models`.

Covers config discovery (E-01), provider discovery + the LiteLLM pricing probe with its
credential guardrails (E-02), the entry point and its flags (E-03), atomic/backed-up writes
(E-04), and formatting-faithful serialization (E-06).

No test performs real network I/O: every path injects a fake fetcher, and one test asserts the
fetcher is never called for an insecure base URL.
"""

from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import oc_models

FAKE_KEY = "sk-fake-do-not-log-1234567890"


def _config(indent: int = 4, base_url: str = "https://gw.example/v1") -> str:
    payload = {
        "$schema": "https://opencode.ai/config.json",
        "model": "uri/alpha",
        "lsp": True,
        "provider": {
            "uri": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Gateway",
                "options": {"baseURL": base_url, "apiKey": FAKE_KEY},
                "models": {
                    "alpha": {"name": "Alpha", "cost": {"input": 1.0, "output": 2.0}},
                    "gone": {"name": "Gone", "cost": {"input": 9.0, "output": 9.0}},
                },
            },
            "openai": {
                "npm": "@ai-sdk/openai",
                "models": {"gpt-x": {"name": "GPT X", "cost": {"input": 5.0}}},
            },
        },
    }
    return json.dumps(payload, indent=indent) + "\n"


def _model_info_payload():
    """A `/model/info` shaped payload: costs nested under `model_info`, per token."""
    return {
        "data": [
            {
                "model_name": "alpha",
                "model_info": {
                    "input_cost_per_token": 3.3e-06,
                    "output_cost_per_token": 1.65e-05,
                    "cache_read_input_token_cost": 3.3e-07,
                    "cache_creation_input_token_cost": 4.125e-06,
                },
            },
            {
                "model_name": "beta",
                "model_info": {
                    "input_cost_per_token": 1.5e-07,
                    "output_cost_per_token": 6e-07,
                },
            },
        ]
    }


class ResolveConfigPathTests(unittest.TestCase):
    """E-01 / V-01: precedence, missing config, and the .jsonc write refusal."""

    def test_opencode_config_env_wins(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            explicit = root / "explicit.json"
            explicit.write_text(_config(), encoding="utf-8")
            project = root / "opencode.json"
            project.write_text(_config(), encoding="utf-8")
            target = oc_models.resolve_config_path(
                env={"OPENCODE_CONFIG": str(explicit)}, cwd=root
            )
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(target.path, explicit)
            self.assertTrue(target.writable)

    def test_project_config_found_by_walking_up(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "opencode.json").write_text(_config(), encoding="utf-8")
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            target = oc_models.resolve_config_path(env={}, cwd=nested)
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(target.path, root / "opencode.json")

    def test_xdg_config_home_used(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            xdg = root / "xdg"
            cfg = xdg / "opencode" / "opencode.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(_config(), encoding="utf-8")
            empty = root / "empty"
            empty.mkdir()
            target = oc_models.resolve_config_path(
                env={"XDG_CONFIG_HOME": str(xdg), "HOME": str(root / "nohome")},
                cwd=empty,
            )
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(target.path, cfg)

    def test_home_config_fallback(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            home = root / "home"
            cfg = home / ".config" / "opencode" / "opencode.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(_config(), encoding="utf-8")
            empty = root / "empty"
            empty.mkdir()
            target = oc_models.resolve_config_path(env={"HOME": str(home)}, cwd=empty)
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(target.path, cfg)

    def test_missing_config_returns_none(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            empty = root / "empty"
            empty.mkdir()
            self.assertIsNone(
                oc_models.resolve_config_path(
                    env={"HOME": str(root / "nohome")}, cwd=empty
                )
            )

    def test_jsonc_is_unsupported_for_write_not_parsed(self):
        """A .jsonc resolves but is marked non-writable; it must not raise."""
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "opencode.jsonc"
            cfg.write_text('{\n  // a comment\n  "model": "x"\n}\n', encoding="utf-8")
            target = oc_models.resolve_config_path(env={}, cwd=root)
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(target.path, cfg)
            self.assertFalse(target.writable)
            self.assertIn("jsonc", target.reason)


class PricingProbeTests(unittest.TestCase):
    """E-02 / V-02: cost conversion, endpoint fallback, and the guardrails."""

    def test_sync_converts_per_token_to_per_million(self):
        config = json.loads(_config())
        calls = []

        def fetch(url, key):
            calls.append((url, key))
            if url.endswith("/model/info"):
                return _model_info_payload()
            return None

        outcome = oc_models.sync_provider(config, "uri", fetch)
        self.assertTrue(outcome.synced)
        models = config["provider"]["uri"]["models"]
        self.assertEqual(
            models["alpha"]["cost"],
            {"input": 3.3, "cache_read": 0.33, "cache_write": 4.125, "output": 16.5},
        )
        self.assertEqual(models["beta"]["cost"], {"input": 0.15, "output": 0.6})
        # Strict sync: a model the gateway no longer lists is removed.
        self.assertNotIn("gone", models)
        self.assertEqual(outcome.removed, ("gone",))
        self.assertEqual(outcome.added, ("beta",))
        self.assertEqual(outcome.changed, ("alpha",))
        # The /v1 suffix is stripped for the admin route.
        self.assertEqual(calls[0][0], "https://gw.example/model/info")

    def test_existing_display_name_preserved(self):
        config = json.loads(_config())
        oc_models.sync_provider(config, "uri", lambda u, k: _model_info_payload())
        self.assertEqual(config["provider"]["uri"]["models"]["alpha"]["name"], "Alpha")

    def test_model_group_info_fallback(self):
        """When /model/info is absent, /model_group/info (flat costs) is used."""
        config = json.loads(_config())

        def fetch(url, key):
            if url.endswith("/model_group/info"):
                return {
                    "data": [
                        {
                            "model_group": "alpha",
                            "input_cost_per_token": 1e-06,
                            "output_cost_per_token": 2e-06,
                        }
                    ]
                }
            return None

        outcome = oc_models.sync_provider(config, "uri", fetch)
        self.assertTrue(outcome.synced)
        self.assertEqual(
            config["provider"]["uri"]["models"]["alpha"]["cost"],
            {"input": 1.0, "output": 2.0},
        )

    def test_provider_without_pricing_left_unchanged(self):
        config = json.loads(_config())
        before = json.loads(_config())["provider"]["uri"]["models"]
        outcome = oc_models.sync_provider(config, "uri", lambda u, k: None)
        self.assertFalse(outcome.synced)
        self.assertEqual(outcome.skip_reason, oc_models.SKIP_NO_PRICING)
        self.assertEqual(config["provider"]["uri"]["models"], before)

    def test_insecure_base_url_skipped_without_any_request(self):
        config = json.loads(_config(base_url="http://gw.example/v1"))
        calls = []

        def fetch(url, key):
            calls.append(url)
            return _model_info_payload()

        outcome = oc_models.sync_provider(config, "uri", fetch)
        self.assertFalse(outcome.synced)
        self.assertEqual(outcome.skip_reason, oc_models.SKIP_INSECURE)
        self.assertEqual(calls, [], "no request may be issued to an http:// baseURL")

    def test_insecure_nonloopback_refused_even_with_allow_insecure(self):
        config = json.loads(_config(base_url="http://gw.example/v1"))
        calls = []
        outcome = oc_models.sync_provider(
            config, "uri", lambda u, k: calls.append(u), allow_insecure=True
        )
        self.assertFalse(outcome.synced)
        self.assertEqual(outcome.skip_reason, oc_models.SKIP_INSECURE_NONLOOPBACK)
        self.assertEqual(calls, [])

    def test_insecure_loopback_allowed_with_opt_in(self):
        config = json.loads(_config(base_url="http://127.0.0.1:4000/v1"))
        outcome = oc_models.sync_provider(
            config, "uri", lambda u, k: _model_info_payload(), allow_insecure=True
        )
        self.assertTrue(outcome.synced)

    def test_untrusted_cost_values_ignored(self):
        """Non-numeric, negative, bool, and absent costs must not become prices."""
        self.assertIsNone(oc_models.per_million("1.0"))
        self.assertIsNone(oc_models.per_million(True))
        self.assertIsNone(oc_models.per_million(-5e-06))
        self.assertIsNone(oc_models.per_million(None))
        self.assertIsNone(oc_models.per_million(0))
        self.assertEqual(oc_models.per_million(1e-06), 1.0)

    def test_malformed_payload_yields_no_sync(self):
        config = json.loads(_config())
        for payload in ({}, {"data": "nope"}, {"data": []}, {"data": [{"x": 1}]}, None):
            outcome = oc_models.sync_provider(config, "uri", lambda u, k, p=payload: p)
            self.assertFalse(outcome.synced)

    def test_discover_providers_finds_openai_compatible_only(self):
        config = json.loads(_config())
        self.assertEqual(oc_models.discover_providers(config), ["uri"])

    def test_api_key_file_interpolation(self):
        with TemporaryDirectory() as td:
            keyfile = Path(td) / "k.key"
            keyfile.write_text(FAKE_KEY + "\n", encoding="utf-8")
            self.assertEqual(oc_models.resolve_api_key(f"{{file:{keyfile}}}"), FAKE_KEY)
        self.assertIsNone(oc_models.resolve_api_key("{file:/nonexistent/x.key}"))
        self.assertIsNone(oc_models.resolve_api_key(""))
        self.assertEqual(oc_models.resolve_api_key("literal"), "literal")

    def test_key_never_appears_in_output(self):
        """V-02(e): the API key must not leak into stdout on any path."""
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                oc_models.run(
                    ["--config", str(cfg), "--apply"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertNotIn(FAKE_KEY, buf.getvalue())
            self.assertNotIn("Authorization", buf.getvalue())


class EntryPointTests(unittest.TestCase):
    """E-03 / V-03: preview-by-default, flags, and the .jsonc apply refusal."""

    def test_entry_point_preview_apply_and_backup(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            before = cfg.read_bytes()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = oc_models.run(
                    ["--config", str(cfg)], fetch=lambda u, k: _model_info_payload()
                )
            self.assertEqual(rc, 0)
            self.assertEqual(cfg.read_bytes(), before)
            self.assertIn("preview only", buf.getvalue())

            # dry-run
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--dry-run"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(cfg.read_bytes(), before)

            # apply writes and backs up
            with redirect_stdout(io.StringIO()):
                rc = oc_models.run(
                    ["--config", str(cfg), "--apply"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(rc, 0)
            written = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertIn("beta", written["provider"]["uri"]["models"])
            backups = list(Path(td).glob("opencode.json.*.bak"))
            self.assertEqual(len(backups), 1)

            # no-backup suppresses bak and idempotent rerun
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            after_first = cfg.read_bytes()
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(cfg.read_bytes(), after_first)
            self.assertIn("up to date", buf2.getvalue())

    def test_entry_point_errors_and_non_openai(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.jsonc"
            original = '{\n  // keep me\n  "provider": {}\n}\n'
            cfg.write_text(original, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = oc_models.run(
                    ["--config", str(cfg), "--apply"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertNotEqual(rc, 0)
            self.assertEqual(cfg.read_text(encoding="utf-8"), original)

        with redirect_stdout(io.StringIO()):
            rc = oc_models.run(["--config", "/nonexistent/opencode.json"])
        self.assertEqual(rc, 2)

        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            written = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertEqual(
                written["provider"]["openai"]["models"],
                {"gpt-x": {"name": "GPT X", "cost": {"input": 5.0}}},
            )


class AtomicWriteTests(unittest.TestCase):
    """E-04 / V-04: a failed write leaves the original intact with no temp residue."""

    def test_failed_write_leaves_original_intact(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            original = _config()
            cfg.write_text(original, encoding="utf-8")

            class Boom(Exception):
                pass

            real_replace = os.replace

            def exploding_replace(src, dst):
                raise Boom("simulated interruption")

            os.replace = exploding_replace
            try:
                with self.assertRaises(Boom):
                    oc_models.write_config(cfg, "{}\n", backup=False)
            finally:
                os.replace = real_replace

            self.assertEqual(cfg.read_text(encoding="utf-8"), original)
            json.loads(cfg.read_text(encoding="utf-8"))  # still valid JSON
            residue = [
                p.name for p in Path(td).iterdir() if p.name.startswith(".oc-models-")
            ]
            self.assertEqual(residue, [], "temp file must be cleaned up")

    def test_backup_written_before_replace(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            original = _config()
            cfg.write_text(original, encoding="utf-8")
            backup = oc_models.write_config(cfg, "{}\n", backup=True)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertEqual(backup.read_text(encoding="utf-8"), original)
            self.assertEqual(cfg.read_text(encoding="utf-8"), "{}\n")


class SerializationTests(unittest.TestCase):
    """E-06 / V-06: indent is detected and reused; only models values change."""

    def test_serialization_and_indent_preservation(self):
        self.assertEqual(oc_models.detect_indent('{\n  "a": 1\n}\n'), 2)
        self.assertEqual(oc_models.detect_indent('{\n    "a": 1\n}\n'), 4)
        self.assertEqual(oc_models.detect_indent("{}\n"), 4)
        self.assertEqual(oc_models.detect_indent("{}\n", default=2), 2)

        with TemporaryDirectory() as td:
            cfg2 = Path(td) / "opencode2.json"
            cfg2.write_text(_config(indent=2), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg2), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            text2 = cfg2.read_text(encoding="utf-8")
            self.assertIn('\n  "model"', text2)

            cfg4 = Path(td) / "opencode4.json"
            cfg4.write_text(_config(indent=4), encoding="utf-8")
            before = json.loads(cfg4.read_text(encoding="utf-8"))
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg4), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            after = json.loads(cfg4.read_text(encoding="utf-8"))
            self.assertIn('\n    "model"', cfg4.read_text(encoding="utf-8"))
            self.assertEqual(list(before), list(after))
            for key in ("$schema", "model", "lsp"):
                self.assertEqual(before[key], after[key])
            self.assertNotEqual(
                before["provider"]["uri"]["models"], after["provider"]["uri"]["models"]
            )


# ==================================================================================================
# runverdict Order 07 (`w33lrl`) E-01/E-02/E-05: the host default model and its rate card
#
# EVERY TEST HERE INJECTS `env`/`cwd`. None reads the maintainer's real `~/.config/opencode/
# opencode.json`, which differs per machine and is rewritten by every `aw oc update-models`, and none
# reads the gitignored `.aw/records/runs/` tree. Both would make an assertion unreproducible on a
# fresh clone or in a lane worktree, which is what E-05 exists to prevent.
# ==================================================================================================


def _card_config(
    default_model="uri/alpha",
    cost=None,
    extra_top=None,
    agent=None,
):
    """A config fixture whose DEFAULT model and cost block the caller controls.

    Deliberately separate from `_config` above: that one is shaped for the sync/write path (it needs a
    gateway baseURL and an apiKey), while these cases are about the top-level `model` key and one
    model's `cost` block. Sharing it would couple the card tests to the write path's fixture.
    """

    entry = {"name": "Alpha"}
    if cost is not None:
        entry["cost"] = cost
    payload = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {"uri": {"models": {"alpha": entry}}},
    }
    if default_model is not None:
        payload["model"] = default_model
    if agent is not None:
        payload["agent"] = agent
    if extra_top:
        payload.update(extra_top)
    return json.dumps(payload, indent=2) + "\n"


def _write_config(root, text, name="opencode.json"):
    (root / name).write_text(text, encoding="utf-8")
    return root


class HostDefaultModelTests(unittest.TestCase):
    """E-01: WHICH model the host will use, and WHICH key said so.

    The reason this accessor exists at all: `models_from_config` returns the CATALOG of declared
    `provider/model` keys and can never say which one is DEFAULT, so before this there was no reader
    in the package that could answer the question a cost record has to answer.
    """

    def test_host_default_model_resolution_and_overrides(self):
        with TemporaryDirectory() as td:
            root = _write_config(Path(td), _card_config())
            got = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertTrue(got.resolved)
            self.assertEqual(got.model, "uri/alpha")
            self.assertEqual(got.key, oc_models.DEFAULT_MODEL_KEY_TOP_LEVEL)
            self.assertEqual(got.config_name, "opencode.json")
            self.assertRegex(got.config_digest, r"^[0-9a-f]{64}$")
            rendered = json.dumps(got._asdict())
            self.assertNotIn(str(root), rendered)
            self.assertNotIn("/", got.config_name)

        # agent override
        with TemporaryDirectory() as td:
            root = _write_config(
                Path(td),
                _card_config(agent={"build": {"model": "uri/beta"}}),
            )
            got = oc_models.resolve_host_default_model(env={}, cwd=root, agent="build")
            self.assertEqual(got.model, "uri/beta")
            self.assertEqual(got.key, oc_models.DEFAULT_MODEL_KEY_AGENT)
            plain = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertEqual(plain.model, "uri/alpha")

        # agent with no model falls through
        with TemporaryDirectory() as td:
            root = _write_config(
                Path(td), _card_config(agent={"build": {"temperature": 0.1}})
            )
            got = oc_models.resolve_host_default_model(env={}, cwd=root, agent="build")
            self.assertEqual(got.model, "uri/alpha")

        # no credentials leaked
        secret = "sk-must-never-be-read-0987654321"
        with TemporaryDirectory() as td:
            root = _write_config(
                Path(td),
                json.dumps(
                    {
                        "model": "uri/alpha",
                        "provider": {
                            "uri": {
                                "options": {
                                    "apiKey": secret,
                                    "baseURL": "https://gw.example/v1",
                                    "headers": {"X-Token": secret},
                                },
                                "models": {"alpha": {"cost": {"input": 1.0}}},
                            }
                        },
                    },
                    indent=2,
                ),
            )
            got = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertNotIn(secret, json.dumps(got._asdict()))

    def test_host_default_model_failures_and_unknowns(self):
        with TemporaryDirectory() as td:
            empty = Path(td) / "empty"
            empty.mkdir()
            got = oc_models.resolve_host_default_model(
                env={"HOME": str(Path(td) / "nohome")}, cwd=empty
            )
            self.assertFalse(got.resolved)
            self.assertEqual(got.reason, oc_models.DEFAULT_MODEL_NO_CONFIG)

        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "opencode.jsonc").write_text(
                '{\n  // the default\n  "model": "uri/alpha"\n}\n', encoding="utf-8"
            )
            got = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertFalse(got.resolved)
            self.assertEqual(got.reason, oc_models.DEFAULT_MODEL_UNPARSEABLE)

        with TemporaryDirectory() as td:
            root = _write_config(Path(td), _card_config(default_model=None))
            got = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertFalse(got.resolved)
            self.assertEqual(got.reason, oc_models.DEFAULT_MODEL_NOT_DECLARED)

        with TemporaryDirectory() as td:
            root = _write_config(
                Path(td),
                json.dumps({"small_model": "uri/cheap", "provider": {}}, indent=2),
            )
            got = oc_models.resolve_host_default_model(env={}, cwd=root)
            self.assertFalse(got.resolved)
            self.assertEqual(got.reason, oc_models.DEFAULT_MODEL_NOT_DECLARED)

        for bad in ("not-a-model-id", "", 7, True, None):
            with TemporaryDirectory() as td:
                root = _write_config(
                    Path(td),
                    json.dumps({"model": bad, "provider": {}})
                    if bad is not None
                    else json.dumps({"model": None, "provider": {}}),
                )
                got = oc_models.resolve_host_default_model(env={}, cwd=root)
                self.assertFalse(got.resolved)


class RateCardFromConfigTests(unittest.TestCase):
    """E-02: the card as the config declares it, with an ABSENT component distinguishable from ZERO."""

    def test_rate_card_resolution_and_distinctions(self):
        full = {"input": 5.5, "cache_read": 0.55, "cache_write": 6.875, "output": 27.5}
        components, reason = oc_models.card_from_config(
            json.loads(_card_config(cost=full)), "uri/alpha"
        )
        self.assertEqual(reason, "")
        self.assertEqual(components, full)

        # per-million is not applied
        self.assertEqual(components["input"], 5.5)

        # absent vs zero distinguishable
        partial, _ = oc_models.card_from_config(
            json.loads(_card_config(cost={"input": 5.5, "output": 27.5})), "uri/alpha"
        )
        zeroed, _ = oc_models.card_from_config(
            json.loads(
                _card_config(
                    cost={
                        "input": 5.5,
                        "output": 27.5,
                        "cache_read": 0,
                        "cache_write": 0,
                    }
                )
            ),
            "uri/alpha",
        )
        self.assertEqual(partial["cache_read"], oc_models.CARD_COMPONENT_ABSENT)
        self.assertEqual(zeroed["cache_read"], 0.0)
        self.assertEqual(oc_models.CARD_UNIT, "$/Mtok")

        # malformed component
        for bad in (True, False, "5.5", None, -1, [5.5]):
            comps, _ = oc_models.card_from_config(
                json.loads(_card_config(cost={"input": bad, "output": 27.5})),
                "uri/alpha",
            )
            self.assertEqual(comps["input"], oc_models.CARD_COMPONENT_MALFORMED)

    def test_rate_card_missing_and_unpriced(self):
        comps, reason = oc_models.card_from_config(
            json.loads(_card_config(cost=None)), "uri/alpha"
        )
        self.assertEqual(comps, {})
        self.assertEqual(reason, oc_models.CARD_NO_COST_BLOCK)

        comps, reason = oc_models.card_from_config(
            json.loads(_card_config()), "google/gemini-3.7-flash-high"
        )
        self.assertEqual(comps, {})
        self.assertEqual(reason, oc_models.CARD_MODEL_NOT_DECLARED)

        comps, reason = oc_models.card_from_config(json.loads(_card_config()), "")
        self.assertEqual(comps, {})
        self.assertEqual(reason, oc_models.CARD_NO_MODEL)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

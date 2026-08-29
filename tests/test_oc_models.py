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

    def test_preview_leaves_file_byte_identical(self):
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
            self.assertEqual(cfg.read_bytes(), before, "preview must not write")
            self.assertIn("preview only", buf.getvalue())

    def test_dry_run_is_synonym_for_preview(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            before = cfg.read_bytes()
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--dry-run"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(cfg.read_bytes(), before)

    def test_apply_writes_and_backs_up(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                rc = oc_models.run(
                    ["--config", str(cfg), "--apply"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(rc, 0)
            written = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertIn("beta", written["provider"]["uri"]["models"])
            backups = list(Path(td).glob("opencode.json.*.bak"))
            self.assertEqual(len(backups), 1, "exactly one backup expected")
            # The backup holds the PRE-change content.
            self.assertIn(
                "gone", json.loads(backups[0].read_text())["provider"]["uri"]["models"]
            )

    def test_no_backup_suppresses_bak(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(list(Path(td).glob("*.bak")), [])

    def test_apply_on_jsonc_exits_nonzero_and_writes_nothing(self):
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
            self.assertIn("refusing to rewrite", buf.getvalue())

    def test_missing_config_arg_is_usage_error(self):
        with redirect_stdout(io.StringIO()):
            rc = oc_models.run(["--config", "/nonexistent/opencode.json"])
        self.assertEqual(rc, 2)

    def test_non_openai_compatible_provider_untouched(self):
        """The `openai` provider has no baseURL, so it must never be rewritten."""
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

    def test_idempotent_second_run_reports_up_to_date(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            after_first = cfg.read_bytes()
            buf = io.StringIO()
            with redirect_stdout(buf):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertEqual(cfg.read_bytes(), after_first)
            self.assertIn("up to date", buf.getvalue())


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

    def test_detect_indent(self):
        self.assertEqual(oc_models.detect_indent('{\n  "a": 1\n}\n'), 2)
        self.assertEqual(oc_models.detect_indent('{\n    "a": 1\n}\n'), 4)
        self.assertEqual(oc_models.detect_indent("{}\n"), 4)
        self.assertEqual(oc_models.detect_indent("{}\n", default=2), 2)

    def test_two_space_config_stays_two_space(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(indent=2), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            text = cfg.read_text(encoding="utf-8")
            self.assertIn('\n  "model"', text)
            self.assertNotIn('\n    "model"', text)

    def test_four_space_config_stays_four_space(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(indent=4), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            self.assertIn('\n    "model"', cfg.read_text(encoding="utf-8"))

    def test_changes_confined_to_models(self):
        with TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(_config(), encoding="utf-8")
            before = json.loads(cfg.read_text(encoding="utf-8"))
            with redirect_stdout(io.StringIO()):
                oc_models.run(
                    ["--config", str(cfg), "--apply", "--no-backup"],
                    fetch=lambda u, k: _model_info_payload(),
                )
            after = json.loads(cfg.read_text(encoding="utf-8"))
            # Every top-level key and relative order preserved.
            self.assertEqual(list(before), list(after))
            for key in ("$schema", "model", "lsp"):
                self.assertEqual(before[key], after[key])
            # Only provider.uri.models differs.
            self.assertNotEqual(
                before["provider"]["uri"]["models"], after["provider"]["uri"]["models"]
            )
            for key in ("npm", "name", "options"):
                self.assertEqual(
                    before["provider"]["uri"][key], after["provider"]["uri"][key]
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

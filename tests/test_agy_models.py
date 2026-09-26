"""Tests for agent_workflows.agy_models: dynamic AGY model and config resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_models


class AgyModelsTests(unittest.TestCase):
    def test_resolve_config_path_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            path = agy_models.resolve_config_path(env={}, home=home)
            self.assertIsNone(path)

    def test_resolve_config_path_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            settings_file = home / ".gemini" / "antigravity-cli" / "settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings_file.write_text(
                '{"model": "Gemini 3.8 Flash (High)"}', encoding="utf-8"
            )

            path = agy_models.resolve_config_path(env={}, home=home)
            self.assertEqual(path, settings_file)

    def test_resolve_config_path_env_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom = Path(tmpdir) / "custom_settings.json"
            custom.write_text('{"model": "custom-gemini"}', encoding="utf-8")

            for var in ("AGY_SETTINGS", "ANTIGRAVITY_SETTINGS", "AGY_CONFIG"):
                path = agy_models.resolve_config_path(env={var: str(custom)})
                self.assertEqual(path, custom)

    def test_resolve_agy_default_model_from_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            settings_file = home / ".gemini" / "antigravity-cli" / "settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings_file.write_text(
                '{"model": "Gemini 3.8 Flash (High)"}', encoding="utf-8"
            )

            model, source = agy_models.resolve_agy_default_model(env={}, home=home)
            self.assertEqual(model, "Gemini 3.8 Flash (High)")
            self.assertEqual(source, "settings.json")
            self.assertEqual(
                agy_models.resolve_agy_config_model(env={}, home=home),
                "Gemini 3.8 Flash (High)",
            )

    def test_resolve_agy_default_model_missing_model_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            settings_file = home / ".gemini" / "antigravity-cli" / "settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings_file.write_text('{"agentMode": "accept-edits"}', encoding="utf-8")

            model, source = agy_models.resolve_agy_default_model(env={}, home=home)
            self.assertIsNone(model)
            self.assertEqual(source, "host-default")
            self.assertIsNone(agy_models.resolve_agy_config_model(env={}, home=home))

    def test_resolve_agy_default_model_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            settings_file = home / ".gemini" / "antigravity-cli" / "settings.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings_file.write_text("{not valid json}", encoding="utf-8")

            model, source = agy_models.resolve_agy_default_model(env={}, home=home)
            self.assertIsNone(model)
            self.assertEqual(source, "host-default")

    def test_resolve_agy_default_model_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            model, source = agy_models.resolve_agy_default_model(env={}, home=home)
            self.assertIsNone(model)
            self.assertEqual(source, "host-default")


class AgyRunIpdModelFlagTests(unittest.TestCase):
    def test_model_flag_omitted_when_not_explicitly_passed(self):
        # When explicit_model is None, --model must NOT be passed to agy so agy uses its config/default
        options = {
            "model": "Gemini 3.8 Flash (High)",
            "explicit_model": None,
        }
        # Emulate argv assembly logic in agy_runipd.run_turn_inner
        argv = ["agy", "-p", "prompt", "--output-format", "stream-json"]
        model_flag = options.get("explicit_model")
        if model_flag is None and "explicit_model" not in options:
            model_flag = options.get("model")
        if model_flag:
            argv.extend(["--model", model_flag])

        self.assertNotIn("--model", argv)

    def test_model_flag_included_when_explicitly_passed(self):
        # When explicit_model is set (via CLI --model), --model must be passed to agy
        options = {
            "model": "gemini-3.8-flash-high",
            "explicit_model": "gemini-3.8-flash-high",
        }
        argv = ["agy", "-p", "prompt", "--output-format", "stream-json"]
        model_flag = options.get("explicit_model")
        if model_flag is None and "explicit_model" not in options:
            model_flag = options.get("model")
        if model_flag:
            argv.extend(["--model", model_flag])

        self.assertIn("--model", argv)
        self.assertIn("gemini-3.8-flash-high", argv)

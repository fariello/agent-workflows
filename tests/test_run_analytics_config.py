"""Tests for the telemetry configuration model (IPD lhccjf, Set runanalytics, E-07).

WHAT THIS SUITE IS ACTUALLY PROVING, since "reads a JSON key" would not be worth a file. Three
things, each of which was a measured trap rather than a hypothetical.

FIRST, THAT THE SETTING LIVES SOMEWHERE IT SURVIVES. The obvious home,
:mod:`agent_workflows.config`, persists an ALLOWLIST of top-level keys and rebuilds its output from
``default_config()``, so an unregistered key is DROPPED on the next save with no error. This suite
asserts the shipped ``review_findings_gate`` precedent instead: read from
``.aw/config/project.json`` (committed, portable) with a machine-local override in
``.aw/config/local.json`` (gitignored), round-tripping through ``project_schema``'s
``unknown_fields``.

SECOND, THAT THE READER IS TOTAL. Telemetry is not a safety gate, so the default direction is the
OPPOSITE of ``review_findings_gate``'s fail-closed one: an absent, malformed, hostile, or
out-of-vocabulary value must land on the documented default and must never raise. A telemetry
setting that can break a run protects nothing.

THIRD, THAT THE INTERVAL BOUND HAS EXACTLY ONE ENFORCEMENT POINT. Two bound checks eventually
disagree, so the suite asserts that constructing a config through the only public producer clamps,
and that the clamp function is what does it.

Stdlib unittest only. No network, no subprocess, no sleep, no real device.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import run_analytics_config as cfg


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class DefaultsTests(unittest.TestCase):
    """The documented defaults, asserted so a silent change to one is a test failure."""

    def test_basic_telemetry_is_on_and_periodic_sampling_is_off_by_default(
        self,
    ) -> None:
        config = cfg.parse_telemetry_settings()
        self.assertTrue(config.enabled, "basic start/end telemetry is ON by default")
        self.assertFalse(
            config.sampling_enabled,
            "periodic sampling is OPT-IN: the plan's required decision says to ask separately",
        )
        self.assertFalse(config.samples_enabled)
        self.assertEqual(
            config.sample_interval_seconds, cfg.DEFAULT_SAMPLE_INTERVAL_SECONDS
        )
        self.assertEqual(config.sources, ())

    def test_disabling_telemetry_also_disables_sampling(self) -> None:
        # `samples_enabled` is DERIVED rather than stored, so "telemetry off" can never be
        # contradicted by a stale "sampling on" flag.
        config = cfg.parse_telemetry_settings(
            {"enabled": False, "sampling_enabled": True}
        )
        self.assertFalse(config.enabled)
        self.assertTrue(config.sampling_enabled)
        self.assertFalse(
            config.samples_enabled,
            "sampling requires telemetry itself to be enabled",
        )

    def test_periodic_sampling_can_be_enabled_explicitly(self) -> None:
        config = cfg.parse_telemetry_settings(
            {"enabled": True, "sampling_enabled": True, "sample_interval_seconds": 30}
        )
        self.assertTrue(config.samples_enabled)
        self.assertEqual(config.sample_interval_seconds, 30.0)


class NeverRaisesTests(unittest.TestCase):
    """Every hostile input lands on the documented default WITHOUT raising."""

    def test_malformed_and_out_of_vocabulary_values_land_on_defaults(self) -> None:
        hostile = [
            {"enabled": "maybe"},
            {"enabled": ["yes"]},
            {"enabled": {"nested": True}},
            {"sampling_enabled": "sometimes"},
            {"sample_interval_seconds": "fast"},
            {"sample_interval_seconds": None},
            {"sample_interval_seconds": [1, 2, 3]},
            {"sample_interval_seconds": float("nan")},
            {"sample_interval_seconds": float("inf")},
            {"sample_interval_seconds": True},
            {"max_probe_seconds": "quick"},
            {"max_probe_seconds": -5},
            {"unknown_future_key": "ignored"},
        ]
        for payload in hostile:
            with self.subTest(payload=payload):
                config = cfg.parse_telemetry_settings(payload)
                self.assertIsInstance(config, cfg.TelemetryConfig)
                self.assertIn(config.enabled, (True, False))
                self.assertGreaterEqual(
                    config.sample_interval_seconds, cfg.MIN_SAMPLE_INTERVAL_SECONDS
                )
                self.assertLessEqual(
                    config.sample_interval_seconds, cfg.MAX_SAMPLE_INTERVAL_SECONDS
                )
                self.assertGreater(config.max_probe_seconds, 0)

    def test_boolean_spellings_are_tolerated(self) -> None:
        for raw, expected in (
            ("true", True),
            ("TRUE", True),
            ("on", True),
            ("yes", True),
            ("1", True),
            (1, True),
            ("false", False),
            ("off", False),
            ("no", False),
            ("0", False),
            (0, False),
        ):
            with self.subTest(raw=raw):
                self.assertIs(
                    cfg.parse_telemetry_settings(
                        {"sampling_enabled": raw}
                    ).sampling_enabled,
                    expected,
                )

    def test_unreadable_and_invalid_files_yield_defaults(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            # No .aw at all.
            self.assertEqual(cfg.read_telemetry_config(root).sources, ())
            # A file that is not JSON.
            (root / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            (root / ".aw" / "config" / "project.json").write_text(
                "{not json at all", encoding="utf-8"
            )
            config = cfg.read_telemetry_config(root)
            self.assertTrue(config.enabled)
            self.assertEqual(config.sources, ())
            # A JSON document that is not an object.
            (root / ".aw" / "config" / "project.json").write_text(
                "[1,2,3]", encoding="utf-8"
            )
            self.assertEqual(cfg.read_telemetry_config(root).sources, ())
            # A telemetry key that is not an object.
            _write(root / ".aw" / "config" / "project.json", {cfg.TELEMETRY_KEY: "on"})
            self.assertEqual(cfg.read_telemetry_config(root).sources, ())


class IntervalBoundTests(unittest.TestCase):
    """The bound is enforced in ONE place, and the public producer routes through it."""

    def test_clamp_is_the_single_enforcement_point(self) -> None:
        self.assertEqual(cfg.clamp_interval(0.001), cfg.MIN_SAMPLE_INTERVAL_SECONDS)
        self.assertEqual(cfg.clamp_interval(-99), cfg.MIN_SAMPLE_INTERVAL_SECONDS)
        self.assertEqual(cfg.clamp_interval(10**9), cfg.MAX_SAMPLE_INTERVAL_SECONDS)
        self.assertEqual(cfg.clamp_interval(42), 42.0)
        self.assertEqual(
            cfg.clamp_interval("nonsense"), cfg.DEFAULT_SAMPLE_INTERVAL_SECONDS
        )

    def test_every_config_is_in_bounds_because_the_producer_clamps(self) -> None:
        for raw in (0.0, 0.5, -1, 10**9, 3601, 1, 3600):
            with self.subTest(raw=raw):
                config = cfg.parse_telemetry_settings({"sample_interval_seconds": raw})
                self.assertGreaterEqual(
                    config.sample_interval_seconds, cfg.MIN_SAMPLE_INTERVAL_SECONDS
                )
                self.assertLessEqual(
                    config.sample_interval_seconds, cfg.MAX_SAMPLE_INTERVAL_SECONDS
                )

    def test_probe_budget_cannot_exceed_the_module_ceiling(self) -> None:
        # A project may ask for LESS probe time than the ceiling, never more: the ceiling is the
        # overhead guarantee, so a config file may not raise it.
        self.assertEqual(
            cfg.parse_telemetry_settings({"max_probe_seconds": 0.25}).max_probe_seconds,
            0.25,
        )
        self.assertEqual(
            cfg.parse_telemetry_settings({"max_probe_seconds": 600}).max_probe_seconds,
            cfg.MAX_PROBE_SECONDS,
        )


class ConfigHomeTests(unittest.TestCase):
    """OQ-01, asserted rather than merely documented in prose."""

    def test_project_policy_is_read_from_the_committed_portable_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / ".aw" / "config" / "project.json",
                {
                    "schema_version": 2,
                    "preset": "private-target",
                    cfg.TELEMETRY_KEY: {
                        "sampling_enabled": True,
                        "sample_interval_seconds": 20,
                    },
                },
            )
            config = cfg.read_telemetry_config(root)
            self.assertTrue(config.samples_enabled)
            self.assertEqual(config.sample_interval_seconds, 20.0)
            self.assertEqual(config.sources, ("project",))

    def test_machine_local_override_beats_project_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / ".aw" / "config" / "project.json",
                {
                    cfg.TELEMETRY_KEY: {
                        "sampling_enabled": True,
                        "sample_interval_seconds": 5,
                    }
                },
            )
            # The intended machine-local use: an operator on a constrained box DECLINING sampling.
            _write(
                root / ".aw" / "config" / "local.json",
                {
                    "schema_version": 2,
                    "runtime_overrides": {
                        cfg.TELEMETRY_KEY: {"sampling_enabled": False}
                    },
                },
            )
            config = cfg.read_telemetry_config(root)
            self.assertFalse(
                config.samples_enabled,
                "local.json (gitignored, per-machine) overrides project.json (committed)",
            )
            self.assertEqual(
                config.sample_interval_seconds,
                5.0,
                "an unset local key leaves the project value in force",
            )
            self.assertEqual(config.sources, ("project", "local"))

    def test_telemetry_key_survives_a_project_policy_round_trip(self) -> None:
        # THE POINT OF THE PRECEDENT: `parse_portable_policy` preserves an unknown key in
        # `unknown_fields` and writes it BACK, which is exactly what `config.py` would not do.
        from agent_workflows import project_schema

        payload = {
            "schema_version": 2,
            "preset": "private-target",
            "role": "target",
            cfg.TELEMETRY_KEY: {
                "sampling_enabled": True,
                "sample_interval_seconds": 30,
            },
        }
        parsed = project_schema.parse_portable_policy(payload)
        self.assertIn(cfg.TELEMETRY_KEY, parsed.unknown_fields)
        round_tripped = parsed.to_dict()
        self.assertIn(
            cfg.TELEMETRY_KEY,
            round_tripped,
            "the key must survive serialization, which is why it is NOT in config.py's schema",
        )
        self.assertEqual(
            round_tripped[cfg.TELEMETRY_KEY],
            payload[cfg.TELEMETRY_KEY],
        )
        recovered = cfg.parse_telemetry_settings(round_tripped[cfg.TELEMETRY_KEY])
        self.assertTrue(recovered.samples_enabled)
        self.assertEqual(recovered.sample_interval_seconds, 30.0)

    def test_the_key_is_deliberately_absent_from_the_xdg_config_schema(self) -> None:
        # Measured: `config.py` enforces a FIXED top-level allowlist and `normalize()` rebuilds its
        # output from `default_config()`, so registering the key there would make it vanish on save.
        # This asserts the deliberate absence, so a future contributor who "fixes" it by
        # registering the key breaks a test that explains why not.
        from agent_workflows import config as xdg_config

        self.assertNotIn(cfg.TELEMETRY_KEY, xdg_config._ALLOWED_TOP_KEYS)
        normalized = xdg_config.normalize({cfg.TELEMETRY_KEY: {"enabled": False}})
        self.assertNotIn(
            cfg.TELEMETRY_KEY,
            normalized,
            "proof the XDG config DROPS this key rather than storing it",
        )

    def test_top_level_key_wins_over_runtime_overrides_within_one_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / ".aw" / "config" / "local.json",
                {
                    "runtime_overrides": {
                        cfg.TELEMETRY_KEY: {"sample_interval_seconds": 11}
                    },
                    cfg.TELEMETRY_KEY: {"sample_interval_seconds": 22},
                },
            )
            self.assertEqual(
                cfg.read_telemetry_config(root).sample_interval_seconds,
                22.0,
                "the more explicit placement wins within a single file",
            )


if __name__ == "__main__":
    unittest.main()

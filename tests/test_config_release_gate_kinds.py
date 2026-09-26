"""Tests for gatekinds kxawm4: config reader for release_gate_work_kinds."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent_workflows import config
from agent_workflows.project_schema import parse_portable_policy


class TestConfigReleaseGateKinds(unittest.TestCase):
    """Verify release_gate_work_kinds reader and policy round-trip."""

    def test_absent_file(self) -> None:
        """When .aw/config/project.json is missing, silently return default."""
        with TemporaryDirectory() as tmp:
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug"}))
            self.assertEqual(warnings, [])

    def test_absent_key(self) -> None:
        """When project.json exists without release_gate_work_kinds, silently return default."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"role": "target"}), encoding="utf-8"
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug"}))
            self.assertEqual(warnings, [])

    def test_object_form(self) -> None:
        """Object form {"kinds": ["bug", "security"]} returns configured set."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"release_gate_work_kinds": {"kinds": ["bug", "security"]}}),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug", "security"}))
            self.assertEqual(warnings, [])

    def test_bare_list(self) -> None:
        """Bare list form ["bug", "security"] returns configured set."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"release_gate_work_kinds": ["bug", "security"]}),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug", "security"}))
            self.assertEqual(warnings, [])

    def test_bare_string(self) -> None:
        """Bare string form "security" or "bug" returns single-element set."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "project.json").write_text(
                json.dumps({"release_gate_work_kinds": "security"}),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"security"}))
            self.assertEqual(warnings, [])

    def test_empty_list(self) -> None:
        """Explicit empty list [] or {"kinds": []} disables gating and returns empty set."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            proj_file = conf_dir / "project.json"

            # Object form with empty list
            proj_file.write_text(
                json.dumps({"release_gate_work_kinds": {"kinds": []}}),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset())
            self.assertEqual(warnings, [])

            # Bare empty list
            proj_file.write_text(
                json.dumps({"release_gate_work_kinds": []}),
                encoding="utf-8",
            )
            kinds2 = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds2, frozenset())
            self.assertEqual(warnings, [])

    def test_unknown_kind_name_warns_and_dropped(self) -> None:
        """Unknown kind name emits warning naming dropped kind, key, and file, and drops it."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            proj_file = conf_dir / "project.json"
            proj_file.write_text(
                json.dumps(
                    {"release_gate_work_kinds": {"kinds": ["bug", "unknown_defect"]}}
                ),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug"}))
            self.assertEqual(len(warnings), 1)
            warn_msg = warnings[0]
            self.assertIn("release_gate_work_kinds", warn_msg)
            self.assertIn("unknown_defect", warn_msg)
            self.assertIn(str(proj_file), warn_msg)

    def test_non_list_garbage_warns_and_returns_default(self) -> None:
        """Non-list garbage emits warning naming key, value, and file, and falls back to default."""
        with TemporaryDirectory() as tmp:
            conf_dir = Path(tmp) / ".aw" / "config"
            conf_dir.mkdir(parents=True, exist_ok=True)
            proj_file = conf_dir / "project.json"

            # Top-level non-list/non-dict/non-string garbage
            proj_file.write_text(
                json.dumps({"release_gate_work_kinds": 12345}),
                encoding="utf-8",
            )
            warnings: list[str] = []
            kinds = config.release_gate_work_kinds(tmp, warn=warnings.append)
            self.assertEqual(kinds, frozenset({"bug"}))
            self.assertEqual(len(warnings), 1)
            self.assertIn("release_gate_work_kinds", warnings[0])
            self.assertIn("12345", warnings[0])
            self.assertIn(str(proj_file), warnings[0])

            # Dict with non-list kinds
            proj_file.write_text(
                json.dumps({"release_gate_work_kinds": {"kinds": 12345}}),
                encoding="utf-8",
            )
            warnings2: list[str] = []
            kinds2 = config.release_gate_work_kinds(tmp, warn=warnings2.append)
            self.assertEqual(kinds2, frozenset({"bug"}))
            self.assertEqual(len(warnings2), 1)
            self.assertIn("release_gate_work_kinds", warnings2[0])
            self.assertIn("12345", warnings2[0])
            self.assertIn(str(proj_file), warnings2[0])

    def test_portable_policy_round_trip(self) -> None:
        """The key round-trips through parse_portable_policy into unknown_fields and to_dict()."""
        raw_policy = {
            "schema_version": 2,
            "role": "target",
            "release_gate_work_kinds": {"kinds": ["bug", "security"]},
        }
        policy = parse_portable_policy(raw_policy)
        self.assertIn("release_gate_work_kinds", policy.unknown_fields)
        self.assertEqual(
            policy.unknown_fields["release_gate_work_kinds"],
            {"kinds": ["bug", "security"]},
        )
        serialized = policy.to_dict()
        self.assertIn("release_gate_work_kinds", serialized)
        self.assertEqual(
            serialized["release_gate_work_kinds"],
            {"kinds": ["bug", "security"]},
        )


if __name__ == "__main__":
    unittest.main()

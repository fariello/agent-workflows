"""Tests for trailing newline consistency in project.json and local.json (IPD kb64ea)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.config import KNOWN_FEATURE_CUTOVERS
from agent_workflows.install_wizard import (
    ProjectPolicy,
    persist_project_policy,
)
from agent_workflows.placement_switch import _write_atomic_json
from agent_workflows.project_schema import Preset, ProjectRole


class TestInstallConfigTrailingNewline(unittest.TestCase):
    """Verify trailing newline behavior for install-time config writers."""

    def _init_repo(self, path: Path) -> None:
        subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(path), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(path),
            check=True,
        )

    def test_persist_project_policy_fresh_install_trailing_newline(self):
        """(a) Fresh install writes project.json and local.json ending with '}\\n' and not '\\n\\n'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=False)

            proj_file = repo / ".aw" / "config" / "project.json"
            local_file = repo / ".aw" / "config" / "local.json"

            proj_bytes = proj_file.read_bytes()
            local_bytes = local_file.read_bytes()

            self.assertTrue(
                proj_bytes.endswith(b"}\n"),
                f"project.json expected to end with b'}}\\n', got: {proj_bytes[-10:]!r}",
            )
            self.assertFalse(
                proj_bytes.endswith(b"\n\n"),
                f"project.json expected not to end with b'\\n\\n', got: {proj_bytes[-10:]!r}",
            )
            self.assertTrue(
                local_bytes.endswith(b"}\n"),
                f"local.json expected to end with b'}}\\n', got: {local_bytes[-10:]!r}",
            )
            self.assertFalse(
                local_bytes.endswith(b"\n\n"),
                f"local.json expected not to end with b'\\n\\n', got: {local_bytes[-10:]!r}",
            )

    def test_persist_project_policy_reinstall_byte_identical_with_complete_cutovers(
        self,
    ):
        """(b) Reinstall with already-complete cutovers leaves project.json byte-identical ending in '\\n'."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            initial_proj = {
                "schema_version": 2,
                "preset": "private-target",
                "role": "source-checkout",
                "placements": {"records": "target-records"},
                "git_policies": {"records": "ignored"},
                "cutovers": {k: "2026-01-01" for k in KNOWN_FEATURE_CUTOVERS},
            }
            proj_file = cfg_dir / "project.json"
            with open(proj_file, "w", encoding="utf-8") as f:
                json.dump(initial_proj, f, indent=2)
                f.write("\n")

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=False)
            proj_bytes_first = proj_file.read_bytes()

            persist_project_policy(str(repo), policy, replace_config=False)
            proj_bytes_second = proj_file.read_bytes()

            self.assertEqual(proj_bytes_second, proj_bytes_first)
            self.assertTrue(
                proj_bytes_second.endswith(b"}\n"),
                f"project.json expected to end with b'}}\\n', got: {proj_bytes_second[-10:]!r}",
            )
            self.assertFalse(
                proj_bytes_second.endswith(b"\n\n"),
                f"project.json expected not to end with b'\\n\\n', got: {proj_bytes_second[-10:]!r}",
            )

    def test_placement_switch_write_atomic_json_trailing_newline(self):
        """(c) _write_atomic_json ends with exactly one newline and round-trips through json.loads."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            target_path = tpath / "sub" / "test.json"
            data = {"key": "value", "items": [1, 2, 3], "nested": {"a": True}}

            _write_atomic_json(target_path, data)

            raw = target_path.read_bytes()
            self.assertTrue(
                raw.endswith(b"}\n"),
                f"Expected raw bytes to end with b'}}\\n', got: {raw[-10:]!r}",
            )
            self.assertFalse(
                raw.endswith(b"\n\n"),
                f"Expected raw bytes not to end with b'\\n\\n', got: {raw[-10:]!r}",
            )
            self.assertEqual(json.loads(raw.decode("utf-8")), data)

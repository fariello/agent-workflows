"""Tests for install consent plan truth and state tracking policy alignment (IPD gi1w75)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows.install_wizard import (
    ProjectPolicy,
    render_pre_write_plan,
)
from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import (
    PRESETS,
    GitPolicy,
    Preset,
    RootClass,
)
from agent_workflows.term import Term


class TestInstallConsentTruth(unittest.TestCase):
    """Validate that pre-write consent plan paths match physical reality and git ignore rules."""

    def setUp(self):
        self.repo_root = str(Path(__file__).parent.parent.resolve())

    def _init_git_repo(self, path: Path) -> None:
        subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(path), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(path),
            check=True,
        )

    def _run_install(
        self, target_dir: Path, fake_home: Path, preset: str = "private-target"
    ) -> subprocess.CompletedProcess:
        env = dict(
            os.environ,
            PYTHONPATH=self.repo_root,
            AW_NO_REEXEC="1",
            HOME=str(fake_home),
        )
        return subprocess.run(
            [
                "python3",
                "-m",
                "agent_workflows",
                "install",
                ".",
                "--preset",
                preset,
                "-y",
                "--no-interactive",
            ],
            cwd=str(target_dir),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_target_placement_paths_exist_after_install(self) -> None:
        """(a) Extract every target path from rendered plan and assert each exists after install."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as fake_home:
            repo_path = Path(td)
            self._init_git_repo(repo_path)

            policy = ProjectPolicy(preset=Preset.PRIVATE_TARGET.value)
            plan = render_pre_write_plan(policy, str(repo_path), Term(color=False))

            # Extract target paths
            target_paths: dict[str, Path] = {}
            for line in plan.splitlines():
                line_s = line.strip()
                if line_s.startswith("- ") and "[" in line_s and "]" in line_s:
                    parts = line_s.split()
                    cls_name = parts[1].rstrip(":")
                    if cls_name in [c.value for c in RootClass]:
                        owner = line_s[line_s.index("[") + 1 : line_s.index("]")]
                        path_str = parts[3]
                        if owner == "target":
                            # Strip directory trailing slash for Path object
                            target_paths[cls_name] = Path(path_str.rstrip("/"))

            res = self._run_install(
                repo_path, Path(fake_home), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(res.returncode, 0, f"Install failed: {res.stderr}")

            # Assert each path exists (a file for config classes, a dir or parent for state classes)
            for cls_name, p_obj in target_paths.items():
                if cls_name in (
                    RootClass.CONFIG_PROJECT.value,
                    RootClass.CONFIG_LOCAL.value,
                ):
                    self.assertTrue(
                        p_obj.is_file(), f"{cls_name} expected file at {p_obj}"
                    )
                elif cls_name in (
                    RootClass.STATE_DURABLE.value,
                    RootClass.STATE_RUNTIME.value,
                ):
                    self.assertTrue(
                        p_obj.exists() or p_obj.parent.exists(),
                        f"{cls_name} expected dir or parent at {p_obj}",
                    )
                else:
                    self.assertTrue(
                        p_obj.is_dir(), f"{cls_name} expected dir at {p_obj}"
                    )

    def test_printed_paths_equal_resolve_project_context_for_all_presets(self) -> None:
        """(a) For every preset, assert each printed path equals resolve_project_context(...).physical_classes."""
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            self._init_git_repo(repo_path)

            home_dir = str(Path.home())

            def _fmt(p: str) -> str:
                if p.startswith(home_dir):
                    return "~" + p[len(home_dir) :]
                return p

            for preset in PRESETS:
                policy = ProjectPolicy(preset=preset)
                plan = render_pre_write_plan(policy, str(repo_path), Term(color=False))
                ctx = resolve_project_context(
                    target_repo=str(repo_path),
                    aw_home=policy.aw_home,
                    delivery_mode=policy.delivery_mode,
                    records_backend=policy.records_backend,
                    preset=policy.preset,
                    role=policy.role,
                    companion_dir=policy.companion_dir,
                )

                printed_classes: dict[str, str] = {}
                for line in plan.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("- ") and "[" in line_s and "]" in line_s:
                        parts = line_s.split()
                        cls_name = parts[1].rstrip(":")
                        if cls_name in [c.value for c in RootClass]:
                            raw_path = parts[3].rstrip("/")
                            printed_classes[cls_name] = raw_path

                for cls in RootClass:
                    self.assertIn(
                        cls.value,
                        printed_classes,
                        f"Class {cls.value} missing in plan for {preset}",
                    )
                    expected = _fmt(str(ctx.physical_classes[cls.value]))
                    self.assertEqual(
                        printed_classes[cls.value],
                        expected,
                        f"Preset {preset} class {cls.value} printed path mismatch",
                    )

    def test_resolve_project_context_private_target_git_policies(self) -> None:
        """(a2) Assert resolve_project_context for private-target returns git_policies["state_durable"] == "ignored"."""
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            self._init_git_repo(repo_path)
            ctx = resolve_project_context(
                target_repo=str(repo_path), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(
                ctx.git_policies.get("state_durable"),
                GitPolicy.IGNORED.value,
                "resolve_project_context git_policies[state_durable] must be ignored",
            )

    def test_fresh_install_project_json_and_git_check_ignore(self) -> None:
        """(b) Assert fresh install project.json declares state_durable ignored and git check-ignore confirms it."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as fake_home:
            repo_path = Path(td)
            self._init_git_repo(repo_path)

            res = self._run_install(
                repo_path, Path(fake_home), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(res.returncode, 0, f"Install failed: {res.stderr}")

            proj_json = repo_path / ".aw" / "config" / "project.json"
            self.assertTrue(proj_json.is_file(), "project.json not created")
            data = json.loads(proj_json.read_text(encoding="utf-8"))

            self.assertEqual(
                data["git_policies"].get("state_durable"),
                "ignored",
                "project.json git_policies[state_durable] must be ignored",
            )
            self.assertEqual(
                data["placements"].get("state_durable"),
                "target-ignored",
                "project.json placements[state_durable] must be target-ignored",
            )

            check_ign = subprocess.run(
                ["git", "check-ignore", "-v", ".aw/state/durable/install.json"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                check_ign.returncode, 0, "state file must be ignored by git"
            )
            self.assertIn(
                "/state/", check_ign.stdout, "check-ignore must cite /state/ rule"
            )

    def test_upgrade_normalization_announcement_and_no_repeat(self) -> None:
        """(c) Upgrade case: seed project.json with target-git, reinstall, assert ignored and announced once."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as fake_home:
            repo_path = Path(td)
            self._init_git_repo(repo_path)

            # Baseline install
            res0 = self._run_install(
                repo_path, Path(fake_home), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(res0.returncode, 0)

            # Seed project.json with target-git
            proj_json = repo_path / ".aw" / "config" / "project.json"
            data = json.loads(proj_json.read_text(encoding="utf-8"))
            data["git_policies"]["state_durable"] = "target-git"
            data["placements"]["state_durable"] = "target-tracked"
            proj_json.write_text(json.dumps(data, indent=2), encoding="utf-8")

            # Upgrade install
            res1 = self._run_install(
                repo_path, Path(fake_home), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(res1.returncode, 0, f"Upgrade failed: {res1.stderr}")
            combined_out = res1.stdout + res1.stderr
            self.assertIn(
                "Normalizing state_durable git policy from target-git to ignored",
                combined_out,
                "Expected normalization announcement on upgrade",
            )
            data_upgraded = json.loads(proj_json.read_text(encoding="utf-8"))
            self.assertEqual(data_upgraded["git_policies"]["state_durable"], "ignored")

            # Second install: assert no repeat announcement
            res2 = self._run_install(
                repo_path, Path(fake_home), preset=Preset.PRIVATE_TARGET.value
            )
            self.assertEqual(res2.returncode, 0)
            combined_out2 = res2.stdout + res2.stderr
            self.assertNotIn(
                "Normalizing state_durable git policy from target-git to ignored",
                combined_out2,
                "Normalization announcement must not repeat on second install",
            )


if __name__ == "__main__":
    unittest.main()

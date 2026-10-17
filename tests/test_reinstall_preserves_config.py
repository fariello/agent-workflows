"""Tests for config and cutover preservation across reinstall (IPD on0keo, backlog qyevpr)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows.install_wizard import (
    InvalidPolicyError,
    ProjectPolicy,
    persist_project_policy,
    resolve_existing_policy,
    resolve_policy_noninteractive,
)
from agent_workflows.project_context import (
    DEFAULT_ENABLED_HOSTS,
    resolve_project_context,
)
from agent_workflows.project_schema import (
    DeliveryMode,
    PrecedenceLevel,
    Preset,
    ProjectRole,
    RecordsBackend,
    parse_portable_policy,
)


class TestProjectPolicySchemaSerialization(unittest.TestCase):
    """Verify ProjectPolicySchema.to_dict preservation of empty and None cutovers/setids."""

    def test_empty_cutovers_and_setids_preserved(self):
        schema = parse_portable_policy({"cutovers": {}, "setids": {}})
        d = schema.to_dict()
        self.assertIn("cutovers", d)
        self.assertEqual(d["cutovers"], {})
        self.assertIn("setids", d)
        self.assertEqual(d["setids"], {})

    def test_none_cutovers_and_setids_omitted(self):
        schema = parse_portable_policy({"cutovers": None, "setids": None})
        d = schema.to_dict()
        self.assertNotIn("cutovers", d)
        self.assertNotIn("setids", d)


class TestPersistProjectPolicyPreservation(unittest.TestCase):
    """Verify persist_project_policy preserves project.json and local.json fields."""

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

    def test_preserves_full_v2_policy_keys_on_reinstall(self):
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
                "enabled_hosts": ["opencode"],
                "non_secret_consent": {"consent_a": True},
                "cutovers": {"spec_id6": "2020-01-01"},
                "setids": {"warn_length": 10},
                "run": {"retry_budget": 2},
                "release_gate_work_kinds": ["bug", "security"],
                "review_findings_gate": {"strict": True},
                "run_analytics_telemetry": {"enabled": False},
            }
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(initial_proj, f)

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
                non_secret_consent={"consent_b": True},
            )
            persist_project_policy(str(repo), policy, replace_config=False)

            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                res_proj = json.load(f)

            self.assertEqual(res_proj.get("cutovers", {}).get("spec_id6"), "2020-01-01")
            self.assertEqual(res_proj.get("setids"), {"warn_length": 10})
            self.assertEqual(res_proj.get("run"), {"retry_budget": 2})
            self.assertEqual(
                res_proj.get("release_gate_work_kinds"), ["bug", "security"]
            )
            self.assertEqual(res_proj.get("review_findings_gate"), {"strict": True})
            self.assertEqual(
                res_proj.get("run_analytics_telemetry"), {"enabled": False}
            )
            self.assertEqual(
                res_proj.get("non_secret_consent"),
                {"consent_a": True, "consent_b": True},
            )

    def test_preserves_partial_pre_wizard_project_json(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            partial_proj = {
                "cutovers": {"spec_id6": "2020-01-01"},
                "run": {"retry_budget": 4},
            }
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(partial_proj, f)

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=False)

            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                res_proj = json.load(f)

            self.assertEqual(res_proj.get("cutovers", {}).get("spec_id6"), "2020-01-01")
            self.assertEqual(res_proj.get("run"), {"retry_budget": 4})
            self.assertEqual(res_proj.get("schema_version"), 2)
            self.assertEqual(res_proj.get("preset"), Preset.PRIVATE_TARGET.value)

    def test_resets_config_when_replace_config_true(self):
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
                "cutovers": {"spec_id6": "2020-01-01"},
                "setids": {"warn_length": 10},
                "run": {"retry_budget": 2},
            }
            initial_local = {
                "schema_version": 2,
                "project_id": "test_id",
                "human_slug": "old-slug",
                "run_analytics_sharing": {"opt_in": True},
            }
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(initial_proj, f)
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump(initial_local, f)

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=True)

            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                res_proj = json.load(f)
            with open(cfg_dir / "local.json", "r", encoding="utf-8") as f:
                res_local = json.load(f)

            self.assertIsNone(res_proj.get("run"))
            self.assertIsNone(res_proj.get("setids"))
            self.assertEqual(res_local.get("human_slug"), "")
            self.assertIsNone(res_local.get("run_analytics_sharing"))

    def test_preserves_local_json_keys(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            initial_local = {
                "schema_version": 2,
                "project_id": "test_id",
                "human_slug": "my-slug",
                "common_dir": "/common/dir",
                "worktree_path": "/worktree/path",
                "local_aliases": {"al": "alias_val"},
                "runtime_overrides": {"ro": "override_val"},
                "run_analytics_sharing": {"opt_in": True},
            }
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump(initial_local, f)

            policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role=ProjectRole.TARGET.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=False)

            with open(cfg_dir / "local.json", "r", encoding="utf-8") as f:
                res_local = json.load(f)

            self.assertEqual(res_local.get("human_slug"), "my-slug")
            self.assertEqual(res_local.get("common_dir"), "/common/dir")
            self.assertEqual(res_local.get("worktree_path"), "/worktree/path")
            self.assertEqual(res_local.get("local_aliases"), {"al": "alias_val"})
            self.assertEqual(res_local.get("runtime_overrides"), {"ro": "override_val"})
            self.assertEqual(res_local.get("run_analytics_sharing"), {"opt_in": True})

    def test_preserves_companion_dir_for_companion_backend(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            initial_local = {
                "schema_version": 2,
                "project_id": "test_id",
                "companion_dir": "/saved/companion/dir",
            }
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump(initial_local, f)

            policy = ProjectPolicy(
                preset=Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value,
                role=ProjectRole.TARGET.value,
                records_backend=RecordsBackend.COMPANION.value,
                aw_home=str(aw_home),
            )
            persist_project_policy(str(repo), policy, replace_config=False)

            with open(cfg_dir / "local.json", "r", encoding="utf-8") as f:
                res_local = json.load(f)

            self.assertEqual(res_local.get("companion_dir"), "/saved/companion/dir")


class TestResolveExistingPolicyAndNoninteractive(unittest.TestCase):
    """Verify resolve_existing_policy, resolve_policy_noninteractive, and enabled_hosts precedence."""

    def _init_repo(self, path: Path) -> None:
        subprocess.run(["git", "init", str(path)], check=True, capture_output=True)

    def test_resolve_existing_policy_round_trips_fields(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": 2,
                        "role": "source-checkout",
                        "enabled_hosts": ["opencode"],
                        "non_secret_consent": {"telemetry": True},
                    },
                    f,
                )
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": 2,
                        "project_id": "p_id",
                        "companion_dir": "/companion/path",
                    },
                    f,
                )

            ex = resolve_existing_policy(str(repo))
            self.assertIsNotNone(ex)
            assert ex is not None
            self.assertEqual(ex.role, "source-checkout")
            self.assertEqual(ex.enabled_hosts, ["opencode"])
            self.assertEqual(ex.companion_dir, "/companion/path")
            self.assertEqual(ex.non_secret_consent, {"telemetry": True})

    def test_resolve_policy_noninteractive_normalizes_alias_on_local_only(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            local_only_policy = ProjectPolicy(
                preset=Preset.LOCAL_ONLY.value,
                role="source-checkout",
                non_secret_consent={"telemetry": True},
            )
            pol = resolve_policy_noninteractive(
                str(repo),
                existing_policy=local_only_policy,
                explicit_preset="clean-target",
            )
            self.assertEqual(pol.preset, Preset.COMPLETELY_CLEAN_TARGET.value)
            self.assertEqual(pol.delivery_mode, DeliveryMode.CLEAN_DELTA.value)
            self.assertEqual(pol.records_backend, RecordsBackend.HOME.value)
            self.assertEqual(pol.role, "source-checkout")
            self.assertEqual(pol.non_secret_consent, {"telemetry": True})

    def test_resolve_policy_noninteractive_cross_placement_guard_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            priv_policy = ProjectPolicy(
                preset=Preset.PRIVATE_TARGET.value,
                role="source-checkout",
                non_secret_consent={"telemetry": True},
            )
            with self.assertRaises(InvalidPolicyError) as cm:
                resolve_policy_noninteractive(
                    str(repo),
                    existing_policy=priv_policy,
                    explicit_preset="clean-target",
                )
            msg = str(cm.exception)
            self.assertIn("private-target", msg)
            self.assertIn("completely-clean-target", msg)
            self.assertIn("--relocate", msg)

    def test_resolve_project_context_enabled_hosts_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            repo = tpath / "repo"
            repo.mkdir()
            self._init_repo(repo)

            # 1. Built-in defaults when nothing stored
            ctx1 = resolve_project_context(target_repo=str(repo))
            self.assertEqual(ctx1.enabled_hosts, DEFAULT_ENABLED_HOSTS)
            self.assertEqual(
                ctx1.provenance["enabled_hosts"]["source"],
                PrecedenceLevel.BUILTIN_DEFAULTS.value,
            )

            # 2. Project policy durable config
            cfg_dir = repo / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump({"schema_version": 2, "enabled_hosts": ["opencode"]}, f)
            ctx2 = resolve_project_context(target_repo=str(repo))
            self.assertEqual(ctx2.enabled_hosts, ["opencode"])
            self.assertEqual(
                ctx2.provenance["enabled_hosts"]["source"],
                PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            )

            # 3. Machine-local binding takes precedence over project policy
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump({"schema_version": 2, "enabled_hosts": ["antigravity"]}, f)
            ctx3 = resolve_project_context(target_repo=str(repo))
            self.assertEqual(ctx3.enabled_hosts, ["antigravity"])
            self.assertEqual(
                ctx3.provenance["enabled_hosts"]["source"],
                PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            )

            # 4. Explicit flags take highest precedence
            ctx4 = resolve_project_context(
                target_repo=str(repo), enabled_hosts=["claude"]
            )
            self.assertEqual(ctx4.enabled_hosts, ["claude"])
            self.assertEqual(
                ctx4.provenance["enabled_hosts"]["source"],
                PrecedenceLevel.EXPLICIT_FLAGS.value,
            )


@pytest.mark.slow
class TestReinstallPreservesConfigSubprocess(unittest.TestCase):
    """Subprocess integration tests for aw install config preservation."""

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

    def _make_env(self, tpath: Path, aw_home: Path, xdg_home: Path) -> dict:
        return dict(
            os.environ,
            PYTHONPATH=f"{self.repo_root}:{os.environ.get('PYTHONPATH', '')}",
            AW_NO_REEXEC="1",
            HOME=str(tpath),
            AW_HOME=str(aw_home),
            XDG_CONFIG_HOME=str(xdg_home),
        )

    def test_subprocess_fresh_repo_defaults_to_private_target(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "fresh"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                r.returncode, 0, f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
            )
            ctx = resolve_project_context(target_repo=str(repo), aw_home=str(aw_home))
            self.assertEqual(ctx.preset, Preset.PRIVATE_TARGET.value)

    def test_subprocess_reinstall_private_target_preserves_all_keys(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            r_init = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r_init.returncode, 0)

            cfg_dir = repo / ".aw" / "config"
            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj = json.load(f)
            proj["cutovers"] = {"spec_id6": "2020-01-01"}
            proj["setids"] = {"warn_length": 10}
            proj["run"] = {"retry_budget": 2}
            proj["release_gate_work_kinds"] = ["bug", "security"]
            proj["enabled_hosts"] = ["opencode"]
            proj["role"] = "source-checkout"
            proj["non_secret_consent"] = {"telemetry_prompted": True}
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(proj, f)

            with open(cfg_dir / "local.json", "r", encoding="utf-8") as f:
                local_data = json.load(f)
            local_data["run_analytics_sharing"] = {"opt_in": True}
            local_data["runtime_overrides"] = {"run_analytics_telemetry": False}
            with open(cfg_dir / "local.json", "w", encoding="utf-8") as f:
                json.dump(local_data, f)

            r_re = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                r_re.returncode, 0, f"STDOUT:\n{r_re.stdout}\nSTDERR:\n{r_re.stderr}"
            )

            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj_after = json.load(f)
            with open(cfg_dir / "local.json", "r", encoding="utf-8") as f:
                local_after = json.load(f)

            self.assertEqual(proj_after.get("preset"), Preset.PRIVATE_TARGET.value)
            self.assertEqual(
                proj_after.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_after.get("setids"), {"warn_length": 10})
            self.assertEqual(proj_after.get("run"), {"retry_budget": 2})
            self.assertEqual(
                proj_after.get("release_gate_work_kinds"), ["bug", "security"]
            )
            self.assertEqual(proj_after.get("enabled_hosts"), ["opencode"])
            self.assertEqual(proj_after.get("role"), "source-checkout")
            self.assertEqual(
                proj_after.get("non_secret_consent"), {"telemetry_prompted": True}
            )
            self.assertEqual(local_after.get("run_analytics_sharing"), {"opt_in": True})
            self.assertEqual(
                local_after.get("runtime_overrides"),
                {"run_analytics_telemetry": False},
            )

    def test_subprocess_reinstall_local_only_preserves_all_keys(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "local"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            r_init = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "local-only",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r_init.returncode, 0)

            ctx = resolve_project_context(target_repo=str(repo), aw_home=str(aw_home))
            cfg_dir = Path(ctx.physical_classes["config_project"]).parent
            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj = json.load(f)
            proj["cutovers"] = {"spec_id6": "2020-01-01"}
            proj["run"] = {"retry_budget": 5}
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(proj, f)

            r_re = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r_re.returncode, 0)

            ctx2 = resolve_project_context(target_repo=str(repo), aw_home=str(aw_home))
            self.assertEqual(ctx2.preset, Preset.LOCAL_ONLY.value)
            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj_after = json.load(f)
            self.assertEqual(
                proj_after.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_after.get("run"), {"retry_budget": 5})

    def test_subprocess_reinstall_private_target_to_local_only_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                check=True,
                capture_output=True,
            )

            proj_file = repo / ".aw" / "config" / "project.json"
            before_bytes = proj_file.read_bytes()

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "local-only",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 1)
            after_bytes = proj_file.read_bytes()
            self.assertEqual(before_bytes, after_bytes)
            output = r.stdout + r.stderr
            self.assertIn("--relocate", output)
            self.assertIn("Switching config placement", output)

    def test_subprocess_reinstall_local_only_to_clean_target_normalizes_and_preserves(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            aw_home = tpath / "aw_home"
            aw_home.mkdir()
            xdg_home = tpath / "xdg"
            xdg_home.mkdir()
            repo = tpath / "repo"
            repo.mkdir()
            self._init_git_repo(repo)

            env = self._make_env(tpath, aw_home, xdg_home)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "local-only",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                check=True,
                capture_output=True,
            )

            ctx = resolve_project_context(target_repo=str(repo), aw_home=str(aw_home))
            cfg_dir = Path(ctx.physical_classes["config_project"]).parent
            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj = json.load(f)
            proj["cutovers"] = {"spec_id6": "2020-01-01"}
            proj["run"] = {"retry_budget": 5}
            with open(cfg_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(proj, f)

            r = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(repo),
                    "--preset",
                    "completely-clean-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                r.returncode, 0, f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
            )

            ctx2 = resolve_project_context(target_repo=str(repo), aw_home=str(aw_home))
            self.assertEqual(ctx2.preset, Preset.COMPLETELY_CLEAN_TARGET.value)
            with open(cfg_dir / "project.json", "r", encoding="utf-8") as f:
                proj_after = json.load(f)
            self.assertEqual(
                proj_after.get("cutovers", {}).get("spec_id6"), "2020-01-01"
            )
            self.assertEqual(proj_after.get("run"), {"retry_budget": 5})

"""Tests for clean-target project config and install state under AW_HOME (p425hv).

Validates that:
(a) clean-target install leaves no <target>/.aw/config and no <target>/.aw/state, and
    git status --porcelain --ignored -- .aw/config .aw/state is empty;
(b) project.json, local.json, install.json, history/installs.jsonl exist under
    AW_HOME/projects/<id>/ where <id> equals resolve_project_context(...).project_id,
    is non-empty, and equals the id in the dry-run's printed paths; nothing exists at
    AW_HOME/projects/state;
(c) a second clean-target install exits 0, keeps the stored preset, and appends a
    second history line in the same home file;
(d) config.resolve_cutover_date(repo, "spec_id6") returns the date stamped in the home project.json;
(e) a private-target install still writes <target>/.aw/config/project.json (staged) and
    local.json (ignored) and nothing under AW_HOME/projects/*/config;
(f) a target pre-seeded with the OLD polluted layout (target local.json with project_id: ""
    and a target project.json) resolves a non-empty project id and keeps reading the target config;
(g) cases (a) and (b) repeated for --preset local-only;
(h) after a clean-target install, aw doctor reports the stored preset;
(i) after a clean-target install, aw uninstall . -y removes the home config and state files
    and a following install exits 0 as a first install;
(j) a public-target-private-companion install is unchanged (its config_project stays under
    the target, its delivery_mode is tracked).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import shutil
from pathlib import Path

import pytest

from agent_workflows import config, ipd_lifecycle
from agent_workflows.project_context import project_config_dir, resolve_project_context


class TestCleanTargetConfigHome(unittest.TestCase):
    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.test_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.test_dir.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.home = self.base / "fake_home"
        self.home.mkdir()
        self.aw_home = self.home / ".aw"
        self.aw_home.mkdir()

        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(self.repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(self.repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.repo),
            check=True,
        )
        (self.repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit"], cwd=str(self.repo), check=True
        )

        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["AW_HOME"] = str(self.aw_home)
        self.env["XDG_CONFIG_HOME"] = str(self.home / ".config")
        self.env["AW_NO_REEXEC"] = "1"
        repo_root = Path(__file__).resolve().parent.parent
        self.env["PYTHONPATH"] = f"{repo_root}:{self.env.get('PYTHONPATH', '')}"

        self._orig_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

    def tearDown(self) -> None:
        if self._orig_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._orig_aw_home
        self.test_dir.cleanup()

    def _run_aw(
        self, *args: str, check: bool = True, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        return subprocess.run(
            cmd,
            cwd=str(cwd or self.repo),
            env=self.env,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_case_a_clean_target_no_target_config_or_state(self) -> None:
        """Case (a): clean-target install leaves no <target>/.aw/config and no <target>/.aw/state."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        # Assert no .aw/config and no .aw/state in the target
        self.assertFalse((self.repo / ".aw" / "config").exists())
        self.assertFalse((self.repo / ".aw" / "state").exists())

        # Check git status for .aw/config and .aw/state
        res = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--ignored",
                "--",
                ".aw/config",
                ".aw/state",
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")

    def test_case_b_home_project_id_and_files(self) -> None:
        """Case (b): project.json, local.json, install.json, history/installs.jsonl exist under AW_HOME/projects/<id>/."""
        dry_res = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
            "--dry-run",
        )
        match = re.search(r"projects/([^/\s]+)/config/project\.json", dry_res.stdout)
        self.assertIsNotNone(
            match, f"Failed to extract project id from dry-run: {dry_res.stdout}"
        )
        dry_pid = match.group(1)
        self.assertTrue(bool(dry_pid.strip()))

        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(ctx.project_id, dry_pid)
        self.assertTrue(bool(ctx.project_id.strip()))

        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())
        self.assertTrue((proj_dir / "config" / "local.json").is_file())
        self.assertTrue((proj_dir / "state" / "durable" / "install.json").is_file())
        self.assertTrue(
            (proj_dir / "state" / "durable" / "history" / "installs.jsonl").is_file()
        )

        # Nothing exists at AW_HOME/projects/state
        self.assertFalse((self.aw_home / "projects" / "state").exists())

        # local.json carries the non-empty project_id
        local_data = json.loads(
            (proj_dir / "config" / "local.json").read_text(encoding="utf-8")
        )
        self.assertEqual(local_data.get("project_id"), ctx.project_id)

    def test_case_c_second_install_keeps_preset_appends_history(self) -> None:
        """Case (c): second clean-target install exits 0, keeps stored preset, and appends a second history line."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(ctx.preset, "completely-clean-target")

        proj_dir = self.aw_home / "projects" / ctx.project_id
        hist_file = proj_dir / "state" / "durable" / "history" / "installs.jsonl"
        lines = [
            line.strip()
            for line in hist_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 2)

    def test_case_d_cutover_date_resolved_from_home_config(self) -> None:
        """Case (d): config.resolve_cutover_date(repo, 'spec_id6') returns the date stamped in the home project.json."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )

        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_json = (
            self.aw_home / "projects" / ctx.project_id / "config" / "project.json"
        )
        pdata = json.loads(proj_json.read_text(encoding="utf-8"))
        pdata.setdefault("cutovers", {})["spec_id6"] = "2026-10-12"
        proj_json.write_text(json.dumps(pdata, indent=2), encoding="utf-8")

        # Set AW_HOME in os.environ for in-process resolution
        old_aw_home = os.environ.get("AW_HOME")
        try:
            os.environ["AW_HOME"] = str(self.aw_home)
            c_date = config.resolve_cutover_date(self.repo, "spec_id6")
            self.assertEqual(c_date, "20261012")
        finally:
            if old_aw_home is not None:
                os.environ["AW_HOME"] = old_aw_home
            else:
                os.environ.pop("AW_HOME", None)

    def test_case_e_private_target_writes_target_config(self) -> None:
        """Case (e): private-target install still writes <target>/.aw/config/project.json and local.json."""
        self._run_aw(
            "install", ".", "--preset", "private-target", "-y", "--no-interactive"
        )

        self.assertTrue((self.repo / ".aw" / "config" / "project.json").is_file())
        self.assertTrue((self.repo / ".aw" / "config" / "local.json").is_file())

        # No home config directories created
        projects_dir = self.aw_home / "projects"
        if projects_dir.exists():
            home_configs = list(projects_dir.glob("*/config"))
            self.assertEqual(home_configs, [])

    def test_case_f_legacy_polluted_target_preserved(self) -> None:
        """Case (f): target pre-seeded with old polluted layout resolves non-empty id and reads target config."""
        cfg_dir = self.repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "project.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "preset": "completely-clean-target",
                    "delivery_mode": "clean-delta",
                }
            ),
            encoding="utf-8",
        )
        (cfg_dir / "local.json").write_text(
            json.dumps({"schema_version": 2, "project_id": ""}),
            encoding="utf-8",
        )

        old_aw_home = os.environ.get("AW_HOME")
        try:
            os.environ["AW_HOME"] = str(self.aw_home)
            pcd = project_config_dir(self.repo)
            self.assertEqual(pcd, cfg_dir)

            ctx = resolve_project_context(target_repo=str(self.repo))
            self.assertTrue(bool(ctx.project_id.strip()))
            self.assertEqual(ctx.preset, "completely-clean-target")
        finally:
            if old_aw_home is not None:
                os.environ["AW_HOME"] = old_aw_home
            else:
                os.environ.pop("AW_HOME", None)

    def test_case_g_local_only_preset(self) -> None:
        """Case (g): cases (a) and (b) repeated for --preset local-only."""
        # Case (a) for local-only
        self._run_aw("install", ".", "--preset", "local-only", "-y", "--no-interactive")
        self.assertFalse((self.repo / ".aw" / "config").exists())
        self.assertFalse((self.repo / ".aw" / "state").exists())

        res = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--ignored",
                "--",
                ".aw/config",
                ".aw/state",
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(res.stdout.strip(), "")

        # Case (b) for local-only
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        self.assertTrue(bool(ctx.project_id.strip()))
        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())
        self.assertTrue((proj_dir / "config" / "local.json").is_file())
        self.assertTrue((proj_dir / "state" / "durable" / "install.json").is_file())
        self.assertTrue(
            (proj_dir / "state" / "durable" / "history" / "installs.jsonl").is_file()
        )
        self.assertFalse((self.aw_home / "projects" / "state").exists())

    def test_case_h_doctor_reports_preset(self) -> None:
        """Case (h): after a clean-target install, aw doctor reports the stored preset."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        doc_res = self._run_aw("doctor", check=False)
        self.assertIn("preset: completely-clean-target", doc_res.stdout)

    def test_case_i_uninstall_cleans_home_and_allows_reinstall(self) -> None:
        """Case (i): after clean-target install, aw uninstall . -y removes home files and allows reinstall."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue((proj_dir / "config" / "project.json").is_file())

        un_res = self._run_aw("uninstall", ".", "-y")
        self.assertFalse((proj_dir / "config" / "project.json").exists())
        self.assertFalse((proj_dir / "state").exists())
        self.assertIn("removed", un_res.stdout)

        re_res = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self.assertEqual(re_res.returncode, 0)
        self.assertTrue((proj_dir / "config" / "project.json").is_file())

    def test_case_j_public_target_private_companion(self) -> None:
        """Case (j): public-target-private-companion install keeps config_project in target and tracked delivery."""
        companion_repo = self.base / "companion_repo"
        companion_repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(companion_repo), check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(companion_repo),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(companion_repo),
            check=True,
        )
        (companion_repo / "README.md").write_text("# Companion\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(companion_repo), check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit"],
            cwd=str(companion_repo),
            check=True,
        )

        self._run_aw(
            "install",
            ".",
            "--preset",
            "public-target-private-companion",
            "--companion-dir",
            str(companion_repo),
            "-y",
            "--no-interactive",
        )

        self.assertTrue((self.repo / ".aw" / "config" / "project.json").is_file())
        ctx = resolve_project_context(
            target_repo=str(self.repo), companion_dir=str(companion_repo)
        )
        self.assertEqual(ctx.delivery_mode, "tracked")

    def test_case_k_clean_target_install_zero_target_delta(self) -> None:
        """Case (k): clean-target install (both presets) leaves zero target delta and writes home state."""
        for i, preset in enumerate(("completely-clean-target", "local-only")):
            target = self.base / f"repo_k_{i}"
            target.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main", "-q"], cwd=str(target), check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=str(target), check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=str(target),
                check=True,
            )
            (target / "README.md").write_text("# Test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=str(target), check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=str(target), check=True
            )

            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            res = self._run_aw(
                "install", ".", "--preset", preset, "-y", "--no-interactive", cwd=target
            )
            self.assertEqual(res.returncode, 0, f"Install failed: {res.stderr}")

            head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(
                head_before, head_after, f"HEAD changed under preset {preset}"
            )

            status = subprocess.run(
                ["git", "status", "--porcelain", "--ignored"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(
                status,
                "",
                f"Target git status is not empty under preset {preset}: {status}",
            )

            for forbidden in (
                target / ".aw",
                target / "AGENTS.md",
                target / ".agents",
                target / ".claude",
                target / ".opencode",
                target / ".github",
                target / ".gitignore",
                target / ".gitleaksignore",
            ):
                self.assertFalse(
                    forbidden.exists(), f"Forbidden target file exists: {forbidden}"
                )

            ctx = resolve_project_context(
                target_repo=str(target), aw_home=str(self.aw_home)
            )
            proj_dir = self.aw_home / "projects" / ctx.project_id
            runtime_state = proj_dir / "state" / "runtime"
            self.assertTrue((runtime_state / "setup-repo-needed.md").is_file())
            created_files = list(
                (runtime_state / "backups").glob("*/.created-files.json")
            )
            self.assertTrue(
                len(created_files) >= 1,
                "Expected .created-files.json in home runtime backups",
            )

    @pytest.mark.xfail(strict=False, reason="bug: 96lj37 - hardcodes file count")
    def test_case_l_tracked_install_still_writes_target(self) -> None:
        """Case (l): tracked private-target install still writes target, commits under -y, and matches baseline."""
        target = self.base / "repo_l"
        target.mkdir()
        subprocess.run(["git", "init", "-b", "main", "-q"], cwd=str(target), check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(target), check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(target),
            check=True,
        )
        (target / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(target), check=True)
        subprocess.run(
            ["git", "commit", "-qm", "initial commit"], cwd=str(target), check=True
        )

        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(target),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        res = self._run_aw(
            "install",
            ".",
            "--preset",
            "private-target",
            "-y",
            "--no-interactive",
            cwd=target,
        )
        self.assertEqual(res.returncode, 0)

        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(target),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertNotEqual(
            head_before, head_after, "Expected commit under private-target -y"
        )

        self.assertTrue((target / "AGENTS.md").is_file())
        self.assertTrue((target / ".aw" / ".gitignore").is_file())
        self.assertTrue((target / ".agent-workflows-installer-backups").is_dir())

        self.assertIn("Git: changes staged; commit offered below", res.stdout)
        commit_paths = set(
            subprocess.run(
                ["git", "show", "--name-only", "--format=", "HEAD"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        )
        tracked_paths = set(
            subprocess.run(
                ["git", "ls-files"],
                cwd=str(target),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        ) - {"README.md"}
        self.assertEqual(commit_paths, tracked_paths)
        self.assertTrue(len(commit_paths) > 0)
        self.assertIn("AGENTS.md", commit_paths)
        self.assertIn(".aw/.gitignore", commit_paths)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(target),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(status, "")

    def test_case_m_clean_target_reinstall_and_rollback(self) -> None:
        """Case (m): clean-delta reinstall is a no-op on target, and rollback removes home files leaving target empty."""
        from agent_workflows import engine

        res1 = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self.assertEqual(res1.returncode, 0)

        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Second install
        res2 = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self.assertEqual(res2.returncode, 0)

        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(head_before, head_after)

        status = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(status, "")

        # Rollback
        rc = engine.run_rollback(self.repo, True)
        self.assertEqual(rc, 0)

        status_after_rollback = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(status_after_rollback, "")

    def test_case_n_engine_run_shell_clean_target(self) -> None:
        """Case (n): engine.run() in-process presentation shell on clean-delta target leaves HEAD unchanged."""
        from agent_workflows import engine
        from agent_workflows.install_wizard import (
            persist_project_policy,
            resolve_policy_noninteractive,
        )

        policy = resolve_policy_noninteractive(
            str(self.repo),
            explicit_preset="completely-clean-target",
            explicit_aw_home=str(self.aw_home),
        )
        persist_project_policy(str(self.repo), policy)

        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        args = engine.parse_args(["--repo", str(self.repo), "-y", "--no-color"])
        rc = engine.run(args)
        self.assertEqual(rc, 0)

        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(head_before, head_after)

        status = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertEqual(status, "")

    def test_is_clean_delta_install(self) -> None:
        """Unit test for engine._is_clean_delta_install covering all E-02 cases."""
        from agent_workflows import engine
        from agent_workflows.install_wizard import (
            persist_project_policy,
            resolve_policy_noninteractive,
        )

        # 1. completely-clean-target -> True
        repo_clean = self.base / "repo_pred_clean"
        repo_clean.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(repo_clean), check=True
        )
        pol_clean = resolve_policy_noninteractive(
            str(repo_clean),
            explicit_preset="completely-clean-target",
            explicit_aw_home=str(self.aw_home),
        )
        persist_project_policy(str(repo_clean), pol_clean)
        self.assertTrue(engine._is_clean_delta_install(repo_clean))

        # 2. local-only -> True
        repo_local = self.base / "repo_pred_local"
        repo_local.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(repo_local), check=True
        )
        pol_local = resolve_policy_noninteractive(
            str(repo_local),
            explicit_preset="local-only",
            explicit_aw_home=str(self.aw_home),
        )
        persist_project_policy(str(repo_local), pol_local)
        self.assertTrue(engine._is_clean_delta_install(repo_local))

        # 3. private-target -> False
        repo_priv = self.base / "repo_pred_priv"
        repo_priv.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(repo_priv), check=True
        )
        pol_priv = resolve_policy_noninteractive(
            str(repo_priv),
            explicit_preset="private-target",
            explicit_aw_home=str(self.aw_home),
        )
        persist_project_policy(str(repo_priv), pol_priv)
        self.assertFalse(engine._is_clean_delta_install(repo_priv))

        # 4. public-target-private-companion -> False
        repo_comp = self.base / "repo_pred_comp"
        repo_comp.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(repo_comp), check=True
        )
        comp_dir = self.base / "repo_pred_comp_store"
        comp_dir.mkdir()
        pol_comp = resolve_policy_noninteractive(
            str(repo_comp),
            explicit_preset="public-target-private-companion",
            explicit_companion=str(comp_dir),
            explicit_aw_home=str(self.aw_home),
        )
        persist_project_policy(str(repo_comp), pol_comp)
        self.assertFalse(engine._is_clean_delta_install(repo_comp))

        # 5. unconfigured repo -> False
        repo_unconf = self.base / "repo_pred_unconf"
        repo_unconf.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=str(repo_unconf), check=True
        )
        self.assertFalse(engine._is_clean_delta_install(repo_unconf))

        # 6. stored-tracked repo -> False
        self.assertFalse(engine._is_clean_delta_install(repo_priv))

        # 7. user config default_delivery_mode: clean-delta but no stored policy in repo -> False
        user_cfg_dir = self.home / ".config" / "agent-workflows"
        user_cfg_dir.mkdir(parents=True, exist_ok=True)
        (user_cfg_dir / "config.json").write_text(
            json.dumps({"default_delivery_mode": "clean-delta"}), encoding="utf-8"
        )
        self.assertFalse(engine._is_clean_delta_install(repo_unconf))

    def test_setup_marker_clean_target(self) -> None:
        """Setup marker test: attention.setup_needed True after install and False after remove_setup_marker."""
        from agent_workflows import attention, engine

        res = self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue(attention.setup_needed(self.repo))

        removed = engine.remove_setup_marker(self.repo)
        self.assertTrue(removed)
        self.assertFalse(attention.setup_needed(self.repo))

    def test_case_o_uninstall_keeps_home_records(self) -> None:
        """Case (o): aw uninstall --yes on clean targets keeps home records byte-identical and cleans everything else."""
        import hashlib

        for preset in ("completely-clean-target", "local-only"):
            with self.subTest(preset=preset):
                r = self.base / f"repo_o_{preset}"
                r.mkdir()
                subprocess.run(
                    ["git", "init", "-b", "main", "-q"], cwd=str(r), check=True
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test User"],
                    cwd=str(r),
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.email", "test@example.com"],
                    cwd=str(r),
                    check=True,
                )
                (r / "README.md").write_text("# Test\n", encoding="utf-8")
                subprocess.run(["git", "add", "README.md"], cwd=str(r), check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=str(r), check=True
                )

                self._run_aw(
                    "install",
                    str(r),
                    "--preset",
                    preset,
                    "-y",
                    "--no-interactive",
                )
                self._run_aw(
                    "backlog",
                    "new",
                    "--summary",
                    f"item for {preset}",
                    "--priority",
                    "high",
                    "--work-kind",
                    "bug",
                    "--apply",
                    cwd=r,
                )

                ctx = resolve_project_context(
                    target_repo=str(r), aw_home=str(self.aw_home)
                )
                proj_dir = self.aw_home / "projects" / ctx.project_id
                rec_dir = proj_dir / "records"
                self.assertTrue(rec_dir.is_dir())

                def hash_records():
                    hashes = {}
                    for p in sorted(rec_dir.rglob("*")):
                        if p.is_file():
                            rel = p.relative_to(rec_dir).as_posix()
                            hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
                    return hashes

                before_hashes = hash_records()
                self.assertTrue(len(before_hashes) > 0)

                head_proc = subprocess.run(
                    ["git", "-C", str(r), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                head_before = head_proc.stdout.strip()

                un_res = self._run_aw("uninstall", str(r), "--yes")
                self.assertEqual(un_res.returncode, 0)
                self.assertNotIn("Deletions are STAGED", un_res.stdout)
                self.assertNotIn("Deletions are STAGED", un_res.stderr)
                self.assertNotIn("Traceback", un_res.stderr)

                # Home system, config, state, worktrees are absent
                self.assertFalse((proj_dir / "system").exists())
                self.assertFalse((proj_dir / "config").exists())
                self.assertFalse((proj_dir / "state").exists())
                self.assertFalse((proj_dir / "worktrees").exists())

                # records/ is present and byte-identical
                self.assertTrue(rec_dir.is_dir())
                after_hashes = hash_records()
                self.assertEqual(before_hashes, after_hashes)

                # Target git status porcelain ignored is empty and HEAD is unchanged
                st_proc = subprocess.run(
                    ["git", "-C", str(r), "status", "--porcelain", "--ignored"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(st_proc.stdout.strip(), "")
                head_proc_after = subprocess.run(
                    ["git", "-C", str(r), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertEqual(head_proc_after.stdout.strip(), head_before)

    def test_case_p_uninstall_deep_removes_project_dir(self) -> None:
        """Case (p): aw uninstall --deep --yes removes project directory completely."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self._run_aw(
            "backlog",
            "new",
            "--summary",
            "item deep",
            "--priority",
            "high",
            "--work-kind",
            "bug",
            "--apply",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id
        self.assertTrue(proj_dir.is_dir())

        un_res = self._run_aw("uninstall", ".", "--deep", "--yes")
        self.assertEqual(un_res.returncode, 0)
        self.assertFalse(proj_dir.exists())

        st_proc = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(st_proc.stdout.strip(), "")

    def test_case_q_uninstall_tears_down_idle_lane(self) -> None:
        """Case (q): uninstall tears down idle branch lane, merged lane, and detached checkout."""
        from agent_workflows import worktree_lease

        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id

        # 1. Idle branch lane
        worktree_lease.allocate_worktree(self.repo, "idle01")
        worktree_lease.clear_lane_owner(self.repo, "idle01")

        # 2. Already-merged lane
        h2 = worktree_lease.allocate_worktree(self.repo, "mrg002")
        (Path(h2.path) / "test.txt").write_text("merged content\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(h2.path), "add", "test.txt"], check=True)
        subprocess.run(
            ["git", "-C", str(h2.path), "commit", "-qm", "merge commit"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "merge", "--ff-only", h2.branch],
            check=True,
        )
        worktree_lease.clear_lane_owner(self.repo, "mrg002")

        # 3. Detached checkout under state/suite-baselines/
        baseline_dir = proj_dir / "state" / "suite-baselines" / "base-01"
        baseline_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "worktree",
                "add",
                "--detach",
                str(baseline_dir),
                "HEAD",
            ],
            check=True,
            capture_output=True,
        )

        un_res = self._run_aw("uninstall", ".", "--yes")
        self.assertEqual(un_res.returncode, 0)

        # Afterwards:
        git_wt_dir = self.repo / ".git" / "worktrees"
        if git_wt_dir.exists():
            self.assertEqual(len(list(git_wt_dir.iterdir())), 0)
        br_proc = subprocess.run(
            ["git", "-C", str(self.repo), "branch", "--list", "aw/lane/*"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(br_proc.stdout.strip(), "")
        wt_proc = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line.strip() for line in wt_proc.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("main", lines[0])

    def test_case_r_uninstall_refuses_live_lane(self) -> None:
        """Case (r): uninstall refuses while a lane is live-owned; refuses holds-work without --force; proceeds under --force."""
        from agent_workflows import worktree_lease

        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id

        # Live-owned lane
        h_live = worktree_lease.allocate_worktree(self.repo, "live01")
        worktree_lease.write_lane_owner(self.repo, "live01")

        # Plain --yes refuses with exit 1
        res1 = self._run_aw("uninstall", ".", "--yes", check=False)
        self.assertEqual(res1.returncode, 1)
        self.assertIn("live01", res1.stderr + res1.stdout)
        self.assertTrue((proj_dir / "system").exists())
        self.assertTrue((proj_dir / "config").exists())
        self.assertTrue((proj_dir / "state").exists())
        self.assertTrue((proj_dir / "worktrees").exists())

        # --yes --force ALSO refuses when live
        res_force = self._run_aw("uninstall", ".", "--yes", "--force", check=False)
        self.assertEqual(res_force.returncode, 1)
        self.assertIn("live01", res_force.stderr + res_force.stdout)
        self.assertTrue((proj_dir / "system").exists())

        # Now test dirty non-live lane
        worktree_lease.clear_lane_owner(self.repo, "live01")
        worktree_lease.teardown_worktree(self.repo, h_live, force=True)

        h_dirty = worktree_lease.allocate_worktree(self.repo, "dirty02")
        worktree_lease.clear_lane_owner(self.repo, "dirty02")
        (Path(h_dirty.path) / "dirty.txt").write_text(
            "uncommitted work\n", encoding="utf-8"
        )

        res_dirty_no_force = self._run_aw("uninstall", ".", "--yes", check=False)
        self.assertEqual(res_dirty_no_force.returncode, 1)
        self.assertIn("dirty02", res_dirty_no_force.stderr + res_dirty_no_force.stdout)

        res_dirty_force = self._run_aw(
            "uninstall", ".", "--yes", "--force", check=False
        )
        self.assertEqual(res_dirty_force.returncode, 0)
        self.assertIn("dirty02", res_dirty_force.stderr + res_dirty_force.stdout)

    def test_case_s_uninstall_refuses_live_driver(self) -> None:
        """Case (s): uninstall refuses while a peer driver holds driver.lock."""
        from agent_workflows import platform_lock

        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id

        run_dir = proj_dir / "records" / "runs" / "run-20261016T120000Z-999999"
        run_dir.mkdir(parents=True, exist_ok=True)
        lock_file = run_dir / "driver.lock"

        with platform_lock.acquire(lock_file):
            res = self._run_aw("uninstall", ".", "--yes", check=False)
            self.assertEqual(res.returncode, 1)
            self.assertIn("run-20261016T120000Z-999999", res.stderr + res.stdout)
            self.assertTrue((proj_dir / "system").exists())
            self.assertTrue((proj_dir / "config").exists())
            self.assertTrue((proj_dir / "state").exists())

    def test_case_t_uninstall_dry_run_lists_home_trees(self) -> None:
        """Case (t): dry-run lists all home trees with counts and ~-relative paths, changing nothing."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        self._run_aw(
            "backlog",
            "new",
            "--summary",
            "item t",
            "--priority",
            "high",
            "--work-kind",
            "bug",
            "--apply",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id

        res = self._run_aw("uninstall", ".", "--dry-run")
        self.assertEqual(res.returncode, 0)
        out = res.stdout

        self.assertIn("system:", out)
        self.assertIn("config:", out)
        self.assertIn("state:", out)
        self.assertIn("worktrees:", out)
        self.assertIn("records", out)

        # No line contains the temp HOME absolute prefix
        self.assertNotIn(str(self.home), out)
        self.assertNotIn(str(self.home), res.stderr)

        # Nothing changes
        self.assertTrue((proj_dir / "system").exists())
        self.assertTrue((proj_dir / "config").exists())
        self.assertTrue((proj_dir / "state").exists())
        self.assertTrue((proj_dir / "records").exists())

    def test_case_u_uninstall_recovers_partial(self) -> None:
        """Case (u): partial-uninstall recovery deletes leftover home system and worktrees even when config is gone."""
        self._run_aw(
            "install",
            ".",
            "--preset",
            "completely-clean-target",
            "-y",
            "--no-interactive",
        )
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        proj_dir = self.aw_home / "projects" / ctx.project_id

        # Delete config by hand to simulate partial uninstall
        shutil.rmtree(proj_dir / "config")
        self.assertFalse((proj_dir / "config").exists())
        self.assertTrue((proj_dir / "system").exists())

        res1 = self._run_aw("uninstall", ".", "--yes")
        self.assertEqual(res1.returncode, 0)
        self.assertFalse((proj_dir / "system").exists())
        self.assertFalse((proj_dir / "worktrees").exists())

        # Second run reports framework not installed
        res2 = self._run_aw("uninstall", ".", "--yes", check=False)
        self.assertEqual(res2.returncode, 1)
        self.assertIn("framework not installed", res2.stderr + res2.stdout)


if __name__ == "__main__":
    unittest.main()

"""Regression tests for `aw work begin` plan_path relativization (IPD t1fri2).

Verifies that:
1. For clean-delta presets (`completely-clean-target`, `local-only`), plans living outside
   the repo root under AW_HOME do not cause `ValueError` when `aw work begin` relativizes
   the plan path, and the resulting lease `plan_path` is a resolved absolute POSIX path.
2. For tracked-records installs, `aw work begin` writes a repo-relative POSIX path
   (not absolute) into the lease and places no lease under AW_HOME.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle
from agent_workflows.project_context import resolve_project_context


class TestWorkBeginPlanPathOutsideRoot(unittest.TestCase):
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
        self.env.pop("XDG_CONFIG_HOME", None)
        self.env.pop("AW_CONFIG_DIR", None)
        self.env["AW_NO_REEXEC"] = "1"
        self.env["AW_IPD_AUTHOR"] = "regression-test"
        repo_root = Path(__file__).resolve().parent.parent
        self.env["PYTHONPATH"] = f"{repo_root}:{self.env.get('PYTHONPATH', '')}"

        self._orig_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

    def tearDown(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        if self._orig_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._orig_aw_home
        self.test_dir.cleanup()

    def _run_aw(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        return subprocess.run(
            cmd,
            cwd=str(self.repo),
            env=self.env,
            capture_output=True,
            text=True,
        )

    def _run_clean_delta_preset_case(self, preset: str) -> None:
        # 1. install with preset
        res = self._run_aw("install", ".", "--preset", preset, "-y", "--no-interactive")
        self.assertEqual(
            res.returncode,
            0,
            f"install failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 2. resolve project context
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        project_id = ctx.project_id
        records_root = Path(ctx.physical_classes["records"])
        self.assertTrue(records_root.is_dir())
        self.assertFalse(records_root.is_relative_to(self.repo))

        # 3. scaffold child plan
        res = self._run_aw(
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            f"Regression probe plan {preset}",
            "--set",
            "regset",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
        )
        self.assertEqual(
            res.returncode,
            0,
            f"scaffold failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        pending_plans = list((records_root / "plans" / "pending").glob("*.ipd.md"))
        self.assertEqual(len(pending_plans), 1)
        plan_file = pending_plans[0]
        m = re.search(
            r"^- Id:\s*([a-z0-9]{6})",
            plan_file.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        self.assertIsNotNone(m, "scaffolded plan must have '- Id: <id6>'")
        id6 = m.group(1)

        # 4. set dependencies to none
        res = self._run_aw("ipd", "dependencies", "set", id6, "none")
        self.assertEqual(
            res.returncode,
            0,
            f"dependencies set failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 5. run work begin
        res = self._run_aw("work", "begin", id6)
        combined_output = res.stdout + res.stderr
        self.assertNotIn("ValueError", combined_output)
        self.assertNotIn("Traceback", combined_output)
        self.assertEqual(
            res.returncode,
            0,
            f"work begin failed with exit {res.returncode}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 6. verify lease
        lease_path = (
            self.aw_home
            / "projects"
            / project_id
            / "state"
            / "work"
            / id6
            / "work-lease.json"
        )
        self.assertTrue(lease_path.is_file(), f"expected lease file at {lease_path}")
        lease = json.loads(lease_path.read_text(encoding="utf-8"))
        plan_path_val = lease.get("plan_path")
        self.assertIsNotNone(plan_path_val)
        self.assertTrue(
            Path(plan_path_val).is_absolute(),
            f"plan_path must be absolute: {plan_path_val}",
        )
        self.assertNotIn(
            "\\",
            plan_path_val,
            f"plan_path must not contain backslash: {plan_path_val}",
        )
        self.assertEqual(Path(plan_path_val).resolve(), plan_file.resolve())
        self.assertEqual(lease.get("plan_id"), id6)
        print(f"[{preset}] observed lease plan_path: {plan_path_val}")

    def test_plan_path_outside_root_completely_clean_target(self) -> None:
        self._run_clean_delta_preset_case("completely-clean-target")

    def test_plan_path_outside_root_local_only(self) -> None:
        self._run_clean_delta_preset_case("local-only")

    def test_plan_path_in_root_tracked_records(self) -> None:
        # 1. install with default in-root tracked records
        res = self._run_aw("install", ".", "-y", "--no-interactive")
        self.assertEqual(
            res.returncode,
            0,
            f"install failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 2. scaffold child plan under repo
        res = self._run_aw(
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "In-root probe plan",
            "--set",
            "inrootset",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
        )
        self.assertEqual(
            res.returncode,
            0,
            f"scaffold failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        pending_plans = list(
            (self.repo / ".aw" / "records" / "plans" / "pending").glob("*.ipd.md")
        )
        self.assertEqual(len(pending_plans), 1)
        plan_file = pending_plans[0]
        m = re.search(
            r"^- Id:\s*([a-z0-9]{6})",
            plan_file.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        self.assertIsNotNone(m, "scaffolded plan must have '- Id: <id6>'")
        id6 = m.group(1)

        # 3. set dependencies to none
        res = self._run_aw("ipd", "dependencies", "set", id6, "none")
        self.assertEqual(
            res.returncode,
            0,
            f"dependencies set failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 4. run work begin
        res = self._run_aw("work", "begin", id6)
        combined_output = res.stdout + res.stderr
        self.assertNotIn("ValueError", combined_output)
        self.assertNotIn("Traceback", combined_output)
        self.assertEqual(
            res.returncode,
            0,
            f"work begin failed with exit {res.returncode}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

        # 5. verify lease
        lease_path = self.repo / ".aw" / "state" / "work" / id6 / "work-lease.json"
        self.assertTrue(lease_path.is_file(), f"expected lease file at {lease_path}")
        lease = json.loads(lease_path.read_text(encoding="utf-8"))
        plan_path_val = lease.get("plan_path")
        self.assertIsNotNone(plan_path_val)
        expected_rel = f".aw/records/plans/pending/{plan_file.name}"
        self.assertEqual(plan_path_val, expected_rel)
        self.assertFalse(
            Path(plan_path_val).is_absolute(),
            f"plan_path must be relative: {plan_path_val}",
        )
        self.assertNotIn(
            "\\",
            plan_path_val,
            f"plan_path must not contain backslash: {plan_path_val}",
        )
        self.assertEqual((self.repo / plan_path_val).resolve(), plan_file.resolve())
        self.assertEqual(lease.get("plan_id"), id6)

        # 6. verify no work-lease.json exists under AW_HOME
        home_leases = list(self.aw_home.glob("**/work-lease.json"))
        self.assertEqual(
            home_leases, [], f"unexpected work-lease.json under AW_HOME: {home_leases}"
        )
        print(f"[tracked-records] observed lease plan_path: {plan_path_val}")

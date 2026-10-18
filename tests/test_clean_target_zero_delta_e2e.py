"""End-to-end zero target delta proof through ordinary use (IPD nwporz).

Demonstrates that for clean-delta presets (`completely-clean-target` and `local-only`):
1. `git status --porcelain --ignored` is empty and `git rev-parse HEAD` is unchanged
   after install, after every ordinary verb, and after uninstall.
2. Every generated artifact lands under `<AW_HOME>/projects/<project_id>/`.
3. Worktrees are isolated under `<AW_HOME>/projects/<project_id>/worktrees/`.
4. Run state lands under `<AW_HOME>/projects/<project_id>/records/runs/`.
5. Uninstall cleans up the worktrees and home runtime/state while preserving records.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle, runner_shared
from agent_workflows.project_context import resolve_project_context


class TestCleanTargetZeroDeltaE2E(unittest.TestCase):
    def setUp(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        self.test_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.test_dir.name).resolve()
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
        self.env["AW_IPD_AUTHOR"] = "e2e"
        repo_root = Path(__file__).resolve().parent.parent
        self.env["PYTHONPATH"] = f"{repo_root}:{self.env.get('PYTHONPATH', '')}"

        self._orig_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

        self._init_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def tearDown(self) -> None:
        ipd_lifecycle.clear_checkout_control_root_cache()
        if self._orig_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._orig_aw_home
        self.test_dir.cleanup()

    def _assert_zero_delta(self, step: str) -> None:
        porcelain = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if porcelain:
            self.fail(
                f"Step '{step}' left target delta (porcelain --ignored):\n{porcelain}"
            )
        if head != self._init_head:
            self.fail(
                f"Step '{step}' changed target HEAD from {self._init_head} to {head}"
            )

    def _run_aw(
        self, *args: str, expected_exit: int = 0, step: str = ""
    ) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "agent_workflows.cli", *args]
        res = subprocess.run(
            cmd,
            cwd=str(self.repo),
            env=self.env,
            capture_output=True,
            text=True,
        )
        if res.returncode != expected_exit:
            self.fail(
                f"Step '{step or ' '.join(args)}' expected exit {expected_exit}, "
                f"got {res.returncode}.\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            )
        return res

    def _run_preset_ordinary_use_sequence(self, preset: str) -> None:
        # Pre-install baseline check
        self._assert_zero_delta("pre-install")

        # 1. install
        self._run_aw(
            "install",
            ".",
            "--preset",
            preset,
            "-y",
            "--no-interactive",
            expected_exit=0,
            step="install",
        )
        self._assert_zero_delta("install")

        # Read project context after install
        ctx = resolve_project_context(
            target_repo=str(self.repo), aw_home=str(self.aw_home)
        )
        project_id = ctx.project_id
        records_root = Path(ctx.physical_classes["records"])
        self.assertTrue(
            records_root.is_dir(), f"records root {records_root} does not exist"
        )
        self.assertFalse(
            records_root.is_relative_to(self.repo),
            f"records root {records_root} must not be inside target repo",
        )

        # 2. backlog new
        self._run_aw(
            "backlog",
            "new",
            "--summary",
            "E2E probe",
            "--work-kind",
            "chore",
            "--priority",
            "low",
            "--apply",
            expected_exit=0,
            step="backlog new",
        )
        self._assert_zero_delta("backlog new")

        # Positive assertion (E-03): backlog item exists under records class root
        backlog_items = list((records_root / "backlog" / "open").glob("*.backlog.md"))
        self.assertTrue(
            len(backlog_items) >= 1, "expected backlog item in home records"
        )
        self.assertFalse(
            (self.repo / ".aw" / "records").exists(),
            "records directory leaked into target",
        )

        # 3. index prompts
        self._run_aw("index", "prompts", expected_exit=0, step="index prompts")
        self._assert_zero_delta("index prompts")

        # 4. research new
        self._run_aw(
            "research",
            "new",
            "--kind",
            "findings",
            "--slug",
            "e2e-probe",
            "--apply",
            expected_exit=0,
            step="research new",
        )
        self._assert_zero_delta("research new")

        # Positive assertion (E-03): research file exists under records class root
        research_files = list((records_root / "research").glob("*e2e-probe*.md"))
        self.assertTrue(
            len(research_files) >= 1, "expected research file in home records"
        )

        # 5. attention
        self._run_aw("attention", expected_exit=0, step="attention")
        self._assert_zero_delta("attention")

        # 6. status
        self._run_aw("status", expected_exit=0, step="status")
        self._assert_zero_delta("status")

        # 7. doctor (exits 1 on fresh install because prompt index manifest not generated, PR-003)
        self._run_aw("doctor", expected_exit=1, step="doctor")
        self._assert_zero_delta("doctor")

        # 8. ipd scaffold
        self._run_aw(
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "E2E probe plan",
            "--set",
            "e2eset",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
            expected_exit=0,
            step="ipd scaffold",
        )
        self._assert_zero_delta("ipd scaffold")

        # Positive assertion (E-03): scaffolded plan exists under records/plans/pending/
        pending_plans = list((records_root / "plans" / "pending").glob("*.ipd.md"))
        self.assertEqual(
            len(pending_plans),
            1,
            f"expected 1 pending plan under {records_root / 'plans' / 'pending'}, found {pending_plans}",
        )
        plan_content = pending_plans[0].read_text(encoding="utf-8")
        m = re.search(r"^- Id:\s*([a-z0-9]{6})", plan_content, re.MULTILINE)
        self.assertIsNotNone(m, "scaffolded plan must have '- Id: <id6>'")
        id6 = m.group(1)

        # 9. ipd dependencies set <id6> none
        self._run_aw(
            "ipd",
            "dependencies",
            "set",
            id6,
            "none",
            expected_exit=0,
            step="ipd dependencies set",
        )
        self._assert_zero_delta("ipd dependencies set")

        # 10. work begin <id6>
        self._run_aw("work", "begin", id6, expected_exit=0, step="work begin")
        self._assert_zero_delta("work begin")

        # Positive assertions (E-03):
        # - worktree path is under <AW_HOME>/projects/<id>/worktrees/
        expected_wt_dir = self.aw_home / "projects" / project_id / "worktrees" / id6
        self.assertTrue(
            expected_wt_dir.is_dir(),
            f"expected worktree dir {expected_wt_dir} to exist",
        )
        # - registered in git worktree list --porcelain
        wt_list = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertTrue(
            str(expected_wt_dir) in wt_list or expected_wt_dir.as_posix() in wt_list,
            f"git worktree list should include {expected_wt_dir}",
        )
        # - validated a plan that lives ONLY in home records
        self.assertFalse(
            (self.repo / ".aw" / "records").exists(),
            "target should not have .aw/records",
        )

        # 11. oc run start <id6> --prepare-only
        self._run_aw(
            "oc",
            "run",
            "start",
            id6,
            "--prepare-only",
            expected_exit=0,
            step="oc run start --prepare-only",
        )
        self._assert_zero_delta("oc run start --prepare-only")

        # Positive assertions (E-03):
        # - exactly one new run-* dir under runner_shared.state_root(<t>)
        st_root = runner_shared.state_root(self.repo)
        expected_runs_dir = self.aw_home / "projects" / project_id / "records" / "runs"
        self.assertEqual(
            st_root.resolve(),
            expected_runs_dir.resolve(),
            f"state_root {st_root} should equal {expected_runs_dir}",
        )
        runs = list(st_root.glob("run-*"))
        self.assertEqual(
            len(runs),
            1,
            f"expected exactly one run directory under {st_root}, found {runs}",
        )
        # - none under <t>
        self.assertFalse(
            (self.repo / ".aw" / "records" / "runs").exists(),
            "runs directory leaked into target",
        )
        self.assertFalse(
            (self.repo / ".aw" / "state").exists(),
            "state directory leaked into target",
        )

        # 12. uninstall . --yes
        self._run_aw(
            "uninstall",
            ".",
            "--yes",
            expected_exit=0,
            step="uninstall . --yes",
        )
        self._assert_zero_delta("uninstall")

        # Positive assertions (E-03):
        # - home records still holds the backlog item
        remaining_backlog = list(
            (records_root / "backlog" / "open").glob("*.backlog.md")
        )
        self.assertTrue(
            len(remaining_backlog) >= 1,
            "home records must retain backlog item after non-deep uninstall",
        )
        # - git worktree list shows only the main worktree
        wt_list_after = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertNotIn(
            str(expected_wt_dir),
            wt_list_after,
            "lane worktree must be unregistered after uninstall",
        )
        self.assertNotIn(
            expected_wt_dir.as_posix(),
            wt_list_after,
            "lane worktree must be unregistered after uninstall",
        )
        worktree_lines = [
            line for line in wt_list_after.splitlines() if line.startswith("worktree ")
        ]
        self.assertEqual(
            len(worktree_lines),
            1,
            f"expected only the main worktree remaining, found {worktree_lines}",
        )

    def test_completely_clean_target_ordinary_use(self) -> None:
        """Prove completely-clean-target preset maintains zero target delta through ordinary use."""
        self._run_preset_ordinary_use_sequence("completely-clean-target")

    def test_local_only_ordinary_use(self) -> None:
        """Prove local-only preset maintains zero target delta through ordinary use."""
        self._run_preset_ordinary_use_sequence("local-only")


if __name__ == "__main__":
    unittest.main()

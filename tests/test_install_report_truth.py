"""Regression tests for install report truth and tracked policy staging (IPD gzsfqn).

Validates:
(a) Tracked wizard writes (.aw/config/project.json) are staged and committed by -y;
    machine-local binding (.aw/config/local.json) remains untracked and ignored.
(b) Run-scratch gitignore advisory matches git check-ignore on fresh install.
(c) Fresh -y install prints "Changes committed: <short sha>" and no "STAGED but NOT committed".
(d) Second -y install (no-change upgrade) leaves status clean with neither staged nor false committed lines.
(e) Decline path in prompt_and_run_commit prints staged-not-committed line and manual command.
"""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import pytest

from agent_workflows import engine
from tests.support import REPO_ROOT

pytestmark = pytest.mark.slow


def _make_temp_target_repo(tmpdir: str) -> tuple[pathlib.Path, dict[str, str]]:
    """Initialize a git repo with a package.json and deterministic identity."""
    repo = pathlib.Path(tmpdir) / "repo"
    repo.mkdir()
    home = pathlib.Path(tmpdir) / "home"
    home.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["AW_NO_REEXEC"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["GIT_AUTHOR_NAME"] = "Test Author"
    env["GIT_AUTHOR_EMAIL"] = "author@example.com"
    env["GIT_COMMITTER_NAME"] = "Test Committer"
    env["GIT_COMMITTER_EMAIL"] = "committer@example.com"

    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Committer"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "committer@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    (repo / "package.json").write_text('{"name": "test-pkg"}\n', encoding="utf-8")
    subprocess.run(["git", "add", "package.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    return repo, env


class TestInstallReportTruth(unittest.TestCase):
    """Test post-install report truthfulness and tracked policy staging."""

    def test_fresh_install_staging_advisories_and_closing_report(self) -> None:
        """Covers requirements (a), (b), (c) on a fresh -y install."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo, env = _make_temp_target_repo(tmpdir)

            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    ".",
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                res.returncode, 0, f"install failed:\n{res.stderr}\n{res.stdout}"
            )

            # (a) git status --porcelain is empty; project.json is tracked; local.json is untracked
            status_proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(
                status_proc.stdout.strip(),
                "",
                f"expected clean porcelain status, got:\n{status_proc.stdout}",
            )

            ls_proc = subprocess.run(
                ["git", "ls-files", ".aw/config"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            ls_files = ls_proc.stdout.splitlines()
            self.assertIn(".aw/config/project.json", ls_files)
            self.assertNotIn(".aw/config/local.json", ls_files)

            # (b) captured run-scratch line says "is ignored" and agrees with git check-ignore
            scratch_lines = [
                line
                for line in res.stdout.splitlines()
                if "Gitignore (run scratch):" in line
            ]
            self.assertTrue(
                scratch_lines, "missing 'Gitignore (run scratch):' line in output"
            )
            self.assertIn("is ignored", scratch_lines[0])

            ci_proc = subprocess.run(
                ["git", "check-ignore", "-q", ".aw/workflow-artifacts/README.md"],
                cwd=repo,
            )
            self.assertEqual(ci_proc.returncode, 0)

            # (c) output contains "Changes committed: <short sha>" and no "STAGED but NOT committed"
            head_sha = subprocess.run(
                ["git", "log", "-1", "--format=%h"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertIn(f"Changes committed: {head_sha}", res.stdout)
            self.assertNotIn("STAGED but NOT committed", res.stdout)

    def test_second_install_nochange_leaves_clean_status_and_no_false_lines(
        self,
    ) -> None:
        """Covers requirement (d): second install leaves porcelain empty with no staged or committed claims."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo, env = _make_temp_target_repo(tmpdir)

            res1 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    ".",
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res1.returncode, 0)

            # Run second install (no-change upgrade)
            res2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    ".",
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res2.returncode, 0)

            status_proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(
                status_proc.stdout.strip(),
                "",
                f"expected clean porcelain status, got:\n{status_proc.stdout}",
            )

            self.assertNotIn("STAGED but NOT committed", res2.stdout)
            self.assertNotIn("Changes committed:", res2.stdout)

    def test_decline_path_in_prompt_and_run_commit(self) -> None:
        """Covers requirement (e): prompt_and_run_commit non-interactive decline path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = pathlib.Path(tmpdir)
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test Committer"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "committer@example.com"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
            )

            sample_file = repo / "sample.txt"
            sample_file.write_text("sample content\n", encoding="utf-8")
            subprocess.run(["git", "add", "sample.txt"], cwd=repo, check=True)

            plan = engine.InstallPlan(
                source_root=REPO_ROOT,
                repo_root=repo,
                dry_run=False,
                backup=False,
                prune=False,
                yes=False,
            )

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                with mock.patch(
                    "agent_workflows.term.is_interactive", return_value=False
                ):
                    engine.prompt_and_run_commit(
                        plan=plan,
                        installed=["sample.txt [install]"],
                        pruned=[],
                        agents_status={},
                        backups_ignore_status="",
                        use_git=True,
                    )

            output = buf.getvalue()
            self.assertIn("Changes are STAGED but NOT committed.", output)
            self.assertIn('git commit -m "sync agent-workflows" -- sample.txt', output)
            self.assertNotIn("Changes committed:", output)

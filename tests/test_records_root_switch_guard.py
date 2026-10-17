"""Records-root switch refusal on reinstall (IPD s07f73 / Set rbswitch, backlog wbz75c).

An install that changes only the records backend keeps the config directory but moves the
records root the resolver reads. When the current root holds records, every install entry
point must refuse before writing anything, so no record is left where no reader looks.
"""

from __future__ import annotations

import glob
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch

import pytest

from agent_workflows import cli
from agent_workflows.install_wizard import (
    ProjectPolicy,
    RecordsRootSwitchRequired,
    get_preset_defaults,
    persist_project_policy,
    records_root_switch,
)
from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import Preset

REPO_ROOT = str(Path(__file__).resolve().parent.parent)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test User",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test User",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def _scratch_env(tpath: Path) -> Dict[str, str]:
    aw_home = tpath / "aw_home"
    xdg = tpath / "xdg"
    home = tpath / "home"
    for p in (aw_home, xdg, home):
        p.mkdir(exist_ok=True)
    return {
        "HOME": str(home),
        "AW_HOME": str(aw_home),
        "XDG_CONFIG_HOME": str(xdg),
        "AW_NO_REEXEC": "1",
        **GIT_ENV,
    }


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        env=dict(os.environ, **GIT_ENV),
        timeout=60,
    )


def _new_repo(tpath: Path, name: str = "repo") -> Path:
    repo = tpath / name
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    return repo


def _install_inproc(repo: Path, *extra: str) -> int:
    with patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()):
        return cli.main(
            ["--no-color", "install", str(repo), *extra, "-y", "--no-interactive"]
        )


def _commit_record(repo: Path) -> Path:
    rec = repo / ".aw" / "records" / "backlog" / "mine.md"
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text("# mine\n", encoding="utf-8")
    _git(repo, "add", str(rec.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "record")
    return rec


def _policy(
    preset: str,
    aw_home: str,
    records_backend: Optional[str] = None,
    companion_dir: Optional[str] = None,
) -> ProjectPolicy:
    _pls, _gps, dm, rb, ds = get_preset_defaults(preset)
    return ProjectPolicy(
        preset=preset,
        delivery_mode=dm,
        records_backend=records_backend or rb,
        durability_state=ds,
        aw_home=aw_home,
        companion_dir=companion_dir,
        non_secret_consent={"telemetry": True},
    )


def _records_root(repo: Path) -> Path:
    return Path(resolve_project_context(target_repo=str(repo)).logical_roots["records"])


class TestRecordsRootSwitchDetector(unittest.TestCase):
    def test_detector_cases(self) -> None:
        """(1) None for every non-orphaning case; hits for records and companion."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            with patch.dict(os.environ, env):
                aw_home = env["AW_HOME"]
                priv = Preset.PRIVATE_TARGET.value
                same = _policy(priv, aw_home)
                home = _policy(priv, aw_home, records_backend="home")

                fresh = _new_repo(tpath, "fresh")
                self.assertIsNone(records_root_switch(fresh, home))

                repo = _new_repo(tpath)
                self.assertEqual(_install_inproc(repo, "--preset", priv), 0)
                self.assertIsNone(records_root_switch(repo, same))
                self.assertIsNone(
                    records_root_switch(repo, _policy(Preset.LOCAL_ONLY.value, aw_home))
                )
                self.assertIsNone(
                    records_root_switch(
                        repo,
                        _policy(priv, aw_home, records_backend="repository-untracked"),
                    )
                )
                # Scaffold only: nothing to orphan.
                self.assertIsNone(records_root_switch(repo, home))
                comp = _policy(
                    priv,
                    aw_home,
                    records_backend="companion",
                    companion_dir=str(tpath / "companion"),
                )
                self.assertIsNone(records_root_switch(repo, comp))

                _commit_record(repo)
                hit = records_root_switch(repo, home)
                self.assertIsNotNone(hit)
                assert hit is not None
                self.assertEqual(hit.reason, "records")
                self.assertEqual(hit.record_files, 1)
                self.assertEqual(
                    hit.current_root.resolve(), (repo / ".aw" / "records").resolve()
                )
                self.assertNotEqual(
                    hit.current_root.resolve(), hit.target_root.resolve()
                )

                chit = records_root_switch(repo, comp)
                self.assertIsNotNone(chit)
                assert chit is not None
                self.assertEqual(chit.reason, "companion")
                self.assertEqual(chit.record_files, 1)

    def test_persist_project_policy_refuses(self) -> None:
        """(2) persist_project_policy refuses before writing."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            with patch.dict(os.environ, env):
                repo = _new_repo(tpath)
                self.assertEqual(
                    _install_inproc(repo, "--preset", Preset.PRIVATE_TARGET.value), 0
                )
                _commit_record(repo)
                proj = repo / ".aw" / "config" / "project.json"
                before = proj.read_bytes()
                pol = _policy(
                    Preset.PRIVATE_TARGET.value, env["AW_HOME"], records_backend="home"
                )
                with self.assertRaises(RecordsRootSwitchRequired) as cm:
                    persist_project_policy(str(repo), pol)
                self.assertEqual(cm.exception.reason, "records")
                self.assertEqual(cm.exception.record_files, 1)
                self.assertIn("would leave 1 record files", str(cm.exception))
                self.assertEqual(proj.read_bytes(), before)

    def test_interactive_wizard_refuses(self) -> None:
        """(7) Interactive path: answer n, pick private-target; the home backend refuses."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            with patch.dict(os.environ, env):
                repo = _new_repo(tpath)
                self.assertEqual(
                    _install_inproc(repo, "--preset", Preset.PRIVATE_TARGET.value), 0
                )
                _commit_record(repo)
                proj = repo / ".aw" / "config" / "project.json"
                before = proj.read_bytes()
                out = io.StringIO()
                with patch(
                    "sys.stdin", io.StringIO("n\n1\nprivate\n" + "\n" * 10)
                ), patch("sys.stdout", out), patch("sys.stderr", out):
                    rc = cli.main(
                        [
                            "--no-color",
                            "install",
                            str(repo),
                            "--records-backend",
                            "home",
                        ]
                    )
                self.assertEqual(rc, 1, out.getvalue()[-2000:])
                self.assertIn("would leave 1 record files", out.getvalue())
                self.assertEqual(proj.read_bytes(), before)
                self.assertEqual(json.loads(before)["records_backend"], "repository")


@pytest.mark.slow
class TestRecordsRootSwitchSubprocess(unittest.TestCase):
    def _run(self, env: Dict[str, str], *args: str) -> subprocess.CompletedProcess:
        full = dict(os.environ, **env)
        full["PYTHONPATH"] = (
            f"{REPO_ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"
        )
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", "--no-color", "install", *args],
            env=full,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

    def _setup_with_record(self, tpath: Path, env: Dict[str, str]) -> Path:
        repo = _new_repo(tpath)
        r = self._run(
            env, str(repo), "--preset", "private-target", "-y", "--no-interactive"
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        _commit_record(repo)
        return repo

    def _assert_refused(self, repo: Path, env: Dict[str, str], *extra: str) -> None:
        proj = repo / ".aw" / "config" / "project.json"
        before = proj.read_bytes()
        r = self._run(
            env,
            str(repo),
            "--records-backend",
            "home",
            *extra,
            "-y",
            "--no-interactive",
        )
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        self.assertIn("would leave 1 record files", out)
        self.assertIn(str(repo / ".aw" / "records"), out)
        self.assertIn(str(Path(env["AW_HOME"]) / "projects"), out)
        self.assertEqual(proj.read_bytes(), before)
        self.assertTrue((repo / ".aw" / "records" / "backlog" / "mine.md").is_file())
        self.assertEqual(
            glob.glob(
                os.path.join(
                    env["AW_HOME"], "projects", "*", "records", "backlog", "mine.md"
                )
            ),
            [],
        )

    def test_reinstall_home_backend_refuses(self) -> None:
        """(3) install --records-backend home exits 1 and writes nothing."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            repo = self._setup_with_record(tpath, env)
            self._assert_refused(repo, env)

    def test_reinstall_home_backend_dry_run_refuses(self) -> None:
        """(4) the same with --dry-run exits 1."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            repo = self._setup_with_record(tpath, env)
            self._assert_refused(repo, env, "--dry-run")

    def test_reverse_direction_refuses(self) -> None:
        """(5) home -> repository with a home record exits 1."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            repo = _new_repo(tpath)
            r = self._run(
                env,
                str(repo),
                "--preset",
                "private-target",
                "--records-backend",
                "home",
                "-y",
                "--no-interactive",
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with patch.dict(os.environ, env):
                home_root = _records_root(repo)
            self.assertTrue(str(home_root).startswith(env["AW_HOME"]))
            (home_root / "backlog").mkdir(parents=True, exist_ok=True)
            (home_root / "backlog" / "mine.md").write_text("# mine\n", encoding="utf-8")
            proj = repo / ".aw" / "config" / "project.json"
            before = proj.read_bytes()
            r = self._run(
                env,
                str(repo),
                "--records-backend",
                "repository",
                "-y",
                "--no-interactive",
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("would leave 1 record files", r.stdout + r.stderr)
            self.assertEqual(proj.read_bytes(), before)

    def test_repair_of_orphaned_repo_is_allowed(self) -> None:
        """(6) With only scaffold in the current root, switching back restores visibility."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            env = _scratch_env(tpath)
            repo = _new_repo(tpath)
            r = self._run(
                env, str(repo), "--preset", "private-target", "-y", "--no-interactive"
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            r = self._run(
                env, str(repo), "--records-backend", "home", "-y", "--no-interactive"
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            # Simulate the record the backlog bug left behind in the old root.
            rec = repo / ".aw" / "records" / "backlog" / "mine.md"
            rec.parent.mkdir(parents=True, exist_ok=True)
            rec.write_text("# mine\n", encoding="utf-8")
            r = self._run(
                env,
                str(repo),
                "--records-backend",
                "repository",
                "-y",
                "--no-interactive",
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with patch.dict(os.environ, env):
                root = _records_root(repo)
            self.assertEqual(root.resolve(), (repo / ".aw" / "records").resolve())
            self.assertTrue((root / "backlog" / "mine.md").is_file())


if __name__ == "__main__":
    unittest.main()

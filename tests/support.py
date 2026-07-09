"""Shared helpers for the framework self-tests (stdlib only)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

# Repo root = the directory containing install-workflows.py (two up from this file's dir).
REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / "install-workflows.py"
SCANNER = REPO_ROOT / ".agents" / "workflows" / "assess" / "tools" / "scan_secrets.py"
RUN_CHECKS = REPO_ROOT / ".agents" / "workflows" / "verify" / "tools" / "run_checks.py"
BENCH_ENV = REPO_ROOT / ".agents" / "workflows" / "benchmark" / "tools" / "bench_env.py"
SETUP_TOOLS = REPO_ROOT / ".agents" / "workflows" / "setup-repo" / "tools" / "setup_tools.py"


def load_module(name: str, path: Path):
    """Import a Python file as a named module, registered in sys.modules.

    Registration is required so that decorators like @dataclass in the imported module
    can resolve `cls.__module__` (Python 3.12+/3.14 look the module up in sys.modules).
    """

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in cwd, returning the completed process."""

    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


def init_repo(path: Path) -> Path:
    """Initialize a minimal git repo at path with a deterministic identity."""

    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    git(path, "config", "commit.gpgsign", "false")
    return path


def run_installer(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    """Run the installer against a target repo, from the repo's own source tree."""

    return subprocess.run(
        [sys.executable, str(INSTALLER), "--repo", str(repo), *extra],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def run_tool(tool: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run one of the framework's Python tools with args."""

    return subprocess.run(
        [sys.executable, str(tool), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )

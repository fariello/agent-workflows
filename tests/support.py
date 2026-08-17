"""Shared helpers for the framework self-tests (stdlib only)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

# Repo root = the directory containing install-workflows.py (two up from this file's dir).
REPO_ROOT = Path(__file__).resolve().parent.parent
# Static, checked-in test fixtures (decoupled from the mutable live plans board).
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONFORMING_ORCHESTRATOR = FIXTURES / "conforming-orchestrator.md"
INSTALLER = REPO_ROOT / "install-workflows.py"


def _source_workflows_root() -> Path:
    """The framework's OWN source workflow bundle, layout-aware.

    Canonical nested `.aw/system/workflows/` after the physical-layout migration; falls back
    to the legacy `.agents/workflows/` for a pre-migration checkout. Keeping this dual-aware
    lets the self-tests run before AND after the source repo is migrated.
    """

    aw = REPO_ROOT / ".aw" / "system" / "workflows"
    return aw if aw.is_dir() else REPO_ROOT / ".agents" / "workflows"


SOURCE_WORKFLOWS = _source_workflows_root()


def _source_plans_root() -> Path:
    """The framework's OWN source plans tree, layout-aware: `.aw/records/plans/` after the
    migration, else legacy `.agents/plans/`."""

    aw = REPO_ROOT / ".aw" / "records" / "plans"
    return aw if aw.is_dir() else REPO_ROOT / ".agents" / "plans"


SOURCE_PLANS = _source_plans_root()


def _source_docs_root() -> Path:
    """The framework's OWN source docs tree, layout-aware: `.aw/records/docs/` after the
    migration, else legacy `.agents/docs/`."""

    aw = REPO_ROOT / ".aw" / "records" / "docs"
    return aw if aw.is_dir() else REPO_ROOT / ".agents" / "docs"


SOURCE_DOCS = _source_docs_root()
SCANNER = SOURCE_WORKFLOWS / "assess" / "tools" / "scan_secrets.py"
RUN_CHECKS = SOURCE_WORKFLOWS / "verify" / "tools" / "run_checks.py"
BENCH_ENV = SOURCE_WORKFLOWS / "benchmark" / "tools" / "bench_env.py"
SETUP_TOOLS = SOURCE_WORKFLOWS / "setup-repo" / "tools" / "setup_tools.py"
CONFORMANCE_HARNESS = (
    SOURCE_WORKFLOWS / "conformance" / "tools" / "conformance_harness.py"
)


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


def run_tool(
    tool: Path, *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Run one of the framework's Python tools with args."""

    return subprocess.run(
        [sys.executable, str(tool), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )

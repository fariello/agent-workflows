"""Tests for atomic_write and record creation mode under umask (IPD ic4eg0).

POSIX only. Ensures tracked records written or replaced have standard umask-derived
permissions (e.g. 644 under umask 022, 664 under umask 002) and preserve custom
modes (e.g. 640), while private files (config, state) retain owner-only 600 permissions.
"""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX file permissions (umask/chmod) are not applicable on Windows",
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_aw(
    repo_root: Path,
    home_dir: Path,
    args: list[str],
    *,
    umask: str = "022",
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run `python3 -m agent_workflows <args>` in a subprocess with isolated umask and HOME."""
    full_env = dict(os.environ)
    full_env["HOME"] = str(home_dir)
    full_env["XDG_CONFIG_HOME"] = str(home_dir / ".config")
    full_env["AW_NO_REEXEC"] = "1"
    existing_pythonpath = full_env.get("PYTHONPATH", "")
    full_env["PYTHONPATH"] = (
        f"{REPO_ROOT}:{existing_pythonpath}" if existing_pythonpath else str(REPO_ROOT)
    )

    if env:
        full_env.update(env)

    cli_cmd = f"{shlex.quote(sys.executable)} -m agent_workflows {' '.join(shlex.quote(a) for a in args)}"
    full_cmd = f"umask {umask} && exec {cli_cmd}"

    return subprocess.run(
        ["sh", "-c", full_cmd],
        cwd=str(repo_root),
        env=full_env,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo_and_home(tmp_path: Path) -> tuple[Path, Path]:
    """Create a temporary initialized git repository with agent-workflows installed."""
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    (home / ".config").mkdir()

    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
    )

    res = run_aw(repo, home, ["install", ".", "-y", "--preset", "private-target"])
    assert (
        res.returncode == 0
    ), f"install failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"

    return repo, home


def test_research_new_mode(repo_and_home: tuple[Path, Path]) -> None:
    """(a) `aw research new --apply` creates a 644 file under umask 022."""
    repo, home = repo_and_home
    res = run_aw(
        repo,
        home,
        [
            "research",
            "new",
            "--kind",
            "research-report",
            "--slug",
            "mode-test",
            "--apply",
        ],
    )
    assert res.returncode == 0, f"research new failed: {res.stderr}\n{res.stdout}"

    matches = list(repo.glob(".aw/records/research/*mode-test*.md"))
    assert len(matches) == 1, f"Expected 1 research file, found: {matches}"
    file_mode = stat.S_IMODE(matches[0].stat().st_mode)
    assert file_mode == 0o644, f"Expected 0o644, got {oct(file_mode)}"


def test_adopt_mode(repo_and_home: tuple[Path, Path]) -> None:
    """(b) `aw adopt --apply` creates a 644 file under umask 022."""
    repo, home = repo_and_home
    inbox_dir = repo / ".aw" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    inbox_file = inbox_dir / "external.md"
    inbox_file.write_text("External research drop\n", encoding="utf-8")

    res = run_aw(
        repo,
        home,
        [
            "adopt",
            ".aw/inbox/external.md",
            "--kind",
            "findings",
            "--slug",
            "ext-test",
            "--apply",
        ],
    )
    assert res.returncode == 0, f"adopt failed: {res.stderr}\n{res.stdout}"

    matches = list(repo.glob(".aw/records/research/*ext-test*.md"))
    assert len(matches) == 1, f"Expected 1 adopted research file, found: {matches}"
    file_mode = stat.S_IMODE(matches[0].stat().st_mode)
    assert file_mode == 0o644, f"Expected 0o644, got {oct(file_mode)}"


def test_ipd_scaffold_and_terminal_set_mode(repo_and_home: tuple[Path, Path]) -> None:
    """(c) `aw ipd scaffold --apply` creates a 644 plan and `aw ipd set` to terminal status moves it with 644."""
    repo, home = repo_and_home
    res = run_aw(
        repo,
        home,
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Scaffold mode test",
            "--set",
            "modetest",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
        ],
        env={"AW_IPD_AUTHOR": "probe"},
    )
    assert res.returncode == 0, f"ipd scaffold failed: {res.stderr}\n{res.stdout}"

    pending_matches = list(repo.glob(".aw/records/plans/pending/*modetest*.ipd.md"))
    assert len(pending_matches) == 1, f"Expected 1 plan, found: {pending_matches}"
    scaffold_mode = stat.S_IMODE(pending_matches[0].stat().st_mode)
    assert scaffold_mode == 0o644, f"Expected 0o644, got {oct(scaffold_mode)}"

    plan_id = pending_matches[0].name.split("-")[3]

    res_set = run_aw(
        repo,
        home,
        [
            "ipd",
            "set",
            "not-executed",
            plan_id,
            "--no-commit",
            "-m",
            "terminal move test",
        ],
    )
    assert (
        res_set.returncode == 0
    ), f"ipd set failed: {res_set.stderr}\n{res_set.stdout}"

    terminal_matches = list(
        repo.glob(".aw/records/plans/not-executed/*modetest*.ipd.md")
    )
    assert (
        len(terminal_matches) == 1
    ), f"Expected 1 moved plan, found: {terminal_matches}"
    moved_mode = stat.S_IMODE(terminal_matches[0].stat().st_mode)
    assert moved_mode == 0o644, f"Expected 0o644 after move, got {oct(moved_mode)}"


def test_plan_preserve_mode_on_rewrite(repo_and_home: tuple[Path, Path]) -> None:
    """(d) A plan chmodded to 640 and then rewritten by `aw ipd set` stays 640."""
    repo, home = repo_and_home
    res = run_aw(
        repo,
        home,
        [
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Preserve mode test",
            "--set",
            "presrv",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
        ],
        env={"AW_IPD_AUTHOR": "probe"},
    )
    assert res.returncode == 0, f"ipd scaffold failed: {res.stderr}\n{res.stdout}"

    pending_matches = list(repo.glob(".aw/records/plans/pending/*presrv*.ipd.md"))
    assert len(pending_matches) == 1
    plan_path = pending_matches[0]
    os.chmod(plan_path, 0o640)
    assert stat.S_IMODE(plan_path.stat().st_mode) == 0o640

    plan_id = plan_path.name.split("-")[3]
    res_set = run_aw(
        repo,
        home,
        ["ipd", "set", "to-review", plan_id, "--no-commit", "-m", "rewrite plan"],
    )
    assert (
        res_set.returncode == 0
    ), f"ipd set failed: {res_set.stderr}\n{res_set.stdout}"

    rewritten_matches = list(repo.glob(".aw/records/plans/pending/*presrv*.ipd.md"))
    assert len(rewritten_matches) == 1
    preserved_mode = stat.S_IMODE(rewritten_matches[0].stat().st_mode)
    assert (
        preserved_mode == 0o640
    ), f"Expected preserved 0o640, got {oct(preserved_mode)}"


def test_umask_002_mode(repo_and_home: tuple[Path, Path]) -> None:
    """(e) Under `umask 002` a new record is 664."""
    repo, home = repo_and_home
    res = run_aw(
        repo,
        home,
        [
            "research",
            "new",
            "--kind",
            "research-report",
            "--slug",
            "umask002",
            "--apply",
        ],
        umask="002",
    )
    assert res.returncode == 0, f"research new failed: {res.stderr}\n{res.stdout}"

    matches = list(repo.glob(".aw/records/research/*umask002*.md"))
    assert len(matches) == 1
    file_mode = stat.S_IMODE(matches[0].stat().st_mode)
    assert file_mode == 0o664, f"Expected 0o664 under umask 002, got {oct(file_mode)}"


def test_install_leaves_managed_sections_644(repo_and_home: tuple[Path, Path]) -> None:
    """(f) `aw install` leaves `.aw/system/managed-sections.json` 644."""
    repo, _home = repo_and_home
    managed_sections = repo / ".aw" / "system" / "managed-sections.json"
    assert managed_sections.exists(), "managed-sections.json does not exist"
    file_mode = stat.S_IMODE(managed_sections.stat().st_mode)
    assert (
        file_mode == 0o644
    ), f"Expected 0o644 for managed-sections.json, got {oct(file_mode)}"


def test_private_config_mode_remains_600(tmp_path: Path) -> None:
    """(g) A PRIVATE writer is still 600: `aw config set defaults.prune false` writes config.json 600."""
    home = tmp_path / "home"
    cfg_dir = home / ".config"
    cfg_dir.mkdir(parents=True)

    dummy_repo = tmp_path / "dummy_repo"
    dummy_repo.mkdir()

    res = run_aw(
        dummy_repo,
        home,
        ["config", "set", "defaults.prune", "false"],
        umask="022",
    )
    assert res.returncode == 0, f"config set failed: {res.stderr}\n{res.stdout}"

    cfg_file = cfg_dir / "agent-workflows" / "config.json"
    assert cfg_file.exists(), "config.json does not exist"
    file_mode = stat.S_IMODE(cfg_file.stat().st_mode)
    assert (
        file_mode == 0o600
    ), f"Expected private config to be 0o600, got {oct(file_mode)}"

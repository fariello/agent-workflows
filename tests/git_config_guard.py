"""Pytest plugin guarding repository git config against test identity leaks.

Snapshots identity-bearing keys (`user.*`, `author.*`, `committer.*`) of the real
checkout's git config files at session start, re-checks them after each test, fails
any test that modifies them, and restores the snapshot.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from tests.support import clean_git_env

_guarded_files: list[Path] = []
_snapshots: dict[Path, dict[str, str]] = {}
_last_stats: dict[Path, tuple[int, int] | None] = {}
_enabled: bool = False


def _read_identity_keys(file_path: Path) -> dict[str, str]:
    if not file_path.exists():
        return {}
    proc = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(file_path),
            "--get-regexp",
            r"^(user|author|committer)\.",
        ],
        capture_output=True,
        text=True,
        env=clean_git_env(),
        check=False,
    )
    if proc.returncode != 0:
        return {}
    keys: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if " " in line:
            k, v = line.split(" ", 1)
            keys[k] = v
    return keys


def pytest_configure(config: pytest.Config) -> None:
    global _enabled
    _guarded_files.clear()
    _snapshots.clear()
    _last_stats.clear()

    repo_env = os.environ.get("AW_TEST_GIT_CONFIG_GUARD_REPO")
    repo = Path(repo_env) if repo_env else Path(config.rootpath)

    # Check if target is a git repository
    proc_common = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        env=clean_git_env(),
        check=False,
    )
    if proc_common.returncode != 0:
        _enabled = False
        return

    common_raw = proc_common.stdout.strip()
    if not common_raw:
        _enabled = False
        return

    common_dir = Path(common_raw)
    if not common_dir.is_absolute():
        common_dir = (repo / common_dir).resolve()
    else:
        common_dir = common_dir.resolve()

    shared_config = (common_dir / "config").resolve()
    _guarded_files.append(shared_config)

    proc_wt = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-path", "config.worktree"],
        capture_output=True,
        text=True,
        env=clean_git_env(),
        check=False,
    )
    if proc_wt.returncode == 0:
        wt_raw = proc_wt.stdout.strip()
        if wt_raw:
            wt_path = Path(wt_raw)
            if not wt_path.is_absolute():
                wt_path = (repo / wt_path).resolve()
            else:
                wt_path = wt_path.resolve()
            if wt_path.exists():
                _guarded_files.append(wt_path)

    for f in _guarded_files:
        _snapshots[f] = _read_identity_keys(f)
        _last_stats[f] = (
            (f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None
        )

    _enabled = True


def _check_and_restore(nodeid: str) -> None:
    if not _enabled:
        return

    for f in _guarded_files:
        current_stat = (f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None
        if current_stat == _last_stats.get(f):
            continue

        current_keys = _read_identity_keys(f)
        old_keys = _snapshots.get(f, {})
        if current_keys != old_keys:
            all_keys = set(old_keys.keys()) | set(current_keys.keys())
            diffs: list[str] = []
            for k in sorted(all_keys):
                old_v = old_keys.get(k)
                new_v = current_keys.get(k)
                if old_v != new_v:
                    if old_v is None:
                        diffs.append(f"{k}: <absent> -> '{new_v}'")
                        subprocess.run(
                            ["git", "config", "--file", str(f), "--unset-all", k],
                            env=clean_git_env(),
                            check=False,
                        )
                    elif new_v is None:
                        diffs.append(f"{k}: '{old_v}' -> <absent>")
                        subprocess.run(
                            ["git", "config", "--file", str(f), k, old_v],
                            env=clean_git_env(),
                            check=False,
                        )
                    else:
                        diffs.append(f"{k}: '{old_v}' -> '{new_v}'")
                        subprocess.run(
                            [
                                "git",
                                "config",
                                "--file",
                                str(f),
                                "--replace-all",
                                k,
                                old_v,
                            ],
                            env=clean_git_env(),
                            check=False,
                        )
            _last_stats[f] = (
                (f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None
            )
            diff_str = "; ".join(diffs)
            msg = (
                f"GIT CONFIG GUARD: {nodeid} left {f} changed: {diff_str}; restored. "
                f"Under xdist the writer may be a concurrent test in another worker; rerun with -o addopts=\"\" -m '' to attribute it."
            )
            pytest.fail(msg, pytrace=False)
        else:
            _last_stats[f] = current_stat


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: Any) -> Any:
    try:
        res = yield
    finally:
        pass
    _check_and_restore(item.nodeid)
    return res


@pytest.fixture(autouse=True)
def _guard_git_config_fixture(request: pytest.FixtureRequest) -> Any:
    yield
    _check_and_restore(request.node.nodeid)

"""Loaded code detection and fingerprinting for the runner (runfresh Order 02, `34zv7d`).

Implements spec 25kzda 5.3b points 1 and 6 and 5.3 A.2.
Detects when on-disk toolkit code has changed since the current process imported it,
and records the toolkit version each run starts on.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any, NamedTuple


class CodeChange(NamedTuple):
    """Result of comparing current toolkit code against what this process loaded."""

    changed: bool
    old: str
    new: str
    restartable: bool
    changed_files: list[str]


# Module-level memo storing what this process loaded, keyed by canonical package_root path.
_LOADED_CODE_MEMO: dict[str, dict[str, Any]] = {}


def _resolve_root(root: Path | str) -> tuple[Path, Path]:
    """Resolve the package root and the agent_workflows package directory.

    Returns (package_root, agent_workflows_dir).
    """
    root_path = Path(root).resolve()
    pkg_dir = root_path / "agent_workflows"
    if not pkg_dir.is_dir() and root_path.name == "agent_workflows":
        root_path = root_path.parent
        pkg_dir = root_path / "agent_workflows"
    return root_path, pkg_dir


def file_digests(root: Path | str) -> dict[str, str]:
    """Return a mapping of sorted relative POSIX paths to sha256 digests for agent_workflows/**/*.py."""
    root_path, pkg_dir = _resolve_root(root)
    digests: dict[str, str] = {}
    if not pkg_dir.is_dir():
        return digests

    for p in pkg_dir.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root_path).as_posix()
            digests[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            pass
    return digests


def fingerprint_from_digests(digests: dict[str, str]) -> str:
    """Compute sha256 fingerprint over sorted <relpath>\\0<file digest>\\n lines."""
    hasher = hashlib.sha256()
    for relpath in sorted(digests):
        line = f"{relpath}\0{digests[relpath]}\n"
        hasher.update(line.encode("utf-8"))
    return hasher.hexdigest()


def fingerprint(root: Path | str) -> str:
    """Compute sha256 fingerprint over all agent_workflows/**/*.py files under root."""
    digests = file_digests(root)
    return fingerprint_from_digests(digests)


def loaded_code_record(
    repo: Path | str | None,
    *,
    package_root: Path | str | None = None,
) -> dict[str, Any]:
    """Record the toolkit code loaded by the current process.

    The first call for a given package_root in this process memoizes the package_root,
    fingerprint, file digests, and recorded_at timestamp. Subsequent calls reuse the
    memoized code state, while recomputing is_target_checkout for the given repo.
    """
    if package_root is None:
        from agent_workflows import runner_shared

        resolved_root = Path(runner_shared.runner_package_root()).resolve()
    else:
        resolved_root, _ = _resolve_root(package_root)

    memo_key = str(resolved_root)
    if memo_key not in _LOADED_CODE_MEMO:
        digests = file_digests(resolved_root)
        fp = fingerprint_from_digests(digests)
        recorded_at = (
            dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        )
        _LOADED_CODE_MEMO[memo_key] = {
            "package_root": memo_key,
            "fingerprint": fp,
            "file_digests": digests,
            "recorded_at": recorded_at,
        }

    memo_entry = _LOADED_CODE_MEMO[memo_key]

    is_target = False
    if repo is not None:
        try:
            is_target = Path(repo).resolve() == resolved_root
        except Exception:
            is_target = False

    return {
        "package_root": memo_entry["package_root"],
        "fingerprint": memo_entry["fingerprint"],
        "recorded_at": memo_entry["recorded_at"],
        "is_target_checkout": is_target,
    }


def code_changed(
    repo: Path | str,
    *,
    package_root: Path | str | None = None,
) -> CodeChange:
    """Compare on-disk toolkit code against what this process loaded.

    When no record is memoized yet (e.g. in a process started by resume), establishes
    the baseline record first and returns changed=False.
    """
    if package_root is None:
        from agent_workflows import runner_shared

        resolved_root = Path(runner_shared.runner_package_root()).resolve()
    else:
        resolved_root, _ = _resolve_root(package_root)

    memo_key = str(resolved_root)
    if memo_key not in _LOADED_CODE_MEMO:
        rec = loaded_code_record(repo, package_root=resolved_root)
        return CodeChange(
            changed=False,
            old=rec["fingerprint"],
            new=rec["fingerprint"],
            restartable=rec["is_target_checkout"],
            changed_files=[],
        )

    memo_entry = _LOADED_CODE_MEMO[memo_key]
    old_fp = memo_entry["fingerprint"]
    old_digests = memo_entry["file_digests"]

    current_digests = file_digests(resolved_root)
    current_fp = fingerprint_from_digests(current_digests)

    is_target = False
    if repo is not None:
        try:
            is_target = Path(repo).resolve() == resolved_root
        except Exception:
            is_target = False

    if current_fp == old_fp:
        return CodeChange(
            changed=False,
            old=old_fp,
            new=current_fp,
            restartable=is_target,
            changed_files=[],
        )

    all_files = sorted(set(old_digests) | set(current_digests))
    changed_files = [
        f for f in all_files if old_digests.get(f) != current_digests.get(f)
    ][:50]

    return CodeChange(
        changed=True,
        old=old_fp,
        new=current_fp,
        restartable=is_target,
        changed_files=changed_files,
    )


def _reset_for_tests() -> None:
    """Clear the process-level memoized loaded-code records (test use only)."""
    _LOADED_CODE_MEMO.clear()

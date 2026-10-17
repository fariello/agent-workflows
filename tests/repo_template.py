"""Shared temp git repository template helper (IPD 83nnyn E-09).

Provides a per-process lazily built cached empty git repository template
and a copy_template_repo function that clones it via shutil.copytree.
"""

from __future__ import annotations

import atexit
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Optional

_TEMPLATE_DIR: Optional[Path] = None


def get_template_repo() -> Path:
    """Return the process-singleton template repo path, initializing lazily."""
    global _TEMPLATE_DIR
    if _TEMPLATE_DIR is not None and _TEMPLATE_DIR.is_dir():
        return _TEMPLATE_DIR

    tmp_root = Path(tempfile.mkdtemp(prefix="aw_template_repo_"))
    atexit.register(shutil.rmtree, str(tmp_root), ignore_errors=True)

    repo_dir = tmp_root / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # git init with quiet flag
    subprocess.run(
        ["git", "init", "-b", "main", "-q"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    # configure local identity
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    _TEMPLATE_DIR = repo_dir
    return _TEMPLATE_DIR


def copy_template_repo(dest: Path) -> Path:
    """Copy the cached process template repository to dest and return dest."""
    template = get_template_repo()
    dest_path = Path(dest).resolve()
    if dest_path.exists():
        shutil.copytree(template, dest_path, symlinks=True, dirs_exist_ok=True)
    else:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(template, dest_path, symlinks=True)
    return dest_path

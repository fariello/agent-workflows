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
_INSTALLED_TEMPLATES: dict[str, tuple[Path, str]] = {}


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
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
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
    return Path(dest)


def get_installed_template_repo(preset: str = "private-target") -> tuple[Path, str]:
    """Return ``(repo_dir, template_project_id)`` for a per-process cached ``aw install``.

    Runs the real installer once per preset per worker process, then tests clone it with
    ``shutil.copytree`` and rebind ``project_id`` (~30ms instead of ~1.3s per test case).
    Only intended for self-contained in-repo presets such as ``private-target``.
    """
    existing = _INSTALLED_TEMPLATES.get(preset)
    if existing is not None and existing[0].is_dir():
        return existing

    import os
    from agent_workflows.placement_switch import _canonical_path, _derive_project_id
    from tests.conformance_matrix import run_cli_inproc

    tmp_root = Path(tempfile.mkdtemp(prefix=f"aw_installed_tpl_{preset}_"))
    atexit.register(shutil.rmtree, str(tmp_root), ignore_errors=True)
    aw_home = tmp_root / "aw_home"
    aw_home.mkdir(parents=True, exist_ok=True)
    xdg_home = tmp_root / "xdg"
    xdg_home.mkdir(parents=True, exist_ok=True)
    repo_dir = tmp_root / "repo"
    copy_template_repo(repo_dir)
    (repo_dir / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "."], cwd=str(repo_dir), check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
    )
    env = dict(
        os.environ,
        AW_NO_REEXEC="1",
        HOME=str(tmp_root),
        AW_HOME=str(aw_home),
        XDG_CONFIG_HOME=str(xdg_home),
        GIT_AUTHOR_NAME="Test User",
        GIT_AUTHOR_EMAIL="test@example.com",
        GIT_COMMITTER_NAME="Test User",
        GIT_COMMITTER_EMAIL="test@example.com",
    )
    res = run_cli_inproc(
        [
            "install",
            str(repo_dir),
            "--preset",
            preset,
            "-y",
            "--no-interactive",
        ],
        env_overrides=env,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"template aw install failed (preset={preset}): {res.stdout}\n{res.stderr}"
        )
    tpl_pid = _derive_project_id(_canonical_path(repo_dir))
    _INSTALLED_TEMPLATES[preset] = (repo_dir, tpl_pid)
    return repo_dir, tpl_pid


def copy_installed_template_repo(dest: Path, *, preset: str = "private-target") -> Path:
    """Clone the cached installed template repo for ``preset`` into ``dest`` and rebind project_id."""
    from agent_workflows.placement_switch import _canonical_path, _derive_project_id

    template, tpl_pid = get_installed_template_repo(preset=preset)
    dest_path = Path(dest).resolve()
    if dest_path.exists():
        shutil.copytree(template, dest_path, symlinks=True, dirs_exist_ok=True)
    else:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(template, dest_path, symlinks=True)

    new_pid = _derive_project_id(_canonical_path(dest_path))
    if new_pid != tpl_pid:
        for rel in (
            Path(".aw/config/local.json"),
            Path(".aw/state/durable/install.json"),
            Path(".aw/state/durable/history/installs.jsonl"),
        ):
            p = dest_path / rel
            if p.is_file():
                txt = p.read_text(encoding="utf-8")
                if tpl_pid in txt:
                    p.write_text(txt.replace(tpl_pid, new_pid), encoding="utf-8")
    return Path(dest)


def directory_content_digest(root: Path) -> str:
    """Compute deterministic SHA256 digest of all files in a directory tree."""
    import hashlib

    hasher = hashlib.sha256()
    root_path = Path(root).resolve()
    for p in sorted(root_path.rglob("*")):
        if p.is_file() and not p.is_symlink():
            rel = p.relative_to(root_path).as_posix().encode("utf-8")
            hasher.update(rel)
            try:
                hasher.update(p.read_bytes())
            except OSError:
                pass
    return hasher.hexdigest()

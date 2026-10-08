"""Regression tests for the .aw/inbox/ lane and its tracked README (IPD xzlu9b).

Tests:
(a) fresh install: .aw/inbox/README.md exists and is tracked, while drops stay ignored.
(b) upgrade from old /inbox/ rule: rewrites rule, stages README, contains negation once.
(c) attention board: footer prints no waiting drops when only README is present,
    and prints 'TODO: 1 file waiting' when a drop is added.
(d) nested .aw/inbox/sub/README.md is ignored (re-include does not leak).

Behavioral only: exercises real CLI and engine functions against temporary git repositories
without code-structure inspection (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import subprocess
from contextlib import redirect_stdout
from pathlib import Path
import pytest

from agent_workflows import cli
from tests.support import REPO_ROOT, git, init_repo


def test_fresh_install_inbox_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fresh install creates .aw/inbox/README.md, tracks it, and ignores drops."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    target = init_repo(tmp_path / "target_fresh")
    code = cli.main(["install", "--source", str(REPO_ROOT), str(target), "-y"])
    assert code == 0

    readme = target / ".aw" / "inbox" / "README.md"
    assert readme.is_file()
    assert (
        readme.read_bytes() == (REPO_ROOT / ".aw" / "inbox" / "README.md").read_bytes()
    )

    # git check-ignore -q returns 1 if NOT ignored, 0 if ignored
    p_readme = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", ".aw/inbox/README.md"],
        cwd=target,
    )
    assert p_readme.returncode == 1

    drop = target / ".aw" / "inbox" / "some-drop.md"
    drop.write_text("unadopted drop text", encoding="utf-8")
    p_drop = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/inbox/some-drop.md"],
        cwd=target,
    )
    assert p_drop.returncode == 0

    p_keep = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/records/comms/shared/inbox/.gitkeep"],
        cwd=target,
    )
    assert p_keep.returncode == 1

    ls_out = subprocess.run(
        ["git", "ls-files", ".aw/inbox"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert ".aw/inbox/README.md" in ls_out


def test_upgrade_from_seeded_inbox_gitignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Upgrade from a seeded /inbox/-only .aw/.gitignore rewrites pattern and stages README."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    target = init_repo(tmp_path / "target_upgrade")
    gi = target / ".aw" / ".gitignore"
    gi.parent.mkdir(parents=True, exist_ok=True)
    gi.write_text("records/*/untracked/\n/inbox/\n", encoding="utf-8")
    git(target, "add", ".aw/.gitignore")
    git(target, "commit", "-m", "seed old gitignore")

    code = cli.main(["install", "--source", str(REPO_ROOT), str(target), "-y"])
    assert code == 0

    readme = target / ".aw" / "inbox" / "README.md"
    assert readme.is_file()

    p_readme = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", ".aw/inbox/README.md"],
        cwd=target,
    )
    assert p_readme.returncode == 1

    drop = target / ".aw" / "inbox" / "some-drop.md"
    drop.write_text("unadopted drop text", encoding="utf-8")
    p_drop = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/inbox/some-drop.md"],
        cwd=target,
    )
    assert p_drop.returncode == 0

    p_keep = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/records/comms/shared/inbox/.gitkeep"],
        cwd=target,
    )
    assert p_keep.returncode == 1

    ls_out = subprocess.run(
        ["git", "ls-files", ".aw/inbox"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert ".aw/inbox/README.md" in ls_out

    gi_text = gi.read_text(encoding="utf-8")
    assert gi_text.count("!/inbox/README.md") == 1


def test_attention_board_inbox_footer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Attention board prints no waiting drops when only README exists, and 1 when drop added."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    target = init_repo(tmp_path / "target_attention")
    cli.main(["install", "--source", str(REPO_ROOT), str(target), "-y"])

    buf = io.StringIO()
    with redirect_stdout(buf):
        cli.main(["attention", "--dir", str(target), "--no-color"])
    out1 = buf.getvalue()
    assert "waiting in `.aw/inbox/`" not in out1

    (target / ".aw" / "inbox" / "drop.md").write_text("external drop", encoding="utf-8")
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli.main(["attention", "--dir", str(target), "--no-color"])
    out2 = buf.getvalue()
    assert "TODO: 1 file waiting in `.aw/inbox/`" in out2


def test_nested_sub_readme_in_inbox_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nested .aw/inbox/sub/README.md is ignored (re-include must not leak into subdirs)."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("AW_NO_REEXEC", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    target = init_repo(tmp_path / "target_nested")
    cli.main(["install", "--source", str(REPO_ROOT), str(target), "-y"])

    nested = target / ".aw" / "inbox" / "sub" / "README.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("nested readme", encoding="utf-8")

    p_nested = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/inbox/sub/README.md"],
        cwd=target,
    )
    assert p_nested.returncode == 0

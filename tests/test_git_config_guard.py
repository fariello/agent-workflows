"""Tests for the git config identity guard and hardened test repository initialization."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from tests import support


def _clean_git_env(env: dict[str, str] | None = None) -> dict[str, str]:
    if hasattr(support, "clean_git_env"):
        return support.clean_git_env(env)
    return dict(os.environ if env is None else env)


def test_guard_catches_leak_and_restores_config(tmp_path: Path):
    """(a) End-to-end: a test writing user.email into the target repo fails and is restored."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo), check=True, env=_clean_git_env()
    )

    test_leak = repo / "test_leak.py"
    test_leak.write_text(
        "import subprocess\n"
        "def test_leak():\n"
        "    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)\n"
    )
    test_clean = repo / "test_clean.py"
    test_clean.write_text("def test_clean():\n    pass\n")

    env = _clean_git_env()
    env["PYTHONPATH"] = str(support.REPO_ROOT)
    env["AW_TEST_GIT_CONFIG_GUARD_REPO"] = str(repo)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.git_config_guard",
            "-o",
            "addopts=",
            str(repo),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )

    combined_out = proc.stdout + "\n" + proc.stderr
    assert (
        proc.returncode == 1
    ), f"Expected pytest to fail, got {proc.returncode}:\n{combined_out}"
    assert "GIT CONFIG GUARD" in combined_out
    assert "test_leak.py::test_leak" in combined_out
    assert "test_clean" in combined_out and (
        "1 passed" in combined_out
        or "PASSED" in combined_out
        or "passed" in combined_out
    )

    p_check = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(repo / ".git" / "config"),
            "--get",
            "user.email",
        ],
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    assert (
        p_check.returncode == 1
    ), f"Expected user.email to be unset, got rc {p_check.returncode}: {p_check.stdout}"


def test_guard_restores_preexisting_identity_value(tmp_path: Path):
    """(b) Pre-existing identity values modified by a test are restored to original values."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo), check=True, env=_clean_git_env()
    )
    subprocess.run(
        ["git", "config", "user.email", "original@example.com"],
        cwd=str(repo),
        check=True,
        env=_clean_git_env(),
    )

    test_mod = repo / "test_mod.py"
    test_mod.write_text(
        "import subprocess\n"
        "def test_modify():\n"
        "    subprocess.run(['git', 'config', 'user.email', 'mutated@example.com'], check=True)\n"
    )

    env = _clean_git_env()
    env["PYTHONPATH"] = str(support.REPO_ROOT)
    env["AW_TEST_GIT_CONFIG_GUARD_REPO"] = str(repo)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.git_config_guard",
            "-o",
            "addopts=",
            str(repo),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )

    combined_out = proc.stdout + "\n" + proc.stderr
    assert (
        proc.returncode == 1
    ), f"Expected pytest to fail, got {proc.returncode}:\n{combined_out}"
    assert "GIT CONFIG GUARD" in combined_out
    assert "mutated@example.com" in combined_out

    p_check = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(repo / ".git" / "config"),
            "--get",
            "user.email",
        ],
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    assert p_check.returncode == 0
    assert p_check.stdout.strip() == "original@example.com"


def test_guard_ignores_non_identity_keys(tmp_path: Path):
    """(c) Modifying non-identity keys (e.g. core.foo) does not trigger the guard."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo), check=True, env=_clean_git_env()
    )

    test_non_id = repo / "test_non_id.py"
    test_non_id.write_text(
        "import subprocess\n"
        "def test_non_identity():\n"
        "    subprocess.run(['git', 'config', 'core.foo', 'bar'], check=True)\n"
    )

    env = _clean_git_env()
    env["PYTHONPATH"] = str(support.REPO_ROOT)
    env["AW_TEST_GIT_CONFIG_GUARD_REPO"] = str(repo)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.git_config_guard",
            "-o",
            "addopts=",
            str(repo),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
    )

    combined_out = proc.stdout + "\n" + proc.stderr
    assert (
        proc.returncode == 0
    ), f"Expected pytest to pass, got {proc.returncode}:\n{combined_out}"

    p_check = subprocess.run(
        ["git", "config", "--file", str(repo / ".git" / "config"), "--get", "core.foo"],
        capture_output=True,
        text=True,
        env=_clean_git_env(),
    )
    assert p_check.returncode == 0
    assert p_check.stdout.strip() == "bar"


def test_guard_disables_itself_on_non_git_target(tmp_path: Path):
    """(d) Running against a non-git target disables the guard silently with exit code 0."""
    nongit = tmp_path / "nongit"
    nongit.mkdir()

    test_ok = nongit / "test_ok.py"
    test_ok.write_text("def test_ok():\n    pass\n")

    env = _clean_git_env()
    env["PYTHONPATH"] = str(support.REPO_ROOT)
    env["AW_TEST_GIT_CONFIG_GUARD_REPO"] = str(nongit)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "tests.git_config_guard",
            "-o",
            "addopts=",
            str(nongit),
        ],
        cwd=str(nongit),
        env=env,
        capture_output=True,
        text=True,
    )

    combined_out = proc.stdout + "\n" + proc.stderr
    assert (
        proc.returncode == 0
    ), f"Expected pytest to pass, got {proc.returncode}:\n{combined_out}"


def test_init_repo_failure_does_not_leak_to_enclosing_repo(tmp_path: Path):
    """(e) init_repo on an unwritable path raises RuntimeError without leaking to enclosing repo."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("Test requires non-root user for chmod 0o500 permissions")

    enclosing = tmp_path / "enclosing"
    enclosing.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(enclosing), check=True)

    readonly_dir = enclosing / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o500)
    try:
        with pytest.raises(RuntimeError) as exc_info:
            support.init_repo(readonly_dir)
        assert str(readonly_dir) in str(exc_info.value)
    finally:
        readonly_dir.chmod(0o700)

    p_check = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(enclosing / ".git" / "config"),
            "--get",
            "user.email",
        ],
        cwd=str(enclosing),
        capture_output=True,
        text=True,
    )
    assert (
        p_check.returncode == 1
    ), f"Enclosing repo unexpectedly received user.email: {p_check.stdout}"


def test_init_repo_with_inherited_git_dir_does_not_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """(f) Inherited GIT_DIR is scrubbed so init_repo initializes target and leaves outer repo clean."""
    outer = tmp_path / "outer"
    outer.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(outer), check=True)

    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))

    sub = outer / "sub"
    support.init_repo(sub)

    p_outer = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(outer / ".git" / "config"),
            "--get",
            "user.email",
        ],
        cwd=str(outer),
        capture_output=True,
        text=True,
    )
    assert (
        p_outer.returncode == 1
    ), f"Outer enclosing repo unexpectedly got user.email: {p_outer.stdout}"

    p_sub = subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(sub / ".git" / "config"),
            "--get",
            "user.email",
        ],
        cwd=str(sub),
        capture_output=True,
        text=True,
    )
    assert p_sub.returncode == 0
    assert p_sub.stdout.strip() == "test@example.com"

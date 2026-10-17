"""Behavioral tests verifying aw set refuses review records with exit 2 without mutating them."""

from __future__ import annotations

import io
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
from typing import Callable

import pytest

from agent_workflows import cli
from tests import support


@pytest.fixture
def repo_with_review(tmp_path: Path) -> tuple[Path, Path]:
    repo = support.init_repo(tmp_path / "repo")
    reviews_dir = repo / ".aw" / "records" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "20260929-demo-01-ab12cd-x.review.md"
    content = "# Review: x\n\n- Subject-Id: ab12cd\n"
    review_path.write_text(content, encoding="utf-8")
    c_env = support.clean_git_env()
    subprocess.run(["git", "add", "."], cwd=repo, check=True, env=c_env)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, env=c_env)
    return repo, review_path


def _run_cli(cmd: list[str]) -> tuple[int, str]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = cli.main(cmd)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 0
    if rc is None:
        rc = 0
    return rc, buf_out.getvalue() + buf_err.getvalue()


@pytest.mark.parametrize(
    ("argv_factory", "run_in_cwd"),
    [
        (
            lambda repo, rev: [
                "--no-interactive",
                "set",
                "approved",
                str(rev),
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
            ],
            False,
        ),
        (
            lambda repo, rev: [
                "--no-interactive",
                "set",
                "approved",
                str(rev),
                "--yes",
                "--no-commit",
                "--dry-run",
                "--dir",
                str(repo),
            ],
            False,
        ),
        (
            lambda repo, rev: [
                "--no-interactive",
                "set",
                "other",
                "approved",
                str(rev),
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
            ],
            False,
        ),
        (
            lambda repo, rev: [
                "--no-interactive",
                "set",
                "to-review",
                rev.relative_to(repo).as_posix(),
                "--yes",
                "--no-commit",
            ],
            True,
        ),
    ],
    ids=["untyped", "dry_run", "other_scoped", "relative_path_in_cwd"],
)
def test_set_refuses_review_record(
    repo_with_review: tuple[Path, Path],
    argv_factory: Callable[[Path, Path], list[str]],
    run_in_cwd: bool,
):
    repo, review_path = repo_with_review
    original_bytes = review_path.read_bytes()
    cmd = argv_factory(repo, review_path)

    old_cwd = Path.cwd()
    try:
        if run_in_cwd:
            os.chdir(repo)
        rc, out = _run_cli(cmd)
    finally:
        os.chdir(old_cwd)

    assert rc == 2, f"Expected rc=2, got {rc}. Output: {out}"
    assert "reviews" in out, f"Expected 'reviews' in output. Output: {out}"
    assert (
        "no status lifecycle" in out
    ), f"Expected 'no status lifecycle' in output. Output: {out}"
    assert review_path.read_bytes() == original_bytes, "Review file bytes changed!"

    c_env = support.clean_git_env()
    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        env=c_env,
    )
    assert (
        status_proc.stdout.strip() == ""
    ), f"Git working tree is not clean: {status_proc.stdout}"


def test_set_positive_control_backlog_item(repo_with_review: tuple[Path, Path]):
    repo, _ = repo_with_review
    bkl_dir = repo / ".aw" / "records" / "backlog" / "open"
    bkl_dir.mkdir(parents=True, exist_ok=True)
    bkl_path = bkl_dir / "20260929-zz12cd-01-zz12cd-y.backlog.md"
    content = (
        "# Backlog: y\n\n"
        "- Id: zz12cd\n"
        "- Status: open\n"
        "- Set: zz12cd\n"
        "- Priority: low\n"
        "- Work-Kind: chore\n"
        "- Summary: y\n"
    )
    bkl_path.write_text(content, encoding="utf-8")
    c_env = support.clean_git_env()
    subprocess.run(["git", "add", "."], cwd=repo, check=True, env=c_env)
    subprocess.run(
        ["git", "commit", "-m", "add backlog"], cwd=repo, check=True, env=c_env
    )

    cmd = [
        "--no-interactive",
        "set",
        "parked",
        str(bkl_path),
        "--yes",
        "--no-commit",
        "--dir",
        str(repo),
    ]
    rc, out = _run_cli(cmd)
    assert rc == 0, f"Expected rc=0 for positive control, got {rc}. Output: {out}"

    parked_path = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / "parked"
        / "20260929-zz12cd-01-zz12cd-y.backlog.md"
    )
    assert parked_path.is_file(), f"Expected parked file at {parked_path}"
    parked_text = parked_path.read_text(encoding="utf-8")
    assert "- Status: parked" in parked_text

"""Outcome tests for `aw migrate metadata --apply --include-paths` (spec 4sd62s 5.2 step 7).

IPD clors0 (E-19 / V-19). The one migration commit must be able to carry the cutover's code,
test and documentation changes. The named extra paths are staged BEFORE the step-4a marker
records `git write-tree`, so the installed hooks accept the commit through the marker; a path
staged after the marker changes the tree and the hooks refuse it.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest

from agent_workflows import cli, layout_migration
from agent_workflows.migrations import chain, m0001_metadata_v2

pytestmark = pytest.mark.core

_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/runs/\n"
)
_CODE_REL = "src/feature.py"
_TEST_REL = "tests/test_feature.py"
_DOC_REL = "docs/guide.md"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _install_hooks(repo: Path) -> None:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    pkg_root = Path(__file__).resolve().parent.parent
    hook.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        f'export PYTHONPATH="{pkg_root}${{PYTHONPATH:+:$PYTHONPATH}}"\n'
        f'"{sys.executable}" -m agent_workflows ipd-executed-gate\n'
        f'"{sys.executable}" -m agent_workflows backlog-blocking-close-gate\n',
        encoding="utf-8",
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _legacy_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str) -> Path:
    """A legacy-format repository whose migration renames an executed plan (a gated transition)."""
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    monkeypatch.setenv("HOME", str(aw_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(aw_home / "xdg"))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "backlog" / "done").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")
    (repo / ".aw" / "config").mkdir(parents=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        json.dumps({"schema_version": 2, "preset": "private-target"}, indent=2) + "\n",
        encoding="utf-8",
    )
    (rec / "plans" / "executed" / "20261101-0900-01-legacy-exec.ipd.md").write_text(
        "# IPD: Legacy Executed\n\n"
        "- Id: pl9001\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Short-Description: Executed legacy plan\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 executed (tester): done\n",
        encoding="utf-8",
    )
    (
        rec / "backlog" / "done" / "20261101-demo-01-bk9001-blocking.backlog.md"
    ).write_text(
        "- Id: bk9001\n"
        "- Status: done\n"
        "- Set: demo\n"
        "- Blocks-Release: next\n"
        "- Summary: Release-blocking item\n"
        "- Short-Description: Blocking done item\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src" / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("# Guide\n\nOld text.\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed legacy repository")
    _install_hooks(repo)
    return repo


def _make_uncommitted_cutover_changes(repo: Path) -> Dict[str, bytes]:
    """Modify one tracked code file and one doc, and add one untracked test file."""
    (repo / "src" / "feature.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "docs" / "guide.md").write_text("# Guide\n\nNew text.\n", encoding="utf-8")
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests" / "test_feature.py").write_text(
        "def test_value():\n    assert True\n", encoding="utf-8"
    )
    return {rel: (repo / rel).read_bytes() for rel in (_CODE_REL, _TEST_REL, _DOC_REL)}


def _run_cli(repo: Path, argv: List[str]) -> tuple[int, str]:
    old = os.getcwd()
    buf = io.StringIO()
    try:
        os.chdir(repo)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(argv)
    finally:
        os.chdir(old)
    return rc, buf.getvalue()


def _journal_dir(repo: Path) -> Path:
    return repo / ".aw" / "state" / "durable" / "migrations" / "m0001"


def test_apply_with_include_paths_makes_one_commit_that_passes_every_installed_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _legacy_repo(tmp_path, monkeypatch, "one_commit")
    expected = _make_uncommitted_cutover_changes(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    rc, out = _run_cli(
        repo,
        [
            "migrate",
            "metadata",
            "--apply",
            "--no-describe",
            "--include-paths",
            _CODE_REL,
            _TEST_REL,
            _DOC_REL,
        ],
    )
    assert rc == 0, out

    # Exactly one new commit, made through the installed pre-commit hooks (no --no-verify).
    commits = _git(repo, "rev-list", f"{head_before}..HEAD").stdout.strip().splitlines()
    assert len(commits) == 1
    changed = set(_git(repo, "show", "--name-only", "--format=", "HEAD").stdout.split())
    assert {_CODE_REL, _TEST_REL, _DOC_REL} <= changed
    assert ".aw/records/meta/pl9001.jsonl" in changed
    assert ".aw/records/meta/bk9001.jsonl" in changed
    assert ".aw/config/project.json" in changed
    assert any(p.startswith(".aw/records/plans/executed/") for p in changed)

    # The committed bytes are the uncommitted bytes the operator named.
    for rel, data in expected.items():
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f"HEAD:{rel}"],
            capture_output=True,
            check=True,
        ).stdout
        assert blob == data
    assert chain.read_metadata_schema(repo) == 2
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    assert not (_journal_dir(repo) / "terminal_commit_marker.json").exists()
    jdata = json.loads((_journal_dir(repo) / "journal.json").read_text("utf-8"))
    assert jdata["include_paths"] == sorted([_CODE_REL, _DOC_REL, _TEST_REL])


def test_extra_path_staged_after_the_marker_is_refused_by_the_installed_hooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _legacy_repo(tmp_path, monkeypatch, "late_path")
    _make_uncommitted_cutover_changes(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    report = m0001_metadata_v2.run(
        repo, apply=True, commit=False, include_paths=[_CODE_REL, _TEST_REL]
    )
    assert report["status"] == "applied"
    assert report["include_paths"] == [_CODE_REL, _TEST_REL]
    staged = set(_git(repo, "diff", "--cached", "--name-only").stdout.split())
    assert {_CODE_REL, _TEST_REL} <= staged
    assert _DOC_REL not in staged
    marker = json.loads(
        (_journal_dir(repo) / "terminal_commit_marker.json").read_text("utf-8")
    )
    assert marker["tree_id"] == _git(repo, "write-tree").stdout.strip()

    # The doc is staged AFTER the marker: the staged tree no longer matches it.
    _git(repo, "add", "--", _DOC_REL)
    late = _git(repo, "commit", "-m", "cutover with a late path", check=False)
    assert late.returncode != 0
    assert "terminal commit marker tree_id mismatch" in late.stderr
    assert "raw plan->executed transition" in late.stderr
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_before

    # Unstaging the late path restores the marker's tree, and the same hooks accept the commit.
    _git(repo, "restore", "--staged", "--", _DOC_REL)
    ok = _git(repo, "commit", "-m", "cutover", check=False)
    assert ok.returncode == 0, ok.stderr
    changed = set(_git(repo, "show", "--name-only", "--format=", "HEAD").stdout.split())
    assert {_CODE_REL, _TEST_REL} <= changed
    assert _DOC_REL not in changed


def test_include_paths_are_inert_without_apply_and_bad_paths_refuse_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _legacy_repo(tmp_path, monkeypatch, "inert")
    _make_uncommitted_cutover_changes(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    rc, out = _run_cli(
        repo,
        [
            "migrate",
            "metadata",
            "--dry-run",
            "--no-describe",
            "--include-paths",
            _CODE_REL,
        ],
    )
    assert rc == 0, out
    assert _git(repo, "diff", "--cached", "--name-only").stdout.strip() == ""
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_before
    assert chain.read_metadata_schema(repo) is None
    assert not (repo / ".aw" / "records" / "meta").exists()
    assert not (_journal_dir(repo) / "terminal_commit_marker.json").exists()

    journal_path = _journal_dir(repo) / "journal.json"
    journal_before = journal_path.read_bytes() if journal_path.exists() else None

    (repo / "build").mkdir()
    (repo / "build" / "out.txt").write_text("x\n", encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
    (repo / "ignored.log").write_text("x\n", encoding="utf-8")
    bad = [
        ".aw/records/plans/executed/20261101-0900-01-legacy-exec.ipd.md",
        "build",
        "ignored.log",
        "missing.py",
        str(tmp_path / "outside.txt"),
    ]
    with pytest.raises(layout_migration.PreflightGateError) as exc_info:
        m0001_metadata_v2.run(repo, apply=True, include_paths=bad)
    msg = str(exc_info.value)
    assert "inside the records root" in msg
    assert "build: a directory" in msg
    assert "ignored.log: ignored by git" in msg
    assert "missing.py: neither tracked nor present on disk" in msg
    assert "outside the repository" in msg
    assert _git(repo, "diff", "--cached", "--name-only").stdout.strip() == ""
    assert chain.read_metadata_schema(repo) is None
    journal_after = journal_path.read_bytes() if journal_path.exists() else None
    assert journal_after == journal_before
    assert not (_journal_dir(repo) / "terminal_commit_marker.json").exists()

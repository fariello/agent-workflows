"""Tests for `aw install` / `aw setup` pending-migration prompt, `--migrate`, and schema stamp.

Covers IPD 1vfqdu E-03 / E-04 (V-03): spec 4sd62s AC-28 cases 1-4, AC-11 cases 2-3,
and the phase-A constant-at-1 `--migrate` case.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, Optional, Sequence, Tuple
import pytest

from agent_workflows import cli
from agent_workflows.migrations import chain


# Marked slow per IPD 1vfqdu E-04 duration rule (real `aw install` takes ~3s per test).
pytestmark = pytest.mark.slow

REPO_SOURCE_WORKFLOWS = (
    Path(__file__).resolve().parent.parent / ".aw" / "system" / "workflows"
)


def _clean_git_env() -> Dict[str, str]:
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("GIT_"):
            del env[k]
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", str(repo)],
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _record_hashes(repo: Path) -> Dict[str, str]:
    records_dir = repo / ".aw" / "records"
    out: Dict[str, str] = {}
    if not records_dir.exists():
        return out
    for p in sorted(records_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix()
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _run_cli_inproc(
    repo: Path,
    argv: Sequence[str],
    *,
    aw_home: Path,
    stdin_text: Optional[str] = None,
    force_noninteractive_env: bool = False,
) -> Tuple[int, str, str]:
    old_cwd = os.getcwd()
    old_env = dict(os.environ)
    old_argv = list(sys.argv)
    old_stdin = sys.stdin

    out = io.StringIO()
    err = io.StringIO()
    try:
        os.environ["AW_HOME"] = str(aw_home)
        os.environ["HOME"] = str(aw_home)
        os.environ["XDG_CONFIG_HOME"] = str(aw_home / "xdg")
        os.environ["NO_COLOR"] = "1"
        if force_noninteractive_env:
            os.environ["AW_NONINTERACTIVE"] = "1"
        else:
            os.environ.pop("AW_NONINTERACTIVE", None)
        os.environ.pop("CI", None)
        os.chdir(repo)
        sys.argv = ["agent-workflows", *argv]
        if stdin_text is not None:
            sys.stdin = io.StringIO(stdin_text)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = cli.main(list(argv))
            except SystemExit as exc:
                rc = (
                    int(exc.code)
                    if isinstance(exc.code, int)
                    else (1 if exc.code else 0)
                )
        return rc, out.getvalue(), err.getvalue()
    finally:
        sys.stdin = old_stdin
        sys.argv = old_argv
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)


def _seed_installed_legacy_repo(repo: Path, *, aw_home: Path) -> None:
    """Create a committed legacy-records repo that already has the aw bundle installed."""
    _init_git_repo(repo)
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "20261101-demo-01-ab1234-legacy-plan.ipd.md").write_text(
        "# IPD: Legacy plan\n\n"
        "- Id: ab1234\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 approved (tester): approved\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed legacy plan")

    # Install bundle under phase-A (CURRENT_METADATA_SCHEMA == 1), leaving no metadata_schema stamp.
    rc, out, err = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--preset",
            "private-target",
            "--yes",
        ],
        aw_home=aw_home,
    )
    assert rc == 0, f"pre-install failed:\n{out}\n{err}"
    assert chain.read_metadata_schema(repo) is None

    # Add sidecar and commit anything still untracked/unstaged so the repo starts clean.
    status = _git(repo, "status", "--porcelain").stdout.strip()
    if status:
        _commit_all(repo, "commit install leftovers")
    (repo / ".aw" / "records" / "history.jsonl").write_text(
        json.dumps(
            {
                "date": "2026-11-01",
                "type": "ipd",
                "id6": "ab1234",
                "verb": "set",
                "status": "approved",
            }
        )
        + "\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------------------
# AC-28 cases 1-4
# --------------------------------------------------------------------------------------


def test_ac28_case1_terminal_no_prints_command_and_preserves_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """At a terminal, answering 'n' leaves every record byte-identical and prints `aw migrate metadata`."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)
    before = _record_hashes(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--interactive",
            "--yes",
        ],
        aw_home=aw_home,
        stdin_text="n\n",
    )
    assert rc == 0, out
    assert "Run migration 0001 metadata-v2 now? [y/N]" in out
    assert "aw migrate metadata" in out
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()


def test_ac28_case1_terminal_yes_runs_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """At a terminal, answering 'y' runs the pending migration."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)
    before = _record_hashes(repo)
    assert ".aw/records/history.jsonl" in before

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--interactive",
            "--yes",
        ],
        aw_home=aw_home,
        stdin_text="y\n",
    )
    assert rc == 0, out
    assert "Run migration 0001 metadata-v2 now? [y/N]" in out
    journal = (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    assert journal.is_file()
    assert json.loads(journal.read_text(encoding="utf-8"))["status"] == "applied"
    assert not (repo / ".aw" / "records" / "history.jsonl").exists()


def test_ac28_case2_no_terminal_only_reports_and_preserves_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no terminal and no `--migrate`, install only reports and leaves records byte-identical."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)
    before = _record_hashes(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--no-interactive",
            "--yes",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc == 0, out
    assert "0001 metadata-v2" in out
    assert "aw migrate metadata" in out
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()


def test_ac28_case3_yes_and_install_all_yes_never_run_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`aw install --yes` and `aw install all --yes` report pending migration and keep records byte-identical."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)
    before = _record_hashes(repo)

    # Configure allowlist for `aw install all --yes` under isolated XDG_CONFIG_HOME
    cfg_dir = aw_home / "xdg" / "agent-workflows"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.json").write_text(
        json.dumps({"repos": {"search": [], "installed": [str(repo)], "exclude": []}})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc_single, out_single, _ = _run_cli_inproc(
        repo,
        ["install", str(repo), "--source", str(REPO_SOURCE_WORKFLOWS), "--yes"],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_single == 0, out_single
    assert "aw migrate metadata" in out_single
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()

    rc_all, out_all, _ = _run_cli_inproc(
        repo,
        ["install", "all", "--source", str(REPO_SOURCE_WORKFLOWS), "--yes"],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_all == 0, out_all
    assert "aw migrate metadata" in out_all
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()


def test_ac28_case4_migrate_flag_runs_and_still_refuses_step1_condition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`aw install --migrate` runs without `--force` or `--force-worktree`, so step-1 refusals still stop it."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)

    # Dirty a tracked record under .aw/records/ to trigger step-1 UNCOMMITTED refusal.
    plan_file = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-ab1234-legacy-plan.ipd.md"
    )
    plan_file.write_text(
        plan_file.read_text(encoding="utf-8") + "\n<!-- dirty -->\n",
        encoding="utf-8",
    )
    before = _record_hashes(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc_refused, out_refused, err_refused = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--yes",
            "--migrate",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_refused == 1
    assert "UNCOMMITTED" in (out_refused + err_refused)
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()

    # Clean the dirty record and verify `aw setup --root ... --yes --migrate` applies cleanly.
    _git(repo, "checkout", "--", str(plan_file.relative_to(repo)))
    rc_ok, out_ok, _ = _run_cli_inproc(
        repo,
        [
            "setup",
            "--root",
            str(repo.parent),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--yes",
            "--migrate",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_ok == 0, out_ok
    journal = (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    assert journal.is_file()
    assert json.loads(journal.read_text(encoding="utf-8"))["status"] == "applied"


# --------------------------------------------------------------------------------------
# AC-11 cases 2 and 3, plus E-03 phase-A constant-at-1 case
# --------------------------------------------------------------------------------------


def test_ac11_case2_empty_repo_stamped_and_commands_succeed_under_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`aw install` in an empty repo writes metadata_schema=2; backlog new + find succeed without migrate."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "empty_repo"
    _init_git_repo(repo)
    (repo / "README.md").write_text("# empty\n", encoding="utf-8")
    _commit_all(repo, "init")

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, err = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--preset",
            "private-target",
            "--yes",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc == 0, f"{out}\n{err}"
    assert chain.read_metadata_schema(repo) == 2

    rc_b, out_b, err_b = _run_cli_inproc(
        repo,
        [
            "backlog",
            "new",
            "--summary",
            "Fresh repo item",
            "--priority",
            "low",
            "--work-kind",
            "chore",
            "--apply",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_b == 0, f"{out_b}\n{err_b}"

    rc_f, out_f, err_f = _run_cli_inproc(
        repo,
        ["find", "backlog"],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc_f == 0, f"{out_f}\n{err_f}"
    assert "fresh-repo-item" in out_f


def test_ac11_case3_legacy_repo_is_never_stamped_by_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`aw install` in a repository with legacy records never writes `metadata_schema`."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "legacy_repo"
    _init_git_repo(repo)
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "20261101-demo-01-ab1234-legacy-plan.ipd.md").write_text(
        "# IPD: Legacy plan\n\n- Id: ab1234\n- Status: approved\n\n## Workflow history\n\n- 2026-11-01 approved (tester): approved\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed legacy")
    before = _record_hashes(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, err = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--preset",
            "private-target",
            "--yes",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc == 0, f"{out}\n{err}"
    assert chain.read_metadata_schema(repo) is None
    after = _record_hashes(repo)
    for rel, digest in before.items():
        assert after.get(rel) == digest


def test_e03_phase_a_constant_at_1_migrate_asks_and_runs_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With CURRENT_METADATA_SCHEMA left at 1, `aw install --migrate` asks and runs nothing."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_installed_legacy_repo(repo, aw_home=aw_home)
    before = _record_hashes(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 1)
    rc, out, _ = _run_cli_inproc(
        repo,
        [
            "install",
            str(repo),
            "--source",
            str(REPO_SOURCE_WORKFLOWS),
            "--yes",
            "--migrate",
        ],
        aw_home=aw_home,
        force_noninteractive_env=True,
    )
    assert rc == 0, out
    assert "Run migration" not in out
    assert _record_hashes(repo) == before
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()

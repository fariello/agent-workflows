"""CLI tests for `aw migrate` group, bare `aw migrate`, and `chain.pending_migrations`.

Covers IPD 1vfqdu E-01, E-02, E-04, E-05 (V-01, V-02, V-05).
All tests use real `git init` repositories under `tmp_path` and assert on CLI outputs,
exit codes, git state, and SHA-256 file bytes.
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


pytestmark = pytest.mark.core


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
    _git(repo, "config", "core.autocrlf", "false")


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _tree_sha256(
    root: Path, *, ignore_prefixes: Tuple[str, ...] = (".git/", ".aw/state/")
) -> Dict[str, str]:
    digests: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(rel.startswith(pref) for pref in ignore_prefixes):
            continue
        digests[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return digests


def _run_cli_inproc(
    repo: Path,
    argv: Sequence[str],
    *,
    aw_home: Path,
    stdin_text: Optional[str] = None,
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


def _seed_legacy_aw_repo(repo: Path, *, with_sidecar: bool = True) -> None:
    _init_git_repo(repo)
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "20261101-demo-01-ab1234-legacy-plan.ipd.md").write_text(
        "# IPD: Legacy plan\n\n"
        "- Id: ab1234\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Short-Description: Legacy plan\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 approved (tester): approved\n",
        encoding="utf-8",
    )
    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / ".aw" / ".gitignore").write_text(
        "/state/\nrecords/history.jsonl\n", encoding="utf-8"
    )
    _commit_all(repo, "seed legacy aw repo")
    if with_sidecar:
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


def _seed_legacy_agents_repo(repo: Path) -> None:
    _init_git_repo(repo)
    (repo / ".agents" / "workflows").mkdir(parents=True, exist_ok=True)
    (repo / ".agents" / "workflows" / "index.md").write_text(
        "# workflows\n", encoding="utf-8"
    )
    plans_dir = repo / ".agents" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    (plans_dir / "20261101-demo-01-ab1234-legacy-plan.md").write_text(
        "# IPD: Legacy agents plan\n\n"
        "- Id: ab1234\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Short-Description: Legacy agents plan\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 approved (tester): approved\n",
        encoding="utf-8",
    )
    _commit_all(repo, "seed legacy agents repo")


# --------------------------------------------------------------------------------------
# E-01: aw migrate group, metadata leaf, and layout leaf
# --------------------------------------------------------------------------------------


def test_migrate_help_lists_metadata_and_layout_and_group_flags(
    tmp_path: Path,
) -> None:
    """`aw migrate --help` lists `metadata` and `layout` plus bare-group flags."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    rc, out, _ = _run_cli_inproc(tmp_path, ["migrate", "--help"], aw_home=aw_home)
    assert rc == 0
    assert "metadata" in out
    assert "layout" in out
    assert "[<subcommand>]" in out
    assert "--dry-run" in out
    assert "--apply" in out
    assert "--commit" in out


def test_migrate_layout_status_matches_migrate_layout_status(tmp_path: Path) -> None:
    """`aw migrate layout status` and `aw migrate-layout status` produce identical output."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_agents_repo(repo)

    rc_new, out_new, err_new = _run_cli_inproc(
        repo, ["migrate", "layout", "status"], aw_home=aw_home
    )
    rc_old, out_old, err_old = _run_cli_inproc(
        repo, ["migrate-layout", "status"], aw_home=aw_home
    )
    assert rc_new == rc_old == 0
    assert out_new == out_old
    assert err_new == err_old


def test_migrate_metadata_explicit_leaf_runs_before_cutover(tmp_path: Path) -> None:
    """`aw migrate metadata` executes by default and requires `--dry-run` to preview."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=True)

    assert chain.CURRENT_METADATA_SCHEMA == 1
    before_tree = _tree_sha256(repo)
    rc_dry, out_dry, _ = _run_cli_inproc(
        repo, ["migrate", "metadata", "--dry-run"], aw_home=aw_home
    )
    assert rc_dry == 0, out_dry
    assert _tree_sha256(repo) == before_tree
    assert "Dry run only" in out_dry

    rc_apply, out_apply, _ = _run_cli_inproc(
        repo, ["migrate", "metadata"], aw_home=aw_home
    )
    assert rc_apply == 0, out_apply
    journal_file = (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    assert journal_file.is_file()
    journal_data = json.loads(journal_file.read_text(encoding="utf-8"))
    assert journal_data["status"] == "applied"
    assert not (repo / ".aw" / "records" / "history.jsonl").exists()


# --------------------------------------------------------------------------------------
# E-05: chain.pending_migrations (4 cases)
# --------------------------------------------------------------------------------------


def test_pending_migrations_returns_m0001_when_schema_2_and_legacy_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unstamped legacy repo returns [m0001] when CURRENT_METADATA_SCHEMA is 2."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=False)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    pending = chain.pending_migrations(repo)
    assert pending == [chain.MIGRATIONS[0]]


def test_pending_migrations_returns_empty_when_schema_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same legacy repo returns [] when CURRENT_METADATA_SCHEMA is 1."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=False)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 1)
    assert chain.pending_migrations(repo) == []


def test_pending_migrations_returns_empty_when_stamped_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repo stamped metadata_schema=2 returns [] even under CURRENT_METADATA_SCHEMA=2."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    chain.write_metadata_schema(repo, 2)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    assert chain.pending_migrations(repo) == []


def test_pending_migrations_returns_empty_for_empty_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty repo with no legacy records returns [] under CURRENT_METADATA_SCHEMA=2."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))
    repo = tmp_path / "repo"
    _init_git_repo(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    assert chain.pending_migrations(repo) == []


# --------------------------------------------------------------------------------------
# E-02: bare aw migrate (7 cases)
# --------------------------------------------------------------------------------------


def test_bare_migrate_case1_legacy_layout_and_records_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 1: `--dry-run` on legacy .agents/ + legacy records lists layout then metadata with zero tracked changes and no interactive rename prompt."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_agents_repo(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    monkeypatch.setattr("agent_workflows.term.is_interactive", lambda *a, **kw: True)
    before = _tree_sha256(repo)
    rc, out, _ = _run_cli_inproc(repo, ["migrate", "--dry-run"], aw_home=aw_home)
    after = _tree_sha256(repo)

    assert rc == 0, out
    assert before == after
    assert "Also rename migrated records" not in out
    assert "Dry run only" in out
    assert "layout" in out
    assert "metadata" in out
    assert out.index("layout") < out.index("metadata")


def test_bare_migrate_case2_default_commit_runs_layout_commits_then_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 2: bare `aw migrate --commit` executes by default: runs layout, commits its moves, then runs metadata."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_agents_repo(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(
        repo, ["migrate", "--commit", "--json"], aw_home=aw_home
    )
    assert rc == 0, out
    records = [json.loads(line) for line in out.strip().splitlines() if line.strip()]
    assert [r["step"] for r in records] == ["layout", "metadata"]
    assert all(r["applied"] is True for r in records)

    head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head_after != head_before
    assert (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-ab1234-legacy-plan.md"
    ).is_file()
    journal_file = (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    )
    assert journal_file.is_file()
    assert json.loads(journal_file.read_text(encoding="utf-8"))["status"] == "applied"


def test_bare_migrate_case3_without_commit_leaves_uncommitted_and_skips_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 3: bare `aw migrate` without `--commit` executes layout, leaves moves uncommitted, and skips metadata."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_agents_repo(repo)
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(repo, ["migrate"], aw_home=aw_home)
    assert rc == 1, out
    assert "layout" in out
    assert "aw migrate --commit" in out
    assert "aw commit" in out
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_before
    status_out = _git(repo, "status", "--porcelain", "--", ".aw/records").stdout.strip()
    assert status_out != ""
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()


def test_bare_migrate_case4_aw_only_legacy_records_lists_only_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 4: repository with only `.aw/` legacy records lists only metadata on `--dry-run`."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=False)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(
        repo, ["migrate", "--dry-run", "--json"], aw_home=aw_home
    )
    assert rc == 0, out
    records = [json.loads(line) for line in out.strip().splitlines() if line.strip()]
    assert [r["step"] for r in records] == ["metadata"]
    assert records[0]["applied"] is False


def test_bare_migrate_case5_migrated_repo_prints_nothing_to_migrate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 5: fully migrated repository prints 'nothing to migrate' and exits 0."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    chain.write_metadata_schema(repo, 2)
    _commit_all(repo, "stamped v2")

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, _ = _run_cli_inproc(repo, ["migrate"], aw_home=aw_home)
    assert rc == 0, out
    assert "nothing to migrate" in out.lower()


def test_bare_migrate_case6_refused_layout_step_does_not_start_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 6: when the layout step refuses under bare `aw migrate --commit`, metadata does not start."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_agents_repo(repo)

    # Plant an unknown-owner top-level directory under `.agents/` so layout preflight refuses.
    (repo / ".agents" / "unknown_custom").mkdir(parents=True, exist_ok=True)
    (repo / ".agents" / "unknown_custom" / "stray.md").write_text(
        "# stray\n", encoding="utf-8"
    )
    _commit_all(repo, "add unknown owner under .agents")

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    rc, out, err = _run_cli_inproc(repo, ["migrate", "--commit"], aw_home=aw_home)
    assert rc != 0
    assert "layout" in (out + err).lower()
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "journal.json"
    ).exists()


def test_bare_migrate_case7_phase_a_constant_1_aw_only_prints_nothing_to_migrate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Case 7: with CURRENT_METADATA_SCHEMA at 1, `.aw/`-only legacy repo prints 'nothing to migrate'."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=False)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 1)
    rc, out, _ = _run_cli_inproc(repo, ["migrate"], aw_home=aw_home)
    assert rc == 0, out
    assert "nothing to migrate" in out.lower()


def test_bare_migrate_ignores_preserved_agents_skills_in_modern_aw_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Modern `.aw/` repo with only `.agents/skills/` reports nothing to migrate and mutates zero files."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    repo = tmp_path / "repo"
    _seed_legacy_aw_repo(repo, with_sidecar=False)
    (repo / ".agents" / "skills" / "demo").mkdir(parents=True, exist_ok=True)
    (repo / ".agents" / "skills" / "demo" / "SKILL.md").write_text(
        "# Demo skill\n", encoding="utf-8"
    )
    (repo / ".aw" / "config" / "config.json").write_text(
        json.dumps({"records_backend": "repository"}, indent=2) + "\n",
        encoding="utf-8",
    )
    _commit_all(repo, "add preserved .agents/skills and config.json")
    before_tree = _tree_sha256(repo)

    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 1)
    rc, out, err = _run_cli_inproc(repo, ["migrate", "--agent"], aw_home=aw_home)
    assert rc == 0, err or out
    rec = json.loads(out.strip().splitlines()[-1])
    assert rec["outcome"] == "clean", rec
    assert rec["applied"] is False, rec

    rc_plain, out_plain, err_plain = _run_cli_inproc(repo, ["migrate"], aw_home=aw_home)
    assert rc_plain == 0, err_plain or out_plain
    assert "nothing to migrate" in out_plain.lower()
    assert _tree_sha256(repo) == before_tree
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "switch_receipt.json"
    ).exists()
    assert not (
        repo / ".aw" / "state" / "durable" / "migrations" / "retention_manifest.json"
    ).exists()

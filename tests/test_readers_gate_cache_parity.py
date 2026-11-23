"""Gate and setter cache-parity and offline execution tests (spec `4sd62s` AC-1a, AC-12; IPD `t4gl15` E-13 / E-14).

Exercises `aw ipd set to-review <plan>`, `aw ipd-status-untooled-gate`, `aw ipd-executed-gate`,
and `aw backlog-blocking-close-gate` across cold, warm, deleted, and corrupt SQLite cache states,
staged external edits without cache rebuild, and unparseable staged records failing closed while
naming the record. Also proves `aw ipd set to-review <plan>` and `aw ipd-executed-gate` exit 0
offline with `opencode`, `agy`, and `claude` removed from `PATH` and `socket.socket` disabled
through a `sitecustomize` on `PYTHONPATH`. Uses real `git init` repositories and real `aw` CLI
entry points without inspecting production source code.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import backlog, cli, plans
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOST_BINARIES = ("opencode", "agy", "claude")

_PARITY_COMMANDS = (
    "ipd_set_to_review",
    "ipd_status_untooled_gate",
    "ipd_executed_gate",
    "backlog_blocking_close_gate",
)
_CACHE_STATES = ("cold", "warm", "deleted", "corrupt")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def _run_cli_in_repo(repo: Path, argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    prev_cwd = os.getcwd()
    prev_noninteractive = os.environ.get("AW_NONINTERACTIVE")
    os.chdir(repo)
    os.environ["AW_NONINTERACTIVE"] = "1"
    try:
        with patch("sys.stdout", out), patch("sys.stderr", err):
            try:
                rc = cli.main(argv)
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
    finally:
        os.chdir(prev_cwd)
        if prev_noninteractive is None:
            os.environ.pop("AW_NONINTERACTIVE", None)
        else:
            os.environ["AW_NONINTERACTIVE"] = prev_noninteractive
    return rc, out.getvalue(), err.getvalue()


def _cache_files(state_root: Path) -> List[Path]:
    db = state_root / "index.db"
    return [
        db,
        Path(f"{db}-wal"),
        Path(f"{db}-shm"),
        Path(f"{db}-journal"),
    ]


def _delete_cache(state_root: Path) -> None:
    for path in _cache_files(state_root):
        if path.exists():
            path.unlink()


def _corrupt_cache(state_root: Path) -> None:
    _delete_cache(state_root)
    state_root.mkdir(parents=True, exist_ok=True)
    garbage = bytes((i * 73 + 19) % 256 for i in range(4096))
    (state_root / "index.db").write_bytes(garbage)


def _normalize(text: str, repo: Path) -> str:
    norm = text.replace("\r\n", "\n")
    norm = norm.replace(str(repo.resolve()), "<REPO>")
    norm = norm.replace(str(repo), "<REPO>")
    return norm


def _plan_text(
    *,
    id6: str,
    status: str = "draft",
    order: int = 1,
    history_lines: Tuple[str, ...] = ("- 2026-11-01 draft (tester): created",),
) -> str:
    valid_status = status if status in plans.RECOGNIZED else "approved"
    raw_fields: Dict[str, object] = {
        "Concern": f"Verify gate cache parity for {id6}.",
        "Scope": "Exercise staged git reads and setter transitions across cache states.",
    }
    if valid_status != status:
        raw_fields["Status"] = status
    return str(
        RecordBuilder().plan(
            title=f"Gate Parity Plan {id6}",
            when="2026-11-01",
            plan_role="child",
            scope_paths="tests/test_readers_gate_cache_parity.py",
            item_dependencies="none",
            status=valid_status,
            work_kind="chore",
            priority="low",
            set="gset",
            order=order,
            highest_e_allocated="01",
            author="tester",
            review_depth="simple",
            id6=id6,
            history=list(history_lines),
            open_questions="None.",
            body=(
                "## Goal\n\n"
                "Verify gate and setter parity across cache states.\n\n"
                "## Detailed Implementation Checklist (TODO)\n\n"
                "- [ ] E-01 Execute check\n"
                "  - Depends on: none\n"
                "  - Expected outcome: command output is deterministic\n"
                "  - Execution state: pending\n\n"
                "## Project conventions discovered (Step 0)\n\n"
                "- Core tests run under pytest.\n\n"
                "## Findings\n\n"
                "- None.\n\n"
                "## Proposed changes (ordered, validatable)\n\n"
                "1. Run gate parity checks.\n\n"
                "## Deferred / out of scope (with reason)\n\n"
                "None.\n\n"
                "## Scope check\n\n"
                "- Over-scope: none.\n"
                "- Under-scope: none.\n\n"
                "## Required tests / validation\n\n"
                "Run pytest on tests/test_readers_gate_cache_parity.py.\n\n"
                "## Spec / documentation sync\n\n"
                "N/A.\n\n"
                "## Validation and cross-check (verify before reporting done)\n\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: paste pytest output with every case PASSED\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n\n"
                "## Approval and execution gate\n\n"
                "- Size assessment: standard\n"
                "- Cohesion rationale: not required"
            ),
            raw_fields=raw_fields,
            text_only=True,
        )
    )


def _backlog_text(
    *,
    id6: str,
    status: str,
    blocks_release: str | None = None,
) -> str:
    extra: Dict[str, object] = {}
    if blocks_release is not None:
        extra["blocks_release"] = blocks_release
    return str(
        RecordBuilder().backlog(
            id6=id6,
            summary=f"Gate parity backlog {id6}",
            when="2026-11-01",
            status=status,
            work_kind="bug",
            priority="high",
            set="gset",
            history=[f"- 2026-11-01 {status} (aw backlog): state"],
            body="## Details\n\nGate parity backlog item.",
            text_only=True,
            **extra,
        )
    )


def _init_base_repo(tmp_path: Path, name: str) -> Tuple[Path, Dict[str, str]]:
    """Create a committed fixture repository with plans, backlog item, and release."""
    repo = (tmp_path / name).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Parity Tester")
    _git(repo, "config", "user.email", "parity@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

    wf_dir = repo / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "index.md").write_text("# Workflows\n", encoding="utf-8")

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "placements": {
                    "system": "target-tracked",
                    "config_project": "target-tracked",
                    "config_local": "target-ignored",
                    "state_durable": "target-tracked",
                    "state_runtime": "target-ignored",
                    "records": "target-tracked",
                },
                "records_backend": "repository",
                "dependency_schema_cutover": {"date": "2020-01-01"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for sub in (
        ".aw/records/plans/pending",
        ".aw/records/plans/executed",
        ".aw/records/plans/superseded",
        ".aw/records/specs/approved",
        ".aw/records/releases",
    ):
        (repo / sub).mkdir(parents=True, exist_ok=True)
    for st in backlog.STATUSES:
        (repo / ".aw" / "records" / "backlog" / st).mkdir(parents=True, exist_ok=True)

    (
        repo
        / ".aw"
        / "records"
        / "releases"
        / "20261101-rel001-01-rel001-v1.release.md"
    ).write_text(
        RecordBuilder().release(
            version="1.0.0",
            when="2026-11-01",
            id6="rel001",
            status="planned",
            set="rel001 (1.0.0)",
            order=1,
            summary="Parity test release",
            text_only=True,
        ),
        encoding="utf-8",
    )

    paths = {
        "setter_plan": ".aw/records/plans/pending/20261101-gset-01-gp0001-setter.ipd.md",
        "untooled_plan": ".aw/records/plans/pending/20261101-gset-02-gp0002-untooled.ipd.md",
        "executed_plan": ".aw/records/plans/pending/20261101-gset-03-gp0003-executed.ipd.md",
        "executed_plan_dest": ".aw/records/plans/executed/20261101-gset-03-gp0003-executed.ipd.md",
        "backlog_open": ".aw/records/backlog/open/20261101-gset-01-gb0001-blocker.backlog.md",
        "backlog_done": ".aw/records/backlog/done/20261101-gset-01-gb0001-blocker.backlog.md",
    }

    (repo / paths["setter_plan"]).write_text(
        _plan_text(id6="gp0001", status="draft", order=1), encoding="utf-8"
    )
    (repo / paths["untooled_plan"]).write_text(
        _plan_text(id6="gp0002", status="draft", order=2), encoding="utf-8"
    )
    (repo / paths["executed_plan"]).write_text(
        _plan_text(id6="gp0003", status="approved", order=3), encoding="utf-8"
    )
    (repo / paths["backlog_open"]).write_text(
        _backlog_text(id6="gb0001", status="open", blocks_release="next"),
        encoding="utf-8",
    )

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gate parity fixture")
    return repo, paths


def _build_staged_parity_repo(tmp_path: Path, name: str) -> Tuple[Path, Dict[str, str]]:
    """Build a staged repository exercising all three pre-commit gates and a clean setter target."""
    repo, paths = _init_base_repo(tmp_path, name)

    # 1. Staged untooled status flip (no matching history line) -> ipd-status-untooled-gate refuses.
    (repo / paths["untooled_plan"]).write_text(
        _plan_text(id6="gp0002", status="to-review", order=2), encoding="utf-8"
    )
    _git(repo, "add", paths["untooled_plan"])

    # 2. Staged raw move into executed/ (no finalize journal) -> ipd-executed-gate refuses.
    _git(repo, "mv", paths["executed_plan"], paths["executed_plan_dest"])
    (repo / paths["executed_plan_dest"]).write_text(
        _plan_text(id6="gp0003", status="executed", order=3), encoding="utf-8"
    )
    _git(repo, "add", paths["executed_plan_dest"])

    # 3. Staged blocking backlog close to done/ without handoff -> backlog-blocking-close-gate refuses.
    _git(repo, "mv", paths["backlog_open"], paths["backlog_done"])
    (repo / paths["backlog_done"]).write_text(
        _backlog_text(id6="gb0001", status="done", blocks_release="next"),
        encoding="utf-8",
    )
    _git(repo, "add", paths["backlog_done"])

    return repo, paths


def _invoke_parity_command(
    repo: Path, paths: Dict[str, str], command: str
) -> Tuple[int, str, str]:
    if command == "ipd_set_to_review":
        rc, out, err = _run_cli_in_repo(
            repo,
            [
                "ipd",
                "set",
                "to-review",
                "gp0001",
                "--message",
                "ready for review",
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
            ],
        )
        return rc, _normalize(out, repo), _normalize(err, repo)

    if command == "ipd_status_untooled_gate":
        rc, out, err = _run_cli_in_repo(repo, ["ipd-status-untooled-gate"])
        return rc, _normalize(out, repo), _normalize(err, repo)

    if command == "ipd_executed_gate":
        rc, out, err = _run_cli_in_repo(repo, ["ipd-executed-gate"])
        return rc, _normalize(out, repo), _normalize(err, repo)

    if command == "backlog_blocking_close_gate":
        rc, out, err = _run_cli_in_repo(repo, ["backlog-blocking-close-gate"])
        return rc, _normalize(out, repo), _normalize(err, repo)

    raise ValueError(f"Unknown command: {command}")


# --------------------------------------------------------------------------------------
# E-13: 4 commands x 4 cache states = 16 parity cases (AC-1a)
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _base_template(
    tmp_path_factory: pytest.TempPathFactory,
) -> Tuple[Path, Dict[str, str]]:
    """Build the committed base repository once per module for fast per-test copytree."""
    base_dir = tmp_path_factory.mktemp("gate_parity_base_tpl")
    return _init_base_repo(base_dir, "tpl_base")


@pytest.fixture(scope="module")
def _staged_template(
    tmp_path_factory: pytest.TempPathFactory,
) -> Tuple[Path, Dict[str, str]]:
    """Build the staged parity repository once per module for fast per-test copytree."""
    staged_dir = tmp_path_factory.mktemp("gate_parity_staged_tpl")
    return _build_staged_parity_repo(staged_dir, "tpl_staged")


def _clone_template(
    template: Tuple[Path, Dict[str, str]], tmp_path: Path, name: str
) -> Tuple[Path, Dict[str, str]]:
    src, paths = template
    dst = (tmp_path / name).resolve()
    shutil.copytree(src, dst)
    return dst, dict(paths)


@pytest.fixture(scope="module")
def _cold_gate_references(
    tmp_path_factory: pytest.TempPathFactory,
    _staged_template: Tuple[Path, Dict[str, str]],
) -> Dict[str, Tuple[int, str, str, str]]:
    """Compute the cold-cache reference `(rc, stdout, stderr, plan_text)` once per command."""
    refs: Dict[str, Tuple[int, str, str, str]] = {}
    base = tmp_path_factory.mktemp("gate_parity_refs")
    for cmd in _PARITY_COMMANDS:
        repo, paths = _clone_template(_staged_template, base, f"ref_{cmd}")
        assert not (repo / ".aw" / "state" / "index.db").exists()
        rc, out, err = _invoke_parity_command(repo, paths, cmd)
        if cmd == "ipd_set_to_review":
            assert rc == 0, f"cold setter failed: stdout={out!r} stderr={err!r}"
            plan_after = (repo / paths["setter_plan"]).read_text(encoding="utf-8")
            assert "- Status: to-review" in plan_after
        elif cmd == "ipd_status_untooled_gate":
            assert rc == 1, f"expected refusal, got rc={rc}: out={out!r} err={err!r}"
            assert "gp0002" in err
            plan_after = ""
        elif cmd == "ipd_executed_gate":
            assert rc == 1, f"expected refusal, got rc={rc}: out={out!r} err={err!r}"
            assert "gp0003" in err
            plan_after = ""
        elif cmd == "backlog_blocking_close_gate":
            assert rc == 1, f"expected refusal, got rc={rc}: out={out!r} err={err!r}"
            assert "gb0001" in err
            plan_after = ""
        else:
            raise AssertionError(cmd)
        refs[cmd] = (rc, out, err, plan_after)
    return refs


@pytest.mark.parametrize("command", _PARITY_COMMANDS)
@pytest.mark.parametrize("cache_state", _CACHE_STATES)
def test_gate_and_setter_cache_state_parity(
    tmp_path: Path,
    _staged_template: Tuple[Path, Dict[str, str]],
    _cold_gate_references: Dict[str, Tuple[int, str, str, str]],
    command: str,
    cache_state: str,
) -> None:
    ref_rc, ref_out, ref_err, ref_plan_after = _cold_gate_references[command]
    repo, paths = _clone_template(
        _staged_template, tmp_path, f"target_{command}_{cache_state}"
    )
    state_dir = repo / ".aw" / "state"
    db_path = state_dir / "index.db"

    if cache_state == "cold":
        assert not db_path.exists()
    elif cache_state == "warm":
        rc_rb, _, err_rb = _run_cli_in_repo(
            repo, ["index", "rebuild", "--agent", "--dir", str(repo)]
        )
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        if command == "ipd_set_to_review":
            # Warm working-tree cache via a read-only lookup without mutating gp0001 yet.
            rc_f, _, err_f = _run_cli_in_repo(
                repo, ["find", "plans", "gp0001", "--paths", "--dir", str(repo)]
            )
            assert rc_f == 0 and err_f == ""
        else:
            # Prime rev_mirrors / rev_log_states for the read-only gate before measuring warm run.
            _invoke_parity_command(repo, paths, command)
        assert db_path.is_file()
    elif cache_state == "deleted":
        rc_rb, _, err_rb = _run_cli_in_repo(
            repo, ["index", "rebuild", "--agent", "--dir", str(repo)]
        )
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        _delete_cache(state_dir)
        assert not db_path.exists()
    elif cache_state == "corrupt":
        rc_rb, _, err_rb = _run_cli_in_repo(
            repo, ["index", "rebuild", "--agent", "--dir", str(repo)]
        )
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        _corrupt_cache(state_dir)
        assert db_path.is_file()

    got_rc, got_out, got_err = _invoke_parity_command(repo, paths, command)
    assert got_rc == ref_rc, (
        f"{command} ({cache_state}) rc={got_rc} != cold ref rc={ref_rc}\n"
        f"stdout={got_out!r}\nstderr={got_err!r}"
    )
    assert (
        got_out == ref_out
    ), f"{command} ({cache_state}) stdout diverged from cold ref"
    assert (
        got_err == ref_err
    ), f"{command} ({cache_state}) stderr diverged from cold ref"
    if command == "ipd_set_to_review":
        got_plan_after = (repo / paths["setter_plan"]).read_text(encoding="utf-8")
        assert got_plan_after == ref_plan_after


# --------------------------------------------------------------------------------------
# E-13: Staged external edit visible with no cache rebuild
# --------------------------------------------------------------------------------------


def test_staged_external_edit_visible_without_rebuild_parity(
    tmp_path: Path, _base_template: Tuple[Path, Dict[str, str]]
) -> None:
    """Each pre-commit gate observes a newly staged external edit without rebuilding index.db."""
    repo, paths = _clone_template(_base_template, tmp_path, "ext_staged")

    # Warm the cache on the clean repository and confirm all three gates pass.
    rc_rb, _, err_rb = _run_cli_in_repo(
        repo, ["index", "rebuild", "--agent", "--dir", str(repo)]
    )
    assert rc_rb == 0 and err_rb == ""
    assert (repo / ".aw" / "state" / "index.db").is_file()

    for gate_cmd in (
        "ipd-status-untooled-gate",
        "ipd-executed-gate",
        "backlog-blocking-close-gate",
    ):
        rc0, _, err0 = _run_cli_in_repo(repo, [gate_cmd])
        assert rc0 == 0, f"clean {gate_cmd} failed: {err0}"

    # Stage external edits directly outside artifact_meta and DO NOT run aw index rebuild.
    (repo / paths["untooled_plan"]).write_text(
        _plan_text(id6="gp0002", status="to-review", order=2), encoding="utf-8"
    )
    _git(repo, "add", paths["untooled_plan"])

    (repo / paths["executed_plan"]).write_text(
        _plan_text(id6="gp0003", status="executed", order=3), encoding="utf-8"
    )
    _git(repo, "add", paths["executed_plan"])

    _git(repo, "mv", paths["backlog_open"], paths["backlog_done"])
    (repo / paths["backlog_done"]).write_text(
        _backlog_text(id6="gb0001", status="done", blocks_release="next"),
        encoding="utf-8",
    )
    _git(repo, "add", paths["backlog_done"])

    rc_u, _, err_u = _run_cli_in_repo(repo, ["ipd-status-untooled-gate"])
    assert rc_u == 1, f"untooled gate missed staged external edit: {err_u!r}"
    assert "gp0002" in err_u

    rc_e, _, err_e = _run_cli_in_repo(repo, ["ipd-executed-gate"])
    assert rc_e == 1, f"executed gate missed staged external edit: {err_e!r}"
    assert "gp0003" in err_e

    rc_b, _, err_b = _run_cli_in_repo(repo, ["backlog-blocking-close-gate"])
    assert rc_b == 1, f"backlog gate missed staged external edit: {err_b!r}"
    assert "gb0001" in err_b


# --------------------------------------------------------------------------------------
# E-13: Unparseable staged blob / corrupt staged log fails closed naming the record
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("gate_cmd", "corrupt_mode"),
    [
        ("ipd-status-untooled-gate", "invalid_utf8_md"),
        ("ipd-status-untooled-gate", "corrupt_meta_log"),
        ("ipd-executed-gate", "invalid_utf8_md"),
        ("ipd-executed-gate", "corrupt_meta_log"),
        ("backlog-blocking-close-gate", "invalid_utf8_md"),
        ("backlog-blocking-close-gate", "corrupt_meta_log"),
    ],
)
def test_invalid_staged_record_fails_closed_parity(
    tmp_path: Path,
    _base_template: Tuple[Path, Dict[str, str]],
    gate_cmd: str,
    corrupt_mode: str,
) -> None:
    """Replacing a staged blob with an unparseable record makes the gate fail closed naming it."""
    repo, paths = _clone_template(
        _base_template, tmp_path, f"invalid_{gate_cmd}_{corrupt_mode}"
    )

    # Warm the cache first so stale state would be served if fail-closed were broken.
    rc_rb, _, err_rb = _run_cli_in_repo(
        repo, ["index", "rebuild", "--agent", "--dir", str(repo)]
    )
    assert rc_rb == 0 and err_rb == ""

    if gate_cmd in ("ipd-status-untooled-gate", "ipd-executed-gate"):
        target_rel = paths["untooled_plan"]
        target_id = "gp0002"
        if corrupt_mode == "invalid_utf8_md":
            (repo / target_rel).write_bytes(b"\xff\xfe\x00\x00unparseable-record")
            _git(repo, "add", target_rel)
        else:
            # Stage a touched plan alongside a corrupt staged meta/<id6>.jsonl log.
            (repo / target_rel).write_text(
                (repo / target_rel).read_text(encoding="utf-8") + "\nBody note.\n",
                encoding="utf-8",
            )
            log_rel = f".aw/records/meta/{target_id}.jsonl"
            (repo / log_rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / log_rel).write_text("{corrupt json line\n", encoding="utf-8")
            _git(repo, "add", target_rel, log_rel)
    else:
        target_rel = paths["backlog_done"]
        target_id = "gb0001"
        _git(repo, "mv", paths["backlog_open"], target_rel)
        if corrupt_mode == "invalid_utf8_md":
            (repo / target_rel).write_bytes(b"\xff\xfe\x00\x00unparseable-record")
            _git(repo, "add", target_rel)
        else:
            # Stage a non-blocking close (which would otherwise pass) alongside a corrupt log.
            (repo / target_rel).write_text(
                _backlog_text(id6=target_id, status="done", blocks_release=None),
                encoding="utf-8",
            )
            log_rel = f".aw/records/meta/{target_id}.jsonl"
            (repo / log_rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / log_rel).write_text("{corrupt json line\n", encoding="utf-8")
            _git(repo, "add", target_rel, log_rel)

    rc, out, err = _run_cli_in_repo(repo, [gate_cmd])
    combined = f"{out}\n{err}"
    assert rc != 0, (
        f"{gate_cmd} ({corrupt_mode}) failed OPEN (exit 0) on unparseable staged record; "
        f"stdout={out!r} stderr={err!r}"
    )
    assert (
        target_rel in combined or target_id in combined
    ), f"{gate_cmd} ({corrupt_mode}) refusal did not name {target_rel!r} or {target_id!r}: {combined!r}"
    assert "corrupt" in combined.lower() or "unparseable" in combined.lower(), (
        f"{gate_cmd} ({corrupt_mode}) refusal did not report an unparseable/corrupt record: "
        f"{combined!r}"
    )

    # Verify corrupt staged blob left no valid rev_log_states entry for target_id.
    db_path = repo / ".aw" / "state" / "index.db"
    if db_path.is_file() and corrupt_mode == "corrupt_meta_log":
        conn = sqlite3.connect(str(db_path))
        try:
            rows = conn.execute(
                "SELECT id6 FROM rev_log_states WHERE id6 = ?", (target_id,)
            ).fetchall()
        finally:
            conn.close()
        assert rows == [], f"corrupt log was cached in rev_log_states: {rows}"


# --------------------------------------------------------------------------------------
# E-14: Offline setter and gate proof (AC-12, no host binaries, sockets disabled)
# --------------------------------------------------------------------------------------


def _offline_env(tmp_path: Path) -> Tuple[Dict[str, str], Path]:
    bin_dir = tmp_path / "stripped_bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    git_bin = shutil.which("git")
    assert git_bin is not None, "git executable required to build stripped PATH"
    git_link = bin_dir / Path(git_bin).name
    if not git_link.exists():
        os.symlink(git_bin, git_link)

    stripped_path = str(bin_dir)
    for host_bin in _HOST_BINARIES:
        assert shutil.which(host_bin, path=stripped_path) is None

    sc_dir = tmp_path / "offline_site"
    sc_dir.mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "sitecustomize_loaded.txt"
    (sc_dir / "sitecustomize.py").write_text(
        "import pathlib, socket\n"
        f"pathlib.Path({str(marker)!r}).write_text('loaded', encoding='utf-8')\n"
        "_OrigSocket = socket.socket\n"
        "class _BlockedSocket(_OrigSocket):\n"
        "    def __new__(cls, *args, **kwargs):\n"
        "        raise RuntimeError('network disabled by offline gate test')\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        raise RuntimeError('network disabled by offline gate test')\n"
        "def _blocked_conn(*args, **kwargs):\n"
        "    raise RuntimeError('network disabled by offline gate test')\n"
        "socket.socket = _BlockedSocket\n"
        "socket.create_connection = _blocked_conn\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PATH"] = stripped_path
    existing_pp = env.get("PYTHONPATH", "")
    pp_parts = [str(sc_dir), str(_REPO_ROOT)]
    if existing_pp:
        pp_parts.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    env["AW_NONINTERACTIVE"] = "1"
    env["AW_NO_REEXEC"] = "1"
    return env, marker


def _run_offline_aw(
    tmp_path: Path, repo: Path, *aw_args: str
) -> subprocess.CompletedProcess[str]:
    env, marker = _offline_env(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", *aw_args],
        cwd=str(repo),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert marker.is_file() and marker.read_text(encoding="utf-8") == "loaded"
    return proc


def test_offline_ipd_set_to_review_no_host_binaries_no_network(
    tmp_path: Path, _base_template: Tuple[Path, Dict[str, str]]
) -> None:
    """aw ipd set to-review <plan> exits 0 with host binaries absent and sockets blocked."""
    repo, paths = _clone_template(_base_template, tmp_path, "offline_setter")
    proc = _run_offline_aw(
        tmp_path,
        repo,
        "ipd",
        "set",
        "to-review",
        "gp0001",
        "--message",
        "offline review handoff",
        "--yes",
        "--no-commit",
        "--dir",
        str(repo),
    )
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"
    updated = (repo / paths["setter_plan"]).read_text(encoding="utf-8")
    assert "- Status: to-review" in updated


def test_offline_ipd_executed_gate_no_host_binaries_no_network(
    tmp_path: Path, _base_template: Tuple[Path, Dict[str, str]]
) -> None:
    """aw ipd-executed-gate exits 0 with host binaries absent and sockets blocked."""
    repo, paths = _clone_template(_base_template, tmp_path, "offline_gate")
    # Stage a benign body edit on a pending plan so the gate runs read_at against :0: and HEAD.
    plan_p = repo / paths["setter_plan"]
    plan_p.write_text(
        plan_p.read_text(encoding="utf-8") + "\nBenign staged body note.\n",
        encoding="utf-8",
    )
    _git(repo, "add", paths["setter_plan"])

    proc = _run_offline_aw(tmp_path, repo, "ipd-executed-gate")
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"

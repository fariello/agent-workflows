"""Tests for CI health checkup module and CLI.

Covers cases (a) through (h) specified in IPD n7xlhm:
(a) passing, failing, and unknown CI shapes
(b) commits-since computed from first-parent history
(c) interval: not due below N, due at N, disabled at 0
(d) concurrent checkups: race condition handled via platform_lock
(e) aw attention and aw doctor read saved record without executing gh
(f) raising checkup records checkup-failed without aborting run
(g) record written at primary checkout when run in linked worktree
(h) custom workflow and branch reach gh argv
"""

from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path
import subprocess

import pytest

from agent_workflows import checkup
from agent_workflows import config as aw_config
from agent_workflows import doctor


def _run_git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return res.stdout.strip()


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "test@example.com")
    _run_git(path, "config", "user.name", "Test User")
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (path / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-qm", "Initial commit")
    return path


def _create_gh_stub(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub_path = bin_dir / "gh"
    log_path = tmp_path / "gh_calls.log"
    resp_path = tmp_path / "gh_response.json"

    stub_code = f"""#!/usr/bin/env python3
import json
import os
import sys
import time

log_file = {repr(str(log_path))}
resp_file = {repr(str(resp_path))}

call_entry = {{"argv": sys.argv[1:], "cwd": os.getcwd()}}
with open(log_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(call_entry) + "\\n")

if os.path.exists(resp_file):
    with open(resp_file, "r", encoding="utf-8") as f:
        resp = json.load(f)
    if "sleep" in resp:
        time.sleep(resp["sleep"])
    if resp.get("stderr"):
        sys.stderr.write(resp["stderr"])
    if resp.get("stdout") is not None:
        sys.stdout.write(resp["stdout"])
    sys.exit(resp.get("exit_code", 0))

# Default response: empty list
sys.stdout.write("[]\\n")
sys.exit(0)
"""
    stub_path.write_text(stub_code, encoding="utf-8")
    stub_path.chmod(0o755)
    return stub_path, log_path, resp_path


@pytest.fixture
def gh_env(tmp_path, monkeypatch):
    stub_path, log_path, resp_path = _create_gh_stub(tmp_path)
    old_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{stub_path.parent}:{old_path}")
    return {"stub": stub_path, "log": log_path, "resp": resp_path}


# ----------------------------------------------------------------------------------
# (a) CI Shapes: passing, failing, and unknown shapes
# ----------------------------------------------------------------------------------


def test_ci_shape_passing(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo, "rev-parse", "HEAD")

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        }
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.PASSING
    assert info.latest_run_commit == head_sha
    assert info.last_pass_commit == head_sha
    assert info.commits_since_pass == 0
    assert info.reason is None


def test_ci_shape_failing_with_prior_pass(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    pass_sha = _run_git(repo, "rev-parse", "HEAD")

    (repo / "file2.txt").write_text("commit 2\n", encoding="utf-8")
    _run_git(repo, "add", "file2.txt")
    _run_git(repo, "commit", "-qm", "Second commit")
    fail_sha = _run_git(repo, "rev-parse", "HEAD")

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": fail_sha,
                            "conclusion": "failure",
                            "status": "completed",
                            "createdAt": "2026-10-13T14:00:00Z",
                        },
                        {
                            "headSha": pass_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        },
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.FAILING
    assert info.latest_run_commit == fail_sha
    assert info.last_pass_commit == pass_sha
    assert info.commits_since_pass == 1


def test_ci_shape_unknown_no_gh(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    # Point PATH to an empty dir so gh is missing
    empty_bin = tmp_path / "empty_bin"
    empty_bin.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PATH", str(empty_bin))

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "command not found" in (info.reason or "").lower()


def test_ci_shape_unknown_nonzero_exit(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    gh_env["resp"].write_text(
        json.dumps(
            {
                "stderr": "gh: authentication failed",
                "exit_code": 1,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "authentication failed" in (info.reason or "")


def test_ci_shape_unknown_malformed_json(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": "Not JSON at all! 502 Bad Gateway",
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "malformed json" in (info.reason or "").lower()


def test_ci_shape_unknown_timeout(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    gh_env["resp"].write_text(
        json.dumps(
            {
                "sleep": 2.0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo, timeout_sec=0.1)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "timed out" in (info.reason or "")


def test_ci_shape_commit_not_in_local_history(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    foreign_sha = "0123456789abcdef0123456789abcdef01234567"

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": foreign_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        }
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "not in local history" in (info.reason or "")


def test_ci_shape_widen_limit_when_no_pass_in_page_1(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo, "rev-parse", "HEAD")

    # In checkup.py, when initial query returns 30 failing runs, it queries again with limit 100
    # Let's verify widening by inspecting the stub's call log
    failing_runs = [
        {
            "headSha": head_sha,
            "conclusion": "failure",
            "status": "completed",
            "createdAt": "2026-10-13T12:00:00Z",
        }
        for _ in range(30)
    ]

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(failing_runs),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.UNKNOWN
    assert "no passing run in the last" in (info.reason or "")

    calls = [
        json.loads(line)
        for line in gh_env["log"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    # We should have seen 2 calls: first with limit 30, second with limit 100
    assert len(calls) == 2
    assert "--limit" in calls[0]["argv"]
    idx0 = calls[0]["argv"].index("--limit")
    assert calls[0]["argv"][idx0 + 1] == "30"
    idx1 = calls[1]["argv"].index("--limit")
    assert calls[1]["argv"][idx1 + 1] == "100"


# ----------------------------------------------------------------------------------
# (b) Commits-since calculation via first-parent git rev-list
# ----------------------------------------------------------------------------------


def test_commits_since_first_parent(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    pass_sha = _run_git(repo, "rev-parse", "HEAD")

    # Create a side branch with 3 commits
    _run_git(repo, "checkout", "-q", "-b", "feature")
    for i in range(3):
        (repo / f"side_{i}.txt").write_text(f"side {i}\n", encoding="utf-8")
        _run_git(repo, "add", f"side_{i}.txt")
        _run_git(repo, "commit", "-qm", f"side commit {i}")

    # Switch back to main and merge feature with --no-ff
    _run_git(repo, "checkout", "-q", "main")
    (repo / "main_1.txt").write_text("main 1\n", encoding="utf-8")
    _run_git(repo, "add", "main_1.txt")
    _run_git(repo, "commit", "-qm", "main commit 1")

    _run_git(repo, "merge", "--no-ff", "-qm", "Merge feature into main", "feature")

    (repo / "main_2.txt").write_text("main 2\n", encoding="utf-8")
    _run_git(repo, "add", "main_2.txt")
    _run_git(repo, "commit", "-qm", "main commit 2")
    head_sha = _run_git(repo, "rev-parse", "HEAD")

    # First parent history from pass_sha to main:
    # pass_sha -> main commit 1 (1) -> merge commit (2) -> main commit 2 (3) = 3 first-parent commits.
    # Total commits would be 3 + 3 (side branch) = 6.
    # First-parent count must be 3!
    count = checkup.count_first_parent_commits(pass_sha, "main", repo)
    assert count == 3

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "conclusion": "failure",
                            "status": "completed",
                            "createdAt": "2026-10-13T15:00:00Z",
                        },
                        {
                            "headSha": pass_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        },
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    info = checkup.read_ci_status(repo)
    assert info.health == checkup.CiHealth.FAILING
    assert info.commits_since_pass == 3


# ----------------------------------------------------------------------------------
# (c) Interval check: not due below N, due at N, disabled at 0
# ----------------------------------------------------------------------------------


def test_interval_check(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    c0 = _run_git(repo, "rev-parse", "HEAD")

    # Record at c0
    rec = {
        "version": 1,
        "recorded_at": "2026-10-13T12:00:00Z",
        "commit": c0,
        "branch": "main",
        "ci": {
            "health": "PASSING",
            "latest_run_commit": c0,
            "last_pass_commit": c0,
            "commits_since_pass": 0,
            "last_pass_date": "2026-10-13",
        },
        "slow_checks": {"stale_spec_anchors": 0},
    }
    checkup.save_checkup_record(rec, repo)

    # 1. 0 commits ahead, interval 5: not due
    assert not checkup.is_checkup_due(repo, interval=5, branch="main")

    # 2. Add 4 commits
    for i in range(4):
        (repo / f"f_{i}.txt").write_text(f"{i}\n", encoding="utf-8")
        _run_git(repo, "add", f"f_{i}.txt")
        _run_git(repo, "commit", "-qm", f"c{i}")

    # 4 commits ahead, interval 5: not due
    assert not checkup.is_checkup_due(repo, interval=5, branch="main")

    # 3. Add 5th commit (now 5 commits ahead)
    (repo / "f_4.txt").write_text("4\n", encoding="utf-8")
    _run_git(repo, "add", "f_4.txt")
    _run_git(repo, "commit", "-qm", "c4")

    # 5 commits ahead, interval 5: DUE
    assert checkup.is_checkup_due(repo, interval=5, branch="main")

    # 4. Interval 0 disables periodic checkup
    assert not checkup.is_checkup_due(repo, interval=0, branch="main")

    # 5. Missing record: DUE when interval > 0, False when interval == 0
    rec_path = checkup.checkup_record_path(repo)
    rec_path.unlink()
    assert checkup.is_checkup_due(repo, interval=5, branch="main")
    assert not checkup.is_checkup_due(repo, interval=0, branch="main")


def test_config_interval_fallbacks(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    aw_cfg = repo / ".aw" / "config"
    aw_cfg.mkdir(parents=True, exist_ok=True)

    # Missing config: defaults
    assert aw_config.ci_checkup_interval_commits(repo) == 100
    assert aw_config.ci_checkup_workflow(repo) == "tests.yml"
    assert aw_config.ci_checkup_branch(repo) == "main"

    # Valid config
    (aw_cfg / "project.json").write_text(
        json.dumps(
            {
                "ci_checkup_interval_commits": 50,
                "ci_checkup_workflow": "custom.yml",
                "ci_checkup_branch": "trunk",
            }
        ),
        encoding="utf-8",
    )
    assert aw_config.ci_checkup_interval_commits(repo) == 50
    assert aw_config.ci_checkup_workflow(repo) == "custom.yml"
    assert aw_config.ci_checkup_branch(repo) == "trunk"

    # Zero disables
    (aw_cfg / "project.json").write_text(
        json.dumps({"ci_checkup_interval_commits": 0}),
        encoding="utf-8",
    )
    assert aw_config.ci_checkup_interval_commits(repo) == 0

    # Negative falls back to default 100 with warning
    warnings = []
    (aw_cfg / "project.json").write_text(
        json.dumps({"ci_checkup_interval_commits": -10}),
        encoding="utf-8",
    )
    assert aw_config.ci_checkup_interval_commits(repo, warn=warnings.append) == 100
    assert len(warnings) == 1
    assert "is -10, which is negative" in warnings[0]

    # Non-integer falls back to default 100 with warning
    warnings.clear()
    (aw_cfg / "project.json").write_text(
        json.dumps({"ci_checkup_interval_commits": "invalid"}),
        encoding="utf-8",
    )
    assert aw_config.ci_checkup_interval_commits(repo, warn=warnings.append) == 100
    assert len(warnings) == 1
    assert "is not an integer" in warnings[0]


# ----------------------------------------------------------------------------------
# (d) Concurrency: two processes racing the lock
# ----------------------------------------------------------------------------------


def _hold_lock_and_signal(lock_path: Path, started_event, release_event):
    from agent_workflows import platform_lock

    with platform_lock.acquire(lock_path, blocking=False):
        started_event.set()
        release_event.wait(timeout=5.0)


def test_concurrency_lock_busy(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    lock_file = checkup.checkup_lock_path(repo)
    events_file = repo / "events.jsonl"

    ctx = multiprocessing.get_context("spawn")
    started_event = ctx.Event()
    release_event = ctx.Event()

    p = ctx.Process(
        target=_hold_lock_and_signal,
        args=(lock_file, started_event, release_event),
    )
    p.start()
    try:
        assert started_event.wait(timeout=5.0), "Holder process did not start"

        # Now run_start_checkup in this process while lock is held
        res = checkup.run_start_checkup(
            repo_root=repo,
            run_id="run-peer-test",
            events_path=events_file,
            config={"ci_checkup_interval_commits": 1},
        )
        assert res is not None

        # Check events.jsonl for checkup-skipped-peer
        assert events_file.exists()
        events = [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
        ]
        assert len(events) == 1
        assert events[0]["event"] == "checkup-skipped-peer"
        assert events[0]["run_id"] == "run-peer-test"
    finally:
        release_event.set()
        p.join(timeout=3.0)


# ----------------------------------------------------------------------------------
# (e) aw attention and aw doctor read saved record and make zero gh calls
# ----------------------------------------------------------------------------------


def test_attention_and_doctor_read_record_zero_gh_calls(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo, "rev-parse", "HEAD")

    # Write a saved record
    rec = {
        "version": 1,
        "recorded_at": "2026-10-13T12:00:00Z",
        "commit": head_sha,
        "branch": "main",
        "ci": {
            "health": "FAILING",
            "latest_run_commit": head_sha,
            "last_pass_commit": "0123456789abcdef0123456789abcdef01234567",
            "commits_since_pass": 42,
            "last_pass_date": "2026-10-12",
        },
        "slow_checks": {"check.spec-anchor-stale": 2},
    }
    checkup.save_checkup_record(rec, repo)

    # 1. Test attention
    import argparse
    from io import StringIO
    from unittest.mock import patch
    from agent_workflows import attention

    with patch("sys.stdout", new_callable=StringIO) as fake_out:
        args = argparse.Namespace(
            dir=str(repo),
            repo=repo,
            format="human",
            agent=False,
            all=False,
            check=False,
            status=None,
            type=None,
            priority=None,
            blocking=None,
            readiness=None,
            run_status=None,
            selectors=None,
            long=False,
            no_color=True,
            order_by=None,
        )
        attention.run(args)
        board_rendered = fake_out.getvalue()
        assert "Checkup" in board_rendered
        assert "CI FAILING" in board_rendered
        assert "42 commits" in board_rendered

    with patch("sys.stdout", new_callable=StringIO) as fake_out:
        args = argparse.Namespace(
            dir=str(repo),
            repo=repo,
            format="agent",
            agent=True,
            all=False,
            check=False,
            status=None,
            type=None,
            priority=None,
            blocking=None,
            readiness=None,
            run_status=None,
            selectors=None,
            long=False,
            no_color=True,
            order_by=None,
        )
        attention.run(args)
        agent_out = json.loads(fake_out.getvalue())
        ev_list = agent_out.get("evidence", [])
        assert any(
            (isinstance(ev, str) and "checkup" in ev)
            or (isinstance(ev, dict) and ev.get("key") == "checkup")
            for ev in ev_list
        )

    # 2. Test doctor
    doc_res = doctor.inspect_repo(repo)
    doc_evidence = [ev for ev in doc_res.evidence if ev.key == "checkup"]
    assert len(doc_evidence) == 1
    assert "CI FAILING" in doc_evidence[0].value["summary"]

    # Assert gh stub was NEVER called
    if gh_env["log"].exists():
        calls = [
            line
            for line in gh_env["log"].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(calls) == 0, f"Expected 0 gh calls, found {len(calls)}"


# ----------------------------------------------------------------------------------
# (f) Raising checkup records checkup-failed without aborting run
# ----------------------------------------------------------------------------------


def test_raising_checkup_records_checkup_failed(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    events_file = repo / "events.jsonl"

    def _boom(*args, **kwargs):
        raise RuntimeError("Network boom!")

    monkeypatch.setattr(checkup, "perform_checkup", _boom)

    # Should not raise
    res = checkup.run_start_checkup(
        repo_root=repo,
        run_id="run-fail-test",
        events_path=events_file,
        config={"ci_checkup_interval_commits": 1},
    )
    assert res is None

    assert events_file.exists()
    events = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 1
    assert events[0]["event"] == "checkup-failed"
    assert "Network boom!" in events[0]["reason"]


# ----------------------------------------------------------------------------------
# (g) Record written to primary checkout from linked worktree
# ----------------------------------------------------------------------------------


def test_record_written_to_primary_checkout_from_linked_worktree(tmp_path, gh_env):
    primary = _init_repo(tmp_path / "primary")
    head_sha = _run_git(primary, "rev-parse", "HEAD")

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        }
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    lane_dir = tmp_path / "lane_wt"
    _run_git(
        primary, "worktree", "add", "-q", "-b", "aw/lane/test", str(lane_dir), "HEAD"
    )

    # Perform checkup with repo_root = lane_dir
    res = checkup.perform_checkup(lane_dir)
    assert res["ci"]["health"] == "PASSING"

    # Assert record is written to primary checkout
    primary_rec = primary / ".aw" / "state" / "checkup" / "last.json"
    lane_rec = lane_dir / ".aw" / "state" / "checkup" / "last.json"

    assert primary_rec.exists(), "Record should exist in primary checkout"
    assert not lane_rec.exists(), "Record should NOT exist in lane checkout"

    # Reading checkup record from lane should resolve to primary checkout
    read_rec = checkup.read_checkup_record(lane_dir)
    assert read_rec is not None
    assert read_rec["commit"] == head_sha


# ----------------------------------------------------------------------------------
# (h) ci_checkup_workflow and ci_checkup_branch reach gh argv
# ----------------------------------------------------------------------------------


def test_custom_workflow_and_branch_reach_gh_argv(tmp_path, gh_env):
    repo = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo, "rev-parse", "HEAD")

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "ci_checkup_workflow": "custom-ci.yml",
                "ci_checkup_branch": "dev-branch",
            }
        ),
        encoding="utf-8",
    )

    gh_env["resp"].write_text(
        json.dumps(
            {
                "stdout": json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "conclusion": "success",
                            "status": "completed",
                            "createdAt": "2026-10-13T12:00:00Z",
                        }
                    ]
                ),
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )

    checkup.perform_checkup(repo)

    assert gh_env["log"].exists()
    calls = [
        json.loads(line)
        for line in gh_env["log"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(calls) >= 1
    argv = calls[0]["argv"]

    assert "--workflow" in argv
    wf_idx = argv.index("--workflow")
    assert argv[wf_idx + 1] == "custom-ci.yml"

    assert "--branch" in argv
    br_idx = argv.index("--branch")
    assert argv[br_idx + 1] == "dev-branch"

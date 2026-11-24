"""Behavioral tests for agent_workflows.hooks.prepush_fast_forward_gate."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Tuple

import yaml

from agent_workflows.hooks import prepush_fast_forward_gate as gate


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def _init_remote_and_two_clones(tmp_path: Path) -> Tuple[Path, Path, Path]:
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(remote))

    clone_a = tmp_path / "clone_a"
    _git(tmp_path, "clone", str(remote), str(clone_a))
    _git(clone_a, "config", "user.name", "Test User")
    _git(clone_a, "config", "user.email", "test@example.com")
    (clone_a / "README.md").write_text("initial\n", encoding="utf-8")
    _git(clone_a, "add", "README.md")
    _git(clone_a, "commit", "-m", "initial")
    _git(clone_a, "push", "-u", "origin", "main")

    clone_b = tmp_path / "clone_b"
    _git(tmp_path, "clone", str(remote), str(clone_b))
    _git(clone_b, "config", "user.name", "Test User")
    _git(clone_b, "config", "user.email", "test@example.com")
    return remote, clone_a, clone_b


def test_fast_forward_ahead_of_remote_passes(tmp_path: Path) -> None:
    _remote, clone_a, _clone_b = _init_remote_and_two_clones(tmp_path)
    (clone_a / "a.txt").write_text("new\n", encoding="utf-8")
    _git(clone_a, "add", "a.txt")
    _git(clone_a, "commit", "-m", "ahead")
    local_sha = _git(clone_a, "rev-parse", "HEAD")

    rc, msgs = gate.check(
        clone_a,
        env={
            "PRE_COMMIT_REMOTE_NAME": "origin",
            "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/main",
            "PRE_COMMIT_TO_REF": local_sha,
        },
    )
    assert rc == 0
    assert msgs == []


def test_unfetched_remote_commit_refuses_with_fetch_first(tmp_path: Path) -> None:
    _remote, clone_a, clone_b = _init_remote_and_two_clones(tmp_path)
    # Peer pushes a new commit that clone_a has NOT fetched.
    (clone_b / "peer.txt").write_text("from peer\n", encoding="utf-8")
    _git(clone_b, "add", "peer.txt")
    _git(clone_b, "commit", "-m", "peer commit")
    _git(clone_b, "push", "origin", "main")
    peer_sha = _git(clone_b, "rev-parse", "HEAD")

    # clone_a makes its own commit and tries to push without fetching.
    (clone_a / "local.txt").write_text("local\n", encoding="utf-8")
    _git(clone_a, "add", "local.txt")
    _git(clone_a, "commit", "-m", "local commit")
    local_sha = _git(clone_a, "rev-parse", "HEAD")

    rc, msgs = gate.check(
        clone_a,
        env={
            "PRE_COMMIT_REMOTE_NAME": "origin",
            "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/main",
            "PRE_COMMIT_TO_REF": local_sha,
        },
    )
    assert rc == 1
    assert len(msgs) == 1
    assert "fetch first" in msgs[0]
    assert peer_sha[:12] in msgs[0]


def test_fetched_but_diverged_remote_refuses_and_env_override_allows(
    tmp_path: Path,
) -> None:
    _remote, clone_a, clone_b = _init_remote_and_two_clones(tmp_path)
    (clone_b / "peer.txt").write_text("from peer\n", encoding="utf-8")
    _git(clone_b, "add", "peer.txt")
    _git(clone_b, "commit", "-m", "peer commit")
    _git(clone_b, "push", "origin", "main")
    peer_sha = _git(clone_b, "rev-parse", "HEAD")

    (clone_a / "local.txt").write_text("local\n", encoding="utf-8")
    _git(clone_a, "add", "local.txt")
    _git(clone_a, "commit", "-m", "local commit")
    _git(clone_a, "fetch", "origin")
    local_sha = _git(clone_a, "rev-parse", "HEAD")

    env = {
        "PRE_COMMIT_REMOTE_NAME": "origin",
        "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/main",
        "PRE_COMMIT_TO_REF": local_sha,
    }
    rc, msgs = gate.check(clone_a, env=env)
    assert rc == 1
    assert len(msgs) == 1
    assert "not a fast-forward" in msgs[0]
    assert peer_sha[:12] in msgs[0]
    assert gate.ALLOW_NON_FF_ENV in msgs[0]

    rc_override, msgs_override = gate.check(
        clone_a,
        env={**env, gate.ALLOW_NON_FF_ENV: "1"},
    )
    assert rc_override == 0
    assert msgs_override == []


def test_new_remote_branch_and_branch_deletion_pass(tmp_path: Path) -> None:
    _remote, clone_a, _clone_b = _init_remote_and_two_clones(tmp_path)
    local_sha = _git(clone_a, "rev-parse", "HEAD")

    rc_new, msgs_new = gate.check(
        clone_a,
        env={
            "PRE_COMMIT_REMOTE_NAME": "origin",
            "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/new-feature",
            "PRE_COMMIT_TO_REF": local_sha,
        },
    )
    assert rc_new == 0
    assert msgs_new == []

    rc_del, msgs_del = gate.check(
        clone_a,
        env={
            "PRE_COMMIT_REMOTE_NAME": "origin",
            "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/main",
            "PRE_COMMIT_TO_REF": "0" * 40,
        },
    )
    assert rc_del == 0
    assert msgs_del == []


def test_upstream_fallback_without_pre_commit_env_catches_unfetched_remote(
    tmp_path: Path,
) -> None:
    _remote, clone_a, clone_b = _init_remote_and_two_clones(tmp_path)
    (clone_b / "peer.txt").write_text("from peer\n", encoding="utf-8")
    _git(clone_b, "add", "peer.txt")
    _git(clone_b, "commit", "-m", "peer commit")
    _git(clone_b, "push", "origin", "main")

    (clone_a / "local.txt").write_text("local\n", encoding="utf-8")
    _git(clone_a, "add", "local.txt")
    _git(clone_a, "commit", "-m", "local commit")

    rc, msgs = gate.check(clone_a, env={})
    assert rc == 1
    assert "fetch first" in msgs[0]


def test_unreachable_remote_fails_fast(tmp_path: Path) -> None:
    _remote, clone_a, _clone_b = _init_remote_and_two_clones(tmp_path)
    local_sha = _git(clone_a, "rev-parse", "HEAD")

    rc, msgs = gate.check(
        clone_a,
        env={
            "PRE_COMMIT_REMOTE_NAME": str(tmp_path / "does-not-exist.git"),
            "PRE_COMMIT_REMOTE_BRANCH": "refs/heads/main",
            "PRE_COMMIT_TO_REF": local_sha,
        },
    )
    assert rc == 1
    assert "cannot reach remote" in msgs[0]


def test_precommit_config_runs_fast_gates_before_thorough_suite() -> None:
    cfg_path = Path(__file__).resolve().parents[1] / ".pre-commit-config.yaml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    pre_push_hooks = [
        hook
        for repo in data["repos"]
        for hook in repo["hooks"]
        if "pre-push" in (hook.get("stages") or [])
    ]
    pre_push_ids = [hook["id"] for hook in pre_push_hooks]
    hooks_by_id = {hook["id"]: hook for hook in pre_push_hooks}
    assert pre_push_ids[0] == "prepush-fast-forward-gate"
    assert pre_push_ids.index("attention-gate") < pre_push_ids.index("thorough-suite")
    assert pre_push_ids.index("static-type-gate") < pre_push_ids.index("thorough-suite")
    for fast_id in ("prepush-fast-forward-gate", "attention-gate", "static-type-gate"):
        assert (
            hooks_by_id[fast_id].get("fail_fast") is True
        ), f"{fast_id} must set fail_fast: true so pre-commit does not fall through to thorough-suite"

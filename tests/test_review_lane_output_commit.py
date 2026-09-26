"""Tests for driver-side review output commits in isolated review lanes.

Pins behavior of `runner_shared.commit_review_lane_output`:
- Baseline trailer, clean, and refusing-hook cases (E-01)
- Cross-turn attribution scoping against the shared sweep lane (E-02, E-03)
- Expanded uncollapsed directory paths on untracked trees (E-04)
- Trailing run, item, and committer metadata (E-05)
- End-of-run driver-committed review counting (E-07)
"""

from __future__ import annotations

import pathlib
import subprocess


from agent_workflows import runner_shared, worktree_lease


def _make_repo(root: pathlib.Path) -> pathlib.Path:
    """Create a temporary git repository with user identity and an initial commit.

    Crucially commits a placeholder inside `.aw/records/plans/pending/` so that
    `.aw/` is tracked and `git status --porcelain` does not collapse the entire tree.
    """
    repo = root / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    (pending / "placeholder.txt").write_text("seed", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _make_worktree(
    repo: pathlib.Path, lane_id: str = "rvc001"
) -> tuple[pathlib.Path, worktree_lease.WorktreeHandle]:
    branch = f"aw/lane/{lane_id}"
    subprocess.run(["git", "branch", branch, "HEAD"], cwd=repo, check=True)
    wt = repo.parent / f"wt-{lane_id}"
    subprocess.run(
        ["git", "worktree", "add", "-q", str(wt), branch], cwd=repo, check=True
    )
    handle = worktree_lease.WorktreeHandle(
        lane_id=lane_id, path=wt, branch=branch, base_commit="HEAD"
    )
    return wt, handle


def _install_hook(repo: pathlib.Path, body: str) -> pathlib.Path:
    """Install a hook in the COMMON git dir so worktrees also execute it."""
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(body, encoding="utf-8")
    hook.chmod(0o755)
    return hook


def test_baseline_trailer_case(tmp_path: pathlib.Path) -> None:
    """E-01 case 1: Driver commits uncommitted review output with trailers and subject."""
    repo = _make_repo(tmp_path)
    wt, handle = _make_worktree(repo, "rvc001")
    plan_path = wt / ".aw" / "records" / "plans" / "pending" / "x-rvc001-p.ipd.md"
    plan_path.write_text("plan text", encoding="utf-8")

    sha, paths = runner_shared.commit_review_lane_output(
        repo, handle, "rvc001", host_label="oc", run_id="run-test"
    )
    rev_parse = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True, text=True, check=True
    )
    head_sha = rev_parse.stdout.strip()
    assert sha == head_sha
    assert paths == (".aw/records/plans/pending/x-rvc001-p.ipd.md",)

    # Subject check
    subj = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert subj == "review(oc): record the review of rvc001"

    # Trailers check
    msg = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    trailers_proc = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        input=msg,
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    )
    parsed_trailers = [
        line.strip() for line in trailers_proc.stdout.splitlines() if line.strip()
    ]
    print("Parsed trailers:\n" + trailers_proc.stdout)
    assert "AW-Run: run-test" in parsed_trailers
    assert "AW-Item: rvc001" in parsed_trailers
    assert "AW-Committed-By: driver" in parsed_trailers


def test_baseline_clean_worktree(tmp_path: pathlib.Path) -> None:
    """E-01 case 2: Clean worktree returns (None, ()) and makes no commit."""
    repo = _make_repo(tmp_path)
    wt, handle = _make_worktree(repo, "rvc001")

    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True, text=True, check=True
    ).stdout.strip()

    sha, paths = runner_shared.commit_review_lane_output(
        repo, handle, "rvc001", host_label="oc"
    )
    assert sha is None
    assert paths == ()

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=wt, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert head_before == head_after


def test_baseline_refusing_hook(tmp_path: pathlib.Path) -> None:
    """E-01 case 3: Refusing hook returns (None, (<path>,)) and leaves file uncommitted."""
    repo = _make_repo(tmp_path)
    wt, handle = _make_worktree(repo, "rvc001")

    # Verify that inside the worktree, hooks path points to the COMMON dir
    proc_git_path = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    )
    hooks_rel = proc_git_path.stdout.strip()
    hooks_resolved = (wt / hooks_rel).resolve()
    common_hooks_resolved = (repo / ".git" / "hooks").resolve()
    print(f"git rev-parse --git-path hooks in worktree: {hooks_rel}")
    print(f"resolved worktree hooks path: {hooks_resolved}")
    print(f"common git hooks path: {common_hooks_resolved}")
    assert hooks_resolved == common_hooks_resolved
    assert ".git/worktrees" not in hooks_resolved.as_posix()

    _install_hook(repo, "#!/bin/sh\nexit 1\n")

    plan_path = wt / ".aw" / "records" / "plans" / "pending" / "x-rvc001-p.ipd.md"
    plan_path.write_text("plan text", encoding="utf-8")

    sha, paths = runner_shared.commit_review_lane_output(
        repo, handle, "rvc001", host_label="oc"
    )
    print(f"Refusing hook result: sha={sha}, paths={paths}")
    assert sha is None
    assert paths == (".aw/records/plans/pending/x-rvc001-p.ipd.md",)

    # Verify file is still uncommitted in worktree
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert ".aw/records/plans/pending/x-rvc001-p.ipd.md" in status


def test_cross_turn_attribution_scoping(tmp_path: pathlib.Path) -> None:
    """E-02: Cross-turn attribution scoping against the shared sweep lane."""
    repo = _make_repo(tmp_path)
    wt, handle = _make_worktree(repo, "sweep")
    hook = _install_hook(repo, "#!/bin/sh\nexit 1\n")

    # Turn 1: aaa111 with refusing hook
    plan_a = wt / ".aw" / "records" / "plans" / "pending" / "p-aaa111.ipd.md"
    plan_a.write_text("plan aaa", encoding="utf-8")
    rev_a = wt / ".aw" / "records" / "reviews" / "r-aaa111.review.md"
    rev_a.parent.mkdir(parents=True, exist_ok=True)
    rev_a.write_text("rev aaa", encoding="utf-8")

    sha_a, paths_a = runner_shared.commit_review_lane_output(
        repo, handle, "aaa111", host_label="oc"
    )
    assert sha_a is None

    # Remove the hook so Turn 2 can commit
    hook.unlink()

    # Turn 2: bbb222
    plan_b = wt / ".aw" / "records" / "plans" / "pending" / "p-bbb222.ipd.md"
    plan_b.write_text("plan bbb", encoding="utf-8")
    rev_b = wt / ".aw" / "records" / "reviews" / "r-bbb222.review.md"
    rev_b.write_text("rev bbb", encoding="utf-8")

    all_porcelain_paths = [
        str(plan_a.relative_to(wt)),
        str(rev_a.relative_to(wt)),
        str(plan_b.relative_to(wt)),
        str(rev_b.relative_to(wt)),
    ]
    own_b = runner_shared.classify_review_writes(
        all_porcelain_paths, id6="bbb222"
    ).allowed

    sha_b, paths_b = runner_shared.commit_review_lane_output(
        repo, handle, "bbb222", host_label="oc", own_paths=own_b
    )
    assert sha_b is not None

    show_proc = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    )
    committed_paths = tuple(
        sorted(line.strip() for line in show_proc.stdout.splitlines() if line.strip())
    )
    print("git show --name-only --format= HEAD:\n" + show_proc.stdout)
    expected_paths = tuple(
        sorted([str(plan_b.relative_to(wt)), str(rev_b.relative_to(wt))])
    )
    assert committed_paths == expected_paths


def test_collapsed_directory_untracked_paths(tmp_path: pathlib.Path) -> None:
    """E-04: First-use lane with entirely untracked .aw tree returns actual committed paths."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(cmd, cwd=repo, check=True)
    (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

    wt, handle = _make_worktree(repo, "firstuse")
    plan_path = wt / ".aw" / "records" / "plans" / "pending" / "x-rvc001-p.ipd.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("plan text", encoding="utf-8")

    sha, paths = runner_shared.commit_review_lane_output(
        repo, handle, "rvc001", host_label="oc"
    )
    assert sha is not None
    show_proc = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    )
    committed_from_git = tuple(
        sorted(line.strip() for line in show_proc.stdout.splitlines() if line.strip())
    )
    print(f"returned paths: {paths}")
    print(f"git show paths: {committed_from_git}")
    assert paths == committed_from_git


def test_driver_committed_reviews_helper_and_report() -> None:
    """E-07: driver_committed_reviews scans ANY attempt and report formats count."""
    import io

    # Case 1: item whose attempt 1 carries review_lane_commit and attempt 2 does not -> still reported!
    state_two_attempts = {
        "queue": [
            {
                "id6": "rev001",
                "attempts": [
                    {"attempt": 1, "review_lane_commit": "c0ffee123456"},
                    {"attempt": 2},
                ],
            }
        ]
    }
    assert runner_shared.driver_committed_reviews(state_two_attempts) == ["rev001"]

    buf = io.StringIO()
    lines = runner_shared.report_driver_committed_reviews(
        state_two_attempts, stream=buf
    )
    assert lines == ["1 review(s) had their output committed by the driver: rev001"]
    assert (
        buf.getvalue().strip()
        == "1 review(s) had their output committed by the driver: rev001"
    )

    # Case 2: self-committed review (no review_lane_commit on any attempt)
    state_self_committed = {
        "queue": [
            {
                "id6": "rev002",
                "attempts": [
                    {"attempt": 1, "commit": "feedbeef1234"},
                ],
            }
        ]
    }
    assert runner_shared.driver_committed_reviews(state_self_committed) == []
    buf2 = io.StringIO()
    lines2 = runner_shared.report_driver_committed_reviews(
        state_self_committed, stream=buf2
    )
    assert lines2 == []
    assert buf2.getvalue() == ""

    # Case 3: empty state prints nothing
    state_empty: dict = {}
    assert runner_shared.driver_committed_reviews(state_empty) == []
    buf3 = io.StringIO()
    lines3 = runner_shared.report_driver_committed_reviews(state_empty, stream=buf3)
    assert lines3 == []
    assert buf3.getvalue() == ""

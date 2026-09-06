"""A lifecycle commit refused by a CONCURRENT WRITER must say so, not blame the plan.

Measured 2026-09-06 in run `run-20260906T222302Z-2985274`. Orchestrator `84j8d7` was fully
eligible to retire (all three children `executed` on disk), the transition ran, and its lifecycle
commit was rejected by `pre-commit`::

    no local leaks in tracked files..........................................Failed
    - hook id: local-leaks
    - files were modified by this hook

    No local leaks found.

The hook said it found nothing AND failed. That is not a contradiction in the hook: pre-commit
stashes unstaged changes, runs the hooks, then compares tree state, so a write by ANY concurrent
process during that window is attributed to whichever hook happened to be running. The real writer
was another agent's review run editing an unrelated plan file (confirmed by recovering pre-commit's
stashed patch, which contained that plan's own edits).

`local-leaks` is an innocent bystander here: it is `always_run: true, pass_filenames: false`, it
exits nonzero only on real findings, and its only file write is behind `--fix`, which the hook never
passes. So the fix is NOT in the sanitizer. The defect is that retirement recorded the generic
`finalize-refused`, which reads as "this Set is not retirable" when the truth was "retry in a
moment".

These tests pin the diagnosis, including its refusals to over-claim.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_workflows.ipd_lifecycle import classify_commit_refusal

PRECOMMIT_MODIFIED = (
    "no local leaks in tracked files..........................................Failed\n"
    "- hook id: local-leaks\n"
    "- files were modified by this hook\n\nNo local leaks found.\n"
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.invalid")
    _git(r, "config", "user.name", "T")
    (r / "owned.txt").write_text("owned\n", encoding="utf-8")
    (r / "foreign.txt").write_text("foreign\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    return r


def test_names_a_concurrent_writer_when_a_foreign_path_is_dirty(repo: Path) -> None:
    """The measured case: our staged path is clean, someone else's file is dirty."""
    (repo / "foreign.txt").write_text("edited by a co-worker\n", encoding="utf-8")

    reason = classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"])

    assert reason is not None
    assert "foreign.txt" in reason
    assert "CONCURRENT WRITER" in reason
    # The operator's actual next step must be stated.
    assert "RETRY" in reason
    # And the misleading attribution must be defused explicitly.
    assert "not necessarily the cause" in reason


def test_says_nothing_was_committed_so_the_state_is_safe(repo: Path) -> None:
    (repo / "foreign.txt").write_text("x\n", encoding="utf-8")
    reason = classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"])
    assert reason is not None
    assert "rolled back cleanly" in reason


def test_refuses_to_claim_a_race_when_only_an_owned_path_is_dirty(repo: Path) -> None:
    """A formatter rewriting OUR OWN staged file is not a foreign cause.

    This is the important negative: over-claiming here would tell an operator to retry when the real
    fix is to re-stage the hook's rewrite.
    """
    (repo / "owned.txt").write_text("reformatted by a hook\n", encoding="utf-8")
    assert classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"]) is None


def test_refuses_to_claim_a_race_when_the_tree_is_clean(repo: Path) -> None:
    assert classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"]) is None


def test_returns_none_for_an_unrecognized_failure(repo: Path) -> None:
    """An unrecognized failure must NEVER be dressed up as a benign race (fail closed)."""
    (repo / "foreign.txt").write_text("dirty\n", encoding="utf-8")
    for stderr in (
        "",
        "error: pathspec 'x' did not match any file(s) known to git",
        "Detect hardcoded secrets................................................Failed",
    ):
        assert classify_commit_refusal(repo, stderr, ["owned.txt"]) is None


def test_counts_and_truncates_many_foreign_paths(repo: Path) -> None:
    for i in range(7):
        (repo / f"extra{i}.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add extras")
    for i in range(7):
        (repo / f"extra{i}.txt").write_text("dirty\n", encoding="utf-8")

    reason = classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"])

    assert reason is not None
    assert "7 dirty path(s)" in reason
    assert "+3 more" in reason


def test_ignores_untracked_files(repo: Path) -> None:
    """An untracked scratch file is not a concurrent WRITE to tracked content.

    pre-commit's stash/restore concerns tracked modifications; treating a stray untracked file as a
    race would fire this diagnosis constantly in a normal working tree.
    """
    (repo / "scratch.tmp").write_text("junk\n", encoding="utf-8")
    assert classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["owned.txt"]) is None


def test_resolves_a_rename_to_its_destination(repo: Path) -> None:
    """A lifecycle move stages `orig -> dest`; the dest is what must match the owned set."""
    _git(repo, "mv", "foreign.txt", "moved.txt")
    reason = classify_commit_refusal(repo, PRECOMMIT_MODIFIED, ["moved.txt"])
    assert reason is None, reason


def test_non_git_directory_is_not_reported_as_a_race(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    assert classify_commit_refusal(plain, PRECOMMIT_MODIFIED, ["owned.txt"]) is None

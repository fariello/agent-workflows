"""The lane merge-back conflict reason must name the CONFLICT, not the expected ff-only failure.

mergemsg. Regression tests for a defect measured 2026-09-06 in run
`run-20260906T162533Z-1552446`, where child `ueg5cf` reported its merge-back failure as::

    merge-back conflict: hint: Diverging branches can't be fast-forwarded, you need to either:
    ...
    fatal: Not possible to fast-forward, aborting.

That is the output of the FIRST merge attempt (`--ff-only`), whose failure is the EXPECTED
"main advanced" case and not an error at all. The real cause was a content conflict in ONE
generated file (`.aw/records/plans/INDEX.json`).

ROOT CAUSE, which these tests pin so it cannot silently return: GIT WRITES MERGE CONFLICTS TO
STDOUT. Both runners kept only STDERR from each attempt and reported `(err2 or err)`; because a
conflicting `git merge --no-ff` leaves stderr EMPTY, that expression always fell through to the
ff-only stderr. The conflicted paths sat in the discarded stdout and were never reported.

These tests drive REAL git rather than mocking it, because the bug WAS an incorrect belief about
which stream git writes to; a mock asserting the same wrong belief would have passed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared


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
def diverged_repo(tmp_path: Path) -> Path:
    """A repo whose `main` and `lane` both changed the SAME file: ff-only fails, no-ff conflicts."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")
    (repo / "shared.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")

    _git(repo, "checkout", "-qb", "lane")
    (repo / "shared.txt").write_text("lane side\n", encoding="utf-8")
    _git(repo, "commit", "-qam", "lane change")

    _git(repo, "checkout", "-q", "main")
    (repo / "shared.txt").write_text("main side\n", encoding="utf-8")
    _git(repo, "commit", "-qam", "main change")
    return repo


def test_ff_only_failure_writes_to_stderr_not_stdout(diverged_repo: Path) -> None:
    """The EXPECTED ff-only failure puts its advice on STDERR (this is what used to be reported)."""
    proc = _git(diverged_repo, "merge", "--ff-only", "lane")
    assert proc.returncode != 0
    assert "Not possible to fast-forward" in proc.stderr
    assert "Not possible to fast-forward" not in proc.stdout


def test_conflicting_merge_writes_conflict_to_stdout_and_leaves_stderr_empty(
    diverged_repo: Path,
) -> None:
    """THE ROOT CAUSE: a conflicting merge reports on STDOUT, so a stderr-only reader sees nothing."""
    _git(diverged_repo, "merge", "--ff-only", "lane")
    proc = _git(diverged_repo, "merge", "--no-ff", "--no-edit", "-m", "x", "lane")
    assert proc.returncode != 0
    assert "CONFLICT" in proc.stdout
    # The empty stderr is precisely why `(err2 or err)` fell back to the ff-only text.
    assert proc.stderr.strip() == ""


def test_conflicted_paths_reports_unmerged_files(diverged_repo: Path) -> None:
    _git(diverged_repo, "merge", "--no-ff", "--no-edit", "-m", "x", "lane")
    assert runner_shared.conflicted_paths(diverged_repo) == ["shared.txt"]


def test_conflicted_paths_is_empty_before_any_merge(diverged_repo: Path) -> None:
    """No merge in progress means no unmerged entries: the caller can tell the cases apart."""
    assert runner_shared.conflicted_paths(diverged_repo) == []


def test_conflicted_paths_must_be_read_before_abort(diverged_repo: Path) -> None:
    """Documents WHY the callers capture paths before aborting: the abort clears the state."""
    _git(diverged_repo, "merge", "--no-ff", "--no-edit", "-m", "x", "lane")
    assert runner_shared.conflicted_paths(diverged_repo) == ["shared.txt"]
    _git(diverged_repo, "merge", "--abort")
    assert runner_shared.conflicted_paths(diverged_repo) == []


def test_reason_names_the_conflicted_path_and_omits_ff_only_advice(
    diverged_repo: Path,
) -> None:
    """The end-to-end shape: the reason must carry the PATH and must NOT carry the ff-only advice."""
    ff = _git(diverged_repo, "merge", "--ff-only", "lane")
    merge = _git(diverged_repo, "merge", "--no-ff", "--no-edit", "-m", "x", "lane")
    paths = runner_shared.conflicted_paths(diverged_repo)

    reason = runner_shared.format_merge_conflict_reason(
        diverged_repo,
        merge_stdout=merge.stdout,
        merge_stderr=merge.stderr,
        paths=paths,
    )

    assert "shared.txt" in reason
    assert "CONFLICT" in reason
    # The regression itself: the old code reported THIS instead.
    assert "Not possible to fast-forward" not in reason
    assert "Diverging branches" not in reason
    assert (
        "Not possible to fast-forward" in ff.stderr
    )  # the text really was available to leak


def test_reason_never_falls_back_to_ff_only_stderr() -> None:
    """Even with an empty conflicting-merge output, the ff-only stderr must not be substituted.

    The signature makes this structural (there is no ff-only parameter), so this test pins the
    CONTRACT: the reason is built from the conflicting merge's streams and the paths only.
    """
    reason = runner_shared.format_merge_conflict_reason(
        Path("/nonexistent-repo-path"),
        merge_stdout="",
        merge_stderr="",
        paths=["a.txt"],
    )
    assert "a.txt" in reason
    assert "fast-forward" not in reason


def test_generated_manifest_conflict_says_regenerate_not_merge() -> None:
    """The ueg5cf case exactly: an all-generated conflict must not advise a hand merge."""
    reason = runner_shared.format_merge_conflict_reason(
        Path("/nonexistent-repo-path"),
        merge_stdout="CONFLICT (content): Merge conflict in .aw/records/plans/INDEX.json",
        merge_stderr="",
        paths=[".aw/records/plans/INDEX.json"],
    )
    assert "GENERATED" in reason
    assert "aw index" in reason


def test_mixed_conflict_flags_generated_subset_without_claiming_all() -> None:
    reason = runner_shared.format_merge_conflict_reason(
        Path("/nonexistent-repo-path"),
        merge_stdout="CONFLICT",
        merge_stderr="",
        paths=[".aw/records/plans/INDEX.json", "agent_workflows/oc_runipd.py"],
    )
    assert "aw index" in reason
    assert "every conflicted path" not in reason
    assert "agent_workflows/oc_runipd.py" in reason


def test_generated_manifest_paths_selects_only_manifests() -> None:
    assert runner_shared.generated_manifest_paths(
        [
            ".aw/records/plans/INDEX.json",
            ".aw/records/research/INDEX.md",
            "agent_workflows/cli.py",
            "docs/INDEX.json.md",
        ]
    ) == [".aw/records/plans/INDEX.json", ".aw/records/research/INDEX.md"]


@pytest.mark.parametrize(
    "name",
    ["conflicted_paths", "format_merge_conflict_reason", "generated_manifest_paths"],
)
def test_both_runners_share_one_definition(name: str) -> None:
    """Anti-re-fork (2r306y/818uru): ONE definition, asserted by object identity, not by grep."""
    shared = getattr(runner_shared, name)
    assert getattr(oc_runipd, name) is shared
    assert getattr(agy_runipd, name) is shared
    assert shared.__module__ == "agent_workflows.runner_shared"

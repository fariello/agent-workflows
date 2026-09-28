"""Tests for aw find prompts lane status column and filter (IPD iq3txw)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agent_workflows import cli
from agent_workflows.term import Term


def _make_args(
    repo_root: Path,
    *,
    status: str | None = None,
    id: str | None = None,
    set: str | None = None,
    topic: str | None = None,
    disposition: str | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        dir=str(repo_root),
        id=id,
        set=set,
        status=status,
        topic=topic,
        disposition=disposition,
    )


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    prompts_dir = repo / ".aw" / "records" / "prompts"
    walkthroughs_dir = repo / ".aw" / "records" / "walkthroughs"

    lanes = ["pending", "executed", "reusable", "superseded", "not-executed"]
    for lane in lanes:
        lane_dir = prompts_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        id6 = f"pr{lane[:4]}"
        prompt_file = lane_dir / f"20260927-{id6}-01-{id6}-{lane}-prompt.prompt.md"
        prompt_file.write_text(
            f"<!-- aw-prompt: Kind: research | Id: {id6} | Status: {lane} | Created: 2026-09-27 -->\n"
            f"# {lane.title()} Prompt\n\nPrompt in {lane} lane.\n",
            encoding="utf-8",
        )

    # Divergent prompt in pending lane that carries an explicit - Status: superseded bullet
    div_p = (
        prompts_dir / "pending" / "20260927-prmdiv-01-prmdiv-divergent-status.prompt.md"
    )
    div_p.write_text(
        "<!-- aw-prompt: Kind: research | Id: prmdiv | Status: pending | Created: 2026-09-27 -->\n"
        "# Divergent Prompt\n\n"
        "- Status: superseded\n\n"
        "Prompt body text with explicit diverging bullet.\n",
        encoding="utf-8",
    )

    # Prompt in no lane directory (directly under .aw/records/prompts/)
    no_lane_p = prompts_dir / "20260927-prmnol-01-prmnol-no-lane-prompt.prompt.md"
    no_lane_p.write_text(
        "<!-- aw-prompt: Kind: research | Id: prmnol | Status: pending | Created: 2026-09-27 -->\n"
        "# No Lane Prompt\n\nPrompt sitting directly in prompts root.\n",
        encoding="utf-8",
    )

    # Walkthrough file for generic type non-leakage verification
    walkthroughs_dir.mkdir(parents=True, exist_ok=True)
    wt_p = walkthroughs_dir / "20260927-wt0001-01-wt0001-sample-flow.walkthrough.md"
    wt_p.write_text(
        "# Sample Walkthrough\n\nWalkthrough body without status.\n",
        encoding="utf-8",
    )

    return repo


def test_all_five_lanes_render_status(tmp_repo: Path) -> None:
    """(a) Each of the five lanes renders its own lane word in the status column."""
    term = Term(color=False)
    args = _make_args(tmp_repo)
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)

    path_to_line = dict(zip(paths, lines))
    lanes = ["pending", "executed", "reusable", "superseded", "not-executed"]

    for lane in lanes:
        id6 = f"pr{lane[:4]}"
        expected_rel = f".aw/records/prompts/{lane}/20260927-{id6}-01-{id6}-{lane}-prompt.prompt.md"
        assert (
            expected_rel in path_to_line
        ), f"Missing path for lane {lane}: {expected_rel}"
        line = path_to_line[expected_rel]
        tokens = line.split()
        assert (
            tokens[1] == lane
        ), f"Expected status column '{lane}', got '{tokens[1]}' in line: {line}"


def test_divergent_bullet_status_takes_precedence_over_lane(tmp_repo: Path) -> None:
    """(b) A prompt carrying an explicit - Status: bullet that disagrees with its lane renders the bullet value."""
    term = Term(color=False)
    args = _make_args(tmp_repo)
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)

    div_rel = ".aw/records/prompts/pending/20260927-prmdiv-01-prmdiv-divergent-status.prompt.md"
    path_to_line = dict(zip(paths, lines))
    assert div_rel in path_to_line
    line = path_to_line[div_rel]
    assert "superseded" in line
    # Must NOT report pending from its directory
    tokens = line.split()
    assert tokens[1] == "superseded"


def test_prompt_in_no_lane_renders_dash(tmp_repo: Path) -> None:
    """(c) A prompt in no lane directory still renders '-' rather than raising."""
    term = Term(color=False)
    args = _make_args(tmp_repo)
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)

    no_lane_rel = (
        ".aw/records/prompts/20260927-prmnol-01-prmnol-no-lane-prompt.prompt.md"
    )
    path_to_line = dict(zip(paths, lines))
    assert no_lane_rel in path_to_line
    line = path_to_line[no_lane_rel]
    tokens = line.split()
    assert tokens[1] == "-"


def test_status_filter_matches_each_lane(tmp_repo: Path) -> None:
    """(d) --status <lane> returns exactly the matching rows, covering the filter."""
    term = Term(color=False)

    # pending: only the standard pending prompt (divergent prompt has bullet superseded)
    args = _make_args(tmp_repo, status="pending")
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)
    assert len(paths) == 1
    assert (
        paths[0]
        == ".aw/records/prompts/pending/20260927-prpend-01-prpend-pending-prompt.prompt.md"
    )

    # executed: exactly 1
    args = _make_args(tmp_repo, status="executed")
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)
    assert len(paths) == 1
    assert (
        paths[0]
        == ".aw/records/prompts/executed/20260927-prexec-01-prexec-executed-prompt.prompt.md"
    )

    # reusable: exactly 1
    args = _make_args(tmp_repo, status="reusable")
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)
    assert len(paths) == 1
    assert (
        paths[0]
        == ".aw/records/prompts/reusable/20260927-prreus-01-prreus-reusable-prompt.prompt.md"
    )

    # not-executed: exactly 1
    args = _make_args(tmp_repo, status="not-executed")
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)
    assert len(paths) == 1
    assert (
        paths[0]
        == ".aw/records/prompts/not-executed/20260927-prnot--01-prnot--not-executed-prompt.prompt.md"
    )

    # superseded: matches the superseded-lane prompt AND the divergent prompt with bullet superseded
    args = _make_args(tmp_repo, status="superseded")
    lines, paths, _ = cli._find_type_records(tmp_repo, "prompts", [], args, term)
    assert len(paths) == 2
    assert set(paths) == {
        ".aw/records/prompts/superseded/20260927-prsupe-01-prsupe-superseded-prompt.prompt.md",
        ".aw/records/prompts/pending/20260927-prmdiv-01-prmdiv-divergent-status.prompt.md",
    }


def test_status_filter_case_variant(tmp_repo: Path) -> None:
    """(g) A case-variant --status argument (e.g. PENDING) returns the same rows as lowercase."""
    term = Term(color=False)
    args_lower = _make_args(tmp_repo, status="pending")
    _, paths_lower, _ = cli._find_type_records(
        tmp_repo, "prompts", [], args_lower, term
    )

    args_upper = _make_args(tmp_repo, status="PENDING")
    _, paths_upper, _ = cli._find_type_records(
        tmp_repo, "prompts", [], args_upper, term
    )

    assert paths_lower == paths_upper
    assert len(paths_upper) == 1


def test_walkthroughs_generic_type_column_and_filter_non_leakage(
    tmp_repo: Path,
) -> None:
    """(e) Non-prompts generic type (walkthroughs) renders '-' in status column.
    (f) --status <lane> against walkthroughs returns nothing (filter non-leakage).
    """
    term = Term(color=False)

    # (e) Column rendering: status is '-'
    args_all = _make_args(tmp_repo)
    lines, paths, _ = cli._find_type_records(
        tmp_repo, "walkthroughs", [], args_all, term
    )
    assert len(lines) == 1
    assert (
        paths[0]
        == ".aw/records/walkthroughs/20260927-wt0001-01-wt0001-sample-flow.walkthrough.md"
    )
    tokens = lines[0].split()
    assert tokens[1] == "-"

    # (f) Filter non-leakage: --status pending returns 0 rows
    for lane in ("pending", "executed", "reusable", "superseded", "not-executed"):
        args_filter = _make_args(tmp_repo, status=lane)
        flines, fpaths, _ = cli._find_type_records(
            tmp_repo, "walkthroughs", [], args_filter, term
        )
        assert (
            len(flines) == 0
        ), f"Expected 0 walkthroughs for status '{lane}', got: {flines}"
        assert len(fpaths) == 0

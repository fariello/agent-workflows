"""Tests for layout inventory classification and preflight gate behavior (IPD vv6y7e).

Validates that:
(1) the three single-trigger shapes (.agents/skills, .aw/.gitignore, .aw/setup-repo-needed.md)
    each dry-run cleanly;
(2) a combined shape carrying all three triggers dry-runs cleanly;
(3) an applied migration on the combined shape leaves all three paths present and byte-identical,
    and creates .aw/system/;
(4) direct classify_item assertions for the three paths match expected dispositions;
(5) a negative control with an unknown path (.agents/mystery.txt) still blocks and refuses;
(6) rollback after an applied migration leaves all three paths present.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict

import pytest

from agent_workflows import layout_inventory, layout_migration
from agent_workflows.layout_migration import PreflightGateError


@pytest.fixture(autouse=True)
def isolate_aw_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    aw_home = tmp_path / "isolated_aw_home"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    return aw_home


def _make_git_repo(repo_dir: Path, extra_files: Dict[str, bytes]) -> Path:
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main", str(repo_dir)], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "Test User"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "test@example.com"],
        check=True,
    )

    base_files = {
        ".agents/workflows/VERSION": b"1.0.0\n",
        ".agents/workflows/index.md": b"# Index\n",
        ".agents/plans/README.md": b"# Plans\n",
    }
    all_files = dict(base_files)
    all_files.update(extra_files)
    for rel, content in all_files.items():
        p = repo_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    subprocess.run(
        ["git", "-C", str(repo_dir), "add", "."], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )
    return repo_dir


def test_case_1_single_trigger_shapes_dry_run_cleanly(tmp_path: Path) -> None:
    """Case 1: the three single-trigger shapes each dry-run cleanly."""
    single_triggers = [
        ("skills", {".agents/skills/assess/SKILL.md": b"# Assess Skill\n"}),
        ("gitignore", {".aw/.gitignore": b"# AW gitignore\n"}),
        ("setup_marker", {".aw/setup-repo-needed.md": b"# Setup needed\n"}),
    ]
    for name, extra in single_triggers:
        repo = _make_git_repo(tmp_path / f"repo_single_{name}", extra)
        mgr = layout_migration.MigrationManager(str(repo))
        plan = mgr.execute_migration(dry_run=True, leftover_disposition="remove")
        assert plan.is_valid, f"Expected dry-run to succeed for single trigger {name}"


def test_case_2_combined_shape_dry_runs_cleanly(tmp_path: Path) -> None:
    """Case 2: a combined shape carrying all three triggers dry-runs cleanly."""
    combined_files = {
        ".agents/skills/assess/SKILL.md": b"# Assess Skill\n",
        ".aw/.gitignore": b"# AW gitignore\n",
        ".aw/setup-repo-needed.md": b"# Setup needed\n",
    }
    repo = _make_git_repo(tmp_path / "repo_combined_dry_run", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    plan = mgr.execute_migration(dry_run=True, leftover_disposition="remove")
    assert plan.is_valid, "Expected dry-run to succeed for combined shape"


def test_case_3_applied_migration_preserves_paths_and_creates_aw_system(
    tmp_path: Path,
) -> None:
    """Case 3: applied migration leaves all three paths byte-identical and creates .aw/system/."""
    skills_bytes = b"# Skill Assess Payload\n"
    gitignore_bytes = b"# .aw/.gitignore Payload\n"
    marker_bytes = b"# Setup Marker Payload\n"

    combined_files = {
        ".agents/skills/assess/SKILL.md": skills_bytes,
        ".aw/.gitignore": gitignore_bytes,
        ".aw/setup-repo-needed.md": marker_bytes,
    }
    repo = _make_git_repo(tmp_path / "repo_applied", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    mgr.execute_migration(dry_run=False, leftover_disposition="remove")

    skills_path = repo / ".agents/skills/assess/SKILL.md"
    gitignore_path = repo / ".aw/.gitignore"
    marker_path = repo / ".aw/setup-repo-needed.md"
    system_dir = repo / ".aw/system"

    assert (
        skills_path.exists()
    ), "Expected .agents/skills/assess/SKILL.md to be preserved in place"
    assert (
        skills_path.read_bytes() == skills_bytes
    ), "Expected skills file to be byte-identical"

    assert gitignore_path.exists(), "Expected .aw/.gitignore to be skipped in place"
    assert (
        gitignore_path.read_bytes() == gitignore_bytes
    ), "Expected .aw/.gitignore to be byte-identical"

    assert (
        marker_path.exists()
    ), "Expected .aw/setup-repo-needed.md to be skipped in place"
    assert (
        marker_path.read_bytes() == marker_bytes
    ), "Expected setup marker to be byte-identical"

    assert system_dir.is_dir(), "Expected .aw/system directory to be created"


def test_case_4_direct_classify_item_assertions() -> None:
    """Case 4: direct classify_item assertions for the three paths."""
    skills_res = layout_inventory.classify_item("agents", "skills/assess/SKILL.md")
    assert skills_res == {
        "ownership": "host-adapter-candidate",
        "lifecycle_class": "host-adapter-candidate",
        "expected_destination_class": "host-adapter-in-place",
        "disposition": "preserve",
    }

    # Also verify directory entries yielded by walker
    assert (
        layout_inventory.classify_item("agents", "skills")["disposition"] == "preserve"
    )
    assert (
        layout_inventory.classify_item("agents", "skills/assess")["disposition"]
        == "preserve"
    )

    gitignore_res = layout_inventory.classify_item("partial-aw", ".gitignore")
    assert gitignore_res == {
        "ownership": "system",
        "lifecycle_class": "system",
        "expected_destination_class": "system",
        "disposition": "skip",
    }

    marker_res = layout_inventory.classify_item("partial-aw", "setup-repo-needed.md")
    assert marker_res == {
        "ownership": "system",
        "lifecycle_class": "system",
        "expected_destination_class": "system",
        "disposition": "skip",
    }


def test_case_5_negative_control_unknown_path_blocks_and_refuses(
    tmp_path: Path,
) -> None:
    """Case 5: negative control where an unrelated unknown path still blocks and refuses."""
    mystery_res = layout_inventory.classify_item("agents", "mystery.txt")
    assert mystery_res == {
        "ownership": "unknown",
        "lifecycle_class": "review-required",
        "expected_destination_class": "unknown",
        "disposition": "block-unknown",
    }

    repo = _make_git_repo(
        tmp_path / "repo_mystery", {".agents/mystery.txt": b"whoami\n"}
    )
    mgr = layout_migration.MigrationManager(str(repo))
    with pytest.raises(PreflightGateError) as exc_info:
        mgr.execute_migration(dry_run=True, leftover_disposition="remove")
    assert "agents:mystery.txt has unknown owner/disposition" in str(exc_info.value)


def test_case_6_rollback_leaves_all_three_paths_present(tmp_path: Path) -> None:
    """Case 6: after applied migration, rollback_migration() leaves all three paths present."""
    skills_bytes = b"# Skill Assess Payload\n"
    gitignore_bytes = b"# .aw/.gitignore Payload\n"
    marker_bytes = b"# Setup Marker Payload\n"

    combined_files = {
        ".agents/skills/assess/SKILL.md": skills_bytes,
        ".aw/.gitignore": gitignore_bytes,
        ".aw/setup-repo-needed.md": marker_bytes,
    }
    repo = _make_git_repo(tmp_path / "repo_rollback", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    mgr.execute_migration(dry_run=False, leftover_disposition="remove")

    rb_res = mgr.rollback_migration()
    assert rb_res.get("status") == "rolled_back"

    skills_path = repo / ".agents/skills/assess/SKILL.md"
    gitignore_path = repo / ".aw/.gitignore"
    marker_path = repo / ".aw/setup-repo-needed.md"

    assert (
        skills_path.exists()
    ), "Expected .agents/skills/assess/SKILL.md to remain present after rollback"
    assert (
        skills_path.read_bytes() == skills_bytes
    ), "Expected skills file to be byte-identical after rollback"

    assert (
        gitignore_path.exists()
    ), "Expected .aw/.gitignore to remain present after rollback"
    assert (
        gitignore_path.read_bytes() == gitignore_bytes
    ), "Expected .aw/.gitignore to be byte-identical after rollback"

    assert (
        marker_path.exists()
    ), "Expected .aw/setup-repo-needed.md to remain present after rollback"
    assert (
        marker_path.read_bytes() == marker_bytes
    ), "Expected setup marker to be byte-identical after rollback"

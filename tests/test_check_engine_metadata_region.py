"""Outcome tests for bounding check_engine identity readers to the metadata region.

Covers IPD xvon5j (E-04, E-05, E-07):
- build_dependency_index gives a quoted id6 exactly ONE owner rather than two.
- check_collisions reports no spurious check.id6-collision when a document quotes
  another document's metadata block.
- _read_item_id, _read_blocks_release, and _read_plan_status read only from the
  metadata region and ignore body quotations.
"""

from pathlib import Path
import pytest

from agent_workflows import check_engine as ce


@pytest.fixture
def fixture_dep_tree(tmp_path: Path):
    """Build an isolated fixture tree with a real plan and a quoting research doc."""
    records_dir = tmp_path / ".aw" / "records"
    plans_dir = records_dir / "plans"
    research_dir = records_dir / "research"
    plans_dir.mkdir(parents=True)
    research_dir.mkdir(parents=True)

    plan_file = plans_dir / "20260901-test-01-ddd444-plan.ipd.md"
    plan_file.write_text(
        "# Plan Title\n\n"
        "- Id: ddd444\n"
        "- Status: approved\n"
        "- Set: fxset\n\n"
        "Plan body.\n",
        encoding="utf-8",
    )

    research_file = research_dir / "20260901-test-01-eee555-report.research-report.md"
    research_file.write_text(
        "---\n"
        "id: eee555\n"
        "status: active\n"
        "set: fxset\n"
        "---\n\n"
        "# Research Report\n\n"
        "This document quotes another plan's metadata block:\n"
        "- Id: ddd444\n"
        "- Status: approved\n"
        "- Set: fxset\n",
        encoding="utf-8",
    )

    return tmp_path, plan_file, research_file


def test_build_dependency_index_single_owner_on_quoted_id(fixture_dep_tree):
    """build_dependency_index must record only the declaring plan as owner of ddd444,

    not the quoting research document.
    """
    repo_root, plan_file, _ = fixture_dep_tree
    idx = ce.build_dependency_index(repo_root)

    owners = idx.owners.get("ddd444", [])
    # At pre-change HEAD, owners has length 2 (plans + research).
    # After bounding status_set.read_artifact_record, owners has length 1.
    assert len(owners) == 1, f"Expected 1 owner, got {len(owners)}: {owners}"
    assert owners[0][0] == "plans"
    assert owners[0][2] == str(plan_file)


def test_check_collisions_no_spurious_collision(fixture_dep_tree):
    """check_collisions must not report check.id6-collision between real plan and quoting doc."""
    repo_root, _, _ = fixture_dep_tree
    drift = ce.check_collisions(repo_root)
    collision_findings = [d for d in drift if d.rule == "check.id6-collision"]
    assert (
        len(collision_findings) == 0
    ), f"Expected 0 id6 collisions, got {len(collision_findings)}: {collision_findings}"


def test_bounded_accessors_ignore_body_quotations():
    """Verify that _read_item_id, _read_blocks_release, and _read_plan_status

    ignore metadata-shaped lines in body text beyond the metadata region.
    """
    body_quoted_text = (
        "# Document Header\n\n"
        "- Id: real01\n"
        "- Status: draft\n\n"
        "## Body Section\n\n"
        "Here is a quoted block:\n"
        "- Id: fff666\n"
        "- Blocks-Release: next\n"
        "- Status: reviewed\n"
    )

    assert hasattr(ce, "_read_item_id"), "check_engine must expose _read_item_id"
    assert hasattr(
        ce, "_read_blocks_release"
    ), "check_engine must expose _read_blocks_release"
    assert hasattr(
        ce, "_read_plan_status"
    ), "check_engine must expose _read_plan_status"

    assert ce._read_item_id(body_quoted_text) == "real01"
    assert ce._read_blocks_release(body_quoted_text) is None
    assert ce._read_plan_status(body_quoted_text) == "draft"

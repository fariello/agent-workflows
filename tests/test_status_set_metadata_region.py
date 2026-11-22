"""Outcome tests for bounding status_set identity readers to the metadata region.

Covers IPD xvon5j (E-01, E-02, E-03):
- read_artifact_record reads declared identity, status, and setid only from
  the metadata region.
- Invariant is DECLARED-OR-NOTHING: a body-quoted block must never win,
  and for a YAML-fenced document with no YAML set: fallback, set_id is None
  rather than a quoted body set.
- match_selector does not resolve a quoted id6 to the quoting document.
"""

from pathlib import Path
import pytest

from agent_workflows import status_set
from tests.record_builder import RecordBuilder


@pytest.fixture
def fixture_records_tree(tmp_path: Path):
    """Build an isolated fixture tree with a quoting doc and a real plan."""
    records_dir = tmp_path / ".aw" / "records"
    research_dir = records_dir / "research"
    plans_dir = records_dir / "plans"
    research_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)

    # Fixture 1: YAML fence declaring aaa111 / active / fxset,
    # body quotes bbb222 / approved / otherset.
    quoting_doc = research_dir / "20260901-test-01-aaa111-doc.research-report.md"
    quoting_doc.write_text(
        RecordBuilder().research(
            id6="aaa111",
            status="active",
            set="fxset",
            body="\n# Research Report\n\nThis document quotes another plan's metadata block:\n- Id: bbb222\n- Status: approved\n- Set: otherset\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    # Fixture 2: Real plan declaring bbb222 / approved / otherset in bullet front matter.
    real_plan = plans_dir / "20260901-test-01-bbb222-plan.ipd.md"
    real_plan.write_text(
        RecordBuilder().plan(
            title="Plan Title",
            id6="bbb222",
            status="approved",
            set="otherset",
            body="Plan body.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    return tmp_path, quoting_doc, real_plan


def test_read_artifact_record_yaml_fence_declared_or_nothing(fixture_records_tree):
    """Assert declared-or-nothing: YAML fence answers id6, status, and set_id via artifact_meta (D-6).

    The quoted body block (bbb222 / approved / otherset) must never win.
    """
    repo_root, quoting_doc, _ = fixture_records_tree
    rec = status_set.read_artifact_record(quoting_doc, repo_root)
    assert rec is not None

    # Declared via YAML fallback in metadata region
    assert rec.id6 == "aaa111"
    assert rec.status == "active"
    # Under D-6, set_id comes from artifact_meta (YAML set: fxset), NEVER quoted "otherset"
    assert rec.set_id == "fxset"
    assert rec.set_id != "otherset"


def test_read_artifact_record_bullet_frontmatter_all_fields(tmp_path: Path):
    """Assert all three fields recover when declared in bullet front matter above quotes."""
    records_dir = tmp_path / ".aw" / "records" / "plans"
    records_dir.mkdir(parents=True)

    bullet_doc = records_dir / "20260901-test-01-ccc333-plan.ipd.md"
    bullet_doc.write_text(
        RecordBuilder().plan(
            title="Bullet Plan",
            id6="ccc333",
            status="draft",
            set="bulletset",
            body=(
                "Body quotes another record:\n"
                "- Id: bbb222\n"
                "- Status: approved\n"
                "- Set: otherset\n"
            ),
            raw_fields={"status": "open"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    rec = status_set.read_artifact_record(bullet_doc, tmp_path)
    assert rec is not None
    assert rec.id6 == "ccc333"
    assert rec.status == "open"
    assert rec.set_id == "bulletset"


def test_match_selector_does_not_collide_with_quoted_id(fixture_records_tree):
    """match_selector('bbb222') must return exactly the 1 real plan, not the quoting doc."""
    repo_root, quoting_doc, real_plan = fixture_records_tree
    inv = status_set.inventory_all_artifacts(repo_root)

    matches = status_set.match_selector("bbb222", inv, repo_root)
    assert len(matches) == 1
    assert matches[0].path == real_plan
    assert matches[0].path != quoting_doc

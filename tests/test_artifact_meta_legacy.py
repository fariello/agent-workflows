"""Tests for artifact_meta legacy loader (phase B source, E-11 & E-12).

Validates E-11 (-k "artifact or naming") and E-12 (-k "history or review").
"""

from __future__ import annotations

from pathlib import Path
import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import artifact_naming as naming
from agent_workflows import attention_contract as att


pytestmark = pytest.mark.core


# --------------------------------------------------------------------------------------
# E-11 & V-11: Legacy loader for artifacts and naming (-k "artifact or naming")
# --------------------------------------------------------------------------------------


def test_legacy_naming_precedence_artifact(tmp_path: Path):
    """Legacy timestamp format tested first; slug starting with 6 letters is not parsed as id6."""
    records_root = tmp_path / "records"
    records_root.mkdir()
    specs_dir = records_root / "specs" / "draft"
    specs_dir.mkdir(parents=True)

    # Filename where slug starts with 6 letters 'assess'
    p = specs_dir / "20260818-1525-02-assess-workflow.spec.md"
    p.write_text(
        "# Assess Workflow\n\n- Id: spc001\n- Status: draft\n", encoding="utf-8"
    )

    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["filename_date"] == "20260818"
    assert art_row["order_nn"] == 2
    assert art_row["id6"] == "spc001"
    assert art_row["type"] == "spec"


def test_legacy_attributed_naming_d177_artifact():
    """D177 prompt filename parses ace, model, and type."""
    fn = "20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md"
    attr = naming.parse_attributed(fn)
    assert attr is not None
    assert attr.date == "20261024"
    assert attr.set == "specflow"
    assert attr.nn == "01"
    assert attr.id6 == "hj6b60"
    assert attr.slug == "spec-generation"
    assert attr.ace == "agy"
    assert attr.model == "gemini38flashhigh"
    assert attr.type == "prompt"


def test_legacy_load_plan_artifact(tmp_path: Path):
    """Plan bullet block parses and maps Kind to plan_role."""
    records_root = tmp_path / "records"
    plans_dir = records_root / "plans" / "pending"
    plans_dir.mkdir(parents=True)
    p = plans_dir / "20261102-test-01-pln001-slug.ipd.md"
    content = """# My Plan Title

- Id: pln001
- Status: draft
- Kind: child
- Set: test
- Order: 1
- Item-Dependencies: none
- Work-Kind: feature

## Summary
Plan body text.
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "pln001"
    assert art_row["type"] == "ipd"
    assert art_row["status"] == "draft"
    assert art_row["title"] == "My Plan Title"
    assert art_row["set_id"] == "test"
    assert art_row["order_nn"] == 1


def test_legacy_load_spec_artifact(tmp_path: Path):
    """Spec bullet block parses fields."""
    records_root = tmp_path / "records"
    specs_dir = records_root / "specs" / "approved"
    specs_dir.mkdir(parents=True)
    p = specs_dir / "20261102-spc002-01-spc002-slug.spec.md"
    content = """# Spec Title

- Id: spc002
- Status: to-review
- Blocks-Release: next

## Details
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "spc002"
    assert art_row["type"] == "spec"
    assert art_row["status"] == "to-review"


def test_legacy_load_backlog_artifact(tmp_path: Path):
    """Backlog bullet block maps Work-Kind to work_kind."""
    records_root = tmp_path / "records"
    b_dir = records_root / "backlog" / "open"
    b_dir.mkdir(parents=True)
    p = b_dir / "20261102-bck003-01-bck003-item.backlog.md"
    content = """# Backlog Item

- Id: bck003
- Status: open
- Work-Kind: bug
- Priority: high

## Content
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "bck003"
    assert art_row["type"] == "backlog"
    assert art_row["status"] == "open"


def test_legacy_load_research_artifact(tmp_path: Path):
    """Research YAML front matter maps kind to research_kind."""
    records_root = tmp_path / "records"
    r_dir = records_root / "research" / "active"
    r_dir.mkdir(parents=True)
    p = r_dir / "20261102-res004-01-res004-topic.research.md"
    content = """---
id: res004
kind: investigation
status: active
set: metastore
order: 1
---

# Research Heading

Prose content.
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "res004"
    assert art_row["type"] == "research"
    assert art_row["status"] == "active"
    assert art_row["title"] == "Research Heading"


def test_legacy_load_staged_prompt_with_comment_artifact(tmp_path: Path):
    """Staged prompt comment maps Kind to prompt_kind."""
    records_root = tmp_path / "records"
    p_dir = records_root / "prompts" / "staged"
    p_dir.mkdir(parents=True)
    p = p_dir / "20261102-prm005-01-prm005-slug.prompt.md"
    content = """<!-- aw-managed-prompt: id: prm005 | status: pending | Kind: pipeline -->
# Prompt Task

Execute prompt here.
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "prm005"
    assert art_row["type"] == "prompt"
    assert art_row["status"] == "pending"
    assert art_row["title"] == "Prompt Task"
    assert art_row["fields"]["prompt_kind"] == "pipeline"


def test_legacy_load_aw_prompt_maps_kind_and_created_day(tmp_path: Path):
    """Legacy aw-prompt comment maps Kind/kind to prompt_kind and Created/created to created_day."""
    records_root = tmp_path / "records"
    p_dir = records_root / "prompts" / "pending"
    p_dir.mkdir(parents=True)

    p_title_case = p_dir / "20261119-prset-01-prm011-research.prompt.md"
    p_title_case.write_text(
        "<!-- aw-prompt: Kind: research | Id: prm011 | Set: prset | Status: pending | Created: 2026-11-19 -->\n"
        "# Research Prompt\n\nInvestigate legacy prompt metadata.\n",
        encoding="utf-8",
    )
    art_row, _ = meta.load_legacy_artifact(p_title_case, records_root)
    assert art_row["id6"] == "prm011"
    assert art_row["type"] == "prompt"
    assert art_row["fields"]["prompt_kind"] == "research"
    assert art_row["fields"]["created_day"] == "2026-11-19"
    assert art_row["created_day"] == "2026-11-19"

    p_lower_case = p_dir / "20261119-prset-02-prm012-handoff.prompt.md"
    p_lower_case.write_text(
        "<!-- aw-prompt: kind: session-handoff | id: prm012 | set: prset | status: pending | created: 2026-11-18 -->\n"
        "# Handoff Prompt\n\nContinue task.\n",
        encoding="utf-8",
    )
    art_row_lower, _ = meta.load_legacy_artifact(p_lower_case, records_root)
    assert art_row_lower["id6"] == "prm012"
    assert art_row_lower["type"] == "prompt"
    assert art_row_lower["fields"]["prompt_kind"] == "session-handoff"
    assert art_row_lower["fields"]["created_day"] == "2026-11-18"
    assert art_row_lower["created_day"] == "2026-11-18"


def test_legacy_load_non_prompt_kind_mappings_preserved(tmp_path: Path):
    """Non-prompt records retain ipd Kind->plan_role, backlog Kind->work_kind, and research kind->research_kind."""
    records_root = tmp_path / "records"

    plans_dir = records_root / "plans" / "pending"
    plans_dir.mkdir(parents=True)
    ipd_path = plans_dir / "20261119-pset-01-pln021-sample.ipd.md"
    ipd_path.write_text(
        "# IPD: Sample\n\n- Id: pln021\n- Status: draft\n- Kind: child\n- Created: 2026-11-19\n\n## Goal\nG\n",
        encoding="utf-8",
    )
    ipd_row, _ = meta.load_legacy_artifact(ipd_path, records_root)
    assert ipd_row["fields"]["plan_role"] == "child"
    assert "prompt_kind" not in ipd_row["fields"]
    assert ipd_row["created_day"] is None

    backlog_dir = records_root / "backlog" / "open"
    backlog_dir.mkdir(parents=True)
    bkl_fallback = backlog_dir / "20261119-bkl021-01-bkl021-legacy-kind.backlog.md"
    bkl_fallback.write_text(
        "- Id: bkl021\n- Status: open\n- Kind: bug\n- Priority: medium\n",
        encoding="utf-8",
    )
    bkl_fallback_row, _ = meta.load_legacy_artifact(bkl_fallback, records_root)
    assert bkl_fallback_row["fields"]["work_kind"] == "bug"
    assert bkl_fallback_row["created_day"] is None

    bkl_explicit = backlog_dir / "20261119-bkl022-01-bkl022-work-kind.backlog.md"
    bkl_explicit.write_text(
        "- Id: bkl022\n- Status: open\n- Work-Kind: feature\n- Kind: bug\n- Priority: high\n",
        encoding="utf-8",
    )
    bkl_explicit_row, _ = meta.load_legacy_artifact(bkl_explicit, records_root)
    assert bkl_explicit_row["fields"]["work_kind"] == "feature"
    assert bkl_explicit_row["created_day"] is None

    research_dir = records_root / "research" / "active"
    research_dir.mkdir(parents=True)
    res_path = research_dir / "20261119-rset-01-res021-topic.research.md"
    res_path.write_text(
        "---\nid: res021\ncreated: 20261119\nkind: investigation\nstatus: active\nset: rset\n---\n\n# Research\n",
        encoding="utf-8",
    )
    res_row, _ = meta.load_legacy_artifact(res_path, records_root)
    assert res_row["fields"]["research_kind"] == "investigation"
    assert res_row["fields"]["created"] == "20261119"
    assert res_row["created_day"] is None


def test_legacy_load_staged_prompt_without_comment_artifact(tmp_path: Path):
    """Staged prompt without comment loads correctly."""
    records_root = tmp_path / "records"
    p_dir = records_root / "prompts" / "pending"
    p_dir.mkdir(parents=True)
    p = p_dir / "20261102-test-01-prm006-slug.prompt.md"
    content = """# Bare Prompt

Do something.
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "prm006"
    assert art_row["type"] == "prompt"
    assert art_row["title"] == "Bare Prompt"


def test_legacy_load_release_artifact(tmp_path: Path):
    """Release record loads correctly."""
    records_root = tmp_path / "records"
    rel_dir = records_root / "releases" / "planned"
    rel_dir.mkdir(parents=True)
    p = rel_dir / "20261102-rel007-01-rel007-v2.release.md"
    content = """# Release 2.0.0

- Id: rel007
- Status: planned

## Scope
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "rel007"
    assert art_row["type"] == "release"
    assert art_row["status"] == "planned"


def test_legacy_load_walkthrough_artifact(tmp_path: Path):
    """Walkthrough loads with status None."""
    records_root = tmp_path / "records"
    w_dir = records_root / "walkthroughs"
    w_dir.mkdir(parents=True)
    p = w_dir / "20261102-wlk008-01-wlk008-feature.walkthrough.md"
    content = """# Feature Walkthrough

Narrative walkthrough.
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["id6"] == "wlk008"
    assert art_row["type"] == "walkthrough"
    assert art_row["status"] is None


def test_legacy_unregistered_bullet_artifact(tmp_path: Path):
    """Unregistered legacy bullet does not invalidate record (OQ-02)."""
    records_root = tmp_path / "records"
    p_dir = records_root / "plans" / "pending"
    p_dir.mkdir(parents=True)
    p = p_dir / "20261102-test-01-pln009-slug.ipd.md"
    content = """# Plan With Unregistered Bullets

- Id: pln009
- Status: draft
- Note: custom maintainer note
- Origin: external review
- Custom-Header: abc

## Work
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    assert art_row["valid"] == 1
    assert art_row["id6"] == "pln009"


def test_legacy_multiword_status_artifact(tmp_path: Path):
    """Multi-word status sets artifacts.status to None (OQ-03)."""
    records_root = tmp_path / "records"
    p_dir = records_root / "plans" / "pending"
    p_dir.mkdir(parents=True)
    p = p_dir / "20261102-test-01-pln010-slug.ipd.md"
    content = """# Multi Word Status

- Id: pln010
- Status: draft (waiting on spec)

## Work
"""
    p.write_text(content, encoding="utf-8")
    art_row, _ = meta.load_legacy_artifact(p, records_root)
    # Single token check: 'draft (waiting on spec)' has multiple tokens
    assert art_row["status"] is None
    assert art_row["valid"] == 1


# --------------------------------------------------------------------------------------
# E-12 & V-12: Legacy loader for history and review records (-k "history or review")
# --------------------------------------------------------------------------------------


def test_legacy_three_round_review(tmp_path: Path):
    """Three-round review file yields three reviews rows with verdict only on round 3 (K5a)."""
    records_root = tmp_path / "records"
    rev_dir = records_root / "reviews"
    rev_dir.mkdir(parents=True)
    p = rev_dir / "20261102-rev011-01-sub011-review.review.md"
    content = """# Plan Review

- Subject-Id: sub011
- Verdict: APPROVE
- Reviewer: user1
- Reviewed-At: 2026-10-24
- Readiness: go

## Round 1
Initial feedback.

## Round 2
Revisions requested.

## Round 3
Approved.
"""
    p.write_text(content, encoding="utf-8")
    rf_row, reviews = meta.load_legacy_review(p, records_root)
    assert rf_row["round_count"] == 3
    assert rf_row["subject_id6"] == "sub011"
    assert len(reviews) == 3

    # Rounds 1 and 2 have no verdict, reviewer, or observed_day
    assert reviews[0]["round"] == 1
    assert reviews[0]["verdict"] is None
    assert reviews[0]["reviewer"] is None
    assert reviews[0]["observed_day"] is None

    assert reviews[1]["round"] == 2
    assert reviews[1]["verdict"] is None
    assert reviews[1]["reviewer"] is None
    assert reviews[1]["observed_day"] is None

    # Round 3 has verdict, reviewer, and observed_day
    assert reviews[2]["round"] == 3
    assert reviews[2]["verdict"] == "APPROVE"
    assert reviews[2]["reviewer"] == "user1"
    assert reviews[2]["observed_day"] == "2026-10-24"


def test_legacy_two_review_files_distinct_bindings(tmp_path: Path):
    """Two review files for one subject keep distinct bindings."""
    records_root = tmp_path / "records"
    rev_dir = records_root / "reviews"
    rev_dir.mkdir(parents=True)

    p1 = rev_dir / "20261102-test-01-rf1001-review1.review.md"
    p1.write_text(
        "# Review 1\n\n- Subject-Id: sub012\n\n## Round 1\n", encoding="utf-8"
    )

    p2 = rev_dir / "20261102-test-01-rf2002-review2.review.md"
    p2.write_text(
        "# Review 2\n\n- Subject-Id: sub012\n\n## Round 1\n", encoding="utf-8"
    )

    rf1, _ = meta.load_legacy_review(p1, records_root)
    rf2, _ = meta.load_legacy_review(p2, records_root)

    assert rf1["subject_id6"] == "sub012"
    assert rf2["subject_id6"] == "sub012"
    assert rf1["review_ref"] == "rf1001"
    assert rf2["review_ref"] == "rf2002"
    assert rf1["review_ref"] != rf2["review_ref"]


def test_legacy_history_lines_order_and_last_history_day(tmp_path: Path):
    """History rows returned in file order, and last_history_day equals attention_contract.last_history_at."""
    records_root = tmp_path / "records"
    p_dir = records_root / "plans" / "pending"
    p_dir.mkdir(parents=True)
    p = p_dir / "20261102-test-01-hst013-slug.ipd.md"

    # In disk files, new records are prepended (newest-first in file order)
    history_lines = [
        "- 2026-10-24 approved (aw set): maintainer approved",
        "- 2026-10-22 note: tool-prepended progress",
        "- 2026-10-20 created (aw ipd new): initial creation",
    ]
    content = f"""# Plan With History

- Id: hst013
- Status: approved

## Workflow history
{chr(10).join(history_lines)}

## Other section
"""
    p.write_text(content, encoding="utf-8")
    art_row, hist_rows = meta.load_legacy_artifact(p, records_root)

    # Order maintained
    assert len(hist_rows) == 3
    assert [hr["seq"] for hr in hist_rows] == [1, 2, 3]
    assert [hr["line"] for hr in hist_rows] == history_lines

    # V-12 quotation: legacy last_history_day equals attention_contract.last_history_at
    expected_day = att.last_history_at(history_lines)
    assert art_row["last_history_day"] == expected_day
    assert art_row["last_history_day"] == "2026-10-24"


def test_read_text_strict_two_space_and_tab_whitespace():
    """artifact_meta.read_text separates strict `^- <Key>:` from loose `^-[ \\t]*<Key>:` fields."""
    strict = (
        "# Strict\n\n"
        "- Id: abc123\n"
        "- Status: approved\n"
        "- Set: `myset` (desc)\n"
        "- Blocks-Release: next\n"
        "## Body\n\n- Id: xyz999\n"
    )
    st_strict = meta.read_text(strict, record_type="ipd")
    assert st_strict.id6 == "abc123"
    assert st_strict.status == "approved"
    assert st_strict.legacy_raw_status == "approved"
    assert st_strict.legacy_raw_set == "`myset`"
    assert st_strict.loose_id == "abc123"
    assert st_strict.loose_status == "approved"
    assert st_strict.loose_blocks_release == "next"

    two_spaces = (
        "# Two Spaces\n\n-  Id: def456\n-  Status: draft\n-Blocks-Release: rel001\n"
    )
    st_two = meta.read_text(two_spaces, record_type="ipd")
    assert st_two.id6 == ""
    assert st_two.status is None
    assert st_two.legacy_raw_status is None
    assert st_two.loose_id == "def456"
    assert st_two.loose_status == "draft"
    assert st_two.loose_blocks_release == "rel001"

    tab = "# Tab\n\n-\tId: ghi789\n-\tStatus: reviewed\n-\tBlocks-Release: next\n"
    st_tab = meta.read_text(tab)
    assert st_tab.id6 == ""
    assert st_tab.status is None
    assert st_tab.legacy_raw_status is None
    assert st_tab.loose_id == "ghi789"
    assert st_tab.loose_status == "reviewed"
    assert st_tab.loose_blocks_release == "next"


def test_read_text_yaml_only_and_multiword_status():
    """artifact_meta.read_text supports YAML-only research front matter and preserves multi-word status."""
    yaml_only = (
        "---\n"
        "id: rsh001\n"
        "status: 'reference'\n"
        "set: `rset` (research set)\n"
        "kind: findings\n"
        "---\n\n"
        "# Research Title\n\n"
        "- Id: quoted9\n"
        "- Status: parked\n"
    )
    st_yaml = meta.read_text(yaml_only, record_type="research")
    assert st_yaml.id6 == "rsh001"
    assert st_yaml.status == "reference"
    assert st_yaml.legacy_raw_status == "reference"
    assert st_yaml.legacy_raw_set == "rset"
    assert st_yaml.loose_id is None
    assert st_yaml.loose_status is None
    assert st_yaml.loose_blocks_release is None

    multiword = "# Plan\n\n- Id: pln999\n- Status: EXECUTED (approved by maintainer)\n"
    st_multi = meta.read_text(multiword, record_type="ipd")
    assert st_multi.id6 == "pln999"
    assert st_multi.status is None
    assert st_multi.legacy_raw_status == "EXECUTED (approved by maintainer)"
    assert st_multi.loose_id == "pln999"
    assert st_multi.loose_status is None


_HISTORY_FIXTURE_TEXTS = [
    "# No history\n\n- Id: nhs001\n- Status: draft\n",
    (
        "# Plan\n\n- Id: hst101\n\n## Workflow history\n"
        "- 2026-10-24 approved (aw set): maintainer approved\n"
        "- 2026-10-20 created (aw ipd new): initial creation\n"
        "\n## Goal\n\nBody.\n"
    ),
    (
        "# Wrapped\n\n## Workflow history\n"
        "- 2026-11-02 reviewed (agent): a record whose text\n"
        "  wraps onto a continuation line\n"
        "- not a dated record\n"
        "  continuation of a non-record bullet\n"
        "- 2026-11-01 to-review (agent): second record\n"
        "\n"
        "    an indented quotation after a blank line ends the block\n"
        "- 2026-01-01 not a record because the block already ended\n"
    ),
    (
        "# Column zero prose ends it\n\n## Workflow history   \n"
        "- 2026-09-09 note: only record\n"
        "Prose at column zero.\n"
        "- 2026-09-08 after the block\n"
    ),
    "# CRLF\r\n\r\n## Workflow history\r\n- 2026-08-01 created (x): crlf record\r\n\r\n## Next\r\n",
    "# Empty block\n\n## Workflow history\n\n## Next\n",
]


@pytest.mark.parametrize(
    "text",
    _HISTORY_FIXTURE_TEXTS,
    ids=[
        "no-history",
        "two-records",
        "wrapped-and-quoted",
        "column-zero-prose",
        "crlf",
        "empty-block",
    ],
)
def test_history_records_matches_attention_contract_history_block(text: str):
    """`artifact_meta.history_records` is the one history grammar and answers exactly as the
    `attention_contract` original does, including the newest record and its day."""
    got = meta.history_records(text)
    want = att.history_block(text)
    assert got.records == want.records
    assert got.record_lines == want.record_lines
    assert got.body == want.body
    assert tuple(got) == tuple(want)
    assert meta._newest_history_record(got.records) == att.newest_history_record(
        want.records
    )
    assert meta._last_history_at(got.records) == att.last_history_at(want.records)


def test_last_history_at_copy_matches_original_for_event_dicts():
    events = [
        [{"line": "- 2026-10-24 approved (aw set): x"}, {"line": "- 2026-10-20 y z"}],
        [{"observed_day": "2026-07-01"}, {"at": "2026-07-03T10:00:00Z"}],
        [{"at": "2026-07-03T10:00:00Z"}, {"observed_day": "2026-07-04"}],
        [{"at": "bad"}],
        [],
    ]
    for ev in events:
        assert meta._last_history_at(ev) == att.last_history_at(ev)

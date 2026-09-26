"""Tests for aw find reading records once (IPD qfpnrm)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

import pytest

from agent_workflows import cli
from agent_workflows import plans_index as pi
from agent_workflows.term import Term


PLAN_TEMPLATE = """# IPD: {title}

- Date: 2026-09-20
- Kind: child
- Scope: test
- Status: {status}
- Set: {set_field}
- Order: {order}
- Id: {id6}

## Workflow history
- 2026-09-20 created
"""

RESEARCH_TEMPLATE = """---
id: {id6}
created: 20260920
set: {set_id}
order: {order}
topic: []
model:
kind: findings
status: {status}
outcome: informational
summary: {summary}
consumed-by: []
---
# {title}

Body text for research doc.
"""


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    plans_dir = repo / ".aw" / "records" / "plans"
    research_dir = repo / ".aw" / "records" / "research"

    (plans_dir / "pending").mkdir(parents=True, exist_ok=True)
    (plans_dir / "executed").mkdir(parents=True, exist_ok=True)
    (plans_dir / "executed" / "202608").mkdir(parents=True, exist_ok=True)
    research_dir.mkdir(parents=True, exist_ok=True)

    # 1 & 2: Two sharing a Set (myset)
    p1 = plans_dir / "pending" / "20260920-myset-01-pln001-plan-one.ipd.md"
    p1.write_text(
        PLAN_TEMPLATE.format(
            title="Plan One",
            status="draft",
            set_field="myset (My Set)",
            order="01",
            id6="pln001",
        ),
        encoding="utf-8",
    )
    p2 = plans_dir / "pending" / "20260920-myset-02-pln002-plan-two.ipd.md"
    p2.write_text(
        PLAN_TEMPLATE.format(
            title="Plan Two",
            status="draft",
            set_field="myset (My Set)",
            order="02",
            id6="pln002",
        ),
        encoding="utf-8",
    )

    # 3: One executed
    p3 = plans_dir / "executed" / "20260920-otherset-01-pln003-plan-three.ipd.md"
    p3.write_text(
        PLAN_TEMPLATE.format(
            title="Plan Three",
            status="executed",
            set_field="otherset",
            order="01",
            id6="pln003",
        ),
        encoding="utf-8",
    )

    # 4: One in executed/202608/ shard
    p4 = (
        plans_dir
        / "executed"
        / "202608"
        / "20260815-sharded-01-pln004-plan-four.ipd.md"
    )
    p4.write_text(
        PLAN_TEMPLATE.format(
            title="Plan Four",
            status="executed",
            set_field="sharded",
            order="01",
            id6="pln004",
        ),
        encoding="utf-8",
    )

    # 5: One whose - Status: has trailing prose so plans_index and selectors disagree
    p5 = plans_dir / "pending" / "20260920-statset-01-pln005-plan-five.ipd.md"
    p5.write_text(
        PLAN_TEMPLATE.format(
            title="Plan Five",
            status="draft (aw set): status set to draft",
            set_field="statset",
            order="01",
            id6="pln005",
        ),
        encoding="utf-8",
    )

    # 6: One for unreadable test
    p6 = plans_dir / "pending" / "20260920-unread-01-pln006-plan-six.ipd.md"
    p6.write_text(
        PLAN_TEMPLATE.format(
            title="Plan Six",
            status="draft",
            set_field="unread",
            order="01",
            id6="pln006",
        ),
        encoding="utf-8",
    )

    # Research docs: 3 well-formed + 1 unparseable
    r1 = research_dir / "20260920-topic-01-res001-first-research.findings.md"
    r1.write_text(
        RESEARCH_TEMPLATE.format(
            id6="res001",
            set_id="topic",
            order="01",
            status="reference",
            summary="first research",
            title="First Research",
        ),
        encoding="utf-8",
    )

    r2 = research_dir / "20260920-topic-02-res002-second-research.findings.md"
    r2.write_text(
        RESEARCH_TEMPLATE.format(
            id6="res002",
            set_id="topic",
            order="02",
            status="reference",
            summary="second research",
            title="Second Research",
        ),
        encoding="utf-8",
    )

    r3 = research_dir / "20260920-othertopic-01-res003-third-research.findings.md"
    r3.write_text(
        RESEARCH_TEMPLATE.format(
            id6="res003",
            set_id="othertopic",
            order="01",
            status="todo",
            summary="third research",
            title="Third Research",
        ),
        encoding="utf-8",
    )

    # 4: Unparseable filename under research_contract.parse_name
    r4 = research_dir / "conformance-results-template.md"
    r4.write_text(
        "# Conformance Results Template\n\nNo frontmatter block here.\n",
        encoding="utf-8",
    )

    return repo


def _audit_count_opens(target_prefix: str):
    opens: Dict[str, int] = {}

    def hook(event: str, args: tuple) -> None:
        if event == "open":
            p = str(args[0])
            if target_prefix in p and p.endswith(".md"):
                opens[p] = opens.get(p, 0) + 1

    sys.addaudithook(hook)
    return opens


def test_a_find_plans_single_read_non_matched(tmp_repo: Path) -> None:
    plans_dir = tmp_repo / ".aw" / "records" / "plans"
    opens = _audit_count_opens(str(plans_dir))

    args = argparse.Namespace(
        dir=str(tmp_repo),
        id=None,
        set=None,
        status=None,
        topic=None,
        disposition=None,
    )
    term = Term(color=False)
    lines, paths, matches = cli._find_type_records(
        tmp_repo, "plans", ["pln001"], args, term
    )

    assert len(lines) == 1
    assert "pln001" in lines[0]

    all_plan_files = list(plans_dir.rglob("*.md"))
    assert len(all_plan_files) == 6

    matched_path = str(
        (plans_dir / "pending" / "20260920-myset-01-pln001-plan-one.ipd.md").resolve()
    )
    assert opens.get(matched_path, 0) <= 2

    for p in all_plan_files:
        p_str = str(p.resolve())
        if p_str != matched_path:
            count = opens.get(p_str, 0)
            assert (
                count == 1
            ), f"Non-matched plan {p.name} opened {count} times (expected 1)"


def test_b_find_research_single_read_non_matched(tmp_repo: Path) -> None:
    research_dir = tmp_repo / ".aw" / "records" / "research"
    opens = _audit_count_opens(str(research_dir))

    args = argparse.Namespace(
        dir=str(tmp_repo),
        id=None,
        set=None,
        status=None,
        topic=None,
        disposition=None,
    )
    term = Term(color=False)
    lines, paths, matches = cli._find_type_records(
        tmp_repo, "research", ["res001"], args, term
    )

    assert len(lines) == 1
    assert "res001" in lines[0]

    all_research_files = list(research_dir.rglob("*.md"))
    assert len(all_research_files) == 4

    matched_path = str(
        (research_dir / "20260920-topic-01-res001-first-research.findings.md").resolve()
    )
    assert opens.get(matched_path, 0) <= 2

    for p in all_research_files:
        p_str = str(p.resolve())
        if p_str != matched_path:
            count = opens.get(p_str, 0)
            assert (
                count == 1
            ), f"Non-matched research doc {p.name} opened {count} times (expected 1)"


def test_c_find_plans_setid_matches_oracle_and_shard_ordering(
    tmp_repo: Path,
) -> None:
    plans_dir = tmp_repo / ".aw" / "records" / "plans"

    # Evidence that the shard exists in the fixture
    shard_file = (
        plans_dir
        / "executed"
        / "202608"
        / "20260815-sharded-01-pln004-plan-four.ipd.md"
    )
    assert shard_file.is_file(), f"Fixture shard missing: {shard_file}"
    rel_shard = shard_file.relative_to(plans_dir).as_posix()
    assert rel_shard.startswith("executed/202608/")

    args = argparse.Namespace(
        dir=str(tmp_repo),
        id=None,
        set=None,
        status=None,
        topic=None,
        disposition=None,
    )
    term = Term(color=False)

    for selector in ["myset", "sharded"]:
        # Oracle: old algorithm using scan_plans
        entries, _drift = pi.scan_plans(plans_dir)
        matched_paths, _ = cli._resolve_selectors_with_kinds(
            tmp_repo, "plans", [selector]
        )
        matched = set(p.resolve() for p in matched_paths)
        oracle_results = [
            e
            for e in entries
            if (plans_dir / e.path).resolve() in matched
            or (tmp_repo / e.path).resolve() in matched
        ]
        oracle_lines = []
        for e in oracle_results:
            status = e.disposition or e.status or "-"
            status_txt, id6_txt = cli._find_status_and_id6(
                "plans", status, e.plan_id or "??????", term
            )
            set_txt = f"{e.set_id or '-':<14}"
            full_p = (plans_dir / e.path).resolve()
            try:
                rel_p = str(full_p.relative_to(tmp_repo.resolve()))
            except Exception:
                rel_p = str(e.path)
            disp_p = cli._highlight_filename_matches(rel_p, [selector], term)
            oracle_lines.append(f"{status_txt}  {id6_txt}  {set_txt}  {disp_p}")

        lines, paths, matches = cli._find_type_records(
            tmp_repo, "plans", [selector], args, term
        )
        assert lines == oracle_lines


def test_d_status_disagreement_record_matches_and_preserves_plans_index_status(
    tmp_repo: Path,
) -> None:
    plans_dir = tmp_repo / ".aw" / "records" / "plans"
    args = argparse.Namespace(
        dir=str(tmp_repo),
        id=None,
        set=None,
        status=None,
        topic=None,
        disposition=None,
    )
    term = Term(color=False)

    # 1. Matches per selector by id6
    lines, paths, matches = cli._find_type_records(
        tmp_repo, "plans", ["pln005"], args, term
    )
    assert len(lines) == 1
    assert "pln005" in lines[0]

    # 2. plans_index whole-file parse preserves the trailing prose
    entries, _ = pi.scan_plans(plans_dir)
    target = [e for e in entries if e.plan_id == "pln005"][0]
    assert target.status == "draft (aw set): status set to draft"


def test_e_unparseable_research_doc_produces_no_rows(tmp_repo: Path) -> None:
    args = argparse.Namespace(
        dir=str(tmp_repo),
        id=None,
        set=None,
        status=None,
        topic=None,
        disposition=None,
    )
    term = Term(color=False)

    # 'template' matches conformance-results-template.md by substring
    lines, paths, matches = cli._find_type_records(
        tmp_repo, "research", ["template"], args, term
    )
    # The display layer skips unparseable research docs, printing no rows
    assert lines == []
    assert paths == []
    assert len(matches) == 1
    assert matches[0].kind == "substring"


def test_f_unreadable_matched_plan_raises_permission_error(
    tmp_repo: Path,
) -> None:
    if os.getuid() == 0:
        pytest.skip("Running as root; chmod 0 does not deny read")

    plans_dir = tmp_repo / ".aw" / "records" / "plans"
    p6 = plans_dir / "pending" / "20260920-unread-01-pln006-plan-six.ipd.md"

    p6.chmod(0o000)
    try:
        args = argparse.Namespace(
            dir=str(tmp_repo),
            id=None,
            set=None,
            status=None,
            topic=None,
            disposition=None,
        )
        term = Term(color=False)
        with pytest.raises(PermissionError):
            cli._find_type_records(tmp_repo, "plans", ["unread"], args, term)
    finally:
        p6.chmod(0o644)

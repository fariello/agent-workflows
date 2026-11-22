"""Behavioral pinning tests for selectors and aw find (IPD cdglt1 E-01).

Pins observable behavior of `agent_workflows.selectors` and `aw find` across record types,
filter flags, loose-whitespace and quoted-example fixtures, zero-match exit code 2, and the
multi-word `EXECUTED (approved ...)` fixture before moving readers onto `artifact_meta`.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import cli, plans, selectors
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _run_find(repo: Path, *args: str) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(["find", *args, "--dir", str(repo)])
    return rc, out.getvalue(), err.getvalue()


def _build_fixture_repo(tmp_path: Path) -> dict[str, Path]:
    repo = tmp_path / "repo"
    recs = repo / ".aw" / "records"
    for sub in (
        "plans/pending",
        "plans/executed",
        "specs/to-review",
        "specs/approved",
        "backlog/open",
        "backlog/done",
        "research",
        "prompts/pending",
        "prompts/executed",
        "releases",
        "walkthroughs",
        "reviews",
    ):
        (recs / sub).mkdir(parents=True, exist_ok=True)

    p1 = recs / "plans" / "pending" / "20261101-alpha-01-pln001-first-plan.ipd.md"
    p1.write_text(
        RecordBuilder().plan(
            title="First Plan",
            id6="pln001",
            status="approved",
            set="alpha (Alpha Set)",
            order=1,
            blocks_release="next",
            history=["- 2026-11-01 created"],
            text_only=True,
        ),
        encoding="utf-8",
    )

    p2 = recs / "plans" / "pending" / "20261101-alpha-02-pln002-second-plan.ipd.md"
    p2.write_text(
        RecordBuilder().plan(
            title="Second Plan",
            id6="pln002",
            status="draft",
            set="alpha (Alpha Set)",
            order=2,
            history=["- 2026-11-01 created"],
            text_only=True,
        ),
        encoding="utf-8",
    )

    p_multi = (
        recs / "plans" / "executed" / "20260710-oldset-01-pln003-multiword-exec.ipd.md"
    )
    p_multi.write_text(
        RecordBuilder().plan(
            title="Multiword Executed Plan",
            id6="pln003",
            set="oldset",
            order=1,
            history=["- 2026-07-10 executed"],
            raw_fields={"Status": "EXECUTED (approved by maintainer)"},
            text_only=True,
        ),
        encoding="utf-8",
    )

    s1 = recs / "specs" / "to-review" / "20261101-spc001-01-spc001-core-spec.spec.md"
    s1.write_text(
        RecordBuilder().spec(
            title="Core Spec",
            id6="spc001",
            status="to-review",
            set="spc001",
            text_only=True,
        ),
        encoding="utf-8",
    )

    b1 = recs / "backlog" / "open" / "20261101-bklset-01-bkl001-open-bug.backlog.md"
    b1.write_text(
        RecordBuilder().backlog(
            id6="bkl001",
            status="open",
            set="bklset",
            work_kind="bug",
            priority="high",
            body="## Summary\nOpen bug item",
            text_only=True,
        ),
        encoding="utf-8",
    )

    r1 = recs / "research" / "20261101-resset-01-res001-topic-study.research-report.md"
    r1.write_text(
        RecordBuilder().research(
            id6="res001",
            when="2026-11-01",
            set="resset",
            order=1,
            topic=["cache"],
            model="opus",
            research_kind="research-report",
            status="reference",
            outcome="informational",
            summary="Study of cache reads",
            consumed_by=[],
            body="# Topic Study\n\nBody text.\n",
            text_only=True,
        ),
        encoding="utf-8",
    )

    pr1 = (
        recs
        / "prompts"
        / "pending"
        / "20261101-prset1-01-pr0001-comment-prompt.prompt.md"
    )
    pr1.write_text(
        RecordBuilder().prompt(
            prompt_kind="research",
            id6="pr0001",
            set="prset1",
            status="pending",
            when="2026-11-01",
            body="# Comment Prompt\n\nPrompt text.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    pr2 = (
        recs
        / "prompts"
        / "executed"
        / "20261101-prset2-01-pr0002-slot-prompt.prompt.md"
    )
    pr2.write_text(
        "# Slot Prompt\n\nPrompt without comment.\n",
        encoding="utf-8",
    )

    rel1 = recs / "releases" / "20261101-relset-01-rel001-v2.release.md"
    rel1.write_text(
        RecordBuilder().release(
            id6="rel001", status="planned", set="relset", text_only=True
        ),
        encoding="utf-8",
    )

    w1 = recs / "walkthroughs" / "20261101-wlkset-01-wlk001-walkthrough.walkthrough.md"
    w1.write_text(
        RecordBuilder().walkthrough(
            id6="wlk001",
            set="wlkset",
            body="# Walkthrough: wlkset\n\n## Notes\nDone.",
            text_only=True,
        ),
        encoding="utf-8",
    )

    rev1 = recs / "reviews" / "20261101-alpha-01-pln001-first-plan.review.md"
    rev1.write_text(
        RecordBuilder().review(
            subject="pln001", subject_type="ipd", verdict="APPROVE", text_only=True
        ),
        encoding="utf-8",
    )

    return {
        "repo": repo,
        "p1": p1,
        "p2": p2,
        "p_multi": p_multi,
        "s1": s1,
        "b1": b1,
        "r1": r1,
        "pr1": pr1,
        "pr2": pr2,
        "rel1": rel1,
        "w1": w1,
        "rev1": rev1,
    }


def test_selector_matching_per_type(tmp_path: Path) -> None:
    """Pin id6, Set, status, stem, and substring selector matching across record types."""
    fx = _build_fixture_repo(tmp_path)
    repo = fx["repo"]

    # Plans: id6, setid, status, stem, substring
    assert selectors.resolve(repo, "plans", "pln001").kind == selectors.MATCH_ID6
    assert selectors.resolve(repo, "plans", "pln001").paths == [fx["p1"].resolve()]

    res_set = selectors.resolve(repo, "plans", "alpha")
    assert res_set.kind == selectors.MATCH_SETID
    assert res_set.paths == sorted([fx["p1"].resolve(), fx["p2"].resolve()])

    res_status = selectors.resolve(repo, "plans", "approved")
    assert res_status.kind == selectors.MATCH_STATUS
    assert res_status.paths == [fx["p1"].resolve()]

    stem = fx["p2"].stem
    res_stem = selectors.resolve(repo, "plans", stem)
    assert res_stem.kind == selectors.MATCH_STEM
    assert res_stem.paths == [fx["p2"].resolve()]

    res_sub = selectors.resolve(repo, "plans", "second-plan")
    assert res_sub.kind == selectors.MATCH_SUBSTRING
    assert res_sub.paths == [fx["p2"].resolve()]

    # Specs, backlog, research, releases, walkthroughs, reviews
    assert selectors.resolve(repo, "specs", "to-review").kind == selectors.MATCH_STATUS
    assert selectors.resolve(repo, "specs", "spc001").kind == selectors.MATCH_ID6
    assert selectors.resolve(repo, "backlog", "open").kind == selectors.MATCH_STATUS
    assert selectors.resolve(repo, "backlog", "bklset").kind == selectors.MATCH_SETID
    assert selectors.resolve(repo, "research", "res001").kind == selectors.MATCH_ID6
    assert (
        selectors.resolve(repo, "research", "reference").kind == selectors.MATCH_STATUS
    )
    assert selectors.resolve(repo, "research", "resset").kind == selectors.MATCH_SETID
    assert selectors.resolve(repo, "releases", "planned").kind == selectors.MATCH_STATUS
    assert selectors.resolve(repo, "walkthroughs", "wlk001").kind == selectors.MATCH_ID6
    assert selectors.resolve(repo, "reviews", "pln001").paths == [fx["rev1"].resolve()]


def test_find_plans_id6_and_filter_flags(tmp_path: Path) -> None:
    """Pin `aw find plans <id6>` and --status/--status-not/--set/--id filters."""
    fx = _build_fixture_repo(tmp_path)
    repo = fx["repo"]

    rc, out, _ = _run_find(repo, "plans", "pln001", "--paths")
    assert rc == 0
    assert out.strip().splitlines() == [
        ".aw/records/plans/pending/20261101-alpha-01-pln001-first-plan.ipd.md"
    ]

    rc, out, _ = _run_find(repo, "plans", "--status", "draft", "--paths")
    assert rc == 0
    assert out.strip().splitlines() == [
        ".aw/records/plans/pending/20261101-alpha-02-pln002-second-plan.ipd.md"
    ]

    rc, out, _ = _run_find(
        repo, "plans", "--set", "alpha", "--status-not", "draft", "--paths"
    )
    assert rc == 0
    assert out.strip().splitlines() == [
        ".aw/records/plans/pending/20261101-alpha-01-pln001-first-plan.ipd.md"
    ]

    rc, out, _ = _run_find(repo, "plans", "--id", "pln002", "--paths")
    assert rc == 0
    assert out.strip().splitlines() == [
        ".aw/records/plans/pending/20261101-alpha-02-pln002-second-plan.ipd.md"
    ]


def test_find_research_and_prompts_rows(tmp_path: Path) -> None:
    """Pin `aw find research` and `aw find prompts` comment-first then slot rows."""
    fx = _build_fixture_repo(tmp_path)
    repo = fx["repo"]

    rc, out, _ = _run_find(repo, "research", "--agent")
    assert rc == 0
    items = [json.loads(ln) for ln in out.splitlines() if ln.strip()]
    research_items = [x for x in items if x.get("kind") == "item"]
    assert len(research_items) == 1
    assert research_items[0]["id6"] == "res001"
    assert research_items[0]["status"] == "reference"
    assert research_items[0]["set"] == "resset"

    rc, out, _ = _run_find(repo, "prompts", "--agent")
    assert rc == 0
    items = [json.loads(ln) for ln in out.splitlines() if ln.strip()]
    prompt_items = {x["path"]: x for x in items if x.get("kind") == "item"}
    assert len(prompt_items) == 2

    p1_rel = (
        ".aw/records/prompts/pending/20261101-prset1-01-pr0001-comment-prompt.prompt.md"
    )
    p2_rel = (
        ".aw/records/prompts/executed/20261101-prset2-01-pr0002-slot-prompt.prompt.md"
    )
    assert prompt_items[p1_rel]["id6"] == "pr0001"
    assert prompt_items[p1_rel]["set"] == "prset1"
    assert prompt_items[p1_rel]["status"] == "pending"
    assert prompt_items[p2_rel]["id6"] == "pr0002"
    assert prompt_items[p2_rel]["set"] == "prset2"
    assert prompt_items[p2_rel]["status"] == "executed"


def test_loose_whitespace_and_quoted_example_fixtures(tmp_path: Path) -> None:
    """Pin public loose-whitespace readers, declared_id6, and quoted-example bounding."""
    two_spaces = (
        "# IPD: Two Spaces\n\n"
        "-  Id: lse001\n"
        "-  Status: approved\n"
        "-  Blocks-Release: next\n\n"
        "## Workflow history\n- 2026-11-01 created\n"
    )
    tab_sep = (
        "# IPD: Tab\n\n"
        "-\tId: lse002\n"
        "-\tStatus: reviewed\n"
        "-\tBlocks-Release: abc123\n\n"
        "## Workflow history\n- 2026-11-01 created\n"
    )
    assert selectors.read_front_matter_id(two_spaces) == "lse001"
    assert selectors.read_front_matter_status(two_spaces) == "approved"
    assert selectors.read_front_matter_blocks_release(two_spaces) == "next"
    assert selectors._read_id(two_spaces) is None
    assert selectors._read_status(two_spaces) is None

    assert selectors.read_front_matter_id(tab_sep) == "lse002"
    assert selectors.read_front_matter_status(tab_sep) == "reviewed"
    assert selectors.read_front_matter_blocks_release(tab_sep) == "abc123"
    assert selectors._read_id(tab_sep) is None
    assert selectors._read_status(tab_sep) is None

    quoted = RecordBuilder().plan(
        title="Real",
        id6="real01",
        status="draft",
        body="## Example\n- Id: quot01\n- Status: approved\n- Blocks-Release: next",
        text_only=True,
    )
    assert selectors.read_front_matter_id(quoted) == "real01"
    assert selectors.read_front_matter_status(quoted) == "draft"
    assert selectors.read_front_matter_blocks_release(quoted) is None

    p_real = tmp_path / "20261101-demo-01-real01-real.ipd.md"
    p_real.write_text(quoted, encoding="utf-8")
    assert selectors.declared_id6(p_real) == "real01"
    assert selectors.declares_id6(p_real, "real01") is True
    assert selectors.declares_id6(p_real, "quot01") is False
    assert selectors.id6_ownership(p_real, "real01") == selectors.OWNERSHIP_DECLARED
    assert selectors.id6_ownership(p_real, "quot01") == selectors.OWNERSHIP_FOREIGN_ID


def test_find_zero_match_exits_2(tmp_path: Path) -> None:
    """Pin exit code 2 when `aw find` receives a selector matching nothing (4.4a zyj8io)."""
    fx = _build_fixture_repo(tmp_path)
    repo = fx["repo"]

    rc, out, err = _run_find(repo, "plans", "zzzzzz", "--paths")
    assert rc == 2
    assert out == ""
    assert "zzzzzz" in err

    rc_agent, out_agent, _ = _run_find(repo, "plans", "zzzzzz", "--agent")
    assert rc_agent == 2
    rec = json.loads(out_agent.strip())
    assert rec["exit"] == 2
    assert rec["outcome"] == "cannot-run"


def test_multiword_executed_plan_disagreement_fixture(tmp_path: Path) -> None:
    """Pin the 24-plan disagreement fixture: `- Status: EXECUTED (approved ...)` in executed/."""
    fx = _build_fixture_repo(tmp_path)
    repo = fx["repo"]
    multi_rel = (
        ".aw/records/plans/executed/20260710-oldset-01-pln003-multiword-exec.ipd.md"
    )
    multi_text = fx["p_multi"].read_text(encoding="utf-8")

    # Canonical plan status reader already reports 'executed'
    assert plans.read_status(fx["p_multi"]) == "executed"

    # D-1 convergence: selector path and filter path both normalize multi-word EXECUTED to 'executed'
    rc_flt, out_flt, _ = _run_find(repo, "plans", "--status", "executed", "--paths")
    assert rc_flt == 0
    assert multi_rel in out_flt.splitlines()

    rc_sel, out_sel, _ = _run_find(repo, "plans", "executed", "--paths")
    assert rc_sel == 0
    assert multi_rel in out_sel.splitlines()
    assert selectors._read_status(multi_text) == "executed"

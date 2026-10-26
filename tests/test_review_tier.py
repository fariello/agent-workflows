"""Tests for review_tier module and Review-Depth metadata field (spec k3yx72; IPD gv3smb)."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import unittest

import pytest

from agent_workflows import (
    ipd_lifecycle,
    ipd_lint,
    review_tier,
    run_analytics_cli as analytics_cli,
    run_analytics_query as query,
)
from tests.test_run_analytics_review_cost import (
    _NO_REVIEW_TIER,
    _review_run,
)

pytestmark = pytest.mark.core


def _conforming_child(
    *,
    scope_paths: str | None = None,
    extra_e_count: int = 0,
    review_depth: str | None = None,
) -> str:
    meta_lines = [
        "- Date: 2026-08-03",
        "- Kind: child",
        "- Concern: sample concern.",
        "- Scope: sample scope.",
        "- Status: to-review",
        "- Work-Kind: chore",
        "- Priority: medium",
        "- Set: x",
        "- Order: 1",
        f"- Highest E allocated: {1 + extra_e_count:02d}",
        "- Author: tester",
        "- Id: abc123",
    ]
    if scope_paths is not None:
        meta_lines.append(f"- Scope-Paths: {scope_paths}")
    if review_depth is not None:
        meta_lines.append(f"- Review-Depth: {review_depth}")

    checklist_lines = [
        "- [ ] E-01 do the first thing.",
        "  - Depends on: none",
        "  - Expected outcome: the first thing exists.",
        "  - Execution state: pending",
    ]
    for i in range(2, 2 + extra_e_count):
        checklist_lines.extend(
            [
                f"- [ ] E-{i:02d} do thing {i}.",
                "  - Depends on: none",
                f"  - Expected outcome: thing {i} exists.",
                "  - Execution state: pending",
            ]
        )

    return f"""# IPD: sample (Set x, Order 1)

{chr(10).join(meta_lines)}

## Workflow history

- 2026-08-03 to-review (tester): created.

## Goal

Sample goal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark performed only after doing it.

### Task group 1: main tasks

{chr(10).join(checklist_lines)}

## Project conventions discovered (Step 0)

- x

## Findings

- x

## Proposed changes (ordered, validatable)

1. E-01: first step.

## Deferred / out of scope (with reason)

- none
  - Carrier: none

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- test something.

## Spec / documentation sync

None needed.

## Open questions

### OQ-01: sample question

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: done.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass.

- [ ] V-01 validates E-01
  - Required evidence: check output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: none
"""


def test_lint_text_review_depth_accepted() -> None:
    """(a) ipd_lint.lint_text on a minimal conformant plan with - Review-Depth: standard

    reports no IPD-M103/IPD-M104, and with huge reports IPD-M104.
    """
    text_std = _conforming_child(review_depth="standard")
    res_std = ipd_lint.lint_text(text_std, checkpoint="author")
    codes_std = [d.code for d in res_std.diagnostics]
    assert "IPD-M103" not in codes_std
    assert "IPD-M104" not in codes_std

    text_huge = _conforming_child(review_depth="huge")
    res_huge = ipd_lint.lint_text(text_huge, checkpoint="author")
    codes_huge = [d.code for d in res_huge.diagnostics]
    assert "IPD-M104" in codes_huge


def test_frozen_region_digest_invariant() -> None:
    """(b) ipd_lifecycle.frozen_region_digest is equal for the same plan with and without Review-Depth."""
    text_without = _conforming_child(scope_paths="agent_workflows/a.py")
    text_with = _conforming_child(
        scope_paths="agent_workflows/a.py", review_depth="standard"
    )
    d1 = ipd_lifecycle.frozen_region_digest(text_without)
    d2 = ipd_lifecycle.frozen_region_digest(text_with)
    assert d1 == d2


def test_tier_facts_fixtures() -> None:
    """(c) tier_facts on three fixture plans returns expected values:

    1. naming a .spec.md -> names_spec=True, scope_paths has it.
    2. with 19 E-items -> e_items=19, exceeds_size=True (19 > 18).
    3. with no - Scope-Paths: -> scope_paths=None, names_spec=False.
    """
    # 1. Naming a .spec.md
    plan_spec = _conforming_child(
        scope_paths="docs/sample.spec.md, agent_workflows/a.py"
    )
    facts_spec = review_tier.tier_facts(plan_spec)
    assert facts_spec["kind"] == "child"
    assert facts_spec["in_set"] is True
    assert facts_spec["names_spec"] is True
    assert facts_spec["scope_paths"] == ["docs/sample.spec.md", "agent_workflows/a.py"]
    assert facts_spec["e_items"] == 1
    assert facts_spec["task_groups"] == 1
    assert facts_spec["exceeds_size"] is False

    # 2. 19 E-items (1 + 18 extra)
    plan_19 = _conforming_child(extra_e_count=18, scope_paths="agent_workflows/a.py")
    facts_19 = review_tier.tier_facts(plan_19)
    assert facts_19["e_items"] == 19
    assert facts_19["exceeds_size"] is True

    # 3. No - Scope-Paths:
    plan_no_scope = _conforming_child(scope_paths=None)
    facts_no_scope = review_tier.tier_facts(plan_no_scope)
    assert facts_no_scope["scope_paths"] is None
    assert facts_no_scope["names_spec"] is False


def test_parse_tier_marker() -> None:
    """(d) parse_tier_marker accepts each valid marker, accepts it before a trailing fence line,

    and returns None for aw-tier: simple, a marker not on the last line, and an unknown tier.
    """
    assert review_tier.parse_tier_marker("Some text\nAW-TIER: simple") == "simple"
    assert review_tier.parse_tier_marker("Some text\nAW-TIER: standard") == "standard"
    assert review_tier.parse_tier_marker("Some text\nAW-TIER: complex") == "complex"

    # Before trailing code-fence line
    assert (
        review_tier.parse_tier_marker("Some text\nAW-TIER: standard\n```\n")
        == "standard"
    )
    assert (
        review_tier.parse_tier_marker("Some text\nAW-TIER: complex\n~~~\n") == "complex"
    )

    # Lowercase marker
    assert review_tier.parse_tier_marker("Some text\naw-tier: simple") is None

    # Marker not on the last line
    assert (
        review_tier.parse_tier_marker("AW-TIER: standard\nExtra text afterwards")
        is None
    )

    # Unknown tier
    assert review_tier.parse_tier_marker("AW-TIER: huge") is None
    assert review_tier.parse_tier_marker("AW-TIER: orchestrator") is None
    assert review_tier.parse_tier_marker("") is None


def test_parse_tier_answers_two_rounds() -> None:
    """(e) parse_tier_answers on a review text with two rounds reads the last round only

    and tier_answers_complete is false when answer 4 is missing.
    """
    review_text = """# Review

## Round 1
### Step T
1. Answer 1 from round 1
2. Answer 2 from round 1
3. Answer 3 from round 1
4. Answer 4 from round 1
5. Answer 5 from round 1

## Round 2
### Step T
1. Answer 1 from round 2
2. Answer 2 from round 2
3. Answer 3 from round 2
5. Answer 5 from round 2
"""
    answers = review_tier.parse_tier_answers(review_text)
    assert answers is not None
    assert answers[1] == "Answer 1 from round 2"
    assert answers[2] == "Answer 2 from round 2"
    assert answers[3] == "Answer 3 from round 2"
    assert 4 not in answers
    assert answers[5] == "Answer 5 from round 2"
    assert review_tier.tier_answers_complete(answers) is False

    # Complete answers test
    complete_text = review_text.replace(
        "5. Answer 5 from round 2",
        "4. Answer 4 from round 2\n5. Answer 5 from round 2",
    )
    complete_answers = review_tier.parse_tier_answers(complete_text)
    assert complete_answers is not None
    assert review_tier.tier_answers_complete(complete_answers) is True

    # Subsection absent returns None
    no_step_t = "## Round 1\n### Step P\nNotes."
    assert review_tier.parse_tier_answers(no_step_t) is None


def test_record_review_tier() -> None:
    """(f) record_review_tier writes the four keys, passes the tier through unchanged (MD-1),

    survives json.dumps, and an unknown tier or source raises ValueError.
    """
    attempt: dict = {"number": 1, "action": "review"}
    answers = {1: "No.", 2: "No.", 3: "No.", 4: "Yes.", 5: "No."}
    facts = {"kind": "child", "in_set": True, "e_items": 3}

    review_tier.record_review_tier(
        attempt,
        tier="standard",
        source="agent",
        answers=answers,
        facts=facts,
    )

    assert attempt["review_tier"] == "standard"
    assert attempt["review_tier_source"] == "agent"
    assert attempt["review_tier_answers"] == {
        "1": "No.",
        "2": "No.",
        "3": "No.",
        "4": "Yes.",
        "5": "No.",
    }
    assert attempt["review_tier_facts"] == facts

    dumped = json.dumps(attempt)
    loaded = json.loads(dumped)
    assert loaded["review_tier"] == "standard"
    assert loaded["review_tier_answers"]["1"] == "No."

    # Unknown tier raises ValueError
    with pytest.raises(ValueError, match="Invalid review tier"):
        review_tier.record_review_tier(
            attempt,
            tier="huge",
            source="agent",
            answers=None,
            facts=None,
        )

    # Unknown source raises ValueError
    with pytest.raises(ValueError, match="Invalid review tier source"):
        review_tier.record_review_tier(
            attempt,
            tier="standard",
            source="invalid_source",
            answers=None,
            facts=None,
        )


def test_tier_facts_empty_and_no_metadata() -> None:
    """(h) tier_facts on an empty string and on a plan with no metadata block returns

    the seven keys without raising.
    """
    f_empty = review_tier.tier_facts("")
    assert set(f_empty.keys()) == {
        "kind",
        "scope_paths",
        "names_spec",
        "e_items",
        "task_groups",
        "exceeds_size",
        "in_set",
    }
    assert f_empty["kind"] is None
    assert f_empty["scope_paths"] is None
    assert f_empty["names_spec"] is False
    assert f_empty["e_items"] == 0
    assert f_empty["task_groups"] == 0
    assert f_empty["exceeds_size"] is False
    assert f_empty["in_set"] is False

    f_no_meta = review_tier.tier_facts("# IPD: Plan Title\n\n## Goal\nSome goal.")
    assert set(f_no_meta.keys()) == {
        "kind",
        "scope_paths",
        "names_spec",
        "e_items",
        "task_groups",
        "exceeds_size",
        "in_set",
    }
    assert f_no_meta["kind"] is None
    assert f_no_meta["scope_paths"] is None


class TestAttemptGrainRoundTrip(unittest.TestCase):
    """(g) Attempt-grain round trip:

    A fixture run whose attempt carries review_tier: "simple", analyzed by the real
    aw runs analyze leaf, answers run_query("attempts", group_by="review_tier", ...)
    with a simple row, and an attempt with no review_tier key lands in the ""/(none) group
    rather than being dropped.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        runs = self.repo / ".aw" / "records" / "runs"

        # Run 0 carries review_tier="simple"
        _review_run(
            runs,
            "run-20260910T000000Z-0",
            label="exp1",
            variant="grouped-6",
            model="uri/m-a",
            review_tier="simple",
        )

        # Run 1 carries no review_tier key (unrecorded)
        _review_run(
            runs,
            "run-20260910T010000Z-1",
            label="exp1",
            variant="single-12",
            model="uri/m-b",
            review_tier=_NO_REVIEW_TIER,
        )

        args = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=False,
            open=False,
            rebuild=False,
            keep_snapshot=None,
            targets=[],
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
            since=None,
            until=None,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            res = analytics_cli.run_analyze(args)
            self.assertEqual(res, 0)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_group_by_review_tier_round_trip(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            group_by="review_tier",
            metric="cost",
            stat="count",
        )
        tier_counts = {r["review_tier"]: r["n"] for r in res.rows}
        # Run 0 has 2 main sessions with review_tier="simple"
        self.assertIn("simple", tier_counts)
        self.assertEqual(tier_counts["simple"], 2)
        # Run 1 has 2 main sessions with no review_tier (lands in ""/(none)/(not recorded) group)
        unrecorded_label = next(k for k in tier_counts if k != "simple")
        self.assertIn(unrecorded_label, ("(not recorded)", "(none)", ""))
        self.assertEqual(tier_counts[unrecorded_label], 2)

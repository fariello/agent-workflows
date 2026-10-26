"""Pure tests for review sequence model, prompt rendering, postconditions, and structural diff.

Covers IPD uiyoax Task group 1 (spec k3yx72 Sections 5.3, 6, 6.1).
"""

from __future__ import annotations

import pytest

from agent_workflows import review_sequence

pytestmark = pytest.mark.core


SAMPLE_PLAN = """# IPD: Sample Test Plan

- Date: 2026-10-25
- Id: spl001
- Set: sample
- Order: 1
- Status: to-review
- Kind: child
- Concern: Test concern.
- Scope: Test scope.
- Scope-Paths: none
- Item-Dependencies: none
- Priority: medium
- Work-Kind: feature
- Author: test
- Highest E allocated: 01

## Workflow history

- 2026-10-25 to-review (test): authored
- 2026-10-25 draft (test): created

## Goal

Test goal.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Implement the feature
  - Depends on: none
  - Expected outcome: feature is working
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: tests pass
  - Result: pending

## Open questions

### OQ-01: Is this a test question?

- Blocking: no
- Status: open
- Rationale: Non-blocking test question.
"""


def test_prompt_plan_counts() -> None:
    """AC-01 & V-01: verify prompt group counts per tier and variant."""
    # simple (quick_ok True and False): expected 2, 3
    assert len(review_sequence.prompt_plan("simple", quick_ok=True)) == 2
    assert len(review_sequence.prompt_plan("simple", quick_ok=False)) == 3

    # standard: expected 5
    assert len(review_sequence.prompt_plan("standard")) == 5
    standard_groups = review_sequence.prompt_plan("standard")
    assert standard_groups == [
        ("P", "T"),
        ("R1", "R2"),
        ("R3", "R4"),
        ("S5", "S6"),
        ("S7",),
    ]

    # complex grouped-6: expected 7
    assert len(review_sequence.prompt_plan("complex", "grouped-6")) == 7

    # complex single-12 in and outside Set: expected 13, 12
    assert len(review_sequence.prompt_plan("complex", "single-12", in_set=True)) == 13
    assert len(review_sequence.prompt_plan("complex", "single-12", in_set=False)) == 12

    # orchestrator: expected 4
    assert len(review_sequence.prompt_plan("orchestrator")) == 4


def test_raise_tier_plan() -> None:
    """Verify extra groups when raising tier before S5."""
    done = {"P", "T", "Q"}
    # Raising simple -> standard
    extra_std = review_sequence.raise_tier_plan(done, "standard")
    assert extra_std == [("R1", "R2"), ("R3", "R4")]

    # Raising simple -> complex:single-12 (in set)
    extra_single = review_sequence.raise_tier_plan(
        done, "complex", "single-12", in_set=True
    )
    expected_single = [
        ("R1",),
        ("R2",),
        ("R3",),
        ("R4",),
        ("R5",),
        ("R6",),
        ("R7",),
    ]
    assert extra_single == expected_single

    # Outside set drops R7
    extra_single_out = review_sequence.raise_tier_plan(
        done, "complex", "single-12", in_set=False
    )
    assert ("R7",) not in extra_single_out
    assert len(extra_single_out) == 6


def test_render_prompt_and_reask() -> None:
    """V-02: verify prompt rendering and byte-for-byte re-ask wording."""
    p1 = review_sequence.prompt_plan("standard")[0]
    rendered = review_sequence.render_prompt(
        p1,
        first=True,
        plan_rel=".aw/records/plans/pending/test.ipd.md",
        facts_md="- Kind: child\n- Execution items: 1",
        lane_notice="[ISOLATION NOTICE]",
    )
    assert "Review plan: .aw/records/plans/pending/test.ipd.md" in rendered
    assert ".aw/system/workflows/plan-review/steps/_kernel.md" in rendered
    assert ".aw/system/workflows/plan-review/steps/p-proofread.md" in rendered
    assert ".aw/system/workflows/plan-review/steps/t-tier.md" in rendered
    assert "- Kind: child" in rendered
    assert "[ISOLATION NOTICE]" in rendered

    # Re-ask wording
    reask = review_sequence.render_reask(
        "P", "The structural preservation check passes."
    )
    expected = (
        "Your last reply did not complete P: The structural preservation check passes. "
        "Complete it now and end your reply as the step file requires."
    )
    assert reask == expected


def test_postcondition_P() -> None:
    """V-03: check_P verifies ### Proofreading in current round."""
    good_review = """## Round 1

### Proofreading
No issues found.
"""
    bad_review = """## Round 1

### Step T
AW-TIER: standard
"""
    assert review_sequence.check_P(SAMPLE_PLAN, SAMPLE_PLAN, good_review, "") is None
    res = review_sequence.check_P(SAMPLE_PLAN, SAMPLE_PLAN, bad_review, "")
    assert res is not None
    assert "### Proofreading" in res


def test_postcondition_T() -> None:
    """V-03: check_T verifies AW-TIER marker and 5 answers."""
    good_reply = "I completed the assessment.\n\nAW-TIER: standard"
    good_review = """## Round 1

### Step T
1. No
2. No
3. No
4. Yes, listed
5. No
"""
    assert (
        review_sequence.check_T(SAMPLE_PLAN, SAMPLE_PLAN, good_review, good_reply)
        is None
    )

    # Missing marker
    bad_reply = "I think it is standard."
    res = review_sequence.check_T(SAMPLE_PLAN, SAMPLE_PLAN, good_review, bad_reply)
    assert res is not None
    assert "AW-TIER:" in res

    # Missing answer 5
    incomplete_review = """## Round 1

### Step T
1. No
2. No
3. No
4. Yes, listed
"""
    res2 = review_sequence.check_T(
        SAMPLE_PLAN, SAMPLE_PLAN, incomplete_review, good_reply
    )
    assert res2 is not None
    assert "answers all five tier questions" in res2


def test_postcondition_steps() -> None:
    """V-03: check_steps verifies ### Step <check> with - Checked: line."""
    good_review = """## Round 1

### Step R1
- Checked: citations in ## Scope and ## Proposed changes.
All citations valid.

### Step R2
- Checked: E/V bijection and evidence demands.
No issues.
"""
    assert (
        review_sequence.check_steps(
            SAMPLE_PLAN, SAMPLE_PLAN, good_review, "", checks=("R1", "R2")
        )
        is None
    )

    # Missing R2 subsection
    bad_review_missing = """## Round 1

### Step R1
- Checked: citations.
"""
    res = review_sequence.check_steps(
        SAMPLE_PLAN, SAMPLE_PLAN, bad_review_missing, "", checks=("R1", "R2")
    )
    assert res is not None
    assert "### Step R2" in res

    # Missing - Checked: line in R2
    bad_review_unchecked = """## Round 1

### Step R1
- Checked: citations.

### Step R2
Looked at the plan, looks fine.
"""
    res2 = review_sequence.check_steps(
        SAMPLE_PLAN, SAMPLE_PLAN, bad_review_unchecked, "", checks=("R1", "R2")
    )
    assert res2 is not None
    assert "- Checked:" in res2


def test_postcondition_S5() -> None:
    """V-03: check_S5 verifies open questions Blocking/Status and unescalated findings."""
    review_with_finding = """## Round 1

### Findings
| Id | Severity | Scope | Area | Evidence | Finding | Remediation risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-01 | high | Scope | Area | Evidence | Finding detail | Low | open | Will fix |
"""
    # Plan where F-01 is not escalated
    res = review_sequence.check_S5(SAMPLE_PLAN, SAMPLE_PLAN, review_with_finding, "")
    assert res is not None
    assert "check.review-finding-unescalated" in res

    # Plan where F-01 is escalated
    escalated_plan = (
        SAMPLE_PLAN
        + """
### OQ-02: Escalated finding F-01

- Blocking: yes
- Status: open
- Finding: F-01
- Rationale: High severity finding.
"""
    )
    assert (
        review_sequence.check_S5(SAMPLE_PLAN, escalated_plan, review_with_finding, "")
        is None
    )

    # Plan with missing Status in open question
    malformed_oq_plan = SAMPLE_PLAN.replace("- Status: open\n", "")
    res2 = review_sequence.check_S5(SAMPLE_PLAN, malformed_oq_plan, "", "")
    assert res2 is not None
    assert "Blocking:" in res2 and "Status:" in res2


def test_postcondition_S7() -> None:
    """V-03: check_S7 verifies (a)/(b), exactly one verdict history entry, and lint."""
    # Conforming review finalization
    finalized_plan = SAMPLE_PLAN.replace(
        "- Status: to-review",
        "- Status: reviewed\n- Readiness: go",
    ).replace(
        "## Workflow history\n",
        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE; looks good\n",
    )
    assert (
        review_sequence.check_S7(SAMPLE_PLAN, finalized_plan, "## Round 1\n", "")
        is None
    )

    # Non-verdict progress lines are allowed and do not count toward verdict entries
    plan_with_progress = finalized_plan.replace(
        "## Workflow history\n\n",
        "## Workflow history\n\n- 2026-10-25 review progress (test): pass 2 re-ran R2\n",
    )
    assert (
        review_sequence.check_S7(SAMPLE_PLAN, plan_with_progress, "## Round 1\n", "")
        is None
    )

    # Two verdict entries added -> fails
    two_verdicts_plan = plan_with_progress.replace(
        "## Workflow history\n\n",
        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE WITH REVISIONS APPLIED\n",
    )
    res_two = review_sequence.check_S7(
        SAMPLE_PLAN, two_verdicts_plan, "## Round 1\n", ""
    )
    assert res_two is not None
    assert "Exactly one verdict-bearing history entry" in res_two

    # Missing status move -> fails
    unmoved_plan = SAMPLE_PLAN.replace(
        "## Workflow history\n",
        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
    )
    res_unmoved = review_sequence.check_S7(
        SAMPLE_PLAN, unmoved_plan, "## Round 1\n", ""
    )
    assert res_unmoved is not None
    assert "One of: (a)" in res_unmoved


def test_structural_diff() -> None:
    """V-04: structural_diff distinguishes refused vs confirm-only changes."""
    # 1. Unchanged plan
    refused, confirm = review_sequence.structural_diff(SAMPLE_PLAN, SAMPLE_PLAN)
    assert refused == []
    assert confirm == []

    # 2. Ticking an E-* checkbox -> yields 1 refused entry, 0 confirm
    ticked_e_plan = SAMPLE_PLAN.replace("- [ ] E-01", "- [x] E-01")
    refused, confirm = review_sequence.structural_diff(SAMPLE_PLAN, ticked_e_plan)
    assert len(refused) == 1
    assert "checkbox state changed" in refused[0]
    assert confirm == []

    # 3. Rewording Expected outcome -> yields 1 confirm-only entry, 0 refused
    reworded_eo_plan = SAMPLE_PLAN.replace(
        "- Expected outcome: feature is working",
        "- Expected outcome: feature is working and validated",
    )
    refused, confirm = review_sequence.structural_diff(SAMPLE_PLAN, reworded_eo_plan)
    assert refused == []
    assert len(confirm) == 1
    assert "Expected outcome changed" in confirm[0]

    # 4. Modifying front-matter -> refused
    fm_plan = SAMPLE_PLAN.replace("- Priority: medium", "- Priority: high")
    refused, _ = review_sequence.structural_diff(SAMPLE_PLAN, fm_plan)
    assert len(refused) == 1
    assert "Priority" in refused[0]

    # 5. Modifying H2 headings -> refused
    h2_plan = SAMPLE_PLAN.replace("## Goal", "## Objectives")
    refused, _ = review_sequence.structural_diff(SAMPLE_PLAN, h2_plan)
    assert any("H2 headings" in r for r in refused)

    # 6. Modifying open question Status/Blocking -> refused
    oq_plan = SAMPLE_PLAN.replace("- Blocking: no", "- Blocking: yes")
    refused, _ = review_sequence.structural_diff(SAMPLE_PLAN, oq_plan)
    assert any("Blocking" in r for r in refused)

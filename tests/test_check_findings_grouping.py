"""Behavior tests for HumanRenderer check findings severity badging, ordering, and Next deduping.

Pins observable outcomes:
1. Every finding line carries a bracketed severity badge, including records-tree (numbered) findings.
2. Every block header carries the group's severity set as bracketed badges.
3. Groups with mixed severities render their severity set in worst-first order on the header.
4. Block ordering is worst-severity-first (error < warning < info).
5. Unrecognized or empty severities sort to the worst rank (fail-safe).
6. Deterministic tie-breaking by title for blocks with equal severity rank.
7. Duplicate NextAction commands collapse to one line while preserving order.
"""

from agent_workflows.renderers import HumanRenderer
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
    NextAction,
    OutputContext,
    OutputMode,
)


def _render_human(result: CommandResult) -> str:
    renderer = HumanRenderer()
    ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
    return renderer.render(result, ctx)


def test_records_tree_numbered_finding_carries_severity_badge():
    """Verify that records-tree findings (dir_str != '') carry [SEVERITY] badge on numbered lines."""
    diag = Diagnostic(
        location=".aw/records/plans/pending/test-plan.ipd.md",
        rule="check.test-rule",
        detail="A detailed test issue",
        severity="error",
        fix="run aw test fix",
    )
    result = CommandResult(command="check", summary="1 finding", diagnostics=[diag])
    rendered = _render_human(result)

    assert "Issue: A detailed test issue [ERROR]" in rendered
    assert "1. test-plan.ipd.md [ERROR]" in rendered


def test_root_level_finding_carries_severity_badge():
    """Verify that root-level findings (empty dir_str) carry [SEVERITY] badge on hyphen lines."""
    diag = Diagnostic(
        location="README.md",
        rule="check.root-rule",
        detail="A root file issue",
        severity="warning",
        fix="run aw fix readme",
    )
    result = CommandResult(command="check", summary="1 finding", diagnostics=[diag])
    rendered = _render_human(result)

    assert "Issue: A root file issue [WARNING]" in rendered
    assert "- README.md [WARNING]" in rendered


def test_block_header_severity_set_mixed_severities():
    """Verify that a group with multiple severities shows the sorted set on the header."""
    # When title and fix match, findings group together
    diag1 = Diagnostic(
        location=".aw/records/plans/pending/p1.ipd.md",
        rule="check.mixed-rule",
        detail="A common issue detail string",
        severity="info",
        fix="common fix command",
    )
    diag2 = Diagnostic(
        location=".aw/records/plans/pending/p2.ipd.md",
        rule="check.mixed-rule",
        detail="A common issue detail string",
        severity="error",
        fix="common fix command",
    )
    result = CommandResult(
        command="check", summary="2 findings", diagnostics=[diag1, diag2]
    )
    rendered = _render_human(result)

    # Worst severity (ERROR) precedes INFO on the header line
    assert "Issue: A common issue detail string [ERROR] [INFO]" in rendered
    assert "1. p1.ipd.md [INFO]" in rendered
    assert "2. p2.ipd.md [ERROR]" in rendered


def test_block_ordering_worst_severity_first():
    """Verify that error blocks sort before warning blocks, which sort before info blocks."""
    info_diag = Diagnostic(
        location="a.md",
        rule="check.info-rule",
        detail="An informational finding",
        severity="info",
        fix="fix info",
    )
    warn_diag = Diagnostic(
        location="b.md",
        rule="check.warn-rule",
        detail="A warning finding",
        severity="warning",
        fix="fix warn",
    )
    err_diag = Diagnostic(
        location="c.md",
        rule="check.err-rule",
        detail="An error finding",
        severity="error",
        fix="fix err",
    )

    # Supply diagnostics in reverse order (info, warning, error)
    result = CommandResult(
        command="check",
        summary="3 findings",
        diagnostics=[info_diag, warn_diag, err_diag],
    )
    rendered = _render_human(result)

    pos_err = rendered.find("Issue: An error finding [ERROR]")
    pos_warn = rendered.find("Issue: A warning finding [WARNING]")
    pos_info = rendered.find("Issue: An informational finding [INFO]")

    assert pos_err != -1
    assert pos_warn != -1
    assert pos_info != -1
    assert pos_err < pos_warn < pos_info


def test_unrecognized_or_empty_severity_sorts_to_worst():
    """Verify that unknown or empty severities sort to rank 0 (worst), preceding info and warning."""
    info_diag = Diagnostic(
        location="a.md",
        rule="check.info-rule",
        detail="Info issue",
        severity="info",
        fix="fix info",
    )
    warn_diag = Diagnostic(
        location="b.md",
        rule="check.warn-rule",
        detail="Warn issue",
        severity="warning",
        fix="fix warn",
    )
    empty_diag = Diagnostic(
        location="c.md",
        rule="check.empty-rule",
        detail="Empty severity issue",
        severity="",
        fix="fix empty",
    )
    custom_diag = Diagnostic(
        location="d.md",
        rule="check.custom-rule",
        detail="Custom severity issue",
        severity="advisory",
        fix="fix custom",
    )

    result = CommandResult(
        command="check",
        summary="4 findings",
        diagnostics=[info_diag, warn_diag, empty_diag, custom_diag],
    )
    rendered = _render_human(result)

    pos_custom = rendered.find("Issue: Custom severity issue [ADVISORY]")
    pos_empty = rendered.find("Issue: Empty severity issue []")
    pos_warn = rendered.find("Issue: Warn issue [WARNING]")
    pos_info = rendered.find("Issue: Info issue [INFO]")

    assert pos_custom != -1
    assert pos_empty != -1
    assert pos_warn != -1
    assert pos_info != -1

    # Both custom and empty sort before warning (rank 1) and info (rank 2)
    assert pos_custom < pos_warn
    assert pos_empty < pos_warn
    assert pos_warn < pos_info


def test_deterministic_ordering_by_title_within_same_severity():
    """Verify that blocks with identical severity rank are sorted alphabetically by title."""
    diag_z = Diagnostic(
        location="z.md",
        rule="check.z-rule",
        detail="Z issue",
        severity="error",
        fix="fix z",
    )
    diag_a = Diagnostic(
        location="a.md",
        rule="check.a-rule",
        detail="A issue",
        severity="error",
        fix="fix a",
    )

    result = CommandResult(
        command="check", summary="2 findings", diagnostics=[diag_z, diag_a]
    )
    rendered = _render_human(result)

    pos_a = rendered.find("Issue: A issue [ERROR]")
    pos_z = rendered.find("Issue: Z issue [ERROR]")

    assert pos_a != -1 and pos_z != -1
    assert pos_a < pos_z


def test_duplicate_next_action_commands_collapse():
    """Verify that duplicate NextAction commands are deduplicated in human render."""
    next_actions = [
        NextAction(command="aw check --help", description="help description"),
        NextAction(command="aw group plans x --set y", description="regroup"),
        NextAction(command="aw check --help", description="duplicate help command"),
        NextAction(command="aw doctor", description="run doctor"),
        NextAction(command="aw doctor", description="duplicate doctor"),
    ]
    result = CommandResult(
        command="check",
        summary="Check summary",
        next_actions=next_actions,
    )
    rendered = _render_human(result)

    lines = [line for line in rendered.splitlines() if line.startswith("Next")]
    assert len(lines) == 3
    assert "aw check --help" in lines[0]
    assert "help description" in lines[0]
    assert "aw group plans x --set y" in lines[1]
    assert "aw doctor" in lines[2]

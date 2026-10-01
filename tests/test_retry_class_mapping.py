"""Tests pinning retry classification derivation, coverage, and predicate agreement.

Per spec 25kzda Section 5.5 and IPD 4gx141 (backlog rb4wgj):
- TURN_RETRYABLE_DISPOSITIONS must be derived from TURN_RETRY_CLASSIFICATION.
- Every member of KNOWN_ITEM_STATUSES and both drivers' TERMINAL_STATES must be
  covered by TURN_RETRY_CLASSIFICATION (one-directional coverage, not a bijection).
- turn_failure_is_retryable must agree with the table's retryable flags.
"""

from agent_workflows import agy_runipd, oc_runipd
from agent_workflows.runner_shared import (
    TURN_RETRY_CLASSIFICATION,
    TURN_RETRYABLE_DISPOSITIONS,
    turn_failure_is_retryable,
)
from agent_workflows.runner_shutdown import KNOWN_ITEM_STATUSES


def test_derivation_is_single_source_of_truth() -> None:
    """The allowlist frozenset must match the comprehension over the table."""
    expected = frozenset(
        name for name, retryable, _ in TURN_RETRY_CLASSIFICATION if retryable
    )
    assert TURN_RETRYABLE_DISPOSITIONS == expected


def test_vocabulary_coverage_is_one_directional() -> None:
    """Every known item status and terminal state must have a row in the table.

    This invariant is strictly ONE-DIRECTIONAL:
    (KNOWN_ITEM_STATUSES | oc_TERMINAL_STATES | agy_TERMINAL_STATES) <= table.
    It is NOT a bijection or equality. The table intentionally contains rows like
    'merge-unchecked' and 'unknown_outcome' which are not members of KNOWN_ITEM_STATUSES
    or TERMINAL_STATES. A classified disposition that no vocabulary lists is harmless,
    whereas an unclassified status in the driver vocabulary would fail closed with an
    uninformative 'has no entry' reason instead of a deliberate verdict.
    """
    table_statuses = {name for name, _, _ in TURN_RETRY_CLASSIFICATION}
    required_statuses = (
        set(KNOWN_ITEM_STATUSES)
        | set(oc_runipd.TERMINAL_STATES)
        | set(agy_runipd.TERMINAL_STATES)
    )

    uncovered = required_statuses - table_statuses
    assert not uncovered, f"Vocabularies contain statuses with no row in TURN_RETRY_CLASSIFICATION: {sorted(uncovered)}"

    # Confirm the one-directional property holds: extra table rows do not fail the test
    assert "merge-unchecked" in table_statuses
    assert "unknown_outcome" in table_statuses
    assert "merge-unchecked" not in required_statuses
    assert "unknown_outcome" not in required_statuses


def test_predicate_agrees_with_table() -> None:
    """turn_failure_is_retryable must agree with each row's retryable flag."""
    for name, retryable, _why in TURN_RETRY_CLASSIFICATION:
        verdict, reason = turn_failure_is_retryable({}, name)
        assert (
            verdict == retryable
        ), f"disposition {name!r}: expected {retryable}, got {verdict} (reason: {reason})"
        assert not (
            "is not retryable" in reason and reason.rstrip().endswith("retryable")
        ), f"disposition {name!r} returned self-contradicting reason: {reason}"

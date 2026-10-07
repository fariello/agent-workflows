"""Behavioral baseline and post-hoist validation for refuse_unsafe_descriptive (IPD 685iq8).

Tests observable behavior and return values across all five helper routes:
- attention_contract.refuse_unsafe_descriptive (public hoisted owner)
- backlog._refuse_unsafe_descriptive (retained delegating alias)
- specs._refuse_unsafe_descriptive (retained delegating alias)
- status_set._refuse_unsafe_descriptive (retained delegating alias)
- research_cmd._refuse_unsafe_descriptive (retained delegating alias)

Does not inspect source or assert on code structure.
"""

import argparse
from typing import Optional
import pytest

from agent_workflows import (
    attention_contract,
    backlog,
    releases,
    research_cmd,
    specs,
    status_set,
)

FLAG = "--test-flag"

VAL_NONE = None
VAL_OK = "ok"
VAL_EMPTY = ""
VAL_NEWLINE = "a\nb"
VAL_CR = "a\rb"
VAL_BELL = "a\x07b"
VAL_LEN340 = "x" * 340
VAL_LEN1200 = "x" * 1200
VAL_LATE_CTRL = "a" * 500 + "\x07" + "b"

TEST_VALUES = [
    VAL_NONE,
    VAL_OK,
    VAL_EMPTY,
    VAL_NEWLINE,
    VAL_CR,
    VAL_BELL,
    VAL_LEN340,
    VAL_LEN1200,
    VAL_LATE_CTRL,
]

REAL_NONEMPTY_VERBS = [
    "aw backlog new",
    "aw backlog set",
    "aw backlog note",
    "aw specs set",
    "aw specs new",
    "aw specs note",
    "aw set",
    "aw research new",
    "aw research new-comparison",
    "aw research set-outcome",
]

# 18-row literal table of (bound_length, value) -> expected SUFFIX
# Captured from the unmodified specs copy with verb="" and flag="--test-flag".
FROZEN_SUFFIX_TABLE = {
    # bound_length=True
    (True, VAL_NONE): None,
    (True, VAL_OK): None,
    (True, VAL_EMPTY): None,
    (True, VAL_NEWLINE): "--test-flag must not contain embedded newlines",
    (True, VAL_CR): "--test-flag must not contain embedded newlines",
    (True, VAL_BELL): "--test-flag must not contain control characters",
    (
        True,
        VAL_LEN340,
    ): "--test-flag exceeds maximum length of 300 characters (340 > 300)",
    (
        True,
        VAL_LEN1200,
    ): "--test-flag exceeds maximum length of 300 characters (1200 > 300)",
    (True, VAL_LATE_CTRL): "--test-flag must not contain control characters",
    # bound_length=False
    (False, VAL_NONE): None,
    (False, VAL_OK): None,
    (False, VAL_EMPTY): None,
    (False, VAL_NEWLINE): "--test-flag must not contain embedded newlines",
    (False, VAL_CR): "--test-flag must not contain embedded newlines",
    (False, VAL_BELL): "--test-flag must not contain control characters",
    (False, VAL_LEN340): None,
    (False, VAL_LEN1200): None,
    (False, VAL_LATE_CTRL): "--test-flag must not contain control characters",
}

ALL_FIVE_ROUTES = [
    ("attention_contract", attention_contract.refuse_unsafe_descriptive),
    ("backlog", backlog._refuse_unsafe_descriptive),
    ("specs", specs._refuse_unsafe_descriptive),
    ("status_set", status_set._refuse_unsafe_descriptive),
    ("research_cmd", research_cmd._refuse_unsafe_descriptive),
]


def test_public_hoisted_helper_exists():
    """Verify refuse_unsafe_descriptive exists and is public in attention_contract."""
    assert callable(attention_contract.refuse_unsafe_descriptive)
    assert not hasattr(attention_contract, "_refuse_unsafe_descriptive")


@pytest.mark.parametrize("route_name,route_fn", ALL_FIVE_ROUTES)
@pytest.mark.parametrize("verb", REAL_NONEMPTY_VERBS)
@pytest.mark.parametrize("bound_length", [True, False])
@pytest.mark.parametrize("val", TEST_VALUES)
def test_all_five_routes_match_frozen_table_for_nonempty_verbs(
    route_name: str, route_fn, verb: str, bound_length: bool, val: Optional[str]
):
    """Every route must match the frozen literal table for all nonempty verbs."""
    expected_suffix = FROZEN_SUFFIX_TABLE[(bound_length, val)]
    expected_msg = f"{verb}: {expected_suffix}" if expected_suffix is not None else None

    actual = route_fn(verb, FLAG, val, bound_length=bound_length)
    assert actual == expected_msg


@pytest.mark.parametrize("route_name,route_fn", ALL_FIVE_ROUTES)
@pytest.mark.parametrize("bound_length", [True, False])
@pytest.mark.parametrize("val", TEST_VALUES)
def test_all_five_routes_match_frozen_table_for_empty_verb(
    route_name: str, route_fn, bound_length: bool, val: Optional[str]
):
    """Post-hoist pin: every route emits UNPREFIXED message for empty verb.

    Replaces pre-hoist divergence test. The empty verb yields exactly suffix
    with no leading ': ' separator from all five routes.
    """
    expected_suffix = FROZEN_SUFFIX_TABLE[(bound_length, val)]
    actual = route_fn("", FLAG, val, bound_length=bound_length)
    assert actual == expected_suffix


@pytest.mark.parametrize("route_name,route_fn", ALL_FIVE_ROUTES)
def test_bound_length_asymmetry_survived(route_name: str, route_fn):
    """Pin that bound_length asymmetry survived across all five routes (zllcnv design point).

    A 340-character value returns a length-naming message under bound_length=True
    and None under bound_length=False.
    A 1200-character value also returns length-naming under bound_length=True and None under bound_length=False.
    A late control character ('a'*500 + '\x07' + 'b') returns control character refusal in both modes.
    """
    verb = "aw test"
    # 340 characters
    bounded_340 = route_fn(verb, FLAG, VAL_LEN340, bound_length=True)
    unbounded_340 = route_fn(verb, FLAG, VAL_LEN340, bound_length=False)
    assert (
        bounded_340
        == f"{verb}: --test-flag exceeds maximum length of 300 characters (340 > 300)"
    )
    assert unbounded_340 is None

    # 1200 characters
    bounded_1200 = route_fn(verb, FLAG, VAL_LEN1200, bound_length=True)
    unbounded_1200 = route_fn(verb, FLAG, VAL_LEN1200, bound_length=False)
    assert (
        bounded_1200
        == f"{verb}: --test-flag exceeds maximum length of 300 characters (1200 > 300)"
    )
    assert unbounded_1200 is None

    # Late control character past 300 chars: refused in BOTH modes
    bounded_late = route_fn(verb, FLAG, VAL_LATE_CTRL, bound_length=True)
    unbounded_late = route_fn(verb, FLAG, VAL_LATE_CTRL, bound_length=False)
    assert bounded_late == f"{verb}: --test-flag must not contain control characters"
    assert unbounded_late == f"{verb}: --test-flag must not contain control characters"


def test_releases_run_new_cli_empty_verb_single_prefix(tmp_path, capsys):
    """End-to-end CLI assertion: releases.run_new emits exactly one ': ' separator.

    Validates that releases.run_new passing verb='' does not produce a doubled colon.
    """
    args = argparse.Namespace(
        dir=str(tmp_path),
        version="a\nstatus: shipped",
        summary="x",
        status="planned",
        no_color=True,
        color=False,
        no_interactive=True,
        interactive=False,
        agent=False,
        json=False,
        fields=None,
        verbose=False,
        apply=False,
    )
    rc = releases.run_new(args)
    assert rc == 2
    captured = capsys.readouterr()
    expected_line = "aw releases new: --version must not contain embedded newlines\n"
    assert captured.err == expected_line
    # Confirm single ': ' separator after 'aw releases new'
    prefix = "aw releases new: "
    assert captured.err.startswith(prefix)
    rest = captured.err[len(prefix) :]
    assert not rest.startswith(": ")

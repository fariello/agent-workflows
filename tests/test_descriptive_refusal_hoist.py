"""Behavioral baseline and post-hoist validation for refuse_unsafe_descriptive (IPD 685iq8, 83nnyn).

Tests observable behavior and return values across all five helper routes:
- attention_contract.refuse_unsafe_descriptive (public hoisted owner)
- backlog._refuse_unsafe_descriptive (retained delegating alias)
- specs._refuse_unsafe_descriptive (retained delegating alias)
- status_set._refuse_unsafe_descriptive (retained delegating alias)
- research_cmd._refuse_unsafe_descriptive (retained delegating alias)

Tabulated accumulate test (P16): case id first, expected literal, trailing why.
Does not inspect source or assert on code structure.
"""

import argparse
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
VAL_LEN300 = "x" * 300
VAL_LEN301 = "x" * 301
VAL_LEN340 = "x" * 340
VAL_LEN1200 = "x" * 1200
VAL_LATE_CTRL = "a" * 500 + "\x07" + "b"

REPRESENTATIVE_VERB = "aw backlog new"

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

# Literal suffixes for (bound_length, val_label, value)
# Captured from unmodified specs copy with verb="" and flag="--test-flag".
VALUE_SPECS = [
    ("val_none", VAL_NONE, None, None, "None descriptive value is always accepted"),
    ("val_ok", VAL_OK, None, None, "simple safe string accepted"),
    ("val_empty", VAL_EMPTY, None, None, "empty string accepted"),
    (
        "val_newline",
        VAL_NEWLINE,
        "--test-flag must not contain embedded newlines",
        "--test-flag must not contain embedded newlines",
        "embedded newline rejected in both modes",
    ),
    (
        "val_cr",
        VAL_CR,
        "--test-flag must not contain embedded newlines",
        "--test-flag must not contain embedded newlines",
        "embedded carriage return rejected in both modes",
    ),
    (
        "val_bell",
        VAL_BELL,
        "--test-flag must not contain control characters",
        "--test-flag must not contain control characters",
        "control bell rejected in both modes",
    ),
    (
        "val_len300",
        VAL_LEN300,
        None,
        None,
        "exact 300 char boundary accepted in both modes",
    ),
    (
        "val_len301",
        VAL_LEN301,
        "--test-flag exceeds maximum length of 300 characters (301 > 300)",
        None,
        "301 char boundary rejected only when bound_length=True",
    ),
    (
        "val_len340",
        VAL_LEN340,
        "--test-flag exceeds maximum length of 300 characters (340 > 300)",
        None,
        "340 char overlength rejected only when bound_length=True",
    ),
    (
        "val_len1200",
        VAL_LEN1200,
        "--test-flag exceeds maximum length of 300 characters (1200 > 300)",
        None,
        "1200 char overlength rejected only when bound_length=True",
    ),
    (
        "val_late_ctrl",
        VAL_LATE_CTRL,
        "--test-flag must not contain control characters",
        "--test-flag must not contain control characters",
        "late control char past bound rejected in both modes",
    ),
]

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


def test_refuse_unsafe_descriptive_accumulate_table():
    """Table-driven accumulate test across all five routes, boundary cases, and verbs."""
    failures = []

    # 1. Every route x representative verb + empty verb x bound_length True/False x every value spec (including 300/301 boundary)
    verbs_to_test = [
        ("rep_verb", REPRESENTATIVE_VERB),
        ("empty_verb", ""),
    ]

    for route_name, route_fn in ALL_FIVE_ROUTES:
        for verb_label, verb in verbs_to_test:
            for bound_length in [True, False]:
                bound_label = "bound_true" if bound_length else "bound_false"
                for (
                    val_label,
                    val,
                    expected_suffix_true,
                    expected_suffix_false,
                    why,
                ) in VALUE_SPECS:
                    suffix = (
                        expected_suffix_true if bound_length else expected_suffix_false
                    )
                    expected_msg = (
                        f"{verb}: {suffix}" if (verb and suffix is not None) else suffix
                    )
                    case_id = (
                        f"hoist-{route_name}-{verb_label}-{bound_label}-{val_label}"
                    )

                    actual = route_fn(verb, FLAG, val, bound_length=bound_length)
                    if actual != expected_msg:
                        failures.append(
                            f"[{case_id}] route={route_name} verb={verb!r} bound={bound_length} "
                            f"val_label={val_label} expected={expected_msg!r} got={actual!r} why={why}"
                        )

    # 2. Every verb in REAL_NONEMPTY_VERBS against one rejecting value (VAL_NEWLINE, bound_length=True)
    for route_name, route_fn in ALL_FIVE_ROUTES:
        for verb in REAL_NONEMPTY_VERBS:
            verb_slug = verb.replace(" ", "_").replace("-", "_")
            case_id = f"hoist-{route_name}-verb_{verb_slug}-bound_true-val_newline"
            expected_msg = f"{verb}: --test-flag must not contain embedded newlines"
            why = "every verb renders prefix on rejection"

            actual = route_fn(verb, FLAG, VAL_NEWLINE, bound_length=True)
            if actual != expected_msg:
                failures.append(
                    f"[{case_id}] route={route_name} verb={verb!r} bound=True "
                    f"expected={expected_msg!r} got={actual!r} why={why}"
                )

    if failures:
        pytest.fail(
            f"{len(failures)} descriptive refusal case(s) failed:\n"
            + "\n".join(failures)
        )


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

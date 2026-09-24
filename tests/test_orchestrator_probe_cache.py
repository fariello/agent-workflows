"""orchprobe Order 02 (`8tgg6g`): the orchestrator probe verdict cache, keyed on content.

WHAT THIS PINS, and why each half exists rather than merely that it does.

E-01/V-01, ONE ROW-WALK SHARED WITH THE RETIREMENT GATE. `runner_shared` already owned a child-table
row scanner (`parse_declared_child_orders`) that found the section by schema heading, matched rows,
skipped the alignment row, and then discarded every cell but the first. The cache needs the SAME rows
with ALL their cells, so the walk is factored into `child_table_rows` and both callers use it; a
second scanner would give the gate and the cache two definitions of "a child row". The splitter is a
PARAMETER because the two consumers legitimately need different ones: an all-cells digest must be
backtick-aware (a backticked pipe fragments later columns), while the gate reads only cell 0, which
is measured identical under both splitters, so its behavior is left bit-for-bit unchanged.

E-02/E-03/V-02/V-03, THE DIGEST AND THE `xmqv5l` TRAP. The naive key is a whole-file hash and this
repository already MEASURED that as a dead end: `ipd_lifecycle.frozen_region_digest` exists because
hashing exact bytes made a begin receipt go stale on every CORRECT execution, since a conforming
executor MUST tick checkboxes, fill `Observed evidence` and append history. So the no-op mutations
below are the load-bearing half: five edits a correct executor makes, each asserted NOT to move the
digest.

THE CONTRAST TESTS ARE THE POINT, not decoration. Four of the five properties this digest needs
ALREADY hold for `frozen_region_digest`; the ONLY thing it adds is CHILD-TABLE SENSITIVITY. So
`TheDigestDiffersFromFrozenRegionDigest` asserts the existing function does NOT move on the same
child-table edits (which is why a second function exists at all), and `TheKeyIsRowTextNotTheOrderGraph`
asserts `ipd_set_plan.parse_child_table(...).rows` is BYTE-IDENTICAL for an Id swap and a description
rewrite (which is why the key must be row TEXT). A proof that omitted those two cases could not tell
a correct implementation from the broken one, because the obvious fixture ADDS a row and a row add is
the one child-table edit BOTH keys detect.

E-04/E-05/E-06/V-04/V-05/V-06, THE STORE AND ITS TWO GUARDS. A MISS is `unknown`, never `pass`: "not
probed" and "probed and cleared" are different facts and the whole gate rests on silence no longer
meaning safe. Both polarities are cached per the maintainer's OQ-01 ruling, and
`AStaleFailCannotBeServed` is the fixture that ruling specified: apply the real remedy (move the work
into a new child, editing BOTH the checklist and the child table) and the digest MOVES, so the fail
entry is discarded rather than re-served.

FIXTURES ARE FROZEN, DELIBERATELY. Every orchestrator text below is built in this module. Pinning to
live plan files is what broke `tests/test_orchestrator_retirement.py::RealRepositorySets` (a test
asserting a plan's mutable `- Status:`), and this Set's own orchestrator forbids repeating it. The
real-corpus measurements this child owes are recorded as pasted evidence in the IPD, not as asserts
against files that change under the suite.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import ipd_lifecycle, ipd_set_plan
from agent_workflows import runner_shared as rs
from tests.support import REPO_ROOT

# ==================================================================================================
# The frozen orchestrator fixture
# ==================================================================================================
#
# Shaped after a REAL orchestrator (`yeh7gc`): a metadata block, a `## Workflow history`, an E-item
# with the sub-fields a conforming executor mutates, a prose section, and a `## Child IPDs...`
# section carrying BOTH a table and explanatory paragraphs beside it. Each of those is a mutation
# target below, so the fixture has to contain all of them.

FIXTURE = """\
# IPD: frozen orchestrator fixture

- Date: 2026-09-14
- Kind: orchestrator
- Concern: synthetic fixture for the probe cache digest.
- Scope: synthetic.
- Scope-Paths: agent_workflows/runner_shared.py
- Status: approved
- Set: fixture
- Order: 0
- Highest E allocated: 02
- Id: fix000

## Workflow history

- 2026-09-14 draft (fixture): created.

## Goal

Give the digest tests something with every mutable region a real orchestrator has.

## Detailed Implementation Checklist (TODO)

### Task group 1: sequence the Set

- [ ] E-01 SEQUENCE THE THREE CHILDREN IN ORDER, confirming each is executed before the next.
  - Depends on: none
  - Expected outcome: all children executed in order.
  - Execution state: pending

- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.
  - Depends on: E-01
  - Expected outcome: records reconciled.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

All children are AUTHORED and lint conforming. There are NO placeholder rows.

| Order | Id | Child plan | Depends on |
| --- | --- | --- | --- |
| 01 | aaa111 | Surface the refusal reason and its remedy | none |
| 02 | bbb222 | Cache the verdict against a content digest | none |
| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |

Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set.

Order 02 is independent of 01 and could run in parallel.

## Findings

| Id | Severity | Finding |
| --- | --- | --- |
| F-1 | HIGH | A whole-file digest punishes correct execution. |

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: paste the children's statuses.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the reconciled records.
  - Observed evidence:
  - Result: pending
"""


# ---- the five NO-OP mutations (what a conforming executor does) -----------------------------------


def tick_a_checkbox(text: str) -> str:
    """Mark E-01 performed, which every conforming executor must do."""
    return text.replace("- [ ] E-01 SEQUENCE", "- [x] E-01 SEQUENCE")


def fill_observed_evidence(text: str) -> str:
    """Fill V-01's `Observed evidence`, which every conforming executor must do."""
    return text.replace(
        "  - Required evidence: paste the children's statuses.\n  - Observed evidence:\n",
        "  - Required evidence: paste the children's statuses.\n"
        "  - Observed evidence: all three read `- Status: executed` (pasted output here).\n",
    )


def append_a_history_line(text: str) -> str:
    """Append a `## Workflow history` line, which every conforming executor must do."""
    return text.replace(
        "- 2026-09-14 draft (fixture): created.",
        "- 2026-09-14 draft (fixture): created.\n"
        "- 2026-09-14 executed (fixture): performed E-01 and E-02.",
    )


def edit_prose_outside_the_child_section(text: str) -> str:
    """Rewrite a prose section (`## Findings`), which is not part of the reviewed contract."""
    return text.replace(
        "| F-1 | HIGH | A whole-file digest punishes correct execution. |",
        "| F-1 | HIGH | COMPLETELY REWRITTEN FINDING TEXT WITH DIFFERENT WORDS. |",
    )


def edit_prose_inside_the_child_section(text: str) -> str:
    """Rewrite the explanatory paragraphs that sit INSIDE `## Child IPDs...`, beside its table.

    Pins rows-not-section: including that prose would reintroduce exactly the prose sensitivity
    `frozen_region_digest` deliberately excludes.
    """
    return text.replace(
        "Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set.",
        "TOTALLY DIFFERENT EXPLANATORY PARAGRAPH SAYING SOMETHING ELSE ENTIRELY ABOUT ORDERING.",
    )


NO_OP_MUTATIONS = {
    "tick-a-checkbox": tick_a_checkbox,
    "fill-observed-evidence": fill_observed_evidence,
    "append-a-history-line": append_a_history_line,
    "edit-prose-outside-the-child-section": edit_prose_outside_the_child_section,
    "edit-prose-inside-the-child-section": edit_prose_inside_the_child_section,
}


# ---- the four REAL edits (a different plan than the one that was probed) --------------------------


def edit_an_e_item_action(text: str) -> str:
    """Change what E-02 ASKS FOR, which is a different question for the probe."""
    return text.replace(
        "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.",
        "- [ ] E-02 PRODUCE the migration research artifact before any child runs.",
    )


def add_a_child_row(text: str) -> str:
    """Add a fourth child row (the edit a parsed-order-graph key ALSO catches)."""
    return text.replace(
        "| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |",
        "| 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |\n"
        "| 04 | ddd444 | Reconcile the Set's records | executed:ccc333 |",
    )


def swap_a_child_id(text: str) -> str:
    """Swap a child's Id (INVISIBLE to a parsed-order-graph key; measured on `yeh7gc`)."""
    return text.replace("| 02 | bbb222 |", "| 02 | qqqqqq |")


def rewrite_a_child_description(text: str) -> str:
    """Rewrite a child's description (INVISIBLE to a parsed-order-graph key; measured)."""
    return text.replace(
        "| 02 | bbb222 | Cache the verdict against a content digest | none |",
        "| 02 | bbb222 | TOTALLY REWRITTEN: do something completely different | none |",
    )


REAL_EDITS = {
    "edit-an-e-item-action": edit_an_e_item_action,
    "add-a-child-row": add_a_child_row,
    "swap-a-child-id": swap_a_child_id,
    "rewrite-a-child-description": rewrite_a_child_description,
}

#: The two child-table edits a parsed-order-graph key CANNOT see. Named because three tests depend on
#: exactly this pair and a hand-repeated list would drift.
ROW_CONTENT_EDITS = ("swap-a-child-id", "rewrite-a-child-description")


class _Repo:
    """A throwaway directory used as a repo root (no git init: `checkout_control_root` falls back)."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()


class RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = _Repo()
        self.addCleanup(self._repo.close)

    @property
    def root(self) -> Path:
        return self._repo.root


# ==================================================================================================
# E-01: ONE shared row-walk, returning full cell tuples
# ==================================================================================================


class ChildTableRowsTests(unittest.TestCase):
    """`child_table_rows` returns FULL cells, in document order, header included.

    ONE table replaces four tests that each called `child_table_rows` on one text and asserted the
    rows. The text is the only thing that varied, so it is the column, and the expectation is the FULL
    tuple rather than a property of it: an exact-equality row states the cell text, the cell COUNT, the
    document ORDER, the header's inclusion and the alignment row's exclusion all at once, and each of
    the four old tests asserted only one of those. This is the payload the digest hashes and the probe
    reads, so under-specifying it is how an edit becomes invisible to the cache.
    """

    _FULL_FIXTURE_ROWS = (
        ("Order", "Id", "Child plan", "Depends on"),
        ("01", "aaa111", "Surface the refusal reason and its remedy", "none"),
        ("02", "bbb222", "Cache the verdict against a content digest", "none"),
        (
            "03",
            "ccc333",
            "Probe every queued orchestrator",
            "executed:aaa111, executed:bbb222",
        ),
    )

    #: (case, the orchestrator text, the exact rows expected, why this row exists)
    WALKS = (
        (
            "the frozen fixture's child table",
            FIXTURE,
            _FULL_FIXTURE_ROWS,
            "THE WHOLE CONTRACT IN ONE EQUALITY, and each clause of it is load-bearing for a different "
            "reason. ALL CELLS, because a walk that kept only cell 0 is what this function was "
            "extracted from and the digest needs the rest. DOCUMENT ORDER, because a table's order is "
            "part of what it says, so sorting here would make a reordering invisible to the cache. THE "
            "HEADER ROW INCLUDED, which is deliberate and surprising: it makes a COLUMN RENAME move the "
            "digest, and the five live layouts share only their first column so a header change is a "
            "real signal. THE ALIGNMENT ROW EXCLUDED, because `|---|:--:|` is layout, so reformatting a "
            "table must not invalidate a cached verdict. AND the `## Findings` table above it "
            "contributes NOTHING, which is the section scoping: were it included, editing an unrelated "
            "findings row would serve a re-probe for no reason",
        ),
        (
            "a document with no child-IPDs section at all",
            "# IPD: no table here\n",
            (),
            "AN ABSENT SECTION YIELDS NO ROWS RATHER THAN RAISING. A child plan legitimately has no "
            "child table, and both callers run over every queued plan, so an exception here would fail "
            "a whole run on an ordinary document",
        ),
        (
            "the empty string",
            "",
            (),
            "THE DEGENERATE INPUT, kept because an unreadable or empty plan file reaches this by the "
            "same path and the two callers differ in how defensively they read text",
        ),
        (
            "the section heading present but carrying no table",
            f"## {rs._CHILD_IPDS_HEADING}\n\nAll children are authored. No table yet.\n",
            (),
            "PROSE IN THE RIGHT SECTION IS NOT A ROW. This is the shape the retirement gate must read "
            "as `parsed=False` and REFUSE on, so it must not be mistaken for an empty-but-valid table; "
            "the gate's own handling of it is asserted separately, but the walk must report nothing "
            "here for that to be reachable",
        ),
    )

    def test_the_row_walk_returns_exactly_the_declared_child_rows(self):
        wrong = []
        for case, text, expected, why in self.WALKS:
            got = rs.child_table_rows(text)
            if got != expected:
                wrong.append(
                    f"  {case}:\n    - expected {expected!r}\n    -      got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the shared row walk returned the wrong rows for {len(wrong)} of {len(self.WALKS)} "
            "documents. THESE ROWS ARE BOTH A CACHE KEY AND A PROBE PAYLOAD, so the two failure "
            "directions are opposite and both bad: rows that STOP appearing (a dropped cell, a "
            "narrowed section scope) make a real edit invisible and serve a stale verdict under "
            "apparent authority, while rows that START appearing (the alignment row, another section's "
            "table) invalidate cached verdicts on reformatting and cost a re-probe per orchestrator. "
            "If the three EMPTY rows failed together, the walk stopped tolerating a document with no "
            "child table, which raises inside a loop over every queued plan. FIX: both consumers read "
            "this ONE function (asserted below), so a change here changes the retirement gate too.\n"
            + "\n".join(wrong),
        )

    def test_a_backticked_pipe_does_NOT_fragment_the_row(self):
        """The measured live defect: three real orchestrators carry a backticked pipe.

        `94dhrt`, `mvz3d2` and `rreixg` each contain such a row, one splitting 12 cells instead of 4
        under the naive splitter. Harmless when only cell 0 is read; NOT harmless for an all-cells
        digest, where a backticked plan filename would fragment into bogus columns.
        """

        text = (
            f"## {rs._CHILD_IPDS_HEADING}\n\n"
            "| Order | Id | Child plan | Depends on |\n"
            "| --- | --- | --- | --- |\n"
            "| 01 | aaa111 | see `aw oc run | agy run` for the host split | none |\n"
        )
        aware = rs.child_table_rows(text)
        naive = rs.child_table_rows(text, backtick_aware=False)
        self.assertEqual(
            len(aware[-1]), 4, f"backtick-aware split fragmented: {aware[-1]}"
        )
        self.assertEqual(len(naive[-1]), 5, "the naive split is expected to fragment")
        self.assertEqual(
            aware[-1][0], naive[-1][0], "cell 0 must agree under both splitters"
        )


class TheRowWalkIsSharedWithTheRetirementGate(unittest.TestCase):
    """E-01: ONE definition of "a child row", consumed by the gate AND the digest.

    THREE SOURCE-TEXT PINS WERE REPLACED HERE AND THE REASONING DIFFERS PER PIN, so it is worth
    reading before re-adding any of them.

    THE TWO "CALLS THE SHARED ROW WALK" PINS searched `inspect.getsource(...)` for the substring
    `"child_table_rows("`. That is satisfied by a COMMENT or a docstring naming the helper while the
    body keeps a private scanner, which is EXACTLY the fork the pin existed to prevent, and it breaks
    on a rename that changes no behavior. Note the old class docstring argued the structural form was
    chosen OVER output agreement because "two independent scanners can agree today and drift
    tomorrow" - a correct concern, but a text search does not address it either. What does: SPY on the
    shared helper (so the call is observed during a real invocation) and then replace it with a
    SENTINEL row set whose cells must appear in each consumer's output. A private scanner produces the
    real rows and fails both.

    THE "GATE KEEPS THE NAIVE SPLIT" PIN searched for `"backtick_aware=False"` while its own docstring
    said the claim was that BEHAVIOR is unchanged. Behavior is now asserted directly, over a table of
    row shapes INCLUDING the awkward ones the two splitters genuinely disagree on. That is the part
    the implementation pin could not do and the part that matters: the shipped justification is that
    cell 0 is "measured identical under both splitters", and that is TRUE for the corpus (a backticked
    pipe in a LATER cell) but FALSE in general - a backticked pipe spanning cell 0 itself splits
    differently, measured below. So the table both protects the gate's behavior and records that the
    equivalence is corpus-specific rather than universal, which is the honest version of the claim.
    """

    def test_both_consumers_reach_the_ONE_shared_row_walk(self):
        """The gate AND the digest payload call `child_table_rows`, observed rather than grepped."""
        # 1. Each consumer CALLS it, exactly once, on the text it was given.
        for label, drive in (
            ("parse_declared_child_orders", rs.parse_declared_child_orders),
            ("probe_cache_payload", rs.probe_cache_payload),
        ):
            with self.subTest(consumer=label):
                with mock.patch.object(
                    rs, "child_table_rows", wraps=rs.child_table_rows
                ) as spy:
                    drive(FIXTURE)
                self.assertEqual(
                    spy.call_count,
                    1,
                    f"{label} called the shared row walk {spy.call_count} times; it must call it "
                    "exactly ONCE. Zero means it keeps a private scanner, so the retirement gate and "
                    "the cache would hold two definitions of `a child row` (the `2r306y`/`818uru` "
                    "failure class).",
                )
                self.assertEqual(spy.call_args.args, (FIXTURE,))

        # 2. And the shared walk's OUTPUT is what each consumer reads. These sentinel rows exist in no
        #    source file, so no substring search could ever establish this.
        sentinel_rows = (
            ("Order", "Id", "Child plan", "Depends on"),
            ("SENTINEL-ORDER-A", "sentaa", "planted row A", "none"),
            ("SENTINEL-ORDER-B", "sentbb", "planted row B", "none"),
        )
        with mock.patch.object(rs, "child_table_rows", lambda _t, **_k: sentinel_rows):
            tokens, parsed = rs.parse_declared_child_orders(FIXTURE)
            payload_rows = rs.probe_cache_payload(FIXTURE)["child_table_rows"]

        self.assertEqual(
            (tokens, parsed),
            (("SENTINEL-ORDER-A", "SENTINEL-ORDER-B"), True),
            "the retirement gate's Order tokens did not come from the shared row walk, so it scans "
            "the table itself",
        )
        self.assertEqual(
            payload_rows,
            [list(row) for row in sentinel_rows],
            "the digest payload's rows did not come from the shared row walk, so the cache key "
            "covers something the gate does not see (or the reverse)",
        )

    #: (case, the single table row, the Order tokens the gate MUST return, does the backtick-aware
    #:  splitter give cell 0 a DIFFERENT value?, why this row exists)
    #:
    #: Replaces a pin on `backtick_aware=False`. The claim being protected is the gate's BEHAVIOR, so
    #: the table drives the gate and additionally records, per row, whether the two splitters actually
    #: agree on cell 0. The `differs` column is what makes this more than a regression fence: it
    #: distinguishes rows where the choice of splitter is IRRELEVANT from rows where it changes the
    #: gate's answer, and only the latter are why the gate is pinned to one splitter at all.
    ROW_SHAPES = (
        (
            "a backticked pipe in a LATER cell",
            "| 01 | aaa111 | see `aw oc run | agy run` for the host split | none |",
            ("01",),
            False,
            "THE MEASURED LIVE SHAPE: `94dhrt`, `mvz3d2` and `rreixg` each carry such a row, one "
            "splitting 12 cells instead of 4 under the naive splitter. Cell 0 is UNAFFECTED, which is "
            "the shipped justification for leaving the gate on the naive split, and this row is what "
            "keeps that justification true",
        ),
        (
            "a backticked pipe spanning cell 0 itself",
            "| `01 | 02` | aaa111 | x | none |",
            ("01",),
            True,
            "THE COUNTEREXAMPLE TO THE SHIPPED JUSTIFICATION, and the reason this table exists rather "
            "than a pin on the flag. `cell 0 is identical under both splitters` is a CORPUS "
            "measurement, not a theorem: here the naive split yields `` `01 `` (stripping to `01`) "
            "while the backtick-aware split yields `` `01 | 02` `` (stripping to `01 | 02`), which is "
            "not an Order and would never resolve. So switching the gate's splitter WOULD change its "
            "answer on this input, which is exactly what must not happen by accident during a cache "
            "change",
        ),
        (
            "a backticked pipe inside a non-numeric cell 0",
            "| `a|b` | x | y | none |",
            ("a",),
            True,
            "the same divergence with no spaces around the pipe, so the split is shown to turn on the "
            "BACKTICK SPAN and not on whitespace. The gate returns the token either way and the "
            "CALLER refuses it, which keeps this function a parser",
        ),
        (
            "a decorated token in backticks",
            "| `01` | aaa111 | x | none |",
            ("01",),
            False,
            "PROSE DECORATION IS STRIPPED: a wholly-backticked token has no interior pipe, so both "
            "splitters agree and the gate still reads `01`. Without this row the stripping could be "
            "dropped and only the divergent rows above would notice",
        ),
        (
            "a bold token",
            "| **02** | bbb222 | x | none |",
            ("02",),
            False,
            "the other decoration authors use. Same stripping rule, different characters",
        ),
        (
            "a non-numeric `03+` token",
            "| 03+ | ccc333 | x | none |",
            ("03+",),
            False,
            "MEASURED IN `rununify`: tokens are NOT all numeric. The gate must RETURN it rather than "
            "dropping or crashing on it, because the policy of refusing an unresolvable token belongs "
            "to the caller and keeping it here would put policy in two places",
        ),
        (
            "the word token `last`",
            "| last | ddd444 | x | none |",
            ("last",),
            False,
            "the other real `rununify` token. Paired with `03+` so a change that started filtering "
            "non-numeric tokens fails on both rather than looking like a one-off",
        ),
        (
            "an empty first cell",
            "|  | aaa111 | x | none |",
            (),
            False,
            "AN EMPTY CELL 0 DECLARES NO ORDER and must be skipped rather than returned as an empty "
            "token, which a caller would try to resolve. Note this row still counts as a ROW for the "
            "`parsed` flag, which the assertion below checks separately",
        ),
    )

    def test_the_gate_reads_the_same_Order_tokens_the_naive_split_gives_it(self):
        wrong = []
        real_walk = rs.child_table_rows
        for case, row, expected, differs, why in self.ROW_SHAPES:
            text = (
                f"## {rs._CHILD_IPDS_HEADING}\n\n"
                "| Order | Id | Child plan | Depends on |\n"
                "| --- | --- | --- | --- |\n"
                f"{row}\n"
            )
            problems = []
            tokens, parsed = rs.parse_declared_child_orders(text)
            if tokens != expected:
                problems.append(f"gate returned {tokens!r}, expected {expected!r}")
            if not parsed:
                problems.append(
                    "gate reported `parsed=False`, so a real table row went unrecognized and the "
                    "caller would refuse to retire a correctly-authored Set"
                )
            # The splitter-sensitivity column, measured rather than asserted in prose: force the gate
            # onto the backtick-AWARE splitter (the "tidy" a future cache change might perform) and
            # record whether its answer moves.
            with mock.patch.object(
                rs,
                "child_table_rows",
                lambda t, **_k: real_walk(t, backtick_aware=True),
            ):
                tidied, _ = rs.parse_declared_child_orders(text)
            if (tidied != tokens) != differs:
                problems.append(
                    f"the two splitters were expected to {'DIFFER' if differs else 'AGREE'} on this "
                    f"row's cell 0, but the naive split gives {tokens!r} and the backtick-aware "
                    f"split gives {tidied!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} ({row!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the retirement gate parsed {len(wrong)} of {len(self.ROW_SHAPES)} row shapes "
            "differently. THIS GATE DECIDES WHETHER AN ORCHESTRATOR MAY RETIRE, so a token that "
            "changes value stops resolving and a correctly-authored Set is refused (or, worse, an "
            "unauthored row goes unnoticed). READ THE `differs` FAILURES SPECIFICALLY: if a row "
            "expected to AGREE now differs, the shared row walk's naive splitter changed; if a row "
            "expected to DIFFER now agrees, the two splitters were unified, which is a behavior "
            "change to this gate and must be a deliberate reviewed act rather than a side effect of a "
            "cache change. FIX: the gate asks for `backtick_aware=False` because cell 0 is measured "
            "identical under both splitters across the LIVE corpus; that equivalence is corpus-"
            "specific, not universal, and two rows here are the counterexamples.\n"
            + "\n".join(wrong),
        )

    def test_the_gate_still_reads_the_five_real_column_shapes(self):
        """Regression fence for the refactor: the Order tokens must be unchanged.

        The five layouts share ONLY the first column and `rununify` has no `Id` column at all, so a
        row-walk change is exactly the kind of edit that would break one shape silently.
        """

        shapes = {
            "orchretire": ["Order", "Id", "Child", "Depends on"],
            "wslayout": ["Order", "Id", "What it does", "Set dependencies"],
            "runprofile": ["Order", "Id", "Child", "Responsibility", "Depends on"],
            "lanectn": [
                "Order",
                "Id",
                "Depth",
                "Requirements owned",
                "Prerequisite",
                "What it delivers",
            ],
            "rununify": ["Order", "What it does", "Depends on"],
        }
        for name, header in shapes.items():
            with self.subTest(shape=name):
                rows = ["| " + " | ".join(["01"] + ["x"] * (len(header) - 1)) + " |"]
                rows.append(
                    "| " + " | ".join(["02"] + ["y"] * (len(header) - 1)) + " |"
                )
                text = (
                    f"## {rs._CHILD_IPDS_HEADING}\n\n"
                    + "| "
                    + " | ".join(header)
                    + " |\n"
                    + "|"
                    + "|".join(["---"] * len(header))
                    + "|\n"
                    + "\n".join(rows)
                    + "\n"
                )
                tokens, parsed = rs.parse_declared_child_orders(text)
                self.assertTrue(parsed)
                self.assertEqual(tokens, ("01", "02"))


# ==================================================================================================
# E-02 / E-03: the digest, and the `xmqv5l` trap it must avoid
# ==================================================================================================


class TheDigestIgnoresWhatCorrectExecutionChanges(unittest.TestCase):
    """E-03: the five NO-OP mutations. This is the `xmqv5l` proof."""

    def test_each_executor_mutation_leaves_the_digest_IDENTICAL(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name, mutate in NO_OP_MUTATIONS.items():
            with self.subTest(mutation=name):
                mutated = mutate(FIXTURE)
                self.assertNotEqual(
                    mutated, FIXTURE, f"{name} did not actually change the text"
                )
                self.assertEqual(
                    rs.probe_cache_digest(mutated),
                    base,
                    f"{name} moved the digest; a conforming executor would re-probe on every tick",
                )

    def test_the_payload_carries_no_prose_from_inside_the_child_section(self):
        payload = rs.probe_cache_payload(FIXTURE)
        blob = json.dumps(payload)
        self.assertNotIn("DEFECT TODAY", blob)
        self.assertNotIn("could run in parallel", blob)

    def test_the_payload_carries_the_row_cell_TEXT(self):
        payload = rs.probe_cache_payload(FIXTURE)
        blob = json.dumps(payload)
        self.assertIn("bbb222", blob)
        self.assertIn("Cache the verdict against a content digest", blob)

    def test_the_payload_carries_no_scope_paths_and_no_V_item_text(self):
        """The deliberate divergence from `frozen_region_digest`, asserted rather than described."""
        blob = json.dumps(rs.probe_cache_payload(FIXTURE))
        self.assertNotIn("agent_workflows/runner_shared.py", blob)
        self.assertNotIn("paste the children's statuses", blob)


class TheDigestChangesForARealEdit(unittest.TestCase):
    """E-03: the four REAL edits. Each is a different question for the probe."""

    def test_each_real_edit_MOVES_the_digest(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name, mutate in REAL_EDITS.items():
            with self.subTest(mutation=name):
                mutated = mutate(FIXTURE)
                self.assertNotEqual(
                    mutated, FIXTURE, f"{name} did not actually change the text"
                )
                self.assertNotEqual(
                    rs.probe_cache_digest(mutated),
                    base,
                    f"{name} left the digest unchanged; the probe would serve a stale verdict",
                )


class TheDigestIsDeterministic(unittest.TestCase):
    """E-02: stable across PROCESSES, not merely repeatable within one."""

    def test_two_separate_interpreters_agree(self):
        script = (
            "import sys;"
            f"sys.path.insert(0, {str(REPO_ROOT)!r});"
            "from agent_workflows import runner_shared as rs;"
            "import tests.test_orchestrator_probe_cache as m;"
            "print(rs.probe_cache_digest(m.FIXTURE))"
        )
        outs = []
        for _ in range(2):
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outs.append(proc.stdout.strip())
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[0], rs.probe_cache_digest(FIXTURE))

    # A SOURCE-TEXT PIN WAS DELETED HERE, not replaced.
    # `test_the_docstring_states_the_divergence_from_frozen_region_digest` asserted three substrings
    # in `probe_cache_digest.__doc__`: `"frozen_region_digest"`, `"CHILD-TABLE ROWS ARE IN"` and
    # `"V-ITEM TEXT ARE OUT"`. Each of the three properties it was proxying for is asserted
    # BEHAVIORALLY, in this same module, on real inputs:
    #   * the divergence FROM `frozen_region_digest` ->
    #     `TheDigestDiffersFromFrozenRegionDigest.test_frozen_region_digest_does_NOT_move_on_a_child_
    #     table_edit` plus `test_the_probe_digest_DOES_move_on_those_same_edits`, which is the
    #     contrast stated as two measurements rather than as a sentence;
    #   * CHILD-TABLE ROWS ARE IN -> `TheDigestIgnoresWhatCorrectExecutionChanges
    #     .test_the_payload_carries_the_row_cell_TEXT` and `TheKeyIsRowTextNotTheOrderGraph
    #     .test_the_row_cells_DO_distinguish_those_same_edits`;
    #   * V-ITEM TEXT ARE OUT -> `test_the_payload_carries_no_scope_paths_and_no_V_item_text`.
    # So the pin added no coverage and subtracted editability: rewording a docstring while the code
    # and every behavioral assertion stayed correct would fail the suite, and (the worse direction) a
    # digest that silently stopped covering child-table rows would still pass it as long as the prose
    # still made the claim. Documentation quality is a review concern, not a substring assertion.


class TheDigestDiffersFromFrozenRegionDigest(unittest.TestCase):
    """E-02's ONLY genuinely new behavior, asserted as a CONTRAST.

    Four of the five properties above already hold for `frozen_region_digest`. If this class ever
    passed vacuously (both functions moving on a child-table edit), this whole child would be cost
    with no benefit, so the contrast is a test rather than a claim in a docstring.
    """

    def test_frozen_region_digest_does_NOT_move_on_a_child_table_edit(self):
        base = ipd_lifecycle.frozen_region_digest(FIXTURE)
        for name in ("add-a-child-row",) + ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                mutated = REAL_EDITS[name](FIXTURE)
                self.assertEqual(
                    ipd_lifecycle.frozen_region_digest(mutated),
                    base,
                    "frozen_region_digest moved on a child-table edit, so this "
                    "child's digest has no reason to exist; re-derive the design",
                )

    def test_the_probe_digest_DOES_move_on_those_same_edits(self):
        base = rs.probe_cache_digest(FIXTURE)
        for name in ("add-a-child-row",) + ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertNotEqual(
                    rs.probe_cache_digest(REAL_EDITS[name](FIXTURE)), base
                )

    def test_both_digests_agree_on_the_executor_mutations(self):
        """The four properties that ALREADY held: neither function may move on them."""
        for name in (
            "tick-a-checkbox",
            "fill-observed-evidence",
            "append-a-history-line",
            "edit-prose-outside-the-child-section",
        ):
            with self.subTest(mutation=name):
                mutated = NO_OP_MUTATIONS[name](FIXTURE)
                self.assertEqual(
                    ipd_lifecycle.frozen_region_digest(mutated),
                    ipd_lifecycle.frozen_region_digest(FIXTURE),
                )
                self.assertEqual(
                    rs.probe_cache_digest(mutated), rs.probe_cache_digest(FIXTURE)
                )

    def test_neither_existing_digest_function_was_modified(self):
        """This child's fence: `plan_content_digest`/`frozen_region_digest` are gate inputs."""
        for fn in (
            ipd_lifecycle.plan_content_digest,
            ipd_lifecycle.frozen_region_digest,
        ):
            self.assertTrue(callable(fn))
        # A `Scope-Paths` fence cannot be asserted at runtime, so assert the OBSERVABLE property
        # those two functions are relied on for instead: the frozen digest still ignores execution
        # state (the `xmqv5l` fix) and still moves on an E-item edit (the receipt guard).
        base = ipd_lifecycle.frozen_region_digest(FIXTURE)
        self.assertEqual(
            ipd_lifecycle.frozen_region_digest(tick_a_checkbox(FIXTURE)), base
        )
        self.assertNotEqual(
            ipd_lifecycle.frozen_region_digest(edit_an_e_item_action(FIXTURE)), base
        )


class TheKeyIsRowTextNotTheOrderGraph(unittest.TestCase):
    """F-10: the correction the whole justification rests on.

    `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}`. A key built on it would be
    sensitive to row COUNT and BLIND to row CONTENT, and since child 03 sends the child table AS the
    probe payload, a row edit the key ignored would serve a stale verdict under apparent authority.
    """

    def test_parse_child_table_rows_are_BYTE_IDENTICAL_for_a_row_content_edit(self):
        base = ipd_set_plan.parse_child_table(FIXTURE).rows
        for name in ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertEqual(
                    ipd_set_plan.parse_child_table(REAL_EDITS[name](FIXTURE)).rows,
                    base,
                    "parse_child_table became content-sensitive; re-check whether "
                    "row-cell extraction is still required",
                )

    def test_the_row_cells_DO_distinguish_those_same_edits(self):
        base = rs.child_table_rows(FIXTURE)
        for name in ROW_CONTENT_EDITS:
            with self.subTest(mutation=name):
                self.assertNotEqual(
                    rs.child_table_rows(REAL_EDITS[name](FIXTURE)), base
                )

    def test_a_row_ADD_is_the_one_edit_BOTH_keys_catch(self):
        """Why the OQ-01 fixture alone cannot prove a correct implementation."""
        base = ipd_set_plan.parse_child_table(FIXTURE).rows
        self.assertNotEqual(
            ipd_set_plan.parse_child_table(add_a_child_row(FIXTURE)).rows, base
        )
        self.assertNotEqual(
            rs.child_table_rows(add_a_child_row(FIXTURE)), rs.child_table_rows(FIXTURE)
        )


# ==================================================================================================
# E-04: the verdict store
# ==================================================================================================


def _rewrite_entry(path: Path, digest: str, value: object) -> None:
    """Replace one entry in the store wholesale, keeping the rest of the file valid JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["entries"][digest] = value
    path.write_text(json.dumps(payload), encoding="utf-8")


def _rewrite_field(path: Path, digest: str, field: str, value: object) -> None:
    """Replace ONE field of one entry, leaving the entry a well-formed mapping."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["entries"][digest][field] = value
    path.write_text(json.dumps(payload), encoding="utf-8")


class VerdictStoreTests(RepoCase):
    """E-04: write-then-read round trips, the recorded model, and a corrupt entry."""

    def test_write_then_read_round_trips_with_the_model(self):
        digest = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(
            self.root, digest, rs.PROBE_VERDICT_PASS, model="vendor/model-x"
        )
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertEqual(got.model, "vendor/model-x")
        self.assertTrue(got.recorded_at)
        self.assertTrue(got.is_hit)

    def test_the_store_path_derives_from_checkout_control_root(self):
        path = rs.probe_verdict_store_path(self.root)
        expected = (
            ipd_lifecycle.checkout_control_root(self.root)
            / "state"
            / "runtime"
            / "orchestrator-probe-verdicts.json"
        )
        self.assertEqual(path, expected)

    def test_a_linked_worktree_resolves_to_the_SAME_store(self):
        """The `dh0uno` property: an in-lane `repo_root` is the LANE, so hand-composition forks."""

        import os

        repo = self.root / "main"
        repo.mkdir()
        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(self.root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }

        def git(*args: str, cwd: Path = repo) -> None:
            subprocess.run(
                ["git", *args], cwd=str(cwd), check=True, env=env, capture_output=True
            )

        git("init", "-q", ".")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "fixture")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        git("add", "seed.txt")
        git("commit", "-qm", "seed")
        lane = self.root / "lane"
        git("worktree", "add", "-q", "-b", "lane", str(lane))

        self.assertEqual(
            rs.probe_verdict_store_path(repo),
            rs.probe_verdict_store_path(lane),
            "the lane resolved to a SECOND store the driver cannot see (dh0uno)",
        )

    def test_recording_one_verdict_does_not_discard_another(self):
        a = rs.probe_cache_digest(FIXTURE)
        b = rs.probe_cache_digest(add_a_child_row(FIXTURE))
        rs.record_probe_verdict(self.root, a, rs.PROBE_VERDICT_PASS, model="m")
        rs.record_probe_verdict(self.root, b, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, a, model="m").verdict,
            rs.PROBE_VERDICT_PASS,
        )
        self.assertEqual(
            rs.read_probe_verdict(self.root, b, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
        )

    #: (case, how to damage the store after ONE good verdict was written, the verdict the reader must
    #:  return, the stale reason it must report, why this row exists)
    #:
    #: ONE table replaces three tests. All three wrote the same `pass` verdict, damaged the store in
    #: some way, and required the read to report `unknown` with a particular reason. Only the damage
    #: varied, so it is the column, and the damage is expressed as a CALLABLE because the three operate
    #: at different layers (the file's bytes, one entry's type, one field's value) - which is the
    #: distinction the table is FOR.
    #:
    #: THE STALE REASON IS ASSERTED, NOT JUST THE VERDICT, and that is the whole value of grouping
    #: these: all three return `unknown`, so a row that checked only the verdict would pass if the
    #: reasons collapsed into one. They must not, because a MISS and a CORRUPT entry call for different
    #: operator responses (re-probe versus investigate a damaged file), and they are reported to a
    #: human.
    DAMAGE = (
        (
            "the whole store file is truncated mid-JSON",
            lambda path, _digest: path.write_text(
                '{"entries": {"trunc', encoding="utf-8"
            ),
            "PROBE_STALE_MISS",
            "AN UNPARSEABLE FILE IS `unknown`, NOT AN EXCEPTION AND NOT `pass`. Reported as a MISS "
            "rather than CORRUPT because no entry could be read at all, so the honest statement is "
            "`not probed`. An interrupted write is the realistic cause, which is why the file is "
            "truncated rather than scrambled",
        ),
        (
            "one ENTRY is the wrong type entirely",
            lambda path, digest: _rewrite_entry(path, digest, "not-an-object"),
            "PROBE_STALE_CORRUPT",
            "THE STORE PARSES BUT THE ENTRY IS NOT A MAPPING, which is a DIFFERENT fact from a miss "
            "and must report CORRUPT: the file is readable, so an operator needs to know something "
            "damaged an entry rather than that the plan was never probed. Distinguishing these two is "
            "why the reason column exists",
        ),
        (
            "one entry's `verdict` field holds an unrecognized value",
            lambda path, digest: _rewrite_field(
                path, digest, "verdict", "probably-fine"
            ),
            "PROBE_STALE_CORRUPT",
            "AN UNKNOWN VERDICT VALUE IS NOT SILENTLY TRUSTED. The load-bearing direction is that it "
            "must not read as `pass`: the gate's whole premise is that silence no longer means safe, "
            "so an unrecognized token must fail closed rather than being passed through to a caller "
            "that only checks `!= fail`",
        ),
    )

    def test_a_damaged_store_reads_as_unknown_with_the_right_reason(self):
        wrong = []
        for case, damage, reason_attr, why in self.DAMAGE:
            digest = rs.probe_cache_digest(FIXTURE)
            rs.record_probe_verdict(self.root, digest, rs.PROBE_VERDICT_PASS, model="m")
            path = rs.probe_verdict_store_path(self.root)
            self.assertEqual(
                rs.read_probe_verdict(self.root, digest, model="m").verdict,
                rs.PROBE_VERDICT_PASS,
                f"{case}: the verdict must be SERVED before the damage, or this row proves nothing",
            )
            damage(path, digest)
            expected_reason = getattr(rs, reason_attr)
            problems = []
            try:
                got = rs.read_probe_verdict(self.root, digest, model="m")
            except Exception as exc:  # noqa: BLE001 - raising IS the failure being reported
                problems.append(f"RAISED {type(exc).__name__}: {exc}")
            else:
                if got.verdict != rs.PROBE_VERDICT_UNKNOWN:
                    problems.append(
                        f"verdict was {got.verdict!r}, must be {rs.PROBE_VERDICT_UNKNOWN!r}"
                        + (
                            " -- and it read as PASS, which serves a verdict from a damaged store"
                            if got.verdict == rs.PROBE_VERDICT_PASS
                            else ""
                        )
                    )
                if got.stale_reason != expected_reason:
                    problems.append(
                        f"stale_reason was {got.stale_reason!r}, must be {expected_reason!r} "
                        f"({reason_attr})"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the reader mishandled {len(wrong)} of {len(self.DAMAGE)} damaged stores. A `RAISED` "
            "result is always a defect: this reader sits in front of a gate that runs unattended, so "
            "an exception here fails a whole run over a scratch file. A verdict of `pass` is the "
            "DANGEROUS failure, because the gate's premise is that silence no longer means safe. If "
            "the two CORRUPT rows started reporting MISS (or the reverse), the reasons collapsed: "
            "they are reported to a human and call for different responses (re-probe versus "
            "investigate a damaged file), so the distinction must survive. FIX: the store is "
            "gitignored runtime scratch, so any damage is recoverable by re-probing; prefer widening "
            "what the reader tolerates over making a caller handle an exception.\n"
            + "\n".join(wrong),
        )

    def test_recording_unknown_is_REFUSED(self):
        """`unknown` is the ABSENCE of an answer; storing it would make 'not probed' a fact."""
        with self.assertRaises(ValueError):
            rs.record_probe_verdict(
                self.root, "d" * 64, rs.PROBE_VERDICT_UNKNOWN, model="m"
            )


class TheStoreIsGitignoredInAnAdopter(unittest.TestCase):
    """E-04's prerequisite, verified in a FRESH repo carrying ONLY installer output.

    THIS REPOSITORY PROVES NOTHING HERE. `.aw/state/` is ignored here by the ROOT `.gitignore`, which
    the installer explicitly never writes, so a `git check-ignore` run in this tree would pass and
    say nothing about an adopter. The framework-owned `.aw/.gitignore` gained an anchored `/state/`
    entry in BOTH `_AW_GITIGNORE_TEMPLATE` (fresh installs) and the `_ensure_aw_gitignore` back-fill
    (already-installed adopters) on 2026-09-12, commit `ee38864c`, which is the prerequisite this
    child's E-04 waited on.
    """

    def _fresh_repo(self, base: Path) -> Path:
        import os

        repo = base / "adopter"
        repo.mkdir()
        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(base / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        subprocess.run(
            ["git", "init", "-q", "."],
            cwd=str(repo),
            check=True,
            env=env,
            capture_output=True,
        )
        self._env = env
        return repo

    def test_check_ignore_matches_the_framework_owned_gitignore(self):
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as td:
            repo = self._fresh_repo(Path(td))
            engine._ensure_aw_gitignore(repo)
            rel = ".aw/state/runtime/orchestrator-probe-verdicts.json"
            proc = subprocess.run(
                ["git", "check-ignore", "-v", rel],
                cwd=str(repo),
                capture_output=True,
                text=True,
                env=self._env,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"the verdict store is NOT ignored in an adopter: {proc.stderr}",
            )
            self.assertIn(".aw/.gitignore", proc.stdout)

    def test_the_template_and_the_backfill_BOTH_carry_the_rule(self):
        """A template-only entry reaches FRESH installs only; the back-fill is a literal list."""
        from agent_workflows import engine

        self.assertIn("/state/", engine._AW_GITIGNORE_TEMPLATE)
        with tempfile.TemporaryDirectory() as td:
            repo = self._fresh_repo(Path(td))
            gi = repo / ".aw" / ".gitignore"
            gi.parent.mkdir(parents=True, exist_ok=True)
            gi.write_text(
                "records/*/untracked/\n", encoding="utf-8"
            )  # pre-`state/` adopter
            engine._ensure_aw_gitignore(repo)
            self.assertIn("/state/", gi.read_text(encoding="utf-8"))


# ==================================================================================================
# E-05: a MISS fails closed, and both polarities are cached
# ==================================================================================================


class AMissFailsClosed(RepoCase):
    """E-05: `unknown`, NEVER `pass`. The gate's whole premise."""

    def test_an_empty_store_returns_unknown(self):
        got = rs.read_probe_verdict(
            self.root, rs.probe_cache_digest(FIXTURE), model="m"
        )
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertNotEqual(got.verdict, rs.PROBE_VERDICT_PASS)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MISS)
        self.assertFalse(got.is_hit)

    def test_a_digest_that_moved_is_a_MISS_not_the_old_verdict(self):
        rs.record_probe_verdict(
            self.root, rs.probe_cache_digest(FIXTURE), rs.PROBE_VERDICT_PASS, model="m"
        )
        moved = rs.probe_cache_digest(edit_an_e_item_action(FIXTURE))
        self.assertEqual(
            rs.read_probe_verdict(self.root, moved, model="m").verdict,
            rs.PROBE_VERDICT_UNKNOWN,
        )

    def test_the_three_states_are_distinct_values(self):
        self.assertEqual(
            len(
                {rs.PROBE_VERDICT_PASS, rs.PROBE_VERDICT_FAIL, rs.PROBE_VERDICT_UNKNOWN}
            ),
            3,
        )


class AStaleFailCannotBeServed(RepoCase):
    """OQ-01's ruling, as the fixture the maintainer specified.

    BOTH polarities are cached, and re-evaluate-on-change is what makes a cached FAIL safe: the
    remedy for a fail is to move the work into a NEW CHILD, which edits BOTH the parent's checklist
    text and its child table, and the digest covers both. So the remedy is APPLIED here rather than
    argued about.
    """

    #: The remedy, applied to the fixture: E-02's parent-only work moves OUT of the checklist and INTO
    #: a new child row. Exactly the two edits the ruling names.
    @staticmethod
    def apply_the_remedy(text: str) -> str:
        without_the_item = text.replace(
            "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.\n"
            "  - Depends on: E-01\n"
            "  - Expected outcome: records reconciled.\n"
            "  - Execution state: pending\n\n",
            "",
        )
        assert without_the_item != text, "the checklist item was not removed"
        with_the_child = add_a_child_row(without_the_item)
        assert with_the_child != without_the_item, "the child row was not added"
        return with_the_child

    def test_the_remedy_MOVES_the_digest_so_the_fail_entry_is_discarded(self):
        before = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, before, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, before, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
            "the fail must be served BEFORE the remedy, or this test proves nothing",
        )

        fixed = self.apply_the_remedy(FIXTURE)
        after = rs.probe_cache_digest(fixed)
        self.assertNotEqual(after, before, "the remedy did not move the digest")
        got = rs.read_probe_verdict(self.root, after, model="m")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_MISS)

    def test_a_ROW_ONLY_remedy_also_discards_the_stale_fail(self):
        """The half of the remedy that ONLY child-table sensitivity can see.

        Adding a child that covers the parent's work while LEAVING the parent's item as sequencing
        prose is a real authoring outcome, and it is the case a parsed-order-graph key would get
        wrong in the dangerous direction: the fail entry would still be served after the work was
        genuinely moved. So this is asserted separately from the two-edit remedy above, whose
        checklist half moves the key on its own and therefore cannot prove this property.
        """
        before = rs.probe_cache_digest(FIXTURE)
        rs.record_probe_verdict(self.root, before, rs.PROBE_VERDICT_FAIL, model="m")
        self.assertEqual(
            rs.read_probe_verdict(self.root, before, model="m").verdict,
            rs.PROBE_VERDICT_FAIL,
        )

        after = rs.probe_cache_digest(add_a_child_row(FIXTURE))
        self.assertNotEqual(
            after,
            before,
            "a child-table-only remedy left the key unchanged, so a fixed "
            "orchestrator would keep being served its old FAIL",
        )
        self.assertEqual(
            rs.read_probe_verdict(self.root, after, model="m").verdict,
            rs.PROBE_VERDICT_UNKNOWN,
        )

    def test_the_remedy_is_detected_by_the_checklist_edit_ALONE_too(self):
        """Belt and braces: either half of the remedy moves the key on its own.

        Pinned because a remedy that only added a child row (without removing the parent item) is a
        real authoring outcome too, and a key that needed BOTH edits would serve a stale fail for it.
        """
        base = rs.probe_cache_digest(FIXTURE)
        checklist_only = FIXTURE.replace(
            "- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.",
            "- [ ] E-02 SEQUENCE the fourth child once the third is executed.",
        )
        self.assertNotEqual(rs.probe_cache_digest(checklist_only), base)
        self.assertNotEqual(rs.probe_cache_digest(add_a_child_row(FIXTURE)), base)


# ==================================================================================================
# E-06: the staleness guard
# ==================================================================================================


class StalenessRuleTests(RepoCase):
    """E-06: a digest match proves the plan did not change, NOT that the answer is still good."""

    def _record(self, *, model: str | None, days_ago: int, digest: str = "") -> str:
        digest = digest or rs.probe_cache_digest(FIXTURE)
        when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
        rs.record_probe_verdict(
            self.root,
            digest,
            rs.PROBE_VERDICT_PASS,
            model=model,
            recorded_at=when.replace(microsecond=0).isoformat(),
        )
        return digest

    #: (case, the model RECORDED, the age in days, the model READ BACK, the `max_age_days` to read
    #:  with or None for the default, the verdict expected, the stale reason expected, why this row
    #:  exists)
    #:
    #: ONE table replaces four tests. Each recorded a `pass` verdict and read it back, differing only
    #: in the model on either side, the age, and the explicit bound. THE READ SIDE IS A COLUMN, which
    #: is what makes the table state something the four could not: the SAME stored entry is served or
    #: withheld depending on who asks and when, which is the definition of a staleness rule.
    #:
    #: AGES ARE DERIVED FROM `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS`, never written as literals, so
    #: changing the shipped bound re-aims the fixtures instead of failing rows that still describe
    #: correct behavior. The rows that pass an EXPLICIT bound deliberately use a fixed age either side
    #: of it, since the point there is that the argument overrides the default in both directions.
    STALENESS = (
        (
            "fresh, same model",
            "vendor/model-x",
            1,
            "vendor/model-x",
            None,
            "PROBE_VERDICT_PASS",
            "",
            "THE CACHE HIT: the one row where the cache does its job. Every withholding row below is "
            "vacuous while this one is broken, because a reader that served nothing would satisfy "
            "them all and the cache would simply not exist",
        ),
        (
            "past the default bound, same model",
            "vendor/model-x",
            None,  # filled from the constant: bound + 1
            "vendor/model-x",
            None,
            "PROBE_VERDICT_UNKNOWN",
            "PROBE_STALE_TOO_OLD",
            "A DIGEST MATCH PROVES THE PLAN DID NOT CHANGE, NOT THAT THE ANSWER IS STILL GOOD, which "
            "is E-06's whole premise: the model, the prompt and the repository's conventions all move "
            "under an unchanged plan. The TIME BOUND is also the guard that applies even when no "
            "model can be named, which is why it carries the unnamed-model cases elsewhere",
        ),
        (
            "fresh, but a DIFFERENT model",
            "vendor/model-x",
            1,
            "vendor/model-y",
            None,
            "PROBE_VERDICT_UNKNOWN",
            "PROBE_STALE_MODEL_CHANGED",
            "A DIFFERENT MODEL IS A DIFFERENT JUDGE. Differs from the HIT row ONLY in the model read "
            "back, so the pair isolates the model comparison from the time bound; and the REASON "
            "matters because an operator seeing `model-changed` knows a re-probe will be cheap and "
            "correct, where `too-old` might mean something else moved",
        ),
        (
            "inside an explicitly WIDER bound",
            "vendor/model-x",
            10,
            "vendor/model-x",
            30,
            "PROBE_VERDICT_PASS",
            "",
            "THE PER-READ BOUND OVERRIDES THE DEFAULT UPWARDS. Paired with the row below over the "
            "SAME stored entry and the same age: only the argument differs, which is what states that "
            "the caller decides rather than the constant",
        ),
        (
            "outside an explicitly NARROWER bound",
            "vendor/model-x",
            10,
            "vendor/model-x",
            5,
            "PROBE_VERDICT_UNKNOWN",
            "PROBE_STALE_TOO_OLD",
            "and downwards. Without this row `max_age_days` could be accepted and ignored, and the "
            "row above would still pass since 10 days is inside the default bound anyway",
        ),
    )

    def test_a_stored_verdict_is_served_or_withheld_per_read(self):
        bound = rs.DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS
        wrong = []
        for (
            case,
            recorded_model,
            days_ago,
            read_model,
            max_age,
            verdict_attr,
            reason_attr,
            why,
        ) in self.STALENESS:
            age = bound + 1 if days_ago is None else days_ago
            digest = self._record(model=recorded_model, days_ago=age)
            kwargs = {} if max_age is None else {"max_age_days": max_age}
            got = rs.read_probe_verdict(self.root, digest, model=read_model, **kwargs)
            expected_verdict = getattr(rs, verdict_attr)
            problems = []
            if got.verdict != expected_verdict:
                problems.append(
                    f"verdict was {got.verdict!r}, expected {expected_verdict!r}"
                )
            if reason_attr:
                expected_reason = getattr(rs, reason_attr)
                if got.stale_reason != expected_reason:
                    problems.append(
                        f"stale_reason was {got.stale_reason!r}, expected "
                        f"{expected_reason!r} ({reason_attr})"
                    )
                # A WITHHELD verdict must still REPORT what was stored, so a human can see what
                # expired rather than only that nothing was served.
                if got.recorded_verdict != rs.PROBE_VERDICT_PASS:
                    problems.append(
                        f"recorded_verdict was {got.recorded_verdict!r}; the reader must still "
                        "report the STORED value so a human can see what was withheld and why"
                    )
            else:
                if not got.is_hit:
                    problems.append(
                        "the verdict was served but `is_hit` is False, so a caller counting cache "
                        "hits sees none"
                    )
            if problems:
                wrong.append(
                    f"  {case} (recorded model={recorded_model!r} {age}d ago, read as "
                    f"{read_model!r}, max_age_days={max_age if max_age is not None else 'default'}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the reader served the wrong thing for {len(wrong)} of {len(self.STALENESS)} reads. READ "
            "THE GROUPING: if the single HIT row failed, the cache serves nothing and every "
            "withholding row below became vacuous, so the cache costs a store and buys nothing. If "
            "every withholding row failed, a stale verdict is now served under apparent authority, "
            "which is the dangerous direction: this gate's premise is that silence no longer means "
            "safe. A WRONG REASON on a correct verdict means two staleness causes collapsed, and they "
            "are reported to an operator who responds differently to `model-changed` than to "
            "`too-old`. The two explicit-bound rows share one stored entry and one age and differ "
            "only in the argument, so if they move together `max_age_days` is being ignored. FIX: the "
            f"ages here are DERIVED from `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS` (currently {bound}), so "
            "changing the shipped bound re-aims these fixtures rather than breaking them.\n"
            + "\n".join(wrong),
        )

    def test_an_unparseable_timestamp_is_treated_as_infinitely_old(self):
        digest = self._record(model="vendor/model-x", days_ago=1)
        path = rs.probe_verdict_store_path(self.root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"][digest]["recorded_at"] = "not-a-timestamp"
        path.write_text(json.dumps(payload), encoding="utf-8")
        got = rs.read_probe_verdict(self.root, digest, model="vendor/model-x")
        self.assertEqual(got.verdict, rs.PROBE_VERDICT_UNKNOWN)
        self.assertEqual(got.stale_reason, rs.PROBE_STALE_TOO_OLD)


class TheHostDefaultModelCaseIsDecided(RepoCase):
    """F-12: `runner_profiles.resolve` returns `model=None` with provenance `host-default`.

    DECISION: when EITHER side cannot name a model, the model comparison is SKIPPED and the TIME
    BOUND alone decides. The rejected alternative (an unknown model never matches) would make the
    cache miss in the COMMON case, i.e. a cache that does not exist. The honest cost is stated in
    `read_probe_verdict`'s docstring and pinned by the last test here.
    """

    def _record(self, *, model: str | None, days_ago: int) -> str:
        digest = rs.probe_cache_digest(FIXTURE)
        when = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
        rs.record_probe_verdict(
            self.root,
            digest,
            rs.PROBE_VERDICT_PASS,
            model=model,
            recorded_at=when.replace(microsecond=0).isoformat(),
        )
        return digest

    def test_the_premise_is_real_a_resolve_can_return_model_None(self):
        """Asserted rather than trusted, so the rule's rationale cannot quietly become false."""
        from agent_workflows import runner_profiles

        cfg = runner_profiles.ProfileConfig()
        resolved = runner_profiles.resolve(cfg, runner="opencode")
        self.assertIsNone(resolved.model)
        self.assertEqual(
            resolved.provenance.get("model"), runner_profiles.PROVENANCE_HOST_DEFAULT
        )

    #: (case, model RECORDED, age in days, model READ BACK, expected verdict, expected stale reason
    #:  or "", why this row exists)
    #:
    #: ONE table replaces four tests over the SAME decision: when EITHER side cannot name a model, the
    #: comparison is SKIPPED and the time bound alone decides. All four combinations of
    #: (recorded named?, read named?) belong together because the rule is stated over the PAIR, and any
    #: one of them alone reads as an arbitrary special case.
    #:
    #: THE EXPIRY ROW IS IN THIS TABLE DELIBERATELY. Skipping the model comparison means the time bound
    #: is the ONLY remaining guard for these reads, so the row that shows it still bites is what makes
    #: the decision defensible rather than merely convenient. Its age is derived from the shipped
    #: constant, not written as 400.
    UNNAMED_MODEL = (
        (
            "neither side names a model, fresh",
            None,
            1,
            None,
            "PROBE_VERDICT_PASS",
            "",
            "THE COMMON CASE, which is the entire reason for the decision: measured, "
            "`runner_profiles.resolve` returns `model=None` with provenance `host-default` whenever "
            "nothing names one. The rejected alternative (an unknown model never matches) would make "
            "the cache miss here, i.e. a cache that does not exist",
        ),
        (
            "neither side names a model, PAST the bound",
            None,
            None,  # bound + 1, derived from the shipped constant
            None,
            "PROBE_VERDICT_UNKNOWN",
            "PROBE_STALE_TOO_OLD",
            "THE HONEST COST OF THE DECISION, and why it is acceptable: with the model comparison "
            "skipped, the TIME BOUND is the only guard left for these reads, so it must still bite. "
            "Without this row the decision would amount to `unnamed models are cached forever`",
        ),
        (
            "a NAMED current model against an UNRECORDED one",
            None,
            1,
            "vendor/model-x",
            "PROBE_VERDICT_PASS",
            "",
            "THE ASYMMETRIC HALF: the entry predates model recording, the caller can name one, and "
            "the read is still SERVED. This is the migration case - entries written before the model "
            "was captured must not all miss at once",
        ),
        (
            "an UNNAMED current model against a recorded one",
            "vendor/model-x",
            1,
            None,
            "PROBE_VERDICT_PASS",
            "",
            "the mirror of the row above, which is what makes the rule `EITHER side unnamed` rather "
            "than `the recorded side unnamed`. Read against "
            "`StalenessRuleTests`'s `fresh, but a DIFFERENT model` row: two NAMED models that "
            "disagree DO miss, so this is a skip and not a blanket acceptance",
        ),
    )

    def test_an_unnamed_model_on_either_side_skips_the_comparison(self):
        bound = rs.DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS
        wrong = []
        for (
            case,
            recorded_model,
            days_ago,
            read_model,
            verdict_attr,
            reason_attr,
            why,
        ) in self.UNNAMED_MODEL:
            age = bound + 1 if days_ago is None else days_ago
            digest = self._record(model=recorded_model, days_ago=age)
            got = rs.read_probe_verdict(self.root, digest, model=read_model)
            expected_verdict = getattr(rs, verdict_attr)
            problems = []
            if got.verdict != expected_verdict:
                problems.append(
                    f"verdict was {got.verdict!r}, expected {expected_verdict!r}"
                )
            if reason_attr and got.stale_reason != getattr(rs, reason_attr):
                problems.append(
                    f"stale_reason was {got.stale_reason!r}, expected "
                    f"{getattr(rs, reason_attr)!r} ({reason_attr})"
                )
            if not reason_attr and recorded_model is None and got.model != "":
                problems.append(
                    f"an unrecorded model read back as {got.model!r}; it must normalise to the "
                    "empty string so a caller cannot mistake it for a named one"
                )
            if problems:
                wrong.append(
                    f"  {case} (recorded={recorded_model!r} {age}d ago, read as {read_model!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the unnamed-model rule answered {len(wrong)} of {len(self.UNNAMED_MODEL)} reads wrongly. "
            "READ THE GROUPING: if the three SERVED rows failed together, the rule was inverted into "
            "`an unknown model never matches`, which makes the cache miss in the COMMON case and is a "
            "cache that does not exist (this alternative was considered and rejected). If only the "
            "EXPIRY row failed, the decision lost the guard that justifies it: with the model "
            "comparison skipped the time bound is the ONLY remaining check for these reads, so "
            f"unnamed-model entries would be cached forever. FIX: the age is derived from the shipped "
            f"bound (currently {bound}); and note the premise itself is asserted separately by "
            "`test_the_premise_is_real_a_resolve_can_return_model_None`, so check that first - if it "
            "also failed, `runner_profiles.resolve` changed and this whole rule may no longer be "
            "needed.\n" + "\n".join(wrong),
        )

    # A SOURCE-TEXT PIN WAS DELETED HERE, not replaced.
    # `test_the_docstring_states_the_decision_and_its_cost` asserted three substrings in
    # `read_probe_verdict.__doc__`: `"model=None"`, `"TIME BOUND alone decides"` and
    # `"honest limit"`. The class docstring above says the cost is "stated in `read_probe_verdict`'s
    # docstring and pinned by the last test here" - but a substring search does not pin a COST, it
    # pins a spelling. Both halves of the decision it was proxying for are asserted behaviorally by
    # its four siblings in this class:
    #   * the DECISION (an absent model on either side skips the comparison) ->
    #     `test_no_model_either_side_within_the_bound_is_SERVED`,
    #     `test_a_named_current_model_against_an_UNRECORDED_one_is_served` and
    #     `test_an_UNNAMED_current_model_against_a_recorded_one_is_served`, which is the rule stated
    #     over all three combinations rather than as a phrase;
    #   * the COST (the time bound is then the ONLY guard) ->
    #     `test_no_model_either_side_PAST_the_bound_is_unknown`, which drives the case the phrase
    #     describes;
    #   * and the PREMISE the whole rule rests on -> `test_the_premise_is_real_a_resolve_can_return_
    #     model_None`, which is the genuinely valuable one because it fails if
    #     `runner_profiles.resolve` ever stops returning `model=None`, making the rationale false.
    # Deleting the pin removes a test that would fail on a reworded docstring while passing on a
    # broken rule.


# ==================================================================================================
# E-07: one shared definition, no deeper oc->agy coupling
# ==================================================================================================


class BothHostsShareEverySymbol(unittest.TestCase):
    """E-07: object identity, not grep (`2r306y`/`818uru`)."""

    NEW_SYMBOLS = (
        "child_table_rows",
        "probe_cache_payload",
        "probe_cache_digest",
        "probe_verdict_store_path",
        "record_probe_verdict",
        "read_probe_verdict",
        "ProbeVerdict",
        "PROBE_VERDICT_PASS",
        "PROBE_VERDICT_FAIL",
        "PROBE_VERDICT_UNKNOWN",
        "PROBE_VERDICT_STORE_SCHEMA_VERSION",
        "DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS",
        "PROBE_STALE_MISS",
        "PROBE_STALE_CORRUPT",
        "PROBE_STALE_MODEL_CHANGED",
        "PROBE_STALE_TOO_OLD",
    )

    def test_every_new_symbol_is_defined_in_runner_shared(self):
        for name in self.NEW_SYMBOLS:
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(rs, name), f"{name} is not in runner_shared")

    def test_both_hosts_reach_the_SAME_object(self):
        from agent_workflows import agy_runipd, oc_runipd

        for name in self.NEW_SYMBOLS:
            with self.subTest(symbol=name):
                shared = getattr(rs, name)
                for host in (oc_runipd, agy_runipd):
                    reached = getattr(host.runner_shared, name)
                    self.assertIs(
                        reached,
                        shared,
                        f"{host.__name__} reaches a DIFFERENT {name} object",
                    )

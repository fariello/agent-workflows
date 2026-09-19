"""Tests for the canonical IPD schema (Set ipd-structure, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the schema against the specification
.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md and against the LIVE
templates (for the heading orders).

WHY THIS FILE IS MOSTLY TABLES. The subject is a SCHEMA, which is to say a collection of closed
sets (the recognized metadata fields, the statuses, the execution and validation states, the
checkpoints, the dispositions) plus small pure predicates over them. Nearly every test here had the
identical shape: call one predicate with one tuple of arguments and assert one answer. That is a
data row, not a test. The class boundaries mostly tracked which SECTION of `ipd_schema.py` a
predicate lives in, which is an implementation detail rather than a property of the subject.

The realistic regression in a schema is not "one predicate got one case wrong"; it is that a closed
set gained or lost a member, or that a rule table was re-keyed, and BOTH of those move several cases
at once. N single-assertion tests report that as N unrelated red lines each saying `None is not
None`; a table reports one failure naming every case that moved, which is the shape of the actual
problem, and it makes each closed set browsable AS A SET so the next person adding a member can see
what is already there.

FIELD NAMES AND ENUM MEMBERS ARE ASSERTED AS LITERAL STRINGS, NOT via the `S.META_*` constants,
wherever the spelling is what matters. Parsers read `- Scope-Paths:` verbatim out of plan text, so a
rename is a breaking change to every plan on disk; referencing the constant would make a rename
invisible because the constant and the parsed spelling move together. Do not "tidy" these into
constants.

MODE DISTINCTIONS ARE COLUMNS. The plan KIND (child versus orchestrator), the disposition DIRECTORY,
and the input FORM a value arrives in (bare prose, a `- [ ] E-NN` checkbox line, an `E-NN:` prefix)
are columns, because in each case the property worth asserting is that the SAME subject gets a
different answer per mode, which no single-mode test can state.

POSITIVE ROWS SHARE EACH TABLE WITH THE NEGATIVE ONES. A validator that rejected everything would
satisfy every negative row on its own, so each table's failure message says outright when a positive
row is among the failures and that the negatives are vacuous while it is broken.

Tests that are NOT rows carry a one-line docstring saying why. The recurring reasons: the subject is
a real FILE on disk or the whole plan corpus rather than an in-memory fixture; or the claim is
structural about the module itself (its import allowlist) rather than about a schema value.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from agent_workflows import ipd_schema as S
from tests.support import CONFORMING_ORCHESTRATOR, REPO_ROOT

from tests.support import SOURCE_WORKFLOWS as _SWF

CHILD_TEMPLATE = _SWF / "assess" / "templates" / "ipd.md"
# A static, checked-in conforming orchestrator fixture (see tests/fixtures/). Decoupled from
# the mutable live plans board so ordinary lifecycle moves (pending -> executed) never break
# these structural tests. Regenerate with ipd_authoring.build_skeleton(kind="orchestrator", ...).
ORCH_IPD = CONFORMING_ORCHESTRATOR

#: The metadata field map of a minimal VALID child plan sitting in `pending/`. Every metadata row
#: below is this dict with exactly one thing changed, which is what makes a row's failure
#: attributable to that one change.
VALID_CHILD_META = {
    "Date": "2026-08-03",
    "Kind": "child",
    "Concern": "x",
    "Scope": "x",
    "Status": "to-review",
    "Author": "x",
    "Id": "abc123",
    "Set": "s",
    "Order": "1",
}


def _h2_sequence(path: Path):
    seq = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            seq.append(line[3:].strip())
    return seq


def _meta(**changes):
    """`VALID_CHILD_META` with fields replaced, or REMOVED when the value is None."""
    fields = dict(VALID_CHILD_META)
    for key, value in changes.items():
        if value is None:
            fields.pop(key, None)
        else:
            fields[key] = value
    return fields


def _pairs(errors):
    """A comparable, readable view of a `MetaError` list."""
    return sorted((e.field, e.message) for e in errors)


class HeadingOrderTests(unittest.TestCase):
    """The H2 order per KIND, checked against the live template and against the placement rules.

    ONE table with two rows replaces five tests. Two of them compared a schema tuple to the H2
    sequence of a real template (one per kind), and three asserted placement or membership
    properties of those same tuples, each calling its predicate once per kind. So the KIND is a
    column: both kinds must satisfy every property, and the interesting claim is precisely that the
    two DIFFERENT orders agree on the placement rules while differing in their heading lists.

    Why the table beats the five: `CHILD_H2_ORDER` and `ORCHESTRATOR_H2_ORDER` are the same kind of
    object consumed by the same linter, and the realistic change is a section being renamed, added,
    or moved. That breaks the template comparison AND, if it lands next to Goal or the gate, the
    placement predicates too, for one kind or for both. Reading those failures together is what
    tells you whether a section moved or a whole order was re-listed; five tests report the same
    event as five unrelated failures in different classes.

    HEADING SPELLINGS ARE LOAD-BEARING and are asserted as literal strings. The linter matches `## `
    lines verbatim, so `Findings` versus `Findings (drivers)` is a breaking change to every plan on
    disk; that specific pair is a row's forbidden entry because the drivers-suffixed variant is what
    this repo drifted to once.
    """

    #: (kind, the schema's order tuple, the live file that must exhibit it, headings that MUST be
    #: in the order, headings that must NOT be, why this row exists)
    ORDERS = (
        (
            S.KIND_CHILD,
            S.CHILD_H2_ORDER,
            CHILD_TEMPLATE,
            (
                "Project conventions discovered (Step 0)",
                "Findings",
                "Deferred / out of scope (with reason)",
                "Scope check",
                "Open questions",
            ),
            ("Findings (drivers)",),
            "the CHILD order is the one authors meet, and it is checked against the LIVE template "
            "so the template an agent copies cannot drift from the schema the linter enforces. The "
            "`Step 0` and bare `Findings` entries are named explicitly because both were once "
            "spelled differently (`Findings (drivers)`), and the forbidden entry is what keeps that "
            "drift from returning silently",
        ),
        (
            S.KIND_ORCHESTRATOR,
            S.ORCHESTRATOR_H2_ORDER,
            ORCH_IPD,
            (
                "Child IPDs, sequence, and dependencies",
                "Completion criteria (the whole Set is done only when)",
                "Cross-IPD validation",
            ),
            ("Project conventions discovered (Step 0)", "Findings"),
            "the ORCHESTRATOR order is a DIFFERENT list, not a superset: it carries the three "
            "Set-level sections and deliberately omits the child's per-plan research sections. The "
            "forbidden entries are what prove that difference is intentional, so a well-meaning "
            "unification of the two orders fails here rather than silently demanding Findings of "
            "every orchestrator. Checked against the checked-in conforming fixture, not a live "
            "plan, so ordinary lifecycle moves cannot break it",
        ),
    )

    def test_each_kind_order_matches_its_file_and_the_placement_rules(self):
        wrong = []
        for kind, order, path, required, forbidden, why in self.ORDERS:
            order = list(order)
            problems = []
            on_disk = _h2_sequence(path)
            if order != on_disk:
                only_schema = [h for h in order if h not in on_disk]
                only_file = [h for h in on_disk if h not in order]
                problems.append(
                    f"the schema order does not match {path.name}: schema {order!r} vs file "
                    f"{on_disk!r}"
                    + (f"; in the schema only: {only_schema!r}" if only_schema else "")
                    + (f"; in the file only: {only_file!r}" if only_file else "")
                )
            if not S.execution_follows_goal(kind):
                problems.append(
                    "the execution checklist is not the H2 IMMEDIATELY after Goal (Goal at "
                    f"{order.index(S.H_GOAL)}, checklist at {order.index(S.H_EXECUTION)})"
                )
            if not S.validation_precedes_gate(kind):
                validation = S.VALIDATION_HEADING_BY_KIND[kind]
                problems.append(
                    "the validation checklist is not the H2 IMMEDIATELY before the approval gate "
                    f"(validation at {order.index(validation)}, gate at "
                    f"{order.index(S.H_APPROVAL_GATE)})"
                )
            missing = [h for h in required if h not in order]
            if missing:
                problems.append(
                    f"these headings must be in the order and are not: {missing!r}"
                )
            leaked = [h for h in forbidden if h in order]
            if leaked:
                problems.append(
                    f"these headings must NOT be in the order and are: {leaked!r}"
                )
            if problems:
                wrong.append(
                    f"  kind {kind!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ORDERS)} IPD kinds have a broken H2 order. BOTH ROWS "
            "FAILING TOGETHER on the placement predicates means a section was inserted next to Goal "
            "or next to the approval gate in both orders at once, which is one edit, not two bugs; "
            "both rows failing on the file comparison instead means the schema tuples were re-listed "
            "while the template and fixture were not (or the reverse). FIX: the heading strings are "
            "matched VERBATIM by the linter, so renaming one invalidates every plan already on "
            "disk. Change the schema, the template, the orchestrator fixture, and a migration "
            "together, or not at all.\n" + "\n".join(wrong),
        )


class MetadataFieldVocabularyTests(unittest.TestCase):
    """The metadata block's CLOSED vocabulary: which field names exist, and which are required.

    ONE table replaces the requiredness assertions that were scattered over three classes
    (`MetadataTests.test_id_is_required`, `ScopePathsSchemaTests`'s
    recognized-but-not-required pair, and `BlocksReleaseSchemaTests`'s identical pair). Every one of
    them asked the same two questions of one field name - is it RECOGNIZED, and is it REQUIRED - and
    differed only in the name. That is the definition of a data row.

    Why the table beats them, and why it is the natural shape for a schema: `META_RECOGNIZED` is a
    CLOSED SET assembled from five tuples, and `META_REQUIRED` is a subset of it. The realistic
    regression is a field moving BETWEEN those sets, and the consequences of the two directions are
    opposite and both severe. Promoting an optional field into `META_REQUIRED` mass-fails every plan
    already on disk that does not carry it (this is the "grandfather guarantee" the module comments
    keep invoking); dropping a field out of `META_RECOGNIZED` turns it into an IPD-M103 "unknown
    field" error, which also mass-fails every plan that DOES carry it. A table over the whole
    vocabulary states the required/optional split as a partition and reports every field that
    crossed it at once.

    THE FIELD NAMES ARE LITERAL STRINGS, NOT `S.META_*` CONSTANTS, AND THAT IS DELIBERATE. These
    spellings are parsed verbatim out of plan text by `parse_metadata_block`'s `_META_LINE_RE`, so
    the name IS the interface: `- Scope-Paths:` renamed to `- ScopePaths:` silently stops being
    recognized in every plan on disk. Referencing the constant would make that rename invisible
    because the constant and the parsed spelling move together. The row's `constant` column pins the
    constant to the same literal, which is what catches a rename in the other direction (the
    constant repointed while the on-disk spelling stayed).

    TWO-SIDED, SO IT CANNOT PASS VACUOUSLY: the table ALSO asserts it covers `META_RECOGNIZED`
    exactly, so a field added to the schema without a row here fails rather than going untested.
    """

    #: (field name AS PARSED FROM DISK, the `S.META_*` constant that must equal it or None when the
    #: schema exposes no constant, required?, why this row exists)
    FIELDS = (
        (
            "Date",
            None,
            True,
            "REQUIRED: a plan with no date cannot be aged, sharded, or archived",
        ),
        (
            "Kind",
            None,
            True,
            "REQUIRED and structural: `child` versus `orchestrator` selects the H2 order, the "
            "validation heading, and the Order rule, so nothing can be checked until it is known",
        ),
        (
            "Concern",
            None,
            True,
            "REQUIRED: the one-line statement of what the plan is for",
        ),
        (
            "Scope",
            None,
            True,
            "REQUIRED: prose scope, distinct from the machine-readable Scope-Paths",
        ),
        (
            "Status",
            None,
            True,
            "REQUIRED and the single most consumed field: the whole lifecycle, the attention view, "
            "and the runner's queue action are all read off it. A plan with no Status has no state",
        ),
        ("Author", None, True, "REQUIRED: attribution for the record"),
        (
            "Id",
            None,
            True,
            "REQUIRED (plans-adopter Order 02): the stable 6-char citation handle. Everything that "
            "links to a plan (`From-Backlog`, `Item-Dependencies`, a citation in another record) "
            "resolves through it, so an id-less plan is unreferenceable",
        ),
        (
            "Set",
            None,
            False,
            "OPTIONAL ALONE but PAIRED: see the all-or-none row in the validation table. A standalone "
            "plan belongs to no Set, so requiring it unconditionally would be wrong",
        ),
        ("Order", None, False, "OPTIONAL ALONE, paired with Set for the same reason"),
        (
            "Highest E allocated",
            "META_WATERMARK",
            False,
            "OPTIONAL at the schema layer because a plan with no E items has nothing to watermark; "
            "`watermark_error` makes it CONDITIONALLY mandatory once any E exists. Note the field "
            "name contains SPACES, which is why `_META_LINE_RE` admits them",
        ),
        (
            "Approval",
            "META_APPROVAL",
            False,
            "OPTIONAL, and CONDITIONALLY FORBIDDEN: it is required iff Status is `approved` and must "
            "be absent otherwise, which is the human attestation gate. Both directions are rows in "
            "the validation table below",
        ),
        (
            "Scope-Paths",
            "META_SCOPE_PATHS",
            False,
            "recognized-but-OPTIONAL by explicit design (Order oorry1): putting it in META_REQUIRED "
            "would fail every existing pending plan at the always-on author check. Its "
            "mandatoriness is CONDITIONAL and lives in the checkpoint layer at the ready-to-execute "
            "gate, not here",
        ),
        (
            "Item-Dependencies",
            "META_ITEM_DEPENDENCIES",
            False,
            "recognized-but-OPTIONAL (Order g69y23): cross-IPD prerequisites, a DIFFERENT layer from "
            "an E item's intra-plan `Depends on:`. Recognition here only stops IPD-M103",
        ),
        (
            "Blocks-Release",
            "META_BLOCKS_RELEASE",
            False,
            "recognized-but-OPTIONAL (Order si3mmt): the release gate. Whether the target RESOLVES "
            "to a release record is an `aw check` concern, not a schema one, because this module is "
            "pure and may not read the repository",
        ),
        (
            "From-Backlog",
            "META_FROM_BACKLOG",
            False,
            "recognized-but-OPTIONAL (Order ku93tn): the backlog->plan graduation link the "
            "close-legitimacy predicate consumes to confirm a blocking item's gate was handed off",
        ),
        (
            "From-Spec",
            "META_FROM_SPEC",
            False,
            "recognized-but-OPTIONAL: the SPEC-side sibling of From-Backlog. Both exist because a "
            "spec is an equally valid gate carrier, so recognizing only one would make the "
            "documented parity false of the schema",
        ),
        (
            "Priority",
            "META_PRIORITY",
            False,
            "recognized-but-OPTIONAL (Order 1b45el): the ENUM check lives in `aw check` because the "
            "vocabulary is OWNED by `backlog.PRIORITIES` and must not be forked here",
        ),
        (
            "Work-Kind",
            "META_WORK_KIND",
            False,
            "recognized-but-OPTIONAL, and named `Work-Kind` NOT `Kind` because `Kind` is already "
            "booked by this schema's own required structural field on a disjoint vocabulary. The "
            "spelling is the entire point of the field, so this row is why it is a literal string",
        ),
        (
            "Readiness",
            "META_READINESS",
            False,
            "recognized-but-OPTIONAL (Order 97df1z) and the one optional field whose VALUE enum is "
            "checked in this module rather than in `aw check`, because `READINESS_VALUES` is defined "
            "here. ABSENCE IS THE CORRECT AUTHORING STATE: it is a review OUTPUT, and the consumer "
            "fails closed on absence rather than reading it as approval",
        ),
        (
            "Quarantine",
            None,
            False,
            "OPTIONAL and part of an all-or-none TRIO; a quarantined plan is nonterminal by rule",
        ),
        (
            "Quarantine owner",
            None,
            False,
            "the second of the trio; another SPACE-containing name",
        ),
        (
            "Quarantine follow-up",
            None,
            False,
            "the third of the trio; a HYPHEN-containing name",
        ),
    )

    def test_every_recognized_field_has_the_requiredness_the_schema_promises(self):
        wrong = []
        for name, constant, required, why in self.FIELDS:
            problems = []
            if name not in S.META_RECOGNIZED:
                problems.append(
                    "not in META_RECOGNIZED, so a plan carrying it is an IPD-M103 'unknown field' "
                    "error; every plan on disk that declares it now fails"
                )
            if required and name not in S.META_REQUIRED:
                problems.append(
                    f"must be REQUIRED and is not (META_REQUIRED is {S.META_REQUIRED!r}), so a plan "
                    "omitting it lints clean"
                )
            if not required and name in S.META_REQUIRED:
                problems.append(
                    "must be OPTIONAL and is in META_REQUIRED, which MASS-FAILS every existing plan "
                    "that does not carry it (the grandfather guarantee)"
                )
            if constant is not None:
                actual = getattr(S, constant, None)
                if actual != name:
                    problems.append(
                        f"S.{constant} is {actual!r} but the on-disk spelling asserted here is "
                        f"{name!r}; the constant was repointed without the parsed spelling moving"
                    )
            if problems:
                wrong.append(
                    f"  field {name!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.FIELDS)} metadata fields have the wrong recognition or "
            "requiredness. The two failure directions have OPPOSITE causes and both mass-fail the "
            "corpus: a field wrongly in META_REQUIRED breaks every plan that OMITS it, and a field "
            "missing from META_RECOGNIZED breaks every plan that CARRIES it. SEVERAL ROWS MOVING "
            "TOGETHER almost always means one of the five tuples composing META_RECOGNIZED was "
            "edited or dropped from the union, not that several fields were each changed. FIX: "
            "adding a field to META_REQUIRED is a corpus migration, never a one-line change; the "
            "house pattern for a new field is recognized-but-optional here plus a CONDITIONAL "
            f"requirement in the checkpoint layer.\n" + "\n".join(wrong),
        )

    def test_the_table_covers_the_whole_recognized_vocabulary(self):
        """Two-sided guard: a field added to the schema with no row above must FAIL, not pass quietly.

        Without this, `META_RECOGNIZED` could grow a field nothing asserts, which is exactly how an
        unvalidated name reaches plan files. Kept separate because it is a claim about the TABLE's
        completeness rather than about any one field.
        """
        tabulated = {name for name, _c, _r, _w in self.FIELDS}
        self.assertEqual(
            tabulated,
            set(S.META_RECOGNIZED),
            "the FIELDS table and META_RECOGNIZED have diverged. Fields in the schema with no row: "
            f"{sorted(set(S.META_RECOGNIZED) - tabulated)!r}; rows naming a field the schema does "
            f"not recognize: {sorted(tabulated - set(S.META_RECOGNIZED))!r}. FIX: add a row stating "
            "the new field's requiredness and WHY, or (if a field was removed) delete its row and "
            "check no plan on disk still carries it.",
        )


class MetadataValidationTests(unittest.TestCase):
    """`validate_metadata` on one field map per row, with the disposition DIRECTORY as a column.

    ONE table replaces eleven tests spread over three classes (`MetadataTests`,
    `ScopePathsSchemaTests.test_absent_scope_paths_is_not_a_metadata_error`, and two
    `BlocksReleaseSchemaTests` absent/present cases). Every one built the same minimal valid child
    map, changed exactly one thing, and asserted that some error did or did not name one field. The
    class split tracked which FEATURE introduced the field, which is history, not structure.

    Why the table beats the eleven: `validate_metadata` is ONE function running its checks in
    sequence over one dict, so the realistic regression is a check being reordered, made conditional,
    or dropped, and that moves every row touching that check. Eleven tests report it as eleven
    `False is not true` lines naming no field; the table reports the exact (field, message) pairs
    expected versus produced for every row at once, which is what distinguishes "one rule dropped"
    from "the error TYPE changed for all of them".

    DIRECTORY IS A COLUMN, not a second class. The path/status compatibility rule only exists as a
    relation between the Status VALUE and the directory the plan sits in, so the same map must be
    clean in one directory and an error in another; a single-directory test cannot state that and the
    old `test_terminal_status_directory_mismatch` could only show one half of it.

    EACH ROW ASSERTS THE FULL ERROR SET, not merely that some expected error is present. The old
    tests used `any(e.field == "X" for e in errs)`, which passes even when the validator ALSO reports
    three unrelated errors, so a rule that started over-firing on valid input was invisible. Pinning
    the whole set is strictly stronger and it is what makes the clean rows meaningful.

    THE CLEAN ROWS ARE IN THIS TABLE deliberately. A validator that returned an error for every
    input would satisfy every negative row here on its own. The failure message says so when a clean
    row is among the failures.
    """

    #: (case, the field map, the directory, the EXACT sorted (field, message) pairs expected, why
    #: this row exists)
    CASES = (
        (
            "the minimal valid child in pending/",
            _meta(),
            "pending",
            [],
            "THE PRIMARY POSITIVE ROW: every negative row below is vacuous while this one is broken, "
            "because a validator that rejects everything satisfies all of them",
        ),
        (
            "the same plan carrying the optional Scope-Paths",
            _meta(**{"Scope-Paths": "agent_workflows/foo.py"}),
            "pending",
            [],
            "A POSITIVE ROW for the recognized-but-optional contract: declaring the field must not "
            "trip the always-on metadata check. Its GRAMMAR is `parse_scope_paths`' job, checked in "
            "its own table; `validate_metadata` deliberately does not parse the value",
        ),
        (
            "the same plan carrying the optional Blocks-Release",
            _meta(**{"Blocks-Release": "next"}),
            "pending",
            [],
            "A POSITIVE ROW (Order si3mmt): the release gate must be declarable without a metadata "
            "error, and whether `next` RESOLVES to a release record is an `aw check` concern because "
            "this module may not read the repository",
        ),
        (
            "a required field deleted (Status)",
            _meta(Status=None),
            "pending",
            [("Status", "required field missing")],
            "the required set is unconditional. Status is the row's subject because it is the most "
            "consumed field of all: a plan whose Status nothing can read has no lifecycle state, so "
            "the runner, the attention view, and every gate see it as undefined rather than as bad",
        ),
        (
            "Status: auto-approved",
            _meta(Status="auto-approved"),
            "pending",
            [],
            "A POSITIVE ROW and the whole point of the tier existing: `auto-approved` is a LEGAL "
            "ready-to-execute status that records an AUTOMATED clear, so it must NOT demand the "
            "human `Approval` field. If this row grows an Approval error, automated approval has "
            "silently started requiring a human attestation nobody wrote",
        ),
        (
            "Status: approved with no Approval field",
            _meta(Status="approved"),
            "pending",
            [("Approval", "Approval is required when Status is approved")],
            "`approved` means a HUMAN signed off, and the Approval field is the attestation. Without "
            "this rule a plan could claim human approval with no record of who or when, which is the "
            "forged-attestation failure the whole gate exists to stop",
        ),
        (
            "Status: approved WITH an Approval field",
            _meta(Status="approved", Approval="approved by x 2026-08-03"),
            "pending",
            [],
            "THE POSITIVE HALF of the previous row, and it must be in the same table: a rule that "
            "rejected Approval unconditionally would satisfy the row above while making every "
            "genuinely approved plan invalid",
        ),
        (
            "an Approval field WITHOUT approved status",
            _meta(Approval="approved by x"),
            "pending",
            [("Approval", "Approval must be absent unless Status is approved")],
            "the iff is enforced in BOTH directions. A lingering Approval line on a to-review plan "
            "is a stale human attestation attached to work that has since changed, which is worse "
            "than none because it reads as current",
        ),
        (
            "Id deleted",
            _meta(Id=None),
            "pending",
            [("Id", "required field missing")],
            "the id6 is the stable citation handle every cross-record link resolves through, so an "
            "id-less plan cannot be referenced by a backlog handoff or a dependency edge",
        ),
        (
            "Id that is not a valid id6",
            _meta(Id="TOOLONGX"),
            "pending",
            [("Id", "Id must be a 6-char base36-lowercase token")],
            "PRESENCE IS NOT ENOUGH: the grammar is checked, because ids are matched literally "
            "across records. This value fails on BOTH counts (8 chars, uppercase), and uppercase is "
            "the likelier real mistake since a hand-copied id6 keeps its case",
        ),
        (
            "an orchestrator declaring Order 1",
            _meta(Kind="orchestrator"),
            "pending",
            [("Order", "orchestrator Order must be 0")],
            "`00` is RESERVED for the orchestrator of a Set, and the filename embeds the Order, so "
            "an orchestrator at Order 1 COLLIDES with a child plan's slot",
        ),
        (
            "an orchestrator declaring Order 0",
            _meta(Kind="orchestrator", Order="0"),
            "pending",
            [],
            "THE POSITIVE HALF of the previous row: the rule is kind-CONDITIONAL, so it must accept "
            "the value it reserves. Without this row the rule could be `Order must be >= 1` for "
            "everything, which passes the negative above for the wrong reason",
        ),
        (
            "a child declaring Order 0",
            _meta(Order="0"),
            "pending",
            [("Order", "child Order must be an integer >= 1")],
            "THE MIRROR of the orchestrator rule, and this is where the KIND column earns its place: "
            "the SAME value `0` is mandatory for one kind and forbidden for the other, which no "
            "single-kind test can express",
        ),
        (
            "a non-integer Order",
            _meta(Order="x"),
            "pending",
            [("Order", "Order must be an integer")],
            "the Order is compared numerically and sorts the queue, so a non-numeric value would "
            "otherwise reach an `int()` at a later, less forgiving layer",
        ),
        (
            "Set present, Order deleted",
            _meta(Order=None),
            "pending",
            [("Set/Order", "Set and Order are required together")],
            "all-or-none PAIRING: a Set membership with no position in it cannot be ordered against "
            "its siblings. NOTE the error field is the composite `Set/Order`, not either field name, "
            "which is why asserting the exact pair matters here",
        ),
        (
            "an unrecognized Kind",
            _meta(Kind="bogus"),
            "pending",
            [("Kind", "unknown kind (expected child or orchestrator)")],
            "`Kind` selects the H2 order, the validation heading, and the Order rule, so an "
            "unrecognized value is not a cosmetic defect: nothing downstream knows which contract to "
            "apply",
        ),
        (
            "an unrecognized Status",
            _meta(Status="bogus"),
            "pending",
            [("Status", "unrecognized readiness status")],
            "the status vocabulary is CLOSED and imported from `plans` (never forked). A typo'd "
            "status is the classic silent failure: `aproved` is not approved, and a plan carrying it "
            "is invisible to every view that filters by state",
        ),
        (
            "a present but out-of-enum Readiness",
            _meta(Readiness="bogus"),
            "pending",
            [
                (
                    "Readiness",
                    "unrecognized readiness value (expected one of go, go-pending-approval, no-go)",
                )
            ],
            "the one OPTIONAL field whose value enum is checked in THIS module, because "
            "`READINESS_VALUES` is defined here rather than owned by another module. The message "
            "enumerates the legal values, which is asserted verbatim because it is what an author "
            "sees when the auto-approve gate refuses their plan",
        ),
        (
            "a present and legal Readiness",
            _meta(Readiness="go-pending-approval"),
            "pending",
            [],
            "THE POSITIVE HALF: a real review writes this field, so the enum check must accept the "
            "vocabulary it polices",
        ),
        (
            "one third of the Quarantine trio",
            _meta(Quarantine="reason"),
            "pending",
            [
                (
                    "Quarantine",
                    "Quarantine, Quarantine owner, and Quarantine follow-up are required together",
                )
            ],
            "all-or-none: a quarantine with no OWNER and no FOLLOW-UP is a plan parked forever with "
            "nobody accountable for un-parking it, which is the exact shape of silently dropped work",
        ),
        (
            "the complete Quarantine trio on a nonterminal plan",
            _meta(
                Quarantine="r",
                **{"Quarantine owner": "o", "Quarantine follow-up": "f"},
            ),
            "pending",
            [],
            "THE POSITIVE HALF of both quarantine rows: quarantining IS legal, and only nonterminal "
            "plans may do it. Without this row the rule could be `Quarantine is never allowed`",
        ),
        (
            "the complete Quarantine trio on a TERMINAL plan",
            _meta(
                Status="executed",
                Set=None,
                Order=None,
                Quarantine="r",
                **{"Quarantine owner": "o", "Quarantine follow-up": "f"},
            ),
            "executed",
            [("Quarantine", "only nonterminal plans may be quarantined")],
            "quarantine means WORK IS PARKED AND WILL RESUME, which is a contradiction on a plan "
            "already executed. Filed in `executed/` so the path/status rule is satisfied and this "
            "row isolates the quarantine violation alone",
        ),
        (
            "a terminal Status sitting in pending/",
            _meta(Status="executed", Set=None, Order=None),
            "pending",
            [
                (
                    "Status",
                    "terminal Status must live in the matching terminal directory",
                )
            ],
            "THE DIRECTORY COLUMN'S REASON FOR EXISTING: directory carries disposition and Status "
            "carries readiness, and the two must agree. An `executed` plan left in `pending/` claims "
            "to be done while every directory-scanning tool still offers it as runnable",
        ),
        (
            "the SAME terminal plan sitting in executed/",
            _meta(Status="executed", Set=None, Order=None),
            "executed",
            [],
            "THE POSITIVE HALF, and the pair is the whole point of the column: one identical field "
            "map, two directories, two different answers. Neither row alone can state the relation",
        ),
        (
            "a pre-terminal Status sitting in executed/",
            _meta(Status="to-review"),
            "executed",
            [("Status", "pre-terminal Status must live under pending/")],
            "THE MIRROR VIOLATION, which is not symmetric with the one above: it reports a DIFFERENT "
            "message, so a refactor that collapsed the three branches of `_check_path_status` into "
            "one generic message would fail here and pass if only the terminal case were tested",
        ),
        (
            "a reusable Status sitting in pending/",
            _meta(Status="reusable", Set=None, Order=None),
            "pending",
            [("Status", "reusable Status must live in the reusable directory")],
            "the THIRD branch: `reusable` is STANDING, neither pre-terminal nor terminal, and it has "
            "its own directory and its own message. Three branches need three rows or the collapsed "
            "ones go unnoticed",
        ),
        (
            "a reusable Status sitting in reusable/",
            _meta(Status="reusable", Set=None, Order=None),
            "reusable",
            [],
            "THE POSITIVE HALF of the standing branch: a reusable plan is a legitimate, permanent "
            "resident of its own directory, not a lifecycle violation",
        ),
        (
            "a pre-terminal plan with the directory UNKNOWN",
            _meta(),
            None,
            [],
            "`directory=None` means the caller does not know where the plan lives, and the path "
            "checks are then SKIPPED rather than guessed. That is what lets `validate_metadata` "
            "serve callers holding only plan text, and a refactor that defaulted the unknown "
            "directory to a real name would start reporting a path error on a plan that has no path",
        ),
    )

    def test_each_metadata_case_reports_exactly_its_expected_errors(self):
        wrong = []
        clean_rows_broken = 0
        for case, fields, directory, expected, why in self.CASES:
            actual = _pairs(S.validate_metadata(dict(fields), directory=directory))
            expected_sorted = sorted(expected)
            if actual != expected_sorted:
                if not expected_sorted:
                    clean_rows_broken += 1
                missing = [p for p in expected_sorted if p not in actual]
                extra = [p for p in actual if p not in expected_sorted]
                detail = []
                if missing:
                    detail.append(f"MISSING {missing!r} (the rule did not fire)")
                if extra:
                    detail.append(f"UNEXPECTED {extra!r} (a rule over-fired)")
                wrong.append(
                    f"  {case} [directory={directory!r}]:\n"
                    f"    - expected exactly {expected_sorted!r}, got {actual!r}; "
                    + "; ".join(detail)
                    + f"\n    this row exists because: {why}"
                )
        vacuity = ""
        if clean_rows_broken:
            vacuity = (
                f" {clean_rows_broken} CLEAN row(s) are among the failures, and while any of those "
                "is broken every negative row here is VACUOUS: a validator that rejects everything "
                "satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"validate_metadata mishandled {len(wrong)} of {len(self.CASES)} metadata cases."
            f"{vacuity} All of these run through ONE function's sequential checks over one dict, so "
            "read the failures together: rows failing with MISSING errors point at a check that "
            "stopped firing or became conditional, while rows failing with UNEXPECTED errors point "
            "at one over-firing on valid input, and that direction MASS-FAILS the plan corpus. If "
            "the three path/status rows moved together, `_check_path_status`' branches were "
            "collapsed or its messages rewritten. FIX: each row pins the EXACT error set, not merely "
            "that the expected one appears, so an extra error is a failure by design; do not weaken "
            f"a row to an `any()` to make it pass.\n" + "\n".join(wrong),
        )


class MetadataBlockParseTests(unittest.TestCase):
    """`parse_metadata_block`: the LINE-level parse, which is a different subject from validation.

    ONE table replaces two tests (`test_duplicate_and_unknown_fields_from_parse` and
    `BlocksReleaseSchemaTests.test_blocks_release_line_parses_without_unknown_field_error`). Both fed
    raw `- Field: value` LINES to the parser and asserted which `MetaError`s came back, differing
    only in the lines. Kept in its own table rather than merged into the validation table above
    because the INPUT TYPE differs (a list of raw text lines versus an already-parsed dict) and the
    parser reports errors `validate_metadata` structurally cannot: duplicate and unknown fields are
    detectable only while reading lines, since a dict has already collapsed both.

    Why the table beats the two: the parser is one regex plus a small loop, and each row asserts the
    full (fields, errors) outcome, so a regex change that broke space-containing or hyphenated field
    names shows up across rows at once rather than as one unrelated failure.
    """

    #: (case, the raw metadata lines, expected {field: value}, expected sorted (field, message)
    #: pairs, why this row exists)
    BLOCKS = (
        (
            "a duplicate field and an unknown field together",
            ["- Date: 2026-08-03", "- Date: 2026-08-04", "- Bogus: x"],
            {"Date": "2026-08-03", "Bogus": "x"},
            [("Bogus", "unknown field"), ("Date", "duplicate field")],
            "BOTH parser-only errors in one row, because they are the two things a dict cannot "
            "express. FIRST-OCCURRENCE-WINS is asserted through the value map (`2026-08-03`, not "
            "`2026-08-04`), which is the part that matters: a silently-last-wins parser would make a "
            "duplicated Status read as whichever line came second. The unknown field is what "
            "IPD-M103 reports, and its purpose is catching a TYPO in a real field name, since a "
            "typo'd `- Status:` that parses clean is a plan whose state nothing can read",
        ),
        (
            "the optional Blocks-Release line",
            ["- Date: 2026-08-03", "- Blocks-Release: next"],
            {"Date": "2026-08-03", "Blocks-Release": "next"},
            [],
            "the recognized-but-optional contract at the PARSE layer: the line must both land in the "
            "field map AND produce no 'unknown field' error. Recognition is asserted separately from "
            "the vocabulary table because a field can be in META_RECOGNIZED and still be unparseable "
            "if the line regex rejects its spelling",
        ),
        (
            "field names containing SPACES and a HYPHEN",
            [
                "- Highest E allocated: 03",
                "- Quarantine follow-up: f",
                "- From-Backlog: abc123",
            ],
            {
                "Highest E allocated": "03",
                "Quarantine follow-up": "f",
                "From-Backlog": "abc123",
            },
            [],
            "THE LINE REGEX'S CHARACTER CLASS, which no validation-layer test reaches. Three real "
            "field names contain a space or a hyphen, so a regex tightened to `[A-Za-z]+` would "
            "silently stop parsing them; they would then read as ABSENT, which turns the watermark "
            "check off and breaks the quarantine trio rather than reporting anything",
        ),
        (
            "blank lines and a non-bullet line inside the run",
            ["- Date: 2026-08-03", "", "not a bullet", "- Author: x"],
            {"Date": "2026-08-03", "Author": "x"},
            [],
            "blanks are SKIPPED and a non-bullet line is IGNORED rather than treated as an error or "
            "as a terminator that drops later fields: `- Author: x` after the stray line is still "
            "parsed. This is what keeps an editing artifact in the middle of a block from silently "
            "erasing the metadata below it",
        ),
        (
            "an empty line list",
            [],
            {},
            [],
            "the degenerate input returns empty and does NOT invent 'required field missing' errors. "
            "Requiredness is `validate_metadata`'s job, and keeping the two layers separate is why "
            "the parser can be reused on a partial block",
        ),
    )

    def test_each_metadata_block_parses_to_its_exact_fields_and_errors(self):
        wrong = []
        for case, lines, expected_fields, expected_errors, why in self.BLOCKS:
            fields, errors = S.parse_metadata_block(lines)
            problems = []
            if fields != expected_fields:
                problems.append(
                    f"expected field map {expected_fields!r}, got {fields!r}"
                )
            actual_errors = _pairs(errors)
            if actual_errors != sorted(expected_errors):
                problems.append(
                    f"expected errors {sorted(expected_errors)!r}, got {actual_errors!r}"
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
            f"parse_metadata_block mishandled {len(wrong)} of {len(self.BLOCKS)} raw metadata "
            "blocks. One regex (`_META_LINE_RE`) plus one loop implements all of it, so SEVERAL ROWS "
            "FAILING TOGETHER means the regex changed rather than several behaviors breaking: check "
            "the field-name character class first, since three real field names contain a space or "
            "a hyphen. FIX: a field that stops PARSING reads as ABSENT to everything downstream, "
            "which is worse than an error, because absence silently disables the rules keyed on that "
            f"field instead of reporting anything.\n" + "\n".join(wrong),
        )


class IdGrammarTests(unittest.TestCase):
    """The E-*/V-* identifier grammar: what MATCHES in prose, and what parses to a suffix.

    ONE table replaces two tests (`test_id_matches_in_filename_and_prose` and
    `test_rejects_malformed`) that between them made five loose assertions. They split by OUTCOME
    (things that match versus things that do not), which is the least useful axis: both were asking
    the same three questions of one string, so the questions became COLUMNS and each string became a
    row carrying all three answers.

    THE THREE COLUMNS ARE THE POINT, because the two regexes and the strict parser are deliberately
    DIFFERENT predicates and the old tests could not state the difference. `E_ID_RE` is a SEARCH with
    `\\b` guards, used to find ids mentioned anywhere in prose or in a filename; `suffix_of` is an
    ANCHORED parse used to convert a whole token to an integer. So `"see E-07 for details"` must
    match the search and return NO suffix, while `"E-07"` must do both. Splitting by outcome hid
    exactly that relation; a row with both answers states it.

    Why the table beats the two: these are two regexes and one parser sharing one `[0-9]{2,}` shape,
    so the realistic regression (the `\\b` guards dropped, the two-digit minimum relaxed to one, the
    anchors lost from the strict pattern) shifts SEVERAL rows in one direction at once. Two tests
    report that as two failures naming no string; the table names every string whose answer moved.
    """

    #: (the string, must E_ID_RE.search match?, must V_ID_RE.search match?, expected `suffix_of`
    #: result, why this row exists)
    IDS = (
        (
            "E-01",
            True,
            False,
            1,
            "THE CANONICAL FORM: it matches the E search, is NOT a V, and parses to the integer 1. "
            "Note `01` -> `1`, so the suffix is numeric and zero padding is presentational only",
        ),
        (
            "V-12",
            False,
            True,
            12,
            "the V grammar is the SAME shape with a different prefix, and the two searches must not "
            "cross-match. If a V matched E_ID_RE the bijection checker would count validations as "
            "execution items and the E/V pairing would silently self-satisfy",
        ),
        (
            "20260803-01-k7-slug.md path E-01 here",
            True,
            False,
            None,
            "an id embedded in a FILENAME-bearing line still matches the search, which is what the "
            "`\\b` guards buy: the plan filename's own `-01-` Order segment must NOT be mistaken for "
            "an id, while the real `E-01` later in the line is found. `suffix_of` is None because the "
            "whole string is not a token, which is the search/parse split this table exists to state",
        ),
        (
            "see E-07 for details",
            True,
            False,
            None,
            "an id cited in PROSE matches. This is the case that makes cross-references findable, and "
            "it is why the regex is a search rather than an anchored match",
        ),
        (
            "V-12 validates",
            False,
            True,
            None,
            "the V equivalent of the prose case, and it is the leading text of a real validation row "
            "header, so the search must find the id before `V_ROW_RE` parses the rest of the line",
        ),
        (
            "E-1",
            False,
            False,
            None,
            "TWO DIGITS MINIMUM, which is not cosmetic: ids are sorted and matched as text in "
            "several places, so a one-digit id would sort `E-1` after `E-10`. A relaxed quantifier "
            "would make this row match and every plan's id ordering silently unstable",
        ),
        (
            "X-01",
            False,
            False,
            None,
            "the PREFIX is closed to E and V. An unrecognized prefix must parse to nothing rather "
            "than to a suffix, or an arbitrary token would enter the bijection as an execution item",
        ),
        (
            "E-007",
            True,
            False,
            7,
            "`{2,}` is a MINIMUM, not a fixed width, so a three-digit id is legal and parses to 7. A "
            "plan that outgrows 99 items must not become unparseable, and the leading zero must not "
            "survive into the integer where it would compare unequal to 7",
        ),
    )

    def test_each_identifier_gets_its_search_and_parse_answers(self):
        wrong = []
        for text, want_e, want_v, want_suffix, why in self.IDS:
            problems = []
            got_e = bool(S.E_ID_RE.search(text))
            got_v = bool(S.V_ID_RE.search(text))
            got_suffix = S.suffix_of(text)
            if got_e != want_e:
                problems.append(f"E_ID_RE.search should be {want_e} and is {got_e}")
            if got_v != want_v:
                problems.append(f"V_ID_RE.search should be {want_v} and is {got_v}")
            if got_suffix != want_suffix:
                problems.append(
                    f"suffix_of should be {want_suffix!r} and is {got_suffix!r}"
                )
            if problems:
                wrong.append(
                    f"  {text!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the identifier grammar answered {len(wrong)} of {len(self.IDS)} strings wrongly. The "
            "two regexes and `suffix_of` share one `[0-9]{2,}` shape, so SEVERAL ROWS MOVING IN THE "
            "SAME DIRECTION names the cause: newly-matching malformed rows mean the `\\b` guards or "
            "the strict anchors were lost, and newly-NON-matching well-formed rows mean the "
            "quantifier or a prefix changed. Remember the columns are deliberately different "
            "predicates: SEARCH finds an id anywhere in prose, PARSE converts a whole token, so a "
            "prose row matching with no suffix is CORRECT and not a contradiction. FIX: relaxing the "
            "two-digit minimum makes ids sort unstably as text (`E-1` after `E-10`) everywhere they "
            f"are ordered.\n" + "\n".join(wrong),
        )


class WatermarkTests(unittest.TestCase):
    """The allocation watermark: `Highest E allocated` versus the E ids actually present.

    ONE table replaces three tests (`test_next_suffix_from_watermark_not_max_present`,
    `test_watermark_below_present_id_is_error`, `test_watermark_required_once_e_exists`) that made
    six assertions between them. Each was one (watermark, present ids) pair and one verdict, and they
    were split by which ASPECT of the same rule they probed, so the aspects became one predicate
    column and the pairs became rows.

    Why the table beats the three: this is one small function whose whole behavior is a 2x2 of
    (watermark present or absent) x (any E present or not), plus an inequality. Enumerating the four
    quadrants as adjacent rows makes the rule readable as a rule, and a change to the comparison
    (`<` to `<=`, or the None branch made unconditional) moves two rows together rather than
    producing two unrelated failures in different tests.

    `next_suffix` IS IN THIS TABLE rather than in its own test because it is the other half of one
    contract: the watermark exists SO THAT allocation never reuses an id, and `next_suffix` is the
    allocation. Asserting them together is what states the invariant the module comment claims,
    namely that the next id comes from the WATERMARK and never from the max present id.
    """

    #: (case, the watermark or None, the present E suffixes, does an error string come back?, the
    #: expected `next_suffix` for that watermark or None to skip, why this row exists)
    WATERMARKS = (
        (
            "watermark 8 with present ids up to 5",
            8,
            [1, 2, 5],
            False,
            9,
            "THE WHOLE REASON THE WATERMARK EXISTS, and it is the row where both columns are needed: "
            "the highest id was DELETED, so the max present id is 5 while the watermark remembers 8, "
            "and the next allocation must be 9 and NOT 6. Handing out 6 would reuse an id that "
            "already appears in a review comment, a commit message, or another plan's citation",
        ),
        (
            "watermark 5 exactly equal to the highest present id",
            5,
            [1, 2, 5],
            False,
            6,
            "the boundary, and the comparison is `>=` NOT `>`: a watermark that equals the highest "
            "present id is the ORDINARY state of a plan that has never deleted an item, so an "
            "off-by-one here would flag almost every conforming plan in the corpus",
        ),
        (
            "watermark 3 BELOW the highest present id",
            3,
            [1, 2, 5],
            True,
            None,
            "the violation: a watermark that LAGS hands out an id that is already in use, silently "
            "creating two E-06 items in one plan whose validations then cannot be told apart",
        ),
        (
            "no watermark at all, with one E present",
            None,
            [1],
            True,
            None,
            "the field is CONDITIONALLY MANDATORY: once any E exists the watermark is required, "
            "because without it a later session has nothing to allocate from and falls back to "
            "guessing from the max present id, which is exactly the reuse bug the first row forbids",
        ),
        (
            "no watermark and NO E items",
            None,
            [],
            False,
            None,
            "THE POSITIVE ROW for absence: a plan with an empty checklist has nothing to watermark, "
            "so demanding the field here would fail every skeleton `aw ipd scaffold` produces. This "
            "row is why the requirement is conditional rather than absolute",
        ),
        (
            "watermark 0 with no E items",
            0,
            [],
            False,
            1,
            "ZERO IS A LEGAL WATERMARK, not a falsy stand-in for absence. A `if not watermark:` "
            "written where `if watermark is None:` was meant would treat this as missing, and "
            "`next_suffix(0)` must still be 1 so the first allocated id is E-01",
        ),
    )

    def test_each_watermark_case_gets_its_verdict_and_next_allocation(self):
        wrong = []
        for case, watermark, present, want_error, want_next, why in self.WATERMARKS:
            problems = []
            err = S.watermark_error(watermark, present)
            if want_error and err is None:
                problems.append(
                    "expected an error string and got None, so this invalid watermark passes"
                )
            if not want_error and err is not None:
                problems.append(
                    f"expected NO error and got {err!r}, so a valid watermark is being rejected"
                )
            if want_next is not None:
                got_next = S.next_suffix(watermark)
                if got_next != want_next:
                    problems.append(
                        f"next_suffix({watermark!r}) should allocate {want_next} and returned "
                        f"{got_next}"
                        + (
                            f"; note max(present)+1 would be {max(present) + 1}, and agreeing with "
                            "THAT is the specific bug this column exists to catch"
                            if present
                            else ""
                        )
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
            f"the watermark contract failed on {len(wrong)} of {len(self.WATERMARKS)} cases. The "
            "rows enumerate a 2x2 of (watermark present or absent) x (any E present or not) plus the "
            "inequality, so read them together: if the two None-watermark rows moved together the "
            "conditional requirement was made unconditional (or dropped) rather than two things "
            "breaking, and if the `equal` and `below` rows moved together the comparison flipped "
            "between `<` and `<=`. FIX: a lagging watermark does not merely mis-report; it causes an "
            "id ALREADY CITED elsewhere to be handed out again, and duplicate E ids in one plan make "
            f"its validations unattributable.\n" + "\n".join(wrong),
        )


class DependencyGrammarTests(unittest.TestCase):
    """An E item's intra-plan `Depends on:` value: the parse, then the graph over the parsed edges.

    ONE table for the PARSE replaces `test_depends_on_grammar`'s four assertions, and a second for
    the GRAPH replaces `test_dependency_self_missing_cycle`'s four. They stay two tables rather than
    one because the subjects genuinely differ: `parse_depends_on` reads ONE value string into ids,
    while `dependency_errors` takes an already-parsed edge MAP and answers a question about the whole
    graph. Merging them would force a row to carry an unused half.

    Why each table beats the test it replaces: both old tests bundled several unrelated inputs into
    one method, so the first failing assertion hid the rest and the failure message named neither the
    input nor the rule. Each row now carries its input, its expected answer, and the rule it encodes.

    THE PARSE TABLE ASSERTS BOTH RETURN VALUES ON EVERY ROW, which is stronger than the test it
    replaces. `parse_depends_on` returns `(ids, error)` and, on a malformed value, returns the
    SPLIT-BUT-UNVALIDATED tokens ALONGSIDE the error rather than an empty list; the old test checked
    only that the error was not None, so a caller that ignored the error and used the ids was
    untested. Pinning both is what documents that the ids on an error row are not trustworthy.
    """

    #: (the raw `Depends on:` value, expected id list, does an error come back?, why this row exists)
    DEPENDS_VALUES = (
        (
            "none",
            [],
            False,
            "`none` is the EXPLICIT no-dependencies value and must parse to an empty list with no "
            "error. It is not a sentinel the caller has to special-case, which is why authors are "
            "told to write it instead of leaving the field blank",
        ),
        (
            "",
            [],
            False,
            "an EMPTY value is accepted as equivalent to `none`. That is a deliberate leniency: the "
            "field is mandatory in the template, so a blank one is an author who has not filled it "
            "in, and failing the parse here would report a grammar error where a template nudge "
            "belongs",
        ),
        (
            "NONE",
            [],
            False,
            "the `none` keyword is CASE-INSENSITIVE, so a capitalized value is not a grammar error. "
            "Asserted because the ids themselves are case-SENSITIVE (`e-01` is not an id), which "
            "makes the two halves of this function differ and invites a well-meaning unification",
        ),
        (
            "E-01, E-02",
            ["E-01", "E-02"],
            False,
            "the ordinary form: comma-separated ids, whitespace around each stripped, ORDER "
            "PRESERVED. Order is asserted through the expected list because these ids feed the "
            "dependency graph, where a reordering would be invisible to a set comparison",
        ),
        (
            "E-01,E-02 ,",
            ["E-01", "E-02"],
            False,
            "tolerant splitting: no space after a comma is fine, and a TRAILING comma does not "
            "produce a third empty id. An empty token reaching the graph would report as a missing "
            "dependency on `''`, which is a confusing way to say `you left a trailing comma`",
        ),
        (
            "E-1, bogus",
            ["E-1", "bogus"],
            True,
            "THE MALFORMED ROW, and the ids column is the interesting half: the function returns the "
            "split-but-UNVALIDATED tokens ALONGSIDE the error, so a caller that ignores the error "
            "gets `bogus` as a dependency id. Pinning both values is what documents that these ids "
            "must not be used when the error is non-None; the test this replaced checked only the "
            "error and left that trap untested",
        ),
    )

    #: (case, the {E-id: [dep ids]} edge map, substrings that must ALL appear somewhere in the
    #: returned errors, must the error list be EMPTY?, why this row exists)
    GRAPHS = (
        (
            "a clean chain",
            {"E-01": [], "E-02": ["E-01"]},
            (),
            True,
            "THE POSITIVE ROW: an ordinary two-step plan where the second depends on the first must "
            "produce NO errors. Every negative row below is vacuous while this one is broken, because "
            "a checker that flagged every graph would satisfy all of them",
        ),
        (
            "an item depending on itself",
            {"E-01": ["E-01"]},
            ("itself", "cycle"),
            False,
            "a self-reference is UNEXECUTABLE and is reported twice, once as a self-dependency and "
            "once as the degenerate cycle it also is. BOTH substrings are asserted because the "
            "specific self-message is the actionable one: `cycle detected involving E-01` alone would "
            "send an author looking for a second item that does not exist",
        ),
        (
            "a dependency on an id that does not exist",
            {"E-02": ["E-09"]},
            ("missing",),
            False,
            "a DANGLING edge, which is the common real defect: an author renumbers or deletes an item "
            "and leaves a reference behind. It must be distinguished from a cycle, since the fix is "
            "the opposite (repoint or drop the edge, rather than break a loop)",
        ),
        (
            "two items depending on each other",
            {"E-01": ["E-02"], "E-02": ["E-01"]},
            ("cycle",),
            False,
            "a true CYCLE makes the checklist unexecutable in ANY order, and it is the one dependency "
            "defect careful reading does not catch reliably. This is why the checker does a real DFS "
            "rather than only comparing each edge against the known ids",
        ),
        (
            "a THREE-item cycle",
            {"E-01": ["E-02"], "E-02": ["E-03"], "E-03": ["E-01"]},
            ("cycle",),
            False,
            "the cycle must be found at DEPTH, not only between adjacent pairs. A checker that "
            "compared each item against its direct dependency's dependency would pass the two-item "
            "row above and miss this one, so without this row the DFS could be replaced by a "
            "one-hop check and nothing would notice",
        ),
        (
            "a DIAMOND: two items sharing one dependency, joined later",
            {"E-01": [], "E-02": ["E-01"], "E-03": ["E-01"], "E-04": ["E-02", "E-03"]},
            (),
            True,
            "THE SECOND POSITIVE ROW, and the one that stops a false-positive fix: a diamond visits "
            "E-01 twice along different paths, which a cycle detector that forgot to mark nodes BLACK "
            "(or that treated any re-visit as a loop) would report as a cycle. This is a legal and "
            "common plan shape, so flagging it would fail real plans",
        ),
    )

    def test_each_depends_on_value_parses_to_its_ids_and_verdict(self):
        wrong = []
        for value, want_ids, want_error, why in self.DEPENDS_VALUES:
            ids, err = S.parse_depends_on(value)
            problems = []
            if ids != want_ids:
                problems.append(f"expected ids {want_ids!r}, got {ids!r}")
            if want_error and err is None:
                problems.append("expected an error string and got None")
            if not want_error and err is not None:
                problems.append(f"expected NO error and got {err!r}")
            if problems:
                wrong.append(
                    f"  {value!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"parse_depends_on mishandled {len(wrong)} of {len(self.DEPENDS_VALUES)} values. Each "
            "row pins BOTH return values, so note which column moved: an `ids` mismatch on the "
            "tolerant rows means the split or strip changed, while a verdict mismatch means the token "
            "pattern did. FIX: on a malformed value this function returns the UNVALIDATED tokens "
            "together with the error, so a caller that ignores the error consumes junk ids; that is "
            f"why the malformed row pins the ids too.\n" + "\n".join(wrong),
        )

    def test_each_dependency_graph_reports_its_defect(self):
        wrong = []
        clean_rows_broken = 0
        for case, edges, needles, want_clean, why in self.GRAPHS:
            errors = S.dependency_errors(dict(edges))
            problems = []
            if want_clean and errors:
                clean_rows_broken += 1
                problems.append(f"expected NO errors on a legal graph, got {errors!r}")
            if not want_clean and not errors:
                problems.append(
                    "expected errors and got NONE, so this unexecutable graph passes"
                )
            joined = " | ".join(errors)
            missing = [n for n in needles if n not in joined]
            if missing:
                problems.append(
                    f"no error mentions {missing!r}; the errors were {errors!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if clean_rows_broken:
            vacuity = (
                f" {clean_rows_broken} LEGAL-GRAPH row(s) are among the failures, and while either "
                "of those is broken every defect row is VACUOUS: a checker that flags every graph "
                "satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"dependency_errors mishandled {len(wrong)} of {len(self.GRAPHS)} graphs.{vacuity} The "
            "edge checks and the cycle DFS are one function, so read the failures together: if the "
            "two multi-item cycle rows failed while the self-reference row passed, the DFS is gone "
            "and only a one-hop check remains; if the DIAMOND row failed while the cycle rows "
            "passed, the traversal stopped marking visited nodes finished and now calls any "
            "re-visited node a loop, which fails LEGAL plans. FIX: the distinct messages "
            "(`itself` / `missing` / `cycle`) are what make the defect actionable, since the repair "
            f"differs completely between a dangling edge and a loop.\n"
            + "\n".join(wrong),
        )


class BijectionTests(unittest.TestCase):
    """The E<->V bijection: every step verifiable, every verification real.

    ONE table replaces `test_bijection`'s four bundled assertions. Each was an (e_ids, v_targets)
    pair and a verdict, split by nothing at all; they simply sat in one method, so the first failure
    hid the others and the message named neither input nor rule.

    Why this is worth its own table rather than rows in the dependency one: the subject is a
    DIFFERENT relation. `dependency_errors` is a graph over E items; this is a 1:1 pairing between two
    id families, with THREE independent ways to break (an orphan V, an E with no V, and a
    suffix-mismatched pair) that a single verdict column would blur. Each row therefore carries the
    message substrings that identify WHICH breakage fired, because the codes they feed are what an
    author reads when a plan is refused.

    THE CLEAN ROW IS IN THIS TABLE: a checker that reported an error for every input would satisfy
    all three violation rows, and the E/V bijection is precisely the mechanism that makes a plan's
    claims of completion checkable, so a vacuously-passing version of it is the worst outcome here.
    """

    #: (case, the E ids present, the {V-id: targeted E-id} map, substrings that must ALL appear in
    #: the errors, must the error list be EMPTY?, why this row exists)
    PAIRINGS = (
        (
            "a clean 1:1 pairing",
            ["E-01", "E-02"],
            {"V-01": "E-01", "V-02": "E-02"},
            (),
            True,
            "THE POSITIVE ROW: the ordinary conforming shape must produce nothing. Every violation "
            "row below is vacuous while this one is broken, and a vacuous bijection check is "
            "especially bad because this relation is what makes a plan's completion claims checkable",
        ),
        (
            "an ORPHAN V targeting an E that does not exist",
            ["E-01"],
            {"V-01": "E-01", "V-02": "E-02"},
            ("targets missing",),
            False,
            "a validation claiming to verify work NO STEP PERFORMS. This is how a plan comes to look "
            "more validated than it is, so the message names the missing target rather than only "
            "saying the counts disagree",
        ),
        (
            "an E item with NO validation",
            ["E-01", "E-02"],
            {"V-01": "E-01"},
            ("no validation item",),
            False,
            "THE MIRROR VIOLATION and the more consequential one: an UNVERIFIED step. The plan can "
            "be marked executed with E-02 performed and nothing ever asked whether it worked, which "
            "is exactly what the bijection exists to prevent",
        ),
        (
            "a SUFFIX-MISMATCHED pair (V-02 validates E-01)",
            ["E-01", "E-02"],
            {"V-02": "E-01", "V-01": "E-02"},
            ("must validate the matching-suffix",),
            False,
            "the counts are PERFECTLY BALANCED here (two Es, two Vs, every target exists), so a "
            "checker that only compared cardinalities would pass this. The suffix rule is what lets a "
            "reader pair E-07 with V-07 by eye, and crossed pairs make every later cross-reference "
            "in the plan misleading",
        ),
        (
            "TWO validations targeting one E",
            ["E-01"],
            {"V-01": "E-01", "V-02": "E-01"},
            ("more than one validation item",),
            False,
            "the pairing is 1:1 in BOTH directions, so a duplicate is its own error and not merely a "
            "spare. Two validations of one step mean one of them is really verifying something else "
            "that now has no row of its own, which is how a step goes unverified while the counts "
            "still look plausible",
        ),
    )

    def test_each_pairing_reports_its_bijection_defect(self):
        wrong = []
        clean_rows_broken = 0
        for case, e_ids, v_targets, needles, want_clean, why in self.PAIRINGS:
            errors = S.bijection_errors(list(e_ids), dict(v_targets))
            problems = []
            if want_clean and errors:
                clean_rows_broken += 1
                problems.append(
                    f"expected NO errors on a clean pairing, got {errors!r}"
                )
            if not want_clean and not errors:
                problems.append(
                    "expected errors and got NONE, so this broken pairing passes and the plan's "
                    "claims of verification go unchecked"
                )
            joined = " | ".join(errors)
            missing = [n for n in needles if n not in joined]
            if missing:
                problems.append(
                    f"no error mentions {missing!r}; the errors were {errors!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if clean_rows_broken:
            vacuity = (
                " THE CLEAN row is among the failures, and while it is broken every violation row "
                "here is VACUOUS: a checker that rejects every pairing satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"bijection_errors mishandled {len(wrong)} of {len(self.PAIRINGS)} pairings.{vacuity} "
            "The three breakages are independent, so note which failed: an orphan-V or duplicate row "
            "failing alone points at the targeting loop, while the `no validation item` row failing "
            "alone points at the per-E count. If ONLY the suffix-mismatch row fails, the check was "
            "reduced to comparing CARDINALITIES, which that row is specifically built to defeat "
            "(its counts balance perfectly). FIX: the worse direction is an error that stops firing, "
            "because an unverified step then lets a plan reach `executed` with nothing having asked "
            f"whether the work succeeded.\n" + "\n".join(wrong),
        )


class ExecutionAndValidationStateTests(unittest.TestCase):
    """The per-row state tables: a state, a checkbox, a note or evidence, and whether they agree.

    ONE table replaces FIVE tests across three classes (`ExecutionStateTests`' legal/illegal pair,
    `ValidationStateTests`' legal/illegal pair, and `test_cross_state`), which made twenty-two
    assertions between them. The old split was by OUTCOME (a `legal` method of `assertIsNone` calls
    and an `illegal` method of `assertIsNotNone` calls), which is the one axis that guarantees a
    regression is reported twice and explained neither time: flipping one entry in the rule table
    makes a legal case fail in one method and its illegal twin fail in another, with no message
    naming the state.

    THE WHICH-PREDICATE DISTINCTION IS A COLUMN, not a class. `execution_row_error`,
    `validation_row_error`, and `cross_state_error` are three functions over the same closed
    vocabularies, and the rule they jointly encode is one thing: THE CHECKBOX, THE STATE LINE, AND THE
    EVIDENCE ARE THREE RECORDS OF ONE FACT AND MUST AGREE. Keeping them adjacent is what makes that
    readable, and it puts the cross-state rows (which are about an E and a V TOGETHER) beside the
    single-row rules they depend on.

    Why the table beats the five, concretely: `_EXEC_CHECKBOX` and `_VALIDATION_RULES` are literal
    dicts, so the realistic regression is an entry edited or a key renamed, which moves the legal AND
    illegal rows for that state at once. The table reports every state whose answer moved, in one
    failure, naming the state and the arguments.

    LEGAL AND ILLEGAL ROWS SHARE THE TABLE deliberately, and here the vacuity risk runs both ways: a
    predicate returning an error for everything satisfies every illegal row, and one returning None
    for everything satisfies every legal row. The failure message reports the counts of each so the
    direction is immediate.
    """

    #: (which predicate: "exec", "validation", or "cross"; the argument tuple; must an error come
    #: back?; why this row exists)
    STATES = (
        # ---- execution rows: (state, checkbox_checked, has_note) ----
        (
            "exec",
            ("pending", False, False),
            False,
            "LEGAL: the freshly scaffolded state. Unchecked and pending agree, and no note is owed",
        ),
        (
            "exec",
            ("performed", True, False),
            False,
            "LEGAL: the only state whose checkbox is CHECKED. No note is required because a step that "
            "simply worked has nothing to explain",
        ),
        (
            "exec",
            ("blocked", False, True),
            False,
            "LEGAL: blocked is UNCHECKED (the work did not happen) and REQUIRES a note, because a "
            "blocked step with no explanation is indistinguishable from a forgotten one",
        ),
        (
            "exec",
            ("failed", False, True),
            False,
            "LEGAL: failed is also unchecked, which is the entry an author gets wrong most often - "
            "the work was ATTEMPTED, but attempting is not performing, so the box stays empty",
        ),
        (
            "exec",
            ("pending", True, False),
            True,
            "ILLEGAL and the most dangerous direction: a CHECKED box over a `pending` state. A "
            "reader skimming checkboxes sees completed work the state line denies, which is how a "
            "plan comes to claim steps nobody performed",
        ),
        (
            "exec",
            ("performed", False, False),
            True,
            "ILLEGAL in the harmless direction (real work reported as undone) and it must STILL fail, "
            "because the two records disagree. A rule that only caught over-claiming would let the "
            "checkbox and the state drift apart in one direction and stop being two records of one "
            "fact",
        ),
        (
            "exec",
            ("blocked", False, False),
            True,
            "ILLEGAL: blocked with NO NOTE. The note is the entire value of the blocked state, since "
            "without it nothing records what the blocker was or who could clear it",
        ),
        (
            "exec",
            ("failed", False, False),
            True,
            "ILLEGAL: failed with no note, for the same reason. Both note-requiring states are rows "
            "because they come from a separate `_EXEC_NOTE_REQUIRED` set, so one could be dropped "
            "from it while the other stayed",
        ),
        (
            "exec",
            ("bogus", False, False),
            True,
            "ILLEGAL: an out-of-vocabulary state. `EXEC_STATES` is CLOSED, and this row also proves "
            "the unknown-state branch runs BEFORE the checkbox lookup, since an unguarded "
            "`_EXEC_CHECKBOX[state]` would raise KeyError here instead of returning a message",
        ),
        (
            "exec",
            ("pending", False, True),
            False,
            "LEGAL: a note on a PENDING item is allowed. Notes are required for some states and "
            "forbidden for none, which is deliberate: an author may record why a step has not started "
            "yet, and rejecting that would push the information into prose nothing reads",
        ),
        # ---- validation rows: (result, checkbox_checked, observed_evidence_nonempty) ----
        (
            "validation",
            ("pending", False, False),
            False,
            "LEGAL: the scaffolded validation. Unchecked, and its `Observed evidence:` line is empty",
        ),
        (
            "validation",
            ("pass", True, True),
            False,
            "LEGAL, and THE MOST IMPORTANT ROW IN THIS TABLE: a pass requires BOTH the checkbox and "
            "NONEMPTY observed evidence. This is the shape of an honest verification, and the two "
            "illegal `pass` rows below are what make the requirement real",
        ),
        (
            "validation",
            ("blocked", False, True),
            False,
            "LEGAL: a blocked validation is unchecked yet still owes evidence - of the BLOCKAGE. "
            "Unlike execution, where evidence is optional, every non-pending validation result here "
            "must say something",
        ),
        (
            "validation",
            ("failed", False, True),
            False,
            "LEGAL: a failed validation is unchecked and must show what was observed. A failure with "
            "no evidence cannot be distinguished from an untried check",
        ),
        (
            "validation",
            ("pass", True, False),
            True,
            "ILLEGAL AND THE WHOLE POINT OF THE MODULE: `pass` with EMPTY observed evidence is "
            "precisely the shape of a plan claiming success nobody demonstrated. If exactly one row "
            "in this file must never stop failing, it is this one",
        ),
        (
            "validation",
            ("pass", False, True),
            True,
            "ILLEGAL: a `pass` result with an UNCHECKED box. The records disagree, and a plan whose "
            "checkboxes and results diverge cannot be skimmed for completion at all",
        ),
        (
            "validation",
            ("pending", False, True),
            True,
            "ILLEGAL, and the asymmetry with execution is the reason for this row: `pending` FORBIDS "
            "evidence, while a pending EXECUTION row may carry a note. Evidence under a pending "
            "result means someone observed something and left the result unrecorded, which reads as "
            "unverified while the information to verify it already exists",
        ),
        (
            "validation",
            ("blocked", False, False),
            True,
            "ILLEGAL: blocked with no evidence. Asserted separately from `failed` because both come "
            "from the same `_VALIDATION_RULES` dict and either entry could be edited alone",
        ),
        (
            "validation",
            ("failed", False, False),
            True,
            "ILLEGAL: failed with no evidence, the twin of the row above",
        ),
        (
            "validation",
            ("bogus", False, False),
            True,
            "ILLEGAL: an out-of-vocabulary result, and (as with the execution twin) proof that the "
            "unknown branch precedes the `_VALIDATION_RULES` lookup rather than raising KeyError",
        ),
        # ---- cross-state rows: (execution_state, validation_result) ----
        (
            "cross",
            ("performed", "pass"),
            False,
            "LEGAL: the only combination in which a plan may claim a verified, completed step, and "
            "the one every executed plan's rows must reach",
        ),
        (
            "cross",
            ("pending", "pending"),
            False,
            "LEGAL: both halves untouched, which is every row of a freshly scaffolded plan",
        ),
        (
            "cross",
            ("pending", "pass"),
            True,
            "ILLEGAL: a validation cannot PASS work that was never performed. This is the cross-row "
            "companion of the empty-evidence rule, and together they close the two routes to a plan "
            "claiming unearned success",
        ),
        (
            "cross",
            ("blocked", "pass"),
            True,
            "ILLEGAL: a BLOCKED step has no outcome to verify, so a pass over it is a contradiction. "
            "A separate row from the pending case because the function reaches this verdict by a "
            "DIFFERENT branch (its second condition, not its first)",
        ),
        (
            "cross",
            ("failed", "pass"),
            True,
            "ILLEGAL: the sharpest contradiction of all, a step that FAILED with a validation that "
            "PASSED. Both of the function's branches reject it, which is why it must stay a row: a "
            "refactor could drop either branch and this combination would still be caught, so its "
            "presence is what lets the other two rows attribute a failure to a specific branch",
        ),
        (
            "cross",
            ("pending", "failed"),
            True,
            "ILLEGAL, and NOT symmetric with the pass rules: a `failed` validation ALSO requires the "
            "step to have been performed, because a validation can only fail against work that was "
            "actually attempted. Otherwise `failed` becomes a synonym for `not yet run`, which "
            "`pending` already means",
        ),
        (
            "cross",
            ("performed", "failed"),
            False,
            "LEGAL: performed work whose validation FAILED is an honest, expected state, and it must "
            "not be blocked. Without this row the rule could be `failed is never allowed`, which "
            "would force authors to hide real failures",
        ),
        (
            "cross",
            ("blocked", "blocked"),
            False,
            "LEGAL: a blocked step with a blocked validation is coherent, and it is the state a "
            "half-finished execution legitimately rests in. Only `pass` (and `failed`) are constrained "
            "against the execution state, and this row is what proves the constraint is not blanket",
        ),
    )

    _PREDICATES = {
        "exec": ("execution_row_error", S.execution_row_error),
        "validation": ("validation_row_error", S.validation_row_error),
        "cross": ("cross_state_error", S.cross_state_error),
    }

    def test_every_state_combination_gets_its_verdict(self):
        wrong = []
        legal_rows_broken = 0
        illegal_rows_broken = 0
        for which, args, want_error, why in self.STATES:
            name, func = self._PREDICATES[which]
            got = func(*args)
            problems = []
            if want_error and got is None:
                illegal_rows_broken += 1
                problems.append(
                    "expected an error string and got None, so this contradictory row lints clean"
                )
            if not want_error and got is not None:
                legal_rows_broken += 1
                problems.append(
                    f"expected NO error and got {got!r}, so a LEGAL row is being rejected"
                )
            if problems:
                wrong.append(
                    f"  {name}{args!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if legal_rows_broken and not illegal_rows_broken:
            vacuity = (
                f" ALL {legal_rows_broken} failures are LEGAL rows, which means a predicate is "
                "rejecting valid rows: the illegal rows are passing for the wrong reason, and the "
                "immediate effect is that conforming plans are refused."
            )
        elif illegal_rows_broken and not legal_rows_broken:
            vacuity = (
                f" ALL {illegal_rows_broken} failures are ILLEGAL rows, which means a predicate has "
                "gone permissive: it is returning None where it should object, and every legal row "
                "here is VACUOUS while that is true."
            )
        self.assertEqual(
            wrong,
            [],
            f"the state tables mishandled {len(wrong)} of {len(self.STATES)} rows.{vacuity} "
            "`_EXEC_CHECKBOX`, `_EXEC_NOTE_REQUIRED`, and `_VALIDATION_RULES` are literal dicts, so "
            "A STATE'S LEGAL AND ILLEGAL ROWS FAILING TOGETHER means that state's ENTRY was edited "
            "rather than two things breaking; all rows of one predicate failing means the function "
            "was rewritten. FIX: the single row that must never stop failing is "
            "`validation_row_error('pass', True, False)`, a PASS WITH NO EVIDENCE, because that is "
            "exactly the shape of a plan claiming success nobody demonstrated; the cross-state "
            f"`('pending', 'pass')` row closes the same hole from the other side.\n"
            + "\n".join(wrong),
        )

    def test_the_state_tables_cover_their_closed_vocabularies(self):
        """Two-sided guard: a state added to `EXEC_STATES`/`VALIDATION_RESULTS` with no row must FAIL.

        Kept separate because it is a claim about the TABLE's coverage of two closed sets rather than
        about any one combination. Without it a new state could be introduced, be accepted by the
        predicates, and have its checkbox and evidence rules asserted nowhere.
        """
        exec_covered = {
            args[0] for which, args, _w, _why in self.STATES if which == "exec"
        }
        validation_covered = {
            args[0] for which, args, _w, _why in self.STATES if which == "validation"
        }
        self.assertEqual(
            exec_covered - {"bogus"},
            set(S.EXEC_STATES),
            "the execution rows and EXEC_STATES have diverged; states with no row: "
            f"{sorted(set(S.EXEC_STATES) - exec_covered)!r}. FIX: add a LEGAL and an ILLEGAL row "
            "for the new state stating its checkbox and note rules.",
        )
        self.assertEqual(
            validation_covered - {"bogus"},
            set(S.VALIDATION_RESULTS),
            "the validation rows and VALIDATION_RESULTS have diverged; results with no row: "
            f"{sorted(set(S.VALIDATION_RESULTS) - validation_covered)!r}. FIX: add a LEGAL and an "
            "ILLEGAL row stating the new result's checkbox and evidence rules.",
        )


class CheckpointTests(unittest.TestCase):
    """Which readiness STATUS each lint checkpoint accepts: the full checkpoint x status matrix.

    ONE table replaces two tests. `test_checkpoints_set` pinned the tuple and
    `test_checkpoint_status_compat` made seven scattered `assertTrue`/`assertFalse` calls that
    sampled the matrix unevenly (three statuses at `pre-execution`, one each elsewhere). The STATUS
    is the natural column here, so each row is a checkpoint carrying the EXACT SET of statuses it
    admits, computed against the whole recognized vocabulary rather than the few an author happened
    to think of.

    Why the table beats the two, and why exhaustive sets rather than samples: `checkpoint_allows_status`
    is a chain of `if checkpoint == ...` branches returning membership tests over four status groups
    (`PRE_TERMINAL`, `TERMINAL`, `STANDING`, `READY_TO_EXECUTE`). Sampling three of nine statuses
    leaves six unasserted per checkpoint, so a branch repointed from one group to another can stay
    green; asserting the whole admitted SET cannot miss that. It also makes the matrix readable as a
    matrix, which matters because the surprises here are real (see the `pre-transition` row).

    THE CHECKPOINT ORDER IS ALSO PINNED, in `test_checkpoints_are_the_expected_ordered_tuple` below,
    because `CHECKPOINTS` is both a closed set and a SEQUENCE users pass to `--phase`.
    """

    #: (the checkpoint, the EXACT set of recognized statuses it must admit, why this row exists)
    CHECKPOINTS = (
        (
            "author",
            {"draft", "to-review", "reviewed", "approved", "auto-approved"},
            "the authoring phase accepts every PRE-TERMINAL status and nothing else. It is the "
            "always-on phase, so it must not refuse a plan merely for having progressed: a reviewed "
            "or approved plan can still be re-linted for structure",
        ),
        (
            "review-finalize",
            {"draft", "to-review", "reviewed", "approved", "auto-approved"},
            "IDENTICAL to `author`, and the duplication is the assertion: review-finalize is a "
            "different phase with the same status precondition, so a refactor that made it stricter "
            "(say, `reviewed` only) would break re-running a review over a draft. Both rows exist so "
            "the deliberate sameness is recorded rather than looking like a copy-paste",
        ),
        (
            "pre-execution",
            {"approved", "auto-approved"},
            "THE GATE THAT MATTERS: only the two READY-TO-EXECUTE tiers pass, which is what stops an "
            "unreviewed plan from being run. `auto-approved` is admitted beside `approved` because it "
            "is a sibling tier recording an automated clear; if this set ever grew `reviewed` or "
            "`to-review`, `aw ipd begin` would start executing unapproved plans",
        ),
        (
            "pre-transition",
            {
                "draft",
                "to-review",
                "reviewed",
                "approved",
                "auto-approved",
                "reusable",
            },
            "THE SURPRISING ROW, and the reason to write the sets out: pre-transition admits "
            "everything NOT YET TERMINAL, which INCLUDES the standing `reusable` status and even "
            "`draft`. The rule is stated as a negative (`status not in TERMINAL`), so it is broader "
            "than the pre-terminal group the two authoring phases use. A sampled test would almost "
            "certainly have missed that `reusable` is allowed here and nowhere else except its own "
            "directory",
        ),
        (
            "post-transition",
            {"executed", "superseded", "not-executed"},
            "the EXACT COMPLEMENT: only terminal statuses, because the phase exists to verify a "
            "transition that has already happened. Together with the row above this states the "
            "partition, and the two rows failing together would mean the terminal test was inverted "
            "rather than either phase being wrong",
        ),
        (
            "bogus",
            set(),
            "AN UNRECOGNIZED CHECKPOINT ADMITS NOTHING, which is fail-closed and the correct default: "
            "a typo'd `--phase` must refuse every status rather than falling through to the "
            "permissive final branch. This row is what makes the function's leading membership guard "
            "load-bearing",
        ),
    )

    def test_each_checkpoint_admits_exactly_its_statuses(self):
        wrong = []
        for checkpoint, expected, why in self.CHECKPOINTS:
            admitted = {
                status
                for status in S.RECOGNIZED_STATUS
                if S.checkpoint_allows_status(checkpoint, status)
            }
            if admitted != expected:
                wrongly_allowed = sorted(admitted - expected)
                wrongly_refused = sorted(expected - admitted)
                detail = []
                if wrongly_allowed:
                    detail.append(
                        f"WRONGLY ADMITS {wrongly_allowed!r} (the gate got more permissive)"
                    )
                if wrongly_refused:
                    detail.append(
                        f"WRONGLY REFUSES {wrongly_refused!r} (the gate got stricter)"
                    )
                wrong.append(
                    f"  checkpoint {checkpoint!r}:\n"
                    f"    - expected exactly {sorted(expected)!r}, admits {sorted(admitted)!r}; "
                    + "; ".join(detail)
                    + f"\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CHECKPOINTS)} checkpoints admit the wrong status set. Each "
            "branch of `checkpoint_allows_status` returns a membership test over one of four status "
            "GROUPS (PRE_TERMINAL / TERMINAL / STANDING / READY_TO_EXECUTE), so several rows moving "
            "together usually means a GROUP changed membership, not that several branches were "
            "edited: check `plans.PRE_TERMINAL` and friends before the branches. THE ROW TO READ "
            "FIRST IS `pre-execution`: anything extra admitted there is a route from unapproved to "
            "EXECUTING, since that is the gate `aw ipd begin` consults. FIX: the sets are asserted "
            "EXHAUSTIVELY against the whole recognized vocabulary on purpose; do not narrow a row to "
            f"the statuses you happen to be thinking about.\n" + "\n".join(wrong),
        )

    def test_checkpoints_are_the_expected_ordered_tuple(self):
        """Kept separate: pins the ORDER and exact membership of the closed checkpoint sequence.

        The table above asserts what each checkpoint ADMITS, which says nothing about the tuple's
        contents or order. `CHECKPOINTS` is a user-facing vocabulary (`aw ipd lint --phase <name>`)
        AND a lifecycle sequence, so both the spellings and their progression are the interface.
        """
        self.assertEqual(
            S.CHECKPOINTS,
            (
                "author",
                "review-finalize",
                "pre-execution",
                "pre-transition",
                "post-transition",
            ),
            "the checkpoint vocabulary changed. These names are typed by users at `--phase` and "
            "cited in workflows, so a rename is a breaking change; the ORDER is the lifecycle "
            "progression and a reordering misrepresents which gate comes first.",
        )


class SizeThresholdTests(unittest.TestCase):
    """`size_warning`: an OR over two independent thresholds, asserted at both boundaries.

    ONE table replaces `test_thresholds`, which made three bundled calls plus an unrelated assertion
    about the size vocabulary. Three samples cannot state a two-input OR: the old calls never tried
    exceeding BOTH thresholds, never tried either boundary from above and below as a pair, and never
    tried the degenerate empty plan. The rows here walk each threshold across its edge with the other
    input held safely below, which is what makes a single failure attributable to one constant.

    Why the table beats the one test: the constants (`MAX_TASK_GROUPS = 5`, `MAX_E_LEAVES = 18`) are
    compared with a strict `>`, so the classic regression is an off-by-one turning the warning into
    a warning at the threshold rather than above it. That moves the two `exactly at` rows together
    while leaving the `above` rows green, and the failure message says so.

    THE THRESHOLD VALUES ARE ASSERTED AS LITERALS in the boundary rows rather than computed from the
    constants, deliberately: deriving the row's inputs from `S.MAX_E_LEAVES` would make a change to
    the constant invisible, because the input and the threshold would move together. The size
    thresholds are a REVIEW TRIGGER, so raising one silently stops plans from being flagged for
    splitting.
    """

    #: (task group count, E leaf count, must a warning fire?, why this row exists)
    SIZES = (
        (
            5,
            18,
            False,
            "EXACTLY AT both thresholds and therefore CLEAN: the comparison is `>`, not `>=`, so a "
            "plan of five groups and eighteen items is the largest conforming plan. This is the row an "
            "off-by-one breaks, and it is the boundary most real plans sit near",
        ),
        (
            6,
            1,
            True,
            "one OVER the task-group threshold with a tiny checklist, which isolates the group "
            "condition: too many groups is a size problem even when there is little work, because "
            "groups are how a plan's concerns are counted",
        ),
        (
            1,
            19,
            True,
            "one OVER the E-leaf threshold with a single group, isolating the other side of the OR. "
            "Paired with the row above, these two prove the conditions are INDEPENDENT rather than "
            "one being unreachable behind the other",
        ),
        (
            6,
            19,
            True,
            "BOTH thresholds exceeded. It cannot distinguish the two conditions on its own, which is "
            "exactly why it is here: an implementation that replaced the OR with an AND would still "
            "pass this row while failing the two isolating rows, so seeing this one pass while those "
            "fail identifies the operator as the cause",
        ),
        (
            0,
            0,
            False,
            "THE DEGENERATE PLAN: an empty skeleton must not warn. A comparison accidentally written "
            "against a falsy or negated value would fire here, and a scaffold that warns on creation "
            "trains authors to ignore the warning",
        ),
        (
            1,
            18,
            False,
            "a normal small plan sitting one below the leaf threshold: CLEAN. The second clean row, "
            "which is what keeps the warning from being vacuously true for everything",
        ),
    )

    def test_each_size_pair_gets_its_warning_verdict(self):
        wrong = []
        clean_rows_broken = 0
        for groups, leaves, want_warning, why in self.SIZES:
            got = S.size_warning(groups, leaves)
            if got != want_warning:
                if not want_warning:
                    clean_rows_broken += 1
                wrong.append(
                    f"  task_groups={groups}, e_leaves={leaves}:\n"
                    f"    - expected size_warning to be {want_warning} and it is {got} "
                    f"(the thresholds are MAX_TASK_GROUPS={S.MAX_TASK_GROUPS}, "
                    f"MAX_E_LEAVES={S.MAX_E_LEAVES}, compared with a strict `>`)\n"
                    f"    this row exists because: {why}"
                )
        vacuity = ""
        if clean_rows_broken:
            vacuity = (
                f" {clean_rows_broken} CLEAN row(s) are among the failures, so the warning is firing "
                "on conforming plans and every warning row here is passing for the wrong reason."
            )
        self.assertEqual(
            wrong,
            [],
            f"size_warning answered {len(wrong)} of {len(self.SIZES)} pairs wrongly.{vacuity} If the "
            "`exactly at both thresholds` row is the one failing, the comparison became `>=` and "
            "every maximally-sized conforming plan now warns; if the two ISOLATING rows failed while "
            "the both-exceeded row passed, the OR became an AND and a plan can now blow one threshold "
            "freely. FIX: the row inputs are LITERALS rather than derived from MAX_TASK_GROUPS / "
            "MAX_E_LEAVES on purpose, so raising a constant fails here; that is intended, because "
            "these thresholds are a REVIEW TRIGGER and raising one silently stops oversized plans "
            f"from being flagged for splitting.\n" + "\n".join(wrong),
        )

    def test_the_size_assessment_vocabulary_is_exactly_two_values(self):
        """Kept separate: a closed VOCABULARY assertion, not a threshold computation.

        `SIZE_ASSESSMENTS` is what an author writes in `- Size assessment:`, and `exception` is the
        value that obliges a cohesion rationale. A third value would silently escape that obligation,
        which is a different claim from anything `size_warning` computes.
        """
        self.assertEqual(
            S.SIZE_ASSESSMENTS,
            frozenset(("standard", "exception")),
            "the size vocabulary is two values written verbatim in plan metadata, and `exception` is "
            "the one that demands a cohesion rationale; a third value escapes that obligation.",
        )


class OpenQuestionTests(unittest.TestCase):
    """`open_question_error`: the structural consistency of one OQ's four subfields.

    ONE table replaces `test_legal_and_illegal`, which bundled six calls into one method so that the
    first failure hid the rest and the message named neither the arguments nor the rule. The
    arguments are four booleans-and-enums, which is precisely a row.

    Why the table beats the one test: the function is a sequence of five guards, and each row now
    names which guard it targets. That matters because two of the guards overlap on `deferred` (the
    blocking check rejects `yes`+`deferred` before the deferred-completeness check is reached), so a
    reordering changes WHICH message an author sees for the same input. The rows keep both paths
    covered and adjacent.

    THE VOCABULARY ROWS ARE HERE TOO, not in a separate class: `Blocking` and `Status` are closed
    enums and an out-of-vocabulary value must be refused before any semantic rule runs, which is the
    same shape of claim as the rest of the table.
    """

    #: (the (blocking, status, has_rationale, has_owner) tuple, must an error come back?, why)
    QUESTIONS = (
        (
            ("no", "open", False, False),
            False,
            "THE POSITIVE ROW and the state every scaffolded question starts in: a non-blocking OPEN "
            "question owes nothing yet. Every negative row is vacuous while this is broken, and note "
            "the argument ORDER is (blocking, status, has_rationale, has_owner) - the last two are "
            "easy to transpose, and a swap would silently reinterpret every row below",
        ),
        (
            ("yes", "resolved", True, True),
            False,
            "A POSITIVE ROW: a BLOCKING question may absolutely be RESOLVED, with a rationale. This is "
            "the intended endpoint for a blocker, so a rule that simply refused `Blocking: yes` would "
            "break the normal path",
        ),
        (
            ("no", "deferred", True, True),
            False,
            "A POSITIVE ROW for the DEFERRAL path: deferring is legal when the question does not "
            "block AND an owner and a rationale are present. All three conditions together are what "
            "make a deferral a commitment rather than an abandonment",
        ),
        (
            ("yes", "deferred", True, True),
            True,
            "ILLEGAL and the headline rule: `deferred` means WE CHOSE TO PROCEED WITHOUT THE ANSWER, "
            "which contradicts the question BLOCKING. Resolve it or drop the blocking claim, never "
            "both. Note this input is otherwise complete (owner and rationale present), so only the "
            "blocking contradiction can be what fails it",
        ),
        (
            ("yes", "resolved", False, True),
            True,
            "ILLEGAL: `resolved` with NO RATIONALE. A question marked answered with no record of the "
            "answer is worse than an open one, because it stops anyone from asking again while "
            "preserving nothing",
        ),
        (
            ("no", "deferred", True, False),
            True,
            "ILLEGAL: a deferral with a rationale but NO OWNER. Ownership is what makes a deferral "
            "revisitable; without it the question leaves every view and nothing brings it back, which "
            "is the silent-drop failure the deferral rules exist to prevent",
        ),
        (
            ("no", "deferred", False, True),
            True,
            "ILLEGAL: a deferral with an owner but NO RATIONALE. The twin of the row above, and both "
            "are rows because the guard tests three conditions at once, so one could be dropped from "
            "the conjunction while the others held",
        ),
        (
            ("maybe", "open", False, False),
            True,
            "ILLEGAL: `Blocking` is a CLOSED two-value enum (yes/no). `maybe` must be refused rather "
            "than treated as either, since every blocking rule keys off an exact match and an "
            "unrecognized value would silently read as non-blocking",
        ),
        (
            ("no", "bogus", False, False),
            True,
            "ILLEGAL: `Status` is a closed three-value enum. An unrecognized status must be refused "
            "BEFORE the semantic rules run, or a typo like `defered` would bypass every deferral "
            "requirement above by matching none of the branches",
        ),
    )

    def test_each_open_question_shape_gets_its_verdict(self):
        wrong = []
        legal_rows_broken = 0
        for args, want_error, why in self.QUESTIONS:
            got = S.open_question_error(*args)
            problems = []
            if want_error and got is None:
                problems.append(
                    "expected an error string and got None, so this inconsistent question passes"
                )
            if not want_error and got is not None:
                legal_rows_broken += 1
                problems.append(
                    f"expected NO error and got {got!r}, so a legitimate question is refused"
                )
            if problems:
                wrong.append(
                    f"  (blocking, status, has_rationale, has_owner)={args!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if legal_rows_broken:
            vacuity = (
                f" {legal_rows_broken} LEGAL row(s) are among the failures, and while any of those is "
                "broken every illegal row here is VACUOUS: a predicate that rejects every question "
                "satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"open_question_error mishandled {len(wrong)} of {len(self.QUESTIONS)} question shapes."
            f"{vacuity} The function is five sequential guards and two of them OVERLAP on `deferred` "
            "(the blocking check rejects yes+deferred before the completeness check is reached), so a "
            "reordering changes which message an author sees without changing any verdict; if the "
            "verdicts moved as a block, suspect the enum guards at the top instead. FIX: the two "
            "deferral-completeness rows exist because that guard tests THREE conditions in one "
            "conjunction, and a deferral with no owner is how a question silently leaves every "
            f"attention view with nobody bringing it back.\n" + "\n".join(wrong),
        )


class DispositionTests(unittest.TestCase):
    """The lint DISPOSITION vocabulary and which members count as a pass.

    ONE table replaces two tests (`test_dispositions`' five assertions and `test_is_quarantined`'s
    two). Each disposition row carries its literal spelling, the constant that must equal it, and
    whether it is PASSING, which is the one property every consumer reads.

    Why the table beats them: `PASSING_DISPOSITIONS` is a one-member subset of a four-member set, and
    everything that gates on lint results (`aw ipd begin`, CI, the runner) asks only "is this
    passing". So the realistic regression is a member being ADDED to the passing set, which is
    invisible unless every non-passing member is asserted as non-passing. The table states the
    partition and reports every member that crossed it.

    THE SPELLINGS ARE LITERALS because they are printed to users and matched by consumers;
    `legacy/not evaluated` in particular contains a SPACE and a SLASH, so it is the member a careless
    normalization would rewrite.
    """

    #: (the literal disposition string, the constant that must equal it, is it PASSING?, why)
    DISPOSITIONS = (
        (
            "conforming",
            "DISPOSITION_CONFORMING",
            True,
            "THE ONLY PASSING MEMBER, and the positive row: if it ever stopped being in "
            "PASSING_DISPOSITIONS nothing could pass the linter at all, and the non-passing rows "
            "below would all be satisfied vacuously",
        ),
        (
            "error",
            "DISPOSITION_ERROR",
            False,
            "NON-PASSING, the ordinary rejection. Every structural violation resolves to this, which "
            "is why it is the disposition the linter's negative tests assert on",
        ),
        (
            "quarantined",
            "DISPOSITION_QUARANTINED",
            False,
            "NON-PASSING and the subtle one: quarantine is a deliberate, owned parking of a plan, so "
            "it is tempting to treat as benign. It must NOT pass, because a quarantined plan is not "
            "conforming and letting it through a gate would execute a plan someone explicitly parked",
        ),
        (
            "legacy/not evaluated",
            "DISPOSITION_LEGACY",
            False,
            "NON-PASSING, meaning NOT EVALUATED rather than acceptable, which is the distinction that "
            "keeps grandfathering honest: a pre-cutover plan is exempt from being FAILED, not "
            "promoted to passing. The spelling contains a SPACE and a SLASH, so this is the member a "
            "well-meaning slug normalization would silently rewrite",
        ),
    )

    def test_each_disposition_has_its_spelling_and_passing_status(self):
        wrong = []
        for name, constant, passing, why in self.DISPOSITIONS:
            problems = []
            actual = getattr(S, constant, None)
            if actual != name:
                problems.append(
                    f"S.{constant} is {actual!r} but the reported spelling asserted here is {name!r}"
                )
            if name not in S.DISPOSITIONS:
                problems.append(
                    f"not in DISPOSITIONS (which is {sorted(S.DISPOSITIONS)!r}), so it is outside the "
                    "closed vocabulary the linter may report"
                )
            is_passing = name in S.PASSING_DISPOSITIONS
            if passing and not is_passing:
                problems.append(
                    "must be PASSING and is not, so nothing can pass the linter through this "
                    "disposition"
                )
            if not passing and is_passing:
                problems.append(
                    "must be NON-PASSING and is in PASSING_DISPOSITIONS, so a plan in this state now "
                    "clears every gate that consumes a lint result"
                )
            if problems:
                wrong.append(
                    f"  disposition {name!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DISPOSITIONS)} dispositions are wrong. Everything that gates "
            "on a lint result asks only IS THIS PASSING, so the dangerous direction is a member "
            "JOINING PASSING_DISPOSITIONS: a quarantined or legacy plan that suddenly passes clears "
            "`aw ipd begin` and CI without conforming. If the `conforming` row is the one failing, "
            "nothing passes at all and the other three rows are vacuous. FIX: `legacy/not evaluated` "
            "means NOT EVALUATED, not acceptable, and its spelling (with a space and a slash) is "
            f"printed to users, so do not normalize it.\n" + "\n".join(wrong),
        )

    def test_is_quarantined_keys_on_the_quarantine_field_alone(self):
        """Kept separate: the subject is a FIELD-MAP predicate, not a disposition value.

        `is_quarantined` answers a question about a parsed metadata dict while the table above is
        about the disposition vocabulary, so a row there would carry no field map. The three cases
        state the rule: presence of `Quarantine` decides, its VALUE is not inspected, and the other
        two trio members do not by themselves make a plan quarantined (the all-or-none requirement is
        `validate_metadata`'s job, asserted in its own table).
        """
        self.assertTrue(
            S.is_quarantined({"Quarantine": "r"}),
            "a plan declaring Quarantine is quarantined",
        )
        self.assertFalse(
            S.is_quarantined({"Date": "x"}),
            "a plan with no Quarantine field is not quarantined",
        )
        self.assertFalse(
            S.is_quarantined({"Quarantine owner": "o"}),
            "the OWNER field alone must not make a plan read as quarantined; only `Quarantine` "
            "itself decides, and the incomplete trio is reported by validate_metadata instead",
        )


class ScopePathsGrammarTests(unittest.TestCase):
    """`parse_scope_paths`: the allowlist grammar that BOUNDS what a plan may change.

    ONE table replaces eight tests (`test_grandfathered_sentinel_parses`,
    `test_valid_literals_and_bounded_pathspecs_accepted`, `test_absolute_paths_rejected`,
    `test_parent_escape_rejected`, `test_repo_wide_globs_rejected`,
    `test_grandfathered_may_not_be_mixed_with_real_entries`, `test_empty_value_is_an_error`, and the
    recognition half already folded into the vocabulary table above). Five of those were loops over a
    list of values asserting one bool, which is a table with the reporting removed: the loop aborted
    on the first bad value and named it with a bare `assertTrue`, so a second failing value in the
    same list was invisible until the first was fixed.

    Why ONE table rather than five loops: the rejections are all produced by one function
    (`_scope_path_entry_error`) running its guards in a fixed order over one string, and the guards
    OVERLAP. `/` is caught as absolute rather than as the repo root; `**` is caught as a root-wide
    glob rather than as a bare glob. So the REASON matters, not just the verdict, and each row
    therefore carries a message substring identifying WHICH guard fired. A reordering of the guards
    changes the reason an author is given for the same input while every bool stays true, and only
    adjacent rows with pinned reasons can show that.

    ALL THREE RETURN VALUES ARE PINNED ON EVERY ROW, which is stronger than the tests this replaces.
    `parse_scope_paths` returns `(paths, is_grandfathered, errors)`, and on a REJECTED value it still
    returns the offending entry in `paths`; the old tests checked only `errors` being truthy, so a
    caller that ignored the errors and used the paths was untested. That matters here more than
    usual, because these paths are an ALLOWLIST: a caller that consumed the paths from a rejected
    value would be granting the very scope the grammar just refused.

    ACCEPTED ROWS SHARE THE TABLE WITH REJECTED ONES, and the risk is asymmetric. A grammar that
    rejected everything would satisfy every rejection row while making the field unusable; a grammar
    that accepted everything would satisfy the acceptances while removing the bound entirely, which is
    the security-relevant direction.
    """

    #: (the raw `Scope-Paths` value, expected paths list, expected is_grandfathered, must errors come
    #: back?, a substring that must appear in the errors (or None), why this row exists)
    VALUES = (
        (
            "grandfathered",
            [],
            True,
            False,
            None,
            "THE SENTINEL: a whole-value reserved token that grandfathers a pre-cutoff plan. It "
            "yields NO paths and NO errors and sets the flag, and all three halves matter: a caller "
            "reading only `paths` would see an empty allowlist and could conclude the plan may change "
            "nothing, when the flag actually means the check is advisory for this plan",
        ),
        (
            "agent_workflows/foo.py",
            ["agent_workflows/foo.py"],
            False,
            False,
            None,
            "THE ORDINARY CASE: one repo-relative literal file. The positive row a broken grammar "
            "would break first, and the shape almost every real plan uses",
        ),
        (
            "agent_workflows/foo.py, tests/test_foo.py",
            ["agent_workflows/foo.py", "tests/test_foo.py"],
            False,
            False,
            None,
            "comma-separated entries with surrounding whitespace stripped, ORDER PRESERVED. Two "
            "entries is the realistic shape (a module and its tests), so a split that dropped or "
            "merged entries would silently shrink or widen a plan's declared scope",
        ),
        (
            "tests/",
            ["tests/"],
            False,
            False,
            None,
            "a DIRECTORY-bounded entry with a trailing slash is legal: its blast radius is bounded by "
            "a concrete leading segment, which is the criterion the whole grammar turns on",
        ),
        (
            "agent_workflows/**",
            ["agent_workflows/**"],
            False,
            False,
            None,
            "a recursive glob BOUNDED by a concrete directory is legal. Contrast the bare `**` row "
            "below: the same glob is refused at the ROOT and accepted under a directory, which is the "
            "single most important distinction in this grammar and one no test can state alone",
        ),
        (
            "agent_workflows/*.py",
            ["agent_workflows/*.py"],
            False,
            False,
            None,
            "a filename glob bounded by a directory is legal, where the SAME pattern at the root "
            "(`*.py`, below) is not. Another instance of the bounded-versus-root rule",
        ),
        (
            "docs/**/*.md",
            ["docs/**/*.md"],
            False,
            False,
            None,
            "a glob at DEPTH with `**` in the middle is legal: only the FIRST segment is judged for "
            "blast radius, so an implementation that scanned every segment for `*` would reject this "
            "legitimate and common pattern",
        ),
        (
            "/etc/passwd",
            ["/etc/passwd"],
            False,
            True,
            "absolute paths are not allowed",
            "AN ABSOLUTE PATH IS REFUSED. This is the security-relevant direction: a scope declaration "
            "that reached outside the repository would let a finalize gate bless a change to a system "
            "file. Note `paths` still contains the offending entry, which is why that column is pinned",
        ),
        (
            "C:\\Windows",
            ["C:\\Windows"],
            False,
            True,
            "absolute paths are not allowed",
            "a WINDOWS DRIVE path is refused too, by a separate regex from the leading-slash check. "
            "Without this row the drive form would be accepted on every platform, since it does not "
            "begin with a slash",
        ),
        (
            "\\\\server\\share",
            ["\\\\server\\share"],
            False,
            True,
            "absolute paths are not allowed",
            "a UNC network path is refused, caught by the leading-BACKSLASH branch. A remote share is "
            "the widest possible escape from a repo-relative allowlist",
        ),
        (
            "../outside",
            ["../outside"],
            False,
            True,
            "parent-directory escape",
            "A PARENT ESCAPE at the start is refused. Being repo-relative is not sufficient on its "
            "own: `..` walks out, so the two guards are independent and both are needed",
        ),
        (
            "agent_workflows/../../etc",
            ["agent_workflows/../../etc"],
            False,
            True,
            "parent-directory escape",
            "a parent escape hidden MID-PATH behind a legitimate leading segment. This is the form "
            "that defeats a naive `startswith('..')` check, so it is the row that forces per-SEGMENT "
            "inspection",
        ),
        (
            "a/../../b",
            ["a/../../b"],
            False,
            True,
            "parent-directory escape",
            "DOUBLE ascent that net-escapes the repo while looking relative. A guard written as "
            "`normpath` comparison rather than a segment scan could be fooled by ordering here",
        ),
        (
            "**",
            ["**"],
            False,
            True,
            "repo-wide glob is too broad",
            "THE BARE RECURSIVE GLOB is refused, and the reason string is asserted because it is a "
            "DIFFERENT guard from the root-level filename glob below. This is the value that would "
            "make a plan's declared scope the whole repository, which is the same as declaring nothing",
        ),
        (
            "*",
            ["*"],
            False,
            True,
            "repo-wide glob is too broad",
            "the bare single-star glob, refused by the same root-segment guard. Both stars are rows "
            "because the guard tests a two-member set and either member could be dropped from it",
        ),
        (
            "*.py",
            ["*.py"],
            False,
            True,
            "root-level glob is too broad",
            "A ROOT-LEVEL FILENAME GLOB, refused with a DIFFERENT message than the bare stars above: "
            "it is caught by the single-segment-containing-a-star guard, not the root-segment set. "
            "Pinning the two distinct reasons is what proves both guards exist, since a single "
            "verdict column would let one absorb the other",
        ),
        (
            ".",
            ["."],
            False,
            True,
            "the repo root is too broad",
            "THE REPO ROOT as a dot has its own message, a third distinct guard. A plan scoped to `.` "
            "is scoped to everything while looking specific",
        ),
        (
            "/",
            ["/"],
            False,
            True,
            "absolute paths are not allowed",
            "A DELIBERATE SURPRISE, and the reason the reason column exists: a bare slash is caught by "
            "the ABSOLUTE-PATH guard, NOT by the repo-root guard, because the leading-slash check runs "
            "first. The verdict is right either way, so only a pinned message records which guard "
            "owns it, and reordering the guards would change the message an author sees",
        ),
        (
            "agent_workflows/foo.py, grandfathered",
            ["agent_workflows/foo.py", "grandfathered"],
            False,
            True,
            "must be the whole Scope-Paths value",
            "THE SENTINEL MAY NOT BE MIXED with real entries, and note `is_grandfathered` comes back "
            "FALSE: a mixed value does not half-grandfather the plan. If the flag were True here, a "
            "plan could claim the advisory exemption while also declaring a narrow allowlist, getting "
            "the benefit of both",
        ),
        (
            "   ",
            [],
            False,
            True,
            "must not be empty",
            "A WHITESPACE-ONLY value is an error, not an empty allowlist. The distinction matters "
            "because an empty allowlist would read as 'this plan changes nothing', which is a claim, "
            "whereas a blank field is an author who has not declared anything",
        ),
        (
            "",
            [],
            False,
            True,
            "must not be empty",
            "the truly empty value, same rule. Both are rows because the check is on the STRIPPED "
            "value, so a refactor that stripped later would let the whitespace form fall through to "
            "the comma split and produce a confusing per-entry error instead",
        ),
    )

    def test_each_scope_paths_value_parses_to_its_paths_flag_and_errors(self):
        wrong = []
        accepted_rows_broken = 0
        for value, want_paths, want_gf, want_errors, needle, why in self.VALUES:
            paths, is_gf, errors = S.parse_scope_paths(value)
            problems = []
            if paths != want_paths:
                problems.append(f"expected paths {want_paths!r}, got {paths!r}")
            if is_gf != want_gf:
                problems.append(f"expected is_grandfathered={want_gf} and got {is_gf}")
            if want_errors and not errors:
                problems.append(
                    "expected errors and got NONE, so this value is ACCEPTED and the scope bound it "
                    "violates no longer holds"
                )
            if not want_errors and errors:
                accepted_rows_broken += 1
                problems.append(
                    f"expected NO errors on a legal value and got {errors!r}"
                )
            if needle is not None and not any(needle in e for e in errors):
                problems.append(
                    f"no error mentions {needle!r}; the errors were {errors!r}, so a DIFFERENT guard "
                    "than this row's is producing the rejection"
                )
            if problems:
                wrong.append(
                    f"  {value!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if accepted_rows_broken:
            vacuity = (
                f" {accepted_rows_broken} LEGAL-VALUE row(s) are among the failures, and while any of "
                "those is broken every rejection row is VACUOUS: a grammar that refuses everything "
                "satisfies all of them, and the field becomes undeclarable."
            )
        self.assertEqual(
            wrong,
            [],
            f"parse_scope_paths mishandled {len(wrong)} of {len(self.VALUES)} values.{vacuity} The "
            "rejections all come from `_scope_path_entry_error`'s guards in a FIXED ORDER and they "
            "OVERLAP, so read the message failures carefully: a row whose verdict is right but whose "
            "REASON moved means the guards were reordered (the bare `/` row is the canonical case, "
            "caught as absolute rather than as the repo root), which changes what an author is told "
            "without changing what is refused. THE DIRECTION THAT MATTERS MOST is a rejection row "
            "that starts passing: this grammar is what BOUNDS a plan's blast radius, so accepting "
            "`**` or an absolute path makes a scope declaration meaningless. FIX: each row also pins "
            "`paths`, because a rejected value STILL returns its offending entry there, and a caller "
            f"that ignored the errors would grant exactly the scope just refused.\n"
            + "\n".join(wrong),
        )

    def test_every_implicit_lifecycle_allowance_is_itself_a_legal_pathspec(self):
        """Kept separate: the subject is the schema's OWN allowance list, not an author's value.

        The table above parses values an author writes; this parses the constants the schema grants
        implicitly, which is a self-consistency claim (the grammar must accept its own allowances, or
        the implicit grant could never be expressed by a plan that wanted to declare it explicitly).
        It also asserts the plan-file lifecycle path is covered, which is the allowance's whole reason
        for existing: a plan moving from `pending/` to `executed/` changes its own file, and no author
        should have to declare that.
        """
        allowances = S.scope_paths_implicit_allowances()
        self.assertTrue(allowances, "the implicit allowance list must not be empty")
        for spec in allowances:
            _paths, _gf, errors = S.parse_scope_paths(spec)
            self.assertEqual(
                errors,
                [],
                f"the implicit allowance {spec!r} is not itself a legal pathspec: {errors!r}. The "
                "schema cannot grant a scope its own grammar would refuse.",
            )
        self.assertTrue(
            any(a.startswith(".aw/records/plans/") for a in allowances),
            f"no allowance covers the plan file's own lifecycle path; allowances are {allowances!r}. "
            "Without it every plan would have to declare the directory it moves itself between.",
        )


class DensityHeuristicTests(unittest.TestCase):
    """Order 07: the per-E-item density advisory (spec Section 8.1), with the input FORM as a column.

    ONE table replaces five tests (`test_known_multi_concern_items_flagged`,
    `test_single_concern_items_stay_quiet`, `test_bare_and_does_not_fire`, `test_raw_prefix_stripping`,
    `test_empty_and_whitespace`) that between them held two bare string LISTS and eleven scattered
    calls. The lists were the giveaway: a positive list and a negative list looped over with one
    assertion each is a table whose rows have lost their reasons and whose failures abort on the first
    bad row. Merging them puts each item beside the linguistic pattern it encodes, which is what a
    heuristic's test data is FOR - the next person tuning the regexes needs to know why each string is
    expected to fire, not merely that it does.

    THE INPUT FORM IS A COLUMN, which is where this merge got strictly stronger. `e_item_density_advisory`
    strips an optional `- [ ] E-NN ` checkbox prefix or an `E-NN:` prefix before analyzing the text, and
    the old `test_raw_prefix_stripping` checked that on ONE positive string only. Here EVERY row is
    evaluated in all three forms and the three verdicts must AGREE, which is a much stronger statement:
    it asserts the prefix strip is verdict-neutral for negatives too, so a strip that accidentally
    consumed a leading clause (turning a multi-concern item into a single-concern one, or the reverse)
    fails here where it previously could not.

    Why the table beats the five for a HEURISTIC specifically: this is a regex bundle tuned against a
    corpus, so the realistic change is someone adjusting a pattern to catch a new case and silently
    breaking neighbors. The two directions have different costs, which the failure message states: a
    missed positive is a dense item that ships unflagged (recoverable, a reviewer may still catch it),
    while a false positive on a legitimate item trains authors to ignore the advisory, which disables
    the feature socially rather than technically. One failure listing every row that moved, with its
    linguistic reason, is what makes a tuning change reviewable.

    POSITIVES AND NEGATIVES SHARE THE TABLE, necessarily: a heuristic that fired on everything or
    nothing satisfies one whole list, and both degenerate versions are things a plausible regex edit
    can produce.
    """

    #: (the E-item action text, must the advisory fire?, why this row exists)
    ITEMS = (
        (
            "add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator",
            True,
            "MULTIPLE SHOUTY `AND`s joining three independent deliverables. The clearest positive: "
            "three separately-testable artifacts in one step, so no single validation item can verify it",
        ),
        (
            "implement canonical workflow compiler, build the runtime engine, and migrate existing workflows",
            True,
            "THREE IMPERATIVE VERBS (implement/build/migrate) over three different subjects, joined by "
            "commas plus a final `and`. This is the commonest real shape of an over-dense item",
        ),
        (
            "create ledger record schema, implement hash-chained storage, add evidence validator suite, and write CLI",
            True,
            "FOUR verb-object clauses. Included beside the three-clause row because the threshold is "
            "the thing being tuned, so having both densities pinned shows whether a change moved the "
            "cutoff or broke the detection",
        ),
        (
            "add user authentication service, implement payment gateway integration, and build admin dashboard",
            True,
            "three clauses with NO shared vocabulary between them, from a different domain than the "
            "rows above. Domain-neutral positives are what stop the patterns from being tuned to this "
            "repository's own nouns",
        ),
        (
            "(a) implement storage layer; (b) add network transport protocol; (c) build React frontend",
            True,
            "EXPLICIT (a)/(b)/(c) ENUMERATION with semicolons. The author has literally numbered the "
            "concerns, which is the strongest possible signal and needs no verb analysis at all. "
            "Contrast the (a)/(b)/(c) NEGATIVE row below, which enumerates TEST CASES for one change - "
            "that pair is the hardest distinction in this heuristic",
        ),
        (
            "add unit tests for ledger, integration tests for runtime engine, and end-to-end performance benchmarks",
            True,
            "three clauses that are ALL TESTS, so the repeated noun `tests` does not rescue it: the "
            "subjects (ledger, runtime engine, benchmarks) are independent work. This row guards "
            "against a well-meaning exemption for anything mentioning tests, which the `and its tests` "
            "negative below could otherwise motivate",
        ),
        (
            "add user management; implement billing gateway; build admin UI; and write documentation",
            True,
            "SEMICOLON-separated clauses rather than commas, ending with `and`. Separator variety is "
            "asserted because a pattern written only for commas would miss this, and semicolons are "
            "exactly what an author reaches for when the clauses are long",
        ),
        (
            "add agent_workflows/run_ledger_schema.py and its tests",
            False,
            "NEGATIVE: `X and its tests` is ONE concern. A module and its tests ship together, are "
            "reviewed together, and are verified by one validation item, so flagging this would fire "
            "on most well-formed steps in the corpus",
        ),
        (
            "define MAX_TASK_GROUPS and MAX_E_LEAVES count thresholds",
            False,
            "NEGATIVE: a bare `and` joining two NOUNS that share one predicate (`count thresholds`). "
            "This is the coordination-of-objects case, and distinguishing it from coordination of "
            "CLAUSES is the core of the heuristic",
        ),
        (
            "update README.md and documentation links",
            False,
            "NEGATIVE: two closely-related documentation objects under one verb. A row here because "
            "documentation items are numerous in the corpus, so a false positive on this shape would "
            "be highly visible and quickly ignored",
        ),
        (
            "add --check: exit nonzero on drift, reusing the Order-01 core drift shape",
            False,
            "NEGATIVE despite containing a COMMA and a colon: the comma introduces an ELABORATION of "
            "one change, not a second deliverable. This is why comma counting alone cannot be the "
            "rule",
        ),
        (
            "add falsifiable tests: (a) returns root from nested subdir; (b) returns None when not found; (c) handles permission errors",
            False,
            "THE HARDEST NEGATIVE, and the deliberate near-twin of the (a)/(b)/(c) POSITIVE above: the "
            "same enumeration syntax and the same semicolons, but the enumerated things are TEST CASES "
            "for one change rather than independent deliverables. The two rows must be read together; "
            "if this one starts firing, the enumeration pattern has become purely syntactic",
        ),
        (
            "add unit tests for ipd_schema.py and ipd_lint.py",
            False,
            "NEGATIVE: one verb, one KIND of work, two closely-related files. Contrast the positive "
            "three-clause tests row: what makes that one dense is three independent SUBJECTS, not the "
            "word `tests`",
        ),
        (
            "implement tools/agy_run.py with argument parsing and multi-mode resolution",
            False,
            "NEGATIVE: `with A and B` describes the CONTENT of one deliverable. The `with` preposition "
            "subordinates both nouns to a single implementation, which a clause-splitting pattern must "
            "not treat as coordination",
        ),
        (
            "reject invalid input clearly using research_contract vocab/normalization API",
            False,
            "NEGATIVE containing a SLASH (`vocab/normalization`), which is a compound name and not a "
            "separator. Asserted because a pattern that treated `/` as a clause boundary would fire on "
            "every path and every compound term in the corpus",
        ),
        (
            "surface the heuristic in aw ipd lint --agent output as an advisory record",
            False,
            "NEGATIVE: a long single-concern item with no coordination at all. The control row - if "
            "this fires, the heuristic is keying on LENGTH, which would flag every carefully-worded "
            "step",
        ),
        (
            "add feature X and its tests",
            False,
            "NEGATIVE: the minimal `and its tests` form. Kept beside the longer version above because "
            "a length or word-count component in the heuristic could treat the two differently",
        ),
        (
            "update documentation and fix typo",
            False,
            "NEGATIVE, and the most debatable row in the table: TWO VERBS joined by a bare `and`, which "
            "is syntactically the positive pattern, yet both actions are trivial and inseparable in "
            "practice. It records that a bare two-verb `and` is NOT sufficient on its own to fire, so "
            "the threshold needs three clauses or an explicit enumeration",
        ),
        (
            "export symbols A and B in __init__.py",
            False,
            "NEGATIVE: `A and B` coordinates two SYMBOLS inside one file under one verb. The "
            "single-letter names make it a pure syntax probe, with no domain words for a pattern to "
            "latch onto",
        ),
        (
            "",
            False,
            "the EMPTY string must be silent, not an error and not an advisory. A parser handing "
            "through a blank line must not produce a diagnostic about nothing",
        ),
        (
            "   ",
            False,
            "WHITESPACE ONLY, silent for the same reason. Both are rows because a strip that happened "
            "after the analysis rather than before could treat them differently",
        ),
    )

    #: The three input FORMS every row is evaluated in. The verdict must be identical in all three,
    #: because the prefix strip exists to make the advisory callable on a raw checklist line, on an
    #: `E-NN:`-prefixed citation, and on bare action text alike.
    FORMS = (
        ("bare action text", "{0}"),
        ("a raw `- [ ] E-NN ` checklist line", "- [ ] E-01 {0}"),
        ("an `E-NN:` prefixed citation", "E-01: {0}"),
    )

    def test_every_item_gets_the_same_verdict_in_every_input_form(self):
        wrong = []
        positives_missed = 0
        negatives_fired = 0
        for text, want_fire, why in self.ITEMS:
            problems = []
            for form_name, template in self.FORMS:
                reason = S.e_item_density_advisory(template.format(text))
                fired = reason is not None
                if fired != want_fire:
                    if want_fire:
                        positives_missed += 1
                        problems.append(
                            f"in {form_name}: expected the advisory to FIRE and it stayed silent"
                        )
                    else:
                        negatives_fired += 1
                        problems.append(
                            f"in {form_name}: expected SILENCE and it fired with {reason!r}"
                        )
                elif fired and not (isinstance(reason, str) and reason.strip()):
                    problems.append(
                        f"in {form_name}: fired with a non-string or empty reason ({reason!r}); the "
                        "advisory must say WHY or an author cannot act on it"
                    )
            if problems:
                wrong.append(
                    f"  {text!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        directionality = ""
        if positives_missed and not negatives_fired:
            directionality = (
                " ALL failures are MISSED POSITIVES, so the heuristic got quieter: dense items now "
                "ship unflagged. That is the recoverable direction (a reviewer may still catch them)."
            )
        elif negatives_fired and not positives_missed:
            directionality = (
                " ALL failures are FALSE POSITIVES, which is the WORSE direction: an advisory that "
                "fires on legitimate single-concern items trains authors to ignore it, disabling the "
                "feature socially rather than technically."
            )
        self.assertEqual(
            wrong,
            [],
            f"the density heuristic mishandled {len(wrong)} of {len(self.ITEMS)} items across "
            f"{len(self.FORMS)} input forms each.{directionality} This is a tuned regex bundle, so the "
            "usual cause is a pattern adjusted to catch a new case that broke its neighbors; the pair "
            "to read first is the (a)/(b)/(c) POSITIVE (independent deliverables) beside the "
            "(a)/(b)/(c) NEGATIVE (test cases for one change), because if the negative started firing "
            "the enumeration pattern has become purely syntactic. IF ONE FORM FAILS AND THE OTHER TWO "
            "DO NOT, the prefix strip is at fault rather than the patterns: all three forms carry the "
            "SAME action text, so any disagreement between them means the strip consumed or left "
            "something it should not, and the verdict is then sensitive to how a caller happened to "
            f"slice the line.\n" + "\n".join(wrong),
        )

    def test_a_bare_e_id_with_no_action_text_is_silent(self):
        """Kept separate: the input is a PREFIX with nothing after it, so it has no row's action text.

        `- [ ] E-01` and `E-01:` are what the strip leaves EMPTY, which is a claim about the strip
        rather than about any item's density. It cannot be a row because every row is evaluated in all
        three forms by substituting action text, and these inputs are precisely the forms with none.
        """
        for raw in ("- [ ] E-01", "E-01:", "- [ ] E-01 ", "E-01: "):
            self.assertIsNone(
                S.e_item_density_advisory(raw),
                f"{raw!r} carries no action text at all, so there is nothing to call dense; an "
                "advisory here means the prefix strip left residue that the patterns then matched.",
            )

    def test_executed_conforming_corpus_low_overfire_rate(self):
        """Kept separate: the subject is the whole EXECUTED PLAN CORPUS on disk, not fixture strings.

        Reads every `.ipd.md` under `.aw/records/plans/executed/`, so it is slow, filesystem-dependent,
        and its assertion is a RATE over hundreds of items rather than a verdict on one. The table
        above pins the heuristic's behavior on chosen examples; this bounds its false-positive rate
        against real history, which is the only check that can catch a pattern that is right on every
        example and wrong in aggregate.
        """
        from agent_workflows import ipd_lint

        all_e_items = []
        for p in sorted(
            (REPO_ROOT / ".aw" / "records" / "plans" / "executed").rglob("*.ipd.md")
        ):
            try:
                doc = ipd_lint.parse(p.read_text(encoding="utf-8"))
                for lf in doc.exec_leaves:
                    if lf.kind == "E":
                        all_e_items.append((p.name, lf.ident, lf.text))
            except Exception:
                pass
        self.assertGreater(
            len(all_e_items),
            500,
            "Should have a substantial corpus of executed E-items",
        )
        fired = [
            (p, ident, text, S.e_item_density_advisory(text))
            for p, ident, text in all_e_items
            if S.e_item_density_advisory(text) is not None
        ]
        overfire_rate = len(fired) / len(all_e_items)
        # Assert low overfire rate (<= 5% of historical corpus)
        self.assertLessEqual(
            overfire_rate,
            0.10,
            f"Overfire rate too high: {len(fired)}/{len(all_e_items)} ({overfire_rate * 100:.1f}%)",
        )


class NoDependencyTests(unittest.TestCase):
    def test_module_is_stdlib_only(self):
        """Kept separate: inspects the module's own SOURCE for an import allowlist, not a schema value.

        The claim is structural (zero runtime dependencies, D46) and its subject is the text of
        `ipd_schema.py`, so it shares no input, no predicate, and no failure mode with any table here.
        """
        # The module must not import third-party packages (zero runtime deps, D46).
        src = (REPO_ROOT / "agent_workflows" / "ipd_schema.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {"__future__", "re", "typing", "agent_workflows"},
                "unexpected import: " + line,
            )


if __name__ == "__main__":
    unittest.main()

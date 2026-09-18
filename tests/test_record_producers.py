"""Unit tests for the record/state class consolidation onto the layout model.

Spec `kw5y2s` Section 5.1 items 2 and 4; Set `wslayout` Order 03 (`rodj06`).

WHAT THIS FILE FENCES, and why each fence is here rather than assumed. Order 03 replaced three
hand-written enums and four hand-written subpath maps in `agent_workflows/record_producers.py` with
values DERIVED from `agent_workflows/layout.py`. A derivation is exactly the kind of change that can
look green while quietly altering a routing path, so these tests assert the three properties whose
violation the plan-review identified as the concrete failure modes:

1. THE `records` EMPTY-SUBPATH CARVE-OUT (spec Section 3.2.1, plan-review PR-001). `RecordClass`
   keeps a `RECORDS` member and it maps to the EMPTY string. A naive derivation would either drop
   the member (breaking every existing `RecordClass.RECORDS` caller) or give it `subpath="records"`,
   producing a nonsensical `records/records/` path.
2. THE PRESERVED LEGACY `.agents/` READ PATHS. `_LEGACY_RECORD_CLASS_SUBPATHS` stays DECOUPLED from
   the final map so `resolve_record_read_paths` still finds `.agents/docs/specs` and friends after
   the final layout was flattened out of `docs/`.
3. THE WRITE GUARD, which is a security boundary and must reject exactly what it rejected before.

NON-NARROWING IS THE OTHER HALF. The consolidation is only behavior-preserving if every class that
existed before still exists with the same value, so the pre-Order-03 nine are pinned LITERALLY here
rather than compared against the model (a model comparison would be a tautology once the module
derives from it, and could not catch a narrowing at all - the same reasoning Order 02 applied when
it converted the parity assertions in `tests/test_layout.py`).

NO THIRD-PARTY IMPORTS; plain stdlib `unittest`, matching the rest of the suite.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import layout as _layout
from agent_workflows import record_producers as RP
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import (
    DeliveryMode,
    LogicalRoot,
    RecordsBackend,
    RootClass,
)

# The record classes that existed BEFORE the Order 03 consolidation, with their exact values. Pinned
# as a literal so a narrowing fails here; see the module docstring.
_PRE_CONSOLIDATION_RECORD_CLASSES = (
    "plans",
    "specs",
    "research",
    "records",
    "prompts",
    "comms",
    "walkthroughs",
    "releases",
    "reviews",
)

# The three classes the maintainer's UNION ruling adds (spec Section 3.2, Section 5.1 item 2).
_UNION_NET_NEW_RECORD_CLASSES = ("backlog", "roadmaps", "other")


class DerivedRecordClassTests(unittest.TestCase):
    """`RecordClass` is derived from the layout model without narrowing (E-01).

    ONE table replaces three tests of identical shape (assert a member ATTRIBUTE resolves, assert its
    VALUE, assert that value is in the live vocabulary). The table is better than the three for the
    reason that governs this whole file: `RecordClass` is a CLOSED SET now DERIVED from
    `layout.py`, so the realistic failure is not one member breaking on its own, it is the
    derivation changing its naming rule or its source vocabulary and moving SEVERAL members at
    once. Three tests report that as three unrelated red lines, each stopping at its first bad
    assertion; the table reports it as one failure listing every member that moved, which is the
    shape of the actual defect.

    The `era` column is what keeps the NON-NARROWING guarantee literal (see the module docstring):
    the pre-Order-03 nine are pinned by name here, not compared against the model, and the table's
    own era partition is checked against the pinned tuples so a row cannot be quietly reclassified
    or dropped out of the table to make a narrowing pass.
    """

    #: (member attribute, expected value, era, why this row exists)
    MEMBERS = (
        (
            "PLANS",
            "plans",
            "pre",
            "the oldest record class; every plan workflow routes through it",
        ),
        ("SPECS", "specs", "pre", "spec tree, flattened out of docs/ by Order 07"),
        ("RESEARCH", "research", "pre", "research tree, also de-nested from docs/"),
        (
            "RECORDS",
            "records",
            "pre",
            "the ROOT ALIAS the carve-out exists for; dropping it breaks every "
            "RecordClass.RECORDS caller",
        ),
        ("PROMPTS", "prompts", "pre", "prompts tree"),
        ("COMMS", "comms", "pre", "inter-agent comms tree"),
        (
            "WALKTHROUGHS",
            "walkthroughs",
            "pre",
            "walkthroughs tree, the third member of the de-nested doc family",
        ),
        ("RELEASES", "releases", "pre", "release records"),
        ("REVIEWS", "reviews", "pre", "review records"),
        (
            "BACKLOG",
            "backlog",
            "net-new",
            "gained by the maintainer's UNION ruling (spec 3.2); the tree already exists on disk",
        ),
        (
            "ROADMAPS",
            "roadmaps",
            "net-new",
            "gained by the UNION ruling, likewise already on disk",
        ),
        (
            "OTHER",
            "other",
            "net-new",
            "the computed COMPLEMENT of the owned trees; a class with no directory of its own",
        ),
    )

    def test_every_record_class_member_resolves_to_its_pinned_value(self) -> None:
        live = {c.value for c in RP.RecordClass}
        wrong = []
        for attr, expected, era, why in self.MEMBERS:
            member = getattr(RP.RecordClass, attr, None)
            if member is None:
                wrong.append(
                    "  RecordClass.{0} does not exist (expected value {1!r})\n"
                    "    this row exists because: {2}".format(attr, expected, why)
                )
                continue
            if member.value != expected:
                wrong.append(
                    "  RecordClass.{0}.value expected {1!r}, got {2!r}\n"
                    "    this row exists because: {3}".format(
                        attr, expected, member.value, why
                    )
                )
            if expected not in live:
                wrong.append(
                    "  {0!r} is missing from the live vocabulary {1}\n"
                    "    this row exists because: {2}".format(
                        expected, sorted(live), why
                    )
                )
        # The table's own era partition must still match the literally pinned tuples, so a
        # narrowing cannot be laundered by editing the table instead of the source.
        for era, pinned in (
            ("pre", _PRE_CONSOLIDATION_RECORD_CLASSES),
            ("net-new", _UNION_NET_NEW_RECORD_CLASSES),
        ):
            tabled = {v for _a, v, e, _w in self.MEMBERS if e == era}
            if tabled != set(pinned):
                wrong.append(
                    "  TABLE COVERAGE: the {0!r} rows are {1} but the pinned tuple is {2}; the "
                    "table itself was edited rather than the source".format(
                        era, sorted(tabled), sorted(pinned)
                    )
                )
        self.assertEqual(
            wrong,
            [],
            "record_producers.RecordClass mishandled {0} of {1} members. The enum is DERIVED from "
            "layout.py and its member names come from upper-casing the value, so several rows "
            "failing together usually means the derivation's naming rule or its source vocabulary "
            "changed rather than {1} independent breakages. FIX: compare "
            "`layout.build_default_layout().record_classes` against this table before touching "
            "either.\n".format(len(wrong), len(self.MEMBERS))
            + "\n".join(wrong),
        )

    def test_class_set_is_exactly_the_model_vocabulary(self) -> None:
        """Kept separate: a set-equality guard against the model, not a per-member row."""
        model = _layout.build_default_layout()
        self.assertEqual(
            {c.value for c in RP.RecordClass},
            set(model.record_classes),
            "the enum must be the model's vocabulary, no more and no less",
        )

    def test_str_mixin_is_preserved_so_value_comparisons_keep_working(self) -> None:
        """Kept separate: asserts the enum's TYPE and protocol, not any member's value."""
        # `RecordClass` has always been a `str` subclass, and callers compare members to plain
        # strings and use them as dict keys. Losing the mixin would break those silently.
        self.assertIsInstance(RP.RecordClass.PLANS, str)
        self.assertEqual(RP.RecordClass.PLANS, "plans")
        self.assertEqual({RP.RecordClass.PLANS: 1}["plans"], 1)

    def test_enum_module_is_this_module_so_members_stay_picklable(self) -> None:
        """Kept separate: asserts an enum METADATA attribute, not any member's value."""
        # The functional `Enum` API otherwise records the calling frame's module, which breaks
        # pickling of a member; the derivation sets `__module__` explicitly.
        self.assertEqual(RP.RecordClass.__module__, "agent_workflows.record_producers")

    def test_state_class_enums_are_derived_and_unchanged(self) -> None:
        """Kept separate: two DIFFERENT enums, pinned as ordered lists rather than per-member rows,
        because for these the ORDER is the contract the state roots are laid out in."""
        self.assertEqual(
            [c.value for c in RP.DurableStateClass],
            ["install", "history", "actions", "migrations", "routing_receipts"],
        )
        self.assertEqual(
            [c.value for c in RP.RuntimeStateClass],
            ["transactions", "locks", "staging", "backups", "cache", "tmp"],
        )
        self.assertEqual(
            RP.DurableStateClass.ROUTING_RECEIPTS.value, "routing_receipts"
        )
        self.assertEqual(RP.RuntimeStateClass.TRANSACTIONS.value, "transactions")


#: Sentinel for a class that must have NO literal key in `_RECORD_CLASS_SUBPATHS`.
_NO_KEY = "<no literal key>"


class RecordsCarveOutTests(unittest.TestCase):
    """The FINAL subpath map: two carve-outs to "" and a flat, non-empty subpath for everyone else.

    ONE table replaces six tests that each poked one or three entries of the SAME dict
    (`_RECORD_CLASS_SUBPATHS`) plus its accessor. The table is better because the map is a closed
    vocabulary DERIVED from `layout.py`: the realistic defect is the derivation changing shape (the
    carve-out lost, `docs/` nesting reintroduced into the final map, a literal `other` key invented),
    and each of those moves SEVERAL entries at once. Six tests report that as six red lines whose
    relationship a reader has to reconstruct; the table reports every wrong entry in one failure,
    where the pattern across rows is what identifies the cause.

    Both columns are asserted per row on purpose. `_RECORD_CLASS_SUBPATHS` is the literal dict and
    `_record_class_subpath()` is the accessor callers are told to prefer, and they DISAGREE by design
    for the two carve-outs (`records` has an empty-string key; `other` has no key at all yet must
    still resolve to ""). Asserting only one column would let the two drift apart silently.
    """

    #: (record class, expected literal map entry or _NO_KEY, expected accessor result, why)
    SUBPATHS = (
        (
            "records",
            "",
            "",
            "THE CARVE-OUT (spec 3.2.1, PR-001): the root ALIAS must map to the EMPTY string. A "
            "naive derivation giving it subpath='records' under a root already ending in `records` "
            "produces the nonsensical `.aw/records/records/`",
        ),
        (
            "other",
            _NO_KEY,
            "",
            "the computed COMPLEMENT: `.aw/records/other/` does not exist, so a literal entry would "
            "manufacture a directory the sweep never uses, yet the accessor must still answer ''",
        ),
        ("plans", "plans", "plans", "the ordinary case: subpath equals the class name"),
        (
            "specs",
            "specs",
            "specs",
            "Order 07 flattened the doc family out of `docs/`; the FINAL map must be flat (only the "
            "LEGACY map keeps `docs/specs`)",
        ),
        ("research", "research", "research", "the second de-nested doc-family class"),
        (
            "walkthroughs",
            "walkthroughs",
            "walkthroughs",
            "the third de-nested doc-family class",
        ),
        ("prompts", "prompts", "prompts", "flat, non-empty"),
        ("comms", "comms", "comms", "flat, non-empty"),
        ("releases", "releases", "releases", "flat, non-empty"),
        ("reviews", "reviews", "reviews", "flat, non-empty"),
        (
            "backlog",
            "backlog",
            "backlog",
            "net-new by the union ruling, and it must MATCH the tree already on disk",
        ),
        (
            "roadmaps",
            "roadmaps",
            "roadmaps",
            "net-new by the union ruling, likewise already on disk",
        ),
    )

    def test_every_class_maps_to_its_pinned_subpath_in_both_the_dict_and_the_accessor(
        self,
    ) -> None:
        wrong = []
        for name, expected_entry, expected_accessor, why in self.SUBPATHS:
            present = name in RP._RECORD_CLASS_SUBPATHS
            if expected_entry is _NO_KEY:
                if present:
                    wrong.append(
                        "  {0!r} must have NO literal key, but the dict holds {1!r}\n"
                        "    this row exists because: {2}".format(
                            name, RP._RECORD_CLASS_SUBPATHS[name], why
                        )
                    )
            elif not present:
                wrong.append(
                    "  {0!r} is MISSING from _RECORD_CLASS_SUBPATHS (expected {1!r})\n"
                    "    this row exists because: {2}".format(name, expected_entry, why)
                )
            elif RP._RECORD_CLASS_SUBPATHS[name] != expected_entry:
                wrong.append(
                    "  _RECORD_CLASS_SUBPATHS[{0!r}] expected {1!r}, got {2!r}\n"
                    "    this row exists because: {3}".format(
                        name, expected_entry, RP._RECORD_CLASS_SUBPATHS[name], why
                    )
                )
            got_accessor = RP._record_class_subpath(name)
            if got_accessor != expected_accessor:
                wrong.append(
                    "  _record_class_subpath({0!r}) expected {1!r}, got {2!r}\n"
                    "    this row exists because: {3}".format(
                        name, expected_accessor, got_accessor, why
                    )
                )
        # Coverage: every key the map actually has must be a row, so a class added to the model
        # cannot arrive with an unasserted (possibly empty or `docs/`-nested) subpath.
        tabled = {n for n, entry, _a, _w in self.SUBPATHS if entry is not _NO_KEY}
        if tabled != set(RP._RECORD_CLASS_SUBPATHS):
            wrong.append(
                "  TABLE COVERAGE: the map holds {0} but the table asserts {1}; every key needs a "
                "row or its subpath is unasserted".format(
                    sorted(RP._RECORD_CLASS_SUBPATHS), sorted(tabled)
                )
            )
        self.assertEqual(
            wrong,
            [],
            "record_producers' FINAL subpath map is wrong for {0} of {1} classes. Every entry is "
            "derived from layout.py, so several rows failing together usually means one structural "
            "change (the records carve-out dropped, `docs/` nesting reintroduced, or a literal "
            "`other` key invented) rather than {1} independent mistakes. FIX: read "
            "`layout.get_record_subpath` and the carve-out note above `_RECORD_CLASS_SUBPATHS`, not "
            "this table.\n".format(len(wrong), len(self.SUBPATHS))
            + "\n".join(wrong),
        )


class LegacyReadPathTests(unittest.TestCase):
    """`_LEGACY_RECORD_CLASS_SUBPATHS` stays decoupled from the final map, but BOUNDEDLY (F-3).

    ONE table replaces four tests that each asserted one or three entries of the SAME dict, plus a
    set-difference computed over it. The table is better for the reason the decoupling exists: only
    three classes ever had a legacy `docs/` tree, so the interesting property is not any single entry
    but the PARTITION - which classes override and which inherit their final subpath by absence. A
    regression is a class crossing that line (the `**` spread accidentally overriding everything, or
    the doc-family overrides being dropped when the final map was flattened), which moves several
    entries at once. Four tests report that as four red lines; the table reports the partition.

    The `overrides` column carries the bound directly: a True row asserts a legacy path DIFFERENT
    from the final one, a False row asserts it is IDENTICAL to the final one. That replaces the old
    set-difference assertion without losing it, because a row silently changing side fails.
    """

    #: (record class, expected legacy subpath, overrides the final map?, why this row exists)
    LEGACY = (
        (
            "specs",
            "docs/specs",
            True,
            "the legacy `.agents/docs/specs` tree must stay readable after Order 07 flattened the "
            "FINAL map to `specs`; this decoupling is the whole point of the second map",
        ),
        (
            "research",
            "docs/research",
            True,
            "second of exactly three legacy `docs/` trees",
        ),
        (
            "walkthroughs",
            "docs/walkthroughs",
            True,
            "third of exactly three legacy `docs/` trees",
        ),
        (
            "records",
            "",
            False,
            "the records carve-out must SURVIVE into the legacy map too, or a migration read builds "
            "`.agents/records/`",
        ),
        (
            "backlog",
            "backlog",
            False,
            "correct-by-absence, as the hand-written `**` spread provided: no override means reuse "
            "the final subpath",
        ),
        (
            "roadmaps",
            "roadmaps",
            False,
            "net-new relative to `.agents/`, so no override",
        ),
        (
            "reviews",
            "reviews",
            False,
            "net-new relative to the legacy tree and carries a deliberate no-override note",
        ),
        (
            "plans",
            "plans",
            False,
            "never lived under `docs/`, so it must not inherit the prefix",
        ),
        ("prompts", "prompts", False, "never lived under `docs/`"),
        ("comms", "comms", False, "never lived under `docs/`"),
        ("releases", "releases", False, "never lived under `docs/`"),
    )

    def test_the_legacy_map_overrides_exactly_the_doc_family_and_inherits_the_rest(
        self,
    ) -> None:
        wrong = []
        for name, expected, overrides, why in self.LEGACY:
            if name not in RP._LEGACY_RECORD_CLASS_SUBPATHS:
                wrong.append(
                    "  {0!r} is MISSING from _LEGACY_RECORD_CLASS_SUBPATHS, so a migration read "
                    "raises KeyError for a class that routes fine going forward\n"
                    "    this row exists because: {1}".format(name, why)
                )
                continue
            got = RP._LEGACY_RECORD_CLASS_SUBPATHS[name]
            if got != expected:
                wrong.append(
                    "  _LEGACY_RECORD_CLASS_SUBPATHS[{0!r}] expected {1!r}, got {2!r}\n"
                    "    this row exists because: {3}".format(name, expected, got, why)
                )
            final = RP._RECORD_CLASS_SUBPATHS.get(name)
            if overrides and got == final:
                wrong.append(
                    "  {0!r} must OVERRIDE the final subpath but both are {1!r}; the legacy read "
                    "path collapsed into the flat one\n    this row exists because: {2}".format(
                        name, got, why
                    )
                )
            if not overrides and got != final:
                wrong.append(
                    "  {0!r} must INHERIT its final subpath {1!r} by absence, but the legacy map "
                    "holds {2!r}, which invents a directory that never existed\n"
                    "    this row exists because: {3}".format(name, final, got, why)
                )
        # The DECOUPLING IS BOUNDED: no class outside the tabled overrides may differ. Computed over
        # the live map rather than the table, so a new class differing is caught even with no row.
        differing = {
            name
            for name, sub in RP._LEGACY_RECORD_CLASS_SUBPATHS.items()
            if sub != RP._RECORD_CLASS_SUBPATHS.get(name)
        }
        expected_differing = {n for n, _s, ov, _w in self.LEGACY if ov}
        if differing != expected_differing:
            wrong.append(
                "  BOUND: exactly {0} may differ from the final map, but {1} do; any other class "
                "carrying a `docs/`-prefixed legacy path is an invented directory".format(
                    sorted(expected_differing), sorted(differing)
                )
            )
        # Full coverage in both directions, so a migration read can never fall through to a KeyError.
        if set(RP._LEGACY_RECORD_CLASS_SUBPATHS) != set(RP._RECORD_CLASS_SUBPATHS):
            wrong.append(
                "  COVERAGE: the legacy map holds {0} but the final map holds {1}; they must cover "
                "the same classes".format(
                    sorted(RP._LEGACY_RECORD_CLASS_SUBPATHS),
                    sorted(RP._RECORD_CLASS_SUBPATHS),
                )
            )
        tabled = {n for n, _s, _o, _w in self.LEGACY}
        if tabled != set(RP._LEGACY_RECORD_CLASS_SUBPATHS):
            wrong.append(
                "  TABLE COVERAGE: the legacy map holds {0} but the table asserts {1}".format(
                    sorted(RP._LEGACY_RECORD_CLASS_SUBPATHS), sorted(tabled)
                )
            )
        self.assertEqual(
            wrong,
            [],
            "record_producers' LEGACY subpath map is wrong for {0} of {1} classes. The two maps are "
            "deliberately decoupled for exactly three doc-family classes and identical for every "
            "other, so several rows failing together usually means the decoupling was collapsed (the "
            "`docs/` overrides dropped) or over-applied (the spread rewriting classes that never "
            "lived under `docs/`) rather than {1} independent mistakes. FIX: read the override block "
            "beside `_LEGACY_RECORD_CLASS_SUBPATHS`; the end-to-end consequence is fenced by "
            "RoutingResolutionTests' legacy read-path test.\n".format(
                len(wrong), len(self.LEGACY)
            )
            + "\n".join(wrong),
        )


class ProjectSchemaAlignmentTests(unittest.TestCase):
    """`LogicalRoot` (4) and `RootClass` (6) stay aligned but NOT collapsed (E-02, F-4).

    ONE table replaces four tests over the same two enums (pin the members of each, pin the two
    lengths, compare each against the layout model). Tabulating is better here because the two
    vocabularies are closed sets whose relationship is the actual contract: they must each match the
    model AND must not become each other. The realistic failure is a single "simplification" that
    touches both at once (collapsing the six physical placement classes into the four logical roots,
    which spec Section 5.1 item 4 specifically prohibits), and that shows up as several rows moving
    together rather than as one independent breakage.

    The ORDER is pinned, not just the set, because these lists are asserted positionally in shipped
    code; and the model column is per-enum so a drift naming WHICH enum diverged is reported.
    """

    #: (enum name, enum, expected member values IN ORDER, model vocabulary, why this row exists)
    ENUMS = (
        (
            "LogicalRoot",
            LogicalRoot,
            ["system", "config", "state", "records"],
            _layout.LOGICAL_ROOTS,
            "the FOUR logical roots: what a path is FOR",
        ),
        (
            "RootClass",
            RootClass,
            [
                "system",
                "config_project",
                "config_local",
                "state_durable",
                "state_runtime",
                "records",
            ],
            _layout.ROOT_CLASSES,
            "the SIX physical placement classes: WHERE it goes and under whose git policy. "
            "`config` and `state` each split into a tracked and an untracked half whose policies "
            "are opposite, which is exactly why this enum is larger than LogicalRoot",
        ),
    )

    def test_both_root_vocabularies_match_the_model_and_stay_distinct(self) -> None:
        wrong = []
        for name, enum_cls, expected, model, why in self.ENUMS:
            got = [m.value for m in enum_cls]
            if got != expected:
                wrong.append(
                    "  {0} members expected {1} (in this ORDER), got {2}\n"
                    "    this row exists because: {3}".format(name, expected, got, why)
                )
            if set(got) != set(model):
                wrong.append(
                    "  {0} disagrees with the layout model: enum has {1}, model has {2}\n"
                    "    this row exists because: {3}".format(
                        name, sorted(set(got)), sorted(set(model)), why
                    )
                )
        # NOT COLLAPSED (spec 5.1 item 4). Kept in this table rather than its own test because it is
        # the relationship the two rows above exist to protect: each enum matching the model is
        # vacuous reassurance if the two vocabularies have become the same four names.
        logical = {m.value for m in LogicalRoot}
        classes = {m.value for m in RootClass}
        if logical == classes:
            wrong.append(
                "  COLLAPSED: LogicalRoot and RootClass now have the SAME vocabulary {0}. Spec "
                "5.1 item 4 prohibits this: they answer different questions, and collapsing them "
                "erases the tracked/untracked split".format(sorted(logical))
            )
        self.assertEqual(
            wrong,
            [],
            "the project_schema root vocabularies are wrong in {0} of {1} respects. Both are "
            "derived from layout.py and are deliberately DIFFERENT sizes (4 vs 6), so rows failing "
            "together usually means one enum was 'simplified' into the other rather than {1} "
            "independent breakages. FIX: read `project_schema._assert_layout_alignment`, whose "
            "rejection of exactly these drifts is fenced by the two tests below.\n".format(
                len(wrong), len(self.ENUMS)
            )
            + "\n".join(wrong),
        )

    def test_the_alignment_check_rejects_a_dropped_logical_root(self) -> None:
        """Kept separate: monkeypatches the enum and uses assertRaises, not a row of values."""
        # The guard must actually reject drift, so it is exercised rather than merely present. A
        # DROPPED member is the realistic drift: someone "simplifies" the enum and the model no
        # longer matches.
        import enum

        from agent_workflows import project_schema as PS

        narrowed = enum.Enum(
            "LogicalRoot",
            [("SYSTEM", "system"), ("CONFIG", "config"), ("STATE", "state")],
            type=str,
        )
        original = PS.LogicalRoot
        try:
            PS.LogicalRoot = narrowed
            with self.assertRaises(RuntimeError) as ctx:
                PS._assert_layout_alignment()
            self.assertIn("records", str(ctx.exception))
        finally:
            PS.LogicalRoot = original

    def test_the_alignment_check_rejects_collapsing_root_classes_to_four(self) -> None:
        """Kept separate: monkeypatches the enum and uses assertRaises, not a row of values."""
        # THE SPECIFIC PROHIBITION (spec Section 5.1 item 4): collapsing the six physical placement
        # classes into the four logical roots must not start up.
        import enum

        from agent_workflows import project_schema as PS

        collapsed = enum.Enum(
            "RootClass",
            [
                ("SYSTEM", "system"),
                ("CONFIG", "config"),
                ("STATE", "state"),
                ("RECORDS", "records"),
            ],
            type=str,
        )
        original = PS.RootClass
        try:
            PS.RootClass = collapsed
            with self.assertRaises(RuntimeError):
                PS._assert_layout_alignment()
        finally:
            PS.RootClass = original

    def test_the_alignment_check_passes_for_the_real_vocabularies(self) -> None:
        """The POSITIVE case for the two negative tests above: the guard must not reject reality.

        Kept separate from the vocabulary table because it asserts the guard RUNS CLEAN rather than
        any value, and it is the row that makes the two monkeypatching negatives non-vacuous: a
        guard that raised unconditionally would satisfy both of them.
        """
        from agent_workflows import project_schema as PS

        PS._assert_layout_alignment()


class RoutingResolutionTests(unittest.TestCase):
    """`resolve_record_path` routes every class correctly after the derivation (V-01).

    ONE table replaces seven tests that all did the same thing: call `_resolve(class, sub)` against
    one shared fixture repo and assert the result ENDS WITH a known path. The table is better than
    the seven because this is the OBSERVABLE half of everything the two map tests above assert
    structurally: routing is a single function over a closed class vocabulary, and a derivation
    defect (a lost carve-out, reintroduced `docs/` nesting, a state class escaping into the records
    root) changes SEVERAL destinations at once. Seven tests report that as seven red lines, each
    stopping at its own first failure; the table reports every class that moved, and the pattern
    across the rows is what tells you which structural change caused it.

    The `forbidden` column preserves the old negative assertion (`records/records` must never
    appear) rather than dropping it into a positive-only check, because the doubled-segment defect
    is the specific one the carve-out exists to prevent and an `endswith` assertion alone would pass
    on a path like `.aw/records/records/../records`.
    """

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-rodj06"
        )

        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )
        for rel in (
            (".aw", "records", "plans"),
            (".aw", "state", "durable"),
            (".aw", "state", "runtime"),
        ):
            os.makedirs(os.path.join(self.target_repo, *rel), exist_ok=True)

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _resolve(self, record_class: str, sub: str = "") -> str:
        return RP.resolve_record_path(
            record_class,
            sub,
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        ).as_posix()

    #: (record class, subpath argument, expected path suffix, forbidden substring or None, why)
    ROUTES = (
        (
            RP.RecordClass.RECORDS.value,
            "",
            ".aw/records",
            "records/records",
            "THE CARVE-OUT'S OBSERVABLE CONSEQUENCE, which is the point of the whole fence: the "
            "root alias must land ON the records root, not in a nested `records/records/`",
        ),
        (
            RP.RecordClass.RECORDS.value,
            "README.md",
            ".aw/records/README.md",
            "records/records",
            "the same carve-out WITH a subpath, where a doubled segment would otherwise appear "
            "between the root and the file",
        ),
        (
            "other",
            "",
            ".aw/records",
            "records/other",
            "the COMPLEMENT has no directory of its own, so it must resolve to the root rather than "
            "raise or fabricate `.aw/records/other/`",
        ),
        (
            "plans",
            "x.md",
            ".aw/records/plans/x.md",
            None,
            "pre-existing class, unchanged route",
        ),
        (
            "specs",
            "x.md",
            ".aw/records/specs/x.md",
            "docs/specs",
            "pre-existing doc-family class: the WRITE route is flat, and the legacy `docs/` prefix "
            "must not leak out of the legacy read map into it",
        ),
        (
            "research",
            "x.md",
            ".aw/records/research/x.md",
            "docs/research",
            "second doc-family class, same no-leak requirement",
        ),
        (
            "walkthroughs",
            "x.md",
            ".aw/records/walkthroughs/x.md",
            "docs/walkthroughs",
            "third doc-family class, same no-leak requirement",
        ),
        (
            "prompts",
            "x.md",
            ".aw/records/prompts/x.md",
            None,
            "pre-existing class, unchanged route",
        ),
        (
            "comms",
            "x.md",
            ".aw/records/comms/x.md",
            None,
            "pre-existing class, unchanged route",
        ),
        (
            "releases",
            "x.md",
            ".aw/records/releases/x.md",
            None,
            "pre-existing class, unchanged route",
        ),
        (
            "reviews",
            "x.md",
            ".aw/records/reviews/x.md",
            None,
            "pre-existing class, unchanged route",
        ),
        (
            "backlog",
            "x.md",
            ".aw/records/backlog/x.md",
            None,
            "the union ruling requires a net-new member to route to the tree that ALREADY exists on "
            "disk, not to invent a directory",
        ),
        (
            "roadmaps",
            "x.md",
            ".aw/records/roadmaps/x.md",
            None,
            "the other net-new member, same requirement",
        ),
        (
            RP.DurableStateClass.HISTORY.value,
            "h.json",
            ".aw/state/durable/history/h.json",
            "/records/",
            "a DURABLE STATE class must stay under the state root; the records vocabulary sharing "
            "one resolver is exactly how it could leak into `.aw/records/`",
        ),
        (
            RP.RuntimeStateClass.LOCKS.value,
            "l.json",
            ".aw/state/runtime/locks/l.json",
            "/records/",
            "a RUNTIME STATE class must stay under the untracked runtime root, whose git policy is "
            "the opposite of the records root's",
        ),
        (
            RP.DurableStateClass.INSTALL.value,
            "",
            ".aw/state/durable/install.json",
            None,
            "`install` is a FILE, not a directory, so it must not gain a trailing segment",
        ),
    )

    def test_every_class_routes_to_its_pinned_destination(self) -> None:
        wrong = []
        for record_class, sub, expected, forbidden, why in self.ROUTES:
            label = "{0!r}{1}".format(
                record_class, " + {0!r}".format(sub) if sub else " (no subpath)"
            )
            try:
                resolved = self._resolve(record_class, sub)
            except (
                Exception
            ) as exc:  # a route that RAISES is a routing failure like any other
                wrong.append(
                    "  {0} raised {1}: {2} (expected a path ending {3!r})\n"
                    "    this row exists because: {4}".format(
                        label, type(exc).__name__, exc, expected, why
                    )
                )
                continue
            if not resolved.endswith(expected):
                wrong.append(
                    "  {0}\n    expected a path ending {1!r}\n    got               {2!r}\n"
                    "    this row exists because: {3}".format(
                        label, expected, resolved, why
                    )
                )
            if forbidden is not None and forbidden in resolved:
                wrong.append(
                    "  {0} resolved to {1!r}, which must NEVER contain {2!r}\n"
                    "    this row exists because: {3}".format(
                        label, resolved, forbidden, why
                    )
                )
        self.assertEqual(
            wrong,
            [],
            "record_producers.resolve_record_path sent {0} of {1} classes to the wrong place. Every "
            "destination comes from one derived subpath map, so several rows failing together "
            "usually means one structural change (the records carve-out lost, the legacy `docs/` "
            "prefix leaking into the write route, or a state class escaping into the records root) "
            "rather than {1} independent misroutes. FIX: check `_record_class_subpath` and the two "
            "map tests above, which fence the same defects structurally; a row that RAISES instead "
            "of misrouting usually means the class left the enum entirely.\n".format(
                len(wrong), len(self.ROUTES)
            )
            + "\n".join(wrong),
        )

    def test_an_unknown_class_is_still_rejected(self) -> None:
        """Kept out of the routing table: `assertRaises`, not an expected path."""
        with self.assertRaises(RP.InvalidRecordClassError):
            self._resolve("nonexistent_class")

    def test_parent_traversal_in_a_subpath_is_still_rejected(self) -> None:
        """Kept out of the routing table: `assertRaises`, and a security boundary of its own."""
        with self.assertRaises(RP.UnsafeSymlinkError):
            self._resolve("plans", "../../../etc/passwd")

    def test_an_absolute_subpath_is_still_rejected(self) -> None:
        """Kept separate: `assertRaises`, and an absolute path is NOT caught by the traversal check,
        so this is a distinct assertion rather than another row of the same one."""
        with self.assertRaises(RP.UnsafeSymlinkError):
            self._resolve("plans", "/etc/passwd")

    def test_legacy_read_paths_resolve_for_a_doc_family_class(self) -> None:
        """Kept separate: needs materially different setup (a retention manifest plus a real legacy
        directory on disk) and asserts over a LIST of paths rather than one resolved path."""
        # With a retention manifest present, the legacy `.agents/docs/specs` tree must be returned
        # in ADDITION to the flat primary, which is the whole reason the legacy map stays decoupled.
        manifest = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"retained": True}), encoding="utf-8")
        legacy = Path(self.target_repo) / ".agents" / "docs" / "specs"
        legacy.mkdir(parents=True, exist_ok=True)

        paths = [
            p.as_posix()
            for p in RP.resolve_record_read_paths(
                "specs", target_repo=self.target_repo, aw_home=self.aw_home
            )
        ]
        self.assertTrue(any(p.endswith(".aw/records/specs") for p in paths), paths)
        self.assertTrue(
            any(p.endswith(".agents/docs/specs") for p in paths),
            "the decoupled legacy subpath must still be resolved: {0}".format(paths),
        )

    def test_record_routing_still_reports_the_repository_backend(self) -> None:
        """Kept separate: asserts four fields of a routing INFO object, not a resolved path."""
        info = RP.resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(info.records_backend, RecordsBackend.REPOSITORY.value)
        self.assertTrue(info.allow_git_stage)
        self.assertEqual(info.commit_destination, "repository")
        self.assertTrue(info.records_root.endswith(".aw/records"), info.records_root)

    def test_git_owner_is_unchanged_for_records_and_runtime(self) -> None:
        """Kept separate: a different function (`get_git_owner`) whose answer is an OWNER, and whose
        two cases include a None that no path-suffix row could express."""
        self.assertEqual(
            RP.get_git_owner(
                RP.RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            ),
            "target",
        )
        self.assertIsNone(
            RP.get_git_owner(
                RP.RuntimeStateClass.TRANSACTIONS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )
        )

    def test_logical_root_vocabulary_is_still_used_by_the_router(self) -> None:
        info = RP.resolve_record_routing(
            target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertIn(LogicalRoot.RECORDS.value, ("records",))
        self.assertTrue(info.records_root)


class WriteGuardTests(unittest.TestCase):
    """The central write guard is a security boundary and must be unchanged (V-01)."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-rodj06-guard"
        )
        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )
        for rel in (
            (".aw", "records", "plans"),
            (".aw", "state", "durable"),
            (".aw", "state", "runtime"),
        ):
            os.makedirs(os.path.join(self.target_repo, *rel), exist_ok=True)

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_a_legal_record_write_is_permitted(self) -> None:
        """The POSITIVE case the four refusals below depend on: a guard that rejected everything
        would satisfy every one of them. Kept separate because it returns a PATH rather than raising,
        so it cannot share a row shape with an assertRaises case."""
        target = Path(self.target_repo) / ".aw" / "records" / "plans" / "new.ipd.md"
        result = RP.guard_write(
            target,
            record_class=RP.RecordClass.PLANS.value,
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )
        self.assertEqual(result, target)

    def test_a_legacy_agents_write_is_still_rejected(self) -> None:
        """Kept separate: assertRaises, and it passes a record_class the next test does not."""
        with self.assertRaises(RP.LegacyWriteError):
            RP.guard_write(
                Path(self.target_repo) / ".agents" / "docs" / "specs" / "x.spec.md",
                record_class=RP.RecordClass.SPECS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    def test_a_workflow_artifacts_write_is_still_rejected(self) -> None:
        """Kept separate: assertRaises, and deliberately passes NO record_class, so the refusal is
        proven to come from the destination alone."""
        with self.assertRaises(RP.LegacyWriteError):
            RP.guard_write(
                Path(self.target_repo) / "workflow-artifacts" / "assess" / "x.md",
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    def test_a_producer_write_into_the_runtime_state_root_is_still_rejected(
        self,
    ) -> None:
        """Kept separate: assertRaises, and needs the distinct `is_producer=True` setup."""
        with self.assertRaises(RP.ForbiddenWriteError):
            RP.guard_write(
                Path(self.target_repo) / ".aw" / "state" / "runtime" / "locks" / "l",
                target_repo=self.target_repo,
                aw_home=self.aw_home,
                is_producer=True,
            )

    def test_a_pre_switch_migration_still_blocks_writes(self) -> None:
        """Kept separate: assertRaises, and needs materially different setup (an in-flight migration
        transaction file written to the runtime root first)."""
        tx = (
            Path(self.target_repo)
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        tx.parent.mkdir(parents=True, exist_ok=True)
        tx.write_text("{}", encoding="utf-8")
        with self.assertRaises(RP.MigrationInFlightError):
            RP.guard_write(
                Path(self.target_repo) / ".aw" / "records" / "plans" / "x.ipd.md",
                record_class=RP.RecordClass.PLANS.value,
                target_repo=self.target_repo,
                aw_home=self.aw_home,
            )

    #: (subclass name, base name, base, why this row exists)
    HIERARCHY = (
        (
            "LegacyWriteError",
            "GuardError",
            RP.GuardError,
            "a legacy-sink write is a guard refusal",
        ),
        (
            "ForbiddenWriteError",
            "GuardError",
            RP.GuardError,
            "a forbidden-root write is a guard refusal",
        ),
        (
            "MigrationInFlightError",
            "GuardError",
            RP.GuardError,
            "an in-flight migration refusal is a guard refusal, so a caller that pauses on "
            "GuardError pauses on this too",
        ),
        (
            "UnsafeSymlinkError",
            "GuardError",
            RP.GuardError,
            "the symlink/traversal refusal raised by the routing tests above must be catchable at "
            "the guard level as well",
        ),
        (
            "StaleContextError",
            "GuardError",
            RP.GuardError,
            "a stale-context refusal is a guard refusal",
        ),
        (
            "CrossGitStagingError",
            "GuardError",
            RP.GuardError,
            "a cross-git staging refusal is a guard refusal",
        ),
        (
            "GuardError",
            "RecordProducerError",
            RP.RecordProducerError,
            "the whole guard family must sit under the module's root error, which is the outermost "
            "level callers catch at",
        ),
        (
            "InvalidRecordClassError",
            "RecordProducerError",
            RP.RecordProducerError,
            "an unknown class is a producer error even though it is not a guard refusal",
        ),
        (
            "InvalidRecordClassError",
            "ValueError",
            ValueError,
            "DUAL inheritance, deliberately: pre-existing callers catch ValueError, so losing this "
            "base is a silent break no GuardError row would reveal",
        ),
        (
            "DuplicateAuthorityError",
            "RecordProducerError",
            RP.RecordProducerError,
            "duplicate-authority detection reports through the same root error",
        ),
    )

    def test_the_guard_exception_hierarchy_is_unchanged(self) -> None:
        """Callers catch at these levels, so the hierarchy is part of the contract.

        Tabulated for the same reason as the tables above: these ten edges are ONE inheritance tree,
        and the realistic failure is a refactor that reparents a whole family at once (say, moving
        the guard errors off `RecordProducerError`). The old form was ten bare `assertTrue`s in one
        method, which stopped at the FIRST broken edge and printed only `False is not true`; every row
        here names the edge, and all broken edges are reported together.
        """
        wrong = []
        for sub_name, base_name, base, why in self.HIERARCHY:
            sub = getattr(RP, sub_name, None)
            if sub is None:
                wrong.append(
                    "  record_producers.{0} does not exist (must subclass {1})\n"
                    "    this row exists because: {2}".format(sub_name, base_name, why)
                )
                continue
            if not issubclass(sub, base):
                wrong.append(
                    "  {0} must subclass {1} but its MRO is {2}\n"
                    "    this row exists because: {3}".format(
                        sub_name,
                        base_name,
                        [c.__name__ for c in sub.__mro__],
                        why,
                    )
                )
        self.assertEqual(
            wrong,
            [],
            "record_producers' exception hierarchy lost {0} of {1} edges. Callers catch at the "
            "GuardError and RecordProducerError levels, so a broken edge means an exception escapes "
            "a handler that used to catch it; several rows failing together usually means one "
            "family was reparented rather than {1} independent changes. FIX: compare the `class "
            "...Error(...)` bases at the top of record_producers.py against this table.\n".format(
                len(wrong), len(self.HIERARCHY)
            )
            + "\n".join(wrong),
        )


class ProducerInventoryTests(unittest.TestCase):
    """`PRODUCER_INVENTORY` is untouched by the vocabulary consolidation."""

    def test_inventory_is_non_empty_and_every_category_is_a_known_class(self) -> None:
        """Kept separate: already a loop over LIVE data, so there is no fixed row set to tabulate."""
        self.assertTrue(RP.PRODUCER_INVENTORY)
        known = {c.value for c in RP.RecordClass}
        for entry in RP.PRODUCER_INVENTORY:
            self.assertIn(
                entry.category,
                known,
                "producer {0!r} routes to unknown class {1!r}".format(
                    entry.name, entry.category
                ),
            )

    def test_the_legacy_allowlist_still_holds_only_non_writers(self) -> None:
        """Kept separate: asserts a different structure (the allowlist) from the inventory."""
        self.assertTrue(RP.LEGACY_ALLOWLIST)
        self.assertNotIn("agent_workflows/record_producers.py", RP.LEGACY_ALLOWLIST)

    def test_no_known_writer_module_reintroduced_a_legacy_write_sink(self) -> None:
        """Kept separate: scans the whole repository tree, materially different setup and cost."""
        repo_root = Path(__file__).resolve().parent.parent
        self.assertEqual(RP.discover_legacy_write_sinks(repo_root), set())


if __name__ == "__main__":
    unittest.main()

"""Tests for agent_workflows.check_engine (awcheck Order 01): the unified check engine core.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: write a small records
tree into a temp repo, call one check function, assert one rule id fired (or that none did). That is a
(fixture -> rule id) table, which is the natural shape for a RULE ENGINE.

THE RULE IDS ARE LOAD-BEARING AND ARE ASSERTED EXACTLY, never as "a finding appeared". Users read
them in `aw check` output, CI greps them, and `aw attention` routes on them, so a renumbering or a
rule splitting in two is a BREAKING CHANGE that must fail here. Rows therefore pin the exact rule
SET, and several rows additionally pin the DETAIL, because a finding that fires without naming the
two files involved cannot be acted on. The ids are written as LITERAL STRINGS rather than read back
from `RULE_REGISTRY`, since a constant and the reported id move together and a renumbering would be
invisible.

WHAT WAS A CLASS PER SUBJECT IS NOW A COLUMN WHERE THE SUBJECT IS A MODE: the `legacy=True` flag, the
`include_retired=True` flag, the `names_only=True` flag, the record TYPE, and the file's DIRECTORY all
appear as columns, because in every case the property worth stating is that the SAME tree gets a
DIFFERENT answer in a different mode, which no single-mode test can express.

ROWS ASSERT THE EXACT RULE SET RATHER THAN AN EMPTY DRIFT LIST where the fixture legitimately trips
an unrelated rule (a `draft` plan with no placeholders trips the advisory
`check.ipd-draft-ready-to-review`, and a status-less spec trips two `attention.*` rules). Asserting
emptiness there would couple every row to every unrelated rule in the engine.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the claim is about the REGISTRY rather than about any tree; the subject is a single helper
predicate rather than a check; or the fixture is one tree that must be checked through FOUR different
entry points at once, which is the claim itself.
"""

from __future__ import annotations

import collections
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce

NONCONFORMANT = "check.name-nonconformant"
ID6_COLLISION = "check.id6-collision"
SETID_COLLISION = "check.setid-collision"
IDENTITY_SLOT = "check.id6-identity-slot"
TYPE_UNSUPPORTED = "check.type-unsupported"
DRAFT_READY = "check.ipd-draft-ready-to-review"
MISSING_STATUS = "attention.missing-status"
HISTORY_MISSING = "attention.history-missing"

PLANS = ".aw/records/plans/pending"
SPECS = ".aw/records/specs"
WALK = ".aw/records/walkthroughs"


def _plan_text(id6, setid="demo", desc=None, status="approved"):
    setline = f"{setid} ({desc})" if desc else setid
    return (
        f"# IPD\n\n- Id: {id6}\n- Status: {status}\n- Set: {setline}\n\n## Goal\n\nx\n"
    )


def _spec_text(id6, setid="demo", desc=None, status="draft"):
    setline = f"{setid} ({desc})" if desc else setid
    return (
        f"# Spec\n\n- Id: {id6}\n- Status: {status}\n- Set: {setline}\n\n## Body\n\nx\n"
    )


def _walk_text(id6=None):
    idline = f"- Id: {id6}\n" if id6 else ""
    return f"# Walkthrough\n\n- Date: 20260101\n{idline}\n## Summary\n\nx\n"


def _tree(files):
    """Materialize `[(relative path, text)]` into a fresh temp repo and return its root."""
    root = Path(tempfile.mkdtemp())
    for rel, text in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def _rules(drift):
    return sorted(d.rule for d in drift)


def _counts(drift):
    return (
        repr(dict(collections.Counter(d.rule for d in drift))) if drift else "nothing"
    )


class NameGrammarTests(unittest.TestCase):
    """Which filenames `check_names` accepts, per record type and per `legacy` mode.

    ONE table replaces three tests (`test_check_names_flags_bad_name`,
    `test_legacy_flag_allows_legacy_name`, `test_current_name_ok`). All three wrote one file and
    asked `check_names` whether it conformed, differing only in the filename shape and the `legacy`
    flag, so both are columns.

    THE `legacy` FLAG IS A COLUMN AND THAT IS THE WHOLE REASON THIS IS ONE TABLE: the flag's purpose
    is that the SAME filename is refused without it and accepted with it, so both answers for one
    input must be asserted together. The old test did this for exactly one filename shape; here every
    row is checked in BOTH modes, which is what turns "the flag works on this file" into "the flag
    widens the grammar by exactly the legacy forms". Two rows are load-bearing in the other
    direction: junk is refused in BOTH modes, so `legacy=True` is a WIDENING and not an off switch.

    Why the table beats the three: one naming authority decides every row, the grammar is a closed set
    of accepted shapes (`YYYYMMDD-<setid>-NN-<id6>-<slug>` current, `YYYYMMDD-HHMM-NN-<slug>` legacy,
    hyphenated-date legacy), and the realistic regression is a grammar change that reclassifies
    SEVERAL shapes at once. Three tests report that as three unrelated failures; the table reports one
    naming every shape that moved.

    The conformant rows are in the same table because a checker that flagged every file would satisfy
    both flagging rows on its own, and one that flagged nothing would satisfy every clean row.
    """

    #: (case, record type, filename, file text, rules expected WITHOUT `legacy`, rules expected WITH
    #: `legacy=True`, why this row exists)
    NAMES = (
        (
            "the current id6-slot plan grammar",
            "plans",
            "20260101-demo-01-aaa111-ok.ipd.md",
            _plan_text("aaa111"),
            (),
            (),
            "THE CANONICAL SHAPE every new plan is born with (`aw ipd scaffold` derives it). It must "
            "be clean in BOTH modes; every flagging row below is vacuous while this one is broken, "
            "because a checker that rejects everything satisfies all of them",
        ),
        (
            "a legacy YYYYMMDD-HHMM-NN-<slug> plan name",
            "plans",
            "20260101-1357-01-assess-bugs.ipd.md",
            "# IPD\n\n- Id: wvlk84\n- Status: draft\n\n## Goal\n\nx\n",
            (),
            (),
            "PRE-CUTOVER NAMES ARE GRANDFATHERED, so this must be clean WITHOUT the flag too. That "
            "is the surprising half and the reason the row exists: `legacy=True` is not what makes "
            "an HHMM name acceptable, the grammar itself admits it, and a change that started "
            "flagging these would light up a large part of the real tree at once",
        ),
        (
            "a legacy YYYYMMDD-HHMM-NN-<slug> spec name",
            "specs",
            "20260101-1200-01-x.spec.md",
            "# Spec: x\n\n- Status: draft\n\n## Workflow history\n\n- 2026-01-01 note (human): x\n",
            (),
            (),
            "THE TYPE IS A COLUMN: specs carry the id6 in the filename GOING FORWARD while "
            "pre-cutover spec names stay valid, so the grandfathering must hold for specs and not "
            "only for plans. One row per type is what would localise a per-type grammar regression",
        ),
        (
            "a hyphenated-date legacy plan name",
            "plans",
            "2026-01-01-old-hyphenated.md",
            "# IPD\n\n- Id: aaa111\n- Status: draft\n\n## Goal\n\nx\n",
            (NONCONFORMANT,),
            (),
            "THE ROW THE `legacy` FLAG EXISTS FOR, and the only one that differs between the two "
            "modes: `parse_name` RECOGNIZES this form while `is_conformant` refuses it, so it is "
            "flagged by default and accepted under `--legacy`. That asymmetry is the flag's entire "
            "definition and cannot be stated by a single-mode row",
        ),
        (
            "a plan filename matching no grammar at all",
            "plans",
            "not-a-grammar.md",
            "# IPD: bad\n\n- Id: bbb222\n- Status: draft\n\n## Goal\n\nx\n",
            (NONCONFORMANT,),
            (NONCONFORMANT,),
            "JUNK IS REFUSED IN BOTH MODES, which is what makes `legacy=True` a WIDENING rather than "
            "an off switch. Without this row the flag could disable name checking entirely and the "
            "row above would still pass",
        ),
        (
            "a spec filename matching no grammar at all",
            "specs",
            "junk.spec.md",
            "# Spec: x\n\n- Status: draft\n\n## Workflow history\n\n- 2026-01-01 note (human): x\n",
            (NONCONFORMANT,),
            (NONCONFORMANT,),
            "the per-type twin of the row above, so `--legacy` is shown not to be an off switch for "
            "specs either. Keeping both types here is what states that the flag's meaning is "
            "uniform across the tree",
        ),
    )

    def test_each_filename_shape_is_judged_the_same_way_in_both_modes(self):
        wrong = []
        for case, rtype, name, text, strict, lenient, why in self.NAMES:
            directory = {"plans": PLANS, "specs": SPECS}[rtype]
            root = _tree([(f"{directory}/{name}", text)])
            problems = []
            for mode, expected, kwargs in (
                ("default", strict, {}),
                ("legacy=True", lenient, {"legacy": True}),
            ):
                drift = [
                    d
                    for d in ce.check_names(root, rtype, **kwargs)
                    if name in d.location
                ]
                if _rules(drift) != sorted(expected):
                    problems.append(
                        f"[{mode}] expected {sorted(expected)!r}, got {_counts(drift)}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (type={rtype}, name={name!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`check_names` judged {len(wrong)} of {len(self.NAMES)} filename shapes wrongly. ONE "
            "naming authority decides every row and each row is asked in BOTH modes, so read the "
            "grouping: all three GRANDFATHERED rows flagging at once means the legacy grammar was "
            "dropped and a large part of the real tree now reports nonconformant; the two JUNK rows "
            "going clean under `legacy=True` means the flag became an off switch instead of a "
            "widening; a per-type row failing alone means one type's grammar changed. FIX: "
            "`check.name-nonconformant` is a published rule id that CI greps, so if a grammar change "
            f"is intended, update these rows deliberately rather than relaxing the assertion.\n"
            + "\n".join(wrong),
        )


class CollisionTests(unittest.TestCase):
    """The cross-tree uniqueness rules: id6 identity, setid descriptives, and the filename slot.

    ONE table replaces ELEVEN tests spread over two classes (`CollisionTests` and
    `IdentitySlotTests`). Every one wrote one to three small records and asserted which
    `check.*-collision` / `check.id6-identity-slot` findings came back. All three rules are produced
    by a SINGLE pass of `check_collisions` over every supported type, which is why they belong in one
    table: the pass is where the interference between them lives.

    Why the table beats the eleven: two of the rules are keyed on data structures a refactor can
    quietly re-key (`seen_sets` is `(type, setid)` and NOT setid alone; `records` holds every file's
    declared id and slot id6 so the slot rule can tell who OWNS an id6), and a re-keying changes
    SEVERAL rows at once. Eleven tests report that as eleven unrelated red lines; the grouping here is
    the diagnosis. It also makes the rules browsable as a set, which matters because the most
    dangerous mistake in this area is ADDING a rule that reports correct behavior.

    THE DETAIL IS ASSERTED, NOT ONLY THE RULE ID, on every row where two files are involved. These
    findings are unactionable without naming BOTH sides: "setid `topic` conflicts" tells a user
    nothing, while naming both descriptives tells them which to change. Two rows additionally assert
    what must NOT appear in the detail, which is how the cross-type carve-out is pinned.

    THE CLEAN ROWS ARE IN THE SAME TABLE and three of them are load-bearing policy rather than
    vacuity: a setid shared ACROSS types is CORRECT (D153 / spec `2lcqno` N1), a setid reused with a
    CONSISTENT descriptive is correct, and legacy HHMM names have no id6 slot to validate. Each is a
    check somebody might "helpfully" add back; the rows say why not.
    """

    #: (case, the files as (relative path, text), rules that must be reported EXACTLY (sorted, WITH
    #: DUPLICATES where a rule fires once per file), detail/location substrings required, substrings
    #: that must NOT appear anywhere in the findings, why this row exists)
    #:
    #: THE EXPECTED SET IS THE FULL SWEEP'S, so it includes rules the fixture trips for reasons
    #: unrelated to collisions: a synthetic spec has no `## Workflow history`, so every row carrying
    #: a spec also carries `attention.history-missing` (once per spec), and a `draft` plan with no
    #: remaining placeholders carries the `check.ipd-draft-ready-to-review` advisory. Those are real
    #: findings about these fixtures and listing them is deliberate: trimming the assertion to "the
    #: collision rules only" would let a content rule silently stop firing tree-wide.
    COLLISIONS = (
        (
            "the same id6 declared by a plan and a spec",
            (
                (f"{PLANS}/20260101-demo-01-dup111-a.ipd.md", _plan_text("dup111")),
                (f"{SPECS}/20260101-demo-01-dup111-b.spec.md", _spec_text("dup111")),
            ),
            (ID6_COLLISION, HISTORY_MISSING),
            ("dup111", ".ipd.md"),
            (),
            "THE id6 IS THE IDENTITY, so two files claiming one is the fundamental violation: every "
            "`aw` verb resolves an artifact BY id6, so a duplicate means a command silently operates "
            "on whichever file it found first. The detail must name the OTHER file, or a user knows "
            "there is a clash without knowing with what",
        ),
        (
            "two plans sharing a setid with DIFFERENT descriptives",
            (
                (
                    f"{PLANS}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111", setid="demo", desc="Alpha"),
                ),
                (
                    f"{PLANS}/20260101-demo-02-bbb222-b.ipd.md",
                    _plan_text("bbb222", setid="demo", desc="Beta"),
                ),
            ),
            (SETID_COLLISION,),
            ("demo", "Alpha", "Beta", "descriptive"),
            (),
            "ONE SET, TWO NAMES is a genuine inconsistency in that Set's own name, and the finding "
            "must cite BOTH descriptives because that is the only information that says which to "
            "change",
        ),
        (
            "two SPECS conflicting under a setid a PLAN also uses",
            (
                (
                    f"{PLANS}/20260101-demo-01-aaa111-p.ipd.md",
                    _plan_text("aaa111", setid="topic", desc="PlanDesc"),
                ),
                (
                    f"{SPECS}/20260101-topic-01-bbb222-s1.spec.md",
                    _spec_text("bbb222", setid="topic", desc="Alpha"),
                ),
                (
                    f"{SPECS}/20260101-topic-02-ccc333-s2.spec.md",
                    _spec_text("ccc333", setid="topic", desc="Beta"),
                ),
            ),
            (SETID_COLLISION, HISTORY_MISSING, HISTORY_MISSING),
            (".spec.md", "Alpha", "Beta"),
            ("PlanDesc", ".ipd.md"),
            "THE SHARED-SLOT CASE (spec `2lcqno` N5), and the row that pins WHY `seen_sets` is keyed "
            "per `(type, setid)` rather than by setid alone. `SUPPORTED` iterates `plans` FIRST, so "
            "with a setid-only key the plan occupied the slot the spec-vs-spec comparison needed and "
            "the genuine Alpha/Beta conflict was NEVER reported. Measured: the setid-keyed version "
            "emitted two cross-type findings and missed this one, while a same-type GUARD alone "
            "emitted nothing at all, turning a noisy miss into a silent one. The must-NOT column is "
            "what proves the finding is between the two SPECS. WHICH spec is first-seen is "
            "filesystem-iteration order and is deliberately not asserted",
        ),
        (
            "one setid used by a plan and a spec, no descriptives",
            (
                (
                    f"{PLANS}/20260101-demo-01-aaa111-p.ipd.md",
                    _plan_text("aaa111", setid="topic"),
                ),
                (
                    f"{SPECS}/20260101-topic-01-bbb222-s.spec.md",
                    _spec_text("bbb222", setid="topic"),
                ),
            ),
            (HISTORY_MISSING,),
            (),
            ("setid",),
            "A SETID IS A SHARED CROSS-TYPE TOPIC LABEL (D153 / spec `2lcqno` N1), so one token under "
            "two record types is CORRECT and must report NOTHING about the setid. This row exists so "
            "the cross-type branch removed by E-01 cannot be re-added as a 'missing' check: it "
            "reported 29 findings on this repository's own default scope, EVERY ONE of them for "
            "endorsed behavior. No `info`-severity variant either (spec `2lcqno` OQ-01 rejected it, "
            "because narrating the normal state teaches a reader to ignore the output)",
        ),
        (
            "one setid reused with a CONSISTENT descriptive",
            (
                (
                    f"{PLANS}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111", setid="topic", desc="Alpha"),
                ),
                (
                    f"{PLANS}/20260101-demo-02-bbb222-b.ipd.md",
                    _plan_text("bbb222", setid="topic", desc="Alpha"),
                ),
            ),
            (),
            (),
            ("setid",),
            "THE NORMAL STATE OF EVERY MULTI-PLAN SET: members share the setid AND the descriptive. "
            "Paired with the Alpha/Beta row above, these two state the rule precisely (the "
            "DESCRIPTIVE must agree, not the setid be unique), which neither can state alone",
        ),
        (
            "two different id6 under two different setids",
            (
                (
                    f"{PLANS}/20260101-demo-01-aaa111-a.ipd.md",
                    _plan_text("aaa111", desc="Demo"),
                ),
                (
                    f"{SPECS}/20260101-demo-01-bbb222-b.spec.md",
                    _spec_text("bbb222", setid="other"),
                ),
            ),
            (HISTORY_MISSING,),
            (),
            ("collision",),
            "THE FULLY CLEAN TREE, and the anti-vacuity row for all three rules at once: a collision "
            "pass that reported on every pair of files would satisfy every flagging row above. Note "
            "the expected set is NOT empty (the spec legitimately lacks a workflow history), which "
            "is why rows assert an exact rule SET rather than an empty list",
        ),
        (
            "a file whose declared Id differs from its filename slot",
            (
                (
                    f"{PLANS}/20260101-demo-01-slotaa-a.ipd.md",
                    _plan_text("fmbbb1", status="draft"),
                ),
            ),
            (IDENTITY_SLOT, DRAFT_READY),
            ("slotaa", "fmbbb1"),
            (),
            "IDENTITY-SLOT RULE (a), DECISIONS D140: the `<id6>` in the filename IS the file's "
            "identity, so it must EQUAL the declared `- Id:`. When they disagree, a name-based lookup "
            "and a content-based lookup resolve to different artifacts. The detail must cite BOTH "
            "ids, since either one could be the typo",
        ),
        (
            "a walkthrough with no declared Id whose slot is a PLAN's identity",
            (
                (
                    f"{PLANS}/20260101-demo-01-abc123-plan.ipd.md",
                    _plan_text("abc123", status="draft"),
                ),
                (
                    f"{WALK}/20260101-demo-01-abc123-execution.walkthrough.md",
                    _walk_text(),
                ),
            ),
            (IDENTITY_SLOT, DRAFT_READY),
            ("execution.walkthrough.md", "abc123", "plan.ipd.md"),
            (),
            "IDENTITY-SLOT RULE (b), the `p7dqwz` case: a file declaring NO Id must not SQUAT on "
            "another file's id6 in its filename slot. This is the half that needs global knowledge "
            "(who OWNS `abc123`), which is why `check_collisions` gathers every file's declared and "
            "slot ids before evaluating. The finding must name the offender AND the owner",
        ),
        (
            "a file whose declared Id EQUALS its slot, beside another owning its own",
            (
                (
                    f"{PLANS}/20260101-demo-01-abc123-ok.ipd.md",
                    _plan_text("abc123", status="draft"),
                ),
                (
                    f"{WALK}/20260101-demo-01-def456-own.walkthrough.md",
                    _walk_text("def456"),
                ),
            ),
            (DRAFT_READY,),
            (),
            (IDENTITY_SLOT,),
            "THE CONFORMANT SHAPE of both slot rules at once, and the anti-vacuity row for them: a "
            "slot rule that flagged every file with an id6 in its name would satisfy both flagging "
            "rows above. The walkthrough declares its OWN id6, which is rule (b) satisfied rather "
            "than merely dodged",
        ),
        (
            "legacy HHMM names whose slug's first word looks like an id6",
            (
                (
                    f"{PLANS}/20260101-1357-01-assess-bugs.ipd.md",
                    "# IPD\n\n- Id: wvlk84\n- Status: draft\n\n## Goal\n\nx\n",
                ),
                (
                    f"{WALK}/20260101-1033-01-assess-bugs-and-tests.walkthrough.md",
                    _walk_text(),
                ),
            ),
            (DRAFT_READY,),
            (),
            (IDENTITY_SLOT,),
            "THE MASS-FLAGGING TRAP: in `YYYYMMDD-HHMM-NN-<slug>` the 4-digit HHMM occupies the "
            "setid segment and the slug's first word (`assess`) is six lowercase characters, so a "
            "naive slot parser reads `assess` as an id6 and flags every legacy file in the tree. "
            "Only a filename whose slot parses as a REAL id6 via the naming authority is checked, and "
            "this row is what holds that line",
        ),
    )

    def test_one_pass_reports_exactly_the_collisions_present(self):
        wrong = []
        clean_row_broken = False
        for case, files, expected, needles, forbidden, why in self.COLLISIONS:
            root = _tree(files)
            drift = ce.check_collisions(root)
            # The collision pass is also reached via the full sweep; that seam is asserted in
            # `EntryPointTests`, so here the subject is the pass itself plus whatever content rules
            # the same tree legitimately trips.
            all_drift = ce.check_types(root, ["all"])
            problems = []
            collision_rules = {ID6_COLLISION, SETID_COLLISION, IDENTITY_SLOT}
            got = _rules([d for d in drift if d.rule in collision_rules])
            want = sorted(r for r in expected if r in collision_rules)
            if got != want:
                if not want:
                    clean_row_broken = True
                problems.append(
                    f"`check_collisions` expected {want!r}, got {_counts(drift)}"
                )
            if _rules(all_drift) != sorted(expected):
                problems.append(
                    f"the full sweep over the same tree expected {sorted(expected)!r}, got "
                    f"{_counts(all_drift)}"
                )
            haystack = " | ".join(f"{d.location} {d.detail}" for d in drift)
            missing = [n for n in needles if n not in haystack]
            if missing:
                problems.append(
                    f"the findings never mention {missing!r}, so a user cannot tell WHICH files are "
                    f"involved; they said {haystack!r}"
                )
            leaked = [n for n in forbidden if n in haystack]
            if leaked:
                problems.append(
                    f"the findings must NOT mention {leaked!r}; they said {haystack!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if clean_row_broken:
            note = (
                " NOTE: a CLEAN row is among the failures, so the pass is now reporting endorsed "
                "behavior as a violation. If it is the cross-type setid row, the branch removed by "
                "E-01 is back: it emitted 29 findings on this repository's own default scope, every "
                "one of them correct behavior. If it is a legacy-name row, every pre-cutover file in "
                "the tree is being mass-flagged."
            )
        self.assertEqual(
            wrong,
            [],
            f"`check_collisions` was wrong for {len(wrong)} of {len(self.COLLISIONS)} trees.{note} "
            "All three rules come from ONE pass whose two data structures are the usual culprits "
            "(`seen_sets` keyed per `(type, setid)`, and the global record of who OWNS each id6), so "
            "read the grouping: the SHARED-SLOT row failing with the cross-type row means `seen_sets` "
            "was re-keyed by setid alone; both IDENTITY-SLOT rows failing means the global ownership "
            "gather was narrowed to one type; a DETAIL-only failure means the rule still fires but "
            "has stopped naming the other file, which makes it unactionable. FIX: these rule ids are "
            "consumed by users and CI, so a rule splitting or renumbering must be an intentional "
            f"update here.\n" + "\n".join(wrong),
        )

    def test_the_setid_and_id6_rules_trace_to_their_own_invariants(self):
        """Kept separate: the claim is about the RULE REGISTRY, with no repository and no fixture.

        E-03: the setid rule's catalog home is I-16 (setid SEMANTICS), not I-09 (filename-grammar
        conformance), while the two id6 rules deliberately STAY on I-09 because the identity-slot rule
        genuinely concerns the filename slot. Spec `pqsx96` Section 4 records the correction.
        """
        self.assertEqual(ce.rule_spec(SETID_COLLISION).invariant, "I-16")
        self.assertEqual(ce.rule_spec(ID6_COLLISION).invariant, "I-09")
        self.assertEqual(ce.rule_spec(IDENTITY_SLOT).invariant, "I-09")


class EntryPointTests(unittest.TestCase):
    """Which sub-checks each entry point composes, over ONE shared tree.

    ONE table replaces six tests (`test_check_content_surfaces_malformed_spec`,
    `test_no_content_validator_returns_empty`, `test_check_type_names_only`,
    `test_check_types_all_runs`, `test_unsupported_single_type`, `test_check_refs_seam_empty`). Each
    called a different entry point on the same kind of tree and asserted something about the result,
    so the ENTRY POINT is the column and the tree is shared.

    Why the table beats the six: `SUPPORTED` declares which sub-checks each type has (`plans` has
    names+content+refs, `prompts` has names only, and so on), and `check_type` composes exactly
    those. The realistic regression is a sub-check being added to or dropped from a type, which
    changes what SEVERAL entry points return. The table states the composition as data, so a
    composition change reports as one failure naming every entry point affected.

    TWO OLD TESTS WERE WEAKER THAN THEIR ROWS AND THAT IS THE MAIN GAIN. `test_check_types_all_runs`
    asserted only `assertIsInstance(drift, list)`, which no plausible bug violates; its row now pins
    the exact rule set the sweep produces over this tree, so a sub-check silently dropping out of the
    fan-out fails. `test_check_content_surfaces_malformed_spec` asserted only `len(drift) >= 1`, which
    passes whichever rule fires; its row names `attention.missing-status` and
    `attention.history-missing` exactly, because those ids are what `aw attention` routes on.

    THE EMPTY-RESULT ROWS ARE IN THE SAME TABLE, and they are the SEAM rows rather than vacuity
    filler: a type with no content validator must return `[]` rather than raising, and `check_refs` is
    a declared-but-unimplemented seam whose emptiness is a STATED cost. If either starts producing
    findings, that is a new feature to record here, not a test to loosen.
    """

    #: The shared tree: a conformant plan, a plan whose FILENAME is junk, and a spec missing its
    #: `- Status:` and its workflow history. One tree exercising three different defects is what lets
    #: every row below be a different question about the SAME input.
    TREE = (
        (f"{PLANS}/20260101-demo-01-aaa111-ok.ipd.md", _plan_text("aaa111")),
        (
            f"{PLANS}/not-a-grammar.md",
            "# IPD: bad\n\n- Id: bbb222\n- Status: draft\n\n## Goal\n\nx\n",
        ),
        (
            f"{SPECS}/20260101-1200-01-x.spec.md",
            "# Spec: x\n\n- Author: t\n\n## Body\n\nno status here\n",
        ),
    )

    #: (case, the entry point to drive, the exact expected rule set, why this row exists)
    ENTRY_POINTS = (
        (
            "names over plans",
            ("check_names", "plans"),
            (NONCONFORMANT,),
            "THE NAME CHECK IN ISOLATION: only the junk filename is reported, and the conformant "
            "plan beside it is not. Without a clean file in the same tree, a checker that flagged "
            "every plan would pass",
        ),
        (
            "content over specs",
            ("check_content", "specs"),
            (MISSING_STATUS, HISTORY_MISSING),
            "CONTENT VALIDATION IS A DIFFERENT AXIS FROM NAMING: this spec's NAME is fine and its "
            "BODY is not. Both ids are named exactly, because the old test asserted only `len >= 1` "
            "and would have passed on any single unrelated rule; `aw attention` routes on these ids, "
            "so which one fires is the whole content of the claim",
        ),
        (
            "content over prompts, a type with NO content validator",
            ("check_content", "prompts"),
            (),
            "A DECLARED-BUT-UNVALIDATED TYPE MUST RETURN `[]`, NOT RAISE. `SUPPORTED['prompts']` is "
            "`('names',)` only, so this row pins that the composition is data-driven rather than a "
            "hardcoded chain that assumes every type has a content validator",
        ),
        (
            "refs over plans, a declared seam",
            ("check_refs", "plans"),
            (),
            "A STATED COST asserted so it is a decision rather than a surprise: `plans` declares a "
            "`refs` sub-check and the implementation is an EMPTY SEAM. If reference checking is ever "
            "implemented, this row SHOULD fail and be updated; it is not a licence to loosen",
        ),
        (
            "check_type over plans with names_only",
            ("check_type_names_only", "plans"),
            (NONCONFORMANT,),
            "THE `names_only` FLAG IS A COLUMN, and its content is the CONTRAST with the row below: "
            "the same type over the same tree must report ONLY the naming rule, which is what makes "
            "`aw check --names-only` a narrowing of the same pass rather than a different one",
        ),
        (
            "check_type over plans, fully composed",
            ("check_type", "plans"),
            (NONCONFORMANT, DRAFT_READY),
            "THE CONTRAST ROW: without `names_only` the content sub-check also runs, and this tree's "
            "junk-named plan is additionally a `draft` with no remaining placeholders, so the "
            "advisory fires too. Adjacency to the row above is what states that the flag SUBTRACTS "
            "content checking rather than switching pass",
        ),
        (
            "check_type over an unsupported type",
            ("check_type", "bogus"),
            (TYPE_UNSUPPORTED,),
            "AN UNKNOWN TYPE IS A FINDING, NOT AN EMPTY RESULT, when asked for DIRECTLY: `aw check "
            "bogus` must tell the user their type does not exist rather than silently reporting a "
            "clean tree, which reads as 'checked and fine'",
        ),
        (
            "check_types over the unsupported type",
            ("check_types", ("bogus",)),
            (),
            "THE SAME UNKNOWN TYPE IS SKIPPED SILENTLY in the FAN-OUT, which is the opposite answer "
            "to the row above and is why both belong here. The fan-out passes `_from_all=True`, so "
            "an unsupported member of a list cannot poison a multi-type sweep. Two entry points, two "
            "deliberate answers; no single-entry-point test can state the difference",
        ),
        (
            "the full sweep over every type",
            ("check_types", ("all",)),
            (NONCONFORMANT, DRAFT_READY, MISSING_STATUS, HISTORY_MISSING),
            "THE WHOLE COMPOSITION AT ONCE, and the row that replaces an assertion of "
            "`isinstance(drift, list)` (which no plausible bug violates). Every defect in the tree "
            "must surface here exactly once: the junk name, the draft advisory, and both spec content "
            "rules. A sub-check silently dropping out of the fan-out fails this row and nothing else",
        ),
        (
            "an explicit two-type sweep",
            ("check_types", ("plans", "specs")),
            (NONCONFORMANT, DRAFT_READY, MISSING_STATUS, HISTORY_MISSING),
            "NAMING THE TYPES MUST EQUAL `['all']` HERE, since this tree holds only plans and specs. "
            "Comparing the two rows is what shows `all` is a SENTINEL expanding to the supported "
            "types rather than a separate code path with its own rule set (its one documented extra "
            "is the cross-tree collision pass, which this tree does not trip)",
        ),
    )

    def test_each_entry_point_composes_exactly_its_declared_sub_checks(self):
        wrong = []
        for case, call, expected, why in self.ENTRY_POINTS:
            root = _tree(self.TREE)
            fn, arg = call
            if fn == "check_names":
                drift = ce.check_names(root, arg)
            elif fn == "check_content":
                drift = ce.check_content(root, arg)
            elif fn == "check_refs":
                drift = ce.check_refs(root, arg)
            elif fn == "check_type":
                drift = ce.check_type(root, arg)
            elif fn == "check_type_names_only":
                drift = ce.check_type(root, arg, names_only=True)
            else:
                drift = ce.check_types(root, list(arg))
            if _rules(drift) != sorted(expected):
                wrong.append(
                    f"  {case} ({fn}({arg!r})):\n"
                    f"    - expected {sorted(expected)!r}, got {_counts(drift)}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ENTRY_POINTS)} entry points composed the wrong sub-checks "
            "over ONE shared tree. `SUPPORTED` declares which sub-checks each type has and "
            "`check_type` composes exactly those, so read the grouping: every row losing "
            "`check.name-nonconformant` means the name sub-check left the composition rather than "
            "the grammar changing; the two SWEEP rows disagreeing means `['all']` stopped being a "
            "sentinel over `SUPPORTED`; the two UNSUPPORTED-TYPE rows agreeing means the "
            "direct-versus-fan-out distinction was lost, so either `aw check bogus` reports a clean "
            "tree for a type that does not exist, or one bad member poisons a multi-type sweep. FIX: "
            "an entry point reporting FEWER rules than its row is a check that stopped running while "
            f"still appearing to pass.\n" + "\n".join(wrong),
        )


class RetiredAndIgnoredScopeTests(unittest.TestCase):
    """WHICH FILES the engine looks at: retired artifacts and ignored directories.

    ONE table replaces three tests (`test_is_retired_helper`, `test_check_ignores_retired_by_default`,
    `test_check_includes_retired_when_requested`). All three used one tree of active-plus-retired
    artifacts; two called a check with and without `include_retired`, and the third asked the
    `is_retired` predicate about six paths one assertion at a time.

    THE `include_retired` FLAG IS A COLUMN, which is what makes this one table: the SAME malformed
    file must be invisible by default and reported when asked for, and only adjacent columns state
    that. Split apart, a change that dropped retirement filtering entirely would leave the
    include-retired test green and read as one unrelated new failure.

    THE PREDICATE ROWS AND THE CHECK ROWS SHARE THE TABLE because they must agree: `is_retired` is
    what `_iter_type_files` filters on, so a path the predicate misjudges is a file the checks
    silently include or exclude. The old helper test asserted six paths with six bare assertions and
    no message, so a failure named a boolean and not a path; each is now a row saying WHY that path is
    (or is not) retired, distinguishing the two independent mechanisms: the DIRECTORY segment
    (`executed/`, `done/`) and the frontmatter STATUS (`implemented`, `done`).

    THE ACTIVE ROWS ARE IN THE SAME TABLE and they are load-bearing: a predicate returning True
    unconditionally would make every check blind to the whole tree while satisfying every retired row.
    """

    #: Retired-or-not rows: (case, relative path, text, expected `is_retired`, why this row exists)
    ARTIFACTS = (
        (
            "an approved plan in pending/",
            f"{PLANS}/20260101-demo-01-aaa111-active.ipd.md",
            "# IPD: active\n\n- Id: aaa111\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            False,
            "THE ACTIVE BASELINE: live work must be CHECKED. A predicate returning True here makes "
            "every check blind to the tree while satisfying every retired row below",
        ),
        (
            "a badly-named plan in executed/",
            ".aw/records/plans/executed/bad-name-executed.md",
            "# IPD: executed\n\n- Id: eee111\n- Status: executed\n- Set: demo\n\n## Goal\n\nx\n",
            True,
            "RETIREMENT BY DIRECTORY SEGMENT. This is the load-bearing case for the whole feature: "
            "AGENTS.md FORBIDS editing a plan already in `executed/`, so flagging its filename would "
            "demand a fix that is not permitted. Retired history is read-only, so it is not linted "
            "by default",
        ),
        (
            "an approved spec",
            f"{SPECS}/20260101-1200-01-active.spec.md",
            "# Spec: active\n- Status: approved\n\n## Workflow history\n\n- 2026-01-01 note (human): initial approval\n",
            False,
            "the active case for a type with NO disposition directories at all: specs live in one "
            "flat directory, so their retirement can only come from the STATUS. This row is the "
            "counterpart that proves an ordinary spec is not caught by that",
        ),
        (
            "a spec whose Status is `implemented`",
            f"{SPECS}/20260101-1200-02-done.spec.md",
            "# Spec: done\n- Status: implemented\n\n## Body\n\nx\n",
            True,
            "RETIREMENT BY FRONTMATTER STATUS, the SECOND and independent mechanism. It is what "
            "covers a flat tree, and `implemented` is a spec-only spelling that appears in no "
            "directory name, so a path-only predicate would miss it entirely",
        ),
        (
            "a backlog item in open/",
            ".aw/records/backlog/open/20260101-bkl111-01-bkl111-open.backlog.md",
            "- Id: bkl111\n- Status: open\n- Set: bkl111\n- Priority: high\n- Work-Kind: feature\n- Summary: Open\n\n## Detail\n\nx\n",
            False,
            "the active case for the third tree shape, whose disposition directories are STATUS "
            "names. `open/` must not be mistaken for a retirement segment",
        ),
        (
            "a backlog item in done/",
            ".aw/records/backlog/done/20260101-bkl222-01-bkl222-done.backlog.md",
            "- Id: bkl222\n- Status: done\n- Set: bkl222\n- Priority: high\n- Work-Kind: feature\n- Summary: Done\n\n## Detail\n\nx\n",
            True,
            "THE OVERLAP ROW: `done` is BOTH a directory segment and a status, so this path is "
            "retired by either mechanism. Kept because it is the shape most likely to be "
            "accidentally excluded when one of the two mechanisms is refactored, and it is also why "
            "the retired-status set and the retired-path set are not identical",
        ),
    )

    #: Scope rows: (case, the check to drive, whether `include_retired` is passed, the exact expected
    #: rule set, why this row exists)
    SCOPES = (
        (
            "names over plans, retired excluded (the default)",
            "names",
            False,
            (),
            "THE DEFAULT SCOPE, and the whole point of the feature: the `executed/` plan's filename "
            "is junk and must NOT be reported, because the only available fix is a commit AGENTS.md "
            "forbids. A finding nobody may act on is worse than no finding",
        ),
        (
            "names over plans with include_retired=True",
            "names",
            True,
            (NONCONFORMANT,),
            "THE OPT-IN, which is the other half of the same claim: the file IS nonconformant and an "
            "auditor asking for retired artifacts must be told. Adjacency to the row above states "
            "that retirement filters VISIBILITY and not the grammar, which neither row can state "
            "alone",
        ),
        (
            "the full sweep, retired excluded",
            "all",
            False,
            (),
            "THE DEFAULT SCOPE ACROSS EVERY TYPE AT ONCE: this tree holds a malformed plan, a "
            "malformed spec, and a done backlog item, all retired, plus three active artifacts that "
            "are clean. Zero findings is therefore a strong claim and it is the state a maintainer "
            "expects `aw check` to report on a healthy tree with history in it",
        ),
    )

    #: The shared tree for both tables, built from `ARTIFACTS` so the predicate rows and the scope
    #: rows cannot drift apart.
    def _tree(self):
        return _tree([(rel, text) for _c, rel, text, _e, _w in self.ARTIFACTS])

    def test_is_retired_and_the_default_scope_agree_about_every_artifact(self):
        wrong = []
        active_row_broken = False
        root = self._tree()
        for case, rel, _text, expected, why in self.ARTIFACTS:
            actual = ce.is_retired(root / rel)
            if actual is not expected:
                if expected is False:
                    active_row_broken = True
                wrong.append(
                    f"  is_retired: {case} ({rel}):\n"
                    f"    - expected {expected}, got {actual}\n"
                    f"    this row exists because: {why}"
                )
        for case, which, include, expected, why in self.SCOPES:
            if which == "names":
                drift = ce.check_names(root, "plans", include_retired=include)
            else:
                drift = ce.check_types(root, ["all"], include_retired=include)
            if _rules(drift) != sorted(expected):
                wrong.append(
                    f"  scope: {case}:\n"
                    f"    - expected {sorted(expected)!r}, got {_counts(drift)}\n"
                    f"    this row exists because: {why}"
                )
        total = len(self.ARTIFACTS) + len(self.SCOPES)
        note = ""
        if active_row_broken:
            note = (
                " NOTE: an ACTIVE row is among the failures, so `is_retired` is now claiming live "
                "work is retired. That makes every check BLIND to the artifacts it exists to "
                "validate while every retired row still passes, which is the quietest possible "
                "failure of this engine."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {total} retirement rows were wrong.{note} `is_retired` is what "
            "`_iter_type_files` filters on, so the predicate rows and the scope rows are ONE "
            "mechanism seen twice and must agree. Read the grouping: every DIRECTORY row failing "
            "while the STATUS rows pass means the retired-path segment set changed (and vice versa "
            "for the frontmatter set); a SCOPE row failing while every predicate row passes means "
            "the filter stopped being applied at the iteration seam even though the predicate is "
            "still correct. FIX: an under-reporting default scope hides real findings, while an "
            "over-reporting one demands edits to `executed/` plans that AGENTS.md forbids, so check "
            f"WHICH direction moved before changing anything.\n" + "\n".join(wrong),
        )

    def test_ignored_directories_are_invisible_to_every_entry_point(self):
        """Kept separate: ONE tree checked through FOUR entry points at once IS the claim.

        The property is that a `tmp/` path is invisible to names, content, collisions, AND the full
        sweep, so a row per entry point would let three pass while one leaks. It is also a
        cross-cutting NEGATIVE over locations rather than a per-fixture rule expectation: nothing may
        mention `tmp`, whatever rule it would have been.

        Two ignored locations are covered deliberately: a top-level `tmp/`, and a `tmp/` nested INSIDE
        a records tree, which is the one a directory-name filter catches but a prefix filter does not.
        """
        root = _tree(
            [
                # Invalid files in an ignored top-level directory.
                (
                    "tmp/bad-nonconformant.ipd.md",
                    "# IPD\n\n- Id: aaa111\n- Status: draft\n\n## Goal\n\nx\n",
                ),
                ("tmp/bad-spec.spec.md", "# Spec: bad\n\nno frontmatter\n"),
                # An invalid file in an ignored subdirectory UNDER a records tree.
                (
                    ".aw/records/plans/tmp/bad-sub-tmp.ipd.md",
                    "# IPD\n\n- Id: ccc333\n- Status: invalid-status\n",
                ),
                # A valid conformant plan that must still be seen.
                (
                    f"{PLANS}/20260101-demo-02-bbb222-valid.ipd.md",
                    "# IPD: valid\n\n- Id: bbb222\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
                ),
            ]
        )
        for label, drift in (
            ("check_names", ce.check_names(root, "plans")),
            ("check_content", ce.check_content(root, "plans")),
            ("check_collisions", ce.check_collisions(root)),
            ("check_types(['all'])", ce.check_types(root, ["all"])),
        ):
            leaked = [d for d in drift if "tmp" in d.location]
            self.assertEqual(
                leaked,
                [],
                f"{label} looked inside an ignored directory and reported "
                f"{[(d.rule, d.location) for d in leaked]!r}; ignored paths are scratch space, so a "
                "finding there is noise a user cannot act on and did not ask for",
            )


if __name__ == "__main__":
    unittest.main()

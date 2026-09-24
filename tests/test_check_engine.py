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
import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce

NONCONFORMANT = "check.name-nonconformant"
ID6_COLLISION = "check.id6-collision"
SETID_COLLISION = "check.setid-collision"
IDENTITY_SLOT = "check.id6-identity-slot"
SETID_LEN_WARN = "check.setid-length-warn"
SETID_LEN_ERROR = "check.setid-length-error"
IDENTITY_ABSENT = "check.identity-absent-from-name"
TYPE_UNSUPPORTED = "check.type-unsupported"
COLLISIONS_NOT_CHECKED = "check.collisions-not-checked"
DRAFT_READY = "check.ipd-draft-ready-to-review"
MISSING_STATUS = "attention.missing-status"
HISTORY_MISSING = "attention.history-missing"

PLANS = ".aw/records/plans/pending"
SPECS = ".aw/records/specs"
WALK = ".aw/records/walkthroughs"


def _plan_text(id6, setid="demo", desc=None, status="approved"):
    """A plan body that is CONFORMANT to the full IPD contract, not a four-line stub.

    IT USED TO BE A STUB, AND THAT MATTERED ONCE `aw check plans` STARTED RUNNING THE LINTER
    (lintreach `k9awrq`). The old body was `# IPD` plus `- Id:`/`- Status:`/`- Set:` plus a `## Goal`,
    which `aw ipd lint --phase author` reports TWENTY diagnostics against: five missing required
    metadata fields, a `Set` with no `Order`, an `approved` status with no `Approval` attestation, no
    `Scope-Paths`, and eleven absent required H2 sections. Nothing surfaced that, because the sweep did
    not call the linter - which is the exact gap `check.ipd-lint-diagnostic` closes.

    SO THE FIXTURE IS FIXED RATHER THAN THE ASSERTIONS LOOSENED, and that direction is deliberate. This
    file's own header says rows "assert the EXACT rule SET" and its collision table's comment says the
    expected sets list rules "the fixture trips for reasons unrelated to collisions" ON PURPOSE, because
    "trimming the assertion to 'the collision rules only' would let a content rule silently stop firing
    tree-wide". Adding `check.ipd-lint-diagnostic` to a dozen expected sets, or filtering it out of this
    file's helpers, would both weaken exactly that property. A conformant fixture keeps every row
    asserting precisely what it always claimed: that the rule under test fires, and that nothing else
    does.

    Every parameter the callers vary (`id6`, `setid`, the optional Set `desc`, and `status`) still
    varies, and the body stays minimal in the sense that matters: it trips NO rule by itself.
    `- Approval:` is emitted only for `approved`, because `IPD-M104` requires it there and the other
    statuses must not carry an attestation they have not earned.
    """
    setline = f"{setid} ({desc})" if desc else setid
    approval = (
        "- Approval: 2026-01-01, recorded via aw ipd set\n"
        if status == "approved"
        else ""
    )
    return (
        "# IPD\n\n"
        "- Date: 2026-01-01\n"
        "- Kind: child\n"
        "- Concern: a check_engine fixture\n"
        "- Scope: a check_engine fixture\n"
        "- Scope-Paths: x.py\n"
        "- Item-Dependencies: none\n"
        f"- Status: {status}\n"
        f"- Set: {setline}\n"
        "- Order: 1\n"
        "- Highest E allocated: 01\n"
        # planprio (`lkexaw`): REQUIRED at the ready-to-execute gate, and this fixture defaults to
        # `approved`, which IS that gate. Real vocabulary values rather than the `grandfathered`
        # sentinel, per the maintainer's 2026-09-24 decision: the sentinel is advisory-SATISFIED, so it
        # would add a permanent nudge to every row, and it asserts the plan predates the rule, which a
        # fixture built milliseconds ago does not. Fixing the FIXTURE rather than the assertions is this
        # helper's own stated discipline (see its docstring).
        "- Priority: medium\n"
        "- Work-Kind: chore\n"
        "- Author: fixture\n"
        f"- Id: {id6}\n"
        f"{approval}"
        "\n## Workflow history\n"
        f"- 2026-01-01 {status} (t): created.\n"
        "\n## Goal\n\nx\n"
        "\n## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 do it.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n"
        "\n## Project conventions discovered (Step 0)\n\n- none\n"
        "\n## Findings\n\n"
        "| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n"
        "| F-1 | LOW | x | y | z |\n"
        "\n## Proposed changes (ordered, validatable)\n\n1. do it\n"
        "\n## Deferred / out of scope (with reason)\n\n"
        "- nothing deferred.\n  - Carrier-Declined: a fixture has no obligations.\n"
        "\n## Scope check\n\n- Over-scope: none\n- Under-scope: none\n"
        "\n## Required tests / validation\n\nthe suite\n"
        "\n## Spec / documentation sync\n\nnone\n"
        "\n## Open questions\n\nnone\n"
        "\n## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: paste it\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n"
        "\n## Approval and execution gate\n\n"
        "- Size assessment: standard\n- Cohesion rationale: not required\n"
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
                    f"{PLANS}/20260101-topic-01-aaa111-p.ipd.md",
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
                    f"{PLANS}/20260101-topic-01-aaa111-p.ipd.md",
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
                    f"{PLANS}/20260101-topic-01-aaa111-a.ipd.md",
                    _plan_text("aaa111", setid="topic", desc="Alpha"),
                ),
                (
                    f"{PLANS}/20260101-topic-02-bbb222-b.ipd.md",
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
                    f"{SPECS}/20260101-other-01-bbb222-b.spec.md",
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
                    # A CONFORMANT BODY under a legacy FILENAME, which is precisely this row's subject:
                    # the defect (or non-defect) under test is the NAME, so the body must not contribute
                    # findings of its own. `check.ipd-lint-diagnostic` (lintreach `k9awrq`) runs the real
                    # linter over the plans sweep, and the inline stub this row used to carry tripped 20
                    # `IPD-*` diagnostics, which would have made the row fail for a reason unrelated to
                    # the slot-parsing trap it exists to guard. `_plan_text` supplies the `- Id:` this
                    # row needs (a declared id6 ABSENT from its own filename, which is what
                    # `check.identity-absent-from-name` reports here on purpose). `draft` is retained
                    # because this row's expected set includes `check.ipd-draft-ready-to-review`, which
                    # only fires on a placeholder-free `draft`.
                    _plan_text("wvlk84", status="draft"),
                ),
                (
                    f"{WALK}/20260101-1033-01-assess-bugs-and-tests.walkthrough.md",
                    _walk_text(),
                ),
            ),
            # IDENTITY_ABSENT FIRES TWICE ON THE ONE PLAN, AND BOTH ARE CORRECT. That rule reports each
            # declared identity absent from a pre-id6-grammar filename, and a conformant body declares
            # `- Set:` as well as `- Id:`, so this legacy `YYYYMMDD-HHMM-NN-<slug>` name is missing both.
            # It counted once only because the old stub body omitted `- Set:` entirely, i.e. the single
            # count was an artifact of an incomplete fixture rather than a property of the rule.
            # Duplicates in an expected set are the established convention in this table ("WITH
            # DUPLICATES where a rule fires once per file"), and the MUST-NOT column below still holds
            # the line this row exists for: `check.id6-identity-slot` must NOT appear.
            (DRAFT_READY, IDENTITY_ABSENT, IDENTITY_ABSENT),
            (),
            (IDENTITY_SLOT,),
            "THE MASS-FLAGGING TRAP: in `YYYYMMDD-HHMM-NN-<slug>` the 4-digit HHMM occupies the "
            "setid segment and the slug's first word (`assess`) is six lowercase characters, so a "
            "naive slot parser reads `assess` as an id6 and flags every legacy file in the tree. "
            "Only a filename whose slot parses as a REAL id6 via the naming authority is checked, and "
            "this row is what holds that line. THE MUST-NOT COLUMN IS THE LOAD-BEARING HALF: findtier "
            "`3i6rso` added `check.identity-absent-from-name`, which reports this record ON PURPOSE "
            "(its declared `Id: wvlk84` is absent from its own filename, so `aw find` cannot locate "
            "it by name), and the two rules must stay DISTINGUISHABLE - `check.id6-identity-slot` is "
            "an `error` about a foreign id6 in a real slot, while the advisory is a `warning` about a "
            "grandfathered name. This row passing with BOTH ids would mean the trap re-opened",
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

    def test_the_setid_length_rules_are_registered_under_their_own_invariant(self):
        """setidlen x75obw E-03/V-03. The two length rules are I-17, NOT I-16 and NOT I-09.

        I-16 is setid SEMANTICS (a shared topic label, not an identity) and a 30-character setid
        violates nothing that sentence says; I-09 is filename-grammar conformance, and the setid group
        in both naming regexes is deliberately UNBOUNDED so length can be a POLICY with two tiers and a
        cutover. Spec `pqsx96` Section 4 records the choice and why widening I-16 was refused.
        """
        warn = ce.rule_spec(SETID_LEN_WARN)
        err = ce.rule_spec(SETID_LEN_ERROR)
        self.assertEqual(warn.invariant, "I-17")
        self.assertEqual(err.invariant, "I-17")
        self.assertEqual(warn.severity, "warning")
        self.assertEqual(err.severity, "error")
        self.assertEqual(warn.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(err.determinism, ce.DET_DETERMINISTIC)
        # The length rules must NOT have been homed on the semantics invariant.
        self.assertNotEqual(warn.invariant, ce.rule_spec(SETID_COLLISION).invariant)


class SetidLengthTests(unittest.TestCase):
    """setidlen x75obw E-04 (catalog I-17): `check_setid_length` over a small records tree.

    THE BOUNDARY ROWS ARE THE POINT. The longest setid in the real repository is EXACTLY 24
    characters (`research-prompt-pipeline`), so the error threshold has ZERO MARGIN and the table pins
    24-conforms / 25-errors rather than testing a comfortable 26. An off-by-one (`>=` for `>`) would
    hard-fail a live record, and only these two rows catch it.

    THE CLEAN ROWS ARE LOAD-BEARING POLICY, not vacuity: a PRE-cutover artifact with a long setid must
    report NOTHING (that is what keeps the 36 grandfathered setids from turning CI red), and an
    unstamped repository must report nothing at all (the documented fail-open tier of the resolver).
    """

    def _tree(
        self,
        d,
        *,
        cutover: "str | None" = "2026-09-23",
        files=(),
        setids_policy=None,
    ):
        root = Path(d)
        cfg = root / ".aw" / "config"
        cfg.mkdir(parents=True)
        project: dict = {"schema_version": 2}
        if cutover is not None:
            project["cutovers"] = {"setid_length": cutover}
        if setids_policy is not None:
            project["setids"] = setids_policy
        (cfg / "project.json").write_text(json.dumps(project), encoding="utf-8")
        pend = root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        for name, text in files:
            (pend / name).write_text(text, encoding="utf-8")
        return root

    def _plan(self, setid, date):
        return (
            f"{date.replace('-', '')}-{setid}-01-abc123-x.ipd.md",
            f"# IPD: x\n\n- Date: {date}\n- Id: abc123\n- Set: {setid} (topic)\n- Order: 1\n",
        )

    def _rules(self, drift):
        return sorted(d.rule for d in drift)

    def test_the_boundary_is_pinned_at_exactly_24_conforms_and_25_errors(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 24, "2026-09-23")])
            self.assertEqual(
                self._rules(ce.check_setid_length(root)),
                [SETID_LEN_WARN],
                "a 24-character setid must WARN, never error: the longest real setid is exactly 24, "
                "so an error here hard-fails a live record",
            )
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 25, "2026-09-23")])
            self.assertEqual(
                self._rules(ce.check_setid_length(root)), [SETID_LEN_ERROR]
            )

    def test_a_post_cutover_16_char_setid_warns(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 16, "2026-09-23")])
            drift = ce.check_setid_length(root)
            self.assertEqual(self._rules(drift), [SETID_LEN_WARN])
            self.assertIn("16 characters", drift[0].detail)

    def test_a_post_cutover_26_char_setid_errors(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 26, "2026-09-23")])
            self.assertEqual(
                self._rules(ce.check_setid_length(root)), [SETID_LEN_ERROR]
            )

    def test_a_conformant_14_char_setid_reports_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 14, "2026-09-23")])
            self.assertEqual(ce.check_setid_length(root), [])

    def test_a_pre_cutover_20_char_setid_reports_nothing(self):
        """The grandfathering row. This is what keeps the existing corpus green."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 20, "2026-08-01")])
            self.assertEqual(ce.check_setid_length(root), [])

    def test_an_unstamped_repository_reports_nothing_at_all(self):
        """The documented fail-open tier: absent boundary -> everything grandfathered."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(
                d, cutover=None, files=[self._plan("a" * 26, "2026-09-23")]
            )
            self.assertEqual(ce.check_setid_length(root), [])

    def test_strict_flags_a_pre_cutover_record(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 20, "2026-08-01")])
            self.assertEqual(
                self._rules(ce.check_setid_length(root, strict=True)), [SETID_LEN_WARN]
            )

    def test_strict_via_project_policy_matches_the_flag(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(
                d,
                files=[self._plan("a" * 20, "2026-08-01")],
                setids_policy={"strict": True},
            )
            self.assertEqual(self._rules(ce.check_setid_length(root)), [SETID_LEN_WARN])

    def test_one_artifact_yields_ONE_finding_not_one_per_place_the_setid_appears(self):
        """The declared `- Set:` and the filename setid are one defect about one file."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 25, "2026-09-23")])
            drift = ce.check_setid_length(root)
            self.assertEqual(len(drift), 1)

    def test_a_legacy_hhmm_name_is_not_read_as_a_long_setid(self):
        """`YYYYMMDD-HHMM-NN-<slug>` has no setid slot; reading `2147` as one invents findings."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[])
            pend = root / ".aw" / "records" / "plans" / "pending"
            (pend / "20260923-2147-01-a-legacy-plan.ipd.md").write_text(
                "# IPD: x\n\n- Date: 2026-09-23\n- Id: abc124\n", encoding="utf-8"
            )
            self.assertEqual(ce.check_setid_length(root), [])

    def test_the_full_sweep_surfaces_the_rule_exactly_once_per_artifact(self):
        """It rides the once-per-full-sweep collisions seam, so a multi-type tree cannot double it."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 25, "2026-09-23")])
            drift = ce.check_types(root, ["all"])
            self.assertEqual(
                [d_.rule for d_ in drift].count(SETID_LEN_ERROR),
                1,
                "the sweep must report the length rule once, not once per type enumerated",
            )

    def test_a_per_type_run_does_not_run_the_length_scan(self):
        """Same contract as its `check.setid-collision` neighbour: it is a cross-tree scan."""
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 25, "2026-09-23")])
            drift = ce.check_types(root, ["plans"])
            self.assertNotIn(SETID_LEN_ERROR, [d_.rule for d_ in drift])

    def test_a_repository_may_raise_max_length(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(
                d,
                files=[self._plan("a" * 26, "2026-09-23")],
                setids_policy={"max_length": 30},
            )
            self.assertEqual(self._rules(ce.check_setid_length(root)), [SETID_LEN_WARN])

    def test_the_warn_tier_does_not_fail_the_gate_but_the_error_tier_does(self):
        from agent_workflows import artifact_core as core

        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 16, "2026-09-23")])
            warn_drift = ce.check_setid_length(root)
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d, files=[self._plan("a" * 25, "2026-09-23")])
            err_drift = ce.check_setid_length(root)
        # A `warning` is NOT `info`, so it does set the exit code; an `error` certainly does. This row
        # exists so a later severity change is a deliberate, visible decision.
        self.assertEqual(core.drift_exit_code(warn_drift), 1)
        self.assertEqual(core.drift_exit_code(err_drift), 1)


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
            # The defect in this file is its NAME, so its BODY is conformant (`_plan_text`), for the
            # same reason recorded on the legacy-name row in `CollisionTests`: since
            # `check.ipd-lint-diagnostic` (lintreach `k9awrq`) runs the real linter over the plans
            # sweep, a stub body would add a second, unrelated finding to every row below and each
            # row's expected set would then be asserting the fixture's sloppiness rather than the
            # composition it exists to pin. `draft` is retained because several rows expect
            # `check.ipd-draft-ready-to-review` from this file.
            _plan_text("bbb222", status="draft"),
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
            (
                NONCONFORMANT,
                DRAFT_READY,
                MISSING_STATUS,
                HISTORY_MISSING,
                COLLISIONS_NOT_CHECKED,
            ),
            "NAMING THE TYPES MUST EQUAL `['all']` HERE, since this tree holds only plans and specs - "
            "EXCEPT for the one rule that distinguishes them, which is the whole point of comparing "
            "this row with the sweep row above. `all` is a SENTINEL expanding to the supported types, "
            "and its documented extra is the cross-tree COLLISION pass. A named-type run does NOT run "
            "that pass, so (IPD sk7ggr E-06) it must SAY so rather than render an unqualified clean: "
            "before that notice existed, `aw check research` reported `errors 0 warnings 0` and exited "
            "0 over a tree that held a real id6 collision. The notice is `info`, so it adds a line to "
            "the report WITHOUT failing the gate; the sweep row above must never carry it, because "
            "the sweep really does check",
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
            # CONFORMANT, because the SCOPES rows below assert that the default scope over this tree
            # reports ZERO findings ("the state a maintainer expects `aw check` to report on a healthy
            # tree"). A stub body would make that claim false through
            # `check.ipd-lint-diagnostic` (lintreach `k9awrq`), which is the one active plan the default
            # scope actually lints.
            _plan_text("aaa111", setid="demo"),
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
                # A valid conformant plan that must still be seen. Built with `_plan_text` rather than
                # inline, because "conformant" now has to be TRUE: `check.ipd-lint-diagnostic`
                # (lintreach `k9awrq`) runs the real linter over the plans sweep, and the inline stub
                # this row used to carry tripped 20 `IPD-*` diagnostics, which made the row fail while
                # claiming the finding came from the ignored `tmp/` tree.
                (
                    f"{PLANS}/20260101-demo-02-bbb222-valid.ipd.md",
                    _plan_text("bbb222", setid="demo"),
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


class DynamicCutoverCheckEngineTests(unittest.TestCase):
    """Plan ogs6a2: tests for dynamic cutovers in check_engine."""

    def test_deprecated_aliases_remain_accessible(self):
        self.assertEqual(ce.SPEC_ID6_CUTOVER_DATE, "20260828")
        self.assertEqual(ce.CARRIER_CUTOVER_DATE, "20260919")

    def test_check_names_honors_dynamic_spec_id6_cutover(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg_dir = root / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"cutovers": {"spec_id6": "2026-09-10"}}),
                encoding="utf-8",
            )
            specs_dir = root / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            # 20260828 would be flagged under static cutover, but under dynamic 2026-09-10 it is grandfathered
            (specs_dir / "20260828-1200-01-legacy.spec.md").write_text(
                "# Spec\n\n- Status: draft\n", encoding="utf-8"
            )
            drift = ce.check_names(root, "specs")
            self.assertEqual(drift, [])

            # A spec at or after the dynamic cutover date is flagged
            (specs_dir / "20260910-1200-01-post.spec.md").write_text(
                "# Spec\n\n- Status: draft\n", encoding="utf-8"
            )
            drift2 = ce.check_names(root, "specs")
            self.assertEqual(len(drift2), 1)
            self.assertEqual(drift2[0].rule, "check.name-nonconformant")

    def test_carrier_severity_honors_dynamic_carrier_cutover(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg_dir = root / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            plan_text = "# IPD\n\n- Date: 2026-09-15\n"

            # When dynamic cutover is 2026-09-18, plan is grandfathered -> info
            (cfg_dir / "project.json").write_text(
                json.dumps({"cutovers": {"carrier_obligations": "2026-09-18"}}),
                encoding="utf-8",
            )
            self.assertEqual(
                ce.carrier_severity_for_plan(plan_text, repo_root=root), "info"
            )

            # When dynamic cutover is 2026-09-10, plan is post-cutover -> error
            (cfg_dir / "project.json").write_text(
                json.dumps({"cutovers": {"carrier_obligations": "2026-09-10"}}),
                encoding="utf-8",
            )
            self.assertEqual(
                ce.carrier_severity_for_plan(plan_text, repo_root=root), "error"
            )


if __name__ == "__main__":
    unittest.main()

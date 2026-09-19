"""Tests for nobugship rgaasb: `check.live-bug-ungated` plus the `from-backlog-gate-mismatch` narrowing.

TWO SHIPPED BEHAVIORS ARE PINNED HERE AND THEY ARE DELIBERATELY IN ONE FILE, because the second
exists only to make the first landable:

1. `check.live-bug-ungated` (NEW): a LIVE (`open`/`blocked`/`graduated`) `Work-Kind: bug` backlog item
   carrying no `- Blocks-Release:` is a finding. The enforcement half of the maintainer's standing
   rule "we don't ship known bugs" (written in AGENTS.md by sibling `zqs0px`, defaulted at creation by
   sibling `di08i9`).

2. `check.from-backlog-gate-mismatch` NARROWED to a LIVE carrier (parent `qmgn12` OQ-03, maintainer
   ruling 2026-09-12). Backfilling every live bug's gate would otherwise newly flag every carrier
   plan, including plans in `executed/` that AGENTS.md forbids editing in place. The ruling restates
   the rule as the one-way obligation it already implements and skips a terminal carrier.

THE ZERO-FINDING DIRECTION IS ASSERTED EXPLICITLY (a row of `MISMATCHES` below) and that is the
durable half of the ruling. A gated carrier under an UNGATED item is currently unreachable BY
CONSTRUCTION (the `item_gate` map is populated only for a gated item), so nothing today would notice
if a refactor made the rule symmetric. Without that row the reframing is undefended.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a one- or
two-file temp repo, call one predicate, assert one rule id. The tables group by SUBJECT (the gate
grid, the narrowing, the seams, the registration, the reuse), and every MODE that used to justify a
separate test or a separate class is now a COLUMN: the item's STATUS, its WORK-KIND, the `Work-Kind:`
versus legacy `Kind:` SPELLING, whether the item itself carries a gate, whether a CARRIER exists and
of which type/disposition/gate, and which SEAM is driven. That is what lets a row state the thing no
single-mode test can: that the same document gets a different answer in a different mode.

THE RULE IDS ARE WRITTEN AS LITERAL STRINGS AND THE EXPECTATION IS THE EXACT RULE LIST, not "a
finding appeared". These ids are a published interface: `aw check` prints them, CI greps them, and
the recovery text names them, so a renumbering is a breaking change that must fail here.

Every test builds its OWN temp repo; none reads the live checkout.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the subject is a module FILE and the claim is a COUNT rather than a per-function
containment; the claim is over shared VOCABULARY SETS with no repository at all; the subject is a
DIFFERENT predicate being proven UNUSABLE rather than the rule under test; or the test is a
before/after co-update PAIR whose whole content is that the answer CHANGES between two tree states.
"""

from __future__ import annotations

import collections
import inspect
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

from agent_workflows import check_engine

ITEM = """- Id: {id6}
- Status: {status}
- Set: tst
- Priority: medium
- {kind_field}: {work_kind}
- Summary: A test item.
{gate}
## Workflow history
- 2026-09-18 created (test): A test item.
"""

PLAN = """# IPD: A test plan

- Date: 2026-09-18
- Kind: child
- Concern: Testing.
- Scope: Testing.
- Scope-Paths: x
- Item-Dependencies: none
- From-Backlog: {backlog_id6}
{gate}- Status: {status}
- Set: tst
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-18 created (test): Testing.
"""

SPEC = """# Spec: A test spec

- Date: 2026-09-18
- Status: approved
- Id: {id6}
- From-Backlog: {backlog_id6}
{gate}- Scope: Testing.

## Workflow history
- 2026-09-18 created (test): Testing.
"""


def _item(
    root: Path,
    id6: str,
    *,
    status: str = "open",
    work_kind: str = "bug",
    gate: Optional[str] = None,
    kind_field: str = "Work-Kind",
) -> Path:
    """A backlog item in the status directory matching its `- Status:` (as the real tree does).

    `kind_field` is a COLUMN rather than a second fixture: `parse_item` reads both the canonical
    `- Work-Kind:` and the legacy `- Kind:` spelling, and the rule must catch either.
    """
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-item.backlog.md"
    p.write_text(
        ITEM.format(
            id6=id6,
            status=status,
            work_kind=work_kind,
            kind_field=kind_field,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _plan(
    root: Path,
    id6: str,
    backlog_id6: str,
    *,
    gate: Optional[str] = None,
    disposition: str = "pending",
    status: str = "to-review",
) -> Path:
    d = root / ".aw" / "records" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-tst-01-{id6}-a-test-plan.ipd.md"
    p.write_text(
        PLAN.format(
            id6=id6,
            backlog_id6=backlog_id6,
            status=status,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _spec(
    root: Path, id6: str, backlog_id6: str, *, gate: Optional[str] = None
) -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260918-{id6}-01-{id6}-a-test-spec.spec.md"
    p.write_text(
        SPEC.format(
            id6=id6,
            backlog_id6=backlog_id6,
            gate=(f"- Blocks-Release: {gate}\n" if gate else ""),
        ),
        encoding="utf-8",
    )
    return p


def _rules(drift) -> List[str]:
    return [d.rule for d in drift]


def _counts(drift) -> str:
    return repr(dict(collections.Counter(_rules(drift)))) if drift else "no findings"


RULE = "check.live-bug-ungated"
MISMATCH = "check.from-backlog-gate-mismatch"

# A carrier column value: (record type, its own gate or None, its directory disposition). `None` in
# the column means the item has NO From-Backlog carrier at all.
PLAN_GATED = ("plan", "next", "pending")
PLAN_UNGATED = ("plan", None, "pending")
SPEC_GATED = ("spec", "next", "specs")


class LiveBugGateGridTests(unittest.TestCase):
    """The (status x work-kind x item-gate x carrier) grid `check.live-bug-ungated` decides.

    ONE table replaces ELEVEN tests spread over two classes (`LiveBugGateBehaviorTests` and
    `LiveBugGateEdgeTests`). Every one had the identical shape: write one backlog item (sometimes
    with one carrier), call `check_live_bug_gate`, assert `[RULE]` or `[]`. The class boundary
    tracked which IPD item had asked for the case, which is provenance, not a property of the
    subject.

    Why the table beats the eleven: the rule is a conjunction over FOUR independent dimensions
    (`item.kind in GATE_DEFAULT_KINDS`, `item.status in live`, `not item.blocks_release`, and no
    gated carrier), and the realistic regression is that ONE conjunct changes meaning: a status
    leaving or joining the live set, `parked` losing its skip, the carrier exemption widening to any
    carrier regardless of its gate. Eleven tests report such a change as N unrelated `[] != ['...']`
    lines with no hint that they share a cause. The table reports one failure whose grouping IS the
    diagnosis, and it makes the grid browsable as a grid, so the next person adding a status can see
    which cells already exist.

    THE CLEAN ROWS ARE IN THE SAME TABLE and they carry the real weight here, because a predicate
    that flagged every backlog item would satisfy every flagging row on its own. `done` and `parked`
    are the load-bearing ones: a CLOSED bug is deliberately NOT gated (asserting a gate on it now
    would rewrite history), and a `parked` maybe is uncommitted work nobody has taken on. Their
    failure message says the flagging rows are vacuous while they are broken.

    EVERY FLAGGED ROW ALSO PINS THE FINDING'S SHAPE, which subsumes the old
    `test_finding_cites_the_written_rule_and_teaches_the_fix` and strengthens it from one status to
    all three: the fix must live in the STRUCTURED `recovery` field (what the human renderer prints
    as the Fix line and what the machine record carries), it must name THIS item's own status and
    id6, and the severity must be `error`. A fix written into `detail` instead is invisible where a
    reader looks for it; that was measured, and the generic "inspect ... frontmatter" fallback was
    printed in its place.
    """

    #: (case, status, work_kind, the metadata spelling of the kind field, the item's own gate or
    #: None, the carrier or None, whether RULE must fire, why this row exists)
    GRID = (
        (
            "an open ungated bug",
            "open",
            "bug",
            "Work-Kind",
            None,
            None,
            True,
            "THE BASE CASE OF THE WHOLE RULE: we do not ship known bugs, so a bug that is merely "
            "OPEN is already a release blocker. Filing it is not enough; the gate is what makes the "
            "release refuse to ship over it",
        ),
        (
            "a blocked ungated bug",
            "blocked",
            "bug",
            "Work-Kind",
            None,
            None,
            True,
            "BLOCKED IS A LIVE STATUS, and this row is what stops the intuitive-but-wrong reading "
            "that a blocked item is excused. BLOCKS-RELEASE and BLOCKED-BY are independent axes: "
            "the item cannot proceed, which is a fact about the item, and it still must not ship, "
            "which is a fact about the release",
        ),
        (
            "a graduated ungated bug with no carrier at all",
            "graduated",
            "bug",
            "Work-Kind",
            None,
            None,
            True,
            "`graduated` is LIVE too: the design was handed off but the code is not written, so the "
            "bug is still in the product. With no carrier there is nowhere else the gate could be, "
            "so the exemption below cannot apply",
        ),
        (
            "a graduated ungated bug whose carrier ALSO dropped the gate",
            "graduated",
            "bug",
            "Work-Kind",
            None,
            PLAN_UNGATED,
            True,
            "THE LEAK ITSELF: a carrier that exists but is UNGATED does not satisfy the rule. The "
            "exemption keys on the carrier HOLDING a gate, not on a carrier existing, so this row "
            "is what distinguishes a real handoff from a dropped one",
        ),
        (
            "a legacy `- Kind: bug` spelling",
            "open",
            "bug",
            "Kind",
            None,
            None,
            True,
            "THE SPELLING IS A COLUMN, NOT A SECOND FIXTURE: `parse_item` keeps a dual-read window "
            "over the canonical `- Work-Kind:` and the legacy `- Kind:`, so an item written before "
            "the rename is still a bug and must still be caught. A rule reading only the new "
            "spelling would silently exempt every pre-rename item",
        ),
        (
            "an open bug carrying its OWN gate",
            "open",
            "bug",
            "Work-Kind",
            "next",
            None,
            False,
            "THE PRIMARY CLEAN ROW: the item satisfies the rule directly. Every flagging row above "
            "is vacuous while this one is broken, because a predicate that flags every backlog item "
            "satisfies all of them",
        ),
        (
            "a DONE ungated bug",
            "done",
            "bug",
            "Work-Kind",
            None,
            None,
            False,
            "A CLOSED BUG IS DELIBERATELY NOT GATED, and this is a policy row rather than a "
            "convenience: a done bug shipped or it did not, so asserting a gate on it NOW would "
            "write a history that did not happen. The close direction has its own owner, "
            "`check.blocking-item-closed-without-gate`",
        ),
        (
            "a PARKED ungated bug",
            "parked",
            "bug",
            "Work-Kind",
            None,
            None,
            False,
            "a parked maybe is UNCOMMITTED work the attention view hides, so gating a release on "
            "one asserts an obligation nobody has taken on. This pair with `done` must match "
            "`backlog._GATE_DEFAULT_SKIP_STATUSES` exactly, or the creation default writes a gate "
            "the checker does not require (or the reverse)",
        ),
        (
            "an open ungated FEATURE",
            "open",
            "feature",
            "Work-Kind",
            None,
            None,
            False,
            "the gating work-kind set is `GATE_DEFAULT_KINDS`, today `bug` ALONE. A feature that is "
            "not finished is not a defect being shipped, so it does not gate by default",
        ),
        (
            "an open ungated CHORE",
            "open",
            "chore",
            "Work-Kind",
            None,
            None,
            False,
            "the separate row (rather than one loop over kinds) is what makes a WIDENING of "
            "`GATE_DEFAULT_KINDS` report as the specific kinds it newly caught. `chore` is the most "
            "likely to be widened, since an imperceptible inefficiency is filed here",
        ),
        (
            "an open ungated FOLLOWUP",
            "open",
            "followup",
            "Work-Kind",
            None,
            None,
            False,
            "a followup is deferred work by definition, so gating one would gate the release on "
            "something explicitly postponed",
        ),
        (
            "an open ungated SECURITY item",
            "open",
            "security",
            "Work-Kind",
            None,
            None,
            False,
            "THE MOST SURPRISING CLEAN ROW, kept for exactly that reason: a security item feels like "
            "it should gate, and today it does NOT, because the gating set is keyed on `bug` alone "
            "(widening it per repository is designed but unbuilt, backlog `0htqmm`). If this row "
            "ever starts failing, the set was widened and that is a DELIBERATE change to record",
        ),
        (
            "a graduated ungated bug whose PLAN carrier holds the gate",
            "graduated",
            "bug",
            "Work-Kind",
            None,
            PLAN_GATED,
            False,
            "HANDOFF, which AGENTS.md defines as legitimate: the gate travels with the work. "
            "Without this exemption a correctly-handed-off bug would be flagged forever, which "
            "trains people to ignore the rule",
        ),
        (
            "a graduated ungated bug whose SPEC carrier holds the gate",
            "graduated",
            "bug",
            "Work-Kind",
            None,
            SPEC_GATED,
            False,
            "A SPEC IS AN EQUALLY VALID CARRIER (`find_from_backlog_artifacts`), so a spec-first "
            "graduation closes the gate just as a plan does. Keeping both carrier types in one "
            "table is what shows the exemption is about the HANDOFF and not about plans",
        ),
        (
            "an OPEN ungated bug whose plan carrier holds the gate",
            "open",
            "bug",
            "Work-Kind",
            None,
            PLAN_GATED,
            False,
            "THE DISCRIMINATOR IS THE CARRIER'S GATE, NOT THE ITEM'S STATUS. Measured on the real "
            "tree, two `open` items have carriers, so keying the exemption on `graduated` would "
            "treat identical evidence differently depending on a status the handoff does not depend "
            "on. This row and the graduated one above are the same evidence in two statuses",
        ),
    )

    def _build(
        self, root: Path, id6: str, status, work_kind, kind_field, gate, carrier
    ):
        _item(
            root,
            id6,
            status=status,
            work_kind=work_kind,
            gate=gate,
            kind_field=kind_field,
        )
        if carrier is None:
            return
        kind, carrier_gate, _disposition = carrier
        if kind == "spec":
            _spec(root, "s" + id6[1:], id6, gate=carrier_gate)
        else:
            _plan(root, "p" + id6[1:], id6, gate=carrier_gate)

    def test_the_rule_fires_on_exactly_the_live_ungated_bugs(self):
        wrong = []
        clean_row_broken = False
        for i, (
            case,
            status,
            work_kind,
            kind_field,
            gate,
            carrier,
            fires,
            why,
        ) in enumerate(self.GRID):
            id6 = "g%05d" % i
            with TemporaryDirectory() as td:
                root = Path(td)
                self._build(root, id6, status, work_kind, kind_field, gate, carrier)
                drift = check_engine.check_live_bug_gate(root)
            hits = [d for d in drift if d.rule == RULE]
            problems = []
            if fires and _rules(drift) != [RULE]:
                problems.append(
                    f"expected exactly ['{RULE}']; the predicate reported {_counts(drift)}"
                )
            if not fires and drift:
                clean_row_broken = True
                problems.append(
                    f"expected NO finding; the predicate reported {_counts(drift)} "
                    f"({[d.detail for d in drift]!r})"
                )
            if fires and hits:
                hit = hits[0]
                # The finding's SHAPE, pinned on every flagging row rather than on one of them.
                if "Every live bug gates the next release" not in hit.detail:
                    problems.append(
                        "the detail must CITE the written rule (AGENTS.md, 'Every live bug gates "
                        f"the next release') rather than restate it; it said {hit.detail!r}"
                    )
                expected_fix = f"aw backlog set {status} {id6} --blocks-release next"
                if expected_fix not in (hit.recovery or ""):
                    problems.append(
                        f"the STRUCTURED recovery field must teach the runnable fix "
                        f"{expected_fix!r} (naming this item's own status and id6); it said "
                        f"{hit.recovery!r}. A fix written into `detail` is invisible where the "
                        "renderer prints the Fix line"
                    )
                if hit.severity != "error":
                    problems.append(
                        f"severity must be 'error' so the sweep's exit code refuses; it was "
                        f"{hit.severity!r}"
                    )
                if "no Blocks-Release" not in (hit.observed or ""):
                    problems.append(
                        f"`observed` must say what was actually found ('no Blocks-Release'); it "
                        f"said {hit.observed!r}"
                    )
                if "Blocks-Release" not in (hit.required or ""):
                    problems.append(
                        f"`required` must name the field that would satisfy the rule; it said "
                        f"{hit.required!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (status={status}, {kind_field}={work_kind}, item gate="
                    f"{gate!r}, carrier={carrier!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if clean_row_broken:
            note = (
                " NOTE: at least one CLEAN row is among the failures, so the predicate is now "
                "flagging items it must not. That makes every flagging row above vacuous, and if "
                "the `done` or `parked` row is one of them the rule is asserting an obligation on "
                "closed or uncommitted work."
            )
        self.assertEqual(
            wrong,
            [],
            f"`check_live_bug_gate` was wrong for {len(wrong)} of {len(self.GRID)} grid cells."
            f"{note} The rule is a CONJUNCTION over four dimensions (gating work-kind, live "
            "status, absent own gate, no gated carrier), so read the grouping rather than the "
            "rows: all three LIVE rows going clean means a status left the live set or "
            "`GATE_DEFAULT_KINDS` stopped matching `bug`; both CARRIER rows flipping together "
            "means the handoff exemption changed shape; the legacy-spelling row alone means "
            "`parse_item`'s dual read narrowed. FIX: a row that should fire and now lints clean is "
            "the dangerous direction, because the rule's only job is to REFUSE to ship a known "
            "bug, and a rule that stopped firing is a gate that stopped existing while still "
            f"appearing in the registry.\n" + "\n".join(wrong),
        )


class MismatchNarrowingTests(unittest.TestCase):
    """The OQ-03 ruling: `check.from-backlog-gate-mismatch` fires only for a LIVE carrier.

    ONE table replaces SEVEN tests. Each wrote one item plus one carrier, called
    `check_release_gate_consistency`, and asserted `[MISMATCH]` or `[]`, differing only in the
    carrier's DISPOSITION, its TYPE, and which side held a gate. Those three are now columns.

    THE DISPOSITION IS THE COLUMN THAT MATTERS, and it is why this must be one table rather than a
    live test plus a terminal test. The whole ruling is that the SAME mismatched pair is a finding
    when the carrier is live and is NOT one when the carrier is terminal, and only adjacent rows can
    state that. Split apart, a change that dropped the narrowing entirely would leave the live test
    green and read as three unrelated new failures in unrelated directories.

    Why the table beats the seven: the narrowing is ONE `if is_retired(p): continue`, so a
    regression moves rows in a legible pattern. All three TERMINAL rows failing together means the
    narrowing was reverted and the rule again demands an edit to a plan in `executed/` that
    AGENTS.md forbids; the LIVE rows failing together means the rule stopped firing at all and a
    dropped handoff is now silent.

    THE CLEAN ROWS ARE IN THE SAME TABLE. Two of them are load-bearing beyond vacuity: the
    matching-gates row is the ordinary correct state (a rule that fired on every carrier would
    satisfy every flagging row), and the GATED-CARRIER-UNDER-UNGATED-ITEM row is the durable half of
    the ruling, asserting the deliberate ASYMMETRY.
    """

    #: (case, the item's gate or None, ("plan"|"spec", carrier gate, disposition, plan status), the
    #: From-Backlog id6 the carrier points at ("item" means the item written for this row), rules
    #: that must be reported EXACTLY, detail substrings required on them, why this row exists)
    MISMATCHES = (
        (
            "a LIVE pending plan carrier that dropped the gate",
            "next",
            ("plan", None, "pending", "to-review"),
            "item",
            (MISMATCH,),
            ("plan", "next"),
            "THE DIRECTION THAT MUST KEEP FIRING, and the only thing this rule protects: a DROPPED "
            "HANDOFF, where the gate silently vanishes between a blocking item and the live plan "
            "that graduated from it",
        ),
        (
            "a LIVE spec carrier whose gate names a DIFFERENT release",
            "next",
            ("spec", "v9z9z9", "specs", ""),
            "item",
            (MISMATCH,),
            ("spec", "next", "v9z9z9"),
            "THE SPEC SIDE OF THE SCAN MUST SURVIVE THE NARROWING (bklgrad v58bvy E-07), and this "
            "row uses a MISMATCHED gate rather than an absent one so it also proves the rule "
            "compares VALUES and does not merely check presence. The detail must name the record "
            "type, or a reader cannot tell which of two carriers is at fault",
        ),
        (
            "an EXECUTED plan carrier that dropped the gate",
            "next",
            ("plan", None, "executed", "executed"),
            "item",
            (),
            (),
            "THE CASE THAT BLOCKED THE PARENT SET, and it FAILS against pre-change code, which is "
            "the point of the row: flagging it demanded a commit to a plan already in `executed/` "
            "that AGENTS.md forbids. A terminal carrier's work is DONE, so it cannot drop a FUTURE "
            "obligation and there is no future release for it to gate",
        ),
        (
            "a SUPERSEDED plan carrier that dropped the gate",
            "next",
            ("plan", None, "superseded", "superseded"),
            "item",
            (),
            (),
            'the ruled rationale ("work is DONE, no future release to gate") holds for EVERY '
            "terminal disposition, which is why the shipped `is_retired` predicate is used rather "
            "than the narrower `_EXECUTED_SEGMENT` literal. This row is what would fail if someone "
            "narrowed the skip back to `executed/` alone",
        ),
        (
            "a NOT-EXECUTED plan carrier that dropped the gate",
            "next",
            ("plan", None, "not-executed", "not-executed"),
            "item",
            (),
            (),
            "the third terminal disposition, kept as its own row for the same reason: a plan "
            "deliberately never run has no future either, and `not-executed` is the disposition "
            "most likely to be forgotten in a hand-written path test",
        ),
        (
            "a GATED carrier under an UNGATED item",
            None,
            ("plan", "next", "pending", "to-review"),
            "item",
            (),
            (),
            "THE ZERO-FINDING DIRECTION AND THE DURABLE HALF OF THE RULING. The maintainer's pivot "
            'question was "why would we care if a plan is blocking but the backlog is not?", and '
            "the answer is that we would not: a plan can discover DURING execution that it gates a "
            "release for reasons its originating item never knew, and forbidding that punishes the "
            "plan for being better informed than its own provenance. This is currently unreachable "
            "BY CONSTRUCTION (the `item_gate` map is populated only for a GATED item), so WITHOUT "
            "this row nothing would notice a refactor making the rule symmetric again",
        ),
        (
            "matching gates on both sides",
            "next",
            ("plan", "next", "pending", "to-review"),
            "item",
            (),
            (),
            "THE ORDINARY CORRECT STATE, and the anti-vacuity row: a rule that flagged every "
            "From-Backlog carrier would satisfy both flagging rows above on its own",
        ),
        (
            "a live gated carrier pointing at an item that does not exist",
            None,
            ("plan", "next", "pending", "to-review"),
            "zzzzzz",
            (),
            (),
            "DIVISION OF LABOUR: a DANGLING `From-Backlog` is `check.from-backlog-dangling`'s job, "
            "not this rule's. Without this row the mismatch rule could start reporting a second "
            "finding for the same defect, and a user fixing one would still see the other",
        ),
    )

    def test_the_mismatch_rule_fires_only_for_a_live_carrier(self):
        wrong = []
        clean_row_broken = False
        for i, (
            case,
            item_gate,
            carrier,
            target,
            expected,
            needles,
            why,
        ) in enumerate(self.MISMATCHES):
            id6 = "m%05d" % i
            kind, carrier_gate, disposition, plan_status = carrier
            with TemporaryDirectory() as td:
                root = Path(td)
                _item(root, id6, status="graduated", work_kind="bug", gate=item_gate)
                points_at = id6 if target == "item" else target
                if kind == "spec":
                    _spec(root, "s" + id6[1:], points_at, gate=carrier_gate)
                else:
                    _plan(
                        root,
                        "p" + id6[1:],
                        points_at,
                        gate=carrier_gate,
                        disposition=disposition,
                        status=plan_status,
                    )
                drift = check_engine.check_release_gate_consistency(root)
            problems = []
            if _rules(drift) != list(expected):
                if expected:
                    problems.append(
                        f"expected exactly {list(expected)!r}; the rule reported "
                        f"{_counts(drift)}"
                    )
                else:
                    clean_row_broken = True
                    problems.append(
                        f"expected NO finding; the rule reported {_counts(drift)} "
                        f"({[d.detail for d in drift]!r})"
                    )
            details = " | ".join(d.detail for d in drift)
            missing = [n for n in needles if n not in details]
            if missing:
                problems.append(
                    f"the detail never mentions {missing!r}, so a reader cannot tell which carrier "
                    f"or which release is at fault; it said {details!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (item gate={item_gate!r}, carrier={kind} gate={carrier_gate!r} in "
                    f"{disposition}/):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if clean_row_broken:
            note = (
                " NOTE: a CLEAN row is among the failures. If it is one of the three TERMINAL "
                "rows, the OQ-03 narrowing was reverted and the rule again demands a commit to a "
                "plan in a terminal directory that AGENTS.md forbids editing. If it is the "
                "gated-carrier-under-ungated-item row, the rule became SYMMETRIC and now punishes "
                "a plan for gating a release its originating item never knew about."
            )
        self.assertEqual(
            wrong,
            [],
            f"`check_release_gate_consistency` was wrong for {len(wrong)} of "
            f"{len(self.MISMATCHES)} item/carrier pairs.{note} ONE `if is_retired(p): continue` "
            "implements the narrowing and ONE value comparison implements the rule, so read the "
            "grouping: all three TERMINAL rows failing together means the narrowing is gone, both "
            "FLAGGING rows failing together means the rule stopped firing and a dropped handoff is "
            "now silent, and the spec row alone means the walk narrowed back to plans. FIX: this "
            "rule's entire subject is a gate that VANISHED between an item and its carrier, so a "
            "flagging row that goes clean means the release gate can now be lost in the handoff "
            f"with nothing reporting it.\n" + "\n".join(wrong),
        )

    def test_narrowing_uses_the_shipped_terminal_predicate(self):
        """Kept separate: the subject is the FUNCTION'S SOURCE, not a repository state.

        Per the ruling, terminal classification must reuse the shipped `is_retired` rather than a
        fresh path test. No fixture row can state that, since every fixture would pass against a
        hand-rolled duplicate.
        """
        src = inspect.getsource(check_engine.check_release_gate_consistency)
        self.assertIn("is_retired(", src)


class LiveBugGateSeamTests(unittest.TestCase):
    """WHICH SHIPPED SEAM surfaces the rule, which is not the same question as whether it fires.

    ONE table replaces FIVE tests (four from this class plus `BackfillEndStateTests`'s zero-finding
    case). Review measured that calling a predicate DIRECTLY passes while the shipped command
    reports nothing, which is exactly how an unwired rule ships green, so each row drives a real
    entry point rather than the predicate.

    THE SEAM IS A COLUMN, and that is the whole reason these belong together: the rule must be
    REPORTED by `check_types(['all'])`, must be ABSENT from `check_types(['backlog'])`, and must be
    ABSENT from `check_commit_invariants`. Each of those alone is a weak claim; together they state
    the rule's wiring exactly. A change that moved the I-07 family onto the backlog content path
    would flip two rows at once and read as one decision rather than two unrelated failures.

    THE TREE STATE IS THE SECOND COLUMN, so the same seam appears with a violating tree and with a
    clean one. The clean-tree rows are the anti-vacuity half: a sweep that reported the rule
    unconditionally would satisfy every must-report row.
    """

    #: (case, the item's own gate or None, the carrier or None, the seam to drive, rules that must
    #: be reported, rules that must NOT be reported, why this row exists)
    SEAMS = (
        (
            "the full sweep over a tree with an ungated live bug",
            None,
            None,
            "check_types:all",
            (RULE,),
            (),
            "THE SEAM TEST, and the reason this class exists: an unwired rule passes every direct "
            "predicate call and reports nothing from the command a human actually runs. Only "
            "driving `check_types` can catch that",
        ),
        (
            "the BACKLOG type scope over the same tree",
            None,
            None,
            "check_types:backlog",
            (),
            (RULE,),
            "A STATED COST, asserted so it is a decision rather than a surprise: the whole I-07 "
            "family rides the once-per-full-sweep seam, so `aw check backlog` is BLIND to it. If a "
            "later change wires the family into the backlog content path, this row SHOULD fail and "
            "be updated rather than worked around",
        ),
        (
            "the pre-commit aggregator over the same tree",
            None,
            None,
            "check_commit_invariants",
            (),
            (RULE,),
            "IT MUST NOT REACH `check_commit_invariants`: every rule there is commit- or "
            "receipt-scoped, and a WHOLE-TREE rule in a pre-commit gate would refuse your commit "
            "because ANOTHER party's item elsewhere in this shared checkout is ungated",
        ),
        (
            "the full sweep over a tree whose bug carries its own gate",
            "next",
            None,
            "check_types:all",
            (),
            (RULE,),
            "THE ANTI-VACUITY ROW for the seam above: a sweep that reported the rule "
            "unconditionally would satisfy the must-report row while saying nothing about the "
            "tree. Note this tree is NOT finding-free (the gate resolves to no release record, so "
            "`check.blocks-release-dangling` fires), which is why rows assert rule PRESENCE rather "
            "than an empty list",
        ),
        (
            "the full sweep after backfilling a gate onto an item with a TERMINAL carrier",
            "next",
            ("plan", None, "executed", "executed"),
            "check_types:all",
            (),
            (RULE, MISMATCH),
            "THE CROSS-RULE END STATE THE PARENT SET REQUIRED, and the case that blocked it: "
            "satisfying the NEW rule by gating the item is what VIOLATED the OLD one, because its "
            "carrier sits in `executed/` with no tooled remedy. With the narrowing, BOTH rules are "
            "clean on one tree, and asserting both together is the only way to state that the "
            "remedy for one rule does not trip the other",
        ),
    )

    def test_each_seam_reports_exactly_the_rules_it_should(self):
        wrong = []
        for i, (case, gate, carrier, seam, must, must_not, why) in enumerate(
            self.SEAMS
        ):
            id6 = "e%05d" % i
            with TemporaryDirectory() as td:
                root = Path(td)
                _item(root, id6, status="graduated", work_kind="bug", gate=gate)
                if carrier is not None:
                    _kind, carrier_gate, disposition, plan_status = carrier
                    _plan(
                        root,
                        "p" + id6[1:],
                        id6,
                        gate=carrier_gate,
                        disposition=disposition,
                        status=plan_status,
                    )
                if seam == "check_commit_invariants":
                    drift = check_engine.check_commit_invariants(root)
                else:
                    drift = check_engine.check_types(root, [seam.split(":", 1)[1]])
            reported = _rules(drift)
            problems = []
            absent = [r for r in must if r not in reported]
            if absent:
                problems.append(
                    f"{absent!r} never reached this seam, so the rule is unwired here; it reported "
                    f"{_counts(drift)}"
                )
            leaked = [r for r in must_not if r in reported]
            if leaked:
                problems.append(
                    f"{leaked!r} must NOT be reported at this seam and was; it reported "
                    f"{_counts(drift)}"
                )
            if problems:
                wrong.append(
                    f"  {case} (seam={seam}, item gate={gate!r}, carrier={carrier!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the rule was surfaced at the wrong seams in {len(wrong)} of {len(self.SEAMS)} cases. "
            "The three seams are ONE wiring decision, so read the grouping: the `all` row failing "
            "alone means the rule is not registered on the full sweep and ships green while "
            "reporting nothing to a human; the `backlog` and `check_commit_invariants` rows "
            "failing together means the whole I-07 family moved onto a narrower path, which is a "
            "deliberate change to record here, not a bug to route around. FIX: a leak into "
            "`check_commit_invariants` is the worst outcome, because a whole-tree rule in a "
            "pre-commit gate refuses commits over ANOTHER party's item in this shared "
            f"checkout.\n" + "\n".join(wrong),
        )


class LiveBugGateRegistrationTests(unittest.TestCase):
    """The I-07 family's registry entries, asserted as a FAMILY.

    ONE table replaces THREE tests. Two asserted different fields of the same registry entry
    (severity+invariant, then assurance+determinism), and the third looped four siblings asserting
    only that their invariant EQUALS the new rule's. Comparing to a sibling is weaker than naming
    the value: if the whole family were renumbered together, that comparison stays green.

    Why the table beats the three: an UNREGISTERED rule silently falls back to `_DEFAULT_RULESPEC`
    with an empty invariant, losing the I-07 trace, and the realistic regression is a family-wide
    renumbering or an assurance/determinism reclassification. The table names the expected values
    literally, so a family-wide move reports as one failure listing every rule that moved, which is
    the shape of that problem.

    THE INVARIANT IS WRITTEN AS THE LITERAL 'I-07', NOT read back from another registry entry, and
    that is deliberate: a comparison against a sibling cannot distinguish "correct" from "all five
    moved together".
    """

    #: (rule id, expected severity, expected invariant, expected assurance, expected determinism,
    #: why this row exists)
    REGISTRATIONS = (
        (
            RULE,
            "error",
            "I-07",
            check_engine.ASSURANCE_REPOSITORY,
            check_engine.DET_DETERMINISTIC,
            "THE RULE UNDER TEST. Registration is not cosmetic: an unregistered rule falls back to "
            "`_DEFAULT_RULESPEC`, whose invariant is EMPTY, so the I-07 trace is lost and the rule "
            "stops being attributable to the release-gate family. `error` is what makes the sweep "
            "exit nonzero; a `warning` here would let a known bug ship with a green check",
        ),
        (
            "check.blocking-item-closed-without-gate",
            "error",
            "I-07",
            check_engine.ASSURANCE_REPOSITORY,
            check_engine.DET_DETERMINISTIC,
            "THE CLOSE DIRECTION of the same invariant, and the reason the new rule skips `done`: "
            "this one owns that half. Their sharing I-07 is what documents that they are two "
            "directions of one obligation rather than two unrelated checks",
        ),
        (
            MISMATCH,
            "error",
            "I-07",
            check_engine.ASSURANCE_REPOSITORY,
            check_engine.DET_DETERMINISTIC,
            "the HANDOFF-CONTRADICTED direction, and the rule narrowed by the same plan. It must "
            "stay `error`: a mismatched handoff silently loses a release gate, which is the exact "
            "failure the family exists to prevent",
        ),
        (
            "check.blocks-release-dangling",
            "error",
            "I-07",
            check_engine.ASSURANCE_REPOSITORY,
            check_engine.DET_DETERMINISTIC,
            "the UNRESOLVABLE-gate direction. Together with the rows above this states the family's "
            "division of labour: ABSENT gate (the new rule), UNRESOLVABLE gate (this), "
            "CONTRADICTED gate (mismatch), carrier pointing at NOTHING (below)",
        ),
        (
            "check.from-backlog-dangling",
            "error",
            "I-07",
            check_engine.ASSURANCE_REPOSITORY,
            check_engine.DET_DETERMINISTIC,
            "the BROKEN-PROVENANCE direction, which is why the mismatch rule may stay silent on a "
            "dangling From-Backlog (see that row in `MISMATCHES`): this rule already owns it",
        ),
    )

    def test_the_whole_I07_family_is_registered_as_deterministic_repository_errors(
        self,
    ):
        wrong = []
        for (
            rule,
            severity,
            invariant,
            assurance,
            determinism,
            why,
        ) in self.REGISTRATIONS:
            problems = []
            spec = check_engine.RULE_REGISTRY.get(rule)
            if spec is None:
                problems.append(
                    "NOT IN `RULE_REGISTRY` at all, so it falls back to `_DEFAULT_RULESPEC` with "
                    "an empty invariant and loses its family trace"
                )
            else:
                for field, expected in (
                    ("severity", severity),
                    ("invariant", invariant),
                    ("assurance", assurance),
                    ("determinism", determinism),
                ):
                    actual = getattr(spec, field, None)
                    if actual != expected:
                        problems.append(
                            f"{field}: expected {expected!r}, got {actual!r}"
                        )
            if problems:
                wrong.append(
                    f"  {rule}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.REGISTRATIONS)} I-07 rules are registered wrongly. These "
            "five are ONE family, so read the grouping: EVERY row reporting the same wrong "
            "invariant means the family was renumbered (a deliberate change; update the literals "
            "here, and note that the old version of this test compared siblings to each other and "
            "would have stayed GREEN through exactly that move), while ONE row differing means a "
            "single rule was misfiled or a new registration overwrote it. FIX: a severity "
            "downgraded from `error` is the silent failure that matters, because the sweep's exit "
            "code is what stops a release, so a `warning` here lets a known bug ship with a green "
            f"check.\n" + "\n".join(wrong),
        )


class LiveBugGateReuseTests(unittest.TestCase):
    """The predicate must CONSUME the shared definitions rather than fork them.

    ONE table replaces FOUR tests, three of which were already `subTest` loops over the same two
    functions: one asserted each consumer mentions `_from_backlog_carrier_index`, one asserted
    neither re-derives the walk with its own iterator, and one asserted the new predicate does not
    fork the live-status vocabulary. They differed only in WHICH function and WHICH token, so both
    are columns.

    Why the table beats the four: these are all one claim, that "what counts as a carrier" and "what
    counts as LIVE" each have exactly ONE owner. A fork shows up as a missing REQUIRED token or a
    present FORBIDDEN one, and seeing both consumers side by side is what states the shared-owner
    property; a single function's source proves nothing about sharing.

    NOTE ON WHAT THIS REPLACED: the parent plan asked for proof that the predicate consumes
    `evaluate_blocking_close`. It does not and cannot (see
    `test_evaluate_blocking_close_cannot_answer_the_open_direction`), so asserting that would pin
    the wrong design in place. These assert the reuse that actually matters.
    """

    #: (the function, tokens whose PRESENCE is required, tokens whose ABSENCE is required, why this
    #: row exists)
    REUSE = (
        (
            check_engine.check_live_bug_gate,
            (
                "_from_backlog_carrier_index",
                "_backlog.STATUSES",
                "_GATE_DEFAULT_SKIP_STATUSES",
                "GATE_DEFAULT_KINDS",
            ),
            ("_iter_plan_ipds", "_iter_spec_records"),
            "THE NEW PREDICATE, which must fork NEITHER definition. The carrier index owns what "
            "counts as a handoff; `STATUSES` minus `_GATE_DEFAULT_SKIP_STATUSES` owns what counts "
            "as LIVE, and deriving it that way is what keeps the CHECKER and the creation DEFAULT "
            "teaching one rule instead of two. A fourth hardcoded status list here is how the "
            "setter and the checker silently disagree",
        ),
        (
            check_engine.check_release_gate_consistency,
            ("_from_backlog_carrier_index",),
            ("_iter_plan_ipds", "_iter_spec_records"),
            "THE OTHER CONSUMER, and the row that makes this a SHARING claim rather than a spelling "
            "check: with only the row above, both functions could each own a private walk and the "
            "test would pass. This one does not assert the status vocabulary, because the mismatch "
            "rule legitimately has no live-status opinion; it compares gate VALUES",
        ),
    )

    def test_neither_consumer_forks_the_shared_definitions(self):
        wrong = []
        for fn, required, forbidden, why in self.REUSE:
            src = inspect.getsource(fn)
            problems = []
            missing = [t for t in required if t not in src]
            if missing:
                problems.append(
                    f"does not consume {missing!r}, so it has forked a definition that must have "
                    "exactly one owner"
                )
            present = [t for t in forbidden if t in src]
            if present:
                problems.append(
                    f"re-derives the carrier set with {present!r} instead of using the shared "
                    "index, so the two consumers can now disagree about what a carrier is"
                )
            if problems:
                wrong.append(
                    f"  {fn.__name__}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.REUSE)} consumers forked a shared definition. The claim is "
            "that `_from_backlog_carrier_index` is the ONE definition of a handoff carrier and that "
            "the live-status set is DERIVED, so read the grouping: BOTH rows losing the index means "
            "it was inlined or renamed (update the tokens if renamed), while ONE row losing it "
            "means that consumer grew a private walk and the two rules will drift on what counts as "
            "a carrier. FIX: a forked LIVE-status list is the subtler half, because the checker and "
            "`aw backlog new`'s gate default would then teach different rules and neither would "
            f"look wrong on its own.\n" + "\n".join(wrong),
        )

    def test_no_second_copy_of_the_blocks_release_regex(self):
        """Kept separate: the subject is the whole MODULE FILE and the claim is a COUNT.

        Every row above reads ONE function's source and asks about containment. This asks how many
        times the compiled `- Blocks-Release:` pattern is written anywhere in the module, which no
        per-function containment row can express.
        """
        src = Path(check_engine.__file__).read_text(encoding="utf-8")
        self.assertEqual(src.count('r"(?m)^- Blocks-Release:'), 1)

    def test_the_live_set_agrees_with_the_creation_default(self):
        """Kept separate: asserts over shared VOCABULARY SETS, with no repository and no rule.

        The statuses this rule REQUIRES a gate on must be exactly the ones the creation default
        APPLIES a gate to, or the checker and the setter teach different rules. That is a claim
        about two frozensets, so no fixture row can state it.
        """
        from agent_workflows import backlog

        live = backlog.STATUSES - backlog._GATE_DEFAULT_SKIP_STATUSES
        self.assertEqual(live, {"open", "blocked", "graduated"})

    def test_evaluate_blocking_close_cannot_answer_the_open_direction(self):
        """Kept separate: the subject is a DIFFERENT predicate, proven UNUSABLE rather than checked.

        The NON-USE proof. Every branch of `evaluate_blocking_close` keys on the gate being PRESENT,
        so on an ungated item it returns legitimate/ok whichever transition is asked about. Folding
        this into the gate grid would file a claim about a different function under the rule's name.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            p = _item(root, "ddd111", status="open", work_kind="bug", gate=None)
            done = check_engine.evaluate_blocking_close(root, p, "done")
            self.assertTrue(done.legitimate)
            self.assertEqual(done.severity, "ok")
            self.assertEqual(done.reason, "no release gate to preserve")
            other = check_engine.evaluate_blocking_close(root, p, "open")
            self.assertTrue(other.legitimate)
            self.assertEqual(other.severity, "ok")
            self.assertEqual(other.reason, "unchecked transition")


class BackfillEndStateTests(unittest.TestCase):
    """The one cross-rule case that is a BEFORE/AFTER pair rather than a row."""

    def test_backfilling_an_item_with_a_live_carrier_needs_the_carrier_co_updated(self):
        """Kept separate: a before/after pair whose content is that the answer CHANGES.

        A LIVE carrier is NOT skipped, so a backfill genuinely has to co-update it. The claim is
        about the TRANSITION (mismatch reported, then the carrier edited, then silent on the same
        tree), which a single-state row cannot express. Asserted so the remedy is not mistaken for
        unnecessary. Its zero-finding twin, the TERMINAL-carrier case, is a row in
        `LiveBugGateSeamTests.SEAMS`.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            _item(root, "ggg222", status="graduated", work_kind="bug", gate="next")
            carrier = _plan(root, "ppg222", "ggg222", gate=None, disposition="pending")
            before = _rules(check_engine.check_types(root, ["all"]))
            self.assertIn(MISMATCH, before)
            self.assertNotIn(RULE, before)
            carrier.write_text(
                carrier.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Blocks-Release: next\n- Status: to-review"
                ),
                encoding="utf-8",
            )
            after = _rules(check_engine.check_types(root, ["all"]))
            self.assertNotIn(MISMATCH, after)
            self.assertNotIn(RULE, after)


if __name__ == "__main__":
    unittest.main()

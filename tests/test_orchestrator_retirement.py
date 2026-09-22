"""orchretire Order 01 (`5942n7`): the shared ON-DISK Set-completeness decision predicate.

WHAT THIS PINS, and why each half exists rather than merely that it does.

E-01/V-01, MEMBERSHIP FROM THE PLANS TREE. The defect being fixed is that
`oc_runipd._set_children_all_executed` reads `state["queue"]`, so a run that executes the Set's LAST
outstanding child sees ONE child rather than the Set. The CROSS-RUN case is therefore the load-bearing
test here: a Set whose children all sit in `executed/` and appear in NO queue must be readable in full.

E-02/V-02, THE TYPED DECISION. The old shape returned `(False, [])` for BOTH "children are unfinished"
and "there are no children", which is how `5e4sb6`'s durable event came to read "dependency-blocked
(unmet dependencies)" while naming no dependency. Every refusal cause is asserted to be DISTINCT and to
carry its own specifics. The `executed` test is an ALLOWLIST, so a status nobody has invented yet is
refused by construction; a denylist of known-bad values would silently admit it.

E-03/V-03, THE CHILD-TABLE PARSER, TESTED ON THE FOUR REAL COLUMN SHAPES. This is the half a synthetic
test suite would have got wrong. Measured across all five live orchestrators, the layouts share ONLY
the FIRST column and `rununify` has NO `Id` column at all:

    orchretire  | Order | Id | Child | Depends on |
    wslayout    | Order | Id | What it does | Set dependencies |
    runprofile  | Order | Id | Child | Responsibility | Depends on |
    lanectn     | Order | Id | Depth | Requirements owned | Prerequisite | What it delivers |
    rununify    | Order | What it does | Depends on |            <- NO `Id` COLUMN

So the fixtures below COPY those four real shapes instead of inventing a uniform one: a parser
validated only on this plan's own table format is validated on the one shape that was never going to
break. `rununify` also carries the non-numeric row tokens `03+` AND `last`, and `runprofile`
legitimately has SIX children on disk against five declared rows - the case that proves the
declared-vs-resolved comparison must stay ONE-DIRECTIONAL.

THE FAILURE DIRECTION IS ASSERTED, NOT ASSUMED. A false refusal leaves an orchestrator in `pending/`
(today's status quo); a false eligibility asserts a completion that never happened. Every ambiguous
input below is therefore expected to REFUSE.

MUCH OF THIS FILE IS TABLE-DRIVEN, because much of it was one shape repeated: build a Set on disk,
ask one question, assert one verdict. The tables group by SUBJECT (the decision, the child-table
parse, the membership read, the rollup's refusal gates, the live corpus) rather than by which plan
Order added the behavior, which is what the class boundaries used to track.

RETIREMENT IS A SAFETY GATE, SO NO ROW EVER ASSERTS MERELY "IT REFUSED". Every refusal row names the
EXACT typed reason and additionally pins the specifics that substantiate it (the `unfinished` map,
the `unauthored_rows` tuple, the detail naming what is being waited on), including asserting those
are EMPTY where the cause is something else. That is deliberate and it is the defect this Set fixed:
`5e4sb6`'s durable event read "dependency-blocked (unmet dependencies)" while naming no dependency,
because the old shape returned `(False, [])` for BOTH "children unfinished" and "no children". A
table asserting only a boolean would pass on that. Rows in the rollup-gate table further assert the
plan was left BYTE-UNCHANGED and IN PLACE, so a refusal that has already performed the transition is
not accepted as a refusal.

SOURCE-TEXT PINS WERE REPLACED WITH BEHAVIORAL TESTS, roughly two dozen of them, and this is the
largest change in the file. What they had in common: they asserted that some function's TEXT
contained or lacked a token (via `inspect.getsource`, an `ast.unparse` of one function body, or a
`read_text` of a whole module), which breaks on reformatting and on any rename, and which can be
satisfied by editing a COMMENT. Two bespoke helpers existed only to make such assertions survivable
and are now deleted with their last callers. Each was replaced by a test that DRIVES the code and
measures the observable result, or deleted where an existing behavioral test already covered it:

  * "the predicate performs no transition" now SNAPSHOTS the whole plans tree byte for byte, drives
    every decision path, and compares, so it catches a mutation by ANY spelling rather than by the
    seven tokens somebody thought to forbid;
  * "the rollup reuses the ONE canonical role message" now PATCHES `LIFECYCLE_ROLE_ERROR` to a
    sentinel and requires it in the refusal, which a hardcoded copy cannot produce;
  * "these gates are shared AS CODE" now patches each shared helper with a spy and drives BOTH
    transition paths, so a faithful copy of the helper's body fails where a name in a comment passed;
  * "the rollup does not reimplement the move or the commit" now NEUTRALIZES the shared transaction
    and asserts the plan did not move and HEAD did not advance;
  * "the gate and the dispatch cannot disagree" now asks BOTH sites about every Set shape and
    requires their verdicts to correspond, which a name-mentioning gate that then overrode the shared
    verdict would have passed;
  * "agy's branch short-circuits" now makes `execute_item` RAISE, so reaching it fails with the
    exception rather than with a claim about an `ast.If`;
  * "the ff-only merge is the only thing that advances the branch" now RECORDS every git command and
    the directory it ran in. This one found a real thing the pin could not see: a path-scoped
    `git checkout HEAD -- <the plan's own path>` that runs from `_release_own_uncommitted_plan_edit`,
    not from the function the pin inspected.

TESTS THAT ARE NOT ROWS CARRY A ONE-LINE DOCSTRING SAYING WHY. The recurring reasons: the subject is
the REAL repository rather than a fixture; the setup is materially different (a git-backed checkout,
a patched collaborator, a fault injection, a hand-built record); the claim is STRUCTURAL (a constant's
value, a symbol's existence, a record type's property); the assertion is an EXACT finding tuple where
a table row asserts membership; or the property is a before/after pair or a comparison of two results
to each other rather than to an expectation.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import runner_shared as rs
from tests.support import REPO_ROOT

# ==================================================================================================
# Synthetic-repo helpers
# ==================================================================================================


def _plan_text(
    *,
    plan_id: str,
    set_id: str,
    order: int,
    status: str,
    kind: str = "child",
    body: str = "",
) -> str:
    return (
        "# IPD: synthetic\n"
        "- Date: 2026-09-06\n"
        f"- Kind: {kind}\n"
        "- Concern: synthetic fixture.\n"
        "- Scope: synthetic fixture.\n"
        "- Scope-Paths: grandfathered\n"
        f"- Status: {status}\n"
        f"- Set: {set_id}\n"
        f"- Order: {order}\n"
        f"- Id: {plan_id}\n"
        "\n" + body
    )


def _write_plan(
    repo: Path,
    bucket: str,
    *,
    plan_id: str,
    set_id: str,
    order: int,
    status: str,
    kind: str = "child",
    body: str = "",
) -> Path:
    d = repo / ".aw" / "records" / "plans" / bucket
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"20260906-{set_id}-{order:02d}-{plan_id}-synthetic.ipd.md"
    path.write_text(
        _plan_text(
            plan_id=plan_id,
            set_id=set_id,
            order=order,
            status=status,
            kind=kind,
            body=body,
        ),
        encoding="utf-8",
    )
    return path


def _table(header_cells: list[str], rows: list[list[str]]) -> str:
    """Render a child-IPDs section with an EXPLICIT column layout.

    The layout is a PARAMETER precisely because the five real orchestrators disagree about it; a
    helper that hardcoded one would defeat the purpose of these fixtures.
    """

    out = [f"## {rs._CHILD_IPDS_HEADING}", ""]
    out.append("| " + " | ".join(header_cells) + " |")
    out.append("|" + "|".join(["---"] * len(header_cells)) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    out.append("")
    return "\n".join(out)


class _Repo:
    """A throwaway repo containing only a plans tree."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()


class SyntheticSetCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _Repo()
        self.addCleanup(self.repo.close)

    @property
    def root(self) -> Path:
        return self.repo.root

    def make_set(
        self,
        setid: str,
        children: list[tuple[str, int, str, str]],
        *,
        header: list[str] | None = None,
        declared_rows: list[str] | None = None,
        orchestrator_status: str = "approved",
        orchestrator_id: str = "orc000",
        orchestrator_body: str | None = None,
        with_orchestrator: bool = True,
    ) -> None:
        """`children` is a list of `(id6, order, status, bucket)`."""

        for id6, order, status, bucket in children:
            _write_plan(
                self.root,
                bucket,
                plan_id=id6,
                set_id=setid,
                order=order,
                status=status,
            )
        if not with_orchestrator:
            return
        if orchestrator_body is None:
            cells = header or ["Order", "Id", "Child", "Depends on"]
            tokens = declared_rows or [
                f"{order:02d}" for _id6, order, _s, _b in children
            ]
            rows = [[tok] + ["x"] * (len(cells) - 1) for tok in tokens]
            orchestrator_body = _table(cells, rows)
        _write_plan(
            self.root,
            "pending",
            plan_id=orchestrator_id,
            set_id=setid,
            order=0,
            status=orchestrator_status,
            kind="orchestrator",
            body=orchestrator_body,
        )


# ==================================================================================================
# V-01: membership is read from the PLANS TREE, across runs
# ==================================================================================================


class MembershipReadsThePlansTree(SyntheticSetCase):
    """Membership is read from the PLANS TREE on disk, ACROSS runs, and never from a queue.

    ONE table replaces five tests (the cross-run case, the pending/executed split, the kind-not-
    counting case, the ordering case, and the empty/unknown selector case). Each wrote a synthetic
    Set, called `read_set_membership`, and asserted some part of the returned membership.

    THE WHOLE MEMBERSHIP IS ASSERTED PER ROW, which is what the table bought. The old tests each
    checked ONE facet: the cross-run test checked the child ids and statuses, the split test checked
    only the (id, status) pairs, the kind test checked only the counts, and the ordering test checked
    only the orders. So a resolver that returned the right children in the right order while
    misidentifying WHICH member is the orchestrator passed four of the five. Every row now pins the
    orchestrator's id6, the child list IN ORDER, the statuses, and the member/child counts together.

    THE BUCKET IS A COLUMN, AND IT IS THE DEFECT THIS PREDICATE EXISTS TO FIX.
    `oc_runipd._set_children_all_executed` read `state["queue"]`, so a run that executed a Set's LAST
    outstanding child saw ONE child rather than the Set. The cross-run row is therefore load-bearing:
    its children sit in `executed/` and appear in NO queue (the row asserts the repo has no run state
    at all), and it must still be read in full. A queue-scoped check cannot answer it.

    THE EMPTY AND UNKNOWN SELECTORS ARE ROWS, NOT RAISES, deliberately: an unresolvable Set must
    return an EMPTY membership rather than throw, because the caller's next step is a refusal decision
    and an exception there would abort a whole run over one mistyped setid.
    """

    #: (case, children as (id6, order, status, bucket), the selector to resolve, the expected
    #:  orchestrator id6 or None, the expected child ids IN ORDER, the expected member COUNT, why)
    MEMBERSHIPS = (
        (
            "every child in `executed/`, with NO run state anywhere",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
            ],
            None,
            "orc000",
            ["aaa111", "bbb222", "ccc333"],
            4,
            "THE CROSS-RUN CASE, which is the whole reason this predicate reads DISK. None of these "
            "children is in any queue and the repo has no run state at all, yet the Set must be seen "
            "as complete. The queue-scoped predicate it replaces saw ONE child here, so a run that "
            "executed the last outstanding child could never retire the parent",
        ),
        (
            "members SPLIT across `pending/` and `executed/`",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
            ],
            None,
            "orc000",
            ["aaa111", "bbb222"],
            3,
            "the tree is read across BUCKETS, so a partially finished Set is seen whole. Reading one "
            "bucket would make a Set look complete by ignoring the children that are not done yet, "
            "which is the direction that retires a parent early",
        ),
        (
            "one child, so the orchestrator cannot be identified by COUNTING",
            [("aaa111", 1, "executed", "executed")],
            None,
            "orc000",
            ["aaa111"],
            2,
            "the orchestrator is distinguished by KIND (and by Order 0), not by being the first or "
            "the only member. With a single child, a resolver that guessed would have a 50% chance of "
            "reporting the child as the parent and the parent as a child, at which point the parent's "
            "own status would gate retirement on itself",
        ),
        (
            "children written OUT of order",
            [
                ("ccc333", 3, "executed", "executed"),
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            None,
            "orc000",
            ["aaa111", "bbb222", "ccc333"],
            4,
            "children come back sorted by ORDER regardless of the sequence they were written in, "
            "which is what lets a caller name the first unfinished child meaningfully rather than "
            "naming whichever file the filesystem happened to list first",
        ),
        (
            "an EMPTY selector",
            [("aaa111", 1, "executed", "executed")],
            "",
            None,
            [],
            0,
            "AN UNRESOLVABLE SELECTOR RETURNS AN EMPTY MEMBERSHIP RATHER THAN RAISING. The caller's "
            "next step is a refusal decision, and an exception here would abort a whole run over one "
            "bad selector instead of refusing one item",
        ),
        (
            "a WHITESPACE selector",
            [("aaa111", 1, "executed", "executed")],
            "   ",
            None,
            [],
            0,
            "whitespace is not a setid, and it is what an empty CLI argument most often becomes",
        ),
        (
            "an UNKNOWN selector",
            [("aaa111", 1, "executed", "executed")],
            "nosuchset",
            None,
            [],
            0,
            "a mistyped setid resolves to nothing rather than to the Set that happens to exist, which "
            "is what keeps a typo from retiring a real orchestrator",
        ),
        (
            "an id6-SHAPED Set name that collides with nothing",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            "zzz999",
            "orc000",
            ["aaa111", "bbb222"],
            3,
            "`selectors.resolve` ranks `id6` ABOVE `setid`, and this repo HAS 6-char Set names "
            "(`awhelp`, `clianx`, `detrun`, `agyrun`, `ackme8`, `ocsync`, `awuiux`, `rstodo`, "
            "measured), so an unpinned resolve could match a PLAN whose `Id` equals the setid and "
            "return ONE file where the Set has six. This row pins that a 6-char Set name still "
            "resolves normally when nothing collides",
        ),
    )

    def test_every_selector_yields_its_exact_membership(self):
        wrong = []
        for (
            case,
            children,
            selector,
            orchestrator,
            child_ids,
            members,
            why,
        ) in self.MEMBERSHIPS:
            repo = _Repo()
            self.addCleanup(repo.close)
            setid = "zzz999" if selector == "zzz999" else "probe"
            for id6, order, status, bucket in children:
                _write_plan(
                    repo.root,
                    bucket,
                    plan_id=id6,
                    set_id=setid,
                    order=order,
                    status=status,
                )
            _write_plan(
                repo.root,
                "pending",
                plan_id="orc000",
                set_id=setid,
                order=0,
                status="approved",
                kind="orchestrator",
                body=_table(
                    ["Order", "Id", "Child", "Depends on"],
                    [[f"{o:02d}", "x", "x", "x"] for _i, o, _s, _b in children],
                ),
            )
            m = rs.read_set_membership(
                repo.root, setid if selector is None else selector
            )
            problems = []
            got_orchestrator = (
                m.orchestrator.id6 if m.orchestrator is not None else None
            )
            if got_orchestrator != orchestrator:
                problems.append(
                    f"the orchestrator is {got_orchestrator!r}, expected {orchestrator!r}"
                )
            if m.orchestrator is not None:
                if not m.orchestrator.is_orchestrator:
                    problems.append(
                        "the member returned as the orchestrator does not report "
                        "`is_orchestrator`, so the two ways of asking disagree"
                    )
                if m.orchestrator.kind != "orchestrator":
                    problems.append(
                        f"its kind is {m.orchestrator.kind!r}, not 'orchestrator'"
                    )
            if [c.id6 for c in m.children] != child_ids:
                problems.append(
                    f"children are {[c.id6 for c in m.children]!r} IN THIS ORDER, expected "
                    f"{child_ids!r}"
                )
            if [c.order for c in m.children] != sorted(c.order for c in m.children):
                problems.append(
                    f"children are not sorted by Order: {[c.order for c in m.children]!r}"
                )
            if len(m.members) != members:
                problems.append(
                    f"the member count is {len(m.members)}, expected {members} (children plus the "
                    "orchestrator)"
                )
            expected_statuses = {
                status for id6, _o, status, _b in children if id6 in child_ids
            }
            got_statuses = {c.status for c in m.children}
            if child_ids and got_statuses != expected_statuses:
                problems.append(
                    f"child statuses are {got_statuses!r}, expected {expected_statuses!r}"
                )
            if (repo.root / ".aw" / "records" / "runs").exists():
                problems.append(
                    "fixture sanity: this repo must contain NO run state, or the cross-run claim is "
                    "not being measured"
                )
            if problems:
                wrong.append(
                    f"  {case} (selector {selector!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"membership was wrong for {len(wrong)} of {len(self.MEMBERSHIPS)} selectors. ONE tree "
            "walk answers all of them, so read the grouping. If the RESOLVED rows fail while the "
            "empty/unknown rows pass, the walk is finding fewer members than exist, and the severe "
            "version of that is a Set looking COMPLETE because the unfinished children were not seen "
            "at all: this is the queue-scoped defect the predicate was written to replace. If the "
            "ORCHESTRATOR cell is wrong on the single-child row, identification fell back to "
            "counting or to position. If the empty/unknown rows RAISE instead of returning nothing, "
            "one mistyped setid will abort a whole run rather than refusing one item. FIX: the member "
            f"count is children PLUS the orchestrator, so it is one more than the child list.\n"
            + "\n".join(wrong),
        )

    def test_a_legacy_order_zero_plan_with_no_kind_bullet_is_still_the_orchestrator(
        self,
    ):
        """Kept separate: constructs `SetMember` records DIRECTLY, with no repository at all.

        74 plans in this repo carry `Order: 0` and NO `Kind:` bullet (measured). Reading `Kind` alone
        would count those as children, making an old Set look permanently one-child-short, so the
        `Order == 0` fallback keeps them recognized. Not a row in the table above, because the claim
        is about the RECORD TYPE's `is_orchestrator` property on a hand-built member, which no
        on-disk fixture can express: writing a plan file with no `Kind:` bullet would test the parser
        as well, and the point here is the fallback rule in isolation.
        """

        member = rs.SetMember(
            id6="old001", order=0, kind="", status="executed", path=Path("x")
        )
        self.assertTrue(member.is_orchestrator)
        child = rs.SetMember(
            id6="old002", order=2, kind="", status="executed", path=Path("x")
        )
        self.assertFalse(child.is_orchestrator)

    def test_children_are_returned_in_order(self):
        self.make_set(
            "sorted",
            [
                ("ccc333", 3, "executed", "executed"),
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
        )
        m = rs.read_set_membership(self.root, "sorted")
        self.assertEqual([c.order for c in m.children], [1, 2, 3])

    def test_an_empty_or_unknown_selector_yields_no_members_rather_than_raising(self):
        for token in ("", "   ", "nosuchset"):
            with self.subTest(token=token):
                m = rs.read_set_membership(self.root, token)
                self.assertIsNone(m.orchestrator)
                self.assertEqual(m.children, ())

    def test_an_id6_shaped_setid_resolves_by_set_when_nothing_collides(self):
        """`selectors.resolve` ranks `id6` ABOVE `setid`, and this repo HAS id6-shaped setids.

        `awhelp`, `clianx`, `detrun`, `agyrun`, `ackme8`, `ocsync`, `awuiux` and `rstodo` are all
        6-char Set names (measured), so an unpinned resolve could match a PLAN whose `Id` equals the
        setid and return one file where the Set has six. Pinning to the `setid` kind is what prevents
        that, and a 6-char Set name must still resolve normally.
        """

        self.make_set(
            "zzz999",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
        )
        m = rs.read_set_membership(self.root, "zzz999")
        self.assertEqual([c.id6 for c in m.children], ["aaa111", "bbb222"])
        self.assertEqual(m.resolution_note, "")

    def test_a_setid_colliding_with_another_plans_id6_refuses_and_SAYS_WHY(self):
        """Kept separate: needs a COLLIDING plan outside the Set, and asserts through TWO functions.

        The pin's one honest cost, asserted rather than left to be discovered.

        When a setid collides with some other plan's `Id`, the pinned resolve rejects the `id6` match
        and returns NOTHING. That is the safe direction (an unresolvable Set is never retired), but a
        bare "no orchestrator" would misdescribe a Set sitting plainly on disk, so the refusal must
        carry the real reason. No live Set collides today; this is a guard.
        """

        _write_plan(
            self.root,
            "executed",
            plan_id="zzz999",
            set_id="other",
            order=1,
            status="executed",
        )
        self.make_set(
            "zzz999",
            [("aaa111", 1, "executed", "executed")],
        )
        m = rs.read_set_membership(self.root, "zzz999")
        self.assertEqual(m.children, ())
        self.assertIn("not as a Set name", m.resolution_note)
        d = rs.evaluate_set_retirement(self.root, "zzz999")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_NO_ORCHESTRATOR)
        self.assertIn("not as a Set name", d.detail)

    def test_every_id6_shaped_setid_in_this_repo_still_resolves_by_set(self):
        """Kept separate: sweeps the REAL repository's Set names, so it has no fixture and no rows.

        Pins the "no live Set collides today" claim the guard above makes. It is a CORPUS check, so
        it would fail the moment a real Set name collided with a real plan's id6, which is exactly
        when the guard stops being hypothetical.
        """

        for setid in (
            "awhelp",
            "clianx",
            "rstodo",
            "agyrun",
            "ackme8",
            "ocsync",
            "awuiux",
            "detrun",
        ):
            with self.subTest(setid=setid):
                m = rs.read_set_membership(REPO_ROOT, setid)
                self.assertEqual(m.resolution_note, "")
                self.assertTrue(m.members, f"{setid} resolved to nothing")


# ==================================================================================================
# V-02: one TYPED reason per refusal cause, and an allowlist rather than a denylist
# ==================================================================================================


class TypedRefusalReasons(SyntheticSetCase):
    """RETIREMENT IS A SAFETY GATE, so EVERY refusal cause keeps its OWN ROW and its OWN reason.

    ONE table replaces sixteen tests across four classes (`TypedRefusalReasons`,
    `ExecutedIsAnAllowlist`, `RealColumnShapeFixtures`, `ParserFailsClosed`). Every one built a
    synthetic Set on disk, called `evaluate_set_retirement`, and asserted the eligibility plus one
    typed reason; they differed only in the Set.

    THE REASON IS NEVER "IT REFUSED". That is the whole point of this table and the reason it is
    stricter than the tests it replaces rather than looser. Each row names the EXACT
    `RETIRE_REFUSED_*` reason, and the failure message says which one it got instead, because the
    defect this predicate was written to fix (`5e4sb6`) was precisely a refusal that could not say
    WHY: the old shape returned `(False, [])` for both "children are unfinished" and "there are no
    children", so a durable event read "dependency-blocked (unmet dependencies)" while naming no
    dependency at all. A table that asserted only `eligible is False` would pass on that defect, so
    every row additionally asserts the `unfinished` map and the `unauthored_rows` tuple, including
    asserting they are EMPTY where the cause is something else. A reason that starts firing for the
    wrong cause therefore fails on TWO cells, not one.

    ALL FIVE OUTCOMES ARE REPRESENTED, and the runner's four documented refusals each have at least
    one row of their own: `unfinished-children`, `no-children`, `unauthored-child-rows`,
    `no-orchestrator`, plus `eligible`. The fifth refusal the runner performs, a REFUSING TRANSITION,
    is not reachable from this predicate at all (it decides, it does not transition) and is pinned
    separately by `TheFourRefusalReasonsAreDistinguishable`, which drives the dispatcher.

    THE POSITIVE ROWS ARE IN THE SAME TABLE AND THEY CARRY UNUSUAL WEIGHT HERE. A predicate that
    refused everything would satisfy every refusal row while making retirement impossible; but the
    dangerous direction is the opposite one, so the eligible rows are also where a FALSE ELIGIBILITY
    would show up. Their failure message says which way the gate broke, because a false refusal
    merely leaves an orchestrator in `pending/` (today's status quo) while a false eligibility
    asserts a completion that never happened.

    THE COLUMN LAYOUT IS A COLUMN, copied from the five real orchestrators rather than invented. The
    layouts share ONLY the first column and `rununify` has NO `Id` column at all, so a parser
    validated on this plan's own table format is validated on the one shape that was never going to
    break. Keeping the shapes as rows in the same table as the status cases is what shows that a
    parse failure and an unfinished child are DIFFERENT refusals rather than one generic one.

    `executed` IS AN ALLOWLIST, which is why the non-executed statuses are rows rather than a
    denylist assertion: a status nobody has invented yet is refused BY CONSTRUCTION. A denylist would
    silently admit any status added to the vocabulary later, which is how a conservative gate stops
    gating without anyone editing it.
    """

    #: Column layouts COPIED from the five live orchestrators (measured), because they disagree:
    #:     orchretire  | Order | Id | Child | Depends on |
    #:     wslayout    | Order | Id | What it does | Set dependencies |
    #:     runprofile  | Order | Id | Child | Responsibility | Depends on |
    #:     lanectn     | Order | Id | Depth | Requirements owned | Prerequisite | What it delivers |
    #:     rununify    | Order | What it does | Depends on |            <- NO `Id` COLUMN
    ORCHRETIRE_HEADER = ["Order", "Id", "Child", "Depends on"]
    WSLAYOUT_HEADER = ["Order", "Id", "What it does", "Set dependencies"]
    RUNPROFILE_HEADER = ["Order", "Id", "Child", "Responsibility", "Depends on"]
    LANECTN_HEADER = [
        "Order",
        "Id",
        "Depth",
        "Requirements owned",
        "Prerequisite",
        "What it delivers",
    ]
    RUNUNIFY_HEADER = ["Order", "What it does", "Depends on"]

    #: The statuses that are NOT `executed`. Includes casing variants, near-misses, and a status
    #: nobody has invented, which is what makes this an ALLOWLIST test rather than a denylist one.
    NON_EXECUTED = (
        "substantially-complete",
        "approved",
        "reviewed",
        "to-review",
        "draft",
        "blocked",
        "dependency-blocked",
        "merge-needs-human",
        "merge-refused",
        "partial",
        "superseded",
        "not-executed",
        "executing",
        "Executed",
        "EXECUTED",
        "executed-ish",
        "some-status-nobody-has-invented-yet",
    )

    #: (case, children as (id6, order, status, bucket), the header layout, the declared row tokens
    #:  (None = derive from the children), an explicit orchestrator BODY (None = build the table),
    #:  whether to write an orchestrator at all, expected eligibility, the EXACT expected reason,
    #:  the expected `unfinished` map, the expected `unauthored_rows`, a detail substring, why)
    #:
    #: THE REASONS ARE `rs.RETIRE_*` CONSTANTS HERE, deliberately, and this is the opposite choice
    #: from the literal `IPD-*` codes in `test_ipd_lint.py`. These strings are NOT a published
    #: interface: they are consumed inside this repository by the dispatcher and written into run
    #: records, and `TypedRefusalReasons.test_the_five_outcomes_are_all_distinct` below pins that the
    #: constants are five DISTINCT values. What must never happen is two causes COLLAPSING onto one
    #: reason, and referencing the constants catches that while a renaming (which breaks nothing
    #: outside the repo) does not need to fail here.
    DECISIONS = (
        (
            "every child executed, this plan's own column layout",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            ORCHRETIRE_HEADER,
            None,
            None,
            True,
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            None,
            "THE POSITIVE ROW, and the one the whole mechanism exists to reach. Every refusal row "
            "below is vacuous while this is broken, because a predicate that refused everything "
            "would satisfy all of them and make retirement impossible",
        ),
        (
            "every child executed, the `wslayout` five-row layout",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
                ("ddd444", 4, "executed", "executed"),
                ("eee555", 5, "executed", "executed"),
            ],
            WSLAYOUT_HEADER,
            None,
            None,
            True,
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            None,
            "a SECOND positive row on a DIFFERENT real layout, so eligibility is not an accident of "
            "one column arrangement. `wslayout` is the shape where all five declared rows resolve",
        ),
        (
            "every child executed, the `lanectn` six-column layout with a `Depth` column",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            LANECTN_HEADER,
            None,
            None,
            True,
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            None,
            "the widest real layout. An extra column between `Id` and the description must not shift "
            "what the parser reads as the Order token",
        ),
        (
            "SIX children on disk against FIVE declared rows (`runprofile`)",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
                ("ddd444", 4, "executed", "executed"),
                ("eee555", 5, "executed", "executed"),
                ("fff666", 6, "executed", "executed"),
            ],
            RUNPROFILE_HEADER,
            ["01", "02", "03", "04", "05"],
            None,
            True,
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            None,
            "F-7: THE COMPARISON IS ONE-DIRECTIONAL. A symmetric 'table and disk must match' rule "
            "would refuse a legitimately EXTENDED Set forever, and `runprofile` really is in this "
            "shape. An UNDECLARED child is not the unauthored-rows rule's business; its STATUS is "
            "the executed rule's business, which the row below pins",
        ),
        (
            "an UNDECLARED extra child that is NOT executed",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("fff666", 6, "reviewed", "pending"),
            ],
            RUNPROFILE_HEADER,
            ["01", "02"],
            None,
            True,
            False,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            {"fff666": "reviewed"},
            (),
            None,
            "the companion to the row above, and together they are the whole rule: an extra child "
            "does not refuse for being UNDECLARED, but it is still gated on being EXECUTED. Without "
            "this pair, 'one-directional' could be implemented as 'ignore undeclared children "
            "entirely', which would retire a parent over an unfinished child",
        ),
        (
            "one child approved and one reviewed",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
                ("ccc333", 3, "reviewed", "pending"),
            ],
            ORCHRETIRE_HEADER,
            None,
            None,
            True,
            False,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            {"bbb222": "approved", "ccc333": "reviewed"},
            (),
            None,
            "REFUSAL REASON 1 OF 4, and R-9: a refusal that cannot NAME what it is waiting for is "
            "the `5e4sb6` defect. The `unfinished` map must carry the id AND the actual status of "
            "every waiting child, and the EXECUTED child must NOT appear in it",
        ),
        (
            "a child with NO `- Status:` bullet at all",
            [("aaa111", 1, "", "pending")],
            ORCHRETIRE_HEADER,
            ["01"],
            None,
            True,
            False,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            {"aaa111": "<no Status:>"},
            (),
            None,
            "AN ABSENT STATUS IS NOT DONE. Read as complete it would be the worst possible default, "
            "because a malformed plan file would retire its parent; the allowlist makes absence "
            "refuse by construction. MEASURED WHILE WRITING THIS TABLE: the missing status is "
            "reported as the SENTINEL `<no Status:>` rather than as an empty string, which is the "
            "better behavior and is pinned here rather than loosened, because a refusal reading "
            '"bbb222 ()" would not tell a human the bullet is absent as opposed to blank',
        ),
        (
            "a Set with NO children",
            [],
            ORCHRETIRE_HEADER,
            [],
            None,
            True,
            False,
            rs.RETIRE_REFUSED_NO_CHILDREN,
            {},
            (),
            "no child plans",
            "REFUSAL REASON 2 OF 4, AND THE MEASURED DEFECT ITSELF. This is the case that produced "
            "`(False, [])` and a durable event naming no dependency at all. It must be its OWN "
            "reason, distinct from unfinished-children, and its `unfinished` map must be EMPTY: an "
            "empty list dressed up as an unmet dependency is exactly what `5e4sb6` recorded",
        ),
        (
            "a Set with children but NO Order-0 orchestrator",
            [("aaa111", 1, "executed", "executed")],
            ORCHRETIRE_HEADER,
            None,
            None,
            False,
            False,
            rs.RETIRE_REFUSED_NO_ORCHESTRATOR,
            {},
            (),
            "no Order-0 orchestrator",
            "REFUSAL REASON 3 OF 4: there is nothing to retire. Distinct from no-children because "
            "the remedy is opposite (author a parent, versus author children), and a caller that "
            "confused them would tell a human to do the wrong thing",
        ),
        (
            "a declared row resolving to NO plan on disk",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            ORCHRETIRE_HEADER,
            ["01", "02", "03"],
            None,
            True,
            False,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            {},
            ("03",),
            None,
            "REFUSAL REASON 4 OF 4, and THE 2.5 CASE: every child that EXISTS is executed, so a "
            "naive rule would retire the parent. The declared row `03` was never authored, so the "
            "work it names has not been done and the token must be carried verbatim for a human to "
            "act on",
        ),
        (
            "the `rununify` Id-less layout with the real tokens `03+` and `last`",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            RUNUNIFY_HEADER,
            ["01", "02", "03+", "last"],
            None,
            True,
            False,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            {},
            ("03+", "last"),
            None,
            "THE REAL `5e4sb6` SHAPE: three columns, NO `Id` column, and two non-numeric tokens that "
            "stood unauthored by deliberate design for two weeks. A parser keyed on a named `Id` "
            "header crashes or vacuously PASSES here, and a vacuous pass retires the parent",
        ),
        (
            "a Child IPDs section containing PROSE and no table",
            [("aaa111", 1, "executed", "executed")],
            ORCHRETIRE_HEADER,
            None,
            f"## {rs._CHILD_IPDS_HEADING}\n\nThe child breakdown is DELIBERATELY NOT FIXED HERE.\n",
            True,
            False,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            {},
            (),
            "no rows could be parsed",
            "THE PARSER FAILS CLOSED. An unparseable section is never read as 'fully authored', and "
            "the detail says the rows could not be PARSED rather than that a row was unauthored, so "
            "a human is sent to the table rather than to a missing child",
        ),
        (
            "NO Child IPDs section at all",
            [("aaa111", 1, "executed", "executed")],
            ORCHRETIRE_HEADER,
            None,
            "## Goal\n\nx\n",
            True,
            False,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            {},
            (),
            "no rows could be parsed",
            "a missing section is the same fail-closed outcome as an unparseable one: absence of a "
            "declaration is not a declaration that there is nothing to declare",
        ),
    )

    def test_every_cause_yields_its_OWN_typed_reason_with_its_OWN_specifics(self):
        wrong = []
        for (
            case,
            children,
            header,
            declared,
            body,
            with_orchestrator,
            eligible,
            reason,
            unfinished,
            unauthored,
            detail_substring,
            why,
        ) in self.DECISIONS:
            # A fresh repo per row: `make_set` writes into `self.root`, so rows must not share one.
            repo = _Repo()
            self.addCleanup(repo.close)
            setid = "probe"
            for id6, order, status, bucket in children:
                _write_plan(
                    repo.root,
                    bucket,
                    plan_id=id6,
                    set_id=setid,
                    order=order,
                    status=status,
                )
            if with_orchestrator:
                orchestrator_body = body
                if orchestrator_body is None:
                    tokens = (
                        declared
                        if declared is not None
                        else [f"{order:02d}" for _i, order, _s, _b in children]
                    )
                    orchestrator_body = _table(
                        header, [[t] + ["x"] * (len(header) - 1) for t in tokens]
                    )
                _write_plan(
                    repo.root,
                    "pending",
                    plan_id="orc000",
                    set_id=setid,
                    order=0,
                    status="approved",
                    kind="orchestrator",
                    body=orchestrator_body,
                )
            d = rs.evaluate_set_retirement(repo.root, setid)
            problems = []
            if d.eligible is not eligible:
                problems.append(
                    f"eligible is {d.eligible!r}, expected {eligible!r}"
                    + (
                        "  <-- A FALSE ELIGIBILITY ASSERTS A COMPLETION THAT NEVER HAPPENED"
                        if d.eligible
                        else ""
                    )
                )
            if d.reason != reason:
                problems.append(
                    f"reason is {d.reason!r}, expected {reason!r}; a refusal that reports the WRONG "
                    "cause sends a human to fix the wrong thing"
                )
            if dict(d.unfinished) != unfinished:
                problems.append(
                    f"unfinished is {dict(d.unfinished)!r}, expected {unfinished!r}"
                )
            if tuple(d.unauthored_rows) != unauthored:
                problems.append(
                    f"unauthored_rows is {tuple(d.unauthored_rows)!r}, expected {unauthored!r}"
                )
            if not d.detail.strip():
                problems.append(
                    "the detail is EMPTY, so a caller would have to invent the sentence it writes "
                    "into the durable record"
                )
            elif detail_substring is not None and detail_substring not in d.detail:
                problems.append(
                    f"the detail must contain {detail_substring!r}; it said {d.detail!r}"
                )
            # Every unfinished child must be NAMED in the detail with its status, and no FINISHED
            # child may be, which is the `5e4sb6` requirement stated positively and negatively.
            for child, status in unfinished.items():
                if child not in d.detail:
                    problems.append(
                        f"the detail does not name the waiting child {child!r}: {d.detail!r}"
                    )
                elif status and status not in d.detail:
                    problems.append(
                        f"the detail names {child!r} but not its status {status!r}: {d.detail!r}"
                    )
            # ONLY ON A REFUSAL. An ELIGIBLE detail legitimately ENUMERATES the executed children
            # ("all N child(ren) are executed (aaa111, bbb222)"), which is the evidence for the
            # verdict rather than a misdescription; measured while writing this table.
            if not eligible:
                for id6, _order, status, _bucket in children:
                    if status == "executed" and id6 in d.detail:
                        problems.append(
                            f"the detail names {id6!r}, which IS executed, so the refusal "
                            f"misdescribes what it is waiting for: {d.detail!r}"
                        )
            for token in unauthored:
                if token not in d.detail:
                    problems.append(
                        f"the detail does not carry the unauthored token {token!r} verbatim, so a "
                        f"human cannot find the row to author: {d.detail!r}"
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
            f"the retirement decision was wrong for {len(wrong)} of {len(self.DECISIONS)} Sets. THIS "
            "IS A SAFETY GATE, so the DIRECTION of the failure decides how bad it is and the two are "
            "not comparable. A row that should REFUSE and is now ELIGIBLE asserts a completion that "
            "never happened: the runner will retire an orchestrator whose work is unfinished or whose "
            "child table declares rows nobody authored, and the plan lands in `executed/` claiming "
            "work no agent performed. A row that should be ELIGIBLE and now refuses merely leaves the "
            "parent in `pending/`, which is the pre-fix status quo and costs a human one command. "
            "READ THE REASON CELLS NEXT: if two DIFFERENT causes now report the SAME reason, the "
            "predicate has collapsed them, which is precisely the `5e4sb6` defect where a "
            "no-children Set produced `(False, [])` and a run summary claimed an unmet dependency it "
            "could not name. If the reasons are right but the `unfinished`/`unauthored_rows` cells or "
            "the detail are wrong, the gate still gates but its record cannot substantiate the "
            "refusal, so a human is told to wait without being told for what. FIX: the eligible rows "
            f"differ only in COLUMN LAYOUT, all copied from live orchestrators; if only those fail "
            f"together the child-table PARSER broke, not the status rule.\n"
            + "\n".join(wrong),
        )

    def test_only_the_exact_token_executed_qualifies(self):
        """The ALLOWLIST, swept over every status that is NOT `executed`.

        Kept as its own test rather than seventeen rows in the table above, for a reason that is the
        point of the test: it iterates a LIST OF STATUSES against ONE fixed Set shape, so the
        assertion is that the token comparison is EXACT rather than that a particular Set refuses.
        Folding these into `DECISIONS` would add seventeen near-identical rows whose eligible/reason/
        unfinished cells are all the same, which would bury the thirteen rows that each encode a
        different rule.

        ASSERTED AS AN ALLOWLIST rather than as a denylist of known-bad values, because a denylist
        silently admits any status added to the vocabulary later, which is how a conservative gate
        stops gating without anyone editing it. The casing variants (`Executed`, `EXECUTED`) and the
        near-miss (`executed-ish`) are what make "exact token" mean exact, and
        `some-status-nobody-has-invented-yet` is the row that stands in for the future.

        `substantially-complete` IS IN THIS LIST AND IS HONESTLY LABELLED: it means finalize REFUSED
        (`i452hf`), so it is not done. It is a RUN-STATE disposition rather than a plan-file
        `- Status:`, so this predicate will not meet it from its own input; the guard defends against
        the value arriving from ANOTHER caller, and this test proves the guard, NOT that real plan
        data contains the value.
        """

        wrong = []
        for status in self.NON_EXECUTED:
            repo = _Repo()
            self.addCleanup(repo.close)
            _write_plan(
                repo.root,
                "pending",
                plan_id="aaa111",
                set_id="allow",
                order=1,
                status=status,
            )
            _write_plan(
                repo.root,
                "pending",
                plan_id="orc000",
                set_id="allow",
                order=0,
                status="approved",
                kind="orchestrator",
                body=_table(self.ORCHRETIRE_HEADER, [["01", "x", "x", "x"]]),
            )
            d = rs.evaluate_set_retirement(repo.root, "allow")
            problems = []
            if d.eligible:
                problems.append(
                    "QUALIFIED AS EXECUTED, so this status would retire an orchestrator"
                )
            if d.reason != rs.RETIRE_REFUSED_UNFINISHED_CHILDREN:
                problems.append(
                    f"reason is {d.reason!r}, expected "
                    f"{rs.RETIRE_REFUSED_UNFINISHED_CHILDREN!r}"
                )
            if dict(d.unfinished) != {"aaa111": status}:
                problems.append(
                    f"unfinished is {dict(d.unfinished)!r}, expected {{'aaa111': {status!r}}}; the "
                    "refusal must carry the ACTUAL status so a human sees what the child is waiting "
                    "on"
                )
            if status not in d.detail:
                problems.append(f"the detail does not name the status: {d.detail!r}")
            if problems:
                wrong.append(
                    f"  status {status!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NON_EXECUTED)} non-executed statuses were mishandled. ONE "
            "exact-token comparison against `rs.SET_RETIREMENT_DONE_STATUS` decides all of them. FIX: "
            "if a status QUALIFIED, the comparison stopped being exact and the gate now retires "
            "orchestrators over unfinished children, which is the severe direction. Note WHICH "
            "statuses leaked: the CASING variants leaking means the comparison was case-folded; "
            "`executed-ish` leaking means it became a prefix or substring match; and "
            "`some-status-nobody-has-invented-yet` leaking means the check was turned into a DENYLIST "
            "of known-bad values, which silently admits every status added to the vocabulary after "
            f"this file was written.\n" + "\n".join(wrong),
        )

    def test_the_five_outcomes_are_all_distinct(self):
        """Kept separate: asserts the CONSTANTS are five distinct strings, before any Set exists.

        This is what makes the reason cells in `DECISIONS` meaningful: if two of these constants were
        ever given the same value, every row asserting one of them would still pass while the two
        causes had become indistinguishable to the dispatcher and to the run record. That is the
        `5e4sb6` collapse expressed at the vocabulary level rather than in the predicate.
        """

        outcomes = {
            rs.RETIRE_ELIGIBLE,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            rs.RETIRE_REFUSED_NO_CHILDREN,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            rs.RETIRE_REFUSED_NO_ORCHESTRATOR,
        }
        self.assertEqual(
            len(outcomes),
            5,
            f"two retirement outcomes share one string, so the causes they distinguish have "
            f"collapsed: {sorted(outcomes)}",
        )

    def test_every_decision_carries_a_nonempty_detail(self):
        """Kept separate: sweeps Sets INCLUDING one that does not exist, which no row can express.

        A caller must never have to invent the sentence it writes into the durable record. The
        `nosuch` selector is the reason this is not folded into the table: it names a Set with no
        plans at all, so there is no fixture to describe in a row's children column, and it is the
        case a caller reaches when a human mistypes a setid.
        """

        self.make_set("d1", [("aaa111", 1, "executed", "executed")])
        self.make_set("d2", [("bbb222", 1, "approved", "pending")])
        self.make_set("d3", [], declared_rows=[])
        for setid in ("d1", "d2", "d3", "nosuch"):
            with self.subTest(setid=setid):
                self.assertTrue(rs.evaluate_set_retirement(self.root, setid).detail)

    def test_the_real_nna8yz_plan_file_carries_a_real_plan_status(self):
        """Kept separate: reads the REAL repository, so it has no fixture and no rows.

        Pins the F-5 measurement, so the `substantially-complete` docstring on
        `test_only_the_exact_token_executed_qualifies` cannot rot into a false claim. THE INVARIANT IS
        THE SECOND ASSERT: what must not become true is that `substantially-complete` reaches this
        predicate from real plan data, since that value lives only in a run's `state.json`. The plan's
        own status legitimately ADVANCES over time (measured 2026-09-08: `nna8yz` moved `approved` ->
        `executed`), so pinning one specific value would assert the repository's transient state
        rather than the guard.
        """

        m = rs.read_set_membership(REPO_ROOT, "lanectn")
        by_id = {c.id6: c.status for c in m.children}
        self.assertIn(
            by_id.get("nna8yz"),
            {"approved", "executed"},
            "nna8yz must carry a real plan-file status, not a run-scoped disposition",
        )
        self.assertNotIn("substantially-complete", set(by_id.values()))


class ChildTableParserTests(SyntheticSetCase):
    """What the child-table parser reads as a declared row, and what it must SKIP.

    ONE table replaces five tests (`RealColumnShapeFixtures.test_the_rununify_table_parses_without_an_id_column`,
    `ParserFailsClosed`'s header/alignment, right-aligned-separator, decorated-token and
    other-section cases). Each built an orchestrator body and asserted the token tuple that
    `parse_declared_child_orders` returned, or that it refused.

    SEPARATE FROM `TypedRefusalReasons` ON PURPOSE, because the subject is different: that table
    asserts the DECISION over a whole Set, and this asserts the PARSE, i.e. the exact tuple of tokens
    read out of one document. The distinction matters because a parse that silently returns NOTHING
    is the vacuous-pass risk: `parsed=False` must be the fail-closed signal, and a table of
    eligibility verdicts cannot tell "parsed nothing" apart from "parsed correctly and found nothing
    wrong".

    EVERY ROW ASSERTS THE EXACT TOKEN TUPLE, which is stronger than the tests it replaces. Three of
    them asserted only `assertTrue(parsed)` plus an eligibility verdict, so a parser that read the
    ALIGNMENT row as a child, or read a table from a DIFFERENT section, could still produce an
    eligible Set and pass. Naming the tuple is what makes the skip rules assertable.
    """

    #: (case, the orchestrator body, the expected token tuple, whether the parse must SUCCEED, why)
    PARSES = (
        (
            "this plan's own four-column layout",
            _table(
                ["Order", "Id", "Child", "Depends on"],
                [["01", "`aaa111`", "x", "none"]],
            ),
            ("01",),
            True,
            "the base case. The `Id` cell holds a BACKTICKED id6, as every real orchestrator writes "
            "it, so the parser is reading the Order column and not stumbling on the decoration",
        ),
        (
            "the `rununify` three-column layout with NO `Id` column",
            _table(["Order", "What it does", "Depends on"], [["01", "x", "none"]]),
            ("01",),
            True,
            "THE SHAPE THAT WAS NEVER GOING TO WORK BY ACCIDENT. A parser keyed on a named `Id` "
            "header crashes here or returns nothing, and returning nothing is a VACUOUS PASS "
            "upstream: the Set would look fully authored and the parent would be retired",
        ),
        (
            "a RIGHT-ALIGNED separator row (`|---:|`)",
            "\n".join(
                [
                    f"## {rs._CHILD_IPDS_HEADING}",
                    "",
                    "| Order | Id | What it does | Set dependencies |",
                    "|---:|---|---|---|",
                    "| 01 | `aaa111` | x | none |",
                    "",
                ]
            ),
            ("01",),
            True,
            "`wslayout` and `runprofile` both write alignment rows in this form. The separator must "
            "be SKIPPED rather than read as a declared child: read as one, `---:` becomes an "
            "unauthored row and the parent is refused forever for a formatting choice",
        ),
        (
            "DECORATED order tokens (backticked and bolded)",
            "\n".join(
                [
                    f"## {rs._CHILD_IPDS_HEADING}",
                    "",
                    "| Order | What it does | Depends on |",
                    "|---|---|---|",
                    "| `01` | x | none |",
                    "| **02** | x | 01 |",
                    "",
                ]
            ),
            ("01", "02"),
            True,
            "`rununify` writes `| 01 | **AUTHORED ...** |`, so real tables carry markdown emphasis on "
            "the Order cell. The token must be read THROUGH the decoration, and note the expected "
            "tuple is the BARE tokens: a parser that returned '`01`' with backticks would then fail "
            "to match the child on disk and report it unauthored",
        ),
        (
            "a table in ANOTHER section, before the Child IPDs section",
            "\n".join(
                [
                    "## Findings",
                    "",
                    "| # | Sev | Where |",
                    "|---|---|---|",
                    "| 99 | HIGH | somewhere |",
                    "",
                    f"## {rs._CHILD_IPDS_HEADING}",
                    "",
                    "| Order | Id | Child | Depends on |",
                    "|---|---|---|---|",
                    "| 01 | `aaa111` | x | none |",
                    "",
                ]
            ),
            ("01",),
            True,
            "THE SECTION FENCE, and the exact-tuple assertion is what pins it. A Findings table's "
            "first column holds a FINDING NUMBER (`99` here), so a parser that read the whole "
            "document would declare a child at Order 99 that no plan can ever satisfy, and the Set "
            "would be refused permanently for a row nobody wrote",
        ),
        (
            "a Child IPDs section holding PROSE and no table",
            f"## {rs._CHILD_IPDS_HEADING}\n\nThe child breakdown is DELIBERATELY NOT FIXED HERE.\n",
            (),
            False,
            "FAIL CLOSED: `parsed` must be FALSE, not an empty success. The distinction is the whole "
            "reason this test asserts the flag separately, because an empty tuple with `parsed=True` "
            "reads as 'a fully authored table declaring no children', which retires the parent",
        ),
        (
            "no Child IPDs section at all",
            "## Goal\n\nx\n",
            (),
            False,
            "the same fail-closed signal for a missing section, so absence and unparseability are "
            "not distinguished into one working and one broken path",
        ),
    )

    def test_every_table_shape_parses_to_its_exact_declared_tokens(self):
        wrong = []
        for case, body, tokens, parsed_ok, why in self.PARSES:
            repo = _Repo()
            self.addCleanup(repo.close)
            _write_plan(
                repo.root,
                "executed",
                plan_id="aaa111",
                set_id="parse",
                order=1,
                status="executed",
            )
            orch = _write_plan(
                repo.root,
                "pending",
                plan_id="orc000",
                set_id="parse",
                order=0,
                status="approved",
                kind="orchestrator",
                body=body,
            )
            got_tokens, got_parsed = rs.parse_declared_child_orders(
                orch.read_text(encoding="utf-8")
            )
            problems = []
            if bool(got_parsed) is not parsed_ok:
                problems.append(
                    f"parsed is {got_parsed!r}, expected {parsed_ok!r}"
                    + (
                        "  <-- an empty-but-SUCCESSFUL parse reads as a fully authored table "
                        "declaring no children, which retires the parent"
                        if got_parsed
                        else ""
                    )
                )
            if tuple(got_tokens) != tokens:
                problems.append(
                    f"tokens are {tuple(got_tokens)!r}, expected {tokens!r}"
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
            f"the child-table parser was wrong for {len(wrong)} of {len(self.PARSES)} table shapes. "
            "ONE row-scanning loop reads all of them. FIX: the two directions are not equally bad. "
            "EXTRA tokens (an alignment row, a Findings row, a decorated token kept verbatim) refuse "
            "the parent FOREVER for a row nobody wrote, which is annoying but safe. MISSING tokens, "
            "or a `parsed=True` on an unparseable section, are the severe direction: the Set then "
            "looks fully authored and the orchestrator is retired while declared work is "
            "unaccounted for. If only the Id-less `rununify` row fails, the parser has been rewritten "
            f"to key on a named `Id` header, which four of the five real layouts have and one does not.\n"
            + "\n".join(wrong),
        )

    def test_assorted_unresolvable_tokens_all_refuse(self):
        """Kept separate: sweeps a list of TOKENS against one fixed table, not a table shape.

        The subject here is which token STRINGS fail to resolve to a child, so it iterates tokens
        against one layout, where `PARSES` iterates layouts. `03+` and `last` are the two real ones
        from `rununify`; the rest are shapes a future author might reasonably write (`many`, `3-5`,
        `TBD`) and two that look numeric but are not (`0x02`, `1.5`).
        """

        for token in ("03+", "last", "many", "3-5", "??", "TBD", "0x02", "1.5"):
            with self.subTest(token=token):
                repo = _Repo()
                self.addCleanup(repo.close)
                _write_plan(
                    repo.root,
                    "executed",
                    plan_id="aaa111",
                    set_id="tok",
                    order=1,
                    status="executed",
                )
                _write_plan(
                    repo.root,
                    "pending",
                    plan_id="orc000",
                    set_id="tok",
                    order=0,
                    status="approved",
                    kind="orchestrator",
                    body=_table(
                        ["Order", "Id", "Child", "Depends on"],
                        [["01", "x", "x", "x"], [token, "x", "x", "x"]],
                    ),
                )
                d = rs.evaluate_set_retirement(repo.root, "tok")
                self.assertFalse(d.eligible, f"token {token!r} must refuse")
                self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
                self.assertIn(token, d.unauthored_rows)


# `RealColumnShapeFixtures` AND `ParserFailsClosed` WERE REMOVED HERE, their twelve tests absorbed
# by `TypedRefusalReasons.DECISIONS` (the verdict per column layout and per refusal cause) and
# `ChildTableParserTests.PARSES` (the exact declared tokens per table shape).
#
# WHY THE MERGE IS NOT A LOSS, stated because deleting parser coverage deserves scrutiny. Every case
# those classes held is a row now, and most rows are STRICTER than the test they replace: the four
# real column layouts were previously asserted only through an eligibility verdict (so a parser that
# read the ALIGNMENT row, or a table from ANOTHER section, could still produce `eligible=True` and
# pass), and they now pin the EXACT token tuple plus the `parsed` flag. The one-directional
# declared-vs-disk comparison keeps BOTH of its cases, adjacent, since the pair is the rule. The
# token sweep (`03+`, `last`, `many`, `3-5`, `??`, `TBD`, `0x02`, `1.5`) survives as its own test in
# `ChildTableParserTests`, because it iterates TOKENS against one layout where the table iterates
# LAYOUTS.


class RealRepositorySets(unittest.TestCase):
    """The predicate against THIS repository's real Sets: the measurements the plan is built on.

    ONE table replaces seven tests, each of which called `evaluate_set_retirement` on one live Set and
    asserted its verdict, several of them also re-parsing the orchestrator's table for non-vacuity.

    WHY A CORPUS TABLE EARNS ITS KEEP HERE. The synthetic tables above prove the RULES; these rows
    prove the rules meet the real column layouts, the real child counts and the real statuses. A
    parser validated only on fixtures is validated on shapes this file's author imagined, and the four
    live layouts disagree in ways nobody would invent (`rununify` has no `Id` column at all).

    EVERY ROW ASSERTS NON-VACUITY, which the old split did unevenly. Three of the seven re-parsed the
    child table to prove the refusal was about child STATUS rather than a table the reader failed to
    parse; four did not, so a parser regression could turn an eligible Set into an
    unauthored-rows refusal and pass. Now `parsed` is asserted on every row, alongside the child count
    and the status set, so a row can say WHY it reached its verdict and not merely that it did.

    THESE ROWS ARE WRITTEN AGAINST MEASURED STATE AND MUST BE RE-MEASURED, NOT LOOSENED. Each carries
    its own re-measurement history, because these Sets legitimately advance: a child reaching
    `executed` flips a refusal to eligible, and a NEW child being authored flips it back (measured on
    `lanectn`, four times). When a row goes red, re-measure and re-point it at a Set that still has
    the property, rather than weakening the assertion.

    URGENCY, preserved because it is the strongest argument this class contains: the runner gates lane
    integration on a bare whole-repo `pytest`, so one red test here refuses integration for EVERY lane
    that finishes afterwards. On 2026-09-14 that stranded eight plans in one night. Do not leave a red
    row here.
    """

    #: (setid, expected eligibility, the EXACT expected reason, the expected `unfinished` map, the
    #:  expected `unauthored_rows`, the minimum child count, the expected set of child statuses,
    #:  why this row exists and what to do when it goes red)
    LIVE_SETS = (
        (
            "wslayout",
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            5,
            {"executed"},
            "THE STABLE ELIGIBLE CARRIER: every child genuinely executed, four-column layout. This "
            "row is what proves the refusal rows below are not vacuous, since a predicate that "
            "refused every real Set would satisfy all of them",
        ),
        (
            "lanectn",
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            7,
            {"executed"},
            "THE MOST RE-MEASURED SET IN THE REPOSITORY, six columns including a `Depth` column. "
            "History: originally refused on two approved children; 2026-09-08 `nna8yz` recovered; "
            "2026-09-14 `xdr83v` integrated, so ELIGIBLE; 2026-09-16 a SEVENTH child (`4fodkt`) was "
            "AUTHORED, so REFUSED again (a new child appearing, not a child completing); 2026-09-17 "
            "`4fodkt` reached executed, so ELIGIBLE. WHY THAT CHILD EXISTS is the lesson: parent "
            "`h0zljh` carried an E-02 no child covered, and retirement SKIPS the pre-transition E/V "
            "checkpoint by design, so with six children executed that item would have been marked "
            "complete having never been performed. The child count is asserted at >= 7 so the Set "
            "cannot become eligible by LOSING that child",
        ),
        (
            "rununify",
            False,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            {"40it5e": "reviewed"},
            (),
            12,
            {"executed", "reviewed"},
            "THE THREE-COLUMN, NO-`Id` LAYOUT, and the Set that motivated the unauthored-rows rule. "
            "Its placeholder rows `03+` and `last` stood unauthored by deliberate design and the "
            "runner correctly refused the parent on every run for two weeks; on the maintainer's "
            "2026-09-14 ruling they were replaced with nine named children, all now executed. "
            "RE-MEASURED 2026-09-22 AND RE-POINTED PER THIS CLASS'S OWN RULE (re-measure, never "
            "loosen): the row asserted ELIGIBLE with 11 children, and a TWELFTH child `40it5e` was "
            "authored on 2026-09-22, so the parent is correctly refused again. That is "
            "this class's documented 'a NEW child being AUTHORED flips eligible back to refused' "
            "case, arriving for the same reason as `h0zljh` above: the orchestrator coverage gate "
            "found this parent carrying E-02 and E-03 that no child covered, and retirement SKIPS "
            "the pre-transition E/V checkpoint, so those two items would have been marked complete "
            "having never been performed. The Set therefore now exercises BOTH halves of the "
            "eligible/refused transition over its history rather than only the eligible end. "
            "RE-POINTED A SECOND TIME 2026-09-22 (`40it5e` `to-review` -> `reviewed`), and this "
            "second move is worth distinguishing from the first because it is a DIFFERENT event "
            "class than the two this row's prose already names. The first re-point recorded a child "
            "APPEARING; this one records a child ADVANCING WITHOUT COMPLETING, when `/plan-review` "
            "set `40it5e` to `reviewed`. The predicate is unaffected and that is the POINT: "
            "`SET_RETIREMENT_DONE_STATUS` is an allowlist of exactly `executed`, so every "
            "non-executed status is equally unfinished and the refusal REASON does not move. Only "
            "the observed status strings move, which is why re-pointing them is a re-measurement "
            "and not a loosening. A THIRD move is expected and is not a defect: when `40it5e` "
            "reaches `approved` this row reads `approved`, and when it reaches `executed` the Set "
            "flips back to ELIGIBLE with all twelve children executed. Re-measure then; do not "
            "widen the status set to admit several values at once, which would stop this row "
            "detecting anything",
        ),
        (
            "runprofile",
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            6,
            {"executed"},
            "THE ONE-DIRECTIONAL COMPARISON, measured on the real Set that has it: the child table "
            "declares Orders 01-05 while SIX children exist on disk, and the extra child must NOT "
            "produce an unauthored-rows refusal. A symmetric 'table and disk must match' rule would "
            "refuse this legitimately extended Set forever",
        ),
        (
            "orchretire",
            True,
            rs.RETIRE_ELIGIBLE,
            {},
            (),
            3,
            {"executed"},
            "THIS SET'S OWN orchestrator, whose layout the fixtures copy as their baseline. Included "
            "so the table covers the shape a reader of this file is most likely to assume is the only "
            "one",
        ),
        (
            "commitguard",
            False,
            rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            {"2s0iym": "reviewed"},
            (),
            3,
            {"executed", "reviewed"},
            "THE UNFINISHED-CHILDREN REFUSAL, pinned against a Set that HAS one today. `commitguard` "
            "is the right carrier because its child table is FULLY AUTHORED, so a refusal here can "
            "ONLY be the unfinished-children rule and never the unauthored-rows rule that `runstop` "
            "pins, which keeps the two reasons independently tested. WHEN THIS GOES RED, re-point it "
            "at another Set with a real unfinished child rather than deleting it; `runnoop` "
            "(`zz5yxq`) is the obvious successor. "
            "RE-MEASURED 2026-09-20: a THIRD child (`2s0iym`, `to-review`) was AUTHORED, so the "
            "unfinished map and the status set both grew and the child count went 2 -> 3. This is a "
            "child APPEARING, not a child completing, which is exactly the `lanectn` history above "
            "(a seventh child authored 2026-09-16 flipped that Set from eligible back to refused). "
            "WHY THAT CHILD EXISTS is the same lesson too: parent `ao1rb7` carried an E-03 (a "
            "cross-child honesty comparison of Order 01's shipped gate disclosures against Order "
            "02's shipped contract sentences) that NO child covered, and retirement SKIPS the "
            "pre-transition E/V checkpoint by design, so the ORCHESTRATOR COVERAGE GATE refused a "
            "run rather than let that item be marked complete unperformed. The parent's own OQ-02 "
            "had already named 'add an Order 03 child' as the fix. The refusal REASON is unchanged, "
            "which is the property this row actually pins. "
            "RE-MEASURED 2026-09-21: `2s0iym` advanced `to-review` -> `reviewed` (a `/plan-review` "
            "ran on it), so its entry in the unfinished map and the status set moved with it. The "
            "child COUNT is still 3 and the refusal reason is STILL "
            "`RETIRE_REFUSED_UNFINISHED_CHILDREN`, so this is the ordinary within-lifecycle advance "
            "this row's own guidance predicts, not a change of property. Re-pointed rather than "
            "loosened: `reviewed` is asserted exactly, so a child reaching `approved` or `executed` "
            "will correctly turn this row red again. RE-MEASURED 2026-09-22 AND IT DID EXACTLY "
            "THAT, which is this row working as designed rather than breaking: `y9vpvv` reached "
            "`executed`, so it LEFT the unfinished map and the status set lost `approved`. The "
            "child COUNT is still 3 and the refusal REASON is STILL "
            "`RETIRE_REFUSED_UNFINISHED_CHILDREN` (carried by `2s0iym` alone now), so the property "
            "this row pins is intact and only the membership moved. NOTE THE DIRECTION IS THE "
            "OPPOSITE of the two prior re-measurements: those were children APPEARING, this is a "
            "child COMPLETING, so this row has now exercised both directions of the transition. "
            "`y9vpvv` was finalized by hand after run `run-20260922T003657Z-1022108` was "
            "signal-stopped leaving its verified lane unintegrated; the work landed in `13192e38` "
            "and the record closed in `5d8779e8`",
        ),
        (
            "runstop",
            False,
            rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
            {},
            ("00", "-"),
            6,
            {"executed"},
            "THE 2.5 CASE ON REAL DATA: every child IS executed, so a naive rule would retire this "
            "orchestrator, and only the unauthored rows `00` and `-` stop it. This is the row that "
            "proves the unauthored-rows rule is reachable on real layouts and not just on fixtures. "
            "WHEN THIS GOES RED, `selfcommit` (row `02`) is the obvious successor",
        ),
    )

    def test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason(self):
        wrong = []
        for (
            setid,
            eligible,
            reason,
            unfinished,
            unauthored,
            min_children,
            statuses,
            why,
        ) in self.LIVE_SETS:
            d = rs.evaluate_set_retirement(REPO_ROOT, setid)
            m = rs.read_set_membership(REPO_ROOT, setid)
            problems = []
            if d.eligible is not eligible:
                problems.append(f"eligible is {d.eligible!r}, expected {eligible!r}")
            if d.reason != reason:
                problems.append(f"reason is {d.reason!r}, expected {reason!r}")
            if dict(d.unfinished) != unfinished:
                problems.append(
                    f"unfinished is {dict(d.unfinished)!r}, expected {unfinished!r}"
                )
            if tuple(d.unauthored_rows) != unauthored:
                problems.append(
                    f"unauthored_rows is {tuple(d.unauthored_rows)!r}, expected {unauthored!r}"
                )
            # NON-VACUITY, asserted on EVERY row: the orchestrator must exist and its child table
            # must actually PARSE, so a verdict cannot be reached because the reader gave up.
            if m.orchestrator is None:
                problems.append(
                    "the Set has NO orchestrator on disk, so every assertion above is about a Set "
                    "this reader could not find"
                )
            else:
                tokens, parsed = rs.parse_declared_child_orders(
                    m.orchestrator.path.read_text(encoding="utf-8")
                )
                if not parsed:
                    problems.append(
                        "the child table did NOT parse, so any refusal here is about the reader "
                        "rather than about the Set, and any eligibility is vacuous"
                    )
                if not tokens:
                    problems.append(
                        "the child table parsed to NO tokens, which is the vacuous-pass shape"
                    )
            if len(m.children) < min_children:
                problems.append(
                    f"the Set has {len(m.children)} children, expected at least {min_children}; a "
                    "verdict reached by LOSING a child is not the verdict this row measured"
                )
            got_statuses = {c.status for c in m.children}
            if got_statuses != statuses:
                problems.append(
                    f"child statuses are {sorted(got_statuses)!r}, expected {sorted(statuses)!r}"
                )
            if problems:
                wrong.append(
                    f"  {setid}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.LIVE_SETS)} live Sets no longer match their measured state. "
            "READ THIS BEFORE EDITING ANYTHING. These rows assert the REAL repository, and a real Set "
            "legitimately ADVANCES: a child reaching `executed` flips a refusal to eligible, and a NEW "
            "child being AUTHORED flips eligible back to refused (measured on `lanectn` four times). "
            "So a single red row is usually a correct change in the corpus, and the fix is to "
            "RE-MEASURE and re-point the row, or to move the property to another Set that still has "
            "it, NEVER to loosen the assertion. If MANY rows fail at once, that is the opposite "
            "situation and points at the predicate or the child-table parser rather than at the "
            "corpus; check the `did NOT parse` lines first, since a parser that gives up turns every "
            "Set into an unauthored-rows refusal. URGENCY: lane integration is gated on a bare "
            "whole-repo pytest, so one red row here refuses integration for EVERY lane that finishes "
            f"afterwards (on 2026-09-14 that stranded eight plans in one night).\n"
            + "\n".join(wrong),
        )


# ==================================================================================================
# Scope fence: this child DECIDES ONLY
# ==================================================================================================


class ThisChildDecidesOnly(unittest.TestCase):
    """The predicate DECIDES and never ACTS, demonstrated by driving it and measuring the tree.

    WHAT THIS CLASS USED TO DO, AND WHY IT WAS REPLACED. It asserted over
    `inspect.getsource(...)` that four functions' text did not contain the tokens `ipd_set`,
    `set executed`, `finalize`, `shutil.move`, `git mv`, `write_text` or `subprocess`. That is a
    CHANGE DETECTOR, not a test: it breaks when the source is reformatted or a helper is renamed, it
    cannot see an action performed through a differently-spelled call (`os.replace`, `Path.rename`,
    `os.rename`, a `pathlib` write, anything reached indirectly), and it can be satisfied by moving
    a real mutation behind a name the list does not mention. It was also satisfiable by editing a
    COMMENT, since the whole function source including comments was searched.

    WHAT REPLACES IT IS AN OBSERVATION. A byte-level SNAPSHOT of the entire plans tree is taken, the
    predicate is driven over every kind of Set it can meet (eligible, unfinished, unauthored,
    parse-refused, unresolvable), and the snapshot is compared. That catches a mutation performed by
    ANY spelling, including ones nobody thought to forbid, and it cannot be quieted by a comment.

    "THE PREDICATE QUIETLY GREW A TRANSITION" is the failure being defended against, because a
    predicate that MOVES a plan turns a wrong decision from a wrong answer into a wrong ACTION.
    `5942n7` owns the decision; `ueg5cf` owns the transition and `pgq326` the wiring.
    """

    def _snapshot(self, root: Path) -> dict:
        """Every file under the plans tree, by relative path, with its bytes and mtime."""

        base = root / ".aw" / "records" / "plans"
        out = {}
        for path in sorted(base.rglob("*")):
            if path.is_file():
                out[str(path.relative_to(base))] = (
                    path.read_bytes(),
                    path.stat().st_mtime_ns,
                )
        return out

    def test_driving_every_decision_path_writes_NOTHING_to_the_plans_tree(self):
        """The behavioral replacement for the source-token pin, over every decision path.

        Each Set shape drives a DIFFERENT branch of `evaluate_set_retirement`, and the eligible one
        is the important one: it is the only shape on which an accidental transition would look
        CORRECT to its author, because it is the case where the runner's real transition does move the
        plan. A test that drove only refusals could not see a predicate that retired on success.
        """

        repo = _Repo()
        self.addCleanup(repo.close)
        root = repo.root
        shapes = {
            # setid -> (children, declared row tokens or None, body override or None)
            "elig": ([("aaa111", 1, "executed", "executed")], None, None),
            "unfin": ([("bbb222", 1, "approved", "pending")], None, None),
            "unauth": ([("ccc333", 1, "executed", "executed")], ["01", "02"], None),
            "noparse": (
                [("ddd444", 1, "executed", "executed")],
                None,
                f"## {rs._CHILD_IPDS_HEADING}\n\nProse only, no table.\n",
            ),
            "nokids": ([], [], None),
        }
        for setid, (children, declared, body) in shapes.items():
            for id6, order, status, bucket in children:
                _write_plan(
                    root,
                    bucket,
                    plan_id=id6,
                    set_id=setid,
                    order=order,
                    status=status,
                )
            orchestrator_body = body
            if orchestrator_body is None:
                tokens = (
                    declared
                    if declared is not None
                    else [f"{o:02d}" for _i, o, _s, _b in children]
                )
                orchestrator_body = _table(
                    ["Order", "Id", "Child", "Depends on"],
                    [[t, "x", "x", "x"] for t in tokens],
                )
            _write_plan(
                root,
                "pending",
                plan_id=f"orc{setid[:3]}",
                set_id=setid,
                order=0,
                status="approved",
                kind="orchestrator",
                body=orchestrator_body,
            )

        before = self._snapshot(root)
        self.assertTrue(before, "fixture sanity: the plans tree must not be empty")

        # Drive EVERY public entry point of the decision layer, on every shape, plus an
        # unresolvable selector. This is the set of calls a runner makes before deciding.
        verdicts = {}
        for setid in list(shapes) + ["nosuchset"]:
            m = rs.read_set_membership(root, setid)
            verdicts[setid] = rs.evaluate_set_retirement(root, setid).reason
            if m.orchestrator is not None:
                text = m.orchestrator.path.read_text(encoding="utf-8")
                rs.parse_declared_child_orders(text)
                rs.find_unauthored_child_rows(text, m)

        after = self._snapshot(root)

        # The verdicts prove the calls were not no-ops: an inert predicate would also write nothing.
        self.assertEqual(
            verdicts["elig"],
            rs.RETIRE_ELIGIBLE,
            f"fixture sanity: the eligible shape must actually be eligible, or this test proves "
            f"nothing about the path where a transition would look correct; got {verdicts}",
        )
        # FIVE distinct reasons, i.e. every outcome the predicate has: `nosuchset` reaches
        # `no-orchestrator`, which is the fifth and is why the unresolvable selector is driven too.
        self.assertEqual(
            sorted(set(verdicts.values())),
            sorted(
                {
                    rs.RETIRE_ELIGIBLE,
                    rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
                    rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
                    rs.RETIRE_REFUSED_NO_CHILDREN,
                    rs.RETIRE_REFUSED_NO_ORCHESTRATOR,
                }
            ),
            f"fixture sanity: the shapes must exercise EVERY outcome the predicate has, or a branch "
            f"that mutates would never be driven; got {verdicts}",
        )

        changed = sorted(set(before) ^ set(after))
        rewritten = sorted(
            name
            for name in set(before) & set(after)
            if before[name][0] != after[name][0]
        )
        touched = sorted(
            name
            for name in set(before) & set(after)
            if before[name][1] != after[name][1]
        )
        self.assertEqual(
            (changed, rewritten, touched),
            ([], [], []),
            "DECIDING MUTATED THE PLANS TREE. The decision layer must perform NO transition: a "
            "predicate that moves or rewrites a plan turns a wrong decision from a wrong ANSWER into "
            f"a wrong ACTION.\n  appeared/disappeared: {changed}\n  rewritten in place: {rewritten}"
            f"\n  mtime changed: {touched}\n"
            "FIX: this is measured by snapshotting the whole tree rather than by grepping the source, "
            "so it catches a mutation by ANY spelling (`git mv`, `shutil.move`, `Path.rename`, "
            "`write_text`, a subprocess) including one nobody thought to forbid. The transition "
            "belongs in `ipd_lifecycle.retire_orchestrator`, which is gated and journalled; nothing "
            "in `runner_shared`'s decision region may act.",
        )

    def test_the_decision_layer_is_idempotent_over_repeated_calls(self):
        """The second behavioral half: deciding twice gives the SAME answer.

        A predicate that ACTED would change the state its own next call reads, so a second call would
        legitimately differ. Asserting stability over repeated calls therefore catches a side effect
        that happened to leave the tree byte-identical (for instance one that only touched run state),
        which the snapshot above cannot see.
        """

        repo = _Repo()
        self.addCleanup(repo.close)
        _write_plan(
            repo.root,
            "executed",
            plan_id="aaa111",
            set_id="idem",
            order=1,
            status="executed",
        )
        _write_plan(
            repo.root,
            "pending",
            plan_id="orc000",
            set_id="idem",
            order=0,
            status="approved",
            kind="orchestrator",
            body=_table(
                ["Order", "Id", "Child", "Depends on"], [["01", "x", "x", "x"]]
            ),
        )
        verdicts = [rs.evaluate_set_retirement(repo.root, "idem") for _ in range(3)]
        self.assertTrue(
            verdicts[0].eligible,
            f"fixture sanity: this Set must be eligible; {verdicts[0].detail}",
        )
        self.assertEqual(
            [(v.eligible, v.reason, v.detail) for v in verdicts],
            [(verdicts[0].eligible, verdicts[0].reason, verdicts[0].detail)] * 3,
            "the decision changed between identical calls, so deciding has a SIDE EFFECT on the "
            "state it reads. A pure predicate must answer the same question the same way until "
            "something else changes the tree.",
        )

    def test_execution_success_states_was_not_touched(self):
        """Kept separate: asserts two module CONSTANTS relate correctly, with no repository.

        Spec Section 4 puts `EXECUTION_SUCCESS_STATES` out of scope for this Set. The claim is that
        the retirement allowlist and the run-state success set are DIFFERENT things: the latter admits
        `substantially-complete` (finalize REFUSED) and the former must not.
        """

        from agent_workflows import oc_runipd

        self.assertIn("substantially-complete", oc_runipd.EXECUTION_SUCCESS_STATES)
        self.assertNotEqual(
            rs.SET_RETIREMENT_DONE_STATUS, oc_runipd.EXECUTION_SUCCESS_STATES
        )

    def test_the_queue_scoped_predicate_is_left_in_place_for_child_03(self):
        """Kept separate: an EXISTENCE claim about a symbol this child deliberately did not remove."""

        from agent_workflows import oc_runipd

        self.assertTrue(callable(oc_runipd._set_children_all_executed))


# ==================================================================================================
# orchretire Order 02 (`ueg5cf`): the RUNNER-OWNED ROLLUP RETIREMENT TRANSITION
#
# WHAT THIS HALF PINS, and why it is written adversarially rather than as a happy-path check.
#
# This transition DELIBERATELY OPENS A LIFECYCLE GATE: it reaches `executed` without the
# `pre-transition` E/V checkpoint and without a `begin` receipt. That is legitimate for an Order-0
# plan whose items the runner supersedes (spec `77tr3o` R-5/R-6, shape (b), chosen by the maintainer)
# and it is a HOLE for anything else. So the tests below spend more effort proving the gate did NOT
# open anywhere else than proving it opened where intended:
#
#   * a `Kind: child` plan is REFUSED by this route no matter its state;
#   * an orchestrator whose Set is INELIGIBLE is refused, because `Kind` alone is not authority
#     (`oc_runipd.action_for` returns `orchestrate` from `reviewed` onward, so a Kind-only route would
#     retire whatever it was handed);
#   * the ordinary `aw ipd finalize` path still produces the six `IPD-S404` findings for an
#     orchestrator, so no human-facing gate was relaxed;
#   * a WORKER-role process is refused, because that guard lives in the CLI wrappers and is NOT
#     inherited by a new transition function; and
#   * `ipd_lint.py` is byte-unchanged, which is the positive evidence that the REJECTED shape (a) was
#     not taken.
#
# The gate-parity tests exist because the maintainer accepted ONE known cost of shape (b): two
# transition paths can DRIFT. Where a gate could be SHARED AS CODE it is (`_early_recovery_result`,
# `_finalize_transaction`, `acquire_finalize_lock`), which removes it from the drift surface; what
# remains is named in `ROLLUP_SHARED_GATES`/`ROLLUP_OMITTED_GATES` and asserted here.
# ==================================================================================================


def _git(root: Path, *args: str) -> str:
    import subprocess

    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def _structurally_conforming_plan(
    *,
    plan_id: str,
    set_id: str,
    order: int,
    status: str,
    kind: str = "orchestrator",
    child_table: str = "",
) -> str:
    """A plan built from the REAL `aw ipd scaffold` skeleton, so structural lint conforms.

    WHY NOT the lightweight `_plan_text` fixture the predicate tests use. The predicate reads four
    metadata bullets and never lints, so a four-line fixture is honest there. The TRANSITION runs
    `post-transition` lint on the committed plan, which requires every mandated H2 section and
    metadata field, so a lightweight fixture lands the transaction in `committed-incomplete` and the
    test would then be measuring the fixture rather than the transition.

    Deliberately built via `ipd_authoring.build_skeleton` rather than hand-written: the required
    section set is the scaffold's business, and a hand-copied list here would rot the first time the
    schema gains a section.

    IMPORTANT: the `E-01`/`V-01` rows are left at `pending`/`pending`, exactly as an unexecuted
    orchestrator's are. That is not laziness, it IS the fixture: the whole point of the rollup is that
    it retires a plan whose items nobody performed, so back-filling them would test nothing. It is
    also what makes `TheHumanFacingGateIsUNCHANGED` meaningful - the same fixture still produces the
    `IPD-S404` findings on the ordinary finalize path.
    """

    from agent_workflows import ipd_authoring as A

    txt = A.build_skeleton(
        kind=kind,
        title=f"synthetic {kind}",
        author="tester",
        when="2026-09-06",
        set_name=set_id,
        order=order,
        plan_id=plan_id,
    )
    out: list[str] = []
    in_meta = True
    for ln in txt.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append(f"- Status: {status}")
            continue
        if in_meta and ln.startswith("- Scope-Paths:"):
            # `grandfathered` is the reserved sentinel for a plan with no machine path fence, which
            # is what an orchestrator legitimately is: it coordinates, it does not edit.
            out.append("- Scope-Paths: grandfathered")
            continue
        if in_meta and ln.startswith("- Item-Dependencies:"):
            out.append("- Item-Dependencies: none")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            if status in ("approved", "auto-approved"):
                out.append("- Approval: 2026-09-06, human: approved")
    text = "\n".join(out) + "\n"
    if child_table:
        text = text.replace(
            "## Child IPDs, sequence, and dependencies\n\n"
            "TODO: child IPD table (Order | File | What it does | Depends on).\n",
            child_table + "\n",
        )
    return text


def _write_conforming_plan(root: Path, bucket: str, **kw) -> Path:
    text = _structurally_conforming_plan(**kw)
    d = root / ".aw" / "records" / "plans" / bucket
    d.mkdir(parents=True, exist_ok=True)
    path = (
        d
        / f"20260906-{kw['set_id']}-{kw['order']:02d}-{kw['plan_id']}-synthetic.ipd.md"
    )
    path.write_text(text, encoding="utf-8")
    return path


def _init_git_repo(root: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    # Mirror the real repo: lifecycle control state is gitignored, so writing a journal/lock never
    # dirties the tree.
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


class RollupTransitionCase(unittest.TestCase):
    """A git-backed throwaway repo holding one real Set, for the TRANSITION (not the predicate).

    Git-backed rather than a bare temp dir because the transition makes a real path-scoped commit,
    takes a real lock, and writes a real journal; a fixture that stubbed git would prove nothing about
    the gates this plan's whole risk lives in.
    """

    def setUp(self) -> None:
        import tempfile as _tf

        from agent_workflows import ipd_lifecycle as LC

        self._tmp = _tf.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        # A per-case checkout at a fresh path must not read a previous case's memoized control root.
        LC.clear_checkout_control_root_cache()
        self.addCleanup(LC.clear_checkout_control_root_cache)
        _init_git_repo(self.root)

    def make_set(
        self,
        setid: str,
        children: list[tuple[str, int, str, str]],
        *,
        orchestrator_status: str = "approved",
        orchestrator_id: str = "orc000",
        declared_rows: list[str] | None = None,
    ) -> Path:
        """Write a Set and commit it. Returns the orchestrator's path.

        Both the orchestrator AND the children use the structurally-conforming scaffold, because the
        `Kind: child` refusal tests aim the rollup route at a real child plan and the human-gate test
        runs the ordinary finalize on one.
        """

        for id6, order, status, bucket in children:
            _write_conforming_plan(
                self.root,
                bucket,
                plan_id=id6,
                set_id=setid,
                order=order,
                status=status,
                kind="child",
            )
        cells = ["Order", "Id", "Child", "Depends on"]
        tokens = declared_rows or [f"{order:02d}" for _i, order, _s, _b in children]
        rows = [[tok] + ["x"] * (len(cells) - 1) for tok in tokens]
        orch = _write_conforming_plan(
            self.root,
            "pending",
            plan_id=orchestrator_id,
            set_id=setid,
            order=0,
            status=orchestrator_status,
            kind="orchestrator",
            child_table=_table(cells, rows),
        )
        import subprocess

        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "set"], cwd=self.root, check=True)
        return orch

    def retire(self, orch: Path, setid: str, **kw):
        from agent_workflows import ipd_lifecycle as LC

        kw.setdefault("actor", "aw oc run model=test")
        kw.setdefault("run_id", "run-20260906T000000Z-1")
        # env is passed EXPLICITLY as a non-worker mapping: the suite itself may run inside a managed
        # lane (this very plan was executed in one, with AW_EXECUTION_ROLE=worker set), and a test
        # that silently read os.environ would then refuse for the wrong reason and pass vacuously.
        kw.setdefault("env", {})
        return LC.retire_orchestrator(self.root, orch, setid=setid, **kw)


class RollupRetiresAnEligibleSet(RollupTransitionCase):
    """V-01, the intended opening: an eligible Set retires with NO `IPD-S404` findings."""

    def test_an_eligible_set_retires_and_lands_in_executed(self):
        """Kept separate: THE POSITIVE PATH, and the one case where the plan must actually MOVE.

        Every refusal test in `TheGateDoesNotOpenForOrdinaryPlans` asserts the plan stays put, so all
        of them would pass against a transition that never worked at all. This is the test that makes
        them non-vacuous, and it additionally asserts NONE of the six `IPD-S404` findings appears,
        which is the exemption being exercised rather than merely declared.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set(
            "good",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
        )
        res = self.retire(orch, "good", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        # NONE of the six IPD-S404 findings the main path produces for an orchestrator.
        self.assertEqual(
            [f for f in res.findings if "IPD-S404" in f],
            [],
            f"the rollup must not hit the E/V checkpoint: {res.findings}",
        )
        dest = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260906-good-00-orc000-synthetic.ipd.md"
        )
        self.assertTrue(
            dest.is_file(), "the retired orchestrator must land in executed/"
        )
        self.assertFalse(orch.is_file(), "it must not remain in pending/")
        text = dest.read_text(encoding="utf-8")
        self.assertIn("- Status: executed", text)
        self.assertIsNotNone(res.commit)

    def test_the_dry_run_evaluates_every_gate_and_mutates_nothing(self):
        """Kept separate: `apply=False` is a MODE of the whole transition, asserted as an absence.

        It must reach EXIT_OK (so every gate was evaluated) while leaving the plan, its bytes and HEAD
        untouched, which is a conjunction of one positive and three negative claims about one call.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("dry", [("aaa111", 1, "executed", "executed")])
        before = orch.read_text(encoding="utf-8")
        head_before = _git(self.root, "rev-parse", "HEAD").strip()
        res = self.retire(orch, "dry", apply=False)
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertIsNone(res.commit)
        self.assertTrue(orch.is_file())
        self.assertEqual(orch.read_text(encoding="utf-8"), before)
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head_before)

    def test_the_lifecycle_commit_is_path_scoped_to_owned_paths_only(self):
        """A rollup must never sweep a co-worker's file into its commit."""

        orch = self.make_set("scoped", [("aaa111", 1, "executed", "executed")])
        # A concurrent agent's unrelated dirty + untracked work, which must survive untouched.
        (self.root / "someone_elses.py").write_text("# not mine\n", encoding="utf-8")
        res = self.retire(orch, "scoped", apply=True)
        self.assertEqual(res.exit_code, 0, res.message)
        assert res.commit is not None
        committed = _git(
            self.root, "show", "--name-only", "--format=", res.commit
        ).split()
        self.assertNotIn("someone_elses.py", committed)
        for path in committed:
            self.assertTrue(
                path.startswith(".aw/records/plans/"),
                f"the rollup committed a non-lifecycle path: {path}",
            )
        # Untouched AND still unstaged: a rollup that staged it would have "preserved" the file while
        # stealing its provenance on the next commit anyone made.
        self.assertTrue((self.root / "someone_elses.py").is_file())
        self.assertEqual(
            _git(self.root, "status", "--porcelain", "--", "someone_elses.py").strip(),
            "?? someone_elses.py",
        )


class TheGateDoesNotOpenForOrdinaryPlans(RollupTransitionCase):
    """V-01/V-05, THE REGRESSION THAT MATTERS MOST: the exemption must not widen.

    THIS TRANSITION DELIBERATELY OPENS A LIFECYCLE GATE. It reaches `executed` without the
    pre-transition E/V checkpoint and without a `begin` receipt, which is legitimate for an Order-0
    plan whose items the runner supersedes (spec `77tr3o` R-5/R-6, shape (b)) and is a HOLE for
    anything else. So these tests spend more effort proving the gate did NOT open elsewhere than
    proving it opened where intended.

    ONE TABLE replaces four refusal tests (a child by the rollup route, a child in an eligible Set, an
    ineligible orchestrator, an unauthored-rows orchestrator, an already-terminal orchestrator, and a
    forged verdict). Each aimed `retire_orchestrator` at one target and asserted a typed finding.

    EVERY REFUSAL REASON KEEPS ITS OWN ROW, AND THE ROW NAMES THE REASON. Retirement is a safety gate,
    so `assertFalse(ok)` is never sufficient: a gate that refused everything for one generic reason
    would be indistinguishable from the correct behavior in a boolean test, and a gate whose reasons
    drifted would send a human to fix the wrong thing. Each row additionally asserts the plan was left
    BYTE-UNCHANGED and IN PLACE, so a refusal that has already performed the transition is not
    accepted as a refusal.

    THE TWO MEASURED-BYPASS TESTS ARE KEPT SEPARATE, below, and each says why: they assert the EXACT
    finding tuple (nothing else may mask the Kind gate) against targets built outside `make_set`, and
    one of them records a real reproduction in which an evidence-free plan reached `executed/`.
    """

    #: (case, the target to aim the route at, the setid to pass, the Set to build, the orchestrator's
    #:  status, declared row tokens, whether to hand in a forged verdict, the EXACT typed finding
    #:  expected, a message substring or None, why this row exists)
    GATES = (
        (
            "an `executed` CHILD plan, by the rollup route",
            "child",
            "kid",
            [("aaa111", 1, "executed", "executed")],
            "approved",
            None,
            False,
            "ROLLUP_REFUSED_NOT_ORCHESTRATOR",
            "not an orchestrator",
            "THE KIND GATE. `retire_orchestrator` must refuse anything that is not an Order-0 "
            "orchestrator, because the exemption it carries (no E/V checkpoint, no receipt) is only "
            "legitimate for a plan whose items the runner supersedes",
        ),
        (
            "a CHILD of an ELIGIBLE Set, where nothing else is wrong",
            "child",
            "kid2",
            [("aaa111", 1, "executed", "executed")],
            "approved",
            None,
            False,
            "ROLLUP_REFUSED_NOT_ORCHESTRATOR",
            None,
            "THE DANGEROUS SHAPE: the Set IS eligible and the actor IS valid, so only `Kind` differs. "
            "A Kind check that ran only after something else had already failed would pass a "
            "happy-path test and still be a hole",
        ),
        (
            "an orchestrator whose Set has an UNFINISHED child",
            "orchestrator",
            "unfin",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
            ],
            "approved",
            None,
            False,
            "ROLLUP_REFUSED_SET_INELIGIBLE",
            "bbb222",
            "F-9: `Kind: orchestrator` ALONE IS NOT AUTHORITY. `action_for` returns `orchestrate` "
            "from `reviewed` onward, so a Kind-only route would retire an orchestrator whose children "
            "are still in flight. The eligibility verdict is required IN the transition, not merely "
            "from a well-behaved caller, and the message must NAME the child being waited on",
        ),
        (
            "an orchestrator with an UNAUTHORED child row",
            "orchestrator",
            "unauth",
            [("aaa111", 1, "executed", "executed")],
            "approved",
            ["01", "03+"],
            False,
            "ROLLUP_REFUSED_SET_INELIGIBLE",
            "03+",
            "the `rununify`/`5e4sb6` case reaching the TRANSITION rather than only the predicate. "
            "Every child that EXISTS is executed here, so a transition that trusted child statuses "
            "alone would retire this parent while declared work is unaccounted for",
        ),
        (
            "an orchestrator that is ALREADY `executed`",
            "orchestrator",
            "done",
            [("aaa111", 1, "executed", "executed")],
            "executed",
            None,
            False,
            "ROLLUP_REFUSED_ALREADY_TERMINAL",
            None,
            "a terminal plan must not be re-transitioned: doing so would append a SECOND history "
            "entry claiming a retirement that already happened, and would move a file that is "
            "already at its destination",
        ),
        (
            "an eligible Set with a FORGED ineligible verdict handed in",
            "orchestrator",
            "hand",
            [("aaa111", 1, "executed", "executed")],
            "approved",
            None,
            True,
            "ROLLUP_REFUSED_SET_INELIGIBLE",
            None,
            "A SUPPLIED VERDICT IS VALIDATED, NOT TRUSTED. A caller may hand in a decision to avoid "
            "recomputing it, and the direction tested here is the SAFE one (a refusal is honored). "
            "The dangerous direction, a forged ELIGIBLE verdict, is covered by the ineligible-Set row "
            "above, which recomputes and refuses regardless of what a caller believes",
        ),
    )

    def test_every_gate_refuses_its_own_target_for_its_own_typed_reason(self):
        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared as rs

        wrong = []
        for (
            case,
            target,
            setid,
            children,
            orchestrator_status,
            declared,
            forge,
            finding,
            message_substring,
            why,
        ) in self.GATES:
            self.setUp()
            orch = self.make_set(
                setid,
                children,
                orchestrator_status=orchestrator_status,
                declared_rows=declared,
            )
            if target == "child":
                id6, order, _status, bucket = children[0]
                plan = (
                    self.root
                    / ".aw"
                    / "records"
                    / "plans"
                    / bucket
                    / f"20260906-{setid}-{order:02d}-{id6}-synthetic.ipd.md"
                )
            else:
                plan = orch
            before = plan.read_text(encoding="utf-8")
            head = _git(self.root, "rev-parse", "HEAD").strip()
            kwargs = {}
            if forge:
                kwargs["eligibility"] = rs.RetirementDecision(
                    eligible=False,
                    reason=rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
                    setid=setid,
                    detail="caller says no",
                )
            res = self.retire(plan, setid, apply=True, **kwargs)
            expected_finding = getattr(LC, finding)
            problems = []
            if res.exit_code != LC.EXIT_FINDINGS:
                problems.append(
                    f"exit code is {res.exit_code!r}, expected EXIT_FINDINGS "
                    f"({LC.EXIT_FINDINGS!r}); message: {res.message!r}"
                )
            if expected_finding not in res.findings:
                problems.append(
                    f"the typed finding {expected_finding!r} is absent; got {res.findings!r}. A gate "
                    "that refuses for the WRONG reason sends a human to fix the wrong thing"
                )
            if message_substring is not None and message_substring not in res.message:
                problems.append(
                    f"the message must contain {message_substring!r}; it said {res.message!r}"
                )
            # A REFUSAL THAT HAS ALREADY ACTED IS NOT A REFUSAL.
            if not plan.is_file():
                problems.append(
                    "the plan LEFT its directory, so the transition happened despite the refusal"
                )
            elif plan.read_text(encoding="utf-8") != before:
                problems.append(
                    "the plan's BYTES changed, so a status edit was applied despite the refusal"
                )
            if _git(self.root, "rev-parse", "HEAD").strip() != head:
                problems.append(
                    "HEAD ADVANCED, so a lifecycle commit was made despite the refusal"
                )
            if problems:
                wrong.append(
                    f"  {case} (target={target}, setid={setid!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.GATES)} rollup gates did not refuse correctly. THIS IS THE "
            "REGRESSION THAT MATTERS MOST in this file: `retire_orchestrator` reaches `executed` with "
            "NO pre-transition E/V checkpoint and NO begin receipt, which is legitimate only for an "
            "Order-0 plan whose items the runner supersedes and is a HOLE for anything else. FIX: a "
            "row that stopped refusing means an ordinary plan can now reach `executed/` with no "
            "evidence at all, and the KIND rows are the severe ones, because a widened Kind gate was "
            "MEASURED to carry an approved, evidence-free child of another Set to `executed` (see "
            "`test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict`). If the plan MOVED or "
            "HEAD ADVANCED while the finding was still reported, the gate refuses too late: it is "
            f"reporting a refusal it has already overridden.\n" + "\n".join(wrong),
        )

    def test_an_APPROVED_PENDING_child_with_unperformed_items_is_refused(self):
        """Kept separate: asserts the EXACT finding tuple, so no other gate may mask the Kind gate.

        THE CASE THIS WHOLE PLAN MUST NEVER ENABLE, isolated so nothing else can mask it. Not a row in
        `GATES` above, because the assertion is `res.findings == (ONE finding,)` rather than
        `assertIn`, and its target is built OUTSIDE `make_set` (a separate approved, pending,
        evidence-free plan committed on its own), which no row's children column can express.

        The two tests above aim the route at an `executed` child, so if the Kind gate were removed the
        `already-terminal` gate would still refuse them and the sabotage would look half-contained.
        This target is the genuinely dangerous one: an APPROVED plan sitting in `pending/` whose
        `E-01` is `pending` and whose `V-01` has no evidence, i.e. exactly a plan that must NOT be
        able to reach `executed`.

        MEASURED CAVEAT, recorded because it changes what this test proves. For a victim in the SAME
        Set the eligibility gate ALSO refuses (an unexecuted child makes its own Set ineligible), so
        with the Kind gate widened this test fails on the FINDING it observes rather than on a plan
        actually moving. That containment is real but accidental; the shape where only the Kind gate
        stands in the way is the sibling test
        `test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict`, which is where an
        evidence-free plan was measured genuinely reaching `executed/`. Both are kept: this one pins
        the refusal REASON, that one pins the CONSEQUENCE.
        """

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared as rs

        # An eligible Set (so the eligibility gate cannot be what refuses), plus a SEPARATE approved,
        # pending, evidence-free child plan as the target.
        self.make_set("bypass", [("aaa111", 1, "executed", "executed")])
        victim = _write_conforming_plan(
            self.root,
            "pending",
            plan_id="vvv999",
            set_id="bypass",
            order=9,
            status="approved",
            kind="child",
        )
        import subprocess

        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "victim"], cwd=self.root, check=True
        )

        text = victim.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("- Execution state: pending", text)
        self.assertIn("- Result: pending", text)
        self.assertNotIn("- Status: executed", text)

        res = self.retire(victim, "bypass", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        self.assertEqual(
            res.findings,
            (LC.ROLLUP_REFUSED_NOT_ORCHESTRATOR,),
            "the KIND gate must be what refuses here; no other gate can mask it",
        )
        # And it is genuinely untouched: still pending, still approved, still unevidenced.
        self.assertTrue(victim.is_file())
        self.assertEqual(victim.read_text(encoding="utf-8"), text)
        self.assertFalse(
            (
                self.root
                / ".aw/records/plans/executed/20260906-bypass-09-vvv999-synthetic.ipd.md"
            ).exists()
        )
        # Sanity: this plan really would have been refused evidence-wise by the honest path too.
        self.assertTrue(
            rs.evaluate_set_retirement(self.root, "bypass").eligible is False
        )

    def test_a_child_of_ANOTHER_set_cannot_ride_an_eligible_sets_verdict(self):
        """Kept separate: the MEASURED bypass, with its reproduction transcript recorded inline.

        THE ACTUAL BYPASS, measured. This is the strongest test in the module, and it stays its own
        test for two reasons a row cannot carry: it asserts the EXACT finding tuple (only the Kind gate
        may refuse this shape), and its victim belongs to a DIFFERENT Set than the `setid` argument
        names, which is the whole point and is not expressible in a table keyed on one Set.

        MEASURED DURING EXECUTION, not hypothesised. Widening the Kind gate and pointing the route at
        a child of the SAME Set is contained by the eligibility gate (an unexecuted child makes its
        own Set ineligible, so the call refuses for that reason instead). That containment is real but
        it is ACCIDENTAL, and relying on it would have left the suite blind to the shape that actually
        works: name an ELIGIBLE Set as `setid` while pointing `plan_path` at an approved,
        evidence-free child of a DIFFERENT Set. Reproduced with the Kind gate widened:

            exit_code = 0
            message   = finalized vvv999 -> executed at a4e30f98c3d8
            VICTIM REACHED executed/ WITHOUT EVIDENCE = True
              its Status: '- Status: executed'
              its E-01 : '  - Execution state: pending'

        So `setid` and `plan_path` are two SEPARATE inputs and nothing correlates them except the Kind
        gate. That is why the Kind gate is load-bearing and why this test exists: it is the one that
        fails on the widening edit with no other gate able to mask it.
        """

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared as rs

        # An ELIGIBLE Set, whose verdict an attacker would like to borrow.
        self.make_set("clean", [("aaa111", 1, "executed", "executed")])
        self.assertTrue(rs.evaluate_set_retirement(self.root, "clean").eligible)
        # The victim: approved, pending, evidence-free, and in a DIFFERENT Set.
        victim = _write_conforming_plan(
            self.root,
            "pending",
            plan_id="vvv999",
            set_id="other",
            order=1,
            status="approved",
            kind="child",
        )
        import subprocess

        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "victim"], cwd=self.root, check=True
        )
        before = victim.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", before)
        self.assertIn("- Execution state: pending", before)

        res = self.retire(victim, "clean", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        self.assertEqual(
            res.findings,
            (LC.ROLLUP_REFUSED_NOT_ORCHESTRATOR,),
            "ONLY the Kind gate can refuse this shape; if it stops refusing, an evidence-free plan "
            "reaches executed (measured: it did)",
        )
        self.assertTrue(victim.is_file(), "the victim must stay in pending/")
        self.assertEqual(victim.read_text(encoding="utf-8"), before)
        self.assertFalse(
            (
                self.root
                / ".aw/records/plans/executed/20260906-other-01-vvv999-synthetic.ipd.md"
            ).exists(),
            "an ordinary plan must never reach executed/ through the rollup route",
        )


class TheHumanFacingGateIsUNCHANGED(RollupTransitionCase):
    """V-01: `aw ipd finalize` on an orchestrator STILL faces the E/V requirement.

    This is the assertion that proves the opening is confined to the runner-owned route. If a human
    (or an agent) runs the ordinary finalize on an orchestrator, the six `IPD-S404` findings must
    still appear exactly as they do today.
    """

    def test_the_ordinary_finalize_still_refuses_an_orchestrator(self):
        """Kept separate: drives the OTHER transition path (`LC.finalize`), and mints a receipt first.

        The receipt is what makes the observed refusal the E/V CHECKPOINT rather than the receipt gate,
        which is the probe spec Section 2.3 describes.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("human", [("aaa111", 1, "executed", "executed")])
        # Mint a receipt so the refusal we observe is the E/V CHECKPOINT, not the receipt gate. This
        # is exactly the probe the spec describes at Section 2.3.
        begin = LC.begin(
            self.root, orch, "tester/probe", timestamp="2026-09-06T00:00:00Z"
        )
        self.assertEqual(begin.exit_code, LC.EXIT_OK, begin.message)
        res = LC.finalize(self.root, orch, "tester/probe", "probe", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        s404 = [f for f in res.findings if "IPD-S404" in f]
        self.assertTrue(
            s404, f"the E/V checkpoint must still fire on the main path: {res.findings}"
        )
        self.assertTrue(orch.is_file(), "the plan must be left unmoved")

    def test_the_ordinary_finalize_still_refuses_a_child_without_evidence(self):
        """Kept separate: the CHILD-plan gate on the HUMAN-facing path, stated so it cannot regress.

        Not a row in `GATES`, which drives the ROLLUP route: this drives `LC.finalize`, i.e. what a
        human or agent runs by hand, and the property is that the rollup's exemption did not leak into
        it.
        """

        from agent_workflows import ipd_lifecycle as LC

        self.make_set("kidgate", [("aaa111", 1, "approved", "pending")])
        child = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260906-kidgate-01-aaa111-synthetic.ipd.md"
        )
        res = LC.finalize(self.root, child, "tester/probe", "probe", apply=True)
        self.assertNotEqual(res.exit_code, LC.EXIT_OK)
        self.assertTrue(child.is_file())


class TheHonestTerminalRecord(RollupTransitionCase):
    """V-04 (spec R-4): the history entry says RETIRED, names the run and the children."""

    def _retired_text(self, setid: str = "hist") -> str:
        orch = self.make_set(
            setid,
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
        )
        res = self.retire(orch, setid, apply=True)
        self.assertEqual(res.exit_code, 0, f"{res.message} {res.findings}")
        return (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / f"20260906-{setid}-00-orc000-synthetic.ipd.md"
        ).read_text(encoding="utf-8")

    def test_the_entry_names_the_rollup_the_run_and_the_children(self):
        text = self._retired_text()
        line = next(
            ln
            for ln in text.splitlines()
            if ln.startswith("- ") and " executed (" in ln
        )
        self.assertIn("RETIRED", line)
        self.assertIn("rollup", line)
        self.assertIn("run-20260906T000000Z-1", line)
        self.assertIn("aaa111", line)
        self.assertIn("bbb222", line)

    def test_the_entry_does_NOT_claim_the_orchestrators_own_items_were_performed(self):
        """R-4's prohibition, asserted positively: it must say they were NOT performed."""

        text = self._retired_text("nope")
        line = next(
            ln
            for ln in text.splitlines()
            if ln.startswith("- ") and " executed (" in ln
        )
        self.assertIn("NOT performed", line)
        self.assertIn("not executed by an agent", line)
        # The forbidden claims, chosen so each is a SUBSTRING-SAFE positive assertion of execution.
        # Note "executed by an agent" alone would be a FALSE positive here, because the honest
        # sentence contains it as "NOT executed by an agent"; a negative substring test has to be
        # written against phrasings the honest text cannot contain.
        for claim in (
            "all E-* performed",
            "every V-* verified",
            "was executed by an agent",
            "validated by an agent",
        ):
            with self.subTest(claim=claim):
                self.assertNotIn(claim, line)
        # And the plan's own E/V rows are untouched: nothing was back-filled to fake evidence.
        self.assertIn("- Execution state: pending", text)
        self.assertIn("- Result: pending", text)
        self.assertIn("- [ ] E-01", text)

    def test_the_actor_passes_the_attribution_lint(self):
        """F-4: today's `aw oc run (orchestrator rollup)` actor MISPARSES and would fail here."""

        from agent_workflows import ipd_lint as L
        from agent_workflows import ipd_schema as S

        setid = "attrib"
        orch = self.make_set(setid, [("aaa111", 1, "executed", "executed")])
        res = self.retire(orch, setid, apply=True)
        self.assertEqual(res.exit_code, 0, f"{res.message} {res.findings}")
        dest = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / f"20260906-{setid}-00-orc000-synthetic.ipd.md"
        )
        lint = L.lint_file(dest, checkpoint="post-transition")
        attribution = [d for d in lint.diagnostics if d.code == "IPD-S406"]
        self.assertEqual(
            attribution,
            [],
            f"attribution lint failed: {[d.message for d in lint.diagnostics]}",
        )
        self.assertEqual(
            lint.disposition,
            S.DISPOSITION_CONFORMING,
            [f"{d.code} {d.message}" for d in lint.diagnostics],
        )

    def test_a_parenthesized_actor_is_refused_BEFORE_any_mutation(self):
        """Refuse early rather than commit and then fail post-transition lint.

        The alternative is worse than it sounds: the attribution failure happens AFTER the lifecycle
        commit, leaving the transaction `committed-incomplete`, which is a state a human has to
        resolve. The exact string is today's, from `oc_runipd.finalize_orchestrator`.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("paren", [("aaa111", 1, "executed", "executed")])
        head = _git(self.root, "rev-parse", "HEAD").strip()
        res = self.retire(
            orch, "paren", apply=True, actor="aw oc run (orchestrator rollup)"
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("parenthesis", res.message)
        self.assertTrue(orch.is_file())
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)

    def test_the_message_helper_is_pure_and_states_the_three_required_facts(self):
        from agent_workflows import ipd_lifecycle as LC

        msg = LC.rollup_history_message(
            setid="s1", run_id="run-x", children=["c1", "c2"]
        )
        self.assertIn("RETIRED", msg)
        self.assertIn("s1", msg)
        self.assertIn("run-x", msg)
        self.assertIn("c1, c2", msg)
        self.assertIn("NOT performed", msg)
        # A run id is not always available (a hand-invoked retirement); it must still be honest
        # rather than fabricate one.
        self.assertIn(
            "unrecorded run",
            LC.rollup_history_message(setid="s1", run_id=None, children=["c1"]),
        )


class NoReceiptIsRequiredAndNoneIsLeftBehind(RollupTransitionCase):
    """V-03 (spec R-6): the receipt gate is resolved, and no false evidence is created."""

    def test_the_rollup_succeeds_with_NO_begin_receipt(self):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("norcpt", [("aaa111", 1, "executed", "executed")])
        self.assertFalse(LC.receipt_path_for(self.root, "orc000").exists())
        res = self.retire(orch, "norcpt", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        self.assertNotIn("no begin receipt", res.message)

    def test_NO_receipt_is_minted_so_nothing_claims_an_execution_that_did_not_happen(
        self,
    ):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("nomint", [("aaa111", 1, "executed", "executed")])
        res = self.retire(orch, "nomint", apply=True)
        self.assertEqual(res.exit_code, 0, res.message)
        self.assertFalse(
            LC.receipt_path_for(self.root, "orc000").exists(),
            "a rollup must not leave a receipt asserting the orchestrator was executed",
        )
        rdir = LC.receipt_dir(self.root)
        leftovers = (
            [p.name for p in rdir.iterdir() if "orc000" in p.name]
            if rdir.is_dir()
            else []
        )
        self.assertEqual(leftovers, [])

    def test_the_scope_delta_consequence_is_RECORDED_not_merely_true(self):
        """Dropping the receipt drops `base_head`, hence the whole scope reconciliation.

        R-6 lists two options and mentions neither this consequence nor its justification, which is
        precisely why it must be written down where a reader will find it instead of rediscovered.
        """

        from agent_workflows import ipd_lifecycle as LC

        self.assertIn("scope-delta-reconciliation", LC.ROLLUP_OMITTED_GATES)
        reason = LC.ROLLUP_OMITTED_GATES["scope-delta-reconciliation"]
        self.assertIn("base_head", reason)
        self.assertIn("no scope reconciliation", reason)
        self.assertIn("begin-receipt-requirement", LC.ROLLUP_OMITTED_GATES)

    def test_a_DIRTY_orchestrator_file_is_refused_which_is_what_makes_that_safe(self):
        """The one part of "a rollup edits nothing" that could be false, verified not assumed.

        Committing a dirty plan file would sweep another party's in-flight edit into a lifecycle
        commit and attribute it to the runner. With no receipt there is no `base_head` and therefore
        no scope delta to catch it, so the check has to be here.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("dirty", [("aaa111", 1, "executed", "executed")])
        orch.write_text(
            orch.read_text(encoding="utf-8") + "\nsomeone else was editing this\n",
            encoding="utf-8",
        )
        head = _git(self.root, "rev-parse", "HEAD").strip()
        res = self.retire(orch, "dirty", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        self.assertIn(LC.ROLLUP_REFUSED_UNOWNED_EDIT, res.findings)
        self.assertIn("someone else", orch.read_text(encoding="utf-8"))
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)

    def test_a_clean_rollup_changes_nothing_outside_its_owned_lifecycle_paths(self):
        """The positive form of the same property: the commit's paths ARE the owned set."""

        orch = self.make_set("owned", [("aaa111", 1, "executed", "executed")])
        res = self.retire(orch, "owned", apply=True)
        self.assertEqual(res.exit_code, 0, res.message)
        assert res.commit is not None
        # `--no-renames` so a rename is reported as delete+add rather than collapsed to the
        # destination alone; the ORIGIN path is half of what "the plan moved" means, and git's default
        # rename detection would hide it.
        changed = set(
            _git(
                self.root,
                "show",
                "--name-only",
                "--no-renames",
                "--format=",
                res.commit,
            ).split()
        )
        expected = {
            ".aw/records/plans/pending/20260906-owned-00-orc000-synthetic.ipd.md",
            ".aw/records/plans/executed/20260906-owned-00-orc000-synthetic.ipd.md",
        }
        self.assertTrue(
            expected <= changed, f"expected the plan move; got {sorted(changed)}"
        )
        # The plan move is the WHOLE commit: there are no other paths at all. Asserted as an exact
        # set rather than by prefix, so a rollup that started committing some other plans-tree file
        # would fail here.
        self.assertEqual(changed - expected, set(), sorted(changed))
        # In particular the GENERATED plans manifests are absent. They are still refreshed on disk
        # by the transaction (`_refresh_plans_index_fail_loud`), but generated output is no longer
        # committed by any `aw` verb, so committing one here would be the regression (idxuntrack
        # `4r0qp1` E-01).
        self.assertNotIn(".aw/records/plans/INDEX.json", changed)
        self.assertNotIn(".aw/records/plans/INDEX.md", changed)


class TheWorkerRoleIsRefused(RollupTransitionCase):
    """V-06 (E-06): the refusal is NOT inherited, so it is asserted on THIS path.

    `worker_role_active` is called in the CLI wrappers `run_begin` (`ipd_lifecycle.py:2223`) and
    `run_finalize` (`:2403`), NOT inside `finalize()`. A new transition function therefore starts with
    NO role guard at all, and a managed worker could create lifecycle authority through it. Only a
    test on this path can show the guard is actually here.
    """

    def test_a_worker_role_rollup_performs_NO_transition(self):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("wrole", [("aaa111", 1, "executed", "executed")])
        before = orch.read_text(encoding="utf-8")
        head = _git(self.root, "rev-parse", "HEAD").strip()
        res = self.retire(
            orch,
            "wrole",
            apply=True,
            env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER},
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertIn("AW-LIFECYCLE-ROLE-001", res.message)
        self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res.findings)
        # NO side effect whatsoever: not moved, not rewritten, not committed.
        self.assertTrue(orch.is_file())
        self.assertEqual(orch.read_text(encoding="utf-8"), before)
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)
        self.assertEqual(_git(self.root, "status", "--porcelain").strip(), "")

    def test_the_coordinator_role_is_UNAFFECTED(self):
        """The guard must not break the path it protects."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("crole", [("aaa111", 1, "executed", "executed")])
        for env in ({}, {LC.EXECUTION_ROLE_ENV: "coordinator"}):
            with self.subTest(env=env):
                res = self.retire(orch, "crole", apply=False, env=env)
                self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

    def test_the_refusal_is_the_FIRST_gate_so_it_cannot_leak_through_another(self):
        """Refused even when EVERYTHING else about the call is invalid.

        If the role check ran late, a worker could still reach selector resolution and the gates
        beyond it. Asserting the role reason wins over an invalid actor AND a non-orchestrator target
        pins its position without asserting a line number.
        """

        from agent_workflows import ipd_lifecycle as LC

        self.make_set("first", [("aaa111", 1, "executed", "executed")])
        child = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260906-first-01-aaa111-synthetic.ipd.md"
        )
        res = self.retire(
            child,
            "first",
            apply=True,
            actor="",
            env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER},
        )
        self.assertIn(LC.ROLLUP_REFUSED_WORKER_ROLE, res.findings)
        self.assertNotIn(LC.ROLLUP_REFUSED_NOT_ORCHESTRATOR, res.findings)

    def test_it_reuses_the_ONE_canonical_refusal_message(self):
        """The rollup's refusal is BUILT FROM `LIFECYCLE_ROLE_ERROR`, proven by patching it.

        REPLACES A SOURCE-TEXT PIN. This test used to assert that the strings `LIFECYCLE_ROLE_ERROR`
        and `worker_role_active` appeared in `inspect.getsource(LC.retire_orchestrator)`. That is a
        change detector: it passes if the names appear in a COMMENT, it breaks on a rename that
        changes nothing, and it cannot distinguish "reuses the constant" from "happens to mention
        it" or from a faithful COPY of its text, which is the exact drift being guarded against.

        WHAT REPLACES IT DRIVES THE CODE. The constant is patched to a sentinel and the rollup is
        run as a worker; the sentinel must appear in the refusal message. A hardcoded second wording
        cannot produce it, and neither can a copy of the original text, so this fails on precisely
        the drift the old pin claimed to catch while surviving any renaming or reformatting.

        The unpatched half is `test_a_worker_role_rollup_performs_NO_transition`, which pins that the
        real code `AW-LIFECYCLE-ROLE-001` reaches the operator.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        sentinel = "AW-SENTINEL-ROLE-PATCHED: this text exists only in the constant"
        orch = self.make_set("canon", [("aaa111", 1, "executed", "executed")])
        with mock.patch.object(LC, "LIFECYCLE_ROLE_ERROR", sentinel):
            res = self.retire(
                orch,
                "canon",
                apply=True,
                env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER},
            )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertIn(
            sentinel,
            res.message,
            "the rollup's worker-role refusal does NOT read the canonical "
            "`LIFECYCLE_ROLE_ERROR` constant: patching the constant left the message unchanged, so "
            "the rollup carries a SECOND wording that can drift from the one every other lifecycle "
            f"verb reports. Observed message: {res.message!r}",
        )
        self.assertIn(
            LC.ROLLUP_REFUSED_WORKER_ROLE,
            res.findings,
            "the typed finding must accompany the message, or a caller cannot detect the cause "
            "without string matching",
        )


class TheSharedGatesActuallyFireOnTheRollupPath(RollupTransitionCase):
    """V-02, the BEHAVIORAL half: the gates are not merely declared and called, they WORK here.

    `GateParityBetweenTheTwoPaths` asserts the declaration and the shared call sites, which is a
    source-level claim. These tests exercise the gates at RUNTIME on the rollup path, because "the
    function name appears in the source" and "the lock is actually held while the plan moves" are
    different claims and only the second one protects a concurrent runner.
    """

    def test_a_LIVE_finalize_lock_blocks_the_rollup(self):
        """The exclusive lock, exercised rather than inspected.

        This is the gate an earlier draft's five-item list omitted. The rollup runs inside a live
        runner that may be finalizing a child at the same moment, in a checkout shared with other
        agents, so a lockless rollup could interleave with that child's own transaction.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("locked", [("aaa111", 1, "executed", "executed")])
        # A DIFFERENT live process (this test's parent pid is alive by construction) holding the lock.
        # Written through the real accessor so the file shape cannot drift from what the lock reader
        # expects.
        lock = LC.finalize_lock_path(self.root)
        lock.parent.mkdir(parents=True, exist_ok=True)
        import json
        import os

        lock.write_text(
            json.dumps({"plan_id": "someone-else", "pid": os.getppid()}),
            encoding="utf-8",
        )
        res = self.retire(orch, "locked", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertIn("writer lock held by active PID", res.message)
        self.assertTrue(orch.is_file(), "a lock-refused rollup must not move the plan")

    def test_the_transaction_journal_is_written_and_cleared(self):
        """The two-phase journal: present during the transaction, absent after a clean COMPLETE."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("journal", [("aaa111", 1, "executed", "executed")])
        seen: list[str] = []
        real = LC._write_finalize_journal

        def spy(repo_root, journal):
            seen.append(journal.get("phase", "?"))
            return real(repo_root, journal)

        from unittest import mock

        with mock.patch.object(LC, "_write_finalize_journal", spy):
            res = self.retire(orch, "journal", apply=True)
        self.assertEqual(res.exit_code, 0, res.message)
        # The real phase progression, not a subset chosen to pass.
        for phase in (
            LC.PHASE_PREPARED,
            LC.PHASE_MUTATING,
            LC.PHASE_READY_TO_COMMIT,
            LC.PHASE_COMMITTED_INCOMPLETE,
            LC.PHASE_COMPLETE,
        ):
            self.assertIn(
                phase, seen, f"the rollup skipped journal phase {phase}: {seen}"
            )
        self.assertFalse(
            LC.finalize_journal_path(self.root, "orc000").exists(),
            "a completed transaction must clear its journal",
        )

    def test_an_injected_pre_commit_FAULT_rolls_the_rollup_back(self):
        """The journal is load-bearing, not decorative: a mid-transaction failure restores state.

        THE TREE-STATE ASSERTION IS THE POINT OF PLAN `4xt6u4`, and its absence is why a real defect
        lived here unnoticed. This test already asserted the plan's restoration, the destination's
        removal and HEAD, all of which PASSED while the rollback left
        `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md` behind in a tree that
        had neither: its own step 4 regenerated the manifests instead of leaving them as it found
        them. Four assertions about the right thing cannot substitute for one about the tree.

        IT COMPARES AGAINST THE CAPTURED PRE-ATTEMPT STATUS RATHER THAN ASSERTING EMPTINESS. Emptiness
        happens to hold in this fixture, which is exactly what makes it the wrong property: it would
        also pass if the rollback destroyed unrelated state, and it would break the moment a fixture
        legitimately carried dirt. Equality says the thing the rollback actually promises - the tree
        is as it was found.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("faulty", [("aaa111", 1, "executed", "executed")])
        before = orch.read_text(encoding="utf-8")
        head = _git(self.root, "rev-parse", "HEAD").strip()
        status_before = _git(self.root, "status", "--porcelain")
        res = self.retire(orch, "faulty", apply=True, fault_injection="after_move")
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertIn("rolled back", res.message)
        self.assertTrue(orch.is_file(), "rollback must restore the plan to pending/")
        self.assertEqual(orch.read_text(encoding="utf-8"), before)
        self.assertFalse(
            (
                self.root
                / ".aw/records/plans/executed/20260906-faulty-00-orc000-synthetic.ipd.md"
            ).exists()
        )
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)
        self.assertEqual(
            _git(self.root, "status", "--porcelain"),
            status_before,
            "a FAILED retirement changed the shared checkout: the rollback must leave the tree "
            "exactly as it found it (plan 4xt6u4 measured it leaving ?? INDEX.json / ?? INDEX.md "
            "behind, because its step 4 regenerated the manifests instead of not touching them)",
        )

    def test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt(self):
        """Early crash recovery on THIS path, using the shared helper.

        A previous rollup that died mid-mutation leaves a pre-commit journal. The next attempt must
        finish that rollback idempotently and then proceed, rather than building on half-mutated state.

        THE TREE-STATE CHECK HERE IS AT THE MIDPOINT, DELIBERATELY, and plan `4xt6u4` F-9 is why. An
        earlier draft of that plan wanted a `git status --porcelain` EMPTINESS assertion at the END of
        this test. That would pin a FALSE property: this test's subject is crash RECOVERY and its last
        act is a SUCCESSFUL retirement, which legitimately regenerates the manifests. MEASURED
        post-fix at all three points of this sequence: `''` before anything, `''` after the failed
        attempt, and `?? INDEX.json` + `?? INDEX.md` after the successful retry. So the comparison
        belongs BETWEEN the two retirements, where the subject is the ROLLBACK, and it is an equality
        against the captured pre-attempt status rather than an emptiness claim.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("recov", [("aaa111", 1, "executed", "executed")])
        status_before = _git(self.root, "status", "--porcelain")
        first = self.retire(orch, "recov", apply=True, fault_injection="before_commit")
        self.assertEqual(first.exit_code, LC.EXIT_CANNOT_RUN, first.message)
        self.assertTrue(orch.is_file())
        # MIDPOINT: the failed attempt rolled back, so the tree must be as it was found. Sampled HERE
        # and not at the end, because the successful retry below legitimately changes the manifests.
        self.assertEqual(
            _git(self.root, "status", "--porcelain"),
            status_before,
            "the rolled-back first attempt left residue in the shared checkout",
        )
        # Now a clean retry succeeds, which is the property that matters: the failure was recoverable.
        second = self.retire(orch, "recov", apply=True)
        self.assertEqual(second.exit_code, LC.EXIT_OK, second.message)
        self.assertTrue(
            (
                self.root
                / ".aw/records/plans/executed/20260906-recov-00-orc000-synthetic.ipd.md"
            ).is_file()
        )

    def test_a_FAILING_plans_index_refresh_fails_the_whole_transaction(self):
        """Fail-loud, not the `status_set` swallow: a stale index still FAILS the transaction.

        WHAT CHANGED, AND WHY IT IS NOT A WEAKENING (plan `u23gbn` E-07). The refresh used to run
        INSIDE the mutating phase, so a failure rolled back and HEAD was unmoved. It now runs AFTER
        the reconciliation, because the relocation happens in a coordinator-owned worktree and the
        SHARED disk still shows the plan at `pending/` during the mutating phase: refreshing there
        generated a manifest describing the OLD layout, converged against it, and the gate PASSED,
        after which the merge relocated the file and the manifest was instantly stale. That INVERTED
        the gate into a false pass leaving `check.stale-index-stale` unreported.

        So the gate is still FAIL-LOUD and still refuses; what moved is the classification. The
        lifecycle commit has LANDED by the time the refresh runs, so the outcome is
        COMMITTED-INCOMPLETE and the commit is deliberately NOT reverted (a landed lifecycle commit is
        resumed, never rolled back), with a mechanical local remedy because the manifests are
        gitignored generated views.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("idx", [("aaa111", 1, "executed", "executed")])
        head = _git(self.root, "rev-parse", "HEAD").strip()
        with mock.patch.object(
            LC, "_refresh_plans_index_fail_loud", side_effect=RuntimeError("index boom")
        ):
            res = self.retire(orch, "idx", apply=True)
        self.assertNotEqual(res.exit_code, LC.EXIT_OK)
        self.assertIn("index boom", res.message)
        # NOT reported as success, and recorded as committed-incomplete rather than rolled back.
        self.assertIn("COMMITTED-INCOMPLETE", res.message)
        journal = LC.read_finalize_journal(self.root, "orc000")
        assert journal is not None
        self.assertEqual(journal["phase"], LC.PHASE_COMMITTED_INCOMPLETE)
        # The commit LANDED, so HEAD moved and the plan is at its executed/ path. Reverting it is
        # exactly what `_resume_post_commit` refuses to do.
        self.assertNotEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)
        self.assertEqual(res.commit, _git(self.root, "rev-parse", "HEAD").strip())
        self.assertTrue(
            (
                self.root
                / ".aw/records/plans/executed/20260906-idx-00-orc000-synthetic.ipd.md"
            ).is_file()
        )

    def test_post_transition_lint_gates_the_rollup_too(self):
        """The honesty checker still runs; the rollup skips only the PRE-transition E/V checkpoint."""

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import ipd_lint as L

        orch = self.make_set("postl", [("aaa111", 1, "executed", "executed")])
        real = L.lint_file

        def failing(path, checkpoint="author", **kw):
            if checkpoint == "post-transition":
                return L.LintResult(
                    "error",
                    [
                        L.Diagnostic(
                            0, 0, "IPD-TEST", "injected post-transition failure"
                        )
                    ],
                )
            return real(path, checkpoint=checkpoint, **kw)

        with mock.patch.object(L, "lint_file", failing):
            res = self.retire(orch, "postl", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS, res.message)
        self.assertIn("COMMITTED-INCOMPLETE", res.message)

    def test_an_empty_actor_is_refused(self):
        """Kept separate: sweeps two blank actor spellings, and the refusal is EXIT_CANNOT_RUN.

        A different exit class from the gate refusals above (`EXIT_CANNOT_RUN`, not `EXIT_FINDINGS`),
        because an unusable actor means the call itself cannot proceed rather than that the plan was
        judged ineligible.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("noactor", [("aaa111", 1, "executed", "executed")])
        for actor in ("", "   "):
            with self.subTest(actor=actor):
                res = self.retire(orch, "noactor", apply=True, actor=actor)
                self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
                self.assertIn("non-empty --actor", res.message)
                self.assertTrue(orch.is_file())


class GateParityBetweenTheTwoPaths(unittest.TestCase):
    """V-02: pin the ACCEPTED COST of shape (b) - two paths can DRIFT.

    The maintainer chose a separate transition over a linter exemption and accepted drift as its known
    risk. This class is what makes that risk DETECTABLE rather than latent. It enumerates the shared
    gates BY NAME rather than by inspecting control flow, because the failure mode being defended
    against is precisely a gate silently missing from one path.

    THE ENUMERATION IS DELIBERATELY LONGER THAN THE OBVIOUS FIVE. An earlier draft listed status
    legality, the plan move, the index refresh, the commit and post-transition lint. `finalize` also
    takes an EXCLUSIVE LOCK, writes a two-phase JOURNAL, performs EARLY CRASH RECOVERY and refuses an
    empty actor. A drift test built from the short list would pass while the rollup ran lockless and
    journal-less inside a live runner in a shared checkout.
    """

    #: Every gate that MUST appear in `ROLLUP_SHARED_GATES`, with the `ipd_lifecycle` evidence for why
    #: it is a real gate on the main path. Written out here so this test is readable as the contract.
    _REQUIRED_SHARED = {
        "worker-role-refusal": "run_begin/run_finalize check worker_role_active",
        "actor-and-message-required": "finalize refuses an empty actor/message",
        "early-crash-recovery": "finalize resumes/rolls back a prior journal first",
        "exclusive-finalize-lock": "acquire_finalize_lock, released in finally",
        "transaction-journal": "PHASE_PREPARED..PHASE_COMPLETE two-phase journal",
        "status-legality": "checkpoint_allows_status('pre-transition', ...)",
        "plan-move": "status_set.apply_status_change moves the plan",
        "plans-index-refresh-fail-loud": "_refresh_plans_index_fail_loud raises",
        "path-scoped-lifecycle-commit": "git commit -- <owned_paths>",
        "post-transition-lint": "_complete_after_commit lints post-transition",
        # plan `u23gbn` E-06. Listed HERE, in the contract table, for the same reason the lock and the
        # journal are: it is the step whose REFUSAL protects a co-worker's uncommitted bytes, so a
        # change that forced it (or that advanced the ref some other way, making it a no-op) would
        # remove the protection while every other assertion in this file still passed.
        "refusing-fast-forward-reconciliation": (
            "land_worktree_commit runs `git merge --ff-only` as the SINGLE branch advance and "
            "REFUSES rather than clobbering"
        ),
    }

    def test_every_required_gate_is_declared_shared(self):
        from agent_workflows import ipd_lifecycle as LC

        missing = sorted(set(self._REQUIRED_SHARED) - set(LC.ROLLUP_SHARED_GATES))
        self.assertEqual(
            missing,
            [],
            "the rollup path dropped a gate the main path performs: "
            + "; ".join(f"{g} ({self._REQUIRED_SHARED[g]})" for g in missing),
        )

    def test_the_lock_journal_recovery_and_index_refresh_are_all_named(self):
        """Called out separately because these four are the ones a short list omits."""

        from agent_workflows import ipd_lifecycle as LC

        for gate in (
            "exclusive-finalize-lock",
            "transaction-journal",
            "early-crash-recovery",
            "plans-index-refresh-fail-loud",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, LC.ROLLUP_SHARED_GATES)

    def test_every_omitted_gate_carries_a_REASON(self):
        """A gate may be omitted only with a justification; that is the whole discipline."""

        from agent_workflows import ipd_lifecycle as LC

        for gate, reason in LC.ROLLUP_OMITTED_GATES.items():
            with self.subTest(gate=gate):
                self.assertTrue(reason.strip(), f"{gate} is omitted with no reason")
                self.assertGreater(
                    len(reason), 120, f"{gate}'s reason is too thin to be a reason"
                )

    def test_the_only_omitted_gates_are_the_ev_checkpoint_and_its_consequences(self):
        """R-5 permits skipping the E/V checkpoint. Nothing else may quietly join it."""

        from agent_workflows import ipd_lifecycle as LC

        self.assertEqual(
            set(LC.ROLLUP_OMITTED_GATES),
            {
                "pre-transition-ev-checkpoint",
                "begin-receipt-requirement",
                "scope-delta-reconciliation",
            },
        )

    def test_shared_and_omitted_are_disjoint(self):
        from agent_workflows import ipd_lifecycle as LC

        self.assertEqual(
            set(LC.ROLLUP_SHARED_GATES) & set(LC.ROLLUP_OMITTED_GATES), set()
        )


class TheSharedGatesAreSharedAsCODE(RollupTransitionCase):
    """The two claims `GateParityBetweenTheTwoPaths` could only make about SOURCE TEXT, made by
    DRIVING both paths instead.

    Split from that class because these need the git-backed fixture: proving a gate is shared requires
    RUNNING both transitions, where the declaration tests above only read module constants.
    """

    def _evidenced_child(self, setid: str) -> Path:
        """A committed child plan whose `E-01`/`V-01` are PERFORMED and evidenced.

        The ordinary `make_set` fixture leaves those rows `pending`, deliberately, because the
        ROLLUP's whole point is retiring a plan nobody executed. The main path is the opposite: its
        pre-transition E/V checkpoint refuses such a plan before taking the lock or opening the
        transaction, so a shared-gate count taken against it would be zero for a reason unrelated to
        sharing. Back-filling the rows here is what lets `finalize` run to completion.
        """

        import subprocess

        child = _write_conforming_plan(
            self.root,
            "pending",
            plan_id="bbb222",
            set_id=setid,
            order=1,
            status="approved",
            kind="child",
        )
        text = child.read_text(encoding="utf-8")
        text = (
            text.replace("- [ ] E-01", "- [x] E-01")
            .replace("- Execution state: pending", "- Execution state: performed")
            .replace("- [ ] V-01", "- [x] V-01")
            .replace(
                "- Observed evidence:",
                "- Observed evidence: verified by running the probe; output recorded.",
            )
            .replace("- Result: pending", "- Result: pass")
        )
        child.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "evidenced child"], cwd=self.root, check=True
        )
        return child

    #: (the shared helper's attribute name on `ipd_lifecycle`, why sharing it matters)
    SHARED_CALLS = (
        (
            "_early_recovery_result",
            "a prior crashed transaction's journal must be resumed or rolled back BEFORE a fresh "
            "attempt, or the new attempt builds on half-mutated state",
        ),
        (
            "acquire_finalize_lock",
            "the rollup runs inside a live runner that may be finalizing a CHILD at the same moment, "
            "in a checkout shared with other agents, so a lockless rollup interleaves with that "
            "child's own transaction",
        ),
        (
            "_finalize_transaction",
            "the plan move, the path-scoped commit and the index refresh all live here; a private "
            "copy in the rollup is the drift this exists to prevent",
        ),
    )

    def test_both_paths_call_the_SAME_shared_gate_functions(self):
        """Patching one shared helper must be OBSERVED BY BOTH paths, proving they call it.

        REPLACES TWO SOURCE-TEXT PINS. This test used to read
        `inspect.getsource(LC.retire_orchestrator)` and `inspect.getsource(LC.finalize)` and assert
        that four helper NAMES appeared in both, while a sibling asserted that `'"commit"'`,
        `apply_status_change` and `shutil.move` did NOT appear in the rollup's source. Both were
        change detectors: they passed on a name in a COMMENT, broke on any rename or reformat, and
        could not tell "calls the shared function" apart from "contains a copy of its body", which is
        exactly the drift the class exists to detect.

        WHAT REPLACES THEM IS A PATCH. Each shared helper is replaced by a spy that records which
        path invoked it and then delegates, and BOTH paths are driven for real: the rollup via
        `retire_orchestrator`, the main path via `LC.finalize`. A faithful copy of the helper's body
        cannot record a call, so a re-implementation fails here; a rename cannot break it, because
        the attribute is resolved through the module rather than matched as text.

        WHY THIS IS STRICTLY STRONGER: the old pin would have passed if the rollup had contained a
        private copy of `_finalize_transaction`'s body while merely MENTIONING the name in a comment.
        This cannot.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        wrong = []
        for name, why in self.SHARED_CALLS:
            observed = {"rollup": 0, "finalize": 0}
            real = getattr(LC, name)
            current = {"path": None}

            def spy(*args, _real=real, _observed=observed, _current=current, **kwargs):
                if _current["path"] is not None:
                    _observed[_current["path"]] += 1
                return _real(*args, **kwargs)

            with mock.patch.object(LC, name, spy):
                # THE ROLLUP PATH, on an eligible Set, applied for real.
                orch = self.make_set(
                    f"sh{name[:4].strip('_')}", [("aaa111", 1, "executed", "executed")]
                )
                current["path"] = "rollup"
                rollup_res = self.retire(orch, f"sh{name[:4].strip('_')}", apply=True)
                # THE MAIN PATH, on a FULLY EVIDENCED child, which is what makes this half
                # meaningful: a child whose items are `pending` is refused by the pre-transition E/V
                # CHECKPOINT before the lock or the transaction is ever reached, so the counts would
                # be zero for a reason that has nothing to do with sharing.
                child = self._evidenced_child(f"m{name[:3].strip('_')}")
                current["path"] = "finalize"
                begin = LC.begin(
                    self.root, child, "tester/probe", timestamp="2026-09-06T00:00:00Z"
                )
                main_res = LC.finalize(
                    self.root, child, "tester/probe", "probe", apply=True
                )
                current["path"] = None

            problems = []
            if rollup_res.exit_code != LC.EXIT_OK:
                problems.append(
                    f"fixture sanity: the rollup did not succeed, so its call count is not "
                    f"meaningful: {rollup_res.message} {rollup_res.findings}"
                )
            if begin.exit_code != LC.EXIT_OK:
                problems.append(
                    f"fixture sanity: `begin` refused on the main path, so `finalize` never got far "
                    f"enough to reach any shared gate: {begin.message}"
                )
            if main_res.exit_code != LC.EXIT_OK:
                problems.append(
                    f"fixture sanity: the MAIN path did not succeed, so its call count reflects an "
                    f"early refusal rather than a dropped gate: {main_res.message} "
                    f"{main_res.findings}"
                )
            if observed["rollup"] == 0:
                problems.append(
                    "the ROLLUP path never called it, so `retire_orchestrator` performs this gate "
                    "itself (or skips it); a private copy is invisible to the main path's tests"
                )
            if observed["finalize"] == 0:
                problems.append(
                    "the MAIN path never called it, so if `finalize` genuinely dropped this gate, "
                    "decide deliberately whether the rollup should too and update "
                    "ROLLUP_SHARED_GATES either way"
                )
            if problems:
                wrong.append(
                    f"  {name} (observed {observed}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this gate is shared because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SHARED_CALLS)} gates are no longer shared AS CODE by both "
            "transition paths. Sharing the FUNCTION is what removes a gate from the drift surface "
            "entirely, which is the one mitigation the maintainer accepted for choosing a separate "
            "transition over a linter exemption. FIX: a gate the ROLLUP stopped calling is the severe "
            "direction, because the rollup runs unattended inside a live runner in a shared checkout: "
            "losing `acquire_finalize_lock` lets it interleave with a child's transaction, and losing "
            "`_finalize_transaction` means it moves and commits a plan through code the main path's "
            "tests never exercise. A gate the MAIN path stopped calling is a deliberate decision "
            f"somebody must record, not a failure to fix here.\n" + "\n".join(wrong),
        )

    def test_the_rollup_performs_no_plan_move_or_commit_of_its_own(self):
        """Behavioral: make the SHARED transaction a no-op and the plan must NOT move.

        REPLACES the `assertNotIn('"commit"', src)` / `assertNotIn("apply_status_change", src)` /
        `assertNotIn("shutil.move", src)` source pin, which could be satisfied by spelling a private
        move differently (`os.replace`, `Path.rename`, `git_mv`) and broke on unrelated edits.

        THE INSTRUMENT IS A NEUTRALIZED `_finalize_transaction`: if the rollup delegates, stubbing it
        out means NOTHING happens to the plan or to HEAD. If the rollup has a private copy of the
        move or the commit, the plan moves (or HEAD advances) anyway, which is the drift.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("nomove", [("aaa111", 1, "executed", "executed")])
        before = orch.read_text(encoding="utf-8")
        head = _git(self.root, "rev-parse", "HEAD").strip()
        dest = (
            self.root
            / ".aw/records/plans/executed/20260906-nomove-00-orc000-synthetic.ipd.md"
        )

        class _Neutralized:
            ok = False
            exit_code = LC.EXIT_CANNOT_RUN
            message = "neutralized transaction: performed nothing"
            commit = None
            findings: tuple = ()

        with mock.patch.object(
            LC, "_finalize_transaction", return_value=_Neutralized()
        ):
            self.retire(orch, "nomove", apply=True)

        problems = []
        if not orch.is_file():
            problems.append(
                "the plan LEFT `pending/` even though the shared transaction did nothing, so the "
                "rollup moves the plan itself"
            )
        elif orch.read_text(encoding="utf-8") != before:
            problems.append(
                "the plan's BYTES changed even though the shared transaction did nothing, so the "
                "rollup performs its own status edit"
            )
        if dest.exists():
            problems.append(
                "the plan APPEARED at its executed/ path, so the rollup performs its own move"
            )
        if _git(self.root, "rev-parse", "HEAD").strip() != head:
            problems.append(
                "HEAD ADVANCED even though the shared transaction did nothing, so the rollup makes "
                "its own commit"
            )
        self.assertEqual(
            problems,
            [],
            "the rollup does NOT delegate the move/commit to `_finalize_transaction`:\n"
            + "".join(f"  - {p}\n" for p in problems)
            + "FIX: delegate, so the two transition paths cannot diverge. A private copy of the move "
            "or the commit is a second implementation of the most dangerous step in the lifecycle, "
            "and it would not be covered by any of the transaction's own journal, rollback or "
            "path-scoping tests.",
        )


class TheRejectedShapeWasNotTaken(unittest.TestCase):
    """The linter learned NO orchestrator exception, demonstrated BY LINTING orchestrators.

    TWO SOURCE-TEXT PINS WERE DELETED HERE AND ONE BEHAVIORAL TEST ABSORBED THEM.
    `test_the_honesty_checker_has_no_orchestrator_concept` asserted
    `ipd_lint.py`'s text contained the word "orchestrator" ZERO times, and
    `test_the_lint_module_is_not_in_this_plans_scope_paths` asserted the string `ipd_lint` was absent
    from one plan's `- Scope-Paths:` line. Both were change detectors with the same two defects: the
    first breaks if anyone so much as writes the word in a comment (and is satisfied by DELETING such
    a comment while adding a `kind == "orchestrator"` branch spelled through a variable), and the
    second asserts a historical plan's front matter rather than any behavior of the shipped code. A
    plan's scope declaration is enforced by the runner's own scope gate, not by this suite.

    WHAT REPLACES THEM IS THE CLAIM ITSELF, driven: the pre-transition E/V checkpoint must produce the
    SAME findings for an orchestrator as for a child, so the table below lints one document twice with
    only `- Kind:` changed and requires the findings to be IDENTICAL. That is what "no Kind-aware
    exception" means operationally, and unlike a word count it cannot be satisfied by an edit to prose.

    WHY THE SHAPE WAS REJECTED, so the test is not mistaken for pedantry: the maintainer refused a
    linter exemption (spec `77tr3o` OQ-1 shape (a)) because a safety check that learns one narrow
    exception is how it quietly stops protecting anything. The exemption lives in the RUNNER-owned
    transition instead, where it is gated on an on-disk eligibility verdict.
    """

    #: (case, the `- Kind:` value, why this row exists)
    KINDS = (
        (
            "an ORCHESTRATOR with an unperformed E-01",
            "orchestrator",
            "THE ROW THE REJECTED SHAPE WOULD HAVE EXEMPTED. If the linter grew a Kind-aware "
            "exception, this is the document that would stop being flagged, and every orchestrator "
            "could then reach `executed` through the ORDINARY human-facing finalize with no evidence",
        ),
        (
            "a CHILD with an identical unperformed E-01",
            "child",
            "THE CONTROL. It fixes what the orchestrator row is compared against, so the assertion "
            "can be 'the findings are the SAME' rather than 'some finding appeared', which a "
            "half-exemption could still satisfy",
        ),
        (
            "a plan with NO `- Kind:` bullet at all",
            None,
            "the legacy shape (74 plans in this repo carry `Order: 0` and no `Kind:`), so a "
            "Kind-dispatching linter cannot take a third path for an absent value either",
        ),
    )

    def test_the_pre_transition_ev_requirement_is_identical_for_every_kind(self):
        from agent_workflows import ipd_lint as L

        body = (
            "## Detailed Implementation Checklist (TODO)\n\n"
            "- [ ] E-01 do a thing.\n"
            "  - Depends on: none\n"
            "  - Expected outcome: x\n"
            "  - Execution state: pending\n"
        )
        results = {}
        wrong = []
        for case, kind, why in self.KINDS:
            text = _plan_text(
                plan_id="orc000",
                set_id="s",
                order=0,
                status="approved",
                kind=kind or "child",
                body=body,
            )
            if kind is None:
                text = text.replace("- Kind: child\n", "")
            diags = L.check_checkpoint(L.parse(text), "pre-transition", "pending")
            messages = sorted(d.message for d in diags)
            results[case] = messages
            if not any("E-01" in m and "performed" in m for m in messages):
                wrong.append(
                    f"  {case}:\n"
                    "    - the unperformed E-01 was NOT flagged, so this plan could reach `executed` "
                    f"through the ordinary finalize with no evidence. Findings: {messages!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the pre-transition E/V checkpoint exempted {len(wrong)} of {len(self.KINDS)} plan "
            "kinds. FIX: the checkpoint must be UNCONDITIONAL. The maintainer rejected a linter "
            "exemption (spec `77tr3o` OQ-1 shape (a)) because a safety check that learns one narrow "
            "exception stops protecting anything; the orchestrator carve-out belongs in the "
            "runner-owned transition, which is gated on an on-disk eligibility verdict, and NOT "
            f"here.\n" + "\n".join(wrong),
        )
        # AND THE FINDINGS MUST BE THE SAME SET, not merely all non-empty: a linter that flagged the
        # orchestrator differently (say, advisory rather than blocking, or with a Kind-specific
        # message) would satisfy every row above while having grown exactly the Kind awareness this
        # test exists to forbid.
        distinct = {tuple(v) for v in results.values()}
        self.assertEqual(
            len(distinct),
            1,
            "the checkpoint produced DIFFERENT findings for different `- Kind:` values, so the "
            "honesty checker has become Kind-aware. The same document with only `- Kind:` changed "
            f"must lint identically. Observed: {results!r}",
        )


# ==================================================================================================
# orchretire Order 03 (`pgq326`): WIRING BOTH HOSTS' DISPATCH
#
# WHAT THIS THIRD SECTION PINS, and why it is the half that makes the previous two REACHABLE. Children
# 01 and 02 built a predicate and a transition that NOTHING CALLED: a correct mechanism that no real run
# can reach is indistinguishable, from the outside, from the broken one it replaced. So the tests below
# drive `run_queue` itself rather than the helpers, because the defect was never in a helper:
#
#   * the oc branch wrote a TERMINAL `dependency-blocked` on ANY failure, so an orchestrator whose
#     children finished LATER IN THE SAME RUN was excluded forever, from an event named
#     `orchestrator-deferred`;
#   * one `else` covered two unrelated failures, so `kxkc04`'s "leave it queued" fix was right for one
#     and would have SPUN on the other; and
#   * the agy runner had NO `orchestrate` action and no branch reading one, so `aw agy run` would have
#     spent an agent turn AUTHORING against a plan whose purpose the runner supersedes.
#
# EVERY TEST HERE RUNS ON BOTH HOSTS where the behavior is shared, because a one-host fix passes every
# oc-only test - the exact failure `818uru` recorded when a guard written for one runner let the other
# re-fork four symbols and DRIFT one of them.
#
# THE SPIN TESTS ARE NOT DEFENSIVE PADDING. `test_a_child_only_on_disk_terminates_instead_of_spinning`
# pins a loop that was MEASURED, not imagined: with the naive "reconsider unless a child is dead" rule,
# a scripted run dispatched the orchestrator 201 times without terminating, and the existing drain path
# could not catch it because the drain is reached only when NOTHING is selectable while that
# orchestrator stayed selectable forever.
# ==================================================================================================


def _dispatch_hosts():
    """(label, module) for every host that must behave identically. Both, always."""

    from agent_workflows import agy_runipd, oc_runipd

    return (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


class TheActionDecisionIsSHAREDCode(unittest.TestCase):
    """E-04/V-04: both hosts must call the SAME decider object, not merely agree today.

    Object identity rather than equal outputs, and the distinction is the whole point: two copies agree
    until one is edited, which is precisely how `Heartbeat` DRIFTED after `render_stream` was extracted
    with a one-sided guard. Equal outputs would pass against two copies.

    THIS CLASS PROVES THE DECISION ONLY. The dispatched OUTCOME is `TheAgyHostActsOnTheDecision`'s, and
    reading this class as evidence of host parity is the specific mistake `pgq326`'s gate warns about:
    before that class existed, agy DECIDED `orchestrate` and then ignored it.
    """

    def test_both_hosts_bind_the_same_decider_object(self):
        from agent_workflows import runner_shared

        for name in ("action_for", "determine_action", "dispatch_orchestrator_item"):
            objs = {label: getattr(mod, name) for label, mod in _dispatch_hosts()}
            with self.subTest(symbol=name):
                self.assertIs(
                    objs["oc_runipd"],
                    objs["agy_runipd"],
                    f"{name} must be ONE shared object, not a copy per host",
                )
                self.assertIs(
                    objs["oc_runipd"],
                    getattr(runner_shared, name),
                    f"{name} must be owned by runner_shared",
                )

    # `test_neither_host_redefines_the_decider` WAS DELETED HERE, NOT REPLACED, and the reasoning is
    # recorded because deleting a guard needs more justification than rewriting one.
    #
    # WHAT IT DID: parsed each host module with `ast` and asserted that `action_for`,
    # `determine_action` and `dispatch_orchestrator_item` did not appear as top-level `def`s.
    #
    # WHY IT IS NOT REPLACED BY A BEHAVIORAL TEST: a behavioral replacement was ATTEMPTED and does
    # not work, which is worth knowing before someone tries again. Patching
    # `runner_shared.action_for` and asking each host does NOT move the host's answer, because the
    # hosts bind the function object at IMPORT time (`from runner_shared import action_for`), so the
    # host attribute keeps pointing at the original object. The patch-observation technique used
    # elsewhere in this file works only where the call goes through a module attribute at call time.
    #
    # WHY DELETION IS SAFE: what the scan actually added over `test_both_hosts_bind_the_same_decider_object`
    # is the detection of a DEAD local definition shadowed by a later import, which is a lint concern
    # rather than a behavior, and the behavior it was standing in for is covered twice over. The
    # `assertIs` identity test proves each host's attribute IS the shared object, so no live copy can
    # exist; and `test_the_QUEUE_BUILD_derives_orchestrate_on_both_hosts` drives the real
    # `initialize_run` on BOTH hosts and asserts the `orchestrate` action FROZEN onto the queue entry,
    # which is the observable result a fork would change. A dead definition that nothing calls cannot
    # affect either.

    def test_an_approved_orchestrator_is_orchestrate_on_BOTH_hosts(self):
        """The measured asymmetry: agy returned `execute` here and would have agent-executed it."""

        for label, mod in _dispatch_hosts():
            with self.subTest(host=label):
                self.assertEqual(
                    mod.action_for("orchestrator", "approved"), "orchestrate"
                )
                self.assertEqual(
                    mod.action_for("orchestrator", "auto-approved"), "orchestrate"
                )
                # Past review, but NOT before it: a to-review orchestrator still needs its own review.
                self.assertEqual(mod.action_for("orchestrator", "to-review"), "review")
                self.assertEqual(mod.action_for("orchestrator", "draft"), "review")
                # And an ordinary plan is untouched by any of this.
                self.assertEqual(mod.action_for("child", "approved"), "execute")
                self.assertEqual(mod.action_for(None, "approved"), "execute")

    def test_the_agy_queue_entry_carries_kind(self):
        """Without `kind` on the entry the shared decider cannot see an orchestrator at all.

        Asserted through the real `build_dynamic_manifest` + `discover_plans` path rather than a
        hand-built dict, because the defect was that agy's record type had no `kind` field and nothing
        supplied it from anywhere else. rununify 06 (`sy7uwh`) gave the shared record that field, so the
        entry now gets it from `rec.kind` instead of from a per-plan re-read of the file; this test
        passed before and after that change, which is why it is the guard the change was made under.
        """

        from agent_workflows import agy_runipd, oc_runipd

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / ".aw" / "records" / "plans" / "pending"
            d.mkdir(parents=True)
            (d / "20260906-kindset-00-orck01-o.ipd.md").write_text(
                "# IPD: o\n\n- Id: orck01\n- Kind: orchestrator\n- Set: kindset\n"
                "- Order: 0\n- Status: approved\n",
                encoding="utf-8",
            )
            found = agy_runipd.discover_plans(root)
            manifest = agy_runipd.build_dynamic_manifest(root, found)
            entry = manifest["plans"]["orck01"]
            self.assertEqual(entry["kind"], "orchestrator")
            self.assertEqual(
                agy_runipd.action_for(entry["kind"], entry["status"]), "orchestrate"
            )
            # PIN TWO OF TWO, INVERTED BY rununify 06 (`sy7uwh`), which IS the "later child" that
            # `818uru` deferred the unification to. This line used to read
            # `assertNotIn("kind", agy_runipd.PlanRecord._fields)` with the comment "`818uru` pinned the
            # two as distinct and that invariant is not this plan's to break" - true when it was
            # written, and false now that `sy7uwh` has broken it deliberately and with authority. See
            # `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` for the full override record.
            #
            # EVERYTHING ABOVE THIS LINE IS UNTOUCHED ON PURPOSE. This test is the best existing
            # end-to-end guard for the silent, type-shaped failure the unification risks (a dropped
            # `kind` disables orchestrator detection without crashing), so it had to keep passing
            # BEFORE and AFTER with only this one record-shape assertion changed.
            self.assertIn("kind", agy_runipd.PlanRecord._fields)
            self.assertIs(agy_runipd.PlanRecord, oc_runipd.PlanRecord)

    def test_the_QUEUE_BUILD_derives_orchestrate_on_both_hosts(self):
        """The real `initialize_run` queue entry, not just the decider called by hand.

        THIS IS THE TEST THE OTHERS IN THIS CLASS CANNOT REPLACE, and its absence was found by
        SABOTAGE: reverting agy's queue-build line back to `determine_action(status)` left every other
        assertion here PASSING, because they read module attributes or call `action_for` directly and
        none of them observes what `initialize_run` actually FREEZES onto the queue entry. The frozen
        `action` is what the dispatch loop reads, so it is the value that decides whether an agent turn
        is spent.
        """

        import argparse
        import contextlib as _ctx
        import io as _io
        import subprocess

        for label, module in _dispatch_hosts():
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                    subprocess.run(
                        ["git", "config", "user.email", "t@e.com"], cwd=root, check=True
                    )
                    subprocess.run(
                        ["git", "config", "user.name", "T"], cwd=root, check=True
                    )
                    for bucket, id6, order, status, kind in (
                        ("pending", "orcq01", 0, "approved", "orchestrator"),
                        ("executed", "chiq01", 1, "executed", "child"),
                    ):
                        d = root / ".aw" / "records" / "plans" / bucket
                        d.mkdir(parents=True, exist_ok=True)
                        (
                            d / f"20260906-qbuild-{order:02d}-{id6}-synthetic.ipd.md"
                        ).write_text(
                            "# IPD: synthetic\n\n"
                            f"- Date: 2026-09-06\n- Kind: {kind}\n- Id: {id6}\n"
                            f"- Set: qbuild\n- Order: {order}\n- Status: {status}\n\n"
                            "## Child IPDs, sequence, and dependencies\n\n"
                            "| Order | Id | Child | Depends on |\n|---|---|---|---|\n"
                            "| 01 | x | x | x |\n",
                            encoding="utf-8",
                        )
                    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
                    subprocess.run(["git", "commit", "-qm", "s"], cwd=root, check=True)

                    args = argparse.Namespace(
                        repo=str(root),
                        selectors=["qbuild"],
                        manifest=None,
                        runbook=None,
                        model=None,
                        agent=None,
                        variant=None,
                        opencode="opencode",
                        antigravity="antigravity",
                        full_auto=False,
                        action=None,
                        isolate_worktree=True,
                        validate=None,
                        retry_budget=None,
                        prepare_only=True,
                        profile=None,
                        output_mode=None,
                        new_session=False,
                        verify=False,
                        timeout=None,
                        stall_timeout=None,
                    )
                    buf = _io.StringIO()
                    with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(buf):
                        run_dir = module.initialize_run(args)
                    state = json.loads(
                        (Path(run_dir) / "state.json").read_text(encoding="utf-8")
                    )
                    entry = next(it for it in state["queue"] if it["id6"] == "orcq01")
                    self.assertEqual(
                        entry["action"],
                        "orchestrate",
                        f"{label} froze action={entry['action']!r} onto the queue entry; an "
                        "'execute' here means the host will spend an AGENT TURN authoring "
                        "against an orchestrator",
                    )


class DispatchRunCase(unittest.TestCase):
    """Drives a host's real `run_queue` over a synthetic Set, with agent turns stubbed out.

    Stubbing `execute_item` is not a shortcut around the thing under test: the thing under test is
    exactly whether the ORCHESTRATOR path avoids `execute_item` while a CHILD reaches it, so the stub is
    the instrument. It records every call, which is what lets a test assert "no agent turn".
    """

    PLAN = (
        "# IPD: synthetic {kind}\n\n"
        "- Date: 2026-09-06\n"
        "- Kind: {kind}\n"
        "- Id: {id6}\n"
        "- Set: {setid}\n"
        "- Order: {order}\n"
        "- Status: {status}\n\n"
        "## Child IPDs, sequence, and dependencies\n\n"
        "| Order | Id | Child | Depends on |\n"
        "|---|---|---|---|\n"
        "{rows}"
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.turns: list[str] = []

    def write_plan(self, *, bucket, id6, order, status, kind, setid, declared=()):
        d = self.root / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        rows = "".join(f"| {tok} | x | x | x |\n" for tok in declared)
        path = d / f"20260906-{setid}-{order:02d}-{id6}-synthetic.ipd.md"
        path.write_text(
            self.PLAN.format(
                kind=kind,
                id6=id6,
                setid=setid,
                order=order,
                status=status,
                rows=rows,
            ),
            encoding="utf-8",
        )
        return path

    def make_run(self, module, queue, *, run_id="run-dispatch"):
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "created_at": "2026-09-06T00:00:00+00:00",
            "updated_at": "2026-09-06T00:00:00+00:00",
            "selectors": ["synthetic"],
            "options": {},
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir

    def item(self, id6, setid, action, status, *, kind=None, deps=(), position=1):
        return {
            "position": position,
            "id6": id6,
            "setid": setid,
            "action": action,
            "kind": kind or ("orchestrator" if action == "orchestrate" else "child"),
            "status": status,
            "dependencies": list(deps),
            "attempts": [],
        }

    def drive(self, module, run_dir, *, on_turn=None, budget=50):
        """Run the queue with agent turns stubbed, and FAIL LOUDLY on a spin rather than hanging.

        The budget is the spin detector. A test that merely hung would time the suite out with no
        diagnosis; this reports the dispatch count, which is the number that distinguishes 1 from 201.
        """

        import contextlib as _ctx
        import io as _io
        from unittest.mock import patch

        shared = module.dispatch_orchestrator_item
        seen = {"n": 0}

        def counted(*a, **kw):
            seen["n"] += 1
            if seen["n"] > budget:
                raise AssertionError(
                    f"SPIN: the orchestrator was dispatched {seen['n']} times without the run "
                    "terminating; a RECONSIDERED item must become either retired or terminal"
                )
            return shared(*a, **kw)

        def fake_exec(rd, st, it, *a, **kw):
            self.turns.append(str(it.get("id6")))
            if on_turn is not None:
                on_turn(it)
            else:
                it["status"] = "executed"
            module.save_state(rd, st)

        buf = _io.StringIO()
        with patch.object(module, "execute_item", side_effect=fake_exec):
            with patch.object(
                module, "dispatch_orchestrator_item", side_effect=counted
            ):
                with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(buf):
                    rc = module.run_queue(run_dir, retry_incomplete=False)
        self.dispatch_count = seen["n"]
        return rc, json.loads((run_dir / "state.json").read_text())

    def events(self, run_dir):
        path = run_dir / "events.jsonl"
        if not path.exists():
            return []
        return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]

    def statuses(self, state):
        return {it["id6"]: it["status"] for it in state["queue"]}


class AnOrchestratorIsRetiredMidRun(DispatchRunCase):
    """V-01: the case the terminal write made IMPOSSIBLE.

    The orchestrator is offered for dispatch BEFORE its last child finishes, so it must be RECONSIDERED
    and then RE-SELECTED and retired in the SAME run.

    WHERE RECONSIDERATION ACTUALLY HAPPENS, measured rather than assumed, because the plan expected the
    dispatch branch to own it and it does not. `run_queue` has TWO deferral points for an `orchestrate`
    item, and the FIRST one fires:

      1. THE SELECTION GATE (`dependency_status`), which now asks the same shared decision. On
         RECONSIDER it reports UNSATISFIED, so the item is skipped by the inner selection pass and left
         `queued` with no status written, no event, and NO dispatch at all. That is the cheapest correct
         reconsideration and it is the path a mid-run orchestrator takes.
      2. THE DISPATCH BRANCH, reached once the gate admits it, which then retires or terminates it.

    So RE-SELECTION here means "considered again on a later iteration and then dispatched", which is
    asserted below by ITERATION COUNT and final state rather than by a dispatch count of 2: the first
    consideration deliberately never reaches the dispatcher. An item left unlabelled and never
    reconsidered at all would end the run `queued`, and that is the assertion that separates
    reconsidered from forgotten.
    """

    def _set(self, setid="midrun"):
        self.write_plan(
            bucket="pending",
            id6="orc100",
            order=0,
            status="approved",
            kind="orchestrator",
            setid=setid,
            declared=("01",),
        )
        self.child = self.write_plan(
            bucket="pending",
            id6="chi100",
            order=1,
            status="approved",
            kind="child",
            setid=setid,
        )

    def test_reconsidered_then_retired_in_the_same_run_on_both_hosts(self):
        for label, module in _dispatch_hosts():
            with self.subTest(host=label):
                self.setUp()
                self._set()
                run_dir = self.make_run(
                    module,
                    [
                        # Position 1: the orchestrator is dispatched FIRST, which is what makes this a
                        # test of reconsideration rather than of ordering.
                        self.item(
                            "orc100", "midrun", "orchestrate", "queued", position=1
                        ),
                        self.item("chi100", "midrun", "execute", "queued", position=2),
                    ],
                )

                def finish_child(it):
                    """The child's turn ALSO lands `Status: executed` on disk, as a real turn does."""
                    it["status"] = "executed"
                    text = self.child.read_text(encoding="utf-8")
                    self.child.write_text(
                        text.replace("- Status: approved", "- Status: executed"),
                        encoding="utf-8",
                    )

                from unittest.mock import patch

                # The TRANSITION is stubbed: this test is about the DISPATCH reaching it, and child 02
                # already proves the transition itself against a real git repo. Stubbing keeps this
                # test from silently re-testing `ueg5cf`.
                from agent_workflows import ipd_lifecycle as LC

                applied = []

                class _Ok:
                    exit_code = 0
                    message = "stubbed retire"

                def fake_retire(repo, plan_path, actor, **kw):
                    applied.append((str(plan_path), kw.get("setid"), actor))
                    return _Ok()

                with patch.object(LC, "retire_orchestrator", side_effect=fake_retire):
                    rc, state = self.drive(module, run_dir, on_turn=finish_child)

                st = self.statuses(state)
                self.assertEqual(
                    st["chi100"], "executed", "the child must have run its turn"
                )
                self.assertEqual(
                    st["orc100"],
                    "executed",
                    "the orchestrator must be RETIRED in this same run, not left blocked",
                )
                # RE-SELECTION, the property that distinguishes RECONSIDERED from FORGOTTEN. The
                # orchestrator was offered at position 1 and DECLINED by the gate on the first
                # iteration (unsatisfied, because its child had not run), then considered again on a
                # later iteration and dispatched. Evidence: the child took its turn FIRST, and the
                # orchestrator still reached the dispatcher afterwards.
                self.assertEqual(
                    self.dispatch_count,
                    1,
                    "the orchestrator must reach the dispatcher EXACTLY once: the first consideration "
                    "is declined by the selection gate (RECONSIDER writes nothing and does not "
                    "dispatch), and re-dispatching it more than once would be a spin",
                )
                self.assertEqual(
                    self.turns,
                    ["chi100"],
                    "only the CHILD may consume an agent turn; the orchestrator must not",
                )
                self.assertTrue(applied, "the retirement transition must be reached")
                # The ORDER is the re-selection proof: the child's turn must precede the retirement, so
                # the orchestrator cannot have been retired on the first consideration.
                names = [e["event"] for e in self.events(run_dir)]
                self.assertIn("orchestrator-finalized", names)
                # And it was NOT terminally labelled on the way, which is the whole defect.
                self.assertEqual(
                    [
                        e
                        for e in self.events(run_dir)
                        if e["event"] == "orchestrator-deferred" and e.get("terminated")
                    ],
                    [],
                    "an orchestrator whose children merely had not finished must never receive a "
                    "TERMINAL disposition; that is the bug this plan fixes",
                )

    def test_an_unfinished_child_yields_RECONSIDER_and_never_a_TERMINAL_disposition(
        self,
    ):
        """The RECONSIDER branch itself, exercised DIRECTLY. SABOTAGE-DRIVEN.

        WHY THE END-TO-END TEST ABOVE CANNOT COVER THIS, discovered by sabotage rather than by reading.
        Forcing the RECONSIDER branch to return TERMINATE left that test PASSING, because
        `dependency_depth` treats every non-orchestrator Set member as a prerequisite of its
        orchestrator, so `queue_sort_key` dispatches the CHILD FIRST no matter what positions the queue
        declares (measured: child depth 0, orchestrator depth 1). By the time the orchestrator is
        dispatched the Set is already complete, so the run never reaches the RECONSIDER branch and a
        broken RECONSIDER is invisible to it.

        That ordering is a FEATURE (it is why a mid-run retirement works at all), so the fix is not to
        fight it but to test the branch on its own. This is the assertion that fails if RECONSIDER is
        ever turned back into a terminal write, which is the exact defect this plan exists to fix.
        """

        self._set("recons")
        decision = rs.decide_orchestrator_dispatch(
            self.root,
            "recons",
            "orc100",
            [
                self.item("orc100", "recons", "orchestrate", "queued"),
                # In the queue and NOT terminal: this run will still act on it.
                self.item("chi100", "recons", "execute", "queued"),
            ],
            terminal_states={"failed-safely", "dependency-blocked", "executed"},
            success_states={"executed"},
        )
        self.assertEqual(
            decision.outcome,
            rs.ORCH_DISPATCH_RECONSIDER,
            "an unfinished child THIS RUN will act on must be RECONSIDERED, never terminal; "
            f"got {decision.outcome!r} ({decision.detail})",
        )
        self.assertNotIn(
            decision.outcome,
            {rs.ORCH_DISPATCH_TERMINATE},
            "the pre-pgq326 code wrote a TERMINAL dependency-blocked here",
        )
        self.assertEqual(decision.unfinished, (("chi100", "queued"),))

    def test_the_reconsidered_item_is_left_queued_and_not_relabelled_by_the_cascade(
        self,
    ):
        """The half of RECONSIDER that a status check alone cannot see (F-6).

        `cascade_dependency_blocked` runs at the TOP of every iteration and propagates
        `dependency-blocked` over reverse edges to a fixed point, so it could undo RECONSIDER through a
        path the dispatch never touches. It reads only DECLARED `dependencies` edges, and an
        orchestrator's child-set relationship is not one - asserted here rather than trusted.
        """

        from agent_workflows import oc_runipd

        state = {
            "repo": str(self.root),
            "queue": [
                self.item("orc100", "midrun", "orchestrate", "queued", position=1),
                self.item("chi100", "midrun", "execute", "queued", position=2),
            ],
        }
        self.assertEqual(oc_runipd.cascade_dependency_blocked(state), [])
        self.assertEqual(self.statuses(state)["orc100"], "queued")


class TheSelectionGateUsesTheSameDecision(DispatchRunCase):
    """E-01: the gate is part of the wiring, and missing it left the mechanism UNREACHABLE.

    THE MEASURED DEFECT, which is why this class exists at all. `dependency_status_detailed` has its own
    `action == "orchestrate"` clause and it used the QUEUE-SCOPED `_set_children_all_executed`. Meanwhile
    `initialize_run` derives an already-`executed` child's RUN status as `reviewed` (only
    to-review/draft/approved/auto-approved become `queued`). So for the PRIMARY case spec R-1 names --
    `aw oc run <setid>` on a Set whose children executed in EARLIER runs -- the gate reported
    `satisfied=False, missing=['executed:<child>']` while the on-disk verdict was `eligible=True`, and
    the orchestrator was never selected at all. Wiring only the dispatch branch would have fixed nothing
    for that run, because the dispatch branch was never reached.

    Two predicates answering one question is also how `cascade_dependency_blocked` and this function once
    gave OPPOSITE verdicts (runorder F-7), so the gate now asks the same shared decision.
    """

    def _set(self, setid, child_bucket, child_status):
        self.write_plan(
            bucket="pending",
            id6="orc600",
            order=0,
            status="approved",
            kind="orchestrator",
            setid=setid,
            declared=("01",),
        )
        self.write_plan(
            bucket=child_bucket,
            id6="chi600",
            order=1,
            status=child_status,
            kind="child",
            setid=setid,
        )

    def test_a_cross_run_complete_set_is_ADMITTED_by_the_gate(self):
        """The R-1 case: an already-`executed` child, which the OLD gate counted as unfinished.

        THE QUEUE SHAPE IS THE TEST, and getting it wrong makes this vacuous. `initialize_run` derives
        an already-`executed` child's RUN status as `reviewed`, NOT `executed` (only
        to-review/draft/approved/auto-approved become `queued`; everything else becomes `reviewed`), so
        the child IS in the queue and the old queue-scoped check saw `unfinished=['chi600']` and BLOCKED.

        An earlier draft of this test put the orchestrator in the queue ALONE. That version passed even
        with the fix reverted, because the old check's no-children branch returned `(False, [])` and an
        empty list blocks nothing -- it was measuring nothing at all. Verified by reverting the gate: the
        realistic shape below FAILS, the orchestrator-only shape did not.
        """

        from agent_workflows import oc_runipd

        self._set("crossrun", "executed", "executed")
        orch = self.item("orc600", "crossrun", "orchestrate", "queued", position=1)
        # `reviewed` is exactly what `initialize_run` writes for a plan already `executed` on disk.
        child = self.item("chi600", "crossrun", "execute", "reviewed", position=2)
        state = {"repo": str(self.root), "queue": [orch, child]}
        satisfied, missing, why = oc_runipd.dependency_status_detailed(orch, state)
        self.assertTrue(
            satisfied,
            f"the gate must ADMIT a Set that is complete on disk; it reported missing={missing} "
            f"reasons={why}",
        )
        self.assertEqual(missing, [])

    def test_the_gate_is_not_vacuous_for_the_orchestrator_only_queue_either(self):
        """The other cross-run shape: `aw oc run <orchestrator-id6>` with no child in the queue."""

        from agent_workflows import oc_runipd

        self._set("crossrn2", "executed", "executed")
        item = self.item("orc600", "crossrn2", "orchestrate", "queued")
        state = {"repo": str(self.root), "queue": [item]}
        satisfied, missing, _why = oc_runipd.dependency_status_detailed(item, state)
        self.assertTrue(satisfied, f"missing={missing}")

    def test_the_gate_still_makes_a_LIVE_child_wait(self):
        """The gate must not become a rubber stamp: a child this run will run still blocks."""

        from agent_workflows import oc_runipd

        self._set("waiting", "pending", "approved")
        orch = self.item("orc600", "waiting", "orchestrate", "queued", position=1)
        child = self.item("chi600", "waiting", "execute", "queued", position=2)
        state = {"repo": str(self.root), "queue": [orch, child]}
        satisfied, missing, why = oc_runipd.dependency_status_detailed(orch, state)
        self.assertFalse(satisfied, "an unfinished in-queue child must still gate")
        self.assertEqual(missing, ["executed:chi600"])
        # The reason names the child AND its actual status, so the record can substantiate the wait.
        self.assertIn("chi600", why["executed:chi600"])
        self.assertIn("queued", why["executed:chi600"])

    def test_a_TERMINATE_verdict_is_admitted_so_it_gets_its_SPECIFIC_reason(self):
        """Deliberately admitted, and the alternative is the `5e4sb6` record.

        If the gate BLOCKED a terminal verdict, the item would be left to the drain path, which labels
        it `dependency-blocked` with whatever this function reported. For the no-children case that list
        is EMPTY, producing exactly the recorded event that named no dependency at all while the summary
        claimed an unmet one. Admitting it routes it to the dispatch branch, which writes the typed
        cause.
        """

        from agent_workflows import oc_runipd

        # No children at all: a TERMINATE verdict.
        self.write_plan(
            bucket="pending",
            id6="orc601",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="nokid2",
            declared=("01",),
        )
        item = self.item("orc601", "nokid2", "orchestrate", "queued")
        state = {"repo": str(self.root), "queue": [item]}
        satisfied, missing, _why = oc_runipd.dependency_status_detailed(item, state)
        self.assertTrue(
            satisfied,
            "a TERMINATE verdict must reach the dispatch branch, or its specific reason is lost",
        )
        self.assertEqual(missing, [])

    def test_the_gate_and_the_dispatch_cannot_disagree(self):
        """The gate and the dispatcher agree on EVERY Set shape, measured by asking both.

        REPLACES A SOURCE-TEXT PIN. This test used to `ast.unparse` the body of
        `dependency_status_detailed` and assert the string `decide_orchestrator_dispatch` appeared in
        it while `_set_children_all_executed` did not. Two defects: it asserted which NAME the gate
        mentions rather than whether the two sites AGREE (a gate could call the shared decision and
        then override its verdict, and the pin would pass), and it breaks on any refactor that moves
        the call behind a helper while changing nothing observable.

        WHAT REPLACES IT ASKS BOTH SITES THE SAME QUESTION over every Set shape that matters and
        requires their verdicts to CORRESPOND: the gate must ADMIT exactly those items the dispatcher
        would RETIRE or TERMINATE, and must WITHHOLD exactly those it would RECONSIDER. That is the
        property the shared decision exists to guarantee, stated directly.

        WHY IT MATTERS, measured (runorder F-7): two predicates answering one question once gave
        OPPOSITE verdicts, and the consequence here is specific. `initialize_run` derives an
        already-`executed` child's RUN status as `reviewed`, so for spec R-1's primary case (a Set
        whose children executed in EARLIER runs) the old queue-scoped gate reported
        `satisfied=False, missing=['executed:<child>']` while the on-disk verdict was `eligible=True`,
        and the orchestrator was never selected at all. Wiring only the dispatch branch would have
        fixed nothing, because the dispatch branch was never reached.
        """

        from agent_workflows import oc_runipd

        #: (case, the child's bucket and plan status, the child's QUEUE status or None to leave the
        #:  child out of the queue entirely, why this shape is worth asking twice)
        shapes = (
            (
                "a cross-run complete Set, child already executed on disk",
                "executed",
                "executed",
                "reviewed",
                "THE R-1 PRIMARY CASE. `reviewed` is exactly what `initialize_run` writes for a plan "
                "already executed on disk, and it is the shape where the two sites DID disagree",
            ),
            (
                "the same Set with NO child in the queue at all",
                "executed",
                "executed",
                None,
                "`aw oc run <orchestrator-id6>`. The old check's no-children branch returned "
                "`(False, [])`, and an empty missing list BLOCKS NOTHING, so this shape measured "
                "nothing at all before the fix",
            ),
            (
                "a child this run will still act on",
                "pending",
                "approved",
                "queued",
                "THE GATE MUST NOT BECOME A RUBBER STAMP. Here the dispatcher would RECONSIDER, so "
                "the gate must WITHHOLD; a gate that admitted this would burn a dispatch on every "
                "iteration",
            ),
            (
                "a child that is terminally dead",
                "pending",
                "approved",
                "failed-safely",
                "the dispatcher TERMINATES here, so the gate must ADMIT: withheld, the item falls to "
                "the drain path, which labels it `dependency-blocked` with whatever the gate "
                "reported, and for the empty case that is the `5e4sb6` event naming no dependency",
            ),
        )
        wrong = []
        for case, bucket, plan_status, queue_status, why in shapes:
            self.setUp()
            self.write_plan(
                bucket="pending",
                id6="orc900",
                order=0,
                status="approved",
                kind="orchestrator",
                setid="agree",
                declared=("01",),
            )
            self.write_plan(
                bucket=bucket,
                id6="chi900",
                order=1,
                status=plan_status,
                kind="child",
                setid="agree",
            )
            orch = self.item("orc900", "agree", "orchestrate", "queued", position=1)
            queue = [orch]
            if queue_status is not None:
                queue.append(
                    self.item("chi900", "agree", "execute", queue_status, position=2)
                )
            state = {"repo": str(self.root), "queue": queue}
            satisfied, missing, _why = oc_runipd.dependency_status_detailed(orch, state)
            decision = rs.decide_orchestrator_dispatch(
                self.root,
                "agree",
                "orc900",
                queue,
                terminal_states=set(oc_runipd.TERMINAL_STATES),
                success_states=set(oc_runipd.EXECUTION_SUCCESS_STATES),
            )
            # The correspondence: RECONSIDER is the ONLY outcome the gate may withhold for, because
            # it is the only one that will be reconsidered later in this same run.
            should_admit = decision.outcome != rs.ORCH_DISPATCH_RECONSIDER
            problems = []
            if bool(satisfied) is not should_admit:
                problems.append(
                    f"the GATE says satisfied={satisfied!r} (missing={missing!r}) while the "
                    f"DISPATCHER says {decision.outcome!r} ({decision.detail}). The gate must admit "
                    f"exactly what the dispatcher would act on and withhold only RECONSIDER"
                    + (
                        "  <-- WITHHELD a decision the dispatcher would act on, so the specific "
                        "typed reason is LOST to the drain path"
                        if not satisfied
                        else "  <-- ADMITTED an item the dispatcher will only reconsider, so a "
                        "dispatch is burned on every iteration"
                    )
                )
            if satisfied and missing:
                problems.append(
                    f"the gate reported satisfied with a non-empty missing list {missing!r}, which "
                    "no caller can interpret"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this shape is asked twice because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the selection gate and the dispatcher disagreed on {len(wrong)} of {len(shapes)} Set "
            "shapes. They must consult ONE shared decision, because two predicates answering one "
            "question is how `cascade_dependency_blocked` and this function once gave OPPOSITE "
            "verdicts (runorder F-7). FIX: if the CROSS-RUN rows fail, the gate has gone back to a "
            "QUEUE-SCOPED check, and the consequence is that spec R-1's primary case is unreachable: "
            "the orchestrator is never selected, so the dispatch branch that would retire it never "
            "runs, and no amount of correctness there can help. If the LIVE-CHILD row fails by "
            "admitting, the gate is a rubber stamp and the run re-dispatches an item it cannot yet "
            f"finish.\n" + "\n".join(wrong),
        )


class ADeadSetTerminatesInsteadOfLooping(DispatchRunCase):
    """V-03: a child that can never become `executed` must END the run, with a naming reason."""

    def test_a_terminally_failed_child_terminates_with_a_reason_naming_it(self):
        for label, module in _dispatch_hosts():
            with self.subTest(host=label):
                self.setUp()
                self.write_plan(
                    bucket="pending",
                    id6="orc200",
                    order=0,
                    status="approved",
                    kind="orchestrator",
                    setid="deadset",
                    declared=("01",),
                )
                self.write_plan(
                    bucket="pending",
                    id6="chi200",
                    order=1,
                    status="approved",
                    kind="child",
                    setid="deadset",
                )
                run_dir = self.make_run(
                    module,
                    [
                        self.item(
                            "orc200", "deadset", "orchestrate", "queued", position=1
                        ),
                        # Already dead: this run cannot make it `executed`.
                        self.item(
                            "chi200", "deadset", "execute", "failed-safely", position=2
                        ),
                    ],
                )
                rc, state = self.drive(module, run_dir)

                self.assertIn(
                    self.statuses(state)["orc200"],
                    rs_terminal(module),
                    "a dead Set's orchestrator must be TERMINAL, not left reconsiderable forever",
                )
                self.assertEqual(self.turns, [], "no agent turn may be spent")
                deferred = [
                    e
                    for e in self.events(run_dir)
                    if e["event"] == "orchestrator-deferred"
                ]
                self.assertTrue(deferred, "the refusal must be recorded")
                last = deferred[-1]
                self.assertTrue(last["terminated"])
                self.assertIn(
                    "chi200",
                    last["detail"],
                    f"the reason must NAME the dead child; got {last['detail']!r}",
                )

    def test_a_child_only_on_disk_terminates_instead_of_spinning(self):
        """THE MEASURED SPIN (E-03/OQ-01), pinned so it cannot come back.

        `dependency_status` gates an `orchestrate` item on its IN-QUEUE children, so when every queued
        child is `executed` the orchestrator is SELECTABLE even though a child on disk is unfinished. A
        naive RECONSIDER then re-dispatches it forever, and the drain path never sees it because the
        drain is reached only when nothing is selectable. Measured before the fix: 201 dispatches.
        """

        for label, module in _dispatch_hosts():
            with self.subTest(host=label):
                self.setUp()
                self.write_plan(
                    bucket="pending",
                    id6="orc300",
                    order=0,
                    status="approved",
                    kind="orchestrator",
                    setid="spinset",
                    declared=("01", "02"),
                )
                self.write_plan(
                    bucket="executed",
                    id6="chia03",
                    order=1,
                    status="executed",
                    kind="child",
                    setid="spinset",
                )
                # Unfinished ON DISK and absent from the queue: nothing this run does can finish it.
                self.write_plan(
                    bucket="pending",
                    id6="chib03",
                    order=2,
                    status="approved",
                    kind="child",
                    setid="spinset",
                )
                run_dir = self.make_run(
                    module,
                    [
                        self.item(
                            "orc300", "spinset", "orchestrate", "queued", position=1
                        ),
                        self.item(
                            "chia03", "spinset", "execute", "executed", position=2
                        ),
                    ],
                )
                rc, state = self.drive(module, run_dir, budget=25)

                self.assertLessEqual(
                    self.dispatch_count,
                    2,
                    "a decision this run cannot change must be made ONCE, not re-evaluated",
                )
                self.assertIn(self.statuses(state)["orc300"], rs_terminal(module))
                deferred = [
                    e
                    for e in self.events(run_dir)
                    if e["event"] == "orchestrator-deferred"
                ]
                self.assertEqual(
                    deferred[-1]["reason"], rs.ORCH_REASON_CHILDREN_NOT_IN_RUN
                )
                self.assertIn("chib03", deferred[-1]["detail"])


class TheFourRefusalReasonsAreDistinguishable(DispatchRunCase):
    """V-02: spec R-9. Four different facts must not share one message.

    The defect being measured: `5e4sb6`'s durable event carried `unfinished_children: []` while the run
    summary read "dependency-blocked (unmet dependencies)", naming no dependency at all - because the
    no-children branch returned `(False, [])` and every cause collapsed into one write.
    """

    def _decide(self, setid):
        return rs.decide_orchestrator_dispatch(
            self.root,
            setid,
            "orc400",
            [],
            terminal_states={"failed-safely", "dependency-blocked", "executed"},
            success_states={"executed"},
        )

    def test_each_cause_yields_a_DISTINCT_reason_and_a_detail_that_substantiates_it(
        self,
    ):
        # 1. no children at all.
        self.write_plan(
            bucket="pending",
            id6="orc400",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="nokids",
            declared=("01",),
        )
        nokids = self._decide("nokids")

        # 2. children exist but are unfinished, and this run will not act on them.
        self.write_plan(
            bucket="pending",
            id6="orc401",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="unfin",
            declared=("01",),
        )
        self.write_plan(
            bucket="pending",
            id6="chi401",
            order=1,
            status="approved",
            kind="child",
            setid="unfin",
        )
        unfin = rs.decide_orchestrator_dispatch(
            self.root,
            "unfin",
            "orc401",
            [],
            terminal_states={"failed-safely"},
            success_states={"executed"},
        )

        # 3. the child table declares a row resolving to no plan (the `rununify` shape).
        self.write_plan(
            bucket="pending",
            id6="orc402",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="unauth",
            declared=("01", "03+"),
        )
        self.write_plan(
            bucket="executed",
            id6="chi402",
            order=1,
            status="executed",
            kind="child",
            setid="unauth",
        )
        unauth = rs.decide_orchestrator_dispatch(
            self.root,
            "unauth",
            "orc402",
            [],
            terminal_states={"failed-safely"},
            success_states={"executed"},
        )

        # 4. the transition refuses. Exercised through the dispatcher, because the rewrite from RETIRE
        #    to TERMINATE happens there and nowhere else.
        self.write_plan(
            bucket="pending",
            id6="orc403",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="refuse",
            declared=("01",),
        )
        self.write_plan(
            bucket="executed",
            id6="chi403",
            order=1,
            status="executed",
            kind="child",
            setid="refuse",
        )
        run_dir = self.root / "run-refuse"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = self.item("orc403", "refuse", "orchestrate", "queued")
        state = {"repo": str(self.root), "run_id": "run-refuse", "queue": [item]}

        from unittest.mock import patch

        from agent_workflows import ipd_lifecycle as LC

        class _No:
            exit_code = 3
            message = "REFUSED: synthetic structural refusal"

        with patch.object(LC, "retire_orchestrator", return_value=_No()):
            refused = rs.dispatch_orchestrator_item(
                self.root,
                run_dir,
                state,
                item,
                actor="aw oc run model=test",
                terminal_states={"failed-safely"},
                success_states={"executed"},
            )

        reasons = {
            "no-children": nokids.reason,
            "unfinished": unfin.reason,
            "unauthored": unauth.reason,
            "finalize-refused": refused.reason,
        }
        self.assertEqual(
            len(set(reasons.values())),
            4,
            f"the four causes must be DISTINGUISHABLE; got {reasons}",
        )
        self.assertEqual(nokids.reason, rs.RETIRE_REFUSED_NO_CHILDREN)
        self.assertEqual(unauth.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
        self.assertEqual(refused.reason, rs.ORCH_REASON_FINALIZE_REFUSED)

        # `finalize-refused` is TERMINATE, never RECONSIDER: `rh5tt6` proves a refusal can be
        # structural, and retrying it every iteration would spin.
        self.assertEqual(refused.outcome, rs.ORCH_DISPATCH_TERMINATE)

        # Every detail SUBSTANTIATES its reason, so no summary can claim a cause it cannot name.
        self.assertIn("chi401", unfin.detail)
        self.assertIn("03+", unauth.detail)
        self.assertIn("synthetic structural refusal", refused.detail)
        for label, decision in reasons.items():
            with self.subTest(cause=label):
                self.assertTrue(decision, "every refusal must carry a typed reason")

    def test_the_unfinished_case_names_the_ids_AND_their_actual_statuses(self):
        """`5e4sb6` reported an unmet dependency it could not name. Both halves are required."""

        self.write_plan(
            bucket="pending",
            id6="orc404",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="named",
            declared=("01", "02"),
        )
        self.write_plan(
            bucket="pending",
            id6="chi404",
            order=1,
            status="approved",
            kind="child",
            setid="named",
        )
        self.write_plan(
            bucket="pending",
            id6="chi405",
            order=2,
            status="reviewed",
            kind="child",
            setid="named",
        )
        decision = rs.decide_orchestrator_dispatch(
            self.root,
            "named",
            "orc404",
            [
                self.item("chi404", "named", "execute", "queued"),
                self.item("chi405", "named", "execute", "queued"),
            ],
            terminal_states={"failed-safely"},
            success_states={"executed"},
        )
        self.assertEqual(decision.outcome, rs.ORCH_DISPATCH_RECONSIDER)
        ids = {i for i, _s in decision.unfinished}
        self.assertEqual(ids, {"chi404", "chi405"})
        for child, status in decision.unfinished:
            with self.subTest(child=child):
                self.assertTrue(status, "the STATUS must be carried, not only the id")
                self.assertIn(child, decision.detail)
                self.assertIn(status, decision.detail)

    def test_a_terminated_item_never_claims_a_dependency_it_cannot_name(self):
        """The `5e4sb6` summary defect, asserted on the written ITEM rather than on prose."""

        self.write_plan(
            bucket="pending",
            id6="orc406",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="noname",
            declared=("01",),
        )
        run_dir = self.root / "run-noname"
        run_dir.mkdir(parents=True, exist_ok=True)
        item = self.item("orc406", "noname", "orchestrate", "queued")
        state = {"repo": str(self.root), "run_id": "run-noname", "queue": [item]}
        rs.dispatch_orchestrator_item(
            self.root,
            run_dir,
            state,
            item,
            actor="aw oc run model=test",
            terminal_states={"failed-safely"},
            success_states={"executed"},
        )
        # No children exist, so there is no dependency to name -- and the record must therefore carry
        # the TYPED reason instead of an empty dependency list dressed up as one.
        self.assertEqual(item["unsatisfied_dependencies"], [])
        self.assertEqual(
            item["orchestrator_refusal_reason"], rs.RETIRE_REFUSED_NO_CHILDREN
        )
        self.assertIn("noname", item["orchestrator_refusal_detail"])


class TheAgyHostActsOnTheDecision(DispatchRunCase):
    """V-07: agy must DISPATCH the outcome, which sharing the DECIDER does not accomplish.

    THE CONTRAST THIS CLASS EXISTS FOR. Before it, `agy_runipd` contained the token `orchestrate`
    nowhere outside an unrelated import, derived only `is_review` in `execute_item`, and called
    `execute_item` unconditionally. So a shared decider alone would have shipped a value agy IGNORED,
    while `TheActionDecisionIsSHAREDCode`'s identity assertion still passed. That is why the two are
    separate test classes and why V-04 must not be read as evidence for this.
    """

    def test_agy_retires_an_approved_orchestrator_with_NO_agent_turn(self):
        from agent_workflows import agy_runipd

        self.write_plan(
            bucket="pending",
            id6="orc500",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="agyset",
            declared=("01",),
        )
        self.write_plan(
            bucket="executed",
            id6="chi500",
            order=1,
            status="executed",
            kind="child",
            setid="agyset",
        )
        run_dir = self.make_run(
            agy_runipd,
            [self.item("orc500", "agyset", "orchestrate", "queued", position=1)],
        )

        from unittest.mock import patch

        from agent_workflows import ipd_lifecycle as LC

        class _Ok:
            exit_code = 0
            message = "stubbed retire"

        with patch.object(LC, "retire_orchestrator", return_value=_Ok()):
            rc, state = self.drive(agy_runipd, run_dir)

        self.assertEqual(self.statuses(state)["orc500"], "executed")
        self.assertEqual(
            self.turns,
            [],
            "agy must NOT call execute_item for an orchestrator; that is the whole defect",
        )
        # No session/prompt artifact was written for it either: an agent turn leaves traces even when
        # `execute_item` is stubbed, so both are asserted.
        for sub in ("sessions", "prompts"):
            leftovers = (
                list((run_dir / sub).glob("*")) if (run_dir / sub).is_dir() else []
            )
            self.assertEqual(
                leftovers, [], f"an orchestrator must leave no {sub}/ artifact"
            )
        self.assertIn(
            "orchestrator-finalized", [e["event"] for e in self.events(run_dir)]
        )

    def test_the_orchestrate_branch_SHORT_CIRCUITS_before_execute_item_on_both_hosts(
        self,
    ):
        """The branch must guard `execute_item`, measured by making `execute_item` EXPLODE.

        REPLACES AN AST SOURCE SCAN. This test used to parse `agy_runipd`, find `run_queue`, look for
        an `ast.If` whose test mentioned the string `orchestrate`, and assert that some `ast.Continue`
        existed somewhere inside it and that the unparsed branch contained
        `dispatch_orchestrator_item`. Three defects: a branch written as a dict dispatch, an early
        `return`, a guard clause at the top of the loop, or a match statement all short-circuit
        correctly while matching none of those shapes; the `Continue` could belong to an unrelated
        nested branch; and the scan asserted nothing about whether control ACTUALLY avoided
        `execute_item`.

        WHAT REPLACES IT IS THE CONSEQUENCE ITSELF, on BOTH hosts. `execute_item` is patched to RAISE,
        so if control ever reaches it the test fails with that exception rather than with a claim about
        syntax. An agent turn is the thing being prevented (it costs money and authors against a plan
        whose purpose the runner supersedes), so the assertion is that the turn never happens while the
        orchestrator still reaches its terminal state.

        WHY IT RUNS ON BOTH HOSTS: the defect this Set fixed was one-sided. `agy_runipd` contained the
        token `orchestrate` nowhere outside an unrelated import, derived only `is_review` in
        `execute_item`, and called `execute_item` unconditionally, so a shared decider alone would have
        shipped a value agy IGNORED while the identity assertions all passed.
        """

        import contextlib as _ctx
        import io as _io
        from unittest.mock import patch

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared

        wrong = []
        for label, module in _dispatch_hosts():
            self.setUp()
            # V-04's identity assertion still holds by construction: the decider is untouched.
            if module.action_for is not runner_shared.action_for:
                wrong.append(
                    f"  {label}: does not bind the shared `action_for` at all, so this test cannot "
                    "distinguish a missing BRANCH from a missing DECIDER"
                )
                continue
            self.write_plan(
                bucket="pending",
                id6="orc800",
                order=0,
                status="approved",
                kind="orchestrator",
                setid="branch",
                declared=("01",),
            )
            self.write_plan(
                bucket="executed",
                id6="chi800",
                order=1,
                status="executed",
                kind="child",
                setid="branch",
            )
            run_dir = self.make_run(
                module,
                [self.item("orc800", "branch", "orchestrate", "queued", position=1)],
            )

            class _Ok:
                exit_code = 0
                message = "stubbed retire"

            def exploding_execute(*a, **kw):
                raise AssertionError(
                    "execute_item WAS REACHED for an `orchestrate` item: the branch does not "
                    "short-circuit, so this host spends an AGENT TURN authoring against an "
                    "orchestrator"
                )

            buf = _io.StringIO()
            reached = None
            with patch.object(LC, "retire_orchestrator", return_value=_Ok()):
                with patch.object(
                    module, "execute_item", side_effect=exploding_execute
                ):
                    with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(buf):
                        try:
                            module.run_queue(run_dir, retry_incomplete=False)
                        except AssertionError as exc:
                            reached = str(exc)
            problems = []
            if reached is not None:
                problems.append(reached)
            else:
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                status = self.statuses(state)["orc800"]
                if status != "executed":
                    problems.append(
                        f"the orchestrator ended `{status}` rather than `executed`, so the branch "
                        "avoided `execute_item` but did not reach the retirement either: the item is "
                        "simply dropped"
                    )
                events = [e["event"] for e in self.events(run_dir)]
                if "orchestrator-finalized" not in events:
                    problems.append(
                        f"no `orchestrator-finalized` event was recorded, so the run leaves no "
                        f"durable trace of the retirement; events seen: {events!r}"
                    )
                # No session or prompt artifact either: an agent turn leaves traces even when
                # `execute_item` is stubbed, so both are checked.
                for sub in ("sessions", "prompts"):
                    leftovers = (
                        [p.name for p in (run_dir / sub).glob("*")]
                        if (run_dir / sub).is_dir()
                        else []
                    )
                    if leftovers:
                        problems.append(
                            f"an orchestrator left {sub}/ artifacts {leftovers!r}, which only an "
                            "agent turn produces"
                        )
            if problems:
                wrong.append(
                    f"  {label}:\n" + "".join(f"    - {p}\n" for p in problems)
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of 2 hosts mishandled an `orchestrate` queue item. FIX: the branch must "
            "short-circuit BEFORE `execute_item` and route to the shared performer. Reaching "
            "`execute_item` is the measured defect (`agy_runipd` called it unconditionally and would "
            "have spent an agent turn authoring against an orchestrator); ending in a non-terminal "
            "state instead is the opposite failure, where the branch swallows the item and the "
            f"orchestrator is never retired at all.\n" + "\n".join(wrong),
        )

    def test_neither_host_forks_the_dispatch_or_the_decision(self):
        """Both hosts route an `orchestrate` item through the SHARED performer, proven by patching it.

        REPLACES AN AST SOURCE SCAN that asserted `dispatch_orchestrator_item` and
        `decide_orchestrator_dispatch` were not top-level `def`s in either host module. It was also a
        near-duplicate of the scan in `TheActionDecisionIsSHAREDCode`, so one re-fork failed twice
        while a fork spelled any other way failed neither.

        WHAT REPLACES IT DRIVES `run_queue` ON BOTH HOSTS with the shared performer patched to a spy.
        The spy records the call and returns a TERMINATE decision, so the run ends; the assertion is
        that the spy was reached at all. A host with a private copy of the outcome logic dispatches
        its own way and never touches the spy, which is the drift spec R-10 forbids, and no renaming
        or reformatting can produce a false failure.
        """

        wrong = []
        for label, module in _dispatch_hosts():
            self.setUp()
            self.write_plan(
                bucket="pending",
                id6="orc700",
                order=0,
                status="approved",
                kind="orchestrator",
                setid="forkset",
                declared=("01",),
            )
            self.write_plan(
                bucket="executed",
                id6="chi700",
                order=1,
                status="executed",
                kind="child",
                setid="forkset",
            )
            run_dir = self.make_run(
                module,
                [self.item("orc700", "forkset", "orchestrate", "queued", position=1)],
            )
            calls = []

            def spy(repo, rd, st, it, **kw):
                calls.append(str(it.get("id6")))
                it["status"] = "dependency-blocked"
                module.save_state(rd, st)
                return rs.OrchestratorDispatch(
                    outcome=rs.ORCH_DISPATCH_TERMINATE,
                    reason=rs.ORCH_REASON_NO_CHILDREN,
                    detail="spy",
                )

            import contextlib as _ctx
            import io as _io
            from unittest.mock import patch

            buf = _io.StringIO()
            with patch.object(module, "dispatch_orchestrator_item", side_effect=spy):
                with patch.object(
                    module, "execute_item", side_effect=lambda *a, **k: None
                ):
                    with _ctx.redirect_stdout(buf), _ctx.redirect_stderr(buf):
                        module.run_queue(run_dir, retry_incomplete=False)
            if not calls:
                wrong.append(
                    f"  {label}:\n"
                    "    - the SHARED `dispatch_orchestrator_item` was never called, so this host "
                    "performs the orchestrator outcome with its own code. A private copy agrees until "
                    "one side is edited, and it is invisible to every test written against the "
                    "other host\n"
                    "    this row exists because: spec R-10 requires shared CODE, not two copies; the "
                    "re-fork would be silent until it drifted"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of 2 hosts do not route an `orchestrate` item through the shared performer. "
            "FIX: import it rather than reimplementing it. `818uru` recorded exactly this failure "
            "shape, where a guard written for one runner let the other re-fork four symbols and DRIFT "
            f"one of them.\n" + "\n".join(wrong),
        )


def rs_terminal(module):
    """The host's own terminal-state set, read from the host rather than re-listed here."""
    return set(module.TERMINAL_STATES)


class TheDocumentedClaimMatchesTheCode(unittest.TestCase):
    """E-05/V-05: every factual claim the managed AGENTS.md block makes must have a TEST behind it.

    ONE table replaces five tests, which each read the same generated paragraph and asserted that
    some phrase was present or absent.

    THESE ARE PINS ON A DOCUMENT, NOT ON SOURCE CODE, and the distinction is why they survive a pass
    that deletes source-text change-detectors elsewhere in this file. A source pin asserts that CODE
    contains a phrase, which is a proxy for behavior that a behavioral test can replace and a comment
    can satisfy. Here the prose IS the artifact under test: AGENTS.md is loaded into every agent's
    context, so what it SAYS is the deliverable, and no assertion about runtime behavior can state
    that the documentation does not lie about it. The two halves are therefore tested together, which
    is the whole point of this class: each row names both a claim the text must make and the
    BEHAVIORAL test class that demonstrates it, and the row fails if either is missing.

    THE DEFECT THIS EXISTS FOR, measured: AGENTS.md asserted the runner self-finalized orchestrators
    while that had never once succeeded (0 in 103 run records). So the FORBIDDEN rows are not
    stylistic; each is a sentence that was actually false, and the symbols it cited were cited as
    evidence for a mechanism that never ran. R-11 additionally forbids replacing one overstatement
    with another, which is why the table carries REQUIRED and FORBIDDEN rows together: text that said
    only what the runner does, omitting what it REFUSES, would be the same defect inverted.
    """

    def prose(self) -> str:
        from agent_workflows import engine

        return engine.agents_pointer_prose(target_layout="aw")

    def paragraph(self) -> str:
        text = self.prose()
        start = text.find("### The runners own ordering, isolation, and orchestrators")
        self.assertGreater(start, 0, "the runner-behavior paragraph must exist")
        end = text.find("### ", start + 10)
        return text[start : end if end > 0 else len(text)]

    #: (the fragment, whether it must be PRESENT, the scope to search ("paragraph", the whole
    #:  "rendered" AGENTS.md, or the "instruction" that follows "Do NOT raise"), the behavioral test
    #:  class that demonstrates the claim (None where the row is purely a retraction), why)
    CLAIMS = (
        (
            "retires it",
            True,
            "paragraph",
            AnOrchestratorIsRetiredMidRun,
            "the CORRECTED claim: the runner RETIRES an Order-0 orchestrator once its children are "
            "executed. Backed by a test that drives `run_queue` and observes the plan reach "
            "`executed` with no agent turn spent",
        ),
        (
            "same run",
            True,
            "paragraph",
            AnOrchestratorIsRetiredMidRun,
            "the part that makes the claim USEFUL rather than theoretical: a child finishing LATER IN "
            "THE SAME RUN still lets its parent retire. This is what the old terminal write made "
            "impossible",
        ),
        (
            "ON DISK",
            True,
            "paragraph",
            AnOrchestratorIsRetiredMidRun,
            "membership is read from the plans tree, not from the run queue, which is what makes the "
            "CROSS-RUN case work. An agent reading 'in the queue' would wrongly tell a human a "
            "completed Set cannot be retired",
        ),
        (
            "REFUSES",
            True,
            "paragraph",
            TheFourRefusalReasonsAreDistinguishable,
            "R-11: the text must say what the mechanism does NOT do. Stating only the success path is "
            "the same overstatement defect in the other direction, and it is what would send an agent "
            "to report a legitimate refusal as a bug",
        ),
        (
            "unauthored",
            True,
            "paragraph",
            TheFourRefusalReasonsAreDistinguishable,
            "the specific refusal an agent is most likely to meet and least likely to guess: a child "
            "table row nobody authored. Naming it is what lets an agent act (author the child) rather "
            "than retry",
        ),
        (
            "this run cannot finish",
            True,
            "paragraph",
            ADeadSetTerminatesInsteadOfLooping,
            "the refusal that distinguishes a dead Set from a waiting one. Without it in the text, an "
            "agent would expect a retry to help, and the measured failure was a 201-dispatch SPIN",
        ),
        (
            "BOTH hosts",
            True,
            "paragraph",
            TheAgyHostActsOnTheDecision,
            "host parity is a claim an agent relies on when told to run `aw agy run`, and it was FALSE "
            "before `pgq326`: agy had no branch reading the `orchestrate` action at all",
        ),
        (
            "no agent turn",
            True,
            "paragraph",
            TheAgyHostActsOnTheDecision,
            "the observable consequence of that parity, and the one a human notices on their bill: an "
            "orchestrator must not consume a model turn on either host",
        ),
        (
            "self-finalizes",
            False,
            "paragraph",
            None,
            "THE MEASURED FALSE CLAIM ITSELF: 0 successes in 103 run records. It must not return, and "
            "this row is the only thing standing between it and a future summariser who finds the "
            "old wording tidier",
        ),
        (
            "_set_children_all_executed",
            False,
            "paragraph",
            None,
            "a SYMBOL the false claim cited as its evidence. Citing a queue-scoped predicate as proof "
            "of a cross-run mechanism is what made the claim credible, so the citation must go with "
            "it",
        ),
        (
            "finalize_orchestrator",
            False,
            "paragraph",
            None,
            "the second cited symbol, for the same reason",
        ),
        (
            "self-finalizes",
            False,
            "rendered",
            None,
            "THE GENERATOR IS THE SOURCE BUT THE RENDERED FILE IS WHAT AN AGENT LOADS, which is why "
            "the scope column exists: a corrected generator with a stale `AGENTS.md` on disk would "
            "leave every agent in this repository still reading the false claim",
        ),
        (
            "retires it",
            True,
            "rendered",
            AnOrchestratorIsRetiredMidRun,
            "the positive half of the same claim, checked in the rendered file, so the two cannot "
            "drift apart unnoticed",
        ),
        (
            "orchestrator finalization",
            False,
            "instruction",
            TheFourRefusalReasonsAreDistinguishable,
            "THE NEIGHBOURING INSTRUCTION, and the scope is what makes this row precise: the 'Do NOT "
            "raise' list told agents that orchestrator finalization was SETTLED and not worth "
            "raising. It is not settled; a refusal is something an agent legitimately MAY raise, so "
            "the instruction must be scoped to the parts these tests actually demonstrate",
        ),
    )

    def test_every_documented_claim_is_present_and_has_a_test_behind_it(self):
        paragraph = self.paragraph()
        rendered = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        idx = paragraph.find("Do NOT raise")
        self.assertGreater(
            idx, 0, "the 'Do NOT raise' instruction must still exist in the paragraph"
        )
        scopes = {
            "paragraph": paragraph,
            "rendered": rendered,
            "instruction": paragraph[idx:],
        }
        wrong = []
        for fragment, present, scope, test_class, why in self.CLAIMS:
            haystack = scopes[scope]
            problems = []
            found = fragment in haystack
            if present and not found:
                problems.append(
                    f"the {scope} does NOT make this claim, so either the documentation lost it or "
                    "the test that demonstrates it is now guarding nothing"
                )
            if not present and found:
                problems.append(
                    f"the {scope} STILL contains this, which is a claim the code does not support"
                )
            if test_class is not None:
                tests = [
                    name
                    for name in vars(test_class)
                    if name.startswith("test_")
                    and callable(getattr(test_class, name, None))
                ]
                if not tests:
                    problems.append(
                        f"{test_class.__name__} contains NO tests, so this documented claim is "
                        "asserted by prose alone, which is exactly the defect this class exists for"
                    )
            if problems:
                wrong.append(
                    f"  {fragment!r} (must be {'PRESENT' if present else 'ABSENT'} in the {scope}"
                    + (f", demonstrated by {test_class.__name__}" if test_class else "")
                    + "):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CLAIMS)} documented claims are wrong. AGENTS.md IS LOADED "
            "INTO EVERY AGENT'S CONTEXT in this repository, so a false sentence here is acted on by "
            "every session until someone measures it. FIX: read the DIRECTION. A FORBIDDEN fragment "
            "returning is the severe case and it is not hypothetical: `self-finalizes` was asserted "
            "for 103 run records during which the mechanism never once succeeded, so agents "
            "confidently told humans a thing that had never happened. A REQUIRED fragment going "
            "missing is the mirror defect R-11 names: text that states only what the runner DOES, "
            "omitting what it REFUSES, makes an agent report a correct refusal as a bug. If a "
            "`contains NO tests` line appears, a documented claim has lost the behavioral test behind "
            f"it, which is how the original false claim survived review.\n"
            + "\n".join(wrong),
        )

    # RECONCILIATION NOTE (2026-09-19). main added two tests here while this branch was
    # consolidating the same concern into `TheDocumentedClaimMatchesTheCode.CLAIMS`:
    # `test_the_rendered_AGENTS_md_carries_the_corrected_text` and
    # `test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module`. Both are SUBSUMED, not
    # dropped, and the table is a superset rather than an equal: it asserts `self-finalizes` absent
    # AND `retires it` present in the `rendered` scope (the on-disk AGENTS.md an agent actually
    # loads), which is the first test verbatim, and every row PAIRS its claim with the test class
    # that demonstrates it, which is the second test's mapping expressed as data instead of prose.
    # Verified by grep before resolving: 4 rows carry scope `rendered`.
    def test_a_re_render_is_IDEMPOTENT(self):
        """Kept separate: compares two RENDERS to each other, so it has no literal expectation.

        A generator edit that renders differently each time would churn every adopter's file on every
        `aw setup-repo`, which is a claim about the merge function rather than about any claim's text.
        """

        from agent_workflows import engine

        current = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        sections = engine.agents_managed_sections(target_layout="aw")
        once, _ = engine.merge_aw_block(current, sections, default_header="# AGENTS")
        twice, _ = engine.merge_aw_block(once, sections, default_header="# AGENTS")
        self.assertEqual(once, twice, "a second render must be a no-op")


# ==================================================================================================
# THE COORDINATOR-OWNED WORKTREE AND THE REFUSING FAST-FORWARD (plan `u23gbn`)
# ==================================================================================================


# `_executable_source` AND `_git_arg_lists` WERE DELETED HERE. Both existed only to make
# source-text assertions survivable: the first stripped comments and docstrings so a "does not call
# X" check would not trip over a function that deliberately NAMES the operation it must never
# perform, and the second read the literal leading arguments of every `_git(...)` call so a check
# could say "runs no `git reset`" without matching the word in a message. Their two consumers are
# now behavioral (see `TheSharedGatesAreSharedAsCODE` and
# `test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree`, which RECORDS the git
# commands actually executed and the directory each ran in), so the helpers have no callers. Keeping
# them would invite the next source pin.


class TheSharedCheckoutIsNotWhereTheMutationHappens(RollupTransitionCase):
    """E-05/V-05: MEASURE the shared checkout at each observable instant of a SUCCESSFUL retirement.

    WHY NOT FAULT INJECTION, which the plan originally prescribed and which cannot work. Injecting a
    fault RAISES `_InjectedFault` and ABORTS the transaction, so by construction it can only ever
    observe a FAILED retirement. These tests use a real observation SEAM instead, which needs no
    production change: patch a function the transaction calls at the instant of interest and delegate
    to the real one.

    THE ASSERTION IS A COMPARISON, NOT A CLAIM OF CLEANLINESS. The pre-change baseline, measured at
    HEAD `73e284a6` by patching `_refresh_plans_index_fail_loud` (post-move) and
    `commit_lock.commit_isolated` (pre-commit), was:

        post-move:   RM .aw/records/plans/pending/<plan> -> .aw/records/plans/executed/<plan>
                      M peer.txt
        pre-commit:  R  .aw/records/plans/pending/<plan> -> .aw/records/plans/executed/<plan>
                      M peer.txt
                     ?? .aw/records/plans/INDEX.json
                     ?? .aw/records/plans/INDEX.md

    THE INSTANTS MOVE, WHICH IS WHY THEY ARE NAMED EXPLICITLY. Both original patch points are changed
    by this plan: the index refresh relocated to AFTER the reconciliation (so it is no longer the
    post-move instant) and `commit_isolated` is no longer the call that commits this transaction. The
    counterpart instants in the new sequence are:

    * POST-MOVE  -> the moment `land_worktree_commit` is entered, i.e. after the status edit, the plan
      move AND the commit have all happened in the coordinator worktree and immediately BEFORE the
      shared checkout is touched at all. It is the strictly LATER counterpart of the old post-move
      sample, so anything the old sample showed must be absent here a fortiori.
    * PRE-COMMIT -> the same instant, for the same reason: the commit no longer happens in a second
      step against the shared tree, so "immediately before the commit" and "immediately before the
      shared tree is written" are now the same point. Asserted as a separate sample anyway, taken
      inside the coordinator worktree's `git commit`, so a future change that reintroduces a
      shared-tree commit step is caught.

    THE RESIDUE THAT REMAINS, enumerated rather than left to be inferred: the peer's own unrelated
    dirty file (never ours to touch), and after the transaction the two GITIGNORED plans manifests
    (`INDEX.json`/`INDEX.md`), which are regenerated generated views that no `aw` verb commits and
    which do not appear in this repository's own `git status` at all because `.aw/.gitignore` ignores
    them. What must NOT appear at either instant is a staged rename of the plan or the plan present at
    its `executed/` path in the shared tree.
    """

    def _retire_with_samples(self, setid: str):
        """Retire, sampling `git status --porcelain` in the SHARED tree at both instants."""

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set(setid, [("aaa111", 1, "executed", "executed")])
        # A peer's unrelated uncommitted edit, so a sample can distinguish plan dirt from peer dirt.
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _git(self.root, "add", "peer.txt")
        import subprocess

        subprocess.run(
            ["git", "commit", "-q", "-m", "peer base"], cwd=self.root, check=True
        )
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        samples: dict[str, str] = {}
        real_land = LC.land_worktree_commit
        real_git = LC._git

        def spy_land(repo_root, landed, *, expected_base=None):
            samples["pre-shared-write"] = _git(repo_root, "status", "--porcelain")
            return real_land(repo_root, landed, expected_base=expected_base)

        def spy_git(root, args):
            # The commit inside the coordinator worktree: sample the SHARED tree at that instant.
            if (
                args
                and args[0] == "commit"
                and Path(root).resolve() != self.root.resolve()
            ):
                samples["pre-commit"] = _git(self.root, "status", "--porcelain")
            return real_git(root, args)

        # NOTE the seam is `ipd_lifecycle._git`, NOT `commit_lock._git`: the commit is no longer made
        # by `commit_isolated`, so patching that module would observe nothing and pass vacuously.
        pre = _git(self.root, "rev-parse", "HEAD").strip()
        with mock.patch.object(LC, "land_worktree_commit", spy_land):
            with mock.patch.object(LC, "_git", spy_git):
                res = self.retire(orch, setid, apply=True)
        return orch, res, samples, pre

    def test_neither_instant_shows_a_staged_rename_or_the_moved_plan(self):
        from agent_workflows import ipd_lifecycle as LC

        orch, res, samples, _pre = self._retire_with_samples("instant")
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        self.assertIn("pre-commit", samples, "the pre-commit instant was never sampled")
        self.assertIn(
            "pre-shared-write",
            samples,
            "the pre-shared-write instant was never sampled",
        )
        for instant, text in samples.items():
            with self.subTest(instant=instant):
                lines = [ln for ln in text.splitlines() if ln.strip()]
                # NO staged rename of the plan (`R`/`RM` in the first column) at all.
                self.assertEqual(
                    [ln for ln in lines if ln[:1] == "R"],
                    [],
                    f"the shared checkout holds a staged rename at the {instant} instant: {lines}",
                )
                # And the plan is not present at its executed/ path in the shared tree yet.
                self.assertEqual(
                    [ln for ln in lines if "/executed/" in ln],
                    [],
                    f"the moved plan appears in the shared tree at the {instant} instant: {lines}",
                )
                # The ONLY entry is the peer's own file, which was never ours to touch.
                self.assertEqual(
                    [ln for ln in lines if "peer.txt" not in ln],
                    [],
                    f"unexpected shared-tree residue at the {instant} instant: {lines}",
                )
        # And the plan file itself was never moved out from under the shared tree mid-transaction:
        # it is at pending/ at both instants and at executed/ only afterwards.
        self.assertFalse(orch.exists())
        self.assertTrue(
            (
                self.root
                / ".aw/records/plans/executed/20260906-instant-00-orc000-synthetic.ipd.md"
            ).is_file()
        )

    def test_the_peers_uncommitted_bytes_survive_verbatim(self):
        _orch, res, _samples, _pre = self._retire_with_samples("peerbytes")
        self.assertEqual(res.exit_code, 0, res.message)
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"),
            "peer v2 UNCOMMITTED\n",
        )

    def test_main_advances_by_exactly_one_commit_carrying_only_the_rename(self):
        _orch, res, _samples, pre = self._retire_with_samples("onecommit")
        self.assertEqual(res.exit_code, 0, res.message)
        self.assertEqual(
            _git(self.root, "rev-list", "--count", f"{pre}..HEAD").strip(), "1"
        )
        assert res.commit is not None
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), res.commit)
        changed = set(
            _git(
                self.root,
                "show",
                "--name-only",
                "--no-renames",
                "--format=",
                res.commit,
            ).split()
        )
        self.assertEqual(
            changed,
            {
                ".aw/records/plans/pending/20260906-onecommit-00-orc000-synthetic.ipd.md",
                ".aw/records/plans/executed/20260906-onecommit-00-orc000-synthetic.ipd.md",
            },
            sorted(changed),
        )

    def test_the_commit_is_produced_in_a_worktree_that_is_NOT_the_shared_checkout(self):
        """The property E-01 is really about, asserted on the observed commit CWD.

        A test that only checked the end state could not distinguish "committed in a worktree" from
        "committed in the shared tree and then cleaned up", which is exactly the difference that
        matters to a peer whose file `pre-commit` would otherwise stash.
        """

        from unittest import mock

        from agent_workflows import commit_lock as CL
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("wtcommit", [("aaa111", 1, "executed", "executed")])
        real_git = LC._git
        commit_roots: list[str] = []

        def spy_git(root, args):
            if args and args[0] == "commit":
                commit_roots.append(str(root))
            return real_git(root, args)

        with mock.patch.object(LC, "_git", spy_git):
            res = self.retire(orch, "wtcommit", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertTrue(commit_roots, "no git commit was observed at all")
        for root in commit_roots:
            with self.subTest(root=root):
                self.assertNotEqual(
                    Path(root).resolve(),
                    self.root.resolve(),
                    "the lifecycle commit ran in the SHARED checkout, which is what lets "
                    "pre-commit stash a peer's in-flight write",
                )
        # No coordinator worktree or branch is left behind.
        self.assertNotIn("aw-coordinator-", _git(self.root, "worktree", "list"))
        self.assertNotIn(
            CL.COORDINATOR_WORKTREE_PREFIX, _git(self.root, "branch", "--list", "-a")
        )


class TheSharedTreeIsReconciledByARefusingFastForward(RollupTransitionCase):
    """E-06/V-06: the three arms of the reconciliation, exercised through the REAL code path.

    Each arm is measured, not asserted from prose, and the arms are distinguished by git's EXIT CODE
    plus the tree state, never by string-matching git's message (the two failure arms word themselves
    differently: `error:` with rc=1 for the would-be-overwritten refusal, `fatal:` with rc=128 for
    divergence).
    """

    def test_the_clean_arm_fast_forwards_and_leaves_only_the_peers_dirt(self):
        import subprocess

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("ffclean", [("aaa111", 1, "executed", "executed")])
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _git(self.root, "add", "peer.txt")
        subprocess.run(
            ["git", "commit", "-q", "-m", "peer base"], cwd=self.root, check=True
        )
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        from unittest import mock

        seen: dict[str, object] = {}
        real_land = LC.land_worktree_commit

        def spy(repo_root, landed, *, expected_base=None):
            out = real_land(repo_root, landed, expected_base=expected_base)
            seen["landing"] = out
            return out

        with mock.patch.object(LC, "land_worktree_commit", spy):
            res = self.retire(orch, "ffclean", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        landing = seen["landing"]
        self.assertEqual(landing.status, LC.RECONCILED_OK, landing.detail)  # type: ignore[union-attr]
        self.assertEqual(landing.returncode, 0)  # type: ignore[union-attr]
        # THE NO-OP ORDERING IS RULED OUT EXPLICITLY: the broken sequence passes every other
        # assertion here, and its signature is git reporting "Already up to date." while the tree
        # keeps a staged D/A pair.
        self.assertIn("Fast-forward", landing.detail)  # type: ignore[union-attr]
        self.assertNotIn("Already up to date", landing.detail)  # type: ignore[union-attr]
        porcelain = [
            ln
            for ln in _git(self.root, "status", "--porcelain").splitlines()
            if ln.strip()
        ]
        # NOTHING ABOUT THE PLAN: no staged rename, no half-move, no `D `/`A ` pair (the exact
        # signature of the no-op ordering). The peer's own entry stays, and so do the two GENERATED
        # plans manifests, which this fixture's `.gitignore` does not cover but the real repository's
        # `.aw/.gitignore` does (verified there with `git check-ignore`), so they cannot dirty a real
        # checkout. Enumerated rather than filtered away, so the residue is a stated property.
        self.assertEqual(
            [ln for ln in porcelain if "peer.txt" not in ln and "/INDEX." not in ln],
            [],
            f"the shared checkout holds more than the peer's dirt: {porcelain}",
        )
        self.assertEqual(
            [ln for ln in porcelain if "-orc000-" in ln],
            [],
            f"the plan itself is dirty in the shared checkout after landing: {porcelain}",
        )
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"),
            "peer v2 UNCOMMITTED\n",
        )
        self.assertTrue(
            (
                self.root
                / ".aw/records/plans/executed/20260906-ffclean-00-orc000-synthetic.ipd.md"
            ).is_file()
        )

    def test_the_ff_only_merge_is_the_ONLY_command_that_touches_the_shared_tree(
        self,
    ):
        """The ordering bug F-10, measured by RECORDING every git command run in the shared checkout.

        REPLACES A SOURCE-TEXT PIN. This test used to strip comments from
        `_finalize_transaction`'s source and assert `update-ref` was absent and
        `land_worktree_commit` present, plus an AST walk over `land_worktree_commit`'s literal `_git`
        argument lists checking no call began with `reset`/`checkout`/`restore`/`clean`/`stash`. It
        needed two bespoke source-introspection helpers (`_executable_source`, `_git_arg_lists`) built
        precisely BECAUSE the functions deliberately NAME the operations they must never perform, and
        it still could not see a forcing command issued with a non-literal subcommand, through
        `subprocess` directly, or from a helper one level down.

        WHAT REPLACES IT OBSERVES THE COMMANDS. `ipd_lifecycle._git` is wrapped for the whole
        retirement, and every invocation is recorded WITH the directory it ran in. The assertion is
        then the property itself: among commands executed against the SHARED checkout, the only
        mutating ones are a single `merge --ff-only` plus the narrow path-scoped release described on
        `_permitted` below. That covers any spelling, any call depth, and any subcommand computed at
        runtime, and it needs no helper.

        THIS FOUND A REAL THING THE SOURCE PIN COULD NOT. The transaction also runs
        `git checkout HEAD -- <the plan's own path>` against the shared tree, from
        `_release_own_uncommitted_plan_edit` rather than from `land_worktree_commit`, which is why a
        pin that inspected only the latter never saw it. It is deliberate and proven safe; see
        `_permitted`.

        WHY THIS PROPERTY IS LOAD-BEARING: a separate `update-ref` before the reconciliation makes the
        merge a no-op that REPORTS SUCCESS, and makes the peer-protecting refusal unreachable because
        git never performs the would-be-overwritten check. A forcing command
        (`reset --hard`, `checkout -f`, `clean`, `stash`) destroys a co-worker's uncommitted bytes
        outright. Neither is visible from a passing happy path, which is why it is asserted directly.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("ffonly", [("aaa111", 1, "executed", "executed")])
        # A peer's uncommitted edit, so a forcing command would have something real to destroy.
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _git(self.root, "add", "peer.txt")
        import subprocess

        subprocess.run(
            ["git", "commit", "-q", "-m", "peer base"], cwd=self.root, check=True
        )
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        observed: list[tuple[str, tuple[str, ...]]] = []
        real_git = LC._git

        def recording_git(root, args):
            observed.append((str(Path(root).resolve()), tuple(args)))
            return real_git(root, args)

        with mock.patch.object(LC, "_git", recording_git):
            res = self.retire(orch, "ffonly", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        self.assertTrue(
            observed, "no git command was observed at all, so this proves nothing"
        )

        shared = str(self.root.resolve())
        shared_calls = [args for root, args in observed if root == shared]
        self.assertTrue(
            shared_calls,
            "no git command ran in the SHARED checkout, so the reconciliation step is missing "
            f"entirely; commands were only seen elsewhere: {observed!r}",
        )

        #: Subcommands that MUTATE a working tree or a ref.
        MUTATING = {
            "merge",
            "reset",
            "checkout",
            "restore",
            "clean",
            "stash",
            "update-ref",
            "switch",
            "rebase",
            "cherry-pick",
            "apply",
            "commit",
            "am",
            "pull",
        }
        mutations = [args for args in shared_calls if args and args[0] in MUTATING]
        plan_rel = (
            ".aw/records/plans/pending/20260906-ffonly-00-orc000-synthetic.ipd.md"
        )

        def _permitted(args: tuple[str, ...]) -> bool:
            """The TWO mutations of the shared tree this transaction is allowed to make.

            MEASURED WHILE WRITING THIS TEST, and the source pin this replaces would never have shown
            it: the transaction runs a PATH-SCOPED `git checkout HEAD -- <its own plan>` before the
            merge. The old pin passed only because it inspected `land_worktree_commit`, where that call
            does not live; it happens in `_release_own_uncommitted_plan_edit`, one level away. So the
            rule is not "exactly one mutation" as this test first asserted; it is narrower and more
            interesting, and it is pinned here rather than loosened away.

            WHY THAT CHECKOUT IS LEGITIMATE, per `ipd_lifecycle`: an agent's own uncommitted status
            edit to the plan being finalized would make `merge --ff-only` REFUSE, so the transaction
            releases THAT ONE PATH, having first PROVED the bytes cannot be lost (the shared tree's
            bytes equal what it mirrored into the worktree, AND the landed commit demonstrably carries
            them). If either proof fails it writes nothing and lets the merge refuse. It is therefore
            scoped to a single path whose content is already durable in a commit, which is what
            distinguishes it from `reset --hard`, `checkout -f` or a forced merge.
            """

            if args[:2] == ("merge", "--ff-only"):
                return True
            # `checkout HEAD -- <the plan's own path>` and NOTHING wider: no `-f`, no `.`, no second
            # path, and specifically not the peer's file.
            return list(args) == ["checkout", "HEAD", "--", plan_rel]

        problems = []
        for args in mutations:
            if not _permitted(args):
                problems.append(
                    f"`git {' '.join(args)}` mutated the SHARED checkout and is not one of the two "
                    "permitted operations (a single `merge --ff-only`, or a path-scoped "
                    "`checkout HEAD -- <this plan's own path>`)"
                )
            if args[0] == "merge" and "--ff-only" not in args:
                problems.append(
                    f"a merge ran WITHOUT `--ff-only` (`git {' '.join(args)}`), so it can create a "
                    "commit instead of refusing, and the peer-protecting refusal is unreachable"
                )
            if args[0] == "update-ref":
                problems.append(
                    f"`git {' '.join(args)}` advances the ref DIRECTLY, which makes the ff-only merge "
                    "a no-op that REPORTS SUCCESS while git never performs the would-be-overwritten "
                    "check (bug F-10)"
                )
            if args[0] in {"reset", "restore", "clean", "stash", "switch"} or (
                args[0] == "checkout" and not _permitted(args)
            ):
                problems.append(
                    f"`git {' '.join(args)}` FORCES past or works around a refusal, destroying a "
                    "co-worker's uncommitted bytes; a refusal must be reported, never overridden"
                )
        if [tuple(a[:2]) for a in mutations].count(("merge", "--ff-only")) != 1:
            problems.append(
                "the branch must be advanced by EXACTLY ONE `merge --ff-only`; observed "
                f"{[' '.join(a) for a in mutations]!r}"
            )
        # AND THE SCOPE OF THE PERMITTED CHECKOUT IS ASSERTED, because its whole safety rests on being
        # narrow: it must never name the peer's file or the whole tree.
        for args in mutations:
            if args[0] == "checkout":
                if "peer.txt" in args:
                    problems.append(
                        f"`git {' '.join(args)}` names the PEER's file, which is never this "
                        "transaction's to restore"
                    )
                if "-f" in args or "--force" in args or "." in args:
                    problems.append(
                        f"`git {' '.join(args)}` is a FORCED or whole-tree checkout, not the narrow "
                        "single-path release the transaction is permitted"
                    )
        # And the peer's bytes are intact, which is the consequence all of the above protects.
        if (self.root / "peer.txt").read_text(
            encoding="utf-8"
        ) != "peer v2 UNCOMMITTED\n":
            problems.append(
                "the peer's uncommitted bytes did NOT survive the retirement, which is the damage "
                "every assertion above exists to prevent"
            )
        self.assertEqual(
            problems,
            [],
            "the shared checkout was advanced by something other than a single ff-only merge:\n"
            + "".join(f"  - {p}\n" for p in problems)
            + "FIX: `land_worktree_commit`'s `git merge --ff-only` must be the SINGLE step that moves "
            "both the ref and the working tree, and its refusal must be surfaced rather than worked "
            "around. Every other mutation of the shared tree belongs in the coordinator-owned "
            f"worktree.\n  all observed commands: {observed!r}",
        )

    def test_the_contended_arm_refuses_and_the_peers_bytes_survive(self):
        """A local modification to the plan being moved: git refuses (rc=1) and nothing is lost.

        THE ORCHESTRATOR'S OWN dirty plan file is refused UP FRONT by
        `_assert_rollup_touched_only_owned_paths`, so this arm is reached on the rollup path only by a
        race in which the file becomes dirty DURING the transaction. That race is what is simulated:
        the peer's edit lands while the coordinator worktree is committing.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("ffdirty", [("aaa111", 1, "executed", "executed")])
        head = _git(self.root, "rev-parse", "HEAD").strip()
        original = orch.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT IN FLIGHT, uncommitted\n"
        real_git = LC._git

        def spy_git(root, args):
            # Land the peer's edit on the plan file just as the worktree commits, i.e. after the
            # up-front dirty check has already passed.
            if (
                args
                and args[0] == "commit"
                and Path(root).resolve() != self.root.resolve()
            ):
                orch.write_text(peer_bytes, encoding="utf-8")
            return real_git(root, args)

        seen: dict[str, object] = {}
        real_land = LC.land_worktree_commit

        def spy_land(repo_root, landed, *, expected_base=None):
            out = real_land(repo_root, landed, expected_base=expected_base)
            seen["landing"] = out
            return out

        with mock.patch.object(LC, "_git", spy_git):
            with mock.patch.object(LC, "land_worktree_commit", spy_land):
                res = self.retire(orch, "ffdirty", apply=True)

        landing = seen["landing"]
        self.assertEqual(landing.status, LC.RECONCILED_REFUSED, landing.detail)  # type: ignore[union-attr]
        self.assertEqual(landing.returncode, 1, landing.detail)  # type: ignore[union-attr]
        self.assertIn(
            ".aw/records/plans/pending/20260906-ffdirty-00-orc000-synthetic.ipd.md",
            landing.paths,  # type: ignore[union-attr]
        )
        # NOT reported as success, and the refusal is surfaced with git's own text.
        self.assertNotEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertIn("would be overwritten", res.message)
        # THE PEER'S BYTES SURVIVE, verbatim, which is the whole point.
        self.assertEqual(orch.read_text(encoding="utf-8"), peer_bytes)
        # The branch was NOT advanced, so the commit is NOT reachable: this is emphatically NOT
        # committed-incomplete, and the recorded classification must agree with that reality.
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)
        journal = LC.read_finalize_journal(self.root, "orc000")
        if journal is not None:
            self.assertNotEqual(journal.get("phase"), LC.PHASE_COMMITTED_INCOMPLETE)

    def test_the_diverged_arm_is_a_race_with_its_own_exit_code(self):
        """A peer COMMIT landing mid-transaction: rc=128, no fast-forward exists, tree clean."""

        import subprocess
        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("ffrace", [("aaa111", 1, "executed", "executed")])
        real_git = LC._git

        def spy_git(root, args):
            if (
                args
                and args[0] == "commit"
                and Path(root).resolve() != self.root.resolve()
            ):
                # A peer commits something unrelated to main while we are committing.
                (self.root / "peer.txt").write_text("peer landed\n", encoding="utf-8")
                subprocess.run(["git", "add", "peer.txt"], cwd=self.root, check=True)
                subprocess.run(
                    ["git", "commit", "-q", "-m", "peer landed first"],
                    cwd=self.root,
                    check=True,
                )
            return real_git(root, args)

        seen: dict[str, object] = {}
        real_land = LC.land_worktree_commit

        def spy_land(repo_root, landed, *, expected_base=None):
            out = real_land(repo_root, landed, expected_base=expected_base)
            seen["landing"] = out
            seen["landed"] = landed
            return out

        with mock.patch.object(LC, "_git", spy_git):
            with mock.patch.object(LC, "land_worktree_commit", spy_land):
                res = self.retire(orch, "ffrace", apply=True)

        landing = seen["landing"]
        self.assertEqual(landing.status, LC.RECONCILED_RACED, landing.detail)  # type: ignore[union-attr]
        self.assertEqual(landing.returncode, 128, landing.detail)  # type: ignore[union-attr]
        self.assertIn("DIVERGED", landing.detail)  # type: ignore[union-attr]
        self.assertNotEqual(res.exit_code, LC.EXIT_OK, res.message)
        # The peer's commit is untouched and still the tip; ours was never landed.
        self.assertEqual(
            _git(self.root, "log", "-1", "--format=%s").strip(), "peer landed first"
        )
        import subprocess as _sp

        ancestor = _sp.run(
            ["git", "merge-base", "--is-ancestor", str(seen["landed"]), "HEAD"],
            cwd=self.root,
            capture_output=True,
        )
        self.assertNotEqual(
            ancestor.returncode,
            0,
            "the abandoned commit must NOT be reachable from main",
        )
        # And the plan is back where it started, untouched.
        self.assertTrue(orch.is_file())


class TheIndexGateIsStillLiveUnderTheNewOrdering(RollupTransitionCase):
    """E-07/V-07: prove the `plans-index-refresh-fail-loud` gate GUARDS, not merely that it is named.

    F-9 established that the test pinning this gate asserts only that its NAME appears in
    `ROLLUP_SHARED_GATES`, so a gate lost IN FACT would be invisible. F-12 then measured exactly such
    a loss: with the relocation moved into the coordinator worktree, a refresh left in its old position
    scanned a shared disk that still showed `pending/`, converged against the OLD layout, and PASSED,
    after which the merge made the manifest instantly stale.
    """

    def _manifest(self) -> str:
        return (self.root / ".aw" / "records" / "plans" / "INDEX.json").read_text(
            encoding="utf-8"
        )

    def _index_check_rc(self) -> int:
        import argparse

        from agent_workflows import plans_index as PIDX

        return PIDX.run_index(
            argparse.Namespace(
                dir=str(self.root),
                check=True,
                agent=False,
                json=False,
                no_color=True,
                limit=None,
                quiet=True,
            )
        )

    def test_the_manifest_names_the_executed_path_and_check_is_clean(self):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("idxlive", [("aaa111", 1, "executed", "executed")])
        res = self.retire(orch, "idxlive", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        manifest = self._manifest()
        name = "20260906-idxlive-00-orc000-synthetic.ipd.md"
        self.assertIn(f"executed/{name}", manifest)
        self.assertNotIn(f"pending/{name}", manifest)
        self.assertEqual(
            self._index_check_rc(),
            0,
            "aw index plans --check must be clean after a successful retirement; a "
            "check.stale-index-stale finding means the refresh still runs BEFORE the reconciliation",
        )

    def test_the_old_position_would_have_produced_a_stale_manifest(self):
        """THE BASELINE, so this class distinguishes the fix from the falsely-passing gate it replaces.

        Reproduces the OLD ordering directly: refresh while the plan is still at `pending/` in the
        shared tree (which is where it sits when the mutation happens in the worktree), then relocate
        as the merge would. The refresh does NOT raise -- the gate passes -- and `--check` is then
        stale on both manifests.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("idxstale", [("aaa111", 1, "executed", "executed")])
        # The gate PASSES here, which is the inversion: it converged against the old layout.
        LC._refresh_plans_index_fail_loud(self.root)
        name = "20260906-idxstale-00-orc000-synthetic.ipd.md"
        self.assertIn(f"pending/{name}", self._manifest())
        self.assertNotIn(f"executed/{name}", self._manifest())
        # Now relocate, as the ff-only merge does, and the manifest is instantly stale.
        dest = self.root / ".aw" / "records" / "plans" / "executed" / orch.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git(
            self.root,
            "mv",
            str(orch.relative_to(self.root)),
            str(dest.relative_to(self.root)),
        )
        self.assertNotEqual(
            self._index_check_rc(),
            0,
            "the baseline must be STALE, or this test is not measuring the defect",
        )

    def test_the_gate_still_REFUSES_on_a_genuine_non_convergence(self):
        """Fail-loud, not fail-quiet: a refresh that cannot converge still fails the transaction."""

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("idxrefuse", [("aaa111", 1, "executed", "executed")])
        with mock.patch.object(
            LC,
            "_refresh_plans_index_fail_loud",
            side_effect=RuntimeError("did not converge"),
        ):
            res = self.retire(orch, "idxrefuse", apply=True)
        self.assertNotEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertIn("did not converge", res.message)
        # POST-COMMIT, so committed-incomplete and NOT rolled back.
        self.assertIn("COMMITTED-INCOMPLETE", res.message)
        journal = LC.read_finalize_journal(self.root, "orc000")
        assert journal is not None
        self.assertEqual(journal["phase"], LC.PHASE_COMMITTED_INCOMPLETE)

    def test_the_refresh_runs_AFTER_the_reconciliation_not_before(self):
        """Pinned as an ORDER of observed calls, because the wrong order still passes the happy path."""

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("idxorder", [("aaa111", 1, "executed", "executed")])
        order: list[str] = []
        real_land = LC.land_worktree_commit
        real_refresh = LC._refresh_plans_index_fail_loud

        def spy_land(repo_root, landed, *, expected_base=None):
            order.append("reconcile")
            return real_land(repo_root, landed, expected_base=expected_base)

        def spy_refresh(repo_root):
            order.append("refresh")
            return real_refresh(repo_root)

        with mock.patch.object(LC, "land_worktree_commit", spy_land):
            with mock.patch.object(LC, "_refresh_plans_index_fail_loud", spy_refresh):
                res = self.retire(orch, "idxorder", apply=True)
        self.assertEqual(res.exit_code, 0, res.message)
        self.assertEqual(
            order,
            ["reconcile", "refresh"],
            "the refresh must scan a disk that already holds the final layout",
        )


class AFailedRetirementCannotDestroyAPeersInFlightEdit(RollupTransitionCase):
    """E-08/V-08: the one requirement here whose failure means DATA LOSS rather than a wrong report.

    `_rollback_precommit` step 2 used to write `journal["original_bytes"]` over `original_path`
    UNCONDITIONALLY. That was correct while this transaction was the party that moved that file away:
    nothing else could legitimately be there. Once the relocation happens in the coordinator worktree
    the shared-tree file is NEVER TOUCHED by the transaction, so the same write becomes an
    unconditional overwrite of whatever a peer has there.

    MEASURED before the guard, with a worktree-shaped journal and a peer edit in flight:
    before `'- Status: approved\\nPEER EDIT IN FLIGHT, uncommitted\\n'`, after
    `'- Status: approved\\nORIGINAL\\n'` -- the peer's bytes destroyed. And because the destructive
    write happens before the later steps, even a rollback that REPORTS FAILURE had already destroyed
    it.
    """

    def _worktree_shaped_journal(self, orch: Path, original: str) -> dict:
        from agent_workflows import ipd_lifecycle as LC

        rel = LC._repo_relative(self.root, orch)
        return {
            "plan_id": "orc000",
            "original_path": rel,
            "original_bytes": original,
            "dest_path": rel.replace("/pending/", "/executed/"),
            "owned_paths": [rel, rel.replace("/pending/", "/executed/")],
            "git_index_entries": {},
            "moved_bytes": original,
            "phase": LC.PHASE_MUTATING,
        }

    def test_a_peers_edit_at_the_plans_original_path_is_NOT_overwritten(self):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("rbpeer", [("aaa111", 1, "executed", "executed")])
        original = orch.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT IN FLIGHT, uncommitted\n"
        orch.write_text(peer_bytes, encoding="utf-8")

        ok, msg = LC._rollback_precommit(
            self.root, self._worktree_shaped_journal(orch, original)
        )

        # The bytes are IDENTICAL before and after: nothing was written.
        self.assertEqual(orch.read_text(encoding="utf-8"), peer_bytes)
        # And the rollback REFUSED rather than reporting a clean restore, naming the path.
        self.assertFalse(ok, msg)
        self.assertIn("unknown-outcome", msg)
        self.assertIn(LC._repo_relative(self.root, orch), msg)

    def test_a_genuine_half_move_is_STILL_restored(self):
        """The guard must not break the case rollback exists for: an absent origin IS restored."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("rbhalf", [("aaa111", 1, "executed", "executed")])
        original = orch.read_text(encoding="utf-8")
        journal = self._worktree_shaped_journal(orch, original)
        # Simulate the half-move the rollback undoes: origin gone, destination holding our bytes.
        dest = self.root / journal["dest_path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(original, encoding="utf-8")
        orch.unlink()

        ok, msg = LC._rollback_precommit(self.root, journal)
        self.assertTrue(ok, msg)
        self.assertTrue(orch.is_file(), "an absent origin must be restored")
        self.assertEqual(orch.read_text(encoding="utf-8"), original)
        self.assertFalse(dest.exists(), "the moved destination must be removed")

    def test_the_rollback_is_IDEMPOTENT_when_the_origin_already_matches(self):
        """Re-running a completed rollback must be a no-op, not a refusal."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("rbidem", [("aaa111", 1, "executed", "executed")])
        original = orch.read_text(encoding="utf-8")
        journal = self._worktree_shaped_journal(orch, original)
        for attempt in (1, 2):
            with self.subTest(attempt=attempt):
                ok, msg = LC._rollback_precommit(self.root, journal)
                self.assertTrue(ok, msg)
                self.assertEqual(orch.read_text(encoding="utf-8"), original)

    def test_a_real_FAILED_retirement_leaves_a_peers_edit_intact(self):
        """End to end through the real transaction, not only the rollback helper.

        A fault injected after the move rolls back. The peer's edit to the plan's pending path (landed
        during the transaction, after the up-front dirty check) must survive byte for byte.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("rbreal", [("aaa111", 1, "executed", "executed")])
        original = orch.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT IN FLIGHT, uncommitted\n"
        head = _git(self.root, "rev-parse", "HEAD").strip()
        real_git = LC._git

        def spy_git(root, args):
            # The peer writes while the coordinator worktree is STAGING its own rename, i.e. after the
            # up-front dirty check has passed and before the transaction fails. `git add` is used as
            # the seam rather than `git mv` because the relocation goes through
            # `artifact_core.git_mv`, which owns its own subprocess and is not this wrapper.
            if (
                args
                and args[0] == "add"
                and Path(root).resolve() != self.root.resolve()
            ):
                orch.write_text(peer_bytes, encoding="utf-8")
            return real_git(root, args)

        with mock.patch.object(LC, "_git", spy_git):
            res = self.retire(
                orch, "rbreal", apply=True, fault_injection="before_commit"
            )
        self.assertIn(
            "PEER EDIT IN FLIGHT",
            peer_bytes,
            "fixture sanity: the peer edit must have been composed",
        )
        self.assertNotEqual(res.exit_code, LC.EXIT_OK, res.message)
        self.assertEqual(
            orch.read_text(encoding="utf-8"),
            peer_bytes,
            "a failed retirement destroyed a co-worker's uncommitted bytes",
        )
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)


class AFailedRetirementLeavesTheManifestsAsItFoundThem(RollupTransitionCase):
    """E-01/E-02 of plan `4xt6u4`: the rollback must not WRITE the plans manifests at all.

    WHY THIS CLASS EXISTS BESIDE THE PORCELAIN ASSERTION in
    `TheSharedGatesActuallyFireOnTheRollupPath`. That assertion is the right one at the right site,
    but it cannot see the whole property, for a reason worth stating: the manifests are GITIGNORED in
    the real repository, so `git status --porcelain` there reports NOTHING whether they were created
    or not. (They show as `??` in this fixture only because its `.gitignore` carries `.aw/state/`
    alone.) An assertion that can be satisfied by a file being invisible rather than absent is not
    the assertion this fix needs, so the EXISTENCE of the files is checked directly here.

    BOTH PRIOR-STATE CASES ARE COVERED, because only one of them was ever broken and a test covering
    only that one would not prove the fix is safe:

    * ABSENT beforehand: the measured defect. Regeneration CREATED both manifests, so a tree that had
      none had two. They must be absent again.
    * PRESENT beforehand: regeneration was already byte-exact here (by the time step 4 ran the corpus
      was restored and the generator is deterministic), so this case guards against the fix
      REGRESSING what the old code got right by accident.
    """

    MANIFESTS = ("INDEX.json", "INDEX.md")

    def _manifest_paths(self):
        base = self.root / ".aw" / "records" / "plans"
        return [base / name for name in self.MANIFESTS]

    def _manifest_state(self):
        """Existence + bytes for both manifests, so ABSENT is distinguishable from PRESENT."""
        return {
            p.name: (p.read_bytes() if p.exists() else None)
            for p in self._manifest_paths()
        }

    def _index_check_rc(self) -> int:
        import argparse

        from agent_workflows import plans_index as PIDX

        return PIDX.run_index(
            argparse.Namespace(
                dir=str(self.root),
                check=True,
                agent=False,
                json=False,
                no_color=True,
                limit=None,
                quiet=True,
            )
        )

    def test_manifests_ABSENT_before_a_failed_retirement_are_ABSENT_after(self):
        """The measured defect: `?? INDEX.json` / `?? INDEX.md` appearing out of a FAILED transition."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfabs", [("aaa111", 1, "executed", "executed")])
        for p in self._manifest_paths():
            self.assertFalse(p.exists(), f"fixture sanity: {p.name} must start absent")

        res = self.retire(orch, "mfabs", apply=True, fault_injection="after_move")
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)

        for p in self._manifest_paths():
            self.assertFalse(
                p.exists(),
                f"a FAILED retirement CREATED {p.name}: the rollback regenerated the manifests "
                "instead of leaving the tree as it found it (plan 4xt6u4 F-1)",
            )
        self.assertEqual(
            self._index_check_rc(),
            0,
            "restoring ABSENCE must not leave the repository in a state its own gate rejects; an "
            "ungenerated manifest is check.stale-index-missing at severity info",
        )

    def test_manifests_PRESENT_before_a_failed_retirement_are_BYTE_IDENTICAL_after(
        self,
    ):
        """The case the pre-fix code already handled, pinned so the fix cannot regress it."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfpres", [("aaa111", 1, "executed", "executed")])
        LC._refresh_plans_index_fail_loud(self.root)
        before = self._manifest_state()
        for name, data in before.items():
            self.assertIsNotNone(data, f"fixture sanity: {name} must start present")

        res = self.retire(orch, "mfpres", apply=True, fault_injection="after_move")
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)

        self.assertEqual(
            self._manifest_state(),
            before,
            "a FAILED retirement changed the plans manifests; they must be byte-identical",
        )
        self.assertEqual(self._index_check_rc(), 0)

    def test_a_PEERS_manifest_write_inside_the_window_is_NOT_clobbered(self):
        """The rollback must not overwrite a generated view a co-worker wrote mid-transaction.

        MEASURED pre-fix: a peer's `INDEX.json` bytes were REPLACED by the rollback's regeneration.
        This is why the fix removes the write rather than restoring a journal snapshot: a restore
        would have overwritten these bytes too, or would have had to REFUSE (`unknown-outcome`) and
        thereby wedge an otherwise clean rollback over a regenerable file.
        """

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfpeer", [("aaa111", 1, "executed", "executed")])
        LC._refresh_plans_index_fail_loud(self.root)
        target = self.root / ".aw" / "records" / "plans" / "INDEX.json"
        peer_bytes = '{"peer": "wrote this during the window"}\n'
        real = LC._rollback_precommit

        def spy(repo_root, journal):
            # The peer writes AFTER the transaction's checkpoint, just before the rollback runs.
            target.write_text(peer_bytes, encoding="utf-8")
            return real(repo_root, journal)

        with mock.patch.object(LC, "_rollback_precommit", spy):
            res = self.retire(orch, "mfpeer", apply=True, fault_injection="after_move")

        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            peer_bytes,
            "the rollback clobbered a peer's manifest write",
        )
        # And it still reported a successful restore: manifest state is not the rollback's business.
        self.assertIn("rolled back", res.message)

    def test_the_rollback_does_NOT_write_the_shared_manifests_at_all(self):
        """Pinned as an OBSERVED absence of writes, because the byte-equality tests above cannot
        distinguish "never written" from "written with identical bytes" - and it was the WRITE, not
        the bytes, that produced the defect."""

        from unittest import mock

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfnow", [("aaa111", 1, "executed", "executed")])
        LC._refresh_plans_index_fail_loud(self.root)
        calls: list[str] = []
        real = LC._refresh_plans_index_fail_loud

        def spy(repo_root):
            calls.append(str(repo_root))
            return real(repo_root)

        with mock.patch.object(LC, "_refresh_plans_index_fail_loud", spy):
            res = self.retire(orch, "mfnow", apply=True, fault_injection="after_move")
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN, res.message)
        self.assertEqual(
            calls,
            [],
            "the rollback path refreshed the plans index; step 4 must not write a generated view",
        )

    def test_the_SUCCESS_path_still_regenerates_the_index(self):
        """The success path is UNCHANGED: a successful retirement really does change the corpus."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfok", [("aaa111", 1, "executed", "executed")])
        res = self.retire(orch, "mfok", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_OK, f"{res.message} {res.findings}")
        manifest = (self.root / ".aw" / "records" / "plans" / "INDEX.json").read_text(
            encoding="utf-8"
        )
        name = "20260906-mfok-00-orc000-synthetic.ipd.md"
        self.assertIn(f"executed/{name}", manifest)
        self.assertNotIn(f"pending/{name}", manifest)
        self.assertEqual(self._index_check_rc(), 0)

    def test_the_rollback_STILL_reports_failure_honestly_for_a_REAL_cause(self):
        """Dropping the manifest arm did not make the rollback unable to fail.

        Plan `4xt6u4` E-01 requires stating the fate of the fail-loud arm that step 4 provided
        (`rollback index regeneration failed: ...`). It is GONE with its subject, deliberately: a
        rollback must not be escalated to unknown-outcome by a gitignored generated view. The arms
        that protect real content are untouched, and this pins one of them firing.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("mfarm", [("aaa111", 1, "executed", "executed")])
        rel = LC._repo_relative(self.root, orch)
        dest_rel = rel.replace("/pending/", "/executed/")
        dest = self.root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # A concurrent writer legitimately owns the destination: its bytes are NOT what we wrote.
        dest.write_text("A CONCURRENT WRITER'S CONTENT\n", encoding="utf-8")
        journal = {
            "plan_id": "orc000",
            "original_path": rel,
            "original_bytes": orch.read_text(encoding="utf-8"),
            "dest_path": dest_rel,
            "owned_paths": [rel, dest_rel],
            "git_index_entries": {},
            "moved_bytes": "WHAT THIS TRANSACTION WROTE\n",
            "phase": LC.PHASE_MUTATING,
        }
        ok, msg = LC._rollback_precommit(self.root, journal)
        self.assertFalse(ok, msg)
        self.assertIn("unknown-outcome", msg)
        self.assertEqual(
            dest.read_text(encoding="utf-8"),
            "A CONCURRENT WRITER'S CONTENT\n",
            "the refusal must be non-destructive",
        )

    def test_the_invariant_the_fix_RESTS_on_is_stated_and_holds(self):
        """The pre-commit phase must not write the SHARED manifests; that is what makes E-01 correct.

        THIS IS THE EARLY-WARNING TEST. If a future change makes the pre-commit phase write the shared
        manifests, the rollback would once again have real damage to repair and NOT writing would stop
        being a sufficient fix - at which point the journal snapshot `4xt6u4` OQ-01 considered becomes
        the right mechanism. This is designed to fail first in that case, so the next reader learns it
        from a red test rather than from a second residue bug.

        Measured across every pre-commit fault point x both prior-state cases.
        """

        from agent_workflows import ipd_lifecycle as LC

        self.assertIn(
            "gitignored",
            LC._pre_commit_phase_leaves_manifests_untouched(),
            "the invariant must state WHY it holds, not merely that it does",
        )

        from unittest import mock

        # A DISTINCT Set per case, in the one fixture repo: `make_set` commits its own Set, so the
        # cases do not interfere, and the manifest state is captured immediately before each retire.
        cases = [
            (fault, present)
            for fault in ("before_mutation", "after_move", "before_commit")
            for present in (False, True)
        ]
        for i, (fault, present) in enumerate(cases):
            with self.subTest(fault=fault, manifests_present=present):
                orch = self.make_set(f"inv{i}", [("aaa111", 1, "executed", "executed")])
                if present:
                    LC._refresh_plans_index_fail_loud(self.root)
                else:
                    for p in self._manifest_paths():
                        p.unlink(missing_ok=True)
                expected = self._manifest_state()
                self.assertEqual(
                    all(v is not None for v in expected.values()),
                    present,
                    "fixture sanity: the prior state is not the one this case intends",
                )

                seen: dict = {}
                real = LC._rollback_precommit

                def spy(repo_root, journal, _real=real, _seen=seen):
                    _seen["at_entry"] = self._manifest_state()
                    return _real(repo_root, journal)

                with mock.patch.object(LC, "_rollback_precommit", spy):
                    self.retire(orch, f"inv{i}", apply=True, fault_injection=fault)

                self.assertEqual(
                    seen.get("at_entry"),
                    expected,
                    "the pre-commit phase wrote the SHARED plans manifests before the rollback "
                    "ran, so `_rollback_precommit` no longer restores them by leaving them "
                    "alone. Re-read `_pre_commit_phase_leaves_manifests_untouched`: a journal "
                    "snapshot (index_json_before/index_md_before) is now the correct mechanism.",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

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
"""

from __future__ import annotations

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
    def test_a_set_whose_children_are_all_in_executed_is_returned_in_full(self):
        """THE CROSS-RUN CASE, which is the whole reason this predicate reads disk.

        None of these children is in any queue - there is no run state in this repo at all - and the
        maintainer's requirement is that such a Set still be seen as complete. A queue-scoped check
        cannot answer this, which is the defect.
        """

        self.make_set(
            "xrun",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
            ],
        )
        m = rs.read_set_membership(self.root, "xrun")
        self.assertIsNotNone(m.orchestrator)
        assert m.orchestrator is not None
        self.assertEqual(m.orchestrator.id6, "orc000")
        self.assertEqual([c.id6 for c in m.children], ["aaa111", "bbb222", "ccc333"])
        self.assertEqual({c.status for c in m.children}, {"executed"})
        self.assertFalse((self.root / ".aw" / "records" / "runs").exists())

    def test_members_split_across_pending_and_executed_are_both_seen(self):
        self.make_set(
            "mixed",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
            ],
        )
        m = rs.read_set_membership(self.root, "mixed")
        self.assertEqual(
            {(c.id6, c.status) for c in m.children},
            {("aaa111", "executed"), ("bbb222", "approved")},
        )

    def test_the_orchestrator_is_distinguished_by_kind_not_by_counting(self):
        self.make_set("kinds", [("aaa111", 1, "executed", "executed")])
        m = rs.read_set_membership(self.root, "kinds")
        assert m.orchestrator is not None
        self.assertTrue(m.orchestrator.is_orchestrator)
        self.assertEqual(m.orchestrator.kind, "orchestrator")
        self.assertEqual(len(m.members), 2)
        self.assertEqual(len(m.children), 1)

    def test_a_legacy_order_zero_plan_with_no_kind_bullet_is_still_the_orchestrator(
        self,
    ):
        """74 plans in this repo carry `Order: 0` and NO `Kind:` bullet (measured).

        Reading `Kind` alone would count those as children, making an old Set look permanently
        one-child-short. The `Order == 0` fallback keeps them recognized.
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
        """The pin's one honest cost, asserted rather than left to be discovered.

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
        """Pins the "no live Set collides today" claim the guard's note makes."""

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
    def test_a_complete_set_is_eligible(self):
        self.make_set(
            "good",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
        )
        d = rs.evaluate_set_retirement(self.root, "good")
        self.assertTrue(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_ELIGIBLE)
        self.assertEqual(d.unfinished, ())
        self.assertEqual(d.unauthored_rows, ())

    def test_unfinished_children_are_named_WITH_their_actual_statuses(self):
        """R-9: a refusal that cannot name what it is waiting for is the `5e4sb6` defect."""

        self.make_set(
            "unfin",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
                ("ccc333", 3, "reviewed", "pending"),
            ],
        )
        d = rs.evaluate_set_retirement(self.root, "unfin")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
        self.assertEqual(
            dict(d.unfinished), {"bbb222": "approved", "ccc333": "reviewed"}
        )
        self.assertIn("bbb222", d.detail)
        self.assertIn("approved", d.detail)
        self.assertNotIn("aaa111", d.detail)

    def test_a_set_with_no_children_refuses_with_its_OWN_reason(self):
        """The case that produced `(False, [])` and an event naming no dependency at all."""

        self.make_set("nokids", [], declared_rows=[])
        d = rs.evaluate_set_retirement(self.root, "nokids")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_NO_CHILDREN)
        self.assertNotEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
        self.assertEqual(d.unfinished, ())
        self.assertTrue(d.detail)

    def test_a_set_with_no_orchestrator_refuses_with_its_OWN_reason(self):
        self.make_set(
            "noorc",
            [("aaa111", 1, "executed", "executed")],
            with_orchestrator=False,
        )
        d = rs.evaluate_set_retirement(self.root, "noorc")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_NO_ORCHESTRATOR)

    def test_unauthored_child_rows_refuse_and_carry_the_literal_tokens(self):
        self.make_set(
            "unauth",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            declared_rows=["01", "02", "03"],
        )
        d = rs.evaluate_set_retirement(self.root, "unauth")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
        self.assertEqual(d.unauthored_rows, ("03",))

    def test_the_four_refusal_reasons_are_all_distinct(self):
        self.assertEqual(
            len(
                {
                    rs.RETIRE_ELIGIBLE,
                    rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
                    rs.RETIRE_REFUSED_NO_CHILDREN,
                    rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS,
                    rs.RETIRE_REFUSED_NO_ORCHESTRATOR,
                }
            ),
            5,
        )

    def test_every_decision_carries_a_nonempty_detail(self):
        """A caller must never have to invent the sentence it writes into the durable record."""

        self.make_set("d1", [("aaa111", 1, "executed", "executed")])
        self.make_set("d2", [("bbb222", 1, "approved", "pending")])
        self.make_set("d3", [], declared_rows=[])
        for setid in ("d1", "d2", "d3", "nosuch"):
            with self.subTest(setid=setid):
                self.assertTrue(rs.evaluate_set_retirement(self.root, setid).detail)


class ExecutedIsAnAllowlist(SyntheticSetCase):
    """R-2: exactly `executed` qualifies, and NOTHING else.

    ASSERTED AS AN ALLOWLIST rather than as a denylist of known-bad values, because a denylist
    silently admits any status added to the vocabulary later - which is how a conservative gate stops
    gating without anyone editing it.
    """

    NON_EXECUTED = (
        "substantially-complete",
        "approved",
        "reviewed",
        "to-review",
        "draft",
        "blocked",
        "dependency-blocked",
        "integration-blocked",
        "merge-conflict",
        "partial",
        "superseded",
        "not-executed",
        "executing",
        "Executed",
        "EXECUTED",
        "executed-ish",
        "some-status-nobody-has-invented-yet",
    )

    def test_only_the_exact_token_executed_qualifies(self):
        for status in self.NON_EXECUTED:
            with self.subTest(status=status):
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
                    body=_table(
                        ["Order", "Id", "Child", "Depends on"], [["01", "x", "x", "x"]]
                    ),
                )
                d = rs.evaluate_set_retirement(repo.root, "allow")
                self.assertFalse(d.eligible, f"{status!r} must NOT qualify as executed")
                self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
                self.assertEqual(dict(d.unfinished), {"aaa111": status})

    def test_substantially_complete_is_refused_and_the_reason_names_it(self):
        """`substantially-complete` means finalize REFUSED (`i452hf`), so it is not done.

        HONEST ABOUT WHAT THIS GUARDS. `substantially-complete` is a RUN-STATE disposition, not a
        plan-file `Status:`. Measured: `nna8yz`'s plan file carries `- Status: approved`, and
        `substantially-complete` appears for it only inside a run's `state.json`. Since this predicate
        reads the PLANS TREE, it will not encounter that value from its own input at all; the guard
        defends against the value arriving from ANOTHER caller. This test therefore proves the guard,
        NOT that real plan data contains the value.
        """

        self.make_set("subc", [("aaa111", 1, "substantially-complete", "pending")])
        d = rs.evaluate_set_retirement(self.root, "subc")
        self.assertFalse(d.eligible)
        self.assertIn("substantially-complete", d.detail)

    def test_the_real_nna8yz_plan_file_carries_approved_not_substantially_complete(
        self,
    ):
        """Pins the F-5 measurement, so the docstring above cannot rot into a false claim."""

        m = rs.read_set_membership(REPO_ROOT, "lanectn")
        by_id = {c.id6: c.status for c in m.children}
        self.assertEqual(by_id.get("nna8yz"), "approved")
        self.assertNotIn("substantially-complete", set(by_id.values()))

    def test_a_child_with_no_status_bullet_is_refused_not_assumed_done(self):
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260906-nostat-01-aaa111-synthetic.ipd.md").write_text(
            "# IPD: x\n- Kind: child\n- Set: nostat\n- Order: 1\n- Id: aaa111\n\n",
            encoding="utf-8",
        )
        _write_plan(
            self.root,
            "pending",
            plan_id="orc000",
            set_id="nostat",
            order=0,
            status="approved",
            kind="orchestrator",
            body=_table(
                ["Order", "Id", "Child", "Depends on"], [["01", "x", "x", "x"]]
            ),
        )
        d2 = rs.evaluate_set_retirement(self.root, "nostat")
        self.assertFalse(d2.eligible)
        self.assertEqual(d2.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)


# ==================================================================================================
# V-03: the FOUR real column shapes, copied from this repo's measured orchestrators
# ==================================================================================================


class RealColumnShapeFixtures(SyntheticSetCase):
    """Each fixture COPIES a live orchestrator's column layout verbatim.

    A synthetic table in this plan's own format would exercise the one shape the parser was always
    going to handle and none of the four that could break it.
    """

    #: `rununify` (`5e4sb6`): THREE columns and NO `Id` column, with the non-numeric tokens `03+`
    #: and `last`. A parser keyed on a named `Id` header crashes or vacuously passes here.
    RUNUNIFY_HEADER = ["Order", "What it does", "Depends on"]
    #: `wslayout` (`rh5tt6`): four columns, all five rows resolve.
    WSLAYOUT_HEADER = ["Order", "Id", "What it does", "Set dependencies"]
    #: `runprofile` (`3m0urk`): five columns; declares 01-05 while SIX children exist on disk.
    RUNPROFILE_HEADER = ["Order", "Id", "Child", "Responsibility", "Depends on"]
    #: `lanectn` (`h0zljh`): six columns, including a `Depth` column.
    LANECTN_HEADER = [
        "Order",
        "Id",
        "Depth",
        "Requirements owned",
        "Prerequisite",
        "What it delivers",
    ]

    def test_rununify_shape_no_id_column_and_non_numeric_tokens_refuses(self):
        self.make_set(
            "shapeA",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            header=self.RUNUNIFY_HEADER,
            declared_rows=["01", "02", "03+", "last"],
        )
        d = rs.evaluate_set_retirement(self.root, "shapeA")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
        self.assertEqual(d.unauthored_rows, ("03+", "last"))

    def test_the_rununify_table_parses_without_an_id_column(self):
        """The parse must SUCCEED on the Id-less shape; a crash would be a silent pass upstream."""

        self.make_set(
            "shapeA2",
            [("aaa111", 1, "executed", "executed")],
            header=self.RUNUNIFY_HEADER,
            declared_rows=["01"],
        )
        m = rs.read_set_membership(self.root, "shapeA2")
        assert m.orchestrator is not None
        tokens, parsed = rs.parse_declared_child_orders(
            m.orchestrator.path.read_text(encoding="utf-8")
        )
        self.assertTrue(parsed)
        self.assertEqual(tokens, ("01",))

    def test_wslayout_shape_all_rows_resolve_is_eligible(self):
        self.make_set(
            "shapeB",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
                ("ddd444", 4, "executed", "executed"),
                ("eee555", 5, "executed", "executed"),
            ],
            header=self.WSLAYOUT_HEADER,
        )
        d = rs.evaluate_set_retirement(self.root, "shapeB")
        self.assertTrue(d.eligible, d.detail)
        self.assertEqual(d.unauthored_rows, ())

    def test_runprofile_shape_more_children_on_disk_than_declared_does_NOT_refuse(self):
        """F-7: the comparison is ONE-DIRECTIONAL.

        `runprofile` declares Orders 01-05 and has SIX children on disk. A symmetric "table and disk
        must match" rule would refuse a legitimately-extended Set forever. The extra child's
        non-`executed` status is R-2's business; an undeclared row is not R-3's.
        """

        self.make_set(
            "shapeC",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("ccc333", 3, "executed", "executed"),
                ("ddd444", 4, "executed", "executed"),
                ("eee555", 5, "executed", "executed"),
                ("fff666", 6, "executed", "executed"),
            ],
            header=self.RUNPROFILE_HEADER,
            declared_rows=["01", "02", "03", "04", "05"],
        )
        d = rs.evaluate_set_retirement(self.root, "shapeC")
        self.assertEqual(d.unauthored_rows, ())
        self.assertTrue(d.eligible, d.detail)

    def test_runprofile_shape_undeclared_extra_child_still_gates_on_R2(self):
        """The undeclared sixth child must still be refused when it is not `executed` - via R-2."""

        self.make_set(
            "shapeC2",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
                ("fff666", 6, "reviewed", "pending"),
            ],
            header=self.RUNPROFILE_HEADER,
            declared_rows=["01", "02"],
        )
        d = rs.evaluate_set_retirement(self.root, "shapeC2")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
        self.assertEqual(dict(d.unfinished), {"fff666": "reviewed"})

    def test_lanectn_six_column_shape_with_a_depth_column_parses(self):
        self.make_set(
            "shapeD",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            header=self.LANECTN_HEADER,
        )
        d = rs.evaluate_set_retirement(self.root, "shapeD")
        self.assertTrue(d.eligible, d.detail)


class ParserFailsClosed(SyntheticSetCase):
    """An unparseable or ambiguous table REFUSES; it is never read as "fully authored"."""

    def test_a_table_with_no_recognizable_rows_refuses(self):
        body = (
            f"## {rs._CHILD_IPDS_HEADING}\n\n"
            "The child breakdown is DELIBERATELY NOT FIXED HERE. Prose only, no table.\n"
        )
        self.make_set(
            "noparse",
            [("aaa111", 1, "executed", "executed")],
            orchestrator_body=body,
        )
        d = rs.evaluate_set_retirement(self.root, "noparse")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
        self.assertIn("no rows could be parsed", d.detail)

    def test_a_missing_child_ipds_section_refuses(self):
        self.make_set(
            "nosection",
            [("aaa111", 1, "executed", "executed")],
            orchestrator_body="## Goal\n\nx\n",
        )
        d = rs.evaluate_set_retirement(self.root, "nosection")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)

    def test_assorted_unresolvable_tokens_all_refuse(self):
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

    def test_the_header_and_alignment_rows_are_not_mistaken_for_declared_children(self):
        self.make_set(
            "hdr",
            [("aaa111", 1, "executed", "executed")],
            declared_rows=["01"],
        )
        m = rs.read_set_membership(self.root, "hdr")
        assert m.orchestrator is not None
        tokens, parsed = rs.parse_declared_child_orders(
            m.orchestrator.path.read_text(encoding="utf-8")
        )
        self.assertTrue(parsed)
        self.assertEqual(tokens, ("01",))

    def test_a_right_aligned_separator_row_is_still_skipped(self):
        """`wslayout` and `runprofile` both use `|---:|---|` alignment rows."""

        body = "\n".join(
            [
                f"## {rs._CHILD_IPDS_HEADING}",
                "",
                "| Order | Id | What it does | Set dependencies |",
                "|---:|---|---|---|",
                "| 01 | `aaa111` | x | none |",
                "",
            ]
        )
        self.make_set(
            "align",
            [("aaa111", 1, "executed", "executed")],
            orchestrator_body=body,
        )
        d = rs.evaluate_set_retirement(self.root, "align")
        self.assertTrue(d.eligible, d.detail)

    def test_decorated_order_tokens_are_read(self):
        """`rununify` writes `| 01 | **AUTHORED ...** |`; a bolded/ticked token must still parse."""

        body = "\n".join(
            [
                f"## {rs._CHILD_IPDS_HEADING}",
                "",
                "| Order | What it does | Depends on |",
                "|---|---|---|",
                "| `01` | x | none |",
                "| **02** | x | 01 |",
                "",
            ]
        )
        self.make_set(
            "deco",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "executed", "executed"),
            ],
            orchestrator_body=body,
        )
        d = rs.evaluate_set_retirement(self.root, "deco")
        self.assertTrue(d.eligible, d.detail)

    def test_a_table_in_another_section_is_not_read(self):
        body = "\n".join(
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
        )
        self.make_set(
            "othersect",
            [("aaa111", 1, "executed", "executed")],
            orchestrator_body=body,
        )
        d = rs.evaluate_set_retirement(self.root, "othersect")
        self.assertTrue(d.eligible, d.detail)
        m = rs.read_set_membership(self.root, "othersect")
        assert m.orchestrator is not None
        tokens, _ = rs.parse_declared_child_orders(
            m.orchestrator.path.read_text(encoding="utf-8")
        )
        self.assertEqual(tokens, ("01",))


# ==================================================================================================
# The predicate against THIS repository's real Sets (the measurements the plan is built on)
# ==================================================================================================


class RealRepositorySets(unittest.TestCase):
    """Pins the four measured outcomes, so a regression names the Set that broke.

    These read the repo the tests run in. Each assertion is written against the CURRENT measured
    state; if a maintainer later executes `kgpptv` or authors `rununify`'s remaining children, the
    corresponding test will fail LOUDLY and must be re-measured rather than loosened.
    """

    def test_wslayout_is_eligible_all_five_children_executed(self):
        d = rs.evaluate_set_retirement(REPO_ROOT, "wslayout")
        self.assertTrue(d.eligible, d.detail)
        self.assertEqual(d.reason, rs.RETIRE_ELIGIBLE)

    def test_lanectn_refuses_naming_its_two_unfinished_children(self):
        d = rs.evaluate_set_retirement(REPO_ROOT, "lanectn")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
        self.assertEqual(
            dict(d.unfinished), {"nna8yz": "approved", "xdr83v": "approved"}
        )

    def test_rununify_refuses_for_unauthored_rows_not_for_unfinished_children(self):
        """The 2.5 case: both children ARE executed, so a naive rule would retire `5e4sb6`."""

        m = rs.read_set_membership(REPO_ROOT, "rununify")
        self.assertEqual({c.status for c in m.children}, {"executed"})
        d = rs.evaluate_set_retirement(REPO_ROOT, "rununify")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNAUTHORED_CHILD_ROWS)
        self.assertEqual(set(d.unauthored_rows), {"03+", "last"})

    def test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows(self):
        d = rs.evaluate_set_retirement(REPO_ROOT, "runprofile")
        self.assertFalse(d.eligible)
        self.assertEqual(d.reason, rs.RETIRE_REFUSED_UNFINISHED_CHILDREN)
        self.assertEqual(dict(d.unfinished), {"kgpptv": "reviewed"})
        m = rs.read_set_membership(REPO_ROOT, "runprofile")
        assert m.orchestrator is not None
        unauth, parsed = rs.find_unauthored_child_rows(
            m.orchestrator.path.read_text(encoding="utf-8"), m
        )
        self.assertTrue(parsed)
        self.assertEqual(unauth, ())

    def test_every_live_orchestrators_table_parses(self):
        """All five measured column shapes must PARSE; a crash here is the vacuous-pass risk."""

        for setid in ("wslayout", "lanectn", "rununify", "runprofile", "orchretire"):
            with self.subTest(setid=setid):
                m = rs.read_set_membership(REPO_ROOT, setid)
                self.assertIsNotNone(m.orchestrator)
                assert m.orchestrator is not None
                tokens, parsed = rs.parse_declared_child_orders(
                    m.orchestrator.path.read_text(encoding="utf-8")
                )
                self.assertTrue(parsed, f"{setid}'s child table did not parse")
                self.assertTrue(tokens)


# ==================================================================================================
# Scope fence: this child DECIDES ONLY
# ==================================================================================================


class ThisChildDecidesOnly(unittest.TestCase):
    """`5942n7` owns the decision; `ueg5cf` the transition and `pgq326` the wiring.

    Pinned as a test rather than trusted to review, because "the predicate quietly grew a transition"
    is the failure that would make a wrong decision able to MOVE a plan.
    """

    def test_the_predicate_module_region_performs_no_transition(self):
        import inspect

        for fn in (
            rs.evaluate_set_retirement,
            rs.read_set_membership,
            rs.find_unauthored_child_rows,
            rs.parse_declared_child_orders,
        ):
            src = inspect.getsource(fn)
            with self.subTest(fn=fn.__name__):
                for forbidden in (
                    "ipd_set",
                    "set executed",
                    "finalize",
                    "shutil.move",
                    "git mv",
                    "write_text",
                    "subprocess",
                ):
                    self.assertNotIn(
                        forbidden,
                        src,
                        f"{fn.__name__} must DECIDE only; `{forbidden}` implies it acts",
                    )

    def test_execution_success_states_was_not_touched(self):
        """Spec Section 4 puts `EXECUTION_SUCCESS_STATES` out of scope for this Set."""

        from agent_workflows import oc_runipd

        self.assertIn("substantially-complete", oc_runipd.EXECUTION_SUCCESS_STATES)
        self.assertNotEqual(
            rs.SET_RETIREMENT_DONE_STATUS, oc_runipd.EXECUTION_SUCCESS_STATES
        )

    def test_the_queue_scoped_predicate_is_left_in_place_for_child_03(self):
        """This child does NOT change `_set_children_all_executed` or its callers."""

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
    """V-01/V-05, THE REGRESSION THAT MATTERS MOST: the exemption must not widen."""

    def test_a_child_plan_is_refused_by_the_rollup_route(self):
        from agent_workflows import ipd_lifecycle as LC

        self.make_set("kid", [("aaa111", 1, "executed", "executed")])
        child = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260906-kid-01-aaa111-synthetic.ipd.md"
        )
        res = self.retire(child, "kid", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_NOT_ORCHESTRATOR, res.findings)
        self.assertIn("not an orchestrator", res.message)

    def test_a_child_plan_in_an_ELIGIBLE_set_is_STILL_refused(self):
        """The dangerous shape: everything else about the call is legitimate.

        A Kind check that ran only when something else already failed would pass a happy-path test
        and still be a hole. Here the Set IS eligible and the actor IS valid; only `Kind` differs.
        """

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared as rs

        self.make_set("kid2", [("aaa111", 1, "executed", "executed")])
        self.assertTrue(rs.evaluate_set_retirement(self.root, "kid2").eligible)
        child = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260906-kid2-01-aaa111-synthetic.ipd.md"
        )
        res = self.retire(child, "kid2", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_NOT_ORCHESTRATOR, res.findings)

    def test_an_APPROVED_PENDING_child_with_unperformed_items_is_refused(self):
        """THE CASE THIS WHOLE PLAN MUST NEVER ENABLE, isolated so nothing else can mask it.

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
        """THE ACTUAL BYPASS, measured. This is the strongest test in the module.

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

    def test_an_orchestrator_whose_set_is_INELIGIBLE_is_refused(self):
        """`Kind: orchestrator` alone is NOT authority (F-9).

        `action_for` returns `orchestrate` from `reviewed` onward, so a Kind-only route would retire
        an orchestrator whose children are still in flight. The eligibility verdict is required IN the
        transition, not merely by a well-behaved caller.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set(
            "unfin",
            [
                ("aaa111", 1, "executed", "executed"),
                ("bbb222", 2, "approved", "pending"),
            ],
        )
        res = self.retire(orch, "unfin", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_SET_INELIGIBLE, res.findings)
        self.assertIn("bbb222", res.message)
        self.assertTrue(orch.is_file(), "an ineligible orchestrator must not move")

    def test_an_orchestrator_with_unauthored_child_rows_is_refused(self):
        """The `rununify`/`5e4sb6` case reaching the TRANSITION, not just the predicate."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set(
            "unauth",
            [("aaa111", 1, "executed", "executed")],
            declared_rows=["01", "03+"],
        )
        res = self.retire(orch, "unauth", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_SET_INELIGIBLE, res.findings)
        self.assertIn("03+", res.message)

    def test_a_supplied_ineligible_verdict_is_VALIDATED_not_trusted(self):
        """A caller may hand in a decision to avoid recomputing; it must still be checked."""

        from agent_workflows import ipd_lifecycle as LC
        from agent_workflows import runner_shared as rs

        orch = self.make_set("hand", [("aaa111", 1, "executed", "executed")])
        forged = rs.RetirementDecision(
            eligible=False,
            reason=rs.RETIRE_REFUSED_UNFINISHED_CHILDREN,
            setid="hand",
            detail="caller says no",
        )
        res = self.retire(orch, "hand", apply=True, eligibility=forged)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_SET_INELIGIBLE, res.findings)
        self.assertTrue(orch.is_file())

    def test_an_already_terminal_orchestrator_is_refused(self):
        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set(
            "done",
            [("aaa111", 1, "executed", "executed")],
            orchestrator_status="executed",
        )
        res = self.retire(orch, "done", apply=True)
        self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
        self.assertIn(LC.ROLLUP_REFUSED_ALREADY_TERMINAL, res.findings)


class TheHumanFacingGateIsUNCHANGED(RollupTransitionCase):
    """V-01: `aw ipd finalize` on an orchestrator STILL faces the E/V requirement.

    This is the assertion that proves the opening is confined to the runner-owned route. If a human
    (or an agent) runs the ordinary finalize on an orchestrator, the six `IPD-S404` findings must
    still appear exactly as they do today.
    """

    def test_the_ordinary_finalize_still_refuses_an_orchestrator(self):
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
        """The CHILD-plan gate, stated separately so it cannot regress unnoticed."""

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
        # The ONLY other paths are the owned index artifacts. Enumerated exactly rather than by
        # prefix, so a rollup that started committing some other plans-tree file would fail.
        self.assertEqual(
            changed - expected,
            {".aw/records/plans/INDEX.json", ".aw/records/plans/INDEX.md"},
            sorted(changed),
        )


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
        """Not a second wording that could drift from `AW-LIFECYCLE-ROLE-001`."""

        import inspect

        from agent_workflows import ipd_lifecycle as LC

        src = inspect.getsource(LC.retire_orchestrator)
        self.assertIn("LIFECYCLE_ROLE_ERROR", src)
        self.assertIn("worker_role_active", src)


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
        """The journal is load-bearing, not decorative: a mid-transaction failure restores state."""

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("faulty", [("aaa111", 1, "executed", "executed")])
        before = orch.read_text(encoding="utf-8")
        head = _git(self.root, "rev-parse", "HEAD").strip()
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

    def test_a_stale_pre_commit_journal_is_ROLLED_BACK_before_a_fresh_attempt(self):
        """Early crash recovery on THIS path, using the shared helper.

        A previous rollup that died mid-mutation leaves a pre-commit journal. The next attempt must
        finish that rollback idempotently and then proceed, rather than building on half-mutated state.
        """

        from agent_workflows import ipd_lifecycle as LC

        orch = self.make_set("recov", [("aaa111", 1, "executed", "executed")])
        first = self.retire(orch, "recov", apply=True, fault_injection="before_commit")
        self.assertEqual(first.exit_code, LC.EXIT_CANNOT_RUN, first.message)
        self.assertTrue(orch.is_file())
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
        """Fail-loud, not the `status_set` swallow: a stale index is a transaction failure."""

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
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(), head)

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

    def test_the_gates_that_CAN_be_shared_as_code_ARE(self):
        """Stronger than naming them: these are literally the same functions, so they cannot drift.

        Asserted on the SOURCE because the property is "this path calls that code", which no runtime
        observation of a passing retirement can distinguish from a faithful copy.
        """

        import inspect

        from agent_workflows import ipd_lifecycle as LC

        rollup = inspect.getsource(LC.retire_orchestrator)
        main = inspect.getsource(LC.finalize)
        for shared_call in (
            "_early_recovery_result",
            "acquire_finalize_lock",
            "release_finalize_lock",
            "_finalize_transaction",
        ):
            with self.subTest(call=shared_call):
                # `assertTrue(x in src)` rather than `assertIn`, because assertIn's default message
                # dumps the ENTIRE function source (hundreds of lines) into the failure output, which
                # buries the one fact the reader needs.
                self.assertTrue(
                    shared_call in rollup,
                    f"retire_orchestrator no longer calls {shared_call}; the rollup must REUSE that "
                    "code, not re-implement it, or the two transition paths can drift",
                )
                self.assertTrue(
                    shared_call in main,
                    f"finalize no longer calls {shared_call}; if the main path genuinely dropped "
                    "this gate, decide deliberately whether the rollup should too, and update "
                    "ROLLUP_SHARED_GATES either way",
                )

    def test_the_rollup_does_NOT_reimplement_the_move_commit_or_index_refresh(self):
        """It delegates to `_finalize_transaction`; a private copy is the drift this pins."""

        import inspect

        from agent_workflows import ipd_lifecycle as LC

        src = inspect.getsource(LC.retire_orchestrator)
        for forbidden in ('"commit"', "apply_status_change", "shutil.move"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(
                    forbidden,
                    src,
                    f"the rollup must not perform its own {forbidden}; delegate to "
                    "_finalize_transaction so the two paths cannot diverge",
                )


class TheRejectedShapeWasNotTaken(unittest.TestCase):
    """V-01: `ipd_lint.py` is UNTOUCHED, which is the positive evidence for OQ-01's resolution.

    The maintainer rejected shape (a), a linter exemption, because a safety check that learns one
    narrow exception is how it quietly stops protecting anything. An empty diff is the assertion; a
    later reader "simplifying" this Set into the exemption would fail here.
    """

    def test_the_honesty_checker_has_no_orchestrator_concept(self):
        text = (REPO_ROOT / "agent_workflows" / "ipd_lint.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            text.lower().count("orchestrator"),
            0,
            "ipd_lint.py must not learn a Kind-aware exception (spec 77tr3o OQ-1 rejected shape (a))",
        )

    def test_the_pre_transition_ev_requirement_is_still_unconditional(self):
        """Directly, on the checker: an orchestrator gets the same findings as anything else."""

        from agent_workflows import ipd_lint as L

        doc = L.parse(
            _plan_text(
                plan_id="orc000",
                set_id="s",
                order=0,
                status="approved",
                kind="orchestrator",
                body=(
                    "## Detailed Implementation Checklist (TODO)\n\n"
                    "- [ ] E-01 do a thing.\n"
                    "  - Depends on: none\n"
                    "  - Expected outcome: x\n"
                    "  - Execution state: pending\n"
                ),
            )
        )
        diags = L.check_checkpoint(doc, "pre-transition", "pending")
        self.assertTrue(
            any("E-01" in d.message and "performed" in d.message for d in diags),
            [d.message for d in diags],
        )

    def test_the_lint_module_is_not_in_this_plans_scope_paths(self):
        """Belt and braces: the plan itself declares the file out of bounds."""

        plans = REPO_ROOT / ".aw" / "records" / "plans"
        matches = list(plans.glob("*/*ueg5cf*.ipd.md"))
        self.assertTrue(matches, "this plan's own file should be findable")
        text = matches[0].read_text(encoding="utf-8")
        scope = next(ln for ln in text.splitlines() if ln.startswith("- Scope-Paths:"))
        self.assertNotIn("ipd_lint", scope)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

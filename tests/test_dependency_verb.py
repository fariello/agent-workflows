"""depverb Order 01 (`f6idxs`): the dependency CLI's two closed gaps, pinned case by case.

THE TWO DEFECTS THIS PINS, both measured against pristine HEAD `3c9663d5` before the fix:

  GAP 4 - `aw ipd dependencies set` validated the dependency GRAMMAR pre-write but not the target's
  EXISTENCE, so a typo was ACCEPTED, exit 0, and genuinely WRITTEN into `- Item-Dependencies:`, in
  all THREE edge forms. The error then arrived later and from a DIFFERENT surface (`aw check`). That
  contradicted the stated requirement that the id6 "MUST be validated before it can be set".

  GAP 2 - there was no `remove` subcommand at all (`invalid choice: 'remove' (choose from 'set')`),
  so dropping ONE edge from a many-edge statement meant re-stating the whole list by hand, which is
  exactly the hand-editing the verbs exist to prevent and which silently races a concurrent edit.

WHAT IS ASSERTED HERE, and why each case exists rather than being folded into another:
  * (a,b,c) a dangling target in EACH of the three edge forms is refused PRE-WRITE, and the proof is
    that the on-disk line is UNCHANGED, not that the command printed something;
  * (d) a VALID target still succeeds, so the new gate is not a blanket refusal;
  * (e) `--allow-dangling` proceeds AND NAMES the admitted target, so a deliberate forward reference
    stays possible and stays visible in the transcript;
  * (j) an AMBIGUOUS target is refused, and is STILL refused under `--allow-dangling`, because
    unlike a forward reference it can never become valid by waiting;
  * (f,g) `remove` drops one edge of three leaving the rest BYTE-IDENTICAL, and an emptied statement
    becomes the explicit `none` (the grammar's zero), never `unresolved`;
  * (h,i) an ABSENT edge is an ERROR naming it, `--if-present` downgrades that to a clean no-op, and
    a repeat is idempotent;
  * (k) a DANGLING edge is still REMOVABLE, proving the new validation did NOT leak into `remove`
    and make a broken edge unfixable;
  * (l) an edge spelled non-canonically is still MATCHED by `remove`, proving canonical comparison;
  * (m,n) the two behaviors that ALREADY worked and must not regress: the setid-shaped grammar
    refusal and `set`'s clear-by-`none`/`-` path;
  * an ANTI-DIVERGENCE guard covering `status_set.py` and `cli.py`, which the existing
    `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` provably CANNOT do (it scans
    `_DRIVER_SOURCES`, exactly the two runner files).

EVERY MUTATING CASE RUNS AGAINST A FIXTURE REPOSITORY, never the live tree, because these verbs
rewrite plan front matter. Assertions are scoped to the `- Item-Dependencies:` LINE rather than
whole-file equality, because the shared setter ALSO appends a `## Workflow history` receipt and, on an
`approved` plan, rewrites `- Approval:` (`apply_status_change`'s behavior for EVERY setter, not this
verb's doing); a whole-file assertion would fail on that unrelated churn.
"""

from __future__ import annotations

import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import check_engine, cli
from agent_workflows import ipd_schema as S
from agent_workflows import status_set
from tests.support import REPO_ROOT

_DEP_LINE_RE = re.compile(r"(?m)^- Item-Dependencies:[^\n]*$")


def _plan_text(
    id6: str, *, order: int, deps: str | None, status: str = "approved"
) -> str:
    dep = f"- Item-Dependencies: {deps}\n" if deps is not None else ""
    return (
        f"# IPD: probe {id6}\n\n"
        f"- Date: 2026-09-08\n"
        f"- Kind: child\n"
        f"- Scope-Paths: x.py\n"
        f"{dep}"
        f"- Status: {status}\n"
        f"- Set: fix\n"
        f"- Order: {order}\n"
        f"- Id: {id6}\n"
        f"- Approval: 2026-09-08, recorded by a human\n\n"
        f"## Workflow history\n- 2026-09-08 draft (t): created.\n\n"
        f"## Goal\n\nProbe.\n"
    )


class _FixtureRepo:
    """A throwaway repository for the MUTATING dependency verbs.

    Seeds real plan/spec/backlog targets plus a DUPLICATE-id6 pair, so the `ambiguous` verdict can be
    exercised. That duplicate mirrors a state this repository genuinely contains (id6 `uyeko5` is
    owned by one `plans` record and two `research` records), so the case is real, not contrived.
    """

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pending = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending.mkdir(parents=True)
        (self.root / ".aw" / "config").mkdir(parents=True)
        self.plan = self._plan("aaaaaa", 1, "none")
        self._plan("bbbbbb", 2, "none")  # a real, resolvable plans target
        self._plan("cccccc", 3, "none")  # a second real plans target
        # AMBIGUOUS seed: ONE id6 owned by TWO plans records.
        self._plan("dupdup", 4, "none")
        self._plan("dupdup", 5, "none")
        specs = self.root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260101-1200-01-ssssss-s.spec.md").write_text(
            "# Spec ssssss\n\n- Id: ssssss\n- Status: approved\n\n## Summary\n\ns\n",
            encoding="utf-8",
        )
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True)
        (bl / "20260101-01-bbbklg-b.backlog.md").write_text(
            "# Backlog bbbklg\n\n- Id: bbbklg\n- Status: open\n\n## Summary\n\nb\n",
            encoding="utf-8",
        )

    def _plan(self, id6: str, order: int, deps: str | None) -> Path:
        p = self.pending / f"20260908-fix-{order:02d}-{id6}-p.ipd.md"
        p.write_text(_plan_text(id6, order=order, deps=deps), encoding="utf-8")
        return p

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def dep_line(self, path: Path | None = None) -> str:
        """The plan's `- Item-Dependencies:` LINE only (F-13: never whole-file equality)."""
        m = _DEP_LINE_RE.search((path or self.plan).read_text(encoding="utf-8"))
        return m.group(0) if m else ""


class _VerbCase(unittest.TestCase):
    """Shared fixture + a CLI runner that captures output and returns (rc, text)."""

    def setUp(self) -> None:
        self.fx = _FixtureRepo()
        self.addCleanup(self.fx.cleanup)

    def run_cli(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["ipd", "dependencies", *argv, "--yes", "--dir", str(self.fx.root)]
            )
        return rc, buf.getvalue()

    def set_deps(self, *argv: str) -> tuple[int, str]:
        return self.run_cli("set", "aaaaaa", *argv)

    def remove_deps(self, *argv: str) -> tuple[int, str]:
        return self.run_cli("remove", "aaaaaa", *argv)


# ======================================================================================
# E-01 / V-01: a dangling target is refused PRE-WRITE, in every edge form.
# ======================================================================================


class DanglingRefusedPreWriteTests(_VerbCase):
    #: (a), (b), (c). All three forms, because each names its target differently and a check written
    #: for one could miss another. Each was measured ACCEPTED and WRITTEN at pristine HEAD.
    THREE_FORMS = (
        ("executed", "executed:zzzzzz"),
        ("exists", "exists:backlog:zzzzzz"),
        ("state", "state:spec:approved:zzzzzz"),
    )

    def test_each_edge_form_with_a_dangling_target_refuses_and_writes_nothing(self):
        for form, edge in self.THREE_FORMS:
            with self.subTest(form=form):
                before = self.fx.dep_line()
                rc, out = self.set_deps(edge)
                self.assertNotEqual(rc, 0, f"{edge} must be refused non-zero")
                self.assertIn("dangling", out.lower())
                self.assertIn(
                    "Refusing before making changes.",
                    out,
                    "the refusal must reuse the established pre-write contract wording",
                )
                self.assertEqual(
                    before,
                    self.fx.dep_line(),
                    "PRE-write means the dependency line is untouched. (Scoped to this LINE on "
                    "purpose: the setter writes a history receipt on its SUCCESS path, so an "
                    "empty-diff assertion would be testing the wrong thing.)",
                )

    def test_a_valid_target_still_succeeds(self):
        """(d) The gate must refuse a BAD target, not every target."""
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)
        self.assertEqual(self.fx.dep_line(), "- Item-Dependencies: executed:bbbbbb")

    def test_the_refusal_names_the_specific_unresolvable_target(self):
        rc, out = self.set_deps("executed:zzzzzz")
        self.assertNotEqual(rc, 0)
        self.assertIn("zzzzzz", out, "the operator must be told WHICH target failed")

    def test_one_bad_edge_refuses_the_whole_statement(self):
        """A partially-valid statement must not be half-written: the value is one field."""
        before = self.fx.dep_line()
        rc, _ = self.set_deps("executed:bbbbbb", "executed:zzzzzz")
        self.assertNotEqual(rc, 0)
        self.assertEqual(before, self.fx.dep_line())


class SetterAgreesWithCheckerTests(_VerbCase):
    """V-01's core contract: the setter and `aw check` must name the SAME condition.

    This is the whole point of resolving through the checker's own resolver. A setter that refuses an
    edge `aw check` would accept (or accepts one it would reject) is the reported defect reappearing
    one level up.
    """

    def _checker_rules(self) -> list[str]:
        return [
            d.rule
            for d in check_engine.evaluate_ipd_dependencies(self.fx.root, phase="check")
        ]

    def test_dangling_edge_the_setter_refuses_is_the_checkers_dangling_rule(self):
        rc, out = self.set_deps("executed:zzzzzz")
        self.assertNotEqual(rc, 0)
        self.assertIn("dangling", out.lower())
        # Admit the same edge through the escape hatch, then ask the CHECKER about it.
        rc2, _ = self.set_deps("executed:zzzzzz", "--allow-dangling")
        self.assertEqual(rc2, 0)
        self.assertIn(S.RULE_IPD_DEP_DANGLING, self._checker_rules())

    def test_ambiguous_edge_the_setter_refuses_is_the_checkers_ambiguous_rule(self):
        rc, out = self.set_deps("executed:dupdup")
        self.assertNotEqual(rc, 0)
        self.assertIn("ambiguous", out.lower())
        # The setter refuses it, so seed the same edge by hand to ask the checker's verdict.
        self.fx.plan.write_text(
            _plan_text("aaaaaa", order=1, deps="executed:dupdup"), encoding="utf-8"
        )
        self.assertIn(S.RULE_IPD_DEP_AMBIGUOUS, self._checker_rules())

    def test_the_setter_resolves_through_the_checkers_resolver_not_the_selector(self):
        """The single-authority requirement, asserted by CALL rather than by reading the source.

        `aw check` resolves an edge with `build_dependency_index` + `_resolve_edge`, which enforce the
        edge's TYPE and return a three-way `ok`/`dangling`/`ambiguous` verdict. `match_selector` has
        neither. Patching the checker's pair must therefore change the SETTER's answer; if it does
        not, the setter grew a second, divergable authority.
        """
        seen: list[str] = []
        real = check_engine._resolve_edge

        def spy(edge, index):
            verdict, detail = real(edge, index)
            seen.append(f"{edge.canonical()}={verdict}")
            return verdict, detail

        with patch.object(check_engine, "_resolve_edge", spy):
            self.set_deps("executed:zzzzzz")
        self.assertIn(
            "executed:zzzzzz=dangling",
            seen,
            "the setter must reach the CHECKER's edge resolver; a match_selector-based existence "
            "check would leave this spy uncalled and could disagree with `aw check`",
        )

    def test_the_typed_resolution_the_selector_could_not_do(self):
        """A plans-owned id6 does NOT satisfy a spec-typed edge; the type is part of the identity."""
        rc, out = self.set_deps("exists:spec:bbbbbb")
        self.assertNotEqual(rc, 0, "a plans id6 must not satisfy an exists:spec: edge")
        self.assertIn("dangling", out.lower())


# ======================================================================================
# E-02 / V-02: the escape hatch, scoped to `dangling` and never to `ambiguous`.
# ======================================================================================


class AllowDanglingTests(_VerbCase):
    def test_allow_dangling_proceeds_and_names_the_admitted_target(self):
        """(e) LOUD, not silent: the deferral must be visible in the transcript."""
        rc, out = self.set_deps("executed:zzzzzz", "--allow-dangling")
        self.assertEqual(rc, 0)
        self.assertIn("executed:zzzzzz", out, "the admitted target must be NAMED")
        self.assertIn("DANGLING", out.upper())
        self.assertEqual(self.fx.dep_line(), "- Item-Dependencies: executed:zzzzzz")

    def test_allow_dangling_says_the_repository_gate_still_reports_it(self):
        _rc, out = self.set_deps("executed:zzzzzz", "--allow-dangling")
        self.assertIn(S.RULE_IPD_DEP_DANGLING, out)

    def test_ambiguous_refuses_even_with_allow_dangling(self):
        """(j) An id6 owned by two artifacts does not become unambiguous by waiting."""
        for flags in ((), ("--allow-dangling",)):
            with self.subTest(allow_dangling=bool(flags)):
                before = self.fx.dep_line()
                rc, out = self.set_deps("executed:dupdup", *flags)
                self.assertNotEqual(rc, 0)
                self.assertIn("ambiguous", out.lower())
                self.assertEqual(before, self.fx.dep_line())

    def test_help_text_states_the_flag_does_not_cover_ambiguous(self):
        """An operator reading only `--help` must learn the boundary, not discover it."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with self.assertRaises(SystemExit):
                cli.main(["ipd", "dependencies", "set", "--help"])
        text = buf.getvalue()
        self.assertIn("--allow-dangling", text)
        self.assertIn("AMBIGUOUS", text)

    def test_operator_facing_help_has_no_em_or_en_dash(self):
        """Repository contract for operator-facing prose."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            for leaf in ("set", "remove"):
                with self.assertRaises(SystemExit):
                    cli.main(["ipd", "dependencies", leaf, "--help"])
        text = buf.getvalue()
        for dash in ("\u2014", "\u2013"):
            self.assertNotIn(dash, text)


# ======================================================================================
# E-03 / V-03: the remove verb.
# ======================================================================================


class RemoveVerbTests(_VerbCase):
    THREE = "executed:bbbbbb, exists:spec:ssssss, state:backlog:open:bbbklg"

    def _seed_three(self) -> None:
        rc, _ = self.set_deps(
            "executed:bbbbbb", "exists:spec:ssssss", "state:backlog:open:bbbklg"
        )
        self.assertEqual(rc, 0)
        self.assertEqual(self.fx.dep_line(), f"- Item-Dependencies: {self.THREE}")

    def test_the_verb_exists(self):
        """GAP 2's direct reproduction: at pristine HEAD this was `invalid choice: 'remove'`."""
        self.assertIn(
            "remove",
            _dependencies_subcommands(),
            "`aw ipd dependencies remove` must be a registered subcommand",
        )

    def test_removing_one_of_three_leaves_the_others_byte_identical(self):
        """(f) The point of the verb: the survivors are not re-derived, they survive."""
        self._seed_three()
        rc, _ = self.remove_deps("exists:spec:ssssss")
        self.assertEqual(rc, 0)
        self.assertEqual(
            self.fx.dep_line(),
            "- Item-Dependencies: executed:bbbbbb, state:backlog:open:bbbklg",
        )

    def test_removing_the_last_edge_writes_the_explicit_none(self):
        """(g) `none` is the grammar's ZERO. A blank value would be malformed, and `unresolved`
        would flip the plan NOT-READY as a side effect of dropping one edge."""
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)
        rc2, _ = self.remove_deps("executed:bbbbbb")
        self.assertEqual(rc2, 0)
        self.assertEqual(
            self.fx.dep_line(), f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}"
        )
        self.assertNotIn(S.ITEM_DEPENDENCIES_UNRESOLVED, self.fx.dep_line())

    def test_a_dangling_edge_is_still_removable(self):
        """(k) Removing an edge whose target was deleted is the NORMAL repair case.

        If E-01's validation leaked into `remove`, a broken edge would become unfixable, which
        inverts the whole intent of adding the verb.
        """
        rc, _ = self.set_deps("executed:zzzzzz", "--allow-dangling")
        self.assertEqual(rc, 0)
        rc2, out = self.remove_deps("executed:zzzzzz")
        self.assertEqual(rc2, 0, f"a dangling edge must stay removable: {out}")
        self.assertEqual(
            self.fx.dep_line(), f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}"
        )

    def test_edges_are_matched_canonically_not_as_raw_strings(self):
        """(l) A spelling the GRAMMAR treats as identical must match.

        Ordering and whitespace differ from the stored canonical rendering here. A raw-string
        comparison would call this a correct request ABSENT and refuse it under E-04, a false
        negative. NOTE what canonical matching does NOT mean: `state:ipd:executed:<id6>` is REFUSED
        by the grammar (it is not redirected), so it is a grammar error in `remove` exactly as it is
        in `set` - pinned in `test_state_ipd_executed_is_a_grammar_error_in_both_verbs`.
        """
        rc, _ = self.set_deps("exists:spec:ssssss", "executed:bbbbbb")
        self.assertEqual(rc, 0)
        rc2, out = self.remove_deps(" exists:spec:ssssss , executed:bbbbbb ")
        self.assertEqual(rc2, 0, out)
        self.assertEqual(
            self.fx.dep_line(), f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}"
        )

    def test_state_ipd_executed_is_a_grammar_error_in_both_verbs(self):
        """The MEASURED grammar behavior, pinned because the plan's F-14 predicted a redirect.

        `_parse_item_dependency_edge` REFUSES `state:ipd:executed:<id6>` with an explicit message
        telling the operator to use `executed:<id6>`; it does not silently rewrite it. Both verbs
        therefore refuse it identically, since both go through the one grammar authority.
        """
        self.assertIsNone(S.canonical_item_dependencies("state:ipd:executed:bbbbbb")[0])
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)
        for verb in ("set", "remove"):
            with self.subTest(verb=verb):
                before = self.fx.dep_line()
                rc2, out = self.run_cli(verb, "aaaaaa", "state:ipd:executed:bbbbbb")
                self.assertNotEqual(rc2, 0)
                self.assertIn("is illegal", out)
                self.assertIn("Refusing before making changes.", out)
                self.assertEqual(before, self.fx.dep_line())

    def test_a_sentinel_is_not_an_edge_and_removal_refuses_it(self):
        """`none`/`unresolved` are statement-level values; clearing is `set`'s job, not `remove`'s."""
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)
        for sentinel in (S.ITEM_DEPENDENCIES_NONE, S.ITEM_DEPENDENCIES_UNRESOLVED):
            with self.subTest(sentinel=sentinel):
                before = self.fx.dep_line()
                rc2, out = self.remove_deps(sentinel)
                self.assertNotEqual(rc2, 0)
                self.assertIn("Refusing before making changes.", out)
                self.assertEqual(before, self.fx.dep_line())

    def test_no_edge_argument_refuses_and_points_at_the_clearing_verb(self):
        before = self.fx.dep_line()
        rc, out = self.remove_deps()
        self.assertNotEqual(rc, 0)
        self.assertIn("none", out)
        self.assertEqual(before, self.fx.dep_line())

    def test_removal_goes_through_the_one_shared_writer(self):
        """No second write path: `remove` must reach the SAME writer `set` uses.

        Asserted by patching that writer and observing the call, rather than by reading the source,
        so a copied-and-pasted second writer fails this test.
        """
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)
        calls: list[str] = []
        real = status_set._write_item_dependencies

        def spy(*a, **kw):
            calls.append(str(a[4]))
            return real(*a, **kw)

        with patch.object(status_set, "_write_item_dependencies", spy):
            rc2, _ = self.remove_deps("executed:bbbbbb")
        self.assertEqual(rc2, 0)
        self.assertEqual(calls, [S.ITEM_DEPENDENCIES_NONE])

    def test_multi_match_selector_removes_from_each_matched_plan(self):
        """The Set-selector loop, STATED rather than inherited by accident.

        A setid legitimately matches several plans, and this verb ACCUMULATES a non-zero exit rather
        than aborting on the first plan, mirroring `set`. For a REPAIR verb that is the right
        default: aborting would make a partially-broken fleet unfixable in one call, while the
        non-zero exit still tells the operator something did not apply.
        """
        # Give TWO plans of the `fix` Set the same edge, leave the others on `none`.
        for target in ("aaaaaa", "bbbbbb"):
            rc, _ = self.run_cli("set", target, "exists:spec:ssssss")
            self.assertEqual(rc, 0)
        other = self.fx.pending / "20260908-fix-02-bbbbbb-p.ipd.md"
        self.assertEqual(
            self.fx.dep_line(other), "- Item-Dependencies: exists:spec:ssssss"
        )
        # The setid matches all five plans; three of them lack the edge, so the DEFAULT is non-zero.
        rc_default, _ = self.run_cli("remove", "fix", "exists:spec:ssssss")
        self.assertNotEqual(rc_default, 0)
        # ...and yet the two plans that DID declare it were still repaired.
        for path in (self.fx.plan, other):
            with self.subTest(plan=path.name):
                self.assertEqual(
                    self.fx.dep_line(path),
                    f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}",
                )

    def test_if_present_makes_a_multi_match_removal_exit_zero(self):
        rc, _ = self.set_deps("exists:spec:ssssss")
        self.assertEqual(rc, 0)
        rc2, _ = self.run_cli("remove", "fix", "exists:spec:ssssss", "--if-present")
        self.assertEqual(rc2, 0)


# ======================================================================================
# E-04 / V-04: absent-edge semantics.
# ======================================================================================


class AbsentEdgeSemanticsTests(_VerbCase):
    def setUp(self) -> None:
        super().setUp()
        rc, _ = self.set_deps("executed:bbbbbb")
        self.assertEqual(rc, 0)

    def test_removing_an_absent_edge_errors_and_names_it(self):
        """(h) A silent no-op on a typo'd edge would leave the operator believing they removed
        something they did not, which is the same class of failure as GAP 4 one level up."""
        before = self.fx.dep_line()
        rc, out = self.remove_deps("exists:spec:ssssss")
        self.assertNotEqual(rc, 0)
        self.assertIn("exists:spec:ssssss", out, "the absent edge must be NAMED")
        self.assertEqual(before, self.fx.dep_line())

    def test_if_present_downgrades_it_to_a_notice_and_no_change(self):
        before = self.fx.dep_line()
        rc, out = self.remove_deps("exists:spec:ssssss", "--if-present")
        self.assertEqual(rc, 0)
        self.assertIn("exists:spec:ssssss", out)
        self.assertEqual(before, self.fx.dep_line())

    def test_repeated_if_present_removal_is_idempotent(self):
        """Not a PARTIAL write: the file and the message must both be stable."""
        first = self.remove_deps("exists:spec:ssssss", "--if-present")
        after_first = self.fx.dep_line()
        second = self.remove_deps("exists:spec:ssssss", "--if-present")
        self.assertEqual(first[0], 0)
        self.assertEqual(second[0], 0)
        self.assertEqual(first[1], second[1], "the notice must be identical")
        self.assertEqual(after_first, self.fx.dep_line())

    def test_if_present_does_not_suppress_a_malformed_edge(self):
        """The flag downgrades ONE condition, not every error."""
        before = self.fx.dep_line()
        rc, out = self.remove_deps("not-an-edge", "--if-present")
        self.assertNotEqual(rc, 0)
        self.assertIn("Refusing before making changes.", out)
        self.assertEqual(before, self.fx.dep_line())

    def test_a_present_and_an_absent_edge_together_under_if_present(self):
        """The present one is removed; the absent one is noted; nothing is half-written."""
        rc, out = self.remove_deps(
            "executed:bbbbbb", "exists:spec:ssssss", "--if-present"
        )
        self.assertEqual(rc, 0)
        self.assertIn("exists:spec:ssssss", out)
        self.assertEqual(
            self.fx.dep_line(), f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}"
        )


# ======================================================================================
# E-06 / V-06: the behaviors that ALREADY worked and must not regress.
# ======================================================================================


class PreservedBehaviorTests(_VerbCase):
    def test_setid_shaped_target_is_still_refused_by_the_grammar(self):
        """(m) This ALREADY worked correctly and is easy to break by moving the new check.

        A setid-shaped target must fail on the GRAMMAR (not the new existence check), with its exact
        established message, because the new check must sit ALONGSIDE the grammar check rather than
        replacing it.
        """
        before = self.fx.dep_line()
        rc, out = self.set_deps("exists:backlog:worksequence")
        self.assertEqual(rc, 2)
        self.assertIn(
            "is not a 6-char base36 id6",
            out,
            "must fail on the grammar, not on the new existence check",
        )
        self.assertIn("Refusing before making changes.", out)
        self.assertEqual(before, self.fx.dep_line())

    def test_the_existing_clear_paths_still_work(self):
        """(n) `none` and `-` clear the statement, and they must not hit the existence check."""
        for clearer in ("none", "-"):
            with self.subTest(clearer=clearer):
                rc, _ = self.set_deps("executed:bbbbbb")
                self.assertEqual(rc, 0)
                rc2, _ = self.set_deps(clearer)
                self.assertEqual(rc2, 0)
                self.assertEqual(
                    self.fx.dep_line(),
                    f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_NONE}",
                )

    def test_the_unresolved_sentinel_is_still_writable(self):
        """The scaffold sentinel must survive: it is not an edge and has no target to resolve."""
        rc, _ = self.set_deps(S.ITEM_DEPENDENCIES_UNRESOLVED)
        self.assertEqual(rc, 0)
        self.assertEqual(
            self.fx.dep_line(),
            f"- Item-Dependencies: {S.ITEM_DEPENDENCIES_UNRESOLVED}",
        )

    def test_canonical_ordering_is_still_applied_on_set(self):
        rc, _ = self.set_deps("exists:spec:ssssss", "executed:bbbbbb")
        self.assertEqual(rc, 0)
        self.assertEqual(
            self.fx.dep_line(),
            "- Item-Dependencies: executed:bbbbbb, exists:spec:ssssss",
        )


# ======================================================================================
# E-05 / V-05: one grammar parser, one edge resolver, and a guard that can SEE this code.
# ======================================================================================


def _dependencies_subcommands() -> set[str]:
    """The registered `aw ipd dependencies` subcommand names, read from the real parser."""
    from agent_workflows.command_surface import discover_parser_leaves

    prefix = "ipd dependencies "
    return {
        leaf[len(prefix) :]
        for leaf in discover_parser_leaves(cli._build_parser())
        if leaf.startswith(prefix)
    }


class AntiDivergenceGuardTests(unittest.TestCase):
    """The guard for THIS plan's modules, which the runner-side guard provably cannot provide.

    WHY THIS EXISTS RATHER THAN AN EXTENSION OF THE EXISTING GUARD, and the choice is recorded here
    because the plan required it to be recorded (F-12, V-05). The sibling
    `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` scans `_DRIVER_SOURCES`, which
    is EXACTLY `oc_runipd.py` and `agy_runipd.py`, so it cannot see `status_set.py` or `cli.py` and
    would have passed unchanged even if this work had added a private dependency regex.

    EXTENDING `_DRIVER_SOURCES` WAS EVALUATED AND REJECTED ON MEASUREMENT, not on preference or on
    the scope fence. Three of that class's four guard bodies are DRIVER-SPECIFIC assertions, not
    general ones: `test_no_driver_defines_the_deleted_private_parser` pins the removal of
    `_DEPS_RE`/`_read_deps`, symbols that only ever existed in the two runners;
    `test_no_driver_exposes_the_deleted_names` introspects the two driver MODULES; and
    `test_drivers_reference_the_shared_dependency_api` requires `META_ITEM_DEPENDENCIES` to appear in
    the source, which is TRUE of `status_set.py` (measured) but FALSE of `cli.py`, whose dependency
    role is argument registration and dispatch and which correctly names no schema constant at all.
    Adding these two files to that tuple would therefore have forced either a false assertion about
    `cli.py` or a per-file exemption, and every message in that class says "driver", which these
    files are not. An equivalent guard here stays inside `Scope-Paths`, needs no `--scope-reason`,
    and asserts what is actually true of these two modules.
    """

    #: The same shape as the runner guard's hint: a `re.compile(...)` whose pattern text mentions a
    #: dependency field name. Bounded by a NEWLINE rather than `[^)]*` on purpose: a real pattern
    #: contains `)` (e.g. a `(?m)` flag group), so a `[^)]*` bound could not reach the field name and
    #: the guard would be vacuous.
    _DEP_REGEX_HINT = re.compile(
        r"re\.compile\([^\n]*(?:Item-Dependencies|Dependencies|Depends-on)"
    )

    #: The modules this plan touches. `status_set.py` holds both verbs; `cli.py` registers them.
    _TOUCHED_SOURCES = (
        ("status_set", REPO_ROOT / "agent_workflows" / "status_set.py"),
        ("cli", REPO_ROOT / "agent_workflows" / "cli.py"),
    )

    def _source(self, path: Path) -> str:
        """Raw source with `#` comments dropped.

        Comments are prose and may legitimately NAME a forbidden construct in order to warn against
        it. String LITERALS are kept, because a dependency regex IS a string literal and stripping
        them would make this guard unfalsifiable.
        """
        return "\n".join(
            ln
            for ln in path.read_text(encoding="utf-8").splitlines()
            if not ln.lstrip().startswith("#")
        )

    def test_neither_touched_module_defines_a_dependency_regex(self):
        for name, path in self._TOUCHED_SOURCES:
            with self.subTest(module=name):
                self.assertIsNone(
                    self._DEP_REGEX_HINT.search(self._source(path)),
                    f"{name} introduced a private dependency regex; the field NAME must come from "
                    "ipd_schema and the GRAMMAR from parse_item_dependencies",
                )

    def test_neither_touched_module_reimplements_the_edge_resolver(self):
        """The verdict vocabulary must come from the checker, not be re-derived locally."""
        for name, path in self._TOUCHED_SOURCES:
            with self.subTest(module=name):
                code = self._source(path)
                self.assertNotIn(
                    "def _resolve_edge",
                    code,
                    f"{name} must CALL check_engine._resolve_edge, never define its own",
                )
                self.assertNotIn(
                    "def build_dependency_index",
                    code,
                    f"{name} must CALL check_engine.build_dependency_index",
                )

    def test_the_setter_module_consumes_the_two_shared_authorities(self):
        code = self._source(REPO_ROOT / "agent_workflows" / "status_set.py")
        self.assertIn("build_dependency_index", code)
        self.assertIn("_resolve_edge", code)
        self.assertIn("parse_item_dependencies", code)

    def test_the_setter_does_not_resolve_edges_through_the_selector(self):
        """The measured divergence this plan's review caught (F-11).

        `match_selector` has no edge-TYPE enforcement and no `ambiguous` verdict, and the divergence
        is real rather than theoretical: an id6 can be owned by one `plans` record and two `research`
        records in this repository, so a selector-based existence check and the shared evaluator can
        reach different conclusions about the same id6. The resolver function must therefore not
        reach for the selector at all.

        Asserted against the function's CODE, with docstrings and comments stripped by the real
        tokenizer: the docstring legitimately NAMES `match_selector` in order to record why it is
        the wrong tool, and prose warning against a construct must not be indistinguishable from
        the construct.
        """
        import inspect
        import io as _io
        import token as _token
        import tokenize as _tokenize

        src = inspect.getsource(status_set.resolve_dependency_edge_targets)
        kept: list[str] = []
        for tok in _tokenize.generate_tokens(_io.StringIO(src).readline):
            if tok.type in (_token.COMMENT, _token.STRING):
                continue
            kept.append(tok.string)
        code = "\n".join(kept)
        self.assertNotIn("match_selector", code)
        self.assertIn("_resolve_edge", code)

    def test_the_shared_modules_did_not_learn_about_the_cli(self):
        """The dependency direction: the CLI consumes the checker, never the reverse."""
        text = (REPO_ROOT / "agent_workflows" / "check_engine.py").read_text(
            encoding="utf-8"
        )
        for cli_only in (
            "run_dependencies_set_command",
            "run_dependencies_remove_command",
        ):
            self.assertNotIn(
                cli_only,
                text,
                "check_engine must not learn about the setter verbs",
            )

    def test_both_dependency_subcommands_are_declared_parser_leaves(self):
        """A leaf with no `CommandDeclaration` fails the repository's own CI gate."""
        from agent_workflows.command_surface import get_declaration

        self.assertEqual(_dependencies_subcommands(), {"set", "remove"})
        for leaf in ("ipd dependencies set", "ipd dependencies remove"):
            with self.subTest(leaf=leaf):
                self.assertIsNotNone(
                    get_declaration(leaf), f"{leaf} carries no CommandDeclaration"
                )

    def test_the_two_verbs_share_one_declared_contract(self):
        from agent_workflows.command_surface import get_declaration

        setter = get_declaration("ipd dependencies set")
        remover = get_declaration("ipd dependencies remove")
        assert setter is not None and remover is not None
        self.assertEqual(setter.command_class, remover.command_class)
        self.assertEqual(setter.exit_contract, remover.exit_contract)


if __name__ == "__main__":
    unittest.main()

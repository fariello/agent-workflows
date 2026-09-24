"""Tests for setidhard Order bwgyum: the `Graduated-To` FORWARD graduation link.

Covers the multi-valued reader (`releases.parse_graduated_to`), the cross-tree reference check
(`releases.check_graduated_to` -> `check.graduated-to-dangling` / `-malformed` / `-duplicate`), the
two DATA-PRESERVATION fixes the field cannot exist without (`aw backlog set` on BOTH of its routing
paths, and `aw ipd lint` legality), and the setter on the backlog and spec surfaces.

EVERY FIXTURE IS BUILT IN A TEMP REPO, NEVER READ FROM THE LIVE TREE. The records trees are edited
concurrently by other agents and by regrouping sweeps, so a test pinned to a real item's setid would
fail for reasons unrelated to this code. The live tree is measured as EVIDENCE (see
`CurrentRepositoryTests`), which is a different claim: that the shipped corpus gains no finding.

THE MULTI-ENTRY CASE IS THE LOAD-BEARING ONE AND IT IS ASSERTED ON ITS OWN, with a comma-AND-SPACE
value. Measured against both sibling patterns before this field existed: on `- Graduated-To: first,
second` BOTH `releases._ITEM_FROM_BACKLOG_RE` and `check_engine._ITEM_FROM_SPEC_RE` match NOTHING,
because `\\S+` cannot span the space and the `$` anchor then fails. So a regex copied from either twin
does not under-validate a two-entry field, it reports it as ABSENT and the file as CLEAN. On the
NO-SPACE form `first,second` those same patterns DO match (capturing the junk token `first,second`),
so a test using only that form would pass against the broken implementation. Hence
`SiblingPatternRegressionTests`, which pins the measurement itself rather than trusting this prose.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import check_engine as ce
from agent_workflows import cli, ipd_schema, releases

_PLAN = """# IPD: x

- Date: 2026-01-01
- Kind: child
- Status: draft
- Set: {setid}
- Order: 1
- Id: {id6}

## Workflow history
- 2026-01-01 draft (t): x

## Goal
x
"""

_ITEM = """- Id: {id6}
- Status: {status}
- Set: {setid}
- Priority: high
- Work-Kind: chore
- Summary: a fixture item
{extra}
## Workflow history
- 2026-01-01 created (t): x
"""


def _write_plan(root: Path, setid: str, id6: str) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260101-{setid}-01-{id6}-x.ipd.md"
    p.write_text(_PLAN.format(setid=setid, id6=id6), encoding="utf-8")
    return p


def _write_item(
    root: Path,
    id6: str,
    *,
    setid: str = "demo",
    status: str = "open",
    graduated_to: str | None = None,
) -> Path:
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    extra = f"- Graduated-To: {graduated_to}\n" if graduated_to is not None else ""
    p = d / f"20260101-{setid}-01-{id6}-x.backlog.md"
    p.write_text(
        _ITEM.format(id6=id6, status=status, setid=setid, extra=extra), encoding="utf-8"
    )
    return p


class ParseGraduatedToTests(unittest.TestCase):
    """E-01/V-01: the reader is list-aware, ordered, and has the empty + duplicate cases DECIDED.

    ONE table, because every row is the same shape: one field value in, one parsed list out. The
    interesting property is that the SAME reader gives a different answer per value, which no
    single-value test can state.
    """

    #: (case, the raw `- Graduated-To:` value or None for no line at all, expected list, why)
    VALUES = (
        ("absent", None, [], "the ordinary case: no claim, nothing to resolve"),
        (
            "one entry",
            "onesetid",
            ["onesetid"],
            "the single-valued case a copied regex would also get right, so it proves nothing on "
            "its own and is here only to keep the multi-entry rows from being vacuous",
        ),
        (
            "two entries, comma AND space",
            "first, second",
            ["first", "second"],
            "THE LOAD-BEARING ROW. Both sibling single-token patterns match NOTHING on this exact "
            "form, so a copied regex reports a well-formed two-entry field as ABSENT and the file "
            "as clean. See SiblingPatternRegressionTests, which pins that measurement",
        ),
        (
            "two entries, no space",
            "first,second",
            ["first", "second"],
            "the form on which a copied regex DOES match, capturing the junk token "
            "'first,second'; asserted so both spellings parse identically",
        ),
        (
            "three entries with ragged whitespace",
            "  a ,b,   c  ",
            ["a", "b", "c"],
            "authors type ragged lists; whitespace must never reach the resolver as part of a token",
        ),
        (
            "order is preserved, not sorted",
            "zzz, aaa, mmm",
            ["zzz", "aaa", "mmm"],
            "the list is a HISTORY (what this source became, in the order it became it), so "
            "re-sorting it would destroy the reading. A sorted implementation passes every other "
            "row here",
        ),
        (
            "an EMPTY field is treated as ABSENT",
            "",
            [],
            "DECIDED in E-01: an empty value asserts nothing, so it resolves to nothing and reports "
            "nothing, exactly as a missing line does",
        ),
        (
            "a whitespace-only field is treated as ABSENT",
            "   ",
            [],
            "the same decision, reached by the other way an author empties a field",
        ),
        (
            "a commas-only field is treated as ABSENT",
            ",,",
            [],
            "the same decision again: splitting yields no nonempty token, so there is nothing to "
            "resolve. Without this an implementation could emit [''] and report a confusing "
            "dangling finding for the empty string",
        ),
        (
            "a DUPLICATE entry is RETURNED, not silently deduped",
            "same, same",
            ["same", "same"],
            "DECIDED in E-01: deduping here would hide an author error while leaving the record "
            "saying something it does not mean. The reader surfaces it; `check_graduated_to` "
            "reports it as check.graduated-to-repeated",
        ),
    )

    def test_every_value_parses_as_decided(self) -> None:
        wrong = []
        for case, value, expected, why in self.VALUES:
            line = "" if value is None else f"- Graduated-To: {value}\n"
            text = f"- Id: aaa111\n- Status: open\n{line}\n## Workflow history\n- x\n"
            got = releases.parse_graduated_to(text)
            if got != expected:
                wrong.append(f"  {case}: expected {expected!r}, got {got!r} ({why})")
        self.assertEqual(
            wrong,
            [],
            "the Graduated-To reader answered wrongly for:\n" + "\n".join(wrong),
        )

    def test_the_multi_entry_case_alone_with_a_comma_and_a_space(self) -> None:
        """Kept SEPARATE and duplicated from the table on purpose (plan E-05/V-05).

        This is the one assertion that fails against a regex copied from either sibling link field,
        and it only fails if the fixture value carries a comma AND A SPACE. A table row can be lost
        in a refactor or its value quietly edited to the no-space form, which still passes against a
        broken implementation, so the claim is restated here where the value is visible on one line.
        """
        text = "- Id: aaa111\n- Status: open\n- Graduated-To: first, second\n\n## X\n"
        self.assertEqual(releases.parse_graduated_to(text), ["first", "second"])


class SiblingPatternRegressionTests(unittest.TestCase):
    """Kept separate: the subject is the TWO SIBLING PATTERNS, not this feature's own code.

    This pins the MEASUREMENT that justifies writing a list parser at all, so the justification
    survives as an executable fact rather than a comment a later reader must take on trust. If a
    future change made either sibling pattern list-aware, this test fails and the next reader learns
    that copying it is now safe, instead of inheriting a warning that has silently gone stale.
    """

    def test_both_single_token_patterns_match_nothing_on_a_spaced_list(self) -> None:
        import re

        line = "- Graduated-To: first, second"
        for name, pattern in (
            ("releases._ITEM_FROM_BACKLOG_RE", releases._ITEM_FROM_BACKLOG_RE.pattern),
            ("check_engine._ITEM_FROM_SPEC_RE", ce._ITEM_FROM_SPEC_RE.pattern),
        ):
            shaped = re.compile(
                pattern.replace("From-Backlog", "Graduated-To").replace(
                    "From-Spec", "Graduated-To"
                )
            )
            self.assertIsNone(
                shaped.search(line),
                f"{name} unexpectedly matched a comma-and-space list; if this pattern became "
                "list-aware, the warning in this module's docstring is stale and should be updated "
                "rather than the assertion relaxed",
            )
        # And on the NO-SPACE form it DOES match, capturing a junk token. This is why a test using
        # only that form would pass against a copied-regex implementation.
        shaped = re.compile(
            releases._ITEM_FROM_BACKLOG_RE.pattern.replace(
                "From-Backlog", "Graduated-To"
            )
        )
        m = shaped.search("- Graduated-To: first,second")
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group(1), "first,second")


class CheckGraduatedToTests(unittest.TestCase):
    """E-03/V-03: the dangling check, as a (tree -> exact rule list) table.

    THE EMPTY-CORPUS ROW IS THE MOST IMPORTANT ONE and is what separates this rule from its
    false-positive-prone `From-Backlog` twin: with no discoverable plan Set at all, a dangling link
    and an invisible plan corpus are indistinguishable, so an `error`-severity rule that can block a
    commit must report NOTHING. Measured before this rule existed, on a tree carrying a plan with
    both links and neither source tree: `check_from_spec_dangling` reported 0 and
    `check_from_backlog` reported 1 FALSE finding. This copies the spec side.

    THE SILENT ROWS SHARE THE TABLE WITH THE FIRING ONES because they fail in opposite directions: a
    rule that reports nothing and a rule that reports every entry would each pass a table holding
    only the other kind.
    """

    #: (case, plan Sets to create, the field value on the source item, exact expected rule list,
    #: a substring the detail must contain or None, why this row exists)
    TREES = (
        (
            "a single entry naming a real plan Set",
            ["realset"],
            "realset",
            [],
            None,
            "THE POSITIVE ROW and the ordinary case. Every firing row below is vacuous while this "
            "one is broken, because a rule that flags every entry satisfies them all",
        ),
        (
            "EVERY entry of a multi-entry field resolves",
            ["alpha", "beta", "gamma"],
            "alpha, beta, gamma",
            [],
            None,
            "the case a single-token regex fails: it would see the field as absent (or capture a "
            "junk token) and report clean for the wrong reason, which this row cannot distinguish "
            "on its own - hence the malformed row below, which a junk token WOULD trip",
        ),
        (
            "one bad entry among three good ones names WHICH entry",
            ["alpha", "beta", "gamma"],
            "alpha, nosuchset, gamma",
            ["check.graduated-to-dangling"],
            "nosuchset",
            "a finding that says only 'a link is broken' leaves a maintainer grepping; with three "
            "resolving entries beside it, naming the entry is the whole value of the finding",
        ),
        (
            "no field at all",
            ["realset"],
            None,
            [],
            None,
            "the silent case; a rule that flags a source carrying no claim would be unusable",
        ),
        (
            "an EMPTY field",
            ["realset"],
            "",
            [],
            None,
            "E-01 decided an empty field is ABSENT, so the check must agree with the reader. An "
            "implementation emitting [''] would report a dangling finding for the empty string",
        ),
        (
            "a DUPLICATE entry is reported as its own rule",
            ["realset"],
            "realset, realset",
            ["check.graduated-to-repeated"],
            "realset",
            "the reader deliberately does not dedupe, so the check is what makes the author error "
            "visible. It is NOT reported as dangling: every entry resolves, so the handoff is "
            "intact and the defect is redundancy",
        ),
        (
            "a MALFORMED token is reported as malformed, NOT as dangling",
            ["realset"],
            "Not_A_Setid",
            ["check.graduated-to-malformed"],
            "Not_A_Setid",
            "'does not resolve to a real Set' would send a reader hunting for a missing Set when "
            "the real defect is a typo in the token. This row also catches a junk token captured "
            "by a copied single-value regex, e.g. 'first,second'",
        ),
        (
            "a setid that is well-formed but names no Set",
            ["realset"],
            "ghostset",
            ["check.graduated-to-dangling"],
            "ghostset",
            "the rule itself: a forward link pointing at nothing is a broken graduation claim, in "
            "the same way its From-Backlog twin's dangling id6 is",
        ),
        (
            "a Set whose only plan is RETIRED still resolves",
            ["retiredset:not-executed"],
            "retiredset",
            [],
            None,
            "OQ-01: resolution spans EVERY lifecycle directory, including terminal ones. The "
            "alternative fires on exactly the successful case, because a graduated source's Set "
            "eventually becomes entirely executed",
        ),
    )

    def _build(self, sets: list[str], value: str | None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for i, spec in enumerate(sets):
            if ":" in spec:
                setid, disposition = spec.split(":", 1)
                d = root / ".aw" / "records" / "plans" / disposition
                d.mkdir(parents=True, exist_ok=True)
                (d / f"20260101-{setid}-01-pl{i:04d}-x.ipd.md").write_text(
                    _PLAN.format(setid=setid, id6=f"pl{i:04d}"), encoding="utf-8"
                )
            else:
                _write_plan(root, spec, f"pl{i:04d}")
        _write_item(root, "aaa111", graduated_to=value)
        return root

    def test_every_tree_reports_exactly_its_own_rules(self) -> None:
        wrong = []
        for case, sets, value, expected, detail_needle, why in self.TREES:
            root = self._build(list(sets), value)
            drift = releases.check_graduated_to(root)
            rules = sorted(d.rule for d in drift)
            if rules != sorted(expected):
                wrong.append(
                    f"  {case}: expected {sorted(expected)}, got {rules} ({why})"
                )
                continue
            if detail_needle is not None and not any(
                detail_needle in d.detail for d in drift
            ):
                wrong.append(
                    f"  {case}: no finding named {detail_needle!r}; details="
                    f"{[d.detail for d in drift]} ({why})"
                )
        self.assertEqual(
            wrong,
            [],
            "check_graduated_to answered wrongly for:\n" + "\n".join(wrong),
        )

    def test_an_empty_plan_set_corpus_reports_nothing(self) -> None:
        """Kept SEPARATE: this is the FAIL-SAFE, and it is the assertion that distinguishes this
        rule from its `From-Backlog` twin, which measurably produced a false finding in exactly this
        situation. It is not a row because the tree it needs has NO plans tree at all, which the
        table's builder always creates.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_item(root, "aaa111", graduated_to="whatever, else")
        self.assertEqual(
            releases.check_graduated_to(root),
            [],
            "with no discoverable plan Set, a dangling link and an invisible plan corpus are "
            "indistinguishable, so this error-severity rule must report NOTHING",
        )

    def test_the_field_is_tolerated_on_a_plan_and_on_a_spec_too(self) -> None:
        """Kept separate: the subject is the TRAVERSAL's reach, not one verdict.

        The scan covers plans/specs/backlog for the same symmetry reason `check_from_backlog` does:
        the field's primary home is the SOURCE, but tolerating it anywhere keeps one rule instead of
        three. A scan that only read backlog items would pass every row of the table above.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_plan(root, "realset", "pl0001")
        specs = root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "20260101-sp0001-01-sp0001-x.spec.md").write_text(
            "# Spec\n\n- Id: sp0001\n- Status: draft\n- Graduated-To: ghostset\n\n## X\n",
            encoding="utf-8",
        )
        plan_carrier = _write_plan(root, "realset", "pl0002")
        plan_carrier.write_text(
            plan_carrier.read_text(encoding="utf-8").replace(
                "- Id: pl0002", "- Id: pl0002\n- Graduated-To: ghostset"
            ),
            encoding="utf-8",
        )
        locations = {
            Path(d.location).name
            for d in releases.check_graduated_to(root)
            if d.rule == "check.graduated-to-dangling"
        }
        self.assertIn("20260101-sp0001-01-sp0001-x.spec.md", locations)
        self.assertIn("20260101-realset-01-pl0002-x.ipd.md", locations)

    def test_resolution_is_plans_only_and_not_confused_by_a_shared_setid(self) -> None:
        """Kept separate: the subject is spec `2lcqno` N3, type-scoped resolution.

        A setid is a SHARED cross-type TOPIC label, so a backlog item and a plan Set legitimately
        carry the same token; that is the EXPECTED case, not a collision. An all-types search would
        make a link trivially self-resolving against the SOURCE's own setid, so this asserts that a
        setid carried only by a backlog item does NOT satisfy the link.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_plan(root, "realset", "pl0001")
        # `topic` names the SOURCE item's own Set, and no plan Set at all.
        _write_item(root, "aaa111", setid="topic", graduated_to="topic")
        rules = [d.rule for d in releases.check_graduated_to(root)]
        self.assertEqual(rules, ["check.graduated-to-dangling"])


class RuleRegistrationTests(unittest.TestCase):
    """Kept separate: the claim is about the RULE REGISTRY, not about any tree.

    An UNREGISTERED rule id silently falls back to the default `RuleSpec` with an EMPTY invariant, so
    registration is a behavioural contract rather than bookkeeping: severity decides whether
    `aw check` exits nonzero, and the invariant is what appears in the trace. Compared against the
    `From-Backlog` twin rather than to literals, so the two directions of ONE graduation link cannot
    drift apart in severity.
    """

    def test_dangling_and_malformed_match_the_backlog_twin(self) -> None:
        twin = ce.rule_spec("check.from-backlog-dangling")
        for rule in ("check.graduated-to-dangling", "check.graduated-to-malformed"):
            spec = ce.rule_spec(rule)
            self.assertEqual(spec.severity, "error", rule)
            self.assertEqual(spec.severity, twin.severity, rule)
            self.assertEqual(spec.invariant, twin.invariant, rule)
            self.assertEqual(spec.invariant, "I-07", rule)

    def test_repeated_is_a_warning_deliberately(self) -> None:
        spec = ce.rule_spec("check.graduated-to-repeated")
        self.assertEqual(
            spec.severity,
            "warning",
            "a duplicate entry is redundant rather than broken (every entry still resolves, so the "
            "handoff is intact), so it must be visible without blocking a commit",
        )
        self.assertEqual(spec.invariant, "I-07")

    def test_the_repeated_rule_id_avoids_the_sibling_prohibition(self) -> None:
        """Kept separate: the subject is a SHIPPED GUARD IN ANOTHER FILE, not this rule's behavior.

        The `graduate` Set's read-only view asserts structurally that no rule id containing
        `graduation` or `duplicate` is registered, because a rule counting the artifacts per source
        would flag legitimate decomposition. That guard's keyword match is broader than its subject,
        so this rule is named `-repeated`. Asserted here so a later rename back to `-duplicate` fails
        HERE, next to the reason, rather than surfacing as a puzzling failure in an unrelated file.
        """
        offenders = [
            r for r in ce.RULE_REGISTRY if "graduation" in r or "duplicate" in r
        ]
        self.assertEqual(offenders, [])


class SchemaRecognitionTests(unittest.TestCase):
    """E-02/V-02: a PLAN carrying the field lints CLEAN (no IPD-M103).

    Required by this plan's own design, not by taste: the check above scans PLANS (mirroring the
    twin's symmetry rule), so without schema recognition the rule would flag a field the linter
    forbids anyone from writing there. Measured before the fix: `IPD-M103`, exit 1.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        plans = self.root / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        from tests.support import CONFORMING_ORCHESTRATOR

        self.plan = plans / "20260803-fixture-00-fix000-sample-fixture.ipd.md"
        base = CONFORMING_ORCHESTRATOR.read_text(encoding="utf-8")
        self.plan.write_text(
            releases.set_graduated_to_line(base, "onesetid, twosetid"), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_field_is_recognized_but_optional(self) -> None:
        self.assertIn("Graduated-To", ipd_schema.META_RECOGNIZED)
        self.assertNotIn("Graduated-To", ipd_schema.META_REQUIRED)

    def test_a_plan_carrying_the_field_lints_clean(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["ipd", "lint", "--agent", str(self.plan)])
        out = buf.getvalue()
        self.assertEqual(rc, 0, f"plan with Graduated-To must lint clean: {out}")
        self.assertNotIn("IPD-M103", out)
        self.assertIn(
            "- Graduated-To: onesetid, twosetid", self.plan.read_text(encoding="utf-8")
        )


class WritePrimitiveTests(unittest.TestCase):
    """`set_graduated_to_line` sets, overwrites and clears idempotently, like its siblings."""

    def test_set_overwrite_clear_round_trip(self) -> None:
        text = "# X\n\n- Id: aaa111\n- Status: open\n\n## Goal\n\nx\n"
        with_field = releases.set_graduated_to_line(text, "one, two")
        self.assertIn("- Status: open\n- Graduated-To: one, two", with_field)
        over = releases.set_graduated_to_line(with_field, "three")
        self.assertIn("- Graduated-To: three", over)
        self.assertEqual(over.count("Graduated-To"), 1)
        self.assertNotIn("Graduated-To", releases.set_graduated_to_line(over, "-"))
        self.assertNotIn("Graduated-To", releases.set_graduated_to_line(over, None))
        self.assertIn("- Status: open", releases.set_graduated_to_line(over, "-"))

    def test_canonicalization_refuses_a_malformed_token(self) -> None:
        good, err = releases.canonicalize_graduated_to("  a ,b ")
        self.assertEqual(good, "a, b")
        self.assertIsNone(err)
        cleared, err = releases.canonicalize_graduated_to("-")
        self.assertEqual(cleared, "-")
        self.assertIsNone(err)
        bad, err = releases.canonicalize_graduated_to("Not_A_Setid")
        self.assertIsNone(bad)
        assert err is not None
        self.assertIn("Not_A_Setid", err)


class BacklogSetterPreservationTests(unittest.TestCase):
    """E-02/E-04, V-02/V-04: the field survives `aw backlog set` on BOTH of its routing paths.

    THE TWO PATHS ARE THE WHOLE POINT. `aw backlog set` forks on whether `--status` was PASSED: the
    bare `<status> <selector>` spelling routes to `status_set.run_set_command` (a surgical line
    rewrite, which always preserved the field), and the `--status <s> <path>` spelling routes to
    `backlog.run_set`, which rebuilds the bullet block from a FIXED template and therefore SILENTLY
    DELETED it (measured end to end: exit 0, no warning, line gone). A fix proven on one path says
    nothing about the other, so both are pinned here.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write_plan(self.root, "realset", "pl0001")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _item_text(self) -> str:
        found = list((self.root / ".aw" / "records" / "backlog").rglob("*.backlog.md"))
        self.assertEqual(len(found), 1, f"expected exactly one item, got {found}")
        return found[0].read_text(encoding="utf-8")

    def _item_path(self) -> Path:
        return next((self.root / ".aw" / "records" / "backlog").rglob("*.backlog.md"))

    def test_the_status_flag_path_preserves_an_existing_field(self) -> None:
        _write_item(self.root, "aaa111", graduated_to="realset")
        rc = cli.main(
            [
                "backlog",
                "set",
                "--status",
                "graduated",
                str(self._item_path()),
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(releases.parse_graduated_to(self._item_text()), ["realset"])

    def test_the_bare_path_preserves_an_existing_field(self) -> None:
        _write_item(self.root, "aaa111", graduated_to="realset")
        rc = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "aaa111",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "x",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(releases.parse_graduated_to(self._item_text()), ["realset"])

    def test_the_bare_path_writes_a_multi_entry_value_and_clears_it(self) -> None:
        _write_item(self.root, "aaa111")
        rc = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "aaa111",
                "--graduated-to",
                "realset, demo",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "graduated",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(
            releases.parse_graduated_to(self._item_text()), ["realset", "demo"]
        )
        rc = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "aaa111",
                "--graduated-to",
                "-",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "cleared",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(releases.parse_graduated_to(self._item_text()), [])

    def test_the_status_flag_path_writes_the_field_too(self) -> None:
        _write_item(self.root, "aaa111")
        rc = cli.main(
            [
                "backlog",
                "set",
                "--status",
                "graduated",
                str(self._item_path()),
                "--graduated-to",
                "realset",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(releases.parse_graduated_to(self._item_text()), ["realset"])

    def test_both_paths_refuse_a_malformed_setid_with_exit_2(self) -> None:
        _write_item(self.root, "aaa111")
        before = self._item_text()
        rc_bare = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "aaa111",
                "--graduated-to",
                "Not_A_Setid",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc_bare, 2)
        rc_flag = cli.main(
            [
                "backlog",
                "set",
                "--status",
                "graduated",
                str(self._item_path()),
                "--graduated-to",
                "Not_A_Setid",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc_flag, 2)
        self.assertEqual(
            self._item_text(), before, "a refused setter must not write anything"
        )

    def test_the_flag_is_OPTIONAL(self) -> None:
        """A graduation performed WITHOUT the flag still succeeds and produces no finding.

        OQ-02: four agents graduate items concurrently, so a required flag would fail every one of
        their calls the moment it landed, for a field nothing yet consumes.
        """
        _write_item(self.root, "aaa111")
        rc = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "aaa111",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "no forward link",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(releases.parse_graduated_to(self._item_text()), [])
        self.assertEqual(releases.check_graduated_to(self.root), [])


class SpecSetterTests(unittest.TestCase):
    """V-04's spec half, which is REQUIRED rather than optional.

    `aw specs set` has the same two spellings as `aw backlog set`: the bare form shares
    `status_set.run_set_command` with every other setter (so one write serves it), and the
    `--status` form routes to the FORKED `specs.run_set`. Both are pinned, because a field writable
    by one spelling of one verb and not the other teaches a false expectation.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write_plan(self.root, "realset", "pl0001")
        specs = self.root / ".aw" / "records" / "specs" / "draft"
        specs.mkdir(parents=True)
        self.spec = specs / "20260101-sp0001-01-sp0001-demo.spec.md"
        self.spec.write_text(
            "# Spec: demo\n\n- Id: sp0001\n- Status: draft\n\n"
            "## Workflow history\n- 2026-01-01 draft (t): x\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_bare_form_writes_the_field(self) -> None:
        rc = cli.main(
            [
                "specs",
                "set",
                "to-review",
                "sp0001",
                "--graduated-to",
                "realset",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "graduated",
            ]
        )
        self.assertEqual(rc, 0)
        target = self.root / ".aw" / "records" / "specs" / "to-review" / self.spec.name
        self.assertEqual(
            releases.parse_graduated_to(target.read_text(encoding="utf-8")),
            ["realset"],
        )

    def test_the_status_form_writes_the_field_and_refuses_a_typo(self) -> None:
        rc = cli.main(
            [
                "specs",
                "set",
                "--status",
                "to-review",
                str(self.spec),
                "--graduated-to",
                "realset, demo",
                "--yes",
                "--dir",
                str(self.root),
                "--message",
                "both",
            ]
        )
        self.assertEqual(rc, 0)
        target = self.root / ".aw" / "records" / "specs" / "to-review" / self.spec.name
        self.assertEqual(
            releases.parse_graduated_to(target.read_text(encoding="utf-8")),
            ["realset", "demo"],
        )
        before = target.read_text(encoding="utf-8")
        rc_bad = cli.main(
            [
                "specs",
                "set",
                "--status",
                "to-review",
                str(target),
                "--graduated-to",
                "BAD Setid",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc_bad, 2)
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            before,
            "a refused setter must leave the spec byte-identical",
        )


class CurrentRepositoryTests(unittest.TestCase):
    """Kept separate: the subject is the REAL checkout, not a fixture.

    Every fixture above builds a tree designed to produce a chosen answer; this asserts the shipped
    corpus gains no finding from the new rules, which is the only guard against a rule that is
    correct on fixtures and noisy on the real tree. It is also the assertion that would catch a
    traversal bug counting PROSE mentions of the field (which are numerous) as authored bullets.
    """

    def test_the_new_rules_report_nothing_on_this_repository(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(releases.check_graduated_to(repo), [])

    def test_the_from_backlog_twin_is_not_perturbed(self) -> None:
        """The twin shares this module, this traversal and the same sweep seam, so its count is the
        control: a change here means the new code perturbed the existing scan. Asserted as a SET of
        rule ids rather than a count, so a legitimate corpus edit by another agent does not fail this
        test for an unrelated reason.
        """
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(
            {d.rule for d in releases.check_from_backlog(repo)}
            - {"check.from-backlog-dangling"},
            set(),
            "check_from_backlog must emit only its own rule id",
        )


if __name__ == "__main__":
    unittest.main()

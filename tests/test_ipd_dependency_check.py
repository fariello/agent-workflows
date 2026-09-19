"""Tests for ipddeps Order ovbnyq: the shared cross-IPD dependency evaluator + check.ipd-dependency-*
rule family across `aw check` and phased `aw ipd lint`, plus grandfathering cutover.

Covers:
* V-01 - the pure evaluator emits each of the six findings on exactly its own fixture:
  missing / unresolved / malformed / dangling / ambiguous / cycle; clean otherwise.
* V-02 - BOTH `aw check plans` AND `aw check all` surface a dangling and a cyclic finding with the
  same rule IDs; a clean tree passes both; no double-report in the `all` sweep.
* V-03 - the phase matrix: author = advisory for missing/unresolved (blocking for malformed);
  review-finalize/pre-execution/pre-transition = blocking for missing/unresolved/malformed, and the
  repo-resolving dangling/cyclic checks block at those phases (author does not resolve).
* V-04 - grandfathering: with NO cutover marker the current corpus does not mass-fail; with a
  cutover marker a post-cutover missing-field IPD errors while a pre-cutover plan is grandfathered;
  no tool auto-inserts `none` (scaffold emits `unresolved`).

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a plans tree (or
a parsed document) with one dependency statement in it, call one function, assert one rule id. That
is a (fixture -> rule id) table, which is the natural shape for a RULE FAMILY.

THE RULE IDS ARE LOAD-BEARING AND ARE ASSERTED EXACTLY, never as "a finding appeared". Users read
them in `aw check` and `aw ipd lint` output, CI greps them, and `aw attention` routes on them, so a
renumbering or a rule splitting in two is a BREAKING CHANGE that must fail here. The tables added
after the first round therefore spell the ids as LITERAL STRINGS rather than reading `S.RULE_*`,
because a constant and the reported id move together and a rename would leave a constant-referencing
table GREEN (measured on `test_ipd_lint.py`, whose table carries the same warning).
`EvaluatorRuleMatrixTests` predates that finding and still references the constants; it is left
BYTE-UNCHANGED deliberately rather than churned.

WHAT WAS A CLASS PER MODE IS NOW A COLUMN: the lint PHASE (`author` versus the three blocking
checkpoints), the cutover MARKER and the plan's DATE relative to it, the ENTRY POINT (`aw check
plans` versus the `all` sweep versus the bare check function), and the CARRIER (a plan versus a spec)
are all columns, because in every case the property worth asserting is that the SAME document gets a
DIFFERENT answer in a different mode, which no single-mode test can state.

ROWS PIN THE DEPENDENCY RULE FAMILY, NOT AN EMPTY DIAGNOSTIC LIST, wherever the fixture is a minimal
plan that legitimately trips unrelated structural rules (a three-line IPD is missing most required H2
and metadata, and a `draft` plan trips the advisory `check.ipd-draft-ready-to-review`). Asserting
emptiness there would couple every row to every unrelated rule in the linter.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the subject is the REAL repository rather than a fixture; the claim is about the RULE
REGISTRY rather than about any tree; or the assertion is over module SOURCE text.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_depchk_"))
    (d / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    return d


def _set_cutover(repo: Path, date: str | None) -> None:
    import json

    pj = repo / ".aw" / "config" / "project.json"
    if date is None:
        if pj.exists():
            pj.unlink()
        return
    pj.write_text(
        json.dumps({"dependency_schema_cutover": {"date": date}}), encoding="utf-8"
    )


def _plan(
    repo: Path,
    *,
    id6: str,
    order: int,
    item_deps: str | None,
    date: str = "2026-08-27",
    setid: str = "demo",
) -> Path:
    pend = repo / ".aw" / "records" / "plans" / "pending"
    dep_line = f"- Item-Dependencies: {item_deps}\n" if item_deps is not None else ""
    p = pend / f"{date.replace('-', '')}-{setid}-{order:02d}-{id6}-p.ipd.md"
    p.write_text(
        f"# IPD: {id6}\n\n"
        f"- Date: {date}\n- Kind: child\n- Scope-Paths: x.py\n"
        f"{dep_line}"
        f"- Status: draft\n- Set: {setid}\n- Order: {order}\n- Id: {id6}\n\n"
        f"## Workflow history\n- {date} draft (t): x\n\n## Goal\ng\n",
        encoding="utf-8",
    )
    return p


def _spec(repo: Path, *, id6: str, status: str = "draft") -> Path:
    d = repo / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260101-1200-01-{id6}-s.spec.md"
    p.write_text(
        f"# Spec {id6}\n\n- Id: {id6}\n- Status: {status}\n\n## Summary\ns\n",
        encoding="utf-8",
    )
    return p


def _rules(drift, prefix="check.ipd-") -> list:
    # This helper targets the cross-IPD DEPENDENCY rules. The agentadhere Phase 1 (IPD uisjns)
    # advisory `check.ipd-draft-ready-to-review` shares the `check.ipd-` prefix but is a separate
    # (draft-readiness) concern, so it is excluded here to keep these dependency assertions focused.
    return [
        d.rule
        for d in drift
        if d.rule.startswith(prefix) and d.rule != "check.ipd-draft-ready-to-review"
    ]


# --------------------------------------------------------------------------------------
# V-01: the pure evaluator, one finding per crafted fixture
# --------------------------------------------------------------------------------------


class EvaluatorRuleMatrixTests(unittest.TestCase):
    """V-01: the pure evaluator emits the right rule for each dependency-statement shape.

    ONE table-driven test replaces eleven near-identical ones. Each old test built a fixture and
    made a single assertion, so the eleven differed only in their DATA; expressing that data as
    rows makes the truth table readable as a table and, more importantly, reports EVERY wrong row
    in one run. The old shape stopped at the first failure, so a change that broke the resolver for
    several shapes at once took several fix-and-rerun cycles to fully diagnose.

    Each row is `(case, plans, spec_id6s, phase, expect_rule)` where `expect_rule=None` means the
    fixture must be CLEAN. Asserting cleanliness and a specific rule in the same table is
    deliberate: a resolver bug that makes everything clean, and one that makes everything fire, are
    opposite failures and a table containing both kinds cannot pass under either.
    """

    #: (case name, [(id6, order, item_deps)], [spec id6], phase, expected rule or None for clean)
    CASES = (
        ("clean 'none' statement", [("aaaaaa", 1, "none")], [], "check", None),
        (
            "no statement at all",
            [("aaaaaa", 1, None)],
            [],
            "check",
            S.RULE_IPD_DEP_MISSING,
        ),
        (
            "the 'unresolved' sentinel at a blocking phase",
            [("aaaaaa", 1, "unresolved")],
            [],
            "pre-execution",
            S.RULE_IPD_DEP_UNRESOLVED,
        ),
        (
            "duplicate edge (the parser catches this before the self-edge)",
            [("aaaaaa", 1, "executed:aaaaaa, executed:aaaaaa")],
            [],
            "check",
            S.RULE_IPD_DEP_MALFORMED,
        ),
        (
            "self dependency",
            [("aaaaaa", 1, "executed:aaaaaa")],
            [],
            "check",
            S.RULE_IPD_DEP_MALFORMED,
        ),
        (
            "edge to an id6 nothing owns",
            [("aaaaaa", 1, "executed:zzzzzz")],
            [],
            "check",
            S.RULE_IPD_DEP_DANGLING,
        ),
        (
            "edge to an id6 TWO plans claim",
            [
                ("dupdup", 1, "none"),
                ("dupdup", 2, "none"),
                ("aaaaaa", 3, "executed:dupdup"),
            ],
            [],
            "check",
            S.RULE_IPD_DEP_AMBIGUOUS,
        ),
        (
            "two-node cycle",
            [("aaaaaa", 1, "executed:bbbbbb"), ("bbbbbb", 2, "executed:aaaaaa")],
            [],
            "check",
            S.RULE_IPD_DEP_CYCLE,
        ),
        (
            "three-node cycle",
            [
                ("aaaaaa", 1, "executed:bbbbbb"),
                ("bbbbbb", 2, "executed:cccccc"),
                ("cccccc", 3, "executed:aaaaaa"),
            ],
            [],
            "check",
            S.RULE_IPD_DEP_CYCLE,
        ),
        (
            "cross-type edge resolves against the SPECS tree",
            [("aaaaaa", 1, "exists:spec:spec01")],
            ["spec01"],
            "check",
            None,
        ),
        (
            "spec edge where only a PLAN owns that id6 (type is part of the key)",
            [("plnpln", 1, "none"), ("aaaaaa", 2, "exists:spec:plnpln")],
            [],
            "check",
            S.RULE_IPD_DEP_DANGLING,
        ),
    )

    def test_every_dependency_shape_produces_its_own_rule(self):
        failures = []
        for case, plans, specs, phase, expected in self.CASES:
            repo = _mkrepo()
            # Cutover set in the past, so a missing statement is an error rather than grandfathered.
            _set_cutover(repo, "2020-01-01")
            for id6 in specs:
                _spec(repo, id6=id6)
            for id6, order, item_deps in plans:
                _plan(repo, id6=id6, order=order, item_deps=item_deps)
            got = _rules(ce.evaluate_ipd_dependencies(repo, phase=phase))
            if expected is None:
                if got:
                    failures.append(
                        f"  {case!r} (phase {phase}): expected NO finding, got {got}"
                    )
            elif expected not in got:
                failures.append(
                    f"  {case!r} (phase {phase}): expected {expected!r}, got {got or 'no findings'}"
                )
        self.assertEqual(
            failures,
            [],
            "check_engine.evaluate_ipd_dependencies returned the wrong rule for "
            f"{len(failures)} of {len(self.CASES)} dependency-statement shapes:\n"
            + "\n".join(failures)
            + "\n  Each row is an independent fixture, so several failing rows usually means the "
            "resolver or the rule ids changed, not that each shape broke separately.",
        )


# --------------------------------------------------------------------------------------
# V-01b: the pure cycle helper
# --------------------------------------------------------------------------------------


class CycleHelperTests(unittest.TestCase):
    """V-01b: `S.item_dependency_cycles` over a hand-built graph, at every cycle LENGTH.

    ONE table replaces four tests: three here (acyclic / two-node / leaf-target) plus the whole
    `FourNodeCycleTests` class, which was a single test that built four temp-repo plan FILES to assert
    a four-node cycle is detected. Absorbing it as a GRAPH row rather than leaving it a file fixture
    is the right home for the claim it makes: the docstring said the point was to guard against "a
    future length-limited rewrite", and length is a property of the pure helper, not of the repo scan.
    The routine is one colored-DFS over `edges_by_plan`, so 2, 3 and 4 nodes exercise the SAME
    back-edge branch and belong in one place where a reader can see the lengths are contiguous.
    `CheckSurfaceTests` below separately covers that a cycle reaches the repo-scanning entry points,
    and `EvaluatorRuleMatrixTests` already covers 2- and 3-node cycles end to end through real files,
    so no coverage is lost by making this row a graph.

    THE ROWS PIN THE CYCLE CONTENT, NOT JUST A COUNT. The old two-node test asserted only
    `len(cycles) == 1`, which a routine returning the WRONG cycle satisfies. Each row here names the
    exact expected cycle lists, which is what makes the reported `aw check` detail ("a -> b -> c ->
    a") trustworthy.

    ACYCLIC ROWS ARE IN THE SAME TABLE deliberately: a helper that returned a cycle for every graph
    and one that returned none are opposite failures, and a table holding both kinds cannot pass
    under either.
    """

    #: (case, the graph as {owner id6: [target id6]}, the EXACT expected cycle list, why this row
    #: exists)
    #:
    #: A cycle is reported as the visitation path with the closing node repeated, and nodes and
    #: neighbors are visited in SORTED order, so these literals are deterministic rather than
    #: incidental.
    GRAPHS = (
        (
            "a linear chain where the last node is an owner with no edges",
            {"a": ["b"], "b": ["c"], "c": []},
            [],
            "THE POSITIVE ROW: the ordinary shape of a real Set, where each plan depends on the one "
            "before it. Every cycle-detecting row below is vacuous while this one is broken, because "
            "a routine that reports a cycle for everything satisfies all of them",
        ),
        (
            "a two-node cycle",
            {"a": ["b"], "b": ["a"]},
            [["a", "b", "a"]],
            "the minimal cycle, and the one an author actually writes: two plans each declaring they "
            "come after the other. The expected list pins WHICH cycle, where the old test pinned "
            "only that there was one of them",
        ),
        (
            "a three-node cycle",
            {"a": ["b"], "b": ["c"], "c": ["a"]},
            [["a", "b", "c", "a"]],
            "one indirection longer, so the back edge is found from a node that is NOT the search "
            "root. A routine only checking immediate reciprocity passes the two-node row and fails "
            "this one",
        ),
        (
            "a four-node cycle",
            {"a": ["b"], "b": ["c"], "c": ["d"], "d": ["a"]},
            [["a", "b", "c", "d", "a"]],
            "ABSORBED FROM `FourNodeCycleTests` (OQ-02), which built four plan FILES for this. Adds "
            "little assurance over three nodes, because the routine is a general colored DFS rather "
            "than length-specific logic, and is kept as a cheap guard against a future rewrite that "
            "hardcodes a lookahead depth",
        ),
        (
            "a self edge",
            {"a": ["a"]},
            [["a", "a"]],
            "the DEGENERATE cycle, length one. It is reported here even though the STATEMENT PARSER "
            "rejects a self dependency as malformed first (see the evaluator matrix), so the pure "
            "helper must not quietly rely on the parser having filtered it: this function is also "
            "called on graphs assembled from already-accepted edges",
        ),
        (
            "a target that is not itself an owner in the graph",
            {"a": ["b"]},
            [],
            "`b` is a LEAF: a spec or backlog id6, or an IPD outside the scanned tree. Only "
            "IPD-typed edges make a node an owner, so a leaf cannot close a cycle and must not be "
            "treated as one. NOTE the repo-level scan reports such an edge as "
            "`check.ipd-dependency-dangling` instead, which is a different rule and a different "
            "layer; silence HERE is what keeps the two from double-reporting one defect",
        ),
        (
            "two disjoint cycles in one graph",
            {"a": ["b"], "b": ["a"], "c": ["d"], "d": ["c"]},
            [["a", "b", "a"], ["c", "d", "c"]],
            "ALL cycles are reported, not just the first found. A routine returning early would "
            "hide the second one from an author who then fixes half the graph and re-runs, and the "
            "sorted visitation order is what makes the two-element list order stable",
        ),
        (
            "an empty graph",
            {},
            [],
            "the boundary a repo with no plans (or no IPD-typed edges) produces. It must return "
            "empty rather than raising, because `aw check` runs on trees that legitimately have no "
            "dependency statements at all",
        ),
    )

    def test_every_graph_shape_yields_exactly_its_cycles(self):
        wrong = []
        positive_rows_broken = 0
        for case, graph, expected, why in self.GRAPHS:
            got = S.item_dependency_cycles(dict(graph))
            if got != expected:
                if not expected:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - graph {graph!r}\n"
                    f"    - expected cycles {expected!r}\n"
                    f"    - got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} ACYCLIC row(s) are among the failures, and while any of "
                "those is broken every cycle row here is VACUOUS: a routine that reports a cycle "
                "for every graph satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"ipd_schema.item_dependency_cycles was wrong on {len(wrong)} of {len(self.GRAPHS)} "
            f"graph shapes.{vacuity} The rows are ordered by cycle LENGTH (1, 2, 3, 4), so SEVERAL "
            "LENGTHS FAILING TOGETHER means the detection routine itself broke, while ONE length "
            "failing alone means something became length-specific, which is exactly the rewrite "
            "OQ-02 added the four-node row to catch. FIX: a wrong cycle LIST (right count, wrong "
            "nodes) is as bad as no detection, because the reported path is what `aw check` prints "
            "for an author to break the cycle with.\n" + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-02: aw check plans AND all surface findings once
# --------------------------------------------------------------------------------------


class CheckSurfaceTests(unittest.TestCase):
    """V-02: one tree, checked through EVERY entry point a user or CI can reach it by.

    ONE table replaces four tests. All four wrote a single plan into a temp repo and asked whether the
    dependency rule fired, differing only in which function they called (`check_ipd_dependencies`,
    `check_content("plans")`, `check_types(["all"])`) and in the statement they wrote. THE ENTRY POINT
    IS THEREFORE A COLUMN, and making it one is the whole reason this is a table: the property V-02
    actually states is that `aw check plans` and `aw check all` AGREE with the bare check function, and
    an agreement claim cannot be made by three tests that each know about one route. A rule wired into
    `check_content` but missing from the `all` aggregator was invisible before.

    EVERY ROW ASSERTS THE PER-ROUTE COUNT, NOT MERELY MEMBERSHIP, which is how the old
    double-reporting test's claim generalizes. `check_types(["all"])` sweeps plans through more than
    one code path, so a finding reachable twice would appear twice and a user would see one defect
    listed as two. Expecting an exact count per route makes every row carry that guard for free
    instead of only the one fixture that had a dedicated test.

    THE CLEAN ROW IS IN THE SAME TABLE because it is the only thing standing between these rows and a
    checker that flags every plan: with negative rows alone, `return [DANGLING]` passes them all.
    """

    #: (case, [(id6, order, item_deps)], the rule each route must report, how MANY times, why this
    #: row exists)
    #:
    #: THE RULE IDS ARE LITERAL STRINGS, NOT `S.RULE_*` CONSTANTS, AND THAT IS DELIBERATE: `aw check`
    #: prints them, CI greps them, and `aw attention` routes on them, so a renumbering is a BREAKING
    #: CHANGE. Referencing the constants would move both sides together and hide it. Do not "tidy"
    #: these into constants.
    SURFACES = (
        (
            "an edge to an id6 nothing owns",
            [("aaaaaa", 1, "executed:zzzzzz")],
            "check.ipd-dependency-dangling",
            1,
            "THE CANONICAL FINDING and the reason `aw check` scans dependencies at all: a plan "
            "declaring it comes after something that does not exist can never become runnable, and "
            "the runner would mark it `dependency-blocked` forever with no explanation",
        ),
        (
            "a two-node cycle",
            [("aaaaaa", 1, "executed:bbbbbb"), ("bbbbbb", 2, "executed:aaaaaa")],
            "check.ipd-dependency-cycle",
            1,
            "a SECOND rule of the family through the same routes, which is what proves the routes "
            "carry the whole check rather than one wired-up rule. It is also the finding whose "
            "REPORT COUNT is most fragile: a cycle is discoverable from either of its two nodes, so "
            "a de-duplication regression shows up here as 2 and nowhere else",
        ),
        (
            "a clean `none` statement",
            [("aaaaaa", 1, "none")],
            None,
            0,
            "THE POSITIVE ROW: an explicit `none` is the correct, fully-declared state and must be "
            "SILENT on every route. Both rows above are vacuous while this one is broken, because a "
            "checker that flags every plan satisfies them",
        ),
    )

    #: (label, how to run it, why this route is checked)
    ROUTES = (
        (
            "check_ipd_dependencies (the bare check function)",
            lambda repo: ce.check_ipd_dependencies(repo),
            "the rule's own entry point; a failure here and nowhere else means the rule broke, not "
            "the wiring",
        ),
        (
            "check_content('plans') (reached by `aw check plans`)",
            lambda repo: ce.check_content(repo, "plans"),
            "the per-type surface a maintainer invokes directly, and the one a pre-commit hook or CI "
            "step is most likely to call",
        ),
        (
            "check_types(['all']) (reached by `aw check all`)",
            lambda repo: ce.check_types(repo, ["all"]),
            "THE AGGREGATOR, and the one that can be wrong in BOTH directions: a rule can be missing "
            "from the sweep entirely, or reached twice and reported twice",
        ),
    )

    def test_every_check_entry_point_reports_the_same_findings_once(self):
        wrong = []
        positive_rows_broken = 0
        for case, plans, expected, times, why in self.SURFACES:
            repo = _mkrepo()
            # Cutover in the past, so a missing statement would be an error rather than
            # grandfathered; every row here declares one, so this only removes a confound.
            _set_cutover(repo, "2020-01-01")
            for id6, order, item_deps in plans:
                _plan(repo, id6=id6, order=order, item_deps=item_deps)
            problems = []
            for label, run, route_why in self.ROUTES:
                reported = _rules(run(repo))
                if expected is None:
                    if reported:
                        problems.append(
                            f"via {label}: expected NO dependency finding, got {reported!r}"
                        )
                    continue
                count = reported.count(expected)
                if count != times:
                    problems.append(
                        f"via {label}: expected {expected!r} exactly {times} time(s), got {count} "
                        f"(all dependency findings on this route: "
                        f"{reported or 'NOTHING AT ALL'}); this route matters because {route_why}"
                    )
            if problems:
                if expected is None:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} CLEAN row(s) are among the failures, and while any of "
                "those is broken every flagging row here is VACUOUS: a checker that flags every "
                "plan satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the dependency rule family disagreed across entry points on {len(wrong)} of "
            f"{len(self.SURFACES)} trees.{vacuity} READ WHICH ROUTE FAILED: if ONE route failed on "
            "several rows, the rule is fine and its WIRING into that surface broke, so fix the "
            "surface (`check_content` / `check_types`), not the rule. If EVERY route failed on one "
            "row, that fixture's rule broke. A count of 2 where 1 was expected is a DOUBLE REPORT, "
            "which shows a user one defect as two and is a `check_types` aggregation bug rather than "
            "a rule bug. FIX: a route reporting NOTHING AT ALL is the worst case, because `aw check "
            "all` is what CI runs, and a rule missing from it is a rule that does not exist in "
            "practice.\n" + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-03: phased lint matrix (pure syntax fn + resolution pass)
# --------------------------------------------------------------------------------------


class PhasedLintTests(unittest.TestCase):
    """V-03: the phase matrix, in BOTH layers: the pure syntax function and the repo-aware `lint_file`.

    TWO tables replace nine tests, and THE PHASE IS A COLUMN rather than a test name, which is the
    whole point. The property V-03 states is not "unresolved is advisory" and separately "unresolved
    blocks"; it is that the SAME statement gets a DIFFERENT severity at a DIFFERENT checkpoint, so the
    severity must be asserted across the whole phase axis at once. The old shape asserted one cell per
    test and left most of the grid empty: `malformed` was checked at `author` only, so a change making
    it merely advisory at `pre-execution` (the phase that gates execution) passed. Every statement is
    now evaluated at all four phases.

    THE TWO LAYERS ARE SEPARATE TABLES BECAUSE THEIR INPUTS DIFFER IN KIND, not because the claims
    differ: the pure function takes a PARSED DOCUMENT and can only see syntax, while `lint_file` takes
    a FILE IN A REPO and additionally resolves ids and reads the cutover marker. Keeping them adjacent
    documents the division of labour the design rests on, which the second table's `missing` and
    `dangling` rows depend on: both are SILENT in the pure layer (see the `PURE` rows) and blocking in
    the resolved one.

    WHY `missing` AND `dangling` ARE SILENT IN THE PURE LAYER, since it reads as a gap: the MISSING
    rule is cutover-gated and the DANGLING rule needs the whole tree, so neither is decidable from one
    document. Emitting them there would mass-fail (or mass-advise on) every pre-cutover plan in the
    corpus, which is the outcome the grandfathering design exists to avoid.
    """

    PHASES = ("author", "review-finalize", "pre-execution", "pre-transition")
    BLOCKING_PHASES = ("review-finalize", "pre-execution", "pre-transition")

    def _doc(self, item_deps: str | None):
        dep = f"- Item-Dependencies: {item_deps}\n" if item_deps is not None else ""
        text = (
            "# IPD: x\n\n- Date: 2026-08-27\n- Kind: child\n- Scope-Paths: x.py\n"
            f"{dep}- Status: draft\n- Set: demo\n- Order: 1\n- Id: aaaaaa\n\n"
            "## Workflow history\n- 2026-08-27 draft (t): x\n\n## Goal\ng\n"
        )
        return ipd_lint.parse(text)

    #: (case, the statement or None to omit the field, {phase: (blocking codes, advisory codes)}
    #: given as a dict keyed by phase or by the sentinel "*" meaning every phase, why this row exists)
    #:
    #: THE RULE IDS ARE LITERAL STRINGS ON PURPOSE (see the module docstring): they are printed to
    #: users and gated on by `aw ipd begin`, so a renumbering must fail here rather than move both
    #: sides of a comparison together.
    PURE = (
        (
            "an explicit `none`",
            "none",
            {"*": ((), ())},
            "THE POSITIVE ROW: `none` is a COMPLETE declaration ('I depend on nothing'), not an "
            "absence, so it must be silent at every phase. Every row below is vacuous while this one "
            "is broken, because a check that flagged every statement satisfies them all",
        ),
        (
            "no statement at all",
            None,
            {"*": ((), ())},
            "SILENT IN THIS LAYER AT EVERY PHASE, including the blocking ones. The MISSING rule is "
            "cutover-gated and repo-aware, so it is applied in `lint_file` (see the RESOLVED table) "
            "where the marker is readable. Emitting it here would mass-fail the entire pre-cutover "
            "corpus, and emitting it as an ADVISORY here would flood every author with a nudge they "
            "cannot act on. Both halves are asserted, which the old test pair did only at two phases",
        ),
        (
            "the `unresolved` sentinel",
            "unresolved",
            {
                "author": ((), ("check.ipd-dependency-unresolved",)),
                "*": (("check.ipd-dependency-unresolved",), ()),
            },
            "THE ROW THE WHOLE PHASE AXIS EXISTS FOR: `unresolved` is the HONEST state while drafting "
            "(the author has not worked the edges out yet), so at `author` it is an ADVISORY nudge "
            "and must NOT block. By review it is an unanswered question about execution ORDER, so it "
            "BLOCKS. A single-phase test cannot state that transition, and either half alone is "
            "wrong: blocking at `author` makes `aw ipd scaffold`'s own output unlintable, since "
            "scaffold emits exactly this sentinel",
        ),
        (
            "a duplicate edge (malformed)",
            "executed:aaaaaa, executed:aaaaaa",
            {"*": (("check.ipd-dependency-malformed",), ())},
            "BLOCKING AT EVERY PHASE, `author` INCLUDED, which is what distinguishes a SYNTAX defect "
            "from an unfinished one: a statement that does not parse has no meaning to defer, so "
            "there is nothing to nudge about. The old test checked `author` alone, so a regression "
            "demoting this to advisory at `pre-execution` (the phase gating execution) would have "
            "passed",
        ),
        (
            "an edge to an id6 nothing owns",
            "executed:zzzzzz",
            {"*": ((), ())},
            "SILENT IN THIS LAYER, and NOT because dangling is tolerated: it is blocking in the "
            "RESOLVED table below. Resolution needs the whole plans tree, which a single parsed "
            "document does not have. This row is what documents the layer boundary; without it a "
            "reader would take the pure function for the complete check",
        ),
    )

    def test_the_pure_syntax_check_assigns_the_right_severity_at_every_phase(self):
        wrong = []
        positive_rows_broken = 0
        for case, statement, expectations, why in self.PURE:
            doc = self._doc(statement)
            problems = []
            for phase in self.PHASES:
                want_block, want_adv = expectations.get(phase, expectations["*"])
                blocking, advisory = ipd_lint.check_item_dependencies(
                    doc, phase, "pending"
                )
                got_block = tuple(d.code for d in blocking)
                got_adv = tuple(d.code for d in advisory)
                if got_block != tuple(want_block):
                    problems.append(
                        f"at phase {phase!r}: expected BLOCKING {tuple(want_block)!r}, got "
                        f"{got_block or 'nothing'}"
                    )
                if got_adv != tuple(want_adv):
                    problems.append(
                        f"at phase {phase!r}: expected ADVISORY {tuple(want_adv)!r}, got "
                        f"{got_adv or 'nothing'}"
                    )
            if problems:
                silent_row = not any(
                    codes for pair in expectations.values() for codes in pair
                )
                if silent_row:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case} (statement {statement!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} SILENT row(s) are among the failures, and while any of "
                "those is broken every flagging row here is VACUOUS: a check that flags every "
                "statement satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"ipd_lint.check_item_dependencies assigned the wrong severity for {len(wrong)} of "
            f"{len(self.PURE)} statements.{vacuity} READ THE DIRECTION, because the two failures are "
            "not symmetric: a rule that started BLOCKING at `author` refuses documents "
            "`aw ipd scaffold` itself writes and stops authoring dead, while a rule that stopped "
            "blocking at `pre-execution` lets an undeclared or unparseable dependency through the "
            "gate that guards execution, which is the silent and dangerous direction. FIX: if the "
            "`missing` or `dangling` row started firing here, the fix is NOT to delete the row: those "
            "rules belong in `lint_file`, where the cutover marker and the rest of the tree are "
            "readable, and moving them earlier mass-fails the grandfathered corpus.\n"
            + "\n".join(wrong),
        )

    #: (case, cutover marker date or None, the plan's own Date, the statement or None, the dependency
    #: codes `lint_file` must report at a BLOCKING phase, why this row exists)
    RESOLVED = (
        (
            "a POST-cutover plan with no statement",
            "2026-01-01",
            "2026-08-27",
            None,
            ("check.ipd-missing-dependency-statement",),
            "THE CUTOVER'S WHOLE PURPOSE: once a repo declares a date, every plan written AFTER it "
            "must state its dependencies, so the field is mandatory going forward. This is the rule "
            "the pure layer cannot express, because only `lint_file` can read the marker",
        ),
        (
            "a PRE-cutover plan with no statement",
            "2026-08-01",
            "2026-01-01",
            None,
            (),
            "GRANDFATHERED, and the reason the cutover is a date rather than a flag: a plan written "
            "before the rule existed cannot have obeyed it, and flagging it would demand edits to "
            "plans that may already be in `executed/`, which AGENTS.md forbids",
        ),
        (
            "no cutover marker at all, no statement",
            None,
            "2026-08-27",
            None,
            (),
            "AN UNCONFIGURED REPO MUST NOT MASS-FAIL. Absence of the marker means the repo has not "
            "adopted the rule, so a missing statement is the norm rather than a defect. This is the "
            "DEFAULT every adopter starts in, so a regression here breaks every fresh install at once",
        ),
        (
            "an edge to an id6 nothing owns",
            "2020-01-01",
            "2026-08-27",
            "executed:zzzzzz",
            ("check.ipd-dependency-dangling",),
            "THE RESOLUTION PASS, which is what `lint_file` adds over the pure function: the tree is "
            "readable here, so the edge can be checked against it. Silent in the PURE table above, "
            "blocking here, and that contrast IS the layer boundary",
        ),
        (
            "a fully-declared `none`",
            "2020-01-01",
            "2026-08-27",
            "none",
            (),
            "THE POSITIVE ROW: with a cutover in force, a plan that DOES declare its dependencies "
            "must draw no dependency finding. Every row above is vacuous while this one is broken. "
            "It asserts the dependency FAMILY is empty rather than that the plan lints clean, "
            "because this three-line fixture legitimately trips many structural rules (missing "
            "required H2, missing metadata, `draft` status at a pre-execution checkpoint)",
        ),
    )

    def test_lint_file_resolves_the_repo_aware_rules_at_a_blocking_phase(self):
        wrong = []
        positive_rows_broken = 0
        for case, cutover, date, statement, expected, why in self.RESOLVED:
            problems = []
            for phase in self.BLOCKING_PHASES:
                repo = _mkrepo()
                _set_cutover(repo, cutover)
                p = _plan(repo, id6="aaaaaa", order=1, item_deps=statement, date=date)
                res = ipd_lint.lint_file(p, checkpoint=phase)
                got = tuple(
                    d.code for d in res.diagnostics if d.code.startswith("check.ipd-")
                )
                if got != expected:
                    problems.append(
                        f"at phase {phase!r}: expected dependency codes {expected!r}, got "
                        f"{got or 'NOTHING AT ALL'}"
                    )
                if expected and res.disposition != S.DISPOSITION_ERROR:
                    problems.append(
                        f"at phase {phase!r}: a flagged plan must have disposition "
                        f"{S.DISPOSITION_ERROR!r}, got {res.disposition!r}; a finding that does not "
                        "set the disposition is a finding no gate acts on"
                    )
            if problems:
                if not expected:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case} (cutover {cutover!r}, plan dated {date}, statement {statement!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} row(s) that must draw NO dependency finding are among the "
                "failures, and while any of those is broken the flagging rows are VACUOUS: a linter "
                "that flags every plan satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"ipd_lint.lint_file mishandled {len(wrong)} of {len(self.RESOLVED)} repo-aware "
            f"fixtures.{vacuity} THE THREE GRANDFATHERING ROWS FAILING TOGETHER means the cutover "
            "comparison itself broke (a date parse, or the marker no longer being read), not that "
            "three policies changed: check `_set_cutover`'s file shape against what the resolver "
            "reads before touching the rule. FIX: a grandfathering row that STARTED firing is the "
            "expensive direction, because it demands a dependency statement be added to every "
            "pre-cutover plan, including ones in `executed/` that AGENTS.md forbids editing.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-04: grandfathering
# --------------------------------------------------------------------------------------


class GrandfatheringTests(unittest.TestCase):
    """V-04: the MISSING rule fires only for plans the cutover actually reaches.

    ONE table replaces three tests. All three wrote plans with no `- Item-Dependencies:` field into a
    temp repo, called `check_ipd_dependencies`, and asked whether MISSING fired; they differed only in
    the cutover marker and the plans' dates. THE MARKER AND THE DATE ARE THEREFORE COLUMNS, and that
    is what makes the table state the actual policy: this rule is a COMPARISON between two dates, so
    every row must say which side of the marker it sits on. Three separately-named tests hid that they
    were three points on one axis.

    THE `no marker` ROW WRITES TWO PLANS, kept from the test it replaces: the risk the cutover design
    guards against is a MASS failure across the corpus, so the row asserts a count of zero over more
    than one candidate rather than testing a single file that happens to pass.

    Where a `lint_file` view of the same policy is asserted, see `PhasedLintTests.RESOLVED`. The two
    are deliberately not merged: this table is the `aw check` repo sweep (many plans, one call), that
    one is the per-file lint at a checkpoint, and a policy present in one and missing from the other is
    precisely the drift worth catching.
    """

    #: (case, cutover marker date or None, [(id6, order, Date)] all written WITHOUT the field, how
    #: many MISSING findings are expected, why this row exists)
    #:
    #: The rule id is a LITERAL STRING on purpose (see the module docstring).
    CUTOVERS = (
        (
            "no cutover marker, several plans missing the field",
            None,
            [("aaaaaa", 1, "2026-08-27"), ("bbbbbb", 2, "2026-08-27")],
            0,
            "AN UNADOPTED REPO MUST NOT MASS-FAIL, and TWO plans are written precisely because "
            "MASS-failing is the risk: absence of the marker means the repo never adopted the rule, "
            "so a missing statement is the norm. This is the state every fresh adopter is in, so a "
            "regression here fires on every install at once",
        ),
        (
            "a plan dated AFTER the cutover",
            "2026-01-01",
            [("aaaaaa", 1, "2026-08-27")],
            1,
            "THE RULE ITSELF: once a repo sets a date, a plan authored after it must declare its "
            "dependencies. Exactly one finding is expected, so a rule that reported per-edge or "
            "per-phase instead of per-plan is caught here rather than surfacing as duplicate output",
        ),
        (
            "a plan dated BEFORE the cutover",
            "2026-08-01",
            [("aaaaaa", 1, "2026-01-01")],
            0,
            "GRANDFATHERED. A plan written before the rule existed could not have obeyed it, and "
            "flagging it demands edits to plans that may already be in `executed/`, which AGENTS.md "
            "forbids. This row and the one above share a fixture and differ ONLY in which side of the "
            "marker the date falls, which is what makes them a real boundary test rather than two "
            "anecdotes",
        ),
    )

    def test_the_cutover_decides_exactly_which_plans_owe_a_statement(self):
        wrong = []
        for case, cutover, plans, expected_count, why in self.CUTOVERS:
            repo = _mkrepo()
            _set_cutover(repo, cutover)
            for id6, order, date in plans:
                _plan(repo, id6=id6, order=order, item_deps=None, date=date)
            drift = ce.check_ipd_dependencies(repo)
            found = [
                d for d in drift if d.rule == "check.ipd-missing-dependency-statement"
            ]
            if len(found) != expected_count:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected_count} "
                    f"'check.ipd-missing-dependency-statement' finding(s), got {len(found)} "
                    f"({[d.location for d in found]!r})\n"
                    f"    - all rules reported: {_rules(drift) or 'nothing'}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the cutover gate admitted or refused the wrong plans in {len(wrong)} of "
            f"{len(self.CUTOVERS)} configurations. ALL THREE ROWS FAILING TOGETHER means the marker "
            "is no longer being READ at all (a `.aw/config/project.json` shape change, or a date "
            "parse), not that three policies changed; verify `_set_cutover`'s file against what the "
            "resolver loads before touching the rule. FIX: the two directions cost very differently. "
            "A rule that stopped firing post-cutover silently lets undeclared plans accumulate, "
            "which the runner later reports as unexplained `dependency-blocked` items. A rule that "
            "STARTED firing pre-cutover demands a field be added to every historical plan, including "
            "ones in `executed/` that AGENTS.md forbids editing, so it cannot simply be complied "
            "with.\n" + "\n".join(wrong),
        )

    def test_current_repo_not_mass_failed(self):
        """Kept separate: the subject is the REAL repository, not a fixture.

        Every row above builds a temp tree with a chosen marker and chosen dates; this asserts the
        shipped corpus under this checkout's own configuration is clean, which is a claim about the
        repository rather than about the rule. It is also the only guard that would catch a cutover
        date being committed that retroactively obliges hundreds of existing plans.
        """
        repo = Path(__file__).resolve().parents[1]
        drift = ce.check_ipd_dependencies(repo)
        missing = [d for d in drift if d.rule == S.RULE_IPD_DEP_MISSING]
        self.assertEqual(
            missing,
            [],
            f"current corpus must not mass-fail; got {len(missing)} missing findings",
        )

    def test_no_tool_auto_inserts_none(self):
        """Kept separate: the assertion is over MODULE SOURCE TEXT, not over any tree or result.

        `none` is a substantive claim ('I depend on nothing') that only an author can make, so no tool
        may write it on their behalf; scaffold emits the `unresolved` sentinel instead. There is no
        fixture that can express 'no code path anywhere writes this string', so this greps the module.
        """
        from agent_workflows import ipd_authoring

        import inspect

        src = inspect.getsource(ipd_authoring)
        self.assertIn("- Item-Dependencies: unresolved", src)
        self.assertNotIn("- Item-Dependencies: none", src)


# --------------------------------------------------------------------------------------
# detrun Order bmh754: `From-Spec` schema recognition + `check.from-spec-dangling`.
#
# These live in THIS module rather than a new `tests/test_item_dependencies.py` on purpose: the
# reviewed plan explicitly prohibits creating that module because it would duplicate this one. The
# `From-Spec` link is the spec-side twin of `From-Backlog` and its dangling rule is a sibling of the
# `check.ipd-dependency-dangling` family already covered above, so it belongs beside them.
# --------------------------------------------------------------------------------------


def _plan_from_spec(repo: Path, *, id6: str, order: int, from_spec: str) -> Path:
    """A plan carrying a `- From-Spec:` line (the fixture `_plan` does not emit one)."""
    pend = repo / ".aw" / "records" / "plans" / "pending"
    pend.mkdir(parents=True, exist_ok=True)
    date = "2026-08-30"
    p = pend / f"{date.replace('-', '')}-demo-{order:02d}-{id6}-p.ipd.md"
    p.write_text(
        f"# IPD: {id6}\n\n"
        f"- Date: {date}\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: none\n"
        f"- From-Spec: {from_spec}\n"
        f"- Status: draft\n- Set: demo\n- Order: {order}\n- Id: {id6}\n\n"
        f"## Workflow history\n- {date} draft (t): x\n\n## Goal\ng\n",
        encoding="utf-8",
    )
    return p


class FromSpecSchemaRecognitionTests(unittest.TestCase):
    """The graduation-source carriers must be RECOGNIZED but OPTIONAL, and must AGREE with each other.

    ONE table replaces three tests that each made one membership assertion about `From-Spec`
    (recognized / not required / agrees with `From-Backlog` on optionality). THE FIELD IS A COLUMN, so
    the agreement claim the third test tried to make is now structural rather than an extra assertion:
    both carriers are checked against the same two sets, and a divergence shows up as one of them
    failing a cell the other passes. That matters because `aw check`'s close-legitimacy predicate
    accepts EITHER carrier as a release-gate handoff, so one being enforceable and the other not is a
    real hole rather than an aesthetic inconsistency.

    Both halves of each cell are load-bearing and they pull in opposite directions: an UNRECOGNIZED
    field raises IPD-M103 ("unknown field") and makes every plan that carries a legitimate handoff
    link nonconforming, while a REQUIRED field mass-fails every plan that has no graduation source at
    all, which is most of them.
    """

    #: (case, the field name, must be RECOGNIZED, must be REQUIRED, why this row exists)
    CARRIERS = (
        (
            "From-Spec (the spec-side graduation source)",
            S.META_FROM_SPEC,
            True,
            False,
            "the newer of the two carriers, added by detrun Order bmh754. Recognition is what keeps "
            "it from raising IPD-M103 on a plan that legitimately graduated from a spec; optionality "
            "is what keeps it from mass-failing the plans that graduated from nothing",
        ),
        (
            "From-Backlog (the backlog-side graduation source)",
            S.META_FROM_BACKLOG,
            True,
            False,
            "THE TWIN, and the row that turns this table into an agreement check. AGENTS.md makes a "
            "spec an 'equally valid gate carrier' to a backlog item, so the two must have the SAME "
            "enforceability. If this row's answers ever differ from the row above, one handoff shape "
            "is enforceable and the other is not, and a release gate can be dropped through whichever "
            "is weaker",
        ),
    )

    def test_both_graduation_source_carriers_are_recognized_and_optional(self):
        wrong = []
        for case, field, recognized, required, why in self.CARRIERS:
            problems = []
            if (field in S.META_RECOGNIZED) is not recognized:
                problems.append(
                    f"expected {field!r} in META_RECOGNIZED to be {recognized}, got "
                    f"{field in S.META_RECOGNIZED}"
                )
            if (field in S.META_REQUIRED) is not required:
                problems.append(
                    f"expected {field!r} in META_REQUIRED to be {required}, got "
                    f"{field in S.META_REQUIRED}"
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
            f"{len(wrong)} of {len(self.CARRIERS)} graduation-source carriers have the wrong schema "
            "membership. IF ONLY ONE ROW FAILED, the two carriers have DIVERGED, which is the failure "
            "this table exists to catch: AGENTS.md treats a spec and a backlog item as equally valid "
            "release-gate carriers, so a gate can now be dropped through whichever of the two is the "
            "weaker. If BOTH failed, the metadata vocabulary itself was edited. FIX: losing "
            "RECOGNITION makes every plan carrying that link report IPD-M103 (unknown field); gaining "
            "REQUIREMENT mass-fails every plan that graduated from nothing, which is most of the "
            "corpus. Neither is a small change.\n" + "\n".join(wrong),
        )

    def test_from_spec_does_not_raise_unknown_field(self):
        """Kept separate: the claim is about a LINTED FILE, not about set membership.

        The table asserts `From-Spec` is in `META_RECOGNIZED`; this asserts the linter actually USES
        that set, by linting a real plan carrying the field and requiring IPD-M103 to be absent. A
        recognition set the metadata check no longer consults would pass the table and fail here.
        """
        repo = _mkrepo()
        _spec(repo, id6="spec01")
        p = _plan_from_spec(repo, id6="aaaaaa", order=1, from_spec="spec01")
        res = ipd_lint.lint_file(p, checkpoint="author")
        blob = "\n".join(
            f"{getattr(d, 'code', '')} {getattr(d, 'message', '')}"
            for d in res.diagnostics
        )
        self.assertNotIn(
            "IPD-M103",
            blob,
            f"From-Spec must not be an unknown field; got {blob}",
        )


class FromSpecDanglingRuleTests(unittest.TestCase):
    """`check.from-spec-dangling`: a `From-Spec` link that resolves to nothing is a broken handoff.

    ONE table replaces five tests. Each wrote a small tree into a temp repo, called
    `check_from_spec_dangling`, and asserted the returned rule list, differing only in the tree: a
    resolvable link, an unresolvable one, no link at all, no specs tree, and the link carried on a spec
    instead of a plan. THE CARRIER (plan versus spec) AND THE PRESENCE OF A SPECS TREE ARE COLUMNS,
    because in both cases the interesting property is that the SAME link gets a different answer in a
    different context.

    THE FIRING ROW ALSO ASSERTS THE FINDING'S CONTENT, absorbing a sixth test: a dangling finding must
    carry a `recovery` and must name the unresolvable id6 in its `detail`. That is not a separate
    claim about the same input, it is the difference between a finding a maintainer can act on and one
    that only says something is wrong, so it belongs on the row that produces it.

    THE `no specs tree` ROW IS THE MOST IMPORTANT ONE and is FAIL-SAFE by design: with no discoverable
    spec identity at all, a dangling link and an invisible corpus are indistinguishable, so the rule
    must report NOTHING rather than flag every link. That is a real measured false positive, not a
    hypothetical: in an externally-redirected project the spec read-path resolver returned a directory
    outside the repo, the known-set came back empty, and every valid link looked dangling.

    THE SILENT ROWS ARE IN THE SAME TABLE as the firing ones because they fail in opposite directions:
    a rule that flags nothing and a rule that flags every link would each pass a table containing only
    the other kind.
    """

    #: (case, specs to write as [(id6)], plans to write as [(kind, id6, from_spec)] where kind is
    #: "from-spec" / "plain" / "spec-carrier", the EXACT expected rule list, the id6 the detail must
    #: name or None, why this row exists)
    #:
    #: The rule id is a LITERAL STRING on purpose (see the module docstring): `aw check` prints it and
    #: `aw attention` routes on it.
    LINKS = (
        (
            "a plan whose From-Spec resolves to a real spec",
            ["spec01"],
            [("from-spec", "aaaaaa", "spec01")],
            [],
            None,
            "THE POSITIVE ROW and the ordinary case: a spec-first graduation, which AGENTS.md makes "
            "an equally valid release-gate handoff. Every firing row below is vacuous while this one "
            "is broken, because a rule that flags every link satisfies them all",
        ),
        (
            "a plan whose From-Spec resolves to nothing",
            ["spec01"],
            [("from-spec", "aaaaaa", "zzzzzz")],
            ["check.from-spec-dangling"],
            "zzzzzz",
            "THE RULE ITSELF. A `From-Spec` pointing at no spec is a BROKEN HANDOFF CLAIM, which is "
            "worse than no claim: a release-blocking backlog item may have been closed `done` on the "
            "strength of it, so the gate is gone and the artifact meant to carry it does not exist. "
            "The row also requires the finding to carry a `recovery` and to NAME the unresolved id6, "
            "since a finding that says only 'a link is broken' leaves a maintainer grepping",
        ),
        (
            "a plan carrying no From-Spec at all",
            ["spec01"],
            [("plain", "aaaaaa", None)],
            [],
            None,
            "THE FIELD IS OPTIONAL (see the schema table above), so its ABSENCE is not a defect. "
            "Without this row the rule could be 'every plan must declare a graduation source', which "
            "would fire on most of the corpus",
        ),
        (
            "a link with NO specs tree in the repo at all",
            [],
            [("from-spec", "aaaaaa", "zzzzzz")],
            [],
            None,
            "FAIL-SAFE, and a MEASURED false positive rather than a hypothetical: in an "
            "externally-redirected project the spec read-path resolver returned a directory outside "
            "the repo, so the known-set was empty and every VALID link looked dangling. With no "
            "discoverable spec identity, a dangling link is indistinguishable from an invisible "
            "corpus, so the rule must report nothing. Note this row uses the same unresolvable id6 as "
            "the firing row above and differs ONLY in whether a specs tree exists, which is what "
            "makes it a real fail-safe test",
        ),
        (
            "a SPEC carrying a dangling From-Spec",
            ["spec01"],
            [("spec-carrier", "spec02", "zzzzzz")],
            ["check.from-spec-dangling"],
            "zzzzzz",
            "THE CARRIER IS A COLUMN: the link's primary home is a plan, but a spec may graduate from "
            "another spec, and the scan tolerates it there for the same symmetry reason "
            "`check_from_backlog` does. A scan that only walked the plans tree would pass every other "
            "row and silently miss this whole class of link",
        ),
    )

    def test_every_from_spec_link_shape_gets_its_own_answer(self):
        wrong = []
        positive_rows_broken = 0
        for case, specs, plans, expected, named_id6, why in self.LINKS:
            repo = _mkrepo()
            for id6 in specs:
                _spec(repo, id6=id6)
            for kind, id6, from_spec in plans:
                if kind == "from-spec":
                    _plan_from_spec(repo, id6=id6, order=1, from_spec=from_spec)
                elif kind == "plain":
                    _plan(repo, id6=id6, order=1, item_deps="none")
                else:
                    d = repo / ".aw" / "records" / "specs"
                    d.mkdir(parents=True, exist_ok=True)
                    (d / f"20260101-1200-02-{id6}-s.spec.md").write_text(
                        f"# Spec {id6}\n\n- Id: {id6}\n- Status: draft\n"
                        f"- From-Spec: {from_spec}\n\n## Summary\ns\n",
                        encoding="utf-8",
                    )
            drift = ce.check_from_spec_dangling(repo)
            problems = []
            got = [d.rule for d in drift]
            if got != expected:
                problems.append(
                    f"expected rules {expected!r}, got {got or 'NOTHING AT ALL'}"
                )
            if expected and drift:
                finding = drift[0]
                if not finding.recovery:
                    problems.append(
                        "the finding carries no `recovery`; a dangling link must teach the fix, "
                        "because the remedy (correct the id6, or drop the claim) is not obvious from "
                        "the message"
                    )
                if named_id6 and named_id6 not in finding.detail:
                    problems.append(
                        f"the detail does not name the unresolvable id6 {named_id6!r}: "
                        f"{finding.detail!r}"
                    )
            if problems:
                if not expected:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} row(s) that must stay SILENT are among the failures, and "
                "while any of those is broken every firing row here is VACUOUS: a rule that flags "
                "every link satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"check_engine.check_from_spec_dangling was wrong on {len(wrong)} of {len(self.LINKS)} "
            f"link shapes.{vacuity} READ WHICH DIRECTION FAILED. If the `NO specs tree` row started "
            "FIRING, the known-set is empty and the rule is now flagging valid links in every "
            "externally-redirected project, which is the measured false positive it was written "
            "against. If the firing rows went SILENT, a broken handoff claim now passes `aw check`, "
            "and a release-blocking item closed on the strength of that claim has silently lost its "
            "gate. FIX: the fail-safe row and the firing row use the SAME unresolvable id6 and differ "
            "only in whether a specs tree exists, so if both moved together the resolver stopped "
            "discovering specs rather than the rule changing.\n" + "\n".join(wrong),
        )

    def test_rule_is_registered_as_error_like_its_backlog_twin(self):
        """Kept separate: the claim is about the RULE REGISTRY, not about any tree.

        An UNREGISTERED rule id silently falls back to the default `RuleSpec`, so registration is a
        behavioural contract rather than bookkeeping: severity decides whether `aw check` exits
        nonzero. Compared against the `From-Backlog` twin rather than to a literal, so the two
        equally-valid gate carriers cannot drift apart in severity.
        """
        spec = ce.rule_spec("check.from-spec-dangling")
        twin = ce.rule_spec("check.from-backlog-dangling")
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.severity, twin.severity)
        self.assertEqual(spec.invariant, twin.invariant)

    def test_current_repo_has_no_from_spec_findings(self):
        """Kept separate: the subject is the REAL checkout, not a fixture.

        Every row above builds a tree designed to produce a chosen answer; this asserts the shipped
        corpus gains no finding from this rule, which is the only guard against a new rule that is
        correct on fixtures and noisy on the real tree.
        """
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(ce.check_from_spec_dangling(repo), [])


if __name__ == "__main__":
    unittest.main()

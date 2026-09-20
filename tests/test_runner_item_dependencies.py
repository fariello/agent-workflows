"""lanetruth Order 03 (8guhs0): the runners must consume the SHARED `Item-Dependencies` predicate.

THE DEFECT THIS PINS. Both drivers carried a private `_DEPS_RE` matching a LEGACY
`Dependencies:`/`Depends-on:` field that no plan in the tree uses, so the canonical
`- Item-Dependencies:` statement was invisible: `_read_deps` returned `[]` for a valid three-edge
statement while `ipd_schema.parse_item_dependencies` returned three typed records, every frozen queue
item carried `dependencies: []`, and ordering fell back to Set/Order, which spec 25kzda calls only a
tiebreaker.

WHAT IS ASSERTED HERE, and the division of labor that must not be "consolidated" later:
  * the typed-edge round trip through BOTH drivers' record-building path (contrasted with the
    measured pre-fix `[]`), with QUALIFIERS PRESERVED rather than flattened to bare id6 strings;
  * each edge kind's runtime satisfaction rule (spec 2.9), including wait-not-start;
  * fail-closed preflight for malformed / dangling / ambiguous / cyclic / self-edge / `unresolved`
    statements, delegated ENTIRELY to `check_engine.evaluate_ipd_dependencies`;
  * NO runner-local missing-statement rule (8guhs0 OQ-02: that decision belongs to the shared
    evaluator plus the cutover marker);
  * declared edges authoritative for ordering, with Set/Order demoted to a tiebreaker, and the
    `dependency-blocked` cascade;
  * an ANTI-DIVERGENCE guard: neither driver may define a dependency regex or a private dependency
    parser, and the two must share ONE implementation.

MOST OF THIS FILE IS TABLE-DRIVEN, and DRIVER is the archetypal column. The whole point of the suite
is that the TWO hosts answer identically, so a per-host class would let a rule hold on oc and not on
agy while both classes stayed green - which is exactly the state this file was written to end (agy
carried its own broken copy of `dependency_status_detailed` for months). Every table below runs every
row through both drivers and reports the failing (row, driver) cells together. ACTION (`execute` vs
`review`), ENTRY POINT (`dependency_status` at dispatch vs `dependency_status_detailed` at drain),
and TARGET LOCATION (in-queue vs on-disk bucket) are likewise columns, because in each case the
property worth asserting is that the SAME edge gets different answers in different modes, which no
single-mode test can state.

ONE SOURCE-TEXT PIN WAS REPLACED. `test_the_status_field_is_read_with_the_already_shared_reader` ran
`inspect.getsource(oc_runipd.edge_satisfied)` through `_code_only` and then grepped the text for
`"_read_status"` and against `"_artifact_owners"`. Even with comments and strings stripped, that is a
change-detector on a NAME: it goes vacuous the moment the alias is renamed, it fails on any rewrite
that reaches the reader through a local variable, and it says nothing about which reader actually
ran. It is now asserted by DELEGATION - the shared reader is replaced with a sentinel and the edge
verdict must change - plus an OBSERVED call count proving the read is skipped entirely for a terminal
directory, which the text pin could not express at all.

THE REMAINING SOURCE READS IN THIS FILE ARE KEPT DELIBERATELY, and they are a different thing from a
text grep of a FUNCTION BODY. `_DRIVER_SOURCES` reads each driver FILE to prove a deleted construct
was not re-introduced (a `re.compile` whose pattern names a dependency field; the inlined
queue-status allowlist; `_DEPS_RE`). Those are ARCHITECTURE invariants about code that must not
exist, so there is no behavior to drive: a re-introduced private parser works correctly right up
until it drifts from the shared one, which is precisely how the defect this file pins was born. They
are also falsifiable in the right direction (they were each measured against the real pre-fix source)
and they run through `_code_only`, so honest documentation of the fix does not trip them.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    check_engine,
    ipd_schema,
    oc_runipd,
    review_findings,
    runner_shared,
    selectors,
)
from tests.support import REPO_ROOT

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_DRIVER_SOURCES = (
    ("oc_runipd", REPO_ROOT / "agent_workflows" / "oc_runipd.py"),
    ("agy_runipd", REPO_ROOT / "agent_workflows" / "agy_runipd.py"),
)

# One valid statement exercising ALL THREE edge kinds at once.
_THREE_EDGE_VALUE = "executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9"


def _code_only(text: str) -> str:
    """``text`` with `#` comments and docstrings/string literals removed, via the real tokenizer.

    The anti-divergence guards assert things about CODE, not about prose. A comment or docstring that
    NAMES the deleted construct in order to warn against it must not trip the guard, or the honest
    documentation of a fix would be indistinguishable from the defect.
    """
    import io
    import token as _token
    import tokenize as _tokenize

    kept: list[str] = []
    try:
        for tok in _tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (_token.COMMENT, _token.STRING):
                continue
            kept.append(tok.string)
    except (_tokenize.TokenError, IndentationError):  # pragma: no cover - defensive
        return "\n".join(
            ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
        )
    return "\n".join(kept)


def _code_without_prose(text: str) -> str:
    """``text`` with comments and DOCSTRINGS removed, but every OTHER string literal KEPT.

    THE MIDDLE GROUND BETWEEN TWO WRONG ANSWERS, both of which were measured on this repository.

    `_code_only` above drops every STRING token. A guard whose pattern anchors on a string literal
    (``'"queued"\\s*if\\s*status\\s*in\\s*\\('``) therefore becomes UNFALSIFIABLE when run through it:
    the literal is gone before the regex ever looks. Measured by re-inlining the real pre-fix
    expression into ``oc_runipd.initialize_run`` -- the shipped guard stayed GREEN.

    Raw source is the opposite error. ``runner_shared.initial_queue_status`` QUOTES the defective
    expression in its own docstring in order to record what was fixed, so a raw scan reports correct,
    fixed code as a live re-inlining. Measured at the 2026-09-18 merge: two FALSE POSITIVES.

    So: docstrings and comments are PROSE and go; every other literal is CODE and stays. A docstring
    is identified structurally, as a bare string EXPRESSION statement, rather than by position, so a
    module/class/function docstring at any nesting depth is removed while an assignment such as
    ``x = "queued"`` survives.
    """
    import ast

    try:
        tree = ast.parse(text)
    except (
        SyntaxError
    ):  # pragma: no cover - defensive; a broken module is a different failure
        return text

    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        # `body` is a LIST on modules/classes/functions, but a single expression on a `lambda` and an
        # `IfExp`, so it must be type-checked rather than merely truth-checked.
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for child in body:
            if (
                isinstance(child, ast.Expr)
                and isinstance(child.value, ast.Constant)
                and isinstance(child.value.value, str)
                and child.end_lineno is not None
            ):
                spans.append((child.lineno, child.end_lineno))

    drop = {ln for start, end in spans for ln in range(start, end + 1)}
    return "\n".join(
        ln
        for number, ln in enumerate(text.splitlines(), start=1)
        if number not in drop and not ln.lstrip().startswith("#")
    )


def _plan_text(
    id6: str,
    *,
    deps: str | None = _THREE_EDGE_VALUE,
    setid: str = "demo",
    order: int = 1,
    status: str = "approved",
    date: str = "2026-08-29",
) -> str:
    """A minimal plan whose metadata block the structural reader will accept."""
    lines = [
        f"# IPD: {id6}",
        "",
        f"- Date: {date}",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {setid} (the {setid} set)",
        f"- Order: {order}",
        f"- Id: {id6}",
    ]
    if deps is not None:
        lines.append(f"- Item-Dependencies: {deps}")
    lines += ["", "## Goal", "", "Demo.", ""]
    return "\n".join(lines)


def _write_plan(pending: Path, id6: str, order: int = 1, **kw) -> Path:
    path = pending / f"20260829-{kw.get('setid', 'demo')}-{order:02d}-{id6}-demo.ipd.md"
    path.write_text(_plan_text(id6, order=order, **kw), encoding="utf-8")
    return path


class TypedEdgeRoundTripTests(unittest.TestCase):
    """E-01: the canonical field is READ, and its qualifiers survive."""

    #: (case, the plan text to read, expected canonical edges, an error is expected?, why this row)
    STATEMENTS = (
        (
            "all three edge kinds at once",
            _plan_text("aaaaaa"),
            ["executed:a1b2c3", "exists:spec:d4e5f6", "state:backlog:done:g7h8j9"],
            False,
            "THE DEFECT ROW, and the positive case the whole file exists for: PRE-FIX THIS RETURNED "
            "`[]` for this exact statement, because both drivers matched a legacy "
            "`Dependencies:`/`Depends-on:` field no plan uses. Every negative row below is vacuous "
            "while this one is broken, since a reader that returned `[]` for everything satisfies all "
            "of them. THE QUALIFIERS ARE PART OF THE EXPECTATION (plan finding F4): keeping only bare "
            "id6 tokens would silently degrade `exists:spec:<id6>` into an untyped edge with "
            "different release semantics, and the satisfaction rule depends on the kind",
        ),
        (
            "the LEGACY field the fix deleted",
            "# IPD: aaaaaa\n\n- Id: aaaaaa\n- Dependencies: [5ahblp, pr2nd0]\n\n## Goal\n",
            [],
            False,
            "OQ-01 (resolved): the legacy field is REMOVED, not accepted alongside the canonical one. "
            "Accepting both would mean a plan could declare dependencies in a spelling no other "
            "surface (`aw check`, `aw ipd lint`) reads, so the runner would gate on edges the "
            "checkers cannot see. Note this is NOT an error: an unrecognized field is simply not a "
            "dependency statement",
        ),
        (
            "the literal `none`",
            _plan_text("aaaaaa", deps="none"),
            [],
            False,
            "the explicit no-dependencies declaration. It must be silent, not an error, or every "
            "independent plan in the tree fails preflight",
        ),
        (
            "the scaffold sentinel `unresolved`",
            _plan_text("aaaaaa", deps="unresolved"),
            [],
            False,
            "`aw ipd scaffold` writes this, so the READER must treat it as no edges. Whether it is a "
            "FINDING is the shared evaluator's call, not the reader's (8guhs0 OQ-02), which is why "
            "there is no error here even though `PreflightFailClosedTests` expects a finding for it",
        ),
        (
            "an EMPTY value",
            _plan_text("aaaaaa", deps=""),
            [],
            False,
            "a present-but-blank field. It must not raise and must not be read as a malformed "
            "statement, because that would refuse a whole run over a trailing-space edit",
        ),
        (
            "the field ABSENT entirely",
            _plan_text("aaaaaa", deps=None),
            [],
            False,
            "the MISSING case, which is deliberately indistinguishable from `none` AT THIS LAYER. The "
            "missing-vs-`none` decision belongs to the shared evaluator plus the cutover marker, and "
            "a runner-local rule here is exactly what 8guhs0 OQ-02 forbids",
        ),
        (
            "a malformed target id6",
            _plan_text("aaaaaa", deps="executed:TOOLONGID"),
            [],
            True,
            "a malformed statement must surface the shared parser's ERROR rather than silently "
            "yielding no edges. Silence here is the dangerous direction: the plan looks independent, "
            "so it runs with its prerequisite unmet",
        ),
    )

    def test_every_statement_shape_reads_the_same_on_both_drivers(self):
        """Every value the field can carry, through both drivers, against the SHARED parser.

        Six tests became one table. `test_both_drivers_yield_three_typed_edges`,
        `test_shared_parser_agreement_is_exact`, `test_qualifiers_are_not_flattened_to_bare_id6`,
        `test_legacy_field_no_longer_yields_dependencies`,
        `test_none_and_unresolved_and_absent_all_yield_no_edges`, and
        `test_malformed_statement_surfaces_the_shared_parser_error` all called
        `_read_item_dependencies` on one plan text and compared `(edges, error)`; only the text
        differed, which is a data row.

        THE MERGE IS STRICTLY STRONGER IN THREE WAYS. First, DRIVER became a column on every row:
        three of the six old tests called `oc_runipd` only, so `none`, `unresolved`, the absent field,
        the malformed statement, and the qualifier-preservation property were UNTESTED on agy - and a
        divergence between the two readers is the defect class this file exists for. Second, every row
        now additionally cross-checks against `ipd_schema.parse_item_dependencies` directly, which
        generalizes what the old `test_shared_parser_agreement_is_exact` did for one value only; an
        expectation that drifts from the shared grammar fails as a mismatch rather than quietly
        pinning a runner-local answer. Third, the qualifier check is applied to every returned edge on
        every row rather than to one fixture.
        """
        wrong = []
        for case, text, expected, expect_error, why in self.STATEMENTS:
            for driver, mod in _DRIVERS:
                edges, err = mod._read_item_dependencies(text)
                problems = []
                if edges != expected:
                    problems.append(f"read {edges!r}, expected {expected!r}")
                if expect_error and err is None:
                    problems.append(
                        "no parser error was surfaced; a malformed statement read as 'no "
                        "dependencies' lets a plan run with its prerequisite unmet"
                    )
                if not expect_error and err is not None:
                    problems.append(f"an unexpected parser error was surfaced: {err!r}")
                for tok in edges:
                    if ":" not in tok:
                        problems.append(
                            f"edge {tok!r} lost its qualifier (degraded to a bare id6), which "
                            "silently changes the edge's release semantics (F4)"
                        )
                if problems:
                    wrong.append(
                        f"  {case} on {driver}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )

        # THE SHARED-GRAMMAR CROSS-CHECK, applied to every row that carries a real value: the runner's
        # view must EQUAL `ipd_schema.parse_item_dependencies`, not merely be plausible. Without this
        # the table could pin a runner-local answer that drifts from what `aw check` sees.
        for case, text, expected, _expect_error, why in self.STATEMENTS:
            match = re.search(r"^- Item-Dependencies: ?(.*)$", text, re.M)
            if match is None:
                continue
            shared, _ready, shared_err = ipd_schema.parse_item_dependencies(
                match.group(1).strip()
            )
            shared_edges = [] if shared_err else [e.canonical() for e in shared]
            if shared_edges != expected:
                wrong.append(
                    f"  {case} (shared-grammar cross-check):\n"
                    f"    - `ipd_schema.parse_item_dependencies` yields {shared_edges!r} but this "
                    f"table expects {expected!r}\n"
                    "    this row exists because: the runner's view must EQUAL the authority "
                    "surface's. If they differ, this table is pinning a runner-local answer and the "
                    f"drift it was written to prevent has simply moved into the test\n"
                    f"    the row's own rule: {why}"
                )

        self.assertEqual(
            wrong,
            [],
            f"`_read_item_dependencies` is wrong for {len(wrong)} of "
            f"{len(self.STATEMENTS) * len(_DRIVERS)} (statement, driver) cells. READ THE SHAPE: if "
            "the THREE-EDGE row fails while the empty rows pass, that is the original defect back "
            "(the canonical field invisible, every queue entry frozen with `dependencies: []`, and "
            "ordering silently falling back to Set/Order, which spec 25kzda calls only a tiebreaker). "
            "If a row fails on ONE driver only, the two readers have diverged, which is what the "
            "anti-divergence guards at the bottom of this file exist to make impossible. If a "
            "SHARED-GRAMMAR cross-check fails, fix the TABLE and not the runner: the authority is "
            f"`ipd_schema.parse_item_dependencies`.\n" + "\n".join(wrong),
        )

    def test_the_typed_edges_survive_every_stage_of_the_freeze(self):
        """The plan RECORD and the frozen MANIFEST, both drivers, in one report.

        Two tests became one. Both wrote the same three-edge plan into a temp repo and asserted the
        same three canonical edges came back; they differed only in WHICH STAGE they read them from,
        which is a column. Keeping the stages adjacent is what makes the pipeline legible: the field
        is read once and then carried through `parse_plan_file` into `build_dynamic_manifest`, so a
        regression at the read shows up in BOTH stages while a regression in the freeze shows up in the
        manifest alone. Split across two tests that distinction was invisible.

        THE MANIFEST STAGE IS THE MEASURED ONE: real run records froze `dependencies: []` for plans
        that declared three edges, which is where the defect was actually observed.
        """
        expected = [
            "executed:a1b2c3",
            "exists:spec:d4e5f6",
            "state:backlog:done:g7h8j9",
        ]
        wrong = []
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            path = _write_plan(pending, "aaaaaa")
            for driver, mod in _DRIVERS:
                rec = mod.parse_plan_file(path, repo)
                if rec.dependencies != expected:
                    wrong.append(
                        f"  the plan RECORD on {driver}:\n"
                        f"    - carries {rec.dependencies!r}, expected {expected!r}\n"
                        "    this stage exists because: `parse_plan_file` is where the statement "
                        "becomes structured data. A failure HERE means the read is wrong, and the "
                        "manifest stage below will fail identically"
                    )
                if rec.dependency_error is not None:
                    wrong.append(
                        f"  the plan RECORD on {driver}:\n"
                        f"    - reports a dependency error on a VALID statement: "
                        f"{rec.dependency_error!r}"
                    )

                manifest = mod.build_dynamic_manifest(repo, mod.discover_plans(repo))
                got = manifest["plans"]["aaaaaa"]["dependencies"]
                if got != expected:
                    wrong.append(
                        f"  the FROZEN manifest on {driver}:\n"
                        f"    - carries {got!r}, expected {expected!r}\n"
                        "    this stage exists because: THIS IS WHERE THE DEFECT WAS MEASURED. Real "
                        "run records froze `dependencies: []` for plans declaring three edges, so "
                        "every ordering and gating decision for the whole run was made against an "
                        "empty graph. A failure here with the RECORD stage passing means the read "
                        "works and the FREEZE drops the edges"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} stage/driver cell(s) lost the typed edges. READ THEM TOGETHER: both stages "
            "failing on both drivers is the original defect (the canonical field invisible); the "
            "MANIFEST stage failing alone means the freeze drops what the read found, which is worse "
            "in practice because the plan file still looks correct while the run's frozen graph is "
            "empty; a failure on one DRIVER only means the two hosts freeze different graphs from one "
            f"tree.\n" + "\n".join(wrong),
        )


class DependencyTokenGrammarTests(unittest.TestCase):
    """The token grammar: what resolves, what normalizes, and what is REFUSED.

    ONE table replaces three tests. `test_typed_tokens_resolve_through_the_shared_grammar`,
    `test_bare_id6_normalizes_to_an_executed_edge`, and `test_illegal_tokens_are_rejected` each fed one
    token to `parse_dependency_token` and checked one outcome. The legal and ILLEGAL tokens belong in
    one table because the realistic failure is a widened or narrowed grammar, which moves tokens across
    the boundary: three tests report that as unrelated red lines, while the table shows which tokens
    crossed and in which direction, and the illegal rows are what stop the legal rows from being
    satisfied by a parser that accepts anything.
    """

    #: (token, expected (kind, target_type, status, id6) or None meaning it must be REFUSED, why)
    TOKENS = (
        (
            "executed:a1b2c3",
            ("executed", "ipd", None, "a1b2c3"),
            "the default edge kind and the default target type: an `executed:` edge with no type "
            "qualifier means an IPD, which is why the type is `ipd` and not None",
        ),
        (
            "exists:spec:d4e5f6",
            ("exists", "spec", None, "d4e5f6"),
            "a cross-type EXISTENCE edge. It carries no status because existence is the whole "
            "condition, and spec 2.9 releases it from current state without waiting",
        ),
        (
            "state:backlog:done:g7h8j9",
            ("state", "backlog", "done", "g7h8j9"),
            "the fully qualified form, and the only kind that carries a STATUS. All four fields are "
            "asserted because dropping the status silently converts it into an `exists:` edge, which "
            "releases on a backlog item that exists in ANY state",
        ),
        (
            "a1b2c3",
            ("executed", "ipd", None, "a1b2c3"),
            "a BARE id6 normalizes to `executed:`, because a legacy hand-written manifest JSON may "
            "still carry them and that is what they meant. Refusing them instead would make an older "
            "manifest unrunnable",
        ),
        (
            "",
            None,
            "the empty token. Accepting it would create an edge with no target, which can never be "
            "satisfied and would block its dependent forever",
        ),
        (
            "garbage",
            None,
            "a non-id6 word. `garbage` is 7 characters, so this is also the length check: an id6 is "
            "exactly 6 base36 characters",
        ),
        (
            "executed:",
            None,
            "a kind with NO target. This is the shape a string-formatting bug produces, and accepting "
            "it would turn a broken write into a permanently unsatisfiable edge",
        ),
        (
            "state:ipd:executed:a1b2c3",
            None,
            "a `state:` edge naming an IPD. Refused because IPD terminal state is what `executed:` "
            "already expresses; admitting a second spelling would give one condition two grammars "
            "free to drift apart",
        ),
        (
            "E-01",
            None,
            "an EXECUTION ITEM id, not a plan id. This is the most likely authoring mistake in a real "
            "plan (the same document is full of `E-01` references), and reading it as a dependency "
            "would silently make a plan depend on something that is not an artifact at all",
        ),
    )

    def test_every_token_resolves_or_is_refused_by_the_shared_grammar(self):
        wrong = []
        for token, expected, why in self.TOKENS:
            edge = oc_runipd.parse_dependency_token(token)
            problems = []
            if expected is None:
                if edge is not None:
                    problems.append(
                        f"was ACCEPTED as {(edge.kind, edge.target_type, edge.status, edge.id6)!r}; "
                        "it must be refused"
                    )
            elif edge is None:
                problems.append("was REFUSED; it must resolve")
            else:
                got = (edge.kind, edge.target_type, edge.status, edge.id6)
                if got != expected:
                    problems.append(f"resolved to {got!r}, expected {expected!r}")
            if problems:
                wrong.append(
                    f"  {token!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the token grammar is wrong for {len(wrong)} of {len(self.TOKENS)} tokens. READ THE "
            "DIRECTION: tokens that should be REFUSED being accepted is the permissive failure, and it "
            "produces edges that can never be satisfied, so a dependent waits forever or is "
            "`dependency-blocked` for a reason no operator can act on. Tokens that should RESOLVE "
            "being refused is the strict failure, and `dependency_status` fails closed on an "
            "unparseable token, so it BLOCKS a plan whose statement was perfectly valid. If several "
            "rows moved at once, the grammar was widened or narrowed rather than one case regressing; "
            f"the grammar has one definition, in `ipd_schema`.\n" + "\n".join(wrong),
        )


class EdgeSatisfactionTests(unittest.TestCase):
    """E-03: spec 25kzda 2.9 runtime satisfaction, every edge kind against every target state.

    ONE TABLE REPLACES NINE TESTS spanning three edge kinds, two target locations, and the
    fail-closed cases. Every one of them built the same `{"repo": ..., "queue": [...]}` state, called
    `dependency_status`, and compared `(satisfied, missing)`; they differed only in the edge token and
    in what existed in the queue or on disk, which is data.

    THE THREE DISTINCTIONS THAT WERE CLASSES-WORTH-OF-STRUCTURE ARE NOW COLUMNS, and each one states a
    property no single-mode test can:

    * EDGE KIND is a column, so the kinds' different TIMING is readable side by side rather than
      inferred from three separate tests: an `executed:` edge WAITS for an in-queue prerequisite, while
      `exists:` and `state:` are evaluated from current state and never wait (spec 2.9).
    * TARGET LOCATION is a column. An `executed:` edge whose target is IN THE QUEUE is answered from
      run state (is it verified in THIS run yet), and one whose target is only ON DISK is answered from
      the target's directory. Those are genuinely different code paths reaching one verdict, which is
      exactly where a divergence hides.
    * DRIVER is a column on every row. Four of the nine old tests called `oc_runipd` only, so the
      `exists:`/`state:`/fail-closed rules were UNTESTED on agy - and an agy-only copy of
      `dependency_status_detailed` really did ship and survive for months.

    THE POSITIVE AND NEGATIVE ROWS SHARE THE TABLE deliberately. `dependency_status` fails closed, so a
    function that returned `(False, edges)` for everything would satisfy every unsatisfied row on its
    own while blocking every runnable plan in the tree; the satisfied rows are what stop that passing.
    """

    #: (case, in-queue prerequisite status or None, on-disk fixture or None, the declared edge tokens,
    #: expected satisfied, expected `missing` list, why this row exists)
    #:
    #: An on-disk fixture is `("spec", <status>)` for a spec record or `(<plans bucket>, <status>)` for
    #: a plan file written into that bucket.
    SATISFACTION = (
        (
            "executed: whose target is IN THE QUEUE and still queued",
            "queued",
            None,
            ["executed:depaaa"],
            False,
            ["executed:depaaa"],
            "WAIT, NOT START. This is the only row where the right answer is to wait rather than to "
            "decide: the prerequisite is in THIS run and has not been verified yet, so its dependent "
            "must be held rather than declared dead (which is what the cascade does) or admitted",
        ),
        (
            "executed: an in-queue target reporting `executed` with NO plan on disk",
            "executed",
            None,
            ["executed:depaaa"],
            False,
            ["executed:depaaa"],
            "REVERSED 2026-09-19 when the in-queue shortcut was deleted (one authority: disk). This "
            "row used to be THE POSITIVE ROW for that shortcut, releasing 'with no disk read at all'. "
            "Its shape cannot occur after a real finalize: `aw ipd finalize` MOVES the plan into "
            "`executed/`, so a target genuinely reporting `executed` HAS a plan there and releases "
            "through the on-disk branch (proven by the `executed/` fixture row below). A run status of "
            "`executed` with no plan on disk means the transition did not happen, so refusing is the "
            "honest answer",
        ),
        (
            "executed: an in-queue `substantially-complete` target (THE 2026-09-19 INCIDENT)",
            "substantially-complete",
            None,
            ["executed:depaaa"],
            False,
            ["executed:depaaa"],
            "REVERSED 2026-09-19, and this row IS the incident. It used to assert that "
            "`substantially-complete` releases dependents 'exactly as `executed` does', on the "
            "reasoning that refusing 'would strand the rest of a Set behind an item that did its "
            "work'. MEASURED, THE OPPOSITE HAPPENED: that status means finalize did NOT run, so the "
            "plan is still in `pending/` and its lane was never merged. Run "
            "`run-20260919T194413Z-2056285` released `n4xq3l` against a tree holding NONE of "
            "`yaxr4i`'s work, which then refused and cascaded `dependency-blocked` to eight more "
            "items: 2h 10m and $55.02 for nothing integrated. Stranding a Set loudly is recoverable; "
            "building against absent work is not",
        ),
        (
            "executed: whose EXTERNAL target sits in `executed/`",
            None,
            ("executed", "approved"),
            ["executed:depaaa"],
            True,
            [],
            "the on-disk path, and the row that makes a PARTIALLY EXECUTED Set runnable. A resume, or "
            "a child executed alone, is the normal case rather than an edge case, so a dependent whose "
            "prerequisite already finished in an earlier session must run",
        ),
        (
            "executed: whose EXTERNAL target sits in `pending/`",
            None,
            ("pending", "approved"),
            ["executed:depaaa"],
            False,
            ["executed:depaaa"],
            "the counterpart: an `approved` plan has not been EXECUTED, so an execute turn must not "
            "build against it. This row is what keeps the row above from being read as 'any target on "
            "disk satisfies'",
        ),
        (
            "exists: whose spec target is PRESENT with a non-terminal status",
            None,
            ("spec", "draft"),
            ["exists:spec:d4e5f6"],
            True,
            [],
            "spec 2.9: an `exists:` edge is evaluated from current state and does NOT wait. The "
            "target's status is deliberately `draft`, the least advanced value, because existence is "
            "the whole condition - a plan that only needs the spec to EXIST must not be gated on the "
            "spec being approved",
        ),
        (
            "exists: whose spec target is ABSENT",
            None,
            None,
            ["exists:spec:d4e5f6"],
            False,
            ["exists:spec:d4e5f6"],
            "the same edge with nothing to find. It must refuse rather than release, or `exists:` "
            "would be a no-op that documents an intention and enforces nothing",
        ),
        (
            "state: whose spec target is a NEAR MISS on status",
            None,
            ("spec", "draft"),
            ["state:spec:approved:d4e5f6"],
            False,
            ["state:spec:approved:d4e5f6"],
            "a `state:` edge demands the EXACT status. `draft` is a real spec in a real state, so this "
            "is where an `in`/`>=` comparison or a status-ordering assumption would wrongly release",
        ),
        (
            "state: whose spec target holds the EXACT status",
            None,
            ("spec", "approved"),
            ["state:spec:approved:d4e5f6"],
            True,
            [],
            "the positive half of the same rule, releasing IMMEDIATELY without waiting. Together with "
            "the row above it pins `state:` as an equality test on current state rather than a wait",
        ),
        (
            "an UNPARSEABLE token",
            None,
            None,
            ["not-an-edge"],
            False,
            ["not-an-edge"],
            "FAIL CLOSED. A token the grammar rejects must never be read as 'no dependency': that "
            "would convert a typo in a plan into a silently ungated execution, which is the one "
            "failure mode nothing downstream can detect",
        ),
        (
            "NO declared edges at all",
            None,
            None,
            [],
            True,
            [],
            "the ordinary case for most plans, and the row that keeps fail-closed from becoming "
            "fail-always: an item with no statement is READY, and an empty `missing` list is what the "
            "dispatcher reads",
        ),
    )

    def test_every_edge_kind_and_target_state_gets_the_right_verdict(self):
        wrong = []
        for case, prereq, fixture, edges, expected, missing, why in self.SATISFACTION:
            for driver, mod in _DRIVERS:
                with tempfile.TemporaryDirectory() as t:
                    repo = Path(t) / "repo"
                    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
                    if fixture is not None:
                        kind, status = fixture
                        if kind == "spec":
                            specs = repo / ".aw" / "records" / "specs"
                            specs.mkdir(parents=True, exist_ok=True)
                            (
                                specs / "20260829-d4e5f6-01-d4e5f6-demo.spec.md"
                            ).write_text(
                                f"# Spec\n\n- Id: d4e5f6\n- Status: {status}\n",
                                encoding="utf-8",
                            )
                        else:
                            bucket = repo / ".aw" / "records" / "plans" / kind
                            bucket.mkdir(parents=True, exist_ok=True)
                            (bucket / "20260829-demo-01-depaaa-x.ipd.md").write_text(
                                _plan_text("depaaa", deps="none", status=status),
                                encoding="utf-8",
                            )

                    queue: list[dict] = []
                    if prereq is not None:
                        queue.append(
                            {
                                "id6": "depaaa",
                                "status": prereq,
                                "action": "execute",
                                "dependencies": [],
                                "position": 1,
                            }
                        )
                    item = {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": list(edges),
                        "position": len(queue) + 1,
                    }
                    queue.append(item)
                    state = {"repo": str(repo), "queue": queue}

                    got_satisfied, got_missing = mod.dependency_status(item, state)
                    problems = []
                    if got_satisfied is not expected:
                        problems.append(
                            f"satisfied={got_satisfied!r}, expected {expected!r}"
                        )
                    if got_missing != missing:
                        problems.append(
                            f"missing={got_missing!r}, expected {missing!r}; this list is what the "
                            "operator is shown as the reason the item did not start"
                        )
                    if problems:
                        wrong.append(
                            f"  {case} on {driver}:\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"spec 2.9 satisfaction is wrong for {len(wrong)} of "
            f"{len(self.SATISFACTION) * len(_DRIVERS)} (case, driver) cells. READ THE DIRECTION, "
            "because the two are not symmetric. WRONGLY SATISFIED is the dangerous one: an execute turn "
            "builds against a prerequisite that never ran, and nothing downstream notices. WRONGLY "
            "UNSATISFIED over-blocks, which is loud and recoverable, and is the direction the F8 "
            "hazard fails in (a raw token used as both a queue key and an id6 misses BOTH lookups). If "
            "every `exists:`/`state:` row fails while `executed:` rows pass, the non-waiting kinds are "
            "being routed through the in-queue path, which answers a different question. A failure on "
            "ONE driver only means the shared implementation was re-forked on that host.\n"
            + "\n".join(wrong),
        )

    def test_unconverted_typed_token_blocks_rather_than_admits(self):
        """Kept separate: it asserts a NEGATIVE about the implementation, not an edge verdict.

        Plan finding F8 pins the failure DIRECTION, and the assertion that carries it is that the raw
        token is NOT a queue key - a claim about the fixture and the hazard rather than about
        `dependency_status`'s answer. A wrong implementation using `"executed:depaaa"` as both a dict
        key and an id6 misses the queue lookup AND fails id6 resolution, so it OVER-blocks a satisfied
        dependent; a test written for the other direction would pass while the bug was live.
        """
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t) / "repo"
            (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
            # The prerequisite must be REALLY finalized on disk, because since 2026-09-19 the disk is
            # the only authority for an `executed:` edge (the in-queue run-status shortcut was
            # deleted). Without this fixture the dependent would refuse for the RIGHT reason - the
            # work is not in `executed/` - and this test would stop discriminating the F8 hazard it
            # exists to pin, which is about TOKEN PARSING rather than about readiness.
            executed_dir = repo / ".aw" / "records" / "plans" / "executed"
            executed_dir.mkdir(parents=True, exist_ok=True)
            (executed_dir / "20260919-f8haz-01-depaaa-prerequisite.ipd.md").write_text(
                "# IPD: prerequisite\n\n- Id: depaaa\n- Status: executed\n",
                encoding="utf-8",
            )
            state = {
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "depaaa",
                        "status": "executed",
                        "action": "execute",
                        "dependencies": [],
                        "position": 1,
                    },
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "action": "execute",
                        "dependencies": ["executed:depaaa"],
                        "position": 2,
                    },
                ],
            }
            # The naive lookup the fix must NOT do:
            by_id = {e["id6"]: e for e in state["queue"]}
            self.assertNotIn(
                "executed:depaaa",
                by_id,
                "the raw token is not a queue key; treating it as one is the F8 hazard",
            )
            satisfied, missing = oc_runipd.dependency_status(state["queue"][1], state)
            self.assertTrue(
                satisfied,
                "an unconverted token would BLOCK this satisfied dependent (F8 direction)",
            )
            self.assertEqual(missing, [])


class PreflightFailClosedTests(unittest.TestCase):
    """E-02: refuse BEFORE any host session, naming the shared rule; no runner-local policy."""

    def _repo(self, temp: Path) -> tuple[Path, Path]:
        repo = temp / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        return repo, pending

    #: (case, the plans to write as (id6, statement, order), a dupe fixture is needed?, rules that
    #: MUST be reported, a needle the refusal must carry or None, why this row exists)
    #:
    #: THE RULE NAMES ARE THE `ipd_schema` CONSTANTS HERE, NOT LITERALS, and that is the opposite of
    #: `test_ipd_lint.py`'s convention for a deliberate reason. There, the codes are a PUBLISHED
    #: interface (users read them in `aw ipd lint` output, the spec names them, workflows cite them) so
    #: a renumbering must fail. Here the property under test is DELEGATION: the runner must report
    #: exactly what the shared evaluator returned, so the two sides SHOULD move together, and pinning
    #: literals would convert a legitimate rename in `ipd_schema` into a runner test failure. What the
    #: literals would buy is covered by `check_engine`'s own suite, which owns those names.
    FAIL_CLOSED = (
        (
            "a malformed target id6",
            [("aaaaaa", "executed:NOTANID6", 1)],
            False,
            (ipd_schema.RULE_IPD_DEP_MALFORMED,),
            None,
            "an unparseable statement must refuse the run rather than be read as no dependencies, "
            "which would let the plan execute with its prerequisite unmet",
        ),
        (
            "an edge naming an id6 that does not exist",
            [("aaaaaa", "executed:zzzzzz", 1)],
            False,
            (ipd_schema.RULE_IPD_DEP_DANGLING,),
            None,
            "a DANGLING edge can never be satisfied, so admitting the run means the item waits forever "
            "or is `dependency-blocked` for a reason no operator can act on. Refusing before the run "
            "starts tells them at the only moment they can fix it",
        ),
        (
            "a plan depending on ITSELF",
            [("aaaaaa", "executed:aaaaaa", 1)],
            False,
            (ipd_schema.RULE_IPD_DEP_MALFORMED, ipd_schema.RULE_IPD_DEP_CYCLE),
            None,
            "BOTH rules fire on a self-edge, and both are asserted because it is genuinely both "
            "defects: the statement is malformed AND it forms a one-node cycle. THE OLD TEST ASSERTED "
            "ONLY `MALFORMED`, so a self-edge that stopped being reported as a cycle would have passed "
            "- verified against real output when tabulating",
        ),
        (
            "the scaffold sentinel `unresolved`",
            [("aaaaaa", "unresolved", 1)],
            False,
            (ipd_schema.RULE_IPD_DEP_UNRESOLVED,),
            None,
            "`aw ipd scaffold` writes this placeholder, and a plan still carrying it has not had its "
            "dependencies decided. The READER treats it as no edges (see `TypedEdgeRoundTripTests`); "
            "turning that into a FINDING is the evaluator's call, which is what this row proves is "
            "being delegated rather than re-decided",
        ),
        (
            "two plans depending on each other",
            [("aaaaaa", "executed:bbbbbb", 1), ("bbbbbb", "executed:aaaaaa", 2)],
            False,
            (ipd_schema.RULE_IPD_DEP_CYCLE,),
            None,
            "a cycle makes the queue unexecutable in ANY order, and it is the one dependency defect no "
            "amount of careful reading catches reliably. Note it reports ONLY the cycle rule here, "
            "unlike the self-edge row, since each statement is individually well formed",
        ),
        (
            "an AMBIGUOUS id6 resolving to two plans",
            [("aaaaaa", "executed:d4e5f6", 1)],
            True,
            (ipd_schema.RULE_IPD_DEP_AMBIGUOUS,),
            "ABORTED",
            "spec 2.10 maps ambiguity to the run-wide `fatal` identity class, so this row asserts a "
            "DIFFERENT refusal wording than every other: `ABORTED` rather than an ordinary refusal. "
            "The distinction is real - an ambiguous id6 means the runner cannot know WHICH artifact "
            "any edge refers to, so no per-item disposition is trustworthy",
        ),
        (
            "a VALID graph",
            [("aaaaaa", "none", 1), ("bbbbbb", "executed:aaaaaa", 2)],
            False,
            (),
            None,
            "THE POSITIVE ROW. Every refusal row above is vacuous while this one is broken, because a "
            "preflight that refused everything satisfies all of them - and it would block every run in "
            "the repository",
        ),
        (
            "a plan with NO dependency statement",
            [("aaaaaa", None, 1)],
            False,
            (),
            None,
            "THE SECOND POSITIVE ROW, and 8guhs0 OQ-02: the runner adds NO rule for the missing case. "
            "With no cutover marker set every existing plan is grandfathered, so a fieldless plan must "
            "be admitted; a runner-local refusal here would be STRICTER than `aw check` and "
            "`aw ipd lint`, recreating the divergence this work removed",
        ),
    )

    def test_every_fail_closed_class_refuses_and_names_the_shared_rule(self):
        """Each defect class, both drivers, with the findings list and the refusal as columns.

        SIX TESTS BECAME ONE TABLE. `test_each_fail_closed_class_refuses_and_names_the_shared_rule`
        (itself already a four-case dict), `test_cycle_is_refused`,
        `test_ambiguous_id6_is_reported_as_fatal`, `test_a_valid_graph_is_admitted`, and the
        no-statement half of `test_missing_statement_severity_follows_the_cutover_marker` all wrote
        plans into a temp repo, called `preflight_dependency_findings`, and then
        `enforce_dependency_preflight`; they differed only in the statements and the expected rule.

        THE MERGE IS STRICTLY STRONGER IN THREE WAYS. First, DRIVER is a column: every one of the old
        tests called `oc_runipd` ONLY, so no fail-closed class was tested on agy at all, even though
        both drivers are in this plan's Scope-Paths and a per-host divergence is the defect class this
        file exists for. Second, the self-edge row now asserts `CYCLE` as well as `MALFORMED`, where
        the old test accepted `MALFORMED` alone and would have passed if the cycle detection stopped
        seeing a one-node loop. Third, the POSITIVE rows sit in the same table as the refusals, so a
        preflight that refuses everything cannot satisfy the suite.

        THE `ABORTED` WORDING IS A COLUMN rather than a separate test, which is what makes the
        fatal-versus-ordinary distinction legible: it is the same function, the same call, and a
        deliberately different refusal.
        """
        wrong = []
        for case, plans, needs_dupe, rules, needle, why in self.FAIL_CLOSED:
            for driver, mod in _DRIVERS:
                with tempfile.TemporaryDirectory() as t:
                    repo, pending = self._repo(Path(t))
                    paths = [
                        _write_plan(pending, id6, order=order, deps=deps)
                        for id6, deps, order in plans
                    ]
                    if needs_dupe:
                        dup = repo / ".aw" / "records" / "plans" / "executed"
                        dup.mkdir(parents=True, exist_ok=True)
                        for n, sub in enumerate(("one", "two"), start=1):
                            (
                                dup / f"20260829-dupe-0{n}-d4e5f6-{sub}.ipd.md"
                            ).write_text(
                                _plan_text(
                                    "d4e5f6", deps="none", setid="dupe", order=n
                                ),
                                encoding="utf-8",
                            )

                    findings = mod.preflight_dependency_findings(repo, paths)
                    reported = sorted({f[1] for f in findings})
                    problems = []
                    for rule in rules:
                        if rule not in reported:
                            problems.append(
                                f"the finding {rule!r} was NOT reported; reported: {reported}"
                            )
                    if not rules and findings:
                        problems.append(
                            f"a legal graph produced findings: {reported}. This refuses a run that "
                            "must be admitted"
                        )

                    try:
                        admitted = mod.enforce_dependency_preflight(repo, paths)
                    except mod.DriverError as exc:
                        message = str(exc)
                        if not rules:
                            problems.append(
                                f"the run was REFUSED though the graph is legal: {message[:200]!r}"
                            )
                        else:
                            for rule in rules:
                                if rule not in message and needle is None:
                                    problems.append(
                                        f"the refusal does not name {rule!r}, so the operator is not "
                                        f"told which rule fired: {message[:200]!r}"
                                    )
                            if needle is not None and needle not in message:
                                problems.append(
                                    f"the refusal does not carry {needle!r}: {message[:200]!r}"
                                )
                    else:
                        if rules:
                            problems.append(
                                "`enforce_dependency_preflight` did NOT raise, so a defect the "
                                "findings sweep reported was allowed to start a run"
                            )
                        elif admitted != []:
                            problems.append(
                                f"a legal graph was admitted but returned {admitted!r}, expected []"
                            )

                    if problems:
                        wrong.append(
                            f"  {case} on {driver}:\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"the dependency preflight is wrong for {len(wrong)} of "
            f"{len(self.FAIL_CLOSED) * len(_DRIVERS)} (case, driver) cells. READ THE DIRECTION: a "
            "REFUSAL THAT STOPPED FIRING is the severe one, because the run then starts and spends "
            "agent turns on a graph that cannot be executed; a POSITIVE ROW that started failing "
            "blocks legitimate work, and if it is the no-statement row specifically, a runner-local "
            "missing-statement rule has appeared and the runner is now stricter than `aw check` "
            "(8guhs0 OQ-02 forbids exactly that). If several rows regress at once the delegation "
            "itself broke rather than one rule; the whole judgement belongs to "
            f"`check_engine.evaluate_ipd_dependencies`.\n" + "\n".join(wrong),
        )

    def test_the_fatal_rule_set_is_what_makes_ambiguity_abort(self):
        """Kept separate: the MEMBERSHIP claim behind the `ABORTED` row above.

        The table asserts the OBSERVABLE difference (a different refusal wording); this asserts the
        mechanism (`DEPENDENCY_FATAL_RULES` contains the ambiguity rule and, so that the set is not
        silently widened, contains nothing else). Merging it into a row would mix a structural claim
        about a constant into a table of per-graph outcomes.
        """
        self.assertEqual(
            set(oc_runipd.DEPENDENCY_FATAL_RULES),
            {ipd_schema.RULE_IPD_DEP_AMBIGUOUS},
            "spec 2.10 makes IDENTITY ambiguity, and only that, the run-wide fatal class. Widening "
            "this set converts an item-scoped refusal into a run-wide abort; narrowing it lets an "
            "ambiguous id6 produce per-item dispositions that cannot be trusted, since the runner "
            "does not know which artifact any edge referred to",
        )
        self.assertIs(
            agy_runipd.DEPENDENCY_FATAL_RULES,
            oc_runipd.DEPENDENCY_FATAL_RULES,
            "and both drivers must share the SAME object, or one host can abort where the other "
            "continues",
        )

    def test_the_findings_are_the_shared_evaluators_verbatim_on_both_drivers(self):
        """8guhs0 OQ-02: the runner adds NO rule of its own; it surfaces the evaluator's answer.

        Two claims, both strengthened relative to what they replace. The AGREEMENT half is the old
        `test_missing_statement_is_delegated_not_decided_locally`, now run on BOTH drivers (it called
        `oc_runipd` only, so agy adding a local rule was invisible). The SENTINEL half is new and is
        what makes the agreement meaningful: the evaluator is replaced by one returning a diagnostic no
        runner could invent, and both drivers must report exactly that. A runner carrying its own rules
        would report its own findings alongside, or instead of, the sentinel.
        """
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps=None)
            shared = check_engine.evaluate_ipd_dependencies(
                repo,
                phase="pre-execution",
                plans=[(path, path.read_text(encoding="utf-8"))],
            )
            for driver, mod in _DRIVERS:
                with self.subTest(driver=driver, half="agreement"):
                    runner = mod.preflight_dependency_findings(repo, [path])
                    self.assertEqual(
                        [(f[1], f[2]) for f in runner],
                        [(d.rule, d.detail) for d in shared],
                        "the runner must report EXACTLY what the shared evaluator returns",
                    )

            class _Sentinel:
                location = "sentinel-location"
                rule = "check.sentinel-rule"
                detail = "a sentinel detail no runner could invent"

            for driver, mod in _DRIVERS:
                with self.subTest(driver=driver, half="sentinel"):
                    with mock.patch.object(
                        check_engine,
                        "evaluate_ipd_dependencies",
                        lambda *a, **k: [_Sentinel()],
                    ):
                        self.assertEqual(
                            mod.preflight_dependency_findings(repo, [path]),
                            [
                                (
                                    "sentinel-location",
                                    "check.sentinel-rule",
                                    "a sentinel detail no runner could invent",
                                )
                            ],
                            "the runner must surface the EVALUATOR's diagnostics and add none of its "
                            "own. Extra findings here are a runner-local rule; a missing sentinel "
                            "means the evaluator is not being called at all and the runner is "
                            "deciding for itself",
                        )

    def test_missing_statement_severity_follows_the_cutover_marker(self):
        """With no marker set, everything is grandfathered; setting it makes the field mandatory.

        Kept as a BEFORE/AFTER pair rather than tabulated: the whole claim is that the SAME repository
        and the SAME plan produce different answers once the marker is written, which needs the two
        states in sequence against one fixture. A table of independent rows cannot express a transition.

        This is the OQ-02 consequence demonstrated rather than argued: the behavior changes with the
        MARKER, with no change in the runner. DRIVER is a column here too, since a host that consulted
        the marker itself would keep its own answer.
        """
        from agent_workflows import config as _config

        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps=None, date="2026-08-29")
            self.assertIsNone(
                _config.dependency_cutover_date(repo), "no marker in a fresh repo"
            )
            for driver, mod in _DRIVERS:
                with self.subTest(driver=driver, marker="absent"):
                    self.assertEqual(
                        mod.preflight_dependency_findings(repo, [path]),
                        [],
                        "grandfathered: an absent marker must never mass-fail the corpus",
                    )
            marker = repo / ".aw" / "config" / "project.json"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                json.dumps({_config.DEPENDENCY_SCHEMA_CUTOVER_KEY: "2026-01-01"}),
                encoding="utf-8",
            )
            self.assertEqual(_config.dependency_cutover_date(repo), "2026-01-01")
            for driver, mod in _DRIVERS:
                with self.subTest(driver=driver, marker="set"):
                    self.assertIn(
                        ipd_schema.RULE_IPD_DEP_MISSING,
                        [f[1] for f in mod.preflight_dependency_findings(repo, [path])],
                        "a POST-cutover fieldless plan starts failing automatically, with no change "
                        "in either runner",
                    )

    def test_no_runner_local_missing_statement_branch_exists(self):
        """The diff must contain no runner-local rule for the missing case (OQ-02)."""
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                code = _code_only(path.read_text(encoding="utf-8"))
                self.assertNotIn(
                    ipd_schema.RULE_IPD_DEP_MISSING,
                    code,
                    "the runner must not name the missing-statement rule in CODE; "
                    "it delegates to the shared evaluator",
                )
                self.assertNotIn(
                    "dependency_cutover_date",
                    code,
                    "the runner must not consult the cutover marker itself; that is the "
                    "shared evaluator's input (OQ-02)",
                )

    def test_preflight_refuses_before_any_session_starts(self):
        """The refusal must precede the run directory, hence any session log or launch event."""
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            _write_plan(pending, "aaaaaa", deps="executed:zzzzzz")
            runs_root = oc_runipd.state_root(repo)
            args = _StartArgs(repo=str(repo), selectors=["aaaaaa"])
            with self.assertRaises(oc_runipd.DriverError) as ctx:
                oc_runipd.initialize_run(args)
            self.assertIn(ipd_schema.RULE_IPD_DEP_DANGLING, str(ctx.exception))
            self.assertFalse(
                runs_root.exists() and any(runs_root.iterdir()),
                "no run directory (hence no session log/prompt) may exist after a refusal",
            )

    def test_agy_preflight_raises_a_driver_error_agy_main_can_catch(self):
        """agy's `main` catches `agy_runipd.DriverError`; a leaked oc error would traceback.

        THIS ASSERTION WAS DELIBERATELY INVERTED by rununify Order 02 (`818uru` E-03), and the
        inversion is the POINT rather than a weakening. This test previously asserted
        `assertIsNot(agy_runipd.DriverError, oc_runipd.DriverError)`, pinning the two-distinct-classes
        state that `818uru` F-3 identified as a LATENT BUG: because the classes differed, a refusal
        raised by the shared (oc-owned) preflight was invisible to `except DriverError` here, and
        `agy_runipd` carried a hand-written wrapper whose only job was to translate one into the
        other. There is now ONE `DriverError` in the package.

        The property this test actually exists to protect is UNCHANGED and now holds more strongly:
        the refusal is still raised, and it is still catchable as `agy_runipd.DriverError` by agy's
        `main` - now by class identity rather than by a translation step that could be forgotten.
        """
        with tempfile.TemporaryDirectory() as t:
            repo, pending = self._repo(Path(t))
            path = _write_plan(pending, "aaaaaa", deps="executed:zzzzzz")
            self.assertIs(agy_runipd.DriverError, oc_runipd.DriverError)
            with self.assertRaises(agy_runipd.DriverError):
                agy_runipd.enforce_dependency_preflight(repo, [path])
            # And the half that made the old wrapper necessary: an error raised on the OC side is
            # now caught by an `except` naming AGY's class, which was previously impossible.
            with self.assertRaises(agy_runipd.DriverError):
                raise oc_runipd.DriverError("raised from the opencode side")


def _StartArgs(repo: str, selectors: list[str]) -> argparse.Namespace:
    """The `initialize_run` argument surface (`initialize_run` reads it with `getattr`)."""
    return argparse.Namespace(
        repo=repo,
        selectors=selectors,
        manifest=None,
        runbook=None,
        session=None,
        run_id=None,
        full_auto=False,
        opencode="opencode",
        model=None,
        agent=None,
        auto=True,
        output_mode="clean",
        stall_timeout=600.0,
        validate=False,
        self_finalize=True,
        isolate_worktree=False,
        max_items_per_session=4,
    )


class OrderingAndCascadeTests(unittest.TestCase):
    """E-04: declared edges authoritative; Set/Order a tiebreaker; `dependency-blocked` cascade."""

    def _item(
        self, id6, *, deps=None, setid="demo", order=1, position=1, status="queued"
    ):
        return {
            "id6": id6,
            "setid": setid,
            "order": order,
            "position": position,
            "status": status,
            "action": "execute",
            "dependencies": list(deps or []),
        }

    #: (case, the queue as (id6, deps, setid, order, position) rows, expected id6 order after sorting,
    #: why this row exists)
    ORDERING = (
        (
            "a declared edge DISAGREEING with Set/Order",
            (
                ("depend", ["executed:prereq"], "demo", 1, 1),
                ("prereq", [], "demo", 9, 2),
            ),
            ["prereq", "depend"],
            "THE LOAD-BEARING ROW: the prerequisite has the HIGHER Order and the LATER position, so "
            "every tiebreaker says depend-first and only the declared edge says otherwise. Spec 25kzda "
            "calls Set/Order a TIEBREAKER, which means `dependency_depth` must stay FIRST in the key; "
            "if it does not, a dependent is dispatched before the work it consumes",
        ),
        (
            "two equally-ready nodes with different positions",
            (
                ("bbbbbb", [], "demo", 2, 1),
                ("aaaaaa", [], "demo", 1, 2),
            ),
            ["bbbbbb", "aaaaaa"],
            "DELIBERATELY INVERTED by runorder `prpipy`; a CONTRACT CHANGE, not a broken row. It used "
            "to expect `[aaaaaa, bbbbbb]` ('Order 1 precedes Order 2 on a tie'), pinning 8guhs0's key "
            "`(depth, setid, order, id6, position)`. `prpipy` moved `position` from LAST to "
            "immediately after `depth` on the maintainer's 2026-09-01 ruling, because ranking it last "
            "recorded the operator's requested order and then discarded it (run "
            "`run-20260901T042331Z-118022` inverted `aw oc run m73aet 6lu3rq` on Set id alone). So "
            "among equally-ready nodes the REQUESTED order decides. Inverted rather than deleted, "
            "following this repo's pin-then-deliberately-change convention",
        ),
        (
            "two equally-ready nodes at the SAME position",
            (
                ("bbbbbb", [], "demo", 2, 1),
                ("aaaaaa", [], "demo", 1, 1),
            ),
            ["aaaaaa", "bbbbbb"],
            "`Order` did not stop mattering; it dropped ONE RANK. With the requested order tied, Set "
            "then Order decides, so Order 1 precedes Order 2. This row is what keeps the row above "
            "from being read as 'Order is dead'",
        ),
    )

    def test_the_sort_key_ranks_every_ordering_signal_correctly(self):
        """All three ordering signals, both drivers, with the position-stability check on every row.

        FOUR TESTS BECAME ONE TABLE. `test_declared_edges_beat_set_order_when_the_two_disagree`,
        `test_request_order_outranks_set_order_among_equally_ready_nodes`,
        `test_set_order_still_breaks_ties_when_the_request_order_ties`, and
        `test_position_is_never_renumbered_by_ordering` each built a two-item queue, sorted it by
        `queue_sort_key`, and compared one id6 list; only the queue differed.

        WHY THE TABLE BEATS THE FOUR: the subject is a single sort KEY, i.e. a PRECEDENCE ORDER among
        signals, and the realistic regression is a reordering of that key rather than one comparison
        breaking. A reordering moves several rows at once, and WHICH rows move is what identifies the
        change: all three failing means the key was rebuilt, the second and third failing together
        means `position` and `order` swapped ranks, and the first failing alone means `depth` is no
        longer first, which is the only one of the three that can dispatch work before its prerequisite.
        Four separate tests report a reordering as four unrelated red lines each showing one inverted
        pair.

        THE POSITION-STABILITY CHECK IS NOW ON EVERY ROW, where it used to be one test over one queue.
        `position` is a stable IDENTITY (outcome, prompt, and session filenames key on it), so sorting
        must never renumber it; asserting that after each sort is strictly stronger and costs nothing.
        """
        wrong = []
        for case, rows, expected, why in self.ORDERING:
            for driver, mod in _DRIVERS:
                queue = [
                    self._item(
                        id6, deps=deps, setid=setid, order=order, position=position
                    )
                    for id6, deps, setid, order, position in rows
                ]
                by_id = {i["id6"]: i for i in queue}
                before = [i["position"] for i in queue]
                ordered = [
                    i["id6"]
                    for i in sorted(queue, key=lambda it: mod.queue_sort_key(it, by_id))
                ]
                problems = []
                if ordered != expected:
                    problems.append(f"sorted to {ordered}, expected {expected}")
                if [i["position"] for i in queue] != before:
                    problems.append(
                        f"sorting RENUMBERED `position` from {before} to "
                        f"{[i['position'] for i in queue]}; it is a stable identity that outcome, "
                        "prompt, and session filenames key on"
                    )
                if problems:
                    wrong.append(
                        f"  {case} on {driver}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"the queue sort key is wrong for {len(wrong)} of "
            f"{len(self.ORDERING) * len(_DRIVERS)} (case, driver) cells. READ WHICH ROWS MOVED: the "
            "key is a PRECEDENCE ORDER (`depth` first, then `position`, then Set, then `order`), so a "
            "reordering moves several rows at once. ALL THREE failing means the key was rebuilt. The "
            "LAST TWO failing together means `position` and `order` swapped ranks, which silently "
            "discards the operator's requested order (measured in run "
            "`run-20260901T042331Z-118022`). THE FIRST failing ALONE is the severe one: `depth` is no "
            "longer first, so a dependent can be dispatched before the work it consumes, and no later "
            f"tiebreaker can recover that.\n" + "\n".join(wrong),
        )

    #: (case, the queue rows, expected {id6: depth}, why this row exists)
    DEPTHS = (
        (
            "a three-link in-queue chain plus two external leaves",
            (
                ("aaaaaa", [], 1),
                ("bbbbbb", ["executed:aaaaaa"], 2),
                ("cccccc", ["executed:bbbbbb"], 3),
                ("dddddd", ["exists:spec:d4e5f6"], 4),
                ("eeeeee", ["executed:zzzzzz"], 5),
            ),
            {
                "aaaaaa": 0,
                "bbbbbb": 1,
                "cccccc": 2,
                "dddddd": 0,
                "eeeeee": 0,
            },
            "depth counts IN-QUEUE IPD edges and nothing else. The chain gives 0/1/2, which is what "
            "orders the queue; `dddddd`'s spec leaf and `eeeeee`'s external plan are NOT queue nodes, "
            "so they are depth 0 and dispatch immediately. Counting them would push items behind "
            "targets this run will never execute, and the run would deadlock waiting on work outside "
            "its own queue",
        ),
        (
            "a two-node CYCLE",
            (
                ("aaaaaa", ["executed:bbbbbb"], 1),
                ("bbbbbb", ["executed:aaaaaa"], 2),
            ),
            {"aaaaaa": 2, "bbbbbb": 2},
            "CYCLE SAFETY. A cycle is refused by the preflight, but `dependency_depth` must still "
            "TERMINATE on one, because it also runs on frozen state from an older run and on a queue "
            "the preflight did not build. The exact values matter less than the function returning at "
            "all: an unbounded walk here hangs queue construction with no output, which is the worst "
            "failure shape available",
        ),
    )

    def test_dependency_depth_counts_only_in_queue_ipd_edges(self):
        """Depth for every node of both graphs, on both drivers.

        Two tests became one. `test_dependency_depth_counts_only_in_queue_ipd_edges` and
        `test_dependency_depth_is_cycle_safe` both built a queue and asked for depths; only the graph
        differed. Kept SEPARATE from the sort-key table above even though depth feeds that key,
        because these rows assert an integer per node while those assert an ordering over a queue - and
        depth is the input that makes the sort table's first row work, so a reader wants it to fail with
        its own name.

        THE CYCLE ROW NOW PINS ITS VALUES rather than only asserting `isinstance(..., int)`, which is
        what tabulating bought: the old test accepted any integer, so a cycle silently returning 0 (and
        thereby dispatching a cyclic pair immediately) would have passed.
        """
        wrong = []
        for case, rows, expected, why in self.DEPTHS:
            for driver, mod in _DRIVERS:
                queue = [
                    self._item(id6, deps=deps, position=position)
                    for id6, deps, position in rows
                ]
                by_id = {i["id6"]: i for i in queue}
                got = {id6: mod.dependency_depth(id6, by_id) for id6 in expected}
                if got != expected:
                    wrong.append(
                        f"  {case} on {driver}:\n"
                        f"    - depths {got} , expected {expected}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"`dependency_depth` is wrong for {len(wrong)} of {len(self.DEPTHS) * len(_DRIVERS)} "
            "(graph, driver) cells. READ WHICH NODES MOVED: if the EXTERNAL leaves gained depth, "
            "non-queue targets are being counted as queue nodes and items will wait on work this run "
            "will never do. If the CHAIN collapsed to 0, the sort key's first component carries no "
            "information and ordering silently falls back to position/Set/Order. If the cycle row "
            "HANGS rather than fails, the walk lost its visited set, which wedges queue construction "
            f"with no output at all.\n" + "\n".join(wrong),
        )

    def test_missing_order_key_still_sorts(self):
        """Kept separate: a BACKWARD-COMPATIBILITY claim about a malformed item, not an ordering.

        An older run directory frozen before E-04 has no `order` key at all, so resume must not crash.
        There is no expected ordering to assert (one item), and the row shape of the tables above
        requires every field; the claim is only that the key is constructible.
        """
        legacy = {
            "id6": "aaaaaa",
            "setid": "demo",
            "position": 1,
            "status": "queued",
            "action": "execute",
            "dependencies": [],
        }
        by_id = {"aaaaaa": legacy}
        for driver, mod in _DRIVERS:
            with self.subTest(driver=driver):
                self.assertIsInstance(
                    mod.queue_sort_key(legacy, by_id),
                    tuple,
                    "a run frozen before E-04 carries no `order` key; raising here makes an existing "
                    "run directory unresumable, which is state an operator cannot recover by hand",
                )

    #: (case, prerequisite status as frozen on the queue entry, the dependents' ACTION, expected
    #: blocked id6 set, why this row exists)
    #:
    #: Every row uses the same shape: one prerequisite plus a TWO-LINK chain of dependents
    #: (`child1` depends on the prerequisite, `child2` on `child1`), so each row also exercises the
    #: fixed point over reverse edges rather than only the direct dependent.
    CASCADE = (
        (
            "a prerequisite that FAILED",
            "failed-safely",
            "execute",
            {"child1", "child2"},
            "the base case the cascade exists for: work that consumes a failed prerequisite must be "
            "marked rather than attempted. BOTH children are expected, which is what proves the "
            "cascade reaches a FIXED POINT over reverse edges instead of marking only the direct "
            "dependent",
        ),
        (
            "a prerequisite that EXECUTED",
            "executed",
            "execute",
            set(),
            "THE MEASURED DEFECT (13 runs; `run-20260917T033138Z-557584` is the worst). Both hosts "
            "built the queue entry's status from an allowlist with no `executed` arm, so a plan "
            "sitting in `executed/` was relabeled `reviewed` - in `TERMINAL_STATES` but NOT in "
            "`EXECUTION_SUCCESS_STATES` - and the cascade declared the executed parent a dead "
            "prerequisite: nine mislabeled parents killed six approved children and two orchestrators "
            "at queue build, before any agent turn, for zero tokens. A partially executed Set is a "
            "NORMAL state (a resume, a child run alone, a Set spread over sessions), so this is the "
            "common case",
        ),
        (
            "a prerequisite that is SUBSTANTIALLY COMPLETE",
            "substantially-complete",
            "execute",
            set(),
            "the second success disposition. It must release dependents exactly as `executed` does, or "
            "an item that did its work still strands the rest of its Set",
        ),
        (
            "a merely REVIEWED prerequisite, consumed by a REVIEW turn",
            "reviewed",
            "review",
            set(),
            "MEASURED FAILURE (run `run-20260904T042705Z-1025943`): a 6-item all-`review` run of the "
            "`wslayout` Set reviewed Orders 00 and 01, and the instant Order 01 reached `reviewed` the "
            "cascade marked Orders 02-05 `dependency-blocked` with 'prerequisite reached a non-success "
            "terminal state', making a review-mode Set run impossible to complete. The cascade "
            "hardcoded `EXECUTION_SUCCESS_STATES` while `dependency_status_detailed` returned "
            "satisfied=True for the same items: two functions, opposite answers, and the cascade won "
            "because it runs after each item. Reviewing a child that imports a module the previous "
            "child creates needs only that the previous child was REVIEWED, since a review pass writes "
            "and imports no code",
        ),
        (
            "an APPROVED prerequisite, consumed by a REVIEW turn",
            "approved",
            "review",
            set(),
            "the same rule one status further along. `approved` is sanctioned for a review-consumed "
            "edge by spec 2.9, and asserting it separately from `reviewed` is what shows the review "
            "bar is a SET of statuses rather than a special case for one",
        ),
        (
            "a merely REVIEWED prerequisite, consumed by an EXECUTE turn",
            "reviewed",
            "execute",
            {"child1", "child2"},
            "THE COUNTERPART that keeps the two review rows honest. `reviewed` is NOT enough to "
            "execute against: if this ever passes through, an execute pass builds on a prerequisite "
            "whose code was never written. ACTION is the whole reason this is a column - the same "
            "prerequisite status must give opposite answers for the two actions",
        ),
        (
            "a FAILED prerequisite, consumed by a REVIEW turn",
            "failed-safely",
            "review",
            {"child1", "child2"},
            "WRONG EXPECTATION FOUND WHEN TABULATING, and the table was fixed rather than the source: "
            "this row (and the two mapped rows below) first expected `{child1}` alone, carried over "
            "from tests whose fixture had only ONE dependent. On the shared two-link chain the cascade "
            "correctly reaches `child2` as well, since a blocked item is itself not a success. The "
            "measured answer is the right one and the rows now assert it. "
            "The rule: the review relaxation is bounded - it admits NON-SUCCESS-BUT-PROGRESSING "
            "statuses, not "
            "FAILURE. Without this row the review rows above could be satisfied by a cascade that "
            "never blocks a review turn at all",
        ),
        (
            "a `superseded` prerequisite (mapped to `reviewed` on the queue)",
            None,  # derived below via `initial_queue_status("superseded")`
            "execute",
            {"child1", "child2"},
            "THE NARROWNESS OF THE `executed` FIX IS THE POINT, and it is a measured constraint rather "
            "than conservatism. A status is only safe to write onto a queue entry if BOTH vocabularies "
            "admit it: `TERMINAL_STATES` (or the cascade cannot act on it) and "
            "`runner_shutdown.KNOWN_ITEM_STATUSES` (or the R3 ledger-coherence check calls the run "
            "undefined and REFUSES ITS OWN RESUME). `superseded` is in NEITHER, so preserving it would "
            "trade this cascade bug for a resume-refusing ledger. It falls back to `reviewed`, which "
            "already produces the right OUTCOME, since a non-success status blocks a dependent either "
            "way - and THE OUTCOME is what this row asserts, whatever the name",
        ),
        (
            "a `not-executed` prerequisite (mapped to `reviewed` on the queue)",
            None,  # derived below via `initial_queue_status("not-executed")`
            "execute",
            {"child1", "child2"},
            "the sibling terminal disposition, for the same reason. Asserted separately so a fix that "
            "started preserving one of the two names is caught by the one it broke",
        ),
    )

    def test_the_cascade_blocks_exactly_the_right_dependents(self):
        """Every prerequisite disposition crossed with the consuming ACTION, on both drivers.

        SEVEN TESTS BECAME ONE TABLE. `test_cascade_marks_only_dependents_of_a_failed_item`,
        `test_cascade_does_not_block_on_a_successful_prerequisite`,
        `test_review_action_is_not_cascade_blocked_by_a_reviewed_prerequisite`,
        `test_execute_action_still_blocks_on_a_merely_reviewed_prerequisite`,
        `test_already_executed_prerequisite_does_not_block_its_dependent`,
        `test_only_executed_is_preserved_and_the_rest_still_block`, and
        `test_cascade_and_edge_satisfied_agree_on_the_success_bar` all built one prerequisite plus a
        dependent chain, called `cascade_dependency_blocked`, and compared which items got blocked.

        ACTION IS THE COLUMN THAT MATTERS, and it is the reason this must be one table rather than a
        review class and an execute class. The two measured outages in this file are both cases of the
        SAME prerequisite status giving the wrong answer for ONE action: `reviewed` must release a
        review turn and block an execute turn. Split into per-action classes, a fix that relaxed BOTH
        (the obvious way to fix the review outage) would have turned the execute class red in a
        different file-region, and the relationship between the two answers - which is the actual
        contract - would appear nowhere.

        THE ANTI-DIVERGENCE INVARIANT IS ASSERTED ON EVERY ROW, not in a separate test: if
        `dependency_status` says an edge is satisfied, the cascade must NOT declare the item dead. That
        disagreement between two functions IS the 2026-09-04 outage (`dependency_status_detailed`
        returned satisfied=True while the cascade blocked the same items, and the cascade won because it
        runs after each item), so checking it per row rather than over a hand-picked matrix is what
        makes it hold for every case in the table.
        """
        wrong = []
        for case, prereq_status, action, expected_blocked, why in self.CASCADE:
            if prereq_status is None:
                # The mapped rows: the point is the OUTCOME under whatever name the mapping produces.
                mapped = "superseded" if "superseded" in case else "not-executed"
                status = runner_shared.initial_queue_status(mapped)
            else:
                status = prereq_status
            for driver, mod in _DRIVERS:
                queue = [
                    self._item("prereq", position=1, status=status),
                    self._item("child1", deps=["executed:prereq"], position=2),
                    self._item("child2", deps=["executed:child1"], position=3),
                ]
                for entry in queue[1:]:
                    entry["action"] = action
                state = {"repo": "/nonexistent", "queue": queue}

                # Asked BEFORE the cascade runs, since the cascade mutates the statuses it reads.
                edge_ok, _missing = mod.dependency_status(queue[1], state)
                blocked = mod.cascade_dependency_blocked(state)
                got = {b["id6"] for b in blocked}

                problems = []
                if got != expected_blocked:
                    problems.append(
                        f"blocked {sorted(got)}, expected {sorted(expected_blocked)}"
                    )
                for entry in queue[1:]:
                    want = (
                        "dependency-blocked"
                        if entry["id6"] in expected_blocked
                        else "queued"
                    )
                    if entry["status"] != want:
                        problems.append(
                            f"{entry['id6']}'s status is {entry['status']!r}, expected {want!r}"
                        )
                if edge_ok and got:
                    problems.append(
                        f"THE ANTI-DIVERGENCE INVARIANT BROKE: `dependency_status` called child1 "
                        f"READY while the cascade killed {sorted(got)}. Two functions, opposite "
                        "answers, and the cascade wins because it runs after each item - this is "
                        "exactly the 2026-09-04 outage"
                    )
                if problems:
                    wrong.append(
                        f"  {case}, consumed by an action of {action!r} (queue status "
                        f"{status!r}) on {driver}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"the cascade is wrong for {len(wrong)} of {len(self.CASCADE) * len(_DRIVERS)} "
            "(disposition x action, driver) cells. READ THE DIRECTION, because the two are not "
            "symmetric. OVER-BLOCKING is what both measured outages were: it costs an entire Set run "
            "at queue build, before any agent turn and for zero tokens, and the operator sees healthy "
            "plans marked `dependency-blocked` for no reason they can act on. UNDER-BLOCKING is worse "
            "per item but rarer: an execute turn builds against a prerequisite whose code was never "
            "written. If the REVIEW rows fail while the EXECUTE rows pass, the cascade is hardcoding "
            "`EXECUTION_SUCCESS_STATES` again and a review-mode Set run cannot complete. If BOTH the "
            "review AND the execute `reviewed` rows pass-through, the fix was over-applied and the "
            "execute bar is gone. If the ANTI-DIVERGENCE line appears, fix the disagreement and not "
            f"this table.\n" + "\n".join(wrong),
        )

    def test_cascade_uses_the_existing_disposition_not_a_new_state(self):
        """Kept separate: an ANTI-DIVERGENCE claim about a vocabulary, not a cascade outcome.

        Plan finding F9: `dependency-not-met` does not exist in this runner; do not invent it. The
        source reads are deliberate and are NOT text greps of a function body (see this module's
        docstring): they assert a construct must not EXIST anywhere in either driver, which has no
        behavior to drive - a second state name works correctly right up until run records on disk
        carry two spellings for one condition and the ledger check refuses its own resume.
        """
        state = {
            "repo": "/nonexistent",
            "queue": [
                self._item("failed", position=1, status="failed-safely"),
                self._item("child1", deps=["executed:failed"], position=2),
            ],
        }
        oc_runipd.cascade_dependency_blocked(state)
        self.assertEqual(state["queue"][1]["status"], "dependency-blocked")
        self.assertIn("dependency-blocked", oc_runipd.TERMINAL_STATES)
        for name, path in _DRIVER_SOURCES:
            code = _code_only(path.read_text(encoding="utf-8"))
            for spelling in ("dependency-not-met", "dependency_not_met"):
                with self.subTest(driver=name, spelling=spelling):
                    self.assertNotIn(
                        spelling,
                        code,
                        "the spec's `dependency_not_met` vocabulary must not become a second runner "
                        "state; run records already on disk use `dependency-blocked`",
                    )

    def test_no_declared_edges_set_is_untouched_by_the_cascade(self):
        """Kept separate: a NO-REGRESSION claim about a queue with NO edges at all.

        Every row of `CASCADE` declares an edge, so none of them can state this: a failed item in a
        queue where nothing declares a dependency on it must block NOTHING. That is the behavior every
        Set predating `Item-Dependencies` relies on, and the cascade's blast radius is exactly what a
        regression here would widen.
        """
        for driver, mod in _DRIVERS:
            with self.subTest(driver=driver):
                state = {
                    "repo": "/nonexistent",
                    "queue": [
                        self._item("failed", position=1, status="failed-safely"),
                        self._item("other1", position=2),
                        self._item("other2", position=3),
                    ],
                }
                self.assertEqual(mod.cascade_dependency_blocked(state), [])
                self.assertEqual(
                    [i["status"] for i in state["queue"]],
                    ["failed-safely", "queued", "queued"],
                    "an item failing must not touch work that never declared a dependency on it",
                )

    #: (the plan's on-disk `- Status:`, the status that must be frozen onto its queue entry, why)
    QUEUE_STATUS = (
        (
            "executed",
            "executed",
            "THE FIX. A plan whose `- Status:` is `executed` must NOT be relabeled, or the cascade "
            "reads an executed parent as a dead prerequisite and kills its children at queue build",
        ),
        (
            "  EXECUTED  ",
            "executed",
            "case and surrounding whitespace must not decide a gate: one plan in the live corpus "
            "carries the upper-case form, and a case-sensitive compare would mislabel it",
        ),
        (
            "to-review",
            "queued",
            "a non-terminal plan is DISPATCHABLE. This and the three rows below are the states that "
            "carried every run before the fix, so they pin that the change affects ONLY a status that "
            "is terminal on disk",
        ),
        ("draft", "queued", "the same, for a draft admitted through the draft gate"),
        ("approved", "queued", "the same, for the ordinary execute path"),
        ("auto-approved", "queued", "the same, for a `--full-auto` promotion"),
        ("reusable", "queued", "the same, for a standing reusable plan"),
        (
            "reviewed",
            "reviewed",
            "`reviewed` must REMAIN the fallback, which is what keeps the review-mode queue fixtures in "
            "`test_oc_runipd` passing",
        ),
        (
            None,
            "reviewed",
            "an older hand-written manifest yields None, and it must land on the fallback rather than "
            "raising or producing an empty status the ledger cannot classify",
        ),
        ("", "reviewed", "an empty field, for the same reason"),
        (
            "something-unrecognized",
            "reviewed",
            "an UNKNOWN status must fall back rather than being written through. A status the ledger "
            "does not know makes the R3 coherence check call the run undefined and REFUSE ITS OWN "
            "RESUME, which is unrecoverable state rather than a wrong answer",
        ),
        (
            "superseded",
            "reviewed",
            "in NEITHER `TERMINAL_STATES` nor `runner_shutdown.KNOWN_ITEM_STATUSES`, so preserving it "
            "would trade the cascade bug for a resume-refusing ledger. The `CASCADE` table asserts the "
            "OUTCOME is still right under this name",
        ),
        (
            "not-executed",
            "reviewed",
            "the sibling case, for the same measured reason",
        ),
    )

    def test_the_frozen_queue_status_is_right_for_every_on_disk_status(self):
        """Every on-disk status mapped to its queue status, in one report.

        THREE TESTS BECAME ONE TABLE. `test_already_executed_prerequisite_does_not_block_its_dependent`,
        `test_only_executed_is_preserved_and_the_rest_still_block`, and
        `test_initial_queue_status_keeps_non_terminal_plans_dispatchable` between them called
        `initial_queue_status` on thirteen values and compared one string each; the cascade OUTCOMES
        those tests also asserted now live in the `CASCADE` table above, where action is a column.

        THE TABLE IS THE RIGHT SHAPE because this is a closed MAPPING, and the realistic regression is
        that the mapping widens: someone adds a status to the preserved set without checking that both
        vocabularies admit it. Thirteen assertions spread over three tests cannot show which side of the
        boundary moved; one report listing every status whose mapping changed can.
        """
        wrong = []
        for on_disk, expected, why in self.QUEUE_STATUS:
            got = runner_shared.initial_queue_status(on_disk)
            if got != expected:
                wrong.append(
                    f"  {on_disk!r} -> {got!r}, expected {expected!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.QUEUE_STATUS)} on-disk statuses map to the wrong queue "
            "status. READ WHICH WAY THE BOUNDARY MOVED: if `executed` stopped being preserved, the "
            "measured cascade defect is back and executed parents kill their children at queue build. "
            "If a status that should fall back to `reviewed` is now PRESERVED, check it against BOTH "
            "vocabularies before assuming that is an improvement: a status absent from "
            "`runner_shutdown.KNOWN_ITEM_STATUSES` makes the run refuse its own resume, which is "
            "worse than the mislabeling it fixes. The anti-drift guard "
            f"`test_every_preserved_queue_status_is_in_both_vocabularies` enforces exactly that.\n"
            + "\n".join(wrong),
        )

    def test_every_preserved_queue_status_is_in_both_vocabularies(self):
        """ANTI-DRIFT: widening `TERMINAL_QUEUE_STATUSES` must not break the cascade or resume.

        This is the guard that makes the narrowness above enforceable rather than merely documented. If
        someone later adds a status to `TERMINAL_QUEUE_STATUSES`, it must be admitted by both drivers'
        `TERMINAL_STATES` and by `runner_shutdown.KNOWN_ITEM_STATUSES`, or the run it appears in cannot
        be resumed.
        """
        from agent_workflows import runner_shutdown

        for status in runner_shared.TERMINAL_QUEUE_STATUSES:
            with self.subTest(status=status):
                self.assertIn(
                    status,
                    runner_shutdown.KNOWN_ITEM_STATUSES,
                    "an unknown queue status makes Phase 0 refuse the run's own resume",
                )
                for name, mod in _DRIVERS:
                    self.assertIn(
                        status,
                        mod.TERMINAL_STATES,
                        f"{name}'s cascade cannot act on a status it calls non-terminal",
                    )

    def test_initial_queue_status_keeps_non_terminal_plans_dispatchable(self):
        """NO-REGRESSION on the states that carried every run before the fix.

        `reviewed` must REMAIN the fallback (including for the `None` an older hand-written manifest
        yields), which is what keeps the review-mode queue fixtures in `test_oc_runipd` passing: the
        fix changes the answer ONLY for a status that is terminal on disk.
        """
        for st in ("to-review", "draft", "approved", "auto-approved", "reusable"):
            with self.subTest(status=st):
                self.assertEqual(runner_shared.initial_queue_status(st), "queued")
        for st in (
            "reviewed",
            None,
            "",
            "something-unrecognized",
            "superseded",
            "not-executed",
        ):
            with self.subTest(status=st):
                self.assertEqual(runner_shared.initial_queue_status(st), "reviewed")
        # Case and surrounding whitespace must not decide a gate: one plan in the live corpus
        # carries the multi-word/upper-case `EXECUTED` form.
        self.assertEqual(runner_shared.initial_queue_status("  EXECUTED  "), "executed")


class NoRegressionForUndeclaredEdgesTests(unittest.TestCase):
    """A Set with NO declared edges must gate exactly as it did pre-fix."""

    def test_existing_bare_id6_gating_semantics_are_preserved(self):
        """A bare id6 still means `executed:`, now answered from DISK for every target.

        UPDATED 2026-09-19 with the deletion of the in-queue shortcut (one authority: disk). The
        expectations below are unchanged EXCEPT the `dep003` execute row, and the reason is that this
        test deliberately passes `repo` as a path that does not exist: with the shortcut gone there is
        no in-memory answer, and a nonexistent repository cannot show a plan in `executed/`, so the
        edge refuses. That is the honest verdict for "the prerequisite's work is not on disk", which
        is precisely the condition the shortcut used to paper over.

        A REAL finalized dependency still releases: `ExternalTargetReadinessMatrixTests` covers it
        with an actual `executed/` fixture, and the gating direction here is unchanged (an execute
        dependent refuses a merely `reviewed`/`approved` prerequisite; a review dependent accepts it).
        """
        state = {
            "repo": "/nonexistent",
            "queue": [
                {"id6": "dep001", "status": "reviewed", "action": "review"},
                {"id6": "dep002", "status": "approved", "action": "execute"},
                {"id6": "dep003", "status": "executed", "action": "execute"},
            ],
        }
        for dep, action, expected in (
            ("dep001", "execute", False),
            ("dep002", "execute", False),
            # No repository on disk, so no plan can be in `executed/`: refuse rather than trust a
            # run-state claim that the work landed.
            ("dep003", "execute", False),
            # Same reason: a review dependent accepts a `reviewed`/`approved` prerequisite, but that
            # answer is read from the plan's `- Status:` field ON DISK, and this state names no real
            # repository. `ExternalTargetReadinessMatrixTests` proves the relaxation with a real
            # fixture; verified 2026-09-19 that a review dependent whose prerequisite sits in
            # `pending/` with `- Status: reviewed` is SATISFIED.
            ("dep001", "review", False),
        ):
            with self.subTest(dep=dep, action=action):
                item = {"id6": "tgt", "action": action, "dependencies": [dep]}
                sat, _missing = oc_runipd.dependency_status(item, state)
                self.assertEqual(sat, expected)

    def test_orchestrator_deferral_path_is_unchanged(self):
        """The orchestrator `dependency-blocked` call sites gate on children, not on edges."""
        state = {
            "repo": "/nonexistent",
            "queue": [
                {
                    "id6": "orch00",
                    "setid": "demo",
                    "status": "queued",
                    "action": "orchestrate",
                    "dependencies": [],
                    "position": 1,
                },
                {
                    "id6": "child1",
                    "setid": "demo",
                    "status": "queued",
                    "action": "execute",
                    "dependencies": [],
                    "position": 2,
                },
            ],
        }
        all_done, unfinished = oc_runipd._set_children_all_executed(
            state, "demo", "orch00"
        )
        self.assertFalse(all_done)
        self.assertEqual(unfinished, ["child1"])
        self.assertEqual(oc_runipd.cascade_dependency_blocked(state), [])


class ExternalTargetReadinessMatrixTests(unittest.TestCase):
    """depreview 03ie04 E-06: the ACTION x TARGET-STATE matrix for an EXTERNAL `executed:` target.

    THE WHOLE CORRECTNESS OF 03ie04 IS WHICH COMBINATIONS PASS, so the matrix is the test. The
    defect it pins: `edge_satisfied` compared the target's DIRECTORY (`plan_bucket`) against
    `("executed", "reviewed", "approved")`, but this layout has no `reviewed/` or `approved/`
    directory (a plan stays in `pending/` from `draft` through `approved`), so two thirds of that
    tuple were unreachable and a REVIEW turn refused exactly as an EXECUTE turn would. Spec 25kzda
    2.9's review-action row requires the opposite.

    PRECEDENCE UNDER TEST: a TERMINAL directory decides on its own; for a NON-TERMINAL directory the
    `- Status:` FIELD decides, and an unreadable field FAILS CLOSED.
    """

    #: (label, action, bucket, status-or-None, expected-satisfied)
    MATRIX = (
        # 1-4: the review row of spec 2.9, which was UNREACHABLE before this change.
        ("review vs pending/ + reviewed", "review", "pending", "reviewed", True),
        ("review vs pending/ + approved", "review", "pending", "approved", True),
        ("review vs pending/ + to-review", "review", "pending", "to-review", False),
        ("review vs executed/ + executed", "review", "executed", "executed", True),
        # 5-6: the execute row, DELIBERATELY unrelaxed.
        ("execute vs pending/ + reviewed", "execute", "pending", "reviewed", False),
        ("execute vs pending/ + approved", "execute", "pending", "approved", False),
        ("execute vs executed/ + executed", "execute", "executed", "executed", True),
        # 7: an unreadable field in a NON-TERMINAL directory fails closed for BOTH actions.
        # `read_front_matter_status` returns None for an ABSENT and for a MULTI-WORD status alike.
        ("review vs pending/ + absent", "review", "pending", None, False),
        (
            "review vs pending/ + multi-word",
            "review",
            "pending",
            "EXECUTED (approved)",
            False,
        ),
        ("execute vs pending/ + absent", "execute", "pending", None, False),
        (
            "execute vs pending/ + multi-word",
            "execute",
            "pending",
            "EXECUTED (approved)",
            False,
        ),
        # 8: THE ANTI-REGRESSION CASE. A TERMINAL directory decides ALONE, so a plan in `executed/`
        # whose field is absent, multi-word, or STALE still satisfies under BOTH actions. This is not
        # hypothetical: 25 of the 454 plans in `executed/` have a field the shared reader returns None
        # for (24 absent, 1 the multi-word `EXECUTED (...)` form) and all 25 satisfy today. A fix that
        # made the field authoritative everywhere would break all 25, and NO other row here notices.
        ("review vs executed/ + absent", "review", "executed", None, True),
        ("execute vs executed/ + absent", "execute", "executed", None, True),
        (
            "review vs executed/ + multi-word",
            "review",
            "executed",
            "EXECUTED (approved)",
            True,
        ),
        (
            "execute vs executed/ + multi-word",
            "execute",
            "executed",
            "EXECUTED (approved)",
            True,
        ),
        (
            "review vs executed/ + stale to-review",
            "review",
            "executed",
            "to-review",
            True,
        ),
        (
            "execute vs executed/ + stale to-review",
            "execute",
            "executed",
            "to-review",
            True,
        ),
        # A NON-EXECUTED terminal directory never satisfies `executed:` under either action
        # (spec 5.4 rule 9), and the field must not rescue it.
        ("review vs superseded/ + reviewed", "review", "superseded", "reviewed", False),
        (
            "review vs not-executed/ + approved",
            "review",
            "not-executed",
            "approved",
            False,
        ),
        (
            "execute vs superseded/ + executed",
            "execute",
            "superseded",
            "executed",
            False,
        ),
    )

    def _repo_with_target(self, temp: Path, bucket: str, status: str | None) -> Path:
        repo = temp / "repo"
        d = repo / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        text = _plan_text("depaaa", deps="none", status=status or "approved")
        if status is None:
            text = "\n".join(
                ln for ln in text.splitlines() if not ln.startswith("- Status:")
            )
        (d / "20260829-demo-01-depaaa-x.ipd.md").write_text(text, encoding="utf-8")
        return repo

    def _item(self, action: str) -> dict:
        return {
            "id6": "itemaa",
            "status": "queued",
            "action": action,
            "dependencies": ["executed:depaaa"],
            "position": 1,
            "configured_file": "",
        }

    def _ask(self, mod, fn_name: str, repo: Path, action: str):
        item = self._item(action)
        state = {"repo": str(repo), "queue": [item]}
        return getattr(mod, fn_name)(item, state)

    def test_the_matrix_holds_on_both_hosts_and_through_both_entry_points(self):
        """Every row, for oc and agy, through the DISPATCH and the DRAIN entry point alike.

        BE HONEST ABOUT WHAT THE TWO-PATH SWEEP PROVES. After E-03 deleted agy's local
        `dependency_status_detailed`, both agy paths call the SAME objects as oc, so "they agree" is
        true by construction. The value here is that the matrix is asserted through the exact
        functions the two dispatch sites call (`dependency_status` at dispatch,
        `dependency_status_detailed` at drain), so a future re-fork of either one is caught by a
        BEHAVIORAL failure and not only by the identity pin in `CrossDriverSymmetryTests`.
        """
        for label, action, bucket, status, expected in self.MATRIX:
            for driver, mod in _DRIVERS:
                for fn_name in ("dependency_status", "dependency_status_detailed"):
                    with self.subTest(case=label, driver=driver, entry=fn_name):
                        with tempfile.TemporaryDirectory() as t:
                            repo = self._repo_with_target(Path(t), bucket, status)
                            got = self._ask(mod, fn_name, repo, action)
                            self.assertEqual(
                                got[0],
                                expected,
                                f"{label}: expected satisfied={expected}; reasons={got[-1]!r}",
                            )

    def test_the_measured_case_now_satisfies_and_names_what_it_read(self):
        """The refusal that motivated 03ie04, reproduced SYNTHETICALLY and then fixed.

        MEASURED 2026-09-07: a `review` item declaring `executed:tm2cz8` was refused with "external
        target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved']" while
        `tm2cz8` carried `- Status: reviewed`. Deliberately NOT written against `tm2cz8`: that plan
        has since advanced to `approved`, so a test naming it would silently change what it proves.
        """
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo_with_target(Path(t), "pending", "reviewed")
            satisfied, missing, reasons = self._ask(
                oc_runipd, "dependency_status_detailed", repo, "review"
            )
            self.assertTrue(
                satisfied, f"the measured case must now pass; reasons={reasons!r}"
            )
            self.assertEqual(missing, [])

    def test_the_refusal_message_names_the_field_it_actually_read(self):
        """An operator-facing refusal must not claim to have read a state it never looked at."""
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo_with_target(Path(t), "pending", "to-review")
            _sat, _missing, reasons = self._ask(
                oc_runipd, "dependency_status_detailed", repo, "review"
            )
            reason = reasons["executed:depaaa"]
            self.assertIn(
                "'to-review'", reason, "the refusal must name the FIELD it read"
            )
            self.assertIn("directory 'pending'", reason, "and the directory it saw")

    def test_the_status_field_is_read_with_the_already_shared_reader(self):
        """The SHARED reader is the one that decides, and it is consulted only where the field matters.

        REPLACES A SOURCE-TEXT PIN. The old test ran `inspect.getsource(oc_runipd.edge_satisfied)`
        through `_code_only` and then grepped: `assertIn("_read_status", body)` and a
        `body.split("if edge.kind == 'executed'")[-1].split("record_type")[0]` slice that had to
        contain no `_artifact_owners`. Even with comments stripped that is a change-detector on a NAME
        and on TEXT LAYOUT at once: it goes vacuous the moment the alias is renamed, it fails when the
        branch it slices on is rewritten or reordered, and it says nothing about which reader actually
        RAN. The slice expression in particular encoded the source's line order into the test.

        Now two behavioral claims, plus the identity pin the old test also carried (which is a real
        structural claim and is kept):

        * DELEGATION: the shared reader is replaced with a sentinel that reports `reviewed`, and the
          verdict for a target whose real on-disk status is `to-review` must FLIP to satisfied. A
          second reader, or an inlined regex, keeps reading the file and the verdict does not move.
        * BOUNDEDNESS: the reader is called for a target in a NON-TERMINAL directory and NOT called
          for one in `executed/`, because a terminal directory decides alone. That is the
          anti-regression property behind the 25 plans in `executed/` whose field the shared reader
          returns None for; a text pin could not express it at all.

        WHY `_artifact_owners` IS STILL THE WRONG SUBSTITUTE, recorded since the pin naming it is gone:
        it looks like the smaller change (it already returns `(status, path)`), but it rebuilds the
        whole-repo artifact inventory PER CALL and reads through the STRICT status regex, while the
        runners deliberately use the PERMISSIVE `_read_status` alias. Substituting it would silently
        narrow which front-matter spellings the runner accepts - which the delegation assertion below
        would catch, because the sentinel would no longer be consulted.
        """
        self.assertIs(
            oc_runipd._read_status,
            selectors.read_front_matter_status,
            "`_read_status` must remain the shared PERMISSIVE reader. A private alias here would read "
            "different front-matter spellings than every other surface in the package",
        )
        self.assertIs(
            agy_runipd._read_status,
            oc_runipd._read_status,
            "and both drivers must bind the SAME object, or one host accepts a status the other refuses",
        )

        # THE PATCH TARGET IS `oc_runipd`, FOR BOTH DRIVERS, and that is the point rather than a
        # convenience. `edge_satisfied` is an oc-OWNED object that agy BINDS (see
        # `CrossDriverSymmetryTests._SHARED_NAMES`), so exactly one module global named `_read_status`
        # is consulted no matter which driver's entry point is called. MEASURED while writing this: a
        # first version patched `mod._read_status` per driver and FAILED on agy, because patching agy's
        # alias changes nothing the shared function reads. That failure is the invariant, not a
        # problem: if patching oc's global did NOT move agy's verdict, agy would be running its own
        # copy - which is exactly what shipped once and survived for months.
        for driver, mod in _DRIVERS:
            with self.subTest(driver=driver, half="delegation"):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo_with_target(Path(t), "pending", "to-review")
                    self.assertFalse(
                        self._ask(mod, "dependency_status", repo, "review")[0],
                        "baseline: a `to-review` target in `pending/` does not satisfy a review turn",
                    )
                    with mock.patch.object(
                        oc_runipd, "_read_status", lambda _p: "reviewed"
                    ):
                        self.assertTrue(
                            self._ask(mod, "dependency_status", repo, "review")[0],
                            "with the SHARED reader replaced by one reporting `reviewed`, this "
                            "driver's verdict must flip. Still refusing means EITHER this branch "
                            "reads the status some other way (a second reader or an inlined regex) OR "
                            "this driver is running its own COPY of `edge_satisfied` and never sees "
                            "the shared module's reader at all",
                        )

        for bucket, status, expect_reads, why in (
            (
                "pending",
                "reviewed",
                True,
                "a NON-TERMINAL directory cannot decide alone, so the `- Status:` FIELD must be read",
            ),
            (
                "executed",
                "approved",
                False,
                "a TERMINAL directory decides ALONE, so the field must NOT be consulted. This is the "
                "anti-regression property: 25 of the 454 plans in `executed/` carry a field the shared "
                "reader returns None for (24 absent, 1 the multi-word `EXECUTED (...)` form), and all "
                "25 satisfy today. A fix that made the field authoritative everywhere would break all "
                "25 while every verdict row in MATRIX still passed",
            ),
        ):
            for driver, mod in _DRIVERS:
                with self.subTest(driver=driver, bucket=bucket, half="boundedness"):
                    with tempfile.TemporaryDirectory() as t:
                        repo = self._repo_with_target(Path(t), bucket, status)
                        reads: list = []
                        real = oc_runipd._read_status

                        def spy(path, _sink=reads, _real=real):
                            _sink.append(path)
                            return _real(path)

                        # Patched on oc for the same reason as above: one shared global backs both.
                        with mock.patch.object(oc_runipd, "_read_status", spy):
                            self._ask(mod, "dependency_status", repo, "review")
                        self.assertEqual(
                            bool(reads),
                            expect_reads,
                            f"expected the status field to be read: {expect_reads} "
                            f"(it was read {len(reads)} time(s)). {why}",
                        )

    def test_queue_membership_does_not_change_an_edges_verdict(self):
        """ONE authority: the plan on DISK, whether or not the target is in this run.

        REWRITTEN 2026-09-19 on the maintainer's ruling. This test used to pin an IN-QUEUE branch that
        answered an `executed:` edge from the target's in-memory RUN status, accepting any member of
        `EXECUTION_SUCCESS_STATES` - which admits `substantially-complete`, i.e. finalize did NOT
        happen and, measured, the lane was never merged. Run `run-20260919T194413Z-2056285` therefore
        dispatched `n4xq3l` against a tree holding none of its prerequisite's work: 2h 10m, $55.02,
        nothing integrated.

        THE OLD TEST'S OWN `STATE_CONSTANTS` COMMENT ARGUED FOR THIS FIX while the test pinned the
        opposite: it warns that if the two state sets drift "one edge's verdict starts depending on
        QUEUE MEMBERSHIP - whether the target happens to be in this run - which the same spec
        paragraph explicitly prohibits". The shortcut made the verdict depend on queue membership by
        construction. It is gone, and this test now pins its absence.

        The action asymmetry is UNCHANGED and still lives in the on-disk branch: an EXECUTE dependent
        needs the prerequisite in `executed/`, a REVIEW dependent also accepts a `reviewed`/`approved`
        `- Status:` field, because reviewing plan B against plan A needs A's TEXT and not A's code.
        """
        with tempfile.TemporaryDirectory() as t:
            # The target is in `pending/` with `- Status: reviewed` on DISK, so if the in-queue branch
            # ever started consulting disk this test would stop discriminating.
            repo = self._repo_with_target(Path(t), "pending", "reviewed")
            for action, expected in (("execute", False), ("review", True)):
                with self.subTest(action=action):
                    item = self._item(action)
                    prq = {
                        "id6": "depaaa",
                        "status": "reviewed",
                        "action": "execute",
                        "dependencies": [],
                        "position": 0,
                    }
                    state = {"repo": str(repo), "queue": [prq, item]}
                    sat, _missing, reasons = oc_runipd.dependency_status_detailed(
                        item, state
                    )
                    self.assertEqual(sat, expected, f"reasons={reasons!r}")
                    if not sat:
                        self.assertNotIn(
                            "in-run target",
                            reasons["executed:depaaa"],
                            "the deleted in-queue shortcut answered this edge; the refusal must now "
                            "come from the plan on DISK, which is the single authority",
                        )

    #: (constant name, its exact expected value or None to assert cross-driver equality only, why)
    STATE_CONSTANTS = (
        (
            "SUCCESS_STATES",
            {"executed", "reviewed", "approved"},
            "spec 25kzda 2.9 sanctions exactly these three for a REVIEW-consumed edge, and the in-run "
            "twin must EQUAL the on-disk set. If the two drift, one edge's verdict starts depending on "
            "QUEUE MEMBERSHIP - whether the target happens to be in this run - which the same spec "
            "paragraph explicitly prohibits",
        ),
        (
            "EXECUTION_SUCCESS_STATES",
            {"executed", "substantially-complete"},
            "the EXECUTE bar, and it is deliberately NARROWER than the review bar above. The gap "
            "between the two sets IS the action asymmetry the cascade table exercises; collapsing them "
            "either lets an execute turn build on unwritten code or makes a review-mode Set run "
            "impossible to complete",
        ),
        (
            "TERMINAL_STATES",
            None,
            "asserted for CROSS-DRIVER equality only. Its exact membership is not this file's contract "
            "(the shutdown and ledger surfaces own it), but a per-host difference would mean the "
            "cascade can act on a status one host calls terminal and the other does not",
        ),
    )

    def test_the_state_constants_hold_their_values_and_agree_across_drivers(self):
        """The exact sets AND the cross-driver equality, in one report.

        Two tests became one. `test_the_in_run_success_states_equal_the_sanctioned_on_disk_tuple` pinned
        two values on oc; `test_the_per_driver_state_constants_are_equal_even_though_not_shared` looped
        three names comparing oc to agy. Same three constants, two views, so a single edit to one of
        them fails both - and the two failures answer different halves of the same question ('is the
        value right' and 'do the hosts agree'), which is exactly what one report should show together.

        THE VALUES ARE LITERAL SETS, not references to the constants, so an edit must be deliberate.
        THE EQUALITY IS `assertEqual` AND NOT `assertIs` deliberately: agy re-declares these as EQUAL
        BUT SEPARATE objects, and unifying them is `rununify`'s job, not this file's. Asserting identity
        would fail today for a reason this plan is not fixing.
        """
        wrong = []
        for name, expected, why in self.STATE_CONSTANTS:
            oc_value = getattr(oc_runipd, name)
            agy_value = getattr(agy_runipd, name)
            problems = []
            if expected is not None and oc_value != expected:
                problems.append(f"oc's value is {oc_value!r}, expected {expected!r}")
            if oc_value != agy_value:
                problems.append(
                    f"the two drivers DISAGREE: oc {oc_value!r} vs agy {agy_value!r}"
                )
            if problems:
                wrong.append(
                    f"  {name}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.STATE_CONSTANTS)} state constants are wrong. READ WHICH HALF "
            "FAILED: a VALUE change is a contract change and needs a spec amendment, since these sets "
            "are what spec 2.9's action asymmetry is implemented with. A DISAGREEMENT between drivers "
            "is worse operationally - one host accepts an edge the other refuses, so the same Set "
            "behaves differently depending on which runner an operator reached for, and nothing in "
            f"either host's own suite can see it.\n" + "\n".join(wrong),
        )


class ReviewQueuePreflightTests(unittest.TestCase):
    """depreview 03ie04 E-07: a REVIEW-only selection must not be refused on EXECUTION readiness.

    THE DEFECT, measured 2026-09-07: `aw oc run orchprobe` over four REVIEW turns was refused by
    `check.ipd-dependency-findings-blocked` naming `executed:8tgg6g` and `executed:r2i1b1`, and the
    refusal blocked the very re-review that would have resolved those findings. The preflight refuses
    BEFORE selection ever consults `edge_satisfied`, so nothing in E-01..E-06 can reach it.

    WHAT ACTUALLY FIXES IT, and why this class does not pass a `phase` (see decision 01-03ie04-D1).
    E-07 proposed deriving a review-appropriate `phase`. Measured, `phase` cannot do this job: inside
    `check_engine.evaluate_ipd_dependencies` it is used for EXACTLY ONE thing,
    `blocking = phase in _DEP_BLOCKING_PHASES`, gating the `unresolved` SCAFFOLD SENTINEL finding, and
    every phase a review turn could claim is already in that set. The findings-blocked rule is gated
    on the CONSUMING ACTION instead (`actions`, threaded from `_consuming_actions_for`). So the goal is
    real and reachable, and these tests pin the goal on both hosts rather than the guessed mechanism.
    """

    def _repo(
        self, temp: Path, *, dep_bucket: str, dep_status: str, dependent_status: str
    ):
        repo = temp / "repo"
        for sub in ("plans/pending", "reviews"):
            (repo / ".aw" / "records" / sub).mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".aw" / "config" / "project.json").write_text(
            json.dumps({"review_findings_gate": {"block_at": "high"}}), encoding="utf-8"
        )
        d = repo / ".aw" / "records" / "plans" / dep_bucket
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260829-demo-01-depaaa-x.ipd.md").write_text(
            _plan_text("depaaa", deps="none", status=dep_status), encoding="utf-8"
        )
        dependent = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260829-demo-02-itemaa-x.ipd.md"
        )
        dependent.write_text(
            _plan_text(
                "itemaa", deps="executed:depaaa", order=2, status=dependent_status
            ),
            encoding="utf-8",
        )
        # An UNRESOLVED gating finding against the prerequisite, written through the real writer so
        # the fixture cannot drift from the format `subject_gating_blocks` actually parses.
        review_findings.write_review(
            repo
            / ".aw"
            / "records"
            / "reviews"
            / "20260829-demo-01-depaaa-x.review.md",
            subject_id="depaaa",
            subject_type="ipd",
            reviewed_at="2026-08-29",
            reviewer="test",
            verdict="REVIEWED - OPEN QUESTIONS",
            rounds=[
                review_findings.Round(
                    1,
                    (
                        review_findings.Finding(
                            id="PR-001",
                            severity="high",
                            scope="in-scope",
                            area="correctness",
                            evidence="x.py:1",
                            finding="deliberately unresolved",
                            remediation_risk="low",
                            decision="accepted",
                            resolution="pending",
                        ),
                    ),
                    (),
                )
            ],
        )
        return repo, dependent

    #: (case, prerequisite bucket, prerequisite `- Status:`, the DEPENDENT's `- Status:`, refused?, why)
    FINDINGS_GATE = (
        (
            "a REVIEW queue against a target with open gating findings",
            "pending",
            "reviewed",
            "to-review",
            False,
            "THE DEFECT, measured 2026-09-07: `aw oc run orchprobe` over four REVIEW turns was refused "
            "by `check.ipd-dependency-findings-blocked` naming `executed:8tgg6g` and "
            "`executed:r2i1b1`, and the refusal blocked the very re-review that would have resolved "
            "those findings. `- Status: to-review` derives the `review` action, and a review turn is "
            "not gated on EXECUTION readiness. The preflight refuses BEFORE selection ever consults "
            "`edge_satisfied`, so nothing in E-01..E-06 can reach this",
        ),
        (
            "an EXECUTE queue against the same class of target",
            "executed",
            "executed",
            "approved",
            True,
            "THE COUNTER-CASE: the fix must have narrowed NOTHING it should not. An execute turn is "
            "still refused when its prerequisite carries unresolved gating findings, which is what "
            "keeps the row above from being read as 'the findings gate is off'. Note the prerequisite "
            "here is fully `executed` - the refusal is about the FINDINGS, not about readiness",
        ),
    )

    def test_the_findings_gate_applies_to_execute_turns_and_not_review_turns(self):
        """Both consuming actions against the same findings fixture, on both drivers.

        Two tests became one. Both built the same repository through `_repo` and called
        `enforce_dependency_preflight`; they differed in the fixture's statuses (which is what DERIVES
        the consuming action) and in whether a refusal was expected.

        THE TWO ROWS ARE ONE CONTRACT and belong together: the gate must relax for exactly one action
        and stay strict for the other, so the pair is the assertion and either row alone is satisfiable
        by a gate that is uniformly on or uniformly off. That is not hypothetical - the measured defect
        was a gate that applied to BOTH, and the obvious fix (turn it off) would have left the execute
        row passing in a different test while silently exempting execute runs.
        """
        wrong = []
        for (
            case,
            bucket,
            dep_status,
            dependent_status,
            refused,
            why,
        ) in self.FINDINGS_GATE:
            for driver, mod in _DRIVERS:
                with tempfile.TemporaryDirectory() as t:
                    repo, dependent = self._repo(
                        Path(t),
                        dep_bucket=bucket,
                        dep_status=dep_status,
                        dependent_status=dependent_status,
                    )
                    problems = []
                    try:
                        findings = mod.enforce_dependency_preflight(repo, [dependent])
                    except oc_runipd.DriverError as exc:
                        if not refused:
                            problems.append(
                                f"the run was REFUSED: {str(exc)[:200]!r}. A review-only selection "
                                "must not be gated on execution readiness"
                            )
                        elif "check.ipd-dependency-findings-blocked" not in str(exc):
                            problems.append(
                                f"refused for the wrong reason: {str(exc)[:200]!r}; the findings-"
                                "blocked rule must be the one named"
                            )
                    else:
                        if refused:
                            problems.append(
                                "the run was ADMITTED; an execute turn against a prerequisite with "
                                "unresolved gating findings must be refused"
                            )
                        elif findings != []:
                            problems.append(
                                f"admitted but returned findings {findings!r}, expected []"
                            )
                    if problems:
                        wrong.append(
                            f"  {case} on {driver}:\n"
                            + "".join(f"    - {p}\n" for p in problems)
                            + f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"the findings gate is wrong for {len(wrong)} of "
            f"{len(self.FINDINGS_GATE) * len(_DRIVERS)} (action, driver) cells. BOTH ROWS FAILING IN "
            "THE SAME DIRECTION means the gate became uniform, which is the real risk here: uniformly "
            "ON reproduces the 2026-09-07 outage where a re-review could not run because the findings "
            "it would resolve blocked it, and uniformly OFF silently exempts execute runs from a gate "
            "that exists to stop building on unresolved high-severity findings. The mechanism is the "
            "CONSUMING ACTION threaded from `_consuming_actions_for`, not a `phase` argument (see "
            f"`test_the_phase_argument_cannot_discriminate_a_review_turn`).\n"
            + "\n".join(wrong),
        )

    def test_removing_the_action_input_re_blocks_the_review_queue(self):
        """THE MUTATION CHECK: the admitting behavior is load-bearing, not incidental.

        Neutralize the consuming-action derivation (the mechanism that actually carries the fix) and
        the review-only selection must be REFUSED again, then restore it and it passes. This is the
        E-07 equivalent of "revert the change, see it break, restore it": it proves the review case
        passes BECAUSE of the action input rather than because the fixture is toothless.
        """
        with tempfile.TemporaryDirectory() as t:
            repo, dependent = self._repo(
                Path(t),
                dep_bucket="pending",
                dep_status="reviewed",
                dependent_status="to-review",
            )
            self.assertEqual(
                oc_runipd.enforce_dependency_preflight(repo, [dependent]), []
            )
            original = oc_runipd._consuming_actions_for
            try:
                oc_runipd._consuming_actions_for = lambda plans: {}
                with self.assertRaises(oc_runipd.DriverError) as caught:
                    oc_runipd.enforce_dependency_preflight(repo, [dependent])
                self.assertIn(
                    "check.ipd-dependency-findings-blocked", str(caught.exception)
                )
            finally:
                oc_runipd._consuming_actions_for = original
            self.assertEqual(
                oc_runipd.enforce_dependency_preflight(repo, [dependent]),
                [],
                "the fixture must pass again once the action input is restored",
            )

    def test_the_phase_argument_cannot_discriminate_a_review_turn(self):
        """Pins decision 01-03ie04-D1, so nobody re-adds a phase argument expecting it to gate.

        `phase` reaches exactly one rule (the `unresolved` sentinel) and EVERY blocking phase name
        behaves identically for these inputs. Asserted rather than argued, because the plan's E-07
        prose proposed `phase` as the lever and a future reader will otherwise try it again.
        """
        with tempfile.TemporaryDirectory() as t:
            repo, dependent = self._repo(
                Path(t),
                dep_bucket="executed",
                dep_status="executed",
                dependent_status="approved",
            )
            for phase in sorted(check_engine._DEP_BLOCKING_PHASES):
                with self.subTest(phase=phase):
                    with self.assertRaises(oc_runipd.DriverError):
                        oc_runipd.enforce_dependency_preflight(
                            repo, [dependent], phase=phase
                        )


class ConsumingActionDerivationTests(unittest.TestCase):
    """`_consuming_actions_for` must agree with `action_for` and fail closed on unreadable input.

    This is the runner half of the 2026-09-08 findings-gate fix. The evaluator relaxes its
    findings-blocked check ONLY for a `review` turn, so a wrong or missing action here is what would
    either re-block a review run or silently exempt an execute run. Both directions are pinned.
    """

    def _write(self, tmp: Path, name: str, kind: str, status: str) -> Path:
        p = tmp / name
        p.write_text(
            f"# IPD: t\n\n- Kind: {kind}\n- Status: {status}\n- Id: aaa111\n",
            encoding="utf-8",
        )
        return p

    def test_derived_action_matches_the_shared_action_for(self):
        """Left unmerged: it is already table-driven over its own five (kind, status) cases, and it
        asserts the derivation against `runner_shared.action_for` per case AND the whole dict at once,
        which a per-row loop would lose."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cases = [
                ("child", "to-review", "review"),
                ("child", "approved", "execute"),
                ("child", "reviewed", "execute"),
                ("orchestrator", "to-review", "review"),
                ("orchestrator", "approved", "orchestrate"),
            ]
            plans = []
            want = {}
            for i, (kind, status, expected) in enumerate(cases):
                p = self._write(tmp, f"p{i}.ipd.md", kind, status)
                plans.append((p, p.read_text(encoding="utf-8")))
                want[str(p)] = expected
                self.assertEqual(
                    runner_shared.action_for(kind, status),
                    expected,
                    "the fixture's own expectation must match the shared predicate",
                )
            self.assertEqual(oc_runipd._consuming_actions_for(plans), want)

    def test_unreadable_plan_is_omitted_so_the_evaluator_stays_strict(self):
        """Unreadable must never mean permissive: omission leaves the strict (execute) default."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            bad = tmp / "bad.ipd.md"
            bad.write_text("no front matter at all\n", encoding="utf-8")
            good = self._write(tmp, "good.ipd.md", "child", "to-review")
            plans = [
                (bad, bad.read_text(encoding="utf-8")),
                (good, good.read_text(encoding="utf-8")),
            ]
            derived = oc_runipd._consuming_actions_for(plans)
            self.assertNotIn(str(bad), derived)
            self.assertEqual(derived.get(str(good)), "review")


class AntiDivergenceGuardTests(unittest.TestCase):
    """E-05: the two parsers must not be able to diverge again."""

    # A `re.compile(...)` call whose pattern text mentions a dependency field name. Deliberately
    # NOT `[^)]*`: a real pattern contains `)` (e.g. the `(?m)` flag group), so a `[^)]*` bound
    # cannot reach the field name and the guard would be VACUOUS - measured: it passed against the
    # pre-fix `_DEPS_RE` it was written to catch. Bounded by a newline instead, since these are
    # single-line declarations.
    _DEP_REGEX_HINT = re.compile(
        r"re\.compile\([^\n]*(?:Item-Dependencies|Dependencies|Depends-on)"
    )

    def test_no_driver_defines_a_dependency_regex(self):
        """Left separate from `DELETED_CONSTRUCTS`: its subject is a compiled REGEX, matched by a
        module-level pattern whose own falsifiability comment (a `[^)]*` bound made it vacuous) belongs
        beside it."""
        for name, path in _DRIVER_SOURCES:
            with self.subTest(driver=name):
                text = path.read_text(encoding="utf-8")
                # NOTE: this guard reads the RAW source on purpose. A dependency regex is written as
                # a string literal, which `_code_only` would strip, so stripping here would make the
                # guard unfalsifiable. Comments are dropped (they are prose), string literals are not.
                code = "\n".join(
                    ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
                )
                self.assertIsNone(
                    self._DEP_REGEX_HINT.search(code),
                    f"{name} re-introduced a private dependency regex; the field NAME must come "
                    "from ipd_schema and the GRAMMAR from parse_item_dependencies",
                )

    #: (case, the raw-source substrings that must be ABSENT, a whitespace-insensitive regex that must
    #: not match or None, module attributes that must not EXIST, why this row exists)
    #:
    #: These read the driver SOURCE FILES on purpose, and that is a different thing from grepping a
    #: function body for a name it happens to use (see this module's docstring). The claim in every row
    #: is that a construct must not EXIST ANYWHERE, which has no behavior to drive: a re-introduced
    #: private parser works CORRECTLY right up until it drifts from the shared one, which is precisely
    #: how the defect this file pins was born. Each pattern was measured against the real pre-fix
    #: source, so each is falsifiable in the right direction.
    DELETED_CONSTRUCTS = (
        (
            "a private dependency PARSER",
            ("_DEPS_RE = ", "def _read_deps("),
            None,
            ("_DEPS_RE", "_read_deps"),
            "THE ORIGINAL DEFECT. Both drivers carried a private `_DEPS_RE` matching a legacy "
            "`Dependencies:`/`Depends-on:` field no plan in the tree uses, so `_read_deps` returned "
            "`[]` for a valid three-edge statement while the shared parser returned three typed "
            "records. Both the DEFINITION in source and the ATTRIBUTE on the module are checked, "
            "because a re-export would satisfy one and not the other",
        ),
        (
            "an INLINED queue-status allowlist",
            (),
            r'"queued"\s*if\s*status\s*in\s*\(',
            (),
            "the defect was ONE expression, present BYTE-IDENTICALLY in both hosts, which is exactly "
            'the divergence shape this class exists to prevent. It read `"status": "queued" if '
            'status in ("to-review","draft","approved","auto-approved") else "reviewed"`, and '
            "its missing `executed` arm silently converted every already-executed prerequisite into a "
            "dead one. Matched whitespace-insensitively so a reformat cannot hide it. "
            "REAL DEFECT FOUND WHEN TABULATING: THE GUARD THIS ROW REPLACES WAS VACUOUS. It searched "
            "`_code_only(...)` output, and `_code_only` strips STRING LITERALS via the tokenizer, so "
            'the `"queued"` the pattern anchors on had already been removed and the regex could never '
            "match anything. MEASURED by re-inlining the real pre-fix expression into "
            "`oc_runipd.initialize_run`: the old guard stayed GREEN (only an unrelated behavioral test "
            "caught it). The row now scans COMMENT-STRIPPED RAW source, which is the same treatment "
            "`test_no_driver_defines_a_dependency_regex` already documents for exactly this reason - "
            "comments are prose and are dropped, string literals are CODE here and are kept",
        ),
    )

    def test_no_driver_re_introduces_a_deleted_construct(self):
        """Every deleted construct, both drivers, in one report.

        THREE TESTS BECAME ONE TABLE. `test_no_driver_defines_the_deleted_private_parser`,
        `test_no_driver_inlines_the_initial_queue_status_allowlist`, and
        `test_no_driver_exposes_the_deleted_names` all swept the same two driver files (or the same two
        modules) asserting one construct absent; only the construct differed.

        WHY ONE REPORT: these guards exist because a re-fork is SILENT, and a re-fork usually arrives as
        a group - someone restoring 'the old way of reading dependencies' brings back the regex AND the
        function AND possibly the allowlist in one edit. Three tests report that as three unrelated red
        lines; the table names every construct that came back, on which host, which is the shape of the
        actual regression.

        SOURCE TEXT AND MODULE ATTRIBUTES ARE BOTH CHECKED PER ROW, which the old tests did in separate
        methods: a driver could delete the definition and keep a re-export (attribute present, source
        clean) or vice versa, and only one of the two old tests would have noticed.
        """
        wrong = []
        for case, substrings, pattern, attributes, why in self.DELETED_CONSTRUCTS:
            for driver, path in _DRIVER_SOURCES:
                text = path.read_text(encoding="utf-8")
                problems = []
                for needle in substrings:
                    if needle in text:
                        problems.append(f"the raw source still contains {needle!r}")
                if pattern is not None:
                    # COMMENT-STRIPPED RAW SOURCE, NOT `_code_only`. `_code_only` also strips STRING
                    # LITERALS, and these patterns anchor on one (`"queued"`), so running them through
                    # it makes them unfalsifiable - measured: the guard this replaced stayed green
                    # against the real pre-fix expression re-inlined into `initialize_run`. Comments
                    # are prose and are dropped so documenting the fix does not trip the guard; string
                    # literals are CODE for this purpose and are kept.
                    # WHAT IS STRIPPED, AND WHY EACH CHOICE IS DELIBERATE. This scan must be
                    # falsifiable, and it must not fire on documentation of the very defect it hunts.
                    #
                    # COMMENTS AND DOCSTRINGS ARE STRIPPED because they are PROSE: `initial_queue_status`
                    # QUOTES the old defective expression verbatim in its own docstring, to record what
                    # was fixed. Measured at this merge: not stripping docstrings reports that quote as
                    # a live re-inlining on both hosts, a FALSE POSITIVE on correct code.
                    #
                    # OTHER STRING LITERALS ARE KEPT because they are CODE here: the pattern anchors on
                    # `"queued"`, so a scan that drops every string can never match and the guard becomes
                    # unfalsifiable. Measured: the shipped guard used `_code_only`, which drops ALL
                    # STRING tokens, and stayed GREEN against the real pre-fix expression re-inlined
                    # into `initialize_run`.
                    #
                    # So neither `_code_only` (too aggressive, vacuous) nor raw source (too permissive,
                    # false-positive) is correct; the middle is what this does.
                    code = _code_without_prose(text)
                    # ADOPTED FROM main AT THE 2026-09-18 MERGE: after `7a28ed11` unified
                    # `initialize_run` into `runner_shared.initialize_run_core`, the construct this row
                    # hunts for can live in the SHARED module rather than the driver file, so a
                    # driver-only scan would go quiet for the wrong reason. Widen as main does.
                    if "initialize_run_core" in code:
                        code += _code_without_prose(
                            (path.parent / "runner_shared.py").read_text(
                                encoding="utf-8"
                            )
                        )
                    if re.search(pattern, re.sub(r"\s+", " ", code)):
                        problems.append(
                            f"the pattern {pattern!r} matches the CODE (comments stripped, string "
                            "literals kept), so this is a live re-inlining and not documentation of "
                            "the fix"
                        )
                if problems:
                    wrong.append(
                        f"  {case} in {driver}.py:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
            for driver, mod in _DRIVERS:
                present = [name for name in attributes if hasattr(mod, name)]
                if present:
                    wrong.append(
                        f"  {case} as a module ATTRIBUTE on {driver}:\n"
                        f"    - {present} still exist(s)\n"
                        "    this half exists because: a driver can delete the definition and keep a "
                        "RE-EXPORT, which leaves the source clean while every caller still reaches the "
                        f"old symbol\n    the row's rule: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} deleted construct(s) are back. Each one is a SECOND definition of something "
            "the shared modules own, and the failure mode is silent: a private parser or an inlined "
            "allowlist behaves correctly until it drifts, and then the runner gates on a graph no other "
            "surface can see (`aw check` and `aw ipd lint` read the shared one). If several rows fail "
            "together, someone restored 'the old way' wholesale rather than one construct regressing. "
            "FIX: the field NAME comes from `ipd_schema`, the GRAMMAR from `parse_item_dependencies`, "
            f"and the queue status from `runner_shared.initial_queue_status`.\n"
            + "\n".join(wrong),
        )

    def test_both_hosts_bind_the_shared_queue_status_helper(self):
        """Kept separate: an OBJECT IDENTITY claim, which no absence-of-text row can make.

        Merged from `test_both_hosts_agree_on_every_frozen_queue_status`, whose two `assertIs` calls
        differed only in the module. Identity is the positive counterpart to the absence rows above: they
        prove no host rebuilt the mapping, this proves both reach the SAME object, so a future status
        addition cannot land on one host only.

        Spec `20260826-0718-01` 2.9 requires an `executed:` edge to be decided by the consuming action
        "and by nothing else: not by queue membership, not by which host is running".
        """
        for driver, mod in _DRIVERS:
            with self.subTest(driver=driver):
                self.assertIs(
                    mod.runner_shared.initial_queue_status,
                    runner_shared.initial_queue_status,
                    f"{driver} must reach the SHARED helper object, not a copy: a per-host mapping is "
                    "one of the two ways spec 2.9's 'not by which host is running' gets broken",
                )

    def test_drivers_reference_the_shared_dependency_api(self):
        """Pre-fix BOTH drivers referenced the shared dependency API zero times."""
        oc_text = (REPO_ROOT / "agent_workflows" / "oc_runipd.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("parse_item_dependencies", oc_text)
        self.assertIn("META_ITEM_DEPENDENCIES", oc_text)
        self.assertIn("evaluate_ipd_dependencies", oc_text)

    def test_each_shared_api_is_actually_REACHED_on_both_drivers(self):
        """The behavioral counterpart to the reference sweep above: each shared API really RUNS.

        The sibling `test_drivers_reference_the_shared_dependency_api` asserts three names APPEAR in
        oc's source, which was written against a measured pre-fix state where both drivers referenced
        the shared dependency API ZERO times. That mention check is a weak proxy, and it stays only
        because a mention is where the fix began; what matters is that each authority is CONSULTED, on
        BOTH drivers, which a mention cannot show and a comment can fake.

        Each row patches the shared authority with a sentinel and requires the runner's answer to move.
        A private copy keeps producing the real answer, so the sentinel never appears.
        """
        wrong = []
        for driver, mod in _DRIVERS:
            # `ipd_schema.parse_item_dependencies`: the VALUE grammar.
            with mock.patch.object(
                ipd_schema,
                "parse_item_dependencies",
                lambda _raw: ([], False, "sentinel parser error"),
            ):
                got = mod._read_item_dependencies(_plan_text("aaaaaa"))
            if got != ([], "sentinel parser error"):
                wrong.append(
                    f"  `ipd_schema.parse_item_dependencies` on {driver}:\n"
                    f"    - patched to report a sentinel error, but the runner returned {got!r}\n"
                    "    this row exists because: the VALUE GRAMMAR has one definition. A runner "
                    "parsing the statement itself accepts and rejects different tokens than `aw check` "
                    "and `aw ipd lint`, which is the divergence this whole file pins"
                )

            # `ipd_schema.META_ITEM_DEPENDENCIES`: the FIELD NAME.
            with mock.patch.object(
                ipd_schema, "META_ITEM_DEPENDENCIES", "Sentinel-Field-Name"
            ):
                edges, _err = mod._read_item_dependencies(_plan_text("aaaaaa"))
            if edges != []:
                wrong.append(
                    f"  `ipd_schema.META_ITEM_DEPENDENCIES` on {driver}:\n"
                    f"    - the field name was renamed to a value no plan carries, yet the runner "
                    f"still read {edges!r}\n"
                    "    this row exists because: the FIELD NAME is the schema's constant, not a "
                    "local literal. A hardcoded name is how the runner came to read a legacy field "
                    "that no plan in the tree uses"
                )

            # `check_engine.evaluate_ipd_dependencies`: the RULES. (Covered in depth by
            # `PreflightFailClosedTests`; asserted here so all three authorities are in one place.)
            with tempfile.TemporaryDirectory() as t:
                repo = Path(t) / "repo"
                pending = repo / ".aw" / "records" / "plans" / "pending"
                pending.mkdir(parents=True)
                path = _write_plan(pending, "aaaaaa", deps="none")
                calls: list = []
                with mock.patch.object(
                    check_engine,
                    "evaluate_ipd_dependencies",
                    lambda *a, **k: calls.append(k) or [],
                ):
                    mod.preflight_dependency_findings(repo, [path])
                if len(calls) != 1:
                    wrong.append(
                        f"  `check_engine.evaluate_ipd_dependencies` on {driver}:\n"
                        f"    - was called {len(calls)} time(s), expected exactly 1\n"
                        "    this row exists because: spec 25kzda 2.10 says 'all surfaces call this "
                        "evaluator; none reimplement the rules'. Zero calls means this host has its "
                        "own dependency policy"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} shared-authority delegation(s) are broken. The three authorities are the "
            "field NAME (`ipd_schema.META_ITEM_DEPENDENCIES`), the value GRAMMAR "
            "(`parse_item_dependencies`), and the RULES (`check_engine.evaluate_ipd_dependencies`), and "
            "each can be forked independently. READ WHICH ONE: a forked NAME makes the runner read a "
            "different field than the checkers; a forked GRAMMAR makes it accept different tokens; "
            "forked RULES make it refuse or admit runs `aw check` disagrees about. A failure on ONE "
            f"driver only means that host re-forked while the other stayed correct.\n"
            + "\n".join(wrong),
        )

    def test_shared_rule_modules_are_not_modified_by_the_runner(self):
        """The runner became a CONSUMER; the shared rules stay in the shared modules."""
        for mod_name in ("check_engine", "ipd_lint"):
            text = (REPO_ROOT / "agent_workflows" / f"{mod_name}.py").read_text(
                encoding="utf-8"
            )
            with self.subTest(module=mod_name):
                for runner_only in ("oc_runipd", "agy_runipd", "dependency_status"):
                    self.assertNotIn(
                        runner_only,
                        text,
                        f"{mod_name} must not learn about the runner or its run state",
                    )


class CrossDriverSymmetryTests(unittest.TestCase):
    """Both drivers are declared in this plan's Scope-Paths, so REAL symmetry is required."""

    # THIS LIST IS THE ONLY AVAILABLE HOME FOR A RUNNER-OWNED SHARED SYMBOL, and the reason is
    # structural rather than preference (depreview 03ie04 E-04). The sibling guard
    # `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` cannot host one: its `Owned` contract is
    # "a NON-RUNNER module owns this symbol; no runner may re-define it", every row's owner is
    # `render_stream`, `runner_shared` or `selectors`, and naming `oc_runipd` as an owner would make
    # its AST half forbid oc's own definition. So `oc_runipd`-owned names that agy must BIND rather
    # than copy are pinned here, by OBJECT IDENTITY, in `test_the_implementation_is_shared_not_copied`.
    #
    # KNOW WHAT THIS CATCHES AND WHAT IT DOES NOT: identity catches a RE-DEFINED copy, which is what
    # actually happened to `dependency_status_detailed` (agy carried its own broken copy for months
    # BECAUSE this list did not name it, so the guard passed over a live divergence). It would NOT
    # catch a copy assigned over the re-export at import time. That residual hole is accepted, not
    # fixed here: no such pattern exists in either driver today.
    _SHARED_NAMES = (
        "_read_item_dependencies",
        "parse_dependency_token",
        "dependency_target_id6",
        "edge_satisfied",
        "dependency_status",
        # depreview 03ie04 E-04: the `_detailed` sibling was MISSING from this list, which is exactly
        # why the guard below passed over agy's real copy of it. Both names are required.
        "dependency_status_detailed",
        "dependency_reasons",
        "dependency_depth",
        "queue_sort_key",
        "cascade_dependency_blocked",
        "preflight_dependency_findings",
        "DEPENDENCY_FATAL_RULES",
    )

    def test_every_shared_name_is_present_on_both_drivers_and_is_the_SAME_object(self):
        """PRESENCE and IDENTITY for every shared name, in one report.

        Two tests became one. `test_both_drivers_expose_the_dependency_api` looped the names asserting
        `hasattr`; `test_the_implementation_is_shared_not_copied` looped the same names asserting `is`.
        They fail together whenever a name is renamed, and the two answers are only useful read
        side by side: PRESENT-BUT-DIFFERENT is a re-forked copy (what actually happened to
        `dependency_status_detailed`, which agy carried its own broken version of for months), while
        ABSENT is an unbound re-export. The fixes are opposite - delete a copy versus add a binding -
        so the report must say which it is.

        WHY IDENTITY RATHER THAN EQUALITY: identity is the only check that catches a copy, since a
        freshly re-forked function is `==` to nothing and `is` to nothing but still passes `hasattr`.
        Its known limit is recorded above the name list: it would NOT catch a copy assigned over the
        re-export at import time, and that residual hole is accepted rather than fixed here.
        """
        wrong = []
        for name in self._SHARED_NAMES:
            oc_attr = getattr(oc_runipd, name, None)
            agy_attr = getattr(agy_runipd, name, None)
            if oc_attr is None and not hasattr(oc_runipd, name):
                wrong.append(
                    f"  {name}: ABSENT from oc_runipd, which OWNS it. Every other claim about this "
                    "name is vacuous until it exists"
                )
                continue
            if not hasattr(agy_runipd, name):
                wrong.append(
                    f"  {name}: ABSENT from agy_runipd. agy must BIND oc's object; an unbound name "
                    "means agy either reimplements this behavior under another name or does not "
                    "perform it at all"
                )
            elif agy_attr is not oc_attr:
                wrong.append(
                    f"  {name}: PRESENT on both but they are DIFFERENT objects "
                    f"({agy_attr!r} vs {oc_attr!r}). This is a re-forked COPY, which is the exact "
                    "shape of the measured defect: agy carried its own broken "
                    "`dependency_status_detailed` for months BECAUSE this list did not name it, so "
                    "the guard passed over a live divergence"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self._SHARED_NAMES)} shared names are not one implementation. READ "
            "THE KIND: a DIFFERENT-OBJECT failure is a copy and the fix is to delete it and bind oc's "
            "(a fix landing in one driver only is how one host accepts an edge the other refuses); an "
            "ABSENT failure is a missing binding and the fix is to add the re-export. Note identity "
            "catches a re-DEFINED copy but would not catch one assigned over the re-export at import "
            f"time; that hole is accepted and documented above the name list.\n"
            + "\n".join(wrong),
        )

    def test_both_drivers_agree_on_a_typed_statement(self):
        """Kept separate: the BEHAVIORAL twin of the identity table above.

        Identity proves the two names point at one object; this proves the two ENTRY POINTS return the
        same answer for a real statement. Both are needed, because identity would be satisfied by a
        shared object that either host wrapped, and agreement would be satisfied by two copies that
        happen to agree today.
        """
        text = _plan_text("aaaaaa")
        self.assertEqual(
            oc_runipd._read_item_dependencies(text),
            agy_runipd._read_item_dependencies(text),
        )

    def test_both_drivers_freeze_the_same_queue_dependencies(self):
        """Left separate: materially different setup (a two-plan repo built and discovered twice) and a
        cross-driver EQUALITY over whole manifests, not a per-row verdict."""
        with tempfile.TemporaryDirectory() as t:
            repo = Path(t)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            _write_plan(pending, "aaaaaa", order=1, deps="none")
            _write_plan(pending, "bbbbbb", order=2, deps="executed:aaaaaa")
            oc_manifest = oc_runipd.build_dynamic_manifest(
                repo, oc_runipd.discover_plans(repo)
            )
            agy_manifest = agy_runipd.build_dynamic_manifest(
                repo, agy_runipd.discover_plans(repo)
            )
            self.assertEqual(
                {k: v["dependencies"] for k, v in oc_manifest["plans"].items()},
                {k: v["dependencies"] for k, v in agy_manifest["plans"].items()},
            )
            self.assertEqual(
                oc_manifest["plans"]["bbbbbb"]["dependencies"], ["executed:aaaaaa"]
            )

    def test_both_drivers_validate_a_typed_manifest_identically(self):
        """Left unmerged with its two `assertRaises` siblings below: merging would couple an
        accept-path claim to two refusal paths whose failure mode (a missing exception) is different."""
        manifest = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": [],
                },
                "bbbbbb": {
                    "file": ".aw/records/plans/pending/b.ipd.md",
                    "set": "demo",
                    "dependencies": ["executed:aaaaaa", "exists:spec:d4e5f6"],
                },
            },
            "sets": {"demo": {"order": ["aaaaaa", "bbbbbb"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                mod.validate_manifest(json.loads(json.dumps(manifest)))

    def test_both_drivers_reject_an_unknown_ipd_target_and_accept_a_leaf(self):
        """Left separate: an `assertRaises` test, and its two halves share one fixture by mutation."""
        base = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": ["executed:zzzzzz"],
                }
            },
            "sets": {"demo": {"order": ["aaaaaa"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name, case="unknown ipd target"):
                with self.assertRaises(mod.DriverError):
                    mod.validate_manifest(json.loads(json.dumps(base)))
        leaf = json.loads(json.dumps(base))
        leaf["plans"]["aaaaaa"]["dependencies"] = ["exists:spec:zzzzzz"]
        for name, mod in _DRIVERS:
            with self.subTest(driver=name, case="spec leaf"):
                mod.validate_manifest(json.loads(json.dumps(leaf)))

    def test_both_drivers_reject_a_malformed_manifest_edge(self):
        """Left separate: an `assertRaises` test (see the sibling above for the shared reason)."""
        bad = {
            "schema_version": oc_runipd.SCHEMA_VERSION,
            "plans": {
                "aaaaaa": {
                    "file": ".aw/records/plans/pending/a.ipd.md",
                    "set": "demo",
                    "dependencies": ["not-an-edge"],
                }
            },
            "sets": {"demo": {"order": ["aaaaaa"]}},
        }
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with self.assertRaises(mod.DriverError):
                    mod.validate_manifest(json.loads(json.dumps(bad)))


class LiveCorpusAgreementTests(unittest.TestCase):
    """The runner must now see what the authority surface sees on the REAL tree."""

    def test_runner_extraction_matches_the_authority_surface(self):
        """Left separate: a REAL-CORPUS sweep with its own skip conditions, not a fixture table."""
        plans_root = REPO_ROOT / ".aw" / "records" / "plans"
        if not plans_root.is_dir():
            self.skipTest("no plans tree in this checkout")
        files = sorted(plans_root.rglob("*.ipd.md"))
        if not files:
            self.skipTest("no IPDs in this checkout")
        compared = 0
        for path in files:
            text = path.read_text(encoding="utf-8")
            m = check_engine._ITEM_DEPENDENCIES_RE.search(text)
            if m is None:
                continue
            expected_edges, err = (
                (
                    [
                        e.canonical()
                        for e in ipd_schema.parse_item_dependencies(m.group(1).strip())[
                            0
                        ]
                    ],
                    None,
                )
                if ipd_schema.parse_item_dependencies(m.group(1).strip())[2] is None
                else ([], ipd_schema.parse_item_dependencies(m.group(1).strip())[2])
            )
            got_edges, got_err = oc_runipd._read_item_dependencies(text)
            self.assertEqual(
                (got_edges, got_err is None),
                (expected_edges, err is None),
                f"runner disagrees with the authority extraction for {path.name}",
            )
            compared += 1
        self.assertGreater(compared, 0)

    def test_a_declaring_plan_yields_nonempty_dependencies(self):
        """Contrast with the measured pre-fix state: real run records froze `dependencies: []`."""
        plans_root = REPO_ROOT / ".aw" / "records" / "plans"
        if not plans_root.is_dir():
            self.skipTest("no plans tree in this checkout")
        found = []
        for path in sorted(plans_root.rglob("*.ipd.md")):
            rec = oc_runipd.parse_plan_file(path, REPO_ROOT)
            if rec and rec.dependencies:
                found.append((rec.id6, rec.dependencies))
        if not found:
            self.skipTest("no plan in this checkout declares a dependency edge")
        for _id6, deps in found:
            for tok in deps:
                self.assertIsNotNone(
                    oc_runipd.parse_dependency_token(tok),
                    f"live corpus token {tok!r} must parse through the shared grammar",
                )


class InRunExecutedDependencyTests(unittest.TestCase):
    """Regression test for in-run executed plan dependency satisfaction (hp9rot E-08 / BUG-04)."""

    def test_in_run_executed(self):
        """E-08: initialize_run preserves on-disk terminal status ('executed') instead of coercing
        already-executed plans to 'reviewed', allowing downstream execution plans with 'executed:<id6>'
        dependencies to be satisfied."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            for d in (".aw/records/plans/pending", ".aw/records/plans/executed"):
                (repo / d).mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

            p1 = (
                repo / ".aw/records/plans/executed/20260908-demo-01-aaaaaa-first.ipd.md"
            )
            p1.write_text(
                _plan_text("aaaaaa", status="executed", deps=None), encoding="utf-8"
            )

            p2 = (
                repo / ".aw/records/plans/pending/20260908-demo-02-bbbbbb-second.ipd.md"
            )
            p2.write_text(
                _plan_text(
                    "bbbbbb", status="approved", deps="executed:aaaaaa", order=2
                ),
                encoding="utf-8",
            )

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

            for name, mod in _DRIVERS:
                with self.subTest(driver=name):
                    args = _StartArgs(repo=str(repo), selectors=["demo"])
                    args.action = None
                    args.run_id = f"run-{name}"
                    run_dir = mod.initialize_run(args)
                    state = mod.load_state(run_dir)
                    q = state["queue"]
                    it1 = next(it for it in q if it["id6"] == "aaaaaa")
                    self.assertEqual(
                        it1["status"],
                        "executed",
                        f"{name} must retain executed status for executed plan",
                    )

                    it2 = next(it for it in q if it["id6"] == "bbbbbb")
                    self.assertEqual(
                        it2["status"],
                        "queued",
                        f"{name} dependent plan must stay queued and not be marked dependency-blocked",
                    )

                    blocked = mod.cascade_dependency_blocked(state)
                    self.assertNotIn(
                        "bbbbbb",
                        [b.get("id6") if isinstance(b, dict) else b for b in blocked],
                    )
                    self.assertEqual(it2["status"], "queued")


class TheDiskIsTheOnlyAuthorityForAnExecutedEdgeTests(unittest.TestCase):
    """REGRESSION GUARD for the 2026-09-19 incident: run `run-20260919T194413Z-2056285`.

    `yaxr4i` finished `substantially-complete`, which means `aw ipd finalize` did NOT run, so the plan
    stayed in `pending/` and its two commits lived only on `aw/lane/yaxr4i`. The deleted in-queue
    shortcut accepted that status for an `executed:` edge, so `n4xq3l` was told its prerequisite was
    done and was dispatched into a lane holding NONE of that work. It refused, went `blocked`, and
    cascaded `dependency-blocked` to eight further items. Cost: 2h 10m and $55.02, nothing integrated.

    The maintainer's ruling was ONE authority, not gates in depth: the plan's directory on disk.
    """

    def _state(self, repo: Path, dep_run_status: str) -> dict:
        return {
            "repo": str(repo),
            "queue": [
                {
                    "id6": "depaaa",
                    "status": dep_run_status,
                    "action": "execute",
                    "dependencies": [],
                    "position": 1,
                },
                {
                    "id6": "itemaa",
                    "status": "queued",
                    "action": "execute",
                    "dependencies": ["executed:depaaa"],
                    "position": 2,
                },
            ],
        }

    def _repo(self, temp: Path, bucket: str, status: str) -> Path:
        repo = temp / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        target = repo / ".aw" / "records" / "plans" / bucket
        target.mkdir(parents=True, exist_ok=True)
        (target / "20260919-inc-01-depaaa-prerequisite.ipd.md").write_text(
            f"# IPD: prerequisite\n\n- Id: depaaa\n- Status: {status}\n",
            encoding="utf-8",
        )
        return repo

    def test_the_incident_shape_refuses(self):
        """substantially-complete in the run + plan still in pending/ must NOT release a dependent."""
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t), "pending", "approved")
            state = self._state(repo, "substantially-complete")
            satisfied, missing, reasons = oc_runipd.dependency_status_detailed(
                state["queue"][1], state
            )
            self.assertFalse(
                satisfied,
                "the 2026-09-19 incident: a dependent released against work that was never "
                "integrated, because the run status said substantially-complete while the plan sat "
                "in pending/",
            )
            self.assertEqual(missing, ["executed:depaaa"])
            self.assertNotIn(
                "in-run target",
                reasons["executed:depaaa"],
                "the refusal must come from the plan on DISK; the in-queue shortcut is deleted",
            )

    def test_a_genuinely_finalized_prerequisite_still_releases(self):
        """The fix must not strand a Set whose prerequisite really did finalize."""
        with tempfile.TemporaryDirectory() as t:
            repo = self._repo(Path(t), "executed", "executed")
            state = self._state(repo, "substantially-complete")
            satisfied, missing, _reasons = oc_runipd.dependency_status_detailed(
                state["queue"][1], state
            )
            self.assertTrue(
                satisfied,
                "a prerequisite in executed/ on disk satisfies the edge regardless of its in-run "
                "status, which is the whole point of making the directory the authority",
            )
            self.assertEqual(missing, [])

    def test_queue_membership_cannot_change_the_verdict(self):
        """The same on-disk state must give the same answer in-queue and out-of-queue.

        This is the property the OLD test file argued for in prose while pinning the opposite: it
        warned that a drifting state set would make a verdict "depend on QUEUE MEMBERSHIP - whether
        the target happens to be in this run - which the same spec paragraph explicitly prohibits".
        """
        for bucket, status, expected in (
            ("executed", "executed", True),
            ("pending", "approved", False),
        ):
            with self.subTest(bucket=bucket):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t), bucket, status)
                    in_queue = self._state(repo, "substantially-complete")
                    out_of_queue = {
                        "repo": str(repo),
                        "queue": [in_queue["queue"][1]],
                    }
                    a, _m = oc_runipd.dependency_status(in_queue["queue"][1], in_queue)
                    b, _m2 = oc_runipd.dependency_status(
                        out_of_queue["queue"][0], out_of_queue
                    )
                    self.assertEqual(a, expected)
                    self.assertEqual(
                        a,
                        b,
                        "queue membership changed the verdict for identical on-disk state",
                    )


if __name__ == "__main__":
    unittest.main()

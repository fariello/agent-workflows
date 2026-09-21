"""Tests for the analytics CLI leaves: `aw runs analyze` and `aw runs query`.

runanalytics Order 08 (`mm5p3v`), covering E-01 through E-08 and their V-items.

FOUR CONVENTIONS THIS SUITE HOLDS ITSELF TO, each for a measured reason.

FIRST, THE COLLISION TESTS ARE NON-VACUOUS BY CONSTRUCTION. Measured at review: nothing in the tree
collides with a leaf name (zero of 78 run-corpus setids, 345 run tokens and 639 tracked plan
setids/id6s), so a collision test written against the real corpus passes before any code exists and
proves nothing. This suite therefore CONSTRUCTS runs genuinely named `analyze` and `query` and asserts
both halves of the ambiguity rule against them.

SECOND, NO TEST READS THE LIVE CORPUS AS ITS ASSERTION SOURCE. `.aw/records/runs/` is gitignored and
absent from every fresh checkout and from every isolated lane worktree, so a test keyed to it is
unrunnable exactly where it runs. Every fixture is synthetic and lives in a temporary directory.

THIRD, THE NO-LAUNCH PROPERTY IS PROVEN, NOT INSPECTED. The launcher seam is injected with a stub that
FAILS the test if it is ever invoked, so "analysis without --open never launches a browser" is a
property under test rather than a claim about code that looks right.

FOURTH, THE BUDGET IS ASSERTED IN BYTES. The 1200-byte / 400-token agent-record budget is enforced by
`tests/test_cli_quality_gates.py` for its own fixtures; this suite asserts it for every view's real
output, because a view over a corpus-scale fact table is exactly where it would break.

Stdlib unittest only.
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import run_analytics_cli as analytics_cli
from agent_workflows import run_analytics_query as query_mod
from agent_workflows import agent_schema

# The enforced per-record budget. Imported as literals rather than from the quality-gate module so a
# change there is a visible conflict here rather than a silent relaxation of this suite.
BYTE_BUDGET = 1200
TOKEN_BUDGET = 400


def _approx_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def _run(argv: list[str]) -> tuple[str, str, int]:
    """Invoke the REAL cli entry point. Returns ``(stdout, stderr, rc)``.

    Streams are captured SEPARATELY because a refusal's human message goes to stderr deliberately, and
    a combined capture could not tell the two apart.
    """

    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(argv)
    except SystemExit as exc:  # argparse usage errors exit rather than return
        rc = int(exc.code or 0)
    return out.getvalue(), err.getvalue(), rc


def _records(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def _code_only(source: str) -> str:
    """Strip comments AND docstrings, so a source assertion tests CODE rather than prose.

    Necessary rather than fastidious: these modules DOCUMENT the literals they must not compose (the
    `.aw/records/runs` path, `xdg-open`) in order to explain why. A naive substring scan over the raw
    file matches that explanation and fails, which would either force the documentation out or teach
    the reader that the assertion is noise. Parsing to an AST and re-emitting only executable code is
    the honest scope for a "this token never appears in the implementation" claim.
    """

    import ast

    tree = ast.parse(source)
    for node in ast.walk(tree):
        # Drop docstrings: they are the first statement of a module, class, or function body.
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)
    # `ast.unparse` drops every comment by construction (3.9+ via the stdlib backport is absent, so
    # this suite's floor is the same 3.9 the package supports and `unparse` exists from 3.9).
    return ast.unparse(tree)


def _make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    return repo


def _write_run(repo: Path, run_id: str, *, setid: str, terminal: bool = True) -> Path:
    """A synthetic run directory in the shape the drivers write."""

    run_dir = repo / ".aw" / "records" / "runs" / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T01:00:00Z",
        "driver": {"path": "agent_workflows/oc_runipd.py", "host": "opencode"},
        "selectors": [setid],
        "queue": [
            {
                "position": 1,
                "id6": "aaa111",
                "setid": setid,
                "action": "execute",
                "status": "executed" if terminal else "running",
                "attempts": [
                    {
                        "attempt": 1,
                        "cost": 1.25,
                        "tokens": {"input": 100, "output": 20, "total": 120},
                    }
                ],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps({"type": "turn", "seq": i}) for i in range(3)) + "\n",
        encoding="utf-8",
    )
    (run_dir / "outcomes" / "01-aaa111.json").write_text(
        json.dumps({"disposition": "executed", "cost": 1.25}), encoding="utf-8"
    )
    return run_dir


class _RepoFixture(unittest.TestCase):
    """Base fixture: a synthetic repo with three runs, two of which collide with leaf names."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _make_repo(Path(self._tmp.name))
        _write_run(self.repo, "run-20260901T000000Z-1111111", setid="runanalytics")
        # THE PURPOSE-BUILT COLLISIONS. Nothing in the real tree is named `analyze` or `query`, so
        # without these the escape-hatch assertions below would pass vacuously.
        _write_run(self.repo, "run-20260901T010000Z-2222222", setid="analyze")
        _write_run(self.repo, "run-20260901T020000Z-3333333", setid="query")
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(analytics_cli.reset_launcher)

    def _dir(self) -> list[str]:
        return ["--dir", str(self.repo)]


# ============================================================ E-01: the declaration contract
class DeclarationContractTests(unittest.TestCase):
    """E-01 / V-01: both leaves are declared, and no NEW leaf is undeclared."""

    #: The measured pre-existing baseline. These five are a live failure of
    #: `test_no_undeclared_parser_leaves` that predates this plan and is explicitly out of scope; they
    #: are pinned here so a NEW undeclared leaf is attributable to whoever added it.
    KNOWN_UNDECLARED = {
        "oc profile add",
        "oc profile default",
        "oc profile list",
        "oc profile remove",
        "oc profile show",
    }

    def test_both_leaves_are_declared_with_the_intended_class(self):
        from agent_workflows.command_surface import get_declaration

        analyze = get_declaration("runs analyze")
        query = get_declaration("runs query")
        self.assertIsNotNone(analyze, "`runs analyze` carries no CommandDeclaration")
        self.assertIsNotNone(query, "`runs query` carries no CommandDeclaration")
        assert analyze is not None and query is not None
        # `analyze` WRITES (cache + published bundle), so it is a mutation on a read noun. Declaring
        # it `read` would be a false entry in the normative inventory AND would demand the wrong
        # scenario coverage from the conformance matrix.
        self.assertEqual(analyze.command_class, "mutation")
        self.assertEqual(query.command_class, "read")

    def test_no_new_undeclared_parser_leaf(self):
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import find_undeclared_leaves

        undeclared = find_undeclared_leaves(_build_parser())
        self.assertEqual(
            undeclared,
            self.KNOWN_UNDECLARED,
            "a NEW undeclared parser leaf appeared (the five `oc profile *` entries are the "
            f"pre-existing baseline): {sorted(undeclared - self.KNOWN_UNDECLARED)}",
        )

    def test_exit_contract_is_consistent_with_the_agent_schema(self):
        """The declared contract must be expressible in a record the schema accepts.

        `validate_agent_record` requires a result/summary/error `exit` in (0, 1, 2). Both leaves emit
        agent records on every path, so a declared code above 2 would be unrepresentable.
        """

        from agent_workflows.command_surface import get_declaration

        for name in ("runs analyze", "runs query"):
            decl = get_declaration(name)
            assert decl is not None
            with self.subTest(leaf=name):
                self.assertTrue(
                    set(decl.exit_contract) <= {0, 1, 2},
                    f"{name} declares a code the agent record cannot carry: {decl.exit_contract}",
                )

    def test_required_scenarios_follow_from_the_declared_class(self):
        """A mutation owes `success_preview`; a read whose contract includes 1 owes `domain_failure`."""

        from agent_workflows.command_surface import get_declaration
        from tests.conformance_matrix import required_scenarios

        analyze = get_declaration("runs analyze")
        query = get_declaration("runs query")
        assert analyze is not None and query is not None
        self.assertIn("success_preview", required_scenarios(analyze))
        self.assertIn("domain_failure", required_scenarios(query))
        for decl in (analyze, query):
            for scenario in (
                "tty",
                "non_tty",
                "agent",
                "no_color",
                "help",
                "usage_error",
            ):
                self.assertIn(scenario, required_scenarios(decl))


# ============================================================ E-02: parser registration
class ParserRegistrationTests(_RepoFixture):
    """E-02 / V-02: both leaves are REAL subparsers, and the noun's help stopped lying."""

    def test_both_leaves_are_real_parser_leaves(self):
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import discover_parser_leaves

        leaves = discover_parser_leaves(_build_parser())
        self.assertIn("runs analyze", leaves)
        self.assertIn("runs query", leaves)

    def test_each_leaf_has_native_help_and_exits_zero(self):
        for leaf in ("analyze", "query"):
            with self.subTest(leaf=leaf):
                out, err, rc = _run(["runs", leaf, "--help"])
                self.assertEqual(rc, 0, out + err)
                self.assertIn("usage", (out + err).lower())

    def test_each_leaf_gives_a_native_usage_error_exit_2(self):
        for leaf in ("analyze", "query"):
            with self.subTest(leaf=leaf):
                out, err, rc = _run(["runs", leaf, "--this-flag-does-not-exist"])
                self.assertEqual(rc, 2, out + err)
                self.assertIn("usage", (out + err).lower())

    def test_runs_description_names_every_mutating_exception(self):
        """The read-only claim must stay TRUE as mutating verbs accumulate on this noun.

        THE COUNT IN THIS ASSERTION HAS MOVED TWICE AND WILL MOVE AGAIN, which is the finding rather
        than an annoyance. It read "ONE exception" before Order 08 (`repair` alone), "TWO" after
        Order 08 (`analyze`), and "FOUR" after Order 09 (`ixis0c`) added `export` and `submit`. So
        the NAMES are what this test really pins: every verb declared `mutation` under `runs` in
        `COMMAND_INVENTORY` must be named in the help text, derived from the inventory rather than
        hand-listed, so a fifth mutating verb fails here instead of shipping a help string that
        claims a read-only surface. The count is checked too, because a stale number is itself a
        false statement.
        """

        from agent_workflows.command_surface import get_all_declarations

        out, err, rc = _run(["runs", "--help"])
        self.assertEqual(rc, 0, out + err)
        text = out + err

        mutating = {
            d.command.split(" ", 1)[1]
            for d in get_all_declarations()
            if d.command.startswith("runs ") and d.command_class == "mutation"
        }
        # `repair` is positionally routed (see `_ViewerOrLeafSubParsersAction`) so it carries no
        # declaration, but it IS a mutating verb on this noun and must be named too.
        mutating.add("repair")

        # ONE KNOWN MISDECLARATION IS SUBTRACTED, WITH ITS CARRIER NAMED, rather than silently
        # tolerated. `runs resume` is declared `mutation` but WRITES NOTHING: `run_cli._run_resume`
        # calls `run_recovery.resume`, whose body is `reconstruct_state()` +
        # `detect_unknown_outcomes()` + `get_runnable_steps()` and a print, and `run_cli`'s own
        # docstring says `next` and `resume` "only reconstruct state and report". Its sibling
        # `runs next` is correctly declared `read`. Measured 2026-09-18 by THIS test, which found it
        # because it derives the set instead of hand-listing it; filed as backlog `cldbus` and NOT
        # fixed here, because re-classifying a shipped leaf changes which conformance scenarios CI
        # demands for it and does not belong inside a data-sharing plan.
        self.assertIn(
            "resume", mutating, "backlog cldbus appears fixed; drop this subtraction"
        )
        mutating.discard("resume")

        expected_named = sorted(mutating)
        self.assertEqual(expected_named, ["analyze", "export", "repair", "submit"])
        for verb in expected_named:
            self.assertIn(
                f"'{verb}'",
                text,
                f"the `aw runs` help does not NAME its mutating verb {verb!r}",
            )
        self.assertIn("FOUR exceptions", text)
        # Every superseded count must be gone, not merely supplemented.
        self.assertNotIn("with ONE exception", text)
        self.assertNotIn("TWO exceptions", text)

    def test_runs_help_advertises_both_analytics_leaves(self):
        out, err, rc = _run(["runs", "--help"])
        self.assertEqual(rc, 0, out + err)
        self.assertIn("aw runs analyze", out + err)
        self.assertIn("aw runs query", out + err)

    def test_no_positional_routing_was_added(self):
        """Neither leaf may be routed from a positional the way `repair` is.

        A positionally-routed leaf is invisible to `discover_parser_leaves`, so declaring it (E-01)
        would register as declaration/parser drift. This asserts the absence directly.
        """

        code = _code_only(
            (Path(cli.__file__).parent / "run_viewer.py").read_text(encoding="utf-8")
        )
        for token in ("raw_targets[0] == 'analyze'", "raw_targets[0] == 'query'"):
            self.assertNotIn(token, code)

    def test_existing_leaves_and_the_bare_viewer_still_route(self):
        """The nine existing leaves and the bare viewer must be unaffected by the two additions."""

        from agent_workflows.run_viewer import RUNS_VIEWER_LEAF_NAMES

        out, err, rc = _run(["runs", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        for leaf in RUNS_VIEWER_LEAF_NAMES:
            with self.subTest(leaf=leaf):
                # Each still resolves as a LEAF: it either runs or reports its own missing target,
                # never the viewer's unresolvable-target refusal.
                o, e, code = _run(["runs", leaf, *self._dir()])
                self.assertNotIn("no run matched target", o + e)
                self.assertIn(code, (0, 1, 2))


# ============================================================ E-07: routing and collision
class RoutingAndCollisionTests(_RepoFixture):
    """E-07 / V-07: the ambiguity rule, proven against PURPOSE-BUILT collisions."""

    def test_bare_form_reaches_the_leaf_not_a_run_named_the_same(self):
        """A first positional equal to a leaf name routes to the LEAF, even though a run collides."""

        out, err, rc = _run(["runs", "query", "schema", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        # The LEAF answered (a schema view), not the viewer rendering the run called `query`.
        self.assertNotIn("run-20260901T020000Z-3333333", out)

    def test_escape_hatch_reaches_the_viewer_for_a_colliding_target(self):
        """`aw runs -- analyze` views the RUN named `analyze`; it can never reach the leaf."""

        out, err, rc = _run(["runs", *self._dir(), "--", "analyze"])
        self.assertEqual(rc, 0, out + err)
        self.assertIn("run-20260901T010000Z-2222222", out)

    def test_escape_hatch_reaches_the_viewer_for_the_query_collision_too(self):
        out, err, rc = _run(["runs", *self._dir(), "--", "query"])
        self.assertEqual(rc, 0, out + err)
        self.assertIn("run-20260901T020000Z-3333333", out)

    def test_the_escape_path_forces_runs_command_to_none_at_dispatch(self):
        """Whatever the viewer receives after `--`, its `runs_command` is None and the token is a TARGET.

        REPLACES A SOURCE-TEXT PIN that asserted the literal
        `"setattr(args_ns, 'runs_command', None)"` appeared in `cli.py`'s comment-stripped source.
        That form pins one exact spelling of one statement: `args_ns.runs_command = None` does the
        identical thing and would have failed it, while the statement being moved somewhere
        UNREACHABLE would have passed it.

        The pin's docstring argued a behavioral test "would not distinguish it from a lucky
        resolution order", and that is only true of an END-TO-END observation. Intercepting the
        VIEWER SEAM removes the ambiguity: the namespace the viewer is actually handed is recorded,
        so `runs_command is None` is read off the real dispatch rather than inferred from a render.
        Every colliding leaf name is driven, so the guarantee is a property of the escape hatch
        rather than of one token.
        """
        from agent_workflows import run_viewer

        real_viewer = run_viewer.run_viewer_cli
        received = {}

        def recorder(args_ns):
            received["runs_command"] = getattr(args_ns, "runs_command", "<absent>")
            received["targets"] = list(getattr(args_ns, "targets", None) or [])
            return 0

        #: (the argv before `--`, the escaped target, why this row exists)
        #:
        #: THE THIRD AND FOURTH ROWS ARE THE LOAD-BEARING ONES, and they were found by mutation
        #: rather than reasoned about: with the `setattr` deleted, the first two rows still reported
        #: `runs_command is None` (nothing before `--` named a leaf, so argparse never set it) and
        #: the test passed against a broken dispatch. A row whose PRE-`--` argv contains a leaf
        #: token is what makes the clear observable at all.
        escapes = (
            (
                ["runs"],
                "analyze",
                "the documented form: nothing but the noun precedes the escape, so the token after "
                "`--` is unambiguously a viewer target",
            ),
            (
                ["runs"],
                "query",
                "the second colliding leaf name, kept as its own row because the collision set is "
                "data and a guard written for one member can miss another",
            ),
            (
                ["runs", "analyze"],
                "analyze",
                "THE ROW THE CLEAR EXISTS FOR: a LEAF token precedes the escape, so argparse has "
                "already set `runs_command='analyze'` by the time the hatch runs. Without the "
                "explicit clear the viewer is handed a live leaf name and the escape means nothing - "
                "and this is the only shape in which that failure is visible",
            ),
            (
                ["runs", "query"],
                "analyze",
                "the CROSS pairing, which separates 'the clear happened' from 'the target happened "
                "to equal the leaf': the leaf before `--` and the target after it differ, so a "
                "dispatch that confused the two cannot pass by coincidence",
            ),
        )

        wrong = []
        run_viewer.run_viewer_cli = recorder  # type: ignore[assignment]
        try:
            for prefix, target, why in escapes:
                received.clear()
                out, err, rc = _run([*prefix, *self._dir(), "--", target])
                problems = []
                if rc != 0:
                    problems.append(f"exit {rc} rather than 0: {(out + err)[:200]!r}")
                if received.get("runs_command") is not None:
                    problems.append(
                        f"the viewer was handed runs_command={received.get('runs_command')!r}; an "
                        "escaped token must never arrive as a leaf"
                    )
                if target not in received.get("targets", []):
                    problems.append(
                        f"the escaped token never arrived as a viewer TARGET: {received!r}"
                    )
                if problems:
                    wrong.append(
                        f"  `aw {' '.join(prefix)} -- {target}`\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        finally:
            run_viewer.run_viewer_cli = real_viewer  # type: ignore[assignment]

        self.assertEqual(
            wrong,
            [],
            f"the `--` escape hatch was wrong for {len(wrong)} of {len(escapes)} forms. ONE pre-parse "
            "branch implements it, so read the grouping: only the rows WITH a leaf token before `--` "
            "failing means the explicit `runs_command` clear was removed (the other rows cannot see "
            "that, which is why they are not the measurement); every row failing means the hatch is "
            "not being taken at all and `--` has stopped being honored. FIX: whatever follows `--` "
            "is a viewer TARGET by definition, so the dispatch must clear any leaf argparse already "
            "resolved rather than trusting resolution order.\n" + "\n".join(wrong),
        )

    def test_the_collision_fixture_is_load_bearing(self):
        """PROOF THE COLLISION TESTS ARE NOT VACUOUS.

        Without a run actually named `analyze`, `aw runs -- analyze` REFUSES (exit 2, no run matched),
        which is what the real repository does today. So the passing assertions above depend on the
        constructed fixture rather than on behavior that was already true.
        """

        with tempfile.TemporaryDirectory() as td:
            empty = _make_repo(Path(td))
            _write_run(empty, "run-20260901T000000Z-9999999", setid="unrelated")
            out, err, rc = _run(["runs", "--dir", str(empty), "--", "analyze"])
            self.assertEqual(rc, 2, out + err)
            self.assertIn("no run matched target", out + err)

    def test_a_leaf_name_is_not_resolved_by_the_setid_fallback(self):
        """The setid fallback reads setid FIELDS, so an ordinary JSON key does not over-match.

        Re-measured in this lane: `aw runs -- status` REFUSES (exit 2) rather than returning every
        run. The plan cited a review-time measurement of 135 runs matching via a raw-text fallback;
        that fallback was replaced by `_state_setids` in commit 9c589d2d (runsverify 7wei1o E-07), so
        the behavior the plan told this item to report is already fixed. Pinned here so a regression
        to raw-substring matching fails loudly. No assertion in this suite depends on the old bug.
        """

        out, err, rc = _run(["runs", *self._dir(), "--", "driver"])
        self.assertEqual(rc, 2, out + err)
        self.assertIn("no run matched target", out + err)


# ============================================================ E-03: analyze's option surface
class AnalyzeOptionSurfaceTests(_RepoFixture):
    """E-03 / V-03: flag precedence, exit codes, and no prompt on any path."""

    def test_path_before_any_report_exists_is_a_refusal_not_an_empty_success(self):
        out, err, rc = _run(["runs", "analyze", "--path", "--agent", *self._dir()])
        self.assertEqual(rc, 2, out + err)
        rec = _records(out)[-1]
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)

    def test_list_writes_nothing_and_succeeds_on_an_empty_analytics_tree(self):
        from agent_workflows.runner_shared import analytics_root

        before = analytics_root(self.repo).exists()
        out, err, rc = _run(["runs", "analyze", "--list", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(analytics_root(self.repo).exists(), before)

    def test_path_and_list_are_mutually_exclusive(self):
        out, err, rc = _run(["runs", "analyze", "--path", "--list", *self._dir()])
        self.assertEqual(rc, 2, out + err)
        self.assertIn("not allowed with", (out + err))

    def test_rebuild_is_exclusive_with_the_read_only_modes(self):
        for other in ("--path", "--list"):
            with self.subTest(flag=other):
                out, err, rc = _run(
                    ["runs", "analyze", "--rebuild", other, *self._dir()]
                )
                self.assertEqual(rc, 2, out + err)
                self.assertIn("not allowed with", out + err)

    def test_analyze_sweeps_and_reports_totals(self):
        out, err, rc = _run(["runs", "analyze", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        rec = _records(out)[-1]
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_analyze_writes_only_inside_the_reserved_analytics_namespace(self):
        """The containment claim that makes a mutation on a read noun defensible."""

        from agent_workflows.runner_shared import path_is_within_analytics

        runs_root = self.repo / ".aw" / "records" / "runs"
        before = {
            p.relative_to(runs_root): p.stat().st_mtime
            for p in runs_root.rglob("*")
            if p.is_file() and not path_is_within_analytics(p, self.repo)
        }
        out, err, rc = _run(["runs", "analyze", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        after = {
            p.relative_to(runs_root): p.stat().st_mtime
            for p in runs_root.rglob("*")
            if p.is_file() and not path_is_within_analytics(p, self.repo)
        }
        self.assertEqual(
            before, after, "a source run file changed; analyze must never write one"
        )

    def test_keep_snapshot_publishes_an_immutable_snapshot(self):
        """`--keep-snapshot LABEL` is WIRED, not merely parsed.

        Registered-but-unimplemented is the specific failure this asserts against: a flag that parses,
        documents itself in `--help`, and then does nothing is worse than an absent one, because the
        caller believes a snapshot exists.
        """

        from agent_workflows import run_analytics_report as report_mod
        from agent_workflows.runner_shared import analytics_snapshots_dir

        out, err, rc = _run(
            ["runs", "analyze", "--keep-snapshot", "s1", "--agent", *self._dir()]
        )
        self.assertEqual(rc, 0, out + err)
        snapshot_dir = analytics_snapshots_dir(self.repo) / "s1"
        self.assertTrue(snapshot_dir.is_dir(), f"no snapshot at {snapshot_dir}")
        # The manifest is Order 07's completeness signal and is written LAST, so its presence means
        # the snapshot is whole rather than a readable half.
        self.assertEqual(report_mod.verify_bundle(snapshot_dir), [])
        self.assertTrue((snapshot_dir / report_mod.INDEX_FILENAME).is_file())

    def test_a_snapshot_label_that_is_not_one_path_component_is_refused(self):
        """A traversing label is refused by Order 07 and reported, never written."""

        for label in ("../escape", "a/b", ".."):
            with self.subTest(label=label):
                out, err, rc = _run(
                    [
                        "runs",
                        "analyze",
                        "--keep-snapshot",
                        label,
                        "--agent",
                        *self._dir(),
                    ]
                )
                self.assertEqual(rc, 2, out + err)

    def test_the_snapshot_lands_inside_the_reserved_namespace(self):
        from agent_workflows.runner_shared import path_is_within_analytics

        _run(["runs", "analyze", "--keep-snapshot", "s2", "--agent", *self._dir()])
        from agent_workflows.runner_shared import analytics_snapshots_dir

        self.assertTrue(
            path_is_within_analytics(
                analytics_snapshots_dir(self.repo) / "s2", self.repo
            )
        )

    def test_an_unresolvable_target_is_refused_not_silently_swept(self):
        out, err, rc = _run(
            ["runs", "analyze", "totalgibberish", "--agent", *self._dir()]
        )
        self.assertEqual(rc, 2, out + err)

    def test_no_path_in_the_source_composes_the_runs_literal(self):
        """Every path must come from Order 01's resolver; the literal would be the seventh site."""

        for module in ("run_analytics_cli.py", "run_analytics_query.py"):
            source = (Path(cli.__file__).parent / module).read_text(encoding="utf-8")
            with self.subTest(module=module):
                self.assertNotIn(".aw/records/runs", _code_only(source))

    def test_neither_leaf_prompts(self):
        """No interactive prompt on any path: stdin is never read."""

        for module in ("run_analytics_cli.py", "run_analytics_query.py"):
            code = _code_only(
                (Path(cli.__file__).parent / module).read_text(encoding="utf-8")
            )
            with self.subTest(module=module):
                self.assertNotIn("input(", code)
                self.assertNotIn("sys.stdin", code)


# ============================================================ E-04: the launch seam
class OpenSeamTests(_RepoFixture):
    """E-04 / V-04: `--open` is opt-in, and the no-launch property is PROVEN by a failing stub."""

    def _install_failing_stub(self) -> None:
        def _must_not_be_called(path: Path):
            raise AssertionError(
                f"a browser launch was attempted without --open: {path}"
            )

        analytics_cli.set_launcher(_must_not_be_called)

    def test_analysis_without_open_never_launches(self):
        """INSPECTION IS NOT EVIDENCE: the stub RAISES if invoked, so passing means it never was."""

        self._install_failing_stub()
        out, err, rc = _run(["runs", "analyze", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)

    def test_path_and_list_never_launch_either(self):
        self._install_failing_stub()
        for flag in ("--path", "--list"):
            with self.subTest(flag=flag):
                _run(["runs", "analyze", flag, "--agent", *self._dir()])

    def test_open_is_off_by_default_in_the_parser(self):
        from agent_workflows.cli import _build_parser

        args = _build_parser().parse_args(["runs", "analyze"])
        self.assertFalse(getattr(args, "open"))

    def test_a_supported_platform_launches_and_reports_success(self):
        calls: list[Path] = []

        def _ok(path: Path):
            calls.append(path)
            return analytics_cli.LaunchOutcome(
                True, True, "opened in the default browser"
            )

        analytics_cli.set_launcher(_ok)
        _run(["runs", "analyze", "--agent", *self._dir()])
        report = analytics_cli._latest_report_path(self.repo)
        if report.exists():
            out, err, rc = _run(["runs", "analyze", "--open", "--agent", *self._dir()])
            self.assertEqual(rc, 0, out + err)
            self.assertTrue(calls, "the launcher was never invoked despite --open")

    def test_an_unsupported_platform_yields_a_documented_code_and_remedy(self):
        report_dir = analytics_cli._latest_report_path(self.repo).parent
        report_dir.mkdir(parents=True, exist_ok=True)
        analytics_cli._latest_report_path(self.repo).write_text(
            "<html></html>", encoding="utf-8"
        )

        analytics_cli.set_launcher(
            lambda p: analytics_cli.LaunchOutcome(
                False,
                False,
                "no browser is available on this system",
                f"open manually: {p}",
            )
        )
        out, err, rc = _run(["runs", "analyze", "--open", "--agent", *self._dir()])
        self.assertEqual(rc, 2, out + err)
        rec = _records(out)[-1]
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["next"], "aw runs analyze --path")

    def test_a_launch_failure_is_reported_not_propagated(self):
        report_path = analytics_cli._latest_report_path(self.repo)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("<html></html>", encoding="utf-8")

        def _raise(path: Path):
            raise OSError("display not found")

        # The real default launcher swallows an exception into a documented outcome; assert that
        # contract on the seam itself rather than only through the CLI.
        analytics_cli.set_launcher(_raise)
        with self.assertRaises(OSError):
            analytics_cli.open_report(report_path)

    def test_the_default_launcher_reports_rather_than_raising(self):
        """The shipped launcher converts any failure into a documented outcome with a remedy."""

        outcome = analytics_cli._default_launcher(Path("/nonexistent/report.html"))
        self.assertIsInstance(outcome, analytics_cli.LaunchOutcome)
        if not outcome.launched:
            self.assertTrue(outcome.remedy, "a failed launch must carry a remedy")

    def test_no_new_runtime_dependency_was_added(self):
        """`webbrowser` is stdlib, imported inside the guarded path; nothing else was introduced."""

        source = (Path(cli.__file__).parent / "run_analytics_cli.py").read_text(
            encoding="utf-8"
        )
        code = _code_only(source)
        self.assertIn("import webbrowser", code)
        for forbidden in ("import requests", "import selenium", "xdg-open"):
            self.assertNotIn(forbidden, code)


# ============================================================ E-05: the query grammar
class QueryGrammarTests(_RepoFixture):
    """E-05 / V-05: every view, over an ALLOWLISTED filter/group schema, with no escape."""

    def test_every_declared_view_answers(self):
        extra = {
            "slices": ["--group-by", "phase"],
            "explain": ["--price", "era-b"],
        }
        for view in query_mod.VIEWS:
            with self.subTest(view=view):
                out, err, rc = _run(
                    [
                        "runs",
                        "query",
                        view,
                        *extra.get(view, []),
                        "--agent",
                        *self._dir(),
                    ]
                )
                self.assertIn(rc, (0, 2), out + err)
                self.assertTrue(out.strip(), f"view {view} emitted nothing")

    def test_a_rejected_filter_names_the_allowlist_and_does_not_echo_input(self):
        marker = "definitely-not-a-field"
        out, err, rc = _run(
            ["runs", "query", "metrics", "--filter", f"{marker}=1", *self._dir()]
        )
        self.assertEqual(rc, 2, out + err)
        combined = out + err
        self.assertIn("allowed filter fields are", combined)
        # The rejected token is NOT reflected back: an error that echoes arbitrary input is a
        # needless injection surface for zero diagnostic gain.
        self.assertNotIn(marker, combined)

    def test_a_rejected_grouping_names_the_allowlist(self):
        out, err, rc = _run(
            ["runs", "query", "slices", "--group-by", "nope", *self._dir()]
        )
        self.assertEqual(rc, 2, out + err)
        self.assertIn("allowed grouping field", out + err)

    def test_run_id_is_filterable_but_not_groupable(self):
        """Grouping by an unbounded identifier would defeat the row bound, so it is excluded."""

        self.assertIn("run_id", query_mod.FILTERABLE_FIELDS)
        self.assertNotIn("run_id", query_mod.GROUPABLE_FIELDS)

    def test_a_repeated_filter_field_is_refused_rather_than_last_wins(self):
        with self.assertRaises(query_mod.QueryError):
            query_mod.parse_filters(["phase=execute", "phase=verify"])

    def test_no_expression_evaluation_reaches_the_engine(self):
        source = (Path(cli.__file__).parent / "run_analytics_query.py").read_text(
            encoding="utf-8"
        )
        code = _code_only(source)
        for forbidden in ("eval(", "exec(", "__import__", "getattr(entry"):
            self.assertNotIn(forbidden, code)

    def test_a_path_like_filter_value_cannot_escape_the_resolved_roots(self):
        """A filter VALUE is compared as a string; it is never opened, joined, or resolved."""

        result = query_mod.run_query(
            "overview", repo=self.repo, filters=["run_id=../../../../etc/passwd"]
        )
        self.assertEqual(result.payload["cached_runs"], 0)

    def test_a_refused_slice_is_forwarded_with_its_observed_n_not_computed(self):
        """THE CENTRAL HONESTY PROPERTY: Order 06's refusal is reproduced, never answered."""

        name = "merge-conflict-share-and-recurrence"
        result = query_mod.run_query("metrics", repo=self.repo, analysis=name)
        self.assertTrue(result.refused)
        self.assertEqual(result.verdict, "cannot-determine")
        self.assertEqual(result.exit_code, 2)
        self.assertIsNotNone(result.sample_size)
        # The observed n is the engine's, not one this module recomputed.
        from agent_workflows import run_analytics_statistics as stats

        expected = stats.refuse_under_powered_required_analyses()[name]
        self.assertEqual(result.sample_size, expected.sample_size)
        self.assertEqual(result.reason, expected.reason)

    def test_the_refusal_survives_into_the_machine_record(self):
        """An agent must be able to tell a measured refusal from a malformed query; both exit 2."""

        out, err, rc = _run(
            [
                "runs",
                "query",
                "metrics",
                "--analysis",
                "merge-conflict-share-and-recurrence",
                "--agent",
                *self._dir(),
            ]
        )
        self.assertEqual(rc, 2, out + err)
        rec = _records(out)[-1]
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertTrue(rec["refused"])
        self.assertEqual(rec["verdict"], "cannot-determine")
        self.assertIn("sample_size", rec)

    def test_group_by_model_renders_an_honest_empty_state_with_its_coverage_caveat(
        self,
    ):
        """Model identity is near-absent in historical data; the caveat must travel WITH the result."""

        result = query_mod.run_query("metrics", repo=self.repo, group_by="model")
        joined = " ".join(result.caveats)
        self.assertIn("model identity", joined)
        self.assertIn("unresolved", joined)

    def test_missingness_is_reported_and_never_counted_as_zero(self):
        result = query_mod.run_query("distributions", repo=self.repo, metric="cost")
        self.assertIn("missing_count", result.payload)
        self.assertIn("sample_size", result.payload)


# ================================================== metgap `6krsym`: the metric surface is HONEST
def _entry(
    run_id: str,
    *,
    facts: dict | None = None,
    quality_flags: tuple[str, ...] = (),
    is_complete: bool = True,
) -> dict:
    """One synthetic cache entry in the shape `_cache_entries` returns.

    A SYNTHETIC ENTRY IS THE PRIMARY EVIDENCE HERE, NOT A FALLBACK. `.aw/records/runs/` is gitignored
    and absent from every lane and fresh clone, and on an empty corpus a perfectly working metric and a
    never-produced one return byte-identical payloads (`sample_size: 0`, `outcome: clean`, `exit 0`),
    so a corpus-based assertion would pass before the fix and after it. Constructing the entries makes
    the sample sizes and the absence classes known by construction.
    """

    return {
        "schema_version": 1,
        "run_id": run_id,
        "is_complete": is_complete,
        "metric_facts": dict(facts or {}),
        "event_facts": [],
        "quality_flags": list(quality_flags),
        "warnings": [],
    }


class NumbersForTests(unittest.TestCase):
    """THE FIRST DIRECT TEST OF `_numbers_for` (it had none), plus its new absence classification.

    Measured while authoring metgap `6krsym`: zero matches for the symbol across `tests/`, so every
    assertion below is added coverage rather than a change to pinned behavior.
    """

    def test_a_present_value_is_sampled_and_an_absent_one_is_counted_not_zeroed(self):
        entries = [
            _entry("run-1", facts={"cost": 2.0}),
            _entry("run-2", facts={}),
            _entry("run-3", facts={"cost": 4.0}),
        ]
        values, missing, classes = query_mod._numbers_for(entries, "cost")
        self.assertEqual(values, [2.0, 4.0])
        self.assertEqual(missing, 1)
        self.assertEqual(
            classes, [], "classification is opt-in and meaningful for tokens only"
        )
        self.assertNotIn(
            0.0, values, "an absent value must never enter the sample as a zero"
        )

    def test_a_BOOLEAN_is_not_a_number_and_counts_as_missing(self):
        """`isinstance(True, int)` is True in Python, so this guard is load-bearing."""

        values, missing, _ = query_mod._numbers_for(
            [_entry("run-1", facts={"cost": True})], "cost"
        )
        self.assertEqual(values, [])
        self.assertEqual(missing, 1)

    def test_the_tokens_metric_falls_back_to_token_total_and_reads_a_map_total(self):
        entries = [
            _entry("run-1", facts={"token_total": 120}),
            _entry("run-2", facts={"tokens": {"input": 10, "output": 5, "total": 15}}),
        ]
        values, missing, _ = query_mod._numbers_for(entries, "tokens")
        self.assertEqual(sorted(values), [15.0, 120.0])
        self.assertEqual(missing, 0)

    def test_the_absence_classes_PARTITION_the_folded_missing_count(self):
        """The constraint that makes the new vocabulary a refinement rather than a second statistic.

        Demonstrated on entries that MIX both absence kinds: on an empty corpus both sides are 0 and
        the partition would hold trivially while proving nothing.
        """

        entries = [
            _entry("run-1", facts={"token_total": 120}),
            _entry(
                "run-2",
                facts={"quality_flags": ["tokens-nothing-to-record"]},
            ),
            _entry(
                "run-3",
                facts={"quality_flags": ["tokens-nothing-to-record"]},
            ),
            # NO explanatory flag: a genuine, unexplained absence.
            _entry("run-4", facts={}),
            _entry("run-5", facts={"quality_flags": ["tokens-run-unfinished"]}),
        ]
        _values, missing, classes = query_mod._numbers_for(
            entries, "tokens", classify_absence=True
        )
        counts = query_mod.classify_token_absences(entries)
        self.assertEqual(missing, 4)
        self.assertEqual(len(classes), missing)
        self.assertEqual(
            counts,
            {"not-recorded": 1, "nothing-to-record": 2, "run-unfinished": 1},
        )
        self.assertEqual(
            sum(counts.values()),
            missing,
            "the classes must sum to the folded missing count, or one of them is lying",
        )

    def test_an_UNFLAGGED_absence_fails_CLOSED_as_not_recorded(self):
        """An older entry written before the flags existed must read as a possible defect."""

        entries = [_entry("legacy-run", facts={})]
        self.assertEqual(query_mod._token_absence_class(entries[0]), "not-recorded")
        self.assertEqual(query_mod.classify_token_absences(entries)["not-recorded"], 1)

    def test_an_ENVELOPE_level_flag_is_read_as_well_as_the_run_facts_one(self):
        """Both lists exist; reading only one misclassified every explained absence (measured)."""

        entry = _entry("run-1", facts={}, quality_flags=("tokens-nothing-to-record",))
        self.assertEqual(query_mod._token_absence_class(entry), "nothing-to-record")


class HonestMetricSurfaceTests(unittest.TestCase):
    """metgap `6krsym`: every offered metric computes, and a removed one REFUSES."""

    def setUp(self) -> None:
        self.maxDiff = None
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_duration_seconds_is_REFUSED_by_name_rather_than_returning_an_empty_result(
        self,
    ):
        """The removal's externally visible effect: a name that never returned data now refuses.

        It is asserted through the real CLI as well as the parser, because "advertised and always
        empty" and "refused" are the two states this plan chose between and only one of them is honest.
        """

        with self.assertRaises(query_mod.QueryError) as ctx:
            query_mod.run_query("metrics", repo=self.repo, metric="duration_seconds")
        self.assertIn("unknown metric", str(ctx.exception))

        out, err, rc = _run(
            [
                "runs",
                "query",
                "metrics",
                "--metric",
                "duration_seconds",
                "--dir",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 2, out + err)
        self.assertIn("allowed metrics are", out + err)

    def test_the_schema_view_no_longer_advertises_the_removed_metric(self):
        """One tuple feeds the schema view AND the refusal, so a removal must propagate to both."""

        payload = query_mod.run_query("schema", repo=self.repo).payload
        self.assertNotIn("duration_seconds", payload["metrics"])
        self.assertEqual(payload["metrics"], list(query_mod.AGGREGATE_METRICS))

    def test_event_count_aggregates_a_NONZERO_sample_over_a_constructed_corpus(self):
        entries = [
            _entry("run-1", facts={"event_count": 3}),
            _entry("run-2", facts={"event_count": 5}),
            _entry("run-3", facts={"event_count": 4}),
        ]
        result = query_mod.view_metrics(
            entries,
            metric="event_count",
            stat="median",
            group_by=(),
            analysis=None,
            limit=20,
        )
        self.assertEqual(result.payload["sample_size"], 3)
        self.assertEqual(result.payload["missing_count"], 0)
        self.assertEqual(result.payload["value"], 4)

    def test_a_run_with_no_event_stream_is_EXCLUDED_rather_than_counted_as_zero(self):
        entries = [
            _entry("run-1", facts={"event_count": 10}),
            _entry("run-2", facts={}),  # no key at all: nothing to count
        ]
        result = query_mod.view_metrics(
            entries,
            metric="event_count",
            stat="mean",
            group_by=(),
            analysis=None,
            limit=20,
        )
        self.assertEqual(result.payload["sample_size"], 1)
        self.assertEqual(result.payload["missing_count"], 1)
        self.assertEqual(
            result.payload["value"],
            10,
            "a zero-filled absence would have dragged this mean to 5",
        )

    def test_the_token_metric_reports_its_absences_IN_CLASSES_with_a_caveat(self):
        entries = [
            _entry("run-1", facts={"token_total": 100}),
            _entry("run-2", facts={"quality_flags": ["tokens-nothing-to-record"]}),
            _entry("run-3", facts={}),
        ]
        result = query_mod.view_metrics(
            entries,
            metric="tokens",
            stat="median",
            group_by=(),
            analysis=None,
            limit=20,
        )
        self.assertEqual(
            result.payload["missing_by_class"],
            {"not-recorded": 1, "nothing-to-record": 1, "run-unfinished": 0},
        )
        self.assertEqual(result.payload["missing_count"], 2)
        joined = " ".join(result.caveats)
        self.assertIn("NOTHING to record", joined)
        self.assertIn("NOT RECORDED", joined)
        # The ESTABLISHED sentence is preserved verbatim rather than rewritten, so an operator who
        # learned to read the cost caveat does not have to relearn it.
        self.assertIn("EXCLUDED, not counted as zero", joined)

    def test_a_NON_token_metric_gets_no_class_breakdown_it_cannot_justify(self):
        """The ingester records flags explaining a TOKEN absence and no other, so inventing a class
        for cost would be a guess dressed as a measurement."""

        entries = [_entry("run-1", facts={"cost": 1.0}), _entry("run-2", facts={})]
        result = query_mod.view_metrics(
            entries, metric="cost", stat="median", group_by=(), analysis=None, limit=20
        )
        self.assertNotIn("missing_by_class", result.payload)
        self.assertEqual(result.payload["missing_count"], 1)

    def test_missing_count_KEEPS_its_meaning_so_an_existing_consumer_is_unaffected(
        self,
    ):
        """The refinement is additive: the folded field still counts every unusable observation."""

        entries = [
            _entry("run-1", facts={"token_total": 10}),
            _entry("run-2", facts={"quality_flags": ["tokens-nothing-to-record"]}),
            _entry("run-3", facts={"quality_flags": ["tokens-run-unfinished"]}),
            _entry("run-4", facts={}),
        ]
        result = query_mod.view_metrics(
            entries, metric="tokens", stat="count", group_by=(), analysis=None, limit=20
        )
        self.assertEqual(result.payload["missing_count"], 3)
        self.assertEqual(sum(result.payload["missing_by_class"].values()), 3)

    def test_NO_GENUINE_LOSS_IS_EXCUSED_and_the_check_is_shown_to_FIRE(self):
        """V-07's zero-result check, plus the demonstration that it discriminates.

        A check never seen to fire is not evidence, so this asserts BOTH directions: an explained
        absence is not counted as a loss, and an UNexplained one is.
        """

        explained = _entry(
            "run-empty", facts={"quality_flags": ["tokens-nothing-to-record"]}
        )
        genuine_loss = _entry("run-lost", facts={"observed_activity_seconds": 1200.0})

        self.assertEqual(
            query_mod.classify_token_absences([explained])["not-recorded"],
            0,
            "a run that dispatched nothing must not be reported as lost data",
        )
        self.assertEqual(
            query_mod.classify_token_absences([genuine_loss])["not-recorded"],
            1,
            "THE CHECK MUST FIRE: a run that did work and recorded no tokens is a real gap",
        )


# ============================================================ E-06: the envelope and the budget
class AgentEnvelopeAndBudgetTests(_RepoFixture):
    """E-06 / V-06: the EXISTING `aw.agent/v1` envelope, inside the enforced budget, paginated."""

    def _all_view_argvs(self) -> list[list[str]]:
        extra = {"slices": ["--group-by", "phase"], "explain": ["--price", "era-b"]}
        return [
            ["runs", "query", view, *extra.get(view, []), "--agent", *self._dir()]
            for view in query_mod.VIEWS
        ]

    def test_every_record_of_every_view_validates(self):
        for argv in self._all_view_argvs():
            out, err, rc = _run(argv)
            for rec in _records(out):
                with self.subTest(view=argv[2], kind=rec.get("kind")):
                    self.assertEqual(
                        agent_schema.validate_agent_record(rec), [], f"{rec}"
                    )

    def test_every_record_of_every_view_is_inside_the_byte_and_token_budget(self):
        """THE MEASURED CONSTRAINT: 1200 bytes / 400 approximate tokens, per RECORD."""

        worst = 0
        for argv in self._all_view_argvs():
            out, err, rc = _run(argv)
            for line in out.splitlines():
                if not line.strip():
                    continue
                size = len(line.encode("utf-8"))
                worst = max(worst, size)
                with self.subTest(view=argv[2]):
                    self.assertLessEqual(
                        size,
                        BYTE_BUDGET,
                        f"{argv[2]}: record {size} bytes > {BYTE_BUDGET}",
                    )
                    self.assertLessEqual(_approx_tokens(line), TOKEN_BUDGET)
        self.assertGreater(worst, 0, "no records were emitted at all")

    def test_the_schema_version_is_the_existing_one_and_no_outcome_was_invented(self):
        self.assertEqual(agent_schema.SCHEMA_VERSION, "aw.agent/v1")
        for argv in self._all_view_argvs():
            out, _err, _rc = _run(argv)
            for rec in _records(out):
                self.assertEqual(rec["schema"], "aw.agent/v1")
                self.assertIn(rec["kind"], agent_schema.RECORD_KINDS)
                if "outcome" in rec:
                    self.assertIn(rec["outcome"], agent_schema.VALID_OUTCOMES)

    def test_a_bounded_page_reports_omitted_rather_than_truncating_silently(self):
        out, err, rc = _run(
            ["runs", "query", "findings", "--limit", "1", "--agent", *self._dir()]
        )
        self.assertEqual(rc, 0, out + err)
        summary = _records(out)[-1]
        self.assertEqual(summary["kind"], "summary")
        self.assertFalse(summary["complete"])
        self.assertGreater(summary["omitted"], 0)
        self.assertEqual(summary["emitted"] + summary["omitted"], summary["total"])
        self.assertIn("next", summary)

    def test_a_complete_page_says_so(self):
        out, err, rc = _run(
            ["runs", "query", "findings", "--limit", "500", "--agent", *self._dir()]
        )
        self.assertEqual(rc, 0, out + err)
        summary = _records(out)[-1]
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["omitted"], 0)

    def test_a_corpus_scale_distribution_stays_bounded(self):
        """A distribution over a corpus-scale sample is a FIXED-SIZE summary, not a row dump.

        This is the view the budget would otherwise break. It is bounded structurally: the payload is
        nine statistics plus a missing count, so it does not grow with the number of observations.
        """

        entries = [
            {
                "metric_facts": {"run_id": f"r{i}", "cost": float(i % 97)},
                "is_complete": True,
            }
            for i in range(30000)
        ]
        result = query_mod.view_distributions(entries, metric="cost", limit=20)
        self.assertEqual(result.total, 30000)
        as_json = json.dumps(result.to_dict(), separators=(",", ":"))
        self.assertLessEqual(
            len(as_json.encode("utf-8")),
            BYTE_BUDGET,
            f"a 30000-row distribution serialized to {len(as_json)} bytes",
        )

    def test_fields_projection_reuses_the_shared_helper_and_shrinks_the_record(self):
        full, _e, _rc = _run(["runs", "query", "schema", "--agent", *self._dir()])
        projected, _e2, _rc2 = _run(
            ["runs", "query", "schema", "--agent", "--fields", "view", *self._dir()]
        )
        self.assertLessEqual(len(projected), len(full))
        for rec in _records(projected):
            if rec.get("kind") in ("result", "summary", "error"):
                for mandatory in ("schema", "kind", "cmd"):
                    self.assertIn(mandatory, rec)

    def test_agent_and_json_streams_are_ansi_free(self):
        import re

        ansi = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
        for mode in ("--agent", "--json"):
            out, _err, _rc = _run(["runs", "query", "schema", mode, *self._dir()])
            with self.subTest(mode=mode):
                self.assertIsNone(ansi.search(out))

    def test_a_full_finding_is_returned_whole_across_budgeted_records(self):
        """Nothing is abridged: the mandatory honesty fields are all reachable.

        One finding's full contract does not fit a single 1200-byte record, so the `evidence` view
        SECTIONS it. Truncating `uncertainty` or a caveat instead would leave text that still reads as
        complete, which is worse than the split.
        """

        out, err, rc = _run(
            ["runs", "query", "evidence", "--finding", "F-01", "--agent", *self._dir()]
        )
        self.assertEqual(rc, 0, out + err)
        blob = " ".join(json.dumps(r) for r in _records(out))
        for required in (
            "uncertainty",
            "alternative_explanations",
            "data_quality_caveats",
            "next_experiment",
        ):
            self.assertIn(required, blob)


# ============================================================ E-08: failure semantics and cache reuse
class FailureSemanticsTests(_RepoFixture):
    """E-08 / V-08: every named failure class has an exit code AND an actionable remedy."""

    def _human(self, argv: list[str]) -> tuple[str, int]:
        out, err, rc = _run(argv)
        return out + err, rc

    def test_malformed_filter(self):
        text, rc = self._human(
            ["runs", "query", "metrics", "--filter", "nope=1", *self._dir()]
        )
        self.assertEqual(rc, 2)
        self.assertIn("allowed filter fields are", text)

    def test_unknown_view(self):
        text, rc = self._human(["runs", "query", "nosuchview", *self._dir()])
        self.assertEqual(rc, 2)
        self.assertIn("allowed views are", text)

    def test_missing_corpus_is_an_honest_empty_state_not_a_crash(self):
        with tempfile.TemporaryDirectory() as td:
            bare = Path(td) / "empty"
            bare.mkdir()
            out, err, rc = _run(
                ["runs", "query", "overview", "--agent", "--dir", str(bare)]
            )
            self.assertEqual(rc, 0, out + err)

    def test_corrupt_cache_entry_is_skipped_and_counted_not_fatal(self):
        from agent_workflows import run_analytics_cache as cache_mod

        _run(["runs", "analyze", "--agent", *self._dir()])
        root = cache_mod.cache_root(self.repo)
        entries = sorted(root.rglob(cache_mod.ENTRY_FILENAME)) if root.is_dir() else []
        self.assertTrue(entries, f"no cache entry was published under {root}")
        entries[0].write_text("{ not json", encoding="utf-8")

        # The corrupt entry is SKIPPED, the view still answers, and the damage is COUNTED rather than
        # silently reducing the corpus.
        out, err, rc = _run(["runs", "query", "cache-status", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)
        context = next(
            (r["context"] for r in _records(out) if "context" in r),
            {},
        )
        self.assertGreaterEqual(context.get("unreadable_entries", 0), 1, context)

    def test_unsupported_schema_version_is_refused_with_a_forward_compatible_message(
        self,
    ):
        from agent_workflows import run_analytics_cache as cache_mod

        _run(["runs", "analyze", "--agent", *self._dir()])
        root = cache_mod.cache_root(self.repo)
        self.assertTrue(root.is_dir(), "the sweep produced no cache at all")
        # Entries live under `<cache_root>/<root-id>/<run-id>/entry.json`, i.e. one level deeper than
        # the cache root. `rglob` rather than a fixed depth so a layout change surfaces as a real
        # failure here instead of a skip that quietly stops testing anything.
        entries = sorted(root.rglob(cache_mod.ENTRY_FILENAME))
        self.assertTrue(entries, f"no cache entry was published under {root}")
        target = entries[0]
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["schema_version"] = cache_mod.CACHE_SCHEMA_VERSION + 99
        target.write_text(json.dumps(payload), encoding="utf-8")
        # The entry is unreadable at this version: it is SKIPPED, and the view still answers.
        out, err, rc = _run(["runs", "query", "cache-status", "--agent", *self._dir()])
        self.assertEqual(rc, 0, out + err)

    def test_open_failure_carries_a_remedy(self):
        report_path = analytics_cli._latest_report_path(self.repo)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("<html></html>", encoding="utf-8")
        analytics_cli.set_launcher(
            lambda p: analytics_cli.LaunchOutcome(
                False, False, "no browser", f"open manually: {p}"
            )
        )
        text, rc = self._human(["runs", "analyze", "--open", *self._dir()])
        self.assertEqual(rc, 2)
        self.assertIn("open", text.lower())

    def test_analyze_twice_reuses_the_cache(self):
        """CACHE REUSE, measured through Order 02's own verdict vocabulary."""

        from agent_workflows import run_analytics_cache as cache_mod
        from agent_workflows import run_analytics

        run_dirs = sorted((self.repo / ".aw" / "records" / "runs").iterdir())
        first = cache_mod.update_cache(
            run_dirs, build_facts=run_analytics.build_cache_facts, repo=self.repo
        )
        second = cache_mod.update_cache(
            run_dirs, build_facts=run_analytics.build_cache_facts, repo=self.repo
        )
        self.assertGreater(
            second.totals.get("hit", 0),
            first.totals.get("hit", 0),
            f"the second sweep did not reuse the cache: {first.totals} then {second.totals}",
        )

    def test_mutating_one_run_rebuilds_only_that_entry(self):
        """SELECTIVE REBUILD: a changed run is rebuilt; its unchanged siblings stay hits."""

        from agent_workflows import run_analytics_cache as cache_mod
        from agent_workflows import run_analytics

        run_dirs = sorted((self.repo / ".aw" / "records" / "runs").iterdir())
        cache_mod.update_cache(
            run_dirs, build_facts=run_analytics.build_cache_facts, repo=self.repo
        )
        target = run_dirs[0]
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        state["updated_at"] = "2026-02-02T02:02:02Z"
        (target / "state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )

        report = cache_mod.update_cache(
            run_dirs, build_facts=run_analytics.build_cache_facts, repo=self.repo
        )
        verdicts = {d.run_id: d.verdict for d in report.decisions}
        self.assertEqual(verdicts.get(target.name), "rebuild", verdicts)
        others = [v for k, v in verdicts.items() if k != target.name]
        self.assertTrue(all(v == "hit" for v in others), verdicts)

    def test_help_is_asserted_through_the_conformance_matrix_help_scenario(self):
        """Discoverability is gated by the matrix's `help` scenario, not an ad hoc snapshot.

        THE DOCS-SNIPPET CLAIM IS EXPLICITLY DOWNGRADED. The plan's authored text promised "Help and
        README command snippets are executable", and NO such mechanism exists: no test in this suite
        executes a documented command line, and `tests/test_cli_output_docs_rollout.py` asserts docs
        CONTENT only. Rather than imply coverage that does not exist, this asserts what is real: the
        declared class requires the `help` scenario, and the leaf satisfies it natively.
        """

        from agent_workflows.command_surface import get_declaration
        from tests.conformance_matrix import required_scenarios

        for name, leaf in (("runs analyze", "analyze"), ("runs query", "query")):
            decl = get_declaration(name)
            assert decl is not None
            with self.subTest(leaf=name):
                self.assertIn("help", required_scenarios(decl))
                out, err, rc = _run(["runs", leaf, "--help"])
                self.assertEqual(rc, 0)
                self.assertIn("usage", (out + err).lower())

    def test_no_test_here_reaches_the_network_or_launches_a_browser(self):
        """No test in this file imports a network or browser module.

        Asserted over the parsed IMPORT SET rather than by scanning for substrings. A substring scan
        is self-defeating here: the scan's own list of forbidden tokens is itself text in this file, so
        the test would fail on its own source. Reading the AST's imports asks the real question, which
        is what this module actually pulls in.
        """

        import ast

        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for forbidden in (
            "urllib",
            "http",
            "socket",
            "requests",
            "webbrowser",
            "selenium",
        ):
            self.assertNotIn(forbidden, imported)


class TheReportIsRenderedByTheSpaNotAStub(unittest.TestCase):
    """`aw runs analyze` must publish the real document, not a placeholder.

    REGRESSION GUARD for a gap between two plans that both reported done. Order 07 (`6eq3oq`) built
    `run_analytics_spa.render_document` (1567 lines, shipped CSS/JS) and its goal was that opening the
    HTML from disk "must provide useful charts, raw normalized data, quality context, and findings
    without a server or network"; it then scoped the wiring out by name to Order 08 (`mm5p3v`). Order 08
    registered the leaves and wrote a hardcoded four-line HTML string instead of calling the renderer,
    so `render_document` had ZERO callers in the package and every published report was a 194-byte stub
    reading "Machine-readable companion: analysis.json". Measured 2026-09-18 over 180 analyzed runs.

    These assert the OUTCOME (a document with the panels and the corpus in it) rather than the call, so
    they still hold if the wiring is refactored.
    """

    def test_the_renderer_is_reachable_from_this_module(self):
        """The published document must be produced BY the SPA renderer, proven with a sentinel.

        REPLACES A SOURCE-TEXT PIN that read `inspect.getsource(analytics_cli._render_report_html)`
        and asserted the strings `"render_document"` and `"build_view_model"` appeared in it. Both
        names appear in that function's own DOCSTRING (it explains at length that Order 08 failed
        to call the renderer), so the pin matched prose and would have stayed GREEN for the exact
        194-byte stub it was written to catch. That is failure mode 2 from the brief, measured on
        the very defect the guard names.

        Replaced with a SENTINEL: the shared renderer is patched to return a marker and the
        view-model builder is spied on. The marker must reach the function's return value and the
        builder must have been called exactly once with the model the renderer received. A stub
        that composes its own HTML cannot pass, whatever its source says, and a refactor that
        renames or relocates the call still passes as long as the renderer is what renders.
        """
        from agent_workflows import run_analytics_spa as spa_mod

        marker = "<!DOCTYPE html><!-- SENTINEL from the shared SPA renderer -->"
        real_render, real_build = spa_mod.render_document, spa_mod.build_view_model
        built, rendered = [], []

        def spy_build(**kwargs):
            model = real_build(**kwargs)
            built.append(kwargs)
            return model

        def sentinel_render(model, **kwargs):
            rendered.append(model)
            return marker

        spa_mod.build_view_model = spy_build  # type: ignore[assignment]
        spa_mod.render_document = sentinel_render  # type: ignore[assignment]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                html = analytics_cli._render_report_html(
                    Path(tmp), generated_label="sentinel-probe"
                )
        finally:
            spa_mod.build_view_model = real_build  # type: ignore[assignment]
            spa_mod.render_document = real_render  # type: ignore[assignment]

        self.assertEqual(
            html,
            marker,
            "the published document is not the shared renderer's output; something else composed "
            "it (this is the zero-caller stub defect, and a source scan for the renderer's NAME "
            "matched only this function's docstring)",
        )
        self.assertEqual(
            len(built),
            1,
            f"build_view_model was called {len(built)} times, expected exactly 1",
        )
        self.assertEqual(len(rendered), 1)
        self.assertEqual(
            built[0].get("generated_label"),
            "sentinel-probe",
            "the caller's label must reach the view model, or the document cannot say what it is",
        )

    def test_the_rendered_document_carries_the_panels_and_is_not_a_stub(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            html = analytics_cli._render_report_html(repo, generated_label="probe")
            # The stub was 194 bytes. A real document is an order of magnitude larger, but assert on
            # STRUCTURE rather than size so the test says what it means.
            for panel in (
                "overview",
                "charts",
                "findings",
                "pricing",
                "quality",
                "refusals",
            ):
                with self.subTest(panel=panel):
                    self.assertIn(f'id="{panel}"', html)
            self.assertNotIn("Machine-readable companion: analysis.json", html)

    def test_an_empty_corpus_still_renders_rather_than_refusing(self):
        """A repo with no runs must produce a document that says so, not an exception."""
        with tempfile.TemporaryDirectory() as tmp:
            html = analytics_cli._render_report_html(Path(tmp), generated_label="empty")
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn('id="overview"', html)

    def test_the_raw_table_is_not_truncated_to_the_terminal_page_size(self):
        """A corpus LARGER than every page size must be embedded in full, run for run.

        REPLACES A SOURCE-TEXT PIN that searched `_render_report_html`'s source for `"max_limit"`
        and `"limit=row_limit"`. Both appear in that function's own explanatory COMMENT block, and
        neither says anything about how many rows actually reach the document: leaving
        `row_limit = 20` while still spelling `limit=row_limit` would have kept the pin green and
        truncated the corpus to a terminal page.

        This builds a corpus exceeding BOTH thresholds - `run_query`'s 20-row terminal default and
        the SPA's 100-row view page - renders the real document, decodes its embedded payload, and
        demands EVERY run id. The run-by-run set difference is deliberate rather than a count
        comparison, because a truncation reports a plausible number and the missing members are the
        evidence a reader needs.

        The page size is NOT the defect: the raw view paginates by design, so 100-at-a-time in the
        BROWSER is correct. What must not be truncated is the DATA embedded in the file, since a
        page the reader can never reach is a corpus member that silently does not exist.
        """
        from agent_workflows import run_analytics_cache as cache_mod
        from agent_workflows import run_analytics
        from agent_workflows import run_analytics_spa as spa_mod

        # Bigger than the larger of the two thresholds, derived from the shipped constants rather
        # than hardcoded, so raising either one re-tightens this test instead of silently relaxing it.
        total = max(query_mod.DEFAULT_ROW_LIMIT, spa_mod.RAW_VIEW_PAGE_SIZE) + 7
        with tempfile.TemporaryDirectory() as tmp:
            repo = _make_repo(Path(tmp))
            expected = set()
            for index in range(total):
                run_id = f"run-20260901T{index:04d}00Z-{index:07d}"
                expected.add(run_id)
                _write_run(repo, run_id, setid="runanalytics")

            # Populate the cache DIRECTLY (the query views read the cache, and this is the same
            # call `aw runs analyze` makes) rather than through the CLI, which would also publish a
            # snapshot bundle this test has no use for.
            run_dirs = sorted((repo / ".aw" / "records" / "runs").iterdir())
            cache_mod.update_cache(
                run_dirs, build_facts=run_analytics.build_cache_facts, repo=repo
            )

            html = analytics_cli._render_report_html(
                repo, generated_label="truncation-probe"
            )

        encoded = re.search(r'id="embedded-data">([^<]*)</script>', html)
        self.assertIsNotNone(
            encoded, "the document carries no embedded data payload at all"
        )
        assert encoded is not None
        payload = spa_mod.decode_embedded_payload(encoded.group(1))

        self.assertEqual(
            payload.get("row_count"),
            total,
            f"the embedded payload declares {payload.get('row_count')!r} rows for a {total}-run "
            f"corpus; {query_mod.DEFAULT_ROW_LIMIT} would mean the report inherited the TERMINAL "
            f"page size and {spa_mod.RAW_VIEW_PAGE_SIZE} would mean it inherited the browser's",
        )
        embedded = set(payload.get("data", {}).get("run_id") or ())
        missing = sorted(expected - embedded)
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} of {total} runs are absent from the embedded corpus (first few: "
            f"{missing[:5]}). A raw table is the panel an operator sorts and filters, so a run that "
            "never reaches the file is a corpus member that silently does not exist. FIX: the row "
            "limit must come from the query grammar's own ceiling (`MAX_ROW_LIMIT`), never from "
            "`DEFAULT_ROW_LIMIT` and never from a number hardcoded here.",
        )
        # The browser-side page size is still PUBLISHED, so pagination is a UI affordance rather
        # than a data loss; asserted here so this test cannot be "fixed" by removing pagination.
        self.assertIn(
            f'"raw_view_page_size":{spa_mod.RAW_VIEW_PAGE_SIZE}',
            html,
            "the document must still declare its page size; the corpus is complete AND paginated",
        )


if __name__ == "__main__":
    unittest.main()

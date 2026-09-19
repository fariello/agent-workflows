"""`aw * run` must announce, before it starts, which queued plans will change a SPEC.

WHY (maintainer request 2026-09-07). A plan's `- Scope-Paths:` is its declared allowlist, and the
finalize gate already reconciles the real change set against it. But nothing SURFACED a spec edit to
the operator: the pre-run output printed the run order and nothing else, so "this run will rewrite an
approved specification" was discoverable only by opening every queued plan. A spec is the contract
other plans are reviewed against, which makes an unnoticed spec edit the highest-leverage change a run
can make and, until now, the least visible one.

The policy this rests on, decided by the maintainer the same day: an IPD MAY edit a spec. Plan
`51vw4y` proved the alternative is a dead end (the flag table it must extend is spec-governed, and the
plan had no spec-edit authority, so every route either edited an approved spec or weakened a shipped
contract test). Specs are living contracts, so the answer is to permit the amendment and make it LOUD.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: hand one stage of the
announcement pipeline a single input and assert the one list it returns. The pipeline is three pure
stages (extract declared spec paths from a plan's text -> collect them across a queue of plans on disk
-> format the operator-facing lines), and the tables group BY STAGE.

DETECTING ROWS AND NON-DETECTING ROWS LIVE IN THE SAME TABLE, which is the load-bearing decision
here. This is a SAFETY ANNOUNCEMENT, so the two failure directions are not symmetric and both are
fatal: an extractor that found nothing makes every spec edit silent again, reproducing the incident
exactly, while one that found everything floods the operator until the announcement is ignored, which
is the same outcome by a slower route. A table of only-detecting rows is satisfied by a function
returning every path it is given, and a table of only-empty rows by one returning nothing. The failure
messages name which direction collapsed.

Tests that are NOT rows carry a one-line docstring saying why they stay separate.
"""

from __future__ import annotations

from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows.render_stream import (
    Palette,
    format_spec_impact_announcement,
)

PLAN = """\
# IPD: demo

- Date: 2026-09-07
- Kind: child
- Scope-Paths: {scope}
- Status: approved
- Set: demo
- Order: 1
- Id: {id6}
"""


def _plan(root: Path, id6: str, scope: str) -> Path:
    p = root / f"20260907-demo-01-{id6}-demo.ipd.md"
    p.write_text(PLAN.format(scope=scope, id6=id6), encoding="utf-8")
    return p


class TestDeclaredSpecPaths:
    """Which entries of a plan's `- Scope-Paths:` count as a declared SPEC edit.

    ONE table replaces seven tests. Every one of them formatted the same plan template with a
    different `Scope-Paths` value and asserted the exact list `declared_spec_paths` returned, so the
    only thing that varied was the DATA and the shape of the expected answer, which is a column.

    Why the table beats the seven: one selection rule decides every row (does the entry carry the
    `.spec.md` type facet), so the realistic regression moves a legible GROUP of rows. Every row
    reporting nothing means extraction broke and the whole announcement went silent; the two
    non-detecting rows reporting paths means the facet test became a substring match and the operator
    is about to be flooded. Seven tests report either case as unrelated `[] != [...]` lines, which
    hides which of the two happened - and the two need opposite fixes.

    THE NON-DETECTING ROWS ARE IN THE SAME TABLE and carry the weight for the detecting half: a
    function that echoed back every scope entry would satisfy all four detecting rows on its own. Two
    of them are the subtle ones (`docs/spec.md` and `agent_workflows/ipd_schema.py` are spec-SHAPED
    but are not specs), and they are what turn "it finds specs" into "it finds exactly specs".

    ORDER IS ASSERTED, NOT MEMBERSHIP. The announcement lists paths in the order the plan declared
    them, so a set-based implementation would pass a membership check while making the operator's
    output non-deterministic across runs.
    """

    #: (case, the `- Scope-Paths:` value, the EXACT list expected in order, why this row exists)
    SCOPES = (
        (
            "a spec among code and test paths",
            "agent_workflows/cli.py, .aw/records/specs/20260826-0718-01-x.spec.md, tests/t.py",
            [".aw/records/specs/20260826-0718-01-x.spec.md"],
            "THE ORDINARY CASE, and the one the whole surface exists for: a plan that edits a spec "
            "ALONGSIDE code, which is how a legitimate spec amendment always arrives. The neighbours "
            "must be filtered out, so this row states both halves of the rule at once. Every "
            "non-detecting row below is vacuous while this one is broken",
        ),
        (
            "two specs, declared out of alphabetical order",
            "b/second.spec.md, a/first.spec.md",
            ["b/second.spec.md", "a/first.spec.md"],
            "DECLARED ORDER IS PRESERVED, not sorted and not set-deduplicated. The expected list is "
            "deliberately anti-alphabetical, so a `sorted()` or a `set()` in the implementation fails "
            "exactly here; either would make the operator's pre-run output differ between runs of an "
            "unchanged queue",
        ),
        (
            "a spec OUTSIDE the records tree",
            "somewhere/else/20260101-0000-01-y.spec.md",
            ["somewhere/else/20260101-0000-01-y.spec.md"],
            "IDENTIFIED BY THE TYPE FACET, NOT BY DIRECTORY, so a relocated records tree cannot hide "
            "a spec edit. A path-prefix implementation would pass every other row here and go silent "
            "the day the tree moves",
        ),
        (
            "only code and test paths",
            "agent_workflows/cli.py, tests/t.py",
            [],
            "THE COMMON CASE IS SILENCE: the overwhelming majority of plans touch no spec, and an "
            "announcement that fired on them would be noise the operator learns to skip - which "
            "costs exactly as much as no announcement at all",
        ),
        (
            "the `grandfathered` sentinel",
            "grandfathered",
            [],
            "A SENTINEL IS NOT A PATH. `grandfathered` is what a pre-cutover plan carries instead of "
            "an allowlist, and treating it as a filename would announce a spec edit for a plan that "
            "declared no scope at all",
        ),
        (
            "the `none` sentinel",
            "none",
            [],
            "the other sentinel spelling, kept beside `grandfathered` so the rule reads as 'sentinels "
            "are not paths' rather than as one hardcoded word",
        ),
        (
            "an EMPTY Scope-Paths value",
            "",
            [],
            "the degenerate value: a present-but-empty field must yield nothing rather than a list "
            "containing an empty string, which downstream would resolve to the repo root",
        ),
        (
            "a doc merely NAMED like a spec",
            "agent_workflows/ipd_schema.py, docs/spec.md",
            [],
            "THE PRECISION ROW, and the one most likely to break: `.spec.md` is the FACET, so "
            "`docs/spec.md` (a doc about specs) and `ipd_schema.py` (the schema a spec governs) are "
            "not spec edits. A substring or `'spec' in path` test passes every detecting row above "
            "and fails only here",
        ),
    )

    def test_exactly_the_spec_facet_paths_are_reported_in_declared_order(self) -> None:
        wrong = []
        detecting_rows_broken = 0
        silent_rows_broken = 0
        for case, scope, expected, why in self.SCOPES:
            got = runner_shared.declared_spec_paths(
                PLAN.format(scope=scope, id6="aaa111")
            )
            if got != expected:
                if expected:
                    detecting_rows_broken += 1
                else:
                    silent_rows_broken += 1
                wrong.append(
                    f"  {case} (Scope-Paths: {scope!r}):\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        direction = ""
        if detecting_rows_broken and not silent_rows_broken:
            direction = (
                f" ALL {detecting_rows_broken} failing row(s) are DETECTING rows, so extraction has "
                "gone quiet and spec edits are invisible to the operator again - which is the "
                "incident this surface was built for."
            )
        elif silent_rows_broken and not detecting_rows_broken:
            direction = (
                f" ALL {silent_rows_broken} failing row(s) are rows that must report NOTHING, so the "
                "facet test has widened into a substring match; the detecting rows above now prove "
                "nothing, since a function echoing back every scope entry satisfies them all. A "
                "flooded announcement is ignored, which costs the same as no announcement."
            )
        assert not wrong, (
            f"`declared_spec_paths` misread {len(wrong)} of {len(self.SCOPES)} scope "
            f"declarations.{direction} ONE selection rule decides every row (the `.spec.md` type "
            "facet), so read the grouping: every row failing means parsing of the field itself broke, "
            "the two sentinel rows failing together means sentinels are being treated as paths, and "
            "the `docs/spec.md` row alone means the facet test became a substring match. FIX: this is "
            "the input to a SAFETY ANNOUNCEMENT, so do not relax a row to make it pass - a missed spec "
            "edit is silent, and a spurious one trains the operator to ignore the line.\n"
            + "\n".join(wrong)
        )

    def test_a_missing_scope_paths_field_yields_empty(self) -> None:
        """Kept separate: the field is ABSENT rather than carrying a value, so the plan template
        the table formats cannot express it."""
        assert runner_shared.declared_spec_paths("# IPD: no scope field\n") == []


class TestSpecImpactsForQueue:
    """Collecting declared spec edits across a queue of plan files on disk.

    ONE table replaces four tests. Each built a queue of item dicts, called `spec_impacts_for_queue`,
    and asserted the impact list; they differed in the QUEUE SHAPE (how many items, how each item's
    path was spelled, whether the file existed, whether a path was present at all), which is a
    column.

    Why the table beats the four: this stage adds exactly two behaviors on top of the extractor
    (resolve a repo-relative path, and skip an item that cannot be read) and must otherwise pass the
    extractor's answer through untouched. Both skip rows are ADVISORY-SURFACE guarantees - a run must
    never fail to start because an announcement could not be built - so they belong beside the
    collecting rows that show the surface still works when nothing is wrong. Read together they say
    the stage is fail-soft rather than silent.

    THE MIXED-QUEUE ROW IS THE IMPORTANT ONE: an item declaring only code must be ABSENT from the
    output rather than present with an empty `specs` list, because the formatter counts plans from
    this list and an empty entry would announce a plan that changes no spec.
    """

    #: (case, the queue as a list of `(id6, how to spell the path, scope value or None to write no
    #: file)` tuples, the EXACT expected impact list built with `{id6, setid, specs}`, why this row
    #: exists)
    QUEUES = (
        (
            "two queued plans, only one of which touches a spec",
            (
                ("bbb111", "absolute", "x/one.spec.md, agent_workflows/cli.py"),
                ("bbb222", "absolute", "agent_workflows/only_code.py"),
            ),
            [{"id6": "bbb111", "setid": "demo", "specs": ["x/one.spec.md"]}],
            "THE CANONICAL CASE and the row that pins the output SHAPE: the code-only plan must be "
            "ABSENT from the list, not present with an empty `specs`. The formatter counts plans from "
            "this list, so an empty entry would announce that a plan changes a spec when it does not",
        ),
        (
            "a queue item whose path is repo-RELATIVE",
            (("ccc111", "relative", "x/one.spec.md"),),
            [{"id6": "ccc111", "setid": "demo", "specs": ["x/one.spec.md"]}],
            "QUEUE ITEMS ARRIVE WITH EITHER SPELLING depending on how the queue was built, and a "
            "relative path must be resolved against the repo root rather than the process cwd. "
            "Unresolved, it would read as unreadable and be silently SKIPPED by the row below, so "
            "this row is what stops the fail-soft behavior from swallowing a real spec edit",
        ),
        (
            "a queue item naming a plan file that does not exist",
            (("ddd111", "missing", None),),
            [],
            "FAIL-SOFT BY DESIGN: this is an advisory surface, so an unreadable plan is skipped and "
            "the run still starts. Refusing to begin a run because an announcement could not be built "
            "would be a worse failure than a missing line of output",
        ),
        (
            "a queue item with no path key at all",
            (("eee111", "nokey", None),),
            [],
            "the other malformed-item shape, from a queue entry built before its path was known. It "
            "must be skipped by the same route rather than raising a KeyError inside pre-run output",
        ),
    )

    def test_impacts_are_collected_across_the_queue_and_bad_items_are_skipped(
        self, tmp_path: Path
    ) -> None:
        wrong = []
        collecting_rows_broken = 0
        for case, items, expected, why in self.QUEUES:
            queue = []
            for id6, spelling, scope in items:
                if scope is not None:
                    written = _plan(tmp_path, id6, scope)
                if spelling == "absolute":
                    entry = {"id6": id6, "setid": "demo", "path": str(written)}
                elif spelling == "relative":
                    entry = {"id6": id6, "setid": "demo", "path": written.name}
                elif spelling == "missing":
                    entry = {
                        "id6": id6,
                        "setid": "demo",
                        "path": "does/not/exist.ipd.md",
                    }
                else:
                    entry = {"id6": id6, "setid": "demo"}
                queue.append(entry)
            got = runner_shared.spec_impacts_for_queue(tmp_path, queue)
            if got != expected:
                if expected:
                    collecting_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - queue: {queue!r}\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        extra = ""
        if collecting_rows_broken:
            extra = (
                f" {collecting_rows_broken} COLLECTING row(s) are among the failures, and while any "
                "of those is broken the two SKIP rows here are vacuous: a function returning an empty "
                "list for every queue satisfies both of them while announcing nothing, ever."
            )
        assert not wrong, (
            f"`spec_impacts_for_queue` mishandled {len(wrong)} of {len(self.QUEUES)} queue "
            f"shapes.{extra} This stage adds exactly two behaviors over the extractor (resolve a "
            "repo-relative path; skip an unreadable item), so read the grouping: the relative-path "
            "row failing alone means resolution now happens against the process cwd, which makes real "
            "plans read as unreadable and be SILENTLY SKIPPED by the fail-soft path; a skip row "
            "failing means a malformed queue entry can now stop a run from starting, which is a worse "
            "failure than a missing line of output. FIX: an item declaring no spec must be ABSENT "
            "from this list rather than present with an empty `specs`, because the formatter counts "
            "plans from it.\n" + "\n".join(wrong)
        )


class TestAnnouncement:
    """What the operator actually sees, and when they see nothing.

    ONE table replaces three tests (`test_silent_when_no_plan_touches_a_spec`,
    `test_names_every_plan_and_every_spec`, `test_says_why_it_matters`). All three called
    `format_spec_impact_announcement` with an impact list and asserted over the rendered lines; they
    differed in the input and in whether the claim was SILENCE, CONTENT, or a fixed sentence, so the
    check is a column: each row says which tokens must appear and whether any output is permitted at
    all.

    Why the table beats the three: the silence rows and the content rows constrain each other and
    neither direction is safe alone. A formatter returning `[]` unconditionally satisfies both
    silence rows while making every spec edit invisible - the original incident - and one that always
    emitted a header satisfies the content rows while printing a spec warning on every ordinary run,
    which trains the operator to skip the line. Together they are satisfiable by neither.

    THE COUNTS ARE PINNED AS RENDERED TEXT (`3 specification file(s)` over `2 queued plan(s)`) because
    the count is the part an operator reads first and the part an off-by-one breaks invisibly: a
    formatter listing all five paths correctly while claiming one file is worse than one that lists
    nothing, since it looks authoritative. The rationale sentence is pinned for the reason recorded
    when this surface was built - a list of paths does not tell an operator why to care, and this line
    is the only place the stake is stated.
    """

    #: (case, the impacts argument, whether ANY output is permitted, tokens that must all appear in
    #: the joined output, why this row exists)
    ANNOUNCEMENTS = (
        (
            "no impacts at all",
            [],
            False,
            (),
            "THE COMMON CASE: most runs touch no spec, so the announcement must be completely absent "
            "rather than a header with nothing under it. An empty-but-present section is the shape "
            "operators learn to skip",
        ),
        (
            "an impact entry whose `specs` list is EMPTY",
            [{"id6": "x", "specs": []}],
            False,
            (),
            "DEFENCE IN DEPTH against the upstream stage: the collector is supposed to omit such an "
            "entry, but if one ever arrives the formatter must still print nothing rather than "
            "announce a spec edit for a plan that changes no spec",
        ),
        (
            "two plans across two Sets declaring three specs between them",
            [
                {"id6": "aaa111", "setid": "one", "specs": ["a/x.spec.md"]},
                {
                    "id6": "bbb222",
                    "setid": "two",
                    "specs": ["b/y.spec.md", "b/z.spec.md"],
                },
            ],
            True,
            (
                "3 specification file(s)",
                "2 queued plan(s)",
                "aaa111",
                "bbb222",
                "a/x.spec.md",
                "b/y.spec.md",
                "b/z.spec.md",
                "contract other plans are reviewed against",
            ),
            "THE FULL-CONTENT ROW, asserting the COUNTS as rendered text alongside every id6 and every "
            "path. The counts are what an operator reads first, so an off-by-one is worse than a "
            "missing line: it looks authoritative while under-reporting. The fan-out (one plan naming "
            "TWO specs) is what makes the two counts differ, so a formatter conflating plans with "
            "files fails here",
        ),
        (
            "a single plan naming a single spec",
            [{"id6": "aaa111", "setid": "one", "specs": ["a/x.spec.md"]}],
            True,
            ("contract other plans are reviewed against", "aaa111", "a/x.spec.md"),
            "THE RATIONALE MUST APPEAR EVEN IN THE SMALLEST ANNOUNCEMENT. A list of paths does not "
            "tell an operator why to care, and this sentence is the only place the stake is stated; "
            "keeping the claim on the minimal input stops it from being a property of the multi-plan "
            "header alone",
        ),
    )

    def test_the_announcement_is_silent_when_it_should_be_and_complete_when_it_fires(
        self,
    ) -> None:
        wrong = []
        silence_rows_broken = 0
        content_rows_broken = 0
        for case, impacts, expect_output, tokens, why in self.ANNOUNCEMENTS:
            lines = format_spec_impact_announcement(impacts, pal=Palette(False))
            blob = "\n".join(lines)
            problems = []
            if not expect_output:
                if lines:
                    silence_rows_broken += 1
                    problems.append(f"must produce NO output at all; got {lines!r}")
            else:
                if not lines:
                    content_rows_broken += 1
                    problems.append(
                        "produced NO output, so this run's spec edits are invisible to the operator"
                    )
                missing = [t for t in tokens if t not in blob]
                if missing:
                    content_rows_broken += 1
                    problems.append(
                        f"these required tokens are absent: {missing!r}; rendered output was {lines!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if silence_rows_broken and not content_rows_broken:
            extra = (
                f" ALL {silence_rows_broken} failing row(s) are SILENCE rows, so the announcement now "
                "fires on runs that touch no spec; that is noise the operator learns to skip, which "
                "costs as much as printing nothing."
            )
        elif content_rows_broken and not silence_rows_broken:
            extra = (
                f" ALL {content_rows_broken} failing row(s) are CONTENT rows, so the announcement has "
                "gone quiet or incomplete and the silence rows above prove nothing: a formatter "
                "returning [] unconditionally satisfies them both, which is exactly the original "
                "incident."
            )
        assert not wrong, (
            f"the announcement was wrong for {len(wrong)} of {len(self.ANNOUNCEMENTS)} inputs.{extra} "
            "One formatter decides every row, so read the grouping: both silence rows failing means "
            "the empty-input guard went, a missing COUNT token means plans and files are being "
            "conflated (the fan-out row is where that shows), and a missing rationale token means the "
            "line degraded into a bare path list. FIX: the counts and the rationale sentence are "
            "pinned as RENDERED TEXT because an operator reads them first - an off-by-one count is "
            "worse than no line at all, since it looks authoritative while under-reporting.\n"
            + "\n".join(wrong)
        )

    def test_is_pure(self, capsys) -> None:
        """Kept separate: the claim is about STDOUT rather than the returned lines.

        Every table row inspects the return value; this asserts the formatter WRITES nothing, so a
        renderer that printed as a side effect (and returned the lines too) would pass the whole table
        while double-printing the announcement in the runner.
        """
        format_spec_impact_announcement(
            [{"id6": "a", "setid": "s", "specs": ["x.spec.md"]}], pal=Palette(False)
        )
        assert capsys.readouterr().out == ""


class TestBothHostsShareOneDefinition:
    """Anti-re-fork (2r306y/818uru): asserted by object identity, not by grep.

    ONE table replaces the loop this class already carried, promoting it to the accumulating shape the
    rest of the file uses so a fork in ONE symbol on ONE host reports the whole picture rather than
    failing on the first mismatch.

    Why it matters that this is one test over a table rather than per-symbol tests: the property is
    that BOTH driver hosts resolve to the SAME object, so the interesting information is which
    (symbol, host) cells moved. Identity is asserted rather than equality of behavior, because a
    re-forked copy that happens to behave identically today is exactly how the two hosts drifted
    before.
    """

    #: (symbol name, why this row exists)
    SHARED = (
        (
            "spec_impacts_for_queue",
            "the QUEUE-LEVEL stage. If one host re-forked it, that host's pre-run output could omit "
            "a spec edit the other announced, and nobody would see a discrepancy because no operator "
            "runs the same queue on both hosts",
        ),
        (
            "declared_spec_paths",
            "the EXTRACTOR the stage above delegates to. It is the smaller function and therefore the "
            "likelier one to be quietly reimplemented inline when a host needs a small variation",
        ),
    )

    def test_both_hosts_resolve_to_the_one_shared_definition(self) -> None:
        wrong = []
        for name, why in self.SHARED:
            shared = getattr(runner_shared, name, None)
            problems = []
            if shared is None:
                problems.append(
                    "`runner_shared` does not define it at all, so there is no shared definition to "
                    "point at"
                )
            else:
                if (
                    getattr(shared, "__module__", None)
                    != "agent_workflows.runner_shared"
                ):
                    problems.append(
                        f"its __module__ is {getattr(shared, '__module__', None)!r}, so the name in "
                        "`runner_shared` is itself an alias of something defined elsewhere"
                    )
                for host, mod in (("oc", oc_runipd), ("agy", agy_runipd)):
                    attr = getattr(mod, name, None)
                    if attr is None:
                        problems.append(
                            f"[{host}] does not expose it; that host cannot be using the shared one"
                        )
                    elif attr is not shared:
                        problems.append(
                            f"[{host}] resolves to a DIFFERENT object ({attr!r}), i.e. a re-fork"
                        )
            if problems:
                wrong.append(
                    f"  {name}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        assert not wrong, (
            f"{len(wrong)} of {len(self.SHARED)} shared spec-visibility symbols are no longer one "
            "definition across both hosts. Identity is asserted deliberately: a re-forked copy that "
            "behaves identically TODAY is exactly how the two hosts drifted before (2r306y/818uru), "
            "so equality of behavior is not enough. Read the grouping: ONE host failing on both "
            "symbols means that host stopped importing from `runner_shared`, while ONE symbol failing "
            "on both hosts means it was moved out of the shared module. FIX: import the definition "
            "from `agent_workflows.runner_shared` rather than reimplementing it; a host-local "
            "variation belongs as a PARAMETER on the shared function, because a divergence here means "
            "one host announces a spec edit the other hides and no operator ever compares the two.\n"
            + "\n".join(wrong)
        )

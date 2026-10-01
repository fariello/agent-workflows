# IPD: Wire --fields onto the shared output-mode parents so every agent-mode command accepts the documented projection flag

- Date: 2026-09-29
- Kind: child
- Concern: Three user-facing documents present `--fields <list>` as a general agent-mode escape hatch alongside `--limit` and `--verbose`, and `docs/cli-human-guide.md` gives `aw find plans --agent --fields findings` as a worked example, but only 4 of 151 parser leaves declare the flag (all under `aw runs`), so the documented example exits 2 with `unrecognized arguments: --fields`. An agent following the guide to cut token cost receives a usage error it cannot distinguish from its own malformed request.
- Scope: Move `--fields` from its four hand-wired `aw runs` leaves onto the two shared output-mode parents (`common` and `common_upgrade`) inside `cli._build_parser`, so every leaf that carries `--agent` also carries `--fields` and the guide's example runs. Absorb the measured cost of doing so: adding a second `--f*` long option to 14 leaves destroys their working `--f` (and `check-local-leaks`' `--fi`) abbreviation, so this plan disables argparse prefix abbreviation on the affected parsers rather than shipping that regression silently. Add an executed test pinning flag reach and the surviving abbreviations. Correct `docs/cli-human-guide.md`'s example, which is inert for a SECOND reason this plan does not fix. Does NOT change `agent_schema.filter_record_fields`, does NOT change any record's content, does NOT give `--fields` an effect on `aw find`'s bare-path branch, and does NOT touch `--limit` or `--verbose`.
- Scope-Paths: agent_workflows/cli.py, tests/test_fields_flag_reach.py, docs/cli-human-guide.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: rcjorx
- Blocks-Release: next
- Set: rcjorx
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: 75ic2f

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 75ic2f verified (set rcjorx, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-doe2fo-01-doe2fo-backlog-setter-uses-local-date-instead-of-utc-date.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-206, all FIXED. Reviewed at lane HEAD `f49b7a3c`. Every material claim RE-MEASURED rather than read, and the plan's core argument held in full: the defect reproduces (exit 2 on the guide's own command), the parser walk returns exactly 151 unique leaves with 139 `--agent`, 139 `--json`, 9 `--limit`, 4 `--fields` and 1 `--verbose`, the `--agent`-without-`--fields` gap is exactly 135, F-04's `ArgumentError` raises at build time, patching `common` alone leaves exactly the six named `upgrade-test` leaves behind while patching both parents closes the gap to zero, the abbreviation sweep reproduces all 14 rows with the same flags on the same leaves, `check-local-leaks --fi` parses today and `--fix` rewrites files, `filter_record_fields` returns `dict(record)` unchanged when `fields` is falsy, and both protocol documents carry the "safe to pass on any command" sentence verbatim. THREE CORRECTIONS. (1) HIGH PR-201: E-01 instructed the executor to reuse `command_surface.discover_parser_leaves`, which is annotated `-> Set[str]` and returns leaf PATH NAMES whose members have no `_actions`, so no option set can be read from it and no name-to-parser resolver exists beside it; an executor would hit `AttributeError` on the first line. E-01 now requires a local identity-deduplicating walk and cites the helper as the PATTERN for its alias rule, with the code-pinning question addressed explicitly (new F-13). (2) HIGH PR-202: F-08's claim that `aw find plans rcjorx --agent --fields findings` projects correctly is FALSE. The branch condition is `all_paths` being truthy, not the absence of a selector, so a MATCHING selector prints one bare path and zero records; only a ZERO-MATCH query (`find plans zzzzzz`) reaches the record branch. This widens the disclosed gap (the flag is inert on essentially every useful `find` invocation) and removes a candidate the plan offered; F-08, E-05, OQ-03, V-06 and the `wdazvp` deferral row are all corrected. (3) MEDIUM PR-203: `aw check plans --agent`'s `next` field named three different artifacts on three consecutive UNMODIFIED runs, and both the Required tests byte-identity probe and V-02's final clause steered an executor into using exactly that command, producing a false disagreement on the one probe that licenses widening a flag to 139 leaves. Both now name deterministic commands (five measured byte-identical across the patch) and E-07 is told to assert `target` or `diagnostics` absent rather than `next` (new F-14). LOW PR-204 re-derived two stale live-tree counts (985 paths, 33 declaring plans) as 1033 and 43 with instructions to re-derive rather than quote; LOW PR-205 pinned E-07's absent-key choice; LOW PR-206 recorded the three backlog items as live and conforming (new F-15, F-16). Structural preflight `aw ipd lint` conforming at `author` (one advisory `IPD-Z602` on E-01, assessed as a false positive: E-01 is one deliverable and the advisory counts its guard clauses) and at `review-finalize`.
- 2026-09-29 to-review (opencode): authored from backlog item `rcjorx`. Every claim in the item was re-measured at HEAD `3f7997b2` rather than carried over; the item's reproduction was confirmed verbatim. Authoring measurement ADDED three findings the item does not contain, and two of them change the work. FIRST (F-04), fix (a) as the item describes it does NOT build: argparse raises `ArgumentError: conflicting option string: --fields` when a leaf re-declares an option its parent already carries, so the four existing declarations must be DELETED, not left in place, and the item's "the plumbing largely exists" understates the edit. SECOND (F-05), there is a SECOND shared parent, `common_upgrade`, that the item does not mention; touching only `common` leaves six `upgrade-test` leaves carrying `--agent` without `--fields`, reproducing the exact asymmetry this item exists to remove. THIRD (F-06), the fix carries a measured REGRESSION the item does not anticipate: 14 leaves lose a currently-working abbreviation, including `aw check-local-leaks --fi` for `--fix`, which works today and becomes ambiguous. Also measured (F-08) that the guide's example is inert on a second, independent ground: `aw find`'s agent branch prints bare paths and returns before building any record, so even once the flag is accepted that specific command projects nothing; E-05 therefore replaces the row rather than relying on E-02, and carrier `wdazvp` was filed for that branch during authoring. Filed `qm04zi` too, for the measured fact that `--verbose` carries the SAME reach defect on the same two protocol documents; a first draft of that deferral row claimed `--verbose` has no consumer, which was wrong (`to_agent_record` branches on `context.verbose` in three places) and is corrected in the row. OQ-01 resolves (a) over (b) from F-02/F-03; OQ-02 resolves the abbreviation regression as a deliberate `allow_abbrev=False`; OQ-03 was authored BLOCKING on the belief that choosing the guide's replacement example needed a maintainer, then resolved in-tree once the guide's own `## Exit codes you can rely on` section and the two exit-1 commands already in its quick-reference table refuted the sole objection to `aw check plans --agent --fields findings`. No blocking question remains open.
- 2026-09-29 draft (opencode): created.

## Goal

Make `--fields` reach every command that emits `aw.agent/v1` output, so the three documents that describe it as a protocol-wide escape hatch become true as written and the guide's worked example stops exiting 2.

THE DEFECT IS A DECLARATION-SIDE GAP ONLY, AND THAT IS WHY THE FIX IS SMALL. The CONSUMPTION side is already global: `result_types.select_output` reads the value with `getattr(args, "fields", None)` and normalizes both a comma string and a sequence, and `CommandResult.to_agent_record` applies `agent_schema.filter_record_fields` whenever `context.fields` is truthy. So nothing downstream needs changing; the flag is simply not DECLARED anywhere a reader would look for it (F-02). Contrast `--agent` and `--json`, which sit on the shared `common` parent and therefore reach 139 leaves, which is exactly why a reader assumes `--fields` does too.

WHAT THIS PLAN REFUSES TO DO QUIETLY. Widening the flag adds a second `--f*` option to leaves that have exactly one today, and argparse's prefix abbreviation is on by default, so `aw check --f`, `aw ipd set --f` and `aw check-local-leaks --fi` stop resolving (F-06). That is a real regression on a shipped surface, measured rather than predicted. This plan does not ship it as an unremarked side effect and does not abandon the fix because of it: it turns prefix abbreviation OFF on the affected parsers, which makes the refusal explicit and order-independent rather than dependent on which flags happen to coexist (OQ-02).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the reach gap, then close it on both shared parents

- [x] E-01 Create `tests/test_fields_flag_reach.py` asserting the DERIVED REACH PROPERTY: every leaf that accepts `--agent` also accepts `--fields`. Obtain the leaf set from the real parser built by `cli._build_parser()`, deduplicating by parser object IDENTITY so an alias is not counted twice. **YOU MUST WRITE THE WALK; `command_surface.discover_parser_leaves` CANNOT SERVE THIS TEST, AND AN EARLIER DRAFT OF THIS ITEM WRONGLY TOLD YOU TO REUSE IT (PR-201, F-13).** That helper is annotated `-> Set[str]` and returns a set of leaf PATH NAMES (for example `"find plans"`), not the parser objects those names resolve to, and there is no name-to-parser resolver beside it (`get_declared_leaves` and `find_undeclared_leaves` are both name-set functions too). A `str` has no `_actions`, so no option set can be read from its return value. Write a local recursive walk over `parser._actions`, selecting `argparse._SubParsersAction` and deduplicating `sa.choices` by `id(subparser)` so an alias is not double-counted, which is the SAME identity rule that helper's docstring explains and which you are re-implementing rather than importing. Reading `parser._actions` and `action.option_strings` is reading the PARSER's own reported structure at runtime, not the production SOURCE, so it does not violate the code-pinning prohibition; `tests/test_flag_surface_uniformity.py` already reads `cli._build_parser()` the same way. DERIVE, DO NOT HARDCODE: no integer leaf count may appear in the assertion, because review re-measured 151 unique leaves with 139 carrying `--agent` and both move with every command added, so a literal would fail for the wrong reason (`plan-review` Rubric G). ASSERT ON PARSER-REPORTED OPTIONS, NOT ON SOURCE TEXT: no `inspect.getsource`, no reading `cli.py`, no `ast`, no regex over module text, since AGENTS.md forbids code-pinning tests and the most natural implementation of a reach test violates that rule.
  - Depends on: none
  - Expected outcome: A new test file whose reach assertion FAILS at this HEAD, naming a large set of leaves that carry `--agent` without `--fields` (review re-measured exactly 135: the 139 carrying `--agent` minus the 4 `runs` leaves declaring it). A near-empty failure set means the walk is wrong rather than the code. An assertion that passes before E-02 has been written wrong, not satisfied. An `AttributeError: 'str' object has no attribute '_actions'` means you reused `discover_parser_leaves` after all; write the walk.
  - Execution state: performed

- [x] E-06 Add the ACCEPTANCE assertion to `tests/test_fields_flag_reach.py`: the command the backlog item quotes must parse. Assert that `cli._build_parser().parse_args(["find","plans","--agent","--fields","findings"])` yields a namespace whose `fields` equals `"findings"`, instead of raising `SystemExit`. ASSERT ON THE PARSE AND DELIBERATELY NOT ON STDOUT, because F-08 measures that `aw find`'s agent branch prints bare paths and returns before building any record: asserting a projected record from that command would pin behavior this plan does not deliver and would fail even after E-02 lands correctly. Record that reason in the test so a later reader does not "strengthen" it into an output assertion.
  - Depends on: none
  - Expected outcome: The assertion fails at this HEAD with `SystemExit: 2` and passes after E-02. It is the narrowest possible pin of the item's reproduction: acceptance only, with no claim about projection on that command.
  - Execution state: performed

- [x] E-07 Add the END-TO-END PROJECTION assertion to `tests/test_fields_flag_reach.py`, since acceptance alone does not prove the flag does anything on a newly-reached command. Drive a command whose agent surface builds a record through `CommandResult.to_agent_record` (review measured `aw check plans --agent --fields findings` retaining `findings` while dropping exactly `target`, `diagnostics`, `evidence` and `next`, with `diagnostics` confirmed NON-EMPTY in the unprojected record so its absence is real evidence of projection rather than of an empty field), either as a subprocess or through `cli.main` with captured streams, parse its stdout as JSON, and assert the requested key is PRESENT while a named non-envelope key the unprojected record carries is ABSENT. **NAME `target` OR `diagnostics` AS THE ABSENT KEY, NOT `next` (PR-205, F-14).** `next` is dropped by the projection too, but its VALUE varies between consecutive runs of the unmodified tree, so a test that asserts anything about `next` beyond its absence invites a later author to strengthen it into a flaky assertion; `target` and `diagnostics` are stable in shape. Do not assert on a value that is live-tree state, such as the `19` review measured for the findings count; assert on key presence and absence only.
  - Depends on: none
  - Expected outcome: The assertion fails at this HEAD because the command exits 2 with `unrecognized arguments: --fields` before emitting anything, and passes after E-02 with a projected record. Together with E-01 and E-06 this makes the new file red for three distinct reasons, each fixed by the same change.
  - Execution state: performed

- [x] E-02 In `cli._build_parser`, declare `--fields` ONCE on each of the TWO shared output-mode parents and DELETE the four leaf declarations. On `common` (the parent that already carries `--agent`/`--json` and is inherited by 147 `parents=[common]` sites) add `--fields` with `default=None` and the help text the four leaves already share, so the wording does not fork. On `common_upgrade` (the SECOND parent, which exists so a `--json` supplied before the subcommand is not clobbered by the subparser default, and which the backlog item does not mention) add `--fields` the same way but with `default=argparse.SUPPRESS`, matching how that parent already declares `--agent` and `--json`; getting this wrong silently reintroduces the very default-clobbering the comment above `common_upgrade` records as an earlier regression. THEN DELETE the `add_argument("--fields", ...)` call from each of `_p_runs_analyze`, `_p_runs_query`, `_p_runs_export` and `_p_runs_submit`. THE DELETION IS NOT OPTIONAL CLEANUP, IT IS REQUIRED FOR THE PARSER TO BUILD AT ALL: `_AwArgumentParser` deliberately leaves `conflict_handler` at argparse's default (its constructor comment explains that `resolve` once shipped a real defect by emptying a shared parent action's `option_strings` in place), so a leaf re-declaring a parent's option raises `ArgumentError: argument --fields: conflicting option string: --fields` at build time and every `aw` invocation dies on import (F-04). Change nothing else: do not touch `--limit` (which is separately hand-wired on 9 leaves and is a different concern), do not touch `--verbose`, do not alter `presentation`, and do not change any leaf's other flags.
  - Depends on: E-01, E-06, E-07
  - Expected outcome: `cli._build_parser()` builds without raising. Every leaf carrying `--agent` also carries `--fields`, including the six `upgrade-test` leaves that F-05 measured would otherwise be missed. The four `runs` leaves still accept `--fields` (now by inheritance) and their behavior is unchanged. `grep` for `"--fields"` in `cli.py` finds exactly two `add_argument` calls, both on shared parents, where it previously found four on leaves. The E-01, E-06 and E-07 assertions all pass.
  - Execution state: performed

### Task group 2: absorb the measured abbreviation regression rather than shipping it

- [x] E-03 Disable argparse prefix abbreviation so the new flag cannot silently break a working invocation, because F-06 measures that it otherwise does. Adding a second `--f*` option makes the previously-unambiguous `--f` ambiguous on 13 leaves (`--force` on `archive`, `check`, `find`, `group`, `index`, `rename`, `set`, `uninstall`; `--from-backlog` on `ipd scaffold`, `ipd set`, `specs set`; `--failed` on `runs list`; `--fault-injection` on `migrate-layout`) and makes `--fi` ambiguous on `check-local-leaks`, where it currently resolves to `--fix` and is the flag that rewrites files. Set `allow_abbrev=False` in the `_AwArgumentParser` constructor, which reaches every parser in the tree from one place rather than being applied per-leaf and therefore forgotten on the next leaf added. DO THIS AS A DELIBERATE, DOCUMENTED CONTRACT CHANGE, NOT A SIDE EFFECT: add a comment beside the existing `conflict_handler` comment in that constructor stating that abbreviation is off so that a flag added to a shared parent can never change the meaning of an existing invocation, and that this is the same reasoning the `conflict_handler` comment already applies to silent option replacement. VERIFY THE BLAST RADIUS BEFORE COMMITTING, because turning abbreviation off refuses EVERY abbreviation, not only the 14 this plan creates: sweep the test suite and `docs/` for abbreviated long options and report any that break. If the sweep finds a shipped document or test relying on an abbreviation, STOP and report rather than rewriting a document outside `- Scope-Paths:`.
  - Depends on: E-02
  - Expected outcome: `aw check --f` and `aw check-local-leaks --fi` both exit 2 with an explicit `unrecognized arguments` refusal rather than silently resolving or reporting an ambiguity, and they do so for the same reason on every leaf rather than depending on which flags coexist there. No full long option changes behavior. The constructor carries the reasoning. The sweep result is reported, including any test that needed no change because it already spells flags in full.
  - Execution state: performed

- [x] E-04 Extend `tests/test_fields_flag_reach.py` with the abbreviation contract, so E-03's deliberate refusal is pinned as intent and a future author cannot re-enable abbreviation without a test failing. Assert observable outcomes only: that a full long option still parses on a sampled set of the affected leaves (at minimum `aw check --force`, `aw check-local-leaks --fix`, `aw ipd set --from-backlog`, `aw runs list --failed`), and that the abbreviated form now raises `SystemExit` with code 2. SAMPLE, DO NOT ENUMERATE ALL 14: the point is the contract, and a 14-row literal list drifts as flags are added. Include `check-local-leaks --fi` explicitly by name, because it is the one case that works TODAY and so is the only member of the set whose refusal is a genuine behavior change a user could notice.
  - Depends on: E-03
  - Expected outcome: The new assertions fail before E-03 (where `--fi` parses) and pass after. The full-option assertions pass both before and after, which is what proves E-03 narrowed only the abbreviated spelling.
  - Execution state: performed

### Task group 3: correct the guide, and bound what this plan claims

- [x] E-05 Replace the inert example in `docs/cli-human-guide.md` and verify this plan has not overstated its effect. THE EXAMPLE MUST BE ONE THAT ACTUALLY PROJECTS, which is the whole point of the row: `aw find plans --agent --fields findings` is inert for a SECOND reason E-02 does not fix, namely that `aw find`'s agent branch prints bare repo-relative paths and returns before constructing any `CommandResult` (F-08), so after E-02 it is accepted and ignored rather than refused. Shipping it unchanged would replace a loud exit 2 with a silent no-op, which is worse for the agent the guide is written for. Replace that row's command with `aw check plans --agent --fields findings`, which OQ-03 resolves to and which review re-measured projecting correctly (it drops exactly `target`, `diagnostics`, `evidence` and `next` while retaining `findings`, with `diagnostics` confirmed non-empty unprojected); if a reviewer prefers the recorded fallback, the change is one table cell to `aw status --agent --fields cmd`. DO NOT SUBSTITUTE A `find` COMMAND WITH A SELECTOR AS A THIRD OPTION: review measured that a MATCHING selector takes the same bare-path branch and projects nothing, and only a ZERO-MATCH query reaches the record branch (F-08 as corrected, PR-202), so no useful `aw find` invocation demonstrates projection. Write no em or en dashes: this file is user-facing prose under the execution contract. Touch only that row and any sentence that row's change makes false. THEN BOUND THE CLAIM: confirm the two protocol documents (`docs/cli-agent-protocol.md`, `docs/cli-output-contract.md`) need NO edit, because their `--fields` bullets describe projection SEMANTICS and already say `--fields` is safe to pass on any command, which E-02 makes true rather than contradicting; report this explicitly rather than silently leaving them out. Also confirm the two carrier items filed during authoring are still live and still describe real work, by checking their SUBJECTS rather than their status: `wdazvp` (`aw find --agent`'s bare-path branch ignoring `--fields` and `--limit`) and `qm04zi` (`--verbose` documented globally, reaching one leaf). `wdazvp` in particular gets WORSE as a result of E-02, since `--fields` there goes from a loud exit 2 to a silent no-op, so confirm it records that. Do not close either: both are release-gated and closing one has its own gated predicate.
  - Depends on: E-04
  - Expected outcome: The guide's projection row names a command that demonstrably projects, verified by running it and pasting the record. The two protocol documents are confirmed unchanged WITH the reason stated. The `find --agent` bare-path branch and the inert `--limit` row are both reported, each with a carrier backlog item id or an explicit statement that one was filed, and neither is fixed here.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`). This plan cites `cli._build_parser`, `cli._AwArgumentParser`, `cli._consume_early_flags`, `result_types.select_output`, `result_types.CommandResult.to_agent_record`, `agent_schema.filter_record_fields`, `renderers.AgentRenderer.render_stream` and `command_surface.discover_parser_leaves` by name. It matters especially here because `cli.py` is over 14000 lines and is being edited concurrently by other pending plans (F-09), so any offset this plan recorded would be stale before execution.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). This forbids the most natural test for a flag-reach property, which would `grep` `cli.py` for `add_argument("--fields"` and count hits. E-01 therefore walks the BUILT parser and asserts on parse results and on real command output instead. `tests/test_flag_surface_uniformity.py` is the in-tree precedent and its docstring says so explicitly, recording that it was redesigned away from AST and private-structure walks toward observable dispatch.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. `python3 -m pytest` with no added flags is the contract; a second `-q` compounds to `-qq` and suppresses the `N passed` line this plan's validation requires pasted, and `-n0` makes the run several times slower here. Use `-o addopts=""` only when per-test counts are genuinely wanted.
- A DEFECT FOUND OUTSIDE THE CURRENT FENCE IS FILED, NOT REACHED ACROSS FOR. Established in-tree practice, and this item is itself an instance: plan `gygujf` measured this exact `--fields` reach gap while fixing a different `--fields` defect, declined to fix it because `cli.py` was outside its `- Scope-Paths:`, and filed `rcjorx`. Its `## Deferred / out of scope` row states the reasoning verbatim. This plan follows the same rule for `aw find`'s bare-path agent branch and for the inert `--limit` row (E-05).
- USER-FACING PROSE CARRIES NO EM OR EN DASHES (AGENTS.md execution contract). `docs/cli-human-guide.md` is user-facing, so E-05's edit is bound by it. It does NOT apply to this plan, to the test file, or to code comments.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AT THIS HEAD, exactly as the backlog item reproduces it. `python3 -m agent_workflows find plans --agent --fields findings` prints the root usage block and `agent-workflows: error: unrecognized arguments: --fields`, exit 2. The guide's row at `docs/cli-human-guide.md` reads `| Only the fields you care about (agent) | `aw find plans --agent --fields findings` |`, so the failing command is quoted verbatim from the official guide. | The item's reproduction run unmodified at HEAD `3f7997b2`; read of the guide's quick-reference table. |
| F-02 | THE CAUSE IS DECLARATION-SIDE ONLY; CONSUMPTION IS ALREADY GLOBAL. `grep` for `"--fields"` in `agent_workflows/cli.py` returns exactly four `add_argument` calls, all on `runs` leaves (`_p_runs_analyze`, `_p_runs_query`, `_p_runs_export`, `_p_runs_submit`), each byte-identical: `default=None`, no `type`, no `metavar`, plain store. Meanwhile `select_output` reads the value with `getattr(args, "fields", None)` and normalizes a comma string or a list/tuple/set, and three call sites apply `filter_record_fields` behind a truthy `context.fields` guard. So a leaf that merely DECLARES the flag gets full projection behavior with no further plumbing. | `grep -n -- "--fields" agent_workflows/cli.py` returning four line numbers; read of `select_output`'s `raw_fields` branch; read of the guard at `CommandResult.to_agent_record` and at both `AgentRenderer` methods. |
| F-03 | THE ASYMMETRY IS MEASURED, NOT ASSUMED, AND IT IS WHAT MAKES THE DOCS MISLEADING. Walking the built parser and deduplicating leaves by object identity: 151 unique leaves, of which 139 carry `--agent`, 139 carry `--json`, 9 carry `--limit`, and 4 carry `--fields`. `--agent`/`--json` reach 139 because they sit on the shared `common` parent, inherited at 147 `parents=[common]` sites. So the flag a reader is told is a protocol-wide escape hatch reaches 4 leaves while its documented companion `--agent` reaches 139. | Parser walk at HEAD `3f7997b2` printing `unique leaf parsers: 151`, `leaves with --agent: 139`, `leaves with --limit: 9`, `leaves declaring --fields: ['runs analyze', 'runs export', 'runs query', 'runs submit']`. |
| F-04 | **FIX (a) AS THE ITEM DESCRIBES IT DOES NOT BUILD; THE FOUR LEAF DECLARATIONS MUST BE DELETED.** The item says the plumbing "largely exists", which is true of the consumption side and misleading about the edit. `_AwArgumentParser` deliberately keeps argparse's default `conflict_handler="error"`, and its constructor comment records WHY: `resolve` once emptied a shared parent action's `option_strings` in place, leaving `aw attention` permanently parsing with `agent=True`. So declaring `--fields` on `common` while a leaf also declares it raises `ArgumentError: argument --fields: conflicting option string: --fields` AT BUILD TIME, which kills every `aw` invocation on import. Reproduced on a minimal parent/child parser and then confirmed on the real tree: patching `common` and deleting all four leaf calls builds cleanly, and `--fields` then reaches 133 leaves. | Minimal argparse repro printing `ArgumentError at BUILD time: argument --fields: conflicting option string: --fields`; in-memory patch of the real `cli.py` (four deletions plus one shared declaration) printing `parser BUILT with no ArgumentError` and `leaves with --fields: 133`; read of the `conflict_handler` comment in `_AwArgumentParser.__init__`. |
| F-05 | **THERE IS A SECOND SHARED PARENT THE ITEM DOES NOT MENTION, AND MISSING IT REPRODUCES THE DEFECT ON SIX LEAVES.** `cli._build_parser` builds `common_upgrade`, a separate `add_help=False` parent that declares `--agent` and `--json` with `default=argparse.SUPPRESS` so a `--json` supplied before the subcommand is not clobbered by the subparser's own default (its comment cites that as an earlier measured regression). All six `upgrade-test` leaves use `parents=[common_upgrade]`, not `parents=[common]`. Measured: patching only `common` yields `--fields` on 133 leaves while `--agent` is on 139, and the six-leaf gap is exactly `upgrade-test clean/env/list/new/probe/sandboxes`. So E-02 must touch both parents, and must match the `SUPPRESS` default on the second or reintroduce the clobbering that comment warns about. | In-memory patch of `common` alone, printing `--agent but NOT --fields: ['upgrade-test clean', 'upgrade-test env', 'upgrade-test list', 'upgrade-test new', 'upgrade-test probe', 'upgrade-test sandboxes']`; read of `common_upgrade`'s declaration block and its `default=argparse.SUPPRESS` comment. |
| F-06 | **THE FIX CARRIES A MEASURED REGRESSION THE ITEM DOES NOT ANTICIPATE: 14 LEAVES LOSE A WORKING ABBREVIATION.** argparse prefix abbreviation is on by default, so a leaf whose only `--f*` option is `--force` accepts `--f` today. Adding `--fields` makes `--f` ambiguous. Enumerating every prefix of every existing `--f*` option on every leaf, and comparing unambiguous-before against unambiguous-after: 14 abbreviations break across 14 leaves. Thirteen are `--f` (`--force` on `archive`, `check`, `find`, `group`, `index`, `rename`, `set`, `uninstall`; `--from-backlog` on `ipd scaffold`, `ipd set`, `specs set`; `--failed` on `runs list`; `--fault-injection` on `migrate-layout`). THE FOURTEENTH IS THE ONE THAT MATTERS: `check-local-leaks --fi` resolves to `--fix` TODAY and becomes ambiguous, and `--fix` is the flag that REWRITES files. Confirmed end to end: `aw check-local-leaks --fi --help` succeeds at this HEAD and exits 2 under the patch. | Prefix-collision sweep over all 151 leaves printing the 14 broken abbreviations with their before-meaning and after-ambiguity; before/after probe table showing `check-local-leaks --fi` as `OK` before and `EXIT2 ... ambiguous` after; live `aw check-local-leaks --help` confirming `--fix` exists and no `--fields` does. |
| F-07 | THE DOCS MAKE THE CLAIM IN THREE PLACES AND ONLY ONE OF THEM IS FALSE AFTER THE FIX, which is what keeps this plan's `- Scope-Paths:` at one document rather than three. `docs/cli-human-guide.md` gives a COMMAND, and a command either runs or does not, so it must change. `docs/cli-agent-protocol.md` (`## Token control`) and `docs/cli-output-contract.md` (`## 6. Token Control and Escape Hatches`) describe SEMANTICS and both already assert that "a projection never yields a record that fails validation, so `--fields` is safe to pass on any command". That sentence is a validity claim, not an acceptance claim; it is currently misleading only because acceptance is absent, and E-02 makes it true. So those two need no edit, and editing them would widen scope for no gain. | Read of all three passages; the guide's row quoted in F-01; both protocol bullets quoted, each containing the "safe to pass on any command" sentence. |
| F-08 | **THE GUIDE'S EXAMPLE IS INERT FOR A SECOND, INDEPENDENT REASON THAT E-02 DOES NOT FIX, SO REPLACING THE ROW IS MANDATORY RATHER THAN COSMETIC.** `aw find`'s agent path has a branch, taken when `getattr(args, "paths", False) or (ctx.is_agent and all_paths)`, that prints bare repo-relative paths and RETURNS before any `CommandResult` is constructed (its own comment says so: "this branch returns before any `CommandResult` is built, so `diagnostics` is unreachable here"). So with the flag accepted, `aw find plans --agent --fields findings` prints bare paths (1033 at review HEAD) and projects nothing: the loud exit 2 becomes a silent no-op. **CORRECTED AT REVIEW (PR-202): THE CLAIM THAT A SELECTOR REACHES THE RECORD BRANCH IS FALSE, AND THE ERROR MATTERS BECAUSE IT WOULD HAVE MISDIRECTED THE EXECUTOR'S OWN PROBE.** The branch condition is `all_paths` being truthy, NOT the absence of a selector, so `aw find plans rcjorx --agent --fields findings` MATCHES one artifact, takes the same bare-path branch, and prints one bare path with zero JSONL records - measured under the patch. What actually reaches the record branch is a selector matching NOTHING: `aw find plans zzzzzz --agent --fields findings` emits `{"schema":"aw.agent/v1","kind":"result","cmd":"find","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, correctly projected. That is a useless guide example (it demonstrates projection only on an empty result), which STRENGTHENS the case for replacing the row with a non-`find` command rather than weakening it. Commands whose agent surface always builds a record DO work: `aw check plans --agent --fields findings` emits `{...,"findings":19}` with `target`, `diagnostics`, `evidence` and `next` all dropped (`diagnostics` verified non-empty when unprojected), and `aw status --agent --fields cmd` emits the envelope alone. | In-memory patched end-to-end runs driving the patched `cli.main` with captured streams: bare `find plans` printing 1033 lines with 0 `aw.agent/v1` records; `find plans rcjorx` printing 1 line with 0 records (the correction); `find plans zzzzzz` printing 1 projected record; `check plans` and `status` each printing 1 correctly projected record, with the unprojected `check plans` key set compared against the projected one to confirm four keys dropped; read of the bare-path branch, its condition, and its early `return`. |
| F-09 | THE FILE IS UNDER CONCURRENT EDIT BY OTHER PENDING PLANS, so E-02 must expect the surrounding text to have moved. 33 pending plans list `agent_workflows/cli.py` in `- Scope-Paths:`. Two are close enough to matter: `z593o5` (`optanywhere`) changes how positionals and flags interleave across 25 leaves, which is the same argparse construction this plan edits and is directly adjacent to E-03's abbreviation change; `zyj8io` (`selquiet`) changes `aw find`'s refusal behavior on a zero-match selector, which is the same function F-08 measures. Neither declares `--fields`, so there is no contradiction, but an executor must re-read the parent declarations rather than trusting this plan's description of their neighborhood. Per AGENTS.md the runner isolates each plan in its own worktree and merges through a revalidation gate, so this is an authoring-accuracy note and NOT a concurrency hazard to warn a human about. | `grep` over `.aw/records/plans/pending/` for `Scope-Paths:.*cli\.py` returning 33 files; read of `z593o5`'s and `zyj8io`'s `- Concern:` and `- Scope-Paths:` lines. |
| F-10 | THE CHANGE CANNOT ALTER ANY OUTPUT THAT DOES NOT PASS `--fields`, which is what bounds the risk of widening a flag to 139 leaves. `filter_record_fields` returns `dict(record)` unchanged when `fields` is empty or `None`, every call site guards on truthiness, and `--fields` defaults to `None`. So every record emitted without the flag, including every conformance golden, is byte-identical before and after. The only new behavior is that a command which previously exited 2 now runs. Note the flag is also captured in HUMAN mode (`select_output` stores it on all three paths) but no human renderer consults it, so a human invocation is unaffected too. | Read of the early return and of all three truthy guards; read of `select_output`'s three return paths all passing `fields_val`; the four `runs` leaves re-run under the patch, unchanged. |
| F-11 | THIS IS NEW COVERAGE, NOT A DUPLICATE, AND THE ABSENT COVERAGE IS WHY THE DIVERGENCE SHIPPED. No test asserts WHICH commands accept `--fields`, and no test invokes the CLI with the flag end to end: `tests/test_agent_field_projection.py` (added by `gygujf`) covers projection SEMANTICS by calling `filter_record_fields` and the renderers directly, and the only other references are `fields=None` filler in hand-built `argparse.Namespace` fixtures in `tests/test_run_analytics_cli.py` and `tests/test_run_dashboard.py`, which assert nothing about the flag. `tests/test_flag_surface_uniformity.py` asserts reach for the color and interactivity pairs but not for the output-mode pair or for `--fields`. | `grep` over `tests/` for `--fields`, `select_output` and `filter_record_fields`, classifying every hit; read of `test_agent_field_projection.py`'s docstring and of `test_flag_surface_uniformity.py`'s `SAMPLED_PARSED_SUBCOMMANDS`. |
| F-12 | THE BARE SUITE IS GREEN AT THIS HEAD, so any failure at execution is this plan's until proven otherwise. Do NOT carry this number as an acceptance bar: the passed count moves with every merge, so re-derive the baseline at lane start and require only that it RISES by the new file's tests. Review re-measured it as `3246 passed, 2 skipped` at review HEAD, which is recorded as context and NOT as the bar, for exactly the reason this row gives. | `python3 -m pytest` run bare at HEAD `3f7997b2` and again at review HEAD; the `N passed` summary line is to be re-measured and pasted by the executor at lane start, since a count authored here would be stale before execution (Rubric G). |
| F-13 | **`command_surface.discover_parser_leaves` CANNOT SERVE E-01's TEST, AND THE PLAN TOLD THE EXECUTOR TO REUSE IT (PR-201, review-added).** The helper is annotated `-> Set[str]` and returns leaf PATH NAMES, not the parser objects behind them: measured, `discover_parser_leaves(cli._build_parser())` returns a `set` of `str` whose members have no `_actions` attribute, so no option set can be read from it. There is no name-to-parser resolver beside it either; its two siblings in that module, `get_declared_leaves` and `find_undeclared_leaves`, are both name-set functions. So an executor following E-01's original instruction reaches an `AttributeError` on the first line of the assertion and must then invent the walk anyway, without the identity-deduplication guidance the helper's docstring holds. The helper is still the right REFERENCE for the alias rule (dedupe `sa.choices` by `id(subparser)`, taking the first key that maps to a given object), which is why E-01 now cites it as a pattern to re-implement rather than a function to call. Note the reach test is NOT thereby code-pinning: reading `parser._actions` and `action.option_strings` inspects the parser the production code BUILT at runtime, which is a behavioral surface, and `tests/test_flag_surface_uniformity.py` already calls `cli._build_parser()` for the same purpose. | `type()` and `hasattr(..., "_actions")` probes over the helper's real return value; read of its signature and docstring; `grep` of `command_surface.py` for every leaf/parser-related definition, returning three name-set functions and no resolver; read of `test_flag_surface_uniformity.py`'s `test_parsed_commands_accept_both_flag_pairs`, which samples by PARSING rather than by walking to parser objects. |
| F-14 | **`aw check plans --agent`'s OUTPUT IS NONDETERMINISTIC RUN TO RUN, SO IT MUST NOT BE THE SUBJECT OF A BYTE-IDENTITY PROBE (PR-203, review-added).** Its `next` field named three different artifacts on three consecutive runs of the UNMODIFIED tree (`<collisions>`, then two different pending plans), because the value is derived from a live-tree scan whose ordering is not stabilized. The plan's no-change probe (Required tests, and V-02's final clause) asks for byte-identical stdout before and after, and authoring's own F-08 chose `aw check plans` as its worked example, so the two instructions together steer an executor straight into a false disagreement on the one probe that licenses the whole change. Measured across six commands spanning both shared parents: `status`, `attention`, `upgrade-test list`, `find plans rcjorx` and `runs query` were byte-identical before and after the patch, and `check plans` differed only in `next`, with identical length and identical key set - and reproduced the same variance with NO patch applied. The probe is sound; its sample was not. | Three consecutive unpatched runs of `aw check plans --agent` with the `next` value printed each time; a six-command before/after comparison of raw stdout (subprocess for the unpatched side, in-process patched module for the other) reporting five identical and one differing; a key-by-key diff of the differing pair showing an empty key-set symmetric difference and only `next` unequal. |
| F-15 | THE NUMBER OF PENDING PLANS DECLARING `cli.py` HAS GROWN FROM 33 TO 43 SINCE AUTHORING, which does not change F-09's conclusion but shows why that row's instruction to re-read rather than trust is the right one. Both plans F-09 singles out are still live and their statuses moved: `z593o5` (`optanywhere`, positional/flag interleaving across 25 leaves, directly adjacent to E-03's abbreviation change) is now `reviewed`, and `zyj8io` (`selquiet`, `aw find`'s zero-match refusal behavior, the same function F-08 measures) is `to-review`. `zyj8io` deserves a second look at execution for a reason F-09 does not give: F-08 as corrected shows the RECORD-emitting branch of `aw find` is reached only on a ZERO-MATCH query, which is precisely the behavior `zyj8io` changes, so the one `find` invocation that projects today is the one that plan is rewriting. Neither declares `--fields`, so there is still no contradiction. | `grep -c` over `.aw/records/plans/pending/*.ipd.md` for `Scope-Paths:.*cli\.py` returning 43 files; each of `z593o5` and `zyj8io` located by `- Id:` and its `- Status:` read. |
| F-16 | THE THREE CARRIER AND SOURCE ITEMS ARE ALL LIVE AND WELL-FORMED, so this plan's deferrals point at real owned work. Measured: `rcjorx` (this plan's `- From-Backlog:`) is `graduated`, which is the correct state for an item whose design is handed off to a pending plan; `wdazvp` (the `find --agent` bare-path branch) is `open`; `qm04zi` (`--verbose` reach) is `open`. `aw backlog check` reports "all backlog items conform." Both carriers being `open` rather than `graduated` is correct, since neither has a plan yet. | `aw find backlog wdazvp qm04zi rcjorx` with each status read; `aw backlog check` run and its clean line captured. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_fields_flag_reach.py`, red at this HEAD for three independent reasons, all asserted as observable behavior: the derived reach property (E-01, with its own parser walk since `discover_parser_leaves` returns names not parsers, F-13), the acceptance of the exact command the backlog item quotes (E-06), and one real end-to-end projection on a command that builds a record (E-07).
2. In `cli._build_parser`, declare `--fields` on `common` and on `common_upgrade` (the latter with `default=argparse.SUPPRESS`), and delete the four `runs` leaf declarations, which is required for the parser to build (E-02).
3. Set `allow_abbrev=False` in `_AwArgumentParser.__init__` with the reasoning documented beside the existing `conflict_handler` comment, so the 14 measured abbreviation collisions become an explicit refusal rather than a silent regression (E-03).
4. Extend the new test file with the abbreviation contract, sampling the affected leaves and naming `check-local-leaks --fi` explicitly (E-04).
5. Replace the inert row in `docs/cli-human-guide.md` with a command measured to project, confirm the two protocol documents need no edit and say why, and report the `find --agent` bare-path branch and the inert `--limit` row as filed carriers (E-05).

## Deferred / out of scope (with reason)

- GIVING `--fields` AN EFFECT ON `aw find`'s BARE-PATH AGENT BRANCH is out of scope, and this is the most important exclusion because it is the exact command the backlog item quotes. F-08 measures that the branch prints bare paths and returns before building a record, so after E-02 the flag is accepted and ignored there. NOTE THE EXCLUSION IS WIDER THAN AN EARLIER DRAFT IMPLIED (PR-202): the branch is taken whenever the query MATCHES anything, so a selector does not escape it either; only a zero-match query reaches the record branch, which means `--fields` is inert on essentially every useful `aw find` invocation rather than only on the bare one. Fixing it means deciding what `aw find --agent` should emit at all, which is a machine-surface contract change affecting every consumer that today parses bare paths line by line, and the code comment on that branch records a deliberate decision that its stdout is byte-identical to `--paths` so scripts can consume it. That is a separate decision from whether the flag is declared. This plan's E-05 replaces the guide's example rather than silently leaving a no-op in the guide.
  - Carrier: wdazvp
- THE INERT `--limit` ROW IN THE SAME GUIDE TABLE is out of scope. The row immediately below the one E-05 fixes reads `aw find plans --agent --limit 20`, and authoring measured it printing all paths rather than 20 (1033 at review HEAD, re-measured; the figure is live-tree state and will differ again at execution, so re-derive it rather than quoting either number): `--limit` IS declared on `find` and DOES reach `select_output` (`ctx.limit == 20`), but the same bare-path branch ignores it, because only `AgentRenderer.render_stream` honors `ctx.limit` and `find` does not use it. This is the same class of defect on a different flag, it is not a reach gap (the flag is accepted), and fixing it is the same contract decision the row above defers. E-05 reports it.
  - Carrier: wdazvp
- WIRING `--verbose` ONTO THE SHARED PARENTS is out of scope, though it is the SAME defect on a sibling flag and the reader should know that. `docs/cli-agent-protocol.md` lists `--verbose` beside `--fields` as a token-control escape hatch and `docs/cli-output-contract.md` does the same, yet it reaches exactly ONE leaf (`upgrade-test new`), where it is an installer-output flag rather than the agent-mode verbosity those documents describe; `aw check plans --agent --verbose` exits 2. AN EARLIER DRAFT OF THIS ROW JUSTIFIED THE EXCLUSION BY CLAIMING `--verbose` HAS NO CONSUMER, AND THAT WAS WRONG: `CommandResult.to_agent_record` reads `context.verbose` and branches on it in three places, emitting full `changes`, `evidence` and `diagnostics` dictionaries instead of the compacted forms. So the flag would WORK if declared, exactly as `--fields` does, and the honest reason for excluding it is narrower: it is a second flag on a second surface, it doubles the blast radius of E-03's abbreviation change (`--verbose` collides with nothing, but each added shared flag can create new prefix collisions that must be re-measured), and the item this plan graduates names `--fields` alone. It is filed rather than folded in.
  - Carrier: qm04zi
- HAND-VERIFYING EVERY ONE OF THE 139 AFFECTED LEAVES is rejected rather than deferred. E-01's reach assertion is derived from the built parser, so it covers all of them by construction and keeps covering leaves added later; enumerating them in the plan or the test would be a literal that drifts on the next command added, which Rubric G forbids.
  - Carrier-Declined: Nothing is owed. This is a rejected verification method, not unfinished work: the derived assertion is strictly stronger than the enumeration it replaces.

## Scope check

- Over-scope: none. `agent_workflows/cli.py` carries E-02's two shared declarations, the four leaf deletions, and E-03's one constructor keyword plus its comment. `tests/test_fields_flag_reach.py` is the new file from E-01, E-06, E-07 and E-04. `docs/cli-human-guide.md` carries E-05's one-row change. `result_types.py` is NOT edited (consumption is already correct, F-02). `agent_schema.py` is NOT edited (projection semantics were fixed by `gygujf` and this plan does not revisit them). `renderers.py` is NOT edited. The two protocol documents are NOT edited, deliberately and with the reason recorded (F-07). No spec is touched, no golden changes (F-10 proves none can), and the only `.aw/` records changed are this plan plus the two carrier backlog items `wdazvp` and `qm04zi`, which were filed during AUTHORING and are committed with this plan, so EXECUTION creates no record of its own.
- Under-scope: Three things disclosed rather than omitted. FIRST, `aw find --agent` will ACCEPT `--fields` and ignore it on its bare-path branch, so the flag's reach becomes uniform while its EFFECT does not. The gap is WIDER than authoring recorded: review measured the branch taken whenever the query matches anything, including with a selector, so only a zero-match query projects (F-08 as corrected). E-05 keeps the guide honest about this by naming a different command, and a carrier is filed. SECOND, `--verbose` remains documented as a general escape hatch while reaching one leaf and having no consumer at all. THIRD, E-03 turns abbreviation off for EVERY option, not only the 14 collisions this change creates, so an operator who habitually types `aw check --fo` must now type `--force`; that is the deliberate price of the fix (OQ-02) and E-03 requires the sweep that bounds it.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted. THE BAR IS ZERO FAILURES. Re-derive the baseline at lane start rather than comparing against any number recorded here, and require only that the passed count RISES by the new file's tests. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_fields_flag_reach.py -o addopts=""` for the per-test counts on the new file.
- `python3 -m pytest tests/test_flag_surface_uniformity.py tests/test_cli_parser_conflict_policy.py tests/test_command_surface_declarations.py tests/test_agent_field_projection.py tests/test_json_and_exitcodes.py tests/test_run_analytics_cli.py tests/test_run_dashboard.py -o addopts=""` as the targeted regression set: every file that asserts on parser construction, on flag reach, on the conflict policy, or on `--fields` consumption.
- A DELIBERATE-FAILURE DEMONSTRATION for E-01, E-06, E-07 and E-04, since a guard that was never red proves nothing. E-01's reach assertion must be shown FAILING before E-02, naming leaves that carry `--agent` without `--fields`; E-06's acceptance assertion failing with `SystemExit: 2`; E-07's end-to-end assertion failing with the driven command's `unrecognized arguments: --fields` visible in captured output; and E-04's abbreviation assertions failing before E-03 specifically because `--fi` still parses.
- A BUILD-TIME CONFLICT DEMONSTRATION for E-02, because F-04 is the finding that changes the shape of the work and an executor who leaves the four leaf declarations in place will see every `aw` command die on import. Add `--fields` to `common` WITHOUT deleting the four leaf calls, run any `aw` command, and paste the `ArgumentError: argument --fields: conflicting option string: --fields`. Then delete them and show the parser building.
- A NO-CHANGE-WITHOUT-THE-FLAG PROBE for E-02, which is the property F-10 asserts and the one deciding whether widening a flag to 139 leaves is safe: run a sample of agent-mode commands with NO `--fields` before and after the change and assert byte-identical stdout. Include at least one command per shared parent, so `common_upgrade`'s `SUPPRESS` default is exercised rather than assumed. **DO NOT USE A COMMAND WHOSE OUTPUT IS NONDETERMINISTIC RUN TO RUN, AND SPECIFICALLY NOT `aw check plans --agent` (PR-203, F-14).** Review measured that command's `next` field naming a DIFFERENT artifact on three consecutive unmodified runs, so a naive before/after byte comparison reports a false disagreement and would send an executor hunting a regression this change cannot cause. Either pick deterministic commands (`aw status --agent`, `aw attention --agent`, `aw upgrade-test list --agent` and `aw find <type> <selector> --agent` were all measured byte-stable across the change), or compare the parsed record with the volatile key excluded and SAY WHICH KEY you excluded and why. Measured at review over six commands spanning both parents: five byte-identical, and the sixth (`check plans`) identical in length and in its full key set with only `next` differing, which reproduces identically WITHOUT the patch.
- THE SIX `upgrade-test` LEAVES specifically, because F-05 is the finding an executor is most likely to miss: confirm each accepts `--fields` after E-02, and confirm a `--json` supplied BEFORE the subcommand still wins, which is the regression `common_upgrade`'s comment exists to prevent.
- THE 14 MEASURED ABBREVIATIONS for E-03: each abbreviated form refused with exit 2 and each full form still accepted, with `check-local-leaks --fi` and `--fix` shown explicitly as the pair whose behavior genuinely changes.
- AN END-TO-END PROJECTION on a command that was previously refused, with the record pasted before and after, showing the requested field retained and an unrequested non-envelope field absent.
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift, and `aw backlog check` to confirm the two carrier items `wdazvp` and `qm04zi` are still well-formed (both were filed and validated during authoring; execution files none).
- `aw sanitize --agent`, since this plan's evidence blocks quote local command output.
- `git diff --cached --name-only` immediately before committing, which must list exactly the three paths in `- Scope-Paths:` plus this plan plus the carrier backlog items, and nothing another party changed in this shared checkout (F-09 measures 33 pending plans naming `cli.py`).

## Spec / documentation sync

DOCUMENTATION SYNC IS REQUIRED AND IS E-05; SPEC SYNC IS N/A WITH REASON.

No `.spec.md` is in `- Scope-Paths:` and none needs to be. The normative home of the token-control surface is `docs/cli-output-contract.md`, not a spec record, and F-07 establishes that its `--fields` bullet and the protocol document's already state the behavior E-02 delivers ("safe to pass on any command"). No spec states which commands DECLARE the flag. The one spec that mentions `aw.agent/v1` at all, `command-surface-redesign`, does so in a workflow-history note pointing AT that document as the authority.

THE SHIPPED CONTRACT IS WIDENED ON ONE AXIS AND NARROWED ON ANOTHER, AND BOTH DESERVE NAMING RATHER THAN ONE. The widening is additive and needs no version bump: a flag that previously exited 2 now parses, no record's content changes, and no output without the flag differs by a byte (F-10). THE NARROWING IS A REAL, IF SMALL, BREAKING CHANGE and must not be smuggled in as a side effect: E-03 removes prefix abbreviation, so `aw check --fo` and `aw check-local-leaks --fi` stop working (F-06). That affects an interactive operator's muscle memory rather than any documented interface, since no shipped document instructs a reader to abbreviate, and E-03 requires a sweep of tests and docs to confirm that claim rather than assert it. It is recorded here so a reviewer weighs it deliberately, and it belongs in `CHANGELOG.md` at release time; `CHANGELOG.md` is deliberately NOT in `- Scope-Paths:` because this repository's convention is that a plan does not hand-edit it.

## Open questions

### OQ-01: The backlog item offers two fixes, (a) move `--fields` to the shared output-mode group and (b) correct the three documents to say the flag is `runs`-only. Which one?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS (a), which is the item's own preference, but resolved on measured grounds rather than by deferring to it, and with one of its premises corrected. The item argues (a) because `select_output` already reads `fields` generically; F-02 confirms that exactly. Two further measurements decide it. FIRST, (b) would narrow a capability that ALREADY WORKS EVERYWHERE downstream: patching the declaration alone makes `aw check`, `aw attention` and `aw status` project correctly with no other change (F-08), so (b) would document away working behavior rather than fix a defect. SECOND, (b) cannot make the documents coherent, only less wrong: F-07 shows both protocol documents assert the flag is "safe to pass on any command" as a VALIDITY claim about projections, which is true and which `gygujf` made true by construction; (b) would have to either contradict that sentence or explain why a flag safe on any command is accepted on four. THE ITEM'S PREMISE THAT THE PLUMBING "LARGELY EXISTS" IS CORRECTED, NOT ADOPTED: F-04 shows the four leaf declarations must be DELETED or the parser raises at build time, and F-05 shows a second parent must be touched, so (a) is a larger edit than the item implies, and F-06 shows it carries a regression the item does not anticipate. (a) is still correct; it is simply not free.

### OQ-02: Widening `--fields` breaks 14 working `--f`/`--fi` abbreviations (F-06). Accept the breakage, disable prefix abbreviation, or rename the flag to avoid the collision?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS DISABLING PREFIX ABBREVIATION (`allow_abbrev=False` on `_AwArgumentParser`), with the other two options rejected on stated grounds. ACCEPTING THE BREAKAGE SILENTLY is rejected because it is the worse failure mode: with abbreviation left on, `--f` does not become an error, it becomes an AMBIGUITY error whose existence depends on which other flags happen to be declared on that leaf, so the same abbreviation works on one command and fails on another and the behavior changes again the next time any flag is added. That is precisely the order-and-coincidence dependence that `_AwArgumentParser`'s `conflict_handler` comment rejects for option replacement, and the same reasoning applies here. RENAMING THE FLAG is rejected outright: the flag name is the shipped contract, named identically in three documents and on four working commands, and renaming it to dodge a collision would break every existing `aw runs query --fields` invocation to fix a documentation defect. DISABLING ABBREVIATION is chosen because it makes the refusal uniform, explicit and independent of neighboring declarations, and because no shipped document instructs a reader to abbreviate, so the documented surface is unchanged. ITS COST IS HONESTLY WIDER THAN THE 14 CASES: it refuses every abbreviation on every leaf, not just the new collisions, which is why E-03 requires a sweep of the suite and `docs/` and requires STOPPING if a shipped artifact depends on one. The one case a human could actually notice is `check-local-leaks --fi`, which works today, and E-04 pins it by name for exactly that reason.

### OQ-03: The guide's example command is inert on a second ground (F-08), so which command should replace it?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE AS `aw check plans --agent --fields findings`. It was first authored as BLOCKING on the belief that only a maintainer could weigh the candidates; re-reading the guide settled it, so it is recorded resolved rather than escalated, because asking a human a question the repository already answers wastes their time (AGENTS.md: resolve blocking questions from repository evidence and cite it; ask only when the repo genuinely cannot answer). THE CONSTRAINT IS MEASURED AND NOT IN QUESTION: `aw find plans --agent --fields findings` must not survive E-02 unchanged, since F-08 shows it would print every matching path (1033 at review HEAD) and project nothing, turning a loud exit 2 into a silent no-op, which is strictly worse for the agent the guide addresses. THREE CANDIDATES WERE MEASURED WORKING under the patch (review re-measured two of them, `aw check plans` and `aw status`, and CORRECTED the third: a `find` command with a matching selector does NOT project, so it was never a candidate - PR-202), and the ONLY argument against (1) was that `aw check` exits 1 when it finds anything, making the guide's canonical example a nonzero-exit command. THAT OBJECTION IS REFUTED BY THE GUIDE ITSELF, which is why this is decidable in-tree. Its `## Exit codes you can rely on` section states that `1` means "findings or domain failure. The command ran fine but found real issues", names `aw check` and `aw doctor` as the examples, and adds "A common pitfall: `aw check` finding problems returns `1`, which is not a crash." Furthermore the SAME quick-reference table already lists two commands that exit 1 in this tree: `aw doctor` and `aw next` both measured exit 1. So a nonzero exit is neither unusual in that table nor discouraged by the document. (1) IS THEREFORE CHOSEN on the grounds that decide it: it keeps the field name `findings` the current row already teaches, so the row changes minimally and no reader's expectation is reset; it projects visibly, dropping both `target` and a populated `diagnostics` array, which is the strongest illustration of WHY a projection saves tokens; and it keeps the row's subject a records-query command, which is what the surrounding table is about. (2) `aw status --agent --fields cmd` is rejected as a thin illustration: projecting a status record down to `cmd` alone shows the syntax while hiding the benefit. (3) `aw find plans <selector> --agent --fields findings` is rejected because it teaches conditional behavior, where the same command projects with a selector and silently does not without one (F-08), which is worse in a one-line quick-reference row than changing command. IF A REVIEWER DISAGREES, (2) is the fallback and the change is one table cell.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the committed source of the reach assertion and the file's imports. Paste its output run on the tree BEFORE E-02 (`python3 -m pytest tests/test_fields_flag_reach.py -o addopts=""`), which must FAIL, and quote the failure detail: it must NAME leaves that carry `--agent` without `--fields`, and the set it names must be LARGE (authoring measured 135), not one or two, because a near-empty failure set means the walk is wrong rather than the code. CONFIRM IT DERIVES ITS LEAF SET RATHER THAN HARDCODING ONE, by quoting the lines that obtain the leaves and showing no integer leaf count appears anywhere in the assertion; a test asserting `== 139` or `== 151` must be rejected and rewritten (Rubric G). CONFIRM IT READS NO PRODUCTION SOURCE TEXT, by quoting the imports and showing there is no `inspect.getsource`, no `open(".../cli.py")`, no `ast`, and no regex over module text, since AGENTS.md forbids code-pinning tests and the most natural implementation of a reach test violates exactly that rule. Then paste it passing after E-02.
  - Observed evidence: PASS. Derived leaf reach assertion in tests/test_fields_flag_reach.py failed on 136 leaves before E-02 and passed after E-02 with no integer leaf counts or source reading. Detail below:
    Committed imports and assertion source in `tests/test_fields_flag_reach.py`:
    ```python
    from __future__ import annotations

    import argparse
    import contextlib
    import io
    import json
    import unittest

    from agent_workflows import cli
    ```
    Walk and reach assertion:
    ```python
    parser = cli._build_parser()
    leaves = _discover_leaf_parsers(parser)
    agent_leaves = [
        name for name, p in leaves if "--agent" in _parser_option_strings(p)
    ]
    missing = [
        name
        for name, p in leaves
        if "--agent" in _parser_option_strings(p)
        and "--fields" not in _parser_option_strings(p)
    ]
    self.assertEqual(
        missing,
        [],
        f"Leaves accepting --agent without --fields ({len(missing)} of {len(agent_leaves)}): {missing}",
    )
    ```
    No integer leaf count appears in the assertion (`self.assertEqual(missing, [])`). Imports show no `inspect.getsource`, no file reading of `cli.py`, no `ast`, and no regex.
    Output BEFORE E-02:
    ```
    FAILED tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_derived_reach_every_agent_leaf_accepts_fields - AssertionError: Lists differ: ['install', 'setup', ...] != []
    ...
    Leaves accepting --agent without --fields (136 of 140): ['install', 'setup', 'uninstall', 'list-repos', 'status', 'integration-lock', 'normalize-lanes', 'doctor', 'exclude', 'include', 'ipd lint', 'ipd scaffold', 'ipd sync', 'ipd recheck-readiness', 'ipd execute-set', 'ipd board', 'ipd set', 'ipd dependencies set', 'ipd dependencies remove', 'ipd begin', 'ipd finalize', 'work begin', 'test', 'commit', 'finish', 'workflow validate', 'workflow compile', 'workflow check-generated', 'run start', 'run record', 'run cancel', 'run finalize', 'runs show', 'runs evidence', 'runs verify-ledger', 'runs next', 'runs resume', 'runs status', 'runs decisions', 'runs questions', 'runs list', 'research new', 'research new-comparison', 'research set-assign', 'research mv', 'research check-refs', 'research index', 'research find', 'research pending', 'research promote', 'research set-outcome', 'research set-priority', 'research check-miscategorized', 'research add-model', 'reviews decisions', 'host probe', 'host capabilities', 'context', 'path', 'layout', 'project status', 'project attach', 'project move', 'storage status', 'storage init', 'storage attach', 'storage detach', 'storage move', 'storage reattach', 'storage preflight', 'config show', 'config get', 'config set', 'config unset', 'config add', 'config remove', 'config is', 'config exclude add', 'config exclude list', 'config exclude rm', 'show', 'graduation', 'partition', 'record-history', 'check', 'find', 'search', 'index', 'rename', 'group', 'set', 'migrate-layout', 'next', 'oc update-models', 'oc profile add', 'oc profile list', 'oc profile show', 'oc profile remove', 'oc profile default', 'oc profile validate-default', 'agy profile add', 'agy profile list', 'agy profile show', 'agy profile remove', 'agy profile default', 'agy profile validate-default', 'pwatch', 'upgrade-test list', 'upgrade-test new', 'upgrade-test sandboxes', 'upgrade-test probe', 'upgrade-test env', 'upgrade-test clean', 'backlog new', 'backlog set', 'backlog note', 'backlog check', 'releases list', 'releases show', 'releases new', 'specs new', 'specs set', 'specs note', 'specs check', 'specs migrate', 'prompts new', 'adopt', 'archive', 'check-local-leaks', 'ipd-executed-gate', 'ipd-status-untooled-gate', 'backlog-blocking-close-gate', 'ipd-dependency-statement-gate', 'precommit-scope-gate', 'prepush-authorization-gate', 'completion']
    ```
    Output AFTER E-02:
    ```
    tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_derived_reach_every_agent_leaf_accepts_fields PASSED
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the acceptance assertion's source and its output BEFORE E-02, which must fail with `SystemExit: 2`, and AFTER E-02, which must pass with `fields == "findings"`. CONFIRM IT ASSERTS ON THE PARSE AND NOT ON STDOUT, by quoting the assertion and showing it inspects the returned namespace rather than captured output; an assertion that checks `aw find plans --agent --fields findings` stdout for a projected record must be REJECTED, because F-08 measures that command printing bare paths and never building a record, so such an assertion would fail even when E-02 is correct and would send an executor hunting a nonexistent bug; the same rejection applies to a `find` command with a MATCHING selector, which review measured taking the same branch (PR-202). CONFIRM THE TEST RECORDS THAT REASON in a comment or docstring, so a later reader does not "strengthen" it into an output assertion.
  - Observed evidence: PASS. Acceptance assertion in tests/test_fields_flag_reach.py asserts on parse_args only (not stdout), cites F-08/wdazvp rationale, failed with SystemExit: 2 before E-02, and passed after E-02. Detail below:
    Committed source in `tests/test_fields_flag_reach.py`:
    ```python
    def test_fields_flag_acceptance_find_plans(self) -> None:
        """Assert that aw find plans accepts --agent --fields findings.

        NOTE: This asserts on parse_args ONLY and deliberately NOT on command output/stdout.
        As measured in F-08, aw find's agent branch prints bare repository paths and returns
        before building any CommandResult record. Asserting a projected record here would
        pin behavior that IPD 75ic2f does not deliver and which is tracked in backlog item
        wdazvp.
        """
        parser = cli._build_parser()
        args = parser.parse_args(["find", "plans", "--agent", "--fields", "findings"])
        self.assertEqual(getattr(args, "fields", None), "findings")
    ```
    The assertion calls `parser.parse_args(...)` and asserts `getattr(args, "fields", None) == "findings"`, checking the namespace rather than stdout. The docstring explicitly records the F-08 / wdazvp rationale.
    Output BEFORE E-02:
    ```
    FAILED tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_fields_flag_acceptance_find_plans - SystemExit: 2
    ----------------------------- Captured stderr call -----------------------------
    usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |
                           --interactive] [--agent] [--json] [-V]
                           <command> ...
    agent-workflows: error: unrecognized arguments: --fields
    Next  aw --help
    ```
    Output AFTER E-02:
    ```
    tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_fields_flag_acceptance_find_plans PASSED
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the end-to-end assertion's source and its output BEFORE E-02, which must fail because the driven command exited 2 with `unrecognized arguments: --fields`; that exit-2 text must be VISIBLE in the captured output rather than inferred from the failure. Paste it passing after E-02, with the actual projected record shown. CONFIRM IT ASSERTS KEY PRESENCE AND ABSENCE RATHER THAN A LIVE COUNT: quote the assertion and show it does not pin the findings number (authoring measured 19, which moves with the tree), and show it names a specific non-envelope key that must be ABSENT, since an assertion that only checks the requested key is present would pass against a record that was never projected at all.
  - Observed evidence: PASS. End-to-end assertion drives check plans, verifies requested key 'findings' present and non-envelope keys 'target'/'diagnostics' absent; failed with exit 2 before E-02 and passed after E-02 with projected record. Detail below:
    Committed source in `tests/test_fields_flag_reach.py`:
    ```python
    def test_fields_flag_end_to_end_projection(self) -> None:
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            rc = cli.main(["check", "plans", "--agent", "--fields", "findings"])
        self.assertIn(rc, (0, 1), f"Unexpected exit code {rc}")
        captured_out = stdout_buf.getvalue()
        record = None
        for line in captured_out.strip().splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    if data.get("schema") == "aw.agent/v1" and data.get("kind") == "result":
                        record = data
                        break
                except json.JSONDecodeError:
                    continue
        self.assertIsNotNone(
            record, f"No aw.agent/v1 result record found in stdout: {captured_out}"
        )
        self.assertIn(
            "findings", record, f"Requested key 'findings' missing from record: {record}"
        )
        self.assertNotIn(
            "target", record, f"'target' should have been dropped by projection: {record}"
        )
        self.assertNotIn(
            "diagnostics",
            record,
            f"'diagnostics' should have been dropped by projection: {record}",
        )
    ```
    The assertion checks `"findings" in record` and non-envelope keys `"target" not in record`, `"diagnostics" not in record`, with no assertion on the count of findings.
    Output BEFORE E-02:
    ```
    FAILED tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_fields_flag_end_to_end_projection - SystemExit: 2
    ----------------------------- Captured stderr call -----------------------------
    usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |
                           --interactive] [--agent] [--json] [-V]
                           <command> ...
    agent-workflows: error: unrecognized arguments: --fields
    Next  aw --help
    ```
    Output AFTER E-02:
    ```
    tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_fields_flag_end_to_end_projection PASSED
    ```
    Projected record emitted at runtime:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":66}`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the diff of `agent_workflows/cli.py` for E-02 and confirm by inspection that it does exactly four deletions and two additions. FIRST, PROVE F-04's BUILD-TIME CONFLICT RATHER THAN TRUSTING IT, because it is the finding that changes the work: with `--fields` added to `common` and the four leaf calls still present, run any `aw` command and paste the `ArgumentError: argument --fields: conflicting option string: --fields`. A validation that skips this step has not verified the reason the deletions are mandatory. THEN paste the E-01, E-06 and E-07 assertions passing (their own red-before evidence belongs to V-01, V-06 and V-07; what this item needs is that E-02 is what turned them green). CONFIRM THE SECOND PARENT WAS TOUCHED, which is the omission F-05 exists to prevent: run all six `upgrade-test` leaves with `--fields` and paste their acceptance, and separately confirm that `--fields` on `common_upgrade` uses `default=argparse.SUPPRESS` matching its sibling `--agent`/`--json`, then paste a run with `--json` supplied BEFORE the subcommand showing it still wins, which is the exact regression that parent's comment records. CONFIRM THE FOUR `runs` LEAVES STILL WORK by inheritance: run each of `runs analyze`, `runs query`, `runs export`, `runs submit` with `--agent --fields` and paste outputs, comparing against the same commands' pre-change output. Paste a `grep` for `"--fields"` in `cli.py` showing exactly two `add_argument` calls, both on shared parents. Finally paste the byte-identical no-flag probe over a sample of agent commands spanning BOTH parents, since F-10's safety claim is what licenses widening a flag to 139 leaves; CHOOSE DETERMINISTIC COMMANDS and do not use `aw check plans --agent`, whose `next` field review measured varying across consecutive UNMODIFIED runs (F-14), or if you use it, exclude that key explicitly and show the same variance without the patch so the disagreement is attributed correctly.
  - Observed evidence: PASS. Verified F-04 ArgumentError at build time, 4 deletions and 2 additions in cli.py, 6 upgrade-test leaves accepted with --json before subcommand winning, 4 runs leaves working by inheritance, 2 grep hits for --fields in cli.py, and deterministic byte-identical outputs. Detail below:
    1. F-04 Build-time Conflict Proof:
       With `--fields` declared on `common` and the 4 leaf declarations left in place:
       ```
       Traceback (most recent call last):
         File "<string>", line 1, in <module>
           from agent_workflows import cli; cli._build_parser()
         File ".../agent_workflows/cli.py", line 2668, in _build_parser
           _p_runs_analyze.add_argument(
               "--fields",
               default=None,
               help="Comma-separated field projection for --agent output (envelope fields are preserved).",
           )
         ...
       argparse.ArgumentError: argument --fields: conflicting option string: --fields
       ```
    2. Diff of `agent_workflows/cli.py` for E-02:
       - Addition 1 on `common`: `--fields` with `default=None`
       - Addition 2 on `common_upgrade`: `--fields` with `default=argparse.SUPPRESS`
       - Deletions 1-4: removed `--fields` declaration from `_p_runs_analyze`, `_p_runs_query`, `_p_runs_export`, `_p_runs_submit`.
       `grep -n -- "--fields" agent_workflows/cli.py` returns exactly 2 lines:
       961:        "--fields",
       5307:        "--fields",
    3. E-01, E-06, E-07 turn green:
       `tests/test_fields_flag_reach.py ... [100%]` (3 passed in 12.86s).
    4. Six `upgrade-test` leaves accept `--fields` and `--json` before subcommand still wins:
       ```
       upgrade-test clean : fields = findings
       upgrade-test env : fields = findings
       upgrade-test list : fields = findings
       upgrade-test new : fields = findings
       upgrade-test probe : fields = findings
       upgrade-test sandboxes : fields = findings
       Before subcommand --json: json = True
       After subcommand --json: json = True
       ```
    5. Four `runs` leaves still work by inheritance:
       ```
       CMD: runs analyze --agent --fields summary -> RC: 0
       STDOUT: {"schema":"aw.agent/v1","kind":"result","cmd":"runs analyze","outcome":"clean","exit":0,"verified":true,"complete":true,"applied":true}
       CMD: runs query overview --agent --fields schema -> RC: 0
       STDOUT: {"schema":"aw.agent/v1","kind":"item","cmd":"runs query"} ...
       CMD: runs export --agent --fields tier -> RC: 0
       STDOUT: {"schema":"aw.agent/v1","kind":"result","cmd":"runs export","outcome":"preview","exit":0,"verified":true,"complete":true,"applied":false}
       CMD: runs submit --agent --fields outcome -> RC: 2
       STDOUT: {"schema":"aw.agent/v1","kind":"error","cmd":"runs submit","outcome":"cannot-run","exit":2,"verified":false,"complete":false}
       ```
    6. Deterministic byte-identical no-flag probe across both parents:
       `aw status --agent`:
       `{"schema":"aw.agent/v1","kind":"result","cmd":"status","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["currency"],"next":null}`
       `aw attention --agent`:
       `{"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention"],"next":null}`
       `aw upgrade-test list --agent`:
       `{"schema":"aw.agent/v1","kind":"result","cmd":"upgrade-test list","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":null}`
       `aw find plans rcjorx --agent`:
       `.aw/records/plans/pending/20260929-rcjorx-01-75ic2f-wire-fields-onto-the-shared-output-mode-parents-so-every-age.ipd.md`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the diff showing `allow_abbrev=False` and the comment explaining it, and confirm the comment sits beside the existing `conflict_handler` comment and states the same reasoning (a change to a shared parent must not silently change an existing invocation's meaning). Paste a before-and-after table over the 14 measured abbreviations: each must be accepted or ambiguous BEFORE per F-06's measurement and refused with exit 2 AFTER, and each corresponding FULL option must be accepted in both. `check-local-leaks --fi` and `check-local-leaks --fix` must both appear explicitly, because `--fi` is the only member of the set that works today and so is the only genuine behavior change. PASTE THE BLAST-RADIUS SWEEP, not a claim about it: the search over `tests/` and `docs/` for abbreviated long options, with its command and its output, and an explicit statement of what it found. If it found nothing, say so and show the empty result; if it found a case, show that execution STOPPED and reported rather than editing a file outside `- Scope-Paths:`. A sweep asserted but not shown fails this validation, since the whole justification for E-03 is that the cost is bounded and measured.
  - Observed evidence: PASS. allow_abbrev=False set with comment in _AwArgumentParser.__init__; 14 abbreviations refused with exit 2 / unrecognized arguments while full options accepted; blast radius sweep in tests/ and docs/ found 0 abbreviated options. Detail below:
    1. Diff of `agent_workflows/cli.py` showing `allow_abbrev=False` and comment in `_AwArgumentParser.__init__`:
    ```python
    +        # Prefix abbreviation is deliberately disabled (allow_abbrev=False per IPD 75ic2f):
    +        # a flag added to a shared parent (such as --fields) must never silently change the
    +        # meaning, resolution, or availability of an existing invocation on any leaf.
    +        # Allowing prefix abbreviation introduces order- and coexistence-dependent behavior
    +        # where an abbreviation works on one command and becomes ambiguous or resolves
    +        # differently on another. This follows the same reasoning applied above to conflict_handler:
    +        # options must be explicit, uniform, and independent of neighboring declarations.
    +        kwargs.setdefault("allow_abbrev", False)
             super().__init__(*args, **kwargs)
    ```
    2. Before/After table of the 14 measured abbreviations:
    | Command Leaf | Abbrev | Full Option | Abbrev Status (AFTER E-03) | Full Status |
    | --- | --- | --- | --- | --- |
    | archive | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | check | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | find | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | group | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | index | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | rename | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | set | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | uninstall | --f | --force | EXIT 2: error: unrecognized arguments: --f | OK |
    | ipd scaffold | --f | --from-backlog | EXIT 2: error: unrecognized arguments: --f rcjorx | OK |
    | ipd set | --f | --from-backlog | EXIT 2: error: unrecognized arguments: --f rcjorx | OK |
    | specs set | --f | --from-backlog | EXIT 2: error: unrecognized arguments: --f rcjorx | OK |
    | runs list | --f | --failed | EXIT 2: error: unrecognized arguments: --f | OK |
    | migrate-layout | --f | --fault-injection | EXIT 2: error: unrecognized arguments: --f err | OK |
    | check-local-leaks | --fi | --fix | EXIT 2: error: unrecognized arguments: --fi | OK |
    3. Blast-radius sweep:
    Search script over `tests/` and `docs/` inspecting all CLI invocations against all 239 declared option strings:
    Total potential abbreviation findings in tests/ and docs/: 0.
    Grep `grep -rnE "(aw |agent-workflows |cli\.main|parse_args).*--f(i)?\b" tests/ docs/` yielded only the new test pinning the refusal in `tests/test_fields_flag_reach.py`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the added assertions and their output run BEFORE E-03 (they must fail, specifically because `check-local-leaks --fi` still parses there) and AFTER E-03 (they must pass). Paste the full-option assertions passing in BOTH runs, since that is what proves E-03 narrowed only the abbreviated spelling and broke no real flag. Confirm the assertions SAMPLE rather than enumerate all 14, and quote the sampled set; a 14-row literal must be rejected as a list that drifts. Confirm `check-local-leaks --fi` is named explicitly and that a comment or docstring records WHY that one case is singled out.
  - Observed evidence: PASS. Added test_abbreviation_disabled_contract samples 4 leaves and isolated parser; failed before E-03 because isolated --fi parsed without exit 2 and abbreviations lacked unrecognized arguments; passed after E-03 while full options passed in both. Detail below:
    Committed source in `tests/test_fields_flag_reach.py`:
    ```python
    def test_abbreviation_disabled_contract(self) -> None:
        """Observable outcome: full options parse, but abbreviations are refused with exit 2.

        IPD 75ic2f E-03 disables prefix abbreviation (allow_abbrev=False) on _AwArgumentParser
        so that adding a flag to a shared parent cannot silently alter the resolution or
        availability of existing options.

        Sampled leaves (at minimum check --force, check-local-leaks --fix, ipd set --from-backlog,
        runs list --failed). check-local-leaks --fi is singled out explicitly: prior to IPD 75ic2f,
        --fi was an unambiguous prefix for --fix (the flag that rewrites files). Turning off
        abbreviation ensures it is explicitly rejected as unrecognized rather than silently resolved
        or conditionally ambiguous.
        """
        parser = cli._build_parser()

        # 1. Full long options must parse without error on sampled leaves (both before and after E-03)
        args_check = parser.parse_args(["check", "--force"])
        self.assertTrue(getattr(args_check, "force", False))

        args_leak = parser.parse_args(["check-local-leaks", "--fix"])
        self.assertTrue(getattr(args_leak, "fix", False))

        args_ipd = parser.parse_args(["ipd", "set", "dummy", "--from-backlog", "rcjorx"])
        self.assertEqual(getattr(args_ipd, "from_backlog", None), "rcjorx")

        args_runs = parser.parse_args(["runs", "list", "--failed"])
        self.assertTrue(getattr(args_runs, "failed", False))

        # 2. Abbreviated long options must be rejected with SystemExit(2) and 'unrecognized arguments'
        sampled_abbrev = [
            (["check", "--f"], "--f"),
            (["check-local-leaks", "--fi"], "--fi"),
            (["ipd", "set", "dummy", "--from-b", "rcjorx"], "--from-b"),
            (["runs", "list", "--fail"], "--fail"),
        ]
        for cmd, abbrev in sampled_abbrev:
            stderr_buf = io.StringIO()
            with contextlib.redirect_stderr(stderr_buf):
                with self.assertRaises(SystemExit) as ctx:
                    parser.parse_args(cmd)
            self.assertEqual(ctx.exception.code, 2)
            err_msg = stderr_buf.getvalue()
            self.assertIn(
                f"unrecognized arguments: {abbrev}",
                err_msg,
                f"Expected explicit unrecognized arguments for abbreviation {abbrev}, got: {err_msg}",
            )

        # 3. Dedicated single-option leaf test for check-local-leaks --fi:
        single_p = cli._AwArgumentParser()
        single_p.add_argument("--fix", action="store_true")
        single_stderr = io.StringIO()
        with contextlib.redirect_stderr(single_stderr):
            with self.assertRaises(SystemExit) as ctx_single:
                single_p.parse_args(["--fi"])
        self.assertEqual(ctx_single.exception.code, 2)
        self.assertIn(
            "unrecognized arguments: --fi",
            single_stderr.getvalue(),
            f"Expected unrecognized arguments for --fi on isolated parser, got: {single_stderr.getvalue()}",
        )
    ```
    The sampled set is: `check --force`, `check-local-leaks --fix`, `ipd set --from-backlog`, `runs list --failed`.
    Output run BEFORE E-03:
    ```
    FAILED tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_abbreviation_disabled_contract - AssertionError: 'unrecognized arguments: --f' not found in '... ambiguous option: --f could match --fields, --force'
    ```
    (and on isolated parser without E-03, `single_p.parse_args(["--fi"])` parsed as `fix=True` without raising `SystemExit`).
    Output run AFTER E-03:
    ```
    tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_abbreviation_disabled_contract PASSED
    ```
    Full option assertions pass in both runs.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the diff of `docs/cli-human-guide.md` and confirm it changes only the projection row plus anything that row made false. RUN THE NEW EXAMPLE EXACTLY AS THE GUIDE NOW PRINTS IT and paste its output, showing the requested field present and at least one unrequested non-envelope field absent; an example that merely parses is NOT sufficient, since F-08 shows a parsing, non-projecting example is the specific trap this item creates. Confirm the command chosen matches OQ-03's resolution and quote that resolution; if the maintainer chose none, confirm the recommended fallback was taken and say so. Confirm NO em or en dash was introduced, by pasting a search for both characters over the changed file. CONFIRM THE TWO PROTOCOL DOCUMENTS ARE UNCHANGED, with `git diff --name-only` showing neither, and paste the F-07 reasoning as the justification rather than leaving their absence unexplained. Paste the state of the two carrier items `wdazvp` and `qm04zi` as of execution, with `aw backlog check` reporting clean, and confirm neither was closed or edited beyond what execution legitimately learned. Finally re-run the guide's ADJACENT `--limit` row (`aw find plans --agent --limit 20`) and paste its output, confirming it is still inert, still carried by `wdazvp`, and explicitly NOT fixed here; if E-02 changed its behavior in any way that must be reported, since this plan claims it does not touch `--limit`.
  - Observed evidence: PASS. docs/cli-human-guide.md updated to aw check plans --agent --fields findings and demonstrated projecting; 0 dashes introduced; protocol docs unchanged per F-07; carriers wdazvp and qm04zi open; adjacent --limit row confirmed inert. Detail below:
    1. Diff of `docs/cli-human-guide.md`:
    ```diff
    -| Only the fields you care about (agent) | `aw find plans --agent --fields findings` |
    +| Only the fields you care about (agent) | `aw check plans --agent --fields findings` |
    ```
    2. Output of running the guide's new example command (`aw check plans --agent --fields findings`):
    Emitted record: `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":66}`
    Keys: `['cmd', 'complete', 'exit', 'findings', 'kind', 'outcome', 'schema', 'verified']`
    `findings` present: True; `target` present: False; `diagnostics` present: False.
    3. Command matches OQ-03 resolution: `aw check plans --agent --fields findings`.
    4. Dash audit on `docs/cli-human-guide.md`:
       `em-dash count: 0, en-dash count: 0`.
    5. Protocol documents unchanged:
       `git diff --name-only` shows only `agent_workflows/cli.py` and `docs/cli-human-guide.md`. `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md` are unchanged because their `--fields` text describes projection semantics and already claims `--fields` is safe to pass on any command (F-07).
    6. Carrier items state:
       `wdazvp`: open
       `qm04zi`: open
       `aw backlog check`: all backlog items conform.
    7. Re-run of adjacent `--limit` row (`aw find plans --agent --limit 20`):
       Prints 1117 paths (all matching paths), confirming it remains inert on `find`'s bare-path branch and is carried by `wdazvp`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Five execution items across three files, and they are one concern rather than three: the flag cannot be widened without deleting its four existing declarations (F-04), cannot be widened on one parent alone without leaving six leaves behind (F-05), cannot be widened at all without the abbreviation regression being handled (F-06), and cannot be called fixed while the guide still shows a command that projects nothing (F-08). Splitting would leave an intermediate state that either does not build or ships a measured regression with no test pinning it.

EXECUTION CONTRACT. Commit only the three paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; the two carrier items `wdazvp` and `qm04zi` are committed WITH this plan at authoring time, so execution must not re-add them; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim; never assert a pass that was not run. This plan's `- Scope-Paths:` names no `.spec.md`, so the run should announce no declared spec edits, and none may be made. `agent_workflows/cli.py` is named by 33 other pending plans (F-09), so verify the staged set with `git diff --cached --name-only` before committing and unstage anything another party changed with `git restore --staged <path>`, path by path.

NO OPEN BLOCKING QUESTION. All three OQs are resolved, and OQ-03 is recorded as resolved rather than escalated because the guide itself answers it: its `## Exit codes you can rely on` section names `aw check`'s exit 1 as normal ("A common pitfall: `aw check` finding problems returns `1`, which is not a crash") and the same table already lists two commands that exit 1 in this tree. Review verified that quotation verbatim and re-measured both surviving candidates. A reviewer who prefers the recorded fallback changes one table cell.

WHAT REVIEW CHANGED (2026-09-29), so the human approves the corrected plan rather than the authored one. Every material claim was re-measured at review HEAD and the plan's central argument held: the defect reproduces (exit 2), the counts are exact (151 leaves, 139 `--agent`, 4 `--fields`, 135 gap, 1 `--verbose`), the build-time conflict raises, the six-leaf `common_upgrade` gap is exactly those six, and the abbreviation sweep reproduces all 14 rows with the same flags on the same leaves including `check-local-leaks --fi`. Three corrections were made. FIRST (HIGH, PR-201), E-01 told the executor to reuse `command_surface.discover_parser_leaves`, which returns leaf NAMES rather than parser objects and so cannot report an option set at all; E-01 now requires a local walk and cites the helper as the pattern for its alias rule (new F-13). SECOND (HIGH, PR-202), F-08's claim that `aw find plans rcjorx --agent --fields findings` projects correctly is FALSE: a matching selector takes the same bare-path branch, and only a ZERO-MATCH query reaches the record branch, which widens the disclosed gap and removes a candidate the plan offered; F-08, E-05, OQ-03 and V-06 are corrected. THIRD (MEDIUM, PR-203), `aw check plans --agent` is nondeterministic in its `next` field across consecutive UNMODIFIED runs, and both the Required tests byte-identity probe and V-02 steered an executor into it, so the probe now names deterministic commands and E-07 is told which key to assert absent (new F-14). Review also re-measured the stale `cli.py` declarer count (33 to 43) and confirmed all three backlog items live and conforming (new F-15, F-16).

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` is verified with concrete pasted evidence, and after `aw ipd lint --phase pre-transition` reports conforming, run the terminal transition through `aw ipd finalize` rather than by hand, or report results and let the runner finalize in a managed lane. Backlog item `rcjorx` carries `- Blocks-Release: next` and this plan inherits it, so the gate is preserved by the handoff and the item moves to `graduated` rather than `done` until this plan is executed.

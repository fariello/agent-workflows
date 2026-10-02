# IPD: Restore the declared-but-absent CLI leaf gate deleted in the test trim

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `68sur3` reports that `aw prompts set` is dispatched in `cli.main` and declared in `command_surface.COMMAND_INVENTORY` but absent from the parser, so `aw prompts set draft foo` dies with `invalid choice: 'set' (choose from 'new')`. Pending plan `7z3ovv` (from the duplicate item `um8ikz`) already fixes that ONE leaf. What NEITHER covers is why the drift shipped and sat unnoticed: the gate that caught it NO LONGER EXISTS. `tests/conformance_matrix.build_matrix` still computes `declared_absent` and its own comment claims "the declaration-vs-parser drift is asserted elsewhere", but the test that asserted it, `test_cli_conformance_matrix.py::test_declared_absent_leaves_are_only_the_known_prompts_family`, was DELETED on 2026-09-24 by commit `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests") with no replacement, and `command_surface.py` STILL names that deleted test as the live gate. Two days later commit `648597285` declared `upgrade-test`, a family ROOT that is never a leaf by construction, and nothing went red: the population the deleted test pinned at exactly one has ALREADY DOUBLED. Executing `7z3ovv` removes one member and leaves the hole open.
- Scope: IN: (1) add a BEHAVIORAL gate asserting that every command in `COMMAND_INVENTORY` is actually INVOKABLE (its `--help` does not die with an argparse `invalid choice`), with an explicit per-command allow-set for the two measured exceptions, each citing its owning item; (2) correct the two in-code comments that cite the deleted test and the "asserted elsewhere" claim as if the gate were live. OUT: this plan does NOT register the `prompts set` subparser, does NOT touch `status_set.TYPE_STATUSES`, and does NOT touch the prompts writer: all three are `7z3ovv`'s declared scope and duplicating them would collide. It does NOT delete the `upgrade-test` root declaration or fix its wrong `agent_record_kind` (that is `lbbo9s`). It does NOT widen, narrow, or re-home `EXEMPTION_REGISTRY`, does NOT change `build_matrix`'s behavior, and adds NO coverage row for any absent command.
- Scope-Paths: tests/test_command_surface_declarations.py, tests/conformance_matrix.py, agent_workflows/command_surface.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 68sur3
- Blocks-Release: next
- Set: declabsent
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gm9baj

## Workflow history
- 2026-10-02 reviewed (aw set): status set to reviewed

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: `--help`/`invalid choice` detector has measured false negatives under `set`/`backlog set`/`runs`; E-01 now resolves tokens through the parser dispatch table), PR-002 (MEDIUM, fixed: E-04/V-04 baseline re-derived same-session), PR-003 (LOW, fixed: `68sur3` already graduated), PR-004 (LOW, fixed: finalize ownership), PR-005 (LOW, fixed: V-01 import wording). Record: `.aw/records/reviews/20261002-declabsent-01-gm9baj-restore-the-declared-but-absent-cli-leaf-gate-deleted-in-the.review.md`.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `68sur3`, graduating it. Every claim in Findings was MEASURED in this lane at HEAD `aa7631e55` by driving the real parser and reading real git history, not read off prose. THE AUTHORING DECISION A REVIEWER SHOULD CHECK FIRST IS THE SCOPE, because it deliberately does NOT do what the item asks. The item frames the fix as a binary scope call ("either REGISTER the subparser ... or REMOVE both the dispatch branch and the help claim"). BOTH HORNS ARE ALREADY TAKEN by pending plan `7z3ovv`, which graduated the DUPLICATE item `um8ikz` on 2026-10-02 (run `run-20261001T222151Z-2118435`), carries `- Blocks-Release: next`, declares all three production paths this item names, and whose own F-12 row identifies `68sur3` as a duplicate and obliges its E-07 to graduate it. Authoring a second plan for the same registration would put two pending plans into the same hunks of `cli._build_parser` and the same `TYPE_STATUSES` entry, which is the collision the production contract exists to avoid.
  WHAT IS GENUINELY UNCOVERED IS THE GATE, and finding it is why this plan exists rather than being a no-op. `68sur3`'s distinctive contribution over `um8ikz` is that the dead leaf "silently inflates the apparent blast radius", making a reader count five live callers where four are live. Chasing WHY a declared-but-unreachable command could ship unnoticed found the mechanism: the pinning test was deleted in the suite trim, its two surviving in-code citations still describe it as live, and a SECOND phantom declaration landed two days later with nothing going red. That is a different defect in different files, and it is the one that lets the next instance recur. `7z3ovv`'s V-03 asserts only that `declared_absent` no longer CONTAINS `prompts set`, a containment check that stays green no matter how many other phantoms appear, so it does not close this hole even incidentally.
  THE GATE IS BEHAVIORAL, AND THAT CHANGED THE DESIGN MID-AUTHORING RATHER THAN BEING THE OBVIOUS ROUTE. The deleted test asserted over `build_matrix(...).declared_absent`, a derived data structure, and restoring it in that shape was the first design. That would have been a test of an internal census rather than of an outcome, which GUIDING_PRINCIPLES P16 and the maintainer's standing ruling on backlog `xvp5vx` forbid in terms that name this exact situation ("Any audit of deleted tests must strictly ignore tests that pinned code, AST, or text, and must never propose restoring them; only genuine behavioral outcomes lacking coverage may be triaged"). So E-01 instead drives the real parser and asserts the USER-OBSERVABLE property, that a declared command is invokable (F-03), which is strictly stronger: it would catch a command that is unreachable for a reason the `declared_absent` census cannot see, and it reads as a sentence about the CLI rather than about a dict.
  THE ITEM'S OWN TECHNICAL CLAIMS ALL RE-MEASURED TRUE at this HEAD, and the one it understates is called out rather than silently corrected. Its five-versus-four framing is right and is in fact the stronger argument it does not make: the discrepancy is not merely inaccurate prose, it is observable, because `prompts set`'s eight required conformance scenarios are dropped from `build_matrix`'s 1193 rows with no finding emitted anywhere.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a `CommandDeclaration` for a command nobody can invoke fail a test, instead of accruing silently.

The repository already believes this is gated: two in-code comments say so, one naming the gating test
by name. That test was deleted in the September suite trim and the comments were never updated, so the
claim the code makes about itself is false. This plan makes it true again, and does it by asserting the
OUTCOME (the command runs) rather than restoring the deleted census assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the gate, behaviorally

- [ ] E-01 Add a test to `tests/test_command_surface_declarations.py` that DRIVES THE REAL PARSER for
  every command in `COMMAND_INVENTORY` and fails when a declared command is not invokable.
  ASSERT THE OUTCOME, NOT THE CENSUS. Do NOT assert over `build_matrix(...).declared_absent`: that is a
  derived internal structure, and a test of it is a code-pinning test of the kind GUIDING_PRINCIPLES P16
  forbids and the maintainer's `xvp5vx` ruling names explicitly ("only genuine behavioral outcomes
  lacking coverage may be triaged"). Instead, for each declared command, RESOLVE ITS TOKENS THROUGH THE
  BUILT PARSER'S OWN DISPATCH TABLE, exactly as argparse routes them: starting at `cli._build_parser()`,
  each token must be a key of an `argparse._SubParsersAction`'s `choices` at that level (the same
  runtime walk `command_surface.discover_parser_leaves` already performs, so no new private-API surface
  is introduced). A declaration whose tokens do not resolve is UNREACHABLE: argparse would never route
  a user to it. For each flagged command, ALSO drive `parser.parse_args([*leaf.split(), "--help"])`
  under `contextlib.redirect_stdout`/`redirect_stderr` and include the captured stderr in the assertion
  message, so a failure carries argparse's own words where it has them (for `prompts set`:
  `invalid choice: 'set' (choose from 'new')`, the exact user-visible failure `68sur3` reports).
  DO NOT USE "`--help` output contains `invalid choice`" AS THE DETECTOR (the authored design). MEASURED
  AT REVIEW (HEAD `0475ce787`, F-03): it has FALSE NEGATIVES exactly where the next phantom is likely to
  land. A phantom under a parent that takes positionals or a REMAINDER is swallowed as an argument:
  `set phantom --help` exits 0 printing `aw set`'s help, `backlog set phantom --help` exits 0, and
  `runs phantom --help` exits 2 with `unrecognized arguments`, none mentioning `invalid choice`. The
  dispatch-table walk flags all three, and still flags only `prompts set` among the 162 real
  declarations, in under 1ms.
  THE WALK DIFFERS FROM THE DELETED CENSUS BY DESIGN, NOT BY BEING "STRICTLY STRONGER": it ACCEPTS a
  declared family root (a root resolves, it is just not a leaf), which is why `upgrade-test` is not
  flagged, and otherwise flags the same population `declared_absent` reports minus roots.
  NOTE THAT `upgrade-test` IS REACHABLE AND MUST NOT BE FLAGGED, which is a real behavioral difference
  from the census view and must not be papered over: `aw upgrade-test --help` exits 0 and prints its own
  help, because it is a family ROOT with subcommands. It appears in `declared_absent` only because a root
  is never a LEAF. So the behavioral gate's allow-set has ONE member where the census view would have
  needed two, and the plan must state that rather than carrying a dead entry.
  FOLLOW THE IN-MODULE PRECEDENT FOR MECHANICS: the sibling
  `tests/test_exit_contract_conformance.py::test_usage_error_floor_gate_tree_wide` already drives
  `parser.parse_args` in-process under redirected streams over `get_declared_leaves()` and derives its
  observation dynamically rather than hardcoding it. Reuse that shape for the message's `--help` capture.
  DO NOT use a subprocess sweep: measured, an in-process sweep takes well under a second for all 162
  declarations (0.50s at authoring for the `--help` form; under 1ms for the dispatch-table walk at
  review), while a subprocess per command
  exceeded a 120s budget, which would force a `@pytest.mark.slow` marker and so be DESELECTED from the
  default suite by the configured `addopts` (`-m 'not slow and not livecorpus'`) and from the
  fail-closed CI job.
  - Depends on: none
  - Expected outcome: a new test in `tests/test_command_surface_declarations.py` that passes at HEAD
    (with the allow-set of E-02) and fails when a declaration names a command no parser accepts,
    INCLUDING one nested under a positional- or REMAINDER-taking parent (`set <phantom>`,
    `runs <phantom>`), while NOT flagging a declared family root (`upgrade-test`), a declared alias
    (`att`, `spec set`) or a REMAINDER-forwarding leaf (`agy exec`); the
    module's existing `test_zero_undeclared_parser_leaves` still passes unchanged; the new test adds well
    under a second to the suite.
  - Execution state: pending

- [ ] E-02 Give the gate an explicit, individually-justified allow-set so it is GREEN at HEAD and turns
  RED on the next drift, placed as module-level data in `tests/conformance_matrix.py`.
  FOLLOW THE SHAPE `EXEMPTION_REGISTRY` ALREADY ESTABLISHES in that module, do not invent a second
  convention: a frozen dataclass per entry carrying a typed reason, a citation and prose, with a header
  stating the governing rule. That registry's header states it outright ("THE REGISTRY IS A CEILING, NOT
  A CONVENIENCE ... There is no catch-all, wildcard, or default-skip permitted; every exempted leaf must
  be individually enumerated with a valid typed reason and resolvable citation"), and a `known_broken`
  entry REQUIRES a filed item id. The same rule must govern this allow-set, for the same reason: an
  allow-set with a wildcard reproduces the hole it closes.
  SEED IT WITH EXACTLY ONE MEMBER: `prompts set`, citing backlog `68sur3` and pending plan `7z3ovv`,
  which removes it. Do NOT add `upgrade-test` (E-01: it is reachable, so the behavioral gate never flags
  it). If a second member appears while executing, that is the gate working and it must be REPORTED, not
  absorbed.
  PUT THE DATA IN THE HARNESS AND THE ASSERTION IN THE TEST MODULE, per OQ-01: `conformance_matrix.py`
  has no `test_` functions and is the established home for per-command exception data, which
  `test_agent_surface_conformance.py` already imports by name.
  ASSERT SET EQUALITY, NOT SUBSET. `7z3ovv`'s V-03 shows the weakness to avoid: it asserts
  `declared_absent` no longer contains `prompts set`, which stays green while any number of other
  commands break. Equality is what makes the next one red.
  THE FAILURE MESSAGE MUST NAME BOTH DIRECTIONS, because each needs a different human act. An
  UNEXPECTED unreachable command means a declaration was added for a command no parser accepts, and the
  fix is to register it or drop the declaration. A member that has become REACHABLE means the drift was
  fixed and the stale allow-set entry must be DELETED. The second direction is not hypothetical:
  `7z3ovv` is pending and WILL make `prompts set` reachable, so whichever plan executes second must
  delete the entry, and the message is what tells its executor so.
  - Depends on: E-01
  - Expected outcome: the allow-set exists with exactly one entry carrying a typed reason and a
    resolvable item citation; the E-01 gate is green at HEAD; removing the entry makes it red.
  - Execution state: pending

### Task group 2: stop the code claiming a deleted test gates it

- [ ] E-03 Correct the two in-code comments that describe the deleted gate as live, so a reader is not
  sent to a test that does not exist.
  `agent_workflows/command_surface.py` claims, in the `runs` family declaration block, that declaring a
  family root "registered as declaration/parser DRIFT
  (`test_declared_absent_leaves_are_only_the_known_prompts_family`), exactly as it would for the other
  bare-invokable family roots (`aw ipd` renders the board, `aw specs`, `aw backlog`), none of which is
  declared either". Re-point it at the gate E-01 adds, AND correct its substance, because that comment is
  now wrong in two ways rather than one: the named test is gone, and the new gate is behavioral, so it
  would NOT flag a declared family root (F-04 measured `aw upgrade-test --help` at exit 0). Say that
  plainly. The comment's underlying JUDGEMENT remains correct and independently corroborated, that
  `ipd`, `specs`, `backlog`, `prompts`, `runs`, `research` and `config` are all bare-invokable roots and
  none is declared while `upgrade-test` is; preserve that reasoning and note that the live owner of the
  inconsistency is `lbbo9s`.
  `tests/conformance_matrix.py`'s `build_matrix` claims, on the `declared_absent` branch, "(kept out of
  the live matrix; the declaration-vs-parser drift is asserted elsewhere)". The parenthetical was TRUE
  when written and is false now. Make it name the gate that exists, and state that `declared_absent`
  itself is REPORTED but no longer ASSERTED over, which is the honest description once E-01 asserts a
  different (stronger) property.
  DO NOT CHANGE `build_matrix`'s BEHAVIOR. Its `continue` before emitting rows is correct: an unreachable
  command cannot be exercised, so manufacturing coverage rows would be a false coverage claim.
  - Depends on: E-02
  - Expected outcome: neither comment names a nonexistent test; both describe the restored gate
    accurately including its behavioral scope; no executable line of `build_matrix` changes.
  - Execution state: pending

- [ ] E-04 Run the whole-repository validation gate and leave the backlog item for the runner.
  DO NOT SET `68sur3` DONE AND DO NOT CLEAR ITS GATE. It carries `- Blocks-Release: next` and
  `- Work-Kind: bug`. `aw backlog set done 68sur3` would FAIL CLOSED anyway while a same-gate carrier is
  unexecuted (`check_engine.evaluate_blocking_close`, HANDOFF arm: EVERY `From-Backlog` carrier with the
  same `Blocks-Release` must be executed), and `--blocks-release -` would silently drop a live release
  gate. The item is ALREADY `graduated` (re-measured at review: `- Status: graduated`,
  `- Graduated-To: declabsent`, history `graduated by run run-20261001T221821Z-1985969: gm9baj`), so
  there is nothing to set; this plan must not edit the item at all.
  THE TWO CARRIERS BOTH CARRYING THE SAME GATE IS CORRECT, not a defect to reconcile: with two same-gate
  carriers (`7z3ovv` and `gm9baj`) the HANDOFF arm holds the item open until BOTH execute, which is
  wanted, because either alone leaves real work undone.
  RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies
  `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so `-n0` makes it several times slower
  and a second `-q` suppresses the `N passed` line this plan requires pasted.
  - Depends on: E-03
  - Expected outcome: the bare suite shows no failure NAME absent from a same-session pre-change
    baseline (capture the bare-suite failure names and `aw check all` output BEFORE E-01's edits, in the
    executing session; F-05's authoring numbers are context, not the bar, because the tree drifts);
    `aw check all` shows no new finding relative to that baseline; `git diff -- .aw/records/backlog/` is
    EMPTY.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `command_surface.COMMAND_INVENTORY` is the normative declaration of every CLI leaf's output contract.
  `command_surface.find_undeclared_leaves` computes the forward direction (a parser leaf with no
  declaration) and `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`
  asserts it EMPTY. The reverse direction (a declaration no user can invoke) is asserted nowhere as of
  commit `19313eed7`.
- TESTS MUST ASSERT OUTCOMES, NEVER CODE STRUCTURE. GUIDING_PRINCIPLES P16 and AGENTS.md forbid tests
  that read production source, assert symbol censuses, or pin text. The maintainer's note on backlog
  `xvp5vx` (2026-09-28) applies this directly to restoring trimmed tests: "We test outcomes and
  functionality, never code structure or text in a script. Zero tests that pin code. Any audit of
  deleted tests must strictly ignore tests that pinned code, AST, or text, and must never propose
  restoring them." This is why E-01 drives the parser instead of restoring the deleted census assertion.
- A family ROOT is never a parser leaf by construction: `command_surface.discover_parser_leaves` recurses
  into `_SubParsersAction.choices` and reports only parsers with no subparsers. So declaring a root
  always shows up in `declared_absent`, even when the root is perfectly invokable, which is exactly the
  `upgrade-test` case and the reason the behavioral gate and the census view disagree by one member.
- `tests/conformance_matrix.EXEMPTION_REGISTRY` is the established shape for a per-command justified
  exception: a frozen `Exemption` dataclass with `reason_kind` (`sanctioned_raw` | `known_broken` |
  `not_runnable`), a `citation`, and a prose `reason`, with a header declaring it "a CEILING, NOT A
  CONVENIENCE", requiring a filed item id for `known_broken`, and permitting no wildcard or
  default-skip. 27 entries today (16 `not_runnable`, 7 `sanctioned_raw`, 4 `known_broken`).
- `tests/conformance_matrix.py` is a HARNESS MODULE, not a test module: no `test_` functions, imported by
  `test_agent_surface_conformance.py`, `test_exit_contract_conformance.py` and
  `test_index_check_agent_records.py`. Its docstring names its "former drivers"
  (`test_cli_conformance_matrix.py`, `test_cli_quality_gates.py`), both deleted by `19313eed7`. Data
  belongs in the harness; assertions belong in a `test_*` module.
- The fail-closed CI job `output-conformance` in `.github/workflows/tests.yml` runs exactly ONE test
  file, `tests/test_command_surface_declarations.py`, despite the step name advertising "E-01 matrix +
  E-02 gates + E-03 docs". A gate placed anywhere else is outside that job.
- The default suite DESELECTS `slow` and `livecorpus` markers via `addopts`, so a subprocess-heavy sweep
  would not run by default. In-process `parse_args` under redirected streams is the established fast
  pattern (`test_exit_contract_conformance.test_usage_error_floor_gate_tree_wide`), with that file's own
  standing warning that the in-process shortcut is justified PER PATH and must be re-measured per use.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Every row was measured in this lane at HEAD `aa7631e55` on 2026-10-02, by driving the real parser/CLI and
reading real git history. No production file was modified while measuring; `git status --porcelain` shows
only this plan.

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE GATE THAT WOULD HAVE CAUGHT THIS DEFECT WAS DELETED AND NOT REPLACED.** This is the finding the plan exists for and it is absent from both backlog items. | `git grep -ln test_declared_absent_leaves_are_only_the_known_prompts_family 19313eed7^ -- tests/` returns `tests/test_cli_conformance_matrix.py`; the same search at HEAD returns NOTHING under `tests/`. The deleted body asserted `set(report.declared_absent) == {"prompts set"}` with the docstring "This test PINS that set so a NEW silent drift (a declaration whose parser leaf silently vanished) fails CI instead of hiding." Commit `19313eed7` is `test: trim test suite from 9,136 to under 2,000 tests`, dated 2026-09-24; its `--stat` shows `tests/test_cli_conformance_matrix.py | 224 --`. At HEAD the ONLY surviving occurrence of that test name outside `.aw/records/` is a COMMENT in `agent_workflows/command_surface.py`. |
| F-02 | **THE POPULATION THE DELETED TEST PINNED AT ONE HAS ALREADY DOUBLED, two days after the deletion, with nothing going red.** So the hole is not theoretical. | `build_matrix(cli._build_parser())` reports `declared_absent: ['prompts set', 'upgrade-test']` and `undeclared: []` over 1193 rows. `git log -S 'command="upgrade-test"' -- agent_workflows/command_surface.py` names exactly one commit, `648597285` (`feat(upgrade-test): restore safety tests and graduate harness to aw upgrade-test`, 2026-09-26), i.e. TWO DAYS AFTER the deletion. `python3 -m pytest tests/test_command_surface_declarations.py` is green at HEAD (`1 passed in 0.44s`), confirming nothing gates it. |
| F-03 | **THE BEHAVIORAL GATE WORKS, IS FAST, AND DISAGREES WITH THE CENSUS VIEW BY ONE MEMBER** - which is what makes it the right assertion and not merely a P16-compliant substitute. REVIEW CORRECTION (HEAD `0475ce787`): the authored `--help`/`invalid choice` DETECTOR has false negatives, so E-01 now uses the parser dispatch-table walk; see the appended review measurement. | Driving `parser.parse_args([*leaf.split(), "--help"])` under redirected streams across all 162 declarations took **0.50s** and reported exactly ONE unreachable command: `('prompts set', 2, ["agent-workflows prompts: error: argument prompts_command: invalid choice: 'set' (choose from 'new')"])`. `upgrade-test` was NOT flagged. A subprocess form of the same sweep (`python3 -m agent_workflows <leaf> --help` per command) found the same single failure but EXCEEDED a 120s budget, which would force `@pytest.mark.slow` and so be deselected by the configured `addopts`. REVIEW MEASUREMENT: injected phantoms `set phantom`, `backlog set phantom` (`--help` exit 0, no `invalid choice`) and `runs phantom` (exit 2, `unrecognized arguments: --help`) are all MISSED by the `--help` detector; resolving tokens through each level's `_SubParsersAction.choices` flags all three plus `ipd phantom` and `phantom`, flags exactly `['prompts set']` over the 162 real declarations in 0.0009s, and resolves `upgrade-test`, `att`, `spec set`, `sanitize` and `agy exec`. |
| F-04 | A DECLARED FAMILY ROOT IS REACHABLE EVEN THOUGH IT IS NOT A LEAF, so the `upgrade-test` member of `declared_absent` is NOT a user-visible defect of the kind this gate asserts. | `python3 -m agent_workflows upgrade-test --help` exits **0** and prints its own help. `python3 -m agent_workflows upgrade-test` (no subcommand) exits 2 with a usage block, which is the separate defect `lbbo9s` owns. Of the bare-invokable roots, `ipd`, `specs`, `backlog`, `prompts`, `runs`, `research` and `config` are each NEITHER declared NOR a leaf; only `upgrade-test` is declared. Its six real leaves (`upgrade-test env|clean|probe|sandboxes|list|new`) are all present and declared. |
| F-05 | THE BASELINE IS GREEN ON EVERY MODULE THIS PLAN TOUCHES, so a failure after the change belongs to this plan. | `python3 -m pytest tests/test_agent_surface_conformance.py tests/test_command_surface_declarations.py -o addopts="" -q` reported `44 passed in 60.90s`. `python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q` reported `1 passed in 0.44s`. `aw check plans` reports 71 findings tree-wide at HEAD, of which exactly one names this plan file. |
| F-06 | **`7z3ovv` ALREADY OWNS THE REGISTRATION AND ALREADY OWNS GRADUATING THIS ITEM, so re-authoring it would collide.** This is why the scope is the gate and not the item's stated fix. | `.aw/records/plans/pending/20261002-promptsset-01-7z3ovv-...ipd.md` is `- Status: to-review`, `- From-Backlog: um8ikz`, `- Blocks-Release: next`, and its `- Scope-Paths:` declares `agent_workflows/cli.py`, `agent_workflows/status_set.py`, `agent_workflows/prompts.py`, `agent_workflows/command_surface.py`, `tests/test_status_set.py`, `tests/test_exit_contract_conformance.py`, `tests/test_prompts_set_surface.py`, `docs/artifact-lifecycles.md` AND `68sur3`'s own backlog file. Its F-12 row names `68sur3` a duplicate; its E-07 obliges setting it `graduated` citing `7z3ovv`. The duplicate source item `um8ikz` sits in `.aw/records/backlog/graduated/` with history `2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 7z3ovv`. |
| F-07 | `7z3ovv`'s OWN VALIDATION DOES NOT CLOSE THIS HOLE, even incidentally, so this plan is not redundant with it. | Its E-03 and V-03 assert that `build_matrix(...).declared_absent` "no longer contains `prompts set`", a CONTAINMENT check that remains green with `upgrade-test` still absent and with any future phantom present. No item in it asserts over the population, and `tests/test_command_surface_declarations.py` is NOT in its `- Scope-Paths:`. |
| F-08 | THE ITEM'S OWN MEASUREMENTS RE-MEASURE TRUE AT THIS HEAD, so nothing in it needs correcting. | `python3 -m agent_workflows prompts set draft foo` prints `agent-workflows prompts: error: argument prompts_command: invalid choice: 'set' (choose from 'new')`. `cli.main` still carries the `if prompt_cmd == "set":` arm returning `status_set.run_set_command(args.args, scoped_type="prompts", ...)`. `cli._COMMAND_DESCRIPTIONS["prompts"]` still contains `"'set' transitions a staged prompt's status"`. `status_set._offer_self_commit`'s docstring still reads "ONE integration in the shared engine covers every `set` variant (`aw set`/`ipd set`/`spec set`/`prompts set`/`backlog set`)", while the live `set` leaves are `set`, `backlog set`, `config set`, `ipd set`, `ipd dependencies set`, `specs set`. |
| F-09 | THE MISSING CONFORMANCE COVERAGE IS QUANTIFIED, which is what makes `68sur3`'s "five live callers when four are live" an observable defect rather than a prose nit. | `required_scenarios(decl)` for `prompts set` is `('tty', 'non_tty', 'agent', 'no_color', 'help', 'usage_error', 'json', 'success_preview')` (8 scenarios). `build_matrix`'s `declared_absent` branch `continue`s BEFORE the `for scenario in required_scenarios(decl)` loop, so all 8 are dropped from the 1193 rows with no finding emitted. `'prompts set' in command_surface.get_declared_leaves()` is `True` (162 declared leaves), while the only `prompts` leaf is `prompts new`. |
| F-10 | THE `upgrade-test` DECLARATION HAS AN OWNER ALREADY, so no part of it is this plan's to fix. | `.aw/records/backlog/open/...lbbo9s...` is `- Status: open`, `- Work-Kind: bug`, `- Blocks-Release: next`, summary "aw upgrade-test bare group declares agent_record_kind=result but prints argparse usage at exit 2". `EXEMPTION_REGISTRY["upgrade-test"]` already cites `lbbo9s` with `reason_kind="known_broken"`. |

## Proposed changes (ordered, validatable)

1. `tests/test_command_surface_declarations.py`: add a behavioral test driving the real parser over every
   declared command and failing on an argparse `invalid choice`. (E-01)
2. `tests/conformance_matrix.py`: add a module-level allow-set in the `EXEMPTION_REGISTRY` shape with the
   single measured member, so the gate is green at HEAD and red on the next drift. (E-02)
3. `agent_workflows/command_surface.py` and `tests/conformance_matrix.py`: re-point and correct the two
   comments that cite the deleted test / claim the drift is "asserted elsewhere". Comment-only. (E-03)
4. Run the repository-wide gate; leave the backlog item untouched for the runner. (E-04)

## Deferred / out of scope (with reason)

- REGISTERING `aw prompts set`, NARROWING `TYPE_STATUSES["prompts"]`, AND FIXING THE PROMPT WRITER are
  deliberately NOT done here. Pending plan `7z3ovv` declares every one of those paths and was authored
  from the duplicate item `um8ikz` (F-06). Two pending plans in the same hunks of `cli._build_parser` and
  the same `TYPE_STATUSES` entry is the collision the production contract exists to prevent.
  - Carrier: 7z3ovv
- DELETING THE `upgrade-test` ROOT DECLARATION, or fixing its `agent_record_kind`, is out of scope. Both
  belong to `lbbo9s`, which is `open` and release-gated (F-10). The behavioral gate this plan adds does
  not flag it at all (F-04), so nothing here depends on that resolution.
  - Carrier: lbbo9s
- A GENERAL AUDIT OF WHAT ELSE THE 2026-09-24 SUITE TRIM DELETED is out of scope: `19313eed7` removed
  assertions across roughly a hundred files. That audit is already filed and DONE as a census
  (`xvp5vx`, graduated to plan `oyh28b`, now `executed`); this plan closes the single hole that
  `68sur3`'s defect led to, which that census did not surface.
  - Carrier-Evidence: .aw/records/backlog/done/20260928-xvp5vx-01-xvp5vx-audit-guards-lost-in-suite-trim.backlog.md
- CHANGING `build_matrix`'s SKIP BEHAVIOR is out of scope and would be wrong, so there is nothing to hand
  off. An unreachable command cannot be exercised, so emitting coverage rows for it would manufacture a
  false coverage claim. The defect is the missing assertion, not the skip.
  - Carrier-Declined: Not a defect. The skip is the correct behavior and no change is wanted, so an owner would have nothing to do.
- RECONCILING THE `output-conformance` CI STEP NAME with what it runs (it advertises "E-01 matrix + E-02
  gates + E-03 docs" and runs one file) is a real inaccuracy observed while placing E-01, but it is a
  workflow-file edit outside this plan's `- Scope-Paths:` and unrelated to the drift.
  - Carrier-Declined: Misleading prose in CI configuration with no user-perceptible impact, which the repository's own perceptibility test puts below the `bug` bar; filing it would add a release-gated item for a comment.

## Scope check

- Over-scope: none. The three declared paths are the assertion
  (`tests/test_command_surface_declarations.py`), the allow-set data plus one comment
  (`tests/conformance_matrix.py`), and one stale comment (`agent_workflows/command_surface.py`).
  `agent_workflows/command_surface.py` is ALSO declared by `7z3ovv`, disclosed deliberately: this plan's
  edit there is COMMENT-ONLY in the `runs`-family block, while `7z3ovv` edits the `prompts set`
  declaration's `legacy_flags` tuple. Different hunks of one file, and the runner isolates each plan in
  its own worktree and merges through the revalidation gate, so the overlap is not a runtime hazard. No
  production behavior changes.
- Under-scope: the `prompts set` allow-set entry becomes STALE the moment `7z3ovv` executes, and
  whichever plan runs second must delete it. Handled by E-02's required failure message (which names the
  stale-entry direction explicitly) rather than by an `executed:7z3ovv` dependency edge, because such an
  edge would block this gate behind an unrelated plan's approval and leave the hole open longer for no
  safety gain: the equality assertion fails LOUDLY and names exactly what to delete.

## Required tests / validation

- `python3 -m pytest tests/test_command_surface_declarations.py` must pass, and the new test must be
  shown to FAIL on a deliberately-injected unreachable declaration, then pass again once reverted. A
  gate never observed red is not a gate.
- The new test must also be shown to FAIL when the allow-set entry is stale (make `prompts set`
  reachable, or drop its declaration, and observe the stale-entry branch of the message).
- `python3 -m pytest tests/test_agent_surface_conformance.py tests/test_exit_contract_conformance.py`
  must pass: both import `tests.conformance_matrix`, so the new module-level data must not perturb them.
- The new test's own runtime must be measured and pasted, to evidence it carries no `slow` marker and so
  actually runs in the default suite and the fail-closed CI job.
- The bare full suite (`python3 -m pytest`) must introduce no failure name absent from a same-session
  pre-change baseline.
- `aw check all` must report no new findings relative to a same-session pre-change run.

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `- Scope-Paths:`. This plan adds a test and
corrects two comments; it changes no CLI contract, no artifact contract, and no status vocabulary.
Checked for a governing spec: the command-surface contract is carried by `docs/cli-output-contract.md`
(which `EXEMPTION_REGISTRY` cites for its `sanctioned_raw` entries) and that document describes OUTPUT
shape per command class, not the declaration-versus-invokability invariant, so nothing in it is made
stale. No user-facing documentation changes, because nothing a user invokes behaves differently.

## Open questions

### OQ-01: should the allow-set live in `tests/conformance_matrix.py` or in the test module that asserts it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence, in the harness module. The
  precedent is unambiguous: `EXEMPTION_REGISTRY`, the existing per-command justified-exception registry,
  lives in `tests/conformance_matrix.py` and is imported by the test modules that consume it
  (`test_agent_surface_conformance.py` imports it by name). The harness holds DATA and has no `test_`
  functions; the `test_*` modules hold assertions. E-02 therefore puts the data in the harness and E-01
  the assertion in the CI-wired test module.

### OQ-02: should the gate assert over `declared_absent`, or drive the parser?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, drive the parser. Asserting over
  `build_matrix(...).declared_absent` would restore the deleted test's shape, but that is a test of a
  derived internal census rather than of an outcome, which GUIDING_PRINCIPLES P16 forbids and which the
  maintainer's standing ruling on `xvp5vx` addresses in terms that name this exact case (an audit of
  trimmed tests "must strictly ignore tests that pinned code, AST, or text, and must never propose
  restoring them"). The routing form is measurably cheap (F-03: under 1ms for 162 declarations, one
  real failure detected; review replaced the `--help`-text detector with the dispatch-table walk after
  measuring its false negatives), and it exposed a fact the census view hides, that a
  declared family root is REACHABLE (F-04), which shrinks the allow-set from two members to one.

### OQ-03: should the gate be a failing test or merely a report?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, a failing test. Three reasons from the repository's own
  record. First, the deleted test it replaces was a hard assertion whose docstring states the intent
  ("fails CI instead of hiding"). Second, its sibling in the same module,
  `test_zero_undeclared_parser_leaves`, asserts the opposite direction as a hard equality against the
  empty set, so a softer treatment of this half would be an unexplained asymmetry. Third, this
  repository records leaving a rule permanently advisory as a known failure mode (the
  `check.live-bug-ungated` registration comment cites `rnkqrc` E-05 for exactly that), and the measured
  history here is the strongest case available: with no gate at all, the population silently doubled in
  two days.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: Paste the new test verbatim. Paste the output of a run showing it green, and
    paste its MEASURED runtime from `python3 -m pytest tests/test_command_surface_declarations.py
    -o addopts="" -q --durations=5`, evidencing it is fast enough to carry no `slow` marker (F-03
    measured the sweep well under a second). Paste evidence that the test ASSERTS AN OUTCOME and reads no
    production source: show that its only project imports are `cli`/`command_surface`/the allow-set (stdlib `argparse`,
    `contextlib`, `io` are expected) and that it contains no use of `inspect`, `ast`, or source reading, per GUIDING_PRINCIPLES P16. Paste a run of
    the sweep showing the one unreachable command detected WITH argparse's own `invalid choice` text in
    the failure message, and showing `upgrade-test` NOT flagged (F-04). Paste a scratch probe (not
    committed) running the test's detector over the phantoms `set phantom`, `backlog set phantom` and
    `runs phantom`, showing ALL THREE flagged, and over `upgrade-test`, `att`, `spec set` and `agy exec`,
    showing NONE flagged; a detector that misses any of the three phantoms is the rejected `--help`-text
    design and does NOT validate this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THIS ITEM MUST SHOW THE GATE RED, NOT ONLY GREEN; a gate never observed failing
    is unproven. Paste four runs of `python3 -m pytest tests/test_command_surface_declarations.py`:
    (1) at HEAD before the change, showing the module green with its single existing test;
    (2) after the change, green with both;
    (3) with a deliberately-injected `CommandDeclaration` for a command no parser accepts, NESTED UNDER A
    POSITIONAL-TAKING PARENT (e.g. `set phantom`, the false-negative class F-03 measured), showing the
    new test FAIL and the message NAMING the injected command as an unexpected unreachable member;
    (4) after reverting the injection, green again.
    Then paste a FIFTH run demonstrating the stale-entry direction: delete the `prompts set` declaration
    (or register its parser leaf) so the allow-set entry is stale, and show the test fail with a message
    naming the entry to DELETE. Paste `git diff --stat` after each revert showing the injection is gone.
    Paste the allow-set verbatim showing exactly ONE entry, no wildcard key, and a resolvable citation
    (`aw find 68sur3` and `aw find 7z3ovv`, or the equivalent resolution). Also paste the
    `.github/workflows/tests.yml` `output-conformance` step's `pytest` invocation as it stands, to
    evidence the new test is inside that fail-closed job rather than merely in the suite.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste both corrected comments verbatim, and paste a repository-wide search for
    `test_declared_absent_leaves_are_only_the_known_prompts_family` showing ZERO matches outside
    `.aw/records/` (plan/record history legitimately keeps the old name). Paste a diff of
    `tests/conformance_matrix.py` restricted to `build_matrix` showing NO executable line changed (the
    `continue` and the `required_scenarios` loop byte-identical), evidencing the comment-only claim.
    Confirm the corrected `command_surface.py` comment states that the new gate is BEHAVIORAL and so
    would not flag a declared family root, since asserting otherwise would re-introduce a false claim.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the BARE `python3 -m pytest` run including its `N passed` summary line (do
    not add `-n0` or a second `-q`), for BOTH the same-session pre-change baseline and the post-change
    run, and compare failure sets BY NAME (any post-change failure must be shown present before).
    Paste `aw check all` output before and after, naming any delta. Paste `git diff -- .aw/records/backlog/` showing it is EMPTY, evidencing the
    backlog item was left entirely to the runner. Paste `git diff --cached --name-only` immediately
    before committing, showing only this plan's three declared paths plus this plan file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before
execution. It carries `- Blocks-Release: next`, inherited from backlog item `68sur3` per the
gate-travels-with-the-work rule.

A REVIEWER SHOULD TEST THE SCOPE DECISION FIRST. The plan deliberately does NOT do what its source item
asks (register or remove the `prompts set` verb), on the measured ground that pending plan `7z3ovv`
already owns that work, declares those paths, and is itself obliged to graduate this item (F-06). If the
maintainer disagrees and wants this item's stated fix duplicated here, this plan should be RETIRED rather
than rewritten, because the two would then edit the same hunks of `cli.py` and `status_set.py`.

Execution contract: commit only the declared `- Scope-Paths:` plus this plan file, through
`aw commit <plan> -- <paths>`; never `git add -A`, never push. Paste actual runner output for every
validation item; never claim a test result that was not run. `68sur3`'s `- Status:` is the RUNNER's to
set to `graduated`; this plan must not set it, and must not set it `done`.

Post-gate lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms,
the plan moves to `.aw/records/plans/executed/` through the tooled transition: under `aw oc run` /
`aw agy run` the runner owns finalize; when executed by hand, the executor runs `aw ipd finalize`.
Never `git mv` it by hand.

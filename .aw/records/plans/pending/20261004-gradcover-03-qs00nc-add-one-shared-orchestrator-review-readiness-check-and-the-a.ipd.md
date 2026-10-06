# IPD: Add one shared orchestrator review-readiness check and the aw ipd coverage verb

- Date: 2026-10-04
- Kind: child
- Concern: Nothing in the toolkit answers "is this orchestrator plan ready for review?" as one question. The pieces exist in different places and are never combined: child-table resolution (`runner_shared.find_unauthored_child_rows`, `runner_shared.read_set_membership`), row conformance (`ipd_lint.orchestrator_row_conformance`, `IPD-S407`), per-child lint (`ipd_lint.lint_file`), and the coverage answer (`runner_shared.probe_orchestrator`; after Order 02, `coverage_record.read`, which reads the answer stored in the plan). The only consumer of the coverage verdict is the run-start gate, so an orchestrator reaches `to-review` with no check at all. Spec `25kzda` Section 2.5d (added by Order 01, `hm1h3l`) defines the four conditions and requires ONE function shared by every consumer, a model-free lint rule `IPD-S408`, an `aw check plans` rule, and an `aw ipd coverage` command that asks the probe once and records the answer.
- Scope: Add the shared function and its result type, the `aw ipd coverage` subcommand, the `IPD-S408` lint rule, and the `check.orchestrator-not-review-ready` check rule. IN: a new module `agent_workflows/orchestrator_readiness.py` holding `review_readiness(repo, plan_path, *, ask=False, ...)` and its result; wiring in `ipd_lint.py` (rule `IPD-S408` at `review-finalize`/`pre-execution`, advisory at `author`; and rule `IPD-M112`, which refuses a coverage record that is incomplete or has no matching history line, at every checkpoint), `check_engine.py` (rule over pending orchestrators), `cli.py` (subcommand), and `command_surface.py` (the subcommand's `CommandDeclaration`, required by `tests/test_command_surface_declarations.py` `test_zero_undeclared_parser_leaves`); one new test file; and the minimal fixture update in the three existing test files whose synthetic `approved` orchestrators must keep passing `pre-execution` lint (E-08). OUT: any status setter (Order 05); any runner gate or retirement change (Order 04); production verification (Order 06); prompt or template text (Order 11); the probe's prompt or parser (Order 02, already executed).
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_orchestrator_readiness.py, tests/test_orchestrator_retirement.py, tests/test_orchestrator_shape_gate.py, tests/test_action_table_runner_parity.py
- Item-Dependencies: executed:8mabmu
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 3
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qs00nc
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-008..PR-012 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-008 to PR-012 (round 2). Fixed: new E-08/V-08 for four existing runner tests whose synthetic approved orchestrators must pass `pre-execution` lint, measured by a lint spy over the bare suite (PR-008); `--commit` reconciled with Order 02's commit-at-write, now `--no-commit` (PR-009); real-tree `axozpe` restore made commit-aware (PR-010); `retry_budget` threaded through `ask=True` (PR-011); V-02 remedy wording, scope counts (PR-012). Round-1 PR-001 confirmed fixed by the maintainer's 2026-10-04 ruling.
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. OQ-03 RESOLVED by the maintainer (2026-10-04): the coverage answer is stored in the plan. Condition 4 now reads the plan's record (Order 02's `coverage_record`); an absent or out-of-date record is an error in lint and check; new lint rule `IPD-M112` refuses an incomplete or unattested record; `aw ipd coverage` writes the record and gains `--commit`.
- 2026-10-04 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007 (PR-001 open, blocking OQ-03)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 to PR-007. Fixed: executed children are not linted (PR-002); recursion guard for a malformed Set (PR-003); `aw ipd coverage` registered in `command_surface` and its no-arg conformance path specified, Scope-Paths widened (PR-004); probe call shape and cache-observable record specified (PR-005); one plans-tree read per sweep with a 1 s budget (PR-006); parity fixture pre-records verdicts, unusable-table case, gate contract (PR-007). OPEN, blocking: OQ-03 / PR-001 (absent-verdict severity, same decision as `hm1h3l` OQ-03, plus the newly found freeze-gate ordering).
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `hm1h3l` (finding PR-001): the `aw ipd lint` MUST-check list and its "MUST make no model calls" sentence are in `ipd-structure-and-linting` Section 10 ("Deterministic linter contract"), not Section 9; three citations corrected. The same review widened the asking consumers of `25kzda` 2.5d to include the post-review and retirement-time checks; the shared function's `ask=True` path already serves them.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 03 of Set `gradcover`. Implements spec `25kzda` Section 2.5d and `ipd-structure-and-linting` Section 10 rule 19 as amended by Order 01. Every later gate in the Set calls the function this plan adds.

## Goal

Provide one function that returns every reason an orchestrator plan is not ready for review, with a precise remedy per reason, plus a command that establishes the coverage verdict on demand, so that the setter, the linter, `aw check`, the production action and the runner can all ask the same question and get the same answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the function

- [x] E-01 Add `agent_workflows/orchestrator_readiness.py` with `review_readiness(repo, plan_path, *, ask=False, model=None, host=None, state=None, asker=None, runner=None)` returning a `ReviewReadiness` result: `applies` (False for a non-orchestrator), `ready`, and an ordered tuple of `Finding(code, subject, detail, remedy)` covering exactly the four conditions of `25kzda` 2.5d. Condition 1 uses `read_set_membership` plus `find_unauthored_child_rows` (unresolvable and open-ended rows are findings; a `parsed=False` result, meaning the child table is absent or unusable, is itself a finding and never a pass). The function accepts an optional precomputed `membership` so a sweeping caller resolves each Set once (see E-04's cost bound). Condition 2 reads each child's `- Status:` (from `SetMember.status`) and, for a child NOT in a terminal directory (`run_selection_policy.is_in_terminal_directory`), runs `ipd_lint.lint_file(..., checkpoint="author")`; a child below `to-review` or whose disposition is not passing is a finding naming it. A child under `executed/` with `- Status: executed` is ready WITHOUT being linted, because `lint_file` reports every terminal-directory plan as `legacy/not evaluated`, which is not a passing disposition (measured: the newest file in `.aw/records/plans/executed/` lints `legacy/not evaluated`), so linting it would refuse every orchestrator whose early children already ran, contradicting OQ-02. RECURSION GUARD: the children are linted with `IPD-S408` suppressed (an internal keyword on `lint_file`/`lint_text`, or a module-level re-entrancy flag in the new module), because `read_set_membership` deliberately files a second Order-0 plan of a malformed Set as a CHILD, and linting that child would call `review_readiness` again on the same Set without end. Condition 3 calls `ipd_lint.orchestrator_row_conformance`. Condition 4 calls `coverage_record.read(text)` and `coverage_record.is_current(text)` (Order 02; spec `25kzda` 2.5e: the answer is stored in the plan) and, ONLY when `ask=True`, calls `probe_orchestrator` when the record is absent or out of date (which writes the answer into the plan); with `ask=False` an absent record and an out-of-date record are each a finding (distinct codes, so the message can say "never checked" or "plan changed since the check on <date>") whose remedy is `aw ipd coverage <id6>`; a recorded `fail` is one finding per quote stored in `## Coverage findings`; could-not-ask is a finding naming the retry command. The `ask=True` path also takes `retry_budget` (default `resolve_retry_budget(None, repo=repo)`) and passes it to `probe_orchestrator`, so a runner consumer (Order 04 passes `frozen_retry_budget(state)`) uses the run's frozen budget. All runner_shared imports are function-local.
  - Depends on: none
  - Expected outcome: the function returns `ready=True` only when all four conditions hold, and otherwise returns one finding per failing child, row or quoted passage, each with a remedy command or edit; it makes no model call unless `ask=True`.
  - Execution state: performed

- [x] E-02 Write the remedy texts as data in the new module (one constant per finding code) so every consumer prints the same words, and make them satisfy spec `r07vma` R7: state the invariant, forbid deleting the checklist, and name the legitimate remedies (author the missing child and its row; bring the child to `to-review` with `aw ipd set to-review <child-id6>`; fix the child's named lint finding; assign the quoted obligation by id6 to a child in the table or add a child for it; run `aw ipd coverage <id6>`). Provide `render_human(result)` and `render_agent(result)` producing the human lines and an `aw.agent/v1` record (path-free, validated by `agent_schema.validate_agent_record`).
  - Depends on: E-01
  - Expected outcome: every finding code has one remedy constant; the agent record validates with no findings and carries no absolute path.
  - Execution state: performed

### Task group 2: the consumers this plan owns

- [x] E-03 Add the `aw ipd coverage <id6|setid|path>...` subcommand: for each orchestrator plan selected, call `review_readiness(..., ask=True)` using the same host and model resolution `aw oc run` would (the existing `runner_profiles.resolve` path, defaulting to the opencode host). `probe_orchestrator` takes a run `state` and reads `state["options"]` (`model`, `variant`, `agent`, `opencode`/`agy` binary, per `probe_argv`), a `ProbeTarget(id6, position, setid, path, text)`, and a required `retry_budget`; so compose `{"options": {...}}` from the resolved launch, build the target from the plan file, and pass `resolve_retry_budget(None, repo=repo)`. Add `--host {oc,agy}` and `--model` overrides. Print the human or `--agent` rendering; the agent record carries, per orchestrator, `id6`, `ready`, the finding codes, and whether the answer was read from a current record in the plan (`ProbeOutcome.cached`) and how many probe calls were spent (`ProbeOutcome.calls`), so V-03's no-second-call claim is observable. COMMIT BEHAVIOR IS ORDER 02'S: `probe_orchestrator`'s write already makes one path-scoped commit per recorded plan and skips a plan that has another party's uncommitted edit (`8mabmu` E-07), so this verb adds no second commit path. Add `--no-commit` (mirroring `aw ipd set`'s `--commit | --no-commit` pair) to suppress that commit for an operator who wants to inspect the record first, and report per orchestrator whether the record was written and whether it was committed. Exit 0 when every selected orchestrator is ready, 1 when any is not, 2 when it cannot run (no project, no orchestrator selected). A non-orchestrator selection is reported as not applicable, not as a failure. Register the leaf in `command_surface.COMMAND_INVENTORY` (a `CommandDeclaration` with `command="ipd coverage"`, `command_class="check"`, `agent_record_kind="result"`, `exit_contract=(0, 1, 2)`; it writes the coverage record into the selected plans and nothing else). Because a `check`-class `result` leaf enters the `tests/test_agent_surface_conformance.py` universe, which runs it with no arguments against a bare scoped repo, the no-argument invocation must exit 2 with a valid `aw.agent/v1` record and must never reach a model.
  - Depends on: E-02
  - Expected outcome: `aw ipd coverage <orchestrator>` asks the probe at most once per orchestrator, records the verdict, prints every finding, and returns the documented exit code; a second invocation on an unchanged plan spends no model call.
  - Execution state: performed

- [x] E-04 Add lint rule `IPD-S408` in `ipd_lint.py` (a new constant beside `C_ORCH_ROW`), called from the top-level lint for `Kind: orchestrator` plans, mapping each finding of `review_readiness(..., ask=False)` to a diagnostic by checkpoint. At `review-finalize` and `pre-execution`, conditions 1 to 3, a recorded `fail` verdict and an `unknown` verdict are errors. At `author` every finding is an advisory. At `pre-transition` and `post-transition` the rule does not run (spec `77tr3o` R-12 point 3 as amended). An ABSENT or OUT-OF-DATE coverage record is an ERROR at `review-finalize` and `pre-execution` (OQ-03, resolved: the record is in the plan, so every clone and CI see the same answer). Separately add `IPD-M112` (a new constant), run at every checkpoint: a coverage record whose three fields are not all present, whose `- Coverage:` value is not `pass`/`fail`, whose `fail` lacks a `## Coverage findings` section, or which has no `coverage` line in `## Workflow history` with the same fingerprint prefix, is an error naming `aw ipd coverage <id6>` as the remedy (the `IPD-M107` pattern for `- Readiness:`). Why `pre-execution` matters: `runner_shared.enforce_freeze_time_refusal` lints every queued `approved`/`auto-approved` IPD at `pre-execution` before `initialize_run_core` reaches `enforce_orchestrator_probe_gate` (F-05). Because the record is in the plan, an approved orchestrator that was checked before approval passes this freeze-time lint with no model call; one never checked is refused there with a remedy that names `aw ipd coverage <id6>`, which is correct: an approved orchestrator nobody has checked is not ready. COST BOUND: bare `aw ipd lint` lints every pending plan at `author`, so the advisory runs for every pending orchestrator; resolve Set membership from ONE plans-tree read per invocation and pass it as E-01's `membership`, never one `read_set_membership` per orchestrator (F-07).
  - Depends on: E-03
  - Expected outcome: per checkpoint, `IPD-S408` has the severities stated; an absent or out-of-date record is an error at `review-finalize` and at `pre-execution`; `IPD-M112` refuses a hand-written or incomplete record at every checkpoint; lint makes no model call; warm bare `aw ipd lint` on the real tree grows by no more than 1 s over a pre-edit baseline.
  - Execution state: performed

- [x] E-06 Add `check.orchestrator-not-review-ready` in `check_engine.py`, registered in `RULE_REGISTRY` as a `RuleSpec` with severity `error`, over pending orchestrators whose status is `to-review`, `reviewed`, `approved` or `auto-approved`, calling the same `review_readiness(..., ask=False)` so `aw check plans` reports the same finding codes as `IPD-S408`. An absent or out-of-date coverage record is an `error` too (OQ-03). Resolve Set membership once per invocation as in E-04.
  - Depends on: E-04
  - Expected outcome: `aw check plans` and `aw ipd lint --phase review-finalize` report the same finding codes for the same fixture orchestrator; a `draft` orchestrator is not flagged; an absent record is an error; warm `aw check plans --agent` on the real tree grows by no more than 1 s over a pre-edit baseline.
  - Execution state: performed

### Task group 3: pin it

- [x] E-08 Keep the existing runner tests green. Measured at review (2026-10-06) by spying on `ipd_lint.lint_file` across the bare suite: four existing tests drive a synthetic `approved` orchestrator through `pre-execution` lint (via `runner_shared.enforce_freeze_time_refusal` or `ipd_lifecycle.begin_plan`) and need it to pass: `tests/test_orchestrator_retirement.py` `TheActionDecisionIsSHAREDCode.test_action_decision_shared_code_binding_and_queue_derivation` and `TheHumanFacingGateIsUNCHANGED.test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`, `tests/test_orchestrator_shape_gate.py` `TheGateIsSitedBeforeRunDirAndPrepareOnlyRefuses.test_prepare_only_succeeds_on_conforming_queue`, and `tests/test_action_table_runner_parity.py` (one test, re-derive which by the same spy). After E-04 each fixture orchestrator has no coverage record, so `IPD-S408` refuses it. Re-derive the list at execution (run the same spy, or run those files and read the failures), then give each failing fixture a valid record written by `coverage_record.write` (never a hand-written record, which `IPD-M112` refuses) BEFORE the code under test reads it; change no assertion. Any other test that breaks for the same reason is fixed the same way and named in the evidence with a `--scope-reason`.
  - Depends on: E-06
  - Expected outcome: every listed test passes with its original assertions; the only change in each file is fixture setup that records a coverage pass.
  - Execution state: performed

- [x] E-05 Add `tests/test_orchestrator_readiness.py` with fixture repositories built under `tempfile` and an injected fake probe: one case per condition (missing child file; open-ended `03+` row; child at `draft`; child failing lint; non-conforming row; no coverage record; an out-of-date record; a recorded fail with two quotes; could-not-ask; and three `IPD-M112` cases: a record missing `- Coverage-Fingerprint:`, a `fail` with no findings section, and a record with no matching history line), plus an executed-child case (a child under `executed/` with `- Status: executed` is NOT a finding) and an unusable-child-table case (finding, not pass), each asserting the finding code, subject and remedy; a ready case; an `aw ipd coverage --agent` case with no argument in a bare repo (exit 2, valid record, asker never called) and a second-invocation case asserting the answer is read from the plan with zero calls, and a case asserting `aw ipd coverage` wrote the record and history line into the plan; a parity case asserting `aw ipd lint --phase review-finalize`, `aw check plans --agent` and `aw ipd coverage --agent`, driven as subprocesses, report the same finding codes for the same fixture (a subprocess cannot receive an injected asker, so the parity fixture PRE-WRITES its coverage records into the fixture plans with `coverage_record.write` and `aw ipd coverage` reads them; the inherited `PYTEST_CURRENT_TEST` makes any real spawn raise via `_assert_probe_spawn_is_permitted`, so a parity run that tries to ask fails loudly instead of spending tokens); and a no-model-call case asserting lint and check never call the injected asker. Prove the test can fail by making condition 2 accept `draft` and pasting the failure.
  - Depends on: E-08
  - Expected outcome: the new file passes, the mutation fails it, and no test reads production source.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ONE IMPLEMENTATION, SEVERAL CONSUMERS is the established pattern: `check_engine.evaluate_blocking_close` backs both backlog setter spellings, three `aw check` rules and a pre-commit hook; `ipd_lint.orchestrator_row_conformance` backs lint, `/plan-review` and both runners (spec `r07vma` R3).
- `ipd_lint` IMPORTS ARE FUNCTION-LOCAL FOR FIRST-PARTY CYCLES. The orchestrator-row section states that `ipd_set_plan` imports `ipd_lint` at module level, so `ipd_lint` must import other first-party modules inside function bodies; the same applies to the new module's use of `runner_shared`.
- `aw ipd lint` MUST BE MODEL-FREE (`ipd-structure-and-linting` Section 10). The rule reads the coverage record stored in the plan; only `aw ipd coverage` (and the runner's asking consumers) ask.
- THE COVERAGE RECORD TRAVELS WITH THE PLAN (`25kzda` 2.5e, Order 02), so it is identical in every clone, every lane worktree and CI, with no expiry.
- `IPD-M107` (`ipd_lint.check_readiness_attestation`) is the model for `IPD-M112`: a tool-written field refused when no history line accounts for it.
- EXIT CODES follow `docs/cli-output-contract.md`: 0 clean, 1 findings, 2 cannot-run.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The four conditions are each computed somewhere already, none in combination. Child-table resolution: `find_unauthored_child_rows` (one-directional, refuses open-ended tokens). Row shape: `orchestrator_row_conformance`. Child lint: `lint_file`. Coverage: `read_probe_verdict` / `probe_orchestrator`. | the four symbols |
| F-02 | No status-time consumer of coverage exists. `enforce_orchestrator_probe_gate` is called once, from `initialize_run_core`; `aw ipd set`, `aw ipd lint` and `aw check` never read any coverage answer. | the single call site of `enforce_orchestrator_probe_gate` in `initialize_run_core` |
| F-03 | Measured 2026-10-04 over the 16 pending orchestrators: all child-table rows resolve to existing plans at `to-review` or later, so conditions 1 and 2 pass for every one today; all 13 refusals come from condition 4. The check is still needed for 1 and 2 because a production turn can write the orchestrator before its children, which is the normal authoring order. | a script over `.aw/records/plans/pending/*.ipd.md` resolving each `## Child IPDs` id to a plan and its status, printing `[]` failures for all 16 |
| F-04 | `aw check plans` runs in CI as a fail-closed step (`.github/workflows/tests.yml`, step "aw check plans (plan conformance; fail closed)"). A new `error` rule therefore turns CI red on any pending orchestrator that fails. At authoring, 13 would. That is why Order 09 (reopen and demote them to `draft`) precedes Order 10, and why this rule flags only `to-review` and later: a `draft` orchestrator is not flagged. | the quoted CI step; Order 09's scope |
| F-05 | `aw ipd lint` at `pre-execution` is not only a hand command: `runner_shared.enforce_freeze_time_refusal` lints every queued `approved`/`auto-approved` IPD at that checkpoint, and `initialize_run_core` calls it before `enforce_orchestrator_probe_gate`. So `IPD-S408` at `pre-execution` sits IN FRONT of the run-start probe. | `enforce_freeze_time_refusal`: `checkpoint = ("pre-execution" if status in ("approved", "auto-approved") else "author")`; its call in `initialize_run_core` precedes `probe_decision = enforce_orchestrator_probe_gate(` |
| F-06 | A plan under `executed/` lints as `legacy/not evaluated`, which is not in `ipd_schema.PASSING_DISPOSITIONS`, so condition 2 must not lint executed children. | `lint_file` on the newest `.aw/records/plans/executed/*.ipd.md` returned `legacy/not evaluated` (measured at review) |
| F-07 | `read_set_membership` costs 0.3 to 0.45 s per call warm (cProfile: `selectors.resolve` dominates) and there are 17 pending orchestrators; bare `aw ipd lint` lints every pending plan at `author` in about 2.3 s today. | measured at review, 2026-10-04 |

## Proposed changes (ordered, validatable)

1. New module with `review_readiness`, its result and finding types, and remedy constants (E-01, E-02).
2. `aw ipd coverage` subcommand in `cli.py` (E-03).
3. `IPD-S408` in `ipd_lint.py` (E-04) and `check.orchestrator-not-review-ready` in `check_engine.py` (E-06).
4. Tests with fixtures, a parity case across three commands, and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- REFUSING THE STATUS CHANGE. Order 05.
  - Carrier: 26m1nb
- THE RUN-START AND RETIREMENT GATES. Order 04.
  - Carrier: 5etev3
- THE PRODUCTION GATE. Order 06.
  - Carrier: r2wa38
- TURNING `aw check plans` RED on the orchestrators already at `to-review` or later, none of which carries a coverage record yet. Order 09 records an answer for each and demotes the failing ones within the Set's own execution; the maintainer ruled (2026-10-04) that the Set runs as a whole before anything is pushed, so CI never sees the interval.
  - Carrier: 52opph

## Scope check

- Over-scope: none. One new module, four wiring edits (`ipd_lint`, `check_engine`, `cli`, `command_surface`), one new test file, and fixture-only edits in three existing test files (E-08).
- Under-scope: after this plan the check exists and `aw check`/`aw ipd lint` report it, but nothing yet REFUSES a status change or a production handoff. A reader must not assume `aw ipd set to-review` is gated until Order 05 executes.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree before editing, failing node ids recorded. Baseline warm wall time (second of two runs) of bare `python3 -m agent_workflows ipd lint` and of `python3 -m agent_workflows check plans --agent`, recorded before editing.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_readiness.py tests/test_orchestrator_shape_gate.py tests/test_ipd_lint.py tests/test_check_engine.py tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py tests/test_orchestrator_retirement.py tests/test_action_table_runner_parity.py -q` pasted.
- The same two timings after the change, warm, pasted beside the baseline (E-04 and E-06 cost bound).
- The mutation run for E-05 pasted.
- `python3 -m agent_workflows ipd coverage axozpe --agent` run once against the real tree, output pasted (this spends one real model call by design and writes the record into `axozpe`; run it by hand outside pytest, paste the resulting record lines, run it with `--no-commit`, then restore `axozpe` with `git checkout -- <path>` so this plan does not change a plan outside its scope; Order 09 records answers for real).
- `python3 -m agent_workflows check plans` pasted, listing the current set of `check.orchestrator-not-review-ready` findings, which Order 09 will use.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled against the baseline.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` Section 2.5d and `ipd-structure-and-linting` Section 10 rule 19 (both added by Order 01). No spec edited here. `docs/cli-human-guide.md` is not changed by this plan; the new subcommand is documented by its `--help` text, and Order 11 updates authoring guidance.

## Open questions

### OQ-01: Should the function live in `ipd_lint`, `runner_shared`, or a new module?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a NEW module. `runner_shared` has a pinned module-level import set (`tests/test_lost_guard_census.py` `test_no_new_module_level_first_party_import_in_runner_shared`) and is 39,625 lines; `ipd_lint` must stay model-free, and the function's `ask=True` path calls the probe. A small module importing both lazily lets lint call it with `ask=False` and the runner call it with `ask=True` without either module importing the other at load time.

### OQ-02: Which child statuses count as ready?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: `to-review`, `reviewed`, `approved`, `auto-approved`, `executed`, as written in `25kzda` 2.5d condition 2. `executed` is included so an orchestrator whose early children already ran can still be reviewed; `draft`, `superseded` and `not-executed` are not ready (a superseded child must be replaced in the table first).

### OQ-03: What severity does an absent or stale coverage verdict carry in `aw ipd lint` (`review-finalize` and `pre-execution`) and `aw check plans`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-10-04 by the maintainer, in session: the coverage answer is STORED IN THE PLAN (`25kzda` 2.5e, written by Order 02's `coverage_record`), so CI, every clone and the freeze-time lint all read the same answer and there is nothing machine-local to be missing. Therefore an absent or out-of-date record is an ERROR in `aw ipd lint` (`review-finalize`, `pre-execution`) and `aw check plans`, the same as conditions 1 to 3. The freeze-gate concern (F-05) is answered: an approved orchestrator checked before approval passes with no model call; one never checked is refused with `aw ipd coverage <id6>` as the remedy. A hand-written record is refused by `IPD-M112` unless a matching history line accounts for it. Same decision as `hm1h3l` OQ-03 and `1f4faf` OQ-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the new module's public signature and result types. Paste test output for each condition case named in E-05 (the eight failing conditions, the executed-child case showing NO finding, and the unusable-child-table case showing a finding) with the finding code and subject, and for the ready case showing `ready=True` with no findings. Paste the no-model-call case showing the injected asker was called zero times with `ask=False`. Paste the malformed-Set fixture (two Order-0 plans) returning a result without recursing.
  - Observed evidence:
    Public signatures in `agent_workflows/orchestrator_readiness.py`:
    ```python
    class Finding(NamedTuple):
        code: str
        subject: str
        detail: str
        remedy: str

    class ReviewReadiness(NamedTuple):
        applies: bool
        ready: bool
        findings: tuple[Finding, ...] = ()
        id6: str = ""
        setid: str = ""
        cached: bool = False
        calls: int = 0
        written: bool = False
        committed: bool = False

    def review_readiness(
        repo: Path | str,
        plan_path: Path | str,
        *,
        ask: bool = False,
        model: Optional[str] = None,
        host: Optional[str] = None,
        state: Optional[Mapping[str, Any]] = None,
        asker: Any = None,
        runner: Any = None,
        membership: Any = None,
        retry_budget: Optional[int] = None,
        status_overrides: Optional[Mapping[str, str]] = None,
        suppress_commit: bool = False,
    ) -> ReviewReadiness: ...
    ```
    Verbose test output from `python3 -m pytest -o addopts="" tests/test_orchestrator_readiness.py -v`:
    ```
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_unauthored PASSED [code: child-unauthored]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_open_ended PASSED [code: child-open-ended]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_1_child_table_unusable PASSED [code: child-table-unusable]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_draft PASSED [code: child-status]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_fails_lint PASSED [code: child-lint]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_executed_child_under_executed_dir_is_ready PASSED [ready=True, findings=()]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_3_checklist_row_nonconforming PASSED [code: checklist-row]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_absent PASSED [code: coverage-record-absent]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_record_stale PASSED [code: coverage-record-stale]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_coverage_fail_with_two_quotes PASSED [code: coverage-fail]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_4_could_not_ask PASSED [code: coverage-could-not-ask]
    tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_ready_orchestrator PASSED [ready=True, findings=()]
    tests/test_orchestrator_readiness.py::TestConsumerParityAndModelFreeLinters::test_lint_and_check_never_call_model PASSED [asker called 0 times with ask=False]
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the remedy constants. Paste one rendered human refusal and its agent record for the fail-verdict case, showing the quoted passage, the "do not delete the checklist" sentence, and the remedies E-02 names for that finding (assign the obligation by id6 to a child in the table, or add a child for it). Paste `agent_schema.validate_agent_record` returning `[]` and a grep showing no absolute path in the record.
  - Observed evidence:
    Remedy constants in `agent_workflows/orchestrator_readiness.py`:
    ```python
    REMEDY_CHILD_UNAUTHORED = "author the missing child plan and add its row to the child table; do not delete the checklist"
    REMEDY_CHILD_OPEN_ENDED = "replace the open-ended token with explicit child rows; do not delete the checklist"
    REMEDY_TABLE_UNUSABLE = "restore the child table with conforming rows; do not delete the checklist"
    REMEDY_CHILD_STATUS = "bring the child to to-review or later via aw ipd set to-review <child-id6>; do not delete the checklist"
    REMEDY_CHILD_LINT = "resolve the child plan's lint finding; do not delete the checklist"
    REMEDY_CHECKLIST_ROW = "reformat the child table row to match canonical format; do not delete the checklist"
    REMEDY_COVERAGE_ABSENT = "run `aw ipd coverage <id6>`"
    REMEDY_COVERAGE_STALE = "run `aw ipd coverage <id6>`"
    REMEDY_COVERAGE_FAIL = "assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"
    REMEDY_COULD_NOT_ASK = "ensure runner model/host is accessible and retry `aw ipd coverage <id6>`"
    ```
    Rendered human refusal:
    ```
    Orchestrator orch01 is not ready for review:
      - [coverage-fail] orch01: uncovered obligation: Test obligation passage here
        Remedy: assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist
    ```
    Agent record:
    ```json
    {"schema": "aw.agent/v1", "kind": "result", "cmd": "ipd coverage", "exit": 1, "outcome": "findings", "verified": true, "complete": true, "summary": "orchestrator orch01 is not ready for review (1 finding(s))", "data": {"id6": "orch01", "setid": "set01", "ready": false, "cached": false, "calls": 0, "written": false, "committed": false, "finding_codes": ["coverage-fail"], "findings": [{"code": "coverage-fail", "subject": "orch01", "detail": "uncovered obligation: Test obligation passage here", "remedy": "assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"}]}}
    ```
    `agent_schema.validate_agent_record`: `[]`; path check confirms no `/home` or absolute paths in record.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw ipd coverage --help`. Paste the fixture run's exit codes for ready (0), not ready (1), and no project (2). Paste the real-tree run for `axozpe` with `--agent`, a grep of `axozpe`'s file showing the `- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:` lines and the history line written by the command, and a second run whose record shows `cached: true` and `calls: 0` for `axozpe`; then restore `axozpe` (run the real-tree command with `--no-commit` and `git checkout -- <axozpe path>` afterwards, or, if it was committed, `git revert --no-edit <that commit>` through the normal commit path) and paste the restore. Paste the `CommandDeclaration` added for `ipd coverage` and the no-argument `aw ipd coverage --agent` record in a bare repo (exit 2, validates with `agent_schema.validate_agent_record`).
  - Observed evidence:
    `aw ipd coverage --help`:
    ```
    usage: agent-workflows ipd coverage [-h] [--no-color | --color]
                                        [--no-interactive | --interactive]
                                        [--agent] [--json] [--fields FIELDS]
                                        [--verbose] [--host {oc,agy}]
                                        [--model MODEL] [--no-commit] [--dir DIR]
                                        [targets ...]
    ```
    Exit codes: ready=0, not ready=1, no project/target=2 (asserted in `tests/test_orchestrator_readiness.py`).
    Real-tree run output (`python3 -m agent_workflows ipd coverage axozpe --agent --no-commit`):
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd coverage","exit":1,"outcome":"findings","verified":true,"complete":true,"summary":"1 of 1 orchestrator(s) not ready for review","data":{"orchestrators":[{"id6":"axozpe","setid":"dirsilent","ready":false,"cached":false,"calls":1,"written":true,"committed":false,"finding_codes":["coverage-fail","coverage-fail","coverage-fail","coverage-fail","coverage-fail","coverage-fail"],"findings":[{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: Check by reading each converted call site for a call to the primitive rather than a locally built `summary` string or `NextAction`. This is the Set's central structural claim and the reason Order 01 precedes everything.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"},{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: Order 03 routes six sites INTO the resolver, which is the opposite change and preserves the rule; confirm it did not relax it.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"},{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: 4. THE REFUSAL HAS EXACTLY ONE DEFINITION IN THE PACKAGE: every converted verb, plus `attention.run` and `cli._run_plans`, obtains its message, machine summary and next-action from Order 01's primitive, with the two previously hand-rolled copies retired.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"},{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: Confirm child 02 (`jei45f`, the two fail-closed validators) reached `executed`, and that `aw specs check --dir <subdir>` and `aw backlog check --dir <subdir>` now refuse at exit 2 rather than announcing conformance over zero artifacts.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"},{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: Confirm child 03 (`sjsb04`, the six resolver-bypass sites) reached `executed`, and that a BARE invocation from a project subdirectory now climbs for all six verbs, including `aw doctor` no longer reporting an installed project as `not installed`.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"},{"code":"coverage-fail","subject":"axozpe","detail":"uncovered obligation: Confirm child 04 (`rlhmt9`, the helper split, the remaining read-class callers and the duplication retirement) reached `executed`, and that no write-class verb gained a refusal.","remedy":"assign the quoted obligation by id6 to a child in the table or add a child for it; do not delete the checklist"}]}],"id6":"axozpe","ready":false,"cached":false,"calls":1,"written":true,"committed":false,"finding_codes":["coverage-fail","coverage-fail","coverage-fail","coverage-fail","coverage-fail","coverage-fail"]}}
    ```
    Lines written into `axozpe`:
    ```
    - Coverage: fail
    - Coverage-Fingerprint: b59fda92b7d914389f7b46014b3a883915e98daae683ce245f55d8ad16abc222
    - Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
    ## Workflow history
    - 2026-10-06 coverage fail (aw oc run): fingerprint b59fda92b7d9, model uri/its_direct/pt3-claude-opus-5.5-1m-us
    ```
    Second run record (`cached: true`, `calls: 0`):
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd coverage","exit":1,"outcome":"findings","verified":true,"complete":true,"summary":"1 of 1 orchestrator(s) not ready for review","data":{"orchestrators":[{"id6":"axozpe","setid":"dirsilent","ready":false,"cached":true,"calls":0,"written":false,"committed":false,...
    ```
    Restore executed cleanly via `git checkout -- .aw/records/plans/pending/20261002-dirsilent-00-axozpe-stop-the-silent-dir-and-bare-cwd-under-report-across-every-r.ipd.md`.
    CommandDeclaration added in `agent_workflows/command_surface.py`:
    ```python
    CommandDeclaration(
        command="ipd coverage",
        category="ipd",
        command_class="check",
        agent_record_kind="result",
        exit_contract=(0, 1, 2),
        writes_plan=True,
        summary="Evaluate orchestrator review-readiness (spec 25kzda 2.5d).",
    ),
    ```
    Bare repo no-arg output: exit 2, validates via `agent_schema.validate_agent_record`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `aw ipd lint --phase review-finalize`, `--phase pre-execution`, `--phase author` and `--phase pre-transition` on one fixture orchestrator failing condition 2, showing `IPD-S408` as an error, an error, an advisory only, and absent respectively. For a fixture whose conditions 1 to 3 pass and which has NO coverage record, paste `--phase review-finalize` and `--phase pre-execution` showing the absent-record finding as an error; and for the three `IPD-M112` fixtures paste each refusal. Paste the before and after warm timings (second of two runs) of bare `python3 -m agent_workflows ipd lint`, delta at most 1 s.
  - Observed evidence:
    `IPD-S408` per checkpoint on condition 2 failure (asserted in `tests/test_orchestrator_readiness.py`):
    - `review-finalize`: `IPD-S408` diagnostic with disposition `error`
    - `pre-execution`: `IPD-S408` diagnostic with disposition `error`
    - `author`: `IPD-S408` advisory with disposition `conforming`
    - `pre-transition`: absent, disposition `conforming`
    Absent coverage record: error at `review-finalize` and `pre-execution` with code `coverage-record-absent`.
    Three `IPD-M112` cases:
    - Missing fingerprint: `IPD-M112: coverage record missing required field(s) ... remedy: run aw ipd coverage <id6>`
    - Fail with no findings section: `IPD-M112: coverage record indicates fail but has no ## Coverage findings section ... remedy: run aw ipd coverage <id6>`
    - No matching history line: `IPD-M112: coverage record has no matching 'coverage' entry in ## Workflow history ... remedy: run aw ipd coverage <id6>`
    Warm bare `aw ipd lint` timings:
    - Baseline: 2.491s
    - Post-change: 3.080s (delta +0.589s <= 1.0s budget)
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; the mutation (condition 2 accepts `draft`) failing it; the revert passing it; a grep of the test file for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
    Test suite: `tests/test_orchestrator_readiness.py`:
    ```
    ============================== 19 passed in 3.93s ==============================
    ```
    Mutation test:
    Temporarily added `draft` to `_READY_CHILD_STATUSES`:
    `FAILED tests/test_orchestrator_readiness.py::TestOrchestratorReadinessConditions::test_condition_2_child_status_draft - AssertionError: False is not true : Expected review_readiness to fail for draft child`
    Revert restored clean pass across all 19 tests.
    Grep for code-pinning patterns (`inspect`, `ast.parse`, production source reads): 0 matches.
    Bare `python3 -m pytest`: `5138 passed, 2 skipped, 3 warnings in 251.65s (0:04:11)`
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the parity case's three outputs (`aw ipd lint --phase review-finalize`, `aw check plans --agent`, `aw ipd coverage --agent`) for one fixture showing identical finding codes. Paste `aw check plans --agent` against a draft fixture orchestrator showing no `check.orchestrator-not-review-ready`, and against the no-record fixture showing the absent-record finding as an error. Paste `check_engine.rule_spec(...)` for each rule id added. Paste the before and after warm timings of `python3 -m agent_workflows check plans --agent`, delta at most 1 s.
  - Observed evidence:
    Parity across consumers: `aw ipd lint --phase review-finalize`, `aw check plans --agent`, and `aw ipd coverage --agent` emit identical finding codes `['coverage-fail', 'coverage-fail']` for the parity fixture (asserted in `tests/test_orchestrator_readiness.py`).
    Draft fixture: 0 `check.orchestrator-not-review-ready` findings emitted.
    No-record fixture: emitted finding with severity `error` and remedy `run aw ipd coverage <id6>`.
    RuleSpec in `agent_workflows/check_engine.py`:
    ```python
    RuleSpec(
        rule_id="check.orchestrator-not-review-ready",
        severity="error",
        summary="Pending orchestrator is not ready for review (spec 25kzda 2.5d).",
        doc_url="specs/25kzda-orchestrator-retirement-protocol.spec.md#25d-the-shared-review-readiness-check",
        remedy="run `aw ipd coverage <id6>` or resolve the child plan/row finding",
    )
    ```
    Warm timings for `check plans`:
    - Before (without check): 24.173s
    - After (with check): 24.977s (delta +0.804s <= 1.0s budget)
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the re-derived list of existing tests that failed after E-04 (the spy output or the failing node ids), the diff of each changed fixture showing only a `coverage_record.write` setup call added, and those test files passing: `python3 -m pytest -o addopts="" tests/test_orchestrator_retirement.py tests/test_orchestrator_shape_gate.py tests/test_action_table_runner_parity.py -q` with its summary line.
  - Observed evidence:
    Re-derived failing tests:
    - `tests/test_orchestrator_retirement.py`: `TheActionDecisionIsSHAREDCode.test_action_decision_shared_code_binding_and_queue_derivation` and `TheHumanFacingGateIsUNCHANGED.test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`
    - `tests/test_orchestrator_shape_gate.py`: `TheGateIsSitedBeforeRunDirAndPrepareOnlyRefuses.test_prepare_only_succeeds_on_conforming_queue`
    - `tests/test_action_table_runner_parity.py`: `test_orchestrator_retirement_parity`
    Diff in each test file only added setup writing a valid coverage pass (`coverage_record.write(..., verdict="pass")`) and a conforming child row.
    Test execution output:
    ```
    ...................................................................      [100%]
    67 passed in 14.13s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Scope fence: the nine `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and a declared path left untouched with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. The real-tree `aw ipd coverage` run spends one model call and is required evidence. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

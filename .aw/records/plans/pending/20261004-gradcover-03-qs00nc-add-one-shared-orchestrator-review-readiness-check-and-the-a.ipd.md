# IPD: Add one shared orchestrator review-readiness check and the aw ipd coverage verb

- Date: 2026-10-04
- Kind: child
- Concern: Nothing in the toolkit answers "is this orchestrator plan ready for review?" as one question. The pieces exist in different places and are never combined: child-table resolution (`runner_shared.find_unauthored_child_rows`, `runner_shared.read_set_membership`), row conformance (`ipd_lint.orchestrator_row_conformance`, `IPD-S407`), per-child lint (`ipd_lint.lint_file`), and the coverage verdict (`runner_shared.read_probe_verdict` / `probe_orchestrator`). The only consumer of the coverage verdict is the run-start gate, so an orchestrator reaches `to-review` with no check at all. Spec `25kzda` Section 2.5d (added by Order 01, `hm1h3l`) defines the four conditions and requires ONE function shared by every consumer, a model-free lint rule `IPD-S408`, an `aw check plans` rule, and an `aw ipd coverage` command that asks the probe once and records the answer.
- Scope: Add the shared function and its result type, the `aw ipd coverage` subcommand, the `IPD-S408` lint rule, and the `check.orchestrator-not-review-ready` check rule. IN: a new module `agent_workflows/orchestrator_readiness.py` holding `review_readiness(repo, plan_path, *, ask=False, ...)` and its result; wiring in `ipd_lint.py` (rule at `review-finalize`/`pre-execution`, advisory at `author`), `check_engine.py` (rule over pending orchestrators), `cli.py` (subcommand), and `command_surface.py` (the subcommand's `CommandDeclaration`, required by `tests/test_command_surface_declarations.py` `test_zero_undeclared_parser_leaves`); one new test file. OUT: any status setter (Order 05); any runner gate or retirement change (Order 04); production verification (Order 06); prompt or template text (Order 11); the probe's prompt or parser (Order 02, already executed).
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_orchestrator_readiness.py
- Item-Dependencies: executed:8mabmu
- Status: reviewed
- Readiness: no-go
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qs00nc

## Workflow history
- 2026-10-04 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007 (PR-001 open, blocking OQ-03)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 to PR-007. Fixed: executed children are not linted (PR-002); recursion guard for a malformed Set (PR-003); `aw ipd coverage` registered in `command_surface` and its no-arg conformance path specified, Scope-Paths widened (PR-004); probe call shape and cache-observable record specified (PR-005); one plans-tree read per sweep with a 1 s budget (PR-006); parity fixture pre-records verdicts, unusable-table case, gate contract (PR-007). OPEN, blocking: OQ-03 / PR-001 (absent-verdict severity, same decision as `hm1h3l` OQ-03, plus the newly found freeze-gate ordering).
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `hm1h3l` (finding PR-001): the `aw ipd lint` MUST-check list and its "MUST make no model calls" sentence are in `ipd-structure-and-linting` Section 10 ("Deterministic linter contract"), not Section 9; three citations corrected. The same review widened the asking consumers of `25kzda` 2.5d to include the post-review and retirement-time checks; the shared function's `ask=True` path already serves them.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 03 of Set `gradcover`. Implements spec `25kzda` Section 2.5d and `ipd-structure-and-linting` Section 10 rule 19 as amended by Order 01. Every later gate in the Set calls the function this plan adds.

## Goal

Provide one function that returns every reason an orchestrator plan is not ready for review, with a precise remedy per reason, plus a command that establishes the coverage verdict on demand, so that the setter, the linter, `aw check`, the production action and the runner can all ask the same question and get the same answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the function

- [ ] E-01 Add `agent_workflows/orchestrator_readiness.py` with `review_readiness(repo, plan_path, *, ask=False, model=None, host=None, state=None, asker=None, runner=None)` returning a `ReviewReadiness` result: `applies` (False for a non-orchestrator), `ready`, and an ordered tuple of `Finding(code, subject, detail, remedy)` covering exactly the four conditions of `25kzda` 2.5d. Condition 1 uses `read_set_membership` plus `find_unauthored_child_rows` (unresolvable and open-ended rows are findings; a `parsed=False` result, meaning the child table is absent or unusable, is itself a finding and never a pass). The function accepts an optional precomputed `membership` so a sweeping caller resolves each Set once (see E-04's cost bound). Condition 2 reads each child's `- Status:` (from `SetMember.status`) and, for a child NOT in a terminal directory (`run_selection_policy.is_in_terminal_directory`), runs `ipd_lint.lint_file(..., checkpoint="author")`; a child below `to-review` or whose disposition is not passing is a finding naming it. A child under `executed/` with `- Status: executed` is ready WITHOUT being linted, because `lint_file` reports every terminal-directory plan as `legacy/not evaluated`, which is not a passing disposition (measured: the newest file in `.aw/records/plans/executed/` lints `legacy/not evaluated`), so linting it would refuse every orchestrator whose early children already ran, contradicting OQ-02. RECURSION GUARD: the children are linted with `IPD-S408` suppressed (an internal keyword on `lint_file`/`lint_text`, or a module-level re-entrancy flag in the new module), because `read_set_membership` deliberately files a second Order-0 plan of a malformed Set as a CHILD, and linting that child would call `review_readiness` again on the same Set without end. Condition 3 calls `ipd_lint.orchestrator_row_conformance`. Condition 4 calls `read_probe_verdict(repo, probe_cache_digest(text), model=model)` on the plan's current text (with `model=None` from the model-free consumers, so the time bound alone decides, per `read_probe_verdict`'s documented `model=None` rule) and, ONLY when `ask=True`, calls `probe_orchestrator` on a miss (recording the verdict); an absent or stale verdict with `ask=False` is a finding whose remedy is `aw ipd coverage <id6>`; a fail verdict is one finding per stored quote; could-not-ask is a finding naming the retry command. All runner_shared imports are function-local.
  - Depends on: none
  - Expected outcome: the function returns `ready=True` only when all four conditions hold, and otherwise returns one finding per failing child, row or quoted passage, each with a remedy command or edit; it makes no model call unless `ask=True`.
  - Execution state: pending

- [ ] E-02 Write the remedy texts as data in the new module (one constant per finding code) so every consumer prints the same words, and make them satisfy spec `r07vma` R7: state the invariant, forbid deleting the checklist, and name the legitimate remedies (author the missing child and its row; bring the child to `to-review` with `aw ipd set to-review <child-id6>`; fix the child's named lint finding; assign the quoted obligation by id6 to a child in the table or add a child for it; run `aw ipd coverage <id6>`). Provide `render_human(result)` and `render_agent(result)` producing the human lines and an `aw.agent/v1` record (path-free, validated by `agent_schema.validate_agent_record`).
  - Depends on: E-01
  - Expected outcome: every finding code has one remedy constant; the agent record validates with no findings and carries no absolute path.
  - Execution state: pending

### Task group 2: the consumers this plan owns

- [ ] E-03 Add the `aw ipd coverage <id6|setid|path>...` subcommand: for each orchestrator plan selected, call `review_readiness(..., ask=True)` using the same host and model resolution `aw oc run` would (the existing `runner_profiles.resolve` path, defaulting to the opencode host). `probe_orchestrator` takes a run `state` and reads `state["options"]` (`model`, `variant`, `agent`, `opencode`/`agy` binary, per `probe_argv`), a `ProbeTarget(id6, position, setid, path, text)`, and a required `retry_budget`; so compose `{"options": {...}}` from the resolved launch, build the target from the plan file, and pass `resolve_retry_budget(None, repo=repo)`. Add `--host {oc,agy}` and `--model` overrides. Print the human or `--agent` rendering; the agent record carries, per orchestrator, `id6`, `ready`, the finding codes, and whether the verdict was served from the cache (`ProbeOutcome.cached`) and how many probe calls were spent (`ProbeOutcome.calls`), so V-03's cache claim is observable. Exit 0 when every selected orchestrator is ready, 1 when any is not, 2 when it cannot run (no project, no orchestrator selected). A non-orchestrator selection is reported as not applicable, not as a failure. Register the leaf in `command_surface.COMMAND_INVENTORY` (a `CommandDeclaration` with `command="ipd coverage"`, `command_class="check"`, `agent_record_kind="result"`, `exit_contract=(0, 1, 2)`; it writes only the gitignored verdict store, as `ipd begin` writes only a local receipt). Because a `check`-class `result` leaf enters the `tests/test_agent_surface_conformance.py` universe, which runs it with no arguments against a bare scoped repo, the no-argument invocation must exit 2 with a valid `aw.agent/v1` record and must never reach a model.
  - Depends on: E-02
  - Expected outcome: `aw ipd coverage <orchestrator>` asks the probe at most once per orchestrator, records the verdict, prints every finding, and returns the documented exit code; a second invocation on an unchanged plan spends no model call.
  - Execution state: pending

- [ ] E-04 Add lint rule `IPD-S408` in `ipd_lint.py` (a new constant beside `C_ORCH_ROW`), called from the top-level lint for `Kind: orchestrator` plans, mapping each finding of `review_readiness(..., ask=False)` to a diagnostic by checkpoint. At `review-finalize` and `pre-execution`, conditions 1 to 3, a recorded `fail` verdict and an `unknown` verdict are errors. At `author` every finding is an advisory. At `pre-transition` and `post-transition` the rule does not run (spec `77tr3o` R-12 point 3 as amended). An ABSENT OR STALE verdict takes the severity OQ-03 records, which must agree with the executed text of spec `25kzda` 2.5d and `ipd-structure-and-linting` Section 10 rule 19 (`hm1h3l` OQ-03); if they disagree, STOP and report. Why `pre-execution` matters: `runner_shared.enforce_freeze_time_refusal` lints every queued `approved`/`auto-approved` IPD at `pre-execution` before `initialize_run_core` reaches `enforce_orchestrator_probe_gate` (F-05). COST BOUND: bare `aw ipd lint` lints every pending plan at `author`, so the advisory runs for every pending orchestrator; resolve Set membership from ONE plans-tree read per invocation and pass it as E-01's `membership`, never one `read_set_membership` per orchestrator (F-07).
  - Depends on: E-03
  - Expected outcome: per checkpoint, `IPD-S408` has the severities stated; an absent verdict has exactly OQ-03's severity at `review-finalize` and at `pre-execution`; lint makes no model call; warm bare `aw ipd lint` on the real tree grows by no more than 1 s over a pre-edit baseline.
  - Execution state: pending

- [ ] E-06 Add `check.orchestrator-not-review-ready` in `check_engine.py`, registered in `RULE_REGISTRY` as a `RuleSpec` with severity `error`, over pending orchestrators whose status is `to-review`, `reviewed`, `approved` or `auto-approved`, calling the same `review_readiness(..., ask=False)` so `aw check plans` reports the same finding codes as `IPD-S408`. An absent or stale verdict is emitted under OQ-03's recorded severity (as a separate rule id registered at that severity if it differs from `error`, since `RuleSpec` severity is per rule). Resolve Set membership once per invocation as in E-04.
  - Depends on: E-04
  - Expected outcome: `aw check plans` and `aw ipd lint --phase review-finalize` report the same finding codes for the same fixture orchestrator; a `draft` orchestrator is not flagged; an absent verdict carries OQ-03's severity; warm `aw check plans --agent` on the real tree grows by no more than 1 s over a pre-edit baseline.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_orchestrator_readiness.py` with fixture repositories built under `tempfile` and an injected fake probe: one case per condition (missing child file; open-ended `03+` row; child at `draft`; child failing lint; non-conforming row; no recorded verdict; recorded fail verdict with two quotes; could-not-ask), plus an executed-child case (a child under `executed/` with `- Status: executed` is NOT a finding) and an unusable-child-table case (finding, not pass), each asserting the finding code, subject and remedy; a ready case; an `aw ipd coverage --agent` case with no argument in a bare repo (exit 2, valid record, asker never called) and a second-invocation case asserting the record reports a cache hit with zero calls; a parity case asserting `aw ipd lint --phase review-finalize`, `aw check plans --agent` and `aw ipd coverage --agent`, driven as subprocesses, report the same finding codes for the same fixture (a subprocess cannot receive an injected asker, so the parity fixture PRE-RECORDS its verdicts with `runner_shared.record_probe_verdict` into the fixture's own store and `aw ipd coverage` serves them from the cache; the inherited `PYTEST_CURRENT_TEST` makes any real spawn raise via `_assert_probe_spawn_is_permitted`, so a parity run that tries to ask fails loudly instead of spending tokens); and a no-model-call case asserting lint and check never call the injected asker. Prove the test can fail by making condition 2 accept `draft` and pasting the failure.
  - Depends on: E-06
  - Expected outcome: the new file passes, the mutation fails it, and no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE IMPLEMENTATION, SEVERAL CONSUMERS is the established pattern: `check_engine.evaluate_blocking_close` backs both backlog setter spellings, three `aw check` rules and a pre-commit hook; `ipd_lint.orchestrator_row_conformance` backs lint, `/plan-review` and both runners (spec `r07vma` R3).
- `ipd_lint` IMPORTS ARE FUNCTION-LOCAL FOR FIRST-PARTY CYCLES. The orchestrator-row section states that `ipd_set_plan` imports `ipd_lint` at module level, so `ipd_lint` must import other first-party modules inside function bodies; the same applies to the new module's use of `runner_shared`.
- `aw ipd lint` MUST BE MODEL-FREE (`ipd-structure-and-linting` Section 10). The rule reads the verdict store; only `aw ipd coverage` asks.
- THE VERDICT STORE IS SHARED ACROSS WORKTREES through `ipd_lifecycle.checkout_control_root`, so a verdict recorded in a lane is visible to the driver and vice versa (`probe_verdict_store_path` docstring).
- EXIT CODES follow `docs/cli-output-contract.md`: 0 clean, 1 findings, 2 cannot-run.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The four conditions are each computed somewhere already, none in combination. Child-table resolution: `find_unauthored_child_rows` (one-directional, refuses open-ended tokens). Row shape: `orchestrator_row_conformance`. Child lint: `lint_file`. Coverage: `read_probe_verdict` / `probe_orchestrator`. | the four symbols |
| F-02 | No status-time consumer of coverage exists. `enforce_orchestrator_probe_gate` is called once, from `initialize_run_core`; `aw ipd set`, `aw ipd lint` and `aw check` never read the verdict store. | the single call site of `enforce_orchestrator_probe_gate` in `initialize_run_core` |
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
- TURNING `aw check plans` RED IN CI on the orchestrators already at `to-review` or later whose conditions 1 to 3 or recorded verdict fail. Order 09 demotes them within the Set's own execution. The PERMANENT red that an absent verdict would cause in CI (no verdict store there) is not deferred: it is OQ-03 below.
  - Carrier: 52opph

## Scope check

- Over-scope: none. One new module, four wiring edits (`ipd_lint`, `check_engine`, `cli`, `command_surface`), one test file.
- Under-scope: after this plan the check exists and `aw check`/`aw ipd lint` report it, but nothing yet REFUSES a status change or a production handoff. A reader must not assume `aw ipd set to-review` is gated until Order 05 executes.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree before editing, failing node ids recorded. Baseline warm wall time (second of two runs) of bare `python3 -m agent_workflows ipd lint` and of `python3 -m agent_workflows check plans --agent`, recorded before editing.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_readiness.py tests/test_orchestrator_shape_gate.py tests/test_ipd_lint.py tests/test_check_engine.py tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py -q` pasted.
- The same two timings after the change, warm, pasted beside the baseline (E-04 and E-06 cost bound).
- The mutation run for E-05 pasted.
- `python3 -m agent_workflows ipd coverage axozpe --agent` run once against the real tree, output pasted (this spends one real model call by design and records a verdict; it must be run by hand outside pytest).
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

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Context: this is the SAME decision as `hm1h3l` OQ-03 and `1f4faf` OQ-03 (finding PR-006 in both); answer it once and record it in all three. This plan is where the answer becomes code. The verdict store is gitignored and machine-local (`runner_shared.probe_verdict_store_path`, under `.aw/state/`) and expires after `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`, so CI and every fresh clone have NO verdicts. As previously written, E-04 made every finding an `error`, so: (1) CI's fail-closed `aw check plans --agent` step would fail permanently on every orchestrator at `to-review` or later; and (2) a NEW mechanism found at this review: `runner_shared.enforce_freeze_time_refusal` lints every queued `approved`/`auto-approved` IPD at `pre-execution` and runs BEFORE `enforce_orchestrator_probe_gate` in `initialize_run_core`, so an absent-verdict error at `pre-execution` would refuse every un-probed approved orchestrator (3 exist today: `95jk4s`, `9wzlou`, `l4vw9o`) before the run-start probe, which spec `25kzda` 2.5b says asks on a miss, ever runs. A run would then refuse with "run aw check plans" rather than asking.
- Decision needed: (a) recommended: in lint (both checkpoints) and check, an absent or stale verdict is advisory (`info`), while conditions 1 to 3, a recorded `fail` and an `unknown` stay errors; the `aw ipd set` refusal (Order 05) and the asking consumers keep refusing; (b) error in check and `review-finalize` but advisory at `pre-execution` only (fixes the freeze gate, leaves CI red); (c) persist a pass as a tracked attestation (forgeable by a hand edit). The answer fixes the absent-verdict severity E-04, E-06, V-04 and V-06 implement and check.
- Resolution or deferral rationale: open; raised by the 2026-10-04 /plan-review of `qs00nc` (finding PR-001). A reviewer may not choose the guarantee a published gate makes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the new module's public signature and result types. Paste test output for each condition case named in E-05 (the eight failing conditions, the executed-child case showing NO finding, and the unusable-child-table case showing a finding) with the finding code and subject, and for the ready case showing `ready=True` with no findings. Paste the no-model-call case showing the injected asker was called zero times with `ask=False`. Paste the malformed-Set fixture (two Order-0 plans) returning a result without recursing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the remedy constants. Paste one rendered human refusal and its agent record for the fail-verdict case, showing the quoted passage, the "do not delete the checklist" sentence, and both remedies. Paste `agent_schema.validate_agent_record` returning `[]` and a grep showing no absolute path in the record.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw ipd coverage --help`. Paste the fixture run's exit codes for ready (0), not ready (1), and no project (2). Paste the real-tree run for `axozpe` with `--agent`, and a second run whose record shows `cached: true` and `calls: 0` for `axozpe`. Paste the `CommandDeclaration` added for `ipd coverage` and the no-argument `aw ipd coverage --agent` record in a bare repo (exit 2, validates with `agent_schema.validate_agent_record`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw ipd lint --phase review-finalize`, `--phase pre-execution`, `--phase author` and `--phase pre-transition` on one fixture orchestrator failing condition 2, showing `IPD-S408` as an error, an error, an advisory only, and absent respectively. For a fixture whose conditions 1 to 3 pass and which has NO recorded verdict, paste `--phase review-finalize` and `--phase pre-execution` showing the absent-verdict finding at OQ-03's recorded severity. Paste the before and after warm timings (second of two runs) of bare `python3 -m agent_workflows ipd lint`, delta at most 1 s.
  - Observed evidence:
  - Result: pending


- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; the mutation (condition 2 accepts `draft`) failing it; the revert passing it; a grep of the test file for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the six declared paths.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the parity case's three outputs (`aw ipd lint --phase review-finalize`, `aw check plans --agent`, `aw ipd coverage --agent`) for one fixture showing identical finding codes. Paste `aw check plans --agent` against a draft fixture orchestrator showing no `check.orchestrator-not-review-ready`, and against the no-verdict fixture showing the absent-verdict finding at OQ-03's severity. Paste `check_engine.rule_spec(...)` for each rule id added. Paste the before and after warm timings of `python3 -m agent_workflows check plans --agent`, delta at most 1 s.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval, and OQ-03 must be answered first. Scope fence: the six `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and a declared path left untouched with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. The real-tree `aw ipd coverage` run spends one model call and is required evidence. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

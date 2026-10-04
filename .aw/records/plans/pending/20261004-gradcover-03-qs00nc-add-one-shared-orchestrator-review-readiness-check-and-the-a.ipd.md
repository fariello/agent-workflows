# IPD: Add one shared orchestrator review-readiness check and the aw ipd coverage verb

- Date: 2026-10-04
- Kind: child
- Concern: Nothing in the toolkit answers "is this orchestrator plan ready for review?" as one question. The pieces exist in different places and are never combined: child-table resolution (`runner_shared.find_unauthored_child_rows`, `runner_shared.read_set_membership`), row conformance (`ipd_lint.orchestrator_row_conformance`, `IPD-S407`), per-child lint (`ipd_lint.lint_file`), and the coverage verdict (`runner_shared.read_probe_verdict` / `probe_orchestrator`). The only consumer of the coverage verdict is the run-start gate, so an orchestrator reaches `to-review` with no check at all. Spec `25kzda` Section 2.5d (added by Order 01, `hm1h3l`) defines the four conditions and requires ONE function shared by every consumer, a model-free lint rule `IPD-S408`, an `aw check plans` rule, and an `aw ipd coverage` command that asks the probe once and records the answer.
- Scope: Add the shared function and its result type, the `aw ipd coverage` subcommand, the `IPD-S408` lint rule, and the `check.orchestrator-not-review-ready` check rule. IN: a new module `agent_workflows/orchestrator_readiness.py` holding `review_readiness(repo, plan_path, *, ask=False, ...)` and its result; wiring in `ipd_lint.py` (rule at `review-finalize`/`pre-execution`, advisory at `author`), `check_engine.py` (rule over pending orchestrators), and `cli.py` (subcommand); one new test file. OUT: any status setter (Order 05); any runner gate or retirement change (Order 04); production verification (Order 06); prompt or template text (Order 11); the probe's prompt or parser (Order 02, already executed).
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_orchestrator_readiness.py
- Item-Dependencies: executed:8mabmu
- Status: to-review
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: qs00nc

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 03 of Set `gradcover`. Implements spec `25kzda` Section 2.5d and `ipd-structure-and-linting` Section 9 rule 19 as amended by Order 01. Every later gate in the Set calls the function this plan adds.

## Goal

Provide one function that returns every reason an orchestrator plan is not ready for review, with a precise remedy per reason, plus a command that establishes the coverage verdict on demand, so that the setter, the linter, `aw check`, the production action and the runner can all ask the same question and get the same answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the function

- [ ] E-01 Add `agent_workflows/orchestrator_readiness.py` with `review_readiness(repo, plan_path, *, ask=False, model=None, host=None, state=None, asker=None, runner=None)` returning a `ReviewReadiness` result: `applies` (False for a non-orchestrator), `ready`, and an ordered tuple of `Finding(code, subject, detail, remedy)` covering exactly the four conditions of `25kzda` 2.5d. Condition 1 uses `read_set_membership` plus `find_unauthored_child_rows` (unresolvable and open-ended rows are findings). Condition 2 reads each child's `- Status:` and runs `ipd_lint.lint_file(..., checkpoint="author")`; a child below `to-review` or failing lint is a finding naming it. Condition 3 calls `ipd_lint.orchestrator_row_conformance`. Condition 4 calls `read_probe_verdict` on the plan's current digest and, ONLY when `ask=True`, calls `probe_orchestrator` on a miss (recording the verdict); an absent or stale verdict with `ask=False` is a finding whose remedy is `aw ipd coverage <id6>`; a fail verdict is one finding per stored quote; could-not-ask is a finding naming the retry command. All runner_shared imports are function-local.
  - Depends on: none
  - Expected outcome: the function returns `ready=True` only when all four conditions hold, and otherwise returns one finding per failing child, row or quoted passage, each with a remedy command or edit; it makes no model call unless `ask=True`.
  - Execution state: pending

- [ ] E-02 Write the remedy texts as data in the new module (one constant per finding code) so every consumer prints the same words, and make them satisfy spec `r07vma` R7: state the invariant, forbid deleting the checklist, and name the legitimate remedies (author the missing child and its row; bring the child to `to-review` with `aw ipd set to-review <child-id6>`; fix the child's named lint finding; assign the quoted obligation by id6 to a child in the table or add a child for it; run `aw ipd coverage <id6>`). Provide `render_human(result)` and `render_agent(result)` producing the human lines and an `aw.agent/v1` record (path-free, validated by `agent_schema.validate_agent_record`).
  - Depends on: E-01
  - Expected outcome: every finding code has one remedy constant; the agent record validates with no findings and carries no absolute path.
  - Execution state: pending

### Task group 2: the consumers this plan owns

- [ ] E-03 Add the `aw ipd coverage <id6|setid|path>...` subcommand: for each orchestrator plan selected, call `review_readiness(..., ask=True)` using the same host and model resolution `aw oc run` would (the existing `runner_profiles.resolve` path, defaulting to the opencode host), print the human or `--agent` rendering, and exit 0 when every selected orchestrator is ready, 1 when any is not, 2 when it cannot run (no project, no orchestrator selected). A non-orchestrator selection is reported as not applicable, not as a failure.
  - Depends on: E-02
  - Expected outcome: `aw ipd coverage <orchestrator>` asks the probe at most once per orchestrator, records the verdict, prints every finding, and returns the documented exit code; a second invocation on an unchanged plan spends no model call.
  - Execution state: pending

- [ ] E-04 Add lint rule `IPD-S408` in `ipd_lint.py` (new constant beside `C_ORCH_ROW`), called from the top-level lint for `Kind: orchestrator` plans: at `review-finalize` and `pre-execution` each finding of `review_readiness(..., ask=False)` becomes an error diagnostic; at `author` it becomes an advisory; at `pre-transition` and `post-transition` the rule does not run (spec `77tr3o` R-12 point 3 as amended keeps those checkpoints unchanged). Add `check.orchestrator-not-review-ready` (severity `error`) in `check_engine.py` over pending orchestrators whose status is `to-review`, `reviewed`, `approved` or `auto-approved`, using the same function, so `aw check plans` reports the same findings.
  - Depends on: E-03
  - Expected outcome: `aw ipd lint --phase review-finalize` and `aw check plans` report the same findings for the same fixture orchestrator; a draft orchestrator is not flagged by `aw check`; lint makes no model call.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_orchestrator_readiness.py` with fixture repositories built under `tempfile` and an injected fake probe: one case per condition (missing child file; open-ended `03+` row; child at `draft`; child failing lint; non-conforming row; no recorded verdict; recorded fail verdict with two quotes; could-not-ask), each asserting the finding code, subject and remedy; a ready case; a parity case asserting `aw ipd lint --phase review-finalize`, `aw check plans --agent` and `aw ipd coverage --agent`, driven as subprocesses, report the same finding codes for the same fixture; and a no-model-call case asserting lint and check never call the injected asker. Prove the test can fail by making condition 2 accept `draft` and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes, the mutation fails it, and no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE IMPLEMENTATION, SEVERAL CONSUMERS is the established pattern: `check_engine.evaluate_blocking_close` backs both backlog setter spellings, three `aw check` rules and a pre-commit hook; `ipd_lint.orchestrator_row_conformance` backs lint, `/plan-review` and both runners (spec `r07vma` R3).
- `ipd_lint` IMPORTS ARE FUNCTION-LOCAL FOR FIRST-PARTY CYCLES. The orchestrator-row section states that `ipd_set_plan` imports `ipd_lint` at module level, so `ipd_lint` must import other first-party modules inside function bodies; the same applies to the new module's use of `runner_shared`.
- `aw ipd lint` MUST BE MODEL-FREE (`ipd-structure-and-linting` Section 9). The rule reads the verdict store; only `aw ipd coverage` asks.
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

## Proposed changes (ordered, validatable)

1. New module with `review_readiness`, its result and finding types, and remedy constants (E-01, E-02).
2. `aw ipd coverage` subcommand in `cli.py` (E-03).
3. `IPD-S408` in `ipd_lint.py` and `check.orchestrator-not-review-ready` in `check_engine.py` (E-04).
4. Tests with fixtures, a parity case across three commands, and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- REFUSING THE STATUS CHANGE. Order 05.
  - Carrier: 26m1nb
- THE RUN-START AND RETIREMENT GATES. Order 04.
  - Carrier: 5etev3
- THE PRODUCTION GATE. Order 06.
  - Carrier: r2wa38
- TURNING `aw check plans` RED IN CI on the 13 orchestrators already at `to-review`. Avoided by ordering: this rule ships in this Order, and if CI runs between this Order and Order 09 it will report them. Order 09 runs the same Set so the window is the Set's own execution; recorded so a reviewer can choose to have this rule ship as `warn` until Order 09 if a red CI window is unacceptable.
  - Carrier: 52opph

## Scope check

- Over-scope: none. One new module, three wiring edits, one test file.
- Under-scope: after this plan the check exists and `aw check`/`aw ipd lint` report it, but nothing yet REFUSES a status change or a production handoff. A reader must not assume `aw ipd set to-review` is gated until Order 05 executes.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree before editing, failing node ids recorded.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_readiness.py tests/test_orchestrator_shape_gate.py tests/test_ipd_lint.py tests/test_check_engine.py -q` pasted.
- The mutation run for E-05 pasted.
- `python3 -m agent_workflows ipd coverage axozpe --agent` run once against the real tree, output pasted (this spends one real model call by design and records a verdict; it must be run by hand outside pytest).
- `python3 -m agent_workflows check plans` pasted, listing the current set of `check.orchestrator-not-review-ready` findings, which Order 09 will use.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled against the baseline.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` Section 2.5d and `ipd-structure-and-linting` Section 9 rule 19 (both added by Order 01). No spec edited here. `docs/cli-human-guide.md` is not changed by this plan; the new subcommand is documented by its `--help` text, and Order 11 updates authoring guidance.

## Open questions

### OQ-01: Should the function live in `ipd_lint`, `runner_shared`, or a new module?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a NEW module. `runner_shared` has a pinned module-level import set (`test_no_new_module_level_first_party_import_in_runner_shared`) and is 39,625 lines; `ipd_lint` must stay model-free, and the function's `ask=True` path calls the probe. A small module importing both lazily lets lint call it with `ask=False` and the runner call it with `ask=True` without either module importing the other at load time.

### OQ-02: Which child statuses count as ready?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: `to-review`, `reviewed`, `approved`, `auto-approved`, `executed`, as written in `25kzda` 2.5d condition 2. `executed` is included so an orchestrator whose early children already ran can still be reviewed; `draft`, `superseded` and `not-executed` are not ready (a superseded child must be replaced in the table first).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the new module's public signature and result types. Paste test output for each of the eight condition cases named in E-05 showing the finding code and subject, and for the ready case showing `ready=True` with no findings. Paste the no-model-call case showing the injected asker was called zero times with `ask=False`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the remedy constants. Paste one rendered human refusal and its agent record for the fail-verdict case, showing the quoted passage, the "do not delete the checklist" sentence, and both remedies. Paste `agent_schema.validate_agent_record` returning `[]` and a grep showing no absolute path in the record.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw ipd coverage --help`. Paste the fixture run's exit codes for ready (0), not ready (1), and no project (2). Paste the real-tree run for `axozpe` with `--agent`, and a second run showing it was served from the verdict cache (no model call; the record's cache field or timing shows it).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the parity case's three outputs for one fixture showing identical finding codes. Paste `aw ipd lint --phase author` on the same fixture showing the findings as advisories only, and `--phase pre-transition` showing no `IPD-S408`. Paste `aw check plans` against a draft fixture orchestrator showing no `check.orchestrator-not-review-ready`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; the mutation (condition 2 accepts `draft`) failing it; the revert passing it; a grep of the test file for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the five declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only the declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual test output. The real-tree `aw ipd coverage` run spends one model call and is required evidence. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

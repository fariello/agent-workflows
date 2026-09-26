# IPD: Dispatch an approved spec as a report-only production action verified by the SPEC-PLAN codes

- Date: 2026-09-26
- Kind: child
- Concern: PRODUCTION HAS NO CONSUMER (spec `z7nbn1` 4.3). `run_selection_policy.ACTION_PLAN` is defined and mapped (spec `approved -> plan`, backlog `open -> plan`), but re-measured at HEAD `310ea53e` it appears in `agent_workflows/` only in its definition, `ACTION_ORDER`, the two table entries, and one `runner_shared` docstring; `runner_shared.ACTION_IMPLEMENTED` is `frozenset(("review",))`, so `--action plan` fails closed; and nothing dispatches an approved spec. The three verification codes spec `z7nbn1` 4.4 brings in scope from approved spec `25kzda` 4.8 (`SPEC-PLAN-COUNT`, `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-GATE-CARRY`) grep to ZERO under `agent_workflows/`. Spec `z7nbn1` section 3 and `25kzda` 3.3's `approved` row define the action: author one or more conformant IPDs linked by `From-Spec`, preserve `Blocks-Release` on each, tool-set the spec `approved -> implementing` through `aw specs set`, verify, and REPORT the produced plans as next actions without enqueueing them (OQ-01).
- Scope: IN: (a) a production dispatcher for a queue entry with `artifact_type: spec` and action `plan`: an authoring turn whose prompt names the spec and the production contract (the house "Acting on a backlog item" authoring rules applied to a spec: review-ready `to-review` plans in `pending/`, `aw ipd scaffold`, `From-Spec: <id6>`, the spec's `Blocks-Release` copied exactly, `aw ipd lint` conforming, no edit to the spec's approved requirements); (b) deterministic post-turn verification implementing the three in-scope codes with the pass criteria, message templates and Action columns `25kzda` 4.8 specifies (this plan does not restate them); (c) on success, the runner tool-sets the spec `approved -> implementing` through `aw specs set` citing the produced plans, AFTER the produced plans are committed, and never marks the spec `implemented`; on failure, the spec is left `approved`; (d) report-only: produced plans are recorded on the item as `generated_next_actions` and rendered in the run's end-of-run report, and are NOT added to `state["queue"]`; (e) `ACTION_IMPLEMENTED` gains `plan`, and `enforce_requested_action` legality for `--action plan` is table-driven (legal only where the derived action is `plan`). OUT: `SPEC-PLAN-TRACE` (deferred to backlog `vy20et`, spec `z7nbn1` OQ-02); the other ten `SPEC-*` codes, including the dedicated `SPEC-IMPLEMENTING-TRANSITION` verifier (spec `z7nbn1` 4.4 NOT IN SCOPE; the transition itself IS performed here); dispatching `implementing` specs' children (stays with `25kzda` 3.3, `z7nbn1` section 7); backlog production (plan `y3p3p5`); a same-run follow of produced plans (removed by `hzdq8y`, out of scope per `z7nbn1` 3.4).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_spec_production.py
- Item-Dependencies: executed:2ptgds
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 5
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: aeq7f8

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 05 of Set artdispatch). ACTION_PLAN consumers, ACTION_IMPLEMENTED, and the three in-scope SPEC-PLAN codes re-measured at HEAD 310ea53e (zero enforcement); the approved->implementing transition confirmed legal and executor-owned in attention_contract; SPEC-PLAN-TRACE excluded per the maintainer's 2026-09-26 ruling (vy20et).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running an approved spec produces review-ready plans that link back to it and carry its release gate, moves the spec to `implementing` through the setter, reports those plans as next actions, and fails the item (leaving the spec `approved`) if the plans were not written, not linked, not conformant, or dropped or invented a gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 RE-MEASURE at the executing HEAD: `grep -rn "ACTION_PLAN\|\"plan\"" agent_workflows/runner_shared.py agent_workflows/run_selection_policy.py` (paste each hit and whether it is a consumer); `ACTION_IMPLEMENTED`; `grep -rn "SPEC-PLAN-\|BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` (expect zero); `attention_contract.SPEC_TRANSITIONS["approved"]` and `TRANSITION_AUTHORITY["->implementing"]` (at authoring: `implementing` is a legal target, `who: executor`, no human flag, no evidence). Read `25kzda` 4.8's three in-scope rows and paste their pass criteria and Action cells verbatim into this plan's Findings at execution, so E-04..E-06 implement the exact text. Enumerate how the execute path's lane, commit, integration and scope-reconciliation steps (`execute_item_core` through `integrate_lane_branch`) would treat a turn that writes only new files under `.aw/records/plans/pending/`, and decide whether production reuses that path (isolated lane, merge-and-revalidate) or the review path (no revalidation); record the decision with its reason as OQ-02's resolution text at execution.
  - Depends on: none
  - Expected outcome: zero existing enforcement confirmed; the verbatim rows pasted; the lane/integration decision recorded.
  - Execution state: pending

### Task group 2: the verifiers

- [ ] E-02 ADD `agent_workflows/production_checks.py`, a pure-ish module (reads the repository; no runner state, no host) exposing one function per code, each returning a list of findings `(code, plan_or_source_id6, message)` rendered from the `25kzda` 4.8 message template: `spec_plan_count(repo, spec_id6, baseline_plan_ids)`, `spec_plan_conformance(repo, spec_id6, produced_paths)`, `spec_plan_gate_carry(repo, spec_id6, produced_paths)`. Inputs are a BASELINE plan inventory (id6 -> path, captured before the turn) and the current tree, so "new" means "absent from the baseline". COUNT: at least one new plan carries `- From-Spec: <spec_id6>` and no NON-TERMINAL plan carrying the same `From-Spec` existed in the baseline (the duplicate-active-plan clause; "same phase" is read as "any live plan from this spec", recorded as OQ-01). CONFORMANCE: each new linked plan lints conforming at `review-finalize` (`ipd_lint.lint_file`), has `- Status: to-review`, sits under `pending/`, carries `From-Spec`, a concrete `- Scope-Paths:` (not empty, not `TODO`, not `grandfathered`), and a resolved `- Item-Dependencies:` (not `unresolved`). GATE-CARRY: each new linked plan's `Blocks-Release` equals the spec's exactly (compared through `check_engine._same_release`, so `next` and the release id6 it resolves to compare equal) and a spec with no gate yields plans with none. Reuse `check_engine._ITEM_FROM_SPEC_RE` and the existing plan iterators; no new path literal.
  - Depends on: E-01
  - Expected outcome: each function returns `[]` for a conforming production and the templated finding for each violation.
  - Execution state: pending

### Task group 3: the dispatcher

- [ ] E-03 ADD THE SPEC PRODUCTION TURN. In the shared dispatch (`execute_item_core` or a sibling it routes to by `(artifact_type, action)`; spec `z7nbn1` 1.8 leaves router versus monolith to the implementer, so record the choice), a `spec`/`plan` entry captures the baseline plan inventory and then runs one authoring turn with the E-01-chosen isolation. Its prompt names the spec path and states the production contract from the Scope bullet (a) list, and it adds two prohibitions: the agent must not change the spec's `- Status:` (the runner sets `implementing`), and must not execute any plan it writes. After the turn, the runner commits only the new plan files under the plans `pending/` tree (new relative to the baseline), and reports any other written path as out of scope the way `classify_review_writes` does for reviews. This replaces plan `8l8dgb`'s item-local "no dispatcher" refusal for `spec`/`plan`. `--full-auto` changes nothing here, because the produced plans are `to-review` and this action never approves them.
  - Depends on: E-02
  - Expected outcome: a fake agent that writes one conforming plan yields a committed plan file in `pending/` and nothing else committed.
  - Execution state: pending

- [ ] E-04 VERIFY, TRANSITION, REPORT. After the turn and commit, run the three E-02 checks against the committed tree. ANY finding: the item ends `fail-gate` (the `25kzda` 4.8 Action column for these rows is `FAIL ITEM after containment` / `RETRY, then FAIL ITEM`; use the existing correction budget for CONFORMANCE's RETRY by returning a retryable disposition through `handle_turn_failure_retry` only if its classification table admits it, else FAIL ITEM, and record which), with every finding recorded via `render_stream.record_refusal` and printed; the spec is NOT transitioned; produced files stay committed on the lane and are reported as quarantined-not-integrated (never merged to main) so a human can inspect them. NO finding: run `aw specs set <spec path> --status implementing --message "produced by run <run-id>: <plan id6s>"` through `pinned_module_argv` (the gated `--status` spelling, as `close_backlog_item` does for backlog), in the same tree that holds the committed plans, and commit that transition path-scoped; then record `generated_next_actions: [{id6, path, from_spec}]` on the item and end it `executed` (the production verified endpoint). NEVER set `implemented`. `state["queue"]` is not touched.
  - Depends on: E-03
  - Expected outcome: a conforming production ends `executed` with the spec in `implementing/` and the plans listed as next actions; any violation ends `fail-gate` with the spec still `approved`.
  - Execution state: pending

- [ ] E-05 RENDER THE NEXT ACTIONS AND ENABLE `--action plan`. The end-of-run report (`write_report` / the run summary) prints a "Generated next actions" block listing each produced plan with the command to review it (`aw <host> run <id6>`), and states they were NOT run in this run (spec `z7nbn1` 3.4, OQ-01). `ACTION_IMPLEMENTED` becomes `{"review", "plan"}`, and `enforce_requested_action`'s legality becomes "requested equals derived" for every implemented action (it already compares; fix its hardcoded `--action review` wording to name the requested action). `resume` of a completed production run must dispatch nothing new: confirm by reading the resume path that it iterates `state["queue"]` only.
  - Depends on: E-04
  - Expected outcome: the report shows the generated block; `--action plan` over an approved spec is legal and over a to-review plan is refused naming both actions.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 ADD `tests/test_spec_production.py` (behavioral only; temp git repos; `AW_HOME` isolated; host spawn patched with a fake agent that writes scripted files and commits nothing). Cases on BOTH hosts: (1) 5.5 success: the fake agent writes one conformant `to-review` plan carrying `From-Spec`; item `executed`, spec `implementing` via the setter (its history shows the `aw specs set` record), not `implemented`; (2) 5.5 refusal `SPEC-PLAN-COUNT`: the fake agent writes nothing; item `fail-gate` naming the code; spec `approved`; (3) 5.5 refusal `SPEC-PLAN-COUNT`: a plan lacking `From-Spec`; (4) 5.5 refusal `SPEC-PLAN-CONFORMANCE`: a plan with `- Status: draft` or a TODO Scope-Paths; (5) the duplicate clause: a live plan with the same `From-Spec` already exists before the run; `SPEC-PLAN-COUNT`; (6) 5.5b BOTH directions: a spec with `Blocks-Release: next` whose produced plan carries `next` passes, and one whose plan omits it fails `SPEC-PLAN-GATE-CARRY`; a spec with NO gate whose plan invents `Blocks-Release: next` fails `SPEC-PLAN-GATE-CARRY`, and one whose plan carries none passes; (7) 5.5a REPORT-ONLY: capture the set of queue id6s before the first turn and at run end and assert equality, assert the produced plan appears in `generated_next_actions` and in the report, then call the host's resume on that run and assert no new turn is spawned (spawn patched to fail if called).
  - Depends on: E-05
  - Expected outcome: all pass on both hosts; every case FAILS against the pre-change code (which refuses the spec item-locally as undispatchable).
  - Execution state: pending

- [ ] E-07 UNIT-TEST THE VERIFIERS DIRECTLY in the same file against hand-built trees (no runner), one case per pass criterion clause, so a verifier regression is visible without a run.
  - Depends on: E-06
  - Expected outcome: each clause has a passing and a failing fixture.
  - Execution state: pending

- [ ] E-08 RUN the bare suite before and after, and confirm `grep -rn "SPEC-PLAN-TRACE" agent_workflows/` still finds no enforcement (the deferred code was not half-built).
  - Depends on: E-07
  - Expected outcome: the after-minus-before failing node set is empty; `SPEC-PLAN-TRACE` has no enforcement.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Status transitions go through the setters with the GATED spelling (`aw <type> set <path> --status <s>`), invoked by the runner via `pinned_module_argv`, never by text edit (`close_backlog_item`'s docstring explains why the positional spelling is unsafe for gated transitions).
- `approved -> implementing` is `who: executor`, no human flag, no evidence (`attention_contract.TRANSITION_AUTHORITY`); `implementing -> implemented` requires resolvable executed-plan evidence and is never set here.
- `check_engine._same_release` compares gates by release identity; `check.from-spec-dangling` already validates that a `From-Spec` resolves.
- 25kzda 5.4 rule 10: generated IPDs are recorded as generated next actions and never join the frozen run.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ACTION_PLAN` | No consumer. | `grep ACTION_PLAN agent_workflows/` -> `run_selection_policy` definition, `ACTION_ORDER`, two table rows; one `runner_shared` docstring |
| F-2 | HIGH | `runner_shared.ACTION_IMPLEMENTED` | `--action plan` refused. | `ACTION_IMPLEMENTED = frozenset(("review",))` |
| F-3 | HIGH | verification | The three in-scope codes have zero enforcement. | `grep -rn "SPEC-PLAN-" agent_workflows/` -> no hits |
| F-4 | INFO | transition authority | `approved -> implementing` is legal and executor-owned. | `SPEC_TRANSITIONS["approved"]` includes `implementing`; `TRANSITION_AUTHORITY["->implementing"] == {'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': False}` |
| F-5 | INFO | corpus | No approved spec currently has a live `From-Spec` plan, so the duplicate clause starts from a clean baseline. | 13 approved specs, 0 non-terminal plans carrying their `From-Spec` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures and decides the lane/integration shape.
2. E-02 adds the three verifiers.
3. E-03 adds the production turn.
4. E-04 verifies, transitions and records next actions.
5. E-05 renders the report and enables `--action plan`.
6. E-06 adds run-level behavioral tests for 5.5, 5.5a, 5.5b.
7. E-07 adds verifier unit tests.
8. E-08 runs the suite.

## Deferred / out of scope (with reason)

- `SPEC-PLAN-TRACE` (requirement coverage).
  - Carrier: vy20et
  - Rationale: maintainer ruling 2026-09-26 (spec `z7nbn1` OQ-02 revised): needs a requirement-ID convention the corpus lacks; plan review remains the coverage check, and a produced plan must not be described as trace-verified.
- The other `SPEC-*` codes of `25kzda` 4.8, including `SPEC-IMPLEMENTING-TRANSITION`.
  - Carrier-Declined: spec `z7nbn1` 4.4 places them NOT IN SCOPE and leaves them with `25kzda` 4.8 for separate work; the `approved -> implementing` transition is still performed here through the setter.
- Dispatching an `implementing` spec's children.
  - Carrier-Declined: `z7nbn1` section 7 leaves the `implementing` dispatch row with `25kzda` 3.3; it stays `undetermined` and plan `jdn790` refuses it clearly.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/specs.py`, `check_engine.py`, `ipd_lint.py` are called, not changed. The report renderer may live in `render_stream.py`; if E-05 must edit it, declare it at finalize with `--scope-reason`.
- Scope-Paths justification: `production_checks.py` (new) holds the verifiers so plan `y3p3p5` can add the backlog codes beside them; `runner_shared.py` holds dispatch, commit, transition and report wiring; the host modules hold any host-specific prompt spelling; the new test file holds E-06/E-07.

## Required tests / validation

- `tests/test_spec_production.py` (new): run-level cases for 5.5 (success and each refusal), 5.5a (queue id set before equals after, resume dispatches nothing), 5.5b (both directions), and verifier unit cases; shown failing before the change.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` section 3, 4.3, the three in-scope 4.4 codes, and acceptance 5.5, 5.5a, 5.5b as written, and `25kzda` 3.3's `approved` row. `25kzda` 4.8's rows are implemented with their existing text; nothing is amended.
- No user-facing docs beyond the generated `--action` help text.

## Open questions

### OQ-01: What is "the same phase" in SPEC-PLAN-COUNT's duplicate clause?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: any NON-TERMINAL plan already carrying `From-Spec: <this spec>`, from repository evidence: `25kzda` 3.3 dispatches `approved` exactly once (the spec moves to `implementing` on success), so a live linked plan at the start of a production turn can only be a prior production or a hand-authored graduation, and producing again would duplicate it (spec `z7nbn1` 3.3a). Plans in `executed/`/`superseded/`/`not-executed/` do not count. Measured baseline: no approved spec has a live linked plan today (F-5).

### OQ-02: Does a production turn run in an isolated lane with merge-and-revalidate?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: it runs in an isolated lane (the runner's default for every turn, `resolve_isolation`), and its integration is the REVIEW-style integration without suite revalidation, because the turn's legitimate output is new plan documents and a spec status change, the same class of output as a review; `integration_action_for_item`'s rationale (a review lane "must NOT be" revalidated because its output is records) applies. E-01 confirms this against the code at execution and records the result here; if the lane path cannot carry a production turn without the execute-path gates, E-01 records the smallest change and its reason.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `ACTION_PLAN`/code greps, `ACTION_IMPLEMENTED`, the transition-authority values, the three 25kzda 4.8 rows verbatim, and the recorded lane/integration decision.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new module's public signatures and one `python3 -c` run per verifier on a hand-built tree showing `[]` and a templated finding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the dispatcher diff, the production prompt text for a scratch spec, and the lane commit's `git show --name-only` for a fake agent that wrote one plan plus one stray file (stray reported, not committed).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a success run's item record (`status: executed`, `generated_next_actions`), the spec's new location and history line from `aw specs set`, and a failure run's item record (`fail-gate`, refusal naming the code) with the spec still under `approved/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the end-of-run report's "Generated next actions" block, the `--action plan` legal and refused outputs, and the resume code path read showing it iterates `state["queue"]` only.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_production.py -q` passing with count, and with E-03..E-05 reverted the run-level cases FAILING; passing again after restoring. For 5.5a paste the asserted before and after queue id sets.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the verifier unit cases' names and their pass output, one pass and one fail fixture per clause.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty), and `grep -rn "SPEC-PLAN-TRACE" agent_workflows/` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Running an approved spec now PRODUCES plans: one agent turn writes review-ready plans linked to the spec, the runner checks them deterministically (at least one new linked plan and no live duplicate, each plan conformant and `to-review` in `pending/`, and the spec's release gate copied exactly or none invented), then moves the spec to `implementing` through the setter and lists the plans as next actions without running them. Any failed check fails the item, leaves the spec `approved`, and keeps the produced files quarantined on the lane for inspection. `--action plan` becomes legal where the table says `plan`. Requirement coverage (`SPEC-PLAN-TRACE`) is NOT checked; plan review remains the coverage check, per the maintainer's 2026-09-26 ruling. Order 05 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `2ptgds`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).

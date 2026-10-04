# IPD: Check the whole Set before a production action hands off a backlog item or spec

- Date: 2026-10-04
- Kind: child
- Concern: When `aw oc run` / `aw agy run` graduates an `open` backlog item (or produces plans from an `approved` spec), `runner_shared.execute_item_core`'s production branches verify each new plan alone (`production_checks.backlog_graduate_count`, `backlog_graduate_ipd`, `backlog_gate_handoff`; for specs `spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`) and then tool-set the source `graduated` / `implementing`. `production_checks._check_ipd_conformance` reads bucket, status, origin link, Scope-Paths, Item-Dependencies and `lint_file(checkpoint="review-finalize")` for one file; nothing reads the child table, the children's readiness, or the coverage verdict. That is how 11 backlog items reached `graduated` with orchestrators the next run refused. Spec `25kzda` 4.8 and 4.9 as amended by Order 01 add `SPEC-PLAN-SET` and `BACKLOG-GRADUATE-SET`.
- Scope: IN: two new verifiers in `production_checks.py`, `backlog_graduate_set` and `spec_plan_set`, each calling `orchestrator_readiness.review_readiness(..., ask=True)` for every newly produced plan with `- Kind: orchestrator` and returning one finding per not-ready condition with the code and message template of the amended spec; calling them in both production branches of `execute_item_core` after the existing per-plan verifiers and before the source transition; on success, the verdict is already recorded by `review_readiness`, so the produced Set enters the next run with a cached pass; on failure, the existing finding path applies unchanged (fail-gate, refusal recorded, lane preserved, source left `open`/`approved`). OUT: the correction turn (Order 07); continuing an unfinished handoff (Order 08); the prompt text (Order 11); the readiness function (Order 03).
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_production_set_check.py
- Item-Dependencies: executed:qs00nc
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 6
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: r2wa38

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 06 of Set `gradcover`. Implements `25kzda` 4.8 `SPEC-PLAN-SET` and 4.9 `BACKLOG-GRADUATE-SET` as amended by Order 01. This is the change that stops a graduation reporting success with a refused orchestrator.

## Goal

Make a production action succeed only when every orchestrator it wrote is ready for review, so a backlog item reaches `graduated` (or a spec `implementing`) only with a Set the next run will accept, and record the passing verdict so that run makes no probe call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the verifiers

- [ ] E-01 Add `backlog_graduate_set(repo, item_id6, produced_paths, *, host, run_id, state=None, asker=None, runner=None)` and `spec_plan_set(...)` to `production_checks.py`. Each selects the produced plans whose metadata `- Kind:` is `orchestrator` (via `ipd_lint.parse`), calls `orchestrator_readiness.review_readiness(repo, path, ask=True, ...)` on each, and returns `[(code, plan_id, message)]` where code is `BACKLOG-GRADUATE-SET` or `SPEC-PLAN-SET` and message follows the amended `25kzda` template, listing every finding's subject, quoted passage (if any) and remedy. A produced Set with no orchestrator returns no finding. Each finding's message ends with the resume command, matching the existing codes.
  - Depends on: none
  - Expected outcome: given a produced orchestrator whose child is `draft`, the verifier returns one finding naming the child; given one whose fake probe answers with a quote, it returns one finding containing the quote; given a ready one, it returns none and the verdict store holds a pass for its digest.
  - Execution state: pending

### Task group 2: wire them in

- [ ] E-02 In `execute_item_core`'s backlog production branch, call `backlog_graduate_set` after `backlog_gate_handoff` and add its findings to the same `findings` list, so the existing `if findings:` path (fail-gate, `record_refusal`, `record_lane_preserved`) handles a failure and the `open -> graduated` transition is never reached. Pass the run's `state` and host so the probe uses the run's model.
  - Depends on: E-01
  - Expected outcome: a backlog production whose produced orchestrator fails ends `fail-gate`, the backlog item stays `open`, the lane is preserved, and the refusal code is `BACKLOG-GRADUATE-SET`.
  - Execution state: pending

- [ ] E-03 Make the same change in the spec production branch with `spec_plan_set` after `spec_plan_gate_carry`, so the spec stays `approved` on failure.
  - Depends on: E-02
  - Expected outcome: a spec production whose produced orchestrator fails ends `fail-gate`, the spec stays `approved`, and the refusal code is `SPEC-PLAN-SET`.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_production_set_check.py`. Unit cases for both verifiers over fixture repositories with an injected fake probe (draft child; missing child; quoted uncovered passage; ready; no orchestrator produced). Integration cases reusing the fixture and fake-host pattern of `tests/test_backlog_production.py` and `tests/test_spec_production.py`: a backlog production whose scripted agent writes an orchestrator with a `draft` child ends `fail-gate` with the item still `open`; the same with a ready Set ends with the item `graduated` and a pass verdict recorded for the orchestrator's digest; the spec-production twin of each. Prove the tests can fail by removing the E-02 call and pasting the failure.
  - Depends on: E-03
  - Expected outcome: the new file passes; the mutation fails it; existing `tests/test_backlog_production.py` and `tests/test_spec_production.py` still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PRODUCTION PATH ALREADY CONTAINS A FAILURE ON ANY FINDING. In both branches `if findings:` sets `disposition = "fail-gate"`, records every finding as a refusal, and preserves the lane; nothing integrates. New findings join that list rather than adding a new failure path.
- `production_checks` IS THE HOME OF THE PRODUCTION CODES. Its module docstring names it the deterministic verifier module for `25kzda` 4.8/4.9; the new verifiers sit beside `backlog_graduate_ipd`.
- REAL MODEL CALLS ARE FORBIDDEN IN TESTS (`_assert_probe_spawn_is_permitted`); integration tests inject the probe runner.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Per-plan only. `backlog_graduate_ipd` loops over `produced_paths` calling `_check_ipd_conformance` once per file; `_check_ipd_conformance` has no Set or child-table logic. | the two function bodies |
| F-02 | The source transition follows directly. After `if findings:` / `else:` in the backlog branch, the `else` reads the item's current status and calls `aw backlog set <id6> --status graduated`; there is no further check between the per-plan verifiers and that call. | the backlog branch's `else` block with the `"--status", "graduated"` argv |
| F-03 | The measured outcome: 11 of the 13 refused orchestrators' backlog items read `graduated` (`ildjse`, `dvonrn`, `eeiytw`, `7yz545`, `fcnz1r`, `mflqqf`, `s8veyk`, `ariaau`, `rgl2d4`, `sv9ce4`, `qbz8i1`); `0livgf` and `h0tiaw` read `open`. | `grep '^- Status:'` on each backlog file named by the orchestrators' `- From-Backlog:` |

## Proposed changes (ordered, validatable)

1. Two verifiers in `production_checks.py` (E-01).
2. Wire into the backlog branch (E-02) and the spec branch (E-03).
3. Unit and integration tests plus a mutation proof (E-04).

## Deferred / out of scope (with reason)

- ASKING THE AGENT TO FIX THE FINDING IN THE SAME RUN. Order 07.
  - Carrier: nnsa2o
- A PRODUCTION ACTION THAT FINDS AN EARLIER, UNFINISHED SET FOR THE SAME SOURCE. Today `backlog_graduate_count` refuses it as a duplicate; Order 08 changes that.
  - Carrier: 24qw39

## Scope check

- Over-scope: none. Two production modules and one test file.
- Under-scope: after this plan a failed graduation leaves the backlog item `open` with the work in a preserved lane, but a re-run will be refused by `BACKLOG-GRADUATE-COUNT`'s duplicate branch if the lane's plans were integrated earlier; Order 08 resolves that. The 2026-10-03 orchestrators were never in a lane (they were integrated), which is Order 09's case.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_production_set_check.py tests/test_backlog_production.py tests/test_spec_production.py -q` pasted.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 4.8 `SPEC-PLAN-SET` and 4.9 `BACKLOG-GRADUATE-SET` as amended by Order 01. Spec `z7nbn1` Section 4.4 delegates the production codes to `25kzda` and needs no edit. No spec edited here.

## Open questions

### OQ-01: Should the Set check run on every produced plan, or only on orchestrators?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: only on produced orchestrators. A child plan's readiness is already covered by `BACKLOG-GRADUATE-IPD` (status `to-review`, conformant lint), and a single-plan graduation with no orchestrator has no Set to check. The orchestrator's check includes its children (condition 2), so children are checked through it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `production_checks.py`. Paste the unit-case outputs for draft child, missing child, quoted passage (message contains the quote), ready (no finding, and the verdict store holds `pass` for the digest), and no orchestrator (no finding).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the backlog branch. Paste the integration case's final item status (`fail-gate`), the backlog item's on-disk `- Status: open`, the recorded refusal code `BACKLOG-GRADUATE-SET`, and the lane-preserved event.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the spec branch, the spec integration case's final status, the spec's on-disk `- Status: approved`, and the `SPEC-PLAN-SET` refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new file passing with its count and the two existing production test files passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

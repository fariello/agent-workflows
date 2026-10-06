# IPD: Check the whole Set before a production action hands off a backlog item or spec

- Date: 2026-10-04
- Kind: child
- Concern: When `aw oc run` / `aw agy run` graduates an `open` backlog item (or produces plans from an `approved` spec), `runner_shared.execute_item_core`'s production branches verify each new plan alone (`production_checks.backlog_graduate_count`, `backlog_graduate_ipd`, `backlog_gate_handoff`; for specs `spec_plan_count`, `spec_plan_conformance`, `spec_plan_gate_carry`) and then tool-set the source `graduated` / `implementing`. `production_checks._check_ipd_conformance` reads bucket, status, origin link, Scope-Paths, Item-Dependencies and `lint_file(checkpoint="review-finalize")` for one file; nothing reads the child table, the children's readiness, or the coverage verdict. That is how 11 backlog items reached `graduated` with orchestrators the next run refused. Spec `25kzda` 4.8 and 4.9 as amended by Order 01 add `SPEC-PLAN-SET` and `BACKLOG-GRADUATE-SET`.
- Scope: IN: two new verifiers in `production_checks.py`, `backlog_graduate_set` and `spec_plan_set`, each calling `orchestrator_readiness.review_readiness(..., ask=True)` for every newly produced plan with `- Kind: orchestrator` and returning one finding per not-ready condition with the code and message template of the amended spec; calling them in both production branches of `execute_item_core` after the existing per-plan verifiers and before the source transition; on success, the verdict is already recorded by `review_readiness`, so the produced Set enters the next run with a cached pass; on failure, the existing finding path applies unchanged (fail-gate, refusal recorded, lane preserved, source left `open`/`approved`). OUT: the correction turn (Order 07); continuing an unfinished handoff (Order 08); the prompt text (Order 11); the readiness function (Order 03).
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_production_set_check.py
- Item-Dependencies: executed:qs00nc
- Status: reviewed
- Readiness: go-pending-approval
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
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-006..PR-009 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-006 to PR-009 (round 2). Fixed: commit ordering settled from code (production commit precedes the verifiers; Order 02 commits the record at write; no second commit path; stop condition) (PR-006); `state` made required since `frozen_retry_budget(None)` raises (PR-007); integration evidence rewritten for the `--no-isolate-worktree` fixtures, which have no integrated branch (PR-008); mutation count, test list (PR-009).
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. Maintainer ruling 2026-10-04: the coverage answer is stored in the plan itself (`25kzda` 2.5e, Order 02's `coverage_record`), not in the gitignored 30-day cache. The Set verifier writes the record into the produced orchestrator in the lane; the executor must confirm it is committed with the production output.
- 2026-10-04 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 (all fixed)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-005. Fixed: Set verifier ordered before the per-plan verifier and `IPD-S408` de-duplicated, since the per-plan lint already inherits it (PR-001); could-not-ask handled and frozen retry budget passed (PR-002); host string and lane verdict store specified (PR-003); probe injection seam for integration tests named (PR-004); extra cases, mutation, gate contract (PR-005).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 06 of Set `gradcover`. Implements `25kzda` 4.8 `SPEC-PLAN-SET` and 4.9 `BACKLOG-GRADUATE-SET` as amended by Order 01. This is the change that stops a graduation reporting success with a refused orchestrator.

## Goal

Make a production action succeed only when every orchestrator it wrote is ready for review, so a backlog item reaches `graduated` (or a spec `implementing`) only with a Set the next run will accept, and record the passing answer in the orchestrator plan itself so that run makes no probe call.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the verifiers

- [ ] E-01 Add `backlog_graduate_set(repo, item_id6, produced_paths, *, host, run_id, state, asker=None, runner=None)` and `spec_plan_set(...)` (`state` REQUIRED, not defaulted: `runner_shared.frozen_retry_budget` calls `state.get(...)` and raises on `None`, and the probe reads its model from `state["options"]`) to `production_checks.py`. Each selects the produced plans whose metadata `- Kind:` is `orchestrator` (via `ipd_lint.parse`), calls `orchestrator_readiness.review_readiness(repo, path, ask=True, ...)` on each, and returns `[(code, plan_id, message)]` where code is `BACKLOG-GRADUATE-SET` or `SPEC-PLAN-SET` and message follows the amended `25kzda` template, listing every finding's subject, quoted passage (if any) and remedy. A produced Set with no orchestrator returns no finding. Each finding's message ends with the resume command, matching the existing codes. Pass `retry_budget=frozen_retry_budget(state)` through to the probe. A could-not-ask is a finding (spec `25kzda` 2.5d UNAVAILABILITY: the production consumer refuses) whose message names `aw ipd coverage <plan-id>` as well as the resume command, so the operator is not sent to re-run an agent turn for a host outage.
  - Depends on: none
  - Expected outcome: given a produced orchestrator whose child is `draft`, the verifier returns one finding naming the child; given one whose fake probe answers with a quote, it returns one finding containing the quote; given a ready one, it returns none and the orchestrator plan carries a current `- Coverage: pass` record with its history line.
  - Execution state: pending

### Task group 2: wire them in

- [ ] E-02 In `execute_item_core`'s backlog production branch, call `backlog_graduate_set` BEFORE `backlog_graduate_ipd` (and after `backlog_graduate_count`), and add its findings to the same `findings` list. ORDER AND DE-DUPLICATION ARE REQUIRED, not stylistic: `production_checks._check_ipd_conformance`, which `backlog_graduate_ipd` calls per produced plan, runs `ipd_lint.lint_file(p, checkpoint="review-finalize")`, and after Order 03 that lint runs `IPD-S408` on a produced orchestrator, READING the plan's coverage record. Run the asking Set verifier first so the record exists when the per-plan lint reads it; and drop `IPD-S408` diagnostics from `_check_ipd_conformance`'s output (the Set verifier owns that condition), so one not-ready orchestrator yields one `BACKLOG-GRADUATE-SET` finding rather than that plus a `BACKLOG-GRADUATE-IPD` restatement, and an absent verdict never fails the per-plan verifier for a plan the Set verifier just cleared. The existing `if findings:` path then applies: so the existing `if findings:` path (fail-gate, `record_refusal`, `record_lane_preserved`) handles a failure and the `open -> graduated` transition is never reached. Pass the run's `state` and the branch's existing `host_name` (`"agy" if "agy" in host_labels.id else "oc"`, the string `probe_argv` branches on) so the probe uses the run's model and host. The probe is asked with `repo=target_tree` (the lane, or the shared checkout under `--no-isolate-worktree`) and writes the record into the produced orchestrator there. COMMIT ORDERING, settled at review rather than left to the executor: `commit_backlog_production_output` (and `commit_spec_production_output` in the spec branch) runs BEFORE the verifiers, so the produced plan is already committed and clean when the Set verifier asks; Order 02 (`8mabmu` E-07) makes `probe_orchestrator` commit the record itself, path-scoped, whenever the plan file is clean. So the record lands as its own commit after the production commit and before the `graduated` transition commit, and reaches `main` when the lane integrates; do NOT add a second commit path. This ordering keeps `backlog_graduate_legitimacy` clause 3 satisfied (the production commit is still an ancestor of the item's transition commit). If Order 02 as executed does not commit at write, STOP and report, because the record would then be left uncommitted in the lane. A `fail` record is committed the same way, so a failed graduation leaves the answer and its quotes durable in the preserved lane for Order 07 and the operator.
  - Depends on: E-01
  - Expected outcome: a backlog production whose produced orchestrator fails ends `fail-gate`, the backlog item stays `open`, the lane is preserved, and the refusal code is `BACKLOG-GRADUATE-SET`.
  - Execution state: pending

- [ ] E-03 Make the same change in the spec production branch with `spec_plan_set`, called BEFORE `spec_plan_conformance` (after `spec_plan_count`), with the same `IPD-S408` de-duplication (both per-plan verifiers share `_check_ipd_conformance`), so the spec stays `approved` on failure.
  - Depends on: E-02
  - Expected outcome: a spec production whose produced orchestrator fails ends `fail-gate`, the spec stays `approved`, and the refusal code is `SPEC-PLAN-SET`.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_production_set_check.py`. Unit cases for both verifiers over fixture repositories with an injected fake probe (draft child; missing child; quoted uncovered passage; ready; no orchestrator produced). Integration cases reusing the `initialize_run` + `run_queue` + `_patch_host_agent` pattern of `tests/test_backlog_production.py` and `tests/test_spec_production.py` (whose existing fixtures produce only `Kind: child` plans, so their behavior is unchanged), on both hosts. `execute_item_core` passes no asker, so integration cases inject the probe by patching `runner_shared.ask_orchestrator_probe` with a scripted double that counts its calls; the real spawn raises under pytest. Cases: a backlog production whose scripted agent writes an orchestrator with a `draft` child ends `fail-gate` with the item still `open`; the same with a ready Set ends with the item `graduated` and a current coverage pass recorded in the orchestrator and committed (the existing fixtures run `--no-isolate-worktree` in a `git init` repo, so assert `git status --porcelain -- <orchestrator>` is empty and `git log --format=%s -- <orchestrator>` lists the coverage commit after the production commit, rather than an integrated branch); the spec-production twin of each; a ready Set whose probe double answers could-not-ask ends `fail-gate` naming `aw ipd coverage`; and a not-ready orchestrator yields exactly one finding (no `BACKLOG-GRADUATE-IPD` restatement of `IPD-S408`). Prove the tests can fail by removing the E-02 call and pasting the failure, and by moving the Set verifier after the per-plan verifier and pasting the resulting failure of the ready case (OQ-03 of `qs00nc` is resolved: an absent record IS an error at `review-finalize`, so this mutation is observable).
  - Depends on: E-03
  - Expected outcome: the new file passes; each of the two mutations fails it; existing `tests/test_backlog_production.py` and `tests/test_spec_production.py` still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PRODUCTION PATH ALREADY CONTAINS A FAILURE ON ANY FINDING. In both branches `if findings:` sets `disposition = "fail-gate"`, records every finding as a refusal, and preserves the lane; nothing integrates. New findings join that list rather than adding a new failure path.
- `production_checks` IS THE HOME OF THE PRODUCTION CODES. Its module docstring names it the deterministic verifier module for `25kzda` 4.8/4.9; the new verifiers sit beside `backlog_graduate_ipd`.
- REAL MODEL CALLS ARE FORBIDDEN IN TESTS (`_assert_probe_spawn_is_permitted`); integration tests inject the probe by patching `runner_shared.ask_orchestrator_probe`.
- THE PER-PLAN VERIFIER LINTS AT `review-finalize`. `_check_ipd_conformance` calls `lint_file(p, checkpoint="review-finalize")` and copies every diagnostic when the disposition is not conforming, so any rule Order 03 adds at that checkpoint is already inherited by `BACKLOG-GRADUATE-IPD` and `SPEC-PLAN-CONFORMANCE`.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Per-plan only. `backlog_graduate_ipd` loops over `produced_paths` calling `_check_ipd_conformance` once per file; `_check_ipd_conformance` has no Set or child-table logic. | the two function bodies |
| F-02 | The source transition follows directly. After `if findings:` / `else:` in the backlog branch, the `else` reads the item's current status and calls `aw backlog set <id6> --status graduated`; there is no further check between the per-plan verifiers and that call. | the backlog branch's `else` block with the `"--status", "graduated"` argv |
| F-04 | After Order 03, the per-plan verifier would already report `IPD-S408` for a produced orchestrator, reading (never asking) the plan's coverage record, so without ordering the Set verifier first a fresh orchestrator is judged before anyone has asked. | `_check_ipd_conformance` "Lints conforming at review-finalize" block; `qs00nc` E-04 |
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
- `python3 -m pytest -o addopts="" tests/test_production_set_check.py tests/test_backlog_production.py tests/test_spec_production.py tests/test_orchestrator_readiness.py -q` pasted.
- Both mutation runs pasted (E-04).
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
  - Required evidence: paste the diff of `production_checks.py`. Paste the unit-case outputs for draft child, missing child, quoted passage (message contains the quote), ready (no finding, and the orchestrator file carries `- Coverage: pass`, a fingerprint matching its text, and the history line), and no orchestrator (no finding).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the backlog branch showing the Set verifier ordered before `backlog_graduate_ipd` and the `IPD-S408` filter, and paste the check of `coverage_record.write`'s commit-at-write behavior made before editing (the commit-ordering prerequisite of E-02). Paste the single-finding case's findings list, the could-not-ask case's refusal naming `aw ipd coverage`, and the integration case's final item status (`fail-gate`), the backlog item's on-disk `- Status: open`, the recorded refusal code `BACKLOG-GRADUATE-SET`, and the lane-preserved event.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the spec branch (same ordering and filter), the spec integration case's final status, the spec's on-disk `- Status: approved`, and the `SPEC-PLAN-SET` refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new file passing with its count and the two existing production test files passing; each mutation failing (or the recorded reason one is not observable) and the revert passing; the probe double's call count for the ready integration case (exactly one per produced orchestrator); the ready case's `git log --format=%s -- <orchestrator>` showing the production commit then the coverage commit, and `git status --porcelain -- <orchestrator>` empty; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Scope fence: the three `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

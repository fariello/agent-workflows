# IPD: Dispatch a to-review spec to the spec review and advance it only on a conforming review record

- Date: 2026-09-26
- Kind: child
- Concern: `aw oc run reviews --type spec` can SELECT the specs awaiting review, and after plan `8l8dgb` a queue can CARRY one, but nothing can RUN one (spec `z7nbn1` section 0, 1.6 first bullet, acceptance 5.4). Measured at HEAD `310ea53e`: the only review prompt is `runner_shared.build_review_prompt`, which returns `/plan-review <path>` unconditionally; `runner_shared.reconcile_disposition`'s review rung reads the artifact through `resolve_plan_path` and returns `reviewed` on exit 0 even when the status did not change ("if status in (reviewed, approved): return status ... return reviewed"); and the `--full-auto` bridge after a review (`is_plan_review_approved` / `set_plan_approved`) is plan-only. Handing a spec to that path would run the WRONG workflow (`/plan-review`'s IPD-lint preflight and `Readiness` write corrupt a spec, per the `spec-review` row of `.aw/system/workflows/index.md`) and would report success for a turn that never advanced the spec. The spec-side machinery already exists and must be CONSUMED, not rebuilt: the `/spec-review` workflow (`.aw/system/workflows/spec-review/spec-review.md`, shims under `.opencode/commands/` and `.claude/commands/`) advances a spec with `aw specs set reviewed <id6>`, and that transition already REFUSES without a conforming record through `specs._review_attestation_refusal` over `review_findings.review_attestation_missing(repo, id6, "spec")`.
- Scope: IN: (a) type-appropriate review dispatch: a queue entry with `artifact_type: spec` and action `review` gets the `/spec-review <path>` command (same argv-safety and lane-isolation-notice shape as `build_review_prompt`), and the run record names the handler (`review_handler: spec-review` on the attempt and in the `ipd-started`-equivalent event); (b) spec-aware disposition: after the turn, the spec is `reviewed` ONLY if its on-disk `- Status:` is `reviewed` AND `review_attestation_missing(repo, id6, "spec")` is `None`; otherwise the item ends `fail-gate` with a recorded refusal naming what is missing and the spec is left as it was; (c) the review output commit/integration for a spec lane scoped to the spec file, its history, and its review record (`classify_review_writes` keys on the id6, which the spec path and the record path both carry); (d) the `--full-auto` approval bridge is NEVER applied to a spec (spec `25kzda` 3.3: a reviewed spec stops at the human approval gate "including under `--full-auto`"); (e) replace plan `8l8dgb`'s item-local "no dispatcher" refusal for spec review with this dispatch. OUT: spec `draft` completeness (no spec completeness parser exists; `draft` stays `undetermined` and plan `jdn790` refuses it); `--action review` on a `reviewed` spec (re-review row of `25kzda` 3.3) beyond confirming the existing `enforce_requested_action` legality still refuses it until a later change; the review workflow body itself.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_spec_review_dispatch.py
- Item-Dependencies: executed:jdn790
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 4
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2ptgds

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 04 of Set artdispatch). build_review_prompt, reconcile_disposition's review rung and the full-auto bridge measured plan-only at HEAD 310ea53e; the spec->reviewed attestation predicate and the /spec-review workflow and shims confirmed present, so this plan consumes them.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A to-review spec in a run gets the spec review, not the plan review, and the run counts it reviewed only when the spec actually reached `reviewed` through the setter with a conforming review record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 TRACE THE REVIEW PATH at the executing HEAD for an entry with `artifact_type: spec`, action `review`, as plan `8l8dgb` leaves it: list every function `execute_item_core` calls between prompt build and final disposition that resolves or reads the artifact (at authoring: `build_review_prompt`, `commit_review_lane_output` / `commit_review_shared_output` with `classify_review_writes`, the review integration ladder (`integrate_review_lane_branch`, `record_integration_refusal`), `reconcile_disposition`'s review rung, and the `--full-auto` bridge), and for each say whether it is plan-only. Confirm `review_findings.review_attestation_missing` signature `(repo_root, subject_id6, subject_type="spec")` and that `aw specs set reviewed` refuses without a record (run it on a scratch spec and paste the refusal). Confirm `/spec-review` is installed as a command shim for both hosts (`.opencode/commands/spec-review.md`, `.claude/commands/spec-review.md`) and how the agy host invokes a workflow (paste the agy review prompt shape).
  - Depends on: none
  - Expected outcome: the trace table with a plan-only column; the setter refusal pasted; both hosts' invocation shape recorded.
  - Execution state: pending

### Task group 2: dispatch

- [ ] E-02 TYPE-APPROPRIATE REVIEW PROMPT. Make the review prompt builder dispatch on `queue_entry_type(item)` (plan `8l8dgb`): `ipd` -> `/plan-review <rel>` (byte-identical to today); `spec` -> `/spec-review <rel>`; any other type -> `DriverError` naming the type (no review handler). Keep the argv-safety rule (prose never on the command line) and the lane isolation notice on its own lines. Record `review_handler` (`plan-review`/`spec-review`) on the attempt, in the item, and in the turn-start event, so `aw runs show` names which handler ran (spec 5.4 "the run record shows which handler ran"). Resolve the spec path through `queue_artifact_path`, never `resolve_plan_path`.
  - Depends on: E-01
  - Expected outcome: a spec review item's prompt file starts `/spec-review .aw/records/specs/to-review/...spec.md`; a plan review item's prompt is unchanged; the attempt carries `review_handler: spec-review`.
  - Execution state: pending

- [ ] E-03 SPEC-AWARE DISPOSITION. In `reconcile_disposition`'s review rung, for a spec entry: read the spec's current `- Status:` through `queue_artifact_path` (lane copy when isolated, as the plan branch reads `plan_repo`), and return `reviewed` ONLY when it is `reviewed` AND `review_findings.review_attestation_missing(<same tree>, id6, "spec") is None`; otherwise return `fail-gate` and record a refusal (`render_stream.record_refusal`) whose reason names the unmet half (status still `<x>`, or the attestation reason string) and whose remedy is the `/spec-review` command. A nonzero exit is `fail-gate` as today. Do NOT touch the plan branch's semantics. Ensure the `--full-auto` bridge (`is_plan_review_approved` / `set_plan_approved`) is skipped for a non-`ipd` entry, and that `item_needs_approval` for a reviewed spec reports the human gate (it keys on `action != "review"`, so confirm the spec path records the approval gate as `needs_input` in the report, per `25kzda` 3.3 "Stop `needs_input`, including under `--full-auto`").
  - Depends on: E-02
  - Expected outcome: a turn that set the spec `reviewed` with a conforming record ends `reviewed`; a turn that exited 0 but left the spec `to-review` ends `fail-gate` with a refusal naming the unchanged status; a turn that hand-edited the status to `reviewed` without a record ends `fail-gate` naming the missing attestation.
  - Execution state: pending

- [ ] E-04 SCOPE THE REVIEW OUTPUT for a spec lane. Confirm by test that `classify_review_writes(changed, id6=<spec id6>)` allows the spec file and its `.review.md` record (both carry the id6) and names anything else out of scope, and that the lane commit (`commit_review_lane_output`) and the non-isolated commit (`commit_review_shared_output`) commit exactly those. If the non-isolated path's staging is plan-shaped (its docstring: "Path-scoped to the plan under review and its review record"), generalize the wording and logic to "the artifact under review and its review record" without changing plan behavior. Integration through the review ladder (`integrate_review_lane_branch`) must treat a spec lane exactly as a plan review lane (no revalidation, `ajxr5d` OQ-01).
  - Depends on: E-03
  - Expected outcome: a spec review lane's commit contains only the spec and its review record; an extra file written by the turn is reported out of scope, as for a plan review.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 ADD `tests/test_spec_review_dispatch.py` (behavioral only; temp git repos; `AW_HOME` isolated; host spawn patched with a fake agent that performs a scripted action in the working tree). Cases on BOTH hosts: (1) a to-review spec's prompt is `/spec-review ...` and the run record's `review_handler` is `spec-review` (and a to-review plan's is still `plan-review` in the same run); (2) the fake agent writes a conforming review record and runs `aw specs set reviewed <id6>`: item ends `reviewed`, spec file in `reviewed/`; (3) REFUSAL: the fake agent exits 0 and writes nothing: item ends `fail-gate`, refusal names the unchanged status, spec still `to-review`; (4) REFUSAL: the fake agent hand-edits `- Status: reviewed` without a record: item ends `fail-gate` naming the missing attestation; (5) under `--full-auto` a reviewed spec is NOT advanced to `approved`/`auto-approved`; (6) an extra file written by the fake agent is reported out of scope and not committed.
  - Depends on: E-04
  - Expected outcome: all pass on both hosts; (1)-(4) FAIL against the pre-change code (which, after `8l8dgb`, refuses the spec item-locally as undispatchable).
  - Execution state: pending

- [ ] E-06 RUN a real `--prepare-only` scratch run over one to-review spec and one to-review plan to show both queue entries with their handlers, and run the bare suite before and after.
  - Depends on: E-05
  - Expected outcome: the frozen queue shows both review entries with their types; the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `build_review_prompt` puts only the slash command on the command line because the host passes it as ONE argv element after `--`, where extra words become `$ARGUMENTS`.
- The spec `->reviewed` attestation is ONE predicate (`review_findings.review_attestation_missing`) consulted by both `aw specs set` spellings and by `check_engine`'s spec-review-attestation rule; this plan consults the same predicate and adds none.
- `/spec-review` never approves (`spec-review.md` hard rule), and `25kzda` 3.3 forbids any automated approval of a spec, `--full-auto` included.
- Review integration is deliberately not revalidated (`integration_action_for_item`, `ajxr5d` OQ-01).
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `build_review_prompt` | Always `/plan-review`. | `command = f"/plan-review {rel_path}"` |
| F-2 | HIGH | `reconcile_disposition` review rung | Exit 0 returns `reviewed` whatever the artifact's status; resolves through `resolve_plan_path`. | "if status in (\"reviewed\", \"approved\"): return status, None / return \"reviewed\", None" |
| F-3 | HIGH | `--full-auto` bridge | Plan-only approval after review. | `is_plan_review_approved(plan_curr)` then `set_plan_approved(repo, item["id6"])` in `execute_item_core` |
| F-4 | INFO | specs setter | `to-review -> reviewed` already refuses without a conforming record. | `specs.run_set`: `auth.get("review_record")` -> `_review_attestation_refusal`; `attention_contract.TRANSITION_AUTHORITY["->reviewed"]["review_record"] is True` |
| F-5 | INFO | workflow | `/spec-review` exists with shims for both hosts. | `.opencode/commands/spec-review.md`, `.claude/commands/spec-review.md`; index row `spec-review` |

## Proposed changes (ordered, validatable)

1. E-01 traces the review path and confirms the spec-side machinery.
2. E-02 dispatches the spec review prompt and records the handler.
3. E-03 makes the disposition spec-aware and gated on the record.
4. E-04 scopes the spec review output.
5. E-05 adds behavioral tests including both refusal paths.
6. E-06 scratch run and suite.

## Deferred / out of scope (with reason)

- Reviewing a `draft` spec.
  - Carrier-Declined: requires a deterministic spec completeness parser that does not exist (`sweep_review_candidates_for_type` comment); spec `z7nbn1` 1.7 makes such an item `undetermined`, which plan `jdn790` refuses clearly.
- `--action review` re-review of a `reviewed` spec.
  - Carrier-Declined: `25kzda` 3.3's re-review row is not an acceptance criterion of spec `z7nbn1`; `enforce_requested_action` keeps refusing an illegal `--action` by name, so nothing silently misbehaves.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/review_findings.py`, `specs.py` are called, not changed; the workflow body and command shims are read, not changed.
- Scope-Paths justification: `runner_shared.py` holds the prompt builder, disposition and commit helpers; the two host modules hold any host-specific prompt spelling; the new test file holds E-05.

## Required tests / validation

- `tests/test_spec_review_dispatch.py` (new): six cases on both hosts, including the two refusal paths of spec 5.4; shown failing before the change.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` 1.6 (first bullet) and acceptance 5.4 as written, and `25kzda` 3.3's `to-review` row (run spec review, tool-set `reviewed`, stop at the approval gate). Nothing in either spec changes.
- No user-facing docs.

## Open questions

### OQ-01: Should the runner itself run `aw specs set reviewed` after the turn?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from repository evidence. `/spec-review` performs the transition itself (`spec-review.md`: "aw specs set reviewed <id6> --message ..."), exactly as `/plan-review` does for plans; the runner's job is to VERIFY the outcome (status plus the shared attestation predicate), which is what spec 5.4's refusal path tests. A runner-side setter call would let a turn that wrote no real review be advanced by the driver.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the trace table with its plan-only column, the scratch `aw specs set reviewed` refusal, and both hosts' review invocation shapes.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the prompt-builder diff, a spec review item's prompt file first line, a plan review item's prompt unchanged, and the attempt's `review_handler`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the disposition diff and the three outcomes (advanced with record, unchanged, hand-edited without record) with their refusal texts.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `classify_review_writes` result for a spec lane with one extra file, and the resulting commit's `git show --name-only`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_review_dispatch.py -q` passing with count; with E-02..E-04 reverted, cases (1)-(4) FAILING; passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the scratch run's frozen queue (types, actions) and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw <host> run reviews --type spec` (or naming a to-review spec) now actually reviews it: the runner sends the spec review workflow, not the plan review, records which handler ran, and counts the spec reviewed only if the spec really reached `reviewed` through the setter with a conforming review record. A turn that leaves no record fails the item and leaves the spec where it was. A reviewed spec always stops for human approval, `--full-auto` included. Order 04 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `jdn790` (and through it on the typed queue).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).

# IPD: Send out-of-scope edits back as revert-or-justify and record kept ones as Scope-Exceeded

- Date: 2026-10-07
- Kind: child
- Concern: When an executing agent changes a path outside its plan's `- Scope-Paths:`, the RUNNER writes the justification for it: `runner_shared.compute_scope_reconciliation` builds "changed by the plan's approved execution (auto-reconciled by <host>)" for every out-of-scope path, and `driver_finalize` passes each as `--scope-reason`, so finalize accepts and the lane is merged. The reason on record is therefore the runner's boilerplate, not the agent's judgement, and nothing marks the plan as having gone outside its scope, so the maintainer cannot track or analyse how often it happens. The maintainer ruled on 2026-10-07: send it back, let the agent revert or justify with a real reason, and flag kept edits in the artifact's metadata.
- Scope: Stop auto-writing out-of-scope reasons; send an unjustified out-of-scope delta back to the agent as a fix-it turn ("revert X, or justify it"); give the agent a way to justify a path it ALREADY committed (today's `aw commit --scope-reason` refuses a path with no new staged change) and keep recorded reasons across the recovery turn's re-`begin` (today `begin` overwrites the receipt and drops them); record every kept out-of-scope path and its reason in a new recognized plan field `- Scope-Exceeded:` written by finalize; amend the IPD structure spec to recognize the field. KEEP the additive-widening reasons and the declared-but-unmodified acks as they are (both describe declared paths, not out-of-scope edits). EXCLUDES review-turn out-of-scope warnings, any absolute ban on editing gate code (Order 03's message carries the judgement rule), and a corpus report over `Scope-Exceeded` values.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_schema.py, agent_workflows/work_cmd.py, agent_workflows/cli.py, tests/test_scope_exceeded.py, tests/test_oc_runipd.py, tests/test_finalize_sendback.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: executed:mcbph5
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 6
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: psgyzw
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009. Demonstrated on a scratch repo that the plan's own remedy could not work: `aw commit --scope-reason P=WHY -- P` on an already-committed out-of-scope path exits 1 "nothing to commit" and records no reason, and the recovery turn's re-`begin` overwrites the receipt and drops recorded reasons, so the fix-it loop could never converge (new E-06, E-07; E-02 reworded). The refusal's real summary is "finalize needs scope reconciliation answers", not the `SCOPE_REFUSAL` fixture text, and `tests/test_finalize_sendback.py` pins it NOT retryable, so that test is now in scope with its update named. A reason with an embedded newline reaches the history note verbatim, so E-03 now requires single-line sanitization before writing metadata. `aw ipd lint` today refuses the field (`IPD-M103`, measured), so V-03 needs E-03's schema entry. `aw find plans <text>` does not search metadata (measured), so E-05's "locate by field" demand is replaced. Spec-edit visibility (`record_item_spec_edits` reads the same reasons map) kept intact. Existing `test_compute_scope_reconciliation_handles_out_of_scope_and_unmodified` added to scope. Gate contract added. Review record `.aw/records/reviews/20261007-fixfirst-06-psgyzw-send-out-of-scope-edits-back-as-revert-or-justify-and-record.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An agent that edits outside its plan's scope is asked to revert or justify, writes its own reason, and the executed plan says plainly that it exceeded its scope, which paths, and why, so these cases can be found and analysed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: give the agent a working way to justify, and keep it

- [ ] E-06 Make a scope reason recordable for a path that is ALREADY committed. Today `aw commit <plan> --scope-reason P=WHY -- P` returns 1 "nothing to commit: requested path(s) have no staged changes" when `P` was committed earlier in the lane, and `work_cmd.run_commit` calls `ipd_lifecycle.record_scope_reasons` only on `STATUS_COMMITTED`, so no reason is recorded (measured at review). Add a recording-only path: `aw commit <plan> --scope-reason P=WHY` with NO paths after `--` (or an explicit `--record-only` flag, executor's choice, stated in the help text) records the reasons into the begin receipt via `record_scope_reasons` and commits nothing. Refuse (exit 2, nothing recorded) when a reason names a path that is not in the plan's current out-of-scope set as computed by `ipd_lifecycle.finalize_precheck` `scope_audit.out_of_scope_paths`, so a reason can only be written for a path this execution actually changed. Keep every existing `aw commit` behavior byte-identical when paths are given.
  - Depends on: none
  - Expected outcome: in a scratch repo after `begin` and a commit touching `OTHER.txt` outside Scope-Paths, the recording-only form exits 0 and `ipd_lifecycle.read_scope_reasons` then returns `{"OTHER.txt": <why>}`; naming a path that is not out-of-scope exits 2 and records nothing; `aw commit <plan> --scope-reason ... -- <path>` with a staged change behaves exactly as before.
  - Execution state: pending

- [ ] E-07 Keep agent-recorded scope reasons across the recovery turn's re-`begin`. `execute_item_core` calls `driver_begin` before EVERY attempt, including the fix-it re-dispatch, and `ipd_lifecycle.begin` writes a fresh receipt that drops `scope_justifications` (measured at review: reasons `{OTHER.txt, OTHER2.txt}` became `{}` after a re-`begin`). In `begin`, when a readable receipt already exists for the same `plan_id`, carry its `scope_justifications` and `scope_justifications_audit` forward into the new receipt unchanged, and do nothing else differently. A reason that names a path the new window no longer changes is harmless: finalize only consults reasons for paths it demands.
  - Depends on: none
  - Expected outcome: record a reason, re-run `begin` for the same plan, and `read_scope_reasons` still returns it; a `begin` with no prior receipt writes a receipt with no `scope_justifications` key, exactly as today.
  - Execution state: pending

### Task group 2: stop writing the agent's reasons for it

- [ ] E-01 In `compute_scope_reconciliation`, stop generating a reason for an out-of-scope path. Use only reasons the agent recorded (`ipd_lifecycle.read_scope_reasons`). Keep the widening reasons and the declared-but-unmodified acks unchanged. Change the return to a NamedTuple (or a third tuple element) that also carries the unjustified out-of-scope paths, and update its two callers (`driver_finalize`, and the `reconcile=` lambdas passed to `record_item_spec_edits` at both finalize call sites) so the end-of-run spec-edit report still lists an out-of-scope `.spec.md` path as `modified_not_declared` whether or not it is justified: pass the union of justified and unjustified out-of-scope paths as that report's `reasons` keys. Update `tests/test_oc_runipd.py` `test_compute_scope_reconciliation_handles_out_of_scope_and_unmodified`, which asserts `"OTHER.txt" in reasons` for an unjustified path, to assert the new split instead.
  - Depends on: none
  - Expected outcome: for a lane with one justified and one unjustified out-of-scope path, the function returns the agent's reason for the first and lists the second as unjustified, with no runner-written reason for either; widened and unmodified paths are handled exactly as before; an unjustified out-of-scope spec still appears as `modified_not_declared` in `item["spec_edits"]`.
  - Execution state: pending

- [ ] E-02 When unjustified out-of-scope paths remain, finalize refuses as it already does today ("finalize needs scope reconciliation answers (plan left unmoved)" with one `IPD-FINALIZE out-of-scope path needs a --scope-reason: <path>` finding per path). Admit exactly that refusal in `finalize_refusal_is_retryable` as its own arm: the summary string is matched, and EVERY finding line must be an `out-of-scope path needs a --scope-reason:` line, so a mixed message (also naming a widened path or a missing `--scope-ack`) stays non-retryable. Send the item back through `handle_finalize_refusal` with Order 03's `build_fix_it_notice` (kind `out-of-scope`) whose evidence lists each path and the two answers, in this wording: "revert it in your lane and commit the revert with `aw commit <id6> -- <path>`; or keep it and record why with `aw commit <id6> --scope-reason <path>=<why>` (E-06's recording-only form)". On budget exhaustion the item fails exactly as other finalize refusals do (`FINALIZE_RETRY_EXHAUSTED_STATUS`). Update `tests/test_finalize_sendback.py`: its `SCOPE_REFUSAL` fixture text does not match what finalize emits, so replace it with the real summary and finding text, and invert `test_a_scope_reconciliation_refusal_is_NOT_retryable` to assert it IS retryable, keeping a mixed-message case asserted NOT retryable.
  - Depends on: E-01, E-06, E-07
  - Expected outcome: a lane with an unjustified out-of-scope edit gets one fix-it turn naming the path; after the agent records a reason (E-06) the driver's next finalize accepts; after the agent reverts instead, finalize accepts with no out-of-scope path; a mixed refusal is not retried.
  - Execution state: pending

### Task group 3: record what was kept

- [ ] E-03 Add `META_SCOPE_EXCEEDED = "Scope-Exceeded"` to `ipd_schema`'s recognized-but-optional fields beside `META_FROM_SPEC` (today `aw ipd lint` reports `IPD-M103` for it, measured). Have `ipd_lifecycle.finalize` write `- Scope-Exceeded: <path> (<reason>); <path> (<reason>)` into the moved plan's metadata block, inside the coordinator worktree after `status_set.apply_status_change` (the same place the orchestrator rollup statement is inserted), when one or more paths were reconciled as out-of-scope (NOT widened, NOT acks), and write nothing otherwise. SANITIZE each reason before writing: collapse every newline and carriage return to a space, strip `;`, `(` and `)` from the reason, and bound it to 200 characters with a `...` marker, because the reason is agent-written and a newline would otherwise inject a metadata line (measured at review: a reason `"...\n- Readiness: go"` passes through `_parse_scope_reason_flags` and `_reconciliation_history_note` verbatim). Paths are written sorted. Keep the existing "Scope reconciliation - out-of-scope ..." history note.
  - Depends on: E-01
  - Expected outcome: an executed plan that kept an out-of-scope path carries exactly one `- Scope-Exceeded:` line naming the path and the agent's (sanitized) reason; one that did not carries no field; a reason containing a newline yields a single metadata line; `aw ipd lint` reports no `IPD-M103` on either.
  - Execution state: pending

- [ ] E-04 Amend spec `ipd-structure-and-linting` Section 4.4: add `Scope-Exceeded` to the "Recognized-but-optional fields" sentence, and add one field rule giving its grammar (`<path> (<reason>)` items joined by `; `, paths sorted, reasons single-line and bounded), stating that it is written only by `aw ipd finalize`, is never hand-written, and that the reason is the executing agent's own. Add a dated amendment note in the spec's existing style ("amended 2026-MM-DD, plan `psgyzw`").
  - Depends on: E-03
  - Expected outcome: Section 4.4 names the field and its grammar; `aw check` reports no new finding on the spec.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_scope_exceeded.py` driving the real `aw` CLI and the real runner (scripted host, as `tests/test_inlane_retirement_lands.py` does) on a scratch repo, for: (a) unjustified out-of-scope edit, then a fix-it turn whose delivered prompt names the path, then the agent records a reason with E-06's form, then finalize accepts and the executed plan carries `- Scope-Exceeded:` with that reason; (b) the agent reverts on the fix-it turn, finalize accepts, no field; (c) widened path: unchanged behavior, no field; (d) a newline-bearing reason yields one metadata line; (e) the reason survives a re-`begin` (E-07); (f) `aw ipd lint` on the executed plan reports no `IPD-M103`; (g) budget 0: the item fails on the first refusal with no fix-it turn. No source introspection.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the module passes; `tests/test_finalize_sendback.py` and `tests/test_oc_runipd.py` pass with only the updates E-01 and E-02 name.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A new recognized field goes in `ipd_schema` beside `META_FROM_SPEC`, so `IPD-M103` does not flag it, and value validation lives in `aw check`, not the schema.
- A spec edit is declared in `- Scope-Paths:` (AGENTS.md).
- Finalize mutates the moved plan inside a coordinator worktree (`ipd_lifecycle._finalize_transaction`, "MUTATING + READY_TO_COMMIT + the commit, ALL IN A COORDINATOR-OWNED WORKTREE"); a metadata write belongs there, not in the shared tree.
- The receipt lives at the checkout control root (`ipd_lifecycle.receipt_dir`), so an in-lane `aw commit` and the driver's finalize read the same receipt.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The runner writes the out-of-scope reasons itself. | `compute_scope_reconciliation`: `reasons = {p: f"changed by the plan's approved execution (auto-reconciled by {labels.command})" for p in out_of_scope}`; `driver_finalize` appends each as `--scope-reason`. |
| F-02 | Agents have a way to record a reason only for a path they are committing in that same call. | `aw commit --scope-reason PATH=WHY` "records it in the begin receipt for finalize to consume"; `work_cmd.run_commit` calls `record_scope_reasons` only `if outcome.status == _gch.STATUS_COMMITTED`. |
| F-03 | No metadata marks a plan that exceeded its scope; the only trace is a history note. | `ipd_lifecycle._reconciliation_history_note` renders "Scope reconciliation - out-of-scope ..." into workflow history. |
| F-04 | Maintainer ruling 2026-10-07: send it back, trust the agent's judgement with a good reason, and flag it in metadata for tracking. | Session 2026-10-07. |
| F-05 | (review PR-001) For an already-committed out-of-scope path, `aw commit <plan> --scope-reason P=WHY -- P` exits 1 "nothing to commit" and records nothing, so the original E-02 remedy could not be followed. | Review demo on a scratch repo: `aw commit on already-committed path: rc= 1 \| aw commit: nothing to commit (nothing to commit: requested path(s) have no staged changes (OTHER.txt))`; `receipt reasons after: {}`. |
| F-06 | (review PR-002) The recovery turn's re-`begin` drops recorded reasons. | `execute_item_core` calls `driver_begin` before each attempt; `ipd_lifecycle.begin` builds a fresh `receipt` dict with no `scope_justifications`. Review demo: `recorded: {'OTHER.txt': ..., 'OTHER2.txt': 'why2'}`, `re-begin: 0`, `reasons after re-begin: {}`. |
| F-07 | (review PR-003) The real refusal is "finalize needs scope reconciliation answers (plan left unmoved)" with `IPD-FINALIZE out-of-scope path needs a --scope-reason: <p>` findings; `tests/test_finalize_sendback.py` pins a different fixture text as NOT retryable. | `ipd_lifecycle.finalize` returns that summary; `tests/test_finalize_sendback.py` `SCOPE_REFUSAL` and `test_a_scope_reconciliation_refusal_is_NOT_retryable`. Review demo: `no reason: 1 \| finalize needs scope reconciliation answers (plan left unmoved). \| ('out-of-scope path needs a --scope-reason: OTHER.txt',)`. |
| F-08 | (review PR-004) An agent-written reason containing a newline passes through verbatim. | Review demo: `_parse_scope_reason_flags(["A.txt=ok\n- Readiness: go"])` returns `{'A.txt': 'ok\n- Readiness: go'}`; the history note carries it unchanged. |

## Proposed changes (ordered, validatable)

1. A recording-only `aw commit --scope-reason` for already-committed paths (E-06).
2. Keep recorded reasons across re-`begin` (E-07).
3. Use only the agent's reasons; return unjustified paths (E-01).
4. Send unjustified edits back as a retryable finalize refusal (E-02).
5. `- Scope-Exceeded:` written by finalize, sanitized (E-03).
6. Spec recognizes the field (E-04).
7. Tests (E-05).

## Deferred / out of scope (with reason)

- A report over all plans' `Scope-Exceeded` values. The field is grep-able in tracked files today; `aw find plans <text>` does NOT search metadata values (measured at review), so a query verb is real follow-up work, not existing capability.
  - Carrier-Declined: no defect is deferred; the field is the deliverable and is greppable; a query surface is a feature to request once there is data.

## Scope check

- Over-scope: none. `runner_shared.py` E-01, E-02; `ipd_lifecycle.py` E-03, E-07; `ipd_schema.py` E-03; `work_cmd.py` and `cli.py` E-06; the spec E-04; `tests/test_scope_exceeded.py` E-05; `tests/test_oc_runipd.py` E-01; `tests/test_finalize_sendback.py` E-02.
- Under-scope: a path whose ownership cannot be established is still DISREGARDED by finalize's attribution (`_disregarded_history_note`) and is not demanded; that is unchanged and owned by backlog `s9z85a`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_scope_exceeded.py tests/test_finalize_sendback.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_finalize_stale_plan_path.py`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.
- `aw ipd lint` on an executed plan carrying the field.

## Spec / documentation sync

THIS PLAN AMENDS spec `ipd-structure-and-linting` (implemented, legacy-named, no `- Id:`), declared in `- Scope-Paths:`, because it adds a recognized metadata field and the spec's Section 4.4 is the list of recognized fields. The amendment adds one field and changes nothing else. The `aw commit` help text for the new recording-only form is updated in `cli.py` (E-06). Spec `25kzda` 5.5's out-of-scope class is amended by Order 01 (`tb6lw3`), not here.

## Open questions

### OQ-01: Should the field be a list of paths or a yes/no flag?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: Paths with reasons. The maintainer wants to "track these things and analyze them", which needs what and why, not only whether.

### OQ-02: How does an agent justify a path it already committed?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: A recording-only `aw commit --scope-reason` that commits nothing and refuses a path not in the current out-of-scope set (E-06). Demonstrated at review that the existing form cannot do it (F-05) and that `ipd_lifecycle.finalize` accepts an agent-supplied reason for a committed out-of-scope path (`agent reason: 0 | precheck + reconciliation passed`), so recording into the receipt, which finalize already merges (`effective_scope_reasons = {**receipt_reasons, **(scope_reasons or {})}`), is sufficient. Recorded as decision D-1 in the review record.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing the function's output for the justified, unjustified, widened and unmodified cases, showing no runner-written reason; and the `item["spec_edits"]` record for an unjustified out-of-scope `.spec.md` showing it under `modified_not_declared`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the delivered fix-it prompt naming the path and both answers; the finalize result after the agent recorded a reason; the result after a revert; `finalize_refusal_is_retryable` on the real refusal text (True) and on a mixed message (False); and the `tests/test_finalize_sendback.py` diff.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the executed plan's metadata block showing one `- Scope-Exceeded:` line (including the newline-reason case) and `aw ipd lint` on it showing no `IPD-M103`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff and `aw check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module runs with per-test counts (from the Required tests command) and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the scratch-repo transcript: the recording-only form exiting 0 and `read_scope_reasons` showing the reason; a non-out-of-scope path exiting 2 with nothing recorded; the unchanged with-paths form.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `read_scope_reasons` before and after a re-`begin` showing the reason kept, and a fresh receipt's keys showing no `scope_justifications`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `mcbph5` has executed (`- Item-Dependencies:`), because E-02 sends its notice through `build_fix_it_notice`.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.

# IPD: Report a stranded lane honestly instead of as a completed run

- Date: 2026-09-06
- Kind: child
- Concern: When a lane's integration is not earned, every report the operator sees is technically true and practically misleading. MEASURED on run `run-20260907T010730Z-3199043` (`mm6wuz`), which left 2164 insertions across 10 files on a branch and reached main only through a hand recovery: the exit summary printed `Outcome: COMPLETED   Duration: 1h 36m 25s   Spend: $39.42` and `Progress: 1/1 [##########] 100% (1 substantially-complete)`. A run whose entire product was stranded reported COMPLETED at 100 percent, in green.
  THE MECHANISM IS A MISSING QUESTION, NOT A WRONG ANSWER. `render_run_summary_table` derives its outcome purely from per-item STATUS (`render_stream.py:1795-1803`): if every item is in `("executed", "reviewed", "approved", "substantially-complete")` the outcome is `COMPLETED`, and `substantially-complete` is in that tuple. Nothing in that computation asks whether the work INTEGRATED, so a stranded lane and a landed one are indistinguishable to it.
  THREE INDEPENDENT MISREPORTS, each separately fixable, all from the same incident. (1) The disposition downgrade is SILENT: the outcome file says `'disposition': 'executed'` and `reconcile_disposition` overrides it to `substantially-complete` because `plan_bucket() != "executed"` (`oc_runipd.py:5814-5822`). That override is CORRECT as an anti-fabrication guard and must stay, but a reader comparing the two records finds a contradiction with no explanation. (2) The integration verdict is DISCARDED: `attempt["integration"]` is `None` in the run state and no event names the gate's decision, while `suite_check` IS persisted (`{'passing': False, 'exit_code': 1}`), so the record holds the INPUT to the decision and not the decision. (3) `Outcome: COMPLETED` contradicts `aw runs <id>`, which DOES surface the truth in its discrepancy table (`Expected executed/ | Actual pending/`) and is how the maintainer caught this at all.
  WHY THIS MATTERS MORE THAN THE GATE BUG IT REPORTED ON. Sibling child `32ij2j` fixes WHY integration was not earned. The gate will be wrong again for some new reason; what must not recur is a report that hides it. An operator or agent reading only the summary would reasonably conclude the work had landed, and the honest signal lives in a different command that one must already suspect a problem to run.
- Scope: Make the run's own reporting tell the truth about integration: persist the integration verdict and its reason, record the disposition downgrade with its cause instead of silently replacing the value, emit an event for a not-earned decision, and give the exit summary a distinct outcome for "verified but NOT integrated" that names the recovery route. Do NOT weaken the anti-fabrication override; only its silence is the defect.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/run_viewer.py, tests/test_render_stream.py, tests/test_run_viewer.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Set: integearn
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xtklpd
- From-Backlog: 7m0aro
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `7m0aro`, filed from the same measured incident as its sibling: a $39.42 lane reported COMPLETED at 100 percent while all of its work sat on a branch. Every claim re-verified against code at HEAD `6f62419b` rather than trusted. CONFIRMED: the outcome string is computed from per-item status alone (`render_stream.py:1795-1803`) with `substantially-complete` inside the COMPLETED tuple and no integration term anywhere in the expression; `COMPLETED` is additionally rendered GREEN (`:1817-1819`), so the visual signal agrees with the wrong verdict. FOUND WHILE AUTHORING, and it makes the fix much smaller than the backlog item assumed: `run_viewer.audit_step_artifact` (`:465`) ALREADY computes exactly the missing fact, returning a `StepArtifactAudit` (`:425-435`) carrying `location_mismatch`, `expected_dir` and `actual_dir`, and `format_discrepancy_table` (`:1341`) already renders it. So the truth is already computed and already displayed in ONE view; the defect is that the exit summary does not consume it. That reframes E-04 from "compute integration state" to "consume the existing audit", which is why this plan does not add a second source of truth. DELIBERATELY NOT IN SCOPE: why integration was not earned is `32ij2j` (integearn-01); this child assumes the gate may refuse for ANY reason and only insists the refusal be visible.

## Goal

Make a run that strands its work say so, in the place the operator actually looks, so a near-total loss can never again read as a completed run at 100 percent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop discarding what the runner already decided

- [ ] E-01 Persist the INTEGRATION VERDICT and its reason onto the attempt record, on BOTH the earned and not-earned paths. Today `attempt["integration"]` is `None` after a not-earned decision, while `attempt["suite_check"]` IS written, so the record keeps the decision's INPUT and drops the decision itself.
  `IntegrationVerdict` ALREADY CARRIES THE REASON, so this is persistence rather than new computation. Write the verdict's `earned` boolean and its reason string; sibling `32ij2j` enriches that reason with the failing-set delta, and this item must not assume any particular reason TEXT, only that a reason exists.
  KEEP THE EXISTING KEYS AND THEIR MEANINGS. `suite_check` and `integration_deferral` are already read by other code and by tests; add to the attempt record rather than repurposing a field.
  - Depends on: none
  - Expected outcome: `attempt["integration"]` holds the verdict and reason on both paths; no existing key changes meaning; a run whose integration was refused records WHY.
  - Execution state: pending

- [ ] E-02 Emit a DURABLE EVENT for a not-earned integration decision, so the event log shows the fork rather than falling silent. MEASURED: `mm6wuz`'s log ends `lane-submissions-collected` / `worktree-preserved` / `ipd-finished` and `grep -c integrat events.jsonl` returns 0, so nothing records that an integration decision was even reached.
  FOLLOW THE EXISTING EVENT SHAPE, including a `detail` field. Every neighbouring event type carries one; the `dependency-blocked` event's lack of a detail is the same defect one layer over (backlog `phawyy`), so do not reproduce it here.
  NAME THE LANE AND THE RECOVERY ROUTE in the detail, because an event a reader cannot act on is only marginally better than silence: state the preserved branch and that the work is recoverable from it.
  - Depends on: E-01
  - Expected outcome: a `not-earned` integration decision emits an event carrying the id6, the reason, and the preserved lane branch; the event log no longer goes silent at the fork.
  - Execution state: pending

- [ ] E-03 Record the DISPOSITION DOWNGRADE explicitly instead of silently replacing the value. `reconcile_disposition` (`oc_runipd.py:5814-5822`) reads `plan_bucket(current_plan)` and, when the plan is not in `executed/`, overrides an outcome file claiming `disposition: executed` down to `substantially-complete`.
  THE OVERRIDE IS CORRECT AND MUST NOT BE WEAKENED. The runner must not take an agent's word that a plan was finalized; that is the anti-fabrication guard, and this repository's history of agents over-claiming completion is exactly why it exists. This item changes only its SILENCE.
  WRITE THE FACT AND THE CAUSE, for example an `attempt["disposition_downgraded"]` naming the claimed value, the recorded value, and the observed reason (the plan's actual bucket). A reader comparing the outcome file against the queue entry must find an explanation rather than a bare contradiction.
  DO NOT DERIVE THE CAUSE FROM A GUESS. The bucket is the observed fact the override actually used; record that, not an inference about why finalize did not run.
  - Depends on: E-02
  - Expected outcome: a downgrade is recorded with the claimed value, the recorded value and the observed bucket; the override's behavior is byte-identical to today.
  - Execution state: pending

### Task group 2: make the summary agree with the truth

- [ ] E-04 Give `render_run_summary_table` a DISTINCT OUTCOME for "verified but NOT integrated", by consuming the audit that already exists rather than adding a second source of truth. Today the outcome is computed from per-item status alone (`render_stream.py:1795-1803`) and `substantially-complete` sits inside the COMPLETED tuple, so a stranded lane is indistinguishable from a landed one.
  THE FACT IS ALREADY COMPUTED, which is the finding that shapes this item: `run_viewer.audit_step_artifact` (`:465`) returns a `StepArtifactAudit` (`:425-435`) carrying `location_mismatch`, `expected_dir` and `actual_dir`, and `format_discrepancy_table` (`:1341`) already renders it. So `aw runs <id>` already tells the truth in one view. Consume that audit; do NOT reimplement the check, or the two views can disagree again in a new way.
  FIX THE COLOR TOO. `COMPLETED` is rendered green (`:1817-1819`), so today the visual signal reinforces the wrong verdict. A stranded outcome must not be green.
  NAME THE RECOVERY ROUTE in the summary, since a bare label leaves the operator stuck: state that the lane branch is preserved and how to recover (the `integrate` verb once `yocdq4` lands, the preserved branch meanwhile).
  BE CAREFUL WITH THE PRECEDENCE ORDER. The existing expression checks FAILED, then BLOCKED, then COMPLETED, then PARTIAL, then QUEUED. A stranded run must not mask a genuine FAILED or BLOCKED verdict; place the new outcome so those still win.
  - Depends on: E-03
  - Expected outcome: a run whose items are `substantially-complete` with a location mismatch reports a distinct non-green outcome naming the stranded state and the recovery route; FAILED and BLOCKED still take precedence; the audit is consumed rather than duplicated.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Test the RECORD, deterministically and without running a real lane. Assert: a not-earned decision writes `attempt["integration"]` with a reason; an earned one writes it too; the not-earned event exists and carries a `detail` naming the lane branch; a downgrade writes the claimed value, the recorded value and the observed bucket; and `reconcile_disposition`'s RETURN VALUE is unchanged for every input it handles today.
  THE LAST ASSERTION IS THE SAFETY ONE. This item touches the anti-fabrication override, so a test must prove the override still downgrades exactly as before. Drive it with an outcome file claiming `executed` and a plan in `pending/`, and assert `substantially-complete` is still returned.
  ASSERT BACKWARD COMPATIBILITY: an OLDER run record lacking every new key must still render without raising, which is the rule the `launch_profile` record already follows.
  - Depends on: E-04
  - Expected outcome: the verdict, the event, and the downgrade record are each pinned; the override's return values are unchanged; an older record still renders.
  - Execution state: pending

- [ ] E-06 Test the SUMMARY against the real incident, so the test documents the bug it prevents. Reconstruct `mm6wuz`'s shape: one item, status `substantially-complete`, plan in `pending/` while the audit expects `executed/`. Assert the summary does NOT say `COMPLETED`, does NOT render green, names the stranded state, and names the recovery route.
  ASSERT THE CONTRAST, which is what makes the test meaningful: the SAME item with the plan actually in `executed/` must still report `COMPLETED` and stay green. A test that only checks the stranded case would pass if the outcome were hardcoded to the new label.
  ASSERT PRECEDENCE with a mixed queue: one stranded item plus one genuinely failed item must report FAILED, not the stranded label.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. VALIDATE IN THE REAL CHECKOUT: `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/`, so it fails in a bare worktree and passes in the real checkout; green elsewhere proves nothing, and that file is in this plan's Scope-Paths.
  - Depends on: E-05
  - Expected outcome: the incident's shape reports honestly and non-green; the landed case still reports COMPLETED; FAILED still wins in a mixed queue; bare suite green with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE OUTCOME STRING IS COMPUTED FROM STATUS ALONE. `render_stream.py:1795-1803` tests membership in `("executed", "reviewed", "approved", "substantially-complete")` and has no integration term, which is the entire defect. `COMPLETED` is then colored green at `:1817-1819`.
- THE MISSING FACT IS ALREADY COMPUTED ELSEWHERE. `run_viewer.audit_step_artifact` (`:465`) maps `substantially-complete` to `complete`, expects `executed/`, and returns `location_mismatch` plus `expected_dir`/`actual_dir` on a `StepArtifactAudit` (`:425-435`); `format_discrepancy_table` (`:1341`) renders it. Consume it rather than recomputing.
- `substantially-complete` IS IN `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:321`), so it legitimately reads as a success variant. The fix is not to reclassify the status but to stop treating success-of-the-turn as success-of-the-run.
- THE ANTI-FABRICATION OVERRIDE IS DELIBERATE. `reconcile_disposition` trusts the DIRECTORY over the agent's outcome file. Keep it; record it.
- THE ATTEMPT RECORD ALREADY PERSISTS DECISION INPUTS (`suite_check`) and already has a place for the decision (`attempt["integration"]`, currently `None`), so persistence needs no new structure.
- EVENTS CARRY A `detail` FIELD BY CONVENTION, and the `dependency-blocked` event's lack of one is a known defect (`phawyy`). Do not add a second detail-less event.
- BACKWARD COMPATIBILITY RULE: `run_viewer` must read a new field defensively so an older record still renders, as the `launch_profile` record already requires.
- `tests/test_run_viewer.py` READS THE GITIGNORED `.aw/records/runs/`, so it must be validated in the REAL checkout, not a bare worktree.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **THE MISREPORT, MEASURED.** A run that stranded 2164 insertions across 10 files printed `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 substantially-complete)`, `Spend: $39.42`. | `run-20260907T010730Z-3199043` exit summary |
| F-2 | The outcome is derived from per-item STATUS with no integration term, and `substantially-complete` is inside the COMPLETED tuple. | `render_stream.py:1795-1803` |
| F-3 | `COMPLETED` is rendered GREEN, so the visual signal reinforces the wrong verdict. | `render_stream.py:1817-1819` |
| F-4 | **THE MISSING FACT IS ALREADY COMPUTED AND ALREADY DISPLAYED IN ONE VIEW**, which makes this fix a consumption change rather than a new mechanism: `audit_step_artifact` returns `location_mismatch`/`expected_dir`/`actual_dir`, and `format_discrepancy_table` renders `Expected executed/ | Actual pending/`. That table is how the maintainer caught the incident. | `run_viewer.py:465`, `:425-435`, `:1341` |
| F-5 | The integration verdict is DISCARDED while its INPUT is kept: `attempt["integration"]` is `None` and `attempt["suite_check"]` is `{'passing': False, 'exit_code': 1}`. | `mm6wuz` state.json attempt record |
| F-6 | NO EVENT RECORDS THE FORK: the log ends at `worktree-preserved` / `ipd-finished` and `grep -c integrat events.jsonl` returns 0. | `run-20260907T010730Z-3199043` events.jsonl |
| F-7 | THE DOWNGRADE IS SILENT AND CONTRADICTORY: the outcome file says `disposition: executed`, the queue entry says `substantially-complete`, and nothing records that an override occurred or why. | `oc_runipd.py:5814-5822`; `mm6wuz` outcome vs queue entry |
| F-8 | The override reads the DIRECTORY, which is the same bucket-versus-status confusion filed as `yf9fj9` for the dependency gate. Recording the observed bucket keeps this plan honest about what the override actually used. | `oc_runipd.py:5815`; backlog `yf9fj9` |
| F-9 | `substantially-complete` is a legitimate success variant (`EXECUTION_SUCCESS_STATES`), so the fix must not reclassify the status; only the run-level verdict is wrong. | `oc_runipd.py:321` |

## Proposed changes (ordered, validatable)

1. Persist the integration verdict and reason on both paths (E-01).
2. Emit a not-earned integration event carrying a `detail` that names the lane and the recovery route (E-02).
3. Record the disposition downgrade with its claimed value, recorded value and observed bucket, leaving the override's behavior unchanged (E-03).
4. Give the summary a distinct non-green outcome for a stranded run by consuming the existing audit, preserving FAILED/BLOCKED precedence (E-04).
5. Pin the record: verdict, event, downgrade, unchanged override return values, older-record rendering (E-05).
6. Pin the summary against the real incident plus the landed contrast and the precedence case (E-06).

## Deferred / out of scope (with reason)

- WHY INTEGRATION WAS NOT EARNED. That is sibling `32ij2j` (integearn-01), which changes the gate from absolute-green to a delta against the frozen base. This child deliberately assumes the gate may refuse for ANY reason and only insists the refusal be visible, so the two can be reviewed and verified independently.
- WEAKENING OR REMOVING THE ANTI-FABRICATION OVERRIDE. Explicitly counter to the goal: the override is right, its silence is the defect.
- RECLASSIFYING `substantially-complete`. It is in `EXECUTION_SUCCESS_STATES` and legitimately describes the TURN's outcome; changing its membership would ripple through dependency satisfaction and retry eligibility for no gain here.
- THE `dependency-blocked` EVENT'S MISSING REASON. Same class of defect, different code path, already filed as `phawyy`. Named here so the executor does not fix half of it incidentally and leave the record inconsistent.
- THE `integrate` VERB the summary will point at. That is `yocdq4` (integpath Set). This plan names the recovery route in prose and must degrade gracefully while that verb does not exist.
- THE STALE-BASE SCOPE MISATTRIBUTION (`hyx1dg`). Same incident, unrelated mechanism.

## Scope check

- Over-scope: none. Two drivers, the summary renderer, the viewer, and three test modules.
- Scope-Paths justification: `oc_runipd.py` holds `reconcile_disposition` and the attempt record (E-01, E-03) plus the event emission (E-02); `agy_runipd.py` needs the same three changes at its own sites; `render_stream.py` holds the outcome computation and its color (E-04); `run_viewer.py` holds the audit being consumed and must read new fields defensively; `tests/test_render_stream.py` covers the summary, `tests/test_run_viewer.py` the audit consumption, `tests/test_oc_runipd.py` the record and the override.
- BOTH DRIVER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPOSITORY. Expect drift and re-locate by symbol.
- Under-scope, stated rather than left as `none`: this child does not change WHEN integration is earned, does not touch the override's behavior, does not reclassify any status, does not fix the `dependency-blocked` event, and does not build the `integrate` verb. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE: at authoring it is `1 failed, 5612 passed, 3 skipped, 2 xfailed` at HEAD `6f62419b`, the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`. The criterion is that the AFTER failure set minus the BEFORE failure set is EMPTY.
- Targeted: `tests/test_render_stream.py`, `tests/test_run_viewer.py`, `tests/test_oc_runipd.py`.
- VALIDATE `tests/test_run_viewer.py` IN THE REAL CHECKOUT. It reads the gitignored `.aw/records/runs/` and fails in a bare worktree; it is in this plan's Scope-Paths, so a bare-worktree run would report a false failure.
- A RENDERED-OUTPUT PASTE of the summary for the stranded case AND the landed case, side by side, with ANSI stripped so the color difference is visible as a code rather than as a claim.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda` governs the run's reporting surface. This plan ADDS an outcome label and record fields; if the spec enumerates run outcomes, the new one must be reflected there, and if it does not, no spec change is needed. Verify by reading rather than assuming, and do NOT edit the spec's §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

`render_run_summary_table`'s docstring must state that the outcome now depends on integration state and not on item status alone, since that docstring is where a future reader will look to understand the verdict.

Any user-facing text describing the new outcome must name the recovery route plainly and must not imply the work is lost: the lane branch is preserved and the commits are recoverable. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: What should the new outcome be called?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A LABEL THAT NAMES THE STATE, not a severity word. The operator's question is "did my work land", so the label must answer it: something of the form `NOT INTEGRATED` (optionally qualified, e.g. `VERIFIED, NOT INTEGRATED`) rather than `WARNING` or `PARTIAL`. `PARTIAL` is already taken by a different meaning in the same expression (some items completed, others did not) and reusing it would collapse two distinct facts. The exact string is the executor's choice within that constraint; what E-06 pins is that it is NOT `COMPLETED`, is NOT green, and names both the stranded state and the recovery route.

### OQ-02: Should a stranded run exit nonzero?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: OUT OF SCOPE FOR THIS PLAN, and deliberately not changed. Exit codes are a contract other tooling and CI may already depend on, and spec `25kzda` owns the run's exit-code table; changing one is a separate, wider decision with its own compatibility surface. This plan fixes what the run SAYS, which is the defect that cost a near-total loss its visibility. If the maintainer wants a nonzero exit for a stranded run, that is a follow-up item against the exit-code table, and it should be decided with the spec in hand rather than as a side effect of a reporting fix.

### OQ-03: Should the summary consume `run_viewer`'s audit directly, given `render_stream` does not import it today?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, CONSUME THE EXISTING AUDIT, and if the import direction is awkward, pass the audit RESULT in rather than reimplementing the check. The requirement that matters is ONE source of truth for "did this land": the incident happened because two views disagreed, and adding a third computation would make that worse. If `render_stream` must stay free of a `run_viewer` import, the caller that already has both should compute the audit and hand the summary a boolean plus the expected/actual directories. What is forbidden is a second independent implementation of the location check.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `attempt["integration"]` from a real run state for BOTH an earned and a not-earned decision, each carrying a reason. Confirm `suite_check` and `integration_deferral` are unchanged in shape and meaning by pasting them alongside. State in one sentence why the reason text is not asserted verbatim (sibling `32ij2j` enriches it).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new event line from a real `events.jsonl` for a not-earned decision, showing the id6, the reason, and the preserved lane branch in its `detail`. Paste `grep -c integrat events.jsonl` returning nonzero for that run, contrasted with the measured 0 from `run-20260907T010730Z-3199043`. Confirm the event carries a `detail` field, naming the `phawyy` defect this avoids repeating.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the downgrade record showing the claimed value (`executed`), the recorded value (`substantially-complete`), and the OBSERVED BUCKET. THEN paste the safety proof: `reconcile_disposition` driven with an outcome file claiming `executed` and a plan in `pending/` still returns `substantially-complete`, byte-identical to today. A paste that does not demonstrate the override still firing is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rendered summary (ANSI STRIPPED, and separately the raw escape codes) for a stranded run, showing the outcome is NOT `COMPLETED`, is NOT green, and names both the stranded state and the recovery route. Paste the code showing the existing audit is CONSUMED and quote the line proving no second location check was written. Paste the precedence case: a queue with one stranded item and one failed item reports FAILED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL output of the record tests: verdict on both paths, the event with its detail, the downgrade record, and the unchanged-override assertion. Paste the backward-compatibility test rendering an OLDER run record that lacks every new key, still passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the incident-shaped test (one item `substantially-complete`, plan in `pending/`, audit expecting `executed/`) and its assertions. Paste the CONTRAST case with the plan actually in `executed/` still reporting `COMPLETED` and still green; without that contrast the test would pass on a hardcoded label. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is empty. State that `tests/test_run_viewer.py` was validated in the REAL checkout and why that matters here.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the seven paths in `Scope-Paths`. Do NOT change WHEN integration is earned (that is `32ij2j`). Do NOT weaken, bypass, or remove the `reconcile_disposition` override. Do NOT reclassify `substantially-complete` or alter `EXECUTION_SUCCESS_STATES`. Do NOT change any run exit code (OQ-02). Do NOT write a second implementation of the artifact-location check. Do NOT edit spec `25kzda`, and never its finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and both driver modules are the highest-contention files in it: run `aw runs` before starting, and if a driver file is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. Judge yourself on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `render_run_summary_table`'s outcome expression, `reconcile_disposition`, `audit_step_artifact`, `StepArtifactAudit`, and `format_discrepancy_table` by name.

THE ITEM THAT MATTERS MOST IS V-06's CONTRAST PASTE. This plan's claim is that a stranded run and a landed run now report DIFFERENTLY. A test that only exercises the stranded case would pass if the label were hardcoded, and a test that only exercises the landed case would pass if nothing changed. Both must be shown, from the same code path.

DO NOT SOLVE THIS BY MAKING THE SUMMARY PESSIMISTIC. A label that says NOT INTEGRATED whenever it is unsure would be as useless as one that always says COMPLETED, and it would train operators to ignore it. The verdict must follow the observed artifact location, which is why E-04 consumes the audit instead of guessing.

On completion, close backlog `7m0aro`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits.

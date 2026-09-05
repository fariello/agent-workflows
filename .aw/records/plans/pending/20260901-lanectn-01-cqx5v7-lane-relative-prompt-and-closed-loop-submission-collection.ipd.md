# IPD: Lane-relative prompt and closed-loop submission collection

- Date: 2026-09-01
- Kind: child
- Concern: An isolated turn's prompt emits FIVE absolute paths outside the lane and then declares them authorized exceptions, so the worker must resolve a self-contradiction on every turn (spec `7ckptx` R1.1, R1.2). Removing the paths alone is NOT safe: the driver's reconciliation reads the run directory, so an obedient worker's lane-side outcome would never be found and a successful turn would silently never finalize (R2.1).
- Scope: Make every worker-facing path in an isolated prompt lane-relative, DELETE the exception clause, and in the SAME plan collect the worker's submissions back to the paths the driver already reads. Implements spec `7ckptx` R1.1, R1.2, R1.3, R1.4, R2.1, R2.2, R2.3, R2.4 and nothing else. Also implements R2.5 (an authoritative attempt-keyed collection record, which `xdr83v` consumes) and R2.6 (the declared shared-code home, created here as `agent_workflows/lane_containment.py`).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_prompt_purity.py, tests/test_lane_submission_collection.py
- Item-Dependencies: none
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: reviewed
- Readiness: go-pending-approval
- Set: lanectn
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: cqx5v7

## Workflow history
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED; round 2 is a DISCLOSED SELF-REVIEW (I authored this plan, so it is weaker evidence than round 1, which was independent and performed by codex/gpt-5). Round 1's PR-* findings were all resolved and moved to FIXED in the typed review record; round 2 then found 2 further findings, SR-002, SR-003 (both FIXED), of which four across the Set were defects I INTRODUCED while fixing round 1. Round 2 is appended to the plan-specific typed review record.
- 2026-09-01 reviewed (aw set): /aw plan-review round 1 complete; all findings ACCEPTED and resolved. Every one was verified against the artifact before fixing. Two were serious: (1) my orchestrator claimed a proven-complete dependency graph while two children's metadata omitted edges their own prose required, which is the same CLASS of defect that got the predecessor tch3bo rejected - the proof had checked acyclicity only and never metadata-vs-prose agreement; (2) the spec's secret vocabulary was derived from THIS repository's ignore file with no floor, which would admit secrets in a managed target repo, fixed by a maintainer-approved spec amendment adding a built-in floor, union-only composition, and fail-closed behavior. Also fixed: the right-sizing complaint that I complied on E-item count while hiding each second driver's whole implementation in one 'mirror' item (now host-neutral code plus thin adapters), stale hardcoded suite baselines (now measure-at-execution-time and compare failures by identity), a genuine data-model error where retention read the input manifest for OUTPUT collection state (now an attempt-keyed collection receipt owned by the plan that owns collection), and an unfollowable instruction to read docstring owner labels that name superseded phases (now a measured predicate ownership table).

- 2026-09-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): first child of Set `lanectn`, tracing to approved spec `7ckptx`. Deliberately small: 5 E-items, two files of product code, two new test files. R1 and R2 are together in THIS plan because spec R2.1 makes shipping them together normative; splitting them is the invisible-failure mode recorded there.
- 2026-09-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

An isolated turn is told exactly one thing about where it may work, and everything it writes is still found by the driver.

Concretely: the emitted prompt contains ZERO absolute paths outside the lane root, no sentence authorizes an exception, the worker is told the ONE form for reporting a missing input, and the driver collects the worker's submissions to its own read locations before computing the turn's disposition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

HOST-NEUTRAL FIRST, ADAPTERS SECOND. Corrected after `/aw plan-review` finding PR-001, which was right: the original E-05 compressed the whole second driver into one "mirror" item spanning path projection, exception removal, collection timing, and idempotency, so it could be checked off while one property was still absent. Smaller by COUNT is not smaller by SUBSTANCE. So E-01 through E-04 MUST place their logic in host-neutral functions that BOTH drivers call, and E-05 is reduced to wiring plus event-shape adaptation. The precedent is established: the two drivers already share ten modules including `worktree_lease`, `ipd_lifecycle`, and `runner_stop`. If a behavior genuinely cannot be made host-neutral, say so explicitly in that E-item's outcome and explain why, rather than silently duplicating it.

THE SHARED HOME IS NAMED, and is `agent_workflows/lane_containment.py` (declared first in this plan's `Scope-Paths`). Added 2026-09-01 after a self-review found that requiring host-neutral code while the fence named only the two driver modules told the executor to do something the fence forbade. Put the host-neutral functions THERE. Do NOT improvise a home by putting them in one driver and importing from the other: that makes one host the de-facto shared library, which is the opposite of host-neutral, and spec R2.6 forbids it. If the module does not exist yet, the plan that reaches it first CREATES it; a later plan EXTENDS it.

DO NOT SPLIT THIS PLAN, and do not land E-01 in a commit that does not also contain E-03. Spec R2.1 is normative on this point: a lane-relative instruction whose output nobody collects fails INVISIBLY (the worker writes inside the lane, reconciliation reads the run directory, finds nothing, scores the turn from the empty-outcome fallback, and that disposition is outside the gating set, so a fully successful turn never finalizes). That is worse than the contradiction being removed.

### Task group 1: lane-relative paths (R1)

- [ ] E-01 IMPLEMENTS R1.1, R1.3. In `oc_runipd.build_prompt`, compute the worker-facing paths (plan file, run directory, decisions register, outcome JSON, driver report) RELATIVE to the lane root when the turn is isolated, keyed so a resumed run, a retry, and a co-resident lane cannot collide. Leave the non-isolated branch byte-identical: pass a lane root of `None` and the emitted string must be unchanged.
  - Depends on: none
  - Expected outcome: for an isolated item the returned string contains no substring matching an absolute path outside the lane root; for a non-isolated item the returned string is byte-identical to the pre-change output for the same inputs.
  - Execution state: pending
- [ ] E-02 IMPLEMENTS R1.2, R1.4. DELETE the exception clause from the isolation notice, verbatim the sentence beginning "When a path below is given as an absolute path outside the lane" and ending "you write them exactly as given" (`oc_runipd.build_isolation_notice`). Keep the rest of that block: it is main's own plain-language statement of the rule and it is not the defect. Then ensure the notice states that the cwd is the complete authorized workspace AND names the exact missing-input token form, so the strictness from E-01 ships with its escape hatch.
  - Depends on: E-01
  - Expected outcome: the exception sentence is absent from the module; the emitted isolated prompt contains the workspace statement and the literal missing-input token form.
  - Execution state: pending

### Task group 2: close the loop (R2)

- [ ] E-03 IMPLEMENTS R2.1, R2.2, R2.4. Add a collection step that COPIES (never moves) the worker's lane-side submissions to the exact paths the driver already reads, and call it in `execute_item` IMMEDIATELY BEFORE `reconcile_disposition`. A turn that wrote nothing must reconcile to the existing empty-outcome fallback without raising.
  - Depends on: E-01
  - Expected outcome: after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns that disposition and the file exists at the driver-side path; the lane retains its own copy; a turn with no submission still reconciles without error.
  - Execution state: pending
- [ ] E-06 IMPLEMENTS R2.5, R2.6. EMIT AN AUTHORITATIVE COLLECTION RECORD, and create the shared home. Added after `/aw plan-review` on child `xdr83v` (finding PR-001), and given a spec basis on 2026-09-01 as R2.5 after a self-review found this obligation had none - the same PR-005 class of defect the predecessor was rejected for. R2.6 is cited here because this plan is first in the Set and therefore CREATES `agent_workflows/lane_containment.py`. That review established that the sealed input manifest CANNOT answer "was this lane's submission collected?": the manifest records materialized INPUTS (R5.1), while collection is R2 OUTPUT, so they are different data. Without a receipt, `xdr83v`'s retention classification would have to GUESS from path presence, which either preserves every successful lane forever or deletes output whose collection failed. So this item, which owns collection, must record the fact: for each attempt, write an attempt-keyed receipt naming what was collected, its source digest, and the destination result (success or failure with a reason). Absence of a receipt means NOT collected; it must never be inferred from a file existing somewhere.
  - Depends on: E-03
  - Expected outcome: after a collection attempt, an attempt-keyed receipt records each submission's source digest and destination result; a FAILED collection is recorded as failed rather than omitted; and a consumer can distinguish collected, uncollected, and failed-collection without inspecting the run directory's contents.
  - Execution state: pending
- [ ] E-04 IMPLEMENTS R2.3. Make collection IDEMPOTENT for the run-wide decisions register, which is APPENDED to and shared by every item. Choose ONE mechanism and state which in the code comment: key the appended block to the attempt, or write deterministic per-lane files that are concatenated on read. Retry is a real path, not hypothetical: `requeue_interrupted` re-queues interrupted items for recovery.
  - Depends on: E-03
  - Expected outcome: running the same attempt's collection twice leaves the lane's contribution present exactly once; a sibling lane's contribution is still present after both runs.
  - Execution state: pending
- [ ] E-05 WIRE THE AGY TWIN TO THE SHARED CODE. E-01 through E-04 put the path projection, the exception removal, the collection, and the idempotency into HOST-NEUTRAL functions (see the preamble); this item only CALLS them from `agy_runipd.py` and adapts that host's event shapes. It is deliberately a thin adapter, NOT a second implementation: re-implementing any of the four would fork the rule (CID-2) and is a STOP-and-report condition. Verify each call site in this driver rather than assuming symmetry with the oc twin.
  - Depends on: E-04
  - Expected outcome: `agy_runipd.py` reaches the same host-neutral functions the oc driver uses, containing NO duplicated projection, collection, or idempotency logic (shown by AST or the import graph, not a text grep), and the shared parameterized tests pass for both drivers.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Measured at HEAD `59e68d5a`; anchor on symbol names, since this plan moves these lines.
- Main ALREADY solved the prompt-after-allocation sequencing, differently from the retired lane design: `execute_item` builds a pre-lane draft prompt, then REBUILDS it after allocation with the lane root and the lane's plan path, re-writing the prompt file and re-taking its digest so the digest describes what the agent actually received. Build ON that; do not revert to moving the first call.
- `build_isolation_notice` is main's own work, added for a measured leak. Only the exception clause is the defect; the rest of the block stays.
- The two drivers are near-parity twins; `cdef9c90` is the precedent for editing both symmetrically in one pass.
- The suite must be run BARE and `make test-all` separately: a bare run deselects `slow` tests, and during `zpbx7o` a bare run reported GREEN while `make test-all` was red (`mzy2so`).

## Findings

| id | Finding | Evidence |
| --- | --- | --- |
| F-1 | The contradiction is emitted by the driver itself and is measurable, not inferred. An isolated prompt says "Do NOT read or write the main checkout" and nine lines later declares five absolute paths "the only exceptions ... you write them exactly as given". | `oc_runipd.build_isolation_notice`; read verbatim from the prompt a worker actually received in run `run-20260901T042331Z-118022`. |
| F-2 | FIVE absolute out-of-lane paths are emitted today. Built by invoking `build_prompt` directly with a synthetic isolated item: the plan file, the run directory, the decisions register, the execution report, and the outcome JSON. In the live prompt the main-checkout path appears 7 times, only 2 of them inside the lane. | Direct invocation plus regex over the returned string; `grep -c` over the live prompt file. |
| F-3 | Collection is REQUIRED, not optional polish. The driver reads `<run_dir>/outcomes/<NN>-<id6>.json`; a lane-relative instruction alone leaves that path empty, and the resulting fallback disposition sits outside the set that gates verification and self-finalize. | `reconcile_disposition`'s read path; spec `7ckptx` R2.1 rationale. |
| F-4 | Idempotency is required because retry is real. `requeue_interrupted` re-queues interrupted items so resume retries in recovery mode, and the decisions register is run-wide and append-only. | `oc_runipd.requeue_interrupted`; spec R2.3. |
| F-5 | This child carries the WHOLE containment guarantee for Antigravity, which raises its priority. That host contributes nothing at the permission layer by design (its `--dangerously-skip-permissions` default is a decided constraint, spec R4.1c), so R1 plus the driver-side bounds in child `03` are all there is. | Spec `7ckptx` R4.1 antigravity case. |

## Proposed changes (ordered, validatable)

1. Lane-relative worker-facing paths in the oc driver, non-isolated branch untouched (E-01).
2. Delete the exception clause; keep the workspace statement and name the missing-input token (E-02).
3. Collect submissions back, immediately before reconciliation (E-03).
4. Make the shared register's collection idempotent under retry (E-04).
5. Mirror all of it in the agy twin, verifying each seam rather than assuming symmetry (E-05).

## Deferred / out of scope (with reason)

- The lane input manifest, all `--file` attachments, and the clean-base guard: child `02` (`nna8yz`) owns R5.1-R5.4. This plan may name the missing-input TOKEN (R1.4) but must not implement the classifier.
- The missing-input classifier and repair cycle: child `04` (`y5od1h`) owns R3.
- Permission policy and turn deadlines: child `03` (`lhmrhx`) owns R4. Spec R4.6 forbids that work landing before THIS plan.
- Retention and teardown: child `05` (`xdr83v`) owns R5.5-R5.6.
- Shared predicate bodies: child `06` (`604wra`) owns R6.
- The noise-gated watchdog: spec Section 5.1 DECLINES it on measurement. Out of scope for the whole Set.

## Scope check

- Over-scope: none. Four files, all declared, and the eight requirements this plan is assigned.
- Under-scope: none for its assigned requirements. It does NOT deliver containment on its own: without child `03`'s bounds and child `04`'s repair path the guarantee is prompt-level only, which is why the orchestrator sequences all six.

## Required tests / validation

Two new test modules, parameterized over BOTH drivers rather than duplicated:

- `tests/test_lane_prompt_purity.py`: the R1 property assertions.
- `tests/test_lane_submission_collection.py`: the R2 loop and idempotency assertions.

BASELINES MUST BE MEASURED AT EXECUTION TIME, NOT COPIED FROM THIS PLAN. Corrected after `/aw plan-review` (PR-003 on every plan in this Set): the exact counts originally written here were already STALE before execution, because a co-worker's commit `8ced15ce` added two tests, moving the bare suite from `3996 passed` to `3998 passed`. A hardcoded count cannot distinguish an honest change from a regression, and treating it as an expectation would either raise a false alarm or, worse, mask a real failure behind an off-by-two rationalization.

SO DO THIS INSTEAD. Immediately before you start, run BOTH invocations and record their counts as YOUR baseline, pasting them. Then after your change, run both again and COMPARE FAILURES BY TEST IDENTITY, not by total: list the failing test node ids before and after and account for every difference by name. A count that changed with no new failing id is fine and must be explained (usually tests added); a new failing id is a STOP regardless of what the totals do.

TWO INVOCATIONS WITH DIFFERENT SEMANTICS, and the distinction is load-bearing: bare `python3 -m pytest` is expected to have ZERO failures, while `make test-all` carries a known set of PRE-EXISTING CLI-surface declaration failures that are not this plan's to fix. State the expected outcome separately per invocation; a single "failed == 0" claim across both is the contradiction that got the predecessor `tch3bo` flagged (PR-006). Identify the pre-existing set by NAME in your own measurement rather than trusting the number recorded here.

## Spec / documentation sync

- Spec `7ckptx` is the normative source; this plan cites requirement ids and does not restate them.
- No user-facing documentation change: no public command surface is altered.

## Open questions

### OQ-01: Attempt-keyed dedup or deterministic per-lane files for R2.3?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: EITHER IS ACCEPTABLE and the choice is the executor's, which is exactly how spec `7ckptx` OQ-03 deferred it: R2.3 fixes the REQUIREMENT (a retry must not duplicate, and must not remove a sibling's contribution) and A4 fixes the test, so the mechanism is an implementation decision rather than a contract question. E-04 requires the executor to CHOOSE ONE and state which in the code comment, so a later reader is not left guessing which invariant the code relies on. What is NOT acceptable is implementing neither and claiming idempotency, which V-04's two-run evidence is designed to catch.

### OQ-02: May E-05 remain one combined Antigravity mirror item?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-01: NO, E-05 may not remain a combined mirror, and it no longer is. E-01 through E-04 must place their logic in HOST-NEUTRAL functions in the declared module `agent_workflows/lane_containment.py`, and E-05 is reduced to wiring plus event-shape adaptation, with its expected outcome demanding AST or import-graph proof of NO duplicated projection, collection, or idempotency logic. A self-review then caught that the shared home had not been DECLARED anywhere, so spec R2.6 was added and the module is now first in this plan's `Scope-Paths`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01 (proves R1.1, R1.3; spec A1, A2)
  - Required evidence: paste the FULL emitted prompt for an isolated turn, then paste the output of a pattern scan over that string proving zero absolute paths outside the lane root, STATING THE PATTERN USED. A visual reading does not satisfy this item. Then paste a digest comparison of the NON-isolated prompt before and after the change for identical inputs, showing they match. SABOTAGE REQUIRED: re-introduce one absolute out-of-lane path, paste the FAILING scan, revert, paste the passing scan and `git status` proving the product is unmodified. A scan that passes both before and after sabotage is not testing anything.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02 (proves R1.2, R1.4; spec A1, A17)
  - Required evidence: paste a search of the module showing the exception sentence is ABSENT, and paste the emitted isolated prompt showing both the workspace statement and the literal missing-input token form are PRESENT. The absence assertion must be over the EMITTED OUTPUT, not only the source, so that a reworded exception also fails; state how your check would catch a rephrased exception. A test pinned to the exact old sentence does not satisfy this item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03 (proves R2.1, R2.2, R2.4; spec A3, A5, A18)
  - Required evidence: paste a test run showing that after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns THAT disposition and not the empty-outcome fallback; paste the harvested file's driver-side path; paste evidence the LANE still holds its own copy (proving copy, not move); and paste a case where the worker wrote nothing reconciling without raising. Also paste the source order proving the collection call precedes `reconcile_disposition` in `execute_item`. SABOTAGE REQUIRED: remove the collection call, paste the run showing the disposition degrade to the fallback, restore, paste it passing.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06 (proves the receipt `xdr83v` consumes)
  - Required evidence: paste receipts for all four states and show they are distinguishable WITHOUT inspecting run-directory contents: collected, uncollected (no receipt), interrupted mid-collection, and repeated collection of the same attempt. Paste the source digest and destination result recorded for each. State explicitly that absence of a receipt means NOT collected. SABOTAGE REQUIRED: make a collection fail (for example an unwritable destination) and show the receipt records it as FAILED rather than omitting it, because a silently omitted failure is indistinguishable from a lane that wrote nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04 (proves R2.3; spec A4)
  - Required evidence: paste a test that runs the SAME attempt's collection TWICE and asserts the lane's contribution to the run-wide register appears exactly once, AND that a sibling lane's contribution is still present after both runs. State which mechanism E-04 chose and quote the code comment recording it. A single-run test does not satisfy this item, because the defect only appears on the second run.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05 (proves twin parity; CID-3)
  - Required evidence: paste the test run showing the SAME parameterized assertions passing for BOTH `oc_runipd` and `agy_runipd`, and paste evidence the tests are parameterized over the two drivers rather than copied (show the parameterization, not two similar functions). Then paste both whole-suite invocations with their summary lines, reconciled against the baselines, with the expected count stated SEPARATELY per invocation. An unexplained new failure means `Result: pending`, never a pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 5 E-leaves in 2 task groups, well under both thresholds. The two groups are one indivisible change by spec mandate (R2.1), not two concerns bundled: the prompt change and the collection change are the two halves of a single loop, and shipping either alone is a regression. Everything separable was deliberately pushed to siblings `02` through `06`.

Execution contract: this plan INHERITS the shared execution contract from orchestrator `h0zljh` verbatim, including its ten numbered rules. The four most likely to be skipped here, restated because skipping them is how this work gets faked:

1. PROSE IS NEVER EVIDENCE. Paste real command output and exit codes, never a summary of them.
2. SABOTAGE the central assertions in V-01 and V-03. A passing test that also passes when the product is broken proves nothing; this session already produced one such test and only sabotage exposed it.
3. ASSERT THE PROPERTY, NOT THE WORDING (V-02). A reworded exception must still fail the check.
4. THE SCOPE FENCE IS A DECLARATION, NOT A HALT CONDITION. Touch only the four declared paths as a default, and never expand casually. If the work genuinely requires the manifest, the classifier, the deadlines, or the retention rules, those are SIBLINGS' surfaces: do NOT reimplement them (that forks the rule, CID-2) and do NOT halt the run over it. Report the need, and if you must touch a path outside the fence, MAKE THE EDIT AND JUSTIFY IT in the finalize reconciliation (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path), which is where an unjustified widening is caught.

Commits are path-scoped and never pushed. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed or hook-interrupted commit.

Post-gate lifecycle: run `aw ipd lint --phase pre-transition`, then `aw ipd finalize`, never a hand edit. If validation did not pass, record `substantially-complete` honestly rather than marking this executed.

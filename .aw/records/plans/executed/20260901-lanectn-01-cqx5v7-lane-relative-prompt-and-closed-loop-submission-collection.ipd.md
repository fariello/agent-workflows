# IPD: Lane-relative prompt and closed-loop submission collection

- Date: 2026-09-01
- Kind: child
- Concern: An isolated turn's prompt emits FIVE absolute paths outside the lane and then declares them authorized exceptions, so the worker must resolve a self-contradiction on every turn (spec `7ckptx` R1.1, R1.2). Removing the paths alone is NOT safe: the driver's reconciliation reads the run directory, so an obedient worker's lane-side outcome would never be found and a successful turn would silently never finalize (R2.1).
- Scope: Make every worker-facing path in an isolated prompt lane-relative, DELETE the exception clause, and in the SAME plan collect the worker's submissions back to the paths the driver already reads. Implements spec `7ckptx` R1.1, R1.2, R1.3, R1.4, R2.1, R2.2, R2.3, R2.4 and nothing else. Also implements R2.5 (an authoritative attempt-keyed collection record, which `xdr83v` consumes) and R2.6 (the declared shared-code home, created here as `agent_workflows/lane_containment.py`).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_lane_prompt_purity.py, tests/test_lane_submission_collection.py
- Item-Dependencies: none
- From-Spec: 7ckptx
- Blocks-Release: next
- Status: executed
- Readiness: go-pending-approval
- Set: lanectn
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: cqx5v7

## Workflow history
- 2026-09-05 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Executed: lane-relative isolated prompt (R1.1-R1.4) and closed-loop submission collection with an attempt-keyed receipt (R2.1-R2.6), in one host-neutral module both drivers call. All 6 V-items verified with pasted output including two product-level sabotage runs; both suite invocations show an identical failing set before and after.
- 2026-09-05 executed (aw oc run, opencode/its_direct/pt3-claude-opus-5-1m-us): all 6 E-items performed and all 6 V-items verified with pasted command output, including the two required product-level sabotage runs. Created the declared shared home `agent_workflows/lane_containment.py` (spec R2.6) and wired BOTH drivers to it; `agy_runipd.build_isolation_notice` had been delegating to `oc_runipd`, which made one host the de-facto shared library, and that pre-existing R2.6 violation was fixed here. THREE THINGS FOUND THAT THE PLAN DID NOT PREDICT, all recorded rather than absorbed: (1) the RECOVERY prompt leaked out-of-lane absolute paths through the prior-attempt record's `prompt`/`log`/`worktree` keys, a route the plan's five named path lines do not cover, so `prior_attempt_summary` allow-lists path-free facts for an isolated turn and leaves a non-isolated turn's record untouched; (2) the plan's `make test-all` baseline of 4 CLI-surface failures is STALE - in this lane the pre-existing set is instead the 14 `dh0uno` `test_run_viewer` failures, which is exactly why the plan says to identify the set by name rather than trust the count; (3) an intermediate `save_state` call added at the collection seam tripped `test_no_call_site_was_rewritten` (31 != 30), a real guard, and was removed as redundant. Bare suite and `make test-all` both show an IDENTICAL failing set before and after (14 pre-existing lane failures), with +45 passing accounted for by name.
- 2026-09-05 approved (aw set): status set to approved
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

- [x] E-01 IMPLEMENTS R1.1, R1.3. In `oc_runipd.build_prompt`, compute the worker-facing paths (plan file, run directory, decisions register, outcome JSON, driver report) RELATIVE to the lane root when the turn is isolated, keyed so a resumed run, a retry, and a co-resident lane cannot collide. Leave the non-isolated branch byte-identical: pass a lane root of `None` and the emitted string must be unchanged.
  - Depends on: none
  - Expected outcome: for an isolated item the returned string contains no substring matching an absolute path outside the lane root; for a non-isolated item the returned string is byte-identical to the pre-change output for the same inputs.
  - Execution state: performed
  - Notes: `lane_containment.project_worker_paths` (host-neutral) returns lane-RELATIVE paths for an isolated turn and the exact pre-change absolute paths when `lane_root is None`; `oc_runipd.build_prompt` interpolates its result. Keyed on run id + `<NN>-<id6>` + attempt number (`lane_submission_root`), so a resumed run, a retry, and an adopted co-resident lane cannot collide. ONE ADDITION BEYOND THE LITERAL FIVE PATHS, made because the property, not the enumeration, is the requirement: the prior-attempt record interpolated on a RECOVERY turn carries `prompt`, `log`, and `worktree` as absolute driver-side paths, so a resumed isolated turn leaked out-of-lane paths through a route the five named lines do not cover. `prior_attempt_summary` allow-lists the path-free facts for an isolated turn and returns the record UNCHANGED for a non-isolated one.
- [x] E-02 IMPLEMENTS R1.2, R1.4. DELETE the exception clause from the isolation notice, verbatim the sentence beginning "When a path below is given as an absolute path outside the lane" and ending "you write them exactly as given" (`oc_runipd.build_isolation_notice`). Keep the rest of that block: it is main's own plain-language statement of the rule and it is not the defect. Then ensure the notice states that the cwd is the complete authorized workspace AND names the exact missing-input token form, so the strictness from E-01 ships with its escape hatch.
  - Depends on: E-01
  - Expected outcome: the exception sentence is absent from the module; the emitted isolated prompt contains the workspace statement and the literal missing-input token form.
  - Execution state: performed
  - Notes: The clause is DELETED (not reworded) and the notice text moved to `lane_containment.isolation_notice`, which both drivers call. The block keeps its measured-defect content (`## Work here`, ISOLATED GIT WORKTREE, the `../../../` prohibition) and gains R1.4: "That directory is your COMPLETE authorized workspace and it is your working directory" plus the literal `AW_MISSING_INPUT:<repo-relative-path>:<why it is required>` form, exported as `MISSING_INPUT_TOKEN_FORM`. Only the FORM is stated here; emit/parse bodies stay owned by child `y5od1h` per R6.3.

### Task group 2: close the loop (R2)

- [x] E-03 IMPLEMENTS R2.1, R2.2, R2.4. Add a collection step that COPIES (never moves) the worker's lane-side submissions to the exact paths the driver already reads, and call it in `execute_item` IMMEDIATELY BEFORE `reconcile_disposition`. A turn that wrote nothing must reconcile to the existing empty-outcome fallback without raising.
  - Depends on: E-01
  - Expected outcome: after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns that disposition and the file exists at the driver-side path; the lane retains its own copy; a turn with no submission still reconciles without error.
  - Execution state: performed
  - Notes: `lane_containment.collect_lane_submissions` copies the lane-side outcome to `<run_dir>/outcomes/<NN>-<id6>.json`, merges the decisions contribution into the run-wide register, and collects a worker-written report to `<run_dir>/lane-reports/<NN>-<id6>-attempt-<N>-execution-report.md`. Called in `oc_runipd.execute_item` immediately before `reconcile_disposition` (asserted structurally by AST in `test_collection_is_called_before_reconcile_disposition`). COPY only, never move. A turn that submitted nothing records every submission `absent` and reconciles to the fallback without raising. ONE DELIBERATE DESTINATION CHOICE: the worker's report does NOT land on `<run_dir>/execution-report.md`, because the driver regenerates that file from durable state on every `save_state` and a worker copy there would destroy the run-wide record; the receipt names the real destination so nothing is implicit.
- [x] E-06 IMPLEMENTS R2.5, R2.6. EMIT AN AUTHORITATIVE COLLECTION RECORD, and create the shared home. Added after `/aw plan-review` on child `xdr83v` (finding PR-001), and given a spec basis on 2026-09-01 as R2.5 after a self-review found this obligation had none - the same PR-005 class of defect the predecessor was rejected for. R2.6 is cited here because this plan is first in the Set and therefore CREATES `agent_workflows/lane_containment.py`. That review established that the sealed input manifest CANNOT answer "was this lane's submission collected?": the manifest records materialized INPUTS (R5.1), while collection is R2 OUTPUT, so they are different data. Without a receipt, `xdr83v`'s retention classification would have to GUESS from path presence, which either preserves every successful lane forever or deletes output whose collection failed. So this item, which owns collection, must record the fact: for each attempt, write an attempt-keyed receipt naming what was collected, its source digest, and the destination result (success or failure with a reason). Absence of a receipt means NOT collected; it must never be inferred from a file existing somewhere.
  - Depends on: E-03
  - Expected outcome: after a collection attempt, an attempt-keyed receipt records each submission's source digest and destination result; a FAILED collection is recorded as failed rather than omitted; and a consumer can distinguish collected, uncollected, and failed-collection without inspecting the run directory's contents.
  - Execution state: performed
  - Notes: The shared home `agent_workflows/lane_containment.py` is CREATED by this plan (R2.6). The receipt is written to `<run_dir>/collections/<NN>-<id6>-attempt-<N>.json` and read back with `read_collection_receipt`. It records, per submission, the source path, the `source_sha256`, the destination, and a `result` of `collected` / `absent` / `failed` with a reason. Four states are distinguishable from the receipt ALONE: `collected` (status `complete`, result `collected`), UNCOLLECTED (NO receipt, and absence is authoritative - never inferred from a file existing), INTERRUPTED (status `in-progress`, written BEFORE the first copy), and REPEATED (`collection_runs` > 1). A failed collection is recorded as `failed`, never omitted.
- [x] E-04 IMPLEMENTS R2.3. Make collection IDEMPOTENT for the run-wide decisions register, which is APPENDED to and shared by every item. Choose ONE mechanism and state which in the code comment: key the appended block to the attempt, or write deterministic per-lane files that are concatenated on read. Retry is a real path, not hypothetical: `requeue_interrupted` re-queues interrupted items for recovery.
  - Depends on: E-03
  - Expected outcome: running the same attempt's collection twice leaves the lane's contribution present exactly once; a sibling lane's contribution is still present after both runs.
  - Execution state: performed
  - Notes: MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP, recorded verbatim in the `merge_decisions_block` docstring under the heading "MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP" (pinned by `test_the_chosen_mechanism_is_recorded_in_the_code`). Each lane's contribution is wrapped in `<!-- aw:lane-decisions <NN>-<id6>-attempt-<N> -->` delimiters and REPLACED in place on a re-run, so a second collection is byte-identical and a sibling's block is untouched. Chosen over deterministic per-lane files because the register is an existing single file that humans and the run readers already read, and because the delimiters make the idempotency observable in the artifact rather than implied by the writer.
- [x] E-05 WIRE THE AGY TWIN TO THE SHARED CODE. E-01 through E-04 put the path projection, the exception removal, the collection, and the idempotency into HOST-NEUTRAL functions (see the preamble); this item only CALLS them from `agy_runipd.py` and adapts that host's event shapes. It is deliberately a thin adapter, NOT a second implementation: re-implementing any of the four would fork the rule (CID-2) and is a STOP-and-report condition. Verify each call site in this driver rather than assuming symmetry with the oc twin.
  - Depends on: E-04
  - Expected outcome: `agy_runipd.py` reaches the same host-neutral functions the oc driver uses, containing NO duplicated projection, collection, or idempotency logic (shown by AST or the import graph, not a text grep), and the shared parameterized tests pass for both drivers.
  - Execution state: performed
  - Notes: WIRING ONLY. `agy_runipd` imports `lane_containment` DIRECTLY (line 94) and defines ZERO of the ten shared symbols; AST proof pasted at V-05. One pre-existing R2.6 violation was FIXED here rather than preserved: `agy_runipd.build_isolation_notice` previously delegated to `oc_runipd.build_isolation_notice`, which made the OpenCode driver the de-facto shared library for a host-neutral rule - exactly what R2.6 forbids. Each seam was verified at THIS driver rather than assumed symmetric: this host names the exit code `rc` and the log `log_file`, and its `execute_item` derives `attempt_no` the same way, so the collection call is placed on its own measured seam immediately before its own `reconcile_disposition`.

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

- [x] V-01 validates E-01 (proves R1.1, R1.3; spec A1, A2)
  - Required evidence: paste the FULL emitted prompt for an isolated turn, then paste the output of a pattern scan over that string proving zero absolute paths outside the lane root, STATING THE PATTERN USED. A visual reading does not satisfy this item. Then paste a digest comparison of the NON-isolated prompt before and after the change for identical inputs, showing they match. SABOTAGE REQUIRED: re-introduce one absolute out-of-lane path, paste the FAILING scan, revert, paste the passing scan and `git status` proving the product is unmodified. A scan that passes both before and after sabotage is not testing anything.
  - Observed evidence: R1.1/R1.3 PROVEN. Full isolated prompt + pattern scan (zero out-of-lane absolute paths, both drivers), non-isolated digests identical to pre-change HEAD 97d5ddf4 in both recovery modes, and a sabotage run failing 6 tests then passing after revert. Detail follows.

    FULL EMITTED ISOLATED PROMPT (oc_runipd; lane root `/tmp/repo/.aw/worktrees/aaaaaa`). The agy
    twin's full prompt is identical in every path line and differs only in its host-specific prose;
    both were emitted in the same run and both scanned clean (scan output below).

    ```
    # OpenCode IPD Driver Turn

    Mode: NORMAL EXECUTION

    ## Work here

    You are running in an ISOLATED GIT WORKTREE (a "lane"), not the main checkout:

        /tmp/repo/.aw/worktrees/aaaaaa

    That directory is your COMPLETE authorized workspace and it is your working directory. It is a
    full checkout of this repository on its own branch, so the whole tree you need is already there.
    Do EVERY edit, test run, and commit inside it, and write every path this prompt gives you exactly
    as given: they are relative to that directory.

    Do NOT read or write the main checkout, and do NOT climb out with a relative path such as
    `../../../<file>`. If you need a repository file, use the copy inside your workspace.

    If you genuinely need an input that is NOT present in your workspace, do not go looking for it
    outside. Report it on its own line in exactly this form, then continue with every independent part
    of your task:

        AW_MISSING_INPUT:<repo-relative-path>:<why it is required>

    The driver integrates your lane back into the main checkout after this turn, and collects
    everything you write under the submission directory named below. Leaving work outside your
    workspace defeats that integration and can corrupt another agent's tree.
    Run ID: run-20260901T000000Z-1
    Queue position: 1
    Assigned IPD: aaaaaa
    Assigned Set: lanectn
    Plan file at launch: x.ipd.md
    Your submission directory (relative to your workspace): .aw/state/lane-submissions/run-20260901T000000Z-1/01-aaaaaa/attempt-1
    Decisions/questions register: .aw/state/lane-submissions/run-20260901T000000Z-1/01-aaaaaa/attempt-1/decisions-and-questions.md
    Required JSON outcome: .aw/state/lane-submissions/run-20260901T000000Z-1/01-aaaaaa/attempt-1/outcomes/01-aaaaaa.json
    Your report for this turn (relative to your workspace): .aw/state/lane-submissions/run-20260901T000000Z-1/01-aaaaaa/attempt-1/execution-report.md
    Prior attempt: none

    ## Concurrent Work

    Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.

    Do not alter, revert, stage, or commit another agent's work. Stage only your files; never use `git add .` or `git add -A`.

    Before EVERY commit, verify what you are actually about to commit: run `git diff --cached --name-only` and confirm every path listed is one YOU modified for this task; `git restore --staged <path>` anything that is not yours. Path-scoping is NOT by itself sufficient, because `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, including a co-worker's edits to the same file.

    Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work.

    Execute only IPD aaaaaa. Read the attached driver runbook, every applicable
    repository instruction, the assigned IPD in full, its current orchestrator, current
    repository state, and completed prerequisite artifacts before editing. Do not implement
    another IPD in this turn.

    All target IPDs are already human-approved. Do not ask for approval. This run is
    non-interactive: do not invoke an interactive question tool or wait for human input.
    When a material question arises, investigate the approved plans, repository decisions,
    source, tests, history, and current primary documentation. If a reasonable recommended
    approach exists, choose it, record it in the decisions/questions register with evidence,
    alternatives, rationale, confidence, scope, reversibility, and validation, then continue.
    If no reasonable approach exists, record a DEFERRED question with the work completed,
    work blocked, dependency effect, exact preserved state, and recommended human action.
    Continue every independent part of this IPD despite a deferred question.

    Maximize safe forward progress. A local failure or unanswered question is not permission
    to abandon independent work. Do not weaken checks, fabricate evidence, broaden approved
    scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
    git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
    ownership. Use the lifecycle available at this bootstrap stage and path-scoped commits.

    If the IPD cannot validly finalize, preserve partial work using the repository-supported
    nonterminal checkpoint mechanism or an attributable isolated branch/worktree. Leave every
    checkout you did not own safe for subsequent turns. Never claim executed unless the real
    terminal state and acceptance criteria support it.

    Before exiting, write valid JSON to .aw/state/lane-submissions/run-20260901T000000Z-1/01-aaaaaa/attempt-1/outcomes/01-aaaaaa.json with at least:
    {
      "schema_version": 1,
      "run_id": "run-20260901T000000Z-1",
      "position": 1,
      "id6": "aaaaaa",
      "setid": "lanectn",
      "disposition": "executed|substantially-complete|partial|blocked|failed-safely",
      "summary": "...",
      "starting_head": "...",
      "ending_head": "...",
      "commits": [],
      "files_changed": [],
      "tests": [],
      "decision_ids": [],
      "deferred_question_ids": [],
      "incomplete_requirements": [],
      "partial_work_location": null,
      "recommended_next_action": "...",
      "pushed": false
    }

    The disposition must describe the actual repository result, not merely your effort. If no
    material question arose, say so in the summary. Explicitly confirm pushed=false.

    ## Concise reporting (user-facing prose)

    [the shared reporting contract block, byte-identical to `reporting_contract.contract_text()`,
    elided here only for length; it contains no filesystem paths, and the scan below covers it]
    ```

    PATTERN SCAN over that exact emitted string, PATTERN STATED:

    ```
    -- SCAN pattern: (?<![A-Za-z0-9_.~/-])/(?:[A-Za-z0-9_.~+-]+/)*[A-Za-z0-9_.~+-]+
    agent_workflows.oc_runipd  -- absolute paths outside lane: []
    agent_workflows.agy_runipd -- absolute paths outside lane: []
    ```

    DIGEST COMPARISON of the NON-isolated prompt, pre-change vs post-change, for identical inputs.
    The pre-change module is loaded from `git show HEAD:agent_workflows/<driver>.py` (HEAD
    `97d5ddf4`), so this compares against real prior code and not a reconstruction. Both recovery
    modes are compared, because the recovery branch is the one this plan also touched:

    ```
    oc_runipd  recovery=False: HEAD sha256=73778d84740ee1a1ee396abf41fb39180997ae2bbd9948306a84bd4de68fdc55  NOW sha256=73778d84740ee1a1ee396abf41fb39180997ae2bbd9948306a84bd4de68fdc55  IDENTICAL=True
    oc_runipd  recovery=True:  HEAD sha256=d7833cbc783fc67e4ceaa45f62537638db916bb462568d22b996a22f662214b3  NOW sha256=d7833cbc783fc67e4ceaa45f62537638db916bb462568d22b996a22f662214b3  IDENTICAL=True
    agy_runipd recovery=False: HEAD sha256=7811a8d05d95661d9440b531362637bba5f0993f4131784e678f228200550afd  NOW sha256=7811a8d05d95661d9440b531362637bba5f0993f4131784e678f228200550afd  IDENTICAL=True
    agy_runipd recovery=True:  HEAD sha256=3c8a0174ecf57a43ff3c3e03fc9d0d8d19f127f8fb8ea0f5d93420f6034a7974  NOW sha256=3c8a0174ecf57a43ff3c3e03fc9d0d8d19f127f8fb8ea0f5d93420f6034a7974  IDENTICAL=True
    ```

    SABOTAGE. The product was broken by changing `project_worker_paths`' isolated branch to return
    the ABSOLUTE run directory (`prompt_run_dir=str(run_dir)`) instead of the lane-relative one, i.e.
    exactly the defect R1.1 forbids, then the suite was run:

    ```
    $ grep -n "SABOTAGE" agent_workflows/lane_containment.py
    246:        prompt_run_dir=str(run_dir),  # SABOTAGE: re-introduce one absolute out-of-lane path
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_prompt_purity.py -o addopts="" -q
    FAILED tests/test_lane_prompt_purity.py::test_isolated_prompt_names_no_absolute_path_outside_the_lane[oc_runipd]
    FAILED tests/test_lane_prompt_purity.py::test_isolated_prompt_names_no_absolute_path_outside_the_lane[agy_runipd]
    FAILED tests/test_lane_prompt_purity.py::test_recovery_prompt_is_also_pure[agy_runipd]
    FAILED tests/test_lane_prompt_purity.py::test_the_worker_is_told_where_its_submissions_go[agy_runipd]
    FAILED tests/test_lane_prompt_purity.py::test_recovery_prompt_is_also_pure[oc_runipd]
    FAILED tests/test_lane_prompt_purity.py::test_the_worker_is_told_where_its_submissions_go[oc_runipd]
    6 failed, 13 passed in 0.39s
    ```

    Note the sabotage failed in BOTH drivers from ONE product change, which is the parity property
    the parameterization exists to demonstrate. Reverted, re-run, and the product proven unmodified:

    ```
    $ grep -c SABOTAGE agent_workflows/lane_containment.py
    0
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_prompt_purity.py -o addopts="" -q
    ...................                                                      [100%]
    19 passed in 0.33s
    $ git status --porcelain agent_workflows/
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
    ?? agent_workflows/lane_containment.py
    ```

    (The two `M` entries and the new untracked module are THIS plan's own intended changes; the
    sabotage-specific edit is gone, which is what the `grep -c` zero establishes.)
  - Result: pass
- [x] V-02 validates E-02 (proves R1.2, R1.4; spec A1, A17)
  - Required evidence: paste a search of the module showing the exception sentence is ABSENT, and paste the emitted isolated prompt showing both the workspace statement and the literal missing-input token form are PRESENT. The absence assertion must be over the EMITTED OUTPUT, not only the source, so that a reworded exception also fails; state how your check would catch a rephrased exception. A test pinned to the exact old sentence does not satisfy this item.
  - Observed evidence: R1.2/R1.4 PROVEN. The exception clause is absent from the EMITTED output of both drivers (source hit is a docstring quoting what was deleted); workspace statement and literal token form both present; a rephrased exception is caught semantically. Detail follows.

    SOURCE SEARCH across `agent_workflows/`, for three fragments of the retired clause:

    ```
    'those are the only exceptions': ABSENT
    'DRIVER-OWNED control path': ABSENT
    'you write them exactly as given': agent_workflows/lane_containment.py:331:    the driver-owned control paths as "the only exceptions ... you write them exactly as given". That
    ```

    The single remaining hit is inside `isolation_notice`'s DOCSTRING, quoting the retired sentence to
    record what was deleted and why. It is not emitted, which the output check below establishes
    independently, and that is exactly why the authoritative assertion is over the OUTPUT.

    EMITTED-OUTPUT check, both drivers:

    ```
    agent_workflows.oc_runipd:  'those are the only exceptions' present=False
    agent_workflows.oc_runipd:  'DRIVER-OWNED control path' present=False
    agent_workflows.oc_runipd:  'you write them exactly as given' present=False
    agent_workflows.oc_runipd:  workspace statement present=True
    agent_workflows.oc_runipd:  missing-input token form present=True
    agent_workflows.agy_runipd: 'those are the only exceptions' present=False
    agent_workflows.agy_runipd: 'DRIVER-OWNED control path' present=False
    agent_workflows.agy_runipd: 'you write them exactly as given' present=False
    agent_workflows.agy_runipd: workspace statement present=True
    agent_workflows.agy_runipd: missing-input token form present=True
    ```

    The full emitted prompt containing both R1.4 elements is pasted at V-01 (the `COMPLETE authorized
    workspace` sentence and the `AW_MISSING_INPUT:<repo-relative-path>:<why it is required>` line).

    HOW A REPHRASED EXCEPTION IS CAUGHT, which is the part a fragment search cannot do. An exception
    clause must do TWO things at once: name a path outside the lane, and grant permission about it.
    The first is already impossible by construction - V-01's scan reads the WHOLE emitted string for
    absolute out-of-lane paths and no wording can hide one, so a rephrased exception that still named
    a path would fail there. `test_no_reworded_exception_survives_either` closes the remaining gap
    semantically: it rejects any LINE combining an outside-the-lane referent (`outside the lane`,
    `outside your workspace`, `outside this workspace`) with permission vocabulary (`exception(s)`,
    `permitted`, `allowed`, `authorized to write`, `you may write`), so a differently-worded grant
    fails without the test naming any sentence. Both tests pass for both drivers:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_prompt_purity.py -o addopts="" -q \
        -k "exception or workspace_rule or reworded"
    ......                                                                   [100%]
    6 passed, 13 deselected in 0.16s
    ```
  - Result: pass
- [x] V-03 validates E-03 (proves R2.1, R2.2, R2.4; spec A3, A5, A18)
  - Required evidence: paste a test run showing that after an isolated turn whose worker wrote a lane-side outcome declaring `executed`, `reconcile_disposition` returns THAT disposition and not the empty-outcome fallback; paste the harvested file's driver-side path; paste evidence the LANE still holds its own copy (proving copy, not move); and paste a case where the worker wrote nothing reconciling without raising. Also paste the source order proving the collection call precedes `reconcile_disposition` in `execute_item`. SABOTAGE REQUIRED: remove the collection call, paste the run showing the disposition degrade to the fallback, restore, paste it passing.
  - Observed evidence: R2.1/R2.2/R2.4 PROVEN. Collected lane outcome yields `substantially-complete` with the worker's `executed` (not the `partial` fallback); lane keeps its copy; empty submission reconciles without raising; collection precedes reconciliation by AST. Sabotage run pasted. Detail follows.

    THE FIVE ASSERTIONS, run together for BOTH drivers:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_submission_collection.py -o addopts="" -q \
        -k "yields_the_workers_disposition or without_collection or submitted_nothing or copies_and_the_lane or called_before"
    ..........                                                               [100%]
    10 passed, 16 deselected in 0.38s
    ```

    WHAT EACH ONE PROVES, since a green count alone is not the evidence:

    * `test_collected_lane_outcome_yields_the_workers_disposition` - after an obedient worker wrote
      its outcome at the LANE-RELATIVE path and collection ran, `reconcile_disposition` returns
      `substantially-complete` with `outcome["disposition"] == "executed"`. `substantially-complete`
      is the CORRECT expectation, not a weaker one: the plan is still in `pending/` at that moment and
      `reconcile_disposition` deliberately downgrades a worker's self-claimed `executed`, while the
      self-finalize gate fires on `{executed, substantially-complete}`. The test also asserts the file
      now exists at the driver-side path.
    * `test_without_collection_the_disposition_degrades` - THE SAME lane-side outcome with collection
      SKIPPED reconciles to `partial` with `outcome is None`, and the test asserts explicitly that
      this value is OUTSIDE the gating set. That is the R2.1 invisible failure, demonstrated rather
      than described.
    * `test_a_turn_that_submitted_nothing_reconciles_without_raising` - R2.4. Every submission records
      `absent`, and reconciliation returns `partial` without an exception.
    * `test_collection_copies_and_the_lane_keeps_its_evidence` - R2.2/A18. The lane-side file still
      exists after collection and is byte-equal to the collected copy.
    * `test_collection_is_called_before_reconcile_disposition` - the ORDERING, established by AST
      inside `execute_item` (comparing the `collect_lane_submissions` call's line to the
      `disposition, outcome = ...` assignment's), not by reading the file.

    DRIVER-SIDE DESTINATION and the LANE's retained copy, from a live collection receipt:

    ```
    "name": "outcome",
    "source":      ".../.aw/worktrees/aaaaaa/.aw/state/lane-submissions/run-R/01-aaaaaa/attempt-1/outcomes/01-aaaaaa.json",
    "destination": ".../.aw/records/runs/run-R/outcomes/01-aaaaaa.json",
    "result": "collected",
    "source_sha256": "0ef60b16a454753698364624c055400e0801d6d1ce624b96229b3b8872e434a3"
    ```

    SOURCE ORDER in both drivers (`grep -n`, confirming what the AST test asserts):

    ```
    $ grep -n "collect_lane_submissions(\|disposition, outcome = reconcile_disposition" \
        agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:4971:            collection = lane_containment.collect_lane_submissions(
    agent_workflows/oc_runipd.py:5008:    disposition, outcome = reconcile_disposition(repo, item, run_dir, exit_code)
    agent_workflows/agy_runipd.py:3025:            collection = lane_containment.collect_lane_submissions(
    agent_workflows/agy_runipd.py:3059:    disposition, outcome = reconcile_disposition(repo, item, run_dir, rc)
    ```

    SABOTAGE. The collection CALL was removed from `execute_item` in BOTH drivers (replaced with
    `collection = None` plus a no-op lambda, so the surrounding code still parses):

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_submission_collection.py -o addopts="" -q
    tests/test_lane_submission_collection.py:248: AssertionError
    FAILED tests/test_lane_submission_collection.py::test_collection_is_called_before_reconcile_disposition[agy_runipd]
    FAILED tests/test_lane_submission_collection.py::test_collection_is_called_before_reconcile_disposition[oc_runipd]
    2 failed, 24 passed in 1.14s
    ```

    HONEST READING OF THAT RESULT, because it is narrower than it looks and pretending otherwise
    would be the greenwash this plan is written against. Removing the call fails the ORDERING test in
    both drivers (the driver no longer collects at all), but it does NOT fail the disposition tests,
    because those call `collect_lane_submissions` directly rather than driving a whole `execute_item`
    turn with a live agent subprocess. The DEGRADATION half of the sabotage is therefore carried by
    `test_without_collection_the_disposition_degrades`, which is a permanent test rather than a
    temporary edit: it runs the identical fixture with collection skipped and asserts the fallback
    `partial`. Together the two cover what the item asks for - "the call is really wired in the driver"
    and "without collection the disposition really degrades" - and the second one cannot rot away.

    Restored, re-run, product proven unmodified:

    ```
    $ grep -c SABOTAGE agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:0
    agent_workflows/agy_runipd.py:0
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_submission_collection.py -o addopts="" -q
    ..........................                                               [100%]
    26 passed in 1.05s
    $ git status --porcelain agent_workflows/
     M agent_workflows/agy_runipd.py
     M agent_workflows/oc_runipd.py
    ?? agent_workflows/lane_containment.py
    ```
  - Result: pass
- [x] V-06 validates E-06 (proves the receipt `xdr83v` consumes)
  - Required evidence: paste receipts for all four states and show they are distinguishable WITHOUT inspecting run-directory contents: collected, uncollected (no receipt), interrupted mid-collection, and repeated collection of the same attempt. Paste the source digest and destination result recorded for each. State explicitly that absence of a receipt means NOT collected. SABOTAGE REQUIRED: make a collection fail (for example an unwritable destination) and show the receipt records it as FAILED rather than omitting it, because a silently omitted failure is indistinguishable from a lane that wrote nothing.
  - Observed evidence: R2.5 PROVEN. Receipts pasted for all four states (collected / uncollected-no-receipt / interrupted in-progress / repeated collection_runs=2) with per-submission source digest and destination, plus a genuinely failed copy recorded as `failed`. Detail follows.

    ABSENCE OF A RECEIPT MEANS NOT COLLECTED, stated explicitly as this item requires, and it is
    load-bearing rather than a formality: `read_collection_receipt` returns `None` when no receipt
    exists, and a consumer must treat that as NOT COLLECTED. It must NEVER infer collection from a
    file existing at the driver-side path, because a PREVIOUS attempt may have put it there and
    because a collection can FAIL after its destination directory already exists. The receipt is the
    only authoritative source, which is precisely why spec R2.5 exists.

    STATE 2, UNCOLLECTED (read before any collection ran):

    ```
    ### UNCOLLECTED (no receipt on disk)
    NO RECEIPT (means NOT collected)
    ```

    STATE 1, COLLECTED. Note each submission's `source_sha256` and `destination`, and that the
    worker's absent report is recorded as `absent` with a reason rather than omitted:

    ```
    {
      "attempt": 1,
      "collected": ["outcome", "decisions"],
      "collection_runs": 1,
      "failed": [],
      "id6": "aaaaaa",
      "lane_root": ".../.aw/worktrees/aaaaaa",
      "lane_submission_root": ".../.aw/worktrees/aaaaaa/.aw/state/lane-submissions/run-R/01-aaaaaa/attempt-1",
      "position": 1,
      "run_id": "run-R",
      "schema_version": 1,
      "status": "complete",
      "submissions": [
        {
          "destination": ".../.aw/records/runs/run-R/outcomes/01-aaaaaa.json",
          "name": "outcome",
          "reason": null,
          "result": "collected",
          "source": ".../attempt-1/outcomes/01-aaaaaa.json",
          "source_sha256": "0ef60b16a454753698364624c055400e0801d6d1ce624b96229b3b8872e434a3"
        },
        {
          "destination": ".../.aw/records/runs/run-R/lane-reports/01-aaaaaa-attempt-1-execution-report.md",
          "name": "report",
          "reason": "the lane holds no such submission",
          "result": "absent",
          "source": ".../attempt-1/execution-report.md",
          "source_sha256": null
        },
        {
          "destination": ".../.aw/records/runs/run-R/decisions-and-questions.md",
          "name": "decisions",
          "reason": null,
          "result": "collected",
          "source": ".../attempt-1/decisions-and-questions.md",
          "source_sha256": "f6a4ebcee0b2f239a6878b0e41372d43cd908382d85ceea35fe34c81674651e0"
        }
      ]
    }
    ```

    STATE 4, REPEATED collection of the same attempt. Identical submission records, distinguished by
    `collection_runs`:

    ```
    "collection_runs": 2,
    "status": "complete",
    "collected": ["outcome", "decisions"],
    "failed": []
    ```

    STATE 3, INTERRUPTED mid-collection. `_copy_file` was made to raise, so the process died after the
    receipt was opened and before any submission was recorded:

    ```
    (raised: interrupted mid-collection )

    {
      "attempt": 1,
      "collection_runs": 1,
      "id6": "aaaaaa",
      "lane_submission_root": ".../attempt-1",
      "position": 1,
      "run_id": "run-R",
      "schema_version": 1,
      "status": "in-progress",
      "submissions": []
    }
    ```

    All four are distinguishable from the RECEIPT ALONE, without reading run-directory contents:
    `None` -> uncollected; `status == "in-progress"` -> interrupted; `status == "complete"` with
    `collection_runs == 1` -> collected; `collection_runs > 1` -> repeated.

    SABOTAGE, the failed-collection case. `<run_dir>/outcomes` was chmodded `0o500` so the copy
    genuinely fails at the OS level:

    ```
    {
      "collected": ["decisions"],
      "failed": ["outcome"],
      "status": "complete",
      "submissions": [
        {
          "destination": ".../.aw/records/runs/run-R/outcomes/01-aaaaaa.json",
          "name": "outcome",
          "reason": "PermissionError: [Errno 13] Permission denied: '.../outcomes/.01-aaaaaa.json.34mmlsel'",
          "result": "failed",
          "source": ".../attempt-1/outcomes/01-aaaaaa.json",
          "source_sha256": null
        },
        ...
      ]
    }
    ```

    The failure is recorded as `failed` with its reason and listed in `failed`, NOT omitted, so it is
    distinguishable from `absent` (the lane wrote nothing). The `decisions` submission still collected,
    which shows one failure does not abort the rest.

    Test coverage for all of the above, both drivers:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_submission_collection.py -o addopts="" -q \
        -k "receipt or failed_collection"
    ........                                                                 [100%]
    8 passed, 18 deselected in 0.43s
    ```
  - Result: pass
- [x] V-04 validates E-04 (proves R2.3; spec A4)
  - Required evidence: paste a test that runs the SAME attempt's collection TWICE and asserts the lane's contribution to the run-wide register appears exactly once, AND that a sibling lane's contribution is still present after both runs. State which mechanism E-04 chose and quote the code comment recording it. A single-run test does not satisfy this item, because the defect only appears on the second run.
  - Observed evidence: R2.3 PROVEN. Mechanism ATTEMPT-KEYED DEDUP, quoted from the code; two-run register output byte-identical with the lane's block appearing once and the sibling's surviving. Detail follows.

    MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP. Quoted verbatim from `merge_decisions_block`'s docstring in
    `agent_workflows/lane_containment.py`, which is the code record E-04 requires:

    > MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP by HTML-comment delimiters, not deterministic per-lane
    > files concatenated on read. Recorded here because plan `cqx5v7` OQ-01 leaves the choice to the
    > executor and requires the choice be stated where a later reader will find it. Two reasons it won:
    > the register is an EXISTING single file that humans and `aw oc run status` already read, so
    > switching to a fan-in directory would change a read surface this plan is not chartered to change;
    > and the delimiters make the idempotency observable in the artifact itself rather than implied by
    > the writer's behavior.

    TWO-RUN EVIDENCE at the artifact level. Two lanes collected into ONE run-wide register, then lane
    `aaaaaa` re-collected (the retry path `requeue_interrupted` really takes):

    ```
    === register after both lanes collected ===
    # Decisions and Questions for run-R

    <!-- aw:lane-decisions 01-aaaaaa-attempt-1 -->
    ## DECISION 01-aaaaaa-D1
    - Question: mine
    <!-- /aw:lane-decisions 01-aaaaaa-attempt-1 -->

    <!-- aw:lane-decisions 02-bbbbbb-attempt-1 -->
    ## DECISION 02-bbbbbb-D1
    - Question: theirs
    <!-- /aw:lane-decisions 02-bbbbbb-attempt-1 -->

    === register after RE-collecting lane aaaaaa (the retry) ===
    # Decisions and Questions for run-R

    <!-- aw:lane-decisions 01-aaaaaa-attempt-1 -->
    ## DECISION 01-aaaaaa-D1
    - Question: mine
    <!-- /aw:lane-decisions 01-aaaaaa-attempt-1 -->

    <!-- aw:lane-decisions 02-bbbbbb-attempt-1 -->
    ## DECISION 02-bbbbbb-D1
    - Question: theirs
    <!-- /aw:lane-decisions 02-bbbbbb-attempt-1 -->

    byte-identical to previous: True
    count of 01-aaaaaa block: 1
    count of 02-bbbbbb block (sibling survives): 1
    ```

    The run's own preamble survives too, so idempotency is not implemented by truncating the shared
    file - which is the wrong fix this item's second clause exists to rule out.

    TESTS, both drivers, all multi-run:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_submission_collection.py -o addopts="" -q \
        -k "idempotent or sibling or mechanism or merge_is_pure"
    ......                                                                   [100%]
    6 passed, 20 deselected in 0.42s
    ```

    `test_running_the_same_attempts_collection_twice_is_idempotent` runs collection TWICE and asserts
    byte-equality plus a block count of exactly 1; `test_a_siblings_contribution_survives_both_runs`
    adds a second lane and asserts both blocks survive the retry; `test_merge_is_pure_and_replaces_
    rather_than_appends` pins the unit invariant independently of the filesystem.
  - Result: pass
- [x] V-05 validates E-05 (proves twin parity; CID-3)
  - Required evidence: paste the test run showing the SAME parameterized assertions passing for BOTH `oc_runipd` and `agy_runipd`, and paste evidence the tests are parameterized over the two drivers rather than copied (show the parameterization, not two similar functions). Then paste both whole-suite invocations with their summary lines, reconciled against the baselines, with the expected count stated SEPARATELY per invocation. An unexplained new failure means `Result: pending`, never a pass.
  - Observed evidence: CID-3 PROVEN. 45 assertions pass for BOTH drivers from one parameterized body; AST/import-graph shows neither driver defines or re-imports a shared symbol; both suite invocations reconciled by failing-test IDENTITY against baselines measured in this lane. Detail follows.

    THE SAME ASSERTIONS PASSING FOR BOTH HOSTS. Every id below carries an `[oc_runipd]` or
    `[agy_runipd]` suffix, which is pytest's own parameterization marker - the proof that one function
    body ran against both drivers rather than two functions existing:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_lane_prompt_purity.py \
        tests/test_lane_submission_collection.py -o addopts="" -v
    tests/test_lane_prompt_purity.py::test_isolated_prompt_names_no_absolute_path_outside_the_lane[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_isolated_prompt_names_no_absolute_path_outside_the_lane[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_scan_can_actually_fail[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_scan_can_actually_fail[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_recovery_prompt_is_also_pure[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_recovery_prompt_is_also_pure[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_exception_clause_is_absent_from_the_emitted_prompt[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_exception_clause_is_absent_from_the_emitted_prompt[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_no_reworded_exception_survives_either[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_no_reworded_exception_survives_either[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_isolated_prompt_states_the_workspace_rule_and_the_token_form[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_isolated_prompt_states_the_workspace_rule_and_the_token_form[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_worker_is_told_where_its_submissions_go[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_the_worker_is_told_where_its_submissions_go[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_non_isolated_prompt_is_byte_identical_to_the_pre_change_output[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_non_isolated_prompt_is_byte_identical_to_the_pre_change_output[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_non_isolated_recovery_prompt_keeps_the_whole_prior_record[oc_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_non_isolated_recovery_prompt_keeps_the_whole_prior_record[agy_runipd] PASSED
    tests/test_lane_prompt_purity.py::test_neither_driver_holds_a_second_copy_of_the_rule PASSED
    tests/test_lane_submission_collection.py::test_collected_lane_outcome_yields_the_workers_disposition[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_collected_lane_outcome_yields_the_workers_disposition[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_without_collection_the_disposition_degrades[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_without_collection_the_disposition_degrades[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_turn_that_submitted_nothing_reconciles_without_raising[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_turn_that_submitted_nothing_reconciles_without_raising[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_non_isolated_turn_collects_nothing_and_writes_no_receipt[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_non_isolated_turn_collects_nothing_and_writes_no_receipt[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_collection_copies_and_the_lane_keeps_its_evidence[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_collection_copies_and_the_lane_keeps_its_evidence[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_collection_is_called_before_reconcile_disposition[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_collection_is_called_before_reconcile_disposition[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_running_the_same_attempts_collection_twice_is_idempotent[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_running_the_same_attempts_collection_twice_is_idempotent[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_siblings_contribution_survives_both_runs[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_siblings_contribution_survives_both_runs[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_the_chosen_mechanism_is_recorded_in_the_code PASSED
    tests/test_lane_submission_collection.py::test_merge_is_pure_and_replaces_rather_than_appends PASSED
    tests/test_lane_submission_collection.py::test_receipt_distinguishes_all_four_states[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_receipt_distinguishes_all_four_states[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_failed_collection_is_recorded_as_failed_not_omitted[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_a_failed_collection_is_recorded_as_failed_not_omitted[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_the_receipt_is_attempt_keyed_so_a_retry_does_not_overwrite_history[oc_runipd] PASSED
    tests/test_lane_submission_collection.py::test_the_receipt_is_attempt_keyed_so_a_retry_does_not_overwrite_history[agy_runipd] PASSED
    tests/test_lane_submission_collection.py::test_both_drivers_reach_the_same_shared_functions PASSED
    tests/test_lane_submission_collection.py::test_these_tests_are_parameterized_rather_than_duplicated PASSED
    ============================== 45 passed in 1.20s ==============================
    ```

    PARAMETERIZED, NOT COPIED, established three ways rather than by inspection:
    (1) the `[oc_runipd]`/`[agy_runipd]` id suffixes above, which only a parametrize mark produces;
    (2) ONE shared mark, `DRIVERS = pytest.mark.parametrize("driver", (oc_runipd, agy_runipd), ids=...)`,
    declared once per module and applied as `@DRIVERS`;
    (3) `test_these_tests_are_parameterized_rather_than_duplicated`, which walks the AST of BOTH test
    modules and asserts every `test_*` takes a `driver` argument IFF it carries `@DRIVERS`, and that no
    test name is suffixed with a host name (the shape a copy-paste takes). So a future copied test fails.

    AST / IMPORT-GRAPH PROOF for E-05 and CID-2 (structure, not grep):

    ```
    === AST: top-level definitions of the shared symbols, per module ===
    agent_workflows/lane_containment.py: defines ['absolute_paths_outside_lane', 'collect_lane_submissions',
      'collection_receipt_path', 'isolation_notice', 'lane_submission_root', 'merge_decisions_block',
      'prepare_lane_submission_dir', 'prior_attempt_summary', 'project_worker_paths', 'read_collection_receipt']
    agent_workflows/oc_runipd.py: defines []
    agent_workflows/agy_runipd.py: defines []

    === IMPORT GRAPH: who imports lane_containment ===
    agent_workflows/oc_runipd.py:213: from agent_workflows import lane_containment
    agent_workflows/agy_runipd.py:94: from agent_workflows import lane_containment

    === agy_runipd must NOT import a containment rule from oc_runipd (spec R2.6) ===
    violations: NONE

    === identity: both drivers reach the SAME module object ===
    oc_runipd.lane_containment is agy_runipd.lane_containment -> True

    === CID-1 regression sanity: terminate_process bodies in agent_workflows/ ===
    ['agent_workflows/agy_runipd.py:2154', 'agent_workflows/oc_runipd.py:3837', 'agent_workflows/runner_shutdown.py:126']
    ```

    On that last line, honestly: the two driver entries are PRE-EXISTING one-line delegations to
    `runner_shutdown.terminate_process` (the single reaper), unchanged by this plan. This scan is
    recorded as a no-regression check, not as a CID-1 verdict; CID-1 is the orchestrator's E-02 to
    establish, and it must distinguish a delegating wrapper from a second body.

    WHOLE-SUITE INVOCATIONS, WITH EXPECTED OUTCOMES STATED SEPARATELY PER INVOCATION, and baselines
    MEASURED in this lane immediately before the work rather than copied from the plan.

    ONE MEASUREMENT CAVEAT, stated up front because it changes how the numbers read. This lane is a
    linked worktree, so `dh0uno` applies: 14 `tests/test_run_viewer.py` tests fail in any lane and pass
    in the primary tree. The orchestrator's own conventions record this ("Validate in the PRIMARY
    checkout ... that is `dh0uno`, not a regression"). Consequently the BARE expectation of `failed == 0`
    is NOT reproducible here, and the honest thing is to compare failing test IDENTITIES before and
    after, which is what the plan's own "compare failures by identity" instruction asks for.
    Additionally, the environment sets `AW_EXECUTION_ROLE=worker` (the driver marks a lane turn), which
    by itself fails 17 further lifecycle tests; every run below therefore uses
    `env -u AW_EXECUTION_ROLE` so that the marker is not measured as a code regression.

    BARE `python3 -m pytest` (expected: NO NEW failing id versus baseline; the 14 `dh0uno` lane
    failures are pre-existing and not this plan's):

    ```
    BEFORE (baseline, measured at HEAD 97d5ddf4 before any edit):
    14 failed, 4436 passed, 3 skipped, 4 xfailed in 35.86s

    AFTER:
    14 failed, 4481 passed, 3 skipped, 4 xfailed in 32.72s

    $ diff baseline-bare-ids.txt after-bare-ids.txt && echo "IDENTICAL FAILING SET"
    IDENTICAL FAILING SET
    ```

    The 14 failing ids, identical before and after, all `dh0uno`:

    ```
    tests/test_run_viewer.py::RunViewerTests::test_aw_cli_entry_points
    tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs
    tests/test_run_viewer.py::RunViewerTests::test_format_run_human
    tests/test_run_viewer.py::RunViewerTests::test_load_run_summary_state_json
    tests/test_run_viewer.py::RunViewerTests::test_multi_run_cli_json_summary
    tests/test_run_viewer.py::RunViewerTests::test_resolve_target_runs_by_substring_and_setid
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_agent
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_filters
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_json
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only_single_run
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_short
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_since_filter
    tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_target_human
    ```

    The `+45 passed` delta is fully accounted for by name: it is exactly the 45 new tests listed at the
    top of this item (19 + 26). No previously-passing test disappeared.

    `make test-all` (expected: a KNOWN pre-existing failing set, no worse; NOT `failed == 0`):

    ```
    BEFORE (baseline):
    14 failed, 4839 passed, 3 skipped, 4 xfailed in 127.45s (0:02:07)

    AFTER:
    14 failed, 4884 passed, 3 skipped, 4 xfailed in 108.32s (0:01:48)

    $ diff base-ta-ids.txt after-ta-ids.txt && echo "IDENTICAL FAILING SET (test-all)"
    IDENTICAL FAILING SET (test-all)
    ```

    Note what this measurement found and the plan did NOT predict: the plan expected `make test-all`
    to carry 4 pre-existing CLI-surface declaration failures. In THIS lane the pre-existing set is
    instead the same 14 `dh0uno` `test_run_viewer` failures, and the CLI-surface tests pass. The plan's
    own instruction covers exactly this - "Identify the pre-existing set by NAME in your own
    measurement rather than trusting the number recorded here" - and this is why: the recorded count
    was stale. Reported as a measured discrepancy rather than reconciled away.

    ONE INTERMEDIATE FAILURE, FOUND AND FIXED, recorded rather than hidden: an early version of the
    collection wiring added a `save_state(run_dir, state)` call in each driver, which moved a call-site
    count that `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten`
    deliberately pins (`AssertionError: 31 != 30`). That is a real guard doing its job, not noise. The
    call was removed - it was redundant, because the receipt is written atomically by the collection
    itself and the event is already appended, and the existing `save_state` a few lines below persists
    the annotation - and a comment at each seam records why no save belongs there.
  - Result: pass

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

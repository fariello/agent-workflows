# IPD: Delete the pre-launch dirty-tree refusal and report it as a warning instead

- Date: 2026-09-13
- Kind: child
- Concern: The spec-R5.4 clean-base gate refuses an unattended isolated turn when ANY tracked path in the shared checkout is dirty, regardless of whether the plan will touch that path. RE-MEASURED AT REVIEW from each run's `state.json`: one uncommitted backlog markdown file refused 27 of 42, 23 of 41 and 18 of 43 items across three consecutive runs, cascading 36 more to `dependency-blocked`, across four runs costing ~$131. The gate does not prevent the harm it names for an isolated turn; it only defers it. CORRECTED AT REVIEW: not a "100% batch failure rate", since each run still executed at least one item and completed several reviews (reviews are exempt from this gate); the honest claim is that the majority of every run was lost.
  SCOPE CAVEAT ADDED AT REVIEW: this plan changes the ISOLATED path only (the call site is guarded by `if isolate and self_finalize and not is_review`), and approved release-blocking plan `3i0aaz` E-03 is signed off to EXTEND this same refusal to the `--no-isolate-worktree` path, where the disproof in F-3 does not apply. E-04's spec amendment must not remove the obligation for that path; see blocking OQ-03 on the orchestrator.
- Scope: Turn the pre-launch clean-base REFUSAL into a non-blocking WARNING on both hosts, and amend spec 7ckptx R5.4 plus its acceptance criterion A14 to match. Excludes the integration-time overlap check (Order 02), the backlog close (Order 03), and orchestrator retirement (Order 04).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/lane_containment.py, tests/test_lane_clean_base.py, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: dirtygates
- Order: 1
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: d7qoxv
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-101..PR-107; six FIXED, PR-101 (HIGH) left OPEN and escalated as blocking OQ-02; OQ-01 resolved from evidence; review record written; Readiness no-go.
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored from a live measurement session. The gate was traced from the refusal text through `lane_containment.evaluate_clean_base` to both call sites, and the claim that it PREVENTS a stale-base failure was tested and DISPROVED (see Findings F-3).

## Goal

Stop a dirty path in the shared checkout from refusing unattended isolated turns that will never touch it. Report the dirty paths so the operator is informed, and let the merge-and-revalidate gate remain the thing that actually catches a stale base.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: replace the refusal with a report

- [ ] E-01 In `oc_runipd.py` at the pre-launch gate (`:6123`, `base = evaluate_clean_base_for_launch(repo)`), stop writing a terminal disposition when the base is not clean. Today the not-clean branch sets `attempt["disposition"] = "blocked"`, `item["status"] = "blocked"`, records `clean_base_refused` / `clean_base_dirty_paths`, saves state and skips the turn. Instead: emit the dirty-path list as a WARNING to stderr, record the same observation on the attempt under a NON-refusal key (e.g. `clean_base_warning` / `clean_base_dirty_paths`) so the run record still carries the fact, and PROCEED to `driver_begin` and lane allocation. Do not change `evaluate_clean_base`'s classification itself (E-03 owns the shared rule's docstring).
  - Depends on: none
  - Expected outcome: an isolated turn launched against a checkout holding a dirty tracked path proceeds, and the run record carries the dirty paths as a warning rather than a refusal.
  - Execution state: pending
- [ ] E-02 Apply the byte-equivalent change to `agy_runipd.py` at `:3262-3263`, which is the same gate with the same placement (its own comment at `:3258-3261` states it shares the RULE via `lane_containment.evaluate_clean_base`). HOST PARITY IS A REQUIREMENT, not a nicety, and CITED CORRECTLY AT REVIEW: the authority is spec `7ckptx` R2.6 plus its acceptance criterion A5c ("THE SHARED-CODE HOME IS DECLARED ... neither driver holds a second copy"), reinforced by the R6.1 single-definition rule, NOT R4, which governs the host PERMISSION POSTURE and says nothing about guard parity. Note also that the agy comment's citation of "CID-3" is dead: `CID-3` appears NOWHERE in the specs tree (grepped at review), so do not chase it; R2.6/A5c is the live requirement. `z2isfg` already left agy behind once on the neighbouring begin-dirty gate ("AGY IS DEFERRED, NOT DONE"), which is exactly the asymmetry this item must not repeat.
  BOTH CALL SITES ARE ALREADY IDENTICAL, VERIFIED AT REVIEW, so this is a mirrored edit and not a reconciliation: oc `:6122-6148` and agy `:3262` open with the same `if isolate and self_finalize and not is_review:` condition and the same `evaluate_clean_base_for_launch(repo)` call, and each host defines that wrapper once (`oc_runipd.py:1955`, `agy_runipd.py:1299`).
  - Depends on: E-01
  - Expected outcome: both hosts warn and proceed; no host retains the refusal.
  - Execution state: pending

### Task group 2: keep the rule honest where it is defined

- [ ] E-03 Update `lane_containment.CleanBaseResult.reason` (`:2543-2551`) and `evaluate_clean_base`'s docstring (`:2554-2582`) so the text describes a WARNING rather than a refusal. The current `reason` string literally begins "refusing to launch an unattended isolated turn", which would otherwise be printed by a code path that no longer refuses. Preserve the `clean` / `dirty_paths` shape and the deliberate `--untracked-files=no` exclusion unchanged, and preserve the docstring paragraph that contrasts this check with `dirty_tree_overlap` (Order 02 changes that neighbour; this item must not silently invalidate the cross-reference).
  - Depends on: E-01
  - Expected outcome: the emitted text matches the behavior; no string claims a refusal that cannot happen.
  - Execution state: pending

### Task group 3: the contract and its tests

- [ ] E-04 Amend spec `7ckptx` R5.4 (`:416-420`) and acceptance criterion A14 (`:570-572`). R5.4 currently says the checkout "MUST have no dirty TRACKED paths, and a refusal MUST name them and occur BEFORE any worker process is spawned". Replace the refusal obligation with a reporting obligation, and record WHY in the amendment: (a) the gate does not prevent a stale-base failure for an isolated turn, it defers it (F-3); (b) the merge-and-revalidate gate already re-runs the suite against the combined result, which is where a genuine stale base surfaces with real evidence (F-4); (c) the measured cost was 68 refusals across three runs (27 of 42, 23 of 41, 18 of 43), each naming one uncommitted backlog file, plus 36 cascaded `dependency-blocked` (F-6). Use those measured figures, NOT "100% batch failure", which F-6 disproves. KEEP R5.4's untracked-file exclusion and its rationale, which remain correct. A14 must be rewritten to assert the warning-and-proceed behavior rather than the refusal.
  SCOPE THE AMENDMENT TO THE ISOLATED CASE ONLY, pending the orchestrator's blocking OQ-03. R5.4's subject is "an unattended isolated turn", and this plan's F-3 disproof is about a LANE cut from HEAD; it says nothing about a shared-tree run, where the worker writes into the polluted tree directly. Approved plan `3i0aaz` E-03 is signed off to EXTEND this refusal to the `--no-isolate-worktree` path. So the amended R5.4 MUST NOT read as "no dirty-base refusal exists anywhere": write it as a reporting obligation for the ISOLATED path and leave the shared-tree question to `3i0aaz`, or state explicitly that the maintainer answered OQ-03 the other way. An amendment that silently removes the obligation for both paths would negate an approved release blocker through a spec edit, which is the highest-leverage change a run can make.
  DO NOT HAND-EDIT THE SPEC'S `- Status:` (it is `approved`); record the amendment in the spec's own history with `aw specs note`, which is what the declared-spec-edit mechanism expects.
  - Depends on: E-01, E-02
  - Expected outcome: the spec and the code agree, the amendment states the measured figures from F-6 rather than the disproved rate, and R5.4 still carries an obligation for the non-isolated path unless OQ-03 removed it.
  - Execution state: pending
- [ ] E-05 Update `tests/test_lane_clean_base.py` so it pins the NEW contract, and add the regression that the old contract lacked: a queue of several isolated execute items, with one dirty tracked path OUTSIDE every plan's declared scope, completes every item. That test is the direct regression for run `run-20260913T031148Z-1722898` (23 of 41 items blocked). Also assert the warning names the dirty path, so removing the refusal does not silently remove the operator's signal.
  FOUR NAMED TESTS WILL FAIL AND EACH MUST BE RETARGETED DELIBERATELY, ENUMERATED AT REVIEW so no executor discovers them by running the suite and then guesses (baseline: `python3 -m pytest tests/test_lane_clean_base.py` is `15 passed`). (1) `test_case_1_a_dirty_tracked_file_refuses_and_names_it:105` and (2) `test_case_1_a_staged_tracked_change_also_refuses:114` assert the REFUSAL classification; both must become warn-and-proceed assertions, and note they exercise `evaluate_clean_base` (the pure rule, which E-03 keeps classifying `clean=False`), so decide explicitly whether the RULE still reports not-clean while only the CALLER stops refusing. That distinction is the whole design and a test that blurs it will hide a regression. (3) `test_refusal_records_the_dirty_paths_on_the_attempt:192` asserts the literal source strings `attempt["clean_base_dirty_paths"]` and `"event": "clean-base-refused"` by SOURCE INSPECTION of `execute_item`, so E-01's rename to a non-refusal key breaks it textually; retarget it to the new key and event name rather than deleting it, because it is the only thing pinning that the paths reach durable state instead of only stderr. (4) `test_case_3_an_untracked_file_does_NOT_refuse:123` must stay GREEN unchanged; if it goes red you have widened the tracked/untracked scope, which F-5 forbids.
  KEEP `test_guard_precedes_spawn_and_allocation:172` GREEN AND MEANINGFUL. It asserts the guard call precedes both the spawn and the lane allocation. After this change the call still runs there (it now warns), so the test should still pass; if you move the call, that ordering property is what R5.4's "before any worker process is spawned" clause becomes under a reporting obligation, so preserve it rather than deleting the test.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the suite fails if the refusal is reintroduced, fails if the warning stops naming the paths, and all four enumerated tests are retargeted (not deleted) with the untracked-exclusion test still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The RULE lives once in `lane_containment` and each host injects its own git runner (`oc_runipd.py:1955`, `agy_runipd.py:1299`). Change the rule in one place; change the two call sites symmetrically.
- Both runners deliberately avoid `input()` anywhere and hand children `stdin=subprocess.DEVNULL` under the `ttywedge (g40w37)` banner. This plan adds no prompt.
- Warnings in these runners go to stderr so a caller parsing stdout for structured output is unaffected.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | The gate is the only one of three dirty-tree gates that is NOT path-scoped. | `run_evidence.dirty_within` (`:223-241`) ignores disjoint dirty work by design, "the path-overlap rule that preserves a concurrent multi-agent workflow"; `runner_shared.dirty_tree_overlap` (`:888-917`) refuses only on intersection with the lane's changed files; `lane_containment.evaluate_clean_base` (`:2554`) is whole-tree and absolute. |
| F-2 | The blast radius is the whole run, not one item. | Runs `run-20260913T031350Z-1732436` (27 of 42 blocked), `run-20260913T031148Z-1722898` (23 of 41), `run-20260913T031521Z-1774617` (18 of 43). Every refusal named the same single backlog markdown file. |
| F-3 | THE GATE DOES NOT PREVENT THE HARM IT NAMES, FOR AN ISOLATED TURN. Tested 2026-09-13. A worker lane cut from HEAD lacked an uncommitted `src/lib.py` change; its new test passed in the lane, merged with no overlap, then failed against the real tree (`assert 5 == 4`). Committing the same uncommitted change with NO lane involved produced the IDENTICAL failure. So the lane was never the cause; the gate defers the failure to whenever the operator commits, which must happen anyway. SCOPE LIMIT ADDED AT REVIEW: this disproof is about a LANE CUT FROM A COMMIT and does NOT transfer to a `--no-isolate-worktree` run, where the worker writes into a tree that already holds another party's uncommitted work and cannot distinguish its own changes from theirs at commit or finalize time. That case is the subject of blocking OQ-03 on the orchestrator and of approved plan `3i0aaz` E-03. | reproduced in a scratch repo during the session that authored this plan; scope limit added at review |
| F-6 | THE MEASURED COST IS RE-VERIFIED AND SLIGHTLY RESTATED. Read from each run's `state.json` at review: 27 of 42, 23 of 41 and 18 of 43 items `blocked`, each with a `clean_base_refused` attempt naming exactly ONE dirty path (`.aw/records/backlog/graduated/...0k74my...` in the first run, `...lsztiu...` in the other two), plus 8, 12 and 16 cascaded `dependency-blocked`. Total cost across the four runs ~$131, of which the largest single stranded item was $18.57. NOT a 100% failure rate: each large run still executed at least one item and completed 4 to 6 reviews, because reviews are EXEMPT from this gate. Correct the "100% batch failure" wording; the true claim is that the majority of every run was lost. | `.aw/records/runs/run-20260913T031350Z-1732436/state.json`, `run-20260913T031148Z-1722898`, `run-20260913T031521Z-1774617`, per-item `status` and `attempts[].clean_base_refused` |
| F-4 | The failure F-3 describes is already caught downstream, with better evidence. | The merge-and-revalidate gate re-runs validation against the combined result (`oc_runipd.make_integration_validation_runner`, and `runner_shared.integrate_lane_branch` step 1), so a genuine stale-base problem appears as a test failure on the real tree rather than as a guess about a dirty file. |
| F-5 | Untracked files are already excluded, deliberately, and that part is right. | `evaluate_clean_base`'s docstring: tightening to include untracked files "would make an unattended run unstartable in essentially any working checkout, which is why it must not be 'fixed'". |
| F-7 | THE RENAMED KEYS AND THE REFUSAL CLASSIFICATION ARE PINNED BY FOUR SHIPPED TESTS, which this plan did not name. `tests/test_lane_clean_base.py:192` asserts the literal source strings `attempt["clean_base_dirty_paths"]` and `"event": "clean-base-refused"` by inspecting `execute_item`'s SOURCE, so E-01's rename breaks it textually rather than behaviorally; `:105` and `:114` assert the refusal classification; `:123` pins the untracked exclusion and must stay green. Baseline measured at review: `15 passed`. E-05 now enumerates all four with the required disposition for each. | `tests/test_lane_clean_base.py:105`, `:114`, `:123`, `:192`; `python3 -m pytest tests/test_lane_clean_base.py -o addopts=""` -> `15 passed` |
| F-8 | THE HOST-PARITY CITATION IN E-02 WAS WRONG AND IS CORRECTED. The plan cited spec `7ckptx` "R4", which governs the host PERMISSION POSTURE (strongest available posture, observed effective policy, per-turn bounds) and says nothing about guard parity. The live authority is R2.6 ("THE SHARED-CODE HOME MUST BE DECLARED") with acceptance criterion A5c ("neither driver holds a second copy"), plus the R6.1 single-definition rule. Separately, the `CID-3` identifier that BOTH the agy code comment and the original plan text lean on appears NOWHERE in the specs tree, so it is a dead reference an executor should not chase. | `.aw/records/specs/20260901-7ckptx-...spec.md:165-172` (R2.6), `:477-480` (A5c), `:248-298` (R4 is permission posture); `grep -rn CID-3 .aw/records/specs/` returns nothing |

## Proposed changes (ordered, validatable)

1. `oc_runipd.py` pre-launch gate: warn and proceed instead of blocking (E-01).
2. `agy_runipd.py` twin: identical change (E-02).
3. `lane_containment.py`: make the message and docstring describe a warning (E-03).
4. Spec `7ckptx` R5.4 + A14: amend the obligation from refusal to report, recording the measurement (E-04).
5. `tests/test_lane_clean_base.py`: pin the new contract and add the multi-item regression (E-05).

## Deferred / out of scope (with reason)

- Path-scoping the gate to `Scope-Paths` instead of deleting the refusal. CONSIDERED AND REJECTED during authoring: it keeps a gate that F-3 shows prevents nothing, adds a dependency on a DECLARATION (a worker can read a file it never declared), and still refuses in the case where the declaration happens to overlap. Deleting the refusal is simpler and strictly more useful. Recorded here because it was the author's own first proposal and the reasoning that killed it is worth keeping.
- The integration-time overlap check (`dirty_tree_overlap`), the backlog close, and orchestrator retirement: Orders 02, 03 and 04 of this Set.
- Making the runner distinguish dirty paths IT authored from a co-worker's. Not needed once the refusal is gone, and Order 03 removes the runner's own mid-run writes anyway.

## Scope check

- Over-scope: none.
- Under-scope: this plan removes a refusal and does not add a replacement guard. That is deliberate per F-3/F-4: the replacement already exists downstream. If review disagrees, the alternative is the rejected path-scoping option above, which should then become its own plan rather than an expansion of this one.

## Required tests / validation

- `tests/test_lane_clean_base.py` updated and passing, including the new multi-item regression.
- The full suite, run bare (`python3 -m pytest`), with the failure set compared against a baseline from the same commit. Paste both counts and the diff of FAILED sets.
- A manual end-to-end check: with one dirty tracked path in the checkout, start a run of at least two isolated execute items and paste the output showing both items launching and the warning naming the path.

## Spec / documentation sync

- Spec `7ckptx` R5.4 and A14 are amended by E-04. This plan declares that spec file in `Scope-Paths`, which is what makes the amendment visible to the runner's declared-spec-edit announcement and to the finalize scope gate.
- No user-facing README or CHANGELOG change: the behavior removed is a refusal nobody should have been relying on. If review disagrees, add a CHANGELOG note rather than widening code scope.

## Open questions

### OQ-02: Does this plan's removal survive against approved plan `3i0aaz`, which is signed off to EXTEND the same refusal?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-101
- Resolution or deferral rationale: NOT resolvable from repository evidence, because a human has already approved BOTH directions. `3i0aaz` is `Status: approved`, `Blocks-Release: next`, and its E-03 extends this exact clean-base refusal to the `--no-isolate-worktree` path, calling that "the case where dirt is MOST dangerous"; its E-04/E-05 then add `--allow-dirty-base` as the consent escape hatch with a spec `25kzda` 2.1 amendment. This plan deletes the refusal on the isolated path and rewrites the R5.4 obligation that `3i0aaz` builds on. The two are not automatically incompatible, and the coherent combined end state is worth stating: THIS plan removes the refusal for the ISOLATED path (where F-3 disproves it), `3i0aaz` keeps and extends it for the SHARED-TREE path (where F-3 does not apply), and `--allow-dirty-base` remains the consent surface for that path. If the maintainer confirms that shape, E-04's amendment must preserve R5.4's obligation for the non-isolated case and this question closes; if they instead want no dirty-base refusal anywhere, `3i0aaz` needs narrowing or retiring, which is their call and not an executor's.
  WHY BLOCKING RATHER THAN A NOTE: E-04 edits an APPROVED spec, and a spec edit changes the contract every other plan is reviewed against. Getting it wrong silently negates a release blocker, and the weaker R5.4 cannot be un-shipped once other plans are reviewed against it. This is the same question as the orchestrator's OQ-03, carried here because this is the plan that performs the amendment.

### OQ-01: Should the warning appear once per run or once per item?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-13 FROM REPOSITORY EVIDENCE, not by asking, because an approved plan already settled the identical question. `3i0aaz` E-02 was revised by its own review (PR-005) for exactly this defect: a report placed in `execute_item` "fires once per queue entry and says the same thing N times", and the fix named `initialize_run` on both hosts (`oc_runipd.py:2732`, `agy_runipd.py:1800`) as "the one place 'run start' actually exists", beside `refuse_unimplemented_run_flags`. So the answer is BOTH, split by purpose: the OPERATOR-FACING stderr warning goes ONCE PER RUN, and the per-attempt RECORD (`clean_base_warning` / `clean_base_dirty_paths`) stays PER ITEM so each attempt remains self-describing.
  ONE CONSEQUENCE FOR E-01, which otherwise conflicts: E-01 as written emits the warning at the per-item call site. Keep the per-item RECORD there, and either emit the stderr line once per run from `initialize_run` or de-duplicate it per run, so this plan does not ship the N-times noise that `3i0aaz`'s review already rejected. COORDINATE, DO NOT DUPLICATE: `3i0aaz` E-02 is approved to add an UNTRACKED-dirt report at that same seam, so a second unconditional tracked-dirt report placed there without reference to it would give the operator two adjacent dirty-tree reports at run start. Whichever lands second should extend the first rather than add a parallel one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the run output for an isolated execute item launched against a checkout with a dirty tracked path, showing the item PROCEEDING and the warning text. Paste the attempt record from `state.json` showing the dirty paths recorded under a non-refusal key and no `blocked` status.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the diff hunks for both hosts side by side, or a test that exercises both call sites, proving the change is symmetric. Naming the two line numbers is NOT sufficient evidence; show the code.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `grep` output proving no shipped string in `lane_containment.py` claims "refusing to launch" for this gate, plus the new text.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the amended R5.4 and A14 text, and confirm `aw specs check` conforms. The amendment must contain the measurement (three runs, the item counts) rather than only the new obligation.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_lane_clean_base.py` output with the count, and paste the bare full-suite counts before and after with the FAILED-set diff. A green subset alone is not sufficient.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. This plan amends an approved spec, so the spec file is declared in `Scope-Paths` and the amendment's reason is recorded in the spec's own text, not only here.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.

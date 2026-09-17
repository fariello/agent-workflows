# IPD: Let a finalize accept a WIDENED Scope-Paths with a recorded reason instead of refusing the honest declaration

- Date: 2026-09-17
- Kind: child
- Concern: An executing agent that discovers it must touch a file its plan did not declare has exactly two options, and the system punishes the honest one. If it ADDS the path to `Scope-Paths` (the honest declaration), that edit changes the plan's frozen region, `receipt_is_current` returns False, and `finalize_precheck` refuses with "the begin receipt ... is STALE", stranding correct and tested work on a lane. If it instead edits the file WITHOUT declaring it, `aw ipd finalize --scope-reason <path>=<why>` accepts the run. So the undeclared edit finalizes and the declared one does not. Measured 2026-09-16/17 in run `run-20260917T023628Z-4108757`: this fired on THREE of the twelve items (`i3d6ml`, `tx6q0h`, `sy7uwh`), costing $95.71 of the run's $212.60, stranding three lanes, and cascading to leave orchestrator `5e4sb6` `dependency-blocked` and backlog items `dhuape` and `alw22r` unevaluated. In all three the ONLY differing frozen field was `scope`, and in all three the change was purely ADDITIVE.
- Scope: Make an ADDITIVE widening of `Scope-Paths` a recordable, justified condition at finalize rather than a hard refusal, while keeping every genuinely contract-changing edit (a REMOVED scope path, a rewritten E/V requirement, a changed `## Scope` line) refusing exactly as it does today. Amends the spec clause that lists "changed frozen requirements" as never-retryable so it distinguishes an additive widening from a contract rewrite. Does NOT touch the retry machinery, the scope-collision rule, or the out-of-scope-mutation refusal.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, tests/test_finalize_isolated_commit.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Blocks-Release: next
- Status: to-review
- Set: rcptwiden
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 63425h

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a measured, three-times-reproduced failure in run `run-20260917T023628Z-4108757`. VERIFIED NO PENDING PLAN OWNS THIS before authoring, which is why it is a new plan rather than a note on an existing one: `wmnmei` (rcptstale-01, approved) analyses what the frozen `base_head` MEANS for the `check.scope-drift` advisory and explicitly excludes `ipd_lifecycle.py` from its scope ("If E-02 or E-03 concludes the advisory cannot be fixed without a lifecycle change, that is a FINDING and a follow-up plan, not a silent scope widening"); `zzcrlo` (finalback-01, approved) hands a refused finalize BACK to the same agent but its own analysis puts "changed frozen requirements" on the never-retry boundary it promises to honor, so it would re-dispatch this failure and refuse it again rather than fix it; `tgop8e` (stalecrit-01) re-derives a plan's target population at execution time, a different staleness. So the cause is unowned. THE ASYMMETRY IS THE DEFECT, not the freeze: freezing the reviewed contract is correct and `receipt_is_current`'s own docstring records that an earlier whole-file digest "refused every self-finalizing run" and was narrowed for exactly this class of false positive. This plan finishes that narrowing for the one case it left: an ADDITIVE scope declaration.

## Goal

Stop the system from refusing the honest act. An agent that declares a newly-needed path should finalize
with that declaration recorded; an agent that rewrites its reviewed contract should still be refused.

Today those two are indistinguishable because `frozen_region_digest` hashes a single opaque payload, so
ANY change to the frozen region yields one boolean. The fix is to compare the frozen region
STRUCTURALLY when the digests differ, and to treat exactly one difference class (a superset of
`scope_paths`, with every requirement category byte-identical) as justifiable rather than fatal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the failure and the blast radius before changing a gate

- [ ] E-01 REPRODUCE THE ASYMMETRY AS A TEST FIRST, so the fix has a falsifiable target and the claim in this plan's Concern is proven rather than cited. Build two fixture plans from one begin receipt: (a) one whose `Scope-Paths` gained a path and whose requirements are otherwise identical, and (b) one whose `## Scope` line or an `E-*` action text was rewritten. Assert that TODAY both are refused identically by `receipt_is_current` / `finalize_precheck`, and paste the refusal message for each. Then assert the third case for contrast: a plan that edited a file NOT in `Scope-Paths` and finalizes with `--scope-reason`, showing it is ACCEPTED. That three-way fixture is the specification for E-03.
  - Depends on: none
  - Expected outcome: a pasted test run showing all three current behaviors, with the two refusals byte-identical in kind and the third accepted, so the asymmetry is demonstrated rather than asserted.
  - Execution state: pending

- [ ] E-02 MEASURE EVERY CONSUMER OF THE FROZEN REGION AT EXECUTION HEAD, and refuse to proceed to E-03 on this plan's list. `frozen_region_digest` (`agent_workflows/ipd_lifecycle.py:474`) is consumed by `receipt_is_current` (`:837`) and written by `run_begin`; `_frozen_scope_paths` (`:564`) and `_requirements_from_plan` (`:516`) are its inputs. Find every OTHER reader of any of the four, including tests that pin the digest as a literal and any hook or CLI path, and state per consumer whether a structural comparison changes what it sees. A consumer that stores or compares the digest VALUE is a compatibility surface; name it. Do not change behavior in this item.
  - Depends on: none
  - Expected outcome: a pasted per-consumer table (symbol, file:line, what it does with the digest, whether E-03 affects it), with an explicit statement of any consumer that would need a change and any test that pins a digest literal.
  - Execution state: pending

### Task group 2: distinguish the two cases, and keep the refusal for the real one

- [ ] E-03 ADD A STRUCTURAL FROZEN-REGION COMPARISON that returns WHICH categories differ instead of one boolean, leaving `receipt_is_current`'s signature and current semantics intact so nothing that calls it changes meaning. The new function takes the receipt and the plan text and reports, per category: `scope_paths` added / removed / unchanged, and for each requirement category (`scope`, `must`, `validation`) identical or differing. The digest stays the fast path and the authority for "unchanged"; the structural comparison runs ONLY when the digests differ, so an unchanged plan costs nothing new. Store nothing new in the receipt; derive everything from the receipt fields that already exist plus the plan text. NOTE the receipt today stores only the DIGEST, not the payload, so E-03 must either recompute the receipt-side payload from a field that exists or record honestly that a v2 receipt cannot be decomposed and state what E-04 therefore needs; do NOT invent a field silently.
  - Depends on: E-01, E-02
  - Expected outcome: a pure, tested function returning a per-category difference report; `receipt_is_current` behavior byte-identical for both the unchanged and the requirement-rewritten cases, proven by E-01's fixtures still refusing case (b).
  - Execution state: pending

- [ ] E-04 TEACH `finalize_precheck` TO ACCEPT AN ADDITIVE WIDENING WITH A RECORDED REASON, and only that. The accept condition is narrow and must be stated in code: every requirement category byte-identical AND `scope_paths` a strict SUPERSET of the receipt's. Any removal, any requirement change, or both together still refuses with today's message. The reason is not optional: reuse the existing `--scope-reason PATH=WHY` surface rather than adding a flag, so a widened path carries the same justification an out-of-scope edit already must, and a widening with no reason for a given added path REFUSES. Record the accepted widening in the finalize evidence so it appears in the run record and the plan's history rather than passing silently.
  - Depends on: E-03
  - Expected outcome: E-01's case (a) finalizes when each added path carries a `--scope-reason` and REFUSES when one does not; case (b) still refuses; the accepted widening is visible in the finalize evidence, pasted.
  - Execution state: pending

- [ ] E-05 KEEP THE REFUSAL LOUD FOR A NARROWING, which is the direction this plan must not soften and which no measured incident asked for. A REMOVED scope path is a contract reduction: it can retroactively make an already-made edit out-of-scope and it is how a plan could be quietly re-fenced around whatever was touched. Assert it refuses with a message naming the removed path, distinct from the additive case's acceptance, and add the negative-control test that a superset-plus-one-removal is treated as a REMOVAL rather than as a widening.
  - Depends on: E-03
  - Expected outcome: pasted tests showing a removal refuses and names the path, and that a mixed add-and-remove refuses rather than being accepted on the strength of its additions.
  - Execution state: pending

### Task group 3: amend the contract this changes, and say so

- [ ] E-06 AMEND THE SPEC CLAUSE THAT THIS CHANGES, because it is a shipped contract and leaving it would put the code and the spec in direct conflict. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:1009` lists "changed frozen requirements" in the never-retry class. That clause is CORRECT for a requirement rewrite and WRONG for an additive scope declaration, and plan `zzcrlo` (finalback-01, approved) explicitly promises to honor that list as its retry boundary, so if this plan lands without the amendment `zzcrlo` will re-dispatch and re-refuse exactly this failure. Split the clause: a changed REQUIREMENT stays never-retryable; an ADDITIVE scope widening with a recorded reason becomes a finalize-time accept (not a retry). State the measured incident as the amendment's rationale.
  - Depends on: E-04, E-05
  - Expected outcome: the amended clause quoted before and after, with the split stated and the incident cited; any contract test reading this spec text still passing, named and pasted.
  - Execution state: pending

- [ ] E-07 REPORT THE THREE STRANDED PLANS THIS WOULD HAVE SAVED, as a check that the fix addresses the real incident rather than a plausible model of it. For each of `i3d6ml`, `tx6q0h` and `sy7uwh`, state the paths its agent added and confirm each is an ADDITIVE widening that E-04 would accept. If ANY of the three would still refuse, say so plainly and name why: that is a finding about this plan's completeness, not a detail. Report only; do NOT finalize those plans here.
  - Depends on: E-04
  - Expected outcome: a per-plan statement of the added paths and whether E-04's condition accepts it, with any non-accepting case named as a finding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FREEZE IS RIGHT AND ITS HISTORY MATTERS. `receipt_is_current` (`agent_workflows/ipd_lifecycle.py:837`) already survived exactly this class of bug once: its docstring records that the ORIGINAL whole-file `plan_content_digest` "was self-defeating" because a correct execution MUST edit its own plan, so it "refused every self-finalizing run" and was narrowed to the frozen contract (wtiso-03 `rchpms` E-03, backlog `xmqv5l`). This plan finishes that narrowing for the one false-positive class it left behind. It does NOT argue against freezing.
- THE DIGEST IS AN OPAQUE PAYLOAD HASH. `frozen_region_digest` (`:474`) serializes `{"scope_paths": sorted(...), "requirements": {...}}` with `json.dumps(sort_keys=True)` and hashes it, so one changed path and a rewritten requirement are indistinguishable downstream. That is precisely why a structural comparison is needed rather than a looser digest.
- LEGACY v1 RECEIPTS FALL BACK TO THE WHOLE-FILE RULE deliberately (`:860-864`), so a pre-Phase-2 receipt "must not be spuriously ACCEPTED by a rule it was never bound under". E-03/E-04 must leave that fallback alone; a v1 receipt is not eligible for the widening accept.
- `--scope-reason` ALREADY EXISTS AND IS THE RIGHT SURFACE. `aw ipd finalize --scope-reason PATH=WHY` is the "headless answer to the two-way scope" question, with `--scope-ack` for a declared-but-unmodified path. Adding a second, differently-named justification flag for widening would fork one concept into two.
- SCOPE FENCES ARE DECLARATIONS, NOT STOP SIGNS (2026-09-01 maintainer ruling, recorded in `plan-review`). The fence exists so the runner can tell afterwards whether an out-of-scope file was edited or a declared one was not; the correct requirement is that an out-of-scope edit be MADE and then JUSTIFIED. An additive widening is the most honest possible form of that justification, which is the strongest argument that refusing it is a defect.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | BLOCKER | `ipd_lifecycle.receipt_is_current` + `finalize_precheck` | **THE HONEST ACT IS THE ONE THAT FAILS.** Declaring a newly-needed path in `Scope-Paths` invalidates the receipt and refuses finalize; editing the same file WITHOUT declaring it finalizes fine with `--scope-reason`. The incentive gradient points at concealment. | measured three times in run `run-20260917T023628Z-4108757`; `--scope-reason` present in `aw ipd finalize --help`, no widening equivalent |
| F2 | HIGH | run `run-20260917T023628Z-4108757` | **THE COST IS MEASURED, NOT HYPOTHETICAL.** 3 of 12 items ended `substantially-complete` for this reason: `i3d6ml` ($20.24, 49m40s), `tx6q0h` ($30.72, 1h09m04s), `sy7uwh` ($44.75, 1h11m12s) = $95.71 and 3h10m of the run's $212.60 / 8h06m. Three lanes stranded, `5e4sb6` left `dependency-blocked`, backlog `dhuape` and `alw22r` unevaluated. | the run summary table; the three `Diagnostics / Blocked Items` lines |
| F3 | HIGH | all three incidents | **EVERY OCCURRENCE WAS PURELY ADDITIVE, which is what makes a narrow fix sufficient.** Measured per plan: `i3d6ml` added `tests/test_resumedupe.py`; `tx6q0h` added `tests/test_defect_report.py`, `tests/test_lane_retention.py`, `tests/test_shared_checkout_contract.py`; `sy7uwh` added `tests/test_orchestrator_probe_cache.py`. In all three, scope removed = none, and the only differing requirement key was `scope`. | `_frozen_scope_paths` / `_requirements_from_plan` diffed between each lane copy and its main copy |
| F4 | HIGH | spec `:1009` and plan `zzcrlo` | **WITHOUT THE SPEC AMENDMENT THE FIX IS DEFEATED BY AN APPROVED PLAN.** The spec lists "changed frozen requirements" as never-retryable, and `zzcrlo` (approved) names that list as the boundary it honors, so it would hand this failure back and refuse it again. The amendment is load-bearing, not tidying. | spec `:999-1010`; `zzcrlo`'s E-03 analysis quoting the never-retry list |
| F5 | MEDIUM | `receipt_is_current` docstring | **THIS EXACT BUG CLASS ALREADY BIT ONCE AND WAS ONLY PARTLY FIXED.** The whole-file digest "refused every self-finalizing run"; narrowing to the frozen region fixed evidence edits and left scope declarations. The precedent both justifies the fix and proves the shape (narrow the predicate, do not remove it). | `agent_workflows/ipd_lifecycle.py:844-852` |
| F6 | MEDIUM | the receipt file | **THE RECEIPT STORES ONLY THE DIGEST, so a structural comparison cannot decompose the receipt side.** `i3d6ml.receipt.json` carries `frozen_region_digest` and no payload. E-03 must therefore compare the plan text against something reconstructible, or state honestly that a v2 receipt cannot be decomposed and say what E-04 needs instead. Discovered at authoring so the executor does not hit it mid-item. | the receipt's own keys, read at authoring |
| F7 | LOW | run summary | NOT THIS PLAN'S TO FIX, recorded so it is not conflated: the same run preserved a lane over 4,176 "unknown IGNORED" files that are the run's own `commit-msg-*.txt` scratch and `__pycache__/*.pyc`. That is a retention-classification nit, unrelated to the receipt, and it belongs in its own item. | the `lane aw/lane/3dki3o PRESERVED` diagnostic |

## Proposed changes (ordered, validatable)

1. Reproduce the three-way asymmetry as fixtures (E-01) and measure every frozen-region consumer (E-02).
2. Add a structural per-category frozen-region comparison, leaving `receipt_is_current` semantics intact (E-03).
3. Accept an additive widening at finalize when every added path carries a `--scope-reason`; refuse otherwise (E-04).
4. Keep a narrowing, and a mixed add-plus-remove, refusing loudly with the path named (E-05).
5. Amend the spec's never-retry clause to split a requirement change from an additive widening (E-06).
6. Report whether the fix would have saved each of the three stranded plans (E-07).

## Deferred / out of scope (with reason)

- THE RETRY MACHINERY. `zzcrlo` owns handing a refused finalize back to the same agent. This plan removes one CAUSE of refusal; it does not touch dispatch, budget, or the send-back path. The two compose: fewer refusals to hand back.
- THE `check.scope-drift` ADVISORY AND WHAT `base_head` MEANS. `wmnmei` owns that and explicitly defers a lifecycle change to a follow-up plan, which this is. This plan does not touch `check_engine.py`.
- THE OUT-OF-SCOPE-MUTATION REFUSAL and the scope-collision rule. Both stay exactly as they are; a widening is a DECLARATION change, not a mutation, and conflating them would weaken a real guard.
- THE 4,176-FILE LANE-RETENTION NOISE (F7). Real, unrelated, and its own item.
- LETTING AN AGENT WIDEN SCOPE AT `begin` TIME or re-freezing mid-run. Deliberately not proposed: a re-freeze mid-execution would let an agent rewrite its reviewed contract and then bless it, which is the thing the freeze exists to prevent.

## Scope check

- Over-scope: none. Every item is contained in the one asymmetry, its spec clause, and the report on the three measured incidents.
- Under-scope: none for the cause. The three stranded plans are REPORTED (E-07), not finalized here, because finalizing them is a lifecycle act on other plans and needs its own attention.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures; a pre-existing failure must be named rather than absorbed.
2. E-01's three-way fixture, pasted, showing the two refusals and one acceptance BEFORE the change, and the additive case accepted AFTER while case (b) still refuses.
3. E-05's negative controls: a removal refuses and names the path; a mixed add-plus-remove refuses.
4. A widening with a MISSING `--scope-reason` for one added path refuses (the accept must not be unconditional).
5. A LEGACY v1 receipt is NOT eligible for the widening accept, asserted explicitly.
6. `aw ipd lint --phase pre-transition` conforming on this plan.
7. `aw sanitize --agent` clean.

## Spec / documentation sync

THIS PLAN AMENDS A SPEC AND DECLARES IT. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` is in `- Scope-Paths:` because E-06 must edit `:1009`'s never-retry clause. WHY, since a spec edit changes the contract every other plan is reviewed against: that clause currently makes "changed frozen requirements" unconditionally never-retryable, which is right for a requirement rewrite and wrong for an additive scope declaration, and an approved plan (`zzcrlo`) names the clause as the boundary it will honor. Landing the code without the amendment would leave code and spec in direct conflict and let `zzcrlo` re-refuse the same failure. The amendment SPLITS the clause rather than deleting it: a changed requirement stays never-retryable.

## Open questions

### OQ-01: Should an additive widening require a `--scope-reason` per added path, or is the declaration itself sufficient?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the plan is executable under either answer and E-04 implements the STRICTER one by default (a reason is required per added path), which is the safe direction and can be relaxed without rework. The argument for requiring a reason: it matches what an out-of-scope edit already owes, and it keeps a widening from becoming a silent way to grow a fence. The argument against: the declaration IS the honest act this plan exists to reward, and demanding prose for it may reintroduce friction at the same moment. Recorded rather than decided because it is a usability-versus-rigor call on a gate the maintainer owns. If unanswered, the strict form ships.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted test output showing all THREE current behaviors at execution HEAD: fixture (a) additive-widening REFUSED with the STALE message quoted, fixture (b) requirement-rewrite REFUSED, and the third case (undeclared edit + `--scope-reason`) ACCEPTED. The asymmetry must be visible in the pasted output, not described.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted per-consumer table for `frozen_region_digest`, `receipt_is_current`, `_frozen_scope_paths` and `_requirements_from_plan`, produced by an actual search at execution HEAD (paste the search), with an explicit statement of every test that pins a digest literal and every consumer E-03 would affect. "No other consumers" is a claim that must be shown by the search, not asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new comparison function's output pasted for BOTH fixtures, showing it reports `scope_paths: added=[...]` with all requirement categories identical for (a), and a differing requirement category for (b). PLUS proof that `receipt_is_current` is UNCHANGED in behavior: fixture (b) still refuses, and an unmodified plan still returns True. PLUS the F6 resolution stated: how the receipt side was reconstructed, or the honest statement that a v2 receipt cannot be decomposed and what E-04 uses instead.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: fixture (a) FINALIZING when each added path carries `--scope-reason`, pasted end to end; the SAME fixture REFUSING when one added path lacks a reason; fixture (b) still refusing. PLUS the finalize evidence pasted, showing the accepted widening is recorded (which paths, which reasons) rather than passing silently.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted output showing a REMOVED scope path refuses with the removed path NAMED, and that a mixed add-plus-remove refuses rather than being accepted on its additions. PLUS the legacy-v1-receipt case asserted ineligible for the widening accept, since `:860-864` deliberately binds a v1 receipt to the whole-file rule.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the spec clause quoted BEFORE and AFTER, showing the split (requirement change stays never-retryable; additive widening becomes a finalize-time accept) and the measured incident cited as the rationale. PLUS every test that reads this spec text named and pasted passing, since a contract test reading the spec as a FILE would otherwise fail silently on a reworded clause.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: a per-plan statement for `i3d6ml`, `tx6q0h` and `sy7uwh` listing the paths each added and whether E-04's condition accepts it, with the measurement pasted rather than quoted from this plan's F3. Any plan that would STILL refuse is named as a finding with its reason. Explicit confirmation that none of the three was finalized by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with the STRICT form (a
`--scope-reason` per added path) and do not guess a relaxation. SCOPE FENCE: this plan declares
`agent_workflows/ipd_lifecycle.py`, two test files, and one spec file; an out-of-scope edit must be made
only if genuinely required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and
a declared path left unmodified needs a `--scope-ack`. THE IRONY IS DELIBERATE AND IS ALSO THE BEST
DOGFOOD: if executing this plan requires touching a file it did not declare, the executor will meet the
very refusal this plan removes. Record that if it happens; it is evidence, not an obstacle. THE HARD-MUST
HONESTY RULE: paste the ACTUAL command and test output for every `V-*`; never claim a test run you did
not run, and never soften a refusal into an acceptance to make an item pass. A gate that accepts one
case more than it should is worse than the bug this plan fixes. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours; this is a shared checkout with
concurrent sessions. After the gate, move this plan to `.aw/records/plans/executed/` via
`aw ipd finalize`, and do not claim done until `aw ipd lint --phase pre-transition` conforms and every
`V-*` above carries real observed evidence.

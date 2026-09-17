# IPD: Let a finalize accept a WIDENED Scope-Paths with a recorded reason instead of refusing the honest declaration

- Date: 2026-09-17
- Kind: child
- Concern: An executing agent that discovers it must touch a file its plan did not declare has exactly two options, and the system punishes the honest one. If it ADDS the path to `Scope-Paths` (the honest declaration), that edit changes the plan's frozen region, `receipt_is_current` returns False, and `finalize_precheck` refuses with "the begin receipt ... is STALE", stranding correct and tested work on a lane. If it instead edits the file WITHOUT declaring it, `aw ipd finalize --scope-reason <path>=<why>` accepts the run. So the undeclared edit finalizes and the declared one does not. Measured 2026-09-16/17 in run `run-20260917T023628Z-4108757`: this fired on THREE of the twelve items (`i3d6ml`, `tx6q0h`, `sy7uwh`), costing $95.71 of the run's $212.60, stranding three lanes, and cascading to leave orchestrator `5e4sb6` `dependency-blocked` and backlog items `dhuape` and `alw22r` unevaluated. In all three the ONLY differing frozen field was `scope`, and in all three the change was purely ADDITIVE. REVIEW CORRECTED THE SECOND HALF OF THAT SENTENCE, and the correction MATTERS because it changes what E-04 must build: an UNCOMMITTED undeclared edit is not "accepted with a reason", it is DISREGARDED ENTIRELY and needs no reason at all (`_working_tree_path_is_owned` finds no ownership evidence for a path that matches no `Scope-Paths` entry and appears in no commit). Reproduced at review: `disregarded_unowned_paths: ['tests/test_extra.py']`, `out_of_scope_paths: []`, precheck `rc=0`. A `--scope-reason` becomes REQUIRED only when the undeclared path rides in a COMMIT cohesive with a declared one. So the asymmetry the plan exists to fix is WIDER than "reason versus refusal": the honest declaration is refused while the concealed uncommitted edit is not even noticed. See F-8.
- Scope: Make an ADDITIVE widening of `Scope-Paths` a recordable, justified condition at finalize rather than a hard refusal, while keeping every genuinely contract-changing edit (a REMOVED scope path, a rewritten E/V requirement, a changed `## Scope` line) refusing exactly as it does today. Amends the spec clause that lists "changed frozen requirements" as never-retryable so it distinguishes an additive widening from a contract rewrite. Does NOT touch the retry machinery, the scope-collision rule, or the out-of-scope-mutation refusal.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_receipt_requirement_digest.py, tests/test_ipd_lifecycle_cli.py, tests/test_finalize_isolated_commit.py, tests/test_rununify_host_descriptor.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Blocks-Release: next
- Status: approved
- Readiness: go-pending-approval
- Set: rcptwiden
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 63425h
- Approval: 2026-09-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-17 approved (aw set): status set to approved
- 2026-09-17 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 all FIXED; 2 non-blocking OQs (OQ-01 reason-per-added-path, OQ-02 directory/glob eligibility) both ship fail-closed. Reproduced the asymmetry end to end; withdrew false F-6; added the runner half, E-08 fence-neutering and E-09 ineligible shapes.

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a measured, three-times-reproduced failure in run `run-20260917T023628Z-4108757`. VERIFIED NO PENDING PLAN OWNS THIS before authoring, which is why it is a new plan rather than a note on an existing one: `wmnmei` (rcptstale-01, approved) analyses what the frozen `base_head` MEANS for the `check.scope-drift` advisory and explicitly excludes `ipd_lifecycle.py` from its scope ("If E-02 or E-03 concludes the advisory cannot be fixed without a lifecycle change, that is a FINDING and a follow-up plan, not a silent scope widening"); `zzcrlo` (finalback-01, approved) hands a refused finalize BACK to the same agent but its own analysis puts "changed frozen requirements" on the never-retry boundary it promises to honor, so it would re-dispatch this failure and refuse it again rather than fix it; `tgop8e` (stalecrit-01) re-derives a plan's target population at execution time, a different staleness. So the cause is unowned. THE ASYMMETRY IS THE DEFECT, not the freeze: freezing the reviewed contract is correct and `receipt_is_current`'s own docstring records that an earlier whole-file digest "refused every self-finalizing run" and was narrowed for exactly this class of false positive. This plan finishes that narrowing for the one case it left: an ADDITIVE scope declaration.

## Goal

Stop the system from refusing the honest act. An agent that declares a newly-needed path should finalize
with that declaration recorded; an agent that rewrites its reviewed contract should still be refused.

Today those two are indistinguishable because `frozen_region_digest` hashes a single opaque payload, so
ANY change to the frozen region yields one boolean. The fix is to compare the frozen region
STRUCTURALLY when the digests differ, and to treat exactly one difference class (a superset of
`scope_paths`, with every requirement category byte-identical) as justifiable rather than fatal.

THE MECHANISM IS ALREADY AVAILABLE, WHICH REVIEW ESTABLISHED AND F-6 GOT WRONG. The receipt stores
`scope_paths` VERBATIM beside the digest (`ipd_lifecycle.py:1095`, `"scope_paths": _frozen_scope_paths(plan_text)`;
confirmed by generating a real receipt at review, whose keys include `scope_paths: ['agent_workflows/demo.py',
'tests/test_demo.py']`), and `finalize_precheck` ALREADY reads it (`:1630`). So the receipt side does not need
reconstructing and no new field is needed. The comparison E-03 must implement is a SUBSTITUTION TEST that needs
no new stored state:

> take the CURRENT plan text, replace its `scope_paths` and its `requirements["scope"]` with the RECEIPT's
> stored `scope_paths`, re-serialize with `frozen_region_digest`'s exact payload shape, and compare to the
> stored digest. Equality PROVES every non-scope requirement category is byte-identical, because the digest
> is a collision-resistant hash over the whole payload. Inequality means something other than scope changed.

VERIFIED AT REVIEW on all three measured incidents: the substitution reproduces the stored digest for
`i3d6ml`, `tx6q0h` and `sy7uwh` (True in each case), and a negative control that additionally rewrites an
E-item's action text does NOT reproduce it (False in each case). That is the whole predicate, it is a dozen
lines, and it needs no receipt schema change. E-03 must implement THIS rather than inventing a v3 receipt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the failure and the blast radius before changing a gate

- [x] E-01 REPRODUCE THE ASYMMETRY AS A TEST FIRST, so the fix has a falsifiable target and the claim in this plan's Concern is proven rather than cited. Build two fixture plans from one begin receipt: (a) one whose `Scope-Paths` gained a path and whose requirements are otherwise identical, and (b) one whose `## Scope` line or an `E-*` action text was rewritten. Assert that TODAY both are refused identically by `receipt_is_current` / `finalize_precheck`, and paste the refusal message for each. Then assert the third case for contrast: a plan that edited a file NOT in `Scope-Paths` and finalizes with `--scope-reason`, showing it is ACCEPTED. That three-way fixture is the specification for E-03.
  - Depends on: none
  - Expected outcome: a pasted test run showing all three current behaviors, with the two refusals byte-identical in kind and the third accepted, so the asymmetry is demonstrated rather than asserted.
  - Execution state: performed

- [x] E-02 MEASURE EVERY CONSUMER OF THE FROZEN REGION AT EXECUTION HEAD, and refuse to proceed to E-03 on this plan's list. `frozen_region_digest` (`agent_workflows/ipd_lifecycle.py:474`) is consumed by `receipt_is_current` (`:837`) and written by `begin` (`:1093`); `_frozen_scope_paths` (`:564`) and `_requirements_from_plan` (`:516`) are its inputs. Find every OTHER reader of any of the four, including tests that pin the digest as a literal and any hook or CLI path, and state per consumer whether a structural comparison changes what it sees. A consumer that stores or compares the digest VALUE is a compatibility surface; name it. Do not change behavior in this item.
  - THE CONSUMERS REVIEW ALREADY LOCATED, to be re-derived rather than trusted: `check_engine.py:1366` calls `_frozen_scope_paths` for the `check.scope-drift` advisory (which compares against the PLAN's current scope, not the receipt's, so a widening SILENCES the advisory for the added path the moment it is declared: state whether that is correct); `run_evidence.py:1431` names `ipd_lifecycle._frozen_scope_paths` as a string; `runner_shared.py:5958-6093` documents a DELIBERATE divergence from `frozen_region_digest` for the orchestrator probe cache and must not be changed; `tests/test_orchestrator_probe_cache.py:541-594` asserts `frozen_region_digest` does NOT move on a child-table edit and DOES move on an E-item edit; `tests/test_event_derived_lifecycle.py:288` and `tests/test_dirty_base_gate.py:395` assert the SOURCE TEXT contains `_frozen_scope_paths` / `_frozen_scope_paths(plan_text)`, so a rename or a call-shape change breaks them. Review found NO test pinning a digest as a hex literal; confirm that independently rather than inheriting it.
  - Depends on: none
  - Expected outcome: a pasted per-consumer table (symbol, file:line, what it does with the digest, whether E-03 affects it), with an explicit statement of any consumer that would need a change, any test that pins a digest literal, any test that pins SOURCE TEXT, and an explicit answer on the `check.scope-drift` interaction.
  - Execution state: performed

### Task group 2: distinguish the two cases, and keep the refusal for the real one

- [x] E-03 ADD A STRUCTURAL FROZEN-REGION COMPARISON that returns WHICH categories differ instead of one boolean, leaving `receipt_is_current`'s signature and current semantics intact so nothing that calls it changes meaning. IMPLEMENT THE SUBSTITUTION TEST STATED IN THE GOAL, which review verified against all three incidents; do NOT invent a receipt field and do NOT bump the receipt schema. The function takes the receipt and the plan text and returns: the `scope_paths` ADDED set, the REMOVED set, and one boolean `non_scope_identical` obtained by substituting the receipt's stored `scope_paths` (`ipd_lifecycle.py:1095`, read today at `:1630`) into the current plan's payload and comparing against the stored `frozen_region_digest`. The digest stays the fast path and the authority for "unchanged"; the structural comparison runs ONLY when the digests differ, so an unchanged plan costs nothing new. MAKE IT PURE: take the receipt dict and the plan text, touch no filesystem, so it is unit-testable without a git fixture. THE PAYLOAD SHAPE MUST BE SHARED, NOT RE-TYPED: extract `frozen_region_digest`'s payload construction into one helper both it and this function call, because a second hand-written copy of the `{"scope_paths": ..., "requirements": ...}` literal is a silent-drift hazard on a gate input, and a drifted copy would make the substitution never match and the accept never fire.
  - Depends on: E-01, E-02
  - Expected outcome: a pure, tested function returning `(added, removed, non_scope_identical)`; ONE payload builder shared with `frozen_region_digest` (assert it, do not merely state it); `receipt_is_current` behavior byte-identical for both the unchanged and the requirement-rewritten cases, proven by E-01's fixtures still refusing case (b).
  - Execution state: performed

- [x] E-04 TEACH THE FINALIZE PATH TO ACCEPT AN ADDITIVE WIDENING WITH A RECORDED REASON, and only that. The accept condition is narrow and must be stated in code: `non_scope_identical` true AND `removed` empty AND `added` non-empty. Any removal, any requirement change, or both together still refuses with today's message. The reason is not optional: reuse the existing `--scope-reason PATH=WHY` surface rather than adding a flag, and a widening with no reason for a given added path REFUSES. Record the accepted widening in the finalize evidence so it appears in the run record and the plan's history rather than passing silently.
  - THE REASON DEMAND CANNOT BE LEFT TO THE EXISTING RECONCILIATION, WHICH REVIEW PROVED WOULD MAKE THE FLAG VACUOUS (F-9). `finalize_precheck` computes `out_of_scope` against the RECEIPT's `scope_paths` (`:1630`), so an added path is judged against the OLD fence. Measured at review with the staleness check stubbed out: for an UNCOMMITTED edit to an added path, `out_of_scope_paths: []` and `disregarded_unowned_paths: ['tests/test_extra.py']`, i.e. `_reconcile_scope` demands NOTHING and a `--scope-reason` for that path is never required. So if E-04 merely lets the widening through, the strict form OQ-01 mandates is silently not implemented in the commonest case. E-04 must therefore ADD AN EXPLICIT PER-ADDED-PATH REASON REQUIREMENT that does not depend on the path landing in `out_of_scope`: require a reason for EVERY member of `added`, unconditionally, and refuse naming the paths that lack one.
  - AND IT MUST NOT DOUBLE-DEMAND. In the COMMITTED-cohesive case the same path DOES appear in `out_of_scope` (measured: `out_of_scope_paths: ['.aw/state/ipd-lifecycle/abc123.receipt.json', 'tests/test_extra.py']`), so the two demands would otherwise both fire for one path. One reason must satisfy both; assert that a single `--scope-reason` per added path suffices in BOTH the committed and the uncommitted case, and that the recorded evidence names the path once, not twice.
  - THE RUNNER MUST BE ABLE TO SUPPLY THE REASON OR THE FIX DOES NOT REACH THE MEASURED INCIDENT. `compute_scope_reconciliation` (`runner_shared.py:8562-8596`) builds its reason map ONLY from `audit["out_of_scope_paths"]`, so for an uncommitted widened path it produces no entry and `driver_finalize` (`oc_runipd.py:1304-1328`) passes no `--scope-reason` for it. The three measured incidents were finalized BY THE RUNNER, not by hand. So E-04 must ALSO surface the added set in the precheck evidence under its own key (e.g. `scope_audit["widened_paths"]`) and teach `compute_scope_reconciliation` to auto-reason those paths in the same shape it already auto-reasons an out-of-scope path. WITHOUT THIS the fix converts a STALE refusal into a MISSING-REASON refusal and strands exactly the same three lanes. Add `agent_workflows/runner_shared.py` to the fence for this and nothing else; do NOT alter what any gate DECIDES on the paths it already judges.
  - Depends on: E-03
  - Expected outcome: E-01's case (a) finalizes when each added path carries a `--scope-reason` and REFUSES when one does not, in BOTH the committed and the uncommitted variant; case (b) still refuses; ONE reason satisfies both demands for one path; the runner's auto-reconciliation supplies the reason unaided, proven by driving `compute_scope_reconciliation` on a widened fixture; the accepted widening is visible in the finalize evidence, pasted.
  - Execution state: performed

- [x] E-05 KEEP THE REFUSAL LOUD FOR A NARROWING, which is the direction this plan must not soften and which no measured incident asked for. A REMOVED scope path is a contract reduction: it can retroactively make an already-made edit out-of-scope and it is how a plan could be quietly re-fenced around whatever was touched. Assert it refuses with a message naming the removed path, distinct from the additive case's acceptance, and add the negative-control test that a superset-plus-one-removal is treated as a REMOVAL rather than as a widening. COMPARE AS SETS OF ENTRY STRINGS, and state so in code: the plan's `Scope-Paths` order is not semantic and a reordering must not read as a removal-plus-addition.
  - Depends on: E-03
  - Expected outcome: pasted tests showing a removal refuses and names the path, that a mixed add-and-remove refuses rather than being accepted on the strength of its additions, and that a pure REORDERING of the same entries is treated as unchanged.
  - Execution state: performed

- [x] E-08 REFUSE A FENCE-NEUTERING WIDENING, which is the one way this plan could make the system LESS safe and which the strict-superset rule alone does NOT catch. Measured at review with `_scope_match`: adding the single entry `tests/` is a strict superset of `{agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py}` and brings EVERY file under `tests/` inside the fence; adding `agent_workflows` brings the whole package; adding `*` matches `tests/test_secret.py`, `agent_workflows/check_engine.py`, `RELEASING.md` and `.aw/records/specs/x.spec.md` all at once. Under E-04 as first authored, an agent could convert a four-file fence into a whole-repo fence with ONE added entry and ONE reason string, and every subsequent edit would then be in-scope and demand nothing. That is strictly worse than the bug being fixed, because today the refusal at least stops. SO: an added entry that is a DIRECTORY or contains a GLOB is NOT eligible for the widening accept; only a LITERAL FILE PATH is. Refuse a directory-or-glob addition with today's stale message and a distinct finding naming the offending entry and why. Use the same classification `_scope_match` (`:1475-1505`) branches on (trailing `/`, trailing `/**`, any of `* ? [`, and the bare-directory prefix case) so the eligibility rule and the matching rule cannot disagree; a bare `agent_workflows` matches a prefix and MUST be treated as a directory even though it contains no glob character.
  - Depends on: E-03
  - Expected outcome: pasted tests showing each of `tests/`, `agent_workflows`, `agent_workflows/**` and `*` REFUSED as an added entry with the entry named, while a literal `tests/test_resumedupe.py` is accepted; plus one test asserting the eligibility classifier and `_scope_match` agree on a shared table of entry shapes.
  - Execution state: performed

- [x] E-09 PIN THE THREE INELIGIBLE RECEIPT SHAPES, so the accept cannot leak into a case it was never reasoned about. (a) A LEGACY v1 receipt carries no `frozen_region_digest` and is deliberately bound to the whole-file rule (`:860-864`, "must not be spuriously ACCEPTED by a rule it was never bound under"); it is NOT eligible, and the substitution test must not even be attempted on it. (b) A GRANDFATHERED plan has `_frozen_scope_paths == []` while `requirements["scope"] == ["grandfathered", <the free-form Scope prose>]` (verified at review on `.aw/records/plans/executed/20260823-execset-04-31744f-*.ipd.md`), so "adding a path" is not a widening of an allowlist but a CONVERSION from no-fence to fence, and a plan that becomes non-grandfathered mid-execution has changed its scope MODEL rather than extended it; NOT eligible. (c) The mirror case, a plan that BECOMES grandfathered mid-execution, empties the allowlist and must read as a REMOVAL, not as an unchanged empty set; refuse it. Each of the three gets its own test with the reason in the docstring.
  - Depends on: E-03
  - Expected outcome: three pasted tests, one per ineligible shape, each refusing with today's message; plus an assertion that the v1 path does not invoke the new comparison at all.
  - Execution state: performed

### Task group 3: amend the contract this changes, and say so

- [x] E-06 AMEND THE SPEC CLAUSE THAT THIS CHANGES, because it is a shipped contract and leaving it would put the code and the spec in direct conflict. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:1009` lists "changed frozen requirements" in the never-retry class (verified at review: that is the exact line, in Section 5.5's second list). That clause is CORRECT for a requirement rewrite and WRONG for an additive scope declaration, and plan `zzcrlo` (finalback-01, approved) explicitly promises to honor that list as its retry boundary, so if this plan lands without the amendment `zzcrlo` will re-dispatch and re-refuse exactly this failure. Split the clause: a changed REQUIREMENT stays never-retryable; an ADDITIVE scope widening with a recorded reason becomes a finalize-time accept (not a retry). State the measured incident as the amendment's rationale. WRITE THE ELIGIBILITY CONDITIONS INTO THE SPEC, NOT ONLY INTO THE CODE: name the literal-file-path restriction (E-08) and the three ineligible shapes (E-09), because a spec that authorizes "an additive widening" without them authorizes the whole-repo fence E-08 refuses. THE SPEC IS APPROVED AND RELEASE-GATING, and `zzcrlo`'s own execution contract forbids ITS executor from editing it; this plan holds the amendment authority for this clause and no other. Do not touch any other section.
  - REVIEW MEASURED THE TEST EXPOSURE, which is smaller than the boilerplate suggests: three test files read this spec FILE (`tests/test_run_flag_surface.py:48`, `tests/test_run_evidence_completion.py:1024`, `tests/test_run_selection_policy.py:806`), and all three parse OTHER sections (4.1's abort classes, 4.2's `RUN-*` table, 2.5a's draft gate). No test reads Section 5.5's never-retry list, so the amendment breaks no contract test. RE-VERIFY that at execution HEAD rather than trusting it, and if a test HAS come to read 5.5, treat that as a finding and update it deliberately rather than reflexively.
  - Depends on: E-04, E-05, E-08, E-09
  - Expected outcome: the amended clause quoted before and after, with the split stated, the eligibility conditions written in, and the incident cited; the three spec-reading test files named and pasted passing.
  - Execution state: performed

- [x] E-07 PROVE END TO END THAT THE THREE STRANDED PLANS WOULD HAVE FINALIZED, as a check that the fix addresses the real incident rather than a plausible model of it. Not a paper check: reconstruct each case from git (the pre-widening plan text is `<sha>^:<path>` and the post-widening text is `<sha>:<path>` for `i3d6ml`=`89324096`, `tx6q0h`=`e5fbe9c4`, `sy7uwh`=`20311677`, all verified at review), issue a receipt against the BEFORE text, then drive the WHOLE path the runner drives, `compute_scope_reconciliation` INCLUDED, and show the finalize is accepted with the reason the runner itself generated. A per-plan assertion that "E-04's condition accepts it" is NOT sufficient, because F-10 is exactly a case where the condition accepts and the run still refuses. If ANY of the three would still refuse, say so plainly and name why: that is a finding about this plan's completeness, not a detail. Report only; do NOT finalize those real plans, and do NOT write a receipt for a real plan id into `.aw/state/`; work on copies in a temporary tree.
  - REVIEW ALREADY MEASURED THE FROZEN-REGION DELTA for all three, so E-07 re-derives rather than discovers: added paths are `i3d6ml` -> `tests/test_resumedupe.py`; `tx6q0h` -> `tests/test_defect_report.py`, `tests/test_lane_retention.py`, `tests/test_shared_checkout_contract.py`; `sy7uwh` -> `tests/test_orchestrator_probe_cache.py`. Removed: none in any case. Differing requirement categories: `scope` only; `must` and `validation` identical in all three. Every added entry is a LITERAL FILE PATH, so all three pass E-08's eligibility rule. Re-measure and paste; a mismatch against these numbers is a finding.
  - Depends on: E-04, E-08
  - Expected outcome: for each of the three, the reconstructed run driven end to end with the runner's own reconciliation, the generated reason pasted, and the finalize outcome pasted; plus explicit confirmation that no real plan was finalized and no receipt was written for a real plan id.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE FREEZE IS RIGHT AND ITS HISTORY MATTERS. `receipt_is_current` (`agent_workflows/ipd_lifecycle.py:837`) already survived exactly this class of bug once: its docstring records that the ORIGINAL whole-file `plan_content_digest` "was self-defeating" because a correct execution MUST edit its own plan, so it "refused every self-finalizing run" and was narrowed to the frozen contract (wtiso-03 `rchpms` E-03, backlog `xmqv5l`). This plan finishes that narrowing for the one false-positive class it left behind. It does NOT argue against freezing.
- THE DIGEST IS AN OPAQUE PAYLOAD HASH, BUT ITS SCOPE INPUT IS STORED IN THE CLEAR. `frozen_region_digest` (`:474`) serializes `{"scope_paths": sorted(...), "requirements": {...}}` with `json.dumps(sort_keys=True)` and hashes it, so one changed path and a rewritten requirement are indistinguishable FROM THE DIGEST ALONE. But `begin` also writes `scope_paths` verbatim into the receipt (`:1095`) and `finalize_precheck` already reads it (`:1630`), which is exactly the input a substitution test needs. So the structural comparison is a dozen lines over existing state, not a schema change (review correction to F-6).
- THE `scope` REQUIREMENT CATEGORY AND `scope_paths` ARE NOT THE SAME FIELD, and conflating them is the likeliest E-03 bug. For a normal plan `requirements["scope"] == _frozen_scope_paths(text)` (verified on this plan). For a GRANDFATHERED plan `_frozen_scope_paths` is `[]` while `requirements["scope"]` is `["grandfathered", <the free-form Scope prose>]` (verified on `.aw/records/plans/executed/20260823-execset-04-31744f-*.ipd.md`). A substitution that replaces only one of the two will silently mis-compare, which is why E-09 pins the grandfathered shapes as INELIGIBLE rather than trying to reason about them.
- LEGACY v1 RECEIPTS FALL BACK TO THE WHOLE-FILE RULE deliberately (`:860-864`), so a pre-Phase-2 receipt "must not be spuriously ACCEPTED by a rule it was never bound under". E-03/E-04 must leave that fallback alone; a v1 receipt is not eligible for the widening accept (E-09).
- THE WORKER-ROLE ENV VAR BREAKS TWO LIFECYCLE TESTS AND IS NOT A CODE FAULT. `run_begin` and `run_finalize` refuse outright when `AW_EXECUTION_ROLE=worker` (`:3686`, `:3866`, `AW-LIFECYCLE-ROLE-001`), so under a managed worker lane `tests/test_ipd_lifecycle_cli.py` reports `2 failed` on the two CLI happy-path tests. Measured at review: `env -u AW_EXECUTION_ROLE python3 -m pytest` on the three lifecycle files gives `91 passed`. Say which form you ran; do not edit the tests.
- THE RUNNER, NOT A HUMAN, PERFORMS THE FINALIZE THAT FAILED. `driver_finalize` (`oc_runipd.py:1294-1341`) assembles `--scope-reason` flags from `compute_scope_reconciliation` (`runner_shared.py:8562`), whose reason map is derived ONLY from `out_of_scope_paths`. Any change to what finalize DEMANDS must be matched by a change to what the runner SUPPLIES, or the demand simply cannot be met in the automated path. This is the single most important convention for E-04.
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
| F6 | ~~MEDIUM~~ WITHDRAWN AT REVIEW | the receipt file | **WITHDRAWN: FALSE AS WRITTEN, AND THE CORRECTION SIMPLIFIES E-03 SUBSTANTIALLY.** The claim was "the receipt stores only the digest, so a structural comparison cannot decompose the receipt side". It stores `scope_paths` VERBATIM (`ipd_lifecycle.py:1095`) and `finalize_precheck` already reads it (`:1630`). A real receipt generated at review carries `['actor', 'base_head', 'frozen_region_digest', 'kind', 'plan_content_digest', 'plan_id', 'plan_path', 'pre_execution', 'requirement_digest', 'schema_version', 'scope_paths', 'timestamp']`. So the substitution test in the Goal works with no schema change, and E-03's escape hatch ("state honestly that a v2 receipt cannot be decomposed") is void: an executor taking it would invent a v3 receipt this plan does not need. Corrected rather than deleted so the reasoning is auditable. | a receipt generated at review via `LC.begin` on the `tests/test_receipt_requirement_digest.py` fixture; substitution reproduces the stored digest for all three incidents, negative control does not |
| F7 | LOW | run summary | NOT THIS PLAN'S TO FIX, recorded so it is not conflated: the same run preserved a lane over 4,176 "unknown IGNORED" files that are the run's own `commit-msg-*.txt` scratch and `__pycache__/*.pyc`. That is a retention-classification nit, unrelated to the receipt, and it belongs in its own item. | the `lane aw/lane/3dki3o PRESERVED` diagnostic |
| F8 | HIGH (added at review) | `_working_tree_path_is_owned` via `finalize_precheck` | **THE ASYMMETRY IS WIDER THAN THE CONCERN STATED, AND THE WIDER HALF IS WORSE.** The Concern says the undeclared edit "finalizes fine with `--scope-reason`". For an UNCOMMITTED undeclared edit no reason is demanded AT ALL: the path is DISREGARDED as unowned. Reproduced at review: `out_of_scope_paths: []`, `disregarded_unowned_paths: ['tests/test_extra.py']`, precheck `rc=0`. A reason becomes required only when the path rides in a commit cohesive with a declared one (then: `out_of_scope_paths: ['.aw/state/ipd-lifecycle/abc123.receipt.json', 'tests/test_extra.py']`). So concealment is not merely cheaper than honesty, it is FREE in the common case, which strengthens the plan's premise and changes E-04's construction. | two end-to-end fixtures driven at review through `LC.begin` + `LC.finalize_precheck` + `LC.finalize` |
| F9 | BLOCKER (added at review) | E-04 as first authored | **THE `--scope-reason` REQUIREMENT WOULD HAVE BEEN VACUOUS, so the plan would have shipped the LENIENT form while claiming the strict one.** `finalize_precheck` computes `out_of_scope` against the RECEIPT's `scope_paths` (`:1630`), so a newly-added path is judged against the OLD fence and, uncommitted, lands in `disregarded_unowned` where `_reconcile_scope` demands nothing. Measured with the staleness check stubbed: the widened uncommitted path yields `out_of_scope_paths: []`. E-04 therefore needs its OWN unconditional per-added-path reason demand, plus proof one reason satisfies both demands in the committed case. Without this, OQ-01's "the strict form ships" is false. | `LC.receipt_is_current` stubbed True, then `finalize_precheck` driven on a widened fixture, uncommitted and committed |
| F10 | BLOCKER (added at review) | `runner_shared.compute_scope_reconciliation:8562-8596`; `oc_runipd.driver_finalize:1304-1328` | **THE RUNNER CANNOT SUPPLY THE REASON, SO THE FIX WOULD NOT HAVE SAVED THE THREE MEASURED LANES.** All three incidents were finalized BY THE RUNNER. The runner's auto-reconciliation builds its reason map only from `audit["out_of_scope_paths"]`, which (F9) does not contain an uncommitted widened path, so `driver_finalize` passes no `--scope-reason` for it. Net effect of E-04 alone: a STALE refusal becomes a MISSING-REASON refusal and the same three lanes strand. E-04 must surface the added set in the precheck evidence and teach the runner to auto-reason it; `runner_shared.py` added to the fence for exactly that. | source read at both call sites; the reason-map construction is `{p: ... for p in out_of_scope}` |
| F11 | HIGH (added at review) | E-04's superset rule as first authored | **A STRICT SUPERSET CAN NEUTER THE WHOLE FENCE, which the accept condition did not exclude.** Measured with `_scope_match`: adding `tests/` is a strict superset and admits every file under `tests/`; adding `agent_workflows` admits the package (a bare directory matches by PREFIX with no glob character, `:1504-1505`); adding `*` admits `tests/test_secret.py`, `agent_workflows/check_engine.py`, `RELEASING.md` and `.aw/records/specs/x.spec.md`. One added entry plus one reason string would convert a four-file fence into a repo-wide one, after which nothing is out of scope and nothing demands a reason. Strictly worse than the bug. E-08 restricts eligibility to LITERAL FILE PATHS. | `_scope_match` driven at review over the five entry shapes |
| F12 | MEDIUM (added at review) | `check_engine.py:1366` | **A WIDENING SILENCES `check.scope-drift` FOR THE ADDED PATH, and the plan does not say whether that is intended.** The advisory reads `_frozen_scope_paths(text)` from the PLAN's current text, not from the receipt, so declaring a path removes it from the drift report immediately, before any finalize accepts anything. That is arguably correct (the path is now declared), but it means the honest declaration is ALSO the way to silence the advisory, and this plan is the one that makes declaring safe. E-02 must state the interaction explicitly. Note `wmnmei` owns the advisory and this plan must not edit `check_engine.py`; reporting the interaction is not editing it. | source read; `wmnmei`'s own scope statement excludes `ipd_lifecycle.py` and this plan excludes `check_engine.py`, so the two do not collide |
| F13 | MEDIUM (added at review) | `tests/test_receipt_requirement_digest.py` | **THE FILE THAT ACTUALLY OWNS THIS BEHAVIOR WAS NOT IN `Scope-Paths`.** That file holds `FrozenRegionDigestTests` and `ReceiptBindingTests`, i.e. every existing assertion about `frozen_region_digest`, the v2 receipt binding and the legacy v1 fallback (`:99-249`), which is precisely where E-03's and E-09's tests belong. The plan declared `tests/test_ipd_lifecycle_cli.py` and `tests/test_finalize_isolated_commit.py` instead. Added to the fence at review, along with `tests/test_rununify_host_descriptor.py` for the runner half (F10). Filed with deliberate irony: this plan exists because an undeclared-but-needed test file strands a lane. | file read at review; `rg -l frozen_region_digest tests/` |

## Proposed changes (ordered, validatable)

1. Reproduce the asymmetry as fixtures (E-01) and measure every frozen-region consumer (E-02).
2. Add the substitution-based structural frozen-region comparison, leaving `receipt_is_current` semantics intact, with ONE shared payload builder (E-03).
3. Accept an additive widening at finalize when every added path carries a `--scope-reason`, demanded unconditionally per added path and supplied by the runner's auto-reconciliation (E-04).
4. Keep a narrowing, and a mixed add-plus-remove, refusing loudly with the path named; treat a reordering as unchanged (E-05).
5. Refuse a directory-or-glob addition, so a widening cannot neuter the fence (E-08).
6. Pin the three ineligible receipt shapes: legacy v1, becoming-grandfathered, and grandfathered-plus-paths (E-09).
7. Amend the spec's never-retry clause to split a requirement change from an additive widening, carrying the eligibility conditions into the spec text (E-06).
8. Report whether the fix would have saved each of the three stranded plans, end to end through the runner (E-07).

## Deferred / out of scope (with reason)

- THE RETRY MACHINERY. `zzcrlo` owns handing a refused finalize back to the same agent. This plan removes one CAUSE of refusal; it does not touch dispatch, budget, or the send-back path. The two compose: fewer refusals to hand back.
- THE `check.scope-drift` ADVISORY AND WHAT `base_head` MEANS. `wmnmei` owns that and explicitly defers a lifecycle change to a follow-up plan, which this is. This plan does not touch `check_engine.py`. E-02 REPORTS the interaction F-12 found (a widening silences the advisory for the added path) because an executor must know it; reporting is not editing, and the decision about whether the advisory should read the receipt's scope instead of the plan's belongs to `wmnmei`.
- THE OUT-OF-SCOPE-MUTATION REFUSAL and the scope-collision rule. Both stay exactly as they are; a widening is a DECLARATION change, not a mutation, and conflating them would weaken a real guard.
- CLOSING THE DISREGARDED-UNOWNED HOLE F-8 FOUND. That an UNCOMMITTED undeclared edit is disregarded entirely, demanding no reason, is a real gap in the other direction, and this plan deliberately does NOT close it: `_working_tree_path_is_owned`'s docstring records that disregarding an unattributable dirty path is a deliberate shared-checkout concession (demanding a reason for a co-worker's file "would force a FALSE claim into this plan's permanent record"), and tightening it needs its own analysis of the concurrent-agent case. This plan makes HONESTY WORK; it does not make CONCEALMENT fail. File the gap as a backlog item rather than absorbing it.
- THE 4,176-FILE LANE-RETENTION NOISE (F7). Real, unrelated, and its own item.
- LETTING AN AGENT WIDEN SCOPE AT `begin` TIME or re-freezing mid-run. Deliberately not proposed: a re-freeze mid-execution would let an agent rewrite its reviewed contract and then bless it, which is the thing the freeze exists to prevent.

## Scope check

- Over-scope: none. Every item is contained in the one asymmetry, the runner path that must be able to exercise it, its spec clause, and the report on the three measured incidents. `runner_shared.py` was added at review NOT to widen the plan's ambition but because F-10 measured that without it the fix does not reach the incident it cites.
- Under-scope: none for the cause, after review added E-08 (fence-neutering), E-09 (ineligible receipt shapes) and the runner half of E-04. The three stranded plans are REPORTED (E-07), not finalized here, because finalizing them is a lifecycle act on other plans and needs its own attention. The disregarded-unowned hole F-8 found is deliberately deferred with a stated reason rather than silently omitted.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures; a pre-existing failure must be named rather than absorbed. NOTE FOR THE EXECUTOR, measured at review: if `AW_EXECUTION_ROLE=worker` is set in your environment, `tests/test_ipd_lifecycle_cli.py` fails two tests (`test_cli_happy_path_exit_0_and_writes_receipt`, `test_cli_non_conforming_exit_1`) because `run_begin` refuses a worker-role process (`AW-LIFECYCLE-ROLE-001`). That is an ARTIFACT OF THE ENVIRONMENT, not a code failure: `env -u AW_EXECUTION_ROLE python3 -m pytest` on the three lifecycle test files gives `91 passed`. Do not "fix" the tests; unset the variable, and say which form you ran.
2. E-01's fixture set, pasted, showing each current behavior BEFORE the change and the additive case accepted AFTER while the requirement-rewrite case still refuses.
3. E-05's negative controls: a removal refuses and names the path; a mixed add-plus-remove refuses; a pure reordering is unchanged.
4. A widening with a MISSING `--scope-reason` for one added path refuses, IN BOTH the committed and the uncommitted variant (the accept must not be unconditional, and F-9 showed the uncommitted variant is where a vacuous implementation would hide).
5. The three ineligible receipt shapes (E-09): legacy v1, becoming-grandfathered, grandfathered-plus-paths, each asserted refused.
6. E-08's eligibility controls: `tests/`, `agent_workflows`, `agent_workflows/**` and `*` each refused as an added entry; a literal file path accepted.
7. The runner half (F-10): `compute_scope_reconciliation` driven on a widened fixture, showing it emits a reason for the added path, and `driver_finalize`'s assembled argv containing the corresponding `--scope-reason`.
8. E-07's three end-to-end reconstructions, each pasted.
9. `aw ipd lint --phase pre-transition` conforming on this plan.
10. `aw sanitize --agent` clean.

### Executed results (2026-09-17)

WHICH FORM I RAN, as item 1 demands: `env -u AW_EXECUTION_ROLE python3 -m pytest`, BARE apart from unsetting that variable. `AW_EXECUTION_ROLE=worker` WAS set in this lane's environment, exactly as review predicted, so the variable was unset rather than the tests edited. Everything below is `addopts` as configured (`-q -n auto --dist=worksteal -m 'not slow'`) unless a narrowed run is explicitly shown with `-o addopts=""`.

PRE-EXECUTION BASELINE, taken at HEAD `a451ab9c` before any edit:

```
7825 passed, 3 skipped, 2 xfailed in 123.77s (0:02:03)
```

POST-EXECUTION, two consecutive clean runs:

```
7855 passed, 3 skipped, 2 xfailed in 106.83s (0:01:46)
7855 passed, 3 skipped, 2 xfailed in 111.11s (0:01:51)
```

+30 tests, no failures, no new skips. NO NEW FAILURES, and nothing absorbed.

ONE FLAKE ENCOUNTERED AND RUN TO GROUND RATHER THAN WAVED AWAY, reported because item 1 says a pre-existing failure must be NAMED. Two earlier post-change runs failed on `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` with `subprocess.TimeoutExpired ... timed out after 30 seconds`: the test signals a real child process and waits 30s for it to report and exit. Investigated instead of assumed:

- it passes ALONE, five consecutive times (`1 passed in 0.63s` each);
- its whole file passes under forced parallelism (`47 passed in 2.96s`);
- I STASHED every code change of this plan and ran the full suite on the otherwise-pristine tree, which passed `7825 passed, 3 skipped, 2 xfailed in 107.45s`, then restored the work; and
- with the changes restored it then passed twice consecutively, as pasted above.

So it is a load-sensitive timing flake in a signal test, not a regression: this plan touches neither the runner's signal handling nor `test_runner_backlog_close.py`, and the failure mode is a wall-clock timeout rather than an assertion. Filed as a backlog item rather than left as folklore, and reported in this turn's defect report. Honest limit: the pristine run passing does not PROVE the flake is independent of my change (a flake can hide), which is why the two clean post-change runs are pasted rather than one.

GATES:

```
$ env -u AW_EXECUTION_ROLE python3 -m agent_workflows ipd lint <this plan> --phase pre-transition
- >  approved     plan        20260917-rcptwiden-01-63425h  [blocking]  conforming

$ env -u AW_EXECUTION_ROLE python3 -m agent_workflows check-local-leaks . --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```

Items 2 through 8 are each pasted under their `V-*` item above (V-01, V-05, V-04, V-09, V-08, V-04's runner paragraph, V-07 respectively).

## Spec / documentation sync

THIS PLAN AMENDS A SPEC AND DECLARES IT. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (spec `25kzda`, `Status: approved`) is in `- Scope-Paths:` because E-06 must edit `:1009`'s never-retry clause. WHY, since a spec edit changes the contract every other plan is reviewed against: that clause currently makes "changed frozen requirements" unconditionally never-retryable, which is right for a requirement rewrite and wrong for an additive scope declaration, and an approved plan (`zzcrlo`) names the clause as the boundary it will honor. Landing the code without the amendment would leave code and spec in direct conflict and let `zzcrlo` re-refuse the same failure. The amendment SPLITS the clause rather than deleting it: a changed requirement stays never-retryable.

THE AMENDMENT MUST CARRY THE ELIGIBILITY CONDITIONS, not just the permission. A spec sentence authorizing "an additive scope widening with a recorded reason" would authorize adding `*` as one entry, which E-08 refuses and which would make the fence meaningless. So the amended clause must state the literal-file-path restriction and the ineligible receipt shapes, and the code and the spec must say the same thing. REVIEW MEASURED THE COLLISION SURFACE: `zzcrlo`'s own execution contract forbids ITS executor from editing this spec ("Do NOT edit spec `25kzda` (approved, release-gating): if the code cannot satisfy it as written, STOP AND REPORT"), so this plan holds the amendment authority for this clause and there is no competing claim on it. Three test files read this spec as a FILE (`tests/test_run_flag_surface.py:48`, `tests/test_run_evidence_completion.py:1024`, `tests/test_run_selection_policy.py:806`) and all three parse OTHER sections, so no contract test reads the clause being amended; re-verify at execution HEAD and paste all three green regardless, since the risk is a test that came to read 5.5 after review.

## Open questions

### OQ-01: Should an additive widening require a `--scope-reason` per added path, or is the declaration itself sufficient?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the plan is executable under either answer and E-04 implements the STRICTER one by default (a reason is required per added path), which is the safe direction and can be relaxed without rework. The argument for requiring a reason: it matches what an out-of-scope edit already owes, and it keeps a widening from becoming a silent way to grow a fence. The argument against: the declaration IS the honest act this plan exists to reward, and demanding prose for it may reintroduce friction at the same moment. Recorded rather than decided because it is a usability-versus-rigor call on a gate the maintainer owns. If unanswered, the strict form ships. REVIEW CORRECTION (F-9): as first authored, "the strict form ships" was NOT TRUE OF THE CODE THE PLAN DESCRIBED. Reusing `--scope-reason` without an added demand yields NO reason requirement for an uncommitted widened path, because the reconciliation judges against the receipt's old fence. So the default was silently the LENIENT form. E-04 now carries an explicit unconditional per-added-path demand, which is what makes this question genuinely non-blocking: the strict form is now implemented, and relaxing it later is deleting a check rather than adding one. NOTE THE COST OF THE STRICT FORM HONESTLY, since it bears on the maintainer's answer: E-04's runner half auto-generates a reason string for the added path, so in a runner-driven finalize (the case all three incidents were) the "reason" is machine boilerplate rather than an agent's justification. The strict form therefore buys a RECORD, not an explanation, on the automated path; it buys a real explanation only on a hand-run finalize.

### OQ-02: Should a DIRECTORY or GLOB addition be permanently ineligible, or eligible with a stronger gate?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED AT REVIEW from F-11. E-08 implements the strict answer: only a LITERAL FILE PATH may be added under the widening accept, and `tests/` or `agent_workflows` or `*` refuses exactly as today. That is the fail-closed direction and is what ships if this is unanswered. The question is whether it is too strict for a legitimate case: a plan that must add a whole new test DIRECTORY it creates, or a generated-file tree, would be refused and would still have to re-run `aw ipd begin`. NOT blocking, because re-running begin remains available and is the current behavior for every case, so the strict form strands nothing that is not already stranded; and because relaxing it later (say, admitting a directory whose entries are all new files) is an addition, while tightening it later would be a regression for anyone who had relied on it. Recorded because "how much fence may an execution grant itself" is a policy question about a gate, which is the maintainer's.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted test output showing each current behavior at execution HEAD: fixture (a) additive-widening REFUSED with the STALE message quoted, fixture (b) requirement-rewrite REFUSED, and the concealment case (undeclared edit, no widening) ACCEPTED. FOR THE CONCEALMENT CASE, PASTE BOTH VARIANTS AND SAY WHICH DEMANDED A REASON, since F-8 measured that the uncommitted variant demands NONE (`out_of_scope_paths: []`, `disregarded_unowned_paths: [<the path>]`) while the committed-cohesive variant does. The asymmetry must be visible in the pasted output, not described.
  - Observed evidence: Measured at execution HEAD `a451ab9c` BEFORE any code change, driving the real `LC.finalize_precheck` / `LC.finalize` on git-backed fixtures. The asymmetry reproduced exactly as the Concern and F-8 state. Verbatim output:

    ```
    FIXTURE (a) ADDITIVE WIDENING (declared the path honestly)
      precheck rc=1
      message: the begin receipt for abc123 is STALE: the plan content changed since begin; re-run `aw ipd begin`.
      findings: ('plan content digest no longer matches the receipt',)
      receipt_is_current: False

    FIXTURE (b) REQUIREMENT REWRITE (changed the reviewed contract)
      precheck rc=1
      message: the begin receipt for abc123 is STALE: the plan content changed since begin; re-run `aw ipd begin`.
      findings: ('plan content digest no longer matches the receipt',)
      receipt_is_current: False

    FIXTURE (c1 UNCOMMITTED) CONCEALMENT (edited tests/test_extra.py, did NOT declare it)
      precheck rc=0
      message: precheck passed (receipt valid, pre-transition conforming; scope delta computed). Disregarded 1 path(s) not owned by this execution (no reason required, recorded in the scope audit): tests/test_extra.py.
      findings: ()
      out_of_scope_paths: []
      disregarded_unowned_paths: ['tests/test_extra.py']
      A --scope-reason IS DEMANDED for tests/test_extra.py: False
      finalize(apply=False) rc=0; findings=()

    FIXTURE (c2 COMMITTED-COHESIVE) CONCEALMENT (edited tests/test_extra.py, did NOT declare it)
      precheck rc=0
      message: precheck passed (receipt valid, pre-transition conforming; scope delta computed).
      findings: ()
      out_of_scope_paths: ['tests/test_extra.py']
      disregarded_unowned_paths: []
      A --scope-reason IS DEMANDED for tests/test_extra.py: True
      finalize(apply=False) rc=1; findings=('out-of-scope path needs a --scope-reason: tests/test_extra.py',)
    ```

    WHICH DEMANDED A REASON, stated explicitly as the item requires: the UNCOMMITTED concealment (c1) demanded NONE and passed with `rc=0` outright; only the COMMITTED-cohesive concealment (c2) demanded a `--scope-reason`. So F-8 is confirmed: the honest declaration (a) is REFUSED while the concealed uncommitted edit is not merely cheaper, it is FREE. The two refusals (a) and (b) are byte-identical in message and findings, which is precisely the conflation E-03 had to decompose.

    The three-way behavior is now pinned as PERMANENT tests rather than only measured here: `tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_the_uncommitted_added_path_is_NOT_in_out_of_scope` pins the (c1) measurement so a future refactor cannot silently undo the premise, and `::test_a_requirement_rewrite_still_refuses_as_STALE_even_with_reasons` pins (b).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted per-consumer table for `frozen_region_digest`, `receipt_is_current`, `_frozen_scope_paths` and `_requirements_from_plan`, produced by an actual search at execution HEAD (paste the search), with an explicit statement of every test that pins a digest literal, every test that pins SOURCE TEXT (F-13 named three), and every consumer E-03 would affect. "No other consumers" is a claim that must be shown by the search, not asserted. PLUS the explicit `check.scope-drift` answer F-12 requires.
  - Observed evidence: THE SEARCH, run at execution HEAD `a451ab9c` (82 hits total, every one classified below):

    ```
    $ git rev-parse HEAD
    a451ab9c70feefd7bbbedc650c6f17eacb664ca5
    $ rg -n "frozen_region_digest|_frozen_scope_paths|_requirements_from_plan|receipt_is_current" --glob '!*.pyc' agent_workflows/ tests/ .aw/system/ *.py *.md
    ```

    PER-CONSUMER TABLE (non-test consumers; every hit not listed is a docstring/comment mention that reads nothing):

    | Symbol | Consumer | file:line | What it does with it | Affected by E-03? |
    | --- | --- | --- | --- | --- |
    | `frozen_region_digest` | `begin` | `ipd_lifecycle.py:1093` | WRITES it into the receipt | No. Unchanged; the payload it hashes is byte-identical (V-03 asserts the digest is reproducible through the shared builder). |
    | `frozen_region_digest` | `receipt_is_current` | `ipd_lifecycle.py:909` | Compares stored vs recomputed | No. Left byte-identical in behavior, deliberately (see V-03). |
    | `frozen_region_digest` | `frozen_region_comparison` | `ipd_lifecycle.py` (new) | Compares the SUBSTITUTED payload's hash to the stored digest | New consumer, added by E-03. Reads only; writes nothing. |
    | `receipt_is_current` | `finalize_precheck` | `ipd_lifecycle.py:1612` | Gates the STALE refusal | YES, and this is the ONE behavioral change: on a False it now asks `frozen_region_comparison` a second question and accepts an eligible additive widening. Every other outcome refuses with the identical message. |
    | `_frozen_scope_paths` | `begin` | `ipd_lifecycle.py:1052,1095` | Frozen fence + receipt field | No. |
    | `_frozen_scope_paths` | `check_engine.check_scope_drift` | `check_engine.py:1366` | Reads the PLAN's CURRENT scope for the advisory | Not edited (this plan must not touch `check_engine.py`), but there IS an interaction; see the F-12 answer below. |
    | `_frozen_scope_paths` | `frozen_region_comparison` | `ipd_lifecycle.py` (new) | Reads the plan's current scope for the delta | New consumer. |
    | `_requirements_from_plan` | `frozen_region_digest` | via `_frozen_region_payload` | Requirement categories | No; call shape preserved. |
    | `_requirements_from_plan` | `begin` | `ipd_lifecycle.py:1035` | `run_freeze.freeze_requirements` input | No. |

    NO CONSUMER STORES OR COMPARES THE DIGEST VALUE outside `ipd_lifecycle`, so there is no compatibility surface to migrate. `runner_shared.py:5958-6093` documents a DELIBERATE divergence from `frozen_region_digest` for the orchestrator probe cache and was NOT changed (its own digest is separate and untouched). `wtiso_gate.py:427,441` and `run_evidence.py:1431` mention the symbols only as NARRATIVE STRINGS (a findings message and a `predicates` tuple entry); neither calls anything, and `run_evidence.py:1431`'s string `"ipd_lifecycle._frozen_scope_paths"` still names a real symbol because E-03 renamed nothing.

    TESTS THAT PIN A DIGEST AS A HEX LITERAL: NONE. Verified independently rather than inherited from review:

    ```
    $ rg -n "[0-9a-f]{64}" tests/ --glob '!*.pyc'
    tests/test_run_evidence_completion.py:183:            "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03",
    ```

    That single hit is the sha256 of `"hello\n"` asserted as a tool event's `stdout_sha256`; it is unrelated to any frozen-region digest.

    TESTS THAT PIN SOURCE TEXT (F-13 named three; all three re-verified present and all three still pass):
    - `tests/test_event_derived_lifecycle.py:288` - `assertIn("_frozen_scope_paths", src)` on `check_scope_drift`'s source. Unaffected: not renamed, and `check_engine.py` untouched.
    - `tests/test_dirty_base_gate.py:395` - `assertIn("_frozen_scope_paths(plan_text)", begin_source)`. Unaffected: `begin`'s call shape preserved verbatim.
    - `tests/test_orchestrator_probe_cache.py:526-594` - asserts `frozen_region_digest` does NOT move on a child-table edit and DOES move on an E-item edit, plus a docstring-divergence assertion. Unaffected: the digest's value is unchanged by the payload extraction.
    - Additionally found and re-based deliberately: `tests/test_finalize_isolated_commit.py` asserts `finalize_precheck`/`finalize` source contains no `isolated_baseline` and no `aw/lane/`; E-03/E-04 introduced neither, and that test passes.

    All four pass together with the lifecycle files:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_event_derived_lifecycle.py tests/test_dirty_base_gate.py tests/test_orchestrator_probe_cache.py tests/test_finalize_isolated_commit.py -o addopts="" -q
    (see the run pasted under V-09; 0 failures)
    ```

    THE `check.scope-drift` ANSWER F-12 DEMANDS, measured rather than reasoned. The advisory reads `_frozen_scope_paths(text)` from the PLAN's CURRENT text (not the receipt's), so declaring a path removes it from the drift report IMMEDIATELY, before any finalize accepts anything. Measured:

    ```
    BEFORE declaring the path (undeclared edit, live receipt):
      drift: changed path 'tests/test_extra.py' is outside the plan's declared Scope-Paths
    AFTER declaring it in Scope-Paths (receipt now STALE, no finalize yet):
      (no drift reported -> the advisory is SILENCED for the added path)
      and finalize_precheck still rc=1: the begin receipt for abc123 is STALE: ...
    ```

    IS THAT CORRECT? Yes, and it is PRE-EXISTING rather than introduced here: the silencing already happened at HEAD, before any code change, because the advisory has always read the plan's current scope. The advisory's own recovery text already NAMES declaring the path as a legitimate fix ("or declare the path in the plan's Scope-Paths (then re-`aw ipd begin`)"), so an advisory that stops reporting a now-declared path is doing what it says. What this plan changes is that the declaration is no longer a dead end at finalize; before, an agent following that recovery advice silenced the advisory AND stranded its lane. Whether the advisory should instead read the RECEIPT's scope is `wmnmei`'s decision and is deliberately not taken here; `check_engine.py` is not edited.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the new comparison function's output pasted for BOTH fixtures, showing `added=[...]`, `removed=[]` and `non_scope_identical=True` for (a), and `non_scope_identical=False` for (b). PLUS proof that `receipt_is_current` is UNCHANGED in behavior: fixture (b) still refuses, and an unmodified plan still returns True. PLUS the assertion that ONE payload builder is shared with `frozen_region_digest` (pasted; a test that would fail if a second copy were introduced, not a statement that they match).
  - Observed evidence: `frozen_region_comparison` driven on the E-01 fixtures and on every control, with `widening_is_acceptable` (the accept condition, stated in one place) and `receipt_is_current` printed alongside so the "unchanged behavior" claim is visible rather than asserted:

    ```
    (unchanged plan)
      added=[] removed=[] non_scope_identical=True
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=True
    (a) ADDITIVE WIDENING tests/test_extra.py
      added=['tests/test_extra.py'] removed=[] non_scope_identical=True
      eligible=True ineligible_reason=''
      widening_is_acceptable=True
      receipt_is_current=False
    (b) REQUIREMENT REWRITE
      added=[] removed=[] non_scope_identical=False
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=False
    (a+b) WIDENING *AND* REQUIREMENT REWRITE
      added=['tests/test_extra.py'] removed=[] non_scope_identical=False
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=False
    ```

    (a) yields `added=['tests/test_extra.py']`, `removed=[]`, `non_scope_identical=True`; (b) yields `non_scope_identical=False`. The adversarial combination (a+b) is NOT accepted, which is the case that would let additions launder a simultaneous rewrite.

    `receipt_is_current` IS UNCHANGED IN BEHAVIOR, and note the accept does not run through it at all: it still returns `True` for the unchanged plan and `False` for BOTH the widening and the rewrite. The widening accept is a SECOND question asked by `finalize_precheck` after this predicate has already said False, so every other caller sees exactly what it saw before. Pinned by `tests/test_receipt_requirement_digest.py::FrozenRegionComparisonTests::test_receipt_is_current_is_unchanged_by_this_work`, which asserts all four outcomes including that the xmqv5l self-execution-edit fix still holds.

    THE ONE SHARED PAYLOAD BUILDER, asserted as a test that FAILS if a second copy is introduced rather than as a statement that they currently match (`test_ONE_payload_builder_is_shared_with_frozen_region_digest`): it recomputes the digest by calling `_frozen_region_payload` and hashing it the same way and requires equality with `frozen_region_digest`; it requires BOTH functions' source to contain `_frozen_region_payload(`; and it requires NEITHER to contain the `"requirements":` literal, so a hand-written second copy fails the test. It also asserts the override substitutes BOTH scope inputs (the top-level `scope_paths` AND `requirements["scope"]`), which is the property the substitution depends on. Measured:

    ```
    PAYLOAD BUILDER SHARE:
      frozen_region_digest calls _frozen_region_payload: True
      frozen_region_digest contains no inline 'scope_paths': True
      frozen_region_comparison calls _frozen_region_payload: True
      frozen_region_comparison contains no inline 'requirements': True
    ```

    The function is PURE apart from an optional directory probe (it takes the receipt dict and the plan text; `repo_root` is used only by `_entry_is_bare_directory` and may be omitted), so all 19 tests in that file run with no git fixture where none is needed:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_receipt_requirement_digest.py -o addopts="" -q
    ...................                                                      [100%]
    19 passed in 1.10s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: fixture (a) FINALIZING when each added path carries `--scope-reason`, pasted end to end, IN BOTH the committed and the uncommitted variant; the SAME fixture REFUSING when one added path lacks a reason, IN BOTH variants (this is the F-9 control and the one most likely to pass vacuously, so a paste showing only the committed variant does NOT satisfy this item); fixture (b) still refusing. PLUS proof one `--scope-reason` per path satisfies both demands in the committed case, with the recorded evidence naming the path ONCE. PLUS the finalize evidence pasted, showing the accepted widening is recorded (which paths, which reasons).
  - Observed evidence: `tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests` covers every branch this item names, and each of the two central tests runs BOTH variants via `subTest(committed=True/False)` so the uncommitted case cannot be silently omitted:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest "tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests" -o addopts="" -v
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_ONE_reason_satisfies_both_demands_in_the_committed_case PASSED [ 12%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_widening_finalizes_when_each_added_path_carries_a_reason PASSED [ 25%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_a_removal_refuses_and_NAMES_the_removed_path PASSED [ 37%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_a_directory_addition_refuses_and_NAMES_the_offending_entry PASSED [ 50%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_the_uncommitted_added_path_is_NOT_in_out_of_scope PASSED [ 62%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_widening_REFUSES_when_an_added_path_lacks_a_reason PASSED [ 75%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_an_empty_reason_for_an_added_path_still_refuses PASSED [ 87%]
    tests/test_ipd_lifecycle_cli.py::AdditiveScopeWideningTests::test_a_requirement_rewrite_still_refuses_as_STALE_even_with_reasons PASSED [100%]
    ============================== 8 passed in 2.43s ===============================
    ```

    (The order varies run to run: `pytest-randomly` is configured on and deliberately left on.)

    (a) FINALIZES WITH A REASON, BOTH VARIANTS (`test_widening_finalizes_when_each_added_path_carries_a_reason`, subTests `committed=True` and `committed=False`): `finalize(..., apply=True, scope_reasons={"tests/test_extra.py": ...})` returns `EXIT_OK`, the plan reaches `.aw/records/plans/executed/`, and the terminal history carries `widened-scope tests/test_extra.py` with the reason verbatim.

    (a) REFUSES WITHOUT A REASON, BOTH VARIANTS (`test_widening_REFUSES_when_an_added_path_lacks_a_reason`): `EXIT_FINDINGS`, the plan is left unmoved, and the message names the exact re-invocation flag `--scope-reason tests/test_extra.py=`. THIS IS THE F-9 CONTROL and it is asserted in the uncommitted variant specifically, which is where a vacuous implementation would hide. An empty/whitespace reason also refuses (`test_an_empty_reason_for_an_added_path_still_refuses`).

    THE F-9 MEASUREMENT ITSELF IS PINNED (`test_the_uncommitted_added_path_is_NOT_in_out_of_scope`), so the independence of the new demand cannot be quietly undone: for the uncommitted widening, `out_of_scope_paths == []`, `disregarded_unowned_paths` contains the path, and `widened_paths == ['tests/test_extra.py']`. That is exactly why the reason demand is its own unconditional per-added-path requirement in `_reconcile_scope` rather than an inheritance from `out_of_scope`.

    (b) STILL REFUSES EVEN WITH REASONS SUPPLIED (`test_a_requirement_rewrite_still_refuses_as_STALE_even_with_reasons`): passing `scope_reasons` cannot buy a contract rewrite; the refusal keeps the STALE message and adds a finding saying why it is not a widening.

    ONE REASON SATISFIES BOTH DEMANDS (`test_ONE_reason_satisfies_both_demands_in_the_committed_case`): in the committed-cohesive variant the precheck shows the path in BOTH `out_of_scope_paths` and `widened_paths`; supplying a single `--scope-reason` finalizes, and the executed plan's text contains `tests/test_extra.py:` exactly ONCE (asserted by count, so a double-record fails). The `test_widening_finalizes...` test asserts the same count property and additionally that `out-of-scope tests/test_extra.py` does NOT appear, since the record must describe the act accurately as a widening.

    THE ACCEPTED WIDENING IS RECORDED, in the evidence and in the permanent history. From the E-07 end-to-end reconstruction of a real incident (full output under V-07):

    ```
      precheck: rc=0
        message: precheck passed (receipt valid, pre-transition conforming; scope delta computed).
        widened_paths: ['tests/test_resumedupe.py']
      RUNNER-GENERATED reasons:
        tests/test_resumedupe.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
      FINALIZE: rc=0 -> finalized zzd6ml -> executed at fc9237dd18db (actor aw oc run model=test).
      reached executed/: True
        recorded: - 2026-09-17 executed (aw oc run model=test): reconstructed finalize [Scope reconciliation - widened-scope tests/test_resumedupe.py: declared in Scope-Paths during execution because the approved work required it (additiv...
    ```

    Evidence keys asserted by the tests: `evidence["frozen_region_widening"] == {"accepted": True, "added_paths": [...], ...}` and `evidence["scope_audit"]["widened_paths"]`.

    THE RUNNER HALF (F-10), without which the fix would not reach the measured incident: `tests/test_rununify_host_descriptor.py::TheRunnerCanSupplyAWideningReasonTests` drives `compute_scope_reconciliation` on BOTH hosts with the incident's exact audit shape (widened but NOT out-of-scope) and asserts a reason is produced; that a path which is both widened and out-of-scope gets exactly ONE reason; that a widened path is not also demanded as an ack; that an ABSENT `widened_paths` key changes nothing (so a pre-existing tree behaves identically); and, end to end, that `driver_finalize`'s assembled argv actually carries one `--scope-reason tests/test_resumedupe.py=...` flag.

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_rununify_host_descriptor.py -o addopts="" -q
    .......................................                                  [100%]
    39 passed in 1.33s
    ```

    And in a REAL ISOLATED LANE, which is where all three incidents ran: `tests/test_finalize_isolated_commit.py::IsolatedFinalizeCommittedHalfIsLaneLocalTests::test_a_lane_that_DECLARES_a_newly_needed_path_can_finalize` builds a real `git worktree`, widens the plan in-lane, obtains the reason from the runner's own `compute_scope_reconciliation` (not by hand), finalizes to `EXIT_OK`, and asserts the lane's plan reached `executed/` with `widened-scope tests/test_resumedupe.py` recorded.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted output showing a REMOVED scope path refuses with the removed path NAMED, that a mixed add-and-remove refuses rather than being accepted on its additions, and that a pure REORDERING of the same entries is treated as unchanged.
  - Observed evidence: All three, measured through the comparison and end to end through `finalize`.

    ```
    (E-05) REMOVAL of tests/test_demo.py
      added=[] removed=['tests/test_demo.py'] non_scope_identical=True
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=False
    (E-05) MIXED add tests/test_extra.py + remove tests/test_demo.py
      added=['tests/test_extra.py'] removed=['tests/test_demo.py'] non_scope_identical=True
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=False
    (E-05) pure REORDERING
      added=[] removed=[] non_scope_identical=True
      eligible=True ineligible_reason=''
      widening_is_acceptable=False
      receipt_is_current=True
    ```

    A REMOVAL REFUSES WITH THE PATH NAMED, end to end (`AdditiveScopeWideningTests::test_a_removal_refuses_and_NAMES_the_removed_path`): `finalize` returns `EXIT_FINDINGS`, keeps the STALE message, leaves the plan unmoved, and emits a finding containing both `REMOVED` and `tests/test_demo.py`. The finding text is `Scope-Paths entry REMOVED since begin (a contract reduction, never accepted as a widening): tests/test_demo.py`.

    A MIXED ADD-AND-REMOVE IS TREATED AS A REMOVAL, not accepted on the strength of its additions: note above that `non_scope_identical=True` and `added` is non-empty, so ONLY the `not removed` clause of `widening_is_acceptable` stops it. That is the exact adversarial case, and it is pinned by `FrozenRegionComparisonTests::test_mixed_add_and_remove_is_treated_as_a_removal`.

    A PURE REORDERING IS UNCHANGED: `added=[]`, `removed=[]`, and `receipt_is_current` is `True` (the digest sorts entries before hashing, so the reorder never even reaches the comparison). The comparison compares SETS OF ENTRY STRINGS, stated in `FrozenRegionComparison`'s docstring and asserted by `test_pure_reordering_is_unchanged`, so declaration order is not semantic and a reorder can never read as a removal-plus-addition.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the spec clause quoted BEFORE and AFTER, showing the split (requirement change stays never-retryable; additive widening becomes a finalize-time accept), the E-08/E-09 eligibility conditions written INTO the spec text, and the measured incident cited as the rationale. PLUS the three spec-reading test files (`tests/test_run_flag_surface.py`, `tests/test_run_evidence_completion.py`, `tests/test_run_selection_policy.py`) named and pasted passing, plus the re-verified statement that no test reads Section 5.5. PLUS confirmation that no OTHER spec section was touched (paste the spec diff).
  - Observed evidence: BEFORE, the never-retry list item in Section 5.5 (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, the exact line E-06 names):

    ```
    - changed frozen requirements;
    ```

    AFTER:

    ```
    - changed frozen requirements, EXCEPT an additive scope widening as defined below;
    ```

    THE SPLIT IS EXPLICIT AND THE REQUIREMENT HALF IS UNWEAKENED. The new subsection `5.5a Additive scope widening is a finalize-time accept, not a retry` opens by restating that a changed frozen requirement REMAINS never-retryable, and states that the widening is NOT a retry ("nothing is re-dispatched, no budget is spent, and the same finalize call proceeds"), so it does not create a new retry class and cannot be spent from the retry budget. It states the asymmetry it exists to correct (the declared edit failed while the concealed edit succeeded) and CITES THE MEASURED INCIDENT as the rationale: run `run-20260917T023628Z-4108757`, three of twelve items (`i3d6ml`, `tx6q0h`, `sy7uwh`), $95.71 and 3h10m of a $212.60 / 8h06m run, three lanes stranded, orchestrator `5e4sb6` dependency-blocked.

    THE ELIGIBILITY CONDITIONS ARE IN THE SPEC TEXT, not only in the code, as six numbered conditions with "any one failing restores the unmodified never-retryable refusal": (1) the substitution proof that every non-scope category is byte-identical; (2) no removal, with a mixed add-and-remove refusing and entries compared as SETS so a reorder is not a change; (3) at least one path added; (4) E-08's LITERAL FILE PATH restriction, naming `tests/`, the bare-directory `agent_workflows`, `agent_workflows/**` and `*` as ineligible and giving the reason (one such entry would make the fence repository-wide, "strictly worse than the defect being fixed"); (5) E-09's three ineligible SHAPES (legacy v1 receipt, a receipt with no declared allowlist, and a plan that becomes grandfathered); and (6) the unconditional per-added-path `--scope-reason`, including why it is independent of the out-of-scope reconciliation and that one reason covers both demands. It also records honestly that a runner-generated reason is a RECORD rather than an explanation, and closes by keeping begin-time widening and mid-run re-freezing unsupported.

    NO TEST READS SECTION 5.5, re-verified at execution HEAD rather than inherited from review:

    ```
    $ rg -n "aw-run-deterministic-run-and-verify" tests/
    tests/test_run_selection_policy.py:806:    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    tests/test_run_flag_surface.py:48:    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    tests/test_run_evidence_completion.py:1024:    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    ```

    Exactly the three files review named, and no more. All three parse OTHER sections (4.1's abort classes, 4.2's `RUN-*` table, 2.5a's draft gate); a search for a 5.5 / never-retry reference in the test tree returns only unrelated `R5.5` matches belonging to a DIFFERENT spec (`7ckptx`, lane retention) and float literals like `5.5`. All three pass:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_run_flag_surface.py tests/test_run_evidence_completion.py tests/test_run_selection_policy.py -o addopts="" -q
    ........................................................................ [ 27%]
    ........................................................................ [ 55%]
    ........................................................................ [ 82%]
    .............................................                            [100%]
    261 passed in 6.37s
    ```

    NO OTHER SPEC SECTION WAS TOUCHED. The whole spec diff is one line changed plus the new 5.5a block appended immediately after 5.5's closing paragraph:

    ```
    $ git diff --stat -- .aw/records/specs/
     ...-01-aw-run-deterministic-run-and-verify.spec.md | 23 +++++++++++++++++++++-
     1 file changed, 22 insertions(+), 1 deletion(-)
    ```

    One deletion and one insertion are the amended list item; the remaining 21 insertions are 5.5a itself. Section 5.6 and every other section are untouched.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: for each of `i3d6ml`, `tx6q0h` and `sy7uwh`, the END-TO-END reconstruction pasted: the receipt issued against the BEFORE text, the added paths measured (not quoted from F3), the reason the RUNNER's own `compute_scope_reconciliation` generated, and the finalize outcome. A per-plan "E-04's condition accepts it" WITHOUT the runner in the loop does NOT satisfy this item (F-10). Any plan that would STILL refuse is named as a finding with its reason. Explicit confirmation that no real plan was finalized and no receipt was written for a real plan id.
  - Observed evidence: ALL THREE WOULD HAVE FINALIZED. Reconstructed FROM GIT (BEFORE text = `<sha>^:<path>`, AFTER text = `<sha>:<path>`), a real receipt issued against the BEFORE text, then the WHOLE runner path driven including `compute_scope_reconciliation`, whose generated reason was passed to a real `finalize(apply=True)`. Verbatim:

    ```
    ==============================================================================
    INCIDENT i3d6ml  sha=89324096
      plan file: .aw/records/plans/pending/20260915-rununify-03-i3d6ml-lift-the-48-non-conflicting-shared-runner-symbols-into-runne.ipd.md
      MEASURED added:   ['tests/test_resumedupe.py']
      MEASURED removed: []
      MEASURED differing requirement categories: ['scope']
      every added entry is a LITERAL FILE PATH: True
      begin: rc=0 (begin receipt written for zzd6ml at base 5d2d42e39220 (actor opencode/test).)
      precheck: rc=0
        message: precheck passed (receipt valid, pre-transition conforming; scope delta computed).
        widened_paths: ['tests/test_resumedupe.py']
      RUNNER-GENERATED reasons:
        tests/test_resumedupe.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
    plans index --check: clean
      FINALIZE: rc=0 -> finalized zzd6ml -> executed at fc9237dd18db (actor aw oc run model=test).
      reached executed/: True
        recorded: - 2026-09-17 executed (aw oc run model=test): reconstructed finalize [Scope reconciliation - widened-scope tests/test_resumedupe.py: declared in Scope-Paths during execution because the approved work required it (additiv
    ==============================================================================
    INCIDENT tx6q0h  sha=e5fbe9c4
      plan file: .aw/records/plans/pending/20260915-rununify-04-tx6q0h-parameterize-the-8-host-label-symbols-and-lift-them-to-runne.ipd.md
      MEASURED added:   ['tests/test_defect_report.py', 'tests/test_lane_retention.py', 'tests/test_shared_checkout_contract.py']
      MEASURED removed: []
      MEASURED differing requirement categories: ['scope']
      every added entry is a LITERAL FILE PATH: True
      begin: rc=0 (begin receipt written for zz6q0h at base 24697a63404d (actor opencode/test).)
      precheck: rc=0
        message: precheck passed (receipt valid, pre-transition conforming; scope delta computed).
        widened_paths: ['tests/test_defect_report.py', 'tests/test_lane_retention.py', 'tests/test_shared_checkout_contract.py']
      RUNNER-GENERATED reasons:
        tests/test_defect_report.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
        tests/test_lane_retention.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
        tests/test_shared_checkout_contract.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
    plans index --check: clean
      FINALIZE: rc=0 -> finalized zz6q0h -> executed at e8d945363631 (actor aw oc run model=test).
      reached executed/: True
        recorded: - 2026-09-17 executed (aw oc run model=test): reconstructed finalize [Scope reconciliation - widened-scope tests/test_defect_report.py: declared in Scope-Paths during execution because the approved work required it (addi
    ==============================================================================
    INCIDENT sy7uwh  sha=20311677
      plan file: .aw/records/plans/pending/20260915-rununify-06-sy7uwh-unify-the-plan-record-type-and-its-two-readers-overriding-th.ipd.md
      MEASURED added:   ['tests/test_orchestrator_probe_cache.py']
      MEASURED removed: []
      MEASURED differing requirement categories: ['scope']
      every added entry is a LITERAL FILE PATH: True
      begin: rc=0 (begin receipt written for zz7uwh at base 0f174a2b0559 (actor opencode/test).)
      precheck: rc=0
        message: precheck passed (receipt valid, pre-transition conforming; scope delta computed).
        widened_paths: ['tests/test_orchestrator_probe_cache.py']
      RUNNER-GENERATED reasons:
        tests/test_orchestrator_probe_cache.py = declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run)
    plans index --check: clean
      FINALIZE: rc=0 -> finalized zz7uwh -> executed at d87586942eea (actor aw oc run model=test).
      reached executed/: True
        recorded: - 2026-09-17 executed (aw oc run model=test): reconstructed finalize [Scope reconciliation - widened-scope tests/test_orchestrator_probe_cache.py: declared in Scope-Paths during execution because the approved work requir
    ==============================================================================
    NO real plan was finalized: every reconstruction ran in a fresh temporary git repo
    with the plan id6 RENAMED, so no receipt was written for a real plan id.
    ```

    NONE WOULD STILL REFUSE, so there is no completeness finding to file against this plan. THE RUNNER WAS IN THE LOOP for all three, which is what F-10 requires: the reason passed to `finalize` was the one `runner_shared.compute_scope_reconciliation` generated, not one written by this harness.

    RE-MEASURED VS F-3, and every number MATCHES (a mismatch would have been a finding): `i3d6ml` -> `tests/test_resumedupe.py`; `tx6q0h` -> `tests/test_defect_report.py`, `tests/test_lane_retention.py`, `tests/test_shared_checkout_contract.py`; `sy7uwh` -> `tests/test_orchestrator_probe_cache.py`. Removed: none in any case. Differing requirement categories: `scope` ONLY in all three (`must` and `validation` identical). Every added entry is a literal file path, so all three pass E-08's eligibility rule.

    NO REAL PLAN WAS FINALIZED BY THIS EXECUTION AND NO RECEIPT WAS WRITTEN FOR A REAL PLAN ID, by construction rather than by care: each reconstruction ran in its own `tempfile.TemporaryDirectory()` git repo, and the plan id6 was REWRITTEN before anything was issued (`i3d6ml`->`zzd6ml`, `tx6q0h`->`zz6q0h`, `sy7uwh`->`zz7uwh`), so `receipt_path_for` could only ever address the renamed id. Verified afterwards in this workspace:

    ```
    $ for id in i3d6ml tx6q0h sy7uwh; do ls .aw/records/plans/*/*$id*; ls .aw/state/ipd-lifecycle/$id.receipt.json; done
    .aw/records/plans/executed/20260915-rununify-03-i3d6ml-lift-the-48-non-conflicting-shared-runner-symbols-into-runne.ipd.md
      receipt exists: no
    .aw/records/plans/executed/20260915-rununify-04-tx6q0h-parameterize-the-8-host-label-symbols-and-lift-them-to-runne.ipd.md
      receipt exists: no
    .aw/records/plans/executed/20260915-rununify-06-sy7uwh-unify-the-plan-record-type-and-its-two-readers-overriding-th.ipd.md
      receipt exists: no
    ```

    A CORRECTION TO THIS PLAN'S OWN ASSUMPTION, stated rather than quietly dropped: all three real plans are ALREADY in `.aw/records/plans/executed/` and hold no live receipt. They were recovered between the incident and this execution by some other route (a hand-run or delegated finalize), NOT by this turn, which touched none of them. So "the three stranded plans" are no longer stranded ON DISK; what E-07 establishes is the counterfactual it was written to establish, that the widening accept WOULD have let each of them finalize in the run where it failed. That remains the load-bearing claim, since the next occurrence of this shape is what the fix prevents.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted output showing each of `tests/`, `agent_workflows`, `agent_workflows/**` and `*` REFUSED as an added entry with the offending entry NAMED, and a literal `tests/test_resumedupe.py` accepted. PLUS the shared-table test proving the eligibility classifier and `_scope_match` agree on entry shape, including the bare-directory case (`agent_workflows`) which contains no glob character yet matches by prefix.
  - Observed evidence: All four fence-neutering shapes REFUSED, each with the offending entry NAMED in the reason:

    ```
    (E-08) added entry 'tests/'
      added=['tests/'] removed=[] non_scope_identical=True
      eligible=False ineligible_reason='added Scope-Paths entry would widen the fence to a DIRECTORY or GLOB rather than a literal file: tests/'
      widening_is_acceptable=False
    (E-08) added entry 'agent_workflows'
      added=['agent_workflows'] removed=[] non_scope_identical=True
      eligible=False ineligible_reason='added Scope-Paths entry would widen the fence to a DIRECTORY or GLOB rather than a literal file: agent_workflows'
      widening_is_acceptable=False
    (E-08) added entry 'agent_workflows/**'
      added=['agent_workflows/**'] removed=[] non_scope_identical=True
      eligible=False ineligible_reason='added Scope-Paths entry would widen the fence to a DIRECTORY or GLOB rather than a literal file: agent_workflows/**'
      widening_is_acceptable=False
    (E-08) added entry '*'
      added=['*'] removed=[] non_scope_identical=True
      eligible=False ineligible_reason='added Scope-Paths entry would widen the fence to a DIRECTORY or GLOB rather than a literal file: *'
      widening_is_acceptable=False
    ```

    NOTE `non_scope_identical=True` IN ALL FOUR: these are genuinely additive, strict-superset widenings, so the strict-superset rule ALONE would have accepted every one. Only the eligibility restriction stops them, which is exactly F-11's point and why this item is not redundant with V-03.

    THE CONTRAST CASE IS ACCEPTED, so the rule is a restriction and not a blanket refusal: a literal `tests/test_resumedupe.py` gives `eligible=True`, `widening_is_acceptable=True` (`WideningEligibilityTests::test_a_literal_file_path_addition_is_accepted`).

    END TO END through `finalize`, so the refusal is not merely a predicate result (`AdditiveScopeWideningTests::test_a_directory_addition_refuses_and_NAMES_the_offending_entry`): adding `tests/` and supplying a `--scope-reason` for it still returns `EXIT_FINDINGS`, keeps the STALE message, leaves the plan unmoved, and emits a finding containing both `tests/` and `DIRECTORY or GLOB`. One reason string cannot buy a repo-wide fence.

    THE SHARED-TABLE TEST (`WideningEligibilityTests::test_the_eligibility_classifier_and_scope_match_agree_on_entry_shapes`) drives `scope_entry_is_literal_file` and `_scope_match` over one table of entry shapes: `tests/`, `tests/**`, `agent_workflows/**`, `*`, `tests/test_*.py` (all ineligible) and `tests/test_resumedupe.py` (eligible), asserting for each that `_scope_match` admits a probe path inside the tree it would open. The classifier branches on the SAME classification `_scope_match` branches on (trailing `/`, trailing `/**`, any of `* ? [`), so the eligibility rule and the matching rule cannot disagree by construction.

    THE BARE-DIRECTORY CASE is asserted explicitly, because it is the one a naive "has no glob character" rule gets wrong: the test asserts that `scope_entry_is_literal_file("agent_workflows")` is `True` (the pure classifier genuinely cannot see it), that `_scope_match("agent_workflows/check_engine.py", "agent_workflows")` is `True` (it matches by PREFIX and so admits the whole package), that `_entry_is_bare_directory(root, "agent_workflows")` is `True` while it is `False` for `tests/test_demo.py`, and that the COMBINED decision therefore yields `eligible=False`. That is why the filesystem probe exists as a separate function rather than being folded into the pure classifier.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: three pasted tests, one per ineligible shape (legacy v1, becoming-grandfathered, grandfathered-plus-paths), each refusing with today's message. PLUS the assertion that the v1 path does not invoke the new comparison at all, since `:860-864` binds a v1 receipt to the whole-file rule and running a v2-shaped comparison on it would be the exact "accepted by a rule it was never bound under" error that comment forbids.
  - Observed evidence: All three shapes measured, each ineligible with its own named reason:

    ```
    (E-09a) LEGACY v1 receipt, widened plan
      added=[] removed=[] non_scope_identical=False
      eligible=False ineligible_reason='legacy v1 receipt (no frozen_region_digest): bound to the whole-file rule'
      widening_is_acceptable=False
      receipt_is_current=False
    (E-09c) plan BECAME grandfathered
      added=[] removed=['agent_workflows/demo.py', 'tests/test_demo.py'] non_scope_identical=False
      eligible=False ineligible_reason='the plan BECAME grandfathered mid-execution: its declared allowlist was emptied, which is a scope REMOVAL and a changed scope model'
      widening_is_acceptable=False
      receipt_is_current=False
    (E-09b) GRANDFATHERED receipt, plan now declares paths
      added=['agent_workflows/demo.py', 'tests/test_demo.py'] removed=[] non_scope_identical=False
      eligible=False ineligible_reason='the receipt was issued for a plan with no declared allowlist (grandfathered/absent): declaring paths now CHANGES the scope model rather than widening it'
      widening_is_acceptable=False
      receipt_is_current=False
    ```

    ONE TEST PER SHAPE, each with the reason in its docstring, in `tests/test_receipt_requirement_digest.py::IneligibleReceiptShapeTests`:
    - (a) `test_legacy_v1_receipt_is_not_eligible_and_is_not_even_compared`
    - (b) `test_a_grandfathered_receipt_gaining_paths_is_a_changed_scope_MODEL`
    - (c) `test_a_plan_that_BECOMES_grandfathered_reads_as_a_removal`

    THE v1 PATH DOES NOT INVOKE THE COMPARISON AT ALL, which is the specific assertion this item demands. `frozen_region_comparison` returns on its FIRST branch when `frozen_region_digest` is absent, before reading any scope or building any payload, and the test asserts the OBSERVABLE consequence: `added == []`, `removed == []`, `non_scope_identical is False`. So nothing was computed and nothing was proven about the non-scope categories; the v1 receipt stays bound to the whole-file rule and cannot be "accepted by a rule it was never bound under". The empty delta on a plan that visibly DID gain a path is the evidence that the substitution was skipped rather than run and rejected.

    (c) READS AS A REMOVAL, not as an unchanged empty set: `removed` names BOTH previously declared paths. (b) is refused because in that shape the two scope inputs are NOT the same field, which the test asserts directly before exercising the refusal: `_frozen_scope_paths(gf_text) == []` while `_requirements_from_plan(gf_text)["scope"][0] == "grandfathered"`. A substitution that replaced only one of the two would silently mis-compare, which is why the shape is excluded rather than reasoned about.

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_receipt_requirement_digest.py -o addopts="" -q
    ...................                                                      [100%]
    19 passed in 1.10s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (9 E-items in 3 task groups, under the 18-leaf / 5-group thresholds). Assessed for CONCEPTUAL density at review, not only count: each E-item has one deliverable and one test surface, and the two largest (E-03's predicate and E-04's accept-plus-runner) were examined specifically for bundling. E-04 is the one item that legitimately touches two modules, and it is kept whole deliberately: the lifecycle accept and the runner's ability to supply the reason are ONE behavior (F-10 measured that either alone leaves the incident unfixed), so splitting them would produce a child that passes its own tests while the fix does not work.

EXECUTION CONTRACT. `OQ-01` and `OQ-02` are both non-blocking and the maintainer's; execute with the
STRICT form on both (a `--scope-reason` per added path; only a LITERAL FILE PATH eligible) and do not
guess a relaxation. THE FOUR THINGS REVIEW MEASURED THAT YOU MUST NOT RE-DERIVE FROM THE OLD TEXT:
(1) the receipt DOES store `scope_paths` (F-6 is WITHDRAWN, do not build a v3 receipt); (2) an
uncommitted undeclared edit is DISREGARDED, not reasoned (F-8); (3) therefore the reason demand must be
EXPLICIT and unconditional per added path or it is vacuous (F-9); (4) the RUNNER must be taught to
supply it or the three cited lanes still strand (F-10). SCOPE FENCE: this plan declares
`agent_workflows/ipd_lifecycle.py`, `agent_workflows/runner_shared.py`, four test files, and one spec
file; an out-of-scope edit must be made only if genuinely required and then JUSTIFIED to
`aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a
`--scope-ack`. DO NOT EDIT `agent_workflows/check_engine.py` (`wmnmei` owns the advisory; E-02 REPORTS
the interaction and does not change it) and DO NOT EDIT ANY OTHER SPEC SECTION than 5.5's never-retry
clause. THE IRONY IS DELIBERATE AND IS ALSO THE BEST DOGFOOD: if executing this plan requires touching a
file it did not declare, the executor will meet the very refusal this plan removes. Record that if it
happens; it is evidence, not an obstacle. THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test
output for every `V-*`; never claim a test run you did not run, and never soften a refusal into an
acceptance to make an item pass. A gate that accepts one case more than it should is worse than the bug
this plan fixes, and V-04's uncommitted variant is the specific place where a vacuous pass would hide.
Commit path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit
run `git diff --cached --name-only` and unstage anything not yours; this is a shared checkout with
concurrent sessions. After the gate, move this plan to `.aw/records/plans/executed/` via
`aw ipd finalize`, and do not claim done until `aw ipd lint --phase pre-transition` conforms and every
`V-*` above carries real observed evidence.

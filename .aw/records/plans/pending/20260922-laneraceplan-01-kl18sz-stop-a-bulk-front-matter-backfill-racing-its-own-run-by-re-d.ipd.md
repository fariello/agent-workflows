# IPD: Stop a bulk front-matter backfill racing its own run by re-deriving the edit against the settled tree

- Date: 2026-09-22
- Kind: child
- Concern: A plan whose job is to edit front matter across the whole `pending/` population is, by construction, contending with every execute item in its own run, so the more successful the run the more conflicts that plan causes and the more likely it is to be stranded. MEASURED on item `8u6770` in run `run-20260922T024054Z-2245533`, which ended `merge-refused` with a real git conflict in 13 files, ALL of them `.aw/records/plans/*.ipd.md` and NONE of them code.
  THE SHAPE IS A PURE LIFECYCLE RACE, NOT A DISAGREEMENT. `8u6770` reads plans in `.aw/records/plans/pending/` and adds two adjacent front-matter lines (`- Work-Kind:` and `- Priority:`) plus one history line to each, inheriting each value from a backlog item the plan itself names. While it ran, THE SAME RUN executed 13 of those very plans, and executing a plan moves the file `pending/` -> `executed/` AND rewrites its `- Status:` line from `approved` to `executed` AND appends its own history line. Git therefore sees both sides touching adjacent lines of a renamed file and conflicts. Measured at resolution time: of the 45 plans the lane edits, 15 had already moved to `executed/` on `main`.
  THE TWO EDITS ARE NOT IN OPPOSITION, which is what makes this losslessly resolvable and therefore worth automating. The lane's own appended history line says in as many words "status unchanged (no lifecycle transition)", so it never intended to touch `- Status:` at all. Resolution is mechanical: keep `main`'s `- Status:`, keep the lane's two new fields, keep both history lines. That is exactly what a human did on 2026-09-22 for all 13 files, verified green.
  THERE IS A TRAP IN THE OBVIOUS RESOLUTION, and it is a RESOLVER'S trap rather than a silent-merge one. The lane holds a ten-day-old snapshot in which those 13 plans still read `- Status: approved`. Taking the lane's side of the conflict, which is the natural thing to do for "the branch that owns this edit", asserts that 13 plans sitting in `executed/` are merely approved and undoes 13 real executions. PRECISION MATTERS HERE AND AN EARLIER VERSION OF THIS PARAGRAPH OVERSTATED IT: git does NOT do this on its own. Measured in throwaway repositories, a stale side that edits a plan `main` has moved produces `CONFLICT (modify/delete)`, or `CONFLICT (content)` once rename detection fires, and a stale side that does not touch the plan leaves the transition intact; there is no conflict-free path that un-executes a plan. So the hazard is entirely in what a HUMAN OR AGENT then types at the conflict prompt, where "keep the lane's version" is one keystroke and looks defensible. That is still worth engineering against, because the resolver is handed 13 files and no signal that one side's `- Status:` is a stale snapshot, but the claim is about resolver ergonomics and not about git losing data.
  THIS IS AN ARCHETYPE RATHER THAN AN INCIDENT. The same Set contains `lc4unl` (Order 03), which hit the same class and also ended unintegrated, and `lkexaw` (Order 01), which is the same kind of population-wide records edit. So the pattern recurs for every plan of this shape, and the cost scales with how well the run performs.
- Scope: Make a population-wide records edit survive its own run, by RE-DERIVING the intended field values against the settled tree at integration time rather than merging a stale snapshot of them, and/or by ordering such a plan after the execute items it would contend with. EXCLUDES any change to what values are written or to the inheritance rule that picks them (that is `planprio`'s own subject matter), excludes editing any plan in a terminal directory, and excludes the post-merge revalidation defect (sibling plan `tgyfs2`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_records_only_lane_rederive.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: laneraceplan
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kl18sz
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: 21fykf

## Workflow history
- 2026-09-23 implementation-complete (opencode its_direct/pt3-claude-opus-5-1m-us): NOT A LIFECYCLE TRANSITION - the plan's `- Status:` is UNCHANGED and only the runner may finalize it (`AW-LIFECYCLE-ROLE-001`). ALL FIVE E-items PERFORMED and V-01..V-05 verified with pasted evidence; `aw ipd lint --phase pre-transition` CONFORMING. THE REPLAY SOURCE IS BETTER THAN THE PLAN COULD KNOW, and F-7 is partly corrected: `aw/lane/8u6770` and `aw/lane/lc4unl` are indeed absent as BRANCH REFS (94 lane refs checked; `aw/lane/lc4unl_attempt2` carries zero work), but the original lane's commits SURVIVE as dangling objects, so the replay ran against the real finalize tip `0abc01d9` and produced a 34-path conflict set (30 targets now in `executed/`, 4 in `pending/`), every path a `.ipd.md` plan and ALL 34 classifying as this one shape. That is larger than the recorded 13 only because main has advanced; it is NOT a claim to have reproduced that day's number, and no synthetic fixture was used. TWO MEASUREMENTS CORRECTED THE PLAN'S EXPECTATIONS. FIRST, the anti-revert defence is DOUBLE rather than single: widening the allow-list to `- Status:` does not even reach the writer on the real shape, because the classifier's clash rule refuses first, so the test now pins BOTH layers and says which is load-bearing (the writer's, since it accepts only the shipped constant while the classifier accepts an injected list for testability). SECOND, the plan's expected pre-existing failure in `test_orchestrator_retirement.py::RealRepositorySets` DID NOT OCCUR in either run. ONE OUT-OF-SCOPE EDIT, made and justified per the scope fence: `tests/test_runner_shared.py::...::test_the_kind_vocabulary_is_UNCHANGED_by_the_extraction` asserts the returned kind set EQUALS exactly three members, and F-11 forbids reusing either `integrated` or `merge-refused` for a recomputed integration, so the expected set is now four and remains an EQUALITY assertion; `aw check` reports `check.scope-drift` for it, which is the gate working, and it needs a `--scope-reason` at finalize. Suite bare: `1 failed, 8605 passed, 3 skipped, 2 xfailed` against a same-session baseline of `1 failed, 8567 passed, 3 skipped, 2 xfailed` at `6444056e`; no new failing node ids, the one failure being the known ambient `OPENCODE_CONFIG_CONTENT` leak (`76 passed` under `env -u`). Spec `25kzda` gained Section 2.1a, phrased on the RECOMPUTED-versus-RETRIED distinction the approval rests on, leaving stale base / scope violation / combined-red terminal by name. NOT FINALIZED by this lane: the runner owns `aw ipd begin`/`aw ipd finalize` (`AW-LIFECYCLE-ROLE-001`).
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-09-22, findings OQ-01. Recomputed at HEAD `721e3003`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-22 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 7 findings, all FIXED; OQ-01 remains Blocking: yes and open (a maintainer contract decision, now carrying the spec-amendment cost found at review); readiness no-go until answered; typed review record under .aw/records/reviews/

- 2026-09-22 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007, all FIXED. Reviewed at HEAD `fbf5f85c`; `aw ipd lint --phase author` exit 1 on `IPD-Q501` (OQ-01 blocking and open, which is CORRECT here and stays), `--phase review-finalize` conforming after with that same expected gate; `aw check` reported `check.ipd-uncarried-obligation` at error, now clear. THE DIAGNOSIS IS EXCELLENT AND THE PLAN'S SELF-CORRECTION IS EXEMPLARY: the orthogonality argument (F-1/F-2/F-3) is sound, the lane's own history line does say "status unchanged (no lifecycle transition)", the archetype claim verifies (`lc4unl`, `lkexaw` and `8u6770` all present, `21fykf` graduated with the same gate), the integration seam really is shared in `runner_shared` so `Scope-Paths` is right for E-01..E-04, and the plan correctly retracts its own earlier silent-revert claim after measurement. SEVEN DEFECTS. (PR-001, BLOCKER) The mandatory replay is UNSATISFIABLE: `aw/lane/8u6770` is ABSENT from all 125 lane branches, so "the lane branch and the merge base are both still resolvable" is false and the 13-file replay V-01 demands cannot be reconstructed; `aw/lane/lc4unl` does exist (tip `b1223b4f`, 4 paths, all under `.aw/records/`) and is now the sanctioned substitute with an honest size caveat. (PR-002, BLOCKER) E-03 contradicts an APPROVED SPEC, not merely a docstring: spec `25kzda` 2.1 says the ladder "never applies to a genuine merge conflict ... none of which repetition fixes" and that "no rung ... reclassifies a failure as a deferral", and `8u6770` hit exactly that class, so re-derivation needs a declared narrow carve-out in the same change; the plan cited only `runner_shared.integrate_lane_branch`'s docstring and declared no spec path. (PR-004) "Orthogonal to `- Status:`" is a deny-list of one, which would admit `- Readiness:` (an attestation only `/plan-review` may write and the auto-approve predicate reads FIRST), `- Approval:`, `- Blocks-Release:` and `- Item-Dependencies:` to automatic writing; now an explicit allow-list (`- Work-Kind:`, `- Priority:`) with its own failing-test control. (PR-005) The shape spanned all of `.aw/records/` although only plan front matter was measured, and `lc4unl`'s own diff includes two `.backlog.md` files; now type-aware with UNKNOWN for unmeasured types. (PR-006) A re-derived integration had no distinct reported outcome, so it would surface as a plain `integrated`, hiding the one event an auditor needs; `merge-refused` is documented in-code as "the gate measured the work and REFUSED it" and must not be stretched either. (PR-003) The `queue_sort_key`/`dependency_depth` convention is real but lives in `oc_runipd`, not `runner_shared` as cited. (PR-007) Both open questions named no durable carrier. OQ-01 REMAINS `Blocking: yes` and open BY DESIGN: it is a genuine maintainer decision, now carrying the spec cost so it can be answered once with the price visible.
- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `21fykf`, inheriting its `Blocks-Release: next` gate. The conflict shape was measured across all 13 files during a hand-resolution on 2026-09-22 and was IDENTICAL in every one (main's `- Status: executed` versus the lane's `- Status: approved` plus two new keys, and two competing history lines), which is what justifies a mechanical fix rather than case-by-case judgement. The plan deliberately offers detection-and-refusal as the minimum viable outcome (E-01/E-02) so that even if the maintainer rejects automatic re-derivation, the resolver-facing trap is closed. NOTE a correction made during authoring: an earlier draft called that trap a SILENT merge revert, and the maintainer challenged it correctly. Measurement showed git always conflicts loudly in this shape, so the trap is in what a resolver chooses at the prompt, not in git losing the transition.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop a records-only backfill being punished for its own run's success, and make it impossible for a resolver to un-execute a plan while resolving the conflict it causes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the trap first

- [x] E-01 Add a pure classifier that recognizes the RECORDS-ONLY FRONT-MATTER conflict shape: every conflicting path is under `.aw/records/`, and on each the incoming side changes only front-matter keys ORTHOGONAL to `- Status:` while the target side changed `- Status:` and/or the file's lifecycle directory. It must return a three-valued answer and report UNKNOWN for anything it cannot prove, never assuming the safe-looking case.
  - Depends on: none
  - DEFINE "ORTHOGONAL" AS AN EXPLICIT ALLOW-LIST, NOT AS "NOT `- Status:`" (PR-004). A deny-list of one key silently admits every field that has lifecycle or gate meaning, and this repository has several whose forgery the conventions treat as a serious matter: `- Readiness:` is an attestation only `/plan-review` may write, `- Approval:` records human sign-off, `- Blocks-Release:` carries a release gate, `- Item-Dependencies:` changes queue ordering, and `- Id:`/`- Set:`/`- Order:` are identity. A classifier that calls any of those orthogonal would let an integration write one automatically. So enumerate the keys that MAY be re-derived (the measured case needs exactly `- Work-Kind:` and `- Priority:`), treat every other key as NOT this shape, and state the allow-list in the code so widening it is a visible edit rather than an accident.
  - CLASSIFY THE ARTIFACT TYPE TOO, since `.aw/records/` is broader than plans. The measured shape is plan front matter under `plans/`, while backlog, spec, release and review records have their own status vocabularies and their own lifecycle directories; `aw/lane/lc4unl` itself touches two `backlog/open/*.backlog.md` files alongside two plans. Either restrict the shape to the types you have actually measured or state per type what counts as orthogonal. An UNKNOWN verdict for an unmeasured type is correct and cheap.
  - Expected outcome: given a real conflicting file set of this shape, classifies every file as this shape; given a conflict touching a code path, a `- Status:`-versus-`- Status:` disagreement, a non-allow-listed front-matter key, or an unmeasured record type, returns UNKNOWN or not-this-shape. Paste the allow-list.
  - Execution state: performed
- [x] E-02 Make the integration REFUSE with a shape-specific, actionable message when E-01 recognizes this case, naming the trap explicitly: state that the incoming branch holds a STALE lifecycle snapshot, that taking its `- Status:` would revert N real executions, and name the files. This was authored as the minimum viable outcome for a NO answer to OQ-01; the answer was YES (2026-09-22), so it is no longer a landable stopping point, but it remains worth landing FIRST because it changes no contract and closes the measured resolver trap before E-03's riskier write path exists.
  - Depends on: E-01
  - THIS ITEM CHANGES NO CONTRACT AND THAT IS ITS VALUE. It still returns the same terminal `merge-refused` kind for the same condition, so spec `25kzda` 2.1's prohibition is untouched and no spec path is needed; only the MESSAGE improves. Keep it that way: if implementing E-02 starts to alter the refusal's classification or its terminality, it has drifted into E-03 and inherits E-03's spec obligation.
  - SAY WHICH SIDE IS STALE AND HOW TO RESOLVE IT, in the message, because the whole measured hazard is a resolver typing "keep the lane's version" at a prompt where both sides look defensible. Name the safe resolution concretely (keep the target's `- Status:` and lifecycle directory, keep the incoming branch's new orthogonal keys, keep BOTH history lines), which is exactly what the human did on 2026-09-22 for all 13 files.
  - Expected outcome: replaying a real conflict of this shape produces a refusal naming the already-executed plans and the safe resolution, instead of today's generic conflict text. State the replay source and its size (see the substitution rule in Required tests: the original 13-file lane no longer exists).
  - Execution state: performed

### Task group 2: re-derive instead of merge

- [x] E-03 Implement RE-DERIVATION for the recognized shape (AUTHORIZED: OQ-01 answered yes by the maintainer 2026-09-22): instead of merging the lane's stale file content, re-apply the lane's ORTHOGONAL front-matter keys onto the CURRENT `main` version of each plan, wherever that plan now lives, leaving `- Status:` and the lifecycle directory untouched. The lane's history line is appended without disturbing the target's own history entries.
  - Depends on: E-01
  - THIS ITEM REQUIRES A SPEC AMENDMENT IN THE SAME CHANGE (PR-002). Spec `25kzda` Section 2.1 states the integration ladder "never applies to a genuine merge conflict ... none of which repetition fixes" and that "no rung ... reclassifies a failure as a deferral", and a genuine merge conflict is precisely what `8u6770` hit. So re-derivation contradicts the shipped contract until that spec carries a narrow carve-out. The declare-first obligation is ALREADY SATISFIED: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` was added to `Scope-Paths` on 2026-09-22 when the maintainer answered OQ-01 yes. Amend it in the SAME change and write the carve-out so every other conflict class stays terminal on first attempt, phrasing it on the RECOMPUTED-versus-RETRIED distinction that is the reasoning the approval rests on. See the spec-sync section for the exact quotes and the three obligations.
  - DO NOT LAUNDER A REFUSAL INTO A SUCCESS. `runner_shared.INTEGRATION_REFUSAL_CONFLICT` is `merge-refused` and its comment defines it as "the gate measured the work and REFUSED it", collapsing four distinct causes (`integration_failed_stale_base`, `integration_failed_conflict`, `integration_failed_scope_violation`, `integration_failed_combined_red`). A re-derived integration is NEITHER a plain success NOR that refusal, so give it its own reported outcome and say in the run record that content was RECOMPUTED rather than merged. Reporting it as an ordinary `integrated` hides the one event an auditor most needs to see.
  - RE-DERIVE FROM THE LANE'S INTENT, NOT BY REPLAYING ITS DIFF. The lane's diff is expressed against a ten-day-old snapshot, so applying it as a patch reintroduces the staleness this item exists to remove. Extract the KEY/VALUE pairs the lane added and write those keys onto the current file; if a key already exists on the current file with a different value, that is NOT this shape and E-04's fail-closed rule applies.
  - Expected outcome: applying the intended edit to current `main` yields each plan carrying both new keys AND its true current `- Status:`, with zero plans moved between directories by this step, plus the spec amendment diff and the distinct reported outcome.
  - Execution state: performed
- [x] E-04 Fail closed on any file E-01 did not positively classify: re-derivation applies ONLY to the proven shape, and anything else keeps today's conflict refusal. A partially re-derivable conflict set must NOT be half-applied; either every conflicting file is classified or the whole integration refuses.
  - Depends on: E-03
  - Expected outcome: a conflict set mixing one records-only file and one code file refuses entirely, with nothing written.
  - Execution state: performed

### Task group 3: prove it and prevent the resolver revert

- [x] E-05 Add the regression file with an explicit ANTI-REVERT control: a test that FAILS if any code path can produce a result where a plan present in a terminal directory on `main` ends carrying a non-terminal `- Status:` from an incoming branch. Plus coverage of the classifier's UNKNOWN arm and E-04's all-or-nothing rule.
  - Depends on: E-01, E-02, E-03, E-04
  - ADD AN ALLOW-LIST CONTROL BESIDE THE ANTI-REVERT ONE, since F-9 shows `- Status:` is not the only key whose automatic writing would be a defect. Assert that a conflict whose incoming side touches `- Readiness:`, `- Approval:`, `- Blocks-Release:` or `- Item-Dependencies:` is NOT classified as this shape, and that widening the allow-list to include one of them fails a test. `- Readiness:` is the sharpest case: the repository's own conventions call a hand-written value a forged attestation that the auto-approve predicate reads FIRST, so an integration that could write it is strictly worse than the conflict it resolves.
  - PIN THE UNMEASURED-TYPE ARM TOO (F-10): a conflict on a `.backlog.md` or `.spec.md` record must return UNKNOWN rather than being treated as a plan.
  - THE SUITE RULE: the gate is NO NEW failing node ids against a baseline taken THE SAME WAY in the same session, never an absolute green. Measured at review HEAD in this lane: `2 failed, 8521 passed, 3 skipped, 2 xfailed`, both unrelated to this plan (`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, an ambient `OPENCODE_CONFIG_CONTENT` leak that is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`; and `tests/test_orchestrator_retirement.py::RealRepositorySets`, unrelated corpus drift whose own message forbids loosening it). Classify each failure; edit neither test.
  - Expected outcome: the file is RED against pre-fix source and GREEN after; the anti-revert control fails if re-derivation is ever widened to `- Status:`; the allow-list control fails if it is widened to a gate or attestation key; the unmeasured-type arm returns UNKNOWN; plus the suite result with every failure classified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The runner ALREADY orders a queue by declared dependency depth first (`dependency_depth` is the first key in `queue_sort_key`, and "DECLARED EDGES WIN" is stated there), so ordering a bulk-records plan after its contenders is expressible today via `- Item-Dependencies:` without new scheduler work. That is why OQ-02 treats sequencing as an available alternative rather than a feature request. CORRECTED AT REVIEW: both symbols live in `oc_runipd`, NOT in `runner_shared` (`oc_runipd.queue_sort_key`, `oc_runipd.dependency_depth`, with the "DECLARED EDGES WIN" sentence in the former's docstring and no agy-side definition of either). The convention holds exactly as stated and no code change is asked of it, so `Scope-Paths` needs no widening; the attribution is fixed only so a reader looking for it finds it.
- THE INTEGRATION SEAM ITSELF IS SHARED, which is why `Scope-Paths` naming `runner_shared.py` alone is right for E-01 to E-04: `runner_shared.integrate_lane_branch` is the one implementation both hosts reach through thin wrappers, and the refusal kinds (`INTEGRATION_REFUSAL_CONFLICT = "merge-refused"` and its siblings) are defined there too. A classifier and a refusal message added there reach both runners with no per-host edit.
- A REFUSAL KIND CARRIES A MEANING THAT MUST NOT BE STRETCHED. `merge-refused` is documented in-code as "the gate measured the work and REFUSED it", deliberately renamed from `merge-conflict` because a conflict is only one of the four causes it collapses. So a new behavior needs a new reported outcome rather than a quiet reuse of that word (F-11).
- Never edit a plan in a terminal directory: this repository closes a post-execution gap with a new corrective IPD instead. E-03 must therefore write to `executed/` plans' front matter ONLY if the maintainer explicitly permits it in OQ-03; otherwise those plans keep their missing fields and the gap is reported.
- The existing conflict handling treats conflict DETECTION as the gate's job and conflict RESOLUTION as a human/serial-ordering concern. E-02 respects that split (it improves the refusal), while E-03 deliberately crosses it, which is precisely why OQ-01 was blocking (and why the maintainer, not the executor, authorized the crossing on 2026-09-22). BUT THAT SENTENCE IS A DOCSTRING, NOT THE GOVERNING RULE, and the real obstacle is stronger (F-8): spec `25kzda` Section 2.1 flatly prohibits automated handling of a genuine merge conflict, so E-03 needs a declared spec amendment and not merely a decision to cross a convention.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The conflict is records-only, never code | 13 conflicting files, all `.aw/records/plans/*.ipd.md`; the lane changes 47 files and 0 outside `.aw/records/` |
| F-2 | The two sides are orthogonal | lane adds `- Work-Kind:`/`- Priority:`; main rewrote `- Status:` and moved the file |
| F-3 | The lane never intended to touch status | its own history line reads "status unchanged (no lifecycle transition)" |
| F-4 | Taking the lane's side un-executes real plans, but only by a RESOLVER's choice | the lane's snapshot says `approved` for 15 plans now in `executed/`; git itself always conflicts loudly here (measured), so the risk is the resolution step, not the merge |
| F-5 | The shape was uniform across all 13 files | a single mechanical rule resolved every one, verified green |
| F-6 | It is an archetype, not an incident | sibling `lc4unl` hit the same class in the same run; `lkexaw` is the same plan shape. All three plans verified present in `pending/` at review, and `21fykf` is `graduated` carrying the same `Blocks-Release: next` |
| F-7 | THE NOMINATED REPLAY SOURCE NO LONGER EXISTS, so the mandatory 13-file replay is unsatisfiable as authored | measured at review: `aw/lane/8u6770` is absent from all 125 lane branches (`git branch -a`), contradicting "the lane branch and the merge base are both still resolvable". `aw/lane/lc4unl` DOES exist (tip `b1223b4f`) and its diff against `main` is 4 paths, all under `.aw/records/` (2 backlog, 2 plans), so it is a usable but SMALLER substitute |
| F-8 | A SHIPPED SPEC PROHIBITION blocks E-03, not merely a docstring | spec `25kzda` Section 2.1: the ladder "never applies to a genuine merge conflict ... none of which repetition fixes", and "no rung ... reclassifies a failure as a deferral"; the 2026-09-21 amendment note repeats the scope and says "No rule changed". The authored plan cited only `runner_shared.integrate_lane_branch`'s docstring line, which is not the governing rule |
| F-9 | "ORTHOGONAL TO `- Status:`" IS TOO WEAK A TEST for what may be auto-written | a deny-list of one key admits `- Readiness:` (an attestation only `/plan-review` may write), `- Approval:`, `- Blocks-Release:` (a release gate), `- Item-Dependencies:` (queue ordering) and `- Id:`/`- Set:`/`- Order:` (identity). E-01 now requires an explicit ALLOW-list, which for the measured case is exactly `- Work-Kind:` and `- Priority:` |
| F-10 | `.aw/records/` IS BROADER THAN PLANS and the other types have their own status vocabularies | `aw/lane/lc4unl` touches two `backlog/open/*.backlog.md` files beside two plans; backlog, spec, release and review records each carry a different status enum and lifecycle layout, so one plan-shaped rule cannot be assumed to fit them |
| F-11 | A RE-DERIVED INTEGRATION IS NEITHER A SUCCESS NOR THE EXISTING REFUSAL | `runner_shared.INTEGRATION_REFUSAL_CONFLICT` is `merge-refused`, defined in-code as "the gate measured the work and REFUSED it" and collapsing four causes. Reporting a recomputed integration as plain `integrated` would hide the one event an auditor most needs to see |

## Proposed changes (ordered, validatable)

1. A three-valued, type-aware classifier for the records-only front-matter conflict shape, driven by an
   explicit ALLOW-list of re-derivable keys rather than by "not `- Status:`" (E-01).
2. A shape-specific refusal naming the stale-snapshot trap and the concrete safe resolution, so the resolver
   is told which side's `- Status:` is stale. Changes no contract (E-02).
3. Re-derivation of allow-listed keys onto the current tree, authorized by OQ-01's maintainer answer and
   gated on the spec carve-out F-8 requires, reported as a distinct outcome rather than as a plain
   success (E-03).
4. All-or-nothing fail-closed behavior for unclassified files (E-04).
5. Regression coverage with TWO controls: anti-revert (no terminal plan acquires a non-terminal status) and
   allow-list (the mechanism can never write a gate or attestation key) (E-05).

## Deferred / out of scope (with reason)

- WHICH values a backfill writes and the inheritance rule that chooses them: that is `planprio`'s subject (`8u6770`, `lc4unl`, `lkexaw`). This plan is about surviving integration, not about the values.
  - Carrier: 8u6770
- The post-merge revalidation baseline defect (sibling plan `tgyfs2`): a different cause of the same run's strandings. `8u6770` failed on a genuine git conflict, not on a suite verdict.
  - Carrier: tgyfs2
- Editing plans already in `executed/` to add their missing fields: deferred to OQ-03 because it collides with the standing rule against editing terminal-directory plans.
  - Carrier-Declined: HELD BY THIS PLAN'S OWN BLOCKING-ADJACENT OQ-03, which names the maintainer as owner and forbids the executor from touching an `executed/` plan absent an explicit answer. Filing a separate carrier now would assert that the retroactive edit WILL happen, which is precisely the question OQ-03 leaves open; if the answer is yes, the carrier is authored then, and if it is no those plans stay unlabelled by decision. Recorded as a known gap rather than silently closed.
- A general-purpose semantic merge driver for records: far wider than the measured problem. This plan addresses ONE proven shape and fails closed on everything else.
  - Carrier-Declined: DELIBERATELY NOT WANTED, not postponed. The measured problem is one uniform shape (F-5), and E-04's all-or-nothing rule plus E-01's allow-list exist to keep the scope that narrow on purpose. A general merge driver would be a larger contract change against the spec prohibition F-8 records, so filing it as outstanding work would misrepresent a rejected design as a pending one.

## Scope check

- Over-scope: none. One source path, one new test file, and the spec path E-03's amendment requires (F-8). UPDATED 2026-09-22 WHEN OQ-01 WAS ANSWERED YES: the spec path is now DECLARED, and the earlier note saying it was deliberately omitted no longer applies. That omission was correct only while the answer was unknown (declaring it would have announced a spec change the plan might never make); now that E-03 is approved, the opposite is true and the declaration is MANDATORY, because both runners announce declared spec edits before a run starts and the finalize scope gate reconciles what was actually changed against what was declared. An undeclared spec edit would be an out-of-scope path needing a `--scope-reason` at finalize.
- Under-scope: this plan does not re-run `8u6770` itself. That lane was discarded and the work re-derived by hand, because the lane's content is a mechanical lookup that is cheaper to recompute than to merge; the 15 already-executed plans consequently still lack the two fields, which OQ-03 covers. CONFIRMED AT REVIEW that the lane is gone (`aw/lane/8u6770` is absent from all 125 lane branches), which is why the replay source had to be re-pointed (F-7).
- Under-scope, closed at review (2026-09-22): the mandatory replay named a lane branch that no longer exists, making V-01 unsatisfiable as written (PR-001/F-7, now re-pointed at `aw/lane/lc4unl` with an honest size caveat and a labelled synthetic fallback); E-03 contradicted an approved spec's flat prohibition while the plan cited only a docstring, so the amendment obligation was understated and undeclared (PR-002/F-8, now stated with the quotes and three obligations); "orthogonal to `- Status:`" would have admitted `- Readiness:`, `- Approval:`, `- Blocks-Release:` and `- Item-Dependencies:` to automatic writing (PR-004/F-9, now an explicit allow-list with a test control); the shape was defined over all of `.aw/records/` although only plan front matter was measured (PR-005/F-10, now type-aware with UNKNOWN for unmeasured types); a re-derived integration had no distinct reported outcome and would have been reported as an ordinary success (PR-006/F-11); and both open questions named no durable carrier (PR-007).

## Required tests / validation

- `python3 -m pytest tests/test_records_only_lane_rederive.py` GREEN after, and RED before, the before-run produced by reverting only the source file while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- A REPLAY against a REAL recorded conflict, with the substitution rule below, because the originally
  nominated source is GONE. Measured at review 2026-09-22: `aw/lane/8u6770` DOES NOT EXIST among the 125 lane
  branches in this repository, so "the lane branch and the merge base are both still resolvable" is FALSE and
  the 13-file replay cannot be reconstructed from it. What DOES still exist is `aw/lane/lc4unl` (and
  `aw/lane/lc4unl_attempt2`), the sibling F-6 names as having hit the SAME class in the SAME run; its tip is
  `b1223b4f` and `git diff --name-only main...aw/lane/lc4unl` reports 4 paths, all under `.aw/records/`
  (two `backlog/open/*.backlog.md`, two `plans/pending/*.ipd.md`). SO: replay against `lc4unl`, state plainly
  that it is a 4-path substitute for a 13-path original, and do NOT claim the 13-file measurement was
  reproduced. If no real lane of this shape is resolvable at execution time, say so and fall back to a
  synthetic fixture built from the shape F-1/F-2/F-3 record, labelled as synthetic. A synthetic fixture
  PRESENTED AS the real replay fails V-01.
- The anti-revert control demonstrated FAILING when re-derivation is deliberately widened to include `- Status:`.

## Spec / documentation sync

THE AMENDMENT IS NOW MANDATORY, BECAUSE OQ-01 WAS ANSWERED YES BY THE MAINTAINER ON 2026-09-22 AND E-03 IS
APPROVED. The spec path is declared in `Scope-Paths`. Two things that were true while the answer was pending
are now FALSE and must not be relied on by an executor reading an older copy: stopping at E-02 is no longer a
legitimate completion of this plan (it was, and only while OQ-01 was open), and `Scope-Paths` no longer
omits the spec path. E-01/E-02 still change no contract on their own, so they remain implementable and
committable before the spec edit lands; what changed is that the plan does not COMPLETE there.

THE SPEC TEXT IS HARDER THAN THE AUTHORED VERSION SUGGESTED. Corrected at review: the plan cited only "the spec text that assigns conflict resolution to a
human/serial ordering", but that sentence is a DOCSTRING in `runner_shared.integrate_lane_branch` ("conflict
DETECTION is the gate's job; conflict RESOLUTION is a human/serial ordering"), not spec text. The governing
SPEC rule is in `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` Section 2.1,
and it is a flat prohibition rather than an assignment of responsibility: the `--on-integration-blocked`
ladder "applies ONLY to that transient dirty-overlap refusal. It never applies to a genuine merge conflict, a
stale base, a non-passing combined revalidation, or a scope violation, none of which repetition fixes", with
the guarantee that "no rung ... reclassifies a failure as a deferral". Its 2026-09-21 amendment note restates
the same scope and says "No rule changed". A genuine merge conflict is exactly what `8u6770` hit, so E-03
introduces an automated response to the ONE class the spec says gets none.

THREE OBLIGATIONS FOLLOW, and they are why OQ-01 was correctly blocking until it was answered. FIRST, the executor must declare
`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` in `Scope-Paths` BEFORE
editing it, so both runners announce the declared spec edit before the run starts and reconcile it at
finalize. SECOND, the amendment must be written as a NARROW CARVE-OUT that keeps the existing prohibition
intact for everything else, not as a softening of it: the spec sentence must say that a positively classified
records-only orthogonal-front-matter conflict is re-derived, and that every other conflict remains terminal on
first attempt. THIRD, `merge-refused` must keep meaning what `runner_shared` says it means (the gate measured
the work and REFUSED it), so a re-derived conflict is NOT reported as a refusal that was silently repaired;
it needs its own reported outcome.

WHY THIS IS WORTH THE CONTRACT CHANGE, AND IT IS THE REASON THE MAINTAINER ACCEPTED IT ON 2026-09-22: the
prohibition's stated reason is that "repetition" does not fix a conflict, and that reasoning holds.
Re-derivation is not repetition; it recomputes the intended edit against the settled tree. That distinction is
the entire argument for the carve-out, so write the amendment to turn on it EXPLICITLY: the carve-out is for a
RECOMPUTED edit, not for a retried merge, and the prohibition on retrying a genuine conflict stays exactly as
it reads today. An amendment phrased as "a conflict may be automatically handled when ..." would soften the
prohibition and misstate the approved reasoning; one phrased as "a positively classified records-only
orthogonal-front-matter edit is RE-DERIVED against the settled tree rather than merged, and every other
conflict class remains terminal on first attempt" states it.

## Open questions

### OQ-01: May the integration RE-DERIVE a records-only front-matter edit, or must it only refuse more informatively?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-22 BY THE MAINTAINER (human decision, taken through an interactive prompt that carried the spec-amendment cost and the permanent-records hazard before the choice): YES, the integration MAY re-derive, and E-03 is approved BEHIND E-01's positive classification AND E-04's all-or-nothing rule. That is the recommendation this question already carried, and the maintainer's stated reason is the one recorded below: the failure mode of a classifier-gated re-derivation is a REFUSAL rather than a bad write, so the hazard is bounded, and the recurring manual hand-resolution chore goes away. The carve-out argument was accepted on its merits: spec `25kzda` 2.1's prohibition rests on the premise that REPETITION does not fix a genuine merge conflict, and re-derivation is not repetition (it recomputes the intended edit against the settled tree), so the prohibition's own reasoning does not reach it. CONSEQUENCES THE EXECUTOR NOW OWNS, none of them discretionary: the spec path is DECLARED in `Scope-Paths` as of this resolution (see the Scope-Paths line and the Scope check note), the amendment must be written in the SAME change as a NARROW carve-out leaving a stale base, a scope violation and a combined-red revalidation terminal on first attempt, the allow-list stays exactly `- Work-Kind:` and `- Priority:`, and a re-derived integration gets its own reported outcome rather than being laundered into `integrated` or `merge-refused` (F-11). V-03 fails without the spec diff regardless of how well the code works.
- Carrier-Declined: THIS PLAN IS THE CARRIER AND THE QUESTION GATES ONLY ITS OWN E-03. Both answers are already fully specified here, so no later record is needed either way: a NO lands E-01/E-02 (which change no contract) and the plan completes with E-03 recorded as declined, while a YES executes E-03 behind the spec amendment F-8 requires. Filing a separate carrier would assert outstanding work in a third place while duplicating a decision this plan already holds in one.
  THE ANALYSIS THAT WAS PUT TO THE MAINTAINER IS RETAINED VERBATIM BELOW, because the answer above is only auditable beside the cost the decision was taken against, and a rationale that keeps the outcome while discarding the reasoning loses the expensive half. NOT the executor's call, because it changes a stated division of responsibility: today conflict DETECTION is the gate's and RESOLUTION is a human's. Re-derivation is safe in the narrow proven shape and removes a recurring manual chore, but it means the runner rewrites records content during integration, and a bug there writes wrong metadata into permanent history. RECOMMENDATION: approve E-03 but ONLY behind E-01's positive classification and E-04's all-or-nothing rule, since the failure mode is then a refusal rather than a bad write. If the answer is no, this plan still lands E-01/E-02, which tells the resolver which side's `- Status:` is a stale snapshot, and that is a genuine improvement on its own.
  ADDED AT REVIEW, BECAUSE IT RAISES THE COST OF SAYING YES AND THE MAINTAINER SHOULD SEE IT BEFORE DECIDING (PR-002). The obstacle is NOT only the docstring's division of responsibility; it is a SHIPPED SPEC PROHIBITION. Spec `25kzda` Section 2.1 says the integration ladder "applies ONLY to that transient dirty-overlap refusal. It never applies to a genuine merge conflict, a stale base, a non-passing combined revalidation, or a scope violation, none of which repetition fixes", and guarantees "no rung ... reclassifies a failure as a deferral"; its 2026-09-21 amendment note repeats that scope and states "No rule changed". `8u6770` hit a genuine merge conflict, so approving E-03 means AMENDING AN APPROVED SPEC to carve out one class from a flat prohibition, and that amendment must be declared in `Scope-Paths` and written in the same change. THE ARGUMENT FOR THE CARVE-OUT is that the prohibition's own stated reason is that repetition does not fix these classes, and re-derivation is not repetition: it recomputes the intended edit against the settled tree, which is a different operation with a different failure mode. THE ARGUMENT AGAINST is that the prohibition is currently absolute and therefore easy to audit, while a carve-out makes "is this conflict automatically handled?" depend on a classifier, and a classifier bug writes into permanent records. Both arguments are recorded here so the answer can be given once, with the cost visible.

### OQ-02: Should a bulk-records plan instead be SEQUENCED after the execute items it contends with?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED as a complementary mitigation, not a substitute, and it needs no code here. The scheduler already honors declared edges first (`dependency_depth` is `queue_sort_key`'s first key), so a plan of this shape CAN be ordered last today by declaring `- Item-Dependencies:` on the items it would contend with. That is a per-plan authoring choice, so it belongs in the authoring guidance rather than in this code change; it is also insufficient alone, because a plan can contend with items in a DIFFERENT run (as happened here, where a second driver held ten of the same files), which no intra-queue edge can order.

### OQ-03: Should the 15 plans that reached `executed/` before the backfill ran have the two fields added retroactively?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-22 BY THE MAINTAINER (human decision): NO. Those 15 plans STAY UNLABELLED, by decision rather than by omission. The reason given is that terminal plans are HISTORY: the standing rule against editing a plan in a terminal directory is preserved with no exception carved for it, not even for two non-lifecycle metadata keys, because an exception granted for a harmless-looking key is the precedent that makes the next one arguable. THE CONSEQUENCE IS ACCEPTED, NOT WORKED AROUND: those plans will read as missing `- Work-Kind:` and `- Priority:` forever, so any population-wide report over the plans tree must treat an absent value on a terminal plan as expected rather than as a defect to backfill. NO CARRIER IS FILED, and that is now the final state rather than a pending judgement: filing one would assert outstanding work the maintainer has explicitly declined. This also removes the executor's OQ-03 gate entirely: the answer is not "wait for permission", it is "do not touch an `executed/` plan", which is what the standing rule said anyway.
- Carrier-Declined: DECLINED BY THE MAINTAINER'S ANSWER, not pending it (updated 2026-09-22). The original reasoning was that no carrier could honestly be filed until the question was answered, since filing one would assert that a terminal-directory edit was pending; the answer came back NO, so the alternative that reasoning named has landed: those plans stay unlabelled by decision and there is nothing to carry. The gap stays visible here and in the Under-scope note.
- Historical rationale (superseded by the resolution above): DEFERRED to the maintainer because it collides with a standing rule. `aw ipd set` will not write to a plan in `executed/`, and the repository forbids editing a terminal-directory plan in place, so adding the fields requires either an explicit exception or accepting that those plans stay unlabelled forever. The executor must NOT decide this and must NOT edit any `executed/` plan absent an explicit answer. Reported as a known gap rather than silently closed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the ALLOW-LIST pasted from the code (F-9), plus the classifier run over a REAL conflict set of this shape with its verdict for each file, plus its verdict for FOUR negative cases showing not-this-shape or UNKNOWN: a code-path conflict; a `- Status:`-versus-`- Status:` disagreement; an incoming side touching a non-allow-listed key (use `- Readiness:`, the sharpest case); and a conflict on an unmeasured record type such as `.backlog.md` (F-10).
  - Required evidence: the replay SOURCE named with its size, and labelled real or synthetic. `aw/lane/8u6770` does NOT exist (F-7), so a claim of reproducing the 13-file measurement FAILS this item; `aw/lane/lc4unl` (4 paths) is the sanctioned substitute and must be described as such.
  - Observed evidence: PASS. Allow-list pasted; the REAL original `8u6770` lane replayed (34 paths, all MATCH); all four negative arms pasted. Full evidence below.
    THE ALLOW-LIST, pasted from `runner_shared.REDERIVABLE_FRONT_MATTER_KEYS`:

    ```text
    $ python3 -c "from agent_workflows import runner_shared as r; print(sorted(r.REDERIVABLE_FRONT_MATTER_KEYS)); print(r.REDERIVABLE_RECORD_SUFFIXES)"
    ['Priority', 'Work-Kind']
    ('.ipd.md',)
    ```

    THE REPLAY SOURCE IS THE **REAL ORIGINAL `8u6770` LANE**, NOT THE SANCTIONED SUBSTITUTE AND NOT
    SYNTHETIC, AND F-7 IS PARTLY CORRECTED (see decision `01-kl18sz-D1`). F-7 is right that the BRANCH
    REF is gone, and it is right about `lc4unl` too: measured at execution, `git branch -a` lists 94
    `aw/lane/*` refs and neither `aw/lane/8u6770` nor `aw/lane/lc4unl` is among them, while
    `aw/lane/lc4unl_attempt2` carries NO work (`git merge-base main aw/lane/lc4unl_attempt2` equals its
    own tip `223474b0`, diff 0 paths). What F-7 did not check is that the OBJECTS survive: searching all
    509 dangling commits by subject found the lane's finalize tip `0abc01d9` ("lifecycle(8u6770):
    finalize 8u6770 -> executed"), whose history contains `b6b2afc0` ("records(8u6770): backfill
    Priority and Work-Kind on 57 pending plans by inheritance"). So the replay is the actual incident.

    ```text
    $ git merge-base main 0abc01d9
    c9c03c10b86b80b38e27966aad8db2a5417650d3
    $ git merge-tree --write-tree main 0abc01d9 | grep -c '^CONFLICT'
    34
    ```

    SIZE AND HONEST CAVEAT: 34 conflicting paths, every one a `.aw/records/plans/*.ipd.md`, of which 30
    targets are now in `executed/` and 4 still in `pending/`. This is LARGER than the plan's recorded 13
    because `main` has advanced since 2026-09-22, so it is the same lane measured against a LATER main
    rather than a byte-identical reproduction of that day's measurement. It is NOT a claim to have
    reproduced the 13-file number.

    THE CLASSIFIER OVER THAT REAL SET, verdict per file (all 34 identical, so counted rather than
    pasted 34 times):

    ```text
    REPLAY SOURCE: dangling finalize commit 0abc01d9 of the ORIGINAL aw/lane/8u6770 (REAL, not synthetic)
    merge-base: c9c03c10b86b80b38e27966aad8db2a5417650d3
    conflicting paths from `git merge-tree --write-tree main 0abc01d9`: 34
    VERDICTS: {'records-only-front-matter': 34}
    target in TERMINAL directory: 30
    SET GATE: True | all 34 conflicting path(s) are the proven records-only front-matter shape
    ```

    THE FOUR NEGATIVE CASES, each pasted with the verdict and the reason the code gave:

    ```text
    (a) code-path conflict:
      verdict=not-this-shape
      reason='agent_workflows/runner_shared.py' is not under .aw/records/, so it is not a records edit
    (b) Status-vs-Status disagreement:
      verdict=not-this-shape
      reason=the incoming side CHANGED front-matter key(s) ['Status'] relative to its own base, so it
      asserts a value rather than backfilling a missing one; `- Status:` among them, so this is a real
      lifecycle disagreement
    (c) non-allow-listed key `- Readiness:` (the sharpest case):
      verdict=not-this-shape
      reason=the incoming side added front-matter key(s) ['Readiness'] that are NOT on the re-derivable
      allow-list (['Priority', 'Work-Kind']); a key with lifecycle, gate, identity or attestation
      meaning must never be written by an automated integration
    (d) unmeasured record type .backlog.md:
      verdict=unknown
      reason='.aw/records/backlog/open/...x.backlog.md' is a records file of an UNMEASURED type (only
      .ipd.md has been measured for this shape); its status vocabulary and lifecycle layout are its own,
      so no verdict is claimed
    ```

    Note (d) is UNKNOWN rather than not-this-shape, which is the three-valued contract working: nothing
    here measured what "orthogonal" means for a backlog status enum, so no verdict is claimed.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the actual refusal text pasted for the replayed conflict, showing it names the stale-snapshot trap, the count of already-executed plans, and the CONCRETE safe resolution (keep the target's `- Status:` and directory, keep the incoming orthogonal keys, keep both history lines); contrasted with the generic text produced before the change. Plus evidence the refusal KIND and its terminality are unchanged, since E-02 must change no contract.
  - Observed evidence: PASS. New refusal text pasted from the real 34-path replay, contrasted with the generic pre-change text; kind and terminality proved unchanged. Full evidence below.
    THE NEW SHAPE-SPECIFIC TEXT, produced from the REAL 34-path `8u6770` conflict set (head line plus
    the first of its 34 per-file lines; the rest are identical in shape):

    ```text
    merge-back conflict in 34 records file(s), and it is the RECORDS-ONLY FRONT-MATTER RACE: the
    incoming branch adds only `- Priority:`, `- Work-Kind:` and appends history, while main moved the
    same plans through their lifecycle; THE INCOMING BRANCH HOLDS A STALE LIFECYCLE SNAPSHOT: its
    `- Status:` values were read before those transitions, so TAKING ITS SIDE WOULD REVERT 30 real
    execution(s); SAFE RESOLUTION, per file: keep the TARGET's `- Status:` and its lifecycle directory,
    keep the incoming branch's new field(s), and keep BOTH history lines
      .aw/records/plans/executed/20260908-depblock-01-akzy45-distinguish-not-ready-yet-from-can-never-be-ready-so-a-trans.ipd.md: target `- Status: executed` [TERMINAL directory]; incoming (STALE) `- Status: approved`; re-derivable `- Priority: medium`, `- Work-Kind: bug`
    ```

    THE GENERIC TEXT THE PRE-CHANGE CODE PRODUCED for the SAME conflict, via
    `format_merge_conflict_reason` with the same 34 paths and the same merge stdout (first 400 chars):

    ```text
    merge-back conflict in 34 file(s): .aw/records/plans/executed/20260908-commitguard-02-y9vpvv-add-a-plan-less-aw-commit-and-land-the-ruled-must-wording.ipd.md, .aw/records/plans/executed/20260908-depblock-01-akzy45-distinguish-not-ready-yet-from-can-never-be-ready-so-a-trans.ipd.md, .aw/records/plans/executed/20260908-graduate-01-jxxec8-report-every-existing-plan-for-a-source-before-a-tenth-is-au.i...
    ```

    MEASURED ON THAT GENERIC TEXT, which is the contrast that matters: it states the safe resolution
    **False**, and it counts the executions at risk **False**. It is a list of paths; it does not say
    which side's `- Status:` is stale nor what to do about it, which is precisely the resolver trap.

    THE KIND AND ITS TERMINALITY ARE UNCHANGED, pinned by
    `test_the_E02_refusal_CHANGES_NO_CONTRACT_only_the_message`: a non-re-derived conflict still returns
    `INTEGRATION_REFUSAL_CONFLICT == "merge-refused"`, `classify_integration_refusal` still returns
    False for it, and `decide_integration_deferral(integ_kind="merge-refused", attempts_used=1,
    limit=10)` still yields `deferred=False` with `status="merge-refused"`. So spec `25kzda` 2.1's
    prohibition is untouched by the better message, which is E-02's stated constraint. The E-04 refusal
    replay under V-04 shows this text landing on a real refusal.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: THE SPEC AMENDMENT FIRST (F-8) - the declared spec path in `Scope-Paths` and the diff to `25kzda` Section 2.1 showing a narrow carve-out that leaves the prohibition intact for a stale base, a scope violation and a combined-red revalidation. Absent that diff this item FAILS regardless of how well the code works, because the code would contradict an approved spec.
  - Required evidence: for at least three real plans (one still `pending/`, one now `executed/`, one moved between directories), the resulting front matter pasted showing both new keys present AND the true current `- Status:` preserved, plus `git status` evidence that no plan changed directory as a result of this step.
  - Required evidence: the DISTINCT reported outcome (F-11), showing a re-derived integration is reported as recomputed rather than as a plain `integrated` or as `merge-refused`, with the run-record line pasted.
  - Observed evidence: PASS. Spec `25kzda` Section 2.1a diff pasted (declared path, narrow carve-out); three real plans' front matter pasted with target `- Status:` preserved; zero directory changes; the distinct `merge-rederived` outcome pasted. Full evidence below.
    THE SPEC AMENDMENT FIRST, as F-8 requires. The path is DECLARED in `Scope-Paths`
    (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, third entry) and
    was MODIFIED in this same change. The diff adds a new **Section 2.1a** and one qualifying clause on
    the 2.1 bullet it carves out of. Key lines:

    ```text
    +### 2.1a The records-only front-matter conflict is RE-DERIVED, not retried
    +THE RULE. A positively classified RECORDS-ONLY ORTHOGONAL-FRONT-MATTER conflict is RE-DERIVED
    + against the settled tree rather than merged, and EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON
    + ITS FIRST ATTEMPT. In particular a stale base, a scope violation, and a non-passing combined
    + revalidation are untouched by this section and stay terminal exactly as Section 2.1 requires, as
    + does any genuine merge conflict that does not positively classify.
    ```

    AND THE 2.1 BULLET IS QUALIFIED RATHER THAN WEAKENED (the single-line change to it):

    ```text
    -... it carries its own timeout so no setting of this flag can wait indefinitely.
    +... it carries its own timeout so no setting of this flag can wait indefinitely. This bullet
    + governs the LADDER, which is a RE-ATTEMPT mechanism, and it is unchanged by Section 2.1a: the
    + single conflict class that section carves out is not re-attempted through the ladder or through
    + any other route, and every sentence above continues to hold for it.
    ```

    THE CARVE-OUT IS PHRASED ON THE RECOMPUTED-VERSUS-RETRIED DISTINCTION, as OQ-01's resolution
    requires and NOT as "a conflict may be automatically handled when ...": Section 2.1a's second
    paragraph states "Re-derivation is not repetition. It does not re-attempt the merge, does not consult
    the ladder, does not spend a retry budget, and does not defer anything." The three classes the plan
    names as needing to stay terminal (stale base, scope violation, combined-red) are listed BY NAME in
    THE RULE as untouched, and the 2.1 sentence they live in is left intact.

    THREE REAL PLANS, front matter after re-derivation against the settled tree, showing both new keys
    present AND the true current `- Status:` preserved. The three cover the required cases: one MOVED
    between directories, one still in `pending/`, and (from the same 34-path set) 30 whose target is in
    `executed/`:

    ```text
    [moved  pending/ -> executed/] ...y9vpvv-add-a-plan-less-aw-commit-and-land-the-ruled-must-wording.ipd.md
        - Status: executed   (the TARGET's, preserved; the lane's stale snapshot said `approved`)
        - Id: y9vpvv
        - Priority: high
        - Work-Kind: feature
    [still pending/] ...2s0iym-perform-the-set-wide-honesty-comparison-across-both-children.ipd.md
        - Status: approved          <- the TARGET's, preserved
        - Id: 2s0iym
        - Priority: high
        - Work-Kind: feature
    [executed/, sampled from the live integration replay] ...aaa111-a-plan.ipd.md
        - Status: executed   (the TARGET's, preserved)
        - Work-Kind: bug
        - Priority: medium
    ```

    Asserted mechanically over ALL 34, not just the sampled three: for every verdict,
    `f"- Status: {v.target_status}"` is present in the re-derived text and the incoming (stale) status
    line is absent. BOTH history lines survive in each
    (`test_rederivation_keeps_the_target_status_and_adds_both_keys` pins the lane's
    "status unchanged (no lifecycle transition)" line and the target's own "executed (aw oc run)" line).

    NO PLAN CHANGED DIRECTORY AS A RESULT OF THIS STEP, by construction and by measurement.
    `rederive_front_matter` returns TEXT and performs no IO, so it cannot rename; `apply_records_only_
    rederivation` writes each target's OWN path and issues no `git mv`. Measured on the live end-to-end
    integration replay:

    ```text
    $ git status --short
    (empty)
    $ ls .aw/records/plans/pending/   # the plan is in executed/, and stayed there
    (the pending path does not exist; asserted by `assert not (repo / PENDING).exists()`)
    ```

    And the read-only 34-path replay left THIS lane's own records tree untouched:

    ```text
    $ git status --short -- .aw/records/plans/
    ''
    ```

    THE DISTINCT REPORTED OUTCOME (F-11), from the live `integrate_lane_branch` call:

    ```text
    integrated: True
    kind: merge-rederived
    reason: integration RECOMPUTED rather than merged: re-derived 1 records file(s) against the settled
      tree: wrote `- Priority:`, `- Work-Kind:` and kept every target `- Status:` and lifecycle
      directory unchanged; all 1 conflicting path(s) are the proven records-only front-matter shape
    ```

    And the commit subject it lands on main:

    ```text
    $ git log -1 --format=%s
    integrate(aw oc run): re-derive records-only front matter for lane aaa111 against the settled tree
    ```

    Pinned by `test_the_integration_reports_a_DISTINCT_recomputed_outcome`, which asserts
    `kind == "merge-rederived"`, `kind != INTEGRATION_REFUSAL_CONFLICT`, `kind != "integrated"`, and that
    the reason contains "RECOMPUTED rather than merged". So it is neither laundered into `integrated` nor
    reported as a refusal that did not happen.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: a mixed conflict set (one records-only file plus one code file) shown refusing ENTIRELY, with evidence that nothing was written (clean `git status` and unchanged file digests for both paths).
  - Observed evidence: PASS. A mixed records+code conflict set refuses ENTIRELY: HEAD unmoved, `git status` empty, both sha256 digests unchanged. Full evidence below.
    A MIXED CONFLICT SET driven through the real `integrate_lane_branch` in a throwaway repository: the
    lane backfills `- Work-Kind:`/`- Priority:` on a plan AND edits `mod.py`; main executes the same plan
    (moving it `pending/` -> `executed/` and rewriting `- Status:`) AND edits `mod.py` differently. Both
    paths conflict. The result:

    ```text
    integrated: False kind: merge-refused
    reason:
     merge-back conflict in 2 file(s): .aw/records/plans/executed/20260901-race-01-aaa111-a-plan.ipd.md, mod.py; Auto-merging ...
     CONFLICT (content): Merge conflict in .aw/records/plans/executed/...a-plan.ipd.md
     CONFLICT (content): Merge conflict in mod.py
     merge-back conflict in 1 records file(s), and it is the RECORDS-ONLY FRONT-MATTER RACE: ...
     THE INCOMING BRANCH HOLDS A STALE LIFECYCLE SNAPSHOT: ... WOULD REVERT 1 real execution(s); ...
     NOT re-derived: 1 of 2 conflicting path(s) are NOT the proven records-only front-matter shape, so
     the whole integration refuses rather than half-applying: mod.py [not-this-shape]: 'mod.py' is not
     under .aw/records/, so it is not a records edit
    ```

    NOTHING WAS WRITTEN, on either path:

    ```text
    HEAD unchanged: True
    git status clean: ''
    code digest unchanged: True
    plan digest unchanged: True
    ```

    Note the records file was RECOGNIZED (the refusal even names its safe resolution, which is E-02
    working) and was still NOT written, because E-04's gate is about the SET and not the file. Pinned by
    `test_a_mixed_conflict_set_refuses_ENTIRELY_and_writes_nothing`, which asserts the unchanged HEAD, an
    empty `git status --short`, and identical `sha256` digests for BOTH paths before and after.

    THE GATE IS RE-ASKED AT THE WRITE SITE, not only at the call site:
    `test_apply_RECHECKS_the_set_gate_rather_than_trusting_its_caller` hands
    `apply_records_only_rederivation` a hand-built mixed verdict list and gets
    `(False, "refusing to re-derive: ...")`, so a caller that forgot the gate still cannot half-apply.
    An EMPTY set is also refused (`test_an_empty_conflict_set_is_not_rederivable`), since "every member
    matched" is vacuously true of nothing.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the new test file GREEN after and RED before; the anti-revert control demonstrated FAILING when re-derivation is widened to `- Status:` (paste the failing assertion); the ALLOW-LIST control demonstrated FAILING when widened to a gate or attestation key such as `- Readiness:` (paste it); the unmeasured-type arm returning UNKNOWN; and the suite summary with EVERY failure classified pre-existing or attributable. An absolute-green claim fails this item, since two unrelated failures exist at review HEAD.
  - Observed evidence: PASS. 38 passed after / 35 failed before (source-only revert); both controls demonstrated refusing with the assertions pasted; UNKNOWN arm pasted; bare suite 1 failed / 8605 passed against a 1 failed / 8567 passed baseline, every failure classified. Full evidence below.
    GREEN AFTER:

    ```text
    $ python3 -m pytest tests/test_records_only_lane_rederive.py
    ......................................                                   [100%]
    38 passed in 2.23s
    ```

    RED BEFORE, produced by reverting ONLY the source file (`git stash push -- agent_workflows/runner_shared.py`)
    while keeping the new tests, exactly as required:

    ```text
    $ git stash push -m "kl18sz-fixed-source" -- agent_workflows/runner_shared.py
    Saved working directory and index state On aw/lane/kl18sz: kl18sz-fixed-source
    $ python3 -m pytest tests/test_records_only_lane_rederive.py
    35 failed, 2 passed in 2.37s
    ```

    (The 2 that still pass pre-fix are the two that assert facts about GIT and about the PRE-EXISTING
    refusal contract rather than about new code: `test_git_really_does_conflict_loudly_in_this_shape` and
    `test_the_E02_refusal_CHANGES_NO_CONTRACT_only_the_message`. Both passing before is CORRECT and is
    what makes them premise-pins rather than fix-pins.)

    THE ANTI-REVERT CONTROL DEMONSTRATED FAILING when re-derivation is widened to `- Status:`. MEASURING
    IT CORRECTED THE PLAN'S EXPECTATION (decision `01-kl18sz-D4`): the defence turned out to be DOUBLE,
    and both layers are now pinned rather than one being assumed. Layer one, on the REAL shape, is the
    classifier's clash rule, which refuses BEFORE the allow-list is even consulted:

    ```text
    realistic.verdict == 'not-this-shape'
    realistic.reason contains "DIFFERENT value"
      (target `- Status: executed` vs incoming `- Status: approved`: the two sides hold the key with
       different values, so widening the allow-list alone does not produce a match)
    ```

    Layer two is the load-bearing one, reached via the only shape that evades layer one (a target with no
    `- Status:` line, so the classifier legitimately matches with a widened list). The WRITER refuses, and
    this is the pasted failing assertion:

    ```text
    E   agent_workflows.runner_shared.DriverError: rederive_front_matter: refusing to write
    E   non-allow-listed front-matter key 'Status' (allow-list: ['Priority', 'Work-Kind'])
    ```

    That asymmetry is deliberate and is why the control is evidence rather than decoration: the
    CLASSIFIER accepts an injected `allow_list` so a test can widen it, while the WRITER accepts only the
    shipped `REDERIVABLE_FRONT_MATTER_KEYS`, so no test double and no future caller can widen what
    actually reaches a permanent record.

    THE ALLOW-LIST CONTROL, widened to a gate or attestation key, at BOTH layers.
    `test_a_gate_or_attestation_key_is_never_this_shape` proves the CLASSIFIER refuses each of
    `- Readiness:`, `- Approval:`, `- Blocks-Release:`, `- Item-Dependencies:` and `- Highest E allocated:`;
    `test_the_writer_refuses_every_gate_or_attestation_key_even_if_classified` proves the WRITER refuses
    each of `- Status:`, `- Readiness:`, `- Approval:`, `- Blocks-Release:` EVEN GIVEN A FORGED MATCHING
    VERDICT. The `- Readiness:` case, pasted (the sharpest, since this repository treats a hand-written
    value as a forged attestation the auto-approve predicate reads FIRST):

    ```text
    verdict=not-this-shape
    reason=the incoming side added front-matter key(s) ['Readiness'] that are NOT on the re-derivable
    allow-list (['Priority', 'Work-Kind']); a key with lifecycle, gate, identity or attestation meaning
    must never be written by an automated integration
    ```

    THE UNMEASURED-TYPE ARM RETURNS UNKNOWN (F-10), for `.backlog.md`, `.spec.md` and `.release.md`:

    ```text
    verdict=unknown
    reason='.aw/records/backlog/open/20260901-ccc333-01-ccc333-x.backlog.md' is a records file of an
    UNMEASURED type (only .ipd.md has been measured for this shape); its status vocabulary and lifecycle
    layout are its own, so no verdict is claimed
    ```

    THE SUITE, run BARE per the execution contract, with a baseline taken THE SAME WAY in this worktree
    BEFORE any change (at HEAD `6444056e`):

    ```text
    BASELINE (before the change, HEAD 6444056e):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8567 passed, 3 skipped, 2 xfailed, 3 warnings in 126.58s (0:02:06)

    AFTER the change:
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8605 passed, 3 skipped, 2 xfailed, 3 warnings in 120.69s (0:02:00)
    ```

    NO NEW FAILING NODE IDS. Every failure classified:

    1. `tests/test_turn_bounds.py::...::test_the_permission_policy_by_contrast_IS_isolation_scoped` -
       PRE-EXISTING and UNRELATED, present identically in the baseline. It is the ambient
       `OPENCODE_CONFIG_CONTENT` leak the plan already records: `env -u OPENCODE_CONFIG_CONTENT python3 -m
       pytest tests/test_turn_bounds.py` gives `76 passed`. Not edited (the scope fence forbids it), and
       already carried by backlog `qdxxi9`/`gewvlv`.
    2. `tests/test_orchestrator_retirement.py::RealRepositorySets` - the plan's second expected
       pre-existing failure DID NOT OCCUR in either run here, so there is nothing to classify. Recorded
       because the plan warned to expect it; corpus drift evidently moved it back to green.
    3. `tests/test_runner_shared.py::LaneIntegrationBehaviorTests::test_the_kind_vocabulary_is_UNCHANGED_by_the_extraction`
       - ATTRIBUTABLE TO THIS CHANGE, and FIXED rather than left failing. It asserts the returned kind set
       EQUALS exactly three members, and F-11 requires a fourth. The expected set is now four and remains
       an EQUALITY assertion, so an unreviewed fifth kind still fails; the docstring records why, citing
       spec Section 2.1a and F-11. See decision `01-kl18sz-D2`. `python3 -m pytest
       tests/test_runner_shared.py` -> `230 passed`. NOTE this is an OUT-OF-SCOPE path: `aw check` reports
       `check.scope-drift` on this plan for it, which is the gate working, and it needs a
       `--scope-reason` at finalize.

    The 38-test increase (8567 -> 8605) is this plan's own 38 new tests.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

BOTH OPEN QUESTIONS ARE ANSWERED AS OF 2026-09-22, SO THIS SECTION'S EARLIER STOP INSTRUCTION NO LONGER
APPLIES. The executor implements ALL FIVE E-items: OQ-01 was answered YES by the maintainer, so E-03
re-derivation IS authorized, behind E-01's positive classification and E-04's all-or-nothing rule, and behind
the spec amendment below. Landing E-01/E-02 and stopping is NO LONGER a legitimate completion of this plan; it
was, and only while OQ-01 was open. E-01/E-02 do still change no contract, so they may land first and be
committed before the spec edit, which keeps the resolver-facing trap closed early even if E-03 runs into
trouble. OQ-03 was answered NO: the 15 plans already in `executed/` stay unlabelled BY DECISION, so do NOT
edit any plan in a terminal directory for any reason under this plan, and do not treat their missing
`- Work-Kind:`/`- Priority:` as a gap to close.

E-03 ALSO CARRIES A SPEC OBLIGATION THAT IS NOT DISCRETIONARY (added at review, F-8). Spec `25kzda` Section
2.1 states the integration ladder "never applies to a genuine merge conflict", which is exactly the class
`8u6770` hit, so implementing E-03 without amending that spec would ship code contradicting an approved
contract. That spec path IS NOW DECLARED in `Scope-Paths` (added when OQ-01 was answered, so the runner
announces the declared spec edit before the run starts and the finalize gate reconciles it); amend it in the
same change as a NARROW carve-out that leaves every other conflict class terminal, and say why in the spec-sync
section. V-03 fails without that diff regardless of how well the code works.

THE SPECIFIC HAZARD OF THIS PLAN is that it writes to PERMANENT RECORDS during integration, so E-04's
all-or-nothing rule and E-05's controls are not optional: a wrong write here corrupts history rather than
merely failing a run. TWO CONTROLS, NOT ONE, because `- Status:` is not the only dangerous key: the anti-revert
control stops a plan in a terminal directory acquiring a non-terminal status, and the ALLOW-LIST control stops
the mechanism ever writing a gate or attestation field (`- Readiness:` is the sharpest case, since this
repository treats a hand-written value as a forged attestation that the auto-approve predicate reads first).
An integration that could write either one would be worse than the conflict it resolves.

SCOPE FENCE. Touch ONLY the declared `Scope-Paths`, which now comprise the runner source, the new test file,
and the spec (all three declared, so all three are expected to be modified; a declared-but-unmodified path
needs a `--scope-ack` at finalize). Do NOT edit `tests/test_turn_bounds.py` or `tests/test_orchestrator_retirement.py`,
the two tests already failing at review HEAD for unrelated reasons. If the work genuinely requires a path
outside the fence, MAKE the edit and JUSTIFY it, since `aw ipd finalize` refuses to complete until every
out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

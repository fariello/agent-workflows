# IPD: rename the plan-named review gating predicates to subject-neutral names

- Date: 2026-09-04
- Kind: child
- Concern: After `eyh1fu` makes the review record artifact-neutral, two public predicates keep plan-only names for a record that is no longer plan-only. `review_findings.plan_gating_blocks` (`:758`) and `plan_blocks_dependents` (`:841`) take a `plan_id6` parameter and answer a question that, post-`eyh1fu`, applies equally to a spec: does this artifact's review record carry an unresolved gating finding? A name that says `plan` for a predicate that handles specs misleads the next reader in exactly the way the `- Plan-Id:` FIELD did, which is why the maintainer ruled the rename in rather than leaving it. This plan exists because that rename is a SEPARATE CONCERN from the field change: it alters no behavior at all, and it reaches four modules the field change never touches, two of them the highest-contention files in the repo.
- Scope: Rename `plan_gating_blocks` to a subject-neutral name, DELETE the zero-caller wrapper `plan_blocks_dependents` (maintainer ruling, OQ-01), and update every call site and docstring. BEHAVIOR-PRESERVING: no signature semantics, no call order, no threshold logic, and no message text changes. The deletion is not a behavior change either, because the deleted function has no caller to lose it; that claim is re-verified before the delete rather than assumed. EXCLUDES every part of the record's subject fields, its migration, and the checker's type-directed resolution (`eyh1fu` owns all of it and is this plan's hard prerequisite), excludes any change to what the predicates DECIDE, and excludes renaming the `GatingBlock` type or the `Subject-Id`/`Subject-Type` fields themselves.
- Scope-Paths: agent_workflows/review_findings.py, agent_workflows/check_engine.py, agent_workflows/plan_readiness.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_set_plan.py, tests/test_plan_readiness.py, tests/test_review_findings_cascade.py
- Item-Dependencies: executed:eyh1fu
- Status: approved
- Readiness: go-pending-approval
- Set: revsweep
- Order: 5
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wpomxa
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): OQ-01 RESOLVED by the maintainer, asked interactively: DELETE `plan_blocks_dependents` rather than rename it. Propagated through every dependent statement rather than only the question, because the plan had told the executor the opposite in three places: E-02 now deletes it (and requires RE-VERIFYING the zero-caller fact immediately before deleting, since three other pending plans are editing the modules where a new caller would most likely appear), E-03 notes one of the two docstrings disappears with it, the Scope line now says BEHAVIOR-PRESERVING rather than PURE RENAME, the scope fence's `Do NOT delete` clause became `DO DELETE`, and E-01's baseline covers only the surviving predicate since a deleted function has no behavior to preserve. Also refreshed six stale `both predicates` references. THE MEASUREMENT BEHIND THE RULING, re-verified at review: one line (`return bool(plan_gating_blocks(...))`, `review_findings.py:850`), zero callers anywhere, no direct test, no `__all__` entry, and a docstring that steers callers to the tuple-returning version. ONE CORRECTION recorded so a bad measurement is not trusted twice: an interim note in this conversation claimed tests referenced it; they do not. `aw ipd lint` conforming at `--phase review-finalize` after the edits.

- 2026-09-05 reviewed (aw set): plan-review round 2: APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, three string-reference sites a symbol rename cannot find), PR-002 (MEDIUM, GatingBlock.plan_id6 position), PR-003 (positive verification) all FIXED; D-1, D-2 recorded reversible.

- 2026-09-04 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003 all FIXED, zero deferred, zero open; D-1, D-2 recorded, both reversible. Round 2 at HEAD `9bb47658`, snapshot `f3094173`. `aw ipd lint` conforming at `--phase author` and `--phase review-finalize`. PR-001 (HIGH) is the one that would have bitten: THREE sites name the predicate as a STRING, which a symbol rename cannot find. Two are `mock.patch` dotted paths (`tests/test_plan_readiness.py:736`, `:759`) and mock.patch resolves by getattr at CALL time, so an incomplete rename imports and type-checks cleanly and fails only when those tests run; the third asserts the literal string in each runner's source (`tests/test_review_findings_cascade.py:303`). The plan listed both test modules in Scope-Paths but E-02 spoke only of 'call sites', so an editor's symbol rename would have satisfied it and broken the suite. E-02 now names all three and V-02 demands them. PR-002 (MEDIUM): `GatingBlock.plan_id6` (`:739`) keeps the plan-only word and the plan took no position; E-03 now requires one, defaulting to LEAVE it because renaming a returned record's public attribute is wider than the two functions the ruling named. PR-003 records the positive verification: the five call sites, the zero-caller measurement for `plan_blocks_dependents`, the threshold default, the four positional call sites, and round 1's `doc.plan_id` correction all hold at this HEAD. Review record: `.aw/records/reviews/20260904-revsweep-05-wpomxa-rename-the-plan-named-review-gating-predicates-to-subject-neutral-names.review.md`.

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1 at HEAD `9bb47658`: APPROVE WITH REVISIONS APPLIED; F-1, F-2 both FIXED, zero deferred, zero open. `aw ipd lint` conforming at `--phase author` and again at `--phase review-finalize`. ONE MATERIAL FINDING: the plan's central independence claim was FALSE. It asserted three times that `plan_gating_blocks` never reads the subject field and that the `executed:eyh1fu` edge was mere file serialization; the predicate DOES read it, at `review_findings.py:805` via `doc.plan_id`, populated from `meta["plan-id"]` at `:640`, which is the exact parser field `eyh1fu` E-02 renames. An executor trusting the claim could have renamed around a line about to change. Corrected in F-1, the history and the gate, which now calls the edge LOAD-BEARING. The split remains justified: it rests on separation of CONCERNS (zero-behavior naming versus a release-blocking field change) and on the four extra modules the field change never touches, neither of which the correction affects. VERIFIED WITH NO DEFECT: the five call sites are exactly as claimed, `plan_blocks_dependents` genuinely has zero callers, and the threshold default plus four positional call sites confirm E-01's baseline is the only real guard against a silent semantic change. Review record: `.aw/records/reviews/20260904-revsweep-05-wpomxa-rename-the-plan-named-review-gating-predicates-to-subject-neutral-names.review.md`.

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): EXTRACTED FROM `eyh1fu` at the maintainer's direction after a structural re-review of the plans changed by the 2026-09-04 open-question rulings. The maintainer had ruled (eyh1fu OQ-01) that the rename happen NOW rather than as prose-only, which grew `eyh1fu`'s Scope-Paths from 11 to 15 entries and pulled `oc_runipd.py`, `agy_runipd.py`, `ipd_set_plan.py` and `plan_readiness.py` into a plan whose actual job is the record's subject field. THE SPLIT TEST THE IPD SPEC STATES was then met on two of its three criteria (spans several code regions/files; has independently-executable phases), so the rename is extracted rather than carried. THE INDEPENDENCE CLAIM WAS OVERSTATED AT AUTHORING AND CORRECTED AT REVIEW (F-1): `plan_gating_blocks` DOES read the subject field, at `review_findings.py:805` via `doc.plan_id`, the very parser field `eyh1fu` E-02 renames. The CONCERNS remain separate, which is what justifies the split, but the `executed:eyh1fu` edge is a real code dependency rather than a serialization convenience, and the plan now says so in three places instead of claiming full independence. WHY THIS MATTERS BEYOND TIDINESS: `eyh1fu` removes a RELEASE-BLOCKING blocker that `5slbpi` depends on, and bundling a zero-behavior rename into it meant that blocker-removal could be held up by a merge conflict over function names in the two most contended modules in the repo, where three other pending plans are editing. Separating them lets the blocker land clean. TWO MEASUREMENTS AT AUTHORING, at HEAD `c8a77881`: `plan_gating_blocks` has FIVE call sites (`plan_readiness.py:509`, `agy_runipd.py:1834`, `oc_runipd.py:2847`, `check_engine.py:2070`, `ipd_set_plan.py:489`); `plan_blocks_dependents` has ZERO callers anywhere in the package, so it is public API with no production consumer, which is recorded because it changes the risk profile of renaming it (nothing can break) and raises a separate question this plan does NOT answer (whether it should exist at all).

## Goal

Give the two review gating predicates names that match what they now do, without changing what they do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the rename

- [ ] E-01 Pin the CURRENT behavior of `plan_gating_blocks` before renaming it, so the rename can be proven behavior-free rather than asserted to be. Only that one predicate needs a baseline: `plan_blocks_dependents` is DELETED by E-02 (OQ-01 ruling) and has no caller whose behavior could change.
  A rename is the one change class where "the tests still pass" is weak evidence, because a rename that accidentally swaps an argument or drops the `threshold` default would still satisfy every existing test that passes positionally. So capture, for a fixture with a gating finding and one without: the returned `GatingBlock` tuple contents and order from `plan_gating_blocks`, the boolean from `plan_blocks_dependents`, and the behavior at the default threshold versus an explicit one.
  NOTE `plan_gating_blocks` IS CONSUMED POSITIONALLY BY FOUR OF ITS FIVE CALLERS, so a swapped argument would still satisfy their tests. That makes this baseline the ONLY thing standing between a silent semantic change and a green suite.
  - Depends on: none
  - Expected outcome: a recorded pre-rename baseline for `plan_gating_blocks` covering both threshold paths and the empty/non-empty cases; paste it.
  - Execution state: pending

- [ ] E-02 Rename `plan_gating_blocks` and DELETE `plan_blocks_dependents`, then update all five call sites plus the two test modules.
  MAINTAINER RULING 2026-09-04 (OQ-01), asked interactively: `plan_blocks_dependents` is DELETED, not renamed. It is a one-line wrapper (`return bool(plan_gating_blocks(...))`, `review_findings.py:850`) with ZERO callers anywhere, no direct test, and no `__all__` entry, and its own docstring steers callers to the tuple-returning version instead. Deleting it removes the maintenance and the naming question in one step. Nothing can break, because nothing calls it; that is the whole basis for the ruling, so VERIFY the zero-caller claim again immediately before deleting rather than trusting this plan's measurement.
  CHOOSE A NAME THAT DROPS `plan` WITHOUT INVENTING A NEW VOCABULARY. The record's own new field is `Subject-Id`/`Subject-Type` (`eyh1fu`), so `subject_gating_blocks` keeps one word for one concept across the field and the predicate. Rename the `plan_id6` PARAMETER to match, and keep it POSITIONAL-compatible: four of the five call sites pass positionally, so a keyword-only change would be a behavior change disguised as a rename.
  THE FIVE CALL SITES, measured at HEAD `c8a77881`: `plan_readiness.py:509`, `agy_runipd.py:1834`, `oc_runipd.py:2847`, `check_engine.py:2070`, `ipd_set_plan.py:489`. LOCATE EVERY ONE BY SYMBOL, never by these line numbers: both runners are the highest-contention files in the repo and will have moved.
  DO NOT ADD AN ALIAS. A backward-compatible shim for an internal predicate would leave two names for one function, which is the exact duplication this Set keeps removing, and the repo is pre-release so no external consumer exists.
  TWO SITES REFERENCE THE NAME AS A STRING AND A SYMBOL RENAME WILL NOT FIND THEM (added at review, F-7). `tests/test_plan_readiness.py:736` and `:759` patch the target by dotted path, `mock.patch("agent_workflows.review_findings.plan_gating_blocks", ...)`, which fails at RUNTIME with an AttributeError rather than at import, so a rename that misses them looks fine until those tests run. And `tests/test_review_findings_cascade.py:303` asserts `assertIn("plan_gating_blocks", src)` against each RUNNER'S SOURCE TEXT, so it fails unless the call sites and the assertion are renamed together. Update all three deliberately; do not rely on an editor's symbol rename.
  - Depends on: E-01
  - Expected outcome: `plan_gating_blocks` renamed and its parameter renamed; `plan_blocks_dependents` DELETED with its zero-caller status re-verified first; all five call sites and both test modules updated; no alias left behind; and a grep showing zero remaining references to either old name.
  - Execution state: pending

- [ ] E-03 Correct the DOCSTRINGS and comments that describe these predicates as plan-only, which is the whole point of the rename and the part a mechanical find-and-replace will miss.
  `plan_gating_blocks`'s own docstring says "the answer for a plan with no review artifact at all" (`:761-763`), and the four call sites each carry a comment naming it as the shared predicate (`oc_runipd.py:2834`, `agy_runipd.py:1826`, `check_engine.py:2063`, `ipd_set_plan.py:481`). Update the prose to say ARTIFACT or SUBJECT where it now means either kind, and leave it saying `plan` only where the statement is genuinely plan-specific.
  DECIDE AND STATE WHAT HAPPENS TO `GatingBlock.plan_id6`, the dataclass field these predicates POPULATE (`review_findings.py:739`), which keeps the plan-only word after the rename (added at review, F-8). It is the value an operator sees in a gate message, so leaving it makes the rename visibly half-done, while changing it touches every construction site and any consumer reading the attribute. This plan's default is to LEAVE IT and record why, because it is a public attribute of a returned record and renaming it is a wider change than the two function names the ruling named; if you change it instead, treat it as a third rename with its own before/after evidence. Either way, say which you did rather than leaving it unmentioned.
  NOTE ONE OF THE TWO DOCSTRINGS IS GONE: `plan_blocks_dependents` is DELETED by E-02 (OQ-01 ruling), so only `plan_gating_blocks`'s docstring and the four call-site comments remain to correct. Its "use the tuple-returning version instead" sentence disappears with it, which is consistent: that advice existed to steer callers away from a wrapper that no longer exists.
  DO NOT WEAKEN THE CLAIM THE REMAINING DOCSTRING EXISTS TO MAKE: that an EMPTY tuple means "nothing recorded blocks dependents", the deliberate absent-is-silent design. It is load-bearing and survives the rename unchanged.
  - Depends on: E-02
  - Expected outcome: docstrings and the four call-site comments describe an artifact-neutral predicate; the absent-is-silent and use-the-tuple-to-explain claims are intact; no remaining prose calls the predicate plan-only.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THESE PREDICATES ARE THE ONE SHARED GATE, by design: `oc_runipd.py:2834`, `agy_runipd.py:1826`, `check_engine.py:2063` and `ipd_set_plan.py:481` each carry a comment stating they delegate ENTIRELY to `review_findings.plan_gating_blocks` "so the two hosts cannot diverge". A rename must preserve that single-source property, and must update those comments so the claim still reads true.
- ABSENCE OF A REVIEW IS DELIBERATELY SILENT: an empty tuple is the answer for an artifact with no review record, documented because zero review files existed against hundreds of plans. Nothing here may turn absence into a block.
- `plan_readiness.approval_refusals` CONSUMES THIS PREDICATE and documents that its refusal has NO OVERRIDE. That is why E-01's baseline matters: a semantic slip here blocks approvals unfixably.
- BOTH RUNNER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPO, with three other pending plans editing them; the repo's execution contract requires stopping rather than overwriting a co-worker's in-flight change.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | THE RENAME IS INDEPENDENT OF THE FIELD'S MEANING, BUT NOT OF ITS CODE PATH, and the first draft of this plan overstated it as fully independent. CORRECTED AT REVIEW: `plan_gating_blocks` DOES read the subject field, via `doc.plan_id` at `review_findings.py:805`, where `ReviewDocument.plan_id` (`:187`) is populated from `meta["plan-id"]` (`:640`). `eyh1fu` E-02 renames exactly that parser field, so it MUST update `:805` as part of its own work. What remains true, and is the real basis for the split: this plan changes no LOGIC and the rename needs no knowledge of what the field is called, since the predicate matches an id6 against whatever the parser exposes. So the `executed:eyh1fu` edge is load-bearing rather than merely a serialization convenience, and this plan must be executed against the POST-`eyh1fu` code. | `review_findings.py:805` (`if (doc.plan_id or "").strip() != wanted`), field at `:187`, populated at `:640`; `eyh1fu` E-02 owns the writer/parser change |
| F-2 | FIVE CALL SITES, FOUR OF THEM OUTSIDE `eyh1fu`'s ORIGINAL FENCE. This is the measured basis for the split: `eyh1fu`'s Scope-Paths went 11 -> 15 solely to accommodate the rename. | `plan_readiness.py:509`, `agy_runipd.py:1834`, `oc_runipd.py:2847`, `check_engine.py:2070`, `ipd_set_plan.py:489`, measured at HEAD `c8a77881` |
| F-3 | `plan_blocks_dependents` HAS ZERO CALLERS anywhere in the package: one line at `review_findings.py:841-850`, called by nothing, with no direct test and no `__all__` entry. MAINTAINER RULING 2026-09-04 (OQ-01): therefore DELETE it rather than rename it. Re-measured at review, correcting an interim claim that tests referenced it (they do not; the only references were prose). | `grep -rn "plan_blocks_dependents"` over `agent_workflows/` and `tests/` returns the definition only; body is `return bool(plan_gating_blocks(repo_root, plan_id6, threshold))` at `:850` |
| F-4 | FOUR CALL SITES PASS POSITIONALLY, so renaming the `plan_id6` parameter is safe for them, but making it keyword-only would NOT be a pure rename. Recorded because "rename the parameter too" is the natural instinct and the unsafe version of it is one keystroke away. | `_rf.plan_gating_blocks(repo, dep)` at `oc_runipd.py:2847` and `agy_runipd.py:1834`; `(repo_root, dep_id6, threshold)` at `check_engine.py:2070`; `(_repo_root_for_plans_dir(plans_dir), plan_id6)` at `ipd_set_plan.py:489` |
| F-5 | A GREEN SUITE IS WEAK EVIDENCE FOR A RENAME, which is why E-01 exists. A rename that swapped an argument or dropped the `threshold` default would still pass every positional call site's tests. Combined with F-3 (one predicate has no production caller), the characterization baseline is the only real guard. | `threshold: Optional[str] = None` default at `review_findings.py:759`; four positional call sites (F-4) |
| F-6 | THE DOCSTRINGS ARE PART OF THE DELIVERABLE, not decoration: the predicate's own text says "the answer for a plan with no review artifact", and four call sites carry comments asserting the single-shared-predicate property. A find-and-replace on the symbol alone would leave prose that still calls it plan-only, reproducing in comments the exact misleading-name problem the rename fixes. | `review_findings.py:761-763`; `oc_runipd.py:2834`, `agy_runipd.py:1826`, `check_engine.py:2063`, `ipd_set_plan.py:481` |
| F-7 | **TWO SITES NAME THE PREDICATE AS A STRING, SO A SYMBOL RENAME CANNOT FIND THEM.** `tests/test_plan_readiness.py:736` and `:759` patch it by dotted path via `mock.patch`, which fails at RUNTIME (AttributeError) rather than at import, and `tests/test_review_findings_cascade.py:303` asserts the literal string `"plan_gating_blocks"` appears in each RUNNER'S source. The first class of miss is the dangerous one: an incomplete rename type-checks and imports cleanly, then breaks only when those tests execute. | `tests/test_plan_readiness.py:736`, `:759` (`mock.patch("agent_workflows.review_findings.plan_gating_blocks")`); `tests/test_review_findings_cascade.py:296`, `:303` (`assertIn("plan_gating_blocks", src)`) |
| F-8 | `GatingBlock.plan_id6` KEEPS THE PLAN-ONLY WORD after the rename, and it is the field these predicates POPULATE and an operator reads in a gate message, so the rename is visibly half-done unless the plan states a position. Renaming it is wider than the ruling (every construction site plus any attribute consumer), which is why the recorded default is to leave it deliberately rather than silently. | `review_findings.py:739` (`plan_id6: str` on the `GatingBlock` record); populated at `:812` and `:829` |

## Proposed changes (ordered, validatable)

1. Characterization baseline for `plan_gating_blocks`, both threshold paths, empty and non-empty (E-01).
2. Rename `plan_gating_blocks` and its parameter, DELETE the zero-caller `plan_blocks_dependents`, update all five call sites and two test modules, no alias (E-02).
3. Correct the docstrings and the four call-site comments to artifact-neutral prose, preserving the two load-bearing claims (E-03).

## Deferred / out of scope (with reason)

- EVERYTHING ABOUT THE RECORD'S SUBJECT FIELDS: `Subject-Id`/`Subject-Type`, the corpus migration, the type-directed dangling check, and `_review_index`. All owned by `eyh1fu`, which is this plan's hard prerequisite.
- (RESOLVED, no longer deferred) WHETHER `plan_blocks_dependents` SHOULD EXIST: the maintainer ruled on 2026-09-04 that it is DELETED (OQ-01), so E-02 deletes it. It is recorded here rather than removed from the list so the earlier deferral is visibly closed rather than silently dropped.
- ANY CHANGE TO WHAT THE PREDICATES DECIDE: the threshold semantics, the three failure modes, the deterministic ordering, and the absent-is-silent rule are all unchanged.
- RENAMING `GatingBlock` OR ANY OTHER TYPE. The ruling named two functions; widening to the type would pull in more call sites for no additional clarity.
- THE `aw att` GATE-REF DISPLAY and anything else in the attention board. Unrelated surface.

## Scope check

- Over-scope: none. Every edit renames one of the two named predicates, updates one of its call sites, or corrects prose describing it.
- Not under-scope any more on this point: `plan_blocks_dependents` is DELETED (maintainer ruling, OQ-01), so the plan no longer carries a renamed-but-unused predicate. The deletion is in scope precisely because the code is already open for the rename.
- Under-scope: this plan delivers NO behavior change and no user-visible capability. That is the point, and it is why it was extracted from a plan that does deliver one.

## Required tests / validation

- E-01's characterization baseline, captured BEFORE the rename and reproduced identically after. This is the load-bearing evidence, because a green suite alone would also pass for a rename that silently changed an argument (F-5).
- Proof that `plan_blocks_dependents` had ZERO callers at the moment of deletion, re-measured rather than quoted from this plan, plus proof it is gone afterwards.
- A grep proving zero remaining references to either old name, in code, tests, and comments, INCLUDING the two string-reference sites a symbol rename cannot find (F-7): the `mock.patch` dotted paths and the `assertIn("plan_gating_blocks", src)` source assertion.
- An explicit statement of what happened to `GatingBlock.plan_id6` (F-8): left as-is with the reason, or renamed as a third deliberate rename with its own evidence.
- No alias or compatibility shim left behind.
- The parameter remains POSITIONALLY compatible; four call sites depend on it (F-4).
- Both test modules green: `tests/test_plan_readiness.py`, `tests/test_review_findings_cascade.py`.
- The two load-bearing docstring claims still present: absent-is-silent, and use-the-tuple-predicate-to-explain-why.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- This plan implements the maintainer's 2026-09-04 ruling on `eyh1fu` OQ-01. It changes no spec text; spec `6m4kow` R-01..R-05 describe the field, not these names.
- If `.aw/records/reviews/README.md` or any doc names these predicates, update it; otherwise state N/A with the paths checked.
- No user-facing behavior changes, so no CHANGELOG entry is warranted; say so explicitly rather than leaving it ambiguous.

## Open questions

### OQ-01: Should `plan_blocks_dependents` be deleted instead of renamed, given it has zero callers?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-04 by the maintainer, asked interactively: DELETE it. E-02 now deletes rather than renames it, E-03 notes that one of the two docstrings disappears with it, and the Scope line records that the plan is behavior-preserving rather than a pure rename. THE EVIDENCE THAT MADE DELETION THE CHEAP ANSWER, re-measured at review: it is one line (`return bool(plan_gating_blocks(...))`, `review_findings.py:850`), it has ZERO callers anywhere in the package, it has NO direct test, it is not in any `__all__`, and its own docstring steers callers to the tuple-returning version so the operator can be told why. So it is a shortcut nobody took, and keeping it would have meant renaming and re-documenting surface with no consumer. ONE CORRECTION TO AN EARLIER REPORT, recorded so the measurement is not trusted twice: an interim note in this conversation said tests referenced it; they do not, and the only references were in prose. THE ONE OBLIGATION THE RULING CARRIES: nothing can break only while the zero-caller fact holds, so E-02 requires re-verifying it immediately before deleting rather than relying on this plan's measurement, since three other pending plans are editing the modules that would be the likeliest place a new caller appears.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the pre-rename baseline for `plan_gating_blocks`, covering a fixture WITH a gating finding and one WITHOUT, at the DEFAULT threshold and at an explicit one, showing the returned tuple contents and order. State plainly that this baseline exists because a green suite cannot distinguish a pure rename from one that swapped an argument or dropped the threshold default (F-5), and that `plan_blocks_dependents` has no production caller to protect it (F-3).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the post-rename baseline and show it is IDENTICAL to V-01's, which is this plan's central claim. Paste a grep returning ZERO hits for `plan_gating_blocks` and `plan_blocks_dependents` across code, tests, and comments, plus the before-grep showing the five call sites. Paste evidence NO alias was added. Paste the new signature showing the parameter is still positionally compatible, and confirm all four positional call sites still pass positionally. Paste the re-measured zero-caller grep for `plan_blocks_dependents` taken IMMEDIATELY BEFORE deleting it, and the post-delete grep showing it gone; a deletion justified only by this plan's earlier measurement does not satisfy this item, since three other pending plans are editing the modules where a new caller would most likely appear. Paste the three STRING-REFERENCE sites updated (F-7): both `mock.patch` dotted paths and the `assertIn` source assertion, since a symbol rename cannot find them and the `mock.patch` failure surfaces only at test RUNTIME.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the updated docstring for each predicate and the four updated call-site comments, showing none still describes an artifact-neutral predicate as plan-only. Paste the two load-bearing claims still intact verbatim: that an empty tuple means nothing recorded blocks dependents, and that a caller needing to explain WHY must use the tuple-returning predicate. STATE what you did with `GatingBlock.plan_id6` (F-8) and why. Then both test modules, `aw check all` no-worsening against your own baseline, and the bare full suite with counts compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 3 E-leaves in one task group, one concern: the review gating surface stops saying `plan` for something that is no longer plan-only, with zero behavior change. That now means renaming one predicate and deleting a zero-caller wrapper (maintainer ruling, OQ-01), which is the same concern and not two. E-01 is separate from E-02 because a rename's only real evidence is a before/after behavioral baseline, and capturing it after the edit would be worthless. E-03 is separate from E-02 because the symbol rename is mechanical while the prose correction is judgement about which sentences are genuinely plan-specific, and folding them would let a find-and-replace pass as complete while leaving comments that still call the predicate plan-only (F-6).

Open questions: OQ-01 (delete rather than rename the zero-caller predicate) is non-blocking, with the ruling's answer implemented and the measurement recorded for a follow-up. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It has one hard prerequisite, `- Item-Dependencies: executed:eyh1fu`, and that edge is LOAD-BEARING, not merely a scheduling convenience (corrected at review, F-1): `plan_gating_blocks` reads the subject field through `doc.plan_id` (`review_findings.py:805`), which is precisely the parser field `eyh1fu` E-02 renames. Execute this plan against the POST-`eyh1fu` code and re-read the predicate body before renaming, because the line you are renaming around will have changed. Both plans also edit `review_findings.py` and `check_engine.py`, so they must not run concurrently in any case.

Scope fence: touch ONLY the files in Scope-Paths. Do NOT change what the predicates decide: threshold semantics, the three failure modes, deterministic ordering, and the absent-is-silent rule all stay exactly as they are. Do NOT add an alias or compatibility shim. Do NOT make the renamed parameter keyword-only. DO DELETE `plan_blocks_dependents` (maintainer ruling 2026-09-04, OQ-01), but re-verify its zero-caller status immediately before doing so rather than trusting this plan's measurement. Do NOT rename `GatingBlock` or any other type. Do NOT touch the record's subject fields, its migration, or `_review_index` (`eyh1fu` owns them). Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-02's proof that the post-rename baseline is IDENTICAL to the pre-rename one, because "the tests pass" is exactly what a rename with a swapped argument would also report (F-5). Do NOT describe this plan as delivering any capability: it delivers naming clarity and nothing else, which is why it was extracted from `eyh1fu` rather than carried inside it.

Execution contract: RE-READ `review_findings.py` and every call site immediately before editing and locate each BY SYMBOL, never by the line numbers in this plan: `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in the repo and three other pending plans declare them. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with the rename, STOP and report rather than overwriting: this plan delivers no behavior, so it must never win a race against work that does.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.

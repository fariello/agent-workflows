# IPD: Key the begin receipt on each E/V item's whole action block, not its first line

- Date: 2026-09-28
- Kind: child
- Concern: `ipd_lifecycle.frozen_region_digest` is the begin receipt's validity key, and it is blind to every CONTINUATION line of an E or V item, so a receipt minted against one requirement stays valid after that requirement is rewritten.
- Scope: widen the frozen-region requirement extraction from a leaf's opening line to its whole action block, reusing the already-shipped block rule rather than forking a third definition; accept the resulting one-time receipt invalidation deliberately and prove the recovery path; amend the spec sentence that still describes the superseded whole-file key.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_ipd_lifecycle_cli.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 168p5j
- Blocks-Release: next
- Set: 168p5j
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: qurgra

## Workflow history

- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-306. The defect is real, serious and reproduced exactly at review: the E-item continuation rewrite leaves `frozen_region_digest` at `d6bbbc732bcdbdcb` unchanged with `receipt_is_current` True, F-02's V-item case is identical, and F-03's probe digest correctly DIFFERS. F-01 through F-09 were each re-measured independently and all nine hold; the load-bearing `xmqv5l` no-op invariant was re-run over the corpus at `unchanged=857 MOVED=0`. FIXED A LIVE `aw check` ERROR ON THIS PLAN (PR-301, BLOCKER): all five deferred rows plus OQ-01 named no durable carrier, so `check.ipd-uncarried-obligation` fired at `error` with six uncarried obligations that would have vanished from `aw attention` the moment this plan reached `executed`; each row now carries `Carrier-Declined:` and OQ-01 is resolved, taking the rule to zero drifts and the repository error count 3 -> 2. Also corrected: three Findings whose live-population or machine-dependent counts were asserted as bars rather than context (F-04/F-05/F-08, re-measured: 841 -> 857 files, import absolutes shifted while the ordering held), V-01's comparison which becomes a tautology after E-02 unless the pre-change output is captured first, and a note on F-07 recording that `finalize_refusal_is_retryable` needs the summary line (review briefly misread a true claim as false). Record: `.aw/records/reviews/20260928-168p5j-01-qurgra-key-the-begin-receipt-on-each-e-v-item-s-whole-action-.review.md`.
- 2026-09-28 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-28 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): authored from backlog `168p5j`; measurements taken in lane `168p5j` against this worktree.

## Goal

Make the begin receipt's validity key cover what an E or V item actually asks for. Today `frozen_region_digest` hashes only each leaf's OPENING line, so rewriting an item's continuation lines - which is how an author actually changes what an item demands - leaves the digest byte-identical and a stale receipt keeps authorizing execution of a plan the gate never approved. This plan widens the extraction to the whole action block, reusing the block rule `runner_shared.e_item_action_blocks` already ships, and settles the migration the widening forces.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one block rule, shared

- [ ] E-01 Move the action-block extraction into `ipd_lint` as a public `leaf_action_blocks(text, leaves)` helper (name it beside `parse`, which already owns what a leaf IS), carrying the termination rule `runner_shared.e_item_action_blocks` already implements verbatim: anchor on `Leaf.line`, then read forward and stop at a blank line, at the next leaf (`- [`), at a heading (`#`), at the first `_SUBFIELD_RE` match, or at any non-indented line.
  WHY `ipd_lint` AND NOT `runner_shared`, since the existing copy lives there. `ipd_lint` already owns `Leaf`, `_LEAF_RE` and `_SUBFIELD_RE`, so the rule for "where does a leaf's action END" belongs beside the rule for "where does it BEGIN"; and `ipd_lifecycle` must not import `runner_shared` at module scope for this. Measured in this lane: importing `runner_shared` costs 44.5ms of import time against `ipd_lint`'s 28.1ms, and `ipd_lint` imports `runner_shared` only lazily inside one function (`ipd_lint.py`, the `child_table_rows` caller), so putting a lifecycle-gate dependency on the larger module would invert the existing direction.
  GENERALIZE THE SIGNATURE TO ANY LEAF LIST. The shipped copy hardcodes `doc.exec_leaves` and `kind != "E"`, but this defect affects V-items too (proven in Findings F-02), so the helper takes the leaf list and the caller selects the kind.
  - Depends on: none
  - Expected outcome: `ipd_lint.leaf_action_blocks` exists and, given a plan's text plus its E leaves, returns exactly what `runner_shared.e_item_action_blocks` returns for the same input.
  - Execution state: pending

- [ ] E-02 Re-point `runner_shared.e_item_action_blocks` at `ipd_lint.leaf_action_blocks` so it becomes a thin kind-filtering wrapper and the duplicated loop is deleted, keeping its name, its signature and its return type unchanged because `probe_cache_payload` and the orchestrator probe excerpt both call it.
  ITS DOCSTRING MUST KEEP ITS OWN MEASUREMENTS AND GAIN THE CROSS-REFERENCE. The existing prose records the 58-percent loss and the `wfjsp4` 10-percent case, which is the evidence for the rule; it must now also say that the rule itself lives in `ipd_lint` and that `ipd_lifecycle`'s frozen digest consumes the same definition, so the next reader does not fork a fourth copy.
  - Depends on: E-01
  - Expected outcome: `runner_shared` contains no second copy of the termination rule, and `probe_cache_digest` is byte-identical to its pre-change value for every plan in the corpus.
  - Execution state: pending

### Task group 2: the gate reads the whole block

- [ ] E-03 Change `ipd_lifecycle._requirements_from_plan` to build both the `must` and the `validation` categories from `ipd_lint.leaf_action_blocks` instead of from `Leaf.text`, so each category carries every item's whole action block.
  BOTH CATEGORIES, NOT ONLY `must`. The backlog item names `must`, but the same truncation applies to `validation`: measured in this lane, rewriting a V-item's continuation line from "AND ALSO accept a zero-test run as a pass." to "AND ALSO accept an empty evidence block as a pass." also left the digest IDENTICAL. Fixing only E-items would leave a validation requirement rewritable under a live receipt, which is the same defect in the category that decides whether the work was verified.
  KEEP THE EMPTY-ITEM FILTER. The current code drops a leaf whose `text.strip()` is empty; the block builder already returns nothing for an all-empty block, so the filter is preserved by construction rather than by a second condition.
  - Depends on: E-01
  - Expected outcome: `_requirements_from_plan(text)["must"]` and `["validation"]` each contain continuation prose, and the E-item continuation rewrite in F-01 moves `frozen_region_digest`.
  - Execution state: pending

- [ ] E-04 Rewrite the now-false sentences in `frozen_region_digest`'s docstring, which currently ASSERT the truncation as if it were the mechanism: it says `Leaf.text` "is the action text alone, and `_requirements_from_plan` reads only `.text`". Replace that with the block rule, keep the structural-exclusion paragraph (checkbox marks and indented `- Key: value` sub-fields are still excluded, and that is still what makes a conforming self-execution a no-op), and state the property the digest NOW has rather than the one it claimed.
  RECORD THE DEFECT, NOT ONLY THE FIX. The docstring's "changing ... an E/V requirement line DOES invalidate the receipt" clause was FALSE for a continuation line from the day it was written, and the same paragraph is what a future reader will trust; say that it was false, cite backlog `168p5j`, and give the reproduction digest so the claim is checkable rather than asserted.
  - Depends on: E-03
  - Expected outcome: no sentence in `ipd_lifecycle` describes the digest as first-line-only, and the docstring names `168p5j` and the block rule's home.
  - Execution state: pending

### Task group 3: the migration, which is the real work

- [ ] E-05 Take the ONE-TIME INVALIDATION deliberately rather than versioning the digest, and record the decision plus its evidence in `frozen_region_digest`'s docstring and in this plan's Findings.
  THE DECISION, stated so a reviewer can dispute it: widening the payload changes every key, so every already-minted v2 receipt goes stale at once. That is accepted, and NOT worked around with a dual-digest or a `digest_version` field, for four measured reasons. FIRST, a stale receipt REFUSES, which is the safe direction: `receipt_is_current` returns False, `finalize_precheck` emits `FINDING_RECEIPT_STALE`, and nothing is cleared. SECOND, the blast radius is three receipts, not twenty-four: of the 24 receipts in this checkout's `.aw/state/ipd-lifecycle/`, 21 are schema v1 carrying no `frozen_region_digest` at all and are already bound to the legacy whole-file rule in `receipt_is_current`, which this change does not touch. THIRD, all three v2 receipts are already DEAD by the repository's own liveness test: each one's recorded `plan_path` points into `.aw/records/plans/pending/` and none of those files exists there any more (`63425h` is now in `executed/`, `e32j35` and `xts8ux` in `superseded/`), so `check_engine._receipt_is_live` rejects all three as TERMINAL PLAN regardless of this change. FOURTH, the refusal is ANSWERABLE rather than terminal: measured in this lane, the finding a rule-change staleness produces is the no-scope-delta contract-rewrite string, and `runner_shared.finalize_refusal_is_retryable` returns True for it, so the runner hands it back to the agent to justify or re-`begin` instead of stranding work.
  A VERSIONED DIGEST WOULD BE WORSE HERE, which is why it is refused and not merely skipped: it would require keeping the first-line-only payload builder alive as a second reachable definition in order to validate old receipts under the old rule, i.e. preserving the defective extraction inside the safety gate indefinitely, and `_frozen_region_payload`'s own docstring already records why a second copy of that literal is the failure mode to avoid.
  - Depends on: E-03
  - Expected outcome: the accepted-invalidation decision, its four reasons and the refused alternative are written in the code that implements it, with the 24/21/3 counts and the three plan locations cited.
  - Execution state: pending

- [ ] E-06 Add regression tests to `tests/test_ipd_lifecycle_cli.py` pinning the fixed property and the invariant it must not break, extending the existing `test_receipt_invalidation_and_persistence` shape rather than inventing a parallel fixture.
  FOUR PINS, and the last two are what stop the fix causing the `xmqv5l` regression it inherits the risk of. (a) An E-item CONTINUATION-line rewrite makes `receipt_is_current` False. (b) A V-item continuation-line rewrite makes it False. (c) A full conforming self-execution - tick every `- [ ] E-NN`/`V-NN` to `[x]`, set `Execution state: performed`, fill `Observed evidence:` and `Result: pass`, append a `## Workflow history` line - leaves it True. (d) A trailing prose edit outside any item leaves it True.
  PIN (c) IS THE LOAD-BEARING ONE. `frozen_region_digest` exists BECAUSE the whole-file key "refused every self-finalizing run", and widening the payload is exactly the direction that re-opens that. Pre-verified in this lane before writing this plan: the widened extraction is UNCHANGED by simulated conforming execution edits across all 841 `.ipd.md` files in `.aw/records/plans/`, 0 moved.
  - Depends on: E-03
  - Expected outcome: four new assertions exist and fail against the pre-change extraction for (a) and (b) while passing for (c) and (d).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The extraction rule already exists once, in `runner_shared.e_item_action_blocks`, landed by orchprobe-03 (`m7gvuz`) for the probe cache. The backlog item's instruction is explicit that this plan must REUSE it rather than "forking a third definition of 'where does an action end'", so this plan relocates the single definition instead of copying it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `_frozen_region_payload` is deliberately the ONLY construction of the digest payload, because `frozen_region_comparison` must reproduce it with the receipt's stored scope substituted in. Any change to what the payload contains therefore flows into the additive-widening substitution test automatically, and must not be implemented by editing two call sites.
- Receipts live under the CHECKOUT's control root via `ipd_lifecycle.checkout_control_root`, not the lane's, so a lane sees the same receipt store as the driver (backlog `dh0uno`). The migration counts in E-05 were read through `receipt_dir`, not by composing a path.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The defect reproduces exactly as filed. Rewriting an E-item's continuation line leaves `frozen_region_digest` byte-identical, and `receipt_is_current` returns True for the rewritten plan. | In-lane, with the real `H_EXECUTION`/`H_VALIDATION_CHILD` headings: base and rewritten digests both `d6bbbc732bcdbdcb...`; `receipt_is_current` -> `True`. `_requirements_from_plan(base)["must"]` is `['E-01 Do the safe thing.']` while `e_item_action_blocks` returns the whole block including "AND ALSO delete the production database as part of it." |
| F-02 | The defect is NOT confined to E-items. A V-item continuation rewrite is equally invisible. | Same fixture: rewriting the V-01 continuation from "AND ALSO accept a zero-test run as a pass." to "AND ALSO accept an empty evidence block as a pass." also yields `d6bbbc732bcdbdcb...`, IDENTICAL. `_requirements_from_plan(base)["validation"]` is `['V-01 validates E-01 Check it.']`. This widens the fix beyond the backlog item's `must`-only phrasing. |
| F-03 | The probe path is already fixed, which both confirms the rule and bounds this plan's scope. | Same fixture: `probe_cache_digest` DIFFERS across the E-rewrite (`dc04bdf557750a3e...` -> `d8fee5f0dba349d0...`). So `e_item_action_blocks` is the correct rule and needs no redesign, only re-homing. |
| F-04 | Scale, measured across the whole tracked plan corpus rather than the ten-orchestrator sample the backlog item cites. THE PROPERTY, which is what the plan rests on, is that first-line extraction misses a LARGE MAJORITY of E-item requirement prose and a substantial minority of all requirement prose; the counts below are the measurement that established it and are CONTEXT, not the bar. The corpus is a LIVE population and the counts drift as plans land: re-derive them at execution time (V-06) rather than asserting these. | At authoring: 841 `.ipd.md` files under `.aw/records/plans/`; E-items 2,274,408 of 4,105,073 block characters (55.4%); V-items 78,136 of 80,544 (97.0%); combined 2,352,544 of 4,185,617, so 43.8% invisible. RE-MEASURED AT REVIEW on 2026-09-28: 857 files; E-items 2,349,464 of 4,216,722 (55.7%); V-items 79,675 of 82,083 (97.1%); combined 2,429,139 of 4,298,805, so 43.5% invisible. The percentages are stable to within 0.3 points; only the file count moved (841 -> 857), which is the corpus growing. |
| F-05 | The fix does not re-open `xmqv5l` (the "stale on every correct execution" regression the frozen digest exists to fix). THE PROPERTY IS ZERO MOVERS, and that is the bar; the file count is context and must be re-derived at execution time. | Simulated conforming execution edits (tick `[ ]`->`[x]` on every E/V row, `Execution state: performed`, `Observed evidence:` filled, `Result: pass`, appended history line): at authoring, widened extraction UNCHANGED on 841 of 841, MOVED on 0. RE-RUN INDEPENDENTLY AT REVIEW against the same simulation over the now-857-file corpus: `unchanged=857 MOVED=0 skipped=0`. So the invariant holds on a corpus 16 files larger than the one it was authored against. |
| F-06 | The migration cost is three receipts, and all three are already dead. | `receipt_dir` resolves to the shared checkout root and holds 24 receipts. 21 are `schema_version: 1` with no `frozen_region_digest` (unaffected: they take the legacy whole-file branch). The 3 v2 receipts are `63425h`, `e32j35`, `xts8ux`; every one's recorded `plan_path` is under `plans/pending/` and no such file exists there now (`63425h` -> `executed/`, `e32j35` -> `superseded/`, `xts8ux` -> `superseded/`), so `check_engine._receipt_is_live` already rejects all three as terminal. |
| F-07 | A staleness caused purely by the rule change is answerable, not terminal. NOTE FOR THE EXECUTOR, added at review: `finalize_refusal_is_retryable` requires the SUMMARY LINE as well as the finding, because its Arm 2 gates on `runner_shared.RETRYABLE_STALE_RECEIPT_SUMMARY` (`"is STALE: the plan content changed since begin"`) being present before it inspects findings at all. Passing the finding string ALONE returns False. So any validation of this claim must compose the full refusal message, summary included, or it will appear to disprove a true claim. | Simulating the widened rule against a receipt minted under the narrow one with the plan UNTOUCHED: `receipt_is_current` -> False; `frozen_region_comparison` -> `added=() removed=() non_scope_identical=False eligible=True`; `widening_is_acceptable` -> False; so `finalize_precheck`'s no-scope-delta branch composes `"Scope-Paths unchanged but " + FINDING_CONTRACT_REWRITE.replace("also changed", "changed") + " of the reviewed plan"`, and `runner_shared.finalize_refusal_is_retryable` returns True for the composed message. VERIFIED AT REVIEW by reading `finalize_precheck`'s emitting branch, reconstructing that exact string (`Scope-Paths unchanged but a frozen REQUIREMENT changed, so this is a contract rewrite of the reviewed plan`), and calling the predicate on summary-plus-findings -> `True`; the same predicate on the finding alone -> `False`, which is the trap this note records. The allow-list in Arm 2 names `FINDING_CONTRACT_REWRITE` and its `also changed`->`changed` variant explicitly, so the acceptance is deliberate rather than incidental. |
| F-08 | Module direction, settled by measurement rather than taste. THE PROPERTY is the ORDERING (`ipd_lint` is the cheaper module and does not depend on `runner_shared` at module scope), not the absolute microsecond figures, which vary per machine and per warm/cold cache. | At authoring, `python3 -X importtime`: `agent_workflows.ipd_lint` 28,146us cumulative, `agent_workflows.runner_shared` 44,476us. RE-MEASURED AT REVIEW on the same tree: `ipd_lint` 92,064us cumulative, `runner_shared` 103,585us - DIFFERENT ABSOLUTES (a colder cache), SAME ORDERING, which is why the property and not the number is what this finding claims. Also re-verified structurally, which does not vary: `ipd_lint` has no module-scope `runner_shared` import (exactly one lazy in-function occurrence) and already defines `Leaf`, `_LEAF_RE` and `_SUBFIELD_RE` (all three present). So the rule belongs in `ipd_lint`, and `ipd_lifecycle` gains no dependency on the larger module. |
| F-09 | The spec sentence describing the receipt's key is stale independently of this change, and this plan must not leave it contradicting the code. | `ipd-structure-and-linting` Section 11 still says the receipt is "invalidated only by a change to the plan's own content digest". That has been false since `rchpms` re-keyed it onto the frozen region; after this plan the frozen region also covers continuation lines, so the sentence is wrong twice. |

## Proposed changes (ordered, validatable)

1. `ipd_lint`: add `leaf_action_blocks(text, leaves)` carrying the single termination rule, generalized over any leaf list rather than hardcoding E-items (E-01).
2. `runner_shared`: reduce `e_item_action_blocks` to a kind-filtering wrapper over that helper, deleting the duplicate loop and keeping its measurements in prose (E-02).
3. `ipd_lifecycle._requirements_from_plan`: build `must` and `validation` from the block helper (E-03).
4. `ipd_lifecycle.frozen_region_digest`: correct the docstring's now-false first-line-only mechanism and record that its stated property did not hold (E-04).
5. `ipd_lifecycle`: record the accepted one-time invalidation, its evidence, and why a versioned digest is refused (E-05).
6. `tests/test_ipd_lifecycle_cli.py`: four regression pins, two for the fix and two for the no-op invariant (E-06).
7. `ipd-structure-and-linting` spec Section 11: amend the receipt-invalidation sentence (see Spec / documentation sync).

## Deferred / out of scope (with reason)

- A VERSIONED OR DUAL DIGEST is refused, not deferred, with the reason recorded in E-05: it would require keeping the defective first-line-only payload builder permanently reachable inside the safety gate in order to validate old receipts under the old rule.
  - Carrier-Declined: There is nothing to carry. This row records a REFUSED ALTERNATIVE, not an outstanding defect: the one-time invalidation is accepted deliberately (E-05, with its four measured reasons), so no future work is owed and a carrier would name an obligation that does not exist. Keeping the defective extraction permanently reachable inside the safety gate is the harm this refusal avoids, so it must never be filed as work to do later.
- BACKFILLING OR RE-FREEZING the three affected v2 receipts is out of scope. All three are already dead by `_receipt_is_live` (F-06), and `refreeze_receipt` exists for the case where a live one is hit. Rewriting machine-local state to paper over a rule change would also be exactly the hand-edit of a receipt the execution contract forbids.
  - Carrier-Declined: Nothing is owed. Receipts are GITIGNORED MACHINE-LOCAL STATE under `.aw/state/ipd-lifecycle/`, so there is no tracked artifact a carrier could govern and no other checkout whose receipts this repository can see. All three affected receipts are already rejected as TERMINAL PLAN by `check_engine._receipt_is_live` independently of this change (F-06, re-verified at review: all three `plan_path` values absent), and the shipped `refreeze_receipt` verb already answers the live case, so the remedy exists rather than being deferred.
- `plan_content_digest` IS NOT TOUCHED. It is the receipt's identity field and the legacy v1 fallback key; changing it would alter how 21 of the 24 on-disk receipts are judged, which is a separate and larger change than the one this defect names.
  - Carrier-Declined: This row is a SCOPE BOUNDARY on a field that is behaving correctly, not a deferred defect. `plan_content_digest` is doing its two jobs (receipt identity, and the v1 fallback key for the 21 pre-`rchpms` receipts) and nothing measured here shows it wrong, so filing a carrier would assert an obligation no evidence supports. If a defect in it is ever measured, that is its own item.
- THE CHILD-TABLE SENSITIVITY GAP stays where it is. `probe_cache_digest` covers child-table rows and `frozen_region_digest` deliberately does not; that divergence is documented and justified in both docstrings and is not part of this defect.
  - Carrier-Declined: Nothing is owed, because the divergence is a DECISION already recorded in both docstrings rather than a gap someone forgot. `probe_cache_digest` answers "must the coverage probe re-run?" and `frozen_region_digest` answers "is the reviewed contract unchanged?"; a child table is an input to the first question and not part of the second. Filing a carrier would schedule the undoing of a deliberate design choice.
- `_ORCH_ROW_RE`'s deliberate refusal to parse continuation lines (spec `r07vma` R1a) is untouched. That is a statement about typed child-tracking row SHAPE, not about what the digest freezes.
  - Carrier-Declined: Nothing is owed. This is a SPEC-MANDATED refusal (`r07vma` R1a), so the behavior is the contract rather than a defect, and a carrier would file work to violate a spec. The row exists only to stop a reader inferring that this plan's widening of the digest implies a matching widening of row parsing; the two rules answer different questions.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` is declared because E-02 must delete the duplicate loop there; leaving it undeclared would either fork a third copy of the rule (which the backlog item explicitly forbids) or make an undeclared edit. The spec file is declared because F-09's sentence contradicts the code this plan ships.
- Under-scope: none known. `agent_workflows/ipd_lint.py` gains the helper, `agent_workflows/ipd_lifecycle.py` consumes it, `agent_workflows/runner_shared.py` delegates to it, `tests/test_ipd_lifecycle_cli.py` pins it, and the spec sentence is amended. The probe's own tests need no change because `probe_cache_digest` must not move (V-02 proves it does not).

## Required tests / validation

- `python3 -m pytest` run BARE, per the execution contract: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Paste the actual summary line.
- The four new pins in `tests/test_ipd_lifecycle_cli.py` (E-06), with (a) and (b) confirmed to FAIL against the pre-change extraction, so they are proven to be regression tests rather than tautologies.
- A corpus re-run of the F-05 no-op check and the F-04 capture measurement against the SHIPPED code rather than a simulation.
- `aw ipd lint --phase pre-transition` on this plan.
- `aw check` for the release-gate and consistency rule families, since this plan carries `Blocks-Release: next` and `From-Backlog: 168p5j`.

## Spec / documentation sync

`.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 11 must be amended, and the reason is that it describes the gate this plan changes. The sentence "It PERSISTS across unrelated intervening commits and is invalidated only by a change to the plan's own content digest or by an intervening commit that touched a path inside the plan's `Scope-Paths`" is already wrong at HEAD: `rchpms` re-keyed the receipt from `plan_content_digest` onto `frozen_region_digest`, and the spec was never amended for it (F-09). After this plan it would be wrong in a second way, because the frozen region now covers each item's whole action block. The amendment states the actual key (the frozen `Scope-Paths` plus each E/V item's whole action block, excluding checkbox marks, indented sub-fields, execution/validation state and workflow history) and notes the accepted one-time invalidation.

WHY AMEND RATHER THAN LEAVE IT: a spec sentence that describes a safety gate's invalidation rule is what a future plan gets reviewed against, so leaving it stale means the next author reasons about a key that has not existed since `rchpms`. The repository contract is explicit that a plan changing behavior a spec describes should carry the amendment in the same change and declare the spec file in `- Scope-Paths:`, which this plan does.

NOT AMENDED, deliberately: spec `25kzda` Section 5.5a. Its six accept conditions are stated in terms of "every frozen requirement category other than scope is byte-identical, proven by substituting the receipt's stored `scope_paths` into the plan's current frozen-region payload and reproducing the stored digest". That wording is agnostic about WHAT a category contains, so widening the category's contents leaves every condition true as written. The substitution test also keeps working by construction, because `_frozen_region_payload` remains the single payload builder both paths read.

## Open questions

### OQ-01: Should `ipd_lint.leaf_action_blocks` also be consumed by the `IPD-C801` citation advisory, which today scans raw lines?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: RESOLVED AS NO, and it needs no maintainer ruling because the question is about how to scope a fence, not about scope the human owns. Three reasons, each checkable. FIRST, the two consumers ask different questions of the same text: `IPD-C801` reports a POSITION in raw text so a human can find a bare line-number citation, while `leaf_action_blocks` produces a NORMALIZED joined block (continuation lines are `strip()`ed and joined with a single space), which destroys exactly the column and line information the advisory exists to report. Sharing the helper would therefore make the advisory worse, not merely broader. SECOND, the advisory cannot affect execution authority: it feeds no digest and gates nothing, so it is not part of this defect's blast radius, and folding it in would convert a safety fix into a linter refactor whose failure mode is a wrong advisory position rather than a stale receipt. THIRD, the duplication this question worries about is not the duplication the backlog item forbids: the item forbids a third copy of the TERMINATION RULE ("where does an action end"), and the advisory implements no termination rule at all - it scans lines. So no carrier is owed and none is filed; had the advisory carried its own copy of the termination rule, this would instead have been an in-scope finding.
  - Carrier-Declined: Nothing is owed. The resolution is NO rather than LATER: sharing the helper would degrade the advisory (it needs raw positions, the helper returns normalized joined text), and the advisory duplicates no termination rule, so there is no future obligation a carrier could name. Recorded here so a later reader does not mistake this plan's silence on `IPD-C801` for an oversight.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session showing `ipd_lint.leaf_action_blocks` returning, for a plan whose E-01 has a continuation line and an indented `- Expected outcome:` sub-field, a block that CONTAINS the continuation text and EXCLUDES the sub-field text; plus a corpus comparison over all `.ipd.md` files in `.aw/records/plans/` showing its E-item output equals `runner_shared.e_item_action_blocks`' pre-change output on every file, with the file count printed and the number of DIFFERING files stated as zero. Capture that pre-change output BEFORE applying E-02 (for example into a JSON file under the gitignored `tmp/` tree), because once `e_item_action_blocks` delegates there is no second implementation left to compare against and the comparison becomes a tautology against itself. ALSO assert the helper is exercised on a V-item leaf list, not only an E-item one, since E-01's whole generalization is that it takes the leaf list rather than hardcoding `doc.exec_leaves`: a helper that happens to work only for E-items would pass an E-only check and then silently under-serve E-03's `validation` category.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a corpus run printing `probe_cache_digest` for every `.ipd.md` under `.aw/records/plans/` before and after the change and asserting ZERO differ, with the count printed. This is the pin that proves the re-homing did not perturb the probe cache and so did not silently invalidate every cached orchestrator verdict.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a session on the F-01/F-02 fixture showing, AFTER the change, that `frozen_region_digest` DIFFERS across the E-item continuation rewrite and DIFFERS across the V-item continuation rewrite (print both pairs of digests), and that `receipt_is_current` returns False for each rewritten plan against a receipt minted from the base text. Also print `_requirements_from_plan(base)["must"]` and `["validation"]` showing continuation prose is now present in both.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rewritten `frozen_region_digest` docstring and a `grep`-style search over `agent_workflows/ipd_lifecycle.py` for "only ``.text``", "action text alone" and "first line" showing no surviving sentence describes the extraction as first-line-only; the pasted docstring must name backlog `168p5j` and state where the block rule lives.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the committed decision prose, and paste a fresh re-measurement of its load-bearing numbers taken through `ipd_lifecycle.receipt_dir` (not a composed path): the total receipt count, the v1 count with no `frozen_region_digest`, the v2 ids, and for each v2 receipt its recorded `plan_path` plus whether that path exists now. The prose must match the numbers pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line showing the suite passing, and reconcile it against the pre-change baseline of `2935 passed, 2 skipped` (re-measured at review on 2026-09-28); a DIFFERENT total must be explained against a named E-item rather than waved through, and the expected delta is exactly the four new assertions of E-06. Separately paste the four new assertions running against the PRE-change extraction and showing (a) and (b) FAIL there, proving they are regression tests rather than tautologies. Separately paste the corpus no-op re-run AGAINST SHIPPED CODE (not a simulation): conforming execution edits over every `.ipd.md` under `.aw/records/plans/`, with the file, unchanged and MOVED counts printed. THE BAR IS `MOVED == 0`, RE-DERIVED AT EXECUTION TIME, not a match to any count written in this plan: the corpus is a live population that grew from 841 files at authoring to 857 at review, so a differing file count is expected and is not a finding, while a single mover is a BLOCKER because it means the fix re-opened `xmqv5l`. Also re-derive F-04's capture measurement and state the resulting percentages; the bar there is the PROPERTY (first-line extraction misses a large majority of E-item requirement prose), not the authored figures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` with `- Readiness: go-pending-approval`, written by `/plan-review` on 2026-09-28 as the output of that review. `reviewed` is not approval: explicit human sign-off (`- Status: approved`) is still required before execution.

WHAT THE HUMAN IS APPROVING. This is a real and serious defect in a SAFETY GATE, and review reproduced it exactly: rewriting an E-item's continuation line from "Do the safe thing." plus "delete the production database" to a benign variant leaves `frozen_region_digest` byte-identical at `d6bbbc732bcdbdcb`, and `receipt_is_current` still returns True. The same holds for V-items (F-02). Across the tracked corpus, 43.5% of the requirement prose the digest claims to freeze is invisible to it, and for E-items alone the first line captures only 55.7%. The fix reuses the one shipped block rule rather than forking a third copy, and the invariant that matters most - that a conforming self-execution must NOT invalidate the receipt, which is the `xmqv5l` regression this digest exists to prevent - was independently re-verified at review across all 857 plans with ZERO movers. Two things the human is also approving: a ONE-TIME invalidation of every already-minted v2 receipt (measured blast radius: three receipts, all three already dead by `_receipt_is_live`), and an amendment to an `implemented` spec whose Section 11 sentence has been wrong since `rchpms` re-keyed the receipt.

WHAT REVIEW FIXED: an `aw check` ERROR on this plan. All five `## Deferred / out of scope` rows and OQ-01 named no durable carrier, so `check.ipd-uncarried-obligation` fired at `error` severity with six uncarried obligations - meaning that once this plan reached `executed` it would class `done` in `aw attention` and six recorded obligations would vanish with no record. Each row now carries an explicit `Carrier-Declined:` reason and OQ-01 is resolved. Verified: the rule now returns zero drifts and the repository's `aw check` error count fell from 3 to 2.

On execution, the executor MUST: run `aw ipd begin` before any edit; commit only the paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including V-06's pre-change failure demonstration. No push, no tag, no release. An out-of-scope edit is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop; the fence is a declaration so the reconciliation can tell afterwards what moved. The declared spec edit is announced by the runner before the run starts and reconciled at finalize.

THREE WAYS THIS PLAN CAN FAIL SILENTLY, stated for the executor because a green suite catches none of them.

FIRST, AND WORST: RE-OPENING `xmqv5l`. Widening the digest payload is precisely the direction that made the receipt go stale on every correct execution before `rchpms` fixed it. If any conforming self-execution edit moves the widened extraction, this plan has re-introduced the defect the gate exists to prevent, and the symptom appears later as "the runner refuses every finalize" rather than as a test failure. V-06's corpus no-op re-run is the check, its bar is `MOVED == 0` re-derived against shipped code, and a single mover is a BLOCKER, not a rounding error.

SECOND: A TAUTOLOGICAL V-01. Once E-02 makes `runner_shared.e_item_action_blocks` delegate to the new helper, comparing the two is comparing a function to itself. The pre-change output must be CAPTURED BEFORE E-02 and compared against, or V-01 proves nothing.

THIRD: MOVING `probe_cache_digest`. The probe cache keys orchestrator coverage verdicts. If re-homing the rule perturbs that digest, every cached verdict silently invalidates and every queued orchestrator is re-probed at model cost. V-02's bar is ZERO differing files across the corpus, and it is the reason `runner_shared.py` is in `- Scope-Paths:` at all.

A NOTE ON F-07, SO A TRUE CLAIM IS NOT MISREAD AS FALSE: `finalize_refusal_is_retryable` gates on the refusal SUMMARY line before it inspects findings, so calling it with the contract-rewrite finding ALONE returns False. Compose the whole message, summary included. Review hit this and briefly mistook a correct finding for a wrong one.

This plan carries `- Blocks-Release: next`, inherited from backlog `168p5j` because its `- Work-Kind:` is `bug` and the repository policy is that every live bug gates the next release. That gate travels with this plan and must not be cleared as part of executing it.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.

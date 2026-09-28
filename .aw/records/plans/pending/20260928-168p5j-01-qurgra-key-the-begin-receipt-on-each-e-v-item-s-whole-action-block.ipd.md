# IPD: Key the begin receipt on each E/V item's whole action block, not its first line

- Date: 2026-09-28
- Kind: child
- Concern: `ipd_lifecycle.frozen_region_digest` is the begin receipt's validity key, and it is blind to every CONTINUATION line of an E or V item, so a receipt minted against one requirement stays valid after that requirement is rewritten.
- Scope: widen the frozen-region requirement extraction from a leaf's opening line to its whole action block, reusing the already-shipped block rule rather than forking a third definition; accept the resulting one-time receipt invalidation deliberately and prove the recovery path; amend the spec sentence that still describes the superseded whole-file key.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_ipd_lifecycle_cli.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: to-review
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
| F-04 | Scale, measured across the whole tracked plan corpus rather than the ten-orchestrator sample the backlog item cites. | 841 `.ipd.md` files parsed under `.aw/records/plans/`. E-items: first-line extraction captures 2,274,408 of 4,105,073 block characters (55.4%). V-items: 78,136 of 80,544 (97.0%). Combined E+V: 2,352,544 of 4,185,617 captured, so 43.8% of the requirement prose the digest claims to freeze is invisible to it. |
| F-05 | The fix does not re-open `xmqv5l` (the "stale on every correct execution" regression the frozen digest exists to fix). | Simulated conforming execution edits (tick `[ ]`->`[x]` on every E/V row, `Execution state: performed`, `Observed evidence:` filled, `Result: pass`, appended history line) against all 841 plans: widened extraction UNCHANGED on 841, MOVED on 0. |
| F-06 | The migration cost is three receipts, and all three are already dead. | `receipt_dir` resolves to the shared checkout root and holds 24 receipts. 21 are `schema_version: 1` with no `frozen_region_digest` (unaffected: they take the legacy whole-file branch). The 3 v2 receipts are `63425h`, `e32j35`, `xts8ux`; every one's recorded `plan_path` is under `plans/pending/` and no such file exists there now (`63425h` -> `executed/`, `e32j35` -> `superseded/`, `xts8ux` -> `superseded/`), so `check_engine._receipt_is_live` already rejects all three as terminal. |
| F-07 | A staleness caused purely by the rule change is answerable, not terminal. | Simulating the widened rule against a receipt minted under the narrow one with the plan UNTOUCHED: `receipt_is_current` -> False; `frozen_region_comparison` -> `added=() removed=() non_scope_identical=False eligible=True`; `widening_is_acceptable` -> False; so `finalize_precheck` composes "Scope-Paths unchanged but a frozen REQUIREMENT changed, so this is a contract rewrite of the reviewed plan", and `runner_shared.finalize_refusal_is_retryable` returns True for that message. The agent is asked to justify or undo rather than losing the work. |
| F-08 | Module direction, settled by measurement rather than taste. | `python3 -X importtime`: `agent_workflows.ipd_lint` 28,146us cumulative, `agent_workflows.runner_shared` 44,476us. `ipd_lint` has no module-scope `runner_shared` import (only a lazy in-function one) and `ipd_lint` already owns `Leaf`, `_LEAF_RE` and `_SUBFIELD_RE`. So the rule belongs in `ipd_lint`, and `ipd_lifecycle` gains no dependency on the larger module. |
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
- BACKFILLING OR RE-FREEZING the three affected v2 receipts is out of scope. All three are already dead by `_receipt_is_live` (F-06), and `refreeze_receipt` exists for the case where a live one is hit. Rewriting machine-local state to paper over a rule change would also be exactly the hand-edit of a receipt the execution contract forbids.
- `plan_content_digest` IS NOT TOUCHED. It is the receipt's identity field and the legacy v1 fallback key; changing it would alter how 21 of the 24 on-disk receipts are judged, which is a separate and larger change than the one this defect names.
- THE CHILD-TABLE SENSITIVITY GAP stays where it is. `probe_cache_digest` covers child-table rows and `frozen_region_digest` deliberately does not; that divergence is documented and justified in both docstrings and is not part of this defect.
- `_ORCH_ROW_RE`'s deliberate refusal to parse continuation lines (spec `r07vma` R1a) is untouched. That is a statement about typed child-tracking row SHAPE, not about what the digest freezes.

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
- Status: open
- Owner: none
- Resolution or deferral rationale: Out of scope for this defect and deliberately not bundled. The advisory reports positions in raw text and never feeds the receipt digest, so it cannot affect execution authority; changing it here would broaden a safety fix into a linter refactor. File it separately if the duplication becomes a maintenance cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session showing `ipd_lint.leaf_action_blocks` returning, for a plan whose E-01 has a continuation line and an indented `- Expected outcome:` sub-field, a block that CONTAINS the continuation text and EXCLUDES the sub-field text; plus a corpus comparison over all `.ipd.md` files in `.aw/records/plans/` showing its E-item output equals `runner_shared.e_item_action_blocks`' pre-change output on every file, with the file count printed.
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
  - Required evidence: paste the bare `python3 -m pytest` summary line showing the suite passing. Separately paste the four new assertions running against the PRE-change extraction and showing (a) and (b) FAIL there, proving they are regression tests. Separately paste the corpus no-op re-run against shipped code: conforming execution edits over all plans in `.aw/records/plans/`, with the unchanged and moved counts printed and moved equal to zero.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is one cohesive change to one safety gate: the digest reads the whole action block, the single rule is shared rather than copied, the forced receipt invalidation is accepted with its evidence, and the spec sentence describing the gate is corrected in the same change. Execution follows the repository contract: `aw ipd begin` before any edit, commits only through `aw commit` limited to the declared `- Scope-Paths:`, no push, no tag, bare `python3 -m pytest` with actual output pasted, and no claim of a passing suite that was not run. The declared spec edit is announced by the runner before the run starts and reconciled at finalize. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.

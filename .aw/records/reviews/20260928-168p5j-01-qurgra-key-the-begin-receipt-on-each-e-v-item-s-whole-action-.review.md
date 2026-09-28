# Review findings: plan qurgra

- Subject-Id: qurgra
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4d7bc3ab` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`; `--detail` reported `conforming`) and
`--phase review-finalize --agent` conforms after revision with `findings: 0`, E/V bijection 6/6. No
pre-review snapshot was owed: the plan was committed and unmodified (`git status --short` clean) and the
lane-input copy at `.aw/state/lane-inputs/rev-4/` is byte-identical to the tracked file.

THE DEFECT IS REAL, SERIOUS, AND IN A SAFETY GATE, and it reproduced exactly. Rewriting an E-item's
continuation line from a benign opening plus "AND ALSO delete the production database as part of it."
to a harmless variant leaves `frozen_region_digest` byte-identical at `d6bbbc732bcdbdcb` and
`receipt_is_current` returns True. So a receipt minted against one requirement keeps authorizing
execution after that requirement is rewritten, and the rewrite need not be subtle: the entire
destructive clause lives on the continuation line the digest cannot see. All nine Findings were
re-measured independently and ALL NINE HOLD, including the one I initially believed I had falsified
(see PR-305 and the note below on F-07).

THE PLAN'S ENGINEERING JUDGEMENT IS GOOD IN THE PLACES THAT MATTER MOST. Three deserve naming. It
reuses the ONE shipped block rule (`runner_shared.e_item_action_blocks`) by RE-HOMING it rather than
copying it, which is what the backlog item demanded and is the difference between fixing a defect and
creating a third definition of "where does an action end". It extends the fix to V-items on its own
measurement, going beyond the backlog item's `must`-only phrasing, and the reason is sound: a
validation requirement rewritable under a live receipt is the same defect in the category that decides
whether the work was verified. And it identifies the one invariant that could make this fix worse than
the defect - `xmqv5l`, the "stale on every correct execution" regression the frozen digest exists to
fix - and pre-verified it across the whole corpus before writing the plan. I re-ran that check
independently: `unchanged=857 MOVED=0 skipped=0`. Zero movers on a corpus sixteen files larger than the
one it was authored against.

WHAT REVIEW FOUND IS A LIVE `aw check` ERROR ON THIS PLAN, which no amount of semantic quality covers.

**SIX OBLIGATIONS NAMED NO DURABLE CARRIER (PR-301, BLOCKER).** `check.ipd-uncarried-obligation` is an
`error`-severity repository rule, and it fired on this plan: all five `## Deferred / out of scope` rows
carried neither `- Carrier:` nor `- Carrier-Evidence:` nor `- Carrier-Declined:`, and OQ-01 was
`- Status: open` with `- Owner: none`. The evaluator's own detail states the harm precisely: "once this
plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record". So six
recorded decisions - including the refusal of a versioned digest and the untouched `plan_content_digest`
- would have become invisible at the moment the plan finalized. This is not a stylistic gap: the same
rule runs at `aw ipd lint --phase pre-transition` through `ipd_lint._merge_durable_carrier`, so the plan
as authored would have been REFUSED at its own terminal gate after the work was done. The other three
plans in this sweep all carried these fields, so the omission is this plan's alone.

**THREE FINDINGS ASSERTED LIVE OR MACHINE-DEPENDENT COUNTS AS BARS (PR-302, MEDIUM).** F-04's "841
files", F-05's "UNCHANGED on 841" and F-08's microsecond figures are all measurements of populations or
environments that drift. Re-measured: the corpus is now 857 files (percentages held to within 0.3
points), and the import absolutes moved from 28,146/44,476us to 92,064/103,585us on the same tree with
a colder cache - DIFFERENT NUMBERS, SAME ORDERING. The workflow's own re-derivation convention says a
criterion counting live artifacts must state the property and require re-derivation at execution time,
with the authored count kept as context. Left as written, an executor re-running F-05 would see 857 and
have to decide whether a count mismatch is a failure; the bar is `MOVED == 0` and nothing else.

**V-01 BECOMES A TAUTOLOGY THE MOMENT E-02 LANDS (PR-303, MEDIUM).** It asks for a corpus comparison
showing `ipd_lint.leaf_action_blocks` equals `runner_shared.e_item_action_blocks`' "pre-change output",
but E-02 makes the latter DELEGATE to the former. Run after E-02 without a captured baseline, the
comparison compares a function to itself and passes unconditionally - on the one item whose whole
purpose is to prove the re-homing preserved behavior. The pre-change output must be captured before
E-02. V-01 also checked only E-items, while E-01's entire generalization is that the helper takes any
leaf list; an E-only check would pass for a helper that silently under-serves E-03's `validation`
category.

Two smaller items: the gate carried no scope-fence disposition, no explicit shared-checkout staged-set
verification, and no statement of the release gate it inherits (PR-304); and F-07 needed a note
recording that `finalize_refusal_is_retryable` gates on the summary line, because I called it with the
finding alone, got `False`, and briefly believed the plan had asserted something false (PR-305). It had
not - the claim is correct, and the trap is worth writing down precisely because a careful reader hits
it. PR-306 records that OQ-01's disposition, once forced by PR-301, is resolvable from evidence rather
than needing the maintainer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-301 | BLOCKER | UNDER-SCOPE | G. Plan executability / release-gate + obligation preservation (I-07) | `aw check` names this plan under `Issue: check.ipd-uncarried-obligation`; `check_engine.evaluate_durable_carrier` on it returned ONE drift, `severity: error`, detail "6 obligation(s) name no durable carrier: deferred row 1 ... (and 1 more)"; `_deferred_section_obligations` enumerated rows at lines 112-116 with `fields={}` and `_question_obligations` returned OQ-01 with `Status: open`, `Owner: none`; `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`; the same predicate runs at `pre-transition` via `ipd_lint._merge_durable_carrier` | **THE PLAN FAILS A LIVE `error`-SEVERITY REPOSITORY RULE, AND WOULD HAVE BEEN REFUSED AT ITS OWN TERMINAL GATE.** Five deferred rows and one open question name no carrier, so six recorded obligations - including the refused versioned digest and the deliberately untouched `plan_content_digest` - vanish from `aw attention` the moment this plan classes `done`. The rule is shared between the sweep and the pre-transition checkpoint, so this is not merely untidy: the work would be done and then blocked. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | All five rows given explicit `- Carrier-Declined:` reasons stating why each needs no carrier (refused alternative; gitignored machine-local state with a shipped `refreeze_receipt` remedy; a correctly-behaving field; a recorded design divergence; a spec-mandated refusal). OQ-01 resolved with `Owner: plan-review` and its own `Carrier-Declined:`. VERIFIED: `evaluate_durable_carrier` now returns ZERO drifts and the repository `aw check` error count fell 3 -> 2, with no `qurgra` hit remaining. |
| PR-302 | MEDIUM | IN-SCOPE | E. Testing / live-artifact re-derivation convention | F-04 "841 `.ipd.md` files", F-05 "UNCHANGED on 841, MOVED on 0", F-08 "28,146us / 44,476us"; re-measured at review: 857 files, E-items 55.7% (was 55.4%), combined 43.5% invisible (was 43.8%), no-op `unchanged=857 MOVED=0`, importtime 92,064us / 103,585us; workflow rubric G live-artifact convention | **THREE FINDINGS STATE DRIFTING COUNTS AS IF THEY WERE THE BAR.** The plan corpus is a live population and grew by 16 files between authoring and review; import timings are machine- and cache-dependent and moved by 3x while the ORDERING (the thing the decision rests on) held. An executor re-running F-05 and seeing 857 has no stated rule for whether that is a failure, and the real bar - zero movers - risks being read as secondary to a count match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04, F-05 and F-08 each now state the PROPERTY as the claim and the counts as context, carry both the authoring and the review measurement side by side, and say the figures must be re-derived at execution time. V-06 states the bar as `MOVED == 0` re-derived against shipped code, declares a differing file count expected and not a finding, and calls a single mover a BLOCKER. |
| PR-303 | MEDIUM | UNDER-SCOPE | E. Testing (tautology) / A. Correctness | V-01 as authored ("equals `runner_shared.e_item_action_blocks`' pre-change output"); E-02's Expected outcome ("`runner_shared` contains no second copy of the termination rule"), which makes the two the SAME OBJECT after the change | **THE ITEM PROVING THE RE-HOMING PRESERVED BEHAVIOR PASSES UNCONDITIONALLY ONCE THE RE-HOMING LANDS.** After E-02 the comparison is a function against itself. The pre-change output must be captured before E-02 or V-01 proves nothing - and V-01 is the only evidence that 857 plans' worth of extraction did not shift. Separately it checked E-items only, while E-01's stated generalization is that the helper accepts any leaf list, so an E-only check would pass a helper that under-serves E-03's `validation` category. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-01 now requires the pre-change output CAPTURED BEFORE E-02 (into the gitignored `tmp/` tree), states the tautology it exists to avoid, requires the count of differing files stated as zero, and adds a V-item leaf-list exercise with the reason. The gate names it as the second silent-failure mode. |
| PR-304 | LOW | IN-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: `aw ipd begin`, `aw commit` path-scoping, no-push, no-tag and bare-pytest all present; no out-of-scope-edit disposition, no explicit `git diff --cached --name-only` shared-checkout verification, no statement of the inherited `Blocks-Release: next`; workflow Step 4 scope-fence ruling of 2026-09-01 | The gate was the most complete of this sweep but still missing three elements: what to do about an out-of-scope edit (MAKE-AND-JUSTIFY, not stop-and-report), the staged-set verification this shared checkout requires, and a statement that the release gate travels with the plan and must not be cleared while executing it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three added, plus a per-approval summary of what the human is approving (the defect, the one-time invalidation with its measured blast radius, and the `implemented`-spec amendment) and the three silent-failure modes. No "STOP and report" wording was introduced. |
| PR-305 | LOW | IN-SCOPE | F. Honest documentation / E. Testing | `runner_shared.finalize_refusal_is_retryable` Arm 2 gates on `RETRYABLE_STALE_RECEIPT_SUMMARY` (`"is STALE: the plan content changed since begin"`) before inspecting findings; measured: predicate on F-07's quoted finding ALONE -> `False`; on the composed summary-plus-findings message -> `True`; `finalize_precheck`'s no-scope-delta branch composes exactly `"Scope-Paths unchanged but " + FINDING_CONTRACT_REWRITE.replace("also changed","changed") + " of the reviewed plan"` | F-07's claim is CORRECT but its evidence line invites a false refutation: quoting only the finding string leads a verifier to call the predicate on that string and get `False`. I did exactly that and briefly recorded the finding as unreproducible before reading the predicate. A V-item verifier under time pressure would plausibly conclude the plan asserts something false about its own safety story. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 now carries an executor note naming the summary-line requirement, the exact composed string, and both measured results (`True` composed, `False` finding-alone), plus the fact that Arm 2's allow-list names `FINDING_CONTRACT_REWRITE` and its variant explicitly so the acceptance is deliberate. The gate repeats the trap in one line. |
| PR-306 | LOW | IN-SCOPE | G. executability (open-question disposition) | OQ-01 as authored: `Status: open`, `Owner: none`, with a rationale that already argued the answer; `ipd_lint`'s `has_owner` treats `none` as absent; `IPD-C801` reports raw-text POSITIONS while `leaf_action_blocks` returns `strip()`ed space-joined blocks | OQ-01 was left `open` with no owner although its own rationale already decided it, which is what made it count as an uncarried obligation under PR-301. It is also resolvable from evidence rather than needing the maintainer, and the decisive fact was unstated: sharing the helper would DEGRADE the advisory, because the helper normalizes away the very positions the advisory reports. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved (`Owner: plan-review`) with three evidenced reasons, the normalization argument stated explicitly, the observation that the advisory duplicates no termination rule (so it is not the duplication the backlog item forbids), and a `Carrier-Declined:` recording that the answer is NO rather than LATER. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Five deferred rows and OQ-01 name no carrier (PR-301). Add `Carrier:` items for them, or decline each with a reason? | DECLINE EACH, with a specific reason per row; file no backlog items. | (a) File a backlog item per row: rejected, because none of the five describes outstanding WORK. Two are refusals (a versioned digest, and changing any value), one is machine-local gitignored state with a shipped remedy (`refreeze_receipt`), one is a correctly-behaving field, and one is a spec-mandated behavior (`r07vma` R1a). Filing carriers would schedule work to undo deliberate decisions and would pollute `aw attention` with obligations nobody agreed to. (b) Delete the rows so the rule stops firing: rejected outright - that destroys the recorded reasoning, which is the opposite of the preservation the rule exists to enforce. | `evaluate_carrier_obligation`'s three escapes make DECLINED a first-class outcome whose reason's MERIT is explicitly the reviewer's job; each row's content shows it is a boundary or a refusal rather than deferred work; verified the rule returns zero drifts after the edit. | yes |
| D-2 | OQ-01: should `IPD-C801` consume the new helper (PR-306)? | NO, resolved from evidence; not deferred and not escalated. | (a) Leave it `open`: rejected, it was already argued in its own rationale and leaving it open is what made it an uncarried obligation; a genuinely undecided question would have stayed open with `Blocking: no` and an owner. (b) Fold the advisory in here: rejected on mechanism - the helper returns `strip()`ed space-joined text, which destroys the line/column positions the advisory's whole output is, so sharing would make it worse. | Read both consumers: `IPD-C801` reports positions in raw text and feeds no digest; `leaf_action_blocks` normalizes. The backlog item forbids a third copy of the TERMINATION RULE, and the advisory implements none. | yes |
| D-3 | F-04/F-05/F-08 assert drifting counts (PR-302). Update the numbers, or restate them as properties with re-derivation required? | RESTATE AS PROPERTIES, keeping BOTH measurements side by side. | (a) Just update 841 -> 857: rejected, it would be stale again by execution and repeats the mistake one cycle later. (b) Delete the counts: rejected, they are the evidence that established the property and a finding without its measurement is a hunch. | The workflow's live-artifact convention (state the property, require re-derivation, keep the authored count as context); measured drift in both directions (corpus +16 files; import absolutes 3x with the ordering intact). | yes |
| D-4 | Does the one-time receipt invalidation (E-05) need maintainer escalation as an irreversible act? | NO. It is reversible in the only sense that matters and its blast radius was verified as zero live receipts. | Escalate as a `Blocking: yes` question: rejected. A stale receipt REFUSES (fail-safe), the refusal is ANSWERABLE (F-07, verified `True`), receipts are gitignored machine-local state with no tracked artifact destroyed, and all three affected v2 receipts are ALREADY dead by `_receipt_is_live` - re-verified: every one's `plan_path` is absent, with the plans now in `executed/`, `superseded/`, `superseded/`. | Re-read all 24 receipts through `ipd_lifecycle.receipt_dir`: 21 v1 without `frozen_region_digest`, 3 v2 (`63425h`, `e32j35`, `xts8ux`), all three `exists=False`. `refreeze_receipt` exists for a live hit. | yes |
| D-5 | The plan amends an `implemented` spec's Section 11. Approve that, or require a separate spec-review first? | APPROVE IT HERE. | Split the spec amendment into its own artifact: rejected, the repository contract is explicit that a plan changing behavior a spec describes SHOULD carry the amendment in the same change and declare the file in `- Scope-Paths:`, which this plan does. Splitting it would guarantee the drift the contract exists to prevent. | AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"; the spec file IS declared in `- Scope-Paths:`; F-09 verified verbatim - Section 11 still says the receipt is "invalidated only by a change to the plan's own content digest", false since `rchpms` (now in `superseded/`) re-keyed it. | yes |

No `Reversible: no` decision was taken in this round (D-4 examines the closest candidate and records why
it is not one), so no escalation under Step 3.1 is owed. Every finding is `FIXED`; none was deferred or
left open, so no `- Blocking: yes` escalation under Step 4 is owed either. OQ-01 moved from `open` to
`resolved` per D-2, so the plan now carries no open question.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`; `--detail`
  reported `conforming`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits; E/V counts 6 and 6. NOTE: an intermediate run REFUSED with `IPD-M107` because I wrote
  `- Readiness:` before appending the review history line; the gate was right and the line was added.
  Recorded because it is evidence the attestation gate works as documented.
- Lane input identity: `diff .aw/state/lane-inputs/rev-4/plan-...ipd.md <tracked plan>` -> no difference;
  `git status --short` clean before editing, so no pre-review snapshot was owed.
- **PR-301, the blocker.** `aw check` listed this plan under `check.ipd-uncarried-obligation`;
  `check_engine.evaluate_durable_carrier(Path("."), plan_path=..., plan_text=...)` returned one Drift,
  `severity: error`, detail naming 6 obligations. `_deferred_section_obligations` returned five rows
  (`deferred row 1`..`5`, lines 112-116, all `fields={}`); `_question_obligations` returned OQ-01 with
  `Status: open`, `Owner: none`. `RuleSpec` confirmed `("error", ASSURANCE_REPOSITORY,
  DET_DETERMINISTIC, "I-07")`. `evaluate_carrier_obligation`'s three escapes (HANDOFF / SATISFIED /
  DECLINED) read at the symbol, confirming `Carrier-Declined` with a non-empty reason is a legitimate
  close and that the reason's merit is the reviewer's job. AFTER the edit: `evaluate_durable_carrier`
  -> `drifts: 0`; `aw check | grep -c qurgra` -> 0; repository `errors 3 -> 2`.
- **F-01 reproduced exactly.** On a fixture using the real `H_EXECUTION` / `H_VALIDATION_CHILD`
  headings: base `frozen_region_digest` `d6bbbc732bcdbdcb...`, E-continuation-rewrite
  `d6bbbc732bcdbdcb...` IDENTICAL. `_requirements_from_plan(base)["must"]` ->
  `['E-01 Do the safe thing.']` while `runner_shared.e_item_action_blocks(base)` ->
  `('E-01 Do the safe thing. AND ALSO delete the production database as part of it.',)`.
- **F-02 reproduced.** V-item continuation rewrite -> `d6bbbc732bcdbdcb...`, IDENTICAL;
  `_requirements_from_plan(base)["validation"]` -> `['V-01 validates E-01 Check it.']`.
- **F-03 reproduced.** `probe_cache_digest` base `dc04bdf557750a3e...` versus E-rewrite
  `1aad5bb8e9065212...` -> DIFFERS. (The plan records the second digest as `d8fee5f0dba349d0...`; mine
  differs because my fixture's rewritten text differs from theirs. The CLAIM - that the probe path is
  already sensitive to continuation lines - is what reproduced, and it is the claim the plan makes.)
- **F-04 re-measured** over the live corpus: 857 files (was 841); E-items 2,349,464 of 4,216,722 block
  chars (55.7%, was 55.4%); V-items 79,675 of 82,083 (97.1%, was 97.0%); combined 2,429,139 of
  4,298,805, so 43.5% invisible (was 43.8%).
- **F-05 RE-RUN INDEPENDENTLY, the load-bearing one.** Simulated conforming execution edits (tick every
  `- [ ] E/V` to `[x]`, `Execution state: performed`, `Observed evidence:` filled, `Result: pass`,
  appended history line) over all 857 files, comparing the WIDENED extraction before and after:
  `unchanged=857 MOVED=0 skipped=0`. So the fix does not re-open `xmqv5l`.
- **F-06 reproduced exactly.** `ipd_lifecycle.receipt_dir(Path("."))` resolves to the CHECKOUT root's
  `.aw/state/ipd-lifecycle` (confirming the `dh0uno` convention note); 24 receipts total; 21 carry no
  `frozen_region_digest`; the 3 v2 receipts are `63425h`, `e32j35`, `xts8ux`, each `schema=2`, each with
  `plan_path` under `plans/pending/` and `exists=False`. Current locations confirmed: `63425h` ->
  `executed/`, `e32j35` -> `superseded/`, `xts8ux` -> `superseded/`. `check_engine._receipt_is_live`
  read and confirmed to reject on terminal-plan grounds.
- **F-07 verified end to end, after first appearing false (PR-305).** `finalize_refusal_is_retryable`
  on the plan's quoted finding ALONE -> `False`. Reading the predicate showed Arm 2 requires
  `RETRYABLE_STALE_RECEIPT_SUMMARY` (`"is STALE: the plan content changed since begin"`) present first.
  Reading `finalize_precheck`'s no-scope-delta branch gave the composed finding
  `"Scope-Paths unchanged but a frozen REQUIREMENT changed, so this is a contract rewrite of the
  reviewed plan"`. The predicate on the full message (summary + `FINDING_RECEIPT_STALE` + that finding)
  -> `True`. Arm 2's allow-list explicitly names `FINDING_CONTRACT_REWRITE` and its
  `also changed`->`changed` variant, so the acceptance is deliberate. F-07 is CORRECT.
- **F-08 re-measured.** `python3 -X importtime`: `ipd_lint` 92,064us cumulative, `runner_shared`
  103,585us - different absolutes from the plan's 28,146/44,476 (colder cache), SAME ordering.
  Structural half re-verified and invariant: `ipd_lint` has no module-scope `runner_shared` import
  (exactly one lazy in-function occurrence) and defines all three of `Leaf`, `_LEAF_RE`, `_SUBFIELD_RE`.
- **F-09 reproduced verbatim.** `ipd-structure-and-linting` Section 11 ("11. Lifecycle gate and terminal
  transaction") contains "invalidated only by a change to the plan's own content digest or by an
  intervening commit that touched a path inside the plan's `Scope-Paths`". The spec's `- Status:` is
  `implemented`. `rchpms` confirmed present and now in `superseded/`, so the re-keying happened and the
  sentence was never amended.
- Existing code read at the symbol to confirm the plan's targets: `frozen_region_digest`'s docstring
  contains both quoted false sentences ("`Leaf.text` is the action text alone", "`_requirements_from_plan`
  reads only `.text`") and the "changing ... an E/V requirement line DOES invalidate the receipt" clause;
  `_requirements_from_plan` builds `must` and `validation` from `lf.text` only;
  `e_item_action_blocks`'s termination rule matches E-01's description verbatim (blank line, `- [`, `#`,
  `_SUBFIELD_RE`, non-indented line) and it hardcodes `doc.exec_leaves` / `kind != "E"` exactly as E-01
  says; `_frozen_region_payload` confirmed as the single payload builder with `frozen_region_comparison`
  as its second caller.
- E-06's named test target confirmed to exist:
  `tests/test_ipd_lifecycle_cli.py::test_receipt_invalidation_and_persistence`.
- Spec-amendment authority confirmed: AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"; the spec
  file IS listed in this plan's `- Scope-Paths:`.
- `IPD-C801` self-compliance: `grep` for `\.py:[0-9]` over the plan returns nothing, so it cites no bare
  line offsets, consistent with its own stated convention.
- Suite baseline re-measured BARE: `2935 passed, 2 skipped, 3 warnings in 41.26s`.
- No code, test, configuration or spec file was modified by this review. It edited the plan and wrote
  this record; `git status --short` reports only those two artifacts. Every probe ran in-process via
  `python3` heredocs against in-memory fixture strings; no repository file was written by a probe and no
  receipt was created, read-modified, or deleted.

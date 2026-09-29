# IPD: Pin the cross-type setid silence sovauj reported and retire the workaround prose it forced

- Date: 2026-09-28
- Kind: child
- Concern: The defect backlog `sovauj` reports (a walkthrough declaring `- Set:` beside a pending plan of the same setid is reported `check.setid-collision`) is ALREADY FIXED in code, but nothing pins the walkthrough-vs-plan shape against regression and five tracked walkthroughs plus an undocumented README still teach the reverse rule.
- Scope: Add the missing plans-plus-walkthrough clean row to the `CollisionTests` table, correct the five tracked walkthroughs whose `- Set:` descriptive asserts the reversed prohibition, and state in the walkthroughs README that a walkthrough MAY declare `- Set:`. No change to `check_engine.check_collisions` behavior.
- Scope-Paths: tests/test_check_engine.py, .aw/records/walkthroughs/README.md, .aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md, .aw/records/walkthroughs/20260917-eiclosure-01-pi4wof-execute-item-closure-measured-not-split.walkthrough.md, .aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md, .aw/records/walkthroughs/20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md, .aw/records/walkthroughs/20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md, .aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: sovauj
- Blocks-Release: next
- Set: setidxtype
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: jji5zx
- Approval: 2026-09-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-29 approved (aw set): status set to approved
- 2026-09-28 reviewed (aw set): /plan-review round 1 complete: APPROVE WITH REVISIONS APPLIED; PR-A01 through PR-A06 all FIXED; OQ-01 resolved by the reviewer it was addressed to; review record written; review-finalize lint conforming.

- 2026-09-28 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-A01 through PR-A06 all FIXED. Review record `.aw/records/reviews/20260928-setidxtype-01-jji5zx-pin-the-cross-type-setid-silence-sovauj-reported-and-retire.review.md` Round 1.
  THE PLAN'S CENTRAL JUDGEMENT IS ACCEPTED AND ITS EVIDENCE HOLDS. F-1 re-driven: the exact `sovauj` fixture (pending plan plus walkthrough sharing a setid) returns `[]` from `check_collisions` at both `include_retired` settings AND from the full sweep, so the reported defect genuinely does not reproduce. F-2 re-driven: `c6648722` is an ancestor of HEAD and the `"(different type: ...)"` emission is absent from the module. F-3 re-driven: the parity test's `assertNotIn`/`assertIn` pair does pin the retired-population behavior the item's second fix would have retargeted. F-4, F-5 (two walkthroughs with differing descriptives DO report the within-type collision, so the new row is not vacuous), F-6, F-7 all hold. Re-aiming the plan at the regression pin and the stale prose, rather than re-fixing a fixed defect, is the right call and the plan says so honestly.
  THE FINDING THAT WOULD HAVE FAILED THE ROW ON ARRIVAL (PR-A01, HIGH, F-9): Step 0 recorded the new fixture's full sweep as `['check.ipd-draft-ready-to-review']`. Re-measured, it is `[]` - with or without descriptives. The one-element prediction is reachable only by passing `status="draft"` to `_plan_text`, which neither this plan nor the existing cross-type row does (that row takes the `approved` default and expects only `(HISTORY_MISSING,)`, from its SPEC). The runner compares the full-sweep set EXACTLY, and a failing CLEAN row sets `clean_row_broken`, so the authored tuple would have failed and reported itself as the cross-type carve-out being broken rather than as a wrong expectation. E-01 and Step 0 now specify `()` with the measurement and require re-driving.
  THE FINDING THAT COULD HAVE DAMAGED A SHARED CHECKOUT (PR-A02, HIGH, F-10): V-01 instructed restoring the cross-type comparison inside `agent_workflows/check_engine.py` and reverting. That module is outside `- Scope-Paths:` by this plan's own choice, and TWO other pending plans (`jpn6hy`, `ghna7l`) declare it while `tl2b2r` declares this plan's own `tests/test_check_engine.py`; a write-then-revert can race a co-worker and a failed revert leaves the repository's collision rule mutated with every suite still green. The falsification itself is sound and was DEMONSTRATED at review without touching the tree: grouping the fixture's records by setid ALONE reports `setid 'topic' held by 2 files across types ['plans','walkthroughs']` while `check_collisions` returns `[]`. V-01 now mandates the in-memory route and an empty `git status --porcelain` on that module as proof.
  THREE RECORD-ACCURACY CORRECTIONS. F-6 and V-03 implied all six `- Set:` declarers need corrected descriptives; measured, the sixth is `5gdzyz`'s bare `- Set: locksafe`, which carries no false clause, is correctly absent from `- Scope-Paths:`, and must stay byte-unchanged, while `u8tiox` declares no `- Set:` line at all and is in scope for the history line only (PR-A03). `u8tiox` carries a THIRD now-false passage the plan does not name, in its `- Date:` block, stating the reversed rule as current fact; E-04 correctly refuses to rewrite it, so the appended history line must name the removed arm and the true rule rather than only pointing at this plan, or a reader of that sentence still believes it (PR-A04, F-11). F-8's baseline of 5 findings is spent, re-measured as 3 with a different mix, so V-04's bar is restated as the `check.setid-collision` count staying 0, which is invariant to that drift (PR-A05, F-12).
  OQ-01 WAS ADDRESSED TO THE REVIEWER AND IS NOW RESOLVED (PR-A06): KEEP THE LONG FORM. The author's reasoning is accepted and strengthened - the passage answers a question that is still non-obvious after the fix, and deleting the explanation is how the five reversed clauses arose. `5gdzyz` proves the terse form is also legitimate, so this is style rather than correctness and five files should not be churned toward a form the tree does not require. Verified harmless: `_parse_setid` treats the parenthetical opaquely, and the rule fires only on a within-type descriptive mismatch, which five distinct setids cannot trigger.
  NO BLOCKING QUESTION REMAINS and no finding is left OPEN or DEFERRED, so nothing is escalated. All four authored `Carrier-Declined` rows were checked against evidence and all four are legitimate; the strongest is the rejected second fix, where three independent sources (the module's own comment, the parity test, and open item `e2j5w4`'s explicit instruction to keep the setid pass on the caller's corpus) endorse the behavior it would have changed.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `sovauj`; Step 0 measurement found the reported code defect already fixed by `c6648722`, so the plan is re-aimed at the regression pin and the stale prose that defect left behind.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close backlog `sovauj` honestly. The behavior it reports as broken is fixed, so this plan does NOT re-fix it; it adds the one regression pin that would have caught it (a plans-plus-walkthrough cross-type clean row, which the existing table lacks), and it retires the five tracked descriptives and the README silence that still instruct a reader to apply the removed rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the shape that regressed

- [x] E-01 Add one row to `tests.test_check_engine.CollisionTests.COLLISIONS` whose fixture is the EXACT `sovauj` shape: a plan in `.aw/records/plans/pending/` declaring `- Set: topic (...)` plus a walkthrough under `.aw/records/walkthroughs/` declaring the SAME `- Set: topic (...)` and its own `- Id:`. Expect NO `check.setid-collision`, and add `"setid"` to the row's forbidden-substring tuple so the detail cannot mention it. The row's `why` must state that this is the `sovauj` shape, that the existing cross-type clean row uses plans-plus-SPECS and therefore never covered walkthroughs, and that the walkthrough must declare its own `- Id:` so the row cannot pass by accidentally tripping `check.id6-identity-slot` instead.
  THE EXPECTED-RULES TUPLE IS `()`, NOT A ONE-ELEMENT TUPLE, AND THIS IS MEASURED (see the Step-0 note and F-9). Mirror the existing cross-type row's shape: take `_plan_text`'s default `status='approved'` rather than passing `status="draft"`. A `draft` plan would add `check.ipd-draft-ready-to-review` to the full-sweep set, which is the only way the authored one-element prediction could have been produced, and it buys the row nothing. RE-DRIVE the expected set at execution instead of copying any tuple from this plan; the runner compares it exactly, and a mismatch on a CLEAN row sets `clean_row_broken`, so a wrong tuple reports itself as the carve-out being broken.
  - Depends on: none
  - Expected outcome: `COLLISIONS` has one more row whose expected-rules tuple is `()`; `test_one_pass_reports_exactly_the_collisions_present` passes with it.
  - Execution state: performed

- [x] E-02 Give `tests.test_check_engine._walk_text` an optional setid parameter so E-01's fixture composes with the module's existing helper instead of inlining walkthrough text. Keep the current no-argument behavior byte-identical (no `- Set:` line emitted) so every existing caller of `_walk_text` is unaffected.
  - Depends on: E-01
  - Expected outcome: `_walk_text()` output unchanged; `_walk_text("def456", setid="topic (shared topic)")` emits the `- Set:` line inside the metadata region.
  - Execution state: performed

### Task group 2: retire the prose the defect forced

- [x] E-03 Correct the `- Set:` descriptive on the five `20260917 *closure` walkthroughs (`ryn48z`, `pi4wof`, `ztmh1b`, `zogmmg`, `k2vn8p`), each of which currently reads "because a walkthrough may not reuse the Set id of another artifact type". That clause asserts a prohibition DECISIONS D153 and spec `2lcqno` N1 reversed. Replace it with a descriptive that states the true rule (a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan). Keep each descriptive's setid token and the `Target-Id` reference unchanged, and keep the replacement inside the existing single `- Set:` line so `_parse_setid` still reads it.
  - Depends on: none
  - Expected outcome: no tracked walkthrough asserts the reversed prohibition; `rg -n "may not reuse the Set id" .aw/records/walkthroughs/` returns nothing.
  - Execution state: performed

- [x] E-04 Append a dated `## Workflow history` line to walkthrough `u8tiox` pointing at this plan, and add to `.aw/records/walkthroughs/README.md` one paragraph stating that a walkthrough MAY declare `- Set:`, that doing so is not a collision because a setid is a shared cross-type topic label (D153 / spec `2lcqno` N1), and that `set_records.write_walkthrough` does not write the field so an author adds it by hand.   Do NOT rewrite `u8tiox`'s two existing paragraphs (its `- Date:` block note and its `## A second, smaller defect` section): they are the primary-source record of the defect as it then behaved, and the appended history line is the sanctioned way to mark them superseded.
  THE HISTORY LINE MUST NAME WHAT IS NOW FALSE, NOT MERELY POINT AT THIS PLAN, because the passage it supersedes states the reversed rule as CURRENT FACT (F-11): "`check.setid-collision` treats a setid as owned by ONE record type ... so while this Set's plan is still in `pending/` a walkthrough declaring `- Set: integpath` is reported as a cross-type collision with it". A bare "see `jji5zx`" leaves a reader of that sentence believing it. The appended line must say that the cross-type arm was REMOVED by `c6648722`, that a setid is a shared cross-type topic label (D153 / spec `2lcqno` N1), that the `- Set:` omission this walkthrough explains is therefore no longer necessary (though still permitted, since the field is optional), and that the paragraphs below are retained as the primary-source record of the pre-fix behavior. `u8tiox` declares NO `- Set:` line, so nothing in this item adds or edits one.
  - Depends on: E-03
  - Expected outcome: the README states the permission; `u8tiox` carries a history line naming `jji5zx` AND naming the removed arm and the true rule, and its original narrative is byte-unchanged (addition-only diff).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The rule lives in `check_engine.check_collisions`. Its setid arm compares only WITHIN one type: the slot is `seen_sets` keyed per `(record_type, setid)`, and the comparison fires only on `"setid {sid} conflicts with {prev_path} (descriptive: ...)"`. The cross-type arm the backlog item measured emitted `"(different type: ...)"`; that string is absent from the module at HEAD.
- `check_engine.RULE_REGISTRY` registers `check.setid-collision` at severity `error` against invariant `I-16`, not `I-09`. The backlog item's `I-09` citation is stale; `check_engine` carries a comment recording the repoint.
- `check_engine._iter_type_files` skips a file when `is_retired` is true, and `is_retired` returns true on ANY path component in `_RETIRED_PATH_SEGMENTS` (which includes `executed`) or a frontmatter status in `_RETIRED_STATUSES`. The collision pass calls it with `include_retired=True` and then re-filters per file, so the setid arm still consumes the caller's population.
- `check_engine.SUPPORTED` lists `walkthroughs` with the sub-check tuple `("names",)` only, yet `check_collisions` iterates every `SUPPORTED` key regardless of that tuple. That is how a walkthrough's `- Set:` reaches the setid pass at all, and it is why a test row for walkthroughs is meaningful rather than vacuous.
- `CollisionTests.COLLISIONS` rows are 6-tuples `(case, files, exact_expected_rules, required_detail_substrings, forbidden_substrings, why)`. The runner asserts BOTH `check_collisions(root)` and `check_types(root, ["all"])`, so a row's expected set is the FULL sweep's and must include incidental content findings (a synthetic spec adds `attention.history-missing`; a `draft` plan adds `check.ipd-draft-ready-to-review`).
- THE EXPECTED SET FOR THIS PLAN'S ROW IS EMPTY, `()`, AND THE AUTHORED MEASUREMENT OF IT WAS WRONG. An earlier reading of this plan recorded "the full sweep yields exactly `['check.ipd-draft-ready-to-review']`". RE-MEASURED AT REVIEW 2026-09-28 with this module's own helpers: a pending plan via `_plan_text("aaa111", setid="topic")` plus a walkthrough declaring `- Id:` and the same `- Set:` yields `check_collisions -> []` AND `check_types(root, ["all"]) -> []`, with or without a parenthetical descriptive on either side. The `check.ipd-draft-ready-to-review` finding appears ONLY if the fixture passes `status="draft"` to `_plan_text`, which this plan never asks for and which the EXISTING cross-type row does not do either (it takes the helper's `status='approved'` default and expects just `(HISTORY_MISSING,)`, that one finding coming from the synthetic SPEC, not from the plan). Since the runner compares `_rules(all_drift) != sorted(expected)` exactly, writing the authored one-element tuple would fail the row on arrival; and because a failing CLEAN row sets `clean_row_broken`, the failure would read as the cross-type carve-out being broken rather than as a wrong expected set. Use `()`, and re-drive it rather than trusting either figure.
- `set_records.write_walkthrough` inserts `- Id:` and `- Target-Id:` and inserts them AFTER an existing `- Set:` line when one is present, but it never writes `- Set:` itself. A walkthrough's Set is therefore author-supplied, which is why the README is the right place to state the permission.
- `.aw/records/walkthroughs/README.md` is hand-maintained (no `aw:block` marker, no generator writes it), so E-04 may edit it directly.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The reported defect does not reproduce at HEAD. Building the item's exact fixture (pending plan `- Set: integpath (...)` plus a walkthrough declaring the same) and calling `check_collisions` returns `[]` at BOTH `include_retired=False` and `include_retired=True`. | Measured 2026-09-28 in this lane. |
| F-2 | It was fixed by commit `c6648722` ("setidfix: re-scope check.setid-collision to its within-type half (216rgg)"), which is an ancestor of HEAD and landed one day after the item was filed. The range the item cites inside `check_engine.check_collisions` still contains the `"(different type: ...)"` emission at the revision it measured, `36129255`. | `git merge-base --is-ancestor c6648722 HEAD` succeeds; `rg "different type" agent_workflows/check_engine.py` finds nothing. |
| F-3 | Therefore both candidate fixes the item proposes are wrong to apply. "Exempt walkthrough-vs-plan from the different-type arm" has no arm left to exempt. "Evaluate against retired AND non-retired plans" would change a DIFFERENT and deliberate behavior: `tests/test_collision_population_parity.py` asserts on two surfaces that a retired-side setid conflict is hidden by default and appears only under widening, and spec `2lcqno` Section 6 explicitly declines to decide which population wins, listing it as a non-goal. | The parity test's `assertNotIn` / `assertIn` pair on its `setid_coll_finding`; `2lcqno` Section 6 and Section 7. |
| F-4 | A real coverage gap remains, and it is the reason the regression was possible. The table's cross-type clean row uses a plan plus a SPEC. No row uses a plan plus a WALKTHROUGH, which is the shape `sovauj` reported. | `CollisionTests.COLLISIONS` row "one setid used by a plan and a spec, no descriptives"; no row pairs `PLANS` with `WALK` on a setid. |
| F-5 | The within-type arm is genuinely reachable for walkthroughs, so E-01's row is not vacuous: two walkthroughs sharing a setid with different descriptives DO report `check.setid-collision` (measured). The new row must therefore assert silence for the CROSS-type case while that within-type capability stays intact. | Measured 2026-09-28: two `integpath` walkthroughs with differing descriptives produced one finding naming both. |
| F-6 | Six tracked walkthroughs declare `- Set:`, and five of them carry a descriptive asserting "a walkthrough may not reuse the Set id of another artifact type" - a prohibition that is now false and was itself a workaround for this defect. CORRECTED AT REVIEW: the SIXTH declarer is `5gdzyz` (`20260831-locksafe-01-...`), whose `- Set: locksafe` is a BARE token with no descriptive and no false clause, so it needs no edit and is correctly absent from `- Scope-Paths:`. `u8tiox` is NOT a `- Set:` declarer at all (it has no such line, by the deliberate omission this defect forced); it is in scope for the E-04 history line only. Walkthrough `u8tiox` additionally devotes two passages to explaining the defect as live. | `rg -n "^- Set:" .aw/records/walkthroughs/` -> exactly six lines, five `*closure` files with the false clause plus `5gdzyz`'s bare `- Set: locksafe`; `rg -n "^- Set:" <u8tiox>` -> no match; `rg -c "may not reuse the Set id" .aw/records/walkthroughs/` -> exactly the five. Re-driven at review 2026-09-28. |
| F-9 | THE AUTHORED EXPECTED-SET MEASUREMENT FOR E-01's ROW IS WRONG. Step 0 recorded the full sweep yielding `['check.ipd-draft-ready-to-review']`; re-measured, both `check_collisions` and `check_types(root, ["all"])` return `[]` for the plans-plus-walkthrough fixture, with or without descriptives. The one-element prediction is reachable only by passing `status="draft"` to `_plan_text`, which neither this plan nor the existing cross-type row does. Because the runner compares the full-sweep set EXACTLY and a failing clean row sets `clean_row_broken`, the authored tuple would have failed on arrival and reported itself as the carve-out being broken. | Driven 2026-09-28 through the test module's own `_tree`/`_plan_text`/`_rules` helpers on four fixture variants (with and without descriptives, `approved` and `draft`); the `draft` variant alone produced `['check.ipd-draft-ready-to-review']`. The existing row "one setid used by a plan and a spec" read for its `(HISTORY_MISSING,)` expectation and its default status. |
| F-10 | THE FALSIFICATION V-01 DEMANDS IS SOUND BUT ITS INSTRUCTED METHOD IS UNSAFE HERE. Re-keying the enumeration by setid ALONE does make the fixture collide, so the row is genuinely load-bearing. But V-01 instructed editing `agent_workflows/check_engine.py` and reverting; that file is outside `- Scope-Paths:`, this is a shared checkout, and TWO other pending plans (`jpn6hy`, `ghna7l`) declare that exact file while `tl2b2r` declares `tests/test_check_engine.py`. | Demonstrated at review by enumerating the fixture via `check_engine._iter_type_files` + `_parse_setid` and grouping by setid alone: `setid 'topic' held by 2 files across types ['plans','walkthroughs']`, while `check_collisions` on the same tree returned `[]`. Co-editor set read from each pending plan's `- Scope-Paths:`. |
| F-11 | `u8tiox` CARRIES A THIRD NOW-FALSE PASSAGE THAT E-04 DOES NOT NAME. Beside the two passages F-6 counts, its `- Date:` block states "`check.setid-collision` treats a setid as owned by ONE record type ... so while this Set's plan is still in `pending/` a walkthrough declaring `- Set: integpath` is reported as a cross-type collision with it". That is the reversed rule stated as current fact. E-04 is right not to rewrite it (it is the primary-source record), but the appended history line must therefore be explicit enough that a reader of that paragraph learns it is superseded. | The passage read verbatim from the walkthrough at review; `rg -n "^- Set:"` on the same file returning nothing, confirming the omission the paragraph explains. |
| F-12 | THE F-8 BASELINE IS SPENT. Re-driven, `check_types(Path('.'), ['all'])` reports THREE findings (`check.ipd-uncarried-obligation`, `check.ipd-carrier-finished-unverified`, `check.system-layout-missing`), not the five the plan records, and the rule mix differs (no `check.ipd-lint-diagnostic`). The load-bearing half is unchanged and re-confirmed: `check.setid-collision` count is 0. | Driven 2026-09-28 in this lane, `collections.Counter` over the sweep's rules. Suite baseline also re-driven: `3127 passed, 2 skipped, 3 warnings in 78.55s`, and `tests/test_check_engine.py` + `tests/test_collision_population_parity.py` -> `40 passed`. |
| F-7 | `.aw/records/walkthroughs/README.md` constrains only the identity slot and `Target-Id`. It says nothing about `- Set:`, so nothing documents the permission and the next author will re-derive the same wrong conclusion the five closure walkthroughs did. | README paragraph on the naming grammar and `check.id6-identity-slot`. |
| F-8 | SUPERSEDED AT REVIEW, EXCEPT FOR ITS LOAD-BEARING HALF (see F-12). The authored baseline read 5 findings (three `check.ipd-uncarried-obligation`, one `check.ipd-lint-diagnostic`, one `check.system-layout-missing`). Re-driven 2026-09-28 the sweep reports THREE, with a different mix. What survives and is what V-04 actually needs: `check.setid-collision` count on the live tree is 0, before and after. | Measured 2026-09-28 and RE-DRIVEN at review; do not compare against the 5, which drifted with unrelated main traffic. V-04's bar is the `check.setid-collision` count staying 0, which is invariant to that drift. |

## Proposed changes (ordered, validatable)

1. E-02 first in practice (helper before the row that uses it), then E-01: extend `_walk_text` with an optional setid, add the plans-plus-walkthrough clean row, and confirm the row FAILS if the cross-type arm is restored.
2. E-03: rewrite the five closure walkthroughs' `- Set:` descriptives to state the true cross-type rule.
3. E-04: document the permission in the walkthroughs README and append a history pointer to `u8tiox` without rewriting its narrative.

Explicitly NOT changed: `agent_workflows/check_engine.py`. No behavior change is proposed, which is why the module is absent from `Scope-Paths`.

## Deferred / out of scope (with reason)

- THE ITEM'S SECOND CANDIDATE FIX ("evaluate the rule against non-retired AND retired plans so the verdict stops depending on lifecycle position"). Not applied, and not owed to a later plan either.
  - Carrier-Declined: This is a REJECTED alternative, not deferred work, and three independent sources endorse the behavior it would change. The setid pass's use of the caller's corpus is stated as deliberate in `check_engine.check_collisions` itself ("widening it would surface within-type descriptive conflicts on retired records that are not active work"); `tests/test_collision_population_parity.py` asserts on BOTH surfaces that a retired-side setid conflict is hidden by default and appears only under widening, so applying the change would retarget a passing test that exists to pin it; and open backlog item `e2j5w4`, which fixes exactly this liveness-filter class for the SIBLING identity-slot pass, explicitly instructs "keep the setid pass on the caller's corpus". Naming a carrier would schedule work three records say should not be done. The one genuinely open question in this area is the WIDER product question of whether `aw check` scans retired records for ANY rule, which approved spec `2lcqno` Section 7 lists as a declared non-goal with its reason; that question is far wider than this item and is not this plan's to hand off.
- Correcting the two stale citations inside the backlog item body (its invariant reference, since repointed to I-16, and its bare line-offset reference into `check_engine.check_collisions`, which has since drifted by roughly 550 lines).
  - Carrier-Declined: Nothing is outstanding. The backlog item is the REPORT OF RECORD of the defect as it then behaved, and this plan does not edit the artifact it graduates from. Its citations are correct against the revision it names (`36129255`), so they are historically accurate rather than wrong, and F-2 records the correction in this plan where an executor will read it. Filing a carrier would assert an obligation to rewrite a report for having described the past.
- Retro-adding `- Set:` to walkthroughs that omit it, including `u8tiox`, which omitted it as the workaround this defect forced.
  - Carrier-Declined: No obligation exists, because the field is OPTIONAL and its absence is not a defect. `set_records.write_walkthrough` never writes `- Set:` at all, so every programmatically produced walkthrough lacks it by design and a retrofit would be churn against a contract nothing asserts. E-03 corrects only the FALSE REASON recorded for an absence, which is the actual harm; E-04 documents the permission so a future author chooses freely.

## Scope check

- Over-scope: none. The plan touches one test module, one README, and six walkthrough files, all named in `Scope-Paths`. NOTE the six declared walkthrough paths are the FIVE `*closure` files E-03 corrects plus `u8tiox` (E-04's history line only); the sixth `- Set:` DECLARER in the tree, `5gdzyz`, is deliberately NOT declared and must not be edited, because its `- Set: locksafe` is a bare token carrying no false clause (F-6).
- LIVE CO-EDITORS EXIST ON THE DECLARED TEST FILE AND ON THE MODULE THIS PLAN REFUSES TO TOUCH, declared so the finalize reconciliation and the falsification route both read as expected. `tl2b2r` (`- Status: reviewed`) declares `tests/test_check_engine.py`, this plan's primary path; it adds a new cross-tree placement rule and its own test rows and does not mention `CollisionTests` or `COLLISIONS`, so the two edits do not touch the same region. `jpn6hy` and `ghna7l` both declare `agent_workflows/check_engine.py`, which is precisely why V-01's falsification must NOT write to that file even transiently (F-10). Per AGENTS.md the runner isolates each item in its own worktree and merges through a revalidation gate, so shared files are not a hazard; what would be a hazard is this plan editing an undeclared file that two other plans are queued to change.
- Under-scope: the plan does not fix a live product defect, because measurement (F-1, F-2) shows there is none to fix. If review disagrees with F-1, the correct response is to re-measure the fixture rather than to restore the removed arm, which spec `2lcqno` N5 and OQ-01 forbid (including as an `info` variant).

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py tests/test_collision_population_parity.py` must pass, run bare beyond the path arguments so the configured `addopts` apply. Re-driven at review with `-o addopts=""` for the per-test count: `40 passed`.
- The full suite `python3 -m pytest` must pass, with the `N passed` summary pasted, compared against a baseline RE-MEASURED IN THIS LANE IMMEDIATELY BEFORE THE CHANGE. Re-driven at review as `3127 passed, 2 skipped, 3 warnings in 78.55s`, zero failures; do not compare against any figure written in this plan, since this one has already drifted once.
- A falsification step for E-01, PERFORMED IN MEMORY AND NOT BY EDITING THE TRACKED MODULE. Confirm the new row FAILS against a keying that restores the cross-type comparison, because a clean row that passes against both the fixed and the broken implementation pins nothing.
  DO NOT EDIT `agent_workflows/check_engine.py` TO OBTAIN THIS, EVEN "TEMPORARILY WITH A REVERT". That file is NOT in this plan's `- Scope-Paths:` (deliberately, as this plan's own "Explicitly NOT changed" line states), this is a SHARED CHECKOUT where another party may be mid-edit, and TWO other pending plans declare that exact file right now (`jpn6hy` and `ghna7l`, with `tl2b2r` also declaring `tests/test_check_engine.py`), so a write-then-revert can race a co-worker and a failed revert would leave the repository's own collision rule mutated. Obtain the contrast without touching the tree: re-implement the removed arm's KEYING in a scratch probe (group the enumerated records by setid ALONE across types instead of by `(record_type, setid)`) and show the fixture's two files collide under it, or monkeypatch the keying inside the test process. DEMONSTRATED AT REVIEW 2026-09-28 by the first route: enumerating the fixture through `check_engine._iter_type_files` and `_parse_setid` and grouping by setid alone reports `setid 'topic' held by 2 files across types ['plans','walkthroughs']`, i.e. the row does go RED under the restored arm, while `check_collisions` on the same tree returns `[]`. State which route was used.
- `aw check all` before and after. The BAR is that `check.setid-collision` stays at 0, not that the total matches a number written here: the authored F-8 total of 5 is spent and re-measured as 3 with a different rule mix (F-12), and that total drifts with unrelated main traffic. Re-derive the total in-lane if you want it as context.

## Spec / documentation sync

- No `.spec.md` file is edited, so `Scope-Paths` declares none. Spec `2lcqno` (approved) and its N1/N5/OQ-01 already state the rule this plan pins; the code and the invariant catalog already agree with them. This plan closes the gap between those specs and the repository's own records, which is documentation, not contract change.
- `.aw/records/walkthroughs/README.md` is amended by E-04 to state the `- Set:` permission.
- The `pqsx96` invariant-catalog spec already carries the I-09-to-I-16 repoint and needs no edit.

## Open questions

### OQ-01: Should the five closure walkthroughs' corrected descriptives keep their long explanatory form, or collapse to a terse descriptive?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED BY THE REVIEWER THIS QUESTION WAS ADDRESSED TO: KEEP THE LONG FORM, with the false clause replaced by the true rule. The author's reasoning is accepted and is reinforced by two pieces of repository evidence. FIRST, the passage answers a question a reader genuinely has at that line ("why does this walkthrough's Set differ from the Set of the plan it documents?"), and the answer is still non-obvious after the fix, since the setid slot and `Target-Id` carry different things; deleting the explanation to reach terseness would leave the next author re-deriving it, which is exactly how the five reversed clauses arose in the first place. SECOND, the sixth declarer `5gdzyz` shows the terse form is ALSO legitimate in this tree (`- Set: locksafe`, bare), so this is a genuine style choice rather than a correctness one, and a plan should not churn five files toward a form the tree does not require. Confirmed harmless mechanically: `check_engine._parse_setid` takes the first whitespace token before any `(` as the setid and treats the parenthetical opaquely as the descriptive, so neither form changes what the setid pass compares; and `check.setid-collision` fires only on a DESCRIPTIVE mismatch WITHIN one type, which five walkthroughs with five distinct setids cannot trigger. The alternative (collapse to a bare token) was rejected on those grounds, not on effort. REVERSIBLE: yes, trivially, by editing five descriptives.
- NOTE ON THE `- Carrier-Declined:` LINE BELOW: it was authored while this question was `open` and remains accurate now that it is resolved, since the resolution keeps the work inside E-03 and leaves no residue.
- Carrier-Declined: No obligation survives this plan either way. This is a WORDING PREFERENCE inside E-03's own edit, not work that could be left undone: E-03 rewrites all five descriptives in this plan regardless of which form review picks, and its expected outcome (`rg -n "may not reuse the Set id"` returning nothing) is satisfied by both. Nothing outlives execution, so a carrier would assert a residual that does not exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new row verbatim from `tests/test_check_engine.py`, showing the expected-rules tuple is `()` and `"setid"` present in the forbidden tuple. Paste the passing output of `python3 -m pytest tests/test_check_engine.py -k one_pass_reports_exactly_the_collisions_present`.
    THEN PASTE THE FALSIFICATION, OBTAINED WITHOUT EDITING `agent_workflows/check_engine.py`. Paste the scratch probe (or the in-process monkeypatch) that re-keys the enumeration by setid ALONE, its output showing the fixture's plan and walkthrough colliding under that keying, and `check_collisions` on the SAME tree returning `[]`. Then paste `git status --porcelain agent_workflows/check_engine.py` EMPTY as the proof the module was never touched, which is a stronger and safer claim than a revert. Do NOT paste a diff-then-revert of that module: it is outside `- Scope-Paths:`, two other pending plans declare it, and this is a shared checkout.
  - Observed evidence: PASS. Detailed evidence recorded below:
    Verbatim row added to `tests/test_check_engine.py`:
    ```python
        (
            "one setid used by a plan and a walkthrough (the sovauj shape)",
            (
                (
                    f"{PLANS}/20260101-topic-01-aaa111-p.ipd.md",
                    _plan_text("aaa111", setid="topic", desc="shared topic"),
                ),
                (
                    f"{WALK}/20260101-topic-01-bbb222-w.walkthrough.md",
                    _walk_text("bbb222", setid="topic (shared topic)"),
                ),
            ),
            (),
            (),
            ("setid",),
            "THE sovauj SHAPE: a plan in pending and a walkthrough sharing a setid across types. "
            "The existing cross-type clean row uses plans-plus-SPECS and therefore never covered "
            "walkthroughs, leaving room for the regression sovauj reported. The walkthrough must "
            "declare its own `- Id:` so the row cannot pass by accidentally tripping "
            "`check.id6-identity-slot` instead. Expected rules is () because an approved plan and "
            "walkthrough trip no incidental rules in the full sweep",
        ),
    ```
    Passing pytest output:
    ```
    $ python3 -m pytest tests/test_check_engine.py -k one_pass_reports_exactly_the_collisions_present
    bringing up nodes...
    .                                                                        [100%]
    NOTE: 38 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    1 passed in 3.36s
    ```
    Falsification scratch probe (in-memory, without modifying `agent_workflows/check_engine.py`):
    ```python
    from collections import defaultdict
    from agent_workflows import check_engine as ce
    from tests.test_check_engine import _plan_text, _walk_text, _tree, PLANS, WALK

    files = (
        (
            f"{PLANS}/20260101-topic-01-aaa111-p.ipd.md",
            _plan_text("aaa111", setid="topic", desc="shared topic"),
        ),
        (
            f"{WALK}/20260101-topic-01-bbb222-w.walkthrough.md",
            _walk_text("bbb222", setid="topic (shared topic)"),
        ),
    )
    root = _tree(files)

    # 1. Real check_collisions on the tree:
    real_drift = ce.check_collisions(root)
    print("check_collisions(root):", [d.rule for d in real_drift])

    # 2. Keying by setid ALONE across types (the removed cross-type arm):
    by_setid = defaultdict(list)
    for rtype in ce.SUPPORTED:
        for p in ce._iter_type_files(root, rtype, include_retired=True):
            sid, desc = ce._parse_setid(p.read_text(encoding="utf-8"))
            if sid:
                by_setid[sid].append((rtype, p.name, desc))

    for sid, entries in by_setid.items():
        if len(entries) > 1:
            types = [e[0] for e in entries]
            print(f"setid {sid!r} held by {len(entries)} files across types {types}:")
            for rtype, name, desc in entries:
                print(f"  - {rtype}: {name} (desc={desc!r})")
    ```
    Output:
    ```
    check_collisions(root): []
    setid 'topic' held by 2 files across types ['plans', 'walkthroughs']:
      - plans: 20260101-topic-01-aaa111-p.ipd.md (desc='shared topic')
      - walkthroughs: 20260101-topic-01-bbb222-w.walkthrough.md (desc='shared topic')
    ```
    Git status of `agent_workflows/check_engine.py`:
    ```
    $ git status --porcelain agent_workflows/check_engine.py
    ```
    (returned empty, exit 0, confirming module was untouched)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `_walk_text` after the change, plus output of a one-liner proving `_walk_text()` is byte-identical to its pre-change output (compare against the literal `'# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n'`) and that the setid form emits `- Set:` inside the metadata region. Paste the passing result of the two collision-related test modules.
  - Observed evidence: PASS. Detailed evidence recorded below:
    `_walk_text` implementation in `tests/test_check_engine.py`:
    ```python
    def _walk_text(id6=None, setid=None):
        idline = f"- Id: {id6}\n" if id6 else ""
        setline = f"- Set: {setid}\n" if setid else ""
        return f"# Walkthrough\n\n- Date: 20260101\n{idline}{setline}\n## Summary\n\nx\n"
    ```
    One-liner verification output:
    ```
    $ python3 -c '
    from tests.test_check_engine import _walk_text
    base = _walk_text()
    expected_literal = "# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n"
    assert base == expected_literal
    print("Byte-identical check passed: _walk_text() == expected_literal")
    with_setid = _walk_text("def456", setid="topic (shared topic)")
    print("With setid output:\n" + with_setid)
    assert "- Set: topic (shared topic)\n" in with_setid
    assert with_setid.index("- Set:") < with_setid.index("## Summary")
    print("Emits - Set: inside metadata region check passed!")
    '
    Byte-identical check passed: _walk_text() == expected_literal
    With setid output:
    # Walkthrough

    - Date: 20260101
    - Id: def456
    - Set: topic (shared topic)

    ## Summary

    x

    Emits - Set: inside metadata region check passed!
    ```
    Collision-related test modules passing output:
    ```
    $ python3 -m pytest tests/test_check_engine.py tests/test_collision_population_parity.py
    bringing up nodes...
    ........................................                                 [100%]
    40 passed in 7.83s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "may not reuse the Set id" .aw/records/walkthroughs/` returning no matches, and paste `rg -n "^- Set:" .aw/records/walkthroughs/` showing all six declarer lines: the FIVE corrected `*closure` descriptives PLUS `5gdzyz`'s bare `- Set: locksafe`, which must be BYTE-UNCHANGED because it carries no descriptive and no false clause and is deliberately not in `- Scope-Paths:` (F-6). Do not read "all six with the corrected descriptives" as requiring six edits: only five files carry a descriptive to correct. Confirm each edited file's setid token is unchanged by pasting `git diff` for one of the five in full, and paste `git status --porcelain` for `5gdzyz`'s file showing it EMPTY.
  - Observed evidence: PASS. Detailed evidence recorded below:
    `rg -n "may not reuse the Set id" .aw/records/walkthroughs/`:
    ```
    $ rg -n "may not reuse the Set id" .aw/records/walkthroughs/
    (exit code 1, 0 matches)
    ```
    `rg -n "^- Set:" .aw/records/walkthroughs/`:
    ```
    $ rg -n "^- Set:" .aw/records/walkthroughs/
    .aw/records/walkthroughs/20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md:9:- Set: mnclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)
    .aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md:9:- Set: bpclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)
    .aw/records/walkthroughs/20260831-locksafe-01-5gdzyz-one-cross-platform-file-lock-walkthrough.walkthrough.md:6:- Set: locksafe
    .aw/records/walkthroughs/20260917-eiclosure-01-pi4wof-execute-item-closure-measured-not-split.walkthrough.md:9:- Set: eiclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)
    .aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md:9:- Set: irclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)
    .aw/records/walkthroughs/20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md:9:- Set: rqclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)
    ```
    Full git diff of `20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md`:
    ```diff
    diff --git a/.aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md b/.aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md
    index 5ff7e66b..7193753c 100644
    --- a/.aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md
    +++ b/.aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md
    @@ -6,7 +6,7 @@
     - Plan: `.aw/records/plans/pending/20260915-rununify-10-s16omw-split-build-parser-into-a-shared-core-and-a-thin-host-hook.ipd.md`
     - Base commit: `4a1bb873`
     - Executed by: opencode/its_direct-pt3-claude-opus-5-1m-us, in lane `aw/lane/s16omw`
    -- Set: bpclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`, because a walkthrough may not reuse the Set id of another artifact type)
    +- Set: bpclosure (this walkthrough's own Set; the plan it documents belongs to `rununify`, referenced above by `Target-Id`; a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan)

     ## What this plan did, and what it did not
    ```
    Git status of `5gdzyz`:
    ```
    $ git status --porcelain .aw/records/walkthroughs/20260831-locksafe-01-5gdzyz-one-cross-platform-file-lock-walkthrough.walkthrough.md
    ```
    (returned empty, exit 0, byte-unchanged)
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new README paragraph, paste the appended `## Workflow history` line from `u8tiox`, and paste `git diff .aw/records/walkthroughs/20260918-integpath-05-u8tiox-*.walkthrough.md` proving the diff is ADDITION-ONLY (no `-` lines other than context) so the original narrative is intact. Confirm the appended line names the removed cross-type arm and the true rule, not merely this plan's id6, since the paragraph it supersedes states the reversed rule as current fact (F-11). Paste `aw check all` output and show `check.setid-collision` is 0, which is the bar; the F-8 total of 5 is SUPERSEDED (re-measured as 3 with a different mix, F-12), so report the current total as context rather than comparing to it. Paste the bare `python3 -m pytest` summary line against a baseline re-measured in this lane immediately before the change.
  - Observed evidence: PASS. Detailed evidence recorded below:
    New `.aw/records/walkthroughs/README.md` paragraph:
    ```markdown
    A walkthrough MAY declare `- Set:`. Doing so is not a collision because a setid is a shared cross-type topic label (DECISIONS D153 / spec `2lcqno` N1), so a walkthrough and a plan on the same topic legitimately share the token. The programmatic helper (`set_records.write_walkthrough`) does not write the field, so an author adds it by hand when grouping by Set is desired.
    ```
    Appended `## Workflow history` line from `u8tiox`:
    ```markdown
    ## Workflow history

    - 2026-09-29 note (jji5zx): the cross-type setid collision arm was removed by commit `c6648722`; a setid is a shared cross-type topic label (DECISIONS D153 / spec `2lcqno` N1), so the `- Set:` omission this walkthrough explains is no longer necessary (though still permitted, since the field is optional); the paragraphs below are retained as the primary-source record of the pre-fix behavior.
    ```
    Addition-only `git diff` of `u8tiox`:
    ```diff
    diff --git a/.aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md b/.aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    index bb5acba8..187884a2 100644
    --- a/.aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    +++ b/.aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    @@ -7,6 +7,10 @@
     - Author: opencode its_direct/pt3-claude-opus-5-1m-us
     - Verified at: HEAD `36129255`

    +## Workflow history
    +
    +- 2026-09-29 note (jji5zx): the cross-type setid collision arm was removed by commit `c6648722`; a setid is a shared cross-type topic label (DECISIONS D153 / spec `2lcqno` N1), so the `- Set:` omission this walkthrough explains is no longer necessary (though still permitted, since the field is optional); the paragraphs below are retained as the primary-source record of the pre-fix behavior.
    +
     No `- Set:` line is declared here deliberately, and the reason is mechanical rather than stylistic.
     `check.setid-collision` treats a setid as owned by ONE record type, and it skips `executed/` plans as
     retired, so while this Set's plan is still in `pending/` a walkthrough declaring `- Set: integpath`
    ```
    `aw check all` output:
    ```
    AW check all
    ✗ FINDINGS 3 finding(s) detected across 1748 all
    (check.ipd-uncarried-obligation, naming grammar in backlog, check.system-layout-missing; check.setid-collision count is 0)
    ```
    Full pytest suite summary:
    Baseline: `3207 passed, 2 skipped, 3 warnings in 53.80s`
    Post-change: `3207 passed, 2 skipped, 3 warnings in 50.80s`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution (`aw ipd set approved <path> --by-human`). Execution follows the repository contract: commit only the paths in `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste actual runner output rather than claiming success. On completion with every `V-*` verified, move the plan to `.aw/records/plans/executed/` through the tooled transition.

THE ONE WAY THIS PLAN CAN DO REAL DAMAGE, stated for the executor because it is the only destructive act anywhere in its instructions: V-01's falsification originally said to restore the cross-type comparison inside `agent_workflows/check_engine.py` and then revert it. DO NOT. That module is outside `- Scope-Paths:` by this plan's own deliberate choice, this is a SHARED CHECKOUT, and two other pending plans (`jpn6hy`, `ghna7l`) declare that exact file, so a write-then-revert can race a co-worker's edit and a failed revert would leave the repository's own collision rule mutated while every suite still passed. Obtain the contrast in a scratch probe or an in-process monkeypatch, as the revised V-01 requires, and prove the module is untouched with `git status --porcelain agent_workflows/check_engine.py` returning EMPTY.

REVIEWER, READ THIS FIRST. This plan deliberately does NOT implement either fix backlog `sovauj` proposes, because Step 0 measured the reported defect as already fixed (F-1, F-2) and measured the second proposal as a change to deliberate, spec-deferred behavior (F-3). If that reasoning is accepted, the item graduates to this plan and closes on its evidence. If it is rejected, reject the plan rather than amending it to restore the removed cross-type arm: spec `2lcqno` N5 and OQ-01 forbid that arm in both `error` and `info` form, on the measurement that it reported 29 findings on this repository's own tree, every one of them endorsed behavior.

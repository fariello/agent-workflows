# IPD: Pin the cross-type setid silence sovauj reported and retire the workaround prose it forced

- Date: 2026-09-28
- Kind: child
- Concern: The defect backlog `sovauj` reports (a walkthrough declaring `- Set:` beside a pending plan of the same setid is reported `check.setid-collision`) is ALREADY FIXED in code, but nothing pins the walkthrough-vs-plan shape against regression and five tracked walkthroughs plus an undocumented README still teach the reverse rule.
- Scope: Add the missing plans-plus-walkthrough clean row to the `CollisionTests` table, correct the five tracked walkthroughs whose `- Set:` descriptive asserts the reversed prohibition, and state in the walkthroughs README that a walkthrough MAY declare `- Set:`. No change to `check_engine.check_collisions` behavior.
- Scope-Paths: tests/test_check_engine.py, .aw/records/walkthroughs/README.md, .aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md, .aw/records/walkthroughs/20260917-eiclosure-01-pi4wof-execute-item-closure-measured-not-split.walkthrough.md, .aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md, .aw/records/walkthroughs/20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md, .aw/records/walkthroughs/20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md, .aw/records/walkthroughs/20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: sovauj
- Blocks-Release: next
- Set: setidxtype
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: jji5zx

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `sovauj`; Step 0 measurement found the reported code defect already fixed by `c6648722`, so the plan is re-aimed at the regression pin and the stale prose that defect left behind.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close backlog `sovauj` honestly. The behavior it reports as broken is fixed, so this plan does NOT re-fix it; it adds the one regression pin that would have caught it (a plans-plus-walkthrough cross-type clean row, which the existing table lacks), and it retires the five tracked descriptives and the README silence that still instruct a reader to apply the removed rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the shape that regressed

- [ ] E-01 Add one row to `tests.test_check_engine.CollisionTests.COLLISIONS` whose fixture is the EXACT `sovauj` shape: a plan in `.aw/records/plans/pending/` declaring `- Set: topic (...)` plus a walkthrough under `.aw/records/walkthroughs/` declaring the SAME `- Set: topic (...)` and its own `- Id:`. Expect NO `check.setid-collision`, and add `"setid"` to the row's forbidden-substring tuple so the detail cannot mention it. The row's `why` must state that this is the `sovauj` shape, that the existing cross-type clean row uses plans-plus-SPECS and therefore never covered walkthroughs, and that the walkthrough must declare its own `- Id:` so the row cannot pass by accidentally tripping `check.id6-identity-slot` instead.
  - Depends on: none
  - Expected outcome: `COLLISIONS` has one more row; `test_one_pass_reports_exactly_the_collisions_present` passes with it.
  - Execution state: pending

- [ ] E-02 Give `tests.test_check_engine._walk_text` an optional setid parameter so E-01's fixture composes with the module's existing helper instead of inlining walkthrough text. Keep the current no-argument behavior byte-identical (no `- Set:` line emitted) so every existing caller of `_walk_text` is unaffected.
  - Depends on: E-01
  - Expected outcome: `_walk_text()` output unchanged; `_walk_text("def456", setid="topic (shared topic)")` emits the `- Set:` line inside the metadata region.
  - Execution state: pending

### Task group 2: retire the prose the defect forced

- [ ] E-03 Correct the `- Set:` descriptive on the five `20260917 *closure` walkthroughs (`ryn48z`, `pi4wof`, `ztmh1b`, `zogmmg`, `k2vn8p`), each of which currently reads "because a walkthrough may not reuse the Set id of another artifact type". That clause asserts a prohibition DECISIONS D153 and spec `2lcqno` N1 reversed. Replace it with a descriptive that states the true rule (a setid is a shared cross-type topic label, and this walkthrough carries its own Set while `Target-Id` points at the plan). Keep each descriptive's setid token and the `Target-Id` reference unchanged, and keep the replacement inside the existing single `- Set:` line so `_parse_setid` still reads it.
  - Depends on: none
  - Expected outcome: no tracked walkthrough asserts the reversed prohibition; `rg -n "may not reuse the Set id" .aw/records/walkthroughs/` returns nothing.
  - Execution state: pending

- [ ] E-04 Append a dated `## Workflow history` line to walkthrough `u8tiox` pointing at this plan, and add to `.aw/records/walkthroughs/README.md` one paragraph stating that a walkthrough MAY declare `- Set:`, that doing so is not a collision because a setid is a shared cross-type topic label (D153 / spec `2lcqno` N1), and that `set_records.write_walkthrough` does not write the field so an author adds it by hand. Do NOT rewrite `u8tiox`'s two existing paragraphs (its `- Date:` block note and its `## A second, smaller defect` section): they are the primary-source record of the defect as it then behaved, and the appended history line is the sanctioned way to mark them superseded.
  - Depends on: E-03
  - Expected outcome: the README states the permission; `u8tiox` carries a history line naming `jji5zx` and its original narrative is byte-unchanged.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The rule lives in `check_engine.check_collisions`. Its setid arm compares only WITHIN one type: the slot is `seen_sets` keyed per `(record_type, setid)`, and the comparison fires only on `"setid {sid} conflicts with {prev_path} (descriptive: ...)"`. The cross-type arm the backlog item measured emitted `"(different type: ...)"`; that string is absent from the module at HEAD.
- `check_engine.RULE_REGISTRY` registers `check.setid-collision` at severity `error` against invariant `I-16`, not `I-09`. The backlog item's `I-09` citation is stale; `check_engine` carries a comment recording the repoint.
- `check_engine._iter_type_files` skips a file when `is_retired` is true, and `is_retired` returns true on ANY path component in `_RETIRED_PATH_SEGMENTS` (which includes `executed`) or a frontmatter status in `_RETIRED_STATUSES`. The collision pass calls it with `include_retired=True` and then re-filters per file, so the setid arm still consumes the caller's population.
- `check_engine.SUPPORTED` lists `walkthroughs` with the sub-check tuple `("names",)` only, yet `check_collisions` iterates every `SUPPORTED` key regardless of that tuple. That is how a walkthrough's `- Set:` reaches the setid pass at all, and it is why a test row for walkthroughs is meaningful rather than vacuous.
- `CollisionTests.COLLISIONS` rows are 6-tuples `(case, files, exact_expected_rules, required_detail_substrings, forbidden_substrings, why)`. The runner asserts BOTH `check_collisions(root)` and `check_types(root, ["all"])`, so a row's expected set is the FULL sweep's and must include incidental content findings (a synthetic spec adds `attention.history-missing`; a `draft` plan adds `check.ipd-draft-ready-to-review`). Measured for this plan's fixture: the full sweep yields exactly `['check.ipd-draft-ready-to-review']`.
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
| F-6 | Six tracked walkthroughs declare `- Set:`, and five of them carry a descriptive asserting "a walkthrough may not reuse the Set id of another artifact type" - a prohibition that is now false and was itself a workaround for this defect. Walkthrough `u8tiox` additionally devotes two passages to explaining the defect as live. | `rg -n "^- Set:" .aw/records/walkthroughs/`; `u8tiox` lines 10-16 and its `## A second, smaller defect` section. |
| F-7 | `.aw/records/walkthroughs/README.md` constrains only the identity slot and `Target-Id`. It says nothing about `- Set:`, so nothing documents the permission and the next author will re-derive the same wrong conclusion the five closure walkthroughs did. | README paragraph on the naming grammar and `check.id6-identity-slot`. |
| F-8 | Baseline `aw check all` in this lane reports 5 errors, none of them `check.setid-collision` (three `check.ipd-uncarried-obligation`, one `check.ipd-lint-diagnostic`, one `check.system-layout-missing`). The setid rule's count on the live tree is 0. | Measured 2026-09-28; record the count before and after so V-04 can prove this plan added no finding. |

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

- Over-scope: none. The plan touches one test module, one README, and six walkthroughs, all named in `Scope-Paths`.
- Under-scope: the plan does not fix a live product defect, because measurement (F-1, F-2) shows there is none to fix. If review disagrees with F-1, the correct response is to re-measure the fixture rather than to restore the removed arm, which spec `2lcqno` N5 and OQ-01 forbid (including as an `info` variant).

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py tests/test_collision_population_parity.py` must pass, run bare beyond the path arguments so the configured `addopts` apply.
- The full suite `python3 -m pytest` must pass, with the `N passed` summary pasted.
- A falsification step for E-01: temporarily restore the cross-type comparison in `check_collisions` and confirm the new row FAILS, then revert. A clean row that passes against both the fixed and the broken implementation pins nothing.
- `aw check all` before and after, comparing finding counts to the F-8 baseline.

## Spec / documentation sync

- No `.spec.md` file is edited, so `Scope-Paths` declares none. Spec `2lcqno` (approved) and its N1/N5/OQ-01 already state the rule this plan pins; the code and the invariant catalog already agree with them. This plan closes the gap between those specs and the repository's own records, which is documentation, not contract change.
- `.aw/records/walkthroughs/README.md` is amended by E-04 to state the `- Set:` permission.
- The `pqsx96` invariant-catalog spec already carries the I-09-to-I-16 repoint and needs no edit.

## Open questions

### OQ-01: Should the five closure walkthroughs' corrected descriptives keep their long explanatory form, or collapse to a terse descriptive?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-03 preserves the long form with the false clause replaced, on the reasoning that the passage exists to explain why the walkthrough's Set differs from its subject plan's, which is still worth explaining. A reviewer preferring a terse descriptive can say so; either choice satisfies E-03's expected outcome, and neither affects `_parse_setid`, which reads the whole parenthetical opaquely.
- Carrier-Declined: No obligation survives this plan either way. This is a WORDING PREFERENCE inside E-03's own edit, not work that could be left undone: E-03 rewrites all five descriptives in this plan regardless of which form review picks, and its expected outcome (`rg -n "may not reuse the Set id"` returning nothing) is satisfied by both. Nothing outlives execution, so a carrier would assert a residual that does not exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new row verbatim from `tests/test_check_engine.py`, showing the expected-rules tuple and `"setid"` present in the forbidden tuple. Paste the passing output of `python3 -m pytest tests/test_check_engine.py -k one_pass_reports_exactly_the_collisions_present`. Then paste the FALSIFICATION: the diff that temporarily restores the cross-type comparison, the resulting FAILURE naming this row, and the confirmation (`git diff --stat agent_workflows/check_engine.py` empty) that it was reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `_walk_text` after the change, plus output of a one-liner proving `_walk_text()` is byte-identical to its pre-change output (compare against the literal `'# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n'`) and that the setid form emits `- Set:` inside the metadata region. Paste the passing result of the two collision-related test modules.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "may not reuse the Set id" .aw/records/walkthroughs/` returning no matches, and paste `rg -n "^- Set:" .aw/records/walkthroughs/` showing all six lines with the corrected descriptives. Confirm each file's setid token is unchanged by pasting `git diff` for one of the five in full.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new README paragraph, paste the appended `## Workflow history` line from `u8tiox`, and paste `git diff .aw/records/walkthroughs/20260918-integpath-05-u8tiox-*.walkthrough.md` proving the diff is ADDITION-ONLY (no `-` lines other than context) so the original narrative is intact. Paste `aw check all` output and compare its finding count to the F-8 baseline of 5 errors with 0 `check.setid-collision`. Paste the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution (`aw ipd set approved <path> --by-human`). Execution follows the repository contract: commit only the paths in `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste actual runner output rather than claiming success. On completion with every `V-*` verified, move the plan to `.aw/records/plans/executed/` through the tooled transition.

REVIEWER, READ THIS FIRST. This plan deliberately does NOT implement either fix backlog `sovauj` proposes, because Step 0 measured the reported defect as already fixed (F-1, F-2) and measured the second proposal as a change to deliberate, spec-deferred behavior (F-3). If that reasoning is accepted, the item graduates to this plan and closes on its evidence. If it is rejected, reject the plan rather than amending it to restore the removed cross-type arm: spec `2lcqno` N5 and OQ-01 forbid that arm in both `error` and `info` form, on the measurement that it reported 29 findings on this repository's own tree, every one of them endorsed behavior.

# IPD: Prove the composed control on the merged result across all four children

- Date: 2026-09-19
- Kind: child
- Concern: Spec `r07vma`'s acceptance criteria are mostly properties of the COMPOSED control, not of any one child: that exactly one function decides conformance and both consumers call it (criterion 1); that a deliverable cannot be expressed as a conforming row (criterion 3); that the probe still runs behind the shape check (criterion 9); that the two refusals are distinguishable (criterion 10); that a shape refusal spends zero model calls (criterion 11); and that the suite and `aw check all` are no worse than baseline (criterion 13). No single child can observe any of those, because each holds only its own half of the change.
  THIS CHILD EXISTS BECAUSE THE ORCHESTRATOR MAY NOT HOLD THAT WORK, which is the Set's own thesis applied to the Set. The parent `d1u4sy` is retired PROGRAMMATICALLY once its children are `executed`, with the pre-transition `E-*`/`V-*` checkpoint deliberately skipped, so a verification parked on it would be marked complete having never run. That is not hypothetical: `rh5tt6` was retired 2026-09-08 with a commit message stating "Its own `E-*`/`V-*` items were NOT performed" while its E-02 read `Execution state: pending`. Spec R1b names the remedy and the in-tree precedent is `svacmz`, which carries `- Item-Dependencies:` naming all three of its siblings for exactly this reason.
- Scope: The whole-Set verification, performed and verified by an agent turn. IN: proving criteria 1, 3, 4, 9, 10, 11 and 13 on the MERGED result of all four siblings; pinning that the semantic probe's seven functions and its test file are intact; and pinning that no second implementation of the conformance rule exists anywhere. OUT: any product change whatsoever, which is what keeps this child a verification rather than a fifth feature; and re-proving what a sibling already validated in isolation (criteria 2, 5, 6, 7, 8, 12 belong to children 01 through 04 and are CITED here, not re-run).
- Scope-Paths: tests/test_orchestrator_shape_composed.py
- Item-Dependencies: executed:dpdyed, executed:r3xk1f, executed:0xmk4e, executed:68uhp0
- Status: to-review
- Set: orchtyped
- Order: 5
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: h9cbn4
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 05 of Set `orchtyped`, and as the direct application of R1b to this Set: the whole-Set verification lives here, with `- Item-Dependencies:` naming all four siblings, rather than on the parent where it would be retired unperformed. Follows the `svacmz` precedent the spec cites, which another agent authored independently for the same reason. Adds tests and evidence only; a product change in this child's diff is a scope violation.

## Goal

Prove that the four children compose into the control spec `r07vma` specifies: one rule with two consumers, a deliverable that cannot be written into a row, a probe still standing behind the shape check, two refusals an operator can tell apart, and a suite no worse than before.

READ THE SCOPE PRECISELY: this child adds NO product code. Its whole value is that the composed properties are checked by an agent turn against the merged tree, which is the one thing the runner's programmatic retirement of the parent cannot do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the composed properties

- [ ] E-01 PROVE ONE RULE, TWO CONSUMERS (criterion 1) ON THE MERGED TREE. Show the single conformance function, show both the review-side and run-side call sites reaching it, and prove by grep that no second implementation exists: no second row pattern, no second status list, no second child-table scan in either consumer. This is the criterion most likely to have been violated quietly, because each of children 02 and 03 could have satisfied its own tests with a local copy.
  - Depends on: none
  - Expected outcome: the function named, both call sites pasted, and a grep showing no duplicate rule anywhere in `agent_workflows/`.
  - Execution state: pending

- [ ] E-02 PROVE A DELIVERABLE CANNOT BE EXPRESSED AS A CONFORMING ROW (criterion 3), using the three REAL parent-only items the spec names rather than invented fixtures: `5e4sb6` E-01 ("Produce the function-by-function INVENTORY"), `wfjsp4` E-02 ("VERIFY THE BROWSE AFFORDANCE ACTUALLY ARRIVED"), and `tb63qv` E-01 ("After both children are executed, verify the Set's combined outcome"). All three must be REFUSED.
  `wfjsp4` E-02 IS THE LOAD-BEARING CASE AND MUST BE INCLUDED. It opens with an allowlisted verb ("VERIFY") and names no child, so it would have PASSED the vocabulary rule the spec's draft proposed. It is the evidence that the by-construction claim is stronger than the detection approach it replaced, and a validation without it proves the weaker thing.
  - Depends on: E-01
  - Expected outcome: all three real items refused; `wfjsp4` E-02 explicitly among them with its verb noted.
  - Execution state: pending

- [ ] E-03 PROVE THE PROBE SURVIVED AND STILL BLOCKS (criterion 9). Show an orchestrator whose ROWS all conform but which carries an obligation in a BARE INDENTED continuation line is STILL refused, by the probe. PROVE THIS WITH A BARE INDENTED CONTINUATION LINE AND NOT WITH `## Completion criteria` (corrected at review, PR-005): that SECTION IS NOT IN THE PROBE'S PAYLOAD AT ALL. Verified in-process at review by calling `runner_shared.orchestrator_probe_excerpt` on a fixture whose `## Completion criteria` said "SOMEONE MUST MIGRATE THE DATABASE BEFORE ANY CHILD RUNS": the rendered excerpt contains only the checklist item action text and the child-table row cells, and the string is absent. `probe_cache_payload` returns exactly the two keys `e_items` and `child_table_rows`, so no prose section outside a checklist item ever reaches the model (pre-existing limit, tracked as backlog `rmcqw8`, pinned by `tests/test_orchestrator_probe.py::TheExcerptHasAKnownLIMIT`). A `- Key: value` continuation line is ALSO invisible, because `e_item_action_blocks` stops at the first line matching `ipd_lint._SUBFIELD_RE`. So the ONLY shape that demonstrates criterion 9 is a BARE indented continuation line under a conforming row; anything else reports a pass the mechanism did not earn, and this item FAILS if the evidence uses one. Then pin the probe's integrity on the merged tree: its seven functions present (`enforce_orchestrator_probe_gate`, `ask_orchestrator_probe`, `orchestrator_probe_excerpt`, `queued_orchestrator_targets`, `classify_probe_reply`, `probe_cache_payload`, `probe_refusal_remedy`) and `tests/test_orchestrator_probe.py` byte-unchanged across the whole Set's diff, not merely across one child's.
  THIS IS THE PIN FOR THE SPEC'S OWN BLOCKER FINDING. `r07vma` SR-001 records that the spec's draft proposed retiring this probe, that an approved spec (`25kzda` 2.5b) forbids substituting a syntactic rule for it, and that the substitution would have deleted 476 lines of code and 1265 lines of tests. Verifying the probe intact at the END of the Set is what makes that correction stick.
  - Depends on: E-01
  - Expected outcome: the prose-only obligation still refused by the probe; seven functions present; the probe's test file byte-unchanged across the Set.
  - Execution state: pending

- [ ] E-04 PROVE THE TWO REFUSALS ARE DISTINGUISHABLE AND THE ORDERING HOLDS (criteria 10 and 11). Paste the shape refusal and the probe refusal side by side, showing DIFFERENT rule ids, so an operator knows which control fired and therefore which remedy applies. Then show a run the shape check refused made ZERO probe invocations, asserted through the probe's injected spawn seam rather than inferred from the code path.
  - Depends on: E-03
  - Expected outcome: two refusals with distinct rule ids; zero probe invocations on a shape refusal, proven by injection.
  - Execution state: pending

### Task group 2: the Set's own bar

- [ ] E-05 ESTABLISH THE SUITE AND `aw check all` BASELINE-OR-BETTER ON THE MERGED TREE (criterion 13), and state both counts. Run the suite BARE. For `aw check all`, report the per-rule delta rather than a clean result: the repository carries pre-existing findings unrelated to this Set, so an absolute-green bar would be unsatisfiable and would invite editing the number instead of the code.
  ALSO CONFIRM CRITERION 4 BY CITATION: a conforming orchestrator and a cross-child final child coexist. The proof is this Set itself, whose parent `d1u4sy` carries five conforming rows while this child carries the cross-child verification with four sibling dependencies. Cite `svacmz` as the independent precedent rather than inventing a fixture.
  - Depends on: E-02, E-04
  - Expected outcome: suite counts before and after with failing node ids compared; per-rule `aw check all` delta; criterion 4 satisfied by this Set's own shape with the precedent cited.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PARENT IS RETIRED PROGRAMMATICALLY with the E/V checkpoint SKIPPED, which is why this child exists. `runner_shared.evaluate_set_retirement` decides on four facts (an orchestrator exists, at least one child, every child `executed`, no unresolved child-table row) and contains zero references to `E-`, `V-`, `items` or `checklist`.
- `svacmz` IS THE IN-TREE PRECEDENT for this shape: a final child carrying `- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn`, whose child-table row says it owns the verification "so it is performed and verified by an agent turn instead of being retired unperformed".
- THE PROBE'S SPAWN SEAM IS INJECTABLE BY DESIGN: `ask_orchestrator_probe`'s docstring records that every test injects it and that the real spawn is unreachable by construction, because "a test that spends tokens is not a test". E-04 uses that.
- `aw check all` CARRIES PRE-EXISTING FINDINGS unrelated to this Set, so criterion 13 is a per-rule DELTA and never an absolute green. Capture the tally before the first edit.
- SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly`. Compare failing NODE IDS, not totals.
- THIS CHILD MUST NOT CHANGE PRODUCT CODE. Its only declared path is its own test file; a product edit here would make the verification self-fulfilling.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.evaluate_set_retirement` | The parent's items are performed by nobody, so a whole-Set verification parked there is marked complete unperformed. This child is R1b's remedy applied to this Set. | zero references to `E-`/`V-`/`items`/`checklist` in that function; `rh5tt6` retired 2026-09-08 with its E-02 pending |
| F-2 | HIGH | criteria 1, 3, 9, 10, 11, 13 | Each is a property of the MERGED result and is unobservable from inside any one child, so without this child they would be claimed rather than verified. | the criteria's own wording |
| F-3 | HIGH | `wfjsp4` E-02 | It opens with "VERIFY" and names no child, so it would have PASSED the draft's vocabulary rule while being a genuine deliverable. It is the decisive case for the by-construction claim and E-02 must include it. | the item's text; the draft's allowlist measured at 11 flags of 32 ROWS AS THE SPEC DATED IT, a figure that has since moved to 38 across 12 orchestrators (re-measured at review); the 11-of-32 ratio is quoted here only as the spec's own historical measurement and must not be re-derived as current |
| F-4 | HIGH | `25kzda` 2.5b; `r07vma` SR-001 | The probe must be intact at the Set's end, because an approved spec forbids substituting a syntactic rule and the spec's own draft proposed doing so. Verifying it here is what makes the correction durable. | both spec texts; 476 lines across seven functions plus 1265 test lines |
| F-5 | MEDIUM | children 02 and 03 | Each could satisfy its own tests with a local copy of the rule, so criterion 1 is the one most likely to be quietly violated and needs a grep across the merged tree rather than per-child trust. | R3's requirement read against the two consumers' independence |
| F-6 | LOW | `aw check all` | Pre-existing unrelated findings make an absolute-green bar unsatisfiable, so criterion 13 must be a per-rule delta. | the repository's standing finding set |

## Proposed changes (ordered, validatable)

1. E-01 proves one rule and two consumers, with a grep for any duplicate.
2. E-02 proves the three real deliverables are refused, `wfjsp4` E-02 included.
3. E-03 proves the probe still blocks the prose case and is byte-intact across the Set.
4. E-04 proves the two refusals differ by rule id and that a shape refusal spends nothing.
5. E-05 establishes the suite and `aw check all` bars, and cites criterion 4 from this Set's own shape.

## Deferred / out of scope (with reason)

- ANY PRODUCT CHANGE: strictly out of scope. This child adds tests and evidence only; a product edit would make its own verification self-fulfilling. If a composed property FAILS, the remedy is a finding and a corrective plan, not a fix here.
  - Carrier-Declined: A deliberate boundary that defines this child's value; there is nothing to hand off.
- RE-PROVING WHAT A SIBLING ALREADY VALIDATED IN ISOLATION: criteria 2, 5, 6, 7, 8 and 12 belong to children 01 through 04 and are CITED here rather than re-run. Re-running them would duplicate a child's own assertion, which is the redundancy spec R1b's measurement found in three real parent rows.
  - Carrier-Declined: Owned by named siblings in this Set; citing is the correct treatment.
- TYPING THE ORCHESTRATOR'S PROSE SECTIONS so the probe becomes unnecessary: out of this Set. Spec Section 3a limit 1 records the residue as an honest limit rather than an omission.
  - Carrier: rmcqw8
- MEASURING HOW MUCH OF THE HISTORICAL VIOLATION POPULATION LIVED IN ROWS VERSUS PROSE: spec Section 3a limit 2 asks for this ratio, and E-03's prose-case fixture touches it without quantifying it across the corpus. A proper measurement needs the pre-migration census child 04 takes, so it belongs with that data. CARRIED BY THE SPEC RATHER THAN BY `68uhp0` (repointed at review, PR-001): a sibling that reaches `executed` in this same Set is a dead carrier the moment the Set completes, and this obligation is meant to OUTLIVE the Set. Spec Section 3a limit 2 is where the unanswered ratio is recorded.
  - Carrier-Evidence: .aw/records/specs/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md

## Scope check

- Over-scope: none. One declared path, its own test file, touched by every item.
- Under-scope: deliberately narrow. If proving a composed property requires a test helper that cannot live in this child's own file, that path must be DECLARED before editing; and if it requires a PRODUCT change, that is a finding to report rather than a scope amendment, because this child's separation from product code is what makes its verification meaningful.

## Required tests / validation

`python3 -m pytest` BARE on the merged tree, with the baseline measured in the executing worktree and compared by failing NODE ID rather than by total, since concurrent work moves the total.

Beyond the suite: the grep proving no second rule implementation; the three real deliverables refused; the prose-only case still refused by the probe; the probe's test file byte-unchanged across the whole Set's diff; both refusals side by side with distinct rule ids; zero probe invocations on a shape refusal via the injected seam; and the per-rule `aw check all` delta.

## Spec / documentation sync

N/A with reason: this child verifies spec `r07vma` rather than changing it, and `25kzda` 2.5b is verified intact rather than amended. No `.spec.md` path is declared. If a composed property proves unachievable as specified, that is a finding against `r07vma` to report to the maintainer, not an edit to make from inside its own implementing Set.

## Open questions

### OQ-01: If a composed property fails here, should this child report and stop, or should the Set be held open until a corrective child lands?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the honest behaviour on failure is already determined by the repository's rules: a `V-*` item whose evidence does not hold is recorded `failed` or `blocked`, the plan is not finalized, and `aw ipd finalize` refuses at the pre-transition checkpoint. So this child stops by construction rather than by choice. The question is what happens to the SET: the parent cannot retire while this child is unexecuted (retirement requires every child `executed`), so a failure here correctly holds the whole Set open, which is the desired outcome and needs no mechanism. PROPOSED DIRECTION: report the failing property as a finding, leave this child unfinalized, and let the maintainer decide between a corrective child and a scope reduction. Do NOT weaken a criterion to make this child pass; that would be the fabricated-completion failure the whole Set exists to prevent, committed by the very child meant to catch it.
- Carrier-Declined: NO OBLIGATION OUTLIVES THIS PLAN (added at review, PR-002). The failure behaviour is already determined by shipped rules rather than by a decision this plan owes: a `V-*` whose evidence does not hold is recorded `failed`, `aw ipd finalize` refuses at the pre-transition checkpoint, and `evaluate_set_retirement` cannot retire the parent while this child is unexecuted. So the Set is held open BY CONSTRUCTION. If a composed property does fail, the remedy is a corrective plan authored at that point, which is a new artifact rather than a deferred obligation.


## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: name the one conformance function and paste BOTH call sites (review-side and run-side) reaching it. Paste the grep output proving no second row pattern, no second status list and no second child-table scan exists in `agent_workflows/`. State what you searched for, since a grep that looked for the wrong thing proves nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each of the three real items and the refusal it drew: `5e4sb6` E-01, `wfjsp4` E-02, `tb63qv` E-01. `wfjsp4` E-02 must be present and its leading verb noted, because it is the case that separates by-construction from the abandoned vocabulary rule; a validation omitting it FAILS this item. Note these items may have been MIGRATED by child 04, so take their pre-migration text from git history and say which revision you read.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a fixture orchestrator whose rows all conform but which carries an obligation in a BARE INDENTED continuation line, and show it STILL refused by the probe. State that the fixture uses a bare indented line rather than a `- Key: value` subfield or a prose section, and record the LIMIT this reveals (PR-005): a conforming typed row leaves the probe almost nothing to read, since every `- Key: value` continuation line and every prose section is outside `probe_cache_payload`'s two keys. Reporting that limit is part of this item; a validation that claims broader probe coverage than the payload supports FAILS. Paste the seven probe function names resolved on the merged tree. Paste evidence `tests/test_orchestrator_probe.py` is byte-unchanged across the WHOLE Set's diff (a diff against the Set's base commit, not against one child's parent).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the shape refusal and the probe refusal side by side with their rule ids, and state in one sentence how an operator tells which remedy applies. Paste the test that injects the probe's spawn seam and asserts ZERO invocations on a shape-refused run, showing the injection rather than only the assertion.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare suite before and after, compared by failing NODE ID, naming the worktree the baseline was taken in. Paste the per-rule `aw check all` tally before and after; a rule that got worse must be explained rather than absorbed. Confirm criterion 4 by citing this Set's own shape (parent `d1u4sy` conforming while this child carries four sibling dependencies) and naming `svacmz` as the independent precedent.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 2 groups, all verification. No product code, one declared test file.
- Cohesion rationale: all five items verify ONE thing, the composed control, and each is unobservable from inside a sibling. They belong together because the Set's completion claim is their conjunction: proving one rule exists is worthless if the probe was deleted, and proving the probe survives is worthless if a deliverable can still be written into a row.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. DO NOT make a product change to make a property pass; report it as a finding instead, since this child's separation from product code is what gives its verification value.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved h9cbn4 --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until all four siblings are executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. This child is the LAST to execute, so its completion is the Set's completion.

# IPD: Verify the hostdedup Set against all six completion criteria

- Date: 2026-09-21
- Kind: child
- Concern: The `hostdedup` Set's six-criterion acceptance check is owned by nobody who will run it. It sits on the Order-0 orchestrator `a5wdne` as that plan's only `E-*` item, and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. THE PARENT ALREADY KNOWS THIS AND SAYS SO IN ITS OWN ITEM TEXT: "if the runner retires this Set, this item is marked complete WITHOUT being performed, so the criteria that only E-01 checks (the cross-Set fork count and the two Order-03 durability properties) are verified by nobody. That is a known limitation of orchestrator retirement, not something this plan can fix." IT IS FIXABLE, and this is the fix: a child that owns the verification gets an agent turn. MEASURED 2026-09-22 in run `run-20260922T003414Z-1020752`, where the orchestrator coverage probe refused a 34-set launch naming `a5wdne` among five uncovered parents (`events.jsonl`, event `orchestrator-probe-gate`).
- Scope: Perform the Set-level acceptance check `a5wdne` E-01 describes, against all SIX completion criteria, and record its evidence. IN: the fork-count measurement using the COMMITTED scanner Order 01 produces; the coupling-guard check; the third-host execution and attribution check; the pre-cutover attribution check; the research immortalization check; and a bare green suite. OUT: any lifting, unifying, guard-rewriting or host-adding work (Orders 01/02/03 own those), and any re-performance of a child's own validation - this plan READS recorded evidence and measures the COMBINED result.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:li44r9, executed:xdvglg
- Status: approved
- Work-Kind: followup
- Priority: high
- Readiness: go-pending-approval
- Set: hostdedup
- Order: 4
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 04vf1h
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-24 approved (aw set): backfill: Priority/Work-Kind derived from hostdedup orchestrator a5wdne per planprio-03 lc4unl
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; 6 findings, all FIXED; readiness go-pending-approval; typed review record under .aw/records/reviews/

- 2026-09-22 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008, all FIXED. Reviewed at HEAD `5b29bfa0`; `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after. THE PLAN'S PREMISE IS CORRECT AND VERIFIED: the parent `a5wdne` does carry its six-criterion check as its only `E-*` item, its own E-01 text does say retirement would mark it complete unperformed, `runner_shared` does call `ipd_lifecycle.retire_orchestrator`, the three children are `approved` with `Item-Dependencies` satisfied, and the parent's child table already carries the Order-04 row pointing at this file. So the coverage gap is real and this child is the right fix. EVERY FINDING IS THE SAME CLASS: the plan inherited the parent's DATED MEASUREMENTS as if they were constants, and each would have produced a FALSE NEGATIVE against a correctly-executed Set. Re-measured with the repository's own `_is_pure_delegation` predicate: the fork baseline moved 55/21/34 at `84f140da` to 58/22/36 now, so the pinned `34` is stale (PR-001). The residual target is ambiguous 5-or-3 with BOTH readings present in the parent, and measurement shows both are true at once because `initialize_run`/`execute_item` delegate to `runner_shared.*_core` while still holding 3 statements each, so they are not the one-statement wrapper the predicate counts (PR-002). Property (a) demanded a completed third-host execution where Order 03's own approved V-03 says "A DOCUMENTED WALL SATISFIES THIS ITEM" (PR-003). Property (b) pointed at `.aw/records/runs/`, which `.aw/.gitignore` ignores and which is empty in this lane, where Order 03's V-02 names a TRACKED fixture instead (PR-004). The bare green suite is unreachable and was never the parent's gate: measured `2 failed, 8521 passed`, one an ambient `OPENCODE_CONFIG_CONTENT` leak (`76 passed` with it unset) and one unrelated `commitguard` corpus drift whose own test forbids loosening (PR-005). And the falsifiability proof did not say which import spelling to use, though only `from agent_workflows.oc_runipd import` (9 still present) proves anything, since the vacuous guard already rejects `import oc_runipd` (PR-006). TWO PRE-EXISTING `aw check` ERRORS WERE ALSO CARRIED, invisible to the IPD linter, which is why both were run: the history lines had `draft` above `to-review` in a newest-first section so the derived event stream read as a backwards transition (PR-007, `check.lifecycle-transition-invalid`), and all three Deferred rows named no durable carrier so they would have vanished from `aw attention` on finalize (PR-008, `check.ipd-uncarried-obligation`). All eight fixed in place; `aw check` now reports ZERO findings for this plan (tree total 63 -> 61); OQ-02 and OQ-03 added as recorded decisions.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `a5wdne` as carrying work no child covers. The parent's E-01 had ALREADY RECORDED this exact hazard as "a known limitation of orchestrator retirement, not something this plan can fix"; this child is what makes it fixable. Content is lifted from the parent's item and its six criteria rather than invented, so the obligation is unchanged and only its owner moves; the parent's checklist stays in place.
- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the `hostdedup` Set's completion claim real. The parent specifies six criteria and correctly warns
that retirement would tick them unperformed; three of them (the cross-Set fork count and the two Order-03
durability properties) are checked by NO child V-item, so without this plan they are verified by nobody.
After this executes, "the fork is collapsed and the seam holds" rests on a measurement rather than on a
checkbox the runner filled in.

DEPENDENCY RE-POINTED 2026-09-23: `executed:nmlx47` DROPPED, leaving `executed:li44r9, executed:xdvglg`.
Order 02 (`nmlx47`) was RETIRED as `superseded`, so it will never reach `executed/`, and
`runner_shared.edge_satisfied` satisfies an `executed:` edge ONLY from the target's directory on disk
(the in-run status shortcut was removed by maintainer ruling 2026-09-19). The edge was therefore
unsatisfiable forever and no runner could dispatch this plan.

DROPPED RATHER THAN RE-POINTED, unlike Order 03's edge, and the asymmetry is deliberate: Order 03
consumes a DELIVERABLE (`HostLabels`, shipped by `li44r9`), so its edge moves to the plan that shipped
it, whereas this plan consumes nothing of `nmlx47`'s - it MEASURES the tree. Its remaining two edges
already order it after the work it must measure.

WHAT THIS CHANGES ABOUT THE MEASUREMENT, stated because dropping an edge must not quietly lower a bar.
The fork-count criterion is now measured against a Set where Order 02 did NOT execute, so the honest
expected result is that forks REMAIN, and this plan must report that number rather than treat it as a
failure of its own. Measured at `main` `50a820a6` with the committed scanner `tools/runner_fork_scan.py`:
15 divergent forks, three of which (`expand_selectors`, `_lane_reclaim_prompt`,
`_add_output_mode_flags`) are exactly the ones `nmlx47` would have lifted and which backlog
`xw4rb7`/`ga2dz1` now carry. The parent's headline criterion (34 forks down to the 5 large functions) is
therefore NOT met by this Set and this plan should say so plainly, which is the outcome `nmlx47`'s own
V-07 had already reported honestly before it was retired.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance, on the criteria no child owns

- [ ] E-01 MEASURE THE FORK COUNT WITH THE COMMITTED SCANNER, against the baseline RE-DERIVED AT EXECUTION HEAD, and state the scanner's metric. USE ORDER 01's COMMITTED SCANNER AND NOTHING ELSE: the parent's own PR-006 records that "the same AST scan that produced the baseline" DOES NOT EXIST IN-TREE - the authoring scan was ad hoc and is not reproducible - which is why Order 01 must commit one and why this criterion must be measured with THAT. THE SYMBOL COUNT IS THE GATE; line figures are indicative only, per the parent's Goal, so do not report a line delta as if it were the criterion. If the committed scanner is absent when this runs, that is an upstream failure to REPORT, not a licence to re-improvise a scan whose numbers nobody can reproduce.
  - Depends on: none
  - THE `34` IN THE PARENT'S CRITERION IS A DATED MEASUREMENT, NOT A CONSTANT, and treating it as a constant is how this item fails while looking green (PR-001, measured at review 2026-09-22 with the repository's own `_is_pure_delegation` predicate from `tests/test_rununify_execute_item.py`). At the parent's review HEAD `84f140da` the tree was 55 co-defined / 21 wrappers / 34 forks; at review HEAD `5b29bfa0` it is 58 co-defined / 22 wrappers / 36 forks. THE BASELINE MOVED UP WHILE THE SET SAT UNEXECUTED, so a report of "34 -> N" is a comparison against a tree that no longer exists. Re-derive the pre-state with the SAME committed scanner on the SAME commit the post-state is measured at (use `git stash`/`git worktree` or the scanner's own before/after mode, never a remembered figure), PASTE BOTH, and state the drift from 34 explicitly with the commits named. A drift is a REPORTABLE FACT, not a failure of this item.
  - THE TARGET IS `5` OR `3` DEPENDING ON THE SET'S OWN SCOPE, AND THE TWO ANSWERS ARE BOTH WRITTEN IN THE PARENT (PR-002). The Completion criteria say "fallen from 34 to the five large functions alone"; the parent's Deferred section says `initialize_run` (commit `7a28ed11`) and `execute_item` (commit `70a2059f`) are ALREADY unified and "only 3 of the 5 remain forked". MEASURED AT REVIEW, BOTH ARE TRUE AT ONCE AND THAT IS THE TRAP: `initialize_run` and `execute_item` now delegate to `runner_shared.initialize_run_core` / `execute_item_core`, but each host's copy carries 3 statements (host options, two spawn closures), so the shared-core delegation is NOT the one-statement `_is_pure_delegation` wrapper shape the predicate counts, and they still register as forks. So report the residual set BY NAME rather than as a bare number, and state for each whether it is a full fork, a shared-core delegation, or a sanctioned wrapper. A report of "5 remain" or "3 remain" with no names is not evidence and FAILS V-01.
  - Expected outcome: pasted scanner invocation and output with its metric stated, showing the re-derived before AND after symbol counts at named commits, the drift from the parent's `34` stated explicitly, and the residual forked symbols listed BY NAME with each classified (full fork / shared-core delegation / sanctioned wrapper); plus the scanner's own path in-tree, proving it is committed rather than ad hoc.
  - Execution state: pending

- [ ] E-02 VERIFY THE COUPLING GUARD REJECTS THE COUPLING RATHER THAN ONE SPELLING, and prove the guard is not vacuous. Two halves: confirm no runner imports the other runner, and confirm the guard FAILS against a reintroduction. THE VACUITY IS MEASURED, NOT HYPOTHETICAL, AND IT IS STILL PRESENT AT REVIEW HEAD: `agy_runipd.py` contains 9 imports spelled `from agent_workflows.oc_runipd import` (counted 2026-09-22), while the guard row in `test_review_findings_cascade.py` forbids only the substring `"import oc_runipd"` and PASSES. So a green guard proves nothing by itself; demonstrate falsifiability by reintroducing a coupling in a scratch copy and showing the guard rejects it.
  - Depends on: E-01
  - MEASURE BOTH SPELLINGS, since the whole defect is that one was checked and the other was not. Report the COUNT of `from agent_workflows.oc_runipd import` and of `from agent_workflows.agy_runipd import` in BOTH runners, not merely a pass/fail. A green guard beside a nonzero count is the exact vacuity this item exists to catch, and it must be reported as a Set FAILURE rather than as a pass.
  - THE FALSIFIABILITY PROOF MUST USE THE SPELLING THE OLD GUARD MISSED. Reintroducing a coupling written `import oc_runipd` would be rejected by even the vacuous guard and proves nothing; the scratch reintroduction MUST use the `from agent_workflows.oc_runipd import X` form. Work in a throwaway copy OUTSIDE the tracked tree (a `tempfile` directory, never an edit to `agent_workflows/` that could be committed), since the scope fence forbids product-code changes.
  - Expected outcome: pasted guard output green on the real tree WITH both import counts stated; PLUS pasted output of the same guard FAILING against a scratch copy re-coupled in the `from agent_workflows.oc_runipd import` form, naming the assertion that fires and the scratch path used.
  - Execution state: pending

- [ ] E-03 VERIFY THE THREE REMAINING CRITERIA AND CLOSE THE SET, each with its own evidence: (a) a third host completes a real IPD execution with NO runner module of its own and attributes to that host rather than `unknown`; (b) a PRE-CUTOVER run record still attributes correctly, per the maintainer's host-id ruling; (c) the measured host contract is immortalized under `.aw/records/research/` so the codex/claude/hermes work starts from it. Then (d) paste the suite result per the SUITE RULE below. Items (a) and (b) are the two Order-03 durability properties the parent names as checked by no child V-item, which is precisely why they are here; read Order 03's recorded evidence for them and REPORT rather than compensate if it is absent.
  - Depends on: E-02
  - PROPERTY (a) HAS A SANCTIONED WEAKER FORM AND THIS ITEM MUST ACCEPT IT (PR-003). Order 03's own V-03 says "A DOCUMENTED WALL SATISFIES THIS ITEM; a completed end-to-end execution is not required", so if Order 03 recorded a documented wall instead of a completed run, THAT is the correct evidence and this item reports the wall plus which of the three predicted walls materialized. Demanding a completed execution here would contradict the child's own approved acceptance bar and would make this item unsatisfiable by a correctly-executed Set. What is NOT acceptable is silence: a Set closed with neither a run record nor a documented wall FAILS.
  - PROPERTY (b) READS A TRACKED FIXTURE, NOT `.aw/records/runs/` (PR-004). Order 03's V-02 pins the pre-cutover record to the tracked fixtures at `tests/test_run_analytics_sources.py` and states explicitly that `.aw/records/runs/` is gitignored and ABSENT FROM EVERY LANE - confirmed at review: `.aw/.gitignore` ignores `records/runs/` and the directory is empty in this lane. So look for the attribution evidence in Order 03's recorded V-02 block and in the tracked fixture; do NOT go looking for a run directory, and do NOT report its absence as the Set failing.
  - THE SUITE RULE, WHICH A BARE `python3 -m pytest` DOES NOT SATISFY HERE (PR-005). The parent's criterion is NO NEW failures against a baseline taken THE SAME WAY, never an absolute green. Measured at review HEAD `5b29bfa0` in this lane: a bare run gives `2 failed, 8521 passed, 3 skipped, 2 xfailed`, and BOTH failures are environmental or corpus drift unrelated to this Set - `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` fails only because the ambient `OPENCODE_CONFIG_CONTENT` leaks into the test's environment (the same file is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`), and `tests/test_orchestrator_retirement.py::RealRepositorySets` fails on the unrelated `commitguard` Set's own child advancing, which that test's message says to re-point rather than loosen. So: paste the run, state the invocation form, and CLASSIFY each failure as pre-existing or attributable to this Set, citing the same test's behavior on an unmodified tree. Reporting a red suite as the Set failing, or editing an unrelated test to reach green, both FAIL this item.
  - Expected outcome: one evidence block per property (a)-(d): the third-host run id and its recorded attribution quoted OR the documented wall with its predicted-wall classification; the tracked pre-cutover fixture named with its attribution quoted; the research path named; and the suite invocation plus summary line pasted with every failure classified pre-existing or attributable.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `a5wdne` except its child table.
- THE RETIREMENT HAZARD IS DOCUMENTED IN THE PARENT ITSELF, which is unusual and worth preserving: `a5wdne` E-01 names it and calls it unfixable from there. Leave that text in place; it is the evidence for why this child exists.
- SYMBOL COUNTS OVER LINE COUNTS in this Set, stated by the parent's Goal: the symbol figures reproduced exactly at review while the line figures did not, so the criteria are written against symbols.
- BUT A SYMBOL COUNT IS STILL A DATED MEASUREMENT, not a constant. Re-measured 2026-09-22 with the repository's own `_is_pure_delegation` predicate (`tests/test_rununify_execute_item.py`): 34 forks at the parent's review HEAD `84f140da`, 36 at `5b29bfa0`. The lesson generalizes beyond this plan: a verification plan must RE-DERIVE its baseline at execution time, because the interval between authoring and execution is exactly when the number moves.
- THE REPOSITORY ALREADY OWNS A DELEGATION PREDICATE, so a scanner must not invent a second definition of "forked". `_is_pure_delegation` is what the four `STILL_DOUBLE_DEFINED` pin tables assert against, so a scanner using a different notion would produce a number that disagrees with the guards for no visible reason.
- A LANE SUITE IS NOT EXPECTED TO BE GREEN and the parent says so ("no NEW failures against a baseline taken the same way"). Two unrelated failures exist at review HEAD, one purely environmental. Treat a red suite as something to CLASSIFY, never as a licence to edit an unrelated test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `run-20260922T003414Z-1020752/events.jsonl`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `a5wdne` among five uncovered parents. Without this child the six-criterion check is performed by nobody and reported complete. |
| F-02 | HIGH | `a5wdne` E-01, quoted | The parent states that three criteria - the cross-Set fork count and the two Order-03 durability properties - are checked by NO child V-item, and that retirement would mark them complete unperformed. Those three are the core of this plan. |
| F-03 | HIGH | `a5wdne` PR-006, quoted | The reproducible scanner the fork-count criterion needs DID NOT EXIST in-tree at authoring; Order 01 must commit one. So E-01 must consume THAT scanner and must refuse to re-improvise, or the headline number becomes unreproducible again. |
| F-04 | MEDIUM | `a5wdne` completion criteria, quoted; re-measured at review 2026-09-22 (`agy_runipd.py` still holds 9 `from agent_workflows.oc_runipd import` lines while the guard row in `test_review_findings_cascade.py` forbids only the substring `"import oc_runipd"`) | The coupling guard was measured VACUOUS and STILL IS at review HEAD. A green guard is therefore not evidence; E-02 requires a falsifiability demonstration in the spelling the guard misses. |
| F-05 | HIGH | Review 2026-09-22, `_is_pure_delegation` from `tests/test_rununify_execute_item.py` applied at `84f140da` and at `5b29bfa0` | THE `34` BASELINE DRIFTED WHILE THE SET SAT UNEXECUTED: 55 co-defined / 21 wrappers / 34 forks at the parent's review HEAD, versus 58 / 22 / 36 now. An execution comparing its post-state against the remembered `34` measures against a tree that no longer exists. E-01 must re-derive the pre-state with the same scanner at a named commit. |
| F-06 | HIGH | `a5wdne` Completion criteria ("to the five large functions alone") versus `a5wdne` Deferred ("only 3 of the 5 ... remain forked"); measured at review | THE RESIDUAL TARGET IS AMBIGUOUS, 5 OR 3, AND BOTH READINGS ARE IN THE PARENT. `initialize_run` and `execute_item` DO delegate to `runner_shared.*_core` yet each host copy holds 3 statements, so they are not the one-statement wrapper shape the pin predicate counts and still register as forks. E-01 must report residuals BY NAME and classify each, never as a bare count. |
| F-07 | MEDIUM | `xdvglg` V-03 ("A DOCUMENTED WALL SATISFIES THIS ITEM"), V-02 (tracked fixture, `.aw/records/runs/` gitignored); `.aw/.gitignore` ignores `records/runs/` | TWO OF THIS PLAN'S CRITERIA WOULD HAVE BEEN OVER-DEMANDED. Property (a) is satisfied by a documented wall per the child's own approved bar, and property (b)'s evidence lives in a TRACKED fixture because `.aw/records/runs/` is absent from every lane. E-03 now states both. |
| F-08 | HIGH | Review 2026-09-22 bare run in this lane: `2 failed, 8521 passed, 3 skipped, 2 xfailed`; `tests/test_turn_bounds.py` is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT` | A BARE GREEN SUITE IS NOT REACHABLE AND WAS NOT THE PARENT'S CRITERION. Both failures are environmental or unrelated corpus drift (`commitguard`'s own child advanced). The parent's gate is NO NEW failures against a like-for-like baseline; E-03 now requires per-failure classification instead of green. |
| F-09 | HIGH | `aw check` rule `check.lifecycle-transition-invalid` (error, deterministic); reproduced with `ipd_lifecycle.validate_transition`: `to-review -> draft` "missing predecessor: backwards transition" | THE `## Workflow history` LINES WERE IN THE WRONG ORDER (`draft` printed above `to-review` in a NEWEST-FIRST section), so the derived event stream read as a backwards transition and the plan carried a deterministic error-severity finding. Fixed by reordering the two 2026-09-21 lines; both transitions now validate. |
| F-10 | HIGH | `aw check` rule `check.ipd-uncarried-obligation` (error, post-cutover severity): "3 obligation(s) name no durable carrier" | ALL THREE `## Deferred / out of scope` ROWS NAMED NO DURABLE CARRIER, so once this plan reached `executed` each would class `done` in `aw attention` and vanish with no record. Each is in fact a handoff to a named sibling, so the carriers are `li44r9` (lifting/unifying work and the committed scanner) and `xdvglg` (the children's own validation). Added as `- Carrier:` fields. |

## Proposed changes (ordered, validatable)

1. Measure the fork count with Order 01's committed scanner, stating its metric, re-deriving the baseline at a
   named commit, and naming the residual symbols rather than counting them (E-01).
2. Verify the coupling guard is green with both import spellings counted, and falsifiable in the spelling the
   old guard missed (E-02).
3. Verify the third-host (run record OR the sanctioned documented wall), pre-cutover (tracked fixture) and
   research criteria, then run the suite and classify every failure pre-existing or attributable (E-03).

## Deferred / out of scope (with reason)

- ALL LIFTING, UNIFYING, GUARD-AUTHORING AND HOST-ADDING WORK. Orders 01, 02 and 03 own those; this plan
  measures their combined effect, which is why `Scope-Paths` names only records and no product code.
  - Carrier: li44r9
- COMMITTING THE SCANNER. That is Order 01's E-01 deliverable. If it is missing, E-01 here REPORTS the
  upstream gap rather than filling it, because a scanner authored by the verifier is not an independent
  measurement.
  - Carrier: li44r9
- RE-PERFORMING ANY CHILD'S VALIDATION. E-03 reads Order 03's recorded evidence for the two durability
  properties; compensating for absent evidence would hide an upstream validation failure.
  - Carrier: xdvglg

## Scope check

- Over-scope: none.
- Under-scope: none remaining. The parent carries exactly one `E-*` item enumerating six criteria; E-01 covers
  the first, E-02 the second, and E-03 the remaining four including the suite.
- Under-scope, closed at review (2026-09-22): the fork-count baseline was pinned to a figure that had already
  drifted 34 -> 36 (PR-001/F-05, now re-derivation plus a named-commit before/after in E-01); the residual
  target was ambiguous between 5 and 3 with both readings present in the parent (PR-002/F-06, now a by-name
  classified residual set); property (a) over-demanded a completed execution where the child's own V-03
  sanctions a documented wall (PR-003/F-07); property (b) pointed at a gitignored run directory absent from
  every lane rather than the tracked fixture the child names (PR-004/F-07); the suite criterion was written as
  a bare green when the parent's gate is no-NEW-failures and two unrelated failures exist at HEAD
  (PR-005/F-08); and the falsifiability proof did not say which import spelling it must use, the one detail
  that decides whether the demonstration means anything (PR-006, now stated in E-02).

## Required tests / validation

No product code changes, so no new unit test. The validation IS the pasted measurement set, plus the suite
run in E-03.

THE SUITE CRITERION IS "NO NEW FAILURES", NOT "GREEN", and the distinction is load-bearing here rather than
pedantic (PR-005). The parent states it explicitly: "The suite shows NO NEW failures against a baseline taken
THE SAME WAY ... The gate is NO NEW failures against a baseline taken the same way, never an absolute count."
Measured at review HEAD `5b29bfa0` in this lane, a bare `python3 -m pytest` is `2 failed, 8521 passed, 3
skipped, 2 xfailed`, and neither failure belongs to this Set:

- `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
  fails because the ambient `OPENCODE_CONFIG_CONTENT` leaks into the environment the test inspects; the same
  file is `76 passed` under `env -u OPENCODE_CONFIG_CONTENT`. Environmental, not a defect this Set introduced.
- `tests/test_orchestrator_retirement.py::RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason`
  fails on the unrelated `commitguard` Set, whose child `y9vpvv` reached `executed`. That test's own message
  says to RE-MEASURE and re-point the row, "NEVER to loosen the assertion", and it is not this plan's row.

An executor must therefore state its invocation form and classify each failure. Editing either test to reach
green would be an out-of-scope product change AND would destroy a deliberate real-repository assertion.

NOTE THE SECOND-ORDER EFFECT OF THIS PLAN'S OWN EXISTENCE on that retirement test: authoring a child changes
a Set's child table and status set, which is precisely the kind of corpus drift `RealRepositorySets` pins. If
that test goes red naming `hostdedup`, the remedy is to re-point the row, never to delete this child.

## Spec / documentation sync

N/A. This plan changes no contract: it performs a verification the parent already specified. The only
structural edit is the child-table row on `a5wdne`, which is what the coverage gate reads.

## Open questions

### OQ-01: If Order 01's committed scanner is absent when this runs, does this plan improvise one or refuse?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REFUSE AND REPORT, resolved from the parent's own PR-006 rather than deferred. That finding exists precisely because the authoring scan was ad hoc and unreproducible, so the criterion was rewritten to demand a committed scanner. A verifier that authors its own scanner to unblock itself reproduces the original defect (a headline number nobody else can re-derive) AND destroys the independence that makes the measurement worth anything. E-01's expected outcome therefore requires the scanner's in-tree path, which is what makes an improvised scan detectable rather than silent.

### OQ-02: Is the residual target after this Set FIVE forked large functions or THREE?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NEITHER NUMBER IS THE ANSWER; THE NAMED SET IS (PR-002/F-06, resolved from
  repository measurement rather than deferred to the maintainer, because the repository answers it and the
  answer is that the question is mis-posed). Both figures are in the parent: its Completion criteria say "to
  the five large functions alone" and its Deferred section says `initialize_run` (`7a28ed11`) and
  `execute_item` (`70a2059f`) are already unified so "only 3 of the 5 ... remain forked". Measured at review
  with the repository's own `_is_pure_delegation` predicate, BOTH are accurate descriptions of different
  things: those two symbols DO delegate to `runner_shared.initialize_run_core` / `execute_item_core`, and they
  ALSO still count as forks, because each host copy holds three statements (host options plus two spawn
  closures) rather than the single-statement wrapper the predicate recognizes. So a verifier reporting either
  bare number can be contradicted by the other reading, and neither tells a reader what is actually left.
  E-01 therefore reports residuals BY NAME with a classification per symbol, which is strictly more
  informative and cannot be gamed by choosing a denominator. This is REVERSIBLE: a later maintainer who wants
  a single headline number can derive it from the named set, whereas the reverse is impossible.

### OQ-03: The suite is not green at review HEAD. Does this plan report that as the Set failing?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO - CLASSIFY, resolved from the parent's own stated gate (PR-005/F-08).
  The parent's sixth criterion is "NO NEW failures against a baseline taken THE SAME WAY ... never an absolute
  count", so a bare green was never the contract and this plan's original wording was stricter than the
  criterion it claims to verify. Measured at review: `2 failed, 8521 passed`, one an ambient
  `OPENCODE_CONFIG_CONTENT` leak (`tests/test_turn_bounds.py` is `76 passed` with it unset) and one unrelated
  corpus drift in `RealRepositorySets` caused by the `commitguard` Set's child advancing. Reporting either as
  this Set failing would be a false negative that strands the Set; "fixing" either would be an out-of-scope
  product edit, and in the second case would loosen a real-repository assertion the test explicitly forbids
  loosening. E-03 therefore requires per-failure classification with the like-for-like evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the scanner's committed in-tree path, its invocation, its stated metric, BOTH the re-derived before count and the after count with the commit each was taken at, the drift from the parent's `34` stated explicitly, and the residual forked symbols listed BY NAME with each classified full fork / shared-core delegation / sanctioned wrapper. FOUR WAYS TO FAIL THIS ITEM, each measured as a real hazard: reporting a LINE delta as the criterion; running a scan with no committed in-tree path; comparing the post-state against the remembered `34` instead of a re-derived baseline (F-05: the tree moved 34 -> 36 while the Set waited); or reporting a bare residual count with no names (F-06: `5` and `3` are both defensible readings of the parent, so only the named set is evidence).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: two pasted runs of the coupling guard - green against the real tree WITH the counts of `from agent_workflows.oc_runipd import` and `from agent_workflows.agy_runipd import` in both runners stated, and FAILING against a scratch copy re-coupled in the `from agent_workflows.oc_runipd import` form, naming the assertion that fires and the scratch path. A single green run does NOT satisfy this item; F-04 records that a vacuous guard passed here while 9 real couplings existed AND that both conditions still hold at review HEAD. A falsifiability proof using the `import oc_runipd` spelling also FAILS, because the vacuous guard already rejected that spelling.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: four labelled blocks. (a) the third host's run id plus its recorded attribution showing the host name and not `unknown`, OR the documented wall Order 03's own V-03 sanctions, with which predicted wall materialized; (b) the TRACKED pre-cutover fixture named (per Order 03's V-02; `.aw/records/runs/` is gitignored and absent, so its absence is not evidence of anything), with its attribution quoted; (c) the `.aw/records/research/` path holding the host contract; (d) the suite invocation form plus its summary line, with EVERY failure classified pre-existing or attributable to this Set. Demanding a completed third-host execution where Order 03 recorded a wall FAILS this item, as does reporting an absolute green as the suite criterion (F-08: the parent's gate is no NEW failures against a like-for-like baseline, and two unrelated failures exist at review HEAD). If (a) or (b) rests on absent Order-03 evidence, the required evidence is the STATEMENT of that gap, which satisfies this item while failing the Set.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE. This plan's entire product is a verification, so there is nothing
to show but real output. Two specific temptations are named because both have already occurred in this
Set's history: improvising a fork-count scan when the committed one is missing (which is how the original
unreproducible number arose), and accepting a green coupling guard as proof when that guard was measured
vacuous while nine real couplings existed. In both cases the correct result is a named refusal or a
falsifiability demonstration, never a substitute measurement.

THE OPPOSITE FAILURE IS ALSO A FAILURE, AND IT IS THE MORE LIKELY ONE (added at review). A verifier whose
only failure mode is over-credulity would be improved by strictness, but this plan verifies a Set whose
criteria were written five days before execution, so its realistic failure is a FALSE NEGATIVE: reporting the
Set as incomplete because a baseline drifted (34 -> 36, measured), because the suite is not absolutely green
(2 unrelated failures, measured), because Order 03 recorded a documented wall its own approved V-03 sanctions,
or because `.aw/records/runs/` is absent from a lane where it is gitignored by design. Each of those would
strand a correctly-executed Set behind a verification defect. So the rule cuts both ways: report what is
measured, compare against a baseline re-derived the same way, and never convert an unrelated or environmental
condition into a verdict about this Set.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO product code, author NO scanner, and EDIT NO
TEST - including the two failing at review HEAD, which are environmental and unrelated corpus drift
respectively, and one of which explicitly forbids loosening its assertion. The E-02 falsifiability
demonstration MUST be performed in a throwaway copy outside the tracked tree (a `tempfile` directory), never
by editing `agent_workflows/` and reverting. If the work genuinely requires a path outside the fence, make the
edit and justify it, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a
`--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.

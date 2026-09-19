# IPD: Make an orchestrator checklist a typed child-tracking row so a deliverable cannot be written into one

- Date: 2026-09-19
- Kind: orchestrator
- Concern: An Order-0 orchestrator is retired PROGRAMMATICALLY, with no agent turn and with the pre-transition `E-*`/`V-*` checkpoint deliberately skipped, so a parent item that requires an agent to DO something can never be performed and is marked complete having never run. Measured in production 2026-09-08: `aw oc run` retired `rh5tt6` with a commit message stating "Its own `E-*`/`V-*` items were NOT performed" while its E-02 still read `Execution state: pending` and its V-02 was blank. The existing control is a MODEL PROBE (`77tr3o` R-12, `25kzda` 2.5b) which catches the prose case a parser cannot, but it cannot repair, it spends a model call on the tidy case, it fails open on availability, and it leaves the violation EXPRESSIBLE so its job is to notice afterwards. Approved spec `r07vma` closes that last gap by making a deliverable unwriteable in a checklist row at all.
- Scope: Implement approved spec `r07vma` (`- Status: approved`, human-attested 2026-09-19) end to end. IN: the typed row grammar and the ONE shared validation function (R1a, R3); the `/plan-review` bounded repair loop with honest exhaustion (R5, R6, R7); both runners' pre-queue shape check, batch-reported and ordered AHEAD of the probe (R8, R9); the migration of every pending orchestrator (Section 5 cost 3, criterion 12); and the cross-Set proof no single child can perform (criterion 13, and R1b applied to this Set itself). OUT: retiring or weakening the semantic probe, which `25kzda` 2.5b forbids and criterion 9 pins as still running; teaching `ipd_lint` a `Kind` special case beyond calling the shared function (`77tr3o` OQ-1 shape (a) stays rejected); OQ-01's render-instructions-from-the-rule direction, which is explicitly non-blocking; and any change to `evaluate_set_retirement`'s four eligibility facts.
- Scope-Paths: .aw/records/plans/pending/20260919-orchtyped-01-dpdyed-land-the-typed-child-tracking-row-grammar-and-its-one-shared.ipd.md, .aw/records/plans/pending/20260919-orchtyped-02-r3xk1f-wire-the-shape-check-into-plan-review-as-a-bounded-repair-lo.ipd.md, .aw/records/plans/pending/20260919-orchtyped-03-0xmk4e-wire-the-shape-check-into-both-runners-ahead-of-the-probe-an.ipd.md, .aw/records/plans/pending/20260919-orchtyped-04-68uhp0-migrate-every-pending-orchestrator-checklist-to-the-typed-ro.ipd.md, .aw/records/plans/pending/20260919-orchtyped-05-h9cbn4-prove-the-composed-control-on-the-merged-result-across-all-f.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: orchtyped
- Order: 0
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: d1u4sy
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history
- 2026-09-19 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, none deferred, none open. Readiness go-pending-approval. Record: .aw/records/reviews/20260919-orchtyped-00-d1u4sy-make-an-orchestrator-checklist-a-typed-child-tracking-row-so.review.md. SELF-REVIEW (same agent/model authored the Set), so its value rests on EXECUTING the claims: every named resolver was called in-process, the carrier predicate was driven with a simulated post-retirement index, and the probe payload was rendered on purpose-built fixtures. TWO BLOCKERS, both measured rather than predicted. PR-001: seven deferred rows named 'Carrier: d1u4sy', the orchestrator the runner RETIRES, and check_engine._CARRIER_TERMINAL_STATUSES refuses a terminal-only carrier, so each obligation died at the instant no agent turn remained - the Set's own failure mode in its own front matter. Repointing at siblings was NOT enough (simulating the whole Set executed left three rows dead); the three Set-outliving ones now carry Carrier-Evidence on approved spec r07vma. PR-002: all six plans FAILED 'aw ipd lint --phase pre-transition' at error severity on their own open OQ-01, because CARRIER_CUTOVER_DATE is 20260919 and these are the first plans past it - the Set could not have finalized any child. THREE MORE CHANGED THE WORK. PR-003: child 01 E-02 was told to resolve the child id6 via parse_child_table, which returns NO id6 (ChildTableResult._fields is ('rows','reason'); order_to_id is an INPUT), dead-ending the executor and pushing it toward the fresh scan the same item forbids; the Id cells are in runner_shared.child_table_rows, and 6 of 12 live orchestrators have no Id column at all. PR-005: criterion 9's test would have been a FALSE GREEN - a '## Completion criteria' obligation is absent from orchestrator_probe_excerpt entirely and a '- Context:' continuation line is invisible too (e_item_action_blocks stops at _SUBFIELD_RE), so only a BARE indented line demonstrates it; the same measurement shows a conforming typed row shrinks the parent's payload to five bare strings, which child 04's relocation guidance now accounts for. PR-007: child 02 aimed at plan-review-long.md, a step INDEX, which an existing test refuses because the mistake 'has been made twice'. Also PR-004 (476 is an AST span, 442 non-blank; the 32-row denominator is 38/12 today), PR-006 (rewriting a row stales a live begin receipt via frozen_region_digest, the real mechanism behind child 04's mid-flight question) and PR-008. NO criterion was relaxed: every fix made a demand MORE specific, and criterion 9 is now harder to satisfy than as authored. Validation: bare pytest 7306 passed, 3 skipped, 2 xfailed (fully green); aw check all 247 -> 241 with all six orchtyped findings cleared; author and review-finalize lint conform on all six plans.

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` at the maintainer's instruction. THIS ORCHESTRATOR IS WRITTEN IN THE GRAMMAR ITS OWN SET INTRODUCES (R1a), which is deliberate: a parent specifying a typed row while carrying prose deliverables would refute the Set on its face, and it gives the executor of child 01 a live conforming fixture to test against. Consequently the whole-Set verification lives in child 05 with `- Item-Dependencies:` naming all four siblings, per R1b and following the `svacmz` precedent the spec cites. Every anchor below was measured at HEAD `21eff5d8` rather than carried from the spec.

## Goal

Make spec `r07vma` real: one shared function that validates an orchestrator's checklist rows as typed child-tracking rows, called by `/plan-review` (where a violation can be repaired) and by both runners (where it refuses before spending anything), with every pending orchestrator migrated and the semantic probe left intact behind it.

READ THE GOAL PRECISELY: this Set does not make the probe redundant and does not try to. R1a governs ROWS; the continuation lines and the orchestrator's prose sections are deliberately unparsed, and remain the probe's business. A child that removes the probe has left this Set's scope.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: track the children in dependency order

- [ ] E-01 CONFIRM dpdyed REACHED executed
  - Depends on: none
  - Expected outcome: dpdyed reads `- Status: executed` on disk.
  - Execution state: pending
  - Context, not an obligation (R1a: continuation lines are not parsed): child 01 lands the grammar and the one shared function. It must be first because every other child calls that function rather than re-deriving the rule.

- [ ] E-02 CONFIRM r3xk1f REACHED executed
  - Depends on: E-01
  - Expected outcome: r3xk1f reads `- Status: executed` on disk.
  - Execution state: pending
  - Context: child 02 wires the review-side repair loop. It follows child 01 because it consumes the shared function, and it precedes child 04 because the migration is easier once review can repair a violation it reports.

- [ ] E-03 CONFIRM 0xmk4e REACHED executed
  - Depends on: E-01
  - Expected outcome: 0xmk4e reads `- Status: executed` on disk.
  - Execution state: pending
  - Context: child 03 wires the run-side check. It needs only child 01, not child 02, so the runner and review halves are independently reviewable.

- [ ] E-04 CONFIRM 68uhp0 REACHED executed
  - Depends on: E-03
  - Expected outcome: 68uhp0 reads `- Status: executed` on disk.
  - Execution state: pending
  - Context: child 04 migrates every pending orchestrator. It follows child 03 so the migration is verified against the same check a run will apply, and criterion 12 forbids it leaving any Set refused with no remedy.

- [ ] E-05 CONFIRM h9cbn4 REACHED executed
  - Depends on: E-04
  - Expected outcome: h9cbn4 reads `- Status: executed` on disk.
  - Execution state: pending
  - Context: child 05 owns the whole-Set verification that no single child can perform (R1b). It exists BECAUSE this orchestrator may not carry that work itself, which is the Set's own thesis applied to the Set.

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on |
| --- | --- | --- | --- |
| 01 | `dpdyed` | Lands the R1a row grammar and the ONE shared validation function (R3), with the three typed fields resolved against `ipd_set_plan.parse_child_table` and `ipd_schema.RECOGNIZED_STATUS`. Adds a stable lint rule code. No consumer wiring. | none |
| 02 | `r3xk1f` | Wires the shared function into `/plan-review` as a bounded repair loop (default 2 attempts, following `runner_shared.resolve_retry_budget`'s precedence), with the R7 refusal text and R6's honest exhaustion. | `executed:dpdyed` |
| 03 | `0xmk4e` | Wires the shared function into both runners as a pre-queue gate, ordered AHEAD of the probe, collecting every finding across every queued orchestrator before refusing (R8). Proves the probe still runs (criterion 9) and that the two refusals are distinguishable (criterion 10). | `executed:dpdyed` |
| 04 | `68uhp0` | Migrates every pending orchestrator's checklist to the typed row. Chooses and records the migration route under criterion 12, which forbids leaving any Set refused with no available remedy. | `executed:0xmk4e` |
| 05 | `h9cbn4` | OWNS THE WHOLE-SET VERIFICATION, so it is performed and verified by an agent turn instead of being retired unperformed. Proves criteria 1, 3, 9, 10, 11 and 13 on the MERGED result, which no single child can observe. Adds tests and evidence only, no product change. | `executed:dpdyed`, `executed:r3xk1f`, `executed:0xmk4e`, `executed:68uhp0` |

## Completion criteria (the whole Set is done only when)

These restate spec `r07vma` Section 6 and are verified by child 05 on the merged result, never by this orchestrator.

- ONE function decides conformance and both consumers call it, with no second implementation (criterion 1).
- A conforming row parses as three validated fields, and each of the three failure modes is refused with a rendered message (criterion 2).
- The three real parent-only items measured at review are each REFUSED, including `wfjsp4` E-02, which opens with an allowlisted verb and would have passed a vocabulary rule (criterion 3).
- A conforming orchestrator plus a final cross-child child pass together (criterion 4).
- The refusal names both remedies and forbids satisfying it by deletion (criterion 5).
- Review repairs a violator within budget; an exhausted loop leaves the plan `to-review` with `- Readiness:` ABSENT and the attempts logged (criteria 6 and 7).
- A run reports every finding across every queued orchestrator in one pass, then refuses (criterion 8).
- The probe STILL RUNS and still blocks on a prose-only obligation; its tests pass UNEDITED; its seven functions are intact (criterion 9). PROVE THIS WITH A BARE INDENTED CONTINUATION LINE, NOT A `- Key: value` SUBFIELD (tightened at review, PR-005): the payload builder stops at the first subfield-shaped line, so an obligation written as `- Context: ...` is invisible to the probe and a test built on one would report a pass the mechanism did not earn. See the Cross-IPD validation bullet for the measurement.
- The two refusals are distinguishable by rule id (criterion 10), and a shape refusal spends zero model calls (criterion 11).
- No pre-existing Set is left refused with no available remedy (criterion 12).
- The full suite passes and `aw check all` is no worse than baseline, both counts pasted (criterion 13).

## Cross-IPD validation

- THE GRAMMAR HAS ONE DEFINITION. Children 02, 03 and 04 must all reach the rule through child 01's function. A second regex or a "cheap version" at any consumer violates R3 and is the drift this Set exists to prevent; child 05 greps for it.
- THE PROBE SURVIVES. Measured at HEAD `21eff5d8`: seven functions (`enforce_orchestrator_probe_gate`, `ask_orchestrator_probe`, `orchestrator_probe_excerpt`, `queued_orchestrator_targets`, `classify_probe_reply`, `probe_cache_payload`, `probe_refusal_remedy`) spanning 476 source lines (VERIFIED AT REVIEW by AST: 476 is the sum of each function's `lineno..end_lineno` span, of which 442 are non-blank and 315 are non-blank non-docstring; cite the span figure or state which you mean, since the three differ), plus `tests/test_orchestrator_probe.py` at 1265 lines. No child may edit or delete any of it; child 05 pins that the test file is byte-unchanged.
- THIS ORCHESTRATOR IS ITSELF A FIXTURE. Its five rows are written in the R1a grammar, so child 01's implementation must accept them and child 04 must find it already conforming. If child 01's grammar rejects this parent, either the grammar or this file is wrong, and that disagreement is a finding to report rather than to patch on one side.
- NO CHILD MAY ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. A shared symbol goes in `runner_shared`. Child 03 touches both hosts and is where this is most likely to be violated.
- THE TYPED ROW SHRINKS THE PROBE'S PAYLOAD, AND THAT INTERACTION IS THIS SET'S SHARPEST UNSTATED COST (added at review, PR-005). Measured in-process at review on THIS file: `runner_shared.probe_cache_payload` reports `e_items` as exactly the five strings `E-01 CONFIRM dpdyed REACHED executed` through `E-05 CONFIRM h9cbn4 REACHED executed`, and NOTHING ELSE. Every `- Context:` continuation line is gone, because `e_item_action_blocks` stops at the first line matching `ipd_lint._SUBFIELD_RE` (`^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$`), and a `- Context:` line matches it. So the orchestration meaning this Set tells child 04 to RELOCATE into continuation lines is relocated into a place the semantic probe CANNOT READ. Verified both ways on a synthetic fixture: a BARE indented line under a row IS included in the payload, while the same text written as `- Context: ...` is NOT. TWO CONSEQUENCES the Set must not paper over. FIRST, criterion 9 says the probe "still blocks on a prose-only obligation" stated "in its continuation lines"; as written that is FALSE for a `- Key: value` continuation line and TRUE only for a bare indented one, so child 03 and child 05 must prove criterion 9 with a BARE continuation line and must state this limit rather than demonstrating it with a `- Context:` line and reporting a pass the mechanism did not earn. SECOND, child 04's migration guidance ("relocate into continuation lines") should PREFER a bare indented line over a `- Context:` subfield wherever the relocated text carries obligation-bearing meaning, because the two differ in probe visibility. This is a pre-existing limit of the probe payload, tracked as backlog `rmcqw8`, that the typed row makes materially worse by design; it is NOT a defect introduced by any child, and no child may close it by widening the payload, since payload and cache key must move together (`tests/test_orchestrator_probe.py::TheExcerptHasAKnownLIMIT` fails loudly on a one-sided widening).

## Deferred / out of scope (with reason)

A SELF-CARRIER IS FORBIDDEN ON THIS FILE, AND THE REASON IS THIS SET'S OWN THESIS APPLIED TO ITS OWN FRONT MATTER (added at review, PR-001). A `- Carrier: d1u4sy` on this orchestrator resolves to THIS plan, and `check_engine._resolve_carrier` refuses a carrier whose only resolution is terminal or hidden: `_CARRIER_TERMINAL_STATUSES` contains `executed`. The runner RETIRES this parent to `executed` the moment its last child lands, so a self-carrier is legitimate on the day it is written and becomes a dangling obligation at the instant of retirement, with no agent turn in between to notice. Verified in-process at review by re-running `evaluate_carrier_obligation` against this file with `d1u4sy` mapped to `executed`: both self-carried rows flipped from `True` to `False` with the reason "carrier d1u4sy resolves only to a terminal/hidden artifact (executed); nothing revisits it". So every deferral here must name either a SIBLING CHILD (which an agent turn executes and validates) or a durable backlog item, never this plan. The two rows below that previously read `- Carrier: d1u4sy` were repointed for exactly this reason, and the same correction was applied across all five children.

- RETIRING OR WEAKENING THE SEMANTIC PROBE: forbidden by `25kzda` 2.5b and pinned as still-running by criterion 9. The spec's own SR-001 records that its draft proposed exactly this and was wrong.
  - Carrier-Declined: An explicit non-goal the governing spec forbids; there is no future state in which this Set should do it, so a carrier would imply otherwise.
- OQ-01's RENDER-THE-INSTRUCTIONS-FROM-THE-RULE DIRECTION: the spec leaves it open and non-blocking, and narrows it (a typed row is largely self-documenting through the scaffold). Not required to implement R1a. CARRIED BY THE SPEC RATHER THAN BY A SIBLING (repointed at review, PR-001): the obligation is the spec's own OQ-01, which stays `open` in an `approved` spec that no plan in this Set transitions, so it survives this Set's completion. A sibling carrier would have died with the Set.
  - Carrier-Evidence: .aw/records/specs/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- TEACHING `ipd_lint` A `Kind` SPECIAL CASE beyond calling the shared function: `77tr3o` OQ-1 rejected shape (a) on the grounds that a narrow exception in the honesty checker is how it stops protecting anything.
  - Carrier-Declined: A rejected alternative recorded so it is not re-proposed.
- TYPING THE ORCHESTRATOR'S PROSE SECTIONS (`## Completion criteria`, `## Cross-IPD validation`): out of scope. R1a governs rows; the prose residue is the probe's job, and spec Section 3a limit 1 states this as an honest limit rather than an omission.
  - Carrier: rmcqw8
- CHANGING `evaluate_set_retirement`'s FOUR ELIGIBILITY FACTS: this Set makes R-5's premise TRUE rather than relaxing the shape it chose.
  - Carrier-Declined: Judged correct as-is; nothing deferred.

## Scope check

- Over-scope: none. Every declared path is a child plan this orchestrator tracks; no code path is declared here, because an orchestrator performs no work of its own (which is the Set's own thesis).
- Under-scope: the children collectively declare the code paths. If a child finds a surface it must edit that its own `- Scope-Paths:` does not name, it must declare it before editing rather than reconciling afterwards.

## Required tests / validation

This orchestrator runs no tests. Each child runs `python3 -m pytest` BARE (no added flags; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`) and compares by failing NODE ID against a baseline measured in its own executing worktree. Child 05 performs the merged-result validation, which is the only place the Set's composed behavior is observable.

## Open questions

### OQ-01: Should the typed row's `<status>` field accept the whole plan status vocabulary, or only the terminal subset a parent can meaningfully wait on?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because child 01 can land the grammar accepting the full vocabulary and narrowing later is a one-line change with a test. Measured at HEAD `21eff5d8`, `ipd_schema.RECOGNIZED_STATUS` holds nine values (`approved`, `auto-approved`, `draft`, `executed`, `not-executed`, `reusable`, `reviewed`, `superseded`, `to-review`). A parent legitimately waits on `executed`, and plausibly on `reviewed` for a review-action Set; it is hard to see why a parent would wait on `draft`. PROPOSED DIRECTION: accept the full vocabulary in child 01 and let child 04's migration reveal which values are actually used, then narrow on evidence rather than guessing now. The risk of accepting too much is a parent declaring a wait that never completes, which the runner already reports as `dependency-blocked` rather than silently passing.
- Carrier-Evidence: .aw/records/specs/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- Carrier note (added at review, PR-002): the obligation is CARRIED BY THE SPEC, not by this plan. This orchestrator is retired PROGRAMMATICALLY once its children land, and a retired plan classes `done` in `aw attention`, so an obligation left here with no carrier vanishes at the exact moment nobody is looking. The narrowing decision outlives the Set (it is spec OQ-01's own subject matter and the spec stays `approved` and open on it), which is why the durable home is the spec file rather than any plan in this Set.


## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `dpdyed`'s `- Status:` line and its path read at validation time, showing `executed` and `.aw/records/plans/executed/`. Paste `aw ipd lint --phase post-transition` for that child reporting conforming. Cite the child's own V-evidence for the shared function's existence rather than re-deriving it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `r3xk1f`'s `- Status:` line and path showing `executed`, and its post-transition lint. Cite the child's own evidence that the repair loop ran and that an exhausted loop left `- Readiness:` ABSENT.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `0xmk4e`'s `- Status:` line and path showing `executed`, and its post-transition lint. Cite the child's own evidence that BOTH hosts reach the check through one object and that the probe still runs behind it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `68uhp0`'s `- Status:` line and path showing `executed`, and its post-transition lint. Cite the child's own migration record, including the route chosen and the per-orchestrator disposition, and state the re-derived population rather than quoting this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `h9cbn4`'s `- Status:` line and path showing `executed`, and its post-transition lint. Then confirm, by citation rather than re-running, that child 05 verified every completion criterion above on the MERGED result, and name any criterion it reported as unmet. A Set whose child 05 reported an unmet criterion is NOT complete regardless of the other four children's states.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 child-tracking rows, one per child. This orchestrator carries no work of its own by construction, which is the invariant the Set implements; the whole-Set verification that a parent would traditionally hold is child 05.
- Cohesion rationale: the five children are one dependency chain with one fork. Child 01 is the shared rule every other child consumes, so it is strictly first. Children 02 and 03 are independent consumers of it and could run in either order or in parallel. Child 04 follows 03 so the migration is checked by the same gate a run applies. Child 05 follows everything because its subject is the merged result.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change.

Post-gate lifecycle: this plan and all five children are `to-review` and require `/plan-review` followed by explicit human approval (`aw ipd set approved <id6> --by-human --message ...`) before execution. This orchestrator is retired by the runner once every child is `executed` on disk, which is why it carries no work of its own; if it is run BY HAND instead, its five rows are the checklist to follow in dependency order.

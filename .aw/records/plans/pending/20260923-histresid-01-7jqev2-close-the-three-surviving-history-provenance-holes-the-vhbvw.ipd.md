# IPD: Close the three surviving history-provenance holes the vhbvwz fix left: the migration slimmer, the oldest-first legacy reader, and the missing same-status dedup

- Date: 2026-09-23
- Kind: child
- Concern: TWELVE BACKLOG ITEMS DESCRIBE ONE FAMILY OF HISTORY-PROVENANCE DEFECTS, AND THE HEADLINE MEMBER IS ALREADY FIXED, WHICH IS THE FIRST THING AN EXECUTOR MUST KNOW. Backlog `raxuyq` (`high`, `Blocks-Release: next`) says `aw specs note`/`set` "silently DELETE all but the newest tracked inline workflow-history round". MEASURED AT HEAD `22cf67d9`, THAT IS NO LONGER TRUE: `specs._append_history` PREPENDS and preserves prior rounds, and `backlog._reattach_history` does the same. Probed directly on a 3-round fixture, `_append_history` returned 4 rounds with all three priors intact, and on an id-less spec (backlog `2vg3zo`'s specific claim) it also returned 3 of 3. Executed plan `vhbvwz` (`setterguard` Order 02, commit `fbf85068`) did that work and amended the governing spec. So `raxuyq`, `b6i85r`, `i8wmte`, `l23v3j`, `g31sns`, `2vg3zo` and `yvp951` are all reports of a defect that is CLOSED, and graduating them as new implementation work would re-fix shipped code.
  WHAT SURVIVES IS THREE NARROWER HOLES, EACH MEASURED IN THIS TREE, and they are the whole of this plan. FIRST (`8pcdoa`), `record_history.migrate_inline_history` STILL SLIMS: its body calls `_slim_inline_history(path, text, records)` on every non-plan record, and that helper's docstring says it keeps "ONLY the latest (last-in-order) record line" via `keep = records[-1]`. That premise INVERTED when `vhbvwz` made the writers newest-first, so on any post-`vhbvwz` file the record it keeps is the OLDEST. Proved on a 3-round newest-first spec fixture: the surviving line was `- 2026-09-01 created ... OLDEST` and the round DESTROYED was `- 2026-09-20 approved ... the --by-human attestation`. That is materially worse than `8pcdoa`'s own summary, which says only that it "slims and reads the last record": the round it actually destroys is the human approval attestation, which `AGENTS.md` treats as unforgeable evidence.
  SECOND (`jhrao5`, and `tk1gqo` for plans), `attention_contract.newest_history_record` is DELIBERATELY POSITIONAL, taking the FIRST matching line, and its docstring defends that at length as the writer's contract. Correct for every file the current writers produce, and WRONG for a legacy file still stored oldest-first: probed on a two-round oldest-first block it returned the `2026-09-01` round as "newest" over the `2026-09-15` one. `jhrao5` measures 77 such legacy artifacts.
  THIRD (`4vh5nb`), `specs._append_history` has NO dedup, verified by source inspection, so an identical same-status re-assertion appends a duplicate round. `x6tk1u` established that dedup rule for the backlog writer; the specs fork never got it.
  THE EXISTING TEST CANNOT CATCH THE FIRST HOLE, which is why it shipped green and why this plan must fix the fixture rather than just the code. `tests/test_record_history_migrate.py` passes (3 passed, measured), but its fixture writes `- 2026-01-01 draft` before `- 2026-01-05 executed`, i.e. OLDEST-FIRST, and `test_apply_folds_and_slims_excluding_plans` then ASSERTS the surviving line is `- 2026-01-03 reviewed (t): c`, the last in that oldest-first order. So the test encodes the pre-`vhbvwz` convention and would keep passing while production destroys attestations.
- Scope: Close the three measured holes and make each one's regression test use the NEWEST-FIRST shape production actually writes. IN: (a) make the migration slimmer's retention agree with the writers' newest-first contract, or stop slimming, per OQ-01; (b) make the newest-record reader correct for an oldest-first legacy file without regressing the positional guarantee its docstring defends; (c) add the `x6tk1u` same-status dedup to the specs writer; (d) re-point `tests/test_record_history_migrate.py`'s fixture to newest-first so the first hole is actually covered. OUT: re-fixing `specs._append_history`/`backlog._reattach_history` preservation, which `vhbvwz` already shipped and which this plan VERIFIES rather than changes; re-tracking the gitignored `.aw/records/history.jsonl` sidecar (that was `raxuyq` fix option (a), and the maintainer chose inline-is-durable instead on 2026-09-10); and any change to plans' inline history, which `IPD-S405` requires in full and which the migration correctly excludes.
- Scope-Paths: agent_workflows/record_history.py, agent_workflows/attention_contract.py, agent_workflows/specs.py, tests/test_record_history_migrate.py, tests/test_attention_contract.py, tests/test_specs.py
- Item-Dependencies: none
- Status: to-review
- Set: histresid
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 7jqev2
- From-Backlog: 8pcdoa
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the twelve-item history-provenance family, NARROWED HARD by measurement. Seven of the twelve (`raxuyq`, `b6i85r`, `i8wmte`, `l23v3j`, `g31sns`, `2vg3zo`, `yvp951`) report a defect executed plan `vhbvwz` already FIXED, verified by probing the live `specs._append_history` on both a normal and an id-less spec; they should be closed as done citing `vhbvwz`, not graduated. `- From-Backlog:` names `8pcdoa` because that is the item whose claim is still live and is the largest surviving hole. `- Blocks-Release: next` is INHERITED from the family's gating members (`8pcdoa` carries no gate of its own, but `jhrao5`, `raxuyq` and `hg2oop` do, and the surviving defect destroys human approval attestations, which is squarely the live-bug policy's case).
  THE SHARPEST FINDING IS ONE NO ITEM STATES: the migration slimmer keeps `records[-1]`, which was the newest round under the pre-`vhbvwz` convention and is the OLDEST round now, so the specific line it destroys on a real spec is the `--by-human` approval attestation. Proved on a newest-first fixture rather than reasoned about.
  I ALSO MEASURED WHY THE SUITE IS GREEN OVER IT, because that decides whether a code-only fix is sufficient: `tests/test_record_history_migrate.py` writes an OLDEST-FIRST fixture and asserts the last-in-order survivor, so it pins the retired convention. A fix that does not re-point that fixture leaves the regression invisible exactly as it has been.

## Goal

Make the three surviving history-provenance holes closed and covered: the migration must stop destroying the newest round (the human attestation), the newest-record reader must be right for a legacy oldest-first file, and the specs writer must dedup an identical same-status re-assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the ground, because most of this family is already fixed

- [ ] E-01 RE-VERIFY WHAT IS ALREADY FIXED BEFORE CHANGING ANYTHING, and report any claim that has moved. This plan's central narrowing is that 7 of 12 items are closed work, and an executor who takes that on trust could either re-fix shipped code or skip a real regression.
  PROBE THE TWO WRITERS ON A MULTI-ROUND FIXTURE: call `specs._append_history` on a 3-round block and on an id-less spec, and `backlog._reattach_history` likewise, and confirm prior rounds SURVIVE and the new record is PREPENDED. At authoring: 3 of 3 priors kept in both spec cases.
  CONFIRM `vhbvwz` IS EXECUTED and that commit `fbf85068` is an ancestor of your base, since every "already fixed" claim here rests on it.
  RE-PROVE THE THREE SURVIVING HOLES rather than assuming them: the slimmer's `keep = records[-1]` against a NEWEST-FIRST fixture, `newest_history_record` against an OLDEST-FIRST two-round block, and the absence of dedup in the specs writer. Report any that no longer reproduce, and if a hole is gone, say so and do not invent work for it.
  - Depends on: none
  - Expected outcome: each of the three surviving holes reproduced at your HEAD with pasted output, each of the seven already-fixed claims re-confirmed fixed, and any divergence from this plan's measurements reported rather than silently absorbed.
  - Execution state: pending

### Task group 2: close the holes

- [ ] E-02 STOP THE MIGRATION DESTROYING THE NEWEST ROUND. `record_history._slim_inline_history` keeps `records[-1]` and documents that as "the latest (last-in-order) record", which the `vhbvwz` newest-first switch inverted, so it now keeps the oldest and deletes the human attestation.
  RESOLVE OQ-01 FIRST, because the two candidate fixes differ in kind rather than in detail: either make retention agree with the writers' contract (keep `records[0]`), or stop slimming entirely, which is what the maintainer's 2026-09-10 inline-is-durable ruling implies for every other writer in this family. Do not do both, and record which and why.
  DO NOT REINTRODUCE A SECOND ORDER CONVENTION. If you keep slimming, the retention rule must READ its notion of newest from the same authority the rest of the tree uses (`attention_contract.newest_history_record`) rather than hardcoding an index, or this defect recurs the next time the convention moves. That is the whole lesson of the `records[-1]` inversion.
  PLANS STAY EXCLUDED. The migration already skips them and `IPD-S405` requires a plan's full inline history; nothing here may start slimming a plan.
  - Depends on: E-01
  - Expected outcome: a migration that cannot destroy the newest round on a newest-first file, with the chosen option recorded against OQ-01; the retention rule derives newest from the shared reader rather than an index literal; plans still untouched.
  - Execution state: pending

- [ ] E-03 MAKE THE NEWEST-RECORD READER CORRECT FOR AN OLDEST-FIRST LEGACY FILE WITHOUT LOSING THE POSITIONAL GUARANTEE. `attention_contract.newest_history_record` takes the FIRST matching line, and its docstring defends that choice with a measured rejection of a max-by-date scan (it flips `history_verdict_approves` for 20 plans), so a naive "use the greatest date" fix is already known to be unsafe and must not be re-attempted blindly.
  READ THAT DOCSTRING BEFORE EDITING. It records that two readers once disagreed and what the disagreement cost (373 of 679 multi-record plans misreported). Whatever you do must keep ONE authority for this question.
  THE HONEST OPTIONS ARE NARROWER THAN THEY LOOK: detect a file whose records are demonstrably oldest-first (e.g. strictly ascending dates across every record) and read it accordingly, or NORMALIZE the 77 legacy artifacts `jhrao5` counts to newest-first so the positional rule is true again. The second removes the ambiguity permanently; the first leaves a heuristic in a safety-relevant reader. Prefer normalization if it can be done as a records-only rewrite, and say which you chose.
  - Depends on: E-01
  - Expected outcome: a legacy oldest-first artifact reports its genuinely newest record; the plan-facing behavior the docstring pins is unchanged, proved by the existing plan-readiness tests staying green; one authority for "which record is newest" remains.
  - Execution state: pending

- [ ] E-04 GIVE THE SPECS WRITER THE `x6tk1u` SAME-STATUS DEDUP THE BACKLOG WRITER ALREADY HAS. `specs._append_history` has no dedup (verified by source inspection), so an identical same-status re-assertion appends a duplicate round.
  CONSUME THE EXISTING RULE, DO NOT FORK IT. `x6tk1u` established this behavior for the backlog setter; find that implementation and share it rather than writing a second predicate, because two dedup rules that disagree is the same class of defect as the two newest-record readers E-03 exists to avoid.
  - Depends on: E-01
  - Expected outcome: an identical same-status re-assertion on a spec does not append a duplicate round; the rule is shared with the backlog writer rather than reimplemented; a deliberate message change still records.
  - Execution state: pending

### Task group 3: make the regression visible

- [ ] E-05 RE-POINT THE MIGRATION TEST FIXTURE TO NEWEST-FIRST, so E-02's defect could have failed. `tests/test_record_history_migrate.py` currently writes `- 2026-01-01 draft` before `- 2026-01-05 executed` and `test_apply_folds_and_slims_excluding_plans` asserts the survivor is `- 2026-01-03 reviewed (t): c`, i.e. it pins the RETIRED oldest-first convention and passes while production destroys attestations.
  ADD THE ATTESTATION CASE EXPLICITLY, not just a reordered fixture: a spec whose newest round is a `--by-human` approval attestation, asserting that round SURVIVES the migration. That is the case with real consequences and it should be named in the test.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the migration test fixture is newest-first, an attestation-survival case exists and fails against the pre-E-02 code (demonstrate that), and the whole file passes after.
  - Execution state: pending

## Project conventions discovered (Step 0)

- INLINE HISTORY IS THE DURABLE HOME for specs and backlog items, per the maintainer's 2026-09-10 ruling recorded in `vhbvwz` OQ-01, because `.aw/.gitignore` ignores `records/history.jsonl` (verified: line 11). The sidecar is still written and is advisory only (`record_history.append_advisory`). So no fix here may relocate provenance to the sidecar.
- PLANS ARE DELIBERATELY EXEMPT from slimming (`IPD-S405` requires the inline executed round), and the migration already honors that. That exemption is the precedent showing inline history is understood to be load-bearing wherever a gate reads it.
- NEWEST-FIRST IS THE WRITER'S CONTRACT, documented at length in `attention_contract.newest_history_record` and implemented by `status_set.apply_status_change`'s `insert(i + 1, ...)`. The bug class in this plan is code that predates that contract and still assumes last-in-order.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `record_history._slim_inline_history` | Keeps `records[-1]`, documented as "latest (last-in-order)". Under the post-`vhbvwz` newest-first convention that is the OLDEST round, so the migration DESTROYS the newest one, which on a real spec is the `--by-human` approval attestation. | 3-round newest-first fixture slimmed; survivor was `- 2026-09-01 created ... OLDEST`, destroyed round was `- 2026-09-20 approved ... the --by-human attestation` |
| F-2 | HIGH | `tests/test_record_history_migrate.py` | The suite is green over F-1 because the fixture is OLDEST-FIRST and the assertion expects the last-in-order survivor, pinning the retired convention. A code-only fix leaves the regression invisible. | `3 passed`; fixture writes `- 2026-01-01 draft` then `- 2026-01-05 executed`; assertion expects `- 2026-01-03 reviewed (t): c` |
| F-3 | HIGH | `attention_contract.newest_history_record` | Positional FIRST-match is correct for current writers and wrong for a legacy oldest-first file; `jhrao5` counts 77 such artifacts. A max-by-date fix is already measured unsafe (flips `history_verdict_approves` for 20 plans). | two-round oldest-first block returned the `2026-09-01` round as newest over `2026-09-15` |
| F-4 | MED | `specs._append_history` | No same-status dedup, so an identical re-assertion appends a duplicate round; the backlog writer got this rule from `x6tk1u` and the specs fork did not. | source inspection: no dedup/identical logic present |
| F-5 | HIGH (narrowing) | `specs._append_history`, `backlog._reattach_history` | SEVEN of the twelve family items report an ALREADY-FIXED defect. Both writers prepend and preserve priors, including on an id-less spec. Graduating those items as implementation work would re-fix shipped code. | 3-round fixture -> 4 rounds, all priors intact; id-less spec -> 3 of 3 kept; `vhbvwz` executed at `fbf85068` |

## Proposed changes (ordered, validatable)

1. E-01 re-verifies the three surviving holes and the seven already-fixed claims at the executing HEAD, reporting any drift.
2. E-02 stops the migration destroying the newest round, deriving "newest" from the shared reader rather than an index literal, per OQ-01's answer.
3. E-03 makes the newest-record reader right for a legacy oldest-first artifact while keeping one authority and the measured plan-facing behavior.
4. E-04 shares the `x6tk1u` same-status dedup into the specs writer instead of forking it.
5. E-05 re-points the migration fixture to newest-first and adds an explicit attestation-survival case that fails before E-02.

## Deferred / out of scope (with reason)

- RE-FIXING THE TWO WRITERS' PRESERVATION. `vhbvwz` shipped it (F-5) and this plan verifies it in E-01 rather than changing it. Seven backlog items describing it should be CLOSED citing `vhbvwz`, which is a records act and not implementation work; this plan deliberately does not perform those closes, because closing another item's gate is the kind of bookkeeping that should be visible as its own change.
- RE-TRACKING `.aw/records/history.jsonl`. That was `raxuyq`'s fix option (a); the maintainer chose inline-is-durable on 2026-09-10, so reopening it would relitigate a settled ruling.
- ANY CHANGE TO PLANS' INLINE HISTORY. `IPD-S405` requires the executed round inline and the migration already excludes plans.
- `tk1gqo` (lifecycle-transition-invalid on conformant plans) beyond what E-03 incidentally fixes. It is a plans-side reader-order defect with its own `check.lifecycle-transition-invalid` surface; if E-03's normalization does not close it, it stays open rather than being absorbed silently here.

## Scope check

- Over-scope: `agent_workflows/specs.py` is in scope ONLY for E-04's dedup. Do not touch `_append_history`'s preservation or prepend order, which `vhbvwz` settled and E-01 verifies.
- Under-scope: if E-03 chooses records-only normalization of the 77 legacy artifacts, those record files are edits this plan's `- Scope-Paths:` does not list. Declare them before making them, or choose the reader-side option; do not quietly widen scope at finalize.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_record_history_migrate.py`, plus the attention-contract and specs test modules named in `- Scope-Paths:`.
- The plan-readiness tests must stay green, because E-03 touches the reader whose docstring records that a wrong fix flips `history_verdict_approves` for 20 plans.
- E-05's attestation case must be demonstrated FAILING against the pre-E-02 code and passing after; a test that never failed proves nothing about F-1.

## Spec / documentation sync

- `_slim_inline_history`'s docstring asserts it keeps "the latest (last-in-order) record" and cites spec OQ-2. That sentence is now FALSE for every file the current writers produce and must be corrected in the same change, since it is the comment that made the inversion invisible.
- Spec `20260818-1525-02` R2/OQ-2 is the contract `vhbvwz` amended; if E-02 stops slimming entirely, check whether that spec still describes the migration accurately and amend it in this change rather than leaving the two to drift. Any `.spec.md` actually edited must be added to `- Scope-Paths:` before the edit, per the spec-amendment rule.

## Open questions

### OQ-01: Should the migration keep the newest round, or stop slimming entirely?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer if it implies a spec change
- Resolution or deferral rationale: NOT blocking, because E-02 must record an explicit choice and either option closes F-1, so the plan terminates correctly either way. The case for KEEPING-NEWEST is minimal change and it preserves the sidecar-folding purpose the migration was written for. The case for STOP-SLIMMING is consistency with the maintainer's 2026-09-10 inline-is-durable ruling, which every other writer in this family now follows, and it removes the class of defect rather than re-aiming it; F-1 exists precisely because a retention rule outlived the convention it was written against. Note this may amend spec `20260818-1525-02`, which is why the maintainer is the escalation owner.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of each probe: the two writers preserving priors (normal and id-less spec), `vhbvwz`/`fbf85068` confirmed ancestral, and the three surviving holes reproduced. Any claim that moved is named explicitly.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a newest-first fixture whose newest round is a `--by-human` attestation, run through the migration, with the pasted before/after showing the attestation SURVIVES. Plus the recorded OQ-01 choice and, if slimming is kept, the code path showing newest is derived from `attention_contract.newest_history_record` rather than an index literal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted reader output on an oldest-first two-round legacy block returning the genuinely newest record, plus the plan-readiness test module passing, plus a statement of which option (detection or normalization) was taken and why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted before/after showing an identical same-status re-assertion appending NO duplicate round on a spec, and the symbol name of the SHARED dedup predicate proving it was not forked.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the attestation-survival test pasted FAILING at the pre-E-02 code and PASSING after, plus `tests/test_record_history_migrate.py` green, plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.

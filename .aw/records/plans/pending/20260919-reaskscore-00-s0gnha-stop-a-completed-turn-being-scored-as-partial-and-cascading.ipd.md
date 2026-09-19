# IPD: Stop a completed turn being scored as partial and cascading dependency-blocked across its Set

- Date: 2026-09-19
- Kind: orchestrator
- Concern: FOUR RUNS IN ONE DAY ENDED `BLOCKED` WITH THEIR WORK FINISHED, COMMITTED, AND THROWN AWAY BY THE SCORING. Measured 2026-09-18 across `run-20260918T045802Z-2547360`, `run-20260918T190723Z-2697256`, `run-20260918T193638Z-2963696` and their repeats: in each case one item was recorded `partial`, every sibling cascaded to `dependency-blocked`, and the orchestrator was deferred. Three INDEPENDENT defects compose to produce it. (1) THE HOST truncates a turn it was asked to run in the foreground, terminating the agent's own command and then reporting `SUCCESS` with exit 0, so the driver accepts a killed turn as a clean one. (2) THE DRIVER, having scored that empty turn `partial`, then spends a defect re-ask that COMPLETES THE ENTIRE JOB and re-collects the finished outcome to the exact path the scorer reads - and never rescores it, so a fully successful turn is recorded `partial` with `last_outcome: null` beside a complete outcome file. (3) A TURN THAT PROVABLY DID NOTHING is treated as a terminal attempt indistinguishable from one that genuinely fell short, so a single such item is allowed to block a whole Set. The dependency cascade itself is CORRECT in every instance and must not be loosened; each defect is a wrong INPUT to a right rule.
- Scope: Orchestrate the three child plans that close these defects, in dependency order, and prove at the end that the composed behavior actually fixes the measured runs rather than each piece passing in isolation. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child (`skn8uk` the rescoring, `ty7w6o` the host-truncation signal, `dy9ymn` the zero-work retry), and this file contributes no code, no test, and no record of its own. EXCLUDES loosening any dependency, success-bar, or orchestrator-retirement predicate, in every child without exception.
- Scope-Paths: .aw/records/plans/pending/20260919-reaskscore-00-s0gnha-stop-a-completed-turn-being-scored-as-partial-and-cascading.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: reaskscore
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: s0gnha

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with its three children from backlog `yxfw4k` (the rescoring defect, newly filed) and `x7wfyx` (the zero-work retry, already open). The Set exists rather than a single plan because the three defects are genuinely independent: each one alone is sufficient to lose a run, each is fixable alone, and each has its own review surface. Inherits `Blocks-Release: next`.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a run's recorded outcome match what actually happened, so that finished work is never discarded as
`partial` and a single wasted turn never blocks three siblings. The Set is done when the two measured
failure shapes cannot reproduce and the composed behavior is demonstrated end to end, not merely
unit-tested in three parts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and prove it composed

- [ ] E-01 EXECUTE THE CHILDREN IN THE ORDER THE TABLE BELOW DECLARES, honoring `dy9ymn`'s `executed:ty7w6o` edge, and confirm each child is `executed` before dispatching anything that depends on it. `skn8uk` and `ty7w6o` are INDEPENDENT of each other and may run in either order or in parallel lanes; `dy9ymn` requires `ty7w6o` because it consumes the `attempt["host_truncation"]` record that plan produces. This item is orchestration and performs no product change of its own.
  - Depends on: none
  - Expected outcome: all three children are `executed`, each dependency edge was satisfied at dispatch, and no child's deliverable was performed by this plan.
  - Execution state: pending

- [ ] E-02 CONFIRM NO CHILD WEAKENED A SHARED PREDICATE, which is the one way this Set could do net harm. Every child's Scope forbids loosening the dependency, success-bar, and orchestrator-retirement predicates, because in all four measured runs the cascade was CORRECT and only its input was wrong. Verify against the merged result that `EXECUTION_SUCCESS_STATES`, `SUCCESS_STATES`, `EXECUTE_REPORTING_SUCCESS_STATES`, `TERMINAL_STATES` and `SET_RETIREMENT_DONE_STATUS` are unchanged, and that the cross-host equality pins still pass. A child that made its tests pass by widening a success bar has defeated the purpose of the Set while appearing to fix it.
  - Depends on: E-01
  - Expected outcome: the five named constants are byte-identical to their pre-Set values and the cross-host equality pins pass.
  - Execution state: pending

- [ ] E-03 PROVE THE COMPOSED FIX AGAINST THE MEASURED SHAPES, which no child can do alone because each holds only its own third. Reconstruct both measured shapes end to end and show each now reaches a non-blocking outcome: SHAPE A (the rescoring case) is a first turn that writes no outcome, a defect re-ask that completes and commits the work, and a re-collection - the item must end `substantially-complete` or better and its siblings must NOT be `dependency-blocked`. SHAPE B (the zero-work case) is a host-truncated turn that did nothing at all - the item must be re-dispatched once within budget rather than blocking its Set. Also confirm the two fixes do not collide on one item: a turn that is BOTH truncated AND rescued by its re-ask must be rescored (the work exists) and must NOT also be retried (retrying would re-dispatch completed, committed work), and the predicate ordering must guarantee that rather than leaving it to chance.
  - Depends on: E-01, E-02
  - Expected outcome: both measured shapes reach non-blocking outcomes in reconstruction, and the truncated-and-rescued case is rescored without being retried.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
| --- | --- | --- | --- |
| 01 | `20260919-reaskscore-01-skn8uk-rescore-the-disposition-after-a-defect-re-ask-whose-recollec.ipd.md` | Rescores the disposition from the re-collected outcome after a defect re-ask, monotonically (improvements only), before the integration gate reads it. Fixes the measured `partial`-with-`executed`-outcome. | none |
| 02 | `20260919-reaskscore-02-ty7w6o-record-a-host-truncated-agy-turn-as-truncated-instead-of-acc.ipd.md` | Observes the agy host's own truncation lines on the stream the driver already reads, and records a truncated turn durably instead of accepting exit 0 as a clean finish. Produces the signal only. | none |
| 03 | `20260919-reaskscore-03-dy9ymn-retry-a-turn-that-provably-attempted-nothing-instead-of-bloc.ipd.md` | Adds a narrow, fail-closed "provably attempted nothing" predicate and re-queues such an item once within the existing retry budget instead of recording a terminal `partial`. Consumes `ty7w6o`'s signal. | `executed:ty7w6o` |

## Completion criteria (the whole Set is done only when)

- All three children are `executed`, each having satisfied its own `V-*` items with concrete pasted evidence.
- The two measured failure shapes are reconstructed and shown not to reproduce (E-03).
- No shared predicate was weakened (E-02): the five named constants are unchanged and the cross-host equality pins pass.
- The bare `python3 -m pytest` suite passes on the merged result, with the actual summary line pasted.
- The two source backlog items are transitioned honestly: `yxfw4k` may close once its defect is fixed and validated; `x7wfyx` must be `graduated`, NOT `done`, because only its item B is implemented and it carries `Blocks-Release: next`.

## Cross-IPD validation

- NO CHILD LOOSENED A PREDICATE (E-02). This is the Set's central safety property: all four measured cascades were correct, so any widening of a success bar would trade a visible defect for an invisible one.
- THE TWO FIXES DO NOT COLLIDE (E-03). `skn8uk` rescues a turn whose work EXISTS; `dy9ymn` re-dispatches a turn whose work DOES NOT. Those conditions are mutually exclusive by construction (`dy9ymn`'s conjunction requires no outcome file, no commit, unchanged head, clean tree, all of which a rescued turn violates), but the Set must DEMONSTRATE the exclusivity rather than assume it, because the cost of getting it wrong is re-dispatching completed committed work.
- THE ORDERING WITHIN THE TURN IS CONSISTENT ACROSS CHILDREN. `skn8uk` inserts its rescore between the defect record and the integration gate; `dy9ymn` requeues before the cascade observes a terminal status; `ty7w6o` records at the stdout seam and changes no disposition. Confirm on the merged result that these three insertions did not reorder each other, and that the AST ordering pins in `tests/test_rununify_execute_item_gates.py` pass unweakened.
- NO CHILD EDITED A SPEC. Each child deliberately declares no `.spec.md` path and each records its candidate amendment as a non-blocking open question (`skn8uk` OQ-01 on `7ckptx` R2.1, `ty7w6o` OQ-02 on `7ckptx` R4, `dy9ymn` OQ-01 on `25kzda` 5.5). Confirm none was edited anyway, since an undeclared spec edit is reported by the runner's own scope reconciliation.

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR RETIREMENT BAR IS NOT WIDENED. `SET_RETIREMENT_DONE_STATUS` is `executed` alone (`runner_shared.py:6443`), deliberately not `EXECUTION_SUCCESS_STATES` (`:6440-6442`), and is governed by spec `77tr3o`. So a rescued item that reaches `substantially-complete` unblocks its SIBLINGS but leaves the parent stranded rather than retired; retirement follows normally once the item reaches `executed` through the finalize path `skn8uk` re-opens. Changing that bar inside a defect-fix Set would be an unreviewed contract change.
  - Carrier-Declined: Nothing to carry: the retirement bar is spec `77tr3o`'s reasoned contract and is not defective. A rescued item that reaches `executed` through the re-opened finalize path retires its parent normally, so no future act is pending.
- TELLING THE AGENT ITS REMAINING TURN BUDGET (`x7wfyx` item A) is left undone, with the consequence stated: `x7wfyx` is therefore `graduated`, not closed. It is a prompt change with its own regression surface, and per `ty7w6o`'s finding F-1 the agent was not the one choosing to stop, so it no longer addresses the measured cause.
  - Carrier: x7wfyx
- PREVENTING THE HOST FROM BACKGROUNDING A FOREGROUND COMMAND is out of reach and is `ty7w6o` OQ-03. It is upstream behavior this repository does not control and cannot test; the retry in `dy9ymn` is the compensating control.
  - Carrier: dy9ymn
- NO SPEC IS AMENDED BY THIS SET. Three candidate amendments are recorded as non-blocking open questions on the children for a reviewer to authorize deliberately, rather than being taken silently inside a defect fix.
  - Carrier: s0gnha

## Scope check

- Over-scope: none. This plan declares only its own file and contributes no product change; every deliverable is owned by a child.
- Under-scope: the orchestrator retirement bar, `x7wfyx` item A, the host's own backgrounding behavior, and the three spec amendments, each excluded above with a reason. A reviewer should confirm these exclusions rather than assume them.

## Required tests / validation

Each child carries its own `V-*` items and its own evidence obligations; this plan does not restate them.
At the Set level, the bare `python3 -m pytest` suite must pass on the MERGED result (not merely per lane),
with the actual summary line pasted, and E-03's two reconstructions plus the collision case must be
demonstrated with pasted output. Reconstructions must be built in `tmp_path`: the measured runs live under
`.aw/records/runs/`, which is gitignored and absent in CI, so a test reading it would pass locally and
fail everywhere else.

## Open questions

### OQ-01: Should the three spec amendments the children identified be made in a follow-on plan?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because all three children are conforming under the specs as they stand, and each records its candidate amendment with the wording it would use (`skn8uk` OQ-01: generalize `7ckptx` R2.1 from "collect before scoring" to "score from the latest successful collection"; `ty7w6o` OQ-02: state in `7ckptx` R4 that the driver must record a host-initiated termination; `dy9ymn` OQ-01: name the zero-work class explicitly in `25kzda` 5.5's retryable list). Deliberately not bundled into this Set: amending an approved spec changes the contract every other plan is reviewed against, which is the highest-leverage change a run can make and should be authorized on its own merits rather than carried along by a defect fix. If the reviewer wants them, one follow-on plan declaring the two spec files is the cheapest route.
- Carrier: s0gnha

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted evidence that all three children are `executed` (their plan files' `- Status:` and their location under `.aw/records/plans/executed/`), and that `dy9ymn` was dispatched only after `ty7w6o` reached `executed` (cite the run record or the lifecycle commits). Plus a statement that this plan performed none of the children's deliverables.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff` (or an equivalent demonstration) showing `EXECUTION_SUCCESS_STATES`, `SUCCESS_STATES`, `EXECUTE_REPORTING_SUCCESS_STATES`, `TERMINAL_STATES` and `SET_RETIREMENT_DONE_STATUS` are unchanged across the whole Set, plus pasted output of the cross-host equality pins (`tests/test_rununify_run_queue.py`) and the AST ordering pins (`tests/test_rununify_execute_item_gates.py`) passing unweakened.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output for SHAPE A (no outcome on the first turn, a re-ask that completes and commits, re-collection) showing the item ends `substantially-complete` or better and its siblings are NOT `dependency-blocked`; pasted output for SHAPE B (a host-truncated zero-work turn) showing exactly one re-dispatch within budget rather than a Set-blocking `partial`; and pasted output for the COLLISION case showing a turn that is both truncated and rescued is rescored and NOT retried. Plus the full bare `python3 -m pytest` summary line on the merged result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set is release-blocking (`Blocks-Release: next`, inherited from backlog `yxfw4k` per the
every-live-bug-gates-the-release rule) and must not be executed before explicit human approval, which
`- Status:` records and which no agent may write on the maintainer's behalf.

THIS IS AN ORCHESTRATOR AND HOLDS NO WORK OF ITS OWN. Its three items are sequencing, a cross-child
safety check, and the composed proof no child can produce alone; every product deliverable belongs to a
child. If an executor finds itself needing to make a product change here, that is a missing child and
must be authored as one, not parked on this plan, because a runner retiring this plan SKIPS the
pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody.

EXECUTION CONTRACT (applies to every child). Commit only the files the executing plan changed,
path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`/bare, and never push. Before every
commit run `git diff --cached --name-only` and `git restore --staged` anything not yours: this is a
SHARED CHECKOUT with concurrent workers, and a failed pre-commit hook can leave paths in the index you
never staged, so re-verify after any failed attempt. Prefer `aw commit <plan> -- <paths>`. When reporting
tests passed, paste the ACTUAL bare `python3 -m pytest` output; do not add `-n0`, a second `-q`, or
`-p no:randomly`.

POST-GATE LIFECYCLE MOVE. Do not report the Set complete or move this plan to
`.aw/records/plans/executed/` until every child is `executed`, `aw ipd lint --phase pre-transition`
reports conforming, and every `V-*` above carries concrete pasted evidence. On closing the source items:
`yxfw4k` may close once its defect is fixed and validated; `x7wfyx` must be set `graduated`, not `done`,
and its `Blocks-Release` must not be cleared.

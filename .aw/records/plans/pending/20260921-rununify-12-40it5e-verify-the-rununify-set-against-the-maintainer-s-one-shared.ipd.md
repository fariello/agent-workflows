# IPD: Verify the rununify Set against the maintainer's one-shared-codebase directive and establish the missing characterization baseline

- Date: 2026-09-21
- Kind: child
- Concern: Two distinct pieces of work sit unperformed on the Order-0 orchestrator `5e4sb6` (its E-02 and E-03), and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. ALL ELEVEN CHILDREN ARE ALREADY `executed`, so retirement is imminent and both items would be marked complete having never been performed. MEASURED 2026-09-22 in run `run-20260922T003414Z-1020752`, where the coverage probe refused a 34-set launch naming `5e4sb6` (`events.jsonl`, event `orchestrator-probe-gate`). AND THE MEASUREMENT THAT MAKES THIS URGENT RATHER THAN CLERICAL: an AST count at HEAD finds 58 symbols still defined in BOTH runners, totalling 2711 agy definition lines, including `run_queue` (456 agy / 549 oc), `build_parser` (296/387) and `main` (234/340). The maintainer's 2026-09-16 directive - "at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code" - is this Set's definition of done, and on that count it is NOT met. Retiring `5e4sb6` now would record the directive as satisfied while 58 shared symbols remain.
- Scope: Perform `5e4sb6`'s E-02 and E-03 as real agent turns, and report the Set's true state against the directive. IN: an AST-level, REPO-WIDE single-implementation measurement; a per-symbol disposition of every symbol still defined in both runners (genuinely host-specific versus still-redundant); the characterization baseline E-02 requires, authored now with its LATENESS STATED; and an honest verdict on whether the Set is done. OUT: performing the unification of any remaining symbol - if the measurement shows redundancy remains, this plan REPORTS it and a follow-up Set owns the work, because unifying `run_queue` is not a verification task.
- Scope-Paths: .aw/records/plans/pending, tests/test_rununify_characterization.py, .aw/records/research
- Item-Dependencies: none
- Status: to-review
- Set: rununify
- Order: 12
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 40it5e

## Workflow history

- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `5e4sb6` as carrying work no child covers. THE PARENT'S E-02 EXPLICITLY SANCTIONS THIS SHAPE: "if the repo's conventions make a test-only change count as product code, it becomes child 00 instead, executed before child 01." That window has closed - all eleven children are executed - so E-02 is authored here with its lateness declared rather than pretended away. E-03's content is lifted from the parent unchanged.

## Goal

Tell the truth about whether `rununify` achieved what the maintainer asked for, and leave behind the
characterization baseline the Set was supposed to have. The honest answer looks likely to be "not yet": 58
symbols are still defined in both runners. That is worth knowing BEFORE the orchestrator retires and records
the directive as met, because a Set that reports success is one nobody revisits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the Set against the directive

- [ ] E-01 MEASURE SINGLE-IMPLEMENTATION AST-LEVEL AND REPO-WIDE, not pairwise between the two runners, and record the result with its HEAD. THE PAIRWISE CHECK IS KNOWN-BLIND and the parent says so (F10): "a pairwise check passes while a third copy sits in another module, which is exactly the state measured today". So compare each runner symbol against ALL of `agent_workflows/*.py`. Report three counts: symbols defined in BOTH runners; symbols defined in a runner AND in a non-runner module (class (d) re-forks); and symbols with exactly one definition repo-wide. STATE THE METRIC, because the parent's Goal records that symbol counts reproduce while line figures do not. A STARTING MEASUREMENT IS ALREADY IN HAND and should be re-derived rather than trusted: 58 symbols defined in both runners at authoring HEAD, 2711 agy definition lines, the largest being `run_queue` 456/549, `build_parser` 296/387, `main` 234/340.
  - Depends on: none
  - Expected outcome: a committed, reproducible measurement (script or pasted method) with the three counts, the HEAD, and the stated metric; plus the per-symbol list of everything still defined in both runners.
  - Execution state: pending

- [ ] E-02 DISPOSITION EVERY STILL-SHARED SYMBOL AS HOST-SPECIFIC OR STILL-REDUNDANT, per symbol, with evidence. This is the judgement E-01's raw count cannot make: a symbol defined in both runners is NOT automatically a defect, because the maintainer's own test is "one host does A, the other NOT A" - a real capability difference is legitimately host-shaped. Apply THAT test, and for each symbol record which side is authoritative and why, or that both are needed and why. THE FIVE LARGE HOST-SHAPED FUNCTIONS the Set already identified are the expected legitimate residue; anything BEYOND those five that is not defensibly host-specific is still-redundant code the directive was not satisfied for. Do NOT unify anything here (see the deferral list).
  - Depends on: E-01
  - Expected outcome: a per-symbol table with a disposition and evidence for all symbols from E-01, and an explicit count of the still-redundant residue; immortalized under `.aw/records/research/` with `aw research new` (do not hand-name it), since the next Set starts from it.
  - Execution state: pending

- [ ] E-03 WRITE THE CHARACTERIZATION BASELINE, AND DECLARE THAT IT IS LATE. The parent's E-02 asks for tests pinning CURRENT observable behavior of both hosts "BEFORE any child reconciles anything", following `tests/test_wtiso_characterization.py`'s precedent. That precondition is UNSATISFIABLE NOW: all eleven children have executed, so what this suite can pin is post-reconciliation behavior, not the pre-Set baseline, and it therefore CANNOT retroactively prove the reconciliations preserved behavior. Write it anyway and say exactly that, because its forward value is real: it makes the NEXT phase's changes falsifiable. PRIORITIZE THE SYMBOLS THE PARENT NAMES AS UNCOVERED on the agy side (`integrate_lane_branch`, which had ZERO references anywhere in `tests/`, plus `build_parser`, `extract_session_id`, `build_prompt`), because that asymmetry - 95 oc tests versus 21 agy - is the specific hole the item exists to close.
  - Depends on: E-02
  - Expected outcome: `tests/test_rununify_characterization.py` committed and passing, pinning both hosts' observable behavior for the named uncovered symbols, with a module docstring stating plainly that it was authored AFTER the reconciliations and therefore pins present behavior rather than the pre-Set baseline.
  - Execution state: pending

- [ ] E-04 STATE THE SET'S VERDICT AGAINST THE DIRECTIVE, in one place, and do not soften it. Using E-01 and E-02, answer: is there "one code base shared by the two runners that contains 100% of the otherwise redundant code"? If the still-redundant residue from E-02 is non-empty, the answer is NO and this plan must say so plainly, name the residue, and record that a follow-up Set is required - NOT mark the Set complete because eleven children executed. THE FOLLOW-UP SET ALREADY EXISTS AND MUST BE NAMED BY ID: `runresidue` / `gqo6if` (`.aw/records/plans/pending/20260921-runresidue-01-gqo6if-close-the-runner-unification-residue-share-the-last-forked-s.ipd.md`), authored 2026-09-22 at the maintainer's direction in the same session that resolved OQ-01, precisely so this verdict cites a real carrier rather than a promise. So this item does NOT need to propose a follow-up: it must CONFIRM that plan covers the residue E-02 measured, and report any residue symbol that plan does not name. If the residue is empty (only the five host-shaped functions remain, each defensibly host-specific), say that with the evidence. Either way, paste a bare `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: an explicit YES/NO verdict with its measured basis, the named residue if any, a statement of what a follow-up Set would own, and the pasted suite summary.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `5e4sb6` except its child table.
- THE PARENT ALREADY ANTICIPATED THIS PLAN'S SHAPE for E-02: "if the repo's conventions make a test-only change count as product code, it becomes child 00 instead, executed before child 01." The window closed, so E-03 here declares its lateness rather than claiming the precondition was met.
- THE MAINTAINER'S 2026-09-16 DIRECTIVE IS THE DEFINITION OF DONE and supersedes narrower readings of any child scope: 100 percent of otherwise-redundant code shared. The parent records that every child's OQ-03 resolved to this, and that deferral routes offered at review were REFUSED on this basis.
- SOURCE-READING TESTS ARE WORK, NOT VETOES (the parent's supporting ruling of 2026-09-16): 44 test files in this repository assert on the SHAPE of source, so a test that pins a duplication is a thing to update, not a reason to abandon a unification.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `run-20260922T003414Z-1020752/events.jsonl`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `5e4sb6` as carrying work no child covers. All eleven children are `executed`, so retirement is imminent and both E-02 and E-03 would tick unperformed. |
| F-02 | BLOCKER | AST count at authoring HEAD over `oc_runipd` and `agy_runipd` | 58 symbols are still defined in BOTH runners, totalling 2711 agy definition lines: `run_queue` 456/549, `build_parser` 296/387, `main` 234/340, `expand_selectors` 183/199, `reclaim_lanes_on_interrupt` 174/174, and more. The maintainer's directive demands 100 percent of otherwise-redundant code be shared. On this measurement the Set's definition of done is NOT met, and retiring the parent would record it as met. Whether all 58 are redundant or some are legitimately host-shaped is exactly what E-02 must decide - the count alone is not the verdict, but it is far above the five host-shaped functions the Set expected as residue. |
| F-03 | HIGH | `5e4sb6` E-02, quoted | The characterization baseline was required BEFORE any child reconciled anything, and no such suite exists in-tree (`tests/test_rununify_characterization.py` absent; only `test_wtiso_characterization.py`, the cited precedent, exists). Since all children have executed, this baseline can no longer prove behavior preservation retrospectively. E-03 writes it for forward value and says so. |
| F-04 | MEDIUM | `5e4sb6` E-02, quoted | The suite asymmetry the baseline was meant to cover is measured: 95 opencode runner tests versus 21 agy, with `integrate_lane_branch` (the second-largest divergence) having ZERO references anywhere in `tests/`. A reconciliation that changed agy behavior there would have left both suites green. |
| F-05 | LOW | `5e4sb6` E-01 execution note | E-01 is already `performed` with a DECLARED GAP: 46 of 52 class (c) symbols were left undecided because mechanical signals were silent, and the note says recording a guess would be worse than recording the gap. E-02 here inherits that unfinished judgement for whatever remains shared, and should follow the same honesty. |

## Proposed changes (ordered, validatable)

1. Measure single-implementation AST-level and repo-wide, with the metric stated (E-01).
2. Disposition every still-shared symbol as host-specific or still-redundant, with evidence (E-02).
3. Write the characterization baseline, declaring its lateness (E-03).
4. State the Set's verdict against the directive without softening it (E-04).

## Deferred / out of scope (with reason)

- UNIFYING ANY REMAINING SYMBOL. If E-02 finds still-redundant code, a follow-up Set owns the work.
  Unifying `run_queue` (456/549 lines) is not a verification task, and doing it inside a plan whose job is
  to MEASURE would destroy the independence of the measurement. E-04 records what the follow-up must own.
- `5e4sb6` E-01. Already `performed`, with its gap declared. This plan does not re-open it, though E-02
  inherits the same per-symbol judgement question for whatever is still shared.
- RETROACTIVELY PROVING BEHAVIOR PRESERVATION. It cannot be done: the baseline that would have proven it
  had to exist before the children ran, and it did not. E-03 states this rather than implying the new suite
  closes the gap.

## Scope check

- Over-scope: none.
- Under-scope: none. The parent carries E-01 (performed), E-02 and E-03; this plan covers E-02 via its own
  E-03, and E-03 via its own E-01/E-02/E-04.

## Required tests / validation

`tests/test_rununify_characterization.py` is authored by E-03 and must pass. E-04 additionally requires a
bare `python3 -m pytest`. No runner logic changes, so no behavior-affecting test is expected to move.

## Spec / documentation sync

N/A for contracts. E-02's per-symbol disposition is immortalized under `.aw/records/research/` via
`aw research new`, because the next Set starts from it. The only structural edit is the child-table row on
`5e4sb6`.

## Open questions

### OQ-01: If E-02 shows the directive is unmet, should `5e4sb6` still be allowed to retire as `executed`?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: F-02
- Resolution or deferral rationale: RAISED BY THE AUTHOR, and it is genuinely the maintainer's call because it is about what a completed Set MEANS, not about code. THE MEASUREMENT: 58 symbols are still defined in both runners (2711 agy lines) while the directive asks for 100 percent of otherwise-redundant code shared and the Set expected only five host-shaped functions as residue. So on today's evidence eleven children executed and the Set's own definition of done was not reached. TWO READINGS, and they lead to different records. (a) RETIRE IT ANYWAY: the eleven children each did what they were scoped to do, the Set's children are complete, and the residue becomes a NEW Set with its own plans; `5e4sb6` retires `executed` and this plan's E-04 verdict is the honest record of what remains. (b) DO NOT RETIRE IT: the directive is the definition of done and it is unmet, so retiring records a false completion; the parent should stay pending until a further child closes the residue, which keeps the obligation visible in `aw attention` instead of in a research file nobody re-reads. RECOMMENDATION: (a), on the reasoning that a Set's completion means its CHILDREN are complete and that carrying a parent open indefinitely is how a Set becomes a permanent fixture - provided E-04's verdict is recorded prominently and a follow-up Set is actually filed, which this plan's E-04 requires. BLOCKING because it decides whether this plan's own completion should leave the parent retirable, and because (b) would mean authoring a further child instead.
  RESOLVED 2026-09-22 BY THE MAINTAINER (asked through `/askme`): OPTION (a), RETIRE IT, AND FILE THE RESIDUE AS NEW WORK IMMEDIATELY. Their words: "Mark it done, file the rest as new work ... BUT Write the plan NOW. Don't wait." So the retirement is NOT conditional on the residue being closed, and the follow-up is NOT left as a promise this plan's E-04 merely requires: the follow-up Set `runresidue` was authored in the same session and is on disk before this question was closed, which removes the one risk the recommendation rested on (that a deferred follow-up never gets filed).
  THE NUMBER IN THE PARAGRAPH ABOVE IS WRONG AND IS CORRECTED HERE, because the maintainer decided on the corrected figure and a later reader must not re-derive the stale one. The question was raised citing 58 symbols and 2711 agy lines. RE-MEASURED 2026-09-22 at HEAD `f763be8c` by classifying each shared symbol's BODY rather than counting its NAME: of 57 symbols defined in both runners, 32 have BOTH sides delegating to `runner_shared` (a host-shaped shell over one real implementation, which is the extraction SUCCEEDING), 3 have agy delegating while oc keeps the body, 2 the reverse, and only 20 symbols totalling about 667 agy lines have NEITHER side delegating. The 58/2711 figure counted a genuinely-shared function as duplicated because each host still wraps it. So the residue is 20 symbols, not 58, and the largest functions the original figure leaned on (`run_queue` 456 lines, `main`, `build_parser`, `expand_selectors`, `retry_deferred_integrations`) are all ALREADY delegating - `run_queue` makes 10 calls into `runner_shared`. The Set therefore came much closer to the directive than the raw name count implied, and the honest verdict E-04 must record is 'substantially met, with a named 20-symbol residue' rather than 'unmet'.
  ONE MEASURED DUPLICATION IS WORTH NAMING because it is not a host difference at all: `reclaim_lanes_on_interrupt` is 174 lines on EACH side at 0.998 similarity after host-token normalisation. That is copied code, and it is the first item the follow-up Set should take.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the committed measurement method (path or pasted script), its output, the three counts, the HEAD, and the stated metric. A pairwise runner-to-runner count alone FAILS this item: F10 records that such a check passes while a third copy sits elsewhere, so the repo-wide comparison is the point.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `aw research new` artifact path (tool-created, not hand-named), plus the per-symbol table quoted for at least the ten largest still-shared symbols, each with a disposition and its evidence, plus the explicit still-redundant count. A disposition of "host-specific" asserted without applying the maintainer's "one host does A, the other NOT A" test FAILS for that symbol.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_rununify_characterization.py` output, plus the module docstring quoted showing it states the suite was authored AFTER the reconciliations and cannot prove behavior preservation retrospectively. A suite that implies it is the pre-Set baseline FAILS this item even if it passes.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the verdict quoted verbatim, its measured basis, the named residue (or a demonstration that only the five host-shaped functions remain, each with its host-specific justification), a statement of what a follow-up Set would own, and the bare `python3 -m pytest` summary line. A verdict of YES that does not reconcile with E-02's residue count FAILS this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE is E-04's verdict. This plan exists because a Set was about to
report success, and the strongest pressure on its executor will be to write a verdict that lets the Set
close. Two moves are forbidden: calling a symbol host-specific without applying the maintainer's own "one
host does A, the other NOT A" test, and writing a YES verdict that does not reconcile with E-02's residue
count. A NO verdict is a successful outcome for this plan; it is the Set that would have failed, and saying
so early is the entire value delivered.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Specifically: UNIFY NOTHING - if redundancy remains,
report it. Do not edit either runner. If the work genuinely requires a path outside the fence, make the edit
and justify it, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a
`--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`. NOTE OQ-01 is BLOCKING and
must be answered by the maintainer before this plan executes, because its answer decides whether the parent
may retire.

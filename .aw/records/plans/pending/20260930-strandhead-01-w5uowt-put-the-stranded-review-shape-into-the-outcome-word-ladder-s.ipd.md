# IPD: Put the stranded-review shape into the outcome-word ladder so the headline stops saying COMPLETED above its own stranded-work section

- Date: 2026-09-30
- Kind: child
- Concern: A run whose REVIEW was not integrated prints a green `COMPLETED` headline directly above a red `STRANDED WORK - NOT IN YOUR PROJECT:` section that names the branch the work is sitting on. The two halves of one screen contradict each other, and the `COMPLETED` half is the one a tired operator believes.
- Scope: Teach the outcome-word ladder in `render_stream.render_run_summary_table` the REVIEW stranded shape it already renders a recovery section for, by adding `review_integration_was_refused` to the two success-branch guards and to the `STRANDED` arm's condition, leaving the branch ORDER and both existing predicates untouched. Add a review-shaped case plus a relabel fence to the module that actually tests this ladder.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: aaa2xx
- Blocks-Release: next
- Set: strandhead
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: w5uowt

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `aaa2xx`, graduating plan `entv1d`'s OQ-01 (its typed `- Carrier: aaa2xx`). EVERY load-bearing claim in the backlog item was RE-MEASURED at HEAD `452455dc2` rather than trusted from its prose, and the measurement moved the plan in three places. (1) THE DEFECT REPRODUCES exactly as filed: a one-item review queue carrying `review_integrated: False` renders `Outcome: COMPLETED` above a populated `STRANDED WORK` section (F-01, pasted render). (2) THE BACKLOG'S NAMED TEST TARGET IS WRONG and following it would have put the new case in a module that cannot host it: `tests/test_run_summary_table.py` imports `run_viewer`, not `render_stream`, and contains ZERO occurrences of `render_stream` (F-06, measured `grep -c` = 0). The ladder's real test module is `tests/test_zero_dispatch_outcome.py`, which already owns the sibling `STRANDED` case, so `Scope-Paths` names that module and NOT the one the backlog item suggested. (3) THE BACKLOG'S "VERIFY FAILED AND BLOCKED STILL WIN" INSTRUCTION IS NECESSARY BUT NOT SUFFICIENT: a 32-cell status x attempts probe (F-04) found the fix also changes `queued`, `not-attempted` and `retired` from their current words to `STRANDED`, which the item does not mention. Those three are KEPT (not fenced off) because the EXEC shape already behaves that way at HEAD and dividing the two shapes would be a second inconsistency; the reasoning and the evidence are recorded in OQ-01 and E-04 rather than left for a reviewer to discover. THE FIX WAS DRIVEN, NOT ASSUMED: a probe implementation was applied, the bare suite run green at `3414 passed` with the single pre-existing unrelated failure unchanged, and six unaffected shapes were proven BYTE-IDENTICAL to HEAD (F-05).
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the run summary's HEADLINE agree with its own body for a stranded review. The recovery section already tells the operator their review never landed and names the branch; the outcome word above it still says `COMPLETED`, because the ladder asks only the EXECUTE-shaped question. This plan adds the REVIEW-shaped question that is already defined and already used one function away, so one screen stops stating two contradictory things.

This is the HUMAN-READABLE half of a defect whose MACHINE-READABLE half is owned by approved plan `entv1d` (Set `strandexit`), which makes the same shape count for the process exit code. Neither plan subsumes the other and they touch different seams; the relationship and the no-edge decision are recorded in F-07 and OQ-02.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the premise before changing anything

- [ ] E-01 Re-measure the defect at the executing HEAD and record the numbers in V-01, because every citation below is a point-in-time snapshot and this plan's own authoring already caught one rotted claim in the backlog item (its named test file, F-06). Build a one-item queue dict with `action: "review"`, a status inside the ladder's success tuple (`reviewed`), a non-empty `attempts` list, and `review_integrated: False`; render it through `render_stream.render_run_summary_table` with `pal=render_stream.Palette(False)` and record THREE facts: the outcome word, whether `render_stream.format_stranded_work_section` returns a non-empty section for the same queue, and what each of `render_stream.review_integration_was_refused` and `render_stream.integration_was_refused` returns for that item. The defect is confirmed only if the word is `COMPLETED`, the section is NON-EMPTY, and the two predicates disagree (`True` and `False` respectively). If the word is already `STRANDED`, STOP and report: the defect has been fixed or altered by other work and this plan's premise needs re-authoring rather than execution.
  - Depends on: none
  - Expected outcome: A recorded reproduction showing `COMPLETED` printed above a non-empty stranded section, with `review_integration_was_refused` True and `integration_was_refused` False for the same item.
  - Execution state: pending

- [ ] E-02 Record the BASELINE outcome word for every shape the change could touch, BEFORE editing, because this plan's central risk is relabelling an outcome that is already correct and a baseline captured after the edit cannot prove anything. Probe the cartesian product of the sixteen statuses in F-04's table against `attempts` present and absent, for BOTH shapes (an EXEC item carrying `integration_signal: "suite-failed"` and a REVIEW item carrying `review_integrated: False`), and save the resulting word for each of the 64 cells. MEASURE FROM THE WORKING TREE, NOT AN INSTALLED COPY, and verify it: assert that `render_stream.__file__` resolves under the executing checkout before trusting any cell. This is not a hypothetical caution, it is the authoring bug this plan hit - a probe script invoked by absolute path from a temp directory silently imported a DIFFERENT checkout's `agent_workflows` and produced a 32-cell table that disagreed with the correct one, which was caught only because an inline measurement of the same input contradicted it (F-08). Keep the baseline as a file so E-04 can diff against it mechanically rather than by eye.
  - Depends on: E-01
  - Expected outcome: A saved 64-cell baseline of outcome words, measured against a `render_stream` whose `__file__` was asserted to be inside the executing checkout.
  - Execution state: pending

### Task group 2: the change

- [ ] E-03 In `render_stream.render_run_summary_table`'s outcome-word ladder, add the REVIEW stranded question at exactly three sites, KEEPING THE BRANCH ORDER UNCHANGED. The three sites are the two success-branch guards that currently read `and not any(integration_was_refused(it) for it in queue)` (one in the `COMPLETED` branch, one in the `NO WORK PERFORMED` branch) and the `STRANDED` arm whose condition currently reads `elif any(integration_was_refused(it) for it in queue):`. At each, ask `review_integration_was_refused` in addition to the existing predicate, so a queue holding EITHER stranded shape fails the success guards and reaches the `STRANDED` word. DO NOT reorder the ladder, DO NOT move the `STRANDED` arm, and DO NOT touch either predicate's body: the arm's own comment records that `ys1dor`'s review measured testing a signal BEFORE the status as "a regression dressed as the feature", and the fix needs no reordering because the review shape fails the success guards for the same reason the exec shape does. EDIT BOTH SUCCESS GUARDS, NOT ONE: the two success tuples in this ladder are BYTE-IDENTICAL (plan `165lkb` F-19 records that a `replace`-with-count-1 edit misses the twin), so a single-site edit will leave `NO WORK PERFORMED` reachable for a stranded review, which F-04 measures as a real cell (`reviewed` with no attempts). Add a comment at the `STRANDED` arm naming this plan and stating that the two predicates read DIFFERENT fields written by DIFFERENT paths (`integration_signal` by the execute path, `review_integrated` by the review path), which is why both must be asked and neither can be dropped.
  - Depends on: E-02
  - Expected outcome: The ladder asks both stranded predicates at all three sites; branch order, both predicate bodies, and every other branch are unchanged.
  - Execution state: pending

- [ ] E-04 Diff the post-change 64-cell probe against E-02's baseline and ACCOUNT FOR EVERY CHANGED CELL, treating any unaccounted change as a regression to fix rather than to document. Two properties must hold. FIRST, the EXEC column must be changed at ZERO cells: this plan adds a disjunct and must not perturb the shape that already worked, so a single changed EXEC cell means the edit was mis-sited and must be corrected before proceeding. SECOND, every changed REVIEW cell must appear in F-04's expected-change list, which is exactly the fourteen cells spanning `queued`, `not-attempted`, `reviewed`, `executed`, `approved`, `substantially-complete` and `retired`; a changed cell outside that list is an unintended relabel. ALSO CONFIRM THE NEGATIVE HALF, which is what the backlog item asked for and what the ladder's comments are most protective of: `failed`, `failed-safely`, `integration-blocked`, `merge-conflict`, `blocked`, `dependency-blocked`, `fail-gate`, `not-run` and `interrupted` must each still render their OWN word for the review shape, unchanged from baseline, proving the `FAILED`, `BLOCKED` and `INTERRUPTED` branches still win for the statuses they own.
  - Depends on: E-03
  - Expected outcome: A mechanical diff showing zero EXEC cells changed, every changed REVIEW cell inside F-04's expected set, and the nine failure/blocked/interrupted statuses unchanged.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Extend `tests/test_zero_dispatch_outcome.py` with the review-shaped cases, sited in the module that actually tests this ladder rather than the one the backlog item named (F-06). Reuse the module's existing `_item` / `_state` / `_outcome_word` helpers rather than introducing a parallel fixture idiom. Add, in `ZeroDispatchOutcomeRegressionFenceTests` beside its existing `test_regression_substantially_complete_with_refusing_signal_renders_stranded`: (a) the POSITIVE case, a review item with a success-tuple status and `review_integrated: False` rendering `render_stream.STRANDED_OUTCOME`; (b) the ABSENT-KEY case, the same item with NO `review_integrated` key rendering `COMPLETED`, which is the guard that keeps the predicate from reading absence as refusal and relabelling every execute run; (c) the LANDED case, `review_integrated: True` rendering `COMPLETED`; (d) the `NO WORK PERFORMED` twin-guard case, a review item with `review_integrated: False` and `attempts: []` rendering `STRANDED`, which fails if only one of the two identical success guards was edited (E-03) and is therefore the test that catches the most likely implementation error; (e) a RELABEL FENCE parameterized over the nine failure/blocked/interrupted statuses from E-04, asserting each still renders its own word while carrying `review_integrated: False`; and (f) a PARTIAL case, a two-item queue of one stranded review plus one landed execute item rendering `STRANDED`, matching the arm's documented "one bad item colors the whole outcome" precedence. Assert against the `STRANDED_OUTCOME` CONSTANT, never the literal `"STRANDED"`, following the module's existing practice.
  - Depends on: E-04
  - Expected outcome: Six new behavioral cases in the ladder's real test module, all asserting on rendered output and the exported constant, with the twin-guard and relabel-fence cases present.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CITE BY SYMBOL OR QUOTED STRING, never by a bare line offset (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`). Every citation below names a symbol or quotes content; where an offset appears it is appended to one of those, never standing alone. This plan's authoring independently proved why: the backlog item's own test-file citation had rotted (F-06).
- TEST OUTCOMES, NOT CODE STRUCTURE (`AGENTS.md`, GUIDING_PRINCIPLES P16). Every case E-05 adds renders a summary table and asserts on the resulting word; none inspects source, counts callers, or asserts on comment text.
- ASSERT AGAINST THE EXPORTED CONSTANT. `tests/test_zero_dispatch_outcome.py` already writes `render_stream.STRANDED_OUTCOME` rather than `"STRANDED"`, and `render_stream`'s own color-selection comment states the reason: the color test is "on the constant itself" because "relying on a substring coincidence ... is how the NEXT word breaks".
- RUN THE SUITE BARE as `python3 -m pytest` (`AGENTS.md`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; adding `-n0` or a second `-q` is explicitly contrary to the contract (the latter suppresses the `N passed` line this plan must paste).
- THE LADDER'S BRANCH PRECEDENCE IS LOAD-BEARING AND SAYS SO. Three separate comment blocks inside `render_run_summary_table` state that their conjunct is "PLACED LAST IN THE SUCCESS BRANCH, WHICH IS LOAD-BEARING rather than stylistic" and that "Testing the signal BEFORE the status would RELABEL that existing outcome". This plan adds disjuncts at existing sites and reorders nothing.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT REPRODUCES AT HEAD, exactly as the backlog item describes. A one-item queue with `action: "review"`, `status: "reviewed"`, `attempts: [{"number": 1}]` and `review_integrated: False` renders `Outcome: COMPLETED` and `Progress: 1/1 [##########] 100% (1 reviewed)`, and immediately beneath it `STRANDED WORK - NOT IN YOUR PROJECT:` followed by `• rev001: REVIEW NOT INTEGRATED; its work is on its review lane (no branch recorded)`. One screen, two contradictory verdicts | driven at HEAD `452455dc2`, full render pasted in V-01 |
| F-02 | THE TWO PREDICATES DISAGREE FOR THE SAME ITEM, which is the mechanism. For that item `render_stream.review_integration_was_refused` returns `True` while `render_stream.integration_was_refused` returns `False`. The ladder asks only the second, so the item passes the success guard | driven at HEAD, both values pasted in V-01 |
| F-03 | `review_integration_was_refused` HAS EXACTLY ONE CONSUMER, confirming the backlog item's central claim at HEAD. The only call is inside `render_stream.format_stranded_work_section`; the ladder's two success guards and its `STRANDED` arm all call `integration_was_refused` alone. That is precisely why the section prints and the headline does not | `grep -n "review_integration_was_refused" agent_workflows/render_stream.py` returns the definition, one call site inside `format_stranded_work_section`, and two prose mentions; no ladder site |
| F-04 | THE FIX CHANGES FOURTEEN CELLS, NOT THE FOUR THE BACKLOG ITEM IMPLIES, and the extra ten are the reason this plan carries a mechanical diff instead of a spot check. Probing sixteen statuses against `attempts` present/absent for both shapes, the REVIEW column changes at `queued`, `not-attempted`, `reviewed`, `executed`, `approved`, `substantially-complete` and `retired` (both attempt states each). The EXEC column changes at ZERO cells. The nine failure/blocked statuses (`failed`, `failed-safely`, `integration-blocked`, `merge-conflict`, `blocked`, `dependency-blocked`, `fail-gate`, `not-run`, `interrupted`) are unchanged for both shapes | 64-cell probe driven against baseline and patched trees; table pasted in V-04 |
| F-05 | THE PROBE IMPLEMENTATION BREAKS NOTHING AND IS BYTE-IDENTICAL FOR UNAFFECTED RUNS. With the three-site change applied, the bare suite reports `1 failed, 3414 passed, 2 skipped` - the SAME single failure the clean tree reports (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, an unrelated midnight date-rollover flake asserting `2026-09-30` against `2026-10-01`). Six unaffected shapes (clean exec, landed review, review with no key, failed, blocked, exec-stranded) render BYTE-IDENTICALLY to HEAD | both suite runs and the identity comparison pasted in V-05 |
| F-06 | THE BACKLOG ITEM'S NAMED TEST TARGET CANNOT HOST THE NEW CASE, so this plan does not follow that half of its suggested fix. `tests/test_run_summary_table.py` imports `run_viewer`, `ArtifactAudit` and `runner_shared.landed_verdict`, and tests the `Landed` column of `run_viewer.render_steps_table`; `grep -c "render_stream" tests/test_run_summary_table.py` returns `0`. The ladder's real test module is `tests/test_zero_dispatch_outcome.py`, which imports `render_stream`, owns `_outcome_word`, and already contains the sibling exec-stranded case `test_regression_substantially_complete_with_refusing_signal_renders_stranded`. Two docstrings inside `render_stream.py` also cite `test_run_summary_table.py` for guarantees it does not provide; those stale citations are OUT OF SCOPE here (see Deferred) | both files read; `grep -c` measured |
| F-07 | THE SIBLING PLAN OWNS A DIFFERENT SEAM AND NEEDS NO DEPENDENCY EDGE. Approved plan `entv1d` (Set `strandexit`, `pending/`, `- Status: approved`) fixes the EXIT CODE for both stranded shapes via `runner_shared.exit_code_statuses`, and its own scope fence says DO NOT "reorder the outcome-word ladder in `format_run_summary` or change `STRANDED_OUTCOME`'s branch precedence (the headline half is backlog `aaa2xx`...)". Its `- Carrier: aaa2xx` field names this item. Its E-02 ADDS a composed predicate to `render_stream.py` but explicitly leaves both existing predicates "callable and unchanged", which are the only two symbols this plan calls | `entv1d` read in full at HEAD; its E-02, E-03 and scope fence quoted |
| F-08 | A MEASUREMENT HARNESS IMPORTED THE WRONG CHECKOUT DURING AUTHORING, and E-02 carries an assertion because of it. A probe script invoked as `python3 /tmp/.../probe.py` put its own directory on `sys.path` and resolved `agent_workflows` to a DIFFERENT checkout (`.../agent-workflows/agent_workflows/__init__.py`) instead of this lane's, reporting `QUEUED`/`COMPLETED` for cells that an inline heredoc measurement of byte-identical input reported as `STRANDED`. The contradiction was caught only because both were run. Re-driven with the script fed on stdin from the repo root, the two agree | both harnesses run on identical input; `agent_workflows.__file__` printed for each |
| F-09 | THE STRANDED SECTION ALREADY FIRES FOR THE WIDER STATUSES, so this plan's extra ten cells make the headline MATCH an existing body rather than inventing an alarm. `format_stranded_work_section` keys only on the predicate and ignores status, so it already prints the recovery block for a `not-attempted` review carrying `review_integrated: False` - today under a `QUEUED` headline | section driven at HEAD for the `not-attempted` shape; output pasted in V-04 |

## Proposed changes (ordered, validatable)

1. `agent_workflows/render_stream.py`, `render_run_summary_table`: add `review_integration_was_refused` as a conjunct to the `COMPLETED` branch's guard, as a conjunct to the `NO WORK PERFORMED` branch's guard, and as a disjunct in the `STRANDED` arm's condition. Three sites, no reordering, no predicate-body edits, plus one comment at the `STRANDED` arm recording that the two predicates read different fields written by different paths (E-03).
2. `tests/test_zero_dispatch_outcome.py`: six new cases in `ZeroDispatchOutcomeRegressionFenceTests` covering the positive review-stranded shape, the absent-key guard, the landed-review guard, the `NO WORK PERFORMED` twin-guard, a nine-status relabel fence, and a partially-stranded queue (E-05).

No other file changes. No new module, no new constant, no new exported symbol, and no change to either existing predicate.

## Deferred / out of scope (with reason)

- THE EXIT CODE. A stranded review's process exit status is owned by approved plan `entv1d` (F-07), which is already reviewed and approved for exactly that seam. Touching `runner_shared.exit_code_statuses` here would duplicate an approved change and put two plans in the same function for one defect.
  - Carrier: entv1d
  - Carrier-Evidence: .aw/records/plans/executed/20260929-strandexit-01-entv1d-make-a-stranded-run-exit-nonzero-so-the-process-code-stops-c.ipd.md
- THE TWO STALE DOCSTRING CITATIONS IN `render_stream.py`. `INTEGRATION_EARNED_SIGNALS`'s comment claims `test_run_summary_table.py` "cross-checks these two strings against `runner_shared`'s definitions", and `format_stranded_work_section`'s docstring claims `preserved_branch` "proves its own provenance in `test_run_summary_table.py`"; F-06 measures that this file contains zero `render_stream` references, so BOTH claims are false. The same file also cites a deleted `test_refusal_surfacing.py` in two places, which plan `entv1d`'s F-15 already records and also declines to repair.
  - Carrier-Declined: NO OUTSTANDING WORK REMAINS BEHIND THESE, BY MAINTAINER RULING. Each stale citation names a guard that would PIN CODE STRUCTURE (a cross-check that two string constants still match, an AST scan that every field read is produced elsewhere), and the maintainer has ruled twice that such guards are not to be restored: backlog `1bxw6o` closed `done` with "retired by suite trim; we test outcomes and functionality, never code structure or script text. Do not restore code-pinning guards", and `s4jctz` recorded "We do not test to make sure code does not change or pin imports ... Evaluate re-exports on whether functional callers use them, not based on dead code-pinning tests". `AGENTS.md` states the same rule as a standing prohibition (P16). So the only work a carrier could hold is work the maintainer has forbidden; what is left is a COMMENT naming a test that no longer exists, on two symbols this plan does not edit. Filing a carrier would record an obligation that must never be discharged.
- WIDENING `aw attention`. `review_integration_was_refused`'s own docstring notes an unmerged review "is also invisible to `aw att`". That is a different surface with a different record shape and is not a summary-table concern.
  - Carrier-Declined: ALREADY CARRIED ELSEWHERE, so a second carrier would duplicate it. The attention-side half of unmerged-lane invisibility is the subject of backlog `1z58zm` ("stranded backlog items on unmerged lane"), which is `done`, and the live residue of that surface sits with `0szu1p`; nothing about THIS plan's three ladder sites adds an unowned obligation to it. This plan narrows no claim `aw attention` makes and leaves that surface exactly as it found it.
- A `STRANDED` ROW IN A SPEC TABLE. Spec `25kzda` does not mention the stranded class at all today (`grep` finds one unrelated prose use of the word), and the one spec amendment this defect family needs is already declared by `entv1d`'s E-06 for the EXIT-CODE table. This plan changes no contract: the outcome word is already shipped and already produced for the exec shape, so no spec statement becomes false.
  - Carrier-Declined: NOTHING IS LEFT OUTSTANDING, because no spec statement becomes false. `STRANDED` is an already-shipped outcome word already produced for the execute shape; this plan makes it reachable for a second input shape whose recovery section already prints (F-09). There is no contract to amend and therefore no deferred obligation; the one amendment this defect family does need is declared by `entv1d`'s E-06 and is carried by that plan.

## Scope check

- Over-scope: none. Both declared paths are modified: `render_stream.py` at the three ladder sites (E-03) and `tests/test_zero_dispatch_outcome.py` with the new cases (E-05).
- Under-scope: none. The defect is a wrong word in one ladder; the ladder and its test module are the complete surface. The exit-code half is a different seam, already owned (F-07), and is declared as deferred rather than silently omitted.

## Required tests / validation

1. BARE SUITE, `python3 -m pytest`, with the `N passed` line pasted verbatim. It must show the same single pre-existing unrelated failure F-05 records at HEAD and no new one; if `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` passes at execution time (the flake is date-dependent) the expected result is a fully green run.
2. TARGETED MODULE, `python3 -m pytest tests/test_zero_dispatch_outcome.py`, pasted, proving the six new cases pass alongside the existing ladder fence.
3. THE 64-CELL DIFF from E-04, pasted, showing zero EXEC cells changed and every changed REVIEW cell inside F-04's expected set.
4. THE BYTE-IDENTITY CHECK from F-05 re-driven: at least the six unaffected shapes rendering identically to a pre-change capture.
5. `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

N/A WITH REASON. No spec states the ladder's branch conditions, and no documented contract becomes false. `STRANDED` is an already-shipped outcome word with an already-shipped recovery section; this plan makes the word reachable for a second input shape the section already handles (F-09), so the user-visible vocabulary is unchanged. Spec `25kzda` does not describe the stranded class (F-04 note), and the exit-code table amendment this defect family needs is declared by `entv1d`'s E-06, not here. `docs/cli-output-contract.md` contains no occurrence of `stranded`.

## Open questions

### OQ-01: Should the fix also change `queued`, `not-attempted` and `retired` to `STRANDED` for the review shape, or should those be fenced to preserve their current words?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, no human input required: CHANGE THEM, which is what the three-site fix does without special-casing. The question is real and the backlog item does not mention it, which is why it is recorded rather than left for a reviewer to find: F-04 measures that ten of the fourteen changed cells are these three statuses, so a reviewer could reasonably read them as collateral damage. THREE PIECES OF EVIDENCE SETTLE IT. FIRST, THE EXEC SHAPE ALREADY BEHAVES THIS WAY AT HEAD: a `queued`, `not-attempted` or `retired` item carrying a refusing `integration_signal` ALREADY renders `STRANDED` (F-04, EXEC column, unchanged by this plan). Fencing the review shape would mean the two shapes disagree about the same statuses, which is a second inconsistency of exactly the kind this plan exists to remove. SECOND, THE BODY ALREADY SAYS STRANDED FOR THEM: `format_stranded_work_section` ignores status entirely, so it already prints the recovery block for a `not-attempted` stranded review under a `QUEUED` headline (F-09). Keeping the word `QUEUED` would leave the identical contradiction this plan is fixing, merely at a different status. THIRD, THE RECORD IS NOT ABSURD for these statuses: a review whose own record says `review_integrated: False` HAS work that did not land regardless of the status label, and `review_integration_was_refused` tests key PRESENCE so an item that never reached the merge carries no key and is untouched (its docstring: "ABSENT IS NOT REFUSING"). NOT BLOCKING because the alternative is strictly more code for a less consistent result; REVERSIBLE by adding a status guard if a reviewer disagrees, which is why E-04 records the cells explicitly rather than burying them.

### OQ-02: Should this plan declare an `Item-Dependencies` edge on approved sibling plan `entv1d`, which also declares `render_stream.py` in its `Scope-Paths`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: NO EDGE, hence `- Item-Dependencies: none`. An `Item-Dependencies` edge means the target MUST reach a state before this plan may execute, and no ordering is required in either direction. `entv1d` E-02 ADDS a new composed predicate to `render_stream.py` and its own text requires that both existing predicates stay "callable and unchanged"; this plan calls those two existing predicates and edits three ladder sites that `entv1d`'s scope fence explicitly forbids itself from touching ("DO NOT ... reorder the outcome-word ladder in `format_run_summary` or change `STRANDED_OUTCOME`'s branch precedence"). The two changes are therefore composable in either order, and declaring an edge would make this plan undispatchable until a separate plan executes, for no correctness reason, with the runner marking it `dependency-blocked` at dispatch. THE REAL RISK IS A TEXTUAL MERGE OVERLAP IN ONE FILE, which is not what `Item-Dependencies` is for: `AGENTS.md` records that each execute item gets an isolated worktree whose changes return through the merge-and-revalidate gate, so overlap is handled there. ONE COMPOSITION NOTE FOR WHICHEVER LANDS SECOND, recorded so it is not mistaken for a conflict: if `entv1d` lands first its composed predicate will already answer both shapes, and a later executor of this plan MAY call that one predicate at the three sites instead of two by name. That is an equivalent implementation of the same behavior, not a scope change, and the E-05 cases are written against rendered OUTPUT so they pass either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The FULL rendered summary table for the review-stranded item, pasted verbatim, showing an `Outcome:` line containing `COMPLETED` and, below the table, the literal line `STRANDED WORK - NOT IN YOUR PROJECT:` with at least one `REVIEW NOT INTEGRATED` bullet. Plus the two predicate return values on the same item, pasted, showing `review_integration_was_refused` `True` and `integration_was_refused` `False`. A paraphrase or a bare "confirmed" does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The saved 64-cell baseline, pasted or summarized as a table of `status|attempts -> word` for both shapes, PLUS the printed value of `render_stream.__file__` proving the measurement ran against the executing checkout and not an installed copy (F-08). If the asserted path is outside the checkout, this item FAILS regardless of the cell values.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The `git diff` of `agent_workflows/render_stream.py`, pasted. It must show exactly three changed conditions plus comment lines, and it must NOT show any reordering of branches or any edit inside `integration_was_refused` or `review_integration_was_refused`. Confirm by inspection of the diff that BOTH success guards were edited, not one (the twin-tuple hazard, `165lkb` F-19).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The post-change 64-cell diff against V-02's baseline, pasted, with three explicit statements backed by the pasted cells: (a) the number of changed EXEC cells, which must be `0`; (b) the list of changed REVIEW cells, which must be a subset of F-04's fourteen; and (c) the nine failure/blocked/interrupted statuses each still rendering their own word for the review shape (`FAILED` for `failed`/`failed-safely`/`integration-blocked`/`merge-conflict`, `BLOCKED` for `blocked`/`dependency-blocked`/`fail-gate`/`not-run`, `INTERRUPTED` for `interrupted`). Also paste the `format_stranded_work_section` output for the `not-attempted` review shape, showing the body already named it stranded (F-09).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Both test runs pasted verbatim with their summary lines: `python3 -m pytest tests/test_zero_dispatch_outcome.py` showing the new cases passing, and the BARE `python3 -m pytest` showing its `N passed` line with no failure other than the pre-existing `test_release_exempt_setter_roundtrip_and_parity` date flake F-05 records. PLUS a falsification step, because a test that cannot fail proves nothing: revert the E-03 change with the new tests in place, paste the resulting FAILURE output showing the positive case and the twin-guard case both failing, then restore the change and re-run green. PLUS the byte-identity comparison for the six unaffected shapes, pasted, all `True`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE three-line behavioral change plus its tests, and it is deliberately small because the surface it touches is heavily fenced by prior measurements.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. A run whose REVIEW did not land stops printing a green `COMPLETED` headline above its own red stranded-work section, and prints `STRANDED` instead. Concretely: one predicate added as a conjunct to two success guards and as a disjunct to one arm in `render_stream.render_run_summary_table`, plus six cases in `tests/test_zero_dispatch_outcome.py`. No new symbol, no reordering, no predicate-body change, no spec amendment, and no exit-code change (that half is approved plan `entv1d`). THE ONE CONSEQUENCE WORTH WEIGHING is the ten cells beyond the obvious four: a `queued`, `not-attempted` or `retired` review carrying `review_integrated: False` will also newly read `STRANDED`. OQ-01 resolves that deliberately, on the evidence that the EXEC shape already does exactly this at HEAD and that the recovery section already names those items stranded in the body, so the change removes an inconsistency rather than adding an alarm; a reviewer who disagrees can fence those three statuses with a status guard, and E-04's mechanical diff is what makes that disagreement precise rather than rhetorical.

SCOPE FENCE (a DECLARATION for the runner to reconcile against, not an instruction to stop). Modify exactly the two paths in `Scope-Paths`. Specifically DO NOT: reorder the outcome-word ladder or move the `STRANDED` arm (the fix needs no reordering, and the arm's comments record a measured regression from doing so); edit the body of `integration_was_refused` or `review_integration_was_refused` (both are separately consumed, and `entv1d` E-02 requires them unchanged); edit only ONE of the two byte-identical success tuples (`165lkb` F-19); touch `runner_shared.exit_code_statuses` or any exit-code seam (owned by `entv1d`, F-07); repair the stale docstring citations to `test_run_summary_table.py` or `test_refusal_surfacing.py` (declared deferred, with reasons); add the new cases to `tests/test_run_summary_table.py`, which cannot host them (F-06); introduce a new outcome word or constant; or write a test that inspects source text instead of rendered output (P16). An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED with `aw ipd finalize --scope-reason`, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

EXECUTION CONTRACT. Commit only the files named in `Scope-Paths` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A` and never push. Paste ACTUAL runner output for every test claim; a claimed pass with no pasted summary line does not satisfy any `V-*` item here.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled transition; do not hand-edit `- Status:`. This plan declares `- Item-Dependencies: none` and depends on nothing pending (OQ-02).

# IPD: Display the matched-artifact count in the progress denominator for a zero-dispatch run

- Date: 2026-09-29
- Kind: child
- Concern: The run summary's progress denominator collapses to `1` for a zero-dispatch queue, so a run that matched 8 artifacts renders `Progress: 0/1` and `Total (0/1 items run)` directly above 8 per-artifact rows.
- Scope: Give the summary renderer a display denominator that falls back to the MATCHED count instead of to `1`, leaving the divide-guard accessor untouched along with all THREE of its live-display call sites (`runner_shared.run_ipd`'s bare binding behind the `IPD nn/NN` banner, and both hosts' `... or 1` statusline bindings).
- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_progress_denominator.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 5hf2qy
- Blocks-Release: next
- Set: 5hf2qy
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 35mjqc
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-301 through PR-304 all fixed; both rejected and chosen fixes prototyped

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301 through PR-304, all FIXED. Reviewed at `67e532f6` in a lane worktree. Structural preflight conformed before and after revision. `aw check` reports no finding against this plan, and `aw check release-gates` conforms, so the inherited `- Blocks-Release: next` gate is well formed.
  THE PLAN'S DIAGNOSIS, ITS REJECTED ALTERNATIVES AND ITS CHOSEN FIX WERE ALL REPRODUCED, INCLUDING PROTOTYPING THE FIX END TO END, because a design resolved from measurement is only as good as the measurement. Every row of the nine-shape BEFORE matrix reproduced exactly, so F-01 and F-03 hold. F-04 reproduced and is STRONGER than stated: deleting the `or 1` flips FIVE shapes to `QUEUED`, not one, and fails 8 of the 21 tests in the two suites this plan must not disturb, so the naive fix would not have shipped silently. The chosen separate-accessor fix was prototyped: the nine-shape AFTER matrix matched F-07 row for row with no outcome word changed, a unified diff of the eight-`reviewed` render touched exactly the progress line and the totals row, the two pinned suites stayed at `21 passed` UNMODIFIED, and a bare full suite reported `3246 passed, 2 skipped`. F-06's mutation went raw 0 -> 1, F-08 reproduced verbatim, and F-09's spec search returned zero hits. `render_stream.py` was restored; `git diff --stat` on it is empty.
  THE ONE SUBSTANTIVE CORRECTION IS A MISCOUNTED CALL-SITE SET. The plan says `dispatchable_work_total` is consumed by "both hosts" binding `... or 1`, and builds E-01's required docstring on that. Measured, there are THREE consumers spelled TWO ways: `runner_shared.run_ipd` binds it BARE for the `IPD nn/NN` banner, while `oc_runipd` and `agy_runipd` each add their own redundant `or 1` for the live statusline. So the hosts' `or 1` does not guard the banner, the banner relies on the accessor's internal fallback, and a docstring written from the plan's description would assert something false about a module it never names. F-06's unreachability argument is unaffected and now covers all three.
  TWO SMALLER CORRECTIONS: `b7oicl`/`4po0sc` is ONE plan (Set `b7oicl`, id6 `4po0sc`), not two, and the plan reads as if naming a pair; and V-01 now also requires a call-site census, which is the cheap falsifiable form of "no live display moved" and catches an executor who tidies the redundant host `or 1` while in the file.
  NO PRODUCTION FILE WAS LEFT MODIFIED. Two prototypes were applied, measured with full suites, and reverted.
- 2026-09-29 draft (opencode): created.
- 2026-09-29 to-review (opencode): authored from backlog item `5hf2qy`, which plan `4po0sc` filed as a REPORTED-RATHER-THAN-FIXED finding under its own scope note (naming `5hf2qy` as the carrier). Every measurement in Findings was taken IN THIS LANE at HEAD `4573a8a1` by rendering the real `render_stream.render_run_summary_table` over a nine-shape matrix and by prototyping all four candidate fixes the item listed. THE ITEM LEFT THE DESIGN CHOICE OPEN ("the choice is a judgement about what the fraction MEANS ... which is why this is filed rather than decided here") and this plan RESOLVES it from measurement rather than taste: three of the item's own suggested options were prototyped and TWO OF THEM MEASURABLY REGRESS the `4po0sc` fix that shipped one commit ago, which is what selects the fourth (F-04, F-05, OQ-01). The blast radius also turned out WIDER than the item's report: the same collapse hits an all-already-executed queue, which the item never mentions (F-03). No spec amendment is required and no `.spec.md` file is declared (F-09).

## Goal

Make the run summary's progress fraction agree with the table printed beneath it. A run that matched eight artifacts and dispatched none must render `Progress: 0/8` and `Total (0/8 items run)`, not `0/1`, while every outcome word, every live-banner count, and every already-honest shape stays byte-identical.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: separate the display denominator from the divide guard

- [ ] E-01 Add `progress_display_total(queue)` to `agent_workflows/render_stream.py`, beside `dispatchable_work_total`, returning `0` for an empty queue, the true dispatchable count when that count is non-zero, and `len(queue)` (the MATCHED count) when the queue is non-empty but nothing is dispatchable. Its docstring must state the measured defect (F-01), must state why the fallback is the matched count rather than `1` (F-02), and must state why this is a SECOND accessor rather than an edit to `dispatchable_work_total` (F-06: THREE call sites consume that one for live display, where the zero case provably cannot arise, and where changing the value would change the `IPD nn/NN` banner this plan has no business touching).
  NAME THE THREE CONSUMERS CORRECTLY IF THE DOCSTRING NAMES THEM AT ALL. Measured at review: `runner_shared.run_ipd` binds it BARE for the `IPD nn/NN` banner, and `oc_runipd` and `agy_runipd` each add their own `or 1` for the live statusline. A docstring asserting that "both hosts" guard the banner would be wrong on the module and on the spelling; either state all three accurately or say only "its live-display consumers" without enumerating.
  - Depends on: none
  - Expected outcome: `progress_display_total` returns 8 for the eight-`reviewed` shape, 5 for the five-pre-executed shape, 6 for the ten-member/four-pre-executed shape, 1 for the single-`reviewed` shape, and 0 for an empty queue, while `dispatchable_work_total` returns exactly what it returns today for all five.
  - Execution state: pending

- [ ] E-02 In `render_run_summary_table`, consume `progress_display_total` for the rendered fraction ONLY. Concretely: the `total_items` binding feeding `format_progress_bar(completed_count, total_items, width=10)` and the `total_label = f"Total ({completed_count}/{total_items} items run)"` row. The two `and total_items > 0` conditions in the outcome-word chain must keep reading a value that is `>0` for a non-empty queue, so the `COMPLETED` and `NO WORK PERFORMED` branches `4po0sc` just landed are unaffected; record in a comment that feeding those guards a true `0` was PROTOTYPED and relabels both branches to `QUEUED` (F-04), which is why the guard and the display are now separate reads.
  - Depends on: E-01
  - Expected outcome: the eight-`reviewed` shape renders `Progress: 0/8  [          ]   0% (8 reviewed)` and `Total (0/8 items run)` with `Outcome: NO WORK PERFORMED` unchanged; the five-pre-executed shape renders `0/5` with `Outcome: COMPLETED` unchanged.
  - Execution state: pending

- [ ] E-03 Add `tests/test_zero_dispatch_progress_denominator.py` covering, by rendering the real `render_run_summary_table` and asserting on its output text: (a) the eight-`reviewed` shape's progress line and totals row now name 8, and the count in the fraction equals the number of per-artifact rows rendered in the same table; (b) the all-already-executed shape now names 5 and still reads `COMPLETED`; (c) the single-`reviewed` shape is BYTE-IDENTICAL to today, which is what proves `4po0sc`'s pinned assertion is not disturbed; (d) the ten-member/four-pre-executed shape is byte-identical, which proves `progdenom`'s live-workload denominator is not disturbed; (e) an empty queue still renders `0/0`; and (f) `dispatchable_work_total` itself is unchanged for every one of those shapes, which is the falsifiable form of E-01's "the banner is untouched" claim.
  - Depends on: E-02
  - Expected outcome: the new test file passes, and `tests/test_zero_dispatch_outcome.py` plus `tests/test_run_progress_count.py` pass unmodified.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE SHARED PREDICATE, CONSUMED BY THREE CALL SITES, IS A DELIBERATE INVARIANT HERE, so a fix must not fork it. `runner_shared` (`progdenom` comment at the `IPD nn/NN` banner) states the reason: "One shared predicate with the summary bar, so the banner and the summary cannot disagree about how much work a run holds." That is why E-01 ADDS an accessor instead of editing the existing one.
- THE THREE CALL SITES ARE NOT ALL SPELLED THE SAME WAY, and the difference matters for E-01's docstring. Measured: `runner_shared.run_ipd` binds `total = dispatchable_work_total(state["queue"])` BARE (no `or 1`) for the `IPD nn/NN` banner, while `oc_runipd` and `agy_runipd` each bind `total_items = dispatchable_work_total(queue) or 1` for their live 4-line statusline. So the banner relies on the accessor's OWN internal `or 1` and the two statuslines add a SECOND, redundant one. Do not write a docstring or a comment claiming the hosts' `or 1` guards the banner; it does not, and the banner is a different call site in a different module. F-06's unreachability argument is unaffected and holds for all three (see F-06 as revised).
- A RENDERER MUST BE REPRODUCIBLE FROM `state.json` ALONE. `render_run_summary_table`'s `ys1dor` comment records the rejected alternative and its measured consequence: a design that derived the verdict from a filesystem audit "silently REWROTE HISTORY" when re-rendering a recovered run. Everything this plan reads is already in the queue.
- AGENTS.md: tests must assert observable behavior and outcomes. E-03 therefore drives the real renderer and asserts on rendered text, and specifically does NOT read production source with `inspect`/`ast` to assert the `or 1` literal is gone.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT REPRODUCES EXACTLY AS FILED.** Rendering the real `render_stream.render_run_summary_table` with eight `reviewed`/zero-attempt items yields `Progress: 0/1  [          ]   0% (8 reviewed)` and `Total (0/1 items run)` with EIGHT per-artifact rows between them. The denominator says one, the table shows eight, and the status summary in the same parenthesis says eight. | Rendered in this lane at HEAD `4573a8a1`; full table pasted under "Measured evidence" below. `render_stream.dispatchable_work_total` returned `1` for that queue. |
| F-02 | THE CAUSE IS THE TRAILING `or 1`, AND IT IS TWO DECISIONS WELDED INTO ONE EXPRESSION. `dispatchable_work_total` ends `return sum(1 for item in queue if item_is_dispatchable_work(item)) or 1`. Its docstring justifies only the DIVIDE GUARD ("so a caller dividing by it cannot raise"); nothing justifies the collapsed DISPLAY value, which is the unchosen side effect. Splitting the two reads is therefore the minimal honest fix, and it leaves the documented guarantee intact for its stated consumer. | Read of `render_stream.dispatchable_work_total`; the quoted docstring clause is the only rationale given for the fallback. |
| F-03 | **THE BLAST RADIUS IS WIDER THAN THE ITEM REPORTS, which changes the test matrix.** The item describes only the zero-dispatch `reviewed` shape. Measured, an ALL-ALREADY-EXECUTED queue hits the identical collapse: five `executed` members render `Progress: 0/1` / `Total (0/1 items run)` above five rows, with `Outcome: COMPLETED`. So does a mixed `[executed, executed, reviewed]` queue (`0/1` above three rows). Any fix must be asserted on that shape too, which is why E-03 pins it. | Nine-shape BEFORE/AFTER matrix run in this lane; the `all 5 pre-executed` and `mixed 2 pre-exec 1 reviewed` rows both read `0/1` before. |
| F-04 | **THE OBVIOUS FIX (DELETE THE `or 1`) MEASURABLY REGRESSES THE FIX THAT SHIPPED ONE COMMIT AGO.** Prototyped: returning the true `0` makes the eight-`reviewed` shape render `Outcome: QUEUED` and `Progress: 0/0`, because the outcome chain's two `and total_items > 0` conditions gate BOTH the `COMPLETED` branch and the `NO WORK PERFORMED` branch `4po0sc` added. That would silently undo plan `4po0sc` (Set `b7oicl`, executed 2026-09-28; review correction, the plan previously wrote "`b7oicl`/`4po0sc`" as if naming two plans) and also relabel the legitimately-`COMPLETED` all-pre-executed run. This is the single most important finding in this table: it is the reason the fix is two reads rather than one deletion. THE REGRESSION IS WIDER THAN ONE SHAPE, measured at review: FIVE of the nine shapes flip their outcome word to `QUEUED` (eight-`reviewed`, one-`reviewed`, two-`reviewed`, all-five-pre-executed, and mixed), which is exactly the set whose RAW dispatchable count is 0. The empty shape already read `QUEUED` and is unchanged. AND IT WOULD NOT SHIP SILENTLY: the naive fix fails 8 of the 21 tests in the two suites this plan must not disturb. That does not weaken the finding, it strengthens the plan's choice, and it is worth stating so an executor who tries the deletion recognises the failures as THIS predicted regression rather than as unrelated breakage. | Prototyped in this lane by substituting a no-`or 1` implementation: the eight-`reviewed` shape moved from `NO WORK PERFORMED` to `QUEUED`; output pasted under "Measured evidence". Re-prototyped at review at HEAD `67e532f6`: five shapes flip to `QUEUED`, and `python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_run_progress_count.py` reports `8 failed, 13 passed`. |
| F-05 | THE ITEM'S THIRD SUGGESTED OPTION (SUPPRESS THE BAR ENTIRELY) IS REJECTED ON COST, NOT TASTE. The progress line is load-bearing in a byte-pinned assertion: `tests/test_zero_dispatch_outcome.py::test_changed_shape_byte_identity` asserts `lines[3].strip()` equals `"│ Progress: 0/1  [          ]   0% (1 reviewed)"` and asserts a unified diff shows a change on the Outcome line ONLY. Deleting the line for zero-dispatch runs would break that test's line indexing and force an edit to the proof `4po0sc` left behind. Rendering an honest denominator instead keeps that test passing UNMODIFIED, which is a stronger no-regression signal than adjusting it. | Read of `tests/test_zero_dispatch_outcome.py::test_changed_shape_byte_identity`; the single-`reviewed` shape's denominator is `1` both before and after this plan (F-07), so the pinned string is untouched. |
| F-06 | **THE LIVE BANNER'S AND STATUSLINE'S ZERO CASE PROVABLY CANNOT ARISE, so leaving `dispatchable_work_total` alone costs nothing.** THREE call sites consume it, spelled two different ways (review correction; the plan previously said "both hosts" and implied one spelling): `runner_shared.run_ipd` binds it BARE for `IPD {seq:02d}/{total}`, and `oc_runipd` plus `agy_runipd` each bind `dispatchable_work_total(queue) or 1` for the live statusline. All three are reached only for an item BEING DISPATCHED, and by then `runner_shared.run_ipd` has already run `item.setdefault("attempts", []).append(attempt)` followed by `item["status"] = "running"`, so `item_is_dispatchable_work` returns True for that item and the raw count is >= 1. Prototyped on the eight-`reviewed` queue: raw count 0 before that mutation, 1 after. So the collapsed fallback never decides any live display, and the hosts' extra `or 1` is redundant belt-and-braces rather than the thing protecting the banner. | Prototyped the pre-banner mutation from `runner_shared.run_ipd` in source order (`append(attempt)` then `item["status"] = "running"`): raw dispatchable went 0 -> 1. Reproduced at review at HEAD `67e532f6`, with all three call sites enumerated by `rg dispatchable_work_total agent_workflows/*.py`. |
| F-07 | THE CHOSEN FIX CHANGES EXACTLY THE DISHONEST SHAPES AND NOTHING ELSE. Prototyped across nine shapes: the fraction changes for the eight-`reviewed` (`0/1`->`0/8`), two-`reviewed` (`0/1`->`0/2`), all-pre-executed (`0/1`->`0/5`) and mixed (`0/1`->`0/3`) shapes, and is byte-identical for single-`reviewed` (`0/1`, where matched and fallback coincide), ten-member/four-pre-executed (`6/6`), all-live-done (`3/3`), single-live-queued (`0/1`) and empty (`0/0`). THE OUTCOME WORD IS UNCHANGED FOR ALL NINE. | Nine-shape BEFORE/AFTER matrix, `changed?` column pasted under "Measured evidence"; no row reports `OUTCOME!`. |
| F-08 | THE FALLBACK VALUE IS THE SAME NUMBER THE DISPOSITION SUMMARY ALREADY PRINTS, so the two surfaces agree by construction rather than by coincidence. `run_selection_policy.summarize_dispositions` documents that "THE COUNTS SUM TO THE NUMBER OF ENTRIES", and rendering it on the eight-item queue prints `total: 8 matched, 0 acted on, 8 not acted on`. So `len(queue)` IS the matched count, and a reader seeing `0/8` above `8 matched` sees one number twice instead of two numbers in conflict. | Ran `run_selection_policy.render_disposition_summary` on the eight-item queue: `NO WORK WAS PERFORMED: this run matched 8 artifact(s) and acted on NONE of them` and `total: 8 matched, 0 acted on, 8 not acted on`. |
| F-09 | NO SPEC AMENDMENT IS REQUIRED. The rendered progress fraction is not specified as a byte format by any `.spec.md`; `4po0sc` established the adjacent reading for the outcome vocabulary in the same renderer (spec `25kzda` Section 5.6's vocabulary "is not a closed enum"). A denominator that counts matched artifacts in the zero-dispatch case contradicts no written contract, so no `.spec.md` path is declared in `- Scope-Paths:`. | Searched the specs tree for a pinned progress-line format; the only byte-level pin found is the test in F-05, which this plan keeps passing unmodified. |

### Measured evidence

INDEPENDENTLY REPRODUCED AT REVIEW, at HEAD `67e532f6`, including the chosen fix itself. Every row of the nine-shape BEFORE matrix reproduced exactly (`0/1` for the eight-`reviewed`, one-`reviewed`, two-`reviewed`, all-five-pre-executed, mixed and one-live-queued shapes; `6/6`, `3/3` and `0/0` for the rest), with the same outcome word in every row, so F-01 and F-03 hold. F-04 reproduced and is stronger than the plan claims: deleting the `or 1` not only relabels the eight-`reviewed` shape to `QUEUED` but also relabels the one-`reviewed`, two-`reviewed`, all-pre-executed and mixed shapes, and it FAILS 8 of the 21 tests in the two pinned suites (`8 failed, 13 passed`), so the naive fix is caught by the existing suite rather than shipping silently. The chosen fix was then prototyped end to end: the nine-shape AFTER matrix matched F-07 row for row (`0/8`, `0/1`, `0/2`, `0/5`, `6/6`, `3/3`, `0/3`, `0/0`, `0/1`) with no outcome word changed, the two pinned suites stayed at `21 passed` UNMODIFIED, and a BARE full suite reported `3246 passed, 2 skipped, 3 warnings`. A unified diff of the eight-`reviewed` render before and after the prototype touches exactly two lines, the progress line and the totals row, confirming V-02's scope claim. F-08 reproduced verbatim (`total: 8 matched, 0 acted on, 8 not acted on`), F-09 reproduced (`rg 'Progress:' .aw/records/specs/` returns zero hits), and F-06's mutation went raw 0 -> 1 as stated. `agent_workflows/render_stream.py` was restored and `git diff --stat` on it is empty.

Rendered in this lane at HEAD `4573a8a1`, eight `reviewed`/zero-attempt items (F-01). Note `0/1` in both the progress line and the totals row, with eight rows between them:

```text
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ AW RUN SUMMARY: run-repro (aw oc run)                                                                             │
│ Outcome: NO WORK PERFORMED   Duration: 0s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)                  │
│ Progress: 0/1  [          ]   0% (8 reviewed)                                                                     │
├─────┬─────┬──────┬───────┬────────┬──────────┬────────┬──────────┬───────┬─────────┬────────┬─────────┬───────────┤
│ Run │ Pos │ ID6  │ Set   │ Action │ Status   │ Verify │ Duration │ Spend │ Tok tot │ Tok in │ Tok out │ Tok cache │
├─────┼─────┼──────┼───────┼────────┼──────────┼────────┼──────────┼───────┼─────────┼────────┼─────────┼───────────┤
│  01 │  01 │ it01 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  02 │  02 │ it02 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  03 │  03 │ it03 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  04 │  04 │ it04 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  05 │  05 │ it05 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  06 │  06 │ it06 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  07 │  07 │ it07 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
│  08 │  08 │ it08 │ wtiso │ review │ reviewed │ -      │        - │     - │       - │      - │       - │         - │
├─────┴─────┴──────┴───────┴────────┴──────────┴────────┼──────────┼───────┼─────────┼────────┼─────────┼───────────┤
│ Total (0/1 items run)                                 │       0s │ $0.00 │       0 │      0 │       0 │         0 │
╰───────────────────────────────────────────────────────┴──────────┴───────┴─────────┴────────┴─────────┴───────────╯
```

Deleting the `or 1` outright, which is the fix the item lists first and which F-04 rejects. The progress line becomes honest and THE OUTCOME WORD REGRESSES from `4po0sc`'s verdict to `QUEUED`:

```text
BEFORE (or 1) -> Outcome: NO WORK PERFORMED   |  Progress: 0/1  [          ]   0% (8 reviewed)  |  Total (0/1 items run)
AFTER (no or 1) -> Outcome: QUEUED            |  Progress: 0/0  [          ]   0% (8 reviewed)  |  Total (0/0 items run)
```

Re-prototyped at review, the same deletion over all nine shapes. FIVE outcome words regress, not one, and the two pinned suites catch it:

```text
shape                          prog    total   outcome            vs clean
8 reviewed (THE BUG)           0/0     0/0     QUEUED             OUTCOME REGRESSED (was NO WORK PERFORMED)
1 reviewed                     0/0     0/0     QUEUED             OUTCOME REGRESSED (was NO WORK PERFORMED)
2 reviewed                     0/0     0/0     QUEUED             OUTCOME REGRESSED (was NO WORK PERFORMED)
all 5 pre-executed             0/0     0/0     QUEUED             OUTCOME REGRESSED (was COMPLETED)
10 mem 4 pre-exec              6/6     6/6     COMPLETED
3 live all done                3/3     3/3     COMPLETED
mixed 2 pre-exec 1 reviewed    0/0     0/0     QUEUED             OUTCOME REGRESSED (was NO WORK PERFORMED)
empty                          0/0     0/0     QUEUED
1 live queued                  0/1     0/1     QUEUED

$ python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_run_progress_count.py
8 failed, 13 passed in 2.04s
```

The CHOSEN fix, re-prototyped at review, over the same nine shapes and the full suite:

```text
shape                          prog    total   outcome
8 reviewed (THE BUG)           0/8     0/8     NO WORK PERFORMED
1 reviewed                     0/1     0/1     NO WORK PERFORMED
2 reviewed                     0/2     0/2     NO WORK PERFORMED
all 5 pre-executed             0/5     0/5     COMPLETED
10 mem 4 pre-exec              6/6     6/6     COMPLETED
3 live all done                3/3     3/3     COMPLETED
mixed 2 pre-exec 1 reviewed    0/3     0/3     NO WORK PERFORMED
empty                          0/0     0/0     QUEUED
1 live queued                  0/1     0/1     QUEUED

$ python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_run_progress_count.py
21 passed in 1.99s
$ python3 -m pytest
3246 passed, 2 skipped, 3 warnings in 49.09s
```

The chosen fix (a separate display accessor) over nine shapes. `PROGRESS` marks a changed fraction; no row reports a changed outcome (F-07):

```text
shape                          BEFORE total/outcome               AFTER total/outcome                changed?
8 reviewed (THE BUG)           0/1 NO WORK PERFORMED              0/8 NO WORK PERFORMED              PROGRESS
1 reviewed                     0/1 NO WORK PERFORMED              0/1 NO WORK PERFORMED
2 reviewed                     0/1 NO WORK PERFORMED              0/2 NO WORK PERFORMED              PROGRESS
all 5 pre-executed             0/1 COMPLETED                      0/5 COMPLETED                      PROGRESS
10 mem 4 pre-exec              6/6 COMPLETED                      6/6 COMPLETED
3 live all done                3/3 COMPLETED                      3/3 COMPLETED
mixed 2 pre-exec 1 reviewed    0/1 NO WORK PERFORMED              0/3 NO WORK PERFORMED              PROGRESS
empty                          0/0 QUEUED                         0/0 QUEUED
1 live queued                  0/1 QUEUED                         0/1 QUEUED
```

Baseline for the two suites this plan must not disturb, run in this lane before any change:

```text
$ python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_run_progress_count.py
21 passed in 2.89s
```

## Proposed changes (ordered, validatable)

1. `agent_workflows/render_stream.py`: add `progress_display_total(queue)` beside `dispatchable_work_total`, with the rationale from F-02, F-04 and F-06 in its docstring (E-01).
2. `agent_workflows/render_stream.py`: in `render_run_summary_table`, read the new accessor for the progress bar and the totals label, keeping the outcome chain's two `> 0` guards on a value that stays `>0` for a non-empty queue (E-02).
3. `tests/test_zero_dispatch_progress_denominator.py`: new regression test over the six shapes named in E-03, including the two byte-identity shapes and the assertion that `dispatchable_work_total` is unchanged (E-03).

## Deferred / out of scope (with reason)

- THE OUTCOME WORD IS NOT TOUCHED. `4po0sc` (executed 2026-09-28) owns it, and F-04 is the measurement that this plan's job is to PRESERVE that word rather than revisit it.
  - Carrier-Declined: Nothing is owed. This row records a PROHIBITION on this plan, not a deferred defect: F-04 measures the outcome word as CORRECT today (`NO WORK PERFORMED` for the eight-`reviewed` shape, `COMPLETED` for the all-pre-executed one), so there is no fault to carry. The prohibition is enforced inside this plan by V-02's requirement that the word be identical in both renders and that no row of the nine-shape matrix report a changed outcome.
- `dispatchable_work_total` ITSELF IS NOT CHANGED, and none of its three call sites is edited: neither host's `total_items = dispatchable_work_total(queue) or 1` statusline binding, nor `runner_shared.run_ipd`'s BARE `total = dispatchable_work_total(state["queue"])` behind the `IPD nn/NN` banner. F-06 measures why the zero case cannot reach any of them; changing the shared predicate would alter that announcement, which no reported defect asks for.
  - Carrier-Declined: Nothing is owed, because F-06 measures the fallback as UNREACHABLE on that path rather than merely undesirable: at banner time the dispatched item is already `running` with an appended attempt, so the raw dispatchable count is >= 1 and the `or 1` never decides the banner. An obligation would assert a latent defect that measurement says is not there. The residual readability cost (the `or 1` still visible in that function) is recorded in `- Under-scope:` and answered by E-01's required docstring, not by future work.
- THE LIVE 4-LINE STATUSLINE IS NOT TOUCHED. `format_statusline_lines` takes `total_items` from its caller, so it inherits whatever the host passes; this plan changes only the exit summary. A live run's in-flight fraction always has a dispatchable item by F-06.
  - Carrier-Declined: Nothing is owed, for F-06's reason applied to the same value one call deeper: the statusline receives `total_items` from the host binding, and it is only ever rendered for an item being dispatched, so its denominator is never the collapsed fallback. No measurement in this plan shows a dishonest live fraction, so filing an item would record a defect nobody has observed.
- THE NUMERATOR IS NOT TOUCHED. `completed_count` is already 0 for every shape measured here, so it is not part of this defect; `progdenom` and `prpipy` own the numerator and `execution_index`.
  - Carrier-Declined: Nothing is owed. The numerator is measured CORRECT for every shape in the matrix (0 where nothing ran, 6/6 and 3/3 where work completed), and `progdenom` plus `prpipy` already aligned it with the denominator predicate. There is no outstanding numerator work to hand to a carrier.
- THE `(8 reviewed)` STATUS SUMMARY AND THE DISPOSITION BLOCK ARE NOT TOUCHED. Both already report eight honestly (F-01, F-08); they are the evidence the fraction was wrong, not additional defects.
  - Carrier-Declined: Nothing is owed, and this row exists to prevent a misreading rather than to defer work. Both surfaces are measured CORRECT (the parenthesis reads `(8 reviewed)`; the disposition summary reads `total: 8 matched, 0 acted on, 8 not acted on`), and F-08 makes them the reference the new denominator is made to agree WITH. Changing either would move the number this plan treats as ground truth.

## Scope check

- Over-scope: none. Two files, one new accessor, two call sites in one function, one new test file.
- Under-scope: the plan fixes the RENDERED fraction only. It deliberately leaves `dispatchable_work_total` returning `1` for a zero-dispatch queue (F-06), so a future reader auditing that function in isolation still sees the `or 1`. That is accepted rather than hidden: the fallback remains correct for its documented divide-guard purpose, and E-01's docstring is required to say so, naming this plan's separation so the next reader does not "simplify" the two accessors back into one and silently reintroduce F-04.

## Required tests / validation

- The new `tests/test_zero_dispatch_progress_denominator.py`, driving the real renderer (no source introspection).
- `tests/test_zero_dispatch_outcome.py` and `tests/test_run_progress_count.py` must pass UNMODIFIED; they are the byte-level pins for `4po0sc` and `progdenom` respectively, and needing to edit either is a signal the fix regressed one of them (F-05).
- The bare full suite, `python3 -m pytest`, compared against the pre-change baseline captured in this lane by failing NODE IDS rather than totals.
- `aw check`, `aw ipd lint --phase pre-transition`, and `aw sanitize --agent`.
- `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` and nothing another party changed.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs the rendered progress fraction's byte format (F-09), so no spec path is declared in `- Scope-Paths:`. The rationale that would otherwise go in a spec lives in `progress_display_total`'s docstring, which E-01 requires to carry the measured defect, the reason the fallback is the matched count, and the reason the two accessors stay separate.

## Open questions

### OQ-01: Should the zero-dispatch fraction read `0/8` (matched artifacts) or be suppressed in favour of the disposition summary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, as `0/8`. The backlog item left this open deliberately and listed three candidates. Suppressing the bar is rejected on measured cost (F-05: it breaks `4po0sc`'s byte-pinned `lines[3]` assertion and its line indexing, forcing an edit to the proof that plan left behind). Rendering the true `0/0` is rejected because it measurably regresses the outcome word (F-04). `0/8` is selected because it is the number the disposition summary on the same screen already prints as `8 matched` (F-08), so the two surfaces agree by construction. The fraction's MEANING is thereby stated as "artifacts this run matched" for a zero-dispatch run and remains "work this run can do" whenever anything is dispatchable; that duality is the honest reading of a bar whose numerator is 0 either way, and it is confined to the summary renderer so the live banner keeps the single "dispatchable work" unit (F-06).

### OQ-02: Should the all-already-executed shape (F-03) be fixed in this plan, given the item never mentions it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, yes, because it is the SAME line of the same function with the same cause, and it is fixed by the same one-word change with no additional code. Splitting it into a second plan would mean two plans editing one expression in one function, which is the coupling `4po0sc`'s own scope note warned against. The shape is pinned explicitly in E-03(b) BECAUSE the item does not mention it, so a reviewer can see the widened claim was tested rather than assumed, and E-03(b) also asserts its `COMPLETED` word survives (F-04's regression, measured on exactly this shape).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a transcript calling BOTH accessors on the five shapes named in E-01's expected outcome, showing `progress_display_total` returning 8, 5, 6, 1, 0 and `dispatchable_work_total` returning 1, 1, 6, 1, 0 for the same inputs. (Re-measured at review at HEAD `67e532f6`, `dispatchable_work_total` returns exactly 1, 1, 6, 1, 0 on those five shapes, and the RAW pre-guard count is 0, 0, 6, 0, 0, so the five expected values for the new accessor are arithmetically consistent with its stated rule.) The second half is the point: it is the falsifiable form of "the shared divide guard is untouched", so a transcript showing only the new accessor does NOT satisfy this item. Paste the new docstring and confirm by reading it that it states the measured defect, the matched-count rationale, and the reason the accessors are separate; if it enumerates the consumers, confirm it names all THREE correctly (`runner_shared.run_ipd` bare, both hosts with their own `or 1`) rather than "both hosts".
  ALSO PASTE A `rg dispatchable_work_total agent_workflows/*.py` AT THE EXECUTING HEAD and confirm the only changed line in that output is the ADDITION of the new accessor's definition, i.e. that `runner_shared.run_ipd`'s bare binding and both hosts' `or 1` bindings are textually untouched. That is the cheap falsifiable form of "no live-display call site moved", and it catches an executor who "tidied" the redundant host `or 1` while in the file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the FULL rendered summary table for the eight-`reviewed` shape before and after the change (the BEFORE is already pasted under "Measured evidence"; re-render it at the executing HEAD rather than copying it), showing `Progress: 0/8` and `Total (0/8 items run)` after, and showing `Outcome: NO WORK PERFORMED` in BOTH. Paste a unified diff of the two renders and confirm it touches ONLY the progress line and the totals row: no per-artifact row, no diagnostics block, no outcome line. Then paste the same before/after pair for the all-pre-executed shape showing `0/1`->`0/5` with `Outcome: COMPLETED` in both (F-03, OQ-02). Finally, paste the nine-shape matrix at the executing HEAD and confirm no row reports a changed outcome word, which is what proves F-04 was avoided rather than merely intended.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test file's own run output with its passing count. Paste `python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_run_progress_count.py` output and state it against this lane's pre-change baseline of `21 passed`; both files must be UNMODIFIED, so also paste `git diff --name-only` and confirm neither appears (F-05). Carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line, compared against the pre-change baseline captured in this lane by failing NODE IDS rather than totals; paste `aw check`; paste `aw ipd lint --phase pre-transition`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly the two paths in `- Scope-Paths:` and nothing another party changed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; do not execute it from this authoring turn.

On execution, honor the repository execution contract: commit ONLY the paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` or a bare/`-a` commit, and never push. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit attempt, since this is a shared checkout and another party's restored path can otherwise enter the commit. Paste ACTUAL runner output for every test claim; do not report a suite as passing without it.

Post-gate lifecycle: after every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd finalize` / `aw ipd set executed`), never by hand-editing terminal state. Do not claim done while any `V-*` result is `pending`.

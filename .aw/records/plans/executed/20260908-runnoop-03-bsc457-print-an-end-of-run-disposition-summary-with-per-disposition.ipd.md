# IPD: Print an end-of-run disposition summary with per-disposition counts and the exact remedy command

- Date: 2026-09-08
- Kind: child
- Concern: There is no authoritative closing answer to "what did this invocation actually do?", and the one thing that IS printed at exit reads as a failure when nothing was attempted. MEASURED 2026-08-29 (backlog `em0z50`): `aw oc run wtiso` matched 8 plans, acted on none, and the closing output the operator reacted to was `No OpenCode session was captured for this run.` (find it by symbol in `render_continuation_hint`, both hosts). That sentence describes a launch that failed. Nothing launched, and nothing said so.
  "ITS ONLY CLOSING OUTPUT" IS FALSE AND THE OVERSTATEMENT CHANGES WHAT E-01 MUST BUILD, corrected at review 2026-09-09 the same way child 02's review corrected its twin claim (that plan's F-8/PR-601). Rendering the REAL `render_run_summary_table` with one `reviewed`/zero-attempt item prints a full bordered table: `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)`, a totals row, and a per-artifact row `01 | 01 | abc123 | wtiso | execute | reviewed`. So a zero-action run ALREADY prints a per-artifact listing and a count line. What is missing is (a) the REASON beside the disposition, (b) the REMEDY, and (c) a correct verdict. AN EXECUTOR WHO BELIEVES THE STRONGER CLAIM WILL BUILD A SECOND QUEUE TABLE, satisfying every word of this plan while fixing nothing an operator cares about, and that is the specific failure this correction exists to prevent. Design the summary as the thing the table is NOT: reason-bearing, remedy-bearing, and honest about zero work.
  THE SUMMARY TABLE THAT DOES EXIST AGREES WITH THE WRONG ANSWER. Re-measured at review 2026-09-09 by rendering `render_run_summary_table` with one `reviewed` item: `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)`, and NO diagnostic line. The COMPLETED verdict comes from a status tuple containing `reviewed` (find it by the `outcome_str = "COMPLETED"` assignment) and the silence comes from the diagnostics block keying on a five-status allowlist that `reviewed` is not a member of (find it by the `Diagnostics / Blocked Items:` heading). A green 100% for zero work performed, with a launch-failure sentence underneath it.
  A COUNT LINE EXISTS BUT IS NOT A DISPOSITION SUMMARY. The table's progress line already builds `"1 reviewed"`-style counts from `status_counts`, so the aggregation shape is present. What is missing is that it counts QUEUE STATUSES rather than dispositions, it carries no remedy, and it is rendered inside the table rather than as the authoritative closing statement.
  `status_summary_str` IS NOT A FUNCTION AND CANNOT BE CALLED, corrected at review: it is a LOCAL VARIABLE inside `render_run_summary_table` (assigned at the "Status summary line" comment, consumed one place, in the `Progress:` line). A repo-wide grep finds exactly those two occurrences and no definition. So there is no aggregation helper to reuse or import, and E-01 writes its own counting; the earlier framing "the aggregation substrate is present" overstated a local variable into a reusable API. Nothing else in the design depends on it, since E-01 deliberately uses a different denominator anyway.
  ALSO CORRECTED: THE ZERO-ACTION SUMMARY IS NOT MISSING ITS GUARANTEE THE WAY THIS PLAN ASSUMED. The table DOES render for a `reviewed`-only queue (measured above), so E-03's "print even when zero were acted on" is about the NEW summary block, not about rescuing a table that stays silent. The genuinely unguaranteed thing is the summary block this plan adds.
  THE `all_success` COUPLING IS THE TRAP AN EXECUTOR WILL HIT. The misleading footer and the resume hint come from the SAME function, `render_continuation_hint`, whose `all_success` predicate reads `SUCCESS_STATES` in both hosts. Child 01 (`zz5yxq`) changes what that constant decides for an execute item, so the footer's behavior MOVES when child 01 lands. That is why this child depends on child 02 which depends on child 01, and why this plan must re-measure the footer rather than trusting the description above.
  THE TWO HOSTS' SENTENCES ARE NOT TWINS, AND E-04 MUST NOT MAKE THEM IDENTICAL. Measured at review: oc prints `No OpenCode session was captured for this run.` under a `--- OpenCode Session Continuity ---` header, while agy prints `No Antigravity session was captured for this run.`. The host NAME differs by design, so E-04's "both hosts changed identically" means the same STRUCTURE and the same two-case distinction, NOT the same literal string. An executor who copies oc's sentence into agy would put the wrong product name in agy's output.
- Scope: Print an end-of-run DISPOSITION SUMMARY that enumerates every matched artifact with per-disposition counts and, for each actionable disposition, the exact remedy command; print it even when zero artifacts were acted on; and stop the continuation footer from implying a turn was attempted when none was. EXCLUDES the per-artifact line itself (child 02 `m85gxh`, which owns the vocabulary this summary aggregates); excludes any new refusal kind or refusal RECORD type and the existing `render_stream` diagnostics allowlist (pending plan `r2i1b1`); excludes the `aw runs` `Issue` column and the `--json`/`--agent` payloads (also `r2i1b1`); excludes changing any disposition's MEANING (child 01 `zz5yxq`).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:m85gxh
- Status: executed
- Readiness: go-pending-approval
- Set: runnoop
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: bsc457
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history
- 2026-09-19 executed (aw oc run): aw oc run self-finalize: bsc457 verified (set runnoop, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/runner_shared.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-09 reviewed (aw set): /plan-review round 1 (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-310 all FIXED, both OQs resolved from evidence. Record: .aw/records/reviews/20260908-runnoop-03-bsc457-...review.md. THE BLOCKER RE-AIMS THE PLAN (PR-301): the Concern's claim that a zero-action run's ONLY closing output was the session sentence is FALSE. Rendering the real render_run_summary_table with one reviewed/zero-attempt item already prints a bordered table with a per-artifact row, a 'Progress: 1/1 100% (1 reviewed)' count line and a totals row, so E-01's authored deliverable ('a line per matched artifact and a per-disposition count line') was a description of the SHIPPED TABLE and an executor could pass V-01 by building a duplicate. Re-aimed onto the three things the table genuinely lacks: reason, remedy, honest zero-work verdict; V-01 now requires pasting the table's render beside the new block and naming the difference. PR-302 (HIGH): E-04 called the two hosts' sentences twins and demanded identical changes, but agy says 'No Antigravity session was captured' where oc says OpenCode, so a literal copy would put the wrong product name in agy's output. PR-303 (HIGH): E-05's enforcement claim is false (test_the_table_covers_both_runners checks only the table's aggregate; 4 of 46 rows are one-sided and pass), and it commanded an edit to tests/test_runner_refork_guard.py which was undeclared; path added, requirement moved onto its own mutation check. PR-304: status_summary_str is a LOCAL VARIABLE, not a reusable aggregation helper. PR-305: the baseline was wrong in both halves (bare run is 1 failed 5919 passed, and test_orchestrator_retirement is GREEN at 112 passed; the real failure is the environmental reporting-contract case). PR-306: all eight code anchors had drifted. PR-307/308: OQ-01 resolved end-only-and-self-contained from the maintainer's r2i1b1 OQ-01 four-place ruling, and OQ-02 resolved NO since its three-plan premise shrank to two (xtklpd is superseded). PR-309: the oc-to-agy import count is 48, not 47. PR-310: r2i1b1 is APPROVED with no dependencies, so it is the likely FIRST lander and its refusal record must be checked before E-02 authors remedy data. NOTE five of these ten defects were already found and fixed in sibling m85gxh's review and were not propagated here. Lint conforming at author and review-finalize; four decisions recorded, all reversible.

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50` fix (c), the GENERAL requirement; inherits the item's `- Blocks-Release: next`. This is the child that CLOSES `em0z50`, because it ships the last of the item's three fixes and the operator-visible capability the item describes is not delivered until the closing summary prints. Every claim measured at HEAD `44d4950d`. THREE MEASUREMENTS SHAPED THIS PLAN. FIRST, the aggregation substrate already exists: `status_summary_str` (`render_stream.py:1855`) builds count strings from `status_counts`, so this plan does not invent counting; it changes WHAT is counted (dispositions, not queue statuses), adds the remedy, and guarantees the print. SECOND, the misleading footer and the resume hint share one function and one `SUCCESS_STATES` read (`oc_runipd.py:7362` and `:7377`), which child 01 changes, so this plan MUST re-measure the footer at execution time instead of trusting an authoring-time description; E-04 says so explicitly. THIRD, the overlap fence with pending plan `r2i1b1` is narrow but real: that plan replaces the diagnostics allowlist inside `render_run_summary_table` and adds a refusal record with a REMEDY field. This plan's summary is a NEW closing block, not an edit to that allowlist, and if `r2i1b1` has landed it must SOURCE its remedies from that record rather than writing a second remedy table. E-06 requires that be checked from the plan's status on disk.
  ONE THING DELIBERATELY NOT CLAIMED: the backlog item asks that the summary be "the authoritative answer to what did this invocation actually do". This plan makes it the authoritative HUMAN answer. It does not make it machine-readable, because the `--json`/`--agent` payload surfaces belong to `r2i1b1`, whose E-03 must first extract the five duplicated `aw runs` issue-predicate copies. Stated here rather than left as an implied gap.

## Goal

Give every run a closing statement that names every matched artifact's disposition, counts them, and says what to do next, printed even when the run did nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the summary and its remedies

- [x] E-01 ADD ONE PURE SUMMARY RENDERER to `run_selection_policy.py`, taking the matched artifacts and their dispositions as plain data and returning the closing block: a line per matched artifact and a per-disposition count line. Pure means it returns lines, prints nothing, touches no filesystem, and imports no runner, exactly as `render_action_preview` (`:589`) and `render_refusal` (`:693`) already do there.
  DERIVE THE PER-ARTIFACT LINES FROM CHILD 02'S RENDERER, do not re-format them. Child 02 (`m85gxh`) put one line renderer in this same module for exactly this shape, and its plan forbids a second. Calling it is what makes CID-3 (one disposition vocabulary across the line and the summary) true by construction rather than by test.
  THE COUNTS MUST SUM TO THE NUMBER MATCHED, and that is the property worth asserting, not the individual numbers. The table's existing count line counts QUEUE STATUSES, a different denominator; do not reuse its input. Note there is nothing to reuse anyway: `status_summary_str` is a LOCAL VARIABLE inside `render_run_summary_table`, not a callable, so write your own counting.
  BUILD WHAT THE TABLE IS NOT. The table already prints a per-artifact row and a count line even for a zero-action run (F-8), so a block that merely re-lists the queue adds a third listing and fixes nothing. This summary's reason for existing is that it carries the REASON and the REMEDY beside each disposition and is honest when nothing was done.
  - Depends on: none
  - Expected outcome: one pure function returning the closing block; per-artifact lines produced by child 02's renderer rather than re-formatted; the counts sum to the number matched; an AST walk shows the module's first-party imports unchanged.
  - Execution state: performed

- [x] E-02 ADD THE REMEDY FOR EACH ACTIONABLE DISPOSITION, as data beside the disposition rather than a string at a call site, so a new disposition cannot be added without an author noticing its remedy is missing. The backlog item gives the shape verbatim for the measured case: `needs-approval (8): aw ipd set approved <id6> --by-human, or re-run with --full-auto`.
  THE REMEDY IS THE POINT, NOT DECORATION, and the reason is recorded in this repository's own history: `AGENTS.md` and pending plan `r2i1b1`'s OQ-01 both record that a message saying only "X is not allowed" gets complied with by DELETING the thing, when a correct non-destructive fix exists. A count without a remedy tells an operator they are stuck.
  VERIFY EVERY REMEDY COMMAND BY RUNNING ITS `--help`, not by writing what you remember. `aw ipd set approved <id6> --by-human` must be checked against the shipped CLI, and `--full-auto`'s effect must be stated accurately: it clears `reviewed -> auto-approved` (the automated tier), NOT to human `approved`, per executed plan `97df1z`. A remedy that does not work, or that overstates what it grants, is worse than none.
  MARK A DISPOSITION WITH NO REMEDY EXPLICITLY. Some dispositions are terminal and correct (`executed`), and printing a fabricated remedy for them would be noise. Distinguish "no remedy needed" from "remedy unknown" and never render the second as the first.
  - Depends on: E-01
  - Expected outcome: a remedy associated with each actionable disposition as data; every remedy command verified by running its `--help` and the output pasted; dispositions needing no remedy marked as such distinctly from unknown.
  - Execution state: performed

- [x] E-03 PRINT THE SUMMARY FROM BOTH HOSTS UNCONDITIONALLY, INCLUDING FOR A RUN THAT ACTED ON NOTHING. This is the item that fixes the measured incident: the zero-action case is precisely the one that printed nothing.
  FOLLOW THE ESTABLISHED UNCONDITIONAL-REPORTING PRECEDENT rather than inventing a rule: `announce_run_order` (`oc_runipd.py:4122`) prints the order whether or not anything was reordered, and its docstring gives the reason ("the order must be auditable in the log even when nothing was reordered"). The same argument applies at exit, more strongly.
  PLACE IT AT THE END AND MAKE IT SELF-CONTAINED. OQ-01 is RESOLVED at review, so this is no longer the executor's call: keep the existing start-side `announce_run_order` (which already satisfies the maintainer's start-side requirement unconditionally, and which cannot carry dispositions that do not exist yet), put the disposition summary at the END, and make the end block repeat its own counts and remedies so a `tail` reader needs nothing above it. See OQ-01 for the maintainer's four-place ruling and why (2) is already satisfied and (4) is out of this fence.
  DO NOT ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 48 names from `oc_runipd` (AST re-measured at review 2026-09-09, correcting the 47 authored here, the same off-by-one child 02's review recorded as PR-605) and zero flow back. Both hosts import from `run_selection_policy`. State the criterion as NOT INCREASING from the count you measure yourself, never from a number in this plan.
  - Depends on: E-02
  - Expected outcome: both hosts print the summary on every exit path including a zero-action run; it sits at the END and is self-contained per OQ-01; neither host gained an import from the other.
  - Execution state: performed

### Task group 2: stop the footer lying

- [x] E-04 RE-MEASURE `render_continuation_hint` AT EXECUTION TIME, THEN FIX THE FOOTER. The sentence `No OpenCode session was captured for this run.` (`oc_runipd.py:7362`, agy `:4568`) reads as a launch failure; it must instead say that no turn was ATTEMPTED when that is the truth, and keep its current meaning when a launch genuinely failed.
  RE-MEASURE FIRST, BECAUSE CHILD 01 MOVED THIS. The same function's `all_success` predicate reads `SUCCESS_STATES` (`:7377`, agy `:4583`), and child 01 (`zz5yxq`) changes what that decides for an execute item, so the footer's live behavior at your execution time is NOT what this plan describes at authoring time. Measure it, paste what you measured, and fix from that.
  DISTINGUISH THE TWO CASES RATHER THAN REWORDING ONE SENTENCE. "No session captured because no turn was attempted" and "no session captured although a turn was attempted" are different facts with different remedies, and collapsing them is the defect. The queue's attempt records are the evidence for which one holds.
  DO NOT CHANGE THE RESUME-HINT LOGIC. `all_success` also decides whether the footer offers `aw runs <id>` or `<cmd> resume ... <run-id>`, and that choice is child 01's to move. This item changes the SENTENCE, not the branch.
  - Depends on: E-03
  - Expected outcome: the measured pre-change footer behavior pasted; the two cases distinguished with different text; the resume-hint branch untouched; both hosts changed in the same STRUCTURE while each keeps its own product name (oc "OpenCode", agy "Antigravity").
  - Execution state: performed

### Task group 3: prove and fence

- [x] E-05 ADD THE REGRESSION TEST FOR THE MEASURED INCIDENT: a run matching N artifacts and acting on ZERO still prints the summary, its counts sum to N, and each actionable disposition carries its remedy. Assert on the ACTUAL rendered output, not on the data structure, because the defect was that nothing was PRINTED.
  ADD THE MUTATION CHECK, since a test asserting presence passes trivially. Suppress the unconditional print, show the test FAILS, restore, show it passes.
  PIN THE SHARING SYMMETRICALLY. Register every added symbol in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed.
  THAT TEST DOES NOT ENFORCE WHAT THIS ITEM CLAIMED, so the requirement must stand on its own mutation check rather than on the guard. Measured at review (the same correction child 02's review recorded as its PR-603/F-9): `test_the_table_covers_both_runners` asserts only that the table's AGGREGATE `runners` set equals BOTH and that more than one row names agy; it does NOT fail a one-sided ROW. 4 of the 46 shipped rows name a single runner (`StreamTracker`, `format_tokens`, `format_statusline`, `render_event`) and the suite passes. So a one-sided row for YOUR symbol would slip through, and "already fails a one-sided table" was false as a claim about enforcement while remaining correct as a requirement. Prove the symmetry with the mutation check below, not by citing that test.
  ALSO DECLARE THE FILE YOU ARE EDITING. `tests/test_runner_refork_guard.py` is NOT in this plan's `- Scope-Paths:` as authored, so this instruction commanded an out-of-fence edit; the path has been added at review (the identical defect was child 02's PR-604).
  - Depends on: E-04
  - Expected outcome: tests per host for the zero-action case, the counts-sum property, and remedy presence, asserting on rendered output; a mutation check demonstrating the test can fail; a symmetric `REFORK_TABLE` row whose symmetry is proven by the mutation check rather than by `test_the_table_covers_both_runners`, which does not enforce it.
  - Execution state: performed

- [x] E-06 RECONCILE WITH PENDING PLAN `r2i1b1` FROM ITS STATUS ON DISK, and record the answer. If it has EXECUTED, its refusal record carries reason AND remedy fields, and this summary must SOURCE remedies from that record rather than maintaining a second remedy table; also confirm its replacement of the diagnostics allowlist did not already add a closing block this plan would duplicate. If it has NOT executed, this plan's remedy data stands alone and must not define a refusal record type.
  EXPECT THE EXECUTED BRANCH, AND CHECK BEFORE AUTHORING E-02 RATHER THAN ONLY HERE. Measured at review 2026-09-09: `r2i1b1` is `- Status: approved` with `- Readiness: go-pending-approval`, both its open questions `resolved`, and `- Item-Dependencies: none`, so it is RUNNABLE NOW while this Set is not yet approved, making it the LIKELY first lander. Its declared `Scope-Paths` also include `render_stream.py`, `runner_shared.py` and both drivers, overlapping this child. So the sourcing question is not an end-of-run formality: READ ITS STATUS BEFORE E-02 writes any remedy data, because discovering the record after building a parallel remedy table means throwing that table away. Child 00's review recorded this same ordering correction for the Set. E-06 remains the item that RECORDS the answer, and this ordering note is why the check happens twice.
  DO NOT EDIT THE DIAGNOSTICS BLOCK UNDER EITHER BRANCH. `render_stream.render_run_summary_table`'s diagnostics block (`:2152`) is `r2i1b1`'s E-02 deliverable. This plan's summary is a separate closing block.
  - Depends on: E-05
  - Expected outcome: `r2i1b1`'s status read and pasted; the sourcing decision made and justified; no refusal record type defined here; the diagnostics block unedited.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_selection_policy.py` IS THE PURE-RENDERER HOME and states its own anti-duplication rule: `render_action_preview`'s docstring records that a second renderer was rejected because "the alignment rule, the type order, the action order, and the untyped-tail line would then exist twice and drift once". AST-verified purity: its only first-party imports are `selectors` and `status_set` (`:39-40`).
- UNCONDITIONAL REPORTING IS ALREADY THIS REPO'S CHOICE. `announce_run_order` prints the order even when nothing was reordered, for the stated reason that the log must be an audit trail rather than something to reconstruct from event timestamps.
- A REFUSAL MUST NAME THE CONSTRUCTIVE FIX. Recorded in `AGENTS.md` and in `r2i1b1`'s OQ-01 resolution: a message saying only that something is forbidden gets complied with by deletion. That is why E-02 makes the remedy a required field rather than an optional one.
- START-AND-END DUPLICATION IS AN ACCEPTED COST for critical closing information, per `r2i1b1`'s OQ-01 maintainer resolution, because readers pipe through `head` or `tail`.
- `--full-auto` CLEARS `reviewed -> auto-approved`, NOT to human `approved` (executed plan `97df1z`, and `oc_runipd.py:722` carries the exact provenance string "auto-approved by --full-auto: review readiness cleared (not human approval)"). Any remedy text mentioning it must not overstate what it grants.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 48 names from `oc_runipd` (AST re-measured at review; authored as 47); `oc_runipd` imports zero from agy.
- THE TWO HOSTS' SESSION SENTENCES DIFFER BY PRODUCT NAME BY DESIGN: oc says `No OpenCode session was captured for this run.` under `--- OpenCode Session Continuity ---`, agy says `No Antigravity session was captured for this run.`. "Change both hosts identically" means the same structure, not the same literal string.
- `r2i1b1` IS APPROVED AND RUNNABLE NOW (`- Item-Dependencies: none`, both OQs resolved), so it is likely to land BEFORE this Set. Its `Scope-Paths` overlap this child's drivers. Check for its refusal record BEFORE authoring remedy data, not only at E-06.
- EVERY LINE NUMBER IN THIS PLAN IS STALE. Re-measured at review, each authoring-time anchor had drifted: the session sentence `:7362` -> `:7575` (oc) and `:4568` -> `:4574` (agy), `all_success` `:7377` -> `:7589` / `:4583` -> `:4589`, `announce_run_order` `:4122` -> `:4178`, the provenance string `:722` -> `:731`, the COMPLETED tuple `:1872` -> `:1871-1877`, the diagnostics block `:2152` -> `:2153-2179`. Locate everything by symbol.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a lane worktree shows roughly 32 environmental failures.
- THE BASELINE FIGURE AND THE NAMED FAILURE WERE BOTH WRONG, re-measured at review 2026-09-09. A bare run on main is `1 failed, 5919 passed, 3 skipped, 2 xfailed`, not `1 failed, 5648 passed`; and `tests/test_orchestrator_retirement.py` is fully GREEN at `112 passed`, so the failure this plan named no longer exists. The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL rather than a defect: it enumerates files carrying the reporting-contract prose and trips on a gitignored, untracked local `opencode-recovery/` dump, so it will differ per machine. A WRONG-NAMED EXPECTED FAILURE IS WORSE THAN NONE, because an executor could excuse a real regression in the retirement suite as the known one. Measure your own and compare node ids.

## Findings

| Id | Severity | Location (re-measured at review 2026-09-09; LOCATE BY SYMBOL, every authoring-time line number below had drifted) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_continuation_hint`, both hosts (authored as `oc_runipd.py:7362` / `agy_runipd.py:4568`; actually `:7575` / `:4574`) | The session sentence describes a failed launch rather than an unattempted one. CORRECTED: it is NOT the "only" closing output (see F-8), and the two hosts print DIFFERENT product names. | source read at both hosts; backlog `em0z50`'s observed output |
| F-2 | HIGH | `render_run_summary_table`'s COMPLETED assignment and its `Diagnostics / Blocked Items:` block (authored as `render_stream.py:1872` / `:2152`; actually `:1871-1877` / `:2153-2179`) | The exit summary calls a zero-action run `COMPLETED` at 100% with no diagnostic, because `reviewed` is in the COMPLETED tuple and absent from the five-status diagnostics allowlist. RE-CONFIRMED by rendering the real function. | rendered `render_run_summary_table` with one `reviewed` item: `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)`, no diagnostics block |
| F-3 | MED | the `status_summary_str` LOCAL inside `render_run_summary_table` (authored as `render_stream.py:1855`) | A count line already exists but counts QUEUE STATUSES, carries no remedy, and renders inside the table. CORRECTED: it is a local variable, not a function, so there is nothing to import or reuse and E-01 writes its own counting. | grep finds exactly two occurrences (its assignment and its use in the `Progress:` line) and no definition |
| F-4 | MED | `render_continuation_hint` and its `all_success` read, both hosts (authored as `:7377` / `:4583`; actually `oc_runipd.py:7589`, `agy_runipd.py:4589`) | The misleading footer and the resume hint are in the SAME function and the branch reads `SUCCESS_STATES`, which child 01 changes. So the footer's behavior moves under this plan's feet and must be re-measured at execution time. | source read, both hosts |
| F-5 | MED | `announce_run_order` (authored as `oc_runipd.py:4122`; actually `:4178`) and `format_run_order_announcement` (`render_stream.py:1530`, correct as authored) | The unconditional-reporting precedent already exists at run START with its rationale in the docstring ("the order must be auditable in the log even when nothing was reordered"), so an unconditional closing summary is consistent rather than novel. | source read; docstring quoted verbatim |
| F-6 | MED | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md` | A pending plan owns the diagnostics allowlist, the refusal record (whose REMEDY field is a required one), and the five `aw runs` issue-predicate copies. Its OQ-01 records the maintainer's start-and-end duplication requirement. CORRECTED: it is now `- Status: approved` with `- Item-Dependencies: none`, so it is RUNNABLE NOW and likely to land FIRST (see F-9). | that plan's front matter read at review; both its OQs `resolved` |
| F-7 | LOW | the auto-approval provenance string (authored as `oc_runipd.py:722`; actually `:731`) | The provenance string already states that `--full-auto` is not human approval ("auto-approved by --full-auto: review readiness cleared (not human approval)"), so a remedy citing it has an exact wording to be consistent with. | source read |
| F-8 | HIGH | `render_run_summary_table` | **THE CONCERN'S "ITS ONLY CLOSING OUTPUT" IS FALSE, AND THE OVERSTATEMENT CHANGES WHAT E-01 MUST BUILD.** A zero-action run ALREADY prints a full bordered table with a per-artifact row and a count line, so the missing things are the REASON, the REMEDY and an honest verdict, not a listing. An executor holding the stronger belief could build a second queue table that satisfies every word of this plan and fixes nothing. This is the same correction child 02's review recorded as its F-8/PR-601, so the Set had it twice. | rendered the real function: row `01 / 01 / abc123 / wtiso / execute / reviewed`, `Progress: 1/1 ... (1 reviewed)`, totals row |
| F-9 | HIGH | `tests/test_runner_refork_guard.py`'s `test_the_table_covers_both_runners` | **E-05's ENFORCEMENT CLAIM IS FALSE.** That test asserts only that the table's AGGREGATE `runners` set equals BOTH and that more than one row names agy; it does NOT fail a one-sided ROW. Measured: 4 of 46 rows name a single runner (`StreamTracker`, `format_tokens`, `format_statusline`, `render_event`) and the suite passes. So the symmetry requirement must rest on V-05's mutation check. Child 02's review recorded the identical finding (its F-9/PR-603). | executed the table: 46 rows, 4 single-runner; the test body read |
| F-10 | MED | this plan's `- Scope-Paths:` as authored | E-05 mandated editing `tests/test_runner_refork_guard.py`, which was NOT declared, so the plan commanded an out-of-fence edit. Path added at review; child 02 had the same defect (its PR-604). | the authored `- Scope-Paths:` line versus E-05's instruction |

## Proposed changes (ordered, validatable)

1. E-01 adds ONE pure summary renderer to `run_selection_policy.py`, reusing child 02's per-artifact line renderer so the two vocabularies cannot diverge.
2. E-02 attaches a verified remedy to each actionable disposition as data, distinguishing "no remedy needed" from "remedy unknown".
3. E-03 prints it from both hosts unconditionally, including for a zero-action run, with the placement decision recorded.
4. E-04 re-measures and fixes the footer, distinguishing "no turn attempted" from "launch failed", without moving the resume branch.
5. E-05 tests the measured incident, mutation-checks the test, and registers a symmetric sharing guard.
6. E-06 reconciles with `r2i1b1` from its on-disk status.

## Deferred / out of scope (with reason)

- MACHINE-READABILITY of the summary (`--json`, `--agent`, the `aw runs` `Issue` column, the artifact-discrepancy summary): pending plan `r2i1b1`, whose E-03 must first extract the five duplicated issue-predicate copies. Adding a field here would extend one copy and make the surfaces disagree, which is the exact defect that plan records. So this child makes the summary the authoritative HUMAN answer, not yet the machine one.
- The `render_stream` diagnostics allowlist (`:2152`) and any refusal RECORD type: `r2i1b1`'s E-01/E-02.
- The `render_stream` COMPLETED tuple, which treats `reviewed` as a success. It is the renderer's copy of child 01's question. Excluded here because `r2i1b1`'s E-02 is editing that same function and because changing the table's verdict is a different claim from adding a closing summary; if the summary and the table's `Outcome:` visibly disagree after this plan, that is worth an item rather than a quiet edit inside this fence. OQ-02 resolves the ownership: `r2i1b1` owns the tuple, and the third plan once cited as converging on it (`xtklpd`) is superseded.
- The per-artifact line itself and its skip-reason vocabulary: child 02 (`m85gxh`), declared as this plan's `executed:` dependency.
- Changing what any disposition MEANS, or the run's exit code: child 01 (`zz5yxq`).
- Extending the discipline to `aw runs`, `aw ipd set`, and `aw find`, which the backlog item raises as a question. Each has its own selector semantics and tests; prove the driver shape first.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY to CALL the summary renderer and to change the footer SENTENCE. Do NOT change any gate, disposition value, exit code, or the resume-hint branch. Do NOT edit `render_stream.py` at all.
- Under-scope: stated rather than left as `none`. The summary is not machine-readable after this child, and the exit summary TABLE may still print `COMPLETED` for a zero-action run until child 01's renderer-side twin is addressed. Both are named above with their owners rather than left for a reader to discover.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured THERE and pasted, failing NODE IDS compared. `tests/test_run_selection_policy.py` is where the pure renderer's cases belong. `tests/test_run_summary_table.py` pins the existing diagnostics wording and belongs to `r2i1b1`; do not rewrite it, and if this plan's output makes one of its assertions ambiguous, report rather than edit. Note `tests/test_runner_shared.py::WrapperTests` counts per-runner call sites deliberately.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 already REQUIRES this summary's content, so this child moves the shipped code TOWARD the approved contract and does NOT amend it. Its exact requirement: "The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command." The `next command` element IS this plan's remedy, and `reason code` is child 02's skip reason. No spec file is declared in `- Scope-Paths:`.
CHECKED AT EXECUTION, ANSWERS RECORDED (the plan required these be checked rather than assumed).
FIRST, does §5.6's "the final TABLE" require the elements to live IN `render_run_summary_table`, which this plan deliberately does not edit? DETERMINATION: NO CONFLICT, and no maintainer escalation is warranted. The §5.6 sentence read verbatim at execution is "The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command." Of its ten elements the shipped table already renders position, ID6, type/Set, action, final item state and verification state; what it lacked was `reason code` (shipped by child 02 `m85gxh`) and `next command` (shipped here). The spec constrains the run's FINAL REPORT, and nothing in §5.6 makes the single bordered ASCII table the only admissible rendering of it; the closing block sits immediately beside that table in the same exit sequence, so an operator reads one final report. Reading it the other way would make the requirement unsatisfiable within any fence this Set could own, since `render_stream.py` belongs to `r2i1b1`. So this child moves the shipped code TOWARD the approved contract, as the paragraph above states, and amends no spec. If a future maintainer wants the elements physically inside the bordered table, that is a `render_stream` change owned by `r2i1b1`, and it is now recorded in backlog `b7oicl` alongside the COMPLETED-verdict defect in the same function.
SECOND, does the footer rewording change an operator-facing recovery string that §1.2 or §4.2 quotes verbatim? DETERMINATION: NO. The edited string is `No {product} session was captured for this run.`, which is PRESERVED unchanged for the launch-failed case; the new sentence is an ADDITIONAL branch for the never-dispatched case. Grepped at execution: neither `session was captured` nor `No turn was attempted` appears anywhere in the spec file, and §4.2's finding-code table is untouched (no spec file is in this plan's commits at all, so its byte-equality test against `run_evidence.RUN_FINDING_CODES` cannot be affected).

TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, §5.6 says "the final TABLE", and the shipped final table is `render_run_summary_table`, which this plan deliberately does not edit. Confirm whether the spec is satisfied by a separate closing block beside that table, or whether it requires the elements to live IN the table; if the latter, that is a conflict with the `r2i1b1` fence and must be reported to the maintainer rather than resolved by editing another plan's surface. SECOND, if the footer rewording changes an operator-facing recovery string that §1.2 or §4.2 quotes, the spec quotes it verbatim and the change must be reflected. Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the summary print at the END only, or at both the START and the END?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-09 from the maintainer's own recorded ruling, rather than deferred to the executor, because the repository already answers it and asking again would re-litigate a settled decision. KEEP THE EXISTING START-SIDE ANNOUNCEMENT, PUT THE DISPOSITION SUMMARY AT THE END, AND MAKE THE END BLOCK SELF-CONTAINED. The basis is `r2i1b1`'s OQ-01, resolved BY THE MAINTAINER 2026-09-07 and broadened there into an explicit four-place requirement: every refusal must state what went wrong AND the likely fix, appearing in (1) the end-of-run summary, "the one thing a human is guaranteed to read", (2) the START of output, (3) the END of output, because agents pipe through `head` or `tail`, and (4) the `aw runs` report plus the durable logs. Two facts decide how that applies HERE. FIRST, a START-side print cannot carry final dispositions, which do not exist yet, so the honest start-side artifact is the MATCHED list, and `announce_run_order` ALREADY prints it unconditionally with that rationale in its docstring; requirement (2) is therefore already satisfied by shipped code and needs nothing from this plan. SECOND, requirement (4) is explicitly OUT of this plan's scope (`aw runs` and the payloads belong to `r2i1b1`). What remains for this child is (1) and (3), which are the same physical block at the end of the run. So the end-only placement is not a weaker reading of the maintainer's rule: it is the whole of the rule that this fence owns. Self-contained means the block repeats the counts and remedies rather than referring upward to the table, so a `tail` reader needs nothing above it.

### OQ-02: Should the exit summary table's `Outcome:` be corrected in the same change, given it will read COMPLETED beside a summary saying nothing was done?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-09 as NO, do not edit it here; report the disagreement instead. The plan's own default was already correct and needed no maintainer round trip, and the coordination premise it rested on has SHRUNK, which is what let this be settled from evidence. Re-measured: the COMPLETED tuple containing `reviewed` is live in `render_run_summary_table`; `r2i1b1` is `- Status: approved` with `- Item-Dependencies: none`, so it IS editing that function and is runnable NOW, ahead of this Set; but the third converging plan this question named, `xtklpd`, is `- Status: superseded` under `.aw/records/plans/superseded/`, replaced by `ys1dor` (`integearn` Order 04, `reviewed`). So it is TWO plans converging on that expression, not three, and only ONE of them (`r2i1b1`) declares `render_stream.py`. That makes the ownership unambiguous rather than a judgement call: `r2i1b1` owns the tuple, this plan does not touch it, and reaching into `render_stream.py` would break this plan's own fence. IF the summary and the table's `Outcome:` visibly disagree after this child, report it as a finding naming `r2i1b1` as the owner; do not quietly reconcile them.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the summary renderer as written and the rendered block for a four-disposition mixed case. Paste proof the per-artifact lines came from child 02's renderer (show the CALL, not a similar string). Paste the counts and the number matched, showing they SUM. Paste an AST walk of `run_selection_policy.py` showing its first-party imports are still exactly `selectors` and `status_set`, and paste proof the function prints nothing (call it in a fresh interpreter with no repo present). ALSO paste the existing table's render for the same zero-action case beside your block, and state in one sentence what your block says that the table does not; if the answer is only "the same rows again", the item has built the duplicate F-8 warns about and that is a FAILED validation.
  - Observed evidence: the extracted shared judgement (not a duplicate listing), the mixed-case render, the table's render beside it with the one-sentence difference, the counts summing for both cases, the AST purity walk, and a print-nothing call from a repo-free directory. Detail below.
    THE DESIGN ANSWER TO F-8 FIRST, because it decides whether the rest of this item is even the right work. The plan's instruction "derive the per-artifact lines from child 02's renderer, do not re-format them" was followed in a STRONGER form than a call: the shared thing is the JUDGEMENT, not the string. `derive_item_disposition` was EXTRACTED out of `render_queue_dispositions` with its precedence byte-unchanged, and BOTH the line renderer and the new summary now call it. So the summary does not re-list the artifacts at all (that would have been the third listing F-8 warns about); it AGGREGATES the same per-artifact judgement the line already displays, which makes CID-3 true by construction. Proof the extraction changed no behavior: `tests/test_run_selection_policy.py` and `tests/test_oc_runipd.py` passed unmodified immediately after it (`303 passed in 7.28s`) before any new test existed.
    ```
    $ python3 -m pytest tests/test_run_selection_policy.py tests/test_oc_runipd.py
    303 passed in 7.28s
    ```
    WHAT THE BLOCK SAYS THAT THE TABLE DOES NOT, in one sentence as required: the table lists the queue and calls a zero-work run `COMPLETED` at `100%`, while this block states that NO WORK WAS PERFORMED and gives, per disposition, the REASON and the exact REMEDY command. Rendered side by side for the SAME one-item zero-action queue, the shipped table first (measured at execution, `Palette(False)`):
    ```
    ╭────────────────────────────────────────────────────────────────────────────╮
    │ AW RUN SUMMARY: run-XYZ (opencode)                                         │
    │ Outcome: COMPLETED   Duration: 0s   Spend: $0.00   Tokens: 0 ...           │
    │ Progress: 1/1  [██████████] 100% (1 reviewed)                              │
    ├─────┬─────┬────────┬───────┬─────────┬──────────┬────────┬────────...──────┤
    │ Run │ Pos │ ID6    │ Set   │ Action  │ Status   │ Verify │ Duration ...    │
    │  01 │  01 │ abc123 │ wtiso │ execute │ reviewed │ -      │        - ...    │
    │ Total (1/1 items run)                                    │       0s ...    │
    ╰────────────────────────────────────────────────────────────────────────────╯
    ```
    and THIS PLAN'S block for the measured 8-artifact incident:
    ```
    What this run did (every artifact its selector matched):
    NO WORK WAS PERFORMED: this run matched 8 artifact(s) and acted on NONE of them. This is not a failed launch; nothing was dispatched. See the remedies below.
      needs_human_approval (8): frozen awaiting human approval; reviewed but not approved, so it was never dispatched
        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. `--full-auto` instead clears a `reviewed` plan to `auto-approved` (an AUTOMATED clear, NOT human approval)
      total: 8 matched, 0 acted on, 8 not acted on
    ```
    THE FOUR-DISPOSITION MIXED CASE (six artifacts, five distinct dispositions plus an acted-on one), rendered:
    ```
    What this run did (every artifact its selector matched):
    This run matched 6 artifact(s) and acted on 1; 5 were not acted on.
      needs_human_approval (1): frozen awaiting human approval; reviewed but not approved, so it was never dispatched
        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. ...
      dependency_not_met (1): a declared dependency was not satisfied in this run
        remedy: run the dependency to its declared state first, or include it in the same selector so this run can satisfy the edge
      ipd_already_executed (1): already executed on disk, so there was nothing to do
      type_or_status_not_runnable (1): its status is not runnable, so no session was appropriate
        remedy: check the artifact's `- Status:` with `aw find plans <id6>`: a terminal status (`superseded`, `not-executed`) is correctly skipped, while a MISSING status is a defect in the artifact worth fixing
      integration-blocked (1)
        remedy: re-attempt with `aw oc run integrate <run-id>`
      acted_on (1): acted on by this run
      total: 6 matched, 1 acted on, 5 not acted on
    ```
    THE SHARED-JUDGEMENT CALL, shown as the CALL rather than as a similar string. `render_queue_dispositions` (the `m85gxh` renderer) and `summarize_dispositions` (this plan's counter) both contain the line `decided = derive_item_disposition(entry, refusal_reader)` / `decided = derive_item_disposition(entry, refusal_reader)`, and the line renderer still formats via `render_item_disposition(...)`, untouched. The same six-item queue rendered through the LINE renderer, showing the identical vocabulary the counts grouped by:
    ```
    Per-artifact disposition (every artifact this selector matched):
    - 01 aaa111 [wtiso] execute -> reviewed: needs_human_approval (frozen awaiting human approval; ...)
    - 02 bbb222 [wtiso] execute -> executed: ipd_already_executed (already executed on disk, ...)
    - 03 ccc333 [wtiso] execute -> not-attempted: type_or_status_not_runnable (its status is not runnable, ...)
    - 04 ddd444 [wtiso] execute -> dependency-blocked: dependency_not_met (...; unmet: executed:aaa111 (target reviewed))
    - 05 eee555 [wtiso] execute -> integration-blocked: the lane finalized but could not be merged into main
    - 06 fff666 [wtiso] execute -> executed: acted on by this run
    ```
    THE COUNTS SUM, which is the property asserted rather than any individual number:
    ```
    zero-action: entries=8  sum(counts)=8  equal=True  buckets=[('needs_human_approval', 8)]
    mixed:       entries=6  sum(counts)=6  equal=True  buckets=[('needs_human_approval', 1), ('dependency_not_met', 1), ('ipd_already_executed', 1), ('type_or_status_not_runnable', 1), ('integration-blocked', 1), ('acted_on', 1)]
    ```
    Pinned by `test_the_counts_sum_to_the_number_matched_for_a_mixed_queue` and asserted on the RENDERED text (not the data) by `test_the_printed_counts_sum_to_the_number_of_matched_artifacts`, which parses the counts back out of stdout with a regex.
    PURITY, by AST and by execution. First-party imports UNCHANGED:
    ```
    === V-01: run_selection_policy.py first-party imports (AST walk) ===
    first-party imports: ['selectors', 'status_set']
    unchanged (exactly selectors + status_set): True
    ```
    And the renderer prints nothing, called with the interpreter chdir-ed into an empty directory containing no repo:
    ```
    === V-01 PURITY: interpreter chdir-ed into an empty dir before the call ===
    cwd during call: <lane>/.aw/tmp-bsc457/nowhere
    .git here: False | .aw here: False
    stdout captured DURING the call: ''
    returned 5 lines; printed nothing: True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the remedy data as written. For EVERY remedy command, paste the ACTUAL output of running its `--help`, proving the command and its flags exist as written. Paste one rendered summary showing a remedy beside its count, in the shape the backlog item specifies. Paste one disposition marked as needing no remedy and one that would be marked unknown, showing they render DIFFERENTLY.
  - Observed evidence: the remedy data as data, the ACTUAL `--help` output for all four remedy commands, a remedy rendered beside its count, and the needs-none versus unknown cases rendering differently. Detail below.
    THE REMEDY IS DATA BESIDE THE DISPOSITION, in `DISPOSITION_REMEDIES` (a `Mapping[str, str]` keyed by disposition code) with `DISPOSITIONS_NEEDING_NO_REMEDY` (a `frozenset`) and `REMEDY_UNKNOWN_TEXT` beside it, resolved by `remedy_for_disposition`. `test_every_closed_skip_reason_resolves_to_a_remedy_or_an_explicit_no_remedy` is what makes "a new disposition cannot be added without an author noticing its remedy is missing" enforced rather than hoped: it iterates `SKIP_REASONS` and fails if any member has neither a remedy nor an explicit needs-none marker.
    EVERY REMEDY COMMAND VERIFIED BY RUNNING ITS `--help`. First, `aw ipd set approved <id6> --by-human`:
    ```
    $ python3 -m agent_workflows ipd set --help
    usage: agent-workflows ipd set [-h] ... [--by-human] [--allow-open-questions]
                                   [--actor ACTOR] ... args [args ...]
    Transition the lifecycle status of one or more plan/IPD artifacts or plan
    sets. ... Syntax: 'aw ipd set <status> <id6|setid|fname>...'.
    positional arguments:
      args                  <status> <selector...>
      --message, -m MESSAGE  History record message.
    ```
    so `--by-human`, `--message` and the `<status> <selector...>` positional shape all exist as written. Second, `--full-auto`, whose EFFECT had to be stated accurately:
    ```
    $ python3 -m agent_workflows oc run start --help
      --full-auto, --no-full-auto
                            Clear a plan that is already 'Status: reviewed' to
                            'auto-approved' and execute it immediately. ... This records an
                            AUTOMATED clear, NOT human approval: no --by-human
                            attestation is asserted. Implies --unattended
    ```
    The shipped help says "an AUTOMATED clear, NOT human approval" verbatim, so the remedy text says `(an AUTOMATED clear, NOT human approval)` and does NOT claim it grants human approval; `test_each_actionable_disposition_prints_its_remedy` asserts the string `NOT human approval` is present, which is the overstatement guard. Third and fourth:
    ```
    $ python3 -m agent_workflows host capabilities --help
    usage: agent-workflows host capabilities [-h] [--no-color] [--agent] [--json] [host]
    Print the host capability contract and the per-action verdicts derived from it: ...
    $ python3 -m agent_workflows find plans --help
    usage: agent-workflows find [-h] ... [type] [selector ...]
    Find artifacts of a given TYPE by selector (id6, status, Set, filename fragment) ...
    ```
    A REMEDY BESIDE ITS COUNT, in the shape the backlog item specifies (`needs-approval (8): aw ipd set approved <id6> --by-human, or re-run with --full-auto`); the shipped render of the measured case:
    ```
      needs_human_approval (8): frozen awaiting human approval; reviewed but not approved, so it was never dispatched
        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. `--full-auto` instead clears a `reviewed` plan to `auto-approved` (an AUTOMATED clear, NOT human approval)
    ```
    "NO REMEDY NEEDED" AND "REMEDY UNKNOWN" RENDER DIFFERENTLY, which is the distinction E-02 forbids collapsing. `ipd_already_executed` is terminal and correct, so it carries NO `remedy:` line at all:
    ```
      ipd_already_executed (1): already executed on disk, so there was nothing to do
      (no remedy: line follows)
    ```
    while an UNRECOGNIZED disposition prints an explicit admission of the gap rather than silence:
    ```
      a_brand_new_refusal_code (1)
        remedy: no remedy is recorded for this disposition; this is a gap in the runner's remedy table, please report it
    ```
    Both pinned on the RENDERED block by `test_the_unknown_and_the_no_remedy_cases_render_differently` and `test_a_terminal_disposition_prints_no_fabricated_remedy` (the latter asserts `remedy:` and `REMEDY_UNKNOWN_TEXT` are both ABSENT for `executed`), plus `test_every_actionable_disposition_carries_a_remedy_and_terminal_ones_do_not` on the resolver's three outcomes.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the ACTUAL stdout of a run that acted on ZERO artifacts, showing the full summary. Paste the same for a mixed run. Paste the placement decision (OQ-01's answer) and the reason. Paste the AST-measured oc-to-agy import count BEFORE and AFTER, showing it did not increase from the count you measured yourself (48 at review; measure your own rather than asserting either number). Both hosts, and for agy show its own product name in the header rather than oc's.
  - Observed evidence: ACTUAL `run_queue` stdout for a zero-action and a mixed run on BOTH hosts, agy naming Antigravity, the OQ-01 placement decision with its reason, and an AST import count of 53 before and 53 after. Detail below.
    ACTUAL STDOUT FROM THE REAL `run_queue`, both hosts, driven over a queue whose launcher raises if called (so "nothing was dispatched" is proven positively). ZERO-ACTION, 8 matched, 0 acted on:
    ```
    ### oc :: ZERO-ACTION (8 matched, 0 acted on) -- ACTUAL stdout, closing portion
    What this run did (every artifact its selector matched):
    NO WORK WAS PERFORMED: this run matched 8 artifact(s) and acted on NONE of them. This is not a failed launch; nothing was dispatched. See the remedies below.
      needs_human_approval (8): frozen awaiting human approval; reviewed but not approved, so it was never dispatched
        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. `--full-auto` instead clears a `reviewed` plan to `auto-approved` (an AUTOMATED clear, NOT human approval)
      total: 8 matched, 0 acted on, 8 not acted on

    --- OpenCode Session Continuity ---
    No turn was attempted, so no OpenCode session exists for this run. This is NOT a failed launch: the runner dispatched nothing. See the disposition summary above for what it matched and what to do about each item.
    To resume this run:
      aw oc run resume --repo <tmp> run-test
    ```
    ```
    ### agy :: ZERO-ACTION (8 matched, 0 acted on) -- ACTUAL stdout, closing portion
    What this run did (every artifact its selector matched):
    NO WORK WAS PERFORMED: this run matched 8 artifact(s) and acted on NONE of them. ...
      needs_human_approval (8): frozen awaiting human approval; reviewed but not approved, so it was never dispatched
        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, then re-run. ...
      total: 8 matched, 0 acted on, 8 not acted on

    --- Antigravity Session Continuity ---
    No turn was attempted, so no Antigravity session exists for this run. This is NOT a failed launch: the runner dispatched nothing. ...
    To resume this run:
      aw agy run resume --repo <tmp> run-test
    ```
    AGY NAMES ITSELF, not oc: the header reads `--- Antigravity Session Continuity ---` and the sentence says `no Antigravity session exists`, pinned by `test_this_hosts_footer_names_ANTIGRAVITY_and_not_opencode`, which also asserts `no OpenCode session exists` is ABSENT. MIXED RUN, both hosts (4 matched, 1 acted on):
    ```
    ### oc :: MIXED -- ACTUAL stdout, closing portion
    What this run did (every artifact its selector matched):
    This run matched 4 artifact(s) and acted on 1; 3 were not acted on.
      needs_human_approval (1): ...        remedy: approve it with `aw ipd set approved <id6> --by-human --message ...`, ...
      ipd_already_executed (1): already executed on disk, so there was nothing to do
      type_or_status_not_runnable (1): ... remedy: check the artifact's `- Status:` with `aw find plans <id6>`: ...
      acted_on (1): acted on by this run
      total: 4 matched, 1 acted on, 3 not acted on
    ```
    (the agy MIXED render is byte-identical in the summary block, differing only in its own `--- Antigravity Session Continuity ---` footer, as measured).
    PLACEMENT (OQ-01's answer) AND THE REASON: END-ONLY AND SELF-CONTAINED. The existing start-side `announce_run_order` is kept and untouched, because a start-side print cannot carry dispositions that do not exist yet, and it already satisfies the maintainer's requirement (2) unconditionally with that rationale in its own docstring. The end block repeats its own counts and remedies rather than referring upward to the table, so a `tail` reader needs nothing above it; the `total:` line exists precisely so the block's guarantee is checkable on its face. Within the exit sequence it is placed BEFORE the continuation footer, because the footer is session-continuity plumbing and the answer to "what did this run do?" must not sit beneath it.
    THE IMPORT DIRECTION DID NOT DEEPEN, measured by my own AST walk rather than asserted from the plan (which said 48; this worktree measures 53, the drift the plan's own note predicted):
    ```
    === V-03: oc_runipd -> agy_runipd import direction, by AST ===
    agy_runipd imports from oc_runipd: 53 names
    oc_runipd imports from agy_runipd: 0 names
    render_disposition_summary among them: False
    BEFORE (HEAD): 53 names   AFTER: 53 names   increased: False
    ```
    Both hosts import `render_disposition_summary` from `run_selection_policy` DIRECTLY, and `test_both_hosts_render_the_summary_from_the_same_object` asserts both bindings are the same object by identity.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the PRE-CHANGE footer behavior as MEASURED in the executing worktree, not as described in this plan, since child 01 moved it. Then paste the two post-change forms side by side: the no-turn-attempted case and the launch-failed case, showing they differ. Paste proof the resume-hint BRANCH is unchanged (a diff of that expression, or the assertion that covers it). Both hosts, and show agy's output naming Antigravity rather than OpenCode; an agy footer carrying oc's product name is a FAILED validation.
  - Observed evidence: the PRE-CHANGE footer measured here (identical sentence for both cases), the discovery that the body is now ONE shared definition rather than two per-host copies, the two post-change forms side by side on both hosts, the fail-closed correction a shipped test forced, and proof the resume-hint branch is untouched. Detail below.
    PRE-CHANGE, MEASURED IN THIS WORKTREE BEFORE ANY EDIT (and the measurement immediately found the plan's description stale in a way that mattered, see the note below). The SAME sentence for both the zero-action and the turn-attempted case, which is the defect:
    ```
    === PRE-CHANGE: oc render_continuation_hint, zero-action (reviewed/needs_input) ===
    --- OpenCode Session Continuity ---
    No OpenCode session was captured for this run.
    To resume this run:
      aw oc run resume --repo /repo run-XYZ

    === PRE-CHANGE: oc footer when a turn WAS attempted but no session captured ===
    --- OpenCode Session Continuity ---
    No OpenCode session was captured for this run.
    To resume this run:
      aw oc run resume --repo /repo run-XYZ

    === PRE-CHANGE: agy render_continuation_hint, same state ===
    --- Antigravity Session Continuity ---
    No Antigravity session was captured for this run.
    ```
    THE PLAN'S LOCATION FOR THIS CODE WAS STALE IN KIND, NOT ONLY IN LINE NUMBER, which is the finding of this item. The plan (and its review) describe TWO per-host copies at `oc_runipd.py` and `agy_runipd.py`. Measured: the body has been CONSOLIDATED into ONE shared definition, `runner_shared.render_continuation_hint`, which each host wraps in a one-line call supplying its own `HostLabels`; `tests/test_rununify_main.py` records the move ("`render_continuation_hint` and `write_report` became one-line per-host wrappers"). So "change both hosts in the same STRUCTURE while each keeps its own product name" is satisfied by editing the shared body ONCE, with `labels.product` supplying the name; a per-host edit would have RE-FORKED the string the consolidation existed to unify. This is the out-of-fence path declared in the commit message and in the scope reconciliation.
    POST-CHANGE, THE TWO CASES SIDE BY SIDE, both hosts:
    ```
    ### oc: CASE A - NO TURN ATTEMPTED            ### oc: CASE B - A TURN WAS ATTEMPTED
    --- OpenCode Session Continuity ---           --- OpenCode Session Continuity ---
    No turn was attempted, so no OpenCode         No OpenCode session was captured for
    session exists for this run. This is NOT      this run.
    a failed launch: the runner dispatched
    nothing. See the disposition summary
    above for what it matched and what to
    do about each item.
    To resume this run:                           To resume this run:
      aw oc run resume --repo /repo run-XYZ         aw oc run resume --repo /repo run-XYZ
    ```
    ```
    ### agy: CASE A - NO TURN ATTEMPTED           ### agy: CASE B - A TURN WAS ATTEMPTED
    --- Antigravity Session Continuity ---        --- Antigravity Session Continuity ---
    No turn was attempted, so no Antigravity      No Antigravity session was captured
    session exists for this run. This is NOT      for this run.
    a failed launch: ...
    ```
    ```
    oc case A != oc case B : True
    oc case A mentions 'No turn was attempted': True
    oc case B keeps 'was captured for this run': True
    agy names Antigravity: True | agy leaks 'OpenCode': False
    oc names OpenCode: True | oc leaks 'Antigravity': False
    ```
    THE PREDICATE FAILS CLOSED, AND THE FIRST VERSION DID NOT, which is worth recording because a shipped test caught it rather than a reviewer. Reading `attempts` alone called a bare `[{"status": "failed"}]` unattempted (that shipped fixture, `test_no_sessions_captured_incomplete`, carries no `attempts` key at all), so the new sentence was printed about a run that plainly ran:
    ```
    FAILED tests/test_oc_runipd.py::ContinuationHintTests::test_no_sessions_captured_incomplete
    AssertionError: 'No OpenCode session was captured' not found in '... No turn was attempted, so no OpenCode session exists ...'
    ```
    Fixed with `DISPATCH_PROVING_STATUSES` plus an empty/malformed-queue guard, on the asymmetry that asserting "nothing was attempted" falsely is an affirmative false statement while the older sentence merely adds no information. Pinned by `test_the_no_turn_claim_FAILS_CLOSED_rather_than_guessing` over five dispatch-proving statuses, a recorded attempt, an empty queue, a malformed entry and a mixed queue.
    THE RESUME-HINT BRANCH IS UNCHANGED. `git diff` of `render_continuation_hint` shows the `all_success` expression untouched (`all_success = all(item_reached_success(item) for item in queue)`) and the added code is entirely inside the `if not captured:` arm. Behaviorally:
    ```
    zero-action(reviewed/execute)    resume-hint=True  inspect-hint=False
    attempted(failed-safely)         resume-hint=True  inspect-hint=False
    all-success(executed)            resume-hint=False inspect-hint=True
    ```
    and the shipped assertions that cover the branch all pass unmodified: `test_a_reviewed_but_unapproved_execute_item_offers_RESUME_not_inspect`, `test_no_sessions_captured_success`, `test_no_sessions_captured_incomplete`, `test_single_session_incomplete` (`tests/test_oc_runipd.py -k ContinuationHint`: `9 passed`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the tests and their actual runner output. Paste the MUTATION CHECK in full: suppress the unconditional print, paste the FAILING output, restore, paste the passing output. Paste the new `REFORK_TABLE` row showing BOTH runners, and `tests/test_runner_refork_guard.py` passing. A passing `test_the_table_covers_both_runners` is NOT evidence of row symmetry (it does not fail a one-sided row; 4 of 46 shipped rows are one-sided and pass), so paste a SECOND mutation check that drops one runner from your row and shows what does or does not catch it; if nothing catches it, say so plainly rather than citing the aggregate test.
  - Observed evidence: the tests and `415 passed`, mutation check 1 (print suppressed -> 5 failures across both hosts, then restored green), the symmetric `REFORK_TABLE` row, and mutation check 2 in two parts showing the aggregate test does NOT catch a one-sided row while the per-row identity assertion DOES. Detail below.
    THE TESTS, asserting on RENDERED OUTPUT because the defect was that nothing was PRINTED. Per host: `EndOfRunDispositionSummaryTests` (oc, 6 tests) covering the zero-action case, the counts-sum property parsed back out of stdout with a regex, remedy presence, a terminal disposition printing no fabricated remedy, the footer fix, and the no-driver-copy rule; `AgyEndOfRunDispositionSummaryTests` (agy, 4 tests, INHERITING the oc harness so the two halves cannot drift) covering the zero-action case, the Antigravity product name, shared-object identity, and the no-copy rule; plus 11 pure-module tests in `tests/test_run_selection_policy.py`. Actual output:
    ```
    $ python3 -m pytest tests/test_run_selection_policy.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_runner_refork_guard.py
    415 passed in 10.61s
    ```
    MUTATION CHECK 1, the unconditional print suppressed in BOTH hosts (wrapped in `if False:`). It FAILS, and it fails in both hosts, which is what proves the tests are about the PRINT and not about the data structure:
    ```
    === MUTATION 1: summary print suppressed -> tests MUST fail ===
    E       ValueError: substring not found     <- out.index(pol.SUMMARY_HEADER)
    FAILED tests/test_agy_runipd_cli.py::AgyEndOfRunDispositionSummaryTests::test_a_run_that_acted_on_ZERO_artifacts_still_prints_the_summary
    FAILED tests/test_oc_runipd.py::EndOfRunDispositionSummaryTests::test_a_run_that_acted_on_ZERO_artifacts_still_prints_the_summary
    FAILED tests/test_oc_runipd.py::EndOfRunDispositionSummaryTests::test_each_actionable_disposition_prints_its_remedy
    FAILED tests/test_oc_runipd.py::EndOfRunDispositionSummaryTests::test_a_terminal_disposition_prints_no_fabricated_remedy
    FAILED tests/test_oc_runipd.py::EndOfRunDispositionSummaryTests::test_the_printed_counts_sum_to_the_number_of_matched_artifacts
    5 failed, 8 passed in 2.60s
    ```
    RESTORED, and green again:
    ```
    === RESTORED -> tests pass ===
    13 passed in 2.52s
    ```
    THE NEW `REFORK_TABLE` ROW, naming BOTH runners: `Owned("render_disposition_summary", "run_selection_policy", BOTH),` with a comment recording what it buys (the operator-facing REMEDY text must be ONE object) and what does NOT enforce it. Passing:
    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py
    9 passed in 5.34s
    ```
    MUTATION CHECK 2, IN TWO PARTS, because the plan required showing what does and does not catch asymmetry. PART A re-confirms F-9 by making my own row one-sided (`("oc_runipd",)` instead of `BOTH`); NOTHING CATCHES IT, stated plainly as the plan demands:
    ```
    === MUTATION 2a: my row made ONE-SIDED (oc only) ===
    9 passed in 5.44s
    ```
    So `test_the_table_covers_both_runners` does not fail a one-sided row, exactly as F-9 measured, and citing it as evidence of symmetry would have been false. PART B shows what DOES bite: with the row restored to `BOTH`, removing agy's actual BINDING (renaming its import to `_mutation_renamed_summary` while keeping the call site working, so ONLY the symmetry breaks) fails the per-row identity assertion:
    ```
    === MUTATION 2b: agy stops binding the shared symbol -> the SYMMETRIC row must bite ===
    FAILED tests/test_runner_refork_guard.py::SymmetricReForkGuardTests::test_every_runner_attribute_is_the_owning_modules_object
    AssertionError: 'agy_runipd.render_disposition_summary is MISSING; it must stay reachable
                     (re-export `run_selection_policy.render_disposition_summary`)' != []
    1 failed, 8 passed in 5.78s
    ```
    So the symmetry requirement rests on `test_every_runner_attribute_is_the_owning_modules_object` plus the AST half, NOT on the aggregate test; both mutations were reverted and the guard is green.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `r2i1b1`'s `- Status:` line and its directory, read at validation time. State which branch applied and what was done. Paste proof the `render_stream` diagnostics block is UNEDITED (a diff of `render_stream.py` showing no change, or the file absent from this plan's commits). If `r2i1b1` executed, paste the code sourcing remedies from its record. THEN close backlog `em0z50`: paste its `- Status:` line showing `done`, and paste `aw backlog check` clean. `em0z50` carries `- Blocks-Release: next`, so its close is gated on the handoff, which this plan's `- From-Backlog: em0z50` plus matching `- Blocks-Release: next` satisfies; paste the setter's actual output rather than hand-editing the item.
  - Observed evidence: `r2i1b1` read as `- Status: executed` under `plans/executed/`, the executed branch applied with the code sourcing the record's own remedy, `render_stream.py` absent from this plan's commits entirely, OQ-02's disagreement reported as backlog `b7oicl`, and `em0z50` closed through the setter with `aw backlog check` clean. Detail below.
    `r2i1b1` READ AT EXECUTION TIME, BEFORE E-02 WROTE ANY REMEDY DATA (the plan required the check happen then, not only here, precisely so a parallel remedy table would not be built and thrown away):
    ```
    $ ls -d .aw/records/plans/*/20260907-orchprobe-01-r2i1b1*
    .aw/records/plans/executed/20260907-orchprobe-01-r2i1b1-surface-a-per-item-refusal-reason-and-its-remedy-in-the-run.ipd.md
    $ grep -n "^- Status:" <that file>
    10:- Status: executed
    ```
    THE EXECUTED BRANCH APPLIED, which is the branch the plan expected. What was done: this plan defines NO refusal record type and maintains NO second remedy for an item that carries a refusal. `derive_item_disposition` SOURCES the record's own `code` and `remedy` through that plan's shipped ONE reader (`refusal_of_item`, injected as `refusal_reader`, never by indexing the key), and `summarize_dispositions` prefers `decided.remedy` over its own table:
    ```
    code = getattr(refusal, "code", None)
    remedy = getattr(refusal, "remedy", None)
    return ItemDisposition(
        str(code).strip() if isinstance(code, str) and code.strip() else "refused",
        refusal_reason,
        str(remedy).strip() if isinstance(remedy, str) and remedy.strip() else None,
    )
    ...
    remedies[code] = decided.remedy or remedy_for_disposition(code)
    ```
    Rendered, a refused item shows the RECORD'S remedy, and `integration-blocked` is deliberately absent from this plan's `DISPOSITION_REMEDIES` (asserted by `test_a_recorded_refusals_own_remedy_is_sourced_not_duplicated`):
    ```
      integration-blocked (1)
        remedy: re-attempt with `aw oc run integrate <run-id>`
    ```
    Duck-typed rather than imported, for the same reason `reason_from_refusal` already is: importing `render_stream` would break the two-import purity V-01 asserts.
    THE DIAGNOSTICS BLOCK IS UNEDITED, proven by `render_stream.py` being ABSENT from this plan's commits entirely:
    ```
    $ git show --stat 80b5dc8f
     agent_workflows/agy_runipd.py           |  21 ++
     agent_workflows/oc_runipd.py            |  33 +++
     agent_workflows/run_selection_policy.py | 472 ++++++++++++++++++++----
     agent_workflows/runner_shared.py        |  99 ++++++-
     tests/test_agy_runipd_cli.py            |  81 ++++++
     tests/test_oc_runipd.py                 | 204 ++++++++++++++
     tests/test_run_selection_policy.py      | 161 +++++++++++
     tests/test_runner_refork_guard.py       |  22 ++
    ```
    No `render_stream.py`, so neither its diagnostics block nor its COMPLETED tuple was touched. OQ-02'S CONTINGENCY DID FIRE and was honored: the summary and the table DO visibly disagree (the table renders `Outcome: COMPLETED` at `100%` beside a block reading `NO WORK WAS PERFORMED`), so per OQ-02 it is REPORTED as a finding naming `r2i1b1` as the owner rather than quietly reconciled. Filed as backlog `b7oicl`.
    BACKLOG `em0z50` CLOSED THROUGH THE SETTER, not by hand:
    ```
    $ python3 -m agent_workflows backlog set done 20260829-runnoop-01-em0z50-...backlog.md --message "..."
    - >  backlog     20260829-runnoop-01-em0z50  [high]  [blocking]  graduated → done
    $ grep -n "^- Status:" .aw/records/backlog/*/*em0z50*
    2:- Status: done
    $ python3 -m agent_workflows backlog check
    aw backlog check: all backlog items conform.
    ```
    The setter ACCEPTED the close for a `[blocking]` item, which is the gate being satisfied rather than bypassed: this plan carries `- From-Backlog: em0z50` and the same `- Blocks-Release: next`, which is the HANDOFF fix the close-legitimacy predicate requires.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT edit `render_stream.py` at all, including its COMPLETED tuple and its diagnostics block. Do NOT define a refusal record type. Do NOT change any gate, disposition value, exit code, or the resume-hint branch. Do NOT add a first-party import to `run_selection_policy.py` beyond the two it has. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT rewrite `tests/test_run_summary_table.py`. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and child 01 of this Set edits the very function E-04 changes. Find `render_continuation_hint`, `announce_run_order`, `render_run_summary_table`, `render_action_preview`, and `deliberate_stop_exit_code` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved bsc457 --by-human --message ...`) before execution, and child 02 (`m85gxh`) must read `executed` first, which the declared `- Item-Dependencies: executed:m85gxh` enforces. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION OF THIS PLAN, close backlog `em0z50`, which all three children of this Set carry as `- From-Backlog:` and whose `- Blocks-Release: next` gate they inherit. It closes HERE and not on a sibling, because the operator-visible capability it describes is the closing summary, which ships here.

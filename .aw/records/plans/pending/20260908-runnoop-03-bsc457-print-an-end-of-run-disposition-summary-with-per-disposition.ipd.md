# IPD: Print an end-of-run disposition summary with per-disposition counts and the exact remedy command

- Date: 2026-09-08
- Kind: child
- Concern: There is no authoritative closing answer to "what did this invocation actually do?", and the one thing that IS printed at exit reads as a failure when nothing was attempted. MEASURED 2026-08-29 (backlog `em0z50`): `aw oc run wtiso` matched 8 plans, acted on none, and its ONLY closing output was `No OpenCode session was captured for this run.` (`oc_runipd.py:7362`, agy twin `:4568`). That sentence describes a launch that failed. Nothing launched, and nothing said so.
  THE SUMMARY TABLE THAT DOES EXIST AGREES WITH THE WRONG ANSWER. Re-measured at HEAD `44d4950d` by rendering `render_run_summary_table` with one `reviewed` item: `Outcome: COMPLETED`, `Progress: 1/1 [##########] 100% (1 reviewed)`, and NO diagnostic line. The COMPLETED verdict comes from a status tuple containing `reviewed` (`render_stream.py:1872`) and the silence comes from the diagnostics block keying on a five-status allowlist that `reviewed` is not a member of (`:2152`). A green 100% for zero work performed, with a launch-failure sentence underneath it.
  A COUNT LINE EXISTS BUT IS NOT A DISPOSITION SUMMARY. `status_summary_str` (`render_stream.py:1855`) already builds `"1 reviewed"`-style counts from `status_counts`, so the aggregation substrate is present. What is missing is that it counts QUEUE STATUSES rather than dispositions, it carries no remedy, it is rendered inside the table rather than as the authoritative closing statement, and it is not guaranteed to appear for a run that did nothing.
  THE `all_success` COUPLING IS THE TRAP AN EXECUTOR WILL HIT. The misleading footer and the resume hint come from the SAME function, `render_continuation_hint`, whose `all_success` predicate reads `SUCCESS_STATES` (`oc_runipd.py:7377`, agy `:4583`). Child 01 (`zz5yxq`) changes what that constant decides for an execute item, so the footer's behavior MOVES when child 01 lands. That is why this child depends on child 02 which depends on child 01, and why this plan must re-measure the footer rather than trusting the description above.
- Scope: Print an end-of-run DISPOSITION SUMMARY that enumerates every matched artifact with per-disposition counts and, for each actionable disposition, the exact remedy command; print it even when zero artifacts were acted on; and stop the continuation footer from implying a turn was attempted when none was. EXCLUDES the per-artifact line itself (child 02 `m85gxh`, which owns the vocabulary this summary aggregates); excludes any new refusal kind or refusal RECORD type and the existing `render_stream` diagnostics allowlist (pending plan `r2i1b1`); excludes the `aw runs` `Issue` column and the `--json`/`--agent` payloads (also `r2i1b1`); excludes changing any disposition's MEANING (child 01 `zz5yxq`).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:m85gxh
- Status: to-review
- Set: runnoop
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: bsc457
- Blocks-Release: next
- From-Backlog: em0z50

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `em0z50` fix (c), the GENERAL requirement; inherits the item's `- Blocks-Release: next`. This is the child that CLOSES `em0z50`, because it ships the last of the item's three fixes and the operator-visible capability the item describes is not delivered until the closing summary prints. Every claim measured at HEAD `44d4950d`. THREE MEASUREMENTS SHAPED THIS PLAN. FIRST, the aggregation substrate already exists: `status_summary_str` (`render_stream.py:1855`) builds count strings from `status_counts`, so this plan does not invent counting; it changes WHAT is counted (dispositions, not queue statuses), adds the remedy, and guarantees the print. SECOND, the misleading footer and the resume hint share one function and one `SUCCESS_STATES` read (`oc_runipd.py:7362` and `:7377`), which child 01 changes, so this plan MUST re-measure the footer at execution time instead of trusting an authoring-time description; E-04 says so explicitly. THIRD, the overlap fence with pending plan `r2i1b1` is narrow but real: that plan replaces the diagnostics allowlist inside `render_run_summary_table` and adds a refusal record with a REMEDY field. This plan's summary is a NEW closing block, not an edit to that allowlist, and if `r2i1b1` has landed it must SOURCE its remedies from that record rather than writing a second remedy table. E-06 requires that be checked from the plan's status on disk.
  ONE THING DELIBERATELY NOT CLAIMED: the backlog item asks that the summary be "the authoritative answer to what did this invocation actually do". This plan makes it the authoritative HUMAN answer. It does not make it machine-readable, because the `--json`/`--agent` payload surfaces belong to `r2i1b1`, whose E-03 must first extract the five duplicated `aw runs` issue-predicate copies. Stated here rather than left as an implied gap.

## Goal

Give every run a closing statement that names every matched artifact's disposition, counts them, and says what to do next, printed even when the run did nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the summary and its remedies

- [ ] E-01 ADD ONE PURE SUMMARY RENDERER to `run_selection_policy.py`, taking the matched artifacts and their dispositions as plain data and returning the closing block: a line per matched artifact and a per-disposition count line. Pure means it returns lines, prints nothing, touches no filesystem, and imports no runner, exactly as `render_action_preview` (`:589`) and `render_refusal` (`:693`) already do there.
  DERIVE THE PER-ARTIFACT LINES FROM CHILD 02'S RENDERER, do not re-format them. Child 02 (`m85gxh`) put one line renderer in this same module for exactly this shape, and its plan forbids a second. Calling it is what makes CID-3 (one disposition vocabulary across the line and the summary) true by construction rather than by test.
  THE COUNTS MUST SUM TO THE NUMBER MATCHED, and that is the property worth asserting, not the individual numbers. `status_summary_str` (`render_stream.py:1855`) counts QUEUE STATUSES today, which is a different denominator; do not reuse its input.
  - Depends on: none
  - Expected outcome: one pure function returning the closing block; per-artifact lines produced by child 02's renderer rather than re-formatted; the counts sum to the number matched; an AST walk shows the module's first-party imports unchanged.
  - Execution state: pending

- [ ] E-02 ADD THE REMEDY FOR EACH ACTIONABLE DISPOSITION, as data beside the disposition rather than a string at a call site, so a new disposition cannot be added without an author noticing its remedy is missing. The backlog item gives the shape verbatim for the measured case: `needs-approval (8): aw ipd set approved <id6> --by-human, or re-run with --full-auto`.
  THE REMEDY IS THE POINT, NOT DECORATION, and the reason is recorded in this repository's own history: `AGENTS.md` and pending plan `r2i1b1`'s OQ-01 both record that a message saying only "X is not allowed" gets complied with by DELETING the thing, when a correct non-destructive fix exists. A count without a remedy tells an operator they are stuck.
  VERIFY EVERY REMEDY COMMAND BY RUNNING ITS `--help`, not by writing what you remember. `aw ipd set approved <id6> --by-human` must be checked against the shipped CLI, and `--full-auto`'s effect must be stated accurately: it clears `reviewed -> auto-approved` (the automated tier), NOT to human `approved`, per executed plan `97df1z`. A remedy that does not work, or that overstates what it grants, is worse than none.
  MARK A DISPOSITION WITH NO REMEDY EXPLICITLY. Some dispositions are terminal and correct (`executed`), and printing a fabricated remedy for them would be noise. Distinguish "no remedy needed" from "remedy unknown" and never render the second as the first.
  - Depends on: E-01
  - Expected outcome: a remedy associated with each actionable disposition as data; every remedy command verified by running its `--help` and the output pasted; dispositions needing no remedy marked as such distinctly from unknown.
  - Execution state: pending

- [ ] E-03 PRINT THE SUMMARY FROM BOTH HOSTS UNCONDITIONALLY, INCLUDING FOR A RUN THAT ACTED ON NOTHING. This is the item that fixes the measured incident: the zero-action case is precisely the one that printed nothing.
  FOLLOW THE ESTABLISHED UNCONDITIONAL-REPORTING PRECEDENT rather than inventing a rule: `announce_run_order` (`oc_runipd.py:4122`) prints the order whether or not anything was reordered, and its docstring gives the reason ("the order must be auditable in the log even when nothing was reordered"). The same argument applies at exit, more strongly.
  PLACE IT WHERE BOTH A HUMAN AND A PIPED READER SEE IT. `r2i1b1`'s OQ-01 resolution records the maintainer's requirement that critical closing information appear at the START and the END of output, deliberately duplicated, because agents habitually pipe through `head` or `tail`. Decide whether this summary takes that treatment and record the decision; do not silently choose one position.
  DO NOT ADD A SYMBOL TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back. Both hosts import from `run_selection_policy`.
  - Depends on: E-02
  - Expected outcome: both hosts print the summary on every exit path including a zero-action run; the placement decision recorded with its reason; neither host gained an import from the other.
  - Execution state: pending

### Task group 2: stop the footer lying

- [ ] E-04 RE-MEASURE `render_continuation_hint` AT EXECUTION TIME, THEN FIX THE FOOTER. The sentence `No OpenCode session was captured for this run.` (`oc_runipd.py:7362`, agy `:4568`) reads as a launch failure; it must instead say that no turn was ATTEMPTED when that is the truth, and keep its current meaning when a launch genuinely failed.
  RE-MEASURE FIRST, BECAUSE CHILD 01 MOVED THIS. The same function's `all_success` predicate reads `SUCCESS_STATES` (`:7377`, agy `:4583`), and child 01 (`zz5yxq`) changes what that decides for an execute item, so the footer's live behavior at your execution time is NOT what this plan describes at authoring time. Measure it, paste what you measured, and fix from that.
  DISTINGUISH THE TWO CASES RATHER THAN REWORDING ONE SENTENCE. "No session captured because no turn was attempted" and "no session captured although a turn was attempted" are different facts with different remedies, and collapsing them is the defect. The queue's attempt records are the evidence for which one holds.
  DO NOT CHANGE THE RESUME-HINT LOGIC. `all_success` also decides whether the footer offers `aw runs <id>` or `<cmd> resume ... <run-id>`, and that choice is child 01's to move. This item changes the SENTENCE, not the branch.
  - Depends on: E-03
  - Expected outcome: the measured pre-change footer behavior pasted; the two cases distinguished with different text; the resume-hint branch untouched; both hosts changed identically.
  - Execution state: pending

### Task group 3: prove and fence

- [ ] E-05 ADD THE REGRESSION TEST FOR THE MEASURED INCIDENT: a run matching N artifacts and acting on ZERO still prints the summary, its counts sum to N, and each actionable disposition carries its remedy. Assert on the ACTUAL rendered output, not on the data structure, because the defect was that nothing was PRINTED.
  ADD THE MUTATION CHECK, since a test asserting presence passes trivially. Suppress the unconditional print, show the test FAILS, restore, show it passes.
  PIN THE SHARING SYMMETRICALLY. Register every added symbol in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed; that file's `test_the_table_covers_both_runners` already fails a one-sided table, and the one-sided versions of this guard were RETIRED for being one-sided, which is how the `render_stream` re-fork went unnoticed.
  - Depends on: E-04
  - Expected outcome: tests per host for the zero-action case, the counts-sum property, and remedy presence, asserting on rendered output; a mutation check demonstrating the test can fail; a symmetric `REFORK_TABLE` row.
  - Execution state: pending

- [ ] E-06 RECONCILE WITH PENDING PLAN `r2i1b1` FROM ITS STATUS ON DISK, and record the answer. If it has EXECUTED, its refusal record carries reason AND remedy fields, and this summary must SOURCE remedies from that record rather than maintaining a second remedy table; also confirm its replacement of the diagnostics allowlist did not already add a closing block this plan would duplicate. If it has NOT executed, this plan's remedy data stands alone and must not define a refusal record type.
  DO NOT EDIT THE DIAGNOSTICS BLOCK UNDER EITHER BRANCH. `render_stream.render_run_summary_table`'s diagnostics block (`:2152`) is `r2i1b1`'s E-02 deliverable. This plan's summary is a separate closing block.
  - Depends on: E-05
  - Expected outcome: `r2i1b1`'s status read and pasted; the sourcing decision made and justified; no refusal record type defined here; the diagnostics block unedited.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_selection_policy.py` IS THE PURE-RENDERER HOME and states its own anti-duplication rule: `render_action_preview`'s docstring records that a second renderer was rejected because "the alignment rule, the type order, the action order, and the untyped-tail line would then exist twice and drift once". AST-verified purity: its only first-party imports are `selectors` and `status_set` (`:39-40`).
- UNCONDITIONAL REPORTING IS ALREADY THIS REPO'S CHOICE. `announce_run_order` prints the order even when nothing was reordered, for the stated reason that the log must be an audit trail rather than something to reconstruct from event timestamps.
- A REFUSAL MUST NAME THE CONSTRUCTIVE FIX. Recorded in `AGENTS.md` and in `r2i1b1`'s OQ-01 resolution: a message saying only that something is forbidden gets complied with by deletion. That is why E-02 makes the remedy a required field rather than an optional one.
- START-AND-END DUPLICATION IS AN ACCEPTED COST for critical closing information, per `r2i1b1`'s OQ-01 maintainer resolution, because readers pipe through `head` or `tail`.
- `--full-auto` CLEARS `reviewed -> auto-approved`, NOT to human `approved` (executed plan `97df1z`, and `oc_runipd.py:722` carries the exact provenance string "auto-approved by --full-auto: review readiness cleared (not human approval)"). Any remedy text mentioning it must not overstate what it grants.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses), while a lane worktree shows roughly 32 environmental failures.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:7362`, `agy_runipd.py:4568` | `No OpenCode session was captured for this run.` is the ONLY closing output of a zero-action run, and it describes a failed launch rather than an unattempted one. | source read; backlog `em0z50`'s observed output |
| F-2 | HIGH | `render_stream.py:1872`, `:2152` | The exit summary calls a zero-action run `COMPLETED` at 100% with no diagnostic, because `reviewed` is in the COMPLETED tuple and absent from the five-status diagnostics allowlist. | rendered the real function with one `reviewed` item |
| F-3 | MED | `render_stream.py:1855` | A count line already exists but counts QUEUE STATUSES, carries no remedy, renders inside the table, and is not guaranteed for a zero-action run. So counting is not the missing piece; the denominator, the remedy, and the guarantee are. | source read |
| F-4 | MED | `oc_runipd.py:7362` / `:7377`, `agy_runipd.py:4568` / `:4583` | The misleading footer and the resume hint are in the SAME function and the branch reads `SUCCESS_STATES`, which child 01 changes. So the footer's behavior moves under this plan's feet and must be re-measured at execution time. | source read, both hosts |
| F-5 | MED | `oc_runipd.py:4122`, `render_stream.py:1530` | The unconditional-reporting precedent already exists at run START with its rationale in the docstring, so an unconditional closing summary is consistent rather than novel. | source read |
| F-6 | MED | `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md` | A pending plan owns the diagnostics allowlist, the refusal record (whose REMEDY field is a required one), and the five `aw runs` issue-predicate copies. Its OQ-01 records the maintainer's start-and-end duplication requirement. | read that plan |
| F-7 | LOW | `oc_runipd.py:722` | The auto-approval provenance string already states that `--full-auto` is not human approval, so a remedy citing it has an exact wording to be consistent with. | source read |

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
- The `render_stream` COMPLETED tuple (`:1872`), which treats `reviewed` as a success. It is the renderer's copy of child 01's question. Excluded here because `r2i1b1`'s E-02 is editing that same function and because changing the table's verdict is a different claim from adding a closing summary; if the summary and the table's `Outcome:` visibly disagree after this plan, that is worth an item rather than a quiet edit inside this fence.
- The per-artifact line itself and its skip-reason vocabulary: child 02 (`m85gxh`), declared as this plan's `executed:` dependency.
- Changing what any disposition MEANS, or the run's exit code: child 01 (`zz5yxq`).
- Extending the discipline to `aw runs`, `aw ipd set`, and `aw find`, which the backlog item raises as a question. Each has its own selector semantics and tests; prove the driver shape first.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY to CALL the summary renderer and to change the footer SENTENCE. Do NOT change any gate, disposition value, exit code, or the resume-hint branch. Do NOT edit `render_stream.py` at all.
- Under-scope: stated rather than left as `none`. The summary is not machine-readable after this child, and the exit summary TABLE may still print `COMPLETED` for a zero-action run until child 01's renderer-side twin is addressed. Both are named above with their owners rather than left for a reader to discover.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured THERE and pasted, failing NODE IDS compared. `tests/test_run_selection_policy.py` is where the pure renderer's cases belong. `tests/test_run_summary_table.py` pins the existing diagnostics wording and belongs to `r2i1b1`; do not rewrite it, and if this plan's output makes one of its assertions ambiguous, report rather than edit. Note `tests/test_runner_shared.py::WrapperTests` counts per-runner call sites deliberately.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 already REQUIRES this summary's content, so this child moves the shipped code TOWARD the approved contract and does NOT amend it. Its exact requirement: "The final table includes position, ID/path, type, starting status, action trace, final item state, verification state, reason code, commit(s), and next command." The `next command` element IS this plan's remedy, and `reason code` is child 02's skip reason. No spec file is declared in `- Scope-Paths:`.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, §5.6 says "the final TABLE", and the shipped final table is `render_run_summary_table`, which this plan deliberately does not edit. Confirm whether the spec is satisfied by a separate closing block beside that table, or whether it requires the elements to live IN the table; if the latter, that is a conflict with the `r2i1b1` fence and must be reported to the maintainer rather than resolved by editing another plan's surface. SECOND, if the footer rewording changes an operator-facing recovery string that §1.2 or §4.2 quotes, the spec quotes it verbatim and the change must be reflected. Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the summary print at the END only, or at both the START and the END?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because the end-only form already fixes the measured defect (a zero-action run printing nothing), so the plan is executable either way. The maintainer's recorded preference in `r2i1b1`'s OQ-01 is start-and-end duplication for critical information, accepted deliberately because readers pipe through `head` or `tail`. The complication is that a START summary cannot know final dispositions, so the honest start-side artifact is the MATCHED list (which `announce_run_order` already prints) rather than the summary. Probably the answer is: keep the existing start-side announcement, put the disposition summary at the end, and make the end block self-contained. Decide and record; do not leave it implicit.

### OQ-02: Should the exit summary table's `Outcome:` be corrected in the same change, given it will read COMPLETED beside a summary saying nothing was done?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer because it crosses another plan's fence
- Resolution or deferral rationale: NOT blocking, because the summary is correct and useful whatever the table says, and a visible disagreement is strictly better than the current silence. But it IS a real inconsistency: `render_stream.py:1872`'s COMPLETED tuple contains `reviewed`, and `r2i1b1`'s E-02 is editing that same function, while pending plan `xtklpd` (`integearn` Order 02) is separately changing that outcome expression for the stranded-lane case. THREE plans converging on one expression is a coordination question, not an implementation one. The default is: do NOT edit it here, report the disagreement, and let the maintainer decide which plan owns the tuple. Reaching into `render_stream.py` would violate this plan's own scope fence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the summary renderer as written and the rendered block for a four-disposition mixed case. Paste proof the per-artifact lines came from child 02's renderer (show the CALL, not a similar string). Paste the counts and the number matched, showing they SUM. Paste an AST walk of `run_selection_policy.py` showing its first-party imports are still exactly `selectors` and `status_set`, and paste proof the function prints nothing (call it in a fresh interpreter with no repo present).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the remedy data as written. For EVERY remedy command, paste the ACTUAL output of running its `--help`, proving the command and its flags exist as written. Paste one rendered summary showing a remedy beside its count, in the shape the backlog item specifies. Paste one disposition marked as needing no remedy and one that would be marked unknown, showing they render DIFFERENTLY.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL stdout of a run that acted on ZERO artifacts, showing the full summary. Paste the same for a mixed run. Paste the placement decision (OQ-01's answer) and the reason. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47. Both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the PRE-CHANGE footer behavior as MEASURED in the executing worktree, not as described in this plan, since child 01 moved it. Then paste the two post-change forms side by side: the no-turn-attempted case and the launch-failed case, showing they differ. Paste proof the resume-hint BRANCH is unchanged (a diff of that expression, or the assertion that covers it). Both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the tests and their actual runner output. Paste the MUTATION CHECK in full: suppress the unconditional print, paste the FAILING output, restore, paste the passing output. Paste the new `REFORK_TABLE` row showing BOTH runners, and `tests/test_runner_refork_guard.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `r2i1b1`'s `- Status:` line and its directory, read at validation time. State which branch applied and what was done. Paste proof the `render_stream` diagnostics block is UNEDITED (a diff of `render_stream.py` showing no change, or the file absent from this plan's commits). If `r2i1b1` executed, paste the code sourcing remedies from its record. THEN close backlog `em0z50`: paste its `- Status:` line showing `done`, and paste `aw backlog check` clean. `em0z50` carries `- Blocks-Release: next`, so its close is gated on the handoff, which this plan's `- From-Backlog: em0z50` plus matching `- Blocks-Release: next` satisfies; paste the setter's actual output rather than hand-editing the item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT edit `render_stream.py` at all, including its COMPLETED tuple and its diagnostics block. Do NOT define a refusal record type. Do NOT change any gate, disposition value, exit code, or the resume-hint branch. Do NOT add a first-party import to `run_selection_policy.py` beyond the two it has. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT rewrite `tests/test_run_summary_table.py`. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and child 01 of this Set edits the very function E-04 changes. Find `render_continuation_hint`, `announce_run_order`, `render_run_summary_table`, `render_action_preview`, and `deliberate_stop_exit_code` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved bsc457 --by-human --message ...`) before execution, and child 02 (`m85gxh`) must read `executed` first, which the declared `- Item-Dependencies: executed:m85gxh` enforces. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION OF THIS PLAN, close backlog `em0z50`, which all three children of this Set carry as `- From-Backlog:` and whose `- Blocks-Release: next` gate they inherit. It closes HERE and not on a sibling, because the operator-visible capability it describes is the closing summary, which ships here.

# IPD: Report a run whose work never landed as NOT DONE in red from the run's own record

- Date: 2026-09-08
- Kind: child
- Concern: A run whose entire product was stranded prints a green `Outcome: COMPLETED` at `100%`. MEASURED 2026-09-08 on `run-20260908T140845Z-2489897`: the summary read `Outcome: COMPLETED   Duration: 54m 26s   Spend: $32.83` and `Progress: 1/1 [##########] 100% (1 substantially-complete)` while NOTHING had been integrated; the work sat on a lane branch and the maintainer only discovered it by auditing `git worktree list` by hand. The mechanism is a missing question rather than a wrong answer: `render_run_summary_table` derives the outcome purely from per-item STATUS (`render_stream.py:1869-1877`), and `substantially-complete` is inside the success tuple, so a stranded run and a landed one are indistinguishable to it. The verdict, its reason and the recovery route were all recorded at the time (`integration_signal`, `integration_detail`, `preserved_branch`); no report reads any of them.
- Scope: Make the summary tell the truth about LANDING, using only what the run itself recorded. IN: an outcome that is not `COMPLETED` when the run's own record says integration was refused, rendered in red, naming the preserved branch and the refusal reason. OUT: the CAUSE of stranding (sibling Order 03), the cross-tree `aw attention` view (backlog `nuanaw`), and any change to what integration DECIDES.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_run_summary_table.py
- Item-Dependencies: none
- Status: to-review
- Set: integearn
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ys1dor
- From-Backlog: 7m0aro
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): REPLACES the rejected plan `xtklpd` (Set `integearn` Order 02, `- Status: reviewed`, `- Readiness: no-go`), keeping its correct diagnosis and discarding its mechanism. Authored on the maintainer's ruling of 2026-09-08: report a stranded run as NOT DONE, in red, derived from the run's OWN record. WHY `xtklpd` COULD NOT BE REVISED IN PLACE: its E-04 derived the outcome from `run_viewer.audit_step_artifact`, which reads the LIVE FILESYSTEM, and its own review measured the consequence: auditing the stranded `mm6wuz` run TODAY returns `expected=executed actual=executed` because a later hand recovery moved the plan, so re-rendering that run's summary now reports COMPLETED again. A filesystem-derived summary silently REWRITES HISTORY, which is the exact defect the plan existed to remove. This plan therefore takes the opposite rule: a run summary is a statement about WHAT THAT RUN DID, and only the run's own recorded state is immutable in that way. VERIFIED AT HEAD `e148f82c`: the outcome computation is unchanged at `render_stream.py:1869-1877`, `substantially-complete` is still inside the success tuple at `:1871-1873`, `COMPLETED` is assigned at `:1877`, and the green color is selected at `:1891-1893`. ALSO VERIFIED the facts needed are present without any new plumbing: both drivers write `attempt["integration_signal"]`, `attempt["integration_detail"]`, `item["integration_signal"]` and `item["preserved_branch"]`, and `grep` finds ZERO consumers of `integration_signal` in any reporting module, so this is purely a missing reader. ONE CORRECTION TO `xtklpd` CARRIED FORWARD: its finding that the integration verdict is DISCARDED was already corrected at its own review to "the verdict is persisted and no report reads it", and that corrected version is what this plan builds on.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop a run reporting success for work that never landed. The operator's first and often only signal is the end-of-run summary; it must distinguish "the task finished" from "the work is in your project", because those diverged and the difference cost eleven stranded lanes and one duplicated payment.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: ask the missing question

- [ ] E-01 Add a LANDED question to the outcome computation in `render_run_summary_table` (`render_stream.py:1656`, outcome block `:1869-1881`). Today the success branch tests only per-item status membership in `("executed", "reviewed", "approved", "substantially-complete")` (`:1871-1873`) and assigns `COMPLETED` at `:1877`. Add a prior test: if ANY item's own record shows integration was REFUSED, the run is not `COMPLETED`. Read the refusal from the item's recorded `integration_signal`, which both drivers already write; treat the refusing values as the ones the runner itself defines rather than a hand-copied list, so a new refusal reason cannot silently read as success. DO NOT read the filesystem, and do not consult plan directories or current statuses: that is precisely what made `xtklpd`'s approach rewrite history.
  - Depends on: none
  - Expected outcome: a run with a refusing `integration_signal` on any item does not report `COMPLETED`; a run with none behaves exactly as today.
  - Execution state: pending

- [ ] E-02 Choose the OUTCOME WORD deliberately and make it unmistakable. The maintainer's requirement is that it SCREAM, so it must not be a synonym a reader skims past. `STRANDED` or `NOT LANDED` both state the fact; pick one, use it consistently, and do NOT reuse `PARTIAL` (which already means something else here: some items completed, `:1878-1879`) or `BLOCKED` (which already means dependency-blocked, `:1868`). Render it RED, which means adding it to the color selection at `:1890-1900` rather than letting it fall through to whatever the else-branch gives, since an unhandled outcome silently inheriting a non-red color is exactly the class of miss this plan exists to fix.
  - Depends on: E-01
  - Expected outcome: the new outcome word is distinct from `PARTIAL` and `BLOCKED`, is rendered red, and is not produced by any pre-existing condition.
  - Execution state: pending

- [ ] E-03 Print the RECOVERY ROUTE, because an alarm an operator cannot act on trains them to ignore it. For each stranded item name its `preserved_branch` and its `integration_detail` (the human reason the runner already recorded, for example "no verifier ran (validation off) and the driver-run suite did not pass: ..."). Follow the file's established pattern of appending a SECTION rather than adding table columns: the existing `Diagnostics / Blocked Items` block does exactly this, and the repository has twice recorded that new facts go in sections so the table's column contract is unchanged. State the concrete next step, which is that the work is on that branch and must be merged or re-run.
  - Depends on: E-02
  - Expected outcome: a stranded run's summary names every preserved branch with its refusal reason and states what to do; the item table's columns are unchanged.
  - Execution state: pending

### Task group 2: do not break the honest cases

- [ ] E-04 Preserve every OTHER outcome exactly, verified case by case, because this function is the single most-read output in the product. `BLOCKED` when dependency-blocked (`:1868`), `COMPLETED` for a genuinely landed run, `PARTIAL` when some items completed (`:1878-1879`), `QUEUED` when none did (`:1880-1881`), and the interrupt and stop wordings whose yellow selection is keyed on substrings (`:1895-1900`). A run with NO lanes at all (a review-only run, which integrates nothing by design) must still report `COMPLETED`: an item that was never eligible for integration has no refusal recorded, so it must not be swept into the new outcome. That case is the most likely false positive and needs its own test.
  - Depends on: E-01
  - Expected outcome: all five existing outcomes and the review-only case behave exactly as at HEAD `e148f82c`, demonstrated individually.
  - Execution state: pending

- [ ] E-05 Do NOT make the summary re-derivable into a different answer later, which is this plan's whole reason for existing. The summary must be reproducible from the run's own `state.json` alone: re-rendering an OLD run must produce what that run reported at the time, even after the lane was recovered by hand and the plan moved to `executed/`. PROVE IT ON A REAL RECOVERED RUN: `run-20260908T140845Z-2489897` (plan `03ie04`) was stranded and has since been recovered and finalized, so re-rendering it must STILL say stranded. That is the exact case where `xtklpd`'s filesystem approach was measured to report `COMPLETED`, so it is the sharpest available test of the difference.
  - Depends on: E-03
  - Expected outcome: re-rendering the recovered run's summary still reports stranded, demonstrated against the live record.
  - Execution state: pending

- [ ] E-06 Test with FIXTURES for the synthetic cases and the real record for E-05. `tests/test_run_summary_table.py` already owns this surface and already builds queue dictionaries directly (its existing test supplies `driver_error` on a `failed-safely` item), so extend that harness. Cover: a stranded item yields the new outcome in red; a landed run still yields green `COMPLETED`; a review-only run with no lanes yields `COMPLETED`; a mixed run with one stranded and one landed item yields the stranded outcome (a partial strand is still a strand); the recovery section names branch and reason; and E-05's real recovered run. Assert the stranded case FAILS against HEAD `e148f82c`, where it reports `COMPLETED`.
  - Depends on: E-04, E-05
  - Expected outcome: six cases pass; the stranded case fails before the change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The outcome is computed from per-item STATUS ONLY (`render_stream.py:1869-1881`); nothing in it asks about integration. `substantially-complete` sits inside the success tuple, which is why a stranded run reads as complete.
- The color selection is keyed on the outcome STRING, including substring tests for interrupt and stop wordings (`:1890-1900`). A new outcome word must be added there explicitly or it silently inherits a non-red color.
- The file already appends SECTIONS rather than table columns for new facts (the `Diagnostics / Blocked Items` block), and this repository has recorded that choice twice so the table's column contract stays stable.
- The needed facts are already persisted by BOTH drivers: `integration_signal`, `integration_detail`, `preserved_branch`, `preserved_worktree`, `preserved_lane_id`. `grep` finds no reporting consumer of `integration_signal`.
- A run summary must be derivable from the run's own immutable state. `xtklpd`'s review measured the alternative failing: a filesystem audit of a recovered run reports it clean, so the summary would rewrite history.
- `substantially-complete` is a DELIBERATE and correct status. It records that the agent's work and validation finished while the lifecycle transition did not, and `reconcile_disposition` downgrades a claimed `executed` to it as an anti-fabrication guard. Do NOT remove it from the success tuple; add the landing question alongside it (removing it is the larger-blast-radius option the maintainer did not choose).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | A fully stranded run reports green success: `Outcome: COMPLETED`, `Progress: 1/1 100% (1 substantially-complete)`, with nothing integrated. | measured on `run-20260908T140845Z-2489897` |
| F-2 | The cause is a missing question: the outcome tests per-item status membership only, and `substantially-complete` is in the success tuple. | `render_stream.py:1869-1877`, tuple at `:1871-1873` |
| F-3 | The facts were recorded the whole time and no report reads them. | both drivers write `integration_signal`/`integration_detail`/`preserved_branch`; zero reporting consumers of `integration_signal` at `e148f82c` |
| F-4 | THE REJECTED APPROACH REWRITES HISTORY: deriving the outcome from a filesystem audit reports a recovered run as `COMPLETED`, measured on `mm6wuz` after its hand recovery moved the plan. | `xtklpd` review finding F-11 / OQ-04, re-read at `e148f82c` |
| F-5 | The scale of the harm: eleven lanes stranded unnoticed on one unrelated red test, and plan `03ie04` executed twice for the same fix (`$16.59` then `$32.83`). | run records audited 2026-09-08 |
| F-6 | The color path is string-keyed, so an unhandled new outcome would not be red by default. | `render_stream.py:1890-1900` |
| F-7 | `substantially-complete` is correct and load-bearing, so the fix must add a question rather than remove that status. | `reconcile_disposition`'s anti-fabrication override, recorded in `xtklpd`'s finding (1) |

## Proposed changes (ordered, validatable)

1. Ask whether integration was refused, from the item's own record, before assigning `COMPLETED` (E-01).
2. Pick a distinct, unmistakable outcome word and render it red explicitly (E-02).
3. Append a recovery section naming each preserved branch and its reason (E-03).
4. Preserve all five existing outcomes and the review-only case (E-04).
5. Prove the summary cannot be re-derived into a different answer later (E-05).
6. Pin six cases, with the stranded one failing before the change (E-06).

## Deferred / out of scope (with reason)

- THE CAUSE OF STRANDING. Sibling Order 03 (`daexj1`) replaces the binary suite gate with the maintainer's agent-adjudication design. This plan makes stranding VISIBLE; that one makes it RARE. They are independent and either can land first.
- THE CROSS-TREE VIEW. `aw attention` is equally blind and is backlog `nuanaw` (high, `Blocks-Release: next`). A run summary is seen once; the durable "what needs attention" answer is a different surface, and a lane stranded last week would still be invisible with only this plan landed.
- REMOVING `substantially-complete` FROM THE SUCCESS TUPLE, or adding a new item-level status. Offered to the maintainer as the cleanest model and NOT chosen, because that vocabulary is read by plans, tests and both runners, so the blast radius is much larger than the reporting fix.
- CHANGING WHAT INTEGRATION DECIDES. Untouched; this plan only reports the decision already made.
- `aw runs` OUTPUT. `xtklpd` also covered the run VIEWER. Left out deliberately to keep this fence to one file plus its test; the viewer is the natural companion once this reader exists, and `nuanaw` covers the attention half.

## Scope check

- Over-scope: none. One rendering module and its test module.
- Under-scope: deliberately narrow. The cause, the cross-tree view and `aw runs` are all owned elsewhere (see Deferred).

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline at authoring is 1 failed, 5858 passed (the known `test_plan_readiness` failure); judge on the DELTA.
- `python3 -m pytest tests/test_run_summary_table.py` for the focused surface.
- The E-05 real-record proof: re-render `run-20260908T140845Z-2489897` and show it still reports stranded despite the lane having been recovered and `03ie04` now being `executed`.
- A rendered sample of each of the six E-06 cases, pasted, so the wording and the color are reviewable as text rather than described.

## Spec / documentation sync

No `.spec.md` file governs the run summary's outcome vocabulary, so none is edited and none is declared in `Scope-Paths`. TWO checks for the executor. FIRST, `docs/` may document the summary's outcome words; if it does, the new word must be added there in the same change, and that file then enters the fence. SECOND, spec `25kzda` governs the run pipeline and its exit-code contract: this plan changes a DISPLAYED outcome word, not a process exit code, so confirm the run's exit code is unchanged and say so, because an operator or CI job keying on the exit status must not silently change behavior. If the executor concludes the exit code SHOULD also change for a stranded run, that is a contract change requiring the spec path in `Scope-Paths` and its own justification.

## Open questions

### OQ-01: Should a stranded run also change the process EXIT CODE, not just the printed outcome?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, and genuinely arguable both ways, so it is the maintainer's. FOR: an automated caller (CI, a wrapper script, another agent) reads the exit code, not the pretty table, and a green exit for stranded work is the machine-readable version of exactly the lie this plan removes. AGAINST: the exit code is part of the run contract that spec `25kzda` governs, existing callers may treat non-zero as "the run crashed" rather than "the work needs collecting", and this plan's fence is one rendering file. RECOMMENDATION: land the visible fix now and decide the exit code separately, since the two have different blast radii and the printed outcome is what misled a human here. Note backlog `nuanaw` asks for `aw attention --check` to fail closed on a stranded lane, which gives automation a fail-closed signal without touching the run's exit contract.

### OQ-02: Should a PARTIALLY stranded run report stranded, or partial?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: DECIDED IN THE PLAN as STRANDED, with the reasoning recorded so a reviewer can overrule. A run where three items landed and one did not is a run with unintegrated work sitting in a lane, and that is the fact an operator must act on; reporting `PARTIAL` would bury it under a word that already means something milder here. E-06 pins the mixed case for this reason. The counter-argument is that a mostly-successful run reading as stranded may feel alarmist; the answer is that the recovery section (E-03) names exactly which items are affected, so the alarm is specific rather than blanket.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the rendered summary for a fixture run carrying a refusing `integration_signal`, showing the outcome is NOT `COMPLETED`, alongside the SAME fixture with no refusal showing it still is. Paste the code showing the refusal values come from the runner's own definitions rather than a copied literal list, and paste proof no filesystem read was added (a diff, and the absence of any path or directory lookup in the new branch).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered output with color enabled, showing the RAW escape sequence for red preceding the new outcome word (not merely a claim that it is red). Paste the color-selection diff. Paste evidence the word is not produced by any pre-existing condition (a grep for the word across the module).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the recovery section as rendered, showing each stranded item's preserved branch and its `integration_detail` text and a stated next step. Paste the item table from the same render alongside the pre-change table to show the columns are byte-identical.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: six rendered samples, one per preserved case: `BLOCKED`, `COMPLETED` (landed), `PARTIAL`, `QUEUED`, an interrupt or stop wording with its yellow selection, and a review-only run with no lanes reporting `COMPLETED`. Each must match HEAD `e148f82c` behavior; paste both renders where wording could differ.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the re-render of `run-20260908T140845Z-2489897` performed AFTER its recovery, showing it still reports stranded. Alongside it, paste evidence that a filesystem audit of the same run NOW reports it clean (for example the plan's current `executed/` location), so the two approaches are shown to disagree and the chosen one is shown to be the stable one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all six test names with results, AND the stranded case's FAILING output against pre-change code (stash the change and re-run), proving it bites. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

A reviewer should know that this plan SUPERSEDES `xtklpd` rather than revising it, because that plan's mechanism was measured to rewrite history (F-4), and that its central rule is a maintainer ruling of 2026-09-08: report NOT DONE, in red, from the run's own record. OQ-01 (whether the exit code should follow) is left to the maintainer deliberately, since it changes a machine contract rather than a human-facing word.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. Re-locate `render_run_summary_table` and its outcome block BY SYMBOL at execution time; the block's coordinates have already drifted between review rounds of the plan this one replaces. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`.

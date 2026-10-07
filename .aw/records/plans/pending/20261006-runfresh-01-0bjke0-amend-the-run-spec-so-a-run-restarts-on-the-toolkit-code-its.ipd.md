# IPD: Amend the run spec so a run restarts on the toolkit code its children landed

- Date: 2026-10-06
- Kind: child
- Concern: Spec `25kzda` Section 5.3 ("Durable state and restartability") requires the run to be restartable from durable state and requires the frozen driver record to name the module that created the run, but says nothing about the driver's own code changing during the run. In practice the driver keeps the code it loaded at start for the whole run, so a run whose children change the toolkit judges later steps by outdated rules. Measured 2026-10-06 on run `run-20261006T134924Z-332833`: the retirement of `1f4faf` failed post-transition lint with three `IPD-M103 ... unknown field` findings because the driver's linter predated the `- Coverage:` fields a child of the same run had added; current code lints the same file `conforming`. The same section also does not require a refusal to carry the lint findings that caused it, and the run record kept only "post-transition validation failed". Orders 02 to 05 of Set `runfresh` need an approved contract to implement.
- Scope: Edit exactly one spec file, `25kzda`, adding the text in Proposed changes (a new Section 5.3b and two sentences elsewhere), append a dated history line through `aw specs note`, and run `aw specs check`. OUT: any code or test; any other spec; the spec's `- Status:`.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0bjke0

## Workflow history
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 01 of Set `runfresh`. Amendment text is written below in full, cited by section name, so the contract can be approved before any code exists.

## Goal

Make spec `25kzda` require that a run's driver never judges an item with code older than what that run's own earlier items integrated, that the restart is recorded and bounded, and that a lint refusal at finalize or retirement records its findings.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: amend the spec

- [ ] E-01 Insert Proposed change A.1 (new Section 5.3b) immediately after Section 5.3a, and A.2 (one sentence at the end of Section 5.3's paragraph beginning "The frozen driver record within durable run state must name the module that created the run").
  - Depends on: none
  - Expected outcome: Section 5.3b exists with the text of A.1, and the Section 5.3 paragraph ends with A.2's sentence.
  - Execution state: pending

- [ ] E-02 Insert Proposed change A.3 (one paragraph) at the end of Section 4.1 ("Message and recovery conventions"), and A.4 (one numbered limit) at the end of Section 6.1's list. Then append the A.5 history line with `aw specs note <path> --message "<A.5 text>"`.
  - Depends on: E-01
  - Expected outcome: both insertions present; the history line present; `aw specs check` conforming; `- Status: approved` unchanged.
  - Execution state: pending

### Task group 2: confirm nothing else moved

- [ ] E-03 Confirm the one spec file is the only change, its status is unchanged, and each cross-reference the new text makes (Section 5.3, 5.3b, 4.1, spec `7ckptx` A8, spec `c4gd2h` R2, the event names `driver-restarted`, `driver-restart-unavailable` and `driver-restart-limit`, and `AW_NO_DRIVER_RESTART`) resolves.
  - Depends on: E-02
  - Expected outcome: `git diff --name-only` lists only the `25kzda` file; every cross-reference grep returns a hit; `aw check specs` gains no finding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SPECS ARE AMENDED IN PLACE WITH A DATED HISTORY LINE via `aw specs note`, in the form `AMENDED <date> (plan <id6>): <what changed and why>` (see `25kzda`'s own history). The status is not changed.
- A PLAN THAT AMENDS A SPEC DECLARES IT in `- Scope-Paths:` (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- CITE BY SECTION NAME, NEVER BY LINE NUMBER.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The driver keeps its start-time code. `oc_runipd.main` and `agy_runipd.main` call `run_queue` in the same process for the whole run; `run_queue`'s `while True:` loop calls `execute_item` and `dispatch_orchestrator_item` in that process; nothing re-imports `agent_workflows`. `ipd_lifecycle.retire_orchestrator` and `_complete_after_commit` call `ipd_lint.lint_file` in-process. | the two `main`/`run_queue` call chains; `_complete_after_commit` |
| F-02 | The 2026-10-06 failure is that mechanism. The run started at 09:49 (code `3f4763b56`); `8mabmu` added `ipd_schema.META_COVERAGE` at 11:30 (`c4dc37203`); the retirement at 20:57 was refused. Linting the retired file's committed bytes with code exported from `3f4763b56` returns `error` with `IPD-M103 Coverage: unknown field`, `IPD-M103 Coverage-Fingerprint: unknown field`, `IPD-M103 Coverage-Checked: unknown field`; with current code `conforming`. | the run's `orchestrator-deferred` event for `1f4faf`; the reproduction with `git archive 3f4763b56 agent_workflows` |
| F-03 | Section 5.3 already makes the run restartable from `state.json` (`resume`), so a driver restart can reuse it: "Each event is append-only ... A snapshot is a cache; replaying the ledger is authoritative." | the quoted Section 5.3 text; the `resume` subcommand of both drivers |
| F-04 | The refusal text dropped the findings. `_complete_after_commit` returns the findings in the result's `findings` tuple and in `evidence["post_transition"]`, but `retire_orchestrator`'s caller `dispatch_orchestrator_item` records only `result.message`. | `_complete_after_commit`; the `retirement transition refused: {why}` detail in `dispatch_orchestrator_item` |

## Proposed changes (ordered, validatable)

A.1 ADD a new Section 5.3b immediately after Section 5.3a:

> #### 5.3b A run is judged by the toolkit code its own items have landed
>
> Added 2026-10-06 by plan `0bjke0` (Set `runfresh`). A driver process loads the toolkit's code once. When an item of the same run integrates a change to that code, every later check the driver performs in-process (lint at begin, finalize and retirement; the coverage probe; production verification) would otherwise run on rules that are no longer on the branch. Measured on run `run-20261006T134924Z-332833`: an orchestrator retirement was refused for three metadata fields that a child of the same run had added, by a linter that predated them.
>
> Therefore:
>
> 1. AT RUN START the driver records, in durable run state, the toolkit code it loaded: the package root it imported `agent_workflows` from, and a fingerprint over the contents of every `agent_workflows/**/*.py` file under that root.
> 2. BETWEEN ITEMS, after the previous item's state is saved and before the next item is selected, the driver compares the fingerprint of the code the CURRENT process loaded with the same files on disk. When they differ, it RESTARTS ITSELF: it releases the run lock (so spec `c4gd2h` R2's "`driver.lock` is released" holds across the replacement) and every other per-process hold the resumed process will re-acquire, then replaces its own process with the host's `resume` of the same run, on the code now on disk. A restart never happens inside an item. The restart may be disabled for one driver process by the environment variable `AW_NO_DRIVER_RESTART=1`, which exists so a test can reproduce the old-code behavior; with it set the driver behaves as before this section.
> 3. A RESTART LOSES NOTHING. The resumed process reloads the queue, every item's status and attempts, the frozen options and the session map from the run's durable state exactly as an operator's `resume` does. The display options in force are carried over.
> 4. EVERY RESTART IS RECORDED as a `driver-restarted` event naming the old and new fingerprints, the item whose integration preceded it, and the restart count, and the run summary reports the count. Run start in a driver that will not restart (point 6) is recorded once as a `driver-restart-unavailable` event.
> 5. A RESTART CANNOT LOOP. The driver restarts only when the code on disk differs from the code the CURRENT process loaded, so a restarted process whose fingerprint matches the disk does not restart again. A per-run limit (default 20) refuses further restarts with a named `driver-restart-limit` refusal and stops the run cleanly, leaving the remaining items `queued`.
> 6. A DRIVER NOT RUNNING THE CHECKOUT'S OWN PACKAGE does not restart. When the imported package root is not the root of the checkout the run targets (for example, an installed copy), a restart would load the same outdated code, so the driver records once that it will not restart, and continues.
> 7. NESTED `aw` CALLS STAY PINNED TO THE DRIVER'S OWN PACKAGE (spec `7ckptx` A8). After a restart, the driver's own package IS the current code, so the pin follows it; the tool-identity check is re-established in the new process rather than relaxed.

A.2 Section 5.3, at the end of the paragraph beginning "The frozen driver record within durable run state must name the module that created the run": ADD:

> The frozen driver record also carries the loaded-code record of Section 5.3b, and a restarted driver appends a new loaded-code record rather than overwriting the original, so the run's history shows every code version it ran on.

A.3 Section 4.1 ("Message and recovery conventions"), at the end: ADD:

> A refusal caused by a lint checkpoint at finalize (pre-transition or post-transition) or at orchestrator retirement MUST carry every finding's code and message, in the refusal text, in the item's durable refusal record, and in `aw runs`. A refusal that says only that validation failed is incomplete, because the operator cannot act on it. (A refusal by `aw ipd begin` already carries its findings in its refusal text, which the driver records as the item's begin refusal.)

A.4 Section 6.1, at the end of the numbered list: ADD:

> 10. **A restart sees the code on disk, not only integrated code.** Section 5.3b compares files on disk in the checkout the driver runs from. Code a later item will land is not seen until it lands; code edited by hand in that checkout during a run, committed or not, is picked up at the next item boundary like any other change, so a half-finished hand edit can restart the driver onto code that fails to import. The run then stops at that boundary with its state saved, and `resume` after the edit is repaired continues it.

A.5 History line (via `aw specs note`): `AMENDED 2026-10-06 (plan 0bjke0, Set runfresh): new Section 5.3b requires the driver to record the toolkit code it loaded, to restart itself between items on the current code when an item of the run changed it (recorded, bounded, never inside an item, no restart when the loaded package is not the checkout's own), and to keep nested calls pinned to its own package; Section 5.3 driver record gains the loaded-code record; Section 4.1 requires finalize and retirement lint refusals to carry their findings; Section 6.1 gains limit 10. Motivated by run-20261006T134924Z-332833, whose orchestrator retirement was refused by a linter older than the fields its own children added.`

## Deferred / out of scope (with reason)

- ANY CODE OR TEST CHANGE. Orders 02 to 05.
  - Carrier-Declined: by construction; each later child cites the section it implements
- AMENDING SPEC `7ckptx`. A.1 point 7 preserves A8 rather than changing it.
  - Carrier-Declined: A8 is unchanged; the restart keeps the pin on the driver's own package

## Scope check

- Over-scope: none. One spec file.
- Under-scope: none; the code is Orders 02 to 05.

## Required tests / validation

- `python3 -m agent_workflows specs check <25kzda path>` pasted, conforming.
- `python3 -m agent_workflows check specs` pasted, no new finding against a pre-edit baseline.
- `git diff --name-only` pasted, listing only the `25kzda` file.
- Greps pasted: `5.3b A run is judged by the toolkit code`, `driver-restarted`, `driver-restart-unavailable`, `driver-restart-limit`, `AW_NO_DRIVER_RESTART`, `A refusal caused by a lint checkpoint`, `A restart sees the code on disk`, `7ckptx` and `c4gd2h` within 5.3b.
- `grep -n '^- Status:'` on the spec showing `approved` (the spec carries exactly one such line).
- `aw ipd lint` on this plan conforming.

## Spec / documentation sync

This plan IS the spec sync for Set `runfresh`. It edits spec `25kzda`, declared in `- Scope-Paths:`. WHY: `25kzda` owns the runner's durable-state and restart contract (Section 5.3) and its refusal-message contract (Section 4.1), which are exactly the two behaviors this Set changes. No user-facing document changes here.

## Open questions

### OQ-01: Should the restart limit be configurable?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a fixed default of 20 recorded in the spec, adjustable later if measured need appears. A restart happens at most once per item that changed the toolkit; the 14-item `gradcover` run had 10 such items (children whose `- Scope-Paths:` and commits touch `agent_workflows/`, re-measured at review), so 20 covers a large Set while still stopping a genuine loop. A flag adds surface for a case no run has needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` showing Section 5.3b inserted after 5.3a with A.1's text and the A.2 sentence at the end of the named 5.3 paragraph.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` for A.3 and A.4, the new history line as it appears, `aw specs check` conforming, and `- Status: approved` unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff --name-only` (one file), each cross-reference grep with its hit, `aw check specs` with no new finding against a pre-edit baseline, `aw ipd lint` on this plan conforming, and `git diff --cached --name-only` immediately before committing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval; approving it approves the contract Set `runfresh` implements. Commit only the declared spec path through `aw commit <plan> -- <path>`; never push; do not change the spec's `- Status:`. Paste actual output for every `V-*`. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.

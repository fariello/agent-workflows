# IPD: Keep a long run on the toolkit code its own children have landed

- Date: 2026-10-06
- Kind: orchestrator
- Concern: `aw oc run` and `aw agy run` import the toolkit's Python code once, when the run starts, and use that copy for the whole run, while the run's own children change that code on `main`. Measured on run `run-20261006T134924Z-332833` (Set `gradcover`, 11 hours): the driver started at 09:49 on 2026-10-06 against code at `3f4763b56`; child `8mabmu` landed the `- Coverage:` metadata fields at 11:30; at 20:57 the driver retired orchestrator `1f4faf`, whose file now carried those fields, and its in-memory linter (still the 09:49 code) rejected them as `IPD-M103 Coverage: unknown field` (three findings), so the retirement ended `committed-incomplete` and the item `fail-depend`. Reproduced: linting the retired file with the 09:49 code gives `error` with those three findings; with current code it is `conforming`, which is why the hand resume (`aw ipd finalize 1f4faf ... --apply`) succeeded. The run's own record kept only "post-transition validation failed", not the findings, so the cause took a code reconstruction to find. Any run whose children change the toolkit is exposed: later checks run on outdated rules and can refuse valid work (as here) or pass work the new rules reject. The maintainer is holding every approved plan that changes the toolkit until this is fixed (ruling 2026-10-06).
- Scope: ORCHESTRATION ONLY. This plan sequences six children and contributes no implementation, no test and no deliverable of its own. IN: the dependency order, the Set-level completion criteria with the child that owns each, and the cross-child checks. OUT: everything the children do: the spec amendment (Order 01), detecting that an integrated item changed the toolkit code (Order 02), restarting the driver on current code and resuming the same run (Order 03), recording lint findings on a finalize or retirement refusal (Order 04), the end-to-end proof (Order 05), and stopping `aw ipd coverage` and the other asking checks from reporting a plan ready when its coverage answer was not saved (Order 06).
- Scope-Paths: .aw/records/plans/pending/20261006-runfresh-01-0bjke0-amend-the-run-spec-so-a-run-restarts-on-the-toolkit-code-its.ipd.md, .aw/records/plans/pending/20261006-runfresh-02-34zv7d-detect-when-an-integrated-item-changed-the-toolkit-code-the.ipd.md, .aw/records/plans/pending/20261006-runfresh-03-re15ol-restart-the-runner-on-the-current-code-between-items-and-res.ipd.md, .aw/records/plans/pending/20261006-runfresh-04-vvqr34-record-the-findings-when-a-finalize-or-retirement-lint-refus.ipd.md, .aw/records/plans/pending/20261006-runfresh-05-hohlc6-prove-a-run-that-changes-its-own-linter-retires-its-orchestr.ipd.md, .aw/records/plans/pending/20261006-runfresh-06-7kczdo-never-report-a-coverage-answer-as-recorded-when-it-was-not-w.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: 1e0ad585ff6c4fb5f2d3e277a5df4a5e918d88d8ecb078e298c5f4d141b7efdb
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 0
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 67lvds

## Workflow history
- 2026-10-06 coverage pass (aw oc run): fingerprint 1e0ad585ff6c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): added Order 06 `7kczdo` at the maintainer's instruction, for the silent loss of a coverage answer on a plan with uncommitted changes, found while recording this plan's own answer.

- 2026-10-06 coverage pass (aw oc run): fingerprint e1d11a14b45f, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored at the maintainer's instruction (2026-10-06: "Option 2, in an IWT. Build the plan/plan set. We'll hold the approved plans until we fix this."). Option 2 was chosen over (1) running only the final lint as a separate process, which fixes the one failure but leaves every other in-process check on old code, and (3) only recording the findings, which explains failures but prevents none; (3) is still included here as Order 04 because without it the next such failure is equally opaque. No backlog item, per the maintainer's direction; `- Blocks-Release: f33nrj` because every plan is `Work-Kind: bug`. `- From-Spec: none`: this Set amends `25kzda` (Order 01) rather than being produced from it.

## Goal

After this Set, a run whose children change the toolkit's own code restarts itself on the new code before its next item and continues the same run, so every later check, finalize and retirement is judged by the rules that are actually on `main`; and any finalize or retirement lint refusal records its findings.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: sequence the Set

- [ ] E-01 CONFIRM 0bjke0 REACHED executed
  - Depends on: none
  - Expected outcome: 0bjke0 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-02 CONFIRM 34zv7d REACHED executed
  - Depends on: E-01
  - Expected outcome: 34zv7d reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-03 CONFIRM re15ol REACHED executed
  - Depends on: E-02
  - Expected outcome: re15ol reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-04 CONFIRM vvqr34 REACHED executed
  - Depends on: E-01
  - Expected outcome: vvqr34 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-05 CONFIRM hohlc6 REACHED executed
  - Depends on: E-03, E-04
  - Expected outcome: hohlc6 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-06 CONFIRM 7kczdo REACHED executed
  - Depends on: none
  - Expected outcome: 7kczdo reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Purpose | Depends on |
| --- | --- | --- | --- | --- |
| 01 | 0bjke0 | `.aw/records/plans/pending/20261006-runfresh-01-0bjke0-amend-the-run-spec-so-a-run-restarts-on-the-toolkit-code-its.ipd.md` | Amend spec `25kzda` (Section 5.3 and a new 5.3b) to require that a run whose integrated item changed the toolkit's own code restarts its driver on the current code before the next item, records it, and never loops; and that a finalize or retirement refusal records its lint findings. Edits the spec only. | none |
| 02 | 34zv7d | `.aw/records/plans/pending/20261006-runfresh-02-34zv7d-detect-when-an-integrated-item-changed-the-toolkit-code-the.ipd.md` | Record at run start which toolkit code the driver loaded (package root and a fingerprint of its `agent_workflows/**/*.py` files), and add one shared function that says whether that code on disk now differs, and how. Detection only; nothing restarts. | `executed:0bjke0` |
| 03 | re15ol | `.aw/records/plans/pending/20261006-runfresh-03-re15ol-restart-the-runner-on-the-current-code-between-items-and-res.ipd.md` | In both hosts' dispatch loops, between items, when Order 02 reports the code changed: save state, release the run lock, and replace the driver process with `<host> resume <run-id>` on the current code, carrying the original output options; record the restart; bound restarts per run; refuse to restart when the loaded code is not the checkout's own package. | `executed:34zv7d` |
| 04 | vvqr34 | `.aw/records/plans/pending/20261006-runfresh-04-vvqr34-record-the-findings-when-a-finalize-or-retirement-lint-refus.ipd.md` | Carry the post-transition (and pre-transition) lint findings into the finalize and retirement refusal text, the run's refusal record and `aw runs`, so a refusal names each finding code and message. | `executed:0bjke0` |
| 05 | hohlc6 | `.aw/records/plans/pending/20261006-runfresh-05-hohlc6-prove-a-run-that-changes-its-own-linter-retires-its-orchestr.ipd.md` | The Set's end-to-end measurement: a fixture run whose first child adds a metadata field the linter did not know and whose orchestrator carries that field, driven through the real runner on both hosts, proving the driver restarts, the orchestrator retires `executed`, and the old-code failure is reproduced with the restart disabled. | `executed:re15ol`, `executed:vvqr34` |
| 06 | 7kczdo | `.aw/records/plans/pending/20261006-runfresh-06-7kczdo-never-report-a-coverage-answer-as-recorded-when-it-was-not-w.ipd.md` | Make `aw ipd coverage` and the other checks that ask the model either save the coverage answer in the plan or report plainly that they did not (a finding, exit 1), instead of reporting "ready" while the answer was discarded because the plan had uncommitted changes. Found 2026-10-06 while recording this orchestrator's own answer. | none |

## Completion criteria (the whole Set is done only when)

1. A run whose integrated item changed any `agent_workflows/**/*.py` file in the checkout the driver runs from restarts its driver on the current code before dispatching the next item, and resumes the same run directory with the same queue, statuses, frozen options and session map. Owner: `re15ol` implements it; `hohlc6` measures it end to end.
2. Every restart is recorded in the run's events (old and new code fingerprints, the item that caused it, the restart count) and shown in the run summary. Owner: `re15ol`.
3. A run cannot restart forever: a restart is attempted only when the code actually differs from what the current process loaded, and a per-run limit stops the run with a named refusal if exceeded. Owner: `re15ol`.
4. A run started from a package that is not the checkout's own (for example an installed copy) never restarts and records once that it will not, because restarting would not pick up the checkout's code. Owner: `34zv7d` (classification), `re15ol` (behavior).
5. A finalize or retirement that refuses at a lint checkpoint records each finding's code and message in the refusal, the run state and `aw runs`. Owner: `vvqr34`.
6. The 2026-10-06 failure does not recur: a fixture reproducing it retires its orchestrator `executed` with the restart enabled, and fails as before with the restart disabled. Owner: `hohlc6`.
7. No command that asks the coverage question reports a plan ready while its answer was not written into the plan; the reason is printed and the exit code is 1. Owner: `7kczdo`.
8. The bare suite shows no new failing node id at any child boundary. Owner: each child for its own boundary; `hohlc6` for the final run.

## Cross-IPD validation

- ONE DETECTOR. Order 03 calls Order 02's function and no other comparison of code; checked by outcome in Order 05 (a fixture change to a non-Python file does not restart; a change to an `agent_workflows/*.py` file does).
- NO STATE IS LOST ACROSS A RESTART. Order 03's resume path is the existing `resume` command, which already reloads the run from `state.json`; Order 05 asserts the queue, every item's status and attempts, and the frozen options are byte-identical before and after the restart except for the new restart record.
- THE CHILD-PINNING CONTRACT IS PRESERVED. Nested `aw` calls stay pinned to the driver's own package (`runner_shared.pinned_child_env`, `assert_child_tool_identity`, spec `7ckptx` A8). After a restart the driver's own package is the current code, so the pin follows it; Order 03 must reset the per-process identity cache rather than weaken the check.
- EACH CHILD RE-MEASURES ITS OWN SUITE BASELINE.

## Deferred / out of scope (with reason)

- RESTARTING IN THE MIDDLE OF AN ITEM. A restart happens only between items, after state is saved. Mid-item restart would need every in-flight turn, lane and lock to survive a process replacement, which is a much larger change with no measured need.
  - Carrier-Declined: the measured failure happened between items (the retirement is its own dispatch step); between-item restart covers it
- DETECTING CHANGES TO NON-PYTHON FILES THE TOOLKIT READS (workflow markdown, templates, JSON schemas). Those are read from disk when used, not held in memory from start, so they are already current.
  - Carrier-Declined: measured: they are read per use, so they cannot be outdated in memory
- RE-RUNNING A STEP THAT ALREADY FAILED ON OLD CODE. A restart does not re-dispatch a finished item; an item that failed before the restart keeps its status, and `--retry-incomplete` remains the way to re-queue it.
  - Carrier-Declined: the existing retry path covers it, and automatic re-dispatch of a finished item is the defect `rl67b0` fixed
- RESUMING THE HELD APPROVED PLANS. They restart after this Set executes, by the maintainer.
  - Carrier-Declined: maintainer decision 2026-10-06

## Scope check

- Over-scope: none. `- Scope-Paths:` lists only the five child plans.
- Under-scope: nothing is parked on this plan. The end-to-end proof is Order 05.
- IF A REVIEWER FINDS UNCOVERED WORK, the remedy is to ADD A CHILD and a row to the table, not to add an item here and not to delete the checklist.

## Required tests / validation

This plan runs no tests of its own. Each child validates itself; the Set-level proof is Order 05 (`hohlc6`), which drives the real runner on both hosts over a fixture that reproduces the 2026-10-06 failure, with the restart enabled and disabled, and runs the bare suite.

## Open questions

### OQ-01: Should this Set be run with itself, given that it changes the runner?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes, and the risk is bounded. The defect this Set fixes only bites a step that reads code changed earlier in the same run. Orders 02 to 05 each change runner code, but no later child's success depends on the DRIVER using those changes: each child's own validation runs in its lane as a fresh process. The one step that does read changed code is the final orchestrator retirement, which reads only metadata fields this Set does not add. If the retirement still refuses, the hand resume (`aw ipd finalize 67lvds ... --apply`) runs on current code and completes it, exactly as it did for `1f4faf`.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n '^- Status:' <0bjke0 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n '^- Status:' <34zv7d plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -n '^- Status:' <re15ol plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n '^- Status:' <vvqr34 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n '^- Status:' <hohlc6 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -n '^- Status:' <7kczdo plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It performs no work itself: under `aw oc run` / `aw agy run` the runner retires it once every child is `executed`; run by hand, the executor confirms each child in order and stops at the first that did not reach `executed`. The terminal transition is owned by the runner under a runner and by `aw ipd finalize` by hand; never hand-edit `- Status: executed` and never `git mv` it. Paste actual output for every `V-*`; commit only declared paths through `aw commit`; never push.

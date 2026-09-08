# IPD: Distinguish not-ready-yet from can-never-be-ready so a transiently blocked item is retried instead of parked forever

- Date: 2026-09-08
- Kind: child
- Concern: ONE status carries two incompatible facts, "not ready yet" and "can never be ready", and the runner treats both as the second. TWO PARTS, both re-verified at HEAD `a2e0438a` by importing the module rather than reading it.
  PART 1, BLOCKED IS TERMINAL. `dependency-blocked` is a member of `TERMINAL_STATES` (`oc_runipd.py:308-326`, measured `'dependency-blocked' in TERMINAL_STATES` -> `True`). The selection filter admits only `queued`, so once the label is written the item is never considered again, and `cascade_dependency_blocked` only ever moves `queued -> dependency-blocked`, never back.
  PART 2, ALL-OR-NOTHING BREAK. When NO queued item is satisfiable, the drain-time branch marks EVERY remaining queued item `dependency-blocked` and BREAKS out of the run (the `if runnable is None:` arm inside `run_queue`, `oc_runipd.py:7123-7157`). So a single unsatisfiable node does not park one item; it can END a run that still holds runnable work. The runner's own comment says exactly this.
  WHAT WORKS TODAY, so it is not mistaken for broken: an item merely SKIPPED by the inner selection pass writes no status and IS re-examined next iteration. Ordering is correct right up until something is LABELLED. The bug is the labelling, not the scheduling.
  MEASURED, AND THE MEASUREMENT IS STRONGER THAN THE ITEM RECORDED. Run `run-20260905T050043Z-639569`: `6ypimw` blocked on `executed:76gsmv (target integration-blocked)`, `wpomxa` blocked on `executed:eyh1fu (target integration-blocked)`, and `5slbpi` blocked on `executed:6ypimw (target dependency-blocked)`. That third one is a CASCADE OF A CASCADE: `5slbpi` died because its prerequisite had itself been labelled, not because anything about `5slbpi` was unsatisfiable. All three prerequisites (`76gsmv`, `eyh1fu`, `6ypimw`) now read `executed` on disk, so every one of the three was killed by a condition that has since cleared, and none will ever be retried by the runner.
  RECOVERY IS MANUAL AND FLAG-SPECIFIC. A bare `resume` does NOT re-queue a dependency-blocked item; only `resume --retry-incomplete` does (the `if retry_incomplete:` branch in `run_queue`, `oc_runipd.py:7012`). The runner states this honestly in `DEPENDENCY_BLOCK_RECOVERY_HINT` (`:337-340`) and surfaces it in the event payload and report, which is good, but an unattended run that hits this stops making progress until a human intervenes with a specific flag.
- Scope: Split the two facts the single status conflates, so a prerequisite in a NON-TERMINAL state means wait-and-re-test while only a prerequisite in a non-success TERMINAL state warrants the terminal label and the cascade; and stop the drain-time path labelling every remaining item at once when the cause is transient. EXCLUDES the integration-deferral ladder and the re-integrate verb (backlog `5wdoze`/`yocdq4`, pending plans `51vw4y`/`rl67b0`), which fix the COMMON CAUSE rather than this design defect; excludes changing the `--retry-incomplete` re-queue default, which executed plan `7nkcgp` deliberately preserved; excludes the deferred-orchestrator dead end, filed separately.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_runner_item_dependencies.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: depblock
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: akzy45
- From-Backlog: nueip1

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nueip1`. The item carries no `- Blocks-Release:` so none is inherited or invented.
  EVERY CLAIM RE-VERIFIED at HEAD `a2e0438a` and all held, but EVERY LINE NUMBER HAD DRIFTED, most by roughly 1300 to 3400 lines: the item cites `TERMINAL_STATES` at `:249` (actual `:308-326`), `cascade_dependency_blocked` at `:3661` (actual `:4177`), the selection filter at `:5812`, the drain branch at `:5847-5881` (actual `:7123-7157`), the recovery hint at `:279-283` (actual `:337-340`), and the re-queue branch at `:5745-5758` (actual `:7012`). I re-located every one by symbol; the SUBSTANCE was correct at each new coordinate.
  THE MEASURED INCIDENT IS STRONGER THAN THE ITEM SAID, which I found by reading that run's `state.json` rather than trusting the summary: the item names three blocked plans, and one of them (`5slbpi`) was blocked on `executed:6ypimw (target dependency-blocked)`, meaning it was killed by a SIBLING'S LABEL rather than by any real unsatisfiability. That is the cascade-of-a-cascade case and it is the most persuasive evidence for the split, because no amount of fixing the root cause prevents it: any future terminal label propagates the same way. All three prerequisites now read `executed`, confirming the condition was transient.
  THIS IS A DELIBERATE DESIGN CHANGE, NOT A BUG FIX NOBODY CONSIDERED, and the plan says so because the item does. Executed plan `7nkcgp` is the authoritative record: its review corrected a false draft claim that recovery was free on resume, established the re-queue semantics with citations, and then EXPLICITLY PRESERVED the behavior ("Do NOT change the re-queue default in this plan"). So changing it needs a stated rationale, which is why E-01 is a classification item and OQ-01 escalates the operator-visible half.
  THE INTERACTION WITH `51vw4y` IS THE STRONGEST ARGUMENT FOR SEQUENCING THIS SOON, and I verified it in that plan's text rather than inferring it: `51vw4y` (from `5wdoze`, `to-review`) adds a NON-TERMINAL `integration-deferred` status and its E-01 states that keeping it out of `TERMINAL_STATES` "is therefore exactly what stops the cascade from killing dependents". So that plan already depends on the distinction this item describes being honored, and it names `cascade_dependency_blocked` as the site. This plan must NOT re-implement that (it is that plan's E-01) and must not conflict with it; the fence and OQ-02 record the boundary.

## Goal

Stop the runner writing a permanent label on an item whose prerequisite is merely not finished yet, and stop one unsatisfiable node ending a run that still holds work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: name the distinction before changing behavior

- [ ] E-01 CLASSIFY EVERY REASON THE RUNNER CURRENTLY WRITES `dependency-blocked`, and record for each whether the cause is TRANSIENT (the prerequisite may still finish, or finished later in this run, or can be made to finish) or PERMANENT (the prerequisite reached a non-success terminal state, or the graph is structurally invalid). Locate the write sites by SYMBOL; there are at least two (`cascade_dependency_blocked` and the drain-time `if runnable is None:` arm inside `run_queue`) plus the orchestrator dispatch path.
  THE CONCEPT ALREADY EXISTS IN ONE PLACE AND IS THE MODEL TO FOLLOW. `cascade_dependency_blocked` already reasons in exactly these terms: it kills a dependent only when the prerequisite's status is `in TERMINAL_STATES and st not in required` (`oc_runipd.py:4221`), where `required` is action-aware. That is the PERMANENT case, correctly identified. The drain-time path has no such test and flattens the distinction by labelling everything at once.
  DO NOT INVENT A NEW STATUS IN THIS ITEM. Whether a second status is needed is OQ-01 and it is an operator-visible vocabulary change; the classification is what makes that decision answerable. Note `51vw4y` is separately adding `integration-deferred` as a NON-TERMINAL status, so a second new status here risks two overlapping vocabularies for one idea.
  RECORD THE ANSWER WHERE THE NEXT READER WILL FIND IT, at the `TERMINAL_STATES` definition and at each write site, because the whole defect is that one label means two things and nothing says so at the point of writing.
  - Depends on: none
  - Expected outcome: every `dependency-blocked` write site classified transient or permanent with its reason recorded in the code; no new status introduced; the existing action-aware test in `cascade_dependency_blocked` identified as the correct model.
  - Execution state: pending

### Task group 2: stop the drain-time path over-labelling

- [ ] E-02 MAKE THE DRAIN-TIME PATH LABEL ONLY WHAT IS PERMANENTLY BLOCKED, applying E-01's classification. Today the `if runnable is None:` arm labels EVERY remaining queued item and breaks; after this, an item whose prerequisites are merely unfinished must NOT receive a terminal label.
  THE WIND-DOWN BRANCH IS THE PRECEDENT AND MUST NOT BE DISTURBED. Immediately above the labelling loop, the same arm already declines to relabel the remainder during a deliberate stop, with the recorded reason that items of another set are `queued` because the OPERATOR asked to stop, "not because their dependencies are unmet, and rewriting their status would be exactly the fabricated disposition spec R22 forbids". That is the identical argument this plan applies to the transient case, so follow its shape rather than inventing one, and leave the wind-down path byte-unchanged.
  DECIDE WHAT THE RUN DOES WHEN NOTHING IS RUNNABLE AND NOTHING IS PERMANENTLY DEAD, and this is the substantive question inside E-02. If the remainder is left `queued` and the loop breaks, the run ends with runnable-looking work outstanding, which is honest but must be REPORTED as such rather than looking like a clean finish. If the loop instead waits, that is a scheduling change with a hang risk and needs a bound. State the choice and its reason; do not leave the run silently exiting 0 over unlabelled work.
  DO NOT REMOVE THE RECOVERY HINT. `DEPENDENCY_BLOCK_RECOVERY_HINT` is written into the item, the event payload and the report, and it is the one thing that makes today's dead end discoverable. Whatever replaces the blanket label must be at least as informative.
  - Depends on: E-01
  - Expected outcome: the drain-time path labels only permanently-blocked items; the wind-down branch is byte-unchanged; the nothing-runnable-nothing-dead case has a stated, reported behavior rather than a silent exit; the recovery hint survives or is superseded by something at least as informative.
  - Execution state: pending

- [ ] E-03 MAKE A TRANSIENTLY BLOCKED ITEM RE-TESTABLE WITHIN THE SAME RUN, which is the "blocked is forever" half. An item whose prerequisite completed LATER IN THE SAME RUN must become runnable again without a human passing `--retry-incomplete`.
  THIS IS THE CASE THE MEASUREMENT PROVES, so build the fix against it: in run `run-20260905T050043Z-639569`, `5slbpi` was blocked on `executed:6ypimw (target dependency-blocked)`, i.e. on a sibling's LABEL rather than on any real condition. Even a perfect root-cause fix elsewhere does not prevent that shape, because any future terminal label propagates identically.
  DO NOT CHANGE THE `--retry-incomplete` DEFAULT. Executed plan `7nkcgp` deliberately preserved it and its review recorded the citations; changing it is a separate decision. The fix here is that a TRANSIENTLY blocked item should never have needed the flag, not that the flag's semantics change.
  BEWARE THE SPIN HAZARD, which this repository has already measured in an adjacent path: the orchestrator dispatch comment records that "just leave it queued" fixes only one of two failure modes, and that leaving a STRUCTURAL refusal reconsiderable "would retry a structural refusal every iteration and SPIN". Whatever re-test mechanism you add must be bounded or must only apply to the transient classification, and E-01 is what makes that distinction available.
  - Depends on: E-02
  - Expected outcome: an item blocked on a prerequisite that later succeeds in the same run becomes runnable without `--retry-incomplete`; the flag's default is unchanged; a structural refusal does not spin, demonstrated rather than argued.
  - Execution state: pending

### Task group 3: both hosts, and prove it

- [ ] E-04 APPLY THE CHANGE TO BOTH HOSTS THROUGH ONE IMPLEMENTATION. `agy_runipd` imports `cascade_dependency_blocked` and the dependency evaluators FROM `oc_runipd` (measured: 47 names flow oc-to-agy, zero the other way), so the cascade is already ONE implementation. The drain-time path is NOT: each driver has its own `run_queue`.
  PUT ANY NEW SHARED PREDICATE IN `runner_shared.py`, NEVER IN `oc_runipd` FOR AGY TO IMPORT. Adding to that import list would make it 48 and deepen the layering defect backlog `cnwy8g` owns (whose graduated plans `9kmbr0`/`1f7xno` are re-homing exactly these names). Note `7nkcgp`'s review already caught this trap once: its F-11 records that a proposed shared-predicate home "would have created the first runner-to-runner import".
  EXTEND THE EXISTING CROSS-DRIVER GUARD RATHER THAN REPLACING IT. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` already asserts presence AND object identity for eleven of these names, including `cascade_dependency_blocked` and `dependency_status`, and its `_SHARED_NAMES` tuple is where a new shared symbol is registered.
  - Depends on: E-03
  - Expected outcome: one implementation of the new logic, sited in `runner_shared`; both drivers' drain paths behave identically; the symmetry guard extended with any new symbol; the AST-measured oc-to-agy import count not increased.
  - Execution state: pending

- [ ] E-05 REPRODUCE THE MEASURED INCIDENT AS A TEST, all three shapes, from FIXTURES. The three cases are distinct and the third is the one no root-cause fix covers: (a) a dependent whose prerequisite ended in a non-success TERMINAL state must still be labelled and cascaded, unchanged; (b) a dependent whose prerequisite is merely UNFINISHED must NOT be labelled; (c) a dependent blocked on a SIBLING'S LABEL (`5slbpi` on `executed:6ypimw (target dependency-blocked)`) must not die when that sibling was itself only transiently blocked.
  CASE (a) IS THE ANTI-OVER-SUPPRESSION GUARD and is as important as the fix: a genuinely dead prerequisite must still kill its dependents, or the runner stalls forever waiting on something that will never happen. If one change makes (a) and (b) both pass or both fail, the classification is wrong.
  DO NOT READ `.aw/records/runs/`. It is gitignored and roughly 32 tests fail inside a lane worktree because several read live run state. Build synthetic queue states; the incident's shape is fully described by three items and their `unsatisfied_dependencies` values.
  - Depends on: E-04
  - Expected outcome: three fixture-driven cases per host, (a) still cascading, (b) and (c) no longer labelled; no test reads the gitignored runs tree.
  - Execution state: pending

- [ ] E-06 MUTATION-CHECK BOTH DIRECTIONS, because this fix's risk is symmetric. Revert E-02/E-03 and show cases (b) and (c) FAIL, then restore. Then over-relax deliberately, by treating a non-success TERMINAL prerequisite as transient, and show case (a) FAILS and the run does not stall. Restore.
  THE SECOND MUTATION IS THE LOAD-BEARING ONE: over-relaxation is the failure mode that turns a clean dead-end into an infinite wait, and it is the risk `7nkcgp` was protecting against when it preserved the behavior.
  - Depends on: E-05
  - Expected outcome: two mutations, each failing the case it should, each passing after revert, all outputs pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE DISTINCTION ALREADY EXISTS IN ONE FUNCTION. `cascade_dependency_blocked` kills a dependent only when the prerequisite is `in TERMINAL_STATES and st not in required`, with `required` action-aware (`EXECUTION_SUCCESS_STATES` for execute, `SUCCESS_STATES` for review). That is the model; the drain-time path lacks it.
- THE WIND-DOWN BRANCH ALREADY MAKES THIS EXACT ARGUMENT. The same drain arm declines to relabel the remainder during a deliberate stop because those items are `queued` by operator choice and "rewriting their status would be exactly the fabricated disposition spec R22 forbids". Follow that shape.
- CHANGING THE RE-QUEUE DEFAULT IS FORBIDDEN BY A PRIOR PLAN'S DECISION. Executed plan `7nkcgp` established the semantics with citations and explicitly preserved them ("Do NOT change the re-queue default in this plan"), and its review corrected a false claim that recovery was free on resume.
- "JUST LEAVE IT QUEUED" IS A MEASURED HALF-FIX. The orchestrator dispatch comment records that it addresses only one of two failure modes and that leaving a structural refusal reconsiderable would "retry a structural refusal every iteration and SPIN". Hence three outcomes there, and hence the bound E-03 needs.
- A SIBLING PLAN ALREADY DEPENDS ON THIS DISTINCTION. `51vw4y` (from `5wdoze`, `to-review`) adds a NON-TERMINAL `integration-deferred` and its E-01 states that keeping it out of `TERMINAL_STATES` "is exactly what stops the cascade from killing dependents", naming `cascade_dependency_blocked`. Do not re-implement its status; do not conflict with it.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`, zero flow back, and `7nkcgp` F-11 already caught a proposal that would have created the first reverse import. Shared symbols go in `runner_shared`.
- `.aw/records/runs/` IS GITIGNORED; roughly 32 tests fail in a lane worktree because several read live run state. Use fixtures.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `oc_runipd.py:308-326` | `dependency-blocked` is in `TERMINAL_STATES`, the selection filter admits only `queued`, and the cascade only moves `queued -> dependency-blocked`. Once labelled, never revisited. | `'dependency-blocked' in TERMINAL_STATES` -> `True`; source read |
| F-2 | MED | `oc_runipd.py:7123-7157` | The drain-time `if runnable is None:` arm labels EVERY remaining queued item and BREAKS, so one unsatisfiable node can end a run holding runnable work. | source read; the runner's own comment says so |
| F-3 | HIGH | run `run-20260905T050043Z-639569` | THE CASCADE-OF-A-CASCADE CASE, which the item did not name: `5slbpi` was blocked on `executed:6ypimw (target dependency-blocked)`, i.e. on a SIBLING'S LABEL. No root-cause fix elsewhere prevents that shape. | read that run's `state.json`: three blocked items with their `unsatisfied_dependencies` |
| F-4 | MED | same run | All three prerequisites (`76gsmv`, `eyh1fu`, `6ypimw`) now read `executed`, so all three dependents were killed by a condition that has since cleared and none will be retried. | run state plus the plans tree |
| F-5 | MED | `oc_runipd.py:4221` | The PERMANENT case is already correctly identified in `cascade_dependency_blocked` by an action-aware `TERMINAL_STATES` test. The concept exists; the drain path lacks it. | source read |
| F-6 | MED | `oc_runipd.py:7012`, `:337-340` | Re-queue happens only under `if retry_incomplete:`, so a bare `resume` leaves the item blocked; the runner documents this honestly in the recovery hint and surfaces it in the payload and report. | source read |
| F-7 | LOW | backlog `nueip1` | EVERY line number in the item had drifted, by roughly 1300 to 3400 lines. The substance re-verified correct at each new coordinate. | re-located all six citations by symbol |
| F-8 | MED | executed plan `7nkcgp` | This behavior is DOCUMENTED AND DELIBERATE as of that plan, which preserved the re-queue default on purpose after its review corrected a false claim. So this is a design change needing a rationale, not an unnoticed bug. | that plan's review record and its E-item instruction |
| F-9 | MED | pending plan `51vw4y` E-01 | A sibling plan already DEPENDS on this distinction: it adds a non-terminal `integration-deferred` and states that keeping it out of `TERMINAL_STATES` is what stops the cascade killing dependents. Two overlapping new statuses would be a real hazard. | that plan's E-01 text |
| F-10 | MED | orchestrator dispatch comment | "Just leave it queued" is a measured HALF-fix that would spin on a structural refusal, which is why E-03 needs a bound or a strict transient-only scope. | source read |

## Proposed changes (ordered, validatable)

1. E-01 classifies every `dependency-blocked` write site transient or permanent and records it at the definition and each site.
2. E-02 makes the drain-time path label only the permanent cases, leaving the wind-down branch untouched and giving the nothing-runnable-nothing-dead case a stated reported behavior.
3. E-03 makes a transiently blocked item re-testable in the same run without `--retry-incomplete`, bounded so a structural refusal cannot spin.
4. E-04 lands it on both hosts through one shared predicate in `runner_shared`, extending the existing symmetry guard.
5. E-05 reproduces all three incident shapes from fixtures, including the anti-over-suppression case.
6. E-06 mutation-checks under-fixing and over-relaxing.

## Deferred / out of scope (with reason)

- THE INTEGRATION-DEFERRAL LADDER AND THE RE-INTEGRATE VERB. Backlog `5wdoze`/`yocdq4`, pending plans `51vw4y`/`rl67b0`. They fix the COMMON CAUSE of the blocking in the measured run: if prerequisites integrate instead of stranding, these dependents never block. That is the bulk of the practical harm and it is owned elsewhere. THIS plan is the design defect that survives those fixes, and F-3's cascade-of-a-cascade is the proof: a sibling's label propagates regardless of why the sibling was labelled. The item states plainly "Do not close this item by pointing at those two".
- ADDING A NEW STATUS. OQ-01. Not done here: `51vw4y` is already adding a non-terminal `integration-deferred`, and a second new status for the same idea would be two vocabularies. E-01's classification is what makes the decision answerable later.
- CHANGING THE `--retry-incomplete` RE-QUEUE DEFAULT. Executed plan `7nkcgp` preserved it deliberately after its review established the semantics. A transiently blocked item should never have needed the flag; that is different from changing what the flag does.
- THE DEFERRED-ORCHESTRATOR DEAD END. Filed separately per the item; the orchestrator dispatch path already got its own three-outcome fix (`pgq326`), so re-deciding it here would collide.
- THE ORCHESTRATOR DISPATCH PATH ITSELF. It already has a deliberate three-way outcome and a recorded reason why "leave it queued" was insufficient there. E-01 CLASSIFIES it for completeness but E-02 and E-03 do not change it.

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY to hold a new shared predicate. Do NOT change `TERMINAL_STATES`' membership for any existing value, do NOT touch the wind-down branch, do NOT change `--retry-incomplete`, and do NOT add `integration-deferred` (that is `51vw4y`).
- Under-scope: stated rather than left as `none`. After this plan a genuinely dead prerequisite still ends its dependents' hopes (correctly), and the operator-visible vocabulary is unchanged, so `aw runs` still shows one `dependency-blocked` label for what are now two internally distinct cases unless OQ-01 is answered affirmatively.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. `tests/test_runner_item_dependencies.py` holds the dependency semantics and the cross-driver symmetry guard and is the primary home. Build synthetic queue states; never read `.aw/records/runs/`. Note `tests/test_runner_shared.py::WrapperTests` counts per-runner call sites deliberately, so if the wiring changes a counted site, reflect it rather than working around it.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) GOVERNS THIS DIRECTLY and must be read before execution, because it may already mandate the behavior this plan adds. Its §4.3 `IPD-DEP-CASCADE` row and the propagation text beneath it describe cascade semantics in terms of a node ending "failed, needs_input, or a terminal/gated skip that does not satisfy its outgoing requirement", and state that "On a later explicit resume, the engine re-evaluates every dependency-not-met item. A now-satisfied chain may return to `planned`".
TWO THINGS TO DETERMINE AND REPORT. FIRST, whether that re-evaluation text makes this plan a COMPLIANCE fix (the spec already requires re-evaluation and the runner does not do it without a flag), in which case no amendment is needed and that is the justification to record. SECOND, whether the spec's vocabulary (`dependency_not_met`, `planned`) conflicts with the runner's (`dependency-blocked`, `queued`), which the runner has deliberately not adopted before: `cascade_dependency_blocked`'s docstring states it uses the EXISTING `dependency-blocked` disposition and does NOT introduce `dependency-not-met`, "which is the spec's vocabulary but does not exist anywhere in this runner", because "inventing a parallel state would split the run records already on disk". Respect that decision; if OQ-01 leads to a new status, it must not casually adopt the spec's spelling without reconciling that recorded reasoning.
If an amendment IS required, add the spec file to `- Scope-Paths:` before execution, since the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the transient case need its own operator-visible status, or only different internal handling?

- Blocking: no
- Status: open
- Owner: this plan's executor for the recommendation, the maintainer for the vocabulary decision
- Resolution or deferral rationale: NOT blocking, because the defect is fixable with internal handling alone: the drain path can decline to label a transiently blocked item and leave it `queued`, which requires no new status and no operator-facing change. The question is whether a reader of `aw runs` should be able to SEE the difference. Arguments measured rather than assumed: `cascade_dependency_blocked`'s docstring explicitly declined to add `dependency-not-met` because "inventing a parallel state would split the run records already on disk"; `51vw4y` is concurrently adding a non-terminal `integration-deferred`, so a second new status risks two vocabularies for one idea; and against that, leaving both cases labelled identically means the run record cannot distinguish "waited and the run ended" from "genuinely dead". Recommend internal-handling-only in this plan, with the classification recorded so a later plan can add the status once `51vw4y` has landed and its vocabulary is known.

### OQ-02: What is the exact boundary with `51vw4y`, and which lands first?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer for the sequencing
- Resolution or deferral rationale: NOT blocking, because the two changes are compatible in either order and E-01 requires reading that plan's status on disk at execution time. The boundary as authored: `51vw4y` E-01 adds `integration-deferred` and keeps it OUT of `TERMINAL_STATES`, relying on `cascade_dependency_blocked`'s existing terminal test to stop the cascade; this plan changes the DRAIN-TIME path, which `51vw4y` does not touch. So they are complementary and this plan's fix makes that plan's reliance sound rather than incidental. The real risk is both plans editing `TERMINAL_STATES`-adjacent logic concurrently, and the runner isolates each item in its own worktree, so the coordination question is which merges first rather than whether they conflict semantically. Read its status and record it.

### OQ-03: When nothing is runnable and nothing is permanently dead, does the run wait or exit?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires the choice be made and REPORTED either way, and both answers fix the measured defect (neither leaves a permanent label on a transiently blocked item). It is recorded because the two answers have different risks: EXITING with the remainder left `queued` is honest and terminates, but ends a run with work outstanding, so the summary must say so plainly rather than looking like a clean finish. WAITING keeps the run alive until a prerequisite completes, but nothing else in the run can complete it if no item is runnable, so an unbounded wait is a hang. Since the transient case that matters most is a prerequisite finishing LATER IN THE SAME RUN (which implies something WAS runnable), the exit-and-report answer is probably correct and the waiting case is nearly vacuous. Verify that reasoning against the loop rather than accepting it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classification as recorded, listing every `dependency-blocked` write site with its transient/permanent verdict and reason, located by symbol with the line number AT YOUR HEAD (it will not match this plan). Paste the recorded note at the `TERMINAL_STATES` definition. Confirm no new status was introduced (grep for any added status literal, returning nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the changed drain-time arm. Paste a diff proving the WIND-DOWN branch above it is BYTE-UNCHANGED. Paste a run whose only unsatisfiable node is transient, showing the remainder is NOT labelled. State the OQ-03 answer and paste the reported output for the nothing-runnable-nothing-dead case, showing it does not look like a clean finish. Paste the recovery hint or its replacement.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a synthetic run in which a dependent is blocked while its prerequisite is unfinished, the prerequisite then SUCCEEDS in the same run, and the dependent becomes runnable WITHOUT `--retry-incomplete`, with the actual queue states before and after. Paste proof the `--retry-incomplete` default is unchanged. Paste the SPIN test: a structural refusal must not be retried every iteration; show the bound or the transient-only scope that prevents it, and paste the iteration count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `python3 -c` showing any new shared symbol resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47. Paste both drivers' drain paths behaving identically on the same fixture. Paste the extended `_SHARED_NAMES` and `CrossDriverSymmetryTests` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste all three cases per host with actual runner output. Case (a) MUST still cascade: paste it, since it is the anti-over-suppression guard. Case (c) must reproduce the `5slbpi on executed:6ypimw (target dependency-blocked)` shape specifically, because that is the one no root-cause fix covers. Paste cases (a) and (b) side by side showing they differ only in the prerequisite's terminality and reach opposite verdicts. Paste proof no test reads `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste BOTH mutations in full. Mutation 1: revert E-02/E-03, paste cases (b) and (c) FAILING, restore, paste passing. Mutation 2: treat a non-success terminal prerequisite as transient, paste case (a) FAILING and show the run does not stall waiting forever, restore, paste passing. Mutation 2 is load-bearing: over-relaxation converts a clean dead end into an infinite wait, which is what `7nkcgp` was protecting against.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT add `integration-deferred` or any new status (OQ-01; `51vw4y` owns that one). Do NOT change `TERMINAL_STATES`' membership for any existing value. Do NOT touch the wind-down branch. Do NOT change the `--retry-incomplete` default (`7nkcgp` preserved it deliberately). Do NOT change the orchestrator dispatch path's three-way outcome. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT read `.aw/records/runs/` from a test. Do NOT edit spec `25kzda` unless the spec-sync reading requires it, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Every citation in the backlog item had drifted by 1300 to 3400 lines (F-7), and both drivers are the highest-contention files in this repository, edited by live runs. Find `TERMINAL_STATES`, `cascade_dependency_blocked`, `dependency_status_detailed`, `run_queue`'s `if runnable is None:` arm, `DEPENDENCY_BLOCK_RECOVERY_HINT`, and the `if retry_incomplete:` branch by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index and several pending Sets are editing these same two drivers. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved akzy45 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `nueip1`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited. If OQ-01 resolves that an operator-visible status IS required and is deferred to a follow-on, set the item `graduated` rather than `done` and file the follow-on, so the surviving half is not dropped.

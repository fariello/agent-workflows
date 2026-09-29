# IPD: Narrow the broad suppress(Exception) blocks in execute_item_core so a signature drift fails loudly instead of degrading a record

- Date: 2026-09-28
- Kind: child
- Concern: `runner_shared.execute_item_core` wraps seven best-effort calls in a blanket `contextlib.suppress(Exception)`. A blanket suppress cannot distinguish the failure it ANTICIPATES (an unreachable lane, a missing file) from a failure that means the CODE IS WRONG (a signature drift, a `None` where an object was required), so it converts the second into silence. That is not hypothetical here: it is the mechanism of backlog `cv5n6t`, where `build_lane_outcome` was called without its keyword-only `run_checked`, raised `TypeError` on EVERY integration refusal, and the suppress ate it whole, so `integration_changed_files` was never recorded. Plan `h5pyqa` fixed THAT CALL by binding the host wrapper; it did not remove the hazard that hid it for as long as it existed. `cv5n6t` is the SECOND measured "swallowed exception hid a broken read" defect in this seam (`he9x6j` is the first, still open), which is why the item asks for the audit rather than treating the one call as closed.
- Scope: IN: the seven `contextlib.suppress(Exception)` blocks inside `execute_item_core` (`runner_shared.py`), each narrowed to the exception class it actually anticipates, so a programming error surfaces instead of degrading a record; a guard on the `build_lane_outcome` refusal call for the `wt_handle is None` case its own neighbouring line already treats as reachable; and behavioral regression tests that FAIL when a narrowed block is widened back to `Exception`. OUT: the two blocks already correctly narrowed to `(DriverError, OSError)`; every `suppress` OUTSIDE `execute_item_core` (including the deliberately-silent ones inside `SuiteBaselineRun.collect`/`abandon`, whose "NEVER raises" contract is load-bearing for the `finally` arm); any change to what the runner DECIDES on a refusal; and the separate defect `he9x6j`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_suppress_narrowing.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: cv5n6t
- Blocks-Release: next
- Set: suppressnarrow
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8o709f

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `cv5n6t`. All seven in-scope suppress sites enumerated and each callee's real exception surface derived by reading it; both live failure modes of the `cv5n6t` call site reproduced by execution; the false-`cleared` consequence of the empty field measured.

## Goal

Make every best-effort block in `execute_item_core` suppress only what it anticipates, so that a signature drift or a `None`-where-an-object-was-required FAILS LOUDLY instead of silently degrading a durable record. The one-line repair in `h5pyqa` proved the call site; this plan removes the blindfold that let it stay broken, and pins the narrowing with tests that go red if it is widened back.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the call site the item was filed from

- [ ] E-01 Narrow the integration-refusal block (the `item["integration_changed_files"] = list(build_lane_outcome(...).changed_files)` call in `execute_item_core`, in the `if not integrated:` arm right after `_record_lane_ending_facts`) from `suppress(Exception)` to `suppress(DriverError)`, which is the ONLY failure it anticipates: `build_lane_outcome`'s three `run_checked` calls raise `DriverError` on a failed `git rev-parse`/`git diff`, and its own docstring says so ("that would stop them raising `DriverError`"). A `TypeError` or `AttributeError` from this line means the CODE is wrong and must propagate.
  - Depends on: none
  - Expected outcome: a `git rev-parse` failure on an unreachable lane still degrades quietly to no recorded file list, while the exact `TypeError: build_lane_outcome() missing 1 required keyword-only argument: 'run_checked'` that `cv5n6t` measured now escapes instead of being eaten.
  - Execution state: pending

- [ ] E-02 Guard the same call for `wt_handle is None` rather than relying on suppression to absorb it. The NEXT statement in the same arm already reads `branch=wt_handle.branch if wt_handle else None`, so this arm demonstrably runs with `wt_handle=None`, and on that path `build_lane_outcome` raises `AttributeError: 'NoneType' object has no attribute 'base_commit'` before reaching any git call. Without the guard, E-01's narrowing would turn a REACHABLE state into a crash. Record nothing (leave the field unwritten) when there is no lane, since a non-isolated turn has no lane base to diff.
  - Depends on: E-01
  - Expected outcome: the `None` path is handled by an explicit condition that a reader can see, not by an exception handler that also hides real bugs; E-01's narrowing is then safe on every reachable path.
  - Execution state: pending

### Task group 2: the remaining five blocks

- [ ] E-03 Narrow the two `queue_artifact_path` blocks in the review arms (the `if queue_entry_type(item) != "ipd":` blocks that append to `extra_allowed`, one in the `wt_handle`-bearing arm using `wt_handle.path` and one in the `elif is_review and wt_handle is None:` arm using `repo`) to `suppress(DriverError, ValueError)`. Derived by reading the callees: `queue_artifact_path` raises `DriverError` for an unfound spec, an unfound backlog item, and an unsupported `artifact_type`; the following `Path.relative_to` raises `ValueError` when the artifact lies outside the given root. Nothing else there is anticipated.
  - Depends on: none
  - Expected outcome: a genuinely missing artifact still degrades to an un-widened allow-list, while a typo or a signature change in either call surfaces.
  - Execution state: pending

- [ ] E-04 Narrow the `collect_lane_submissions` block (the `if work_dir:` block in the merge-conflict arm) to `suppress(OSError)`. `lane_containment.collect_lane_submissions` contains NO `try`/`except` and raises no `DriverError`; its per-file helper `_collect_one` already absorbs `OSError` itself and reports `failed` with a reason, so what can still escape the outer call is an `OSError` from the receipt writes (`_atomic_write_text`) and directory creation. Leave the `except (KeyboardInterrupt, StallTimeout)` immediately above untouched: that is control flow, not error suppression.
  - Depends on: none
  - Expected outcome: a full disk or permission fault during collection still cannot fail the turn, while an `AssertionError` from the module's own `assert paths.lane_decisions is not None`, or a keyword drift in this six-argument keyword-only call, is no longer invisible.
  - Execution state: pending

- [ ] E-05 Narrow the suite-baseline collection block (`suite_baseline = suite_baseline_run.collect(wait_seconds=0.0)`) to the tightest form its own contract permits, and record in a comment WHY the surrounding block is kept at all. `SuiteBaselineRun.collect`'s docstring says "NEVER raises and NEVER waits unboundedly" and its body already suppresses internally, so this block is a second belt over a callee that promises nothing escapes; narrow it to `suppress(OSError)` and keep it, because the alternative (removing it) would make a broken promise fail a turn that a missing baseline is explicitly not allowed to fail. Do NOT touch the two blocks in the `finally` arm (`abandon`, `remove_suite_baseline_checkout`): a raise there would REPLACE the exception the turn is already carrying, including a deliberate stop, which the existing comment states and which is a correctness requirement, not an oversight.
  - Depends on: none
  - Expected outcome: a keyword drift in `collect(wait_seconds=...)` surfaces, the documented "missing baseline is not a failed item" rule is preserved, and the `finally` arm's deliberate blanket suppression is left intact with the reason it must stay.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-06 Add `tests/test_suppress_narrowing.py` with behavioral tests that exercise the narrowed arms rather than inspecting source text (no `inspect`/`ast`/regex over production code, per GUIDING_PRINCIPLES P16 and the AGENTS.md outcomes rule). Drive `execute_item_core`'s refusal arm with a `build_lane_outcome` stub that raises `TypeError` and assert the call PROPAGATES (the `cv5n6t` regression); with a stub raising `DriverError` and assert it degrades quietly and the item records no file list; with a working stub and assert `integration_changed_files` is actually written; and with `wt_handle=None` and assert no crash and no field. Follow the calling-convention-guard style of `tests/test_lane_reaper_callshape.py`, whose spy asserts the real call shape by accepting only what the product is supposed to pass.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: a test file that goes RED if any narrowed block is widened back to `Exception`, and RED if the `cv5n6t` defect is reintroduced.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE NARROWING PATTERN ALREADY EXISTS IN THIS VERY FUNCTION, so this plan introduces no new convention. Two blocks in `execute_item_core` already read `with contextlib.suppress(DriverError, OSError):` around `git_head(Path(work_dir))` in the spec/backlog-production isolation arm. The helper `runner_shared._record_lane_ending_facts` does the same thing with an explicit handler: `except (DriverError, OSError): return`. Both are the shape this plan applies to the remaining blocks.
- INJECTED CALLABLES ARE THE REASON SIGNATURES DRIFT HERE. `execute_item_core` rebinds roughly a dozen names off `driver_module` via `getattr(driver_module, "<name>", globals().get("<name>"))`, because the shared body cannot resolve a host-specific `env_builder` (the rule stated for `git_head`/`git_status`/`git_common_dir`, and the reason `build_lane_outcome` takes `run_checked` keyword-only at all). A `getattr` fallback that silently resolves the WRONG definition is exactly the drift a blanket suppress then hides, which is why narrowing matters more in this function than it would elsewhere.
- BEST-EFFORT IS A REAL CONTRACT IN SOME PLACES AND MUST BE RESPECTED. `SuiteBaselineRun.collect`, `SuiteBaselineRun.abandon` and `remove_suite_baseline_checkout` all document "NEVER raises", and the `finally` arm depends on it so cleanup cannot replace an in-flight exception. This plan narrows blocks; it does not convert documented-silent paths into failing ones.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE. A source-scanning test (`grep` for `suppress(Exception)`) would be the easy way to pin this and is forbidden by AGENTS.md and GUIDING_PRINCIPLES P16. `tests/test_lane_reaper_callshape.py` is the in-repo model for pinning a calling convention behaviorally.

## Findings

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | `execute_item_core` contains SEVEN `suppress(Exception)` blocks and TWO already-narrowed `suppress(DriverError, OSError)` blocks. | Enumerated across the function body (`runner_shared.execute_item_core`, roughly lines 30461-34504 at authoring). | The narrow form is already the local convention; the blanket form is the outlier, in the same function. |
| F-2 | The `cv5n6t` call site had TWO independent failure modes, not one. | Reproduced by execution: calling the shared `build_lane_outcome(repo, handle, id6)` without `run_checked` gives `TypeError: build_lane_outcome() missing 1 required keyword-only argument: 'run_checked'`; calling it with `handle=None` gives `AttributeError: 'NoneType' object has no attribute 'base_commit'`. | `h5pyqa` fixed the first. The second is still absorbed by the suppress, and the adjacent `branch=wt_handle.branch if wt_handle else None` proves `None` reaches this arm. Narrowing without E-02's guard would convert that silence into a crash, which is why the two ship together. |
| F-3 | The silently-unwritten field is not merely cosmetic: it changes a runner DECISION. | `integration_changed_files` has two consumers. One builds the gate question's file list. The other passes it to `poll_for_integration_window`. Measured: `dirty_tree_overlap(repo, [])` returns `[]`, and `poll_for_integration_window(repo, [])` returns `bound='dirt-cleared'`, `cleared=True`, `polls=0`, detail "the overlapping dirty path cleared after 0 poll(s)". | An empty field makes the poll report the contention CLEARED without examining anything. The backlog item describes the harm as a human seeing no file list; it is also a false clear-verdict on the retry path. This RAISES the stakes of the field being written, and is recorded here as motivation, not as a second defect to fix: with E-01/E-02 the field is written whenever a lane exists, and honestly absent when none does. |
| F-4 | `build_lane_outcome`'s anticipated failure is exactly `DriverError`. | Its docstring warns against simplifying its three calls onto `_run_git` because "that would stop them raising `DriverError` on a failed `git rev-parse`/`git diff` and silently build a LaneOutcome from empty strings". | `suppress(DriverError)` preserves the documented degradation and nothing more. |
| F-5 | `collect_lane_submissions` has no internal `try`/`except` and raises no `DriverError`; its helper `_collect_one` absorbs `OSError` per file and reports `failed` with a reason. | Read from `lane_containment.collect_lane_submissions` and `lane_containment._collect_one`. | `suppress(OSError)` covers the receipt writes; an `AssertionError` from the function's own `assert paths.lane_decisions is not None` should NOT be suppressed, since it signals a broken precondition. |
| F-6 | No test proves `integration_changed_files` is recorded on refusal. | The only `tests/` references to `build_lane_outcome` are in `tests/test_runner_shared.py` as a NAME in a re-export/wrapper census (its layering fixtures), not a behavioral exercise of this arm. | The `cv5n6t` defect could ship, and did, with a green suite. E-06 closes that gap; without it this plan's narrowing is itself unprotected against re-widening. |

## Proposed changes (ordered, validatable)

1. E-01: narrow the integration-refusal block to `suppress(DriverError)`.
2. E-02: add the explicit `wt_handle is None` guard around that same call, so E-01 is safe on the path the neighbouring line proves is reachable.
3. E-03: narrow both `queue_artifact_path` blocks to `suppress(DriverError, ValueError)`.
4. E-04: narrow the `collect_lane_submissions` block to `suppress(OSError)`.
5. E-05: narrow the baseline `collect` block to `suppress(OSError)`, comment why it is kept, and leave the `finally` arm alone.
6. E-06: add `tests/test_suppress_narrowing.py` pinning the behavior of the refusal arm.

Order matters only for E-01 before E-02 (narrow, then make the narrowing safe) and for E-06 last (it pins the finished state). E-03, E-04 and E-05 are independent of each other.

## Deferred / out of scope (with reason)

- THE `he9x6j` DEFECT is the sibling instance of this failure mode (`tool_event` carried no output text, so every consumer's stdout read silently yielded empty string) and remains OPEN. Not touched here: it is a different seam with a different fix, and it carries its own backlog item.
- `suppress(Exception)` ELSEWHERE IN THE MODULE and in the wider package. The item scopes the audit to `execute_item_core`, and a module-wide sweep would be a much larger change with a much weaker per-site justification. If this plan's pattern is judged worth generalizing, that is a follow-up with its own measurements.
- THE TWO `finally`-ARM BLOCKS (`suite_baseline_run.abandon()`, `remove_suite_baseline_checkout(...)`). Deliberately left blanket: a raise from a `finally` would replace the exception the turn is already carrying, including a deliberate stop. Narrowing them would be a correctness REGRESSION, and the existing comment already states the rule.
- THE FALSE-`cleared` POLL VERDICT measured in F-3. Recorded as motivation, not fixed. With the field reliably written the empty-input case stops arising from THIS cause, but `poll_for_integration_window` would still report `cleared` for a genuinely empty input from any other caller. Whether that degenerate input deserves its own refusal is a separate judgement about the poll's contract, and is not in this item's scope.
- CHANGING WHAT THE RUNNER DECIDES on a refusal. This plan changes only what is RECORDED and what is allowed to stay silent.

## Scope check

- Over-scope: none. Two files, both declared: the seven blocks live in `runner_shared.py`, and the pin needs a new test file.
- Under-scope: the two `(DriverError, OSError)` blocks are already correct and need no edit; the `finally`-arm blocks are deliberately excluded with a stated reason; `he9x6j` is separately filed. `agy_runipd.py` and `oc_runipd.py` are deliberately NOT declared: both hosts reach this code through the one shared `execute_item_core`, so neither needs an edit, and declaring a file no work touches invites a declared-but-unmodified reconciliation note for nothing.

## Required tests / validation

- `tests/test_suppress_narrowing.py` (new, E-06): the four behavioral cases on the refusal arm (propagating `TypeError`, quiet `DriverError`, successful record, `None` lane).
- The FULL suite, run BARE as `python3 -m pytest`, with the actual summary line pasted. `execute_item_core` is the shared body both hosts run, so a narrowing that turns a previously-absorbed exception into a propagating one would surface as a failure in the existing runner tests (`tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_silent_turn_observability.py`); a green suite is therefore part of the evidence, not a formality.
- SABOTAGE CHECKS, since a test that cannot fail proves nothing: for each narrowed block, widen it back to `suppress(Exception)` and confirm the new test goes RED; then restore. For E-02, delete the `None` guard and confirm the `None` case goes RED.

## Spec / documentation sync

N/A with reason: no spec governs the exception-suppression breadth of an internal best-effort block, and no `.spec.md` file is in scope. The behavior a human reads about (a refusal records its file list) is unchanged in the SUCCESS case and only becomes more reliable; nothing user-facing changes, so no README or CHANGELOG entry is required. Each narrowed block keeps an in-code comment naming the exception it anticipates and why, which is where a future reader will look.

## Open questions

### OQ-01: Should E-05's baseline `collect` block be narrowed at all, or removed outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE, no maintainer turn needed. `SuiteBaselineRun.collect` documents "NEVER raises and NEVER waits unboundedly" and its body suppresses internally, so the outer block is a second belt over a callee that already promises silence. Removing it would mean a broken promise fails a turn, and the adjacent code states that a missing baseline must never be a failed item ("A MISSING OR FAILED BASELINE IS NOT A FAILED ITEM"). So the block STAYS, narrowed to `OSError`, with the reason recorded in a comment. This is the conservative reading of an explicit local contract.

### OQ-02: Does narrowing risk turning a previously-survivable turn into a failed one?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY CONSTRUCTION, and this is the plan's main risk, so it is stated rather than assumed. Yes in principle: any exception a narrowed block no longer catches will now propagate. That is the POINT when the exception means the code is wrong, and it is a REGRESSION when the exception was a real anticipated condition. The mitigation is that each narrowed tuple is derived from the callee's own raise sites and docstring (F-4, F-5) rather than guessed, that the one reachable non-error case found (`wt_handle=None`) gets an explicit guard in E-02 instead of being absorbed, and that the full suite plus the sabotage checks are what demonstrate no anticipated path was lost. If review finds a further anticipated exception at any site, the fix is to add that class to that site's tuple, not to restore the blanket form.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the final narrowed block showing `suppress(DriverError)`. Paste a test run in which a `build_lane_outcome` stub raising `TypeError` causes the exception to PROPAGATE out of the refusal arm (the `cv5n6t` regression, previously swallowed), and one in which a stub raising `DriverError` is absorbed with `integration_changed_files` left unwritten. Then paste the SABOTAGE result: widen the block back to `suppress(Exception)` and show the `TypeError` test going RED, with the failing assertion visible.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the guard as written. Paste a test run driving the refusal arm with `wt_handle=None` showing NO exception and NO `integration_changed_files` key on the item. Paste the SABOTAGE result: remove the guard and show that case going RED with `AttributeError: 'NoneType' object has no attribute 'base_commit'`, which proves the guard is load-bearing and not decorative.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both narrowed blocks showing `suppress(DriverError, ValueError)`. Paste evidence that each anticipated class is still absorbed (a non-IPD queue entry whose artifact does not resolve raises `DriverError` and the allow-list is simply not widened; a `relative_to` mismatch raises `ValueError` and is absorbed) and that an unanticipated class now escapes. Quote the `queue_artifact_path` raise sites that justify `DriverError` so a reviewer can check the tuple against the callee.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the narrowed block showing `suppress(OSError)`, plus the observation from `lane_containment.collect_lane_submissions` that it contains no `try`/`except` and no `DriverError` raise, and from `_collect_one` that it already absorbs `OSError` per file. Show the adjacent `except (KeyboardInterrupt, StallTimeout)` UNCHANGED. Demonstrate that a keyword drift in the six-argument keyword-only call now raises instead of vanishing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the narrowed baseline block and its new comment. Paste the two `finally`-arm blocks showing them UNCHANGED as `suppress(Exception)`, since narrowing them would be a regression. Demonstrate that a missing or unfinished baseline still yields a `suite_baseline_absent` record and does NOT fail the item, quoting the resulting `state`/`reason`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full output of `python3 -m pytest tests/test_suppress_narrowing.py` showing every test passing with its count. Paste the BARE full-suite summary line from `python3 -m pytest` (no added flags) and account for every failure: each must be proven PRE-EXISTING on the unmodified tree at the base commit, or fixed. Confirm by inspection that the new test file contains no `inspect`, `ast`, regex or substring search over production source, and no assertion on caller counts or line counts, per GUIDING_PRINCIPLES P16.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved 8o709f --by-human`). The reason to read it before approving is OQ-02: narrowing a suppression is a deliberate decision to let some exceptions propagate that previously did not, in the shared body BOTH host runners execute for every queued item. Each narrowed tuple is derived from its callee's own raise sites rather than guessed (F-4, F-5), the one reachable non-error case found is guarded rather than absorbed (E-02), and the full suite plus per-site sabotage checks are the evidence that no anticipated path was lost. The most likely review objection is that a site needs one more exception class in its tuple; the answer to that is to add the class, not to restore the blanket form.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.

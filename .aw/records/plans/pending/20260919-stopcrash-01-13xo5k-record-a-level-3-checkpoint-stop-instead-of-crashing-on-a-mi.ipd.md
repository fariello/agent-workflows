# IPD: Record a level-3 checkpoint stop instead of crashing on a missing exit_code, and pin the handler bodies that no test executes

- Date: 2026-09-19
- Kind: child
- Concern: A level-3 stop, the feature whose whole purpose is to wind a run down CLEANLY at an observed safe boundary, CRASHES the runner with an unhandled `AttributeError` instead of recording the stop. MEASURED 2026-09-19 at HEAD `ecdd348f` by running `aw oc run setidfix` and letting a level-3 stop fire: `runner_stop.StopAtCheckpoint` was raised correctly at `oc_runipd.run_opencode`, and the handler for it in `runner_shared.execute_item_core` then died on `attempt["exit_code"] = stop.exit_code` with `AttributeError: 'StopAtCheckpoint' object has no attribute 'exit_code'`.
  THE DEFECT IS A TYPO-CLASS MISTAKE WITH AN OUTSIZED CONSEQUENCE, WHICH IS WHY IT IS WORTH A PLAN. `StopAtCheckpoint.__init__` takes ONLY a `CheckpointObserver` and sets ONLY `self.observer`; its attribute surface is `observer` plus `Exception`'s own. Its SIBLING `StopNowForce` (the level-4 exception) DOES carry an `exit_code`, and the two handlers sit a dozen lines apart in the same function, so the level-3 handler was evidently written by adapting the level-4 one and kept a line that cannot work. The result is that the graceful path fails LOUDER than the abrupt one.
  WHAT THE OPERATOR ACTUALLY LOSES, and it is not merely a stack trace. The crash occurs AFTER `_record_checkpoint_stop` has run but BEFORE `save_state`, so the attempt is left un-persisted: `attempt["disposition"]`, `item["status"]` and the `stopped` record are never written, and the cleanly-stopped item is not marked `interrupted`. So a stop that the machinery correctly identified as safe is recorded as a crash, which is precisely the "fabricated disposition" outcome `runner_stop.deliberate_stop_exit_code` documents itself as existing to avoid. A resume then reads a state file that never learned the item stopped.
  THERE ARE TWO HANDLERS AND ONLY ONE IS BROKEN, a distinction an implementer must not flatten. `runner_shared` handles `StopAtCheckpoint` twice. The one in `execute_item_core` assigns `stop.exit_code` and crashes. The second, in the enclosing verify/reconcile block, sets `interrupt_reason`, records the stop, sets the disposition, reconciles `item["status"]` with a literal `1`, and RE-RAISES, touching `exit_code` NOWHERE. So the second is already correct and must be left alone; the fix is to make the first stop inventing an attribute that does not exist.
  AND NOTHING WOULD HAVE CAUGHT IT, WHICH IS THE HALF WORTH FIXING PROPERLY. `tests/test_runner_stop_level3.py` is substantial and pins the exception's CONSTRUCTION well: it greps that `runner_stop.StopAtCheckpoint` appears in the drivers' source and asserts by REGEX that every raise site passes `checkpoint_observer` and not another object. Those are SOURCE-TEXT assertions. No test in the suite EXECUTES the handler body, so an attribute that does not exist on the exception was invisible to a green suite. A regex that proves the raise is well-formed says nothing about whether the catch can run.
- Scope: The level-3 checkpoint-stop handler in `runner_shared.execute_item_core`, and the test gap that let a non-existent attribute ship. IN: removing the impossible `stop.exit_code` read and recording the stop honestly (deriving the exit status the way the stop machinery already prescribes rather than inventing a number); executing BOTH `StopAtCheckpoint` handler bodies in a test so the attempt record and the persisted state are asserted rather than the source text; keeping the second handler's re-raise behavior byte-identical. OUT: any change to `runner_stop`'s exception classes or their constructors (adding an `exit_code` to `StopAtCheckpoint` is considered and REJECTED in OQ-01, because the two levels legitimately differ); any change to level-4 `StopNowForce` handling; the stop LEVELS, their trigger detection, or the checkpoint observer; the unrelated crash class in which a stop fires before `work_dir` exists.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_stop_level3.py
- Item-Dependencies: none
- Status: to-review
- Set: stopcrash
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 13xo5k
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's instruction after the crash was hit live while gathering V-evidence for orchestrator `7ewc74`. The traceback is REAL and pasted in F-1 rather than reconstructed: it came from an actual `aw oc run setidfix` whose level-3 stop fired at event 89. Every claim about the two handlers, the exception's attribute surface, and the test gap was verified by reading the shipped source and by `dir()` on the class, not inferred from the traceback. The run that produced it was stopped and its scratch worktree removed with no state left in main.
- 2026-09-19 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a level-3 stop do what it says: record the item as cleanly stopped, persist that, and return an honest exit status, instead of raising `AttributeError` from its own handler. Then close the gap that hid it, by executing both handler bodies in tests rather than asserting on their source text.

READ THE GOAL PRECISELY: this plan does NOT change WHEN a stop fires, WHICH level does what, or what `StopAtCheckpoint` carries. It fixes one impossible attribute read and the missing coverage that allowed it. The stop machinery's design is correct; its level-3 bookkeeping is not.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the crash

- [ ] E-01 REMOVE THE IMPOSSIBLE READ AND RECORD THE STOP HONESTLY, in `runner_shared.execute_item_core`'s `except runner_stop.StopAtCheckpoint as stop:` branch, at the line `attempt["exit_code"] = stop.exit_code`. `StopAtCheckpoint` has no such attribute and must not gain one (OQ-01). DO NOT simply delete the line and leave the key absent without checking who READS it: establish first whether a consumer (the run record, `aw runs`, the resume path, the summary table) requires `attempt["exit_code"]` to be present, and record the answer in the plan. If it is required, derive it the way the stop machinery already prescribes rather than hardcoding a number: `runner_stop.deliberate_stop_exit_code` exists for exactly the question "what is the honest exit status when a stop left items unrun", and its docstring records that a deliberate stop must not be reported as a failure merely because items are still `queued`. If it is genuinely optional, say so with the evidence and omit it.
  THE SIBLING IS THE TRAP, NOT THE TEMPLATE. `StopNowForce` carries `exit_code` and its handler reads it correctly a dozen lines above. Copying that line is what produced this bug; do not "restore symmetry" by making the two handlers look alike. They handle exceptions with deliberately different payloads.
  - Depends on: none
  - Expected outcome: a level-3 stop completes its handler without raising; `attempt` carries a defensible exit status (or provably does not need one); the crash no longer reproduces.
  - Execution state: pending

- [ ] E-02 CONFIRM THE STOP IS PERSISTED, which is the operator-visible half of the defect and is NOT automatically fixed by E-01. The crash happened after `_record_checkpoint_stop` but BEFORE `save_state`, so the item's `interrupted` disposition and its `stopped` record were computed and then lost. Verify by reading the state file after a level-3 stop that `attempt["disposition"]` and `item["status"]` are both `runner_stop.STOPPED_DISPOSITION` (measured value: `'interrupted'`) and that the `stopped` record is present. If any write still happens after a statement that can raise, move it or justify the order.
  - Depends on: E-01
  - Expected outcome: after a level-3 stop the persisted state records the stop; a resume reads an item that knows it was interrupted.
  - Execution state: pending

### Task group 2: close the gap that hid it

- [ ] E-03 EXECUTE BOTH `StopAtCheckpoint` HANDLER BODIES IN TESTS, which nothing currently does. `tests/test_runner_stop_level3.py` pins the exception's CONSTRUCTION by source text: it greps the drivers for `runner_stop.StopAtCheckpoint` and asserts by regex that each raise site passes `checkpoint_observer`. Both are worth keeping and NEITHER can catch this defect, because a well-formed raise says nothing about whether the catch runs. Add a test that drives `execute_item_core` to the level-3 branch with a real `StopAtCheckpoint` and asserts the attempt record and the persisted state, and a second that reaches the OTHER handler (the verify/reconcile one) and asserts it still RE-RAISES after recording. Assert on OBSERVED behavior, not on source text.
  THE ASSERTION MUST BE ABLE TO FAIL. Re-introduce `attempt["exit_code"] = stop.exit_code` and show the new test raises `AttributeError`; restore and show it passes. A test that cannot fail on the original bug has not closed the gap.
  - Depends on: E-01, E-02
  - Expected outcome: two tests that execute the handler bodies; the mutation check fails on the original line and passes once reverted.
  - Execution state: pending

- [ ] E-04 STATE THE SOURCE-TEXT LIMIT WHERE THE EXISTING TESTS CLAIM COVERAGE, as a comment in `tests/test_runner_stop_level3.py` beside the grep/regex assertions. They read as coverage of the stop path and are not: they cover the RAISE. One sentence naming what they do and do not prove, so the next reader does not take a green file as evidence the handler works. Do NOT weaken or delete those assertions; they catch a different and real regression (a raise site passing the wrong object).
  - Depends on: E-03
  - Expected outcome: the limit is recorded next to the assertions it qualifies; both original assertions still pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `StopAtCheckpoint` AND `StopNowForce` CARRY DELIBERATELY DIFFERENT PAYLOADS. `StopAtCheckpoint.__init__(observer)` sets only `self.observer`; `dir()` confirms the instance surface is `observer` plus `Exception`'s. `StopNowForce` carries an `exit_code`. Their docstrings record that levels 3 and 4 share a TERMINATION mechanism and differ only in WHEN it is issued, so the payload difference is intentional and is not drift to be tidied.
- THE STOPPED DISPOSITION IS A CONSTANT, NOT A LITERAL: `runner_stop.STOPPED_DISPOSITION` is `'interrupted'`. Assert against the constant so a rename cannot silently pass.
- THE EXIT-STATUS QUESTION ALREADY HAS AN OWNER: `runner_stop.deliberate_stop_exit_code(statuses, *, success_states, stopped)`. Its docstring records that the drivers' normal predicate returns 1 for a correct operator-requested wind-down and that spec `c4gd2h` A1/A4 require 0, and that items left `queued` are ignored BECAUSE THEY NEVER RAN. Any exit status this plan records must come from there rather than from a fresh literal.
- THE SECOND HANDLER RE-RAISES ON PURPOSE. The verify/reconcile `except runner_stop.StopAtCheckpoint` records the stop, reconciles the item's status, and `raise`s so the driver's outer `except BaseException` routes to the shared reaper. `StopAtCheckpoint`'s own docstring states that raising is deliberate for exactly this reason (spec R5). Do not convert it to a swallow.
- A GREEN SUITE PROVED THE RAISE, NOT THE CATCH. This is the transferable lesson and the reason E-04 exists: `test_runner_stop_level3.py` asserts over SOURCE TEXT (a `grep` for the symbol, a `re.findall` over raise sites). Source-text assertions cannot detect a non-existent attribute on an exception, and this defect shipped past a substantial, passing test file for that reason.
- BOTH DRIVERS RAISE AND BOTH DELEGATE THE HANDLING. `oc_runipd` and `agy_runipd` each raise `StopAtCheckpoint` and each carry their own thin `except runner_stop.StopAtCheckpoint`, while the substantive handling lives in `runner_shared`. So this is a ONE-PLACE fix that reaches both hosts, and no symbol may be added to `oc_runipd` for agy to import.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.execute_item_core`, its `except runner_stop.StopAtCheckpoint` branch, at `attempt["exit_code"] = stop.exit_code` | The level-3 handler reads an attribute the exception does not have, so the graceful stop path crashes. REAL traceback, from an actual run: `AttributeError: 'StopAtCheckpoint' object has no attribute 'exit_code'`, reached via `run_queue` -> `execute_item` -> `execute_item_core` after `StopAtCheckpoint: level-3 stop honored at safe checkpoint after event 89 (tool_use:read)`. | `aw oc run setidfix` at HEAD `ecdd348f`, 2026-09-19 |
| F-2 | HIGH | `runner_stop.StopAtCheckpoint.__init__` | The attribute genuinely does not exist and its absence is by design: the constructor takes only a `CheckpointObserver` and sets only `self.observer`. `dir()` on the class returns `['add_note', 'args', 'with_traceback']` beyond dunders. | Source read; `dir()` executed |
| F-3 | HIGH | `runner_shared.execute_item_core` ordering: `_record_checkpoint_stop` then `save_state` | THE OPERATOR-VISIBLE LOSS, not just a trace: the crash lands between recording and persisting, so the `stopped` record, `attempt["disposition"]` and `item["status"]` are computed and then discarded. A cleanly stopped item is never marked `interrupted`, and a resume reads a state file that never learned it stopped. | Handler body read in execution order |
| F-4 | MEDIUM | `runner_stop.StopNowForce` and its handler in the same function | The level-4 sibling DOES carry `exit_code` and its handler reads it correctly a dozen lines above. That adjacency is the likely origin of the bug and is a TRAP for the fix: making the two handlers symmetric re-introduces it. | Both handlers and both classes read |
| F-5 | HIGH | `runner_shared`'s SECOND `except runner_stop.StopAtCheckpoint` (verify/reconcile block) | ONLY ONE OF THE TWO HANDLERS IS BROKEN. The second sets `interrupt_reason`, records the stop, sets the disposition, reconciles status with a literal `1`, and re-raises, never touching `exit_code`. It is already correct and must be left alone. A fix that "unifies" them would change working behavior. | Both branches read side by side |
| F-6 | HIGH | `tests/test_runner_stop_level3.py`, its `assertIn("runner_stop.StopAtCheckpoint", source)` and its `re.findall(r"StopAtCheckpoint\((?!checkpoint_observer)\w", src)` assertions | THE TESTS ASSERT OVER SOURCE TEXT, so they prove the RAISE is well-formed and can say nothing about whether the CATCH runs. This is why a substantial, passing test file did not catch an attribute that does not exist. | Test source read |
| F-7 | MEDIUM | `runner_stop.deliberate_stop_exit_code` | The honest-exit-status question is already owned and documented (a deliberate stop must not report failure merely because items are still `queued`; spec `c4gd2h` A1/A4 require 0). So E-01 has a prescribed source for any exit status and needs no new literal. | Signature and docstring read |
| F-8 | LOW | `runner_stop.STOPPED_DISPOSITION` | The disposition is a constant whose value is `'interrupted'`. Tests should assert the constant, not the string. | Value read |

## Proposed changes (ordered, validatable)

1. E-01 removes the impossible `stop.exit_code` read and records a defensible exit status, or proves the key is optional.
2. E-02 confirms the stop is PERSISTED, since the crash discarded a record that had already been computed.
3. E-03 adds tests that EXECUTE both handler bodies, with a mutation check against the original line.
4. E-04 records, beside the existing source-text assertions, what they do and do not prove.

## Deferred / out of scope (with reason)

- ADDING AN `exit_code` TO `StopAtCheckpoint`: rejected, see OQ-01. The two stop levels legitimately differ in payload and the fix belongs in the handler.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed. There is no work to hand off.
- ANY CHANGE TO LEVEL-4 `StopNowForce` OR ITS HANDLER: out of scope and working. It is named here only because its adjacency is the trap F-4 describes.
  - Carrier-Declined: Judged correct as-is; nothing deferred.
- THE SECOND (VERIFY/RECONCILE) HANDLER'S BEHAVIOR: deliberately untouched per F-5. E-03 adds a test that it still re-raises, which is coverage, not a change.
  - Carrier-Declined: Explicitly preserving existing correct behavior is not an outstanding obligation.
- THE STOP LEVELS, TRIGGER DETECTION, AND THE CHECKPOINT OBSERVER: the design is sound; only its level-3 bookkeeping is broken.
  - Carrier-Declined: No defect found in them, so there is nothing to carry.
- A BROADER AUDIT FOR OTHER SOURCE-TEXT-ONLY TEST COVERAGE: the same pattern (assert a symbol appears, never execute it) may hide comparable defects elsewhere, and a repo-wide sweep is real work with its own blast radius. Not undertaken here, where the concern is one handler.
  - Carrier: 13xo5k

## Scope check

- Over-scope: none. `runner_shared.py` is touched by E-01/E-02 and `tests/test_runner_stop_level3.py` by E-03/E-04.
- Under-scope: if E-01's consumer investigation shows a reader of `attempt["exit_code"]` lives OUTSIDE these two files (for example in the run viewer or the summary renderer), that file must be DECLARED before being edited rather than reconciled afterward. The investigation is deliberately part of E-01 so the answer precedes the edit.

## Required tests / validation

`python3 -m pytest` bare. Do NOT add flags: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Establish the baseline IN THE EXECUTING WORKTREE and compare by failing NODE ID, not by total, since concurrent work moves the total.

Beyond the suite: the ORIGINAL crash must be shown not to reproduce, and the evidence must be a level-3 stop that reaches the handler, not merely a passing unit test. A synthetic `StopAtCheckpoint` driven through `execute_item_core` is acceptable and is preferred over spending an agent run; if a live run is used, say so and paste its stop line. Also paste the persisted state after the stop (E-02) and the mutation check (E-03).

## Spec / documentation sync

N/A with reason: spec `c4gd2h` (runner lifecycle graceful quit) already prescribes the behavior this plan restores, including the level-3 checkpoint semantics and the A1/A4 exit-status requirement. Nothing in the spec is wrong, so there is no amendment to make; this plan makes the code match a contract it already violates. No `.spec.md` file is declared in `- Scope-Paths:` for that reason.

## Open questions

### OQ-01: Should `StopAtCheckpoint` gain an `exit_code`, making it symmetric with `StopNowForce`?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED AS NO, from the classes' own documented design. The two exceptions differ in payload because the two stop LEVELS differ: level 4 is an immediate cut that knows its exit status at the raise site, while level 3 is honored at an OBSERVED boundary whose honest exit status depends on what actually ran, which is precisely the question `runner_stop.deliberate_stop_exit_code` exists to answer from the item statuses. Adding the field would let a raise site guess a number the run cannot know yet, and would make the buggy line "work" while recording something less true than a crash. NOT blocking because either answer fixes the crash; it is recorded because "make the sibling classes match" is the obvious wrong instinct here and F-4 shows that instinct is what produced the defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the handler branch as written after the change, showing no `stop.exit_code`. Paste the CONSUMER INVESTIGATION's result: name every reader of `attempt["exit_code"]` you found and how you searched, then state whether the key is required or optional and why. If you recorded an exit status, paste the call to `runner_stop.deliberate_stop_exit_code` and its arguments, and say why those arguments are the right ones; if you omitted the key, paste the evidence no consumer requires it. Paste the original `AttributeError` traceback and then proof it no longer reproduces, by DRIVING the branch rather than by asserting the line is gone.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the persisted state file (or the relevant fragment) after a level-3 stop, showing `attempt["disposition"]` and `item["status"]` both equal to `runner_stop.STOPPED_DISPOSITION` (assert the CONSTANT, and state its value) and the `stopped` record present. Paste the handler's write ORDER, showing nothing that can raise now sits between the record and `save_state`. If the order is unchanged, justify why it is safe rather than asserting it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both new tests and their passing output. For the FIRST, show it executes `execute_item_core`'s level-3 branch (not a re-implementation) and asserts the attempt record. For the SECOND, show the verify/reconcile handler still RE-RAISES after recording. Then the MUTATION CHECK, which is the load-bearing evidence: re-introduce `attempt["exit_code"] = stop.exit_code`, paste the new test FAILING with `AttributeError`, restore, paste it passing. A test that does not fail on the original line has not closed the gap and this item FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the added comment and the two original assertions it qualifies, and confirm both still pass UNCHANGED (show they are absent from your diff, or that only a comment was added around them). State in one sentence what those assertions prove and what they do not, and confirm the comment says the same.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 4 E-leaves in 2 groups. The code fix is one or two lines; most of the work is the investigation E-01 requires before editing and the coverage E-03 adds, because the missing coverage is the reason the bug shipped.
- Cohesion rationale: E-01 and E-02 are one handler's correctness (stop crashing, and persist what was already computed), and separating them would leave a fix that no longer raises while still discarding the stop record. E-03 and E-04 are the test surface for exactly that handler; landing the fix without E-03 leaves the same blind spot that hid it.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. PREFER A SYNTHETIC `StopAtCheckpoint` over a live agent run for evidence; the crash was found during a live run that cost real money and was stopped, and reproducing it that way is not necessary.

Post-gate lifecycle: this plan is `to-review` and requires `/plan-review` followed by explicit human approval (`aw ipd set approved 13xo5k --by-human --message ...`) before execution. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

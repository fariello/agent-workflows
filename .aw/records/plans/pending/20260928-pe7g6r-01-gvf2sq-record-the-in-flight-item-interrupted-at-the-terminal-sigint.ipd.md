# IPD: Record the in-flight item interrupted at the terminal SIGINT rung instead of resetting it to queued

- Date: 2026-09-28
- Kind: child
- Concern: THE TERMINAL SIGINT RUNG STILL DOES NOT LEAVE THE IN-FLIGHT ITEM `interrupted`, AND THE TEST THAT SAID SO NO LONGER EXISTS. Backlog `pe7g6r` (`bug`, `high`, `Blocks-Release: next`) reports `tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted` failing `'running' != 'interrupted'` at HEAD `761edad3`. THAT NODE ID IS UNRUNNABLE TODAY: the whole file was DELETED by trim commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24), which `git log --diff-filter=D -- tests/test_runner_stop_triggers.py` confirms, so the item's own reproduction command now errors on collection rather than failing an assertion. THE ORIGINAL `running` ROOT CAUSE IS GENUINELY FIXED and this plan does not re-fix it: executed plan `87jnym` (`intrecon` Order 1, `From-Backlog: 2415x6`) re-added the `except KeyboardInterrupt as exc:` arm that calls `runner_shared.reconcile_item_on_interrupt`, which now has a live caller in `runner_shared.execute_item_core` beside its `StopNowForce`/`StopAtCheckpoint`/`StallTimeout` siblings, and `tests/test_interrupt_reconcile.py` covers it green (24 passed with its metadata sibling).
   BUT THE CONTRACT THE DELETED TEST ASSERTED IS STILL VIOLATED, ON A DIFFERENT AND UNCOVERED PATH, measured at HEAD `e3ff155e` by driving the REAL `oc_runipd.execute_item` with the EXACT message the terminal rung raises. `runner_shared.install_stop_triggers`'s `_terminal` callback raises `KeyboardInterrupt(f"stop level {level} ({runner_stop.LEVEL_NAMES.get(level, 'unknown')}) requested by {requester or 'SIGINT'}")`, i.e. the literal `stop level 4 (now-force) requested by signal pid=<n>`. That string contains NEITHER sentinel `reconcile_item_on_interrupt` switches on, so it falls through the `if "just-terminate-no-cleanup" in msg:` guard into the DEFAULT `clean-up-and-terminate` arm. On a CLEAN tree that arm computes `holds_work = False` and then deliberately sets `item["status"] = "queued"`, pops the attempt, and unlinks the begin receipt. MEASURED, both arms of the same probe: dirty tree -> `status 'interrupted'`, events `[... 'ipd-interrupted']`; CLEAN tree -> `status 'queued'`, events `[... 'ipd-cleaned-up-no-changes']`, no `ipd-interrupted` at all. So the exact assertion the deleted test made (`item["status"] == "interrupted"`, and never a state that lets the item look un-run) FAILS today on the clean-tree terminal rung, for a reason unrelated to the `running` bug already fixed.
   WHY `queued` IS A REAL DEFECT AND NOT MERELY A DIFFERENT SPELLING. `queued` is not in `runner_shared.TERMINAL_STATES_CANONICAL` (which lists `interrupted` explicitly), so the force-stopped item is indistinguishable from one that never started: `requeue_interrupted`'s spec-R19 indeterminate gate keys on `interrupted` and is therefore never consulted, and its own docstring says the gate exists because "a force-interrupted item whose outcome the driver never established is re-run blindly, which is the exact failure spec R19 exists to prevent". A level-4 force stop is precisely that unestablished outcome: the operator pressed Ctrl-C three times while a child was mid-turn, and `git status --porcelain` being clean does NOT prove the turn did nothing, because the child may have committed (the repo's own execution contract obliges it to) or written outside the repo. `render_stream._interrupt_reason_of`'s `interrupted` arm also renders nothing for a `queued` item. The user-visible stake is the same one `87jnym` was filed for, one step further along: a resumed run silently re-executes a turn whose real outcome nobody established.
- Scope: IN: (a) make the terminal rung's interrupt DISTINGUISHABLE to `reconcile_item_on_interrupt` so it takes an interrupt-preserving path instead of the destructive no-changes cleanup, and leaves the in-flight item recorded `interrupted` with an `ipd-interrupted` event on a CLEAN tree as well as a dirty one; (b) restore BEHAVIORAL coverage of the terminal-rung contract the `19313eed` trim removed, driving the real `execute_item` of BOTH hosts with the real `_terminal` message rather than a hand-written sentinel, and pinning the message-to-arm routing itself so a future reword of `_terminal` cannot silently re-break it; (c) a regression test that the interactive menu's OWN `clean-up-and-terminate` action still reaches the no-changes cleanup arm, since that arm is correct for a DELIBERATE operator cleanup and must not be collateral damage. OUT: the `running` root cause and the `_run_git` tuple/attempt-key defects (all fixed by executed `87jnym`; this plan re-measures them green as a baseline and changes none of them); the `SigtermTests` level-3 `KeyError: 'stopped'` half of sibling backlog `wqk5s2` (a different rung, still live and still gated); reviving `tests/test_runner_stop_triggers.py` wholesale or reversing the `19313eed` trim; any change to `runner_stop`'s ladder levels, budgets, `interrupt_menu_is_safe`, or the exit-130/143 mapping in either host's `main`; the slow-marker visibility problem the item describes, which is owned by `xuc9v0`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_interrupt_reconcile.py
- Item-Dependencies: none
- Status: to-review
- Set: pe7g6r
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: gvf2sq
- From-Backlog: pe7g6r
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `pe7g6r`. Measured at HEAD `e3ff155e` that the item's cited node id is UNRUNNABLE (file deleted by trim `19313eed`), that its `running` root cause is fixed by executed `87jnym`, and that the contract it asserted is NEVERTHELESS still violated on the clean-tree terminal rung, where the real `_terminal` message routes into the destructive no-changes arm and leaves the item `queued` with no `ipd-interrupted` event.

## Goal

Make a third Ctrl-C leave the in-flight item recorded `interrupted` whatever the working tree looks like, so the spec-R19 indeterminate gate can see a force-stopped turn instead of mistaking it for one that never ran, and cover that contract with behavioral tests that survive a test-suite trim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the terminal rung distinguishable and preserve its item

- [ ] E-01 In `agent_workflows/runner_shared.py`, define one module-level sentinel constant for an unrequested force stop (name it for what it means, e.g. `FORCED_INTERRUPT_SENTINEL`, value a stable hyphenated token such as `unrequested-force-stop`) and include it in the `KeyboardInterrupt` message raised by `install_stop_triggers`' inner `_terminal` callback, ALONGSIDE the existing level/level-name/requester text rather than replacing it. Comment WHY the sentinel exists: the message is the only channel `reconcile_item_on_interrupt` receives, and the previous message matched neither of its two sentinels and so silently took the destructive default arm (F-3).
  - Depends on: none
  - Expected outcome: `_terminal`'s message still reads `stop level 4 (now-force) requested by <requester>` for an operator, and additionally carries the sentinel token; the constant is defined once in the shared module and referenced by both the raiser and the reader, so the two cannot drift.
  - Execution state: pending
- [ ] E-02 In `runner_shared.reconcile_item_on_interrupt`, branch on that sentinel BEFORE the `holds_work` computation and take the work-preserving outcome unconditionally: set `attempt["interrupted_at"]`/`["ended_at"]`, set `attempt["interrupt_reason"]` to the sentinel (on the ATTEMPT, never the item, per `render_stream._interrupt_reason_of`), set `item["status"] = "interrupted"`, set `recovery_next`, write the level-4 `stopped` record with `runner_stop.CERTAINTY_KNOWN`, snapshot dirty lane work if there is a lane and it is dirty exactly as the existing preserve arm does, `save_state_fn`, and append an `ipd-interrupted` event carrying a subevent distinguishing it from the menu-initiated preserve. Leave the `just-terminate-no-cleanup` arm and the menu's `clean-up-and-terminate` routing untouched, and update the function's docstring so its by-message description of the arms matches the new routing.
  - Depends on: E-01
  - Expected outcome: a `KeyboardInterrupt` carrying the sentinel leaves the item `interrupted` with an `ipd-interrupted` event on a CLEAN tree as well as a dirty one; the begin receipt is NOT unlinked and the attempt is NOT popped; `test_no_worktree_clean_repo_cleans_up` still passes unchanged because its message is the menu's, not the sentinel's.
  - Execution state: pending

### Task group 2: restore the coverage the trim removed

- [ ] E-03 Add to `tests/test_interrupt_reconcile.py` a behavioral test class for the TERMINAL RUNG that, for BOTH hosts (`oc_runipd` and `agy_runipd`, following the existing `HostBehavioralInterruptTests` pattern including `support.declare_execution_role(self)`), drives the real `execute_item` with a spawn that raises the message produced by the REAL `_terminal` callback (obtain it from `install_stop_triggers`/`runner_stop.SIGINT_LADDER` and `runner_stop.LEVEL_NAMES`, or by capturing the callback, rather than hand-writing the string) and asserts on persisted `state.json` and `events.jsonl` that the item is `interrupted`, that an `ipd-interrupted` event for that id6 exists, that the status is not in `runner_shared.SUCCESS_STATES`, and that no `ipd-cleaned-up-no-changes` event was emitted. Cover the CLEAN-tree case explicitly, since that is the half that fails today. Add a separate test asserting the ROUTING itself: that the message `_terminal` actually raises contains the E-01 sentinel, so a reword of `_terminal` fails here rather than silently restoring the bug (F-8). Do NOT mark any of it `slow`.
  - Depends on: E-02
  - Expected outcome: named tests that fail with the E-01/E-02 change reverted and pass with it applied, on both hosts, without the marker that hid the original regression.
  - Execution state: pending
- [ ] E-04 Add a regression test pinning that the interactive menu's OWN cleanup action is unaffected: a `KeyboardInterrupt("clean-up-and-terminate")` with NO sentinel, on a clean tree, still reaches the no-changes arm (item `queued`, attempt popped, begin receipt unlinked, `ipd-cleaned-up-no-changes` emitted), and that its message does not contain the sentinel. Reference `runner_stop`'s `INTERRUPT_ACTION_CLEANUP` in a comment so the asymmetry with E-02 is documented as deliberate consent rather than read as an inconsistency (F-7).
  - Depends on: E-02
  - Expected outcome: the legitimately destructive arm is proven intact and the deliberate/unrequested asymmetry is pinned, so a later reader cannot "unify" the two arms without a red test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE SHARED-CORE RULE. Both hosts' `execute_item` delegate to `runner_shared.execute_item_core`, and `87jnym`'s own Scope says the handler was added there so "both hosts get it once". A fix belongs in `runner_shared`, never duplicated into `oc_runipd` and `agy_runipd`; the `SUCCESS_STATES` comment in `runner_shared` records why, naming two hosts' constants that were "EQUAL BUT NOT IDENTICAL" and the one-sided edit that is "SILENT because no host-token diff, no import error and no type" error results.
- INTERRUPT REASON LIVES ON THE ATTEMPT, NOT THE ITEM. `render_stream._interrupt_reason_of` documents that every producing site writes `attempt["interrupt_reason"]` and sets only `item["status"]`, and that duplicating the field onto the item "is how the two copies come to disagree". A new reason must follow that shape.
- TESTS MUST DRIVE REAL CODE, NOT SOURCE TEXT. `87jnym`'s Concern records that the previous guard here was "a source-text pin ... satisfied by `install_stop_triggers` docstring prose", which stayed GREEN through the regression. `tests/test_interrupt_reconcile.py::HostBehavioralInterruptTests` is the established pattern: patch `driver_begin` and the host's spawn, raise a real `KeyboardInterrupt`, and assert on persisted `state.json` and `events.jsonl`.
- `support.declare_execution_role(self)` in `setUp` is required of tests in this area (every class in `tests/test_interrupt_reconcile.py` does it); `tests/test_role_declaration_guard.py` is what notices its absence.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml`'s `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. New tests here must NOT be `@pytest.mark.slow`, because that marker is precisely what let this contract rot invisibly (the item's own "WHY IT IS INVISIBLE TODAY").

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The item's cited node id cannot be run at all: `tests/test_runner_stop_triggers.py` was deleted. | `git log --oneline --diff-filter=D -- tests/test_runner_stop_triggers.py` -> `19313eed test: trim test suite from 9,136 to under 2,000 tests`; `ls tests/ \| grep -i stop` returns only `test_liftaudit_stop_halts_run.py`. |
| F-2 | The `running` root cause the item names IS fixed; do not re-fix it. | `reconcile_item_on_interrupt` has a live caller in `runner_shared.execute_item_core`'s `except KeyboardInterrupt as exc:` arm (the only call in `agent_workflows/` besides the definition and a `render_stream` docstring mention). Executed plan `87jnym` records the rewire. `python3 -m pytest tests/test_interrupt_reconcile.py tests/test_interrupt_attempt_metadata.py -o addopts='' -p no:randomly -q` -> `24 passed`. |
| F-3 | THE LIVE DEFECT. The terminal rung's message matches no sentinel, so it routes into the DEFAULT cleanup arm. | `runner_shared.install_stop_triggers`'s `_terminal` raises `KeyboardInterrupt(f"stop level {level} ({runner_stop.LEVEL_NAMES.get(level, 'unknown')}) requested by ...")`. With `runner_stop.SIGINT_LADDER == (1, 3, 4)`, that string is `stop level 4 (now-force) requested by signal pid=<n>`, and `"just-terminate-no-cleanup" in msg` is `False`. |
| F-4 | On a CLEAN tree that arm sets `queued`, not `interrupted`, and emits no `ipd-interrupted`. MEASURED end-to-end. | Probe driving real `oc_runipd.execute_item` with the exact `_terminal` string: clean tree -> `item status 'queued'`, events `['ipd-started', 'suite-baseline-unavailable', 'ipd-cleaned-up-no-changes']`. Dirty tree -> `'interrupted'` with `ipd-interrupted`. The deleted test's assertion fails on the clean half. |
| F-5 | `queued` defeats the spec-R19 gate, which is the user-visible harm. | `queued` is absent from `runner_shared.TERMINAL_STATES_CANONICAL`, which lists `interrupted`. `requeue_interrupted`'s docstring: without its gate "a force-interrupted item whose outcome the driver never established is re-run blindly, which is the exact failure spec R19 exists to prevent". A gate keyed on `interrupted` never fires for a `queued` item. |
| F-6 | A clean `git status` does NOT prove the turn did nothing, so the cleanup arm's premise is false for an UNREQUESTED stop. | The same arm already concedes this for commits: `87jnym`'s E-07 added the `starting_head` comparison after measuring that "`git status --porcelain` is EMPTY after a commit" and that treating it as nothing "destroys recovery state silently instead of failing loudly". A level-4 force stop kills the child mid-turn, so even `starting_head` equality leaves the outcome unestablished. |
| F-7 | The cleanup arm is nonetheless CORRECT for the interactive menu's own cleanup action, so it must not simply be deleted. | `runner_stop`'s `_sigint` raises `KeyboardInterrupt("clean-up-and-terminate")` for `INTERRUPT_ACTION_CLEANUP`, an operator who explicitly chose cleanup. `tests/test_interrupt_reconcile.py::test_no_worktree_clean_repo_cleans_up` pins `status == "queued"`, `attempts == []` and the receipt unlinked for that message. |
| F-8 | Nothing in `tests/` exercises the terminal rung or `install_stop_triggers` at all. | `grep -rn "install_stop_signal_handlers\|on_terminal\|SIGINT_LADDER" tests/` returns no match; the only `SIGINT` mention anywhere in `tests/` is in `tests/test_oc_runipd.py`. The `_terminal`-message-to-arm routing of F-3 is therefore wholly uncovered. |
| F-9 | Sibling backlog `wqk5s2` covers the SAME deleted file and remains live; this plan must not silently absorb its other half. | `wqk5s2` (`open`, `bug`, `Blocks-Release: next`) names both this node id and `SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint` (`KeyError: 'stopped'`). The SIGTERM half is level 3, a different rung, and is explicitly OUT of this plan's scope. |

## Proposed changes (ordered, validatable)

1. Introduce ONE shared sentinel for an unrequested force stop and raise it from `_terminal`, so the terminal rung is distinguishable from the menu's deliberate cleanup (F-3, F-7). Keep the human-readable level/requester text in the message; add the sentinel to it rather than replacing it, so the existing operator-facing string is not lost.
2. In `reconcile_item_on_interrupt`, route that sentinel to the work-preserving outcome UNCONDITIONALLY, independent of `holds_work`: item `interrupted`, `recovery_next`, a `stopped` record, and an `ipd-interrupted` event. Do NOT change the `just-terminate-no-cleanup` arm and do NOT change what the menu's `clean-up-and-terminate` does (F-4, F-5, F-6, F-7).
3. Cover the contract behaviorally on both hosts, driving `execute_item` with the REAL `_terminal` message, plus a routing pin so a reword of `_terminal` fails a test instead of silently restoring the bug (F-8).
4. Pin that the menu's own cleanup path still cleans up, so change 2 is proven not to have broken the arm that is legitimately destructive (F-7).

## Deferred / out of scope (with reason)

- The `SigtermTests` level-3 `KeyError: 'stopped'` failure. A different rung with different semantics; `wqk5s2` stays live and gated for it, and folding it in here would make this plan multi-concern.
- Reviving `tests/test_runner_stop_triggers.py` or any other file the `19313eed` trim removed. The trim was a deliberate maintainer change; this plan restores the one CONTRACT it dropped, in the file that already owns interrupt reconciliation, and does not relitigate the trim.
- The slow-marker visibility gap (`-m 'not slow'` hiding whole contracts). Owned by `xuc9v0`. This plan's own tests are deliberately NOT slow-marked, which is the local mitigation.
- Any change to the exit-130/143 mapping. The deleted test also asserted a nonzero exit; that half is unaffected by this change and both hosts' `main` still `return 143 if is_sigterm else 130`.

## Scope check

- Over-scope: none. Both declared paths are touched: `agent_workflows/runner_shared.py` holds `install_stop_triggers`, `reconcile_item_on_interrupt` and `execute_item_core`, and `tests/test_interrupt_reconcile.py` already owns this function's behavioral coverage on both hosts.
- Under-scope: none. No spec file is amended (see Spec / documentation sync), `runner_stop.py` is NOT edited because the sentinel is raised by `runner_shared`'s own `_terminal` callback, and no host file needs editing because the handler lives in the shared core.

## Required tests / validation

1. `python3 -m pytest tests/test_interrupt_reconcile.py tests/test_interrupt_attempt_metadata.py -o addopts='' -p no:randomly` BEFORE any edit, as the baseline, with the summary pasted.
2. The failing-first probe from F-4 re-run before the fix (clean tree -> `queued`) and after (clean tree -> `interrupted`), both outputs pasted, so the change is shown to fix a measured defect rather than to satisfy a new test.
3. The new tests from E-03/E-04, run by name and green.
4. NON-VACUITY, bidirectional: with the E-01/E-02 product change reverted, the new terminal-rung tests must FAIL; restored, they must pass. Paste both directions.
5. Bare `python3 -m pytest` with the `N passed` summary line pasted, compared against a baseline taken at execution HEAD, with any pre-existing failure named rather than absorbed.
6. `aw sanitize --agent` clean, and `aw ipd lint` conforming for this plan at `--phase pre-transition`.

## Spec / documentation sync

N/A with reason: no `.spec.md` file is amended, so `Scope-Paths` declares none. The behavior changed here is what `runner_stop`'s and `install_stop_triggers`' own docstrings ALREADY promise ("`execute_item`'s `except KeyboardInterrupt` marks the in-flight item `interrupted`, appends `ipd-interrupted`, reclaims lanes", and the terminal rung "is what preserves ... `execute_item`'s `interrupted` bookkeeping that Phases 3-4 rely on"). This plan makes the code match that documented contract, so no contract text needs weakening or widening. `reconcile_item_on_interrupt`'s own docstring DOES describe its arms by message and must be updated in place as part of E-02, since it would otherwise describe routing that no longer exists.

## Open questions

### OQ-01: Should the unrequested force stop preserve work on a clean tree, or clean up and re-queue?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, preserve and record `interrupted`. Three independent citations agree. (1) The contract the deleted test asserted is explicit that `interrupted` is the required outcome and that what "must never happen is the item being left `running` or claimed successful"; a `queued` item with its attempt popped and its receipt unlinked is indistinguishable from never-run, which is a stronger form of the same error. (2) `requeue_interrupted`'s docstring states the spec-R19 gate exists so a force-interrupted item of unestablished outcome is not "re-run blindly", and that gate keys on `interrupted`, so `queued` bypasses the very safeguard designed for this case. (3) `87jnym`'s E-07 already established, with a measurement, that a clean `git status` is not evidence of no work and that guessing wrong here "destroys recovery state silently instead of failing loudly". The asymmetry with the menu's cleanup action is principled rather than inconsistent: there the operator EXPLICITLY asked for cleanup, so destroying recovery state is consented; at the terminal rung nobody chose it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TWO parts. (a) The sentinel constant's definition pasted, plus every reference to it in `agent_workflows/` from a fresh `grep -rn`, showing it defined ONCE and referenced by both `_terminal` and `reconcile_item_on_interrupt` (so E-01 and E-02 cannot drift). (b) The message `_terminal` now produces, printed by CONSTRUCTING it through the real code path (capture the callback or re-evaluate the same expression with `runner_stop.SIGINT_LADDER[-1]` and `runner_stop.LEVEL_NAMES`), showing BOTH that it still contains `stop level 4 (now-force)` and the requester text AND that it now contains the sentinel. A hand-typed string is not acceptable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: THE FAILING-FIRST PAIR, both pasted. Re-run the F-4 probe (real `oc_runipd.execute_item`, real `_terminal` message, clean tree and dirty tree) BEFORE the E-02 edit and AFTER it. Before must reproduce `status 'queued'` with `ipd-cleaned-up-no-changes` and no `ipd-interrupted` on the clean tree; after must show `status 'interrupted'` with an `ipd-interrupted` event on BOTH trees, the begin receipt still present, and the attempt still in `item["attempts"]`. Also paste the `stopped` record written on the clean-tree run, showing level 4 and `CERTAINTY_KNOWN`, and the updated docstring text showing it describes the new routing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: THREE parts. (a) `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts='' -p no:randomly -v` with the new terminal-rung tests green and named, for BOTH hosts, and the routing pin green. (b) NON-VACUITY, both directions shown: with the E-01/E-02 product change reverted (state exactly how), paste the FAILING output naming these tests and the `'queued' != 'interrupted'` style assertion, then restore and paste them passing. (c) Proof the new tests are reachable in the DEFAULT suite, i.e. they appear in a BARE `python3 -m pytest tests/test_interrupt_reconcile.py` collection rather than being deselected by `-m 'not slow'`, which is the specific failure mode that hid this contract.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the new menu-cleanup regression test green BY NAME, plus the PRE-EXISTING `tests/test_interrupt_reconcile.py::InterruptReconcileNoWorktreeUnitTests::test_no_worktree_clean_repo_cleans_up` green and UNMODIFIED (paste `git diff` for that test showing no change to it), proving the destructive arm was preserved rather than adjusted to fit. Then the FULL required-validation set: the baseline from Required tests item 1 pasted, a bare `python3 -m pytest` summary line pasted and compared to a baseline at execution HEAD with any pre-existing failure named, `aw sanitize --agent` output, and `aw ipd lint --phase pre-transition` for this plan reported conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; the executing agent must not self-approve. Execution follows the repository execution contract: commit only the paths this plan declares in `Scope-Paths`, through `aw commit <plan> -- <paths>`, never `git add -A` or a bare/`-a` commit, and never push. Test results must be pasted as ACTUAL runner output; no validation item may be marked verified from intent. The product change (E-01, E-02) and its tests (E-03, E-04) belong in the same change so the contract is never asserted without coverage.

Because E-02 changes what a Ctrl-C does to recorded state, the executor must confirm the ASYMMETRY is preserved rather than smoothed away: the menu's explicit cleanup action stays destructive, and only the UNREQUESTED terminal rung becomes work-preserving. If V-04 shows `test_no_worktree_clean_repo_cleans_up` changed or failing, that is a scope breach, not a test to update.

Post-gate lifecycle: after every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` via the tooled transition. Backlog `pe7g6r` is set `graduated` by the runner on verification of this authoring turn; do NOT set it `done` here. Note for whoever closes it: `pe7g6r`'s `Blocks-Release: next` gate is inherited by this plan, so the handoff is provable, and sibling `wqk5s2` remains live for the SIGTERM half of the same deleted file and must not be closed by this plan.

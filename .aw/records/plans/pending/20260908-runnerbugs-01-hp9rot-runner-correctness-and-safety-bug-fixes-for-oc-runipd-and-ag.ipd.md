# IPD: Runner correctness and safety bug fixes for oc_runipd and agy_runipd

- Date: 2026-09-08
- Kind: child
- Concern: bugs/correctness (assess-bugs)
- Scope: `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/runner_stop.py`, `agent_workflows/runner_shutdown.py`, and regression tests in `tests/`
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, agent_workflows/runner_shutdown.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_stop.py, tests/test_runner_shutdown.py
- Item-Dependencies: none
- Status: to-review
- Set: runnerbugs
- Order: 1
- Highest E allocated: 12
- Author: antigravity
- Id: hp9rot

## Workflow history

- 2026-09-08 to-review (antigravity): /assess bugs: assessed the bugs/correctness concern across oc_runipd.py and agy_runipd.py; identified 15 findings (2 Critical, 8 High, 5 Medium/Low); proposed 12 ordered, validatable changes across verification gating, process lifecycle, signal handling, and queue initialization. Wrote this IPD and run record under workflow-artifacts/assess-bugs/20260908-211500/.

## Goal

Resolve critical correctness, signal lifecycle, process isolation, and queue gating defects in `oc_runipd.py`, `agy_runipd.py`, and shared runner infrastructure (`runner_stop.py`, `runner_shutdown.py`). Ensure independent verification fails closed rather than auto-finalizing on `CORRECTION_REQUIRED`, prevent infinite loops on unhandled tool identity mismatch, fix Antigravity level-3 safe checkpoint matching, prevent in-run executed plans from permanently blocking downstream items, guarantee process group cleanup without leaving orphaned background grandchildren, and accurately track ending repository state for backlog carrier detection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Verification gate and disposition correctness

- [ ] E-01 Harden the verifier outcome parser in `agent_workflows/oc_runipd.py:6637-6648` and `agent_workflows/agy_runipd.py:3687-3698` to whitelist `VERIFIED` (with no `NOT` prefix) as the only passing verdict, treating `CORRECTION_REQUIRED`, `BLOCKED`, `NOT CONFORMING`, unrecognized verdicts, and missing or corrupt outcome files as `unverified` and setting disposition `partial`.
  - Depends on: none
  - Expected outcome: An independent verification turn that reports `CORRECTION_REQUIRED` or fails to write an outcome JSON file is never promoted to `verified` or auto-finalized.
  - Execution state: pending

- [ ] E-02 Remove `substantially-complete` from `EXECUTION_SUCCESS_STATES` in `agent_workflows/oc_runipd.py:337` and `agent_workflows/agy_runipd.py:409` (backlog `rwibaz`), ensuring that a refused finalize on unchecked E/V checklists reports incomplete and exits nonzero rather than falsely declaring `COMPLETED` and exiting 0 while stranding lane branches.
  - Depends on: none
  - Expected outcome: Runs with unfinalized items exit nonzero with status reflecting unfinished work instead of falsely claiming completion.
  - Execution state: pending

- [ ] E-03 In `execute_item` (`oc_runipd.py` and `agy_runipd.py`), update `attempt["ending_head"]` and `attempt["ending_status"]` to match `git_head(repo)` and `git_status(repo)` upon successful completion of `integrate_lane_branch()`, allowing `collect_earned_paths` to discover non-IPD backlog carriers from merged lane commits.
  - Depends on: none
  - Expected outcome: Backlog items declaring non-IPD code or spec carriers are successfully closed after lane integration in isolated mode.
  - Execution state: pending

### Task group 2: Signal handling and stop lifecycle parity

- [ ] E-04 In `agent_workflows/agy_runipd.py:4414-4419`, add the missing `raise` in `except ToolIdentityError:` matching `oc_runipd.py:7403-7409`, terminating the run immediately on tool identity mismatch instead of looping infinitely.
  - Depends on: none
  - Expected outcome: `ToolIdentityError` aborts the run cleanly with exit code 2 and an explanatory diagnostic on stderr.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/runner_stop.py:896-904`, update `is_agy_safe_checkpoint` to accept both `"event": "step_update"` and `"type": "step_update"`, restoring level-3 safe checkpoint stop detection for real Antigravity streaming events.
  - Depends on: none
  - Expected outcome: `is_agy_safe_checkpoint` returns `True` on real Antigravity step completed events, unblocking level-3 graceful stops.
  - Execution state: pending

- [ ] E-06 In both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, do not swallow `KeyboardInterrupt` during independent verification turns, and catch `runner_stop.StopNowForce` and `runner_stop.StopAtCheckpoint` during the verification turn to record stop metadata on the item and re-raise.
  - Depends on: none
  - Expected outcome: Pressing Ctrl-C or issuing level-3/level-4 stops during verification stops the run, preserves worktrees, and exits with expected signal codes rather than ignoring the interrupt.
  - Execution state: pending

- [ ] E-07 In `_record_checkpoint_stop` and `_record_forced_stop` (`oc_runipd.py:5219, 5254` and `agy_runipd.py:2650, 2685`), inspect `work_dir` (when isolation is active) rather than `state["repo"]` for git status.
  - Depends on: none
  - Expected outcome: Durable stop events record accurate working tree dirty status when stopped inside an isolated worktree.
  - Execution state: pending

### Task group 3: Queue initialization and selector safety

- [ ] E-08 In `initialize_run` (`oc_runipd.py:2978-2980` and `agy_runipd.py:2011-2013`), preserve on-disk terminal status (`executed`, `partial`, `blocked`, etc.) instead of coercing already-executed plans to `reviewed`, preventing dependency deadlock for downstream execution plans.
  - Depends on: none
  - Expected outcome: Plans already executed on disk retain `executed` in the queue, satisfying `executed:<id6>` dependencies for downstream plans.
  - Execution state: pending

- [ ] E-09 In `execute_item` (`oc_runipd.py:6927-6940` and `agy_runipd.py:3967-3980`), guard the auto-approve execution mutation so that it does not mutate `item["action"] = "execute"` when the run was invoked with `--action review`.
  - Depends on: none
  - Expected outcome: `aw oc run --action review --full-auto` reviews and auto-approves plans without executing code.
  - Execution state: pending

- [ ] E-10 In `expand_selectors` (`oc_runipd.py:2356-2363` and `agy_runipd.py:1646-1654`), preserve `"kind": rec.kind` when parsing path selectors so that preflight `--action` checks do not misclassify orchestrators.
  - Depends on: none
  - Expected outcome: Selecting an orchestrator by file path with `--action orchestrate` passes preflight validation without error.
  - Execution state: pending

### Task group 4: Worktree isolation and watchdog cleanup

- [ ] E-11 In `reclaim_lanes_on_interrupt` (`agy_runipd.py:1190-1202` and `oc_runipd.py:1845-1857`), invoke `worktree_lease.teardown_worktree(repo, handle, force=True)` when the operator selects `discard` (`d`).
  - Depends on: none
  - Expected outcome: Choosing discard on an interrupted lane removes the worktree directory from disk while keeping the branch ref.
  - Execution state: pending

- [ ] E-12 In `execute_item` (`oc_runipd.py:6441-6467` and `agy_runipd.py:3518-3544`), ensure `StallTimeout` handling records `item["preserved_worktree"]` and invokes dirty work snapshotting before returning.
  - Depends on: none
  - Expected outcome: Stalled turns running in isolated worktrees record their preserved lane identity in `state.json` and persist dirty uncommitted work.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Runner code lives in `agent_workflows/oc_runipd.py` (OpenCode driver) and `agent_workflows/agy_runipd.py` (Antigravity driver).
- Shared runner modules: `agent_workflows/runner_stop.py` (signals, graceful wind-down), `agent_workflows/runner_shutdown.py` (process group reaping, clean shutdown), `agent_workflows/runner_shared.py` (manifests, dependency graph, statusline, selectors).
- IPD schema: `.aw/system/workflows/assess/templates/ipd.md`, governed by `agent_workflows/ipd_schema.py` and linted by `agent_workflows/ipd_lint.py`.
- Suite execution contract: `python3 -m pytest` bare (parallel via xdist, quiet, worksteal). Never add `-n0` or `-p no:randomly`.
- Concurrency contract: path-scoped commits (`git commit -m msg -- <paths>`).

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Evidence | Finding |
|---|---|---|---|---|---|---|
| BUG-01 | CRITICAL | C:Low U:Low S:Low F:Low; Overall:Low | QA / Data Integrity | Verifier Gating | `oc_runipd.py:6637-6648`, `agy_runipd.py:3687-3698` | Permissive verification parser treats `CORRECTION_REQUIRED` as `verified` because it only checks for `BLOCKED` and `NOT CONFORMING`. Also defaults missing outcome files to `verified` if exit code is 0. Auto-finalizes and merges flawed code. |
| BUG-02 | CRITICAL | C:Low U:Low S:Low F:Low; Overall:Low | Software Engineer | Tool Identity | `agy_runipd.py:4414-4419` | Missing `raise` in `except ToolIdentityError:` in `run_queue`. Caught exception leaves item `running` and loops indefinitely instead of aborting. |
| BUG-03 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Systems Engineer | Stop Checkpoints | `runner_stop.py:896-904`, `agy_runipd.py:2861` | Schema mismatch: `is_agy_safe_checkpoint` checks `event.get("type") == "step_update"`, but Antigravity CLI emits `{"event": "step_update"}`. Fails 100% of real checkpoints. |
| BUG-04 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | QA Engineer | Queue Init & Deps | `oc_runipd.py:2978-2980`, `agy_runipd.py:2011-2013`, `oc_runipd.py:3375-3383` | In-run executed plans are coerced to status `reviewed` during queue initialization. Execution items requiring `EXECUTION_SUCCESS_STATES` (`executed`, `substantially-complete`) fail dependency checks and remain deadlocked. |
| BUG-05 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Reliability | Signal Handling | `oc_runipd.py:6649-6651`, `agy_runipd.py:3699-3701` | `KeyboardInterrupt` caught and swallowed during verifier turn. Run continues, merges turn 1 code, and launches next item instead of exiting. |
| BUG-06 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Reliability | Stop Handling | `oc_runipd.py:6630-6665`, `agy_runipd.py:3655-3701` | `StopNowForce` and `StopAtCheckpoint` unhandled during verification turn. Bubbles unhandled to `run_queue`, leaving item `running` and causing exit code 1. |
| BUG-07 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Data Integrity | Backlog Closes | `oc_runipd.py:6496, 6828-6865`, `agy_runipd.py:3562, 3875-3910` | `ending_head` recorded before lane integration and not updated after merge. `git diff starting_head..ending_head` sees no diff, refusing non-IPD backlog closes. |
| BUG-08 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Security & Safety | CLI Flags | `oc_runipd.py:6927-6940`, `agy_runipd.py:3967-3980` | `--action review --full-auto` unconditionally mutates `item["action"] = "execute"` upon auto-approval, executing plans when user requested review only. |
| BUG-09 | HIGH | C:Low U:Low S:Low F:Low; Overall:Low | Data Integrity | Finalize & Success | `oc_runipd.py:337`, `agy_runipd.py:409` (backlog `rwibaz`) | `substantially-complete` in `EXECUTION_SUCCESS_STATES`. A refused finalize on unchecked E/V checkboxes marks item `substantially-complete` and exits 0 claiming COMPLETED while stranding lane commits. |
| BUG-10 | HIGH | C:Med U:Low S:Low F:Low; Overall:Med | Systems Engineer | Process Reaping | `runner_shutdown.py:181-184, 487-490` | If parent process exits while background grandchild processes (test runners, subagents) are alive, `poll() is not None` skips `killpg()`, orphaning grandchildren to PID 1. |
| BUG-11 | MEDIUM | C:Low U:Low S:Low F:Low; Overall:Low | Reliability | Watchdog / Recovery | `oc_runipd.py:6441-6467`, `agy_runipd.py:3518-3544` | Early `return` on `StallTimeout` bypasses `item["preserved_worktree"]` recording and dirty lane snapshotting. |
| BUG-12 | MEDIUM | C:Low U:Low S:Low F:Low; Overall:Low | Concurrency | StallWatchdog | `oc_runipd.py:710-713, 5949-5958`, `agy_runipd.py:778-782, 3070-3075` | Double-termination race: watchdog thread and main thread both invoke `terminate_process` on the same `Popen` object after `join(1.0)` timeout. |
| BUG-13 | MEDIUM | C:Low U:Low S:Low F:Low; Overall:Low | Software Engineer | Lane Teardown | `agy_runipd.py:1190-1202`, `oc_runipd.py:1845-1857` | Operator choosing `discard` (`d`) on lane reclamation prompt prints message but never calls `teardown_worktree`. Worktree remains on disk. |
| BUG-14 | MEDIUM | C:Low U:Low S:Low F:Low; Overall:Low | Diagnostics | Stop Recording | `agy_runipd.py:2650, 2685`, `oc_runipd.py:5219, 5254` | `_record_checkpoint_stop` and `_record_forced_stop` probe `repo` instead of `work_dir`, reporting clean git state when edits exist in the lane. |
| BUG-15 | MEDIUM | C:Low U:Low S:Low F:Low; Overall:Low | Architecture | Selectors | `oc_runipd.py:2356-2363`, `agy_runipd.py:1646-1654` | `expand_selectors` omits `kind` when parsing plan file paths, causing preflight `--action` check to misclassify orchestrators. |

## Proposed changes (ordered, validatable)

1. Fix verifier outcome evaluation to whitelist `VERIFIED` and treat `CORRECTION_REQUIRED` and missing outcomes as `unverified` / `partial` (BUG-01).
2. Remove `substantially-complete` from `EXECUTION_SUCCESS_STATES` so unfinalized items fail the run (BUG-09).
3. Update `ending_head` and `ending_status` after lane integration in isolated mode so backlog carrier diffs are detected (BUG-07).
4. Add missing `raise` for `ToolIdentityError` in `agy_runipd.py` (BUG-02).
5. Support `"event": "step_update"` in `is_agy_safe_checkpoint` (BUG-03).
6. Handle `KeyboardInterrupt`, `StopNowForce`, and `StopAtCheckpoint` properly during verification turns in both runners (BUG-05, BUG-06).
7. Probe `work_dir` for git status during stop recording in isolated mode (BUG-14).
8. Preserve terminal statuses during queue initialization so executed plans do not block dependents (BUG-04).
9. Guard full-auto execution mutation against `--action review` (BUG-08).
10. Populate `kind` in `expand_selectors` when resolving file paths (BUG-15).
11. Call `teardown_worktree` when operator chooses `discard` in `reclaim_lanes_on_interrupt` (BUG-13).
12. Record `preserved_worktree` and snapshot dirty work in `StallTimeout` handler (BUG-11).

## Deferred / out of scope (with reason)

- BUG-10 (process group grandchildren orphaned on direct child exit): Remediation Risk is Medium on Complexity/Functionality due to platform differences and potential signal escalation hazards across diverse process tree structures. Deferred to a dedicated runner shutdown hardening pass.
- BUG-12 (concurrent double-termination in StallWatchdog): Low operational impact because `_close_process_streams` handles closed streams gracefully. Deferred to keep this IPD focused.

## Scope check

- Over-scope: none; confined to runner and stop/lifecycle modules.
- Under-scope: covers both runners symmetrically (`oc_runipd` and `agy_runipd`).

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd.py`
- `python3 -m pytest tests/test_agy_runipd_cli.py`
- `python3 -m pytest tests/test_runner_stop.py`
- `python3 -m pytest tests/test_runner_shutdown.py`
- Bare test suite: `python3 -m pytest`
- `python3 -m agent_workflows ipd lint --phase pre-transition <this-plan>`

### Per-item evidence matrix

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m pytest tests/test_oc_runipd.py -k test_verifier_gate` | Verifier output with `CORRECTION_REQUIRED` | Outcome is `unverified`, disposition is `partial`, finalize is NOT called | Flawed code is finalized or merged |
| E-02 | `python3 -m pytest tests/test_oc_runipd.py -k test_substantially_complete_fails` | Plan with unchecked E/V checkboxes | Run exits nonzero, status is not COMPLETED | Run reports COMPLETED and exits 0 |
| E-03 | `python3 -m pytest tests/test_runner_backlog_close.py` | Isolated lane run addressing backlog with code carriers | Backlog item closes with carriers found | Backlog item close is refused |
| E-04 | `python3 -m pytest tests/test_agy_runipd_cli.py -k test_tool_identity_aborts` | Mismatched child tool identity | Runner raises ToolIdentityError and terminates | Runner enters infinite execution loop |
| E-05 | `python3 -m pytest tests/test_runner_stop.py -k test_agy_checkpoint` | Streaming event `{"event": "step_update", "state": "DONE"}` | `is_agy_safe_checkpoint` returns True | Returns False |
| E-06 | `python3 -m pytest tests/test_runner_stop.py -k test_verifier_stop` | Level 3/4 stop during verification turn | Item stopped metadata recorded, exit code preserved | Item left in `running` status |
| E-07 | `python3 -m pytest tests/test_runner_stop.py -k test_stop_isolated_git_status` | Stop with dirty work in isolated worktree | Recorded git state lists modified files | Recorded git state claims clean tree |
| E-08 | `python3 -m pytest tests/test_runner_item_dependencies.py -k test_in_run_executed` | Queue containing an executed plan and a dependent plan | Dependent plan satisfies dependency and runs | Dependent plan blocked with 'needs executed' |
| E-09 | `python3 -m pytest tests/test_oc_runipd.py -k test_review_action_full_auto` | `--action review --full-auto` with approved review | Plan is auto-approved, not executed | Plan action mutated to execute |
| E-10 | `python3 -m pytest tests/test_runner_shared.py -k test_path_selector_kind` | Path selector to orchestrator IPD | Manifest entry retains `kind: orchestrator` | Kind is None |
| E-11 | `python3 -m pytest tests/test_oc_runipd.py -k test_discard_lane_reclaim` | Operator chooses `discard` at interrupt prompt | Worktree directory is removed | Worktree remains on disk |
| E-12 | `python3 -m pytest tests/test_stall_progress.py -k test_stall_preserved_worktree` | Stall timeout in isolated worktree | `item["preserved_worktree"]` is populated | Key missing from item |

## Spec / documentation sync

- Spec `25kzda` 2.6 (`--action` legality), 2.9 (queue dependency evaluation), 4.6 (refused finalize retry).
- Spec `c4gd2h` R7-R9 (safe checkpoint detection).

## Open questions

### OQ-01: Should `substantially-complete` retry immediately or leave for operator retry?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: In this bugfix IPD, removing `substantially-complete` from `EXECUTION_SUCCESS_STATES` ensures the run fails closed when finalize is refused. Full automated retry and correction packet emission is tracked under backlog item `rwibaz` and Set `finalback`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests proving `CORRECTION_REQUIRED` results in `unverified` and prevents auto-finalize.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test showing refused finalize exits nonzero and does not report `Outcome: COMPLETED`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test showing `ending_head` matches main HEAD post-merge and backlog closes with code carriers.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test showing `ToolIdentityError` raises and aborts rather than looping.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Test showing `is_agy_safe_checkpoint` returns True for `{"event": "step_update"}` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Test showing Ctrl-C and stops during verification turn are recorded and handled.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Test showing `git_status` is read from `work_dir` when isolated.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Test showing queue initialization preserves `executed` status on disk and passes dependency checks.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: Test showing `--action review --full-auto` never executes plans.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: Test showing path selector preserves `kind: orchestrator`.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: Test showing worktree directory is deleted when operator selects discard.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: Test showing `StallTimeout` records preserved worktree path and snapshots dirty edits.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD addresses confirmed bugs in runner correctness, process lifecycle, signal handling, and queue initialization. It requires human review and explicit approval before any execution. Under the execution contract, implementation must proceed in isolated worktrees with path-scoped commits and full pytest test verification.

# IPD: Isolate production checks and reconcile backlog graduation gates

- Date: 2026-10-12
- Kind: child
- Concern: Investigation into runner failures across active multi-shard runs (`run-20261012T005606Z-2321569`, `run-20261012T005617Z-2321742`, `run-20261012T005641Z-2321995`, `run-20261012T005650Z-2322198`) and historical execution runs revealed distinct failure classes. In the active runs, 10 backlog graduation items failed with `fail-gate`: (1) Multi-runner concurrent shard race condition (`2rm0gz`, `iosmvn`), where `production_checks.backlog_graduate_count` iterates over all plans in `repo` against a stale runner-startup baseline, misattributing plans concurrently committed to `main` by peer runner shards as unlinked new plans authored during the current item's turn; (2) Re-running pre-graduated or already-executed backlog items (`ariaau`, `ildjse`, `h0tiaw`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`), where backlog items remained open despite their handoff plans having already been authored and executed under earlier Sets; when the agent correctly declined to duplicate finished work, `existing_handoff_plans` failed to inspect `executed/`, producing a false "0 linked IPDs" refusal. In addition, historical `fail-verify` outcomes (`76ic0k`, `9m4ujh`, `5poaqh`, `uxb0tz`, `3vh74b`) were singleton safety catches (where verifiers legitimately caught real test/lint/invariant regressions or Section 223 partial stops, such as catching unexpected `ast.parse` calls in runner test suites) rather than runner crashes; once their filed defect backlog items (`jahjj4`, `z9pfrk`) were executed, those singleton issues were permanently resolved. This plan implements strict production check isolation to eliminate cross-runner races and reconciles backlog handoff checks to recognize executed handoffs.
- Scope: IN: (1) update `production_checks.backlog_graduate_count` and `production_checks.spec_plan_count` to accept explicit `new_plan_paths` / `new_plan_ids` (passed from `runner_shared.py`), or discover new plans strictly from the turn's lane status and commits, eliminating repository-wide filesystem iteration against a stale baseline; (2) update `production_checks.existing_handoff_plans` and `production_checks.backlog_graduate_count` to recognize plans in `executed/` (and terminal states) so that pre-satisfied or already-executed backlog items are recognized as cleanly graduated and do not fail with false "0 linked IPDs" refusals; (3) update `runner_shared.py` backlog production verification callers to pass lane-discovered new plan paths directly to `production_checks.backlog_graduate_count`; (4) add comprehensive regression test suites in `tests/test_backlog_production.py` and `tests/test_production_resume_handoff.py` validating that concurrent peer plan additions do not cause attribution failures, and already-executed handoffs pass cleanly; (5) document root causes, singleton explanations, and prevention rationale in the record. OUT: changes to the execution verifier prompt or verdict schema; changes to `aw backlog set` transition semantics; modifications to external runner hosts.
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_backlog_production.py, tests/test_production_resume_handoff.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: failfix
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: d52x8b

## Workflow history

- 2026-10-12 draft (Antigravity): created from investigation of active runner shard failures in `aw runs --active -s`.
- 2026-10-12 to-review (Antigravity): authored complete plan addressing multi-shard race conditions, pre-graduated backlog false rejections, and failure mode analysis.

## Goal

Isolate runner production gate checks from concurrent peer-runner repository changes and recognize pre-executed backlog handoffs, ensuring multi-shard runner execution never fails with false `BACKLOG-GRADUATE-COUNT` refusals.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Characterization and baseline (before any edit)

- [ ] E-01 Record pre-edit test baseline and characterize failure modes. Run `python3 -m pytest tests/test_backlog_production.py tests/test_production_resume_handoff.py` and record the summary. Create a reproduction test fixture demonstrating: (a) multi-runner race condition where a peer runner commits a new plan `p_peer` with `From-Backlog: peer_item` while the current item `curr_item` runs, triggering false condition (b) refusal in `backlog_graduate_count`; (b) pre-executed backlog item where linked plans reside in `.aw/records/plans/executed/`, triggering false condition (a) "0 linked IPDs" refusal when 0 new plans are authored.
  - Depends on: none
  - Expected outcome: reproduction cases fail at the baseline commit, demonstrating both root causes cleanly in isolated test fixtures.
  - Execution state: pending

### Task group 2: Isolate production checks from concurrent runner commits

- [ ] E-02 Scope `production_checks.backlog_graduate_count` and `spec_plan_count` to lane-produced plans. In `agent_workflows/production_checks.py`, update `backlog_graduate_count` to accept `new_plan_paths: Sequence[Path] | None = None` and `new_plan_ids: Sequence[str] | None = None`. If provided, inspect only those candidate plans rather than calling `_ce._iter_plan_ipds(repo)`. When `new_plan_paths` is not explicitly passed, inspect only plans modified or untracked in `target_tree` (`git status --porcelain`) rather than scanning all plans across the repository against a stale process-start baseline. Apply the identical isolation pattern to `spec_plan_count`.
  - Depends on: E-01
  - Expected outcome: newly committed plans from other branches or peer runners never enter `unlinked_new_plans`, eliminating cross-runner race conditions.
  - Execution state: pending

### Task group 3: Reconcile pre-graduated and executed backlog handoffs

- [ ] E-03 Support executed handoff recognition in `existing_handoff_plans` and `backlog_graduate_count`. In `agent_workflows/production_checks.py`, update `existing_handoff_plans` to accept `include_executed: bool = True` (or inspect `.aw/records/plans/executed/`). In `backlog_graduate_count`, when `all_linked` has active plans or when all linked plans are in `executed/` (and carry matching `From-Backlog`), accept the count as satisfied without demanding redundant duplicate plans. When an item has already executed all linked plans and 0 new plans are written, return clean findings rather than `BACKLOG-GRADUATE-COUNT`.
  - Depends on: E-02
  - Expected outcome: backlog items whose work is already executed under an existing Set pass `backlog_graduate_count` without false 0-plan rejections.
  - Execution state: pending

### Task group 4: Wire runner production caller and lane discovery

- [ ] E-04 Wire lane discovery paths in `runner_shared.py`. In `agent_workflows/runner_shared.py` (around line 38450), pass `new_plan_paths=new_produced_paths` and `new_plan_ids=[p_id for p_id, _p in new_produced_plans]` into `_pc.backlog_graduate_count`. Ensure that `new_produced_paths` and `existing_linked_plans` are populated from the lane worktree or recent turn commit, never incorporating uncommitted or concurrent changes from other checkouts.
  - Depends on: E-03
  - Expected outcome: runner passes turn-scoped paths to verifiers, sealing the isolation boundary.
  - Execution state: pending

### Task group 5: Regression suite and documentation sync

- [ ] E-05 Add regression tests in `tests/test_backlog_production.py` and `tests/test_production_resume_handoff.py`. Add unit and integration tests covering: (1) multi-runner race condition where unlinked peer plans exist in `repo` but are not in `new_plan_paths` (must pass); (2) pre-executed backlog handoff recognition where all linked plans are in `executed/` (must pass); (3) invalid unlinked plans authored in the turn itself (must still be caught and rejected); (4) second Set introduction in the turn itself (must still be caught and rejected). Run the full project test suite `python3 -m pytest` bare to confirm zero regressions.
  - Depends on: E-04
  - Expected outcome: all new test cases pass, reproduction cases from E-01 pass, full test suite passes with no regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Isolation requirement: always work and test in an isolated worktree under `.aw/worktrees/<name>`, never in `main` (`GEMINI.md` Rule 1).
- Bare test execution: run `python3 -m pytest` bare; never pass `-n0`, an extra `-q`, or `-p no:randomly` (`GEMINI.md` Rule 5).
- Test outcomes, not code structure: test observable behavior and outcomes; never inspect AST or source code structure (`AGENTS.md`, GUIDING_PRINCIPLES P16).
- Commit via `aw commit failfix -- <paths>` and merge to `main` under `aw integration-lock` (`GEMINI.md` Rule 4).
- Cite code by SYMBOL (`module.function`) or by quoted content string, with line numbers appended only to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Topic | Location | Description |
|---|---|---|---|---|
| F-01 | HIGH | Race condition | `production_checks.backlog_graduate_count` | `backlog_graduate_count` iterates over all plans in `repo` via `_ce._iter_plan_ipds(repo)`. Any plan not in `baseline_ids` is assumed to have been created by the current turn. When multiple runner shards run concurrently in parallel worktrees, plans merged by peer shards into `main` are misattributed to the current item, causing `BACKLOG-GRADUATE-COUNT` refusal (observed on `2rm0gz` attributing `jykyqb`, `ml7b9e`; `iosmvn` attributing `k6clui`). |
| F-02 | HIGH | False rejection | `production_checks.existing_handoff_plans` | `existing_handoff_plans` only inspects pending plans (`draft`, `to-review`, `reviewed`, `approved`, `implementing`) and ignores `executed/`. When an already-executed backlog item is processed by a graduation runner, the agent correctly refuses to author duplicate plans; however, because `all_linked` returns empty, `backlog_graduate_count` triggers a false condition (a) refusal: "Backlog <id6> produced 0 linked IPDs" (observed on `ariaau`, `ildjse`, `h0tiaw`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`). |
| F-03 | MEDIUM | Scope leak in finalize | `runner_shared.execute_item_core` | In historical run `run-20261009T030837Z-2088618` (`m47znv`), an executing agent created a new defect backlog file under `.aw/records/backlog/open/` pursuant to Section 223 STOP-and-report. Because the backlog file was outside the plan's `Scope-Paths`, finalize refused with `fail-gate` requiring `--scope-reason`. |
| F-04 | INFO | Verifier safety stop | `runner_shared.canonical_terminal_status` mapping `"partial": "fail-verify"` | Historical `fail-verify` outcomes (`76ic0k`, `9m4ujh`, `5poaqh`, `uxb0tz`, `3vh74b`) were intentional verifier safety stops. For example, in `76ic0k`, the agent discovered pre-existing `ast.parse` violations in `tests/test_runner_shared.py`, filed defect backlog items `jahjj4` and `z9pfrk`, and recorded a `partial` outcome. The runner mapped `partial` to `fail-verify` to prevent merging incomplete work. These were singleton events resolved when the defect items were executed. |
| F-05 | INFO | Pre-execution gate | `runner_shared.execute_item_core` event `ipd-begin-refused` | `fail-begin` occurs when the pre-execution gate refuses to begin an action because the target plan or lane is not in a runnable state (e.g. `tliqz6` attempt 2 where the lane input was unconformant). Validating plans before queueing prevents `fail-begin`. |
| F-06 | INFO | Cascaded dependencies | `runner_shared.execute_item_core` event `dependency-blocked` | `fail-depend` is a cascaded state resulting from an upstream failure (`fail-gate` or `fail-verify`). Resolving the upstream root causes (F-01 and F-02) directly eliminates downstream `fail-depend` occurrences. |

## Detailed Root Cause and Singleton Analysis

### 1. `fail-gate` Root Causes and Prevention
- **Cause 1A (Multi-Runner Concurrent Shard Race Condition)**:
  - *Mechanism*: `backlog_graduate_count` compares repository plans against `baseline_ids` snapshotted when the runner process begins. When multiple runner shards execute in parallel, Shard B integrates new plans (`jykyqb`, `ml7b9e`) into `main`. When Shard A checks its turn for `2rm0gz`, `_iter_plan_ipds(repo)` finds those peer plans. Because they are absent from Shard A's stale baseline, Shard A checks their `- From-Backlog:` metadata, discovers they do not match `2rm0gz`, and refuses with `BACKLOG-GRADUATE-COUNT`.
  - *Fix*: Pass `new_plan_paths` (from `runner_shared.py`'s `new_produced_paths` / `prod_committed_paths`) directly into `backlog_graduate_count`, checking only plans created or modified in the current turn's lane.
  - *Why this prevents future fail-gates*: Shard A will only evaluate plans produced within its own lane. Any concurrent commits to `main` by peer shards are ignored during turn verification.
- **Cause 1B (Pre-Graduated / Already-Executed Backlog Items)**:
  - *Mechanism*: Backlog items whose plans had already executed in earlier runs were left in `.aw/records/backlog/open/`. When dispatched for graduation, agents correctly recognized that the work was already done and declined to create duplicate plans. However, `existing_handoff_plans` only checks pending plans, so `all_linked` was empty, triggering condition (a) refusal: "produced 0 linked IPDs".
  - *Fix*: Enable `existing_handoff_plans` to recognize plans in `.aw/records/plans/executed/`. If an item's work is already covered by executed plans, recognize the item as already satisfied rather than refusing.
  - *Why this prevents future fail-gates*: Backlog items whose handoffs are completed will pass verification cleanly without requiring redundant duplicate plans.

### 2. `fail-verify` Analysis and Singleton Explanation
- *Mechanism*: `fail-verify` is the terminal status of the verification state machine, reached when:
  1. An independent verifier session inspects the executed work and records valid defect findings (`defect-report-recorded`).
  2. An executing agent hits an unexpected blocker or pre-existing invariant violation, and executes a Section 223 STOP-and-report, recording a `partial` outcome with structured findings. The runner maps `partial` to `fail-verify` (`runner_shared.canonical_terminal_status`).
  3. Verifier retries are exhausted (`VERIFICATION_RETRY_EXHAUSTED_STATUS`).
- *Singleton vs Systemic*:
  - Historical instances of `fail-verify` (`76ic0k`, `9m4ujh`, `5poaqh`, `uxb0tz`, `3vh74b`) were **singleton safety stops**, not runner defects.
  - In `76ic0k` (`run-20261003T022532Z-3439336`), plan `76ic0k` added a guard against code-structure pins (`tests/test_no_code_structure_pins.py`). Running the guard revealed pre-existing `ast.parse` calls in `tests/test_runner_shared.py` (introduced by earlier commit `3d4ae3c25`). Per Section 223, the agent stopped, submitted a `partial` outcome, and filed defect backlog items `jahjj4` and `z9pfrk`.
  - *Why this specific issue will never recur*: Backlog items `jahjj4` and `z9pfrk` were subsequently executed and integrated; the offending `ast.parse` calls were refactored into runtime object inspections. The guard now passes without violation.

### 3. Other Fails (`fail-begin`, `fail-depend`, `fail-merge`)
- *`fail-begin`*: Triggered when pre-execution gate validation fails (e.g. `tliqz6` attempt 2 where the worktree lane input was unconformant). Validating plans before dispatch prevents `fail-begin`.
- *`fail-depend`*: Cascaded status when a prerequisite fails. Resolving root causes F-01 and F-02 directly eliminates cascading dependency failures.
- *`fail-merge`*: Merge conflicts when concurrent branches touch identical files. Adhering to the repository integration lock (`aw integration-lock`) and isolated worktrees eliminates integration races.

## Proposed changes (ordered, validatable)

1. Baseline and reproduction characterization in test fixtures (E-01).
2. Isolate `backlog_graduate_count` and `spec_plan_count` using explicit `new_plan_paths` (E-02).
3. Extend `existing_handoff_plans` and `backlog_graduate_count` to recognize executed handoffs (E-03).
4. Wire `runner_shared.py` production callers to pass lane-discovered paths (E-04).
5. Comprehensive unit and integration test suite and bare pytest pass (E-05).

## Deferred / out of scope (with reason)

- Modifying the independent verifier prompt or verdict schema: `fail-verify` is an intentional safety stop and the verifier contract is sound.
  - Carrier-Declined: verifier schema is verified and functioning as specified; not a defect
- Modifying `aw backlog set` state transitions: state transitions are governed by spec `wy9aru` and do not require modification to resolve gate check isolation.
  - Carrier-Declined: transition table is correct; gate checks were over-broad

## Scope check

- Over-scope: none. All modified paths are declared in `Scope-Paths` and are strictly necessary to isolate production checks and reconcile handoffs.
- Under-scope: none. Both root causes of active `fail-gate`s are directly fixed and covered by unit/integration tests; failure modes across all fail classes are fully characterized.

## Required tests / validation

- Bare `python3 -m pytest tests/test_backlog_production.py tests/test_production_resume_handoff.py` passing cleanly.
- Bare `python3 -m pytest` running the full test suite with no regressions.
- `AW_NO_REEXEC=1 aw ipd lint d52x8b` reporting conforming.
- `AW_NO_REEXEC=1 aw sanitize --agent` reporting clean pass.

## Spec / documentation sync

- N/A with reason: no external spec contracts or user-facing CLI documentation changed; this is an internal runner gate check isolation bug fix.
- No user-facing documentation changes; no CHANGELOG entries required.

## Open questions

### OQ-01: Should backlog items whose plans are already executed be automatically transitioned to graduated/done?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED. Backlog items whose plans have fully executed are recognized by `backlog_graduate_count` as satisfied without demanding new plans; operator reconciliation with `aw backlog set` can transition them to graduated/done cleanly without runner failure.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the test execution output showing the pre-edit baseline and reproduction test case failing at the baseline commit for both multi-runner race and pre-executed backlog handoffs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `agent_workflows/production_checks.py` showing `new_plan_paths` / `new_plan_ids` parameter support and isolated plan iteration in `backlog_graduate_count` and `spec_plan_count`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `agent_workflows/production_checks.py` showing `existing_handoff_plans` inspecting `executed/` and `backlog_graduate_count` accepting already-executed handoffs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of `agent_workflows/runner_shared.py` showing `new_produced_paths` passed to `backlog_graduate_count`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of `python3 -m pytest tests/test_backlog_production.py tests/test_production_resume_handoff.py` passing all tests; paste the full bare `python3 -m pytest` test summary line; paste `aw ipd lint d52x8b` conforming output; paste `git diff --cached --name-only` showing only declared `Scope-Paths`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Execute E-items in order: E-01 characterization, E-02 isolation, E-03 executed handoff support, E-04 runner wiring, E-05 regression tests and validation. Commit through `aw commit d52x8b -- <declared paths>`, never push. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`.

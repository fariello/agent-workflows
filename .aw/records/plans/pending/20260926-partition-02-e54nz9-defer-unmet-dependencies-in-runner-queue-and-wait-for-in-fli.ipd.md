# IPD: Defer unmet dependencies in runner queue and wait for in-flight peer runs

- Date: 2026-09-26
- Kind: child
- Concern: RUNNERS CURRENTLY MARK AN ITEM FAIL-DEPEND IMMEDIATELY WHEN AN EXTERNAL PREREQUISITE IS NOT YET IN EXECUTED/, EVEN IF INDEPENDENT WORK REMAINS IN THE RUNNER'S OWN QUEUE OR THE PREREQUISITE IS ACTIVELY IN-FLIGHT IN A CONCURRENT PEER RUNNER. When two or more runners execute concurrently across the repository, an item in Runner 2 declaring `Item-Dependencies: executed:abc123` currently fails immediately at dispatch if Runner 1 has not finished and merged `abc123` yet. This happens even if Runner 2 still has other independent items in its queue that could be run first, or if Runner 1 is seconds away from completing `abc123`. The current behavior is brittle and forces premature failure.
- Scope: IN: (a) in `agent_workflows/runner_shared.py`, add `find_peer_in_flight_prerequisite(repo: Path, dep_id6: str) -> Optional[dict]` to inspect active run directories under `.aw/records/runs/`, read their `state.json`, and check process PID liveness; (b) implement in-queue deferral in the runner dispatch loop: when `edge_satisfied` returns False for an item, but the current run's queue still contains other unattempted items that do not share the blocking dependency, defer the item to the back of the queue and execute independent items first; (c) implement bounded peer-wait when no other unattempted items remain: if the item is at the head of the queue with no other work to run, but `find_peer_in_flight_prerequisite` confirms the prerequisite is actively being executed in a live peer run, enter a bounded polling loop (checking every 5 seconds, up to 900 seconds timeout) with status updates; (d) if the prerequisite lands in `executed/` (or merges to `main`), the item proceeds to execution; if the peer run terminates/fails without executing the prerequisite or times out, the item transitions to `fail-depend` (fail-fast, no infinite hangs); (e) unit and behavioral tests in `tests/test_runner_peer_dependency.py`. OUT: distributed network locks; changing `edge_satisfied`'s disk authority rule (disk remains the source of truth for satisfaction; the change only modifies runner scheduling and wait semantics).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_peer_dependency.py
- Item-Dependencies: executed:xu3yxw
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Set: partition
- Order: 2
- Highest E allocated: 04
- Author: antigravity
- Id: e54nz9

## Workflow history

- 2026-09-26 to-review (antigravity): authored review-ready plan for runner peer-dependency deferral and wait.
- 2026-09-26 draft (antigravity): created.

## Goal

Enable autonomous runners (`aw oc run` and `aw agy run`) to gracefully handle cross-runner dependencies by deferring blocked items to the back of the queue when independent work remains, and waiting with a bounded timeout when a prerequisite is actively in-flight in a live peer runner.

PRECISELY WHAT IMPROVES:
1. Prevents unnecessary `fail-depend` aborts when parallel runners are executing dependent plans concurrently.
2. Allows independent items in a runner's queue to proceed without being blocked behind a temporarily unavailable prerequisite.
3. Automatically unblocks the waiting item as soon as the peer runner merges the prerequisite into `main`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: peer in-flight detection

- [ ] E-01 IMPLEMENT `find_peer_in_flight_prerequisite` IN `agent_workflows/runner_shared.py`.
  In `agent_workflows/runner_shared.py`, implement:
  `find_peer_in_flight_prerequisite(repo: Path, dep_id6: str, current_run_id: Optional[str] = None) -> Optional[dict]`:
  (a) Inspects all sibling run directories under `repo / ".aw" / "records" / "runs" / "*"` (excluding `current_run_id`).
  (b) Reads each run's `state.json` (skipping unreadable or corrupted files fail-safe).
  (c) Checks if `dep_id6` is listed in the peer run's `queue` with status in `("queued", "running", "attempting", "verifying", "merging")`.
  (d) Verifies process liveness using the peer run's recorded PID (e.g. via `platform_lock.probe_free` or `os.kill(pid, 0)`). If the process is dead, ignores the peer run as stale.
  (e) Returns a summary dict `{"run_id": peer_run_id, "status": item_status, "pid": pid}` if found active, otherwise `None`.
  - Depends on: none
  - Expected outcome: returns active peer run facts when a prerequisite is actively in flight in a living process; returns `None` for stale, dead, or completed runs.
  - Execution state: pending

### Task group 2: in-queue deferral

- [ ] E-02 IMPLEMENT IN-QUEUE DEFERRAL IN THE RUNNER DISPATCH LOOP IN `agent_workflows/runner_shared.py`.
  In `agent_workflows/runner_shared.py` inside the queue dispatch loop (`execute_item_core` / `run_queue_core`):
  (a) When an item's dependencies are evaluated via `edge_satisfied` and report unsatisfied:
  (b) Check if the remaining unattempted queue items contain at least one item that is ready or does not share the same blocked prerequisite.
  (c) If unattempted work remains, record a deferred event in `events.jsonl` ("dependency-deferred-pass"), move the blocked item to the tail of the runnable queue, and continue to the next item.
  (d) Track per-item deferral counts to prevent infinite loops: an item may only be deferred up to the count of independent items in the queue. Once all independent work has been exhausted, deferral stops and E-03's handling is entered.
  - Depends on: E-01
  - Expected outcome: a runner with items `[B (needs A), C (independent)]` skips B on the first pass, successfully executes C, and then re-evaluates B.
  - Execution state: pending

### Task group 3: bounded wait on peer run

- [ ] E-03 IMPLEMENT BOUNDED PEER-WAIT IN `agent_workflows/runner_shared.py`.
  In `agent_workflows/runner_shared.py`:
  (a) When an item has an unsatisfied prerequisite and no independent unattempted items remain in the local queue:
  (b) Call `find_peer_in_flight_prerequisite(repo, dep_id6, state["run_id"])`.
  (c) If `None` is returned (the prerequisite is not in-flight anywhere), fail immediately with `item["status"] = "fail-depend"`.
  (d) If an active peer run is found:
      - Enter a bounded polling loop (polling every `peer_poll_interval`, default 5.0 seconds, up to `peer_wait_timeout`, default 900.0 seconds).
      - In each iteration, print status to stdout/TUI ("Waiting for prerequisite <id6> in peer run <run_id> (<elapsed>s / <timeout>s)...").
      - Check if the prerequisite has appeared in `executed/` (or satisfies `edge_satisfied`).
      - Re-verify peer PID liveness: if the peer process exits or the item in `state.json` transitions to a terminal failure (`fail-lane`, `fail-verify`), abort wait immediately.
  (e) If satisfied within timeout, break wait and proceed to execution. If timeout expires, record timeout event and transition to `fail-depend`.
  - Depends on: E-02
  - Expected outcome: the runner waits patiently while a peer runner completes the prerequisite, proceeding seamlessly when it lands, or failing fast if the peer fails.
  - Execution state: pending

### Task group 4: test suite

- [ ] E-04 ADD UNIT AND BEHAVIORAL TESTS IN `tests/test_runner_peer_dependency.py`.
  In `tests/test_runner_peer_dependency.py`:
  (a) Test `find_peer_in_flight_prerequisite` with mock active run directories, verifying dead PID filtering.
  (b) Test in-queue deferral: queue with `[BlockedItem, IndependentItem]`; verify `IndependentItem` runs first, and `BlockedItem` is executed second after its mock prerequisite lands on disk.
  (c) Test bounded peer wait: runner waits on in-flight prerequisite, a background thread creates the prerequisite plan in `executed/`, and the runner unblocks and proceeds.
  (d) Test timeout and fail-fast: runner fails immediately when prerequisite is not in-flight; runner times out cleanly when peer run does not produce plan.
  - Depends on: E-03
  - Expected outcome: all tests pass cleanly under `python3 -m pytest tests/test_runner_peer_dependency.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.edge_satisfied` is the single authority for whether an edge is satisfied on disk (`resolve_plan_path` -> `plan_bucket == "executed"`).
- `runner_shared.INTEGRATION_LOCK_TIMEOUT_SECONDS` (1800s) sets the precedent for bounded waiting on external repository activity; 900s (15 minutes) is a safe, patient bound for peer plan completion.
- Runner state directories live under `.aw/records/runs/<run_id>/state.json` and contain process PID and item statuses.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only, no AST pins. Suites run bare (`python3 -m pytest tests/test_runner_peer_dependency.py`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

Measured at HEAD `98ff83f8` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.edge_satisfied` | Unsatisfied prerequisite immediately returns `False, reason`, causing dispatch loop to mark `fail-depend`. | `ok, reason = edge_satisfied(edge, item, state, by_id)` followed by `item["status"] = "fail-depend"`. |
| F-2 | MEDIUM | `runner_shared.initialize_run_core` | The queue is frozen into `state["queue"]` and processed linearly without lookahead or dynamic reordering. | `for item in state["queue"]:` linear dispatch loop. |
| F-3 | INFO | `.aw/records/runs/*/state.json` | Every active runner writes PID and queue status into its local run directory. | `state["pid"]`, `state["queue"]`, and `state["run_id"]` fields. |

## Proposed changes (ordered, validatable)

1. E-01 implements peer in-flight detection in `agent_workflows/runner_shared.py`.
2. E-02 implements in-queue deferral in the queue dispatch loop.
3. E-03 implements bounded polling wait on live peer runs.
4. E-04 adds full behavioral test suite in `tests/test_runner_peer_dependency.py`.

## Deferred / out of scope (with reason)

- Distributed inter-process locks across separate network nodes.
  - Carrier-Declined: The runner is local-machine repository-scoped; filesystem state and PID liveness under `.aw/records/runs/` are sufficient and robust.

## Scope check

- Over-scope: none.
- Under-scope: none; covers peer detection, liveness checking, in-queue deferral, bounded waiting, and full test suite.

## Required tests / validation

- Unit tests for `find_peer_in_flight_prerequisite` and PID liveness.
- In-queue deferral order tests.
- Bounded wait and unblock tests.
- Clean pytest run: `python3 -m pytest tests/test_runner_peer_dependency.py`.

## Spec / documentation sync

- `N/A with reason`: Internal runner scheduling enhancement adhering to existing spec `25kzda` terminal semantics.

## Open questions

### OQ-01: Default peer wait timeout and polling interval

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Default to 5.0 seconds polling interval and 900.0 seconds (15 minutes) maximum wait timeout.

### OQ-02: Deferral loop termination guard

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Track deferral passes per item to guarantee that an item is deferred at most once per distinct independent plan execution. When no independent items remain, deferral terminates and bounded waiting begins.

### OQ-03: Handling dead or failed peer runs

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: If the peer PID is no longer alive, or if the peer `state.json` records that the prerequisite suffered a terminal failure (`fail-lane`, `fail-verify`, `fail-depend`), the waiting runner aborts the wait immediately and marks the dependent `fail-depend`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests demonstrate `find_peer_in_flight_prerequisite` identifies active peer runs and ignores dead PIDs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test demonstrates an item with an unmet dependency is deferred to the end of the queue while independent items execute first.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test demonstrates runner waits for peer prerequisite completion and unblocks immediately when prerequisite enters `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Captured output of `python3 -m pytest tests/test_runner_peer_dependency.py` showing all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Standard child plan implementing runner peer-dependency awareness. Execution will follow the standard IPD lifecycle in the isolated worktree `feat/aw-partition`.

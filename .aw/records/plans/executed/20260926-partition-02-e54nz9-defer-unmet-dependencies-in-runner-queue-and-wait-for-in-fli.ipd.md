# IPD: Defer unmet dependencies in runner queue and wait for in-flight peer runs

- Date: 2026-09-26
- Kind: child
- Concern: WHEN A RUN HAS NOTHING LEFT TO DISPATCH, AN ITEM WHOSE PREREQUISITE A LIVE PEER RUN IS EXECUTING RIGHT NOW IS FAILED AS IF THE PREREQUISITE COULD NEVER ARRIVE. Two runs in one checkout (a supported configuration: Policy B, `runner_shared` "SERIALIZE THE INTEGRATION STEP, do not refuse a start") can hold a prerequisite and its dependent in different queues. The dependent's `executed:<id6>` edge targets a plan NOT in its own run, so `runner_shared.edge_satisfied` returns "(it is not in this run, so it cannot become satisfied here)", and at drain time `runner_shared.classify_drain_block` classifies that external edge PERMANENT, so the host's drain arm writes `fail-depend` and the run ends, even when the peer is minutes from finalizing it. Recovery then needs a human `--retry-incomplete` (`DEPENDENCY_BLOCK_RECOVERY_HINT`). Independent work is NOT held up today: each dispatch pass already picks the first `queued` item whose dependencies are satisfied (`oc_runipd.run_queue`, "for item in sorted(queued, key=lambda it: queue_sort_key(it, by_id))"), so only the drain-time case is broken.
- Scope: IN: (a) one shared, read-only predicate in `runner_shared` answering "is this external `executed:` prerequisite still live in a peer run", built on the EXISTING `peer_drivers` (OS-lock liveness) and the peer's `state.json` queue; (b) one shared bounded wait that, at drain time only, polls until every such edge is satisfied on disk, its peer stops holding it live, a stop is requested, or the bound expires; (c) wiring it into BOTH hosts' drain arms (`oc_runipd.run_queue`, `agy_runipd.run_queue`) BEFORE the existing classification, so a satisfied item re-enters dispatch and anything else falls through to today's unchanged labelling; (d) behavioral tests. OUT: changing `edge_satisfied`'s disk-authority rule or `classify_drain_block`'s verdicts; waiting on a `spec`/`backlog` edge or on a prerequisite no live peer holds; in-queue reordering (already how selection works); cross-machine coordination.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_peer_dependency.py, CHANGELOG.md
- Item-Dependencies: executed:xu3yxw
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Set: partition
- Order: 2
- Highest E allocated: 05
- Author: antigravity
- Id: e54nz9

## Workflow history
- 2026-09-27 executed (antigravity): finalize e54nz9: defer unmet dependencies and wait for live peer runs [Scope reconciliation - in-scope-unmodified CHANGELOG.md: committed in a7adb1c3; in-scope-unmodified agent_workflows/agy_runipd.py: committed in a7adb1c3; in-scope-unmodified agent_workflows/oc_runipd.py: committed in a7adb1c3; in-scope-unmodified agent_workflows/runner_shared.py: committed in a7adb1c3; in-scope-unmodified tests/test_runner_peer_dependency.py: committed in a7adb1c3]
- 2026-09-26 approved (aw set, --by-human): Human approved in chat: 'OK, They're reviewed. I approve them both. Please do 01.'
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 FIXED

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED. Narrowed on the maintainer's 2026-09-26 ruling to the one missing behavior (a bounded, stop-aware drain-time wait for a prerequisite a LIVE peer run holds), after measuring that in-queue deferral and peer detection already exist; rebuilt on peer_drivers, wired into both hosts' drain arms, bound raised 900s -> 1800s on measured item durations. Readiness GO - PENDING HUMAN APPROVAL.
- 2026-09-26 to-review (antigravity): authored review-ready plan for runner peer-dependency deferral and wait.
- 2026-09-26 draft (antigravity): created.

## Goal

When a run has drained everything else, it waits (bounded, stop-aware, visible) for a prerequisite that a live peer run is executing, then dispatches the dependent once the prerequisite lands in `executed/`, instead of failing it. Every other drain outcome is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared predicate

- [x] E-01 ADD `runner_shared.peer_held_prerequisites(repo, item, state, *, exclude_run_dir) -> dict[str, PeerHold]` (a `NamedTuple` `PeerHold(run_id, peer_state, item_status)`), READ-ONLY. For each of the item's dependency tokens: parse with `parse_dependency_token`; keep only `executed:` edges with `target_type == "ipd"` whose id6 is NOT in this run's queue and which `edge_satisfied` reports unsatisfied. For each such edge, walk `peer_drivers(repo, exclude_run_dir=run_dir)` (do NOT re-implement liveness or read a PID for it: `peer_drivers` already uses `run_viewer.driver_holder_state`'s `flock` probe and states that a recorded PID is "DIAGNOSTIC ONLY, never a liveness signal") and, for each peer with `state == PEER_LIVE`, read its `state.json` fail-safe and look the id6 up in its `queue`. The edge is HELD when a live peer's entry exists and its status is NOT in `TERMINAL_STATES` (so `queued`, `running`, and any other non-terminal status; derive it from the shared set, do not list names). Return only held edges. A `PEER_UNKNOWN` peer does NOT hold (unprovable liveness must not start a wait). Never raises: any read error yields "not held" for that peer.
  - Depends on: none
  - Expected outcome: held edges are returned for a live peer with the id6 non-terminal; nothing is returned for a dead/crashed peer (lock not held), an unknown peer, a peer whose entry is terminal, an in-queue target, a `spec`/`backlog` edge, or an already-satisfied edge.
  - Execution state: performed

### Task group 2: the bounded wait

- [x] E-02 ADD `runner_shared.wait_for_peer_prerequisites(run_dir, state, items, *, timeout, poll, poll_stop, sleep, now, say, append_jsonl) -> PeerWaitOutcome`, the ONE wait loop both hosts call. It takes the drain arm's remaining `queued` items, computes `peer_held_prerequisites` for each, and returns immediately (`waited=False`) if none is held. Otherwise it loops: sleep `poll`; call `poll_stop(run_dir)` and return `stopped=True` at once if any level is requested; recompute; return `released=True` as soon as ANY waited item's `dependency_status` becomes satisfied (disk remains the only authority, via `edge_satisfied`); return `released=False` when no edge is held any more (the peer finished without executing it, died, or went terminal) or when `now()` passes `timeout`. Every `INTEGRATION_LOCK_PROGRESS_SECONDS` it calls `say(...)` with the id6, peer run id and elapsed/limit. It appends `peer-dependency-wait-started` once and `peer-dependency-wait-ended` once (fields: `id6s`, `peers`, `outcome` in `released|peer-gone|timeout|stopped`, `elapsed_s`) to `events.jsonl`. It writes NO item status. Constants: `PEER_DEPENDENCY_WAIT_SECONDS = 1800.0`, `PEER_DEPENDENCY_POLL_SECONDS = 5.0`.
  - Depends on: E-01
  - Expected outcome: the loop ends on each of its four causes, never exceeds the bound, and never writes a status.
  - WHY 1800s AND NOT THE PLAN'S ORIGINAL 900s: measured over the last 30 run records' `ipd-started`/`ipd-finished` pairs, an item takes p50 17.0 min, p90 46.7 min, max 182 min (194 items). 900s is shorter than a MEDIAN item, so it would time out on the normal case; 1800s matches `INTEGRATION_LOCK_TIMEOUT_SECONDS`, the repository's existing bound for waiting on a peer, and still expires inside an operator's attention span. A longer prerequisite still ends the wait and falls through to today's behavior, which is the honest outcome.
  - Execution state: performed

- [x] E-03 WIRE IT INTO BOTH HOSTS' DRAIN ARMS, identically. In `oc_runipd.run_queue` and `agy_runipd.run_queue`, in the `runnable is None` branch, AFTER the existing integration-deferral block and BEFORE the "CLASSIFY BEFORE LABELLING" loop, call `runner_shared.wait_for_peer_prerequisites(...)` (skipped when `wind_down is not None`, which that branch already handles by breaking earlier). If it returns `released=True`, reload/save state and `continue` the outer loop so the now-satisfied item is dispatched by the normal selection (no new dispatch path). If it returns `stopped=True`, `continue` so the loop's existing stop observation handles it (no new stop semantics). Otherwise fall through UNCHANGED to `classify_drain_block` and today's labelling, which still writes `fail-depend` for the external edge. The per-host change must be the same few lines calling the shared function; all logic lives in `runner_shared`.
  - Depends on: E-02
  - Expected outcome: with no live peer holding anything, both hosts' drain arm behaves byte-identically to before; with one, the dependent is dispatched after the prerequisite lands.
  - NO SPIN: each call to the wait either returns `released=True` because an item became dispatchable (so the next pass dispatches it, making progress), or returns a non-released outcome, after which this pass labels and breaks exactly as today. It cannot return `released=True` twice for the same unchanged queue.
  - Execution state: performed

### Task group 3: tests and changelog

- [x] E-04 ADD `tests/test_runner_peer_dependency.py`, behavioral, using real temp run directories and a REAL peer lock holder (a child process holding `driver.lock` via the same `platform_lock` API the drivers use), no mocking of `peer_drivers` or `edge_satisfied`. Cases: (a) predicate: live peer with the id6 `running` -> held; peer process exited (lock released) -> not held; peer entry `executed`/`fail-verify` -> not held; target in own queue -> not held; `exists:`/`state:`/spec edge -> not held; (b) wait released: a background thread moves the prerequisite plan into `executed/` after ~1s -> `released=True`; (c) peer-gone: the holder process exits mid-wait -> `released=False`, outcome `peer-gone`, well before the bound; (d) timeout with an injected clock -> outcome `timeout`; (e) stop: a stop request written mid-wait -> `stopped=True` on the next poll; (f) no-peer drain arm: with no live peer, the external-edge item still ends `fail-depend` with the same event fields as before (regression pin); (g) BOTH hosts: drive each host's `run_queue` drain arm (or the smallest shared seam it calls) on a two-item fixture where the prerequisite lands during the wait, and assert the dependent is dispatched rather than labelled. Use injected `sleep`/`now`/`poll` so the suite stays fast.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all pass; (b), (c), (g) FAIL against the pre-change code (show by reverting E-03's wiring).
  - Execution state: performed

- [x] E-05 `CHANGELOG.md` unreleased entry in plain user-facing language, no dashes: when two runs share a checkout, a run that has finished its other work now waits up to 30 minutes for a prerequisite the other run is still executing, instead of failing the dependent item.
  - Depends on: E-03
  - Expected outcome: one entry.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Selection already skips blocked items: both hosts' `run_queue` pick the first `queued` item, in `queue_sort_key` order, whose `dependency_status` is satisfied, so a blocked item never delays independent work. Nothing to add there.
- The drain arm (`runnable is None`) is per-host code in `oc_runipd.run_queue` and `agy_runipd.run_queue`; its classification is shared (`runner_shared.classify_drain_block`, depblock `akzy45`), and its comment requires the rule to live in `runner_shared` "so agy's copy of this arm cannot drift from it". The wait follows the same split.
- `classify_drain_block` deliberately classifies an EXTERNAL edge PERMANENT ("There is no `--with-dependencies` closure inside a frozen run, so waiting cannot pay off"). That is true unless a live peer holds the target; this plan waits BEFORE classification and leaves the classifier untouched.
- Peer liveness is `runner_shared.peer_drivers` (three-valued `PEER_LIVE`/`PEER_NONE`/`PEER_UNKNOWN`, via `run_viewer.driver_holder_state`'s `flock` probe, resolved through `runs_repo_root` so a lane worktree sees the main runs tree). `_peer_pid` is diagnostic only. Measured: `peer_drivers` over this repository's runs tree took 0.19s, so a 5s poll is cheap.
- `state.json` carries `queue` and `selectors` but NO pid field (measured over the last 40 run records: no key containing `pid`); the driver records `pid=` inside `driver.lock`.
- The repository's precedent for waiting on a peer is the integration lock: `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0`, progress every `INTEGRATION_LOCK_PROGRESS_SECONDS = 30.0`, and on expiry it defers rather than fails.
- Stops are polled with `runner_stop.poll_stop(run_dir)` (side-effect free, idempotent).
- Behavioral tests only, no source-text or AST pins (maintainer ruling 2026-09-26). Suite runs bare (`python3 -m pytest`); narrowed runs use `-o addopts=""`.

## Findings

Original author F-1..F-3 measured at HEAD `98ff83f8`. Review corrections F-4..F-9 at the same HEAD, in the `feat/aw-partition` worktree.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | drain arm | An external `executed:` prerequisite still in flight in a peer run leads to `fail-depend` when the run drains. | `edge_satisfied`: "(it is not in this run, so it cannot become satisfied here)"; `classify_drain_block` external branch -> PERMANENT; host drain arm writes `item["status"] = "fail-depend"` |
| F-2 | MEDIUM | (author) | "processed linearly without lookahead". CORRECTED at review, see F-4. | - |
| F-3 | INFO | (author) | "Every active runner writes PID ... into state.json". CORRECTED at review, see F-5. | - |
| F-4 | HIGH | original E-02 | In-queue deferral ALREADY EXISTS: each pass selects the first satisfied `queued` item, so a blocked item never delays independent work; the item as written re-implemented it. | `oc_runipd.run_queue`: "for item in sorted(queued, key=lambda it: queue_sort_key(it, by_id)): satisfied, _ = dependency_status(item, state); if satisfied: runnable = item; break"; same shape in `agy_runipd.run_queue` |
| F-5 | HIGH | original E-01 | The planned liveness signal does not exist and is rejected by the code: no `state.json` has a pid field, and `_peer_pid` is "DIAGNOSTIC ONLY, never a liveness signal" because PIDs are reused. Peer detection already exists as `peer_drivers`. | scan of the last 40 run `state.json` files: no key containing `pid`; `runner_shared._peer_pid` docstring; `runner_shared.peer_drivers` |
| F-6 | HIGH | original E-02/E-03 targets | The named insertion points `execute_item_core` / `run_queue_core` are wrong: `runner_shared` has no `run_queue_core`, and the drain arm lives in each host's `run_queue`. `- Scope-Paths:` omitted both host modules. | `grep -n "^def run_queue" agent_workflows/*.py` -> `oc_runipd.py:3382`, `agy_runipd.py:2755` |
| F-7 | MEDIUM | original E-01 (c) | Statuses `attempting`, `verifying`, `merging` do not exist in the run status vocabulary; a name list would also drift. | `grep '"attempting"\|"verifying"\|"merging"' runner_shared.py` -> none; status census over recent runs shows `queued`/`running`/terminal only |
| F-8 | MEDIUM | original E-03 / OQ-01 | 900s is shorter than a median item (p50 17.0 min over 194 measured items), so the wait would time out on the normal case. | `ipd-started`/`ipd-finished` pairs over the last 30 runs: p50 17.0, p90 46.7, max 182 min |
| F-9 | MEDIUM | whole plan | Missing: stop-awareness during a wait of up to half an hour, both-host parity, an event trail, a no-peer regression pin, and a changelog entry. | `runner_stop.poll_stop`; depblock `akzy45`'s parity rule in the drain-arm comment |

## Proposed changes (ordered, validatable)

1. E-01: shared read-only "held by a live peer" predicate over `peer_drivers`.
2. E-02: shared bounded, stop-aware, visible wait loop that writes no status.
3. E-03: identical call in both hosts' drain arms, before the unchanged classification.
4. E-04: behavioral tests incl. a real lock-holding peer and both hosts.
5. E-05: changelog.

## Deferred / out of scope (with reason)

- Distributed coordination across machines.
  - Carrier-Declined: runs are repository-local and `peer_drivers` already scopes liveness to this checkout's runs tree.
- Waiting on a prerequisite that no live peer holds (for example one merely `approved` and not in any run).
  - Carrier-Declined: nothing will make it arrive during this run, so waiting cannot pay off; today's `fail-depend` with its recovery hint is the honest outcome. Partition (`xu3yxw`) is what keeps such chains in one run.
- Making the wait bound configurable per repository.
  - Carrier-Declined: one constant matching the existing integration-lock bound; no caller needs a different value yet, and a config key is a public contract.

## Scope check

- Over-scope: removed at review. The original E-02 ("in-queue deferral") re-implemented behavior selection already has; the original E-01 re-implemented peer liveness `peer_drivers` already provides, using a PID signal the code explicitly rejects.
- Under-scope: added at review. The wiring in both hosts' `run_queue` (the only place the drain arm exists), stop-awareness, the events, the no-peer regression pin, and the changelog.

## Required tests / validation

- `python3 -m pytest tests/test_runner_peer_dependency.py -o addopts=""`, plus the revert check for (b), (c), (g).
- Existing drain/dependency suites must stay green unchanged: run `python3 -m pytest -o addopts="" -q tests/ -k "drain or depblock or dependency"` before and after and compare.
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec amendment. Spec `25kzda` 2.9 says an external target "is evaluated from frozen repository state" and "without it [`--with-dependencies`], an unsatisfied external target cannot be met in this run"; this plan does not change satisfaction (disk via `edge_satisfied` stays the only authority, re-read each poll), it only delays the drain-time label while a peer holds the target. If `/plan-review` of a later round or the executor finds 2.9's "cannot be met in this run" read as a prohibition on waiting, amend 2.9 in this plan (add the `.spec.md` to `- Scope-Paths:`) rather than dropping the wait. `CHANGELOG.md` is updated (E-05).

## Open questions

### OQ-01: Default peer wait timeout and polling interval

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode), on measured evidence
- Resolution or deferral rationale: REVISED AT REVIEW from the author's 900s: 1800s bound, 5s poll, progress every 30s. Basis in E-02: measured item durations (p50 17.0 min, p90 46.7 min over 194 items) make 900s shorter than a typical item, and 1800s is the repository's existing peer-wait bound (`INTEGRATION_LOCK_TIMEOUT_SECONDS`). `peer_drivers` costs ~0.19s, so a 5s poll is cheap. Reversible: constants.

### OQ-02: Deferral loop termination guard

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode)
- Resolution or deferral rationale: SUPERSEDED AT REVIEW: there is no deferral loop to guard, because in-queue deferral is removed (selection already skips blocked items). The wait's own termination is guaranteed by E-02's four exits and E-03's no-spin argument.

### OQ-03: Handling dead or failed peer runs

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode)
- Resolution or deferral rationale: The wait ends as soon as no edge is held (E-02 `peer-gone`), which covers a peer whose `driver.lock` is no longer held (process exited or crashed; the OS drops the `flock`) and a peer whose entry for the id6 is in `TERMINAL_STATES` (any terminal outcome, success or failure, since a success lands on disk and releases through `edge_satisfied`). A `PEER_UNKNOWN` peer never starts a wait. The item then falls through to today's labelling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the predicate's code and the passing output of case (a) for every listed sub-case, and `grep -n` showing it calls `peer_drivers` and does not read a PID for liveness.
  - Observed evidence: All 5 predicate sub-cases passed in test_a_predicate_subcases, peer_drivers called at line 5297 with no PID liveness probe.
    Predicate implementation in `agent_workflows/runner_shared.py`:
    ```python
    def peer_held_prerequisites(
        repo: Path,
        item: Mapping[str, Any],
        state: Mapping[str, Any],
        *,
        exclude_run_dir: Path | None = None,
    ) -> dict[str, PeerHold]:
        try:
            repo_path = Path(repo)
            queue_id6s = {
                str(entry.get("id6"))
                for entry in state.get("queue", [])
                if isinstance(entry, Mapping) and "id6" in entry
            }
            by_id = {
                str(entry.get("id6")): entry
                for entry in state.get("queue", [])
                if isinstance(entry, Mapping) and "id6" in entry
            }
            state_dict = dict(state)
            state_dict.setdefault("repo", str(repo_path))

            deps_list: list[Any] = []
            for k in ("dependencies", "item_dependencies"):
                val = item.get(k)
                if isinstance(val, (list, tuple)):
                    for dep in val:
                        if dep not in deps_list:
                            deps_list.append(dep)

            candidate_edges: dict[str, Any] = {}
            for dep in deps_list:
                edge = parse_dependency_token(str(dep))
                if (
                    edge is not None
                    and getattr(edge, "kind", None) == "executed"
                    and getattr(edge, "target_type", None) == "ipd"
                ):
                    target_id6 = str(edge.id6)
                    if target_id6 in queue_id6s:
                        continue
                    sat, _ = edge_satisfied(edge, dict(item), state_dict, by_id)
                    if not sat:
                        candidate_edges[target_id6] = edge

            if not candidate_edges:
                return {}

            peers = peer_drivers(repo_path, exclude_run_dir=exclude_run_dir)
            live_peers = [p for p in peers if p.state == PEER_LIVE]
            if not live_peers:
                return {}

            held: dict[str, PeerHold] = {}
            for peer in live_peers:
                try:
                    peer_state_data = json.loads(
                        (peer.run_dir / "state.json").read_text(encoding="utf-8")
                    )
                except Exception:
                    continue

                peer_queue = peer_state_data.get("queue")
                if not isinstance(peer_queue, list):
                    continue

                for q_entry in peer_queue:
                    if not isinstance(q_entry, Mapping):
                        continue
                    q_id6 = str(q_entry.get("id6", ""))
                    if q_id6 in candidate_edges and q_id6 not in held:
                        st = str(q_entry.get("status", ""))
                        if st not in TERMINAL_STATES:
                            held[q_id6] = PeerHold(
                                run_id=peer.run_id,
                                peer_state=peer.state,
                                item_status=st,
                            )

            return held
        except Exception:
            return {}
    ```
    Passing output of case (a):
    ```
    $ python3 -m pytest tests/test_runner_peer_dependency.py -k "test_a" -o addopts="" -v
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_a_predicate_subcases PASSED [100%]
    1 passed, 6 deselected in 0.93s
    ```
    `grep -n` verification showing calls to `peer_drivers` and no PID read for liveness:
    ```
    $ grep -n "def peer_held_prerequisites" agent_workflows/runner_shared.py -A 85 | grep -E "peer_drivers|pid"
    5247-    Liveness is established through :func:`peer_drivers` (which probes ``driver.lock`` acquirability);
    5297-        peers = peer_drivers(repo_path, exclude_run_dir=exclude_run_dir)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the passing output of cases (b) to (e) and the two emitted event dicts for one run, showing `outcome` and `elapsed_s`, and show the function contains no write to an item's `status`.
  - Observed evidence: All cases (b) through (e) passed in 3.44s, events emitted with outcome and elapsed_s, and no status writes exist in wait_for_peer_prerequisites.
    Passing output of cases (b) to (e):
    ```
    $ python3 -m pytest tests/test_runner_peer_dependency.py -k "test_b or test_c or test_d or test_e" -o addopts="" -v
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_d_timeout PASSED [ 25%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_b_wait_released PASSED [ 50%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_e_stop PASSED [ 75%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_c_peer_gone PASSED [100%]
    4 passed, 3 deselected in 3.44s
    ```
    Emitted events from `events.jsonl`:
    ```json
    {
      "at": "2026-09-26T23:18:45+00:00",
      "event": "peer-dependency-wait-started",
      "id6s": [
        "prereq"
      ],
      "peers": [
        "run-peer"
      ],
      "waiting_id6s": [
        "dep001"
      ]
    }
    {
      "at": "2026-09-26T23:18:46+00:00",
      "elapsed_s": 0.257,
      "event": "peer-dependency-wait-ended",
      "id6s": [
        "prereq"
      ],
      "outcome": "released",
      "peers": [
        "run-peer"
      ],
      "waiting_id6s": [
        "dep001"
      ]
    }
    ```
    Grep confirming no item status write in `wait_for_peer_prerequisites`:
    ```
    $ grep -n 'status' agent_workflows/runner_shared.py | grep -E "53[3-9][0-9]|54[0-8][0-9]"
    5349:    Writes NO item status.
    5439:        # 2. Has any waited item's dependency_status become satisfied on disk?
    5442:            sat, _ = dependency_status(it, state_dict)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste both hosts' diffs, showing the same call in the same position before `classify_drain_block`, and the passing output of cases (f) and (g) for both hosts, plus (g) FAILING with the wiring reverted.
  - Observed evidence: Both hosts wired identically before classify_drain_block, cases (f) and (g) pass, and (g) fails when wiring reverted.
    Both hosts' wiring diff:
    ```diff
    --- a/agent_workflows/oc_runipd.py
    +++ b/agent_workflows/oc_runipd.py
    @@ -3638,6 +3638,18 @@ def run_queue(
                         # An integration that landed during the rungs above can have unblocked a dependent,
                         # so go round again rather than declaring the queue drained.
                         continue
    +            peer_wait = runner_shared.wait_for_peer_prerequisites(
    +                run_dir,
    +                state,
    +                queued,
    +                append_jsonl=append_jsonl,
    +            )
    +            if peer_wait.released:
    +                state = load_state(run_dir)
    +                register_signal_report(run_dir, state)
    +                continue
    +            if peer_wait.stopped:
    +                continue
                 # depblock 01 (`akzy45`) E-02: CLASSIFY BEFORE LABELLING. This loop used to write the
    --- a/agent_workflows/agy_runipd.py
    +++ b/agent_workflows/agy_runipd.py
    @@ -2980,6 +2980,18 @@ def run_queue(
                         save_state(run_dir, state)
                     if [it for it in state["queue"] if it["status"] == "queued"]:
                         continue
    +            peer_wait = runner_shared.wait_for_peer_prerequisites(
    +                run_dir,
    +                state,
    +                queued,
    +                append_jsonl=append_jsonl,
    +            )
    +            if peer_wait.released:
    +                state = load_state(run_dir)
    +                register_signal_report(run_dir, state)
    +                continue
    +            if peer_wait.stopped:
    +                continue
                 # depblock 01 (`akzy45`) E-02/E-04: CLASSIFY BEFORE LABELLING, through the SAME shared
    ```
    Passing output of cases (f) and (g) for both hosts:
    ```
    $ python3 -m pytest tests/test_runner_peer_dependency.py -k "test_f or test_g" -o addopts="" -v
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_g_both_hosts_dispatch_after_peer_release PASSED [ 50%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_f_no_peer_drain_arm PASSED [100%]
    2 passed, 5 deselected in 2.14s
    ```
    Revert test: case (g) FAILING when wiring was temporarily disabled:
    ```
    $ python3 -m pytest tests/test_runner_peer_dependency.py -k "test_g" -o addopts="" -v
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_g_both_hosts_dispatch_after_peer_release FAILED [100%]
    AssertionError: Lists differ: [] != ['dep001']
    - []
    + ['dep001'] : agent_workflows.oc_runipd did not dispatch dep001
    1 failed, 6 deselected in 0.64s
    ```

    VERIFY-EXECUTION ADDENDUM (opencode/its_direct/pt3-claude-opus-5.5-1m-us, 2026-09-26): two defects found in the shipped wiring and fixed in place. (1) A LEVEL-3/4 STOP during the wait SPUN: `if peer_wait.stopped: continue` relies on the loop-top checkpoint, but `_observe_between_turn_stop` makes no wind-down for levels 3/4, so the drain arm re-entered the wait indefinitely (measured before the fix: 51 wait calls in 30s, never exiting, on both hosts). Now a stopped wait `continue`s only for a between-turn level and otherwise sets `stopped_at_checkpoint = True` and breaks, leaving the remainder `queued`. (2) The wait was SILENT: both hosts call it without `say=`, whose default was a no-op; the default now writes `[peer-dependency]` lines to stderr, plus one immediate line naming the prerequisite and peer. Regression tests `test_h_level3_stop_during_wait_ends_the_run_on_both_hosts` and `test_i_wait_is_visible_by_default` FAIL on the pre-fix code and pass after:
    ```
    # pre-fix code:
    E           AssertionError: drain arm re-entered the wait after a stop (spin)
    E       AssertionError: '[peer-dependency]' not found in ''
    2 failed, 7 deselected in 1.81s
    # with the fix:
    $ python3 -m pytest tests/test_runner_peer_dependency.py -o addopts="" -q
    9 passed in 5.91s
    $ python3 -m pytest
    2498 passed, 2 skipped, 3 warnings in 35.10s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full `tests/test_runner_peer_dependency.py` run output, the before/after output of the drain/dependency `-k` selection, and the bare `python3 -m pytest` summary line.
  - Observed evidence: All 7 tests in test_runner_peer_dependency.py pass in 5.19s, drain/dependency suite expands from 19 to 26 passing, and bare pytest suite passes with 2496 passed.
    Full `tests/test_runner_peer_dependency.py` suite output:
    ```
    $ python3 -m pytest tests/test_runner_peer_dependency.py -o addopts="" -v
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_c_peer_gone PASSED [ 14%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_b_wait_released PASSED [ 28%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_e_stop PASSED [ 42%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_f_no_peer_drain_arm PASSED [ 57%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_a_predicate_subcases PASSED [ 71%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_g_both_hosts_dispatch_after_peer_release PASSED [ 85%]
    tests/test_runner_peer_dependency.py::RunnerPeerDependencyTests::test_d_timeout PASSED [100%]
    7 passed in 5.19s
    ```
    Before/after output of drain/dependency suite (`-k "drain or depblock or dependency"`):
    Before:
    ```
    $ python3 -m pytest -o addopts="" -q tests/ -k "drain or depblock or dependency"
    19 passed, 2646 deselected in 2.40s
    ```
    After:
    ```
    $ python3 -m pytest -o addopts="" -q tests/ -k "drain or depblock or dependency"
    26 passed, 2646 deselected in 4.85s
    ```
    Bare `python3 -m pytest` summary line:
    ```
    2496 passed, 2 skipped, 3 warnings in 43.52s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the CHANGELOG entry.
  - Observed evidence: Unreleased entry with no em or en dashes added to CHANGELOG.md under 2.0.0 (pending).
    Entry added to `CHANGELOG.md` under `2.0.0 (pending)`:
    ```markdown
    - Added: when two runs share a checkout, a run that has finished its other work now waits up to 30 minutes for a prerequisite the other run is still executing, instead of failing the dependent item.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xu3yxw` is executed (`- Item-Dependencies: executed:xu3yxw`).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `runner_shared` (the predicate, the wait, two constants), the drain arm of `oc_runipd.run_queue` and `agy_runipd.run_queue`, the new test file, and one CHANGELOG entry. An out-of-scope edit, if one proves necessary, is made and justified at finalize with `--scope-reason`; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence. The terminal transition is `aw ipd finalize`: the runner owns it when this plan runs in a lane; a hand executor runs it only when no runner is driving.

# IPD: Rewire reconcile_item_on_interrupt into execute_item_core and fix its no-worktree _run_git tuple misuse

- Date: 2026-09-24
- Kind: child
- Concern: AN INTERRUPTED ITEM IS LEFT `running`, WITH NO `ipd-interrupted` EVENT, ON BOTH HOSTS. Backlog `2415x6` (`high`, `Blocks-Release: next`, `bug`): commit `70a2059f` ("refactor(runner): deduplicate execute_item into runner_shared.execute_item_core") lifted each driver's `execute_item` into `runner_shared.execute_item_core` and DROPPED the `except KeyboardInterrupt as exc:` handler that called `runner_shared.reconcile_item_on_interrupt`. The function survives with ZERO callers. Measured at HEAD `877545fc` by driving the real `oc_runipd.execute_item` and `agy_runipd.execute_item` with a spawn that raises `KeyboardInterrupt("clean-up-and-terminate")`: the interrupt propagates, the item ends `status running`, and `events.jsonl` holds only `['ipd-started', 'tool-identity-verified', 'suite-baseline-unavailable']`. `render_stream._interrupt_reason_of` names `runner_shared.reconcile_item_on_interrupt` (2 sites) as a producer the viewer's `interrupted` arm depends on, so the viewer renders nothing for this state.
  THE SAME FUNCTION CARRIES A LATENT CRASH THAT THE REWIRE MAKES REACHABLE, which is why both land in one plan. Backlog `tsfk8a` (`bug`, `Blocks-Release: next`) and its duplicate `e17a2e` (`bug`, `high`, `Blocks-Release: next`): the no-worktree arm of `reconcile_item_on_interrupt` does `status_out = _run_git(repo, ["status", "--porcelain"])` then `holds_work = bool(status_out.strip())`, but `runner_shared._run_git` returns `(returncode, stdout, stderr)`. Measured: calling the function with `work_dir=None` and `msg="clean-up-and-terminate"` raises `AttributeError 'tuple' object has no attribute 'strip'`. That arm is reached whenever `work_dir` is `None`, i.e. every `isolate_worktree: false` run. Rewiring the call WITHOUT this fix would replace "silently left running" with "an AttributeError on the interrupt path", which is worse, so the two must ship together.
   A THIRD DEFECT IN THE SAME FUNCTION, found while authoring (F-5): the no-changes arm pops the unfinished attempt only `if attempts[-1].get("attempt") == attempt_no`, but `execute_item_core` builds the attempt record with the key `"number"`, not `"attempt"`, so the pop never fires and the "run fresh" contract in the docstring is not met. The deleted test that covered this arm hid it by building its fixture with `"attempt": 1`.
   A FOURTH DEFECT, ADDED AT REVIEW AND ATTRIBUTABLE TO THIS PLAN'S OWN FIX (F-9, E-07). Unpacking the tuple is necessary but NOT sufficient: `git status --porcelain` is EMPTY after a commit, so the corrected predicate scores a non-isolated turn that did real work AND COMMITTED IT (which the repository's own execution contract obliges an executing agent to do) as holding NOTHING, and routes it to the DESTRUCTIVE no-changes arm, which unlinks the begin receipt, resets the item to `queued` and pops the attempt. Measured at review: after one `git commit`, `_run_git(repo, ["status", "--porcelain"])` -> `(0, '', '')` while HEAD has moved off `attempt["starting_head"]`. That is a WORSE outcome than the `AttributeError` it replaces, because it destroys recovery state silently instead of failing loudly, so E-07 ships with E-01.
  WHY NO TEST CAUGHT ANY OF THIS: the guard was a source-text pin (`"event": "ipd-interrupted"` in each driver's source), satisfied by `install_stop_triggers` docstring prose. Its behavioral successor was an `xfail(strict=True)` test in `tests/test_runner_stop_triggers.py`, and the unit tests calling the function lived in `tests/test_interrupt_menu.py`; BOTH FILES WERE DELETED by trim commit `19313eed`, so there is no xfail marker left to remove and nothing in `tests/` exercises the function today.
- Scope: IN: (a) re-add ONE `except KeyboardInterrupt as exc:` handler in `runner_shared.execute_item_core`, on the executor-spawn `try` beside the existing `StopNowForce`/`StopAtCheckpoint`/`StallTimeout` handlers, calling `reconcile_item_on_interrupt(...)` then re-raising, so both hosts get it once; (b) unpack the `_run_git` tuple in the no-worktree arm and fail SAFE (treat as holding work) when `git status` cannot be observed; (b2) in that same arm, count a COMMIT as work by comparing HEAD to `attempt["starting_head"]`, so the corrected predicate does not silently clean up a committed non-isolated turn (E-07, added at review); (c) make the no-changes arm's attempt pop match the attempt record's real `"number"` key; (d) behavioral tests driving the real `execute_item` of both hosts and unit tests of the no-worktree arm against real git repos. OUT: the verifier-turn spawn (no `KeyboardInterrupt` handler there before `70a2059f` either); the deliberate-stop handlers' `return`-vs-`raise` and status-routing behavior (fixed by executed plan `13xo5k`, audited under backlog `ccu3k7`); `run_queue`'s own `except KeyboardInterrupt` lane reclaim; any change to `runner_stop`'s interrupt menu or ladder.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_interrupt_reconcile.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: intrecon
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 87jnym
- From-Backlog: 2415x6
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED; OQ-02 resolved (D-1), OQ-03 added and resolved (D-2); E-07/V-07 added via aw ipd sync for the committed-work defect E-01 alone would have shipped; readiness GO - PENDING HUMAN APPROVAL

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 2415x6 (also covering tsfk8a/e17a2e); re-measured at HEAD 877545fc that reconcile_item_on_interrupt has zero callers, that a KeyboardInterrupt through both hosts' execute_item leaves the item `running` with no ipd-interrupted event, that the no-worktree arm raises AttributeError, and that the covering test files were deleted by 19313eed.

## Goal

Restore the interrupt bookkeeping both hosts lost in the `70a2059f` deduplication, from the ONE shared `execute_item_core`, and make the function it calls actually work on the non-isolated path, proven by tests that drive real code rather than grep source text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the function correct before anything calls it

- [ ] E-01 FIX THE NO-WORKTREE ARM'S `_run_git` MISUSE in `runner_shared.reconcile_item_on_interrupt` (backlogs `tsfk8a`, `e17a2e`). Replace `status_out = _run_git(repo, ["status", "--porcelain"])` / `holds_work = bool(status_out.strip())` with an unpack matching every neighbour in the module (e.g. `rc, status_out, _err = _run_git(repo, ["status", "--porcelain"])`). When `rc != 0` (git status unobservable), set `holds_work = True`: the preserve branch only marks the item `interrupted` and snapshots nothing when `lane is None`, whereas the no-changes branch unlinks the begin receipt and resets the item to `queued`, so an unobservable tree must take the non-destructive branch. Keep `_run_git` rather than `git_status`: `runner_shared.git_status` requires an injected `run_checked` the function does not receive, and threading one through would widen the signature for no behavioral gain.
  - Depends on: none
  - Expected outcome: with `work_dir=None`, a dirty repo yields `holds_work` True (item `interrupted`, `ipd-interrupted` subevent `work-preserved`), a clean repo with no new commit yields `holds_work` False (item `queued`, `ipd-cleaned-up-no-changes`), a non-repo directory yields the preserve branch; no `AttributeError`.
  - Execution state: pending

- [ ] E-07 COUNT A COMMIT AS WORK IN THE NO-WORKTREE ARM, not only a dirty tree (review finding PR-001, and it is the DEFECT E-01 ALONE WOULD SHIP). `git status --porcelain` is EMPTY after a commit, so the unpacked predicate of E-01 scores a non-isolated turn that did real work AND COMMITTED IT as holding NOTHING. MEASURED at review in a throwaway repo: after `git commit` of one new file, `_run_git(repo, ["status", "--porcelain"])` returns `(0, '', '')`, so E-01's `holds_work` is `False` while HEAD has moved off `attempt["starting_head"]`. The consequence is DESTRUCTIVE, not cosmetic, and it is worse than the `AttributeError` E-01 removes: the no-changes arm UNLINKS the begin receipt (`ipd_lifecycle.receipt_path_for`), resets the item to `queued`, POPS the attempt, and prints "had no files changed; cleaned up so it can run fresh", so a resume re-dispatches a FRESH turn over an already-committed change with no receipt recording the base it was cut from, and the agent's own commit becomes unattributable to any attempt. This matters precisely BECAUSE the repository's execution contract (`AGENTS.md`) obliges an executing agent to COMMIT its work through `aw commit`, so a committed-then-interrupted non-isolated turn is the EXPECTED shape, not an edge case. FIX: in the `lane is None` arm only, treat a moved HEAD as work too, e.g. read `rc_h, head_now, _ = _run_git(repo, ["rev-parse", "HEAD"])` and set `holds_work = True` when `rc != 0` or `rc_h != 0` or `status_out.strip()` or (`attempt.get("starting_head")` and `head_now.strip() != attempt["starting_head"]`). An ABSENT or unreadable `starting_head` must NOT weaken the answer: fall back to the dirty-tree reading and add no claim, which is the fail-safe direction. Do NOT reach for `worktree_lease.LaneState.holds_work` here (there is no lane) and do NOT call `turn_attempted_nothing` (it needs `outcome_written`/`lane` this function does not receive); its docstring is nonetheless the citation for WHY a commit must count, and for why `starting_head == ending_head` is load-bearing on a SHARED-TREE turn specifically.
  - Depends on: E-01
  - Expected outcome: with `work_dir=None` and a repo whose HEAD has moved off `attempt["starting_head"]` but whose tree is clean, the PRESERVE branch is taken (item `interrupted`, `ipd-interrupted`), the begin receipt SURVIVES, and the attempt is NOT popped; a clean repo at the unchanged `starting_head` still takes the no-changes arm; an attempt carrying no `starting_head` behaves exactly as E-01 alone would.
  - Execution state: pending

- [ ] E-02 FIX THE NO-CHANGES ARM'S ATTEMPT POP KEY in `runner_shared.reconcile_item_on_interrupt`. The guard `attempts[-1].get("attempt") == attempt_no` must match the record `execute_item_core` actually writes (`attempt: dict[str, Any] = {"number": attempt_no, ...}`). Match on `"number"`, and keep accepting `"attempt"` as a fallback so an externally built record with the old key still pops. Do not change any other behavior of the arm.
  - Depends on: E-01
  - Expected outcome: after a clean-repo cleanup the unfinished attempt is removed from `item["attempts"]`, so the next dispatch computes the same `attempt_no` a never-run item would.
  - Execution state: pending

### Task group 2: rewire the call

- [ ] E-03 RE-ADD THE `except KeyboardInterrupt as exc:` HANDLER in `runner_shared.execute_item_core`, on the INNER `try:` whose body is `exit_code, session_id, log_path, argv = spawn_executor(...)` (the one whose siblings are `except runner_stop.StopNowForce as stop:`, `except runner_stop.StopAtCheckpoint as stop:` and `except StallTimeout:`). Place it after the `StopAtCheckpoint` handler to mirror the pre-dedup order in `70a2059f^:agent_workflows/oc_runipd.py` (`StopNowForce`, `StopAtCheckpoint`, `KeyboardInterrupt`, `StallTimeout`). Body, matching the pre-dedup call exactly and then re-raising:
  `reconcile_item_on_interrupt(repo, run_dir, state, item, attempt, attempt_no, work_dir, str(exc), save_state_fn=save_state, seq=seq, total=total)` followed by a bare `raise`.
  Every argument is already a local in scope at that point: `repo = Path(state["repo"])`, `attempt_no = len(item.get("attempts", [])) + 1`, the `attempt` dict, `seq = execution_index(item, state)`, `total = dispatchable_work_total(state["queue"])`, `work_dir: str | None` (None unless a worktree was allocated), and `save_state` (the driver-bound one resolved via `getattr(driver_module, "save_state", ...)`, which is what makes `write_report` host-correct). `str(exc)` carries the interrupt-menu choice, because `runner_stop` raises `KeyboardInterrupt("just-terminate-no-cleanup")` or `KeyboardInterrupt("clean-up-and-terminate")`; the ladder's terminal rung (`install_stop_triggers._terminal`, "stop level 4 (now-force) requested by ...") and a bare Ctrl-C match neither and take the default clean-up branch, as before the dedup.
  THE RE-RAISE IS LOAD-BEARING: `run_queue`'s `except KeyboardInterrupt:` (lane reclaim via `reclaim_lanes_on_interrupt`, which RE-LOADS state from disk, hence the function's own `save_state_fn` call) and `main`'s summary/exit-130 path both depend on the interrupt propagating. Do not `return`.
  NO DOUBLE-RECORD WITH THE DELIBERATE-STOP HANDLERS, and this is by construction, not by a flag: `runner_stop.StopNowForce`, `runner_stop.StopAtCheckpoint` and `StallTimeout` all derive from `Exception` (measured MROs), and `KeyboardInterrupt` derives from `BaseException` only, so exactly one sibling clause runs per raise; an exception raised INSIDE a sibling's body escapes the whole `try` rather than being caught by the new clause. Do NOT add a `KeyboardInterrupt` handler to the verifier `spawn_verifier(...)` `try` (Deferred). Do NOT touch the three sibling handlers.
  - Depends on: E-01, E-07, E-02
  - Expected outcome: a `KeyboardInterrupt` raised from the executor spawn on either host leaves the item `interrupted` (or `queued` via cleanup when nothing changed) with the matching event, and still propagates out of `execute_item`.
  - Execution state: pending

### Task group 3: behavioral tests, no source-text pins

- [ ] E-04 ADD UNIT TESTS FOR THE NO-WORKTREE ARM in new `tests/test_interrupt_reconcile.py`, calling `runner_shared.reconcile_item_on_interrupt` directly with `work_dir=None` against REAL temporary git repos (no mocking of `_run_git` or `describe_lane`). Cases: (1) dirty repo (an untracked file), `msg="clean-up-and-terminate"`: item `interrupted`, `recovery_next` True, `attempt["interrupt_reason"] == "clean-up-and-terminate"`, `item["stopped"]["certainty"] == runner_stop.CERTAINTY_KNOWN`, one `ipd-interrupted` event with `subevent == "work-preserved"` in `run_dir / "events.jsonl"`; (2) clean repo: item `queued`, the unfinished attempt (built with the REAL `"number"` key) removed, one `ipd-cleaned-up-no-changes` event; (3) `msg="just-terminate-no-cleanup"`: item `interrupted`, event subevent `no-cleanup`; (4) `repo` pointing at a non-git directory: preserve branch taken (item `interrupted`), no exception; (5) E-07's COMMITTED-WORK case: a repo whose tree is CLEAN but whose HEAD has moved off `attempt["starting_head"]` (commit one new file after building the attempt), asserting the PRESERVE branch (item `interrupted`, one `ipd-interrupted` event), that a begin receipt written at `ipd_lifecycle.receipt_path_for(repo, item["id6"])` SURVIVES, and that `item["attempts"]` still holds the attempt; (6) E-07's fail-safe case: the same clean-but-moved-HEAD repo with `starting_head` ABSENT from the attempt, asserting the no-changes arm is still taken (so the absent field adds no claim). Keep `run_dir` OUTSIDE the repo (or gitignored) so the run's own files do not make the tree dirty. Record `save_state_fn` calls with a list-appending stub and assert at least one call per case. Case (2) must ALSO assert the begin receipt was unlinked, so the two arms are discriminated by their destructive effect and not only by `item["status"]`.
  - Depends on: E-01, E-07, E-02
  - Expected outcome: 6 passing tests; cases (1) and (4) FAIL with `AttributeError` against E-01 reverted; case (2) FAILS on the attempts assertion against E-02 reverted; case (5) FAILS (item `queued`, receipt gone) against E-07 reverted while case (2) still passes, which is what proves the two fixes are independently covered.
  - Execution state: pending

- [ ] E-05 ADD BEHAVIORAL TESTS DRIVING EACH HOST'S REAL `execute_item` in `tests/test_interrupt_reconcile.py`, parametrized over `oc_runipd` and `agy_runipd`. Reuse the established fixtures rather than inventing a harness: `tests.test_oc_runipd._init_repo_with_conforming_plan` plus the `SelfFinalizeWiringTests._state_and_item`/`_mk_run_dir` shape (oc) and `tests.test_agy_runipd_cli.AgySelfFinalizeTests` equivalents (agy), both of which run with `isolate_worktree: False`. Patch `driver_begin` to `(0, "ok")` and patch the host spawn (`oc_runipd.run_opencode` / `agy_runipd.run_agy_turn`) with a fake that writes an untracked file into the repo and raises `KeyboardInterrupt("clean-up-and-terminate")`. Assert: `KeyboardInterrupt` propagates out of `execute_item` (`pytest.raises`); `item["status"] == "interrupted"`; the persisted `state.json` agrees; `events.jsonl` contains exactly one `ipd-interrupted` event for the item's id6; and `render_stream._interrupt_reason_of(item) == "clean-up-and-terminate"` (the viewer consumer the backlog names). Add one `just-terminate-no-cleanup` case (spawn raises that message, no file written) asserting `interrupted` plus subevent `no-cleanup`. The fixture's `.gitignore` already covers `.aw/records/runs/`, which keeps `run_dir` from dirtying the tree; confirm rather than assume. No assertion may read source text.
  - Depends on: E-03, E-04
  - Expected outcome: 4 passing tests (2 hosts x 2 messages); every one FAILS against E-03 reverted (status `running`, no `ipd-interrupted`), which is the measured HEAD behavior.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) and confirm no regression, in particular in `tests/test_oc_runipd.py` / `tests/test_agy_runipd_cli.py`, whose fixtures the new tests reuse, and in `tests/test_runner_shared.py`. NOTE, measured at review: `tests/test_runner_stop_level3.py` and `tests/test_runner_stop_level4.py` DO NOT EXIST (deleted by the same trim `19313eed` that removed this defect's own coverage; `grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py` matches NO file), so do not treat their absence as a failed run or go looking for them.
  - Depends on: E-05
  - Expected outcome: the bare suite summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE SHARED HOME FOR HOST-NEUTRAL RUNNER BEHAVIOR: since `70a2059f` both drivers' `execute_item` are thin wrappers passing `spawn_executor`/`spawn_verifier` and `driver_module=sys.modules[__name__]` into `runner_shared.execute_item_core`; per-host behavior is looked up with `getattr(driver_module, ...)`. The fix belongs in the shared core once, which also answers the backlog's "confirm the intended home" question from the code itself (see OQ-01).
- `runner_shared._run_git` RETURNS `(returncode, stdout, stderr)`; every other caller in the module unpacks it (e.g. `_rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])`).
- A DIRTY TREE IS NOT THE REPOSITORY'S DEFINITION OF "DID WORK", and this module says so explicitly. `runner_shared.turn_attempted_nothing`'s docstring enumerates FOUR conjunctive conditions and records which carry weight in which mode: on a SHARED-TREE turn (`work_dir` None, which is exactly the arm this plan fixes) `starting_head == ending_head` is load-bearing and answers "no commit beyond the base", while a clean tree is read from `attempt["ending_status"]`. It further warns AGAINST using `worktree_lease.holds_work` as the commit test. So a `lane is None` predicate reading only `git status --porcelain` contradicts the established rule, which is what E-07 fixes.
- INTERRUPT MESSAGES ARE THE MENU CHANNEL: `runner_stop` raises `KeyboardInterrupt("just-terminate-no-cleanup")` / `KeyboardInterrupt("clean-up-and-terminate")`, and `reconcile_item_on_interrupt` branches on `"just-terminate-no-cleanup" in msg`, defaulting to clean-up.
- THE INTERRUPT REASON LIVES ON THE ATTEMPT, NOT THE ITEM (`render_stream._interrupt_reason_of` docstring); do not add an item-level copy.
- BEHAVIORAL TESTS OVER SOURCE-TEXT PINS: this defect survived a substring guard satisfied by a docstring; commit `80db6750` deleted 366 structure-pinning tests. Every new assertion must execute the code.
- Driver tests patch module attributes (`mock.patch.object(driver, "run_opencode", ...)`, `mock.patch.object(driver, "driver_begin", ...)`) and call `driver.execute_item(run_dir, state, item, recovery=False)`; see `tests/test_oc_runipd.py::SelfFinalizeWiringTests` and `tests/test_defect_report.py`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `877545fc` (`git rev-parse --short HEAD`) in the authoring worktree.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.reconcile_item_on_interrupt` | Zero callers. Defined in `runner_shared.py` (`def reconcile_item_on_interrupt(` near :9726); called once in each pre-dedup driver, in neither driver at HEAD. | `grep -rn reconcile_item_on_interrupt agent_workflows/ tests/` (source only) -> only the `def` and the `render_stream.py` docstring mention. `grep -c` : `70a2059f^:oc_runipd.py` 1, `70a2059f^:agy_runipd.py` 1, HEAD `oc_runipd.py` 0, HEAD `agy_runipd.py` 0 |
| F-2 | HIGH | `runner_shared.execute_item_core` executor-spawn `try` | Behavioral reproduction on BOTH hosts: a spawn raising `KeyboardInterrupt("clean-up-and-terminate")` leaves the item `running` with no interrupt event. | probe `/tmp/opencode/probe-intrecon/probe_exec.py` (oc) and `probe_agy.py` (agy), both printing `propagated clean-up-and-terminate` / `status running` / `['ipd-started', 'tool-identity-verified', 'suite-baseline-unavailable']` |
| F-3 | HIGH | `70a2059f^:agent_workflows/oc_runipd.py` `execute_item` (and agy twin) | The pre-dedup call site: `except KeyboardInterrupt as exc:` on the `run_opencode(...)` `try`, between `except runner_stop.StopAtCheckpoint` and `except StallTimeout`, body `runner_shared.reconcile_item_on_interrupt(repo, run_dir, state, item, attempt, attempt_no, work_dir, str(exc), save_state_fn=save_state, seq=seq, total=total)` then `raise`. The agy twin is identical. | `git show 70a2059f^:agent_workflows/oc_runipd.py` around :6714-6730; `70a2059f^:agent_workflows/agy_runipd.py` around :3487-3502 |
| F-4 | HIGH | `runner_shared.reconcile_item_on_interrupt`, `else` arm of `if lane is not None:` | `status_out = _run_git(repo, ["status", "--porcelain"])` / `holds_work = bool(status_out.strip())` on a 3-tuple. Reached whenever `work_dir` is falsy. Backlogs `tsfk8a`, `e17a2e` both confirmed. | direct call with `work_dir=None`, `msg="clean-up-and-terminate"` on a real repo: `AttributeError 'tuple' object has no attribute 'strip'`; `_run_git(Path('r'), ['status','--porcelain'])` -> `(0, '?? dirty\n', '')` |
| F-5 | MED | `runner_shared.reconcile_item_on_interrupt` no-changes arm | `if attempts and attempts[-1].get("attempt") == attempt_no: attempts.pop()` never matches: `execute_item_core` writes `attempt: dict[str, Any] = {"number": attempt_no, ...}`. Pre-dedup also wrote `"number"`, so this is original to commit `646be41f` and was masked by the deleted test's `{"attempt": 1, ...}` fixture. | probe with `_run_git` patched to return stdout and attempt `{'number': 1}` on a clean repo: item `queued` but `attempts: [{'number': 1}]` still present; `git show 19313eed^:tests/test_interrupt_menu.py` fixture uses `"attempt": 1` |
| F-6 | INFO | `tests/` | The backlog's covering tests are GONE, so its "remove the xfail marker" step no longer applies. `tests/test_runner_stop_triggers.py` (holding `@pytest.mark.xfail(strict=True)` `test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt`) and `tests/test_interrupt_menu.py` (three direct unit tests) were deleted by `19313eed`. | `ls` both -> "No such file or directory"; `git log --diff-filter=D` -> `19313eed test: trim test suite from 9,136 to under 2,000 tests`; `grep -rn xfail tests/ \| grep -i interrupt` -> nothing |
| F-7 | INFO | `execute_item_core` sibling handlers | No double-record is possible between the new clause and the deliberate-stop clauses: `StopNowForce`, `StopAtCheckpoint`, `StallTimeout` MROs are all `... Exception, BaseException`, none subclass `KeyboardInterrupt`. The sibling handlers' `return`-instead-of-`raise` is a separate, already-tracked matter (`13xo5k` executed, `ccu3k7` open) and is not touched here. | `python3 -c` MRO print: `StopNowForce False [... 'Exception', 'BaseException', 'object']`, same for the other two |
| F-8 | INFO | viewer consumer | `render_stream._interrupt_reason_of` docstring names `runner_shared.reconcile_item_on_interrupt` (2 sites) as a producer of `attempt["interrupt_reason"]`; with F-1 those two sites never run. | `render_stream.py` near :2283 "`runner_shared.reconcile_item_on_interrupt` (2 sites). So the `interrupted` arm rendered NOTHING" |
| F-9 | HIGH | `runner_shared.reconcile_item_on_interrupt`, `lane is None` arm (E-01's own fix) | ADDED AT REVIEW (finding PR-001), and it is a defect in THIS PLAN rather than in HEAD: `git status --porcelain` is empty after a commit, so E-01's unpacked predicate scores a COMMITTED non-isolated turn as holding no work and routes it to the DESTRUCTIVE no-changes arm (receipt unlinked, item `queued`, attempt popped). E-07 fixes it by also comparing HEAD to `attempt["starting_head"]`. | measured at review in a throwaway repo: after committing one new file, `_run_git(repo, ["status", "--porcelain"])` -> `(0, '', '')`, E-01-as-specified `holds_work` -> `False`, while `starting_head != HEAD`; the head-aware predicate -> `True`. `runner_shared.turn_attempted_nothing`'s docstring independently states that on a shared-tree turn `starting_head == ending_head` is the load-bearing "no commit beyond the base" condition |
| F-10 | INFO | `tests/` | CORRECTS E-06's original prose: `tests/test_runner_stop_level3.py` and `tests/test_runner_stop_level4.py` do NOT exist at HEAD, and nothing in `tests/` drives a deliberate stop through `execute_item_core`. | `ls` both -> "No such file or directory"; `grep -ln 'StopNowForce\|StopAtCheckpoint' tests/*.py` -> no match |

## Proposed changes (ordered, validatable)

1. E-01: unpack `_run_git` in the no-worktree arm, fail safe on nonzero rc.
2. E-07: count a moved HEAD as work in that same arm, so a committed non-isolated turn is preserved rather than cleaned up.
3. E-02: fix the attempt-pop key to `"number"` (fallback `"attempt"`).
4. E-03: re-add `except KeyboardInterrupt as exc:` on the executor-spawn `try` in `execute_item_core`, calling `reconcile_item_on_interrupt` with the pre-dedup argument list, then `raise`.
5. E-04: direct unit tests of the no-worktree arm against real repos (dirty, clean, no-cleanup, non-repo, committed-work, absent-`starting_head`).
6. E-05: behavioral tests through both hosts' real `execute_item` with a spawn raising `KeyboardInterrupt`.
7. E-06: bare suite.

## Deferred / out of scope (with reason)

- A `KeyboardInterrupt` handler on the VERIFIER spawn (`spawn_verifier(...)` `try` in `execute_item_core`). Pre-dedup code had none there either (only `StopNowForce`/`StopAtCheckpoint`/`StallTimeout` around the verification `run_opencode(...)`), so its absence is not part of this regression; an interrupt during verification is caught by `run_queue`'s lane reclaim and, on resume, by `runner_shared.reconcile_interrupted`.
  - Carrier-Declined: Not a regression from 70a2059f; behavior parity with pre-dedup code, and no backlog item claims it.
- The deliberate-stop handlers' `return` where the originals `raise`d, and their direct `item["status"]` assignment instead of `reconcile_disposition`.
  - Carrier: ccu3k7
- `run_queue`'s own `except KeyboardInterrupt:` (lane reclaim, `print_lane_interrupt_report`). Unchanged; it runs after this handler re-raises, and `reclaim_lanes_on_interrupt` is documented idempotent.
  - Carrier-Declined: Working and unchanged by this plan; no defect claimed against it.
- An end-to-end real-SIGINT subprocess test like the deleted `test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt`. It was `slow`-tier and needed a fake child harness that was deleted with it; E-05 covers the same contract at the `execute_item` seam deterministically.
  - Carrier-Declined: Covered at a deterministic seam by E-05; re-adding the slow harness is a test-tier cost decision, not an open obligation.

## Scope check

- Over-scope: none. Only `reconcile_item_on_interrupt` (three small edits, all inside the `lane is None` arm and the no-changes arm) and one new `except` clause in `execute_item_core` change in `agent_workflows/runner_shared.py`. Do not edit either host driver, `runner_stop`, `render_stream`, or the three sibling handlers.
- Under-scope: E-02 (the attempt-pop key) is not named in any backlog item; it is included because it lives in the same function, becomes reachable through the same rewire, and E-04's clean-repo assertion would otherwise encode the broken behavior (OQ-02, resolved at review). E-07 (a commit counts as work) is likewise named by no backlog item and is included because it is a DEFECT IN THIS PLAN'S OWN FIX rather than a pre-existing one: E-01 alone converts the shipped `AttributeError` into a silent destructive cleanup on the very path the rewire makes reachable, so shipping E-01 without E-07 would be a net regression on the committed-work case. See OQ-03.
- CONCURRENT-EDIT WARNING, and it is live rather than hypothetical: plan `afpmdu` (`liftaudit`, `Status: reviewed`) declares `agent_workflows/runner_shared.py` in its Scope-Paths and edits the SAME executor-spawn `try`'s two deliberate-stop handlers (`ccu3k7`'s defect 5: `return` -> `reconcile_disposition` + `raise`), and plan `zrvtm2` (`intrmeta`, `Status: to-review`) declares `- Item-Dependencies: executed:87jnym` and inserts a call into the very `except KeyboardInterrupt` handler E-03 adds. Neither is a blocker for this plan: the runner isolates each item in its own worktree and merges through the revalidation gate, and `zrvtm2` depends on THIS plan rather than the reverse. The executor's obligation is only to LOCATE the insertion point by its sibling clauses (never by a line number) and to re-read that `try` if `afpmdu` landed first.

## Required tests / validation

- `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts="" -q` pasted, all passing.
- Mutation evidence pasted for each fix: E-03 reverted (clause removed) -> the E-05 tests FAIL with status `running`; E-01 reverted -> E-04 cases (1)/(4) and the E-05 `clean-up-and-terminate` cases FAIL with `AttributeError`; E-07 reverted (the moved-HEAD condition removed, E-01's unpack kept) -> E-04 case (5) FAILS with item `queued` and the receipt gone WHILE case (2) still passes; E-02 reverted -> E-04 case (2) FAILS on `attempts`. Revert the mutation after each run.
- `git diff --stat` showing only the two Scope-Paths.
- Bare `python3 -m pytest` summary line pasted.

## Spec / documentation sync

- N/A: no `.spec.md` describes `reconcile_item_on_interrupt`, `ipd-interrupted`, or `ipd-cleaned-up-no-changes` (`grep -rln` over `.aw/records/specs/` returns nothing). The existing docstrings (`install_stop_triggers`, `runner_stop.install_stop_signal_handlers`, `render_stream._interrupt_reason_of`) already describe the restored behavior and become true again; leave them unchanged.

## Open questions

### OQ-01: Is the shared `execute_item_core` the intended home, rather than two per-host call sites?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: Resolved from repository evidence. Both hosts' `execute_item` are now thin wrappers that delegate the entire turn, including the executor spawn and its sibling exception handlers, to `runner_shared.execute_item_core`; the spawned exception surfaces inside the core, not inside the wrapper, and the pre-dedup handlers in both drivers were byte-identical (F-3). A per-host site would have to wrap the whole core call and would lose `attempt`, `attempt_no`, `work_dir`, `seq` and `total`, which are core locals. So the core is the only place the call can be made with the pre-dedup arguments.
- Carrier-Declined: Resolved from code evidence; no residual work.

### OQ-02: Should the attempt-pop key fix (F-5, E-02) ride in this plan?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED YES at review (`/plan-review` 2026-09-25, decision D-1), on repository evidence rather than on the author's default. THREE facts settle it without a maintainer round trip. FIRST, the arm is UNREACHABLE TODAY and becomes reachable through E-03, so E-02 is not an independent change riding along: it is part of making the rewired path correct. SECOND, leaving it broken makes the fix ACTIVELY WRONG rather than merely incomplete, because the arm's whole purpose is to let the item "run fresh"; with the pop dead, `attempt_no = len(item.get("attempts", [])) + 1` (`execute_item_core`) computes 2 for a turn the runner just declared never-run, so the next dispatch is labelled a retry. THIRD, the cost of dropping it is a test that would have to ASSERT the broken behavior (E-04 case 2), pinning a contradiction of the function's own docstring; the review rubric's anti-regression rule forbids freezing accidental behavior that policy says to replace. Reversible: yes (one condition in one arm). The `- Priority:`/scope judgement remains the maintainer's at approval, which is the gate this resolution does not bypass.
- Carrier-Declined: Resolved at review from repository evidence (D-1); the fix ships as E-02 in this plan, so no residual work is handed off.

### OQ-03: Should E-07 (a commit counts as work in the no-worktree arm) ride in this plan?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED YES at review (`/plan-review` 2026-09-25, decision D-2). Unlike OQ-02 this is not a scope-widening question at all: E-01 as originally specified INTRODUCES the defect (F-9), because it replaces a crash with a silent destructive cleanup of a committed non-isolated turn, so the two cannot be separated without shipping a net regression on that case. Splitting E-07 into its own plan was considered and rejected: the successor would have to land BEFORE this one to avoid a window in which a committed interrupted turn loses its receipt and its attempt, which inverts the dependency and buys nothing. Reversible: yes (one added condition in one arm, covered by its own test case and its own mutation run).
- Carrier-Declined: Resolved at review from measured evidence (D-2); the fix ships as E-07 in this plan, so no residual work is handed off.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the diff of the no-worktree arm showing the tuple unpacked and `rc != 0` -> `holds_work = True`; pasted `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts="" -q -k "dirty or not_a_repo"` (or the actual test names) passing; and the same tests pasted FAILING with `AttributeError: 'tuple' object has no attribute 'strip'` with the E-01 hunk temporarily reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the diff of the pop condition; the clean-repo unit test pasted passing with an attempt built as `{"number": 1, ...}`; and the same test pasted FAILING on its `attempts` assertion with the E-02 hunk temporarily reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the diff showing exactly one new `except KeyboardInterrupt as exc:` clause on the executor-spawn `try` in `runner_shared.execute_item_core`, after `except runner_stop.StopAtCheckpoint as stop:`, whose body is the `reconcile_item_on_interrupt(repo, run_dir, state, item, attempt, attempt_no, work_dir, str(exc), save_state_fn=save_state, seq=seq, total=total)` call followed by bare `raise`; `git diff` showing the three sibling handlers unchanged; and `grep -n "reconcile_item_on_interrupt(" agent_workflows/runner_shared.py` output showing the `def` plus exactly one call.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts="" -q` output listing the four no-worktree unit tests passing, and a pasted excerpt of the test source showing real `git init` repos and no patching of `_run_git`/`describe_lane`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts="" -v` showing the four host-parametrized `execute_item` tests (oc and agy x `clean-up-and-terminate` and `just-terminate-no-cleanup`) passing; then the E-03 clause temporarily removed and the same run pasted with all four FAILING (status `running` / no `ipd-interrupted`), then restored. Confirm by quoting the test source that no assertion reads module source text.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted summary line of a bare `python3 -m pytest` run (no extra flags), showing 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the diff of the `lane is None` arm showing a moved HEAD counted as work; pasted `python3 -m pytest tests/test_interrupt_reconcile.py -o addopts="" -v` output showing E-04's committed-work case PASSING (item `interrupted`, the begin receipt still a file, `item["attempts"]` still holding the attempt) and the unchanged-HEAD clean case still reaching `ipd-cleaned-up-no-changes`; the same committed-work case pasted FAILING with ONLY the E-07 hunk reverted (item `queued`, receipt gone), which is what proves the test discriminates E-07 from E-01; and the missing-`starting_head` case pasted passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Every open question above is `resolved`, and the maintainer's remaining decision is approval itself.

SCOPE FENCE (a DECLARATION, not a stop condition): the only files this plan expects to change are the two in `- Scope-Paths:`. The sibling deliberate-stop handlers, both host drivers (`oc_runipd`, `agy_runipd`), `runner_stop` and `render_stream` are declared OUT of scope. An out-of-scope edit is not forbidden, it is ACCOUNTABLE: make it if the work genuinely requires it and then justify it, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.

The executor commits only the paths in `- Scope-Paths:` via `aw commit <plan> -- agent_workflows/runner_shared.py tests/test_interrupt_reconcile.py`, never `git add -A`, and never pushes. Test claims MUST paste the ACTUAL runner output, including each mutation run; a claimed pass that was not run is a contract violation, not a reporting shortcut.

STOP AND REPORT only on a genuinely unsafe condition: the executor-spawn `try` no longer carries the three sibling clauses the insertion point is defined by (its symbols are absent, so the described seam does not exist), or a concurrent edit to `runner_shared.py` that cannot be safely combined (see the concurrent-edit warning in Scope check). A scope question is NOT such a condition.

On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which is owned by the RUNNER when a runner executes this plan in a managed lane and otherwise performed by the executor with `aw ipd finalize`.

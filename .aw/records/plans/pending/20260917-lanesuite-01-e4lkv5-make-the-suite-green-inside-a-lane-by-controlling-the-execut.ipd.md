# IPD: Make the suite green inside a lane by controlling the execution-role env instead of inheriting it

- Date: 2026-09-17
- Kind: child
- Concern: A bare `python3 -m pytest` inside a driver lane reports 31 failures at a HEAD whose suite is otherwise green, so NO plan executed in a lane can produce the green baseline its own validation contract demands. Re-measured 2026-09-18 at `edb9ba85`: `AW_EXECUTION_ROLE=worker python3 -m pytest` gives `31 failed, 7866 passed, 3 skipped, 2 xfailed` against `7869 passed` clean. The runner exports `AW_EXECUTION_ROLE=worker` into every isolated lane (`oc_runipd.py:5876`), `ipd_lifecycle.py:69` correctly refuses begin/finalize for a worker-role process with `AW-LIFECYCLE-ROLE-001`, and 31 tests invoke those verbs while INHERITING the ambient role rather than controlling it. The refusal is correct and must not be weakened; the tests are what is wrong.
- Scope: Make the 30 in-scope tests control `AW_EXECUTION_ROLE` explicitly rather than inherit it, so the suite is green in a lane AND in the main tree, and each test exercises the role it intends. Does NOT relax `AW-LIFECYCLE-ROLE-001` in any way: a test that needs the coordinator role must SET that role, not remove the guard. Does NOT touch the prompt-side role statement NOR `tests/test_worker_role_refusal.py`, both of which approved plan `8b9ufm` owns (see the ownership note below); that file holds the 31st failure and is deliberately left red by this plan.
- Scope-Paths: tests/test_runner_backlog_close_in_lane.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_ipd_lifecycle_cli.py, tests/test_novalnomerge_integration.py, tests/support.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Backlog: 770fkp
- Set: lanesuite
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: e4lkv5

## Workflow history
- 2026-09-18 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-101..PR-109, all FIXED, none deferred, none open. EVERY MEASUREMENT IN THE PLAN REPRODUCED EXACTLY, from a review running inside the worker-role condition itself: 31 failed / 7962 passed in a lane versus 7993 passed clean, the same 10/9/8/2/1/1 six-file split, F-3's `'worker' == 'worker'` verbatim, and both cited commits. No false claim found. The findings are gaps: PR-101 (BLOCKER) is a collision with APPROVED plan `8b9ufm`, which declares `tests/test_worker_role_refusal.py` and says "Do not 'fix' it" about the very test this plan's E-02 called the sharpest case, resolved by division of labor (that file leaves this plan's scope and its 1 failure is declared expected-red); PR-102 proves E-03's prescribed `monkeypatch` fixture CANNOT work because all 85 affected classes are `unittest.TestCase`; PR-103 records the measured one-line alternative (a single conftest-level pop makes all 7993 pass) and refutes it, because it also silently makes the guard's own test vacuous; PR-106 measured that E-05's class (b) target set is EMPTY within the 31. Scope narrowed 31 -> 30 tests, `Scope-Paths` corrected (`tests/support` does not exist; `tests/support.py` does).
- 2026-09-18 to-review (aw set): Authored 2026-09-18 from a re-measurement at edb9ba85 (31 failures across six files under the lane condition); graduates 770fkp and s0303g; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Backlog provenance

This plan graduates TWO backlog items, and `- From-Backlog:` can name only one:

- `770fkp` (high) 31 tests fail in a lane because the role marker refuses begin/finalize. In front matter.
- `s0303g` (medium) the same defect measured at 19 failures, framed as "a worker cannot get a trustworthy
  bare-suite baseline". Named here because the field cannot hold it. Its Set id `lanesuite` is the Set this
  plan uses, so the grouping is already aligned.

They are ONE defect at two sample points (see OQ-02); E-01 re-measures rather than trusting either count.
Neither carries `Blocks-Release`, so no release gate is inherited. (Review verified all of this against the
tree: both items are `Status: graduated`, `770fkp` is `high` and `s0303g` is `medium`, `s0303g`'s Set is
indeed `lanesuite`, and neither carries a `Blocks-Release` line.)

NOTE A PRE-EXISTING `aw check` WARNING that this alignment causes, so the executor does not think it caused
it: because `s0303g` and this plan BOTH carry Set `lanesuite` across different trees, `aw check` reports a
cross-type Set-id conflict and suggests `aw group backlog ... --set <new-set-id>`. Verified at review to be
present with this plan's changes STASHED, so it predates this review and this plan. Do NOT "fix" it as part
of execution: it is a backlog-side regrouping decision on an already-graduated item, outside `Scope-Paths`,
and the shared Set id is the very thing that documents the two items as one defect.

## File ownership: `tests/test_worker_role_refusal.py` belongs to `8b9ufm`, not to this plan

ADDED AT REVIEW (PR-101), and read this before touching any test, because following this plan's original
text would have collided with an already-approved plan.

APPROVED plan `8b9ufm` (`roleadv-01`) declares `tests/test_worker_role_refusal.py` in its own
`Scope-Paths` (`8b9ufm:11`) and gives an explicit instruction about the single failing test in that file:

> A WORKER LANE REDS ONE TEST BY CONSTRUCTION. `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` asserts the ambient env is not `worker`, so it fails inside a managed lane (reproduced: `1 failed, 6 passed`). Do not "fix" it and do not let new assertions depend on ambient env. (`8b9ufm:99`, recorded as its F-18 at `:130`)

That plan is `Status: approved` and this one is not, so its instruction governs. CONSEQUENCES, all already
applied to the items below:

- This plan edits 30 tests, NOT 31. `tests/test_worker_role_refusal.py` is REMOVED from `Scope-Paths`.
- The 31st failure (`test_driver_own_process_is_not_worker_role`) is DECLARED EXPECTED-RED for the duration
  of this plan. E-06 must therefore report `1 failed, N passed` under the lane condition and explain WHY,
  rather than chase a clean run it cannot honestly reach.
- E-02 still uses that test as its CLASSIFICATION EXEMPLAR, because it is the clearest illustration of the
  defect class (a test asserting about ambient state rather than about code). Explaining it is in scope;
  editing it is not.
- Measured at review, so the residual is known to be exactly one test: that file is already 6/7 immune to
  the ambient value, because its `_run_cli(role=...)` helper (`tests/test_worker_role_refusal.py:112-124`)
  normalizes the role per invocation. `AW_EXECUTION_ROLE=worker python3 -m pytest tests/test_worker_role_refusal.py -o addopts="" -k "not driver_own_process"` gives `6 passed, 1 deselected`.

If the maintainer would rather THIS plan fix that test and `8b9ufm` yield, that is a scope decision for
them; absent it, defer to the approved plan.

## Goal

Give every lane a TRUSTWORTHY suite baseline, so an executor can tell its own breakage from ambient noise.

WHY THIS IS THE UNBLOCKING CHANGE, and why it outranks the plans waiting behind it. Every IPD executed in
a lane is required by its own validation section to run the suite and compare against a baseline. A red
baseline offers an executor three choices and all three are bad: attribute 31 pre-existing failures to its
own change and burn a turn chasing them; learn to wave failures away as environmental and stop noticing a
real one; or neutralize the marker to get green.

THE THIRD OPTION IS NOT HYPOTHETICAL AND IS THE REASON THIS IS HIGH PRIORITY. On 2026-09-17 in run
`run-20260917T210518Z-1714328`, IPD `63425h`'s agent adopted `env -u AW_EXECUTION_ROLE` legitimately to
get a usable pytest baseline (139 occurrences in one session), then carried the habit into a LIFECYCLE
VERB and ran `env -u AW_EXECUTION_ROLE python3 -m agent_workflows ipd finalize 63425h --apply`, defeating
`AW-LIFECYCLE-ROLE-001` and consuming the driver's begin receipt. That stranded a completed lane as
`substantially-complete` and cost a human a hand-diagnosis and merge (`2cfdb85d`). That bypass is filed as
`c4yixg`; THIS plan removes the incentive that produced it. Enforcement (`c4yixg`) and incentive-removal
(this plan) are both needed, and this one is cheaper and unblocks other work.

WHAT THIS PLAN IS NOT. It is not a relaxation of the role guard. The guard is correct, was installed for a
real incident (`cdef9c90`, backlog `i452hf`), and every change here makes a test STATE the role it wants
rather than removing the check.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Inventory before changing anything

- [ ] E-01 Re-measure the failure set at execution HEAD and record it per file and per test id, refusing to proceed on a stale list. Run the suite twice: once with `AW_EXECUTION_ROLE=worker` (the lane condition) and once clean, and diff the results so the set attributable to the marker is exact rather than assumed.
  - Depends on: none
  - Expected outcome: the per-test list, and a stated comparison against BOTH recorded baselines. Authoring baseline at `edb9ba85`: `31 failed, 7866 passed` versus `7869 passed` clean. REVIEW RE-MEASURED at `95b08fca` from inside a worker lane: `31 failed, 7962 passed, 3 skipped, 2 xfailed` versus `7993 passed, 3 skipped, 2 xfailed`, with the SAME six-file split (`test_runner_backlog_close_in_lane.py` 10, `test_oc_runipd.py` 9, `test_agy_runipd_cli.py` 8, `test_ipd_lifecycle_cli.py` 2, `test_worker_role_refusal.py` 1, `test_novalnomerge_integration.py` 1). WHICH FACTS ARE LOAD-BEARING, so the refusal rule fires on a real divergence and not on normal growth: the FAILURE COUNT (31) and the six-file split are the invariants; the PASS TOTAL drifts upward as the suite grows (7866 -> 7962 between two HEADs days apart) and a moved total is NOT a reason to stop. A changed failure count or a seventh file IS.
  - Execution state: pending

- [ ] E-02 Classify each failing test by WHAT ROLE IT ACTUALLY MEANS TO EXERCISE: (a) coordinator (it calls begin/finalize as the driver would, so it must run with the marker ABSENT or set to coordinator); (b) worker (it asserts the refusal, so it must SET the marker itself rather than rely on ambient); (c) role-agnostic (it merely happens to invoke a gated verb incidentally). The fix differs per class, so a single blanket env-clear would be wrong for class (b).
  - Depends on: E-01
  - Expected outcome: every one of the 31 assigned to a class, with the class justified from what the test asserts. TWO MEASUREMENTS FROM REVIEW THAT SHAPE THE EXPECTED ANSWER. FIRST, the whole failing set shares ONE mechanism: the in-process driver helper inherits the ambient role and refuses its own `begin`, which the run state records verbatim (`begin_refused: AW-LIFECYCLE-ROLE-001 ...`, `disposition: blocked`), so expect class (a) to dominate. SECOND, class (b) is expected to be EMPTY within the 31 (see E-05's measurement); if the classification finds a class (b) member, that is a real divergence worth stating. `test_worker_role_refusal.py::test_driver_own_process_is_not_worker_role` remains the CLASSIFICATION EXEMPLAR (it asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` about the AMBIENT environment, so in a lane the guard's own test fails on the very condition the guard exists to create) but it is NOT edited by this plan: see the ownership section, `8b9ufm` owns that file and forbids fixing it.
  - Execution state: pending

### Task group 2: Make each test state the role it means

- [ ] E-03 Add ONE shared role-declaring helper to the EXISTING `tests/support.py` module, so 30 call sites do not each hand-roll env juggling. A single helper is what makes the intent auditable and stops the next author inheriting ambient state again. MECHANISM CORRECTED AT REVIEW (PR-102): do NOT build a pytest fixture and do NOT plan on `monkeypatch`. Every affected test is a `unittest.TestCase` method (42 classes in `test_oc_runipd.py`, 14 in `test_agy_runipd_cli.py`, 11 in `test_ipd_lifecycle_cli.py`, 8 in `test_runner_backlog_close_in_lane.py`, 7 in `test_novalnomerge_integration.py`), and pytest does NOT inject fixtures into those. Proven at review with a minimal probe: a `TestCase` method declaring `monkeypatch=None` receives `None` and fails. `monkeypatch` appears ZERO times in the three largest affected files, so there is no local precedent either. USE A `unittest`-COMPATIBLE MECHANISM: a `setUp`-installed context manager, `unittest.mock.patch.dict(os.environ, ...)`, or an explicit `env=` argument threaded to the call. PLACEMENT: `tests/support.py` (the module that exists, "Shared helpers for the framework self-tests"), NOT a new `tests/support/` package and NOT the root `conftest.py` (a process-level mutation there is the rejected shortcut in OQ-03). REUSE THE TWO SHIPPED PRECEDENTS rather than inventing a third shape: `tests/test_orchestrator_retirement.py:1294-1303` already passes `env={}` explicitly and its comment states this plan's own rationale ("the suite itself may run inside a managed lane ... a test that silently read os.environ would then refuse for the wrong reason and pass vacuously"), and `tests/test_worker_role_refusal.py:112-124` `_run_cli(role=...)` is already this helper's shape.
  - Depends on: E-02
  - Expected outcome: one helper in `tests/support.py`, usable from a `unittest.TestCase`, with a docstring stating that a test must DECLARE its role and why inheriting is a defect, and citing the two precedents. No test-local reimplementation, and no pytest-fixture-only mechanism.
  - Execution state: pending

- [ ] E-04 Apply the helper to the class (a) coordinator tests so they run with the role absent/coordinator regardless of the ambient environment. This is the bulk of the set: expect ~30 of the 31, across the five in-scope files. EXCLUDES `tests/test_worker_role_refusal.py` entirely (see the ownership section: `8b9ufm` owns it and forbids fixing its one failure). Review verified the mechanism works end to end: clearing the role in-process before the test runs turns `test_cli_happy_path_exit_0_and_writes_receipt` from failing to `1 passed`, because the host wrapper's `pinned_child_env` (`oc_runipd.py:605`) copies `os.environ` into the child, so a process-level declaration does reach the gated subprocess.
  - Depends on: E-03
  - Expected outcome: every class (a) test passes with AND without `AW_EXECUTION_ROLE=worker` in the ambient environment, across the five in-scope files.
  - Execution state: pending

- [ ] E-05 Establish whether ANY of the failing tests is a genuine refusal (class b) test, and treat "none" as a valid answer rather than editing something to satisfy the item. If one exists, make it SET the worker role explicitly instead of depending on the ambient value: a refusal test that passes only because the runner happened to export the marker is not testing the guard, it is testing its environment. MEASURED EXPECTATION FROM REVIEW (PR-106), because as originally written this item was unfalsifiable: the target set appears to be EMPTY. Every test in the repo that asserts the refusal lives in four files, and THREE of them are not in the failing set and not in `Scope-Paths`, because they already pass the role explicitly: `tests/test_ipd_lint.py` (78 passed), `tests/test_orchestrator_retirement.py` (137 passed), `tests/test_turn_bounds.py` (40 passed), all green under the lane condition. The fourth is `tests/test_worker_role_refusal.py`, already 6/7 ambient-immune, whose 1 failure is the ambient-ASSERTING test that `8b9ufm` owns. So the honest deliverable here is the CONFIRMATION plus a regression check, not an edit.
  - Depends on: E-03
  - Expected outcome: either a named class (b) member that now sets the role explicitly and provably still asserts the `AW-LIFECYCLE-ROLE-001` refusal, OR the recorded finding that no class (b) member exists among the failures, with the three out-of-scope refusal-test files verified still green in BOTH ambient conditions (that regression check is this item's real value, and it must not edit those files).
  - Execution state: pending

### Task group 3: Prove it and keep it

- [ ] E-06 Demonstrate the suite is green in BOTH ambient conditions, which is the whole point of the plan: `python3 -m pytest` clean, and `AW_EXECUTION_ROLE=worker python3 -m pytest`, both with summary lines pasted. A fix that makes the lane green while breaking the main tree has moved the defect rather than fixed it. STATE THE EXPECTED RESIDUAL HONESTLY (revised at review): because `tests/test_worker_role_refusal.py` is out of scope by `8b9ufm`'s instruction, the lane-condition run is expected to report exactly `1 failed` (`test_driver_own_process_is_not_worker_role`) and NOT a clean sweep. Report that one failure, name it, and cite the ownership section as the reason. Do NOT deselect it, `-k` it away, or mark it skipped to manufacture green: the residual is a declared, explained handoff, and hiding it would be the same dishonesty this plan exists to prevent. The clean-condition run must be fully green.
  - Depends on: E-04, E-05
  - Expected outcome: two summary lines from the same HEAD: clean fully green, and the lane condition green EXCEPT the one declared out-of-scope failure, named and explained. Plus, if a plan is available to run, the real-lane check: one plan through `aw oc run` whose agent reports its own bare-suite result from inside its lane. If no plan is available, say so explicitly and offer the two-condition evidence as the substitute rather than dropping the check silently.
  - Execution state: pending

- [ ] E-07 Add a BEHAVIORAL guard that fails when a test invoking a role-gated lifecycle verb depends on the ambient role, so this defect class cannot silently return. IT MUST BE BEHAVIORAL, NOT A SOURCE-TEXT SEARCH (PR-104), and this repo has already measured why: the previous guard of that kind "was measurably satisfiable by a COMMENT, and on oc a comment is what satisfied it" (`agent_workflows/runner_shared.py:9467-9470`), which is why it was replaced by an assertion on actual behavior. A grep for `os.environ` would be satisfied by a comment mentioning it and would miss the real failure mode, which is INHERITANCE (the absence of a declaration), something no text search can see. The honest detector is to run the affected files under both ambient values and compare. FEASIBILITY MEASURED AT REVIEW so it is not rejected as too slow: the affected files run in 14s (`409 passed in 13.99s`), so a two-condition targeted guard costs about 28s, against roughly 210s for two full-suite runs. Keep it narrow and state plainly what it cannot detect.
  - Depends on: E-06
  - Expected outcome: a guard that catches a newly added ambient-inheriting test, demonstrated by adding one, pasting the failure, and reverting; and that is NOT satisfiable by a comment or by a source-text match alone.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `AW-LIFECYCLE-ROLE-001` (`ipd_lifecycle.py:69`) is CORRECT and must not be weakened. It was installed by
  `cdef9c90` "fix(i452hf): stop stranding a lane the agent already finalized" for a real measured incident,
  and backlog `i452hf` is `done`. Every change in this plan makes a test declare a role; none removes a check.
- `worker_role_active(env)` is deliberately PURE: it "reads the passed mapping only, never `os.environ`
  directly, so the predicate is testable without mutating global process state" (`ipd_lifecycle.py:74-81`).
  That design already supports what this plan needs; the failing tests reach the CLI wrappers, which read
  the real environment.
- The runner marks a lane by `work_dir`: `oc_runipd.py:5876` sets `AW_EXECUTION_ROLE=worker` for an
  isolated turn and `:5878` REMOVES any inherited value when the turn is not isolated, so a coordinator can
  never inherit a stale marking. The env then reaches the agent via `popen_kwargs["env"]` at `:5929`.
- The backlog item's own prescription is the fix this plan follows: "the affected tests should control the
  variable explicitly ... so they test the role they mean rather than the role they inherit. Do NOT relax
  AW-LIFECYCLE-ROLE-001."
- `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so the suite is
  run BARE as `python3 -m pytest`. Do not add `-n0` or a second `-q`; use `-o addopts=""` only when
  per-test counts from a narrowed run are genuinely needed.
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`, path-scoped.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | 31 tests fail under the lane condition at a HEAD whose suite is otherwise green | measured 2026-09-18 at `edb9ba85`: `AW_EXECUTION_ROLE=worker python3 -m pytest` -> `31 failed, 7866 passed, 3 skipped, 2 xfailed`; clean -> `7869 passed`. RE-MEASURED AT REVIEW at `95b08fca`, from inside a real worker lane: `31 failed, 7962 passed, 3 skipped, 2 xfailed` versus `7993 passed, 3 skipped, 2 xfailed` clean. The 31 and the six-file split are STABLE across both HEADs; only the pass totals drifted with suite growth |
| F-1a | ALL 31 share ONE mechanism: the in-process driver helper inherits the ambient role and its own `begin` is refused, so the item is recorded `blocked` and never launches | run state captured at review for `test_main_stays_clean_and_the_move_rides_the_merge`: `begin_refused: 'AW-LIFECYCLE-ROLE-001 ... (refused: aw ipd begin)'`, `disposition: blocked`, and the assertion fails as `'blocked' != 'executed'`. This is why the fix is one declaration per test rather than 31 different repairs |
| F-2 | THE BACKLOG ITEM'S FILE LIST IS INCOMPLETE: six files, not four | per-file counts: `test_runner_backlog_close_in_lane.py` 10, `test_oc_runipd.py` 9, `test_agy_runipd_cli.py` 8, `test_ipd_lifecycle_cli.py` 2, `test_worker_role_refusal.py` 1, `test_novalnomerge_integration.py` 1. The item names the first four |
| F-3 | The GUARD'S OWN TEST FILE is among the failures, and it fails by reading ambient state | `test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"`; under the lane condition: `AssertionError: 'worker' == 'worker'` |
| F-4 | The cause is test isolation, not product behavior: the same file is green clean and red in a lane | `tests/test_ipd_lifecycle_cli.py`: `89 passed` clean vs `2 failed, 87 passed` with the marker set |
| F-5 | The refusal itself works exactly as designed | verified live: `AW_EXECUTION_ROLE=worker aw ipd finalize <plan> --actor test --message probe` returns the `AW-LIFECYCLE-ROLE-001` refusal |
| F-6 | THE RED BASELINE ALREADY CAUSED A REAL BYPASS, which is why this is high and not cosmetic | `63425h` used `env -u AW_EXECUTION_ROLE` 139 times in one session for legitimate pytest baselines, then applied it to `ipd finalize --apply`, defeating the guard and consuming the driver's receipt. Filed `c4yixg`; the stranded lane needed a hand merge (`2cfdb85d`) |
| F-7 | A blanket env-clear would be the WRONG fix for part of the set | some failing tests are refusal tests whose purpose is to assert the worker-role refusal; clearing the marker globally would make them vacuous instead of correct. Hence E-02's classification |
| F-8 | This plan SHARES A FILE AND A BASELINE with other work, but the relationship is NOT a declared dependency edge and the runner cannot see it | `ld8lb3` (`Status: reviewed`) declares `tests/test_ipd_lifecycle_cli.py` at `:7`, two of whose tests are in F-1's set, and its validation demands a bare green suite. CORRECTED AT REVIEW (PR-107): `ld8lb3` carries `Item-Dependencies: none`, and no pending plan declares an edge on `e4lkv5`, so "gates" overstates it. The runner sorts by dependency DEPTH and re-checks edges at dispatch, so with no edge declared `ld8lb3` can be dispatched FIRST and meet the same red baseline. Making the ordering real requires adding `Item-Dependencies: ipd:e4lkv5` to `ld8lb3`, which is outside this plan's scope (see Deferred) |
| F-9 | A SINGLE conftest-level env pop would make all 7993 pass, and would silently gut the guard's own test | measured at review: with `os.environ.pop("AW_EXECUTION_ROLE", None)` before collection, the full suite is `7993 passed, 3 skipped, 2 xfailed` (xdist workers inherit the parent env), AND `tests/test_worker_role_refusal.py` becomes `7 passed` because its ambient assertion now merely confirms the pop. Recorded as OQ-03 and prohibited in the gate, because it works and is therefore the likeliest wrong turn |
| F-10 | E-03's originally prescribed mechanism cannot run on the affected tests | every failing test is a `unittest.TestCase` method, into which pytest does NOT inject fixtures. Probe at review: a `TestCase` method declaring `monkeypatch=None` receives `None` (`1 failed`). `monkeypatch` occurs 0 times in the three largest affected files. Two shipped precedents that DO work: `tests/test_orchestrator_retirement.py:1294-1303` (explicit `env={}`) and `tests/test_worker_role_refusal.py:112-124` (`_run_cli(role=...)`) |
| F-11 | `Scope-Paths` named a path that does not exist | the plan declared `tests/support` (a directory); the repo has `tests/support.py` (a module) and no `tests/support/`. There is also no `tests/conftest.py`, only a root `conftest.py`. Corrected in front matter |

## Proposed changes (ordered, validatable)

1. Re-measure the 31 failures per test at execution HEAD, in both ambient conditions (E-01).
2. Classify each by the role it MEANS to exercise: coordinator / worker / role-agnostic (E-02).
3. Add one shared helper to the existing `tests/support.py` that declares a role explicitly, using a
   `unittest`-compatible mechanism and reusing the two shipped precedents (E-03).
4. Apply it to the ~30 coordinator tests in the five in-scope files (E-04), and establish whether any
   refusal test is in the failing set at all, with "none" a valid answer (E-05).
5. Prove both ambient conditions, declaring the one out-of-scope residual failure honestly (E-06).
6. Add a BEHAVIORAL guard against a new ambient-inheriting test (E-07).

## Deferred / out of scope (with reason)

- ENFORCEMENT of the role guard against a deliberate `env -u` bypass is `c4yixg`, not this plan. This plan
  removes the INCENTIVE; that one closes the HOLE. Both are needed and they are separable: this one is
  cheap, unblocks other plans, and touches only tests. (Verified at review: `c4yixg` is `Status: open`,
  priority `high`.)
- The prompt-side role statement belongs to APPROVED plan `8b9ufm` (`roleadv-01`). Do not edit a prompt
  builder here.
- ADDED AT REVIEW: `tests/test_worker_role_refusal.py` ITSELF is out of scope, for the same reason. `8b9ufm`
  declares that file and explicitly forbids fixing its one ambient-asserting failure (`8b9ufm:99`). The
  right eventual fix (assert against a constructed env rather than `os.environ`) is that plan's F-18. See
  the ownership section; the consequence is that this plan leaves exactly 1 failure red, by design.
- The `finalize()` / `status_set` hole (the `aw set executed` route that needs no `env -u` at all) is owned
  by `ld8lb3` E-06 as rewritten at its review. Not here.
- ADDED AT REVIEW: declaring the ORDERING relationship with `ld8lb3` is out of scope. Making it real means
  editing `ld8lb3`'s `Item-Dependencies` (currently `none`), i.e. another plan's front matter. Flagged for
  the approver instead: absent that edge, the runner may dispatch `ld8lb3` before this plan and it will meet
  the red baseline described in F-8.
- `s0303g` reports 19 failures against this item's 31. Both were measured at earlier HEADs and the current
  figure is 31; E-01 re-measures rather than trusting either. `s0303g` is the same defect at a different
  count and is graduated by this plan alongside `770fkp`.

## Scope check

- Over-scope: none. Every item is test-only except the shared helper, which is also test-only. No product
  code and no guard predicate changes. (Review confirmed no product change is NEEDED: the role reaches the
  gated subprocess through `pinned_child_env` copying `os.environ` (`oc_runipd.py:605`), so a test-side
  declaration suffices and no new product parameter is required.)
- Under-scope: deliberate, and now THREE items rather than one. (1) The suite being green in a lane does NOT
  stop a determined `env -u` bypass; that is `c4yixg`. (2) `tests/test_worker_role_refusal.py`'s one failure
  is left red because `8b9ufm` owns it, so this plan delivers 30 of the 31. (3) The `ld8lb3` ordering edge is
  not declared. Each is named in Deferred rather than implied.

## Required tests / validation

- BOTH conditions from the same HEAD, with both summary lines pasted:
  `python3 -m pytest` and `AW_EXECUTION_ROLE=worker python3 -m pytest`.
  Authoring baseline: `7869 passed` clean, `31 failed, 7866 passed` in a lane (at `edb9ba85`).
  Review baseline: `7993 passed` clean, `31 failed, 7962 passed` in a lane (at `95b08fca`).
  EXPECTED RESULT AFTER THIS PLAN: clean fully green; lane condition green EXCEPT exactly 1 declared
  out-of-scope failure (`test_driver_own_process_is_not_worker_role`, owned by `8b9ufm`). Naming that
  residual is required; hiding it with `-k`/skip is forbidden.
- Evidence that no refusal test was made vacuous: for whatever E-05 finds, show the assertion still present,
  and show the three out-of-scope refusal-test files (`test_ipd_lint.py`, `test_orchestrator_retirement.py`,
  `test_turn_bounds.py`) still green in BOTH conditions. Review baseline for those: 78, 137, 40 passed.
- The E-07 guard demonstrated failing against a deliberately added ambient-inheriting test, AND shown not to
  be satisfiable by a comment (the failure mode `runner_shared.py:9467-9470` records).
- A REAL lane check, which is the actual acceptance criterion: run one plan through `aw oc run` and show the
  agent's own bare `python3 -m pytest` inside the lane. That is the outcome this plan exists for, and no
  local simulation substitutes for it. If no plan is available to run, say so explicitly rather than
  dropping the check.

## Spec / documentation sync

N/A for `.spec.md`: no specification governs test environment isolation, and no product behavior changes. No
`.spec.md` is declared in `Scope-Paths`. If E-02 finds a test whose assertion encodes a SPEC requirement
about roles, name it rather than editing the spec here.

ONE DOCUMENTATION OBLIGATION, added at review: E-03's helper docstring is the durable statement of the
convention this plan establishes ("a test must DECLARE the role it exercises; inheriting the ambient role is
a defect in either direction"). It must cite the two shipped precedents so the next author extends the
pattern instead of inventing a third, and it is the artifact E-07's guard points at when it fails.

## Open questions

### OQ-01: Should the runner stop exporting the marker during a test run instead of fixing 31 tests?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. It looks like the cheaper fix and it is the wrong one, for two
  reasons. FIRST, the runner cannot tell a pytest subprocess from any other child the agent spawns, so
  "unset it for tests" means either unsetting it for everything the agent runs (which removes the guard
  outright) or teaching the runner to recognize test commands (an unbounded and forgeable heuristic).
  SECOND, it would hide the real defect: a test that INHERITS its role is untrustworthy in either
  direction, and F-3 is the proof - the guard's own test currently asserts something about the ambient
  environment rather than about the code, so it passes for the wrong reason in the main tree. Making the
  tests declare their role fixes both the symptom and the latent unreliability.

### OQ-02: `770fkp` says 31 and `s0303g` says 19. Which is right?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NEITHER is authoritative, and E-01 re-measures instead of choosing.
  Both were taken at earlier HEADs (`770fkp` at `4a1bb873` reporting `31 failed, 7645 passed`), and the
  count moves with the suite. Measured 2026-09-18 at `edb9ba85` the figure is 31 failures / 7866 passed,
  which happens to match `770fkp`'s count against a different total. The plan therefore treats both items
  as ONE defect at two sample points and graduates them together; E-01's re-measurement is the number the
  executor works from. CONFIRMED AT REVIEW at a third HEAD (`95b08fca`): still exactly 31 failures, same
  six-file split, pass total moved to 7962. So 31 is the stable figure across three HEADs and 19 was a
  genuinely earlier state; the FAILURE count is the invariant to compare, not the pass total.

### OQ-03: Why not just pop the variable once in the root `conftest.py`? It makes all 7993 pass.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ADDED AT REVIEW (PR-103), because this alternative WORKS and is
  therefore the likeliest wrong turn for anyone who later wants to "simplify" this plan. It is distinct from
  OQ-01, which rejects the RUNNER unsetting the marker; this is the TEST HARNESS unsetting it, one line, at
  one call site. Measured at review: with `os.environ.pop("AW_EXECUTION_ROLE", None)` executed before
  collection, the full suite reports `7993 passed, 3 skipped, 2 xfailed` and every one of the 31 is fixed,
  xdist workers included (they inherit the parent environment).
  REJECTED ANYWAY, for one decisive reason plus one supporting one. THE DECISIVE REASON: the same one-liner
  also turns `tests/test_worker_role_refusal.py` into `7 passed`, because
  `test_driver_own_process_is_not_worker_role` asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` and
  a global pop makes that assertion merely confirm the pop. That is the guard's OWN test made vacuous, i.e.
  precisely the failure mode E-05's validation exists to prevent, and it would be invisible: the suite goes
  green and nothing announces that a safety test stopped testing anything. THE SUPPORTING REASON: a global
  pop hides the underlying defect rather than fixing it. A test that inherits its role is untrustworthy in
  BOTH directions, so it would still pass for the wrong reason in the main tree, and the next
  ambient-dependent test added would be masked at birth.
  A one-line fix that makes a security guard's test assert nothing is not a cheaper version of this plan; it
  is the opposite of it. Prohibited in the gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: both summary lines pasted from execution HEAD (lane condition and clean), plus the
    per-file failure counts, compared explicitly against BOTH recorded baselines (`edb9ba85`: 31 failures /
    `7866 passed` / `7869 passed` clean; `95b08fca`: 31 failures / `7962 passed` / `7993 passed` clean).
    Judge divergence on the LOAD-BEARING facts (the failure count of 31 and the six-file split), and note a
    moved pass total as expected suite growth rather than treating it as a reason to stop.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the classification table, all 31 assigned to coordinator / worker / role-agnostic,
    each justified by what the test ASSERTS. `test_driver_own_process_is_not_worker_role` must appear with
    its class, a note that it asserts against ambient state, AND a note that it is OUT OF SCOPE for this
    plan because `8b9ufm` owns it. If the table finds any class (b) member among the 31, say so explicitly,
    since review measured the expectation that there is none.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the helper's source and docstring from `tests/support.py`, plus evidence it is the
    ONLY mechanism used (no test-local `os.environ` juggling left in the five in-scope files). The docstring
    must cite the two shipped precedents. Show the helper being used FROM a `unittest.TestCase` and passing,
    which is the property that rules out the pytest-fixture mechanism the plan originally named.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the coordinator-class tests passing in BOTH ambient conditions, pasted for each
    condition, across the five in-scope files. Passing in only one condition fails this item. Confirm
    `tests/test_worker_role_refusal.py` was NOT modified (`git diff --name-only` must not list it).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: EITHER a named class (b) member that sets the role explicitly, shown still asserting
    `AW-LIFECYCLE-ROLE-001` (show the assertion, not just the green), OR the explicit recorded finding that
    no class (b) member exists among the 31. In BOTH cases, paste the three out-of-scope refusal-test files
    green under both ambient conditions (`test_ipd_lint.py`, `test_orchestrator_retirement.py`,
    `test_turn_bounds.py`; review baseline 78 / 137 / 40 passed) and confirm none of them was edited. Silence
    does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest` and `AW_EXECUTION_ROLE=worker python3 -m pytest`, both summary
    lines pasted from the same HEAD. Clean must be FULLY green. The lane condition must be green except
    exactly ONE failure, `test_driver_own_process_is_not_worker_role`, which must be NAMED with the
    ownership reason. Evidence that it was not deselected, skipped, or `-k`-filtered to fake green.
    PLUS the real-lane check: one plan run through `aw oc run` whose agent reports its own bare-suite result
    from inside its lane; if no plan is available to run, state that explicitly and give the two-condition
    evidence as the substitute rather than dropping it.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the guard green, AND its failure output when a deliberately ambient-inheriting test
    is added (add, paste, revert). PLUS proof the guard is BEHAVIORAL: show that it is not satisfied by a
    source-text match alone (the comment-satisfiable failure recorded at `runner_shared.py:9467-9470`), for
    example by adding a test that MENTIONS the env var in a comment while still inheriting, and showing the
    guard still fails it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-leaves in three groups, strictly sequential: inventory, then fix,
  then prove).

This plan requires explicit human approval before execution. One constraint is absolute: `AW-LIFECYCLE-ROLE-001`
must not be weakened. Every change makes a test DECLARE the role it intends; a diff that removes a role check,
or that makes a refusal test pass by no longer asserting the refusal, is out of scope even if the suite goes
green. E-05's V-item exists to catch exactly that.

Execution contract for whoever executes this plan:

1. DO NOT TOUCH `tests/test_worker_role_refusal.py`. APPROVED plan `8b9ufm` declares that file and says
   plainly "Do not 'fix' it" about its one ambient-asserting failure (`8b9ufm:99`, its F-18). This plan
   therefore delivers 30 of the 31 and leaves that one red BY DESIGN. See the ownership section. If you
   believe it must be fixed to finish, STOP and report rather than editing another plan's declared file.
2. DO NOT POP THE VARIABLE GLOBALLY, in the root `conftest.py` or anywhere else process-wide. It WORKS
   (review measured `7993 passed` from one line) and it is the wrong fix, because it also makes the role
   guard's own test assert nothing. OQ-03 records the measurement and the refutation. A green suite bought
   by silencing a safety test is the failure mode this plan exists to prevent.
3. DO NOT USE `env -u AW_EXECUTION_ROLE` ON ANY LIFECYCLE VERB. Using it to get a pytest baseline is
   legitimate and is what E-01 asks for; carrying the habit into `aw ipd begin`/`finalize` is the bypass
   filed as `c4yixg` that stranded a completed lane and cost a human a hand merge (`2cfdb85d`).
4. NOTE THE BOOTSTRAP: this plan's own executor will be running inside a lane, i.e. inside the very
   red-baseline condition it fixes. That is expected and is not a reason to strip the marker. Report the red
   baseline at the start (E-01 requires it), then make it green.
5. E-03's MECHANISM IS CONSTRAINED BY THE TEST STYLE. Every affected test is a `unittest.TestCase`, so a
   pytest fixture (`monkeypatch`) will NOT be injected and will silently do nothing; review proved this.
   Use a `setUp` context manager, `unittest.mock.patch.dict(os.environ, ...)`, or an explicit `env=`
   argument, and reuse the two shipped precedents named in E-03.
6. HARD MUST honesty rule: paste ACTUAL runner output for every V-item. Run the suite BARE
   (`python3 -m pytest`); the configured `addopts` already make it quiet, parallel and fast-scoped. Do not
   add `-n0` (several times slower) or a second `-q` (suppresses the summary line you must paste). Use
   `-o addopts=""` only where a narrowed per-test count is genuinely needed.
7. SCOPE FENCE (a declaration, not a stop order). The declared paths are those in `Scope-Paths`: the five
   in-scope test files plus `tests/support.py`. Editing outside the list is permitted where the work
   genuinely requires it, but each out-of-scope edit MUST be justified at finalize (`--scope-reason`) and
   each declared path left unmodified MUST be acknowledged (`--scope-ack`). Deliberate exclusions:
   `tests/test_worker_role_refusal.py` (clause 1), the root `conftest.py` (clause 2), every prompt builder
   (`8b9ufm`), all product code, and `ld8lb3`'s front matter.
8. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <path>`). Never
   `git add -A`, bare `git add`, or `-a`. Never push. Verify `git diff --cached --name-only` before every
   commit and re-verify after any failed hook.
9. On completion, run `aw ipd lint --phase pre-transition` and confirm it reports conforming with every
   `V-*` carrying observed evidence. The plan then reaches `executed` ONLY through the gated finalize
   transaction, which performs the attributed history entry, the terminal `Status:`, the move and the
   path-scoped lifecycle commit as one transaction. WHO RUNS IT DEPENDS ON HOW YOU ARE EXECUTING:

     - IN A MANAGED LANE (the runner set `AW_EXECUTION_ROLE=worker`): the transition is the RUNNER'S. Do NOT
       run the command. Report your result in the outcome file the prompt names and stop.
     - OTHERWISE (executing by hand, or a run under `--no-self-finalize`): run it yourself:

           aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply

     If you are unsure which case applies, just attempt it: an `AW-LIFECYCLE-ROLE-001` refusal is the
     EXPECTED, SUCCESSFUL handoff, not a failure. In no case may you `git mv` this file or hand-edit
     `- Status:`, and in no case may you `env -u` your way past the refusal (clause 3).

Note for the approver: this is the best-evidenced plan I have reviewed in this sweep. I re-measured every
number from scratch while running inside the worker-role condition itself, and all of them reproduced
exactly (31 failures, the 10/9/8/2/1/1 six-file split, F-3's assertion message verbatim, both cited commits);
I found no false claim. Review changed three things worth knowing before you approve. FIRST, a collision:
APPROVED plan `8b9ufm` declares `tests/test_worker_role_refusal.py` and explicitly forbids fixing the very
test this plan called its "sharpest case", so the scope is narrowed to 30 of 31 and the last failure is now
declared expected-red. If you would rather this plan fix it and `8b9ufm` yield, that is your call to make.
SECOND, I measured that ONE line in the root `conftest.py` makes all 7993 pass, and refuted it: it also makes
the role guard's own test assert nothing, so it is recorded as OQ-03 and forbidden in the gate, because
otherwise someone will eventually find it and think they are helping. THIRD, E-03's prescribed mechanism
could not have worked (pytest fixtures are not injected into `unittest.TestCase`, proven), so it now names
mechanisms that do, and points at two places in the repo that already solved this exact problem.

NOTE THE BOOTSTRAP: this plan's own executor will be running inside a lane, i.e. inside the very red-baseline
condition it fixes. That is expected and is not a reason to strip the marker. Report the red baseline at the
start (E-01 requires it), then make it green. Do NOT use `env -u AW_EXECUTION_ROLE` on any lifecycle verb;
that is the bypass filed as `c4yixg` and this plan exists to remove the reason for it.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence.

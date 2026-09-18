# IPD: Make the suite green inside a lane by controlling the execution-role env instead of inheriting it

- Date: 2026-09-17
- Kind: child
- Concern: A bare `python3 -m pytest` inside a driver lane reports 31 failures at a HEAD whose suite is otherwise green, so NO plan executed in a lane can produce the green baseline its own validation contract demands. Re-measured 2026-09-18 at `edb9ba85`: `AW_EXECUTION_ROLE=worker python3 -m pytest` gives `31 failed, 7866 passed, 3 skipped, 2 xfailed` against `7869 passed` clean. The runner exports `AW_EXECUTION_ROLE=worker` into every isolated lane (`oc_runipd.py:5876`), `ipd_lifecycle.py:69` correctly refuses begin/finalize for a worker-role process with `AW-LIFECYCLE-ROLE-001`, and 31 tests invoke those verbs while INHERITING the ambient role rather than controlling it. The refusal is correct and must not be weakened; the tests are what is wrong.
- Scope: Make the 31 tests control `AW_EXECUTION_ROLE` explicitly rather than inherit it, so the suite is green in a lane AND in the main tree, and each test exercises the role it intends. Does NOT relax `AW-LIFECYCLE-ROLE-001` in any way: a test that needs the coordinator role must SET that role, not remove the guard. Also does not touch the prompt-side role statement, which approved plan `8b9ufm` owns.
- Scope-Paths: tests/test_runner_backlog_close_in_lane.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_ipd_lifecycle_cli.py, tests/test_worker_role_refusal.py, tests/test_novalnomerge_integration.py, tests/support
- Item-Dependencies: none
- Status: to-review
- From-Backlog: 770fkp
- Set: lanesuite
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: e4lkv5

## Workflow history
- 2026-09-18 to-review (aw set): Authored 2026-09-18 from a re-measurement at edb9ba85 (31 failures across six files under the lane condition); graduates 770fkp and s0303g; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Backlog provenance

This plan graduates TWO backlog items, and `- From-Backlog:` can name only one:

- `770fkp` (high) 31 tests fail in a lane because the role marker refuses begin/finalize. In front matter.
- `s0303g` (medium) the same defect measured at 19 failures, framed as "a worker cannot get a trustworthy
  bare-suite baseline". Named here because the field cannot hold it. Its Set id `lanesuite` is the Set this
  plan uses, so the grouping is already aligned.

They are ONE defect at two sample points (see OQ-02); E-01 re-measures rather than trusting either count.
Neither carries `Blocks-Release`, so no release gate is inherited.

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
  - Expected outcome: the per-test list. Baseline measured 2026-09-18 at `edb9ba85`: 31 failures across SIX files, not the four the backlog item names - `test_runner_backlog_close_in_lane.py` 10, `test_oc_runipd.py` 9, `test_agy_runipd_cli.py` 8, `test_ipd_lifecycle_cli.py` 2, `test_worker_role_refusal.py` 1, `test_novalnomerge_integration.py` 1. Any divergence from that is stated, not absorbed.
  - Execution state: pending

- [ ] E-02 Classify each failing test by WHAT ROLE IT ACTUALLY MEANS TO EXERCISE: (a) coordinator (it calls begin/finalize as the driver would, so it must run with the marker ABSENT or set to coordinator); (b) worker (it asserts the refusal, so it must SET the marker itself rather than rely on ambient); (c) role-agnostic (it merely happens to invoke a gated verb incidentally). The fix differs per class, so a single blanket env-clear would be wrong for class (b).
  - Depends on: E-01
  - Expected outcome: every one of the 31 assigned to a class, with the class justified from what the test asserts. Note `test_worker_role_refusal.py::test_driver_own_process_is_not_worker_role` is class (a) and is the sharpest case: it asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` about the AMBIENT environment, so in a lane the guard's own test fails on the very condition the guard exists to create.
  - Execution state: pending

### Task group 2: Make each test state the role it means

- [ ] E-03 Add ONE shared test helper under `tests/support` that sets or clears the role explicitly (e.g. a context manager / fixture taking the intended role), so 31 call sites do not each hand-roll `monkeypatch.delenv`. A single helper is what makes the intent auditable and stops the next author inheriting ambient state again.
  - Depends on: E-02
  - Expected outcome: one helper with a docstring stating that a test must DECLARE its role, and why inheriting is a defect. No test-local reimplementation.
  - Execution state: pending

- [ ] E-04 Apply the helper to the class (a) coordinator tests so they run with the role absent/coordinator regardless of the ambient environment. This is the bulk of the 31.
  - Depends on: E-03
  - Expected outcome: every class (a) test passes with AND without `AW_EXECUTION_ROLE=worker` in the ambient environment.
  - Execution state: pending

- [ ] E-05 Apply the helper to the class (b) refusal tests so they SET the worker role explicitly instead of depending on the ambient value. A refusal test that passes only because the runner happened to export the marker is not testing the guard, it is testing its environment.
  - Depends on: E-03
  - Expected outcome: every class (b) test passes in both ambient conditions and provably still asserts the `AW-LIFECYCLE-ROLE-001` refusal.
  - Execution state: pending

### Task group 3: Prove it and keep it

- [ ] E-06 Demonstrate the suite is green in BOTH ambient conditions, which is the whole point of the plan: `python3 -m pytest` clean, and `AW_EXECUTION_ROLE=worker python3 -m pytest`, both green with summary lines pasted. A fix that makes the lane green while breaking the main tree has moved the defect rather than fixed it.
  - Depends on: E-04, E-05
  - Expected outcome: two green summary lines from the same HEAD.
  - Execution state: pending

- [ ] E-07 Add a guard that FAILS if a test invoking a role-gated lifecycle verb reads the ambient role instead of declaring one, so this class of defect cannot silently return. Keep it narrow and honest about what it can detect; a guard that only re-runs the suite in one condition proves nothing.
  - Depends on: E-06
  - Expected outcome: a guard that catches a newly added ambient-inheriting test, demonstrated by adding one, pasting the failure, and reverting.
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
| F-1 | 31 tests fail under the lane condition at a HEAD whose suite is otherwise green | measured 2026-09-18 at `edb9ba85`: `AW_EXECUTION_ROLE=worker python3 -m pytest` -> `31 failed, 7866 passed, 3 skipped, 2 xfailed`; clean -> `7869 passed` |
| F-2 | THE BACKLOG ITEM'S FILE LIST IS INCOMPLETE: six files, not four | per-file counts: `test_runner_backlog_close_in_lane.py` 10, `test_oc_runipd.py` 9, `test_agy_runipd_cli.py` 8, `test_ipd_lifecycle_cli.py` 2, `test_worker_role_refusal.py` 1, `test_novalnomerge_integration.py` 1. The item names the first four |
| F-3 | The GUARD'S OWN TEST FILE is among the failures, and it fails by reading ambient state | `test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"`; under the lane condition: `AssertionError: 'worker' == 'worker'` |
| F-4 | The cause is test isolation, not product behavior: the same file is green clean and red in a lane | `tests/test_ipd_lifecycle_cli.py`: `89 passed` clean vs `2 failed, 87 passed` with the marker set |
| F-5 | The refusal itself works exactly as designed | verified live: `AW_EXECUTION_ROLE=worker aw ipd finalize <plan> --actor test --message probe` returns the `AW-LIFECYCLE-ROLE-001` refusal |
| F-6 | THE RED BASELINE ALREADY CAUSED A REAL BYPASS, which is why this is high and not cosmetic | `63425h` used `env -u AW_EXECUTION_ROLE` 139 times in one session for legitimate pytest baselines, then applied it to `ipd finalize --apply`, defeating the guard and consuming the driver's receipt. Filed `c4yixg`; the stranded lane needed a hand merge (`2cfdb85d`) |
| F-7 | A blanket env-clear would be the WRONG fix for part of the set | some failing tests are refusal tests whose purpose is to assert the worker-role refusal; clearing the marker globally would make them vacuous instead of correct. Hence E-02's classification |
| F-8 | This plan gates other work: a lane cannot honestly validate a plan whose own tests are in the failing set | `ld8lb3` declares `tests/test_ipd_lifecycle_cli.py`, two of whose tests are in F-1's set, and its validation demands a bare green suite |

## Proposed changes (ordered, validatable)

1. Re-measure the 31 failures per test at execution HEAD, in both ambient conditions (E-01).
2. Classify each by the role it MEANS to exercise: coordinator / worker / role-agnostic (E-02).
3. Add one shared `tests/support` helper that declares a role explicitly (E-03).
4. Apply it to the coordinator tests (E-04) and to the refusal tests (E-05), which need opposite treatment.
5. Prove the suite is green in BOTH ambient conditions (E-06).
6. Guard against a new ambient-inheriting test (E-07).

## Deferred / out of scope (with reason)

- ENFORCEMENT of the role guard against a deliberate `env -u` bypass is `c4yixg`, not this plan. This plan
  removes the INCENTIVE; that one closes the HOLE. Both are needed and they are separable: this one is
  cheap, unblocks other plans, and touches only tests.
- The prompt-side role statement belongs to APPROVED plan `8b9ufm` (`roleadv-01`). Do not edit a prompt
  builder here.
- The `finalize()` / `status_set` hole (the `aw set executed` route that needs no `env -u` at all) is owned
  by `ld8lb3` E-06 as rewritten at its review. Not here.
- `s0303g` reports 19 failures against this item's 31. Both were measured at earlier HEADs and the current
  figure is 31; E-01 re-measures rather than trusting either. `s0303g` is the same defect at a different
  count and is graduated by this plan alongside `770fkp`.

## Scope check

- Over-scope: none. Every item is test-only except the shared helper, which is also test-only. No product
  code and no guard predicate changes.
- Under-scope: deliberate. The suite being green in a lane does NOT stop a determined `env -u` bypass; that
  is `c4yixg`. Claiming this plan closes the bypass would overstate it.

## Required tests / validation

- BOTH conditions green from the same HEAD, with both summary lines pasted:
  `python3 -m pytest` and `AW_EXECUTION_ROLE=worker python3 -m pytest`.
  Authoring baseline: `7869 passed` clean, `31 failed, 7866 passed` in a lane.
- Per-class evidence that a refusal test still asserts the `AW-LIFECYCLE-ROLE-001` refusal after the change
  (not merely that it passes), so E-05 cannot be satisfied by making those tests vacuous.
- The E-07 guard demonstrated failing against a deliberately added ambient-inheriting test.
- A REAL lane check, which is the actual acceptance criterion: run one plan through `aw oc run` and show the
  agent's own bare `python3 -m pytest` inside the lane is green. That is the outcome this plan exists for,
  and no local simulation substitutes for it.

## Spec / documentation sync

N/A: no `.spec.md` governs test environment isolation, and no product behavior changes. No `.spec.md` is
declared in `Scope-Paths`. If E-02 finds a test whose assertion encodes a SPEC requirement about roles, name
it rather than editing the spec here.

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
  executor works from.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: both summary lines pasted from execution HEAD (lane condition and clean), plus the
    per-file failure counts, compared explicitly against the 2026-09-18 baseline (31 failures across six
    files; `7869 passed` clean). State any divergence rather than absorbing it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the classification table, all 31 assigned to coordinator / worker / role-agnostic,
    each justified by what the test ASSERTS. `test_driver_own_process_is_not_worker_role` must appear with
    its class and a note that it currently asserts against ambient state.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the helper's source and docstring, plus evidence it is the ONLY mechanism used (no
    test-local `delenv`/`os.environ` juggling left in the six files).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the coordinator-class tests passing in BOTH ambient conditions, pasted for each
    condition. Passing in only one condition fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the refusal-class tests passing in both conditions AND still asserting the
    `AW-LIFECYCLE-ROLE-001` refusal. Show the assertion, not just the green: the failure mode to exclude is
    a refusal test made vacuous.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest` and `AW_EXECUTION_ROLE=worker python3 -m pytest`, both green,
    both summary lines pasted, from the same HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the guard green, AND its failure output when a deliberately ambient-inheriting test
    is added (add, paste, revert). PLUS the real-lane check: one plan run through `aw oc run` whose agent
    reports a green bare suite from inside its lane. That last item is the plan's actual purpose and cannot
    be substituted by a local simulation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. One constraint is absolute: `AW-LIFECYCLE-ROLE-001`
must not be weakened. Every change makes a test DECLARE the role it intends; a diff that removes a role check,
or that makes a refusal test pass by no longer asserting the refusal, is out of scope even if the suite goes
green. E-05's V-item exists to catch exactly that.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped, never
`git add -A`, never push. Paste ACTUAL runner output for every V-item.

NOTE THE BOOTSTRAP: this plan's own executor will be running inside a lane, i.e. inside the very red-baseline
condition it fixes. That is expected and is not a reason to strip the marker. Report the red baseline at the
start (E-01 requires it), then make it green. Do NOT use `env -u AW_EXECUTION_ROLE` on any lifecycle verb;
that is the bypass filed as `c4yixg` and this plan exists to remove the reason for it.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence.

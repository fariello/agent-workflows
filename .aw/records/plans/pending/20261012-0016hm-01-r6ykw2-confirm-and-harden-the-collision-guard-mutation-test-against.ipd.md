# IPD: Confirm and harden the collision-guard mutation test against preflight refusals

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation` failed in the bare suite with `KeyError: 'verification_status'` (backlog `0016hm`, filed during `tha7a6`), because the `_drive_execute_turn` helper let `runner_shared.execute_item_core` take the host-capability preflight early return, which never writes `verification_status`.
- Scope: Confirm the defect is fixed at HEAD by the frozen `host_capabilities` descriptor that `psgyzw` (commit `163874fcc`) added to the helper, and harden the helper so any future pre-verify early return fails with a named diagnostic instead of a bare KeyError. Test-only change.
- Scope-Paths: tests/test_runwire_verifier_authority.py, .aw/records/plans/pending/20261012-0016hm-01-r6ykw2-confirm-and-harden-the-collision-guard-mutation-test-against.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 0016hm
- Blocks-Release: next
- Set: 0016hm
- Order: 1
- Highest E allocated: 03
- Author: opencode Claude Opus
- Id: r6ykw2

## Workflow history

- 2026-10-12 draft (opencode Claude Opus): created.
- 2026-10-12 to-review (opencode Claude Opus): authored review-ready from backlog 0016hm with root cause reproduced at the filing commit.

## Goal

Close backlog `0016hm` with evidence: show the KeyError no longer reproduces at HEAD, and make the shared test helper fail loudly and specifically if `execute_item_core` ever returns before the verify stage again. That way the same class of regression cannot come back as an opaque KeyError.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the fix at HEAD

- [ ] E-01 Run `tests/test_runwire_verifier_authority.py` at HEAD, both alone and as part of the bare suite, and record that `test_collision_guard_bites_by_mutation` passes.
  - Depends on: none
  - Expected outcome: `12 passed` for the file (or the current count), and the bare suite reports no failure for this test.
  - Execution state: pending

### Task group 2: Harden the helper

- [ ] E-02 In `tests/test_runwire_verifier_authority.py` `_drive_execute_turn`, after `runner_shared.execute_item_core(...)` returns, assert that the item reached the verify stage. Specifically, assert `"verification_status" in item`, with a failure message that quotes `item.get("status")`, `item.get("refusals")` (or the latest attempt's `host_capability_unavailable` / `clean_base_refused` / `begin_refused` / `scope_target_refused` / `worktree_error` keys, whichever are present), so an early return is named rather than surfacing later as `KeyError`. This asserts observable output of the real pipeline; it does not read source.
  - Depends on: E-01
  - Expected outcome: Every existing test in the file still passes. A deliberately induced preflight refusal (removing the `host_capabilities` key from the helper's state, temporarily and locally, with no commit) makes the helper fail with an AssertionError naming the refusal instead of a KeyError.
  - Execution state: pending

- [ ] E-03 Commit only the test file and this plan via `aw commit r6ykw2 -- tests/test_runwire_verifier_authority.py <this plan path>`.
  - Depends on: E-02
  - Expected outcome: One commit whose `git show --stat` lists only those two paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite command: bare `python3 -m pytest` (AGENTS.md repo-local contract); narrowed runs use `-o addopts=""`.
- Tests must assert observable behavior and never read production source (AGENTS.md execution contract, GUIDING_PRINCIPLES P16). E-02 asserts on the item dict the real `runner_shared.execute_item_core` writes.
- `runner_shared.ensure_frozen_host_capabilities` reads `state["host_capabilities"]["descriptor"]` and, when it is absent, probes the live host via `host_sandbox_profile.detect_host_capabilities`. The result depends on the environment.
- `runner_shared.execute_item_core` writes `item["verification_status"] = verify_disp` only after `_run_verifier_turn`. Its earlier returns (host-capability preflight "host capability refused", scope-target refusal, clean-base refusal, begin refusal, worktree allocation failure, stall) set `item["status"]` and return without writing it.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The failure reproduces at the filing commit `bbf408eed` (integrate tha7a6). | Ran the file from a `git archive bbf408eed` copy: `FAILED ...::test_collision_guard_bites_by_mutation`, `KeyError: 'verification_status'`, `1 failed, 11 passed`. Captured stderr: `✗ IPD tst001 host capability refused: [RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session required by tst001 action execute.` |
| F-2 | Root cause: the helper built `state` without `host_capabilities`, so the preflight probed the live host and refused the second (mutated) drive. `execute_item_core` returned at the preflight before writing `verification_status`. | Stderr in F-1; the `if not preflight.ok:` branch in `runner_shared.execute_item_core` returns without setting `verification_status`. |
| F-3 | Already fixed at HEAD: commit `163874fcc` (psgyzw) added `"host_capabilities": {"descriptor": {"supports_fresh_verifier_session": True, "supports_session_resume": True}}` to the helper's state. | `git diff bbf408eed HEAD -- tests/test_runwire_verifier_authority.py` shows only that hunk. At HEAD the file runs `12 passed` three times with random order, and again under the bare configured addopts. |
| F-4 | Residual risk: any new pre-verify early return in `execute_item_core` would bring back the same opaque KeyError in every test that uses this helper. | The early returns listed in Step 0. |

## Proposed changes (ordered, validatable)

1. E-01: re-measure at HEAD and paste the runner output.
2. E-02: add a post-call reached-verify assertion with a diagnostic message to `_drive_execute_turn`.
3. E-03: path-scoped commit.

## Deferred / out of scope (with reason)

- Changing `runner_shared.execute_item_core` to always write `verification_status` on early returns: out of scope. The early-return item shape is a runner contract consumed by `run_viewer` and others, and the defect lives in the test fixture, not the runner.
- Explaining why the live probe passed on the first drive and refused on the second: not needed. The fixture no longer probes, and E-02 surfaces any recurrence.

## Scope check

- Over-scope: none.
- Under-scope: none. The fix is confirmed (E-01) and the regression class is guarded (E-02).

## Required tests / validation

- `python3 -m pytest tests/test_runwire_verifier_authority.py -o addopts="" -q` passes (V-01, V-02).
- The bare `python3 -m pytest` reports no failure for `test_collision_guard_bites_by_mutation` (V-01).
- A temporary, uncommitted removal of `host_capabilities` from the helper produces an AssertionError naming the refusal, not a KeyError (V-02).
- The commit touches only the declared paths (V-03).

## Spec / documentation sync

N/A: this is a test-fixture change with no behavior, CLI, or spec contract change. CHANGELOG is not updated because nothing user-facing changes.

## Open questions

### OQ-01: Should the runner itself write `verification_status` on early returns?

- Blocking: no
- Status: deferred
- Owner: maintainer (trigger: a runner consumer needing the key on early returns)
- Resolution or deferral rationale: Deferred (see Deferred section). The defect was fixture-side, and the runner's early-return item shape is an existing contract. File a separate backlog item if a consumer is found that needs the key.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual pytest summary for the file run at HEAD (`N passed`), plus the bare-suite summary line showing no failure for `test_collision_guard_bites_by_mutation`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` of `_drive_execute_turn`; paste the pytest summary for the file with the change (all passing); paste the AssertionError output from the temporary, uncommitted removal of `host_capabilities`, showing the refusal text and no `KeyError`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git show --stat HEAD` showing only `tests/test_runwire_verifier_authority.py` and this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Follow the agent execution contract: commit through `aw commit r6ykw2 -- <paths>`, never push, and paste real runner output. Once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, finalize to `.aw/records/plans/executed/` through the tooled lifecycle.

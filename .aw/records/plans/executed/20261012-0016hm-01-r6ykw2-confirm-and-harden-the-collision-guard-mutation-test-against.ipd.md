# IPD: Confirm and harden the collision-guard mutation test against preflight refusals

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation` failed in the bare suite with `KeyError: 'verification_status'` (backlog `0016hm`, filed during `tha7a6`), because the `_drive_execute_turn` helper let `runner_shared.execute_item_core` take the host-capability preflight early return, which never writes `verification_status`.
- Scope: Confirm the defect is fixed at HEAD by the frozen `host_capabilities` descriptor that `psgyzw` (commit `163874fcc`) added to the helper, and harden the helper so any future pre-verify early return fails with a named diagnostic instead of a bare KeyError. Test-only change.
- Scope-Paths: tests/test_runwire_verifier_authority.py, .aw/records/plans/pending/20261012-0016hm-01-r6ykw2-confirm-and-harden-the-collision-guard-mutation-test-against.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: r6ykw2 verified (set 0016hm, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (negative control made deterministic; refusal key corrected to singular `refusal`; guard raises explicitly; execution contract completed)
- 2026-10-12 reviewed (aw set): plan-review revisions applied (PR-001..PR-004)
- 2026-10-12 draft (opencode Claude Opus): created.
- 2026-10-12 to-review (opencode Claude Opus): authored review-ready from backlog 0016hm with root cause reproduced at the filing commit.

## Goal

Close backlog `0016hm` with evidence: show the KeyError no longer reproduces at HEAD, and make the shared test helper fail loudly and specifically if `execute_item_core` ever returns before the verify stage again. That way the same class of regression cannot come back as an opaque KeyError.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the fix at HEAD

- [x] E-01 Run `tests/test_runwire_verifier_authority.py` at HEAD, both alone and as part of the bare suite, and record that `test_collision_guard_bites_by_mutation` passes.
  - Depends on: none
  - Expected outcome: every test in the file passes (re-measured at review at HEAD `6bac33183`: `12 passed`; the count is context, not the bar), and the bare suite's `FAILED` list does not name `test_collision_guard_bites_by_mutation`.
  - Execution state: performed

### Task group 2: Harden the helper

- [x] E-02 In `tests/test_runwire_verifier_authority.py` `_drive_execute_turn`, after `runner_shared.execute_item_core(...)` returns, assert that the item reached the verify stage: if `"verification_status" not in item`, raise `AssertionError` whose message starts `execute_item_core returned before the verify stage:` and quotes ALL of `item.get("status")`, `item.get("refusal")` (SINGULAR: `runner_shared.record_refusal` writes `item["refusal"] = {"code", "reason", "remedy"}`; there is no `refusals` key, measured at review), `item.get("worktree_error")` (an ITEM key, not an attempt key), and whichever of `host_capability_unavailable` / `scope_target_refused` / `clean_base_refused` / `begin_refused` are present on the latest attempt. Use an explicit `if ...: raise AssertionError(...)` rather than a bare `assert`, so the guard survives `python -O`. This asserts observable output of the real pipeline; it does not read source. All ten callers in the file then inherit the guard.
  - Depends on: E-01
  - Expected outcome: Every existing test in the file still passes. A deliberately induced preflight refusal makes the helper fail with the named AssertionError instead of a KeyError. INDUCE IT by temporarily setting the helper's `"supports_fresh_verifier_session": True` to `False` (uncommitted, reverted after; verify with `git diff --stat`), NOT by removing the `host_capabilities` key: measured at review, removing the key falls through to the live host probe, which on this machine did NOT refuse (two drives both reached verify), so that control is environment-dependent and can prove nothing. The `False` descriptor refused deterministically on both hosts at review: `7 failed, 5 passed`, each failure `AssertionError: execute_item_core returned before the verify stage: status='fail-gate' refusal={'code': 'host_capability_unavailable', ...}`, zero `KeyError`.
  - Execution state: performed

- [x] E-03 Commit only the test file and this plan via `aw commit r6ykw2 -- tests/test_runwire_verifier_authority.py <this plan path>`.
  - Depends on: E-02
  - Expected outcome: One commit whose `git show --stat` lists only those two paths.
  - Execution state: performed

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
| F-5 | The E-02 guard and its negative control were demonstrated at review on scratch copies (deleted afterwards; no tracked file changed). | Guarded copy: `12 passed`. Guarded copy with the descriptor capability set `False`: `7 failed, 5 passed`, all seven `AssertionError: execute_item_core returned before the verify stage: status='fail-gate' refusal={'code': 'host_capability_unavailable', ...} worktree_error=None early={'host_capability_unavailable': ...}` on opencode and antigravity; no `KeyError`. Removing `host_capabilities` instead reached verify on both of two drives (live probe passed here). |

## Proposed changes (ordered, validatable)

1. E-01: re-measure at HEAD and paste the runner output.
2. E-02: add a post-call reached-verify assertion with a diagnostic message to `_drive_execute_turn`.
3. E-03: path-scoped commit.

## Deferred / out of scope (with reason)

- Changing `runner_shared.execute_item_core` to always write `verification_status` on early returns: out of scope. The early-return item shape is a runner contract consumed by `run_viewer` and others, and the defect lives in the test fixture, not the runner.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Explaining why the live probe passed on the first drive and refused on the second: not needed. The fixture no longer probes, and E-02 surfaces any recurrence.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none. The fix is confirmed (E-01) and the regression class is guarded (E-02).

## Required tests / validation

- `python3 -m pytest tests/test_runwire_verifier_authority.py -o addopts="" -q` passes (V-01, V-02).
- The bare `python3 -m pytest` reports no failure for `test_collision_guard_bites_by_mutation` (V-01).
- A temporary, uncommitted change of the helper's `supports_fresh_verifier_session` to `False` produces the named AssertionError (refusal code `host_capability_unavailable`), not a KeyError (V-02).
- The commit touches only the declared paths (V-03).

## Spec / documentation sync

N/A: this is a test-fixture change with no behavior, CLI, or spec contract change. CHANGELOG is not updated because nothing user-facing changes.

## Open questions

### OQ-01: Should the runner itself write `verification_status` on early returns?

- Blocking: no
- Status: deferred
- Owner: plan author (trigger: a runner consumer needing the key on early returns)
- Resolution or deferral rationale: Deferred (see Deferred section). The defect was fixture-side, and the runner's early-return item shape is an existing contract. File a separate backlog item if a consumer is found that needs the key.
- Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the actual pytest summary for the file run at HEAD (`N passed`), plus the bare-suite summary line showing no failure for `test_collision_guard_bites_by_mutation`.
  - Observed evidence:
    `tests/test_runwire_verifier_authority.py` at HEAD:
    ```
    ============================== 15 passed in 6.46s ==============================
    ```
    Bare suite at HEAD:
    ```
    8247 passed, 4 skipped, 18 xfailed, 3 warnings in 680.24s (0:11:20)
    ```
    Zero failures reported; `test_collision_guard_bites_by_mutation` passed in both.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` of `_drive_execute_turn`; paste the pytest summary for the file with the change (all passing); paste the pytest output from the temporary, uncommitted `supports_fresh_verifier_session: False` edit, showing at least one `AssertionError: execute_item_core returned before the verify stage:` carrying `host_capability_unavailable` and no `KeyError`; then paste `git diff --stat` after reverting it, showing only the E-02 hunk remains.
  - Observed evidence:
    Diff of `_drive_execute_turn` (and caller parameter):
    ```diff
    --- a/tests/test_runwire_verifier_authority.py
    +++ b/tests/test_runwire_verifier_authority.py
    @@ -61,6 +61,7 @@ def _drive_execute_turn(
         validate: bool = True,
         current_status: str = "queued",
         freeze_host_capabilities: bool = True,
    +    expect_verify: bool = True,
     ) -> tuple[dict[str, Any], dict[str, Any], Path]:
         """Drive the real runner_shared.execute_item_core pipeline."""
         run_dir = root / ".aw/runs/run-test"
    @@ -172,6 +173,25 @@ def _drive_execute_turn(
             process_backlog_close=lambda *a, **k: None,
             driver_module=driver_module,
         )
    +    if expect_verify and "verification_status" not in item:
    +        latest_attempt = (item.get("attempts") or [{}])[-1]
    +        early = {
    +            k: latest_attempt[k]
    +            for k in (
                "host_capability_unavailable",
                "scope_target_refused",
                "clean_base_refused",
                "begin_refused",
            )
            if isinstance(latest_attempt, dict) and k in latest_attempt
        }
        raise AssertionError(
            f"execute_item_core returned before the verify stage: "
            f"status={item.get('status')!r} "
            f"refusal={item.get('refusal')!r} "
            f"worktree_error={item.get('worktree_error')!r} "
            f"early={early!r}"
        )
        return state, item, run_dir
    ```

    Pytest summary for the file with the change:
    ```
    ============================== 15 passed in 3.47s ==============================
    ```

    Pytest output from temporary uncommitted `supports_fresh_verifier_session: False` edit:
    ```
    >           raise AssertionError(
                    f"execute_item_core returned before the verify stage: "
                    f"status={item.get('status')!r} "
                    f"refusal={item.get('refusal')!r} "
                    f"worktree_error={item.get('worktree_error')!r} "
                    f"early={early!r}"
                )
    E           AssertionError: execute_item_core returned before the verify stage: status='fail-gate' refusal={'code': 'host_capability_unavailable', 'reason': '[RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session required by tst001 action execute. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw opencode run tst001', 'remedy': 'inspect the refused capability with `aw host capabilities`, then run the item on a host that satisfies it'} worktree_error=None early={'host_capability_unavailable': '[RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session required by tst001 action execute. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw opencode run tst001'}

    tests/test_runwire_verifier_authority.py:188: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_runwire_verifier_authority.py::test_both_hosts_behavioral_properties[agent_workflows.oc_runipd-host_lbls0]
    FAILED tests/test_runwire_verifier_authority.py::test_both_hosts_behavioral_properties[agent_workflows.agy_runipd-host_lbls1]
    FAILED tests/test_runwire_verifier_authority.py::test_verifier_session_collision_refused
    FAILED tests/test_runwire_verifier_authority.py::test_absent_verifier_session_recorded_as_none_and_not_collision
    FAILED tests/test_runwire_verifier_authority.py::test_authority_check_report_only_refuses_nothing
    FAILED tests/test_runwire_verifier_authority.py::test_verifier_session_captured_and_persisted
    FAILED tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation
    ========================= 7 failed, 8 passed in 2.74s ==========================
    ```

    `git diff --stat` after reverting temporary edit:
    ```
     tests/test_runwire_verifier_authority.py | 21 +++++++++++++++++++++
     1 file changed, 21 insertions(+)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git show --stat HEAD` showing only `tests/test_runwire_verifier_authority.py` and this plan (or only the test file, if the runner commits the plan separately).
  - Observed evidence:
    Commit touches only the two declared Scope-Paths:
    ```
     .aw/records/plans/pending/20261012-0016hm-01-r6ykw2-confirm-and-harden-the-collision-guard-mutation-test-against.ipd.md | 114 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-------
     tests/test_runwire_verifier_authority.py                                                                                 |  21 +++++++++++++++
     2 files changed, 128 insertions(+), 7 deletions(-)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Execution contract:
- Open questions: OQ-01 is deferred and non-blocking; nothing else is open.
- Scope fence (a DECLARATION, not a stop condition): `- Scope-Paths:` lists the expected files. An out-of-scope edit that proves necessary is made and then justified with `--scope-reason` at finalize; a declared path left untouched gets `--scope-ack`.
- Honesty: you MUST paste the ACTUAL runner output into each `V-*`; never claim a pass you did not run.
- Commit only your own paths through `aw commit r6ykw2 -- <paths>`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the RUNNER finalizes; do not run `aw ipd finalize` yourself there. In a HAND execution, run `aw ipd finalize r6ykw2` once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-roll a `git mv` to `executed/` or hand-edit `- Status:`. Backlog `0016hm` (gate `Blocks-Release: next`) closes through this plan's `From-Backlog` handoff.

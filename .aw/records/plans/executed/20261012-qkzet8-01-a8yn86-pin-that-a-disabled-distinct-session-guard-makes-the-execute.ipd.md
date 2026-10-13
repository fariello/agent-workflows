# IPD: Pin that a disabled distinct-session guard makes the execute preflight refuse by name

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `qkzet8`: `tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation` failed once `ACTION_EXECUTE` started requiring `supports_fresh_verifier_session` (plan `y9m1ya`), because the test's module-global monkeypatch of `agy_verifier.assert_distinct_sessions` also disables the predicate the host-capability probe `host_sandbox_profile._probe_fresh_verifier_session` exercises. When the run state carries no frozen `host_capabilities` descriptor, `runner_shared.ensure_frozen_host_capabilities` probes on demand, the probe reports False, and `runner_shared.execute_item_core` refuses the item `fail-gate` before any verify turn. That interaction (the execute gate seeing the mutation) is correct fail-closed behavior, but it is pinned by NO test: the only coverage of the refusal path forces the descriptor to False by hand (`tests/test_hostcapgate_execute_requirement.py`), and the failing test was masked, not explained, by `psgyzw` (commit `163874fcc`) adding a frozen descriptor to `_drive_execute_turn`.
- Scope: Test-only. Give `_drive_execute_turn` an opt-out of the frozen descriptor and a record of which spawns ran, then add one end-to-end behavioral test proving that under the same mutation, with the descriptor NOT frozen, the real execute preflight refuses the item by the `host_capability_unavailable` code naming `supports_fresh_verifier_session`, starts no executor or verifier turn, and writes no `verification_status`. No production code changes.
- Scope-Paths: tests/test_runwire_verifier_authority.py, .aw/records/plans/pending/20261012-qkzet8-01-a8yn86-pin-that-a-disabled-distinct-session-guard-makes-the-execute.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: qkzet8
- Blocks-Release: next
- Set: qkzet8
- Order: 1
- Highest E allocated: 03
- Author: opencode Claude Opus
- Id: a8yn86

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: a8yn86 verified (set qkzet8, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (opencode Claude Opus): created.
- 2026-10-12 to-review (opencode Claude Opus): authored review-ready from backlog qkzet8 with the mechanism measured at HEAD and the sibling plans jo55oo/r6ykw2 cross-checked for non-overlap.

## Goal

Turn the hidden interaction behind backlog `qkzet8` into an asserted, intended behavior at the level the backlog names it (the `ACTION_EXECUTE` fresh-verifier requirement in the real execute pipeline), so a future change to the preflight, the on-demand probe, or the test fixture cannot silently re-create the opaque `KeyError: 'verification_status'` or, worse, let an execute item proceed past a disabled guard.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Make the fixture able to exercise the on-demand probe

- [x] E-01 In `tests/test_runwire_verifier_authority.py` `_drive_execute_turn`, add a keyword parameter `freeze_host_capabilities: bool = True`; when False, omit the `host_capabilities` key from `state` so `runner_shared.ensure_frozen_host_capabilities` measures on demand. Also record every call to the local `spawn_executor` / `spawn_verifier` closures in a list stored on the returned state under a test-only key (for example `state["_test_spawns"]`, appending `"executor"` / `"verifier"`). The default path must behave exactly as today, and add a comment on the frozen descriptor citing backlog `qkzet8` (the descriptor is what keeps the preflight from re-probing under a mutated guard). If sibling `jo55oo` has already landed its own comment on that key (citing `4dktme`), extend that comment to cite both backlogs rather than adding a second one.
  - Depends on: none
  - Expected outcome: every existing test in the file still passes unchanged; a caller can now drive the pipeline with no frozen descriptor and observe which spawns ran.
  - Execution state: performed

### Task group 2: Pin the end-to-end refusal

- [x] E-02 Add `test_disabled_distinct_session_guard_refuses_execute_preflight` to `tests/test_runwire_verifier_authority.py`: `monkeypatch.setattr(agy_verifier, "assert_distinct_sessions", lambda e, v: None)`, then call `_drive_execute_turn(..., driver_module=oc_runipd, host_labels=runner_shared.OC_HOST_LABELS, freeze_host_capabilities=False)` and assert ALL of: `item["status"] == "fail-gate"`; `render_stream.refusal_of_item(item)` is not None with `.code == run_selection_policy.SKIP_HOST_CAPABILITY_UNAVAILABLE` and `"supports_fresh_verifier_session" in .reason`; `item["attempts"][-1]["disposition"] == "fail-gate"` and the attempt carries `host_capability_unavailable`; `"verification_status" not in item`; the recorded spawn list is empty (no executor and no verifier turn); and `state["host_capabilities"]["descriptor"]["supports_fresh_verifier_session"] is False` (the on-demand measurement was frozen into state). Also add the unmutated control in the same test or a sibling: with no monkeypatch and `freeze_host_capabilities=False`, the item is NOT refused by the preflight (no `host_capability_unavailable` key on the last attempt, and the item carries no `host_capability_unavailable` refusal) and the recorded spawn list contains `"executor"`. Do NOT assert on `item["status"]` in the control: in this fixture the unmutated item also ends `fail-gate`, from a LATER gate (`turn_retry_skipped` reads "lifecycle gate or clean-base gate refused"), with `verification_status == "verified"` and spawns `["executor", "verifier"]` (measured at review, F-7). So `status == "fail-gate"` alone does not tell the two runs apart; the discriminators are the `host_capability_unavailable` attempt key, the refusal code, and the spawn list.
  - Depends on: E-01
  - Expected outcome: the backlog's exact mechanism (global monkeypatch -> probe False -> execute preflight refusal) is a named, passing behavioral test, with a control proving the refusal is caused by the mutation and not by the environment.
  - Execution state: performed

- [x] E-03 Commit only the declared paths via `aw commit a8yn86 -- tests/test_runwire_verifier_authority.py .aw/records/plans/pending/20261012-qkzet8-01-a8yn86-pin-that-a-disabled-distinct-session-guard-makes-the-execute.ipd.md`.
  - Depends on: E-02
  - Expected outcome: one commit whose `git show --stat` lists only those two paths.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite command is bare `python3 -m pytest` (AGENTS.md repo-local contract); a narrowed run uses `python3 -m pytest -o addopts="" <path>`.
- Tests assert observable behavior, never source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE", GUIDING_PRINCIPLES P16). E-02 drives the real `runner_shared.execute_item_core` and asserts on the item/state it writes.
- `runner_shared.execute_item_core` computes `contract_action = runner_action_contract_class(action)`, calls `ensure_frozen_host_capabilities(state, cli_host, run_dir=run_dir)`, then `host_sandbox_profile.preflight_host_capabilities(...)`; on `not preflight.ok` it appends an attempt with `"host_capability_unavailable": preflight.message, "disposition": "fail-gate"`, sets `item["status"] = "fail-gate"`, records a refusal with `run_selection_policy.SKIP_HOST_CAPABILITY_UNAVAILABLE`, and returns before any spawn.
- `runner_shared.ensure_frozen_host_capabilities` returns the frozen `state["host_capabilities"]["descriptor"]` when present and otherwise probes once via `host_sandbox_profile.detect_host_capabilities` and freezes the result into state.
- `host_sandbox_profile.ACTION_CAPABILITY_REQUIREMENTS[ACTION_EXECUTE].required == (CAP_FRESH_VERIFIER_SESSION,)` (plan `y9m1ya`).
- Do NOT detect "no session started" by counting `oc_runipd.run_opencode` calls: the sandbox rungs of `detect_host_capabilities` themselves call `run_opencode` (see `host_sandbox_profile` "sentinel: _oc.run_opencode("), so that counter is nonzero even on a correct refusal (measured, F-3). The `_drive_execute_turn` spawn closures are the correct observation point.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The probe sees the mutation. With `agy_verifier.assert_distinct_sessions` replaced by a no-op, `detect_host_capabilities('opencode').supports_fresh_verifier_session` is False; unmutated it is True on this host. | Measured 2026-10-12 via `python3 -c` in this worktree: mutated -> `False` (0.53s); unmutated -> `True True` (fresh verifier, session resume). |
| F-2 | Under the mutation with NO frozen descriptor, the real execute path refuses before work starts. | Throwaway prototype (deleted, never committed) using `oc_runipd.execute_item` with the `tests/test_hostcapgate_execute_requirement.py` state shape minus `host_capabilities`: captured stderr `✗ IPD exe001 host capability refused: [RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session required by exe001 action execute. No work started for this item.` |
| F-3 | Counting `run_opencode` calls is the wrong "no session" signal. | Same prototype: `assert launched == []` failed with `[1, 1] == []`, the two calls coming from the on-demand sandbox probe, not from an agent turn. Hence E-01's spawn record. |
| F-4 | At HEAD the original test passes only because `psgyzw` froze the descriptor in the fixture; nothing states or tests that dependency. | `git log -1 -- tests/test_runwire_verifier_authority.py` -> `163874fcc work(psgyzw)`; `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q` -> `12 passed in 15.47s`. |
| F-5 | No existing test pins the end-to-end path "mutated guard -> on-demand probe -> execute refusal". `tests/test_hostcapgate_execute_requirement.py` forces `supports_fresh_verifier_session=False` in the descriptor by hand, so it never exercises the probe; `tests/test_hostcapgate_descriptor_freeze.py` tests freeze/no-reprobe with injected probe functions. | `rg -n assert_distinct_sessions tests/` matches only `tests/test_runwire_verifier_authority.py`. |
| F-7 | (Review, 2026-10-12) The proposed E-01/E-02 shape works at HEAD `d9aa65367`, prototyped in a gitignored scratch copy of the test file that was then deleted. Mutated and unfrozen: passes in 2.23s, every E-02 assertion holds, and stderr names `supports_fresh_verifier_session`. Unmutated control: no `host_capability_unavailable`, spawns `['executor', 'verifier']`, frozen probe verdict `True`, and still `status == 'fail-gate'` from a later lifecycle gate with `verification_status == 'verified'`. A full unfrozen `detect_host_capabilities('opencode')` costs 0.81s (1.2s mutated), so the control's runtime of about 22s is the pipeline's own cost and roughly matches the existing frozen test (about 25s). | Review prototype output: `MUT host_capability_unavailable [RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session ...`; `CONTROL fail-gate verified ['executor', 'verifier'] True`; `--durations` `21.97s call ...test_a8_control`, `25.35s call ...test_verifier_session_captured_and_persisted`. |
| F-6 | Sibling plans cover adjacent but different ground: `jo55oo` (backlog `4dktme`) forces the verdict True around the mutation test and adds a probe-level (not pipeline-level) fail-closed test; `r6ykw2` (backlog `0016hm`) adds a reached-verify assertion in the helper. Neither drives the pipeline with the descriptor unfrozen. | `.aw/records/plans/pending/20261012-4dktme-01-jo55oo-...ipd.md` E-01..E-03; `.aw/records/plans/pending/20261012-0016hm-01-r6ykw2-...ipd.md` E-02. |

## Proposed changes (ordered, validatable)

1. E-01: fixture opt-out of the frozen descriptor plus a spawn record (default behavior unchanged).
2. E-02: end-to-end refusal test with an unmutated control.
3. E-03: path-scoped commit.

## Deferred / out of scope (with reason)

- Production code in `host_sandbox_profile` / `runner_shared` is not changed.
  - Carrier-Declined: No defect: refusing an execute item when the distinct-session guard is disabled is the correct fail-closed behavior (spec `25kzda` 5.2, plan `y9m1ya`).
- Forcing the fresh-verifier verdict True around `test_collision_guard_bites_by_mutation` is owned by the sibling plan; duplicating it here would conflict.
  - Carrier: jo55oo
- The reached-verify assertion in `_drive_execute_turn` is owned by the sibling plan; duplicating it here would conflict.
  - Carrier: r6ykw2

## Scope check

- Over-scope: none.
- Under-scope: none. The one affected surface is the test file in Scope-Paths. If `r6ykw2` lands first, its reached-verify assertion in `_drive_execute_turn` would fire on E-02's intentional refusal; the executor must then scope that assertion off when `freeze_host_capabilities=False` (or check the expected refusal before it), and record that in the plan. This is a merge-time adjustment inside the same file, not new scope.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q` passes, including the new test (V-01, V-02).
- Mutation-of-test check: temporarily remove the monkeypatch line in the new test; the refusal assertions must fail (proves the test is sensitive to the mutation and not to the environment) (V-02).
- Bare `python3 -m pytest` shows no new failures (V-02).
- The commit touches only the declared paths (V-03).

## Spec / documentation sync

N/A: test-only change; no CLI, spec, or user-facing documentation describes this fixture. CHANGELOG is not updated because nothing user-facing changes.

## Open questions

### OQ-01: Should the fixture's frozen descriptor be removed so every test exercises the real probe?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The frozen descriptor is the intended run-scoped design (`bqtgmo`: `ensure_frozen_host_capabilities` reads the frozen descriptor instead of re-probing per item), and leaving it on by default keeps the other tests in the file independent of host probing cost and environment. E-01 makes the unfrozen path opt-in, which is exactly what E-02 needs.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff` hunk of `_drive_execute_turn` showing the `freeze_host_capabilities` parameter and the spawn record, plus pasted output of `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q` with every pre-existing test passing (`N passed`).
  - Observed evidence:
    `git diff` hunk of `_drive_execute_turn`:
    ```diff
    @@ -56,6 +59,7 @@ def _drive_execute_turn(
         write_outcome: bool = True,
         validate: bool = True,
         current_status: str = "queued",
    +    freeze_host_capabilities: bool = True,
     ) -> tuple[dict[str, Any], dict[str, Any], Path]:
         """Drive the real runner_shared.execute_item_core pipeline."""
         run_dir = root / ".aw/runs/run-test"
    @@ -79,23 +83,28 @@ def _drive_execute_turn(
             "status": current_status,
             "configured_file": str(plan_file.relative_to(root)),
         }
    +    spawns: list[str] = []
         state: dict[str, Any] = {
             "repo": str(root),
             "run_id": "run-test",
             "queue": [item],
    -        "host_capabilities": {
    -            "descriptor": {
    -                "supports_fresh_verifier_session": True,
    -                "supports_session_resume": True,
    -            }
    -        },
             "options": {
                 "isolate_worktrees": False,
                 "self_finalize": False,
                 "validate": validate,
                 "no_verify": False,
             },
    +        "_test_spawns": spawns,
         }
    +    if freeze_host_capabilities:
    +        # Backlog qkzet8: frozen descriptor keeps the preflight from re-probing
    +        # on demand under a mutated guard.
    +        state["host_capabilities"] = {
    +            "descriptor": {
    +                "supports_fresh_verifier_session": True,
    +                "supports_session_resume": True,
    +            }
    +        }

         def spawn_executor(
             prompt_path: Path,
    @@ -106,6 +115,7 @@ def _drive_execute_turn(
             session_id: Any,
             use_continue: bool,
         ) -> tuple[int, str | None, Path, list[str]]:
    +        spawns.append("executor")
             log_path = run_dir / "logs" / f"exec-{attempt_no}.log"
             log_path.write_text("exec log", encoding="utf-8")
             outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    @@ -128,6 +138,7 @@ def _drive_execute_turn(
             tracker: Any,
             attempt_no: int,
         ) -> tuple[int, str | None, Path, list[str]]:
    +        spawns.append("verifier")
             v_log = run_dir / "logs" / f"verify-{attempt_no}.log"
             v_log.write_text("verify log\npytest\n", encoding="utf-8")
             if write_outcome:
    ```
    Pre-existing test pass output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q
    ............                                                             [100%]
    12 passed in 5.35s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted passing output of `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q -k disabled_distinct_session_guard`; pasted FAILING output of the same command with the monkeypatch line temporarily removed (then pasted `git diff --stat` showing it restored); and the bare `python3 -m pytest` summary line showing no new failures. The refusal is produced by `runner_shared.execute_item_core`'s preflight branch, reached through E-01's unfrozen fixture path.
  - Observed evidence:
    Passing output:
    ```
    $ python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q -k disabled_distinct_session_guard
    ..                                                                       [100%]
    NOTE: 12 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    2 passed, 12 deselected in 2.26s
    ```
    Failing output with monkeypatch removed:
    ```
    $ python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q -k disabled_distinct_session_guard
    .F                                                                       [100%]
    =================================== FAILURES ===================================
    ________ test_disabled_distinct_session_guard_refuses_execute_preflight ________

    tmp_path = PosixPath('/tmp/pytest-of-<user>/pytest-9830/test_disabled_distinct_session1')
    monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7ae3172bb820>

        def test_disabled_distinct_session_guard_refuses_execute_preflight(
            tmp_path: Path, monkeypatch: pytest.MonkeyPatch
        ):
            """Backlog qkzet8: Disabled distinct-session guard makes execute preflight refuse."""
            repo = _setup_test_repo(tmp_path)

            state, item, _ = _drive_execute_turn(
                repo,
                driver_module=oc_runipd,
                host_labels=runner_shared.OC_HOST_LABELS,
                freeze_host_capabilities=False,
            )

            assert item["status"] == "fail-gate"
            refusal = render_stream.refusal_of_item(item)
    >       assert refusal is not None
    E       assert None is not None

    tests/test_runwire_verifier_authority.py:501: AssertionError
    ----------------------------- Captured stdout call -----------------------------
    ▶ IPD 01/1 tst001  set=test  action=execute  attempt 1
      plan: /tmp/pytest-of-<user>/pytest-9830/test_disabled_distinct_session1/.aw/records/plans/pending/20260101-test-01-tst001-test.ipd.md
      ▶ Verifying tst001 (/tmp/pytest-of-<user>/pytest-9830/test_disabled_distinct_session1/.aw/records/plans/pending/20260101-test-01-tst001-test.ipd.md)...
    ⚠︎ IPD 01/1 tst001 (execute) -> fail-gate  (exit 0)

    NOTE: 12 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    =========================== short test summary info ============================
    FAILED tests/test_runwire_verifier_authority.py::test_disabled_distinct_session_guard_refuses_execute_preflight
    1 failed, 1 passed, 12 deselected in 2.66s
    ```
    Restored `git diff --stat`:
    ```
     tests/test_runwire_verifier_authority.py | 81 +++++++++++++++++++++++++++++---
     1 file changed, 75 insertions(+), 6 deletions(-)
    ```
    Bare `python3 -m pytest` summary:
    ```
    7731 passed, 4 skipped, 3 warnings in 662.45s (0:11:02)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git show --stat HEAD` listing only `tests/test_runwire_verifier_authority.py` and this plan.
  - Observed evidence:
    Commit touches only the two declared Scope-Paths:
    ```
     .aw/records/plans/pending/20261012-qkzet8-01-a8yn86-pin-that-a-disabled-distinct-session-guard-makes-the-execute.ipd.md | ...
     tests/test_runwire_verifier_authority.py                                                                                 | 81 +++++++++++++++++++++++++++++---
     2 files changed, ...
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). All open questions are resolved (OQ-01).

Execution contract:
- Scope declaration: the change is confined to the two paths in `- Scope-Paths:`. That list is a declaration, not a stop condition. If an edit outside it turns out to be genuinely required, make it and justify it at finalize with `--scope-reason`. Acknowledge a declared path you left unmodified with `--scope-ack`.
- Honesty: you MUST paste the ACTUAL runner output for every test claim. Never report a pass you did not run.
- Commits: commit only the declared paths through `aw commit a8yn86 -- <paths>`. Never use `git add -A`, and never push.
- Lifecycle: when this plan runs under `aw oc run` / `aw agy run`, the runner owns finalize and the move to `executed/`. Do not run `aw ipd finalize` yourself. When executing by hand, finalize through `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. Never hand-roll a `git mv` into `executed/`.

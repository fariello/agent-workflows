# IPD: Make the collision-guard mutation test independent of the fresh-verifier capability probe

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation` monkeypatches the module-global `agy_verifier.assert_distinct_sessions`, which is ALSO the predicate the host-capability probe `host_sandbox_profile._probe_fresh_verifier_session` exercises; when the execute preflight measures capabilities on demand, the mutation makes the probe report `supports_fresh_verifier_session=False`, the execute item is refused `fail-gate` before any verify turn, and the test dies with `KeyError: 'verification_status'`.
- Scope: Make the test's isolation from the capability probe explicit and asserted (rather than an incidental side effect of a fixture key), make the mutated run's failure mode diagnosable, and add a behavioral regression proving the probe genuinely detects the same mutation. Test-only change; no production code changes.
- Scope-Paths: tests/test_runwire_verifier_authority.py, .aw/records/plans/pending/20261012-4dktme-01-jo55oo-make-the-collision-guard-mutation-test-independent-of-the-fr.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 4dktme
- Blocks-Release: next
- Set: 4dktme
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: jo55oo
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog 4dktme with measured root cause and reproduction.

## Goal

Make `test_collision_guard_bites_by_mutation` deterministically test what it claims (the runner's shared verify-site collision guard) without depending on whether the host-capability preflight happens to re-probe, and pin, as a separate behavioral test, that the fresh-verifier probe itself fails closed under the same mutation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Decouple the mutation test from the capability probe

- [ ] E-01 In `tests/test_runwire_verifier_authority.py`, make the mutated run in `test_collision_guard_bites_by_mutation` explicitly hold the fresh-verifier capability constant across the mutation: wrap BOTH `_drive_execute_turn` calls in `host_sandbox_profile.forced_runner_safety_verdicts({host_sandbox_profile.CAP_FRESH_VERIFIER_SESSION: (True, "4dktme: isolate verify-site guard from probe")})`, and add a comment on the `host_capabilities` key in `_drive_execute_turn` stating it is the frozen descriptor that keeps the preflight from re-probing (citing backlog `4dktme`). Sibling `a8yn86` (backlog `qkzet8`) adds a comment on the same key and a `freeze_host_capabilities` parameter to the same helper: if it has landed first, extend its comment to cite both backlogs rather than adding a second one, and keep its parameter.
  - Depends on: none
  - Expected outcome: the test no longer relies solely on the incidental `host_capabilities` fixture key added by commit `163874fcc` (psgyzw); removing that key no longer reintroduces the `KeyError`.
  - Execution state: pending

- [ ] E-02 In the same test, before reading `verification_status`, assert the mutated item was NOT refused by the preflight: no attempt carries a `host_capability_unavailable` key, and `render_stream.refusal_of_item(item_mutated)` is either None or has a `.code` other than `run_selection_policy.SKIP_HOST_CAPABILITY_UNAVAILABLE`. Give the assertion a message naming backlog `4dktme`, and read `verification_status` via `.get()` so a regression surfaces as a clear assertion rather than `KeyError`. Do NOT assert on `item_mutated["status"]`: in this fixture the mutated item ends `status == "fail-gate"` EVEN WHEN it reached and passed verification, from a later lifecycle gate (measured at review, F-6), so `status != "fail-gate"` would fail the test on its normal path.
  - Depends on: E-01
  - Expected outcome: if the coupling ever returns, the failure names the preflight refusal instead of `KeyError: 'verification_status'`.
  - Execution state: pending

### Task group 2: Pin the probe's own fail-closed behavior

- [ ] E-03 Add `test_fresh_verifier_probe_detects_disabled_distinct_session_guard` to `tests/test_runwire_verifier_authority.py`: with `monkeypatch.setattr(agy_verifier, "assert_distinct_sessions", lambda e, v: None)`, call `host_sandbox_profile.probe_runner_safety_capabilities()` (unforced) and assert `verdicts[CAP_FRESH_VERIFIER_SESSION] is False` with a note containing `ACCEPTED a reused session identity`; without the mutation assert it is `True`.
  - Depends on: none
  - Expected outcome: the interaction that caused this bug is now an asserted, intended behavior (the probe fails closed when the guard is disabled), not a hidden trap.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite command is bare `python3 -m pytest` (AGENTS.md repo-local contract); a narrowed run uses `python3 -m pytest -o addopts="" <path>`.
- The shipped seam for forcing runner-safety verdicts is `host_sandbox_profile.forced_runner_safety_verdicts` (a restoring context manager, per its docstring "a test that sets it MUST restore it"); used already in `tests/test_host_capability_wiring.py` and `tests/test_host_capability_extension.py`. No new injection mechanism is introduced.
- Tests must exercise behavior, not code structure (P16 / AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); E-03 calls the real probe and asserts its verdict.
- Execute-action preflight: `runner_shared.execute_item_core` calls `runner_action_contract_class(action)` -> `ensure_frozen_host_capabilities(state, cli_host, run_dir=run_dir)` -> `host_sandbox_profile.preflight_host_capabilities`; `ensure_frozen_host_capabilities` re-measures via `detect_host_capabilities` only when `state["host_capabilities"]["descriptor"]` is absent.
- `ACTION_CAPABILITY_REQUIREMENTS[ACTION_EXECUTE].required == (CAP_FRESH_VERIFIER_SESSION,)` (plan `y9m1ya`, commit `5d36b3554`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Root cause: `_probe_fresh_verifier_session` calls the real `agy_verifier.run_fresh_verifier`, which calls the module-global `assert_distinct_sessions`; the test's monkeypatch disables it, so the probe returns False ("fresh-verifier contract ACCEPTED a reused session identity ... (would fail OPEN)"). | Measured 2026-10-12: `python3 -c` with the lambda patch -> `detect_host_capabilities('opencode').supports_fresh_verifier_session == False` and that note. |
| F-2 | With capability False, the execute preflight refuses the item `fail-gate` before the verify turn, so `verification_status` is never written. | Reproduced 2026-10-12: the test file as of commit `846e9a722` (eow7p4) run against current code -> `E KeyError: 'verification_status'`, `1 failed`. |
| F-3 | The failure is currently MASKED, not fixed: commit `163874fcc` (psgyzw, 2026-10-09) added a frozen `host_capabilities.descriptor` to `_drive_execute_turn`'s state, so `ensure_frozen_host_capabilities` does not re-probe. Nothing in the test states or asserts that dependency. | `git show 163874fcc -- tests/test_runwire_verifier_authority.py`; current file passes: `1 passed, 11 deselected`. |
| F-4 | Several executed plans recorded this as a pre-existing failure attributed to backlog `4dktme` (e.g. `urv602`, `x7unul`, `yqv6b7`, `rtvdak`). | grep of `.aw/records/plans/executed/` for `4dktme`. |
| F-5 | Backlog `qkzet8` describes the same defect and has its OWN pending plan, `a8yn86`, which pins the PIPELINE-level refusal (unfrozen descriptor -> preflight `fail-gate`). This plan pins the PROBE-level verdict and the decoupling. Sibling `r6ykw2` (backlog `0016hm`) adds a reached-verify assertion in the helper. All three edit this one test file. | `.aw/records/plans/pending/20261012-qkzet8-01-a8yn86-...ipd.md`, `.aw/records/plans/pending/20261012-0016hm-01-r6ykw2-...ipd.md`. |
| F-6 | (Review, 2026-10-12) The decoupling works, and `status` is not a usable discriminator. | Scratch copy of the test file, deleted. Frozen descriptor plus forced verdict: normal run `fail-verify unverified`; mutated run `fail-gate verified`, with no `host_capability_unavailable`. Descriptor dropped (popped before `execute_item_core`) plus forced verdict: identical, `1 passed`. Descriptor dropped, NOT forced: stderr `[RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_fresh_verifier_session`, mutated `fail-gate None`, `host_capability_unavailable` present. Probe: unmutated `True` ("fresh-verifier separation enforced"); mutated `False`, with the note containing `ACCEPTED a reused session identity`. |

## Proposed changes (ordered, validatable)

1. E-01: force the fresh-verifier verdict True around both drives in the mutation test and document the frozen descriptor in the helper.
2. E-02: assert no preflight refusal before reading the verify disposition; use `.get()`.
3. E-03: add the probe fail-closed regression test.

## Deferred / out of scope (with reason)

- Production code in `host_sandbox_profile` / `runner_shared` is NOT changed: the probe failing closed under a disabled guard is correct behavior (F-1), and the frozen-descriptor design is intentional (bqtgmo).
- Backlog `qkzet8` is not modified by this plan: it is graduated separately through its own plan `a8yn86` (F-5).
  - Carrier: a8yn86

## Scope check

- Over-scope: none.
- Under-scope: none; the only affected surface is the one test file named in Scope-Paths.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q` passes, including the new test.
- Mutation-of-fixture check: temporarily delete the `host_capabilities` key from `_drive_execute_turn` (or, if `a8yn86` landed first, pass `freeze_host_capabilities=False` from the test) and re-run `-k collision_guard_bites`. It must still pass, which proves the E-01 decoupling. Restore afterwards.
- Full bare suite `python3 -m pytest` shows no new failures.

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes this test's fixture.

## Open questions

### OQ-01: Should the fix instead scope the monkeypatch so the probe sees the real predicate?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Both the runner verify site and the probe import the predicate from the same module lazily, so there is no call-site-local seam to patch without a production change. Forcing the verdict via the shipped `forced_runner_safety_verdicts` seam is the repository-established approach and keeps production untouched.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q -k collision_guard_bites` passing BOTH as committed AND with the `host_capabilities` key temporarily removed from `_drive_execute_turn` (paste both runs and the `git diff` of the temporary removal, then `git diff --stat` showing it reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted diff hunk showing the preflight-refusal assertion and the `.get()` read, plus pasted output of a run with E-01's forced verdict temporarily removed AND the `host_capabilities` key removed, showing the failure message names `4dktme`/preflight refusal rather than `KeyError`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted passing output of `python3 -m pytest -o addopts="" tests/test_runwire_verifier_authority.py -q -k fresh_verifier_probe_detects`, plus pasted output of the full bare `python3 -m pytest` summary line showing no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). All open questions are resolved (OQ-01).

Execution contract:
- Scope declaration: `- Scope-Paths:` declares the intended paths. It is a declaration, not a stop condition. An out-of-scope edit that turns out to be genuinely required is made and then justified at finalize with `--scope-reason`; a declared path left unmodified is acknowledged with `--scope-ack`. If sibling `a8yn86` or `r6ykw2` has already changed `_drive_execute_turn`, merge with its edits rather than overwriting them (E-01).
- Honesty: you MUST paste the ACTUAL runner output for every test claim. Never claim a pass you did not run.
- Commits: commit only declared paths through `aw commit jo55oo -- <paths>`. Never use `git add -A`, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; do not run `aw ipd finalize` yourself. When executing by hand, finalize through `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `Result: pass`. Never hand-roll a `git mv` into `executed/`.

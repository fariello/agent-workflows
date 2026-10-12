# Review findings: plan dlggmo

- Subject-Id: dlggmo
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review-sweep lane. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot was needed. `- Kind: child`. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` were clean.

Verified at HEAD: commit `91d973f58` exists with the cited subject; `tests/test_agy_runipd_cli.py` `AgySelfFinalizeTests.test_finalize_fires_on_verified_and_marks_executed` and `test_finalize_refusal_leaves_not_executed_and_not_forced` each pre-seed `01-agy001-verification.json` and branch on `k.get("fresh_session") or k.get("log_suffix") == "verify"`; `agy_runipd._spawn_verifier` passes `log_suffix="verify"` and no `fresh_session`; `runner_shared.execute_item_core._run_verifier_turn` calls `v_outcome_file.unlink(missing_ok=True)` before the spawn; `tests/test_finalize_stale_plan_path.py` test a1/a2 executor mocks write the verdict and `mock_verifier` writes it again.

E-02 DEMONSTRATED (HOW question, plan-review 3.1): a scratch driver of E-02's exact setup was run in this lane (outside the tree, nothing committed). Results: default budget -> `queued`/`verification-sent-back`; `retry_budget: 0` -> `fail-verify`/`verification-never-recorded`, `driver_finalize` not called, plan unmoved; same with the `-verification.json` unlink disabled by an in-process `pathlib.Path.unlink` monkeypatch -> `executed`, finalize called once. Two traps found: a verifier fake returning the executor's session id `"s"` fails `verifier-session-collision`, and a pre-seed with weak `tests_run` fails `verifier-no-test-evidence` under the mutation, so neither proves the claim.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (test validity) | review scratch run: same session id for both turns -> refusal `verifier-session-collision`; positive tests return `"s_verify"` from the verifier branch (`tests/test_agy_runipd_cli.py:296`) | E-02 as written ("a fake whose verifier branch writes nothing") lets an executor writing the natural `return 0, "s", ...` for both turns pass via a session-collision refusal, so the negative control passes without the stale verdict ever being the cause. Its assertion (`status` not `executed`) was too weak to tell. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires a distinct verifier session id and asserts `fail-verify` plus refusal code `verification-never-recorded`; V-02 requires the mutated failure to show `executed`/finalize, not a setup error. Added F6. |
| PR-002 | MEDIUM | IN-SCOPE | E (test validity) | review scratch run: default budget -> `queued`/`verification-sent-back`; weak `tests_run` -> `verifier-no-test-evidence` under mutation | `retry_budget: 0` was conditional ("If the default retry budget would remand"), and the pre-seed's evidence content was unspecified; both change whether the test proves anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 makes `retry_budget: 0` mandatory and pins the pre-seed's `tests_run` to the positive tests' value; the mutation probe may be an in-process monkeypatch. |
| PR-003 | MEDIUM | IN-SCOPE | G (live-artifact bar) | F5 "39 failed, 7180 passed" measured with explicit flags; plan-review rubric G re-derivation convention | E-04/V-04 used an authoring-time failing set as the bar; a live population measured with non-bare flags must be re-derived at execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 re-derives the baseline with a bare run before the first edit; V-04 and Required tests compare against it. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | plan-review Step 4 contract rules; OQ-01 `Owner: none` | The gate had no scope declaration, honesty rule, or runner versus hand finalize ownership, and it named `aw ipd begin`/finalize unconditionally. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate; OQ-01 owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which terminal refusal should the negative control assert? | `fail-verify` with `verification-never-recorded` under `retry_budget: 0`. | Assert only "not executed" (passes for unrelated causes, measured). | Review scratch run (F6); `tests/test_verification_sendback.py` `test_stale_verdict_clearing` asserts the same code. | yes |
| D-2 | How to run the mutation probe? | In-process monkeypatch of `Path.unlink` for `-verification.json`, or a reverted temporary edit. | Only a source edit (riskier in a shared tree). | Review scratch run produced `executed` under the monkeypatch. | yes |

# Review findings: plan yd4tqw

- Subject-Id: yd4tqw
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `ea7d2b880`. The plan was committed and unchanged (`5d962c22c`), so no snapshot was taken. `aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was clean after revisions.

Re-verified at review HEAD:
- `runner_shared.VERIFICATION_RETRYABLE_REFUSAL_CODES` holds three names (`VERIFY_REFUSAL_CODE_UNEVIDENCED`, `VERDICT_REFUSAL_CODE_UNREADABLE`, `VERIFY_ABSENCE_NO_OUTCOME_FILE`). `verifier-declined` is handled separately by disposition. `verifier-transport-error` is absent.
- `verification_failure_is_retryable(item, refusal_code, verify_disp=None)`. The plan called it without `item`.
- `_run_verifier_turn` (nested in `execute_item_core`) catches only `StopNowForce`, `StopAtCheckpoint`, and `StallTimeout` around `spawn_verifier`. None of the three subclasses `OSError` or `HostSpawnError`. The executor spawn site catches `(FileNotFoundError, PermissionError, OSError, HostSpawnError)`.
- `scan_last_host_error` and `_redact_absolute_paths` live in `render_stream`.
- Behavioral probe through `tests/test_verification_sendback.py`'s harness, on both hosts: `FileNotFoundError` and `HostSpawnError` from the verify call escape `execute_item` with `status == "running"`. `rc=1` with no outcome file is remanded as `verification-never-recorded`, and `verify_exit_code` is never written.
- `tests/test_fixfirst_end_to_end.py`: `_setup_matrix_run` sets `no_verify: True`, and `_assert_v02_prompt(prompt, kind, host, evidence_substr)`.
- Spec `25kzda` Section 5.5: the row reads `Implementing: Order 04 (\`ytas91\`)`, and the bullet lists 4 codes. Sibling `6g08rp` (`reviewed`) also rewrites this row and checks it in `tests/test_fixfirst_end_to_end.py`.
- Release `f33nrj` is `planned`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `runner_shared._run_verifier_turn` `try:` around `spawn_verifier` and the whole verdict-processing block | The plan did not say how wide the new `except` should be. Putting it on the existing `try` would also catch `OSError` from outcome-file and log reads after a successful spawn, and label those as transport failures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and Proposed change 2 now require a narrow `try` around the `spawn_verifier` call only, and keep the stop and stall arms unchanged. V-02 asks for a diff proving it. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness | plan E-02 "`v_rc != 0` ... and (`not v_outcome_file.is_file()` or `v_unreadable`)" | Counting an unreadable outcome file as a transport error would reclassify an existing, already-retryable verdict code (`verification-outcome-unreadable`). An outcome file that exists is a verdict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Transport classification is limited to the no-outcome-file branch. The unreadable case is recorded as a declined non-goal. |
| PR-003 | MEDIUM | IN-SCOPE | G. Evidence accuracy | `runner_shared.verification_failure_is_retryable(item, refusal_code, verify_disp=None)` | E-03 and V-01 called the predicate without `item`. | all Low | FIXED | Calls corrected. |
| PR-004 | MEDIUM | IN-SCOPE | E. Executability | `tests/test_verification_sendback.py` `_execute` drives one attempt; `tests/test_fixfirst_end_to_end.py` `_setup_matrix_run` `no_verify: True`; `_assert_v02_prompt(prompt, kind, host, evidence_substr)` | E-03 required a remand through to `executed`, which a one-attempt harness cannot reach. E-04 gave no way to turn verification on and called `_assert_v02_prompt` with the wrong signature. | all Low | FIXED | E-03 now asserts `queued`, the counter, and the event. The second attempt to `executed` belongs to E-04, which now names the option overrides and the call signature. |
| PR-005 | MEDIUM | IN-SCOPE | C. Cross-plan coordination | `6g08rp` E-02 and E-03 (`reviewed`) | `6g08rp` rewrites the same spec row in a different form and adds a checker that would flag an `Implementing:` label beside an executed plan, and its row form would never become `Shipped`. | all Low | FIXED | E-05 now writes `6g08rp`'s target form (`Shipped (\`yd4tqw\`, from backlog \`jodcz3\`).`) in place. F-06 added. |
| PR-006 | MEDIUM | UNDER-SCOPE | E. Verification | plan V-02 "Inspection of ..."; no baseline | V-02 accepted inspection rather than observation. The full-suite and `aw check all` demands had no baseline. | all Low | FIXED | V-02 now demands a probe output on both hosts plus a diff. A new E-06/V-06 records a baseline and compares by node id. |
| PR-007 | LOW | IN-SCOPE | G. Scope-Paths | `- Scope-Paths:` with `.aw/records/specs/*/...`; E-05 `aw specs note 25kzda` | The glob form and the id6 form of `aw specs note` were both non-canonical, and the plan file itself was undeclared. | all Low | FIXED | Concrete spec path and plan path declared. `aw specs note` now takes the path, re-derived at execution. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `## Deferred` "none"; spec-sync WHY | The gate lacked the scope fence, the honesty rule, the never-push rule, and conditional finalize ownership. Deferred listed nothing, and spec sync gave no reason. | all Low | FIXED | Gate rewritten. Two declined non-goals were added with `Carrier-Declined`, and a WHY sentence was added to spec sync. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which verifier outcomes count as transport failures? | A spawn exception, or no outcome file with `rc != 0` or a host error in the log | Also unreadable outcome files (that would change an existing retryable code) | `_run_verifier_turn` outcome-file branch; spec 5.5 bullet lists `verification-outcome-unreadable` separately | yes |
| D-2 | Which status label should the spec row carry? | `Shipped (...)`, in `6g08rp`'s form | `Implementing: yd4tqw ...` (fails `6g08rp`'s checker once executed) | `6g08rp` E-02 and E-03 text | yes |

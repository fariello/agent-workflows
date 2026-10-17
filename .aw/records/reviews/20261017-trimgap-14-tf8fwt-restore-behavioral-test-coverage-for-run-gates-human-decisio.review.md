# Review findings: plan tf8fwt

- Subject-Id: tf8fwt
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5299cf65d`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Child plan (Set `trimgap`, Order 14), test-only.

Verified in the lane (scratch test files `tests/test_zz_scratch_tf8.py` and scratch mutations of `agent_workflows/run_gates.py`, all removed or restored; `git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- The deleted `TestHumanDecisionGates` class: `8 passed, 12 deselected in 0.29s` (F-02 confirmed). Its fixture, the ledger seed records, and the `gated-wf` workflow match E-01 and E-05.
- Every expected value in E-02 to E-05 reproduced by direct call, including the stdin prompt string, both `to_dict` shapes, and the rejected-control case (d).
- A scratch module encoding E-02 to E-05: `26 passed in 0.47s`, `run_gates.py 102 stmts, 0 miss, 100%`.
- All three `b1mx2w` key operators are caught, as are the four mutations the V-items name and four extra branch mutations.

The plan is sound and its expected values are accurate. The findings below concern verification wording and the execution contract.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Validation (mechanism description) | V-04 "deleting the `norm_def in _APPROVAL_TOKENS` guard so an `approve` default is applied on timeout"; `run_gates.evaluate_gate` timeout branch | Deleting the guard does not approve: an `approve` default then falls to the else branch and returns `rejected`. The mutation is still caught, because the row expects `needs_input`, but V-04 misdescribed the consequence. | all Low | FIXED | V-04 now describes the real fall-through, names the row that must fail, and adds an `EOFError`-to-`approve` mutation (the stdin path that would approve). |
| PR-002 | LOW | UNDER-SCOPE | E. Goal verification | Goal; `b1mx2w` operators `return-none` / `return-false` / `return-none`; V-05 | No V-item applied the key-level operators `b1mx2w` assigned. V-05 also left the ledger side effect without any mutation that a test must catch. | all Low | FIXED | V-05 now requires all three `b1mx2w` operators to be caught, plus a no-op `record_approval` mutation. Required tests updated. |
| PR-003 | LOW | IN-SCOPE | Validation (command cannot produce the value) | V-01 `--collect-only -q \| rg -c` | That command prints `1`, not the number of tests. | all Low | FIXED | V-01 now asks for the `path: N` line from the collection output, and says to report a `CORE TIER BUDGET EXCEEDED` warning instead of un-marking tests (`o58dro`). |
| PR-004 | LOW | IN-SCOPE | Live-artifact bar / executability | E-04 and V-04 "7 timeout rows and 6 stdin-fallback cases"; no rule for a failing restored test | Test counts were used as the pass bar, and there was no rule for a restored case that fails at execution time. | all Low | FIXED | The bars now refer to "every row listed". Added the Set's rule for a failing test to E-01. |
| PR-005 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate lacked the honesty rule, the staged-file check, the rule for who runs finalize, and the scope-fence wording. It also used the placeholder `aw commit <plan>`. | all Low | FIXED | Rewrote the gate as a full execution contract using `aw commit tf8fwt`, plus cleanup of the `.coverage` file. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Require a full mutation sweep as the sibling reviews did? | No separate E-item; the three key operators are added to V-05 | A separate sweep E-item (with only 3 keys, a new item adds structure without adding coverage) | `b1mx2w` lists 3 keys; F-06 | yes |
| D-2 | `apply_default` with a non-approval, non-abort default (e.g. `later`) returns `rejected`. Pin it? | Keep the plan's row | Drop it (it could be accidental behavior) | It is the fail-safe direction (never approval) and is the documented "applied default" branch in `run_gates.evaluate_gate` | yes |

# Review findings: plan zhoul7

- Subject-Id: zhoul7
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9854ad239`. The plan was already committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` returned `clean` with 0 findings. This is a test-only child plan (Set `trimgap`, Order 18).

What was checked in the lane: scratch copies `tests/test_zzscr_*.py` of the five files from `19313eed^` with the E-01..E-06 edits, early-return mutations against the `-m core` selection, a coverage JSON file, and the pinned `pre-commit` `ruff` hook. All of these were removed or reverted afterwards; `git diff agent_workflows/` is empty, and `git status` shows only the plan and this record.

The plan's restore choices, its tier marks, the E-04 expectation update (commit `2b9e18bff`) and E-06(a) all reproduce as stated. One residual test, E-06(b), does not do what the plan says it does.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Residual test does not kill its target mutation | plan E-06(b), V-06; `agent_workflows/hooks/ipd_dependency_statement_gate.py:102` `check._on_staged_file`; `agent_workflows/check_engine.py:7241` `evaluate_ipd_dependencies` ("only those plan(s) are evaluated for per-statement findings") | The E-06(b) fixture as written (a committed dangling `aaaaaa` plus a staged valid `bbbbbb`) PASSES under `_on_staged_file -> True`. The evaluator computes per-statement findings only for the staged `plans`, so the dangling finding on `aaaaaa` never reaches `_on_staged_file`. V-06 therefore demanded a failure the planned test could not produce, and the F-05 survivor would have stayed alive. | all Low | FIXED | Replaced the E-06(b) fixture with a cycle across a committed `aaaaaa` and a re-staged `bbbbbb`. The evaluator places that cycle finding on the UNSTAGED `aaaaaa`, and only `_on_staged_file` drops it. In scratch, this test fails under `-> True` while every restored test passes. Added F-07. |
| PR-002 | LOW | UNDER-SCOPE | Goal verification | plan Goal "an early-return mutation of any of the 8 keys turns a routine test red"; Required tests | Only six spot checks were required, and `_plan_date` was never tested by mutation in the routine tier. | all Low | FIXED | Required tests and V-06 now demand all 8 keys (both polarities for `_on_staged_file`), each failing a `-m core` test. At review every one did (F-07). |
| PR-003 | LOW | IN-SCOPE | Validation (the command cannot produce the evidence) | plan Required tests `--cov-report=term-missing` | `term-missing` cannot attribute executed lines to individual keys, and one key is a nested function. | all Low | FIXED | Replaced it with a per-key check that uses a JSON coverage report. |
| PR-004 | LOW | IN-SCOPE | Executability (lint hook) | `19313eed^:tests/test_doctor_and_marker.py:8,10,12`; `.pre-commit-config.yaml` `ruff` `args: [--fix]` | Deleting `DoctorSummaryTests` leaves `io`, `types`, `redirect_stdout` and `redirect_stderr` unused. The `ruff --fix` hook strips them silently at commit time, so the committed file would differ from the diff V-05 pasted. | all Low | FIXED | E-05 now removes them explicitly. V-05 checks the diff and searches for them with `rg`. Required tests run both pinned hooks. |
| PR-005 | LOW | IN-SCOPE | Pass bar uses a live count | plan E-01..E-05, V-01..V-05, Required tests counts | Collected test counts were used as the pass bar. | all Low | FIXED | The bars now state the property (every test passes, the named tests are selected or deselected), with the counts kept as context. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | plan Approval gate; RESTORE RULE "STOP on it" | The gate lacked the honesty rule, the staged-set check, the rule for who runs finalize, and the scope-fence-as-declaration wording. The RESTORE RULE told the executor to STOP and gave no xfail disposition. This did not match the sibling plans. | all Low | FIXED | Rewrote the gate as a full execution contract and used the Set's disposition rule. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the core mark on the cli_layout test, whose class setup costs about 2.2 to 2.9s for one `aw install`? | Keep it | Pick a test from a cheaper class. Rejected: every `SystemLayoutRuleStateTests` case that catches `check_system_layout -> []` shares that setup. The bare suite with this test included ran `802 passed in 27.10s`, within the 30s budget. | F-07; `conftest.py` core budget | yes |
| D-2 | How to fix E-06(b): make the staged plan depend on the dangling one, or use a cycle? | Cycle | Staged dependent of a dangling plan. Rejected: it was also measured as not producing a finding on the unstaged plan. | F-07 probe of `evaluate_ipd_dependencies` with the hook's staged overlay | yes |

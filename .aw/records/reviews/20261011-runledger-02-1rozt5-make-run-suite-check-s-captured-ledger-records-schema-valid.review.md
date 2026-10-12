# Review findings: plan 1rozt5

- Subject-Id: 1rozt5
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7b8dde681`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Re-measured: `run_ledger_schema.ROLES` = coordinator, corrector, executor, human, investigator, runtime,
verifier; `EVIDENCE_KINDS` = artifact, command, diff, inspection, test_report. `capture_command(...,
actor="driver", evidence_kind="tests")` -> tool_event `RL-E014`, envelope `RL-E014`+`RL-E033`;
`runtime`/`test_report` -> both clean (F-01 MATCH). Only two production `capture_command(` calls exist:
`runner_shared.run_suite_check` (defective) and `host_runner.run_worker_process` (defaults, valid) (F-02
MATCH). `run_suite_check` discards `_envelope` and reads only `exit_code`, `stdout`, `stderr` (F-03 MATCH).
`runtime` precedent confirmed in `run_engine` (`actor: str = "runtime"`) and `run_gates` (`actor="runtime"`).
The fixture `runnerlayer_rehomed_premove_fingerprints.json` is referenced by no test or module. Backlog
`1g8lbe` carries `Blocks-Release: next` and `Work-Kind: bug`, and the plan inherits both.

E-03 DEMONSTRATED: with `SUITE_CHECK_ARGV` patched and a delegating spy on `run_evidence.capture_command`,
the real `run_suite_check` called it once and returned `passing=True`, `1 passed in 0.01s`. At HEAD the
captured records failed validation with `['RL-E014']` / `['RL-E014', 'RL-E033']`; with the fixed arguments
they were `[]` / `[]`. The test is mutation-sensitive by construction.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria) | plan "Required tests / validation" ("exactly one added passing test"); V-02 | The suite bar was a total-count delta, a collected test count, which the re-derivation convention forbids as a bar, and the suite size drifts between runs on this tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now by failing node id against the E-01 baseline, plus the new test's node id passing. E-01 and V-02 updated. |
| PR-002 | LOW | UNDER-SCOPE | Rubric G (execution contract) | plan "Approval and execution gate" | The gate did not name who finalizes (runner versus `aw ipd finalize`), and gave no guard that E-03's temporary revert of E-02 is never committed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional finalize ownership and a restore-before-commit rule. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept the author's OQ-01 (pass legal values rather than stop building records)? | Accept. | Drop record construction (REJECTED: that would reimplement the timeout/spawn mapping and out-of-band streams `run_suite_check` depends on; the plan's F-05 is confirmed by `run_suite_check`'s docstring). | `runner_shared.run_suite_check`; `run_evidence.capture_command`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

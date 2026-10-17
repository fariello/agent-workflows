# Review findings: plan 78g6ic

- Subject-Id: 78g6ic
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c71943e22`. The plan was byte-identical to the lane input and already committed, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 19), test-only, one declared path.

Verified in the lane (all scratch files removed and production edits reverted afterwards; `git status` clean, `git diff agent_workflows/` empty):
- `tools/deleted_test_replay.py 19313eed tests/test_benchmark_corpus.py`: `pass (29 passed)`.
- All 25 keys exist as attributes at HEAD. With the restored file alone, the coverage JSON per-function report showed a nonzero `executed_lines` count for every one of the 25 keys (`executing: 25`).
- E-02 values by direct call: `GROUND_TRUTH_FILENAME == "ground_truth.json"`, `CONTROL_CLASS == "honest_complete"`, 14 classes, 13 critical, `is_critical_class("not-a-class") is False`; `is_ground_truth_accessible` gives False for a missing path, False for an empty dir, and True after a nested `a/b/ground_truth.json`.
- Restored file plus a marker and a draft of E-02: `31 passed in 2.52s`; a bare `--collect-only` selects it (core).
- Mutations (insert `return <v>` as the first body line): `is_ground_truth_accessible`->False 1 failed; `is_critical_class`->False 1 failed; `can_pool`->True 2 failed; `freeze_protocol`->None 9 failed; `reset_task`->None 2 failed; `intended_verdict`->None 1 failed. With `-k 'not ResidualKeyTests'` both boolean mutations survive (29 passed), confirming F-03.
- `git diff 19313eed^ HEAD -- agent_workflows/benchmark_*.py tests/benchmark_fixtures` is empty, so the restored expectations still match the code.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability (stop directive) | plan E-01 "STOP on it"; E-02 "apply the E-01 stop rule"; `plan-review.md` scope-fence ruling 2026-09-01 | E-01 told the executor to STOP on a failing restored test while also filing a gated `bug` item outside Scope-Paths, with no justification route and no instruction for the failing test, so an unattended run could strand or delete it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the sibling `438gkf` disposition rule: for an intended change, cite the commit and adjust; for a regression, file a gated `bug` via `aw backlog new`, justify it with `--scope-reason`, mark the test `xfail(strict=True)`, and continue. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (unproducible evidence) | plan Required tests "Reach ... `--cov-report=term-missing`, each of the 25 keys executing" | `term-missing` reports missing lines per module, not per function, so it cannot show that each of the 25 keys executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reach now uses `--cov-report=json` and reads the per-function `executed_lines` for each key. Demonstrated at review: all 25 nonzero. |
| PR-003 | LOW | IN-SCOPE | Validation (worktree pollution) | Reach command; `438gkf` review PR-003 | Running `--cov` writes an untracked `.coverage` file into the worktree root, which the finalize scope gate sees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `COVERAGE_FILE` now points under the gitignored `.aw/state/`, scratch files are deleted, and V-02 demands a `git status --short` showing no scratch file. |
| PR-004 | LOW | IN-SCOPE | Validation (count as bar; V/requirements mismatch) | E-01 "29 tests pass"; V-01 "29 restored tests PASSED"; Required tests list `reset_task`/`intended_verdict` mutations that no V-item demands; `aw sanitize` not in any V-item | A collected test count was the bar (a test-organization artifact). Two required mutation checks and the sanitizer run had no V-item demanding their evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bar is now behavior plus core selection, and 29 is kept as context. V-01 demands all four mutations, V-02 demands `aw sanitize --agent`, and the `ResidualKeyTests` name is now a pointer only. The mutation method is spelled out, with the review measurements. |
| PR-005 | LOW | IN-SCOPE | Execution contract | old gate paragraph | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten as an execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What happens to a restored test that fails because of a regression? | File a gated `bug` backlog item and mark the test `xfail(strict=True)`, then continue | STOP the run; delete the test; leave it failing (breaks the core gate) | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling 2026-09-01; sibling `438gkf` review D-1 | yes |
| D-2 | How is per-key reach shown? | coverage JSON per-function `executed_lines` | `term-missing` line ranges mapped by hand; `--cov-context` | coverage 7.15.0 JSON report carries a `functions` map, demonstrated at review (`executing: 25`) | yes |
| D-3 | Mark the whole file `core`? | Yes, module-level `pytestmark` | Mark only a subset | 31 tests in 2.52s wall on one process at review, which is cheap relative to the 30s core budget (`conftest.py` core tier, IPD `hguae9`) | yes |

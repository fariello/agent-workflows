# Review findings: plan 438gkf

- Subject-Id: 438gkf
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 7), test-only, one declared path.

Verified in the lane (scratch test files removed afterwards; `git status` clean):
- `19313eed^:tests/test_run_analytics_export.py` (597 lines) has the `# --- E-01: the surface contract` banner, the `_code_lines` helper, and the three named source-reading tests above it.
- The E-01 subset (above the banner, minus `_code_lines` and the three tests, plus `pytestmark = pytest.mark.core`) placed under `tests/`: `28 passed in 0.52s`; a bare `python3 -m pytest --collect-only -q` selects it (core tier). With `--cov`: `271 stmts, 22 miss, 92%`, missing `181, 309, 346, 357, 407, 513, 541, 564-565, 594, 613, 638, 642, 769-775, 797, 800`, matching F-05.
- Every E-02 value (a) to (g) re-measured by direct call and matched, including the sha256 of `hi` (`8f4343...27aa4`) and `run_analytics_cache.SCHEMA_VERSION` absent (`MISSING`; `EXPORT_SCHEMA_VERSION == 1`).
- Restored subset plus a draft of E-02: `29 passed in 0.88s`, `271 stmts, 2 miss, 99%`, missing `309, 800` (the two lines F-05 predicts), so the >= 98 percent bar is reachable.
- Carriers exist: backlog `gjmiuw` lists `test_run_analytics_privacy_boundary.py`, `test_run_analytics_submit.py`, `test_run_analytics_wizard.py` to mine; `q86fxm` group 16 is `run_analytics_wizard.py`.
- Side observation (not a plan defect): running a copy of the test file from outside `tests/` with `--rootdir=.` took about 28s in collection (pytest's ignore-collect walking the repo); inside `tests/` it is under 1s. The plan places the file in `tests/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability (stop directive; contradictory regression path) | E-01 "STOP on that test", E-02 "apply the same STOP rule"; `plan-review.md` scope-fence wording ruling 2026-09-01 | E-01 and E-02 told the executor to STOP on a failing restored test, and also to file a gated `bug` backlog item, which is a path outside `Scope-Paths` with no justification route and no instruction for what to do with the failing test. An unattended run could strand, or could delete the test. | all Low | FIXED | Replaced with a disposition rule: an intended change is adjusted with a cited commit. A regression is filed via `aw backlog new` with `--blocks-release next`, justified at finalize with `--scope-reason`, and the test is marked `xfail(strict=True, reason=<bug id6>)`; then execution continues. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (check matches by construction) | old E-01 Expected outcome `rg -n "_code_lines\|read_text\\(\|..."` | The pattern included `read_text\(`, which matches 5 lines in the restored subset, so the "shows only..." check could not be passed or failed mechanically. It also missed `tokenize` (the helper's own mechanism) and any `agent_workflows/` path read. | all Low | FIXED | Split into a must-return-nothing pattern (`_code_lines\|getsource\|import ast\|import inspect\|tokenize\|agent_workflows/`) and a `read_text\(` listing limited to test-written files (5 at review). V-01 aligned. |
| PR-003 | LOW | IN-SCOPE | Validation (worktree pollution) | Reach command `--cov=...`; observed untracked `.coverage` in the lane root | Running the Reach command writes an untracked `.coverage` file into the worktree root, which the finalize scope gate would see and which an executor might commit. | all Low | FIXED | Reach and V-02 now set `COVERAGE_FILE` outside the repo; the gate repeats it. |
| PR-004 | LOW | IN-SCOPE | Evidence (bar reachability) | V-02 ">= 98 percent"; F-05 | The 98 percent bar was asserted without a measurement showing E-02 reaches it. | all Low | FIXED | Measured at review: 99 percent, missing exactly lines 309 and 800; recorded in Required tests. |
| PR-005 | LOW | IN-SCOPE | Execution contract | old gate paragraph | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, and conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What happens to a restored test that fails because of a regression? | File a gated `bug` backlog item and mark the test `xfail(strict=True)` | STOP the run; delete the test; leave it failing (breaks the core gate) | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling 2026-09-01 | yes |
| D-2 | Keep `test_run_analytics_privacy_boundary.py` out of this plan? | Keep it out (plan's OQ-02) | Restore it here as well | backlog `gjmiuw` line 17 lists it; F-06 | yes |
| D-3 | Split E-02 (seven sub-cases)? | Keep as one item | One E-item per sub-case | all seven target one module, one file, one V-item, and run in under 1s together | yes |

# Review findings: plan 9gjvrq

- Subject-Id: 9gjvrq
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `790eee401`. The plan was byte-identical to the lane input and already committed, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 22), test-only.

Verified in the lane (all scratch test files, coverage data and production mutations removed or reverted; `git status` clean, `git diff agent_workflows/` empty):
- `tools/deleted_test_replay.py 19313eed <nine files>`: 8 pass; `test_plan_readiness_recheck.py` `1 failed, 46 passed`, matching F-02. All nine paths are unoccupied at HEAD. Every test and class the plan names exists at `19313eed^`.
- A scratch restore with the E-01..E-05 edits: 7, 8, 12, 11, 5, 20, 44, 50 and 19 passed; core selections 2, 0, 1, 11, 5, 20, 1, 1, 2 (43 core tests, `2.54s`). `ruff check --select F` clean. Per-function coverage JSON under `-m core`: all 13 keys have nonzero executed lines.
- Bare `python3 -m pytest` with the scratch files present: `796 passed in 28.41s` (core budget 30s).
- Mutation sweep, `return <v>` as the first body statement, run with `-m core` over the nine files: killed `read_renames_for []`, `is_legal_edge True/False`, `_nv_resolve_types None`, `_run_noun_verb -1`, `plan_set_priority ()`, `gate_answer_needs_human_remedy ""`, `plan_reference_rewrites []`, `is_unique False`, `_rp_type_facet None`, `run_state ""`, `_rewrite_help_token None/[]`. SURVIVED: `_synthetic_key ""` and `is_unique True` (the plan's F-04, fixed by E-06), plus `RecheckResult.holding ()` (`43 passed`) and `_rewrite_help_token list(argv)` (`43 passed`, and `176 passed` even over all nine files without `-m core`).
- `holding` fix demonstrated: `test_a_blocking_question_holds_only_the_question_condition` (0.08s) fails under the mutation (`1 failed, 1 passed`).
- `_rewrite_help_token` fix demonstrated: `19313eed^:tests/test_help_token.py` passes (`4 passed`); `test_pure_rewrite` fails under the identity mutation.
- E-06 values re-measured by direct call and matched.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Coverage (goal not met on the routine gate) | `plan_readiness.RecheckResult.holding`; `cli._rewrite_help_token`; review core-only mutation sweep | The goal is defined on the routine bare core tier. Under `-m core`, `holding -> ()` survives (the only core-marked test asserts `holding() == ()`), and `_rewrite_help_token -> list(argv)` survives even over all nine files. F-04's sweep ran over all nine files, which masked the first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 adds a core marker on `test_a_blocking_question_holds_only_the_question_condition`. E-01 restores `tests/test_help_token.py` (added to Scope-Paths) with core markers on its two pure-function tests. Both kills demonstrated. Required tests now run every mutation under `-m core`. |
| PR-002 | MEDIUM | IN-SCOPE | Test contract (code-pinning test restored) | `19313eed^:tests/test_plan_readiness_recheck.py` `ContractConsistencyTests.setUp` reads `.aw/system/workflows/plan-review/plan-review.md`; four `assertIn` on wording | The class asserts that specific text remains in a workflow document, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" item (3) forbids restoring. | all Low | FIXED | E-04 removes the class; the `rg` check names it; V-04's diff demand lists it. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (check cannot pass) | E-04 Expected outcome `rg -n "read_text\|import inspect\|AntiForkTests"` | `read_text` occurs legitimately throughout the kept tests (plans written into their own temp repos), so the check could never return nothing. | all Low | FIXED | Replaced with a pattern for the removed constructs and the production-path or document reads only. |
| PR-004 | MEDIUM | IN-SCOPE | Executability (stop directive) | RESTORE RULE "STOP on it" | Same defect as siblings `438gkf`/`8bhcd3`/`94wi2f`: STOP plus an out-of-scope `bug` filing with no justification route and no handling for the failing test. | all Low | FIXED | Replaced with the Set's disposition rule (cite and adjust, or gated `bug` + `xfail(strict=True)` + `--scope-reason`, continue). |
| PR-005 | MEDIUM | IN-SCOPE | Validation (evidence the command cannot produce) | Required tests Reach `--cov-report=term-missing`, "each of the 13 keys executing" | `term-missing` reports lines, not functions, and the run writes an untracked `.coverage`. | all Low | FIXED | Reach uses the coverage JSON per-function report under `.aw/state/`; V-06 demands a clean `git status` and `aw sanitize`. |
| PR-006 | LOW | IN-SCOPE | Executability / validation (counts as bar; insertion hazard) | E-01..E-05 Expected outcomes ("7 and 8", "36", "44", "50"); E-03 `pytestmark` placement | Collected counts were the bar, and after E-04's removals the restored readiness file holds 40, not 44, tests. A naive `pytestmark` insertion after the "last import line" lands inside the parenthesized multi-line import in `test_research_priority.py` (it produced a `SyntaxError` at review). | all Low | FIXED | Bars are now behavior plus exact core selection, with counts as context. The RESTORE RULE says to insert after the last complete import statement. |
| PR-007 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, and conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Guard `_rewrite_help_token` by restoring `test_help_token.py`, or by a new residual test? | Restore the deleted file (two pure tests core-marked) | Write a new residual test in `test_artifact_rename.py` | The deleted file already asserts the rewrite behavior and passes unchanged; restoring is the Set's precedent; the plan's own F-05 had excluded it only on reach grounds | yes |
| D-2 | Drop `ContractConsistencyTests`? | Drop it | Keep it (it guards a documented contract) | `AGENTS.md` item (3) forbids asserting that specific text remains; sibling `8bhcd3` dropped docstring-text tests on the same ground | yes |
| D-3 | Which extra test to core-mark for `holding`? | `test_a_blocking_question_holds_only_the_question_condition` | Any of the other non-empty-holding tests | Measured 0.08s and kills the mutation; same class as the existing marker | yes |
| D-4 | Failure handling for a failing restored test | Set-wide disposition rule | STOP; delete the test | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling | yes |

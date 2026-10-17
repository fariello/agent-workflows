# Review findings: plan 94wi2f

- Subject-Id: 94wi2f
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `805dd2fae`. The plan was byte-identical to the lane input and already committed, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 12), test-only, one declared path.

Verified in the lane (scratch test file, probe script, coverage data and production mutations all removed or reverted; `git status` clean, `git diff agent_workflows/` empty):
- `19313eed^:tests/test_migration_inventory_shared.py` (930 lines) restored unchanged runs `15 passed`; `ruff check --select F` passes on it; the path is unoccupied at HEAD.
- Every E-02 to E-05 added value was re-measured by direct call. All matched EXCEPT the two `to_dict`/report key sets, which now include `repo_local` (added by `9adcff119`, after authoring HEAD `ddc7f543b`): report keys `['count', 'dispositions', 'findings', 'ok', 'repo_local']`; `InventoryResult(dispositions={}, findings=["x"]).to_dict()` is `{'ok': False, 'count': 0, 'dispositions': {}, 'findings': ['x'], 'repo_local': []}`.
- A draft of the recovered file plus all E-02 to E-05 additions (corrected for `repo_local`): `23 passed`. Coverage JSON per-function: all 25 keys executed; the only key-body miss is `plan_review_parity` line 1163 (`"command descriptor missing argument policy"`).
- Mutation sweep (`return None` as first body statement for each of the 25 keys; `negate` for `InventoryResult.ok` and `detect_view_drift`): 24 killed, `PlanReviewViews.semantic_digest -> None` SURVIVED (`23 passed`). Every recovered assertion on it compares two calls of the same method. With an added digest-value test (64-hex, equals `workflow_profile.semantic_digest(views.compiled)`, differs from the assess harness digest): killed (`1 failed, 23 passed`), and a constant `"0"*64` is also killed.
- Every V-item-named mutation was killed: `ok -> bool(findings)` 2 failed; `assert_no_lens_fork` return None 3; `register_persona` skip check 1; `plan_rollup` gate removed 1; `detect_view_drift` negate 2; `aliases_ok = True` 1; `Disposition.to_dict` None 2; `catalog_rows` None 2.
- Bare `python3 -m pytest` with the draft present: `777 passed in 26.02s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (stale expected values) | `migration_inventory.InventoryResult.to_dict` `"repo_local": list(self.repo_local)` (line 560); commit `9adcff119` | E-02 asserted exact key sets `{"count","dispositions","findings","ok"}` and an exact `to_dict()` dict without `repo_local`. At review HEAD both are wrong, so E-02 as written would fail and push an executor toward the wrong fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expected values updated to include `repo_local` and re-measured; the commit is cited; E-02 now requires re-measurement at execution HEAD under the disposition rule. |
| PR-002 | MEDIUM | UNDER-SCOPE | Coverage (goal not met) | `migration_inventory.PlanReviewViews.semantic_digest`; recovered assertions at `19313eed^` file lines 866, 897, 913 compare two calls | Goal says a `return-none` mutation of any of the 25 keys turns a test red. `PlanReviewViews.semantic_digest -> None` survived the review sweep. | all Low | FIXED | E-05 adds a digest-value test (shape, equality with `workflow_profile.semantic_digest`, inequality with the assess digest); V-05 demands its mutation failure. Demonstrated killed at review. |
| PR-003 | MEDIUM | IN-SCOPE | Executability (unworkable instruction) | E-05 "pytest `tmp_path`"; recovered classes are `unittest.TestCase` | pytest fixtures cannot be injected into `unittest.TestCase` methods, so the load-failure test as specified cannot be written. | all Low | FIXED | Uses `tempfile.TemporaryDirectory()`; demonstrated at review. |
| PR-004 | MEDIUM | IN-SCOPE | Validation (evidence the command cannot produce) | Required tests Reach; V-05 "`term-missing` ... all 25 keys' bodies executed" | `term-missing` reports module lines, not functions. One key-body line (`plan_review_parity` missing-argument-policy append) stays unexecuted, so "all bodies executed" was false as stated. Coverage also writes an untracked `.coverage`. | all Low | FIXED | Reach uses the coverage JSON per-function report with `COVERAGE_FILE` under `.aw/state/`; the one documented miss is named as accepted; V-05 demands clean `git status`. |
| PR-005 | LOW | IN-SCOPE | Executability (failure handling; count as bar) | E-01 Expected outcome "all 15 recovered tests pass"; no failure rule | No rule said what to do if a recovered test or added value fails at execution HEAD (PR-001 shows it can), and a collected count was the bar. | all Low | FIXED | Added the Set's disposition rule (cite and adjust, or gated `bug` + `xfail(strict=True)` + `--scope-reason`, continue); 15 is kept as context. |
| PR-006 | LOW | IN-SCOPE | Execution contract | gate paragraph `aw commit <plan>` | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, conditional finalize ownership, and used a `<plan>` placeholder. | all Low | FIXED | Gate rewritten as an execution contract naming `aw commit 94wi2f`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Assert `repo_local` in the exact key set, or relax to a superset check? | Exact set including `repo_local` | Superset assertion (weaker; would miss an unexpected new key) | `InventoryResult.to_dict` at HEAD; plan's own "exactly" wording; `9adcff119` is an intended change | yes |
| D-2 | Must the `plan_review_parity` missing-argument-policy line be covered? | No; documented as the one accepted key-body miss | Add a hand-built descriptor test | Goal is defined by `b1mx2w` operators (`return-none`), which are all killed; the branch needs a synthetic compiled dict outside the fixture | yes |
| D-3 | How to make `PlanReviewViews.semantic_digest` falsifiable? | Shape + equality with `workflow_profile.semantic_digest(views.compiled)` + inequality with the assess digest | Pin a literal digest (brittle to any fixture or compiler change) | Demonstrated kill of `None` and of a constant at review | yes |
| D-4 | Failure handling for a failing recovered test | Set-wide disposition rule (gated `bug`, `xfail(strict=True)`, continue) | STOP; delete the test | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling; siblings `438gkf`/`8bhcd3` | yes |

# Review findings: plan pdemar

- Subject-Id: pdemar
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `beb36ea1e`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Child plan (Set `trimgap`, Order 8), test-only.

Verified in the lane (scratch test file `tests/test_zz_scratch_pdemar.py` and scratch mutations of `agent_workflows/migration_complex.py`, all removed or restored; `git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- `19313eed^:tests/test_migration_complex.py` exists with the classes and 30 tests the plan names; no file at HEAD. Unchanged: `1 failed, 29 passed in 0.89s`, the failing test being the consent-gate table (F-02 confirmed).
- With only the E-02 adaptation (clean one-gate `ReleaseReadinessReport` on the `authorize_release` surface): `30 passed in 1.40s`.
- All 40 `b1mx2w` keys swept with their assigned operators against that file: 39 KILLED, `SURVIVED OperatorDatum.to_dict@return-none | 30 passed in 0.55s`.
- Every E-03 row's message reproduced by direct call; E-04 (a) to (c) expected values reproduced exactly. An extra branch: a NOT-applicable `residual_risk` raises `release refused: hard gate failure(s): residual_risk`.
- Key list in F-01 / Scope matches the 40 `unguarded-unreached` rows in `b1mx2w` `## Rollup mutation results`, with the operators F-01 states.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | E. Testing / Goal verification | Goal "Done means a `return-none`, `return-false`, `negate-return` or `raise` mutation ... of any of them turns a routine test red"; V-01..V-04 spot-check only about 7 keys; review sweep 39/40 | Nothing proves the Goal. The V-items spot-check a handful of keys and rely on coverage, which proves execution, not guarding. The review sweep found one key (`OperatorDatum.to_dict@return-none`) that coverage reports executed but no test guards. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05 (40-key sweep with each key's `b1mx2w` operator, survivors are fixed not reported) and V-05; added F-06 recording the review sweep; moved the coverage demand from V-04 to V-05. |
| PR-002 | MEDIUM | IN-SCOPE | D. Anti-regression (mutation demand mismatch) | V-04 "`OperatorDatum.to_dict` to `return {}`"; `b1mx2w` operator for that key is `return-none` | V-04 tested a different operator from the one that actually survives. | all Low | FIXED | V-04 now demands both `return None` and `return {}` for `to_dict`; E-04 names (c) as the item that kills the survivor. |
| PR-003 | LOW | IN-SCOPE | Executability (internal contradiction) | E-04 "dispositions are `DISPOSITION_FIX_NOW` and `DISPOSITION_ESCALATE`" vs "literal strings for the emitted ... value, so a rename of the emitted value fails" | Asserting emitted dispositions via constants would move with a rename, which defeats the stated purpose; the recovered Fix Bar table deliberately uses literals. | all Low | FIXED | E-04 now asserts literals `"fix-now"` / `"escalate"`; constants are for inputs only. V-04 swaps the `fix_bar` negate check (already E-05/V-05) for a disposition-literal mutation that only E-04(a) catches. |
| PR-004 | LOW | IN-SCOPE | Validation (command cannot produce the value) | V-01 `python3 -m pytest --collect-only -q \| rg -c test_migration_complex` | `--collect-only -q` prints one `path: N` line per file, so `rg -c` prints `1` (same defect fixed in sibling `jy7439` PR-002). | all Low | FIXED | V-01 now pastes the `path: N` line; adds the `CORE TIER BUDGET EXCEEDED` reporting rule (backlog `o58dro`). |
| PR-005 | LOW | IN-SCOPE | Executability / live-artifact bar | E-01 "29 of its 30 recovered tests pass before E-02" | No disposition rule for an unexpected recovered-test failure, and a test count used as the bar. | all Low | FIXED | E-01 carries the Set's disposition rule (intended change vs regression, `xfail(strict=True)` plus gated bug item); bar is now property-based with counts as context. |
| PR-006 | LOW | IN-SCOPE | Execution contract; E-03 completeness | gate paragraph; `ReleaseReviewCoordinator.authorize_release` `READINESS_INPUT_REQUIRED_GATES` branch | The gate had no honesty rule, staged-set check, conditional finalize ownership or scope-fence wording; E-03 covered the NOT-applicable input-required branch only for `full_suite`, not `residual_risk`. | all Low | FIXED | Gate rewritten as an execution contract (pattern of `jy7439`); E-03 gained the NOT-applicable `residual_risk` row. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan prove its Goal for all 40 keys? | A full sweep with each key's assigned `b1mx2w` operator (E-05/V-05) | Keep spot-checks plus coverage (coverage proves execution only; review sweep showed a survivor) | Plan Goal; `b1mx2w` `## Rollup mutation results`; review sweep F-06 | yes |
| D-2 | Assert an empty `ReleaseReadinessReport` (approves today) in E-03? | No | Add a row pinning approval of an empty report (would freeze arguably accidental behavior, and empty-report policy is not in this item's key contract) | rubric D "Do not freeze accidental behavior"; F-06 | yes |
| D-3 | Where may the E-05 sweep script live? | A gitignored scratch path (e.g. `.aw/state/`), never committed | Commit it as a tool (over-scope) or put it outside the workspace (lane permissions refuse it) | `.aw/.gitignore` `/state/`; Scope-Paths | yes |

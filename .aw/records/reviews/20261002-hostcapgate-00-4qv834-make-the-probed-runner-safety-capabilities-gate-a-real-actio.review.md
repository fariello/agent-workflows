# Review: Make the probed runner-safety capabilities gate a real action, or record honestly that they cannot

- Subject-Id: 4qv834
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fa1df54a9` in review lane `review-sweep-run-20261007T165410Z-456709`. Working tree clean;
target plan committed and byte-identical to the lane input, so the pre-review snapshot was skipped.
Structural preflight: `aw ipd lint --phase author` clean; `aw ipd coverage 4qv834` "ready for review".

Re-measured in-process: `ACTION_CLASSES == ('read_only',)`, `read_only.required == ()`,
`RUNNER_ACTION_TO_CONTRACT_ACTION == {}`, `runner_action_contract_class` -> `None` for execute/review/plan
(F-01, F-02 hold; y9m1ya has not run). Both stale-comment hits exist in `run_selection_policy.py`
("not yet exercised by any shipped requirement"). Child `bqtgmo` is under `executed/` with six V-items all
`pass`; child `y9m1ya` is `to-review` in `pending/`, declares `Item-Dependencies: executed:bqtgmo`, has seven
V-items, and its OQ-01 is `Blocking: no`, `resolved`. Carriers `gqy7yd`, `oq05nc`, `eow7p4` resolve. The
sequencing argument and fence are sound; the defects are stale counts and cross-child ownership.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Evidence / verification | Criterion 1 and E-01/V-01 cite `bqtgmo` V-01..V-05 ("five"); `bqtgmo` carries V-01..V-06 (V-06 validates E-06, `oc_runipd._apply_execution_profile`). Criterion 1 and E-02/V-02 cite `y9m1ya` V-01..V-06/V-05 ("six"); `y9m1ya` carries V-01..V-07 | Stale V-counts would let a verifier skip `bqtgmo` V-06 and `y9m1ya` V-07, the latter being the item that performs every cross-child check | All Low | FIXED | Counts corrected to V-01..V-06 and V-01..V-07 in criterion 1, E-01, E-02, V-01, V-02 |
| PR-002 | MEDIUM | IN-SCOPE | G. Orchestrator coverage | E-01 asks to confirm "`- Scope-Paths:` overlap only on files each child edits in disjoint regions" before Order 02 runs; the Cross-IPD bullet assigns disjointness to `y9m1ya` E-07(b), which compares the two diffs' hunk headers | Disjointness of two diffs cannot be checked before the second diff exists, and leaving it on the parent repeats the uncovered-obligation defect that demoted this plan on 2026-10-06 | All Low | FIXED | E-01/V-01 now read only fixed front matter (From-Backlog, Blocks-Release); disjointness is left to `y9m1ya` E-07(b), and V-02 quotes V-07's hunk headers |
| PR-003 | LOW | IN-SCOPE | G. Evidence | E-02 Expected outcome "with its blocking OQ-01 answered"; `y9m1ya` OQ-01 reads `Blocking: no`, `Status: resolved` | Contradicts the plan's own gate ("NEITHER CHILD CARRIES A BLOCKING OPEN QUESTION") | All Low | FIXED | Clause removed |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression | Cross-IPD bullet says `test_unreachable_binding_refusal_fires_under_perturbation` "fails at the Set's base commit"; `bqtgmo` V-05 records it "PASSED (1 passed in 42.84s)"; at review `python3 -m pytest -o addopts="" -q tests/test_run_finding_reachability.py` -> `5 passed in 31.12s` | The check as written ("fails the same way") would make a passing test look like a regression and would accept a new failure as pre-existing | All Low | FIXED | Bullet restated as "outcome unchanged; still passes after `y9m1ya`", citing both measurements, and flags `y9m1ya` E-07(e)'s fails-the-same-way wording as stale (cross-reference; owned by that plan's review) |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` had commit discipline only: no honesty rule, no scope-fence declaration, no conditional lifecycle transition; also said Order 01 "can be approved and executed" though `bqtgmo` executed 2026-10-03 | Hand executor has no instruction on who moves the plan to `executed/`; stale tense | All Low | FIXED | Added OQ status, declaration-only scope fence, hard-MUST paste rule, runner-retires / hand-`aw ipd finalize` split; Order 01 tense corrected |

### Coverage repair loop (`IPD-S408`)

- Attempt 1: after edits, re-ran `aw ipd coverage 4qv834 --no-commit` -> "Orchestrator 4qv834 is ready for
  review." (record written). `aw ipd lint --phase review-finalize` -> clean, 0 findings. Rows: 2 -> 2.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-004: the child `y9m1ya` E-07(e) carries the same stale "fails the same way" wording; edit the child too? | Fix the owning parent text and cross-reference the child's stale clause; leave the child to its own review | Edit `y9m1ya` in this review | plan-review Step 0.1 limits the ledger to the named plan; Step 2.4 "fix it in the owning plan and cross-reference it"; `y9m1ya` is `to-review` and will get its own review | yes |
| D-2 | OQ-01 (narrow gate) is `Status: open`, `Blocking: no`, owner maintainer. Ask now or leave it? | Leave it open, non-blocking, with its recorded default | Resolve it on the maintainer's behalf | The default is argued and both children implement it; the maintainer ruling of 2026-09-10 (plan-review "Verdict and readiness") says a non-blocking open question does not make a plan NO-GO; deciding scope is the maintainer's | yes |

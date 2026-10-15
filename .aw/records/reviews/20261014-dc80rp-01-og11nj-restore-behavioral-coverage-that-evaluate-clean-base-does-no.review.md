# Review findings: plan og11nj

- Subject-Id: og11nj
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `4f3b9c277`. The plan was committed and unchanged (`615b9d315`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review; `--phase review-finalize` conforms after the revisions.

Claims verified:

- `runner_shared.evaluate_clean_base_for_launch` runs `git status --porcelain --untracked-files=no` and delegates to `lane_containment.evaluate_clean_base`; `oc_runipd.evaluate_clean_base_for_launch` and `agy_runipd.evaluate_clean_base_for_launch` are thin wrappers over it.
- `lane_containment.evaluate_clean_base('?? scratch.log\n')` returns `clean=False, dirty_paths=('scratch.log',)`, so the property is the caller's and must be driven through git, as the plan says.
- `rg -ln evaluate_clean_base tests/` returns nothing; `tests/test_clean_base_untracked.py` does not exist.
- The "WHY (3) REPORTS RATHER THAN REFUSING" comment in `runner_shared.py` cites `tests/test_lane_clean_base.py::test_case_3_an_untracked_file_does_NOT_refuse` and is the only `test_lane_clean_base` reference in `agent_workflows/`.
- Prototype run at review (temp git repo, both hosts, both `shared_tree` values): untracked only (two root files plus one in a new subdirectory) -> `clean True, (), refuses False, proceed` on all four; plus a dirty `tracked.txt` -> `dirty_paths ('tracked.txt',)`, `warn` on isolated and `refuse` on shared, on both hosts. The E-01/E-02/E-03 expectations hold exactly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Executability / lifecycle gate | `aw ipd lint --phase pre-transition` on this plan: `check.ipd-uncarried-obligation: 2 obligation(s) name no durable carrier: deferred row 1, deferred row 2` | Neither Deferred row carried a `Carrier`, `Carrier-Evidence` or `Carrier-Declined`, so the plan could not pass its own pre-transition gate after execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row; re-run of pre-transition lint shows only the expected E/V-state S404 items. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification feasibility / ordering | Required tests "in a scratch, uncommitted edit ... revert"; V-01 `git diff --stat agent_workflows/runner_shared.py`; E-04 edits the same file | The non-vacuity mutation was not ordered relative to E-04's comment edit of the same file, so V-01's "diff shows reverted" could not be evidenced once E-04 landed, and a careless revert could discard E-04. It also claimed E-03 must fail, which it need not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mutation now made in place and reverted with `git checkout --` in E-01's outcome, BEFORE E-04; V-01 demands an empty diff at that point; claim narrowed to E-01. |
| PR-003 | LOW | IN-SCOPE | E. Test robustness | `runner_shared._run_git` passes `env=None` (inherits `os.environ`); `tests/support.py` `init_repo` / `clean_git_env` | Under a hook or nested git invocation an inherited `GIT_DIR`/`GIT_INDEX_FILE` would point the production git call at the wrong repository; temp-dir cleanup and gpgsign were unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now uses `TemporaryDirectory` + `addCleanup`, `tests.support.init_repo`, and patches `os.environ` with `clean_git_env()`; subtests named. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none` | The gate lacked the scope fence, honesty rule, `aw ipd begin`, conditional finalize ownership, never-tag and never-commit-the-mutation rules; the plan file was missing from Scope-Paths; `Owner: none` is a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path; owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Carry the deferred rows as backlog items or decline them? | `Carrier-Declined` with reason | File new backlog items (scope expansion not requested) | Backlog `dc80rp` scope as quoted in OQ-01 | yes |
| D-2 | Accept OQ-01 (other deleted classes out of scope)? | Yes, as authored | Reopen | Same basis; P16 forbids the structural pins anyway | yes |
| D-3 | Where to place the non-vacuity mutation? | In place, reverted before E-04 | Scratch copy (never imported, cannot fail the test) | `oc_runipd`/`agy_runipd` import `runner_shared` from the package; precedent review `5ne0fo` PR-002 | yes |

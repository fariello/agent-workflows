# Review findings: plan 5ne0fo

- Subject-Id: 5ne0fo
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`7361e7cc5`), so no snapshot was needed. Lint results:

- `aw ipd lint --phase author` was clean before the review.
- `--phase review-finalize` conforms after the revisions.
- `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

The F-02 prototype was re-run at review under the gitignored `.aw/state/` and then deleted. It drove `oc_runipd.main(["resume", "run-fake"])` with the six cited patches and a nonexistent temp `resolve_run_dir`. Results:

- `clean-up-and-terminate` -> 130 and "Interrupted; durable run state was preserved."
- `Terminated by SIGTERM` -> 143 and the SIGTERM sentence.
- `just-terminate-no-cleanup` -> 130 and "Terminated without clean up; worktree and lanes left in place."
- `emit_shutdown_report` was called exactly once with `to_stderr=True` in each case.
- stdout was empty, and every stderr ended with the `runner_stop.stop_interrupt_hint` line.

`rg -n "durable run state was preserved" tests/` returns nothing (F-01 holds). `oc_runipd.emit_shutdown_report` and `oc_runipd.resolve_run_dir` are module-level re-exports, so `mock.patch.object` reaches them.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Executability / lifecycle gate | `check_engine.evaluate_durable_carrier` on this plan: `check.ipd-uncarried-obligation error 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3`; `aw ipd lint --phase pre-transition` disposition `error` | None of the three Deferred rows carried a `Carrier`, `Carrier-Evidence` or `Carrier-Declined` field. The plan therefore could not pass its own pre-transition gate, so it could not finalize after execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. A re-run of pre-transition lint shows the carrier rule cleared. |
| PR-002 | MEDIUM | IN-SCOPE | E. Verification feasibility | old Required tests "changing the handler's notice string in a scratch copy"; V-01 `git diff --stat` after the mutation; E-02 edits the same file | A scratch copy of the module is never imported, so that mutation could not make the test fail. The revert was also not ordered before E-02's edit of the same file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The mutation is now made in place and reverted with `git checkout --` BEFORE E-02, and V-01 demands an empty diff at that point. |
| PR-003 | LOW | IN-SCOPE | E. Test robustness | stderr ends with `runner_stop.stop_interrupt_hint(...)` (owned by `wqq8ua`); `main` may print to stdout on other branches | E-01 did not say to avoid pinning the hint line or full bytes, did not capture stdout, and did not clean up the temp dir. E-02's `rg` outcome would also still match six unrelated occurrences of the same phrase in the file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now uses `assertIn` on the sentence only, captures stdout, and uses `TemporaryDirectory`. E-02's outcome is scoped to the S-07 comment inside the handler. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none` | The gate lacked the scope fence, the honesty rule, `aw ipd begin`, conditional finalize ownership, and the never-tag and no-commit-of-mutation rules. The plan file was missing from Scope-Paths, and `Owner: none` is a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path, and set the owner to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Carry the agy-twin deferral as a backlog item or decline it? | `Carrier-Declined` with reason (backlog scope is S-07 only; no known defect) | File a new backlog item (scope expansion the maintainer did not request) | Backlog `zgqs4e` body "property: oc_runipd.main interrupt stderr preservation notice" | yes |
| D-2 | Accept OQ-01 (agy twin out of scope)? | Yes, as authored | Reopen | Same basis | yes |

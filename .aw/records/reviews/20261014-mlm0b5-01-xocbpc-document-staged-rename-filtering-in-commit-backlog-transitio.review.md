# Review findings: plan xocbpc

- Subject-Id: xocbpc
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `f94003c03`. The plan was committed and unchanged (`dad855600`), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified at review HEAD:
- `runner_shared.commit_backlog_transition_output` (`def commit_backlog_transition_output(`, :4129) carries `add_paths = [p for p in allowed if (wt / p).exists() or _gch._in_index(wt, p)]` (:4160) with no comment. `git_commit_helper.offer_commit` has the same filter, with its rationale comment, near :1180-1196.
- Commits `9d0ba2810`, `124b917238`, `ccdb6ba94`, and `0a8624802` resolve. `124b917238` touched `runner_shared.py`, `status_set.py`, and `CHANGELOG.md` (`Fixed: ... the move now stays staged as a single file rename`).
- Scratch repo (`_make_test_repo`): `cli.main(["backlog","set",...,"--no-commit","--dir",...])` leaves `RM old -> new`. `commit_backlog_transition_output` then commits `R065`/`R074` with the subject and trailers `AW-Run`, `AW-Item`, `AW-Committed-By: driver`, and `AW-Runner`. The tracked status is clean, and the untracked `.aw/records/history.jsonl` remains.
- Unstaged move, with and without `_in_index` patched to `False`: both commit one `R100` rename and leave a clean status (F-05).
- The end-to-end probe on both hosts covered `test_5_5c_case1_success`, `test_case5c_rollback_lands_on_disk`, and `test_case_a_with_isolate_worktree`. In each, the sha is set and reachable from HEAD, there is exactly one `backlog-transition-committed` event, and no `preserved_worktree` key exists. In the rollback test, the recorded sha is the `-> graduated` commit and HEAD is `-> open`. Forcing every path into `git add` (the pre-fix shape) gave 6 failures. Patching `_in_index` to `False` gave 0 failures.
- `aw check release-gates` exits 0, and `aw sanitize --agent` is clean.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification feasibility | `runner_shared.commit_backlog_transition_output` final `git commit ... -- *allowed`; review probe with `mock.patch.object(git_commit_helper, "_in_index", lambda r, p: False)` | E-03 sensitivity check (2) required E-02 subcase (2) to fail when `or _gch._in_index` is dropped. It does not fail. `git commit -- <old> <new>` records the pathspec'd deletion itself, so the commit is the same `R100` rename. The check was unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Check (2) was removed and F-05 added. E-01's comment must now state that the branch provides index parity with `offer_commit`, not commit correctness. |
| PR-002 | HIGH | IN-SCOPE | Project rule P16 | plan E-02 subcase (2) as authored ("wrap `runner_shared._run_git` to record `git status` immediately after the `[\"add\", ...]` call") | Asserting the index right after one internal `git add` call pins the call sequence, not an observable outcome. It also existed only to serve the unsatisfiable check in PR-001. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Subcase (2) now asserts the returned sha, a single `R` rename in HEAD, and a clean tracked status. It explicitly forbids patching `_run_git`. V-02 checks that no such wrapper exists. |
| PR-003 | MEDIUM | IN-SCOPE | G. Right-sizing | plan E-02 as authored (new unit test plus three end-to-end tightenings across two files, one V-item) | E-02 bundled a new unit test and changes to three end-to-end runner tests in two modules. These are independent test surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The tightenings were split into E-04 with V-04. E-03 now depends on E-04, and `Highest E allocated: 04`. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing precision | `runner_shared._close_already_complete_backlog_item` (isolated path integrates the lane commit); `runner_shared.execute_item_core` rollback path records no `backlog_transition_commit` for the `-> open` commit | The isolated case did not require the lane sha to be reachable from main after integration. The rollback case did not say which commit the recorded sha names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires `git merge-base --is-ancestor <sha> HEAD`. It states that in the rollback case the recorded sha is the `-> graduated` commit and HEAD is `-> open`. F-06 records the measurement. |
| PR-005 | MEDIUM | IN-SCOPE | E. Verification baseline | plan E-03/V-03 "bare `python3 -m pytest` ... exit `0`" | The plan had no pre-edit baseline, so an unrelated failure already present in the suite would block it, or would be misattributed to it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records a bare-suite baseline. E-03 and V-03 compare against it by node id. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract / carriers | `## Approval and execution gate`; `## Deferred` Carrier-Declined text | The gate had no scope-fence declaration or `--scope-reason` route and did not mention the open question. The Carrier-Declined reason was boilerplate. V-01 did not require a comment-only diff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the scope-fence declaration and the OQ line, wrote a concrete Carrier-Declined reason, and made V-01 require a comment-only diff. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan pin the `_in_index` branch when it has no observable effect? | Document the limit in the code comment; no test | Assert the intermediate index (pins internals, P16); remove the branch (diverges from `offer_commit`, out of plan scope) | Review probe F-05; `git_commit_helper.offer_commit` parity | yes |
| D-2 | Should the end-to-end tightenings stay in E-02? | Split into E-04 | Keep one E-item | Right-sizing rubric G (independent test surfaces) | yes |

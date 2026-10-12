# Review findings: plan s95x79

- Subject-Id: s95x79
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `656fa1595` in an isolated review lane. The plan was committed and unchanged (`55687e2af`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was re-run after revisions.

Re-verified:
- F-03 reproduced in throwaway detached worktrees of `aw/lane/iosmvn` (`78d44e6f1`) and `aw/lane/2rm0gz` (`86aa23511`) with id lists read by `git ls-tree`/`git show`: `backlog_graduate_count(iosmvn, ids@c56c5cf0b)` -> refusal naming `k6clui`; `ids@8538be828` -> `[]`; `backlog_graduate_count(2rm0gz, ids@97959e3fa)` -> refusal naming `jykyqb, ml7b9e`; `ids@1feee61ca` -> `[]`.
- F-01 merge times against `git log -g main`: `97959e3fa` 23:14:49, `4c908ae13` (kntbbc) 23:14:52, `1feee61ca` (j7daih) 23:15:12, `c56c5cf0b` 23:18:42, `8538be828` (md2o3y) 23:18:44 (local -04:00, i.e. the plan's 03:1xZ).
- F-02: `git diff --stat 1feee61ca aw/lane/2rm0gz` = 1 file; `git diff --stat 8538be828 aw/lane/iosmvn` = 5 files.
- F-04: `runner_shared.execute_item_core` reads `_ce._iter_plan_ipds(repo)` in the `if is_spec_production or is_backlog_production:` block before the production `allocate_isolation_worktree(repo, item["id6"])` call; `allocate_isolation_worktree` passes `base_commit="HEAD"`.
- OQ-01 mechanism demonstrated: lane-worktree scan equals git read at `8538be828` (1366 ids) and `1feee61ca` (1364 ids), empty symmetric difference.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness (non-isolated path) | `runner_shared.execute_item_core` spec/backlog branches `for p, text in _ce._iter_plan_ipds(target_tree): ... if p_id not in baseline_plan_ids` | E-03 said a non-isolated run should take the baseline "from `HEAD`". The post-turn scan reads the WORKING TREE, so a committed-only baseline would count any uncommitted pre-existing plan in the shared checkout as newly produced, introducing a new false refusal. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now reads `repo`'s working tree (the same reader as the post-turn scan) at the moved point. F-08 added. E-04 case (c) pins it. Non-isolated residual race recorded under Deferred. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / ordering | `execute_item_core` `wt_handle is None and continued_plan_ids` pre-dirty filter uses `existing_before` | E-03 did not say where the moved computation goes relative to the pre-dirty `continued_plan_ids` filter that consumes it, nor that `status_before` must stay put, so an executor could move it past its consumer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names the exact insertion point (after the production lane-allocation block, before the pre-dirty filter), the variables moved, and the ones left alone. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (determinism) | E-04 original "a second process merges a commit ... between the previous item ending and this item starting" | A timing-based second process is flaky and does not target the actual window. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now wraps `allocate_isolation_worktree` to commit the foreign plan on main immediately before the real lane cut, which deterministically lands it in the window. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing (coverage) | `tests/test_backlog_production.py` / `tests/test_spec_production.py` `_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))` | E-04 drove one unspecified host; the change sits in shared code both hosts call. No negative control proved the check still refuses a genuinely mislinked plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 reuses both fixtures and the `_HOSTS` loop, adds non-isolated case (c) and negative control (d), and names the existing modules to re-run. |
| PR-005 | MEDIUM | IN-SCOPE | G. Executability / evidence | E-02 original; `execute_item_core` `attempt = {... "started_at": utc_now() ...}` | E-02's timeline treated "item started" as the read time, but `started_at` is stamped after the read, preflights and prompt build. Its instrumentation was not scoped as temporary and had no exit if the measurement cannot discriminate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 added. E-02 marks instrumentation temporary and uncommitted, compares against `worktree-allocated` events, and records a non-discriminating result instead of stalling. V-02 demands the reverted diff. |
| PR-006 | MEDIUM | IN-SCOPE | B. Safety / G. evidence | E-01 original "call ... (<iosmvn lane>, ...)" | E-01 did not say how to obtain each lane tree or build each id list; reading in the shared checkout or the live lane worktree risks touching preserved work that is a human's to integrate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 uses throwaway detached worktrees, git-read id lists, a dangling-object fallback per plan-review 1.4, and a synthetic fallback via E-04. V-01 demands the cleanup. |
| PR-007 | MEDIUM | IN-SCOPE | G. Execution contract / release gate | `## Approval and execution gate`; AGENTS.md "Every live bug gates the next release"; sibling `0owirm` | The gate lacked OQ status, scope-as-declaration wording, the MUST-paste rule, `aw ipd begin`, the staged-set check, and conditional finalize ownership. A live `Work-Kind: bug` plan carried no `- Blocks-Release:`. Scope-check told the executor to extend Scope-Paths "before changing", contradicting the declaration rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; `- Blocks-Release: next` added (resolves to planned release `f33nrj`, as siblings carry); scope-check now says make the edit and justify with `--scope-reason`. |
| PR-008 | LOW | IN-SCOPE | Spec sync / evidence | spec `25kzda` 4.8 `SPEC-PLAN-COUNT`, 4.9 `BACKLOG-GRADUATE-COUNT` rows | The N/A cited only 4.8 and misquoted it ("At least one new IPD links"); the backlog check this plan mainly fixes is 4.9, and the text reads "At least one active IPD links ... and every new one does". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | N/A rationale corrected to cite both sections verbatim. Conclusion (no spec edit) unchanged: the spec names a "Baseline/current IPD inventory" without fixing when it is taken. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: read the base commit with git, or scan the lane before the turn? | Scan the lane worktree before the turn | git `ls-tree`/`show` at `wt_handle.base_commit` (equivalent result, second reader to maintain) | Measured F-06 (identical id sets on both incident bases); post-turn scan uses `_iter_plan_ipds` on a working tree (F-08) | yes |
| D-2 | Non-isolated baseline source? | `repo` working tree, read immediately before the turn | `git ls-tree HEAD` (miscounts uncommitted plans, PR-001); diff the turn's own commits (design change) | F-08; post-turn `_iter_plan_ipds(target_tree)` reads disk | yes |
| D-3 | Fully close the non-isolated race in this plan? | No; defer with recorded consequence | Lock across the turn; commit-diff detection | Isolation defaults ON (`isolate_worktree`); both incidents isolated; fix carries Medium functionality risk | yes |
| D-4 | Add `- Blocks-Release: next`? | Yes | Leave ungated (violates the live-bug rule) | AGENTS.md "Every live bug gates the next release"; siblings `kht4vk`/`0owirm` carry `next`; `f33nrj` is the single planned release | yes |

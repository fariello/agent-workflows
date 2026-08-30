- Id: 077yqc
- Status: graduated
- Blocks-Release: next
- Set: scopeattrib
- Priority: high
- Kind: bug
- Summary: aw ipd finalize misattributes concurrent agents' uncommitted files to whichever plan finalizes first, because _paths_changed_by_this_execution unions the whole git status porcelain with no ownership filter

## Workflow history
- 2026-08-30 graduated (aw set): design handed off to plan lbgzxg (scopeattrib-01, to-review, carries From-Backlog: 077yqc and Blocks-Release: next); gate preserved via handoff. Plan resolved both open design questions from measurement: candidate (2) lease/ledger ownership lookup ELIMINATED (no per-path ownership data exists in the begin receipt or any durable registry), candidate (3) opt-in flag ELIMINATED (defaults broken behavior on), so candidate (1) intersect-with-owned-paths ships. Also corrected the item's severity: the finalize commit is path-scoped, so no co-worker work is ever swept; harm is record pollution plus unbounded blocking, NOT data loss.
- 2026-08-29 created (aw backlog): aw ipd finalize misattributes concurrent agents' uncommitted files to whichever plan finalizes first, because _paths_changed_by_this_execution unions the whole git status porcelain with no ownership filter

OBSERVED 2026-08-29: finalizing wtiso-01 (8zgybk), whose own Scope-Paths were CLEAN and whose work was already committed, repeatedly refused and demanded --scope-reason for files another agent was editing concurrently and had not yet committed - the set grew during the attempts (agent_workflows/backlog.py, check_engine.py, ipd_schema.py, then also attention_contract.py and AGENTS.md). None were touched by 8zgybk. Re-running 'aw ipd begin' did not help because the foreign files are dirty NOW, so any base yields the same union.

ROOT CAUSE: ipd_lifecycle._paths_changed_by_this_execution (ipd_lifecycle.py:791-814) computes 'paths this execution changed' as the UNION of the committed diff since the frozen base (git diff --name-only BASE..HEAD) AND the ENTIRE working tree per git status --porcelain (staged + unstaged + untracked), with NO filter for which agent or plan owns a path. Its own docstring asserts 'unrelated concurrent commits on disjoint paths are handled by the intervening-commit collision check, not here' - true for COMMITS, but uncommitted concurrent work has no such exclusion, so it is silently attributed to the finalizing plan.

WHY IT MATTERS: this toolkit is expressly designed for parallel agents sharing one checkout (until worktree isolation is universal). The current rule makes the FIRST plan to finalize responsible for every other agent's in-flight edits. The only ways through are both wrong: (a) scope-reason files you did not touch (pollutes the plan's record with false claims and defeats the audit trail the gate exists to provide), or (b) block until every other agent happens to be clean (unbounded wait, and the honest choice I took, which left a verified plan unfinalized).

FIX (direction, decide at plan time): attribute by OWNERSHIP, not by mere dirtiness. Candidates: (1) intersect the working-tree portion with the finalizing plan's frozen Scope-Paths plus paths reachable from ITS commits, and IGNORE dirty paths that are disjoint from both (mirroring the path-overlap rule aw ipd begin already applies at :610-613, which deliberately ignores disjoint uncommitted work so 'a concurrent multi-agent workflow is not thrashed' - begin and finalize are inconsistent today); (2) consult the lane/lease registry or the run ledger to identify which run owns a dirty path; (3) require an explicit --include-worktree opt-in for the current union behavior. Whatever is chosen, keep the real guarantee: an out-of-scope path the plan ITSELF changed must still demand a reason.

TEST: (1) plan P with clean Scope-Paths and committed work finalizes successfully while an UNRELATED dirty file exists outside P's scope (no scope-reason demanded) - this is the exact failure above; (2) a dirty file INSIDE P's scope still demands an ack/reason; (3) an out-of-scope path that P's OWN commits touched still demands a scope-reason (no weakening); (4) assert begin and finalize agree on the disjoint-work rule.

RELATED: begin's path-overlap rule (ipd_lifecycle.py:610-613) already gets this right; this is a begin/finalize consistency bug. Longer term, universal worktree isolation (wtiso Set) removes the shared-tree case, but the gate should be correct regardless.

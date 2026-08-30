- Id: a8eufb
- Status: open
- Set: scopeattrib
- Priority: medium
- Kind: followup
- Summary: finalize still demands a scope reason for a CONCURRENT agent's COMMITTED out-of-scope path (the committed half of the shared-checkout attribution defect)

## Workflow history
- 2026-08-30 created (aw backlog): filed by plan lbgzxg (scopeattrib-01) as the required follow-up for its declared residual gap F9

Plan `lbgzxg` fixed the WORKING-TREE half of finalize's out-of-scope attribution: an uncommitted path that the finalizing execution cannot be shown to own is now disregarded instead of demanding a --scope-reason. It deliberately did NOT touch the COMMITTED half, so this defect remains:

MEASURED (F9, reproduced at be49ac4 pre-fix and again post-fix): with a plan's own in-scope work committed path-scoped, plus ONE unrelated out-of-scope file committed by a concurrent agent, `aw ipd finalize` exits 1 with `out_of_scope_paths: ['agent_workflows/other_agents_file.py']` and demands a --scope-reason for a path that plan never touched. The finalizing plan's only options are to write a false reason into its permanent record or to block. This is the same false-record-or-block dilemma lbgzxg fixed, reached through the other half of the attribution union.

WHY IT WAS NOT FIXED IN lbgzxg: the committed half has no usable ownership signal today.
- Git authorship CANNOT discriminate: every agent in this shared checkout commits under a single user.name/user.email, so an `%an` filter would look like a fix and do nothing. The pinning test `test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation` in tests/test_finalize_scope_ownership.py constructs the co-worker commit under the SAME identity precisely so a future implementer cannot reach for %an and believe it works.
- Filtering by "commits whose message names this plan id" is prose-matching of the kind `97df1z` replaces with a structured field, so it is not acceptable either.
- A real fix needs a durable per-path or per-commit ownership record. lbgzxg's F5 eliminated the existing candidates by measurement: the begin receipt carries no per-path ownership (keys are actor, base_head, kind, plan_content_digest, plan_id, plan_path, pre_execution, requirement_digest, schema_version, scope_paths, timestamp), and `worktree_lease.LeaseTable` is an in-memory allocator structure, not a durable registry finalize can read.

BLAST RADIUS (F9, measured): an ISOLATED lane is immune, because it finalizes inside its own worktree and cannot see main's changes. This bites turns whose execution tree IS main: isolation disabled, a hand-run `aw ipd finalize` from the main checkout, or a retry from main after a lane already committed. Universal worktree isolation (the `wtiso` Set) would mitigate but not fix it.

REQUIRED OF WHOEVER TAKES THIS: the characterization test named above pins the CURRENT refusal and MUST be inverted (not deleted) by the fix, and the no-weakening case `test_own_committed_out_of_scope_path_still_demands_a_reason` must stay green, since a plan's OWN committed out-of-scope path must keep demanding a reason.

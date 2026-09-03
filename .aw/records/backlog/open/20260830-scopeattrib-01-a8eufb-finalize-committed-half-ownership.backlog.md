- Id: a8eufb
- Status: open
- Set: scopeattrib
- Priority: medium
- Work-Kind: followup
- Summary: finalize still demands a scope reason for a CONCURRENT agent's COMMITTED out-of-scope path (the committed half of the shared-checkout attribution defect)

## Workflow history
- 2026-09-03 open (opencode its_direct/pt3-claude-opus-5-1m-us): STALENESS CORRECTION, no status change (verified: `aw backlog set open a8eufb` reports `unchanged`). The item's claim that no durable per-commit ownership record exists is now FALSE: plan `m73aet` shipped the `AW-Run`/`AW-Item` git trailers, which are exactly the missing signal. But ZERO commits carry the trailer, because the only caller is `work_cmd.py:479` and the runner wiring is deliberately deferred, so the reader exists and the data does not. Recorded the precise remaining gap (`oc_runipd.py:1199` already calls `offer_commit` without `trailers=`; `agy_runipd.py` never calls it), the sequencing warning (that wiring edits the repo's highest-contention files, which `lanectn` and `5e4sb6` both touch), and the observed cost from finalizing `97df1z` (7 paths demanded a reason, 5 of them other agents' commits). STAYS OPEN by maintainer decision: `lanectn` removes the trigger more cheaply, since an isolated lane is immune. No code changed.
- 2026-08-30 created (aw backlog): filed by plan lbgzxg (scopeattrib-01) as the required follow-up for its declared residual gap F9

Plan `lbgzxg` fixed the WORKING-TREE half of finalize's out-of-scope attribution: an uncommitted path that the finalizing execution cannot be shown to own is now disregarded instead of demanding a --scope-reason. It deliberately did NOT touch the COMMITTED half, so this defect remains:

MEASURED (F9, reproduced at be49ac4 pre-fix and again post-fix): with a plan's own in-scope work committed path-scoped, plus ONE unrelated out-of-scope file committed by a concurrent agent, `aw ipd finalize` exits 1 with `out_of_scope_paths: ['agent_workflows/other_agents_file.py']` and demands a --scope-reason for a path that plan never touched. The finalizing plan's only options are to write a false reason into its permanent record or to block. This is the same false-record-or-block dilemma lbgzxg fixed, reached through the other half of the attribution union.

WHY IT WAS NOT FIXED IN lbgzxg: the committed half has no usable ownership signal today.
- Git authorship CANNOT discriminate: every agent in this shared checkout commits under a single user.name/user.email, so an `%an` filter would look like a fix and do nothing. The pinning test `test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation` in tests/test_finalize_scope_ownership.py constructs the co-worker commit under the SAME identity precisely so a future implementer cannot reach for %an and believe it works.
- Filtering by "commits whose message names this plan id" is prose-matching of the kind `97df1z` replaces with a structured field, so it is not acceptable either.
- A real fix needs a durable per-path or per-commit ownership record. lbgzxg's F5 eliminated the existing candidates by measurement: the begin receipt carries no per-path ownership (keys are actor, base_head, kind, plan_content_digest, plan_id, plan_path, pre_execution, requirement_digest, schema_version, scope_paths, timestamp), and `worktree_lease.LeaseTable` is an in-memory allocator structure, not a durable registry finalize can read.

## STALENESS CORRECTION 2026-09-03: the ownership record now EXISTS, but nothing writes it

READ THIS BEFORE ACTING ON THE PARAGRAPH ABOVE. Its conclusion that no durable per-commit ownership
record exists is now FALSE, and a future implementer following it would go looking for a mechanism
that already shipped. Corrected while the defect was hit live finalizing plan `97df1z`.

WHAT SHIPPED. Plan `m73aet` (`runtrail-01`, in `executed/`) built exactly the missing signal: immutable
`AW-Run:`/`AW-Item:` git trailers on the shipped commit path, per spec `25kzda` 4.6, which states the
deterministic checker "finds run-owned commits by required immutable trailers". Verified in the package
at HEAD `acc99713`:

- `git_commit_helper.py:48-49` defines `TRAILER_KEY_RUN = "AW-Run"` and `TRAILER_KEY_ITEM = "AW-Item"`.
- `git_commit_helper.compose_message_with_trailers:162` appends them per `git-interpret-trailers`
  convention, and `run_item_trailers:226` formats the canonical pair so callers cannot drift on key
  spelling.
- `offer_commit` takes `trailers: Sequence[str] = ()` (`:353`), defaulting EMPTY so no existing caller
  changed behavior.
- `tests/test_git_commit_helper.py` references trailers 79 times, so the mechanism is covered.

WHY IT DOES NOT YET HELP, which is the actual blocker and is a WIRING gap rather than a design gap:
**no commit anywhere carries the trailer.** Verified by walking the last 400 commits on all refs and
reading `%(trailers:key=AW-Run,valueonly)`: zero hits. The only caller that passes trailers is
`work_cmd.py:479` via `_trailers_from_args`, whose own docstring (`work_cmd.py:362-377`) states the
values must come from a live run and that "the runner wiring is deliberately deferred - a public flag
whose only consumer does not exist yet is a contract taken on for nothing". There is no CLI flag
(`rg -n 'AW-Run' agent_workflows/cli.py` -> 0 hits).

THE PRECISE REMAINING GAP, so the next implementer does not re-derive it: the runner DOES already reach
the shipped commit path, at `oc_runipd.py:1199`, and it calls `offer_commit(repo, paths, message=...,
assume_yes=True, interactive=False)` with NO `trailers=` argument. `agy_runipd.py` does not call
`offer_commit` at all (0 hits). So the work is (1) pass `run_item_trailers(run_id, item_id6)` at that
one opencode call site, (2) give the antigravity runner the same commit path, and (3) only then teach
finalize to attribute a committed path by trailer instead of by "changed since base_head".

SEQUENCING WARNING, and the reason this stays OPEN rather than becoming a plan now (maintainer decision
2026-09-03): step (2) means editing `oc_runipd.py`/`agy_runipd.py`, the highest-contention files in the
repo. 21 unexecuted plans declare them, the `lanectn` Set (7 plans, `reviewed`, unexecuted) edits them,
and `5e4sb6` exists to de-duplicate them, having measured 52 diverged symbols between them at HEAD
`769989ce` (research `tvnq50`). `m73aet` deferred this wiring for exactly that reason. Wiring it now
would start the riskiest work in the repo to fix a paperwork-noise defect that already fails CLOSED.

CHEAPER PATH ALREADY QUEUED: per the BLAST RADIUS note below, an isolated lane is IMMUNE. `lanectn`
(universal lane containment, adopting spec `7ckptx`) therefore removes the TRIGGER for the normal path
without touching attribution logic at all. Prefer letting that land first.

OBSERVED COST, so severity is judged from evidence and not from the defect's shape: finalizing `97df1z`
from the main checkout demanded a `--scope-reason` for SEVEN paths, of which FIVE were other agents'
committed work (`cli.py` and `run_viewer.py` from `1273806c`, `ipd_lifecycle.py` from `6771e590`,
`selectors.py` and `plans_index.py` from `b3233960`). Truthful reasons naming the owning commits were
recorded instead of false ones, so the record is honest but carries five "NOT THIS PLAN'S CHANGE"
entries that should not have been necessary. No wrong code, no data loss, no false claim: the gate fails
closed, so the failure mode is noise plus one round trip, not corruption.

BLAST RADIUS (F9, measured): an ISOLATED lane is immune, because it finalizes inside its own worktree and cannot see main's changes. This bites turns whose execution tree IS main: isolation disabled, a hand-run `aw ipd finalize` from the main checkout, or a retry from main after a lane already committed. Universal worktree isolation (the `wtiso` Set) would mitigate but not fix it.

REQUIRED OF WHOEVER TAKES THIS: the characterization test named above pins the CURRENT refusal and MUST be inverted (not deleted) by the fix, and the no-weakening case `test_own_committed_out_of_scope_path_still_demands_a_reason` must stay green, since a plan's OWN committed out-of-scope path must keep demanding a reason.

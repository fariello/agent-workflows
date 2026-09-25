- Id: j0ag0u
- Status: open
- Set: trailread
- Priority: low
- Work-Kind: chore
- Summary: Spec 25kzda still says NOTHING PASSES the AW-Run/AW-Item trailers, which wao266 made false for the driver-side commit

## Workflow history
- 2026-09-22 created (aw backlog): Spec 25kzda still says NOTHING PASSES the AW-Run/AW-Item trailers, which wao266 made false for the driver-side commit

MEASURED 2026-09-22 at plan wao266's finalize.

WHAT IS NOW STALE. Spec `25kzda` (`.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) says in its infrastructure paragraph, around `:59-62`: 'STILL NET-NEW and to be built: the hash-chained run ledger's `AW-Run:`/`AW-Item:` commit trailers (the ledger AND the writer are built - `git_commit_helper.run_item_trailers` formats them - but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer; plan `wao266` from backlog `a8eufb` owns the wiring)'.

WHAT CHANGED. `wao266` has now EXECUTED. `oc_runipd.commit_backlog_close` passes `run_item_trailers(run_id, plan_id6)` at the one `offer_commit` site both hosts reach, proven by a git-parser read-back test. So 'NOTHING PASSES THEM' is now false as written.

BE PRECISE IN THE CORRECTION, because an overcorrection is worse than the staleness. What is true after `wao266`: the runner passes trailers at its DRIVER-SIDE backlog-close commit, whose population was 46 commits of 3971 at that measurement, every one touching only `.backlog.md` files. What remains TRUE AND UNCHANGED: no commit that finalize's attribution reads carries a trailer, because that range (`base_head..HEAD`) holds the AGENT's own code commits made via raw `git commit`, which pass through no `offer_commit` call (filed as backlog `j2srcc`). Also still true: NOTHING READS a trailer back, so section 4.2's `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY` rows remain correctly unbound and MUST NOT be edited (that table is transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so a cell edit is a code change).

The 'zero of 3764 commits' figure will also stay true until a run closes a backlog item through the non-isolated path; `wao266` could not produce such a commit itself, since the writer is invoked by the driver and not by the executing agent.

WHY NOT FIXED IN wao266. `Scope-Paths` did not include the spec, and the plan's own spec-sync section explicitly instructed the executor NOT to edit the 4.2 rows and did not authorize a preamble edit; the plan's gate additionally forbids editing an approved spec's declared regions without declaring it. Recording it is the conservative act.

RELATED: backlog `sbh1o1` already tracks citation rot in this same spec paragraph, and `sd2wz5` tracked an earlier restaling of it. Consider fixing all of them in one pass, since the paragraph is a point-in-time snapshot the spec's own preamble says nothing enforces.

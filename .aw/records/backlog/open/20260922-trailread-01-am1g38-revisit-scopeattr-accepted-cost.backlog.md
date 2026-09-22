- Id: am1g38
- Status: open
- Set: trailread
- Priority: medium
- Work-Kind: followup
- Summary: Revisit h9cn0y's accepted attribution cost now that the driver-side run ownership trailer writer exists

## Workflow history
- 2026-09-22 created (aw backlog): Revisit h9cn0y's accepted attribution cost now that the driver-side run ownership trailer writer exists

SUCCESSOR TO PLAN wao266 (runtrailwire-01), filed at its finalize as its Deferred section requires.

WHAT h9cn0y LEFT OPEN. h9cn0y (scopeattr-01, executed) owns finalize's committed-half attribution. Its own review F-14 measured that git authorship cannot partition actors in this repository (identical `%an`/`%ae` across five incident commits, the plan's own included) and F-13 that the run record is unreachable from finalize, and it concluded that commit trailers are 'the ONLY identified way to attribute a commit to an execution here'. It then shipped the weaker ownership-PREDICATE fix with a STATED ACCEPTED COST and deferred trailers to a later plan naming backlog a8eufb. Because h9cn0y has EXECUTED, that accepted cost is LIVE in the tree today rather than prospective: its E-02 excludes an unowned committed class, which also stops demanding a reason for the executor's OWN out-of-scope commit, and its E-03 message reflects that exclusion.

WHAT CHANGED THAT MAKES THIS FILEABLE. wao266 landed the WRITER half: `oc_runipd.commit_backlog_close` now passes `git_commit_helper.run_item_trailers(run_id, plan_id6)`, both hosts reach that one site, and a git-parser read-back test proves `AW-Run`/`AW-Item` land as real trailers. So the substrate h9cn0y said did not exist now exists for that one commit path.

WHY THIS IS NOT YET ACTIONABLE AS A FIX, AND WHAT MUST COME FIRST. Reading trailers back only helps if the commits finalize inspects carry them, and they do not: finalize reads `base_head..HEAD` (`ipd_lifecycle._changed_path_sources`), which contains the AGENT's own code commits made via raw `git commit`, not the driver's backlog-close commit. So this item is BLOCKED IN PRACTICE on the agent-commit trailering work, filed as backlog `j2srcc`. Doing this one first would build a reader for an empty corpus.

WHAT THIS ITEM SHOULD DO WHEN UNBLOCKED. (1) Teach finalize's committed-half attribution to consult `AW-Run`/`AW-Item` trailers, FAILING CLOSED on an untrailered commit (never inferring 'not the run's' from absence, per wao266 OQ-03: the corpus will permanently contain untrailered commits and backfilling is impossible without rewriting history). (2) Re-examine whether h9cn0y E-02's accepted cost can then be removed, and whether E-03's message should change. (3) Consider binding `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY`, which `run_evidence.py`'s tally records as unbound precisely because 'nothing reads a trailer back' - but only on a real reader plus a tree-diff proof, since binding them on the strength of a writer is the fail-open error that tally warns about.

NOT A DEFECT REPORT. Nothing is broken by wao266; this records a deliberate deferral so the dependency is not left implicit.

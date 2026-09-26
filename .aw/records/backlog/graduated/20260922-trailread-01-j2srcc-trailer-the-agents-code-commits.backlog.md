- Id: j2srcc
- Status: graduated
- Graduated-To: trailread
- Set: trailread
- Priority: medium
- Work-Kind: feature
- Summary: Make the agent's own code commits carry AW-Run/AW-Item trailers, which is the half that would let finalize attribute a committed path

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan a6xbso (Set trailread), re-verified live at HEAD.
- 2026-09-22 created (aw backlog): Make the agent's own code commits carry AW-Run/AW-Item trailers, which is the half that would let finalize attribute a committed path

THE LARGER HALF OF a8eufb, filed at plan wao266's finalize as its execution gate requires, rather than left implicit.

WHAT wao266 DELIVERED AND WHAT IT DELIBERATELY DID NOT. wao266 wired `run_item_trailers` into `oc_runipd.commit_backlog_close`, the ONE `offer_commit` call site both runners share. Measured at its execution: that path has produced 46 commits across the repository's 3971 (review had measured 3 of 2926; the path became routine after 2026-09-04 and the newest is same-day), and EVERY file any of them touched is a `.backlog.md`. So the writer is real, tested, and in active use - and it puts a trailer on no commit that finalize's attribution reads.

WHY WIRING `offer_commit` CANNOT REACH THE COMMITS THAT MATTER. `ipd_lifecycle._changed_path_sources` attributes by diffing `base_head..HEAD`. Every commit in that range is made by the AGENT running raw `git commit -m msg -- <path>`, as the runbook text at `oc_runipd.py` directs. Those commits pass through no `offer_commit` call, so no amount of driver-side wiring reaches them. This is a structural fact about who makes the commit, not a gap in the wiring.

THE TWO CANDIDATE ROUTES, BOTH WITH REAL COSTS. (A) CHANGE WHAT THE RUNNER INSTRUCTS: extend the runbook/prompt so the agent appends the trailers to its own commit messages. Cheap to build; its compliance CANNOT be enforced by any code path, so an agent that ignores or garbles the instruction produces silently untrailered (or wrongly trailered) commits. (B) ROUTE AGENT COMMITS THROUGH `aw commit`: `work_cmd._trailers_from_args` already accepts `run_id`/`item_id6` off a namespace, so the values have a home. Enforceable and single-sourced, but it changes the committing interface every executing agent uses, and the repository's own AGENTS.md currently prescribes `aw commit` while the runner's runbook directs raw `git commit`, so the two would need reconciling.

THE FAIL-OPEN TRAP THIS MUST AVOID, recorded because it is the likely failure mode. Under either route the corpus will contain untrailered commits forever (pre-existing history cannot be backfilled without rewriting it, and the trailers' whole value is immutability). A consumer must therefore treat an absent trailer as UNKNOWN ownership, NEVER as 'not this run's'. wao266's OQ-03 resolved this explicitly, and this repository has rejected the same fail-open inference twice before (host capabilities, authorship-based attribution). Route (A) makes the trap sharper, because noncompliance is indistinguishable from absence.

WHY IT NEEDS A MAINTAINER DECISION BEFORE A PLAN. Choosing (A) or (B) is a decision about the agent's committing contract and about how much enforcement is worth, which is scope and risk appetite, not a fact recoverable from the repository. A plan should not be authored until that choice is made.

DEPENDENCY: the follow-up that teaches finalize to READ trailers is backlog `am1g38`, which is blocked on this one; building the reader first would mean reading an empty corpus.

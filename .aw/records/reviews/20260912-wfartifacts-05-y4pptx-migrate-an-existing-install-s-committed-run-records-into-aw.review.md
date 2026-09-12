# Review: migrate an existing install's committed run records into .aw/workflow-artifacts, child y4pptx (Set wfartifacts)

- Subject-Id: y4pptx
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `14b09376`. `aw ipd lint --phase author` CONFORMED with zero findings before semantic
review, and `--phase review-finalize` conformed after every revision.

SELF-REVIEW DISCLOSURE: the same agent and model authored this Set minutes earlier, so this is close to
a self-review and is worth less than an independent one. Its value therefore rests on what was
EXECUTED rather than reasoned: every numeric claim in every plan was re-measured against the
repository, which is what produced the findings below.

THIS IS THE ONLY CHILD THAT TOUCHES A USER'S COMMITTED HISTORY, so it got the closest reading, and it
had the most serious gap.

WHAT WAS CONFIRMED EXACTLY. The 29-repo count, the 11 tracked files across two assess runs in one repo, and
the 3 including two advise session summaries in another, all re-verified. `tools/untrack-workflow-artifacts.py`
does set `IGNORE_RULE = f"{ARTIFACTS}/"` on the repo-root path and has NO caller in `agent_workflows/`,
so the plan is right that it untracks in place and is not this deliverable.

THE GAP: THE PLAN DESCRIBED A MOVE WHERE THE REALITY IS A MERGE. Measured in this repository, BOTH trees
are populated (`workflow-artifacts/` 5 entries, `.aw/workflow-artifacts/` 10) and THREE workflow names
exist in both. The plan's only conflict rule was same-file-different-bytes; it never said the
destination directory may already exist and hold other runs. An implementation reading it literally
would either fail on the existing directory or replace it, and replacing it would destroy run records
this repo has kept since July.

WHY IT IS SAFE ANYWAY, AND WHY THAT IS NOT A REASON TO RELAX. No `<RUN_ID>` collides across the three
shared workflows, because a `<RUN_ID>` is a timestamp and collision needs two runs of one workflow in
the same second. So the merge is clean HERE. That is a property of the data, not of the design, which is
why the refusal rule stays and a merge test is now mandatory.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-002 | HIGH | IN-SCOPE | A. Correctness and data integrity | `ls` on both trees; `comm -12` per shared workflow name; `ls` per `<RUN_ID>` | THE DESTINATION IS OFTEN ALREADY POPULATED, SO THIS IS A MERGE. In this repo `workflow-artifacts/` has 5 entries and `.aw/workflow-artifacts/` has 10, sharing `assess-bugs`, `assess-documentation` and `release-review`. The plan described only a same-FILE conflict, so an implementation assuming an absent destination fails on the existing directory or replaces it, destroying records kept since July. ZERO `<RUN_ID>`s collide (run ids are timestamps), so the merge is clean here, but that is the data's property and not the design's. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now requires merging per `<workflow>/<RUN_ID>/` leaf, states the measured populated-destination case, and explains why zero collisions must NOT be read as making collision handling unnecessary. A Required-tests bullet and V-03 now demand a MERGE test proving a pre-existing destination run survives alongside the relocated one, and V-01 makes an absent-destination-only implementation a FAILED validation. Added F-7. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The measurement shows no RUN_ID collisions. Should the refusal rule be dropped as dead code? | KEEP IT. | Drop it and merge unconditionally (rejected: zero collisions is a property of TIMESTAMP run ids in the repos measured, not a guarantee, and the failure mode it prevents is unrecoverable overwrite of a user's run record; the cost of keeping it is one branch). | The per-`<RUN_ID>` `comm` output; the plan's own never-delete invariant. | yes |
| D-2 | Should this plan be tested against the real affected repos? | NO, SCRATCH CLONES ONLY, and the execution contract now says so. | Test against them (rejected: they hold the maintainer's genuinely committed review history, a worktree isolates THIS repo and protects neither, and a bug in a migration under test would damage records that cannot be regenerated). | The `git ls-files` output in both affected repos (unnamed here, being private); maintainer instruction on worktree isolation. | yes |

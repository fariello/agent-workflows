- Id: dvonrn
- Status: parked
- Set: lifegate
- Priority: high
- Work-Kind: bug
- Summary: DRAFT DESIGN: replace the location-plus-token lifecycle gate with one plan-scoped 'a live runner holds this plan' check, allow begin/finalize anywhere, and nudge toward the lane

## Workflow history
- 2026-09-26 created (aw backlog): Draft design, decisions being recorded one at a time with the maintainer (2026-09-26). Not yet ready to graduate.

STATUS: DRAFT. Design decisions are being settled one at a time with the maintainer; do not graduate until every item below is DECIDED.

## Problem

The terminal lifecycle gate added by executed plan u27oh3 (spec c4gd2h) blocks aw ipd finalize and orchestrator retirement in any checkout under .aw/worktrees/ or on an aw/lane/* branch unless a per-run secret token (AW_DRIVER_ATTEST) is presented. It guesses 'a runner owns this' from the folder path, so it wrongly blocks a human's own feature worktree placed under .aw/worktrees/ (measured 2026-09-26: feat-partition, AW-LIFECYCLE-ROLE-001) and blocks recovery of a lane whose runner died. The token only stops honest actors (u27oh3's own honest limit: a same-user agent can read the token file), and honest actors are already stopped by the worker label and a clear message. Guiding principle being added alongside this: we never try to mitigate a malicious agent.

## Decisions

### D1 (DECIDED 2026-09-26): no location rule; refuse only when someone else is actively working on the plan

- begin and finalize are ALLOWED ANYWHERE: inside a lane, on a feature branch, or in main.
- Doing them in the lane/branch is PREFERRED (the plan's move to executed/ travels with the code and lands on main in one reviewed merge) but it is a preference, never enforced.
- The runner itself already finalizes INSIDE its lane (runner_shared: finalize_repo = Path(work_dir), then sync_receipt_into_worktree, then finalize), which is the preferred shape and stays.
- The only reason to refuse: a LIVE runner currently holds this plan and the caller is not that runner. Refuse with the run named and two choices (wait, or aw <host> run stop <run-id>), plus a deliberate override --take-over '<reason>' that records the reason in the plan's history.
- The runner's own agent stays refused by its existing worker label (AW_EXECUTION_ROLE=worker) and the existing 'this is the runner's step, you are done' message. That was the only honest mistake actually observed.
- The runner itself needs NO new label or token: it is the recorded holder (the owner file names its process), so the check lets the holder through by a plain comparison, not a security measure.
- NUDGE, never a refusal: when begin/finalize runs in main and a lane or feature branch for the same plan exists, print one line such as 'a lane for this plan exists; finalizing there keeps main cleaner'.
- Delete: the per-run token (driver-attest.token), minting/passing/withholding it, verify_driver_attestation, and lane_worktree_active's path/branch guess as a gate.

### D2 (OPEN): what 'holds this plan' means and how it is found

Draft direction: key on the PLAN, not the folder (is any live runner holding this id6?), which covers inside-a-lane, main-while-a-lane-runs, and neither. Needs the lookup source and the stale-owner-file rules.

### D3 (OPEN): stale owner files and platforms (reused process numbers are only detected on Linux via /proc start time).

### D4 (OPEN): every entry point (aw ipd begin/finalize, aw set executed, orchestrator retirement) passes the one check at a shared choke point.

### D5 (OPEN): what to do with other gates that exist only against malicious agents (wtiso_gate, runner_shared comments, host_sandbox_profile, the --by-human attestation).

### D6 (OPEN): wording of the new guiding principle (GUIDING_PRINCIPLES.md P15).

### D7 (OPEN): fate of the 1o4eif / x03wgn sandbox work.

### D8 (OPEN): specs to amend (c4gd2h at least) and the Scope-Paths declaration.

## Honest limits

Guidance for honest actors only. It is not, and is not meant to be, a security boundary.

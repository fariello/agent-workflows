- Id: nuanaw
- Status: open
- Blocks-Release: next
- Set: lanevis
- Priority: high
- Work-Kind: bug
- Summary: aw attention is blind to a stranded lane, so unintegrated work is invisible to the one cross-tree view: 11 lanes sat unnoticed and plan 03ie04 was paid for twice ($49.42) because the first lane stranded silently

## Workflow history
- 2026-09-08 created (aw backlog): aw attention is blind to a stranded lane, so unintegrated work is invisible to the one cross-tree view: 11 lanes sat unnoticed and plan 03ie04 was paid for twice ($49.42) because the first lane stranded silently

FOUND 2026-09-08 by the maintainer, after ELEVEN lanes sat unnoticed in `.aw/worktrees/` holding
fully validated, unintegrated work. The maintainer's words: "IT CONSISTENTLY RESULTS IN DOZENS OF
POTENTIALLY LOST WORKSTREAMS."

## The gap

There is NO surface that reports a stranded lane. Measured at HEAD `33cf7bfb`:

- `aw attention` mentions the word "lane" ten times and EVERY occurrence is a plan or backlog TITLE
  containing that word. It reports zero stranded lanes.
- `aw runs --issues` reports directory/status mismatches (`missing_entirely`, `location_mismatch`,
  `status_mismatch`), which describe a plan being in the wrong DIRECTORY. A preserved lane whose plan
  is correctly still in `pending/` is not an "issue" by that definition.
- No verb enumerates `.aw/worktrees/` at all.

So the one question the cross-tree view exists to answer, "what needs attention?", cannot see an
entire class of unfinished work.

## Why this is severe rather than cosmetic

THE DATA IS ALREADY ON DISK AND IS ALREADY CORRECT. This is a missing READER, not a missing record.
Measured on the affected runs' `state.json`: `item["preserved_branch"]`, `item["preserved_worktree"]`,
`item["preserved_lane_id"]`, `item["preserved_disposition"]` and `item["integration_signal"]` are all
written by BOTH drivers. `grep` finds ZERO consumers of `integration_signal` in any reporting module.

MEASURED COST. Plan `03ie04` was executed TWICE because the first lane stranded silently and nobody
noticed: `$16.59` (lane `03ie04`) then `$32.83` (lane `03ie04_attempt2`), `$49.42` for one fix.
Across the eleven stranded lanes recovered on 2026-09-08 the same pattern is the dominant cost. One
lane, `xdr83v_attempt2`, held ZERO commits and zero performed E-items, so a run had produced nothing
at all and reported nothing wrong.

## Relationship to the two existing plans, neither of which closes this

- `32ij2j` (integearn-01, `reviewed`, `Readiness: no-go`) fixes the CAUSE of stranding: the binary
  whole-repo suite gate where one pre-existing red test refuses integration for every lane. It does
  not add any reporting.
- `xtklpd` (integearn-02, `reviewed`, `Readiness: no-go`) fixes the END-OF-RUN report, so a stranded
  run stops printing `Outcome: COMPLETED ... 100%` in green. Its scope is the run summary and
  `aw runs`, NOT `aw attention`.

This item is the THIRD, uncovered surface: the persistent cross-tree view. A run's summary scrolls
past and is seen once; `aw attention` is the durable "what needs attention" answer and is consulted
days later. Even with `xtklpd` landed, a lane stranded last week would still be invisible today.

## What is wanted

1. `aw attention` must report every preserved lane holding unintegrated work as an item needing
   attention, with its lane branch, its worktree path, its `integration_signal`, and the plan id6 it
   belongs to. It must map onto the existing cross-tree class vocabulary (`ready`/`active`/`blocked`/
   `done`/`parked`) rather than inventing a parallel one; a stranded lane is arguably `blocked`.
2. It must be LOUD. The maintainer's requirement is that it SCREAM. A stranded lane is not an
   advisory: it is unintegrated work that will be silently redone at full cost.
3. `aw attention --check` must FAIL CLOSED (nonzero) while any lane is stranded, so CI and any
   agent consuming the view cannot report a clean tree over lost work.
4. It must read the RUN RECORD, not the filesystem. A filesystem-derived verdict rewrites history:
   `xtklpd` measured exactly this, where re-auditing a recovered run today reports it clean because
   the recovery moved the plan. The stranded fact belongs to the run that stranded it.
5. Decide, do not guess, what counts as STRANDED. Candidate predicate: a lane branch with commits not
   reachable from `main`, whose plan is not `executed`. Note a lane may legitimately exist mid-run,
   so a LIVE run's lane must not be reported; `driver.lock` liveness is the existing signal for that.
6. Consider a dedicated verb (`aw lanes`, or `aw runs lanes`) for the detailed list, with `aw
   attention` carrying the alarm. There is no lane-listing verb today, which is why the eleven were
   only found by running `git worktree list` by hand.

## Constraints

- ONE reader, not per-surface copies. `attention_contract` owns the cross-tree class mapping and
  `aw attention` must not grow a second definition of what "needs attention" means.
- Do NOT report a lane belonging to a LIVE run as stranded; that would train operators to ignore the
  alarm, which is the failure mode backlog `gjadwm` records ("a gate that false-positives on correct
  behavior TRAINS agents to bypass it").
- Do NOT delete or auto-merge anything. This item is about VISIBILITY. Recovery is a human act.

## Test

(a) a fixture repo with a lane branch holding commits not in `main` and a non-`executed` plan is
reported by `aw attention`; (b) `aw attention --check` exits nonzero in that state; (c) a lane whose
work IS merged and whose plan IS `executed` is NOT reported; (d) a lane belonging to a run whose
`driver.lock` names a LIVE pid is NOT reported; (e) the `--agent`/`--json` payloads carry the same
fact in a machine-readable field, since an automated consumer reads that path; (f) the reported
detail comes from the run record rather than from a filesystem audit, proven by recovering the lane
and showing the historical run still reports what it did at the time.

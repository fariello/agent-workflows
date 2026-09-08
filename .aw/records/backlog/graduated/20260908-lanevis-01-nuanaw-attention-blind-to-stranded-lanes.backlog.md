- Id: nuanaw
- Status: graduated
- Blocks-Release: next
- Set: lanevis
- Priority: high
- Work-Kind: bug
- Summary: aw attention is blind to a stranded lane, so unintegrated work is invisible to the one cross-tree view: 11 lanes sat unnoticed and plan 03ie04 was paid for twice ($49.42) because the first lane stranded silently

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan pr5b0t (Set lanestrand, .aw/records/plans/pending/20260908-lanestrand-01-pr5b0t-...ipd.md), which carries From-Backlog: nuanaw and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done. NOTHING IS OBSOLETE and the gap was re-measured at HEAD fac69fbd: aw next prints 7 lines containing 'lane' and every one is a plan or backlog TITLE; aw next --check exits 0 ('the view is valid') while 28 aw/lane/* branches exist, including the attempt clusters this item cites (03ie04 + _attempt2, mm6wuz + _attempt2 + _attempt3, nna8yz + _attempt2, xdr83v + _attempt2). Grep counts in attention.py/attention_contract.py: lane 0/0, preserved_ 0/0, integration_signal 0/0, stranded 0/0; the 2 worktree and 1 driver.lock hits are incidental (_resolve_runs_repo_root :1744 climbs to the repo owning .aw/records/runs; get_active_runs_map :1766 inspects LIVE runs only, so a stranded dead run is invisible by construction). SCAN_ROOTS (artifact_core.py:156-172) excludes both .aw/worktrees and .aw/records/runs. BUT THIS ITEM'S MAP OF THE SURROUNDING WORK IS STALE IN THREE WAYS THAT NARROWED THE PLAN, so parts of it became CONSTRAINTS rather than free work. FIRST, both plans it names are now SUPERSEDED, not reviewed: 32ij2j -> daexj1 (commit 32e4b74f) and xtklpd -> ys1dor, both 2026-09-08. The sentence 'Even with xtklpd landed, a lane stranded last week would still be invisible today' should read ys1dor, which HANDS THIS HALF HERE BY NAME: its scope line puts the cross-tree aw attention view OUT and cites nuanaw, its :98 says a lane stranded last week stays invisible with only that plan, its :101 says 'nuanaw covers the attention half', and its OQ-01 defers the machine-readable fail-closed signal TO this item's --check. So asks 2 (loud) and 4 (read the run record) survive but must REUSE ys1dor E-02's outcome word and E-01/E-05's run-record rule rather than invent a parallel vocabulary. SECOND, rl67b0 (integpath-04) E-01 builds exactly the lane RESOLVER and liveness refusal this predicate needs (reconstructing identity from preserved_lane_id/preserved_base/preserved_branch via resolve_prior_lane and worktree_lease.inspect_lane, refusing on owner_live), and its E-02 adds aw <host> integrate <id6>, the REMEDY the alarm must name. rl67b0 reads Readiness: no-go and depends on executed:51vw4y, so it cannot be waited on; the plan designs for convergence (a resolver replaceable by deletion) rather than dependence, and ask 6 (a dedicated aw lanes verb) is DEFERRED for that reason plus the one-reader constraint. THIRD, THIS ITEM'S 'MISSING READER' PREMISE IS INCOMPLETE and the correction shrinks the work: runner_shared._lane_records_from_state (:512), describe_lane (:554), format_lane_report (:585) and build_recovery_lane_notice (:662) ALREADY read the preserved_* fields, and that module's docstring at :515-517 records the written-never-read transition. The true gap is narrower: no REPORTING verb reaches the existing reader. VERIFIED TRUE AS WRITTEN: integration_signal still has ZERO reporting consumers (five occurrences in agent_workflows/, four writes plus one allowlist NAME at lane_containment.py:197), the fields are written by BOTH drivers (oc_runipd.py:6675-6677, :6880-6887; agy_runipd.py:3669-3671, :3863-3870), and there is NO lane-listing verb (the only lanes subcommand is normalize-lanes, cli.py:1035; aw doctor --lanes was designed and RETIRED UNBUILT with superseded 2c122z, as describe_lane's docstring at :558 still records). NO PLAN COVERS ANY PART: 'aw lanes' 0 hits anywhere, lanevis 0 hits; preserved_worktree appears in plans only as Step-0 prose in ys1dor and daexj1. Three pending plans touch the attention modules (m867ox and diof9n declare attention_contract.py, quqyc4 declares attention.py) and none reports lanes, so that is file contention only. 51vw4y E-01 adds a new non-terminal item status (integration-deferred), so a status-keyed predicate must not hardcode today's set. NOT RE-VERIFIABLE FROM A LANE: the $49.42 double payment, the eleven-lane count and xdr83v_attempt2 holding zero commits all need .aw/records/runs/, which is gitignored and absent in a worktree; the corroborating lane BRANCHES do exist, and the plan's E-01 must re-measure all three in the primary checkout before the cost argument is quoted anywhere. Cited HEAD 33cf7bfb is stale (fac69fbd); every substantive claim still holds at the new HEAD.
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

# IPD: Take the graduation baseline from the same commit the lane is cut from

- Date: 2026-10-12
- Kind: child
- Concern: Two of the ten fail-gate items (`2rm0gz`, `iosmvn`) did their job correctly, writing plans that each carried the right `From-Backlog:`, and were still failed with "produced new plan(s) (...) linking a different item or none". The plans named (`jykyqb`, `ml7b9e`, `k6clui`) were not theirs: other runs running at the same time had just merged them into main. The check decides which plans a turn "produced" by comparing the lane's plans after the turn against a list of plans taken BEFORE the turn, and that list missed plans that the lane did contain, so other runs' plans looked new.
- Scope: Compute the pre-turn plan list from the exact commit the lane is cut from, instead of from a separate read of the main checkout, so the comparison is between two states of the same tree and a concurrent merge cannot fall between them. Use the same fix for spec production, which uses the same comparison. No change to which plans count as linked, or to the checks' messages.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_baseline_same_commit.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: gradfix
- Order: 2
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: s95x79

## Workflow history
- 2026-10-12 to-review (aw set): authored to fix the 2026-10-12 fail-gate cluster (Set gradfix)

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A graduation or spec-production turn is judged only on the plans it actually added, regardless of what other runs merge into main while it runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce the mismatch

- [ ] E-01 REPRODUCE on real records. For `iosmvn`: compute the plan id list at commit `c56c5cf0b` (main before `md2o3y` merged) and at `8538be828` (the lane base), and call `production_checks.backlog_graduate_count(<iosmvn lane>, "iosmvn", <list>)` with each. Expected: with the `c56c5cf0b` list it refuses naming `k6clui`; with the `8538be828` list it passes. Do the same for `2rm0gz` with `97959e3fa` (main when its previous item finished) and `1feee61ca` (its lane base): refuses naming `jykyqb, ml7b9e`, then passes. Paste all four results. This proves the failure is the baseline/lane mismatch and nothing about the agent's plans.
  - Depends on: none
  - Expected outcome: two refusals and two passes, pasted.
  - Execution state: pending

- [ ] E-02 FIND WHERE THE LIST GOES STALE, by measurement. The list is built near the top of `runner_shared.execute_item_core` (the `baseline_plan_ids` loop over `_iter_plan_ipds(repo)`), and the lane is allocated later in the same function from `HEAD` (`allocate_isolation_worktree`). In both incidents the list matches main as of the PREVIOUS item's end, not this item's start (`2rm0gz`: previous item finished 03:14:49Z, missing plans merged 03:14:52Z and 03:15:12Z, item started 03:15:15Z; `iosmvn`: previous 03:18:42Z, missing plan merged 03:18:44Z, started 03:19:05Z). Instrument a scripted two-run fixture to confirm which read is stale (the working-tree read, a cached read, or a read taken before a wait), and record the answer in Findings before changing code. The fix in E-03 is correct whichever it is, but the record must say which.
  - Depends on: E-01
  - Expected outcome: a recorded, measured answer to "which read was stale", added to Findings as F-05.
  - Execution state: pending

### Task group 2: fix and prove

- [ ] E-03 Compute the baseline FROM THE LANE'S BASE COMMIT. After the lane is allocated (its `base_commit` is known), build `baseline_plan_ids` and `continued_plan_ids` by listing plan files in that commit (`git ls-tree -r --name-only <base> .aw/records/plans` plus reading each plan's `- Id:` with `git show <base>:<path>`, or by scanning the lane worktree BEFORE the agent turn starts, which holds exactly that commit). Remove the earlier main-checkout read for production items. For a non-isolated run (no lane), take it from `HEAD` immediately before the turn. Spec production uses the same variable and gets the same fix.
  - Depends on: E-02
  - Expected outcome: the baseline and the post-turn scan are two states of the same tree, so a concurrent merge into main cannot appear as a "new plan".
  - Execution state: pending

- [ ] E-04 Add `tests/test_production_baseline_same_commit.py`, driving the real runner backlog-production path with a scripted host in a fixture repo: between the previous item ending and this item starting, a second process merges a commit adding a plan with a DIFFERENT `From-Backlog` into main; the scripted agent then writes one correctly linked plan. Assert the item ends `executed` (not `fail-gate`), the refusal text is absent, and the concurrently merged plan is not reported. Add the matching spec-production case. Both cases must FAIL on the base commit; show it. Run the existing `tests/test_backlog_handoff_close.py` and the production-check tests unchanged, then the bare suite.
  - Depends on: E-03
  - Expected outcome: new module passes and fails on the base commit; existing tests and bare suite pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Cite code by SYMBOL.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | The "unlinked" plans belong to other runs and were merged into main during the gap between items. | `jykyqb` (`From-Backlog: kntbbc`) merged 03:14:52Z by `run-20261012T005617Z-2321742`; `ml7b9e` (`j7daih`) 03:15:12Z and `k6clui` (`md2o3y`) 03:18:44Z by `run-20261012T005641Z-2321995` (main reflog). |
| F-02 | The lanes did contain them, and added only their own plan. | `aw/lane/2rm0gz` base `1feee61ca` contains `jykyqb` and `ml7b9e`; its diff against base is one file (`hdep9j`, `From-Backlog: 2rm0gz`). `aw/lane/iosmvn` base `8538be828` contains `k6clui`; its diff adds five `iosmvn` plans. |
| F-03 | The check reproduces the refusal exactly when the baseline omits those plans, and passes when it is taken at the lane base. | Measured 2026-10-12: `backlog_graduate_count(<iosmvn lane>, "iosmvn", ids@c56c5cf0b)` -> "produced new plan(s) (k6clui) linking a different item"; with `ids@8538be828` -> no finding. |
| F-04 | The baseline and the lane come from two different reads. | `runner_shared.execute_item_core` builds `baseline_plan_ids` from `_iter_plan_ipds(repo)` (the main checkout's files) before allocating the lane from `HEAD`; the post-turn scan reads the lane (`target_tree`). |

## Proposed changes (ordered, validatable)

1. Reproduce (E-01) and pin down the stale read (E-02).
2. Baseline from the lane's base commit (E-03).
3. Concurrent-merge test, both production types (E-04).

## Deferred / out of scope (with reason)

- Serializing runs so nothing merges during an item's start: unnecessary once both reads come from one commit, and it would slow every parallel run.

## Scope check

- Over-scope: none.
- Under-scope: none known. If E-02 shows the stale read lives outside `runner_shared` (for example a cache in `artifact_core`), extend Scope-Paths before changing it and say why.

## Required tests / validation

- `tests/test_production_baseline_same_commit.py` (new), failing on the base commit.
- Existing production-check and handoff tests unchanged and passing.
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

N/A: spec `25kzda` 4.8 defines the checks' pass criteria ("At least one new IPD links to the spec"); this fixes what "new" is measured against and does not change the criteria.

## Open questions

### OQ-01: Read the base commit with git, or scan the lane before the turn?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Either satisfies E-03, since an untouched lane worktree holds exactly its base commit. Scanning the lane before the turn reuses `_iter_plan_ipds` unchanged and is preferred; the executor may choose git reads if E-02 shows the lane can be modified before the scan point. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the four pasted `backlog_graduate_count` results.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the instrumented fixture's output naming which read was stale, and the added F-05 row.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: E-04's concurrent-merge cases passing, produced through the runner's production path with the scripted host.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new module passing, both cases failing on the base commit, the existing tests passing, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit only Scope-Paths files through `aw commit s95x79 -- <paths>`; never push. Paste actual output for every test claim.

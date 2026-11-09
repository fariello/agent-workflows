# IPD: Add the log-only writers and ledger retirement to the cutover code patch

- Date: 2026-11-09
- Kind: child
- Concern: `cxxmyv` E-04 turned on the log-only writers inside the attended cutover turn: retiring the rename ledger and the history-sidecar writers, and removing the INDEX and sidecar ignore lines and scan skip-names from the installer. Like the rest of the code switch, it cannot land on `main` before the one cutover commit (spec `4sd62s` 5.2, C10a), but it can be prepared as part of the inert cumulative code patch that `2k5t16` started (round-3 split, research `nj8zdp`).
- Scope: In a scratch worktree with both cutover patches applied, retire the rename ledger and `record_history` writers, remove the INDEX and sidecar ignore lines from the installer template paths, and remove the INDEX and STATUS skip-name entries; regenerate `.aw/system/cutover/metastore-code.cutover.patch`. No live code changes; this repository's own `.aw/.gitignore`, INDEX files, `STATUS.md` and sidecar are never touched (migration steps 2 and 5 do that).
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-256-g45vyv-add-the-log-only-writers-and-ledger-retirement-to-the-cutove.ipd.md, .aw/system/cutover/metastore-code.cutover.patch
- Item-Dependencies: executed:1ajqaa, executed:87rvs2, executed:90iqr1, executed:aqc3m6, executed:clors0, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:rdg0qv, executed:w13bkp, executed:ya4ee4, executed:zgyna1, executed:2k5t16
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 256
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g45vyv

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from cxxmyv (round 3, research nj8zdp guidance).

## Goal

Extend the cutover code patch so that after the cutover the event logs are the only rename and history record, and a fresh install writes no sidecar or INDEX ignore lines.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create the scratch worktree with the SCRATCH PROCEDURE of `2k5t16` (Step 0): `git worktree add --detach .aw/state/g45vyv/scratch HEAD`, apply the docs patch, record `BASE=$(git write-tree)` in F-01, then `git apply --index .aw/system/cutover/metastore-code.cutover.patch`. If either patch does not apply, stop and report.
  - Depends on: none
  - Expected outcome: the scratch worktree holds HEAD plus both patches, staged.
  - Execution state: pending

### Task group 2: log-only writers (scratch worktree only; was `cxxmyv` E-04, in three steps)

- [ ] E-02 Retire the rename ledger (`xexn45`, AC-31, AC-34), now that `clors0` E-18 already writes path-bearing `rename` events for `aw rename`, `aw group` and `aw archive plans` on log-format records (after the switch every record is log-format, so those events become the only rename record), and retire `record_history.append`, `record_history.append_advisory` and `record_history.append_rename` with their callers.
  - Depends on: E-01
  - Expected outcome: in fixtures, a spec setter, a backlog setter, a rename and a group create no `history.jsonl` and no rename-ledger line, and append the expected events.
  - Execution state: pending

- [ ] E-03 Remove `records/history.jsonl` and the INDEX lines from the `.aw/.gitignore` template in `agent_workflows/engine.py`, from the `engine._ensure_aw_gitignore` adder, and from `agent_workflows/placement_switch.py`. Do NOT edit this repository's own `.aw/.gitignore`.
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` into a temporary repository writes no `records/history.jsonl` or INDEX ignore line.
  - Execution state: pending

- [ ] E-04 Remove the skip-name entries that protected scans from INDEX and STATUS files (`9o83cr` Deferred row). Do NOT delete this repository's on-disk `INDEX.*` files or `plans/STATUS.md`, or move the sidecar: migration steps 2 and 5 do that (`dcerjg` E-06 and E-11); doing it here would un-ignore the sidecar and dirty `.aw/records/`, which the step-1 preflight refuses.
  - Depends on: E-01
  - Expected outcome: `rg` finds no INDEX or STATUS skip-name entry in the scan code of the scratch worktree.
  - Execution state: pending

### Task group 3: package

- [ ] E-05 In the scratch worktree run `git add -A`, write `git diff --cached --binary $BASE` over `.aw/system/cutover/metastore-code.cutover.patch` in the executing checkout, remove the scratch worktree, run `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout, and commit through `aw commit g45vyv -- <this plan> .aw/system/cutover/metastore-code.cutover.patch`; never push.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the regenerated code patch holds the `2k5t16` changes plus this plan's; the guard test passes; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The scratch procedure and the cumulative code patch are defined in `2k5t16` (Step 0, OQ-01).
- The step-1 preflight refuses any uncommitted change under `.aw/records/` (`dcerjg` E-04 condition (2)), so this plan never touches records.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | (written by E-01) | Base tree id (HEAD plus docs patch). |
| F-02 | `rg -n "def append\b\|def append_advisory\|def append_rename" agent_workflows/record_history.py` (2026-11-09) | The three sidecar writers live in `record_history.py`. |

## Proposed changes (ordered, validatable)

1. E-01: scratch worktree with both patches.
2. E-02 to E-04: ledger and writers; ignore lines; skip names.
3. E-05: regenerate the code patch and commit.

## Deferred / out of scope (with reason)

- On-disk deletions of this repository's sidecar, INDEX and STATUS files and its `.aw/.gitignore` lines: migration steps 2 and 5, run by the cutover.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none. `cxxmyv` E-04 maps to E-02 (ledger, `record_history` writers), E-03 (ignore lines) and E-04 (skip names).

## Required tests / validation

- Fixture runs in the scratch worktree (V-02, V-03); the `2k5t16` guard test (V-05).

## Spec / documentation sync

No spec change.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the worktree and both `git apply --index` commands with exit status 0, and F-01.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a fixture test run in the scratch worktree in which a spec setter, a backlog setter, `aw rename` and `aw group` each append the expected event and the fixture has no `records/history.jsonl` afterwards; and `rg -n 'def append\b|def append_advisory|def append_rename' agent_workflows/record_history.py` in the scratch worktree returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a test run showing a fresh `aw install` into a temporary repository writes no `records/history.jsonl` or INDEX ignore line, and `rg -n 'history.jsonl|INDEX' agent_workflows/engine.py agent_workflows/placement_switch.py` in the scratch worktree with each remaining hit classified.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the diff hunk removing the skip-name entries, and `git status --porcelain --ignored -- .aw/.gitignore .aw/records/history.jsonl .aw/records/plans/STATUS.md` in the executing checkout showing them unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-code.cutover.patch`, the `tests/test_metastore_cutover_code_patch.py` run with each test PASSED, `git worktree list` showing the scratch worktree removed, and the `aw commit` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `2k5t16` is `executed` and this plan is `approved`. Code is edited ONLY in the scratch worktree.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output of every command named above; never claim a result you did not run.

Commits: commit only through `aw commit g45vyv -- <paths>`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.

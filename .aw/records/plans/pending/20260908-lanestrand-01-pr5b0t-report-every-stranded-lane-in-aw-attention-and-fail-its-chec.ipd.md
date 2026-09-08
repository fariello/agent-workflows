# IPD: Report every stranded lane in aw attention and fail its check closed so unintegrated work cannot go unnoticed

- Date: 2026-09-08
- Kind: child
- Concern: THE ONE CROSS-TREE "WHAT NEEDS ATTENTION" VIEW CANNOT SEE AN ENTIRE CLASS OF UNFINISHED WORK. Eleven lanes sat unnoticed in `.aw/worktrees/` holding fully validated, unintegrated work, and `aw attention` reported nothing. Re-measured in this lane at HEAD `fac69fbd`: `aw next` prints 7 lines containing the word "lane" and EVERY ONE is a plan or backlog TITLE; `aw next --check` exits 0 ("the view is valid") while 28 `aw/lane/*` branches exist, including the attempt-scoped clusters that record the damage (`aw/lane/03ie04` plus `03ie04_attempt2`, `mm6wuz` plus `_attempt2` plus `_attempt3`, `nna8yz` plus `_attempt2`, `xdr83v` plus `_attempt2`).
  THIS IS A MISSING READER, NOT A MISSING RECORD, WHICH IS WHY IT IS WORTH BUILDING RATHER THAN DESIGNING. The facts are already on disk and already correct, written by BOTH drivers: `preserved_worktree` (`oc_runipd.py:6880`, `agy_runipd.py:3863`), `preserved_branch` (`:6881`, `:3864`), `preserved_lane_id` (`:6885`, `:3868`), `preserved_disposition` (`:6887`, `:3870`), and `integration_signal` (`:6675`/`:6677`, `:3669`/`:3671`). And `integration_signal` has ZERO reporting consumers: exhaustively, its only five occurrences in `agent_workflows/` are those four writes plus one NAME in `lane_containment.py`'s `_PRIOR_ATTEMPT_SAFE_KEYS` allowlist (`:197`), which permits the field to be echoed into a recovery prompt and is not a report.
  THE ATTENTION MODULES CONTAIN NOTHING ABOUT LANES. Grep counts in `attention.py` and `attention_contract.py`: `lane` 0/0, `preserved_` 0/0, `integration_signal` 0/0, `stranded` 0/0; `worktree` 2/0 and `driver.lock` 1/0, all three incidental (`_resolve_runs_repo_root` `attention.py:1744` uses `".aw/worktrees" in str(...)` at `:1759` only to climb to the repo owning `.aw/records/runs`, and `get_active_runs_map` `:1766` inspects LIVE runs only, so a stranded dead run is invisible by construction). The scan set is `SCAN_ROOTS` (`artifact_core.py:156-172`), which excludes both `.aw/worktrees` and `.aw/records/runs`.
  MEASURED COST, and it is paid in dollars and in redone work. Plan `03ie04` was executed TWICE because the first lane stranded silently: `$16.59` then `$32.83`, `$49.42` for one fix. One lane, `xdr83v_attempt2`, held ZERO commits and zero performed E-items, so a run produced nothing and reported nothing wrong. The maintainer's framing: "IT CONSISTENTLY RESULTS IN DOZENS OF POTENTIALLY LOST WORKSTREAMS."
- Scope: Give `aw attention` a lane-visibility surface: report every stranded lane as an item needing attention with its branch, worktree path, `integration_signal` and plan id6, mapped onto the existing class vocabulary, carried in the `--agent`/`--json` payloads, and make `aw attention --check` exit nonzero while any lane is stranded. EXCLUDES the CAUSE of stranding (`daexj1` owns the suite gate); EXCLUDES the end-of-run report (`ys1dor` owns it, and this plan REUSES its vocabulary rather than choosing a second one); EXCLUDES any recovery, merge, or deletion action (`rl67b0` owns `aw integrate`); and EXCLUDES a new `aw lanes` verb, deferred with reasons.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, agent_workflows/runner_shared.py, tests/test_attention.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Set: lanestrand
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pr5b0t
- From-Backlog: nuanaw
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nuanaw`. NOTHING IN THE ITEM IS OBSOLETE; the gap is intact and re-measured at HEAD `fac69fbd` (`aw next --check` exits 0 with 28 lane branches present; zero lane tokens in either attention module). BUT THE ITEM'S MAP OF THE SURROUNDING WORK IS STALE IN A WAY THAT CHANGES THE DESIGN, so three parts of it become CONSTRAINTS rather than free work. FIRST, both plans the item names are now SUPERSEDED, not `reviewed`: `32ij2j` -> `daexj1`, `xtklpd` -> `ys1dor` (both moved 2026-09-08, `32ij2j` by commit `32e4b74f`). The item's sentence "Even with `xtklpd` landed, a lane stranded last week would still be invisible today" should read `ys1dor`, which is also the plan that HANDS THIS HALF TO THIS ITEM BY NAME: `ys1dor`'s scope line says "OUT: ... the cross-tree `aw attention` view (backlog `nuanaw`)", its line 98 says "a lane stranded last week would still be invisible with only this plan landed", its line 101 says "`nuanaw` covers the attention half", and its OQ-01 defers the machine-readable fail-closed signal TO this plan's `--check`. So asks 2 and 4 are not dead but must REUSE `ys1dor` E-02's outcome word and E-01/E-05's run-record rule instead of inventing a parallel vocabulary. SECOND, `rl67b0` (`integpath-04`) E-01 builds exactly the lane RESOLVER and liveness refusal this plan's predicate needs (reconstructing identity from `preserved_lane_id`/`preserved_base`/`preserved_branch` via `resolve_prior_lane` and `worktree_lease.inspect_lane`, refusing on `owner_live`), and its E-02 adds `aw <host> integrate <id6>`, which is the REMEDY this alarm must name. `rl67b0` currently reads `Readiness: no-go`, so it is not runnable today, which is why E-02 here makes the shared reader work with or without it. THIRD, the item's premise "This is a missing READER" is INCOMPLETE and the correction makes the plan smaller: `runner_shared._lane_records_from_state` (`:512`), `describe_lane` (`:554`), `format_lane_report` (`:585`) and `build_recovery_lane_notice` (`:662`) ALREADY read the `preserved_*` fields, and that module's own docstring at `:515-517` records the transition from written-never-read to read. The true gap is narrower: "no REPORTING verb reaches the existing reader". NO PLAN COVERS ANY PART: `aw lanes` 0 hits anywhere, `lanevis` 0 hits, `preserved_worktree` appears in plans only as Step-0 prose in `ys1dor` and `daexj1`. Three pending plans DO touch the attention modules (`m867ox` and `diof9n` declare `attention_contract.py`, `quqyc4` declares `attention.py`) and none reports lanes, so they are file-contention only. UNVERIFIABLE FROM A LANE, stated rather than repeated as fact: the `$49.42` figure, the eleven-lane count and the `xdr83v_attempt2` zero-commit claim all need `.aw/records/runs/`, which is gitignored and absent in a worktree; the corroborating lane BRANCHES do exist. E-01 must re-measure them in the primary checkout before this plan's cost argument is quoted anywhere.

## Goal

Make unintegrated work impossible to lose silently, by teaching the one durable cross-tree view to read the stranded-lane facts both drivers already record, and by making its `--check` refuse to call a tree clean while that work sits unmerged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: decide the predicate before reporting anything

- [ ] E-01 DEFINE AND RECORD THE STRANDED PREDICATE, from the RUN RECORD, and re-measure the item's cost claims in the primary checkout while you are there. The item's candidate is "a lane branch with commits not reachable from `main`, whose plan is not `executed`", and it explicitly says DECIDE, DO NOT GUESS.
  START FROM THE FACTS ALREADY WRITTEN, not from the filesystem. Every input exists on the run record: `preserved_branch`, `preserved_worktree`, `preserved_lane_id`, `preserved_disposition`, `integration_signal`, `integration_detail`. Enumerate for each what it can and cannot decide, and write the predicate as a function of those fields plus at most one git reachability question.
  A LIVE RUN'S LANE MUST NOT BE REPORTED. This is the single most important exclusion and the item names why: a gate that false-positives on correct behavior TRAINS operators to ignore it (the failure mode backlog `gjadwm` records). The existing liveness signal is `driver.lock` holder liveness, already consumed by `attention.get_active_runs_map` (`attention.py:1766`, docstring `:1769`: "Only live runs (whose driver process currently holds driver.lock) are inspected") and by `runner_shared.describe_lane`'s `owner_live`/`owned_by_other_live_process` outputs (`:564-582`). Use one of those; do not invent a third liveness test.
  A RECOVERED LANE MUST NOT BE REPORTED. `aw/lane/xxxxxx` whose commits are merged and whose plan is `executed` is finished; reporting it is the same false positive in the other direction.
  DECIDE WHAT AN UNKNOWN IS. A lane branch that no longer exists, a run record naming a worktree path that is gone, or a git question that cannot be answered must resolve to a STATED UNKNOWN that stays VISIBLE, never to a silent OK. This is the same ruling that shaped `1f9m2j`/`zexed1`: do not print a green verdict the data does not support.
  RE-MEASURE THE COST CLAIMS. In the primary checkout (where `.aw/records/runs/` exists), verify the `$16.59` plus `$32.83` double payment for `03ie04`, the eleven-lane count, and `xdr83v_attempt2` holding zero commits. Paste what you find. If a figure does not reproduce, correct it here rather than propagating it.
  - Depends on: none
  - Expected outcome: a written predicate expressed over named run-record fields plus at most one git question, with the live-run exclusion, the recovered-lane exclusion and the UNKNOWN case each stated, and the three cost claims re-measured with output pasted.
  - Execution state: pending

### Task group 2: one reader, in the module that already owns lane facts

- [ ] E-02 IMPLEMENT THE PREDICATE ONCE, IN `runner_shared.py`, BESIDE THE EXISTING LANE READERS, and do not put it in `attention.py`. The reason is the item's own hard constraint ("ONE reader, not per-surface copies") and the fact that `runner_shared` already holds the whole lane vocabulary: `_lane_records_from_state` (`:512`) reads the `preserved_*` fields, `describe_lane` (`:554`) returns `state`/`commits_ahead`/`dirty`/`head`/`base_sha`/`holds_work`/`owner_live`/`owned_by_other_live_process`, `format_lane_report` (`:585`) and `build_recovery_lane_notice` (`:662`) render them.
  BUILD ON `describe_lane`, DO NOT REIMPLEMENT IT. It already answers `commits_ahead`, `holds_work` and `owner_live`, which is most of E-01's predicate. A second implementation is the exact duplication the item forbids.
  THE FUNCTION MUST BE PURE ENOUGH TO TEST: given a repo root and a run record (or an iterable of them), return structured lane records. No printing, no exit codes, no argparse. The rendering belongs to the consumer, and there will be more than one consumer.
  DO NOT DEPEND ON `rl67b0` LANDING FIRST. Its E-01 builds a re-integration entry point with an overlapping resolver, and it currently reads `Readiness: no-go` so it may not land soon. Write this reader so that if `rl67b0` lands, ITS resolver can be adopted by deletion of the local one rather than by a rewrite; record the intended convergence point explicitly in the docstring so neither plan silently forks a second lane resolver.
  - Depends on: E-01
  - Expected outcome: one host-neutral function in `runner_shared.py` returning structured stranded-lane records, built on `describe_lane`, with no printing and no exit codes, and a docstring naming the convergence point with `rl67b0`'s resolver.
  - Execution state: pending

- [ ] E-03 MAP A STRANDED LANE ONTO THE EXISTING CLASS VOCABULARY IN `attention_contract.py`, and do not invent a parallel one. The authority is `class_of(tree, native_status)` (`:343`) over the per-tree fragments in `CLASS_MAPS` (`:329`), with classes `READY/ACTIVE/BLOCKED/DONE/PARKED` (`:47-53`).
  THE ITEM PROPOSES `blocked` AND THAT IS DEFENSIBLE: a stranded lane cannot proceed without a human act. Adopt it unless E-01's predicate produces a state that genuinely is not blocked (a lane whose work IS merged but whose plan is not yet `executed`, for instance, is arguably `active`). Record the mapping and its reasoning.
  RESPECT THE FAIL-CLOSED SHAPE ALREADY THERE. An unmapped native status raises `UnknownNativeStatus` (`:338`) and the scanner renders it as a VIOLATION rather than defaulting to a class. Whatever fragment or synthetic type you add must keep that property: a lane state nobody mapped must be loud, not silently `ready`.
  MIND THAT `scan()` IS FILE-SHAPED. `attention.scan` (`:325`) is built entirely around `artifact_core.iter_scan_files` (`artifact_core.py:293`) and per-file `_record_for` (`attention.py:781`), so there is no existing route for a non-file-backed item. Choose deliberately between a sixth `CLASS_MAPS` fragment for a synthetic `lanes` tree and a separate lane section joined at render time, and record WHY. Do NOT add `.aw/worktrees` to `SCAN_ROOTS`: the item's ask 4 is explicit that the verdict comes from the run record, and a filesystem walk would rewrite history exactly as `xtklpd`'s review measured.
  - Depends on: E-02
  - Expected outcome: a recorded mapping decision placing a stranded lane in an existing class, the unmapped-state-is-a-violation property preserved, a recorded choice between synthetic tree and render-time join with its reasoning, and `SCAN_ROOTS` unchanged.
  - Execution state: pending

### Task group 3: make it loud, machine-readable, and fail-closed

- [ ] E-04 REPORT EVERY STRANDED LANE IN `aw attention`, LOUDLY, carrying the four facts the item names: the lane branch, the worktree path, the `integration_signal`, and the plan id6 it belongs to. Add the REMEDY too, because an alarm with no route trains its own dismissal.
  REUSE `ys1dor`'s VOCABULARY, DO NOT CHOOSE A SECOND ONE. Its E-02 picks the screaming red outcome word for a stranded run (`STRANDED`/`NOT LANDED`) and its E-03 renders the recovery route naming `preserved_branch` and `integration_detail`. If `ys1dor` has landed, use its word and its route shape verbatim. If it has NOT landed, pick one and say in the plan record which word you chose, so `ys1dor` can converge on it rather than the reverse; two different words for one condition across two surfaces is worse than either word.
  NAME THE REMEDY THAT EXISTS TODAY. `rl67b0` would add `aw <host> integrate <id6>`; until it lands, the honest remedy is the manual one. Print the route that actually works at the time, and do not print a verb that does not exist.
  DO NOT DELETE, MERGE, OR AUTO-RECOVER ANYTHING. The item is explicit: this is about VISIBILITY, and recovery is a human act.
  - Depends on: E-03
  - Expected outcome: `aw attention` reports each stranded lane with branch, worktree path, `integration_signal` and plan id6, in the loud style, naming a remedy that exists, with `ys1dor`'s word reused or the chosen word recorded for convergence, and no mutating action anywhere.
  - Execution state: pending

- [ ] E-05 CARRY THE SAME FACT IN THE `--agent` AND `--json` PAYLOADS, in a machine-readable field, because an automated consumer reads that path and a human-only alarm is invisible to every agent that consults the view. `render_json` is at `attention.py:1069`.
  ADD A FIELD, DO NOT REPURPOSE ONE. An existing consumer parsing the payload must not break; the item's own test (e) demands the same fact reach the machine path.
  KEEP THE VALIDITY FLAG HONEST. The payload already carries a validity notion (`aw attention --check`'s "the view is valid"); a payload that reports `valid: true` alongside a stranded lane would be self-contradictory. Decide and record how the two interact, consistently with E-06.
  - Depends on: E-04
  - Expected outcome: `--agent` and `--json` payloads carry the stranded-lane records in a NEW field with existing fields unchanged, and a recorded, consistent relationship to the payload's validity flag.
  - Execution state: pending

- [ ] E-06 MAKE `aw attention --check` EXIT NONZERO WHILE ANY LANE IS STRANDED, so CI and any agent consuming the view cannot report a clean tree over lost work. Today it exits 0 in exactly this state (measured: exit 0 with 28 lane branches present); the check path is `attention.run` (`:2455`) with the valid message at `:2496`/`:2714`.
  THIS IS THE HALF `ys1dor` DEFERRED TO THIS PLAN. Its OQ-01 declines to change a RUN's exit contract partly because "backlog `nuanaw` asks for `aw attention --check` to fail closed on a stranded lane, which gives automation a fail-closed signal without touching the run's exit contract". So this E-item is load-bearing for another plan's recorded decision and must not be quietly dropped to advisory.
  DISTINGUISH THE UNKNOWN FROM THE STRANDED when deciding the code. E-01 requires an UNKNOWN state; whether an unanswerable git question should fail the check or merely warn is a real decision. Fail-closed is the safer default and matches the item's ask 3; if you choose otherwise, record why.
  DO NOT LET A LIVE RUN FAIL THE CHECK. A driver run in progress legitimately owns a lane, and a `--check` that reds during every normal run is a check that gets bypassed.
  - Depends on: E-05
  - Expected outcome: `--check` exits nonzero with a stranded lane and 0 without one, a live run's lane never causing a failure, and a recorded decision on whether an UNKNOWN fails or warns.
  - Execution state: pending

### Task group 4: prove both directions on fixtures

- [ ] E-07 PROVE THE PREDICATE ON FIXTURES, INCLUDING EVERY CASE THAT MUST **NOT** FIRE, since a false positive here destroys the alarm's value. The item's test list is the minimum: (a) a fixture repo with a lane branch holding commits not in `main` and a non-`executed` plan IS reported; (b) `--check` exits nonzero in that state; (c) a lane whose work IS merged and whose plan IS `executed` is NOT reported; (d) a lane belonging to a run whose `driver.lock` names a LIVE pid is NOT reported; (e) the `--agent`/`--json` payloads carry the same fact; (f) the reported detail comes from the run record rather than a filesystem audit.
  TEST (f) IS THE HARD ONE AND MUST BE DONE AS THE ITEM SPECIFIES: recover the lane, then show the HISTORICAL run still reports what it did at the time. A filesystem-derived verdict rewrites history, which is precisely what `xtklpd`'s review measured when re-auditing a recovered run reported it clean because the recovery had moved the plan.
  ADD A SEVENTH CASE THE ITEM DOES NOT LIST: the UNKNOWN. A run record naming a branch or worktree that no longer exists must produce a visible UNKNOWN row, not a silent pass.
  FIXTURES ONLY. Do NOT read, mutate, prune or merge any real lane: this repo currently holds 28 `aw/lane/*` branches and several live runs, and three agents are graduating concurrently. A test that touches a real lane could destroy exactly the unintegrated work this plan exists to protect. Build synthetic run records and synthetic branches in a throwaway repo, the way `tests/test_runner_shared.py` already builds repo fixtures.
  - Depends on: E-06
  - Expected outcome: seven fixture cases passing (the item's six plus UNKNOWN), with the recovered-lane historical-report case done by actually recovering a fixture lane, and no real lane read or modified.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE DATA IS ALREADY WRITTEN BY BOTH DRIVERS. `preserved_worktree`/`preserved_branch`/`preserved_lane_id`/`preserved_disposition` at `oc_runipd.py:6880-6887` and `agy_runipd.py:3863-3870`; `integration_signal`/`integration_detail` at `oc_runipd.py:6675-6677` and `agy_runipd.py:3669-3671`. This is a reader problem.
- AND A LANE READER ALREADY EXISTS, WHICH THE ITEM DID NOT KNOW. `runner_shared._lane_records_from_state` (`:512`), `describe_lane` (`:554`), `format_lane_report` (`:585`), `build_recovery_lane_notice` (`:662`). The module docstring at `:515-517` records that `preserved_worktree`/`preserved_branch` were "previously WRITTEN and never READ anywhere in the package; this is the consumer that makes them meaningful." Build on it.
- `integration_signal` STILL HAS ZERO REPORTING CONSUMERS. Its five occurrences are four writes plus one allowlist NAME in `lane_containment.py:197`.
- `aw attention`'s CLASS MAPPING IS ONE PURE FUNCTION. `class_of` (`attention_contract.py:343`) over `CLASS_MAPS` (`:329`), classes at `:47-53`, and an unmapped status raises `UnknownNativeStatus` (`:338`) rendered as a violation rather than defaulted. Extend it; do not add a second definition of what needs attention.
- `scan()` IS FILE-SHAPED. `attention.scan` (`:325`) walks `artifact_core.iter_scan_files` (`artifact_core.py:293`) over `SCAN_ROOTS` (`:156-172`), which excludes `.aw/worktrees` and `.aw/records/runs`. A non-file item has no existing route, so the join point is a deliberate choice.
- LIVENESS ALREADY HAS A SIGNAL, TWICE. `attention.get_active_runs_map` (`:1766`) inspects only runs holding `driver.lock`; `runner_shared.describe_lane` returns `owner_live` and `owned_by_other_live_process`. Do not invent a third.
- THERE IS NO LANE-LISTING VERB. The only `lanes` subcommand is `normalize-lanes` (`cli.py:1035`, dispatch `:10865`), which renames comms quarantine lanes and is unrelated. `aw runs` leaves are `decisions, evidence, list, next, questions, resume, show, status, verify-ledger`. `aw doctor --lanes` was DESIGNED AND RETIRED UNBUILT with `2c122z` (superseded), a fact `describe_lane`'s own docstring at `:558` still cites.
- `ys1dor` OWNS THE VOCABULARY FOR THIS CONDITION and hands the attention half here by name (its scope line, `:98`, `:101`, and OQ-01). Reuse its word; do not choose a second one.
- `rl67b0` OWNS THE REMEDY (`aw <host> integrate <id6>`) and an overlapping lane resolver, but reads `Readiness: no-go` today. Design for convergence, not dependence.
- `51vw4y` E-01 ADDS A NEW NON-TERMINAL ITEM STATUS (`integration-deferred`), so any predicate keyed on item status must read the runner's own vocabulary rather than hardcode today's set.
- FILE CONTENTION ON THE ATTENTION MODULES: `m867ox` and `diof9n` declare `attention_contract.py`, `quqyc4` declares `attention.py`. None reports lanes.
- Shared checkout, 28 live lane branches, concurrent graduations. Fixtures only, and the suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the view is blind, re-measured | `aw next` prints 7 lines containing "lane", all plan/backlog TITLES; `aw next --check` exits 0 while 28 `aw/lane/*` branches exist. | measured in this lane at HEAD `fac69fbd` |
| F-2 | HIGH | zero lane awareness in either module | `attention.py`/`attention_contract.py` grep counts: `lane` 0/0, `preserved_` 0/0, `integration_signal` 0/0, `stranded` 0/0. The 2 `worktree` and 1 `driver.lock` hits are incidental. | `attention.py:1744`, `:1759`, `:1766`, `:1769` |
| F-3 | HIGH | the scan set cannot see lanes by construction | `SCAN_ROOTS` excludes `.aw/worktrees` and `.aw/records/runs`; `scan()` is built on per-file records. | `artifact_core.py:156-172`, `:293`; `attention.py:325`, `:781` |
| F-4 | HIGH | the facts exist on both hosts | Seven write sites for the five fields, one pair per host. | `oc_runipd.py:6675-6677`, `:6880-6887`; `agy_runipd.py:3669-3671`, `:3863-3870` |
| F-5 | HIGH | and `integration_signal` is read by nobody who reports | Five occurrences: four writes plus one allowlist name. | `lane_containment.py:197` |
| F-6 | MEDIUM | **the item's "missing reader" premise is incomplete, and that shrinks the work** | `runner_shared` already reads the `preserved_*` fields in four functions, and its docstring records the written-never-read transition. The true gap is that no REPORTING verb reaches that reader. | `runner_shared.py:512`, `:515-517`, `:554`, `:585`, `:662` |
| F-7 | MEDIUM | both plans the item cites are now SUPERSEDED | `32ij2j` -> `daexj1` (commit `32e4b74f`), `xtklpd` -> `ys1dor`, both 2026-09-08. Neither closes anything; the item's "even with `xtklpd` landed" should read `ys1dor`. | `.aw/records/plans/superseded/...32ij2j...`, `...xtklpd...` |
| F-8 | MEDIUM | `ys1dor` hands this half here BY NAME | Its scope line puts the `aw attention` view OUT and cites `nuanaw`; `:98` says a lane stranded last week stays invisible with only that plan; `:101` says "`nuanaw` covers the attention half"; OQ-01 defers the fail-closed signal to this `--check`. | `ys1dor` scope, `:98`, `:101`, OQ-01 |
| F-9 | MEDIUM | `rl67b0` builds the resolver and the remedy, but is not runnable | E-01 reconstructs lane identity from the run record and refuses on `owner_live`; E-02 adds `aw <host> integrate <id6>`. It reads `Readiness: no-go` and depends on `executed:51vw4y`. It enumerates nothing and never touches attention (0 hits). | `rl67b0` metadata, E-01, E-02 |
| F-10 | MEDIUM | no lane-listing verb, and one was retired unbuilt | Only `normalize-lanes` exists; `aw doctor --lanes` was designed and retired with superseded `2c122z`, as `describe_lane`'s docstring still records. | `cli.py:1035`, `:10865`; `runner_shared.py:558` |
| F-11 | MEDIUM | a filesystem-derived verdict rewrites history | `xtklpd`'s review measured that deriving a verdict from a live-filesystem audit reports a recovered run clean today. That ruling is why ask 4 exists and why `SCAN_ROOTS` must not grow `.aw/worktrees`. | `xtklpd:26` |
| F-12 | LOW | a new item status is arriving | `51vw4y` E-01 adds `integration-deferred` as non-terminal, so a status-keyed predicate must not hardcode today's set. | `51vw4y` E-01 |
| F-13 | LOW | attention-module contention | `m867ox`, `diof9n` declare `attention_contract.py`; `quqyc4` declares `attention.py`. None reports lanes. | those plans' `Scope-Paths` |
| F-14 | LOW | the cost figures are unverified from a lane | `$49.42`, the eleven-lane count and `xdr83v_attempt2`'s zero commits need `.aw/records/runs/`, gitignored and absent in a worktree. The corroborating branches exist. E-01 must re-measure. | `.aw/.gitignore` `records/runs/`; `git branch --list 'aw/lane/*'` |

## Proposed changes (ordered, validatable)

1. Decide and record the stranded predicate over named run-record fields, with live-run, recovered-lane and UNKNOWN cases, and re-measure the cost claims (E-01).
2. Implement it ONCE in `runner_shared.py` on top of `describe_lane`, pure and printless (E-02).
3. Map a stranded lane onto an existing attention class, keeping unmapped-is-a-violation and leaving `SCAN_ROOTS` alone (E-03).
4. Report each stranded lane loudly with its four facts and an existing remedy, reusing `ys1dor`'s word (E-04).
5. Carry the same fact in `--agent`/`--json` in a new field, consistent with the validity flag (E-05).
6. Make `--check` fail closed on a stranded lane and never on a live run's lane (E-06).
7. Prove seven fixture cases including the recovered-lane historical report and the UNKNOWN, touching no real lane (E-07).

## Deferred / out of scope (with reason)

- THE CAUSE OF STRANDING. `daexj1` (`integearn-03`) fixes the binary whole-repo suite gate where one pre-existing red test refuses integration for every lane. This plan reports the effect, which will keep occurring for other causes, so the two are independent and neither blocks the other.
- THE END-OF-RUN REPORT. `ys1dor` (`integearn-04`) makes a stranded run stop printing a green `COMPLETED`. Its scope is `render_stream.py`; this plan does not touch it, and REUSES its vocabulary rather than duplicating its surface.
- ANY RECOVERY, MERGE, OR DELETION. The item is explicit that recovery is a human act. `rl67b0` (`integpath-04`) owns `aw <host> integrate <id6>`. This plan prints a route and performs nothing.
- A DEDICATED `aw lanes` VERB (the item's ask 6). Deferred deliberately, with two reasons rather than as an oversight. FIRST, `rl67b0` E-02 is adding `aw <host> integrate <id6>` with its own lane resolver, so the natural home for a LISTING is beside that verb (or as its dry-run), and building a separate `aw lanes` now would create the second lane resolver this plan's own "one reader" constraint forbids. SECOND, the alarm plus `--check` closes the loss-of-work hazard, which is the item's actual cost; a browsing verb is convenience. If a maintainer wants it anyway, it is a thin consumer of E-02's function and should be filed as a follow-up.
- ADDING `.aw/worktrees` TO `SCAN_ROOTS`. Refused on the item's ask 4 and on `xtklpd`'s measured ruling (F-11): a filesystem-derived verdict rewrites history.
- THE ELEVEN STRANDED LANES THEMSELVES, and the 28 live `aw/lane/*` branches. This plan does not prune, merge, audit or touch any of them; several belong to live or recent runs and three agents are graduating concurrently. If E-01's measurement finds a lane holding unintegrated work, REPORT it to the maintainer; do not recover it inside this plan.
- CHANGING A RUN's EXIT CONTRACT. `ys1dor` OQ-01 deliberately left that alone and pointed at this plan's `--check` instead. Honor that division.
- THE `interrupted`-VS-`approved` AND `integration-blocked`-VS-`executed` DISCREPANCY ROWS in `aw runs`. Different surface, owned by `vdabn5` and `zexed1` (from backlog `1f9m2j`).

## Scope check

- Over-scope: none. One predicate, one reader function, one class mapping, one report section, one payload field, one exit code, one fixture suite.
- Scope-Paths justification: `agent_workflows/attention_contract.py` holds `class_of` (`:343`), `CLASS_MAPS` (`:329`), the class constants (`:47-53`) and `UnknownNativeStatus` (`:338`) that E-03 must extend without weakening; `agent_workflows/attention.py` holds `scan` (`:325`), `render_json` (`:1069`), `run` (`:2455`) and the valid-view message (`:2496`, `:2714`) that E-04/E-05/E-06 change, plus `get_active_runs_map` (`:1766`) whose liveness signal E-01 reuses; `agent_workflows/runner_shared.py` holds the existing lane readers (`:512`, `:554`, `:585`, `:662`) that E-02 builds on so the predicate lives with the lane vocabulary rather than in the view; `tests/test_attention.py` and `tests/test_runner_shared.py` are the two suites whose fixtures E-07 extends, split the same way the code is.
- Under-scope, stated rather than left as `none`: this plan builds no `aw lanes` verb, performs no recovery or merge, changes no gate, changes no run exit code, does not extend `SCAN_ROOTS`, does not touch the `aw runs` discrepancy table, does not read or modify any real lane, and writes no spec (see the sync section for why, and for the one contract question it raises).

## Required tests / validation

- SEVEN FIXTURE CASES (E-07), each named and each output pasted: reported-when-stranded; `--check` nonzero; merged-and-executed NOT reported; live-`driver.lock` lane NOT reported; payload carries the fact; historical report survives recovery; UNKNOWN visible.
- THE HISTORICAL-REPORT CASE DONE BY ACTUAL RECOVERY of a fixture lane, not by assertion, since that is the property `xtklpd`'s review found violated by a filesystem audit.
- BEFORE AND AFTER `aw attention --check` EXIT CODES, measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`): 0 at HEAD in a stranded-lane fixture, nonzero after. Both pasted.
- THE LOUD OUTPUT PASTED VERBATIM, showing the branch, worktree path, `integration_signal` and plan id6 on one row, plus the remedy string, so a reviewer can judge whether it screams.
- THE `--agent` AND `--json` PAYLOADS pasted before and after, showing the NEW field and showing existing fields byte-unchanged.
- ONE-READER PROOF: show by object identity or by grep that the stranded predicate exists in exactly one place and that `attention.py` calls it rather than reimplementing it.
- VOCABULARY PROOF: paste the outcome word used and state whether it was taken from `ys1dor` (landed) or chosen for convergence (not landed).
- NEGATIVE PROOF THAT NO REAL LANE WAS TOUCHED: `git branch --list 'aw/lane/*' | wc -l` and `git worktree list` before and after, identical, plus `git status --porcelain` clean of unexpected paths.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated explicitly. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Inside a lane worktree roughly 32 failures are environmental because several tests read live repo state; say so and judge on the delta.
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean. NOTE: this plan's output includes WORKTREE PATHS, which are machine-local absolute paths, so the sanitizer matters more here than usual. Check that the new report and payload cannot leak a maintainer path into a tracked artifact or a shared payload, and record what you found.

## Spec / documentation sync

NO SPEC FILE IS DECLARED IN `Scope-Paths`, and that is a deliberate, contestable choice a reviewer should check.

THE CASE FOR NO SPEC CHANGE: the attention contract's authority is CODE (`attention_contract.class_of` and `CLASS_MAPS`), and this plan extends that mapping the same way `m867ox` extends the scanned trees. The attention spec (`.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`) describes the cross-tree view over TRACKED RECORD TREES, and a lane is not a record tree.

THE CASE A REVIEWER MIGHT MAKE AGAINST IT: making `aw attention --check` FAIL on something that is not a tracked artifact changes what the check MEANS, and `--check` is consumed by CI and by agents. If the maintainer holds that the check's contract is spec-governed, then this plan must declare and amend that spec, per the "a plan may amend a spec, and must declare it" rule. E-06 should surface this explicitly rather than assume: if the spec constrains `--check`'s failure conditions, STOP and add the spec path to `Scope-Paths` before changing the exit code.

DOCUMENTATION THAT MUST CHANGE EITHER WAY: `aw attention`'s own help text should say that it reports stranded lanes and that `--check` fails on them, because an operator cannot infer a new failure condition from silence. This is operator-facing prose: write no em or en dashes.

`runner_shared`'s NEW FUNCTION MUST CARRY THE CONVERGENCE NOTE from E-02, naming `rl67b0`'s resolver as the intended merge point, so the next reader does not fork a second lane resolver. That module already uses its docstrings this way (`:515-517`, `:558`), so follow the local habit.

## Open questions

### OQ-01: Is a stranded lane `blocked`, or does it need a class of its own?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS `blocked`, WITH ONE STATED EXCEPTION FOR E-03 TO HANDLE. The item proposes `blocked` and the vocabulary supports it: a stranded lane cannot proceed without a human act, which is what `blocked` means everywhere else in the view. Inventing a sixth class is refused because the item's own hard constraint is that `attention_contract` must not grow a second definition of what needs attention, and because every consumer of the class vocabulary (renderers, the board, the JSON payload) would need teaching. THE EXCEPTION: E-01's predicate may yield a lane whose work IS merged but whose plan is not yet `executed`, which is not blocked but mid-flight, and `active` fits it better. E-03 must therefore record a mapping per predicate outcome, not one blanket class. This is resolved rather than open because the default is decided and the one ambiguous case has an owner.

### OQ-02: Does `--check` failing on a lane change a spec-governed contract?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE IT IS A CONTRACT QUESTION, NOT A CODE QUESTION, and getting it wrong in either direction is costly. `aw attention --check` is consumed by CI and by agents as "the view is valid"; adding a new FAILURE condition to it is either (a) a natural consequence of the view learning about a new kind of unfinished work, needing no spec change, or (b) a change to what a documented check asserts, which the "a plan may amend a spec, and must declare it" rule says must be declared in `Scope-Paths` and justified. This plan takes position (a) and says so in the sync section, but E-06 is instructed to STOP and add the spec path if it finds the attention spec constraining `--check`'s failure conditions. Non-blocking because the reporting half (E-04, E-05) delivers value under either answer; only the exit code hinges on it.

### OQ-03: Should this plan wait for `ys1dor` and `rl67b0`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THE REASONS ARE ASYMMETRIC PER PLAN. `ys1dor` is a SOFT precedence: it lands the first `integration_signal` reader, picks the red outcome word, and its OQ-01 defers the fail-closed signal to this plan's `--check`, so if it lands first this plan simply reuses its word. If it does NOT land first, E-04 picks a word and records it for `ys1dor` to converge on, which is a smaller cost than blocking. `rl67b0` cannot be waited on at all: it reads `Readiness: no-go` and depends on `executed:51vw4y`, which itself depends on `executed:6sb3yu`, so the chain is `51vw4y` -> `rl67b0`, and gating a release-blocking visibility fix behind a no-go plan would leave the loss-of-work hazard open indefinitely. E-02 therefore designs for CONVERGENCE (a resolver that can be replaced by deletion) rather than dependence, and `Item-Dependencies` is `none` deliberately. `daexj1` is fully independent: it removes one cause, this reports every cause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the written predicate, expressed over NAMED run-record fields, and show the live-run exclusion, the recovered-lane exclusion and the UNKNOWN case each stated. Name which liveness signal was reused and cite it. Paste the re-measurement of the three cost claims (`03ie04`'s two lane costs, the stranded-lane count, `xdr83v_attempt2`'s commit count) with the commands and their actual output; if any figure does not reproduce, state the corrected number.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new `runner_shared` function's signature and docstring, showing it takes a repo root plus run record(s), returns structured records, and PRINTS NOTHING and exits nothing. Show by quotation that it calls `describe_lane` rather than reimplementing reachability or liveness. Paste the docstring's convergence note naming `rl67b0`'s resolver.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the mapping decision PER predicate outcome (not one blanket class) with its reasoning, and paste the code showing an unmapped lane state still raises rather than defaulting to a class. Paste the recorded choice between a synthetic tree and a render-time join with its reason. Paste `git diff` over `artifact_core.py` proving `SCAN_ROOTS` is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL `aw attention` output for a stranded-lane fixture, showing branch, worktree path, `integration_signal` and plan id6 on one row plus the remedy string. State whether the outcome word came from `ys1dor` (paste the matching string from that plan) or was chosen here (state the word for convergence). Confirm by inspection that no code path deletes, merges or moves anything.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `--agent` and `--json` payloads BEFORE and AFTER for the same fixture, showing the new field present and every pre-existing field byte-unchanged. State how the new field relates to the payload's validity flag and show the two cannot contradict (no `valid: true` beside a stranded lane).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste UNPIPED exit codes (`cmd >/dev/null 2>&1; echo $?`) for four states: stranded lane present (nonzero), no lanes (0), live-`driver.lock` lane only (0), UNKNOWN present (whichever was decided, with the decision restated). Paste the recorded decision on whether UNKNOWN fails or warns. If the attention spec was found to constrain `--check`, paste that text and STOP rather than proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL passing output of all seven cases, QUOTING the live-run case and the merged-and-executed case separately since those two are the false positives that would destroy the alarm. Paste the recovered-lane case showing the recovery actually performed and the historical run still reporting what it did at the time. Paste the one-reader proof (object identity or grep). Paste `git branch --list 'aw/lane/*' | wc -l` and `git worktree list` before and after, identical, plus `git status --porcelain`, as negative proof no real lane was touched. THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta explicitly. Paste `aw sanitize --agent` and state what it said about worktree paths in the new output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-01 is resolved (`blocked`, with one ambiguous case assigned to E-03), OQ-03 is resolved (do not wait; design for convergence), and OQ-02 is a genuine contract question that E-06 is instructed to escalate rather than guess, while E-04 and E-05 deliver value under either answer.

IT CARRIES `Blocks-Release: next`, inherited from backlog `nuanaw`. The justification is the measured loss: one fix paid for twice ($49.42, to be re-verified by E-01), eleven lanes holding validated work found only by running `git worktree list` by hand, and one lane that produced nothing while its run reported nothing wrong.

TWO DIVISIONS OF LABOUR A REVIEWER SHOULD CHECK, because getting them wrong would duplicate another plan's work. `ys1dor` owns the RUN SUMMARY and hands the ATTENTION half here by name; this plan reuses its outcome word rather than choosing a second. `rl67b0` owns the REMEDY verb and an overlapping resolver but reads `Readiness: no-go`; this plan converges rather than depends, and `Item-Dependencies: none` is deliberate.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. FIXTURES ONLY: this repo holds 28 `aw/lane/*` branches and live runs, and three agents are graduating concurrently, so a test that touches a real lane could destroy the very unintegrated work this plan protects. Re-locate every symbol by NAME; both driver files and the attention modules are under concurrent edit. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index. If E-01's measurement finds real unintegrated work, REPORT it; do not recover it here.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the two false-positive cases, the recovered-lane historical report done by actual recovery, the before/after `--check` exit codes, and the negative proof that no real lane was touched.

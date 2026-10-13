RETIRED 2026-10-12: duplicate of Set gradfix, which fixes the same two causes of the 2026-10-12 BACKLOG-GRADUATE-COUNT fail-gates in the same functions with incompatible changes; maintainer chose gradfix during /plan-review of gradfix; superseded by .aw/records/plans/pending/20261012-gradfix-00-kht4vk-stop-backlog-graduation-runs-from-failing-on-already-finishe.ipd.md

# IPD: Isolate production checks and reconcile backlog graduation gates

- Date: 2026-10-12
- Kind: child
- Concern: Investigation into runner failures across active multi-shard runs (`run-20261012T005606Z-2321569`, `run-20261012T005617Z-2321742`, `run-20261012T005641Z-2321995`, `run-20261012T005650Z-2322198`) and historical execution runs revealed distinct failure classes. In the active runs, 10 backlog graduation items failed with `fail-gate`: (1) Multi-runner concurrent shard race condition (`2rm0gz`, `iosmvn`), where `production_checks.backlog_graduate_count` iterates over all plans in `repo` against a stale runner-startup baseline, misattributing plans concurrently committed to `main` by peer runner shards as unlinked new plans authored during the current item's turn; (2) Re-running pre-graduated or already-executed backlog items (`ariaau`, `ildjse`, `h0tiaw`, `mflqqf`, `7yz545`, `s8veyk`, `oq05nc`, `vy20et`), where backlog items remained open despite their handoff plans having already been authored and executed under earlier Sets; when the agent correctly declined to duplicate finished work, `existing_handoff_plans` failed to inspect `executed/`, producing a false "0 linked IPDs" refusal. In addition, historical `fail-verify` outcomes (`76ic0k`, `9m4ujh`, `5poaqh`, `uxb0tz`, `3vh74b`) were singleton safety catches (where verifiers legitimately caught real test/lint/invariant regressions or Section 223 partial stops, such as catching unexpected `ast.parse` calls in runner test suites) rather than runner crashes; once their filed defect backlog items (`jahjj4`, `z9pfrk`) were executed, those singleton issues were permanently resolved. This plan implements strict production check isolation to eliminate cross-runner races and reconciles backlog handoff checks to recognize executed handoffs.
- Scope: IN: (1) in `runner_shared.execute_item_core`, re-derive the production baseline (`baseline_plan_ids`, `existing_before`, `continued_plan_ids`) from the ISOLATED LANE immediately after `allocate_isolation_worktree` returns and before the turn, so a plan that landed on `main` between the item-start snapshot and the lane cut is baseline, not this turn's output (fixes `fail-gate` cause 1A for BOTH `backlog_graduate_count` and `spec_plan_count`, which share that baseline); (2) handle an `open` backlog item whose every `From-Backlog` carrier is already terminal (`executed/`) according to the maintainer's answer to OQ-01, replacing the false "produced 0 linked IPDs" refusal (cause 1B); (3) behavioral regression tests in `tests/test_backlog_production.py` and `tests/test_production_resume_handoff.py`, red before and green after. OUT: changing the `production_checks.*_count` signatures (no new `new_plan_paths` parameter; see F-07); the execution verifier prompt or verdict schema; `aw backlog set` transition semantics; the historical `fail-verify`/`fail-begin`/`fail-depend`/`fail-merge` classes (analysis only, no code).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, tests/test_backlog_production.py, tests/test_production_resume_handoff.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/plans/pending/20261012-failfix-01-d52x8b-isolate-production-checks-and-reconcile-backlog-graduation-g.ipd.md
- Item-Dependencies: none
- Status: superseded
- Readiness: no-go
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: failfix
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: d52x8b

## Workflow history
- 2026-10-12 superseded (aw set): RETIRED 2026-10-12 by /plan-review of Set gradfix, maintainer decision: duplicate fix for the same 2026-10-12 BACKLOG-GRADUATE-COUNT fail-gates. Superseded by Set gradfix (kht4vk, 0owirm, s95x79, and Order 03). Its F-03..F-06 analysis of other failure types needs no code change.
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001, PR-002 (open, OQ-01), PR-003, PR-004, PR-005, PR-006

- 2026-10-12 draft (Antigravity): created from investigation of active runner shard failures in `aw runs --active -s`.
- 2026-10-12 to-review (Antigravity): authored complete plan addressing multi-shard race conditions, pre-graduated backlog false rejections, and failure mode analysis.

## Goal

Stop backlog and spec production turns failing `fail-gate` for reasons that are not the turn's fault: a peer shard's plan misattributed to this turn (cause 1A), and an already-finished handoff reported as "produced 0 linked IPDs" (cause 1B). Every refusal that IS the turn's fault (an unlinked plan authored in the turn, a second Set, no handoff at all) must keep refusing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Characterization (red tests before any production edit)

- [ ] E-01 Add two behavioral tests that FAIL at the pre-edit commit. (a) Race, end to end: drive the real runner (`oc_runipd` through `runner_shared.execute_item_core`) on an `open` backlog item `curr01` WITH worktree isolation, wrapping the driver's `allocate_isolation_worktree` (resolved via `getattr(driver_module, "allocate_isolation_worktree", ...)` in `execute_item_core`) so that, just before delegating to the real allocator, it commits a peer plan `peer01` carrying `- From-Backlog: peerbk` to the repo's `main`. The mocked agent turn writes one conforming plan with `- From-Backlog: curr01`. Assert the item does NOT end with a `BACKLOG-GRADUATE-COUNT` refusal naming `peer01` (read through `render_stream.refusal_of_item`) and that the backlog item reaches `graduated`. (b) Executed-only handoff: an `open` backlog item whose only `From-Backlog` carriers sit in `.aw/records/plans/executed/`, a turn that writes no plan; assert the outcome OQ-01 selects (this half is written in E-03, after OQ-01 is answered; E-01 records only the current false refusal as the red baseline). Record the pre-edit `python3 -m pytest -o addopts="" tests/test_backlog_production.py tests/test_production_resume_handoff.py` summary.
  - Depends on: none
  - Expected outcome: test (a) fails at the baseline with the misattribution refusal naming the peer plan; the pre-edit summary for both files is recorded.
  - Execution state: pending

### Task group 2: Re-baseline production checks from the lane (cause 1A)

- [ ] E-02 In `runner_shared.execute_item_core`, in the `if (is_spec_production or is_backlog_production) and isolate:` branch, immediately after `wt_handle = allocate_isolation_worktree(repo, item["id6"])` succeeds and BEFORE the turn is spawned, recompute `baseline_plan_ids` from `_ce._iter_plan_ipds(Path(work_dir))` and recompute `existing_before` / `continued_plan_ids` with `_pc.existing_handoff_plans(Path(work_dir), src_type, item["id6"])`. Leave the non-isolated path (`--no-isolate-worktree`, where `target_tree == repo`) unchanged. Do NOT add `new_plan_paths` / `new_plan_ids` parameters to `production_checks.backlog_graduate_count` / `spec_plan_count` and do NOT switch them to `git status --porcelain` discovery (F-07). Record an `events.jsonl` line (for example `production-baseline-rebased`) carrying the count of ids that entered the baseline only from the lane, so a later run can see the window was hit.
  - Depends on: E-01
  - Expected outcome: E-01 test (a) passes; the existing `TestProductionResumeHandoffUnit` and `TestBacklogProductionUnitE10` count outcomes are unchanged.
  - Execution state: pending

### Task group 3: Executed-only handoff (cause 1B)

- [ ] E-03 BLOCKED ON OQ-01. Implement the maintainer's answer to OQ-01 for an `open` backlog item whose every `From-Backlog` carrier is terminal and whose turn authored no plan, with the matching E-01(b) test asserting that outcome, and amend spec `25kzda` Section 4.9's `BACKLOG-GRADUATE-COUNT` row (and add any new refusal code to the same table) in the same change. Whatever the answer, the refusal or pass MUST NOT read "produced 0 linked IPDs", and the item MUST NOT be set `graduated` (graduated means code not yet written; the carriers are already executed).
  - Depends on: E-02
  - Expected outcome: the executed-only case yields exactly the OQ-01 outcome with an accurate message; spec row and code agree.
  - Execution state: pending

### Task group 4: Preserved refusals and full suite

- [ ] E-04 Add behavioral tests proving the refusals that ARE the turn's fault still fire after E-02/E-03, on the isolated path: (1) an unlinked plan authored in the turn's lane is refused `BACKLOG-GRADUATE-COUNT` "linking a different item or none"; (2) a second Set authored in the turn is refused "introduced a second Set"; (3) a turn that authors nothing for an item with NO carriers at all still refuses "produced 0 linked IPDs"; (4) the same race shape as E-01(a) for a SPEC production item does not misattribute (`SPEC-PLAN-COUNT`). Then run the bare suite.
  - Depends on: E-03
  - Expected outcome: all four pass, and the bare `python3 -m pytest` shows no new failures relative to the E-01 baseline.
  - Execution state: pending

- [ ] E-05 Commit only the declared paths via `aw commit d52x8b -- <declared paths you changed>`; never push.
  - Depends on: E-04
  - Expected outcome: `git show --stat HEAD` lists only paths in `- Scope-Paths:`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Isolation: work and test in an isolated worktree, never in `main` (`GEMINI.md` Rule 1). The runner integrates the lane; the executor never merges or pushes.
- Bare test execution: run `python3 -m pytest` bare; for a narrowed run use `python3 -m pytest -o addopts="" <paths>` (AGENTS.md repo-local contract, `GEMINI.md` Rule 5).
- Test outcomes, not code structure: drive the runner and the checks and assert on refusals, item status and on-disk state (AGENTS.md, GUIDING_PRINCIPLES P16).
- Commit via `aw commit d52x8b -- <paths>` (the plan id6, not the Set id).
- Cite code by SYMBOL or quoted string, line numbers only as hints (spec `ipd-structure-and-linting` Section 10.2).
- A plan that changes behavior a spec describes amends the spec in the same change and lists it in `- Scope-Paths:` (AGENTS.md "A PLAN MAY AMEND A SPEC").

## Findings

| ID | Severity | Topic | Location | Description |
|---|---|---|---|---|
| F-01 | HIGH | Race condition | `runner_shared.execute_item_core` (`for p, text in _ce._iter_plan_ipds(repo): baseline_plan_ids.add(...)` vs. the later `wt_handle = allocate_isolation_worktree(repo, item["id6"])`) | The production baseline is snapshotted PER ITEM from the main checkout at item start (not at runner start), and the isolated lane is cut later from `HEAD` (`allocate_isolation_worktree` -> `worktree_lease.allocate_worktree(repo, id6, base_commit="HEAD")`). A peer plan merged to `main` in that window is in the lane but not in the baseline, so `backlog_graduate_count` condition (b) refuses it as this turn's unlinked output. Git evidence: lane `aw/lane/2rm0gz` was "Created from 1feee61ca" at 23:15:15, and peer plans `jykyqb` (`3bb9d06a2`, From-Backlog `kntbbc`, integrated `4c908ae13` at 23:14:52) and `ml7b9e` (`92062cd4e`, From-Backlog `j7daih`, integrated `1feee61ca` at 23:15:12) are ancestors of that base. Same shape for `iosmvn` (lane base `8538be828`) and `k6clui` (`c1b699e08`, integrated `8538be828` at 23:18:44). |
| F-02 | HIGH | False rejection | `production_checks.existing_handoff_plans` (`if disp in _TERMINAL_DISPOSITIONS: continue`) | Terminal plans are skipped, so for an `open` item whose carriers are all executed, `all_linked` is empty and condition (a) reports "produced 0 linked IPDs". Measured: backlog `ariaau`, `ildjse`, `mflqqf` are `open` with 3-4 `From-Backlog` carriers each, all in `executed/`. |
| F-03 | MEDIUM | Scope refusal in finalize | `runner_shared.execute_item_core` finalize scope gate | Historical `m47znv`: an executor filed a backlog item outside Scope-Paths and finalize refused pending `--scope-reason`. Not addressed here (see Deferred). |
| F-04 | INFO | Verifier safety stop | `runner_shared` status map `"partial": "fail-verify"` | Historical `fail-verify` outcomes (`76ic0k`, `9m4ujh`, `5poaqh`, `uxb0tz`, `3vh74b`) are reported as verifier or `partial` safety stops. UNVERIFIED at review: the defect items `jahjj4` / `z9pfrk` named as their resolution resolve to no backlog record and no commit in this repository, and `tests/test_runner_shared.py` still calls `ast.parse` (a helper reading `pathlib.Path(...).read_text`), so "permanently resolved / will never recur" is not established. Analysis only; no code in this plan depends on it. |
| F-05 | INFO | Pre-execution gate | `execute_item_core` event `ipd-begin-refused` | `fail-begin` is the pre-execution gate refusing an unrunnable plan or lane (for example `tliqz6` attempt 2). Analysis only. |
| F-06 | INFO | Cascaded dependencies | `execute_item_core` event `dependency-blocked` | `fail-depend` cascades from an upstream failure; fixing F-01/F-02 removes the cascades they caused. Analysis only. |
| F-07 | HIGH | Proposed fix was circular (review) | `runner_shared.execute_item_core` backlog branch: `new_produced_paths` is built as `if p_id not in baseline_plan_ids` over `_iter_plan_ipds(target_tree)`; `commit_backlog_production_output` commits the produced plans BEFORE `_pc.backlog_graduate_count` runs | The original E-02/E-04 (pass `new_plan_paths=new_produced_paths` into the count, or fall back to `git status --porcelain`) cannot fix F-01: `new_produced_paths` is derived from the same stale baseline and contains the peer plan, and the porcelain status is already clean at check time because the production commit precedes the check, which would also silently stop detecting unlinked plans the turn itself authored. Review prototype (scratch repo, deleted): stale baseline -> `produced new plan(s) (peer01) linking a different item or none`; baseline re-read from the lane after the cut -> `[]`; same lane plus an unlinked `bad001` written in the turn -> still refused naming `bad001`; executed-only carrier -> `produced 0 linked IPDs`. |

## Root cause and prevention

- Cause 1A (F-01): the baseline and the tree being judged come from two different moments. Fix: take the baseline from the tree being judged, at the moment it is cut (E-02). That closes the window by construction rather than by narrowing it, and needs no change to the check functions or their callers.
- Cause 1B (F-02): an `open` item whose work already executed is a reconciliation gap, not a production failure. What the runner should do with it is a lifecycle decision (OQ-01); the fix must at minimum stop the false message and must not mark finished work `graduated`.
- Other classes (F-03..F-06) are recorded for context; this plan changes none of them.

## Proposed changes (ordered, validatable)

1. E-01: red characterization tests (race end to end; executed-only baseline).
2. E-02: re-baseline from the lane after allocation.
3. E-03: executed-only handoff per OQ-01, with the spec row amended.
4. E-04: preserved-refusal tests and bare suite.
5. E-05: path-scoped commit.

## Deferred / out of scope (with reason)

- Changing the execution verifier prompt or verdict schema: `fail-verify` outcomes are safety stops, not this defect.
  - Carrier-Declined: verifier contract is not implicated by F-01/F-02
- Changing `aw backlog set` state transitions.
  - Carrier-Declined: transition table is correct; the false refusals come from the production checks' inputs
- F-03 finalize refusal for an out-of-scope backlog file.
  - Carrier-Declined: by design, an out-of-scope edit is made and then justified with `--scope-reason` at finalize (AGENTS.md scope-fence ruling); the refusal is the intended prompt for that justification
- Reconciling the already-open items with executed carriers (`ariaau`, `ildjse`, `mflqqf`, ...) by hand: an operator act outside this code change.
  - Carrier-Declined: a one-off data reconciliation, decided by the maintainer alongside OQ-01, not a deliverable of this plan

## Scope check

- Over-scope: none after review. The original Scope item (5) ("document root causes ... in the record") had no E-item and is now the Root cause section of this plan only.
- Under-scope: none, provided OQ-01 is answered. The spec amendment E-03 needs is declared in `- Scope-Paths:`.

## Required tests / validation

- E-01(a) red at the pre-edit commit, green after E-02 (V-01, V-02).
- E-01(b)/E-03 asserting the OQ-01 outcome (V-03).
- E-04 preserved refusals (V-04).
- `python3 -m pytest -o addopts="" tests/test_backlog_production.py tests/test_production_resume_handoff.py` and bare `python3 -m pytest` (V-04).
- `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` passing (V-05).

## Spec / documentation sync

- E-02 changes no specified behavior: spec `25kzda` Section 4.9 already defines `BACKLOG-GRADUATE-COUNT` against "Baseline/current IPDs"; E-02 makes the baseline correct.
- E-03 DOES change specified behavior: the Section 4.9 row requires "At least one active IPD links to the backlog ID", which an executed-only handoff cannot satisfy. The row (and any new refusal code) is amended in the same change, which is why the spec file is in `- Scope-Paths:`.
- No user-facing CLI docs change. Add a CHANGELOG line only if OQ-01's answer changes what an operator sees for an executed-only item.

## Open questions

### OQ-01: What should a backlog production run do with an `open` item whose every `From-Backlog` carrier is already executed?

- Blocking: yes
- Finding: PR-002
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Options. (A) Refuse before spending an agent turn with a distinct, accurate code (for example `BACKLOG-ALREADY-SATISFIED`) naming the executed carriers and the remedy `aw backlog set done <id6> --evidence <executed plan>`; the item stays `open`. (B) Same accurate refusal, but only after the turn. (C) Treat it as satisfied and let the runner close the item `done` itself via the HANDOFF arm. (D) Pass the count and let the runner set `graduated` (the original E-03): rejected at review, because `graduated` claims code not yet written while the carriers are executed, and the setter's history line would cite no produced artifact. Reviewer recommendation: (A); it is the honest message at the lowest cost, and the existing `summarize_graduation_cluster` PRE-GRADUATION VIEW already computes terminal carriers. (C) is the only option that mutates lifecycle state on the runner's own authority and changes a public contract, so it needs the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted FAILING output of the E-01(a) race test at the pre-edit commit, showing the `BACKLOG-GRADUATE-COUNT` refusal naming the injected peer plan; pasted pre-edit summary of `python3 -m pytest -o addopts="" tests/test_backlog_production.py tests/test_production_resume_handoff.py`. The observation is produced by `runner_shared.execute_item_core`'s backlog-production branch, reached through the wrapped `allocate_isolation_worktree` that E-01 creates.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff` hunk of `execute_item_core` showing the re-baseline after allocation; pasted PASSING output of the same E-01(a) test; pasted passing output of the pre-existing `test_backlog_graduate_count_outcomes` / `test_spec_plan_count_outcomes` / `test_backlog_graduate_count` tests; and the `production-baseline-rebased` event line from the test's `events.jsonl` (or the test asserting it).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the recorded OQ-01 answer; pasted passing output of the executed-only test asserting that outcome and asserting the message does not contain "produced 0 linked IPDs" and the item is not `graduated`; pasted diff of the spec `25kzda` Section 4.9 row.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted passing output of the four preserved-refusal tests; pasted `python3 -m pytest -o addopts="" tests/test_backlog_production.py tests/test_production_resume_handoff.py` summary; pasted bare `python3 -m pytest` summary line with any failure compared against the E-01 baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git show --stat HEAD` listing only declared paths; pasted `aw ipd lint --phase pre-transition` conforming output; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`) AND an answer to OQ-01 (blocking). Execute E-items in order.

Execution contract:
- Scope declaration: `- Scope-Paths:` declares the intended paths. It is a declaration, not a stop condition: an out-of-scope edit that turns out to be genuinely required is made and justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`.
- Honesty: you MUST paste the ACTUAL runner output for every test claim; never claim a pass you did not run.
- Commits: commit only declared paths through `aw commit d52x8b -- <paths>`; never `git add -A`, never push, never merge to `main` yourself.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; do not run `aw ipd finalize` yourself. Executing by hand, finalize through `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `Result: pass`. Never hand-roll a `git mv` into `executed/`.

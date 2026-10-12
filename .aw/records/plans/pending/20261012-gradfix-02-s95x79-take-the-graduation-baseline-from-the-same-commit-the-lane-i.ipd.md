# IPD: Take the graduation baseline from the same commit the lane is cut from

- Date: 2026-10-12
- Kind: child
- Concern: Two of the ten fail-gate items (`2rm0gz`, `iosmvn`) did their job correctly, writing plans that each carried the right `From-Backlog:`, and were still failed with "produced new plan(s) (...) linking a different item or none". The plans named (`jykyqb`, `ml7b9e`, `k6clui`) were not theirs: other runs running at the same time had just merged them into main. The check decides which plans a turn "produced" by comparing the lane's plans after the turn against a list of plans taken BEFORE the turn, and that list missed plans that the lane did contain, so other runs' plans looked new.
- Scope: On an isolated run, compute the pre-turn plan list (and the continued-plan list) from the lane worktree right after it is allocated and before the agent turn, instead of from an earlier read of the main checkout, so the comparison is between two states of the same tree and a concurrent merge cannot fall between them. On a non-isolated run, keep reading the shared checkout's working tree but move the read to the same point (immediately before the turn), which narrows the window and does not close it (see Deferred). Use the same fix for spec production, which uses the same comparison. No change to which plans count as linked, or to the checks' messages.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_baseline_same_commit.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: gradfix
- Order: 2
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: s95x79

## Workflow history
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Record: .aw/records/reviews/20261012-gradfix-02-s95x79-take-the-graduation-baseline-from-the-same-commit-the-lane-i.review.md Round 1
- 2026-10-12 to-review (aw set): authored to fix the 2026-10-12 fail-gate cluster (Set gradfix)

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A graduation or spec-production turn is judged only on the plans it actually added, regardless of what other runs merge into main while it runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reproduce the mismatch

- [ ] E-01 REPRODUCE on real records. Check out each preserved lane branch into a throwaway DETACHED worktree under `/tmp` (`git worktree add --detach <tmp> aw/lane/iosmvn`, tip `78d44e6f1` at review; `aw/lane/2rm0gz`, tip `86aa23511`), never into the shared checkout, and remove it afterwards. Build each plan id list from git, not from a working tree: `git ls-tree -r --name-only <commit> .aw/records/plans`, keep `*.ipd.md`, and take each plan's `- Id:` from `git show <commit>:<path>`. For `iosmvn`: call `production_checks.backlog_graduate_count(<tmp lane>, "iosmvn", ids@c56c5cf0b)` (main before `md2o3y` merged) and again with `ids@8538be828` (the lane base). Expected: the first refuses naming `k6clui`; the second returns `[]`. For `2rm0gz`, use `97959e3fa` (main when its previous item finished) and `1feee61ca` (its lane base): refuses naming `jykyqb, ml7b9e`, then `[]`. Paste all four results. This proves the failure is the baseline/lane mismatch and nothing about the agent's plans. If a lane branch is gone, search dangling objects by subject before declaring it unrecoverable (`git fsck --connectivity-only`, or `runner_shared.find_dangling_commits_by_subject`) and record which check ran; if neither lane is recoverable, record that and continue, because E-04's fixture reproduces the same mismatch synthetically.
  - Depends on: none
  - Expected outcome: two refusals and two passes, pasted.
  - Execution state: pending

- [ ] E-02 FIND WHERE THE LIST GOES STALE, by measurement. The list is built near the top of `runner_shared.execute_item_core` (the `baseline_plan_ids` loop over `_iter_plan_ipds(repo)`), and the lane is allocated later in the same function from `HEAD` (`allocate_isolation_worktree`). In both incidents the list matches main as of the PREVIOUS item's end, not this item's start (`2rm0gz`: previous item finished 03:14:49Z, missing plans merged 03:14:52Z and 03:15:12Z, item started 03:15:15Z; `iosmvn`: previous 03:18:42Z, missing plan merged 03:18:44Z, started 03:19:05Z). Note F-07: the attempt's `started_at` is stamped AFTER the baseline read and after the host-capability preflight and prompt build, so "item started" is an upper bound on the read time, and the leading hypothesis is "a read taken before a wait" rather than a cache. Discriminate by measurement: in a scripted fixture (the E-04 harness is fine), temporarily log `utc_now()` at the baseline read and at `allocate_isolation_worktree`, and compare with the incident runs' `events.jsonl` (`worktree-allocated` timestamps) where they are still on disk. The instrumentation is TEMPORARY: revert it before E-03 and never commit it (it is outside Scope-Paths). Record the answer as F-05 before changing code. If the measurement cannot discriminate, record exactly that as F-05 and proceed: E-03 is correct whichever read it was.
  - Depends on: E-01
  - Expected outcome: a recorded, measured answer to "which read was stale" (or a recorded statement that it could not be discriminated, with what was measured), added to Findings as F-05, and no instrumentation left in the diff.
  - Execution state: pending

### Task group 2: fix and prove

- [ ] E-03 Compute the baseline FROM THE TREE THE TURN WILL RUN IN, at the point the turn is about to start. In `runner_shared.execute_item_core`, move the `baseline_plan_ids` / `existing_before` / `continued_plan_ids` computation (today the `if is_spec_production or is_backlog_production:` block that loops `_ce._iter_plan_ipds(repo)` and calls `_pc.existing_handoff_plans(repo, ...)`) to a single point AFTER the `(is_spec_production or is_backlog_production) and isolate` lane-allocation block and BEFORE the `wt_handle is None and continued_plan_ids` pre-dirty filter, so that filter still sees the list. Read from `Path(work_dir)` when a lane was allocated (an untouched lane worktree holds exactly `wt_handle.base_commit`; F-06), else from `repo`. Keep the `is_backlog_production` `status_before` read where it is (it reads the backlog file, not the plan inventory). Do NOT switch the non-isolated read to `git ls-tree HEAD`: the post-turn scan reads the WORKING TREE (`_ce._iter_plan_ipds(target_tree)`), so a committed-only baseline would count any plan already present uncommitted in the shared checkout as "new" (F-08). Leave every downstream consumer (`commit_spec_production_output`, `commit_backlog_production_output`, the `p_id not in baseline_plan_ids` loops and the `existing_handoff_plans(target_tree, ...)` filters, on first and correction attempts) reading the same variables unchanged. Spec production shares the block and gets the same fix. Recompute is per attempt: a correction turn reuses the variables already set for the item, exactly as today.
  - Depends on: E-02
  - Expected outcome: on an isolated run the baseline and the post-turn scan are two states of the same tree, so a concurrent merge into main cannot appear as a "new plan"; on a non-isolated run the read happens immediately before the turn instead of before preflight and prompt build.
  - Execution state: pending

- [ ] E-04 Add `tests/test_production_baseline_same_commit.py` (P16: drive the real runner, assert on queue status, `events.jsonl`, refusal text and committed paths, never on source text). Reuse the fixture shapes of `tests/test_backlog_production.py` and `tests/test_spec_production.py` (`_make_test_repo`, `_write_backlog_item` / `_write_spec`, `_patch_host_agent`, and the `_HOSTS` loop so BOTH `oc_runipd` and `agy_runipd` are driven). Make the concurrent merge DETERMINISTIC rather than timing-based: wrap `runner_shared.allocate_isolation_worktree` (`mock.patch.object` with a side effect that first commits, on the fixture's main branch, a pending plan carrying a DIFFERENT `- From-Backlog:` / `- From-Spec:`, then calls the real function). That lands the foreign plan exactly in the window between the old baseline read and the lane cut, whatever E-02 finds the original trigger to be. The scripted agent then writes one correctly linked, conforming plan. Cases: (a) backlog production, isolation on: item does not end `fail-gate`, the backlog item reaches `graduated`, no `BACKLOG-GRADUATE-COUNT` refusal text appears in state or events, and the foreign plan's id is not among the committed production paths; (b) the same for spec production (no `SPEC-PLAN-COUNT` refusal, spec reaches `implementing`); (c) non-isolated (`--no-isolate-worktree`) backlog production with a pre-existing UNCOMMITTED unrelated plan in the shared checkout: it is not reported as produced (guards against a `HEAD`-only baseline, F-08); (d) negative control: an agent that writes a plan with the WRONG `From-Backlog` still refuses with the unchanged message. Cases (a) and (b) must FAIL on the base commit; show it (for example by stashing the E-03 hunk or running the module against a checkout of the base commit). Then run `tests/test_backlog_handoff_close.py`, `tests/test_backlog_production.py`, `tests/test_spec_production.py` and the `tests/test_production_*.py` modules unchanged, then the bare suite.
  - Depends on: E-03
  - Expected outcome: new module passes on both hosts; (a) and (b) fail on the base commit; existing tests and bare suite pass.
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
| F-05 | (Reserved for E-02's measured answer.) | |
| F-06 | Scanning an untouched lane worktree yields exactly the plan ids `git ls-tree`/`git show` read at its base commit, so the preferred OQ-01 mechanism is equivalent to a git read. | Measured at review 2026-10-12: detached worktrees at `8538be828` and `1feee61ca`; `{_extract_plan_id(p,t) for p,t in check_engine._iter_plan_ipds(wt)}` equals the git-read set (1366 and 1364 ids, symmetric difference empty). |
| F-07 | The attempt's `started_at` is stamped after the baseline read, after the scope-target and host-capability preflights and after the prompt is built, so the incident "item started" times are an upper bound on when the baseline was read. | `runner_shared.execute_item_core`: `baseline_plan_ids` loop precedes `ensure_frozen_host_capabilities`/`preflight_host_capabilities`, `build_backlog_production_prompt`, `write_prompt`, and the `attempt = {... "started_at": utc_now() ...}` dict. |
| F-08 | The post-turn production scan reads the WORKING TREE of `target_tree`, so the baseline must too. A `git ls-tree HEAD` baseline on a non-isolated run would count an uncommitted pre-existing plan as new. | `execute_item_core` spec and backlog branches: `for p, text in _ce._iter_plan_ipds(target_tree): ... if p_id not in baseline_plan_ids`; `check_engine._iter_plan_ipds` globs `*.ipd.md` on disk. |

## Proposed changes (ordered, validatable)

1. Reproduce (E-01) and pin down the stale read (E-02).
2. Baseline from the lane's base commit (E-03).
3. Concurrent-merge test, both production types (E-04).

## Deferred / out of scope (with reason)

- Serializing runs so nothing merges during an item's start: unnecessary on an isolated run once both reads come from one tree, and it would slow every parallel run.
- Closing the race fully on a NON-isolated run (`--no-isolate-worktree`). There, another run's integration advances the shared checkout's working tree during the agent turn itself, so any pre-turn baseline can be overtaken. E-03 only moves the read to immediately before the turn. Closing it would mean diffing against the turn's own commits or holding a lock across the turn, a design change with Medium functionality risk for a mode that is opt-out (isolation defaults ON). Both incidents were isolated runs. Consequence if left: a non-isolated graduation running beside another run can still be falsely refused; the remedy is to re-run, as today.
- Integrating or pruning the preserved `aw/lane/2rm0gz` and `aw/lane/iosmvn` lanes: a human choice (orchestrator `kht4vk` Goal). This plan only reads them in E-01.

## Scope check

- Over-scope: none.
- Under-scope: none known. If E-02 shows the stale read lives outside `runner_shared` (for example a cache in `artifact_core`), make the out-of-scope edit and justify it at finalize with `--scope-reason`, recording why in this plan.

## Required tests / validation

- `tests/test_production_baseline_same_commit.py` (new), both hosts, cases (a) and (b) failing on the base commit.
- Invariants pinned: a concurrently merged foreign plan is never "produced" (a, b); an uncommitted pre-existing plan is never "produced" on a non-isolated run (c); a genuinely mislinked plan still refuses with the unchanged message (d).
- Existing `tests/test_backlog_handoff_close.py`, `tests/test_backlog_production.py`, `tests/test_spec_production.py`, `tests/test_production_*.py` unchanged and passing.
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

N/A: spec `25kzda` Sections 4.8 (`SPEC-PLAN-COUNT`) and 4.9 (`BACKLOG-GRADUATE-COUNT`) define the evidence as the "Baseline/current IPD inventory" and the pass criterion as "At least one active IPD links to the ... ID and every new one does". The spec does not say when the baseline is taken; this fixes what "new" is measured against (the tree the turn ran in, which is what "baseline" already means there) and changes neither the criteria nor the messages.

## Open questions

### OQ-01: Read the base commit with git, or scan the lane before the turn?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Scan the lane worktree before the turn (E-03). Demonstrated at review, not assumed: F-06 shows the lane scan and the git read at the base commit give identical id sets on both incident bases. The lane scan also matches the post-turn scan's own reader (`_iter_plan_ipds` on a working tree, F-08), so the two sides of the comparison use one mechanism. Nothing writes the lane between `allocate_isolation_worktree` returning and the agent turn starting, so the scan point is untouched. Reversible (review decision D-1).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the four pasted `backlog_graduate_count` results (two refusals naming `k6clui` and `jykyqb, ml7b9e`, two `[]`), the commands that built each id list, and `git worktree list` showing the throwaway worktrees removed; or, if a lane was unrecoverable, the pasted dangling-object check that established it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the instrumented fixture's pasted timestamps (baseline read vs lane allocation) naming which read was stale, or the pasted measurement showing it could not be discriminated; the filled F-05 row; and `git diff --stat` after reverting the instrumentation showing no logging hunk remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `execute_item_core` diff hunk showing the baseline block now runs after the production lane-allocation block and reads `work_dir` when a lane exists, and E-04 cases (a) and (b) passing on both hosts through `execute_item_core`'s spec and backlog production branches (the code path that produces the observation) with the scripted host, pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new module's pasted run with every case (a)-(d) passing on both hosts; pasted output of cases (a) and (b) FAILING on the base commit with the `BACKLOG-GRADUATE-COUNT` / `SPEC-PLAN-COUNT` refusal naming the foreign plan; pasted passing runs of the named existing modules; and the bare-suite `N passed` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. STOP and report only if a co-worker's uncommitted change occupies a region you must edit and the two cannot be safely combined, or if a symbol this plan cites by name is absent. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin s95x79`. Commit only through `aw commit s95x79 -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. E-02's instrumentation is never committed. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize s95x79` once `aw ipd lint --phase pre-transition` conforms and every `V-*` records concrete pasted evidence with Result: pass. Never hand-roll the move or `git mv` this plan into `executed/`. Release gate: this plan carries `- Blocks-Release: next` as a live `bug` plan; keep it.

# IPD: Record a driver-side review output commit in the plan's own history

- Date: 2026-09-25
- Kind: child
- Concern: `runner_shared.commit_review_lane_output` commits a review turn's UNCOMMITTED sweep-lane output under the subject "review(<host>): record the review of <id6>", a driver-authored commit of content the agent produced. Re-measured at HEAD `8e74dcac`: the only product call site is the `if is_review and wt_handle is not None:` branch of `runner_shared.execute_item_core` (the two per-host sites the backlog cites were deduplicated by `70a2059f`); the commit carries NO `AW-Run`/`AW-Item` trailers, prints nothing to the operator, and leaves no mark in the plan's `## Workflow history`. Its only traces are `attempt["review_lane_commit"]` in `state.json` and a `review-lane-output-committed` event, neither of which survives outside the run directory. Across the 22 recorded runs with sweep reviews (87 sweep review attempts), the key `review_lane_commit` appears zero times and no commit in `git log --all` carries that subject, so the path has never fired; the gap is visibility of a rare, conservative write, not lost work.
- Scope: IN: (a) the driver commit carries the canonical `AW-Run`/`AW-Item` trailers (`git_commit_helper.run_item_trailers` composed with `compose_message_with_trailers`) plus an `AW-Committed-By: driver` trailer, so the commit is self-describing in permanent history; (b) the driver prints one yellow stderr line naming the id6, the commit and the paths when it commits, and one when a hook refuses; (c) the end-of-run report on both hosts counts driver-committed reviews; (d) a regression test. OUT: writing a line into the plan's `## Workflow history` (rejected, see Findings F-3); refusing a non-committing review as a failed turn (the maintainer decision in OQ-01, defaulted to keep the safety net).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_review_lane_output_commit.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: wtaxvk
- Set: revcommit
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8apjpp

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog wtaxvk; re-measured that the driver-side review commit has one call site, carries no trailers or history mark, and has fired zero times in 87 recorded sweep review attempts.

## Goal

When the driver commits a review's leftover output, that fact is visible where a human looks: in the commit itself (trailers naming run, item and committer), on the operator's terminal, and in the run summary, without changing whether the work lands.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin today's behavior

- [ ] E-01 Add `tests/test_review_lane_output_commit.py`. Build a temp git repo (the `make_repo` shape in `tests/test_runner_shared.py`: `git init`, test identity, one initial commit), add a worktree via `git worktree add`, write an untracked `.aw/records/plans/pending/x-rvc001-p.ipd.md` into it, and call `runner_shared.commit_review_lane_output(repo, handle, "rvc001", host_label="oc", run_id="run-test")` with `handle` a `worktree_lease.WorktreeHandle` for that worktree. Assert: the returned sha is the worktree HEAD; `git interpret-trailers --parse` on its message yields `AW-Run: run-test`, `AW-Item: rvc001` and `AW-Committed-By: driver`; the subject is unchanged ("review(oc): record the review of rvc001"). Second case: a clean worktree returns `(None, ())` and makes no commit. Third case: a `pre-commit` hook in the worktree's git dir exiting 1 returns `(None, (<path>,))` and leaves the file uncommitted.
  - Depends on: none
  - Expected outcome: the trailer case FAILS at HEAD (`TypeError` on `run_id`, then missing trailers); the clean and hook cases pass once the signature exists.
  - Execution state: pending

### Task group 2: make the write visible

- [ ] E-02 In `runner_shared.commit_review_lane_output`, add a keyword-only `run_id: str | None = None` parameter and build the second `-m` body as `git_commit_helper.compose_message_with_trailers(<existing body>, [*git_commit_helper.run_item_trailers(run_id, id6), "AW-Committed-By: driver"])`, each trailer passed through `validate_trailer`. Extend the docstring with a paragraph "VISIBLE BY CONSTRUCTION (revcommit `8apjpp`)" stating the trailers and why history is not written (F-3).
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` passes.
  - Execution state: pending

- [ ] E-03 At the call site in `runner_shared.execute_item_core` (`review_commit, review_committed_paths = commit_review_lane_output(`), pass `run_id=str(state.get("run_id") or "") or None`; when `review_commit` is set, print to stderr, yellow via `pal`, "  ! review <id6> left its output uncommitted; the driver committed <n> path(s) as <sha12> (AW-Committed-By: driver)"; when `review_committed_paths` is set without a commit, print "  ! review <id6> left uncommitted output and a hook refused the driver's commit; the work stays in the sweep lane: <paths>".
  - Depends on: E-02
  - Expected outcome: `grep -n 'the driver committed' agent_workflows/runner_shared.py` returns the new line inside the review branch; `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` still passes.
  - Execution state: pending

- [ ] E-04 Add a pure helper `runner_shared.driver_committed_reviews(state) -> list[str]` returning the id6 of every queue item whose latest attempt carries `review_lane_commit`, and `runner_shared.report_driver_committed_reviews(state, *, stream=None)` printing "N review(s) had their output committed by the driver: <id6s>" only when N > 0. Call it immediately after the PRIMARY end-of-run `report_run_spec_edits(state)` in both `oc_runipd.run_queue` and the agy twin (the sites commented "specvis st5klo E-03: the PRIMARY end-of-run site"). Add tests over a hand-built `state` with one driver-committed and one self-committed review: the helper returns exactly the one id6, and the reporter prints nothing for a state with none.
  - Depends on: E-03
  - Expected outcome: the helper test passes and returns exactly the one id6.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Run the directly affected modules: `python3 -m pytest tests/test_review_lane_output_commit.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py`.
  - Depends on: E-04
  - Expected outcome: 0 failed.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-owned commits are identified by `AW-Run`/`AW-Item` trailers (spec `25kzda` 4.6, quoted at `git_commit_helper.TRAILER_KEY_RUN`); `run_item_trailers` requires the values come from live run state, never synthesized, which `state["run_id"]` and `item["id6"]` satisfy.
- `commit_review_lane_output` is path-scoped, runs hooks, and treats a hook rejection as "nothing committed"; none of that changes here.
- The auto-approve fallback reads the NEWEST history record (`plan_readiness.is_plan_review_approved` -> `history_verdict_approves(extract_newest_history_entry(text))`), and `status_set` prepends records newest-first.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `runner_shared.commit_review_lane_output` | The driver-authored commit carries no run/item/committer trailers, so permanent history cannot tell it from an agent's own review commit except by its body prose. | `subject = f"review({host_label}): record the review of {id6}"`; no `run_item_trailers` call in the function |
| F-2 | LOW | `execute_item_core` review branch | The commit is recorded only in `state.json` and `events.jsonl`; no operator-facing line. | `attempt["review_lane_commit"] = review_commit`; `"event": "review-lane-output-committed"` |
| F-3 | INFO | plan `## Workflow history` | Writing a driver line into the reviewed plan's history is REJECTED: it would become the newest record, and the auto-approve prose fallback reads only the newest record, so a driver line would silently mask the review's verdict. It would also need a second driver commit editing the plan. Trailers carry the same fact without touching the reviewed artifact. | `plan_readiness.is_plan_review_approved` fallback |
| F-4 | INFO | run records | Never fired: 0 of 87 sweep review attempts in 22 runs carry `review_lane_commit`; 0 commits with the subject in `git log --all`. | grep of `.aw/records/runs/*/state.json`; `git log --all --grep="record the review of"` |

## Proposed changes (ordered, validatable)

1. E-01 adds the failing test.
2. E-02 adds trailers.
3. E-03 threads `run_id` and prints the operator line.
4. E-04 adds the run-summary count.
5. E-05 and E-06 run the affected modules and the bare suite.

## Deferred / out of scope (with reason)

- Requiring a review turn to commit for itself and reporting a non-committing review as a failed turn. That is the maintainer decision OQ-01; this plan defaults to keeping the safety net.
  - Carrier: wtaxvk

## Scope check

- Over-scope: none.
- Under-scope: none; `commit_review_lane_output` has one product caller (grep across `agent_workflows`), and the end-of-run report is wired at both hosts.

## Required tests / validation

New `tests/test_review_lane_output_commit.py` (trailer case failing before E-02), the affected modules, then the bare suite.

## Spec / documentation sync

N/A: no spec describes the review sweep's driver commit (grep of `.aw/records/specs` for `commit_review_lane_output` and "record the review of" is empty). The rationale lives in the function docstring (E-02).

## Open questions

### OQ-01: Should the driver commit a review's uncommitted output at all, or should a non-committing review fail its turn?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: keep the driver commit and make it visible (this plan). Evidence: it has fired zero times in 87 sweep reviews, so the honesty cost is currently nil, while removing it would turn a future non-committing review from "landed and labelled" into "work stranded in a lane that is later torn down". If the maintainer prefers strictness, a follow-up replaces the commit with a refusal; the trailers added here are then harmless. Backlog `wtaxvk` remains open as the carrier of this decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` run BEFORE E-02, pasted, showing the trailer case FAILING (`TypeError` naming `run_id`, or a missing `AW-Committed-By` assertion).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the same command after E-02, pasted, all passed; the test's printed `git interpret-trailers --parse` output showing `AW-Run: run-test`, `AW-Item: rvc001`, `AW-Committed-By: driver`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff -- agent_workflows/runner_shared.py` hunk at the `commit_review_lane_output(` call showing `run_id=` and both stderr messages.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted passing output of the `driver_committed_reviews` test, and the diff hunks adding `report_driver_committed_reviews(state)` after `report_run_spec_edits(state)` in `oc_runipd.py` and `agy_runipd.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted summary line of `python3 -m pytest tests/test_review_lane_output_commit.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted final summary line of the bare `python3 -m pytest`, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution. The executor commits only the Scope-Paths via `aw commit 8apjpp -- <paths>`, never `git add -A`, never pushes, pastes actual runner output for every V item, and moves the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms.

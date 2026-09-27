# IPD: Send a merge-back conflict back to the same agent to resolve in its lane instead of failing the item

- Date: 2026-09-27
- Kind: child
- Concern: A lane whose verified work CONFLICTS with main at merge-back is failed (`fail-merge`, terminal on the first attempt, not counted against the retry budget) and handed to a HUMAN, even when the agent that wrote the work is still in the run and the conflict is trivial. Measured 2026-09-27 in run-20260927T051110Z-3282017: `k4vi7z` (already finalized on its lane) failed on an additive-only `CHANGELOG.md` conflict, and `btth0a`'s lane conflicted with `sbo3hl` in `agent_workflows/upgrade_rehearsal.py` and `tests/test_aw_upgrade_test.py`; every hunk was keep-both and a human resolved them by hand. The runner already DETECTS the easy shape (`classify_conflict_hunk_shape`, `CONFLICT_SHAPE_ADJACENCY_ONLY`) and says keep-both is lossless, then stops anyway (`integrate_lane_branch`: "Nothing is RETRIED").
- Scope: IN: on a git merge conflict at merge-back of an EXECUTE lane, bring main into the lane (in the lane worktree, conflicts left for the agent), give the SAME agent a correction turn on its SAME session to resolve and commit, then re-run the normal merge-back (gate + suite + merge) under the integration lock; bounded by the run's existing `--retry-budget`; exhausted or refused = `fail-merge` exactly as today; both hosts; outcome tests; one CHANGELOG line. OUT: auto-resolving conflicts without an agent; review-lane conflicts; changing the gate, the suite or the integration lock; `aw <host> integrate` (the human path stays as is).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_merge_conflict_sendback.py, tests/test_runner_shared.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: next
- From-Backlog: xyv75i
- Work-Kind: bug
- Priority: high
- Set: mergeagent
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ounhsn

## Workflow history
- 2026-09-27 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xyv75i per maintainer ruling 2026-09-27: send a merge-back conflict back to the same agent under the existing retry budget.

- 2026-09-27 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A merge conflict between a lane's verified work and main is sent back to the agent that wrote the work, which resolves it in its own lane; the runner then re-runs the ordinary merge-back. The item fails only when the agent cannot resolve it within the run's existing retry budget.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prepare the lane

- [ ] E-01 Add `runner_shared.prepare_lane_for_conflict_resolution(repo, handle, *, run_checked) -> ConflictPrep` (NamedTuple: `ok`, `conflicted_paths`, `detail`). In the LANE worktree (`handle.path`), run `git merge --no-ff --no-commit <main tip>` where the tip is `git rev-parse main` read in `repo`. If the merge is clean (main moved but nothing now conflicts), commit it with subject `merge main into lane <id6> for merge-back` and return `ok=True, conflicted_paths=()`; the caller then simply re-attempts merge-back. If it conflicts, leave the markers in place, return `ok=True` with the conflicted paths from `git diff --name-only --diff-filter=U`. If git fails for any other reason, `git merge --abort` in the lane and return `ok=False`. Never touches main or the primary checkout. Main is NOT merged into by this function.
  - Depends on: none
  - Expected outcome: a pure lane-local helper; main's HEAD and the primary checkout are byte-identical before and after.
  - Execution state: pending

### Task group 2: ask the agent, then re-integrate

- [ ] E-02 Add `runner_shared.merge_conflict_question(conflicted_paths, *, shape, main_tip) -> str`, the prompt for the correction turn, in plain words: main moved while you worked and these files now conflict; main has been merged into your lane with conflict markers; for each file keep BOTH sides' intent (for a file the runner classified `adjacency-only`, say that keeping both sides in a sensible order is correct; otherwise say to read both sides and resolve on their merits, never keep both blindly); remove every conflict marker; run the tests your plan names; commit with `aw commit <plan id6> -- <paths>` (these paths may be outside your plan's Scope-Paths; that is expected for a merge and is recorded automatically); do NOT run `aw ipd begin`/`finalize`; then write the outcome file. Reuse `classify_conflict_hunk_shape` for the shape and `format_conflict_resolver_facts` for the per-file facts rather than re-deriving them.
  - Depends on: none
  - Expected outcome: one prompt builder; the only new wording in the run's prompts.
  - Execution state: pending

- [ ] E-03 In `execute_item_core`, at the execute-lane publish site (the `integrate_under_repository_lock(..., integrate=_publish, ...)` call and the `record_integration_refusal` branch that follows it), when `integ_kind == INTEGRATION_REFUSAL_CONFLICT` and the reason carries the `git-merge-conflict` cause token (`tag_integration_cause`), and the item has correction budget left (`frozen_retry_budget(state)` against a new durable counter `MERGE_CONFLICT_RETRY_COUNT_KEY` on the ITEM, counted before the turn so a crash cannot yield a free retry): call E-01; if it returns conflicts, ask E-02's question through the SAME in-lane follow-up mechanism the gate-answer turn uses (`resume_via_launcher(raw_launcher, ...)` with `work_dir=<lane>`, the attempt's own session, `log_suffix/label_suffix="merge-conflict"`, host-specific argument shapes exactly as `perform_gate_answer`'s caller passes them); then recollect lane submissions; verify no conflict markers remain and the lane has no unmerged paths (`git diff --name-only --diff-filter=U` empty and `git grep -nE '^(<<<<<<<|>>>>>>>)' -- <conflicted paths>` empty); then re-run the SAME `integrate_under_repository_lock(..., integrate=_publish)` call (gate, suite and merge, inside the lock, main re-read). Loop while conflicts recur and budget remains. If E-01 returned a clean merge, skip the ask and re-run `_publish` directly (counts against the budget too). On exhaustion, an unresolved marker, `ok=False`, or a non-conflict refusal, fall through to the existing `record_integration_refusal` path unchanged, so the item ends `fail-merge` with today's reason and remedy plus a `merge_conflict_sendback` record listing each attempt. Record each attempt on the attempt as `attempt["merge_conflict_sendback"] = [{"conflicted": [...], "shape": ..., "resolved": bool}]` and emit `merge-conflict-sent-back` / `merge-conflict-resolved` / `merge-conflict-unresolved` events.
  - Depends on: E-01, E-02
  - Expected outcome: a conflicted execute lane gets up to `retry_budget` agent resolutions before it can end `fail-merge`; a budget of 0 behaves exactly as today.
  - Execution state: pending

- [ ] E-04 Keep the finalized plan finalized: the lane already moved the plan to `executed/` and committed its finalize before merge-back (`lane_holds_finalized_plan`), so the correction turn must not re-finalize. Assert in E-03's code path that it never calls `driver_finalize`/`finalize_with_contention_retry` and never re-issues `begin`; the finalize record on the lane is what merge-back publishes. Update `TURN_RETRY_CLASSIFICATION`'s `fail-merge` reason text to say a git merge conflict is first sent back to the agent under `--retry-budget` and is terminal only after that (the row stays `False`: this send-back happens inside the item's own integration, not as a re-dispatched turn). Update `integrate_lane_branch`'s "Nothing is RETRIED" comment to point at the send-back so the two do not contradict each other.
  - Depends on: E-03
  - Expected outcome: no double finalize; the documented behavior matches the code.
  - Execution state: pending

### Task group 3: tests and record

- [ ] E-05 Add `tests/test_merge_conflict_sendback.py`, OUTCOME tests only (no source-text pins), on BOTH hosts (`BOTH` / `_MODULES` as `tests/test_runner_shared.py` uses them), with the host spawn replaced by a fake that edits the lane (no real model; the suite forbids real spawns). Build the conflict the way `test_a_real_conflict_still_aborts_leaving_main_clean` does (lane and main both write `clash.txt`). Cases: (a) the fake resolves (writes both lines, removes markers, commits) -> the item integrates, main contains both lines, `merge-conflict-resolved` event emitted, one agent ask recorded; (b) the fake does nothing -> after `retry_budget` asks the item is `fail-merge`, main unchanged, lane preserved, `merge-conflict-unresolved` recorded; (c) `--retry-budget 0` -> no ask at all, `fail-merge` exactly as before (the fake's call count is 0); (d) main moved on an UNRELATED file so E-01's merge is clean -> the item integrates with no agent ask. Update `test_merge_conflict_terminal_and_budget_independence` only if its assertions about `decide_integration_deferral` change; they should not, because the ladder is untouched.
  - Depends on: E-03, E-04
  - Expected outcome: four outcome tests pass on both hosts.
  - Execution state: pending

- [ ] E-06 Add one `- Changed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`, plain words, no em or en dashes: when a finished item's work conflicts with main, the run now hands the conflict back to the same agent to resolve in its lane and then merges it, instead of failing the item; it fails only if the agent cannot resolve it within the run's retry budget. Then run the bare suite and the leak sanitizer.
  - Depends on: E-05
  - Expected outcome: one line; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Follow-up agent turns inside an item's own integration already exist and are the template: the gate-answer turn (`perform_gate_answer`, asked via `resume_via_launcher` on the attempt's session in the lane, bounded by `--retry-budget`, maintainer ruling 2026-09-20 "share it, add no second knob").
- The retry budget is `run_recovery.DEFAULT_RETRY_LIMIT = 2`, frozen per run (`frozen_retry_budget`); `0` means no retries and must keep today's behavior.
- The integration lock (`integrate_under_repository_lock`) re-reads main's tip inside the lock; every publish goes through it.
- Conflict shape and resolver facts already exist (`classify_conflict_hunk_shape`, `build_conflict_resolver_detail`, `format_conflict_resolver_facts`, `conflict_resolver_remedy`); reuse them.
- Tests: outcome only (maintainer standing rule); both hosts; no real model spawns.
- Cite code by symbol; line numbers drift.

## Findings

| # | Location | Finding |
| --- | --- | --- |
| F-1 | `runner_shared.integrate_lane_branch` conflict branch | On `merge_in_progress`, after the records-only re-derivation fails, it aborts and returns `fail-merge` tagged `git-merge-conflict`; its comment says "Nothing is RETRIED ... Every other conflict class remains terminal on its first attempt." |
| F-2 | `decide_integration_deferral` / `classify_integration_refusal` | Only `merge-retry` and `merge-unchecked` defer; `fail-merge` is terminal on attempt 1 regardless of budget (pinned by `test_merge_conflict_terminal_and_budget_independence`). |
| F-3 | `TURN_RETRY_CLASSIFICATION` | `fail-merge` is `False`: "integration refused; owned by the integration deferral ladder or human". |
| F-4 | measured 2026-09-27 | `k4vi7z` (CHANGELOG, additive-only) and `btth0a` (two files, additive-only unions with `sbo3hl`) were resolved by hand as keep-both; `tests/test_aw_upgrade_test.py` 46 passed after the union. |
| F-5 | `conflict_resolver_remedy` | Already tells a human to keep both sides for an adjacency-only set; that advice becomes the agent's instruction instead. |

## Proposed changes (ordered, validatable)

1. E-01 lane-local merge of main with conflicts left for the agent.
2. E-02 the correction question.
3. E-03 the bounded send-back loop at the execute publish site; E-04 no re-finalize and aligned docs.
4. E-05 outcome tests; E-06 CHANGELOG and suite.

## Deferred / out of scope (with reason)

- Automatic keep-both resolution without an agent for adjacency-only conflicts.
  - Carrier-Declined: the maintainer chose agent resolution; an agent turn is cheap relative to a stranded item and also covers non-additive conflicts.
- Review-lane conflicts (`integrate_review_lane_branch`).
  - Carrier-Declined: review lanes write plan and review records only, and none were measured conflicting; nothing is outstanding.
- Changing `aw <host> integrate` (human re-integration).
  - Carrier-Declined: it remains the manual path after a `fail-merge`; the send-back happens before that point.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_merge_conflict_sendback.py`, four cases on both hosts with a fake agent, asserting what ends up on main, the item's status, and whether the agent was asked. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended: spec `25kzda` records `fail-merge` as the status for an unresolved conflict, which stays true (it is now reached only after the send-back). CHANGELOG gains one line.

## Open questions

### OQ-01: Should a merge conflict go back to the agent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-27 BY THE MAINTAINER when asked directly: yes, send it back to the same agent, bounded by the existing retry budget.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a scratch run (or test output) of `prepare_lane_for_conflict_resolution` on a lane/main pair that conflicts, showing `conflicted_paths == ('clash.txt',)`, markers present in the lane file, and `git -C <repo> rev-parse HEAD` unchanged before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered question for one adjacency-only and one semantic conflict, showing the file list and the two different resolution instructions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste E-05 cases (a) and (b) passing (node ids, both hosts) and the `merge_conflict_sendback` record from case (a).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste E-05 case (a)'s evidence that finalize was not called a second time (the fake finalize double's call count, or no second `lifecycle(<id6>): finalize` commit in `git log`), plus the updated `TURN_RETRY_CLASSIFICATION` row text.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_merge_conflict_sendback.py -o addopts="" -v` showing all cases passed on both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff CHANGELOG.md`, `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing, the final summary line of a BARE `python3 -m pytest` with 0 failed, and `aw sanitize --agent` exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, what happens when verified work conflicts with main at merge-back; the helper, the question and the loop are one mechanism.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a run spends up to `--retry-budget` (default 2) extra agent turns on an item whose verified work conflicts with main, and those turns may edit files outside the plan's Scope-Paths to resolve the merge; `fail-merge` is now reached only after that.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit ounhsn -- <paths>`; never `git add -A`, never push. The runner owns finalize in a lane. After execution set backlog `xyv75i` `done` with `--evidence` citing the executed plan (it carries `Blocks-Release: next`).

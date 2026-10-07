# IPD: Detect untooled status changes and hook-skipping commits in a lane and send them back

- Date: 2026-10-07
- Kind: child
- Concern: Two rule breaks the spec says abort a run are not detected at all. (1) An agent that hand-edits a plan's `- Status:` or `git mv`s a plan between lifecycle directories is not caught by the runner: `outcome_precedence_disposition` trusts a plan found in `superseded/`/`not-executed/` by directory alone and lands it as `retired`, and a plan found in `executed/` turns a refused finalize into success through `finalize_already_done`. The only detectors (`check_engine.check_status_untooled`, the `status_untooled_gate` and `executed_transition_gate` hooks) are commit-scoped, local and skippable. (2) A lane commit made with `--no-verify` is not detected: `RUN-COMMIT-GATEWAY` is `UNBOUND_BY_DEPENDENCY`. The maintainer ruled on 2026-10-07: detect them, tell the agent to undo and redo with the proper tool, continue.
- Scope: After each execute turn and before finalize or integration, check the lane's commits since the turn began for (a) plan status or lifecycle-directory changes with no matching tool-written history line or finalize journal, reusing the shared predicates behind `check_status_untooled` and `executed_transition_gate`, and (b) commits whose staged content the repository's pre-commit hooks would refuse, by re-running those hooks over each lane commit's changed files; send any finding back as a fix-it turn (Order 03) with the specific undo-and-redo instruction; stop trusting a plan's directory alone in `outcome_precedence_disposition` and `finalize_already_done`. EXCLUDES push detection (Set `denypush`) and making the local hooks mandatory.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/check_engine.py, agent_workflows/run_evidence.py, tests/test_lane_rule_break_detection.py
- Item-Dependencies: executed:mcbph5
- Status: draft
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 62sdwr

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

If an agent hand-edits a plan's status, moves a plan by hand, or commits around the hooks, the runner notices before the work is finalized or merged and tells the agent to undo it and use the proper tool.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: untooled status changes

- [ ] E-01 In `check_engine`, expose a range-scoped form of the untooled-status predicate: given a base and head commit, return one finding per plan whose `- Status:` or lifecycle directory changed in that range with no matching tool-written `## Workflow history` line (intermediate statuses) or no finalize journal (`executed`). Reuse the existing predicate code; do not write a second rule.
  - Depends on: none
  - Expected outcome: over a scratch range containing one tooled and one hand-edited status change, and one hand `git mv` into `executed/`, the function returns exactly the two untooled ones.
  - Execution state: pending

- [ ] E-02 In the runner, after an execute turn and before finalize, run E-01 over `lane_starting_head..HEAD` of the lane; on any finding, send the item back with Order 03's message (kind `untooled-status-change`) naming each plan and the instruction: "revert the hand edit or move, then use `aw ipd set <status> <id6>` (or `aw ipd finalize`)". Make `outcome_precedence_disposition` and `finalize_already_done` require the tooled evidence, not the directory alone.
  - Depends on: E-01
  - Expected outcome: a lane that `git mv`s its own plan into `executed/` gets a fix-it turn instead of being scored executed; after the agent reverts and the driver finalizes, the item executes normally.
  - Execution state: pending

### Task group 2: hook-skipping commits

- [ ] E-03 After an execute turn, for each lane commit since `lane_starting_head`, re-run the repository's configured pre-commit hooks over that commit's changed files (`pre-commit run --from-ref <parent> --to-ref <commit>` when pre-commit is configured; otherwise skip and record that hook checking was unavailable). A commit the hooks refuse is a hook-skipping commit. Send the item back with Order 03's message (kind `hook-bypass`) carrying the hook output and the instruction: "the commit <sha> does not pass the hooks; fix what they report and recommit through `aw commit` (amend or add a fix commit; do not use --no-verify)".
  - Depends on: none
  - Expected outcome: a lane commit made with `--no-verify` over a file a hook refuses yields a fix-it turn with the hook output; a clean lane yields none; a repo without pre-commit yields none and records "unavailable".
  - Execution state: pending

- [ ] E-04 Bind `RUN-COMMIT-GATEWAY` in `run_evidence` to E-03's check rather than leaving it `UNBOUND_BY_DEPENDENCY`, with its action cell matching the spec as amended by Order 01.
  - Depends on: E-03
  - Expected outcome: `RUN-COMMIT-GATEWAY`'s binding names the new predicate; `tests/test_run_finding_spec_transcription.py` passes.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_lane_rule_break_detection.py` driving the real runner with a scripted host that (a) hand-edits a plan status, (b) `git mv`s its plan into `executed/`, (c) commits with `--no-verify` past a refusing hook, and (d) does everything through the tools; assert on fix-it turns, delivered prompt text and final status. No source introspection.
  - Depends on: E-02, E-04
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One predicate, many surfaces: `status_untooled_gate` delegates to `check_engine.check_status_untooled` so the hook and the check cannot diverge; the runner joins that pattern.
- `RUN-NO-PUSH` was retired because a presence check was being passed off as enforcement (`run_evidence` comment); E-03 re-runs the real hooks, which is a behavior check, not a presence check.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Lifecycle directory alone decides `retired` and `executed` in the lane. | `outcome_precedence_disposition`; `finalize_already_done` / `plan_already_finalized` check the bucket only (survey 2026-10-07). |
| F-02 | The untooled-status detectors are commit-scoped and local only. | `hooks/status_untooled_gate.py` docstring "Git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`"; `check_engine.check_status_untooled` compares the staged index against HEAD. |
| F-03 | Hook bypass is not detected. | `run_evidence` `RUN-COMMIT-GATEWAY` `binding=UNBOUND_BY_DEPENDENCY`, waiting on "a captured commit-gateway RECEIPT". |
| F-04 | Maintainer ruling 2026-10-07: detect hand edits and bypass now; undo and redo with the tools; continue. Push stays with `denypush`. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Range-scoped untooled-status predicate (E-01).
2. Runner check and send-back; stop trusting directory alone (E-02).
3. Re-run hooks over lane commits (E-03).
4. Bind `RUN-COMMIT-GATEWAY` (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Push detection.
  - Carrier: oq05nc

## Scope check

- Over-scope: none. `check_engine.py` E-01; `runner_shared.py` E-02, E-03; `run_evidence.py` E-04; the test module E-05.
- Under-scope: a bypass whose content would pass the hooks is not distinguishable from a normal commit and does not matter for this purpose; recorded rather than chased.

## Required tests / validation

- `python3 -m pytest tests/test_lane_rule_break_detection.py tests/test_run_finding_spec_transcription.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: spec `25kzda` 5.5/5.7 and the Section 4.2 action cells are amended by Order 01.

## Open questions

### OQ-01: Is re-running hooks per lane commit too slow?

- Blocking: no
- Status: open
- Owner: executor of E-03
- Resolution or deferral rationale: Measure at execution on a real lane and record the time. The runner already runs the full suite at merge, so a hook pass over changed files is expected to be small; if it is not, run it once over `lane_starting_head..HEAD` instead of per commit and record that choice.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's findings over the scratch range.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the delivered fix-it prompt for the hand `git mv` case and the item's final status after the agent reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fix-it prompt with hook output for the `--no-verify` case, the clean case showing no finding, the no-pre-commit case showing "unavailable", and the measured hook-pass time for OQ-01.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `RUN-COMMIT-GATEWAY`'s binding and the passing transcription test.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module runs with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.

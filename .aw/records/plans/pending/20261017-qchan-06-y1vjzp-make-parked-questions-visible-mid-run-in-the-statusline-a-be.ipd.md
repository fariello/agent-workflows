# IPD: Make parked questions visible mid-run in the statusline, a bell, aw runs questions and aw attention

- Date: 2026-10-17
- Kind: child
- Concern: A parked question that nobody notices is never answered. Spec `6kwd2e` R4a (mid-run visibility) and R9.6 require a live parked-question count on the runner statusline that names `aw runs answer <run-id>`, one terminal bell on the first park (TTY only, suppressed by presentation overrides), and `aw attention` to surface parked questions for active runs under an explicit label rather than the truncated raw-status fallback, without folding them into `blocked` (OQ-01 ruling) and without touching the artifact's own status.
- Scope: IN: statusline count and hint (`render_stream.Statusline` / `format_statusline_lines`), the once-per-run bell, `attention.get_active_runs_map` label for `awaiting-human` and a parked-question count in the attention output. OUT: off-machine notification (Orders 09-11).
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/attention.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_question_visibility.py
- Item-Dependencies: executed:mtmqlm
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 6
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: y1vjzp

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a waiting question visible on the console the human walked away from and in the standing 'what needs attention' view (spec `6kwd2e` R4a.3-R4a.6, R9.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the runner console

- [ ] E-01 Extend the statusline to show `? N questions` when N > 0 parked questions exist in the run (read from the queue items' open questions), styled as waiting-input, with the hint `answer: aw runs answer <run-id>` on the bottom border, on both hosts.
  - Depends on: none
  - Expected outcome: a rendered statusline for a state with 3 parked questions contains `3 question` and `aw runs answer <run-id>` (A10d, A46).
  - Execution state: pending

- [ ] E-02 Emit one BEL (`\a`) on the first park of a run and never again in that run (persist `bell_rung` in state so a resume does not ring again), only when the output stream is a TTY and color/presentation overrides (`--plain`, `NO_COLOR`-style quiet modes the runners already honor) do not suppress it.
  - Depends on: E-01
  - Expected outcome: with a TTY stream the bell byte appears exactly once across three parks; with a non-TTY stream it never appears (A10e, A10f).
  - Execution state: pending

### Task group 2: aw attention

- [ ] E-03 In `attention.get_active_runs_map` map `awaiting-human` to an explicit label (`question`), not the truncation fallback and not the `blocked` group, and add a parked-question count for active runs to the attention output (human and `--format json`). Do NOT change any artifact's native status (A10h).
  - Depends on: E-02
  - Expected outcome: `aw attention` for a repo with an active run holding one parked item shows the `question` label and a count of 1; the item's artifact status and cross-tree class are unchanged (A10g, A10h).
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_question_visibility.py`: statusline rendering with counts and hint, bell once on TTY and never on non-TTY (capture the stream), and `aw attention` against a fixture run directory with a live driver lock.
  - Depends on: E-03
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The statusline is the single live surface; do not add a second one (spec `6kwd2e` R4a.3).
- `aw attention` classes come from the artifact's own status; run dispositions belong to the live-run column (spec `6kwd2e` R4a.6 correction).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `get_active_runs_map` falls through to a truncated raw string for unknown statuses, so `awaiting-human` would render as `awaitin` today (spec `6kwd2e` R4a.6).
- No notification surface exists in the runners (research `xjsc9k`).

## Proposed changes (ordered, validatable)

1. E-01 statusline. 2. E-02 bell. 3. E-03 attention. 4. E-04 tests.

## Deferred / out of scope (with reason)

- Push and chat notification: Orders 09-11.
  - Carrier: txl556, qrup8m, mrlblc

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_visibility.py tests/test_statusline_stop_tally.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R4a.3-R4a.6 and R9.6 as amended.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the rendered statusline text for the 3-question fixture showing the count and the `aw runs answer` hint.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the byte count of `\a` in the captured TTY stream (1) and in the non-TTY stream (0) after three parks, plus the persisted `bell_rung` field after a simulated resume.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw attention` human and `--format json` output for the fixture, and the artifact's `- Status:` line before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.

# IPD: Make aw doctor report a found leak instead of a probe crash

- Date: 2026-09-25
- Kind: child
- Concern: `doctor.probe_sanitizer` builds each Drift from `f.matched`, but `leak_sanitizer.Finding` has `location`, `rule`, `severity` and `snippet` and no `matched`. The first finding raises AttributeError, the blanket `except` turns it into `doctor.probe-failed`, and agent/JSON consumers see a broken probe instead of `doctor.leak-<rule>`. (The human render still lists the leak, because `res.findings` is set before the loop.)
- Scope: IN: read `f.snippet` (bounded); stop the blanket except from masking programming errors; a regression test. OUT: sanitizer rules.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: doctorleak
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: rpqv4q
- From-Backlog: muwwa5
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog muwwa5. Reproduced at HEAD in a scratch repo with a planted home path: `probe_sanitizer` returned only `doctor.probe-failed` with detail `'Finding' object has no attribute 'matched'`. Corrects the item: the human render does show the leak; the agent/drift channel does not.

## Goal

`aw doctor --agent` reports each leak as `doctor.leak-<rule>`, so automation sees it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix and test

- [ ] E-01 In `doctor.probe_sanitizer`, build the Drift detail from `f.snippet` truncated to 120 characters, and narrow the `except` so it catches only errors from `leak_sanitizer.scan_working_tree` itself (not attribute errors in the loop that consumes its result).
  - Depends on: none
  - Expected outcome: a leak yields `doctor.leak-<rule>`; a genuine scan failure still yields `doctor.probe-failed`.
  - Execution state: pending

- [ ] E-02 Add a test in `tests/test_doctor.py`: a temp git repo with one committed file containing a home-directory path; assert `probe_sanitizer(repo).drift` contains a `doctor.leak-home-path` Drift and no `doctor.probe-failed`.
  - Depends on: E-01
  - Expected outcome: test passes; fails against the pre-change code.
  - Execution state: pending

- [ ] E-03 Run `python3 -m agent_workflows doctor --agent` on this repository and the bare suite.
  - Depends on: E-02
  - Expected outcome: no `doctor.probe-failed` for the sanitizer; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The leak-sanitizer is the authority for leak findings (AGENTS.md, Leak-sanitizer awareness); doctor only reports them.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `doctor.probe_sanitizer` | Reads a field `Finding` does not have. | `leak_sanitizer.Finding` fields: location, rule, severity, snippet |
| F-2 | MED | `doctor.probe_sanitizer` | The blanket `except Exception` converted a programming error into a plausible-looking probe failure. | scratch repo run: only `doctor.probe-failed` |

## Proposed changes (ordered, validatable)

1. E-01: read snippet; narrow the except.
2. E-02: regression test.
3. E-03: live doctor run; bare suite.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_doctor.py -o addopts="" -q` plus the V-02 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the doctor sanitizer probe's field names.

## Open questions

### OQ-01: How much of the snippet belongs in the Drift detail?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: 120 characters, resolved from repository evidence: that is the bound the same function already applies to the probe-failed detail (`str(exc)[:120]`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test passing; restore `f.matched` IN THE WORKTREE and paste it FAILING; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the doctor diagnostics lines mentioning `sanitizer` or `leak`, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

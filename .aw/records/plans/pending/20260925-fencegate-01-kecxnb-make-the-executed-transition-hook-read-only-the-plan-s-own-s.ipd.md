# IPD: Make the executed-transition hook read only the plan's own Status line

- Date: 2026-09-25
- Kind: child
- Concern: The pre-commit hook `hooks/executed_transition_gate.py` decides a plan gained `executed` by `_has_executed_status`, which matches ANY line equal to `- Status: executed`, including one quoted inside a code fence. A plan that quotes that line (as lifecycle docs and reviews do) is refused as a raw transition.
- Scope: IN: `_has_executed_status` reads only the metadata region's `- Status:`; tests. OUT: the rest of the hook's logic.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: fencegate
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: kecxnb
- From-Backlog: 4vhe5o
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4vhe5o. Reproduced at HEAD: `_has_executed_status` on a plan whose own Status is `approved` but which quotes `- Status: executed` in a fence returns True.

## Goal

The hook refuses a real raw `executed` transition and never refuses a plan for quoting one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix and test

- [ ] E-01 Change `_has_executed_status` to read the status from the record's metadata region via `selectors.metadata_region(text)` (the toolkit's ONE metadata boundary), matching the first `- Status:` bullet there, case-insensitively, against `executed` or its `done` alias.
  - Depends on: none
  - Expected outcome: a fenced or body-level `- Status: executed` no longer counts; the metadata one still does.
  - Execution state: pending

- [ ] E-02 Add `tests/test_executed_transition_gate.py` with those two cases plus (c) a `done` alias in metadata -> True and (d) an OQ block's own `- Status: open` below the metadata with metadata `executed` -> True.
  - Depends on: E-01
  - Expected outcome: four cases pass; (a) fails against the pre-change function.
  - Execution state: pending

- [ ] E-03 Run the bare suite.
  - Depends on: E-02
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.metadata_region` is documented as the ONE boundary every identity/status reader is bounded to; reusing it keeps this hook consistent with every other status reader.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `executed_transition_gate._has_executed_status` | Matches any matching line anywhere in the file. | `_has_executed_status('- Id: abcdef\n- Status: approved\n...```text\n- Status: executed\n```\n') -> True` |
| F-2 | INFO | sibling detector | The untooled-status detector (`check_engine._status_meta`) already takes the first match, so it does not share this defect for a plan with front-matter Status. | read `_STATUS_META_RE` use |

## Proposed changes (ordered, validatable)

1. E-01: bound the status read to the metadata region.
2. E-02: behavior tests.
3. E-03: bare suite.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_executed_transition_gate.py -o addopts="" -q` plus the V-02 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: the ipd-lifecycle spec already says a plan's status is its metadata `- Status:`; this makes the hook read that line and nothing else.

## Open questions

### OQ-01: Use `ipd_lint._structural_lines` (fence-aware) or `selectors.metadata_region`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `selectors.metadata_region`, resolved from the code: it is documented as the single boundary for identity/status readers, and a status is a metadata field, so a fence-aware whole-file scan would still wrongly count a body-level status line.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c` driving `_has_executed_status` on (a) metadata `approved` + fenced `executed` -> False and (b) metadata `executed` -> True.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test run passing; revert E-01 IN THE WORKTREE and paste case (a) FAILING; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

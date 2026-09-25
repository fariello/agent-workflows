# IPD: Let aw specs set record and inherit From-Backlog on both spellings

- Date: 2026-09-25
- Kind: child
- Concern: `aw specs set` has no `--from-backlog` flag, so a spec that graduates from a backlog item cannot record the link through a setter or inherit the item's release gate. The bare `aw specs set <status> <sel>` spelling routes through `status_set` (which already writes the field when told to), but the `--status` spelling routes through `specs.run_set`, which has no writer for it.
- Scope: IN: register `--from-backlog` on `specs set`; write it (and inherit `Blocks-Release` the way `aw ipd set --from-backlog` does) on BOTH spellings; declare the flag in `command_surface`; tests. OUT: `aw specs new`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/specs.py, agent_workflows/command_surface.py, tests/test_specs_from_backlog.py, AGENTS.md, .aw/records/specs/README.md, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- Set: specfb
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: uruqaz
- From-Backlog: mod4ml

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog mod4ml. Verified at HEAD: `specs set --help` has no `--from-backlog`; the `--status` path in `specs.run_set` writes Priority, Work-Kind and Graduated-To but not From-Backlog.

## Goal

A spec-first graduation records its backlog source and carries the item's release gate through the same setter a plan uses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: flag and writers

- [ ] E-01 Register `--from-backlog` on the `specs set` parser in `cli.py` (same help text shape as `ipd set`) and add it to the `specs set` `legacy_flags` in `command_surface.py`.
  - Depends on: none
  - Expected outcome: `aw specs set --help` lists `--from-backlog`.
  - Execution state: pending

- [ ] E-02 In `specs.run_set` (the `--status` spelling), write the field through `releases.set_from_backlog_line` beside the existing Work-Kind/Graduated-To writers, validate the id6 against `backlog.existing_backlog_ids`, and inherit the item's `Blocks-Release` through `backlog.blocks_release_of_item` when the spec has none and none was passed, printing the same inheritance line `status_set` prints.
  - Depends on: E-01
  - Expected outcome: both spellings write the field and inherit the gate identically.
  - Execution state: pending

### Task group 2: tests and docs

- [ ] E-03 Add `tests/test_specs_from_backlog.py`: for each spelling, a spec plus a gated backlog item; `--from-backlog <id6>` writes `- From-Backlog:` and inherits `- Blocks-Release:`; an unknown id6 is refused.
  - Depends on: E-02
  - Expected outcome: all pass; the `--status` case fails before E-02.
  - Execution state: pending

- [ ] E-04 Grep the records READMEs and `AGENTS.md` for any statement that a spec cannot record `From-Backlog` through a setter; correct each hit found (measured at authoring: AGENTS.md's Release gates section says a spec is an equally valid carrier and makes no such claim, so there may be none). Then run the bare suite.
  - Depends on: E-03
  - Expected outcome: docs match behavior; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The two `aw specs set` spellings route to different handlers (`status_set.run_set_command` vs `specs.run_set`), and every field writer must exist on both, as the existing `Graduated-To` comment in `specs.run_set` explains.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `cli` `specs set` | No `--from-backlog` flag. | `specs set --help` |
| F-2 | LOW | `specs.run_set` | No From-Backlog writer on the `--status` path. | read `specs.run_set` |

## Proposed changes (ordered, validatable)

1. E-01: register and declare the flag.
2. E-02: writer and gate inheritance on the --status path.
3. E-03: tests for both spellings.
4. E-04: doc check; bare suite.

## Deferred / out of scope (with reason)

- `aw specs new --from-backlog`.
  - Carrier-Declined: a spec created from an item can set the field with the setter immediately after; one route is enough to close the gap mod4ml names.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_specs_from_backlog.py -o addopts="" -q` plus the V-03 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec text changes. E-04 corrects any README or AGENTS.md sentence that says specs lack a setter route; none was found at authoring, so it may be a no-op.

## Open questions

### OQ-01: Should the flag accept `-` to clear?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, resolved from the sibling: `aw ipd set --from-backlog -` clears, and a spec's From-Backlog is optional, so the two setters stay symmetric.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `--help` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the run passing; revert E-02 IN THE WORKTREE, paste the `--status` case FAILING; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the grep with each hit fixed or stated as none, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

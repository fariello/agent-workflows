# IPD: Let an agent propose a gate, tool or approach change and land that one record on main

- Date: 2026-10-07
- Kind: child
- Concern: When an executing agent concludes it cannot finish without a gate, an `aw` tool or the approach changing, nothing durable captures that. Measured 2026-10-07: the outcome file's `defect_report` findings carry only `what`/`where`, are stored in the gitignored run directory, and nothing reads them (`runner_shared.defect_report_record` docstring admits the reader "is unscoped"); an agent told to run `aw backlog new` produces an item that reaches main only if the lane merges, and in the stuck case the lane usually does not. So the maintainer cannot see the proposal and the agent has no sanctioned alternative to editing the gate itself.
- Scope: Add a structured `proposal` field to the execute outcome file; have the runner validate it and file it as a tracked record (a pending plan for a small fix with no behavior change, a backlog item for everything else) on main through a coordinator worktree, independent of whether the lane merges; then stop that item as `needs-human` with dependents skipped and independent items continuing; and surface it in the run summary. EXCLUDES the fix-it message text (Order 03), every new retry class (Orders 04 to 07), and spec `6kwd2e`'s mid-run question pause.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_run_proposal_channel.py, CHANGELOG.md
- Item-Dependencies: executed:tb6lw3
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tha7a6

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An agent that believes a gate, tool or approach must change can say so in its outcome file, and the runner turns that into a tracked plan or backlog item on main that the maintainer sees in `aw attention`, without the agent being authorized to make the change and without dirtying main.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the field and its validation

- [ ] E-01 In `agent_workflows/runner_shared.py`, define the outcome-file `proposal` field and a pure validator beside `validate_defect_report`. Shape: `{"kind": "gate-change" | "tool-defect" | "different-approach", "blocked_by": <what refused or failed, verbatim>, "why": <why the cause cannot be fixed within scope>, "proposed_change": <what should change>, "paths": [<repo-relative paths it would touch>], "size": "small" | "material"}`. The validator never raises, returns a verdict naming each missing or malformed key, and treats an absent field as "no proposal". Add the field to the execute prompt's outcome schema next to `defect_report`.
  - Depends on: none
  - Expected outcome: a valid proposal, a malformed one and an absent one each return the documented verdict; the execute prompt names the field and its keys.
  - Execution state: pending

### Task group 2: land the record on main without the lane

- [ ] E-02 Add a coordinator performer that files a valid proposal as ONE tracked record on main, reusing the shape of `perform_coordinator_backlog_close`: a throwaway worktree cut from main's current tip, the record written by the real tool (`aw backlog new ... --apply`, or `aw ipd scaffold` plus the proposal text for `size: small`), committed there with hooks running, and published with `git merge --ff-only` under the integration lock. Bound the raced-tip retries as that function does. On a refused or exhausted publish, keep the record in the run directory and say so in the summary rather than writing to main any other way.
  CLASSIFY BY SIZE: `small` with no behavior change becomes a pending plan in its own Set with `Status: draft` (a human must review it; the runner never authors a `to-review` plan on an agent's say-so); everything else becomes an `open` backlog item. Both carry the run id, the item id6, the kept lane branch, and `blocked_by` verbatim, and inherit the item's `- Blocks-Release:` when its `Work-Kind` is `bug`.
  - Depends on: E-01
  - Expected outcome: in a scratch repo, a proposal from an item whose lane is NOT merged lands as exactly one commit on main containing exactly one new record; main's worktree is clean afterwards; a raced tip is rebuilt; a refused publish leaves main untouched and the record in the run directory.
  - Execution state: pending

### Task group 3: stop the item, continue the run

- [ ] E-03 When the outcome carries a valid proposal, or when a fix-it budget is exhausted and the last turn carried one, stop the item as `needs-human` (reusing `GATE_ANSWER_NEEDS_HUMAN` and render code `awaiting-human-decision` rather than adding a status to the closed `runner_shutdown.KNOWN_ITEM_STATUSES`), keep its lane branch, mark its dependents `dependency-not-met`, and continue independent items. Do NOT integrate the lane.
  - Depends on: E-02
  - Expected outcome: a two-item run where item A proposes and item B is independent ends with A `needs-human`, B executed, A's lane branch present, A's lane commits absent from main, and the proposal record present on main.
  - Execution state: pending

- [ ] E-04 Surface proposals in the run summary on both hosts: list each first, with the record's path and id6, `blocked_by`, and the command to view it. Wire it in `render_stream` beside the existing `awaiting-human-decision` remedy.
  - Depends on: E-03
  - Expected outcome: the end-of-run summary for the E-03 run names the proposal record path and id6 at the top.
  - Execution state: pending

### Task group 4: tests and changelog

- [ ] E-05 Add `tests/test_run_proposal_channel.py` driving the real runner with a scripted host (the `fake_opencode` pattern in `tests/test_silent_turn_observability.py`) for: a valid `material` proposal (backlog item on main), a valid `small` proposal (draft plan on main), a malformed proposal (no record, item handled as today), a raced tip, and the two-item continuation of E-03; plus a `CHANGELOG.md` entry. No source introspection.
  - Depends on: E-04
  - Expected outcome: the module passes; each case asserts on files on main, git log, item status and summary text.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Coordinator writes to main go through a throwaway worktree and `--ff-only` (`perform_coordinator_backlog_close`, `ipd_lifecycle._finalize_transaction`), never into the shared checkout.
- `runner_shutdown.KNOWN_ITEM_STATUSES` is closed; reuse a token rather than invent one.
- Tests drive the runner and assert on outcomes (GUIDING_PRINCIPLES P16).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Existing problem reports have no durable home and no reader. | `runner_shared.defect_report_record` stores into the queue item; `.aw/.gitignore` ignores run directories; no reader in `run_viewer`, `render_stream`, `attention` or `run_cli` (survey 2026-10-07). |
| F-02 | A mechanism already lands one record on main atomically, independent of the lane, which answers the maintainer's question "use the same lane but merge just the record". | `runner_shared.perform_coordinator_backlog_close`: writes in a coordinator worktree, commits with hooks, publishes with `git merge --ff-only`, classifies OK / REFUSED / RACED. Merging only part of the LANE branch is not possible without cherry-picking a lane commit whose parent is unmerged work, so the record is written fresh on main's tip instead. |
| F-03 | An agent-filed backlog item is stranded when its lane does not merge. | Backlog paths are outside the scope allowlist and ride only an integrated lane (survey 2026-10-07; example `p9ag41` reached main only because its lane merged). |
| F-04 | `needs-human` already exists as a gate answer with a render code and a summary remedy. | `runner_shared.GATE_ANSWER_NEEDS_HUMAN`; `render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE = "awaiting-human-decision"`. |
| F-05 | Maintainer ruling 2026-10-07: a small fix with no material functional impact becomes a plan; everything else a backlog item; the item stops needs-human and the run continues. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Field and validator (E-01).
2. Coordinator performer landing one record on main (E-02).
3. `needs-human` stop with continuation (E-03).
4. Summary surfacing (E-04).
5. Tests and changelog (E-05).

## Deferred / out of scope (with reason)

- Pausing a run to ask a human mid-run. That is spec `6kwd2e`; this plan stops one item and continues.
  - Carrier-Declined: spec `6kwd2e` is itself the carrier; nothing here defers its work.

## Scope check

- Over-scope: none. `runner_shared.py` by E-01 to E-03, both host modules by E-03 (re-export and wiring), `render_stream.py` by E-04, the test module and `CHANGELOG.md` by E-05.
- Under-scope: the message that tells agents to use this field is Order 03.

## Required tests / validation

- `python3 -m pytest tests/test_run_proposal_channel.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

Spec `25kzda` group (b) "agent proposal" is written by Order 01; this plan implements it and edits no spec. `CHANGELOG.md` records the user-visible effect.

## Open questions

### OQ-01: Should a `small` proposal land as `draft` or `to-review`?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: `draft`. A `to-review` plan must be review-ready (AGENTS.md), and the runner cannot vouch for an agent's proposal text; `draft` keeps a human in the loop and costs one `aw ipd set to-review`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing the validator's verdict for a valid, a malformed and an absent proposal, and the execute-prompt excerpt naming the field.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the scratch-repo transcript: `git log --oneline -2` and `git status --short` on main after a proposal from an unmerged lane, the new record's path, and the raced and refused cases.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two-item run's final item statuses, `git branch --list 'aw/lane/*'`, and proof that A's lane commits are not on main.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the end-of-run summary text showing the proposal first.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module run with per-test counts, the bare-suite summary line, and the `CHANGELOG.md` diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.

# IPD: merge plans into ipd and rename list-repos and todo alias

- Date: 2026-08-18
- Kind: child
- Concern: awcmdsurf Order 04 (spec 20260818-1525-01, D2/D4/D5). Merge the `aw plans` board into the `aw ipd` noun (a plan IS an ipd); rename `aw list` -> `aw list-repos`; make `aw todo` an alias of `aw attention`. Additive here (new names added; old `plans`/`list`/`todo` removed in Order 05 for a clean cutover, EXCEPT `plans` whose board relocates to `ipd` and is removed in 05).
- Scope: cli.py parser + dispatch + the plans board function. IN: expose the board (`_run_plans`, cli.py:2810) under `aw ipd` (bare `aw ipd` or `aw ipd board`) defaulting to pending+reusable (item 8); add `aw list-repos` (same handler as `list`, `_run_list` cli.py:2579); make `aw todo` run the attention board (attention.run). OUT: removing the old `plans`/`list`/`todo` verbs (Order 05); the ipd authoring subverbs (unchanged: lint/scaffold/sync); attention's own upgrades (Set F).
- Status: reviewed
- Set: awcmdsurf
- Order: 4
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1njmzt

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from spec 20260818-1525-01 + investigation (_run_plans cli.py:2810, ipd subparsers cli.py:686, _run_list cli.py:2579, attention.run).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against cli.py:686/2579/2810/4088 and attention.run; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Collapse the plan tooling under one noun and fix the two simple renames: `aw ipd` becomes the board +
authoring home (bare `aw ipd`/`aw ipd board` shows the readiness board, default pending+reusable);
`aw list-repos` replaces the too-generic `aw list`; `aw todo` becomes an alias of `aw attention`. Old
names stay reachable this Order (removed in Order 05) so intermediate states are runnable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: plans -> ipd board merge

- [ ] E-01 Add an `ipd board` subcommand (and make bare `aw ipd` route to it, resolving spec OQ-1 to "bare ipd = board") that invokes the existing plans board `_run_plans` (cli.py:2810). Wire the ipd subparser (cli.py:686-717) to accept `board` with the same options the old `plans` had (`dir`, `--status`, `--write-index`), plus default the board to PENDING + REUSABLE only when no `--status`/filter is given (item 8). Keep `ipd lint`/`scaffold`/`sync` untouched.
  - Depends on: none
  - Expected outcome: `aw ipd` and `aw ipd board` show the readiness board (default pending+reusable); `aw ipd board --status executed` shows executed; `aw ipd lint/scaffold/sync` unchanged.
  - Execution state: pending

### Task group 2: list-repos + todo alias

- [ ] E-02 Register `aw list-repos` bound to the existing `_run_list` handler (cli.py:2579) with the same `--recursive` option; add it to the dispatch chain. (The old `aw list` stays until Order 05.)
  - Depends on: none
  - Expected outcome: `aw list-repos` behaves exactly like the old `aw list`.
  - Execution state: pending
- [ ] E-03 Make `aw todo` run the attention board: change the `todo` dispatch (cli.py:4088) to call `attention.run(args)` (like `aw att`), preserving `--agent`/`--all`. (Item 32; item 5/D5.) Note in help that `todo` is an alias of `attention`. The operational action LEDGER verbs (`show`/`complete`/`dismiss`/`reopen`/`history`) are unaffected.
  - Depends on: none
  - Expected outcome: `aw todo` shows the attention board identical to `aw attention`; `--agent`/`--all` honored.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Update help/description text for the merged `ipd` noun and the two renamed verbs (short strings only; full help quality is Set B): `ipd` description mentions the board + authoring; `list-repos` description; `todo` marked as an attention alias.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: `aw ipd --help`/`aw list-repos --help`/`aw todo --help` describe the new roles.
  - Execution state: pending
- [ ] E-05 Add `tests/test_awcmdsurf_merge_and_renames.py`: `aw ipd board` == old `aw plans` board output (default pending+reusable), `aw ipd` bare routes to board, `aw list-repos` == `aw list`, `aw todo` == `aw attention`. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new module passes; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The board is `_run_plans` (cli.py:2810), currently reached via `aw plans` (cli.py:545/4112) with `--pending`/`--status`/`--write-index`.
- `ipd` is already a true subparser noun (cli.py:686) with lint/scaffold/sync; adding `board` is natural.
- `_run_list` (cli.py:2579) backs `aw list` (cli.py:532/4106); `aw list-repos` reuses it.
- `attention.run` backs `aw attention`/`aw att` (cli.py:4196); `todo` currently backs `_run_todo` (cli.py:3479, the ACTION ledger list) - D5 repoints `todo` to attention. The action-ledger LISTING folds into attention (which already scans actions, attention.py:166-209), so no capability is lost.
- Item 8 (board defaults to pending+reusable) is implemented here as part of the board's default filter.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Board logic already exists (`_run_plans`). | The merge is re-exposing it under `ipd board`, not a rewrite. |
| F2 | `todo` currently lists the action ledger. | Repointing to attention is safe because attention already scans the actions tree; the ledger listing is not lost. |
| F3 | Item 8 (default pending+reusable). | Implemented as the board's default filter when no status is given. |

## Proposed changes (ordered, validatable)

1. `ipd board` + bare-ipd routing, default pending+reusable (E-01). 2. `list-repos` (E-02). 3. `todo`->attention (E-03). 4. Help text (E-04). 5. Tests + suite (E-05).

## Deferred / out of scope (with reason)

- Removing old `plans`/`list`/`todo`(old behavior): Order 05.
- ipd authoring subverbs: unchanged. Attention upgrades: Set F. Help-text quality: Set B.

## Scope check

- Over-scope: none - only the merge + two renames.
- Under-scope: none - board reachable under ipd with the item-8 default; both renames functional.

## Required tests / validation

`tests/test_awcmdsurf_merge_and_renames.py` (E-05) + full serial suite. Each V pins one E.

## Spec / documentation sync

Short help strings updated (E-04); full grammar docs at Order 05. Spec stays draft.

## Open questions

### OQ-01: bare `aw ipd` = board or help? (mirrors spec/orchestrator OQ)

- Blocking: no
- Status: open
- Owner: maintainer (resolve at execution)
- Resolution or deferral rationale: Recommendation adopted here: bare `aw ipd` = board (preserves the old `aw plans` quick-glance); `aw ipd --help` shows subverbs. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd` and `aw ipd board` showing the board (default pending+reusable) and `aw ipd board --status executed`; confirm lint/scaffold/sync unaffected.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw list-repos` output matching `aw list`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw todo` output identical to `aw attention` (+ `--agent`).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the three `--help` descriptions (ipd/list-repos/todo).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full serial suite tail showing the new module + no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification + commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 04 of awcmdsurf; depends on 01.

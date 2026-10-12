# IPD: Refuse a backlog item whose Workflow history block holds no record

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in the tree refuses a backlog item whose `## Workflow history` block holds no record. Backlog `wkpcop` measured a suppressed same-status write leaving the heading with no record under it while `backlog.validate_item` returned no drift, and re-measured in this lane at HEAD `5ebf5364d`: after `aw backlog set <item> --status open --message "metadata only"` over an item whose only history-shaped line is indented, `backlog.validate_item(path, text)` returned `[]`. The item names a validation rule for this as "a cheap independent backstop". It is independent of the reader reconciliation in sibling `kgv213`: that plan removes the one measured route to the state, this plan makes any route to it visible.
- Scope: IN: (a) a new `backlog.validate_item` drift rule `backlog.history-empty` raised when the item's `## Workflow history` heading is ABSENT or its block holds no column-zero record, reading the block through `attention_contract.history_block` (added by `kgv213`) so the check and the writer agree on what a record is; (b) document the rule in the backlog README's validation section; (c) behavioral tests; (d) a CHANGELOG entry. OUT: the same rule for specs or plans (specs carry their own `aw specs check` and plans are fenced by `ipd_lint`; neither was measured empty); a fixer or migration (no tracked item violates the rule, F-02); refusing at write time in `status_set` (the writer fix is `kgv213`'s).
- Scope-Paths: agent_workflows/backlog.py, tests/test_backlog_history_empty_rule.py, .aw/records/backlog/README.md, CHANGELOG.md
- Item-Dependencies: executed:kgv213
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 3
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: v5m5y8

## Workflow history

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` as the item's suggested independent backstop. Live-corpus violation count measured as 0 of 967 tracked backlog items at HEAD `5ebf5364d`, so the rule refuses nothing that exists today. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an empty or missing `## Workflow history` block on a backlog item a validation error, so a writer defect that strips an item's provenance is caught by `aw backlog check` / `aw check` instead of passing silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [ ] E-01 `agent_workflows/backlog.py` (`validate_item`): before `return drift`, append `core.Drift(rel, "backlog.history-empty", <detail>)` when `A.history_block(text).records` is empty. The detail must distinguish "no `## Workflow history` heading" from "heading present but no column-zero `- YYYY-MM-DD ...` record in the block", and name the remedy (restore the records from git history; an indented line is not a record). If `kgv213` has not executed (no `attention_contract.history_block`), mark this item `blocked` and edit nothing.
  - Depends on: none
  - Expected outcome: `validate_item` reports `backlog.history-empty` on both empty shapes and nothing new on a conformant item.
  - Execution state: pending

### Task group 2: tests and docs

- [ ] E-02 `tests/test_backlog_history_empty_rule.py` (new): behavioral tests (P16) calling `backlog.validate_item` and the CLI. Cases: (a) a conformant item yields no `backlog.history-empty`; (b) heading with only an indented history-shaped line yields it; (c) heading with only blank lines then prose yields it; (d) no heading yields it; (e) `cli.main(["backlog","check","--dir",<root>])` over a temp repo holding case (b) exits nonzero and names the rule in its output, and over a repo of conformant items exits 0.
  - Depends on: E-01
  - Expected outcome: the new module passes.
  - Execution state: pending

- [ ] E-03 `.aw/records/backlog/README.md`: extend the `aw backlog check [--agent]` bullet's parenthesized rule list with `at least one column-zero history record [backlog.history-empty]`, matching the existing `[backlog.<rule>]` style.
  - Depends on: E-01
  - Expected outcome: README names the rule; no em or en dashes.
  - Execution state: pending

- [ ] E-04 `CHANGELOG.md`: one entry under the top pending section for the new rule.
  - Depends on: E-01
  - Expected outcome: one new line, no em or en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `backlog.validate_item` is a fail-closed shape checker with no repo root (comment "f7igdu design constraint" in it); rules are `core.Drift(rel, "backlog.<rule>", detail)`. It is consumed by `aw backlog check`, `check_engine` (record_type `backlog`), `set_records.promote` (validates BEFORE writing) and `runner_shared`.
- `check_engine` skips `README.md`, `INDEX.md`, `STATUS.md` (`_SKIP_NAMES`), so the backlog README (which has a heading and no record) is not validated as an item.
- Every backlog writer (`backlog.run_new`/`_render_item`, `status_set.apply_status_change` via `_prepend_workflow_history_entry`) emits at least one column-zero record, so a conformant write cannot trip the rule.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `validate_item` accepts an item with no history record. | In-lane probe at `5ebf5364d`: after the indented-fixture `aw backlog set`, `backlog.validate_item(p, p.read_text())` -> `[]`. |
| F-02 | No tracked backlog item would be refused. | Probe over all 967 tracked `*.backlog.md`: every file has the heading, and only `.aw/records/backlog/README.md` (not an item) has a block with no column-zero record. |
| F-03 | `set_records.promote` validates its rendered item before writing, and `_render_item` mints a `created` record, so the new rule does not affect promotion. | `set_records.promote`: `drift = _backlog.validate_item(dest, rendered)` before `atomic_write`. |

## Proposed changes (ordered, validatable)

1. E-01 adds the rule.
2. E-02 fences it; E-03 and E-04 document it.

## Deferred / out of scope (with reason)

- Specs and plans: not measured empty, and each has its own validator (`aw specs check`, `ipd_lint`); extending is a separate decision.
  - Carrier-Declined: neither tree was measured with an empty history block and each has its own validator
- Write-time refusal: the writer-side fix is `kgv213`; this plan is the read-side backstop the item asked for.
  - Carrier: kgv213
- Fixer/migration: F-02 shows nothing to fix.
  - Carrier-Declined: F-02 measures zero violating tracked items

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_backlog_history_empty_rule.py tests/test_backlog.py tests/test_history_block_bounding.py`, actual output pasted.
- The WHOLE BARE SUITE, `python3 -m pytest`, summary pasted, no new failure against the base.
- `aw backlog check` and `aw check` on the live corpus, output pasted, showing zero `backlog.history-empty` findings.

## Spec / documentation sync

`.aw/records/backlog/README.md` gains the rule (E-03). No spec governs backlog validation rules.

## Open questions

### OQ-01: Should a missing heading be refused, or only an empty block?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Both. F-02 shows every tracked item has the heading and every writer emits one, so refusing its absence costs nothing today and catches the same provenance loss.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the `git diff` of `validate_item`. PASTE `aw backlog check` output on the live repository showing no `backlog.history-empty` finding, and a direct `validate_item` call on the F-01 fixture showing the rule with its detail text. Runtime path: `backlog.run_check` -> `validate_item`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the pytest output of the new module passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `git diff .aw/records/backlog/README.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `git diff CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and depends on `kgv213` being executed (`- Item-Dependencies: executed:kgv213`). The executor is bound by the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit <plan> -- <paths>`, never push, paste actual runner output. Before the terminal transition `aw ipd lint --phase pre-transition` must conform. Under `aw oc run` / `aw agy run` the runner finalizes; manually, run `aw ipd finalize v5m5y8 ... --apply`. Do not set backlog `wkpcop` to `done`.

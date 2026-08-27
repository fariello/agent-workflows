# IPD: Add Priority to the spec contract plus aw specs set and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Specs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional spec metadata field reusing the shared `{high,medium,low}` vocab, with the `aw specs set` setter, `aw check`/`aw specs check` validation, and `_spec_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Spec contract (`specs.py`): recognize an optional `- Priority:` bullet, validated against shared `backlog.PRIORITIES` (import, do not fork); optional so existing specs are not mass-failed. (2) Setter: add `--priority <low|medium|high|->` to `aw specs set` (cli.py + specs.py), writing/clearing the bullet + appending history, consistent with how specs set writes typed fields. (3) Validation: `aw specs check`/`aw check` flag an out-of-vocab value. (4) Attention: populate `Item.priority` in `attention._spec_record` (:289) from the spec's `- Priority:`. Absent = unprioritized. Specs only; plans = child 01, research = child 03.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: draft
- Set: xprio
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rp859c

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `Priority` (shared low/medium/high vocab) to specs: contract recognition, `aw specs set --priority`, validation, and `_spec_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract + setter

- [ ] E-01 In `specs.py`, recognize an optional `- Priority:` bullet validated against shared `backlog.PRIORITIES` (import, do not fork); optional (existing specs without it stay conforming). Add `--priority <low|medium|high|->` to `aw specs set` (cli.py + specs.py), writing/clearing the bullet and appending a history record.
  - Depends on: none
  - Expected outcome: a spec may carry `- Priority: high` and `aw specs check` conforms; `aw specs set <spec> --priority medium` writes it, `--priority -` clears; absent stays conforming.
  - Execution state: pending

### Task group 2: check + attention

- [ ] E-02 Flag an out-of-vocab `- Priority:` value on a spec in `aw specs check`/`aw check` (validated against shared `backlog.PRIORITIES`), added to `validate_spec` (specs.py) alongside the existing status/gate checks. Note: `validate_spec` today ignores unrecognized bullets, so this explicit enum check is what catches a bad value.
  - Depends on: E-01
  - Expected outcome: `aw specs check`/`aw check` reports a finding for a spec carrying `- Priority: bogus` and reports none for `- Priority: high` or an absent Priority.
  - Execution state: pending
- [ ] E-03 Populate `Item.priority` in `attention._spec_record` (attention.py:289) from the spec's `- Priority:` line so the board labels a spec's priority (absent = unset). Scope note: reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a spec carrying `- Priority:`, matching backlog's label rendering; no label for an absent Priority.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab `backlog.PRIORITIES` (backlog.py:53) - reuse.
- Spec contract lives in `specs.py` (status enum, required sections, typed gates, history); add Priority as an optional recognized bullet there; `aw specs set` is the tool-owned writer.
- `attention._spec_record` (:289) builds the spec Item; populate its `priority` (Item.priority exists, :45).

## Findings

Same recognized-but-optional-field + setter + attention pattern as the plans child; spec-specific bits are the specs.py contract + `aw specs set` + `_spec_record`.

## Proposed changes (ordered, validatable)

1. `specs.py`: recognize optional `Priority` (shared vocab).
2. `cli.py`+`specs.py`: `aw specs set --priority` (write/clear + history).
3. `check_engine.py`/specs check: enum validation.
4. `attention.py`: populate `Item.priority` in `_spec_record`.
5. `tests/`: specs-check-clean with/without Priority; set/clear; invalid flagged; board shows spec priority.

## Deferred / out of scope (with reason)

- Plans Priority: child 01. Research Priority: child 03.

## Scope check

- Over-scope: none.
- Under-scope: none (specs field+setter+check+attention complete).

## Required tests / validation

- A spec with `- Priority: high` passes `aw specs check`; a spec without it also passes (optional).
- `aw specs set <spec> --priority medium` writes it; `--priority -` clears.
- `aw check`/`aw specs check` flag an out-of-vocab value.
- `aw attention` sorts/labels a spec by priority.

## Spec / documentation sync

- Document `Priority` in the spec contract docs + `aw specs set --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Handled at the orchestrator (OQ-01).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `aw specs check` on a fixture spec carrying `- Priority: high` showing conformance, and on a spec with NO Priority also conforming (optional). Pasted `aw specs set <fixture> --priority medium` run then the resulting `- Priority: medium` bullet AND the appended `## Workflow history` record, and `--priority -` showing the bullet removed. A grep proving `specs.py` imports `backlog.PRIORITIES` (no forked vocab literal).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted `aw specs check` (and `aw check`) over a fixture spec carrying `- Priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `- Priority: high` and no Priority showing NO such finding. Pasted new/updated test in tests/ asserting all three cases.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture spec carrying `- Priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a spec with no Priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`specs.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch the plans/research contracts (children 01/03) or the shared attention sort key. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.

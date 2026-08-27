# IPD: Add Priority to the spec contract plus aw specs set and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Specs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional spec metadata field reusing the shared `{high,medium,low}` vocab, with the `aw specs set` setter, `aw check`/`aw specs check` validation, and `_spec_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Spec contract (`specs.py`): recognize an optional `- Priority:` bullet, validated against shared `backlog.PRIORITIES` (import, do not fork); optional so existing specs are not mass-failed. (2) Setter: add `--priority <low|medium|high|->` to `aw specs set` (cli.py + specs.py), writing/clearing the bullet + appending history, consistent with how specs set writes typed fields. (3) Validation: `aw specs check`/`aw check` flag an out-of-vocab value. (4) Attention: populate `Item.priority` in `attention._spec_record` (:289) from the spec's `- Priority:`. Absent = unprioritized. Specs only; plans = child 01, research = child 03.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: draft
- Set: xprio
- Order: 2
- Highest E allocated: 02
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

- [ ] E-02 Flag an out-of-vocab Priority in `aw specs check`/`aw check`. Populate `Item.priority` in `attention._spec_record` (:289) from the spec's `- Priority:`.
  - Depends on: E-01
  - Expected outcome: `aw check` flags `- Priority: bogus` on a spec; `aw attention` sorts/labels a spec by priority.
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
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

# IPD: Add recognized-but-optional Priority to the IPD schema plus aw ipd set/scaffold and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Plans/IPDs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional IPD metadata field reusing the shared `{high,medium,low}` vocab, with the `aw ipd set` setter, scaffold emission (optional), `aw check` validation, and `_plans_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Schema: add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (NOT `META_REQUIRED`; recognized-but-optional like Scope-Paths/Blocks-Release), value validated against the shared `backlog.PRIORITIES = {high,medium,low}` (import the one vocab, do not fork). (2) Setter: add `--priority <low|medium|high>` to `aw ipd set` in cli.py + status_set.py using the hoisted status-branch-independent write (mirrors `--blocks-release`/`--from-backlog`) so it persists on a no-op transition; `-`/empty clears. (3) `aw check`: validate the enum (flag an out-of-vocab Priority on a plan). (4) Attention: populate `Item.priority` in `attention._plans_record` (:317) from the plan's `- Priority:` (attention.py already renders `Item.priority`, :45/:435). Absent = unprioritized. This child covers PLANS only; specs = child 02, research = child 03.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: draft
- Set: xprio
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 1b45el

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `Priority` (shared low/medium/high vocab) to IPDs: schema recognition, `aw ipd set --priority`, `aw check` enum validation, and `_plans_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema + setter

- [ ] E-01 Add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (not META_REQUIRED); validate its value against the shared `backlog.PRIORITIES` (import, do not fork). Add `--priority <low|medium|high|->` to `aw ipd set` (cli.py + status_set.py) via the hoisted status-branch-independent write; optionally emit it from scaffold.
  - Depends on: none
  - Expected outcome: an IPD may carry `- Priority: high` and lints clean; `aw ipd set <plan> --priority medium` writes it (persists on no-op), `--priority -` clears.
  - Execution state: pending

### Task group 2: check + attention

- [ ] E-02 Validate the Priority enum in `aw check` (flag an out-of-vocab value on a plan). Populate `Item.priority` in `attention._plans_record` from the plan's `- Priority:` so the board sorts/labels plans.
  - Depends on: E-01
  - Expected outcome: `aw check` flags `- Priority: bogus`; `aw attention` shows a plan's priority label/sort.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab: `backlog.PRIORITIES = frozenset(high,medium,low)` + `_PRIORITY_RE` (backlog.py:53/60) - reuse.
- Recognized-but-optional pattern: `META_RECOGNIZED` not `META_REQUIRED` (Scope-Paths/Blocks-Release/From-Backlog precedent); hoisted setter write is the `--blocks-release`/`--from-backlog` pattern (status_set.py) so it persists on a no-op transition.
- `Item.priority` already exists (attention.py:45) and is rendered (:435); `_plans_record` (:317) just needs to read + pass it.

## Findings

Pure clone of the recognized-but-optional-field + hoisted-setter + attention-populate pattern used repeatedly this program; the only plan-specific bit is `_plans_record`.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: recognize `Priority`, validate via shared vocab.
2. `cli.py`+`status_set.py`: `aw ipd set --priority` (hoisted write).
3. `check_engine.py`: enum validation.
4. `attention.py`: populate `Item.priority` in `_plans_record`.
5. `tests/`: lint-clean with Priority; set/clear/no-op-persist; invalid flagged; board shows plan priority.

## Deferred / out of scope (with reason)

- Specs Priority: child 02. Research Priority: child 03. (Same pattern, different contracts.)

## Scope check

- Over-scope: none.
- Under-scope: none (plans field+setter+check+attention complete).

## Required tests / validation

- An IPD with `- Priority: high` lints clean at all phases; absent Priority also clean (optional).
- `aw ipd set <plan> --priority medium` writes it and persists on a same-status no-op; `--priority -` clears.
- `aw check` flags an out-of-vocab Priority on a plan.
- `aw attention` sorts/labels a plan by its priority.

## Spec / documentation sync

- Document `Priority` in the IPD metadata docs + `aw ipd --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Absent-priority rendering is decided at the orchestrator (OQ-01); this child treats absent as unset.

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

# IPD: Add recognized-but-optional Priority to the IPD schema plus aw ipd set/scaffold and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Plans/IPDs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional IPD metadata field reusing the shared `{high,medium,low}` vocab, with the `aw ipd set` setter, scaffold emission (optional), `aw check` validation, and `_plans_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Schema: add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (NOT `META_REQUIRED`; recognized-but-optional like Scope-Paths/Blocks-Release). Schema-layer recognition ONLY suppresses the IPD-M103 "unknown field" lint error; per the documented convention (ipd_schema.py:161-162,168-170), value/enum validation does NOT live in `validate_metadata` but in the `aw check` surface (see (3)). Define `META_PRIORITY` referencing the shared `backlog.PRIORITIES = {high,medium,low}` in prose only; do not fork the vocab. (2) Setter: add `--priority <low|medium|high>` to `aw ipd set` in cli.py + status_set.py using the hoisted status-branch-independent write (mirrors `--blocks-release`/`--from-backlog`, status_set.py:544-562) so it persists on a no-op transition; `-`/empty clears. (3) `aw check`: validate the enum here (flag an out-of-vocab Priority on a plan against the shared `backlog.PRIORITIES`; import the one vocab, do not fork). (4) Attention: populate `Item.priority` in `attention._plans_record` (:317) from the plan's `- Priority:` (attention.py already renders `Item.priority`, :45/:435/:717). Absent = unprioritized. This child covers PLANS only; specs = child 02, research = child 03.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: reviewed
- Set: xprio
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 1b45el

## Workflow history
- 2026-08-27 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-104 fixed (schema recognizes-not-validates, enum-check precedent corrected, label-not-sort, OQ-01 resolved, V-01/V-02 evidence realigned)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `Priority` (shared low/medium/high vocab) to IPDs: schema recognition, `aw ipd set --priority`, `aw check` enum validation, and `_plans_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema + setter

- [ ] E-01 Add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (not META_REQUIRED) so it RECOGNIZES the field (suppresses IPD-M103 unknown-field); do NOT add value/enum validation to `validate_metadata` (per convention that lives in `aw check`, E-02). Add `--priority <low|medium|high|->` to `aw ipd set` (cli.py + status_set.py) via the hoisted status-branch-independent write (mirroring the `--blocks-release`/`--from-backlog` primitives at status_set.py:544-562); optionally emit it from scaffold.
  - Depends on: none
  - Expected outcome: an IPD may carry `- Priority: high` and lints clean (schema recognizes it); `aw ipd set <plan> --priority medium` writes it (persists on no-op), `--priority -` clears.
  - Execution state: pending

### Task group 2: check + attention

- [ ] E-02 Validate the Priority enum in `aw check` (flag an out-of-vocab `- Priority:` value on a plan against the shared `backlog.PRIORITIES`). This is an ENUM check on a plan's own metadata (the true precedent is backlog's own priority enum guard, backlog.py:162, `item.priority not in PRIORITIES`), NOT a dangling/reference-resolution check like `check_blocks_release`/`check_from_backlog` (which resolve a target across trees, check_engine.py:604-607). Wire the new check into the plan-metadata pass of `aw check` (check_engine.py) reusing the shared `backlog.PRIORITIES` vocab.
  - Depends on: E-01
  - Expected outcome: `aw check` reports a finding for a plan carrying `- Priority: bogus` and reports none for `- Priority: high` or an absent Priority.
  - Execution state: pending
- [ ] E-03 Populate `Item.priority` in `attention._plans_record` (attention.py:317) from the plan's `- Priority:` line so the board labels a plan's priority (absent = unset). Scope note: this reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a plan carrying `- Priority:`, matching backlog's label rendering; no label for an absent Priority.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab: `backlog.PRIORITIES = frozenset(high,medium,low)` + `_PRIORITY_RE` (backlog.py:53/60) - reuse.
- Recognized-but-optional pattern: `META_RECOGNIZED` not `META_REQUIRED` (Scope-Paths/Blocks-Release/From-Backlog precedent); hoisted setter write is the `--blocks-release`/`--from-backlog` pattern (status_set.py) so it persists on a no-op transition.
- `Item.priority` already exists (attention.py:45) and is rendered (:435); `_plans_record` (:317) just needs to read + pass it.

## Findings

Pure clone of the recognized-but-optional-field + hoisted-setter + attention-populate pattern used repeatedly this program; the only plan-specific bit is `_plans_record`.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: RECOGNIZE `Priority` (add to `META_RECOGNIZED`) only; enum validation is `aw check`'s job (item 3), not the schema layer.
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
- `aw attention` LABELS a plan by its priority (`[high]`/`[medium]`/`[low]` bracket via the existing renderer, attention.py:717); the shared sort key (attention.py:186) is unchanged (E-03 scope note).

## Spec / documentation sync

- Document `Priority` in the IPD metadata docs + `aw ipd --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the orchestrator's OQ-01 (absent = unprioritized, no `[priority]` label, no priority sort introduced). This child follows that: `_plans_record` passes `Item.priority` (None when absent) to the existing type-agnostic label renderer and does not alter the sort key.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `aw ipd lint --phase author` on a fixture IPD carrying `- Priority: high` showing exit 0 (clean, schema RECOGNIZES the field), and on one with NO Priority also exit 0 (optional). Pasted `aw ipd set <fixture> --priority medium` run then the resulting `- Priority: medium` line, a same-status no-op re-run showing the line PERSISTS, and `--priority -` showing the line removed. A grep proving `ipd_schema` adds `META_PRIORITY` to `META_RECOGNIZED` (recognition only) and does NOT add value validation to `validate_metadata`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted `aw check` run over a fixture plan carrying `- Priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `- Priority: high` and no Priority showing NO such finding. A grep proving the enum check in `check_engine.py` consumes the shared `backlog.PRIORITIES` (no forked `{"high","medium","low"}` literal). Pasted new/updated test in tests/ asserting all three cases.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture plan carrying `- Priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a plan with no Priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`ipd_schema.py`, `status_set.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch specs/research contracts (children 02/03) or the shared attention sort key. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.

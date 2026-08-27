# IPD: Rename the intake status token to todo across the research contract, classification, and CLI modules

- Date: 2026-08-27
- Kind: child
- Concern: The `intake` status token is opaque and must become `todo`. It is referenced in code at: `research_contract.py` STATUSES/HOT_STATUSES (:148-149) + docstring (:18); `research_cmd.py` creation defaults (:189, :244); `attention_contract.py` classification map (:231 `"intake": READY`); `attention.py` stale-reclass logic + color band (:176-228, :485); `research_index.py` hot-glance band + the `## Needs addressing (intake)` header (:185-195); `research_archive.py` docstrings/hot-state logic; `cli.py` (:5994); `term.py`. This child renames the TOKEN in code (behavior-preserving); on-disk doc migration is child 02.
- Scope: Rename `intake` -> `todo` everywhere the token appears in code, keeping behavior identical (a `todo` research doc classifies READY/needs-attention exactly as `intake` did; stale-reclass to PARKED unchanged; color band preserved). Add a BACKWARD-COMPATIBLE READ: the contract accepts a legacy `intake` value as an alias of `todo` (so a not-yet-migrated on-disk doc, and child 02's migration window, do not break). Update the `research_index` `## Needs addressing` header wording to reflect `todo`. Update `cli.py` status choices/help and `term.py` label/color keys. Do NOT migrate on-disk docs here (child 02). Update the module tests that assert `intake` to assert `todo` + add a compat test that a legacy `intake` value still classifies as READY.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, agent_workflows/term.py, tests/
- Status: draft
- Set: rstodo
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: p3o9je

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Rename the research `intake` status token to `todo` across the contract, classification, CLI, index, and color modules, behavior-preserving, with a backward-compatible read accepting legacy `intake` as an alias.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: canonical token + creation

- [ ] E-01 In `research_contract.py` change the canonical token in `STATUSES`/`HOT_STATUSES` (:148-149) from `intake` to `todo` and update the docstring (:18); add a backward-compat read so a parsed `intake` value normalizes to `todo` (accepted, not rejected). In `research_cmd.py` change the creation defaults (:189, :244) to emit `status="todo"`.
  - Depends on: none
  - Expected outcome: new research docs are created `status: todo`; the contract accepts both `todo` and (legacy) `intake`, treating `intake` as `todo`.
  - Execution state: pending

### Task group 2: classification, index, cli, term

- [ ] E-02 Update `attention_contract.py` (:231 map `todo -> READY`) and `attention.py` stale-reclass logic + color band (:176-228, :485) to key on `todo` (behavior identical: READY, stale->PARKED, color preserved), accepting legacy `intake` via the contract normalization.
  - Depends on: E-01
  - Expected outcome: a `todo` research doc classifies READY and stale-reclasses to PARKED exactly as `intake` did; color unchanged.
  - Execution state: pending
- [ ] E-03 Update `research_index.py` hot band + the `## Needs addressing` header (:185-195) to use `todo`; update `cli.py` status choices/help (:5994) and `term.py` label/color keys.
  - Depends on: E-01
  - Expected outcome: index renders the `todo` band under a `## Needs addressing` header; `aw` status choices show `todo`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Canonical vocab lives in `research_contract.STATUSES`/`HOT_STATUSES` (:148-149); everything else keys off it.
- `attention_contract.py:231` maps status->attention class; `attention.py:485` holds the color band; `research_index.py:185-195` already renders a `## Needs addressing (intake)` header (rename to `todo`).
- Pre-release: no external repos depend on `intake`, so a permanent alias is optional (see orchestrator OQ-01); a transitional alias is still needed so child 02's migration window and any unmigrated doc do not break.

## Findings

Behavior-preserving token rename; the only subtlety is the backward-compat read (accept `intake` as `todo`) so it composes with child 02's on-disk migration without a flag day.

## Proposed changes (ordered, validatable)

1. `research_contract.py`: canonical token `todo` + `intake`->`todo` normalization.
2. `research_cmd.py`: creation emits `todo`.
3. `attention_contract.py`/`attention.py`: classify/color on `todo` (behavior identical).
4. `research_index.py`/`cli.py`/`term.py`: `todo` band/header/choices/labels.
5. `tests/`: update assertions to `todo` + a legacy-`intake`-still-READY compat test.

## Deferred / out of scope (with reason)

- On-disk doc migration + INDEX regeneration: child 02.
- The intake overload fix: spec 5tapom.

## Scope check

- Over-scope: none.
- Under-scope: none (all code touchpoints of the token are covered).

## Required tests / validation

- New research doc creation emits `status: todo`.
- A `todo` research doc classifies READY; stale-reclass to PARKED works; color band unchanged.
- A legacy `intake` value still normalizes/classifies as `todo`/READY (backward-compat).
- `research_index` renders the `todo` band under `## Needs addressing`; `aw` status choices include `todo`.

## Spec / documentation sync

- Update research docs/README + AGENTS.md research state vocab (`todo -> active -> reference/archive`); cross-ref spec 5tapom.

## Open questions

### OQ-01: none beyond the orchestrator's alias-lifetime question.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Alias lifetime is decided at the orchestrator (OQ-01); this child implements the alias regardless.

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
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

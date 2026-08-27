# IPD: Rename research status intake -> todo (intuitive; you still need to do this)

- Date: 2026-08-27
- Kind: orchestrator
- Concern: The research status `intake` is opaque - it does not tell a reader "you still need to do this research" - and it is OVERLOADED (means both genuinely-unrun AND finished-but-unpromoted; e.g. this session's sk94i0/40g511 sat as `intake` despite being done + adopted). Graduated from backlog `sr47pt` (Set `researchtodo`); design/rationale in that item. Decision: rename `intake` -> `todo` ('Status: todo' unambiguously = the reader must act). New research lifecycle: `todo` -> `active` -> `reference`/`archive`. This Set is minted with a FRESH setid `rstodo` (NOT the source's `researchtodo`) per the graduation-link model (spec 4w7d6s): the child->source link is `From-Backlog: sr47pt`; the source carries `Graduated-To: rstodo`.
- Scope: Rename the `intake` status token to `todo` across the research contract + classification + CLI + index, and migrate the ~10 existing on-disk research docs, WITHOUT changing behavior (a `todo` research doc classifies READY/needs-attention exactly as `intake` does today). Two children: 01 renames the token in code (research_contract.py STATUSES/HOT_STATUSES:148-149, research_cmd.py creation defaults:189/244, attention_contract.py:231 + attention.py stale-reclass/color:176-228,485, research_index.py band + `## Needs addressing` header:185-195, research_archive.py docstrings/logic, cli.py:5994, term.py); 02 migrates on-disk docs `status: intake` -> `status: todo` + regenerates INDEX, with a backward-compatible read (accept legacy `intake` as an alias of `todo` during/after migration so nothing breaks mid-flight). COUPLING (not in scope here): the OVERLOAD fix (unrun vs done-but-unfiled) is spec 5tapom's tool-owned state-advancement; this rename fixes only the NAME. If 5tapom lands first/concurrently, `todo` should mean genuinely-not-started.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, agent_workflows/term.py, .aw/records/research/, tests/
- Status: draft
- Set: rstodo
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: dh5gnl

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Rename the research status `intake` -> `todo` (a name that says "you still need to do this") across code and the ~10 on-disk docs, behavior-preserving (a `todo` doc is READY/needs-attention exactly as `intake` is today), with a backward-compatible read during migration. Graduated from backlog sr47pt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After children 01-02 execute, confirm no `intake` token remains in code (grep) except the legacy backward-compat alias, all on-disk docs read `todo`, `aw attention` still classifies research `todo` as READY (behavior unchanged), and the full suite is green.
  - Depends on: none
  - Expected outcome: grep shows no live `intake` (only the compat alias); board unchanged; suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | p3o9je | Rename the `intake` token -> `todo` across research contract/classification/CLI/index/color | none |
| 02 | lpqy64 | Migrate the ~10 on-disk docs `intake` -> `todo` + regenerate INDEX; backward-compatible read | 01 |

Order 01 -> 02; orchestrator verifies. (Source link: `From-Backlog: sr47pt`; source `Graduated-To: rstodo`.)

## Completion criteria (the whole Set is done only when)

- The canonical token is `todo` (research_contract STATUSES/HOT_STATUSES); creation emits `todo`; attention/index/color/CLI use `todo` (01).
- All ~10 existing on-disk `status: intake` docs are `status: todo`; INDEX regenerated; a legacy `intake` value still reads as `todo` (backward-compat) so nothing breaks mid-migration (02).
- Behavior preserved: a `todo` research doc is classified READY/needs-attention identically to old `intake`; stale-reclass to PARKED still works.
- Full suite green.

## Cross-IPD validation

- No live `intake` token remains in code after both children (only the documented backward-compat alias).
- The attention classification for research is byte-identical in behavior (READY/PARKED/ACTIVE) before/after - only the token label changes.

## Deferred / out of scope (with reason)

- The intake OVERLOAD fix (unrun vs done-but-unfiled): spec 5tapom (tool-owned state advancement). This Set only renames the token.
- The uniform cross-type Priority field (backlog p9o1oo) and Summary field (ud28vy): separate.

## Scope check

- Over-scope: none.
- Under-scope: none (token rename + on-disk migration is the complete deliverable).

## Required tests / validation

Aggregate of children: contract/classification tests updated to `todo` + a compat test that legacy `intake` still classifies correctly (01); a migration test that on-disk `intake` docs become `todo` and INDEX regenerates (02); an attention behavior-parity assertion.

## Open questions

### OQ-01: Keep the `intake` backward-compat read alias permanently, or only through migration?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Pre-release, no external repos depend on `intake`, so a permanent alias may be unnecessary. Default: accept `intake` as an alias during migration + one release, then drop. Decide at implementation; behavior-parity tests cover both tokens meanwhile.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

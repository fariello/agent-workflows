# IPD: Item-Dependencies schema field, grammar, and aw ipd dependencies set setter (clone the From-Backlog pattern)

- Date: 2026-08-27
- Kind: child
- Concern: An IPD cannot state its cross-IPD prerequisites in any machine-readable form. `ipd_schema.META_RECOGNIZED` has no whole-plan dependency field; the only `Depends on:` is the intra-plan E-item field (`parse_depends_on`, ipd_schema.py:504). The `Item-Dependencies` field designed in spec 25kzda (2.7) must exist before any predicate (child 02) or hook (child 03) can consume it. `From-Backlog` (ipd_schema.py, releases.set_blocks_release_line-style primitive, status_set hoisted write at ~449-461, cli `aw ipd set --from-backlog`) is the exact, tested precedent to clone.
- Scope: Add the `Item-Dependencies` metadata field and its setter. (1) Schema: add `META_ITEM_DEPENDENCIES = "Item-Dependencies"` to `ipd_schema.META_RECOGNIZED` (NOT `META_REQUIRED` - mandatoriness is phase/provenance-conditional and lives in child 02's checks + grandfathering, mirroring how `Scope-Paths`/`Blocks-Release` are recognized-but-optional at the schema layer). Field position: immediately after `Scope-Paths`. (2) Grammar + parser: `none` | comma-separated edges, each `executed:<id6>` | `exists:<type>:<id6>` | `state:<type>:<status>:<id6>` (type in ipd|spec|backlog; `executed:` targets only IPDs; `state:ipd:executed:` illegal - use `executed:`); reject self-edge, duplicate edge, `none` mixed with edges; canonical sort order by kind/type/status/id6; `unresolved` is the reserved scaffold sentinel (parses as not-ready, outside the execution grammar). A pure `parse_item_dependencies(value) -> (edges, error)` returning structured edges. (3) Write primitive: `set_item_dependencies_line(text, value)` (idempotent insert/replace/remove, anchored after `- Status:`/`- Id:`) in the releases-style location. (4) Setter: `aw ipd dependencies set <ipd-selector> <none|edge...>` in cli.py + status_set.py, using the SAME hoisted, status-branch-independent write as `--from-backlog` so it persists on a no-op transition; canonicalizes + validates tokens before writing; appends a workflow-history receipt; commits only the IPD + tool-owned index/history. (5) Scaffold: `aw ipd scaffold` emits `- Item-Dependencies: unresolved` in position (never blank, never `none`). This child delivers ONLY field + grammar + setter + scaffold emission; the graph predicate/rules/grandfathering are child 02; the hook is child 03.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/releases.py, agent_workflows/ipd_authoring.py, tests/
- Status: draft
- Set: ipddeps
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: g69y23

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add the `Item-Dependencies` IPD metadata field with its typed edge grammar, a pure parser, an idempotent write primitive, the `aw ipd dependencies set` setter (hoisted no-op-safe write), and scaffold emission of the `unresolved` sentinel - cloning the tested `From-Backlog` pattern.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema + grammar/parser

- [ ] E-01 Add `META_ITEM_DEPENDENCIES = "Item-Dependencies"` to `ipd_schema.META_RECOGNIZED` (not `META_REQUIRED`), positioned after `Scope-Paths`, with a doc comment matching the recognized-but-optional precedent. Add `parse_item_dependencies(value) -> (edges, error)` implementing the full grammar (none | executed:/exists:/state: edges, type/status pairing, self/duplicate/none-mixture rejection, canonical ordering, `unresolved` sentinel).
  - Depends on: none
  - Expected outcome: an IPD carrying a valid `- Item-Dependencies:` lints clean (no IPD-M103); the parser accepts every valid form and rejects each malformed form with a specific error.
  - Execution state: pending

### Task group 2: write primitive + setter + scaffold

- [ ] E-02 Add `set_item_dependencies_line(text, value)` idempotent primitive (insert/replace/remove, anchored after Status/Id), releases-style.
  - Depends on: E-01
  - Expected outcome: round-trips set / overwrite / clear leaving other metadata intact.
  - Execution state: pending
- [ ] E-03 Wire `aw ipd dependencies set <selector> <none|edge...>` in cli.py + status_set.py using the hoisted status-branch-independent write (mirrors `--from-backlog`), canonicalizing + validating before write, appending a history receipt.
  - Depends on: E-01
  - Expected outcome: setter writes canonical edges, persists on a same-status no-op transition, clears with `none`/`-`, rejects malformed input with the grammar error.
  - Execution state: pending
- [ ] E-04 `aw ipd scaffold` emits `- Item-Dependencies: unresolved` in position (never blank, never `none`).
  - Depends on: E-01
  - Expected outcome: a freshly scaffolded IPD carries `unresolved` and is an honest not-ready draft.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `From-Backlog` is the exact clone target: schema recognition (ipd_schema `META_RECOGNIZED`), idempotent write primitive (releases.py, `set_blocks_release_line`-style), hoisted status-branch-independent setter write (status_set.py ~449-461, the 61qk4a no-op-persist fix), cli flag on `ipd set`.
- Recognized-but-optional fields go in `META_RECOGNIZED` NOT `META_REQUIRED` (else every existing plan fails the always-on author metadata check - the grandfather guarantee).
- The existing intra-plan `parse_depends_on` (ipd_schema.py:504) is a DIFFERENT field; keep the two parsers/namespaces disjoint.

## Findings

The field is the prerequisite for the whole Set; it has a complete tested precedent (`From-Backlog`). The only genuinely new logic is the typed edge grammar/parser; everything else is a clone.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: recognize `Item-Dependencies`; `parse_item_dependencies`.
2. `releases.py`: `set_item_dependencies_line` primitive.
3. `cli.py` + `status_set.py`: `aw ipd dependencies set` (hoisted write).
4. `ipd_authoring.py`: scaffold emits `unresolved`.
5. `tests/`: schema-accepts + lint-clean; parser accept/reject matrix; setter set/overwrite/clear/no-op-persist; scaffold emits unresolved.

## Deferred / out of scope (with reason)

- Graph predicate + `check.ipd-dependency-*` rules + grandfathering: child 02.
- The pre-commit hook: child 03.
- Resolution/existence checks of edge targets: child 02 (this child only parses + writes syntax).

## Scope check

- Over-scope: none.
- Under-scope: none (field + grammar + primitive + setter + scaffold is the complete deliverable).

## Required tests / validation

- An IPD with `- Item-Dependencies: executed:aaaaaa, exists:spec:bbbbbb, state:backlog:done:cccccc` lints CONFORMING at author/pre-execution/pre-transition (no IPD-M103).
- `parse_item_dependencies`: every valid form parses to expected structured edges; each malformed form (self-edge, duplicate, none-mixture, bad type/status, E-id, `state:ipd:executed:`) returns its specific error.
- `aw ipd dependencies set`: writes canonical order; persists on a same-status no-op; clears with `none`; rejects malformed.
- `aw ipd scaffold` output contains `- Item-Dependencies: unresolved`.

## Spec / documentation sync

- Update AGENTS.md / IPD docs + `aw ipd --help` to document `Item-Dependencies` + `aw ipd dependencies set` alongside `From-Backlog`.

## Open questions

### OQ-01: Should `exists:`/`state:` edges accept `ipd` targets too, or only spec/backlog?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Spec allows `exists:ipd:`/`state:ipd:<status>:` (only `state:ipd:executed:` is forbidden, redirected to `executed:`). Implement per spec; the parser enforces the one exclusion.

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
- [ ] V-04 validates E-04
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

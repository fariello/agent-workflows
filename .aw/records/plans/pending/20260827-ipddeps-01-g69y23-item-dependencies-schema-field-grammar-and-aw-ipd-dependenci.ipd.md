# IPD: Item-Dependencies schema field, grammar, and aw ipd dependencies set setter (clone the From-Backlog pattern)

- Date: 2026-08-27
- Kind: child
- Concern: An IPD cannot state its cross-IPD prerequisites in any machine-readable form. `ipd_schema.META_RECOGNIZED` has no whole-plan dependency field; the only `Depends on:` is the intra-plan E-item field (`parse_depends_on`, ipd_schema.py:504). The `Item-Dependencies` field designed in spec 25kzda (2.7) must exist before any predicate (child 02) or hook (child 03) can consume it. `From-Backlog` (ipd_schema.py, releases.set_blocks_release_line-style primitive, status_set hoisted write at ~449-461, cli `aw ipd set --from-backlog`) is the exact, tested precedent to clone.
- Scope: Add the `Item-Dependencies` metadata field and its setter. (1) Schema: add `META_ITEM_DEPENDENCIES = "Item-Dependencies"` to `ipd_schema.META_RECOGNIZED` (NOT `META_REQUIRED` - mandatoriness is phase/provenance-conditional and lives in child 02's checks + grandfathering, mirroring how `Scope-Paths`/`Blocks-Release` are recognized-but-optional at the schema layer). Field position: immediately after `Scope-Paths`. (2) Grammar + parser: `none` | comma-separated edges, each `executed:<id6>` | `exists:<type>:<id6>` | `state:<type>:<status>:<id6>` (type in ipd|spec|backlog; `executed:` targets only IPDs; `state:ipd:executed:` illegal - use `executed:`); reject self-edge, duplicate edge, `none` mixed with edges; canonical sort order by kind/type/status/id6; `unresolved` is the reserved scaffold sentinel (parses as not-ready, outside the execution grammar). A pure `parse_item_dependencies(value) -> (edges, error)` returning structured edges. (3) Write primitive: `set_item_dependencies_line(text, value)` (idempotent insert/replace/remove) in the releases-style location, but anchored IMMEDIATELY AFTER `- Scope-Paths:` (fallback after `- Id:`, then top-of-block) to honor spec 2.7's mandated position - NOT after `- Status:` the way `set_blocks_release_line`/`set_from_backlog_line` anchor (see E-02). (4) Setter: `aw ipd dependencies set <ipd-selector> <none|edge...>` in cli.py + status_set.py, using the SAME hoisted, status-branch-independent write as `--from-backlog` so it persists on a no-op transition; canonicalizes + validates tokens before writing; appends a workflow-history receipt; commits only the IPD + tool-owned index/history. (5) Scaffold: `aw ipd scaffold` emits `- Item-Dependencies: unresolved` in position (never blank, never `none`). This child delivers ONLY field + grammar + setter + scaffold emission; the graph predicate/rules/grandfathering are child 02; the hook is child 03.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/releases.py, agent_workflows/ipd_authoring.py, tests/
- Status: reviewed
- Set: ipddeps
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: g69y23

## Workflow history
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-101/102/103/104 fixed

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

- [ ] E-02 Add `set_item_dependencies_line(text, value)` idempotent primitive (insert/replace/remove), releases-style. ANCHOR CORRECTION (do NOT blind-copy `set_from_backlog_line`): spec 2.7 mandates the field live IMMEDIATELY AFTER `- Scope-Paths:` (and before `Blocks-Release`/`From-Backlog`), whereas the `set_blocks_release_line`/`set_from_backlog_line` primitives anchor after `- Status:` (releases.py:103,148) - which in the real block order (`... Scope-Paths, Status, Set, Order ...`) is the WRONG position for this field. Anchor `Item-Dependencies` after `- Scope-Paths:`, falling back to after `- Id:`, then top-of-block. When `Scope-Paths` is absent, prefer inserting before `Status`.
  - Depends on: E-01
  - Expected outcome: round-trips set / overwrite / clear leaving other metadata intact; the line lands immediately after `Scope-Paths` (spec 2.7 position), NOT after `Status`.
  - Execution state: pending
- [ ] E-03 Wire `aw ipd dependencies set <selector> <none|edge...>` as a NEW `dependencies` subparser under the existing `aw ipd` `add_subparsers(dest="ipd_command")` (cli.py, alongside `lint`/`scaffold`/`sync`), routing through the SAME hoisted status-branch-independent write in status_set.py (the block at status_set.py:449-473 that funnels `--blocks-release`/`--from-backlog` through the shared `releases.set_*_line` primitives on any transition including a same-status no-op). Reuse that no-op-safe path (a same-status transition carrying the new value) rather than a second write path, so persistence-on-no-op is inherited, not reimplemented. Canonicalize + validate tokens (via `parse_item_dependencies`) BEFORE writing; append a workflow-history receipt; commit only the IPD + tool-owned index/history.
  - Depends on: E-01
  - Expected outcome: `aw ipd dependencies set` writes canonical edges, persists on a same-status no-op transition (same guarantee as `--from-backlog`), clears with `none`/`-`, rejects malformed input with the specific grammar error from `parse_item_dependencies`.
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
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Spec 2.7 allows `exists:ipd:`/`state:ipd:<status>:` (only `state:ipd:executed:` is forbidden, redirected to `executed:`). RESOLVED (see gate "Open questions resolved"): implement per spec; the parser enforces the one exclusion.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) An IPD carrying `- Item-Dependencies: executed:aaaaaa, exists:spec:bbbbbb, state:backlog:done:cccccc` lints CONFORMING (no IPD-M103) at `aw ipd lint --phase author` - paste the command + output. (b) A pytest exercising `parse_item_dependencies` shows every VALID form (none; each of executed:/exists:/state:; multi-edge canonical) parses to the expected structured edges, AND every MALFORMED form returns its specific error: self-edge, duplicate edge, none-mixed-with-edge, bad target-type, bad status-for-type, an E-id (e.g. `E-01`), and `state:ipd:executed:<id6>` - paste the passing test IDs/output. Falsifiable: a missing rejection case or a wrong parse fails.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A pytest round-trips `set_item_dependencies_line`: set on a plan with no field inserts it IMMEDIATELY AFTER the `- Scope-Paths:` line (assert the exact adjacent-line position, NOT merely presence, and NOT after `- Status:`); overwrite replaces in place; clear (`-`/None) removes it; all other metadata lines are byte-identical before/after - paste the test output. Falsifiable: an insert after `Status` (the blind-clone bug) fails the position assertion.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A pytest/CLI transcript shows `aw ipd dependencies set <id6> executed:aaaaaa exists:spec:bbbbbb` writes the edges in canonical order; a second same-status invocation persists the value (no-op-transition persistence, mirroring the `--from-backlog` 61qk4a guarantee); `aw ipd dependencies set <id6> none` clears to `none`; a malformed token (e.g. `state:ipd:executed:aaaaaa`) is rejected non-zero with the `parse_item_dependencies` error and writes nothing; a history receipt line is appended - paste each transcript.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Run `aw ipd scaffold` (both kinds if applicable) and grep the output/created file for `- Item-Dependencies: unresolved` positioned immediately after `- Scope-Paths:`; confirm it is never blank and never `none` - paste the scaffolded metadata block. Falsifiable: a blank or `none` default fails.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Open questions resolved

- OQ-01 (do `exists:`/`state:` edges accept `ipd` targets, or only spec/backlog): RESOLVED from spec 2.7 - `exists:ipd:<id6>` and `state:ipd:<status>:<id6>` ARE allowed; the ONLY exclusion is `state:ipd:executed:<id6>`, which the parser must reject and redirect to `executed:<id6>` (so verification evidence is also required). Implement exactly this; the parser enforces the single exclusion. Not a blocker. See OQ-01 above.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` (`ipd_schema.py`, `status_set.py`, `cli.py`, `releases.py`, `ipd_authoring.py`, `tests/`). This child delivers ONLY the field + grammar/parser + write primitive + `aw ipd dependencies set` setter + scaffold emission. Do NOT implement the graph predicate / `check.ipd-dependency-*` rules / grandfathering (child 02 `ovbnyq`) nor the commit hook (child 03 `mp88bl`); do NOT add referential/resolution checks of edge targets (child 02). This child parses and writes SYNTAX only. If a change appears to require editing outside `Scope-Paths` or reaching into child 02/03 territory, STOP and report rather than expanding scope.
- Honesty rule (hard MUST): when a V-item claims a lint/parse/setter/scaffold check passed or the suite is green, paste the ACTUAL runner output (the real `pytest`/`aw ipd lint`/`aw ipd dependencies set`/`aw ipd scaffold` output); never claim a pass you did not run.
- Commit rule: commit ONLY files this child changed, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).

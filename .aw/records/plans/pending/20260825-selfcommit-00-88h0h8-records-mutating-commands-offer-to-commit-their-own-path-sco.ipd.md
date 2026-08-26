# IPD: Records-mutating commands offer to commit their own path-scoped changes when interactive

- Date: 2026-08-25
- Kind: orchestrator
- Concern: Records-mutating verbs (`aw archive`, and its siblings `aw group`, `aw rename`, `aw research set-assign`/`mv`, `aw ipd set`, `aw specs set`) move/rename files and regenerate an INDEX but leave the resulting changeset UNCOMMITTED, so the user must notice and hand-commit a large coherent set of renames + index updates (origin: a 23-file `aw archive` research changeset). There is no shared "commit-what-I-changed" helper today; `ipd_lifecycle._git` (ipd_lifecycle.py:538) is a private path-scoped git wrapper used only by finalize, and each verb reimplements or omits committing. Backlog item vvc7c1 (medium).
- Scope: Add ONE shared "commit-what-I-changed" helper and adopt it across the records-mutating verbs so that, when run interactively (TTY), each verb PROMPTS to commit ONLY the files it just touched (moved/renamed paths + regenerated index), path-scoped, never `git add -A`/`-a`, never push, no hook bypass, with a good per-verb default message. Constraints (from vvc7c1): (1) commit ONLY files the command itself touched - track them explicitly, never commit whatever is dirty; (2) interactive-only by default - non-interactive/CI must NOT auto-commit unless an explicit `--commit` flag is passed, and a `--no-commit` escape hatch exists; (3) respect the repo contract (path-scoped, no push, no hook bypass); (4) if the tree already has unrelated staged/unstaged changes, do not fold them in; (5) sensible default message per verb (e.g. `chore(research): archive aged artifacts and regenerate index`). Two children: 01 builds the shared helper (path-scoped, TTY-gated, explicit path-set, `--commit`/`--no-commit`, per-verb message); 02 adopts it across the verbs with tests. NOTE: this helper is the same path-scoped-commit plumbing the agentadhere `aw commit` primitive (Phase 2) will want; keep it a standalone reusable helper so agentadhere can consume it later (no duplicate code path).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/research_archive.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/
- Status: draft
- Set: selfcommit
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 88h0h8

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Give records-mutating verbs one shared "commit-what-I-changed" helper so they offer, interactively, to path-scoped-commit only the files they just touched (no `git add -A`, no push, no hook bypass), eliminating orphaned uncommitted rename/index changesets. Standalone and reusable so the agentadhere `aw commit` primitive can consume it later.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the executable work. Its only execution step is the whole-Set consistency check after both children land.

### Task group 1: whole-Set integration check

- [ ] E-01 After children 01-02 execute and are green, confirm one shared helper is used by ALL adopting verbs (single definition, no duplicated commit path) and the whole test suite passes.
  - Depends on: none
  - Expected outcome: grep shows a single helper definition; every adopting verb imports it; full suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | shared helper (cv1rfd) | `git_commit_helper`: path-scoped, TTY-gated, explicit path-set, `--commit`/`--no-commit`, per-verb default message | none |
| 02 | adopt across verbs (jgcm68) | wire the helper into `aw archive`/`group`/`rename`/`research set-assign`-`mv`/`ipd set`/`specs set` with tests | 01 |

Sequence: 01 -> 02; orchestrator integration check runs last.

## Completion criteria (the whole Set is done only when)

- A shared helper exists that commits ONLY an explicit path-set, path-scoped, never `add -A`/`-a`, never pushes, no hook bypass; interactive-prompts by default; `--commit`/`--no-commit` honored; does not fold in unrelated dirty files (01).
- All named records-mutating verbs use the helper and offer to commit their own changes with a good default message; tests cover each (02).
- Full test suite green.

## Cross-IPD validation

- Single helper definition consumed by every adopting verb (no duplicate commit logic).
- The helper is standalone (importable by a future agentadhere `aw commit`), not entangled with any one verb.

## Deferred / out of scope (with reason)

- The agentadhere `aw commit <ipd>` primitive that will REUSE this helper: agentadhere set (this set only builds the reusable helper).
- Auto-commit in non-interactive/CI without `--commit`: explicitly excluded by design (constraint 2).

## Scope check

- Over-scope: none.
- Under-scope: none (shared helper + adoption is the complete deliverable).

## Required tests / validation

Aggregate of the children's tests: helper unit tests (path-scoping, TTY gating, `--commit`/`--no-commit`, no-fold-in of unrelated dirty files, no push), and per-verb adoption tests (archive/group/rename/research/ipd set/specs set offer + commit correctly).

## Open questions

### OQ-01: Which default commit-message convention per verb?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Start with `chore(<verb-domain>): <action> and regenerate index` (e.g. `chore(research): archive aged artifacts and regenerate index`); finalize exact strings in child 02.

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

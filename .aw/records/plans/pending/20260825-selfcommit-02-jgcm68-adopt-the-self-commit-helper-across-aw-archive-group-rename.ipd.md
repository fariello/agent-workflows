# IPD: Adopt the self-commit helper across aw archive/group/rename/research set-assign-mv/ipd set/specs set with tests

- Date: 2026-08-25
- Kind: child
- Concern: With the shared `git_commit_helper.offer_commit` (child 01) in place, the records-mutating verbs must actually adopt it so they offer to commit their own path-scoped changes. Today `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189), plus the group/rename/`ipd set`/`specs set` verbs, leave their rename + INDEX-regeneration changeset uncommitted.
- Scope: Wire `offer_commit` into each records-mutating verb so that after it mutates files + regenerates any INDEX, it collects the EXACT set of paths it touched (moved/renamed/deleted paths + regenerated index files) and calls `offer_commit(...)` with a good per-verb default message. Verbs: `aw archive` (research_archive + plans_archive), `aw group`, `aw rename` (plans_refs), `aw research set-assign`/`mv`, `aw ipd set` (status_set), `aw specs set` (specs). Add `--commit`/`--no-commit` flags to each verb's parser in cli.py (or a shared arg group). Each verb must pass the precise touched-path list (tracked explicitly during the mutation), NOT "whatever is dirty". Per-verb default messages (e.g. `chore(research): archive aged artifacts and regenerate index`, `refactor(plans): regroup set <id> and rewrite refs`). Tests per verb: interactive offer commits the right paths; `--no-commit` skips; non-interactive without `--commit` does not auto-commit; an unrelated dirty file is never folded in.
- Scope-Paths: agent_workflows/research_archive.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/
- Status: draft
- Set: selfcommit
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: jgcm68

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Adopt the shared `offer_commit` helper across `aw archive`/`group`/`rename`/`research set-assign`-`mv`/`ipd set`/`specs set` so each offers, interactively, to path-scoped-commit exactly the files it touched, with `--commit`/`--no-commit` flags and a good per-verb default message.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: adopt in the archive verbs

- [ ] E-01 Wire `offer_commit` into `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189): collect the exact moved/renamed/deleted paths + regenerated INDEX, call the helper with a `chore(<domain>): archive ... and regenerate index` message; add `--commit`/`--no-commit` to their cli parsers.
  - Depends on: none
  - Expected outcome: `aw archive` (research + plans) interactively offers to commit exactly its touched paths; `--no-commit` skips; non-interactive without `--commit` does not auto-commit.
  - Execution state: pending

### Task group 2: adopt in the regroup/rename/set verbs

- [ ] E-02 Wire `offer_commit` into `aw group`/`aw rename` (plans_refs) with the moved paths + rewritten INDEX and a `refactor(plans): regroup/rename ...` message; add `--commit`/`--no-commit`.
  - Depends on: none
  - Expected outcome: `aw group`/`aw rename` offer to commit exactly their touched paths + index; flags honored.
  - Execution state: pending
- [ ] E-03 Wire `offer_commit` into `aw research set-assign`/`mv`, `aw ipd set` (status_set), and `aw specs set` (specs) for their file moves + metadata rewrites + any index; add `--commit`/`--no-commit` and per-verb messages.
  - Depends on: none
  - Expected outcome: each of these verbs offers to commit its own path-scoped change; flags honored; unrelated dirty files never folded in.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `research_archive.run_archive` (research_archive.py:284) and `plans_archive.run_archive` (plans_archive.py:189) are the archive entry points; group/rename live in `plans_refs.py`; `ipd set` in `status_set.py`; `specs set` in `specs.py`.
- Each verb already knows the files it moves/renames and regenerates the INDEX - the touched-path set is available at the mutation site; pass it explicitly, do not re-derive from a dirty scan.

## Findings

Adoption is mechanical per verb: collect the touched paths (already known at the mutation site) and call the child-01 helper. The risk is precision of the path-set, so tests assert exactly which paths get committed.

## Proposed changes (ordered, validatable)

1. `research_archive.py` + `plans_archive.py`: adopt helper + flags.
2. `plans_refs.py`: group/rename adopt helper + flags.
3. `status_set.py` + `specs.py` + research set-assign/mv: adopt helper + flags.
4. `cli.py`: `--commit`/`--no-commit` on each verb (or a shared arg group).
5. `tests/`: per-verb offer/commit/skip/no-fold-in.

## Deferred / out of scope (with reason)

- The shared helper itself: child 01 (dependency).

## Scope check

- Over-scope: none.
- Under-scope: none (all six named verb families are covered).

## Required tests / validation

- For each adopting verb: interactive run commits exactly the touched paths (+ index); `--no-commit` skips; non-interactive without `--commit` does not auto-commit; an unrelated dirty file is never included; no push occurs.

## Spec / documentation sync

- Update each verb's `--help` and AGENTS.md / relevant READMEs to note the interactive self-commit offer and the `--commit`/`--no-commit` flags.

## Open questions

### OQ-01: Should the flags be per-verb or a single shared arg group applied to all?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Prefer a shared arg group (`--commit`/`--no-commit`) registered on each records-mutating parser for consistency; finalize in implementation.

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

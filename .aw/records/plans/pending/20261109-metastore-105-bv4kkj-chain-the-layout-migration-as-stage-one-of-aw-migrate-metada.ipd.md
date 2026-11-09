# IPD: Chain the layout migration as stage one of aw migrate metadata and handle no-sidecar and companion backends

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 5.2a items 2, 3 and 5 require `aw migrate metadata` to run the existing transactional layout migration first in a `.agents/` or mixed repository, resolve the records root through `project_context` (companion and home backends), and treat a missing sidecar as normal unless one is expected. Plan `g5hpbb` owned this (its E-06) beside seven other items; research `nj8zdp` guidance splits it in round 3 on 2026-11-09.
- Scope: Chain `layout_migration.MigrationManager` as stage one inside the m0001 journal, migrate companion/home backends in place, and gate the sidecar refusal on `discover`'s expectation (E-01, from `g5hpbb` E-06). EXCLUDES: discovery and id-less conversion (`3g20ms`), the AC-42 test module and changelog (`g5hpbb`).
- Scope-Paths: agent_workflows/migrations/m0001_metadata_v2.py, agent_workflows/layout_migration.py, agent_workflows/cli.py, .aw/records/plans/pending/20261109-metastore-105-bv4kkj-chain-the-layout-migration-as-stage-one-of-aw-migrate-metada.ipd.md
- Item-Dependencies: executed:dcerjg, executed:9vf2iv, executed:3g20ms
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 105
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: bv4kkj

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from g5hpbb (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One `aw migrate metadata` run converts a legacy-layout, mixed, no-sidecar or companion-backed repository in one journal, rolling back both stages on failure.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the layout stage

- [ ] E-01 (carried verbatim from `g5hpbb` E-06) Chain the layout stage (5.2a item 2) and resolve the records root (item 3): when `discover` reports a legacy tree, `aw migrate metadata` runs `layout_migration.MigrationManager` as stage one inside the same journal (its plan, apply, resume and rollback), then the metadata stage on the resolved records root; a failure in stage two rolls back stage one. A companion or home backend is migrated in place with logs beside its records (AC-18). The sidecar refusal fires only when `discover` says a sidecar is expected and absent; otherwise the census prints `no sidecar (none expected)`.
  - Depends on: none
  - Expected outcome: on `legacy_agents_layout` and `mixed_layout` the dry run shows both stages and `--apply` leaves no `.agents/` record tree; an injected failure in stage two (the existing `--fault-injection` hook) leaves the repository byte-identical to before; on `no_sidecar` the migration runs and prints the no-sidecar line; on `companion_backend` the logs are under the companion records root.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `layout_migration.MigrationManager` already owns the transaction journal, writer lock, resume and rollback for `aw migrate-layout`; spec 4sd62s 5.1 forbids new journal or lock components, so E-01 chains it rather than copying it (carried from `g5hpbb` Step 0).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The layout half already has a transactional tool. | `g5hpbb` F-04: `aw migrate-layout plan --json` on a copy of a private repository: `valid: true`, 1057 items, `no_write_proven: true`. |

## Proposed changes (ordered, validatable)

1. E-01: chain the layout stage, companion backends, no-sidecar rule.

## Deferred / out of scope (with reason)

- The AC-42 parameterized proof and the changelog.
  - Carrier: g5hpbb

## Scope check

- Over-scope: none. `layout_migration.py` changes only to be callable as a stage inside the metadata journal; `cli.py` only passes the stage through.
- Under-scope: none for `g5hpbb` E-06.

## Required tests / validation

Proven by V-01 on the `9vf2iv` corpus; existing layout tests `tests/test_layout_migration.py` and `tests/test_migrate_layout_cli.py` must still pass (named in V-01).

## Spec / documentation sync

No spec change; implements `4sd62s` 5.2a items 2, 3 and 5 and AC-18.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the two-stage dry run on `legacy_agents_layout`; `find .agents -name '*.md' | wc -l` after `--apply` (0 record files); the fault-injection run followed by `git status --porcelain` (empty); the `no_sidecar` census line `no sidecar (none expected)`; and the companion fixture's `meta/` directory listing under its records root. Each produced by `aw migrate metadata` (E-01 code path). Also `python3 -m pytest -o addopts="" -v tests/test_layout_migration.py tests/test_migrate_layout_cli.py` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: never run `aw migrate metadata --apply` on this checkout or any of the maintainer's other repositories; only on generated fixtures.

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit bv4kkj -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize bv4kkj` itself.

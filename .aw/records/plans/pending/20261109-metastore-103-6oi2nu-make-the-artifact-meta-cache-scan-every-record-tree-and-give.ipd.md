# IPD: Make the artifact_meta cache scan every record tree and give id-less records a stable identity

- Date: 2026-11-09
- Kind: child
- Concern: Measured 2026-11-07 on a copy of a private `.agents/`-layout repository (`g5hpbb` F-01): `status_set.inventory_all_artifacts` saw 201 records while `artifact_meta.query` saw 0, because the phase-A cache scans only the one records root `project_context` resolves. Id-less records also get a fresh random id6 per process (`g5hpbb` F-05). Plan `g5hpbb` owned both fixes (its E-02, E-03) beside six other items; research `nj8zdp` guidance splits it in round 3 on 2026-11-09.
- Scope: In `agent_workflows/artifact_meta.py`: scan the same directory set as `selectors.record_dirs` (E-01, from `g5hpbb` E-02) and give an id-less record a stable path-keyed identity (E-02, from `g5hpbb` E-03); and the cache-case test module `tests/test_artifact_meta_shapes.py` (E-03, the `g5hpbb` E-07 subset for those two items). EXCLUDES: discovery and conversion (`3g20ms`), layout stage (`bv4kkj`), the AC-42 proof (`g5hpbb`).
- Scope-Paths: agent_workflows/artifact_meta.py, tests/test_artifact_meta_shapes.py, .aw/records/plans/pending/20261109-metastore-103-6oi2nu-make-the-artifact-meta-cache-scan-every-record-tree-and-give.ipd.md
- Item-Dependencies: executed:dcerjg, executed:9vf2iv
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 103
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6oi2nu

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from g5hpbb (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The phase-A cache sees every record today's readers see in a repository of each C12 shape, and an id-less record keeps the same identity across cold builds, so later reader moves preserve behavior everywhere.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the phase-A cache sees every shape

- [ ] E-01 (carried verbatim from `g5hpbb` E-02) In `artifact_meta`, make the cache's scan cover the SAME directories today's readers search: the records root `project_context` resolves, plus the literal `<repo>/.aw/records/<type>` and legacy `<repo>/.agents/<type>` (and `.agents/docs/<type>`) trees that `selectors.record_dirs` already combines, de-duplicated by resolved path. Records found under a legacy tree are typed by the same path rule `status_set.detect_artifact_type` uses. Pin today's behavior first: for each `9vf2iv` corpus shape, save `status_set.inventory_all_artifacts` (`path`, `record_type`, `id6`, `set_id`, `status`) to `.aw/state/g5hpbb/<shape>-before.json`.
  - Depends on: none
  - Expected outcome: for every shape, `artifact_meta.query` returns a row for every record in the before-dump (measured on the fixture shaped like repository P this is 0 rows before the change), and on this repository the record-parity probe of backlog `suth7l` still reports only the 242 named filename-Set differences.
  - Execution state: pending

- [ ] E-02 (carried verbatim from `g5hpbb` E-03) Give an id-less record a STABLE identity in the cache. Today `load_legacy_artifact` mints a fresh random `id6` for each id-less file in each process, so the same file gets a different id6 on every cold cache build and a `read(id6)` cannot be repeated. Derive the phase-B identity deterministically from the record's records-root-relative path (a reserved, non-mintable prefix or a separate `path_key` column, chosen at execution and recorded as a decision), keep it out of `global_id6s` so it can never collide with a minted id6, and keep the migration's minting (`3g20ms` E-02) as the only place a real id6 is assigned.
  - Depends on: E-01
  - Expected outcome: two cold builds of the `idless_prose` fixture give the same identity for each id-less record; no phase-B identity appears in `artifact_core.global_id6s`; `aw find` on the fixture is unchanged.
  - Execution state: pending

### Task group 2: tests

- [ ] E-03 Add `tests/test_artifact_meta_shapes.py` (the `g5hpbb` E-07 subset "for the E-02/E-03 cache cases"), parameterized over the five `9vf2iv` corpus shapes, calling the real functions and asserting outputs (no test reads production source): per shape, `artifact_meta.query` row set equals the `status_set.inventory_all_artifacts` set by path; for `idless_prose`, two cold builds give identical identities and none is in `artifact_core.global_id6s`. Tests over 2 s are marked `slow` and named in V-03.
  - Depends on: E-01, E-02
  - Expected outcome: every parameterized case passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.record_dirs` is the existing, tested authority for "which directories hold records of a type"; E-01 reuses its rule rather than inventing a second one (carried from `g5hpbb` Step 0).
- AGENTS.md forbids tests that read production source (P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The phase-A cache sees 0 of 201 records in an `.agents/`-layout repository. | `g5hpbb` F-01. |
| F-02 | Id-less records get a random id6 per process in the cache. | `g5hpbb` F-05: `artifact_meta.load_legacy_artifact` calls `_core.generate_id6(_pool)` for any record with no id. |

## Proposed changes (ordered, validatable)

1. E-01: scan set.
2. E-02: stable id-less identity.
3. E-03: tests.

## Deferred / out of scope (with reason)

- Discovery, id-less minting in the migration, layout stage, AC-42 proof.
  - Carrier: g5hpbb

## Scope check

- Over-scope: none. `artifact_meta.py` changes only its scan set and id-less identity.
- Under-scope: none for `g5hpbb` E-02, E-03 and the shapes module of its E-07.

## Required tests / validation

New module: `tests/test_artifact_meta_shapes.py`. Existing, run before and after: `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_cache.py`, `tests/test_artifact_meta_loader_parity.py`.

## Spec / documentation sync

No spec change; implements the cache half of `4sd62s` C12 and 5.2a.

## Open questions

### OQ-01: Should id-less records get their permanent id6 in phase B instead of at migration?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `g5hpbb` OQ-01: No. Writing an id into another repository's files is a migration act that 5.2 confines to `aw migrate metadata`; phase B only reads. E-02 gives the cache a stable, non-mintable identity, and `3g20ms` mints the real id6 inside the migration. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste, per shape, the before-dump record count and the `artifact_meta.query` row count after the change (equal), with the repository-P-shaped fixture's before-change count of 0 rows; and the `suth7l` record-parity probe output on this repository showing `records_disagreeing: 242` and `missing_from_cache: 0`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste two cold builds' identities for every id-less record of `idless_prose` (identical), the recorded decision (prefix or `path_key`), and a check that none of them is in `artifact_core.global_id6s(<fixture>)`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_shapes.py tests/test_artifact_meta_legacy.py tests/test_artifact_meta_cache.py tests/test_artifact_meta_loader_parity.py` with the five shape parameter ids of `tests/test_artifact_meta_shapes.py` PASSED by node id and 0 failed in the three existing modules.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: tests run only on generated fixtures.

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 6oi2nu -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 6oi2nu` itself.

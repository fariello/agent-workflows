# IPD: Fix release mechanics: RELEASING.md + Makefile version-file target to .aw/system paths

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 finding S4-D03: the release mechanics still target the moved VERSION artifact. `make version-file` writes `.agents/workflows/VERSION` + `.agents/workflows/index.md` (Makefile:48,51) and RELEASING.md:44 documents `.agents/workflows/VERSION` as the bake target - both moved to `.aw/system/` in the migration. A releaser following RELEASING.md verbatim would re-bake the WRONG file, leave `.aw/system/VERSION` stale, and ship a wrong baked version (the exact failure the bake-then-tag section warns against).
- Scope: Repoint the `version-file` Makefile target and the RELEASING.md bake-then-tag instruction to `.aw/system/VERSION` and `.aw/system/workflows/index.md`. Verify `make version-file` stamps the real shipped files. OUT: choosing the next version NUMBER (orchestrator/maintainer, S6-V01) - this Order only fixes WHERE the bake writes.
- Status: to-review
- Set: awretrofit
- Order: 3
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: giiowo

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 finding S4-D03 (Set awretrofit Order 03).

## Goal

Make the documented release step (`make version-file`) actually stamp the shipped VERSION artifact so
a releaser following RELEASING.md bakes the correct version into the file the installer distributes,
instead of writing a stray legacy `.agents/workflows/VERSION` and leaving `.aw/system/VERSION` stale.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: repoint the bake target and its doc

- [ ] E-01 In the Makefile `version-file` target, change the two write paths from `.agents/workflows/VERSION` and `.agents/workflows/index.md` (Makefile:48,51) to `.aw/system/VERSION` and `.aw/system/workflows/index.md`. Preserve the version-validation regex, the resolver call, and the `WORKFLOWS-VERSION`/`Version:` index-stamp substitutions.
  - Depends on: none
  - Expected outcome: `make version-file VERSION=<X.Y.Z>` writes `.aw/system/VERSION` and re-stamps `.aw/system/workflows/index.md`; no stray `.agents/workflows/*` is created.
  - Execution state: pending

- [ ] E-02 Update RELEASING.md:44 (the bake-then-tag paragraph) to name `.aw/system/VERSION` as the tracked derived artifact the installer copies, keeping the bake-then-tag ordering rule intact.
  - Depends on: none
  - Expected outcome: RELEASING.md documents `.aw/system/VERSION`; no `.agents/workflows/VERSION` reference remains in the live release instructions.
  - Execution state: pending

### Task group 2: verify the bake round-trips

- [ ] E-03 Run `make version-file` with the CURRENT resolved version (no VERSION override, so the baked value is unchanged) and confirm it rewrites `.aw/system/VERSION` + `.aw/system/workflows/index.md` in place with no spurious change, and creates no `.agents/workflows/*`. Restore any incidental reformatting.
  - Depends on: E-01
  - Expected outcome: a no-op-value bake touches only the `.aw/system` files (idempotent), never the legacy path.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The tracked derived VERSION artifact moved from `.agents/workflows/VERSION` to `.aw/system/VERSION`; the shipped workflow catalog from `.agents/workflows/index.md` to `.aw/system/workflows/index.md`. `hatch_build.py` already prefers `.aw/system/VERSION` (code correct; its docstring is stale -> Order 05).
- Bake-then-tag (RELEASING.md): the baked file must equal the tag's version BEFORE tagging. This Order fixes only the WHERE; the version NUMBER and the actual bake/tag are Section 9 / maintainer.

## Findings

| id | artifact | evidence | issue |
|---|---|---|---|
| D03a | Makefile version-file | Makefile:48 `.agents/workflows/VERSION`, :51 `.agents/workflows/index.md` | writes moved paths -> stale real VERSION |
| D03b | RELEASING.md | :44 `.agents/workflows/VERSION` | documents the wrong bake target |

## Proposed changes (ordered, validatable)

1. E-01 Makefile paths -> `.aw/system/`.
2. E-02 RELEASING.md paragraph -> `.aw/system/VERSION`.
3. E-03 idempotent no-op-value bake verification.

## Deferred / out of scope (with reason)

- The next version NUMBER (S6-V01): maintainer decision, Section 9.
- `hatch_build.py`/`versioning.py` stale docstrings: Order 05 (code already correct).

## Scope check

- Over-scope: none.
- Under-scope: none - this Order is exactly the two release-mechanics artifacts; the version-number
  decision is correctly the orchestrator's, not this Order's.

## Required tests / validation

- `make version-file` (current version) rewrites `.aw/system/VERSION` + `.aw/system/workflows/index.md`
  only; `ls .agents/workflows/VERSION` -> absent. `git grep -n "\.agents/workflows/VERSION" Makefile RELEASING.md` -> 0.
- Full serial suite unaffected (no product-code change) - confirm >= 982 passed / 1 skipped.

## Spec / documentation sync

- RELEASING.md is the doc updated here. No spec status change.

## Open questions

### OQ-01: Should this Order bake a new version number?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: NO. This Order fixes only WHERE `make version-file` writes. The
  version NUMBER (S6-V01) is a maintainer decision and the actual bake/commit/tag happens in Section 9
  after an explicit human GO. E-03 verifies with the CURRENT value (a no-op-value bake), changing no number.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `make version-file` writes `.aw/system/VERSION` + re-stamps `.aw/system/workflows/index.md`; `git grep -n "\.agents/workflows" Makefile` -> 0. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git grep -n "\.agents/workflows/VERSION" RELEASING.md` -> 0; the paragraph names `.aw/system/VERSION`. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a current-version `make version-file` touches only `.aw/system/VERSION` + `.aw/system/workflows/index.md` (no value change, no `.agents/workflows/*` created). Paste `git status --short` after + `ls .agents/workflows/VERSION` (absent).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-03, pastes actual evidence (make output, greps, no-op-value bake status), commits
only `Makefile` + `RELEASING.md` (and, if the no-op bake legitimately re-stamps, `.aw/system/VERSION` +
`.aw/system/workflows/index.md` only when their content genuinely changed), never pushes, runs
`aw ipd lint --phase pre-transition` + the full suite, and the orchestrator owns the move to
`executed/`. Does NOT bake a new version number or tag (Section 9).

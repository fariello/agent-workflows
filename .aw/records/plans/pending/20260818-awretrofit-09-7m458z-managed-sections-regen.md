# IPD: Regenerate self-install managed-sections.json to .aw/system keys (via aw install)

- Date: 2026-08-18
- Kind: child
- Concern: Release-review 20260817-153418 finding S5-K01 (split out of Order 05, 2026-08-17): the self-install manifest `.aw/system/managed-sections.json` is keyed entirely on legacy `.agents/workflows/*` (150 keys, 0 `.aw/`) - it was `git mv`'d into `.aw/system/` in the Order-11 migration without rekeying. On the next `aw install`/update ON THIS repo, the installer may treat every `.agents/workflows/*` entry as a vanished managed file, disturbing prune/diff.
- Scope: Regenerate `.aw/system/managed-sections.json` so its keys are `.aw/system/workflows/...`, via the manifest machinery / a controlled `aw install .` self-update (NOT a hand-edit). Verify install/update prune/diff behaves + the rekeyed manifest stays sanitize-clean. This is a self-install-only concern (running `aw install` ON this framework repo), NOT a shipped-artifact defect. OUT: prose/dead-code (Order 05, done).
- Status: to-review
- Set: awretrofit
- Order: 9
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 7m458z

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): split out of Order 05 (carries finding K01 + the sanitize-after-regen check PR-002). Ready for /plan-review.

## Goal

Rekey the self-install manifest so a re-install/update ON this framework repo behaves correctly (no
spurious vanished-managed-file prune), by regenerating it through the manifest machinery rather than
hand-editing 150 stale keys.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: regenerate the manifest

- [ ] E-01 Regenerate `.aw/system/managed-sections.json` so its keys reflect the current `.aw/system/` install layout (`.aw/system/workflows/...`), NOT the 150 stale `.agents/workflows/*` keys. Use the manifest machinery / a controlled `aw install .` self-update (idempotent), NOT a hand-edit. If a full `aw install .` also rewrites shims/AGENTS.md/config/state, commit ONLY the managed-sections.json change path-scoped (verify the other touched files are no-op / already-current, or handle them explicitly). Confirm install/update prune/diff is a clean no-op afterward.
  - Depends on: none
  - Expected outcome: `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0; a second `aw install .`/update dry-run reports no spurious prune.
  - Execution state: pending

### Task group 2: verify

- [ ] E-02 Verify: the rekeyed manifest stays `aw sanitize --agent` clean (it holds this repo's file hashes; PR-002), `aw attention --check` valid, and the full serial suite unaffected (>= 1004 passed / 1 skipped).
  - Depends on: E-01
  - Expected outcome: sanitize + attention clean; suite unchanged.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `managed-sections.json` is a GENERATED manifest (manifest.py; populated during `install_all` keyed by each file's install `relative_posix`), NOT hand-maintained; regenerate via the machinery.
- There is no standalone "rebuild from tree" function; the designed regeneration is a full `aw install .` (idempotent), which also touches shims/AGENTS.md/config/state - hence this is its own isolated Order (split from Order 05).

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| K01 | managed-sections.json | 150 `.agents/workflows/*` keys, 0 `.aw/` (git mv'd in Order 11 without rekey) | self-install prune/diff churn on re-install |

## Proposed changes (ordered, validatable)

1. E-01 regenerate the manifest via `aw install .` (path-scoped commit of managed-sections.json). 2. E-02 verify sanitize/attention/suite.

## Deferred / out of scope (with reason)

- Prose/dead-code (Order 05, done). Any shipped-artifact change (the manifest is self-install-only).

## Scope check

- Over-scope: none - a single manifest regen; commit only managed-sections.json unless a full install legitimately updates other already-current files.
- Under-scope: none - K01 is the whole concern.

## Required tests / validation

- `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0; a re-install/update dry-run is a clean no-op.
- `aw sanitize --agent` clean on the rekeyed manifest; `aw attention --check` valid; full serial suite >= 1004 passed / 1 skipped.

## Spec / documentation sync

- None; self-install manifest only. No spec status change.

## Open questions

### OQ-01: If `aw install .` touches files beyond managed-sections.json, commit them or keep it minimal?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: Commit ONLY `managed-sections.json` path-scoped. If the self-install
  legitimately updates other files (shims/AGENTS.md), verify each is a correct no-op/already-current and
  either leave it unstaged or handle it in a separate, clearly-labeled commit - never bundle an
  unexplained broad rewrite into this manifest-regen Order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0 (keys now `.aw/system/...`); a re-install/update dry-run reports no spurious vanished-managed-file prune. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw sanitize --agent` clean on the rekeyed manifest; `aw attention --check` valid; full serial suite >= 1004 passed / 1 skipped. Paste.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
regenerates the manifest via the machinery, pastes evidence (the 0-legacy-keys grep, the no-op
re-install dry-run, sanitize/attention/suite), commits ONLY `.aw/system/managed-sections.json`
path-scoped (per OQ-01), never pushes, runs `aw ipd lint --phase pre-transition` + the full suite, and
the orchestrator owns the move to `executed/`. LOW-MEDIUM risk (self-install path) - the manifest is
self-install-only and the regen is verified by a clean no-op re-install.

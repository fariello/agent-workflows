# IPD: whatnext rewire and CI wiring (Set attnview, Order 5)

- Date: 2026-08-08
- Kind: child
- Concern: make the attention view actually change behavior: rewire the `/whatnext` workflow to CONSUME `aw attention --format json` first (stop on an invalid view) instead of re-scouring raw files, wire `aw attention --check` (and `aw specs check`) into CI, and land the docs/DECISIONS updates that record the convention.
- Scope: edit the `/whatnext` workflow body, add the CI check, update AGENTS.md pointer + relevant READMEs + DECISIONS. Consumes the Order 03 command; does NOT change the scanner/verbs. Requires Orders 01, 02, 03 executed (04 recommended so the repo view is clean, but not a code dependency).
- Status: approved
- Approval: 2026-08-08, human maintainer ("Approved all. Go.") after /plan-review (APPROVE WITH REVISIONS APPLIED)
- Set: attnview
- Order: 5
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 9y2fz1

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`, authored from the approved spec Sections 8.7 (whatnext), 5 (CI), and G5/G7; requires the Order 03 `aw attention` command.
- 2026-08-08 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. FIXED L5-01 (HIGH: the CI premise was false - no existing `aw ipd lint`/`aw plans index --check` CI gate to "match"; E-03 now states the ground truth and pins the new mechanism, a GitHub Actions step, and names it the first such gate), L5-02 (confirm `aw specs check` is delivered by Order 02 before wiring it, else gate only `aw attention --check`), L5-03 (resolve OQ-01: AGENTS.md source of truth is `agents_pointer_prose()` + regenerate + empty-diff invariant; forbid hand-editing the tracked pointer), L5-04 (V-01 asserts the no-silent-rescan negative), L5-05 (preserve the comms untrusted-payload headers-only invariant among the bounded secondary sources). Status draft -> reviewed.
- 2026-08-08 approved (human maintainer): "Approved all. Go." Status reviewed -> approved; cleared for execution via ipd-lifecycle.

## Goal

Turn `/whatnext` into a thin consumer of the deterministic view and enforce the contract in CI: `/whatnext` runs `aw attention --format json`, stops and surfaces violations on an invalid view, prioritizes `active` then `ready`, shows `blocked` with gates, and reads only selected artifacts (git/TODO.md stay explicitly-bounded separate sources); CI runs `aw attention --check` + `aw specs check`; AGENTS.md/README/DECISIONS record the convention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: rewire /whatnext

- [ ] E-01 edit `.agents/workflows/whatnext/whatnext.md` so Step 1 runs `aw attention --format json` FIRST as the primary source: on nonzero/`valid:false`, present all violations and STOP normal prioritization; on valid, prioritize `active` then `ready`, show `blocked` with gate detail, hide `done`/`parked` unless requested, and read only selected artifacts. Keep comms-inbox, git-WIP, and TODO.md as explicitly-bounded separate SECONDARY sources subordinate to the view, PRESERVING the existing comms untrusted-payload invariant (headers-only, never write a payload to TODO.md; whatnext.md:24-27, 130-133); do NOT silently fall back to full raw rescanning (a diagnostic raw-inspect mode, if present, is explicitly opt-in).
  - Depends on: none
  - Expected outcome: the whatnext workflow text specifies the consume-then-stop-or-prioritize contract (spec Section 8.7) and preserves the comms untrusted-payload boundary.
  - Execution state: pending
- [ ] E-02 update the `/whatnext` README so its described sources match the rewired body (registry-view-first).
  - Depends on: E-01
  - Expected outcome: whatnext README and body agree.
  - Execution state: pending

### Task group 2: CI + docs/decisions

- [ ] E-03 wire `aw attention --check` (and `aw specs check` IF Order 02 delivered it as a subcommand; else gate only `aw attention --check`, which already covers the specs tree) into CI, fail-closed. GROUND TRUTH (verified): no `aw ipd lint` / `aw plans index --check` gate exists in CI or pre-commit today (`.github/workflows/{tests,secret-scan,local-leaks}.yml`, `.pre-commit-config.yaml`), so there is NO existing pattern to "match" - this child adds the FIRST such gate. Pin the mechanism: add a fail-closed step running `python3 -m agent_workflows attention --check` (the checks need the full `.agents/` tree). Prefer a GitHub Actions job/step (after the unittest run in `tests.yml`, matching the secret-scan/local-leaks precedent) over a pre-commit hook; if a `local` pre-commit hook is chosen instead, mirror the `local-leaks` hook (`pass_filenames: false`, `always_run: true`).
  - Depends on: none
  - Expected outcome: a NEW fail-closed CI step runs the attention (and, if present, specs) check and fails on any violation; the chosen surface is named.
  - Execution state: pending
- [ ] E-04 update the AGENTS.md managed pointer by editing `agent_workflows/engine.py::agents_pointer_prose()` (the source of truth, per OQ-01) and regenerating via the installer - do NOT hand-edit the tracked AGENTS.md pointer body - to note the `aw attention` view + `aw specs` verbs + the "attention view is ephemeral/on-demand, not committed" stance; verify the post-regeneration AGENTS.md diff is empty (invariant); update `.agents/docs/specs/README.md` (specs now carry a required status + history) if not already done in Order 02.
  - Depends on: E-01
  - Expected outcome: the always-loaded pointer tells agents to consult `aw attention` and use `aw specs` for spec status.
  - Execution state: pending
- [ ] E-05 add a DECISIONS entry recording the attention-view model (cross-tree class mapping, read-only view + owner writes, ephemeral aggregate, fail-closed), citing the approved spec and the review set; add a TODO note for the deferred adopters (prompts/comms in Phase 3; optional snapshot in Phase 2).
  - Depends on: E-01
  - Expected outcome: DECISIONS + TODO reflect the shipped v1 and its deferred future work.
  - Execution state: pending

### Task group 3: verify

- [ ] E-06 run the full suite; run `aw attention --check` and `aw specs check` on the repo; if AGENTS.md is installer-generated, verify the empty-diff invariant after regeneration; confirm leak-clean and no em/en dashes. Paste actual output.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: suite green; the CI checks pass on this repo; AGENTS.md regeneration (if applicable) is idempotent; leak-clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `/whatnext` today walks raw sources (`.agents/workflows/whatnext/whatnext.md` Step 1); this child makes `aw attention --format json` its first source, keeping comms/git/TODO explicitly bounded.
- AGENTS.md pointer may be installer-generated (`agents_pointer_prose()` in `engine.py`); if so, edit the source and regenerate, then verify the empty-diff invariant (the recurring installer pattern).
- CI/pre-commit is where `--check` gates live; match the existing gate style, do not publish/deploy.

## Findings

The behavior win of the whole Set lands here: without the `/whatnext` rewire, the scanner exists but nothing consumes it. The A10 verification is workflow-contract-level (the workflow text specifies the order + stop-on-invalid), not model-read instrumentation.

## Proposed changes (ordered, validatable)

1. `.agents/workflows/whatnext/whatnext.md` + its README (E-01/E-02).
2. CI config (E-03).
3. AGENTS.md pointer source + `.agents/docs/specs/README.md` (E-04).
4. `DECISIONS.md` + `TODO.md` (E-05).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| prompts/comms adoption | scope | v1 excludes them (OQ3). | Phase 3 |
| Persisted snapshot / cache | complexity | Deferred until justified (OQ9). | Phase 2 |
| Changing the scanner/verbs | scope | Built in Orders 02/03; this child only consumes + documents. | n/a |

## Scope check

- Over-scope: none - workflow rewire + CI + docs/decisions only.
- Under-scope: MUST make `/whatnext` consume the view and stop on invalid, and MUST gate the checks in CI; otherwise the Set ships a tool nothing uses and no CI enforcement.

## Required tests / validation

`python3 -m unittest discover -s tests -t .` green (paste `Ran N ... OK`); `aw attention --check` and `aw specs check` pass on this repo; if AGENTS.md is installer-generated, the post-regeneration diff is empty (pointer body matches the managed section); `aw sanitize --agent` clean; no em/en dashes. The `/whatnext` contract is verified by reading the rewired body for the consume-first + stop-on-invalid + bounded-sources requirements.

## Spec / documentation sync

This child IS the documentation sync for the Set: AGENTS.md pointer, specs README, DECISIONS, TODO. It also flips the approved spec's `Status: approved` toward the terminal `implemented` once the whole Set is executed (done by the orchestrator's post-gate transaction / a follow-up `aw specs set`, not here).

## Open questions

### OQ-01: AGENTS.md pointer source of truth

- Blocking: no
- Status: resolved
- Owner: this child (E-04)
- Resolution or deferral rationale: RESOLVED (verified via `engine.py` `agents_pointer_prose()` + the visible `aw:block`/`aw:pointer` managed region in AGENTS.md): the source of truth is `agent_workflows/engine.py::agents_pointer_prose()`, wrapped as the `aw:pointer` managed section. E-04 edits THAT prose and regenerates via the installer, then verifies the post-regeneration AGENTS.md diff is empty; it does NOT hand-edit the tracked AGENTS.md pointer body (that would be overwritten and fail the empty-diff invariant). The installer may auto-commit AGENTS.md + the managed-sections manifest; record that commit exactly (gate note).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the rewired `whatnext.md` Step 1 runs `aw attention --format json` first, stops on `valid:false`, prioritizes active/ready, shows blocked-with-gates, keeps git/TODO/comms bounded, and preserves comms headers-only; quote the line proving there is NO silent fallback to full raw rescanning when the view is missing/invalid (spec 8.7).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the whatnext README's source list matches the rewired body (no stale "scour raw files first").
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a NEW fail-closed CI step runs `aw attention --check` (and `aw specs check` if delivered); show the added job/step and name the chosen surface (GitHub Actions step vs pre-commit hook); confirm no pre-existing gate was assumed.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the AGENTS.md pointer names the `aw attention` view + `aw specs` verbs; if installer-generated, the regeneration diff is empty; specs README documents the required status + history.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the DECISIONS entry records the model (cite spec + review set); TODO notes the deferred adopters.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the actual `python3 -m unittest` summary; `aw attention --check` + `aw specs check` clean; AGENTS.md empty-diff invariant (if applicable); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. NOTE: `aw install`/the installer may auto-commit AGENTS.md + the managed-sections manifest; if E-04 triggers that, record the installer commit exactly and keep it path-consistent. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an E-*/V-* item. Requires Orders 01, 02, 03 executed first; if the `aw attention`/`aw specs` commands are absent, STOP.

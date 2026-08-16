# IPD: migrate-layout wizard-by-default with config and command-line non-interactive overrides

- Date: 2026-08-16
- Kind: child
- Concern: `aw migrate-layout` is flag-driven, not guided. Reaching the physical-.aw layout requires the operator to know `apply --apply --confirm`, `--target-backend`, `--root`, and (after Order 14) `--leftovers`. The end-state contract (spec 20260810-1447-01 S13; point #4) requires the migration to run as a WIZARD by default that asks the typical questions (records destination/backend, retained-material choice, leftover disposition, confirmation with a preview), while accepting a config file and/or command-line flags to answer those questions non-interactively for scripted/CI use, with no prompt that blocks a non-interactive run and no deletion without an explicit choice.
- Scope: the `migrate-layout` CLI surface in `agent_workflows/cli.py` (`_run_migrate_layout`), a guided front-end that composes the existing inventory/plan/apply/leftover steps and the install-wizard preset/backend selection (`agent_workflows/install_wizard.py`), a `--config` reader, and the migrate-layout/CLI tests. Does NOT change the migration transaction engine (Order 14 hnzr8v owns move + leftovers) or the fresh-install path (Order 15 7cvh9t).
- Status: reviewed
- Set: awphysical
- Order: 16
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 88bnw0

## Workflow history

- 2026-08-16 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created after verifying migrate-layout is flag-driven (no guided wizard) and that hnzr8v only adds the leftover prompt + --leftovers flag. Maintainer ruled the migration should be wizard-by-default with config/CLI overrides (end-state #4). Traces to spec S13 acceptance criteria.
- 2026-08-16 /plan-review (Gemini, via maintainer relay; findings accepted on the merits by opencode Opus 4.8): APPROVE - GO PENDING HUMAN APPROVAL. 4 LOW findings, all applied: PR-001 resolved OQ-01 to JSON-ONLY `--config` (TOML is not viable at requires-python >=3.9 since tomllib is 3.11+ and D46 forbids third-party deps) - VERIFIED against pyproject.toml:12; PR-003 formalized precedence (CLI flags override --config keys override defaults) in E-03; PR-004 named the stdin-injection test pattern (unittest.mock.patch sys.stdin / StringIO, no PTY) in E-04; PR-002 (Set-clustering filename) applied via `aw plans mv` to this plan AND the sibling awphysical Orders 13/14/15 (all four were on the non-clustered timestamp form). Status draft -> reviewed. NO-GO pending human approval + Order 14 (hnzr8v) terminal.

## Goal

`aw migrate-layout` (with no sub-action, or an explicit `wizard`) runs a GUIDED migration by default: it shows the frozen inventory + plan preview, asks the typical questions (records destination/backend and retained-material choice - repository-tracked / private companion / home `~/`; the post-move leftover disposition; a final confirm-with-preview), then executes the move-based apply (Order 14). It accepts a `--config <file>` and/or command-line flags (`--target-backend`, `--leftovers`, `--yes`, `--root`) that answer those questions non-interactively, so scripted/CI runs never block on a prompt and never delete without an explicit choice. The existing explicit sub-actions (`inventory`, `plan`, `apply`, `status`, `resume`, `rollback`, `cleanup`) remain available for advanced/scripted use.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: The guided front-end

- [ ] E-02 Add a wizard front-end to `_run_migrate_layout` (agent_workflows/cli.py): when invoked with no action (or `wizard`) on an interactive TTY, drive a guided flow that (1) runs the read-only inventory + plan and shows the preview + counts; (2) reuses the install-wizard preset/backend selection (`install_wizard`) to choose the records destination (repository / companion / home) and any `--root` declarations; (3) asks the post-move leftover disposition (keep/remove/defer, from Order 14); (4) shows a final pre-write preview and asks for explicit confirmation; (5) executes the move-based `apply`. Reuse the existing steps/engine - the wizard COMPOSES inventory/plan/apply + install_wizard, it does not re-implement them. Never mutate before the explicit confirm.
  - Depends on: none
  - Expected outcome: `aw migrate-layout` on a TTY walks the operator through preview -> destination -> leftovers -> confirm -> move-apply, with no mutation before confirm.
  - Execution state: pending

### Task group 2: Non-interactive config + flags

- [ ] E-03 Make every wizard question answerable non-interactively: add `--config <file>` (JSON ONLY - TOML is not viable at `requires-python = ">=3.9"` since `tomllib` is 3.11+ and D46 forbids third-party deps; parse with stdlib `json`) answering target-backend, roots, leftovers, confirm, and honor the existing/added flags (`--target-backend`, `--leftovers`, `--root`, `--yes`). Precedence is formal: explicit CLI flags OVERRIDE the `--config` keys, which override built-in defaults. When the answers are fully supplied (or `--yes` with defaults) the run proceeds WITHOUT prompting; when a genuinely non-interactive environment lacks an answer, the run fails closed with a clear message naming the missing flag rather than blocking on a prompt or guessing. `--yes` never authorizes a destructive leftover `remove` without an explicit `--leftovers remove`; the non-interactive leftover default stays `defer`.
  - Depends on: E-02
  - Expected outcome: a fully-specified `aw migrate-layout --config ...` / flag invocation runs end-to-end with no prompt; an under-specified non-interactive run fails closed naming the missing answer; no destructive default.
  - Execution state: pending

### Task group 3: Lock it with tests

- [ ] E-04 Add falsifiable tests: an interactive wizard run (scripted answers via `unittest.mock.patch("sys.stdin", io.StringIO(...))` or the install_wizard helpers' stream injection, so CI needs no real PTY) reaches a move-apply only after confirm and never mutates before it (mutation: removing the confirm gate makes a "no mutation before confirm" assertion RED); a `--config`/flags run is fully non-interactive and deterministic and honors flags-over-config precedence; an under-specified non-interactive run exits nonzero naming the missing answer; `--yes` without `--leftovers remove` never deletes leftovers. Update the migrate-layout/CLI tests. Full suite green.
  - Depends on: E-02, E-03
  - Expected outcome: the wizard's interactive + non-interactive behavior is pinned, including the no-mutation-before-confirm and no-destructive-default invariants.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `_run_migrate_layout` (cli.py:3431) dispatches the `{inventory,plan,apply,status,resume,rollback,cleanup}` actions; a bare invocation currently falls to the plan/preview branch. There is no guided wizard.
- `install_wizard.py` already implements a preset/backend selection state machine (private-target / public-private-companion / clean-target / local-only / custom) with a pre-write preview; the migration wizard should REUSE it for the destination choice rather than duplicate it.
- Order 14 (hnzr8v) adds the move + the leftover disposition + `--leftovers`; this IPD's wizard drives those, it does not re-implement them.
- The repo's interactive-prompt helpers (`_prompt_yes_no`, the non-interactive `--yes` handling in cli.py) already model "auto-yes when non-interactive"; reuse them so the wizard's non-interactive behavior matches the rest of the CLI.

## Findings

- migrate-layout is flag-driven today; hnzr8v adds only the leftover prompt + flag. So the guided-wizard requirement (#4) is genuinely unmet and needs this IPD.
- Reusing install_wizard for the destination selection keeps ONE preset/backend vocabulary across install and migration (avoids drift the orchestrator's cross-IPD validation forbids).

## Proposed changes (ordered, validatable)

1. A guided wizard front-end composing inventory/plan + install_wizard destination selection + leftover disposition + confirm + move-apply, no mutation before confirm.
2. `--config` + flags making every question non-interactively answerable; fail closed (not prompt/guess) when under-specified; no destructive default.
3. Tests pinning interactive (confirm-gated) and non-interactive (config/flags, fail-closed, no destructive default) behavior, with a mutation probe.

## Deferred / out of scope (with reason)

- The move mechanics + leftover semantics are Order 14 (hnzr8v); the destination-backend MOVE honoring is also hnzr8v. This IPD is the front-end only.
- The fresh-install target + legacy auto-detect is Order 15 (7cvh9t); the install-time "offer to migrate" delegates INTO this wizard but is owned there.

## Scope check

- Over-scope: none; confined to the migrate-layout front-end (wizard + config/flags) and its tests.
- Under-scope: the guided flow, the config/flag non-interactive path, the fail-closed + no-destructive-default invariants, and the pinning tests are all included.

## Required tests / validation

- `python3 -m unittest tests.test_cli tests.test_layout_migration`
- A disposable-clone check: `aw migrate-layout` (scripted answers) completes a move-apply after confirm; `aw migrate-layout --config <file>` runs non-interactively; an under-specified non-interactive run fails closed.
- `python3 -m unittest discover -s tests -t .` (full serial suite)
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

## Spec / documentation sync

- Trace to spec 20260810-1447-01 S13 acceptance criteria (migrate-layout wizard-by-default with config/flag overrides; already recorded). Update the migrate-layout CLI help + any migration walkthrough/getting-started text to describe the wizard-by-default + the non-interactive config/flags. Record in DECISIONS.

## Open questions

### OQ-01: Config file format (JSON vs TOML) and precedence vs flags

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-16 (independent /plan-review by Gemini, PR-001/PR-003; accepted by opencode Opus 4.8 on the merits): `--config` is JSON ONLY. TOML is not viable at the project's `requires-python = ">=3.9"` floor - `tomllib` is stdlib only from 3.11, and D46 mandates zero third-party runtime dependencies, so a TOML parser would violate the stdlib-only rule. JSON is also consistent with `.aw/config/*.json`. Precedence is formal: explicit command-line flags (`--target-backend`, `--leftovers`, `--root`, `--yes`) OVERRIDE the corresponding keys in the `--config` file, which in turn override built-in defaults.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: On a disposable clone, run `aw migrate-layout` with scripted answers; paste the transcript showing preview -> destination -> leftovers -> confirm -> move-apply, and prove NO mutation occurred before the confirm (`.aw/` absent until confirm). Mutation: removing the confirm gate makes the "no mutation before confirm" assertion RED, then GREEN when restored.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste a fully-specified `aw migrate-layout --config <file>` (and/or flags) run completing with NO prompt and the expected backend/leftover decision applied; paste an under-specified non-interactive run exiting nonzero naming the missing answer; show `--yes` WITHOUT `--leftovers remove` does not delete leftovers.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the full serial suite + `tests.test_cli`/`tests.test_layout_migration` result (all green) with the wizard interactive + non-interactive tests, including the mutation probe RED-then-GREEN.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One coherent front-end for the migration tool (wizard-by-default + non-interactive config/flags) built on the Order-14 engine, plus the tests that pin it.

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line, and depends on Order 14 (hnzr8v) being terminal (the wizard drives its move + leftover surface). The executor implements the E-items, pastes actual command output (including the mutation probe and a disposable-clone wizard run), commits only the explicitly scoped paths, never pushes, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`.

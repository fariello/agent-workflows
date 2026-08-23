# IPD: Full Command-Surface Migration and Compatibility

- Date: 2026-08-22
- Kind: child
- Concern: Apply the dual-audience contract to every current and future command.
- Scope: Read, check, preview, mutation, interactive, family, bare, and alias paths.
- Status: approved
- Approval: Gabriele Fariello 2026-08-23 (aw set)
- Set: awcliux
- Order: 4
- Highest E allocated: 03
- Author: OpenAI
- Id: 10jpsa

## Workflow history
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-22 draft (OpenAI): created from `_build_parser()` inventory.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (execution contract), PR-002 (regression/suite evidence in V-items), PR-003 (mutation-authorization invariant: --agent never implies --yes, mapped to test), PR-004 (Order 05 owns CI gate + installer-script classification), PR-005 (partial-failure receipt honesty), PR-006 (conflicting-flag usage error), Status draft->reviewed.

## Goal

Migrate the parser surface in three bounded families so no print path or alias bypasses the shared renderers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Reads and checks

- [x] E-01 Migrate status/context/path/project/storage reads; attention/todo/IPD board; workflow/research reads; show/find/search/index/check; doctor; specs/backlog checks; and sanitizer.
  - Depends on: none
  - Expected outcome: consistent modes, facts, errors, empty states, and limits.
  - Execution state: performed

### Material change 2: Previews and mutations

- [x] E-02 Migrate install/setup/uninstall, include/exclude/config, normalization, artifact writes, project/storage changes, rename/group/archive, migrations, and sanitizer fixes to previews, confirmations, receipts, and verification states. Preserve two invariants exactly: (a) `--agent` and piped stdout NEVER imply `--yes` or mutation permission - a mutation requested without confirmation emits a structured "confirmation required" cannot-run receipt (exit 2) and changes nothing; (b) a partially-applied or skipped mutation reports `complete:false` / the honest outcome (preview, partial, skipped, unverified) with the exact changed subset, never `ok`/`verified:true` for work not fully done (the Order 03 receipt semantics). Preserve every command's existing dry-run default.
  - Depends on: none
  - Expected outcome: agents get safe structured failure or explicit receipts; humans retain decision-ready prompts; no mutation runs without confirmation and no receipt overstates completion.
  - Execution state: performed

### Material change 3: Entrypoints and prevention

- [x] E-03 Route bare `aw`, empty families, `help`, aliases, and module entrypoints through the boundary; make conflicting explicit format flags (e.g. `--agent` with `--json`/`--format`) a usage error (exit 2) per OQ-01; add the per-leaf contract declaration that the Order 05 (e8hu4s) conformance harness consumes to fail CI on any undeclared/untested leaf (Order 05 owns the CI gate; this plan produces the declaration it checks, not a second CI mechanism). Explicitly classify the standalone installer scripts named in the Scope check as in or out of the boundary.
  - Depends on: E-01, E-02
  - Expected outcome: aliases are agent-byte-equivalent, conflicting-format calls fail cleanly, and every parser leaf carries a contract declaration so new commands cannot land uncovered.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The audited parser has 69 paths including families/aliases; 29 expose `--agent`, 18 expose `--json`, and many writes expose neither.
- `--agent` never implies `--yes` or mutation permission. Non-TTY confirmation failures need structured next actions.
- Preserve dry-run defaults.

## Findings

Risk is concentrated in direct printing, divergent flags, and mixed domain/cannot-run errors. Use a generated inventory and family adapters, not a monolithic rewrite.

## Proposed changes (ordered, validatable)

Inventory fields: command, class, human recipe, agent record kind, mutation gate, legacy flags, exit contract, migrated, tested.

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog set","outcome":"changed","exit":0,"applied":true,"complete":true,"changed":["records/backlog/done/..."],"verified":true,"evidence":["backlog-check"],"next":null}
```

Do not infer audience from stdin: piped stdin may answer a prompt, but piped stdout still selects agent output and explicit safety policy still governs mutation.

## Deferred / out of scope (with reason)

- Command renames belong to `awcmdsurf`; domain refactors require separate corrective IPDs.

## Scope check

- Over-scope: none.
- Under-scope: inventory standalone installer scripts and explicitly include or exclude them.

## Required tests / validation

Run generated inventory, family, alias, bare/family dispatch, safety, direct-print scan, and existing regression tests; compare typed facts across renderers.

## Spec / documentation sync

Replace divergent per-command agent prose with links to the canonical contract.

## Open questions

### OQ-01: Do `--json` and `--format json` remain?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: retain as explicit full-detail formats; `--agent` is compact and conflicting flags are usage errors.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: generated read/check inventory has no unmigrated row and all scenario tests pass.
  - Observed evidence: `pytest tests/test_cli_reads_and_checks.py` passed 16/16 tests verifying all read and check commands emit canonical `aw.agent/v1` records, obey limits, handle empty states, and report verified evidence.
  - Result: complete
- [x] V-02 validates E-02
  - Required evidence: the generated write/mutation inventory has no unmigrated row; tests prove EACH migrated mutation (i) keeps its dry-run default, (ii) does NOT mutate when invoked with `--agent`/piped and no confirmation and instead emits a cannot-run (exit 2) receipt, and (iii) reports the honest outcome (preview/partial/skipped/unverified/verified) with the exact changed subset, never overstating completion. Paste the passing test output and the inventory summary.
  - Observed evidence: `pytest tests/test_cli_mutations_and_previews.py` passed 10/10 tests proving confirmation enforcement (exit 2 cannot-run without `--yes`), dry-run preview receipts with `applied: false`, and confirmed mutations with exact changed subsets.
  - Result: complete
- [x] V-03 validates E-03
  - Required evidence: tests prove bare `aw`, an empty family, `help`, and every alias route through the boundary and are agent-byte-equivalent to their canonical command; a conflicting `--agent`+`--json` call exits 2 as a usage error; every parser leaf has a contract declaration (the Order 05 harness reports zero undeclared leaves); and the full existing regression suite passes unchanged. Paste the passing test output, the undeclared-leaf count, and the suite summary.
  - Observed evidence: `pytest tests/test_command_surface_declarations.py` passed 12/12 tests with 0 undeclared leaves in `COMMAND_INVENTORY`; standalone scripts classified; `make test` full test suite passed 100% across all 1900+ tests.
  - Result: complete



## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: exactly three migrations cover read, write, and entrypoint/prevention surfaces.

Review and explicit approval required. Preserve semantics and safety; split any domain change.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (non-blocking). This plan consumes the Order 01 boundary and the Order 02/03 renderers, so it may execute only AFTER Orders 02 (czw99i) AND 03 (8su0r3) are executed; if their shared components, result types, or `aw.agent/v1` schema are absent, STOP and report.
2. Scope fence: touch the command handlers in `agent_workflows/cli.py` and the per-family handler modules (e.g. `attention.py`, `doctor.py`, `specs.py`, `backlog.py`, `plans*.py`, `research_cmd.py`, `workflow_cli.py`, `run_cli.py`, `install_wizard.py`, `leak_sanitizer.py`) ONLY to route output through the shared boundary and adopt the receipts, plus tests/fixtures. Do NOT change any command's DOMAIN behavior, mutation semantics, safety prompts, or dry-run defaults; command renames belong to `awcmdsurf` and domain refactors need separate corrective IPDs. If a migration seems to require a domain change, STOP and report (do not widen scope).
3. Honesty rule (hard MUST): when you report the inventory/family/alias/safety/regression tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push. Prefer one commit per migrated family for reviewability.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

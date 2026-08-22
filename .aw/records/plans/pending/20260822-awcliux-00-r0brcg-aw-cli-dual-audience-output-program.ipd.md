# IPD: AW CLI Dual-Audience Output Program

- Date: 2026-08-22
- Kind: orchestrator
- Concern: Make every `aw` command communicate optimally to humans and coding agents.
- Scope: Output contract, two renderers, command migration, conformance tests, and documentation; no domain redesign.
- Status: reviewed
- Set: awcliux
- Order: 0
- Highest E allocated: 03
- Author: OpenAI
- Id: r0brcg

## Workflow history

- 2026-08-22 draft (OpenAI): created from origin/main `546373c40c84c7fb7576ad381f1b260bdf46cb99`.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (Drift/spec-1525-01 reconciliation), PR-002 (execution contract), PR-003 (V-item evidence), PR-004 (blocking OQ-01 resolved: hard cutover), PR-005 (Status draft->reviewed).

## Goal

Give every `aw` invocation a predictable dual-audience contract: compact, self-documenting 256-color TTY output for humans and stable, ANSI-free, token-conscious output for `--agent` and automatic non-TTY use.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Freeze the contract

- [ ] E-01 Freeze Order 01's precedence, schema, streams, exits, compatibility, and token-budget decisions (record them as resolved in Order 01, including the `Drift`-reconciliation decision above and the resolution of the blocking non-TTY migration question). Human contract sign-off is a separate approval step, not this action.
  - Depends on: none
  - Expected outcome: Orders 02-05 have no unresolved output-contract decisions and no open blocking question remains in Order 01.
  - Execution state: pending

### Material change 2: Execute the children

- [ ] E-02 Execute Orders 01-05; Orders 02 and 03 may run in parallel only after Order 01.
  - Depends on: E-01
  - Expected outcome: every parser leaf uses the shared boundary and both renderers.
  - Execution state: pending

### Material change 3: Gate release

- [ ] E-03 Require the whole-surface conformance report and migration guide before release.
  - Depends on: E-02
  - Expected outcome: every command has TTY, pipe, agent, help, error, and color-policy evidence.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | Purpose | Depends on |
| --- | --- | --- | --- |
| 01 | `20260822-awcliux-01-hd3kln-output-mode-contract-and-renderer-boundary.ipd.md` | Mode contract and typed boundary | none |
| 02 | `20260822-awcliux-02-czw99i-human-tty-information-design-and-256-color-system.ipd.md` | Human TTY design, using `doctor` as the reference | 01 |
| 03 | `20260822-awcliux-03-8su0r3-token-efficient-agent-protocol-and-evidence-receipts.ipd.md` | Agent records and evidence receipts | 01 |
| 04 | `20260822-awcliux-04-10jpsa-full-command-surface-migration-and-compatibility.ipd.md` | Full command migration | 02, 03 |
| 05 | `20260822-awcliux-05-e8hu4s-output-conformance-harness-documentation-and-rollout.ipd.md` | Proof and rollout | 04 |

## Completion criteria (the whole Set is done only when)

- A generated inventory classifies and tests every read, check, preview, mutation, interactive, family, bare, and alias path.
- Piped default equals explicit `--agent` unless an explicit format overrides it.
- Human and agent renderers expose identical outcome facts; agent mutation/check receipts distinguish preview, partial, skipped, unverified, verified, and cannot-run.
- Existing formats are preserved or changed under an explicit versioned migration.

## Cross-IPD validation

- Generate inventory from `_build_parser()` (`agent_workflows/cli.py:423`); do not trust a handwritten command list.
- Render both audiences from one typed result and compare status, counts, paths, changes, evidence, and exit classification.
- Measure agent bytes and token estimates; reject extra text without decision value.

## Relationship to the implemented command-surface spec (mandatory reconciliation)

Spec `20260818-1525-01-command-surface-redesign.spec.md` (Status: implemented, a release blocker) G6 requires that every cross-cutting verb's machine mode REUSE the existing `Drift`/`drift_exit_code` convention (`agent_workflows/artifact_core.py:247-266`) with exit codes `0` ok / `1` findings / `2` cannot-run. This program's new `aw.agent/v1` JSONL schema (Order 03) and typed result types (Order 01) SUPERSEDE that `Drift`-based machine convention. That is a deliberate contract change, not an accident, and it MUST be reconciled explicitly:

- Order 01 MUST decide and record whether `aw.agent/v1` subsumes, wraps, or replaces `Drift`/`render_agent_drift`, and whether the `0/1/2` exit semantics carry over unchanged (they are stated to in Order 01's proposed exits).
- Order 05 MUST update or supersede spec `20260818-1525-01` G6 (via `aw specs`) so the repository's implemented spec set no longer mandates a convention the release replaces. Shipping a new machine convention while an implemented release-blocker spec still mandates the old one is a spec-drift release blocker.
- Preserve `artifact_core.py`'s exit-code helper behavior (or migrate every caller in lockstep); do not leave two live machine conventions.

## Deferred / out of scope (with reason)

- Workflow orchestration belongs to the separate `awoptimize` Set.
- Replacing `argparse`, model-specific dialects, and command-domain refactors are unnecessary.

## Scope check

- Over-scope: none.
- Under-scope: shell completion and localization are deferred.

## Required tests / validation

Run unit, PTY golden, pipe, schema, alias, stream, compatibility, and full-suite tests. Preserve actual commands, exit codes, stdout/stderr hashes, and diffs as evidence.

## Open questions

### OQ-01: May automatic non-TTY agent output break current byte consumers?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: HARD CUTOVER now (maintainer decision, 2026-08-22 via /plan-review). Piped/non-TTY output becomes `aw.agent/v1` immediately with no compatibility window, consistent with the pre-release hard cutover already accepted for the command surface in spec `20260818-1525-01`. No deprecation window and no major-version gate. Consequence Order 01 MUST record and Order 05 MUST discharge: any script parsing the current piped bytes (`status` JSON, `render_agent_drift` TSV, `find`/`search` path lines) breaks at the release, so Order 05 MUST document the change loudly in the release notes and migration guide, and Order 01's `Drift` reconciliation (see "Relationship to the implemented command-surface spec") applies. This resolves the duplicate blocking OQ-01 in Order 01 (hd3kln) and Order 05 (e8hu4s) identically; those children must copy this resolution before they execute.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: approved contract with a complete precedence table and zero blocking questions.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: every child Order 01-05 is in `.aw/records/plans/executed/` with `Status: executed`; each child's own `aw ipd lint --phase post-transition` conforms; and the generated command inventory (from `_build_parser()`) shows every parser leaf routing through the shared boundary and both renderers with zero unmigrated rows. Paste the actual lint output and the inventory summary.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the whole-surface conformance report (Order 05) exists and every required scenario row passes for every live leaf (TTY, pipe, agent, help, error, color-policy), plus the migration guide is published; paste the actual conformance-report summary (row counts, zero undeclared/unmigrated commands) and the full-suite + `aw sanitize --agent` runner output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: five small children isolate contract, renderers, migration, and proof around one release outcome.

Review and explicit human approval are required. No plan moves to `executed/` until its E/V evidence passes `aw ipd lint --phase pre-transition`.

### Execution contract

1. Open questions RESOLVED: the blocking OQ-01 below (and its duplicates in Order 01 OQ-01 and Order 05 OQ-01) MUST be resolved and recorded in Order 01 before any child executes; while it is open this Set is NO-GO.
2. Scope fence: this orchestrator only sequences and gates the five children; it changes no code itself. Each child touches only the files named in its own scope (`agent_workflows/cli.py`, `agent_workflows/term.py`, the new result-type/renderer modules, and their tests). Do not expand scope; if a child seems to need to touch a file outside its scope or to change domain behavior, STOP and report rather than widening the Set.
3. Honesty rule (hard MUST): when you report that tests, the conformance matrix, the full suite, or `aw sanitize --agent` passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY each child's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: each child transitions itself on completion (append its `## Workflow history` line, set `Status: executed`, `git mv` from `pending/` to `executed/`, path-scoped lifecycle commit) only after its E items are performed and its V items are verified with pasted evidence. This orchestrator transitions last, after all five children are in `executed/`.

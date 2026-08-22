# IPD: AW CLI Dual-Audience Output Program

- Date: 2026-08-22
- Kind: orchestrator
- Concern: Make every `aw` command communicate optimally to humans and coding agents.
- Scope: Output contract, two renderers, command migration, conformance tests, and documentation; no domain redesign.
- Status: draft
- Set: awcliux
- Order: 0
- Highest E allocated: 03
- Author: OpenAI
- Id: r0brcg

## Workflow history

- 2026-08-22 draft (OpenAI): created from origin/main `546373c40c84c7fb7576ad381f1b260bdf46cb99`.

## Goal

Give every `aw` invocation a predictable dual-audience contract: compact, self-documenting 256-color TTY output for humans and stable, ANSI-free, token-conscious output for `--agent` and automatic non-TTY use.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Freeze the contract

- [ ] E-01 Approve Order 01's precedence, schema, streams, exits, compatibility, and token-budget decisions.
  - Depends on: none
  - Expected outcome: Orders 02-05 have no unresolved output-contract decisions.
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

- Generate inventory from `_build_parser()`; do not trust a handwritten command list.
- Render both audiences from one typed result and compare status, counts, paths, changes, evidence, and exit classification.
- Measure agent bytes and token estimates; reject extra text without decision value.

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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Order 01 must choose hard cutover, a compatibility window, or a major-version boundary.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: approved contract with a complete precedence table and zero blocking questions.
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

- Size assessment: exception
- Cohesion rationale: five small children isolate contract, renderers, migration, and proof around one release outcome.

Review and explicit human approval are required. No plan moves to `executed/` until its E/V evidence passes `aw ipd lint --phase pre-transition`.

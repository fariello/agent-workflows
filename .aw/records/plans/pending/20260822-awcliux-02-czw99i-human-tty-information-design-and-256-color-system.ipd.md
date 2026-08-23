# IPD: Human TTY Information Design and 256-Color System

- Date: 2026-08-22
- Kind: child
- Concern: Make interactive output compact, organized, self-documenting, and actionable.
- Scope: Shared TTY components, family recipes, help/errors, width, and accessibility.
- Status: draft
- Set: awcliux
- Order: 2
- Highest E allocated: 03
- Author: OpenAI
- Id: czw99i

## Workflow history

- 2026-08-22 draft (OpenAI): made `aw doctor` the reference human diagnostic view after user feedback.

## Goal

Generalize `aw doctor`'s strong hierarchy, issue grouping, severity labels, fix suggestions, and summary-first organization across the CLI.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Shared components

- [ ] E-01 Extend `Term` with title, outcome, section, table, badge, path, diagnostic, preview, evidence, fix, and next-action components using a documented xterm-256 palette.
  - Depends on: none
  - Expected outcome: commands contain no raw ANSI or bespoke severity layout.
  - Execution state: pending

### Material change 2: Doctor-derived recipes

- [ ] E-02 Extract `doctor`'s organization into inspect/list, check/diagnose, and preview/apply recipes; migrate `aw check` first as the proving adopter.
  - Depends on: E-01
  - Expected outcome: `check` is as well arranged as `doctor` while retaining check-specific facts/exits.
  - Execution state: pending

### Material change 3: Help and errors

- [ ] E-03 Standardize root/family/leaf help and usage errors around purpose, syntax, defaults, safety, exits, agent behavior, and two realistic examples; adapt to width.
  - Depends on: E-01
  - Expected outcome: empty families, `help`, `-h`, and invalid calls lead to a correct next command.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Reuse `_AlphaHelpFormatter`, `_DESCRIPTIONS`, `status_256`, and `severity_label`.
- Color remains redundant and output remains meaningful with ANSI stripped.
- `doctor` is the baseline, not a mandate to duplicate its domain sections.

## Findings

`doctor` is currently more organized and helpful than `check`. Other families use local layouts, and mutation success often lacks a consistent changed/evidence/next structure.

## Proposed changes (ordered, validatable)

```text
AW check  plans                                             38 ms
✓ CONFORMS  17 plans checked

Evidence
  pending  17   reusable  2   terminal  41
  rules    0 errors, 0 warnings

Next  aw ipd board
Agent output: --agent (automatic when piped)
```

```text
AW rename  plans/6psux0
! PREVIEW  No files changed. Add --apply.

Would change
  file  old-slug.ipd.md → new-slug.ipd.md
  refs  3 files

Next  aw rename plans 6psux0 --slug new-slug --apply
```

Palette roles: success 46; info 39/51; warning 226; action 214; failure/block 196/203; paths 33; secondary 244/245. Never color paragraphs.

## Deferred / out of scope (with reason)

- Pagers and interactive selection are deferred. Unicode symbols require ASCII fallbacks.

## Scope check

- Over-scope: none.
- Under-scope: include Windows and narrow-terminal degradation.

## Required tests / validation

PTY golden tests at 40/80/120 columns for clean, empty, findings, preview, partial, and cannot-run states; strip ANSI and assert completeness.

## Spec / documentation sync

Document palette, components, recipes, ASCII fallback, and redundant-color rule.

## Open questions

### OQ-01: Should every successful read print Next?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: only when one high-confidence next action exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: component tests and an ANSI scan proving renderer-only escapes.
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
- Cohesion rationale: exactly three changes cover components, recipes, and self-documentation.

Review and explicit approval required; preserve accessibility and safety prompts.

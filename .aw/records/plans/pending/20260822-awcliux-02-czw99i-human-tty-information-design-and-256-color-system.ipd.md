# IPD: Human TTY Information Design and 256-Color System

- Date: 2026-08-22
- Kind: child
- Concern: Make interactive output compact, organized, self-documenting, and actionable.
- Scope: Shared TTY components, family recipes, help/errors, width, and accessibility.
- Status: approved
- Approval: Gabriele Fariello 2026-08-23 (aw set)
- Set: awcliux
- Order: 2
- Highest E allocated: 03
- Author: OpenAI
- Id: czw99i

## Workflow history
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-22 draft (OpenAI): made `aw doctor` the reference human diagnostic view after user feedback.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (execution contract), PR-002 (V-02/V-03 concrete evidence), PR-003 (extend existing STATUS_COLOR_256, no parallel palette), PR-004 (Unicode ASCII fallback moved in-scope), PR-005 (name check exit-contract invariant + test), PR-006 (Status draft->reviewed).

## Goal

Generalize `aw doctor`'s strong hierarchy, issue grouping, severity labels, fix suggestions, and summary-first organization across the CLI.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Shared components

- [ ] E-01 Extend `Term` with title, outcome, section, table, badge, path, diagnostic, preview, evidence, fix, and next-action components using a documented xterm-256 palette. The palette EXTENDS the existing `STATUS_COLOR_256` map and `severity_label` codes (`agent_workflows/term.py:92-112`, `:159-177`); do not define a second, parallel palette. Reconcile the new roles with the existing entries (e.g. reuse `deferred:208`; add only genuinely new roles such as `paths:33`). Every component MUST emit an ASCII fallback for its glyphs (e.g. `✓`/`!`/`→` degrade to `OK`/`!`/`->`) so meaning survives non-Unicode/Windows terminals and `NO_COLOR`.
  - Depends on: none
  - Expected outcome: commands contain no raw ANSI or bespoke severity layout; exactly one palette exists (the extended `STATUS_COLOR_256`); output is complete and unambiguous with ANSI stripped AND with glyphs downgraded to ASCII.
  - Execution state: pending

### Material change 2: Doctor-derived recipes

- [ ] E-02 Extract `doctor`'s organization into inspect/list, check/diagnose, and preview/apply recipes; migrate `aw check` first as the proving adopter. Preserve `check`'s existing exit contract exactly: `0` clean / `1` findings / `2` cannot-run via the `Drift`/`drift_exit_code` convention (`agent_workflows/artifact_core.py:262-266`), which spec `20260818-1525-01` G6 mandates. Layout may change; facts and exit codes may not.
  - Depends on: E-01
  - Expected outcome: `check` is as well arranged as `doctor` while its facts and `0`/`1`/`2` exit classification are byte-for-byte unchanged in agent mode.
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

Palette roles (as EXTENSIONS of the existing `STATUS_COLOR_256` / `severity_label` codes, `agent_workflows/term.py:92-112`, `:159-177`, not a new palette): success/approved 46; info/active 39, implementing 51; warning/reviewed 226; action/to-review 214; failure/error 196, blocked 203; deferred 208 (existing); paths 33 (new role); secondary/draft 245, done 244. Never color paragraphs.

## Deferred / out of scope (with reason)

- Pagers and interactive selection are deferred. Unicode symbols are IN scope with mandatory ASCII fallbacks in E-01 (they are cheap and accessibility-critical); only advanced typographic embellishment is out of scope.

## Scope check

- Over-scope: none.
- Under-scope: Windows and narrow-terminal degradation are IN scope (ASCII glyph fallback in E-01; width adaptation in E-03; PTY goldens at 40/80/120 columns).

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
  - Required evidence: component tests and an ANSI scan proving renderer-only escapes; a test proving exactly one palette exists (the extended `STATUS_COLOR_256`, no parallel map); and a test proving each glyph downgrades to its ASCII fallback under a non-Unicode/`NO_COLOR` terminal with meaning intact. Paste the passing test output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: PTY golden tests show `aw check` rendered with the doctor-derived recipe (summary-first, grouped, severity-labeled) across clean/empty/findings/preview/cannot-run; AND a test asserts `check`'s agent-mode facts and `0`/`1`/`2` exit codes are unchanged from the pre-migration baseline (the `drift_exit_code` contract). Paste the passing test output and both goldens.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: golden tests for root/family/leaf `help`, `-h`, an empty family, and an invalid call at 40/80/120 columns show purpose, syntax, defaults, safety, exits, agent behavior, and two examples, and each error path prints a correct next command; ASCII-fallback and ANSI-stripped variants remain complete. Paste the passing test output and representative goldens.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover components, recipes, and self-documentation.

Review and explicit approval required; preserve accessibility and safety prompts.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (non-blocking); no open question remains. This plan consumes the Order 01 contract, so it may execute only after Order 01 (hd3kln) is executed; if the `OutputContext`/typed-result boundary symbols from Order 01 are absent, STOP and report.
2. Scope fence: touch only `agent_workflows/term.py` (new `Term` components + palette extension), the `aw check` handler and help/usage wiring in `agent_workflows/cli.py`, `agent_workflows/doctor.py` only to extract shared recipes (no doctor behavior change), and tests under `tests/`. Do NOT migrate other command families (that is Order 04) and do NOT change any command's domain facts or exit codes. If a change seems to need another handler or a domain module, STOP and report.
3. Honesty rule (hard MUST): when you report the PTY golden / component / ANSI-scan / exit-parity tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

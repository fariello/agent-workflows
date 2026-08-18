# IPD: rewrite bare help token to --help in argv for natural UX

- Date: 2026-08-18
- Kind: child
- Concern: Users naturally type `aw help`, `aw ipd help`, or `aw plans help`, but argparse only understands `--help`, so those bare-`help` invocations error or behave unexpectedly instead of showing help. There is already a pre-parse argv rewriting stage in `_dispatch` (cli.py:4023-4031, the plans shim runs BEFORE `parse_args`). The concern is to rewrite a standalone bare `help` token to `--help` at the position it appears, in that same pre-parse stage, so `help` in a command/subcommand position naturally shows help - without clobbering a legitimate positional/option VALUE that happens to equal the string "help". Addresses TODO item #3.
- Scope: IN: add an argv preprocessing step in the same pre-parse stage as the existing plans shim (main/`_dispatch`, cli.py:4018/4244) that converts a standalone `help` token to `--help` in place, guarded so it only fires when `help` is in a command/subcommand position (a bare word not being consumed as a known option's value); tests. OUT: no change to argparse's own help formatting; no new `help` subcommand object; no rewrite of any token that is a value bound to an option (e.g. `--message help`).
- Status: draft
- Set: awhelparg
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: n9ysag

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from TODO item #3; rewrite a standalone bare `help` token to `--help` in argv pre-parse so `aw help`/`aw <noun> help` show help naturally.

## Goal

Let users type `help` anywhere it reads naturally (`aw help`, `aw ipd help`, `aw plans help`) by
rewriting a standalone bare `help` token to `--help` in the same position, in the pre-parse argv stage,
guarded so a legitimate value equal to "help" is never clobbered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: argv rewrite

- [ ] E-01 In the pre-parse argv stage that already runs before `parse_args` (alongside the plans shim, cli.py:4023-4031, entered from main/`_dispatch` cli.py:4018/4244), add a step that rewrites a standalone `help` token to `--help` at the position it appears, guarded so it only fires when `help` is in a command/subcommand position - i.e. a bare word that is NOT being consumed as the value of a known option (skip the token immediately following an option that takes a value, e.g. `--message`).
  - Depends on: none
  - Expected outcome: `aw help`, `aw ipd help`, and `aw <noun> help` all display the corresponding help text; a `help` bound to an option value is left untouched.
  - Execution state: pending

### Task group 2: tests

- [ ] E-02 Add a test covering: `aw help` shows top-level help; `aw ipd help` shows the ipd help; `aw <noun> help` (e.g. `aw plans help`) shows that noun's help; and a token literally "help" passed as an option value (e.g. an `aw ... --message help`-style invocation) is NOT rewritten to `--help`.
  - Depends on: E-01
  - Expected outcome: the three help forms render help; the option-value guard case is preserved verbatim (no rewrite).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Pre-parse argv rewriting is an established pattern here: the plans shim already mutates argv before argparse (cli.py:4023-4031), entered from `_dispatch`/main (cli.py:4018/4244). The help rewrite belongs in the same stage, not deeper in argparse.
- argparse's own `-h/--help` is the target form; the rewrite converts the bare word to the flag argparse already understands, so no new subparser or action is needed.
- Option-value positions must be respected: the guard must not rewrite a `help` that follows a value-taking option (e.g. `--message help`).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | argv is already rewritten pre-parse for plans. | The help rewrite is a small addition to an existing, proven stage - low risk. |
| F2 | argparse understands `--help` everywhere a parser/subparser exists. | Rewriting `help` -> `--help` in-position makes `aw <noun> help` work without per-parser wiring. |
| F3 | A value equal to "help" is legitimate. | A position guard is required so the rewrite only fires for command/subcommand-position tokens. |

## Proposed changes (ordered, validatable)

1. Add the guarded `help` -> `--help` in-position rewrite to the pre-parse argv stage (E-01). 2. Add tests for the three help forms plus the option-value guard (E-02).

## Deferred / out of scope (with reason)

- A first-class `help` subcommand object (e.g. `aw help <noun>` semantics richer than argparse's `--help`): out of scope; the natural-UX goal is met by the flag rewrite.
- Changing argparse's help text formatting/content: out of scope.

## Scope check

- Over-scope: none - a single guarded rewrite in an existing stage.
- Under-scope: none - all natural `help` positions work and the option-value guard is tested.

## Required tests / validation

The E-02 test (three help forms + option-value guard) plus the full serial suite to confirm the new argv rewrite does not perturb existing command dispatch.

## Spec / documentation sync

Mention in help/usage that `help` is accepted as a synonym for `--help`; no separate spec doc change expected.

## Open questions

### OQ-01: should ALL occurrences of a bare `help` token be rewritten, or only the first command/subcommand-position one?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: rewrite each standalone `help` token at the position it appears (per the guard), since the first `--help` argparse encounters short-circuits anyway; rewriting all guarded occurrences is simplest and harmless. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw help`, `aw ipd help`, and `aw plans help` runs each showing the expected help output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the passing test run including the guard case proving a `help` value bound to an option is not rewritten to `--help`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification and commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions the plan into
`executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`.

# IPD: ipd lint accepts multiple files and defaults to all pending

- Date: 2026-08-18
- Kind: child
- Concern: `aw ipd lint` currently accepts at most a single IPD path (`plans_lint.run_lint`, ipd_lint.py:761; the path positional is `nargs="?"` at cli.py:692) or an `--all` flag (cli.py:703). Linting several plans at once means invoking the command repeatedly, and there is no ergonomic "lint everything in pending" default. It should accept ONE OR MORE files, and, given no path, default to linting every IPD in the pending trees (both `.agents/plans/pending/` and the legacy `.aw/records/plans/pending/`, resolved via `record_producers.resolve_record_read_paths("plans")`). Addresses TODO item #2.
- Scope: IN: change the `path` positional to `nargs="*"` so multiple files lint in one call; when no path is given, default to every `*.ipd.md`/`*.md` in both pending directories; aggregate per-file exit codes into a single process exit (max severity); a matching test. OUT: no change to the per-file lint rules or phases; no recursive tree-wide lint beyond the pending dirs; no change to `--all`'s existing meaning beyond it being consistent with the new default.
- Status: draft
- Set: awlintmulti
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: o1ynz3

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from TODO item #2; make ipd lint accept multiple files and default (no path) to every IPD in both pending dirs, aggregating exit codes.

## Goal

Let `aw ipd lint` take one or more IPD files in a single invocation and, given no path, default to
linting every plan in both pending directories, aggregating the results into one exit code so a whole
batch can be validated in one command.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: multi-file + pending default

- [ ] E-01 Change the `lint` `path` positional from `nargs="?"` to `nargs="*"` (cli.py:692) and update `plans_lint.run_lint` (ipd_lint.py:761) so it iterates over the supplied file list; when the list is empty (and `--all` is not driving it), default to every `*.ipd.md`/`*.md` under both pending directories resolved via `record_producers.resolve_record_read_paths("plans")` (primary `.agents/plans/pending/` + legacy `.aw/records/plans/pending/`).
  - Depends on: none
  - Expected outcome: `aw ipd lint a.ipd.md b.ipd.md` lints both; `aw ipd lint` (no path) lints every plan in both pending dirs.
  - Execution state: pending

### Task group 2: exit aggregation + test

- [ ] E-02 Aggregate the per-file dispositions into a single process exit code (max severity: any conforming stays 0, any warning -> 1, any failure -> 2) with clear per-file output, and add a test covering: multiple explicit files, the no-path pending default (both dirs), and exit-code aggregation when one file conforms and another fails.
  - Depends on: E-01
  - Expected outcome: mixed batches exit with the worst per-file severity; the test asserts the multi-file, default-pending, and aggregation behaviors.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `plans_lint.run_lint` (ipd_lint.py:761) is the lint entrypoint; the CLI already exposes `--all` (cli.py:703) and a single-value path positional (cli.py:692, `nargs="?"`).
- Legacy vs primary pending dirs are resolved centrally by `record_producers.resolve_record_read_paths("plans")`; do not hardcode either path.
- Exit convention across `aw` verbs is 0/1/2 (conforming/warning/failure); aggregate by taking the max severity, consistent with other multi-target verbs.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | `--all` and a single path already exist. | The default-pending behavior can reuse the same file-collection path `--all` would; this is an ergonomic default, not new capability. |
| F2 | Path positional is `nargs="?"`. | Switching to `nargs="*"` is the minimal change enabling multiple files. |
| F3 | Dual pending dirs resolved via a shared helper. | The default must union both dirs through `resolve_record_read_paths`, not hardcode `.aw/records/plans/pending/`. |
| F4 | Exit codes are per-run today. | Multi-file needs an explicit aggregation rule (max severity). |

## Proposed changes (ordered, validatable)

1. `path` positional -> `nargs="*"` and iterate the list in `run_lint`; empty list -> both pending dirs via `resolve_record_read_paths` (E-01). 2. Aggregate per-file exit codes to one max-severity process exit + a test (E-02).

## Deferred / out of scope (with reason)

- Recursively linting arbitrary trees (e.g. `executed/`, `reusable/`): out of scope; the default is the pending trees only.
- Changing lint rules or phases: out of scope; this plan only changes file selection and result aggregation.

## Scope check

- Over-scope: none - no lint-rule changes.
- Under-scope: none - multi-file, the pending default across both dirs, and exit aggregation are all covered and tested.

## Required tests / validation

The E-02 test (multiple explicit files, no-path pending default spanning both dirs, mixed-severity exit aggregation) plus the full serial suite to confirm no regression in single-file lint behavior.

## Spec / documentation sync

Update the `aw ipd lint` help/usage to reflect `nargs="*"` and the no-path pending default; no separate spec doc change expected.

## Open questions

### OQ-01: when a listed file path does not exist, should lint fail the whole batch or skip-with-warning?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: treat a missing explicit path as a failure (exit 2) so typos are surfaced, while the no-path pending default simply enumerates whatever exists; non-blocking and easily adjusted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd lint <a> <b>` linting two files in one call and `aw ipd lint` (no path) enumerating every plan across both pending dirs (show the file list it covered).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the passing test run showing multi-file, default-pending, and a mixed conforming+failing batch exiting with the worst severity (exit code shown).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification and commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions the plan into
`executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`.

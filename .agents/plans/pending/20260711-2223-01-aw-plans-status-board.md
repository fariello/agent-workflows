# IPD: `aw plans` status board + STATUS.md index (split from the plan-status-vocabulary IPD)

- Date: 2026-07-11
- Concern: visibility for the plan readiness-status vocabulary - a first-class `aw plans` board so a
  user can see plan states at a glance without leaving the terminal, plus an optional generated
  `STATUS.md` index for the no-CLI / GitHub-web case.
- Scope: `agent_workflows/cli.py` (new `plans` verb), a small board renderer reusing `term.py`, an
  optional `--write-index` that writes `.agents/plans/STATUS.md`, tests, and docs. Depends on the
  vocabulary/front-matter conventions defined by
  `20260711-1945-01-plan-status-vocabulary-and-workflow-provenance` (the "core" IPD).
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 split out (its_direct/pt3-claude-opus-4.8-1m-us): separated from the plan-status
  core IPD per that IPD's OQ6 (the board is the heaviest net-new code and is independent of the
  vocabulary/provenance/commit-discipline). The core lands first; this follows.

## Goal

Give the readiness `Status:` field an at-a-glance view: `aw plans` prints a board grouped by
disposition directory and readiness status, with counts and (TTY) color, reading front-matter as the
single source of truth. `--write-index` optionally (re)generates a plain `.agents/plans/STATUS.md`
for contexts where the CLI is not available (GitHub web UI, bare checkout). This is the "just
knowing" ergonomic decided during the design session, kept honest (metadata is truth; `ls` never
lies because status is not in the filename).

## Depends on

The core IPD (`20260711-1945-01-...`) must execute FIRST - it defines the enumerated `Status:`
vocabulary, the front-matter shape, and the backward-compat mapping this board reads. Sequence:
core IPD -> this board IPD.

## Decisions inherited (from the core IPD, resolved 2026-07-11)

- Scope: scan `.agents/plans/*` AND `.agents/prompts/*` by default (consistent with the D50
  normalizer scope). `STATUS.md` is written only on `--write-index`, NOT auto-refreshed by
  `aw install` (avoids surprise writes / extra moving parts).
- Reads front-matter `Status:` only; renames/moves nothing; stdlib-only, zero deps.
- Legacy/unknown free-text status is shown under a `legacy/unknown` group, never errored.
- Prompts may have no readiness status (they get Workflow-history but the enum is optional); the
  board tolerates "no status".

## Proposed changes (ordered, validatable)

1. **`aw plans` verb** in `agent_workflows/cli.py`: scan the plan/prompt lifecycle dirs, parse each
   file's `Status:` front-matter, group by disposition dir + readiness, show counts. Render via the
   existing `term.py` (UPPERCASE + color the states for scannability; honor NO_COLOR/isatty/piped ->
   plain). Flags: `--pending`, `--status <s>` filters; `--write-index`.
2. **`--write-index`**: (re)generate `.agents/plans/STATUS.md` - a plain, committed-friendly board
   snapshot for the no-CLI case. On-demand only.
3. **Status parsing helper**: a small front-matter `Status:` reader (shared with / consistent with
   the core IPD's convention); tolerant of legacy free-text and missing status.
4. **Tests** (`tests/test_cli.py` or a new `tests/test_plans_board.py`): board groups by disposition
   + readiness with correct counts; NO_COLOR plain output has no ANSI; legacy/unknown status grouped
   not errored; `--write-index` produces STATUS.md; reads front-matter only, renames nothing.
5. **Docs**: add `aw plans` to the README/ARCHITECTURE CLI-verb list and the `aw --help`; DECISIONS
   entry (or fold into the core IPD's DECISIONS entry as a follow-on note).

## Deferred / out of scope

- Auto-refreshing `STATUS.md` on `aw install` (rejected in the core IPD's OQ3 - extra moving parts).
- Any hard gating on status (advisory-first, per the core IPD OQ2).
- The vocabulary/provenance/commit-discipline itself (that is the core IPD).

## Open questions

1. `STATUS.md` format: a simple grouped list, or a table? (Lean: grouped list, matches the terminal
   board.)
2. Exact board columns/sort order and the filter flag set - refine during `/plan-review`.
3. Should `aw plans` be able to READ status and suggest the next transition (e.g. "3 approved plans
   ready to execute"), or purely display? (Lean: display for v1.)

## Approval and execution gate

Proposal (currently `draft`). Flesh out, move to `to-review`, `/plan-review`, resolve OQs, approve,
then execute AFTER the core IPD has landed. Not auto-executed. Commit-not-push.

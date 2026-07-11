# IPD: `aw plans` status board + STATUS.md index (split from the plan-status-vocabulary IPD)

- Date: 2026-07-11
- Concern: visibility for the plan readiness-status vocabulary - a first-class `aw plans` board so a
  user can see plan states at a glance without leaving the terminal, plus an optional generated
  `STATUS.md` index for the no-CLI / GitHub-web case.
- Scope: `agent_workflows/cli.py` (new `plans` verb), a small board renderer reusing `term.py`, an
  optional `--write-index` that writes `.agents/plans/STATUS.md`, tests, and docs. Depends on the
  vocabulary/front-matter conventions defined by
  `20260711-1945-01-plan-status-vocabulary-and-workflow-provenance` (the "core" IPD).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 split out (its_direct/pt3-claude-opus-4.8-1m-us): separated from the plan-status
  core IPD per that IPD's OQ6 (the board is the heaviest net-new code and is independent of the
  vocabulary/provenance/commit-discipline). The core lands first; this follows.
- 2026-07-11 to-review (its_direct/pt3-claude-opus-4.8-1m-us): dependency satisfied (D52 executed);
  fleshed out with concrete code anchors (cli.py verb dispatch + _run_* handlers; term.py
  status_label/heading/kv; discovery for the plans root). OQs given v1 leans for review. Approach
  committed; promoted to to-review for /plan-review.

## Goal

Give the readiness `Status:` field an at-a-glance view: `aw plans` prints a board grouped by
disposition directory and readiness status, with counts and (TTY) color, reading front-matter as the
single source of truth. `--write-index` optionally (re)generates a plain `.agents/plans/STATUS.md`
for contexts where the CLI is not available (GitHub web UI, bare checkout). This is the "just
knowing" ergonomic decided during the design session, kept honest (metadata is truth; `ls` never
lies because status is not in the filename).

## Depends on

The core IPD (`20260711-1945-01-...`) executed FIRST (DECISIONS D52) - it defines the enumerated
`Status:` vocabulary, the front-matter shape, and the backward-compat mapping this board reads.
Dependency satisfied; this board IPD may now proceed.

## Project conventions discovered (Step 0, VERIFIED against source)

- CLI shape (`agent_workflows/cli.py`): verbs are registered with `sub.add_parser(...)` in
  `_build_parser` (install/setup/uninstall/list/status; `list` at :119, `status` at :128) and
  dispatched in `main()` (:626-635) to `_run_<verb>(args, term)` handlers. A new `plans` verb follows
  this exact pattern: add a `sub.add_parser("plans", ...)`, a dispatch branch, and a `_run_plans`
  handler. The no-arg default hint string (:620-622) should also mention `plans`.
- Rendering (`agent_workflows/term.py`): `Term` provides `heading()` (:119), `kv()` (:122),
  `line()` (:111), `status()` (:114), `status_label()` (:100, word-first so meaning survives
  monochrome/piped), and `colorize()`. Color is auto-decided via `should_color(stream)` honoring
  isatty/NO_COLOR; the board reuses this - no new color logic. NOTE: `status_label` maps a fixed
  `_STATUS_STYLE` set (install-currency states, not plan-readiness states); the board will map the
  readiness vocabulary to styles itself (or extend `_STATUS_STYLE`) rather than assume it exists.
- Plans root discovery: locate `.agents/plans/` (and `.agents/prompts/`) from the invocation cwd /
  repo root, tolerating a repo that uses `done/`. Stdlib-only, zero deps (D46), consistent with the
  D48/D50 normalizer's scope model.
- Backward-compat: reuse the same legacy mapping the drift-guard test encodes (D52): case-normalize,
  map `pending`->to-review and `done`->executed; unrecognized values -> a `legacy/unknown` group,
  never an error.
- House rule: no em dashes in authored Markdown.

## Decisions inherited (from the core IPD, resolved 2026-07-11)

- Scope: scan `.agents/plans/*` AND `.agents/prompts/*` by default (consistent with the D50
  normalizer scope). `STATUS.md` is written only on `--write-index`, NOT auto-refreshed by
  `aw install` (avoids surprise writes / extra moving parts).
- Reads front-matter `Status:` only; renames/moves nothing; stdlib-only, zero deps.
- Legacy/unknown free-text status is shown under a `legacy/unknown` group, never errored.
- Prompts may have no readiness status (they get Workflow-history but the enum is optional); the
  board tolerates "no status".

## Proposed changes (ordered, validatable)

1. **Status-parsing helper** (do this first; the board and any future gate share it). A small
   stdlib function - naturally in a new `agent_workflows/plans.py` (keeps `cli.py` thin and gives
   tests a clean import) - that: locates the plans root, scans `.agents/plans/*` and
   `.agents/prompts/*`, reads each file's `- Status:` front-matter, case-normalizes + legacy-maps
   (`pending`->to-review, `done`->executed; unknown -> `legacy/unknown`), and returns records of
   (path, disposition-dir, readiness). Mirror the mapping already in `tests/test_plan_status.py` so
   the two never diverge (single source of truth is the D52 vocabulary; consider having the test
   import from `plans.py` to enforce that).
2. **`aw plans` verb** in `cli.py`: register `sub.add_parser("plans", parents=[common], ...)`, a
   dispatch branch in `main()`, and a `_run_plans(args, term)` handler that calls the helper and
   prints a board grouped by disposition dir then readiness, with per-group counts. Render via
   `term.py` (`heading`, `kv`, `line`; map readiness states to styled labels; honor
   NO_COLOR/isatty/piped -> plain, reusing `should_color`). Add `plans` to the no-arg default hint
   (:620-622). Flags: `--pending` (only pending/), `--status <s>` (filter to one readiness),
   `--write-index`.
3. **`--write-index`**: (re)generate `.agents/plans/STATUS.md` - a plain, committed-friendly grouped
   list mirroring the terminal board, for the no-CLI / GitHub-web case. On-demand only (never
   auto-written by `aw install`, per D52 OQ3). Must be deterministic (stable sort) so re-running
   produces no spurious diff.
4. **Tests** (`tests/test_plans_board.py`): build a temp plans tree with mixed statuses (incl.
   legacy `EXECUTED`/`DONE`, a `draft`, a prompt with no status); assert the board groups by
   disposition + readiness with correct counts; NO_COLOR/piped output contains no ANSI; legacy/unknown
   is grouped not errored; `--write-index` writes a deterministic STATUS.md and re-running is a no-op
   diff; the helper reads front-matter only and renames/moves nothing. Follows the repo's
   "test the mechanical parts" policy.
5. **Docs**: add `aw plans` to the README CLI-verb table and ARCHITECTURE's CLI section, and to
   `aw --help` (the parser help string). DECISIONS: a short entry (next Dnn) recording the board +
   `--write-index` + the metadata-is-truth stance, cross-referencing D52.

## Deferred / out of scope

- Auto-refreshing `STATUS.md` on `aw install` (rejected in the core IPD's OQ3 - extra moving parts).
- Any hard gating on status (advisory-first, per the core IPD OQ2).
- The vocabulary/provenance/commit-discipline itself (that is the core IPD).

## Open questions

1. **STATUS.md format (v1 lean: grouped list).** A plain grouped list mirroring the terminal board
   (disposition -> readiness -> files), not a table - simpler, cleaner git diffs. Confirm at review.
2. **Board sort/order + filter flags (v1 lean).** Group order = lifecycle order (pending groups first
   by readiness draft->approved, then executed/superseded/not-executed/reusable, then
   legacy/unknown); within a group sort by filename (date-ordered by the D48/D50 convention). Flags:
   `--pending`, `--status <s>`, `--write-index`. Confirm the flag set is enough for v1.
3. **Display-only vs. suggest-next-transition (v1 lean: display-only).** v1 just shows state +
   counts. A "3 approved plans ready to execute" hint is a nice follow-on but risks implying action;
   keep it advisory-display for v1 (consistent with D52's advisory-first stance). Confirm.
4. **Helper location + test coupling.** Put the parser in `agent_workflows/plans.py` and have
   `tests/test_plan_status.py` import its legacy-mapping so the drift-guard and the board share ONE
   source of truth (avoids the two-mappings-diverge risk). Confirm this refactor is in scope for this
   IPD (lean: yes, it is cheap and removes duplication).

## Approval and execution gate

This IPD is `to-review` (dependency D52 satisfied; approach committed). Next: `/plan-review` (with the
D52 two-commit contract), resolve the OQs, human-approve (`Status: approved`), then execute changes
1-5, validate (full suite green), commit per batch and NEVER push, set `Status: executed`, and
`git mv` to `.agents/plans/executed/`. Not auto-executed.

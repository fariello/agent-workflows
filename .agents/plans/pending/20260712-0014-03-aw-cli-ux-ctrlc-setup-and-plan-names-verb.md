# IPD: aw CLI UX - graceful CTRL-C, better setup input loop, and an aw verb for plan-name normalization

- Date: 2026-07-12
- Concern: CLI ergonomics + discoverability. Three `aw` UX problems: (1) CTRL-C during interactive
  prompts dumps a raw Python traceback; (2) the `aw setup` roots loop does no path validation, no
  `~`-relative storage, and is plain/uncolored; (3) the plan-filename normalizer is buried at
  `.agents/workflows/setup-repo/tools/normalize_plan_names.py` with no ergonomic entry point, so
  users cannot discover or run it (unlike `aw plans`). Plus a small docs clarification (ITEM-05):
  `aw install` IS the idempotent updater; there is no separate update command.
- Scope: `agent_workflows/cli.py` (signal handling wrapper + setup loop), possibly `engine.py`
  input sites, a new `aw plan-names` (working name) verb delegating to the existing normalizer, and
  docs/help. No new config format (keep `config.json`); no `/setup-repo` rename.
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-04, ITEM-05, ITEM-06, ITEM-07). Awaiting flesh-out.

## Goal / decisions taken (maintainer, 2026-07-12)

1. **Graceful CTRL-C / EOF (ITEM-06).** No raw traceback on `KeyboardInterrupt` (or EOF) at ANY
   interactive prompt. Verified `input()` sites: `cli.py:186` (_confirm), `cli.py:541` (setup roots),
   `engine.py:746` (overwrite?), `engine.py:947` (delete?), `engine.py:1338` (select option),
   `engine.py:1684` (commit?). Catch KeyboardInterrupt centrally (e.g. wrap `main()`), print a clean
   "Cancelled." to stderr, and exit with the conventional 130; also handle EOF consistently. Nothing
   half-written / no partial config on abort.
2. **Better `aw setup` roots loop (ITEM-04).** Enhance the EXISTING loop in place (no new `aw config`
   verb, keep `config.json`): validate each entered path (exists + is a directory) with a clear
   message and re-prompt on error; store `~`-relative for portability; show the current roots; use
   `term.py` color/headings for a prettier, self-documenting prompt. Inspiration:
   `a local checkout dir/linux-config/bin/gits.py` (`run_config_wizard` / `run_first_run_wizard`).
3. **Expose the plan-name normalizer as an aw verb (ITEM-07).** Add `aw plan-names` (working name;
   confirm at review) that runs `normalize_plan_names.py` against the repo, CHECK by default and
   `--apply` to rename (mirroring the script's existing flags: `--area`/`--all`/`--exclude`/
   `--format`/`--assume-dates`/...). Thin verb -> shared logic (do NOT duplicate the algorithm; import
   or invoke the existing module). Add it to `aw --help` and the no-arg hint so it is discoverable.
4. **Docs clarification (ITEM-05).** Document that `aw install <dir>` is the idempotent updater
   (re-run to update; no-clobber), so users looking for "update" find the answer. Keep `/setup-repo`
   named as-is (renaming to `/setup-project` churns installs/shims/docs/tests for little gain).

## Open questions (to resolve during flesh-out / review)

1. Final verb name: `aw plan-names` vs `aw normalize-plans` vs `aw names`. (Lean: `aw plan-names`.)
2. Does the normalizer live where it is (setup-repo/tools) and get imported by the CLI, or move into
   the `agent_workflows` package? (Lean: keep in place, import via a small adapter, to avoid moving a
   file many docs reference; confirm the import path works when installed as a wheel.)
3. CTRL-C wrapper scope: just the CLI `main()`, or also the standalone tools (normalize_plan_names.py,
   scan_secrets.py) run directly? (Lean: CLI main now; tools can follow.)
4. Setup path validation strictness: reject non-existent dirs outright, or warn-and-store (a root may
   be created later)? (Lean: warn but allow, since search_roots are scanned lazily.)

## Approval and execution gate

Proposal (`draft`). Flesh out -> `to-review` -> `/plan-review` -> resolve OQs -> human approve ->
execute -> validate (suite green) -> commit (never push) -> `git mv` to executed/. Not auto-executed.

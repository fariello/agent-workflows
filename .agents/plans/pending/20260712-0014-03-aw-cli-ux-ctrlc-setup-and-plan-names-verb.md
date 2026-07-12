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
- Status: approved
- Approval: approved by maintainer 2026-07-12 (reviewed; OQ1-5 leans confirmed - verb `aw plan-names`;
  normalizer stays in place + loaded via _compat; CTRL-C guard returns 130 in cli.main + engine.main;
  setup warns-but-allows non-existent dirs; exit 130 for SIGINT). Ready to execute changes 1-5.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-04, ITEM-05, ITEM-06, ITEM-07). Awaiting flesh-out.
- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): fleshed out with verified anchors
  (input() sites; normalizer's main(argv)/flags; _compat.packaged_source_root() for locating the
  bundled script in a wheel). OQs leaned. Approach committed; promoted to to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Re-opened evidence: all 3 console scripts -> `agent_workflows.cli:main` (pyproject:36-38); `main()`
  RETURNS an int and `__main__` does `raise SystemExit(main())` (cli.py:726); tests call
  `cli.main(argv)` IN-PROCESS and read the return code (test_cli.py:30); `engine.main()` also returns
  int (engine.py:2363). Findings: PC-1 the CTRL-C guard MUST `return 130` from `main()`, NOT
  `sys.exit()` inside it (else it breaks in-process tests / raises SystemExit mid-call); PC-2 apply the
  same return-code guard shape to `engine.main()`; PC-3 the CTRL-C test patches `input` to raise
  KeyboardInterrupt and asserts `main()` returns 130 with no traceback escaping. Status -> reviewed.

## Project conventions discovered (Step 0, VERIFIED against source)

- `input()` sites needing graceful CTRL-C/EOF: `cli.py:186` (_confirm y/N), `cli.py:541` (setup
  roots loop; already catches EOFError but NOT KeyboardInterrupt -> the reported traceback),
  `engine.py:746` (overwrite?), `engine.py:947` (delete?), `engine.py:1338` (select option 1-3),
  `engine.py:1684` (commit? Y/n). Central fix: wrap `cli.main()` to catch KeyboardInterrupt (+ handle
  EOF consistently), print a clean "Cancelled." to stderr, exit 130. `engine.main()` (used by the
  deprecated installer shim) should get the same guard.
- Normalizer entry: `normalize_plan_names.py` exposes `main(argv=None) -> int` (:505) taking `--repo`
  plus `--format/--area/--all/--exclude/--no-default-excludes/--include-nested/--rename-non-numeric/
  --assume-dates/--apply/--version`; check-by-default, `--apply` performs staged git-mv, returns
  1 when work remains / a decision is needed, 0 when conformant. The `aw` verb builds an argv and
  calls this `main` - NO algorithm duplication.
- Locating the bundled script in an installed wheel: `_compat.packaged_source_root()` returns the
  bundled `.agents/workflows/` dir (wheel `_data/...` or None for a source checkout); the script is
  at `<that or repo-root>/setup-repo/tools/normalize_plan_names.py`. Load it via
  `importlib.util.spec_from_file_location` (it is a standalone script, not an importable package
  module) and call `.main(argv)`. Handle the source-checkout case (root at repo, not `_data`).
- Config: keep `config.json` (D46); no new `aw config` verb; no `/setup-repo` rename. Verbs default
  the root to `Path.cwd()` with an optional path (cli.py pattern). `term.py` provides color/heading/kv
  honoring NO_COLOR/isatty.
- House rule: no em dashes in authored Markdown.

## Decisions taken (maintainer, 2026-07-12)

1. Graceful CTRL-C/EOF (ITEM-06). 2. Improve the EXISTING `aw setup` loop in place, no new `aw config`
verb, keep `config.json` (ITEM-04). 3. Expose the normalizer as an `aw` verb (ITEM-07). 4. Document
`aw install` as the updater; keep `/setup-repo` (ITEM-05).

## Proposed changes (ordered, validatable)

1. **Central CTRL-C / EOF guard (PC-1/PC-2).** Wrap the BODY of `cli.main()` in a
   `try/except KeyboardInterrupt` that prints a clean `Cancelled.` to stderr and RETURNS 130 (the
   conventional SIGINT code) - it MUST return, NOT call `sys.exit()` inside `main()` (tests call
   `cli.main(argv)` in-process and read the int; `__main__` already does `raise SystemExit(main())`,
   so a returned 130 becomes the process exit code). Do the same in `engine.main()` (used by the
   deprecated installer shim; also returns an int). No traceback escapes. Ensure no partial state on
   abort (setup writes config only after the loop completes). Keep the existing per-prompt `EOFError`
   handling; treat EOF consistently as "cancel/finish", not a crash.
2. **Better `aw setup` roots loop (in place).** In `_run_setup`: for each entered root, expand `~`,
   validate it exists and is a directory; on failure print a clear `term.status("warn", ...)` and
   re-prompt (do not abort the loop); store the accepted path `~`-relative when under `$HOME`
   (portability). Show current roots with `term.kv`; use `term.heading`/color for a prettier,
   self-documenting prompt. Inspired by `gits.py` `run_first_run_wizard`/`run_config_wizard`
   (validation + `~`-relative + re-prompt), without adopting its file format or adding a verb.
3. **`aw plan-names` verb (ITEM-07).** Register `sub.add_parser("plan-names", ...)` with an optional
   `[dir]` (default cwd) and pass-through flags mirroring the script (`--apply`, `--area`, `--all`,
   `--exclude`, `--format`, `--include-nested`, `--rename-non-numeric`, `--assume-dates`,
   `--no-default-excludes`). Dispatch to `_run_plan_names`, which resolves the normalizer script via
   `_compat.packaged_source_root()` (wheel) or the repo root (source checkout), loads it with
   `importlib.util.spec_from_file_location`, builds an argv (`--repo <dir>` + the pass-through flags),
   and returns its `main(argv)` exit code. CHECK by default; `--apply` renames (staged git-mv). Add
   `plan-names` to `aw --help` and the no-arg hint. NO algorithm duplication.
4. **Docs (ITEM-05 + ITEM-07).** Document in README/help that `aw install <dir>` is the idempotent
   updater (re-run to update; no-clobber) - the answer for users seeking "update". Add `aw plan-names`
   to the README CLI section. Keep `/setup-repo` named as-is (note the decision in DECISIONS).
5. **Tests (PC-3).** `tests/test_cli.py`: CTRL-C guard - patch `input` (via the `builtins.input`
   the CLI uses) to raise `KeyboardInterrupt`, run `cli.main(["setup"])` in-process, assert it RETURNS
   130 and no traceback escapes; setup rejects/re-prompts a bad path and stores a good one
   `~`-relative (patch `input` to feed a bad-then-good sequence, assert config contents); `aw
   plan-names` on a temp repo with a mis-named plan reports it (check, exit 1) and renames it with
   `--apply` (exit codes match the underlying script). DECISIONS entry (Dnn).

## Open questions (v1 leans for review)

1. **Verb name: RESOLVED lean `aw plan-names`** (reads well; parallels `aw plans`). Confirm vs
   `normalize-plans`/`names`.
2. **Normalizer location: RESOLVED lean - keep in place** (`setup-repo/tools/`), load via
   `_compat` + `spec_from_file_location`. Avoids moving a file many docs reference; verified the wheel
   bundles it. Confirm the loader works for BOTH wheel (`_data/...`) and source-checkout roots.
3. **CTRL-C wrapper scope: RESOLVED lean - CLI `main()` + `engine.main()` now**; the standalone tools
   (`normalize_plan_names.py`, `scan_secrets.py`) can get the guard as a cheap follow-on. Confirm.
4. **Setup path validation strictness: RESOLVED lean - warn but ALLOW** a non-existent dir (roots are
   scanned lazily; a root may be created later), re-prompting only on clearly bad input. Confirm vs
   hard-reject.
5. Exit-code convention: 130 for SIGINT (confirm; matches shells) vs a plain 1.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened against source:
- PC-1: the CTRL-C guard must RETURN 130 from `main()`, not `sys.exit()` inside it - all 3 console
  scripts call `agent_workflows.cli:main`, `__main__` does `raise SystemExit(main())` (cli.py:726),
  and tests call `cli.main(argv)` in-process reading the int (test_cli.py:30). A mid-`main` sys.exit
  would raise SystemExit into those callers.
- PC-2: `engine.main()` also returns int (engine.py:2363) - same return-code guard shape.
- PC-3: the CTRL-C test patches `input` to raise KeyboardInterrupt and asserts `main()` returns 130.
No blocking findings; OQ1-5 leaned for v1 confirmation. This IPD does not self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ1-5 leans), execute changes 1-5, validate (suite green),
commit (never push), `git mv` to executed/. Not auto-executed. (Original stub flow: draft ->
execute -> validate (suite green) -> commit (never push) -> `git mv` to executed/. Not auto-executed.

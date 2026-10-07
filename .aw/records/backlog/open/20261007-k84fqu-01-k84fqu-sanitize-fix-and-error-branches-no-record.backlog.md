- Id: k84fqu
- Status: open
- Blocks-Release: next
- Set: k84fqu
- Priority: medium
- Work-Kind: bug
- Summary: aw sanitize --agent/--json writes nothing to stdout on the --fix branch and on its exit-2 error branches (not a git repo, OSError)

## Workflow history
- 2026-10-07 created (aw backlog): aw sanitize --agent/--json writes nothing to stdout on the --fix branch and on its exit-2 error branches (not a git repo, OSError)

Filed by /plan-review of plan wyy09f on 2026-10-07 (HEAD 3c97bba81), as the carrier for a defect that plan's context threading does not reach.

MEASURED. `python3 -m agent_workflows sanitize . --fix --dry-run --agent` exits 0 with ZERO bytes on stdout and `No auto-fixable local leaks found.` on stderr. `sanitize <dir-outside-any-git-repo> --agent` exits 2 with ZERO bytes on stdout and `check-local-leaks: not a git repository or git unavailable` on stderr. Both occur with `--agent`, which IS forwarded today, so this is not the dropped-flag defect of `xym8g8`/`wyy09f`: inside `leak_sanitizer.main` the `if args.fix:` branch and the `except subprocess.CalledProcessError` / `except (OSError, zipfile.BadZipFile)` handlers return before `select_output` is ever consulted, so no output mode reaches them.

WHY A BUG. `docs/cli-output-contract.md` Section 11.4 requires a `kind: error` record with `outcome: cannot-run` and `exit: 2` under agent mode, and Section 11.3 requires a mutation (`--fix`) to report `applied`/`changes` (or a preview with `next` for `--dry-run`). A scripted caller using the advertised flag gets an empty string and `json.loads` raises.

FIX SHAPE. Once `wyy09f` threads an `OutputContext` into `leak_sanitizer.main`, resolve the context BEFORE the `--fix` branch and the scan, and route those three exits through `get_renderer(ctx).emit` with a `CommandResult` (changes for the rewritten paths, diagnostics for the unfixable ones; an error result for the exit-2 handlers), leaving the human stderr prose byte-identical. Depends on `wyy09f` executing first.

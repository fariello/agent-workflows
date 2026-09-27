- Id: ddo56m
- Status: done
- Graduated-To: wintty
- Blocks-Release: next
- Set: ddo56m
- Priority: medium
- Work-Kind: bug
- Summary: Windows: stdin redirected from NUL reports isatty() True, so human-only gates and prompts treat a non-interactive run as interactive

## Workflow history
- 2026-09-27 set (aw backlog): closed by aw oc run: IPD k4vi7z executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260926-wintty-01-k4vi7z-treat-a-windows-nul-stdin-as-non-interactive-at-the-human-at.ipd.md); evidence .aw/records/plans/executed/20260926-wintty-01-k4vi7z-treat-a-windows-nul-stdin-as-non-interactive-at-the-human-at.ipd.md
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set wintty (commit 2c7068ca).
- 2026-09-25 created (aw backlog): Windows: stdin redirected from NUL reports isatty() True, so human-only gates and prompts treat a non-interactive run as interactive

Found while fixing Windows CI (tests/__init__.py now wraps stdin on win32 so the suite is not fooled). On Windows, NUL is a character device, so sys.stdin.isatty() returns True when stdin is redirected from NUL. git_commit_helper._is_interactive, specs.run_set (which grants --by-human attestation) and status_set trust sys.stdin.isatty() alone. Effect: a Windows invocation run with '< NUL' may treat the human-only approval gate as satisfied, or print an interactive prompt into --json output. engine.is_interactive_session already checks GetConsoleMode and could be reused.

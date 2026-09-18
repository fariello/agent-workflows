- Id: xzdudk
- Status: open
- Blocks-Release: next
- Set: xzdudk
- Priority: medium
- Work-Kind: bug
- Summary: release_readiness gate launches a nested aw with no stdin= and no tooling pin, invisible to both TTY guards

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): release_readiness gate launches a nested aw with no stdin= and no tooling pin, invisible to both TTY guards

MEASURED 2026-09-17 during rununify 05 (ct4w0a) E-03, at HEAD 1171f7b2, BEFORE any change in that plan, so this is PRE-EXISTING and not introduced by it.

`agent_workflows/release_readiness.py` has two nested-`aw` launches, `gate_leak_scan` (:158) and `gate_ipd_lint` (:179). Each builds a literal `[sys.executable, '-m', 'agent_workflows', ...]` argv and calls `subprocess.run` with NEITHER `stdin=subprocess.DEVNULL` NOR the `af7i6p` tooling pin (`env=pinned_child_env()` / `pinned_module_argv`).

WHY NO GUARD SAW THEM, which is the more interesting half. The ttywedge guard (g40w37, tests/test_nested_tty_noninteractive.py) identified launchers by the first argument's NAME being `argv`/`cmd` and only scanned the two driver files; these pass an inline list literal in a third module, so they matched neither condition. The af7i6p pin guard (tests/test_lane_tool_identity.py) only classified sites inside the two drivers as well.

WHAT IS AND IS NOT AT RISK. Both pass `--agent`, which makes the child non-interactive on its own merits, so the 1h49m wedge shape is not reachable through them today; the exposure is that the protection is incidental rather than structural, and that a `-m agent_workflows` launch from a lane cwd resolves the package from the cwd (the defect af7i6p exists to close). These are release-review gates run by a human, not runner launchers.

NOW DETECTED, NOT FIXED. ct4w0a added a package-wide semantic scan (`OwnerSetCompletenessTests`) that finds a nested-`aw` launch by MEANING rather than by argument name, and these two are recorded in its `EXEMPT_OUTSIDE_OWNER_SET` allowlist with this reasoning, so a THIRD such site now fails the suite. They were not fixed because `agent_workflows/release_readiness.py` is outside that plan's declared Scope-Paths.

THE FIX: add `stdin=subprocess.DEVNULL` and route both through `pinned_module_argv`/`pinned_child_env`, then remove the allowlist entry in tests/test_nested_tty_noninteractive.py.

- Id: z63xoh
- Status: open
- Blocks-Release: next
- Set: z63xoh
- Priority: medium
- Work-Kind: bug
- Summary: runs show exits 2 on ledger corruption where every other site exits 5 (EXIT_CORRUPTED_LEDGER)

## Workflow history
- 2026-09-18 created (aw backlog): runs show exits 2 on ledger corruption where every other site exits 5 (EXIT_CORRUPTED_LEDGER)

Found while consolidating tests (test_run_recovery_cli.py).

WHAT: `aw runs show` on a corrupted ledger returns exit code 2. Four other
sites that handle the same `store.LedgerCorruption` condition return
`EXIT_CORRUPTED_LEDGER` (5): run_cli.py:708, :850, :878, :971.

WHERE: agent_workflows/run_cli.py:295-308 hardcodes `"exit_code": 2` in the
machine payload and `return 2`, instead of using the module's own
`EXIT_CORRUPTED_LEDGER` constant defined at run_cli.py:55.

WHY IT IS USER-PERCEPTIBLE: exit codes are the machine contract. A caller
that branches on 5 to detect a corrupt ledger sees 2 from `show` and cannot
distinguish it from an ordinary invalid invocation, which is what 2 means
everywhere else in this CLI. So a wrapper cannot reliably tell 'your ledger is
damaged, recover it' from 'you typed the command wrong'.

CURRENT STATE IN TESTS: the real behavior is now PINNED rather than silently
accepted. tests/test_run_recovery_cli.py documents the asymmetry in the row
rationale, and an accompanying --agent row asserts the payload still carries
`corrupted: true`, so the machine-readable signal is covered whichever exit
code is chosen. Fixing the code therefore requires updating that one row, and
the row says so.

DECISION NEEDED (not assumed here): whether `show` should return 5 like its
siblings, or whether `show` is deliberately lenient because it is a read-only
inspection verb. If the latter, the constant should still be used for the
payload and the divergence documented at the definition site.

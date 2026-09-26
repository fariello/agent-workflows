- Id: mawwlc
- Status: open
- Blocks-Release: next
- Set: gatebypass
- Priority: high
- Work-Kind: bug
- Summary: Positional aw backlog set done closes a release-blocking item with no gate check (the --status spelling refuses correctly)

## Workflow history
- 2026-09-26 created (aw backlog): Positional aw backlog set done closes a release-blocking item with no gate check (the --status spelling refuses correctly)

Found 2026-09-26 during graduation of 30 items and confirmed by the bklgdryrun plan author. Reproduced in a scratch repo: an open item carrying Blocks-Release: next and no handoff/evidence closes with exit 0 via 'aw backlog set done <id6> --yes' (status_set path), while 'aw backlog set --status done <path>' refuses with the three legitimate fixes. So the close-legitimacy rule in AGENTS.md is enforced on one spelling only, and a gated bug can be closed silently. Fix: call check_engine.evaluate_blocking_close on the positional path for backlog done (status_set.apply_status_change or run_set_command), with an outcome test that both spellings refuse the same gated close and accept the same --evidence close.

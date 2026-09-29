- Id: le31pr
- Status: graduated
- Graduated-To: posgate
- Blocks-Release: next
- Set: posgate
- Priority: high
- Work-Kind: bug
- Summary: aw backlog set done <id> (positional) skips the release-gate close predicate

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 2misq5
- 2026-09-26 created (aw backlog): aw backlog set done <id> (positional) skips the release-gate close predicate

The positional spelling aw backlog set done <id> routes to status_set.run_set_command rather than backlog.run_set, and does not run check_engine.evaluate_blocking_close. Measured on a scratch repo with a release-gated item carrying Blocks-Release: next and no carrier: aw backlog set done item01 --yes exits 0 and moves the item to done/, whereas aw backlog set item01 --status done exits 1 with three close fixes. Previously noted as decision D1 of executed plan zhr6mc and not filed.

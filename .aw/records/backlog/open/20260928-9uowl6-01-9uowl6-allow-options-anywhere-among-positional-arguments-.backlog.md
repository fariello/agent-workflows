- Id: 9uowl6
- Status: open
- Blocks-Release: next
- Set: 9uowl6
- Priority: medium
- Work-Kind: bug
- Summary: Allow options anywhere among positional arguments across all aw commands

## Workflow history
- 2026-09-28 created (aw backlog): Allow options anywhere among positional arguments in aw set
- 2026-09-28 amended: Broaden scope to cover all subparsers and subcommands across aw

Across all aw subparsers and subcommands (such as aw set, aw partition, aw specs, etc.), optional flags (such as --dir, -y, -m, -s, -t) placed between or after positional arguments cause standard argparse to halt positional argument consumption and fail with unrecognized arguments. The CLI argument parsing should support options anywhere among positional arguments regardless of ordering across all subcommands.

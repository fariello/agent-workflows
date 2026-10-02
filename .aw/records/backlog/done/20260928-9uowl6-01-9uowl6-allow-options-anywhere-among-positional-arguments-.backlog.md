- Id: 9uowl6
- Status: done
- Graduated-To: optanywhere
- Blocks-Release: next
- Set: 9uowl6
- Priority: medium
- Work-Kind: bug
- Summary: Allow options anywhere among positional arguments across all aw commands

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw oc run: IPD z593o5 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-optanywhere-01-z593o5-accept-options-anywhere-among-positional-arguments-on-every.ipd.md); evidence .aw/records/plans/executed/20260929-optanywhere-01-z593o5-accept-options-anywhere-among-positional-arguments-on-every.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: z593o5
- 2026-09-28 created (aw backlog): Allow options anywhere among positional arguments in aw set
- 2026-09-28 amended: Broaden scope to cover all subparsers and subcommands across aw

Across all aw subparsers and subcommands (such as aw set, aw partition, aw specs, etc.), optional flags (such as --dir, -y, -m, -s, -t) placed between or after positional arguments cause standard argparse to halt positional argument consumption and fail with unrecognized arguments. The CLI argument parsing should support options anywhere among positional arguments regardless of ordering across all subcommands.

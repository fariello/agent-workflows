- Id: 9uowl6
- Status: open
- Blocks-Release: next
- Set: 9uowl6
- Priority: medium
- Work-Kind: bug
- Summary: Allow options anywhere among positional arguments in aw set

## Workflow history
- 2026-09-28 created (aw backlog): Allow options anywhere among positional arguments in aw set

In aw set, optional flags (such as --dir, -y, -m) placed between or after positional arguments cause argparse to halt positional argument consumption and fail with unrecognized arguments. The parser should support options anywhere among positional arguments regardless of ordering.

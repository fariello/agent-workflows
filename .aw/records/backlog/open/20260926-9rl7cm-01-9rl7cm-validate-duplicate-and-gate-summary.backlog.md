- Id: 9rl7cm
- Status: open
- Set: 9rl7cm
- Priority: low
- Work-Kind: chore
- Summary: validate_item: flag duplicate metadata bullets and a Gate-Summary on a non-blocked backlog item

## Workflow history
- 2026-09-26 created (aw backlog): validate_item: flag duplicate metadata bullets and a Gate-Summary on a non-blocked backlog item

Carrier for plan 2yqt0a deferred row 4 (review PR-002/PR-003). validate_item returns [] for a duplicated metadata bullet and for a Gate-Summary on a non-blocked item (2yqt0a F-7, F-8), so neither is caught anywhere. 2yqt0a makes its own renderer never produce them; the validator rules belong here. The live tree carried none of these shapes when filed.

- Id: 0q2x1a
- Status: open
- Set: 0q2x1a
- Work-Kind: bug
- Priority: low
- Summary: aw specs set positional spelling writes history actor 'aw set' while the --status spelling writes 'aw specs'
- Short-Description: aw specs set positional spelling writes history actor 'aw set' while the --status spelling writes 'aw specs'
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-23 created (aw backlog): aw specs set positional spelling writes history actor 'aw set' while the --status spelling writes 'aw specs'

Observed at HEAD c8e713965 (found during IPD wilgfy). On a legacy-format spec, `aw specs set approved <id6> --by-human --message m` appends `- <day> approved (aw set, --by-human): m`, while `aw specs set <id6> --status approved --by-human --message m` appends `- <day> approved (aw specs, --by-human): m`. The same transition records two different actors depending on the CLI spelling, so history readers that key on the actor see an inconsistent tool name. Reproduce on a tmp git repo with a reviewed spec; compare the appended history lines. Expected: one actor label for both spellings.

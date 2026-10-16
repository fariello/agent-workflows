- Id: q3ogs0
- Status: open
- Blocks-Release: next
- Set: q3ogs0
- Priority: medium
- Work-Kind: bug
- Summary: Installer reports AGENTS.md#aw:pointer as manually modified due to stale recorded section hash (recurrence of krwl3t)

## Workflow history
- 2026-10-16 created (aw backlog): Installer reports AGENTS.md#aw:pointer as manually modified due to stale recorded section hash (recurrence of krwl3t)

In this repository aw install . reports AGENTS.md#aw:pointer as manually modified and does not apply the regenerated pointer, although the on-disk section equals engine.agents_pointer_prose('aw') verbatim, because the hash recorded in .aw/system/managed-sections.json matches neither. This is the same symptom closed done in backlog krwl3t (plan b4bvas), recurring after subsequent edits. Worked around in plan er11a0.

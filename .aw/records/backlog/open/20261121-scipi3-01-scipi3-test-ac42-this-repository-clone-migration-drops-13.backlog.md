- Id: scipi3
- Status: open
- Set: scipi3
- Work-Kind: bug
- Priority: medium
- Summary: test_ac42_this_repository_clone_migration drops 130 .aw/records/skills items from aw find
- Short-Description: test_ac42_this_repository_clone_migration drops 130 .aw/records/skills items from aw find
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): test_ac42_this_repository_clone_migration drops 130 .aw/records/skills items from aw find

Observed during aw suite --thorough (epsj2v validation): tests/test_m0001_any_repo.py::test_ac42_this_repository_clone_migration fails at post-migration aw find parity check with 130 dropped items starting with .aw/records/skills/advise-architect/SKILL.md.

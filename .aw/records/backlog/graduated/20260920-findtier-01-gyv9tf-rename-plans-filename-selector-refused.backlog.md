- Id: gyv9tf
- Status: graduated
- Graduated-To: awrenamesel
- Blocks-Release: next
- Set: findtier
- Priority: medium
- Work-Kind: bug
- Summary: aw rename plans refuses a filename selector, so a suggested command built from a filename fails

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260928T235632Z-1358353: 1x4tdo, 3qxuw1, 87m438, 95jk4s, eby93o
- 2026-09-20 created (aw backlog): Found while executing findtier Order 02 (3i6rso). aw rename specs <filename> resolves, but aw rename plans <filename> refuses with "no plan has Id '<filename>'": the plans resolver is id-directed while the generic one accepts a path/stem. Measured at HEAD 7f06bb37: 'aw rename plans 20260808-0004-06-migrate-existing-plans.ipd.md --to-id6' -> error; 'aw rename plans 7qx7ys --to-id6' -> resolves. Also 'aw rename roadmaps effzzi' reports 'no roadmaps artifact matched' while 'aw rename research effzzi' resolves, so the roadmaps type has no rename route of its own. 3i6rso works around both by always suggesting the declared id6 and by mapping roadmaps->research in _IDENT_RENAME_TYPE (agent_workflows/check_engine.py:_identity_rename_hint). The underlying inconsistency between selector kinds across types remains.

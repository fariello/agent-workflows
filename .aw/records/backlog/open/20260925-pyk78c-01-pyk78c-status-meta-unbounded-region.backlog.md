- Id: pyk78c
- Status: open
- Blocks-Release: next
- Set: pyk78c
- Priority: low
- Work-Kind: bug
- Summary: check_engine._status_meta reads the first - Status: anywhere in the file instead of within the metadata region, so a plan with no front-matter Status that quotes an executed line reads as executed

## Workflow history
- 2026-09-25 created (aw backlog): Found at review of plan kecxnb. kecxnb's F-2 correctly says the sibling does not share the fence defect FOR A PLAN WITH FRONT-MATTER STATUS; this is the remaining half. Measured: _status_meta on a plan with no front-matter Status that quotes '- Status: executed' in a fence returns 'executed'. Consumed by check.status-untooled. After kecxnb lands, the HOOK is strictly stricter than this sibling; bounding _status_meta to selectors.metadata_region would align them.

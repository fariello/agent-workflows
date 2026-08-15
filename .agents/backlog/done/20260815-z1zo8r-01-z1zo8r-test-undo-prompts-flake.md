- Id: z1zo8r
- Status: done
- Set: z1zo8r
- Priority: low
- Kind: bug
- Summary: Test-isolation flake: test_undo_removes_prompts_scaffold fails intermittently in full-run interleavings; make it hermetic

## Workflow history
- 2026-08-15 created (aw backlog): Test-isolation flake: test_undo_removes_prompts_scaffold fails intermittently in full-run interleavings; make it hermetic
- 2026-08-15 set (aw backlog): Fixed: root cause was run_rollback selecting dirs[-1] instead of the latest backup carrying a .created-files.json; a boundary-crossing multi-timestamp install could land the record in an earlier dir. run_rollback now prefers the latest dir with a record. Added a deterministic regression test (mutation-probed RED on the old logic).

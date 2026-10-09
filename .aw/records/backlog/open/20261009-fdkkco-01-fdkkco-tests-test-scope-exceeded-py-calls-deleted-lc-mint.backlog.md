- Id: fdkkco
- Status: open
- Blocks-Release: next
- Set: fdkkco
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_scope_exceeded.py calls deleted LC.mint_driver_attestation

## Workflow history
- 2026-10-09 note (aw backlog): Fixed by commit 64b8c94f3 (removed the deleted mint_driver_attestation setup; tests/test_scope_exceeded.py 7 passed; bare suite 7195 passed). Left open because the release-gate close needs a record artifact as evidence; close with the maintainer's chosen evidence or --blocks-release -.
- 2026-10-09 created (aw backlog): tests/test_scope_exceeded.py calls deleted LC.mint_driver_attestation

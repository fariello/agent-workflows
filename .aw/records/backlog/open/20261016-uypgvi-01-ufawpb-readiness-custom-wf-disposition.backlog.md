- Id: ufawpb
- Status: open
- Blocks-Release: next
- Set: uypgvi
- Priority: medium
- Work-Kind: bug
- Summary: release_readiness: workflow_disposition fails NO-GO in a managed repo whose index.md carries its own workflow rows (no reviewed family assignment)

## Workflow history
- 2026-10-16 created (aw backlog): release_readiness: workflow_disposition fails NO-GO in a managed repo whose index.md carries its own workflow rows (no reviewed family assignment)

Measured 2026-10-16 at cb349046d by plan 4bw2u5 (OQ-01): on a fresh managed install, adding one manifest row (copy of whatnext as mycustomwf) makes gate_workflow_disposition FAIL with "manifest command 'mycustomwf' has no reviewed family assignment (silent omission)", because migration_inventory._COMMAND_FAMILY is this toolkit's own catalog. Once kmmoca runs aw releases readiness in every repo, this is a false NO-GO a managed-repo maintainer cannot clear. Not an absent input, so outside the v1re2z not-applicable ruling. Maintainer to decide whether managed-repo custom workflows are supported and how they are dispositioned.

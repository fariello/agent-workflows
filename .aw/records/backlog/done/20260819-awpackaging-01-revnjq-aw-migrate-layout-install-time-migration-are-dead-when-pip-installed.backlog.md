- Id: revnjq
- Status: done
- Set: awpackaging
- Priority: high
- Work-Kind: bug
- Summary: aw migrate-layout + install-time migration are dead when pip-installed: agent_workflows.layout_migration module-level imports the unshipped tools.awphysical -> ModuleNotFoundError. Ship tools.awphysical in the package or inline the inventory it needs.

## Workflow history
- 2026-08-19 set (aw backlog): Implemented by IPD m2h1z4: moved aw_layout_inventory to agent_workflows/layout_inventory.py, repointed shipped callers and tests, left back-compat shim.

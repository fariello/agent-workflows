- Id: 232wcg
- Status: open
- Blocks-Release: next
- Set: tieclass
- Priority: high
- Work-Kind: bug
- Summary: runner_shared.assert_child_tool_identity raises runner_shared.ToolIdentityError, a DIFFERENT class from the one both hosts catch, so a run-fatal tool-identity mismatch is silently downgraded to an item-local failure

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing runnerlayer 02 (1f7xno). ToolIdentityError is defined TWICE: oc_runipd.py:686 and runner_shared.py:21159, and oc.ToolIdentityError is runner_shared.ToolIdentityError -> False. runner_shared.assert_child_tool_identity (:21194) raises the runner_shared class; oc_runipd.py:6877 and agy_runipd.py:3376 both catch the oc class (agy imports it from oc). Measured live: raising runner_shared.ToolIdentityError is NOT caught by except oc_runipd.ToolIdentityError, only by the broader except DriverError. Per the in-tree notes at oc_runipd.py:6879 and agy_runipd.py:3378 that broader handler is ITEM-LOCAL, so the ABORT-RUN escalation spec 25kzda 1.4/A1 reserves for the identity class is lost and the run continues under tooling the runner is not. This is exactly the two-distinct-classes defect 818uru fixed for DriverError, reintroduced one subclass down. Note execute_item_core rebinds assert_child_tool_identity off driver_module, so today's live path raises oc's class; the shared copy is reachable whenever driver_module lacks the attribute.

- Id: 87aj3i
- Status: done
- Blocks-Release: next
- Set: 87aj3i
- Priority: medium
- Work-Kind: bug
- Summary: AgyCostAttributionTests hardcode 56 oc_runipd imports broken by 1f7xno import re-homing

## Workflow history
- 2026-09-24 done (aw set): Fixed on main in c2a7b890..f2651b4d: the 56-name count in both tests is replaced by the named set runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD, plus a third test in tests/test_runner_shared.py that measures the constant against the source and pins the reverse direction empty. Full suite green on main: 9131 passed, 3 skipped, 2 xfailed.
- 2026-09-23 created (aw backlog): AgyCostAttributionTests hardcode 56 oc_runipd imports broken by 1f7xno import re-homing

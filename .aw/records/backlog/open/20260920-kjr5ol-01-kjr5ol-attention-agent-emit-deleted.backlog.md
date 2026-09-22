- Id: kjr5ol
- Status: open
- Blocks-Release: next
- Set: kjr5ol
- Priority: high
- Work-Kind: bug
- Summary: aw attention --agent emitted no record outside a project: a perf commit deleted the emit call and nothing failed

## Workflow history
- 2026-09-20 created (aw backlog): aw attention --agent emitted no record outside a project: a perf commit deleted the emit call and nothing failed

FIXED BY IPD quqyc4 (this item exists as the durable carrier for the defect and for the CLASS it exposes, not as outstanding work on the fix itself).

MEASURED while executing quqyc4 at HEAD 283b3c92. In a bare `git init` directory with no AW layout, `aw attention --agent` exited 3 having written HUMAN prose to stderr and NO `aw.agent/v1` record to stdout at all. A machine consumer saw empty stdout.

CAUSE: commit 4cfa2283 ('perf(attention): optimize attention and set command performance') deleted the line `return get_renderer(ctx).emit(res, ctx)` from the no-project branch of `attention.run` (visible in `git log -L` on that branch). The branch kept BUILDING a `CommandResult` and then fell through to the human `sys.stderr.write`, so the record was constructed and discarded.

WHY IT WENT UNNOTICED, which is the part worth acting on: the branch had NO test asserting the record. The plan quqyc4 was authored against a measured `ValueError` traceback on this same path; by execution time a refactor had replaced the crash with silence, which is a strictly worse failure mode because it is invisible. quqyc4 restored the emit and pinned it in tests/test_attention.py::AttentionNoProjectMachinePathTests and tests/test_awretrofit_project_root_climb.py case (e).

RESIDUAL WORK THIS ITEM CARRIES: a swept check that no OTHER `--agent`/`--json` branch builds a CommandResult it never emits. A crude grep at execution time found no second instance in agent_workflows/*.py, but a grep is not a contract; a conformance test walking the machine branches would be.

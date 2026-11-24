- Id: j7knk0
- Status: open
- Set: fastsuite
- Work-Kind: chore
- Priority: medium
- Summary: Convert repetitive CLI matrix tests to run_cli_inproc while keeping real subprocess entrypoint and signal tests
- Short-Description: Convert repetitive CLI matrix tests to run_cli_inproc while keeping real subprocess entrypoint and signal tests

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): Convert repetitive CLI matrix tests to run_cli_inproc while keeping real subprocess entrypoint and signal tests

Target the heaviest multi-invocation CLI matrix test files (e.g. test_oc_runipd, test_check_engine_release_gate, test_writers_create_summary, test_spec_production, test_ipd_lifecycle_cli, test_cli, test_rename_group_machine_output) to run flag/shape/exit-code matrices via tests/conformance_matrix.py::run_cli_inproc (~5-15ms/call vs ~130ms+ subprocess), preserving dedicated real-subprocess tests for entrypoint wiring, pipes, signals, and env isolation. Goal: reduce thorough-suite CPU time on 6 workers without reducing test count or rigor.

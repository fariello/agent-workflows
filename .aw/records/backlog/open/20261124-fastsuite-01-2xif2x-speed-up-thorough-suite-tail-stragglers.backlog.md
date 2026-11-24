- Id: 2xif2x
- Status: open
- Set: fastsuite
- Work-Kind: chore
- Priority: medium
- Summary: Reduce top thorough-suite tail-straggler test durations (test_production_fix_it, test_attributable_typecheck, conformance roots)
- Short-Description: Reduce top thorough-suite tail-straggler test durations (test_production_fix_it, test_attributable_typecheck, conformance roots)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): Reduce top thorough-suite tail-straggler test durations (test_production_fix_it, test_attributable_typecheck, conformance roots)

Profile and optimize the top remaining >2s thorough-suite tail tests (test_production_fix_it.py at ~123 CPU-s, test_attributable_typecheck.py at ~30 CPU-s, and test_family_root_agent_conformance[runs] at ~7-11s) so pytest-xdist worksteal does not stall on long tail items at 6 workers.

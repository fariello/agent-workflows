- Id: xoetwv
- Status: open
- Set: specaudit
- Priority: low
- Work-Kind: followup
- Summary: Restore tests for spec r07vma AC-2 refusal reasons and fix AC-9's deleted test citation

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Commit 19313eed7 deleted tests/test_orchestrator_row_grammar.py and tests/test_orchestrator_probe.py. At HEAD 5db4791c1 the three AC-2 refusal reasons (child-id6-is-not-a-row, status-is-outside, missing-the-depends-on-edge) behave correctly when probed, but no test asserts them. AC-9 requires tests/test_orchestrator_probe.py to pass unedited; that file no longer exists. Restore behavioral tests for AC-2 and amend AC-9 to name current probe coverage (test_orchestrator_shape_gate.py:488). Then r07vma can move to implemented.

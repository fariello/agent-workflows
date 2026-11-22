- Id: 07w6g0
- Status: open
- Set: 07w6g0
- Work-Kind: bug
- Priority: medium
- Summary: test_plan_transition_gate passes 5-char id6 p0000 to RecordBuilder-backed create_plan
- Short-Description: test_plan_transition_gate passes 5-char id6 p0000 to RecordBuilder-backed create_plan
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): test_plan_transition_gate passes 5-char id6 p0000 to RecordBuilder-backed create_plan

Observed during aw suite --thorough (epsj2v validation on HEAD 2854f236e): tests/test_plan_transition_gate.py::TestPlanTransitionGate::test_case_a_illegal_nonterminal_backwards_edges_refuse_and_preserve_file calls self.create_plan with 5-char id6 p0000, raising ValueError from RecordBuilder/validate_id6 after tests/test_status_set.py::create_plan moved onto RecordBuilder in commit 96a280911.

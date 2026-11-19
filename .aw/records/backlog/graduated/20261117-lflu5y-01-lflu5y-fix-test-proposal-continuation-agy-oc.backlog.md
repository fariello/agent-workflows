- Id: lflu5y
- Status: graduated
- Graduated-To: lflu5y
- Set: lflu5y
- Work-Kind: bug
- Priority: medium
- Summary: Fix pre-existing test_proposal_continuation_agy and test_proposal_continuation_oc failures in tests/test_fixfirst_end_to_end.py
- Short-Description: Fix pre-existing test_proposal_continuation_agy and test_proposal_continuation_oc failures in tests/test_fixfirst_end_to_end.py
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 graduated (aw backlog): graduated by run run-20261119T154257Z-4175363: k1qi85
- 2026-11-17 created (aw backlog): Fix pre-existing test_proposal_continuation_agy and test_proposal_continuation_oc failures in tests/test_fixfirst_end_to_end.py

Pre-existing non-core test failures observed identically on unmodified main (starting_head 9a89a54bc) and during xexn45 make test-all: tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_proposal_continuation_agy and test_proposal_continuation_oc exit 1 instead of 3 (Run exit code must be 3, got 1). Both drivers report item 01 (prp1agy/prp1oc, whose 7-char fixture id causes dependency edge executed:prp1agy to fail as an unparseable dependency token on item 02 prp2agy) as executed despite fake_turn writing a failed-safely outcome carrying a tool-defect proposal.

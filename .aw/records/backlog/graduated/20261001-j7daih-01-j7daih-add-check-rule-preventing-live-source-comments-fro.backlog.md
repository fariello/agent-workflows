- Id: j7daih
- Status: graduated
- Graduated-To: j7daih
- Set: j7daih
- Priority: low
- Work-Kind: feature
- Summary: Add check rule preventing live source comments from citing nonexistent test files

## Workflow history
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005641Z-2321995: ml7b9e
- 2026-10-01 created (aw backlog): Add check rule preventing live source comments from citing nonexistent test files

As documented in plan oyh28b Deferred section, over 60 test citations in agent_workflows/ dangle. Sibling plan 1jg2m2 added test_docs_test_citations.py to prevent dangling citations in docs. A corresponding check rule or linter check for agent_workflows/ source comments should be designed and added once the baseline cleanup is complete.

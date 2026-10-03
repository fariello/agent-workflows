- Id: j7daih
- Status: open
- Set: j7daih
- Priority: low
- Work-Kind: feature
- Summary: Add check rule preventing live source comments from citing nonexistent test files

## Workflow history
- 2026-10-01 created (aw backlog): Add check rule preventing live source comments from citing nonexistent test files

As documented in plan oyh28b Deferred section, over 60 test citations in agent_workflows/ dangle. Sibling plan 1jg2m2 added test_docs_test_citations.py to prevent dangling citations in docs. A corresponding check rule or linter check for agent_workflows/ source comments should be designed and added once the baseline cleanup is complete.

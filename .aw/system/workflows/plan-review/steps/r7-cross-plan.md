# Check R7: Cross-Plan Consistency

Check consistency across related plans in the same Set:

- For a child plan in a Set: verify alignment and consistency with sibling child plans and with the Set's Order 00 orchestrator. Verify shared assumptions, interface contracts, ordering dependencies (`- Item-Dependencies:`), and scope partitions.
- For an Order 00 orchestrator: check consistency across the entire Set. Verify that every child plan's deliverables, dependencies, and validation criteria roll up coherently into the orchestrator's checklist and coverage.

Record notes in the review record's `### Step R7` subsection starting with `- Checked: <what was examined>`.
Record findings per `_findings.md` in the current round's single `### Findings` table.

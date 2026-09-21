- Id: rrvrwv
- Status: open
- Blocks-Release: next
- Set: ipdsetback
- Priority: high
- Work-Kind: bug
- Summary: aw ipd set performs a backwards executed -> reviewed transition that validate_transition refuses

## Workflow history
- 2026-09-21 created (aw backlog): aw ipd set performs a backwards executed -> reviewed transition that validate_transition refuses

MEASURED 2026-09-21 while executing plan 76w6mq, reproduced in a clean throwaway git repo with a single plan at '- Status: executed'.

REPRO: 'aw ipd set reviewed <id6>' on a plan in .aw/records/plans/executed/ SUCCEEDS: it rewrites '- Status: executed' to '- Status: reviewed', appends a 'reviewed (aw set)' workflow-history line, git-mv's the file from executed/ to pending/, and stages the deletion. Exit code 0. No confirmation prompt and no dry-run gate.

WHY IT IS A DEFECT: agent_workflows/ipd_lifecycle.validate_transition already encodes the correct answer and REFUSES this exact move. Measured directly: validate_transition('executed','reviewed') returns TransitionCheck(ok=False, reason="missing predecessor: backwards transition 'executed' -> 'reviewed'"), and _PLAN_STATUS_ORDER is ('draft','to-review','reviewed','approved','executed') with _TERMINAL_STATUSES == frozenset({'executed'}). So the predicate exists, is correct, and the 'aw ipd set' path does not consult it for the backwards case.

IMPACT: a terminal plan can be silently resurrected out of executed/ by a single typo-level command, which falsifies the repository's own lifecycle record (the directory carries disposition, and executed/ means the work was done and validated). It also stages a deletion of a committed record, so an unwary follow-up commit would drop the executed artifact from history. An agent running unattended cannot rely on the setter to fail closed on an illegal transition.

EXPECTED: 'aw ipd set' routes the backwards/terminal-regression case through validate_transition (or the same shared predicate) and REFUSES with its reason, non-zero, writing nothing, consistent with how the tooling refuses other illegal transitions.

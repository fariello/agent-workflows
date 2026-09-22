- Id: uj5g58
- Status: open
- Blocks-Release: next
- Set: uj5g58
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog new has no near-duplicate guard: 18 items independently filed the same turn_bounds ambient-env defect

## Workflow history
- 2026-09-22 created (aw backlog): Filed from lane 8b9ufm (plan roleadv-01) after the defect-report step found the finding already present 18 times.

THE DEFECT, MEASURED. Every managed lane that runs the bare suite hits the same environmental failure (tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reds because the lane's own environment exports OPENCODE_CONFIG_CONTENT, which the spawned child inherits). Each lane's defect-report step then dutifully files it. Measured 2026-09-22 from lane 8b9ufm: 'grep -rln OPENCODE_CONFIG_CONTENT .aw/records/backlog/' returns 18 FILES, and 'aw find backlog' shows at least 4vn040, rfu7mk, to77re, ph0wlt, cfgj8s, wnabns, wx72g3, 8dp3zp, 06ngnx, zgndje all open and all describing the same single defect under different id6s.

WHY THIS IS A BUG AND NOT NOISE. The defect-report contract in the runner prompt instructs EVERY turn to file a backlog item for each finding, and it is right to: reporting outranks filing. But 'aw backlog new' accepts any summary unconditionally, so a finding that many independent lanes legitimately observe becomes N items instead of 1. The cost is user-perceptible in the surface a human reads: 'aw attention' and 'aw find backlog' present 18 rows for one problem, which inflates the apparent open-defect count and buries unrelated items. It also wastes every subsequent lane's turn, since each one re-investigates, re-files, and re-explains.

WHAT IS WANTED (a suggestion, not a design ruling). 'aw backlog new' could WARN, not refuse, when a new item's summary or slug is a near-duplicate of a live item's, naming the existing id6 so the agent references it instead. Refusing would be wrong: a genuine second instance must still be fileable, and failing closed on a fuzzy match would push agents to skip filing, which is worse than duplication. A warning plus the existing id6 gives the agent what it needs to reference rather than duplicate.

SCOPE NOTE. This is about the FILING TOOL, not about the turn_bounds test. That underlying test defect is already filed 18 times over and needs no nineteenth; whichever of those items is adopted should close the rest as duplicates.

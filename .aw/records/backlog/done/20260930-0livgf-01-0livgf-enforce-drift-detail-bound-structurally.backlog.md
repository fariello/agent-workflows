- Id: 0livgf
- Status: done
- Set: 0livgf
- Priority: low
- Work-Kind: chore
- Summary: Nothing structurally enforces the Section 8.8 descriptive bound on a composed drift detail; it is only pinned per site by test

## Workflow history
- 2026-10-07 done (aw set): status set to done
- 2026-09-30 created (aw backlog): Nothing structurally enforces the Section 8.8 descriptive bound on a composed drift detail; it is only pinned per site by test

FILED AS THE CARRIER for two deferred rows in plan `mc6r92` (hv8zlg-01), which bounded the STRANDED-LANE detail by shortening one segment plus a test, and deliberately did NOT add structural enforcement.

THE GAP, measured 2026-09-30 in a lane at HEAD `c5a13052`: `agent_workflows.core.Drift` does not validate its own `detail`, and `attention_contract.is_safe_descriptive` is applied to no composed detail anywhere; its callers are only in `specs`, `backlog` and `check_engine`. `attention.stranded_lane_drift` calls `A.escape_detail`, which escapes tab/newline/backslash for the single-line agent record and does NOT bound length, so passing it proves nothing about the bound.

TWO RESIDUES THIS CARRIES, both stated in `mc6r92`'s deferred section:

1. NO PRODUCER-SIDE REFUSAL. Validating `detail` inside `core.Drift` would red 12 live `aw check all` findings at once (see item `7stpjm` for that population), so it is a repository-wide contract change and not a wording fix. Until it exists, a future edit to any detail assembly can re-break the bound and only a per-site test will catch it.

2. THE LANE PREFIX IS NOT BOUNDED BY CONSTRUCTION. `attention.stranded_lane_drift` composes `detail` as `"; ".join(bits)` plus the record's `why` plus `lane_remedy_hint`. Measured over the five live lane records the prefix runs 116 to 147 characters, but it embeds a `run_id` (26 to 28 characters in the live corpus), an `id6`, a `commits_ahead` count, an `integration_signal` and a repository-relative worktree path, each of which can grow. So `mc6r92`'s 108-character budget for the `why` sentence is derived from TODAY'S worst observed prefix and a sufficiently deep worktree path or long signal could still exceed 300. Closing it means budgeting or eliding the prefix's variable segments, which changes what an operator reads on every lane row.

RELATION TO `7stpjm`: that item is the POPULATION (12 over-bound findings on the carrier-obligation rules); this item is the MECHANISM (nothing enforces the bound structurally). Either could be done first, but a structural refusal added before that population is fixed would fail closed on it.

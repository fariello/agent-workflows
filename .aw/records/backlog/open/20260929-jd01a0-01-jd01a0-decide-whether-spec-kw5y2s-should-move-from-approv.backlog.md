- Id: jd01a0
- Status: open
- Set: jd01a0
- Priority: low
- Work-Kind: chore
- Summary: Decide whether spec kw5y2s should move from approved to implemented now its wslayout Set has fully executed

## Workflow history
- 2026-09-29 created (aw backlog): Decide whether spec kw5y2s should move from approved to implemented now its wslayout Set has fully executed

Spec kw5y2s (.aw/records/specs/approved/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md) is still Status: approved, but the evidence that it is IMPLEMENTED is strong, measured at HEAD 6def8fef on 2026-09-29:

1. All six plans of the implementing Set wslayout (Orders 00-05: rh5tt6, wpu5zu, zvk796, rodj06, hauwqh, 30jug9) are under .aw/records/plans/executed/, and the orchestrator rh5tt6 carries - From-Spec: kw5y2s.
2. agent_workflows/layout.py exists (the Section 3/4 canonical layout model) and the aw layout CLI verb resolves (Section 6).
3. The Section 3.2 unified vocabulary shipped: all eleven record classes are in BOTH artifact_types.ARTIFACT_TYPES and record_producers.RecordClass, closed by adf3c03d (Order 02) and 0c7405db (Order 03).
4. Install-time emission is wired: engine.py references system/layout.json and system/layout.schema.json, including the .aw/.gitignore back-fill Section 2.3 requires.

WHY THIS IS A SEPARATE ITEM rather than part of plan xx5b7a: AGENTS.md reserves the implemented status for a human with cited evidence ('an agent ... may NOT set implemented (needs cited evidence)'). Plan xx5b7a corrects the spec's stale factual claims and deliberately leaves - Status: approved untouched, raising this as its OQ-01; this item is that question's durable carrier so it does not vanish when that plan executes.

WHAT TO DO: verify the four points above at the then-current HEAD, then either run aw specs set implemented with the cited evidence, or record why the spec stays approved (for example an unimplemented section this audit missed). Section 3.4's traversal-exclusion widening was deliberately declared OUT of scope by the spec itself, so it is not a blocker.

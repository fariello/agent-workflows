- Id: mbjuv5
- Status: graduated
- Graduated-To: mbjuv5
- Set: mbjuv5
- Priority: medium
- Work-Kind: chore
- Summary: Audit items already closed done through the ungated positional aw backlog set spelling, whose release gate was silently dropped

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: 1hrlp3
- 2026-09-29 created (aw backlog): Audit items already closed done through the ungated positional aw backlog set spelling, whose release gate was silently dropped

Filed while authoring plan 47ttnv (backlog mawwlc), which deferred this row and needs a durable carrier for it.

47ttnv fixes the bypass going forward (the positional 'aw backlog set done <id6>' spelling did not call check_engine.evaluate_blocking_close, so a release-gated item closed at exit 0). The bypass was reachable for as long as the predicate has shipped, so .aw/records/backlog/done/ may contain items that were closed while carrying Blocks-Release and satisfying none of the three legitimacy paths (no executed From-Backlog carrier, no cited evidence, no de-gate).

THIS IS AN AUDIT, NOT A BACKFILL, and the distinction is the whole point. AGENTS.md states the release-gate rule governs LIVE items only and that gating an already-done item 'would assert a history that did not happen', so the deliverable is a REPORT plus a per-item decision, never a bulk rewrite.

Start from check.blocking-item-closed-without-gate, which already reports this shape without mutating anything: run 'aw check release-gates' and inspect done/ items carrying a Blocks-Release line. Measured on the tree at authoring time that rule reported 0 errors across 332 release-gates checked, so the population may well be empty; confirm that rather than assuming it either way, since the rule is STAGED-PATH scoped in the commit-invariants caller and whole-tree scoped in the sweep, and those two scopes see different populations.

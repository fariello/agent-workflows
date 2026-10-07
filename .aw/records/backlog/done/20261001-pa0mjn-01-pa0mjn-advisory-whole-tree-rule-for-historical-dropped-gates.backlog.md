- Id: pa0mjn
- Status: done
- Graduated-To: pa0mjn
- Set: pa0mjn
- Priority: medium
- Work-Kind: chore
- Summary: Decide whether an advisory whole-tree rule should report historical done items whose close dropped a release gate (check.blocking-item-closed-without-gate is staged-scoped in every caller, so 53 such items on disk are invisible to aw check)

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD heh05a executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-pa0mjn-01-heh05a-report-the-grandfathered-release-gate-close-population-throu.ipd.md); evidence .aw/records/plans/executed/20261002-pa0mjn-01-heh05a-report-the-grandfathered-release-gate-close-population-throu.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: heh05a
- 2026-10-01 created (aw backlog): Decide whether an advisory whole-tree rule should report historical done items whose close dropped a release gate (check.blocking-item-closed-without-gate is staged-scoped in every caller, so 53 such items on disk are invisible to aw check)

Filed while authoring plan 1hrlp3 (backlog mbjuv5), which deferred this row and needs a durable carrier for it.

THIS IS A DESIGN DECISION WITH A REAL BLAST RADIUS, NOT A BUG. `check_engine.check_release_gate_consistency` Rule 1 iterates `_staged_backlog_done_items`, which returns `[]` when nothing under `backlog/` is staged, so the rule is STAGED-SCOPED in every caller (the commit-invariants aggregator, the `aw check` sweep, and the opt-in pre-commit hook alike). Its own comment states grandfathering as the DESIGN INTENT: "historical `done/` items closed before this guard existed are grandfathered (never retroactively flagged)".

Measured on the tree at authoring time (HEAD 615e03f68): `aw check release-gates` reports 0 errors over 556 checked and `aw check release-gates --all` reports 0 errors over 1985 checked, while driving `evaluate_blocking_close` directly over the same corpus returns 53 error verdicts. So no shipped surface reports the historical population.

WHY SIMPLY WIDENING THE RULE IS WRONG: it is ERROR severity and folded into the exit-blocking sweep, so widening it turns `aw check` and CI red on 53 historical items at once, and AGENTS.md forbids the mutation that would clear most of them (the gate rule governs LIVE items only; gating an already-done item "would assert a history that did not happen"). The plausible shape is instead a SEPARATE ADVISORY rule that never sets the exit code, as `check.orphaned-live-blocker` already does.

DO NOT SIZE THIS FROM THE RAW 53. Audit plan 1hrlp3 establishes that 5 were closed before the predicate shipped (no gate existed to bypass), 48 of 53 carry a close message asserting the work shipped, and `--evidence` is NOT PERSISTED on the item, so the 53 is an UPPER BOUND and not a count of proven drops. Read 1hrlp3's findings report before designing the rule; a rule tuned to 53 would mostly report exonerated rows and train people to ignore it.

- Id: mjrac4
- Status: done
- Graduated-To: mjrac4
- Set: mjrac4
- Priority: low
- Work-Kind: chore
- Summary: The two dependency-blocked writers record unsatisfied_dependencies in DIFFERENT shapes, so every consumer needs a special case

## Workflow history
- 2026-10-01 set (aw backlog): closed by aw oc run: IPD 8eei5p executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-mjrac4-01-8eei5p-give-every-dependency-block-producer-the-recovery-hint-by-th.ipd.md); evidence .aw/records/plans/executed/20260929-mjrac4-01-8eei5p-give-every-dependency-block-producer-the-recovery-hint-by-th.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260928T235941Z-1396311: 8eei5p
- 2026-09-21 created (aw backlog): Found while executing akzy45.

MEASURED at HEAD `6466cd33` while executing plan `akzy45`.

Two code paths write `dependency-blocked`, and they record the SAME fact in two incompatible shapes:

* `oc_runipd.cascade_dependency_blocked` writes the reason INTO the token
  (`"executed:aaa111 (target failed-safely)"`) and writes NO `unsatisfied_dependency_reasons` map.
* each host's drain arm writes a BARE token (`"executed:aaa111"`) plus a separate
  `unsatisfied_dependency_reasons` map, plus a `dependency_block_recovery` hint.

So a consumer cannot render either shape generically. `run_selection_policy.derive_item_disposition`
already documents the consequence and deliberately declines a fallback, because
`reasons.get(d, "unsatisfied")` would render the cascade's already-explained token as
`executed:aaa111 (target failed-safely) (unsatisfied)` - two contradictory reasons in one line. That
comment also records that `render_stream`'s diagnostics block carries the SAME fallback shape
(`reasons.get(d, "blocked")`) and therefore the same wart, and that it was left unfixed as
out-of-fence.

EVIDENCE OF THE COST: while writing `akzy45`'s tests I asserted the drain path's
`dependency_block_recovery` key on an item that the CASCADE had labelled, and the assertion failed for
a correct implementation. That is the trap this divergence sets for anyone reading the runner.

WHY `chore` AND NOT `bug`: the rendered output is correct today, because each consumer carries a
special case, and there is no user-perceptible wrong answer or measurable wait. Filed so the shapes can
be unified deliberately rather than discovered again.

SUGGESTED FIX: have the cascade write a bare token plus a reasons map (the drain shape), then delete the
special cases in `derive_item_disposition` and `render_stream`. Needs a migration thought for run
records already on disk carrying the inline-reason spelling.

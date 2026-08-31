- Id: 2k42zu
- Status: open
- Set: worksequence
- Priority: high
- Work-Kind: feature
- Summary: Committed work has no ordering surface: attention is an unordered set, roadmaps are explicitly non-commitments, and Item-Dependencies orders only plans

## Workflow history
- 2026-08-30 created (aw backlog): Committed work has no ordering surface: attention is an unordered set, roadmaps are explicitly non-commitments, and Item-Dependencies orders only plans

OBSERVED 2026-08-30, when the maintainer asked for "a checklist of items we need to work through" and
"where should we write these things down" and there was NO correct answer in the repo.

THE GAP. Nothing expresses "do these things, in this order, before anything else". Each existing
surface was evaluated and each fails for a DIFFERENT and legitimate reason:

- `aw attention` is a SET, by design. Its own contract says the shared sort key deliberately excludes
  priority for every tree, and the `xprio` Set added priority LABELLING only, explicitly leaving the
  sort key alone. So it answers "what needs attention", never "what next".
- The BACKLOG tree is a set too. `Blocked-By` with a typed gate expresses ONE item waiting on ONE
  thing; it cannot say "these six, in this order". `Priority` is a coarse bucket, not a sequence.
- ROADMAPS are explicitly disqualified by their own README: "A roadmap records intent and
  possibilities, not a commitment to execute." Wrong semantics for committed next-actions.
- `Item-Dependencies` on an IPD IS a real ordering mechanism, with typed `executed:<id6>` edges, a
  shared DAG evaluator, and cycle detection. It works well (the five-plan `runstop` chain executed in
  the right order tonight, and the `detrun` chain correctly refused when a link was blocked). But it
  orders PLANS ONLY.

That last point is the crux. Most real next-actions are not plan-shaped: "merge this lane", "answer
this open question", "decide whether to retire these five plans", "clean up these stale worktrees".
None of those can carry an `Item-Dependencies` edge because none of them is an IPD.

CONSEQUENCE. Ordered work currently lives in agent chat or in a gitignored scratch file, i.e. nowhere
durable. That directly contradicts this repo's own thesis: `GUIDING_PRINCIPLES` P5 and `DECISIONS` D91
make filesystem-encoded state the point, and AGENTS.md explicitly warns against keeping committed
backlog in prose "where the attention view cannot see it". An ordered plan-of-action is exactly such
prose today.

WHAT TO SOLVE FOR, not a prescribed design.

1. Is the answer a NEW artifact type, or a field on the existing backlog? A `Sequence`/`After` edge on
   a backlog item would reuse the tree, the checker and the attention view, at the cost of turning a
   set into a graph. Note the precedent: `Item-Dependencies` already proved typed id6 edges plus a
   shared evaluator work well here, and `check_engine.evaluate_ipd_dependencies` might generalize.
2. Should it order ITEMS or WORK SESSIONS? "What next" may be better modelled as a short ordered
   worklist that is deliberately EPHEMERAL and regenerated, rather than a durable graph that rots.
   A hand-maintained committed sequence goes stale the moment work lands, and a stale committed
   sequence is arguably worse than none.
3. Can it be DERIVED instead of authored? Dependencies plus priority plus release-gates may already
   determine a defensible order, in which case the answer is a `aw next` verb computing a view on
   demand (the way `aw attention` computes its classes) rather than a new file to maintain.
4. What is the relationship to `aw attention --check`? If an ordering exists it must not be able to
   contradict the attention view, or agents will get two answers.

NOTE THE IRONY, recorded because it is a genuine clue: the `detrun` Set was ABOUT deterministic run
ordering and cross-item dependency enforcement, and it is the Set that had to be reverted to
`to-review`. Whatever it got right about ordering is worth mining before designing this from scratch.

INTERIM PRACTICE, until this is resolved: durable ITEMS go to the backlog (so nothing is lost) and the
ORDER lives in a gitignored `tmp/` worklist that is treated as disposable and regenerated. Two
surfaces, different jobs. Do not commit a hand-ordered list.

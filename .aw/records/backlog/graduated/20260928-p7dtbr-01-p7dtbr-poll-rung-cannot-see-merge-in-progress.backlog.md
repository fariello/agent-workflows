- Id: p7dtbr
- Status: graduated
- Graduated-To: p7dtbr
- Set: p7dtbr
- Priority: low
- Work-Kind: chore
- Summary: The integration deferral poll rung waits only on dirty paths, so it reports a mid-merge checkout as a clear base and a deferred re-attempt refuses again immediately

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: qkwu1r
- 2026-09-28 created (aw backlog): Carrier for plan g2z2pp's deferred poll-rung row and its OQ-03.

MEASURED 2026-09-28 at HEAD 6a68f7fa while authoring plan g2z2pp (backlog csmtjp).

runner_shared.poll_for_integration_window is rung 2 of the integration deferral ladder. Its clearing
predicate is dirty_tree_overlap(repo, changed_files) alone. With a FOREIGN merge staged in main on a
path that does NOT overlap the incoming change, that returned [] while merge_in_progress(repo) was
True: the rung reports the base CLEAR while MERGE_HEAD is still set.

CONSEQUENCE. Plan g2z2pp makes a mid-merge checkout refuse as the deferrable merge-retry kind instead
of destroying the foreign merge. That refusal is correct, but a deferred re-attempt will refuse again
at once and consume a budget slot without ever waiting, because the rung believes there is nothing to
wait for. Nothing spins forever (the ladder still ends terminal at merge-needs-human when the budget
is exhausted), so this is wasted budget rather than a hang.

WHY IT IS FILED SEPARATELY from g2z2pp rather than folded into it. Teaching the rung about
merge_in_progress changes its clearing predicate, its POLL_BOUND_* reporting vocabulary and its detail
strings, all of which are pinned by tests outside that plan's declared Scope-Paths. It is also a
distinct concern: g2z2pp is about not destroying unowned state, this is about waiting well.

WORK-KIND chore, NOT bug, under the repository's perceptibility test. Nothing a user sees is wrong and
nobody waits on it: the rung returns FASTER than it ideally would, and the outcome is a preserved lane
plus an accurate refusal either way. The cost is a spent re-attempt slot, which is invisible unless an
operator reads the ladder's poll counts.

SKETCH. Add merge_in_progress to the rung's _try_once predicate so a mid-merge base counts as NOT
clear, and give it its own POLL_BOUND_* detail so 'waiting for dirt to clear' and 'waiting for a merge
to conclude' are distinguishable facts (they need different operator responses: the first clears when
someone commits, the second needs whoever staged the merge to conclude or abort it). Cite plan g2z2pp
F-10 for the measurement.

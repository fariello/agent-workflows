- Id: cl9dms
- Status: done
- Blocks-Release: next
- Set: cl9dms
- Priority: high
- Work-Kind: bug
- Summary: Runner dispatches a dependent whose executed: edge target finished substantially-complete, i.e. was never integrated, so the dependent runs against a tree missing the dependency's work

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by commit 8d5ccfb1 ('fix(runner): make the plan on disk the ONLY authority for an executed: dependency', 2026-09-19), verified an ancestor of HEAD 22cf67d9. That commit is the maintainer's response to the SAME incident this item was filed from, and its message names the defect as 'DEFECT 3 of the three the 2026-09-19 incident exposed'. WHAT CHANGED: edge_satisfied used to decide an executed: edge two ways, accepting the target's IN-MEMORY run status when the target was also in the run, which admitted substantially-complete via EXECUTION_SUCCESS_STATES. Now the by_id parameter is DELIBERATELY UNREAD (its docstring says so and says the maintainer removed the shortcut 'in favour of ONE authority: the plan's directory on disk'), and the live predicate resolves the plan path, takes plan_bucket, and requires 'executed' for an execute action. VERIFIED BY READING THE LIVE CODE, not the docstring: EXECUTION_SUCCESS_STATES and substantially-complete still appear in the function but ONLY inside comments narrating this very incident; every executable line of the executed: branch goes through plan_bucket/is_in_terminal_directory. The inconsistency this item flagged (77tr3o ruled substantially-complete does not count for retirement while it still counted for a dependency edge) is therefore resolved in the direction the item recommended. NOTE the item's warned second-order effect is real and unowned: tightening this makes dependents dependency-blocked where they previously ran, and nueip1 records that dependency-blocked has its own is-forever defect; nueip1 is already done, so that half is also addressed.
- 2026-09-19 created (aw backlog): Filed from run-20260919T194413Z-2056285: executed:yaxr4i reported satisfied while yaxr4i's work existed only on an unintegrated lane branch; carrier for the half spec 77tr3o Section 4 deferred.

MEASURED IN PRODUCTION, run `run-20260919T194413Z-2056285`, 2026-09-19. Queue position 3 (`n4xq3l`)
declares `- Item-Dependencies: executed:yaxr4i` and was DISPATCHED anyway, into a lane whose tree
does NOT contain yaxr4i's work. The plan exists solely to re-read a spec against yaxr4i's SHIPPED
flag surface, so it was dispatched against precisely the pre-yaxr4i surface it was written to avoid.

THE MECHANISM, verified by reading the code rather than inferring it. `EXECUTION_SUCCESS_STATES`
(`agent_workflows/oc_runipd.py:492`) is `{"executed", "substantially-complete"}`, and
`edge_satisfied` (`:3544-3555`) admits an IN-QUEUE `executed:` target when its run status is any
member of that set. yaxr4i finished `substantially-complete`, so the edge was reported satisfied.

WHY THAT IS WRONG, and it is not a naming quibble. `substantially-complete` is the status the runner
records when the agent self-reported `disposition: "executed"` but the plan is NOT in `executed/`
(`:6115-6117`). It therefore means the terminal transition did NOT happen. Critically, in this run it
also meant THE LANE WAS NEVER INTEGRATED: the runner's own event says so in as many words,
`worktree-preserved` with `reason: "the item finished 'substantially-complete' rather than executed,
so its work was never integrated; the lane is kept attributably for a later turn"`. yaxr4i's two
commits (`67c15b2f`, `8280c3b8`) exist ONLY on `aw/lane/yaxr4i`; `git merge-base --is-ancestor
67c15b2f HEAD` is false in the dependent's lane, and the dependent's tree measurably lacks the whole
deliverable (`grep -c -- '--color' agent_workflows/cli.py` -> 0, `tests/test_flag_surface_uniformity.py`
absent, `docs/cli-output-contract.md:159-163` still carrying the promise yaxr4i retracted).

So the state admits an edge whose ENTIRE PURPOSE is to guarantee the dependent sees the dependency's
work, at the one moment the runner has just recorded that the work was not merged anywhere the
dependent can see it. The failure direction is the dangerous one: it does not over-block, it
WRONGLY ADMITS.

COST, which is why this is filed as a bug and not a chore. Each wrongly-admitted dispatch spends a
full agent turn (this Set's turns run ~40-75 minutes each) to produce either nothing or, worse,
work validated against a stale tree that then looks verified. `n4xq3l` is one item; positions 4-10 of
this Set chain off it, so a single wrong admit can cascade through seven more dispatches.

ALREADY KNOWN AND DELIBERATELY UNOWNED. Spec `77tr3o` Section 4 names this exact defect in its
out-of-scope list: "`EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for an `executed:`
DEPENDENCY EDGE (`oc_runipd.py:274`). That is a distinct dispatch defect, observed on `xdr83v`, and is
not this spec's; R-2 only fixes what counts for RETIREMENT." That spec correctly fixed only the
RETIREMENT predicate and explicitly left the DEPENDENCY-EDGE predicate alone. Searched 335 backlog
items on 2026-09-19 and found no carrier for the deferred half, so the defect has been observed at
least twice (`xdr83v`, now `yaxr4i`/`n4xq3l`) while owned by nobody. This item is that carrier.

NOTE THE TWO PREDICATES ARE NOW INCONSISTENT, which is the cheap argument for the fix. `77tr3o`
already ruled that for retirement "`substantially-complete` does NOT" count, "it means finalize
refused" (`77tr3o:167`). The same token still counts for a dependency edge. One value, two opposite
readings, in one module.

SUGGESTED DIRECTION, not a design. The honest signal for "may a dependent see this?" is not the
agent's self-report but whether the work REACHED THE DEPENDENT'S BASE: the runner already computes
integration explicitly (`integration_is_earned`, `INTEGRATION_EARNED_BY_*`/`INTEGRATION_REFUSED_*`)
and already records `retention_reasons: ["not-integrated"]`. An `executed:` edge on an in-queue
target plausibly wants that integration verdict, not `EXECUTION_SUCCESS_STATES`. Whether
`substantially-complete` should be dropped from that set wholesale, or the edge check should consult
integration separately, is a design decision with two consumers and belongs in a spec. Flag the
second-order effect before changing it: tightening this makes dependents `dependency-blocked` where
they previously ran, which is the CORRECT direction but will visibly stall Sets whose dependencies
habitually end `substantially-complete`, and `nueip1` records that `dependency-blocked` has its own
is-forever defect. Fixing this one without that one converts wasted turns into stalled queues.

REPORTED BY the `n4xq3l` lane, which refused to act on its own plan because the plan's premise was
absent. It is filed as adjacent-code defect discovery, not as that plan's own unmet requirement.

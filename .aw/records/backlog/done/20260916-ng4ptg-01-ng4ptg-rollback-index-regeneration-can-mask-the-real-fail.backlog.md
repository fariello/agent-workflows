- Id: ng4ptg
- Status: done
- Set: ng4ptg
- Priority: medium
- Work-Kind: bug
- Summary: _rollback_precommit's step-4 index regeneration can turn a successful rollback into a reported failure, and its step-2 refusal now returns before it

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by plan 4xt6u4: step-4 index regeneration removed (ipd_lifecycle._rollback_precommit docstring)
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): _rollback_precommit's step-4 index regeneration can turn a successful rollback into a reported failure, and its step-2 refusal now returns before it

FOUND while executing plan u23gbn (dirtygates Order 04).

WHAT IS WRONG. `_rollback_precommit` performs four steps and returns `(False, msg)` on the FIRST failure. Step 4 regenerates the plans manifests fail-loud, so a manifest that cannot converge makes the whole rollback report FAILURE even when steps 1 to 3 restored the repository correctly. The caller then records `PHASE_UNKNOWN_OUTCOME` and says the repository was "NOT reported restored", which is stricter than the truth and pushes an operator toward manual intervention that is not needed: the manifests are GITIGNORED generated views whose remedy is `aw index plans`.

OBSERVED, in a form that shows the confusion is real. While measuring F-14 for u23gbn, the pre-fix call returned `ok=False` for an UNRELATED fixture reason (the manifest path) even though the destructive write in step 2 had already happened. F-14 itself records that as "itself instructive", and it is: a rollback that reports failure for a manifest reason is indistinguishable, to a caller, from one that failed to restore the plan.

RELATED BUT SEPARATE, and NOT a regression from u23gbn: u23gbn's E-08 guard makes step 2 RETURN EARLY with an unknown-outcome when a peer owns the origin bytes, which is correct and is what stops the data loss. That early return happens BEFORE step 3 (the git-index restore) and step 4, so a refused rollback now leaves the index entries untouched. That is the safe direction (it touches less), but it means the two failure shapes share one return channel and a caller cannot tell "refused to clobber a peer" from "could not restore".

WHAT A FIX MIGHT LOOK LIKE: separate the manifest regeneration from the restore verdict (a manifest failure is a warning on an otherwise-successful rollback), and give the refusal its own typed reason instead of a prose-matched `unknown-outcome:` prefix.

WHERE: `agent_workflows/ipd_lifecycle._rollback_precommit`, steps 2 to 4.

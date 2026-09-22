- Id: rfhiu2
- Status: open
- Set: rfhiu2
- Priority: medium
- Work-Kind: followup
- Summary: The finalize re-resolution silently falls back to a known-stale plan path, the twin of the verify-side hole closed by fzxfph

## Workflow history
- 2026-09-22 created (aw backlog): Identified while executing IPD fzxfph (runverdict-06).

WHAT IS WRONG. In `runner_shared.execute_item_core`, the FINALIZE step re-resolves the plan path and
then swallows the failure into a known-stale value:

    current_plan_for_finalize = resolve_plan_path(...)
    except DriverError:
        current_plan_for_finalize = plan_path

`plan_path` was captured EARLIER IN THE TURN. A self-finalizing plan MOVES out of `pending/` during
its own turn, which is precisely why the value needs re-resolving in the first place, so the fallback
substitutes a path the runner already has reason to believe is wrong and then feeds it to
`aw ipd finalize`.

WHY IT IS FILED SEPARATELY RATHER THAN FIXED IN `fzxfph`. That plan closed the byte-identical twin on
the VERIFY side (its fix (4)), where the same shape was measured causing 23 verifier turns to launch
against a path that no longer existed. Its scope fence explicitly excluded this one and instructed the
executor to identify and report it rather than widen the change, because it has a DIFFERENT CONSUMER
(`aw ipd finalize`, not a verifier launch) and therefore a different failure model: the finalize path
carries its own receipt and scope-reconciliation gates, which may or may not already catch a wrong
path. That question is the first thing this item should answer.

WHY THIS IS `followup` AND NOT `bug`, stated because the sibling defect WAS a bug. I did not measure
this one firing. The verify-side twin was filed on 23 observed occurrences in three named runs; here I
have a correctness hazard read from the source and NO measurement of user-perceptible impact. Per the
repository's own rule that an unmeasured hunch is not a bug, classifying it `bug` (and so gating a
release on it) would assert evidence I do not have. If a scan of recorded runs shows it firing, or if
the finalize gates are shown not to catch a stale path, RECLASSIFY it with the number attached.

SUGGESTED FIRST STEPS.
1. Determine whether `aw ipd finalize` already refuses a path that does not exist or does not match
   the item's id6. If it does, the hole is latent and the fix is a clearer error, not a behavior change.
2. Scan recorded runs for a finalize that acted on a `pending/` path after the plan had moved.
3. If the hole is real, apply the same treatment `fzxfph` applied to the verify site: refuse with a
   named recorded reason (reuse `VERIFY_ABSENCE_*`'s shape, not its verify-specific codes) rather than
   proceeding against a path the runner knows may be stale.

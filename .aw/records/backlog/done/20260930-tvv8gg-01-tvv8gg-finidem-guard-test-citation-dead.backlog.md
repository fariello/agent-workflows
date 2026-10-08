- Id: tvv8gg
- Status: done
- Graduated-To: tvv8gg
- Set: tvv8gg
- Priority: medium
- Work-Kind: chore
- Summary: plan_already_finalized cites a guard test file that does not exist, so the reusable-plan fail-open substitution it warns against is unguarded

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD pud8rp executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-tvv8gg-01-pud8rp-restore-the-reusable-plan-fail-open-guard-for-plan-already-f.ipd.md); evidence .aw/records/plans/executed/20261002-tvv8gg-01-pud8rp-restore-the-reusable-plan-fail-open-guard-for-plan-already-f.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: pud8rp
- 2026-09-30 created (aw backlog): Identified while authoring IPD `1fzist` (rfhiu2-01), whose F-9 measured it.

WHAT IS WRONG. `ipd_lifecycle.plan_already_finalized`'s docstring names a specific guard:

    ``tests/test_finidem_double_finalize.ReusablePlanIsNotAlreadyFinalized`` fails if
    the substitution is ever made.

That file DOES NOT EXIST. Measured at HEAD `2142a15d`: `ls tests/test_finidem_double_finalize.py`
returns "No such file or directory", and the only occurrence of `ReusablePlanIsNotAlreadyFinalized`
anywhere in the tree is the docstring line asserting the test exists.

WHY THE MISSING GUARD MATTERS, in the docstring's own words. The paragraph exists to forbid substituting
`run_selection_policy.is_in_terminal_directory` for the `executed`-bucket predicate, because
`TERMINAL_DIRECTORY_SEGMENTS` includes `/reusable/`, which is NOT a completed disposition
(`run_selection_policy._IPD_ACTIONS["reusable"]` is `ACTION_EXECUTE`, so a reusable plan is one the
runner DISPATCHES REPEATEDLY). Making that substitution would classify every reusable-plan run as
"already finalized", so a never-issued begin receipt would read as consumed and the run would proceed
with NO execution authority. The docstring calls this "the exact fail-open inversion this
classification exists to avoid, delivered by the predicate that looks safest".

WHAT IS OWED. Restore behavioral coverage that `plan_already_finalized` answers False for a plan under
`reusable/` and True for one under `executed/`, driving the shipped predicate rather than reading source
text, and then correct the docstring citation to name the file that actually holds it. `aw check` has no
rule for a dead test citation in a docstring, so nothing else will catch this.

WHY `chore` AND NOT `bug`. The substitution the guard forbids has NOT been made: the shipped predicate
still reads the `executed` bucket, so no user-perceptible defect exists today. What is missing is the
tripwire, plus a docstring that asserts a fact about the test suite that is false. Per the repository's
rule that an unmeasured hazard is not a bug, this is filed `chore`. If someone DOES make the
substitution, that is a fail-open security-shaped defect and the resulting item is a `bug`.

RELATED, NOT DUPLICATE. Plan `1fzist` adds an existence guard to `runner_shared.finalize_already_done`
for a different hole in the same call chain (a stale `executed/`-shaped path that does not exist on disk
converting a real refusal into exit code 0). That plan deliberately does NOT touch
`plan_already_finalized`, whose `executed`-bucket-without-reachable-commit tolerance is correct and is
the measured incident's own shape. This item is the reusable-plan half.

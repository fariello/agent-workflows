- Id: 8mohre
- Status: graduated
- Graduated-To: 8mohre
- Blocks-Release: next
- Set: 8mohre
- Priority: medium
- Work-Kind: bug
- Summary: derive_item_disposition labels an IN-QUEUE unmet dependency 'dependency_not_met_external', telling the operator it is outside this run's queue when it is not

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: zhqt51
- 2026-09-28 created (aw backlog): Filed at /plan-review of plan 5o1jye.

MEASURED 2026-09-28 at HEAD 04352120 while reviewing plan `5o1jye` (from backlog `fvsyqk`).

`run_selection_policy.derive_item_disposition` selects between two dependency disposition codes by SUBSTRING-MATCHING the composed reason prose: `code = SKIP_DEPENDENCY_NOT_MET_EXTERNAL if "not in this run" in named else SKIP_DEPENDENCY_NOT_MET`. Its own comment states the intent plainly and correctly - 'the DISTINCTION IS ACTIONABLE: an in-run dependency may yet be satisfied by this run, while an external one never can, so an operator's next step differs'.

THE SUBSTRING IS REACHABLE FOR A TARGET THAT IS IN THE QUEUE. `edge_satisfied`'s `executed:` branch resolves the target on DISK, not in the queue, and its refusal text is worded for the external case unconditionally: 'external target <id6> is <status> (directory <bucket>), needs one of [...] (it is not in this run, so it cannot become satisfied here)'. So an in-queue prerequisite that has simply not executed yet produces that phrase, and the substring match then picks the EXTERNAL code.

MEASURED, with the dependency target present in `state['queue']`:

    target IS in the queue: True
    reason: executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)
    derive_item_disposition code: dependency_not_met_external
    reason rendered: "dependency_not_met_external (a declared dependency is outside this run's queue and unsatisfied, so it cannot be met here; unmet: ...)"

USER-PERCEPTIBLE: the rendered gloss asserts the dependency is 'outside this run's queue' about an item sitting in that queue, and the two codes exist precisely because the operator's next step differs between them. A reader told 'external' concludes this run can never satisfy the edge and stops waiting; for an in-queue prerequisite that conclusion is wrong. Filed `bug` on the false statement, not on redundancy.

TWO SITES, ONE ROOT CAUSE. The mislabel is in `derive_item_disposition`, but the reason it is reachable is that `edge_satisfied` words an on-disk resolution failure as an external-target refusal regardless of queue membership. A fix that only reworded the refusal would move the problem rather than remove it.

FIX DIRECTION (not decided): give `derive_item_disposition` a TYPED signal rather than a substring match - the queue is available to the caller, so 'is this target a queue member' is answerable directly - and separately stop `edge_satisfied` asserting 'external' about a target it never checked for queue membership. Note deliberately that `by_id` is passed to `edge_satisfied` and is documented as UNREAD by maintainer ruling of 2026-09-19 (one authority: the plan's directory on disk), so the fix must NOT reintroduce a queue-status shortcut into the SATISFACTION decision; only the REASON WORDING and the disposition CODE are at issue, and that distinction is the whole difficulty.

Plan `5o1jye` does not fix this: it constrains its own new cascade prose not to add a THIRD route to the same mislabel (its E-02), and reports the pre-existing route here rather than reaching across its fence into `run_selection_policy.py`.

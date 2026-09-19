- Id: 5rebcb
- Status: open
- Blocks-Release: next
- Set: 5rebcb
- Priority: low
- Work-Kind: bug
- Summary: render_continuation_hint crashes on a malformed queue entry: item_reached_success calls .get unconditionally

## Workflow history
- 2026-09-19 created (aw backlog): Found while executing runnoop Order 03 (bsc457).

Measured 2026-09-19 at HEAD b5208b0e (i.e. BEFORE runnoop Order 03 bsc457, so this is pre-existing and not introduced by it).

`runner_shared.render_continuation_hint`'s `all_success` line evaluates
`all(item_reached_success(item) for item in queue)`, and `item_reached_success` does
`item.get("status")` with no isinstance guard. A queue holding a non-mapping entry therefore
raises `AttributeError: 'str' object has no attribute 'get'` while the driver is PRINTING ITS
EXIT FOOTER.

Reproduced on HEAD (bsc457's changes stashed):

    state = {"repo": "/repo", "run_id": "run-xyz", "set_sessions": {}, "queue": ["not-a-mapping"]}
    oc_runipd.render_continuation_hint(state, Path("/x"))
    -> AttributeError: 'str' object has no attribute 'get'

WHY IT MATTERS despite a malformed queue being unusual: this is on the EXIT path of every run, after
the work is done. A state.json an older driver wrote, or one a partial write corrupted, would crash
the footer and lose the closing report for work that actually completed. `item_reached_success`'s
own docstring advertises exactly this tolerance ('safe to call on a hand-written manifest's entry or
on a state file written by an older driver'), so the guard is missing against its stated contract.

Found while executing bsc457, whose own predicate (`no_turn_was_attempted`) DOES guard this and is
pinned by `test_the_no_turn_claim_FAILS_CLOSED_rather_than_guessing`. Not fixed there because
`all_success` is `zz5yxq`'s expression and bsc457's fence forbids touching the branch.

FIX: guard with `isinstance(item, Mapping)` in `item_reached_success` (fail closed: a
non-mapping entry is NOT a success), and add the malformed-entry case to the footer test.

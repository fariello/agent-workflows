- Id: cv5n6t
- Status: open
- Blocks-Release: next
- Set: cv5n6t
- Priority: medium
- Work-Kind: bug
- Summary: build_lane_outcome called without its required run_checked raised TypeError swallowed by suppress, so integration_changed_files was never recorded

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan h5pyqa; the call site was repaired in that plan.

## What is wrong

In `runner_shared.execute_item_core`, the integration-refusal arm did:

```python
with contextlib.suppress(Exception):
    item["integration_changed_files"] = list(
        build_lane_outcome(repo, wt_handle, item["id6"]).changed_files
    )
```

That resolved the SHARED `runner_shared.build_lane_outcome`, whose `run_checked` is KEYWORD-ONLY and
REQUIRED (each host supplies it via a one-line wrapper, per `integpath-02` `6sb3yu`). So the call raised
`TypeError: build_lane_outcome() missing 1 required keyword-only argument: 'run_checked'` on EVERY
integration refusal, and the surrounding `suppress(Exception)` ate it whole.

MEASURED 2026-09-20 by calling it the same way. The consequence was silent and directly harmful to a human
debugging a refusal: `integration_changed_files` was never written, so the refused item's record carried no
list of the files the lane would have merged.

## What was already fixed, and what is left

Plan `h5pyqa` binds `build_lane_outcome` from the driver module along`git_head`/`git_status` (the same
injection rule), so the existing call now resolves the host wrapper that supplies `run_checked`.

LEFT FOR THIS ITEM: the GENERAL hazard, which is the reason this is filed rather than closed. A broad
`contextlib.suppress(Exception)` around a call whose signature can drift converts a hard `TypeError` into
silence, and this is the second measured instance of a "swallowed exception hid a broken read" defect in
this seam (see `he9x6j`). Worth an audit of the suppress blocks in `execute_item_core` to narrow each to the
exception it actually anticipates, so a signature mismatch fails loudly instead of degrading a record.

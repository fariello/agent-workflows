- Id: qpgs4t
- Status: open
- Set: runviewdisc
- Priority: medium
- Work-Kind: chore
- Summary: Seven terminal-failure run statuses are still reported as artifact-status discrepancies by aw runs

## Workflow history
- 2026-09-22 created (aw backlog): Filed from IPD vdabn5 execution (F-10). Each needs its own measured argument about which declared statuses are legitimate for it.

Measured at HEAD 49848926 by calling `artifact_audit.audit_artifact` against a synthetic repo with a plan at `- Status: approved` in `pending/`.

IPD `vdabn5` added `interrupted` to the in-flight status-tolerance arm in `artifact_audit._status_disagrees`, with a measured argument for that ONE value. SEVEN OTHER run statuses fall through the same final equality with the IDENTICAL signature `location_mismatch=False status_mismatch=True`, so `aw runs` asks an operator to investigate each of them too:

```text
failed               location_mismatch=False status_mismatch=True
failed-safely        location_mismatch=False status_mismatch=True
partial              location_mismatch=False status_mismatch=True
not-attempted        location_mismatch=False status_mismatch=True
merge-conflict       location_mismatch=False status_mismatch=True
integration-blocked  location_mismatch=False status_mismatch=True
merge-needs-human    location_mismatch=False status_mismatch=True
cancelled            location_mismatch=False status_mismatch=True
```

WHY THIS WAS NOT SWEPT IN WITH `vdabn5`, and why it should not be swept in now either. Each of these is a TERMINAL failure state, not an in-flight one, whereas the arm's six accepted file values (`approved`, `to-review`, `draft`, `reviewed`, `queued`, `running`) are all pre-terminal. Admitting a terminal-failure status to that arm asserts something unmeasured: what a `failed` or `partial` item's plan may LEGITIMATELY read is a different question per status, and getting it wrong suppresses a row an operator needs. `vdabn5` earned its one value with a measurement plus a test case pinning the counterexample (an interrupted item beside a plan in `executed/` must KEEP flagging); each status here deserves the same treatment.

`integration-blocked`/`merge-needs-human` is ALREADY OWNED by backlog `1f9m2j`, which is BLOCKED on `rnl3b7` because classifying it benign requires proving a move was legitimate, and `artifact_audit` reads only a parent directory name and a `- Status:` regex. Do not duplicate that here; this item covers the remaining six.

A SCOPE FENCE ALREADY GUARDS THIS: `tests/test_run_viewer.py::RunViewerTests::test_the_seven_sibling_catch_all_statuses_are_deliberately_unchanged` asserts all eight keep flagging, so whoever picks this up must update that test deliberately rather than loosening the arm by accident.

Consider also whether the ad-hoc tolerance list is the right long-term mechanism at all. It is admittedly not a general solution; a direction-aware classifier would be, and the `difference_class` machinery (`classify_difference`, IPD `zexed1`) may already be the better place to express 'the run failed, so the plan's pre-terminal status is expected'.

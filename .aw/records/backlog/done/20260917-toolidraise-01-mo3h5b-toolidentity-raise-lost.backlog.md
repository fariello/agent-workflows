- Id: mo3h5b
- Status: done
- Set: toolidraise
- Priority: high
- Work-Kind: bug
- Summary: run_queue's except ToolIdentityError swallows a run-fatal error on both hosts; the raise was lost in merge 04a613aa

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by 61137509: raise restored in both hosts' except ToolIdentityError
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): Found while executing rununify Order 08 (ty3cj6) E-02

## What is wrong

`run_queue`'s dedicated `except ToolIdentityError` clause, on BOTH hosts, is:

    except ToolIdentityError:
        # ... "Re-raise to abort the whole run."
        save_state(run_dir, state)

The comment promises a re-raise. There is no `raise`. `ToolIdentityError` is documented RUN-FATAL
(lanetruth `af7i6p` OQ-02: a mismatch means nested `aw` calls are resolving a DIFFERENT copy of
`agent_workflows` than the runner itself, so no further item may run).

## Cause: an integration lost it, nobody decided it

The clause was authored WITH the `raise`. Commit `b04c70ce` (lanetruth `af7i6p`, 2026-08-30) added
`save_state(run_dir, state)` followed by a bare `raise`. It is absent from `04a613aa`, the
`laneorphan-01` / `zwnjp3` lane merge the same day, whose FIRST parent (`34aa1812`) has the `raise`
and whose SECOND parent (`6345f3d1`) does not have the clause at all. So this is a silent semantic
regression introduced by a merge resolution, not a recorded decision.

## Measured consequence, both hosts

`execute_item` writes `item["status"] = "running"` BEFORE it calls `assert_child_tool_identity`
(`oc_runipd.py:6807` vs `:7057`; `agy_runipd.py:3558` vs `:3755`). So on a real mismatch:

* the run does NOT abort. Every remaining item is dispatched under the same wrong control plane,
  which is precisely the outcome `af7i6p` OQ-02 says it rejects; and
* each affected item is stranded at the non-terminal status `running`, which is neither a terminal
  disposition nor one `--retry-incomplete` re-queues.

Driving both hosts' real `run_queue` with a stub that raises `ToolIdentityError` dispatches BOTH
queued items and returns exit code 1 with both left `running`.

## Why no existing test caught it

`tests/test_lane_tool_identity.py:733` asserts only that `except ToolIdentityError` appears BEFORE
`except DriverError` in `inspect.getsource(run_queue)`. It does, so all 29 tests in that file are
green on this broken code. That is the generic weakness of a source-offset pin.

## Current state

NOT FIXED. Plan `ty3cj6` pinned the broken behavior in
`tests/test_rununify_run_queue_characterization.py::ADocumentedDefectInTheToolIdentityHandler` (three
tests), each with a docstring instructing that it be DELETED and replaced with the intended-behavior
assertions in the same change that restores the `raise`. So the fix will announce itself as a test
failure rather than silently diverging from the guard.

## Why ty3cj6 did not fix it

Out of that plan's declared scope: it authorizes ONE named two-line repair (E-03's missing signal
refreshes), and the parent `rununify` Set forbids a child changing what a runner DOES. Restoring the
`raise` also changes which handler sees the exception on the interrupt/teardown path directly below
the clause, so it needs its own characterization. Recorded as decision `09-ty3cj6-D4`.

## Suggested fix

Add the bare `raise` back to both hosts, and REPLACE the three pinned-defect tests with the
intended-behavior assertions (the run raises; later items are never dispatched). Also consider
whether the item should be left `running` or recorded with a truthful non-terminal disposition on
the way out, since an aborting run still owes the operator an accurate ledger.

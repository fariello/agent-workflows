- Id: v75mym
- Status: open
- Set: v75mym
- Priority: medium
- Work-Kind: chore
- Summary: An IPD V-item can demand evidence that is impossible to produce, and nothing catches it before execution

## Workflow history
- 2026-09-21 created (aw backlog): Found while executing akzy45.

MEASURED while executing plan `akzy45`, and it cost a real decision mid-run.

That plan's E-03/V-03 require demonstrating that "an item blocked on a prerequisite that later succeeds
in the same run becomes runnable without `--retry-incomplete`", with the queue states before and after.
The demonstration is IMPOSSIBLE as written: AST-measured, both hosts call `requeue_interrupted` and
evaluate the `if retry_incomplete:` branch OUTSIDE their dispatch loop (`oc_runipd.run_queue` loop
6811-7048 with the calls at 6714/6715/6717; `agy_runipd.run_queue` loop 3395-3618 with the calls at
3295/3296/3298), and there are zero re-queue calls inside either loop. So a prerequisite that ended
non-terminally cannot be advanced again in the same invocation.

The only ways to satisfy the wording were (a) add a mid-run re-queue, which the SAME plan's scope fence
explicitly forbids ("Do NOT add a resurrection or un-blocking mechanism") and which spec `c4gd2h` R19's
indeterminate refusal exists to prevent, or (b) fabricate the demonstration. Both are bad outcomes, and
an executor under time pressure could plausibly pick (b), which is precisely the failure mode the V-item
contract exists to stop.

NOTE THE PLAN WAS REVIEWED AND APPROVED, and its review round explicitly re-verified E-03 and corrected
its premise once already (finding F-12). So this is not "a bad plan slipped through": the contradiction
is between an E-item's wording and a runtime fact that neither authoring nor review checked, and
`aw ipd lint` cannot see it because it is a SEMANTIC impossibility, not a structural one.

WHAT MIGHT HELP (not a design, just the shape): `/plan-review` could be asked to confirm, for each
V-item demanding a RUNTIME demonstration, that the demonstration is reachable in the code as it stands -
i.e. name the code path that would produce it. That is cheap for a reviewer already reading the cited
symbols, and it would have caught this one, since the answer is "no such path exists".

WHY `chore`: no shipped behavior is wrong and no user waits. The cost is executor time plus the risk of
a fabricated evidence block, which is a process risk rather than a defect in the product.

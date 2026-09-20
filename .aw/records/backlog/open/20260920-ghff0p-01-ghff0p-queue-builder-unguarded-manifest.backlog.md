- Id: ghff0p
- Status: open
- Blocks-Release: next
- Set: ghff0p
- Priority: medium
- Work-Kind: bug
- Summary: The run queue builder's unguarded manifest lookup can raise a bare KeyError after the run directory exists

## Workflow history
- 2026-09-20 created (aw backlog): The run queue builder's unguarded manifest lookup can raise a bare KeyError after the run directory exists

WHERE. `runner_shared.initialize_run_core`'s queue-build loop begins each item with an UNGUARDED `plan = manifest["plans"][id6]`. Two facts make that a defect rather than a style point: (1) it runs AFTER the run directory is created (`run_dir = state_root(repo) / run_id` plus the `sessions`/`outcomes`/`prompts` mkdirs and the decisions file), and (2) the loop immediately ABOVE it - the `selected_plan_paths` build - resolves the SAME lookup inside `except (DriverError, KeyError): continue`, so the two loops disagree about whether a missing entry is survivable.

WHY IT MATTERS. An id6 that reaches the queue build without a manifest entry produces a bare KeyError traceback with durable state ALREADY WRITTEN, which breaks the no-durable-state property every refusal in this seam is careful to preserve (`refuse_unimplemented_run_flags`, the mixed-type gate, and now the dependency closure all refuse ahead of the run directory for exactly this reason) and leaves the operator a run directory to reconcile by hand for work that never started.

REACHABILITY TODAY, stated honestly so nobody over- or under-rates this. With dynamic discovery every discoverable plan IS in the manifest, and depclosure 01 (`dhycim`) deliberately refuses at the seam any closure target the manifest lacks, so I could not reach it from the closure. It remains reachable in principle through an EXPLICIT `--manifest` whose plan set disagrees with what a selector resolves, and it is one permissive edit away from being reachable from the closure - which is precisely why the closure refuses instead of relying on this. Filed as a bug because the failure MODE (traceback plus orphaned durable state) is user-visible whenever it is reached, not because a reproduction is in hand today.

FIX. Make the access match its sibling loop: catch the missing entry and either skip with a recorded reason or refuse BEFORE the run directory is created. The second is preferable, since a silently shortened queue is the falsehood the surrounding refusals exist to prevent.

PROVENANCE. Recorded as F-18 by `dhycim`'s plan review at HEAD dc10dae6 and re-measured at execution HEAD bb714fd8 in the now-unified `initialize_run_core` (the plan cites the pre-unification per-host locations).

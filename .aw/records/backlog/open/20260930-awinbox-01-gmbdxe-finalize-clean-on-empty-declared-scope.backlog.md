- Id: gmbdxe
- Status: open
- Blocks-Release: next
- Set: awinbox
- Priority: high
- Work-Kind: bug
- Summary: Finalize reconciles an execution that touched NEITHER declared Scope-Path as clean, because the runner auto-acknowledges every declared-but-unmodified path and the zero-work retry predicate only ever considers a partial

## Workflow history
- 2026-09-30 created (aw backlog): Filed while authoring plan olmvgw from backlog an77ub, which re-lands the inbox counter lost by exactly this mechanism. an77ub deliberately does not diagnose the systemic half; this item owns it so olmvgw's Deferred row has a live carrier rather than pointing back at the item it graduated from.

MEASURED 2026-09-30 in lane worktree an77ub at HEAD 2c22b5bd, while authoring plan olmvgw.

WHAT IS WRONG. An execution that modifies NONE of its plan's declared Scope-Paths passes finalize's two-way scope reconciliation as CLEAN, so nothing in the lifecycle notices that a plan reached 'executed' having landed no code. Two independent guards each decline the case:

1. runner_shared.compute_scope_reconciliation builds an ACK for EVERY in_scope_unmodified path, with the wording 'declared-but-unmodified (auto-acknowledged by <host>)'. It does not bound how many of the declared paths may be unmodified, so 'all of them' is auto-answered exactly like 'one of them'.

2. ipd_lifecycle._reconcile_scope then has nothing left to demand. Driven directly with BOTH of plan 9iiqmm's declared paths (agent_workflows/attention.py, tests/test_attention.py) as in_scope_unmodified and those auto-acks supplied, it returned ok=True, missing_reasons=(), missing_acks=(). So the reconciliation cannot refuse.

3. The zero-work retry predicate cannot catch it either. runner_shared.handle_zero_work_retry returns the status immediately unless item['status'] == 'partial' (its docstring states partial is 'the ONLY status this considers'), and a self-finalized item is 'executed'. runner_shared.turn_attempted_nothing is therefore never reached on this shape.

THE MEASURED INSTANCE. Plan 9iiqmm sits in .aw/records/plans/executed/ with a self-finalize history record and V-items pasting PASSING test output, and its feature does not exist: both declared Scope-Paths carry zero 'inbox' occurrences on main, the footer string appears in no reachable commit ever, and the implementation survives only in unreachable dangling git objects. Backlog an77ub carries that lost work; plan olmvgw re-lands it. This item is the OTHER half: the mechanism that let it happen is still live, so the same loss can recur.

WHY 'bug' AND WHY IT GATES THE RELEASE. The user-perceptible harm is a false record: a maintainer reading 'executed' plus a closed backlog item is told the repository does something it does not do, and there is no surface that would have said otherwise. Per AGENTS.md a LIVE item whose work-kind is in the gating set must carry Blocks-Release.

WHAT THIS ITEM DOES NOT DECIDE, and the reason it is filed as a question rather than a patch. The auto-ack is DELIBERATE and correct in the ordinary case: a declared-but-unneeded file is normal, not a failure, and _reconcile_scope's own comment says so. So the fix is NOT 'stop auto-acking'. Candidate shapes, each with a cost a maintainer should weigh rather than an author choosing silently: (a) refuse (or loudly warn) only when EVERY declared path is unmodified, which is cheap and narrow but says nothing about a plan that touched one of five declared paths and skipped the work in the other four; (b) require the finalize record to state the empty-delta fact explicitly, which fixes the RECORD without changing any gate; (c) extend the zero-work predicate past 'partial' so a self-finalized turn that moved no declared path is scored, which is the most complete and the most likely to misfire on a legitimately records-only plan (an orchestrator, or a documentation plan whose declared paths are records). Note (c) interacts with orchestrator retirement, which deliberately skips the pre-transition checkpoint.

A NARROWER PRECEDENT EXISTS AND SHOULD BE READ FIRST. Backlog s9z85a (graduated, plan 1dcl10) concerns the OPPOSITE direction on the same audit: a path changed OUTSIDE the declared fence being silently excused. That plan's chosen posture is instructive here, because it fixes the RECORD without re-deciding the fail-toward direction, which is candidate (b) above. This item should not be resolved without reading it.

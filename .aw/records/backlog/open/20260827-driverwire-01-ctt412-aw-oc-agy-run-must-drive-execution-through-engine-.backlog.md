- Id: ctt412
- Status: open
- Blocks-Release: next
- Set: driverwire
- Priority: high
- Kind: feature
- Summary: aw oc/agy run must drive execution through engine-owned aw commit/aw finish (not runbook prose) so a run never leaves the IPD move/status/code changes uncommitted

## Workflow history
- 2026-08-27 open (aw set): Marked release blocker for 2.0.0 (next): uncommitted-work-after-aw-oc-run must be fixed before ship - the driver must commit through aw commit/aw finish, not rely on agent prose.
- 2026-08-27 created (aw backlog): aw oc/agy run must drive execution through engine-owned aw commit/aw finish (not runbook prose) so a run never leaves the IPD move/status/code changes uncommitted

Problem: after `aw oc run` executes/reviews an IPD, the resulting changes (the plan moved to executed/, status flip, code) can be left UNCOMMITTED, forcing the user to notice and hand-commit. Root cause: the driver `oc_runipd.py`/`agy_runipd.py` only INSTRUCTS the agent via runbook prose ("Commit only files you changed with path-scoped git commits", oc_runipd.py:871/1162/1183) - it does not commit itself. So committing depends on the agent obeying prose, which is exactly the unreliability at issue (build-order 40g511: the driver steers by prose, not enforcement).

Why the current sets DON'T fix it: selfcommit builds the shared path-scoped commit helper but adopts it into `aw archive/group/rename/ipd set/specs set`, NOT the driver. agentadhere Phase 2 (child 8dto0g) builds `aw commit`/`aw finish` (which DO commit deterministically) but nothing wires `aw oc/agy run` to CALL them instead of prose. The primitives exist/are-planned; the driver->primitive connection is the missing link.

Scope (build-order 40g511 R0): make `aw oc/agy run` drive execution THROUGH the engine-owned `aw commit`/`aw finish` primitives (path-scoped, no-push, hook-respecting), so the terminal transaction (finalize move + status + path-scoped commit) is performed by the tool, not left to agent prose. Replace the prose "commit your files" instruction with the tool doing it. Depends on: selfcommit (git_commit_helper), agentadhere Phase 2 (aw commit/aw finish), and the runner rename/wiring. Definition of done: a completed `aw oc run` of an approved IPD leaves the tree with the IPD in executed/ AND a path-scoped commit already made (nothing uncommitted); a test asserts no dirty owned paths remain after a driven run.

Origin: user - 'Will the IPDs fix the issue with uncommitted IPDs after an aw oc run command?' Answer: not as currently planned; this item captures the missing driver-wiring.

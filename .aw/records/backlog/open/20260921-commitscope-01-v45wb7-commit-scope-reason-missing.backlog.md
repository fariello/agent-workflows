- Id: v45wb7
- Status: open
- Blocks-Release: next
- Set: commitscope
- Priority: medium
- Work-Kind: bug
- Summary: aw commit <plan> has no --scope-reason escape, so a legitimate out-of-scope edit forces --no-plan

## Workflow history
- 2026-09-21 created (aw backlog): aw commit <plan> has no --scope-reason escape, so a legitimate out-of-scope edit forces --no-plan

FOUND BY: graduate Order 01 (`jxxec8`) execution, 2026-09-22.

WHAT IS WRONG. `aw commit <plan> -- <paths>` HARD-REFUSES when any path changed since the plan's frozen begin base is outside the plan's declared `- Scope-Paths:`, and it offers NO way to justify such a path. `aw ipd finalize` does: it accepts `--scope-reason <path>=<why>` and `--scope-ack <path>=<note>`, and AGENTS.md tells an agent exactly that ('If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason`'). So the contract instructs an agent to make a justified out-of-scope edit, and then the MANDATED commit verb has no spelling that accepts it.

MEASURED: `grep -c scope_reason` returns 0 in `agent_workflows/work_cmd.py` (which implements `aw commit`) against 8 in `agent_workflows/ipd_lifecycle.py` (which implements finalize). Reproduced live: `aw commit jxxec8 -- <the plan's three declared paths>` refused with two `check.scope-drift` findings naming `agent_workflows/command_surface.py` and `tests/test_command_surface_declarations.py`, which are the two registry entries a NEW CLI parser leaf is REQUIRED to have (an undeclared leaf fails `test_zero_undeclared_parser_leaves` closed).

WHY IT MATTERS, i.e. the user-perceptible impact. The refusal is not advisory and cannot be narrowed: because `check_scope_drift` reads the whole time window since the frozen base, once ONE out-of-scope path is committed in a lane, EVERY subsequent plan-governed commit in that lane is refused too, even a commit whose named paths are exactly the declared Scope-Paths. The only route left is `aw commit --no-plan`, which the tool itself announces SKIPS two protections (Scope-Paths enforcement and plan validation). So a contract-following agent is pushed off the governed path onto the less-protected one, for a reason the contract told it was legitimate. That is the gate training an agent to bypass it, which backlog `gjadwm` records as a failure mode in its own right.

WHERE. `agent_workflows/work_cmd.py`, `run_commit` (the `elif scope_paths and not is_grandfathered:` branch that prints 'refusing - out-of-scope change(s) present', and the `_validate_plan_via_engine` refusal immediately after it).

WHAT A FIX LOOKS LIKE (not prescriptive). Accept `--scope-reason <path>=<why>` on `aw commit` with the SAME spelling and the same semantics finalize already uses, so one grammar covers both ends of the lifecycle and the reason recorded at commit time is available to finalize rather than re-typed. Reuse the finalize helpers rather than forking a second comparator. Do NOT simply weaken the refusal: fail-closed is right, and what is missing is the attested escape, not the gate.

WORK-KIND. Filed `bug` rather than `chore`: it is not merely inelegant, it makes a MANDATED verb unusable for a case the contract explicitly authorizes, and the operator-visible consequence is a governed commit path that cannot be used at all for the rest of a lane. Per AGENTS.md every live bug gates the next release, hence `- Blocks-Release: next`.

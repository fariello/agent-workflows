- Id: s9z85a
- Status: graduated
- Graduated-To: s9z85a
- Blocks-Release: next
- Set: s9z85a
- Priority: medium
- Work-Kind: bug
- Summary: finalize silently excuses an out-of-scope path committed in its own untrailered commit, so the --scope-reason demand never fires

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 1dcl10
- 2026-09-28 created (aw backlog): finalize silently excuses an out-of-scope path committed in its own untrailered commit, so the --scope-reason demand never fires

FOUND WHILE AUTHORING the plan that graduates `ldy1al` (the commit gate's unreachable `--scope-reason` escape). Filed separately because it is a DIFFERENT defect in the OPPOSITE direction, and because `ldy1al`'s fix must not be reviewed as if it closed this.

WHAT IS WRONG. `finalize_precheck` ownership-filters its out-of-scope demand set through `_working_tree_path_is_owned`, whose COMMITTED-half evidence is (1) an `AW-Item` trailer, else (2) commit COHESION, i.e. the path shares a commit with a declared Scope-Paths path. An out-of-scope path committed ALONE, in an UNTRAILERED commit, satisfies neither: it lands in `disregarded_unowned_paths` and `out_of_scope_paths` comes back EMPTY, so `_reconcile_scope` demands nothing and finalize succeeds having never asked for the `--scope-reason` that AGENTS.md says is mandatory.

MEASURED 2026-09-28, in temp repos, using the suite's own `_completed_plan_text` fixture. A plan declaring `agent_workflows/demo.py, tests/test_demo.py` also changed the undeclared `agent_workflows/render.py`. Three arrangements, identical file content, only the COMMIT SHAPE differing:
- render.py alone in an UNTRAILERED commit -> `out_of_scope_paths: []`, `disregarded_unowned_paths: ['agent_workflows/render.py']`, and `finalize(..., apply=False)` with NO `scope_reasons` at all returns **exit 0**.
- the same commit carrying `AW-Item: abc123` -> `out_of_scope_paths: ['agent_workflows/render.py']`, finalize **exit 1** demanding the reason.
- render.py in the SAME commit as the declared `demo.py` (cohesive) -> `out_of_scope_paths: ['agent_workflows/render.py']`, finalize **exit 1**.

So the demand is decided by COMMIT SHAPE, not by what the execution changed, and the shape that escapes it is exactly the one an agent is currently pushed into: `ldy1al` measures that `aw commit <plan>` refuses after any out-of-scope change, leaving `aw commit --no-plan -m ... -- <path>` as the only route, and that route commits the path ALONE. Outside a run it adds no trailer (`_trailers_from_args` returns `[]` with no `AW_RUN_ID`/`AW_ITEM_ID6`), so the commonest hand-execution path produces precisely the untrailered solo commit that escapes.

WHY IT MATTERS. The plan's permanent finalize record then asserts a clean scope reconciliation for an execution that went outside its declared fence, and no human is ever asked. `ldy1al`'s fix makes the governed commit path usable again, which INCREASES how often this shape occurs unless the trailer is present; note the mitigation is real under a runner, where `aw commit` stamps `AW-Item` from `AW_ITEM_ID6` and the demand does fire.

THIS IS NOT THE DOCUMENTED COST. `ipd_lifecycle` is explicit that cohesion is a heuristic and that "an executor's OWN committed out-of-scope path escapes the reason requirement when it rides in an UNTRAILERED commit containing no declared path", adding that with trailers the cost "applies ONLY to untrailered commits". That is an accurate description of the mechanism; what is not recorded is that the accepted cost is reachable by the ROUTE THE TOOLING ITSELF FORCES, which is what makes it a live defect rather than a bounded compromise.

POSSIBLE SHAPES (not a decision). Make `aw commit --no-plan` stamp an `AW-Item` trailer when a plan selector was refused or is otherwise known; or have finalize treat a path recorded as commit-time-justified (whatever store `ldy1al` settles on) as owned, so the justification survives regardless of commit shape; or narrow the excuse so a path is only disregarded on POSITIVE evidence of another owner rather than on absence of evidence of this one. Each trades a false demand against a false excuse and needs a maintainer ruling on which direction fails safe.

WORK-KIND. Filed `bug`: a gate the contract calls mandatory does not fire, and the user-perceptible consequence is a committed permanent record that asserts something untrue about the execution. Per AGENTS.md every live bug gates the next release, hence `- Blocks-Release: next`.

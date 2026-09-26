- Id: m10mrs
- Status: graduated
- Graduated-To: planpathtype
- Blocks-Release: next
- Set: m10mrs
- Priority: medium
- Work-Kind: bug
- Summary: resolve_plan_path fails OPEN and returns a non-plan path with no diagnostic, so a mistyped selection reaches plan-shaped code silently

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan mxzogk (Set planpathtype), re-verified live at HEAD.
- 2026-09-23 created (aw backlog): MEASURED while executing plan ui8b9b on 2026-09-23, and previously measured and recorded by superseded plan mng63x's review (which counted 48 plan-shaped call sites): runner_shared.resolve_plan_path's selectors branch can RETURN a path that is not an IPD (for example a .spec.md file) with no diagnostic at all, because it resolves an id6 through selectors.resolve_selectors and accepts any single file match. Every caller treats the result as a plan.

WHY THIS IS A BUG: the function's own contract is to locate an IPD, and its failure mode for a non-IPD input is to SUCCEED with the wrong artifact type rather than to refuse. A silent wrong answer handed to plan-shaped code is strictly worse than a loud refusal, and is user-perceptible as whatever downstream misbehavior the plan-shaped reader then produces.

HOW ui8b9b WORKED AROUND IT RATHER THAN FIXING IT (out of that plan's declared scope): resolve_selected_artifact_paths resolves each artifact through its OWN discovery authority (discover_plans/the manifest for ipd, discover_specs for spec) precisely so the type of a resolved path is a FACT rather than an inference, and refuse_unrunnable_selected_types then refuses a non-plan selection before the queue is built. That contains the hazard for the new --type path only; the 48 pre-existing call sites are untouched.

SUGGESTED FIX: have resolve_plan_path VERIFY the resolved path is an IPD (the shipped authority is status_set.detect_artifact_type, already used by run_selection_policy.classify_paths) and raise DriverError naming the artifact type it actually found. That is a behavior change for callers that currently get a wrong-typed path silently, which is the point.

WHERE: agent_workflows/runner_shared.py, resolve_plan_path (the selectors branch).

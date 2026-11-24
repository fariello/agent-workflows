- Id: 8nf0jn
- Status: open
- Set: 8nf0jn
- Work-Kind: chore
- Priority: medium
- Summary: Discourage repeated whole-suite pytest/venv runs during /plan-review and tailor review-turn driver prompt
- Short-Description: Discourage repeated whole-suite pytest/venv runs during /plan-review and tailor review-turn driver prompt

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): Discourage repeated whole-suite pytest/venv runs during /plan-review and tailor review-turn driver prompt

Observed on pubrun run-20261123T155235Z-2317768 (aw oc run reviews on Set test-audit): 5 plan-review turns spent 8h 14m and $80.67 running 168 pytest invocations (3h 16m of pytest runtime, including 25 multi-minute full-suite/benchmark runs, throwaway venv/pip installs, and duplicate full-suite -p randomly runs on an unchanged checkout). Contributing causes: (1) plan-review/steps/_kernel.md forbids editing code/tests and states 'Effort, time, cost, and tokens never justify deferral' without clarifying that this applies to fixing vs. deferring findings rather than running redundant multi-minute test suites during review; (2) the driver prompt injects execution boilerplate ('even when it takes minutes (aw check plans, test runs)') into action=='review' turns. Proposed improvement (discourage and scope-bound rather than blanket-forbid, since targeted checks can legitimately settle factual claims): (1) update plan-review/steps/_kernel.md (and plan-review-long parity) to prefer static reading first, allow narrow fast targeted checks (--collect-only or single file/-k with --no-cov) when static reading cannot settle a blocking claim, strongly discourage full-suite runs / --cov / benchmarks / throwaway venvs / /tmp probe plugins, and never repeat a full-suite run on an unchanged tree; (2) clarify the Fix Bar scope sentence in _kernel.md; (3) replace the execution-oriented 'test runs' foreground-wait boilerplate with review-appropriate guidance when action=='review' in oc_runipd/agy_runipd/runner_shared.

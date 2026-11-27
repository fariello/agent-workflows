- Id: 2hssxe
- Status: open
- Set: cliverbs
- Work-Kind: feature
- Priority: medium
- Summary: Add standalone --action validate (/verify-execution on executed plans) to oc_runipd/agy_runipd and wire top-level aw validate (spec ogd2nv R-15)
- Short-Description: Add standalone --action validate (/verify-execution on executed plans) to oc_runipd/agy_runipd and wire top-level aw validate (spec ogd2nv R-15)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 created (aw backlog): Add standalone --action validate (/verify-execution on executed plans) to oc_runipd/agy_runipd and wire top-level aw validate (spec ogd2nv R-15)

Implement standalone AI post-execution verification (/verify-execution) on already-executed plans across runner_shared.py, run_selection_policy.py, oc_runipd.py, and agy_runipd.py (adding 'validate' to ACTION_CHOICES and ACTION_IMPLEMENTED, terminal-plan selection, /verify-execution prompt building, session launch, and evidence/corrective-IPD handling), then expose top-level 'aw validate <ids|set>' wired through run_dispatch.dispatch_for_state (using the 'validate' per-state profile default from m7jcis), command_surface.py, tests/conformance_matrix.py, completion.py, docs/cli-output-contract.md, and CHANGELOG.md. Deferred from Set cliverbs Order 03 (xocj8i) per the 2026-11-27 maintainer ruling on xocj8i OQ-01; tracks spec ogd2nv R-15 and the aw validate portion of AC-06. Acceptance: aw validate <executed-id6|set> dispatches standalone /verify-execution on both oc and agy hosts with normalized selectors, refuses non-executed items before creating a run directory, updates completions/declarations/docs, and passes @pytest.mark.core behavioral tests and mypy.

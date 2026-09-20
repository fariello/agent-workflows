- Id: 7ap6ku
- Status: done
- Blocks-Release: next
- Set: 7ap6ku
- Priority: high
- Work-Kind: bug
- Summary: Naming a Set queues its RETIRED plans for execution: expand_selectors applies its terminal filter only on the 'all' branch, so 271 Sets would dispatch 587 executed/superseded/not-executed plans (measured), on both hosts

## Workflow history
- 2026-09-20 done (aw set): FIXED 2026-09-20 in a0788d4b (merged 1a64e13c). Two shared predicates in runner_shared replace the single-branch closure: manifest_entry_is_selectable refuses only the DELIBERATELY RETIRED (superseded, not-executed) by status OR directory independently, and manifest_entry_is_sweepable carries the all-branch's original stricter allowlist. THE NARROWING MATTERED: refusing everything TERMINAL broke two shipped properties the suite caught, so an executed plan stays selectable (it is a valid executed:<id6> dependency target; filtering it would restore the dead-prerequisite bug that killed 9 parents, 6 children and 2 orchestrators at queue build) and a status-less static-manifest entry stays selectable (initial_queue_status(None) answers reviewed by design). A Set member is dropped silently, an explicitly named plan refuses loudly, and the empty-result message now distinguishes 'you named nothing' from 'everything you named was retired'. MEASURED AFTER: retired plans queueable tree-wide 0 (was 587 terminal / 39 retired across 271 Sets); oc and agy both expand setidhard to ['bwgyum'] alone; the orchestrator probe has no target so the coverage gate cannot fire on yku4ga. 20 new regression cases in tests/test_runipd_selector_admission.py cover every selector FORM on BOTH hosts plus an anti-re-fork guard; verified they fail against the bug (neutering the filter reddens 7). Suite on the merged result: 7134 passed, 3 skipped, 2 xfailed. No new ruff findings (454 before and after, identical code sets).
- 2026-09-20 created (aw backlog): Naming a Set queues its RETIRED plans for execution: expand_selectors applies its terminal filter only on the 'all' branch, so 271 Sets would dispatch 587 executed/superseded/not-executed plans (measured), on both hosts

/tmp/opencode/body.md

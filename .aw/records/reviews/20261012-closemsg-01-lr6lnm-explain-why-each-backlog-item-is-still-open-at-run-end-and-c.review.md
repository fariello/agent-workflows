# Review findings: plan lr6lnm

- Subject-Id: lr6lnm
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `de45dd969` in an isolated review lane. The plan was committed and unchanged, so no snapshot was taken. `aw ipd lint --phase author --agent` was clean before the semantic review, and `--phase review-finalize` was clean after the revisions.

Verified against code and the live tree:
- `runner_shared.unclosed_backlog_items` uses the "so the close was never evaluated" template. `render_unclosed_report` and `record_unclosed_backlog_items` match the plan's description. `emit_shutdown_report` calls both from the signal path.
- `runner_shared.dispatch_orchestrator_item` sets `item["status"] = "executed"`, appends `orchestrator-finalized`, and returns without calling any backlog close. F-03 is confirmed.
- Both `dispatch_orchestrator_item(` call sites are in `oc_runipd.py` and `agy_runipd.py`. Neither host module was in Scope-Paths.
- `evaluate_backlog_close(repo, "iosmvn", [])` on the live tree (orchestrator plus 4 executed children) gives "this run executed none of its carriers, so the close was not earned". With the orchestrator's `executed/` path earned, it gives close=True. An orchestrator item has no attempts, so `collect_earned_paths` returns nothing unless `last_plan_path` is set.
- All seven F-04 items are already under `backlog/done/`, each with "closed by 0owirm: every carrier executed" dated 2026-10-13. `0owirm` explicitly Carrier-Declined a retirement close site, but its check fires only when the item itself is queued for production.
- Re-derived population: among graduated items, `backlog_item_already_complete` is COMPLETE for `rolswj`, `iosmvn`, `23p80m`, `coivul`, `5st6e5`, and `58x9mw`. Of these, `iosmvn`, `coivul`, `5st6e5`, and `58x9mw` have an executed orchestrator carrier. `aw backlog set done iosmvn --dry-run` accepts.
- `deliberate_stop_event` carries `not_started`. `labels.command` already includes the verb (`z3si7r` note). No run records exist in the lane worktree.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness (fix would not work) | `runner_shared.evaluate_backlog_close` "this run executed none of its carriers"; `collect_earned_paths` reads attempts and `last_plan_path`; `iosmvn` probe | Calling `process_backlog_close` after a retirement would REFUSE every time. The orchestrator item contributes no earned path, so E-05 as written would record a refusal and close nothing, and the E-07 test would fail. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now re-resolves `item["last_plan_path"]` after retirement, the way `finish_reintegrated_item` does, and passes `lane_repo=None`. V-05 adds a proof that removing that line brings the refusal back. |
| PR-002 | HIGH | IN-SCOPE | G. Stale premise | All seven F-04 ids are in `backlog/done/`, closed by `0owirm` on 2026-10-13 | E-06 would try to close items that are already closed. The authored count was a live-artifact count used as the bar. | all Low | FIXED | E-06 re-derives the set at execution (COMPLETE and having an orchestrator carrier), with an empty result allowed. Scope, Concern, F-04, and V-06 were updated to match. |
| PR-003 | MEDIUM | UNDER-SCOPE | C. Architecture (overlap with executed work) | `0owirm` Deferred "Carrier-Declined: Covered by this plan's dispatch-time check" | The plan never mentioned that `0owirm` declined this exact close site. Without that, a reviewer or executor could reasonably think E-05 duplicates `0owirm`. | all Low | FIXED | Added a Step 0 convention explaining why the dispatch-time check does not cover a retirement in an execute run. Both routes go through the same gated setter. |
| PR-004 | MEDIUM | IN-SCOPE | E. Verification feasibility | No run records in the lane (runs root is machine-local and gitignored) | E-01, V-02, and V-03 depended on a specific run's `state.json`, which an isolated lane cannot reach. | all Low | FIXED | Allowed a synthetic reproducing state as a fallback, and required stating which source was used. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Scope declaration | `oc_runipd.py` / `agy_runipd.py` `dispatch_orchestrator_item(` call sites | The binding must be threaded at host call sites that were not in Scope-Paths. The plan's own Scope check made this conditional, but it is certain. | all Low | FIXED | Added both host modules to Scope-Paths, E-05, and the Scope check. |
| PR-006 | LOW | IN-SCOPE | F. UX / correctness of next command | `turn_retry_remedy` `z3si7r` note; `emit_shutdown_report` signal path | The resume template `aw <host> run resume` invites the `aw oc run run resume` bug. The rewrite must also stay handler-safe. | all Low | FIXED | E-03 now builds the command from `labels.command` and keeps the Palette coloring and handler safety. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate was missing `aw ipd begin`, a scope fence, the no-hand-edit rule, and finalize that depends on runner vs. hand execution. | all Low | FIXED | Rewrote the gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the retirement close earn its carrier? | Set `last_plan_path` to the retired orchestrator's executed path | Pass `executed_overrides` (meant for a lane's own pending plan, not one already landed); bypass the earned gate (weakens E-04) | `finish_reintegrated_item` precedent; `iosmvn` probe | yes |
| D-2 | What should E-06 close? | Items re-derived as COMPLETE that have an orchestrator carrier | Every COMPLETE item (covers causes outside F-03 that `0owirm` already handles); drop E-06 (leaves the F-03 residue stranded) | live probe; `0owirm` dispatch-time scope | yes |

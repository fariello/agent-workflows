# Review findings: plan nnsa2o

- Subject-Id: nnsa2o
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `7a36efc61`. The plan was committed and byte-identical
to the sealed lane input (rev-8); no snapshot needed. `- Kind: child`, so `IPD-S407` does not apply. `aw ipd lint --phase
author` clean before; `review-finalize` clean after. Orders 00 to 06 are `reviewed`, none executed.

Re-measured in `agent_workflows/runner_shared.py`: `verification_retry_decision` / `perform_verification_retry_decision`
(re-queue with `recovery_next`); `resume_via_launcher` and the defect re-ask's two host shapes (`resume_session=` for oc,
`session_id=` plus `use_continue=False` for agy); `oc_runipd.run_opencode` honors `resume_session` after its isolated-turn
fresh-session rule and reuses `REVIEW_SWEEP_SESSION_KEY` inside the sweep lane; `build_review_prompt` returns only the
slash command plus the isolation notice, while correction notices are rendered by `build_prompt` (execute turns only);
`reconcile_disposition`'s review branch returns `"reviewed"` for any exit-0 turn with positive evidence whatever the plan's
on-disk status; `commit_review_lane_output` / `commit_review_shared_output` precede integration; both production branches
call the production commit helper with the turn-start `baseline_plan_ids`. A spy on `execute_item_core` over the bare suite
(`5083 passed, 2 skipped`) saw no review dispatched on an orchestrator. A demotion on a copy of `r2wa38`
(`aw ipd set to-review r2wa38 --message ... --yes --no-commit`) kept `- Readiness: go-pending-approval`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A data integrity | measured demotion run; `status_set.apply_status_change` strips only `- Approval:`; `tests/test_readiness_absence_invariant.py` `test_corpus_partition_pre_review_plans_lack_readiness_field`; `r07vma` R6 | E-03 demotes a `reviewed` orchestrator to `to-review`, but the reviewing agent's `- Readiness:` survives, so a refused review keeps a readiness claim and the corpus invariant test fails. The plan's "do not write Readiness" did not cover removing one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Order 05 (`26m1nb`) E-05, which owns the backward-move setter behavior, now strips `- Readiness:` on a move to `draft`/`to-review` (re-scope note there); `26m1nb` added to `- Item-Dependencies:`; E-03 relies on it and V-03 greps for its absence. |
| PR-002 | HIGH | IN-SCOPE | A correctness | Order 05 E-01 (setter refuses `reviewed` for a not-ready orchestrator); `reconcile_disposition` review branch | E-03 triggered only "when the plan reads `reviewed`". After Order 05 an orchestrator lacking a coverage record never reaches `reviewed` through the agent's setter call, yet the turn scores `reviewed`, so the check never ran and the item was reported reviewed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 runs after every exit-0 orchestrator review, names three outcomes including "ready but still `to-review`", and sets the item `fail-gate` whenever the plan did not reach `reviewed`. |
| PR-003 | HIGH | UNDER-SCOPE | G reachability | `build_review_prompt` (slash command only); `build_prompt` renders `build_correction_notice` | E-03 "remand the review" with a correction packet had no delivery path: a re-queued review's prompt cannot carry the packet. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 delivers the correction by `resume_via_launcher` into the sweep's recorded session, as E-02 does, with its own decision counter. |
| PR-004 | MEDIUM | IN-SCOPE | A correctness | `commit_backlog_production_output(target_tree, id6, baseline_plan_ids, ...)`; defect re-ask host shapes | E-02 did not say which baseline the correction turn's commit uses (a new baseline would classify the first turn's plans as out of scope) or which session argument each host takes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 states the original baseline, both host shapes, the no-session fallback, and that the Set verifier re-asks after an edit. |
| PR-005 | MEDIUM | IN-SCOPE | G executability | Scope-Paths (runner_shared, one test); `render_stream.render_run_summary_table` | E-04 asked the end-of-run summary to name correction counts, which lives in `render_stream.py`, outside scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 uses `record_refusal` (already rendered by `aw runs` and the summary) and `write_report` in `runner_shared`; any renderer edit needs a scope reason. V-04 updated. |
| PR-006 | LOW | IN-SCOPE | G execution contract | gate section | No scope fence and no paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate completed, dependencies named. |
| PR-007 | LOW | IN-SCOPE | C reuse / consistency | F-03 "verdict store"; E-02 remedy wording; targeted tests | Stale store wording; remedy text would be a second copy of Order 03's shared remedy; existing send-back and review-commit tests absent from the targeted run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 reworded with the spy measurement; remedy reused from `orchestrator_readiness`; three test files added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where is `- Readiness:` removed on a demotion? | In the setter (Order 05 E-05), for every backward move to `draft`/`to-review` | in this plan's review path only (Order 09's demotions would keep it); leave it (invariant test fails) | `status_set.apply_status_change` `- Approval:` strip precedent; `r07vma` R6 | yes |
| D-2 | What triggers the post-review readiness check? | Every exit-0 review of an orchestrator | only when the plan reads `reviewed` (unreachable after Order 05 for a record-less plan) | `reconcile_disposition` review branch; `26m1nb` E-01 | yes |
| D-3 | How is the review correction delivered? | Session resume in the sweep lane | re-queue with `recovery_next` (review prompt drops the packet) | `build_review_prompt`; `oc_runipd.run_opencode` sweep-session reuse | yes |

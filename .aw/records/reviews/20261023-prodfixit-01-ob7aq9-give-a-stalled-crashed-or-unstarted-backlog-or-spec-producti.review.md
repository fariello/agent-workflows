# Review findings: plan ob7aq9

- Subject-Id: ob7aq9
- Subject-Type: ipd
- Reviewed-At: 2026-10-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `bbceabeb2`. The plan was byte-identical to the lane input and already committed, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean` before and after revision. Child plan (Set `prodfixit`, Order 1), runner code plus spec amendment.

Verified at the lane HEAD (all in `agent_workflows/runner_shared.py` unless noted):
- F-01 CONFIRMED: `if not is_review and not is_production:` guards all three `handle_turn_failure_retry(` calls (spawn-failure arm, `except StallTimeout as stall_exc:` arm, post-turn call under the `retrywire` comment); `is_production = action == "plan"`.
- F-02 CONFIRMED: `elif is_fix_it_recovery and prev_attempt is not None:` sits inside `if self_finalize and not is_review and not is_production:`; the production branch `if (is_spec_production or is_backlog_production) and isolate:` always calls `allocate_isolation_worktree` and sets `session_id = None`.
- F-04b CONFIRMED: `reclaim_lanes_on_interrupt` branches on `lane["state"]`, `reclaimable` and `holds_work` and reads the item only through `interrupt_lane_item_record`.
- F-05 CONFIRMED: `lane_containment.format_preserved_lanes` renders from `preserved_worktree`; nothing in the reclaim clears it. An inline clear already exists in the deferred-integration `_finish` closure.
- F-06 CONFIRMED: `commit_backlog_production_output` appends a pending plan to `out_of_scope` when its id is in `baseline_plan_ids` and it is not continued.
- F-07 CONFIRMED, and a second production prompt build site exists (the lane rebuild) which overwrites the first.
- F-08 CONFIRMED: Set correction loop resumes with `corr_session = attempt.get("session_id")` via `resume_via_launcher`.
- F-10 CORRECTED: `aeq7f8` E-03 required the retry decision to be recorded with its reason; its V-item evidence records "retry budget is skipped for production" with no reason. The plan's "neither discusses it" was too strong.
- `turn_failure_is_retryable` reads the LAST entry of `item["attempts"]`; the production Set correction loop appends `corr_rec` (no `turn_failure_kind`) there.
- The Set correction loops wrap `resume_via_launcher` in `except (KeyboardInterrupt, StallTimeout): raise`, outside the inner stall arm; `oc_runipd.run_queue` catches it in `except DriverError` and writes `failed-safely`.
- Shared-tree path: `continued-plan-pre-dirty-dropped` filter and recomputed baseline mis-handle a failed attempt's uncommitted plans.
- `rg -n '\u2014|\u2013'` does match an em dash (probed on a scratch file, exit 0), but run over a whole diff it also matches removed and context lines.
- The incident run directory `run-20261023T221924Z-2698768` is not present in this lane (run records are gitignored); F-03/F-04/F-05 incident facts were not re-verified and E-02 re-derives the defect with a scripted host, so the plan does not depend on that directory.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Correctness (missed failure site) | `runner_shared.py:44897` `except (KeyboardInterrupt, StallTimeout): raise` in the production Set correction loop; `oc_runipd.py:4519` `except DriverError as exc:` | A stall during a Set correction turn escapes `execute_item_core` and is recorded as a bare `failed-safely` with `driver_error`: no stall kind, no snapshot, no fix-it turn. Same production-stall defect, second site, not covered. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added F-13, E-14/V-14 (one shared stall helper used by both sites), E-10 case (11), Scope IN line. |
| PR-002 | HIGH | IN-SCOPE | Correctness (counter isolation) | `turn_failure_is_retryable` `last_attempt = attempts[-1]`; `corr_rec` appended at `runner_shared.py:45043` and `:45674` | The post-turn admission for production cannot rely on the last-attempt read: after a Set correction loop the last entry is a `corr_rec`, so the plan's "admit only a turn carrying `turn_failure_kind`" was unstated as a mechanism and could charge or skip the wrong counter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now gates the production call on the LIVE `attempt` carrying `turn_failure_kind` and records `turn_retry_skipped` otherwise; V-03 tightened. |
| PR-003 | MEDIUM | UNDER-SCOPE | Correctness (shared tree) | `continued-plan-pre-dirty-dropped` block guarded `wt_handle is None and continued_plan_ids`; `commit_backlog_production_output` `if p_id not in baseline_plan_ids:` | With `--no-isolate-worktree` the fix-it attempt recomputes the baseline from a tree holding the failed attempt's uncommitted plans, so they are reported out-of-scope or dropped. E-07 covered only the resumed lane. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-12; E-07 branch (b); E-10 case (12); V-07 extended. |
| PR-004 | MEDIUM | IN-SCOPE | Correctness (prompt delivery) | Pre-lane `elif is_backlog_production:` build and lane rebuild under `if work_dir and (is_spec_production or is_backlog_production):` | Two production prompt build sites; the lane rebuild overwrites the first and is what is written to `prompts/`. Prepending at one site only would be inert on the default isolated path. | all Low | FIXED | E-08 names both sites and one helper; V-08 demands the diff. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (report record) | `lane_containment.record_preserved_lane_state` writes `preserved_disposition`; `_lane_records_from_state` yields one record per lane; `_finish` inline clear | E-09's clear list omitted `preserved_disposition`, did not guard against clearing the record when a DIFFERENT lane of the same item is reclaimed, and duplicated an existing inline clear. | all Low | FIXED | E-09 clears every written field, compares branch/worktree first, replaces the `_finish` inline loop with the helper; V-09 extended. |
| PR-006 | MEDIUM | IN-SCOPE | Correctness (keep predicate) | E-06 "whose last attempt carries `turn_correction`" | `turn_correction` lives on the failed attempt; reading only `attempts[-1]` and ordering against the live-owner skip were unspecified, and the interaction with E-09 clearing was unstated. | all Low | FIXED | E-06 searches back for the newest attempt carrying `turn_correction`, runs after the live-owner skip, and leaves `preserved_*` intact. |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy | `aeq7f8` E-03 "Decide it, record it with the reason"; its V evidence "retry budget is skipped for production" | F-10 said no record discusses the exclusion; `aeq7f8` recorded the decision without a reason. | all Low | FIXED | F-10 rewritten as CORRECTED. |
| PR-008 | LOW | IN-SCOPE | Evidence feasibility | V-12 em/en-dash `rg` over the whole CHANGELOG diff | Over a whole diff the pattern also matches removed and context lines, so it can fail on text the plan did not add. | all Low | FIXED | V-12 greps only added lines (`^\+`). |
| PR-009 | LOW | IN-SCOPE | Test executability / reachability | E-10 case (9) "a stop at the checkpoint between items" | No mechanism was named for a scripted test to stop the run between the failed attempt and the fix-it dispatch. | all Low | FIXED | Case (9) names `runner_stop.request_stop(..., LEVEL_AFTER_CALL, ...)` from the launcher or a direct `reclaim_run_lanes` call, and requires recording which; V-05/V-06/V-14 name the producing code path. |
| PR-010 | LOW | UNDER-SCOPE | Transparency | stall arm `snapshot_lane_dirty_work`; `integrate_review_lane_branch` merge | On a resumed production lane the `WIP INTERRUPTED SNAPSHOT` commit is integrated to main with the lane. Content is correct; history carries a WIP-titled commit. Unstated. | all Low | FIXED | F-14; E-06 records the behavior in a code comment rather than rewriting history. |

`aw ipd lint --phase review-finalize --agent`: recorded in the plan's workflow history after `aw ipd set reviewed`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the Set-correction-turn stall (PR-001) be in this plan or a separate backlog item? | In this plan as E-14 | File a backlog item and defer (rejected: same defect class, same file, same helper; deferral would ship a known production-stall hole under the same `Blocks-Release` gate) | `runner_shared.py:44897`; plan Goal "a backlog or spec production turn stalls"; plan-review Fix Bar (Remediation Risk Medium) | yes |
| D-2 | When a Set correction turn stalls, which counter is charged? | Set counter keeps the unit it already spent; turn counter is charged once for the stall | Refund the Set unit (rejected: the turn ran and cost money); charge neither (rejected: unbounded) | `production_set_retry_decision` spend-before-launch; `handle_turn_failure_retry` budget arithmetic; plan convention "each send-back owns its own counter" | yes |
| D-3 | Should a snapshot commit be squashed out before integrating a resumed production lane? | No; record that it is integrated as-is | Squash or rewrite the lane branch (rejected: rewriting history inside a lane is outside scope and adds risk to the merge path) | `worktree_lease.snapshot_lane_dirty_work` docstring (plumbing commit, "unlosable"); F-14 | yes |
| D-4 | Stop mechanism for E-10 case (9)? | Between-turn stop request from the scripted launcher, or direct `reclaim_run_lanes`, executor records which | Prescribe one (rejected: whether the checkpoint stop reaches run-end reclaim must be measured at execution) | `runner_stop.request_stop`, `BETWEEN_TURN_LEVELS`; `oc_runipd.run_queue` calls `reclaim_run_lanes` after the loop | yes |

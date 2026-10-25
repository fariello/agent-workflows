# Review findings: plan uiyoax

- Subject-Id: uiyoax
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `abf2f8730` in a runner lane worktree (non-interactive). The lane-input copy is
byte-identical to the tracked plan (committed, unmodified, `f10f8f3cd`), so no pre-review snapshot.
`aw ipd lint --phase author` and `--phase review-finalize` are clean before and after revisions.

Verified symbols in `agent_workflows/runner_shared.py`: `build_review_prompt` (returns
`f"/{handler} {rel_path}"`), `execute_item_core` (calls the injected `spawn_executor`),
`reconcile_disposition`, `resume_via_launcher` (docstring pins two launcher callers per host),
`handle_review_orchestrator_readiness` (uses `write_prompt(..., suffix=...)` and both host spellings,
`resume_session=` vs `session_id=`/`use_continue=False`, with `log_suffix`), `write_prompt`,
`attempt_log_path`, `add_run_label_flags` ("no behavior change" help), `dependency_depth` (Set edge only
`if entry.get("action") == "orchestrate"`), `commit_review_lane_output`, `commit_review_shared_output`,
`requeue_interrupted`, `perform_defect_reask`, `probe_reply_text`, `REVIEW_SWEEP_SESSION_KEY`,
`turn_runs_in_review_sweep_lane`, `record_refusal` (re-exported from `render_stream`). In
`plan_readiness`: `newest_verdict`, `REVIEW_VERDICT_TOKENS`, `review_staleness_index`,
`is_review_history_entry`, `classify_verdict`. `run_dashboard._SESSION_NAME_RE`, `phase_of`,
`ATTEMPT_FACTS_SCHEMA_VERSION = 3`. `check_engine` rule `check.review-finding-unescalated`. Runner spec
`25kzda` has Sections 2.6, 3.2, 4.4 (`IPD-REVIEW-HISTORY` row "Exactly one new review entry"), 5.4.
The sweep lane does keep a resumable session (`oc_runipd.run_opencode` `sweep_lane_turn`), so E-06's
same-session premise holds inside the review sweep lane.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | UNDER-SCOPE | A correctness / C state | `runner_shared.execute_item_core` raises `DriverError(f"Review sweep changed session unexpectedly: {existing_sweep} -> {session_id}")`; sweep session read in `oc_runipd.run_opencode` (`sweep_lane_turn`) and `execute_item_core` (`review_uses_sweep_session`) | E-10 asked for a new session on a Set change but did not name that the sweep reuses ONE run-wide session and aborts when the captured id differs. As written the first review of a second Set would abort the run. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-10 names both code paths that must change together, keeps `single` mode unchanged, and its outcome and E-15 assert no `DriverError` on a Set change. |
| PR-002 | medium | IN-SCOPE | E observability | `run_dashboard._SESSION_NAME_RE` role `[a-z][a-z0-9-]*`; measured: `...-review-step-02-R1+R2.jsonl` no match, `...-review-step-02-r1-r2.jsonl` match | Check names are uppercase (`R1`), so per-step logs named from them would be invisible to the attempt grain, defeating E-11/AC-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 fixes the label as lowercased check names joined by `-`. |
| PR-003 | medium | IN-SCOPE | G executability | `run_dashboard.collect_rows` "Session files no attempt claimed" branch builds rows from `by_item_attempt` | E-11 did not say where per-step rows come from; they are unclaimed session files, not the attempt's own `log`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-17 (split from E-11) names that branch and the `""` default elsewhere. |
| PR-004 | high | UNDER-SCOPE | D invariant | measured: `newest_verdict` on a plan whose newest line is `- <date> /plan-review pass 2 (<agent>): re-ran R2` returns `(None, ...)`, hiding an older approving record; `is_review_history_entry` accepts it via the `/plan-review` label | Spec MD-15 allows progress history lines, but a `/plan-review`-labelled progress line is read as the newest review record and voids the verdict. E-03 counted verdict lines by token substring, which misses this. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-03 counts with `is_review_history_entry` + `classify_verdict` and requires a non-review label (`review progress`); E-08 treats a verdict-less `/plan-review` line before S7 as a guard violation; `3bwrfx` E-09 tells the agent the form (cross-plan re-scope line). |
| PR-005 | medium | IN-SCOPE | A correctness | `aw ipd set reviewed` writes `- <date> reviewed (aw set): ...`, which `is_review_history_entry` accepts | E-08's restore removed only lines "that carry a verdict token", missing the `aw set` status line if the agent ran the setter early. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-08 removes every line `is_review_history_entry` accepts, naming the `aw set` line. |
| PR-006 | medium | IN-SCOPE | R7 cross-plan | `is2xiv` E-03 "the small context object Order 04's `run_review_sequence` already holds (send-prompt callable, tier, variant, checks already run, plan path, review-record path, the plan text at the start of the pass)" | No plan defined that object; `is2xiv` assumed it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 defines `ReviewSequenceContext` with those seven fields plus `pass_no`, `baseline`, `review_steps`. |
| PR-007 | medium | UNDER-SCOPE | G right-sizing | E-11 bundled run-state recording and resume snapshots with dashboard/analytics/docs (two test surfaces, three modules) | One item, two independent test surfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Split: E-11 recording + snapshot file (V-11 run-state evidence); new E-17 analytics (V-17); E-15 depends on E-17. |
| PR-008 | low | UNDER-SCOPE | durable carrier | `check.ipd-uncarried-obligation` (fired on sibling plans this run) | Deferred rows had no typed carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `is2xiv` for the loop; `kk62qt` for the Stage 2 rows. |
| PR-009 | low | UNDER-SCOPE | C canonical mechanism | `gv3smb` E-06 (reviewed) adds `review_tier` to `dashboard.js` lists | New attempt fields `review_step`/`review_checks` would be CLI-only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-17 adds them to `COLUMNS` and the `dashboard.js` lists; Scope-Paths adds `dashboard.js`. |
| PR-010 | low | IN-SCOPE | G spec trace | spec `k3yx72` post-cutover; E-15 cited AC-xx unqualified; AC-09 first half unowned | SPEC-PLAN-TRACE ignores unqualified ids; orchestrator `tiwj2o` assigns AC-09 first half to this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-15 cites `` `k3yx72` AC-xx `` and adds the AC-09 first-half case; Required tests updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Change the sweep session rule in single mode too? | No, steps mode only | Change both (alters live sweep cost behavior before the pilot measures it) | spec `k3yx72` MD-19/MD-20 compare old and new on the same code; OQ-01 opt-in | yes |
| D-2 | Progress-line label | `review progress` | Forbid progress lines (spec MD-15 allows them); teach `is_review_history_entry` to skip verdict-less `/plan-review` lines (changes a shared gate predicate outside this plan's scope) | measured `newest_verdict` behavior above; spec `k3yx72` Section 7.2 first bullet | yes |
| D-3 | Split the plan into several child plans on size (30.9 KB, 17 E-items, 4 groups)? | No; split only E-11 | Split into model / loop / sessions+resume plans (would cut E-06..E-09, which share one function, across plans) | each remaining E-item names one deliverable; `aw ipd lint` size limits 18/5 not exceeded | yes |

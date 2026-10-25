# Review findings: plan is2xiv

- Subject-Id: is2xiv
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c63a782d6` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot.
`aw ipd lint --phase author` clean before revisions; `--phase review-finalize` clean after.

Verified: spec `k3yx72` (approved) Sections 5.3, 6, 6.1, 7.1, 7.2, 8.1 to 8.3, 9.1 to 9.4, 14
(AC-03 to AC-07, AC-14), 15 (Order 05 Stage 1); `runner_shared.perform_defect_reask` (re-validates
with `validate_defect_report`, defect-report specific), `runner_shared.probe_reply_text`,
`runner_shared.classify_probe_reply`, `runner_shared.resume_via_launcher`; `ipd_lint.parse`
(`ParsedDoc.exec_leaves`/`valid_leaves`/`meta_fields`/`open_questions`); `ipd_schema.read_readiness`;
`plan_readiness.is_review_history_entry`, `newest_verdict`, `classify_verdict`;
`review_findings.parse_review_text`, `subject_gating_blocks`. `rg -n "AW-REVIEW" agent_workflows`
returns nothing (F-01 holds). Order 04 `uiyoax` (reviewed) E-06 defines `ReviewSequenceContext` and the
S6 delegation point; E-11 the `review_steps` schema with `pass`; E-12 resume. `3bwrfx` E-09 writes
`steps/s6-rereview.md` with both markers and the `review progress` history form. SPEC-PLAN-TRACE
(`production_checks._compute_spec_trace_coverage`) only counts `k3yx72`-qualified ids.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | IN-SCOPE | G executability / R7 cross-plan | `uiyoax` E-06 `ReviewSequenceContext` fields; is2xiv E-03 `run_rereview_loop(ctx)` | The loop signature took only `ctx`, which carries neither the pass-1 S6 reply nor the text after R2/R4, so the loop could not parse the first marker or evaluate the third trigger; nor did it say prompts go through Order 04's per-prompt path. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-03 takes `(ctx, s6_reply, *, after_r_text)`, defines `RereviewResult`, sends every prompt via `ctx.send_prompt`, and propagates host failures. |
| PR-002 | medium | IN-SCOPE | A correctness | spec `k3yx72` Section 8.2 third bullet; is2xiv E-02 `confirm_after_r: bool` | A boolean cannot express "a confirm-listed item changed AFTER R2/R4 ran"; the check needs the plan text at that moment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 takes `after_r_text` and runs `review_sequence.structural_diff(after_r_text, now_text)`; `None` disables it; tests both. |
| PR-003 | medium | IN-SCOPE | G executability | spec `k3yx72` Section 5.3 `simple` and `orchestrator` rows; Section 8.3 | "the tier's review checks (Q or R1 to R7)" left the re-review prompt list undefined for `orchestrator` (R1+R2, R7) and silent on P/T. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-03 derives the pass prompts from the tier's groups minus P, T, S5, S6, S7, kept to `checks_run`, empty groups dropped. |
| PR-004 | medium | IN-SCOPE | C canonical mechanism | `runner_shared.perform_defect_reask` calls `validate_defect_report(read_defect_report_outcome(...))` | The plan cited it as the re-ask primitive; it validates a defect report, so it cannot be reused for a marker. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-03 follows its one-re-ask shape without calling it and gives the marker-only re-ask text; conventions updated. |
| PR-005 | high | UNDER-SCOPE | C recovery / D invariant | spec `k3yx72` Section 9.3 (records pass number); `uiyoax` E-12 resumes from `review_steps` only | Resume inside pass 2 or 3 needs the pass-start text (trigger baseline) and the after-R2/R4 text, which nothing recorded; a resumed re-review would compute triggers against the wrong baseline. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-05 persists `attempt["rereview"]` with pass-start and after-R snapshot hashes; E-06 tests resume inside pass 2. |
| PR-006 | medium | UNDER-SCOPE | G executability | is2xiv E-04; `ipd_schema.read_readiness`; `ipd_lint.parse(...).open_questions` | The limit-rule postcondition had no named home or predicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-04 adds pure `limit_reached_instruction` and `check_limit_s7` (new open question id with `Blocking: yes`, `Status: open`; `no-go`) and states where the runner calls them. |
| PR-007 | medium | UNDER-SCOPE | E testing | spec `k3yx72` AC-07 (pass guard), Section 8.2 (Item-Dependencies, confirm-only); is2xiv E-06 | Tests omitted the verdict guard on a re-review pass prompt, the Item-Dependencies and confirm-only triggers, and `check_limit_s7`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 adds those cases; V-05/V-06 demand their output. |
| PR-008 | low | IN-SCOPE | G spec trace | `production_checks._compute_spec_trace_coverage` `cite_pattern` requires `k3yx72` prefix | AC ids in E-06 and V-* were unqualified, so SPEC-PLAN-TRACE saw none. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Qualified as `` `k3yx72` AC-xx `` in E-06, V-03 to V-06, Required tests. |
| PR-009 | low | UNDER-SCOPE | G execution contract | is2xiv gate; `uiyoax` E-16 runs `make test-all` for runner core | Gate lacked the finalize ownership rule and scope-ack wording; validation omitted `make test-all` although `runner_shared.run_review_sequence` changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten with the full contract; E-07/V-07 add `make test-all` and `tests/test_rereview_reviewed_plan.py`. |
| PR-010 | low | UNDER-SCOPE | durable carrier | `check.ipd-uncarried-obligation` [ERROR] on this plan (`aw check all`) | The Section 9.4 Stage 2 deferral row had no typed carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added `- Carrier: kk62qt` (Order 09 files the Stage 2 backlog item on BUILD THE REST), matching `uiyoax` PR-008. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which prompts does a re-review pass send for tiers without R1 to R7? | Tier's groups minus P, T, S5, S6, S7, kept to checks already run | Always send Q; send all R checks | spec `k3yx72` Section 5.3 and 8.3 ("tier's review checks"); OQ-01 keeps runner-visible units equal to pass 1 | yes |
| D-2 | Marker-only re-ask wording | `Your last reply did not end with the re-review marker. Reply with exactly one last line: AW-REVIEW: AGAIN or AW-REVIEW: DONE.` | Reuse Section 6 generic re-ask text | spec `k3yx72` Section 8.1 rule 3 ("for the marker only") | yes |
| D-3 | Where to record the loop state for resume | `attempt["rereview"]` beside `review_steps` | Extend `uiyoax` `review_steps` entries (another plan's schema) | `uiyoax` E-11/E-12; this plan's Scope-Paths include `runner_shared.py` only | yes |
| D-4 | Split the plan? | No | Split pure functions and runner wiring | 7 E-items, one module plus one wiring point; each E-item one deliverable | yes |

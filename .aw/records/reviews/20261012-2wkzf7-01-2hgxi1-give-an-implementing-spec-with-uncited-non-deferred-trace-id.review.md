# Review: Give an implementing spec with uncited non-deferred TRACE ids a plan-writing turn

- Subject-Id: 2hgxi1
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at lane HEAD `a1fcb9fe1`. The plan was committed and unchanged, so the snapshot was skipped.
`aw ipd lint --phase author` reported `clean` before review and `--phase review-finalize` `clean` after.

Re-verified TRUE:
- `runner_action('spec','implementing')` prints `undetermined`; `test_5_1_undetermined_action_refuses_at_freeze`
  and `test_undeterminable_action_is_reported_not_bucketed` pass (`2 passed`) (F-01).
- `production_checks` exposes `spec_plan_trace`, `parse_spec_requirement_ids`, `parse_spec_id_markers`,
  `_find_executed_linked_plans`, `spec_plan_trace_deferred`, `spec_plan_trace_vacuity`,
  `spec_requires_requirement_ids`, `existing_handoff_plans`; `rtvdak` is in `plans/executed/` (F-02).
- `c4gd2h`, `7ckptx`, `z7nbn1` are the only `implementing` specs, all `False grandfathered` (F-04).
- `spec_plan_trace` body: pooled-set assembly, qualified `cite_pattern`, `_ORCH_ROW_RE` exclusion,
  E-vs-V split and marker filtering all live inside it, so the E-02 extraction is real (F-02).
- `_SPEC_ACTIONS` comment "`implementing` absent: it dispatches its From-Spec children" and the
  `draft` precedent for content-dependent refinements in `runner_action` (OQ-01).
- Every E-03 call site exists: `expand_selectors` (`_policy.runner_action("spec", ...)`),
  `closure_target_admission`, the `--action` preflight (`for_legality=True`) and the typed non-plan
  queue branch in `initialize_run_core`, and `classify_paths` (`_action_for(spec_type, status)`).
  Freeze refusal reads the queue entry's `action`, so routing the queue builder is what lifts it.
- Spec production arm: `build_spec_production_prompt`, `_append_continue_handoff_section`, the five checks
  in the named order, `production_set_retry_decision`, the `specs set ... --status implementing` success
  argv, and `commit_spec_transition_output`'s "-> implementing" subject.
- `25kzda` 3.3 `implementing` row and 2.6 "`--action plan` is legal only for an `approved` spec or
  `open` backlog item"; `89xjll` 3.3 OQ-08 TARGET/STOPGAP bullets, 6.1 first paragraph.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Spec sync | `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md:76` ("Verification entry point: `run_selection_policy._SPEC_ACTIONS` maps strictly `approved` to `ACTION_PLAN` ... judge exclusively the `approved` spec population") | E-05 amends `89xjll` 3.3 and 6.1, but Section 2 carries the same claim, which becomes false once this ships. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05, its Expected outcome, V-05 and the Spec sync section now include the Section 2 "Verification entry point" bullet. |
| PR-002 | MEDIUM | UNDER-SCOPE | F. Honest errors / C. single authority | `agent_workflows/runner_shared.py:29876` `enforce_requested_action` ("Plan is the next legal action only for an approved spec") | Once E-03 makes `--action plan` legal for an eligible `implementing` spec, the refusal text for an ineligible one becomes false and would mislead the operator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now rewords the message to name the `implementing` re-plan condition (the file is already in Scope-Paths). V-03 now asks for the refused run's message to be pasted. |
| PR-003 | LOW | IN-SCOPE | A. Evidence accuracy | Scratch-repo probe: `aw specs set <implementing spec> --status implementing --message probe --no-commit` -> `unchanged`, history `- 2026-10-12 implementing (aw specs): probe` | F-05 said a same-status set is "tagged with `same-status`". The probe shows the setter reports `unchanged` and writes an `implementing` history line, which reads as a transition. The conclusion (use a note) still holds, and is stronger. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 corrected with the probe output. OQ-02 now cites the demonstration of `aw specs note`, which kept status and directory. |
| PR-004 | LOW | UNDER-SCOPE | C. Single authority (scope declaration) | `agent_workflows/partition.py:331` `_is_runnable` uses `action_for_status` (no refinements) | `aw partition -t specs` will treat an eligible `implementing` spec as not runnable. This matches how it already treats every content-dependent row (a complete `draft`), so it is not a new divergence, but the plan's Scope check claimed every entry point was named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to Deferred with the precedent and a Carrier-Declined line. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked a scope-fence declaration, the conditional runner/executor finalize ownership, and an explicit statement that the open questions are resolved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. E-01's GATE is kept and identified as a genuine prerequisite stop. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `aw partition` gain the `implementing` refinement? | Defer, declared | Add it in E-03 | `partition.py:331` already ignores the `draft` refinement; changing it is a separate `partition` behavior change | yes |
| D-2 | Is OQ-02 (record a stage via `aw specs note`) demonstrated? | Yes, keep resolved | Re-open as a spike | Scratch-repo probe recorded in F-05 | yes |
| D-3 | Is the reworded `--action plan` refusal a public-contract change needing the human? | No: wording of an error message inside an already-declared Scope-Path, backed by a spec amendment the plan makes | Raise as a blocking question | `25kzda` 2.6 amended by E-05; the message is diagnostic text | yes |

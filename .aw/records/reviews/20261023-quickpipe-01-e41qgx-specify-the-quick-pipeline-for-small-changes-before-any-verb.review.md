# Review findings: plan e41qgx

- Subject-Id: e41qgx
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72da75876`. The plan was byte-identical to the lane input and already committed (`a91760528`), so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean` before and after revisions. Spec-only child plan (Set `quickpipe`, Order 1) graduating backlog `rsisop`.

Verified at the lane HEAD:
- Backlog `rsisop` exists (now under `graduated/`, `Graduated-To: quickpipe`) and carries the quoted "Needs its own spec" sentence.
- Specs `k3yx72` and `llbr2b` exist under `specs/reviewed/`; `k3yx72` N4 points at `rsisop`, MD-1, Sections 5.1, 5.2 and Order 02 of Section 15 read as cited. No code mentions `Review-Depth` or `sensitive_paths`.
- Every symbol E-02 cites resolves: `ipd_authoring.run_scaffold` / `build_skeleton`, `ipd_lifecycle.validate_transition` (forward skip allowed, `executed` needs `>= reviewed`), `ipd_lint.check_readiness_required` / `check_readiness_attestation`, `attention_contract.TRANSITION_AUTHORITY`, `ipd_schema.READY_TO_EXECUTE` / `META_RECOGNIZED` / `MAX_E_LEAVES` / `MAX_TASK_GROUPS` / `OQ_HEADING_RE` / `META_ATTENDED`, `runner_shared.set_plan_approved` / `initialize_run_core` / `item_needs_approval`, `plan_readiness.is_plan_review_approved`, `run_selection_policy.runner_action`, `production_checks` `BACKLOG-GRADUATE-SET`, `check_engine.check_live_bug_gate` (iterates `backlog._iter_items`), `backlog.decide_gate_default`, `command_surface.COMMAND_INVENTORY`, `ipd_sub` in `cli.py`.
- F-4 re-measured: 151 small executed non-orchestrator plans, 21 with `From-Backlog`, 0 naming a `.spec.md` file (the plan said 150 of 151 name no spec; one names the specs directory).
- F-3's 96 of 1,161 is a live count; re-measured at this HEAD with a slightly different glob as 119 of 1,173, which is drift, not error.
- F-5 reproduced: the scaffold preview with `--work-kind bug` and no `--from-backlog` prints no `Blocks-Release` line.
- `aw specs new --title x --slug x` (preview) writes to `specs/draft/`, confirming the spec starts in `draft/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Executability (sequencing) | old E-08 "write the content from E-01 to E-07 into it", `Depends on: E-07`; E-01 "record the table in the spec's problem section" | E-01 to E-07 write into a spec that E-08 created last, so the dependency order was inverted; and the `aw check` before/after comparison had no point at which the "before" was captured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split old E-08: new E-08 (first, no deps) captures the `aw check --agent` baseline and creates the spec in `draft/`; E-01/E-02 depend on E-08; new E-10 advances and validates. V-08 and V-10 rewritten to match. |
| PR-002 | MEDIUM | UNDER-SCOPE | Spec trace contract (`89xjll`) | `config.KNOWN_FEATURE_CUTOVERS` "spec_requirement_ids": "2026-10-01"; `89xjll` Sections 3.1, 6.3 | The new spec is post-cutover, so `SPEC-PLAN-TRACE` will check its implementing Set against declared FORM A ids; the plan required none, so TRACE would pass the implementing Set vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-09/V-09: a requirements index of `R-NN` ids and an `AC-NN` section, verified with `production_checks.parse_spec_requirement_ids`; added F-11. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence accuracy (approval authority) | `status_set.validate_transition_allowed` applies `TRANSITION_AUTHORITY` inside `if rec.record_type == "specs"`; `aw ipd set approved e41qgx --dry-run --agent` returned `clean` with no `--by-human` | E-05 and F-6 claimed `->approved` is human-only via `TRANSITION_AUTHORITY`; that table binds specs only, and plan approval is human by convention plus `plan_readiness.approval_refusals`. A spec built on the false premise would claim a gate that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02, E-05, F-6 and V-05 now state the real enforcement and require the spec to say whether the implementing Set must add a mechanical gate. Added F-10 for the setter-side gate. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` "Execution contract:" paragraph | The contract lacked the scope-fence declaration wording (`--scope-reason` / `--scope-ack`, notably for a `draft/` path left unmodified after the setter moves the file), the staged-set check, the `aw specs set --no-commit` interaction with `aw commit`, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten as a full itemized execution contract. |
| PR-005 | MEDIUM | IN-SCOPE | Validation (live counts as bar) | E-01 "151 plans ... 21"; E-02 "96 of 1,161"; re-measured 119 of 1,173 | Authoring-time live counts sat in Expected-outcome-adjacent text without a re-derivation instruction, and the 96/1,161 figure already drifted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, E-02 and V-01 now require the values re-derived at execution and state the authoring numbers are context only. |
| PR-006 | LOW | IN-SCOPE | Evidence accuracy | F-4 "150 of the 151 name no spec in `- Scope-Paths:`"; re-measured 0 name a `.spec.md` | Miscount: the one plan names the specs directory, not a spec file, which is what `k3yx72` 5.2 signal 1 keys on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 corrected. |
| PR-007 | LOW | IN-SCOPE | Evidence precision | E-02 "the post-review path"; `runner_shared.execute_item_core` "if is_plan_review_approved(plan_curr):" | The second `--full-auto` site was unnamed, and it is the one that also rewrites the queue `action` to `execute`, the behavior a quick path would reuse. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names `runner_shared.execute_item_core`; added F-9. |

`aw ipd lint --phase review-finalize --agent`: recorded in the plan history at finalize.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the quick-pipeline spec declare TRACE ids even though no implementing Set exists yet? | Yes, declare `R-NN`/`AC-NN` now, deferring undecided ones | Leave ids to a later spec amendment (TRACE would pass vacuously at production) | `89xjll` Sections 3.1, 6.3; `production_checks.SPEC_REQUIREMENT_IDS_CUTOVER_DATE` | yes |
| D-2 | Is the plan-approval human-only claim a maintainer question for this review? | No; correct the premise and carry the "add a mechanical gate?" choice into the spec's own open questions | Raise a blocking OQ on this plan | The decision affects the implementing Set, not this records-only plan; E-07 already routes maintainer decisions to the spec's `OQ-NN` | yes |
| D-3 | How to sequence spec creation versus content? | Create first (E-08), validate last (E-10) | Keep content-then-create (impossible: no file to write) | `aw specs new` preview writes to `specs/draft/` | yes |

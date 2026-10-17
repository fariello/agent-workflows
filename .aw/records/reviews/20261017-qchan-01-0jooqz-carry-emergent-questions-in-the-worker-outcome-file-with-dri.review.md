# Review findings: plan 0jooqz

- Subject-Id: 0jooqz
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `0bc11ec7b` (which already carries the orchestrator review's A30 edit to this plan's E-05/V-05). The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan, not an orchestrator.

Verified:
- `runner_shared.build_prompt` is the one execute-prompt definition; `oc_runipd.build_prompt` / `agy_runipd.build_prompt` delegate with host labels. The prompt holds "If no reasonable approach exists, record a DEFERRED question with the work completed," and the literal `"deferred_question_ids": []`; `render_stream` is the only other reader of that key.
- `runner_shared.build_review_prompt` returns the bare `/<handler> <path>` when `lane_root is None` and appends `lane_containment.isolation_notice` otherwise; it is called twice in `execute_item_core` (first non-isolated, then rebuilt with `lane_root` after the attempt is appended).
- `execute_item_core` runs `lane_containment.collect_lane_submissions` for a review only when `turn_runs_in_review_sweep_lane`, and that collection copies `<lane>/.aw/state/lane-submissions/.../outcomes/<NN>-<id6>.json` to `<run_dir>/outcomes/<NN>-<id6>.json`.
- `runner_shared.reconcile_disposition` returns `(status, None)` for every review branch: it never reads a review outcome.
- The proposal branch in `execute_item_core` runs `validate_proposal(outcome)` only `if not is_review and not is_production`.
- `runner_shared.read_recorded_outcome` reads a fixed per-position path and nothing deletes it between attempts (only the verification outcome is unlinked).
- `validate_proposal`, `sanitize_front_matter_text`, `ProposalVerdict` exist and are re-exported by both hosts; `runner_shared.ID6_RE` exists.
- Spec `6kwd2e` R2.1-R2.6, R4.1a, A19, A29-A31 read as the plan cites them.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric G (reachability) / C | `runner_shared.reconcile_disposition` review branch `return "reviewed", None`; `execute_item_core` "if not is_review and not is_production: proposal_verdict = validate_proposal(outcome)"; plan E-04 "exposes that question to the driver" | No E-item made the driver read `questions[]` at all, for either action: the review outcome is never read, and "exposes to the driver" named no mechanism or hand-off. Order 02 (`epsti7` E-02) assumed a validated question would be available. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-06: after `reconcile_disposition`, validate this attempt's outcome for execute and review turns and record `attempt["questions_verdict"]`, the explicit hand-off; `epsti7` E-02 now cites it. E-04 narrowed to the prompt carrier. V-06 demands the four cases. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric A (stale state) | `read_recorded_outcome` path `outcomes/{position:02d}-{id6}.json`; no unlink of it between attempts (only `v_outcome_file.unlink`) | A retry or resumed attempt that writes no new outcome would re-read the previous attempt's `questions[]`, re-parking an answered item indefinitely (Order 04 E-04 re-park). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-06 FRESHNESS rule: isolated turns require this attempt's collection receipt to list `outcome`; non-isolated turns compare a pre-launch SHA-256; tested by the stale-retry case. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric B (trust boundary) | spec `6kwd2e` R2.2 "the artifact `id6`"; `mtmqlm` E-01 derives `artifact_path`/`artifact_hash` from the question | `artifact_id6` was worker-authored and only shape-checked, so a worker could attach a question (and later an answer) to a different artifact. Duplicate `question_id`s were also unhandled. | all Low | FIXED | E-01 takes `item_id6`, rejects a mismatch and a duplicate `question_id` with named violations; V-01 demands both. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric F (contradictory instruction) | `build_prompt` "If no reasonable approach exists, record a DEFERRED question with the work completed," | E-03 added the new carrier beside the old prose instruction, leaving the worker two contradictory carriers. | all Low | FIXED | E-03 replaces that sentence; V-03 demands `grep -c` 0. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric G (executability) / D | `build_review_prompt` docstring "A NON-isolated review (`lane_root is None`) returns the byte-identical single line"; `lane_containment.project_worker_paths`, `attempt_key` | E-04 did not say how the review outcome path is derived or that the non-isolated review cannot carry it; a naive edit would break spec `7ckptx` R1.3 or the command-line argv rule. | all Low | FIXED | E-04 now names `project_worker_paths` + `prepare_lane_submission_dir`, lines after the notice only, non-isolated byte-identical; the non-isolated limit is a Carrier-Declined row and in Scope OUT. |
| PR-006 | LOW | IN-SCOPE | Rubric F (silent failure) | plan E-01 "Cap the array at 20 entries." | The cap did not say whether overflow is dropped silently; spec A29 says "A dropped question is an unasked question." | all Low | FIXED | Overflow is a named violation; E-06 surfaces malformed verdicts as an event and a stderr line. |

`aw ipd sync --apply` assigned E-06/V-06; `aw ipd lint --phase review-finalize --agent`: `clean`. Sibling `epsti7` (to-review) E-02 edited to consume `attempt["questions_verdict"]`; its author-phase lint is `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan owns reading `questions[]` in the driver? | This plan (E-06), recording the verdict on the attempt; Order 02 acts on it. | Put intake in `epsti7` (REJECTED: this plan's Goal is "hand the driver a question"; Order 02's Scope is acting on it). | plan Goal; `epsti7` E-02 "when `validate_questions` (Order 01) returns". | yes |
| D-2 | Should a non-isolated review turn get a carrier? | No; declined and documented. | Append prose to the command (REJECTED: absorbed into `$ARGUMENTS`); a second carrier (REJECTED: spec R2.4). | `build_review_prompt` docstring; spec `7ckptx` R1.3; `isolation_for_action` default True. | yes |
| D-3 | How to detect a stale outcome? | Collection receipt for isolated turns; pre-launch SHA-256 for non-isolated. | Delete the outcome before each attempt (REJECTED: other readers such as crash reconciliation consume it). | `collect_lane_submissions` receipt `collected`; `reconcile_interrupted` uses `read_recorded_outcome`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

# Review findings: plan j0ufrj

- Subject-Id: j0ufrj
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `83e14a087`. The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisites `epsti7` and `mtmqlm` are `reviewed` (not yet executed), so `awaiting-human`, `question_inbox` and the parked-branch fields do not exist in code yet; their contracts were read from those plans.

Verified:
- `oc_runipd.run_queue` / `agy_runipd.run_queue` loop top: `runner_stop.poll_stop`, `load_state`, `cascade_dependency_blocked`, `deferred_integration_items` retry, then `queued = [...]` and selection `sorted(queued, key=lambda it: queue_sort_key(it, by_id))` with the first `dependency_status`-satisfied item. Both `start` and `resume` enter `run_queue`.
- `runner_shared.resume_via_launcher` is used only for in-turn follow-ups (defect re-ask, corrections) with the parked attempt's own `plan_path`/`work_dir`; it is not a dispatch path.
- `execute_item_core` resumes a prior session in an adopted lane ONLY on its `is_fix_it_recovery` branch (`session_id = prior_session_id`, `use_continue = False`, `inspect_lane`, `lane_is_safe_to_adopt`, `write_lane_owner`); otherwise it calls `allocate_isolation_worktree`, which cuts a fresh lane at HEAD.
- `runner_shared.resolve_prior_lane` reads `preserved_lane_id`/`preserved_base`/`preserved_branch`.
- Reviews: `acquire_review_sweep_lane`, `REVIEW_SWEEP_SESSION_KEY`, `attempt["review_lane_tip_before"]`; `refresh_sweep_lane` is `--ff-only` and refuses on a dirty lane.
- `build_fix_it_notice`, `_redact_absolute_paths`, `sha256_file`, `queue_artifact_path` exist.
- Spec `6kwd2e` R5.5, R5.6, R6.2, R6.3, R9.3, R9.4, R9.4a, A6, A12, A36, A37, A43, A44 read as cited.
- `epsti7` E-06 and `mtmqlm` E-01/E-03/E-05 define the parked branch, qid format (`-a<attempt>-`), stored qids and `set_question_status`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (resume mechanism) | `runner_shared.resume_via_launcher` docstring "follow-up turn"; `execute_item_core` `is_fix_it_recovery` branch, `allocate_isolation_worktree` | E-03 said "resume ... through `resume_via_launcher` on its preserved lane", but a re-queued item is dispatched through `execute_item_core`, which would allocate a FRESH lane at HEAD (dropping the parked commit, A6) and start a new session. `resume_via_launcher` is an in-turn helper and would skip begin, verification, finalize and integration. The plan did not say where the resume hooks in. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 adds a `resume_with_answers` branch beside `is_fix_it_recovery`: lane from `resolve_prior_lane`, the same adoption checks, recorded session via the executor launcher, `answer_resume` recorded; spec-sync note explains the R9.4 mechanism wording (D-2). |
| PR-002 | HIGH | UNDER-SCOPE | Correctness (review resume) / right-sizing | `epsti7` E-06 "Order 04 (`j0ufrj` E-03) resumes a parked REVIEW from `preserved_branch`"; `refresh_sweep_lane` "`--ff-only`" | Review resume was a sentence inside E-03 offering "fast-forward or merge". A fast-forward is impossible once any later review committed on the sweep lane (demonstrated), conflict handling, the order relative to `review_lane_tip_before`, session semantics and parked-branch deletion on a deferred integration were unstated. A separate code region and test surface. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-06 (merge `--no-ff` before `review_lane_tip_before` is recorded, abort + `fail-merge` on conflict, branch deleted only after integration, sweep session) with V-06. |
| PR-003 | HIGH | IN-SCOPE | Correctness (data loss on fallback) | spec A6 "resumes on the SAME lane, with the commit still present"; `allocate_isolation_worktree` | No behavior was specified when the preserved lane is gone or unsafe to adopt; the default code path would allocate a fresh lane and silently lose the parked work. | all Low | FIXED | E-03 refuses (`answer-resume-refused`, `fail-lane`, lane untouched) and never allocates a fresh lane; tested in E-05, evidenced in V-03. |
| PR-004 | MEDIUM | IN-SCOPE | Correctness (re-park accounting) | `mtmqlm` E-01 qid `-a<attempt>-`; plan E-01 "for each `awaiting-human` item, read its answers" | After a re-park the item's earlier answered questions would satisfy "every gating question answered", re-queueing it immediately with no new answer. | all Low | FIXED | E-01 reads only the current park's qids; E-04 replaces the qid list on re-park; V-04 demands the next checkpoint does not consume. |
| PR-005 | MEDIUM | IN-SCOPE | Executability (placement, priority, events) | `oc_runipd.run_queue` loop top; selection `queue_sort_key` | E-01 named events in V-01 (`answer-consumed`, `answer-stale`) that no E-item emitted, placed the call vaguely and added a redundant pre-loop call; E-02 did not say how priority composes with `queue_sort_key`. Missing artifact and inbox read errors were unhandled. | all Low | FIXED | E-01 names the events, places one call before the cascade (covers start/resume drain), treats a missing artifact as stale, never raises; E-02 specifies the key and a shared helper. |
| PR-006 | MEDIUM | IN-SCOPE | Security (untrusted text in prompt) | spec R9.4; `mtmqlm` E-02 bounds answer text "because the answer is later pasted into an agent prompt" | The notice embeds human/chat-supplied text in an agent prompt with no framing or redaction stated. | all Low | FIXED | `build_answer_notice` fences each answer as quoted human input and redacts absolute paths. |
| PR-007 | LOW | IN-SCOPE | Process (attribution, validation) | plan OQ-01 `Owner: maintainer`; Required tests `-q` | OQ-01 was decided at authoring yet labelled `Owner: maintainer`; the validation command passed `-q`, which AGENTS.md says hides the `N passed` line V-05 demands. | all Low | FIXED | Owner corrected and recorded as D-1; command drops `-q` and adds `tests/test_question_inbox.py`. |

`aw ipd sync --apply` assigned E-06/V-06. `aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Resume when only some questions are answered? (OQ-01, author's own decision) | Only when every gating question is answered. | Resume on any answer (REJECTED: the turn would re-park immediately and waste a turn). | spec R9.4 "an answer costs a short turn"; `mtmqlm` `gates_verdict`. | yes |
| D-2 | Which launcher path resumes the session? | The executor launcher with the recorded session id, inside `execute_item_core`, beside `is_fix_it_recovery`. | Call `resume_via_launcher` at dispatch (REJECTED: skips begin, verification, finalize and integration; it is an in-turn helper). | `runner_shared.resume_via_launcher` docstring; `execute_item_core` `is_fix_it_recovery` branch. | yes |
| D-3 | Fast-forward or merge the parked review branch? | `git merge --no-ff`, abort on conflict. | `--ff-only` (REJECTED: scratch repo, base -> parked commit on `aw/parked/run-x/abc123`, sweep reset, later review commit, then `git merge --ff-only` printed `fatal: Not possible to fast-forward, aborting.`; `merge --no-ff` produced a merge holding both commits, and a conflicting merge exited 1 and `merge --abort` restored the tip with a clean status). Cherry-pick (REJECTED: rewrites commit ids the run record names). | scratch-repo demonstration at review. | yes |
| D-4 | What happens when the preserved lane is gone? | Refuse with `fail-lane`, never allocate fresh. | Fresh lane at HEAD (REJECTED: silently drops parked work, violates A6). | spec A6; `allocate_isolation_worktree`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.

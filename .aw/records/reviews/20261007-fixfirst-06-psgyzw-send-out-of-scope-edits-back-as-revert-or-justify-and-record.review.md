# Review findings: plan psgyzw

- Subject-Id: psgyzw
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `6d5fe7c13`. The plan was committed and byte-identical to the sealed lane
input (sha256 `6f53cf9c...`), so there was no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before
review; `--phase review-finalize`: `clean` after revision. Not an orchestrator.

Verified: `runner_shared.compute_scope_reconciliation` writes "changed by the plan's approved execution (auto-reconciled
by ...)" for every out-of-scope path; `driver_finalize` passes each as `--scope-reason`; `ipd_lifecycle.finalize` merges
`read_scope_reasons` with flag reasons (`effective_scope_reasons = {**receipt_reasons, **(scope_reasons or {})}`);
`work_cmd.run_commit` records reasons only on `STATUS_COMMITTED`; `ipd_lifecycle.begin` writes a fresh receipt dict;
`ipd_schema.META_FROM_SPEC` exists; spec Section 4.4 "Recognized-but-optional fields" sentence exists; finalize mutates
the plan in `coordinator_worktree` after `status_set.apply_status_change`.

Scratch-repo demonstrations (real CLI, in the lane's gitignored `.aw/state/`):

```text
TODAY compute_scope_reconciliation reasons: {'OTHER.txt': "changed by the plan's approved execution (auto-reconciled by aw oc run)"}
aw commit on already-committed path: rc= 1 | aw commit: nothing to commit (nothing to commit: requested path(s) have no staged changes (OTHER.txt))
receipt reasons after: {}
recorded: {'OTHER.txt': 'needed for demo', 'OTHER2.txt': 'why2'}
re-begin: 0
reasons after re-begin: {}
parsed: {'A.txt': 'ok\n- Readiness: go'}
no reason: 1 | finalize needs scope reconciliation answers (plan left unmoved). | ('out-of-scope path needs a --scope-reason: OTHER.txt',)
agent reason: 0 | precheck + reconciliation passed; re-run with --apply to perform the terminal transaction.
```

`aw ipd lint` on an executed plan with `- Scope-Exceeded:` added: `IPD-M103`. `aw find plans "From-Spec: 25kzda"` and
`aw find plans Scope-Exceeded` both return nothing: `aw find` does not search metadata values.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric G (reachability) | `work_cmd.run_commit` `if outcome.status == _gch.STATUS_COMMITTED: ... record_scope_reasons`; demo `rc= 1 ... nothing to commit` | E-02's remedy `aw commit <plan> --scope-reason <path>=<why> -- <path>` cannot record a reason for an already-committed path, which is the normal case at finalize, so the fix-it turn could only ever succeed by revert or by a gratuitous edit. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | New E-06/V-06: recording-only form, refusing a path not in the current out-of-scope set. OQ-02, D-1. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric A (state across retries) | `execute_item_core` calls `driver_begin` each attempt; `ipd_lifecycle.begin` fresh `receipt` dict; demo `reasons after re-begin: {}` | Any reason recorded during the fix-it turn's predecessor, and any recorded before the refusal, is dropped by the recovery turn's begin, so the loop could not converge. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07/V-07: carry `scope_justifications` and its audit forward when a receipt exists. D-2. |
| PR-003 | HIGH | IN-SCOPE | Rubric D (anti-regression) | `ipd_lifecycle.finalize` "finalize needs scope reconciliation answers (plan left unmoved)"; `tests/test_finalize_sendback.py` `SCOPE_REFUSAL`, `test_a_scope_reconciliation_refusal_is_NOT_retryable` | E-02 changes behavior a shipped test pins, the test is not in Scope-Paths, and its fixture text is not what finalize emits, so an arm written against the fixture would never match production. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the real summary/finding text, requires all findings to be out-of-scope lines (mixed stays non-retryable), and names the test update; test added to Scope-Paths. |
| PR-004 | MEDIUM | IN-SCOPE | Security lens (untrusted input into metadata) | demo `parsed: {'A.txt': 'ok\n- Readiness: go'}` | An agent-written reason with a newline would inject a metadata line such as `- Readiness:` into the executed plan's front matter, which gates read. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 sanitizes (single line, delimiter strip, 200-char bound); E-05 case (d) tests it. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric D | `record_item_spec_edits(... reconcile=lambda r, p: compute_scope_reconciliation(...))`; `spec_edit_record` reads `reasons` keys as `modified_not_declared` | Removing auto-reasons would silently drop an unjustified out-of-scope spec from the end-of-run declared-spec-edit report (AGENTS.md requires that report to name undeclared spec edits). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 passes the union of justified and unjustified out-of-scope paths to that report; V-01 checks it. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric G (evidence feasibility) | `IPD-M103` on a plan with the field; `aw find plans "From-Spec: 25kzda"` returns nothing | E-05 demanded `aw find plans` locate a plan by the field, which no code path does; the Deferred note claimed existing verbs can filter on metadata. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Demand replaced by lint and metadata checks; Deferred note corrected. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric D | `tests/test_oc_runipd.py` `test_compute_scope_reconciliation_handles_out_of_scope_and_unmodified` asserts `"OTHER.txt" in reasons` | E-01 breaks this assertion; the test was not in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names the update; test added to Scope-Paths. |
| PR-008 | LOW | IN-SCOPE | Rubric C (placement) | `_finalize_transaction` coordinator worktree, rollup insertion after `apply_status_change` | E-03 did not say where the metadata write happens; writing it in the shared tree would reopen the mid-move window `u23gbn` closed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 places it beside the rollup insertion. |
| PR-009 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Original gate | Dependency reason, staged-set check, scope-fence wording and conditional finalize were missing; no budget-0 case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Execution contract added; E-05 case (g). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does an agent justify an already-committed out-of-scope path? | Recording-only `aw commit --scope-reason` that commits nothing and refuses paths not in the current out-of-scope set | Tell the agent to edit the path again (gratuitous churn); let the agent pass the reason in its outcome file (untrusted, unrecorded in the receipt); keep the runner's boilerplate (contradicts F-04) | `ipd_lifecycle.finalize` already merges receipt reasons; demo `agent reason: 0` | yes |
| D-2 | Should re-`begin` keep recorded reasons? | Carry them forward when a receipt exists | Re-record on each turn (agent must repeat itself); switch the driver to `refreeze_receipt` (keeps base_head but changes the dispatch path for every recovery, out of this plan's concern) | `ipd_lifecycle.record_scope_reasons` says reasons are additive and `base_head` untouched | yes |
| D-3 | Should `Scope-Exceeded` include widened paths? | No, out-of-scope only | Include widened (they were declared, so they did not exceed scope) | Plan Scope "KEEP the additive-widening reasons ... both describe declared paths" | yes |

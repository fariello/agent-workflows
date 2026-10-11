# Review findings: plan 62sdwr

- Subject-Id: 62sdwr
- Subject-Type: ipd
- Reviewed-At: 2026-10-11
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-900 (HIGH, fixed), PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (HIGH, fixed), PR-906 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2284049fa`. The plan was committed and byte-identical to the lane input
(sha256 prefix `1780383476875fb7`), so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported
`clean` before review, and `--phase review-finalize --agent` reports `clean` after it. `- Kind: child`, so S407/S408 do
not apply. Dependency `mcbph5` is executed, and `runner_shared.build_fix_it_notice` exists.

Evidence re-checked: `check_engine.check_status_untooled` (compares `:0:` against `HEAD`), `_has_matching_history_line`,
`runner_shared.outcome_precedence_disposition` ("A plan in `executed/` is `executed`"; `RETIRED_PLAN_BUCKETS`),
`runner_shared.finalize_already_done` -> `ipd_lifecycle.plan_already_finalized` (bucket, with the finalize commit as
corroboration only), `ipd_lifecycle._clear_finalize_journal` on the COMPLETE path, `hooks/executed_transition_gate.py`
(the journal "cannot travel with a lane branch", plus the merge-time `lifecycle(<id6>): finalize` path),
`.pre-commit-config.yaml` (`ipd-executed-transition-gate` and `ipd-status-untooled-gate` are `pass_filenames: false`,
`always_run: true`), the `RUN-COMMIT-GATEWAY` row in `run_evidence`, and spec `25kzda` 5.5 rows "an unauthorized status
change or plan move" and "a hook-bypass commit".

Measured at review in a scratch repo under `.aw/state/` (removed afterwards). The repo had a content hook refusing
`BAD`, a staged-index gate shaped like `ipd-executed-gate`, and a mutating fixer:

```text
== plan's mechanism in the lane: pre-commit run --from-ref B --to-ref H
refuse BAD ... Failed / REFUSED x.txt
staged-index gate ... Passed                <- range added z.txt, which the gate refuses
== alternative: disposable worktree at B with the B..H delta staged
refuse BAD ... Failed / REFUSED x.txt
staged-index gate ... Failed / STAGED-z-SEEN
lane status: []
== per-commit form for the BAD commit C, run in lane with HEAD past the fix
refuse BAD ... Passed                       <- yet: C's own x.txt: BAD
== mutating hook run in the lane
lane status after: [ M .pre-commit-config.yaml ]
```

Also measured: `aw ipd set superseded 62sdwr --dry-run` -> `to-review -> superseded (dry-run)`. A tooled retirement
therefore exists and writes a history line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-900 | HIGH | IN-SCOPE | Correctness of the detector (E-03) | Scratch measurement above; `.pre-commit-config.yaml` gates `pass_filenames: false`, `always_run: true` | The `pre-commit run --from-ref/--to-ref` form in the lane checks the working tree, not the commit's content. It passes a bad commit once a later commit fixes it, never triggers the staged-index gates (so a `--no-verify` move into `executed/` passes), and lets mutating hooks rewrite the lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now runs one pass over the lane's net change, staged in a disposable detached worktree. The lane is left untouched, and an unbuildable or offline hook environment counts as "unavailable", not a refusal. Expected outcome and V-03 now require proof that the lane is unchanged and that the move case is caught. F-05 added. |
| PR-901 | HIGH | IN-SCOPE | Evidence choice (E-01) | `ipd_lifecycle._clear_finalize_journal` on COMPLETE; `.aw/state/` gitignored; `executed_transition_gate` docstring | E-01 required a "finalize journal" for `executed`. That journal is deleted once finalize completes and never travels with a lane, so it cannot serve as evidence afterwards. | Overall:Low | FIXED | Evidence is now a commit whose subject starts with `artifact_core.finalize_commit_subject(<id6>)` and lies within the range (the hook's own merge-time path). Under `self_finalize` every in-lane `executed` arrival is correctly untooled. F-06 added. |
| PR-902 | HIGH | UNDER-SCOPE | Anti-regression | `tests/test_inlane_retirement_lands.py` (hand `git mv` to `superseded/`, expects `RETIRED_STATUS`); `outcome_precedence_disposition` `RETIRED_PLAN_BUCKETS` | Removing trust in the directory alone would reclassify the in-lane retirement path, which a shipped test pins as success, and the plan did not mention it. | Overall:Low | FIXED | E-01 and E-02 now distinguish a tooled retirement (`aw ipd set superseded`) from a hand retirement. The test is declared in Scope-Paths and is to be updated. V-01 and V-02 require both cases. |
| PR-903 | MEDIUM | IN-SCOPE | Correctness of the fix-it text | `ipd_lifecycle._refuse_worker_role_verb` (`AW-LIFECYCLE-ROLE-001`); `runner_owns_lifecycle_notice` "Do NOT run them yourself" | The prescribed instruction "(or `aw ipd finalize`)" tells a managed worker to run a verb that is refused, contradicting its own prompt. | Overall:Low | FIXED | The instruction now says to leave `executed` plans in `pending/` for the runner. V-02 and E-05 assert the text never says to run `aw ipd finalize`. |
| PR-904 | MEDIUM | IN-SCOPE | Architecture | `outcome_precedence_disposition` callers (`reconcile_disposition`, the crash path, `run_viewer`); `finalize_outcome` -> `finalize_already_done` (`ld8lb3` idempotence) | "Make [both helpers] require tooled evidence" would change two pure, multi-caller helpers, one of which is the double-finalize idempotence fix, with no stated mechanism. | Overall:Low | FIXED | The check now runs in the execute path, before `reconcile_disposition` and `driver_finalize`. Both helpers stay unchanged for every other caller. An optional keyword is the fallback if a caller turns out not to be covered. |
| PR-905 | HIGH | IN-SCOPE | Honest binding; anti-regression | `RUN-COMMIT-GATEWAY` pass criterion (argv, no `--no-verify`); `run_evidence` "binding these two now would be exactly the fail-open error"; `CommitGatewayClaimConsistencyTests` Leg 2; `test_ipd_exec_finding_codes` `bound_run_finding_codes()) == 10` | Binding the code to a content re-run would claim more than the predicate can decide (the plan's own Scope check concedes a bypass with passing content is invisible). It would also turn two shipped tests red, and neither is declared in scope. | Overall:Low | FIXED | E-04 now keeps the code unbound and records E-03 as a partial detector in `waiting_on`. The two tests are added to Scope-Paths. OQ-02 is added and resolved, with the conditional spec edit noted. F-07 added. |
| PR-906 | LOW | UNDER-SCOPE | Execution contract; coverage | The gate had no lifecycle-transition ownership, scope-fence wording or dependency note. E-05 covered one host only. `- Owner: none` on OQ-01. | Gate incomplete; the sibling `_HOSTS` pattern was not required. | Overall:Low | FIXED | Gate completed (runner owns finalize; never hand-`git mv`; `--scope-reason` rather than stopping). E-05 now covers both hosts and runs offline. OQ-01 owner and resolution updated to the single-pass design. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the runner re-run hooks over lane work? | One pass over the net change since `lane_starting_head`, staged in a disposable detached worktree. | (a) The plan's per-commit `--from-ref/--to-ref` in the lane: rejected, measured to check the wrong content, skip the staged gates and mutate the lane. (b) Per-commit in disposable worktrees: rejected, it flags a bypass commit the agent already fixed, which integration never merges. | Scratch measurement; `.pre-commit-config.yaml`. | yes |
| D-2 | What evidence proves an `executed` arrival was tooled? | A `lifecycle(<id6>): finalize` commit within the range. | The finalize journal: rejected, deleted on completion and gitignored. | `_clear_finalize_journal`; `executed_transition_gate` docstring. | yes |
| D-3 | Bind `RUN-COMMIT-GATEWAY`? | No; record a partial detector (OQ-02). | Bind it as the plan said: rejected as fail-open and test-breaking. | `run_evidence` row and comment; two pinning tests. | yes |
| D-4 | Where does the directory-alone fix live? | A gate in the execute path; both helpers unchanged. | Change the helpers' semantics: rejected, they have other callers, and one is the `ld8lb3` fix. | Caller census by grep. | yes |

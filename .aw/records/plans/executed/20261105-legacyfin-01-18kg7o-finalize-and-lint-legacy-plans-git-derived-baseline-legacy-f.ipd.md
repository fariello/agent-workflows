# IPD: Finalize and lint legacy plans: git-derived baseline, legacy-format check, --without-receipt

- Date: 2026-11-05
- Kind: child
- Concern: A plan migrated from a pre-receipt, pre-current-format repo (`aw migrate-layout`) can be listed but never finalized: `aw ipd finalize` refuses without a begin receipt that could not have existed, and the pre-execution/pre-transition lint refuses fields and headings the format did not have when the plan was written.
- Scope: Two repo-stamped cutovers (`ipd_begin_receipt`, `ipd_plan_format`), a shared legacy predicate, a git-derived finalize baseline for pre-cutover plans, a reasoned `--without-receipt` bypass for post-cutover plans, a reduced lint for pre-cutover pending plans, a no-receipt warning in `aw commit`/`aw test`, cutover stamping in `aw migrate-layout`, and the spec amendment.
- Scope-Paths: agent_workflows/config.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/work_cmd.py, agent_workflows/layout_migration.py, tests/test_legacy_finalize.py, tests/test_config.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Scope-Exceeded: tests/test_migrate_layout_cli.py (E-02 cutover stamping is exercised through the existing migrate-layout CLI test class)
- Item-Dependencies: none
- Status: executed
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: legacyfin
- Order: 1
- Highest E allocated: 08
- Readiness: go
- Review-Depth: standard
- Author: opencode/claude-opus
- Id: 18kg7o

## Workflow history
- 2026-11-06 executed (opencode/claude-opus): executed: legacy plans finish through the normal finalize (git-derived baseline, NOTICE, history), --without-receipt REASON after the cutover, reduced legacy-format lint, migrate-layout stamps cutovers; core 1859 passed, non-slow 10469 passed [Scope reconciliation - out-of-scope tests/test_migrate_layout_cli.py: E-02 cutover stamping is exercised through the existing migrate-layout CLI test class; in-scope-unmodified tests/test_config.py: predicate tests live in tests/test_legacy_finalize.py]
- 2026-11-06 approved (opencode/claude-opus, --by-human): maintainer approved in chat 2026-11-05: 'Yes' to build the recommended design
- 2026-11-06 reviewed (opencode/claude-opus): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-11-05 /plan-review (opencode/claude-opus): APPROVE WITH REVISIONS APPLIED; R-1, R-2 fixed in place (standard tier: references, executability, security, engineering).
- 2026-11-05 to-review (opencode/claude-opus): authored to the design the maintainer accepted in chat on 2026-11-05.

## Goal

Let a plan that predates the begin receipt or the current plan format reach `executed/` through the normal `aw ipd finalize` / `aw ipd set executed` commands, with the deviation printed and permanently recorded, while a plan that skipped an available step still has to say why.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: cutovers and the shared predicate

- [x] E-01 Register `ipd_begin_receipt` (2026-08-24, introduced by `94f36a10b`) and `ipd_plan_format` (2026-10-08, the date `IPD-M113` made `Readiness` required) in `config.KNOWN_FEATURE_CUTOVERS`, and add `config.plan_predates_cutover(repo_root, feature, date)` returning True only when the repo resolves a cutover and `date` is strictly earlier.
  - Depends on: none
  - Expected outcome: `resolve_cutover_date` returns the stamped value for both features; the predicate is False when no cutover resolves (fail closed).
  - Execution state: performed
- [x] E-02 Stamp both cutovers from `aw migrate-layout` after a successful move, by calling `config.sync_cutovers_on_install` against the migrated repo (creating `project.json` cutovers only when absent, never overwriting an existing date).
  - Depends on: E-01
  - Expected outcome: a freshly migrated repo carries `cutovers.ipd_begin_receipt` and `cutovers.ipd_plan_format` dated today, so every pre-existing plan reads as legacy.
  - Execution state: performed

### Task group 2: finalize without a receipt

- [x] E-03 Add `ipd_lifecycle.derive_baseline(repo_root, plan_path)`: the oldest commit, following renames, whose version of the plan carries `- Status: approved` (or the adding commit when the plan was born approved). Returns `(sha, commit_date, plan_text_at_sha)` or None.
  - Depends on: none
  - Expected outcome: for a plan approved in commit A and edited after, returns A and A's plan text; through a `git mv` rename it still finds A.
  - Execution state: performed
- [x] E-04 In `finalize_precheck`, when no receipt exists and the plan is not already finalized, build an in-memory receipt from `derive_baseline` (never written to disk) when EITHER the plan's approval date predates `ipd_begin_receipt` OR the caller passed `without_receipt=<reason>`; accept `base=<commit>` to override the derived commit. Record `evidence["receipt_source"]` as `git-derived-legacy` or `without-receipt`, plus the base sha. Post-cutover with no flag keeps the existing refusal, now naming `--without-receipt`. A baseline git cannot find refuses and names `--without-receipt REASON --base COMMIT`.
  - Depends on: E-01, E-03
  - Expected outcome: a legacy plan passes precheck with a git-derived base; a post-cutover plan refuses unless the reasoned flag is given; scope audit runs from the base either way.
  - Execution state: performed
- [x] E-05 Thread `without_receipt` and `base` through `finalize()`, `run_finalize`, `status_set._delegate_plan_executed_to_finalize`, and the `aw ipd finalize`, `aw ipd set` and `aw set` parsers (`--without-receipt REASON`, `--base COMMIT`; an empty reason is refused). Append a history note naming the source, the base commit and (if given) the reason; print a NOTICE line in human output and carry it as a warning diagnostic in agent/JSON output.
  - Depends on: E-04
  - Expected outcome: `aw ipd finalize <legacy> --actor A -m M --apply` moves the plan to executed/ and its history entry names the git-derived base; the same command on a post-cutover plan refuses until `--without-receipt "<why>"` is added.
  - Execution state: performed
- [x] E-06 Warn on stderr in `aw commit <plan>` and `aw test <id6>` when the plan is `approved`, is NOT legacy for `ipd_begin_receipt`, and has no begin receipt: "no begin receipt for <id6>; run `aw ipd begin <id6> --actor <you>` before executing, or finalize will require --without-receipt". Never changes the exit code.
  - Depends on: E-01
  - Expected outcome: the warning appears for a post-cutover receiptless plan and does not appear for a legacy plan or one with a receipt.
  - Execution state: performed

### Task group 3: legacy plan format

- [x] E-07 In `ipd_lint.lint_file`, for a plan in a non-terminal directory whose `- Date:` predates the repo's `ipd_plan_format` cutover, at checkpoints `pre-execution` and `pre-transition`, apply the reduced check: keep the Id, Status and checkpoint state rules (every present E `performed`, every present V `pass` with evidence at pre-transition) and the scope/dependency rules, and drop the format-only codes (`IPD-M101` for fields other than `Id`/`Status`, `IPD-M104` Approval-required, `IPD-M113`, `IPD-H201`..`IPD-H205`, `IPD-I301`..`IPD-I304`, `IPD-M106`/`M110`/`M111`, `IPD-Z60*`, `IPD-N001`). Report one advisory `IPD-L001` naming the format cutover so the downgrade is visible. A post-cutover plan is unaffected.
  - Depends on: E-01
  - Expected outcome: a pre-cutover pending plan with only `Date`/`Status`/`Id` lints conforming (with the `IPD-L001` advisory) at pre-transition; the same text dated after the cutover still reports `IPD-M101`/`IPD-H202`.
  - Execution state: performed

### Task group 4: contract

- [x] E-08 Amend the IPD structure spec Section 11 (begin receipt) and Section 13 (rollout and legacy behavior) to state the two cutovers, the git-derived baseline and its stated limit, the reasoned `--without-receipt` bypass, and the reduced legacy-pending check; append a dated workflow-history note citing this plan.
  - Depends on: E-04, E-07
  - Expected outcome: the spec describes the behavior the code now has.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cutovers: `config.KNOWN_FEATURE_CUTOVERS` holds FEATURE INTRODUCTION dates; `config.sync_cutovers_on_install` stamps the per-repo boundary; `config.resolve_cutover_date` reads it and fails open to None. A missing cutover must therefore make the legacy predicate False (fail closed), the same direction as `check_engine._spec_requires_id6`.
- The begin receipt is a pure function of plan text plus a base sha (`ipd_lifecycle.begin`, the `receipt: Dict[str, Any] = {` literal); `finalize_precheck` reads `frozen_region_digest`, `scope_paths`, `base_head`, `pre_execution` from it; `_complete_after_commit` unlinks it with `except OSError: pass`, so an in-memory receipt never written is safe.
- Reasoned bypass precedent: `--take-over REASON`, `--allow-uncovered-orchestrator-work '<why>'`.
- History notes are folded into the finalize message as `message = f"{message} [{note}]"` (`_reconciliation_history_note` pattern).
- Tests style: `tests/test_ipd_lifecycle_cli.py` helpers `_init_git`, `_commit_all`, `_completed_plan_text`, `_write_plan`, and `support.declare_execution_role`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | Finalize refuses every receiptless plan, including ones approved before begin receipts existed. | `finalize_precheck`: "no begin receipt for {plan_id}: run `aw ipd begin` first". |
| F-2 | No cutover distinguishes legacy from current plans for the receipt or the format. | `KNOWN_FEATURE_CUTOVERS` has no such entry. |
| F-3 | The terminal-directory legacy branch exempts executed plans but nothing exempts a legacy pending plan. | `lint_text`: `_is_terminal_dir(directory)` -> `DISPOSITION_LEGACY`. |
| F-4 | Nothing warns at the moment begin is skipped. | `work_cmd.run_commit` / `run_test` read no receipt. |
| R-1 | (review) The reduced check must keep `IPD-M104` for an invalid `Status` value; only the Approval-required clause is format-only. A legacy plan with a malformed Status still refuses, with the existing message. | `ipd_schema.validate_metadata`. |
| R-2 | (review) A legacy plan with zero E/V leaves passes the reduced pre-transition check vacuously. Accepted and stated in the spec as a limit: the reduced check proves recorded state, not that work was itemized. | `check_checkpoint` iterates present leaves only. |

## Proposed changes (ordered, validatable)

E-01 to E-08 in order; each is independently testable through the commands named in its expected outcome.

## Deferred / out of scope (with reason)

- Writing `Author`, `Readiness` or other derived fields into legacy plans: rejected (a derived author may be wrong, a tool-written readiness is a forged attestation, and the reduced check does not need them).
  - Carrier-Declined: design decision, not a defect; rejected by the maintainer in chat 2026-11-05.
- `aw how <keyword>` discovery verb: separate concern, not needed for this fix.
  - Carrier-Declined: an optional enhancement mentioned in chat, not a defect; the maintainer did not ask for it.

## Scope check

- Over-scope: none.
- Under-scope: none; runner callers of `finalize_precheck` (`runner_shared`) keep the default (no flag), so a runner gets the legacy path automatically and still refuses a post-cutover receiptless plan.

## Required tests / validation

New `tests/test_legacy_finalize.py` drives `finalize`, `aw ipd finalize`, `aw ipd set executed`, `aw commit`, and `lint_file` against real temporary git repos; `tests/test_config.py` covers the predicate. The routine core gate and the affected lifecycle files run green.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Sections 11 and 13 (declared in Scope-Paths) because the finalize gate and the legacy rules are the contract every other plan is reviewed against.

## Open questions

### OQ-01: Which date decides "legacy" for the receipt?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: the date of the commit that approved the plan (the receipt is created at execution start, which follows approval); falls back to the plan's `- Date:` when no approval commit is found.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing the predicate True before the cutover, False on/after it, and False with no cutover.
  - Observed evidence: pytest -v tests/test_legacy_finalize.py: `PredicateTests::test_strictly_before_cutover_is_legacy PASSED`, `PredicateTests::test_no_cutover_or_no_date_fails_closed PASSED` (True for 2026-08-23 and an ISO timestamp, False for 2026-08-24/20260901, False with no cutover, no date, or garbage).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `project.json` cutovers after a test migration showing both keys.
  - Observed evidence: pytest -v: `test_migrate_layout_cli.py::...::test_migration_stamps_legacy_cutovers_and_keeps_policy PASSED` (asserts both keys in project.json cutovers, records_backend preserved, project.json tracked) and `test_rollback_removes_created_project_json PASSED`. Scratch repo run: project.json cutovers showed `"ipd_begin_receipt": "2026-11-06"`, `"ipd_plan_format": "2026-11-06"`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: test output showing the derived base equals the approval commit, including through a rename.
  - Observed evidence: pytest -v: `DeriveBaselineTests::test_finds_approval_commit_through_rename_and_edit PASSED` (draft -> approve -> git mv + edit; derived sha == approval commit), `test_none_when_never_approved PASSED`. Found during execution: `git log --follow` missed the migrate-layout rename, so the walk traces renames by hand.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: test output: legacy plan precheck exit 0 with `receipt_source=git-derived-legacy`; post-cutover exit 1 naming `--without-receipt`; with the flag exit 0.
  - Observed evidence: pytest -v: `PostCutoverFinalizeTests::test_refuses_and_names_the_flag PASSED` (exit 1, names --without-receipt and `aw ipd begin nw0001`), `test_reasoned_flag_finalizes_and_records_reason PASSED`, `test_scope_check_still_runs_without_receipt PASSED` (exit 1 demanding `--scope-ack src/a.py`), `LegacyFinalizeTests::test_plain_finalize_moves_plan_and_records_baseline PASSED`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: CLI test output showing the plan in executed/ with a history entry naming the base commit, the NOTICE line, and an empty reason refused.
  - Observed evidence: pytest -v: `test_plain_finalize_moves_plan_and_records_baseline PASSED` (plan in executed/, history contains `approval commit <sha12>`, stderr NOTICE, no receipt file written), `test_set_executed_takes_same_route PASSED`, `test_empty_reason_refused PASSED` (exit 2, 'non-empty reason'). Scratch repo: `finalized maipzk -> executed at 3d2b90816891 (actor t).` with history `[no begin receipt (plan predates begin receipts in this repo); baseline derived from git: approval commit 141ee5efa79d]`.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: test output showing the stderr warning present for the post-cutover case and absent for the legacy case.
  - Observed evidence: pytest -v: `PostCutoverFinalizeTests::test_commit_warns_that_begin_was_skipped PASSED` (stderr contains 'no begin receipt for nw0001'), `LegacyCommitDoesNotWarnTests::test_no_warning_for_legacy_plan PASSED`.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: test output: pre-cutover minimal plan conforming with `IPD-L001`; post-cutover same text non-conforming.
  - Observed evidence: pytest -v: `LegacyFormatLintTests::test_pre_cutover_minimal_plan_conforms_with_advisory PASSED` (conforming + IPD-L001), `test_post_cutover_same_text_still_refused PASSED` (IPD-M101 and IPD-H202 present), `test_legacy_keeps_state_and_identity_rules PASSED`, `test_author_checkpoint_is_not_downgraded PASSED`. Post-transition was added to the checkpoints after a scratch-repo finalize went committed-incomplete on IPD-H202.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: diff of the spec Sections 11/13 and its history note.
  - Observed evidence: `git show --stat HEAD -- .aw/records/specs`: `20260802-1904-01-ipd-structure-and-linting.spec.md | 15 +++` adding the Section 11 paragraph `FINALIZING WITHOUT A RECEIPT (legacyfin 18kg7o)`, `### 13.2a Legacy-format nonterminal plans`, and history note `2026-11-05 note (aw specs): Sections 11 and 13.2a amended (legacyfin 18kg7o E-08)`; `aw specs check`: `all specs conform. 1 specs checked.`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (finishing legacy plans), split across the finalize gate and the lint gate that both block it.

Execution contract: execute only after human approval is recorded with `aw ipd set approved --by-human`. Execute in the isolated worktree `.aw/worktrees/migfix`. The scope fence is the Scope-Paths list; an out-of-scope edit is made and then justified at finalize with `--scope-reason`. Paste the ACTUAL test runner output into each V item; never claim a pass that was not run. Commit path-scoped through `aw commit 18kg7o -- <paths>`; never push. The lifecycle move to executed/ is performed by `aw ipd finalize` (by the executor when run by hand, by the runner when run under `aw oc run`).

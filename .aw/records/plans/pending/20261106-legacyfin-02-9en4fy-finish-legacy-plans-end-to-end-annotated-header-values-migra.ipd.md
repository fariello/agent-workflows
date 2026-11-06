# IPD: Finish legacy plans end to end: annotated header values, migration renames, index warnings, bold Id anchors, migration commit counts

- Date: 2026-11-06
- Kind: child
- Concern: Finishing ONE approved legacy plan in a migrated pre-cutover repository (field report from a migrated private target repository, versions 1.1.1.dev12572 to dev12607) still needed a 34-error hand rewrite, a hand-written Readiness, `--base`, and 928 `--scope-reason` arguments, and finalize then reported COMMITTED-INCOMPLETE over an unrelated plan.
- Scope: Reduced legacy lint reads annotated `Status`/`Date` values; the git-derived baseline accepts an annotated approval; finalize rewrites an annotated status without duplicating it; a no-cutover advisory/hint; pure layout-migration renames excused from the finalize scope audit; index findings on other plans become finalize warnings; Id backfill anchors on bold field names; the migrate-layout commit subject counts what the commit changes; the IPD-C801 message and scaffold line stop citing a spec target repos do not have; spec Section 13.2a amended.
- Scope-Paths: .aw/system/workflows/assess/templates/ipd.md, agent_workflows/ipd_lint.py, agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/ipd_authoring.py, agent_workflows/cli.py, tests/test_legacy_finalize.py, tests/test_orchestrator_retirement.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: executed:18kg7o
- Status: approved
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: legacyfin
- Order: 2
- Highest E allocated: 09
- Readiness: go
- Review-Depth: standard
- Author: opencode/claude-opus
- Id: 9en4fy
- Approval: 2026-11-06, human ("approved"): maintainer instruction 2026-11-06: 'Let's address these. Use the repos conventions.'

## Workflow history
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 fixed in place (standard tier: references, executability, security, engineering).
- 2026-11-06 approved (opencode/claude-opus, --by-human): maintainer instruction 2026-11-06: 'Let's address these. Use the repos conventions.'

- 2026-11-06 to-review (opencode/claude-opus): authored from the maintainer's field report on a migrated target repository ("Let's address these. Use the repos conventions."); code written alongside, validation pending.
- 2026-11-06 draft (opencode/claude-opus): created.

## Goal

Let an approved plan written in the old format reach `executed/` in a migrated repository with plain `aw ipd finalize`, with no hand rewrite, no hand-written attestation, no `--base`, and no scope reasons for files the migration moved, while every format or state defect that is real still refuses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: legacy header values (report issues 4, 6, 7)

- [x] E-01 In `ipd_lint._apply_legacy_format`, drop the `IPD-M104` findings that only object to an in-place annotation (`_is_legacy_annotation_diag`): Status leading with a recognized status (`_legacy_leading_status`), Date leading with a valid ISO date, Approval beside a leading `approved`; re-judge the checkpoint status rule on the leading token.
  - Depends on: none
  - Expected outcome: `- Status: approved (2026-07-02; executing)` with `- Date: 2026-07-01 14:00` lints conforming at pre-execution (what `aw ipd begin` runs) and pre-transition with `IPD-L001`; `wobbly (...)` still reports `IPD-M104`; an annotated `draft` still fails pre-execution with `IPD-S404` on its leading token.
  - Execution state: performed
- [x] E-02 Let `ipd_lifecycle._STATUS_APPROVED_RE` match `- Status: approved` followed by end of line or an annotation (` (`, `;`, `,`, ` - `).
  - Depends on: none
  - Expected outcome: `derive_baseline` returns the approval commit of an annotated plan, so finalize needs no `--base`.
  - Execution state: performed
- [x] E-03 Add `IPD-L002` (`ipd_lint._with_no_cutover_advisory`) when format-only findings fire and no `ipd_plan_format` cutover resolves, and append `ipd_lifecycle._no_cutover_hint` to the post-cutover receipt refusal when no `ipd_begin_receipt` cutover resolves. Both name `aw install`; neither changes a disposition.
  - Depends on: none
  - Expected outcome: in a repo with no cutovers, lint carries `IPD-L002` and finalize's refusal names the missing cutover; with cutovers stamped, neither appears.
  - Execution state: performed
- [x] E-04 In `status_set.apply_status_change`, when no bare-token `- Status:` line matches in a plan's front matter, replace the line whose value LEADS with a recognized status and keep the old value as `- Prior-Status:`.
  - Depends on: none
  - Expected outcome: a finalized annotated plan carries exactly one `- Status: executed` and a `- Prior-Status:` line, and post-transition lint passes (previously `IPD-M102` duplicate field, COMMITTED-INCOMPLETE).
  - Execution state: performed

### Task group 2: finalize scope and index (report issues 5, 1)

- [x] E-05 Add `ipd_lifecycle._pure_layout_renames` (`git diff --name-status -M --find-renames=100%`, `R100` from `.agents/` or `workflow-artifacts/` into `.aw/`) and excuse those paths from the out-of-scope set and the in-scope collision list in `finalize_precheck`; record `layout_migration_renames_excused` in the scope audit.
  - Depends on: none
  - Expected outcome: a plan approved before the migration finalizes with no `--scope-reason`; a moved file whose content also changed still demands one.
  - Execution state: performed
- [x] E-06 Give `_refresh_plans_index_fail_loud` a `plan_name` argument: when EVERY failing finding is a per-plan rule (`id-missing`, `id-invalid`, `name-metadata-mismatch`) on a different plan file, return them as warnings; `_finalize_transaction` records them and `_complete_after_commit` returns them as success findings. Update the ordering spy in `tests/test_orchestrator_retirement.py` to forward keyword arguments.
  - Depends on: none
  - Expected outcome: an id-less neighbour plan yields exit 0, a warning naming it, and no journal; stale manifests and findings on the finalized plan still leave COMMITTED-INCOMPLETE.
  - Execution state: performed

### Task group 3: migration and authoring surfaces (report issues 3, 8, 9)

- [x] E-07 Let `ipd_authoring.insert_id_line` accept the bold spelling (`- **Status:**`, `- **Date:**`, `- **Author:**`) of each anchor; the inserted line stays plain `- Id: <id6>`.
  - Depends on: none
  - Expected outcome: `aw ipd sync --all --apply` gives a bold-header plan an Id directly after `- **Status:**`, and `aw index plans --check` is clean.
  - Execution state: performed
- [x] E-08 Add `cli._migration_commit_message`, which counts moves from the porcelain status of the commit's own paths (both sides of a staged rename), and use it for the migrate-layout commit.
  - Depends on: none
  - Expected outcome: a re-run whose moves were already committed is titled `record agent-workflows layout policy (N file(s); no files moved ...)`; a real migration reports its real move count.
  - Execution state: performed
- [x] E-09 Remove the `ipd-structure-and-linting Section 10.2` citation from the `IPD-C801` message (state the line-as-subject exemption inline instead) and from the scaffold's Step 0 guidance line, regenerating the shipped child template `.aw/system/workflows/assess/templates/ipd.md` from `ipd_authoring.build_skeleton`; amend spec Section 13.2a for E-01..E-06 and add a spec history note.
  - Depends on: E-01, E-05, E-06
  - Expected outcome: the advisory is self-contained in a target repo; the spec describes the behavior the code has.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Legacy predicate: `config.plan_predates_cutover` fails closed when no cutover resolves; `aw install` (`engine` -> `config.sync_cutovers_on_install`) and `aw migrate-layout` stamp cutovers.
- Status vocabulary and legacy mapping live in `plans.normalize_status` / `plans.RECOGNIZED`; lint reuses them rather than re-listing.
- Finalize success findings render as `IPD-FINALIZE` warnings in `ipd_lifecycle.run_finalize`.
- Tests for this Set live in `tests/test_legacy_finalize.py` and drive real temp git repos through `cli.main`, `ipd_lifecycle.finalize`/`derive_baseline` and `ipd_lint.lint_file`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | (report 6, 7) The reduced legacy check exists (`18kg7o`) but the target repository had no cutovers when finalize ran: `project.json` was first committed by the installer sync 36 minutes AFTER the finalize commit. Fail-closed predicate, so the full check applied, with nothing saying why. | target repo `git log -- .aw/config/project.json`; `config.plan_predates_cutover`. |
| F-2 | Even with cutovers, the remaining legacy pending plans refuse on `IPD-M104`: annotated Status, Date with a time, and Approval beside an annotated status. | `aw ipd lint --phase pre-transition` on the target repo's `20260914-2010-01-...` plan (3x `IPD-M104`). |
| F-3 | (report 4) `_STATUS_APPROVED_RE` required `approved` to end the line. | `ipd_lifecycle._STATUS_APPROVED_RE`; scratch repro: "git cannot find the commit that approved it". |
| F-4 | After F-2/F-3, finalize inserted a second `- Status:` because `status_set._STATUS_RE` needs a bare token, and post-transition refused `IPD-M102`. | Scratch repro output: COMMITTED-INCOMPLETE, `IPD-M102 Status: duplicate field`. |
| F-5 | (report 5) The scope audit judged every path in `base..HEAD`; the migration's 688 `R100` renames sit inside it when the baseline predates the migration. | target repo `git diff -M --find-renames=100% --name-status <approval> <migration>`: 688 `R100`. |
| F-6 | (report 1) `_refresh_plans_index_fail_loud` raised on any non-info finding, including `id-missing` on another plan. | `ipd_lifecycle._refresh_plans_index_fail_loud`; the report's finalize commit. |
| F-7 | (report 3) `insert_id_line` anchors only on `- Status:`/`- Date:`/`- Author:`. | `ipd_authoring._ID_ANCHOR_PREFIXES`; target repo `aw ipd sync --all`: "cannot place Id". |
| F-8 | (report 8) The commit subject used `summarize()['moved']`, the journal's lifetime count, not the commit's content. | target repo re-run migration commit: "145 moved", 1 file changed. |
| F-9 | (report 9) `IPD-C801` and the scaffold cite a spec only this repository has. | `ipd_lint.check_citation_anchors`; `ipd_authoring` scaffold Step 0 line. |
| F-10 | (report 2) Already fixed in `b61554756`; the target repo's `.aw/.gitignore` carries the INDEX and `/state/` rules. | target repo `.aw/.gitignore`. |

## Proposed changes (ordered, validatable)

E-01 to E-09 in order; each is independently testable through the commands and tests named in its expected outcome and its `V-*` item.

## Deferred / out of scope (with reason)

- Writing `Readiness` from a history verdict (report 7's second suggestion): rejected; `18kg7o` recorded the maintainer's decision that a tool-written readiness is a forged attestation, and the reduced check already drops `IPD-M113` for legacy plans, so the field is not needed.
  - Carrier-Declined: design decision restated from `18kg7o`, not a defect.
- An `aw ipd upgrade` converter (report 6's second suggestion): not needed once the reduced check accepts the old format as written; rewriting reviewed records is what the report objects to.
  - Carrier-Declined: superseded by E-01..E-04.
- Publishing the IPD spec into target repos (report 9's alternative): larger than the defect; the message is now self-contained.
  - Carrier-Declined: optional enhancement, not a defect.

## Scope check

- Over-scope: none.
- Under-scope: runner finalize goes through the same `finalize_precheck` and `_finalize_transaction`, so runners inherit E-05/E-06 with no runner change.

## Required tests / validation

New classes in `tests/test_legacy_finalize.py` drive `aw ipd finalize`, `aw ipd sync --all`, `ipd_lint.lint_file`, `ipd_lifecycle.derive_baseline` and `cli._migration_commit_message` against real temporary git repos. The affected lifecycle/lint/index/status suites and the routine core gate run green; the fix is also exercised against a clone of the target repository's pending plans.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 13.2a (declared in Scope-Paths): the legacy-format rules and the finalize scope/index behavior are the contract every other plan is reviewed against, so they must state the annotated-value reading, `IPD-L002`, the pure-rename exemption and the other-plan index warning.

## Open questions

### OQ-01: Should a pure rename be excused only when it came from an `aw migrate-layout` commit?

- Blocking: no
- Status: resolved
- Owner: opencode/claude-opus
- Resolution or deferral rationale: no. The migration commit carries no machine-readable marker in a target repo (the measured one was hand-titled), and the rename shape (100% similarity, legacy root into `.aw/`) is what identifies migration output. Any content change drops below 100% and is judged normally.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output for `AnnotatedLegacyHeaderTests` and `AnnotatedApprovedPassesPreExecutionTests` (conforming annotated plan at pre-execution and pre-transition, refused unrecognized status, refused annotated draft at pre-execution), plus `aw ipd lint --phase pre-transition` output on a clone of the target repository's `20260914-2010-01-...` plan.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for `test_derive_baseline_finds_an_annotated_approval`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output for `NoCutoverHintTests` (both tests).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output for `test_finalize_completes_and_keeps_the_annotation` (one Status line, Prior-Status kept, exit 0).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output for `MigrationRenamesNotOutOfScopeTests` (pure renames need no reason; a content-changed rename still does).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for `IndexFindingOnAnotherPlanTests` and for `tests/test_orchestrator_retirement.py` plus the `FailLoud` tests in `tests/test_ipd_lifecycle_cli.py` (genuine non-convergence still COMMITTED-INCOMPLETE).
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted pytest output for `BoldHeaderIdBackfillTests`, plus `aw ipd sync --all` dry-run output on a clone of the target repository's plans showing the bold-header plan would get an Id.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted pytest output for `MigrationCommitSubjectTests` (both tests).
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted pytest output for `CitationAdvisoryNamesNoUninstalledSpecTests` and `tests/test_ipd_templates.py` (template parity with `build_skeleton`), the spec diff of Section 13.2a, and the routine core gate (`python3 -m pytest`) summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: all nine items are the steps one legacy plan hits, in order, on the way to `executed/` in a migrated repository; they share one test module and one spec section.

Execution requires human approval. The maintainer's instruction "Let's address these. Use the repos conventions." is recorded as that approval. Commit through `aw commit 9en4fy -- <paths>`, never push, and finalize with `aw ipd finalize 9en4fy` only after every `V-*` item carries pasted evidence.

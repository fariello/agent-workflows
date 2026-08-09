# IPD: Documentation, release, and end-to-end cutover

- Date: 2026-08-09
- Kind: child
- Concern: Align current-state documentation and release metadata with the implemented architecture, then prove the complete install, update, storage, action, migration, and uninstall lifecycle.
- Scope: `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, shipped getting-started and help text, relevant specification status and relation notes, end-to-end fixtures, and release preparation without tag or push.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 11
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: blw6qp

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, D125 attention ownership, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L11-01 [MEDIUM] (the 25-scenario acceptance matrix is asserted but NOT enumerated; E-04's ~12 coarse categories do not visibly cover distinct spec §19 scenarios 19.17/19.22/19.23/19.24/19.25; add a 25-row scenario -> named-test/host-evidence traceability table so V-04's 'no scenario silently skipped' is enforceable). L11-02 (do NOT hand-edit the derived git-tag-driven `VERSION` per RELEASING.md; record notes in CHANGELOG/docs only; the version is set at release-review Section 9). Positive: release boundary honored - no tag/Release/PyPI/push; honestly gates done on Orders 01-10.
- 2026-08-09 author revision (Codex GPT-5): addressed L11-01 and L11-02 by adding the complete 25-row acceptance traceability contract and explicitly excluding hand-edits to the tag-derived `VERSION` from release preparation.

## Goal

Cut over the product narrative only after implementation evidence exists, and verify that the documented choices match observable behavior. Prepare the appropriate major-version release boundary without publishing, tagging, or pushing it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Documentation truth

- [ ] E-01 Audit completed Orders 01 through 10 and update `README.md` and `ARCHITECTURE.md` with the four logical roots, delivery and records axes, AW-home identity, durability language, action lifecycle, wizard behavior, and host support matrix exactly as implemented.
  - Depends on: none
  - Expected outcome: current-state docs contain no planned-as-shipped claims and clearly distinguish supported, conditional, and unsupported modes.
  - Execution state: pending
- [ ] E-02 Add a user migration and recovery walkthrough, backend selection examples, companion-repository guidance, backup caveats, privacy warnings, action commands, noninteractive examples, and uninstall preservation behavior to shipped help and getting-started surfaces.
  - Depends on: E-01
  - Expected outcome: a user can install, choose storage, make records durable, migrate, recover, and remove AW without consulting design documents.
  - Execution state: pending
- [ ] E-03 Update `CHANGELOG.md`, specification statuses and relation notes, compatibility statements, and non-version release metadata for a major storage-layout boundary; record breaking changes and upgrade requirements without editing the tag-derived `VERSION`, creating a tag, or creating a release. `VERSION` changes only in release-review Section 9 through its documented tag process after separate human GO.
  - Depends on: E-02
  - Expected outcome: design history, current behavior, and release notes agree on what changed and how existing users move forward.
  - Execution state: pending

### Task group 2: Cutover proof

- [ ] E-04 Implement and run the canonical specification's acceptance matrix across fresh interactive install, noninteractive install, repeated update, every records backend, durability transitions, action lifecycle, migration, rollback, clean-delta gates, dirty Git, worktrees, and uninstall.
  - Depends on: E-03
  - Expected outcome: each acceptance scenario has a named automated case or a recorded manual host-evidence result with actual output.
  - Execution state: pending
- [ ] E-05 Run all focused and repository-wide validation, IPD and documentation lint, package and wheel checks, shim parity, secret and absolute-path scans, and a second idempotence pass; fix in-scope defects and record any external blocker.
  - Depends on: E-04
  - Expected outcome: the implementation is release-ready locally with no unaccounted drift, placeholder, secret, path leak, or generated-file mismatch.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `README.md` and `ARCHITECTURE.md` describe current behavior, not aspirational design.
- `CHANGELOG.md` records user-visible changes and migration impact.
- Host support claims require D113 evidence and exact version scope.
- Repository instructions prohibit push; release publication remains a separate user-authorized action.
- `VERSION` is derived from Git tags under `RELEASING.md`; ordinary implementation and release-preparation edits must not change it.

## Acceptance traceability contract

The matrix implementation may refine test module names, but every final row must retain its Section 19 number, unique test or host-evidence ID, owning Order, and actual result. Broad categories may not replace individual rows.

| Scenario | Owning Order | Required named test or host evidence |
|---|---:|---|
| 19.1 | 04, 05 | `fresh_interactive_home_recommended` |
| 19.2 | 04, 05 | `fresh_interactive_repository_risk_acknowledged` |
| 19.3 | 03, 06 | `companion_local_git_opens_durability_action` |
| 19.4 | 03 | `companion_confirmed_private_remote` |
| 19.5 | 04, 05 | `first_noninteractive_complete_policy` |
| 19.6 | 04 | `first_noninteractive_missing_policy_fails_before_write` |
| 19.7 | 04, 05 | `same_version_reinstall_checkpoint_noop` |
| 19.8 | 04, 05 | `version_update_keep_policy` |
| 19.9 | 04, 09 | `update_repository_to_home` |
| 19.10 | 06 | `skipped_versions_reconcile_action_generations` |
| 19.11 | 02 | `repository_move_reattach` |
| 19.12 | 01, 02 | `clone_worktree_resolution_matrix` |
| 19.13 | 06, 07 | `setup_action_all_attention_surfaces` |
| 19.14 | 06, 07 | `setup_completion_moves_completed` |
| 19.15 | 06 | `dismissal_history_no_resurrection` |
| 19.16 | 06 | `new_generation_supersedes_open` |
| 19.17 | 01, 03, 08 | `split_product_and_record_commits` |
| 19.18 | 09 | `migration_preserves_before_cleanup` |
| 19.19 | 09 | `uninstall_preserves_external_state_records` |
| 19.20 | 10 | `clean_delta_merge_base_zero_write` |
| 19.21 | 01, 08 | `unavailable_external_root_stops_writes` |
| 19.22 | 04 | `terminal_color_environment_matrix` |
| 19.23 | 04 | `screen_reader_linear_semantics` |
| 19.24 | 03 | `privacy_doctor_refuses_unverified_privacy` |
| 19.25 | 01, 03 | `broken_navigation_link_resolver_succeeds` |

## Findings

| Document surface | Required truth boundary |
|---|---|
| Design specification | intended contract and accepted constraints |
| IPDs | implementation sequence and validation gates |
| README and help | behavior a user can run now |
| Architecture | implemented components and ownership |
| Changelog | shipped delta and upgrade impact |

## Proposed changes (ordered, validatable)

1. Derive current-state docs from completed implementation evidence.
2. Provide complete user setup, durability, migration, and recovery guidance.
3. Align release metadata and design statuses.
4. Run the full acceptance matrix.
5. Complete release-readiness validation without publication.

## Deferred / out of scope (with reason)

- Creating a Git tag, GitHub release, package publication, or push requires separate explicit authorization.
- Unsupported hosts remain documented as unsupported rather than blocking release of proven modes.
- Rewriting historical repository content is excluded.

## Scope check

- Over-scope: no tag, push, package upload, remote release, speculative host claim, or history rewrite.
- Under-scope: user docs, architecture, changelog, help, migration guide, acceptance matrix, packaging, parity, leaks, and idempotence are covered.

## Required tests / validation

- `python3 -m unittest discover -s tests -v`
- `python3 -m agent_workflows ipd lint --root .agents/plans --mode full`
- `python3 -m agent_workflows shim generate`
- `python3 -m agent_workflows parity`
- Run the repository's documented package and wheel verification commands from a clean temporary environment.
- Run repository secret, absolute-path, and Unicode dash scans over every changed text file.

## Spec / documentation sync

- Update `.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` status only after implementation satisfies its acceptance scenarios.
- Record exact relations to D107, D109, D113, and D122 through D129 without erasing historical decisions.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: line-by-line doc audit maps each behavioral claim to passing code or test evidence and labels every unsupported host accurately.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a clean-room walkthrough follows only shipped docs and completes install, durability setup, action resolution, migration dry run, recovery lookup, and uninstall preview.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: changelog, spec status, relation notes, compatibility text, and non-version release metadata agree on the major upgrade boundary; `git diff -- VERSION` is empty; no tag or release exists.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: a generated result table has exactly one row for each scenario 19.1 through 19.25, preserves the named IDs above, cites a passing automated test or explicit actual host-evidence record for each, and fails on missing, duplicate, skipped, or extra scenario numbers.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: actual outputs show all required suites and scans pass, second-generation runs are clean, and the final diff contains only intentional release-ready changes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: user-facing truth, release metadata, and final end-to-end evidence are one cutover gate after component work is complete.

STOP until Orders 01 through 10 reach their defined completion or explicit unsupported-host outcome. Do not execute until this plan and the parent orchestrator are approved. Do not tag, publish, release, or push without a separate user request.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.

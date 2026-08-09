# IPD: Documentation, release, and end-to-end cutover

- Date: 2026-08-09
- Kind: child
- Concern: Align current-state documentation and release metadata with the implemented architecture, then prove the complete install, update, storage, action, migration, and uninstall lifecycle.
- Scope: `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, shipped getting-started and help text, relevant specification status and relation notes, end-to-end fixtures, and release preparation without tag or push.
- Status: to-review
- Set: awlayout (AW project layout)
- Order: 11
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: blw6qp

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, D125 attention ownership, and the current lifecycle execution contract after the upstream rebase.

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
- [ ] E-03 Update `CHANGELOG.md`, specification statuses and relation notes, compatibility statements, and release metadata for a major storage-layout boundary; record breaking changes and upgrade requirements without creating a tag or release.
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
  - Required evidence: changelog, spec status, relation notes, compatibility text, and local version metadata agree on the major upgrade boundary; no tag or release exists.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: every canonical acceptance scenario has a passing automated test or an explicit actual host-evidence record; no scenario is silently skipped.
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

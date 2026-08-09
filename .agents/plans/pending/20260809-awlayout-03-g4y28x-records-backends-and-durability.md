# IPD: Records backends and durability

- Date: 2026-08-09
- Kind: child
- Concern: Implement repository, companion, and AW-home record backends with truthful durability reporting and safe Git boundaries.
- Scope: `agent_workflows/storage.py`, storage-related CLI wiring in `agent_workflows/cli.py`, and `tests/test_storage.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 3
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: g4y28x

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L3-01 (durability HONESTY: a merely-configured remote must NOT map to `durable-private`/secrecy - gate on explicit acknowledgement per §6.2/§16). L3-02 (the `aw storage status` validation command needs a registered-fixture precondition, else it fails for environmental not logic reasons). L3-03 (add §14 identity-conflict-refusal + machine-local-paths-excluded-from-tracked-history assertions). L3-04 (name the owner of the §5.2 `clean-delta`+`repository` prohibition - Order 04 - or add a rejecting V-item).
- 2026-08-09 author revision (Codex GPT-5): addressed L3-01 through L3-04 by separating observable remote configuration from acknowledged durability and privacy claims, adding registered-fixture prerequisites, testing identity and tracked-history boundaries, and assigning the `clean-delta` plus `repository` policy rejection to Order 04.
- 2026-08-09 re-reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (by the author). Verified against repo evidence that the author's revision RESOLVED every prior finding - H1-H7 and all L0/L1..L11 items - and introduced no new finding; the dependency DAG remains valid and the orchestrator/child dependency lines agree (Order 07 now correctly depends on 01,06). All 12 lint conforming at author + review-finalize. Readiness: GO - PENDING HUMAN APPROVAL, gated ONLY on the controlling spec 20260809-2211-01 being approved (still Status: to-review) before any child executes.

## Goal

Make records location an independent policy axis with AW-home storage as the recommended default. Report durability from observable facts and never imply that a local directory is backed up or private merely because it is outside the target repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Backends and boundaries

- [ ] E-01 Define one records-backend interface and implement `home`, `companion`, and `repository` path resolution using the Order 01 context and Order 02 registry.
  - Depends on: none
  - Expected outcome: callers request the logical records root without backend-specific path construction.
  - Execution state: pending
- [ ] E-02 Validate containment, symlink resolution, repository boundaries, and nested-Git hazards before creating or attaching a backend; reject unsafe or ambiguous paths without partial writes.
  - Depends on: E-01
  - Expected outcome: external storage cannot silently resolve inside the target repository or attach to an unintended Git repository.
  - Execution state: pending

### Task group 2: Durability and initialization

- [ ] E-03 Implement observable durability states for uninitialized local storage, local Git only, repository-tracked storage, and explicitly acknowledged external backup; report a configured remote as a separate observable fact and never map it to `durable-private` or any secrecy claim without a recorded user acknowledgement of the applicable remote privacy or backup safeguard.
  - Depends on: E-02
  - Expected outcome: `aw storage status` reports what can be proven, separates privacy from durability, and recommends the next action.
  - Execution state: pending
- [ ] E-04 Add explicit `aw storage init`, `aw storage attach`, and `aw storage status` flows; allow local Git initialization with consent, never create a remote or push, and preserve existing repositories.
  - Depends on: E-03
  - Expected outcome: users can make external records durable without AW taking unrequested remote actions.
  - Execution state: pending
- [ ] E-05 Add `tests/test_storage.py` for all backends, custom paths, symlinks, nested repositories, empty and existing Git repositories, identity-conflicting companion refusal, durability and remote-fact combinations, acknowledgement transitions, redacted output, exclusion of machine-local registry paths from tracked record history, and failure atomicity.
  - Depends on: E-04
  - Expected outcome: supported storage modes and safety failures are deterministic and regression-tested.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Git operations must be noninteractive and narrowly scoped.
- User data must not be deleted, moved, committed, or pushed without an explicit command and confirmation.
- A remote URL, reachability result, or provider name is not evidence of privacy. `durable-private` requires an explicit acknowledgement record and remains a durability label, not a secrecy promise.
- Stable JSON and agent output are required for workflow consumption.
- Temporary repositories in tests must not depend on global Git configuration.

## Findings

| Backend | Target pollution | Typical durability | Main risk |
|---|---:|---|---|
| `home` | none | local until configured | mistaken assumption that local means backed up |
| `companion` | none | local Git or private remote | accidental nesting or wrong repository attachment |
| `repository` | `.aw/records/` present | target Git policy | candid material can enter the public history |

## Proposed changes (ordered, validatable)

1. Implement a backend-neutral records interface.
2. Enforce filesystem and Git safety boundaries.
3. Classify only observable durability.
4. Provide explicit initialization and attachment commands.
5. Exercise normal and adversarial path cases.

## Deferred / out of scope (with reason)

- Hosted private-repository creation, credential management, and pushing are excluded because they require provider-specific authority.
- Record-producing workflow changes are Order 08.
- Moving existing records between backends is Order 09.

## Scope check

- Over-scope: no target layout materialization, workflow edits, migrations, remote creation, commit, or push.
- Under-scope: all three backends, custom external paths, safety boundaries, and durability states are covered.

## Required tests / validation

- `python3 -m unittest tests.test_storage -v`
- `python3 -m unittest discover -s tests -v`
- Create and register the temporary project fixture required by Order 02, then run `python3 -m agent_workflows storage status --repo <fixture> --json`.

## Spec / documentation sync

- Keep backend names, recommended default, and durability language aligned with the canonical 2026-08-09 layout specification.
- Do not describe any backend as private unless access controls were independently observed.
- Order 04 owns policy validation that rejects the forbidden `delivery=clean-delta` plus `records=repository` combination before any materialization; this plan supplies the backend facts consumed by that validator.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: focused tests resolve all backends and prove callers use the logical records root rather than backend literals.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: tests reject traversal, symlink escape, target containment, unsafe nesting, ambiguous Git ownership, and companion identity conflict before mutation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: registered-fixture status tests prove a configured remote alone remains a neutral observable fact, `durable-private` appears only after explicit acknowledgement, acknowledgement removal downgrades the state, and no wording equates external, local, durable, private, or secret.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: command transcripts show consent gates, existing-repository preservation, no remote creation, no push, and idempotent re-entry.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused and full suites pass without reading or changing the operator's global Git configuration; tracked-history inspection contains no machine-local registry path; and an Order 04 contract fixture rejects `clean-delta` plus `repository` before writes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the backend abstraction, its safety checks, and truthful durability state form one storage boundary.

STOP if Orders 01 or 02 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.

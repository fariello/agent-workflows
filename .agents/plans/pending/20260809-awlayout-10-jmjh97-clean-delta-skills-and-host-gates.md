# IPD: Clean-delta skills and host gates

- Date: 2026-08-09
- Kind: child
- Concern: Make clean-delta installation use proven user-scope host capabilities while keeping the target repository free of AW-owned files.
- Scope: user-scope skill installation and capability code, clean-delta engine and manifest integration, host fixtures and probes, and focused tests; evidence requirements remain governed by D113.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 10
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: jmjh97

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L10-01 (add a V-item asserting the set of advertised clean-delta host/version claims EQUALS the set of D113-reproduced pairs - no claim without a matching evidence record - within the order that mints the claim). Positive: intent is sound - unproven combos unsupported, no claim inherited across versions, STOP gate requires D113 evidence for the exact host/version, merge-base zero-write verified; no over-claim found.
- 2026-08-09 author revision (Codex GPT-5): addressed L10-01 by making advertised claim-set equality with the D113 reproduced evidence set an explicit implementation and validation requirement.
- 2026-08-09 re-reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (by the author). Verified against repo evidence that the author's revision RESOLVED every prior finding - H1-H7 and all L0/L1..L11 items - and introduced no new finding; the dependency DAG remains valid and the orchestrator/child dependency lines agree (Order 07 now correctly depends on 01,06). All 12 lint conforming at author + review-finalize. Readiness: GO - PENDING HUMAN APPROVAL, gated ONLY on the controlling spec 20260809-2211-01 being approved (still Status: to-review) before any child executes.

## Goal

Complete the clean-delta architecture only where exact host and version evidence proves that user-scope skills can provide equivalent behavior. Fail closed or use an already specified compatible mode where capability is absent; never infer support from documentation or a different host version.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Evidence and user-scope capability

- [ ] E-01 Consume the D113 Phase 0 evidence manifest for each supported host and exact tested version; record command, environment, observed lookup order, writable scope, and fixture hash, and mark all unproven combinations unsupported.
  - Depends on: none
  - Expected outcome: no clean-delta support claim exists without reproducible, version-specific evidence.
  - Execution state: pending
- [ ] E-02 Implement a versioned user-scope skill payload and capability adapter that owns only AW-installed skill files, respects host lookup precedence, and rejects collisions, drift, or unsupported versions before mutation.
  - Depends on: E-01
  - Expected outcome: the AW command can install and inspect its user-scope integration without overwriting user-owned host content.
  - Execution state: pending
- [ ] E-03 Add dependency-aware install, update, verify, and uninstall behavior for shared user-scope payloads so one project cannot remove assets still required by another registered project.
  - Depends on: E-02
  - Expected outcome: multiple projects safely share a managed host capability with reference and ownership evidence.
  - Execution state: pending

### Task group 2: Zero-target-write integration

- [ ] E-04 Wire clean-delta policy to user-scope skills, the AW registry, external logical roots, and host-required global configuration; verify target zero-write behavior against the pre-install merge base and fail before writes when equivalence is unavailable.
  - Depends on: E-03
  - Expected outcome: successful clean-delta install, update, and workflow use leave the target repository byte-for-byte unchanged by AW.
  - Execution state: pending
- [ ] E-05 Add exact-version host fixtures, capability probes, target-diff assertions, cloud-boundary cases, shared-dependency lifecycle tests, explicit unsupported-version tests, and one deterministic claim manifest generated only from reproduced D113 evidence pairs; fail if advertised clean-delta host/version pairs are not exactly equal to that evidence set.
  - Depends on: E-04
  - Expected outcome: proven hosts pass the full behavior matrix and every unproven host or version receives an actionable refusal.
  - Execution state: pending

## Project conventions discovered (Step 0)

- D113 requires runtime evidence before host-specific skill claims are implemented or documented.
- D109 defines clean-delta as zero AW-owned target writes, measured from an appropriate Git baseline.
- Shared user-scope assets need explicit ownership and dependency tracking.
- Cloud execution may have a different home, filesystem, or skill lookup boundary from local execution.

## Findings

| Evidence result | Allowed behavior |
|---|---|
| Exact host and version proven equivalent | offer clean-delta |
| Host known but tested version differs | run probe; do not inherit the claim |
| Skill scope unavailable or semantically incomplete | refuse clean-delta and explain supported alternatives |
| Cloud boundary cannot access the same user scope | report the boundary; do not claim local configuration applies |

## Proposed changes (ordered, validatable)

1. Gate work on exact D113 evidence.
2. Install a collision-safe user-scope capability.
3. Track shared dependencies across projects.
4. Integrate zero-target-write behavior and fail closed.
5. Test supported and unsupported environments explicitly.

## Deferred / out of scope (with reason)

- Any host or version without D113 runtime evidence remains unsupported.
- Circumventing host sandbox, permission, or cloud-boundary restrictions is excluded.
- Publishing user-scope skills to third-party registries is excluded.

## Scope check

- Over-scope: no speculative host support, permission bypass, remote publication, or compatibility promise based only on docs.
- Under-scope: evidence gating, skill ownership, shared dependencies, target diff, cloud boundaries, unsupported behavior, and uninstall are covered.

## Required tests / validation

- `python3 -m unittest discover -s tests -p '*skill*' -v`
- `python3 -m unittest discover -s tests -p '*clean_delta*' -v`
- `python3 -m unittest discover -s tests -v`
- Run every D113 host probe command recorded for a claimed exact version and preserve its actual output as evidence.

## Spec / documentation sync

- Update support claims only for exact host versions proven by D113 evidence.
- Keep zero-target-write semantics aligned with D109 and the canonical 2026-08-09 layout specification.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: each claimed host-version pair has a complete D113 evidence record whose fixture hash and command can be reproduced.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: install tests prove lookup behavior, ownership boundaries, collision refusal, drift refusal, and no mutation for unsupported versions.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: two-project tests prove updates are deterministic and uninstall preserves shared assets until the last dependent project releases them.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: merge-base and filesystem snapshots prove zero target writes across install, update, workflow use, and uninstall for every supported host fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: exact-version, version-mismatch, missing-scope, cloud-boundary, collision, and shared-dependency suites all produce their specified pass or refusal outcome; a set-equality assertion proves advertised clean-delta host/version claims equal the D113-reproduced pairs with neither unsupported claims nor unadvertised reproduced pairs.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: capability evidence, shared ownership, and target zero-write proof must be validated as one host-integration boundary.

STOP unless D113 evidence is complete for the exact host and version under implementation and Orders 01, 02, 03, 05, 08, and 09 are complete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.

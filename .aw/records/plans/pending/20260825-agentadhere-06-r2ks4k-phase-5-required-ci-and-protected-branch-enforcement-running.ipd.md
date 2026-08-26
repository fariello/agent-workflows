# IPD: Phase 5: required CI and protected-branch enforcement running the same policy engine

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 5 + section 7.8: required CI on a protected branch is the ONLY non-bypassable authority boundary rated "Very high" - a clean, remote environment running the same policy engine, validating committed artifacts, and blocking merge on findings, with branch protection that also protects the policy/workflow files themselves from being weakened without approval. The toolkit has no required-CI gate wired that runs the phase-1 `aw check` engine and blocks the merge boundary.
- Scope: Add required CI + protected-branch enforcement: (1) a CI workflow (e.g. `.github/workflows/`) that runs the SAME phase-1 `aw check --format json` engine in a clean environment, validates the committed workflow artifacts (plans/specs/backlog conformance, scope, release gates), and publishes machine-readable evidence; (2) run the test suite in CI; (3) document/configure branch protection to REQUIRE the check and disallow ordinary bypass actors, and to protect the policy/hook/CI definition files from being weakened without approval (findings 7.8); (4) ensure the CI-run engine and the local `aw check` produce identical results (no divergence). This is the authoritative repository boundary; it does NOT attempt authority-invariant guarantees (external signing/push broker - deferred set). Should land LAST in the set so it gates on a stable engine.
- Scope-Paths: .github/, agent_workflows/check_engine.py, agent_workflows/cli.py, docs/, tests/
- Status: draft
- Set: agentadhere
- Order: 6
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: r2ks4k

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add required CI on a protected branch that runs the same phase-1 `aw check` engine + test suite in a clean environment and blocks the merge boundary on findings, protecting the policy/hook/CI files themselves - the authoritative, non-bypassable repository boundary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CI workflow

- [ ] E-01 Add a CI workflow that runs `aw check --format json` (the phase-1 engine) + the test suite in a clean environment, validates committed workflow artifacts, and publishes machine-readable evidence; fail the job on any finding.
  - Depends on: none
  - Expected outcome: CI runs the engine + tests and fails on a seeded violation; passes on a clean tree.
  - Execution state: pending

### Task group 2: branch protection + divergence check

- [ ] E-02 Document/configure branch protection to require the check and disallow ordinary bypass, protecting the policy/hook/CI definition files from being weakened without approval; add a test/assertion that the CI-run engine and local `aw check` produce identical results.
  - Depends on: E-01
  - Expected outcome: protection config documented/applied; a parity test confirms CI and local engine agree.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The repo has existing CI infra under `.github/`; add the required check there.
- `aw check` (`check_engine`) is the single engine the local hooks (phase 4) already call; CI must call the SAME one (no forked policy).
- Findings 7.8: protect the workflow/policy/CI files themselves and disallow bypass actors; this is the "Very high" authority boundary for repository invariants.

## Findings

CI is the smallest change with the largest assurance gain (a workflow file + branch protection) precisely because it reuses the phase-1 engine; the risk is divergence between CI and local, mitigated by a parity assertion.

## Proposed changes (ordered, validatable)

1. `.github/workflows/`: required job running `aw check --format json` + tests, publishing evidence.
2. Branch protection config/docs (require check, protect policy files, disallow bypass).
3. `tests/`: parity between CI-run and local engine; seeded-violation fails, clean passes.

## Deferred / out of scope (with reason)

- Authority-invariant guarantees (external signing, push broker, remote transition service): deferred external-signing set; CI enforces repository invariants, not non-forgeable provenance.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- CI fails on a seeded invariant violation and passes on a clean tree (paste the CI run result).
- The CI-run engine and local `aw check` produce identical findings on the same tree (parity).
- Branch protection requires the check and protects the policy/hook/CI files (documented/verified).

## Spec / documentation sync

- Document the required CI gate + branch-protection policy in RELEASING.md / CONTRIBUTING.md / AGENTS.md as the authoritative boundary.

## Open questions

### OQ-01: This child edits .github/ and branch protection - is that within an executor's authority, or a human-gated step?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: Adding the CI workflow file is normal code; ENABLING branch protection is a repo-admin action that likely needs an explicit human step. Split: the executor lands the workflow + docs; a human applies protection. Confirm before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).

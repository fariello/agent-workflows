# IPD: Post-migration independent audit

- Date: 2026-08-10
- Kind: child
- Concern: Independently prove migration completeness, routing, Git/privacy boundaries, recoverability, and remaining review needs instead of trusting the migrator's success report.
- Scope: Deterministic compare/postcheck engines, evidence schema, fresh-agent follow-up instructions, deceptive fixtures, completion gate integration, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 10
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: n3fz8b

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to make independent evidence, not same-process narrative, the migration completion authority.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.

## Goal

Compare frozen pre-migration evidence with actual post-migration files, policy, Git repositories, producers, adapters, retained sources, and rollback state. Then give a fresh agent a bounded instruction set to inspect deterministic evidence and identify genuine residual risks without inventing defects.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Compare every inventoried item

- [ ] E-01 Implement or promote `tools/awphysical/aw_layout_compare.py` as a deterministic comparison engine over the frozen inventory, approved migration map, transaction receipt, current policy/context, and destination filesystem.
  - Depends on: none
  - Expected outcome: Every source item has exactly one allowed disposition and matching bytes/metadata where required; missing, changed, unexpected duplicate, unapproved exclusion, stale input, or unaccounted destination fails.
  - Execution state: pending

- [ ] E-02 Verify retained legacy material, compatibility status, authoritative-writer switch, transaction phase, rollback inputs, and cleanup eligibility without mutating any repository.
  - Depends on: E-01
  - Expected outcome: A successful comparison proves legacy remains recoverable and non-authoritative; cleanup remains blocked until its independent retention trigger.
  - Execution state: pending

### Task group 2: Audit behavior and boundaries

- [ ] E-03 Implement or promote `tools/awphysical/aw_layout_postcheck.py` to run context/policy validation, physical-root ownership checks, target/companion/source Git checks, ignored/runtime checks, legacy-write scans, adapter purity, producer-routing probes, indexes, attention, package/source role, and sanitizer gates.
  - Depends on: E-01
  - Expected outcome: Postcheck records exact commands, exit codes, normalized output digests, skipped/unsupported reasons, and overall validity; partial execution can never be labeled pass.
  - Execution state: pending

- [ ] E-04 Add non-mutating canary or sandbox probes for each producer class and preset, proving writes resolve to intended test destinations without touching real records or relying on self-reported paths.
  - Depends on: E-01
  - Expected outcome: Legacy, wrong-Git, system/config/state confusion, inaccessible root, and dual-authority regressions are detected after migration.
  - Execution state: pending

### Task group 3: Fresh-agent follow-up and completion gate

- [ ] E-05 Finalize `tools/awphysical/migration-followup-review.md` as a self-contained fresh-agent protocol that consumes inventory/compare/postcheck evidence, inspects high-risk residuals, runs only named read-only checks, distinguishes facts from inferences, and reports required follow-up without fabricating issues.
  - Depends on: E-01
  - Expected outcome: The reviewer does not accept migrator summaries, does not rerun destructive migration, and produces a severity-ranked evidence table plus GO/NO-GO/REVIEW verdict.
  - Execution state: pending

- [ ] E-06 Make successful deterministic compare and postcheck mandatory before migration can be marked complete or cleanup can be enabled; store evidence in the selected records Git owner, sanitized according to policy.
  - Depends on: E-01
  - Expected outcome: Migration CLI status distinguishes copied, switched, verified, independently reviewed, and cleanup-eligible states.
  - Execution state: pending

- [ ] E-07 Add deceptive fixtures where migrator receipts claim success despite missing files, stale hashes, wrong destinations, wrong Git indexes, ignored leakage, legacy writes, copied adapter logic, inaccessible external roots, broken rollback, and skipped checks.
  - Depends on: E-01
  - Expected outcome: Deterministic tools catch every planted defect; clean fixtures remain clean so the audit does not manufacture findings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 06 through 09 must be verified.
- Independent means a separate read-only evidence pass, not necessarily a second expensive model.
- Deterministic failures outrank agent prose; the agent reviews residual judgment areas only.
- Evidence may contain machine paths and must be stored/sanitized according to the selected private/public policy.

## Findings

- Existing migration success can be asserted by the same code/process that performed the work.
- The user specifically requires a follow-up agent instruction set to find remaining review needs.
- Same-model self-review has previously green-washed unrun validations; wrapper-owned deterministic evidence is required.
- Hash completeness alone does not prove producer routing, Git boundaries, clean-target behavior, adapter purity, or rollback readiness.

## Proposed changes (ordered, validatable)

1. Compare every inventory/map/receipt item to actual destinations.
2. Verify retention, authority, rollback, and cleanup state.
3. Run comprehensive deterministic behavioral/boundary postchecks.
4. Probe every producer class safely.
5. Run a bounded fresh-agent residual review over evidence.
6. Gate completion and cleanup on deterministic success.
7. Test deceptive and clean fixtures equally.

## Deferred / out of scope (with reason)

- Repairing detected defects belongs to the owning prior Order or a new corrective IPD.
- Destructive cleanup remains Order 07's separately gated command.
- Model-specific orchestration wrappers are out of scope; the instruction file is tool-agnostic.

## Scope check

- Over-scope: Read-only independent audit and gate integration only; no migration repair, file movement, staging, commit, push, or cleanup.
- Under-scope: Content completeness, authority, retention, rollback, policy, roots, Git, ignored data, producers, adapters, attention/indexes, source role, sanitizer, evidence honesty, agent review, deceptive fixtures, and false-positive control are included.

## Required tests / validation

- Unit and CLI tests for comparison and postcheck schemas, exit codes, stale/partial inputs, and deterministic output.
- Every planted defect fixture must fail for the intended rule; every clean fixture must pass.
- Run all support scripts against their included fixtures and capture actual JSON/status.
- Run the follow-up instruction with a fresh agent against at least one clean and one deceptive fixture; compare its findings to planted truth.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

## Spec / documentation sync

- Update independent verification, evidence storage, completion status, cleanup gate, and residual-review sections of the controlling spec.
- Document deterministic versus agent responsibilities and privacy/sanitization of evidence.
- Keep the instruction set self-contained and repo-relative.

## Open questions

No open questions. Deterministic compare/postcheck own ground truth; a fresh agent reviews residual judgment areas and cannot override failed gates.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Clean and deceptive comparison fixtures prove exact source-disposition accounting, hash/path/Git detection, stale-input rejection, no writes, and stable machine output with distinct rule IDs.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: A successful comparison proves legacy remains recoverable and non-authoritative; cleanup remains blocked until its independent retention trigger. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Postcheck records exact commands, exit codes, normalized output digests, skipped/unsupported reasons, and overall validity; partial execution can never be labeled pass. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Legacy, wrong-Git, system/config/state confusion, inaccessible root, and dual-authority regressions are detected after migration. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: The reviewer does not accept migrator summaries, does not rerun destructive migration, and produces a severity-ranked evidence table plus GO/NO-GO/REVIEW verdict. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Migration CLI status distinguishes copied, switched, verified, independently reviewed, and cleanup-eligible states. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Deterministic tools catch every planted defect; clean fixtures remain clean so the audit does not manufacture findings. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Comparison, behavioral postcheck, residual agent review, deceptive fixtures, and completion gating form one independent assurance layer.

Execution requires verified Orders 06 through 09, a GO `/plan-review`, and human approval. Scope fence: read-only compare/postcheck, safe probes, evidence schema/storage, follow-up instruction, completion gate, and focused tests/docs. Do not repair, migrate, stage, commit project deltas, push, or clean up. Paste actual outputs, path-scope implementation commits, never broad-stage, and never push. A deterministic failure is a hard NO-GO regardless of agent prose. Complete evidence and lint before moving this plan to `executed/`.

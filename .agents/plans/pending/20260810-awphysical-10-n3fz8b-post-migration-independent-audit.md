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
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.

## Goal

Compare frozen pre-migration evidence with actual post-migration files, policy, Git repositories, producers, adapters, retained sources, and rollback state. Then give a fresh agent a bounded instruction set to inspect deterministic evidence and identify genuine residual risks without inventing defects.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Compare every inventoried item

- [ ] E-01 Promote tracked prototype `tools/awphysical/aw_layout_compare.py` into the production owner surface as a deterministic comparison engine over the frozen inventory, approved migration map, transaction receipt, current policy/context, and destination filesystem.
  - Depends on: none
  - Expected outcome: Every source item has exactly one allowed disposition and matching bytes/metadata where required; missing, changed, unexpected duplicate, unapproved exclusion, stale input, or unaccounted destination fails.
  - Execution state: pending

- [ ] E-02 Verify retained legacy material, compatibility status, authoritative-writer switch, transaction phase, rollback inputs, and cleanup eligibility without mutating any repository.
  - Depends on: E-01
  - Expected outcome: A successful comparison proves legacy remains recoverable and non-authoritative; cleanup remains blocked until its independent retention trigger.
  - Execution state: pending

### Task group 2: Audit behavior and boundaries

- [ ] E-03 Promote tracked development prototype `tools/awphysical/aw_layout_postcheck.py` into `.aw/system/tools/` as the installed production helper. Make the core independently read authority/transaction artifacts, actual producer outputs, adapter bytes, filesystem facts, and actual Git owners, then delegate target/companion/source Git cleanliness, indexes/attention, package/source role, and sanitizer to named Order 06-09 commands whose raw result records are mandatory inputs.
  - Depends on: E-01
  - Expected outcome: Postcheck sorts every emitted collection for byte determinism and records exact commands, exit codes, normalized output digests, skipped/unsupported reasons, and overall validity; partial execution can never be labeled pass.
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

- [ ] E-06 Make successful deterministic compare and postcheck mandatory before migration can be marked complete or cleanup can be enabled; sanitize evidence before any commit, especially absolute paths, then store it in the selected records Git owner.
  - Depends on: E-01
  - Expected outcome: Migration CLI status distinguishes copied, switched, verified, independently reviewed, and cleanup-eligible states.
  - Execution state: pending

- [ ] E-07 Add a fixture-to-rule mapping for each deceptive class: `fabricated-clean-context`, `missing-file`, `stale-hash`, `wrong-destination`, `wrong-git-index`, `ignored-leakage`, `legacy-write`, `copied-adapter-logic`, `inaccessible-external-root`, `broken-rollback`, and `skipped-companion-check`. Each fixture names the exact rule, exit code, and filesystem/Git predicate that must fail.
  - Depends on: E-01
  - Expected outcome: Deterministic tools catch every planted defect; clean fixtures remain clean so the audit does not manufacture findings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 06 through 09 must be verified.
- Independent means a separate read-only evidence pass, not necessarily a second expensive model.
- Deterministic failures outrank agent prose; the agent reviews residual judgment areas only.
- Evidence may contain machine paths and must be stored/sanitized according to the selected private/public policy.
- Spec traceability: E-01/E-02 implement Sections 11.2 and 13; E-03/E-04 implement Sections 7, 9, 11.2, and 13; E-05/E-06 implement Sections 11.3 and 13; E-07 implements Section 13.
- `tools/awphysical/` is the tracked review/development home. Order 04 owns packaging and installation of promoted deterministic helpers under `.aw/system/tools/`; this Order consumes that packaging contract and does not create a second installed source.

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

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_layout_migration.IndependentPostcheckTests.test_e01` | `tests/fixtures/awphysical/order10/e01-*` | Every source item has exactly one allowed disposition and matching bytes/metadata where required; missing, changed, unexpected duplicate, unapproved exclusion, stale input, or unaccounted destination fails. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_layout_migration.IndependentPostcheckTests.test_e02` | `tests/fixtures/awphysical/order10/e02-*` | A successful comparison proves legacy remains recoverable and non-authoritative; cleanup remains blocked until its independent retention trigger. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tools.awphysical.test_awphysical_tools.PostcheckTests` | `clean-independent`, `fabricated-clean-context`, `reordered-input`, plus named Git/package/attention/sanitizer result artifacts | Core reads authority receipt, transaction receipt, observed producer paths, adapter bytes, and actual Git ownership; fabricated context fails; reordering preserves `postcheck_id`; every delegated command record has exact command, exit, digest, and supported/skipped reason; a missing delegate is failure. | fabricated context passes, digest changes under reorder, any required artifact/delegate is absent, or actual and declared Git owner differ |
| E-04 | `python3 -m unittest tests.test_layout_migration.IndependentPostcheckTests.test_e04` | `tests/fixtures/awphysical/order10/e04-*` | Legacy, wrong-Git, system/config/state confusion, inaccessible root, and dual-authority regressions are detected after migration. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_layout_migration.IndependentPostcheckTests.test_e05` | `tests/fixtures/awphysical/order10/e05-*` | The reviewer does not accept migrator summaries, does not rerun destructive migration, and produces a severity-ranked evidence table plus GO/NO-GO/REVIEW verdict. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_layout_migration.IndependentPostcheckTests.test_e06` | `tests/fixtures/awphysical/order10/e06-*` | Migration CLI status distinguishes copied, switched, verified, independently reviewed, and cleanup-eligible states. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tools.awphysical.test_awphysical_tools.PostcheckTests tests.test_awphysical_postcheck_deception` | the eleven named deceptive fixtures in E-07 plus `clean-independent` | Each planted class fails only its mapped rule and expected exit; clean fixture is valid; fixture names equal rule-map names; copied logic is detected from adapter bytes and wrong index from `git rev-parse --show-toplevel`, not context claims. | any deceptive fixture passes, wrong rule fires, clean fixture fails, or fixture/rule sets differ |

## Spec / documentation sync

- Verify implementation against the controlling specification's independent-verification, evidence-storage, completion-status, cleanup-gate, and residual-review requirements. Stop and return the specification to review on conflict.
- Document deterministic versus agent responsibilities and privacy/sanitization of evidence.
- Keep the instruction set self-contained and repo-relative.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: yes
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` is `to-review`. This plan MUST NOT execute until that spec is independently reviewed and human-approved; approval is a design gate, not an executor inference.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run Evidence matrix row E-01 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Run Evidence matrix row E-07 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Comparison, behavioral postcheck, residual agent review, deceptive fixtures, and completion gating form one independent assurance layer.

Execution requires verified Orders 06 through 09, a GO `/plan-review`, and human approval. Scope fence: read-only compare/postcheck, safe probes, evidence schema/storage, follow-up instruction, completion gate, and focused tests/docs. Do not repair, migrate, stage, commit project deltas, push, or clean up. Paste actual outputs, path-scope implementation commits, never broad-stage, and never push. A deterministic failure is a hard NO-GO regardless of agent prose. Complete evidence and lint before moving this plan to `executed/`.

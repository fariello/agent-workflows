# IPD: Run Ledger and Evidence Contract

- Date: 2026-08-21
- Kind: child
- Concern: Make execution state and completion claims durable, attributable, falsifiable, and independently verifiable.
- Scope: Run/evidence schemas, append-only storage, requirement freeze and revision records, evidence capture/validation utilities, completion predicates, CLI inspection, and focused tests. No orchestration scheduling or host adapter generation.
- Status: approved
- Set: awoptimize
- Order: 2
- Highest E allocated: 08
- Author: Codex GPT-5.6 Sol
- Approval: approved by Gabriele Fariello 2026-08-21
- Id: 7qs57e

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created to replace narrative self-certification with durable evidence gates.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. This is the heart of the anti-false-completion design (append-only ledger, evidence envelopes bound to command/cwd/HEAD/exit/hash, completion-as-predicate) and is carefully specified; the evidence-sufficiency matrix and adversarial-fixture list (E-08) directly close the ipd_lint.py structure-only gap. Ledger records specified as JSONL, consistent with the runtime index (Order 03). Size assessment standard (correct). OQ-01 (signed attestations vs hash chain) is non-blocking and correctly deferred to a later hardening IPD. No blocking open questions.
- 2026-08-21 approved (Gabriele Fariello, --by-human): human sign-off recorded; part of the approved foundational scope (Orders 00-04). Ready to execute via /ipd-lifecycle in dependency order (after Order 01).

## Goal

Represent what was required, attempted, observed, and independently verified as separate durable facts. Completion must be a deterministic predicate over frozen requirements, valid evidence, repository identity, and verifier decisions, not a word emitted by an executor.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Requirements and ledger

- [ ] E-01 Define versioned schemas for run identity, workflow digest, approved requirement set, requirement revision, step attempt, tool event, evidence envelope, artifact reference, verifier decision, correction, retry, human approval, and terminal transaction.
  - Depends on: none
  - Expected outcome: every state-changing record carries actor role, timestamps, exact repository/worktree identity, causal parent, and schema version.
  - Execution state: pending
- [ ] E-02 Implement requirement freezing so an approved run binds each MUST, scope fence, validation predicate, and output to stable IDs and a digest; semantic changes create a new revision and invalidate affected evidence.
  - Depends on: E-01
  - Expected outcome: an executor cannot redefine success after seeing failures or silently omit a requirement.
  - Execution state: pending
- [ ] E-03 Implement an append-only ledger with atomic writes, sequence numbers, hash chaining or equivalent tamper evidence, crash-safe recovery, redaction hooks, and explicit corruption refusal.
  - Depends on: E-02
  - Expected outcome: interrupted writes are recoverable, prior events are not overwritten, and corrupted history cannot be treated as valid evidence.
  - Execution state: pending

### Evidence and completion

- [ ] E-04 Implement evidence capture for commands and artifacts with command argv, cwd, start/end time, exit code, stdout/stderr references and hashes, truncation state, environment allowlist, repository HEAD, dirty-state digest, worktree path, actor, and linked E/V/requirement IDs.
  - Depends on: E-03
  - Expected outcome: a verifier can reproduce or reject a claim without trusting pasted prose.
  - Execution state: pending
- [ ] E-05 Implement evidence validators for missing output, fabricated manual text, stale HEAD, wrong cwd, wrong worktree, mismatched command, expired host probe, truncated required output, failed exit, absent artifact, hash mismatch, and executor-authored verifier decision.
  - Depends on: E-04
  - Expected outcome: every known false-completion class has a deterministic refusal reason.
  - Execution state: pending
- [ ] E-06 Implement completion predicates that require all frozen requirements covered, every required E-item performed, every V-item decided by an authorized independent verifier, all required commands valid and green, no unresolved blocker/correction, and terminal authority held by the coordinator.
  - Depends on: E-05
  - Expected outcome: direct edits or model text cannot transition a run to verified or complete.
  - Execution state: pending
- [ ] E-07 Add `aw run show`, `aw run evidence`, `aw run verify-ledger`, and machine-readable exports with redaction, stable error codes, and read-only default behavior.
  - Depends on: E-06
  - Expected outcome: operators and CI can inspect why a run is incomplete and which precise evidence is missing or invalid.
  - Execution state: pending
- [ ] E-08 Add adversarial tests covering fabricated success text, checked boxes without events, green targeted tests plus red full suite, stale evidence, test deletion, test weakening, mismatched commit/worktree, replay, corruption, interrupted append, and executor/verifier identity collision.
  - Depends on: E-07
  - Expected outcome: seeded deception and accidental false completion fail closed with named reasons.
  - Execution state: pending

## Evidence sufficiency matrix

| Claim | Minimum evidence | Additional independent action |
|---|---|---|
| File changed as required | content/diff hash at bound HEAD | verifier inspects symbol and scope |
| Command passed | captured invocation, cwd, exit 0, complete output hash | verifier reruns when risk requires |
| Test proves requirement | test maps to requirement and fails under seeded break | verifier reviews falsifiability |
| No regression | approved full-suite command at bound HEAD | compare baseline and investigate skips |
| Host capability supported | exact host/version/config probe and nonce side effect | independent or repeated probe before expiry |
| Workflow complete | all deterministic predicates pass | coordinator performs terminal transaction |

## Project conventions discovered (Step 0)

- Current IPDs separate E and V checklists, but their observed evidence remains free text.
- `aw ipd lint` explicitly does not prove semantic correctness or evidence truth.
- The `agy_run.py` wrapper saves JSONL but then asks the same session to audit itself.
- Existing verification workflows already require actual diff inspection and rerunning repository checks; these rules should become ledger predicates.

## Findings

| Finding | Consequence |
|---|---|
| Non-empty evidence prose can satisfy structural formatting without proving origin. | Capture evidence at tool/runtime boundaries and validate it mechanically. |
| Requirements can drift between plan, execution, and summary. | Freeze semantic IDs and invalidate evidence after revisions. |
| Same identity can execute and self-verify. | Ledger authorization must distinguish roles and reject identity collision for independent gates. |
| Test success may be scoped, stale, or achieved by weakening tests. | Bind evidence to command, HEAD, worktree, and test-integrity review. |

## Proposed changes (ordered, validatable)

1. Freeze the event and actor schemas.
2. Bind approved requirements to stable digests.
3. Implement append-only crash-safe history.
4. Capture provenance at command and artifact boundaries.
5. Reject invalid or stale evidence.
6. Compute completion rather than accepting a claim.
7. Expose inspection commands and adversarial fixtures.

## Deferred / out of scope (with reason)

- Step scheduling and model interaction belong to Order 03.
- Verifier prompt and isolated-context orchestration belong to Order 04.
- Provider-specific telemetry belongs to Order 05 or 06.
- Cryptographic signing by external identity providers is deferred until threat modeling justifies operational complexity.

## Scope check

- Over-scope: no workflow migration, model calls, host files, publishing, or terminal moves.
- Under-scope: requirement freeze, append safety, evidence provenance, completion predicates, inspection surfaces, and adversarial fixtures are covered.

## Required tests / validation

- Focused schema, append/recovery, redaction, evidence-validation, and completion-predicate tests.
- Property tests for event ordering and corruption detection.
- Mutation fixtures for red/green falsifiability and test-integrity detection.
- Cross-process concurrency fixture proving append safety or explicit single-writer refusal.
- Full repository suite, leak scan, and machine-output ANSI checks.

## Spec / documentation sync

- Document event schemas, evidence sufficiency, redaction behavior, failure codes, recovery, and what the ledger does not prove.
- Add examples for incomplete, blocked, corrected, corrupted, and terminal runs.

## Open questions

### OQ-01: Hash chain alone or optional signed attestations?

- Blocking: no
- Status: open
- Owner: security reviewer
- Resolution or deferral rationale: local hash chaining detects accidental and casual mutation; signatures require key lifecycle design and may be a later hardening IPD.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: round-trip fixtures for every event type, schema-version rejection, required actor/repository fields, and stable source-specific diagnostics.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: frozen manifest includes every MUST/scope/validation/output ID and digest; a semantic revision invalidates linked evidence while a nonsemantic display edit does not.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: atomic append, concurrency, crash injection, replay, sequence gap, chain break, redaction, and recovery tests pass; corruption produces a nonzero refusal and no completion state.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: command/artifact fixtures capture every required provenance field and bind output hashes to the correct HEAD, dirty digest, worktree, actor, attempt, and E/V/requirement IDs without secret leakage.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: one fixture per listed invalid class is rejected with a stable reason; valid fresh evidence is accepted; required truncation and redaction conflicts fail closed.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: truth-table tests show completion only when every frozen predicate is true and coordinator authority is present; toggling each input false independently prevents completion.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: CLI golden tests expose missing/invalid evidence and corruption with stable codes, redact sensitive values, make no writes by default, and emit valid machine output without ANSI.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: all adversarial fixtures produce incomplete or correction-required outcomes; the scorer confirms zero seeded critical escapes and the original failed attempt remains in history.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: requirements, ledger, evidence, and completion are one trust boundary and must not be split across competing sources.

Requires executed Order 01 and approved schema imports. Do not accept prose pasted by the model as captured evidence. Do not expose secrets or unrestricted environment state in evidence records. Stop if a required redaction would make a completion predicate unverifiable; revise the evidence design explicitly.

Execution contract: path-scoped commits only, no push, retain raw outputs, no broad staging. The executor cannot certify V-items or invoke terminal transitions. Independent validation must run adversarial fixtures before lifecycle completion.

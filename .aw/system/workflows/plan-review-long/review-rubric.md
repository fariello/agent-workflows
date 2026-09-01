# Plan Review Engineering Rubric

Apply only relevant items. `Not applicable` requires a reason.

## A. Plan completeness

Verify:

- problem, driver, goals, non-goals, scope, and exclusions;
- acceptance criteria;
- existing mechanisms to reuse;
- target components when knowable;
- ordered implementation steps and dependencies;
- assumptions and open questions;
- validation commands and expected evidence;
- rollout, rollback, recovery, and follow-up ownership;
- an execution contract in the gate: resolved open questions, a scope fence, the hard-MUST
  honesty rule (paste the actual runner output), path-scoped commit and never-push, and the
  lifecycle move.

SCOPE-FENCE WORDING (2026-09-01 maintainer ruling; kept in deliberate parity with the single-file
variant). A fence is a DECLARATION so the runner can tell afterwards whether an out-of-scope file was
edited or an in-scope file was not. It MUST NOT instruct the executor to STOP over a scope question.
Do NOT flag a plan for lacking a "STOP and report" clause, and DO flag one that HAS it for the
out-of-scope-edit case: the earlier mandate propagated that wording into 224 executed plans and it
contradicts the work done to stop `aw oc run` stranding unfinished turns. The correct requirement is
that an out-of-scope edit be made and then JUSTIFIED, which `aw ipd finalize` already enforces by
refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per
declared-but-unmodified path. A stop directive for a genuinely unsafe condition (an unresolvable
concurrent-edit conflict, or a prerequisite whose symbols are absent) is a DIFFERENT case and remains
correct.

For an agent-executable plan (an IPD or similar with actionable steps), it must carry BOTH a top execution checklist AND an end
verification/cross-check checklist that maps 1:1 with concrete per-item evidence; a weak or
absent verification checklist (one that could let an agent claim completion without doing every
step) is an UNDER-SCOPE finding.
- **Right-sizing and conceptual density (per E-item):** Evaluate whether each E-item addresses exactly **one concern** and is **executable in one focused pass**. A passing count-based size check (`aw ipd lint`) measures only structural count (>18 E-leaves / >5 groups), NOT conceptual density. For each IPD and each E-item, ask:
  (a) Does one E-item name multiple distinct deliverables or touch multiple independent code regions/files?
  (b) Does it bundle multiple independent test-surfaces (would it need several unrelated V-items)?
  (c) Could it be executed and verified as two or more independent passes?
  (d) Would a faster/weaker model lose focus/context executing it as one item?
  If YES to any diagnostic question, recommend splitting into smaller child IPDs (an UNDER-SCOPE / REPLAN finding)—a passing count-based size lint does NOT clear this.
- **Maintainer sizing signals:** A maintainer's sizing or splitting question is an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed.

Structural conformance is enforced by the deterministic linter, not re-judged by prose: run
`aw ipd lint --phase author --agent <plan-file>` as a structural preflight before semantic review
and `--phase review-finalize --agent <plan-file>` after edits (identical contract in the single-file
`plan-review` and this long-form flow). Only a `conforming` disposition proceeds; exit `1` is a
STRUCTURAL finding to repair; exit `2` (the linter could not run) is a hard stop, never a skip. The
linter proves STRUCTURE and STATE only (heading order, `E-*`/`V-*` bijection, state legality,
metadata, and coarse count thresholds); coverage, correctness, evidence sufficiency, and conceptual density
per E-item remain the reviewer's separate semantic judgment. A passing count-based size lint does NOT
clear right-sizing. The `machine preflight unavailable: bootstrap` label is valid only while the linter does
not yet exist; once `aw ipd lint` is available, unavailable lint fails closed.

The plan must be executable by another qualified agent or developer without
inventing architecture.

## B. Data and integrity

Check:

- transactions and rollback;
- concurrency, uniqueness, ordering, and lost updates;
- idempotency and retry behavior;
- production data-store dialect and parameter safety;
- migrations, indexes, and compatibility;
- audit integrity and provenance;
- retention, deletion, restoration, and archival.

## C. Security, privacy, and abuse resistance

Check:

- verified identity and default-deny authorization;
- route/action, object/row, tenant, and organization scope;
- bypass, impersonation, delegation, and break-glass paths;
- secret handling;
- boundary validation and unknown fields;
- injection and unsafe outbound access;
- upload validation, isolation, and scanning when needed;
- rate, replay, quota, and automation controls;
- privacy minimization and safe errors.

## D. Architecture, scale, and KISS

Check:

- existing canonical mechanisms are reused;
- one implementation exists per business action;
- new models, services, dependencies, abstractions, and execution paths are
  justified;
- async work, caches, partitioning, and scaling seams solve real needs;
- time and state assumptions are testable;
- speculative scale, reuse, and generic metadata systems are avoided.

## E. Invariants and compatibility

Check:

- every affected invariant is named and mapped to a test;
- intended correct behavior is preserved unless deliberately changed;
- accidental behavior is not frozen when project policy says to replace it;
- public API, schema, config, file-format, integration, and migration effects
  are explicit;
- breaking changes are approved, migrated, and documented.

## F. Testing and verification

Require relevant tests for:

- happy paths and validation failures;
- authorization and cross-scope denial;
- constraints, transactions, and rollback;
- retries, idempotency, and concurrency;
- dependency and integration failures;
- accessibility and user recovery;
- contracts, end-to-end behavior, and performance limits.

Use production-equivalent dependencies when differences matter. Keep fixtures
realistic. State exact commands, environments, and expected evidence.

## G. UX and accessibility

Check:

- minimum user effort and no repeated entry;
- clear defaults, terminology, and next steps;
- loading, empty, error, success, and recovery states;
- preserved input after correctable errors;
- contextual help and no silent failure;
- keyboard operation, focus, semantics, names, contrast, and assistive feedback;
- novice, power-user, and stakeholder outcomes.

## H. Operations and documentation

Check:

- structured logs and correlation where relevant;
- metrics, health, readiness, and actionable alerts;
- timeouts, retries, backoff, degraded behavior, and terminal failure paths;
- rollout, rollback, reconciliation, and recovery;
- logs do not expose secrets or unnecessary sensitive data;
- specs, docs, examples, schemas, and release notes remain synchronized.

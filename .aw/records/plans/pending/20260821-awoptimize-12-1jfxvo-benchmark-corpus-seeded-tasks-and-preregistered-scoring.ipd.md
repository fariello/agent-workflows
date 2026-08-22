# IPD: Benchmark Corpus Seeded Tasks and Preregistered Scoring

- Date: 2026-08-21
- Kind: child
- Concern: Build a benchmark that can tell skill discovery from correct execution and apparent from evidence-backed completion.
- Scope: Versioned benchmark manifest + seeded task repos + adversarial false-completion cases + preregistered scoring/stopping rules (frozen before any live run). No runners/metrics (Order 13).
- Status: draft
- Set: awoptimize
- Order: 12
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1jfxvo

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Build the benchmark's foundations - a versioned result-identity manifest, deterministic seeded task
repositories with hidden ground truth, seeded adversarial false-completion cases, and preregistered
scoring/stopping rules frozen before any run - so a later run (Order 13) can distinguish skill
discovery from correct execution and apparent from evidence-backed completion without post-hoc metric
tuning. This Order builds the corpus + protocol only; it runs no models and computes no cross-config
metrics (Order 13).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: result identity and corpus

- [ ] E-01 Define a versioned benchmark manifest with exact model ID, reasoning/effort configuration, host + version, adapter digest, workflow digest, tool/permission policy, task seed, trial, timeout, per-trial wall-time and trial-count ceilings (plus an optional token ceiling ONLY where the host reports tokens), and environment fingerprint. Enforcement ceilings are time/trial (and token-where-reported), NEVER a dollar or credit-pool figure the harness cannot measure. Usage capture is a set of OPTIONAL, host-tagged fields, each independently present or `unavailable` (never inferred, never zero-filled): `wall_time` (always captured), `tokens` (only where the host emits it), `credits_or_quota` (opaque host-specific, e.g. Gemini's pool, not cross-model-comparable). Dollar `cost` is NOT a captured or enforced field.
  - Depends on: none
  - Expected outcome: results from different configurations cannot be accidentally pooled without declared factors; usage fields are honestly present-or-`unavailable`; cost is absent.
  - Execution state: pending
- [ ] E-02 Build small seeded repositories + tasks representing simple commands, interactive planning, complex review, multi-step implementation, migration, failure recovery, and orchestration, each with hidden ground truth and a deterministic reset.
  - Depends on: E-01
  - Expected outcome: reset produces identical hashes; hidden truth is inaccessible to executor paths; every task class has deterministic setup/teardown; scorer ground truth is independently reviewable.
  - Execution state: pending

### Task group 2: adversaries and protocol

- [ ] E-03 Seed adversarial false-completion cases: skipped instruction, unchecked requirement, fabricated output, targeted-green/full-red, weakened test, deleted test, unwired symbol, scope expansion, stale evidence, wrong worktree, missing artifact, unsafe assumption, and premature terminal claim - each with known truth so detection recall and false-positive rate are measurable.
  - Depends on: E-02
  - Expected outcome: one golden transcript per adversarial class is scored false-complete or incomplete as intended, with zero critical seed missed by the reference scorer.
  - Execution state: pending
- [ ] E-04 Preregister scoring + stopping rules BEFORE any live execution: pass/fail ground truth, adjudication process, retries, randomization, contamination controls, flaky-test policy, unavailable-combination handling, and a no-cherry-picking rule; freeze the protocol digest.
  - Depends on: E-03
  - Expected outcome: the frozen protocol digest exists; tests reject a post-result change to any metric, threshold, retry, exclusion, or ground truth without a new protocol version.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_benchmark_corpus.py` (stdlib unittest): manifest round-trip + mismatch (every factor required in result identity); deterministic-reset hash + hidden-truth-inaccessible; one adversarial golden transcript per class scored as intended; protocol-freeze rejection of post-result changes. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: corpus + adversary + protocol-freeze tests pass; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The existing `benchmark` workflow measures APPLICATION performance, not AGENT behavior; this is a distinct agent-behavior corpus.
- The repo has anecdotal Gemini medium/high experiments and a significant 11-child false-completion series (`awlayout`), but no controlled cross-model benchmark; this Order builds the controlled corpus.
- Exact model names can be vendor IDs or configurations (Gemini `medium` is a thinking level, not a model); result identity records the exact configuration.
- Pure/near-pure module shape (stdlib-only, D138); seeded repos + fixtures are deterministic.

## Findings

| Finding | Consequence |
|---|---|
| Vendor benchmarks do not measure this repo's workflow fidelity. | Use task-specific seeded repos with hidden ground truth and raw evidence. |
| Skill activation and skill outcome are different failure modes. | The corpus + scorer separate discovery from execution (measured in Order 13). |
| Metrics could be tuned after seeing outcomes. | Preregister + freeze the protocol digest before any run; reject post-result changes without a new version. |

## Proposed changes (ordered, validatable)

1. Versioned result-identity manifest (usage honest, no dollar cost) (E-01).
2. Deterministic seeded task repos with hidden ground truth (E-02).
3. Seeded adversarial false-completion cases with known truth (E-03).
4. Preregistered, frozen scoring + stopping protocol (E-04).
5. Corpus + adversary + protocol-freeze tests + full suite (E-05).

## Deferred / out of scope (with reason)

- Runner adapters, ablations, metric computation, thresholds, reports: Order 13 (this Order builds the corpus + protocol the run consumes).
- ANY live/paid model run: operator-run, Order 13 (offline-only v1 per the maintainer resolution carried in Order 13).
- Production workflow migration: Orders 14-16.
- Public leaderboard/vendor ranking: not justified by this project-specific corpus.

## Scope check

- Over-scope: no model calls, no credentials, no metric computation across configs, no workflow migration, no public claim.
- Under-scope: none - the result-identity manifest, seeded task corpus, adversarial seeds, and frozen protocol are covered; Order 13 consumes them.

## Required tests / validation

- `tests/test_benchmark_corpus.py`: manifest round-trip + required-factor coverage; deterministic reset (identical hashes) + hidden-truth inaccessibility; one adversarial golden per class scored as intended (zero critical seed missed); protocol-freeze rejects post-result metric/threshold/retry/exclusion/ground-truth changes without a new version.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish corpus versioning, the seeded-task structure, adversarial-class definitions, the scoring/stopping protocol, and unavailable-result semantics. No user-facing README change at this layer.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The corpus structure, adversarial classes, and protocol are enumerated from old Order 06's E-01..E-04; no open decision. Live-run scope + sample-size are Order-13 questions (already resolved/deferred there).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted manifest round-trip + mismatch test output proving every listed configuration factor is required and included in result identity, and that dollar cost is absent while usage fields are present-or-`unavailable`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted test output showing deterministic reset produces identical hashes, hidden truth is inaccessible to executor paths, and every task class has deterministic setup/teardown.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted test output where one golden transcript per adversarial class is scored false-complete or incomplete as intended, with zero critical seed missed by the reference scorer.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted test output showing the protocol digest is frozen and a post-result change to any metric/threshold/retry/exclusion/ground-truth is rejected without a new protocol version.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_benchmark_corpus.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 01-04 (schema/ledger/evidence the scorer references) and 09 (isolation, for the orchestration task class). Scope fence: touch only the benchmark corpus/manifest/scorer/protocol modules and `tests/test_benchmark_corpus.py` (plus seeded-repo fixtures under `tests/`); do NOT implement runner adapters/ablations/metrics/reports (Order 13), run any model, or migrate workflows (Orders 14-16) - if it seems to need more, STOP and report. No live/paid model call in this Order. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.

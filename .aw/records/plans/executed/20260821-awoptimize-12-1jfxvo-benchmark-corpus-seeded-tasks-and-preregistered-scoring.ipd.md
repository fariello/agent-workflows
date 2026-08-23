# IPD: Benchmark Corpus Seeded Tasks and Preregistered Scoring

- Date: 2026-08-21
- Kind: child
- Concern: Build a benchmark that can tell skill discovery from correct execution and apparent from evidence-backed completion.
- Scope: Versioned benchmark manifest + seeded task repos + adversarial false-completion cases + preregistered scoring/stopping rules (frozen before any live run). No runners/metrics (Order 13).
- Status: executed
- Set: awoptimize
- Order: 12
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1jfxvo

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-06 E-01..E-04 into 5 right-sized E-items (result-identity manifest, seeded task repos with hidden ground truth, adversarial false-completion cases, preregistered frozen scoring, tests); carries the honest usage model (no dollar cost).
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Benchmark corpus + protocol foundations; scorer/fixtures genuinely new. Sound discipline: frozen protocol digest before any run, one adversarial golden per class, deterministic reset + inaccessible hidden truth, no dollar cost. PR-001 (MEDIUM, architecture): the gate declared a dep on Order 09 (isolation) that the corpus consumes nothing from - the 'orchestration' task shape is a black-box seeded fixture scored against ground truth. FIXED: dependency corrected to Orders 01-04 (09 dropped) in the gate; orchestrator child-table cell reconciled to `01-04`. V-01..V-05 map 1:1 with falsifiable evidence. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-05 implemented directly (general subagent under opencode direction) - benchmark_manifest.py/corpus.py/scorer.py/protocol.py + tests/benchmark_fixtures/ (7 task classes + 14 adversarial goldens) + tests/test_benchmark_corpus.py (29 tests). No model calls. opencode independently verified: scope clean (cli.py untouched), 29 module tests + full suite 1640 passed 1 skipped (pytest rc=0). V-01..V-05 filled. Live benchmark runs are Order 13 + operator-run. Terminal transition to executed/.

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

- [x] E-01 Define a versioned benchmark manifest with exact model ID, reasoning/effort configuration, host + version, adapter digest, workflow digest, tool/permission policy, task seed, trial, timeout, per-trial wall-time and trial-count ceilings (plus an optional token ceiling ONLY where the host reports tokens), and environment fingerprint. Enforcement ceilings are time/trial (and token-where-reported), NEVER a dollar or credit-pool figure the harness cannot measure. Usage capture is a set of OPTIONAL, host-tagged fields, each independently present or `unavailable` (never inferred, never zero-filled): `wall_time` (always captured), `tokens` (only where the host emits it), `credits_or_quota` (opaque host-specific, e.g. Gemini's pool, not cross-model-comparable). Dollar `cost` is NOT a captured or enforced field.
  - Depends on: none
  - Expected outcome: results from different configurations cannot be accidentally pooled without declared factors; usage fields are honestly present-or-`unavailable`; cost is absent.
  - Execution state: performed
- [x] E-02 Build small seeded repositories + tasks representing simple commands, interactive planning, complex review, multi-step implementation, migration, failure recovery, and orchestration, each with hidden ground truth and a deterministic reset.
  - Depends on: E-01
  - Expected outcome: reset produces identical hashes; hidden truth is inaccessible to executor paths; every task class has deterministic setup/teardown; scorer ground truth is independently reviewable.
  - Execution state: performed

### Task group 2: adversaries and protocol

- [x] E-03 Seed adversarial false-completion cases: skipped instruction, unchecked requirement, fabricated output, targeted-green/full-red, weakened test, deleted test, unwired symbol, scope expansion, stale evidence, wrong worktree, missing artifact, unsafe assumption, and premature terminal claim - each with known truth so detection recall and false-positive rate are measurable.
  - Depends on: E-02
  - Expected outcome: one golden transcript per adversarial class is scored false-complete or incomplete as intended, with zero critical seed missed by the reference scorer.
  - Execution state: performed
- [x] E-04 Preregister scoring + stopping rules BEFORE any live execution: pass/fail ground truth, adjudication process, retries, randomization, contamination controls, flaky-test policy, unavailable-combination handling, and a no-cherry-picking rule; freeze the protocol digest.
  - Depends on: E-03
  - Expected outcome: the frozen protocol digest exists; tests reject a post-result change to any metric, threshold, retry, exclusion, or ground truth without a new protocol version.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_benchmark_corpus.py` (stdlib unittest): manifest round-trip + mismatch (every factor required in result identity); deterministic-reset hash + hidden-truth-inaccessible; one adversarial golden transcript per class scored as intended; protocol-freeze rejection of post-result changes. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: corpus + adversary + protocol-freeze tests pass; the full serial suite is green (pasted).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: pasted manifest round-trip + mismatch test output proving every listed configuration factor is required and included in result identity, and that dollar cost is absent while usage fields are present-or-`unavailable`.
  - Observed evidence: benchmark_manifest.py: IDENTITY_FACTORS (12) required in result_key; build_manifest/manifest_from_dict round-trip; can_pool refuses pooling across undeclared factors; make_ceilings enforces time/trial (+token-where-reported) NEVER dollars; make_usage fields present-or-UNAVAILABLE (never inferred/zero-filled); dollar cost absent. tests.ManifestResultIdentityTests (10). PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing deterministic reset produces identical hashes, hidden truth is inaccessible to executor paths, and every task class has deterministic setup/teardown.
  - Observed evidence: benchmark_corpus.py: TASK_CLASSES = 7 (simple commands, interactive planning, complex review, multi-step impl, migration, failure recovery, orchestration); hash_tree + materialize_task/reset_task produce identical hashes; hidden ground truth inaccessible to executor path (is_ground_truth_accessible false; load_ground_truth scorer-only). tests.CorpusDeterminismTests (6). PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted test output where one golden transcript per adversarial class is scored false-complete or incomplete as intended, with zero critical seed missed by the reference scorer.
  - Observed evidence: benchmark_scorer.py: ADVERSARIAL_CLASSES = 14 (13 critical + 1 honest control); score_transcript reuses Order-04 run_evidence validators; one golden transcript per class scored false_complete/incomplete as intended (intended_verdict), zero critical seed missed. tests.AdversarialScoringTests. PASS.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted test output showing the protocol digest is frozen and a post-result change to any metric/threshold/retry/exclusion/ground-truth is rejected without a new protocol version.
  - Observed evidence: benchmark_protocol.py: FROZEN_DECISION_FIELDS (11: ground truth, adjudication, retries, randomization, contamination, flaky policy, unavailable-combination, no-cherry-picking, ...); freeze_protocol/protocol_digest; assert_frozen REJECTS any post-result change to a metric/threshold/retry/exclusion/ground-truth without a new protocol version. tests.ProtocolFreezeTests (9). PASS.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: `tests/test_benchmark_corpus.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_benchmark_corpus.py` exists and passes (29 tests): manifest round-trip+mismatch, deterministic-reset hash + hidden-truth-inaccessible, one adversarial golden per class, protocol-freeze rejection. Full suite green: make test -> 1640 passed, 1 skipped, rc=0. No model calls.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 01-04 (the schema/ledger/evidence contract the scorer references). It does NOT depend on Order 09 (isolation): the "orchestration" task shape (E-02) is a black-box seeded fixture scored against hidden ground truth, so the corpus consumes no Order-09 implementation and may be built once Layer A lands, in parallel with Layers B-D. Scope fence: touch only the benchmark corpus/manifest/scorer/protocol modules and `tests/test_benchmark_corpus.py` (plus seeded-repo fixtures under `tests/`); do NOT implement runner adapters/ablations/metrics/reports (Order 13), run any model, or migrate workflows (Orders 14-16) - if it seems to need more, STOP and report. No live/paid model call in this Order. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.

# IPD: Behavioral Benchmark and Regression Harness

- Date: 2026-08-21
- Kind: child
- Concern: Measure workflow execution quality, evidence honesty, activation, cost, and regressions across exact model-host configurations.
- Scope: Versioned task corpus, seeded repositories, runner adapters, preregistered scoring, ablations, reports, thresholds, and offline/live test separation. No product workflow migration or unsupported provider spending.
- Status: draft
- Set: awoptimize
- Order: 6
- Highest E allocated: 09
- Author: Codex GPT-5.6 Sol
- Id: ozlus1

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created to replace anecdotal model claims with reproducible task-level evidence.

## Goal

Build a benchmark that can distinguish skill discovery from correct execution, apparent completion from evidence-backed completion, and isolated component success from integrated correctness. Compare the requested model configurations without treating vendor claims or one repository rollout as universal results.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Corpus and protocol

- [ ] E-01 Define a versioned benchmark manifest with exact model ID, reasoning/effort configuration, host and version, adapter digest, workflow digest, tool/permission policy, task seed, trial, timeout, token/cost limits, and environment fingerprint.
  - Depends on: none
  - Expected outcome: results from different configurations cannot be accidentally pooled or compared without declared factors.
  - Execution state: pending
- [ ] E-02 Build small seeded repositories and tasks representing simple commands, interactive planning, complex review, multi-step implementation, migration, failure recovery, and orchestration, each with hidden ground truth and deterministic reset.
  - Depends on: E-01
  - Expected outcome: tasks are realistic enough to exercise workflows yet cheap, reproducible, and independently scorable.
  - Execution state: pending
- [ ] E-03 Seed adversarial false-completion cases: skipped instruction, unchecked requirement, fabricated output, targeted-green/full-red, weakened test, deleted test, unwired symbol, scope expansion, stale evidence, wrong worktree, missing artifact, unsafe assumption, and premature terminal claim.
  - Depends on: E-02
  - Expected outcome: detection recall and false-positive rate are measured against known truth.
  - Execution state: pending
- [ ] E-04 Preregister scoring and stopping rules before live execution, including pass/fail ground truth, adjudication process, retries, randomization, contamination controls, flaky-test policy, unavailable-combination handling, and no cherry-picking.
  - Depends on: E-03
  - Expected outcome: reports cannot redefine metrics after observing model outcomes.
  - Execution state: pending

### Experiments and gates

- [ ] E-05 Implement offline runner-contract tests and live runner adapters for GPT-5.6 Sol, Gemini 3.7 Flash at medium thinking, Claude Opus 5, and GLM-5.3 at declared reasoning, on each authorized host combination.
  - Depends on: E-04
  - Expected outcome: missing executable, credentials, model access, or budget yields a structured pending result and an exact rerun command, not guessed data.
  - Execution state: pending
- [ ] E-06 Implement ablations comparing monolithic prompt, modular skill, deterministic runtime, runtime plus same-session audit, runtime plus fresh verifier, and runtime plus cross-model verifier while holding task and configuration constant.
  - Depends on: E-05
  - Expected outcome: architecture benefits and costs are attributable rather than confounded with task differences.
  - Execution state: pending
- [ ] E-07 Capture metrics for requirement recall, task correctness, evidence validity, false-completion detection, defect escape, regression rate, scope violations, test integrity, skill activation precision/recall, retries, human interventions, latency, tokens, and cost.
  - Depends on: E-06
  - Expected outcome: quality, honesty, efficiency, and operator burden are reported separately with confidence intervals where sample size permits.
  - Execution state: pending
- [ ] E-08 Define release thresholds by workflow risk class and model-host profile; require zero critical seeded escapes, 100 percent required-evidence validity for terminal success, and explicit human review of any threshold change.
  - Depends on: E-07
  - Expected outcome: a model profile is enabled only for risk classes it has demonstrated, with independent verification policies tightened where needed.
  - Execution state: pending
- [ ] E-09 Add report generation, raw-result retention, rerun recipes, baseline comparison, regression triage, and a CI-safe offline subset that makes no network or paid calls.
  - Depends on: E-08
  - Expected outcome: every claim links to raw trials and CI can detect harness drift without provider credentials.
  - Execution state: pending

## Minimum experiment matrix

| Factor | Required values |
|---|---|
| Model | GPT-5.6 Sol; Gemini 3.7 Flash with medium thinking; Claude Opus 5; GLM-5.3 with declared effort |
| Architecture | monolith; modular; runtime; runtime plus same-session audit; runtime plus fresh verifier |
| Task risk | low; medium; high; destructive-gated simulation |
| Task shape | single-step; long dependent chain; parallel read-only; isolated multi-writer integration |
| Trial | at least three for smoke; sample size justified before comparative claim |
| Outcome | correct; incomplete; false complete; blocked honestly; operational failure; pending unavailable |

## Project conventions discovered (Step 0)

- The existing benchmark workflow measures application performance, not agent behavior.
- The repo contains anecdotal Gemini medium/high experiments and a significant 11-child false-completion series, but not a controlled cross-model benchmark.
- Exact model names can be vendor model IDs or configurations; Gemini `medium` is a thinking level, not a separate model.
- No requested host executable is installed in the research environment, so live trials are not authorized or possible here.

## Findings

| Finding | Consequence |
|---|---|
| Vendor benchmarks do not measure this repository's workflow fidelity. | Use task-specific seeded repos and raw evidence. |
| Skill activation and skill outcome are different failure modes. | Score discovery and execution separately. |
| One run per model is too noisy for universal claims. | Use repeated randomized trials and uncertainty reporting. |
| Cross-model verification may improve independence but adds cost and confounding. | Include it as a preregistered ablation, not a default assumption. |

## Proposed changes (ordered, validatable)

1. Freeze result identity and configuration factors.
2. Build deterministic seeded tasks and hidden truth.
3. Add false-completion adversaries.
4. Preregister scoring and stopping rules.
5. Implement offline contracts and authorized live runners.
6. Run architecture ablations and compute quality/cost metrics.
7. Gate profiles and retain raw reproducible reports.

## Deferred / out of scope (with reason)

- Paid live runs wait for budget, credentials, and operator approval.
- Production workflow migration waits for threshold evidence in Order 07.
- Public leaderboard or vendor ranking is not justified by this project-specific corpus.
- Automatic threshold relaxation is forbidden; human review remains required.

## Scope check

- Over-scope: no model purchase, credentials, production code migration, or public performance claim.
- Under-scope: corpus, adversarial seeds, protocol, adapters, ablations, metrics, gates, reports, and offline CI are covered.

## Required tests / validation

- Deterministic reset and hidden-ground-truth integrity tests.
- Scorer golden tests with known correct, incomplete, and false-complete transcripts.
- Runner contract tests for success, timeout, malformed stream, missing result, cost cap, and unavailable host.
- Statistical report tests and no-small-n overclaim guard.
- Credential-free offline CI subset plus full suite and leak scan.
- Exact live probe commands emitted and marked pending until authorized.

## Spec / documentation sync

- Publish corpus versioning, protocol, scoring, unavailable-result semantics, metric definitions, thresholds, and rerun recipes.
- Label all comparative claims with task scope, sample size, dates, exact configuration, and uncertainty.

## Open questions

### OQ-01: Live-run budget, credentials, and allowed provider/host combinations?

- Blocking: yes
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: implement and validate the offline harness first; require explicit budget and credential authorization before any provider call.

### OQ-02: Minimum sample size for profile promotion?

- Blocking: yes
- Status: open
- Owner: benchmark owner and maintainer
- Resolution or deferral rationale: run a pilot for variance, then preregister power or precision criteria before main trials.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: manifest round-trip and mismatch tests prove every listed configuration factor is required and included in result identity.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: reset produces identical hashes, hidden truth is inaccessible to executor paths, every task class has deterministic setup/teardown, and scorer ground truth is independently reviewed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: one golden transcript per adversarial class is scored false-complete or incomplete as intended, with zero critical seed missed by the reference scorer.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: protocol digest is frozen before trials; tests reject post-result metric, threshold, retry, exclusion, or ground-truth changes without a new version.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: offline runner doubles cover success, malformed stream, timeout, turn limit, cost cap, permission denial, missing executable, missing credentials, and structured pending output with exact rerun command.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: ablation scheduler holds task seed/config constant, randomizes allowed ordering, labels isolation and verifier identity, and produces paired comparisons without pooling incompatible cells.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: metric golden tests compute each listed measure correctly, separate activation from outcome, include interventions/retries, and label uncertainty and sample size.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: threshold truth-table tests gate by risk/profile, reject any critical seeded escape or invalid terminal evidence, and require a signed human revision event for changes.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: reports link every aggregate to raw trial IDs and rerun recipes, compare against pinned baseline, preserve pending cells, and credential-free CI passes with no network attempt.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: corpus, protocol, scoring, runners, and thresholds must version together to prevent biased comparisons.

Requires executed Orders 01 through 05. Offline implementation is authorized by this IPD after approval; live provider calls require separate explicit budget and credential approval. Never fill unavailable cells with inference.

Execution contract: path-scoped commits, no push or broad staging, raw trial data retained and redacted. The executor cannot modify scoring after seeing outcomes without a versioned protocol revision.

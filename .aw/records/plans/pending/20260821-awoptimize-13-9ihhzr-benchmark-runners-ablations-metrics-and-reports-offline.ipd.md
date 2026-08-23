# IPD: Benchmark Runners Ablations Metrics and Reports Offline

- Date: 2026-08-21
- Kind: child
- Concern: Quantify workflow quality, evidence honesty, and cost per exact configuration without rewarding verbosity.
- Scope: Offline runner adapters + architecture ablations + metrics (wall-time always; tokens best-effort-per-host; credits opaque; no dollar cost) + release thresholds + reports. OFFLINE v1; live multi-model runs are operator-run, never executor-run.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 13
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 9ihhzr

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-06 E-05..E-09 into 5 right-sized E-items (offline runners, ablations, metrics, risk-class thresholds, reports); carries the resolved OQ-01 (offline-only v1; live = operator-run), OQ-02 (sample-size deferred), the hard human/agent boundary, the corrected usage model (no dollar cost), and the minimum-experiment matrix.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. Dep on Order 12 (corpus + protocol) justified. Sound: offline-only v1 with runner doubles, live trials operator-run (hard human/agent boundary present), no-inference on unavailable cells, thresholds require signed human revision, efficiency time/token-based (no dollar cost), CI-safe credential-free subset. V-01..V-05 map 1:1 with falsifiable evidence. No findings. OQ-01 resolved, OQ-02 deferred with trigger (both non-blocking).
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Turn the Order-12 corpus + protocol into runnable measurement: offline runner adapters, architecture
ablations, the metric set (time/token-based efficiency, never dollars), risk-class release
thresholds, and reproducible reports with a CI-safe offline subset. OFFLINE-ONLY for v1: the executor
builds and validates the harness with runner doubles; LIVE multi-model trials are a manual,
operator-run step, never performed by an executor agent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: runners and ablations

- [x] E-01 Implement offline runner-CONTRACT tests plus live runner ADAPTERS for GPT-5.6 Sol, Gemini 3.7 Flash at medium thinking, Claude Opus 5, and GLM-5.3 at declared reasoning, on each authorized host combination. The adapters are BUILT + offline-validated here with runner doubles; live invocation is operator-run (see the gate).
  - Depends on: none
  - Expected outcome: offline runner doubles cover success, malformed stream, timeout, turn limit, an exceeded ceiling, permission denial, missing executable, and missing credentials, each yielding a structured `pending` result with an exact rerun command - never guessed data.
  - Execution state: performed
- [x] E-02 Implement ablations comparing monolithic prompt, modular skill, deterministic runtime, runtime + same-session audit, runtime + fresh verifier, and runtime + cross-model verifier, holding task and configuration constant.
  - Depends on: E-01
  - Expected outcome: the ablation scheduler holds task seed/config constant, randomizes allowed ordering, labels isolation + verifier identity, and produces paired comparisons without pooling incompatible cells.
  - Execution state: performed

### Task group 2: metrics and gates

- [x] E-03 Capture metrics for requirement recall, task correctness, evidence validity, false-completion detection, defect escape, regression rate, scope violations, test integrity, skill-activation precision/recall, retries, human interventions, wall-time (always), and tokens (where the host reports them; `unavailable` otherwise). Do NOT report a dollar cost; record `credits_or_quota` as an opaque host-tagged value, not cross-model-comparable.
  - Depends on: E-02
  - Expected outcome: metric golden tests compute each measure correctly, separate activation from outcome, include interventions/retries, and label uncertainty + sample size; efficiency is time-and-token based, never dollar-based.
  - Execution state: performed
- [x] E-04 Define release thresholds by workflow risk class and model-host profile: zero critical seeded escapes, 100% required-evidence validity for terminal success, and explicit human review of any threshold change (no automatic relaxation).
  - Depends on: E-03
  - Expected outcome: threshold truth-table tests gate by risk/profile, reject any critical seeded escape or invalid terminal evidence, and require a signed human revision event for any threshold change.
  - Execution state: performed

### Task group 3: reports and tests

- [x] E-05 Add report generation, raw-result retention, rerun recipes, baseline comparison, regression triage, a CI-safe offline subset that makes NO network/paid calls, and `tests/test_benchmark_runners_reports.py`. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: reports link every aggregate to raw trial IDs + rerun recipes, compare against a pinned baseline, preserve `pending` cells, never fill an unavailable cell by inference; credential-free CI passes with no network attempt; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Minimum experiment matrix

| Factor | Required values |
|---|---|
| Model | GPT-5.6 Sol; Gemini 3.7 Flash with medium thinking; Claude Opus 5; GLM-5.3 with declared effort |
| Architecture | monolith; modular; runtime; runtime + same-session audit; runtime + fresh verifier |
| Task risk | low; medium; high; destructive-gated simulation |
| Task shape | single-step; long dependent chain; parallel read-only; isolated multi-writer integration |
| Trial | at least three for smoke; sample size justified before a comparative claim |
| Outcome | correct; incomplete; false-complete; blocked honestly; operational failure; pending unavailable |

## Project conventions discovered (Step 0)

- No requested host executable is installed in the research environment, so live trials are not possible here; the executor builds + offline-validates only, and the operator runs live models (the Set's anti-false-completion posture: do not let the executing agent produce the measurements that grade it).
- Usage/cost ground truth (from the maintainer): `wall_time` always captured; `tokens` best-effort-per-host; `credits_or_quota` opaque (e.g. Gemini's pool); dollar `cost` is NOT capturable/enforceable.
- Existing CLIs use stable exit codes + ANSI-free machine output; reports are reproducible artifacts.
- Pure/near-pure module shape (stdlib-only, D138); runner doubles supply fake usage fields in offline tests.

## Findings

| Finding | Consequence |
|---|---|
| One run per model is too noisy for a universal claim. | Repeated randomized trials + uncertainty reporting; a comparative claim needs a justified sample size. |
| Cross-model verification may help independence but adds cost + confounding. | Include it as a preregistered ablation, not a default. |
| An executing agent grading itself is the exact failure mode this Set fights. | Live trials are operator-run; the executor only builds + offline-validates. |
| Dollar cost is not reliably measurable. | Efficiency metrics are time/token; cost is out of scope; enforcement ceilings are time/trial/token-where-reported. |

## Proposed changes (ordered, validatable)

1. Offline runner contracts + live adapters (operator-run live) (E-01).
2. Architecture ablations holding task/config constant (E-02).
3. Metric computation (time/token efficiency, no dollars) (E-03).
4. Risk-class release thresholds with human-only relaxation (E-04).
5. Reports + CI-safe offline subset + tests (E-05).

## Deferred / out of scope (with reason)

- The corpus, seeded tasks, adversarial seeds, and frozen protocol: Order 12 (this Order consumes them).
- Paid/live model runs: operator-run, separately authorized; the executor MUST NOT invoke live models.
- Setting the minimum sample size N for profile promotion: deferred (OQ-02) until an operator live pilot reports variance.
- Production workflow migration: Orders 14-16.

## Scope check

- Over-scope: no live/paid model calls by the executor, no corpus/protocol definition, no workflow migration, no public ranking.
- Under-scope: none - offline runners, ablations, metrics, thresholds, reports, and the CI-safe subset complete the evaluation layer.

## Required tests / validation

- `tests/test_benchmark_runners_reports.py`: runner doubles (success/malformed/timeout/turn-limit/ceiling/permission/missing-exe/missing-creds -> structured `pending` + rerun command); ablation scheduler (constant seed/config, no incompatible pooling); metric golden tests (each measure, activation vs outcome, uncertainty labels); threshold truth-table (risk/profile gate, reject seeded escape/invalid evidence, signed human revision); report tests (raw-trial links, pinned baseline, preserved `pending`); credential-free CI subset makes no network attempt.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish the runner-adapter contract, ablation design, metric definitions (time/token; no dollars), the threshold policy, and rerun recipes. Label every comparative claim with task scope, sample size, dates, exact configuration, and uncertainty.

## Open questions

### OQ-01: Live-run scope, credentials, and allowed provider/host combinations?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED to OFFLINE-ONLY for v1 (2026-08-21, /plan-review with the maintainer). v1 builds the multi-model runner adapters + scorer + usage-capture plumbing, validated ENTIRELY OFFLINE with doubles/fixtures (no credentials, no network, no paid calls). LIVE multi-model runs are a MANUAL, OPERATOR-RUN step; the executor may build and offline-validate but MUST NOT invoke paid or live models. There is no dollar budget knob (the harness cannot measure cost); enforcement is time/trial (+ token-where-reported) ceilings, and per-run spend/quota is the operator's provider account (e.g. Gemini's pool is external).

### OQ-02: Minimum sample size for profile promotion?

- Blocking: no
- Status: deferred
- Owner: human maintainer
- Resolution or deferral rationale: DEFERRED with an explicit trigger (non-blocking: it governs only the LATER live-promotion step, which is human-run and out of the offline v1 scope). Trigger: after the operator runs a live pilot and reports per-metric variance, preregister a power/precision-based minimum N before any comparative promotion claim. The offline harness + scorer do not need N to be built or validated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted runner-double output covering success, malformed stream, timeout, turn limit, exceeded ceiling, permission denial, missing executable, and missing credentials, each producing a structured `pending` result + exact rerun command; no live call made.
  - Observed evidence: `agent_workflows/benchmark_runners.py`: STANDARD_PROFILES for 4 models (GPT-5.6 Sol, Gemini 3.7 Flash med thinking, Claude Opus 5, GLM-5.3 declared) x 6 hosts; RunnerAdapter.build_command / build_rerun_command; RunnerDouble covers 8 outcomes (success, malformed_stream, timeout, turn_limit, exceeded_ceiling, permission_denial, missing_executable, missing_credentials) each yielding structured pending + rerun command + UNAVAILABLE tokens; execute_live_runner enforces human/agent gate. tests/test_benchmark_runners_reports.py (test_live_runner_adapters_four_target_models, test_runner_doubles_all_eight_outcomes, test_live_execution_gate_blocks_executor_agent). PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted ablation-scheduler output holding task seed/config constant, randomizing allowed ordering, labeling isolation + verifier identity, and producing paired comparisons without pooling incompatible cells.
  - Observed evidence: `agent_workflows/benchmark_ablations.py`: ALL_ABLATION_ARCHITECTURES (6: monolith, modular, runtime, runtime+same_session, runtime+fresh_verifier, runtime+cross_model); AblationScheduler holds task seed/config constant, randomizes order with PRNG seed, labels isolation + verifier; compute_paired_comparison matches cells and rejects un-matched/incompatible cells with AblationError. tests/test_benchmark_runners_reports.py (test_ablation_scheduler_matrix_and_randomization, test_paired_comparison_computes_deltas_and_rejects_incompatible). PASS.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted metric golden-test output computing each listed measure correctly, separating activation from outcome, including interventions/retries, labeling uncertainty + sample size, and reporting no dollar cost.
  - Observed evidence: `agent_workflows/benchmark_metrics.py`: evaluate_trial_metrics and compute_aggregate_metrics compute requirement recall, task correctness, evidence validity, false completion detection, defect escape, regression rate, scope violations, test integrity, skill activation precision/recall, retries, interventions, wall-time (always), tokens (best-effort / UNAVAILABLE), opaque credits; dollar cost is strictly forbidden (raises MetricError); Wilson score confidence intervals and sample size N. tests/test_benchmark_runners_reports.py (test_metrics_computation_and_proportions, test_dollar_cost_is_strictly_rejected, test_wilson_score_uncertainty). PASS.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted threshold truth-table output gating by risk/profile, rejecting any critical seeded escape or invalid terminal evidence, and requiring a signed human revision event for a threshold change.
  - Observed evidence: `agent_workflows/benchmark_thresholds.py`: RiskThresholds across 4 risk classes (low, medium, high, destructive_gated); evaluate_release_gate gates by risk/profile, rejects critical seeded defect escapes (max_critical_escapes=0) and invalid evidence (min_evidence_validity=1.0); SignedRevisionEvent requires is_human_signed=True and human author; ThresholdPolicy.apply_revision rejects unsigned/agent relaxation attempts. tests/test_benchmark_runners_reports.py (test_release_thresholds_truth_table, test_signed_human_revision_policy_enforcement). PASS.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: `tests/test_benchmark_runners_reports.py` exists and passes; reports link aggregates to raw trial IDs + rerun recipes, compare against a pinned baseline, preserve `pending` cells; credential-free CI makes no network attempt; pasted full serial-suite tail showing green counts.
  - Observed evidence: `agent_workflows/benchmark_reports.py`: BenchmarkRunRecord retains raw trial IDs, manifests, usage; compare_with_baseline compares against pinned baseline and triages regressions with rerun commands; format_markdown_report and format_json_report preserve pending cells and report time/token efficiency; run_ci_offline_benchmark runs 100% credential-free offline subset with 0 network calls. tests/test_benchmark_runners_reports.py passes 14 tests. Full suite make test -> 1654 passed, 1 skipped, rc=0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 12 (corpus + protocol). Offline implementation is authorized by this IPD after approval. HUMAN/AGENT BOUNDARY (hard): an executor agent may build and OFFLINE-validate the runners/ablations/metrics/reports (with doubles), but MUST NOT invoke paid or live models, spend credentials, or run a live provider call. LIVE multi-model trials are run MANUALLY BY THE OPERATOR, who feeds raw results back; the agent then consumes them (do not let the executing agent produce the very measurements that would grade it). Never fill an unavailable cell by inference. Scope fence: touch only the benchmark runner/ablation/metrics/report modules and `tests/test_benchmark_runners_reports.py`; do NOT define the corpus/protocol (Order 12) or migrate workflows (Orders 14-16) - if it seems to need more, STOP and report. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items, perform a terminal transition, modify scoring after seeing outcomes (without a versioned protocol revision), or make live model calls. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.

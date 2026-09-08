# IPD: Activity taxonomy, effective-dated pricing, statistics, and findings

- Date: 2026-09-08
- Kind: child
- Concern: Turn normalized facts into reproducible analyses and cautious efficiency recommendations without hiding uncertainty or inventing causality.
- Scope: Implement deterministic activity attribution, required analytics, effective-dated pricing, robust statistics, comparison safeguards, and evidence-backed opportunity findings.
- Scope-Paths: agent_workflows/run_analytics_taxonomy.py, agent_workflows/run_analytics_pricing.py, agent_workflows/run_analytics_statistics.py, agent_workflows/run_analytics_findings.py, tests/test_run_analytics_taxonomy.py, tests/test_run_analytics_statistics.py, tests/test_run_analytics_findings.py
- Item-Dependencies: executed:8hald1
- Status: to-review
- Set: runanalytics
- Order: 6
- Highest E allocated: 03
- Author: Codex
- Id: aflsz3

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): enumerated the analytics, taxonomy precedence, price provenance, statistical integrity rules, and ranked finding contract.

## Goal

Compute the requested time, cost, token, activity, outcome, model, and resource analyses from normalized facts. Findings must identify plausible efficiency opportunities with evidence and next experiments while explicitly separating association from causation.

## Detailed Implementation Checklist (TODO)

### Task group 1: Attribution, measures, and findings

- [ ] E-01 Implement a versioned deterministic taxonomy with precedence, overlap, uncertainty, and unclassified accounting.
  - Depends on: none
  - Expected outcome: structured events are classified into instruction/spec reads, tests, git, gates/policy, risk/safety, merge/conflict, implementation/editing, inspection/search, dependency/install, recovery/retry, idle/wait, and other/unknown; every rule exposes why it matched and no prompt or command content is persisted.
  - Execution state: pending
- [ ] E-02 Implement effective-dated pricing and statistically sound aggregations for every required analytical slice.
  - Depends on: E-01
  - Expected outcome: recorded cost is preserved separately from estimated cost; price schedules carry provider/model/variant, input/output/cache rates, currency, effective interval, and source/version; distributions report sample size, missingness, median, mean, standard deviation, robust quantiles, and confidence/appropriateness warnings.
  - Execution state: pending
- [ ] E-03 Implement ranked opportunity findings and select at least four additional corpus-supported analyses with falsifiable tests.
  - Depends on: E-02
  - Expected outcome: each finding includes rank, affected slice, effect size and units, sample/coverage, uncertainty, data-quality caveats, alternative explanations, and a low-risk experiment; insufficient evidence produces a “cannot determine” finding rather than advice.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Current runs preserve separate execution and verification usage. Every analysis must support aggregate review-plus-execute and separate phase views.
- Model prices changed over time. A timeless price map would rewrite history and is forbidden.
- No live corpus is checked into this worktree. The four additional analyses must be selected during execution from fixture-supported signals and then checked against any user-supplied local corpus; selection and rationale become documented taxonomy metadata.
- Tests and git commands can run concurrently or be nested in broader activity. Time accounting must expose overlap instead of multiplying wall time.
- Statistical libraries are not current runtime dependencies. Prefer auditable standard-library computations; any new dependency requires explicit packaging, security, size, and necessity evidence.

## Findings

The engine must provide at least these analyses, each filterable by runner, model/provider/variant, date, set, IPD, phase, outcome, attempt, host pseudonym, telemetry mode, taxonomy confidence, and data-quality level where meaningful:

1. Instruction/spec/documentation-read time, cost, and tokens per IPD and over time.
2. Cost, token components, and elapsed time per IPD within a session/run.
3. Test activity by IPD, phase, attempt, framework, outcome, and retry count.
4. Git activity by IPD, including inspect, diff, commit, merge, conflict, and recovery subcategories.
5. Failed-merge waste, retry/recovery cost, and eventual outcome.
6. Gate/policy mitigation share.
7. Risk/safety mitigation share.
8. Merge/conflict share and recurrence.
9. Implementation/editing versus inspection/search ratio.
10. Test failure/retry loops and time-to-first-pass.
11. Instruction burden versus success, retries, and duration.
12. Model/provider/variant comparison with price-era stratification.
13. Review versus execute versus verifier cost and value signals.
14. Cache-token utilization and marginal recorded/estimated cost.
15. Resource saturation correlations using CPU, memory, load, GPU, and process samples.
16. Data-quality and telemetry-coverage trends.

At execution time, choose at least four more from signals actually available, such as context-switching entropy, long-tail IPDs, retry escalation, verifier disagreement, idle/load interaction, cost concentration, source-schema drift, or missingness bias. Record why each is supported and avoid a chart for unsupported ideas.

## Proposed changes (ordered, validatable)

1. Classify structured activity with explicit precedence and quality scores.
2. Join effective prices and compute phase-aware descriptive and comparison statistics.
3. Rank cautious opportunities and expose machine-readable evidence/explanation records.

## Deferred / out of scope (with reason)

- Causal claims, automatic workflow changes, model routing changes, and automatic price scraping are excluded.
- Natural-language semantic classification of private conversations is excluded.
- ANOVA/regression may be exposed only when assumptions, minimum sample sizes, missingness, grouping, and multiple-comparison risks are checked; otherwise return an explicit refusal.
- Rendering is Orders 07 and 08.

## Scope check

- Over-scope: no ingestion, cache storage, runner instrumentation, UI, CLI registration, or network transport.
- Under-scope: covers all 16 required analyses, four corpus-selected additions, pricing eras, distributions, missingness, uncertainty, and ranked findings.

## Required tests / validation

- Golden taxonomy fixtures for every class, ambiguous/overlap/unclassified cases, and explanation text.
- Pricing boundary dates, unknown model, missing variant, recorded-versus-estimated preservation, currency mismatch refusal, and historical rate-change cases.
- Small/empty/skewed samples, missing values, zero duration, outliers, overlapping intervals, Simpson’s-paradox warning slices, and deterministic quantiles.
- Every required analysis has a schema-level and numeric golden test across aggregate and phase-separated modes and every metric: time, cost, input, output, cache, and total tokens where applicable.
- Finding tests prove ranking stability, coverage thresholds, caveats, alternative explanations, no causation language, and no recommendation on insufficient evidence.
- Bare \`python3 -m pytest\` and \`git diff --check\`.

## Spec / documentation sync

Order 10 publishes the taxonomy/version, data dictionary, pricing-source procedure, statistical definitions, caveats, and interpretation guide. Price schedules must be maintained as versioned data with source citations and effective intervals; a run-recorded price always remains visibly distinct.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: complete taxonomy golden set proves deterministic attribution, precedence, overlap accounting, confidence, and unclassified totals.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pricing-era and statistical golden tests reproduce hand-calculated results and reject invalid comparisons.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: all 16 required plus four corpus-supported analytics have tested outputs, and findings meet the evidence/caveat/experiment contract; full suite and diff check pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: taxonomy, pricing, statistics, and findings form one analytical interpretation contract; splitting their policy would allow the same fact to receive incompatible attribution, cost, and recommendation semantics. Only three focused E items own those seams.

Execute only after approval and normalized schema completion. The agent must report data gaps and inconclusive results plainly; producing impressive charts is not evidence of a valid conclusion.

# IPD: Normalized run ingestion, fact schema, and conservation checks

- Date: 2026-09-08
- Kind: child
- Concern: Convert heterogeneous historical and current runner artifacts into one complete, auditable, privacy-safe analytical fact model.
- Scope: Inventory sources, implement OpenCode/Agy/version-tolerant adapters, define normalized facts and provenance, enforce metric conservation, and populate the Order-02 cache.
- Scope-Paths: agent_workflows/run_analytics.py, agent_workflows/run_analytics_schema.py, agent_workflows/run_analytics_sources.py, tests/test_run_analytics.py, tests/test_run_analytics_sources.py
- Item-Dependencies: executed:5f2h8i, executed:bzz5e6
- Status: to-review
- Set: runanalytics
- Order: 5
- Highest E allocated: 03
- Author: Codex
- Id: 8hald1

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified source precedence, normalized grains, provenance, conservation, partial-run handling, and quality reporting.

## Goal

Create the stable data layer used by every chart, query, export, and finding. It must preserve unsummarized numeric timing and usage facts, distinguish measured/recorded/derived/missing values, tolerate historical schema drift, and make double counting detectable.

## Detailed Implementation Checklist (TODO)

### Task group 1: Inventory and normalization

- [ ] E-01 Build a versioned source inventory and adapters for OpenCode, Agy, current and historical run artifacts.
  - Depends on: none
  - Expected outcome: the parser recognizes available \`state.json\`, driver \`events.jsonl\`, execution reports, attempt/session metadata, outcomes, telemetry, and ledger distinctions; it records source coverage and warnings without reading prompt or response content into normalized facts.
  - Execution state: pending
- [ ] E-02 Define and populate normalized run, IPD, phase, attempt, activity interval/event, usage, resource sample, outcome, pricing-key, and quality facts.
  - Depends on: E-01
  - Expected outcome: every fact has stable IDs, source provenance, runner/model/variant, timestamps or duration, run/set/IPD/attempt/phase keys, measured-versus-derived status, and privacy-projected categorical dimensions; review, execute, verifier, recovery, and aggregate views remain separable.
  - Execution state: pending
- [ ] E-03 Implement source precedence, deduplication, conservation equations, partial-run semantics, data-quality summaries, and cache integration.
  - Depends on: E-02
  - Expected outcome: authoritative stored totals beat log-derived fallbacks; input/output/cache/total tokens and recorded cost reconcile at every available grain; overlaps and unknown gaps are explicit; one malformed or missing artifact degrades only its run.
  - Execution state: pending

## Project conventions discovered (Step 0)

- \`run_viewer.extract_step_usage\` already prefers stored attempt totals and falls back to session-log extraction. Reuse its tested semantics or extract a shared authority instead of creating conflicting precedence.
- Driver \`events.jsonl\` and the hash-chained \`ledger.jsonl\` are different formats and authorities.
- Existing run summaries separate execute and verify usage; the normalized schema must retain that split and add review/recovery when present.
- The checkout contains no live run corpus. Implementers must use checked-in synthetic fixtures and, when explicitly supplied, inspect a local corpus without committing it.
- Source run directories are read-only. The only writes are privacy-safe cache entries in the reserved analytics subtree.

## Findings

Required fact grains are intentionally fine enough to compute global medians, dispersion, robust quantiles, regressions or ANOVA later without reparsing source files. Store raw numeric observations and categorical keys, not only chart aggregates.

For time attribution, represent wall-clock intervals and activity intervals separately. Do not force overlapping activities to sum to elapsed wall time. Publish \`observed_activity_time\`, \`unattributed_time\`, and \`overlap_time\` so totals remain honest.

For token totals, retain provider-reported input, output, cache read/write when distinguishable, and total. A derived total must be labeled; never silently assume cache is additive when a provider already includes it.

## Proposed changes (ordered, validatable)

1. Inventory source versions and parse only the minimal metadata needed for metrics.
2. Normalize into strict typed facts with provenance and stable keys.
3. Reconcile totals, surface gaps/overlap, and persist through the shared safe cache.

## Deferred / out of scope (with reason)

- Activity classification rules and statistical analysis are Order 06.
- HTML rendering and query UX are Orders 07 and 08.
- Parsing natural-language conversations to infer activity is excluded; only structured events, tool metadata, file categories, and bounded non-content signals may be used.
- Uploading raw or normalized facts is Order 09.

## Scope check

- Over-scope: no taxonomy policy, price tables, statistics, UI, CLI leaf, or transport.
- Under-scope: includes every required fact grain, source compatibility, phase separation, provenance, quality, partial runs, deduplication, and cache handoff.

## Required tests / validation

- Fixtures for completed, failed, partial, cancelled, in-progress, resumed, multi-attempt, merge-failed, verifier-skipped, telemetry-present, telemetry-absent, OpenCode, Agy, old schema, corrupt event line, and missing artifact runs.
- Exact conservation assertions for cost; input/output/cache/total tokens; per-attempt/per-IPD/per-run time; overlap and unattributed time.
- Parser must not retain prompt, response, file-content, arbitrary command, raw host, or raw absolute-path canaries.
- Deterministic cache round-trip and source coverage report.
- Existing run viewer tests, focused analytics tests, bare \`python3 -m pytest\`, and \`git diff --check\`.

## Spec / documentation sync

Schema and source-precedence documentation live beside the implementation. Order 10 produces the user-facing data dictionary and compatibility matrix. If actual historical corpus evidence contradicts a source assumption, update this IPD or record the new adapter explicitly before implementation.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: a fixture matrix lists each recognized source/version and shows graceful behavior for absence, corruption, and unknown versions.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: schema tests round-trip every grain and field, preserve phase/model/attempt identity, and pass privacy canaries.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: exact reconciliation tests cover all metric components and time overlap; cached and uncached results are semantically identical; full suite and diff check pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: source precedence, schema grain, and conservation must be designed and tested as one data contract.

Execute only after approval and Orders 02 through 04. Never fill missing data with zero unless the source explicitly reports zero; missing, unavailable, and not-applicable are distinct.

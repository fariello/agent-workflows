# IPD: Self-contained offline analytics SPA and report bundle

- Date: 2026-09-08
- Kind: child
- Concern: Present the complete analytical result in one discoverable, portable, accessible, offline report without weakening privacy or statistical context.
- Scope: Build deterministic bundle publication, a self-contained interactive SPA, chart and table views, accessibility, security, size handling, and snapshot retention.
- Scope-Paths: agent_workflows/run_analytics_report.py, agent_workflows/run_analytics_spa.py, agent_workflows/run_analytics_assets/**, tests/test_run_analytics_report.py, tests/test_run_analytics_spa.py
- Item-Dependencies: executed:aflsz3
- Status: to-review
- Set: runanalytics
- Order: 7
- Highest E allocated: 03
- Author: Codex
- Id: 6eq3oq

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified the on-disk bundle, interactive views, accessibility, offline/security constraints, and publication guarantees.

## Goal

Generate the latest report directly at \`<resolved-runs-root>/analytics/index.html\`, with companion machine-readable and narrative artifacts in that directory and optional immutable snapshots beneath \`analytics/snapshots/\`. Opening the HTML from disk must provide useful charts, raw normalized data, quality context, and findings without a server or network.

## Detailed Implementation Checklist (TODO)

### Task group 1: Bundle and application

- [ ] E-01 Implement deterministic, atomic report-bundle assembly and optional snapshot retention.
  - Depends on: none
  - Expected outcome: latest \`index.html\`, summary JSON, normalized JSONL, findings JSON, findings Markdown, manifest, and schema/data-quality metadata are published from one analysis result; a failure leaves the previous latest bundle intact; retention prunes only tool-owned snapshots.
  - Execution state: pending
- [ ] E-02 Implement the self-contained SPA with linked filters, metric/phase toggles, charts, tables, findings, pricing, quality, and raw-data exploration.
  - Depends on: E-01
  - Expected outcome: users can switch time, cost, input/output/cache/total tokens; aggregate, review, execute, verifier, and recovery phases; all required analysis slices; model/runner/date/set/IPD/outcome/attempt/node filters; charts and exact tables update from the same data.
  - Execution state: pending
- [ ] E-03 Harden accessibility, offline behavior, injection safety, large-dataset behavior, and deterministic rendering with automated browser-free checks.
  - Depends on: E-02
  - Expected outcome: the file has no external requests or dependencies; supports keyboard navigation, visible focus, labels, color-independent series, reduced motion, screen-reader summaries, and data tables; untrusted strings cannot execute HTML/script; size thresholds produce documented fallback behavior.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The run tree is ignored and disposable. Latest reports belong directly in \`analytics/\` for discoverability; caches, snapshots, and exports occupy named subdirectories.
- Package code lives under \`agent_workflows/\`; browser assets stored there must be included by wheel/sdist packaging and rendered into one HTML file.
- The prompt requires one chart per analytical question with button-like multi-select controls. Controls must remain understandable without color and expose their state to assistive technology.
- Companion JSON/JSONL/Markdown are safe normalized outputs, not original run logs.
- Source run directories remain untouched; report publication writes only under the reserved analytics namespace.

## Findings

The page must include:

- An overview with corpus coverage, totals, distributions, incomplete/missing data, cache behavior, runner/model/price-era composition, and ranked findings.
- One interactive chart and exact table for each of the 16 required and at least four corpus-supported analyses from Order 06.
- Visible model/provider/variant, recorded price/cost, effective estimated price/cost, price source/version/effective dates, and unknown-price states.
- A raw normalized data view with schema descriptions, pagination or virtualization, download links to safe companion files, and no prompt/conversation/source content.
- An interpretation panel describing overlap, missingness, sample size, uncertainty, association versus causation, and the current filter population.
- Stable deep-linkable or exportable filter state when feasible without compromising single-file/offline behavior.

## Proposed changes (ordered, validatable)

1. Materialize a versioned bundle atomically from normalized analysis output.
2. Render all interactive views from one embedded data contract.
3. Prove offline, safe, accessible, deterministic behavior at small and large scales.

## Deferred / out of scope (with reason)

- A hosted dashboard, web server, database, CDN, or runtime JavaScript dependency is excluded.
- Direct source-run browsing is excluded because it would expose sensitive data.
- CLI command registration is Order 08.
- Network submission is Order 09.
- Pixel-perfect branding is secondary to correctness and accessibility.

## Scope check

- Over-scope: no ingestion, cache parsing, statistics, runner changes, CLI dispatch, or transport.
- Under-scope: includes all report files, all required views, filters/toggles, accessibility, security, offline use, atomicity, snapshots, and large-data behavior.

## Required tests / validation

- Golden bundle manifest and deterministic render tests.
- Static scan proving no \`http:\`, \`https:\`, external script/link/font/image loads, dynamic module imports, or runtime fetch/XHR/WebSocket.
- Injection fixtures containing \`</script>\`, HTML, Unicode controls, formulas, and hostile identifiers.
- DOM-contract tests for every chart/table/control, ARIA state, keyboard path, visible focus class, text alternatives, reduced-motion rule, and no color-only distinction.
- Small, empty, one-run, missing-price, partial, mixed-runner, mixed-price-era, and large synthetic corpus renders.
- Companion-file schema checks and latest/snapshot atomic replacement and retention tests.
- Package wheel/sdist installation test proves assets are present.
- Bare \`python3 -m pytest\` and \`git diff --check\`.

## Spec / documentation sync

Order 10 documents the output tree, open workflow, report/data schemas, browser support, size thresholds, snapshot retention, and privacy caveats. Asset packaging changes are verified there.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: fault-injection tests prove atomic latest publication, valid companion schemas, and retention limited to snapshots.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: structural tests enumerate all required analyses, metric/phase modes, filters, tables, pricing context, findings, and raw normalized data.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: offline/security/accessibility/large-corpus checks and package asset tests pass with the full suite and clean diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: bundle publication and the single-file application share one schema and atomic artifact boundary.

Execute only after approval and Order 06. Do not omit uncertainty or data-quality context to simplify a visualization.

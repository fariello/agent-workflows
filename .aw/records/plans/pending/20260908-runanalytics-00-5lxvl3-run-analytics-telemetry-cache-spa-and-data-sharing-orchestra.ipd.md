# IPD: Run analytics, telemetry, cache, SPA, and data-sharing orchestration

- Date: 2026-09-08
- Kind: orchestrator
- Concern: Coordinate a privacy-safe, incremental, statistically honest analytics system for OpenCode and Agy driver runs from capture through local report, agent query, and explicit sharing.
- Scope: Sequence Orders 01 through 10, preserve their ownership boundaries, map every prompt requirement to an executable child, and define whole-Set completion evidence.
- Scope-Paths: .aw/records/plans/pending/20260908-runanalytics-01-xbwq8n-canonical-run-root-analytics-namespace-and-discovery-isolati.ipd.md, .aw/records/plans/pending/20260908-runanalytics-02-bzz5e6-privacy-safe-incremental-per-run-analytics-cache.ipd.md, .aw/records/plans/pending/20260908-runanalytics-03-lhccjf-cross-host-resource-telemetry-schema-collector-and-sampling.ipd.md, .aw/records/plans/pending/20260908-runanalytics-04-5f2h8i-opencode-and-agy-runner-telemetry-lifecycle-integration.ipd.md, .aw/records/plans/pending/20260908-runanalytics-05-8hald1-normalized-run-ingestion-fact-schema-and-conservation-checks.ipd.md, .aw/records/plans/pending/20260908-runanalytics-06-aflsz3-activity-taxonomy-effective-dated-pricing-statistics-and-fin.ipd.md, .aw/records/plans/pending/20260908-runanalytics-07-6eq3oq-self-contained-offline-analytics-spa-and-report-bundle.ipd.md, .aw/records/plans/pending/20260908-runanalytics-08-mm5p3v-agent-friendly-aw-runs-analyze-and-query-interface.ipd.md, .aw/records/plans/pending/20260908-runanalytics-09-ixis0c-sanitized-export-explicit-submission-and-setup-wizard-contro.ipd.md, .aw/records/plans/pending/20260908-runanalytics-10-9xycbh-integration-fixtures-documentation-packaging-and-regression.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: runanalytics
- Order: 0
- Highest E allocated: 01
- Author: Codex
- Id: 5lxvl3

## Workflow history

- 2026-09-08 draft (Codex): created from the requested implementation prompt.
- 2026-09-08 to-review (Codex): decomposed the feature into ten dependency-ordered children and mapped storage, telemetry, analytics, SPA, agent access, sharing, and acceptance requirements.

## Goal

Deliver a local-first analytics capability for every \`oc_runipd.py\` and \`agy_runipd.py\` execution record. The finished system incrementally caches privacy-safe facts, analyzes time/cost/tokens/activity/outcomes/resources with visible uncertainty, publishes one self-contained offline SPA plus agent-readable data, and permits data sharing only through explicit tiered export and a separate approved submission action.

## Detailed Implementation Checklist (TODO)

Execution-state rule: the orchestrator contains no feature implementation. The runner sequences its children and retires this plan only after every child has completed its own execution and validation gates.

### Task group 1: Sequence the child-owned work

- [ ] E-01 Execute child IPDs 01 through 10 in dependency order, returning any failed cross-contract validation to the child that owns the contract.
  - Depends on: none
  - Expected outcome: each requirement in the coverage matrix has one primary owner, all declared handoffs agree, every child reaches executed with concrete V evidence, and Order 10 produces the whole-Set regression record.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | Primary ownership | Depends on |
|---:|---|---|---|---|
| 01 | \`xbwq8n\` | \`20260908-runanalytics-01-xbwq8n-canonical-run-root-analytics-namespace-and-discovery-isolati.ipd.md\` | Canonical runs root, reserved analytics tree, discovery/target exclusion | none |
| 02 | \`bzz5e6\` | \`20260908-runanalytics-02-bzz5e6-privacy-safe-incremental-per-run-analytics-cache.ipd.md\` | Per-run cache, privacy projection, fingerprints, locks, atomicity | 01 |
| 03 | \`lhccjf\` | \`20260908-runanalytics-03-lhccjf-cross-host-resource-telemetry-schema-collector-and-sampling.ipd.md\` | Telemetry schema, probes, pseudonyms, collector, config | 02 |
| 04 | \`5f2h8i\` | \`20260908-runanalytics-04-5f2h8i-opencode-and-agy-runner-telemetry-lifecycle-integration.ipd.md\` | OpenCode/Agy integration, resume/retry/verifier/shutdown parity, runner spec | 03 |
| 05 | \`8hald1\` | \`20260908-runanalytics-05-8hald1-normalized-run-ingestion-fact-schema-and-conservation-checks.ipd.md\` | Source adapters, normalized facts, provenance, conservation, quality | 02, 04 |
| 06 | \`aflsz3\` | \`20260908-runanalytics-06-aflsz3-activity-taxonomy-effective-dated-pricing-statistics-and-fin.ipd.md\` | Taxonomy, pricing eras, statistics, analyses, ranked findings | 05 |
| 07 | \`6eq3oq\` | \`20260908-runanalytics-07-6eq3oq-self-contained-offline-analytics-spa-and-report-bundle.ipd.md\` | Latest/snapshot bundle and accessible self-contained SPA | 06 |
| 08 | \`mm5p3v\` | \`20260908-runanalytics-08-mm5p3v-agent-friendly-aw-runs-analyze-and-query-interface.ipd.md\` | Fixed analyze/query CLI leaves and agent protocol | 07 |
| 09 | \`ixis0c\` | \`20260908-runanalytics-09-ixis0c-sanitized-export-explicit-submission-and-setup-wizard-contro.ipd.md\` | Export tiers, separate submission, consent, wizard/config | 08 |
| 10 | \`9xycbh\` | \`20260908-runanalytics-10-9xycbh-integration-fixtures-documentation-packaging-and-regression.ipd.md\` | Fixture corpus, docs, package proof, all acceptance evidence | 01 through 09 |

All runtime dependencies are execution-state edges, not file-overlap guesses. Orders 08 and 09 are deliberately serialized because both extend the routing-sensitive CLI. Order 10 does not invent behavior; it sends failures back to the owning child.

## Completion criteria (the whole Set is done only when)

- \`<resolved-runs-root>\` resolves normally to \`<repo>/.aw/records/runs\`, and all analytics writes stay under its reserved \`analytics/\` child.
- The reserved tree contains latest user-facing outputs directly and uses \`cache/\`, \`snapshots/\`, and \`exports/\` for their named purposes; no analytics descendant is treated as a driver run.
- Source run directories are read-only inputs. Re-running analysis changes only tool-owned analytics outputs.
- Per-run caches use source-root/run identity, schema/version metadata, strong freshness inputs, incomplete-run rechecks, atomic publication, and safe concurrent-writer behavior.
- Cache, report, agent, metrics-export, and redacted-event artifacts contain no prompt/conversation/content, raw commands, arbitrary environment data, raw path/host/user identity, secrets, or other forbidden canaries.
- Both runners emit equivalent best-effort per-invocation telemetry with start/end basic snapshots by default, separately opt-in periodic samples, per-attempt/node identity, graceful degradation, and bounded overhead.
- Current and historical OpenCode/Agy records normalize into phase-aware, attempt-aware facts with provenance, quality, missingness, overlap, and cost/token/time conservation.
- All 16 mandatory analyses and at least four additional corpus-supported analyses are reproducible for aggregate and phase-separated views across time, cost, token components, runner, model/provider/variant, price era, and relevant dimensions.
- Recorded costs remain recorded; estimates use effective-dated documented price entries and are visibly labeled with source/version/effective interval.
- Findings are ranked and machine-readable, show evidence/effect/sample/coverage/uncertainty/caveats/alternatives/experiments, and never state correlation as causation.
- \`analytics/index.html\` is a useful self-contained offline SPA with exact data tables, linked controls, accessibility, injection safety, no network dependency, and documented large-data behavior.
- \`aw runs analyze\` and \`aw runs query\` provide stable human and agent surfaces without breaking current viewer/ledger routing or creating dynamic aliases.
- Export is local, tiered, inspectable, and explicit. Raw export requires every-time risk acknowledgement. Submission is a separate explicit command and is unavailable until an endpoint policy is approved.
- Setup presents analytics as optional, asks separately about periodic sampling, never grants submission consent, and supports inspect/reconfigure/disable/delete behavior.
- The installed wheel and sdist contain all code/data/assets, and the mandatory end-to-end matrix, offline proof, sanitizer, performance measurements, bare full suite, lints, index check, and diff check pass.

## Cross-IPD validation

| Requirement family | Primary owner | Required handoff/cross-check |
|---|---|---|
| Canonical disposable locations and discovery isolation | 01 | 02, 07, 08, 09 use only its helpers; 10 searches for duplicate literals and missed selectors. |
| Safe incremental cache | 02 | 05 writes only its allowlisted schema; 08 reports hit/miss reasons; 10 proves selective rebuild. |
| Telemetry collection | 03 | 04 invokes exactly its lifecycle API; 05 parses its versioned events; 10 measures overhead and failures. |
| Runner parity and contemporaneous nodes | 04 | 05 fixture adapters preserve invocation/attempt/node/phase identity; 10 covers both hosts and resume. |
| Normalized fact contract | 05 | 06, 07, 08, and 09 consume the same facts; no consumer reparses sensitive run sources. |
| Attribution/pricing/statistics/findings | 06 | 07 renders and 08 queries identical measures; 10 compares chart/table/query values. |
| SPA and bundle | 07 | 08 publishes/locates it; 09 exports only companion-safe data; 10 proves offline/package behavior. |
| Human and agent CLI | 08 | 09 adds fixed leaves after it; 10 verifies routing collisions and documented examples. |
| Export/submission/setup | 09 | 10 attacks every sensitivity boundary and proves zero network outside explicit submit. |
| Integration evidence | 10 | Every failure is fixed in the owning child scope, then the complete matrix is rerun. |

Additional invariants:

- One vocabulary and enum set governs runner, phase, attempt, outcome, model/provider/variant, metric, taxonomy class, quality, pricing status, telemetry mode, and sensitivity tier.
- Every numeric chart value can be traced through query output to normalized fact IDs and source provenance without exposing sensitive source content.
- Aggregate review-plus-execute values reconcile with their separated components; verifier and recovery remain independently visible.
- Activity duration never exceeds elapsed time without a displayed overlap measure; missing time is displayed as unattributed, not assigned heuristically.
- Analyzer, report open, wizard, installation, cleanup, and export never submit data.
- A cache or report schema change invalidates or migrates explicitly; it never silently misreads old artifacts.

## Deferred / out of scope (with reason)

- A hosted collection/aggregation service, endpoint selection, legal/privacy approval, server retention, and deletion operations are not defined by this repository request. Until approved, submission remains unavailable.
- Automatic changes to prompts, gates, tests, model routing, or runner policy based on findings are excluded. Findings propose measured experiments for human review.
- Conversation-content NLP and source-code semantic analysis are excluded because they conflict with the minimized cache/output boundary.
- Real user run data is not committed or bundled with these IPDs.
- A live web dashboard, server, database, or network-loaded frontend dependency is unnecessary for the requested offline deliverable.
- Claims of anonymity, causal inference, or statistically valid ANOVA without assumptions and sample sufficiency are prohibited.

## Scope check

- Over-scope: no child-independent implementation is assigned to the orchestrator; network service operation and automatic optimization remain excluded.
- Under-scope: the ten children collectively own storage, incremental cache, privacy, telemetry, runner integration, historical ingestion, fact integrity, all analytics, price changes, findings, SPA, agent interface, export/submission, wizard, packaging, docs, and all mandatory tests.

## Required tests / validation

Order 10 must map each test to its owning requirement and retain final evidence for:

- The 33 mandatory scenarios enumerated in Order 10.
- Hand-calculated metric and price-era golden outputs.
- Aggregate/separate phase reconciliation and time overlap/unattributed accounting.
- Cache no-op, selective rebuild, active/resumed run, concurrency, interruption, corruption, and schema change.
- Telemetry host parity, node changes, disabled/basic/periodic modes, probe failures, cleanup, privacy, and overhead.
- Every required and corpus-selected analysis, chart, exact table, query view, and finding contract.
- Offline/no-network SPA, accessibility, hostile-string safety, deterministic bundle, size handling, and packaged assets.
- Export tier separation, raw confirmation, endpoint/consent/auth/receipt safeguards, archive safety, and zero implicit network.
- Existing runner, viewer, ledger, profile, setup, and CLI regression behavior.
- Author and review-finalize lints, plans index check, spec lint after amendments, wheel/sdist build/install, bare \`python3 -m pytest\`, and \`git diff --check\`.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: the runner retires an orchestrator from child status. Do not fabricate an independent implementation checkpoint for this file.

- [ ] V-01 validates E-01
  - Required evidence: all ten Child IPDs are executed with passing V items; Order 10’s final record maps every completion criterion and mandatory scenario to concrete passing evidence; Set dependencies and plan index are clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the Set is intentionally large because it spans capture, normalization, analysis, presentation, agent access, and privacy-sensitive sharing. Ten narrowly owned children keep implementation passes bounded, while this orchestrator carries only sequence and whole-feature acceptance.

Approve and execute children through the normal IPD lifecycle. The orchestrator performs no unique code or validation work and must not be marked executed manually ahead of its children.

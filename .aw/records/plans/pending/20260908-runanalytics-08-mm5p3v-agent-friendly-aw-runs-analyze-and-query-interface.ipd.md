# IPD: Agent-friendly aw runs analyze and query interface

- Date: 2026-09-08
- Kind: child
- Concern: Give humans and agents a stable, collision-safe way to build, inspect, and query analytics without scraping the SPA.
- Scope: Register fixed \`aw runs analyze\` and \`aw runs query\` leaves, define flags and exit codes, generate agent-oriented outputs, and preserve existing viewer/ledger routing.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/run_analytics_cli.py, agent_workflows/run_analytics_query.py, tests/test_run_analytics_cli.py, tests/test_run_viewer.py
- Item-Dependencies: executed:6eq3oq
- Status: to-review
- Set: runanalytics
- Order: 8
- Highest E allocated: 03
- Author: Codex
- Id: mm5p3v

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): defined fixed command grammar, analysis controls, a versioned agent protocol, and routing compatibility tests.

## Goal

Make \`aw runs analyze\` the one command that updates cache and produces the local report bundle, and \`aw runs query\` the concise structured interface agents can use for facts and findings. Fixed leaf names must preserve the current \`aw runs -- <target>\` collision escape and never create dynamic commands.

## Detailed Implementation Checklist (TODO)

### Task group 1: Commands and protocol

- [ ] E-01 Add the \`analyze\` leaf with explicit source/output/open/path/list/latest/snapshot/cache controls and stable diagnostics.
  - Depends on: none
  - Expected outcome: \`aw runs analyze [TARGET ...]\` defaults to all canonical runs and latest output; \`--output\`, \`--open\`, \`--path\`, \`--list\`, \`--latest\`, \`--keep-snapshot\`, \`--rebuild\`, and machine-readable modes have documented precedence, no-prompt behavior, and exit codes.
  - Execution state: pending
- [ ] E-02 Add a versioned \`query\` protocol over cached/companion normalized data and findings.
  - Depends on: E-01
  - Expected outcome: agents can request overview, schema, metrics, distributions, slices, findings, evidence, data quality, cache status, and explain-taxonomy/price records using filters; JSON/JSONL/Markdown/table outputs have stable schemas, explicit units, missingness, provenance, and bounded/default limits.
  - Execution state: pending
- [ ] E-03 Prove routing, compatibility, failure semantics, discoverability, and human/agent help output.
  - Depends on: E-02
  - Expected outcome: existing bare viewer and ledger leaves still route identically; targets named \`analyze\` or \`query\` remain accessible after \`--\`; malformed filters, missing corpus, corrupt cache, partial analysis, open failure, and unsupported schema return documented codes and remedies.
  - Execution state: pending

## Project conventions discovered (Step 0)

- \`aw runs\` uses a custom viewer-or-leaf subparser whose registration order is load-bearing. New fixed leaves must be added through its established leaf table/routing mechanism.
- Existing fixed viewer leaves take a ledger-style target, but analytics leaves require distinct parsers; do not force them through a helper whose arguments do not fit.
- Current help documents the \`--\` escape for targets colliding with a leaf. Keep and extend that contract.
- Agent output conventions use \`--agent\` JSONL and \`--json\`; integrate rather than emit ad hoc prose.
- \`--open\` is an explicit user side effect. Analysis without it must never launch a browser.

## Findings

Recommended command contract:

- \`aw runs analyze [TARGET ...]\`: analyze source runs, update safe caches, publish latest report.
- \`aw runs analyze --path\`: print the latest HTML path without opening it.
- \`aw runs analyze --list\`: list report/snapshot/export artifacts and cache summary.
- \`aw runs query <view>\`: return facts/findings for agents without parsing HTML.
- \`aw runs query findings --limit 10 --format json\`: ranked evidence records.
- \`aw runs query metrics --group-by model,phase --metric cost --stat median\`: bounded aggregation using the same engine.
- \`aw runs query explain --taxonomy <rule-id>\` or \`--price <price-id>\`: provenance and interpretation.

Arbitrary SQL, expression evaluation, filesystem paths outside the resolved roots, and unrestricted field projection are excluded. Filters and groupings come from an allowlisted schema.

## Proposed changes (ordered, validatable)

1. Register the analyze leaf and its deterministic orchestration of cache, engine, and bundle.
2. Implement an allowlisted query grammar and versioned agent response envelopes.
3. Lock down parser routing, help, errors, and collision behavior.

## Deferred / out of scope (with reason)

- Export and submit are Order 09 because their consent and sensitivity model differs.
- Dynamic aliases such as \`aw analyze\` or config-created leaves are excluded to prevent command collisions.
- A long-running API server or MCP server is not required; agents can invoke the deterministic CLI directly.
- Automatic browser launch and automatic network action are excluded.

## Scope check

- Over-scope: no source parsing, statistics, HTML implementation, telemetry, export, or transport.
- Under-scope: includes all user-requested analyze options, direct agent access, stable schemas, errors, help, and collision tests.

## Required tests / validation

- Parser and dispatch tests for every flag and format, defaults, incompatibilities, target resolution, and exit code.
- \`aw runs\` viewer and every existing fixed leaf retain behavior.
- \`aw runs -- analyze\` and \`aw runs -- query\` resolve those words as viewer targets; fixed leaves win without \`--\`.
- Analyze twice to prove cache reuse; mutate/resume one fixture and prove selective rebuild.
- Query golden tests for all views, filters, groupings, units, missingness, provenance, row limits, streaming JSONL, and schema version.
- Open behavior mocked for supported/unsupported/failure systems and never called without \`--open\`.
- Help and README command snippets are executable.
- Bare \`python3 -m pytest\` and \`git diff --check\`.

## Spec / documentation sync

Order 10 publishes the full command and agent-protocol reference. If the repository maintains a controlling CLI grammar spec, execution must amend it before registering leaves; record that discovery in Workflow history rather than silently diverging.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: CLI tests build latest/snapshot outputs with every option and stable exit code while exercising cache hit/miss reporting.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: schema golden files prove each agent view is bounded, typed, versioned, attributable, and free of sensitive canaries.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: full routing matrix, help snapshots, error tests, bare suite, and diff check pass without regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: both leaves share the routing-sensitive command surface and the same agent schema, so one owner must prevent grammar drift.

Execute only after approval and Order 07. Preserve fixed grammar: configuration and data may never manufacture top-level or leaf commands.

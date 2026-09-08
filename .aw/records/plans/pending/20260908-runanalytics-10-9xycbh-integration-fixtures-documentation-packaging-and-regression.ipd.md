# IPD: Integration fixtures, documentation, packaging, and regression closeout

- Date: 2026-09-08
- Kind: child
- Concern: Prove the entire analytics feature works from installed CLI to offline report and agent outputs, with complete documentation and no regressions.
- Scope: Build representative fixture corpora and mutation scenarios, run end-to-end/privacy/offline/package validation, finish user/developer documentation, and close every Set acceptance criterion.
- Scope-Paths: tests/fixtures/run_analytics/**, tests/test_run_analytics_e2e.py, tests/test_run_analytics_packaging.py, README.md, docs/**, pyproject.toml, .aw/records/plans/README.md
- Item-Dependencies: executed:5f2h8i, executed:6eq3oq, executed:8hald1, executed:aflsz3, executed:bzz5e6, executed:ixis0c, executed:lhccjf, executed:mm5p3v, executed:xbwq8n
- Status: to-review
- Set: runanalytics
- Order: 10
- Highest E allocated: 03
- Author: Codex
- Id: 9xycbh

## Workflow history
- 2026-09-08 to-review (aw set): set Item-Dependencies to executed:5f2h8i, executed:6eq3oq, executed:8hald1, executed:aflsz3, executed:bzz5e6, executed:ixis0c, executed:lhccjf, executed:mm5p3v, executed:xbwq8n

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): enumerated the corpus, mutation, packaging, privacy, offline, performance, documentation, and full regression proof.

## Goal

Close the Set with reproducible end-to-end evidence that an installed \`aw\` can analyze both runner formats incrementally, generate a correct offline SPA and agent data, and export only under the requested consent. Make locations, privacy limits, telemetry controls, statistics, and recovery discoverable to users.

## Detailed Implementation Checklist (TODO)

### Task group 1: Corpus, documentation, and release proof

- [ ] E-01 Build a compact synthetic fixture corpus and end-to-end mutation harness covering all required lifecycle, schema, runner, phase, pricing, telemetry, cache, and privacy cases.
  - Depends on: none
  - Expected outcome: fixtures use deterministic timestamps and hand-calculated expectations; generated sensitive canaries never enter safe outputs; a mutation harness exercises unchanged, active, resumed, added, removed, corrupt, and schema-upgraded runs without committing real user data.
  - Execution state: pending
- [ ] E-02 Complete user, agent, operator, schema, taxonomy, pricing, privacy, telemetry, export/submission, troubleshooting, and architecture documentation; verify package contents.
  - Depends on: E-01
  - Expected outcome: docs give exact commands and paths, explain disposable storage and deletion, identify measured/derived/missing values, state no-anonymity/no-causation limits, describe optional install/setup defaults, and an installed wheel/sdist contains every Python and SPA asset.
  - Execution state: pending
- [ ] E-03 Execute the full acceptance matrix, performance budgets, sanitizer scan, offline report proof, bare regression suite, plan/spec lint, and diff checks; resolve every failure within the owning child scope.
  - Depends on: E-02
  - Expected outcome: all Set completion criteria have durable test/log evidence, repeated analysis demonstrates selective cache reuse, reports work from \`file://\` with network denied, no safe artifact contains canaries, and no existing runner/viewer/CLI behavior regresses.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The required test command is bare \`python3 -m pytest\`; flags such as \`-q\`, \`-x\`, or \`--tb\` are not acceptable final evidence.
- IPD IDs, E/V identifiers, dependencies, and indexes are tool-maintained; execution must run sync/lint/index commands rather than edit derived metadata by hand.
- The wheel currently packages the \`agent_workflows\` package and has minimal dependencies. SPA assets and any pricing data need explicit installed-package verification.
- There is no live run corpus in this checkout. Synthetic fixtures are authoritative for tests; optional local-corpus validation must be read-only, opt-in, privacy-safe, and excluded from commits and reports attached to this IPD.
- Existing \`.aw/records/runs\` content is ignored/disposable and must not be used as permanent test evidence.

## Findings

The integration matrix must cover at least these 33 cases from the implementation prompt:

1. OpenCode completed run.
2. Agy completed run.
3. Mixed-runner corpus.
4. Review and execute separated.
5. Review and execute aggregated.
6. Verifier present.
7. Verifier absent.
8. Retry/multi-attempt IPD.
9. Resumed same-directory run.
10. In-progress run cached then changed.
11. New run added after first analysis.
12. Run removed after first analysis.
13. One corrupt run among valid runs.
14. Missing cost.
15. Missing token component.
16. Missing model price.
17. Price changes at an effective-date boundary.
18. Failed merge then successful retry.
19. Permanent merge failure.
20. Test failure/retry loop.
21. Gate/risk-heavy activity.
22. Overlapping activity intervals.
23. Telemetry disabled.
24. Basic start/end telemetry.
25. Periodic telemetry.
26. Different node pseudonyms across attempts.
27. Probe permission/timeout/malformed failure.
28. Concurrent analyzers/cache writers.
29. Interrupted cache/report publication.
30. Empty corpus.
31. Large synthetic corpus.
32. Sensitive canaries in every forbidden source field.
33. Fixed CLI leaf collisions and \`--\` target escape.

Also cover package installation, report opening from a path containing spaces/Unicode, export archive traversal, submission network isolation, config reconfiguration, and snapshot retention.

## Proposed changes (ordered, validatable)

1. Add deterministic cross-runner corpus builders and exact expected outputs.
2. Write progressive-disclosure documentation and verify distribution contents.
3. Run and archive the complete acceptance evidence, fixing only in the correct child-owned files.

## Deferred / out of scope (with reason)

- Real user run data is never committed as a fixture.
- A hosted analytics service and server-side aggregation are outside this repository.
- Performance tuning beyond documented budgets is deferred unless acceptance measurements fail.
- Automatic workflow/model changes based on findings are excluded; the tool advises and supports experiments.

## Scope check

- Over-scope: no new analytical behavior should originate here; failures return to the child that owns the behavior.
- Under-scope: covers fixture breadth, end-to-end behavior, distribution packaging, every documentation audience, all mandatory tests, and repository-wide regression evidence.

## Required tests / validation

- Execute all 33 mandatory scenarios plus the added package/path/archive/network/config/retention cases.
- Run an installed-wheel smoke test in an isolated environment: help, analyze, query, report asset load, export, and submit-unavailable or mocked-approved endpoint.
- Deny network while opening the SPA and assert no attempted requests.
- Compare cached and forced-rebuild facts byte-for-byte after excluding documented volatile manifest fields.
- Measure first scan, unchanged scan, one-run rebuild, large-corpus memory, report size, and telemetry overhead against documented budgets.
- Scan cache/report/metrics/redacted exports, diagnostics, and submission receipts for all sensitive canaries.
- Run author and review-finalize IPD/spec lint as applicable, \`aw plans index --check\`, bare \`python3 -m pytest\`, build wheel/sdist, install artifacts, and \`git diff --check\`.

## Spec / documentation sync

Update README and focused docs for:

- Quick start and optional installation/setup.
- Exact storage tree under \`.aw/records/runs/analytics/\`.
- Analyze/query/open/path/list/snapshot commands.
- Agent JSON/JSONL schemas and examples.
- Fact/data dictionary, metric conservation, overlap, missingness, and phase semantics.
- Taxonomy rules and explanations.
- Effective-dated prices, source maintenance, recorded versus estimated costs.
- SPA controls, accessibility, offline limitations, and large-data fallback.
- Telemetry fields/defaults/periodic opt-in/platform support/overhead/privacy.
- Cache invalidation, corruption recovery, retention, and deletion.
- Export tiers, sanitizer limits, explicit submission, endpoint governance, and no automatic network activity.
- Troubleshooting and compatibility matrix.

Update \`.aw/records/plans/README.md\` only if the new command/report lifecycle creates a durable plan convention; do not add analytics operational detail to always-loaded instructions.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: fixture manifest maps every mandatory scenario to exact assertions and hand-calculated expected metrics, with no real run data.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: link/help/example checks and isolated wheel/sdist installation prove docs and packaged assets match implemented behavior.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: one final evidence record includes all scenario results, cache/performance measurements, network-denied SPA proof, sanitizer results, lints, package install, bare full suite, and clean diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: this is the Set’s single integration and release-proof owner; it adds no independent feature behavior.

Execute only after Orders 01 through 09 are executed. A green unit suite without the offline, privacy, package, cache-mutation, and full bare-suite evidence is not completion.

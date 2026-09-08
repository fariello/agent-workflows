# IPD: Privacy-safe incremental per-run analytics cache

- Date: 2026-09-08
- Kind: child
- Concern: Avoid repeated corpus rescans while ensuring cached analytics facts are complete, fresh, atomic, and safe to share at the metrics level.
- Scope: Define and implement a versioned per-run cache, content freshness fingerprints, privacy projection, locking, atomic replacement, and cache observability.
- Scope-Paths: agent_workflows/run_analytics_cache.py, agent_workflows/run_analytics_privacy.py, tests/test_run_analytics_cache.py, tests/test_run_analytics_privacy.py
- Item-Dependencies: executed:xbwq8n
- Status: to-review
- Set: runanalytics
- Order: 2
- Highest E allocated: 03
- Author: Codex
- Id: bzz5e6

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): fixed the cache hierarchy, freshness protocol, allowed data classes, redaction boundary, and failure behavior.

## Goal

Store one reusable normalized summary per source run beneath \`<resolved-runs-root>/analytics/cache/<source-root-id>/<run-id>/\`. Reuse it only when all analytics-relevant source state is unchanged, and guarantee that the cache contains no prompt, conversation, source text, command text, secrets, raw host identity, or raw absolute path.

## Detailed Implementation Checklist (TODO)

### Task group 1: Cache contract and privacy boundary

- [ ] E-01 Implement a versioned cache envelope and a single allowlist-based privacy projector for all persisted analytics facts.
  - Depends on: none
  - Expected outcome: the envelope records schema/tool versions, source-root ID, run ID, completeness, source fingerprint, source coverage, generated time, metric facts, event facts, quality flags, and warnings; unknown fields fail closed instead of being copied.
  - Execution state: pending
- [ ] E-02 Implement freshness decisions, stable-source reuse, incomplete-run rechecks, locking, atomic replacement, and isolated corruption recovery.
  - Depends on: E-01
  - Expected outcome: unchanged completed runs are cache hits without reparsing; new/resumed/in-progress/mutated/schema-changed runs rebuild; interruption never publishes a partial cache; one corrupt entry does not poison other runs.
  - Execution state: pending
- [ ] E-03 Expose machine-readable cache decisions and add privacy, mutation, concurrency, corruption, and idempotence tests.
  - Depends on: E-02
  - Expected outcome: callers receive per-run hit/miss/rebuild/skip reasons and totals; repeated unchanged analysis is byte-stable apart from explicitly volatile metadata and reads fewer source files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The repository already depends on \`filelock>=3\`; use its established locking approach instead of inventing an incompatible lock primitive.
- Driver artifacts can change during execution and resume in the same directory. Directory mtime alone cannot establish freshness.
- \`.aw/records/runs\` is ignored and disposable, so cache recovery must rebuild rather than require migration or manual repair.
- Source run directories remain read-only. Writes are confined to the Order-01 reserved analytics subtree.
- Downstream report, query, export, and submission paths must consume the same privacy-projected facts rather than create weaker parallel sanitizers.

## Findings

The cache must retain raw numeric observations needed for aggregation, including timestamps, durations, resource samples, token components, monetary values, categorical activity labels, phase, IPD/set/run identifiers, model/provider, price-source metadata, outcome flags, and quality markers. “Raw” here means unsummarized metric facts, not raw source records.

The forbidden set includes prompt and response bodies, agent conversations, instructional file contents, source snippets, arbitrary event payloads, shell command text and arguments, environment values outside an explicit non-sensitive allowlist, usernames, hostnames, raw paths, repository remotes, branch names, commit messages, and secret-shaped strings. Hashed identifiers must use a documented local salt or stable source-root derivation that cannot be reversed or correlated across submissions unless the user explicitly opts into that scope.

## Proposed changes (ordered, validatable)

1. Define cache and privacy schemas with strict loaders and forward-compatible version diagnostics.
2. Compute a deterministic manifest from analytics-relevant file identity and terminal/in-progress state, then publish through lock plus temporary-file rename.
3. Instrument cache behavior and attack the privacy boundary with seeded sensitive canaries.

## Deferred / out of scope (with reason)

- Parsing driver artifacts into facts is Order 05.
- Cache retention CLI and snapshots are Orders 07 and 08.
- Exporting original raw run records is Order 09 and may never reuse the safe-cache label.

## Scope check

- Over-scope: no source adapters, statistical aggregation, UI, runner modification, or network transport.
- Under-scope: includes schema evolution, incomplete-run invalidation, concurrency, partial failure, privacy tests, and observability needed by all downstream consumers.

## Required tests / validation

- Required cases: first scan; unchanged completed run cache hit; one changed run rebuild; resumed/in-progress run rebuild; added run; removed run; schema-version change; interrupted write; concurrent analyzers; corrupt entry isolation; stale lock recovery if supported by the chosen lock API; deterministic projection; unknown-field refusal.
- Seed prompts, paths, commands, hostnames, usernames, environment secrets, and high-entropy tokens into fixtures and assert none occur in cache JSON/JSONL or diagnostics.
- Demonstrate conservation of every numeric fact across encode/decode.
- Focused tests, bare \`python3 -m pytest\`, and \`git diff --check\` pass.

## Spec / documentation sync

Order 10 documents cache location, disposability, privacy claims and limitations, and rebuild behavior. Schema version and forbidden-field rationale belong in module-level developer documentation, not an always-loaded agent instruction.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: schema round-trip and canary tests prove allowed numeric facts survive and forbidden content cannot be serialized.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: mutation and concurrency tests show exact cache decisions, no partial publication, and recovery from one malformed entry.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a second unchanged fixture analysis reports cache hits, performs no source parse calls, and the full suite and diff check pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: cache validity and privacy projection are inseparable because every persisted fact must cross the same boundary.

Execute only after approval. A passing implementation must not describe the cache as anonymous or safe for public release; it is minimized and redacted, with residual re-identification risk documented.

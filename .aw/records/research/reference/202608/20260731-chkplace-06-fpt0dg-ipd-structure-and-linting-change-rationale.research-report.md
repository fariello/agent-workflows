---
id: fpt0dg
created: 20260802
set: chkplace
order: 06
topic: []
model:
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260731-chkplace-06-fpt0dg-ipd-structure-and-linting-change-rationale.research-report.md.
consumed-by: []
---
# Explanation of revisions and recommendations for the IPD structure and linting specification

- Date: 2026-08-02
- Companion specification: `20260731-chkplace-05-kdr9kv-ipd-structure-and-linting.reference-research.md`
- Source reviewed: `20260802-1904-01-ipd-structure-and-linting.spec.md`
- Purpose: explain the material revisions, their rationale, and the implementation recommendations that follow from them

## 1. Overall assessment

The original draft had the correct architecture. It accurately translated the research's central conclusions into a proposed convention:

- exact rather than relational checklist placement;
- distinct execution and validation phases;
- an `E-*`/`V-*` mapping;
- deterministic structural checking;
- a post-gate lifecycle transaction;
- blocking-question and plan-size corrections;
- structural preflight before semantic review;
- grandfathering completed plans.

The draft was not yet implementation-ready because several statements that sounded deterministic still depended on semantic interpretation, and several state transitions were not defined precisely enough for two independent implementations to behave the same way. The revised specification preserves the architecture and hardens the contract.

The most consequential revisions are:

1. IDs are stable and never automatically renumbered.
2. Persisted lifecycle status is separated from lint checkpoint.
3. Execution, validation, question, and size states receive explicit grammars and truth tables.
4. The linter's parser behavior and semantic boundary are defined.
5. One machine-readable schema becomes the source of truth for templates, workflows, and linting.
6. Authoritative workflows invoke lint unconditionally and fail closed.
7. Version 1 keeps two physical checklist sections and defers the merged-ledger variant.

## 2. Stable IDs replace automatic renumbering

### Original issue

The draft called the identifiers “stable” but said `aw ipd` would “assign/renumber” them. Those requirements conflict. Automatic renumbering could invalidate:

- `Depends on:` references;
- `V-* validates E-*` mappings;
- review comments that cite an item;
- progress messages and tool logs;
- partially completed execution state;
- historical discussion of a changed plan.

### Revision

The revised contract makes identifiers monotonic within an IPD:

- reordering never changes IDs;
- gaps are legal;
- new items receive the next unused suffix;
- existing IDs are preserved;
- synchronization becomes non-destructive;
- structural changes after approval or execution require amendment and re-review.

The authoring operation is named `aw ipd sync` rather than “renumber” because synchronization should reconcile missing mechanical structure without rewriting identity.

### Recommendation

Do not provide an ordinary automatic renumber command. If a maintainer ever needs cosmetic compaction, make it an explicit migration command that produces a mapping report and is forbidden after review or execution begins.

## 3. Persisted status is separated from lint checkpoint

### Original issue

The draft proposed inferring phases such as `pre-execution` from `Status:`. But `pre-execution`, `pre-transition`, and `post-transition` are moments at which a check is requested, not necessarily stored lifecycle statuses. A plan with `Status: approved` could be:

- waiting for execution;
- in execution;
- blocked during execution;
- ready for terminal transition.

The persisted value cannot safely distinguish these moments.

### Revision

The revised spec defines five lint checkpoints:

```text
author
review-finalize
pre-execution
pre-transition
post-transition
```

Plain `aw ipd lint FILE` may infer only a conservative default. Every authoritative gate supplies `--phase` explicitly.

### Recommendation

Preserve the repository's existing `Status:` vocabulary unless a separate migration justifies changing it. Define a schema mapping from status/path to safe default checks, but never infer a requested transition gate from status alone.

## 4. Execution and validation now have complete state models

### Original issue

The draft correctly distinguished `E-* checked` from `V-* pass`, but it did not fully define:

- the initial validation state;
- whether `blocked` or `failed` validation rows are checked;
- whether empty evidence is legal;
- how execution itself records blocked or failed work;
- how E and V states constrain one another;
- what exact state is required before terminal transition.

Without a truth table, independently written linters could accept different documents.

### Revision

The revised spec introduces:

- `Execution state: pending | performed | blocked | failed`;
- `Result: pending | pass | blocked | failed`;
- exact checkbox/state rules;
- evidence-presence rules;
- cross-state E/V constraints;
- checkpoint-specific requirements.

Terminal transition requires every current E item to be checked and `performed`, and every V item to be checked and `pass` with nonempty observed evidence.

### Recommendation

Do not use blank result values as state. `pending` is explicit, parseable, and easier for both agents and humans. Do not allow the phrase “every reachable item” to excuse incomplete work. Remove or supersede an obsolete item through plan amendment instead.

## 5. Blocking questions receive a deterministic grammar

### Original issue

The original linter was supposed to reject unresolved blocking questions but did not define how it would recognize one. Natural-language interpretation would violate the linter's declared no-model, structure-only boundary.

### Revision

Each question now has explicit fields:

```markdown
### OQ-01: <question>

- Blocking: yes
- Status: open
- Owner: <person, role, agent, event, or none>
- Resolution or deferral rationale:
```

The linter can enforce field consistency. Semantic review remains responsible for deciding whether `Blocking: no` is credible.

### Recommendation

Keep the machine/human boundary visible in diagnostics. For example, lint may say the declared state is structurally valid; review must still determine whether the question could affect correctness, security, scope, architecture, acceptance criteria, or existing checklist items.

## 6. The lifecycle-transition prohibition is treated honestly

### Original issue

The draft listed “terminal transition is not an execution prerequisite” as a deterministic linter check. A text-only deterministic tool cannot recognize every paraphrase of a lifecycle transition without interpreting meaning.

### Revision

The revised design addresses the defect through several layers:

- terminal transition is absent from the execution template;
- the lifecycle workflow defines it as a post-gate transaction;
- the linter may reject exact reserved commands or markers;
- semantic review enforces the general prohibition;
- pre-transition and post-transition phases verify observable state.

### Recommendation

Do not claim semantic certainty from keyword matching. A rule that catches `git mv ... executed/` but misses “archive this plan after completion” is useful defense in depth, not proof that no lifecycle action is hidden in an E item.

## 7. Markdown parsing is explicitly fence-aware

### Original issue

The specification itself contains Markdown examples with headings and task lists. A regex-based checker could count those examples as real IPD structure, producing false duplicates or mappings.

### Revision

The revised contract requires structural Markdown parsing and excludes headings/checklists inside code blocks, front matter, and quoted examples. It also defines “immediately after” as adjacency among top-level H2 nodes, not physical lines.

### Recommendation

Use a maintained CommonMark-compatible parser and retain source positions for diagnostics. Add fixtures for fenced, indented, and quoted examples before implementing any heading-order logic.

## 8. One canonical schema prevents cross-file drift

### Original issue

The draft proposed changing templates, specifications, the review family, and the linter, but did not identify one authoritative structural representation. Maintaining these independently would recreate the parity risk identified by the research.

### Revision

The revised spec requires one machine-readable schema to own:

- plan kinds;
- headings and order;
- optional sections;
- front-matter fields;
- IDs and states;
- lint phases;
- thresholds;
- legacy behavior.

Templates and embedded workflow material must be generated from it or checked against it.

### Recommendation

Prefer generation where the output must be identical. Use normalized parity tests where human-readable copies need limited surrounding prose. Do not rely on version strings or instructions telling maintainers to update several copies.

## 9. The canonical heading order is corrected and bounded

### Original issue

The draft described “front matter” as part of an H2 list and omitted `## Project conventions discovered (Step 0)`, which appeared in the comprehensive audit's proposed order. It also allowed orchestrators to use another order without requiring that order to be enumerated.

### Revision

The revised spec:

- validates front matter separately;
- restores `## Project conventions discovered (Step 0)` provisionally;
- requires comparison with the actual current template before implementation;
- requires any intentional removal/rename to be a recorded decision;
- requires the complete orchestrator sequence in the canonical schema;
- requires optional H2 sections to have named permitted intervals.

### Recommendation

Confirm the exact current template headings during the implementation IPD's discovery step. Do not allow a seemingly incidental schema cleanup to remove an existing semantic section.

## 10. The two-list version 1 contract is made internally consistent

### Original issue

The draft permitted tiny plans to use a single action/evidence ledger while simultaneously requiring two exact headings and a one-to-one E/V structure. It did not define how the alternate shape would lint.

### Revision

Version 1 supports only separate physical execution and validation sections. The merged-ledger option remains an experimental condition for later evaluation.

### Recommendation

Ship one strict grammar first. If the controlled experiment later supports a merged representation, introduce it as a separate plan kind or schema version with its own state rules and linter fixtures.

## 11. Plan-size warnings become exactly enforceable without becoming caps

### Original issue

The draft said numeric limits would become warning thresholds but did not settle the exact trigger, rationale location, or resulting lint behavior.

### Revision

The recommended defaults are:

- warning above five task groups;
- warning above eighteen E leaves;
- `Size assessment: exception` plus a substantive cohesion rationale when either is exceeded.

Threshold violation remains a warning; missing or inconsistent required metadata is an error. Semantic review decides whether to accept the rationale or split the work.

### Recommendation

Treat these numbers as provisional operational defaults. Collect plan size, omission rate, review burden, and false-completion data before changing them. Never present the threshold as a quality target.

## 12. Evidence language is narrowed to independently inspectable evidence

### Original issue

The draft contrasted “captured command output” with narrated claims, but command output copied by the model may still be a model assertion. A nonempty field does not prove authenticity.

### Revision

The revised spec prefers evidence captured by the command runner or another tool and referenced through a durable path, digest, run ID, diff, or repository state. Human-observed evidence remains possible where tool capture is unavailable.

The linter checks presence and state consistency only. It does not certify truth, relevance, independence, or sufficiency.

### Recommendation

Where practical, later extend the execution tooling to capture command, arguments, exit status, and output artifact automatically. Do not make that a precondition for the structural-linter release unless the scope is manageable.

## 13. Enforcement is mandatory at authoritative gates

### Original issue

The draft allowed plan review to run the linter “or apply its checks.” That retained a prose-only path and made the highest-value intervention optional.

### Revision

Once the linter exists:

- structural preflight runs before semantic review;
- `review-finalize` runs after review edits;
- `pre-execution` and `pre-transition` fail closed;
- `post-transition` verifies the completed transaction;
- tool failure is distinct from lint success.

A narrow bootstrap exception is allowed while the implementation Set is creating the tool. It must be labeled accurately.

### Recommendation

Pre-commit and CI integration can remain a follow-up if every authoritative workflow calls the linter. Hooks are defense in depth; workflow invocation is the minimum viable enforcement.

## 14. Legacy and nonterminal rollout are separated

### Original issue

The draft said the convention applied to new plans, said nonterminal plans would be linted, and grandfathered executed plans. It did not fully define direct lint behavior or migration of existing pending/approved plans.

### Revision

The revised policy is:

- new plans use the new schema;
- existing nonterminal plans are migrated, re-authored, or quarantined before review/execution;
- repository scans skip legacy terminal plans without calling them conforming;
- direct legacy invocation returns an explicit legacy disposition;
- current-schema conformance requires migration.

### Recommendation

Avoid bulk rewriting approximately 120 completed plans. Preserve history and invest migration effort only in active/nonterminal work or a later evidence-backed use case.

## 15. Diagnostics and failure behavior are specified

### Original issue

“Exits nonzero with a precise message” was directionally correct but insufficient for automation and tests.

### Revision

The revised spec recommends:

- stable diagnostic codes;
- file and source location;
- exit `0` for conformance;
- exit `1` for lint errors;
- exit `2` for invocation, parsing, schema, or internal failure.

### Recommendation

Keep warning/error policy stable enough for CI and agent workflows to consume. Never convert parser failure into an empty finding set or passing result.

## 16. Tests are elevated to specification requirements

### Original issue

The draft called for tests but did not define the failure classes required for confidence in a parser/state-machine tool.

### Revision

The revised spec requires fixtures for:

- Markdown parsing and heading order;
- child and orchestrator schemas;
- stable IDs and non-destructive synchronization;
- every legal and illegal state combination;
- open-question grammar;
- size exceptions;
- gate enforcement;
- legacy handling;
- diagnostic locations and codes.

### Recommendation

Use table-driven tests for the state machine and golden fixtures for representative Markdown. Add regression fixtures for every real defect found during dogfooding.

## 17. Recommended implementation sequence

The implementation should proceed in this order:

1. Inventory current front matter, statuses, paths, child/orchestrator headings, optional sections, and duplicated rubric/template material.
2. Define the canonical machine-readable schema and its validation tests.
3. Implement the fence-aware parser and read-only structural linter.
4. Implement the state-machine and checkpoint rules.
5. Implement `scaffold` and non-destructive `sync` using the same schema.
6. Update templates and specifications.
7. Integrate mandatory preflight into review, execution, and transition workflows.
8. Add parity tests and documentation pointers.
9. Migrate or re-author active nonterminal plans.
10. Dogfood against the repository and add regression fixtures.

This order establishes the source of truth and checker before proliferating revised prose across the repository.

## 18. Final recommendation

Approve the revised design for conversion into an orchestrated implementation IPD Set, subject to confirming the repository-specific heading and lifecycle vocabulary during discovery.

The implementation Set should not reopen the following settled design decisions without new evidence or an explicit maintainer decision:

- IDs remain stable and are never automatically renumbered.
- Execution and validation remain separate physical sections in version 1.
- Gate lint uses explicit checkpoints.
- Authoritative workflows fail closed.
- The mutable checklist is never duplicated.
- Structural lint never substitutes for semantic review.
- Completed legacy plans remain grandfathered.

The controlled layout experiment remains valuable but is not required before implementing the deterministic corrections. The provisional top-execution/bottom-validation default should continue to be labeled as provisional.

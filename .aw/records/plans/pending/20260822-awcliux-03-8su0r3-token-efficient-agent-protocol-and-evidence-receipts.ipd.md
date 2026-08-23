# IPD: Token-Efficient Agent Protocol and Evidence Receipts

- Date: 2026-08-22
- Kind: child
- Concern: Give coding agents deterministic, concise, evidence-bearing output.
- Scope: Agent schema, receipts, budgets, errors, and examples; no vendor-specific dialect.
- Status: draft
- Set: awcliux
- Order: 3
- Highest E allocated: 03
- Author: OpenAI
- Id: 8su0r3

## Workflow history

- 2026-08-22 draft (OpenAI): created from agent/pipe output audit.

## Goal

Make output easy for GPT, Gemini, Opus, GLM, shells, and CI to parse without inferring success from prose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Compact records

- [ ] E-01 Define `aw.agent/v1` JSONL with closed record kinds and required fields; use one result for bounded output and summary-plus-items only for streams.
  - Depends on: none
  - Expected outcome: every command emits schema-valid, ANSI-free records.
  - Execution state: pending

### Material change 2: Evidence receipts

- [ ] E-02 Require outcome, applied/preview, completeness, changed targets, verification, evidence, omitted counts, and safe next command; never report `ok` for skipped, partial, unverified, or cannot-run work.
  - Depends on: E-01
  - Expected outcome: ambiguous output cannot support greenwashed completion.
  - Execution state: pending

### Material change 3: Token control

- [ ] E-03 Add compact defaults, `--fields`, `--limit`, and `--verbose`/explicit JSON escape hatches; truncation records retain totals and continuation commands.
  - Depends on: E-01
  - Expected outcome: fewer tokens without silent loss of decision facts.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Current agent formats include JSON, JSONL, TSV, path-only text, and unchanged boards.
- Sort records; use repo-relative normalized paths when unambiguous; omit unstable timestamps.
- Exit codes alone are insufficient because agents may receive captured text without process metadata.

## Findings

Ambiguity, not model identity, is the core defect. Gemini's completion bias is best countered by mandatory `outcome`, `complete`, `verified`, `remaining`, and `evidence` fields.

## Proposed changes (ordered, validatable)

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check plans","outcome":"clean","exit":0,"checked":17,"findings":0,"verified":true,"evidence":["ipd-lint:author"],"next":null}
```

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"rename plans","outcome":"preview","exit":0,"applied":false,"complete":false,"changes":4,"target":"plans/6psux0","next":"aw rename plans 6psux0 --slug new-slug --apply"}
```

```json
{"schema":"aw.agent/v1","kind":"summary","cmd":"attention","outcome":"findings","exit":0,"total":49,"emitted":20,"omitted":29,"complete":false,"next":"aw attention --agent --limit 50"}
```

Cannot-run domain errors are schema-valid stdout records with exit 2. Unexpected serialization/startup faults use stderr; never duplicate a diagnostic on both streams.

## Deferred / out of scope (with reason)

- XML/YAML/Markdown and vendor formats multiply ambiguity. Full contents belong behind `aw show`.

## Scope check

- Over-scope: none.
- Under-scope: review sensitive paths before expanding evidence.

## Required tests / validation

Schema-test every kind; fuzz paths; assert ordering, stable bytes, and size; cover skipped, partial, preview, changed-unverified, verified, truncated, and cannot-run.

## Spec / documentation sync

Publish schema, compatibility promise, exits, streams, examples, and “consume records; do not infer completion.”

## Open questions

### OQ-01: JSON or JSONL for one result?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: one newline-terminated object is both valid JSON and a JSONL stream.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: schema tests for every record kind and identical fixtures across model consumers.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover records, evidence, and bounded verbosity.

Review and explicit approval required; field removal or semantic changes are incompatible.

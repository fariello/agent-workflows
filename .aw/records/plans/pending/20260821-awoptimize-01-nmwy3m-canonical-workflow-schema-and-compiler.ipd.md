# IPD: Canonical Workflow Schema and Compiler

- Date: 2026-08-21
- Kind: child
- Concern: Make workflow semantics typed, reviewable, deterministic, and compilable into bounded execution packets and host adapters.
- Scope: New canonical workflow schema and loader under `agent_workflows/`, canonical source layout under `.aw/system/workflows/`, compiler and drift-check CLI, schema fixtures, and focused tests. No runtime execution, host launch, or workflow migration beyond compiler fixtures.
- Status: draft
- Set: awoptimize
- Order: 1
- Highest E allocated: 07
- Author: Codex GPT-5.6 Sol
- Id: nmwy3m

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created from the architecture research and full workflow inventory.

## Goal

Create one lossless semantic representation for all workflows. A deterministic compiler must validate that representation and emit a portable intermediate form, bounded step packets, documentation, and host-facing adapter inputs without allowing generated copies to become alternate sources of truth.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Schema and canonical source

- [ ] E-01 Define versioned types for workflow identity, aliases, intent, risk, interaction mode, permissions, inputs, outputs, requirement IDs, preconditions, ordered steps, dependencies, stop conditions, evidence predicates, validation checks, rollback, resumability, orchestration policy, and host capability requirements.
  - Depends on: none
  - Expected outcome: invalid IDs, cycles, missing evidence bindings, contradictory permissions, unknown capabilities, and terminal actions owned by a model fail schema validation.
  - Execution state: pending
- [ ] E-02 Define the canonical source layout with a concise entry file and progressive-disclosure resources for protocol, steps, rubrics, templates, examples, and deterministic scripts; document which files are authoritative and which are generated.
  - Depends on: E-01
  - Expected outcome: each workflow can be read incrementally while a semantic digest still covers the entire package.
  - Execution state: pending
- [ ] E-03 Implement a strict loader that resolves referenced resources within the package, rejects traversal and symlink escape, detects cycles and duplicate IDs, preserves source locations, and produces a normalized intermediate representation.
  - Depends on: E-02
  - Expected outcome: compiler errors identify exact workflow, field, file, and source location and never continue with a partial representation.
  - Execution state: pending

### Compiler and parity

- [ ] E-04 Implement deterministic compilation into: a portable prompt bundle, just-in-time step packets, machine-readable manifest, evidence requirements, human catalog row, and adapter-neutral command descriptor.
  - Depends on: E-03
  - Expected outcome: identical source yields byte-identical normalized outputs across two clean runs and ordering is explicit rather than filesystem-dependent.
  - Execution state: pending
- [ ] E-05 Add compiler invariants that reject any output where a profile removes a MUST requirement, validation predicate, stop condition, or scope fence; permit only transport, formatting, packet-size, and evidence-backed reasoning-profile knobs.
  - Depends on: E-04
  - Expected outcome: all host and model variants share the same semantic digest and acceptance predicates.
  - Execution state: pending
- [ ] E-06 Add `aw workflow validate`, `aw workflow compile`, and `aw workflow check-generated` commands with human, JSON, and agent output, nonzero failure codes, no ANSI in machine modes, and no writes in validation or drift-check modes.
  - Depends on: E-05
  - Expected outcome: CI and operators can validate source, regenerate adapters intentionally, and fail on hand-edited or stale generated files.
  - Execution state: pending
- [ ] E-07 Add focused property and golden tests for malformed packages, dependency cycles, stable ordering, semantic-digest parity, source mapping, path safety, generated drift, and round-trip preservation of every schema field.
  - Depends on: E-06
  - Expected outcome: the compiler proves structural completeness and deterministic parity but explicitly does not claim behavioral correctness.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The current manifest is Markdown and generates `.opencode/commands/` and `.claude/commands/` shims.
- Shared assess lenses and advise personas already demonstrate package composition.
- `plan-review-long` demonstrates just-in-time files but manually duplicates `plan-review` semantics.
- The CLI uses Python with `unittest`; agent modes are stable machine interfaces and must be ANSI-free.

## Findings

| Finding | Consequence |
|---|---|
| Markdown tables currently mix catalog, dispatch, arguments, and prose descriptions. | A typed manifest is needed before reliable compilation or conformance checks. |
| Modular and monolithic variants are manually kept in parity. | Compile both views from one source and compare semantic digests. |
| Host shims tell the model to read controlling text but do not prove all referenced text was resolved. | Loader diagnostics and compiled resource closure are required. |
| The existing IPD linter intentionally proves structure and state only. | Compiler validation must make equally explicit what it does and does not prove. |

## Proposed changes (ordered, validatable)

1. Freeze the schema and authority rules.
2. Load and normalize canonical packages safely.
3. Compile deterministic transport-neutral artifacts.
4. Enforce semantic parity across profiles.
5. Expose validation and drift checks through the CLI.
6. Prove determinism and malformed-input refusal.

## Deferred / out of scope (with reason)

- Durable run state and evidence validation belong to Order 02.
- Runtime scheduling and resumption belong to Order 03.
- Host-specific file formats and discovery probes belong to Order 05.
- Migration of production workflow packages belongs to Order 07 after the compiler contract is benchmarked.

## Scope check

- Over-scope: no host execution, model invocation, release, or product workflow behavior change.
- Under-scope: schema, package closure, normalized IR, compilation, semantic parity, CLI, and focused tests are all covered.

## Required tests / validation

- Focused schema, compiler, property, path-safety, and golden tests.
- Two clean compilations compared byte-for-byte.
- Mutation tests that delete one MUST rule, validation binding, stop condition, and source resource and prove validation fails.
- `aw workflow validate --all --agent` and `aw workflow check-generated --agent` with captured exit codes.
- Full repository suite and leak scan.

## Spec / documentation sync

- Add a schema reference, authoring guide, generated-file warning, and migration examples.
- Update the workflow manifest documentation only after generated compatibility output exists.

## Open questions

### OQ-01: YAML, JSON, or TOML for the typed manifest?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: evaluate parser dependencies, source-location diagnostics, comment support, merge ergonomics, and deterministic serialization; record the choice in an ADR before implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: schema fixtures cover every declared type and mutation fixtures prove each invalid invariant fails with a stable diagnostic and nonzero exit.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: package fixtures prove concise entry files resolve protocol, steps, rubrics, templates, scripts, and examples lazily while a closure digest changes when any authoritative resource changes.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: positive closure fixture loads with source locations; traversal, symlink escape, cycle, missing resource, duplicate ID, and partial parse fixtures each fail before IR emission.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: two clean compiles are byte-identical and golden outputs contain every schema field in prompt bundle, packet, manifest, evidence, catalog, and descriptor forms.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: profile ablations that remove or alter a MUST, scope fence, stop condition, or validation predicate fail; permitted transport/format/packet knobs preserve the semantic digest.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: captured CLI fixtures show stable human/JSON/agent output, no ANSI in machine modes, exit 0 only on success, distinct nonzero invalid/drift failures, and no writes from validate/check-generated.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: focused, property, golden, path-safety, source-map, round-trip, and generated-drift tests pass; deleting one required resource and hand-editing one generated adapter make the named tests fail.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: schema, loader, IR, compiler, and drift check form one indivisible authority boundary.

Do not execute until the parent orchestrator, ADR, and this child are reviewed and approved. Touch only declared schema, compiler, canonical-source fixtures, CLI wiring, tests, and documentation. Stop if implementation requires runtime, ledger, host-specific, or production migration changes.

Execution contract: use path-scoped commits; never push or use broad staging. Retain raw test output and exact exit codes. The executor may not mark V-items, assert behavioral model quality, or perform the terminal lifecycle transition. After independent validation passes every V-item, use the repository's post-gate lifecycle transaction.

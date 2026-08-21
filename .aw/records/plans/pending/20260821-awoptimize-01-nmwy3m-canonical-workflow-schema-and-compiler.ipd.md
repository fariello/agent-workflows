# IPD: Canonical Workflow Schema and Compiler

- Date: 2026-08-21
- Kind: child
- Concern: Make workflow semantics typed, reviewable, deterministic, and compilable into bounded execution packets and host adapters.
- Scope: New canonical workflow schema and loader under `agent_workflows/`, canonical source layout under `.aw/system/workflows/`, compiler and drift-check CLI, schema fixtures, and focused tests. No runtime execution, host launch, or workflow migration beyond compiler fixtures.
- Status: approved
- Set: awoptimize
- Order: 1
- Highest E allocated: 07
- Author: Codex GPT-5.6 Sol
- Approval: approved by Gabriele Fariello 2026-08-21
- Id: nmwy3m

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created from the architecture research and full workflow inventory.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Blocking OQ-01 (schema serialization format) RESOLVED with the maintainer to YAML for the canonical source, parsed build/authoring-time only so it is not a runtime dependency (D138); determinism via key-sorting at emit; single-source-of-truth via the compiler + check-generated drift test (E-06/E-07). Added an implementation constraint to keep YAML out of `agent_workflows/*` runtime paths and record the choice in DECISIONS during E-01. Size assessment standard (correct). No remaining open questions.
- 2026-08-21 approved (Gabriele Fariello, --by-human): human sign-off recorded; part of the approved foundational scope (Orders 00-04). Ready to execute via /ipd-lifecycle in dependency order.

## Goal

Create one lossless semantic representation for all workflows. A deterministic compiler must validate that representation and emit a portable intermediate form, bounded step packets, documentation, and host-facing adapter inputs without allowing generated copies to become alternate sources of truth.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Schema and canonical source

- [x] E-01 Define versioned types for workflow identity, aliases, intent, risk, interaction mode, permissions, inputs, outputs, requirement IDs, preconditions, ordered steps, dependencies, stop conditions, evidence predicates, validation checks, rollback, resumability, orchestration policy, and host capability requirements.
  - Depends on: none
  - Expected outcome: invalid IDs, cycles, missing evidence bindings, contradictory permissions, unknown capabilities, and terminal actions owned by a model fail schema validation.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_schema.py` (pure, stdlib-only, no YAML/FS/model/network side effects, per D139). Defines SCHEMA_VERSION, closed vocabularies (intents/risks/interaction/mutation-boundary/host-capabilities/evidence-kinds/forbidden-terminal-actions), id grammars (workflow/`R-NN`/`S-NN`), and `validate_workflow()` returning typed Findings. A smoke run confirmed a conforming workflow passes and an adversarial one is rejected on every named invariant (bad id, unknown enum, unknown capability, read-only vs allowed-path contradiction, duplicate requirement id, unknown requirement reference, forbidden terminal action `push`, dependency cycle S-01->S-02->S-01, missing validation). Formal V-01 evidence is captured in the validation pass, not here.
- [x] E-02 Define the canonical source layout with a concise entry file and progressive-disclosure resources for protocol, steps, rubrics, templates, examples, and deterministic scripts; document which files are authoritative and which are generated.
  - Depends on: E-01
  - Expected outcome: each workflow can be read incrementally while a semantic digest still covers the entire package.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_source.py` (layout contract): fixed `workflow.yaml` entry-file name, `_generated/` generated-subtree, `RESOURCE_DIRS` (steps/rubrics/templates/examples/scripts), authoritative-vs-generated rule, `semantic_digest()` (SHA-256 over sorted rel-path+content-hash for authoritative files only), `assert_no_symlink_escape()`, and a build-time-only `parse_entry()` that lazily imports PyYAML (never a runtime import; fails closed with SourceError if PyYAML absent, per D139). Added an example package `tests/fixtures/workflow-src/plan-review/` (entry + protocol + 2 step bodies). Also added the `resources` optional field to the E-01 schema (`WF-E028`), found by exercising the fixture. Verified: entry parses + validates clean against E-01; digest is stable across calls, excludes `_generated/`+`__pycache__`/`.pyc` cruft, changes on an authoritative edit; symlinks are refused. Formal V-02 evidence in the validation pass.
- [x] E-03 Implement a strict loader that resolves referenced resources within the package, rejects traversal and symlink escape, detects cycles and duplicate IDs, preserves source locations, and produces a normalized intermediate representation.
  - Depends on: E-02
  - Expected outcome: compiler errors identify exact workflow, field, file, and source location and never continue with a partial representation.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_loader.py` composing E-01 (schema) + E-02 (layout/digest/parse) into `load_package() -> LoadResult(ok, ir|None, findings)`. Fails closed: on ANY finding it returns `ir=None` (no partial IR). Resolves every referenced resource and proves closure (exists, regular file, inside package, not generated/cruft, not a symlink, no traversal), preserving source locations as `resources[<rel>] = {path, sha256, text}`. Findings carry `package-id:workflow.yaml#field` provenance. IR is a JSON-serializable dict `{ir_version, digest, source_root, workflow, resources}`. Verified against the fixture (loads to full IR) and 5 adversarial packages (missing resource WF-L013, traversal escape WF-L010, schema-invalid intent WF-E021 with provenance + ir None, dependency cycle WF-E05C, missing entry WF-L001) - each fails closed with a precise location. Formal V-03 evidence in the validation pass.

### Compiler and parity

- [x] E-04 Implement deterministic compilation into: a portable prompt bundle, just-in-time step packets, machine-readable manifest, evidence requirements, human catalog row, and adapter-neutral command descriptor.
  - Depends on: E-03
  - Expected outcome: identical source yields byte-identical normalized outputs across two clean runs and ordering is explicit rather than filesystem-dependent.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_compiler.py`: `compile_workflow(ir)` emits all six `PROJECTION_KEYS` (prompt_bundle, step_packets, manifest, evidence, catalog_row, command_descriptor) and `render_generated_files()` renders them to a deterministic `_generated/`-relative filename->text map. Determinism via stdlib `json.dumps(sort_keys, fixed separators)` + explicit list ordering (steps/requirements by id, resources by declared order), never FS order (D139 needs no dep). Pure transform (no FS/model/network). Verified against the fixture: 6 projections present, manifest binds the source digest, step packets carry only per-step action/satisfies/depends_on/evidence/body, and TWO independent load+compile+render runs are BYTE-IDENTICAL. Formal V-04 evidence in the validation pass.
- [x] E-05 Add compiler invariants that reject any output where a profile removes a MUST requirement, validation predicate, stop condition, or scope fence; permit only transport, formatting, packet-size, and evidence-backed reasoning-profile knobs.
  - Depends on: E-04
  - Expected outcome: all host and model variants share the same semantic digest and acceptance predicates.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_profile.py`: `validate_profile()` (closed `ALLOWED_PROFILE_KEYS` = name/max_packet_chars/output_format/reasoning_level/verifier_policy; rejects unknown keys + bad values, fail closed), `semantic_view()`/`semantic_digest()` over ONLY the acceptance-relevant subset (requirements+evidence, validations+evidence, step id/satisfies/depends_on/stop_conditions, scope fence) - deliberately excluding prose/formatting so transport tuning is allowed - and `check_parity()` returning a precise reason. Verified: a transport-only variant (prompt annotation + packet-body truncation) preserves the semantic digest (parity ok); dropped validation, weakened requirement evidence, widened scope fence (planning-only->product), and changed step-dependency shape are each REJECTED with a precise reason; invalid profiles rejected. Formal V-05 evidence in the validation pass.
- [x] E-06 Add `aw workflow validate`, `aw workflow compile`, and `aw workflow check-generated` commands with human, JSON, and agent output, nonzero failure codes, no ANSI in machine modes, and no writes in validation or drift-check modes.
  - Depends on: E-05
  - Expected outcome: CI and operators can validate source, regenerate adapters intentionally, and fail on hand-edited or stale generated files.
  - Execution state: performed
  - Execution note: implemented `agent_workflows/workflow_cli.py` (`run_workflow`) + wired the `workflow` parser and dispatch into `agent_workflows/cli.py`. Verified through the real `aw`/`python3 -m agent_workflows` CLI: `validate` (human `ok:`/`FAIL`, `--agent` JSONL, exit 0 clean); `compile` dry-run lists 7 would-write files and writes NOTHING, `--apply` writes atomically (temp+os.replace); `check-generated` clean after compile, then detects a hand-edit (`changed`) and an unexpected file (`unexpected`), exit 1. Exit codes are distinct: 0 clean, 1 conformance/drift on a real package, 2 invocation error (bad path -> WF-L001). Machine modes (`--agent` JSONL / `--json` array) emit no ANSI; validate + check-generated never write. Formal V-06 evidence in the validation pass.
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

### OQ-01: YAML, JSON, or TOML for the canonical workflow source?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED to YAML for the CANONICAL SOURCE, parsed only at DEV/BUILD/AUTHORING time (2026-08-21, /plan-review with the maintainer). The compiler (E-04) runs at build/authoring time and emits stdlib-parseable projections (JSON manifest/packets/evidence + Markdown) that are what ship; the installed CLI never parses the YAML source at runtime, so the YAML parser is a BUILD-TIME-ONLY dependency (the same category as `hatchling`), not a runtime dependency. This is consistent with dependency-minimization as a principle, not a prohibition (DECISIONS D138). YAML is chosen over JSON for the source because a human authors and reviews that source and YAML supports comments and friendlier merges; it is chosen over TOML because workflows are deeply nested and stdlib `tomllib` is read-only (no writer). Determinism (E-04's byte-stable requirement) is met by sorting keys and pinning writer options at emit time regardless of source format. The single-source-of-truth guarantee comes from the compiler plus the `check-generated` drift test (E-06/E-07), not from the format. IMPLEMENTATION CONSTRAINT for the executor: keep YAML strictly build-time (never import a YAML parser from `agent_workflows/*` runtime paths; a build/authoring tool or the `[test]`/dev extra may use it), and record the choice + the build-time boundary in a short DECISIONS entry during E-01 before writing the loader.

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

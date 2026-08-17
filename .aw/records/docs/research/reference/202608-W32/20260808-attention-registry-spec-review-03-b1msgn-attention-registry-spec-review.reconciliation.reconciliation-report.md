---
id: b1msgn
created: 20260808
set: attention-registry-spec-review
order: 03
topic: [attention-registry, spec-review, external-review]
model: reconciliation
kind: reconciliation-report
status: reference
outcome: none-yet
summary: Consolidated reconciliation of the gpt-5.6/Gemini/Sonnet-5 reviews of the attention-registry spec
consumed-by: []
---

# Consolidated findings: attention registry and cross-tree status model

## Executive conclusion

All three assessments support the central architectural idea: each artifact tree should retain its native lifecycle, while a deterministic tool maps those native states into a small cross-tree attention model that agents and humans can read. The current specification should not be implemented unchanged, however. The strongest design is a read-only `aw attention` command that performs a full deterministic scan whenever it runs, validates every included artifact, and emits either machine-readable JSON or a human-readable board. In v1, the aggregate view should not be committed to Git. Source artifacts remain the only authority, and `aw attention --check` enforces their contracts directly. This avoids stale generated registries, routine cross-branch conflicts, and an impossible promise of atomicity across a source artifact plus two generated files. Domain tools should own all writes, including a new `aw specs` command for spec status and history changes. The attention model should use five classes, `ready`, `active`, `blocked`, `done`, and `parked`, because an agent must distinguish work it can advance now from work that is waiting on a gate. Any malformed, missing, unknown, contradictory, or unclassified state must produce a structured violation and a nonzero exit. `/whatnext` must stop normal prioritization when the view is invalid and present those violations to the agent for resolution.

This recommendation accepts the main objective of the original proposal while removing machinery that does not materially improve tracking or enforcement. It provides a rigorous source contract, deterministic programmatic output, a human review surface, CI enforcement, and a direct remediation path for agents.

## How the three assessments compare

| Topic | GPT-5.6 Codex | Gemini | Sonnet 5 | Consolidated judgment |
| --- | --- | --- | --- | --- |
| Native lifecycles | Keep native enums and map them | Keep native enums and map them | Keep native enums and map them | Keep native enums. This is unanimous and correct. |
| Attention classes | Add an explicit `blocked` class, producing five classes | Keep the proposed four classes | Four can work, but deferred needs a typed distinction | Use five classes. `blocked` is operationally distinct from `ready` and `parked`. |
| Mapping purity | Current function is not pure because execution and gate meaning are outside status | Generally accepts the mapping as written | Current function is not pure because deferred behavior depends on gate meaning | Make mapping exhaustive and pure. Do not infer activity or gate state from prose, dates, file metadata, or context. |
| Aggregate registry | One roll-up, preferably JSON as canonical generated data | Do not commit a registry; generate at runtime | One committed roll-up is acceptable; questions dual Markdown and JSON | Generate the aggregate view on demand in v1. Do not commit either aggregate file. |
| Markdown and JSON | Prefer one committed JSON file and render Markdown on demand as the simpler option | Emit to stdout or an ignored cache | Consider committing only JSON and rendering Markdown on demand | Emit both formats on demand from one in-memory record set. No cache unless performance evidence requires one. |
| Write ownership | Owner adapters; a later attention router could call them in-process | `aw attention` read-only; introduce `aw specs` | Refuse and point to owner commands for tool-owned trees | `aw attention` remains read-only. Domain tools own writes. Add `aw specs` for specs. No generic write router in v1. |
| Gate representation | Typed single-line gate grammar | Required free-text `Gate` field | Closed `Gate-Kind` plus free-text `Gate` | Use discrete typed fields: `Gate-Kind`, `Gate-Ref`, and optional `Gate-Summary`. |
| CI timing | Put enforcement in Phase 1 | Contract checking remains valuable, with no registry drift check | Put enforcement in Phase 1 | CI enforcement is part of the first usable release. |
| Atomicity | Multi-file atomicity is not available through independent replacements | Flags cross-platform atomic-write concerns | Notes dual-file drift risk | Eliminate aggregate writes in v1. Domain writes are atomic per source artifact only. |
| Phasing | Add a contract phase, then read-only scanner, then writes | Include `aw specs` writes in Phase 1 | Scanner first; write verbs may follow, but phase language must agree | Define contracts and fixtures first, then ship scanner, `aw specs`, `/whatnext`, and CI as one coherent v1. |
| Nonconforming artifacts | Fail with structured contract violations | Warn locally and fail in CI | Fail through `--check` drift records | Fail consistently in local and CI modes. Never silently skip an included artifact. |

## Findings that should survive

### 1. Native statuses remain authoritative

Forcing one lifecycle enum across plans, research, specs, prompts, and communications would erase useful domain meaning or produce a global union filled with values irrelevant to most trees. Each tree's owner must continue to define:

- Its native status enum.
- Legal transitions.
- Directory disposition rules, when applicable.
- Required metadata and history rules.
- How source files are safely changed.

`aw attention` owns only normalization, validation, cross-tree presentation, and the public output schema. It must not redefine or bypass native lifecycles.

### 2. The mapping must be complete, explicit, and pure

The original `class_of(tree, native_status)` claim is contradicted by examples that depend on whether approved work has started and whether a deferred gate is open or represents a decision to stop. Those facts cannot be inferred from the declared inputs.

The corrected rule is:

```text
attention_class = class_of(tree, native_status)
```

This remains pure only if each native status carries enough meaning to map deterministically. Therefore:

- An approved item is `ready`, not `active`, unless the native lifecycle explicitly records active execution.
- A deferred item is always `blocked` and must have a valid unresolved gate.
- A deliberately inactive item must use a native parked, archived, superseded, or not-executed state. It must not overload `deferred`.
- If plans must distinguish approved from executing, the plans owner must add an explicit native `executing` state or another owner-defined machine field. The attention scanner must not infer execution from history prose, modification time, a lock file, or agent context unless that signal becomes a formal owner contract.
- Every native enum value in every included tree must have exactly one mapping. Unknown values are violations, never omissions or default mappings.

Mapping fragments should live next to each tree's native enum and be aggregated by the attention module. This makes an enum change and its cross-tree mapping likely to occur in the same code change. Tests must compare each declared enum with its mapping keys and fail on either missing or extra entries.

### 3. Use five attention classes

The recommended cross-tree enum is:

| Attention class | Meaning | `/whatnext` behavior |
| --- | --- | --- |
| `ready` | A concrete action can be taken now | Candidate for selection and prioritization |
| `active` | Work is explicitly in progress | Surface prominently for continuity or completion |
| `blocked` | Work is intended to continue, but a named gate prevents progress | Report the blocker; select only if the gate itself can be resolved |
| `done` | Successfully complete or accepted as a standing reference | Hidden by default; available by filter |
| `parked` | Intentionally inactive, archived, superseded, abandoned, or not executed | Hidden by default; available by filter |

The fifth class is not cosmetic. Without `blocked`, an agent cannot distinguish work it should start from work it cannot advance. Combining both under `needs-attention` defeats the main purpose of the cross-tree view.

The display may still use an umbrella heading such as "Attention" for `ready`, `active`, and `blocked`, but the machine output must preserve the three values.

### 4. Generate the aggregate view on demand in v1

The aggregate is a projection of source artifacts, not a second source of truth. A full standard-library scan of this repository scale should be inexpensive, and it avoids asking a model to open and interpret every artifact. `/whatnext` can execute one deterministic command and consume its JSON output, which satisfies the cheap single-read objective without a committed snapshot.

Do not commit `.agents/ATTENTION.json` or `.agents/ATTENTION.md` in v1. Instead provide:

```text
aw attention
aw attention --format markdown
aw attention --format json
aw attention --check
aw attention --check --agent
```

Bare `aw attention` should be read-only and show the human board. JSON and Markdown must be rendered from the same in-memory record collection. No aggregate file is written as a side effect.

This decision removes four material risks:

- A source artifact cannot disagree with a stale committed aggregate.
- Independent branches changing unrelated artifacts do not collide on one generated roll-up.
- Markdown and JSON cannot drift from one another between commits.
- A write command does not need to pretend that three independent file replacements form one atomic transaction.

Do not add a cache in v1. Add one only after measurement demonstrates a real performance problem. If a future integration cannot execute the CLI and requires a file, add an explicit `aw attention snapshot` command later. Such a snapshot must remain a generated projection with a schema version, deterministic bytes, and a documented freshness contract. A committed snapshot should be reconsidered only if repository browsing or a non-executable consumer provides a demonstrated benefit greater than its merge and drift costs.

### 5. Make `aw attention` read-only and give writes to domain owners

All three assessments reject uniform direct writes by the attention layer, although they differ on routing. The clearest v1 boundary is:

- `aw plans` owns plans.
- `aw research` owns research.
- `aw specs` owns specs.
- Other tree tools own their respective artifacts when they are added.
- `aw attention` reads and validates all included trees but changes none of them.

Introduce at least:

```text
aw specs set PATH --status STATUS --message TEXT
aw specs note PATH --message TEXT
aw specs check PATH
```

`set` must validate the requested transition, update status and related gate fields, append one history record, validate the complete result in memory, and atomically replace the single source file. `note` appends history without changing status. Neither command stages, commits, or pushes Git changes.

For plans and research, `aw attention` should return the exact owner command when a user attempts an unsupported write. A generic in-process router can be reconsidered later, but only after every owner exposes a stable mutation API. It is not needed to meet the tracking objective.

### 6. Make gates structured and enforceable

A deferred item must identify the condition preventing progress. Free text alone is insufficient for reliable validation or future automation. Use discrete fields:

```text
Status: deferred
Gate-Kind: issue
Gate-Ref: https://github.com/fariello/agent-workflows/issues/123
Gate-Summary: Waiting for the upstream schema decision
```

Required rules:

- `Gate-Kind` is required for `deferred` and uses a closed enum: `artifact`, `decision`, `todo`, `issue`, `date`, or `external`.
- `Gate-Ref` is required and is validated according to the kind.
- `Gate-Summary` is optional human context and must never determine machine behavior.
- Gate fields are forbidden for statuses other than `deferred`; owner tools remove them when the item leaves deferred status and preserve the resolution in workflow history.
- `date` uses `YYYY-MM-DD` in UTC terms.
- `artifact` uses a repository-relative POSIX path with an optional Markdown anchor.
- `todo` and `decision` use stable repository identifiers.
- `issue` uses an absolute issue URL.
- `external` uses a nonempty stable reference chosen by the repository.

`deferred` means the gate is unresolved. When the condition clears, the artifact must transition to `ready`, `active`, `done`, or `parked` through its native status. A separate mutable gate-state field is unnecessary and would create another contradiction surface.

### 7. Standardize specs without confusing lifecycle and authority

The spec lifecycle should include enough state for useful tracking:

```text
draft -> reviewed -> approved -> implementing -> implemented
```

Additional states:

```text
deferred
parked
superseded
```

Recommended mapping:

| Spec status | Attention class |
| --- | --- |
| `draft` | `ready` |
| `reviewed` | `ready` |
| `approved` | `ready` |
| `implementing` | `active` |
| `implemented` | `done` |
| `deferred` | `blocked` |
| `parked` | `parked` |
| `superseded` | `parked` |

Do not use `canonical` as a lifecycle state. A spec can be authoritative and still be unimplemented. If canonicality must be tracked, use a separate owner-defined field such as `Canonical: true`; it must not alter the attention mapping unless the specification defines a real lifecycle consequence.

The spec migration should preserve every repository-relative path. It should normalize metadata and add workflow history without moving files.

### 8. Define the output contract before implementation

The JSON output is an API and must be versioned. A minimum shape is:

```json
{
  "schema_version": 1,
  "mapping_version": 1,
  "valid": true,
  "items": [
    {
      "id": "S012",
      "path": ".agents/docs/specs/example.md",
      "tree": "specs",
      "native_status": "deferred",
      "attention_class": "blocked",
      "gate": {
        "kind": "issue",
        "ref": "https://github.com/example/project/issues/123",
        "summary": "Waiting for the upstream schema decision"
      },
      "last_history_at": "2026-08-08T23:45:00Z"
    }
  ],
  "violations": []
}
```

The full schema must define:

- Required and optional fields.
- Exact types and null behavior.
- Enum values.
- Path normalization.
- ID uniqueness.
- Ordering rules.
- Schema and mapping version semantics.
- Whether history uses a date or timestamp.
- Error representation when `valid` is false.

If any included artifact is invalid, the command must return nonzero. JSON output may include valid records for diagnosis, but it must set `valid` to `false` and include every detected violation. `/whatnext` must not treat an incomplete view as authoritative.

The existing drift record form should remain the machine-readable violation contract:

```text
location<TAB>rule<TAB>detail
```

The specification must define how tabs, newlines, and backslashes are escaped or rejected. Rule identifiers must be stable enough for tests and agent remediation guidance.

### 9. Fail closed and report all violations

The scanner must complete a full scan, collect all detectable violations, and return them together. It must not silently skip malformed artifacts or downgrade local failures to warnings. Local agents and CI should observe the same validity result.

At minimum, `aw attention --check` must detect:

- Missing required status.
- Unknown native status.
- Native status with no attention mapping.
- Missing, unknown, malformed, or contradictory gate fields.
- Missing or malformed required workflow history.
- Duplicate artifact IDs.
- Duplicate normalized paths.
- Disposition directory and terminal status disagreement.
- Invalid or unstable repository-relative paths.
- Unsupported encoding or malformed front matter.
- Included artifact that the walker cannot read.
- Included tree without a declared contract or mapping.
- New artifact tree that is neither explicitly tracked nor explicitly excluded.

Maintain an explicit tree policy inventory. Every known artifact tree is either `tracked` with an owner and mapping or `excluded` with a rationale. A newly discovered tree without a policy is a violation such as `attention.unclassified-tree`. This prevents silent blind spots while allowing walkthroughs, roadmaps, and implementation-support directories to remain intentionally outside the registry.

Contract violations must prevent a successful view. The command should state the exact repository-relative path, stable rule identifier, and actionable detail. When a safe owner command exists, include it in the remediation text.

### 10. Determinism must be specified byte for byte

The following are requirements, not implementation suggestions:

- Perform a full scan on every invocation. Do not depend on Git diffs for correctness.
- Use repository-relative POSIX paths.
- Sort by an explicit fixed class order, then normalized path, then ID as a tie-breaker.
- Read and write UTF-8.
- Emit LF line endings and exactly one final newline.
- Use a fixed JSON key order, indentation, separators, and ASCII escaping policy.
- Do not include generation timestamps, filesystem modification times, absolute paths, terminal width, locale-sensitive formatting, timezone-sensitive values, random values, or hash iteration order.
- Parse `last_history_at` from validated workflow history, never from file modification time.
- Define symlink handling and reject any path that escapes the repository.
- Produce identical output from identical source bytes across supported environments.

Ordinary JSON validity does not provide canonical byte output because JSON objects are unordered. The project need not implement RFC 8785, but it must define and test a local canonical serialization profile.

### 11. `/whatnext` must consume the tool, not rescan artifacts

The revised workflow is:

1. Execute `aw attention --format json`.
2. If the command returns nonzero or `valid` is false, present all violations to the agent and stop normal prioritization until they are addressed or explicitly deferred by the user.
3. If valid, prioritize `active`, then `ready`; show `blocked` with gate details; omit `done` and `parked` unless requested.
4. Read only the specific artifacts selected from the output.
5. Consult Git state and `TODO.md` as separate, explicitly bounded sources because they contain information outside artifact status.

Do not silently fall back to re-scanning every artifact when the command is missing, incompatible, or invalid. That would recreate the cost and nondeterminism the tool exists to remove. Instead, report the failure and the exact remediation. An explicit diagnostic mode may inspect raw artifacts when requested.

This behavior is testable at the workflow boundary: verify the command invoked, the handling of exit status and `valid`, the set of selected paths, and the stop-on-violation behavior. Do not write acceptance criteria about what a language model "reads" unless file access is instrumented.

## Recommended implementation phases

### Phase 0: Contract and fixtures

- Inventory exact enums, directory dispositions, ID rules, metadata syntax, and history grammar for every proposed v1 tree.
- Finalize the five attention classes and exhaustive mapping tables.
- Define tree policy inventory, gate fields, JSON schema, Markdown rendering, Drift rules, and deterministic serialization.
- Create fixture repositories covering every native status and violation.
- Resolve all load-bearing open questions before coding.

### Phase 1: Coherent v1

- Normalize existing specs without changing paths.
- Implement `aw specs set`, `aw specs note`, and spec validation.
- Implement the read-only full scanner and both output formats.
- Include plans, research, and specs. Add prompts and communications only if their full contracts and mappings are completed in Phase 0.
- Implement `aw attention --check` and `--agent` reporting.
- Rewire `/whatnext` to consume JSON and stop on violations.
- Wire the same check into CI before the feature is considered complete.

### Phase 2: Operational refinement

- Add owner tools or adapters for additional structured trees.
- Add filters, richer remediation hints, and optional snapshot export.
- Add caching only if benchmarks justify it and the cache cannot affect correctness.
- Consider an in-process convenience router only if it reduces real user friction without duplicating owner logic.

### Phase 3: Deliberate scope expansion

- Evaluate roadmaps and walkthroughs for actual lifecycle semantics.
- Add a tree only when it has a real owner, closed native status contract, history contract, and exhaustive mapping.
- Revisit a persisted snapshot only for a demonstrated consumer that cannot execute the CLI.

## Revised acceptance criteria

The following criteria should replace corpus-specific and ambiguous assertions in the original specification.

1. A fixture covers every declared native status in every included tree, and each maps to exactly one attention class.
2. Adding a native status without a mapping makes the mapping coverage test and `aw attention --check` fail.
3. Missing or unknown status, invalid gate metadata, missing or malformed required history, duplicate IDs, path or disposition conflicts, unreadable included files, and unclassified trees each produce a stable named violation and exit code 1.
4. A deferred fixture without each required gate component fails. Valid gate kinds pass their kind-specific validation.
5. An invalid scan reports all detectable violations and never returns `valid: true` or a successful exit.
6. Two runs over identical source bytes produce byte-identical JSON, Markdown, and agent output under different working directories, locales, timezones, and supported operating systems.
7. Deleting, renaming, or moving an artifact is reflected on the next full scan without incremental state or cache cleanup.
8. `aw specs set` validates a legal transition, updates related gate fields, appends one valid history record, and atomically replaces one source file. Invalid transitions leave the file byte-identical.
9. `aw specs note` appends one valid history record and does not change status or unrelated content.
10. Existing plans and research checks remain byte-for-byte unchanged on unchanged fixtures.
11. `/whatnext` invokes the JSON view first, stops and surfaces violations when invalid, and opens only paths selected from a valid view, plus explicitly allowed Git and TODO sources.
12. CI runs the same contract check used locally and rejects every contract violation described above.
13. No v1 command writes an aggregate attention file, cache, Git index entry, commit, or remote change as an implicit side effect.

## Original requirements that must change

- G3, F2, F3, A1, and A2 must no longer require committed registry files or registry-to-disk drift checking in v1.
- G4, F5, F6, and A3 must move writes from `aw attention` to the appropriate domain owner, beginning with `aw specs`.
- G4 must describe atomic replacement of one source artifact, not atomic mutation of a source plus aggregate files.
- G7 and Section 13 must agree with the actual v1 scope.
- A1 must use fixtures rather than counts from the live repository.
- A2 must concern contract-relevant source changes, not any hand edit.
- A4 must be split into independently testable violation cases.
- A6 must test observable workflow behavior rather than uninstrumented model reading.
- F4 must define the `--agent` record schema and escaping.
- F7 must define the workflow history grammar and migration behavior.
- G8 must become a measurable promise that the v1 migration preserves existing repository-relative paths.
- N6 should move to a documentation style rule unless a defined lint check enforces it.

## Decisions intentionally rejected or deferred

### Rejected for v1

- One unified lifecycle enum across all trees.
- A committed `.agents/ATTENTION.json` or `.agents/ATTENTION.md`.
- Per-tree attention registries plus a roll-up.
- Generic `aw attention set` and `aw attention note` writes.
- Inferring active work from approved status, history prose, file modification time, or agent context.
- Treating free-text gate summaries as machine state.
- Silently skipping invalid artifacts.
- Unbounded `/whatnext` fallback to raw artifact scanning.
- Time-based hot windows in deterministic output.

### Deferred until justified

- Optional snapshot export.
- A local cache.
- An in-process cross-tree write router.
- Roadmap and walkthrough status adoption.
- A persisted registry for consumers unable to execute the CLI.
- Priority fields beyond the attention classes.

## Overall recommendation

Approve the project direction, but revise the specification before implementation. The revised design should make native artifacts authoritative, make the aggregate view ephemeral and deterministic, give writes to domain owners, distinguish blocked work from actionable work, and fail closed on every contract violation. This design directly serves the stated outcome: agents and humans receive a rigorous, current, programmatically readable view, while every nonconforming artifact is surfaced at execution time and enforced identically in local workflows and CI.

## Sources and evidentiary basis

### Source assessments

- `attention-registry-spec-review-gpt-5.6-codex(1).md`
- `attention-registry-spec-review-gemini.md`
- `attention-registry-spec-review-sonnet-5.md`

### Technical references retained from the assessments

1. [Python 3.9 `os.replace` documentation](https://docs.python.org/3.9/library/os.html#os.replace). Supports atomic replacement of one source and destination, not a transaction spanning independent replacements.
2. [SQLite super-journal documentation](https://sqlite.org/tempfiles.html#super_journal_files). Illustrates that atomic commitment across multiple files requires an explicit coordination protocol.
3. [RFC 8259, JSON](https://www.rfc-editor.org/rfc/rfc8259). Defines JSON objects as unordered collections, supporting the need for a project-specific canonical serialization profile.
4. [RFC 8785, JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785). Provides a technical precedent for invariant JSON representation and deterministic property sorting.
5. [Reproducible Builds documentation on timestamps](https://reproducible-builds.org/docs/timestamps/). Supports excluding current timestamps and file modification times from deterministic generated output.
6. [Reproducible Builds documentation on locales](https://reproducible-builds.org/docs/locales/). Supports fixing sorting, timezone, and encoding behavior.
7. [RFC 3339, Internet timestamps](https://www.rfc-editor.org/rfc/rfc3339). Supports a precise UTC timestamp format for workflow history.
8. [Python 3.9 `argparse` subcommands](https://docs.python.org/3.9/library/argparse.html#sub-commands). Confirms that the proposed CLI separation is compatible with the standard-library-only constraint.

The status taxonomy, write ownership, registry persistence, phasing, and acceptance-test recommendations are architectural judgments based on the three reviews and the specification's stated objectives. The references above support relevant technical premises but do not mandate those design choices.

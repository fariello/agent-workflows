---
id: krgxp6
created: 20260808
set: attention-registry-spec-review
order: 00
topic: [attention-registry, spec-review, external-review]
model: gpt56
kind: assessment
status: reference
outcome: none-yet
summary: gpt-5.6 (Codex) review of the attention-registry spec
consumed-by: []
---

# Review of the attention registry and cross-tree status model

## Overall assessment

The core direction is sound: preserve each artifact tree's native lifecycle, derive a small cross-tree attention view, generate one repository-level registry, and make `/whatnext` consume that deterministic view. That is substantially safer than forcing unrelated trees into one lifecycle or asking a model to rediscover state on every run. However, the current specification is not yet implementation-ready. Its proposed mapping is not always a pure function of `(tree, native_status)`, its four classes conflate actionability with lifecycle state, its write path promises multi-file atomicity that the filesystem cannot provide, and several phase, requirement, and acceptance statements contradict one another. I recommend approving the architecture only after the spec defines a complete mapping table, adds an explicit blocked class or equivalent machine field, makes the JSON registry the canonical generated representation, treats Markdown as a deterministic projection, and assigns every mutation to the owning tree implementation through a shared adapter API.

## Strongest concerns, ranked

### 1. The proposed mapping is not pure as written

Section 6 says `class_of(tree, native_status)` is pure, but its examples depend on facts not present in those two inputs:

- A plan with status `approved` or `auto-approved` is called `in-flight` only when it is "under execution." The status itself does not establish that execution has started.
- A `deferred` artifact may be `needs-attention` when it has an open gate, or `parked` when the gate reflects a deliberate decision. Neither the status nor the mere presence of a gate distinguishes those cases.
- A spec described as `canonical` may mean implemented, authoritative, or merely the current design reference. Those meanings are not interchangeable.

This is a correctness defect, not just an incomplete table. Either every native lifecycle must encode the distinctions needed for the mapping, or the mapping signature must include additional normalized fields such as gate state and activity state. Do not let the scanner infer execution from history prose, modification time, directory location, or an agent's interpretation.

### 2. The four classes do not preserve the distinction `/whatnext` most needs

`needs-attention` currently includes both actionable work and work that cannot advance until a gate changes. Those require opposite behavior from `/whatnext`: one should be proposed for action now, while the other should be reported with its blocker and normally skipped. Likewise, `parked` combines intentionally abandoned or superseded work with deferred work that may become actionable later.

Use five classes:

1. `ready`: an action can be taken now.
2. `active`: work is explicitly in progress.
3. `blocked`: work is intended to continue, but a named gate prevents progress.
4. `done`: successfully complete or accepted as a standing reference.
5. `parked`: intentionally inactive, abandoned, archived, superseded, or not executed.

If compatibility requires the name `needs-attention`, use it instead of `ready`, but do not place blocked items in it. The registry can still present `ready`, `active`, and `blocked` together under a human-facing "attention" heading.

### 3. Multi-file atomicity is impossible under the proposed write flow

`set` changes an artifact, appends history, and refreshes two registry files. An atomic rename can make each individual file replacement atomic, but it cannot by itself atomically commit all three files as one filesystem transaction. Python 3.9 documents `os.replace` as atomic when one source is successfully renamed to one destination. SQLite's documentation is useful corroborating evidence: atomic commitment across multiple files requires an additional coordination mechanism, its super-journal, and without that mechanism atomicity holds only per file. The conclusion that three independent `os.replace` calls do not form one transaction is an inference from these documented guarantees, not a direct quotation from either source. A crash or exception can therefore leave a valid source artifact with stale registries, or one registry refreshed and the other stale. See [Python 3.9 `os.replace`](https://docs.python.org/3.9/library/os.html#os.replace) and [SQLite temporary files and super-journals](https://sqlite.org/tempfiles.html#super_journal_files).

The source artifact must be authoritative. A write command should:

1. Validate the requested transition and construct the complete new artifact in memory.
2. Atomically replace that one source file.
3. Recompute both registry projections from source state, write temporary files, and atomically replace each destination.
4. Return nonzero if registry refresh fails, clearly stating that the source mutation succeeded and `aw attention index` must be rerun.

`aw attention --check` then provides deterministic recovery. The spec must call this "atomic source mutation followed by deterministic index refresh," not an atomic three-file update.

### 4. Write ownership is unresolved and currently duplicated

Section 8.2 allows delegation or refusal, F5 requires "delegates/refuses," OQ7 remains open, and Phase 2 promises delegation. This ambiguity invites two implementations of validation, transition rules, front-matter rewriting, history formatting, directory disposition, and indexes.

The attention layer should never independently rewrite a tool-owned tree. Each tree owner should expose an internal mutation adapter. `aw attention set` may be retained as a convenience router, but it must call that adapter in-process. It must not shell out, duplicate the mutation logic, or directly edit the file. For a tree without a mutation adapter, it should be read-only and name the owning command or report that mutation is unsupported.

For specs, either introduce a small `specs` owner module or explicitly designate the specs adapter as owned by the attention package in v1. The ownership boundary must be documented before implementation.

### 5. The registry contract is underspecified

The JSON schema lacks a version, required field types, sorting rules, path normalization, duplicate ID behavior, null handling, and canonical serialization rules. The Markdown "bounded hot-window" also appears time-dependent, which conflicts with deterministic and pure generation.

The JSON output should be complete, versioned, and canonical. JSON itself defines objects as unordered collections, so ordinary valid JSON does not promise stable property order. RFC 8785 separately defines canonical JSON using deterministic property sorting and a fixed representation. The project does not need full RFC 8785 compliance, but it does need an equally explicit local serialization contract. The Markdown should be a deterministic projection of that JSON. Any window should be count-based with an exact tie-break rule, or applied by the reader at display time. Generation must not depend on the current date, file modification time, locale, timezone, terminal width, hash iteration order, or repository absolute path. Reproducible Builds documentation identifies timestamps and locale-sensitive sorting and formatting as common sources of non-reproducibility. See [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259), [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785), [Reproducible Builds on timestamps](https://reproducible-builds.org/docs/timestamps/), and [Reproducible Builds on locales](https://reproducible-builds.org/docs/locales/).

## Answers to the specific questions

### 1. Native enums versus one unified status enum

Keeping native enums is the right call. Plans, research documents, prompts, communications, and specs have different lifecycle semantics. A plan can be approved but unexecuted; research can become a standing reference without being "implemented"; a communication can be sent; a prompt can be consumed. A unified enum would either become a large union of irrelevant values or erase distinctions that owning tools need to enforce transitions and disposition.

What breaks with a unified enum:

- Existing commands, indexes, tests, and user habits would need migration.
- Values would acquire tree-dependent meanings despite supposedly being universal.
- Terminal success, archival disposition, readiness, and active execution would be forced onto one axis.
- New tree-specific states would require changing a global contract.
- Citation-preserving migration would become riskier if status and directory disposition are coupled.

What can break with native enums plus mapping:

- A newly added native status can be omitted from the mapping.
- Two states that need different cross-tree treatment may be collapsed.
- Cross-tree reports can appear consistent while hiding meaningful native distinctions.
- Mapping behavior can change without source artifacts changing, causing registry churn after an upgrade.

Those risks are manageable if the mapping is explicit, exhaustive, versioned in code, and tested once per native value. Unknown `(tree, status)` pairs must be contract errors, as the spec already proposes.

The proposed four classes should change. `needs-attention` and `in-flight` are action states; `done` and `parked` are disposition states. The missing state is `blocked`. A complete mapping should be normative in the spec, not left as OQ1. At minimum:

| Tree | Native status | Recommended class | Comment |
| --- | --- | --- | --- |
| plans | draft | ready | Authoring or clarification remains. |
| plans | to-review | ready | A review action is available. |
| plans | reviewed | ready | Approval or revision is available. |
| plans | approved | ready | Approval means ready, not proven active. |
| plans | auto-approved | ready | Same reasoning as approved. |
| plans | executed | done | Terminal success. |
| plans | superseded | parked | Replaced by another artifact. |
| plans | not-executed | parked | Intentionally terminal without execution. |
| plans | reusable | done | Standing reference, unless the native contract says it is active work. |
| research | intake | ready | Triage or research action remains. |
| research | active | active | Explicitly in progress. |
| research | reference | done | Standing completed reference. |
| research | archive | parked | Deliberately inactive. |
| specs | draft | ready | Authoring or review remains. |
| specs | reviewed | ready | Approval or revision remains. |
| specs | approved | ready | Implementation is available but not necessarily started. |
| specs | implemented | done | Terminal success. |
| specs | superseded | parked | Replaced. |
| specs | deferred | blocked | Requires a valid gate. |

Do not finalize prompt and communication mappings until their exact native enums and ownership rules are listed. "Covering every native status" is untestable without that table.

If the project needs an `active` plan or spec state, add it to that native lifecycle and define its legal transitions. Do not infer activity from a history note.

### 2. One roll-up registry versus per-tree registries

Use one repository-level registry, not per-tree attention registries plus a roll-up. Per-tree tools may retain their existing indexes, but the attention system should scan authoritative artifacts and produce one cross-tree snapshot.

This choice best serves both named goals:

- `/whatnext` gets one cheap machine read.
- CI performs one recomputation and comparison.
- Cross-tree ordering, duplicate IDs, mapping coverage, and schema versioning have one authority.
- There is no second layer of drift between per-tree attention files and the roll-up.

Within the pair, make `.agents/ATTENTION.json` the canonical generated data and `.agents/ATTENTION.md` a deterministic rendering of the same in-memory records. Neither file is authoritative over source artifacts. This is analogous to a materialized view: PostgreSQL documents that the stored view result is refreshed from its defining query and can be stale between refreshes. The analogy supports treating artifacts as the source and the registry as a refreshable projection, although PostgreSQL is not proposed as a project dependency. `--check` must rescan sources and compare the expected bytes of both files. See [PostgreSQL materialized views](https://www.postgresql.org/docs/current/rules-materializedviews.html).

Do not have the roll-up consume existing per-tree index Markdown unless those indexes expose a documented machine schema. Otherwise, one derived artifact would depend on another derived artifact and could inherit stale or lossy state.

### 3. Write verbs and tool-owned trees

Use delegation through an internal owner API. The cleanest contract is:

- The scanner owns normalization and reporting.
- Each tree module owns legal native values, transition validation, source editing, disposition moves, history format, and tree-specific index refresh.
- `aw attention set` is only a router. It resolves the tree, obtains that tree's adapter, calls `set_status`, and then refreshes the attention registry.
- `aw attention note` similarly calls the owner's `append_history` adapter.
- Unsupported trees are read-only through this command.

Avoid subprocess delegation because it complicates error handling, output composition, testing, and Windows portability. Avoid uniform direct writes because plans can have directory-as-disposition and other invariants that a generic front-matter editor cannot safely preserve.

Also consider whether the convenience router is worth shipping in v1. `aw plans ...`, `aw research ...`, and a future `aw specs ...` are clearer ownership surfaces. A smaller first release can omit attention writes entirely and add the router only after all included tree adapters exist.

### 4. Gate representation

Use a required, single-line field with a small typed-reference grammar, plus an optional human summary:

```text
Status: deferred
Gate: decision:D14 | Architecture group must choose the registry schema
```

Grammar:

```text
Gate := <kind>:<reference> [ " | " <summary> ]
kind := artifact | decision | todo | issue | date | external
```

Examples:

```text
Gate: artifact:.agents/docs/specs/example.md#requirement-7 | Requirement 7 must be approved
Gate: todo:D23 | Repository migration must finish
Gate: issue:https://github.com/fariello/agent-workflows/issues/123 | Waiting for upstream decision
Gate: date:2026-09-01 | Revisit after the pilot
Gate: external:security-review | Security review has not completed
```

Parse only the first colon and the first exact ` | ` delimiter. Forbid newlines and the delimiter inside the summary. Validate known kinds and kind-specific references where practical. Store the parsed gate in JSON as:

```json
{
  "kind": "decision",
  "ref": "D14",
  "summary": "Architecture group must choose the registry schema"
}
```

The `deferred` status itself means the gate is currently unresolved. When the gate clears, the owner command must transition the artifact away from `deferred` and preserve the former gate only in history. Do not add a separate mutable `Gate-status` unless there is a demonstrated need, because it creates two fields that can contradict each other.

For strict path stability, artifact references must use repository-relative POSIX paths and an optional Markdown anchor. A gate should identify a condition that can be evaluated by a human or tool, not only say "waiting" or "blocked." If the contract later adds a timestamp, use an RFC 3339 UTC value with `Z`; RFC 3339 defines an unambiguous Internet timestamp profile of ISO 8601. See [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339).

### 5. Scope and pitfalls of `--check`

The proposed scope is broadly correct, but it needs sharper boundaries. `--check` should fail for:

- Expected JSON bytes differ from committed JSON bytes.
- Expected Markdown bytes differ from committed Markdown bytes.
- Either registry file is missing.
- A scanned artifact is missing a required status or has an unknown status.
- A deferred artifact is missing or has an invalid gate.
- A required history section is absent or malformed.
- A duplicate artifact ID or duplicate normalized path exists.
- A tree-specific source invariant needed for mapping is violated, such as terminal status disagreeing with disposition directory.

It should not fail merely because an unrelated artifact body was hand-edited if that edit does not change registry data. Acceptance criterion A2 is too broad on this point.

Define the following determinism rules:

- Repository-relative POSIX paths only.
- Lexicographic ordering by normalized path, with a stated secondary key if needed.
- UTF-8 input and output, LF line endings, and exactly one trailing newline.
- Canonical JSON serialization with fixed indentation, key order, separator behavior, and `ensure_ascii` behavior.
- No generated timestamps, durations, modification times, current-date windows, absolute paths, locale-dependent sorting, or environment-dependent values.
- Explicit symlink policy and deterministic handling of unreadable files.
- Stable Markdown escaping for pipes, newlines, and link-sensitive characters.
- Stable behavior when an artifact has no history entry.

`--agent` also needs a schema. Define record types and fixed columns rather than merely saying tab-separated. Escape tabs, newlines, and backslashes or reject values containing them. A header or schema version record would reduce accidental parser breakage.

### 6. Silent divergence and prevention by construction

Potential divergence paths include:

- Direct source edits without regeneration.
- A write command succeeds on the source file but fails during registry refresh.
- One registry projection is refreshed but the other is not.
- A native enum changes without updating the mapping.
- Scanner discovery excludes a new tree, nested path, filename form, or disposition directory.
- Duplicate IDs cause one record to overwrite another in an in-memory dictionary.
- The Markdown renderer truncates records that remain in JSON.
- History parsing silently accepts malformed dates or picks the wrong "last" line.
- Mapping logic reads stale per-tree indexes rather than source files.
- A tool-owned write changes status but omits its tree index or history update.
- An installer upgrade changes mapping semantics while an old committed registry remains.

Prevent these by construction:

- Treat source artifacts as the sole authority and registries as disposable projections.
- Build records in one scan and render both outputs from that same immutable record collection.
- Reject unknown trees, statuses, duplicate IDs, invalid gates, and malformed required metadata before writing either registry.
- Compute all expected output bytes before replacing either destination.
- Never truncate JSON. If Markdown uses a count limit, include deterministic overflow counts and make full output available through JSON.
- Require exhaustive mapping tests generated from each owner's declared enum.
- Have owner commands invoke a shared post-mutation attention refresh hook, but retain CI and pre-commit `--check` as the backstop.
- Include `schema_version` and `mapping_version` in JSON so changes are explicit.
- Make `aw attention index` idempotent and safe to rerun after any partial failure.
- Test interrupted or failed writes by injecting failures after each replacement boundary.

There is no honest way to guarantee the committed registry "stays true by construction" when users can edit files directly. The enforceable claim is that owner commands refresh it automatically and CI detects every registry-relevant direct edit.

### 7. Phasing

The intended first slice is mostly right, but the written phases contradict the goals and acceptance criteria. G4 marks the full write verbs as Must, while G7 and Section 13 defer them. A3 and A7 require write-verb behavior even though Phase 1 does not include it. Phase 2 also defers CI wiring even though the value of a committed registry depends on a drift gate from the first merge.

Recommended phases:

#### Phase 0: Contract and fixtures

- Inventory every included tree's exact enum, source field, disposition rules, ID rules, and history format.
- Finalize the class vocabulary and complete normative mapping table.
- Define the gate grammar, JSON schema, Markdown rendering, `--agent` schema, and deterministic serialization.
- Create fixture repositories covering every native state and contract violation.

#### Phase 1: Read-only vertical slice

- Normalize specs in the same change or immediately preceding change.
- Implement scanner, canonical record model, JSON and Markdown renderers, `index`, and `index --check`.
- Include plans, research, and specs first. Include prompts and communications only after their contracts are inventoried.
- Wire CI drift checking now, not in Phase 2.
- Rewire `/whatnext` to consume JSON, while retaining git and TODO sources for information outside the registry's scope.

#### Phase 2: Owner adapters and write routing

- Add or expose owner mutation APIs.
- Add spec mutation ownership.
- Implement `aw attention set` and `note` only as routers.
- Add transition, partial-failure, and recovery tests.

#### Phase 3: Scope expansion

- Decide whether roadmaps and walkthroughs represent actionable state. Do not assign artificial statuses merely to make every directory appear in the registry.
- Add only those trees with a real lifecycle and owner.

CI must accompany the first committed generated registry. Without it, staleness is the normal failure mode.

### 8. A materially simpler alternative

Yes. The smallest design that achieves the operational goal is:

- Standardize status and gate metadata for specs.
- Implement one read-only scanner.
- Commit only `.agents/ATTENTION.json` as the canonical snapshot.
- Provide `aw attention index`, `aw attention index --check`, and `aw attention show`.
- Have `show` render the human Markdown board to stdout from JSON, instead of committing `.agents/ATTENTION.md`.
- Have `/whatnext` read JSON.
- Keep all writes in existing owner commands; add a small specs command if needed.

This removes one generated file, the risk of two projections drifting, generic write verbs, and cross-owner transition logic. It still removes repeated model discovery, exposes deterministic CI drift, and makes deferred spec work visible.

If a committed human board is considered important for repository browsing, keep both files but retain the read-only first release. The write verbs are not necessary to prove the registry architecture and should not block it.

### 9. Naming and CLI ergonomics

`aw attention` is a good top-level name because `aw status` already has a different established meaning. The current verb behavior is unclear, however: Section 8.1 calls the command "READ/regenerate," although reading and mutating generated files are different operations.

Match the existing index idiom. Python 3.9's standard `argparse` documentation explicitly supports subcommands for programs that perform several functions with different argument sets, so this structure remains compatible with the project's standard-library-only constraint. See [Python 3.9 `argparse` subcommands](https://docs.python.org/3.9/library/argparse.html#sub-commands).

```text
aw attention index
aw attention index --check
aw attention show
aw attention show --class ready --class active
aw attention show --format json
aw attention show --format agent
aw attention set PATH --status implemented
aw attention note PATH --message "Implemented by change X"
```

Recommendations:

- Use an explicit `index` or `refresh` verb for writes to registry files.
- Reserve bare `aw attention` for help or a read-only summary, not implicit file mutation.
- Prefer named options for status and note text. They give clearer errors and allow future options without positional ambiguity.
- Define path resolution from repository root and reject paths outside `.agents/`.
- Define whether IDs can be accepted in place of paths. If so, reject ambiguous IDs.
- Keep `--agent` as a formatting option on a read-only command, or replace it with `--format agent` for consistency.
- Do not make `aw ipd` another path to the same mutations unless its ownership relationship to `aw plans` is documented. One native operation should have one implementation.
- When a routed write is unsupported, return a stable nonzero code and the exact owner command to use.

### 10. Requirements and acceptance criteria needing correction

#### Ambiguous, contradictory, or wrong requirements

- G1 and F1 are incomplete until the full mapping table is normative.
- G2 says trees that lack status must be standardized, then limits v1 to specs. State the full intended set or scope G2 explicitly to v1.
- G4 is Must, but G7 and Phase 1 defer full writes. Split requirements by phase.
- G4 and F5 incorrectly imply atomicity across source, history, and registry files.
- G8's "never break existing citation paths" is absolute and lacks a defined citation model. Require unchanged repository-relative paths for the Phase 1 migration and test those exact paths.
- F4 does not define the tab-separated schema or escaping.
- F5 leaves delegation versus refusal unresolved and cannot yield one expected implementation.
- F7 says specs require history but does not define the syntax, date format, ordering, actor field, or behavior for migrated history.
- N5 repeats F2 without adding measurable criteria.
- N6 is a documentation/style constraint, not a runtime non-functional requirement unless a lint rule and scope are defined.

#### Untestable, brittle, or incorrect acceptance criteria

- A1 hardcodes repository counts. Use fixture names and expected records, or state that these are migration assertions for one pinned repository revision.
- A2 says any hand edit causes drift. An edit to unindexed body text should not change the registry. Replace it with registry-relevant source edits and direct registry edits.
- A3 belongs to Phase 2 under the proposed phasing. It also must test partial refresh failure and recovery.
- A4 should include malformed gates, duplicate IDs, malformed history, and path/disposition conflicts if those are part of the contract.
- A5 is necessary but insufficient. Also assert byte-for-byte unchanged outputs from existing per-tree commands on unchanged fixtures.
- A6 cannot reliably prove that a language model "reads only" certain files. Test the workflow's declared input-selection step or an instrumented file-access boundary. It also contradicts Section 8.3, which retains fallback and reconciliation sources.
- A7 says write-verb tests are required even in a phase that defers write verbs. Split the suite by phase and enumerate contract fixtures.

## Concrete proposed spec edits

### Section 1

- Replace "scours" with "scans."
- State that source artifacts are authoritative and the registry is a generated snapshot.
- Remove the claim that write verbs make the registry true by construction.
- Clarify whether bare `aw attention` reads, prints, or regenerates.

### Section 2

- Separate deterministic state derivation from model judgment. The registry can identify normalized state, but `/whatnext` may still need judgment to prioritize ready items.
- State which current `/whatnext` inputs remain necessary: git state and TODO entries are not derivable from artifact status.

### Section 3

- Change G1 to name the final class enum and reference a normative complete mapping table.
- Scope G2 to specs in Phase 1.
- Split G3 into index generation, checking, and read-only display requirements.
- Move G4 to Phase 2 or bring write adapters into Phase 1. Do not mark deferred functionality as a Phase 1 Must.
- Rewrite G8 as a measurable path-preservation requirement for migrated files.

### Section 4

- Add that source artifacts, not registry files, remain authoritative.
- Add that the registry does not infer active execution, gate resolution, priority, or recency from prose or file metadata.

### Section 5

- Change the human scenario to the selected CLI verbs.
- Add recovery behavior after a successful source mutation and failed registry refresh.

### Section 6

- Replace the four classes with `ready`, `active`, `blocked`, `done`, and `parked`, or explain a separate machine-readable blocked dimension.
- Add the complete per-tree mapping table.
- Map `approved` and `auto-approved` plans to `ready` unless the plan lifecycle gains an explicit active state.
- Map `deferred` to `blocked` and require a gate.
- Define `canonical` rather than leaving it as an example or open question.
- State how mapping changes are versioned.

### Section 7

- Specify exact metadata syntax, case, encoding, and duplicate-key handling.
- Add the typed `Gate:` grammar.
- Define the history line grammar, preferably ISO 8601 date in UTC, actor, operation, old state, new state, and escaped note text.
- Define whether history dates are dates or timestamps. The registry field name must match.
- Define legal spec transitions, including leaving `deferred` after gate resolution.
- Do not equate `canonical` and `implemented` unless the project establishes that they are semantically identical.

### Section 8.1

- Rename regeneration to `aw attention index` and checking to `aw attention index --check`.
- Define a versioned JSON schema and canonical serialization.
- Render Markdown from the same in-memory records as JSON.
- Remove time-based hot windows. Prefer complete output or a deterministic count limit.
- Define scanner roots, exclusions, symlink policy, duplicate handling, and path normalization.
- Define `--agent` record types, columns, versioning, and escaping.
- Specify that contract errors prevent registry replacement.

### Section 8.2

- Resolve OQ7: all tool-owned writes go through in-process owner adapters.
- State that source replacement is atomic per file, while registry refresh is a recoverable subsequent operation.
- Define exit codes and user-facing behavior for validation failure, unsupported owner, source-write failure, and refresh failure.
- Define whether `note` is permitted on terminal or archived artifacts.
- Define whether tree-specific indexes refresh before or after the attention registry.

### Section 8.3

- Define the exact fallback rules. Missing or invalid registry should produce a visible warning and a deterministic remediation command.
- Keep git and TODO inputs because the registry explicitly does not replace them.
- Specify that JSON `schema_version` incompatibility fails closed rather than being silently ignored.

### Section 9

- Split Phase 1 and Phase 2 requirements.
- Replace the atomic multi-file claim.
- Add duplicate ID, malformed history, path/disposition consistency, missing registry, and schema-version checks.
- Add deterministic serialization and error-code requirements.
- Add exhaustive mapping coverage against owner-declared enums.

### Section 10

- Replace repository-count assertions with named fixtures or pin them to a migration revision.
- Narrow A2 to registry-relevant edits.
- Move write criteria to Phase 2.
- Make A6 test an observable selection interface, not model reading behavior.
- Add idempotence, canonical byte output, partial-failure recovery, duplicate detection, enum expansion, symlink policy, Windows path normalization, and Python 3.9 tests.

### Section 11

- Identify the actual owner modules and adapter protocol.
- Define installer upgrade behavior for existing repositories with missing or stale registries.
- State whether `.agents/ATTENTION.json` and `.agents/ATTENTION.md` are installed empty, generated during install, or omitted until first indexing.

### Section 12

- Close OQ1, OQ3, OQ4, OQ5, OQ7, and OQ9 before implementation. They affect core data and ownership contracts.
- Exclude walkthroughs by default unless they contain actionable lifecycle state. "Always done" is misleading and adds noise.
- Treat roadmaps similarly. A document's existence does not imply it belongs in an attention registry.

### Section 13

- Add a Phase 0 contract and fixture step.
- Move CI wiring into Phase 1.
- Keep write routing in Phase 2 unless owner adapters already exist.
- Make expansion to roadmaps and walkthroughs conditional on demonstrated lifecycle needs.

## Smaller nits

- Use "attention class" in prose, not uppercase `ATTENTION-CLASS`, unless it is a literal schema name.
- Avoid using "status" for both native lifecycle state and the derived attention class. Use `native_status` and `attention_class` consistently.
- `last_history_date` is ambiguous if lines contain timestamps. Prefer `last_history_at` for a UTC timestamp or `last_history_on` for a date.
- Define whether an artifact without an ID is invalid or receives a deterministic derived ID. Silent derivation can destabilize references after a rename.
- Do not use display ordering as priority. If prioritization is later required, add an explicit owner-defined field rather than inferring it from class or recency.
- Markdown overflow counts should link or point to a command that shows the complete set.
- Error messages should name the repository-relative path, rule identifier, and invalid value without embedding machine-specific absolute paths.
- The registry should record the native status exactly as normalized by the owner, not preserve arbitrary source casing.
- The term "canonical reference spec" needs a definition. Canonicality, completion, and implementation are separate properties unless the project explicitly makes them equivalent.
- Consider naming the generated command `index` to align with `aw plans index` and `aw research index`; consistency is more valuable than introducing `regenerate` or `refresh` as a third convention.

## References and evidentiary basis

### Standards and official technical documentation

1. [Python 3.9 documentation for `os.replace`](https://docs.python.org/3.9/library/os.html#os.replace). Supports the statement that a successful replacement of one source and one destination is atomic, while replacement can fail across filesystems. It does not promise a transaction spanning multiple replacement calls.
2. [SQLite temporary files and super-journals](https://sqlite.org/tempfiles.html#super_journal_files). Supports the inference that cross-file atomicity requires an explicit coordination protocol. SQLite uses a super-journal for transactions across multiple attached database files and explains that, without it, changes are atomic per database file rather than across all files.
3. [RFC 8259, JSON Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259). Defines a JSON object as an unordered collection. This supports the conclusion that deterministic byte output requires rules beyond ordinary JSON validity.
4. [RFC 8785, JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785). Defines an invariant JSON representation using deterministic property sorting, constrained serialization, and UTF-8. The review cites it as precedent for specifying canonical bytes, not as a requirement to implement full JCS.
5. [Reproducible Builds documentation on timestamps](https://reproducible-builds.org/docs/timestamps/). Documents current timestamps as a major source of irreproducible generated output and recommends avoiding or normalizing them.
6. [Reproducible Builds documentation on locales](https://reproducible-builds.org/docs/locales/). Documents that locale can affect time formatting, collation order, and default encoding. This supports fixing sorting, timezone, and encoding rules for deterministic output.
7. [PostgreSQL documentation on materialized views](https://www.postgresql.org/docs/current/rules-materializedviews.html). Documents persisted derived results that are regenerated through refresh and may not always be current. This is an architectural analogy for treating source artifacts as authoritative and the committed attention registry as a refreshable projection.
8. [RFC 3339, Date and Time on the Internet](https://www.rfc-editor.org/rfc/rfc3339). Defines an unambiguous timestamp profile of ISO 8601 suitable for machine interchange. This supports the recommendation to specify UTC timestamps precisely if history uses timestamps rather than dates.
9. [Python 3.9 documentation for `argparse` subcommands](https://docs.python.org/3.9/library/argparse.html#sub-commands). Confirms that the standard library directly supports distinct command functions such as `index`, `show`, `set`, and `note`.
10. [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core). Defines a JSON-based format for describing and validating JSON document structure. This supports publishing a formal registry schema, although the project could instead enforce an internal schema in Python to preserve its zero-dependency design.

### Project-specific evidence supplied by the specification

The following conclusions are grounded primarily in the specification itself and should be validated against repository code and fixtures before implementation:

- The proposed mapping is not pure because Section 6 conditions `approved` on being "under execution" and changes `deferred` treatment based on gate meaning, while the declared function accepts only tree and native status.
- The phase plan is internally inconsistent because G4 marks write verbs as Must, Section 13 defers them to Phase 2, and A3 and A7 require them without a phase qualifier.
- Write ownership is unresolved because Section 8.2 permits delegation or refusal, F5 retains both choices, and OQ7 remains open.
- A2 is too broad because a body-only source edit need not affect any registry field.
- A6 is not directly testable as written because model file-reading behavior is not an observable product contract unless the workflow exposes or instruments its selected inputs.
- A complete mapping cannot be tested until the exact prompt and communication enums are included in the normative specification.

### Architectural judgments, not externally mandated conclusions

No external standard mandates the five proposed attention classes, the owner-adapter design, one roll-up registry, or the recommended phase order. Those are design judgments based on the stated goals and failure modes:

- Adding `blocked` separates work that can advance now from work that cannot, which is the distinction `/whatnext` needs to choose an action.
- Keeping native enums avoids erasing tree-specific lifecycle semantics.
- One roll-up avoids a second derived layer and directly meets the single-read requirement.
- Owner adapters keep validation and transition rules in one implementation.
- A read-only Phase 1 reduces scope while still testing the central registry hypothesis.

These recommendations should therefore be accepted or rejected through project design review, not treated as requirements imposed by the cited standards.

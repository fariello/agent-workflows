# Specification: Physical AW hierarchy, placement, and loss-resistant migration

- Status: reviewed
- Canonical: true
- Date: 2026-08-10
- Supersedes: `.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`
- Implementation Set: `.agents/plans/pending/20260810-awphysical-00-rma3j4-physical-aw-hierarchy-and-migration-orchestrator.md` and Orders 01 through 12

One physical `.aw/` contract separates replaceable framework files, user policy, operational state, and project records while allowing each class to live in the target, an AW home, or a private companion repository.

## 1. Problem and motivation

The superseded layout specification named four logical roots but allowed tracked system content to remain under `.agents/` and allowed a target to have no physical `.aw/` namespace. That design did not deliver the filesystem separation the maintainer intended. It also combined portable and machine-local configuration, durable and disposable state, and source-checkout material in ways that made tracking, privacy, migration, and ownership harder to reason about.

AW needs one physical shape that remains recognizable wherever it is placed, including in the agent-workflows source repository. Users must be able to choose the repository and Git policy for each durable class without allowing local paths, runtime scratch, or locks into history. Existing projects must migrate without losing tracked, untracked, ignored, symlinked, or external material and without silently exposing private records.

## 2. Goals

1. Make `.aw/system/`, `.aw/config/`, `.aw/state/`, and `.aw/records/` the canonical physical namespace for every AW project bundle.
2. Separate portable `config/project.json` from machine-local `config/local.json`.
3. Separate durable operational facts in `state/durable/` from disposable and secret-prone runtime material in `state/runtime/`.
4. Let the wizard place each class in the target, AW home, or a private companion, with an explicit Git policy and exact preview.
5. Protect the agent-workflows source checkout while making it dogfood the same physical namespace.
6. Migrate all legacy material with a frozen inventory, copy-verify-switch-retain transaction, independent postcheck, resume, and rollback.
7. Preserve the operational-action and attention contracts from the superseded specification.

## 3. Non-goals

- AW does not create, select, authenticate to, push to, or delete a Git remote without a separate explicit user action.
- AW does not promise that a repository or remote is private. It reports observable facts and user acknowledgements.
- AW does not store credentials or secrets in portable policy, durable state, records metadata, or migration evidence.
- Migration cutover never deletes legacy material. Cleanup is a later, separately confirmed operation.
- Host-required discovery files are not forced beneath `.aw/`; they remain thin generated adapters only.
- This specification does not authorize implementation, migration, push, tag, release, or cleanup.

## 4. Normative physical contract

The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

Every placement container uses this physical tail:

```text
<container>/.aw/
├── system/
├── config/
│   ├── project.json
│   └── local.json
├── state/
│   ├── durable/
│   └── runtime/
└── records/
```

`<container>` may be the target repository, `AW_HOME/projects/<project-id>`, or an attached companion directory. A class may resolve to a different container, but its physical tail is fixed. For example, external records resolve to `<companion>/.aw/records`, not an unrelated ad hoc records directory. A clean-target policy can therefore leave no target `.aw/` while still using the canonical physical shape outside the target.

The resolver returns each physical class separately: `system`, `config_project`, `config_local`, `state_durable`, `state_runtime`, and `records`. The four short root names remain human-facing group names only; they are not permission to collapse the six physical classes.

### 4.1 Exact ownership and filenames

| Class | Required contents | Writer | Git rule |
|---|---|---|---|
| `system/` | `VERSION`, `manifest.json`, `workflows/`, `templates/`, packaged skills and deterministic helpers | AW CLI in installed projects; developers in a verified source checkout | Tracked only when policy says `target-tracked` or role is `source-checkout`; otherwise external and untracked from target |
| `config/project.json` | schema version, preset, portable placements, tracking intent, enabled hosts, non-secret consent | Human plus schema-aware AW commands | MAY be tracked in its selected Git owner; MUST contain no absolute machine path or secret |
| `config/local.json` | absolute bindings, path aliases, local companion attachment, runtime overrides, host-local facts | Human plus schema-aware AW commands | MUST NOT be tracked in any repository |
| `state/durable/install.json` | current successful install snapshot | AW CLI | MAY be tracked according to policy |
| `state/durable/history/installs.jsonl` | append-only attempted/completed install history | AW CLI | MAY be tracked according to policy |
| `state/durable/actions/{open,completed,dismissed,superseded}/` | AW operational actions such as `setup-repo-v2.md` | `aw todo` owner commands and documented hooks | MAY be tracked according to policy |
| `state/durable/migrations/` | redacted migration receipts, retained-source map, recovery instructions | migration owner commands | MAY be tracked only after sanitization |
| `state/runtime/transactions/` | active journals and staging metadata | AW CLI | MUST NOT be tracked |
| `state/runtime/{locks,staging,backups,cache,tmp}/` | locks, candidates, rollback scratch, caches, transient output | AW CLI | MUST NOT be tracked |
| `records/` | `plans/`, `prompts/`, `docs/specs/`, `research/`, `assessments/`, `incidents/`, `comms/`, `runs/`, indexes and evidence | Producing workflows and humans under lifecycle rules | Track only in the explicitly selected Git owner |

Unknown files in an AW-owned system or runtime directory are never silently adopted or deleted. Runtime content is disposable only after ownership and transaction checks say it is safe. Records are never installer-owned.

### 4.2 Host exceptions

Files at `AGENTS.md`, `.agents/skills/`, `.claude/`, `.opencode/`, or another host-mandated discovery path are permitted only when the host requires that exact path. Each exception MUST be generated, manifest-owned, drift-detected, removable conservatively, and contain a pointer or thin adapter rather than a second canonical workflow body or records tree.

## 5. Placement and Git policy

The closed initial placement vocabulary is:

- `target-tracked`: the class is under `<target>/.aw/` and intentionally tracked by the target Git repository.
- `target-ignored`: the class is under `<target>/.aw/` and covered by a verified ignore rule. Only `config_local` and `state_runtime` may use it by preset.
- `home-untracked`: the class is under `<AW_HOME>/projects/<project-id>/.aw/` and is not tracked by the target.
- `companion-tracked`: the class is under `<companion>/.aw/` and intentionally tracked by the companion Git repository.
- `companion-untracked`: the class is under `<companion>/.aw/` but is excluded from that repository's index.
- `source-checkout`: system resolves to the verified developer-owned source at `<source>/.aw/system/`; installer mutation is prohibited.
- `custom`: an explicit path that passes all containment, alias, Git-owner, portability, and tracking validation and is normalized to the appropriate `.aw/<class>` tail.

Every resolved class records one physical path, one owner, one Git owner or `none`, one tracking policy, one portability classification, and one provenance source. `config_local` and `state_runtime` MUST be untracked in every preset and custom layout. A custom policy MUST NOT put records or mutable state inside system, put one class inside another, alias target and companion, cross a symlink outside an approved root, or claim clean-target while creating any AW-owned target baseline delta.

## 6. Presets

| Preset | System | Project config | Local config | Durable state | Runtime state | Records | Intended use |
|---|---|---|---|---|---|---|---|
| `private-target` | target tracked | target tracked | target ignored | target tracked | target ignored | target tracked | Permanently private repository; maximum portability and collaboration |
| `public-private-companion` | target tracked | companion tracked | home untracked | companion tracked | home untracked | companion tracked | Public product repository with candid durable AW material in a separately access-controlled repository |
| `clean-target` | home untracked | home untracked | home untracked | home untracked or companion tracked | home untracked | home untracked or companion tracked | Upstream contribution or zero AW-owned target delta |
| `local-only` | home untracked | home untracked | home untracked | home untracked | home untracked | home untracked | Local use with honest `unversioned` durability until the user adds backup |

The wizard MAY offer a companion variant of clean-target and constrained custom placement. It MUST display all six physical paths and their Git owners before any write. It MUST label external-but-unversioned storage as not durable. It MUST never infer target ownership or remote privacy.

## 7. Configuration and precedence

Portable project policy is versioned JSON at the resolved `config/project.json`; machine-local binding is versioned JSON at the resolved untracked `config/local.json`. The shipped or legacy `.aw/config/config.json` shape is migration input only. Its portable fields move to `project.json`; absolute paths, aliases, local attachment, and runtime overrides move to `local.json`; conflicting or unknown fields block automatic conversion and remain preserved in the migration inventory.

Resolution uses exactly the existing six precedence levels, highest first:

1. explicit invocation flags;
2. machine-local binding;
3. portable project policy;
4. named global profile;
5. global defaults;
6. built-in defaults.

The resolver MUST be pure and side-effect free. It reports configured versus inherited/default state and provenance for every field. Same-level conflicts, malformed or future schemas, ambiguous project identity, unavailable required roots, symlink escape, unsafe containment, or uncertain Git ownership fail closed before writes.

## 8. Installer and wizard requirements

First interactive install runs the preset-first accessible wizard unless a complete explicit policy exists. A closed stdin or incomplete noninteractive first install fails before writes and prints the missing choices. Update shows the current policy, proposed version, all resolved paths and Git owners, warnings, and `keep current policy and update` as the default; a placement change invokes migration planning rather than silently moving files.

The final review uses words in addition to color and honors `NO_COLOR`, `FORCE_COLOR`, `--no-color`, TTY detection, redirected output, and `TERM=dumb`. Dry-run and cancellation leave filesystem, registry, and Git indexes unchanged.

A fresh install creates the current `setup-repo` action under `state/durable/actions/open/`. Updates append install history and create a new action generation only for a materially new persistent obligation. `aw attention` remains the only cross-tree projection and reads actions through the resolver.

## 9. Source checkout and packaging

Ordinary installed projects materialize the packaged manifest beneath their resolved `.aw/system/`. The package, wheel, sdist, installer, version lookup, adapters, and tests consume one canonical system source.

The agent-workflows source repository uses role `source-checkout`. Its developer-owned canonical workflows, templates, and helper sources live under its own `.aw/system/`. Source role requires positive repository identity evidence, including expected package metadata and Git common-dir checks; path, repository name, origin URL, or copied marker files alone are insufficient. Ambiguous or spoofed evidence fails closed. In source role, `aw install` MUST NOT overwrite, remove, or create a duplicate installed system tree. Build and generated-file tooling reads the source provider explicitly.

## 10. Companion identity, privacy, and durability

A portable companion identity records stable project ID, schema version, and selected durable classes without a machine-local absolute path. The local attachment records canonical path and Git common-dir. Origin URL is matching evidence only, never identity or proof of privacy.

Attachment rejects nested or overlapping Git repositories, unsafe symlinks, case aliases, conflicting identities, and target leakage before writes. AW reports `unversioned`, `local-git`, `unacknowledged-remote`, `acknowledged-durable`, `repository-managed`, `unreachable`, or `unknown` from observable facts. This cutover redefines the durability enum: historical `durable-private` input normalizes to `acknowledged-durable` only through the legacy normalization table, is not a current enum member, and current serialization never emits the historical value; `unreachable` is added as a current state. A configured remote is `unacknowledged-remote`; an acknowledged and reachable arrangement is `acknowledged-durable`; an acknowledged remote that cannot be reached is `unreachable`; inconclusive inspection is `unknown`. It does not create or mutate remotes, authenticate, commit, push, or delete companion content. Target and companion deltas, indexes, and commit instructions remain separate. Order 02 owns the enum, legacy normalization table, and schema. Order 05 consumes it and owns observation/classification. Their shared-schema edit is subject to the Section 14 coordination gate.

## 11. Migration and compatibility

### 11.1 Complete pre-mutation inventory

Before any mutation, AW freezes a versioned inventory of all declared legacy and partial-layout roots, including `.agents/`, `workflow-artifacts/`, existing `.aw/`, installer backups, host adapters, external configured roots, tracked, untracked, ignored, empty, symlinked, modified-managed, and unknown entries. Each item has a stable ID, type, size, mode, hash where applicable, Git classification, and source owner. External roots require explicit operator `--root` declarations. Unknown, ambiguous, conflicting, inaccessible, or unaccounted items block apply.

The approved migration map assigns every inventory item exactly one disposition: copy, explicit identical-content deduplication, retain, or approved exclusion with reason. It records the destination class, relative path, Git owner, and policy digest. A missing or duplicate disposition is an error.

### 11.2 Copy-verify-switch-retain transaction

Migration MUST:

1. acquire one project writer lock and reject unmerged/conflicted Git state;
2. revalidate inventory, map, policy, identities, permissions, and space;
3. copy into transaction-specific staging without following unsafe links or overwriting collisions;
4. verify every destination byte, mode, and safe-link disposition;
5. switch policy and registry authority once, last, with a durable receipt;
6. disable every legacy writer before and after the switch;
7. retain all legacy sources and the old-to-new map during cutover;
8. expose idempotent status, resume, and rollback for every journaled phase;
9. generate separate target, companion, and source Git plans without committing or pushing;
10. require the independent deterministic compare and postcheck before success.

An independent postcheck MUST re-derive expected content from the frozen inventory and the destination filesystem and Git evidence, not from the migration transaction's in-memory map or success state. Its rule results, paths, and content digests MUST be emitted in deterministic sorted order.

Failure before switch leaves legacy authoritative. Failure after switch has an explicit new authority and rollback path. Migration MUST NOT dual-write. Cleanup is a separate preview-first command after the retention gate; it re-inventories and refuses foreign or changed content. No migration or uninstall deletes an external repository or remote.

### 11.3 Compatibility and release boundary

This is a major-version physical cutover. During one documented compatibility window, read-only discovery MAY find legacy records and report `migration-required`; new writes have exactly one resolver-selected destination. Compatibility readers are closed and tested, emit a deprecation notice, and have a stated removal release. A catalog scenario whose `preset` is `all` MUST pass independently for every applicable built-in preset; one execution under a single preset does not satisfy that scenario. The product MUST NOT claim the physical layout shipped until all 44 scenarios, including every required expansion of each `all` scenario, pass; the source repository has been migrated and independently compared; packaging and clean-checkout gates pass; and the release workflow's bake and human tag/release gates are satisfied.

## 12. Legacy 25-scenario crosswalk

The 44-scenario catalog at `tools/awphysical/migration-scenarios.json` is the controlling physical-layout catalog. The prior 25 scenarios are not silently discarded:

| Old | Disposition in the 44-scenario catalog |
|---:|---|
| 1 recommended home records | Extended by AWP-005 and AWP-007 |
| 2 repository records with publication warning | Superseded by AWP-001 and privacy-negative AWP-027 |
| 3 local companion without remote | Extended by AWP-004 |
| 4 acknowledged private companion remote | Extended by AWP-003 |
| 5 explicit noninteractive policy | Extended by AWP-001, AWP-005, and AWP-008 |
| 6 incomplete noninteractive install fails | Asserted by AWP-043: `first-install-eof-fails-closed` and `no-write-before-complete-choice` |
| 7 same-version no-op checkpoint | Retained as an Order 03 acceptance case paired with AWP-001 |
| 8 update keeping policy | Retained as an Order 03 acceptance case paired with AWP-028 |
| 9 repository-to-home change | Superseded by AWP-002 plus AWP-005 transactional migration |
| 10 skipped-version action reconciliation | Extended by AWP-028 |
| 11 repository move and reattach | Extended by AWP-040 |
| 12 clone/worktree resolution | Extended by AWP-019 and ambiguity cases AWP-020/AWP-022 |
| 13 setup action across status surfaces | Retained as an Order 08/12 acceptance case paired with AWP-001 |
| 14 setup completion | Retained as an Order 08/12 acceptance case paired with AWP-001 |
| 15 dismissal history and no resurrection | Retained as an Order 08/12 acceptance case paired with AWP-028 |
| 16 new action generation supersedes old | Extended by AWP-028 |
| 17 separate product and record commits | Extended by AWP-003 and AWP-027 |
| 18 preserve records before cleanup | Extended by AWP-002, AWP-023, and AWP-033 |
| 19 uninstall preserves external roots | Extended by AWP-032 |
| 20 clean-delta merge-base proof | Extended by AWP-005, AWP-006, and AWP-036 |
| 21 unavailable external root stops writes | Extended by AWP-037 |
| 22 color and terminal modes | Asserted by AWP-044: `color-auto-always-never` and `no-color-and-term-dumb` |
| 23 screen-reader text without color | Asserted by AWP-044: `screen-reader-text-without-color` |
| 24 privacy doctor makes no unverifiable claim | Extended by AWP-003, AWP-004, and AWP-027 |
| 25 optional link absent or broken | Retained as an Order 09 acceptance case paired with AWP-005 |

The top-level `legacy_crosswalk` in the catalog is controlling. Every old ID 1 through 25 MUST name one or more AWP scenarios and one or more behavior-level assertion tokens. A crosswalk row passes only when every named assertion exists in the union of those scenarios' `expected` sets and maps to a named automated test assertion. Parent-ID existence alone is insufficient. `retained` means the behavior remains required even where the physical catalog gives it a parent scenario rather than a separate top-level ID. No old scenario or assertion may disappear from the test or evidence set.

## 13. Acceptance criteria

- All six physical classes resolve to the mandated `.aw/` tails for every preset and valid custom policy.
- No tracked index contains `config/local.json` or any `state/runtime/` entry.
- The wizard's filesystem/Git preview equals the actual dry-run plan and first-install EOF fails closed.
- Source-checkout positive, spoofed, and ambiguous fixtures prove no installer write reaches developer-owned system content.
- Inventory expected-item set equals actual-item set; every map item has one disposition; deterministic output differs only in explicitly isolated run metadata.
- Fault injection at every transaction phase proves byte preservation, single authority, resume, rollback, and no cleanup during cutover.
- Target and companion Git status, index, and merge-base evidence prove private records and machine paths do not enter the public target.
- Every producer resolves its record destination and a forbidden legacy write raises before filesystem mutation.
- The independent compare/postcheck maps every deceptive fixture to a named rule and fails for every planted violation.
- A full mirror-backed source-repository rehearsal and real pre/post digest comparison preserve every artifact tree and Git-history tip/count.
- The 25-to-44 behavior crosswalk, all 44 scenario tests, full unittest suite, spec checks, indexes, sanitizer, package inspection, clean-delta gates, and release bake all pass from a clean checkout.

## 14. Constraints, risks, and open questions

- Runtime remains stdlib-only and supported Python/platform behavior must remain explicit.
- Concurrent exclusion-list and general CLI-help work is outside this Set; shared parser/help files require a coordination gate before edits.
- Absolute paths in local evidence are sensitive and must be sanitized before any tracked commit.
- Cross-repository Git operations cannot be atomic. AW coordinates and reports independent transactions but never claims a global commit.
- Human approval of this specification is the only remaining design gate. Until approved, every `awphysical` child is NO-GO.

## 15. Out of scope and future work

- Remote-provider APIs, automatic backup, encryption, and secret management.
- More placement backends or low-level combinations not justified by a concrete user need.
- Automatic legacy cleanup or history rewriting.
- Changes to repository exclusion semantics or unrelated CLI help.

## Workflow history

- 2026-08-10 /spec (Codex (GPT-5)): drafted the superseding physical-layout specification from the maintainer-approved direction and the 2026-08-10 cross-Set plan review.
- 2026-08-10 to-review (aw specs): physical-layout superseding draft ready for independent review and human approval
- 2026-08-10 note (aw specs): 2026-08-10 independent review (opencode Opus 4.8 /plan-review-long): spec verified coherent and implementable on all 8 prior-blocker axes (physical contract, config.json migration, git-policy invariants, source-checkout, migration loss-prevention, release boundary, to-review + human-approval gate). One PARTIAL: the Section 12 crosswalk maps old #6 (first-install EOF fail-closed) and #22/#23 (color/screen-reader accessibility) to AWP scenarios (AWP-041, AWP-001) whose expected sets do not encode those behaviors, so a scenario==evidence gate can pass while they ship untested; the retained/paired disposition is not machine-verifiable at the behavior level. Minor: durability enum drift (acknowledged-durable/unreachable vs shipped DurabilityState); define postcheck 'independence' and all-preset scenario counting. Handed to GPT-5.6 High for reconciliation with tools/awphysical/migration-scenarios.json + Order 12. Spec kept to-review; human approval remains the sole design gate.
- 2026-08-10 note (aw specs): residual reconciliation: added 44-scenario behavior-level legacy crosswalk, seven-state durability ownership and legacy alias, independent postcheck evidence requirements, safety-critical negative fixtures, source self-migration integrity gates, and LOW traceability/tooling corrections; status remains to-review and human approval remains blocking
- 2026-08-10 reviewed (aw specs): 2026-08-10 reviewed (opencode Opus 4.8 /plan-review-long): final targeted verify of GPT-5.6's 1544-01 closeout confirms all spec-gating findings closed at path:line - S2.1 durability-enum redefinition note (durable-private normalizes via the legacy table, not a current enum member; unreachable added; Order 02/05 ownership + Section 14 gate), S2.2 postcheck-independence definition (re-derive from frozen inventory + destination filesystem/Git, deterministic sorted output), S2.3 all-preset scenario counting (44 scenarios; each all-preset scenario must pass per applicable preset), and the Section 12 crosswalk now binds every expected token to a loadable test method. aw specs check conforms; full suite Ran 825 tests OK (skipped=1); all 13 Set plans lint conforming at review-finalize. No open findings block review. to-review -> reviewed. Human approval remains the sole design gate (agent cannot approve).

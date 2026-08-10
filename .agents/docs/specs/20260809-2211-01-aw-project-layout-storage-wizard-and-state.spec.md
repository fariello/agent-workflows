# Specification: AW project layout, storage, install wizard, and operational state

- Date: 2026-08-09
- Status: implemented
- Canonical: true
- Author: Codex (GPT-5, high reasoning)
- Origin: maintainer design discussion on 2026-08-09
- Extends: D107, D109, D113, D117 through D125
- Related specifications: `20260725-0957-01-external-delivery-and-skills.spec.md`, `20260726-1239-01-clean-delta-and-tracking-modes.spec.md`, `20260802-1904-01-ipd-structure-and-linting.spec.md`, `20260808-0004-01-artifact-organization-plans-adopter.spec.md`, `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`
- Implementation Set: `.agents/plans/pending/20260809-awlayout-00-az9912-aw-project-layout-orchestrator.md` and Orders 01 through 11

This specification defines a coherent project namespace, external-by-default records storage, an interactive and accessible install/update wizard, a user-level `AW_HOME`, repository identity and routing, and a per-project AW operational-action model. It is the normative design source for the implementation Set. It does not change current behavior.

## 1. Problem statement

The current installed layout mixes several ownership and lifecycle concepts across `.agents/workflows/`, `.agents/plans/`, `.agents/prompts/`, `.agents/docs/`, `.agents/comms/`, `workflow-artifacts/`, top-level instruction files, host command directories, and installer backup or manifest locations. The result has four problems:

1. A user cannot identify ownership from the path alone. Installer-owned framework files, user configuration, AW operational metadata, and project records are interleaved.
2. Installing AW visibly adds many files to a target repository, even when the user wants private planning or a clean contribution delta.
3. Durable records are coupled to the target repository's tracking policy. The current local-only `workflow-artifacts/` policy prevents accidental publication but does not itself provide durable version history.
4. AW has no first-class per-project operational action ledger. Installation can recommend `/setup-repo`, but that recommendation does not persist until completed or dismissed. D125's existing attention view is the authoritative `/whatnext` input, but it has no native source for AW operational actions stored outside the tracked `.agents/` tree.

The design must preserve the existing strengths: conservative ownership, no-clobber updates, manifest-based drift detection, explicit consent, filesystem-visible lifecycle, accessible color, local clean-delta, tool-agnostic workflows, and durable cold-start context.

## 2. Goals

The implementation MUST:

- give every logical AW file one of four clear ownership homes: `system`, `config`, `state`, or `records`;
- keep records outside the target repository by recommended default;
- let users make records durable in a private Git repository or another explicit backup arrangement;
- retain an in-repository records option for teams that deliberately want shared project history;
- present a detailed, color-aware, accessible wizard on first install and a concise policy review on update;
- keep noninteractive installation deterministic and fail before writes when required choices are missing;
- make every workflow resolve logical roots through one deterministic context resolver;
- persist per-project AW actions such as `setup-repo` until completed, dismissed, or superseded;
- separate installation history from attention-requiring actions;
- extend D125's read-only attention projection with AW actions as a native source instead of creating another cross-tree status aggregator;
- preserve the D109 distinction between tracked delivery and local clean-delta delivery;
- support `AW_HOME` without requiring `~/.aw` specifically;
- provide safe migration, rollback, uninstall, and privacy verification;
- remain usable by both humans and agents with short logical command identifiers.

## 3. Non-goals

This design does not:

- promise that AW usage is secret or undetectable;
- promise that private Git hosting is intrinsically secure;
- make remote or cloud clean-delta work from workstation-local files;
- infer repository ownership from a Git remote;
- rewrite Git history automatically;
- require a symlink, submodule, nested Git repository, database, or network service;
- turn every installation or update event into a TODO;
- replace the project's ordinary `TODO.md`, issue tracker, or IPD lifecycle with AW operational actions;
- make color carry meaning that is absent from plain text;
- update `README.md` or `ARCHITECTURE.md` before behavior ships.

## 4. Normative terms and logical roots

The terms `MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative.

Every enabled project has four logical roots:

```text
.aw/
├── system/
├── config/
├── state/
└── records/
```

This tree is logical. Depending on delivery and storage choices, some or all roots may resolve outside the target repository and no literal target `.aw/` directory may exist.

### 4.1 `system`

`system` contains AW-installed and AW-updated framework content:

- workflow bodies;
- packaged or rendered skills;
- templates;
- deterministic helper tools;
- framework version;
- ownership manifests and installer transaction data that describe system files;
- source material for thin host adapters.

Humans and agents may read `system`. Only the `aw` CLI may modify it. A workflow MUST NOT write records or operational progress into `system`.

### 4.2 `config`

`config` contains user-controlled policy:

- selected delivery mode;
- selected records backend and durability policy;
- project conventions specific to AW;
- sanitizer and privacy settings;
- enabled hosts;
- explicit defaults or consent decisions.

AW reads and validates `config`. Humans may edit it where the schema permits. Machine-local path bindings MUST remain outside tracked target configuration unless the user explicitly selects a tracked, portable path.

### 4.3 `state`

`state` contains AW operational facts about the relationship between AW and one project:

- current effective install snapshot;
- append-only install/update history;
- open, completed, dismissed, and superseded AW actions;
- migration and rollback transaction state;
- recovery snapshots and effective routing summaries;
- host integration registration and ownership state.

`state` is not a project artifact repository. AW owns its schema and transitions. Humans and agents may inspect it. Mutations occur through deterministic AW commands or explicitly documented workflow hooks.

### 4.4 `records`

`records` contains project work created while using AW:

- plans and IPDs;
- prompts;
- specifications;
- assessments;
- research;
- incident records;
- inter-agent communications when enabled;
- workflow run records and evidence;
- other durable project artifacts created by producing workflows.

`records` does not contain installer actions, install history, or tool-maintenance reminders. Workflows and humans create or modify records under the applicable lifecycle rules. AW indexes and routes them but MUST NOT overwrite user-authored records during install or update.

## 5. Two independent policy axes

The design has two independent policy axes. The wizard presents them separately and the resolver returns both.

### 5.1 Delivery mode

Exactly two delivery modes remain:

- `tracked`: the project deliberately carries the selected AW system content or thin host adapters in tracked repository paths.
- `clean-delta`: the target repository carries no AW-owned tracked or baseline local files; local hosts discover AW through proven user-scope mechanisms.

This preserves D109's coherent delivery modes. The implementation MUST NOT expose low-level combinations that violate a mode's invariants.

### 5.2 Records backend

Records storage is selected independently:

- `home`: records live under the user-selected `AW_HOME` project directory. This is the recommended default.
- `companion`: records live in a separately selected project-specific directory or sibling repository.
- `repository`: records live under the target repository's `.aw/records/` and follow its intentional tracking policy.

`tracked` delivery MAY use `home`, `companion`, or `repository` records. `clean-delta` delivery MUST use `home` or `companion` records and MUST NOT route records into the target.

## 6. Recommended default and durability

### 6.1 Recommended interactive default

On first interactive install, the wizard MUST recommend:

- delivery mode appropriate to the user's stated intent, without attempting to infer repository ownership;
- records backend `home`;
- a project directory under `AW_HOME/projects/<project-id>/records/`;
- no `.aw/records/` directory in the target repository;
- an explicit durability decision before completion.

The default keeps candid records outside the target and avoids accidental publication. The wizard MUST explain that external placement alone does not make records durable.

### 6.2 Durability levels

The records backend has an independently reported durability state:

- `unversioned`: ordinary local files with no AW-observed Git history or acknowledged backup;
- `local-git`: a Git repository exists and records have local history, but no verified remote or acknowledged external backup;
- `durable-private`: the user has configured a private remote or explicitly acknowledged another durable backup mechanism;
- `repository-managed`: the target repository intentionally tracks the records backend;
- `unknown`: AW cannot verify the claim.

AW MUST report what it can observe and MUST NOT claim durability or privacy it cannot verify. AW MAY initialize a local Git repository only with confirmation. AW MUST NOT create, select, or push to a remote without explicit user authorization.

If the user selects external records but finishes without `durable-private`, the install MAY complete, but AW MUST create an open `configure-records-durability` action unless the user explicitly dismisses or acknowledges that risk in the wizard.

### 6.3 Repository records option

The wizard MUST present `repository` records as an intentional collaboration choice, not the recommended privacy default. It must explain:

- records travel with clones and are easy for collaborators to discover;
- Git history is straightforward;
- candid prompts, assessments, and plans may become public or enter pull requests;
- ignore rules do not remove already tracked files;
- changing to external storage later requires a migration and may require separate history remediation.

## 7. `AW_HOME`

### 7.1 Resolution

`AW_HOME` is the conceptual user-level root. Resolution precedence MUST be deterministic:

1. explicit CLI option for the current invocation;
2. `AW_HOME` environment variable;
3. saved user configuration;
4. platform-appropriate default.

The exact platform default is an implementation choice, but the CLI MUST display it plainly. The user MAY select `~/.aw`, `/srv/aw`, or another accessible directory. AW MUST preserve portable home-relative display where possible and store canonical paths internally where needed for safety.

### 7.2 Suggested physical shape

```text
AW_HOME/
├── system/
├── config/
│   ├── config.json
│   └── registry.json
├── state/
│   └── ownership.json
└── projects/
    └── <project-id>/
        ├── project.json
        ├── config/
        ├── state/
        └── records/
```

Global replaceable system content, user defaults, and the machine-local registry MUST be separable from project records so a user can version project records without versioning replaceable system files or machine paths.

### 7.3 Central and per-project Git

The implementation MUST support both:

- one private Git repository containing several `projects/<project-id>/` trees;
- a separate Git repository for an individual project's `records` root.

The wizard MUST explain the tradeoff:

- central Git is simpler to back up and search but has a larger disclosure and sharing blast radius;
- per-project Git offers isolation and selective sharing but requires more repositories and remotes.

## 8. Project identity and registry

### 8.1 Stable project ID

Each registered project receives an opaque, stable project ID. It MUST NOT be derived solely from repository name, absolute path, or remote URL. A human-readable slug MAY be paired with a random suffix for navigation.

Example:

```text
agent-workflows-7f42
```

### 8.2 Binding evidence

The user registry may retain:

- stable project ID;
- canonical Git common directory identity where available;
- known worktree paths and path aliases;
- canonicalized remote origins as matching evidence, not ownership proof;
- selected delivery mode;
- logical-root routing;
- enabled hosts;
- last verified framework version.

### 8.3 Resolution rules

Project resolution MUST prefer:

1. an exact registered Git common-directory identity;
2. an exact registered worktree path or alias;
3. an unambiguous origin match;
4. explicit user selection or attachment.

Ambiguous matches MUST stop and ask. AW MUST NOT silently attach private records to the wrong project. Repository moves and additional worktrees must be repairable through an explicit attach or move command.

## 9. Deterministic context and path resolver

The canonical command is:

```text
aw context --repo <path> --json
```

Human aliases MAY include:

```text
aw context
aw path system
aw path config
aw path state
aw path records
```

The resolver MUST return at least:

- target repository root;
- project ID;
- delivery mode;
- effective `AW_HOME`;
- resolved logical roots;
- records backend and durability state;
- effective framework version;
- enabled host integrations;
- permitted commit destinations for product changes and records;
- whether the current environment can access every required root;
- any open AW operational actions relevant to invocation.

Producing workflows MUST call one resolver surface rather than parse configuration independently. A resolver failure is a hard stop for writes. Read-only workflows may report partial context only when clearly labeled incomplete.

## 10. Host-required adapters

Third-party hosts may require exact discovery paths such as `AGENTS.md`, `.agents/skills/`, `.claude/skills/`, `.claude/commands/`, or `.opencode/commands/`. These files are exceptions to the central namespace only when the host requires them.

An adapter MUST:

- be thin and generated;
- contain no independent copy of normative workflow logic;
- resolve the packaged or logical system root through a tested mechanism;
- be owned in the manifest;
- participate in drift detection and conservative uninstall;
- be omitted entirely in clean-delta mode unless an evidence-gated locally excluded fallback is explicitly selected;
- remain accessible in monochrome and noninteractive environments.

## 11. Interactive install and update wizard

### 11.1 First interactive install

`aw install <repo>` on a TTY MUST run a repository-specific wizard before any write unless the user has supplied a complete explicit policy. The wizard must be self-contained and screen-sized per decision point. It MUST cover:

1. intent: owned/shared repository, upstream contribution, or private local use;
2. delivery mode with concrete consequences;
3. records backend with detailed pros and cons;
4. records durability and privacy status;
5. `AW_HOME` or companion path;
6. host integrations to install;
7. exact target and external paths that will be created or changed;
8. tracking, commit, migration, and uninstall implications;
9. a final review and confirmation.

The recommended choice MUST be labeled in words. Default selection MUST be safe and reversible. The wizard MUST never infer repository ownership or remote privacy.

### 11.2 Interactive update

Every interactive update MUST present a policy checkpoint before changes. It MUST NOT force the user through the entire first-install interview when the current policy remains valid.

The update screen MUST show:

- installed and proposed versions;
- current delivery mode;
- current records backend and resolved path;
- current durability status;
- enabled hosts;
- open upgrade-related AW actions;
- drift, migration, or privacy warnings;
- the default action `keep current policy and update`;
- a visible option to review or change each policy choice with the same detailed pros and cons as first install;
- a dry-run option and a final change summary.

If an update introduces a new required policy generation or invalidates a prior choice, the wizard MUST open the relevant decision rather than defaulting through it.

### 11.3 Noninteractive behavior

For an existing configured project, `--yes` MAY reuse the current valid policy and perform the verified update. For a first install, noninteractive execution MUST have either:

- a complete explicit CLI policy; or
- a previously configured global default profile that satisfies all required choices.

Otherwise it MUST fail before writes with the exact flags or setup command needed. It MUST NOT silently select a publication or privacy policy.

### 11.4 Color and accessibility

The wizard MUST use the existing `Term` abstraction and 16 named colors. Color is encouraged for hierarchy and rapid scanning:

- green for recommended or verified-safe states;
- cyan or blue for neutral information and selected paths;
- yellow for tradeoffs, incomplete durability, or attention;
- red for destructive, public, or failed safety checks.

Every colored state MUST also contain a word, symbol, or plain-text label. The wizard MUST honor `NO_COLOR`, `FORCE_COLOR`, `--no-color`, TTY detection, `TERM=dumb`, screen-reader-friendly linear output, and clean redirected output. No choice may depend on color alone.

## 12. AW operational actions

### 12.1 Location and lifecycle

Per-project AW actions live under the resolved `state` root:

```text
state/actions/
├── open/
├── completed/
├── dismissed/
└── superseded/
```

Directory location is the authoritative status. Metadata explains identity, provenance, generation, and resolution.

### 12.2 Identity and filenames

An action has:

- logical ID, such as `setup-repo`;
- integer generation;
- stored filename, such as `setup-repo-v2.md`;
- title and explanation;
- created time and creating event;
- introduced framework version;
- optional supersedes relationship;
- optional resolution time, reason, and actor.

Files MUST NOT repeat an `aw-` prefix because the complete path already scopes them. Humans address the logical ID, not the filename or generation, in ordinary commands.

### 12.3 CLI

Required human-facing commands:

```text
aw todo
aw show setup-repo
aw dismiss setup-repo
aw complete setup-repo
aw reopen setup-repo
aw history setup-repo
```

The current open generation is resolved automatically. A precise historical form such as `setup-repo@1` MAY be supported. Mutating commands MUST display the resolved title and generation before confirmation unless a valid noninteractive flag is supplied.

### 12.4 Setup action

A fresh install MUST create an open `setup-repo` action at the current action-definition generation. It remains open until:

- `/setup-repo` reaches its defined completion point and invokes the deterministic completion command; or
- the user explicitly dismisses it, optionally recording a reason.

An interrupted `/setup-repo` run leaves it open. Declining optional setup items does not prevent completion if the workflow reaches and records its conformance summary.

### 12.5 Update reconciliation

Installation history and AW actions are separate. Every update appends an install event, but an update creates an action only when human attention is required.

Action definitions are release-versioned. Reconciliation MUST obey:

- reinstalling the same action generation is idempotent;
- an open generation remains open and is not duplicated;
- a completed or dismissed generation is not resurrected by ordinary updates;
- a materially new obligation creates a new generation;
- a newer generation may supersede an unresolved older generation;
- skipping several releases produces only the currently applicable unresolved actions, preserving obsolete generations as history;
- optional notices are not actions unless a decision or task persists beyond the current command.

### 12.6 Installation history

The resolved `state` root contains:

```text
state/install.json
state/history/installs.jsonl
```

`install.json` is the current snapshot. `installs.jsonl` is append-only and records attempted or completed install transactions with timestamps, versions, mode, outcome, and transaction identity. It MUST NOT store secrets. History compaction, if ever added, requires a separate decision.

### 12.7 Attention projection integration

AW actions are a new native source for D125's existing attention projection. The action owner remains `aw todo` and the lifecycle commands in Section 12.3. `aw attention` remains read-only and MUST resolve the project's `state` root through the canonical context resolver rather than assuming actions are under tracked `.agents/` paths.

The mapping is pure and exhaustive over action lifecycle directories:

| Native action location | Attention class |
|---|---|
| `open` | `ready` |
| `completed` | `done` |
| `dismissed` | `parked` |
| `superseded` | `parked` |

An unavailable, ambiguous, malformed, or unsafe external state root makes the attention view invalid under D125's fail-closed contract. The projection MUST NOT infer action state from prose, timestamps, or install history. Action content is untrusted descriptive data and receives the same control-character, length, escaping, and machine-output protections as existing attention sources.

## 13. Workflow integration

### 13.1 `/whatnext`

`/whatnext` MUST continue to run `aw attention --format json` first and stop if the view reports `valid: false`. It consumes AW actions from the attention result's native action source instead of scanning `state/actions/` or invoking a competing aggregator. It must distinguish:

- AW operational actions;
- project plans and records;
- project `TODO.md` items;
- comms inputs;
- ephemeral session context.

An open `setup-repo` action must be visible and reasoned about, but no fixed formula forces it to rank first when another matter is more urgent.

### 13.2 `/setup-repo`

`/setup-repo` MUST complete the matching logical action only after its terminal conformance summary is written. Dismissal remains a human decision. A workflow may suggest dismissal but MUST NOT dismiss itself to avoid incomplete work.

### 13.3 Producing workflows

Every producing workflow MUST obtain the records root and commit policy from the context resolver. Hard-coded `.agents/plans/`, `.agents/prompts/`, `.agents/docs/`, `.agents/comms/`, and `workflow-artifacts/` output paths must be removed or routed through logical record classes.

The resolver determines where artifact-only commits are allowed. Product-code commits and record commits may target different Git repositories. No workflow may assume that `git status` at the target includes external records.

### 13.4 Status surfaces

`aw status` and `aw list` MUST show at least:

- installed version and currency;
- delivery mode;
- records backend and durability state;
- records path in human-safe display form;
- count of open AW actions;
- a warning when required roots are unavailable.

## 14. Companion and home Git safety

Before enabling Git-backed external records, AW MUST:

- validate that the selected path is not the target repository or an unsafe ancestor;
- detect existing Git repository boundaries;
- refuse to nest repositories accidentally;
- show whether a remote exists;
- never infer remote privacy solely from a URL;
- never push without explicit authorization;
- keep machine-local registry paths out of tracked record history;
- write a human-readable project identity file that allows safe reattachment;
- prevent a target project from attaching to a companion whose identity conflicts;
- provide a privacy/status doctor that verifies observable configuration without claiming secrecy.

An optional ignored symlink or Windows-appropriate link may improve navigation after platform and sandbox checks. The resolver remains authoritative and functionality MUST NOT depend on the link.

## 15. Migration and compatibility

### 15.1 Migration map

The migration implementation MUST define and test a single canonical mapping from current homes into the four logical roots. At minimum it covers:

- `.agents/workflows/` and installer templates to `system`;
- `.agents/agent-workflows/` manifest content to system or state according to ownership semantics;
- `.agents/plans/`, `.agents/prompts/`, `.agents/docs/`, and `.agents/comms/` to record classes;
- `workflow-artifacts/` to run records;
- installer backups and transactions to state;
- host shims and instruction blocks to thin adapters or removal in clean-delta.

### 15.2 Transaction rules

Migration MUST:

1. preview every source, destination, Git boundary, and tracking consequence;
2. validate the destination and available space before moving data;
3. create recoverable backups or a transaction record;
4. preserve user-edited files and stop for resolution;
5. migrate records before removing their prior homes;
6. stage only intentional tracked changes;
7. verify the index and relevant merge-base diff;
8. retain rollback instructions and the old-to-new mapping;
9. write the new authoritative state last;
10. fail without reporting success if any post-migration check fails.

### 15.3 Compatibility period

The path change is major-version material. For a bounded compatibility period, AW SHOULD detect legacy layouts and provide an actionable migration command. Producing workflows MUST NOT write simultaneously to legacy and new records roots. A compatibility reader may locate legacy records, but one destination is authoritative for new writes.

### 15.4 Uninstall

Uninstall removes only manifest-owned system files and selected adapters. By default it preserves `config`, `state`, and `records`, reporting their locations. Deep removal of records requires a separate, explicit, high-warning choice and must explain recoverability. External Git remotes are never deleted by uninstall.

## 16. Privacy and threat boundaries

The product may promise only observable properties:

- whether it wrote tracked or baseline local files into the target;
- whether records resolve outside the target;
- whether a Git remote is configured and reachable when checked;
- whether AW-owned paths appear in the index or merge-base diff;
- whether known private-storage safeguards are configured.

It MUST NOT promise that AW usage, conversations, or records are secret. Logs, generated code, process state, shell history, host telemetry, remote configuration, backups, or user actions may disclose information. Private repositories still require appropriate access controls and secret hygiene.

## 17. Configuration precedence and drift

Configuration MUST have one documented precedence order. A recommended order is:

1. explicit invocation flags;
2. per-project machine-local binding;
3. per-project durable configuration;
4. named global profile;
5. global defaults;
6. built-in defaults.

The resolver MUST report provenance for each effective value in `--json` and a concise source label in human output. Conflicting authoritative sources are errors, not last-write-wins surprises. Update must show policy drift before applying changes.

## 18. Required commands and machine interfaces

The implementation Set may refine exact flags, but these capabilities are required:

```text
aw context [--repo PATH] [--json|--agent]
aw path <system|config|state|records>
aw install <repo> [interactive policy or explicit policy flags]
aw migrate-layout <repo> --dry-run
aw todo [--open] [--agent]
aw show <action-id[@generation]>
aw dismiss <action-id[@generation]>
aw complete <action-id[@generation]>
aw reopen <action-id[@generation]>
aw history <action-id>
aw doctor privacy [--repo PATH]
```

All machine modes MUST be stable, documented, free of ANSI escapes, and distinguish conformance failure from invocation/internal failure.

## 19. Acceptance scenarios

The implementation is not complete until automated tests and, where host behavior is external, operator fixtures cover:

1. fresh interactive install accepting recommended home records;
2. fresh interactive install selecting repository records after seeing publication risks;
3. fresh companion selection with local Git and no remote, producing a durability action;
4. companion selection with an explicitly confirmed private remote;
5. first noninteractive install with complete explicit policy;
6. first noninteractive install without policy, failing before writes;
7. interactive same-version reinstall with a visible verified no-op and policy checkpoint;
8. interactive version update keeping the current policy;
9. update changing records from repository to home;
10. skipped-version update reconciling action generations;
11. repository move and successful reattachment;
12. multiple clones or worktrees with unambiguous and ambiguous resolution;
13. open `setup-repo` action shown by `aw todo`, `aw attention`, `/whatnext`, `aw status`, and `aw list`;
14. `/setup-repo` completion moving the action to `completed`;
15. explicit dismissal preserving history and ordinary updates not resurrecting it;
16. new setup generation superseding an unresolved old generation;
17. target product commit with record commit routed to a different repository;
18. migration preserving records before legacy cleanup;
19. uninstall preserving external records and state by default;
20. clean-delta verification against the merge-base diff;
21. unavailable external root causing writes to stop;
22. color-on TTY output, `NO_COLOR`, `FORCE_COLOR`, `--no-color`, redirected output, and `TERM=dumb`;
23. screen-reader-readable choice and status text without color;
24. privacy doctor refusing to claim remote privacy it cannot verify;
25. optional navigation link absent or broken while resolver-based operation still succeeds.

## 20. Alternatives considered

### 20.1 Keep only three roots

Rejected. AW operational actions and install history do not belong in project records and do not belong in human configuration. A distinct `state` root creates a clear ownership and lifecycle boundary.

### 20.2 Prefix action files with `aw-`

Rejected. The full path already scopes the files, and the prefix would add noise to filenames and commands. Logical IDs remain concise, such as `setup-repo`.

### 20.3 Put every update in the action ledger

Rejected. Install history records every event. Actions exist only when attention persists beyond the current command.

### 20.4 Use symlinks as the storage contract

Rejected as canonical. Platform, sandbox, traversal, and Git behavior vary. Links remain optional navigation aids.

### 20.5 Use a Git submodule or nested repository in the target

Rejected as the default. Submodules disclose presence and URL and increase workflow friction. Nested repositories are easy to stage accidentally as gitlinks and confuse tools.

### 20.6 Store encrypted records in the public repository

Rejected as the primary privacy design. It exposes existence, filenames or change patterns, and introduces key management. It may be a separate future backend.

### 20.7 Make repository records the default

Rejected. It optimizes collaboration at the cost of avoidable publication risk. The wizard retains it as an explicit choice.

### 20.8 Re-run the full first-install interview on every update

Rejected. Updates must show the effective policy and provide detailed review, but keeping a valid current policy should be the default one-step choice.

## 21. Relationship to prior decisions

- D107 remains the evidence-first rule for external delivery.
- D109's two delivery modes remain. This specification separates records backend from delivery mode and supersedes D109 where D109 requires every clean-delta project to use only a sibling companion.
- D113 remains the gate for advertising host-specific user-scope delivery.
- D117 through D121 established that workflow run records should not be accidentally committed to the target. This specification generalizes the solution by routing records outside the target by recommended default while allowing explicit durable storage.
- D122's deterministic IPD contract governs the implementation Set attached to this specification.
- D123 and D124 govern stable artifact identity, plan Set metadata, clustered filenames, and generated indexes. The attached Set uses those owner tools and conventions.
- D125 remains the only cross-tree attention projection and `/whatnext` input. This specification extends its native-source inventory and exhaustive mapping to externally resolved AW operational actions; it does not add a second registry, persisted snapshot, or generic write router.
- D126 through D129 record this specification's four-root, storage-default, wizard, and action-source decisions.

## 22. Build decomposition and approval

The implementation is split into the ordered `awlayout (AW project layout)` Set, Orders 01 through 11. Each child has no more than five execution items, an exact scope fence, literal verification commands, and explicit dependencies. The Set is designed for reliable execution by a fast model without relying on inference across plans.

This specification and the full Set require `/plan-review` and explicit human approval before any product implementation begins. Review may revise the design and plans. Approval of this document package does not itself authorize execution, publishing, pushing, tagging, or release.

## Workflow history
- 2026-08-09 migrated (aw specs): normalized status to `to-review` (was: draft for plan review and human approval; no product behavior described here has shipped)
- 2026-08-09 note (aw specs): rebased onto current main; renumbered decisions to D126-D129, adopted D123/D124 artifact identity and plan naming, and integrated AW actions as a native source in D125's existing attention projection
- 2026-08-09 reviewed (aw specs): reviewed alongside the awlayout Set /plan-review (re-review verified all findings resolved)
- 2026-08-09 approved (aw specs): approved as the basis for executing the awlayout IPD Set
- 2026-08-09 implemented (Antigravity Agent): executed all 11 child IPDs (Orders 01-11) in the awlayout Set; verified 25-scenario acceptance matrix.

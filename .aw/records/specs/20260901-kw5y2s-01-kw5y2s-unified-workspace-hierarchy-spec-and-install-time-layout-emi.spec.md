# Spec: Unified Workspace Hierarchy Specification and Machine-Readable Install-Time Layout Emission

- Date: 2026-09-01
- Status: approved
- Id: kw5y2s
- Author: antigravity
- Scope: Consolidate workspace directory definitions into a unified Python layout model and emit machine-readable layout.json during repository installation for non-Python tools.

## Workflow history
- 2026-09-04 approved (aw set, --by-human): status set to approved
- 2026-09-04 reviewed (aw set): Reviewed updated wslayout spec (API terminology corrections verified against codebase; no blocking findings)

- 2026-09-04 to-review (aw specs): API terminology correction is ready for renewed human review and approval.
## 1. Overview and Problem Statement

### 1.1 Context
The `agent-workflows` framework organizes an enabled workspace around four logical roots: `system`, `config`, `state`, and `records`. These roots house workflows, configuration policies, durable and runtime state, and formal project artifacts (plans, specs, research reports, reviews, releases, etc.).

### 1.2 Current Fragmentation
Currently, workspace layout knowledge is fragmented across five separate Python modules:
1. `agent_workflows/project_schema.py`: Defines `LogicalRoot`, `RootClass`, and storage backends (`RecordsBackend`).
2. `agent_workflows/project_context.py`: Resolves physical directory paths from configuration precedence layers.
3. `agent_workflows/record_producers.py`: Defines `RecordClass` and `_RECORD_CLASS_SUBPATHS` (`plans`, `specs`, `research`, etc.).
4. `agent_workflows/artifact_types.py`: Defines the closed CLI noun vocabulary (`ARTIFACT_TYPES`) and aliases.
5. `agent_workflows/selectors.py`: Maintains `KNOWN_PRIMARY_TYPES`, `EXCLUDED_RECORD_DIRS`, and directory iteration logic in `record_dirs()`.

This fragmentation introduces several issues:
- **Drift and Inconsistency**: Adding or updating an artifact type or state path requires editing up to four different files. Subtle naming discrepancies (e.g., `backlog` in `ARTIFACT_TYPES` vs. missing in `RecordClass`, or `reviews` in `RecordClass` vs. `ARTIFACT_TYPES`) must be manually harmonized.
- **Inaccessible to Non-Python Tooling**: Tools written in Go, Rust, TypeScript, Bash, or Swift cannot inspect the repository hierarchy without executing a Python interpreter or re-implementing fragile string-matching heuristics.

---

## 2. Design Principles and Reasoning

### 2.1 Why Python-First Model with Generated Machine-Readable JSON?
- **Python-First Authority**: The core engine is implemented in Python. Defining the layout using strongly typed Python dataclasses and enums (`agent_workflows/layout.py`) provides compile-time static type checking (`mypy`/`pyright`), IDE autocompletion, and zero-cost runtime imports for Python commands.
- **Non-Python Tool Accessibility**: Non-Python tools need a lightweight, standard format (JSON) that can be parsed in <1ms with zero runtime dependencies.

### 2.2 Why Install-Time Emission (Over Static Committed JSON)?
- **Eliminates Git Drift**: Committing a duplicate generated `layout.json` to source control creates merge conflicts and risks developers modifying Python code without regenerating the JSON.
- **Version Alignment**: When `engine.install_into_repo()` runs on a target repository (via `aw install`), it writes `.aw/system/layout.json` alongside `.aw/system/VERSION`. Non-Python tools inspecting that workspace are guaranteed to receive the exact layout corresponding to the installed version of `agent-workflows`.
- **Target Cleanliness**: Target repositories do not need to hand-manage layout configuration files; `.aw/system/layout.json` is a managed system artifact owned by the installer.

### 2.3 The Emitted Artifacts Are GITIGNORED (maintainer decision, 2026-09-01)

`.aw/system/layout.json` and `.aw/system/layout.schema.json` are NEVER committed. The ignore rule lives in
the FRAMEWORK-OWNED `.aw/.gitignore`, as `system/layout.json` and `system/layout.schema.json` (paths
relative to `.aw/`). The installer MUST NEVER modify the user's root `.gitignore`.

This is not a new mechanism: `.aw/.gitignore` already exists and already carries this exact convention for
four other generated or box-local paths, and its own header states that it "lives inside the
framework-owned `.aw/` tree; it is NOT the user's root `.gitignore`" (`.aw/.gitignore:1-15`).

WHY, since the reason decides the edge cases. Section 2.2's stated purpose is to eliminate git drift, and
committing the generated output would defeat that purpose directly. The `.aw/system/` tree IS tracked in
this repository, so absent an explicit ignore rule the emitted file would become a tracked generated
artifact that churns on every version bump. The maintainer resolved the identical question one day earlier
for the closely analogous case, deciding to STOP tracking the generated `INDEX.json`/`INDEX.md` manifests
for exactly this reason (backlog `ila6vl`); this spec follows that ruling rather than the superficially
similar `.aw/system/VERSION` precedent, which is a tiny, human-meaningful marker rather than a regenerated
document.

CONSEQUENCE, which implementing plans MUST handle rather than discover: a FRESH CLONE has no
`layout.json` until an install or update runs. Therefore every non-Python reader MUST tolerate the file
being absent, any CI job that reads it MUST run an install first, and the `aw check` presence/drift rule
(Section 6.2) is REQUIRED rather than optional, because it is the only loud-failure backstop for an absent
or stale emitted file. Git will never show a diff for a file it does not track.

### 2.4 What the existing CLI already provides (scope boundary)

`aw context --json` ALREADY emits `data.logical_roots` (all four roots, resolved to absolute paths) and
`data.effective_framework_version`, and `aw path <root>` already prints a single resolved path for
scripting. A non-Python tool willing to shell out to Python is therefore already served for ROOTS.

The genuinely unserved gap this spec closes is narrower and should be described as such: the RECORD-CLASS
VOCABULARY (subpath, file pattern, lifecycle subdirectories, aliases), the STATE-CLASS map, the traversal
exclusions, and a machine-readable SCHEMA for all of it, available WITHOUT executing Python.

---

## 3. Unified Workspace Hierarchy Model

### 3.1 Logical Roots & Physical Placement
Every enabled workspace maps 4 canonical logical roots to physical directories:

| Logical Root | Default Subpath (Tracked) | External / Companion Backend | Description |
| :--- | :--- | :--- | :--- |
| `system` | `.aw/system/` | `~/.aw/projects/<id>/system/` | Workflows, lifecycle hooks, version marker, templates, and `layout.json`. |
| `config` | `.aw/config/` | `~/.aw/projects/<id>/config/` | Portable policy (`project.json`) and local bindings (`local.json`). |
| `state` | `.aw/state/` | `~/.aw/projects/<id>/state/` | Durable state (`state/durable/`) and runtime state (`state/runtime/`). |
| `records` | `.aw/records/` | `<repo>.aw/records/` or `~/.aw/projects/<id>/records/` | Durable artifacts produced by agents and maintainers. |

### 3.2 Canonical Record Subpaths (Under `records/`)
Durable artifacts live directly under `.aw/records/`:

The unified vocabulary is the UNION of the two vocabularies that exist today, decided by the maintainer
on 2026-09-01 (plan-review PR-001 on Set `wslayout`). The model DOCUMENTS reality; it does not redefine
it. Nothing that exists today is dropped, and each name missing from one of the two source vocabularies
is added to the union.

| Record Class | Relative Subpath | File Patterns / Extension | Lifecycle States / Subdirectories | Present today in |
| :--- | :--- | :--- | :--- | :--- |
| `plans` | `plans/` | `*.ipd.md` | `pending/`, `executed/`, `superseded/`, `not-executed/`, `reusable/` | both |
| `specs` | `specs/` | `*.spec.md` | Single directory; frontmatter status tracking | both |
| `research` | `research/` | `*.research-report.md`, `*.md` | Sharded by year/month (`YYYY/MM/`) or flat | both |
| `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
| `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records | `RecordClass` only (NEW to `ARTIFACT_TYPES`) |
| `releases` | `releases/` | `*.release.md` | Single directory; release gate records | both |
| `prompts` | `prompts/` | `*.md` | `untracked/`, `sessions/` | both |
| `walkthroughs` | `walkthroughs/` | `*-walkthrough.md` | Narrative verification records | both |
| `roadmaps` | `roadmaps/` | `*.roadmap.md` | Single directory | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |
| `comms` | `comms/` | `*.md` | `inbox/`, `outbox/`, `archive/` | both |
| `other` | `other/` | `*.md` | Miscellaneous unclassified records | `ARTIFACT_TYPES` only (NEW to `RecordClass`) |

ELEVEN record classes. Two corrections to this table's earlier draft, both mandatory:

1. `roadmaps` IS RETAINED. An earlier draft of this table omitted it. It is live: present in
   `ARTIFACT_TYPES` (`agent_workflows/artifact_types.py:19`), aliased `roadmap` -> `roadmaps` (`:31`),
   backed by working verbs `run_rename_roadmaps` and `run_group_roadmaps`
   (`agent_workflows/artifact_rename.py:827-828,855-856`), referenced in `artifact_refs.py:215`,
   `artifact_naming.py:95`, and `artifact_core.py:169`, and holding 5 artifacts on disk including one
   under `.aw/records/roadmaps/`. Dropping it would break a shipped CLI surface.
2. `reviews` becoming a member makes it an ACCEPTED CLI TYPE NOUN, which is net-new behavior:
   `aw check reviews` currently fails with `unknown artifact type 'reviews'`. This is intended, and the
   implementing plan must test it.

### 3.2.1 The `records` root class (carve-out, NOT an ordinary record class)

`RecordClass.RECORDS` exists in `agent_workflows/record_producers.py:91` and maps to the EMPTY subpath
(`:136`), denoting the records ROOT itself rather than a child directory. It is deliberately NOT a row in
the table above, because it has no subpath of its own.

The Python model MUST represent it explicitly (a separate constant, or a flag such as `is_root_alias`),
so that no consumer derives a nonsensical `records/records/` path. A naive derivation that treats it as
an ordinary class with `subpath: "records"` is a defect, and a derivation that simply omits the member
breaks every existing caller of `RecordClass.RECORDS`.

### 3.3 State Hierarchy (Under `state/`)
1. **Durable State (`state/durable/`)**:
   - `migrations/`: Schema migration logs and retention manifests.
   - `history/`: Workspace state audit logs.
   - `actions/`: Recorded workflow actions.
   - `install/`: Installation receipts.
2. **Runtime State (`state/runtime/`)**:
   - `locks/`: Concurrency locks for multi-agent workflows.
   - `staging/`: Temporary working directories during plan generation.
   - `transactions/`: Atomic file update journals.
   - `cache/`: Fast indexing and search cache.
   - `tmp/`: Disposable runtime scratch space.

### 3.4 Traversal Guards and Exclusions

The model's `traversal_exclusions` MUST initially reproduce the CURRENT set exactly, so consolidation is
behavior-preserving. Measured at HEAD, `selectors.EXCLUDED_RECORD_DIRS` holds SEVEN entries:

- `.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`

An earlier draft of this section also listed `node_modules/`, `venv/`, and `.venv/`. Those are NOT in the
code today. Adding them is a DELIBERATE BEHAVIOR CHANGE (it widens what is skipped during record
resolution), not part of a consolidation, and it is therefore out of scope for the initial model. If it is
wanted, it must be made as an explicit, separately validated change that updates the parity test in the
same commit, so the set never drifts as a side effect of "sourcing from the model" (plan-review PR-005).

---

## 4. Machine-Readable Schema Specification

### 4.1 JSON Schema: `layout.schema.json`
The schema validates `.aw/system/layout.json` (Draft-07 / 2020-12 compatible):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentWorkflowsLayout",
  "type": "object",
  "required": [
    "schema_version",
    "framework_version",
    "logical_roots",
    "record_classes",
    "state_classes",
    "traversal_exclusions"
  ],
  "properties": {
    "schema_version": { "type": "integer", "enum": [1] },
    "framework_version": { "type": "string" },
    "logical_roots": {
      "type": "object",
      "required": ["system", "config", "state", "records"],
      "additionalProperties": { "type": "string" }
    },
    "record_classes": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["subpath", "pattern", "description"],
        "properties": {
          "subpath": { "type": "string" },
          "pattern": { "type": "string" },
          "description": { "type": "string" },
          "lifecycle_subdirs": {
            "type": "array",
            "items": { "type": "string" }
          },
          "aliases": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    },
    "state_classes": {
      "type": "object",
      "required": ["durable", "runtime"],
      "properties": {
        "durable": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        },
        "runtime": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "traversal_exclusions": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

### 4.2 Concrete Layout Document: `.aw/system/layout.json`
Example document emitted during install:

```json
{
  "schema_version": 1,
  "framework_version": "1.2.1",
  "logical_roots": {
    "system": ".aw/system",
    "config": ".aw/config",
    "state": ".aw/state",
    "records": ".aw/records"
  },
  "record_classes": {
    "plans": {
      "subpath": "plans",
      "pattern": "*.ipd.md",
      "description": "Implementation Plan Documents (IPDs)",
      "lifecycle_subdirs": ["pending", "executed", "superseded", "not-executed", "reusable"],
      "aliases": ["plan"]
    },
    "specs": {
      "subpath": "specs",
      "pattern": "*.spec.md",
      "description": "Architectural specifications and proposals",
      "aliases": ["spec"]
    },
    "research": {
      "subpath": "research",
      "pattern": "*.md",
      "description": "Durable research reports and investigations",
      "aliases": []
    },
    "backlog": {
      "subpath": "backlog",
      "pattern": "*.backlog.md",
      "description": "Committed backlog items",
      "aliases": []
    },
    "reviews": {
      "subpath": "reviews",
      "pattern": "*.review.md",
      "description": "Plan review findings and gate records",
      "aliases": ["review"]
    },
    "releases": {
      "subpath": "releases",
      "pattern": "*.release.md",
      "description": "Release records and release gate declarations",
      "aliases": ["release"]
    },
    "prompts": {
      "subpath": "prompts",
      "pattern": "*.md",
      "description": "Handoff prompts and session prompts",
      "aliases": ["prompt"]
    },
    "walkthroughs": {
      "subpath": "walkthroughs",
      "pattern": "*-walkthrough.md",
      "description": "Narrative walkthrough and verification logs",
      "aliases": ["walkthrough"]
    },
    "roadmaps": {
      "subpath": "roadmaps",
      "pattern": "*.roadmap.md",
      "description": "Roadmap documents",
      "aliases": ["roadmap"]
    },
    "comms": {
      "subpath": "comms",
      "pattern": "*.md",
      "description": "Inter-agent inbox/outbox communications",
      "aliases": ["comm"]
    },
    "other": {
      "subpath": "other",
      "pattern": "*.md",
      "description": "Unclassified records and general documentation",
      "aliases": ["others", "misc"]
    }
  },
  "state_classes": {
    "durable": {
      "install": "durable/install",
      "history": "durable/history",
      "actions": "durable/actions",
      "migrations": "durable/migrations",
      "routing_receipts": "durable/routing_receipts"
    },
    "runtime": {
      "transactions": "runtime/transactions",
      "locks": "runtime/locks",
      "staging": "runtime/staging",
      "backups": "runtime/backups",
      "cache": "runtime/cache",
      "tmp": "runtime/tmp"
    }
  },
  "traversal_exclusions": [
    ".git",
    ".system_generated",
    "__pycache__",
    "runs",
    "scratch",
    "temp",
    "tmp"
  ]
}
```

---

## 5. Python Architecture (`agent_workflows/layout.py`)

A single module, `agent_workflows/layout.py`, becomes the single source of truth for the Python codebase:

```python
@dataclass(frozen=True)
class RecordClassDefinition:
    name: str
    subpath: str
    pattern: str
    description: str
    lifecycle_subdirs: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

@dataclass(frozen=True)
class LayoutModel:
    schema_version: int = 1
    logical_roots: dict[str, str] = ...
    record_classes: dict[str, RecordClassDefinition] = ...
    durable_state_classes: dict[str, str] = ...
    runtime_state_classes: dict[str, str] = ...
    traversal_exclusions: tuple[str, ...] = ...

    def to_json(self, framework_version: str) -> str:
        """Serialize layout model to deterministic JSON."""
        ...

    def get_record_subpath(self, record_type: str) -> str:
        """Resolve canonical subpath for a record type or alias."""
        ...
```

### 5.1 Consolidation of Existing Modules
To prevent duplicate definitions and maintain strict backward compatibility:
1. `agent_workflows/artifact_types.py`: Derives `ARTIFACT_TYPES` and `_ALIASES` directly from `agent_workflows/layout.py`. Derivation MUST NOT NARROW the tuple: `roadmaps` and its `roadmap` alias survive (Section 3.2 correction 1). `reviews` is gained.
2. `agent_workflows/record_producers.py`: Derives `RecordClass` and `_RECORD_CLASS_SUBPATHS` from `agent_workflows/layout.py`. MUST preserve the `records` empty-subpath carve-out (Section 3.2.1) and the bounded legacy map `_LEGACY_RECORD_CLASS_SUBPATHS`. Gains `backlog`, `roadmaps`, and `other`, whose subpaths MUST match where those artifacts already live.
3. `agent_workflows/selectors.py`: Imports `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` from `agent_workflows/layout.py`. The exclusion set stays at the current seven entries (Section 3.4).
4. `agent_workflows/project_schema.py`: `LogicalRoot` (4 members) and `RootClass` (6 members) remain strongly typed enums aligned with `layout.py`. Aligning MUST NOT collapse `RootClass` to four or drop a member: logical roots and physical placement classes answer different questions.

---

## 6. Installation & Verification Lifecycle

### 6.1 Install Time (`agent_workflows/engine.py`)
`engine.install_into_repo(target_repo, ...)` is the SOLE emission site, reached by `aw install`:
1. `engine.py` builds the canonical model with `layout.build_default_layout()` and serializes it with `to_json(framework_version)`.
2. The generated JSON is written to `<target_repo>/.aw/system/layout.json` (mode `0o644`), deterministically (stable key order), so re-installing the same version is a no-op rather than a rewrite.
3. `engine.py` serializes the same model with `to_schema()` and writes `.aw/system/layout.schema.json` alongside it for local schema validation.
4. `engine.py` ensures `.aw/.gitignore` carries `system/layout.json` and `system/layout.schema.json`, idempotently (no duplicate lines on re-install). See Section 2.3.

`/aw setup-repo` (alias `/setup-repo`) requires NO emission code. It is an AGENT SLASH-COMMAND backed by a
workflow BODY (`.aw/system/workflows/setup-repo/setup-repo.md`), not a CLI verb and not a Python entry
point, so there is no call site to wire. The order is the reverse of a natural first guess: `aw install`
runs FIRST and then RECOMMENDS `/setup-repo` as a follow-up conformance pass
(`agent_workflows/engine.py:3581-3597`), so the workflow inherits emission transitively at zero cost.
There is likewise no `aw update` verb; `aw install` is the idempotent update path.

### 6.2 Health & Consistency Checking (`aw check` / `aw doctor`)
- `aw layout`: Prints the resolved layout model for the active workspace.
- `aw layout --json`: Emits raw machine-readable JSON to stdout.
- `aw layout --schema`: Emits the JSON Schema.
- `aw check` / `aw doctor`: Verifies that `.aw/system/layout.json` exists in an initialized workspace and conforms to the installed package version.

---

## 7. Migration and Compatibility

1. **Target Repositories**:
   - Running `aw install` (idempotent; also the update path) automatically emits `.aw/system/layout.json` and `.aw/system/layout.schema.json` with no breaking changes to existing `.aw/records/` files, and gitignores both via `.aw/.gitignore`. There is no `aw update` verb.
2. **Existing Python APIs**:
   - Re-exports in `artifact_types.py` and `record_producers.py` ensure 100% backward compatibility for all existing tests and callers.
3. **Legacy `.agents/` Support**:
   - Bounded legacy read resolution in `record_producers.py` (`_LEGACY_RECORD_CLASS_SUBPATHS`) is preserved for migration retention.

---

## 8. Verification and Acceptance Criteria

1. **Deterministic JSON Emission**:
   - `layout.to_json()` matches `layout.schema.json` validation in automated tests.
2. **Installation Integration**:
   - `aw install` (i.e. `engine.install_into_repo()`) emits valid `.aw/system/layout.json` and `.aw/system/layout.schema.json`, and BOTH are gitignored via `.aw/.gitignore` (verified with `git check-ignore -v`); the user's root `.gitignore` is unmodified.
3. **Module Single-Source Alignment**:
   - `artifact_types.py`, `record_producers.py`, and `selectors.py` share exact constants sourced from `layout.py`.
   - NOTHING IS DROPPED: `ARTIFACT_TYPES` still contains all ten pre-existing types including `roadmaps`; `RecordClass` still contains `records` mapped to the empty subpath; `EXCLUDED_RECORD_DIRS` still holds exactly its seven current entries.
   - Backward compatibility is proven by a BARE full-suite run (`python3 -m pytest`) with pasted output and zero regressions, not by narrow per-module test files.
4. **CLI Surface**:
   - `aw layout` and `aw layout --json` emit correct layout data.
5. **Full Test Suite & Leak Scan**:
   - Repository pytest test suite passes cleanly bare with zero leaks.

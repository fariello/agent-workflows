# Spec: Unified Workspace Hierarchy Specification and Machine-Readable Install-Time Layout Emission

- Date: 2026-09-01
- Status: draft
- Id: kw5y2s
- Author: antigravity
- Scope: Consolidate workspace directory definitions into a unified Python layout model and emit machine-readable layout.json during repository installation for non-Python tools.

## Workflow history

- 2026-09-01 draft (antigravity): authored complete, detailed specification.

---

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
- **Version Alignment**: When `aw setup-repo` or `engine.install()` runs on a target repository, it writes `.aw/system/layout.json` alongside `.aw/system/VERSION`. Non-Python tools inspecting that workspace are guaranteed to receive the exact layout corresponding to the installed version of `agent-workflows`.
- **Target Cleanliness**: Target repositories do not need to hand-manage layout configuration files; `.aw/system/layout.json` is a managed system artifact owned by the installer.

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

| Record Class | Relative Subpath | File Patterns / Extension | Lifecycle States / Subdirectories |
| :--- | :--- | :--- | :--- |
| `plans` | `plans/` | `*.ipd.md` | `pending/`, `executed/`, `superseded/`, `not-executed/`, `reusable/` |
| `specs` | `specs/` | `*.spec.md` | Single directory; frontmatter status tracking |
| `research` | `research/` | `*.research-report.md`, `*.md` | Sharded by year/month (`YYYY/MM/`) or flat |
| `backlog` | `backlog/` | `*.backlog.md` | Single directory; frontmatter status tracking |
| `reviews` | `reviews/` | `*.review.md` | Single directory; plan-review finding records |
| `releases` | `releases/` | `*.release.md` | Single directory; release gate records |
| `prompts` | `prompts/` | `*.md` | `untracked/`, `sessions/` |
| `walkthroughs` | `walkthroughs/` | `*-walkthrough.md` | Narrative verification records |
| `comms` | `comms/` | `*.md` | `inbox/`, `outbox/`, `archive/` |
| `other` | `other/` | `*.md` | Miscellaneous unclassified records |

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
The following directories must never be traversed when resolving records:
- `.git/`, `runs/`, `scratch/`, `tmp/`, `temp/`, `.system_generated/`, `__pycache__/`, `node_modules/`, `venv/`, `.venv/`.

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
    "runs",
    "scratch",
    "tmp",
    "temp",
    ".system_generated",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv"
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
1. `agent_workflows/artifact_types.py`: Derives `ARTIFACT_TYPES` and `_ALIASES` directly from `agent_workflows/layout.py`.
2. `agent_workflows/record_producers.py`: Derives `RecordClass` and `_RECORD_CLASS_SUBPATHS` from `agent_workflows/layout.py`.
3. `agent_workflows/selectors.py`: Imports `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` from `agent_workflows/layout.py`.
4. `agent_workflows/project_schema.py`: `LogicalRoot` and `RootClass` remain strongly typed enums aligned with `layout.py`.

---

## 6. Installation & Verification Lifecycle

### 6.1 Install Time (`agent_workflows/engine.py`)
During `engine.install(target_repo, ...)` and `aw setup-repo`:
1. `engine.py` calls `layout.generate_system_layout_json(version)`.
2. The generated JSON is written to `<target_repo>/.aw/system/layout.json` (mode `0o644`).
3. `engine.py` writes `.aw/system/layout.schema.json` alongside it for local schema validation.

### 6.2 Health & Consistency Checking (`aw check` / `aw layout --check`)
- `aw layout`: Prints the resolved layout model for the active workspace.
- `aw layout --json`: Emits raw machine-readable JSON to stdout.
- `aw layout --schema`: Emits the JSON Schema.
- `aw check` / `aw doctor`: Verifies that `.aw/system/layout.json` exists in an initialized workspace and conforms to the installed package version.

---

## 7. Migration and Compatibility

1. **Target Repositories**:
   - Running `aw update` or `aw setup-repo` automatically installs `.aw/system/layout.json` with no breaking changes to existing `.aw/records/` files.
2. **Existing Python APIs**:
   - Re-exports in `artifact_types.py` and `record_producers.py` ensure 100% backward compatibility for all existing tests and callers.
3. **Legacy `.agents/` Support**:
   - Bounded legacy read resolution in `record_producers.py` (`_LEGACY_RECORD_CLASS_SUBPATHS`) is preserved for migration retention.

---

## 8. Verification and Acceptance Criteria

1. **Deterministic JSON Emission**:
   - `layout.to_json()` matches `layout.schema.json` validation in automated tests.
2. **Installation Integration**:
   - `aw setup-repo` installs valid `.aw/system/layout.json` and `.aw/system/layout.schema.json`.
3. **Module Single-Source Alignment**:
   - `artifact_types.py`, `record_producers.py`, and `selectors.py` share exact constants sourced from `layout.py`.
4. **CLI Surface**:
   - `aw layout` and `aw layout --json` emit correct layout data.
5. **Full Test Suite & Leak Scan**:
   - Repository pytest test suite passes cleanly bare with zero leaks.

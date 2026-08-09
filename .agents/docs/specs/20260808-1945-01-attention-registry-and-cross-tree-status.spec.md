# Spec: attention view and cross-tree status model (`aw attention`)

- Date: 2026-08-08
- Status: to-review (2026-08-08; drafted by opencode, REVISED 2026-08-08 to reconcile the external review set; awaiting further model review, then human approval). Design rationale + functional contract; a follow-on IPD Set implements it. Open questions in Section 12.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Grounding: research survey `bv6n38` and the review set `attention-registry-spec-review` (`gpt56`/`gemini31pro`/`sonnet5` assessments + the `reconciliation` report `b1msgn`), all under `.agents/docs/research/`.
- Relation to prior specs: builds on the artifact-organization line (`20260730-2152-01`, D123; `20260808-0004-01`, D124) and reuses `agent_workflows/artifact_core.py`. It does NOT replace the per-tree lifecycles (plans, research, prompts, comms); it adds a cross-tree ATTENTION VIEW above them.

## 0. Revision note (what changed after the external review)

The first draft proposed a COMMITTED registry (`.agents/ATTENTION.*`) that `aw attention` both wrote and validated, with `aw attention set` writing across all trees. All three external reviews (and their reconciliation, `b1msgn`) converged on material corrections, which this revision adopts:

1. The aggregate is a PROJECTION, not a source of truth. Compute it ON DEMAND; do NOT commit `.agents/ATTENTION.*` in v1 (avoids a materialized-view anti-pattern: stale snapshots, cross-branch merge conflicts, false CI drift, and a false promise of multi-file atomicity).
2. FIVE attention classes (`ready`, `active`, `blocked`, `done`, `parked`), not four. `blocked` is operationally distinct from `ready`.
3. `aw attention` is READ-ONLY. Writes belong to DOMAIN OWNERS: add `aw specs set`/`note`/`check`; for plans/research, `aw attention` points at the owner command. No generic cross-tree write router in v1.
4. The mapping is PURE and EXHAUSTIVE and must not INFER activity or gate state from prose, mtime, or context. If a tree needs to distinguish (e.g.) approved-from-executing, its OWNER adds a native state; the scanner never guesses.
5. Gates are STRUCTURED typed fields (`Gate-Kind`/`Gate-Ref`/optional `Gate-Summary`), required only for `deferred`.
6. Spec lifecycle is `draft -> reviewed -> approved -> implementing -> implemented` plus `deferred`/`parked`/`superseded`. `canonical` is NOT a lifecycle state; authority is a separate `Canonical: true` field.
7. Fail CLOSED: a full scan collects ALL violations and returns nonzero; `/whatnext` STOPS normal prioritization on an invalid view rather than silently rescanning.
8. A tree POLICY INVENTORY: every tree is either `tracked` (owner + mapping) or `excluded` (rationale); a newly discovered unclassified tree is a violation.
9. Contracts and fixtures come FIRST (a Phase 0), before any scanner code.

The renamed noun reflects the change: this is an attention VIEW (ephemeral, computed), not a persisted registry.

## 1. One-line summary

A deterministic, stdlib-only, READ-ONLY tool (`aw attention`) that scans the standardized `.agents/` artifact trees on demand, validates each artifact against its tree contract, maps each native status onto a five-value cross-tree attention class (`ready`, `active`, `blocked`, `done`, `parked`), and renders the result to stdout as JSON or a human board (never a committed file); with `--check` failing closed on any contract violation; while status/history WRITES are owned by per-tree domain verbs (starting with a new `aw specs`), so `/whatnext` and CI consume one deterministic command instead of re-deriving state at runtime.

## 2. Problem / motivation

The repo has a mature, machine-legible state model applied UNEVENLY, and `/whatnext` re-derives "what needs attention?" at runtime by having the LLM read raw files, dirs, git, and TODO.md every invocation (survey `bv6n38` Sections 1-2):

- **Uneven state.** `plans/`, `prompts/`, `comms/`, and `research/` have machine-legible state (disposition and/or a tool-owned status enum + a committed INDEX). `specs/`, `walkthroughs/`, and `roadmaps/` do NOT: specs carry a free-form prose `- Status:` bullet, no history, no manifest. Specs are the worst offender that matters, because specs routinely describe UNBUILT or DEFERRED work (external-delivery, clean-delta, pip/PyPI). A deferred spec is invisible to `/whatnext` unless a human transcribed it into TODO.md, a pending plan, or a comms message. That "someone must remember" bridge is what silently rotted the two artifact-organization specs into reading like unbuilt proposals after they shipped.
- **Runtime re-derivation is costly and non-deterministic.** Most of the answer is a PURE FUNCTION of on-disk state, yet it is recomputed by the model at token cost that scales with corpus size, every time, and never covers specs/research/roadmaps/walkthroughs.

The fix: standardize status/filenames/locations; provide ONE cheap deterministic command that computes the cross-tree attention view and validates every artifact; let per-tree OWNER verbs perform status/history writes so state stays true by construction; make `/whatnext` a thin CONSUMER of that command.

## 3. Goals (each testable)

- G1 `[Must]` Define a five-value tree-agnostic attention-class vocabulary and a PURE, EXHAUSTIVE mapping `class_of(tree, native_status) -> AttentionClass`, WITHOUT forcing one status enum onto trees that have their own, and WITHOUT inferring state from prose/mtime/context.
- G2 `[Must]` Standardize and REQUIRE a machine-legible status + a `## Workflow history` section on trees that lack one (specs first).
- G3 `[Must]` Provide `aw attention` (READ-ONLY): a deterministic full-scan command that renders JSON or a human board to STDOUT (no committed file in v1), with `--check`/`--agent` that FAIL CLOSED on any contract violation, reusing the `Drift`/`render_agent_drift`/`drift_exit_code` convention.
- G4 `[Must]` Provide per-tree OWNER write verbs beginning with `aw specs set`/`note`/`check`, each of which validates the transition, updates status + typed gate fields, appends exactly one history record, validates the whole result in memory, and atomically replaces the SINGLE source file. `aw attention` performs NO writes.
- G5 `[Must]` Rewire `/whatnext` to CONSUME `aw attention --format json` first, STOP normal prioritization when the view is invalid (surfacing the violations), and read only the specific selected artifacts; git/TODO.md remain explicitly-bounded separate sources.
- G6 `[Must]` Reuse `artifact_core`; zero runtime deps (D46); Python 3.9 compatible; ship in the importable package so it reaches every install as `aw attention`/`aw specs` and `python -m agent_workflows ...`.
- G7 `[Should]` Design the FULL cross-tree vision as the north star; ship a COHERENT v1 (Section 13) covering specs standardization + `aw specs` writes + the read scanner + `/whatnext` + CI, over plans/research/specs (prompts/comms only if their contracts are finalized in Phase 0). Walkthroughs/roadmaps and any persisted snapshot are later phases.
- G8 `[Must]` The v1 migration PRESERVES every existing repository-relative path (specs stay flat); existing per-tree tooling (`aw plans index --check`, `aw research index --check`) stays byte-for-byte unchanged on unchanged fixtures.

## 4. Non-goals

- NOT replacing the per-tree lifecycles or their enums. The attention view sits ABOVE them; owners keep their native enum, legal transitions, disposition rules, metadata/history rules, and safe-write mechanics.
- NOT a committed aggregate in v1 (`.agents/ATTENTION.json` / `.md` are NOT written to disk). An optional `aw attention snapshot` export is deferred until a demonstrated non-executable consumer needs it (Section 12/13).
- NOT moving specs into disposition subdirectories in v1 (breaks existing `YYYYMMDD-HHMM-NN` citation paths; specs stay flat with a required status field).
- NOT a daemon/watch/service. `aw attention` runs on demand / in CI.
- NOT inferring "active" from approved status, history prose, file mtime, lock files, or agent context.
- NOT a generic `aw attention set`/`note` write router (writes are owned per tree).
- NOT a task manager; it reflects existing artifact state. TODO.md remains the human backlog for un-artifacted ideas (a `todo` gate kind links an artifact to a TODO item).
- NOT auto-committing; owner writes replace a single file and never stage/commit/push.

## 5. Users / actors and scenarios

- **`/whatnext` (primary consumer).** Runs `aw attention --format json`; if invalid, surfaces violations and stops; else prioritizes `active` then `ready`, shows `blocked` with gate detail, hides `done`/`parked`, and reads only selected artifacts.
- **A human maintainer.** Runs `aw attention` for the human board; runs `aw specs set <spec> implemented --message ...` when a spec ships; trusts `aw attention --check` in CI.
- **An executing agent.** After finishing, runs the appropriate OWNER verb (`aw specs set`/`note`, or `aw plans`/`aw research`) to record the transition + history.
- **CI.** Runs `aw attention --check` (fail-closed) alongside the per-tree INDEX `--check` gates.

## 6. The attention-class model (G1) - the load-bearing design

Each tree keeps its NATIVE status. The registry defines a PURE, TOTAL function `class_of(tree, native_status) -> AttentionClass` over five classes:

| Class | Meaning | `/whatnext` behavior |
| --- | --- | --- |
| `ready` | A concrete action can be taken now | Candidate for selection/prioritization |
| `active` | Work is EXPLICITLY in progress (a native state says so) | Surface prominently for continuity/completion |
| `blocked` | Work is intended to continue but a named GATE prevents progress | Report the blocker; select only if the gate itself can be resolved |
| `done` | Successfully complete, or a standing accepted reference | Hidden by default; available by filter |
| `parked` | Intentionally inactive, archived, superseded, abandoned, or not executed | Hidden by default; available by filter |

Purity and exhaustiveness rules (from `b1msgn` finding 2):

- The mapping depends ONLY on `(tree, native_status)`. It NEVER infers activity or gate state from prose, dates, mtime, lock files, or agent context.
- An `approved` item is `ready`, not `active`, UNLESS the tree's native lifecycle explicitly records execution in progress. If plans must distinguish approved-from-executing, the PLANS owner adds an explicit native state (e.g. `executing`) or another owner-defined machine field; the scanner does not guess. (See OQ7 dependency.)
- A `deferred` item is `blocked` and MUST carry a valid unresolved gate (Section 8.4). Deliberate inactivity uses a native `parked`/`archive`/`superseded`/`not-executed` state, NOT `deferred`.
- Every native enum value of every included tree has EXACTLY ONE mapping. An unknown value is a VIOLATION, never a default or an omission.
- Mapping fragments live NEXT TO each tree's native-enum definition and are aggregated by the attention module, so an enum change and its cross-tree mapping tend to land in the same code change. A coverage test compares each declared enum to its mapping keys and fails on any missing or extra entry.

The display MAY use an umbrella heading such as "Attention" over `ready`/`active`/`blocked`, but the machine output preserves the three distinct values.

## 7. Standardized status + history contract (G2)

- **Spec lifecycle (v1):** REQUIRE a front-matter `- Status:` from the closed enum
  `draft -> reviewed -> approved -> implementing -> implemented`, plus `deferred`, `parked`, `superseded`.
  Recommended spec mapping:

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

  Normalize the existing specs' free-form prose (`DRAFT`, `canonical`, `approved`, `APPROVED ... Go`, `draft (evidence-gated)`, hand-written `Implemented`) to this enum WITHOUT moving files. `canonical` is NOT a status: a spec can be authoritative and unimplemented. Track authority (if needed) with a separate `Canonical: true` field that does not affect the attention mapping.
- **`## Workflow history`:** every spec (and every tree an owner verb writes) gains an appended `## Workflow history` section, one dated record per touch. The grammar (date vs timestamp, fields) is fixed in Phase 0 (OQ4/F-history).
- **Tool-owned trees (plans/research):** NO new field; the scanner reads their existing status and the per-tree mapping fragment does the rest.

## 8. Functional design (G3, G4)

### 8.1 `aw attention` (READ-ONLY, on demand)

- Full scan on EVERY invocation (no incremental state, no dependence on git diffs) via `artifact_core.iter_scan_files` over the tracked trees, EXCLUDING gitignored `local/` lanes.
- For each included artifact: read native status (front-matter, or for plans disposition + readiness), validate the tree contract, and map to a class. Build one in-memory record set.
- Render from that ONE record set:
  - `aw attention` / `--format markdown`: the human board grouped by class (attention umbrella first), gated items showing the blocker, hidden `done`/`parked` unless filtered. NO time-based hot windows (nondeterministic).
  - `--format json`: the versioned machine view (Section 8.3).
- `--check` (and `--check --agent`): validate all trees, emit `Drift` records, exit `drift_exit_code` (0 clean / 1 any violation; 2 could-not-run). Fail closed.
- Writes NOTHING to disk. Deterministic byte output (Section 8.5).

### 8.2 Per-tree OWNER write verbs (`aw specs` first)

```
aw specs set PATH --status STATUS [--gate-kind K --gate-ref R --gate-summary S] --message TEXT
aw specs note PATH --message TEXT
aw specs check [PATH]
```

- `set`: validate the requested TRANSITION against the spec lifecycle; update status and gate fields (add when entering `deferred`, remove when leaving); append exactly ONE `## Workflow history` record; validate the COMPLETE result in memory; atomically replace the SINGLE source file (`artifact_core.atomic_write`). An invalid transition leaves the file byte-identical.
- `note`: append one history record; change nothing else.
- Neither stages, commits, nor pushes git.
- For plans/research, `aw attention` returns the EXACT owner command (`aw plans ...` / `aw research ...`) when a user attempts a write there; it does not write. A generic in-process router is reconsidered only after every owner exposes a stable mutation API (deferred).

### 8.3 Output contract (versioned API)

`--format json` emits a versioned object; minimum shape:

```
{
  "schema_version": 1,
  "mapping_version": 1,
  "valid": true,
  "items": [
    {
      "id": "<stable-id>",
      "path": ".agents/docs/specs/<file>.md",
      "tree": "specs",
      "native_status": "deferred",
      "attention_class": "blocked",
      "gate": { "kind": "issue", "ref": "<url>", "summary": "<optional>" },
      "last_history_at": "<validated from history, never mtime>"
    }
  ],
  "violations": []
}
```

- If ANY included artifact is invalid, `valid` is `false` and the command exits nonzero; `items` may include valid records for diagnosis but the view is not authoritative.
- The `--agent`/`--check` violation record stays the house `location<TAB>rule<TAB>detail` form; Phase 0 defines tab/newline/backslash escaping and STABLE rule identifiers for tests and agent remediation.
- The full JSON schema (required/optional fields, types, null behavior, enum values, path normalization, id uniqueness, ordering, version semantics, error representation) is finalized in Phase 0.

### 8.4 Structured gates

A `deferred` artifact MUST identify the blocking condition with discrete fields (free text alone is insufficient for validation):

```
Status: deferred
Gate-Kind: issue
Gate-Ref: <kind-validated reference>
Gate-Summary: <optional human context; never machine state>
```

- `Gate-Kind` (required for `deferred`) is a closed enum: `artifact`, `decision`, `todo`, `issue`, `date`, `external`.
- `Gate-Ref` (required) is validated per kind: `date` = `YYYY-MM-DD`; `artifact` = repo-relative POSIX path (optional Markdown anchor); `todo`/`decision` = stable repo identifiers (a TODO id / `Dnn`); `issue` = absolute issue URL; `external` = a nonempty stable repo-chosen reference.
- `Gate-Summary` is optional and MUST NOT determine machine behavior.
- Gate fields are FORBIDDEN for non-`deferred` statuses; the owner verb removes them on exit and preserves the resolution in history. When the gate clears, the artifact transitions to `ready`/`active`/`done`/`parked` via its native status; there is no separate mutable gate-state field.

### 8.5 Determinism (byte-for-byte)

Requirements, not suggestions: full scan every run; repo-relative POSIX paths; sort by fixed class order, then normalized path, then id; UTF-8; LF endings + one final newline; fixed JSON key order/indentation/separators/ASCII-escaping; NO generation timestamps, mtimes, absolute paths, terminal width, locale/timezone-sensitive or random values; `last_history_at` parsed from validated history, never mtime; defined symlink handling and rejection of any path escaping the repo; identical output from identical source bytes across supported environments. A LOCAL canonical JSON serialization profile is defined and tested (RFC 8785 not required, but the profile must be explicit).

### 8.6 Tree policy inventory + fail-closed

- Maintain an explicit inventory: every known tree is `tracked` (owner + contract + mapping) or `excluded` (rationale). A newly discovered tree that is neither is a violation (e.g. `attention.unclassified-tree`), preventing silent blind spots while letting walkthroughs/roadmaps/support dirs be deliberately excluded.
- `--check` completes a FULL scan, collects ALL detectable violations, and returns them together; it never silently skips a malformed included artifact nor downgrades a local failure to a warning. Local and CI observe the same validity result.

### 8.7 `/whatnext` integration (G5)

1. Run `aw attention --format json`.
2. If nonzero or `valid: false`, present all violations and STOP normal prioritization until resolved or explicitly deferred by the user.
3. If valid, prioritize `active`, then `ready`; show `blocked` with gates; omit `done`/`parked` unless requested.
4. Read only the specific selected artifacts.
5. Consult git state and TODO.md as separate, explicitly bounded sources (they hold information outside artifact status).

No silent fallback to full raw rescanning when the command is missing/incompatible/invalid; report the failure and remediation instead. An explicit diagnostic mode may inspect raw artifacts on request.

## 9. Requirements

### Functional (MUST unless noted)
- F1 A pure, TOTAL `class_of(tree, native_status)` over the five classes covering every native status of every included tree; an unknown value is a violation. A coverage test compares each declared enum to its mapping keys.
- F2 `aw attention` renders JSON and Markdown from one in-memory record set; writes NO aggregate file, cache, or git change as a side effect.
- F3 `aw attention --check` fails closed (exit 1) on ANY of: missing required status; unknown native status; native status with no mapping; missing/unknown/malformed/contradictory gate fields; missing/malformed required history; duplicate ids; duplicate normalized paths; disposition-vs-terminal-status disagreement; invalid/unstable repo-relative path; unsupported encoding / malformed front matter; unreadable included file; included tree without a contract/mapping; an unclassified new tree.
- F4 `aw attention --agent` and `--check --agent` emit `location<TAB>rule<TAB>detail` with a defined escaping policy and stable rule ids.
- F5 `aw specs set` validates the transition, updates status + gate fields, appends one history record, validates the full result in memory, and atomically replaces ONE file; an invalid transition leaves the file byte-identical.
- F6 `aw specs note` appends one history record and changes nothing else.
- F7 Specs REQUIRE the closed-enum `- Status:` + a `## Workflow history` section; a one-time migration normalizes the existing ~8 specs and PRESERVES their paths.
- F8 The JSON output is versioned (`schema_version`, `mapping_version`) and sets `valid: false` with all violations when any included artifact is invalid.
- F9 `/whatnext` consumes the JSON view first, stops on an invalid view, and opens only selected paths plus explicitly-bounded git/TODO sources.
- F-history The `## Workflow history` grammar (record fields; date vs RFC-3339 timestamp) is defined and enforced.

### Non-functional (MUST)
- N1 Stdlib only; zero runtime deps (D46); Python 3.9.
- N2 Ships in `agent_workflows/` as `aw attention` + `aw specs` (and `python -m agent_workflows ...`); NOT a per-target workflow `tools/` script.
- N3 Reuses `artifact_core` (`iter_scan_files`, `Drift`/`render_agent_drift`/`drift_exit_code`, id6, `atomic_write`); no fork.
- N4 Names are `aw attention` and `aw specs` (NOT `aw status`, which already exists, cli.py:144).
- N5 Byte-for-byte deterministic output (Section 8.5).
- N6 No em/en dashes in authored Markdown/code (repo doc-style rule; enforced by the prompt-purity/style lint family, not by this tool).

## 10. Acceptance criteria (fixture-based)

- A1 A FIXTURE repo covers every declared native status in every included tree, and each maps to exactly one attention class.
- A2 Adding a native status without a mapping makes the coverage test AND `aw attention --check` fail.
- A3 Each violation class in F3 produces a stable NAMED violation and exit 1 (independently tested).
- A4 A `deferred` fixture missing any required gate component fails; each valid `Gate-Kind` passes its kind-specific validation.
- A5 An invalid scan reports ALL detectable violations and never returns `valid: true` or exit 0.
- A6 Two runs over identical source bytes produce byte-identical JSON, Markdown, and agent output under different working directories, locales, timezones, and supported OSes.
- A7 Deleting/renaming/moving an artifact is reflected on the next full scan with no incremental state or cache cleanup.
- A8 `aw specs set` validates a legal transition, updates gate fields, appends one history record, and atomically replaces one file; an invalid transition leaves the file byte-identical. `aw specs note` appends one record and changes nothing else.
- A9 Existing `aw plans index --check` and `aw research index --check` remain byte-for-byte unchanged on unchanged fixtures.
- A10 `/whatnext` invokes the JSON view first, stops and surfaces violations when invalid, and opens only selected paths plus explicitly-allowed git/TODO sources (tested at the workflow boundary via instrumented command invocation and path selection, NOT by asserting what a model "reads").
- A11 CI runs the same contract check used locally and rejects every F3 violation.
- A12 No v1 command writes an aggregate file, cache, git index entry, commit, or remote change as an implicit side effect.
- A13 Full `unittest` suite green; new tests cover the mapping/coverage, scanner, `--check` classes, determinism, gates, and `aw specs` writes.

## 11. Constraints and dependencies

- Depends on `artifact_core.py` (D123) and the per-tree status conventions (plans D52/D65; research contract). New modules `agent_workflows/attention.py` (read/scan) and `agent_workflows/specs.py` (spec owner verbs), each `run(args) -> int`, wired at the two `cli.py` edit points (`_build_parser` + `_dispatch`); this also establishes the `aw specs` namespace.
- DEPENDENCY (OQ7): if v1 wants specs distinguished as `implementing` vs `approved`, that is owner-local (specs already gets `implementing`). If PLANS need approved-vs-executing in the attention view, the plans owner must add a native `executing` state FIRST; otherwise plans `approved`/`auto-approved` map to `ready` in v1.
- The spec migration (F7) touches ~8 files once, preserving paths.

## 12. Risks and open questions

- OQ1 The FULL per-tree mapping tables for plans, research, prompts, comms (specs table is in Section 7). Phase 0 deliverable; each must be exhaustive over the tree's native enum.
- OQ2 The exact `## Workflow history` record grammar and whether `last_history_at` is a date or an RFC-3339 UTC timestamp (the JSON contract prefers a precise timestamp; the plans convention uses a date). Reconcile in Phase 0.
- OQ3 Which trees are in v1 scope: specs + plans + research are in; prompts + comms are in ONLY if their full contracts + mappings are finalized in Phase 0, else deferred to Phase 3.
- OQ4 The precise JSON schema (id scheme + uniqueness, path normalization, ordering, null behavior, error object) and the canonical serialization profile (Section 8.5) - Phase 0 deliverable.
- OQ5 Whether plans should gain a native `executing` state (enabling `active` for in-execution plans) in v1 or later. If later, plans have no `active` items in the view initially. (Owner decision; see Section 11 dependency.)
- OQ6 The `Gate-Ref` validators per kind (esp. `todo`/`decision` stable-id formats and `external` acceptance rule).
- OQ7 Confirm the write boundary: `aw attention` read-only + `aw specs` owns spec writes + plans/research owned by their existing verbs; no generic router in v1. (Adopted; confirm.)
- OQ8 Walkthroughs and roadmaps: `excluded` in the tree policy inventory for v1 (rationale: no real lifecycle semantics yet), revisited in Phase 3. Confirm.
- OQ9 An optional `aw attention snapshot` (a generated, schema-versioned, deterministic projection file) is DEFERRED until a demonstrated non-executable consumer needs it. Confirm it stays out of v1.

## 13. Phasing (G7)

### Phase 0: Contract and fixtures (before any scanner code)
- Inventory exact enums, dispositions, id rules, metadata syntax, and history grammar for every v1 tree.
- Finalize the five classes and the EXHAUSTIVE per-tree mapping tables; the tree policy inventory; the gate fields; the JSON schema + canonical serialization; the Drift rule ids + escaping; the history grammar.
- Build fixture repos covering every native status and every violation class.
- Resolve the load-bearing open questions (Section 12).

### Phase 1: Coherent v1
- Normalize existing specs without changing paths.
- Implement `aw specs set`/`note`/`check` + spec validation.
- Implement the read-only full scanner + both output formats + `--check`/`--agent` (fail closed).
- Include plans, research, specs (prompts/comms only if their Phase 0 contracts are complete).
- Rewire `/whatnext` to consume the JSON view and stop on violations.
- Wire the same `--check` into CI before v1 is "done".

### Phase 2: Operational refinement
- Owner tools/adapters for additional structured trees; filters and richer remediation; OPTIONAL snapshot export (only if a real consumer needs it); a cache ONLY if benchmarks justify it and it cannot affect correctness.

### Phase 3: Deliberate scope expansion
- Evaluate roadmaps/walkthroughs for actual lifecycle semantics; add a tree only when it has a real owner, a closed native status contract, a history contract, and an exhaustive mapping. Revisit a persisted snapshot only for a demonstrated non-CLI consumer.

## 14. Next step

Revised to reconcile the external review set; `Status: to-review`. Next: additional model review (the maintainer will circulate this revised spec), reconcile, then `/plan-review` and HUMAN APPROVAL before authoring any IPD Set. Do NOT begin an IPD until approved. Phase 0 (contracts + fixtures) is the first execution step once approved.

## Workflow history
- 2026-08-08 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted the attention-registry and cross-tree-status spec to Status: to-review, grounded in research survey bv6n38; queued for external review by gpt-5.6 and Gemini.
- 2026-08-08 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVISED to reconcile the external review set (gpt56/gemini31pro/sonnet5 assessments + reconciliation b1msgn). Adopted: on-demand ephemeral view (no committed registry in v1), five attention classes (ready/active/blocked/done/parked), read-only aw attention with per-tree owner writes (new aw specs), pure/exhaustive non-inferring mapping, typed gate fields, spec lifecycle draft->reviewed->approved->implementing->implemented (+deferred/parked/superseded; canonical demoted to a separate field), fail-closed scanning, tree policy inventory, versioned JSON + byte determinism, and a Phase-0-contracts-first plan. Renamed the noun to attention VIEW. Held for further model review.

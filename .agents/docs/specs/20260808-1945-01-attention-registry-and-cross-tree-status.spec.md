# Spec: attention registry and cross-tree status model (`aw attention`)

- Date: 2026-08-08
- Status: to-review (2026-08-08; drafted by opencode, awaiting external model review by gpt-5.6 and Gemini, then human approval). Design rationale + functional contract; a follow-on IPD Set implements it. Open questions in Section 12.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Grounding: research survey `bv6n38` (`.agents/docs/research/20260808-attention-registry-cross-tree-status-and-whatnext-00-bv6n38-attention-registry-cross-tree-status-and-whatnext.survey.md`).
- Relation to prior specs: builds on the artifact-organization line (`20260730-2152-01`, D123; `20260808-0004-01`, D124) and reuses `agent_workflows/artifact_core.py`. It does NOT replace the per-tree lifecycles (plans, research, prompts, comms); it adds a cross-tree ATTENTION layer above them.

## 1. One-line summary

A deterministic, stdlib-only tool (`aw attention`) that scours the standardized `.agents/` artifact trees, maps each artifact's native status onto a small tree-agnostic ATTENTION class, and maintains a committed registry (`.agents/ATTENTION.md` + `.agents/ATTENTION.json`) of what needs attention, what is in flight, what is done, and what is parked; plus write verbs that update an artifact's status and append its history atomically, so `/whatnext` and CI READ the registry instead of re-deriving state at runtime.

## 2. Problem / motivation

The repo already has a mature, machine-legible state model, but it is applied UNEVENLY, and the one workflow that answers "what needs attention?" (`/whatnext`) re-derives that answer at runtime by having the LLM read raw files, directories, git, and TODO.md every single invocation. Concretely (survey `bv6n38` Sections 1-2):

- **Uneven state.** `plans/`, `prompts/`, `comms/`, and `research/` have machine-legible state (directory disposition and/or a tool-owned status enum + a committed INDEX). `specs/`, `walkthroughs/`, and `roadmaps/` do NOT: specs carry a free-form prose `- Status:` bullet, no history section, no manifest. Specs are the worst offender that matters, because specs routinely describe UNBUILT or DEFERRED work (external-delivery, clean-delta, pip/PyPI). A deferred spec is invisible to `/whatnext` today unless a human transcribed it into TODO.md, a pending plan, or a comms message. That "someone has to remember" bridge is fragile and is exactly what silently rotted the two artifact-organization specs into reading like unbuilt proposals after they shipped.
- **Runtime re-derivation is costly and non-deterministic.** `/whatnext` Step 1 walks an explicit list of raw sources each run (plans dir, prompts dir, comms headers, TODO.md, DECISIONS/CHANGELOG tails, chat, and a catch-all "use judgment"). Most of that answer is a PURE FUNCTION of on-disk state, yet it is recomputed by the model, at token cost that scales with corpus size, every time - and it structurally never scans specs/research/roadmaps/walkthroughs at all.

The fix the maintainer identified: standardize status/filenames/locations; let a cheap deterministic tool scour the landscape ONCE and emit a registry of what needs attention; let the SAME tool WRITE status transitions and history so the registry stays true by construction; and make `/whatnext` a thin READER of the registry.

## 3. Goals (each testable)

- G1 `[Must]` Define a small, tree-agnostic ATTENTION-CLASS vocabulary and a pure mapping from each tree's native status to a class, WITHOUT forcing one status enum onto trees that have their own (plans, research).
- G2 `[Must]` Standardize and REQUIRE a machine-legible status on trees that lack one (specs first), plus an appended `## Workflow history` convention, lifted from the proven plans model.
- G3 `[Must]` Provide `aw attention` (READ): a deterministic scanner that regenerates a committed registry (`.agents/ATTENTION.md` human view + `.agents/ATTENTION.json` machine view) grouped by attention class, with a `--check` drift gate (CI-wireable) and a `--agent` machine-readable mode, reusing the existing `Drift`/`render_agent_drift`/`drift_exit_code` convention.
- G4 `[Must]` Provide write verbs (`aw attention set` / `aw attention note`) that update an artifact's status and append a dated history line atomically and self-recordingly, then refresh the registry.
- G5 `[Must]` Rewire `/whatnext` to READ the registry as its primary source and escalate to deep reading only for the specific flagged items, cutting token cost and closing the specs/research/roadmaps blind spot.
- G6 `[Must]` Reuse `agent_workflows/artifact_core.py` primitives; add zero runtime dependencies; Python 3.9 compatible; ship in the importable package so it reaches every install as `aw attention` and `python -m agent_workflows attention`.
- G7 `[Should]` Design the FULL cross-tree vision (all doc trees + write verbs) as the north star, but scope the FIRST build phase to: specs standardization, the scanner + registry over the already-structured trees plus specs, and whatnext-as-reader. Later phases: walkthroughs/roadmaps adoption and the full write-verb surface.
- G8 `[Must]` Never break existing citation paths or existing per-tree tooling (plans/research/prompts/comms lifecycles and their INDEX `--check` gates remain intact).

## 4. Non-goals

- NOT replacing the per-tree lifecycles or their enums. Plans keep directory disposition + readiness; research keeps intake/active/reference/archive; comms keep the ack enum. The registry sits ABOVE them.
- NOT moving specs into disposition subdirectories in v1 (rejected: breaks every existing `YYYYMMDD-HHMM-NN` citation path for only ~8 files; see OQ6). Specs stay flat with a required status field.
- NOT a daemon, a watch process, or a background service. `aw attention` is a run-on-demand / run-in-CI command, like `aw plans index`.
- NOT a task manager or issue tracker. It reflects state that already lives in the artifacts + TODO.md; it does not invent work items.
- NOT replacing TODO.md. TODO.md remains the human backlog for un-artifacted ideas; the registry surfaces artifacted work and links gated items back to their TODO/decision.
- NOT auto-committing on the user's behalf beyond what a verb explicitly does (writes are explicit; commits follow the repo's path-scoped, never-push contract).

## 5. Users / actors and scenarios

- **`/whatnext` (primary consumer).** Reads `.agents/ATTENTION.json`, presents the needs-attention and in-flight items cheaply, escalates to reading only the flagged artifacts. Scenario: "what needs attention?" answered from the registry in a handful of tokens instead of a full-corpus scour.
- **A human maintainer.** Reads `.agents/ATTENTION.md` for a grouped board; runs `aw attention set <spec> implemented` when a spec ships; trusts `--check` in CI to fail if the registry drifts from disk.
- **An executing agent.** After finishing work, runs `aw attention set`/`note` to record the transition + history, keeping the registry true without hand-editing prose.
- **CI.** Runs `aw attention --check` (and per-tree INDEX `--check`) to gate that on-disk status + the registry agree.

## 6. The attention-class model (G1) - the load-bearing design

Each tree keeps its NATIVE status. The registry defines a pure function `class_of(tree, native_status) -> AttentionClass`. Proposed classes (OQ1 refines the exact set/names):

- `needs-attention` - work is defined but not moving and something is required to advance it. Examples: spec `approved`-but-not-implemented; spec/plan `draft`/`to-review`/`reviewed`; research `intake`; any artifact explicitly `deferred` WITH an open gate.
- `in-flight` - actively being worked. Examples: plan `approved`/`auto-approved` that is under execution; research `active`.
- `done` - terminal-success; no attention needed. Examples: plan `executed`; spec `implemented`/`canonical`; research `reference`.
- `parked` - deliberately not active; kept for the record. Examples: plan `superseded`/`not-executed`; research `archive`; spec `superseded`; a `deferred` item whose gate is a deliberate decision (not awaiting action).

Rationale: this preserves every existing enum and tool while giving ONE scanner a uniform answer. The mapping table is small, pure, and lives in one module (candidate: extend `artifact_core.py` or a new `attention.py`). A `deferred`/gated artifact SHOULD additionally cite its gate (OQ4) so the registry renders the blocker and `/whatnext` can prioritize.

## 7. Standardized status + history contract (G2)

- **Specs (v1):** REQUIRE a front-matter `- Status:` drawn from a closed spec enum: `draft -> reviewed -> approved -> implemented`, plus terminal `superseded` and the standing `deferred` (which MUST carry a gate, OQ4). Replace the current free-form prose values (`DRAFT`, `canonical`, `approved`, `APPROVED ... Go`, `draft (evidence-gated)`, hand-written `Implemented`) by normalizing them to the enum. `canonical` reference specs map to `implemented` (or a distinct `canonical` value - OQ1).
- **`## Workflow history`:** every spec (and every tree the registry writes to) gains an appended `## Workflow history` section, one dated line per touch (`- YYYY-MM-DD /<workflow> (<agent/model>): <what>`), lifted verbatim from the plans convention.
- **Tool-owned trees (plans/research):** NO new field. The registry reads their existing status; the mapping (Section 6) does the rest.

## 8. Functional design (G3, G4)

### 8.1 `aw attention` (READ / regenerate)

- Scans the standardized trees via `artifact_core.iter_scan_files` (SCAN_ROOTS already covers `.agents/plans` and `.agents/docs`; prompts/comms added as needed), reads each artifact's native status (front-matter or, for plans, disposition + readiness), maps to an attention class, and regenerates:
  - `.agents/ATTENTION.json` - the machine view: every artifact with `{path, tree, native_status, class, id, gate?, last_history_date}`.
  - `.agents/ATTENTION.md` - the human board: grouped by class (needs-attention first), bounded hot-window per group with a "and N more" overflow (mirrors the plans/research INDEX.md bounding), gated items showing their blocker.
- `--check` mode: recompute the registry in memory, diff against the committed files, and emit `Drift` records via `render_agent_drift`; exit `drift_exit_code` (0 clean / 1 drift). Also flags contract violations (a spec missing a required Status, an unknown status value, a `deferred` without a gate).
- `--agent` mode: machine-readable stdout (tab-separated), matching the sanitizer/`--check` house style.
- Deterministic and pure: same disk -> same registry bytes (so `--check` is stable and CI-wireable).

### 8.2 `aw attention set <artifact> <status>` and `aw attention note <artifact> <text>` (WRITE)

- `set`: validate the target status against the artifact's tree enum; rewrite the front-matter status via `atomic_write`; append a `## Workflow history` line; refresh the registry. For a tool-owned tree (plans/research), DELEGATE to that tree's owning verb rather than editing directly (OQ7), or refuse and point at the owning verb.
- `note`: append a `## Workflow history` line only (no status change); refresh the registry.
- Both are explicit, self-recording, and leave a path-scoped-committable change (the tool does not commit; it follows the repo contract that the agent/human commits path-scoped and never pushes).

### 8.3 `/whatnext` integration (G5)

- Step 1 gains a FIRST source: read `.agents/ATTENTION.json` (cheap, deterministic) and present needs-attention + in-flight. Keep the existing sources as FALLBACK/RECONCILE (comms inbox, chat, git WIP) for things the registry cannot know (un-artifacted ideas still live in TODO.md; the registry links artifacted gated items to their TODO line).
- Net effect: the token-heavy full-corpus scour is replaced by a registry read plus targeted escalation.

## 9. Requirements

### Functional (MUST unless noted)
- F1 A pure `class_of(tree, native_status)` mapping covering every current native status of every in-scope tree; unknown status -> a `contract-violation` drift, never a silent drop.
- F2 `aw attention` regenerates `.agents/ATTENTION.json` + `.agents/ATTENTION.md` deterministically.
- F3 `aw attention --check` exits nonzero on ANY of: registry-vs-disk drift, a required Status missing, an unknown status value, a `deferred` artifact lacking a gate.
- F4 `aw attention --agent` prints tab-separated machine records.
- F5 `aw attention set` updates status + appends history + refreshes registry atomically; validates against the tree enum; delegates or refuses for tool-owned trees (OQ7).
- F6 `aw attention note` appends history + refreshes registry.
- F7 Specs REQUIRE a closed-enum `- Status:` and a `## Workflow history` section; a migration normalizes the existing ~8 specs' prose statuses to the enum and adds the history section (SHOULD, one-time).
- F8 `/whatnext` reads the registry first (SHOULD in v1 wording; MUST once the registry exists).

### Non-functional (MUST)
- N1 Stdlib only; zero runtime deps (D46); Python 3.9 compatible.
- N2 Ships in the importable `agent_workflows/` package as `aw attention` + `python -m agent_workflows attention`; NOT a per-target workflow `tools/` script.
- N3 Reuses `artifact_core` (`iter_scan_files`, `Drift`/`render_agent_drift`/`drift_exit_code`, id6, `atomic_write`, `git_mv`); no fork of those primitives.
- N4 Name is `aw attention` (NOT `aw status`, which already exists as the installer-status verb, cli.py:144).
- N5 `--check` is deterministic and stable across runs on unchanged disk.
- N6 No em/en dashes in authored Markdown/code per repo contract.

## 10. Acceptance criteria

- A1 Given the current repo, `aw attention` writes a registry whose needs-attention group INCLUDES the three deferred specs (external-delivery, clean-delta, pip/PyPI-upload) with their gates, and whose done group includes the two implemented artifact-org specs. (Proves the specs blind spot is closed.)
- A2 `aw attention --check` exits 0 immediately after a regenerate, and exits nonzero after any hand-edit to a status or the registry. (Proves drift detection.)
- A3 `aw attention set <a-spec> implemented` flips its status, appends a dated `## Workflow history` line, and a following `--check` is clean. (Proves the writer keeps the registry true.)
- A4 A spec with no `- Status:` (or an unknown value, or a `deferred` with no gate) makes `--check` fail with a `contract-violation` record naming the file. (Proves the contract is enforced.)
- A5 The existing `aw plans index --check` and `aw research index --check` still pass unchanged (no regression to per-tree tooling).
- A6 `/whatnext` produces its board from `.agents/ATTENTION.json` and only reads the specific flagged artifacts thereafter. (Proves the cost/coverage win.)
- A7 Full `unittest` suite green; new unit tests cover the mapping table, the scanner, `--check`, and the write verbs.

## 11. Constraints and dependencies

- Depends on `artifact_core.py` (D123) and the per-tree status conventions (plans D52/D65; research contract). Depends on the existing CLI wiring pattern (two edit points in `cli.py`: `_build_parser` + `_dispatch`; a new `agent_workflows/attention.py` module with `run(args) -> int`).
- The registry file location `.agents/ATTENTION.*` must be scaffolded by the installer for target repos (like the plans/research INDEX homes) - a small setup-artifacts addition (OQ3 may make it per-tree).
- The spec migration (F7) touches ~8 spec files once; low churn, no citation-path change (specs stay flat).

## 12. Risks and open questions

- OQ1 The exact attention-class enum and the full per-tree (native status -> class) mapping table. Also: does `canonical` (reference specs like ipd-spec) map to `done`/`implemented` or get its own value?
- OQ2 Keep each tree's native status field and standardize only the MAPPING (leaning yes), or introduce one unified `Status:` field name/format everywhere? (Leaning: native fields + standardized mapping + require-the-field on trees that lack one.)
- OQ3 One registry file `.agents/ATTENTION.*`, or per-tree registries plus a roll-up? Trade-off: token locality for `/whatnext` vs a single source. (Leaning: one roll-up file, since the whole point is one cheap read.)
- OQ4 How a `deferred`/gated artifact expresses its gate: a front-matter `Blocked-by:` / `Gate:` field citing a TODO line or `Dnn`, so the registry renders the blocker. Required for `deferred`.
- OQ5 Is the registry REQUIRED-in-sync (like INDEX `--check`, committed and CI-gated) or advisory? (Leaning: required-in-sync, committed, `--check` in CI.)
- OQ6 Specs flat-with-Status (leaning yes; only ~8 files) vs disposition subdirs (rejected: breaks citation paths). Confirm.
- OQ7 The write verbs' interaction with tool-owned trees: does `aw attention set` DELEGATE to `aw plans`/`aw research`, or is it read-only for those trees and write-only for the new ones (specs/roadmaps/walkthroughs)? (Leaning: read-only for tool-owned trees, with a pointer to the owning verb; write for the newly-standardized trees.)
- OQ8 Should walkthroughs (narrative records of executed work) even have an attention status, or are they always `done` by nature and thus excluded from the needs-attention computation? (Leaning: excluded/always-done; included in the registry only as provenance links.)
- OQ9 Migration ordering vs the specs-status standardization: does F7 (normalize the 8 specs) land in the same phase as the scanner, or as a preceding phase? (Leaning: same first phase, since the scanner needs specs to be legible.)

## 13. Out-of-scope / future (phasing, G7)

- **Phase 1 (this spec's first build):** specs status+history standardization + one-time normalization; `agent_workflows/attention.py` scanner + `.agents/ATTENTION.*` registry + `--check` + `--agent` over the already-structured trees (plans/research/prompts/comms) plus specs; `/whatnext` reads the registry.
- **Phase 2:** the full write-verb surface (`set`/`note`) including delegation to tool-owned trees; CI wiring of `aw attention --check`.
- **Phase 3:** walkthroughs and roadmaps adoption (status/history where meaningful) and any roll-up refinements.

## 14. Next step

This spec is drafted to `Status: to-review` and paused. Next: external review by gpt-5.6 AND Gemini (an upload-ready review prompt accompanies this spec), reconcile the feedback (especially OQ1-OQ4, the load-bearing mapping + gate design), then `/plan-review` and HUMAN APPROVAL before authoring any IPD Set. Do NOT begin an IPD until this spec is approved.

## Workflow history
- 2026-08-08 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted the attention-registry and cross-tree-status spec to Status: to-review, grounded in research survey bv6n38; queued for external review by gpt-5.6 and Gemini.

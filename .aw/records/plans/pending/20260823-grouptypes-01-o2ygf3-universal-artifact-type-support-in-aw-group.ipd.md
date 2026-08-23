# IPD: Universal Artifact Type Support in aw group

- Date: 2026-08-23
- Kind: child
- Concern: CLI noun-verb grammar consistency across all tracked artifact types for 'aw group'.
- Scope: Extend 'aw group' to support all canonical artifact types (backlog, specs, prompts, roadmaps, walkthroughs) alongside plans and research.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-23
- Set: grouptypes
- Order: 1
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: o2ygf3

## Workflow history
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (scope corrected + OQ-02 resolved by human: grammar types + per-type handlers, comms excluded), PR-004 (corrected extraction approach: artifact_core already exists, parameterized engine required), PR-005 (sibling-collision note).

## Goal

Extend the `aw group` CLI command to support the grammar-carrying repository artifact types plus per-type handlers for the id6-less/free-form types (per OQ-02): `backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`, alongside the existing `plans` and `research`. `comms` is out of scope (message tree, not a grammar artifact). This enables operators and agents to reassign Set IDs, inject/update frontmatter `- Set:` values, rename files to reflect the new set, and update repository-wide inbound references via a parameterized per-type engine. Grouping is a Set operation: for a Set-less type the handler injects `- Set:` (OQ-01) or refuses cleanly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Generalized set-assignment and regrouping engine

- [ ] E-01 Generalize the group/set-assignment backend in `agent_workflows/` to support re-assigning Set IDs across the in-scope artifact types (see the Scope check below), validating the new Set ID syntax, updating the artifact's YAML frontmatter (`- Set: <new-set-id>`), calculating the target grammar filename, executing filesystem renames, and rewriting inbound reference links across all referencing markdown documents.
  - Note (verified): `agent_workflows/artifact_core.py` ALREADY exists and owns the shared primitives (`iter_scan_files`, `atomic_write`, `git_mv`, `find_dangling_citations`, id6/kebab helpers); its docstring deliberately scopes filename-grammar and reference-rewriting OUT of core, keeping them per-area. `plans_refs.run_set_assign` and `research_refs.run_set_assign` genuinely DIVERGE: plans edits in-file `- Set:`/`- Order:` frontmatter and rewrites three citation forms (full name + bare stem + range shorthand) via a clustered grammar (`clustered_name`); research encodes set/order in the FILENAME only (no frontmatter edit), requires `--date`, and rewrites only the full old-filename token. Therefore the generalization MUST be a PARAMETERIZED engine (inject the per-type name-builder, reference-rewriter, and metadata-writer) - NOT a straight copy-paste extraction into a new `generic_refs.py`. Prefer extending `artifact_core.py` for any newly-shared primitive; introduce a new module only if the shared surface genuinely has no home there.
  - Per-type handlers required (OQ-02, human-resolved scope): `backlog` reuses the id6/setid grammar + `- Set:` frontmatter path; `specs`/`prompts` need a handler for id6-less `YYYYMMDD-HHMM-NN-<slug>` names that injects/updates a `- Set:` frontmatter field (per OQ-01) and computes that type's own name form; `roadmaps`/`walkthroughs` are free-form and Set-less, so a group op injects `- Set:` per OQ-01 or refuses cleanly.
  - Depends on: none
  - Expected outcome: a universal set-assignment backend function safely updates Set IDs, frontmatter, filenames, and references for any artifact type.
  - Execution state: pending

### Material change 2: CLI router and backend registration

- [ ] E-02 Register `group` backend routes in `TYPE_BACKENDS` (`agent_workflows/artifact_types.py:72-93`) for each in-scope type resolved in OQ-02 (`backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`), each pointing at the parameterized engine from E-01 with that type's handler. The noun-verb parsers and `_nv_backend_args` already pass `--set`/`--order`/`--apply`/selector (`agent_workflows/cli.py:1662-1708,5002-5017`), so `aw group <type> <selector...> --set <new-setid> [--order <NN>] [--apply]` must execute cleanly without emitting `'group' is not supported for <type>`. For a Set-less free-form type, `group` must either inject `- Set:` per OQ-01 or refuse cleanly - never report a silent no-op as success.
  - Depends on: E-01
  - Expected outcome: `aw group <type>` works consistently for every in-scope artifact type in the noun-verb grammar (`comms` remains excluded).
  - Execution state: pending

### Material change 3: Comprehensive test suite and validation

- [ ] E-03 Author `tests/test_artifact_group.py` validating that `aw group` successfully re-groups artifacts across `backlog`, `specs`, `prompts`, `walkthroughs`, and `roadmaps` (testing dry-run preview, `--apply`, set ID collision resolution, frontmatter synchronization, and reference rewrites), including the OQ-01/OQ-02 edge cases: a Set-less type gets a `- Set:` field injected on group (or the op refuses cleanly with a non-zero/clear message if the project decides the type has no Set semantics - assert whichever behavior E-01/E-02 implement, and assert it is NOT a silent success), and existing `plans`/`research` group behavior is unchanged (regression). Verify the full test suite passes with `pytest -n auto`.
  - Depends on: E-01, E-02
  - Expected outcome: all artifact types are covered with falsifiable unit and integration tests for set assignment.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_types.py` defines `ARTIFACT_TYPES = ("plans", "specs", "prompts", "research", "backlog", "walkthroughs", "roadmaps", "comms")`.
- `TYPE_BACKENDS` in `agent_workflows/artifact_types.py` currently maps `group` only for `plans` and `research`.
- When an unsupported type is passed to `aw group <type>`, `_run_noun_verb` in `agent_workflows/cli.py` prints `'group' is not yet wired / not supported for <type>` and exits with code 2.
- Set IDs cluster related artifacts within a domain. A Set collision (`check.setid-collision`) occurs when two artifacts in different domains or files share an unintended Set ID; `aw group` resolves this by cleanly re-tagging and renaming the artifact.

## Findings

Running `aw group backlog <path> --set <set-id>` currently fails:
```text
% aw group backlog .aw/records/backlog/done/20260815-awphysical-01-u298fd-install-split-brain-guard.backlog.md --set u298fd
WARN           'group' is not supported for backlog.
```
Extending `aw group` ensures `aw doctor` remediation suggestions can be directly executed to resolve set collisions across all artifact types.

## Proposed changes (ordered, validatable)

1. Build a parameterized set-assignment engine (per-type name-builder, reference-rewriter, metadata-writer) reusing `artifact_core.py` primitives; do NOT copy-paste `plans_refs`/`research_refs` into a new `generic_refs.py` (they diverge - see E-01 note).
2. Register `group` in `TYPE_BACKENDS` for the in-scope artifact types in `agent_workflows/artifact_types.py` (per OQ-02).
3. Reuse the existing positional path / id6 selector handling in `_nv_backend_args` (`agent_workflows/cli.py:5002-5017`); confirm `--set`/`--order`/`--apply` already reach the backend (they do, `cli.py:1662-1708`).
4. Add comprehensive test suite in `tests/test_artifact_group.py`, including Set-less edge cases and a `plans`/`research` regression.

## Deferred / out of scope (with reason)

- Modifying `aw rename` is covered in sibling IPD `20260823-renametypes-01-53yczi-universal-artifact-type-support-in-aw-rename.ipd.md`.

## Cross-plan dependency (sibling collision)

This plan, its rename sibling (`53yczi`), and the auto-index plan (`hszr72`) all edit the SAME files: `agent_workflows/plans_refs.py`, `agent_workflows/research_refs.py`, `agent_workflows/artifact_core.py`, and the `TYPE_BACKENDS` map in `agent_workflows/artifact_types.py`. The parameterized engine E-01 builds is shared with `rename`; land order matters.

- Whichever of `group`/`rename` lands first SHOULD build the shared parameterized engine; the second reuses it rather than re-extracting.
- The executor MUST re-read these files at execution time and reconcile with any already-executed sibling; the line references here may be stale.
- Preserve the auto-index hook if `hszr72` has already landed.

## Scope check

- Over-scope: none (scope resolved by OQ-02). `comms` is explicitly EXCLUDED (message tree, not a grammar artifact).
- Under-scope (now IN scope per OQ-02): each in-scope type needs a `TYPE_BACKENDS` `group` entry (`agent_workflows/artifact_types.py:72-93`) and a per-type handler in the parameterized engine (E-01). Note the grammar reality each handler must cover: `backlog` = existing id6/setid grammar + `- Set:` frontmatter; `specs`/`prompts` = id6-less `YYYYMMDD-HHMM-NN-<slug>` names with NO `Id`/`Set`/`Order` frontmatter (handler must inject `- Set:` per OQ-01 and compute the type's own name form); `walkthroughs` (`YYYYMMDD-HHMM-NN-<slug>-walkthrough.md`) and `roadmaps` (`YYYYMMDD-HHMM-NN-<slug>.md`) are free-form and Set-less (a group op injects `- Set:` per OQ-01, or refuses cleanly if the project decides the type has no Set semantics - never a silent no-op reported as success).

## Required tests / validation

- Unit tests in `tests/test_artifact_group.py` verifying preview and apply modes for each artifact type.
- Frontmatter `- Set:` modification verification.
- Reference rewrite tests ensuring references in other files are updated.
- Full test suite via `pytest -n auto`.

## Spec / documentation sync

- Update `AGENTS.md` and CLI `--help` text if required.

## Open questions

### OQ-01: How should artifacts without an existing Set field in frontmatter be updated?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: If an artifact lacks a `- Set:` field in its frontmatter, `aw group` should inject the `- Set: <new-setid>` field directly into the YAML frontmatter block.

### OQ-02: Which artifact types are actually in scope for `aw group` (set reassignment)?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): scope is grammar-carrying types PLUS per-type handlers for the id6-less/free-form types. Concretely: (a) `backlog` uses the existing id6/setid grammar + `- Set:` frontmatter path; (b) `specs` and `prompts` (id6-less `YYYYMMDD-HHMM-NN-<slug>` names, no Set frontmatter) require a distinct per-type handler that injects/updates a `- Set:` field and computes the type's own name form; (c) grouping is a Set operation, so any type WITHOUT a meaningful Set concept (currently `roadmaps`/`walkthroughs`, which are free-form and Set-less) is supported only insofar as a `- Set:` field is injected per OQ-01 - if the project decides a type has no Set semantics, `group` for it is a no-op/refusal, not a silent success. `comms` remains out of scope (message tree, not a grammar artifact). The engine MUST be parameterized per type (E-01).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit tests verify universal group backend modifies frontmatter, calculates target paths, renames files, and rewrites references.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: CLI integration tests verify `aw group <type>` succeeds for `backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`, `plans`, and `research`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: comprehensive test suite passes in `tests/test_artifact_group.py` and `pytest -n auto` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: single focused capability (universal artifact grouping/set assignment).

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved; OQ-02 resolved (human, 2026-08-23) - scope is grammar types plus per-type handlers for id6-less/free-form types, `comms` excluded.
2. Scope fence: Implement per-type artifact grouping for the OQ-02 in-scope types (`backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`) via a parameterized engine, without breaking existing `plans` and `research` group behaviors and without touching `comms`. A Set-less type injects `- Set:` (OQ-01) or refuses cleanly - never a silent no-op.
3. Honesty rule (hard MUST): When reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: On completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

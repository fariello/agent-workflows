# IPD: Universal Artifact Type Support in aw rename

- Date: 2026-08-23
- Kind: child
- Concern: CLI noun-verb grammar consistency across all tracked artifact types for 'aw rename'.
- Scope: Extend 'aw rename' to support all canonical artifact types (backlog, walkthroughs, specs, prompts, roadmaps, comms, releases) alongside plans and research.
- Status: executed
- Set: renametypes
- Order: 1
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: 53yczi

## Workflow history
- 2026-08-23 executed (aw set): status set to executed
- 2026-08-23 approved (aw set): status set to approved

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (scope corrected + OQ-02 resolved by human: grammar types + per-type handlers, comms excluded, releases gated on ARTIFACT_TYPES addition), PR-004 (corrected extraction approach: parameterized engine required), PR-005 (sibling-collision note), PR-006 (research --kind/--model facet gap noted).

## Goal

Extend the `aw rename` CLI command to support the grammar-carrying repository artifact types plus per-type handlers for the id6-less/free-form types (per OQ-02): `backlog`, `walkthroughs`, `specs`, `prompts`, `roadmaps` (and `releases` if it is first added to `ARTIFACT_TYPES`), alongside the existing `plans` and `research`. `comms` is out of scope (message tree, not a grammar artifact). This enables deterministic artifact renames, filename-grammar enforcement, frontmatter updates, and repo-wide reference rewrites via a parameterized per-type engine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Core reference-rewriting rename engine for all artifact types

- [x] E-01 Generalize the artifact rename engine in `agent_workflows/` to support renaming the in-scope artifact types (see the Scope check below) by path or id6 selector, parsing the frontmatter, computing the target grammar-conformant filename (`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`), executing the filesystem move, updating internal frontmatter, and rewriting citing documents across `.aw/`.
  - Note (verified): `agent_workflows/artifact_core.py` ALREADY exists and owns the shared primitives; its docstring deliberately keeps filename-grammar and reference-rewriting per-area. `plans_refs.run_mv` and `research_refs.run_mv` DIVERGE materially: plans reads `--id`/`--set`/`--order`/`--slug`, preserves order/date on a bare rename, and uses the clustered grammar; research's `run_mv` additionally reads `--kind` and `--model` (research filenames carry model+kind facets) and encodes set/order in the filename. Therefore generalize via a PARAMETERIZED engine (inject the per-type name-builder, reference-rewriter, and frontmatter handler) - NOT a straight copy-paste extraction into a new `generic_refs.py`. Prefer extending `artifact_core.py` for any newly-shared primitive; add a new module only if there is genuinely no home for the shared surface.
  - Per-type handlers required (OQ-02, human-resolved scope): `backlog` reuses the id6/setid grammar; `specs`/`prompts`/`walkthroughs`/`roadmaps` are id6-less/free-form (`YYYYMMDD-HHMM-NN-<slug>` names, no Id/Set frontmatter), so each needs a handler that parses the existing name, preserves or derives components, and fails clearly if the name is unparseable (OQ-01). Any type with extra facets (as research uses `--kind`/`--model`) needs those in its handler.
  - Depends on: none
  - Expected outcome: a universal rename backend function can safely rename an artifact of any valid type with full reference rewriting.
  - Execution state: performed

### Material change 2: CLI router and backend mapping

- [x] E-02 Register `rename` backend routes in `TYPE_BACKENDS` (`agent_workflows/artifact_types.py:72-93`) for each in-scope type from OQ-02 (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`), each pointing at the parameterized engine (E-01) with that type's handler, so `aw rename <type> <selector> [--slug <new-slug>] [--order <NN>] [--apply]` dispatches cleanly without emitting `'rename' is not supported for <type>`. `comms` is NOT registered (out of scope). If `releases` is to be supported, FIRST add `releases` to `ARTIFACT_TYPES` (`agent_workflows/artifact_types.py:12-21`) as an explicit sub-step, then register its `rename` route; if the executor cannot confirm `releases` is wanted, defer it and record the deferral. The noun-verb flags (`--slug`/`--order`/`--apply`/selector) are already registered (`agent_workflows/cli.py:1662-1708`); no new flag wiring is needed.
  - Depends on: E-01
  - Expected outcome: `aw rename <type>` works consistently for every in-scope artifact type in the noun-verb grammar (`comms` excluded; `releases` gated on the ARTIFACT_TYPES addition).
  - Execution state: performed

### Material change 3: Comprehensive test suite and validation

- [x] E-03 Author `tests/test_artifact_rename.py` validating that `aw rename` successfully renames artifacts across `backlog`, `walkthroughs`, `specs`, `prompts`, and `roadmaps` (testing dry-run preview, `--apply`, reference rewriting in referencing markdown docs, and error handling for missing files or invalid selectors), including the OQ-01/OQ-02 edge cases: an id6-less/free-form type renames by deriving components from its existing `YYYYMMDD-HHMM-NN-<slug>` name and fails clearly on an unparseable name; and existing `plans`/`research` rename behavior is unchanged (regression). If `releases` was added to `ARTIFACT_TYPES` in E-02, cover it too. Verify the full test suite passes with `pytest -n auto`.
  - Depends on: E-01, E-02
  - Expected outcome: all artifact types are covered with falsifiable unit and integration tests.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_types.py` defines `ARTIFACT_TYPES = ("plans", "specs", "prompts", "research", "backlog", "walkthroughs", "roadmaps", "comms")`.
- `TYPE_BACKENDS` in `agent_workflows/artifact_types.py` currently maps `rename` only for `plans` and `research`.
- When an unsupported type is passed to `aw rename <type>`, `_run_noun_verb` in `agent_workflows/cli.py` prints `'rename' is not yet wired / not supported for <type>` and exits with code 2.
- Artifact naming grammar follows `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`. When renaming, inbound links in other markdown files should be updated to maintain hyperlink integrity across the repo.

## Findings

Running `aw rename walkthroughs <path>` currently fails:
```text
% aw rename walkthroughs .aw/records/walkthroughs/20260821-awoptimize-rescope-walkthrough.walkthrough.md
WARN           'rename' is not supported for walkthroughs.
```
Similarly, running `aw rename backlog <path>` is rejected by the CLI router.
Extending `aw rename` ensures `aw doctor` remediation suggestions can be directly executed by operators and agents.

## Proposed changes (ordered, validatable)

1. Build a parameterized rename engine (per-type name-builder, reference-rewriter, frontmatter handler) reusing `artifact_core.py` primitives; do NOT copy-paste `plans_refs`/`research_refs` into a new `generic_refs.py` (they diverge - see E-01 note).
2. Register `rename` in `TYPE_BACKENDS` for the in-scope artifact types in `agent_workflows/artifact_types.py` (per OQ-02); add `releases` to `ARTIFACT_TYPES` first if it is to be a target.
3. Reuse the existing positional path / id6 selector handling in `_nv_backend_args` (`agent_workflows/cli.py:5002-5017`); confirm `--slug`/`--order`/`--apply` already reach the backend (they do, `cli.py:1662-1708`).
4. Add comprehensive test suite in `tests/test_artifact_rename.py`, including free-form derive-from-name cases and a `plans`/`research` regression.

## Deferred / out of scope (with reason)

- Modifying `aw group` is covered in sibling IPD `20260823-grouptypes-01-o2ygf3-universal-artifact-type-support-in-aw-group.ipd.md`.

## Cross-plan dependency (sibling collision)

This plan, its group sibling (`o2ygf3`), and the auto-index plan (`hszr72`) all edit the SAME files: `agent_workflows/plans_refs.py`, `agent_workflows/research_refs.py`, `agent_workflows/artifact_core.py`, and the `TYPE_BACKENDS` map in `agent_workflows/artifact_types.py`. The parameterized engine E-01 builds is shared with `group`; land order matters.

- Whichever of `rename`/`group` lands first SHOULD build the shared parameterized engine; the second reuses it rather than re-extracting.
- The executor MUST re-read these files at execution time and reconcile with any already-executed sibling; the line references here may be stale.
- Preserve the auto-index hook if `hszr72` has already landed.

## Scope check

- Over-scope: none (scope resolved by OQ-02). `comms` is explicitly EXCLUDED (message tree, not a grammar artifact).
- Under-scope (now IN scope per OQ-02): (1) a `TYPE_BACKENDS` `rename` entry (`agent_workflows/artifact_types.py:72-93`) for each in-scope type pointing at the parameterized engine (E-01); (2) a per-type filename-grammar + frontmatter handler for the id6-less/free-form types (`specs`/`prompts`/`walkthroughs`/`roadmaps`) that derives/preserves components from the existing name (OQ-01) - note `research`'s `run_mv` reads extra facets `--kind`/`--model`, so any type with its own facets needs its own handler; (3) if `releases` is to be a target, an explicit step to add `releases` to `ARTIFACT_TYPES` (it currently is not). The uniform noun-verb parsers already register `--slug`/`--order`/`--apply`/selector (`agent_workflows/cli.py:1662-1708`), so no new flag wiring is needed for those.

## Required tests / validation

- Unit tests in `tests/test_artifact_rename.py` verifying preview and apply modes for each artifact type.
- Reference rewrite tests ensuring references in other files are updated.
- Full test suite via `pytest -n auto`.

## Spec / documentation sync

- Update `AGENTS.md` and CLI `--help` text if required.

## Open questions

### OQ-01: How should files without an Id or Set frontmatter be handled during rename?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: If an artifact lacks frontmatter Id/Set fields (e.g. a plain walkthrough or roadmap), the rename tool should preserve existing frontmatter or infer from existing filename, deriving missing components or prompting/failing if unparseable.

### OQ-02: Which artifact types are actually in scope for `aw rename`?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): scope is grammar-carrying types PLUS per-type handlers for the id6-less/free-form types. In scope: `backlog` (existing id6/setid grammar), `specs`/`prompts` (id6-less `YYYYMMDD-HHMM-NN-<slug>` names, no Id/Set frontmatter - need a per-type handler that derives components from the existing name per OQ-01), `walkthroughs` (`...-walkthrough.md`) and `roadmaps` (free-form, per-type handler). `comms` is EXCLUDED (message tree, not a grammar artifact). `releases`: its files DO carry Id/Set/Order but it is NOT in `ARTIFACT_TYPES` - support requires FIRST adding `releases` to `ARTIFACT_TYPES` (`agent_workflows/artifact_types.py:12-21`); this plan MUST add it as an explicit step, or the executor MUST confirm with the human whether `releases` is deferred. The engine MUST be parameterized per type (E-01).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: unit tests verify universal rename backend computes correct paths and rewrites inbound references across markdown files.
  - Observed evidence: `tests/test_artifact_rename.py` tests `test_rename_backlog_preview_and_apply`, `test_rename_specs_legacy_timestamp`, `test_rename_walkthroughs`, `test_rename_prompts`, `test_rename_roadmaps`, `test_rename_releases` pass cleanly.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: CLI integration tests verify `aw rename <type>` succeeds for `backlog`, `walkthroughs`, `specs`, `prompts`, `roadmaps`, `plans`, and `research`.
  - Observed evidence: `tests/test_artifact_rename.py` tests verify CLI dispatch and error handling for all artifact types.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: comprehensive test suite passes in `tests/test_artifact_rename.py` and `pytest -n auto` passes cleanly.
  - Observed evidence: `pytest -n auto` executed 2086 passed (1 skipped) in 155.02s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: single focused capability (universal artifact renaming).

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved; OQ-02 resolved (human, 2026-08-23) - scope is grammar types plus per-type handlers for id6-less/free-form types, `comms` excluded, `releases` gated on being added to `ARTIFACT_TYPES` first.
2. Scope fence: Implement per-type artifact rename for the OQ-02 in-scope types (`backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`; `releases` only after adding it to `ARTIFACT_TYPES`) via a parameterized engine, without breaking existing `plans` and `research` rename behaviors and without touching `comms`.
3. Honesty rule (hard MUST): When reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: On completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

# IPD: Universal Artifact Type Support in aw group

- Date: 2026-08-23
- Kind: child
- Concern: CLI noun-verb grammar consistency across all tracked artifact types for 'aw group'.
- Scope: Extend 'aw group' to support all canonical artifact types (backlog, specs, prompts, roadmaps, walkthroughs) alongside plans and research.
- Status: draft
- Set: grouptypes
- Order: 1
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: o2ygf3

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Extend the `aw group` CLI command to universally support all canonical repository artifact types (`backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`, `plans`, `research`), enabling operators and agents to reassign Set IDs, update frontmatter `- Set:` values, rename files to reflect the new set in the uniform naming grammar (`YYYYMMDD-<new-setid>-NN-<id6>-<slug>.<type>.md`), and update all repository-wide inbound references.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Generalized set-assignment and regrouping engine

- [ ] E-01 Generalize the group/set-assignment backend in `agent_workflows/` (extracting shared logic from `plans_refs.py` and `research_refs.py` into a unified `generic_refs.py` or `artifact_core.py` helper) to support re-assigning Set IDs across any artifact type, validating the new Set ID syntax, updating the artifact's YAML frontmatter (`- Set: <new-set-id>`), calculating the target grammar filename, executing filesystem renames, and rewriting inbound reference links across all referencing markdown documents.
  - Depends on: none
  - Expected outcome: a universal set-assignment backend function safely updates Set IDs, frontmatter, filenames, and references for any artifact type.
  - Execution state: pending

### Material change 2: CLI router and backend registration

- [ ] E-02 Update `agent_workflows/artifact_types.py` and `agent_workflows/cli.py` to register `group` backend routes for all artifact types in `TYPE_BACKENDS` (`backlog`, `specs`, `prompts`, `roadmaps`, `walkthroughs`), ensuring `aw group <type> <selector...> --set <new-setid> [--order <NN>] [--apply]` executes cleanly without raising `'group' is not supported for <type>`.
  - Depends on: E-01
  - Expected outcome: `aw group <type>` works consistently for every supported artifact type in the noun-verb grammar.
  - Execution state: pending

### Material change 3: Comprehensive test suite and validation

- [ ] E-03 Author `tests/test_artifact_group.py` validating that `aw group` successfully re-groups artifacts across `backlog`, `specs`, `prompts`, `walkthroughs`, and `roadmaps` (testing dry-run preview, `--apply`, set ID collision resolution, frontmatter synchronization, and reference rewrites), while verifying the full test suite passes with `pytest -n auto`.
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

1. Generalize `run_set_assign` reference rewriting to operate across all artifact types in `agent_workflows/`.
2. Register `group` in `TYPE_BACKENDS` for all canonical artifact types in `agent_workflows/artifact_types.py`.
3. Support positional path and id6 selectors in `_nv_backend_args` in `agent_workflows/cli.py`.
4. Add comprehensive test suite in `tests/test_artifact_group.py`.

## Deferred / out of scope (with reason)

- Modifying `aw rename` is covered in sibling IPD `20260823-renametypes-01-53yczi-universal-artifact-type-support-in-aw-rename.ipd.md`.

## Scope check

- Over-scope: none.
- Under-scope: none.

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

1. Open questions RESOLVED: OQ-01 resolved.
2. Scope fence: Implement universal artifact grouping without breaking existing `plans` and `research` group behaviors.
3. Honesty rule (hard MUST): When reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: On completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

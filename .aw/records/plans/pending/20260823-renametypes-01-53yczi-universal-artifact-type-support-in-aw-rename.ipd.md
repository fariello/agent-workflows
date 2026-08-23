# IPD: Universal Artifact Type Support in aw rename

- Date: 2026-08-23
- Kind: child
- Concern: CLI noun-verb grammar consistency across all tracked artifact types for 'aw rename'.
- Scope: Extend 'aw rename' to support all canonical artifact types (backlog, walkthroughs, specs, prompts, roadmaps, comms, releases) alongside plans and research.
- Status: draft
- Set: renametypes
- Order: 1
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: 53yczi

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Extend the `aw rename` CLI command to universally support all canonical repository artifact types (`backlog`, `walkthroughs`, `specs`, `prompts`, `roadmaps`, `comms`, `releases`, `plans`, `research`), enabling deterministic artifact renames, filename grammar enforcement, frontmatter updates, and repo-wide reference rewrites for any artifact type.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Core reference-rewriting rename engine for all artifact types

- [ ] E-01 Generalize the artifact rename engine in `agent_workflows/` (extracting shared logic from `plans_refs.py` and `research_refs.py` into a unified `generic_refs.py` or `artifact_core.py` helper) to support renaming any artifact type by path or id6 selector, parsing the frontmatter, computing the target grammar-conformant filename (`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`), executing the filesystem move, updating internal frontmatter, and rewriting citing documents across `.aw/`.
  - Depends on: none
  - Expected outcome: a universal rename backend function can safely rename an artifact of any valid type with full reference rewriting.
  - Execution state: pending

### Material change 2: CLI router and backend mapping

- [ ] E-02 Update `agent_workflows/artifact_types.py` and `agent_workflows/cli.py` to register `rename` backend routes for all artifact types in `TYPE_BACKENDS` (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `comms`, `releases`), allowing `aw rename <type> <selector> [--slug <new-slug>] [--order <NN>] [--apply]` to dispatch cleanly without throwing `'rename' is not supported for <type>`.
  - Depends on: E-01
  - Expected outcome: `aw rename <type>` works consistently for every supported artifact type in the noun-verb grammar.
  - Execution state: pending

### Material change 3: Comprehensive test suite and validation

- [ ] E-03 Author `tests/test_artifact_rename.py` validating that `aw rename` successfully renames artifacts across `backlog`, `walkthroughs`, `specs`, `prompts`, and `roadmaps` (testing dry-run preview, `--apply`, reference rewriting in referencing markdown docs, and error handling for missing files or invalid selectors), while verifying full test suite passes with `pytest -n auto`.
  - Depends on: E-01, E-02
  - Expected outcome: all artifact types are covered with falsifiable unit and integration tests.
  - Execution state: pending

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

1. Generalize `run_mv` reference rewriting to operate across all artifact types in `agent_workflows/`.
2. Register `rename` in `TYPE_BACKENDS` for all canonical artifact types in `agent_workflows/artifact_types.py`.
3. Support positional path and id6 selectors in `_nv_backend_args` in `agent_workflows/cli.py`.
4. Add comprehensive test suite in `tests/test_artifact_rename.py`.

## Deferred / out of scope (with reason)

- Modifying `aw group` is covered in sibling IPD `20260823-grouptypes-01-o2ygf3-universal-artifact-type-support-in-aw-group.ipd.md`.

## Scope check

- Over-scope: none.
- Under-scope: none.

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit tests verify universal rename backend computes correct paths and rewrites inbound references across markdown files.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: CLI integration tests verify `aw rename <type>` succeeds for `backlog`, `walkthroughs`, `specs`, `prompts`, `roadmaps`, `plans`, and `research`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: comprehensive test suite passes in `tests/test_artifact_rename.py` and `pytest -n auto` passes cleanly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: single focused capability (universal artifact renaming).

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved.
2. Scope fence: Implement universal artifact rename without breaking existing `plans` and `research` rename behaviors.
3. Honesty rule (hard MUST): When reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: On completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.

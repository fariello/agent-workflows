# IPD: verify and regression-test aw_layout_inventory walk honors gitignore

- Date: 2026-08-19
- Kind: child
- Concern: Backlog item ith2xd (medium) asks that the layout-inventory walk honor .gitignore so ignored subtrees such as node_modules are not descended into or hashed. The pruning code already exists in tools/awphysical/aw_layout_inventory.py (_ignored_dirs, _walk, and inventory wiring), but no direct regression test asserts it. Soft ordering dependency: Order 01 of this Set may relocate the module to agent_workflows/layout_inventory.py (leaving a tools/awphysical/aw_layout_inventory.py shim); the executor must import from wherever the module lives at execution time.
- Scope: Verify the existing gitignore-aware pruning behavior with a written probe, then add the missing regression test (tests/test_layout_inventory_gitignore.py) that asserts inventory / _walk skips an ignored subtree, and run the full serial suite. No re-implementation of pruning logic.
- Status: to-review
- Set: backlog-medhigh-260819
- Order: 7
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: m7e2g3

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body drafted from investigation of tools/awphysical/aw_layout_inventory.py and tests/.

## Goal

Close backlog item ith2xd by verifying that the layout-inventory walk already prunes gitignored directory subtrees (node_modules and similar) and by adding the missing direct regression test that proves the prune, so the guarantee is falsifiable and cannot silently regress.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Verify existing behavior and add the regression test

- [ ] E-01 Write and run a throwaway probe against the layout-inventory module (importing it from wherever it lives at execution time: `agent_workflows.layout_inventory` if Order 01 has landed, else `tools.awphysical.aw_layout_inventory`) that creates a temp git repo with a `.gitignore` listing `node_modules/`, populates a `node_modules/` subtree plus a tracked file, and confirms `_ignored_dirs(repo)` returns the ignored dir and that `inventory(...)` does not emit any item whose path is under `node_modules`.
  - Depends on: none
  - Expected outcome: The probe run confirms _ignored_dirs contains "node_modules" and no inventory item path descends into node_modules; the pre-existing pruning behavior is observed to be correct as claimed.
  - Execution state: pending

- [ ] E-02 Add `tests/test_layout_inventory_gitignore.py` codifying the probe as a unittest (temp git repo, .gitignore with node_modules/, tracked and ignored content), asserting both `_ignored_dirs(repo)` includes the ignored subtree and `inventory(...)` yields no item under node_modules, importing the module from wherever it lives at execution time; then run the full serial test suite and close backlog item ith2xd.
  - Depends on: none
  - Expected outcome: New test file exists and passes; full serial suite passes; backlog item ith2xd is moved to done via `aw backlog set`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Inventory tests instantiate a temp git repo with `git init` + `git config` and drive the public API via `inv_mod._default_roots(self.repo)` then `inv_mod.inventory(self.repo, roots, False)` (see tests/test_awphysical_migration.py:112 and tests/test_acceptance_matrix.py:382). The new test should follow this temp-repo-plus-inventory pattern.
- The module is imported today as `from tools.awphysical import aw_layout_inventory as inv_mod` (tests/test_awphysical_migration.py:22). Order 01 of this Set may relocate it to `agent_workflows/layout_inventory.py` behind a shim, so the executor must import from wherever the module resolves at execution time.
- Existing node_modules references in tests/test_installer.py concern `.gitignore` file CONTENT preservation (e.g. tests/test_installer.py:1104, 1527), not the inventory walk prune; they are unrelated to this guarantee.

## Findings

- Pruning helper: `_ignored_dirs(repo)` at tools/awphysical/aw_layout_inventory.py:436 runs `git ls-files --others --ignored --exclude-standard --directory -z` and returns repo-relative POSIX dir paths (trailing slash stripped) so whole ignored subtrees can be pruned without hashing their files.
- Walk prune: `_walk(root, ignored_dirs=..., repo=...)` at tools/awphysical/aw_layout_inventory.py:460 filters `dirnames` in place, dropping `.git` and any dir whose repo-relative path is in `ignored_dirs` (tools/awphysical/aw_layout_inventory.py:484-486), so `os.walk` never descends into node_modules and it is never yielded.
- Wiring: `inventory(...)` computes `ignored_dirs = _ignored_dirs(repo)` (tools/awphysical/aw_layout_inventory.py:499) and passes it to `_walk(root, ignored_dirs=ignored_dirs, repo=repo)` (tools/awphysical/aw_layout_inventory.py:527). The implementation is present and correct as described in the backlog item.
- Test gap: a search of tests/ for node_modules combined with aw_layout_inventory / layout_inventory found NO test asserting the walk prunes an ignored subtree. The node_modules hits are all in tests/test_installer.py (gitignore content), and the inventory-calling tests (tests/test_awphysical_migration.py, tests/test_acceptance_matrix.py) never seed an ignored subtree nor assert its absence. The regression guarantee is therefore currently unprotected.

## Proposed changes (ordered, validatable)

1. E-01: Confirm current behavior with a throwaway probe (temp git repo, .gitignore node_modules/, populated ignored subtree) verifying `_ignored_dirs` and `inventory` prune node_modules. No source change.
2. E-02: Add `tests/test_layout_inventory_gitignore.py` that codifies the probe as a permanent unittest, run the full serial suite, and close backlog ith2xd. No source change to the inventory module.

## Deferred / out of scope (with reason)

- Any change to the pruning logic in aw_layout_inventory.py: out of scope; the code is already implemented and correct. This Order is verify-plus-test only.
- Relocating the module to agent_workflows/layout_inventory.py: out of scope; that is Order 01 of this Set. This Order only adapts its import to whichever location is live at execution time.

## Scope check

- Over-scope: none.
- Under-scope: none. Verifying the behavior and adding the single missing regression test fully satisfies backlog item ith2xd.

## Required tests / validation

- New test: `tests/test_layout_inventory_gitignore.py` asserts (a) `_ignored_dirs(repo)` includes the seeded ignored directory and (b) `inventory(repo, roots, False)` emits no item whose path is under node_modules.
- Full serial test suite is run and passes; actual runner output is pasted into the Observed evidence fields.
- Backlog item ith2xd is set to done and its closure recorded.

## Spec / documentation sync

- N/A: this Order adds a regression test for behavior already documented in the module docstrings (tools/awphysical/aw_layout_inventory.py:436, :460). No spec or user-facing doc change is required.

## Open questions

### OQ-01: Which import path is live at execution time?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: The executor imports the module from wherever it resolves at execution time: `agent_workflows.layout_inventory` if Order 01 of this Set has landed the relocation, else `tools.awphysical.aw_layout_inventory`. Non-blocking because both expose the same `_ignored_dirs`, `_walk`, `inventory`, and `_default_roots` symbols.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Probe output showing `_ignored_dirs(repo)` contains the seeded ignored directory (node_modules) and that no `inventory(...)` item path is under node_modules against a temp repo whose .gitignore lists node_modules/.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `tests/test_layout_inventory_gitignore.py` exists; pasted full-serial test-suite output showing the new test and the whole suite passing; confirmation (command output) that backlog item ith2xd is now done.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is verify-plus-test only and makes no change to the inventory module. On execution, follow the agent execution contract: commit only the files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste actual test-runner output as evidence rather than claiming success. Do not mark the plan done or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every V-item is verified with concrete pasted evidence; otherwise stop and report.

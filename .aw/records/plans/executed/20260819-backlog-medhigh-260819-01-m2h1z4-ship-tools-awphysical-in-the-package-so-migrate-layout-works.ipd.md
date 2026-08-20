# IPD: ship tools.awphysical in the package so migrate-layout works when pip-installed

- Date: 2026-08-19
- Concern: `agent_workflows.layout_migration` (line 30) and `cli.py` `_run_migrate_layout` (import at cli.py:4505 as of review; the plan targets this import by content, not line number) do `from tools.awphysical import aw_layout_inventory`, but the wheel ships `packages = ["agent_workflows"]` only (pyproject.toml:67) - `tools/` is not packaged and is not even a package (no `__init__.py`). So in a pip-installed repo `import agent_workflows.layout_migration` raises `ModuleNotFoundError: No module named 'tools'`, and `aw migrate-layout` + the install-time migration are DEAD. Proven in a clean installed wheel during the awuntrackedfix review. Backlog: revnjq.
- Scope: move `aw_layout_inventory.py` into the shipped `agent_workflows/` package and repoint the two shipped importers + the tests; keep a thin re-export shim at `tools/awphysical/aw_layout_inventory.py` for any source-side `tools.` caller. No behavior change to the inventory logic. Close backlog revnjq.
- Kind: child
- Status: executed
- Set: backlog-medhigh-260819
- Order: 1
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: m2h1z4

## Workflow history

- 2026-08-19 executed (agy_run.py Gemini 3.7 + opencode independent-validate): E-01..E-03 performed; agy moved layout_inventory into the package + repointed importers + repointed tests + added a packaging installed-wheel test + closed revnjq. opencode INDEPENDENTLY verified: imports clean, zero `from tools` in shipped importers, installed-wheel import of layout_migration has NO ModuleNotFoundError: tools, full serial suite 1181 passed 1 skipped, revnjq done. Committed by agy at 5ea4eef.
- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - move the unshipped tools.awphysical.aw_layout_inventory into the package so migrate-layout works when pip-installed (revnjq).
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-01-1 status->to-review, PR-01-2 stale cli.py:4461 anchor corrected to :4505 / find-by-content, PR-01-3 canonical serial-runner note. Anchors verified against the tree (layout_migration.py:30, cli.py:4505, pyproject.toml:67, tools/ no __init__, 5 symbols present). GO - PENDING HUMAN APPROVAL.

## Goal

Make `aw migrate-layout` and the install-time migration work in a pip-installed repo by shipping the inventory module inside the `agent_workflows` package instead of importing it from the unpackaged `tools/` dev tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: move + repoint

- [x] E-01 `git mv tools/awphysical/aw_layout_inventory.py agent_workflows/layout_inventory.py`. It is stdlib-only (imports argparse/hashlib/json/os/re/stat/shutil/subprocess/sys; verified), so it moves cleanly. Leave a thin back-compat shim at `tools/awphysical/aw_layout_inventory.py` whose entire body is `from agent_workflows.layout_inventory import *  # noqa` plus `from agent_workflows.layout_inventory import _default_roots, _walk, _ignored_dirs  # re-export privates used by callers/tests` so any source-side `tools.awphysical` caller still resolves.
  - Depends on: none
  - Expected outcome: `agent_workflows/layout_inventory.py` exists; `python3 -c "import agent_workflows.layout_inventory"` works; the `tools/awphysical/aw_layout_inventory.py` shim re-exports it.
  - Execution state: performed

- [x] E-02 Repoint the two SHIPPED importers to the package module: `agent_workflows/layout_migration.py:30` `from agent_workflows import layout_inventory as inv_mod` (was `from tools.awphysical import aw_layout_inventory as inv_mod`), and the `_run_migrate_layout` import in `agent_workflows/cli.py` (at cli.py:4505 as of review - locate it by matching the `from tools.awphysical import aw_layout_inventory` text rather than trusting the line number) likewise. Confirm the five used symbols still resolve (`_default_roots`, `inventory`, `build_migration_map`, `analyze_migration_risks`, `SCHEMA_VERSION`).
  - Depends on: E-01
  - Expected outcome: neither shipped module imports `tools`; `python3 -c "import agent_workflows.layout_migration, agent_workflows.cli"` works with no `tools` on the path.
  - Execution state: performed

### Task group 2: prove installed + tests

- [x] E-03 Update the tests that import from `tools.awphysical.aw_layout_inventory` (`tests/test_awphysical_migration.py:22`, `tests/test_acceptance_matrix.py:382`) to import from `agent_workflows.layout_inventory` (or keep via the shim - prefer the package path). Add an INSTALLED-WHEEL check (subprocess test or a documented manual V step with pasted output): build the wheel, pip install into a throwaway venv+repo, and run `aw migrate-layout` (or import `agent_workflows.layout_migration`) proving NO `ModuleNotFoundError: tools`. Run the FULL serial suite (canonical: `make test-serial` / `python3 -m unittest discover -s tests -t .`; `python3 -m pytest -p no:xdist` is equivalent only with the `.[test]` extra installed) and paste the tail. Close backlog revnjq to done.
  - Depends on: E-01,E-02
  - Expected outcome: tests import the package module; installed-wheel proof pasted (no tools error); full serial suite green; revnjq done.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `aw_layout_inventory.py` is stdlib-only and imported by exactly two SHIPPED files (layout_migration.py:30, cli.py:4461) + two tests; `tools/` has no `__init__.py` and is excluded from the wheel (pyproject.toml:67 `packages = ["agent_workflows"]`).
- Five symbols are consumed by layout_migration: `_default_roots`, `inventory`, `build_migration_map`, `analyze_migration_risks`, `SCHEMA_VERSION`.
- The sibling `aw_layout_compare`/`aw_layout_postcheck` (used only by tests) can stay in tools/ for now - only the inventory module is on the shipped import path (out of scope, noted).

## Findings

Proven in an installed wheel (awuntrackedfix review): `aw migrate-layout` raises `ModuleNotFoundError: No module named 'tools'`. Root cause is the unpackaged import path, not the logic. Moving the one module onto the shipped path fixes it with no behavior change.

## Proposed changes (ordered, validatable)

1. Move aw_layout_inventory.py into agent_workflows/ + shim.
2. Repoint the two shipped importers.
3. Repoint tests + installed-wheel proof + close revnjq.

## Deferred / out of scope (with reason)

- Moving aw_layout_compare / aw_layout_postcheck into the package: they are test-only, not on the shipped import path; deferred (a follow-on if a shipped verb ever needs them).
- The migrate-layout lane-rename wiring: already handled by awuntrackedfix (normalize-lanes); this Order only fixes the import.

## Scope check

- Over-scope: none.
- Under-scope: does not move the test-only sibling tools modules (not on the shipped path).

## Required tests / validation

Repointed unit tests + an installed-wheel import/run proof; full serial suite green.

## Spec / documentation sync

N/A: no spec pins the module location; it is an internal import path.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The fix (move onto the shipped path + shim) is unambiguous; no open decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `agent_workflows/layout_inventory.py` exists; `python3 -c "import agent_workflows.layout_inventory"` succeeds; the tools/ shim re-exports (import via the old path still works in a source checkout).
  - Observed evidence: `agent_workflows/layout_inventory.py` created via `git mv`; `python3 -c "import agent_workflows.layout_inventory; print(dir(agent_workflows.layout_inventory)[:3])"` printed `['Any', 'DEFAULT_ROOTS', 'Dict']`; `python3 -c "import tools.awphysical.aw_layout_inventory as old; print(dir(old)[:3])"` printed `['Any', 'DEFAULT_ROOTS', 'Dict']`; `python3 -m unittest tools.awphysical.test_awphysical_tools` passed 31/31 tests in 0.571s.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `rg "from tools" agent_workflows/layout_migration.py agent_workflows/cli.py` returns nothing for the inventory import; `python3 -c "import agent_workflows.layout_migration"` succeeds.
  - Observed evidence: `grep` / `rg` for `from tools` across `agent_workflows/layout_migration.py` and `agent_workflows/cli.py` returned 0 matches; all 5 consumed symbols (`_default_roots`, `inventory`, `build_migration_map`, `analyze_migration_risks`, `SCHEMA_VERSION`) resolved directly on `agent_workflows.layout_inventory`; `python3 -c "import agent_workflows.layout_migration, agent_workflows.cli"` succeeded with exit code 0.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: repointed tests pass; INSTALLED-WHEEL proof pasted (build + pip install + `aw migrate-layout`/import with NO `ModuleNotFoundError: tools`); full serial suite tail pasted; `aw backlog check` shows revnjq done.
  - Observed evidence: Repointed tests and packaging tests: `python3 -m unittest tests.test_packaging` passed 7/7 tests (including new `test_installed_wheel_migrate_layout_without_tools` and `assertIn('agent_workflows/layout_inventory.py', self.names)` in `test_wheel_contains_the_package`). Mutation probe verified RED on broken import (`AssertionError: 1 != 0 : importing layout_migration from installed wheel failed: ModuleNotFoundError: No module named 'tools'`) and GREEN when restored (`Ran 1 test in 2.234s OK`). Installed wheel in clean venv (`python3 -m venv` + `pip install`): `Import stdout: layout_migration imported successfully, inv_mod: <module 'agent_workflows.layout_inventory' from '/tmp/aw_test_venv_3ak544zq/lib/python3.14/site-packages/agent_workflows/layout_inventory.py'>`; `aw migrate-layout --help` exited 0 (NO `ModuleNotFoundError: tools`); `aw migrate-layout inventory --target-backend repository --json` exited 0 (`"valid": true`). Full serial suite tail: `Ran 1182 tests in 207.607s OK (skipped=1)`. Backlog revnjq transitioned to done via `aw backlog set --status done`; `aw backlog check` returned `aw backlog check: all backlog items conform.`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. Run the full serial suite and paste the actual runner output as V evidence; the installed-wheel proof is mandatory (this Order EXISTS because the bug only manifests when installed). On completion, lint --phase pre-transition while approved, then flip to executed + executed history line + git mv + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.

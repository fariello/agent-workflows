# IPD: Extract runipd core into the agent_workflows package unchanged

- Date: 2026-08-24
- Kind: child
- Concern: The runipd driver logic lives entirely in the standalone script `tools/ipdrunner/runipd.py` (1696 lines) with NO dependency on the `agent_workflows` package ("kept local so this standalone driver has no package dependency", runipd.py:61). To expose it as `aw oc runipd` and keep a single source of truth, its importable core must first move into the package unchanged. This is the foundation child of the awocrunner Set (orchestrator alkapp); the subcommand (child 02) and the compat shim (child 03) both depend on it.
- Scope: Move the runipd core into `agent_workflows/oc_runipd.py` as a behavior-preserving relocation (no redesign of logic, CLI, or output), and migrate its test suite (`tools/ipdrunner/test_runipd.py`, 795 lines) into the package test tree (`tests/test_oc_runipd.py`) updated to import from the package. The runbook/manifest data files under `tools/ipdrunner/` stay where they are (referenced by path). Child 01 of the awocrunner Set.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tools/ipdrunner/test_runipd.py
- Status: reviewed
- Set: awocrunner
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ckxgx4

## Workflow history
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (verbatim-diff proof in V-01, stdlib-only note), PR-002 (specific test import change + OQ-01 marked resolved)
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 01 of awocrunner Set (behavior-preserving core extraction + test migration).

## Goal

Relocate the OpenCode IPD runner's logic into `agent_workflows/oc_runipd.py` unchanged, with its tests migrated and passing, so downstream children can import a single packaged core rather than a checkout-only script.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Move the core into the package

- [ ] E-01 Create `agent_workflows/oc_runipd.py` containing the full runipd logic from `tools/ipdrunner/runipd.py` VERBATIM (all functions, constants, regexes, the `Palette`/`Heartbeat`/`render_event` streaming layer, `run_queue`, `dependency_status`, `initialize_run`, `main`, argparse setup). Preserve behavior exactly; do NOT redesign, rename functions, or change output. Keep the local ANSI/rendering code inline (no extraction into a shared renderer in this Set). The source imports are all stdlib (verified: argparse/contextlib/datetime/fcntl/hashlib/json/os/re/shlex/signal/subprocess/sys/tempfile/threading/time/pathlib/typing) with NO tools-local or relative imports, so the move requires zero import rewrites and imports cleanly as `agent_workflows.oc_runipd`, exposing `main(argv)`. The ONLY permissible content delta from the source is a module docstring/header adjustment; the executable code must be identical. (Note: the module inherits the source's Unix-only `fcntl` dependency; that is pre-existing behavior being preserved, not introduced here.)
  - Depends on: none
  - Expected outcome: `python3 -c "import agent_workflows.oc_runipd as m; m.main"` succeeds; the module contains the runner's full logic, byte-identical in its executable code to the source.
  - Execution state: pending

### Task group 2: Migrate the tests

- [ ] E-02 Create `tests/test_oc_runipd.py` from `tools/ipdrunner/test_runipd.py`, updating imports to target `agent_workflows.oc_runipd` (specifically: replace the `sys.path.insert(...)` + `import runipd as driver` block at `test_runipd.py:12-15` with `from agent_workflows import oc_runipd as driver`, dropping the now-unneeded tools-dir `sys.path` manipulation), and adjusting any remaining path setup so it runs under the package test tree. Keep every existing test case and assertion.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_oc_runipd.py` passes with the same coverage the standalone tests had.
  - Execution state: pending

### Task group 3: Remove the migrated standalone test

- [ ] E-03 Delete `tools/ipdrunner/test_runipd.py` now that its cases live in `tests/test_oc_runipd.py` (avoid two divergent copies). Confirm nothing else imports it.
  - Depends on: E-02
  - Expected outcome: no duplicate test module; `python3 -m pytest tests/` green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `tools/ipdrunner/runipd.py` is fully standalone (no `agent_workflows` import), which makes the move mechanical. Package modules live flat under `agent_workflows/`; `ipd_set_plan.py` (backs `aw ipd execute-set`) is the precedent for a packaged IPD-runner-adjacent module.
- Tests live in a flat `tests/` directory named `test_<area>.py`; run with `python3 -m pytest tests/`. `tests/support.py` holds shared helpers.
- The driver writes durable state under `.aw/records/runs/` and shells out to the `opencode` binary; both behaviors are preserved by the verbatim move.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit maintainer | runipd logic is checkout-only (`tools/ipdrunner/runipd.py`), unreachable by a pip-installed `aw`; it must be packaged to expose `aw oc runipd`. |
| F-02 | Med | QA | The 795-line test suite lives under `tools/`; it must move with the code and import the package to remain the single test surface. |

## Proposed changes (ordered, validatable)

1. Create `agent_workflows/oc_runipd.py` as a verbatim relocation of the runner core.
2. Create `tests/test_oc_runipd.py` from the standalone tests, importing the package.
3. Delete the now-duplicated `tools/ipdrunner/test_runipd.py`.

## Deferred / out of scope (with reason)

- The `aw oc` subcommand wiring is child 02; the `tools/ipdrunner/runipd.py` shim is child 03. This child only creates the packaged core and moves the tests, so nothing yet imports `oc_runipd` in production; that is expected and correct (children 02/03 wire it up).
- Extracting the render/palette layer into a shared renderer is explicitly deferred (Set-level decision) to keep this a behavior-preserving move.

## Scope check

- Over-scope: none. Only the new module and the test migration.
- Under-scope: none. This is the complete, self-contained foundation; wiring and shim are separate children by design.

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd.py` passes (migrated suite).
- `python3 -m pytest tests/` green overall (no regressions from the test move/delete).
- `python3 -c "import agent_workflows.oc_runipd"` succeeds.
- `pre-commit run --files agent_workflows/oc_runipd.py tests/test_oc_runipd.py`.

## Spec / documentation sync

- No user-facing doc change here (docs are child 04). If a developer doc lists package modules, it may be updated, but N/A otherwise.

## Open questions

### OQ-01: Module name `oc_runipd.py` vs generic `ipd_runner.py`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED as `oc_runipd.py`: the runner is OpenCode-specific (shells out to the `opencode` binary) and pairs with the `aw oc` group; a future Antigravity runner (`aw agy run`) gets its own module. Non-blocking; naming is confined to this child and children 02/03 import this name (consistently used across the Set's Scope-Paths).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -c "import agent_workflows.oc_runipd as m; print(bool(m.main))"` (True); AND a verbatim-move proof - a `diff tools/ipdrunner/runipd.py agent_workflows/oc_runipd.py` (or `git diff --no-index`) showing ONLY the expected header/docstring delta and NO change to any function body, constant, regex, or the argparse setup (proving the executable code is identical, not a paraphrase). A bare line-count match is NOT sufficient; the diff must be pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_oc_runipd.py` output showing all migrated tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/` output green with no reference to a missing `tools/ipdrunner/test_runipd.py`; a grep confirming nothing imports the deleted module.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (relocate the runner core into the package and move its tests), behavior-preserving, confined to the new module and the test migration.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved (`oc_runipd.py`). No blocking open question remains.
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `tests/test_oc_runipd.py`, and `tools/ipdrunner/test_runipd.py` (delete). Do NOT modify `tools/ipdrunner/runipd.py` yet (child 03), do NOT touch `cli.py` (child 02), and do NOT redesign logic or output. The move must be verbatim. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest ...`, the import check); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).

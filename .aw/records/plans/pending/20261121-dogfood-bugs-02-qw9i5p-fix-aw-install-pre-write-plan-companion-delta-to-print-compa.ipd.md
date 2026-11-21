# IPD: Fix aw install pre-write plan Companion Delta to print companion records/ path

- Date: 2026-11-21
- Kind: child
- Concern: `agent_workflows/install_wizard.py::render_pre_write_plan` prints the obsolete decoy path `<companion>/.aw/records` in `Companion Delta:` even though `mnsbzt` eliminated that decoy and stores companion records directly under `<companion>/records/`.
- Scope: Update `agent_workflows/install_wizard.py::render_pre_write_plan` to display the canonical `<companion>/records/` path and add a behavioral regression test.
- Scope-Paths: agent_workflows/install_wizard.py, tests/test_install_wizard_companion_preview.py, .aw/records/plans/pending/20261121-dogfood-bugs-02-qw9i5p-fix-aw-install-pre-write-plan-companion-delta-to-print-compa.ipd.md
- Item-Dependencies: executed:gftvh6
- Status: to-review
- Short-Description: Replace obsolete .aw/records decoy path with records/ in render_pre_write_plan Companion Delta
- Work-Kind: bug
- Priority: medium
- From-Backlog: 479wfb
- Blocks-Release: next
- Set: dogfood-bugs
- Order: 2
- Highest E allocated: 02
- Author: antigravity
- Id: qw9i5p

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-21 to-review (aw set): Review-ready child plans for dogfood-bugs
- 2026-11-21 draft (antigravity): created.

## Goal

Ensure the `Companion Delta:` line rendered by `agent_workflows/install_wizard.py::render_pre_write_plan` displays the real companion records directory (`<companion>/records/`) instead of the obsolete `<companion>/.aw/records` decoy path.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Align Companion Delta preview with canonical companion layout

- [ ] E-01 Update `agent_workflows/install_wizard.py::render_pre_write_plan` so the `Companion Delta:` line references `{comp_path}/records/` (and companion metadata/config) instead of `{comp_path}/.aw/records`.
  - Depends on: none
  - Expected outcome: For a `ProjectPolicy` with `records_backend == "companion"`, `render_pre_write_plan` outputs `{comp_path}/records/` in `Companion Delta:` and does not contain `/.aw/records`.
  - Execution state: pending

- [ ] E-02 Add behavioral tests in `tests/test_install_wizard_companion_preview.py` verifying `render_pre_write_plan` output for `public-target-private-companion` and checking existing install wizard tests for any stale `/.aw/records` assertions.
  - Depends on: E-01
  - Expected outcome: The new test passes and asserts `{comp_path}/records/` is present while `/.aw/records` is absent in `Companion Delta:`, and existing install wizard tests remain green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Executed plan `mnsbzt` (`companion-bugs` Order 01) established `<companion>/records/` as the sole companion records directory and removed creation of the empty `<companion>/.aw/records` decoy directory.
- `agent_workflows/install_wizard.py::render_pre_write_plan` already renders `- records : <companion>/records/ [companion] (companion-git)` in the `Resolved Physical Classes & Git Policies` section, but still hardcodes `{comp_path}/.aw/records and config created/updated.` in `Expected Deltas`.
- Depends on `gftvh6` (Order 01) because both plans edit `agent_workflows/install_wizard.py`.

## Findings

| ID | Severity | Area | Finding |
|---|---|---|---|
| DF-04 | Medium | `agent_workflows/install_wizard.py::render_pre_write_plan` | Observed during `aw install --no-interactive --dry-run` on `polyopen`: `Resolved Physical Classes` printed `<companion>/records/`, while `Expected Deltas` printed `Companion Delta: <companion>/.aw/records and config created/updated.`. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/install_wizard.py::render_pre_write_plan` (`E-01`): Change the `Companion Delta:` format string from `{comp_path}/.aw/records and config created/updated.` to `{comp_path}/records/ and companion config created/updated.`.
2. `tests/test_install_wizard_companion_preview.py` (`E-02`): Add behavioral assertions on `render_pre_write_plan` for companion and non-companion policies.

## Deferred / out of scope (with reason)

- Aligning `.aw/config/project.json` preview parity and target staging when `git_policies.config_project == "companion-git"` is already owned by backlog `o2or8a` and pending plan `ippuby`.
  - Carrier: ippuby

## Scope check

- Over-scope: none. Only the `Companion Delta:` path in `render_pre_write_plan` and its test are modified.
- Under-scope: none.

## Required tests / validation

- Run `python3 -m pytest tests/test_install_wizard_companion_preview.py tests/test_install_wizard*.py tests/test_companion_containment_and_storage.py`.
- Run `make typecheck` and `aw sanitize --agent`.

## Spec / documentation sync

N/A with reason: aligns the pre-write preview text with the companion layout contract already enforced by executed plan `mnsbzt`.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) (as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction) name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff -- agent_workflows/install_wizard.py` showing the updated `Companion Delta:` line using `{comp_path}/records/` with no `/.aw/records` reference.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste full output of `python3 -m pytest tests/test_install_wizard_companion_preview.py tests/test_install_wizard*.py tests/test_companion_containment_and_storage.py`, `make typecheck`, and `aw sanitize --agent` showing all tests pass, 0 mypy errors, and 0 leak findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must reach `approved` before execution. Execute inside an isolated worktree, commit only `Scope-Paths` files via `aw commit qw9i5p -- <paths>`, paste actual command output into each `V-*` Observed evidence block, and finalize via `aw ipd finalize qw9i5p`.

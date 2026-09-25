# IPD: Restore the upgrade-rehearsal safety tests and graduate the harness to an aw command

- Date: 2026-09-25
- Kind: child
- Concern: `tools/aw_upgrade_test.py` rehearses an upgrade in a sandbox copy of a real repo. Its four safety invariants (never write to the source, never push, never touch the real inventory, never delete anything but its own sandbox) lost their tests when `tests/test_aw_upgrade_test.py` was deleted in `19313eed`. The harness is also still a loose script rather than an `aw` command.
- Scope: IN: restore the invariant tests first (maintainer ruling 2026-09-25); then move the logic into the package behind a thin `tools/` shim, register `aw upgrade-test` with a `command_surface` declaration and the standard output modes, and default the sandbox root to a temp location rather than a maintainer path. OUT: new rehearsal features.
- Scope-Paths: tools/aw_upgrade_test.py, agent_workflows/upgrade_rehearsal.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- Set: upgrehearse
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8ud1is
- From-Backlog: u27q6g

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog u27q6g. Verified at HEAD: the tool exists (1370 lines) and `aw upgrade-test` does not; the deleted test file's 13 safety-invariant tests still pass against today's tool (run in place from tests/). Maintainer ruled 2026-09-25 to restore those tests.

## Goal

The rehearsal harness's safety guarantees are tested again, and it is a first-class, documented `aw` command.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: safety tests first

- [ ] E-01 Restore `tests/test_aw_upgrade_test.py` from `19313eed^`, keeping the four `SafetyInvariant*` classes and the helpers they need, and dropping the inspection/CLI classes that pin incidental behavior. Measured before authoring: the 13 safety tests pass against today's tool.
  - Depends on: none
  - Expected outcome: the four invariants are tested in the default suite.
  - Execution state: pending

### Task group 2: graduate

- [ ] E-02 Move the harness logic into `agent_workflows/upgrade_rehearsal.py`, leaving `tools/aw_upgrade_test.py` as a shim that calls it, and point the restored tests at the package module.
  - Depends on: E-01
  - Expected outcome: one implementation; the script still works.
  - Execution state: pending

- [ ] E-03 Register `aw upgrade-test` in `cli.py` with the same subcommands (`list`, `new`, `sandboxes`, `probe`, `env`, `clean`), add `CommandDeclaration`s for each leaf, and support `--agent`/`--json` via the standard output-mode contract.
  - Depends on: E-02
  - Expected outcome: `aw upgrade-test --help` works and `find_undeclared_leaves` stays empty.
  - Execution state: pending

- [ ] E-04 Default the sandbox root to a directory under the system temp dir (keeping the existing environment override) instead of any fixed maintainer path.
  - Depends on: E-02
  - Expected outcome: no maintainer-specific path in the default.
  - Execution state: pending

### Task group 3: verification

- [ ] E-05 Run the bare suite.
  - Depends on: E-03, E-04
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Every parser leaf needs a `CommandDeclaration` (see plan `0yrtne`, which restores the whole-CLI declaration test).
- The four invariants are behavior checks run in temp directories, so restoring them does not conflict with the standing rule against tests that pin code structure.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | tests | The four safety invariants are untested since `19313eed`. | `git log --diff-filter=D -- tests/test_aw_upgrade_test.py` -> `19313eed` |
| F-2 | INFO | tests | The restored invariant tests still pass against today's tool. | run in place from `tests/`: `13 passed` |
| F-3 | LOW | cli | No `aw upgrade-test` command exists. | `python3 -m agent_workflows upgrade-test` -> invalid choice |

## Proposed changes (ordered, validatable)

1. E-01: restore the safety-invariant tests.
2. E-02: move logic into the package.
3. E-03: register and declare the command.
4. E-04: portable sandbox root default.
5. E-05: bare suite.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: the inspection/CLI tests from the deleted file are not restored; they pinned incidental behavior.

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q`.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the rehearsal harness. If a user-facing docs page lists `aw` commands, add the new command there as part of E-03.

## Open questions

### OQ-01: Restore the tests before or after moving the code?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Before, resolved from the maintainer's 2026-09-25 ruling that the safety tests come back: restoring them first means the move in E-02 is checked by the very tests that guard it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the restored file's class list and `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff stat, `python3 tools/aw_upgrade_test.py --help`, and the restored tests passing against the package module.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m agent_workflows upgrade-test --help` and the `find_undeclared_leaves` one-liner printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the default resolution and `python3 -m agent_workflows sanitize --agent` showing no finding in the new files.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the tests guard the move; restoring them first is what makes the graduation safe.

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

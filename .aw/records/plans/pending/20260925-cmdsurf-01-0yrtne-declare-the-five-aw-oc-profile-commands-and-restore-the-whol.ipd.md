# IPD: Declare the five aw oc profile commands and restore the whole-CLI declaration test

- Date: 2026-09-25
- Kind: child
- Concern: The five `aw oc profile` leaves (`add`, `default`, `list`, `remove`, `show`) exist in the parser but have no `CommandDeclaration` in `command_surface.py`, so they carry no declared output-mode, mutation-gate or exit contract. The one test that proved every parser leaf is declared (`tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`) was deleted by the suite trim `19313eed`, so nothing catches this or the next undeclared command.
- Scope: IN: five declarations in `agent_workflows/command_surface.py`; one fast (not `slow`) behavior test asserting `command_surface.find_undeclared_leaves(cli._build_parser())` is empty; repoint the stale comments that still name the deleted `test_cli_conformance_matrix.py`. OUT: changing `oc profile` behavior; restoring any other deleted test.
- Scope-Paths: agent_workflows/command_surface.py, agent_workflows/cli.py, tests/test_command_surface_declarations.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: cmdsurf
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0yrtne
- From-Backlog: 4fe3al
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4fe3al. Verified at HEAD that the five leaves are still undeclared (`find_undeclared_leaves(_build_parser())` returns exactly them) and that the guard test was deleted in 19313eed. Maintainer ruled 2026-09-25 to restore the whole-CLI declaration test (it checks behavior, not source).

## Goal

Every `aw` command has a declared output and exit contract again, and a fast test fails the moment a new parser leaf ships without one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declarations

- [ ] E-01 Add `CommandDeclaration` entries for `oc profile list` and `oc profile show` in `command_surface.py`, modelled on the existing `oc update-models` entry: `command_class="read"`, `legacy_flags` equal to the flags `cli._build_parser` registers on `p_ocp_list`/`p_ocp_show` (read them from the parser, do not guess).
  - Depends on: none
  - Expected outcome: both leaves disappear from `find_undeclared_leaves(_build_parser())`.
  - Execution state: pending

- [ ] E-02 Add `CommandDeclaration` entries for `oc profile add`, `oc profile remove` and `oc profile default` as `command_class="mutation"`, with `mutation_gate` matching how each leaf actually confirms (drive each with `--help` and read its handler; do not assume), and `legacy_flags` taken from the parser.
  - Depends on: E-01
  - Expected outcome: `find_undeclared_leaves(_build_parser())` returns an empty set.
  - Execution state: pending

### Task group 2: guard test

- [ ] E-03 Recreate `tests/test_command_surface_declarations.py` with ONE fast test (no `slow` mark) asserting `find_undeclared_leaves(cli._build_parser()) == set()`, with a failure message that lists the undeclared leaves. Measured: building the parser and running the check takes about 0.4s, so it belongs in the default subset, unlike the deleted `slow`-marked version.
  - Depends on: E-02
  - Expected outcome: the test passes, and FAILS when any one of the five new declarations is removed.
  - Execution state: pending

- [ ] E-04 Repoint the comments that still cite the deleted `tests/test_cli_conformance_matrix.py` (grep `test_cli_conformance_matrix` in `agent_workflows/cli.py` and `agent_workflows/command_surface.py`) at the restored test, and run the bare suite.
  - Depends on: E-03
  - Expected outcome: `grep -rn test_cli_conformance_matrix agent_workflows/` returns nothing; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Every parser leaf needs a `CommandDeclaration` (`command_surface.CommandDeclaration`); `find_undeclared_leaves` is the shipped detector.
- The maintainer's standing rule: tests that pin code STRUCTURE are removed. This test checks a behavioral property of the built parser (every reachable command has a declared contract), which is why it is restored and not treated as a structure pin.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `command_surface` | The five `oc profile` leaves are undeclared. | `find_undeclared_leaves(_build_parser())` -> `['oc profile add', 'oc profile default', 'oc profile list', 'oc profile remove', 'oc profile show']` |
| F-2 | MED | tests | The guard test was deleted, and no remaining test checks the whole CLI; only narrowed checks exist (`test_host_capability_extension.py`, `test_prompts_new.py`). | `git log --diff-filter=D -- tests/test_command_surface_declarations.py` -> `19313eed` |
| F-3 | LOW | comments | Comments in `cli.py` and `command_surface.py` still cite the deleted `test_cli_conformance_matrix.py`. | `grep -rn test_cli_conformance_matrix agent_workflows/` |

## Proposed changes (ordered, validatable)

1. E-01: declare the two read leaves.
2. E-02: declare the three mutation leaves.
3. E-03: restore the whole-CLI guard as a fast test.
4. E-04: fix stale comments; bare suite.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: other tests deleted by `19313eed` are not restored; each needs its own case, and this plan restores only the one the maintainer ruled on.

## Required tests / validation

- `python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q` plus the removal mutation in V-03.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: no spec describes the `oc profile` leaves' declarations; the declaration registry is itself the contract.

## Open questions

### OQ-01: Should the restored test be marked `slow` like the deleted one?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved from measurement: the check takes about 0.4s end to end, so it belongs in the default subset where it actually runs. The deleted version being `slow` is exactly why the regression went unnoticed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "from agent_workflows.cli import _build_parser; from agent_workflows.command_surface import find_undeclared_leaves; print(sorted(find_undeclared_leaves(_build_parser())))"` after this item, showing `list`/`show` absent; paste the two new declarations.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same one-liner printing `[]`; paste the three declarations and, for each, one line naming how its mutation gate was determined (the handler symbol read).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q` passing; then remove the `oc profile show` declaration IN THE WORKTREE, paste the same run FAILING with `oc profile show` named in the message, and restore it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the empty grep, then paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.

# IPD: Fix trailing newline inconsistency for project.json during framework install

- Date: 2026-10-17
- Kind: child
- Concern: `.aw/config/project.json` ends with a trailing newline or not depending on which install code path wrote it last, so a reinstall flips the file's final byte and produces spurious git diffs in a tracked, committed policy file.
- Scope: Make every framework-install and placement-switch writer of `.aw/config/project.json` (and the sibling `.aw/config/local.json` written by the same functions) emit exactly one trailing newline, and add behavioral tests that drive the writers and assert on the bytes on disk.
- Scope-Paths: agent_workflows/install_wizard.py, agent_workflows/placement_switch.py, tests/test_install_config_trailing_newline.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 4qu8zm
- Blocks-Release: next
- Set: 4qu8zm
- Order: 1
- Highest E allocated: 04
- Author: opencode claude opus
- Id: kb64ea

## Workflow history

- 2026-10-17 draft (opencode claude opus): created.
- 2026-10-17 to-review (opencode claude opus): authored from backlog 4qu8zm with findings, checklist, and validation.

## Goal

Every install-time write of `.aw/config/project.json` ends with exactly one `\n`, so running the installer twice (or an install followed by a placement switch) leaves the tracked file byte-identical when the policy content did not change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Writers

- [ ] E-01 In `install_wizard.persist_project_policy`, write a trailing `"\n"` after `json.dump(proj_schema.to_dict(), f, indent=2)` (the `.tmp_project.json` write) and after `json.dump(local_schema.to_dict(), f, indent=2)` (the `.tmp_local.json` write), before each `os.replace`.
  - Depends on: none
  - Expected outcome: both files written by `persist_project_policy` end in exactly one `\n`, matching `config.sync_cutovers_on_install`, which already writes `f.write("\n")`.
  - Execution state: pending
- [ ] E-02 In `placement_switch._write_atomic_json`, write a trailing `"\n"` after `json.dump(data, f, indent=2)`, so the project.json and local.json writes that go through it (the `new_proj_schema` and `new_local_schema` writes) match the records-backend rewrite path in the same module, which already appends `f.write("\n")`.
  - Depends on: none
  - Expected outcome: every file written through `_write_atomic_json` (project.json, local.json, journals, receipts) ends in exactly one `\n`; readers use `json.load`/`json.loads`, which accept trailing whitespace.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-03 Create `tests/test_install_config_trailing_newline.py` with tests that (a) call `persist_project_policy` on a fresh temp git repo (pattern from `tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation`) and assert `project.json` and `local.json` bytes end with `b"}\n"` and not `b"\n\n"`; (b) seed a `project.json` whose `cutovers` are already complete (so `sync_cutovers_on_install` does not rewrite), run `persist_project_policy` twice, and assert the second run leaves `project.json` byte-identical to the first and ending in one `\n`; (c) call `placement_switch._write_atomic_json` on a temp path and assert the bytes end in exactly one `\n` and round-trip through `json.loads`.
  - Depends on: E-01, E-02
  - Expected outcome: the new tests fail against the pre-fix code for (a)/(b)/(c) and pass after E-01/E-02.
  - Execution state: pending
- [ ] E-04 Run the new test file, the existing install and placement-switch test files, and the core suite.
  - Depends on: E-03
  - Expected outcome: all pass with no new failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Install writes are atomic temp-file plus `os.replace` (`install_wizard.persist_project_policy`, `config.sync_cutovers_on_install`, `placement_switch._write_atomic_json`); the fix keeps that pattern and only adds the newline inside the temp-file write.
- The repository's own committed `.aw/config/project.json` ends in `}\n` (checked with `od -c`), and `config.py` writes canonical config with `json.dumps(..., indent=2, sort_keys=True) + "\n"`, so trailing-newline is the established convention.
- Tests must exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no source-reading tests.
- Suite command: bare `python3 -m pytest` (core tier); narrowed runs by explicit path.

## Findings

| Writer | File(s) | Trailing newline today |
|---|---|---|
| `install_wizard.persist_project_policy` (`json.dump(proj_schema.to_dict(), f, indent=2)`) | project.json | no |
| `install_wizard.persist_project_policy` (`json.dump(local_schema.to_dict(), f, indent=2)`) | local.json | no |
| `config.sync_cutovers_on_install` (`f.write("\n")` after dump), only when `modified` | project.json | yes |
| `placement_switch._write_atomic_json` (used for `new_proj_schema` / `new_local_schema`) | project.json, local.json | no |
| `placement_switch` records-backend rewrite (`json.dump(new_proj_data, f, indent=2)` then `f.write("\n")`) | project.json, local.json | yes |

Mechanism: `persist_project_policy` writes project.json without a newline, then calls `config.sync_cutovers_on_install`, which rewrites it WITH a newline only when it stamps a missing cutover. A first install stamps cutovers (newline present); a reinstall finds cutovers already present, skips the rewrite, and leaves the newline-less file from `persist_project_policy`. The tracked file therefore toggles its final byte between installs.

## Proposed changes (ordered, validatable)

1. E-01: append `\n` in both `persist_project_policy` temp writes.
2. E-02: append `\n` in `placement_switch._write_atomic_json`.
3. E-03/E-04: behavioral tests and suite run.

## Deferred / out of scope (with reason)

- `install_history.py` snapshot write (`json.dump(snapshot, f, indent=2)`): an install-history record under durable state, not `project.json`; the backlog item is scoped to project.json, so it is left unchanged.
  - Carrier-Declined: install-history record under durable state; backlog item is scoped to project.json
- A shared JSON-write helper consolidating all writers: refactor beyond this bug's scope.
  - Carrier-Declined: architectural refactoring beyond this bug's focused scope

## Scope check

- Over-scope: E-02 also changes journal/receipt files written through `_write_atomic_json`; this is accepted because splitting the helper just for config files adds complexity, and all readers parse with `json` which ignores trailing whitespace. local.json is fixed alongside project.json because the same functions write it with the same defect.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_install_config_trailing_newline.py` passes (V-03).
- `python3 -m pytest tests/test_reinstall_preserves_config.py tests/test_placement_switch_execute.py tests/test_placement_switch_companion_execute.py tests/test_installer.py` passes (V-04).
- Bare `python3 -m pytest` core tier passes (V-04).

## Spec / documentation sync

N/A: no spec or user-facing doc describes the byte format of `project.json`; this restores the existing convention.

## Open questions

### OQ-01: Should local.json and placement-switch journals also get the newline?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. They are written by the same functions with the same defect, and the repository convention (`config.py` canonical write, `sync_cutovers_on_install`) is trailing newline; fixing only project.json would leave the same function inconsistent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/install_wizard.py` hunk showing a `\n` write after both `json.dump` calls in `persist_project_policy`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/placement_switch.py` hunk showing the `\n` write in `_write_atomic_json`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste pytest output for `tests/test_install_config_trailing_newline.py` showing all tests passed after the fix, plus pasted output of the same file run BEFORE applying E-01/E-02 (write the test first) showing at least one failure.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the `N passed` summary lines from the named existing test files and from the bare `python3 -m pytest` core run, with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit through `aw commit <plan> -- <Scope-Paths>`; never push. After every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the lifecycle tooling.

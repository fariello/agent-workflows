# IPD: Make the install wizard write project.json and local.json with a trailing newline so a no-change reinstall is byte-stable

- Date: 2026-10-17
- Kind: child
- Concern: A second `aw install . --preset private-target -y` with nothing changed still makes an installer commit, so `tests/test_install_report_truth.py::TestInstallReportTruth::test_second_install_nochange_leaves_clean_status_and_no_false_lines` fails on `assertNotIn("Changes committed:", res2.stdout)`. Root cause: `install_wizard.persist_project_policy` writes `.aw/config/project.json` (and `local.json`) with `json.dump(..., indent=2)` and NO trailing newline. On a fresh install, `config.sync_cutovers_on_install` stamps the missing cutovers and rewrites the file WITH `"\n"`, so the committed copy ends in a newline. On a reinstall every cutover already exists, so nothing is stamped and the newline-less wizard output survives. The result is a one-byte diff (`\ No newline at end of file`) that the installer then commits.
- Scope: IN: make `persist_project_policy` write both `project.json` and `local.json` with a trailing newline, matching `sync_cutovers_on_install`'s format; add a fast, non-slow regression test showing a repeated `persist_project_policy` plus `sync_cutovers_on_install` round leaves `project.json` byte-identical. OUT: changing the JSON layout (key order, indent) or any other installer writer; the install-history snapshot writer in `install_history.py` (not part of the committed diff measured below); the existing slow test's assertions (they are correct and are the acceptance check).
- Scope-Paths: agent_workflows/install_wizard.py, tests/test_reinstall_preserves_config.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: denczr
- Blocks-Release: next
- Set: denczr
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: gbnrdf

## Workflow history
- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed (review record `.aw/records/reviews/20261017-denczr-01-gbnrdf-make-the-install-wizard-write-project-json-and-local-json-wi.review.md`)

- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored review-ready from backlog denczr.

## Goal

Make a no-change reinstall leave `.aw/config/project.json` byte-identical, so the installer finds nothing to commit and does not print `Changes committed:`. This fixes backlog `denczr` and its failing test at the source. It does not touch the test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fix the writer

- [ ] E-01 In `agent_workflows/install_wizard.py` function `persist_project_policy`, after `json.dump(proj_schema.to_dict(), f, indent=2)` (the `.tmp_project.json` write) add `f.write("\n")`, and do the same after `json.dump(local_schema.to_dict(), f, indent=2)` (the `.tmp_local.json` write). This matches the `json.dump(data, f, indent=2)` then `f.write("\n")` pattern already used in `config.sync_cutovers_on_install`. Change nothing else in the function. This item runs AFTER E-02 on purpose: E-02's test is written and run red against the unmodified writer first, so no temporary revert of this fix is ever needed.
  - Depends on: E-02
  - Expected outcome: both files written by `persist_project_policy` end in exactly one `\n`, and their JSON content is unchanged.
  - Execution state: pending

### Task group 2: Regression coverage

- [ ] E-02 Add a test to `tests/test_reinstall_preserves_config.py` class `TestPersistProjectPolicyPreservation` (not marked slow, so it runs in the core tier). The test uses the class's `_init_repo` helper and a `private-target` `ProjectPolicy` with a temp `aw_home`, as the existing tests do. It calls `persist_project_policy(str(repo), policy, replace_config=False)` once, which runs the cutover stamp internally, and reads the bytes of `.aw/config/project.json` and `.aw/config/local.json`. Then it calls the function again with the same policy and asserts: (a) the bytes of both files are unchanged; (b) both files end with `b"\n"` and not `b"\n\n"`. Assertions are on the bytes written to disk; the test does not read source code. Write it BEFORE E-01, run it once against the unmodified `install_wizard.py`, and keep the failing output for V-02.
  - Depends on: none
  - Expected outcome: the new test fails before E-01 (the second-round `project.json` bytes lose the trailing newline, measured at review) and passes after it.
  - Execution state: pending

- [ ] E-03 Run the acceptance test and the surrounding suites: `python3 -m pytest -o addopts="" -q tests/test_install_report_truth.py` (slow module, includes the failing test from backlog `denczr`), `python3 -m pytest -o addopts="" -q tests/test_reinstall_preserves_config.py`, and the routine gate `python3 -m pytest`.
  - Depends on: E-01, E-02
  - Expected outcome: all three runs pass with E-01 applied, with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": the new test calls `persist_project_policy` and asserts on the bytes it wrote. It does not inspect source.
- `tests/test_install_report_truth.py` is `pytestmark = pytest.mark.slow`, so the routine core gate never runs the failing test. That explains how the regression shipped unnoticed, and it is why E-02 adds a non-slow test.
- Routine gate: bare `python3 -m pytest`; narrowed runs: `python3 -m pytest -o addopts="" <path>` (AGENTS.md repository development contract).
- Commits go through `aw commit <plan> -- <paths>`; never push.
- Existing format reference: `config.sync_cutovers_on_install` writes `json.dump(data, f, indent=2)` then `f.write("\n")` to `.tmp_project.json`; `config` module's other writer uses `json.dumps(normalize(config), indent=2, sort_keys=True) + "\n"`. A trailing newline is the repository norm for JSON files.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The test fails at the current tip. | `python3 -m pytest -o addopts="" tests/test_install_report_truth.py -q -x` in this worktree: `FAILED ...test_second_install_nochange_leaves_clean_status_and_no_false_lines`, `AssertionError: 'Changes committed:' unexpectedly found`, the second install output listing `[overwrite] .aw/config/project.json` and `Ready to commit framework sync changes: [modified ] .aw/config/project.json`. Result `1 failed, 2 passed in 21.34s`. |
| F2 | The only committed difference is the trailing newline. | Reproduced in a scratch repo with two `python3 -m agent_workflows install . --preset private-target -y --no-interactive` runs; `git show HEAD -- .aw/config/project.json` on the second installer commit shows `-}` / `+}` / `\ No newline at end of file`. |
| F3 | The wizard writes JSON without a trailing newline. | `install_wizard.persist_project_policy`: `json.dump(proj_schema.to_dict(), f, indent=2)` then `os.replace(tmp_proj, proj_json)`; same for `local_schema`. |
| F4 | The cutover stamp writes a newline but only when it changes something. | `config.sync_cutovers_on_install`: the write is under `if modified:` and ends `f.write("\n")`. On a fresh install all `KNOWN_FEATURE_CUTOVERS` are stamped (modified); on a reinstall they all exist (not modified). |
| F5 | The `[overwrite] .aw/config/project.json` line is also reported on reinstall. | F1 output. Once the bytes are identical, the overwrite is a no-op at the git level. The status line is reporting wording only, and the slow test does not assert on it. |
| F6 | The planned test discriminates. | Review probe in `/tmp/opencode`: two `persist_project_policy(..., replace_config=False)` calls on a fresh `git init` repo with a `private-target` policy and temp `aw_home`. Unmodified writer: `project.json` bytes differ between rounds (first ends `}\n` from the cutover stamp, second ends `}` with no newline), `local.json` equal but ends with no newline. With a trailing `\n` added to both writes: both files byte-equal across rounds and both end in a single `\n`. Also re-ran `tests/test_install_report_truth.py` at review: `1 failed, 2 passed`. |

## Proposed changes (ordered, validatable)

1. E-02: add a fast byte-stability regression test and run it red. Validated by V-02.
2. E-01: add the trailing newline to both wizard writes. Validated by V-01.
3. E-03: run the acceptance test, the module, and the routine gate, and prove the new test catches the bug. Validated by V-03.

## Deferred / out of scope (with reason)

- `install_history.py` writes its snapshot with `json.dump(snapshot, f, indent=2)` and no trailing newline. That file did not appear in the reinstall diff (F2), so it does not cause this bug. Changing it is a style fix outside this plan's scope.
  - Carrier-Declined: style-only fix outside scope; does not cause spurious reinstall diff
- The installer reports `[overwrite]` for a byte-identical rewrite (F5). That is wording only, and no test or the backlog item asks for a change, so it is left alone.
  - Carrier-Declined: reporting wording only; not requested by backlog item or tested

## Scope check

- Over-scope: none.
- Under-scope: none. F2 shows `project.json` is the only file in the spurious commit. `local.json` is gitignored and never committed, but it gets the same fix so the wizard has one consistent format; the change is one line.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_install_report_truth.py` reports zero failures, with `test_second_install_nochange_leaves_clean_status_and_no_false_lines` passing (V-03).
- `python3 -m pytest -o addopts="" -q tests/test_reinstall_preserves_config.py` passes, including the new test (V-02).
- The new test fails before E-01 is applied (V-02).
- Routine gate `python3 -m pytest` passes (V-03).

## Spec / documentation sync

N/A: no spec or user documentation describes the byte format of `project.json`. This is a bug fix that restores the behavior the existing test already specifies.

## Open questions

None. The root cause and fix come from reproducing the bug in this repository (F1 to F4). No decision needs the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- agent_workflows/install_wizard.py` showing exactly two added `f.write("\n")` lines, one after each `json.dump` in `persist_project_policy`, and no other change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_reinstall_preserves_config.py` showing the new test, which calls `persist_project_policy` twice and asserts byte equality and a single trailing `\n` for both files. Paste the actual failing output of the new test run against the unmodified `install_wizard.py` (before E-01), showing the byte-equality or trailing-newline assertion failing. Then paste the actual output of `python3 -m pytest -o addopts="" -q tests/test_reinstall_preserves_config.py` after E-01 with its `N passed` summary and zero failures.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual output of `python3 -m pytest -o addopts="" -v tests/test_install_report_truth.py` showing `test_second_install_nochange_leaves_clean_status_and_no_false_lines` PASSED and zero failed. Paste the `N passed` summary line of a bare `python3 -m pytest` and `echo "exit=$?"` showing 0. Paste `git diff --cached --name-only` at commit time listing only `agent_workflows/install_wizard.py`, `tests/test_reinstall_preserves_config.py`, and, if that commit also carries this plan's checklist updates, this plan file; any other path is a fail.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit gbnrdf -- agent_workflows/install_wizard.py tests/test_reinstall_preserves_config.py`, verify `git diff --cached --name-only` lists only your paths, never `git add -A`, and never push.
- Lifecycle: after every V-item reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.

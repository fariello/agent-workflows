# IPD: Verify the five aw oc profile leaves stay declared and the whole-CLI declaration test is enforced

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `vxqtqm` reports five `aw oc profile` parser leaves undeclared in `command_surface.COMMAND_INVENTORY` and a whole-CLI declaration test that fails only when run alone. That defect was already fixed by executed plan `0yrtne` (graduated from the duplicate backlog item `4fe3al`); this plan re-verifies the fix at execution HEAD and closes the duplicate with evidence.
- Scope: Verification of the existing declarations and the test's enforcement in the bare suite and in the CI `output-conformance` job. Code edits are permitted ONLY if a regression is measured, and only to the declarations in `agent_workflows/command_surface.py`.
- Scope-Paths: agent_workflows/command_surface.py, tests/test_command_surface_declarations.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: vxqtqm
- Set: vxqtqm
- Order: 1
- Highest E allocated: 03
- Author: opencode Claude Opus
- Id: 4mv9ul

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 4mv9ul verified (set vxqtqm, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/command_surface.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_command_surface_declarations.py: declared-but-unmodified (auto-acknowledged by aw agy run)] [Scope delta - no declared Scope-Paths were modified since the frozen base (2 declared path(s) unmodified; work may have landed before the begin baseline or not at all): agent_workflows/command_surface.py, tests/test_command_surface_declarations.py]
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: bars by named tests and node ids, not counts; collection under default addopts proven), PR-002 (LOW, fixed: execution contract and finalize ownership). F-1..F-3 re-measured at HEAD dbde69ccb. Record: .aw/records/reviews/20261011-vxqtqm-01-4mv9ul-verify-the-five-aw-oc-profile-leaves-stay-declared-and-the-w.review.md.
- 2026-10-12 draft (opencode Claude Opus): created.
- 2026-10-12 to-review (opencode Claude Opus): authored from backlog `vxqtqm`; found already fixed by executed plan `0yrtne`, so the plan is verification-only.

## Goal

Prove, with pasted output at execution HEAD, that the five `aw oc profile` leaves named by backlog `vxqtqm` (`list`, `show`, `add`, `remove`, `default`) are declared and that `tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves` passes alone, in the bare suite, and as the CI `output-conformance` step, so the item can close as a duplicate of `4fe3al`/`0yrtne` without new code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure the declarations and the test

- [x] E-01 Confirm each of the five leaves has a `CommandDeclaration` in `command_surface.COMMAND_INVENTORY` by running `python3 -c "from agent_workflows import command_surface as c; d={x.command for x in c.get_all_declarations()}; print(sorted(k for k in d if k.startswith('oc profile')))"` and recording the printed list. If any of the five is missing, restore it following the field judgements recorded in executed plan `0yrtne` (Findings F-7) and record the restoration.
  - Depends on: none
  - Expected outcome: printed list contains `oc profile add`, `oc profile default`, `oc profile list`, `oc profile remove`, `oc profile show`.
  - Execution state: performed

- [x] E-02 Run the whole-CLI declaration module ALONE: `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py -v`, and record the output.
  - Depends on: E-01
  - Expected outcome: `test_zero_undeclared_parser_leaves` and `test_zero_unreachable_command_declarations` both PASSED; zero undeclared leaves.
  - Execution state: performed

- [x] E-03 Confirm enforcement outside the isolated run: run the bare suite `python3 -m pytest` and record the summary line, and confirm `.github/workflows/tests.yml` job `output-conformance` step "Run the output-conformance harness" invokes `tests/test_command_surface_declarations.py` by running that step's command `python -m pytest tests/test_command_surface_declarations.py` locally.
  - Depends on: E-02
  - Expected outcome: in the bare suite, the module is COLLECTED under the default `addopts` (not deselected by the `slow`/`livecorpus` markers; shown with `python3 -m pytest --collect-only -q tests/test_command_surface_declarations.py`, which must list both tests), and no node id in `tests/test_command_surface_declarations.py` appears among the bare run's failures. Failures elsewhere in the suite are recorded by node id but are not this plan's bar. The CI step's command exits 0 with `test_zero_undeclared_parser_leaves` and `test_zero_unreachable_command_declarations` both passing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The command inventory is `agent_workflows/command_surface.py` (`COMMAND_INVENTORY`, `get_all_declarations`); the guard is `tests/test_command_surface_declarations.py` (`find_undeclared_leaves`).
- Repo contract: run the suite bare (`python3 -m pytest`); use `-o addopts=""` only to clear defaults for a narrowed run.
- Tests must exercise behavior (GUIDING_PRINCIPLES P16); this plan adds no tests.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-1 | HIGH | The defect is already fixed. Commit `f2cd41b19` "feat(cmdsurf): declare the five aw oc profile commands and restore whole-CLI declaration test (0yrtne)" added declarations for all five leaves (plus `oc profile validate-default`). | `git log -S'command="oc profile list"' -- agent_workflows/command_surface.py` returns `f2cd41b19`; plan `20260925-cmdsurf-01-0yrtne-...ipd.md` is in `executed/` with `- Status: executed`, `- From-Backlog: 4fe3al`. |
| F-2 | MED | `vxqtqm` duplicates `4fe3al` (`20260918-4fe3al-01-4fe3al-oc-profile-leaves-undeclared-command-surface.backlog.md`), which `0yrtne` graduated. | Both item titles describe the same five undeclared leaves. |
| F-3 | MED | The item's secondary concern (bare suite did not enforce the guarantee) was also addressed by `0yrtne`: its Goal requires the test to fail "in the bare suite AND in the CI job", and `.github/workflows/tests.yml` `output-conformance` now runs `tests/test_command_surface_declarations.py`. | At authoring HEAD `9e3b99850`: module alone `2 passed in 2.03s`; bare-defaults run of the module `2 passed in 2.17s`. |

## Proposed changes (ordered, validatable)

1. E-01: re-measure the five declarations.
2. E-02: run the declaration module alone.
3. E-03: run the bare suite and the CI step command.
No code change is proposed unless E-01 or E-02 measures a regression.

## Deferred / out of scope (with reason)

None. Backlog closure is handled by the lifecycle via `- From-Backlog: vxqtqm`, and any other undeclared leaf is caught by the existing guard test, so nothing is deferred.

## Scope check

- Over-scope: none.
- Under-scope: none; the item's two concerns (five leaves, enforcement) are each covered by E-01 and E-02/E-03.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py -v` (E-02).
- `python3 -m pytest` bare suite and `python -m pytest tests/test_command_surface_declarations.py` (E-03).

## Spec / documentation sync

N/A: no behavior or contract changes; verification only.

## Open questions

### OQ-01: Should this item close as a duplicate rather than via a plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The production contract requires a plan to graduate the item; a verification-only plan provides the cited evidence that the gate (`0yrtne`) holds at execution HEAD, which is cheaper than and equivalent to a duplicate closure.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted printed list of `oc profile` declarations containing all five leaves named by `vxqtqm`.
  - Observed evidence: Confirmed all five leaves plus `oc profile validate-default` are declared in `command_surface.COMMAND_INVENTORY`:
    ```
    $ python3 -c "from agent_workflows import command_surface as c; d={x.command for x in c.get_all_declarations()}; print(sorted(k for k in d if k.startswith('oc profile')))"
    ['oc profile add', 'oc profile default', 'oc profile list', 'oc profile remove', 'oc profile show', 'oc profile validate-default']
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `pytest -v` output showing `test_zero_undeclared_parser_leaves PASSED` and `test_zero_unreachable_command_declarations PASSED`, with exit code 0, re-derived at execution HEAD (the passing named tests are the bar, not the count).
  - Observed evidence: Executed isolated test module run; both tests passed with exit code 0:
    ```
    $ python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py -v
    ============================= test session starts ==============================
    collected 2 items

    tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves PASSED [ 50%]
    tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_unreachable_command_declarations PASSED [100%]

    ============================== 2 passed in 8.11s ===============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted `--collect-only` output listing both tests under default `addopts`; the pasted bare-suite summary line plus its failing node ids (if any), showing none from `tests/test_command_surface_declarations.py`; the pasted `sed -n` (or equivalent) excerpt of `.github/workflows/tests.yml`'s `output-conformance` step showing it runs that module; and the pasted output and exit code of that step's command run locally, both named tests passing.
  - Observed evidence: Confirmed collection under default addopts, clean bare suite run, and local CI command pass:
    1. Collect-only output:
    ```
    $ python3 -m pytest --collect-only tests/test_command_surface_declarations.py
    tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_unreachable_command_declarations
    tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves

    2 tests collected in 0.95s
    ```
    2. Bare suite summary line and failure check:
    ```
    $ python3 -m pytest
    7595 passed, 2 skipped, 3 warnings in 948.73s (0:15:48)
    ```
    Failing node ids: none (0 failures; none from tests/test_command_surface_declarations.py).

    3. CI workflow excerpt (.github/workflows/tests.yml lines 267-272):
    ```
    $ sed -n '267,272p' .github/workflows/tests.yml
          - name: Run the output-conformance harness (E-01 matrix + E-02 gates + E-03 docs)
            shell: bash
            run: |
              python -m pytest \
                tests/test_command_surface_declarations.py
    ```
    4. CI step command local execution:
    ```
    $ python -m pytest tests/test_command_surface_declarations.py; echo "EXIT_CODE=$?"
    ..                                                                       [100%]
    2 passed in 6.92s
    EXIT_CODE=0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit through `aw commit 4mv9ul -- <paths>` limited to the declared Scope-Paths (likely only this plan file, since no code change is expected); verify `git diff --cached --name-only` first, and never push. PASTE THE ACTUAL OUTPUT of every command the `V-*` items demand; never report a pass that was not run. If E-01 or E-02 measures a regression, the only permitted code edit is a restored declaration in `agent_workflows/command_surface.py` (using `0yrtne` F-7's field judgements); record it, and justify any other edited path at finalize with `--scope-reason`.

LIFECYCLE. The terminal move to `executed/` goes through the lifecycle tooling, never a hand `git mv`: in a managed lane the runner finalizes; when executing by hand, run `aw ipd finalize 4mv9ul`. Either way, only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with pasted evidence. Backlog `vxqtqm` then closes through the `- From-Backlog:` handoff as a duplicate of `4fe3al` (already `done`).

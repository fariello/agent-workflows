# IPD: Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

- Date: 2026-10-12
- Kind: child
- Concern: The production property "an `executed` plan stays a selectable queue entry, while only the deliberately retired (`superseded`, `not-executed`, by status or directory) are refused" has zero surviving test coverage since commit 19313eed deleted `tests/test_runner_item_dependencies.py`.
- Scope: Add one new behavioral test module that drives `runner_shared.manifest_entry_is_selectable` and, end to end, both hosts' `initialize_run` over a Set selector, asserting on real return values and the persisted queue. No production code changes.
- Scope-Paths: tests/test_manifest_entry_selectable.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: mv18lz
- Set: mv18lz
- Order: 1
- Highest E allocated: 04
- Author: OpenCode model=Claude
- Id: df486j

## Workflow history

- 2026-10-12 draft (OpenCode model=Claude): created.
- 2026-10-12 to-review (OpenCode model=Claude): authored review-ready plan graduating backlog mv18lz.

## Goal

Restore behavioral regression coverage for `runner_shared.manifest_entry_is_selectable` so that a mutation refusing `executed` (or status-less) entries, or admitting retired ones, turns the suite red. The coverage exercises the predicate directly and through the real selector-to-queue path (`expand_selectors` via `initialize_run`) on both hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Predicate-level behavioral table

- [ ] E-01 Create `tests/test_manifest_entry_selectable.py` with a table-driven test calling `runner_shared.manifest_entry_is_selectable` on: `{"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"}` -> True; status-less entry `{"file": "x.ipd.md"}` -> True; `{"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"}` -> True; `{"status": "superseded"}` -> False; `{"status": "not-executed"}` -> False; `{"status": "approved", "file": ".aw/records/plans/superseded/x.ipd.md"}` -> False (directory disagreement); same with `not-executed/` -> False; uppercase/whitespace status `" Superseded "` -> False; `None` and `{}` -> False.
  - Depends on: none
  - Expected outcome: The new module exists and its predicate test passes against current code.
  - Execution state: pending

### Task group 2: End-to-end queue behavior on both hosts

- [ ] E-02 In the same module, add a test that builds a temporary git repo with Set `demo` holding an `executed` plan (`executed/`, `Status: executed`), an `approved` dependent in `pending/` carrying `- Item-Dependencies: executed:<first-id6>`, and a `superseded` plan in `superseded/`; then, for each of `oc_runipd` and `agy_runipd`, calls `initialize_run` with selector `demo` (argparse.Namespace shaped like the deleted `_StartArgs` helper, `isolate_worktree=False`) and asserts from `load_state(run_dir)["queue"]`: the executed plan is PRESENT with `status == "executed"`, the dependent is `queued` and absent from `cascade_dependency_blocked(state)`, and the superseded plan is ABSENT.
  - Depends on: E-01
  - Expected outcome: The end-to-end test passes on both hosts against current code.
  - Execution state: pending

### Task group 3: Prove the coverage is load-bearing

- [ ] E-03 Run an in-memory mutation probe (monkeypatch only, no source edit): patch `runner_shared.manifest_entry_is_selectable` so it returns False for `status == "executed"`, run the new module, and confirm it fails; repeat with a mutant that admits `superseded`; confirm both mutants are killed. Revert nothing on disk because nothing on disk changes.
  - Depends on: E-02
  - Expected outcome: Both mutants produce failing tests in the new module; unmutated code passes.
  - Execution state: pending

### Task group 4: Regression

- [ ] E-04 Run the full fast suite bare (`python3 -m pytest`) and confirm no regressions; commit only `tests/test_manifest_entry_selectable.py` via `aw commit <plan> -- tests/test_manifest_entry_selectable.py`.
  - Depends on: E-03
  - Expected outcome: Suite green with the new tests included; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source. The deleted file also carried source-scanning helpers (`_code_only`, `_code_without_prose`); those are NOT restored.
- Both hosts share one definition of `expand_selectors` and `manifest_entry_is_selectable` in `agent_workflows/runner_shared.py`; host modules `oc_runipd.initialize_run` and `agy_runipd.initialize_run` are the end-to-end entry points. The deleted suite iterated `_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))`.
- `runner_shared.initial_queue_status` preserves `executed` via `TERMINAL_QUEUE_STATUSES` and maps `None` to `reviewed`; the docstring of `manifest_entry_is_selectable` names the deleted `InRunExecutedDependencyTests` as the pin for executed-row presence.
- Existing tests calling `initialize_run` with temp repos: `tests/test_typed_queue_entries.py`, `tests/test_runner_shared.py`; `tests/support.py` provides `REPO_ROOT`.
- Suite runs bare: `python3 -m pytest` (pyproject `addopts`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | No test references `manifest_entry_is_selectable` or `InRunExecutedDependencyTests`. | `grep -rn "manifest_entry_is_selectable\|InRunExecuted" tests` returns nothing. |
| F2 | The deleted test (`git show 19313eed^:tests/test_runner_item_dependencies.py`, class `InRunExecutedDependencyTests.test_in_run_executed`) drove `initialize_run` with Set selector `demo` on both drivers and asserted executed row present + dependent queued. | Read from git history. |
| F3 | Current predicate behavior verified interactively: executed -> True, status-less -> True, superseded -> False, retired directory -> False, None/{} -> False. | `python3 -c` probe in authoring session. |
| F4 | `expand_selectors` silently drops retired Set members (`filtered_out`) and only raises for an explicitly named single plan; a Set selector is therefore the right end-to-end probe. | `runner_shared.expand_selectors`, comment "A SET MEMBER is dropped SILENTLY". |

## Proposed changes (ordered, validatable)

1. Add `tests/test_manifest_entry_selectable.py` with the predicate table (E-01).
2. Add the two-host end-to-end queue test in the same module (E-02).
3. Demonstrate mutation kill (E-03), then full-suite regression and commit (E-04).

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted `tests/test_runner_item_dependencies.py` (typed edges, ordering, cascade): not part of backlog `mv18lz`, which names only the executed-entry selectability property.
- Restoring source-scanning guards from that file: prohibited by the no-code-pinning-tests rule.
- Explicit-plan refusal message of a retired named plan: already a distinct behavior; may be asserted incidentally but is not required.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog asks for behavioral coverage driving queue selection, which E-02 provides on both hosts, and E-03 proves the coverage kills the mutation the backlog measured.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_manifest_entry_selectable.py` passes (E-01, E-02).
- Monkeypatched mutants fail the module (E-03).
- Bare `python3 -m pytest` summary shows no failures (E-04).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes the test file. The predicate docstring cites the deleted test path; updating that docstring is production code and out of the declared Scope-Paths, so it is left as-is.

## Open questions

### OQ-01: Should the restored tests live in a recreated `tests/test_runner_item_dependencies.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. A new, narrowly named module keeps scope to this backlog item and avoids implying the rest of the deleted file was restored. The predicate docstring's stale path reference is cosmetic.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -q tests/test_manifest_entry_selectable.py -k predicate` showing the predicate test(s) passed, plus the diff of the table rows.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_manifest_entry_selectable.py` showing the end-to-end test passed for both `oc_runipd` and `agy_runipd` (subtests or parametrized ids), produced by `initialize_run` -> `runner_shared.expand_selectors` -> persisted `state.json` queue.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output for each mutant (executed refused; superseded admitted) showing at least one FAILED test in the new module, and pasted passing output with no mutant applied.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted final summary line of a bare `python3 -m pytest` run with 0 failed, and `git show --stat HEAD` showing only `tests/test_manifest_entry_selectable.py` changed (plus the plan lifecycle files).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_manifest_entry_selectable.py` through `aw commit`, never push. Move the plan to `executed/` via the tooled lifecycle (`aw ipd finalize`) only after `aw ipd lint --phase pre-transition` conforms and every V-item records pasted evidence with `Result: pass`.

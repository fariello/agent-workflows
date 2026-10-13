# IPD: Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

- Date: 2026-10-12
- Kind: child
- Concern: The production property "an `executed` plan stays a selectable queue entry, while only the deliberately retired (`superseded`, `not-executed`, by status or directory) are refused" has zero surviving test coverage since commit 19313eed deleted `tests/test_runner_item_dependencies.py`.
- Scope: Add one new behavioral test module that drives `runner_shared.manifest_entry_is_selectable` and, end to end, both hosts' `initialize_run` over a Set selector, asserting on real return values and the persisted queue. No production code changes.
- Scope-Paths: tests/test_manifest_entry_selectable.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: mv18lz
- Set: mv18lz
- Order: 1
- Highest E allocated: 04
- Author: OpenCode model=Claude
- Id: df486j

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: df486j verified (set mv18lz, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-12 draft (OpenCode model=Claude): created.
- 2026-10-12 to-review (OpenCode model=Claude): authored review-ready plan graduating backlog mv18lz.

## Goal

Restore behavioral regression coverage for `runner_shared.manifest_entry_is_selectable` so that a mutation refusing `executed` (or status-less) entries, or admitting retired ones, turns the suite red. The coverage exercises the predicate directly and through the real selector-to-queue path (`expand_selectors` via `initialize_run`) on both hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Predicate-level behavioral table

- [x] E-01 Create `tests/test_manifest_entry_selectable.py` with a table-driven test calling `runner_shared.manifest_entry_is_selectable` on: `{"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"}` -> True; status-less entry `{"file": "x.ipd.md"}` -> True; `{"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"}` -> True; `{"status": "superseded"}` -> False; `{"status": "not-executed"}` -> False; `{"status": "approved", "file": ".aw/records/plans/superseded/x.ipd.md"}` -> False (directory disagreement); same with `not-executed/` -> False; uppercase/whitespace status `" Superseded "` -> False; `None` and `{}` -> False.
  - Depends on: none
  - Expected outcome: The new module exists and its predicate test passes against current code.
  - Execution state: performed

### Task group 2: End-to-end queue behavior on both hosts

- [x] E-02 In the same module, add a test that builds a temporary git repo with Set `demo` holding an `executed` plan (`executed/`, `Status: executed`), an `approved` dependent in `pending/` carrying `- Item-Dependencies: executed:<first-id6>`, and a `superseded` plan in `superseded/`, plus a `.gitignore` of `.aw/records/runs/`, all committed. Build the plans with a fixture that passes the run structure preflight: reuse `_make_test_repo`, `_write_plan` and `_build_queue_for_selector` from `tests/test_typed_queue_entries.py` (import those three names only, never its `TestCase` classes, so they are not collected twice), or copy an equally conformant fixture. Do NOT reuse the deleted file's `_plan_text`/`_StartArgs` shape: its minimal plan now fails `initialize_run` with `[RUN-STRUCTURE-PREFLIGHT] ... violates IPD-M101: Concern: required field missing` (F5). Then, for each of `oc_runipd` and `agy_runipd` (as `subTest`s), build the queue through the host's real parser with `start demo --repo <repo> --prepare-only --unattended --run-id <unique>` and `initialize_run` (which is what `_build_queue_for_selector` does), and assert from the persisted `state.json` queue: the executed plan is PRESENT with `status == "executed"`, the dependent is `queued` and absent from `cascade_dependency_blocked(state)`, and the superseded plan is ABSENT.
  - Depends on: E-01
  - Expected outcome: The end-to-end test passes on both hosts against current code. At review a prototype of exactly this shape printed `oc {'aaaaaa': 'executed', 'bbbbbb': 'queued'} []` and the same for `agy`, `1 passed`.
  - Execution state: performed

### Task group 3: Prove the coverage is load-bearing

- [x] E-03 Run an in-memory mutation probe with no source edit: write two pytest plugins in an UNTRACKED scratch directory (for example the gitignored `.aw/state/`, never committed), each rebinding `runner_shared.manifest_entry_is_selectable` at import, one returning False for `status == "executed"` and one returning True for every non-empty entry (admits `superseded`). Run the new module once per plugin with `PYTHONPATH=<scratch>:. python3 -m pytest -o addopts="" -q -n0 -p <plugin> tests/test_manifest_entry_selectable.py` and confirm it fails. Rebinding the module attribute reaches the end-to-end path because `expand_selectors` looks the predicate up as a `runner_shared` global. Confirm each mutant is killed by the PREDICATE test AND, separately, by the END-TO-END test (run each with `-k` or by node id), so the queue-path coverage does not depend on the table.
  - Depends on: E-02
  - Expected outcome: Both mutants make the predicate test and the end-to-end test fail; unmutated code passes. At review the end-to-end prototype failed on both: the admitting mutant with `'cccccc' unexpectedly found`, the executed-refusing mutant with `KeyError: 'aaaaaa'`.
  - Execution state: performed

### Task group 4: Regression

- [x] E-04 Run the full fast suite bare (`python3 -m pytest`) and confirm no regressions; commit only `tests/test_manifest_entry_selectable.py` via `aw commit <plan> -- tests/test_manifest_entry_selectable.py`.
  - Depends on: E-03
  - Expected outcome: Suite green with the new tests included; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior, not code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source. The deleted file also carried source-scanning helpers (`_code_only`, `_code_without_prose`); those are NOT restored.
- Both hosts share one definition of `expand_selectors` and `manifest_entry_is_selectable` in `agent_workflows/runner_shared.py`; host modules `oc_runipd.initialize_run` and `agy_runipd.initialize_run` are the end-to-end entry points. The deleted suite iterated `_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))`.
- `runner_shared.initial_queue_status` preserves `executed` via `TERMINAL_QUEUE_STATUSES` and maps `None` to `reviewed`; the docstring of `manifest_entry_is_selectable` names the deleted `InRunExecutedDependencyTests` as the pin for executed-row presence.
- Existing tests calling `initialize_run` with temp repos: `tests/test_typed_queue_entries.py` (conformant `_write_plan`, `_make_test_repo`, and `_build_queue_for_selector`, which drives the real parser with `--prepare-only --unattended`), `tests/test_runner_shared.py`; `tests/support.py` provides `REPO_ROOT`.
- Suite runs bare: `python3 -m pytest` (pyproject `addopts`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | No test references `manifest_entry_is_selectable` or `InRunExecutedDependencyTests`. | `grep -rn "manifest_entry_is_selectable\|InRunExecuted" tests` returns nothing. |
| F2 | The deleted test (`git show 19313eed^:tests/test_runner_item_dependencies.py`, class `InRunExecutedDependencyTests.test_in_run_executed`) drove `initialize_run` with Set selector `demo` on both drivers and asserted executed row present + dependent queued. | Read from git history. |
| F3 | Current predicate behavior verified interactively: executed -> True, status-less -> True, superseded -> False, retired directory -> False, None/{} -> False. | `python3 -c` probe in authoring session. |
| F5 | The deleted test's fixture no longer reaches the queue: a minimal plan (no `Concern`, `Scope`, sections) built with `_plan_text` and driven through a hand-built `_StartArgs` namespace makes `initialize_run` raise in the structure preflight. The shipped conformant helpers in `tests/test_typed_queue_entries.py` with the real parser and `--prepare-only` work on both hosts. | Review run: `DriverError: [RUN-STRUCTURE-PREFLIGHT] ipd bbbbbb ... violates IPD-M101: Concern: required field missing`; with `_write_plan` + `_build_queue_for_selector`: `oc {'aaaaaa': 'executed', 'bbbbbb': 'queued'} []`, `agy` the same, `1 passed`. |
| F4 | `expand_selectors` silently drops retired Set members (`filtered_out`) and only raises for an explicitly named single plan; a Set selector is therefore the right end-to-end probe. | `runner_shared.expand_selectors`, comment "A SET MEMBER is dropped SILENTLY". |

## Proposed changes (ordered, validatable)

1. Add `tests/test_manifest_entry_selectable.py` with the predicate table (E-01).
2. Add the two-host end-to-end queue test in the same module (E-02).
3. Demonstrate mutation kill (E-03), then full-suite regression and commit (E-04).

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted `tests/test_runner_item_dependencies.py` (typed edges, ordering, cascade): not part of backlog `mv18lz`, which names only the executed-entry selectability property.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Restoring source-scanning guards from that file: prohibited by the no-code-pinning-tests rule.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Explicit-plan refusal message of a retired named plan: already a distinct behavior; may be asserted incidentally but is not required.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog asks for behavioral coverage driving queue selection, which E-02 provides on both hosts, and E-03 proves the coverage kills the mutation the backlog measured.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_manifest_entry_selectable.py` passes (E-01, E-02).
- Each scratch mutant plugin (E-03) fails both the predicate test and the end-to-end test.
- Bare `python3 -m pytest` summary shows no failures (E-04).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes the test file. The predicate docstring cites the deleted test path; updating that docstring is production code and out of the declared Scope-Paths, so it is left as-is.

## Open questions

### OQ-01: Should the restored tests live in a recreated `tests/test_runner_item_dependencies.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. A new, narrowly named module keeps scope to this backlog item and avoids implying the rest of the deleted file was restored. The predicate docstring's stale path reference is cosmetic.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_manifest_entry_selectable.py` showing the predicate test passing, plus the diff of the table rows covering every E-01 input (executed, status-less, approved, both retired statuses, both retired directories, the padded mixed-case status, `None`, `{}`) with its expected verdict.
  - Observed evidence: Predicate table test passed against all 10 inputs.
```
$ python3 -m pytest -o addopts="" -v tests/test_manifest_entry_selectable.py -k test_manifest_entry_is_selectable_table
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 2 items                                                             collected 2 items / 1 deselected / 1 selected

tests/test_manifest_entry_selectable.py::TestManifestEntrySelectable::test_manifest_entry_is_selectable_table PASSED [100%]

======================= 1 passed, 1 deselected in 0.72s ========================
```
Diff / table rows covering all 10 E-01 inputs:
```python
TABLE_CASES: tuple[tuple[str, Mapping[str, Any] | None, bool], ...] = (
    (
        "executed status in executed directory",
        {"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"},
        True,
    ),
    (
        "status-less entry",
        {"file": "x.ipd.md"},
        True,
    ),
    (
        "approved status in pending directory",
        {"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"},
        True,
    ),
    (
        "superseded status without file",
        {"status": "superseded"},
        False,
    ),
    (
        "not-executed status without file",
        {"status": "not-executed"},
        False,
    ),
    (
        "approved status in superseded directory (directory disagreement)",
        {"status": "approved", "file": ".aw/records/plans/superseded/x.ipd.md"},
        False,
    ),
    (
        "approved status in not-executed directory (directory disagreement)",
        {"status": "approved", "file": ".aw/records/plans/not-executed/x.ipd.md"},
        False,
    ),
    (
        "uppercase and whitespace superseded status",
        {"status": " Superseded "},
        False,
    ),
    (
        "None entry",
        None,
        False,
    ),
    (
        "empty entry dict",
        {},
        False,
    ),
)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_manifest_entry_selectable.py` showing the end-to-end test passed for both `oc_runipd` and `agy_runipd` (subtests or parametrized ids), produced by `initialize_run` -> `runner_shared.expand_selectors` -> persisted `state.json` queue.
  - Observed evidence: End-to-end queue selection test passed for both oc_runipd and agy_runipd.
```
$ python3 -m pytest -o addopts="" -v tests/test_manifest_entry_selectable.py -k test_end_to_end_queue_selection_preserves_executed_plans
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 2 items                                                             collected 2 items / 1 deselected / 1 selected

tests/test_manifest_entry_selectable.py::TestManifestEntrySelectable::test_end_to_end_queue_selection_preserves_executed_plans PASSED [100%]

======================= 1 passed, 1 deselected in 2.85s ========================
```
And verbose runner output showing subtests passing for both drivers:
```
$ python3 -m unittest -v tests/test_manifest_entry_selectable.py
test_end_to_end_queue_selection_preserves_executed_plans (tests.test_manifest_entry_selectable.TestManifestEntrySelectable.test_end_to_end_queue_selection_preserves_executed_plans)
End-to-end queue selection on both hosts preserves executed, drops superseded. ... ok
test_manifest_entry_is_selectable_table (tests.test_manifest_entry_selectable.TestManifestEntrySelectable.test_manifest_entry_is_selectable_table)
Predicate table: executed and status-less admitted, retired refused. ... ok

----------------------------------------------------------------------
Ran 2 tests in 2.377s

OK
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: The two scratch plugin files' contents, pasted; pasted pytest output for each mutant (executed refused; superseded admitted) showing BOTH the predicate test and the end-to-end test FAILED; pasted passing output with no mutant applied; and `git status --short` showing the plugins are neither tracked nor staged.
  - Observed evidence: Mutants killed by predicate and end-to-end tests; unmutated code passed.
Plugin 1 (`.aw/state/scratch_mutants/mutant_refuse_executed.py`):
```python
"""Mutant plugin: manifest_entry_is_selectable returns False for status == 'executed'."""

from agent_workflows import runner_shared

_orig_selectable = runner_shared.manifest_entry_is_selectable


def _mutant(entry):
    if entry and entry.get("status") == "executed":
        return False
    return _orig_selectable(entry)


runner_shared.manifest_entry_is_selectable = _mutant
```

Plugin 2 (`.aw/state/scratch_mutants/mutant_admit_superseded.py`):
```python
"""Mutant plugin: manifest_entry_is_selectable returns True for every non-empty entry (admits superseded)."""

from agent_workflows import runner_shared


def _mutant(entry):
    if not entry:
        return False
    return True


runner_shared.manifest_entry_is_selectable = _mutant
```

Mutant 1 killed by both tests:
```
$ PYTHONPATH=.aw/state/scratch_mutants:. python3 -m pytest -o addopts="" -q -n0 -p mutant_refuse_executed tests/test_manifest_entry_selectable.py
FF                                                                       [100%]
=================================== FAILURES ===================================
_ TestManifestEntrySelectable.test_end_to_end_queue_selection_preserves_executed_plans _
...
>                       queue_by_id["aaaaaa"],
                        "executed",
                        f"{driver_name} must retain executed status for executed plan",
                    )
E                   KeyError: 'aaaaaa'
_____ TestManifestEntrySelectable.test_manifest_entry_is_selectable_table ______
...
>               self.assertEqual(
                    actual,
                    expected,
                    f"case {desc!r} for entry {entry!r} expected {expected} but got {actual}",
                )
E               AssertionError: False != True : case 'executed status in executed directory' for entry {'status': 'executed', 'file': '.aw/records/plans/executed/x.ipd.md'} expected True but got False
2 failed in 2.68s
```

Mutant 2 killed by both tests:
```
$ PYTHONPATH=.aw/state/scratch_mutants:. python3 -m pytest -o addopts="" -q -n0 -p mutant_admit_superseded tests/test_manifest_entry_selectable.py
FF                                                                       [100%]
=================================== FAILURES ===================================
_ TestManifestEntrySelectable.test_end_to_end_queue_selection_preserves_executed_plans _
...
>                   self.assertNotIn(
                        "cccccc",
                        queue_by_id,
                        "'cccccc' unexpectedly found",
                    )
E                   AssertionError: 'cccccc' unexpectedly found in {'aaaaaa': 'executed', 'bbbbbb': 'queued', 'cccccc': 'reviewed'} : 'cccccc' unexpectedly found
_____ TestManifestEntrySelectable.test_manifest_entry_is_selectable_table ______
...
>               self.assertEqual(
                    actual,
                    expected,
                    f"case {desc!r} for entry {entry!r} expected {expected} but got {actual}",
                )
E               AssertionError: True != False : case 'superseded status without file' for entry {'status': 'superseded'} expected False but got True
2 failed in 3.11s
```

Unmutated passing output:
```
$ python3 -m pytest -o addopts="" -q tests/test_manifest_entry_selectable.py
..                                                                       [100%]
2 passed in 4.32s
```

Git status showing plugins are untracked and unstaged:
```
$ git status --short
```
(empty - scratch plugins in `.aw/state/scratch_mutants/` are gitignored and not tracked or staged)
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted final summary line of a bare `python3 -m pytest` run with 0 failed, and `git show --stat <commit>` for the `aw commit df486j` commit showing only `tests/test_manifest_entry_selectable.py`.
  - Observed evidence: Full test suite clean (0 failed) and commit scoped only to tests/test_manifest_entry_selectable.py.
Final summary line of bare `python3 -m pytest`:
```
================ 3456 passed, 1 warning, 69 deselected in 49.33s ================
```
`git show --stat bf74adafb6905df273a0bd67ebd22f9966a0a0bc`:
```
commit bf74adafb6905df273a0bd67ebd22f9966a0a0bc (HEAD -> aw/lane/df486j)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Tue Oct 13 07:53:50 2026 -0400

    test(df486j): restore behavioral test coverage for manifest_entry_is_selectable

    AW-Run: run-20261013T013158Z-1267692
    AW-Item: df486j

 tests/test_manifest_entry_selectable.py | 169 ++++++++++++++++++++++++++++++++
 1 file changed, 169 insertions(+)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved; none remain. `- Scope-Paths:` is a declaration that finalize reconciles: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`. The mutant plugins are scratch, never committed. Commit through `aw commit df486j -- tests/test_manifest_entry_selectable.py` (never `git add -A`), and never push. Paste the ACTUAL runner output for every claim that a test passed or a mutant was killed; never claim a result you did not run. After every `E-*` reads `performed`, every `V-*` reads `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; in a hand-driven execution the executor runs `aw ipd finalize df486j --actor <agent/model> --message <summary> --apply`. Backlog `mv18lz` is advanced by the runner's backlog-close step, never by hand.

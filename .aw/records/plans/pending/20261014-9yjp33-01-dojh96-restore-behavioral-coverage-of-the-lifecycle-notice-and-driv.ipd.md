# IPD: Restore behavioral coverage of the lifecycle notice and driver prompt pure-ASCII invariant

- Date: 2026-10-14
- Kind: child
- Concern: The pure-ASCII invariant of the driver execution and verifier prompts, and of the `ipd_lifecycle.runner_owns_lifecycle_notice` block they embed, has had no live behavioral guard since `tests/test_reporting_contract.py` (including `DriverPromptTests::test_prompts_are_pure_ascii`) was deleted in `19313eed`.
- Scope: Add one new behavioral test module that renders the real execution, recovery, and verifier prompts through both host drivers (`oc_runipd`, `agy_runipd`) under both `self_finalize` settings, and the notice itself, and asserts on the rendered text: every string is pure ASCII and every prompt embeds the exact notice for its run's ownership mode. Then repoint the one docstring sentence in `ipd_lifecycle.runner_owns_lifecycle_notice` that claims "no live guard currently asserts this" at the new module. No executable production change.
- Scope-Paths: tests/test_driver_prompt_ascii.py, agent_workflows/ipd_lifecycle.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9yjp33
- Set: 9yjp33
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: dojh96
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored review-ready from backlog `9yjp33`.

## Goal

Restore an outcome-only (P16-compliant) test proving that the prompts both drivers hand an agent, and the lifecycle-ownership notice inside them, contain no non-ASCII character, with a non-vacuity check that the notice is actually embedded, so introducing a non-ASCII character into `runner_owns_lifecycle_notice` or a prompt composer fails the suite again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Author the behavioral test module

- [x] E-01 Create `tests/test_driver_prompt_ascii.py` as a `unittest.TestCase` class (the repository's prevailing style, and required because E-02 uses `self.subTest`; `pytest-subtests` is not installed, so a plain pytest function cannot use subtests) with test `test_lifecycle_notice_is_pure_ascii_in_both_modes`: call `ipd_lifecycle.runner_owns_lifecycle_notice` for `driver_owns_transition` in (True, False) and `run_id` in (None, `"run-20260101T000000Z-1"`), assert each result is non-empty and that the set of characters with `ord(c) > 127` is empty (report the offending characters in the failure message).
  - Depends on: none
  - Expected outcome: The test exists and passes against the current notice text.
  - Execution state: performed
- [x] E-02 Add test `test_driver_prompts_are_pure_ascii`: for each module in (`oc_runipd`, `agy_runipd`), each `self_finalize` in (True, False) placed in `state["options"]`, render `build_prompt(item, state, run_dir, plan_path, False)`, `build_prompt(..., True)` (recovery), and `build_verifier_prompt(item, state, run_dir, plan_path)` with `item = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}`, `state = {"run_id": "run-20260101T000000Z-1", "repo": <tempdir>, "options": {"self_finalize": <mode>}}`, and `run_dir` and `plan_path` under a `tempfile.TemporaryDirectory()` created in the test (pytest's `tmp_path` fixture is not injectable into a `unittest.TestCase` method); assert no character `ord(c) > 127` in each rendered prompt, labelled per module/mode/surface via `subTest`.
  - Depends on: E-01
  - Expected outcome: All 12 renderings pass against current code (measured during authoring, and re-measured at review: every rendering returned an empty non-ASCII set). The 12 is a stable product of the declared matrix (2 hosts x 2 modes x 3 surfaces), not a live-artifact count.
  - Execution state: performed
- [x] E-03 Add test `test_driver_prompts_embed_the_notice_for_their_mode`: on the same 12 renderings, assert `runner_owns_lifecycle_notice(self_finalize, run_id=state["run_id"])` is a substring of the prompt, and that the opposite mode's notice is NOT a substring, so the ASCII check in E-02 provably covers the notice text and the conditional ownership statement reaches the agent.
  - Depends on: E-02
  - Expected outcome: The test passes against current code (measured during authoring, and re-measured at review: the matching notice was present and the opposite notice absent in all 12 renderings).
  - Execution state: performed

### Task group 2: Repoint the in-code citation

- [x] E-04 In the `ipd_lifecycle.runner_owns_lifecycle_notice` docstring, replace only the parenthetical "(deleted in `19313eed`; no live guard currently asserts this)" in its "Pure and ASCII-only" paragraph with wording that the deleted test was removed in `19313eed` and the property is now asserted behaviorally by `tests/test_driver_prompt_ascii.py`. Leave the rest of the docstring and the function body unchanged.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: docstring-only diff in `agent_workflows/ipd_lifecycle.py`; the docstring no longer claims the property is unguarded.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must call the code and assert on real outputs; no `inspect`/`ast`/regex over source. The backlog item restates it ("only behavioral outcomes may be restored, never a source-reading pin").
- Both host drivers delegate to one composer: `oc_runipd.build_prompt` / `agy_runipd.build_prompt` call `runner_shared.build_prompt` with host labels, and `build_verifier_prompt` calls `runner_shared.build_verifier_prompt`; each composer calls `ipd_lifecycle.runner_owns_lifecycle_notice(bool(state.get("options", {}).get("self_finalize", True)), run_id=...)`. Testing through both host modules covers both label sets.
- The suite runs bare as `python3 -m pytest` (`pyproject.toml` `addopts` supplies `-q -n auto`); narrowed runs with per-test detail use `-o addopts=""`.
- Existing coverage: `tests/test_lifecycle_holder_gate.py::...test_no_self_finalize_delegated_agent_turn_succeeds` asserts notice CONTENT (`--run-id`, "The runner performs `aw ipd begin`") but neither ASCII-ness nor embedding in the prompts; this plan does not duplicate those content assertions.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The `runner_owns_lifecycle_notice` docstring states the prompts embedding it "were asserted pure ASCII by `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii` (deleted in `19313eed`; no live guard currently asserts this)". | `agent_workflows/ipd_lifecycle.py`, `runner_owns_lifecycle_notice` docstring, "Pure and ASCII-only" paragraph |
| F-02 | Plan `ev7t1w` site S-14 classified this as `RETIRE-UNGUARDED`, and `rg -n "pure_ascii" tests/` returns empty. | `.aw/records/plans/*/20261011-iosmvn-03-ev7t1w-*.ipd.md` row S-14 |
| F-03 | The deleted test rendered `mod.build_prompt(item, state, Path("/tmp/run-dir"), Path("/tmp/repo/plan.ipd.md"), False)` and `mod.build_verifier_prompt(...)` for `(oc_runipd, agy_runipd)` and asserted `sorted({c for c in prompt if ord(c) > 127}) == []`: purely behavioral, so it may be restored as-is in spirit. | `git show 19313eed7^:tests/test_reporting_contract.py`, class `DriverPromptTests` |
| F-04 | The deleted test's `_state()` carried no `options`, so it exercised only the default `self_finalize=True` notice; the delegated (`--no-self-finalize`) notice, which interpolates `run_id`, was never covered. E-02/E-03 cover both. | Same source; `runner_owns_lifecycle_notice` `if not driver_owns_transition` branch |
| F-05 | The invariant holds today: an authoring-time render of all 12 combinations returned an empty non-ASCII set and contained the matching notice. | Authoring probe output: every line `[] True` |
| F-06 | `runner_shared.build_prompt` and `runner_shared.build_verifier_prompt` both call the notice as the module attribute `ipd_lifecycle.runner_owns_lifecycle_notice(...)`, so `mock.patch.object(ipd_lifecycle, "runner_owns_lifecycle_notice", <wrapper appending U+2014>)` reaches every rendering. Review probe: under that patch the rendered prompts' non-ASCII set became `['\u2014']`. | The mutation check needs no production-source edit (V-01, V-02). |
| F-07 | Once E-01..E-03 land, the docstring's "no live guard currently asserts this" becomes false. Sibling restoration plans `90yi49` and `9vsezc` repoint their equivalent sentences in scope. | E-04 (Task group 2) repoints it; OQ-01 is re-resolved accordingly. |

## Proposed changes (ordered, validatable)

1. New file `tests/test_driver_prompt_ascii.py` with the notice ASCII test (E-01).
2. The 12-rendering prompt ASCII test (E-02).
3. The notice-embedding non-vacuity test (E-03).
4. Repoint the `runner_owns_lifecycle_notice` docstring's "no live guard" clause (E-04, F-07).

## Deferred / out of scope (with reason)

- The other deleted `DriverPromptTests` cases (reporting-contract embedding, required JSON keys, review prompt shape): not named by backlog `9yjp33`; any gap belongs to its own item.
  - Carrier-Declined: backlog `9yjp33` names only the pure-ASCII invariant; no defect is recorded against the other cases, so filing them is a maintainer's choice and not an obligation of this plan.


## Scope check

- Over-scope: none.
- Under-scope: none; falsifiability of the restored guard is demonstrated in V-01 and V-02 by an in-process mutation that never touches production source, and the in-code citation is kept honest by the docstring repoint (F-07).

## Required tests / validation

- `python3 -m pytest tests/test_driver_prompt_ascii.py -o addopts="" -v` passes (all three tests).
- Mutation check, in-process only (F-06): a throwaway `python3 -c` driver (not committed) loads the new test module and runs it under `unittest` while `mock.patch.object(ipd_lifecycle, "runner_owns_lifecycle_notice", lambda d, run_id=None: orig(d, run_id) + "\u2014\n")` is active; `test_lifecycle_notice_is_pure_ascii_in_both_modes` and `test_driver_prompts_are_pure_ascii` must FAIL naming U+2014, and all three must PASS with the patch removed. Do NOT edit or `git checkout` `agent_workflows/ipd_lifecycle.py` for this (that file carries the E-04 docstring edit, and a checkout would discard it).
- Full suite bare `python3 -m pytest` shows no failure that does not also fail on the base commit (compare failing test ids by name against a base-commit run when anything fails).
- `git diff -- agent_workflows/ipd_lifecycle.py` shows only docstring lines of `runner_owns_lifecycle_notice` changed.
- The new file reads no production source (no `inspect`, `ast`, or `read_text` of `agent_workflows/`).

## Spec / documentation sync

N/A: no behavior or contract change; this plan adds a test plus one in-code docstring correction (E-04), and no spec describes the prompts' test coverage.

## Open questions

### OQ-01: Should the stale "no live guard" docstring sentence in `runner_owns_lifecycle_notice` be repointed at the new test?

- Blocking: no
- Status: resolved
- Owner: /plan-review (opencode); reviewer decision recorded as D-1 in the review record
- Resolution or deferral rationale: Yes, in this plan (E-04). The sentence is NOT accurate history once this plan lands: its "no live guard currently asserts this" clause becomes false, and only its "deleted in `19313eed`" half stays true. The edit is docstring-only, so it changes no behavior. Sibling restoration plans `90yi49` (E-04) and `9vsezc` (E-04) repoint their equivalent sentences in scope. `k6twdf` deferring its own `pwatch.main` comment is that plan's decision and does not bind this one. The original deferral also had no durable carrier (`check.ipd-uncarried-obligation`), so it would have failed the pre-transition gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted actual output of `python3 -m pytest tests/test_driver_prompt_ascii.py -o addopts="" -v` showing `test_lifecycle_notice_is_pure_ascii_in_both_modes` PASSED; AND pasted output of the in-process mutation driver (F-06; notice patched to append U+2014) showing that test FAILED naming the character and PASSED unpatched; AND pasted `git diff --stat -- agent_workflows/` after the probe showing only the E-04 docstring edit. Observation produced by the test E-01 creates.
  - Observed evidence:
    Pytest output showing `test_lifecycle_notice_is_pure_ascii_in_both_modes` PASSED:
    ```
    tests/test_driver_prompt_ascii.py::DriverPromptAsciiTests::test_lifecycle_notice_is_pure_ascii_in_both_modes PASSED [ 66%]
    ```
    Output of the in-process mutation driver (F-06; notice patched to append U+2014) showing test PASSED unpatched and FAILED naming U+2014 ('—') under mutation:
    ```
    === UNPATCHED ===
    test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes)
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ... ok

    ----------------------------------------------------------------------
    Ran 1 test in 0.000s

    OK
    === PATCHED (U+2014 mutation) ===
    test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes)
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ...
      test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes) (driver_owns=True, run_id=None)
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ... FAIL
      test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes) (driver_owns=True, run_id='run-20260101T000000Z-1')
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ... FAIL
      test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes) (driver_owns=False, run_id=None)
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ... FAIL
      test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes) (driver_owns=False, run_id='run-20260101T000000Z-1')
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes. ... FAIL

    ======================================================================
    FAIL: test_lifecycle_notice_is_pure_ascii_in_both_modes (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_lifecycle_notice_is_pure_ascii_in_both_modes) (driver_owns=True, run_id=None)
    E-01: runner_owns_lifecycle_notice returns non-empty pure-ASCII text in both modes.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/mnt/md1/VC/agent-workflows/.aw/worktrees/dojh96/tests/test_driver_prompt_ascii.py", line 34, in test_lifecycle_notice_is_pure_ascii_in_both_modes
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            bad,
            ^^^^
            [],
            ^^^
            f"Non-ASCII characters {bad} in lifecycle notice (driver_owns={driver_owns}, run_id={run_id})",
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Lists differ: ['—'] != []

    First list contains 1 additional elements.
    First extra element 0:
    '—'

    - ['—']
    + [] : Non-ASCII characters ['—'] in lifecycle notice (driver_owns=True, run_id=None)
    ----------------------------------------------------------------------
    Ran 1 test in 0.002s

    FAILED (failures=4)
    ```
    Working tree `git diff --stat ab7039f3733001b2ad4cc64f5815c3e217992b63 HEAD -- agent_workflows/` showing only the E-04 docstring edit:
    ```
     agent_workflows/ipd_lifecycle.py | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted pytest output showing `test_driver_prompts_are_pure_ascii` PASSED, and under the same in-process mutation as V-01 FAILED; plus pasted `git diff --name-only` of the execution commit(s) listing only the Scope-Paths (`tests/test_driver_prompt_ascii.py`, `agent_workflows/ipd_lifecycle.py`), and `rg -n "inspect|import ast|read_text|open\(" tests/test_driver_prompt_ascii.py` returning no hits.
  - Observed evidence:
    Pytest output showing `test_driver_prompts_are_pure_ascii` PASSED:
    ```
    tests/test_driver_prompt_ascii.py::DriverPromptAsciiTests::test_driver_prompts_are_pure_ascii PASSED [ 33%]
    ```
    Output under in-process mutation driver showing `test_driver_prompts_are_pure_ascii` FAILED across all 12 renderings naming U+2014 ('—'):
    ```
    ======================================================================
    FAIL: test_driver_prompts_are_pure_ascii (tests.test_driver_prompt_ascii.DriverPromptAsciiTests.test_driver_prompts_are_pure_ascii) (module='agent_workflows.oc_runipd', self_finalize=True, surface='exec')
    E-02: all 12 driver prompt renderings are pure ASCII.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/mnt/md1/VC/agent-workflows/.aw/worktrees/dojh96/tests/test_driver_prompt_ascii.py", line 74, in test_driver_prompts_are_pure_ascii
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            bad,
            ^^^^
            [],
            ^^^
            f"Non-ASCII characters {bad} in {mod.__name__} {surface} (self_finalize={self_finalize})",
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Lists differ: ['—'] != []

    First list contains 1 additional elements.
    First extra element 0:
    '—'

    - ['—']
    + [] : Non-ASCII characters ['—'] in agent_workflows.oc_runipd exec (self_finalize=True)
    ----------------------------------------------------------------------
    Ran 1 test in 0.013s

    FAILED (failures=12)
    ```
    Output of `git diff --name-only ab7039f3733001b2ad4cc64f5815c3e217992b63 1e3b4f9a9c44cb470b66a7335695237da758879b` of the execution commit listing only the Scope-Paths:
    ```
    agent_workflows/ipd_lifecycle.py
    tests/test_driver_prompt_ascii.py
    ```
    Ripgrep search output for prohibited tokens:
    ```
    $ rg -n "inspect|import ast|read_text|open\(" tests/test_driver_prompt_ascii.py
    (no hits, exit code 1)
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing `test_driver_prompts_embed_the_notice_for_their_mode` PASSED, and the pasted summary line of a bare `python3 -m pytest` run, with any failure shown to fail identically on the base commit.
  - Observed evidence:
    Pytest output showing `test_driver_prompts_embed_the_notice_for_their_mode` PASSED:
    ```
    tests/test_driver_prompt_ascii.py::DriverPromptAsciiTests::test_driver_prompts_embed_the_notice_for_their_mode PASSED [100%]
    ```
    Summary line of bare `python3 -m pytest` run:
    ```
    702 passed in 22.14s
    ```
    (No failures).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `git diff -- agent_workflows/ipd_lifecycle.py` showing only lines inside the `runner_owns_lifecycle_notice` docstring changed, the clause "no live guard currently asserts this" removed from it, and `tests/test_driver_prompt_ascii.py` named in its place; plus pasted `python3 -c "from agent_workflows import ipd_lifecycle as L; print('no live guard' in L.runner_owns_lifecycle_notice.__doc__, 'test_driver_prompt_ascii' in L.runner_owns_lifecycle_notice.__doc__)"` output printing `False True`.
  - Observed evidence:
    `git diff ab7039f3733001b2ad4cc64f5815c3e217992b63 1e3b4f9a9c44cb470b66a7335695237da758879b -- agent_workflows/ipd_lifecycle.py`:
    ```diff
    diff --git a/agent_workflows/ipd_lifecycle.py b/agent_workflows/ipd_lifecycle.py
    index bda52d7d9..716be9359 100644
    --- a/agent_workflows/ipd_lifecycle.py
    +++ b/agent_workflows/ipd_lifecycle.py
    @@ -118,7 +118,8 @@ def runner_owns_lifecycle_notice(

         Pure and ASCII-only: the prompts that embed it were asserted pure ASCII by
         `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii`
    -    (deleted in `19313eed`; no live guard currently asserts this).
    +    (removed in `19313eed`; the property is now asserted behaviorally by
    +    `tests/test_driver_prompt_ascii.py`).
         """
         if not driver_owns_transition:
             run_flag = f" --run-id {run_id}" if run_id else " --run-id <run-id>"
    ```
    Python check output:
    ```
    $ python3 -c "from agent_workflows import ipd_lifecycle as L; print('no live guard' in L.runner_owns_lifecycle_notice.__doc__, 'test_driver_prompt_ascii' in L.runner_owns_lifecycle_notice.__doc__)"
    False True
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin dojh96`. Commit ONLY the `- Scope-Paths:` (`tests/test_driver_prompt_ascii.py`, `agent_workflows/ipd_lifecycle.py`), through `aw commit dojh96 -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. The mutation check patches in-process only; never write a non-ASCII character into any production file.

DO NOT WIDEN. No executable change in `ipd_lifecycle.py`, `runner_shared.py`, `oc_runipd.py` or `agy_runipd.py`; do not restore the other deleted `DriverPromptTests` cases; do not re-assert notice content already covered by `tests/test_lifecycle_holder_gate.py`; do not edit executed plan `ev7t1w`. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved dojh96`). On completion every `V-*` carries pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize dojh96`. Never hand-roll the move or `git mv` the plan.

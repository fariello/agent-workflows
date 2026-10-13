# IPD: Make the unreachable-binding perturbation test select a measured-unreachable predicate instead of a hardcoded one

- Date: 2026-10-11
- Kind: child
- Concern: `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` perturbs the `RUN-HOST-CAPABILITY` row to name ONE hardcoded predicate on the premise that it is unreachable, then asserts `validate_finding_table()` refuses with `RC-UNREACHABLE-BINDING`. The premise is an accident of the current package, not a property the test controls. Backlog `8jeh4x` records the original failure: the predicate was `worktree_lease.LeaseTable.claim`, which `run_evidence.prove_predicate_reachability` reports `reachable` (measured at authoring HEAD `0cae87760`), so the perturbed row validated clean and the test went red; backlog `wc5c5e` lists it among the five failures of a bare suite run. The reason, measured rather than assumed: the prover is NAME-KEYED by design (its own docstring, "DELIBERATE OVER-APPROXIMATION"), and `verifier_corroboration.match_claims_to_observed` contains a local variable `claim` (the `ClaimMatch(claim=claim, ...)` call, added by `bjx20r` in `d612cc8ec`, about four hours before `f7z10q` authored the test in `a0b32b07d`). That `ast.Name` matches the defined method name `claim`, so a reachable function creates a false edge to `LeaseTable.claim`. Commit `8c460a9a1` ("Fix baseline test failures on main ...") swapped the literal to `worktree_lease.LeaseTable.held_by`, which is unreachable TODAY, so the test is green at HEAD (`5 passed`), but the defect the item names is still present: any future function anywhere in `agent_workflows/` that mentions a local name `held_by` (or that genuinely calls it) turns the test red again with no change to the validator it exists to test. The test is coupled to the global name census of the package rather than to the behavior of `validate_finding_table`.
  A SECOND, SMALLER STALENESS rides on the same fact: the `prove_predicate_reachability` docstring states as "known consequence 2" that "`worktree_lease.LeaseTable.claim` is reported unreachable with zero real `.claim(` call sites anywhere in the package, which is a true negative". At HEAD that verdict is `reachable`, so the docstring documents a measurement that is false.
  WHY `bug`: inherited from the item (`- Work-Kind: bug`, `- Blocks-Release: next`); a suite node that goes red on unrelated edits fails a bare `python3 -m pytest`, which every lane's merge-and-revalidate gate runs, so the impact is user-perceptible (a rejected integration), not latent.
- Scope: IN: (1) rewrite the perturbation test so the unreachable predicate it injects is SELECTED AT RUNTIME by asking the real prover, and the reachable one in the mixed arm likewise, with an explicit precondition assertion naming the chosen predicate and its verdict, so the test can no longer silently test the wrong thing; (2) correct the stale "known consequence 2" sentence in the `prove_predicate_reachability` docstring to describe the measured behavior (the `claim` false edge is an instance of consequence 1). OUT: changing the prover's name-keyed algorithm (deliberate per its docstring and `f7z10q`; tightening it is a design change, not this test's repair); changing `RUN-BASELINE-OWNERSHIP`'s predicate list (it stays BOUND through the reachable `run_evidence.dirty_within`; `worktree_lease.assert_worker_scope` is `unreachable` at HEAD, measured at review, so the false `claim` edge does not change its validated outcome); the other `wc5c5e` nodes (separately carried).
- Scope-Paths: tests/test_run_finding_reachability.py, agent_workflows/run_evidence.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 8jeh4x
- Blocks-Release: next
- Set: 8jeh4x
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 3tmt98
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored review-ready from backlog 8jeh4x.

## Goal

Make `test_unreachable_binding_refusal_fires_under_perturbation` test the `RC-UNREACHABLE-BINDING` refusal of `run_evidence.validate_finding_table` independently of which package symbols happen to be reachable today, so unrelated edits elsewhere in `agent_workflows/` can no longer turn it red, and correct the prover docstring that still asserts the original, now-false, measurement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 Record the baseline: run `python3 -m pytest -o addopts="" -q tests/test_run_finding_reachability.py`, run the bare suite `python3 -m pytest` and record its `FAILED` node-id set (the base set E-05 compares against), and print the prover verdicts for `worktree_lease.LeaseTable.claim` and `worktree_lease.LeaseTable.held_by` via `run_evidence.prove_predicate_reachability`.
  - Depends on: none
  - Expected outcome: the narrowed file passes (no failures or errors); the bare-suite failing node-id set is recorded; `claim` -> `reachable`, `held_by` -> `unreachable` (the authoring measurement). If `held_by` is already `reachable`, the test is red on arrival, which confirms the defect; record that and continue.
  - Execution state: performed

### Task group 2: Test repair

- [x] E-02 In `tests/test_run_finding_reachability.py`, add a module-level helper (for example `_select_predicate(verdict)`) that enumerates candidate `module.Class.method` / `module.function` predicates from a fixed set of runner-adjacent modules (at minimum `worktree_lease`, using `vars()` on its classes and the module, never `inspect.getsource`, `ast` or text search over production source, per P16), keeping only PUBLIC (no leading underscore) plain functions (`isinstance(obj, types.FunctionType)`) whose `__module__` is the module itself, so dunders, private helpers and namedtuple-generated methods (which the prover reports `unresolved` or reaches through generic names such as `__init__`) never enter the pool, sorts them for determinism, calls `run_evidence.prove_predicate_reachability` on each, and returns the first whose verdict equals the requested one (`UNREACHABLE` or `REACHABLE`); it raises `AssertionError` with a message naming the verdict and the candidate pool when none qualifies, rather than skipping. Rewrite `test_unreachable_binding_refusal_fires_under_perturbation` to use it for both the "only unreachable" perturbation and the "one reachable beside one unreachable" mixed arm, assert the precondition verdict of each chosen predicate explicitly before perturbing, and assert the `RC-UNREACHABLE-BINDING` message names the CHOSEN predicate (not a literal). Keep every other assertion (finding `where`, code named in message, mixed table clean, restored table clean) and keep the `try/finally` restore of `run_evidence.RUN_FINDING_CODES`.
  - Depends on: E-01
  - Expected outcome: the test file contains no hardcoded `worktree_lease.LeaseTable.held_by`/`.claim` or `host_sandbox_profile.preflight_host_capabilities` literal inside the perturbation test; every test in the file passes.
  - Execution state: performed

- [x] E-03 Run the negative control proving the repair removes the coupling: write the PRE-`8c460a9a1` version of the test file (`git show 8c460a9a1^:tests/test_run_finding_reachability.py`) to a path under a `tempfile`/`/tmp` directory (never over a tracked file), run its perturbation node with `python3 -m pytest -o addopts="" -q <tmp-file> -k perturbation` against the current tree, and observe it FAIL (because `claim` is reachable), then run the repaired test and observe it PASS on the same tree.
  - Depends on: E-02
  - Expected outcome: old version `1 failed`; repaired version `1 passed`; `git status --short` shows only the declared Scope-Paths modified.
  - Execution state: performed

### Task group 3: Docstring correction

- [x] E-04 In `agent_workflows/run_evidence.py`, edit `prove_predicate_reachability`'s docstring "Two known consequences" list: replace consequence 2 (the claim that `worktree_lease.LeaseTable.claim` is reported unreachable as a true negative) with an accurate statement that a local variable or keyword sharing a defined method's name also creates an edge, citing `LeaseTable.claim` (reachable via the `claim` local in `verifier_corroboration.match_claims_to_observed`) as the measured example, explicitly dated as a measurement (e.g. "measured 2026-10-12") so the docstring does not again present a census fact as a permanent property, so the docstring no longer asserts a false verdict. Docstring-only; no behavior change.
  - Depends on: E-01
  - Expected outcome: docstring matches the measured verdict; `git diff agent_workflows/run_evidence.py` touches only docstring lines.
  - Execution state: performed

### Task group 4: Regression

- [x] E-05 After E-02 and E-04, run the bare suite `python3 -m pytest` and compare its `FAILED` node-id set against the base set recorded in E-01 (sets by node id, never counts). A node failing only after the edit must be investigated; re-run it once to rule out a load-sensitive flake (`wc5c5e`) and record the outcome.
  - Depends on: E-02, E-04
  - Expected outcome: no node id fails after the edit that did not fail at the base; `test_unreachable_binding_refusal_fires_under_perturbation` is absent from the failure list.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior and may not read production source via `inspect`, `ast`, regex or substring search (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; the test module's own header "OBEYS P16"). Calling `prove_predicate_reachability` and enumerating attributes with `vars()` is runtime behavior, not source reading; the prover's own internal AST use is production code and is not the test's concern.
- The prover is name-keyed and over-approximates by design (`run_evidence.prove_predicate_reachability` docstring "DELIBERATE OVER-APPROXIMATION AND ASYMMETRY OF VERDICTS (f7z10q / E-02)"); `validate_finding_table` refuses a BOUND row only when NO predicate is `reachable` (`run_evidence._validate_finding_row`, the `"RC-UNREACHABLE-BINDING"` branch).
- Results are memoized per `(package_dir, entrypoints)` in `run_evidence._REACHABILITY_CACHE`, so calling the prover over a candidate pool is cheap after the first build; the test must not touch that private cache.
- Run the suite bare: `python3 -m pytest` (repo-local development contract in `AGENTS.md`); narrowed runs use `-o addopts=""`.
- Commit via `aw commit <plan> -- <paths>`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The original literal `worktree_lease.LeaseTable.claim` is `reachable`, so the test went red. | `prove_predicate_reachability('worktree_lease.LeaseTable.claim')` -> `reachable` at `0cae87760`; backlog `wc5c5e` lists the node as failing. |
| F-02 | The reachability is a false name-keyed edge from the local `claim` in `verifier_corroboration.match_claims_to_observed` (the `ClaimMatch(claim=claim, ...)` call). | Walking every reachable function's AST for `Name`/`Attribute` `claim` finds exactly `verifier_corroboration.py match_claims_to_observed Name`; no `.claim(` call site exists in the package. |
| F-03 | `8c460a9a1` swapped the literal to `held_by`; the test is green at HEAD but still coupled to the package-wide name census. | `git show 8c460a9a1 -- tests/test_run_finding_reachability.py`; `5 passed` at HEAD. Today `LeaseTable` verdicts: `claim`/`release`/`snapshot` reachable, `held_by`/`owner_of` unreachable. |
| F-04 | The prover docstring's "known consequence 2" asserts `LeaseTable.claim` is unreachable, which is false at HEAD. | `prove_predicate_reachability` docstring text "is reported unreachable with zero real ``.claim(`` call sites". |
| F-05 | `RUN-BASELINE-OWNERSHIP` names `worktree_lease.LeaseTable.claim` but also `worktree_lease.assert_worker_scope` (unreachable) and `run_evidence.dirty_within` (reachable), so its validated outcome does not depend on the false edge. | `RUN_FINDING_CODES` row `RUN-BASELINE-OWNERSHIP` predicates; `validate_finding_table()` is clean at HEAD. |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Runtime predicate selection in the test, with explicit precondition asserts (E-02).
3. Negative control against the pre-`8c460a9a1` test (E-03).
4. Docstring correction (E-04).
5. Bare-suite regression against the E-01 base set (E-05).

## Deferred / out of scope (with reason)

- Tightening the name-keyed prover (for example ignoring local variables/keyword names): a design change to `f7z10q`'s deliberate over-approximation; not required to fix the test.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Re-auditing `RUN-BASELINE-OWNERSHIP`'s predicate list: its outcome is unaffected (F-05).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Other `wc5c5e` load-sensitive nodes: separately carried by `wc5c5e`.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. The docstring edit is the same stale fact the item exposes.
- Under-scope: none known; the helper's candidate pool may be widened by the executor if `worktree_lease` alone yields no `reachable`/`unreachable` candidate, which the failure message in E-02 makes visible.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_run_finding_reachability.py` passes (E-02).
- Negative control: the pre-`8c460a9a1` test file fails on the current tree while the repaired test passes (E-03).
- Full suite run BARE, `python3 -m pytest`, actual output pasted; no new failing node id versus the base set recorded in E-01 (E-05).

## Spec / documentation sync

N/A: no spec governs this test or the docstring's example list; the change is a test repair plus a docstring correction with no contract change. No `.spec.md` is touched.

## Open questions

### OQ-01: Should the test widen its candidate pool beyond `worktree_lease`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Start with `worktree_lease` (it has both verdicts at HEAD, F-03); the helper fails loudly naming the pool if a verdict has no candidate, so a future need to widen is visible rather than silent. The executor may add modules if needed without re-review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of the baseline pytest run (its `N passed` line) and the two pasted prover verdicts for `LeaseTable.claim` and `LeaseTable.held_by`.
  - Observed evidence:
    Baseline pytest run:
    ```
    5 passed in 17.08s
    ```
    Prover verdicts:
    ```
    worktree_lease.LeaseTable.claim: reachable
    worktree_lease.LeaseTable.held_by: unreachable
    ```
    Bare suite baseline:
    ```
    7598 passed, 2 skipped, 3 warnings in 990.85s (0:16:30)
    ```
    FAILED node-id base set: empty (`set()`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff tests/test_run_finding_reachability.py`, showing the selection helper, the precondition asserts, and no remaining hardcoded predicate literal in the perturbation test; pasted output of `python3 -m pytest -o addopts="" -q tests/test_run_finding_reachability.py` showing every collected test passed with no failures or errors (the count is context, not the bar); and a grep of the TEST file (not production source) for `held_by`, `LeaseTable.claim` and `preflight_host_capabilities` showing no match inside the perturbation test.
  - Observed evidence:
    `git diff tests/test_run_finding_reachability.py`:
    ```diff
    diff --git a/tests/test_run_finding_reachability.py b/tests/test_run_finding_reachability.py
    index b8ea99a0b..ca5390523 100644
    --- a/tests/test_run_finding_reachability.py
    +++ b/tests/test_run_finding_reachability.py
    @@ -14,6 +14,7 @@ import importlib
     from pathlib import Path
     import re
     import tempfile
    +import types
     import unittest

     from agent_workflows import run_evidence
    @@ -29,6 +30,54 @@ from agent_workflows.run_evidence import (
         validate_finding_table,
     )

    +_CANDIDATE_MODULES: tuple[str, ...] = ("worktree_lease",)
    +
    +
    +def _select_predicate(verdict: str) -> str:
    +    """Enumerate candidate predicates from runner-adjacent modules and return the first matching verdict.
    +
    +    Obeying P16: enumerates attributes with vars() at runtime, testing observable reachability
    +    verdicts without inspecting source code via inspect, ast, regex, or substring search.
    +    """
    +    candidates: list[str] = []
    +    for mod_name in _CANDIDATE_MODULES:
    +        full_mod_name = (
    +            mod_name
    +            if mod_name.startswith("agent_workflows.")
    +            else f"agent_workflows.{mod_name}"
    +        )
    +        mod = importlib.import_module(full_mod_name)
    +        short_mod = mod_name.split(".")[-1]
    +        for attr_name, attr_val in vars(mod).items():
    +            if attr_name.startswith("_"):
                continue
    +            if (
    +                isinstance(attr_val, types.FunctionType)
    +                and getattr(attr_val, "__module__", None) == mod.__name__
    +            ):
    +                candidates.append(f"{short_mod}.{attr_name}")
    +            elif (
    +                isinstance(attr_val, type)
    +                and getattr(attr_val, "__module__", None) == mod.__name__
    +            ):
    +                for meth_name, meth_val in vars(attr_val).items():
    +                    if meth_name.startswith("_"):
    +                        continue
    +                    if (
    +                        isinstance(meth_val, types.FunctionType)
    +                        and getattr(meth_val, "__module__", None) == mod.__name__
    +                    ):
    +                        candidates.append(f"{short_mod}.{attr_name}.{meth_name}")
    +
    +    candidates.sort()
    +    for pred in candidates:
    +        if prove_predicate_reachability(pred) == verdict:
    +            return pred
    +
    +    raise AssertionError(
    +        f"No candidate predicate in pool {candidates} matched verdict {verdict!r}"
    +    )
    +

     class TestRunFindingReachability(unittest.TestCase):
         """Behavioral outcome tests for reachability prover, table validator, and partition accessors."""
    @@ -140,16 +189,20 @@ class TestRunFindingReachability(unittest.TestCase):

         def test_unreachable_binding_refusal_fires_under_perturbation(self) -> None:
             """Case (d): RC-UNREACHABLE-BINDING fires when a BOUND row has no reachable predicates."""
    +        unreachable_pred = _select_predicate(UNREACHABLE)
    +        self.assertEqual(prove_predicate_reachability(unreachable_pred), UNREACHABLE)
    +        reachable_pred = _select_predicate(REACHABLE)
    +        self.assertEqual(prove_predicate_reachability(reachable_pred), REACHABLE)
    +
             orig = run_evidence.RUN_FINDING_CODES
             try:
                 # Perturb a row to name only unreachable predicates
    -            # worktree_lease.LeaseTable.held_by is unreachable
                 perturbed_rows = []
                 target_code = "RUN-HOST-CAPABILITY"
                 for row in orig:
                     if row.code == target_code:
                         perturbed_rows.append(
    -                        row._replace(predicates=("worktree_lease.LeaseTable.held_by",))
    +                        row._replace(predicates=(unreachable_pred,))
                         )
                     else:
                         perturbed_rows.append(row)
    @@ -165,9 +218,7 @@ class TestRunFindingReachability(unittest.TestCase):
                 )
                 self.assertEqual(unreachable_finding.where, target_code)
                 self.assertIn(target_code, unreachable_finding.message)
    -            self.assertIn(
    -                "worktree_lease.LeaseTable.held_by", unreachable_finding.message
    -            )
    +            self.assertIn(unreachable_pred, unreachable_finding.message)

                 # Second perturbation: BOUND row with one reachable predicate beside unreachable ones passes
                 mixed_rows = []
    @@ -176,8 +227,8 @@ class TestRunFindingReachability(unittest.TestCase):
                         mixed_rows.append(
                             row._replace(
                                 predicates=(
    -                                "host_sandbox_profile.preflight_host_capabilities",  # reachable
    -                                "worktree_lease.LeaseTable.held_by",  # unreachable
    +                                reachable_pred,
    +                                unreachable_pred,
                                 )
                             )
                         )
    ```
    Pytest run:
    ```
    .....                                                                    [100%]
    5 passed in 13.55s
    ```
    Grep for literals in test file:
    ```sh
    $ grep -n -E "held_by|LeaseTable\.claim|preflight_host_capabilities" tests/test_run_finding_reachability.py
    # (exit code 1, no match)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of the pre-`8c460a9a1` test copy run from a temp path, showing `1 failed` with the assertion message, followed by the repaired node's `1 passed` on the same tree; pasted `git status --short` showing only the declared Scope-Paths.
  - Observed evidence:
    Pre-`8c460a9a1` test copy run on current tree:
    ```
    $ python3 -m pytest -o addopts="" -q /tmp/test_pre_8c460a9a1.py -k perturbation
    F                                                                        [100%]
    =================================== FAILURES ===================================
    _ TestRunFindingReachability.test_unreachable_binding_refusal_fires_under_perturbation _

    self = <test_pre_8c460a9a1.TestRunFindingReachability testMethod=test_unreachable_binding_refusal_fires_under_perturbation>

        def test_unreachable_binding_refusal_fires_under_perturbation(self) -> None:
            """Case (d): RC-UNREACHABLE-BINDING fires when a BOUND row has no reachable predicates."""
            orig = run_evidence.RUN_FINDING_CODES
            try:
                # Perturb a row to name only unreachable predicates
                # worktree_lease.LeaseTable.claim is unreachable
                perturbed_rows = []
                target_code = "RUN-HOST-CAPABILITY"
                for row in orig:
                    if row.code == target_code:
                        perturbed_rows.append(
                            row._replace(predicates=("worktree_lease.LeaseTable.claim",))
                        )
                    else:
                        perturbed_rows.append(row)
                run_evidence.RUN_FINDING_CODES = tuple(perturbed_rows)

                res = validate_finding_table()
    >           self.assertFalse(res.ok)
    E           AssertionError: True is not false

    /tmp/test_pre_8c460a9a1.py:159: AssertionError
    =========================== short test summary info ============================
    FAILED ../../../../../../../tmp/test_pre_8c460a9a1.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation
    1 failed, 4 deselected in 173.10s (0:02:53)
    ```
    Repaired test node run on current tree:
    ```
    $ python3 -m pytest -o addopts="" -q tests/test_run_finding_reachability.py -k perturbation
    .                                                                        [100%]
    NOTE: 4 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    1 passed, 4 deselected in 9.64s
    ```
    `git status --short`:
    ```
     M tests/test_run_finding_reachability.py
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/run_evidence.py` limited to docstring lines in `prove_predicate_reachability`, showing consequence 2 no longer asserts `LeaseTable.claim` is unreachable and the replacement is dated.
  - Observed evidence:
    `git diff agent_workflows/run_evidence.py`:
    ```diff
    diff --git a/agent_workflows/run_evidence.py b/agent_workflows/run_evidence.py
    index 08d43706a..52f842235 100644
    --- a/agent_workflows/run_evidence.py
    +++ b/agent_workflows/run_evidence.py
    @@ -1910,8 +1910,10 @@ def prove_predicate_reachability(

         Two known consequences of this design:
           1. A method name shared by an unrelated class creates a false edge (over-approximation).
    -      2. ``worktree_lease.LeaseTable.claim`` is reported unreachable with zero real ``.claim(`` call sites
    -         anywhere in the package, which is a true negative and not a limitation.
    +      2. A local variable or keyword argument matching a defined method name creates a false edge
    +         (over-approximation); for example, ``worktree_lease.LeaseTable.claim`` is reported reachable
    +         (measured 2026-10-12) via the ``claim`` local in ``verifier_corroboration.match_claims_to_observed``
    +         despite having zero real ``.claim(`` call sites in the package.
         """
         if entrypoints is None:
             ep_tuple = DEFAULT_ENTRYPOINT_MODULES
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted bare-suite summary line and `FAILED` lines after the edit, beside the E-01 base failing set, showing no new node id and the perturbation test absent; for any post-only failure, the pasted single-node re-run output.
  - Observed evidence:
    Base failing set (E-01): `set()` (empty set; 7598 passed, 2 skipped, 3 warnings in 990.85s).
    Post-edit bare suite run:
    ```
    7598 passed, 2 skipped, 3 warnings in 799.65s (0:13:19)
    ```
    Post-edit failing set: `set()` (empty set; 0 failures).
    New failing node-ids: none.
    `test_unreachable_binding_refusal_fires_under_perturbation` absent from failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`; do not push; no tag or release. Paste actual runner output, never summaries. The negative control in E-03 must NOT write over a tracked file: write the old test copy to a temp directory. Do not fix other `wc5c5e` nodes here.

POST-GATE LIFECYCLE. Run `aw ipd begin` before implementing. When dispatched by `aw oc run` / `aw agy run`, the runner performs finalize, so do not run `aw ipd finalize` yourself; when executed by hand, run `aw ipd finalize` after every `V-*` reads `pass`. Never hand-`git mv` the plan to `executed/`. Confirm `aw ipd lint --phase pre-transition` conforms before the transition. The plan carries the item's `- Blocks-Release: next`; backlog `8jeh4x` closes `done` via the From-Backlog handoff once this plan is executed.

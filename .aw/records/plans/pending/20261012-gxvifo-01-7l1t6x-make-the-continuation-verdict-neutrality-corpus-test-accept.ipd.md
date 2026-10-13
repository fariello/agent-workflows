# IPD: Make the continuation verdict-neutrality corpus test accept a delta that only removes evidence-emptiness diagnostics

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` fails on the live plan corpus (552 plan/checkpoint pairs) whenever the `livecorpus` subset runs (`make test-all`, release-review), because its legitimate-adoption exemption is stricter than the property it claims to assert.
- Scope: Correct the exemption predicate inside that one test so it accepts exactly the deltas continuation parsing is meant to produce (removal of evidence-emptiness diagnostics only, nothing added), and keep it refusing every other verdict change. No production code change.
- Scope-Paths: tests/test_ipd_lint.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: gxvifo
- Blocks-Release: next
- Set: gxvifo
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 7l1t6x
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Re-measured at HEAD fee276097: 555 deltas all removed-only-evidence, error->error; Execution-state mutation adds diagnostics.

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog gxvifo; review-ready.

## Goal

Make `test_corpus_verdict_neutrality_delta` pass on the live corpus by asserting the property its own inline comment intends ("Legitimate adoption of continuation parsing": continuation read changes no verdict except by satisfying evidence requirements that one-line read wrongly reported empty), and make its docstring say so (today the docstring states strict pair EQUALITY, which the existing exemption already contradicts), so the `livecorpus` subset stops carrying a known-red test into `make test-all` and release-review.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 Record the pre-change failure: run `python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"` and capture the summary line and the mismatch count.
  - Depends on: none
  - Expected outcome: the test FAILS with `continuation read changed verdict on N plan/checkpoint pairs` (N was 552 at authoring), proving the defect reproduces before the edit.
  - Execution state: performed

### Task group 2: Correct the exemption predicate

- [x] E-02 In `ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta`, replace the exemption condition (currently: widened disposition is `S.DISPOSITION_CONFORMING` AND widened has zero diagnostics AND one-line messages equal the evidence-emptiness set) with a MULTISET comparison of the two message lists (`collections.Counter`), so a changed count of a repeated message is a change: with `added = Counter(widened) - Counter(oneline)` and `removed = Counter(oneline) - Counter(widened)`, require (a) `added` is empty (nothing ADDED), (b) every message in `removed` contains `requires nonempty Observed evidence` or `empty Observed evidence at pre-transition` (only evidence-emptiness REMOVED), and (c) the widened disposition EQUALS the one-line disposition or is `S.DISPOSITION_CONFORMING`. There is NO warning disposition: `ipd_schema.DISPOSITIONS` is exactly `conforming`, `quarantined`, `legacy/not evaluated`, `error`, so do not invent a severity order. Any pair failing (a), (b) or (c) is still appended to `mismatches`. Rewrite BOTH the inline comment and the test DOCSTRING to state this property (the docstring's "equals the pair" sentence is what is being corrected), and render at most the first 10 mismatches in the assertion message so a failure stays readable.
  - Depends on: E-01
  - Expected outcome: the test asserts "continuation read only removes evidence-emptiness diagnostics and never adds a diagnostic or worsens a disposition", which is the docstring's property, and no longer requires an unrelated diagnostic (for example `status 'executed' is incompatible with checkpoint 'author'`) to be absent.
  - Execution state: performed

### Task group 3: Prove it still catches a real regression

- [x] E-03 Verify the predicate still refuses a genuine verdict change, without adding a code-pinning test: temporarily (uncommitted, reverted before commit) make `agent_workflows/ipd_lint.py` `_CONTINUATION_SUBFIELDS` also include `Execution state` (the narrowness-control field of row (e)), run the test, observe it FAIL with a nonzero mismatch count, then revert with `git checkout -- agent_workflows/ipd_lint.py` and confirm. PRECONDITION: before mutating, `git diff --name-only -- agent_workflows/ipd_lint.py` must print nothing, so the revert cannot discard anyone else's edit; if it prints the path, mutate in memory instead (a scratch script that `mock.patch`es `_CONTINUATION_SUBFIELDS` for the widened read and replicates the predicate) and record that. Confirm `git diff --name-only` lists only `tests/test_ipd_lint.py`. Measured at review (HEAD `fee276097`, in-memory `mock.patch` equivalent): this mutation DOES produce a delta that fails predicate (a), e.g. `20260810-awphysical-12-pszk6x-...` at `author` ADDS `E-06: unknown execution state 'performed - Execution note ...'` and `V-06: validation 'pass' requires execution state 'performed'`. If at execution it produces no delta, use instead a temporary mutation that adds a diagnostic under widened parsing and record which mutation was used.
  - Depends on: E-02
  - Expected outcome: a deliberately broken continuation reader turns the test red; the production file is unchanged afterwards.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `pyproject.toml` `[tool.pytest.ini_options]` defines the `livecorpus` marker and `addopts` deselects `not slow and not livecorpus`, so a bare `python3 -m pytest` does not run this test; it runs in `make test-all` and release-review (marker description text "they still run in `make test-all`, in release-review").
- The marker half of the backlog item is already fixed: commit `7295f0a60` ("... mark test_corpus_verdict_neutrality_delta livecorpus") added `@pytest.mark.livecorpus` above `def test_corpus_verdict_neutrality_delta`. The remaining defect is the failure itself.
- `agent_workflows/ipd_lint.py` defines `_CONTINUATION_SUBFIELDS: FrozenSet[str]`, which the test monkeypatches to `frozenset()` to obtain the one-line read.
- Tests must exercise behavior and not pin source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); this plan edits only an outcome test's predicate and its mutation check is a transient manual verification, not a committed source-reading test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Marker already present. | `git log -L` on the decorator shows `7295f0a60` adding `@pytest.mark.livecorpus`. |
| F-2 | Test still fails under the livecorpus subset. | `python3 -m pytest -o addopts="" -q -m livecorpus ...::test_corpus_verdict_neutrality_delta` at HEAD `d9afd242b`: `1 failed in 21.57s`, `continuation read changed verdict on 552 plan/checkpoint pairs`. |
| F-3 | Every delta only REMOVES evidence-emptiness diagnostics and adds none, and none changes the disposition. The population is LIVE and grows as plans are executed (552 at authoring, 555 at review), so the bar is the property, not a count. | Authoring-time classification script: `Counter({'removed-only-evidence': 552})`, zero `other`. Re-run at review, HEAD `fee276097`, multiset comparison over 1441 plans: `Counter({'removed-only-evidence': 555})`, dispositions `Counter({('error', 'error'): 555})`, zero duplicate-message pairs, zero advisory differences. |
| F-4 | Root cause is the exemption's extra conjuncts. | First mismatch: `20260929-ct1n04-01-xs557y-...` at `author`: widened `('error', ["status 'executed' is incompatible with checkpoint 'author'"])` vs one-line `('error', [six "requires nonempty Observed evidence" messages, same status message])`. The exemption demands widened be conforming with zero diagnostics and the one-line set be ONLY evidence messages; the unrelated checkpoint-status diagnostic present in BOTH defeats it. |

## Proposed changes (ordered, validatable)

1. E-01: reproduce and record the failure (validated by V-01).
2. E-02: replace the exemption with the added-nothing / removed-only-evidence / no-worse-disposition predicate (validated by V-02).
3. E-03: transient mutation proves the test still catches a broken reader (validated by V-03).

## Deferred / out of scope (with reason)

- Any change to `agent_workflows/ipd_lint.py`: the parser behaves correctly (F-3); only the test's predicate is wrong.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Re-linting or editing executed plans to make them conform at `author`: forbidden by the execution contract (executed plans' records are immutable) and unrelated to the property.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Removing the `livecorpus` marker: the marker reasoning in `pyproject.toml` still holds.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item's marker half is already done (F-1) and this plan covers the remaining failure.

## Required tests / validation

- V-01: pre-change targeted run fails (pasted output).
- V-02: post-change targeted run `python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"` passes, plus `python3 -m pytest -o addopts="" -q tests/test_ipd_lint.py -k ContinuationSubfieldOutcomeTests` passes, plus a bare `python3 -m pytest` whose failure set is compared by node id against a pre-change bare run (no new failures).
- V-03: transient mutation run fails, and `git diff --name-only` after revert lists only `tests/test_ipd_lint.py`.

## Spec / documentation sync

N/A: no spec governs this test's predicate and no user-facing behavior changes.

## Open questions

### OQ-01: Should an unrelated diagnostic present in both reads block the exemption?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The test's inline comment states the intended exemption is "Legitimate adoption of continuation parsing" (the docstring's literal equality claim is already contradicted by that exemption and is rewritten by E-02); a diagnostic present identically in both reads (F-4) is not a change caused by continuation parsing. Resolved from the test's own docstring and F-3/F-4 evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output of the pre-change targeted livecorpus run showing `1 failed` and the `continuation read changed verdict on N plan/checkpoint pairs` message, with the HEAD commit hash it ran at.
  - Observed evidence:
    Ran at HEAD commit `6bca0b4241cfe93f73e43d9330007f22b3ee3b4d`:
    ```
    $ python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"
    F                                                                        [100%]
    =================================== FAILURES ===================================
    ____ ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta _____

    self = <tests.test_ipd_lint.ContinuationSubfieldOutcomeTests testMethod=test_corpus_verdict_neutrality_delta>
    ...
    >       self.assertEqual(
                mismatches,
                [],
                f"continuation read changed verdict on {len(mismatches)} plan/checkpoint pairs",
            )
    E       AssertionError: Lists differ: [('20260929-ct1n04-01-xs557y-group-the-che[411688 chars]']))] != []
    E
    E       First list contains 601 additional elements.
    E       ...
    E       Diff is 451577 characters long. Set self.maxDiff to None to see it. : continuation read changed verdict on 601 plan/checkpoint pairs

    tests/test_ipd_lint.py:4168: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed in 108.51s (0:01:48)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff tests/test_ipd_lint.py` showing the new multiset predicate, the (c) equal-or-conforming disposition check, and the rewritten docstring; pasted output of the post-change targeted livecorpus run showing `1 passed`; pasted output of the `-k ContinuationSubfieldOutcomeTests` run showing all passed; pasted summary lines of pre-change and post-change bare `python3 -m pytest` runs with their failing node-id sets compared (post-change set is a subset of pre-change set).
  - Observed evidence:
    1. Diff of `tests/test_ipd_lint.py`:
    ```diff
    diff --git a/tests/test_ipd_lint.py b/tests/test_ipd_lint.py
    index fb60af3b1..adb6ccb1c 100644
    --- a/tests/test_ipd_lint.py
    +++ b/tests/test_ipd_lint.py
    @@ -4109,13 +4109,15 @@ class ContinuationSubfieldOutcomeTests(unittest.TestCase):
         @pytest.mark.livecorpus
         @pytest.mark.timeout(180)
         def test_corpus_verdict_neutrality_delta(self):
    -        """E-03: asserting the PROPERTY that continuation read changes no tracked plan's verdict.
    +        """Asserts the property that continuation read changes no tracked plan's verdict.

             Asserts delta neutrality across (author, review-finalize, pre-transition) checkpoints:
    -        for every tracked plan, (disposition, diagnostics) with continuation read equals
    -        the pair computed with one-line read (narrowly monkeypatching _CONTINUATION_SUBFIELDS to empty).
    -        Does NOT assert absolute absence of empty Observed evidence (188+ plans report it legitimately).
    -        """
    +        for every tracked plan, continuation read only removes evidence-emptiness diagnostics
    +        and never adds a diagnostic or worsens a disposition compared with one-line read
    +        (narrowly monkeypatching _CONTINUATION_SUBFIELDS to empty). Does NOT assert absolute
    +        absence of empty Observed evidence (188+ plans report it legitimately).
    +        """
    +        from collections import Counter
             from unittest import mock

             plans = sorted((REPO_ROOT / SOURCE_PLANS).rglob("*.ipd.md"))
    @@ -4147,28 +4149,35 @@ class ContinuationSubfieldOutcomeTests(unittest.TestCase):
                         [d.message for d in res_oneline.diagnostics],
                     )
                     if pair_widened != pair_oneline:
    -                    # Legitimate adoption of continuation parsing: a plan whose one-line
    -                    # read failed strictly due to missing evidence on pass rows, and whose
    -                    # continuation read satisfies all evidence requirements (conforming).
    -                    expected_baseline_msgs = {
    -                        d.message
    -                        for d in res_oneline.diagnostics
    -                        if "requires nonempty Observed evidence" in d.message
    -                        or "empty Observed evidence at pre-transition" in d.message
    -                    }
    +                    # Legitimate adoption of continuation parsing: continuation read only
    +                    # removes evidence-emptiness diagnostics and never adds a diagnostic or
    +                    # worsens a disposition.
    +                    added = Counter(pair_widened[1]) - Counter(pair_oneline[1])
    +                    removed = Counter(pair_oneline[1]) - Counter(pair_widened[1])
                         if (
    -                        res_widened.disposition == S.DISPOSITION_CONFORMING
    -                        and len(res_widened.diagnostics) == 0
    -                        and set(d.message for d in res_oneline.diagnostics)
    -                        == expected_baseline_msgs
    +                        not added
    +                        and all(
    +                            "requires nonempty Observed evidence" in msg
    +                            or "empty Observed evidence at pre-transition" in msg
    +                            for msg in removed
    +                        )
    +                        and (
    +                            res_widened.disposition == res_oneline.disposition
    +                            or res_widened.disposition == S.DISPOSITION_CONFORMING
    +                        )
                         ):
                             continue
                         mismatches.append((plan.name, cp, pair_widened, pair_oneline))

    +        rendered = "\n".join(
    +            f"  {name} ({cp}):\n    widened: {pw}\n    oneline: {po}"
    +            for name, cp, pw, po in mismatches[:10]
    +        )
             self.assertEqual(
                 mismatches,
                 [],
    -            f"continuation read changed verdict on {len(mismatches)} plan/checkpoint pairs",
    +            f"continuation read changed verdict on {len(mismatches)} plan/checkpoint pairs"
    +            + (f" (first {min(len(mismatches), 10)}):\n{rendered}" if mismatches else ""),
             )
    ```

    2. Post-change targeted livecorpus run:
    ```
    $ python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"
    .                                                                        [100%]
    1 passed in 45.03s
    ```

    3. ContinuationSubfieldOutcomeTests run:
    ```
    $ python3 -m pytest -o addopts="" -q tests/test_ipd_lint.py -k ContinuationSubfieldOutcomeTests
    ..........                                                               [100%]
    NOTE: 66 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    10 passed, 66 deselected in 53.85s
    ```

    4. Bare pytest runs pre-change vs post-change:
    Pre-change summary:
    `7598 passed, 2 skipped, 3 warnings in 897.68s (0:14:57)`
    Failing node-id set: empty `set()`

    Post-change summary:
    `7598 passed, 2 skipped, 3 warnings in 809.27s (0:13:29)`
    Failing node-id set: empty `set()`

    Comparison: post-change failing node-id set `set()` is a subset of pre-change failing node-id set `set()`. Zero new failures.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of the targeted livecorpus run under the transient mutation showing `1 failed` with a nonzero mismatch count, the mutation used, and pasted `git diff --name-only` after revert listing only `tests/test_ipd_lint.py`.
  - Observed evidence:
    1. Transient mutation in `agent_workflows/ipd_lint.py`:
    ```python
    _CONTINUATION_SUBFIELDS: FrozenSet[str] = frozenset(
        ("Observed evidence", "Execution note", "Execution state")
    )
    ```

    2. Output of targeted livecorpus run under the transient mutation:
    ```
    $ python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"
    F                                                                        [100%]
    =================================== FAILURES ===================================
    ____ ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta _____
    ...
    E       Diff is 750612 characters long. Set self.maxDiff to None to see it. : continuation read changed verdict on 156 plan/checkpoint pairs (first 10):
    ...
    =========================== short test summary info ============================
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed in 57.98s
    ```

    3. Revert and git diff --name-only check:
    ```
    $ git checkout -- agent_workflows/ipd_lint.py
    $ git diff --name-only
    tests/test_ipd_lint.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved; none remain. `- Scope-Paths:` is a declaration that finalize reconciles: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`. E-03's mutation of `agent_workflows/ipd_lint.py` is transient and MUST NOT be committed. Commit only `tests/test_ipd_lint.py` through `aw commit 7l1t6x -- tests/test_ipd_lint.py` (never `git add -A`), and never push. Paste the ACTUAL runner output for every claim that a test passed or failed. After every `E-*` reads `performed`, every `V-*` reads `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`. In a hand-driven execution the executor runs `aw ipd finalize 7l1t6x --actor <agent/model> --message <summary> --apply`. Backlog `gxvifo` (and the `Blocks-Release: next` gate this plan carries) is advanced by the runner's backlog-close step, never by hand.

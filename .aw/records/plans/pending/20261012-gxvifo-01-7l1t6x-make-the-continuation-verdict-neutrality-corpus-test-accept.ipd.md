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

- [ ] E-01 Record the pre-change failure: run `python3 -m pytest -o addopts="" -q -m livecorpus "tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta"` and capture the summary line and the mismatch count.
  - Depends on: none
  - Expected outcome: the test FAILS with `continuation read changed verdict on N plan/checkpoint pairs` (N was 552 at authoring), proving the defect reproduces before the edit.
  - Execution state: pending

### Task group 2: Correct the exemption predicate

- [ ] E-02 In `ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta`, replace the exemption condition (currently: widened disposition is `S.DISPOSITION_CONFORMING` AND widened has zero diagnostics AND one-line messages equal the evidence-emptiness set) with a MULTISET comparison of the two message lists (`collections.Counter`), so a changed count of a repeated message is a change: with `added = Counter(widened) - Counter(oneline)` and `removed = Counter(oneline) - Counter(widened)`, require (a) `added` is empty (nothing ADDED), (b) every message in `removed` contains `requires nonempty Observed evidence` or `empty Observed evidence at pre-transition` (only evidence-emptiness REMOVED), and (c) the widened disposition EQUALS the one-line disposition or is `S.DISPOSITION_CONFORMING`. There is NO warning disposition: `ipd_schema.DISPOSITIONS` is exactly `conforming`, `quarantined`, `legacy/not evaluated`, `error`, so do not invent a severity order. Any pair failing (a), (b) or (c) is still appended to `mismatches`. Rewrite BOTH the inline comment and the test DOCSTRING to state this property (the docstring's "equals the pair" sentence is what is being corrected), and render at most the first 10 mismatches in the assertion message so a failure stays readable.
  - Depends on: E-01
  - Expected outcome: the test asserts "continuation read only removes evidence-emptiness diagnostics and never adds a diagnostic or worsens a disposition", which is the docstring's property, and no longer requires an unrelated diagnostic (for example `status 'executed' is incompatible with checkpoint 'author'`) to be absent.
  - Execution state: pending

### Task group 3: Prove it still catches a real regression

- [ ] E-03 Verify the predicate still refuses a genuine verdict change, without adding a code-pinning test: temporarily (uncommitted, reverted before commit) make `agent_workflows/ipd_lint.py` `_CONTINUATION_SUBFIELDS` also include `Execution state` (the narrowness-control field of row (e)), run the test, observe it FAIL with a nonzero mismatch count, then revert with `git checkout -- agent_workflows/ipd_lint.py` and confirm. PRECONDITION: before mutating, `git diff --name-only -- agent_workflows/ipd_lint.py` must print nothing, so the revert cannot discard anyone else's edit; if it prints the path, mutate in memory instead (a scratch script that `mock.patch`es `_CONTINUATION_SUBFIELDS` for the widened read and replicates the predicate) and record that. Confirm `git diff --name-only` lists only `tests/test_ipd_lint.py`. Measured at review (HEAD `fee276097`, in-memory `mock.patch` equivalent): this mutation DOES produce a delta that fails predicate (a), e.g. `20260810-awphysical-12-pszk6x-...` at `author` ADDS `E-06: unknown execution state 'performed - Execution note ...'` and `V-06: validation 'pass' requires execution state 'performed'`. If at execution it produces no delta, use instead a temporary mutation that adds a diagnostic under widened parsing and record which mutation was used.
  - Depends on: E-02
  - Expected outcome: a deliberately broken continuation reader turns the test red; the production file is unchanged afterwards.
  - Execution state: pending

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
- Re-linting or editing executed plans to make them conform at `author`: forbidden by the execution contract (executed plans' records are immutable) and unrelated to the property.
- Removing the `livecorpus` marker: the marker reasoning in `pyproject.toml` still holds.

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

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output of the pre-change targeted livecorpus run showing `1 failed` and the `continuation read changed verdict on N plan/checkpoint pairs` message, with the HEAD commit hash it ran at.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff tests/test_ipd_lint.py` showing the new multiset predicate, the (c) equal-or-conforming disposition check, and the rewritten docstring; pasted output of the post-change targeted livecorpus run showing `1 passed`; pasted output of the `-k ContinuationSubfieldOutcomeTests` run showing all passed; pasted summary lines of pre-change and post-change bare `python3 -m pytest` runs with their failing node-id sets compared (post-change set is a subset of pre-change set).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of the targeted livecorpus run under the transient mutation showing `1 failed` with a nonzero mismatch count, the mutation used, and pasted `git diff --name-only` after revert listing only `tests/test_ipd_lint.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved; none remain. `- Scope-Paths:` is a declaration that finalize reconciles: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`. E-03's mutation of `agent_workflows/ipd_lint.py` is transient and MUST NOT be committed. Commit only `tests/test_ipd_lint.py` through `aw commit 7l1t6x -- tests/test_ipd_lint.py` (never `git add -A`), and never push. Paste the ACTUAL runner output for every claim that a test passed or failed. After every `E-*` reads `performed`, every `V-*` reads `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`. In a hand-driven execution the executor runs `aw ipd finalize 7l1t6x --actor <agent/model> --message <summary> --apply`. Backlog `gxvifo` (and the `Blocks-Release: next` gate this plan carries) is advanced by the runner's backlog-close step, never by hand.

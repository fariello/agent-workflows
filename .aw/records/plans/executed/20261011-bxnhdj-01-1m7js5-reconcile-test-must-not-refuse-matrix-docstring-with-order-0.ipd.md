# IPD: Reconcile test_must_not_refuse_matrix docstring with Order 02 plans selector routing

- Date: 2026-10-11
- Kind: child
- Concern: `tests/test_selector_type_containment.py::test_must_not_refuse_matrix` was authored (awrenamesel Order 01) to PIN a pre-existing refusal (`rc == 2`, `no plan has Id`) for path selectors on `aw rename plans`, and Order 02 (`87m438`) routed plans through the shared selector resolver so that refusal no longer happens. The assertions were already flipped in commit `8c460a9a1`, but the test's docstring still states the obsolete rc=2 contract, so the test documents a behavior it no longer asserts.
- Scope: Bring the docstring of `test_must_not_refuse_matrix` into agreement with its (already correct) assertions for the plans arm, and verify by running the test that relpath, abspath and id6 selectors all reach the rename preview for plans. No production code change.
- Scope-Paths: tests/test_selector_type_containment.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: bxnhdj
- Set: bxnhdj
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 1m7js5

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 1m7js5 verified (set bxnhdj, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored review-ready from backlog `bxnhdj`.

## Goal

Make `test_must_not_refuse_matrix` self-consistent: its docstring must describe the plans arm as "id6, repo-relative path and absolute path all reach rename preview (rc=0)", matching the assertions that Order 02 (`87m438`) made true and that commit `8c460a9a1` already encoded, so the backlog item's reconciliation is complete and the test no longer advertises a pinned refusal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 Run `python3 -m pytest -o addopts="" -q tests/test_selector_type_containment.py` and the bare suite `python3 -m pytest` at the execution base BEFORE editing, recording the narrowed summary line and the bare-suite `FAILED` node-id set (this is the base set E-03 compares against), and confirm (by reading the plans arm of `test_must_not_refuse_matrix`, the block after the comment `# Plans: id6, relpath, and abspath selectors succeed`) that all three plans assertions expect `rc == 0 and "would rename" in out`. If the assertions at your base instead still expect `rc == 2`, ALSO flip those two assertions to `rc == 0 and "would rename" in out` in E-02 (the original reconciliation the backlog item asked for).
  - Depends on: none
  - Expected outcome: pasted pre-edit narrowed pytest summary line, the pre-edit bare-suite summary line plus its `FAILED` node-id set, and a statement of which form the plans assertions are in.
  - Execution state: performed

### Task group 2: Reconcile the docstring

- [x] E-02 Edit the docstring of `test_must_not_refuse_matrix` in `tests/test_selector_type_containment.py`: replace the three plans lines (`(c) id6 reaches rename preview (rc=0)`, `(a) repo-relative path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)`, `(b) absolute path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)`) with lines stating that for plans (a) repo-relative path, (b) absolute path and (c) id6 all reach rename preview (rc=0), now that Order 02 (`87m438`) routes plans through the shared selector resolver. Do not change any other test or any assertion other than the conditional flip from E-01.
  - Depends on: E-01
  - Expected outcome: `rg -n "no plan has Id|pins pre-existing refusal" tests/test_selector_type_containment.py` returns no match; the docstring's plans section names rc=0 for all three selector forms.
  - Execution state: performed

### Task group 3: Verify

- [x] E-03 Re-run `python3 -m pytest -o addopts="" -q tests/test_selector_type_containment.py` and then the bare suite `python3 -m pytest`, and compare the bare-suite failing node-id SET against the base set E-01 measured on the unmodified base (not against any count in this plan). A node id failing in both runs is pre-existing and not this plan's concern; a node failing only after the edit must be investigated (a docstring edit cannot plausibly cause it, so re-run it once to rule out flakiness and record the outcome).
  - Depends on: E-02
  - Expected outcome: the containment file passes in full; the bare suite introduces no newly failing node id, and `test_must_not_refuse_matrix` is absent from the failure list.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite runs BARE as `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md, repository development contract).
- Tests assert behavior, never source text (GUIDING_PRINCIPLES P16); this plan edits a docstring only and adds no source-reading test.
- Baselines compare failing SETS by node id, never counts (precedent: executed plans `q4uifc` F-10, `wdyz5n` F-06).
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The test's assertions were already reconciled. Commit `8c460a9a1` ("Fix baseline test failures on main (... selector containment test)") replaced the two `rc == 2 and "no plan has Id" in out` assertions with `rc == 0 and "would rename" in out` and changed the comment to `# Plans: id6, relpath, and abspath selectors succeed`. | `git show 8c460a9a1 -- tests/test_selector_type_containment.py` |
| F-02 | The docstring was NOT updated by that commit and still reads `(a) repo-relative path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)` and the same for `(b) absolute path`. This is the residual drift this plan removes. | Read of `test_must_not_refuse_matrix` docstring in `tests/test_selector_type_containment.py` at HEAD `255f09f98`. |
| F-03 | The file passes at authoring HEAD: `10 passed in 3.31s` via `python3 -m pytest -o addopts="" -q tests/test_selector_type_containment.py`. | Run in this lane before any edit. |
| F-04 | The origin of the item: executed plan `87m438` (awrenamesel Order 02) records "Defect finding: `tests/test_selector_type_containment.py::test_must_not_refuse_matrix` authored in Order 01 pinned the old exit 2 failure for plans; recorded durably in backlog item `bxnhdj`". | `.aw/records/plans/executed/20260929-awrenamesel-02-87m438-...ipd.md` |

## Proposed changes (ordered, validatable)

1. (E-01) Measure baseline; confirm assertion form.
2. (E-02) Rewrite the plans section of the docstring to the rc=0 contract (and conditionally flip assertions if a base predates `8c460a9a1`).
3. (E-03) Re-run the file and the bare suite; compare failing sets.

## Deferred / out of scope (with reason)

- Closing backlog `bxnhdj`: it is already `graduated` (run run-20261012T005606Z-2321569); moving it to `done` after this plan executes is the runner/maintainer's act, not this plan's.
  - Carrier: bxnhdj
- Other pre-existing suite failures (e.g. carriers `6bolin`, `8jeh4x`, `wc5c5e`): owned by their own items.
  - Carrier: 6bolin, 8jeh4x, wc5c5e

## Scope check

- Over-scope: none.
- Under-scope: none; the only remaining divergence between the test and the Order 02 behavior is the docstring (F-01, F-02).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_selector_type_containment.py` passes in full after the edit (performed by this plan, E-03).
- Bare `python3 -m pytest` shows no newly failing node id versus the base set measured in E-01 (performed by this plan, E-01 and E-03).

## Spec / documentation sync

N/A: the change is a test docstring; no spec describes this test's docstring and no user-facing documentation changes.

## Open questions

None. The only candidate question (whether the assertions still need flipping) is answered by repository evidence (F-01) and handled conditionally in E-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-edit pytest summary line for `tests/test_selector_type_containment.py`, the pasted pre-edit bare-suite summary line and `FAILED` node-id set, and the pasted plans-arm assertion lines from the base.
  - Observed evidence:
    Pre-edit narrowed pytest summary line:
    ```
    10 passed in 18.83s
    ```
    Pre-edit bare-suite summary line:
    ```
    7515 passed, 2 skipped, 3 warnings in 1250.79s (0:20:50)
    ```
    Pre-edit bare-suite FAILED node-id set:
    `set()` (0 failed tests).
    Base plans-arm assertions in `tests/test_selector_type_containment.py` (lines 388-396):
    ```python
        # Plans: id6, relpath, and abspath selectors succeed
        rc, out = run_cli("rename", "plans", "pl0001", "--slug", "newslug")
        assert rc == 0 and "would rename" in out, f"plans id6 failed: rc={rc}, {out}"
        rc, out = run_cli(
            "rename", "plans", str(plan.relative_to(repo)), "--slug", "newslug"
        )
        assert rc == 0 and "would rename" in out, f"plans relpath failed: rc={rc}, {out}"
        rc, out = run_cli("rename", "plans", str(plan.resolve()), "--slug", "newslug")
        assert rc == 0 and "would rename" in out, f"plans abspath failed: rc={rc}, {out}"
    ```
    Confirmed all three plans assertions already expect `rc == 0 and "would rename" in out`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- tests/test_selector_type_containment.py` showing only docstring lines changed (plus assertion lines only if E-01 found the rc=2 form), and pasted empty output of `rg -n "no plan has Id|pins pre-existing refusal" tests/test_selector_type_containment.py`.
  - Observed evidence:
    Pasted `git diff -- tests/test_selector_type_containment.py`:
    ```diff
    diff --git a/tests/test_selector_type_containment.py b/tests/test_selector_type_containment.py
    index dd5f1fe24..5ff423e57 100644
    --- a/tests/test_selector_type_containment.py
    +++ b/tests/test_selector_type_containment.py
    @@ -287,9 +287,10 @@ def test_must_not_refuse_matrix(temp_git_repo: Path):
           In selectors.resolve_for_mutation: (a) repo-relative path, (b) absolute path, (c) id6 all resolve.
           In CLI aw rename research: (c) id6 reaches rename preview (rc=0).
         For plans:
    +      (a) repo-relative path reaches rename preview (rc=0)
    +      (b) absolute path reaches rename preview (rc=0)
           (c) id6 reaches rename preview (rc=0)
    -      (a) repo-relative path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)
    -      (b) absolute path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)
    +      (now that Order 02 (87m438) routes plans through the shared selector resolver)
         """
         repo = temp_git_repo
    ```
    Pasted output of `rg -n "no plan has Id|pins pre-existing refusal" tests/test_selector_type_containment.py`:
    ```
    (exit code 1, empty output)
    ```
    Only docstring lines changed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted post-edit summary line of the narrowed run showing all tests in the file passed, and the pasted bare-suite summary plus `FAILED` lines alongside the E-01 base failing set, showing no new node id and `test_must_not_refuse_matrix` absent.
  - Observed evidence:
    Post-edit narrowed pytest run:
    ```
    10 passed in 2.26s
    ```
    Post-edit bare-suite run:
    ```
    7515 passed, 2 skipped, 3 warnings in 1133.32s (0:18:53)
    ```
    Comparison of failing node-id sets:
    Pre-edit failing set (E-01): `set()`
    Post-edit failing set (E-03): `set()`
    Newly failing node IDs: none (0)
    `test_must_not_refuse_matrix` passed and absent from failure list.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING: a docstring-only edit to one test file so that `test_must_not_refuse_matrix` stops describing a pinned rc=2 refusal for plans path selectors that Order 02 (`87m438`) removed and that the assertions (since `8c460a9a1`) no longer check. No production code changes.

EXECUTION CONTRACT. Commit only `tests/test_selector_type_containment.py` through `aw commit <plan> -- tests/test_selector_type_containment.py`; never `git add -A`, never push. Paste ACTUAL runner output for every `V-*`. Do not fix other items' failures here.

POST-GATE LIFECYCLE. Run `aw ipd begin` before implementing. When dispatched by `aw oc run` / `aw agy run`, the runner performs finalize, so do not run `aw ipd finalize` yourself; when executed by hand, run `aw ipd finalize` after every `V-*` reads `pass`. Confirm `aw ipd lint --phase pre-transition` conforms before the transition. Backlog `bxnhdj` carries no `- Blocks-Release:`, so none is inherited.

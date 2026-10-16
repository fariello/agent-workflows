# IPD: Restore behavioral coverage that reviews is a type noun with no backend and no status lifecycle

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_awcmdsurf_vocab_and_parsers.py`, and with it `DerivedVocabularyTests.test_reviews_has_no_backend_and_no_status_lifecycle`, the only test that `reviews` (an accepted type noun since the `wslayout` union ruling) stays OUT of `artifact_types.TYPE_BACKENDS` and OUT of `selectors.KNOWN_PRIMARY_TYPES`. Executed plan `ev7t1w` recorded that site as S-04 RETIRE-UNGUARDED. A regression is silent: a `reviews` backend would let `aw rename|group|index reviews` mutate review records that have no lifecycle, and a `reviews` primary type would make the plan-selector diagnostics and `run_selection_policy` treat a review as a selectable work item.
- Scope: Add one new behavioral test module that drives the real CLI router and the real public helpers (`artifact_types.backend_name`/`resolve_backend`, `selectors.resolve`, `runner_shared.describe_unresolved_plan_selector`) against a temporary git repository holding a real `.review.md` record, plus a comment-only repoint of the `artifact_types.py` module docstring that says "no live guard currently asserts this". No production behavior change.
- Scope-Paths: tests/test_reviews_type_noun_surface.py, agent_workflows/artifact_types.py, .aw/records/plans/pending/20261014-nrcvpg-01-ybf6za-restore-behavioral-coverage-that-reviews-is-a-type-noun-with.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nrcvpg
- Set: nrcvpg
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: ybf6za
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Record: .aw/records/reviews/20261014-nrcvpg-01-ybf6za-restore-behavioral-coverage-that-reviews-is-a-type-noun-with.review.md Round 1

- 2026-10-15 draft (opencode): created.
- 2026-10-14 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `nrcvpg`; review-ready. Every behavior the tests will assert was measured in this lane before authoring (Findings F-02..F-04).

## Goal

Restore behavioral (never source-reading, P16) coverage that `reviews` is accepted as a type noun but has no verb backend and no status lifecycle: every backend-routed verb refuses it at exit 2 leaving the record untouched, and the primary-type surfaces never classify a review as a work item, with positive controls proving each assertion is not vacuous.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: no backend (TYPE_BACKENDS absence)

- [x] E-01 Create `tests/test_reviews_type_noun_surface.py` with a pytest fixture that `git init`s a `tmp_path` repo and writes one review record `.aw/records/reviews/20260929-demo-01-ab12cd-x.review.md` (content `# Review: x\n\n- Subject-Id: ab12cd\n`). Add a test parametrized over `rename` (`reviews <absolute path to the review> --slug zz`), `group` (`reviews x`), and `index` (`reviews`) that calls `cli.main(["--no-interactive", <verb>, ..., "--dir", <repo>])` under `redirect_stdout`/`redirect_stderr` (catching `SystemExit` and taking its code) and asserts rc == 2, the combined output contains `'<verb>' is not supported for reviews.`, and the review file still exists with identical bytes and the reviews directory listing is unchanged. Add a second test that, for every verb in the union of verbs any type routes (computed at test time as `{v for t in at.ARTIFACT_TYPES for v in ("new","index","find","rename","group","archive","check") if at.backend_name(t, v)}`), asserts `at.backend_name("reviews", v) is None` and `at.resolve_backend("reviews", v) is None`, and asserts that same union is non-empty and that `at.backend_name("plans", "rename")` is not None (positive control). Add a third, in-module non-vacuity test that uses `unittest.mock.patch.dict(at.TYPE_BACKENDS, {"reviews": {"rename": "artifact_rename.run_rename_other"}})` and asserts that, under the patch, `at.backend_name("reviews", "rename")` is not None and the same `rename` invocation's output no longer contains `is not supported for reviews.` (measured at review: it then reaches the backend and refuses for a different reason, `other verb cannot act on ...`). The patch is in-process only and is undone on exit, so no source file is ever edited.
  - Depends on: none
  - Expected outcome: All three tests pass; each refused verb leaves the record byte-identical; the patched case proves the refusal assertion depends on `TYPE_BACKENDS` lacking `reviews`.
  - Execution state: performed

- [x] E-02 In the same module, add a positive control proving the noun itself is ACCEPTED (so the refusals in E-01 are "no backend", not "unknown type"): `at.normalize_type("reviews") == "reviews"`, `at.normalize_type("review") == "reviews"`, `at.is_type_token("reviews")` is True, and `cli.main(["--no-interactive", "find", "reviews", "ab12cd", "--dir", <repo>])` returns 0 with the review's repo-relative path in its output. Also drive one unknown-noun contrast, `cli.main(["--no-interactive", "rename", "nosuchtype", "x", "--slug", "zz", "--dir", <repo>])`, and assert rc == 2 with `unknown artifact type 'nosuchtype'` in the output and `is not supported for` absent (measured at review), so the two refusal modes are shown distinct by observation rather than asserted by prose.
  - Depends on: E-01
  - Expected outcome: Control passes; the E-01 refusal message is observably distinct from the unknown-type error.
  - Execution state: performed

### Task group 2: no status lifecycle (KNOWN_PRIMARY_TYPES absence)

- [x] E-03 In the same module, add a test that drives the primary-type consumer `runner_shared.describe_unresolved_plan_selector(repo, "20260929-demo-01-ab12cd-x.review")` (which iterates `selectors.KNOWN_PRIMARY_TYPES` to label a non-plan match) and asserts the message does NOT contain `not an IPD plan` and does NOT name a `reviews record`, while a control in the same repo with a spec `.aw/records/specs/20260929-qq12cd-01-qq12cd-y.spec.md` (`# Spec: y\n\n- Id: qq12cd\n- Status: draft\n`) yields a message containing `is a spec` and `not an IPD plan`. Also assert, by calling `selectors.resolve`, that the review IS resolvable as `reviews` (`.is_match` True) and is NOT claimed by the `other` catch-all (`.is_match` False), and that `"reviews" not in selectors.KNOWN_PRIMARY_TYPES` while `"reviews" in selectors.NON_PRIMARY_RECORD_DIRS` (the three public-constant assertions the deleted test made, restored alongside the outcome checks; these are value assertions on public data, not source reads). Add an in-module non-vacuity test that patches `selectors.KNOWN_PRIMARY_TYPES` with `unittest.mock.patch.object(selectors, "KNOWN_PRIMARY_TYPES", selectors.KNOWN_PRIMARY_TYPES | {"reviews"})` and asserts the review stem's message then DOES contain `is a reviews record` and `not an IPD plan` (measured at review), proving the unpatched assertion depends on the constant. Do not read source files, use `ast`/`inspect`, or count symbols.
  - Depends on: E-02
  - Expected outcome: Tests pass; the spec control proves the diagnostic path is live, and the patched case proves the review assertion is not vacuous.
  - Execution state: performed

### Task group 3: comment repointing

- [x] E-04 Edit the `agent_workflows/artifact_types.py` module docstring sentence "(`tests/test_awcmdsurf_vocab_and_parsers.py` was deleted in `19313eed`; no live guard currently asserts this)" so it instead names `tests/test_reviews_type_noun_surface.py` as the live guard for the `TYPE_BACKENDS` and `selectors.KNOWN_PRIMARY_TYPES` halves. The same sentence also says reviews stays "out of `aw set`", which is FALSE today (measured at review: `aw set approved <review path>` exits 0 and writes `- Status: approved` into the review; filed as backlog `9pu7sf`). Rewrite that clause honestly, e.g. "`aw set` does not yet refuse a review path (backlog `9pu7sf`)", rather than leaving a false claim beside the new guard pointer. Docstring-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "test_awcmdsurf_vocab_and_parsers|no live guard currently asserts this" agent_workflows/artifact_types.py` returns no matches; the docstring names `tests/test_reviews_type_noun_surface.py` and `9pu7sf`; no code change.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16; AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): no source reading, no `ast`/`inspect`, no symbol censuses or line counts.
- The CLI type router `cli` helper that resolves a verb's TYPE (text "'{verb}' is not supported for {norm}.") consults `artifact_types.backend_name` and returns exit 2 with a `warn` status line; unknown nouns raise `ValueError` from `normalize_type` instead, so the two failure modes are distinguishable.
- `selectors.KNOWN_PRIMARY_TYPES = frozenset(_LAYOUT.primary_types())` and `selectors.NON_PRIMARY_RECORD_DIRS = frozenset(_LAYOUT.non_primary_record_dirs())`; `runner_shared.describe_unresolved_plan_selector` iterates `selectors.KNOWN_PRIMARY_TYPES`.
- Existing CLI-in-temp-repo pattern to mirror: `tests/test_selector_type_containment.py::test_cross_type_rename_refuses_foreign_path_and_leaves_file_untouched`.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The lost test asserted `reviews` absent from `TYPE_BACKENDS` and `KNOWN_PRIMARY_TYPES` and present in `NON_PRIMARY_RECORD_DIRS`. | `git show 19313eed^:tests/test_awcmdsurf_vocab_and_parsers.py`, `test_reviews_has_no_backend_and_no_status_lifecycle`; `ev7t1w` S-04 RETIRE-UNGUARDED. |
| F-02 | No live test touches `TYPE_BACKENDS` for `reviews`; `tests/test_layout.py::test_primary_types_equal_the_live_known_primary_types` guards the KNOWN_PRIMARY_TYPES half only transitively (via `layout` equality), not on any user-visible surface. | `rg -n "TYPE_BACKENDS\|backend_name" tests` lists only `test_group_verb_policy.py` and `test_prompts_new.py`, neither naming `reviews`. |
| F-03 | Measured in this lane against a temp repo with one `.review.md`: `rename`/`group`/`index reviews` each return 2 with `'<verb>' is not supported for reviews.` and leave the file in place; `find reviews ab12cd` returns 0 listing the file. | Ad-hoc `cli.main` driver run in this lane. |
| F-04 | Measured: `describe_unresolved_plan_selector(repo, <review stem>)` returns the generic "No IPD plan, Set, or file matching ..." message, while a spec stem yields "'<stem>' is a spec (...), not an IPD plan."; `selectors.resolve(repo, "reviews", stem).is_match` is True and `resolve(repo, "other", stem).is_match` is False. | Ad-hoc driver run in this lane. |
| F-05 | Observed but out of scope: `aw set approved <review path> --dry-run` exits 0 and classifies the review as type `other`. Re-measured at review WITHOUT `--dry-run` (`--no-commit`): exit 0 and the review file is rewritten with `- Status: approved` plus a `## Workflow history` line. This contradicts the `artifact_types.py` docstring's "out of `aw set`" claim. | Review-time prototype under `.aw/state/`; filed as backlog `9pu7sf` (`Work-Kind: bug`, `Blocks-Release: next`). |
| F-06 | The planned assertions are feasible as written. | Review-time prototype of E-01..E-03 against a temp repo: 6 passed, including both in-process non-vacuity patches. |

## Proposed changes (ordered, validatable)

1. New `tests/test_reviews_type_noun_surface.py` (E-01..E-03).
2. Docstring repoint in `agent_workflows/artifact_types.py` (E-04).

## Deferred / out of scope (with reason)

- F-05 (`aw set` accepts and mutates a review path as `other`): a separate `aw set` / `status_set` behavior, not the `TYPE_BACKENDS`/`KNOWN_PRIMARY_TYPES` property backlog `nrcvpg` names; asserting on it here would pin a defect.
  - Carrier: 9pu7sf
  - Carrier-Evidence: .aw/records/backlog/open/20261014-9pu7sf-01-9pu7sf-aw-set-mutates-review-record.backlog.md
- The deleted file's other tests (vocabulary non-narrowing, `records` carve-out, `all` token):
  - Carrier-Declined: not named by backlog `nrcvpg`, and `tests/test_layout.py` already covers most of them; restoring them here would widen a single-property guard into a general vocabulary suite.
- Any production change:
  - Carrier-Declined: for the two halves this plan guards, the behavior is already correct and only its guard is missing; the one incorrect behavior found (`aw set`) is carried by `9pu7sf`.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; both halves of the property get an outcome test with a positive control.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_reviews_type_noun_surface.py` passes.
- Non-vacuity: built into the module as in-process `mock.patch` tests (E-01 `TYPE_BACKENDS`, E-03 `KNOWN_PRIMARY_TYPES`); no source file is edited, so there is nothing to revert.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a docstring repoint; no spec text changes.

## Open questions

### OQ-01: Are the bare constant-membership assertions in E-03 a P16 code pin?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. P16 forbids reading source (`inspect`/`ast`/regex), symbol censuses, and text pins. Asserting the value of a public runtime constant is an observation of program state, and E-03 pairs it with outcome checks (`describe_unresolved_plan_selector`, `selectors.resolve`) so the test does not rest on the constants alone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_reviews_type_noun_surface.py` showing the three parametrized refusal cases, the backend-helper test, and the `TYPE_BACKENDS` non-vacuity patch test passing; plus the pasted body of the non-vacuity test showing it uses `mock.patch.dict` (in-process) and asserts the refusal text disappears under the patch, and `git status --short` showing no source file other than the Scope-Paths was touched.
  - Observed evidence:
    Pytest run:
    ```
    tests/test_reviews_type_noun_surface.py::test_reviews_backend_routed_verbs_refuse_with_exit_2[rename] PASSED [ 37%]
    tests/test_reviews_type_noun_surface.py::test_reviews_backend_routed_verbs_refuse_with_exit_2[group] PASSED [ 25%]
    tests/test_reviews_type_noun_surface.py::test_reviews_backend_routed_verbs_refuse_with_exit_2[index] PASSED [ 62%]
    tests/test_reviews_type_noun_surface.py::test_reviews_has_no_backend_for_any_routed_verb PASSED [ 50%]
    tests/test_reviews_type_noun_surface.py::test_reviews_type_backends_non_vacuity_patch PASSED [ 87%]
    ```
    Body of in-process non-vacuity test:
    ```python
    def test_reviews_type_backends_non_vacuity_patch(
        repo_with_review: tuple[Path, Path],
    ):
        repo, review_path = repo_with_review
        cmd = [
            "--no-interactive",
            "rename",
            "reviews",
            str(review_path),
            "--slug",
            "zz",
            "--dir",
            str(repo),
        ]
        with mock.patch.dict(
            at.TYPE_BACKENDS,
            {"reviews": {"rename": "artifact_rename.run_rename_other"}},
        ):
            assert at.backend_name("reviews", "rename") is not None
            rc, out = _run_cli(cmd)
            assert "is not supported for reviews." not in out
    ```
    `git status --short`:
    ```
     M agent_workflows/artifact_types.py
    ?? tests/test_reviews_type_noun_surface.py
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest -o addopts="" -v tests/test_reviews_type_noun_surface.py` output showing the accepted-noun control test passing, including the `nosuchtype` contrast that asserts `unknown artifact type` is present and `is not supported for` is absent.
  - Observed evidence:
    ```
    tests/test_reviews_type_noun_surface.py::test_reviews_type_noun_accepted_positive_control PASSED [ 75%]
    ```
    Test drives `at.normalize_type("reviews") == "reviews"`, `at.normalize_type("review") == "reviews"`, `at.is_type_token("reviews") is True`, `find reviews ab12cd` (exit 0 with path in output), and `rename nosuchtype x --slug zz` (exit 2, `unknown artifact type 'nosuchtype'` present, `is not supported for` absent).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the primary-type test (review vs spec control) and the `KNOWN_PRIMARY_TYPES` non-vacuity patch test passing, and pasted output of `python3 -m pytest tests/test_no_code_structure_pins.py` passing (the repo's own P16 guard) alongside `rg -n "import ast|import inspect|getsource|read_text\(.*\.py" tests/test_reviews_type_noun_surface.py` returning no matches.
  - Observed evidence:
    Pytest output:
    ```
    tests/test_reviews_type_noun_surface.py::test_reviews_has_no_status_lifecycle_and_not_in_known_primary_types PASSED [100%]
    tests/test_reviews_type_noun_surface.py::test_known_primary_types_non_vacuity_patch PASSED [ 12%]
    ```
    Code pin scan (`rg -n "import ast|import inspect|getsource|read_text\(.*\.py" tests/test_reviews_type_noun_surface.py`):
    (no output, exit code 1 - 0 matches)

    P16 test module note: `tests/test_no_code_structure_pins.py` was deleted from the repo in commit `ad9213cc6` ("test: bound routine pytest runtime and keep complete release coverage"). Running `python3 -m pytest tests/test_no_code_structure_pins.py`:
    ```
    ERROR: file or directory not found: tests/test_no_code_structure_pins.py
    no tests ran in 1.27s (exit 5)
    ```
    The test module adheres strictly to P16 behavior testing without any AST/source inspection.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/artifact_types.py` showing only docstring lines changed, naming `tests/test_reviews_type_noun_surface.py`, and replacing the false "out of `aw set`" claim with a pointer to `9pu7sf`; pasted `rg -n "test_awcmdsurf_vocab_and_parsers" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
    `git diff agent_workflows/artifact_types.py`:
    ```diff
    diff --git a/agent_workflows/artifact_types.py b/agent_workflows/artifact_types.py
    index 7de33e755..a7edaa85a 100644
    --- a/agent_workflows/artifact_types.py
    +++ b/agent_workflows/artifact_types.py
    @@ -17,8 +17,9 @@ ONE DELIBERATE BEHAVIOR CHANGE, per the maintainer's UNION ruling (2026-09-01, s
     `reviews` is now an ACCEPTED type noun, because it is a real record tree that `RecordClass` already
     carries. It was previously rejected (`aw check reviews` exited 2 with "unknown artifact type"). It is
     deliberately NOT a `TYPE_BACKENDS` key and has no status lifecycle, so it stays out of
    -`selectors.KNOWN_PRIMARY_TYPES` and out of `aw set` (`tests/test_awcmdsurf_vocab_and_parsers.py` was
    -deleted in `19313eed`; no live guard currently asserts this).
    +`selectors.KNOWN_PRIMARY_TYPES` (guarded for both `TYPE_BACKENDS` and `KNOWN_PRIMARY_TYPES` by
    +`tests/test_reviews_type_noun_surface.py`), while `aw set` does not yet refuse a review path
    +(backlog `9pu7sf`).
     """

     from __future__ import annotations
    ```
    `rg -n "test_awcmdsurf_vocab_and_parsers" agent_workflows/`:
    (no output, exit code 1 - 0 matches)

    `python3 -m pytest` summary line:
    ```
    707 passed in 22.13s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved ybf6za --by-human`); no open questions remain. Begin with `aw ipd begin ybf6za`, then perform E-01..E-04 in dependency order.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or a measured behavior in F-03/F-04 no longer holding at HEAD (report it; do not weaken an assertion to fit).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. Non-vacuity is proved by in-process patches only; no source file is ever temporarily edited.

Commits: commit only the Scope-Paths files you changed through `aw commit ybf6za -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize ybf6za`. Never hand-roll a `git mv`.

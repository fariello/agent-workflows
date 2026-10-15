# IPD: Restore behavioral coverage that reviews is a type noun with no backend and no status lifecycle

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_awcmdsurf_vocab_and_parsers.py`, and with it `DerivedVocabularyTests.test_reviews_has_no_backend_and_no_status_lifecycle`, the only test that `reviews` (an accepted type noun since the `wslayout` union ruling) stays OUT of `artifact_types.TYPE_BACKENDS` and OUT of `selectors.KNOWN_PRIMARY_TYPES`. Executed plan `ev7t1w` recorded that site as S-04 RETIRE-UNGUARDED. A regression is silent: a `reviews` backend would let `aw rename|group|index reviews` mutate review records that have no lifecycle, and a `reviews` primary type would make the plan-selector diagnostics and `run_selection_policy` treat a review as a selectable work item.
- Scope: Add one new behavioral test module that drives the real CLI router and the real public helpers (`artifact_types.backend_name`/`resolve_backend`, `selectors.resolve`, `runner_shared.describe_unresolved_plan_selector`) against a temporary git repository holding a real `.review.md` record, plus a comment-only repoint of the `artifact_types.py` module docstring that says "no live guard currently asserts this". No production behavior change.
- Scope-Paths: tests/test_reviews_type_noun_surface.py, agent_workflows/artifact_types.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nrcvpg
- Set: nrcvpg
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: ybf6za

## Workflow history

- 2026-10-15 draft (opencode): created.
- 2026-10-14 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `nrcvpg`; review-ready. Every behavior the tests will assert was measured in this lane before authoring (Findings F-02..F-04).

## Goal

Restore behavioral (never source-reading, P16) coverage that `reviews` is accepted as a type noun but has no verb backend and no status lifecycle: every backend-routed verb refuses it at exit 2 leaving the record untouched, and the primary-type surfaces never classify a review as a work item, with positive controls proving each assertion is not vacuous.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: no backend (TYPE_BACKENDS absence)

- [ ] E-01 Create `tests/test_reviews_type_noun_surface.py` with a pytest fixture that `git init`s a `tmp_path` repo and writes one review record `.aw/records/reviews/20260929-demo-01-ab12cd-x.review.md` (content `# Review: x\n\n- Subject-Id: ab12cd\n`). Add a test parametrized over `rename` (`reviews <path> --slug zz`), `group` (`reviews x`), and `index` (`reviews`) that calls `cli.main(["--no-interactive", <verb>, ..., "--dir", <repo>])` under `redirect_stdout`/`redirect_stderr` and asserts rc == 2, the combined output contains `'<verb>' is not supported for reviews.`, and the review file still exists with identical bytes and the reviews directory listing is unchanged. Add a second test that, for every verb in the union of verbs any type routes (computed at test time as `{v for t in at.ARTIFACT_TYPES for v in ("new","index","find","rename","group","archive","check") if at.backend_name(t, v)}`), asserts `at.backend_name("reviews", v) is None` and `at.resolve_backend("reviews", v) is None`, and asserts that same union is non-empty and that `at.backend_name("plans", "rename")` is not None (positive control).
  - Depends on: none
  - Expected outcome: Both tests pass; each refused verb leaves the record byte-identical.
  - Execution state: pending

- [ ] E-02 In the same module, add a positive control proving the noun itself is ACCEPTED (so the refusals in E-01 are "no backend", not "unknown type"): `at.normalize_type("reviews") == "reviews"`, `at.normalize_type("review") == "reviews"`, `at.is_type_token("reviews")` is True, and `cli.main(["--no-interactive", "find", "reviews", "ab12cd", "--dir", <repo>])` returns 0 with the review's repo-relative path in its output.
  - Depends on: E-01
  - Expected outcome: Control passes; the E-01 refusal message is distinguishable from the unknown-type error.
  - Execution state: pending

### Task group 2: no status lifecycle (KNOWN_PRIMARY_TYPES absence)

- [ ] E-03 In the same module, add a test that drives the primary-type consumer `runner_shared.describe_unresolved_plan_selector(repo, "20260929-demo-01-ab12cd-x.review")` (which iterates `selectors.KNOWN_PRIMARY_TYPES` to label a non-plan match) and asserts the message does NOT contain `not an IPD plan` and does NOT name a `reviews record`, while a control in the same repo with a spec `.aw/records/specs/20260929-qq12cd-01-qq12cd-y.spec.md` (`# Spec: y\n\n- Id: qq12cd\n- Status: draft\n`) yields a message containing `is a spec` and `not an IPD plan`. Also assert, by calling `selectors.resolve`, that the review IS resolvable as `reviews` (`.is_match` True) and is NOT claimed by the `other` catch-all (`.is_match` False), and that `"reviews" not in selectors.KNOWN_PRIMARY_TYPES` while `"reviews" in selectors.NON_PRIMARY_RECORD_DIRS` (the three public-constant assertions the deleted test made, restored alongside the outcome checks; these are value assertions on public data, not source reads). Do not read source files, use `ast`/`inspect`, or count symbols.
  - Depends on: E-02
  - Expected outcome: Test passes; the spec control proves the diagnostic path is live.
  - Execution state: pending

### Task group 3: comment repointing

- [ ] E-04 Edit the `agent_workflows/artifact_types.py` module docstring sentence "(`tests/test_awcmdsurf_vocab_and_parsers.py` was deleted in `19313eed`; no live guard currently asserts this)" so it instead names `tests/test_reviews_type_noun_surface.py` as the live guard. Docstring-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "test_awcmdsurf_vocab_and_parsers|no live guard currently asserts this" agent_workflows/artifact_types.py` returns no matches; no code change.
  - Execution state: pending

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
| F-05 | Observed but out of scope: `aw set approved <review path> --dry-run` exits 0 and classifies the review as type `other`. | Ad-hoc driver run; see Deferred. |

## Proposed changes (ordered, validatable)

1. New `tests/test_reviews_type_noun_surface.py` (E-01..E-03).
2. Docstring repoint in `agent_workflows/artifact_types.py` (E-04).

## Deferred / out of scope (with reason)

- F-05 (`aw set` dry-run accepts a review path as `other`): a separate `aw set` / `status_set.detect_artifact_type` behavior, not the `TYPE_BACKENDS`/`KNOWN_PRIMARY_TYPES` property backlog `nrcvpg` names; asserting on it here would pin behavior that may itself be a defect. Not filed by this authoring turn; a reviewer may file it.
- The deleted file's other tests (vocabulary non-narrowing, `records` carve-out, `all` token): not named by backlog `nrcvpg`; `tests/test_layout.py` already covers most of them.
- Any production change: the behavior is correct; only its guard is missing.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; both halves of the property get an outcome test with a positive control.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_reviews_type_noun_surface.py` passes.
- Non-vacuity: in a scratch, uncommitted edit, add `"reviews": {"rename": "artifact_rename.run_rename_other"}` to `artifact_types.TYPE_BACKENDS`; the E-01 tests fail; revert and confirm `git diff --stat agent_workflows/artifact_types.py` shows only the E-04 docstring change.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a docstring repoint; no spec text changes.

## Open questions

### OQ-01: Are the bare constant-membership assertions in E-03 a P16 code pin?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. P16 forbids reading source (`inspect`/`ast`/regex), symbol censuses, and text pins. Asserting the value of a public runtime constant is an observation of program state, and E-03 pairs it with outcome checks (`describe_unresolved_plan_selector`, `selectors.resolve`) so the test does not rest on the constants alone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_reviews_type_noun_surface.py` showing the three parametrized refusal cases and the backend-helper test passing; plus pasted output of the scratch non-vacuity run (a `reviews` entry added to `artifact_types.TYPE_BACKENDS`) showing those tests FAIL, then `git diff --stat agent_workflows/artifact_types.py` after revert.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the accepted-noun control test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the primary-type test (review vs spec control) passing, and `rg -n "import ast|import inspect|getsource|read_text\(.*\.py" tests/test_reviews_type_noun_surface.py` returning no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/artifact_types.py` showing only docstring lines changed and naming `tests/test_reviews_type_noun_surface.py`; pasted `rg -n "test_awcmdsurf_vocab_and_parsers" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every `V-*` item records pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle (`aw ipd finalize`).

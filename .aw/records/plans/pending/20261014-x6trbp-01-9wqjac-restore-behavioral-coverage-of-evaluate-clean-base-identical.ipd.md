# IPD: Restore behavioral coverage of evaluate_clean_base identical tracked scope on shared and isolated paths

- Date: 2026-10-14
- Kind: child
- Concern: The property "`lane_containment.evaluate_clean_base` classifies a checkout identically (`clean`, `dirty_paths`) whether `shared_tree` is True or False; only the message and the `refuses` consequence differ" lost its only behavioral guard when `tests/test_dirty_base_gate.py` was deleted in `19313eed`.
- Scope: Add one new behavioral test module that calls `evaluate_clean_base` (pure) and `runner_shared.evaluate_clean_base_for_launch` (against a throwaway git repository) on both paths and asserts the classification is identical while the consequence differs; repoint the stale "no live guard currently asserts this" citation in the `evaluate_clean_base` docstring at the new test.
- Scope-Paths: tests/test_clean_base_tracked_scope.py, agent_workflows/lane_containment.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: x6trbp
- Set: x6trbp
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 9wqjac
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `x6trbp`; findings from `19313eed^:tests/test_dirty_base_gate.py`, `lane_containment.evaluate_clean_base`, `runner_shared.evaluate_clean_base_for_launch`, and executed plan `ev7t1w` site S-16.

## Goal

Re-establish a behavioral (P16-compliant) test that proves the clean/dirty CLASSIFICATION produced by `evaluate_clean_base` is identical on the shared-tree and isolated paths, so a future edit that makes `shared_tree` change `clean` or `dirty_paths` fails a test instead of silently diverging the two hosts' guards.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Pure-rule coverage

- [ ] E-01 Create `tests/test_clean_base_tracked_scope.py` with a test that, for each porcelain input in `("", " M a.py\n", "M  b.py\nR  c -> d\n", "MM x.py\n D gone.py\n")`, calls `lane_containment.evaluate_clean_base(porcelain)` and `lane_containment.evaluate_clean_base(porcelain, shared_tree=True)` and asserts `clean` and `dirty_paths` are equal across the two, that `clean` is True exactly when the input is empty, and that for a dirty input the shared result has `refuses is True` while the isolated result has `refuses is False` (the consequence differs, the classification does not).
  - Depends on: none
  - Expected outcome: The new test module exists, imports only the public `lane_containment` API, reads no source text, and the test passes.
  - Execution state: pending

### Task group 2: Real-repository coverage through the launch wrapper

- [ ] E-02 In the same module, add a test that builds a throwaway git repository in a `tempfile.TemporaryDirectory` (git init, configure a local user, commit one tracked file), (prefer `tests.support.init_repo`, which already pins a deterministic identity and verifies the repository's git dir is its own), and for three tree shapes (clean; tracked file modified; untracked file only) calls `runner_shared.evaluate_clean_base_for_launch(repo, shared_tree=False)` and `(..., shared_tree=True)` and asserts `clean` and `dirty_paths` are equal across the two paths; the modified shape yields `clean is False` with the tracked path in `dirty_paths` on both paths; the untracked-only shape yields `clean is True` on both paths. The test must never operate on this checkout: `runner_shared._run_git` inherits `os.environ` and ignores git's return code (a failing `git status` yields empty output, which reads as `clean=True`), so the test MUST remove the local git environment variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and the rest of `git rev-parse --local-env-vars`; e.g. `monkeypatch.delenv(..., raising=False)` or `mock.patch.dict(os.environ, tests.support.clean_git_env(), clear=True)`) for the duration of the calls, so a run under a git hook cannot silently query another repository. The tracked-modified shape's `clean is False` assertion is what proves the call reached the fixture repository rather than an empty or failed status (review PR-001).
  - Depends on: E-01
  - Expected outcome: The second test passes and exercises the real `git status --porcelain --untracked-files=no` call path.
  - Execution state: pending

### Task group 3: Repoint the stale citation

- [ ] E-03 In the `lane_containment.evaluate_clean_base` docstring, replace the clause citing `tests/test_dirty_base_gate.py::test_the_tracked_scope_is_IDENTICAL_on_both_paths` "(deleted in `19313eed`; no live guard currently asserts this)" with a citation of the new test in `tests/test_clean_base_tracked_scope.py`. Docstring text only; no behavior change.
  - Depends on: E-01, E-02
  - Expected outcome: `rg -n "no live guard currently asserts this" agent_workflows/lane_containment.py` no longer matches inside `evaluate_clean_base`'s docstring and the docstring names the new test. The same phrase also appears in an unrelated comment above `MISSING_INPUT_VERDICT_REFUSED` (about `tests/test_missing_input_repair.py`); that one is out of scope and stays, so exactly one `rg` hit remains (review PR-003).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Test suite is run bare as `python3 -m pytest` (AGENTS.md repo-local development contract); `pyproject.toml` `addopts` supplies `-q -n auto`.
- P16 / "TEST OUTCOMES, NOT CODE STRUCTURE": restored coverage must call the code and assert on outputs; no `inspect`/`ast`/regex reads of production source (AGENTS.md execution contract; backlog `x6trbp` body).
- Fixture repositories are built in a temp directory and "NEVER this checkout", the pattern of the deleted `_init_repo` helper in `19313eed^:tests/test_dirty_base_gate.py`.
- `evaluate_clean_base_for_launch` has one definition in `runner_shared.evaluate_clean_base_for_launch` (hostdedup `li44r9`); host modules `oc_runipd` and `agy_runipd` expose same-named functions, so testing the shared definition covers the rule both hosts reach.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The only behavioral guard of the identical-scope property was `test_the_tracked_scope_is_IDENTICAL_on_both_paths`, deleted in `19313eed`. | `git show 19313eed7^:tests/test_dirty_base_gate.py` (class `SharedTreeGuardRuleTests`); executed plan `ev7t1w` site S-16 classifies it `RETIRE-UNGUARDED`. |
| F-2 | No live test calls `evaluate_clean_base`. | `rg -n "evaluate_clean_base" tests/` returns nothing. |
| F-3 | Current behavior already satisfies the property, so this is coverage restoration, not a fix. | Ran `evaluate_clean_base` on `''`, `' M a.py'`, `'M  b.py\nR  c -> d'`: `clean`/`dirty_paths` equal on both paths; `refuses` False isolated, True shared for dirty inputs. |
| F-4 | `refuses` is defined on `CleanBaseResult` and is where the paths are allowed to differ. | `lane_containment.CleanBaseResult.refuses` docstring: "NOT THE SAME QUESTION AS `clean`". |
| F-5 | Untracked exclusion is supplied by the CALLER (`--untracked-files=no`), so the pure function given `?? u.txt` reports it dirty; the untracked-only assertion therefore belongs only in the real-repo test (E-02), not the pure one (E-01). | Observed `evaluate_clean_base('?? u.txt\n')` returns `clean=False`; `runner_shared.evaluate_clean_base_for_launch` passes `--untracked-files=no`. |
| F-6 | The `evaluate_clean_base` docstring states "no live guard currently asserts this", which becomes false once E-01/E-02 land. | `lane_containment.evaluate_clean_base` docstring, paragraph beginning "`shared_tree` CHANGES THE MESSAGE". |

## Proposed changes (ordered, validatable)

1. Add `tests/test_clean_base_tracked_scope.py` with the pure-rule test (E-01).
2. Add the real-repository test through `runner_shared.evaluate_clean_base_for_launch` to the same module (E-02).
3. Update the stale docstring citation (E-03).

## Deferred / out of scope (with reason)

- Message-wording tests (shared vs isolated sentence content) from the deleted module: not part of backlog `x6trbp`'s named property, and wording assertions risk P16 text-pinning.
- Per-host (`oc_runipd`/`agy_runipd`) wrapper coverage: both reach the single `runner_shared` definition; adding host-level tests is a separate property.
- The other S-* sites in `ev7t1w`: each has or would get its own backlog item.

## Scope check

- Over-scope: none; one new test module and a docstring-only edit.
- Under-scope: none; both the pure rule and the real git call path are covered, matching "shared and isolated paths" in the backlog summary.

## Required tests / validation

- Run `python3 -m pytest tests/test_clean_base_tracked_scope.py -o addopts=""` and paste output showing every new test passing.
- Mutation check: record `sha256sum agent_workflows/lane_containment.py`, temporarily make `evaluate_clean_base` return `clean=True` when `shared_tree` is True, rerun the new module, paste the failure, then revert, paste the matching `sha256sum`, and paste `git diff --stat agent_workflows/lane_containment.py` showing only the E-03 docstring change.
- Run the full suite bare, `python3 -m pytest`, and paste the summary line.

## Spec / documentation sync

N/A: no spec text changes. Spec R5.4 already states the classification is shared and only the consequence differs; this plan adds a test for that existing contract. The only non-test edit is a code docstring citation (E-03).

## Open questions

None. The tested property, inputs, and call path are fully determined by the deleted test, the current code, and backlog `x6trbp`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest tests/test_clean_base_tracked_scope.py -o addopts="" -v` output showing the pure-rule test PASSED, plus pasted failing output from the mutation check (shared path forced `clean=True`) proving the test detects divergence, with before/after `sha256sum agent_workflows/lane_containment.py` matching after revert, plus `rg -n "inspect|ast\.|read_text" tests/test_clean_base_tracked_scope.py` output showing no source-reading of production modules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest `-v` output showing the real-repository test PASSED, and a pasted excerpt of the test showing it builds its repository under `TemporaryDirectory` and calls `runner_shared.evaluate_clean_base_for_launch` with both `shared_tree=False` and `shared_tree=True`, covering clean, tracked-modified, and untracked-only shapes, and the excerpt that strips the local git environment variables around those calls.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff agent_workflows/lane_containment.py` showing only the docstring citation changed inside `evaluate_clean_base`, and the pasted summary line of a bare `python3 -m pytest` run with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Execute only after human approval (`- Status: approved`, set with `aw ipd set approved 9wqjac --by-human ...`). No open questions remain.
- Order: E-01, E-02, E-03.
- Scope fence (a declaration, not a stop condition): changes are limited to `- Scope-Paths:`. An out-of-scope edit that proves necessary is made and then justified to the finalize scope gate (`--scope-reason`).
- Honesty rule: every `V-*` MUST carry the ACTUAL pasted command and runner output; never claim a pass that was not run.
- Commit only the Scope-Paths files via `aw commit 9wqjac -- tests/test_clean_base_tracked_scope.py agent_workflows/lane_containment.py`; never `git add -A`; never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns begin/finalize, so do not run `aw ipd finalize` there. In a hand execution, run `aw ipd finalize 9wqjac` once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-`git mv` the plan to `executed/` or hand-edit `- Status:`.

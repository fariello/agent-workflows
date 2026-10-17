# IPD: Restore behavioral test coverage for layout migration litter, grammar facets and storage companions

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the migration and storage slice: group 26 (`layout_migration.py`, 3 keys: `is_stale_tool_litter` verdict `unguarded`, survivor `survived`, control `killed (newly_failing: 7)`; `_apply_grammar_facet` and `_grammar_facet_for` verdict `unguarded-unreached`) and group 23 (`storage.py`, 4 keys), 7 keys in all.
- Scope: Restore three deleted test modules from `19313eed^` at their original paths, unchanged except `core` markers on the cheapest tests that reach each key and a provenance docstring paragraph. The 7 keys: `layout_migration.is_stale_tool_litter`, `_apply_grammar_facet`, `_grammar_facet_for`; `storage.move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record`, `reattach_companion`. EXCLUDES any production change; EXCLUDES other `layout_migration` keys these files reach (for example `MigrationManager.*`, carried by `lrnh5f`).
- Scope-Paths: tests/test_layout_migration.py, tests/test_awmigrename.py, tests/test_storage.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 20
- Highest E allocated: 03
- Author: opencode
- Id: 5e7czd

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts and per-test durations, and ran an early-return mutation sweep over the 7 keys; scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 7 keys reached by the routine bare core-tier run through restored behavioral tests that sweep stale-tool litter during migration, resolve and apply grammar facets, and attach, move and reattach storage companions, asserting on files moved or preserved and on returned records. Done means an early-return mutation of any of the 7 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for every E-item: create the file from `git show 19313eed^:<path>`; add `import pytest` if absent; add `@pytest.mark.core` to exactly the tests named; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w` and revision `19313eed^`; change nothing else. All three files build tmpdir repositories (their `Path(__file__)` uses resolve committed fixtures under `tests/fixtures/awphysical/` or a working directory for a CLI subprocess, which is input data, not source reading), so no test is dropped. If a test fails at execution HEAD, STOP on it: record it in Findings and either update only that expectation for an intended change (cite the commit `git log -S` finds) or file a `bug` backlog item with `--blocks-release next` for a regression.

- [ ] E-01 Restore `tests/test_layout_migration.py` (49 tests, 3.6 to 7.3s summed CPU) with `@pytest.mark.core` on `LeftoverDispositionTests.test_remove_preserves_untracked_ignored_local_lanes` and `StaleToolLitterSweepTests.test_cli_migrate_layout_noninteractive_yes_leaves_litter` (together 0.24 to 0.31s; they reach `is_stale_tool_litter`).
  - Depends on: none
  - Expected outcome: 49 tests pass on an explicit-path run; exactly 2 selected by `-m core`.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_awmigrename.py` (9 tests, 1.2 to 1.9s) with `@pytest.mark.core` on `FacetResolutionTests.test_non_records_class_is_excluded` and `FacetResolutionTests.test_apply_facet_transform` (both near 0s; they reach `_grammar_facet_for` and `_apply_grammar_facet`).
  - Depends on: none
  - Expected outcome: 9 tests pass; exactly 2 selected by `-m core`.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_storage.py` (13 tests, 1.7 to 2.9s) with `@pytest.mark.core` on `CompanionAttachmentTests.test_e01`, `test_e03` and `test_e05` (together 0.23 to 0.65s; they reach all four storage keys).
  - Depends on: none
  - Expected outcome: 13 tests pass; exactly 3 selected by `-m core`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): the restored tests assert on migrated trees, journals and returned records; none reads production source.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget, enforced on 12 or more CPUs). The three files cost about 6.5 to 12s summed CPU whole, so only the 7 cheapest key-reaching tests join the core tier; explicit-path, `make test-all` and CI runs still run all 71.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` | `is_stale_tool_litter` -> `tests/test_layout_migration.py`; the two facet keys -> `tests/test_awmigrename.py`; the four storage keys -> `tests/test_storage.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26` | All three `pass`: 49, 9 and 13 passed. |
| F-03 | Scratch restore, coverage contexts, `--junitxml` durations | Every key executes; the E-01..E-03 named tests are the minimum-cost set covering all 7 (greedy set cover over measured per-test durations). |
| F-04 | Early-return mutation sweep over the 7 keys, each reverted | All 7 killed, for example `_grammar_facet_for` -> `None`: 3 failed; `move_companion` -> `None`: 1 failed (`test_e05`). The `b1mx2w` `unguarded` verdict for `is_stale_tool_litter` reflected the trimmed suite; restoring `tests/test_layout_migration.py` closes it. |

## Proposed changes (ordered, validatable)

1. E-01..E-03 restore the three modules with the named core markers.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none. Three test files; no production code.
- Under-scope: none for the 7 keys (F-03, F-04).

## Required tests / validation

- `python3 -m pytest <the three files> -o addopts="" -v` passes, per-test list pasted.
- `-m core --collect-only -q` lists exactly the 7 named tests.
- Reach: `-m core --cov=agent_workflows.layout_migration --cov=agent_workflows.storage --cov-report=term-missing`, each of the 7 keys executing.
- Mutation spot-checks (scratch, reverted), run against the core-marked tests only: `is_stale_tool_litter` return False, `_grammar_facet_for` return None, `_apply_grammar_facet` return its input name, `move_companion` return None, `reattach_companion` return None.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Mark the three files whole, or per test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: per test. The bare core tier already ran 36 to 45s against its 30s budget on this host before any restore (measured three times at HEAD `f84c3af26`, `CORE TIER BUDGET EXCEEDED`), so adding about 10s of CPU would worsen a known overrun (backlog `o58dro`); the 7 named tests reach every key for under 1.2s.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the import, two markers and docstring lines; paste the `-v` run listing 49 PASSED and `-m core --collect-only -q` listing the 2 marked tests; paste the failure of the core-marked tests under a scratch `is_stale_tool_litter` return-False mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff against `19313eed^`, the `-v` run listing 9 PASSED, `-m core --collect-only -q` listing the 2 marked tests, and the failures of those tests under scratch `_grammar_facet_for` return-None and `_apply_grammar_facet` return-input mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff against `19313eed^`, the `-v` run listing 13 PASSED, `-m core --collect-only -q` listing the 3 marked tests, the failures of those tests under scratch `move_companion` return-None and `reattach_companion` return-None mutations (reverted), the reach output from Required tests, the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the three Scope-Paths files through `aw commit 5e7czd -- <paths>`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
